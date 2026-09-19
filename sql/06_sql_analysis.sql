-- Case Assignment Fairness and SLA Control Tower
-- ClearPath Case Services (fictional org, fully synthetic data)
-- SQLite dialect.

--------------------------------------------------------------------
-- 1. Control tower summary
--------------------------------------------------------------------
SELECT COUNT(*)                                                          AS total_cases,
       SUM(CASE WHEN Current_Status = 'Resolved' THEN 1 ELSE 0 END)       AS resolved,
       SUM(CASE WHEN Current_Status <> 'Resolved' THEN 1 ELSE 0 END)      AS open_cases,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                 AS sla_compliance_pct,
       ROUND(100.0 * SUM(CASE WHEN Reassignment_Count = 0 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Reassignment_Count IS NOT NULL
                               THEN 1 ELSE 0 END), 0), 2)                 AS assignment_accuracy_pct,
       ROUND(100.0 * SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                              AS reopen_rate_pct,
       ROUND(AVG(Resolution_Hours), 1)                                    AS avg_resolution_hours,
       ROUND(AVG(Assignment_Lag_Hours), 2)                                AS avg_assignment_lag_hours
FROM case_data;


--------------------------------------------------------------------
-- 2. SLA performance by case type against its own target
--------------------------------------------------------------------
SELECT Case_Type,
       MAX(SLA_Target_Hours)                                              AS sla_target_hours,
       COUNT(*)                                                           AS cases,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                 AS sla_compliance_pct,
       ROUND(AVG(Resolution_Hours), 1)                                    AS avg_resolution_hours,
       ROUND(AVG(SLA_Breach_Hours), 1)                                    AS avg_breach_hours
FROM case_data
GROUP BY Case_Type
ORDER BY sla_compliance_pct;


--------------------------------------------------------------------
-- 3. SLA performance by priority - are urgent cases actually faster?
--------------------------------------------------------------------
SELECT Priority,
       COUNT(*)                                                           AS cases,
       ROUND(AVG(Resolution_Hours), 1)                                    AS avg_resolution_hours,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                 AS sla_compliance_pct
FROM case_data
GROUP BY Priority
ORDER BY avg_resolution_hours;


--------------------------------------------------------------------
-- 4. Workload equity - the index alongside the outcomes
--------------------------------------------------------------------
SELECT w.Team_ID,
       t.Primary_Capability,
       w.Analyst_Count,
       w.Cases_Handled,
       w.Open_Cases,
       ROUND(w.Avg_Complexity, 1)                                         AS avg_complexity,
       w.Workload_Balance_Index,
       w.Balance_Status,
       w.SLA_Compliance_Pct,
       w.Assignment_Accuracy_Pct,
       w.Reopen_Rate_Pct,
       w.Median_Resolution_Hours
FROM team_workload w
JOIN dim_team t ON t.Team_ID = w.Team_ID
ORDER BY w.SLA_Compliance_Pct;


--------------------------------------------------------------------
-- 5. Routing accuracy by method - the core fairness question
--------------------------------------------------------------------
SELECT Routing_Method,
       COUNT(*)                                                           AS cases,
       ROUND(100.0 * SUM(CASE WHEN Reassignment_Count = 0 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Reassignment_Count IS NOT NULL
                               THEN 1 ELSE 0 END), 0), 2)                 AS assignment_accuracy_pct,
       ROUND(AVG(Reassignment_Count), 3)                                  AS avg_reassignments,
       ROUND(AVG(Assignment_Lag_Hours), 2)                                AS avg_assignment_lag_hours,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                 AS sla_compliance_pct,
       ROUND(100.0 * SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                              AS reopen_rate_pct
FROM case_data
GROUP BY Routing_Method
ORDER BY assignment_accuracy_pct;


--------------------------------------------------------------------
-- 6. What does a reassignment cost?
--------------------------------------------------------------------
SELECT Reassignment_Count,
       COUNT(*)                                                           AS cases,
       ROUND(AVG(Resolution_Hours), 1)                                    AS avg_resolution_hours,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                 AS sla_compliance_pct,
       ROUND(100.0 * SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                              AS reopen_rate_pct
FROM case_data
WHERE Reassignment_Count IS NOT NULL
GROUP BY Reassignment_Count
ORDER BY Reassignment_Count;


--------------------------------------------------------------------
-- 7. Complexity band vs outcome - does the score predict anything?
--------------------------------------------------------------------
SELECT Complexity_Band,
       COUNT(*)                                                           AS cases,
       ROUND(AVG(Complexity_Score), 1)                                    AS avg_score,
       ROUND(AVG(Resolution_Hours), 1)                                    AS avg_resolution_hours,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                 AS sla_compliance_pct,
       ROUND(100.0 * SUM(CASE WHEN Reassignment_Count > 0 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Reassignment_Count IS NOT NULL
                               THEN 1 ELSE 0 END), 0), 2)                 AS reassigned_pct,
       ROUND(100.0 * SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                              AS reopen_rate_pct
FROM case_data
GROUP BY Complexity_Band
ORDER BY avg_score;


--------------------------------------------------------------------
-- 8. Is complexity distributed evenly across teams?
--------------------------------------------------------------------
SELECT Assigned_Team,
       COUNT(*)                                                           AS cases,
       SUM(CASE WHEN Complexity_Band = 'Critical' THEN 1 ELSE 0 END)       AS critical,
       SUM(CASE WHEN Complexity_Band = 'High' THEN 1 ELSE 0 END)           AS high,
       SUM(CASE WHEN Complexity_Band = 'Moderate' THEN 1 ELSE 0 END)       AS moderate,
       SUM(CASE WHEN Complexity_Band = 'Low' THEN 1 ELSE 0 END)            AS low,
       ROUND(100.0 * SUM(CASE WHEN Complexity_Band IN ('High', 'Critical')
                              THEN 1 ELSE 0 END) / COUNT(*), 1)           AS pct_high_or_critical
FROM case_data
GROUP BY Assigned_Team
ORDER BY pct_high_or_critical DESC;


--------------------------------------------------------------------
-- 9. Root cause of resolved cases, with the rework they carry
--------------------------------------------------------------------
SELECT Root_Cause,
       COUNT(*)                                                           AS cases,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM case_data
                                 WHERE Current_Status = 'Resolved'), 1)   AS pct_of_resolved,
       ROUND(AVG(Resolution_Hours), 1)                                    AS avg_resolution_hours,
       ROUND(100.0 * SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                              AS reopen_rate_pct,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                              AS sla_compliance_pct
FROM case_data
WHERE Current_Status = 'Resolved'
GROUP BY Root_Cause
ORDER BY cases DESC;


--------------------------------------------------------------------
-- 10. Reopened cases - where does rework come from?
--------------------------------------------------------------------
SELECT Routing_Method,
       Complexity_Band,
       COUNT(*)                                                           AS cases,
       SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)              AS reopened,
       ROUND(100.0 * SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                              AS reopen_rate_pct
FROM case_data
GROUP BY Routing_Method, Complexity_Band
ORDER BY reopen_rate_pct DESC;


--------------------------------------------------------------------
-- 11. Priority queue - open cases ranked for action
--------------------------------------------------------------------
SELECT Case_ID, Case_Type, Priority, Assigned_Team, Assigned_Analyst,
       Complexity_Score, Complexity_Band, Current_Status,
       SLA_Target_Hours,
       ROUND((julianday('2026-06-30') - julianday(Created_Date)) * 24, 1)  AS age_hours,
       ROUND((julianday('2026-06-30') - julianday(Created_Date)) * 24
             - SLA_Target_Hours, 1)                                        AS hours_past_target,
       Reassignment_Count, Customer_Segment
FROM case_data
WHERE Current_Status <> 'Resolved'
ORDER BY hours_past_target DESC, Complexity_Score DESC
LIMIT 50;


--------------------------------------------------------------------
-- 12. Analyst-level view, aggregated so no individual is singled out
-- by tenure band rather than by name.
--------------------------------------------------------------------
SELECT a.Tenure_Band,
       COUNT(DISTINCT a.Analyst_ID)                                       AS analysts,
       COUNT(c.Case_ID)                                                   AS cases,
       ROUND(AVG(c.Complexity_Score), 1)                                  AS avg_complexity,
       ROUND(AVG(c.Resolution_Hours), 1)                                  AS avg_resolution_hours,
       ROUND(100.0 * SUM(CASE WHEN c.SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN c.Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                 AS sla_compliance_pct
FROM dim_analyst a
JOIN case_data c ON c.Assigned_Analyst = a.Analyst_ID
GROUP BY a.Tenure_Band
ORDER BY a.Tenure_Band;


--------------------------------------------------------------------
-- 13. SLA breach severity - how badly are we missing?
--------------------------------------------------------------------
SELECT Case_Type,
       SUM(CASE WHEN SLA_Met_Calculated = 'No' THEN 1 ELSE 0 END)          AS breaches,
       ROUND(AVG(SLA_Breach_Hours), 1)                                    AS avg_breach_hours,
       ROUND(MAX(SLA_Breach_Hours), 1)                                    AS worst_breach_hours,
       ROUND(SUM(SLA_Breach_Hours), 0)                                    AS total_breach_hours
FROM case_data
WHERE SLA_Met_Calculated = 'No'
GROUP BY Case_Type
ORDER BY total_breach_hours DESC;


--------------------------------------------------------------------
-- 14. Assignment lag by routing method and team
--------------------------------------------------------------------
SELECT Assigned_Team, Routing_Method,
       COUNT(*)                                                           AS cases,
       ROUND(AVG(Assignment_Lag_Hours), 2)                                AS avg_assignment_lag_hours,
       ROUND(AVG(Handling_Hours), 1)                                      AS avg_handling_hours
FROM case_data
GROUP BY Assigned_Team, Routing_Method
ORDER BY Assigned_Team, avg_assignment_lag_hours DESC;


--------------------------------------------------------------------
-- 15. Monthly trend
--------------------------------------------------------------------
SELECT strftime('%Y-%m', Created_Date)                                     AS month,
       COUNT(*)                                                            AS cases,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                  AS sla_compliance_pct,
       ROUND(100.0 * SUM(CASE WHEN Reassignment_Count = 0 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Reassignment_Count IS NOT NULL
                               THEN 1 ELSE 0 END), 0), 2)                  AS assignment_accuracy_pct,
       ROUND(100.0 * SUM(CASE WHEN Reopened_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                               AS reopen_rate_pct
FROM case_data
GROUP BY month
ORDER BY month;


--------------------------------------------------------------------
-- 16. Customer segment equity check - is anyone systematically slower?
--------------------------------------------------------------------
SELECT Customer_Segment,
       COUNT(*)                                                            AS cases,
       ROUND(AVG(Complexity_Score), 1)                                     AS avg_complexity,
       ROUND(AVG(Resolution_Hours), 1)                                      AS avg_resolution_hours,
       ROUND(100.0 * SUM(CASE WHEN SLA_Met_Calculated = 'Yes' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN Current_Status = 'Resolved'
                               THEN 1 ELSE 0 END), 0), 2)                  AS sla_compliance_pct
FROM case_data
GROUP BY Customer_Segment
ORDER BY sla_compliance_pct;


--------------------------------------------------------------------
-- 17. Daily team capacity against backlog work hours
--------------------------------------------------------------------
SELECT Team_ID,
       ROUND(AVG(Available_Hours), 1)                                       AS avg_available_hours,
       ROUND(AVG(Assigned_Case_Count), 1)                                   AS avg_daily_new_cases,
       ROUND(AVG(Open_Backlog), 1)                                          AS avg_open_backlog,
       ROUND(AVG(Backlog_Work_Hours), 1)                                    AS avg_backlog_work_hours,
       ROUND(AVG(CASE WHEN Available_Hours > 0
                      THEN Backlog_Work_Hours / Available_Hours END), 2)    AS backlog_days_of_work
FROM team_capacity
GROUP BY Team_ID
ORDER BY backlog_days_of_work DESC;


--------------------------------------------------------------------
-- 18. Data quality exceptions
--------------------------------------------------------------------
SELECT Rule_ID, Severity, Action_Taken, COUNT(*) AS exceptions
FROM dq_exceptions
GROUP BY Rule_ID, Severity, Action_Taken
ORDER BY exceptions DESC;
