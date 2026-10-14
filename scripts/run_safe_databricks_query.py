"""
Step 17: Run Safe Databricks Query
Purpose: Execute only SQL that passes read-only safety checks.
Input: SQL text from terminal and Databricks settings from .env.
Output: Query result rows or BLOCK reason.
Run: python scripts/run_safe_databricks_query.py "SELECT product_type, COUNT(*) AS total_accounts FROM workspace.default.p2c GROUP BY product_type"
"""

import os
import sys

from databricks import sql
from dotenv import load_dotenv

from check_sql_safety import check_sql_safety


MAX_ROWS_TO_PRINT = 20


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def get_connection():
    return sql.connect(
        server_hostname=get_required_env("DATABRICKS_SERVER_HOSTNAME"),
        http_path=get_required_env("DATABRICKS_HTTP_PATH"),
        access_token=get_required_env("DATABRICKS_ACCESS_TOKEN"),
    )


def run_query(query: str) -> list:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchmany(MAX_ROWS_TO_PRINT)

    return rows


def main() -> None:
    load_dotenv()

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "SELECT product_type, COUNT(*) AS total_accounts FROM workspace.default.p2c GROUP BY product_type"

    safety_result = check_sql_safety(query)

    if safety_result["decision"] == "BLOCK":
        print("Decision: BLOCK")
        print(f"Reason: {safety_result['reason']}")
        return

    rows = run_query(query)

    print("Decision: ALLOW")
    print(f"Reason: {safety_result['reason']}")
    print(f"Showing up to {MAX_ROWS_TO_PRINT} rows:")

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()