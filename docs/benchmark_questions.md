# Benchmark Questions

This file stores verified benchmark questions for the Conversational Analytics project.

A benchmark question is a test case. It tells us:

- what the user asked
- which tables should be used
- which columns should be used
- what business logic is expected
- what SQL should be generated

The goal is to measure whether the chatbot is correct, not just whether it gives an answer.

If the system does not have enough approved knowledge to answer, it must say:

`Not under my knowledge.`

---

## Prompt 1: Account Age Risk Analysis

### User Question

I want to see our accounts grouped by how long they've been open — like under 2 years, 2 to 5 years, 5 to 10 years, and over 10 years. For each of those age groups, show me how many accounts are still open versus already closed, what share have gone dormant, and what the average and total balances look like. Then flag any age group where more than a quarter of the accounts are either closed or dormant, so we know where the closure risk is concentrated.

### Expected Tables

- `cdp_uat.dsag_new.p2c`
- `cdp_uat.dsag_new.mab_meb`

### Expected Join

```sql
p.source_account_nbr = m.ACCTNO

### Expected SQL

```sql
WITH joined AS (
    SELECT
        p.ucic_value,
        p.source_account_nbr,
        p.product_type,
        p.account_open_date,
        p.account_close_date,
        p.dormancy_status,
        m.mab_bal,
        m.meb_bal
    FROM cdp_uat.dsag_new.p2c p
    INNER JOIN cdp_uat.dsag_new.mab_meb m
        ON p.source_account_nbr = m.ACCTNO
),

aged AS (
    SELECT
        *,
        DATEDIFF(CURRENT_DATE(), account_open_date) / 365.0 AS account_age_years,
        CASE WHEN account_close_date != '-' THEN 1 ELSE 0 END AS is_closed,
        CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END AS is_dormant
    FROM joined
),

bucketed AS (
    SELECT
        *,
        CASE
            WHEN account_age_years < 2 THEN 'Under 2 years'
            WHEN account_age_years < 5 THEN '2 to 5 years'
            WHEN account_age_years < 10 THEN '5 to 10 years'
            ELSE 'Over 10 years'
        END AS age_bucket
    FROM aged
),

age_stats AS (
    SELECT
        age_bucket,
        COUNT(*) AS total_accounts,
        SUM(is_closed) AS closed_accounts,
        SUM(CASE WHEN is_closed = 0 THEN 1 ELSE 0 END) AS open_accounts,
        SUM(is_dormant) AS dormant_accounts,
        ROUND(SUM(is_dormant) * 100.0 / COUNT(*), 2) AS dormancy_rate_pct,
        ROUND(
            SUM(CASE WHEN is_closed = 1 OR is_dormant = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS closure_or_dormancy_risk_pct,
        ROUND(AVG(mab_bal), 2) AS avg_mab_bal,
        ROUND(SUM(mab_bal), 2) AS total_mab_bal,
        ROUND(AVG(meb_bal), 2) AS avg_meb_bal,
        ROUND(SUM(meb_bal), 2) AS total_meb_bal
    FROM bucketed
    GROUP BY age_bucket
)

SELECT
    age_bucket,
    total_accounts,
    open_accounts,
    closed_accounts,
    dormant_accounts,
    dormancy_rate_pct,
    closure_or_dormancy_risk_pct,
    avg_mab_bal,
    total_mab_bal,
    avg_meb_bal,
    total_meb_bal,
    CASE
        WHEN closure_or_dormancy_risk_pct > 25 THEN 'HIGH RISK'
        ELSE 'NORMAL'
    END AS risk_flag
FROM age_stats
ORDER BY
    CASE age_bucket
        WHEN 'Under 2 years' THEN 1
        WHEN '2 to 5 years' THEN 2
        WHEN '5 to 10 years' THEN 3
        WHEN 'Over 10 years' THEN 4
    END;
```

---

## Prompt 2: Account Type And Segment Dormancy Analysis

### User Question

For each account type and customer segment, I want to see how many accounts we have, how many are dormant and what percentage that is, the average and total balances (both monthly average and month-end), and the average end balance for just the dormant ones. Only show me segments with at least 5 accounts, and within each account type just give me the top 3 segments with the highest dormancy rate.

### Expected Tables

- `cdp_uat.dsag_new.p2c`
- `cdp_uat.dsag_new.mab_meb`

### Expected Join

```sql
p.source_account_nbr = m.ACCTNO

### Expected SQL

```sql
WITH joined AS (
    SELECT
        p.ucic_value,
        p.source_account_nbr,
        p.product_type,
        p.dormancy_status,
        p.nri_status,
        m.final_segment,
        m.mab_bal,
        m.meb_bal
    FROM cdp_uat.dsag_new.p2c p
    INNER JOIN cdp_uat.dsag_new.mab_meb m
        ON p.source_account_nbr = m.ACCTNO
),

segment_stats AS (
    SELECT
        product_type,
        final_segment,
        COUNT(*) AS total_accounts,
        SUM(CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END) AS dormant_accounts,
        ROUND(
            SUM(CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS dormancy_rate_pct,
        ROUND(AVG(mab_bal), 2) AS avg_mab_bal,
        ROUND(SUM(mab_bal), 2) AS total_mab_bal,
        ROUND(AVG(meb_bal), 2) AS avg_meb_bal,
        ROUND(SUM(meb_bal), 2) AS total_meb_bal,
        ROUND(
            AVG(CASE WHEN dormancy_status = 'D' THEN meb_bal END),
            2
        ) AS avg_meb_bal_dormant_only
    FROM joined
    GROUP BY product_type, final_segment
    HAVING COUNT(*) >= 5
),

ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY product_type
            ORDER BY dormancy_rate_pct DESC
        ) AS dormancy_rank_in_product
    FROM segment_stats
)

SELECT
    product_type,
    final_segment,
    total_accounts,
    dormant_accounts,
    dormancy_rate_pct,
    avg_mab_bal,
    total_mab_bal,
    avg_meb_bal,
    total_meb_bal,
    avg_meb_bal_dormant_only,
    dormancy_rank_in_product
FROM ranked
WHERE dormancy_rank_in_product <= 3
ORDER BY product_type, dormancy_rate_pct DESC;
```

---

# Benchmark Evaluation Rules

A generated SQL query is correct only if it satisfies the benchmark question's intent.

## Correctness Checks

For every generated SQL query, check:

- Does it use the expected table or tables?
- Does it use the expected join condition?
- Does it use the expected columns?
- Does it calculate the correct metric?
- Does it group at the correct grain?
- Does it apply the required filters?
- Does it return the expected output columns?
- Does it avoid unsafe database-changing operations?

## Safety Rules

The chatbot may only generate read-only SQL.

Allowed:

```sql
SELECT ...
WITH ... SELECT ...