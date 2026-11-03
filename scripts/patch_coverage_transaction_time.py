from pathlib import Path

path = Path(r".\app\financial_register\ledger_service.py")
text = path.read_text(encoding="utf-8-sig")

if "source_time_by_receipt" not in text:

    anchor = '''    monthly_coverage_rows = []

    for member in members:
'''

    insertion = '''    monthly_coverage_rows = []

    # Original recorded time for each source payment/receipt.
    # Coverage rows inherit this time so the register never shows
    # a blank dash for a payment that has a recorded timestamp.
    source_time_by_receipt = {}

    for source_member in all_time_members:

        if not isinstance(source_member, dict):
            continue

        for source_transaction in (
            source_member.get("transactions") or []
        ):

            if not isinstance(source_transaction, dict):
                continue

            receipt_key = (
                source_transaction.get("receipt_number")
                or source_transaction.get("receipt_reference")
                or source_transaction.get("Receipt Number")
                or ""
            )

            source_time = (
                source_transaction.get("time")
                or source_transaction.get("payment_time")
                or source_transaction.get("received_time")
                or ""
            )

            if receipt_key and source_time:
                source_time_by_receipt[
                    str(receipt_key).strip().upper()
                ] = str(source_time).strip()

    for member in members:
'''

    if anchor not in text:
        raise SystemExit(
            "Coverage member-loop anchor not found."
        )

    text = text.replace(
        anchor,
        insertion,
        1
    )

# Replace the blank coverage-row time.
old = '''                "time": "",

                "payment_type": "Weekly Contribution",
'''

new = '''                "time": source_time_by_receipt.get(
                    str(receipt_number).strip().upper(),
                    ""
                ),

                "payment_type": "Weekly Contribution",
'''

if old not in text:
    raise SystemExit(
        "Coverage transaction time field not found."
    )

text = text.replace(
    old,
    new,
    1
)

path.write_text(
    text,
    encoding="utf-8"
)

print("COVERAGE TRANSACTION TIME PATCH INSTALLED.")
