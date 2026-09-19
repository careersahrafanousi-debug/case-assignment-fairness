# Executive Summary

**Case Assignment Fairness and SLA Control Tower**
ClearPath Case Services · 15,908 cases · 2026-01-02 to 2026-06-30

## The question, and the answer we did not expect

Leadership asked which team was dragging down a blended SLA figure that has sat
between 61% and 64% for six months. Two coaching cycles had already been spent on
that assumption.

**The answer is that no team is the problem.** Workload per available analyst hour
is near-equal across all five teams — indices of 0.715 to 1.190 around a mean of
1.000 — and the five teams' routing accuracy rates sit within 1.6 points of each
other. Yet SLA compliance ranges from 25.88% to 84.19%. A 58 point outcome spread
across teams with equivalent workload and equivalent routing skill is not a
performance problem.

## What is actually happening

**1. One SLA target was never achievable.** Authorization Review carries a 48-hour
target and takes 79.0 hours on average. Its compliance rate is 26.37%. It
generates 73,906 of the 180,810 total breach hours in the period — 41% of all
lateness from 14% of cases. Enrollment Change has the same problem in miniature:
30.9 hours against a 24-hour target, 44.69% compliance. These are the only two
case types whose average resolution time exceeds their own target, and they are the
only two below 60% compliance. The correlation is not subtle.

**2. Auto-routing is the largest controllable driver.** It handles 58% of volume
at 66.77% assignment accuracy. Manual triage handles 29% at 83.83% — a 17.1 point
gap — and reopens 1.5 points less often. Auto-routing buys 2.2 hours of assignment
speed and pays for it many times over.

**3. A reassignment is expensive and nobody was measuring it.** One reassignment
adds 20.8 hours to resolution, drops SLA compliance from 70.33% to 44.18%, and
nearly triples the reopen rate from 4.41% to 12.15%. 26.9% of cases are reassigned
at least once.

**4. Missing documentation is the biggest single root cause.** 4,090 resolved
cases, 26.0% of the total, at 59.5 average hours and 54.72% compliance. It is
found after assignment, when the case is already on the clock.

**5. Two things were tested and found not to matter.** Customer segment does not
predict service level (62.00% to 63.32% across four segments on equal complexity)
— there is no evidence of favouritism. Analyst tenure matters modestly: 57.60% for
0–1 year staff rising to 65.75% for 3+ years. An 8.2 point tenure gap is worth
onboarding attention; it does not explain a 58 point team gap.

## Recommendations

| # | Recommendation | Owner | Basis |
|---|---|---|---|
| 1 | Re-baseline the Authorization Review SLA, or introduce a clock-stop while awaiting external authorization | VP Case Operations, with the client | 26.37% compliance against a target 39% below actual average resolution time |
| 2 | Route Authorization Review and Claims Dispute volume through manual triage instead of auto-routing | Case Operations | Modeled opportunity of about 518 fewer first-time misroutes over six months. Expected impact subject to validation |
| 3 | Stop publishing a single blended SLA figure; report by case type against its own target, with the Workload Balance Index and backlog days of work alongside | Client Reporting | A 58 point team spread and a 60.5 point case-type spread are both invisible in the blended 62.70% |
| 4 | Move the documentation check to intake, with the SLA clock starting once the checklist passes | Case Operations | 26.0% of resolved cases cite missing documentation |
| 5 | Add a reassignment reason code and make root cause mandatory to close | Data Governance | Closes three measurement defects that limit every recommendation above |

Recommendation 5 should go first despite being the least visible. Until
reassignments carry a reason code, Assignment Accuracy Rate is an upper bound on
failure rather than a measurement of it, and recommendation 2 cannot be validated
after the fact.

## What this analysis cannot tell you

- **No savings figures.** Recommendation 2 is expressed as fewer misroutes, not
  dollars. The dataset has no rate or cost data and inventing one would make the
  most quotable number in this summary the least defensible.
- **Reassignment is treated as failure.** Legitimate escalations cannot be
  separated from misroutes without a reason code, so the 26.9% reassignment rate
  overstates routing failure by an unknown amount.
- **SLA is measured in elapsed clock hours, not business hours.** The source has
  no business calendar, so a case created Friday afternoon carries the weekend.
  This biases compliance downward and not evenly across case types.
- **The complexity score is judgement, not a model.** Its weights were not fitted
  to outcomes. It is monotonic against SLA compliance and reassignment rate, which
  is enough to band work for fair comparison and not enough to automate routing.
- **The data is fully synthetic.** The relationships reported here were built into
  the generator. What transfers is the method — the measures, the quality gate, the
  way a stated hypothesis was tested and rejected — not the conclusions.

## Data quality

16,055 rows in, 15,908 reportable, 577 exceptions logged, 92 records excluded,
Data Quality Score 99.43%. Critical failures were excluded and logged rather than
corrected: 34 cases marked Resolved with no resolution date could not be given a
plausible date without fabricating the SLA outcome the analysis exists to measure.

Five source defects are registered in
[07_data_quality_rules.md](07_data_quality_rules.md), the most consequential being
the absence of a business calendar and of a reassignment reason code. Neither is a
rule violation, because no rule can fire on a column that does not exist.
