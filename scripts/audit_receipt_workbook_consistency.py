import json
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(".")
WORKBOOK = ROOT / "data" / "spreadsheets" / "02_CONTRIBUTIONS.xlsx"
RECEIPTS_FILE = ROOT / "data" / "receipts" / "receipts.json"

# ------------------------------------------------------------
# LOAD WORKBOOK RECEIPTS
# ------------------------------------------------------------

wb = load_workbook(
    WORKBOOK,
    read_only=True,
    data_only=True
)

ws = wb["Contributions"]

headers = [
    cell.value
    for cell in ws[1]
]

receipt_col = headers.index("Receipt Number")

workbook_receipts = {}

for row in ws.iter_rows(
    min_row=2,
    values_only=True
):
    value = row[receipt_col]

    if value:
        workbook_receipts[
            str(value).strip()
        ] = row

wb.close()

# ------------------------------------------------------------
# LOAD RECEIPT STORE
# ------------------------------------------------------------

with RECEIPTS_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)

if isinstance(data, dict):
    receipts = data.get("receipts", [])
else:
    receipts = data

receipt_store = {}

for receipt in receipts:
    number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if number:
        receipt_store[number] = receipt

# ------------------------------------------------------------
# COMPARE
# ------------------------------------------------------------

print("=" * 80)
print("TLC RECEIPT ↔ CONTRIBUTION WORKBOOK AUDIT")
print("=" * 80)

missing_from_workbook = sorted(
    set(receipt_store) - set(workbook_receipts)
)

extra_in_workbook = sorted(
    set(workbook_receipts) - set(receipt_store)
)

print()
print("RECEIPTS IN RECEIPT STORE :", len(receipt_store))
print("RECEIPTS IN WORKBOOK      :", len(workbook_receipts))

print()
print("=" * 80)
print("MISSING FROM WORKBOOK")
print("=" * 80)

if missing_from_workbook:
    for number in missing_from_workbook:
        print(number)
else:
    print("NONE")

print()
print("=" * 80)
print("WORKBOOK RECORDS NOT IN RECEIPT STORE")
print("=" * 80)

if extra_in_workbook:
    for number in extra_in_workbook:
        print(number)
else:
    print("NONE")

print()
print("=" * 80)
print("RECEIPT SEQUENCE 1–33")
print("=" * 80)

for number in range(1, 34):

    receipt_number = (
        f"TLC/RCPT/2026/{number:06d}"
    )

    in_receipts = receipt_number in receipt_store
    in_workbook = receipt_number in workbook_receipts

    print(
        f"{receipt_number} | "
        f"RECEIPTS={'YES' if in_receipts else 'NO '} | "
        f"WORKBOOK={'YES' if in_workbook else 'NO '}"
    )
