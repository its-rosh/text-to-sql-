# Data Catalog

This file documents the approved data sources for the Conversational Analytics project.

The chatbot is allowed to answer only from approved tables, approved columns, approved business definitions, benchmark examples, and SQL results.

If a user asks about data that is not described here, the system must return:

`Not under my knowledge.`

---

# Approved Tables

## 1. `cdp_uat.dsag_new.p2c`

### Table Name Meaning

`p2c` means Party to Customer / Party to Customer linkage.

In this project, this table represents account and customer linkage information.

### Source File

`data/p2c_dummy_data_1000rows.xlsx`

### Source Sheet

`P2C`

### Row Count

`1000`

### Purpose

This table contains account and customer linkage information.

It helps answer questions about:

- account identifiers
- customer identifiers
- account open date
- account close date
- product or account type
- dormancy status
- NRI status
- UCIC/linkage information

### Important Columns

| Column | Meaning |
|---|---|
| `ucic_value` | Customer identifier value |
| `source_account_nbr` | Account number used to join with balance data |
| `account_nbr` | Account number in the P2C extract |
| `full_name` | Customer full name |
| `account_open_date` | Date when account was opened |
| `account_close_date` | Date when account was closed, or `-` if still open |
| `product_type` | Account/product type |
| `dormancy_status` | Dormancy flag |
| `nri_status` | NRI status flag |
| `income_segment` | Income segment from P2C, if available |
| `service_segment` | Service segment |
| `linkage_identifier` | Linkage identifier such as UCIC |

---

## 2. `cdp_uat.dsag_new.mab_meb`

### Table Name Meaning

`mab_meb` means Monthly Average Balance and Month End Balance.

In this project, this table represents account balance information.

### Source File

`data/mab_meb_dummy_data_1000rows.xlsx`

### Source Sheet

`Sheet2`

### Row Count

`1000`

### Purpose

This table contains monthly average balance and month-end balance information.

It helps answer questions about:

- MAB balance
- MEB balance
- customer/account balances
- customer segments
- branch codes
- balance buckets
- retail or non-retail categories

### Important Columns

| Column | Meaning |
|---|---|
| `ACCTNO` | Account number used to join with P2C data |
| `CUSTID` | Customer identifier |
| `CUST_NAME` | Customer name |
| `brcode` | Branch code |
| `mab_bal` | Monthly Average Balance |
| `meb_bal` | Month End Balance |
| `final_segment` | Final customer segment |
| `segment` | Raw segment |
| `income_segment` | Income segment |
| `income_segment_mar` | March income segment |
| `bal_bucket` | Balance bucket |
| `fd_bucket` | Fixed deposit bucket |
| `retail_bulk` | Retail or bulk category |
| `sub_product` | Sub-product category |

---

# Approved Join Rules

## P2C To MAB/MEB

Use this join when a question needs account details from `p2c` and balance details from `mab_meb`.

```sql
FROM cdp_uat.dsag_new.p2c p
INNER JOIN cdp_uat.dsag_new.mab_meb m
    ON p.source_account_nbr = m.ACCTNO

---

# Business Definitions

## MAB

MAB means Monthly Average Balance.

In SQL, use:

```sql
m.mab_bal