# To-Be Process Map

Future state. Four new controls, all buildable without a new source system.

```mermaid
flowchart TD
    A[Case received] --> B[Case record created]
    B --> C[Required-fields gate<br/>documentation checklist at intake]

    C --> D{Checklist<br/>complete?}
    D -->|No| E[Hold at intake, request documents<br/>SLA clock not yet started]
    E --> C
    D -->|Yes| F[SLA clock starts<br/>target from reference data]

    F --> G[Complexity score calculated<br/>at intake, not after the fact]
    G --> H{Complexity band}

    H -->|High or Critical| I[Manual triage<br/>lead assigns deliberately]
    H -->|Low or Moderate| J[Auto-route<br/>rules engine]

    I --> K[Analyst takes ownership]
    J --> K

    K --> L{Right analyst?}
    L -->|No| M[Reassign with mandatory<br/>reason code]
    M --> N{Reason code}
    N -->|Misroute| O[Logged against routing accuracy<br/>feeds rules-engine tuning]
    N -->|Planned escalation| P[Logged as escalation<br/>excluded from accuracy denominator]
    O --> K
    P --> K

    L -->|Yes| Q[Analyst works the case]
    Q --> R{Policy exception<br/>required?}
    R -->|Yes| S[Escalate for approval<br/>clock pauses, pause logged]
    S --> Q
    R -->|No| T[Resolve case<br/>root cause mandatory to close]

    T --> U[SLA evaluated against<br/>the case type's own target<br/>on a business calendar]

    U --> V[Weekly workload equity review<br/>Balance Index + backlog days of work]
    U --> W[Control tower dashboard<br/>by case type, by team, by method]

    V --> X{Index outside<br/>0.85 to 1.15<br/>or backlog over 5 days?}
    X -->|Yes| Y[Rebalance queues or<br/>escalate target renegotiation]
    X -->|No| Z[No action]

    class C,F,G,I,M,N,T,U,V,W,X ctrl

    classDef pain fill:#ffe0e0,stroke:#c0392b,stroke-width:2px
    classDef ctrl fill:#e0f5e0,stroke:#27ae60,stroke-width:2px
```

## Controls introduced

| # | Control | Pain addressed | Expected effect |
|---|---|---|---|
| C-1 | Required-fields gate at intake, with the SLA clock starting only once the checklist passes | P-4, P-5 | Removes the largest root cause from the measured clock. Missing documentation drives 26.0% of resolved cases at 59.5 average hours |
| C-2 | Complexity score calculated at intake, used to select the routing path | P-1 | Routes the 3,088 High and Critical cases through the 83.83% accurate method instead of the 66.77% one. Modeled opportunity, subject to validation |
| C-3 | Mandatory reassignment reason code, splitting misroutes from planned escalations | P-2, P-3 | Makes Assignment Accuracy Rate a true measure instead of an upper bound on failure. Closes defect D-01 |
| C-4 | Root cause mandatory to close, plus a business calendar for SLA evaluation | P-6, P-8 | Closes defects D-02 and D-03. Makes the 140 unexplained resolutions impossible |
| C-5 | Weekly workload equity review using the Balance Index **and** backlog days of work together | P-9, P-7 | Would have surfaced TEAM-04's 8.74 days of queued work, which the index alone scores as balanced |
| C-6 | Reporting by case type against its own target, replacing the blended figure | P-7 | Exposes the 60.5 point spread between Authorization Review and Billing Correction that the blended 62.70% conceals |

## Sequencing

C-3 and C-4 are data-capture changes and should go first: they are cheap, they
close three defects, and every other control's measurement depends on them. C-6 is
a reporting change with no system dependency and can run in parallel. C-1 and C-2
are process changes affecting analyst behaviour and should follow, once C-3 makes
their effect measurable. C-5 is the governance routine that keeps the rest honest.

## What this does not fix

Re-baselining the Authorization Review SLA is not in this map, because it is a
commercial negotiation with a client rather than an internal process change. It
remains the single largest contributor to the gap — 73,906 of 180,810 total breach
hours — and no amount of process improvement closes a target that sits 65% below
the average time the work actually takes.
