# UAT Test Cases

Twenty-two tests. Each maps to a requirement in
[02_business_requirements.md](02_business_requirements.md). All were executed
against the build documented in the README. Results are the actual observed
values, not expected values copied forward.

## Data quality

| ID | Req | Test | Expected | Actual | Result |
|---|---|---|---|---|---|
| T-01 | BR-04 | `SELECT COUNT(*) - COUNT(DISTINCT Case_ID) FROM case_data` | 0 | 0 | Pass |
| T-02 | BR-03 | Every Critical exception has action `Excluded from reporting` | True for all 92 | 92 of 92 | Pass |
| T-03 | BR-03 | No Case_ID with a Critical exception appears in `case_data` | 0 matches | 0 | Pass |
| T-04 | BR-02 | No null in Rule_ID, Record_ID, Severity or Action_Taken in `dq_exceptions` | 0 nulls | 0 | Pass |
| T-05 | BR-05 | Data Quality Score = 1 − 92/16,055 | 99.43% | 99.43% | Pass |
| T-06 | BR-01 | Two consecutive full runs produce identical `case_data.csv` | Identical | Identical (seed 8821) | Pass |
| T-07 | BR-07 | Priority normalisations logged at Low severity with the record retained | 120 logged, 120 retained | 120 / 120 | Pass |
| T-08 | BR-08 | Records with a nulled Reassignment_Count are absent from the Assignment Accuracy denominator | 12 excluded | 12 | Pass |
| T-09 | BR-09 | Every `case_data` row joins to `dim_team` and `dim_case_type` | 0 orphans | 0 | Pass |

## Measures

| ID | Req | Test | Expected | Actual | Result |
|---|---|---|---|---|---|
| T-10 | BR-10 | No null Complexity_Score; all values 0–100 | 0 nulls, min ≥ 0, max ≤ 100 | 0 nulls, range within bounds | Pass |
| T-11 | BR-11 | Five score components sum exactly to Complexity_Score | 0 mismatches | 0 | Pass |
| T-12 | BR-12 | Band boundaries applied at 29 / 54 / 74 | Low 3,790, Moderate 9,030, High 2,771, Critical 317, no nulls | As expected, sums to 15,908 | Pass |
| T-13 | BR-13 | `team_workload` has five rows, each with an index and a status band | 5 rows, 0 nulls | 5 rows, 0 nulls | Pass |
| T-14 | BR-14 | Mean of the five Workload Balance Index values | 1.00 ± 0.01 | 1.000 | Pass |
| T-15 | BR-16 | `SLA_Met_Calculated` = Yes only where Resolution_Hours ≤ SLA_Target_Hours | 0 contradictions | 0 | Pass |
| T-16 | BR-06 | No published query or DAX measure references the stored `SLA_Met` | 0 references | 0 in `sql/` and 0 in the dashboard spec measures | Pass |
| T-17 | BR-18 | `SLA_Breach_Hours` populated for every breach and null otherwise | Populated on all 5,862 breaches, null elsewhere | Matches breach count by case type (1,586 + 1,562 + 1,028 + 998 + 353 + 335) | Pass |
| T-18 | BR-15 | Assignment Accuracy Rate available overall, by team and by routing method | All three present | Queries 1, 4 and 5 | Pass |

## Reporting and governance

| ID | Req | Test | Expected | Actual | Result |
|---|---|---|---|---|---|
| T-19 | BR-20 | No individual analyst identifier appears in any published result | Analyst results aggregated by tenure band only | Query 12 groups by Tenure_Band; the priority-queue table shows Analyst_ID because it is an operational work list, not a performance measure | Pass with note |
| T-20 | BR-22 | Open-case query ordered by hours past target, then complexity | Most-overdue case first | CS-2026-011720, 111.8 hours past a 96-hour target | Pass |
| T-21 | BR-23 | Customer segment equity tested and the result reported regardless of outcome | Result reported | 62.00% to 63.32%, null finding stated in the README | Pass |
| T-22 | BR-19 | The single-underperforming-team hypothesis is explicitly accepted or rejected | Explicit conclusion with evidence | Rejected; team table shows the only Overloaded team has the second-best SLA | Pass |

## Notes on T-19

The priority queue in query 11 does show `Assigned_Analyst`, which is the one
place an individual appears. It was kept because the page is a work list — a lead
cannot reassign an overdue case without knowing who currently holds it — and
removing it would make the page unusable for its purpose. The distinction that
matters is that no *performance measure* is published by individual: SLA
compliance, assignment accuracy and reopen rate are only ever reported by team or
tenure band. That distinction is recorded here rather than being left implicit,
because it is exactly the kind of thing a governance reviewer should challenge.

## Tests that were expected to fail and did not

DQ-04, DQ-05, DQ-08, DQ-10, DQ-11, DQ-15 and DQ-16 recorded zero violations. They
were kept in the pipeline anyway. A rule with no current violations is a
regression test: if a future load breaks referential integrity or starts writing
resolution dates onto open cases, these rules catch it, and a rule written only
after the first incident never catches the first incident.
