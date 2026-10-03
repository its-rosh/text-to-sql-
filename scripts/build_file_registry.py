"""Read all Excel files from data/
                ↓
detect file name, sheet name, row count, columns
                ↓
create a simple registry CSV
                ↓
save it to reports/file_registry.csv"""

from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")
REGISTRY_PATH = REPORTS_DIR / "file_registry.csv"


def build_registry_rows() -> list[dict]:
    registry_rows = []

    excel_files = sorted(DATA_DIR.glob("*.xlsx"))

    for file_path in excel_files:
        excel_file = pd.ExcelFile(file_path)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            registry_rows.append(
                {
                    "source_file": file_path.name,
                    "sheet_name": sheet_name,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": ", ".join(str(column) for column in df.columns),
                }
            )

    return registry_rows


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)

    registry_rows = build_registry_rows()
    registry_df = pd.DataFrame(registry_rows)

    registry_df.to_csv(REGISTRY_PATH, index=False)

    print(f"Registry saved to: {REGISTRY_PATH}")
    print(registry_df)


if __name__ == "__main__":
    main()