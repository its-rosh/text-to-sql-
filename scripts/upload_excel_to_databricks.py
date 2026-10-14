"""
Step 16: Upload Excel To Databricks
Purpose: Load local dummy Excel files into Databricks tables.
Input: Excel files from data/ and table names from .env.
Output: Databricks Delta tables with uploaded rows.
Run: python scripts/upload_excel_to_databricks.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
from databricks import sql
from dotenv import load_dotenv


DATA_DIR = Path("data")
BATCH_SIZE = 100

UPLOAD_JOBS = [
    {
        "env_table_name": "DATABRICKS_P2C_TABLE",
        "file_path": DATA_DIR / "p2c_dummy_data_1000rows.xlsx",
        "sheet_name": "P2C",
        "schema": {
            "ucic_value": "STRING",
            "source_system_code": "STRING",
            "account_nbr": "STRING",
            "source_account_nbr": "STRING",
            "source_party_id": "STRING",
            "full_name": "STRING",
            "criteria": "STRING",
            "account_open_date": "DATE",
            "account_close_date": "STRING",
            "card_block_code": "STRING",
            "acc_holder": "STRING",
            "cust_const": "STRING",
            "cust_stat_code": "STRING",
            "schm_type": "STRING",
            "product_type": "STRING",
            "dormancy_status": "STRING",
            "nri_status": "STRING",
            "income_segment": "STRING",
            "service_segment": "STRING",
            "relation_type": "STRING",
            "linked_userid": "STRING",
            "linkage_identifier": "STRING",
        },
    },
    {
        "env_table_name": "DATABRICKS_MAB_MEB_TABLE",
        "file_path": DATA_DIR / "mab_meb_dummy_data_1000rows.xlsx",
        "sheet_name": "Sheet2",
        "schema": {
            "brcode": "STRING",
            "CUSTID": "STRING",
            "ACCTNO": "STRING",
            "CUST_NAME": "STRING",
            "conscode": "STRING",
            "status_code": "STRING",
            "nriflag": "STRING",
            "EMP_CODE": "STRING",
            "ledger_code": "STRING",
            "qo_flag": "STRING",
            "glcode": "STRING",
            "mab_bal": "DOUBLE",
            "meb_bal": "DOUBLE",
            "orig_fdamt": "DOUBLE",
            "mis_date": "DATE",
            "br_recal": "STRING",
            "gldesc": "STRING",
            "rtl_nonrtl": "STRING",
            "segment": "STRING",
            "nca_erv": "STRING",
            "final_segment": "STRING",
            "bal_bucket": "STRING",
            "fd_bucket": "STRING",
            "retail_bulk": "STRING",
            "sub_product": "STRING",
            "pbg_flag": "STRING",
            "source_seg": "STRING",
            "WM_EMPID": "STRING",
            "conscode_new": "STRING",
            "status_code_new": "STRING",
            "nriflag_new": "STRING",
            "caldate": "DATE",
            "income_segment": "STRING",
            "income_segment_mar": "STRING",
            "managed_profile": "STRING",
            "MANAGED_EMPID": "STRING",
        },
    },
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


def validate_table_name(table_name: str) -> None:
    if not table_name.startswith("workspace.default."):
        raise ValueError(
            f"Table {table_name} is blocked. "
            "For Free Edition upload, use workspace.default table names only."
        )


def sql_literal(value, data_type: str) -> str:
    if pd.isna(value):
        return "NULL"

    if data_type == "DOUBLE":
        return str(float(value))

    if data_type == "DATE":
        date_value = pd.to_datetime(value, errors="coerce")

        if pd.isna(date_value):
            return "NULL"

        return f"DATE '{date_value.strftime('%Y-%m-%d')}'"

    text = str(value).replace("'", "''")
    return f"'{text}'"


def create_table_if_needed(cursor, table_name: str, schema: dict) -> None:
    columns_sql = []

    for column_name, data_type in schema.items():
        columns_sql.append(f"`{column_name}` {data_type}")

    query = f"""
CREATE TABLE IF NOT EXISTS {table_name}
(
    {", ".join(columns_sql)}
)
USING DELTA
""".strip()

    cursor.execute(query)


def get_row_count(cursor, table_name: str) -> int:
    cursor.execute(f"SELECT COUNT(*) AS row_count FROM {table_name}")
    result = cursor.fetchone()

    return result.row_count


def insert_dataframe(cursor, table_name: str, df: pd.DataFrame, schema: dict) -> None:
    column_names = list(schema.keys())
    quoted_columns = ", ".join(f"`{column}`" for column in column_names)

    for start_index in range(0, len(df), BATCH_SIZE):
        batch_df = df.iloc[start_index : start_index + BATCH_SIZE]
        values_sql = []

        for _, row in batch_df.iterrows():
            row_values = [
                sql_literal(row[column], schema[column])
                for column in column_names
            ]

            values_sql.append("(" + ", ".join(row_values) + ")")

        insert_query = f"""
INSERT INTO {table_name}
({quoted_columns})
VALUES
{", ".join(values_sql)}
""".strip()

        cursor.execute(insert_query)


def upload_file(cursor, upload_job: dict, replace_existing: bool) -> None:
    table_name = get_required_env(upload_job["env_table_name"])
    validate_table_name(table_name)

    file_path = upload_job["file_path"]
    sheet_name = upload_job["sheet_name"]
    schema = upload_job["schema"]

    print(f"\nUploading: {file_path}")
    print(f"Target table: {table_name}")

    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df = df[list(schema.keys())]

    create_table_if_needed(cursor, table_name, schema)

    existing_rows = get_row_count(cursor, table_name)

    if existing_rows > 0 and not replace_existing:
        print(f"Skipped. Table already has {existing_rows} rows.")
        print("Use --replace only if you intentionally want to reload dummy data.")
        return

    if existing_rows > 0 and replace_existing:
        cursor.execute(f"TRUNCATE TABLE {table_name}")
        print(f"Existing rows removed from {table_name}.")

    insert_dataframe(cursor, table_name, df, schema)

    final_rows = get_row_count(cursor, table_name)
    print(f"Done. Final row count: {final_rows}")


def main() -> None:
    load_dotenv()

    replace_existing = "--replace" in sys.argv

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for upload_job in UPLOAD_JOBS:
                upload_file(cursor, upload_job, replace_existing)


if __name__ == "__main__":
    main()