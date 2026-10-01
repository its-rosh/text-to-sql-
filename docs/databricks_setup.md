# Databricks Setup Checklist

This file tracks the manual Databricks setup for the Conversational Analytics project.

Databricks is the main SQL engine for this project.

The chatbot must only run read-only queries against Databricks.

---

## 1. Workspace

### Requirement

Use Databricks Free Edition or a company-approved Databricks workspace.

### Notes

- Use only dummy/sample data for the free hosted project.
- Do not upload confidential company data to public or personal workspaces.
- Keep Databricks tokens private.
- Real tokens must go only in `.env`.

---

## 2. SQL Warehouse

### Requirement

Create or use one SQL warehouse.

### Values To Store In `.env`

Do not paste real values into GitHub.

```env
DATABRICKS_SERVER_HOSTNAME=
DATABRICKS_HTTP_PATH=
DATABRICKS_ACCESS_TOKEN=
```

---

## 3. Target Tables

The project expects these final Databricks tables:

```text
cdp_uat.dsag_new.p2c
cdp_uat.dsag_new.mab_meb
```

For free/local practice, if these exact catalog/schema names are not available, use a practice schema first.

Example practice names:

```text
conversational_analytics.p2c
conversational_analytics.mab_meb
```

---

## 4. Source Files

Current source files:

```text
data/p2c_dummy_data_1000rows.xlsx
data/mab_meb_dummy_data_1000rows.xlsx
```

Expected row counts:

```text
p2c = 1000 rows
mab_meb = 1000 rows
```

---

## 5. Row Count Validation Queries

After loading data into Databricks, run:

```sql
SELECT COUNT(*) AS row_count
FROM cdp_uat.dsag_new.p2c;
```

Expected:

```text
1000
```

Run:

```sql
SELECT COUNT(*) AS row_count
FROM cdp_uat.dsag_new.mab_meb;
```

Expected:

```text
1000
```

---

## 6. Join Validation Query

Run:

```sql
SELECT COUNT(*) AS joined_rows
FROM cdp_uat.dsag_new.p2c p
INNER JOIN cdp_uat.dsag_new.mab_meb m
    ON p.source_account_nbr = m.ACCTNO;
```

Purpose:

This confirms that the benchmark join works.

---

## 7. Read-Only Rule

The chatbot runtime may execute only:

```sql
SELECT ...
WITH ... SELECT ...
```

The chatbot runtime must block:

```sql
INSERT
UPDATE
DELETE
MERGE
DROP
ALTER
CREATE
TRUNCATE
```