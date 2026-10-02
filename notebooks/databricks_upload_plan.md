# Databricks Upload Plan

This file describes how the Excel data will be loaded into Databricks.

No chatbot logic is built in this step.

The goal is only to create/verify the tables needed by the benchmark questions.

---

## 1. Source Files

Local source files:

```text
data/p2c_dummy_data_1000rows.xlsx
data/mab_meb_dummy_data_1000rows.xlsx
```

---

## 2. Target Tables

Final expected table names:

```text
cdp_uat.dsag_new.p2c
cdp_uat.dsag_new.mab_meb
```

Practice/free-edition fallback names:

```text
conversational_analytics.p2c
conversational_analytics.mab_meb
```

---

## 3. Upload Method

Use Databricks UI or a Databricks notebook to upload the Excel files.

If Excel upload is difficult, convert Excel to CSV first, then upload CSV.

---

## 4. Required Validation

After upload, validate row counts.

Expected:

```text
p2c = 1000 rows
mab_meb = 1000 rows
```

---

## 5. Required Join Validation

Validate that this join works:

```sql
SELECT COUNT(*) AS joined_rows
FROM cdp_uat.dsag_new.p2c p
INNER JOIN cdp_uat.dsag_new.mab_meb m
    ON p.source_account_nbr = m.ACCTNO;
```

If using practice table names, replace the table names.

---

## 6. Success Criteria

Phase 4 is complete when:

- both tables exist in Databricks
- both tables have 1000 rows
- the join query returns rows
- table names are recorded in `.env`
- benchmark SQL can be run manually in Databricks SQL editor
``` d

---

## 7. Future File Ingestion Requirement

In future, the project may receive more Excel or CSV files.

The system should support adding new files with minimal manual work.

Future ingestion flow:

```text
New file added to data/
-> inspect file name, sheets, columns, and row count
-> decide target Databricks table name
-> load file into Databricks
-> validate row count
-> update data catalog metadata
-> create text chunks for RAG
-> embed chunks
-> store embeddings in ChromaDB
-> make the new table available to the Question Router