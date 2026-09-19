# Business Requirements

Twenty-four requirements. Each has an ID, a priority, a source stakeholder, and
acceptance criteria that were tested — see [11_uat_test_cases.md](11_uat_test_cases.md).

Priority: **M** must have, **S** should have, **C** could have.

## Data acquisition and quality

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| BR-01 | M | The pipeline must be reproducible end to end from a fixed seed | Two consecutive clean runs produce byte-identical `data/clean/case_data.csv` |
| BR-02 | M | Every data-quality rule violation must be logged with rule ID, record ID, severity and action taken | `dq_exceptions.csv` has no null in any of those four columns |
| BR-03 | M | Records failing a Critical rule must be excluded from reporting, never corrected | Every exception with severity Critical has action `Excluded from reporting`; no such Case_ID appears in `case_data.csv` |
| BR-04 | M | Case_ID must be unique in the reporting layer | `SELECT COUNT(*) - COUNT(DISTINCT Case_ID) FROM case_data` returns 0 |
| BR-05 | M | A Data Quality Score must be published | Score = 1 − (excluded ÷ input rows), printed by the pipeline and stated in the README |
| BR-06 | M | The stored SLA_Met flag must not be used in any published measure | No query references `SLA_Met`; all SLA measures use `SLA_Met_Calculated` |
| BR-07 | S | Casing and whitespace variants in categorical fields must be normalised, not excluded | Priority and SLA_Met normalisations logged at Low severity with the record retained |
| BR-08 | S | Out-of-range numeric values must be nulled and excluded from the affected measure, not coerced to a boundary | Reassignment_Count outside 0–6 is null, and those records are out of the Assignment Accuracy denominator |
| BR-09 | S | Reference-data integrity must be enforced for team, analyst and case type | Every `case_data` row joins to `dim_team` and `dim_case_type`; analyst misses are retained and flagged, not dropped |

## Measures

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| BR-10 | M | A Case Complexity Score of 0–100 must be calculated for every reportable case | No null `Complexity_Score`; all values within 0–100 |
| BR-11 | M | The complexity score must be decomposable into its five components | Five component columns present; they sum exactly to `Complexity_Score` |
| BR-12 | M | The complexity score must be banded Low / Moderate / High / Critical | Band boundaries 0–29, 30–54, 55–74, 75–100; no null band |
| BR-13 | M | A Workload Balance Index must be published per team with a status band | Five rows in `team_workload`; index and one of Underutilized / Balanced / Overloaded on each |
| BR-14 | M | The Workload Balance Index must average to approximately 1.00 across teams | Mean of the five indices is 1.00 ± 0.01 |
| BR-15 | M | An Assignment Accuracy Rate must be published overall, by team and by routing method | All three breakdowns present in the query set and the dashboard spec |
| BR-16 | M | SLA outcome must be recalculated from dates against the case type's published target | `SLA_Met_Calculated` is Yes only when `Resolution_Hours <= SLA_Target_Hours` |
| BR-17 | S | SLA target must come from reference data, not from the transactional record | Disagreements logged as DQ-15; reference value used |
| BR-18 | S | Breach severity must be quantified, not just breach incidence | `SLA_Breach_Hours` populated for every breach and null otherwise |

## Reporting and governance

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| BR-19 | M | The single-underperforming-team hypothesis must be explicitly accepted or rejected | README states a conclusion with the team table as evidence |
| BR-20 | M | Analyst-level performance must not be published by individual | Analyst results appear only aggregated by tenure band |
| BR-21 | M | A dashboard specification must be complete enough to build without further analyst input | Model, relationships, DAX for every measure, and five page layouts all present |
| BR-22 | S | Open cases must be presented as an actionable queue ranked by lateness then complexity | Query 11 returns open cases ordered by hours past target, then complexity score |
| BR-23 | S | Equity must be tested against customer segment, and the result reported whether or not an effect is found | Segment query present; result reported in README including the null finding |
| BR-24 | C | Backlog pressure must be expressed in days of work, not case counts | `backlog_days_of_work` published per team in query 17 |

## Traceability

| Objective | Requirements |
|---|---|
| O-1 Quantify difficulty | BR-10, BR-11, BR-12 |
| O-2 Workload equity | BR-13, BR-14, BR-24 |
| O-3 Routing quality | BR-15, BR-08 |
| O-4 Test the hypothesis | BR-19, BR-16, BR-17, BR-18, BR-23 |
| O-5 Trustworthy record | BR-01 to BR-09 |
| O-6 Dashboard | BR-21, BR-22, BR-20 |

## Known requirements not met

| ID | Requirement | Why not met |
|---|---|---|
| BR-N1 | Business-hour SLA measurement | No business calendar in the source. Logged as defect D-02 |
| BR-N2 | Separate legitimate escalations from misroutes | No reassignment reason code exists. Logged as defect D-01 |
| BR-N3 | Root cause on every resolved case | 140 resolved cases have none. Logged as defect D-03 |

These are stated rather than quietly dropped because each one limits a
recommendation, and a reader needs to know which conclusions rest on them.
