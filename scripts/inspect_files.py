from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")
REPORT_PATH = REPORTS_DIR / "excel_inspection.txt"

EXCEL_FILES = [
    DATA_DIR / "p2c_dummy_data_1000rows.xlsx",
    DATA_DIR / "mab_meb_dummy_data_1000rows.xlsx",
]


def write_line(report_file, text: str = "") -> None:
    print(text)
    report_file.write(text + "\n")


def inspect_excel_file(file_path: Path, report_file) -> None:
    write_line(report_file, "=" * 80)
    write_line(report_file, f"File: {file_path}")

    excel_file = pd.ExcelFile(file_path)
    write_line(report_file, f"Sheets: {excel_file.sheet_names}")

    for sheet_name in excel_file.sheet_names:
        write_line(report_file, "-" * 80)
        write_line(report_file, f"Sheet: {sheet_name}")

        df = pd.read_excel(file_path, sheet_name=sheet_name)

        write_line(report_file, f"Rows: {len(df)}")
        write_line(report_file, f"Columns: {len(df.columns)}")
        write_line(report_file, "Column names:")

        for column in df.columns:
            write_line(report_file, f"  - {column}")

        write_line(report_file)
        write_line(report_file, "Sample rows:")
        write_line(report_file, df.head(3).to_string(index=False))


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)

    with REPORT_PATH.open("w", encoding="utf-8") as report_file:
        for file_path in EXCEL_FILES:
            if not file_path.exists():
                write_line(report_file, f"Missing file: {file_path}")
                continue

            inspect_excel_file(file_path, report_file)

    print(f"\nInspection report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()