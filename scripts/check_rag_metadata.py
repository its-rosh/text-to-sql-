### This script will check whether reports/rag_metadata.txt contains the minimum information our RAG needs.
"""Does rag_metadata.txt exist?
Does it contain p2c?
Does it contain mab_meb?
Does it contain join rule?
Does it contain MAB/MEB business terms?"""

from pathlib import Path


METADATA_PATH = Path("reports") / "rag_metadata.txt"


REQUIRED_TEXT = [
    "Table name: p2c",
    "Table name: mab_meb",
    "p2c.source_account_nbr joins to mab_meb.ACCTNO",
    "MAB means Monthly Average Balance",
    "MEB means Monthly End Balance",
    "Dormant accounts are identified using dormancy_status = 'D'",
]


def main() -> None:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {METADATA_PATH}")

    metadata_text = METADATA_PATH.read_text(encoding="utf-8")

    missing_items = []

    for required_item in REQUIRED_TEXT:
        if required_item not in metadata_text:
            missing_items.append(required_item)

    if missing_items:
        print("RAG metadata check failed.")
        print("Missing required text:")

        for item in missing_items:
            print(f"- {item}")

        raise SystemExit(1)

    print("RAG metadata check passed.")


if __name__ == "__main__":
    main()