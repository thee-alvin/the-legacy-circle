import json
from copy import copy
from datetime import datetime, date, time
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.cell import get_column_letter, range_boundaries


ROOT = Path(__file__).resolve().parents[1]

SOURCE = (
    ROOT / "data" / "backups" / "recovery"
    / "02_CONTRIBUTIONS_before_receipt_reconciliation_20261001_213639.xlsx"
)

RECEIPTS_FILE = ROOT / "data" / "receipts" / "receipts.json"

COVERAGE_FILE = (
    ROOT / "data" / "spreadsheets"
    / "03_CONTRIBUTION_COVERAGE.xlsx"
)

OUTPUT_DIR = ROOT / "data" / "backups" / "recovery"

HEADERS_REQUIRED = [
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


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_datetime(value):
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    text = str(value).strip()

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text


def parse_time(value):
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value.time()

    if isinstance(value, time):
        return value

    text = str(value).strip()

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            pass

    return text


def load_coverage_mappings():
    if not COVERAGE_FILE.is_file():
        raise RuntimeError(
            f"Coverage workbook not found: {COVERAGE_FILE}"
        )

    wb = load_workbook(
        COVERAGE_FILE,
        read_only=True,
        data_only=True,
    )

    try:
        if "Coverage Ledger" not in wb.sheetnames:
            raise RuntimeError(
                "The Coverage Ledger sheet is missing."
            )

        ws = wb["Coverage Ledger"]
        headers = [
            clean(cell.value)
            for cell in ws[1]
        ]

        if (
            "Receipt Number" not in headers
            or "Contribution ID" not in headers
        ):
            raise RuntimeError(
                "Required mapping columns are missing from Coverage Ledger."
            )

        receipt_col = headers.index("Receipt Number")
        contribution_col = headers.index("Contribution ID")

        mappings = {}

        for row in ws.iter_rows(min_row=2, values_only=True):
            receipt = clean(
                row[receipt_col]
                if receipt_col < len(row)
                else None
            )
            contribution_id = clean(
                row[contribution_col]
                if contribution_col < len(row)
                else None
            )

            if not receipt or not contribution_id:
                continue

            previous = mappings.get(receipt)

            if previous and previous != contribution_id:
                raise RuntimeError(
                    "Conflicting coverage mappings for "
                    f"{receipt}: {previous} and {contribution_id}"
                )

            mappings[receipt] = contribution_id

        return mappings

    finally:
        wb.close()


def main():
    print("=" * 76)
    print("TLC CONTRIBUTIONS — RECOVERY DRAFT")
    print("=" * 76)

    # This script must never write to the damaged live workbook.
    live_workbook = (
        ROOT / "data" / "spreadsheets" / "02_CONTRIBUTIONS.xlsx"
    )

    if not SOURCE.is_file():
        raise RuntimeError(
            f"Validated source backup is missing: {SOURCE}"
        )

    if not RECEIPTS_FILE.is_file():
        raise RuntimeError(
            f"Receipt registry is missing: {RECEIPTS_FILE}"
        )

    if not live_workbook.is_file():
        raise RuntimeError(
            f"Live workbook path is missing: {live_workbook}"
        )

    # Read the receipt registry without modifying it.
    receipts_data = json.loads(
        RECEIPTS_FILE.read_text(encoding="utf-8-sig")
    )

    if not isinstance(receipts_data, list):
        raise RuntimeError(
            "The receipt registry is not a JSON list."
        )

    receipt_by_number = {}

    for receipt in receipts_data:
        if not isinstance(receipt, dict):
            continue

        number = clean(receipt.get("receipt_number"))

        if not number:
            continue

        if number in receipt_by_number:
            raise RuntimeError(
                f"Duplicate receipt number in registry: {number}"
            )

        receipt_by_number[number] = receipt

    coverage_by_receipt = load_coverage_mappings()

    # Confirm that every receipt we intend to recover exists.
    target_receipts = []

    for sequence in range(26, 47):
        number = f"TLC/RCPT/2026/{sequence:06d}"
        receipt = receipt_by_number.get(number)

        if receipt is None:
            raise RuntimeError(
                f"Required receipt is missing from registry: {number}. "
                "No recovery workbook has been created."
            )

        target_receipts.append((sequence, number, receipt))

    # Open only the known-good backup.
    wb = load_workbook(SOURCE)
    
    try:
        if "Contributions" not in wb.sheetnames:
            raise RuntimeError(
                "The source backup has no Contributions sheet."
            )

        ws = wb["Contributions"]

        headers = [
            clean(cell.value)
            for cell in ws[1]
        ]

        missing_headers = [
            header
            for header in HEADERS_REQUIRED
            if header not in headers
        ]

        if missing_headers:
            raise RuntimeError(
                "Source backup is missing columns: "
                + ", ".join(missing_headers)
            )

        column_map = {
            header: index + 1
            for index, header in enumerate(headers)
        }

        receipt_col = column_map["Receipt Number"]
        id_col = column_map["Contribution ID"]

        existing_receipts = {}
        existing_ids = {}

        for row_number in range(2, ws.max_row + 1):
            receipt_number = clean(
                ws.cell(row_number, receipt_col).value
            )
            contribution_id = clean(
                ws.cell(row_number, id_col).value
            )

            if receipt_number:
                if receipt_number in existing_receipts:
                    raise RuntimeError(
                        "Duplicate receipt in source backup: "
                        f"{receipt_number}"
                    )

                existing_receipts[receipt_number] = row_number

            if contribution_id:
                if contribution_id in existing_ids:
                    raise RuntimeError(
                        "Duplicate contribution ID in source backup: "
                        f"{contribution_id}"
                    )

                existing_ids[contribution_id] = receipt_number

        print(f"Source backup rows: {len(existing_receipts)}")
        print(f"Registry receipts: {len(receipt_by_number)}")
        print(f"Coverage mappings inspected: {len(coverage_by_receipt)}")
        print(f"Receipts selected for recovery: {len(target_receipts)}")

        # Preserve the source workbook's row formatting.
        style_source_row = ws.max_row if ws.max_row >= 2 else 1

        added = []
        missing_contact = []
        inferred_ids = []

        for sequence, receipt_number, receipt in target_receipts:

            # Do not create duplicate rows if a source backup changes.
            if receipt_number in existing_receipts:
                print(f"Already present; skipped: {receipt_number}")
                continue

            registry_id = clean(receipt.get("contribution_id"))
            coverage_id = clean(
                coverage_by_receipt.get(receipt_number)
            )

            if (
                registry_id
                and coverage_id
                and registry_id != coverage_id
            ):
                raise RuntimeError(
                    f"Contribution ID conflict for {receipt_number}: "
                    f"registry={registry_id}, coverage={coverage_id}"
                )

            # Prefer an existing explicit mapping.
            contribution_id = (
                registry_id
                or coverage_id
                or f"TLC-CON-{sequence:06d}"
            )

            if not registry_id and not coverage_id:
                inferred_ids.append(
                    (receipt_number, contribution_id)
                )

            owner = existing_ids.get(contribution_id)

            if owner and owner != receipt_number:
                raise RuntimeError(
                    f"Contribution ID {contribution_id} is already "
                    f"assigned to {owner}, not {receipt_number}."
                )

            member_name = clean(
                receipt.get("full_name")
                or receipt.get("member_name")
            )

            phone = clean(
                receipt.get("phone_number")
                or receipt.get("phone")
            )

            email = clean(receipt.get("email"))

            if not phone or not email:
                missing_contact.append(
                    (receipt_number, not phone, not email)
                )

            amount = receipt.get("amount")

            if amount is None or amount == "":
                raise RuntimeError(
                    f"Amount is missing for {receipt_number}."
                )

            try:
                amount = float(amount)
            except (TypeError, ValueError):
                raise RuntimeError(
                    f"Amount is not numeric for {receipt_number}: "
                    f"{amount!r}"
                )

            values = {
                "Contribution ID": contribution_id,
                "Receipt Number": receipt_number,
                "Member ID": clean(receipt.get("member_id")),
                "Full Name": member_name,
                "Phone Number": phone,
                "Email": email,
                "Payment Date": parse_datetime(
                    receipt.get("payment_date")
                ),
                "Payment Time": parse_time(
                    receipt.get("payment_time")
                ),
                "Payment Type": clean(
                    receipt.get("payment_type")
                ),
                "Description": clean(
                    receipt.get("description")
                ),
                "Amount": amount,
                "Payment Method": clean(
                    receipt.get("payment_method")
                ),
                "Transaction Reference": clean(
                    receipt.get("transaction_reference")
                    or receipt.get("payment_reference")
                ),
                # Receipt issuance does not prove email delivery.
                "Status": "RECORDED - RECOVERED",
                "Recorded By": clean(
                    receipt.get("recorded_by")
                ),
                "Created At": parse_datetime(
                    receipt.get("created_at")
                ),
            }

            # Copy the existing final data row's cell formatting.
            next_row = ws.max_row + 1

            for col_num in range(1, ws.max_column + 1):
                source_cell = ws.cell(
                    style_source_row,
                    col_num,
                )
                target_cell = ws.cell(
                    next_row,
                    col_num,
                )

                if source_cell.has_style:
                    target_cell._style = copy(source_cell._style)

                if source_cell.number_format:
                    target_cell.number_format = (
                        source_cell.number_format
                    )

                if source_cell.alignment:
                    target_cell.alignment = copy(
                        source_cell.alignment
                    )

                if source_cell.protection:
                    target_cell.protection = copy(
                        source_cell.protection
                    )

            for header, value in values.items():
                ws.cell(
                    next_row,
                    column_map[header],
                    value,
                )

            existing_receipts[receipt_number] = next_row
            existing_ids[contribution_id] = receipt_number
            added.append(receipt_number)

        # Extend any existing Excel tables to include new rows.
        for table in ws.tables.values():
            min_col, min_row, max_col, max_row = range_boundaries(
                table.ref
            )

            if min_row == 1:
                table.ref = (
                    f"{get_column_letter(min_col)}{min_row}:"
                    f"{get_column_letter(max_col)}{max(max_row, ws.max_row)}"
                )

        # Extend an existing filter, without adding one if absent.
        if ws.auto_filter.ref:
            min_col, min_row, max_col, max_row = range_boundaries(
                ws.auto_filter.ref
            )

            ws.auto_filter.ref = (
                f"{get_column_letter(min_col)}{min_row}:"
                f"{get_column_letter(max_col)}{max(max_row, ws.max_row)}"
            )

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = (
            OUTPUT_DIR
            / f"02_CONTRIBUTIONS_RECOVERY_DRAFT_{stamp}.xlsx"
        )

        counter = 1
        while output.exists():
            output = (
                OUTPUT_DIR
                / f"02_CONTRIBUTIONS_RECOVERY_DRAFT_{stamp}_{counter}.xlsx"
            )
            counter += 1

        # Save only to the new draft path, never to the live workbook.
        wb.save(output)

    finally:
        wb.close()

    # Re-open and validate the generated draft.
    check_wb = load_workbook(output, read_only=True, data_only=True)

    try:
        check_ws = check_wb["Contributions"]
        check_headers = [
            clean(cell.value)
            for cell in check_ws[1]
        ]

        check_receipt_col = check_headers.index("Receipt Number")
        check_id_col = check_headers.index("Contribution ID")

        final_receipts = []
        final_ids = []

        for row in check_ws.iter_rows(min_row=2, values_only=True):
            number = clean(
                row[check_receipt_col]
                if check_receipt_col < len(row)
                else None
            )
            contribution_id = clean(
                row[check_id_col]
                if check_id_col < len(row)
                else None
            )

            if number:
                final_receipts.append(number)

            if contribution_id:
                final_ids.append(contribution_id)

        if len(final_receipts) != len(set(final_receipts)):
            raise RuntimeError(
                "Validation failed: duplicate receipts in the draft."
            )

        if len(final_ids) != len(set(final_ids)):
            raise RuntimeError(
                "Validation failed: duplicate contribution IDs in the draft."
            )

        missing_after_save = [
            number
            for _, number, _ in target_receipts
            if number not in set(final_receipts)
        ]

        if missing_after_save:
            raise RuntimeError(
                "Validation failed; receipts missing after save: "
                + ", ".join(missing_after_save)
            )

        print()
        print("=" * 76)
        print("DRAFT CREATED AND REOPENED SUCCESSFULLY")
        print("=" * 76)
        print("Output:", output)
        print("Total data rows:", len(final_receipts))
        print("Unique receipt numbers:", len(set(final_receipts)))
        print("Unique contribution IDs:", len(set(final_ids)))
        print("New rows added:", len(added))
        print("Live workbook changed: NO")
        print("Receipt registry changed: NO")
        print("Coverage ledger changed: NO")
        print("Email delivery statuses verified by this script: NO")

        if inferred_ids:
            print()
            print("IDs assigned using the established sequence convention:")
            for number, contribution_id in inferred_ids:
                print(f"  {number} -> {contribution_id}")

        if missing_contact:
            print()
            print("Rows with missing contact information:")
            for number, no_phone, no_email in missing_contact:
                absent = []
                if no_phone:
                    absent.append("phone")
                if no_email:
                    absent.append("email")
                print(f"  {number}: missing {', '.join(absent)}")

        print()
        print("Recovered receipt numbers:")
        for number in added:
            print(" ", number)

        print()
        print("No live financial workbook has been replaced.")

    finally:
        check_wb.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print()
        print("RECOVERY DRAFT NOT COMPLETED:", repr(exc))
        raise
