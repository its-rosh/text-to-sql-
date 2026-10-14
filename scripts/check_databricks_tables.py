"""
Step 15: Check Databricks Tables
Purpose: Verify required project tables exist and can be read.
Input: Databricks connection and table names from .env.
Output: Row count for each table, or clear error.
Run: python scripts/check_databricks_tables.py
"""

import os

from databricks import sql
from dotenv import load_dotenv


TABLE_ENV_NAMES = [
    "DATABRICKS_P2C_TABLE",
    "DATABRICKS_MAB_MEB_TABLE",
]


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


def count_rows(cursor, table_name: str) -> int:
    query = f"SELECT COUNT(*) AS row_count FROM {table_name}"
    cursor.execute(query)
    result = cursor.fetchone()

    return result.row_count


def main() -> None:
    load_dotenv()

    table_names = [get_required_env(env_name) for env_name in TABLE_ENV_NAMES]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for table_name in table_names:
                row_count = count_rows(cursor, table_name)
                print(f"{table_name}: {row_count} rows")


if __name__ == "__main__":
    main()