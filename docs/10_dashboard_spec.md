# Dashboard Specification

Five pages. Built directly on `data/cases.db`, no transformation required beyond
the relationships below.

## Why there is no .pbix in this repository

A `.pbix` is a binary. It cannot be diffed, reviewed in a pull request, or read
without a Power BI licence, which makes it the least trustworthy artifact a
portfolio repo could contain. This specification is complete enough to build the
report in an afternoon, and it can be reviewed by anyone.

## Model

| Table | Role | Rows |
|---|---|---|
| `case_data` | Fact | 15,908 |
| `dim_team` | Dimension | 5 |
| `dim_analyst` | Dimension | 35 |
| `dim_case_type` | Dimension | 6 |
| `dim_date` | Date dimension, marked as date table | 180 |
| `team_workload` | Pre-aggregated team measures | 5 |
| `team_capacity` | Team-by-day capacity fact | 900 |
| `dq_exceptions` | Governance fact | 577 |

### Relationships

| From | To | Cardinality | Direction |
|---|---|---|---|
| `case_data[Assigned_Team]` | `dim_team[Team_ID]` | many-to-one | single |
| `case_data[Assigned_Analyst]` | `dim_analyst[Analyst_ID]` | many-to-one | single |
| `case_data[Case_Type]` | `dim_case_type[Case_Type]` | many-to-one | single |
| `case_data[Created_Date]` | `dim_date[Date]` | many-to-one | single |
| `team_workload[Team_ID]` | `dim_team[Team_ID]` | one-to-one | both |
| `team_capacity[Team_ID]` | `dim_team[Team_ID]` | many-to-one | single |
| `team_capacity[Date]` | `dim_date[Date]` | many-to-one | single |

`Created_Date` is the active date relationship. `Resolved_Date` is left
unrelated deliberately: every measure in this report is cohorted by when a case
arrived, not when it closed, so that a month's compliance figure cannot change
retroactively as old cases close.

## Measures

```dax
Total Cases = COUNTROWS ( case_data )

Resolved Cases =
CALCULATE ( [Total Cases], case_data[Current_Status] = "Resolved" )

Open Cases =
CALCULATE ( [Total Cases], case_data[Current_Status] <> "Resolved" )

SLA Compliance % =
DIVIDE (
    CALCULATE ( [Total Cases], case_data[SLA_Met_Calculated] = "Yes" ),
    [Resolved Cases]
)

-- Denominator excludes the 12 records whose reassignment count was nulled by
-- DQ-12. Counting them as zero reassignments would inflate this measure.
Assignment Accuracy % =
VAR Valid =
    CALCULATE ( [Total Cases], NOT ISBLANK ( case_data[Reassignment_Count] ) )
VAR Clean =
    CALCULATE ( [Total Cases], case_data[Reassignment_Count] = 0 )
RETURN
    DIVIDE ( Clean, Valid )

Reopen Rate % =
DIVIDE (
    CALCULATE ( [Total Cases], case_data[Reopened_Flag] = "Yes" ),
    [Total Cases]
)

Avg Resolution Hours = AVERAGE ( case_data[Resolution_Hours] )

Median Resolution Hours = MEDIAN ( case_data[Resolution_Hours] )

Avg Assignment Lag Hours = AVERAGE ( case_data[Assignment_Lag_Hours] )

Total Breach Hours = SUM ( case_data[SLA_Breach_Hours] )

Avg Breach Hours = AVERAGE ( case_data[SLA_Breach_Hours] )

Avg Complexity Score = AVERAGE ( case_data[Complexity_Score] )

Workload Balance Index = AVERAGE ( team_workload[Workload_Balance_Index] )

Backlog Days Of Work =
AVERAGEX (
    team_capacity,
    DIVIDE ( team_capacity[Backlog_Work_Hours], team_capacity[Available_Hours] )
)

Data Quality Score =
VAR Excluded =
    CALCULATE (
        COUNTROWS ( dq_exceptions ),
        dq_exceptions[Action_Taken] = "Excluded from reporting"
    )
RETURN
    1 - DIVIDE ( Excluded, 16055 )

-- Traffic light for the equity page. Deliberately does not colour by SLA,
-- because the whole point of the page is that the two do not agree.
Balance Status Colour =
SWITCH (
    SELECTEDVALUE ( team_workload[Balance_Status] ),
    "Overloaded", "#c0392b",
    "Underutilized", "#f39c12",
    "#27ae60"
)

SLA vs Target Variance Hours =
AVERAGEX (
    FILTER ( case_data, case_data[Current_Status] = "Resolved" ),
    case_data[Resolution_Hours] - case_data[SLA_Target_Hours]
)
```

---

## Page 1 — SLA Control Tower

Purpose: the weekly leadership view. Answers "where are we losing, and by how much".

| Position | Visual | Fields |
|---|---|---|
| KPI row | Six cards | Total Cases 15,908 · SLA Compliance % 62.70% · Assignment Accuracy % 73.10% · Reopen Rate % 6.47% · Avg Resolution Hours 52.7 · Open Cases 194 |
| Left, upper | Bar chart, sorted ascending | `dim_case_type[Case_Type]` by SLA Compliance %, with a reference line at the blended 62.70% |
| Left, lower | Clustered bar | Case_Type by Avg Resolution Hours and Avg of SLA_Target_Hours, so the two types whose average exceeds their own target are visible at a glance |
| Right, upper | Line chart | `dim_date[Month_Name]` by SLA Compliance %, Assignment Accuracy %, Reopen Rate % |
| Right, lower | Treemap | Case_Type sized by Total Breach Hours — Authorization Review is 41% of the area |
| Filters | Month, Team, Case Type, Priority, Complexity Band | |

Design note: the reference line on the first visual exists so nobody reads the
blended figure as a target. Four of six case types sit above it and two sit far
below, which is the page's argument.

## Page 2 — Workload Equity

Purpose: test whether workload distribution explains the SLA spread. It does not,
and the page is laid out to show that.

| Position | Visual | Fields |
|---|---|---|
| Top | Table, conditional formatting on Balance Status Colour | Team, Primary Capability, Analyst Count, Cases Handled, Avg Complexity, Workload Balance Index, Balance Status, SLA Compliance %, Assignment Accuracy %, Median Resolution Hours |
| Middle left | Bullet-style bar | Workload Balance Index by Team, with band markers at 0.85 and 1.15 |
| Middle right | Bar chart | Backlog Days Of Work by Team, descending |
| Bottom left | Scatter | X = Workload Balance Index, Y = SLA Compliance %, one point per team, labelled |
| Bottom right | 100% stacked bar | Team by share of cases in each Complexity Band |
| Text box | Fixed annotation | "The only team flagged Overloaded has the second-best SLA. The worst SLA sits inside the Balanced band. Read this page with Backlog Days Of Work, not the index alone." |

Design note: the scatter is the whole point of the page. With five points and no
visible relationship, it is a more honest visual than a correlation coefficient
computed on n=5 would be.

## Page 3 — Routing Accuracy

Purpose: identify the controllable driver.

| Position | Visual | Fields |
|---|---|---|
| KPI row | Three cards | Assignment Accuracy % by method: Manual Triage 83.83% · Analyst Self-Select 77.69% · Auto-Routed 66.77% |
| Left | Table | Routing Method by Cases, Assignment Accuracy %, Avg Reassignments, Avg Assignment Lag Hours, SLA Compliance %, Reopen Rate % |
| Centre | Combo chart | X = Reassignment_Count (0–4); columns = case count; lines = SLA Compliance % and Reopen Rate % |
| Right upper | Matrix | Routing Method × Complexity Band, values = Reopen Rate % |
| Right lower | Matrix | Team × Routing Method, values = Avg Assignment Lag Hours |
| Filters | Case Type, Month, Team | |

Design note: the combo chart is the cost-of-a-reassignment exhibit. Compliance
falls from 70.33% to 44.18% at one reassignment while reopen rate rises from
4.41% to 12.15%. Both lines on one axis pair makes the trade legible.

## Page 4 — Priority Queue

Purpose: the operational page. What to work on now.

| Position | Visual | Fields |
|---|---|---|
| Top | KPI cards | Open Cases 194 · Past SLA target 20 · Avg Complexity Score of the open set 44.0 |
| Main | Table, sorted by hours past target descending then Complexity Score descending | Case ID, Case Type, Priority, Team, Analyst, Complexity Score, Complexity Band, Status, SLA Target Hours, Age Hours, Hours Past Target, Reassignment Count, Customer Segment |
| Right rail | Slicers | Team, Complexity Band, Status, Priority |
| Conditional format | Hours Past Target | Red above 0, amber within 8 hours of target, green otherwise |
| Right lower | Bar chart | Open cases by Team and Status |

Design note: sorted by lateness first and complexity second, not by priority.
Priority is already inside the complexity score, and sorting by priority would
put a Low-priority case that is 111 hours past target below an Urgent case that
has hours of headroom left.

## Page 5 — Root Cause and Rework

Purpose: where to aim process change.

| Position | Visual | Fields |
|---|---|---|
| Left | Bar chart, descending | Root Cause by case count, with Avg Resolution Hours as a line |
| Centre | Table | Root Cause by Cases, % of Resolved, Avg Resolution Hours, Reopen Rate %, SLA Compliance % |
| Right upper | Matrix | Complexity Band × Routing Method, values = Reopen Rate %, heat-formatted |
| Right lower | Bar chart | Reopen Rate % by Reassignment_Count |
| Bottom strip | Table | `dq_exceptions` grouped by Rule ID, Severity, Action Taken, count — with a Data Quality Score card |
| Filters | Team, Case Type, Month | |

Design note: the exception log lives on this page rather than in a hidden
governance tab, because a reader who is about to act on the root-cause chart
should be able to see that 140 resolved cases have no root cause recorded.

## Refresh and governance

- Source: `data/cases.db`, rebuilt by `python src/load_sqlite.py`.
- In production this would be a scheduled daily refresh against the case system's
  reporting replica, not the transactional database.
- Row-level security: none required here, since no analyst is identified by name
  and no member data exists. In a real deployment, team managers should see their
  own team's analyst detail and the equity page in full, so that the fairness
  argument is auditable by the people it judges.
