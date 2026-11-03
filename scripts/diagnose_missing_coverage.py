import json
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(".")

# ------------------------------------------------------------
# RECEIPTS
# ------------------------------------------------------------

with (ROOT / "data/receipts/receipts.json").open(
    "r",
    encoding="utf-8"
) as f:
    data = json.load(f)

receipts = (
    data.get("receipts", [])
    if isinstance(data, dict)
    else data
)

wanted = {
    "TLC/RCPT/2026/000028",
    "TLC/RCPT/2026/000031",
    "TLC/RCPT/2026/000032",
    "TLC/RCPT/2026/000033",
}

print("=" * 80)
print("RECEIPTS WITHOUT COVERAGE")
print("=" * 80)

for receipt in receipts:

    number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if number in wanted:

        print()
        print("RECEIPT:", number)
        print("MEMBER:", receipt.get("member_id"))
        print("NAME:", receipt.get("member_name"))
        print("DATE:", receipt.get("payment_date"))
        print("AMOUNT:", receipt.get("amount"))
        print("TYPE:", receipt.get("payment_type"))
        print("DESCRIPTION:", receipt.get("description"))
        print("REFERENCE:", receipt.get("payment_reference"))
        print("STATUS:", receipt.get("status"))

# ------------------------------------------------------------
# COVERAGE LEDGER
# ------------------------------------------------------------

path = ROOT / "data/spreadsheets/03_CONTRIBUTION_COVERAGE.xlsx"

wb = load_workbook(
    path,
    read_only=True,
    data_only=True
)

ws = wb["Coverage Ledger"]

headers = [
    c.value
    for c in ws[1]
]

rows = list(
    ws.iter_rows(
        min_row=2,
        values_only=True
    )
)

print()
print("=" * 80)
print("EXISTING COVERAGE FOR THE SAME MEMBERS")
print("=" * 80)

member_col = headers.index("Member ID")
receipt_col = headers.index("Receipt Number")
week_col = headers.index("Coverage Week #")
month_col = headers.index("Coverage Month")
amount_col = headers.index("Allocated Amount")
status_col = headers.index("Allocation Status")

target_members = {
    "TLC/003/2026",
    "TLC/007/2026",
    "TLC/006/2026",
}

for row in rows:

    if len(row) <= max(
        member_col,
        receipt_col,
        week_col,
        month_col,
        amount_col,
        status_col
    ):
        continue

    if row[member_col] not in target_members:
        continue

    print(
        row[receipt_col],
        "|",
        row[member_col],
        "| Week", row[week_col],
        "| Month", row[month_col],
        "| Allocated", row[amount_col],
        "|", row[status_col]
    )

wb.close()


# ------------------------------------------------------------
# FIND COVERAGE-RELATED CODE
# ------------------------------------------------------------

print()
print("=" * 80)
print("COVERAGE-RELATED PYTHON FILES")
print("=" * 80)

for path in (ROOT / "app").rglob("*.py"):

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        if any(
            term in text.lower()
            for term in [
                "coverage ledger",
                "03_contribution_coverage",
                "allocated amount",
                "coverage week",
                "allocation status",
                "coverage_month"
            ]
        ):
            print(path)

    except Exception:
        pass
