# Project Charter

**Project.** Case Assignment Fairness and SLA Control Tower
**Organisation.** ClearPath Case Services (fictional)
**Period analysed.** 2026-01-02 to 2026-06-30
**Sponsor.** VP, Case Operations
**Analyst.** Portfolio author
**Status.** Complete

## Background

ClearPath resolves member and provider case work for health-plan clients under
contractual service levels ranging from 24 to 96 hours by case type. The blended
monthly SLA compliance figure reported to clients has sat between 61% and 64% for
six consecutive months despite two coaching interventions.

The sponsor's stated hypothesis entering this project was that a single
underperforming team was responsible. The reporting available could not test that
hypothesis, because it contained no measure of how difficult each team's work was
and no measure of whether cases reached the right analyst first time.

## Problem statement

Leadership cannot tell whether the SLA gap is a performance problem, a workload
distribution problem, a routing problem, or a target-setting problem. Without
that distinction, any intervention is a guess. Two coaching cycles have already
been spent on the assumption it is a performance problem, with no movement in the
blended figure.

## Objectives

| # | Objective | Success measure |
|---|---|---|
| O-1 | Quantify case difficulty so teams can be compared fairly | Case Complexity Score published for 100% of reportable cases |
| O-2 | Measure whether workload is distributed equitably across teams | Workload Balance Index published per team with a stated band |
| O-3 | Measure routing quality | Assignment Accuracy Rate published overall, by team and by routing method |
| O-4 | Determine whether the single-underperforming-team hypothesis holds | Explicit accept/reject with supporting evidence |
| O-5 | Establish a trustworthy case record | Data Quality Score above 99% with every exception logged and actioned |
| O-6 | Specify a dashboard leadership can act from weekly | Five-page specification buildable without further analyst input |

## Deliverables

1. Reproducible pipeline: synthetic data generation, cleaning and scoring, SQLite load.
2. Sixteen-rule data-quality layer with a published exception log.
3. Eighteen analysis queries.
4. Five-page dashboard specification with DAX.
5. Business requirements with acceptance criteria, UAT test cases, as-is and to-be process maps.
6. Executive summary with findings and recommendations.

## In scope

- Cases created within the six-month period, all five teams, all six case types.
- Assignment, reassignment, resolution, reopen, root cause and SLA outcome.
- Team-level and tenure-band-level aggregation.

## Out of scope

- Individual performance management or any named-analyst ranking.
- Client contract renegotiation, though a recommendation to consider one is made.
- Cost, staffing cost or headcount modelling.
- Any change requiring new fields to be captured in the source system.
- Forecasting future volume.

## Assumptions

| # | Assumption | If wrong |
|---|---|---|
| A-1 | Team headcount was stable across the period | Period-level Workload Balance Index becomes non-comparable |
| A-2 | Elapsed-hour SLA is an acceptable proxy for the contractual measure | Compliance figures shift; ranking between case types may not |
| A-3 | The stored SLA_Met flag is unreliable and must be recalculated | If the flag were reliable, 158 normalisations and the recalculation step would be unnecessary |
| A-4 | A reassignment indicates a routing miss | Assignment Accuracy Rate overstates failure by the share of legitimate escalations |
| A-5 | Complexity weights set by judgement are adequate for banding, not for routing rules | Score cannot be used as an automated routing input |

## Risks

| # | Risk | Likelihood | Impact | Response |
|---|---|---|---|---|
| R-1 | Teams reject the Workload Balance Index as unfair | Medium | High | Publish the formula, the inputs per team, and backlog days of work alongside it |
| R-2 | Finding that the SLA target is unachievable is read as excuse-making | Medium | High | Show average resolution time against target for all six case types, not just the worst |
| R-3 | Complexity score is treated as a validated model | High | Medium | State the unfitted-weights limitation in the README, the dictionary and the executive summary |
| R-4 | Excluded records are assumed to be hidden bad news | Low | Medium | Log every exclusion with rule, severity and reason; report the count in the headline |
| R-5 | Recommendation 2 is quoted as a savings figure | Medium | Medium | Express it only as fewer misroutes, with the population caveat attached |

## Constraints

- No source-system changes available, so every measure must be derivable from
  fields already captured.
- No business calendar in the source, so business-hour SLA cannot be computed.
- No reassignment reason code, so escalations cannot be separated from misroutes.

## Approval

Charter accepted by the sponsor on the basis that the project would report
whatever the data showed, including a result that contradicted the original
hypothesis. It did.
