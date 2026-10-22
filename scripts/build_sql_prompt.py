"""
Step 13: Build SQL Prompt
Purpose: Prepare safe context that will be sent to the LLM for SQL generation.
Input: User question from terminal.
Output: SQL-generation prompt, or BLOCK decision.
Run: python scripts/build_sql_prompt.py "Show total MAB by income segment"
"""

import sys

from check_ques_before_sql import run_pre_sql_checks


APPROVED_TABLES = [
    "workspace.default.p2c",
    "workspace.default.mab_meb",
]

SQL_RULES = [
    "Generate Databricks SQL only.",
    "Use only SELECT or WITH queries.",
    "Do not generate INSERT, UPDATE, DELETE, MERGE, DROP, ALTER, CREATE, TRUNCATE, or REPLACE.",
    "Do not use SELECT *.",
    "Use only approved tables and columns from the provided context.",
    "If the context is not enough, return exactly: Not under my knowledge.",
]


def build_prompt(question: str, route: str, retrieved_context: list[str]) -> str:
    context_text = "\n\n".join(retrieved_context)
    approved_tables_text = "\n".join(f"- {table}" for table in APPROVED_TABLES)
    sql_rules_text = "\n".join(f"- {rule}" for rule in SQL_RULES)

    prompt = f"""
You are a SQL generation assistant for a read-only Databricks analytics chatbot.

User question:
{question}

Question route:
{route}

Approved tables:
{approved_tables_text}

Retrieved RAG context:
{context_text}

SQL rules:
{sql_rules_text}

Return only one of these:
1. A single Databricks SELECT/WITH SQL query.
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