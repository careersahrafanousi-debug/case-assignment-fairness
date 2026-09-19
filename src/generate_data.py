"""
ClearPath Case Services (fictional) - synthetic case routing and SLA data.

Two tables:
  case_data     - one row per case, with routing, SLA, and outcome fields
  team_capacity - daily available hours and workload per team

Patterns built in deliberately:
  - auto-routed cases are reassigned more often than manually triaged ones
  - complexity drives both turnaround and reassignment
  - one team is chronically overloaded and its SLA performance suffers
  - reopened cases cluster on cases that were reassigned at least once
  - documentation gaps are the most common root cause

Dirty records are injected so the cleaning step earns its place.

Run:  python src/generate_data.py
"""

import os
import random
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

SEED = 8821
N_CASES = 16000
START = date(2026, 1, 2)
END = date(2026, 6, 30)
RAW = os.path.join("data", "raw")

# team: (analysts, hours per analyst per day, capability bias)
TEAMS = {
    "TEAM-01": (9, 7.5, "Benefits"),
    "TEAM-02": (7, 7.5, "Claims"),
    "TEAM-03": (6, 7.5, "Enrollment"),
    "TEAM-04": (5, 7.5, "Authorization"),
    "TEAM-05": (8, 7.5, "Billing"),
}

CASE_TYPES = {
    # type: (base hours of work, SLA target hours, owning team)
    "Benefits Inquiry":      (3.5, 48, "TEAM-01"),
    "Claims Dispute":        (6.0, 72, "TEAM-02"),
    "Enrollment Change":     (2.5, 24, "TEAM-03"),
    "Authorization Review":  (5.0, 48, "TEAM-04"),
    "Billing Correction":    (4.0, 72, "TEAM-05"),
    "Coverage Termination":  (7.5, 96, "TEAM-01"),
}

PRIORITIES = {"Urgent": 30, "High": 22, "Standard": 12, "Low": 5}

ROOT_CAUSES = ["Missing documentation", "Policy exception required", "Incorrect initial routing",
               "System data gap", "External party delay", "Complex eligibility",
               "No issue identified"]

SEGMENTS = ["Enterprise", "Mid-Market", "Small Group", "Individual"]


def build_analysts():
    rows = []
    aid = 1
    for team, (n, hrs, bias) in TEAMS.items():
        for _ in range(n):
            rows.append({
                "Analyst_ID": f"AN-{aid:03d}",
                "Team_ID": team,
                "Hours_Per_Day": hrs,
                # tenure drives how much a case slows down or speeds up
                "Tenure_Band": random.choices(["0-1 yr", "1-3 yr", "3+ yr"],
                                              weights=[.3, .4, .3])[0],
            })
            aid += 1
    return pd.DataFrame(rows)


def build_cases(analysts):
    rows = []
    span = (END - START).days
    for i in range(1, N_CASES + 1):
        ctype = random.choices(list(CASE_TYPES),
                               weights=[.24, .19, .18, .14, .16, .09])[0]
        base_hours, sla_hours, owning_team = CASE_TYPES[ctype]
        priority = random.choices(list(PRIORITIES), weights=[.09, .22, .53, .16])[0]

        created = START + timedelta(days=random.randint(0, span))
        created_dt = datetime.combine(created, datetime.min.time()) + timedelta(
            hours=random.randint(7, 17), minutes=random.choice([0, 15, 30, 45]))

        # routing method - auto routing is faster to assign but less accurate
        routing = random.choices(["Auto-Routed", "Manual Triage", "Analyst Self-Select"],
                                 weights=[.58, .30, .12])[0]

        doc_gap = random.random() < 0.31
        policy_exception = random.random() < 0.18
        rework_risk = random.random() < 0.14

        # reassignment probability depends on routing method
        p_reassign = {"Auto-Routed": 0.30, "Manual Triage": 0.13,
                      "Analyst Self-Select": 0.20}[routing]
        if doc_gap:
            p_reassign += 0.07
        if policy_exception:
            p_reassign += 0.05
        reassign = 0
        while reassign < 4 and random.random() < p_reassign:
            reassign += 1
            p_reassign *= 0.45

        # assignment is usually to the owning team, sometimes not
        if random.random() < (0.16 if routing == "Auto-Routed" else 0.06):
            team = random.choice([t for t in TEAMS if t != owning_team])
        else:
            team = owning_team
        pool = analysts[analysts["Team_ID"] == team]
        analyst = pool.sample(1).iloc[0]

        assign_lag_h = {"Auto-Routed": 0.4, "Manual Triage": 3.5,
                        "Analyst Self-Select": 6.0}[routing]
        assigned_dt = created_dt + timedelta(hours=abs(np.random.normal(assign_lag_h, 1.5)))

        # work hours, then elapsed hours
        work = base_hours * random.uniform(0.7, 1.4)
        if doc_gap:
            work *= 1.5
        if policy_exception:
            work *= 1.35
        work *= {"0-1 yr": 1.25, "1-3 yr": 1.0, "3+ yr": 0.85}[analyst["Tenure_Band"]]
        work += reassign * 2.5

        # TEAM-04 is chronically overloaded, so its queue time is worse
        queue_mult = 1.9 if team == "TEAM-04" else random.uniform(0.9, 1.35)
        urgency_mult = {"Urgent": 0.55, "High": 0.75, "Standard": 1.0, "Low": 1.4}[priority]
        # Elapsed time is a multiple of touch time: cases sit in queues far
        # longer than anyone works on them, which is the whole reason SLAs
        # get missed.
        elapsed = work * queue_mult * urgency_mult * random.uniform(3.0, 10.0)

        resolved_dt = assigned_dt + timedelta(hours=elapsed)

        if resolved_dt.date() > END:
            status = random.choices(["In Progress", "Pending Information"],
                                    weights=[.7, .3])[0]
            resolved_dt = None
            sla_met = None
            elapsed_actual = None
        else:
            status = "Resolved"
            elapsed_actual = (resolved_dt - created_dt).total_seconds() / 3600
            sla_met = "Yes" if elapsed_actual <= sla_hours else "No"

        if status == "Resolved":
            if doc_gap and random.random() < 0.55:
                cause = "Missing documentation"
            elif policy_exception and random.random() < 0.6:
                cause = "Policy exception required"
            elif reassign > 0 and random.random() < 0.45:
                cause = "Incorrect initial routing"
            else:
                cause = random.choices(ROOT_CAUSES, weights=[.14, .1, .1, .18, .17, .13, .18])[0]
        else:
            cause = None

        # reopened cases cluster where routing went wrong
        p_reopen = 0.04 + (0.09 if reassign > 0 else 0) + (0.05 if rework_risk else 0)
        reopened = "Yes" if (status == "Resolved" and random.random() < p_reopen) else "No"

        rows.append({
            "Case_ID": f"CS-2026-{i:06d}",
            "Created_Date": created_dt.strftime("%Y-%m-%d %H:%M"),
            "Assigned_Date": assigned_dt.strftime("%Y-%m-%d %H:%M"),
            "Resolved_Date": resolved_dt.strftime("%Y-%m-%d %H:%M") if resolved_dt else None,
            "Case_Type": ctype,
            "Priority": priority,
            "Assigned_Team": team,
            "Assigned_Analyst": analyst["Analyst_ID"],
            "Routing_Method": routing,
            "Reassignment_Count": reassign,
            "Current_Status": status,
            "SLA_Target_Hours": sla_hours,
            "SLA_Met": sla_met,
            "Root_Cause": cause,
            "Reopened_Flag": reopened,
            "Customer_Segment": random.choices(SEGMENTS, weights=[.18, .27, .34, .21])[0],
            # inputs to the complexity score, captured at intake
            "Documentation_Gap": "Yes" if doc_gap else "No",
            "Policy_Exception": "Yes" if policy_exception else "No",
            "Historical_Rework_Risk": "Yes" if rework_risk else "No",
            "Estimated_Work_Hours": round(work, 2),
        })
    return pd.DataFrame(rows)


def build_team_capacity(cases, analysts):
    """Daily available hours per team from headcount, and the workload actually
    sitting with that team, so the Workload Balance Index has real inputs."""
    cases = cases.copy()
    cases["Created_Day"] = pd.to_datetime(cases["Created_Date"]).dt.date
    cases["Resolved_Day"] = pd.to_datetime(cases["Resolved_Date"]).dt.date

    rows = []
    for day in pd.date_range(START, END, freq="D").date:
        for team, (n, hrs, _) in TEAMS.items():
            weekend = day.weekday() >= 5
            available = 0.0 if weekend else n * hrs
            assigned_today = cases[(cases["Created_Day"] == day)
                                   & (cases["Assigned_Team"] == team)]
            # open backlog: created on or before today, not resolved before today
            open_mask = ((cases["Assigned_Team"] == team)
                         & (cases["Created_Day"] <= day)
                         & ((cases["Resolved_Day"].isna()) | (cases["Resolved_Day"] > day)))
            backlog = cases[open_mask]
            rows.append({
                "Team_ID": team,
                "Date": day.isoformat(),
                "Analyst_Count": n,
                "Available_Hours": round(available, 1),
                "Assigned_Case_Count": len(assigned_today),
                "Average_Complexity": round(assigned_today["Estimated_Work_Hours"].mean(), 2)
                if len(assigned_today) else None,
                "Open_Backlog": len(backlog),
                "Backlog_Work_Hours": round(backlog["Estimated_Work_Hours"].sum(), 1),
            })
    return pd.DataFrame(rows)


def dirty(cases):
    dupes = cases.sample(55, random_state=31)
    cases = pd.concat([cases, dupes], ignore_index=True)

    # SLA_Met typed inconsistently
    idx = cases.sample(160, random_state=32).index
    cases.loc[idx, "SLA_Met"] = cases.loc[idx, "SLA_Met"].map({"Yes": "Y", "No": "N"})

    # resolved before assigned
    idx = cases[cases["Resolved_Date"].notna()].sample(26, random_state=33).index
    cases.loc[idx, "Resolved_Date"] = "2025-12-20 09:00"

    # resolved status with no resolved date
    idx = cases[cases["Current_Status"] == "Resolved"].sample(34, random_state=34).index
    cases.loc[idx, "Resolved_Date"] = None

    # priority spelling drift
    idx = cases.sample(120, random_state=35).index
    cases.loc[idx, "Priority"] = cases.loc[idx, "Priority"].str.upper()

    # unknown team code
    idx = cases.sample(17, random_state=36).index
    cases.loc[idx, "Assigned_Team"] = "TEAM-99"

    # negative reassignment count
    idx = cases.sample(12, random_state=37).index
    cases.loc[idx, "Reassignment_Count"] = -1

    # blank root cause on resolved cases
    idx = cases[cases["Current_Status"] == "Resolved"].sample(140, random_state=38).index
    cases.loc[idx, "Root_Cause"] = None

    # unmapped status value
    idx = cases.sample(15, random_state=39).index
    cases.loc[idx, "Current_Status"] = "ON HOLD - LEGAL"

    return cases.sample(frac=1, random_state=40).reset_index(drop=True)


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    os.makedirs(RAW, exist_ok=True)

    analysts = build_analysts()
    cases = build_cases(analysts)
    capacity = build_team_capacity(cases, analysts)
    cases_dirty = dirty(cases)

    dim_team = pd.DataFrame([
        {"Team_ID": t, "Team_Name": f"Case Team {t[-2:]}", "Analyst_Count": n,
         "Primary_Capability": bias, "Hours_Per_Analyst_Day": hrs}
        for t, (n, hrs, bias) in TEAMS.items()])

    dim_case_type = pd.DataFrame([
        {"Case_Type": c, "Base_Work_Hours": h, "SLA_Target_Hours": s, "Owning_Team": t}
        for c, (h, s, t) in CASE_TYPES.items()])

    dates = pd.date_range(START, END, freq="D")
    dim_date = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"), "Year": dates.year, "Month": dates.month,
        "Month_Name": dates.strftime("%B"), "Quarter": dates.quarter,
        "Week_Of_Year": dates.isocalendar().week.values,
        "Day_Name": dates.strftime("%A"),
        "Is_Weekend": np.where(dates.dayofweek >= 5, "Yes", "No"),
    })

    cases_dirty.to_csv(os.path.join(RAW, "case_data_raw.csv"), index=False)
    capacity.to_csv(os.path.join(RAW, "team_capacity.csv"), index=False)
    analysts.to_csv(os.path.join(RAW, "dim_analyst.csv"), index=False)
    dim_team.to_csv(os.path.join(RAW, "dim_team.csv"), index=False)
    dim_case_type.to_csv(os.path.join(RAW, "dim_case_type.csv"), index=False)
    dim_date.to_csv(os.path.join(RAW, "dim_date.csv"), index=False)

    with pd.ExcelWriter(os.path.join(RAW, "04_synthetic_raw_data.xlsx")) as xl:
        cases_dirty.head(5000).to_excel(xl, sheet_name="case_data", index=False)
        capacity.to_excel(xl, sheet_name="team_capacity", index=False)
        dim_team.to_excel(xl, sheet_name="dim_team", index=False)
        dim_case_type.to_excel(xl, sheet_name="dim_case_type", index=False)
        analysts.to_excel(xl, sheet_name="dim_analyst", index=False)

    print(f"analysts:        {len(analysts)}")
    print(f"cases:           {len(cases_dirty)} rows (55 duplicates injected)")
    print(f"capacity rows:   {len(capacity)}")
    print()
    print(cases_dirty["Current_Status"].value_counts().to_string())
    print()
    print("Routing method mix:")
    print(cases_dirty["Routing_Method"].value_counts().to_string())


if __name__ == "__main__":
    main()
