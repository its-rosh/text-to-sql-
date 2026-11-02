# Benchmark Questions

This file stores verified benchmark questions for the Conversational Analytics project.

A benchmark question serves as a gold-standard test case. It specifies:
- What business question the user asked
- Which tables must be queried
- Which input columns are required
- Expected business metrics and calculations
- Expected grouping grain and filters
- Expected output schema
- The exact verified reference SQL

The goal is to measure whether the chatbot generates accurate, reliable, and safe queries rather than hallucinations.

If the system does not have approved knowledge to answer a question, it must return:
`Not under my knowledge.`

---

## Benchmark Question 1 (`BQ001`): Account Age Risk Analysis

### Benchmark ID
`BQ001`

### User Question
I want to see our accounts grouped by how long they've been open — like under 2 years, 2 to 5 years, 5 to 10 years, and over 10 years. For each of those age groups, show me how many accounts are still open versus already closed, what share have gone dormant, and what the average and total balances look like. Then flag any age group where more than a quarter of the accounts are either closed or dormant, so we know where the closure risk is concentrated.

### Expected Tables
- `cdp_uat.dsag_new.p2c` (or `workspace.default.p2c` in Free Edition)
- `cdp_uat.dsag_new.mab_meb` (or `workspace.default.mab_meb` in Free Edition)

### Expected Join
```sql
p.source_account_nbr = m.ACCTNO
```

### Expected Input Columns
- `p.ucic_value`: Customer identifier
- `p.source_account_nbr`: Account number for join
- `p.product_type`: Product/account type
- `p.account_open_date`: Date account was opened
- `p.account_close_date`: Date account was closed (`'-'` if active/open)
- `p.dormancy_status`: Dormancy flag (`'D'` for dormant)
- `m.mab_bal`: Monthly Average Balance
- `m.meb_bal`: Month-End Balance

### Expected Metrics & Derived Calculations
- `account_age_years`: `DATEDIFF(CURRENT_DATE(), account_open_date) / 365.0`
- `is_closed`: `CASE WHEN account_close_date != '-' THEN 1 ELSE 0 END`
- `is_dormant`: `CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END`
- `total_accounts`: `COUNT(*)`
- `open_accounts`: `SUM(CASE WHEN is_closed = 0 THEN 1 ELSE 0 END)`
- `closed_accounts`: `SUM(is_closed)`
- `dormant_accounts`: `SUM(is_dormant)`
- `dormancy_rate_pct`: `ROUND(SUM(is_dormant) * 100.0 / COUNT(*), 2)`
- `closure_or_dormancy_risk_pct`: `ROUND(SUM(CASE WHEN is_closed = 1 OR is_dormant = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)`
- `avg_mab_bal`: `ROUND(AVG(mab_bal), 2)`
- `total_mab_bal`: `ROUND(SUM(mab_bal), 2)`
- `avg_meb_bal`: `ROUND(AVG(meb_bal), 2)`
- `total_meb_bal`: `ROUND(SUM(meb_bal), 2)`
- `risk_flag`: `CASE WHEN closure_or_dormancy_risk_pct > 25 THEN 'HIGH RISK' ELSE 'NORMAL' END`

### Grouping Grain
- `age_bucket`:
  - `'Under 2 years'` (`account_age_years < 2`)
  - `'2 to 5 years'` (`account_age_years >= 2 AND account_age_years < 5`)
  - `'5 to 10 years'` (`account_age_years >= 5 AND account_age_years < 10`)
  - `'Over 10 years'` (`account_age_years >= 10`)

### Expected Output Columns
1. `age_bucket`
2. `total_accounts`
3. `open_accounts`
4. `closed_accounts`
5. `dormant_accounts`
6. `dormancy_rate_pct`
7. `closure_or_dormancy_risk_pct`
8. `avg_mab_bal`
9. `total_mab_bal`
10. `avg_meb_bal`
11. `total_meb_bal`
12. `risk_flag`

### Ordering
Chronological age bucket order:
1. Under 2 years
2. 2 to 5 years
3. 5 to 10 years
4. Over 10 years

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
        ucic_value,
        source_account_nbr,
        product_type,
        account_open_date,
        account_close_date,
        dormancy_status,
        mab_bal,
        meb_bal,
        DATEDIFF(CURRENT_DATE(), account_open_date) / 365.0 AS account_age_years,
        CASE WHEN account_close_date != '-' THEN 1 ELSE 0 END AS is_closed,
        CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END AS is_dormant
    FROM joined
),

bucketed AS (
    SELECT
        ucic_value,
        source_account_nbr,
        product_type,
        account_open_date,
        account_close_date,
        dormancy_status,
        mab_bal,
        meb_bal,
        account_age_years,
        is_closed,
        is_dormant,
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

## Benchmark Question 2 (`BQ002`): Account Type And Segment Dormancy Analysis

### Benchmark ID
`BQ002`

### User Question
For each account type and customer segment, I want to see how many accounts we have, how many are dormant and what percentage that is, the average and total balances (both monthly average and month-end), and the average end balance for just the dormant ones. Only show me segments with at least 5 accounts, and within each account type just give me the top 3 segments with the highest dormancy rate.

### Expected Tables
- `cdp_uat.dsag_new.p2c` (or `workspace.default.p2c` in Free Edition)
- `cdp_uat.dsag_new.mab_meb` (or `workspace.default.mab_meb` in Free Edition)

### Expected Join
```sql
p.source_account_nbr = m.ACCTNO
```

### Expected Input Columns
- `p.ucic_value`: Customer identifier
- `p.source_account_nbr`: Account number for join
- `p.product_type`: Product/account type
- `p.dormancy_status`: Dormancy flag (`'D'` for dormant)
- `p.nri_status`: NRI flag
- `m.final_segment`: Customer segment
- `m.mab_bal`: Monthly Average Balance
- `m.meb_bal`: Month-End Balance

### Expected Metrics & Derived Calculations
- `total_accounts`: `COUNT(*)`
- `dormant_accounts`: `SUM(CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END)`
- `dormancy_rate_pct`: `ROUND(SUM(CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)`
- `avg_mab_bal`: `ROUND(AVG(mab_bal), 2)`
- `total_mab_bal`: `ROUND(SUM(mab_bal), 2)`
- `avg_meb_bal`: `ROUND(AVG(meb_bal), 2)`
- `total_meb_bal`: `ROUND(SUM(meb_bal), 2)`
- `avg_meb_bal_dormant_only`: `ROUND(AVG(CASE WHEN dormancy_status = 'D' THEN meb_bal END), 2)`
- `dormancy_rank_in_product`: `RANK() OVER (PARTITION BY product_type ORDER BY dormancy_rate_pct DESC)`

### Grouping Grain
- `product_type`, `final_segment`

### Filters & Thresholds
- `HAVING COUNT(*) >= 5` (only segments with at least 5 accounts)
- `WHERE dormancy_rank_in_product <= 3` (top 3 highest dormancy segments per product type)

### Expected Output Columns
1. `product_type`
2. `final_segment`
3. `total_accounts`
4. `dormant_accounts`
5. `dormancy_rate_pct`
6. `avg_mab_bal`
7. `total_mab_bal`
8. `avg_meb_bal`
9. `total_meb_bal`
10. `avg_meb_bal_dormant_only`
11. `dormancy_rank_in_product`

### Ordering
- `product_type, dormancy_rate_pct DESC`

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

# Benchmark Evaluation & Quality Gate Rules

A generated SQL query is approved for execution only if it satisfies all safety, semantic, and reliability criteria.

## 1. Safety Gate Rules

The chatbot runtime may execute only read-only queries:

### Allowed:
```sql
SELECT ...
WITH ... SELECT ...
```

### Prohibited & Blocked:
The query engine blocks any SQL with database-altering statements or multiple queries:
- `INSERT`
- `UPDATE`
- `DELETE`
- `MERGE`
- `DROP`
- `ALTER`
- `CREATE`
- `TRUNCATE`
- Semicolon-separated multiple statements (`SELECT ...; DROP ...`)
- `SELECT *` directly on physical base tables

## 2. Business Reliability Gate Rules

Every proposed query is validated against user intent:
- **Table Verification**: Tables must match approved project tables.
- **Join Integrity**: When querying both `p2c` and `mab_meb`, the join must specify `p.source_account_nbr = m.ACCTNO`.
- **Metric Verification**: Total calculations require `SUM(...)`, average calculations require `AVG(...)`, counts require `COUNT(...)`, minimum/maximum require `MIN(...)`/`MAX(...)`.
- **Grain Verification**: Aggregations by dimension (e.g. `income_segment`, `product_type`) must contain the corresponding `GROUP BY` column.
- **Dormancy Logic**: Dormant accounts must be filtered or flagged with `dormancy_status = 'D'`.
- **Open/Closed Logic**: Open accounts must check `account_close_date = '-'`; closed accounts must check `account_close_date != '-'`.

## 3. Unknown Knowledge Handling

If a user question:
- Refers to tables, columns, or metrics outside approved metadata
- Cannot be grounded in the retrieved RAG context
- Exceeds the RAG distance similarity threshold (evidence gate block)
- Refers to out-of-scope non-banking topics

The chatbot runtime will immediately halt and respond with:
`Not under my knowledge.`
