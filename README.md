# Conversational Analytics: Natural Language Text-to-SQL

This project builds a read-only conversational analytics chatbot for banking and reporting data.

The user asks a business question in natural language (English). The system retrieves approved domain context, prompts an LLM to generate Databricks SQL, performs strict safety and business reliability checks, executes the query (in Databricks SQL Warehouse or locally in mock/sandbox mode), and displays the resulting data table and explanation.

## Core Rules

- **Read-Only**: The chatbot may only run `SELECT` queries (including Common Table Expressions with `WITH`).
- **Strict Safety Gate**: Blocks database-altering commands including `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`, and `TRUNCATE`.
- **Anti-Hallucination & Evidence Gate**: If retrieved context does not contain sufficient verified knowledge to answer the question, the chatbot returns:
  `Not under my knowledge.`
- **Business Reliability**: Checks that generated SQL matches the user's intended metrics, aggregations (`SUM`, `AVG`, `COUNT`), dimensions, and joins before execution.

## Data Sources & Tables

- `data/p2c_dummy_data_1000rows.xlsx` (Customer-account linkage data)
- `data/mab_meb_dummy_data_1000rows.xlsx` (Monthly Average and Month-End Balances)

Mapped to Databricks tables:
- `cdp_uat.dsag_new.p2c` (or `workspace.default.p2c` in Free Edition)
- `cdp_uat.dsag_new.mab_meb` (or `workspace.default.mab_meb` in Free Edition)

### Primary Join Condition

```sql
p.source_account_nbr = m.ACCTNO
```

## System Architecture Flow

```text
User question
      ↓
Streamlit website / CLI
      ↓
Question Router (identifies domains: p2c, mab_meb, both, or out-of-scope)
      ↓
ChromaDB Vector Store (retrieves approved metadata chunks)
      ↓
Evidence Gate (validates distance and required context chunks)
      ↓
Prompt Builder & LLM Generator (generates safe Databricks SELECT query)
      ↓
SQL Safety Checker (enforces SELECT-only, single statement, approved tables)
      ↓
SQL Reliability Checker (verifies metrics, dimensions, aggregations, joins)
      ↓
Query Execution Engine (Databricks Warehouse or Local Sandbox Engine)
      ↓
Interactive Results View (Table, Metrics, Status)
```

## Project Structure

- `app/`: Streamlit web interface (`app/main.py`)
- `config/`: Business glossary and mappings (`config/business_glossary.json`)
- `data/`: Excel source files for customer and balance data
- `docs/`: Data catalog, Databricks setup, and benchmark test questions
- `reports/`: Extracted file registry and RAG metadata chunks
- `scripts/`: Modular pipeline scripts:
  - `route_question.py`: Domain routing
  - `check_rag_evidence.py`: RAG context retrieval & distance gating
  - `check_ques_before_sql.py`: Pre-SQL validation gate
  - `build_sql_prompt.py`: Prompt builder with schema & rules
  - `generate_sql_with_llm.py`: Groq LLM integration with Markdown cleaner
  - `check_sql_safety.py`: AST-based SQL safety validation
  - `check_sql_reliability.py`: Business logic and aggregation verification
  - `local_query_engine.py`: Zero-setup local SQLite query executor for dummy data
  - `run_verified_sql.py`: Unified executor supporting Databricks and Local mode
- `tests/`: Automated unit and integration tests

## Setup & Running

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   Copy `.env.example` to `.env` and configure your API keys (or run in local mode):
   ```bash
   cp .env.example .env
   ```

3. Run the Streamlit web application:
   ```bash
   streamlit run app/main.py
   ```

4. Run automated tests:
   ```bash
   pytest
   ```
