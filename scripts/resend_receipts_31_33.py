import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.receipts.receipt_pdf_generator import generate_receipt_pdf
from app.services.email_service import send_receipt_email


RECEIPTS_FILE = PROJECT_ROOT / "data" / "receipts" / "receipts.json"

TARGETS = {
    "TLC/RCPT/2026/000031",
    "TLC/RCPT/2026/000032",
    "TLC/RCPT/2026/000033",
}


def load_existing_receipts():
    with RECEIPTS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        return data.get("receipts", [])

    return data


print("=" * 80)
print("TLC EXISTING RECEIPT EMAIL RESEND")
print("=" * 80)
print()

receipts = load_existing_receipts()

selected = []

for receipt in receipts:
    receipt_number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if receipt_number in TARGETS:
        selected.append(receipt)


found = {
    str(r.get("receipt_number", "")).strip()
    for r in selected
}

missing = TARGETS - found

if missing:
    print("MISSING RECEIPTS:")
    for number in sorted(missing):
        print("   ", number)

    raise SystemExit(
        "Stopping because one or more target receipts were not found."
    )


selected.sort(
    key=lambda r: str(r.get("receipt_number", ""))
)


for receipt in selected:

    receipt_number = str(
        receipt.get("receipt_number", "")
    ).strip()

    member_name = str(
        receipt.get(
            "member_name",
            receipt.get("full_name", "")
        )
    ).strip()

    recipient_email = str(
        receipt.get("email", "")
    ).strip()

    amount = receipt.get("amount", 0)

    print("-" * 80)
    print("RECEIPT:", receipt_number)
    print("MEMBER :", member_name)
    print("EMAIL  :", recipient_email)
    print("STATUS :", receipt.get("status"))

    if not recipient_email:
        print("RESULT : SKIPPED - no email address")
        print()
        continue

    try:

        print("Generating official TLC PDF...")

        receipt_pdf = generate_receipt_pdf(receipt)

        if not receipt_pdf:
            print("RESULT : FAILED - empty PDF")
            print()
            continue

        print(
            "PDF SIZE:",
            len(receipt_pdf),
            "bytes"
        )

        print("Sending email...")

        email_sent, email_message = send_receipt_email(
            recipient_email=recipient_email,
            receipt_number=receipt_number,
            member_name=member_name,
            amount=amount,
            pdf_bytes=receipt_pdf,
        )

        if email_sent:
            print("RESULT : EMAIL SENT")
            print("MESSAGE:", email_message)
        else:
            print("RESULT : EMAIL FAILED")
            print("ERROR  :", email_message)

    except Exception as error:

        print("RESULT : EXCEPTION")
        print("ERROR  :", repr(error))

    print()


print("=" * 80)
print("RESEND PROCESS COMPLETE")
print("=" * 80)
