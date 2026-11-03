import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

from dotenv import load_dotenv
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ENV_FILE = ROOT / ".env"
load_dotenv(ENV_FILE, override=True)

# Import after loading .env so the PDF generator gets the configured URL.
from app.receipts.receipt_pdf_generator import generate_receipt_pdf
from app.services.email_service import send_receipt_email

CONTRIBUTIONS_FILE = (
    ROOT / "data" / "spreadsheets" / "02_CONTRIBUTIONS.xlsx"
)
RECEIPTS_FILE = ROOT / "data" / "receipts" / "receipts.json"
LOG_FILE = ROOT / "data" / "receipts" / "email_recovery_log.json"

# Receipts 31–33 are excluded because previous reconciliation notes
# indicate they were already emailed.
TARGET_SEQUENCES = [43, 44, 45, 46]
TARGETS = [
    f"TLC/RCPT/2026/{number:06d}"
    for number in TARGET_SEQUENCES
]

HEADERS_REQUIRED = [
    "Contribution ID",
    "Receipt Number",
    "Member ID",
    "Full Name",
    "Email",
    "Amount",
    "Status",
]


def clean(value):
    return "" if value is None else str(value).strip()


def write_log(data):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = LOG_FILE.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(LOG_FILE)


def record_attempt(log, number, result, message):
    receipt_log = log["receipts"].setdefault(
        number,
        {"attempts": []},
    )

    receipt_log["attempts"].append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "result": result,
        "message": str(message)[:1000],
    })

    write_log(log)


def was_accepted_by_smtp(log, number):
    receipt_log = log["receipts"].get(number, {})
    return any(
        attempt.get("result") == "SMTP_ACCEPTED"
        for attempt in receipt_log.get("attempts", [])
    )


def main():
    print("=" * 76)
    print("TLC — OUTSTANDING RECEIPT EMAILS")
    print("=" * 76)
    print("Target receipts:", len(TARGETS))
    print("Receipts 31–33 are excluded from this run.")

    for required_file in (CONTRIBUTIONS_FILE, RECEIPTS_FILE):
        if not required_file.is_file():
            raise RuntimeError(f"Required file missing: {required_file}")

    # Check SMTP configuration without revealing credentials.
    for key in (
        "TLC_SMTP_HOST",
        "TLC_SMTP_USERNAME",
        "TLC_SMTP_PASSWORD",
    ):
        if not os.getenv(key):
            raise RuntimeError(f"SMTP configuration is missing: {key}")

    # Require the local portal to be available before generating PDFs.
    base_url = os.getenv(
        "TLC_PORTAL_LOCAL_URL",
        "http://127.0.0.1:5000",
    ).rstrip("/")

    print("Checking the local portal:", base_url)

    with urlopen(base_url + "/", timeout=10) as response:
        if response.status >= 400:
            raise RuntimeError(
                f"Local portal returned HTTP {response.status}"
            )

    registry_data = json.loads(
        RECEIPTS_FILE.read_text(encoding="utf-8-sig")
    )

    if not isinstance(registry_data, list):
        raise RuntimeError("Unexpected receipt registry format.")

    registry = {}

    for receipt in registry_data:
        if not isinstance(receipt, dict):
            continue

        number = clean(receipt.get("receipt_number"))

        if number in registry:
            raise RuntimeError(
                f"Duplicate receipt in registry: {number}"
            )

        if number:
            registry[number] = receipt

    missing = [number for number in TARGETS if number not in registry]

    if missing:
        raise RuntimeError(
            "These target receipts are missing from the registry: "
            + ", ".join(missing)
        )

    if LOG_FILE.exists():
        log = json.loads(LOG_FILE.read_text(encoding="utf-8-sig"))

        if not isinstance(log, dict) or not isinstance(
            log.get("receipts"), dict
        ):
            raise RuntimeError(
                "Email recovery log has an unexpected format. "
                "No emails have been sent by this run."
            )
    else:
        log = {
            "purpose": "TLC recovered-receipt email attempts",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "receipts": {},
        }
        write_log(log)

    wb = load_workbook(CONTRIBUTIONS_FILE)

    sent = 0
    failed = 0
    skipped = 0

    try:
        if "Contributions" not in wb.sheetnames:
            raise RuntimeError("Contributions sheet is missing.")

        ws = wb["Contributions"]
        headers = [clean(cell.value) for cell in ws[1]]

        missing_headers = [
            header for header in HEADERS_REQUIRED
            if header not in headers
        ]

        if missing_headers:
            raise RuntimeError(
                "Contribution workbook is missing columns: "
                + ", ".join(missing_headers)
            )

        col = {
            header: headers.index(header) + 1
            for header in headers
            if header
        }

        rows_by_receipt = {}

        for row_number in range(2, ws.max_row + 1):
            number = clean(
                ws.cell(row_number, col["Receipt Number"]).value
            )

            if not number:
                continue

            if number in rows_by_receipt:
                raise RuntimeError(
                    f"Duplicate receipt in workbook: {number}"
                )

            rows_by_receipt[number] = row_number

        for number in TARGETS:
            if number not in rows_by_receipt:
                raise RuntimeError(
                    f"Receipt not found in contributions workbook: {number}"
                )

        # First reconcile any SMTP-confirmed sends recorded by an earlier run.
        for number in TARGETS:
            if not was_accepted_by_smtp(log, number):
                continue

            row_number = rows_by_receipt[number]
            status_cell = ws.cell(row_number, col["Status"])

            if clean(status_cell.value) != "RECORDED - EMAILED":
                status_cell.value = "RECORDED - EMAILED"
                wb.save(CONTRIBUTIONS_FILE)

            print(number, "| Previously accepted by SMTP; not resent.")

        for number in TARGETS:
            row_number = rows_by_receipt[number]
            row_status = clean(
                ws.cell(row_number, col["Status"]).value
            )

            if was_accepted_by_smtp(log, number):
                skipped += 1
                continue

            if row_status == "RECORDED - EMAILED":
                print(number, "| SKIPPED: already marked emailed.")
                skipped += 1
                continue

            if row_status != "RECORDED - RECOVERED":
                print(
                    number,
                    f"| SKIPPED: unexpected status {row_status!r}",
                )
                record_attempt(
                    log, number, "SKIPPED_UNEXPECTED_STATUS", row_status
                )
                skipped += 1
                continue

            receipt = registry[number]
            member_name = clean(
                receipt.get("member_name")
                or receipt.get("full_name")
            )
            recipient_email = clean(receipt.get("email"))

            workbook_email = clean(
                ws.cell(row_number, col["Email"]).value
            )
            workbook_member = clean(
                ws.cell(row_number, col["Member ID"]).value
            )
            registry_member = clean(receipt.get("member_id"))

            try:
                workbook_amount = float(
                    ws.cell(row_number, col["Amount"]).value
                )
                receipt_amount = float(receipt.get("amount"))
            except (TypeError, ValueError):
                print(number, "| FAILED: invalid payment amount.")
                record_attempt(
                    log, number, "FAILED_DATA_CHECK",
                    "Invalid or missing amount."
                )
                failed += 1
                continue

            if not recipient_email or not workbook_email:
                print(number, "| FAILED: missing email address.")
                record_attempt(
                    log, number, "FAILED_DATA_CHECK",
                    "Email address is missing."
                )
                failed += 1
                continue

            if recipient_email.lower() != workbook_email.lower():
                print(number, "| FAILED: email mismatch between sources.")
                record_attempt(
                    log, number, "FAILED_DATA_CHECK",
                    "Registry and workbook email addresses differ."
                )
                failed += 1
                continue

            if registry_member and workbook_member != registry_member:
                print(number, "| FAILED: member ID mismatch.")
                record_attempt(
                    log, number, "FAILED_DATA_CHECK",
                    "Registry and workbook member IDs differ."
                )
                failed += 1
                continue

            if abs(workbook_amount - receipt_amount) > 0.001:
                print(number, "| FAILED: amount mismatch.")
                record_attempt(
                    log, number, "FAILED_DATA_CHECK",
                    "Registry and workbook amounts differ."
                )
                failed += 1
                continue

            print("-" * 76)
            print("Receipt:", number)
            print("Member:", member_name or "(name missing)")
            print("Generating PDF...")

            try:
                pdf_bytes = generate_receipt_pdf(receipt)

                if (
                    not isinstance(pdf_bytes, bytes)
                    or not pdf_bytes.startswith(b"%PDF")
                    or len(pdf_bytes) < 1000
                ):
                    raise RuntimeError(
                        "Generated receipt PDF failed validation."
                    )

                print("PDF validation: PASS")
                print("Sending email...")

                success, message = send_receipt_email(
                    recipient_email=recipient_email,
                    receipt_number=number,
                    member_name=member_name,
                    amount=receipt_amount,
                    pdf_bytes=pdf_bytes,
                )

                if not success:
                    print("RESULT: FAILED")
                    print("Reason:", message)
                    record_attempt(log, number, "SMTP_FAILED", message)
                    failed += 1
                    continue

                # Persist send evidence before changing the workbook status.
                record_attempt(
                    log,
                    number,
                    "SMTP_ACCEPTED",
                    message or "SMTP accepted the message.",
                )

                # Use the same success status used by TLC's processor.
                ws.cell(
                    row_number,
                    col["Status"],
                ).value = "RECORDED - EMAILED"

                wb.save(CONTRIBUTIONS_FILE)

                print("RESULT: SMTP ACCEPTED")
                print("Workbook status updated.")
                sent += 1

                # Reduce the chance of hitting the provider's sending limit.
                time.sleep(1.5)

            except Exception as exc:
                print("RESULT: FAILED")
                print("Reason:", repr(exc))

                # Do not overwrite existing SMTP_ACCEPTED evidence.
                if not was_accepted_by_smtp(log, number):
                    record_attempt(
                        log,
                        number,
                        "PDF_OR_SENDING_EXCEPTION",
                        repr(exc),
                    )

                failed += 1

    finally:
        wb.close()

    print()
    print("=" * 76)
    print("EMAIL RUN FINISHED")
    print("=" * 76)
    print("SMTP-accepted emails during this run:", sent)
    print("Failed attempts:", failed)
    print("Skipped receipts:", skipped)
    print("Attempt log:", LOG_FILE)
    print()
    print(
        "SMTP acceptance does not prove that the recipient's inbox "
        "received or displayed the email."
    )


if __name__ == "__main__":
    main()
