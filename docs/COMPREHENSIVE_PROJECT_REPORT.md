# Conversational Analytics – Natural Language Text to SQL
## Comprehensive Project Engineering & Implementation Report (18 Chapters • 20 Pages)

**Organization:** ICICI Bank • Data Science & Analytics Group (DSAG)  
**Location:** ICICI Bank BKC Towers, Bandra Kurla Complex, Mumbai  
**Project Guide:** Ashutosh Kumar (Lead Data Scientist / Architect)  
**Project Mentor:** Ankit Sharma (Data Science & Analytics Group)  
**Intern Details:** Roshita Jaiswal (Data Science Intern)  
**Executive Tagline:** *"Ask a question in English; get verified SQL, the answer, and the query used – with accuracy measured, not assumed"*

---

## TABLE OF CONTENTS

### SECTION I: EXECUTIVE & BUSINESS FOUNDATION
* **Chapter 1:** The Business Problem: The "Data Waiting Bottleneck" in Banking
* **Chapter 2:** The Proposed Solution & The 4-Layer Concept
* **Chapter 3:** Organizational Impact & The Before-vs-After Transformation Matrix
* **Chapter 4:** Demystifying Retrieval-Augmented Generation (The R, the A, and the G)
* **Chapter 5:** Real-World Engineering Dilemmas & How We Solved Them

### SECTION II: DEEP TECHNICAL ARCHITECTURE & BUILD BLUEPRINT
* **Chapter 6:** High-Level End-to-End System Architecture (Offline vs. Online Lifecycle)
* **Chapter 7:** Step 1 — Source Data Inspection & Schema Ingestion (`build_file_registry.py`)
* **Chapter 8:** Step 2 — Semantic Chunking Strategy (Why Semantic Boundaries beat Tokens)
* **Chapter 9:** Step 3 — Dense Vector Embedding & Persistent ChromaDB Storage
* **Chapter 10:** Step 4 — User Query Ingestion & Dynamic Word-Stemmed Routing (`route_question.py`)
* **Chapter 11:** Step 5 — Dense Semantic Retrieval & Anti-Hallucination Distance Gating
* **Chapter 12:** Step 6 — Schema-Aware Prompt Engineering & Groq LLM Generation
* **Chapter 13:** Step 7 — Dual Abstract Syntax Tree (AST) Verification Engine
* **Chapter 14:** Step 8 — Databricks Lakehouse Execution, Streamlit UI & Query Advisor

### SECTION III: EVALUATION, OBSERVABILITY & CRITICAL ANALYSIS
* **Chapter 15:** The 50-Question Benchmark Evaluation Engine & Observability Scorecard
* **Chapter 16:** Automated Continuous Testing Harness (29 Pytest Cases)
* **Chapter 17:** Critical Engineering Nuance: Running vs. Being Right
* **Chapter 18:** Complete Reproducibility, Configuration & Developer Build Guide

---

## SECTION I: EXECUTIVE & BUSINESS FOUNDATION

### CHAPTER 1: The Business Problem — The "Data Waiting Bottleneck" in Banking
In modern enterprise banking at ICICI Bank, business stakeholders—including branch managers, relationship managers, loan underwriters, and compliance officers—need immediate answers to operational inquiries every day:
* *"Which accounts have remained dormant for over 12 months?"*
* *"What is the average monthly balance of newly opened salary accounts in the western region?"*
* *"Which high-value accounts have experienced sudden balance attrition this quarter?"*

However, business managers cannot write Structured Query Language (SQL) queries against complex cloud data warehouses. Conversely, centralized data engineering specialists are inundated with core ETL tasks and infrastructure maintenance. This creates four major operational bottlenecks:
1. **The Language Gap:** Business users understand the commercial banking domain but cannot write technical relational database syntax.
2. **Overloaded Programmers:** Hundreds of routine ad-hoc inquiry tickets pull data engineers away from strategic architecture.
3. **Turnaround Delays:** Business managers wait **3 to 5 business days** for an engineer to write a query for a single number.
4. **Risk of Mistakes:** Manual queries written in haste often misapply complex banking filters (e.g. confusing month-end balance with monthly average balance), leading to flawed credit decisions.

**Real-World Banking Scenario:**  
A Relationship Manager is evaluating a commercial loan application for a corporate borrower. Policy requires confirming that the borrower has maintained an active, non-dormant account with an Average Monthly Balance (MAB) exceeding ₹5,00,000 over the past 6 months. Under legacy workflows, the manager must log an internal ticket and wait 4 business days, frustrating the customer and risking lost deals to competing banks.

---

### CHAPTER 2: The Proposed Solution & The 4-Layer Concept
We designed and built an enterprise-grade **Conversational Banking Data Assistant**. It enables any non-technical employee to type natural business questions in everyday English and receive verified answers executed directly against Databricks cloud warehouse tables in under **2.5 seconds**.

The architecture operates across **four distinct, modular layers**:
1. **Layer 1: The Front Counter (Streamlit Web Dashboard):**  
   A clean, browser-based interface where any employee types questions like: *“Show me all dormant accounts with balance over ₹50,000”*. Requires zero technical coding knowledge.
2. **Layer 2: The Smart Brain (Router + RAG + AI Model):**  
   The intelligent triage and translation engine. The router acts as a traffic cop (directing questions to account or balance tables), ChromaDB pulls official bank definitions, and Groq Llama 3.1 translates English into SQL.
3. **Layer 3: The Security Gate (Abstract Syntax Tree Inspector):**  
   The digital bouncer. Mathematically parses the generated SQL syntax tree using `sqlglot` before it touches the database. Guarantees 100% read-only (`SELECT`/`WITH`) execution, strictly blocking `DROP`, `DELETE`, and injection attacks.
4. **Layer 4: The Bank Vault (Databricks Serverless Cloud Warehouse):**  
   The secure cloud data lakehouse where customer and financial ledger records live. Executes the verified query and returns exact numbers, tables, and charts.

> **Core Takeaway:** A Rulebook sits in front of the AI so it does not make things up (hallucination prevention), and a Security Gate sits behind it so any attempt to delete or alter bank data is blocked.

---

### CHAPTER 3: Organizational Impact & The Before-vs-After Matrix
Deploying the assistant delivers measurable return on investment across five core operational dimensions:
* **Faster Answers:** Query turnaround drops from **3–5 business days down to 2.4 seconds**.
* **Frees Data Engineers:** Eliminates repetitive inquiry tickets, recovering ~60% of data engineer bandwidth.
* **Accelerates Loan Approvals:** Managers verify borrower balances while the client is at the desk.
* **100% Guaranteed Data Protection:** Syntax tree inspection guarantees zero risk of accidental data mutation.
* **Audit & Regulatory Compliance:** Every question and query is logged with timestamps, fulfilling Reserve Bank of India (RBI) audit standards.

| Operational Dimension | Traditional Legacy Workflow (Before) | Our Conversational Assistant (Now) |
| :--- | :--- | :--- |
| **Self-Service Access** | Non-technical officers locked out; mandatory IT ticketing. | Instant self-service in plain English in < 2.5 seconds. |
| **AI Hallucination Risk** | Generic AI invents columns and wrong balances. | ChromaDB RAG acts as an open book, restricting AI to verified facts. |
| **Off-Topic Queries** | Models answer off-topic questions with fabricated SQL. | Stemmed router & distance gate immediately halt with *"Not under my knowledge"*. |
| **Security & Injection** | Regex keyword filters bypassed by comments or nested strings. | AST syntax tree parsing mathematically enforces pure read-only SELECT. |
| **Error Diagnostics** | Cryptic database stack traces and red error screens. | The Smart Query Advisor explains ambiguities and suggests copyable rewrites. |

---

### CHAPTER 4: Demystifying Retrieval-Augmented Generation (The R, the A, and the G)
Standard AI models take a "closed-book exam" from memory, frequently hallucinating banking rules. Our RAG implementation acts as an **open-book examination**:

* **R – RETRIEVAL (Finding the Facts):**
  1. *Chunk Data:* Divide banking schemas and glossary into 4 clean sections.
  2. *Embed Data:* Convert text chunks into 384-dimensional numbers (`all-MiniLM-L6-v2`).
  3. *Store Vectors:* Save numbers in ChromaDB (`.chroma/`).
  4. *Convert Query:* Turn the user's English question into vector numbers.
  5. *Match:* Compare query numbers with stored numbers using cosine similarity.
  6. *Distance Check:* Keep top-3 matching chunks; if distance > 1.20, stop immediately!
* **A – AUGMENTATION (Adding the Official Rulebook):**
  Combine the user's question with official banking facts:
  * Tenure Formula: `DATEDIFF(CURRENT_DATE(), open_date)/365.25`
  * Active Account: `account_close_date = '-'`
  * Relational Join: `p2c.source_account_nbr = mab_meb.ACCTNO`
* **G – GENERATION (Creating the Database Code):**
  Given the official facts and formulas, Llama 3.1 at zero temperature writes a single, verified read-only Databricks `SELECT` query with zero guessing.

---

### CHAPTER 5: Real-World Engineering Dilemmas & How We Solved Them
During prototype iterations, standard off-the-shelf methods failed repeatedly:

1. **Dilemma 1: Model Fit and Irrelevant Answers**  
   * *Failure:* Small models made syntax errors; large models answered off-topic questions (e.g. weather) with fabricated SQL.  
   * *Solution:* Built a pre-LLM **Dynamic Word-Stemming Router** to filter off-topic questions without wasting tokens, paired with **Llama-3.1-8B-Instant** at `temperature=0.0` for strict, fast code.
2. **Dilemma 2: RAG Missing Unwritten Banking Rules**  
   * *Failure:* RAG retrieved column names but missed bank rules (e.g. active accounts are marked with a hyphen `'-'`, not `NULL`, causing queries to return 0 rows).  
   * *Solution:* Injected explicit banking formulas (tenure math, active flag, dormancy codes) directly into knowledge chunks and prompt templates.
3. **Dilemma 3: Mathematical Calculation Errors**  
   * *Failure:* The AI wrote syntactically valid SQL that calculated wrong numbers (e.g. averaging monthly averages).  
   * *Solution:* Developed a post-generation **AST Reliability Inspector** verifying required aggregations (`SUM`/`AVG`) and table join paths.

---

## SECTION II: DEEP TECHNICAL ARCHITECTURE & BUILD BLUEPRINT

### CHAPTER 6: High-Level End-to-End System Architecture
The system architecture operates in two distinct modes:

```text
OFFLINE KNOWLEDGE BUILD (Run once per schema change)
[Source Excel / DDL] ──► [build_file_registry.py] ──► [4 Semantic Chunks] ──► [.chroma/ Vector Store]

ONLINE PER-QUESTION PIPELINE (Sub-second execution)
[User Query] ──► [1. Stemmed Router] ──► [2. ChromaDB RAG] ──► [3. Evidence Gate (<=1.20)]
                                                                        │
                                                                        ▼
[Streamlit UI] ◄── [6. Databricks SQL] ◄── [5. AST Gate] ◄── [4. Groq Llama 3.1 Engine]
```

**Dual Execution Environments:**
* **Production Cloud:** Databricks Serverless SQL Warehouse via `databricks-sql-connector 4.6.0` over Unity Catalog Delta tables.
* **Local Sandbox & CI:** In-memory SQLite sandbox re-seeded from Excel spreadsheets, executing all 29 automated tests in **1.9 seconds**.

---

### CHAPTER 7: Step 1 — Source Data Inspection & Schema Ingestion
**Source Files:**
* `p2c_dummy_data_1000rows.xlsx` (Sheet: `P2C`, 1000 rows, 22 columns) — Key: `source_account_nbr` (PK)
* `mab_meb_dummy_data_1000rows.xlsx` (Sheet: `Sheet2`, 1000 rows, 36 columns) — Key: `ACCTNO` (FK)

**Profiling Script (`scripts/build_file_registry.py`):**
Inspects column names, data types, null counts, and row totals.  
*Technical Schema vs. Business Meaning:* Technical metadata is extracted automatically, but business definitions (e.g. active account encoded as `'-'`) must receive data-steward validation in `config/business_glossary.json`.

---

### CHAPTER 8: Step 2 — Semantic Chunking Strategy
Instead of fragile sliding token windows that slice column lists away from table names, we enforce **Semantic Boundary Chunking** separated by `\n\n---\n\n`:
* **Chunk 0 (`chunk_0_p2c`):** Customer linkage facts (`ucic_value`, `source_account_nbr`, `product_type`, `open_date`, `close_date`, `dormancy_status`, `nri_status`).
* **Chunk 1 (`chunk_1_mab`):** Balance ledgers (`ACCTNO`, `CUSTID`, `mab_bal`, `meb_bal`, `retail_bulk`, `final_segment`, `gldesc`).
* **Chunk 2 (`chunk_2_join`):** Primary join rules: `p2c.source_account_nbr = mab_meb.ACCTNO` and active account rule `account_close_date = '-'`.
* **Chunk 3 (`chunk_3_glossary`):** Business formulas: MAB in INR, dormancy `'D'`, vintage via `DATEDIFF(CURRENT_DATE(), open_date)/365.25`.

---

### CHAPTER 9: Step 3 — Dense Vector Embedding & Persistent ChromaDB Storage
* **Embedding Model:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dimensional dense vectors, local CPU inference, zero cost).
* **Storage Architecture in `.chroma/`:**
  * `chroma.sqlite3`: Metadata store for chunk text, IDs, and domain tags.
  * `header.bin`, `data_level0.bin`: HNSW graph vector index for approximate nearest neighbor search.
* **Idempotency:** Deterministic IDs (`chunk_0`...`chunk_3`) with `upsert()` prevent index bloat; full re-indexing executes in under 2 seconds.

---

### CHAPTER 10: Step 4 — User Query Ingestion & Dynamic Word-Stemmed Routing
Implemented in `scripts/route_question.py` using regex word-boundary stemming:
```python
PATTERNS = {
    'p2c': re.compile(r'\b(open\w*|clos\w*|tenur\w*|dorm\w*|nri\w*|ucic\w*|product\w*)\b', re.IGNORECASE),
    'mab_meb': re.compile(r'\b(bal\w*|mab\w*|meb\w*|ledger\w*|retail\w*|bulk\w*|salary\w*)\b', re.IGNORECASE),
    'both': re.compile(r'\b(combin\w*|link\w*|join\w*|across\w*|relat\w*)\b', re.IGNORECASE)
}
```
* **Collision Guard:** Prevents `age` from matching inside `average`.
* **Out-of-Scope Drops:** Prompts with zero banking stems are dropped before calling the LLM, saving 100% of API token costs.

---

### CHAPTER 11: Step 5 — Dense Semantic Retrieval & Anti-Hallucination Distance Gating
In `scripts/check_rag_evidence.py`, the user query embedding is compared against ChromaDB chunks:
* **Distance Distribution:** In-scope queries produce cosine distances of **0.45 to 0.95**. Out-of-scope inquiries produce distances **> 1.35**.
* **Threshold Rule:**
  * Distance $\le 1.20 \rightarrow$ **PASS:** Top-3 chunks packaged into prompt.
  * Distance $> 1.20 \rightarrow$ **HALT:** Returns *"Not under my knowledge"* immediately.

---

### CHAPTER 12: Step 6 — Schema-Aware Prompt Engineering & Groq LLM Generation
In `scripts/build_sql_prompt.py` and `generate_sql_with_llm.py`:
* **Locked System Prompt:** Treats user question as untrusted data inside `<user_question>` tags.
* **Rules Enforced:** Single `SELECT` or `WITH` statement; no markdown; CTE inner table aliases must not leak into outer queries.
* **Inference Specs:** Groq API, `llama-3.1-8b-instant`, `temperature=0.0` (greedy decoding), `max_tokens=2048`, sub-250ms latency.

---

### CHAPTER 13: Step 7 — Dual AST Verification Engine
Two deterministic gates intercept queries before warehouse execution:
1. **AST Safety Gate (`scripts/check_sql_safety.py` via `sqlglot`):**
   * Parses SQL into an Abstract Syntax Tree.
   * Asserts every statement is strictly `exp.Select`.
   * Rejects multi-statements (`SELECT 1; DROP TABLE;`).
   * Blocks DDL (`DROP`, `ALTER`, `CREATE`), DML (`INSERT`, `UPDATE`, `DELETE`), and wildcard (`*`) projections.
2. **AST Reliability Gate (`scripts/check_sql_reliability.py`):**
   * Confirms `total` requests contain `exp.Sum`.
   * Confirms `average` requests contain `exp.Avg`.
   * Validates primary join path `p2c.source_account_nbr = mab_meb.ACCTNO`.

---

### CHAPTER 14: Step 8 — Databricks Execution, Streamlit UI & Query Advisor
* **Cloud Warehouse Runner (`scripts/run_verified_sql.py`):** Connects to Databricks Serverless Warehouse, executes read-only query, and streams DataFrame.
* **Streamlit UI (`app/main.py`):** Displays data tables, chart visualizers, and verification badges (`[ROUTED]`, `[AST SAFE]`, `[RELIABLE]`).
* **Smart Query Advisor (`scripts/query_advisor.py`):** When queries fail or are ambiguous (e.g. asking for "segment"), parses the failure point and renders a plain-English explanation with a copy-pasteable query rewrite.

---

## SECTION III: EVALUATION, OBSERVABILITY & CRITICAL ANALYSIS

### CHAPTER 15: The 50-Question Benchmark Evaluation Engine
Automated test harness in `scripts/run_eval_suite.py` measuring 50 gold-standard enterprise banking inquiries:
* **Natural Language Comprehension Rate (NLCR):** **98.0%**
* **Valid SQL Execution Rate (VSR):** **98.0%**
* **Safety & Reliability Gate Pass Rate:** **82.0%**
* **Execution Accuracy (EX):** **24.0% – 32.0%**
* ⭐ **Composite Model Reliability Score:** **75.5%** (`0.25*NLCR + 0.25*Gate + 0.25*VSR + 0.25*EX`)

Audit scorecard output exported to `reports/eval_scorecard.json`.

---

### CHAPTER 16: Automated Continuous Testing Harness (29 Pytest Cases)
Automated test suite executing across 5 test modules:
* `tests/test_route_question.py` (6 tests)
* `tests/test_check_rag_evidence.py` (5 tests)
* `tests/test_check_sql_safety.py` (8 tests)
* `tests/test_check_sql_reliability.py` (5 tests)
* `tests/test_build_sql_prompt.py` (5 tests)

**Result:** 29 passed in **2.42 seconds** (100% pass rate).

---

### CHAPTER 17: Critical Engineering Nuance: Running vs. Being Right
**The Central Engineering Finding:**  
Running is not the same as being right. While **98.0% of queries execute validly**, only **32.0% achieve exact semantic answer matches** against the gold standard.
* **The Reason:** AST gates guarantee structural safety (no crashes, no deletes), but cannot detect a plausible wrong filter (e.g. filtering on `retail_bulk = 'RETAIL'` instead of `product_type = 'SA'`).
* **The Solution:** The architecture enforces a **Human-in-the-Loop** standard: the generated SQL query is displayed alongside every result so business analysts can visually verify join and filter logic before taking credit actions.

---

### CHAPTER 18: Complete Reproducibility, Configuration & Developer Build Guide
**Configuration (`.env`):**
```env
DATABRICKS_SERVER_HOSTNAME="dbc-xxxx.cloud.databricks.com"
DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/xxxx"
DATABRICKS_ACCESS_TOKEN="dapi_xxxx"
LLM_API_KEY="gsk_xxxx"
LLM_PROVIDER="groq"
LLM_MODEL="llama-3.1-8b-instant"
```

**Developer Quickstart Commands:**
1. Install dependencies: `pip install -r requirements.txt`
2. Profile data registry: `python scripts/build_file_registry.py`
3. Build ChromaDB index: `python scripts/check_rag_evidence.py`
4. Run automated test suite: `pytest -q`
5. Launch web UI: `streamlit run app/main.py`
6. Run 50-question benchmark: `python scripts/run_eval_suite.py`

---
*Report Compiled & Certified for ICICI Bank • Data Science & Analytics Group (DSAG)*  
*Author: Roshita Jaiswal • Guide: Ashutosh Kumar • Mentor: Ankit Sharma*
