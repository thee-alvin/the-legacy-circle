from pathlib import Path

path = Path(r".\app\financial_register\ledger_service.py")
text = path.read_text(encoding="utf-8-sig")

start_marker = "    monthly_coverage_rows = []\n"
end_marker = "    for member in members:\n"

start = text.find(start_marker)
end = text.find(end_marker, start)

if start == -1 or end == -1:
    raise SystemExit(
        "Could not locate the coverage transaction preparation block."
    )

replacement = '''    monthly_coverage_rows = []

    # Build a separate all-time register specifically for recovering
    # original payment metadata such as the recorded transaction time.
    from app.financial_register.service import (
        build_financial_register as _build_full_register_for_time
    )

    source_register_for_times = (
        _build_full_register_for_time()
        or {}
    )

    all_time_members = (
        source_register_for_times.get("members")
        or []
    )

    source_time_by_receipt = {}

    for source_member in all_time_members:

        if not isinstance(source_member, dict):
            continue

        for source_transaction in (
            source_member.get("transactions")
            or []
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

'''

text = (
    text[:start]
    + replacement
    + text[end:]
)

path.write_text(
    text,
    encoding="utf-8"
)

print("TIME LOOKUP BLOCK REBUILT SAFELY.")
