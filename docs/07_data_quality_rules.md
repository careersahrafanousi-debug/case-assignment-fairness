# Data Quality Rules

Sixteen rules, implemented in `src/clean_and_score.py` in the order below. Every
violation is written to `data/clean/dq_exceptions.csv`.

## Severity policy

| Severity | Meaning | Action |
|---|---|---|
| Critical | The record cannot be measured without inventing a value | Exclude from reporting, log it |
| High | A measure is affected but the record is still usable elsewhere | Retain, null the affected field, exclude from that measure only |
| Medium | Descriptive quality issue, no measure affected | Retain, substitute an explicit placeholder |
| Low | Formatting only | Normalise, retain, log so the source defect stays visible |

The rule that matters most: **Critical records are excluded, never corrected.** A
case with status Resolved and no resolution date cannot be given a plausible
resolution date without fabricating the answer the SLA measure is meant to
produce. Excluding 34 records and saying so is honest; guessing 34 dates is not.

## Rules

| Rule | Field | Test | Severity | Action | Violations |
|---|---|---|---|---|---|
| DQ-01 | Case_ID | Must be unique | High | First occurrence retained, later ones dropped | 55 |
| DQ-02 | Priority | Must map to Urgent / High / Standard / Low after trimming and title-casing | Low (normalised) / Critical (unmappable) | Normalise and retain, or exclude | 120 normalised, 0 unmappable |
| DQ-03 | Current_Status | Must be Resolved / In Progress / Pending Information | Critical | Exclude from reporting | 15 |
| DQ-04 | Created_Date | Must be present and parseable | Critical | Exclude from reporting | 0 |
| DQ-05 | Assigned_Date | Must be ≥ Created_Date | Critical | Exclude from reporting | 0 |
| DQ-06 | Resolved_Date | Must be ≥ Assigned_Date | Critical | Exclude from reporting | 26 |
| DQ-07 | Resolved_Date | Must be present when status is Resolved | Critical | Exclude from reporting | 34 |
| DQ-08 | Resolved_Date | Must be absent when status is not Resolved | High | Null the date, retain the record | 0 |
| DQ-09 | Assigned_Team | Must exist in `dim_team` | Critical | Exclude from reporting | 17 |
| DQ-10 | Assigned_Analyst | Must exist in `dim_analyst` and belong to the assigned team | High / Medium | Retain and flag; exclude from analyst-level analysis | 0 |
| DQ-11 | Case_Type | Must exist in `dim_case_type` | Critical | Exclude from reporting | 0 |
| DQ-12 | Reassignment_Count | Must be an integer 0–6 | High | Null it; exclude from the Assignment Accuracy denominator | 12 |
| DQ-13 | SLA_Met | Must be Yes or No on a resolved case | Low (single-letter code) / High (missing) | Normalise, or recalculate from dates | 158 normalised |
| DQ-14 | Root_Cause | Expected on a resolved case | Medium | Set to `Not Recorded` | 140 |
| DQ-15 | SLA_Target_Hours | Must match the case type's published target | High | Use the reference value | 0 |
| DQ-16 | Reopened_Flag | Must be Yes or No | Medium | Set to No | 0 |

Rules showing zero violations are still implemented and still run. They are the
regression tests: DQ-05 firing on a future load means something changed upstream,
and a rule that only exists once a defect appears never catches the first one.

## Results

| Metric | Value |
|---|---|
| Input rows | 16,055 |
| Reportable rows | 15,908 |
| Exceptions logged | 577 |
| Records excluded | 92 |
| **Data Quality Score** | **99.43%** |

```
Data Quality Score = 1 - (records excluded / input rows)
                   = 1 - (92 / 16,055)
                   = 99.43%
```

### By rule

| Rule | Severity | Action | Count |
|---|---|---|---|
| DQ-13 | Low | Normalized, record retained | 158 |
| DQ-14 | Medium | Set to Not Recorded | 140 |
| DQ-02 | Low | Normalized, record retained | 120 |
| DQ-01 | High | First occurrence retained | 55 |
| DQ-07 | Critical | Excluded from reporting | 34 |
| DQ-06 | Critical | Excluded from reporting | 26 |
| DQ-09 | Critical | Excluded from reporting | 17 |
| DQ-03 | Critical | Excluded from reporting | 15 |
| DQ-12 | High | Set to null; excluded from routing accuracy | 12 |

## What the score does not tell you

99.43% looks reassuring and is partly misleading, in the same way any
record-level completeness figure is. Three points a reader should hold onto:

1. The score counts *excluded* records only. The 278 Low-severity normalisations
   and 140 missing root causes are real source defects that the score does not
   penalise at all.
2. 140 resolved cases with no root cause is 0.9% of resolved volume, which sounds
   trivial, but root cause is the field that drives recommendation 4. A 0.9% gap
   in a critical analytical field is more consequential than a 0.9% gap in a
   descriptive one, and a single blended score cannot express that.
3. The most serious quality problems in this dataset are not rule violations at
   all. No business calendar and no reassignment reason code are *absent fields*.
   No rule can fire on a column that does not exist, so they are recorded as
   defects D-01 and D-02 instead.

## Defect register

| ID | Defect | Impact | Recommendation |
|---|---|---|---|
| D-01 | No reassignment reason code | Legitimate escalations cannot be separated from misroutes, so Assignment Accuracy Rate overstates failure | Add a mandatory reason code on reassignment |
| D-02 | No business calendar | Business-hour SLA cannot be computed; elapsed-hour SLA penalises weekend cases and biases compliance downward non-uniformly | Add a business-hours calendar table |
| D-03 | Root_Cause optional on resolution | 140 resolved cases have no cause, weakening the largest-root-cause finding | Make Root_Cause mandatory to close a case |
| D-04 | SLA_Target_Hours duplicated on the transactional record | Creates a second version of a governed value that can drift from reference data | Remove the column; join to `dim_case_type` |
| D-05 | Reassignment_Count accepts negatives | Twelve records held impossible values, showing no source-side validation | Add a non-negative constraint at entry |
