# Data Catalog

This file documents the approved data sources, tables, columns, business definitions, and onboarding rules for the Conversational Analytics project.

The chatbot is strictly bounded to answer only from verified metadata described in this catalog.

If a user asks about data, tables, or metrics not approved here, the system must return:
`Not under my knowledge.`

---

# Approved Tables

## 1. `cdp_uat.dsag_new.p2c`

### Table Name Meaning
`p2c` stands for **Party-to-Customer** / Customer-Account Linkage.

### Target Table Mapping
- **Production / UAT**: `cdp_uat.dsag_new.p2c`
- **Free Edition / Practice**: `workspace.default.p2c`

### Source File & Sheet
- **File**: `data/p2c_dummy_data_1000rows.xlsx`
- **Sheet**: `P2C`
- **Row Count**: `1000`

### Purpose
Contains account and customer linkage information, account opening and closing dates, product classifications, dormancy status, and NRI residency flags.

### Important Columns
| Column | Data Type | Meaning | Business Context / Example |
|---|---|---|---|
| `ucic_value` | STRING | Unique Customer Identification Code | Master customer identifier |
| `source_account_nbr` | STRING | Primary Account Number | Used to join with balance data (`mab_meb.ACCTNO`) |
| `account_nbr` | STRING | P2C system internal account number | System-specific account number |
| `full_name` | STRING | Customer Full Name | Masked / dummy customer name |
| `account_open_date` | DATE | Account Opening Date | Used to calculate account age in years |
| `account_close_date` | STRING | Account Closure Date | `'-'` if active/open; date string if closed |
| `product_type` | STRING | Account / Product Type Code | `SA`, `CA`, `FD`, `RD`, `LN`, `CC`, `OD` |
| `dormancy_status` | STRING | Dormancy Status Flag | `'D'` = Dormant, `'A'` = Active, `'I'` = Inactive |
| `nri_status` | STRING | Non-Resident Indian Flag | `'Y'` = Non-Resident Indian, `'N'` = Resident |
| `income_segment` | STRING | Customer Income Tier | e.g. `PB`, `GB` |
| `service_segment` | STRING | Relationship Service Segment | Customer relationship segment |
| `linkage_identifier` | STRING | Group Linkage ID | Customer grouping identifier |

---

## 2. `cdp_uat.dsag_new.mab_meb`

### Table Name Meaning
`mab_meb` stands for **Monthly Average Balance & Month-End Balance**.

### Target Table Mapping
- **Production / UAT**: `cdp_uat.dsag_new.mab_meb`
- **Free Edition / Practice**: `workspace.default.mab_meb`

### Source File & Sheet
- **File**: `data/mab_meb_dummy_data_1000rows.xlsx`
- **Sheet**: `Sheet2`
- **Row Count**: `1000`

### Purpose
Contains monthly average balance, month-end balance, customer business segments, branch details, and fixed deposit metrics.

### Important Columns
| Column | Data Type | Meaning | Business Context / Example |
|---|---|---|---|
| `ACCTNO` | STRING | Account Number | Used to join with P2C data (`p2c.source_account_nbr`) |
| `CUSTID` | STRING | Customer Identifier | Linked customer ID |
| `CUST_NAME` | STRING | Customer Name | Name of account holder |
| `brcode` | STRING | Branch Code | Operating branch identifier |
| `mab_bal` | DOUBLE | Monthly Average Balance | Core metric for account relationship balance |
| `meb_bal` | DOUBLE | Month-End Balance | Balance on the final calendar day of month |
| `final_segment` | STRING | Final Customer Segment | Granular segment: `SAL`, `HH`, `SAL ERV`, etc. |
| `income_segment` | STRING | Income Tier Segment | `PB` (Privilege Banking), `GB` (General Banking) |
| `bal_bucket` | STRING | Balance Tier Bucket | e.g. `2K-10K`, `1C-5C` |
| `fd_bucket` | STRING | Fixed Deposit Bucket | Categorization of term deposits |
| `retail_bulk` | STRING | Retail vs Bulk Classification | `RETAIL` or `BULK` |
| `sub_product` | STRING | Sub-Product Code | Internal bank ledger sub-code |

---

# Approved Join Rules

## P2C To MAB/MEB Join
Use this inner join when a query requires customer or account attributes from `p2c` alongside balance metrics from `mab_meb`:

```sql
FROM cdp_uat.dsag_new.p2c p
INNER JOIN cdp_uat.dsag_new.mab_meb m
    ON p.source_account_nbr = m.ACCTNO
```

*In Free Edition / local environments, replace `cdp_uat.dsag_new.` with `workspace.default.` or unqualified table names.*

---

# Business Definitions

### 1. Monthly Average Balance (MAB)
- **Meaning**: The average ledger balance maintained across all calendar days in the month.
- **SQL Column**: `m.mab_bal`
- **Aggregations**:
  - Total MAB: `SUM(m.mab_bal)`
  - Average MAB: `AVG(m.mab_bal)`

### 2. Month-End Balance (MEB)
- **Meaning**: The closing ledger balance recorded on the final day of the reporting month.
- **SQL Column**: `m.meb_bal`
- **Aggregations**:
  - Total MEB: `SUM(m.meb_bal)`
  - Average MEB: `AVG(m.meb_bal)`

### 3. Account Count
- **Meaning**: The total count of unique accounts.
- **SQL Expression**: `COUNT(*)` or `COUNT(p.source_account_nbr)`

### 4. Dormancy Status
- **Meaning**: Whether an account has had no customer-initiated activity over a statutory period.
- **Dormant Account**: `p.dormancy_status = 'D'`
- **Active Account**: `p.dormancy_status = 'A'`
- **Dormancy Rate (%)**:
  ```sql
  ROUND(SUM(CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
  ```

### 5. Open vs Closed Accounts
- **Open / Active Account**: `p.account_close_date = '-'`
- **Closed Account**: `p.account_close_date != '-'`

### 6. Account Age & Age Buckets
- **Account Age (Years)**:
  ```sql
  DATEDIFF(CURRENT_DATE(), p.account_open_date) / 365.0
  ```
- **Age Bucketing Logic**:
  ```sql
  CASE
      WHEN account_age_years < 2 THEN 'Under 2 years'
      WHEN account_age_years < 5 THEN '2 to 5 years'
      WHEN account_age_years < 10 THEN '5 to 10 years'
      ELSE 'Over 10 years'
  END
  ```

### 7. Closure or Dormancy Risk Flag
- **Metric**: Percentage of accounts in an age cohort that are either closed or dormant:
  ```sql
  ROUND(SUM(CASE WHEN is_closed = 1 OR is_dormant = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
  ```
- **Flag Logic**:
  ```sql
  CASE
      WHEN closure_or_dormancy_risk_pct > 25 THEN 'HIGH RISK'
      ELSE 'NORMAL'
  END
  ```

### 8. Product Type Mappings
| Code | Meaning | Description |
|---|---|---|
| `SA` | Savings Account | Standard retail savings bank account |
| `CA` | Current Account | Business / commercial checking account |
| `FD` | Fixed Deposit | Term deposit account |
| `RD` | Recurring Deposit | Systematic monthly deposit account |
| `LN` | Loan Account | Retail lending facility |
| `CC` | Credit Card / Cash Credit | Revolving credit line |
| `OD` | Overdraft | Overdraft protection account |

### 9. Customer Segments
- **Income Segments (`income_segment`)**:
  - `PB`: Privilege Banking / Priority Banking
  - `GB`: General Banking
- **Final Segments (`final_segment`)**:
  - `SAL`: Salaried Individual Segment
  - `HH`: Household Account Segment
  - `SES CA`: Small Enterprise Current Account Segment

---

# Future File Onboarding Rules

When new Excel or CSV files are added to `data/`:

### 1. Automated Inspection & Registry
- Every new file must be scanned by `scripts/build_file_registry.py`.
- Source file name, sheet names, row counts, and column schemas are recorded in `reports/file_registry.csv`.

### 2. Validation Criteria
- Row count must exceed zero.
- Table must contain an account or customer linkage identifier that joins to `p2c.source_account_nbr` or `mab_meb.ACCTNO`.
- Column data types must be verified for numeric, date, and categorical integrity.

### 3. Approval Gate
- No uploaded dataset is accessible to the LLM or query router until:
  1. The table schema and business descriptions are added to this `data_catalog.md`.
  2. Mappings and synonyms are added to `config/business_glossary.json`.
  3. RAG metadata chunks are regenerated via `scripts/build_rag_metadata.py` and indexed into ChromaDB.
  4. The question router is updated with the new domain keywords.

---

# ChromaDB RAG Metadata Specification

ChromaDB stores verified text chunks for semantic similarity search.

### Chunk Types
1. **`table_summary`**: High-level table overview, row counts, and primary purpose.
2. **`column_def`**: Specific column names, data types, business definitions, and valid values.
3. **`join_rule`**: Approved table relationship rules and foreign keys.
4. **`business_metric`**: Metric definitions, formulas, acronym mappings, and aggregation rules.

### Metadata Schema
Every chunk upserted to ChromaDB includes the following metadata dictionary:

| Metadata Field | Type | Description |
|---|---|---|
| `source_file` | STRING | Name of source spreadsheet (`p2c_dummy_data_1000rows.xlsx`) |
| `sheet_name` | STRING | Excel sheet name (`P2C`, `Sheet2`) |
| `table_name` | STRING | Target Databricks table (`p2c`, `mab_meb`) |
| `column_name` | STRING | Relevant column name or `ALL` |
| `business_term` | STRING | Business concept (`MAB`, `dormancy_status`, `account_age`) |
| `chunk_type` | STRING | `table_summary`, `column_def`, `join_rule`, or `business_metric` |
| `approved_status` | STRING | `APPROVED` (only approved chunks are stored) |

```