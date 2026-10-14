"""
Step 14: Test Databricks Connection
Purpose: Verify Python can connect to Databricks SQL Warehouse.
Input: Databricks settings from .env.
Output: Connection success or error message.
Run: python scripts/test_databricks_connection.py
"""

import os

from databricks import sql
from dotenv import load_dotenv


TEST_QUERY = "SELECT 1 AS connection_test"


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def test_connection() -> None:
    load_dotenv()

    server_hostname = get_required_env("DATABRICKS_SERVER_HOSTNAME")
    http_path = get_required_env("DATABRICKS_HTTP_PATH")
    access_token = get_required_env("DATABRICKS_ACCESS_TOKEN")

    with sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(TEST_QUERY)
            result = cursor.fetchone()

    print("Databricks connection successful.")
    print(f"Test query result: {result}")


def main() -> None:
    test_connection()


if __name__ == "__main__":
    main()