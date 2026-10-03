"""This script will create simple text chunks for RAG.
Later, ChromaDB will store these chunks as searchable knowledge."""

from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")
REGISTRY_PATH = REPORTS_DIR / "file_registry.csv"
METADATA_PATH = REPORTS_DIR / "rag_metadata.txt"


TABLE_DESCRIPTIONS = {
    "p2c_dummy_data_1000rows.xlsx": {
        "table_name": "p2c",
        "description": "Customer-account linkage data. It contains customer identifiers, account numbers, product type, account status, dormancy status, NRI status, income segment, service segment, and relationship details.",
        "important_columns": [
            "ucic_value",
            "source_account_nbr",
            "account_open_date",
            "account_close_date",
            "product_type",
            "dormancy_status",
            "nri_status",
            "income_segment",
            "service_segment",
            "linkage_identifier",
        ],
    },
    "mab_meb_dummy_data_1000rows.xlsx": {
        "table_name": "mab_meb",
        "description": "Monthly balance data. It contains account number, customer ID, monthly average balance, monthly end balance, segment, final segment, balance bucket, fixed deposit bucket, and income segment.",
        "important_columns": [
            "ACCTNO",
            "CUSTID",
            "mab_bal",
            "meb_bal",
            "segment",
            "final_segment",
            "bal_bucket",
            "fd_bucket",
            "income_segment",
        ],
    },
}


JOIN_RULES = [
    "p2c.source_account_nbr joins to mab_meb.ACCTNO.",
]


BUSINESS_TERMS = [
    "MAB means Monthly Average Balance.",
    "MEB means Monthly End Balance.",
    "UCIC means Unique Customer Identification Code.",
    "NRI means Non-Resident Indian.",
    "Dormant accounts are identified using dormancy_status = 'D'.",
    "Open accounts likely have account_close_date = '-'.",
]


def build_metadata_text(registry_df: pd.DataFrame) -> str:
    chunks = []

    for _, row in registry_df.iterrows():
        source_file = row["source_file"]
        sheet_name = row["sheet_name"]

        table_info = TABLE_DESCRIPTIONS.get(source_file)

        if table_info is None:
            table_name = source_file.replace(".xlsx", "").lower()
            description = "No manual description available yet."
            important_columns = []
        else:
            table_name = table_info["table_name"]
            description = table_info["description"]
            important_columns = table_info["important_columns"]

        chunk = f"""
Table name: {table_name}
Source file: {source_file}
Sheet name: {sheet_name}
Row count: {row["row_count"]}
Column count: {row["column_count"]}
Description: {description}
Important columns: {", ".join(important_columns)}
All columns: {row["columns"]}
""".strip()

        chunks.append(chunk)

    chunks.append("Join rules:\n" + "\n".join(JOIN_RULES))
    chunks.append("Business terms:\n" + "\n".join(BUSINESS_TERMS))

    return "\n\n---\n\n".join(chunks)


def main() -> None:
    registry_df = pd.read_csv(REGISTRY_PATH)

    metadata_text = build_metadata_text(registry_df)

    METADATA_PATH.write_text(metadata_text, encoding="utf-8")

    print(f"RAG metadata saved to: {METADATA_PATH}")
    print(metadata_text)


if __name__ == "__main__":
    main()