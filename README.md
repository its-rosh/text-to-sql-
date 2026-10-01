# Conversational Analytics: Natural Language Text-to-SQL

This project builds a read-only conversational analytics chatbot for banking/reporting data.

The user asks a business question in English. The system retrieves approved context, asks an LLM to generate SQL, checks the SQL for safety and reliability, runs the approved query in Databricks, and returns the answer with the SQL used.

## Core Rules

- The chatbot must be read-only.
- The chatbot may only run `SELECT` queries.
- The chatbot must block unsafe SQL such as `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`, and `TRUNCATE`.
- The chatbot must not hallucinate.
- If approved context is not enough to answer, the chatbot must say: `Not under my knowledge.`
- Reliability checks are built internally.

## Current Data Sources

- `data/p2c_dummy_data_1000rows.xlsx`
- `data/mab_meb_dummy_data_1000rows.xlsx`

These files will be mapped to Databricks tables:

- `cdp_uat.dsag_new.p2c`
- `cdp_uat.dsag_new.mab_meb`

## Main Join

```sql
p.source_account_nbr = m.ACCTNO
```

## Environment Variables

This project uses a local `.env` file for personal project-specific secrets.

Do not commit `.env` to GitHub.

Use `.env.example` as the safe template.

## Planned Flow

```text
User question
-> Question router
-> RAG context retrieval
-> Evidence gate
-> LLM SQL generation
-> SQL safety checker
-> SQL reliability checker
-> Databricks SQL execution
-> Website answer
```

## Project Phases

1. Project foundation and environment setup
2. Benchmark questions
3. Data catalog
4. Databricks setup
5. RAG knowledge base
6. Question router
7. LLM SQL generation
8. SQL safety and reliability checks
9. Streamlit website
10. Evaluation, hosting, and future improvements