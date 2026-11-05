---
title: Conversational Analytics Text To SQL
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.39.0"
app_file: app.py
pinned: false
---

# Conversational Analytics: Natural Language Text-to-SQL

An enterprise-grade, read-only conversational analytics assistant translating business English into verified, high-performance **Databricks SQL** for banking intelligence.

---

## ⚡ Key Capabilities & Architecture

- **Domain Text-to-SQL**: Translates complex financial questions (e.g. dormancy, tenure risk brackets, balance splits) into Databricks dialect SQL with CTE and window function support.
- **Anti-Hallucination Evidence Gate**: Dense vector retrieval via **ChromaDB** (`all-MiniLM-L6-v2`) with cosine distance gating ($\le 1.20$); out-of-scope queries return *"Not under my knowledge."*
- **AST SQL Safety Gate**: Uses **`sqlglot`** Abstract Syntax Tree parsing to mathematically guarantee read-only `SELECT`/`WITH` queries, blocking DDL/DML mutation and SQL injection attacks.
- **Business Semantic Reliability**: Programmatically validates user metrics, aggregations (`SUM`, `AVG`, `COUNT`), and table join paths before warehouse execution.
- **Databricks Serverless Execution**: Connects securely to Databricks SQL Warehouse using `databricks-sql-connector`.
- **Interactive Streamlit UI**: Web dashboard featuring query presets, verification status badges, and an automated benchmark scorecard.
- **Query Advisor & Diagnostics**: Actionable root-cause explanations and instant copy-pasteable *"Suggested change in query"* rewrites.
- **50-Question Benchmark Engine**: Automated evaluation suite measuring **NLCR (98.0%)**, **Safety Gate (82.0%)**, **Valid SQL (98.0%)**, and **Execution Accuracy (24.0%)** $\rightarrow$ **75.5% Composite Model Reliability**.

---

## 🔄 End-to-End Workflow

```text
User Natural Language Question
       ↓
[1. Dynamic Keyword-Stemmed Router] ── (open*, clos*, tenur*, age*, dorm*)
       ↓
[2. ChromaDB RAG Vector Store] ─────── (Top-3 catalog metadata chunks)
       ↓
[3. Evidence Distance Gate] ────────── (Cosine distance <= 1.20)
       ↓
[4. Prompt Builder & Groq LLM] ─────── (Schema rules + CTE scoping + column aliases)
       ↓
[5. AST SQL Safety Checker] ────────── (Read-only SELECT/WITH, single statement)
       ↓
[6. AST Reliability Checker] ───────── (Aggregations, dimensions, join conditions)
       ↓
[7. Databricks SQL Warehouse] ──────── (Direct cloud lakehouse execution)
       ↓
[8. Streamlit Dashboard] ───────────── (Data table, verification pills, scorecard)
```

---

## 📊 Data Model & Catalog

| Table | Catalog Path | Granularity & Description | Key Columns |
| :--- | :--- | :--- | :--- |
| **`p2c`** | `workspace.default.p2c` | Customer-Account Linkage (1 row per account) | `ucic_value`, `source_account_nbr` (PK), `product_type`, `account_open_date`, `account_close_date` (`'-'` = active), `dormancy_status`, `nri_status`, `income_segment` |
| **`mab_meb`** | `workspace.default.mab_meb` | Monthly Financial Balances (1 row per monthly ledger) | `ACCTNO` (FK), `CUSTID`, `mab_bal`, `meb_bal`, `retail_bulk`, `final_segment`, `gldesc`, `EMP_CODE` |

**Primary Relational Join:** `p2c.source_account_nbr = mab_meb.ACCTNO`

---

## 📁 Project Structure

```text
├── app/
│   └── main.py                     # Streamlit web application & sidebar scorecard
├── config/
│   └── business_glossary.json      # Dimension/metric definitions & ambiguous term rules
├── data/                           # Source Excel spreadsheets for initial data seeding
├── docs/                           # Data catalog, benchmark questions, and PDF brief
├── reports/                        # RAG metadata chunks and evaluation scorecards
├── scripts/
│   ├── route_question.py           # Word-boundary stemmed query router
│   ├── check_rag_evidence.py       # ChromaDB vector retrieval & distance gating
│   ├── check_ques_before_sql.py    # Pre-SQL validation gate
│   ├── build_sql_prompt.py         # Schema-aware prompt construction & CTE scoping
│   ├── generate_sql_with_llm.py    # Groq API LLM caller with markdown strip
│   ├── check_sql_safety.py         # AST read-only safety validator
│   ├── check_sql_reliability.py    # Business logic & aggregation validator
│   ├── run_verified_sql.py         # Databricks SQL connector runner
│   ├── query_advisor.py            # Error diagnostics & query rewrite suggestions
│   └── run_eval_suite.py           # 50-benchmark evaluation scoring engine
└── tests/                          # 29 automated pytest unit & integration tests
```

---

## 🚀 Quickstart

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your keys:
   ```env
   DATABRICKS_SERVER_HOSTNAME="dbc-xxxx.cloud.databricks.com"
   DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/xxxx"
   DATABRICKS_ACCESS_TOKEN="dapi_xxxx"
   LLM_API_KEY="gsk_xxxx"
   LLM_PROVIDER="groq"
   LLM_MODEL="llama-3.1-8b-instant"
   ```

3. **Launch Web UI:**
   ```bash
   streamlit run app/main.py
   ```

4. **Run Automated Tests & Benchmarks:**
   ```bash
   pytest -q                      # Runs 29 unit and integration tests
   python scripts/run_eval_suite.py  # Runs full 50-question benchmark evaluation
   ```
