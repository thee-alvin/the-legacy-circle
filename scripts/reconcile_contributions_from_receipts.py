import json
import shutil
from pathlib import Path
from datetime import datetime

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]

WORKBOOK = ROOT / "data" / "spreadsheets" / "02_CONTRIBUTIONS.xlsx"
RECEIPTS_FILE = ROOT / "data" / "receipts" / "receipts.json"

BACKUP = (
    ROOT
    / "data"
    / "backups"
    / "recovery"
    / f"02_CONTRIBUTIONS_before_receipt_reconciliation_"
      f"{datetime.now():%Y%m%d_%H%M%S}.xlsx"
)

TARGET_MIN = 26
TARGET_MAX = 33


EXPECTED_HEADERS = [
    "Contribution ID",
    "Receipt Number",
    "Member ID",
    "Full Name",
    "Phone Number",
    "Email",
    "Payment Date",
    "Payment Time",
    "Payment Type",
    "Description",
    "Amount",
    "Payment Method",
    "Transaction Reference",
    "Status",
    "Recorded By",
    "Created At",
]


print("=" * 80)
print("TLC CONTRIBUTION WORKBOOK RECONCILIATION")
print("=" * 80)


# ------------------------------------------------------------
# SAFETY BACKUP
# ------------------------------------------------------------

if not WORKBOOK.exists():
    raise SystemExit(
        f"Workbook not found: {WORKBOOK}"
    )

BACKUP.parent.mkdir(
    parents=True,
    exist_ok=True
)

shutil.copy2(
    WORKBOOK,
    BACKUP
)

print()
print("BACKUP CREATED:")
print(BACKUP)


# ------------------------------------------------------------
# LOAD WORKBOOK
# ------------------------------------------------------------

wb = load_workbook(
    WORKBOOK,
    read_only=False,
    data_only=False
)

ws = wb["Contributions"]

headers = [
    cell.value
    for cell in ws[1]
]

print()
print("WORKBOOK SHEET:", ws.title)
print("WORKBOOK ROWS BEFORE:", ws.max_row)


missing_headers = [
    h for h in EXPECTED_HEADERS
    if h not in headers
]

if missing_headers:
    wb.close()
    raise SystemExit(
        "Missing workbook headers: "
        + ", ".join(missing_headers)
    )


column_map = {
    header: index + 1
    for index, header in enumerate(headers)
}


# ------------------------------------------------------------
# INDEX CURRENT WORKBOOK RECEIPTS
# ------------------------------------------------------------

existing_receipts = set()

for row in ws.iter_rows(
    min_row=2,
    values_only=True
):
    receipt_col = column_map["Receipt Number"] - 1

    if receipt_col >= len(row):
        continue

    value = row[receipt_col]

    if value:
        existing_receipts.add(
            str(value).strip()
        )


# ------------------------------------------------------------
# LOAD AUTHORITATIVE RECEIPTS
# ------------------------------------------------------------

if not RECEIPTS_FILE.exists():
    wb.close()

    raise SystemExit(
        f"Receipt store not found: {RECEIPTS_FILE}"
    )


with RECEIPTS_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)


if isinstance(data, dict):
    receipts = data.get("receipts", [])
else:
    receipts = data


# ------------------------------------------------------------
# SELECT RECEIPTS 26–33
# ------------------------------------------------------------

target_receipts = []

for receipt in receipts:

    receipt_number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if not receipt_number:
        continue

    try:
        sequence = int(
            receipt_number.split("/")[-1]
        )
    except (ValueError, IndexError):
        continue

    if TARGET_MIN <= sequence <= TARGET_MAX:
        target_receipts.append(receipt)


target_receipts.sort(
    key=lambda item: int(
        str(
            item.get("receipt_number", "")
        ).split("/")[-1]
    )
)


print()
print(
    "RECEIPT STORE RECORDS 26–33:",
    len(target_receipts)
)


# ------------------------------------------------------------
# APPEND ONLY MISSING RECORDS
# ------------------------------------------------------------

added = []
already_present = []


for receipt in target_receipts:

    receipt_number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if receipt_number in existing_receipts:

        already_present.append(
            receipt_number
        )

        continue


    sequence = int(
        receipt_number.split("/")[-1]
    )


    contribution_id = str(
        receipt.get(
            "contribution_id",
            f"TLC-CON-{sequence:06d}"
        )
    ).strip()


    member_id = str(
        receipt.get("member_id", "")
    ).strip()


    member_name = str(
        receipt.get(
            "full_name",
            receipt.get("member_name", "")
        )
    ).strip()


    phone_number = str(
        receipt.get("phone_number", "")
    ).strip()


    email = str(
        receipt.get("email", "")
    ).strip()


    payment_type = str(
        receipt.get("payment_type", "")
    ).strip()


    description = str(
        receipt.get("description", "")
    ).strip()


    amount = receipt.get(
        "amount",
        0
    )


    payment_method = str(
        receipt.get(
            "payment_method",
            "MPESA TILL"
        )
    ).strip()


    transaction_reference = str(
        receipt.get(
            "transaction_reference",
            receipt.get(
                "payment_reference",
                ""
            )
        )
    ).strip()


    payment_date = receipt.get(
        "payment_date"
    )


    payment_time = receipt.get(
        "payment_time"
    )


    recorded_by = str(
        receipt.get(
            "recorded_by",
            ""
        )
    ).strip()


    created_at = receipt.get(
        "created_at",
        ""
    )


    # Existing receipt records represent issued receipts.
    # For receipts 31–33, which we have just successfully
    # emailed, record them explicitly as emailed.
    if sequence >= 31:
        status = "RECORDED - EMAILED"
    else:
        status = "RECORDED - RECOVERED"


    row_values = {
        "Contribution ID": contribution_id,
        "Receipt Number": receipt_number,
        "Member ID": member_id,
        "Full Name": member_name,
        "Phone Number": phone_number,
        "Email": email,
        "Payment Date": payment_date,
        "Payment Time": payment_time,
        "Payment Type": payment_type,
        "Description": description,
        "Amount": amount,
        "Payment Method": payment_method,
        "Transaction Reference": transaction_reference,
        "Status": status,
        "Recorded By": recorded_by,
        "Created At": created_at,
    }


    next_row = ws.max_row + 1

    for header, value in row_values.items():

        column = column_map[header]

        ws.cell(
            row=next_row,
            column=column,
            value=value
        )


    existing_receipts.add(
        receipt_number
    )

    added.append(
        receipt_number
    )


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

wb.save(WORKBOOK)
wb.close()


print()
print("=" * 80)
print("RECONCILIATION RESULT")
print("=" * 80)

print()
print("ADDED:")
for receipt_number in added:
    print("  ", receipt_number)

print()
print("ALREADY PRESENT:")
for receipt_number in already_present:
    print("  ", receipt_number)

print()
print(
    "WORKBOOK RECONCILIATION COMPLETE."
)

print(
    "BACKUP:",
    BACKUP
)
