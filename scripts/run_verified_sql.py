"""
Step 18: Run Verified SQL
Purpose: Check SQL safety and reliability before executing query in Databricks SQL Warehouse.
Input: User question and SQL text.
Output: Query result rows, or BLOCK/REVIEW reason.
Run: python scripts/run_verified_sql.py "Show total MAB by income segment" "SELECT income_segment, SUM(mab_bal) FROM workspace.default.mab_meb GROUP BY income_segment"
"""

import os
import sys
from dotenv import load_dotenv

from check_sql_reliability import check_sql_reliability
from check_sql_safety import check_sql_safety
from run_safe_databricks_query import run_query


def run_verified_sql(
    question: str,
    sql_text: str,
    skip_reliability_check: bool = False,
    max_rows: int | None = None,
) -> dict:
    load_dotenv()

    safety_result = check_sql_safety(sql_text)
    if safety_result["decision"] == "BLOCK":
        return {
            "decision": "BLOCK",
            "reason": safety_result["reason"],
            "rows": [],
            "source": "none",
        }

    if not skip_reliability_check:
        reliability_result = check_sql_reliability(question, sql_text)
        if reliability_result["decision"] == "REVIEW":
            return {
                "decision": "REVIEW",
                "reason": reliability_result["reason"],
                "rows": [],
                "source": "none",
            }

    # Execute directly in Databricks
    try:
        rows = run_query(sql_text, max_rows=max_rows)
        return {
            "decision": "ALLOW",
            "reason": "SQL passed safety and reliability checks (Executed in Databricks).",
            "rows": rows,
            "source": "databricks",
        }
    except Exception as err:
        return {
            "decision": "BLOCK",
            "reason": f"Databricks execution error: {err}",
            "rows": [],
            "source": "databricks",
        }


def main() -> None:
    load_dotenv()

    if len(sys.argv) < 3:
        print("Usage:")
        print(
            'python scripts/run_verified_sql.py '
            '"Show total MAB by income segment" '
            '"SELECT income_segment, SUM(mab_bal) FROM workspace.default.mab_meb GROUP BY income_segment"'
        )
        return

    question = sys.argv[1]
    sql_text = sys.argv[2]

    result = run_verified_sql(question, sql_text)

    print(f"Question: {question}")
    print(f"SQL: {sql_text}")
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")
    print(f"Source: {result.get('source')}")
    print(f"Rows returned: {len(result.get('rows', []))}")


if __name__ == "__main__":
    main()
