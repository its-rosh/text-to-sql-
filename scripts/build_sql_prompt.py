"""
Step 13: Build SQL Prompt
Purpose: Prepare safe context that will be sent to the LLM for SQL generation.
Input: User question from terminal or API.
Output: SQL-generation prompt, or BLOCK decision.
Run: python scripts/build_sql_prompt.py "Show total MAB by income segment"
"""

import os
import sys
from dotenv import load_dotenv
from check_ques_before_sql import run_pre_sql_checks

load_dotenv()


def get_approved_tables(route: str = "both_tables") -> list[str]:
    p2c = os.getenv("DATABRICKS_P2C_TABLE", "workspace.default.p2c")
    mab = os.getenv("DATABRICKS_MAB_MEB_TABLE", "workspace.default.mab_meb")
    if route == "mab_meb":
        return [mab]
    elif route == "p2c":
        return [p2c]
    return [p2c, mab]


SQL_RULES = [
    "Generate Databricks SQL only.",
    "Use only SELECT or WITH queries.",
    "Do not generate INSERT, UPDATE, DELETE, MERGE, DROP, ALTER, CREATE, TRUNCATE, or REPLACE.",
    "Do not use SELECT * on physical database tables; explicitly specify needed column names.",
    "When joining p2c and mab_meb, always join ON p2c.source_account_nbr = mab_meb.ACCTNO.",
    "Do not join p2c if all requested columns (such as EMP_CODE, retail_bulk, mab_bal, meb_bal, gldesc) already exist in mab_meb. Only join p2c when customer attributes (full_name, account_open_date, account_close_date, dormancy_status, nri_status, ucic_value) are explicitly needed.",
    "When using CTEs (WITH clauses), downstream queries referencing a CTE must use the CTE name or unqualified column names (e.g., if FROM base, use base.account_close_date or account_close_date, NEVER inner aliases like p2c.account_close_date).",
    "Use only approved tables and columns from the provided context.",
    "Do not include markdown code block formatting (like ```sql) or explanatory text. Return raw SQL only.",
    "If the context is not enough to answer the question, return exactly: Not under my knowledge.",
]

APPROVED_COLUMN_ALIASES_AND_SYNONYMS = [
    "- Tenure / Account Age (in years): DATEDIFF(CURRENT_DATE(), account_open_date) / 365.25",
    "- Open accounts filter: account_close_date = '-' (hyphen indicates active/open)",
    "- Closed accounts filter: account_close_date <> '-' (or account_close_date != '-')",
    "- Dormancy filter: dormancy_status = 'D' (A = Active, I = Inactive)",
    "- NRI flag in p2c: nri_status = 'Y' (or 'N')",
    "- NRI flag in mab_meb: nriflag = 'Y' (or 'N')",
    "- Balances: mab_bal = Monthly Average Balance, meb_bal = Month-End Balance",
    "- Customer segment in mab_meb: final_segment or income_segment",
    "- Customer name in p2c: full_name (repeatable, group by full_name for customer-level counts)",
    "- Customer name in mab_meb: CUST_NAME (uppercase)",
    "- Employee code: EMP_CODE exists ONLY in mab_meb (it does NOT exist in p2c; never write p.EMP_CODE).",
    "- Retail vs Bulk: retail_bulk exists in mab_meb (values: 'RETAIL', 'BULK').",
    "- Account number: p2c.source_account_nbr and mab_meb.ACCTNO",
    "- Dates are stored as ISO strings (YYYY-MM-DD); use SUBSTR(col, 1, 4) for year or to_date(col) for date functions",
]


def build_prompt(question: str, route: str, retrieved_context: list[str]) -> str:
    context_text = "\n\n".join(retrieved_context)
    approved_tables = get_approved_tables(route)
    approved_tables_text = "\n".join(f"- {table}" for table in approved_tables)
    sql_rules_text = "\n".join(f"- {rule}" for rule in SQL_RULES)
    aliases_text = "\n".join(APPROVED_COLUMN_ALIASES_AND_SYNONYMS)

    prompt = f"""
You are an expert SQL generation assistant for a read-only Databricks analytics chatbot.

User question:
{question}

Question route:
{route}

Approved tables:
{approved_tables_text}

Approved Column Definitions & Derived Formulas:
{aliases_text}

Retrieved RAG context:
{context_text}

SQL rules:
{sql_rules_text}

Return only one of these:
1. A single Databricks SELECT/WITH SQL query (pure SQL without markdown fences or comments).
2. Not under my knowledge.
""".strip()

    return prompt


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Show total MAB by income segment"

    pre_sql_result = run_pre_sql_checks(question)

    if pre_sql_result["decision"] == "BLOCK":
        print("Decision: BLOCK")
        print(f"Reason: {pre_sql_result['reason']}")
        print(f"Final answer: {pre_sql_result['final_answer']}")
        return

    prompt = build_prompt(
        question=question,
        route=pre_sql_result["route"],
        retrieved_context=pre_sql_result["retrieved_context"],
    )

    print(prompt)


if __name__ == "__main__":
    main()
