"""
Step 18: Run Verified SQL
Purpose: Check SQL safety and reliability before running it in Databricks.
Input: User question and SQL text from terminal.
Output: Query result rows, or BLOCK/REVIEW reason.
Run: python scripts/run_verified_sql.py "Show total MAB by income segment" "SELECT income_segment, SUM(mab_bal) AS total_mab_bal FROM workspace.default.mab_meb GROUP BY income_segment"
"""

import sys

from dotenv import load_dotenv

from check_sql_reliability import check_sql_reliability
from check_sql_safety import check_sql_safety
from run_safe_databricks_query import MAX_ROWS_TO_PRINT
from run_safe_databricks_query import run_query


def run_verified_sql(question: str, sql_text: str) -> dict:
    safety_result = check_sql_safety(sql_text)

    if safety_result["decision"] == "BLOCK":
        return {
            "decision": "BLOCK",
            "reason": safety_result["reason"],
            "rows": [],
        }

    reliability_result = check_sql_reliability(question, sql_text)

    if reliability_result["decision"] == "REVIEW":
        return {
            "decision": "REVIEW",
            "reason": reliability_result["reason"],
            "rows": [],
        }

    rows = run_query(sql_text)

    return {
        "decision": "ALLOW",
        "reason": "SQL passed safety and reliability checks.",
        "rows": rows,
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

    if result["rows"]:
        print(f"\nShowing up to {MAX_ROWS_TO_PRINT} rows:")

        for row in result["rows"]:
            print(row)


if __name__ == "__main__":
    main()