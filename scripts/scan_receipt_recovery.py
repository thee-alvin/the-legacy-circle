from pathlib import Path
from openpyxl import load_workbook
import re

ROOT = Path(".")

print("\n" + "="*80)
print("TLC CONTRIBUTION / RECEIPT RECOVERY SCAN")
print("="*80)

print("\n========== VALID XLSX FILES CONTAINING CONTRIBUTION IDs ==========")

for path in ROOT.rglob("*.xlsx"):
    text_path = str(path).lower()

    if any(skip in text_path for skip in [
        "\\.venv\\",
        "\\node_modules\\",
        "\\__pycache__\\"
    ]):
        continue

    try:
        wb = load_workbook(
            path,
            read_only=True,
            data_only=True
        )

        found = []

        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)

            try:
                headers = next(rows)
            except StopIteration:
                continue

            headers = [
                str(x).strip() if x is not None else ""
                for x in headers
            ]

            contribution_index = (
                headers.index("Contribution ID")
                if "Contribution ID" in headers
                else None
            )

            receipt_index = (
                headers.index("Receipt Number")
                if "Receipt Number" in headers
                else None
            )

            if contribution_index is None and receipt_index is None:
                continue

            for row in rows:
                contribution = (
                    str(row[contribution_index]).strip()
                    if contribution_index is not None
                    and contribution_index < len(row)
                    and row[contribution_index] is not None
                    else ""
                )

                receipt = (
                    str(row[receipt_index]).strip()
                    if receipt_index is not None
                    and receipt_index < len(row)
                    and row[receipt_index] is not None
                    else ""
                )

                if (
                    re.search(r"TLC-CON-0000(2[6-9]|3[0-3])$", contribution)
                    or
                    re.search(r"TLC/RCPT/2026/0000(2[6-9]|3[0-3])$", receipt)
                ):
                    found.append(
                        (
                            ws.title,
                            contribution,
                            receipt
                        )
                    )

        wb.close()

        if found:
            print("\nFILE:", path)
            for item in found:
                print("   ", item)

    except Exception:
        pass


print("\n========== TEXT / JSON RECEIPT RECORDS 26–33 ==========")

patterns = [
    "TLC/RCPT/2026/000026",
    "TLC/RCPT/2026/000027",
    "TLC/RCPT/2026/000028",
    "TLC/RCPT/2026/000029",
    "TLC/RCPT/2026/000030",
    "TLC/RCPT/2026/000031",
    "TLC/RCPT/2026/000032",
    "TLC/RCPT/2026/000033",
]

extensions = {
    ".json",
    ".txt",
    ".log",
    ".csv"
}

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    if path.suffix.lower() not in extensions:
        continue

    text_path = str(path).lower()

    if any(skip in text_path for skip in [
        "\\.venv\\",
        "\\node_modules\\",
        "\\__pycache__\\"
    ]):
        continue

    try:
        content = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        matches = [
            p for p in patterns
            if p in content
        ]

        if matches:
            print("\nFILE:", path)
            for match in matches:
                print("   FOUND:", match)

    except Exception:
        pass

print("\n========== SCAN COMPLETE ==========")
