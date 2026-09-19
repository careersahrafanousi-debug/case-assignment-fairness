"""
Cleans case data, applies 16 data-quality rules, and calculates the three
signature measures for the control tower.

Case Complexity Score (0-100):
    30  Case type weight
    25  Priority weight
    20  Documentation gap
    15  Policy exception
    10  Historical rework risk
  Bands: Low 0-29, Moderate 30-54, High 55-74, Critical 75-100

Workload Balance Index:
    Team Weighted Workload / Average Weighted Workload
  <0.85 underutilized, 0.85-1.15 balanced, >1.15 overloaded

Assignment Accuracy Rate:
    Cases resolved without reassignment / Total cases x 100

The score weights are analyst judgement, not fitted to outcomes. Stated here and
in the docs so nobody treats them as a model.

Run after generate_data.py:  python src/clean_and_score.py
"""

import os

import numpy as np
import pandas as pd

RAW = os.path.join("data", "raw")
CLEAN = os.path.join("data", "clean")

VALID_STATUS = {"Resolved", "In Progress", "Pending Information"}
VALID_PRIORITY = {"Urgent", "High", "Standard", "Low"}

# Case type weight out of 30 - heavier work types score higher
TYPE_WEIGHT = {
    "Coverage Termination": 30,
    "Claims Dispute": 26,
    "Authorization Review": 22,
    "Billing Correction": 17,
    "Benefits Inquiry": 13,
    "Enrollment Change": 9,
}

# Priority weight out of 25
PRIORITY_WEIGHT = {"Urgent": 25, "High": 19, "Standard": 11, "Low": 5}

exceptions = []


def log(rule, record, severity, desc, action):
    exceptions.append({"Exception_ID": f"EX-{len(exceptions)+1:05d}", "Rule_ID": rule,
                       "Record_ID": record, "Severity": severity, "Description": desc,
                       "Action_Taken": action})


def clean_cases():
    df = pd.read_csv(os.path.join(RAW, "case_data_raw.csv"))
    n_in = len(df)

    # DQ-01 Case_ID unique
    for cid in df[df.duplicated("Case_ID", keep="first")]["Case_ID"]:
        log("DQ-01", cid, "High", "Duplicate Case_ID.", "First occurrence retained")
    df = df.drop_duplicates("Case_ID", keep="first").copy()

    # DQ-02 priority must normalize to an approved value
    raw_pri = df["Priority"].astype(str)
    df["Priority"] = raw_pri.str.strip().str.title()
    for cid in df.loc[raw_pri != df["Priority"], "Case_ID"]:
        log("DQ-02", cid, "Low", "Priority casing or whitespace did not match the standard.",
            "Normalized, record retained")
    bad = df[~df["Priority"].isin(VALID_PRIORITY)]
    for cid in bad["Case_ID"]:
        log("DQ-02", cid, "Critical", "Priority could not be mapped to an approved value.",
            "Excluded from reporting")
    df = df[df["Priority"].isin(VALID_PRIORITY)].copy()

    # DQ-03 status must be an approved value
    bad = df[~df["Current_Status"].isin(VALID_STATUS)]
    for cid, st in zip(bad["Case_ID"], bad["Current_Status"]):
        log("DQ-03", cid, "Critical", f"Unrecognized status '{st}'.", "Excluded from reporting")
    df = df[df["Current_Status"].isin(VALID_STATUS)].copy()

    for c in ["Created_Date", "Assigned_Date", "Resolved_Date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    # DQ-04 created date required
    for cid in df[df["Created_Date"].isna()]["Case_ID"]:
        log("DQ-04", cid, "Critical", "Created_Date missing or unparseable.",
            "Excluded from reporting")
    df = df[df["Created_Date"].notna()].copy()

    # DQ-05 assigned on or after created
    bad = df[df["Assigned_Date"].notna() & (df["Assigned_Date"] < df["Created_Date"])]
    for cid in bad["Case_ID"]:
        log("DQ-05", cid, "Critical", "Assigned_Date precedes Created_Date.",
            "Excluded from reporting")
    df = df[~df["Case_ID"].isin(bad["Case_ID"])].copy()

    # DQ-06 resolved on or after assigned
    bad = df[df["Resolved_Date"].notna() & (df["Resolved_Date"] < df["Assigned_Date"])]
    for cid in bad["Case_ID"]:
        log("DQ-06", cid, "Critical", "Resolved_Date precedes Assigned_Date.",
            "Excluded from reporting")
    df = df[~df["Case_ID"].isin(bad["Case_ID"])].copy()

    # DQ-07 resolved status requires a resolved date
    bad = df[(df["Current_Status"] == "Resolved") & (df["Resolved_Date"].isna())]
    for cid in bad["Case_ID"]:
        log("DQ-07", cid, "Critical",
            "Status is Resolved but Resolved_Date is missing; SLA cannot be evaluated.",
            "Excluded from reporting")
    df = df[~df["Case_ID"].isin(bad["Case_ID"])].copy()

    # DQ-08 open cases must not carry a resolved date
    bad = df[(df["Current_Status"] != "Resolved") & (df["Resolved_Date"].notna())]
    for cid in bad["Case_ID"]:
        log("DQ-08", cid, "High", "Open case carries a Resolved_Date.",
            "Resolved_Date nulled, record retained")
    df.loc[(df["Current_Status"] != "Resolved") & (df["Resolved_Date"].notna()),
           "Resolved_Date"] = pd.NaT

    # DQ-09 team must exist in reference data
    valid_team = set(pd.read_csv(os.path.join(RAW, "dim_team.csv"))["Team_ID"])
    bad = df[~df["Assigned_Team"].isin(valid_team)]
    for cid in bad["Case_ID"]:
        log("DQ-09", cid, "Critical", "Assigned_Team not found in team reference data.",
            "Excluded from reporting")
    df = df[df["Assigned_Team"].isin(valid_team)].copy()

    # DQ-10 analyst must exist and belong to the assigned team
    analysts = pd.read_csv(os.path.join(RAW, "dim_analyst.csv"))
    amap = dict(zip(analysts["Analyst_ID"], analysts["Team_ID"]))
    bad = df[~df["Assigned_Analyst"].isin(amap)]
    for cid in bad["Case_ID"]:
        log("DQ-10", cid, "High", "Assigned_Analyst not found in analyst reference data.",
            "Retained, excluded from analyst-level analysis")
    mismatch = df[df["Assigned_Analyst"].isin(amap)
                  & (df["Assigned_Analyst"].map(amap) != df["Assigned_Team"])]
    for cid in mismatch["Case_ID"]:
        log("DQ-10", cid, "Medium", "Assigned analyst does not belong to the assigned team.",
            "Retained, flagged")

    # DQ-11 case type must exist in reference data
    types = pd.read_csv(os.path.join(RAW, "dim_case_type.csv"))
    bad = df[~df["Case_Type"].isin(set(types["Case_Type"]))]
    for cid in bad["Case_ID"]:
        log("DQ-11", cid, "Critical", "Case_Type not found in reference data.",
            "Excluded from reporting")
    df = df[df["Case_Type"].isin(set(types["Case_Type"]))].copy()

    # DQ-12 reassignment count must be 0-6
    bad = df[~df["Reassignment_Count"].between(0, 6)]
    for cid in bad["Case_ID"]:
        log("DQ-12", cid, "High", "Reassignment_Count outside the valid range 0-6.",
            "Set to null; excluded from routing accuracy")
    df.loc[~df["Reassignment_Count"].between(0, 6), "Reassignment_Count"] = np.nan

    # DQ-13 SLA_Met must normalize to Yes/No on resolved cases
    raw_sla = df["SLA_Met"].copy()
    df["SLA_Met"] = df["SLA_Met"].replace({"Y": "Yes", "N": "No", "y": "Yes", "n": "No"})
    for cid in df.loc[raw_sla.ne(df["SLA_Met"]) & raw_sla.notna(), "Case_ID"]:
        log("DQ-13", cid, "Low", "SLA_Met used a single-letter code instead of Yes/No.",
            "Normalized, record retained")
    bad = df[(df["Current_Status"] == "Resolved") & (~df["SLA_Met"].isin(["Yes", "No"]))]
    for cid in bad["Case_ID"]:
        log("DQ-13", cid, "High", "SLA_Met missing or unrecognized on a resolved case.",
            "Recalculated from dates")

    # DQ-14 root cause expected on resolved cases
    bad = df[(df["Current_Status"] == "Resolved") & (df["Root_Cause"].isna())]
    for cid in bad["Case_ID"]:
        log("DQ-14", cid, "Medium", "Root_Cause not recorded on a resolved case.",
            "Set to Not Recorded")
    df.loc[(df["Current_Status"] == "Resolved") & (df["Root_Cause"].isna()),
           "Root_Cause"] = "Not Recorded"

    # DQ-15 SLA target must match the case type's published target
    df = df.merge(types[["Case_Type", "SLA_Target_Hours"]], on="Case_Type",
                  how="left", suffixes=("", "_Ref"))
    bad = df[df["SLA_Target_Hours"] != df["SLA_Target_Hours_Ref"]]
    for cid in bad["Case_ID"]:
        log("DQ-15", cid, "High", "SLA_Target_Hours disagrees with the case type reference.",
            "Reference value used")
    df["SLA_Target_Hours"] = df["SLA_Target_Hours_Ref"]
    df = df.drop(columns=["SLA_Target_Hours_Ref"])

    # DQ-16 reopened flag must be Yes/No
    df["Reopened_Flag"] = df["Reopened_Flag"].astype(str).str.strip().str.title()
    bad = df[~df["Reopened_Flag"].isin(["Yes", "No"])]
    for cid in bad["Case_ID"]:
        log("DQ-16", cid, "Medium", "Reopened_Flag is not Yes or No.", "Set to No")
    df.loc[~df["Reopened_Flag"].isin(["Yes", "No"]), "Reopened_Flag"] = "No"

    # derived measures - SLA always recalculated from dates, never trusted as stored
    df["Assignment_Lag_Hours"] = (
        (df["Assigned_Date"] - df["Created_Date"]).dt.total_seconds() / 3600).round(2)
    df["Resolution_Hours"] = (
        (df["Resolved_Date"] - df["Created_Date"]).dt.total_seconds() / 3600).round(2)
    df["Handling_Hours"] = (
        (df["Resolved_Date"] - df["Assigned_Date"]).dt.total_seconds() / 3600).round(2)

    resolved = df["Current_Status"] == "Resolved"
    df["SLA_Met_Calculated"] = None
    df.loc[resolved, "SLA_Met_Calculated"] = np.where(
        df.loc[resolved, "Resolution_Hours"] <= df.loc[resolved, "SLA_Target_Hours"],
        "Yes", "No")
    df["SLA_Breach_Hours"] = np.where(
        resolved & (df["SLA_Met_Calculated"] == "No"),
        (df["Resolution_Hours"] - df["SLA_Target_Hours"]).round(2), np.nan)

    return df, n_in


def complexity_score(df):
    s_type = df["Case_Type"].map(TYPE_WEIGHT).fillna(0)
    s_pri = df["Priority"].map(PRIORITY_WEIGHT).fillna(0)
    s_doc = np.where(df["Documentation_Gap"] == "Yes", 20, 0)
    s_pol = np.where(df["Policy_Exception"] == "Yes", 15, 0)
    s_rew = np.where(df["Historical_Rework_Risk"] == "Yes", 10, 0)

    df["Score_Case_Type"] = s_type
    df["Score_Priority"] = s_pri
    df["Score_Documentation_Gap"] = s_doc
    df["Score_Policy_Exception"] = s_pol
    df["Score_Rework_Risk"] = s_rew
    df["Complexity_Score"] = s_type + s_pri + s_doc + s_pol + s_rew
    df["Complexity_Band"] = pd.cut(df["Complexity_Score"], bins=[-1, 29, 54, 74, 100],
                                   labels=["Low", "Moderate", "High", "Critical"])
    return df


def workload_balance(df):
    """Weighted workload per team = total complexity score of every case the team
    handled in the period, divided by its available analyst hours. Indexed against
    the cross-team average.

    An earlier version used only currently-open cases. That was rejected: with a
    median resolution of about 43 hours the open backlog is under 200 cases across
    five teams, so the index swung wildly on a handful of records. Using the full
    period is stable and still answers the question, because headcount did not
    change during it. Open backlog is reported alongside as its own column rather
    than being folded into the index."""
    teams = pd.read_csv(os.path.join(RAW, "dim_team.csv"))

    agg = df.groupby("Assigned_Team").agg(
        Cases_Handled=("Case_ID", "count"),
        Weighted_Complexity=("Complexity_Score", "sum"),
        Avg_Complexity=("Complexity_Score", "mean"),
    ).reset_index().rename(columns={"Assigned_Team": "Team_ID"})

    open_by_team = (df[df["Current_Status"] != "Resolved"]
                    .groupby("Assigned_Team").size().rename("Open_Cases"))
    agg = agg.merge(open_by_team, left_on="Team_ID", right_index=True, how="left")

    agg = teams.merge(agg, on="Team_ID", how="left").fillna(
        {"Open_Cases": 0, "Cases_Handled": 0, "Weighted_Complexity": 0})
    agg["Daily_Capacity_Hours"] = agg["Analyst_Count"] * agg["Hours_Per_Analyst_Day"]
    agg["Workload_Per_Capacity_Hour"] = (agg["Weighted_Complexity"]
                                        / agg["Daily_Capacity_Hours"]).round(3)
    avg = agg["Workload_Per_Capacity_Hour"].mean()
    agg["Workload_Balance_Index"] = (agg["Workload_Per_Capacity_Hour"] / avg).round(3)
    agg["Balance_Status"] = np.select(
        [agg["Workload_Balance_Index"] < 0.85, agg["Workload_Balance_Index"] > 1.15],
        ["Underutilized", "Overloaded"], default="Balanced")

    # attach SLA and routing performance so the equity story has an outcome column
    perf = df.groupby("Assigned_Team").apply(
        lambda g: pd.Series({
            "Total_Cases": len(g),
            "Resolved_Cases": (g["Current_Status"] == "Resolved").sum(),
            "SLA_Compliance_Pct": round(
                100 * (g.loc[g["Current_Status"] == "Resolved", "SLA_Met_Calculated"]
                       == "Yes").mean(), 2),
            "Assignment_Accuracy_Pct": round(
                100 * (g["Reassignment_Count"] == 0).sum()
                / g["Reassignment_Count"].notna().sum(), 2),
            "Reopen_Rate_Pct": round(100 * (g["Reopened_Flag"] == "Yes").mean(), 2),
            "Median_Resolution_Hours": round(g["Resolution_Hours"].median(), 1),
        }), include_groups=False).reset_index().rename(columns={"Assigned_Team": "Team_ID"})

    return agg.merge(perf, on="Team_ID", how="left")


def main():
    os.makedirs(CLEAN, exist_ok=True)
    df, n_in = clean_cases()
    df = complexity_score(df)
    teams = workload_balance(df)

    ex = pd.DataFrame(exceptions)
    df.to_csv(os.path.join(CLEAN, "case_data.csv"), index=False)
    teams.to_csv(os.path.join(CLEAN, "team_workload.csv"), index=False)
    ex.to_csv(os.path.join(CLEAN, "dq_exceptions.csv"), index=False)

    blocked = (ex["Action_Taken"] == "Excluded from reporting").sum()
    resolved = df[df["Current_Status"] == "Resolved"]
    acc = 100 * (df["Reassignment_Count"] == 0).sum() / df["Reassignment_Count"].notna().sum()

    print(f"cases in:            {n_in}")
    print(f"cases out:           {len(df)}")
    print(f"exceptions:          {len(ex)}  (excluded {blocked})")
    print(f"Data Quality Score:  {100*(1-blocked/n_in):.2f}%")
    print()
    print(f"resolved cases:      {len(resolved)}")
    print(f"SLA compliance:      {100*(resolved['SLA_Met_Calculated']=='Yes').mean():.2f}%")
    print(f"Assignment Accuracy: {acc:.2f}%")
    print(f"reopen rate:         {100*(df['Reopened_Flag']=='Yes').mean():.2f}%")
    print(f"median resolution:   {resolved['Resolution_Hours'].median():.1f} hours")
    print()
    print("Complexity bands:")
    print(df["Complexity_Band"].value_counts().sort_index().to_string())
    print()
    print("Routing method vs assignment accuracy:")
    print(df.groupby("Routing_Method").apply(
        lambda g: round(100*(g["Reassignment_Count"] == 0).sum()
                        / g["Reassignment_Count"].notna().sum(), 2),
        include_groups=False).to_string())
    print()
    print("Team workload balance:")
    print(teams[["Team_ID", "Cases_Handled", "Open_Cases", "Avg_Complexity",
                 "Workload_Balance_Index", "Balance_Status", "SLA_Compliance_Pct",
                 "Assignment_Accuracy_Pct", "Median_Resolution_Hours"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
