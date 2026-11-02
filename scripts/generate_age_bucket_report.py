# scripts/generate_age_bucket_report.py
"""Generate the SQL for the *Account Age Bucket* report.

The function returns a ready‑to‑run SELECT statement that:
1. Joins the `p2c` table with the `mab_meb` balance table.
2. Calculates the account age in years and puts it into four buckets:
   * Under 2 years
   * 2 to 5 years
   * 5 to 10 years
   * Over 10 years
3. Determines whether each account is open or closed and whether it is dormant.
4. Aggregates counts, percentages, average & total balances per bucket.
5. Adds a risk flag – "HIGH RISK" when ≥ 25 % of accounts in the bucket are closed or dormant.
"""

def get_age_bucket_sql() -> str:
    """Return the full SQL for the Age‑Bucket report.

    The query follows the logic described in the project documentation and
    respects the approved table and column names defined in `data_catalog.md`.
    It is a pure ``SELECT`` statement, safe for the existing SQL‑safety
    checks.
    """
    return """
WITH joined AS (
    SELECT
        p.account_open_date,
        p.account_close_date,
        p.dormancy_status,
        m.mab_bal,
        m.meb_bal
    FROM cdp_uat.dsag_new.p2c   p
    INNER JOIN cdp_uat.dsag_new.mab_meb m
        ON p.source_account_nbr = m.ACCTNO
),

aged AS (
    SELECT
        *,
        DATEDIFF(CURRENT_DATE(), account_open_date) / 365.0 AS age_years,
        CASE WHEN account_close_date = '-' THEN 'Open' ELSE 'Closed' END AS open_status,
        CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END AS is_dormant
    FROM joined
),

bucketed AS (
    SELECT
        *,
        CASE
            WHEN age_years < 2  THEN 'Under 2 years'
            WHEN age_years < 5  THEN '2 to 5 years'
            WHEN age_years < 10 THEN '5 to 10 years'
            ELSE 'Over 10 years'
        END AS age_bucket
    FROM aged
),

stats AS (
    SELECT
        age_bucket,
        COUNT(*)                                            AS total_accounts,
        SUM(CASE WHEN open_status = 'Open'  THEN 1 ELSE 0 END) AS open_accounts,
        SUM(CASE WHEN open_status = 'Closed' THEN 1 ELSE 0 END) AS closed_accounts,
        SUM(is_dormant)                                     AS dormant_accounts,
        ROUND( SUM(is_dormant) * 100.0 / COUNT(*), 2)       AS dormancy_pct,
        ROUND( SUM(CASE WHEN open_status='Closed' OR is_dormant=1 THEN 1 ELSE 0 END)
               * 100.0 / COUNT(*), 2)                       AS risk_pct,
        ROUND(AVG(mab_bal), 2)                              AS avg_mab_bal,
        ROUND(SUM(mab_bal), 2)                              AS total_mab_bal,
        ROUND(AVG(meb_bal), 2)                              AS avg_meb_bal,
        ROUND(SUM(meb_bal), 2)                              AS total_meb_bal,
        CASE WHEN
            ROUND( SUM(CASE WHEN open_status='Closed' OR is_dormant=1 THEN 1 ELSE 0 END)
                   * 100.0 / COUNT(*), 2) > 25
            THEN 'HIGH RISK'
            ELSE 'NORMAL'
        END                                                 AS risk_flag
    FROM bucketed
    GROUP BY age_bucket
)
SELECT *
FROM stats
ORDER BY
    CASE age_bucket
        WHEN 'Under 2 years' THEN 1
        WHEN '2 to 5 years'  THEN 2
        WHEN '5 to 10 years' THEN 3
        WHEN 'Over 10 years' THEN 4
    END;
"""

if __name__ == "__main__":
    # Simple self‑test: print the query so a developer can copy‑paste it.
    print(get_age_bucket_sql())
""