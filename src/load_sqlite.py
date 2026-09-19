"""Loads cleaned case tables into SQLite for the analysis queries."""

import os
import sqlite3

import pandas as pd

DB = os.path.join("data", "cases.db")
TABLES = {
    "case_data": ("data", "clean", "case_data.csv"),
    "team_workload": ("data", "clean", "team_workload.csv"),
    "dq_exceptions": ("data", "clean", "dq_exceptions.csv"),
    "team_capacity": ("data", "raw", "team_capacity.csv"),
    "dim_team": ("data", "raw", "dim_team.csv"),
    "dim_analyst": ("data", "raw", "dim_analyst.csv"),
    "dim_case_type": ("data", "raw", "dim_case_type.csv"),
    "dim_date": ("data", "raw", "dim_date.csv"),
}


def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    for name, parts in TABLES.items():
        df = pd.read_csv(os.path.join(*parts))
        df.to_sql(name, con, if_exists="replace", index=False)
        print(f"{name:<18} {len(df):>6} rows")
    con.commit()
    con.close()
    print(f"\nwrote {DB}")


if __name__ == "__main__":
    main()
