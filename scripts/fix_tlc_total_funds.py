from pathlib import Path

path = Path(r".\app\financial_register\ledger_service.py")
text = path.read_text(encoding="utf-8-sig")

old = '''        all_time_register = _build_financial_ledger_cash()

        all_time_summary = (
            all_time_register.get("summary")
            or {}
        )

        overall_total_funds = float(
            all_time_summary.get("total_funds") or 0
        )

        overall_total_money_in = float(
            all_time_summary.get("total_money_in") or 0
        )

        overall_total_money_out = float(
            all_time_summary.get("total_money_out") or 0
        )

        overall_current_balance = float(
            all_time_summary.get("current_balance")
            or overall_total_money_in - overall_total_money_out
        )
'''

new = '''        # IMPORTANT:
        # The monthly ledger is intentionally coverage-based, so its
        # cash totals are period-specific. Overall TLC funds must come
        # from the complete financial register, not the October filter.

        from app.financial_register.service import (
            build_financial_register
        )

        all_time_register = build_financial_register()

        all_time_summary = (
            all_time_register.get("summary")
            or {}
        )

        overall_total_funds = float(
            all_time_summary.get("total_funds") or 0
        )

        # The financial register is the authoritative all-time money
        # position currently exposed by TLC.
        overall_total_money_in = float(
            all_time_summary.get("total_funds") or 0
        )

        overall_total_money_out = float(
            all_time_summary.get("total_money_out") or 0
        )

        overall_current_balance = float(
            all_time_summary.get("current_balance")
            or overall_total_funds - overall_total_money_out
        )
'''

if old not in text:
    raise SystemExit(
        "Overall funds block was not found. No file changed."
    )

text = text.replace(old, new, 1)

path.write_text(
    text,
    encoding="utf-8"
)

print("OVERALL TLC FUNDS SOURCE FIXED.")
