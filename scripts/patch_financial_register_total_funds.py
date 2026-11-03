from pathlib import Path

path = Path(r".\app\financial_register\ledger_service.py")
text = path.read_text(encoding="utf-8-sig")

marker = '''    summary["cash_weekly_contributions_in_month"] = round(
        old_cash_weekly,
        2
    )
'''

if marker not in text:
    raise SystemExit(
        "Could not find the Financial Register summary insertion point."
    )

if 'summary["all_time_total_funds"]' in text:
    print("Total TLC Funds patch is already installed.")
    raise SystemExit(0)

patch = '''

    # ------------------------------------------------------------
    # TLC OVERALL FUND POSITION
    #
    # Monthly filtering must NOT make the group's total funds
    # appear as zero merely because the selected month had no
    # new cash received.
    #
    # Example:
    # October contribution coverage = KSh 500
    # October new cash received    = KSh 0
    # TLC total funds              = overall current TLC funds
    # ------------------------------------------------------------

    try:
        all_time_register = _build_financial_ledger_cash()

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

        # Preserve the overall TLC figures.
        summary["total_funds"] = round(
            overall_total_funds,
            2
        )

        summary["total_money_in"] = round(
            overall_total_money_in,
            2
        )

        summary["total_money_out"] = round(
            overall_total_money_out,
            2
        )

        summary["current_balance"] = round(
            overall_current_balance,
            2
        )

        # Explicit aliases for future UI/report/export use.
        summary["all_time_total_funds"] = round(
            overall_total_funds,
            2
        )

        summary["all_time_total_money_in"] = round(
            overall_total_money_in,
            2
        )

        summary["all_time_total_money_out"] = round(
            overall_total_money_out,
            2
        )

        summary["all_time_current_balance"] = round(
            overall_current_balance,
            2
        )

    except Exception as error:
        print(
            "[FINANCIAL REGISTER OVERALL FUNDS ERROR]",
            repr(error),
            flush=True
        )
'''

text = text.replace(
    marker,
    marker + patch,
    1
)

path.write_text(
    text,
    encoding="utf-8"
)

print("TOTAL TLC FUNDS PATCH INSTALLED.")
