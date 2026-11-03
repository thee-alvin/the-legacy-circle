from pathlib import Path
from datetime import datetime
import ast
import re

path = Path(r".\app\financial_register\ledger_service.py")

text = path.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_name(
    f"{path.name}.bak_before_coverage_reporting_{stamp}"
)

backup.write_text(text, encoding="utf-8")

print(f"Backup: {backup}")

# ------------------------------------------------------------
# DO NOT PATCH TWICE
# ------------------------------------------------------------

if "_build_financial_ledger_cash" in text:
    print("Coverage reporting wrapper already installed.")
    raise SystemExit(0)

# ------------------------------------------------------------
# FIND ORIGINAL FUNCTION
# ------------------------------------------------------------

tree = ast.parse(text)

function_node = None

for node in tree.body:
    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "build_financial_ledger"
    ):
        function_node = node
        break

if function_node is None:
    raise SystemExit(
        "Could not locate build_financial_ledger()."
    )

lines = text.splitlines(keepends=True)

definition_line = function_node.lineno - 1

old_line = lines[definition_line]

new_line = old_line.replace(
    "def build_financial_ledger(",
    "def _build_financial_ledger_cash(",
    1
)

if old_line == new_line:
    raise SystemExit(
        "Could not rename the original build_financial_ledger()."
    )

lines[definition_line] = new_line

text = "".join(lines)

# ------------------------------------------------------------
# WRAPPER
#
# Weekly contributions are reported by COVERAGE MONTH.
# Cash received remains separately available in
# summary.cash_received_in_month / total_money_in.
# ------------------------------------------------------------

wrapper = r'''

# ============================================================
# MONTHLY CONTRIBUTION COVERAGE REPORTING
#
# The underlying cash ledger remains unchanged.
#
# For a selected month:
#
#   contribution = weeks covered during that month
#
# rather than:
#
#   contribution = payment transaction date only
#
# Example:
#
#   10 Sep 2026 → KSh 1,000 → 10 weeks
#
# October:
#
#   Weeks 4–8 → KSh 500 contribution coverage
#
# The original cash payment remains dated 10 Sep.
# ============================================================

def build_financial_ledger(year=None, month=None):

    report = _build_financial_ledger_cash(
        year=year,
        month=month
    )

    # Full register requests keep the original behaviour.
    if year is None or month is None:
        return report

    try:
        selected_year = int(year)
        selected_month = int(month)
    except (TypeError, ValueError):
        return report

    try:
        from app.financial_register.contribution_coverage.service import (
            get_member_monthly_coverage
        )
    except Exception as error:
        print(
            "[FINANCIAL REGISTER COVERAGE IMPORT ERROR]",
            repr(error),
            flush=True
        )
        return report

    summary = report.setdefault(
        "summary",
        {}
    )

    members = report.get("members") or []

    old_cash_weekly = float(
        summary.get("weekly_contributions") or 0
    )

    old_cash_total = float(
        summary.get("total_contributions") or 0
    )

    total_coverage_amount = 0.0
    total_coverage_weeks = 0
    total_coverage_transactions = 0

    members_with_transactions = 0
    total_transactions = 0

    monthly_coverage_rows = []

    for member in members:

        if not isinstance(member, dict):
            continue

        member_id = (
            member.get("member_id")
            or member.get("Member ID")
            or member.get("memberId")
            or member.get("id")
        )

        if not member_id:
            continue

        try:
            coverage = get_member_monthly_coverage(
                str(member_id).strip().upper(),
                selected_year,
                selected_month
            )
        except Exception as error:
            print(
                "[FINANCIAL REGISTER COVERAGE ERROR]",
                str(member_id),
                repr(error),
                flush=True
            )
            continue

        if not isinstance(coverage, dict):
            continue

        weeks = coverage.get("weeks") or []

        if not weeks:
            # Keep non-coverage transactions such as registration fees
            # or fines already supplied by the cash ledger.
            existing = member.get("transactions")

            if isinstance(existing, list) and existing:
                member["transaction_count"] = len(existing)
                total_transactions += len(existing)

            continue

        coverage_transactions = []

        for week in weeks:

            try:
                amount = float(
                    week.get("Allocated Amount") or 0
                )
            except (TypeError, ValueError):
                amount = 0.0

            coverage_week = week.get(
                "Coverage Week #"
            )

            week_start = week.get(
                "Coverage Week Start"
            ) or ""

            week_end = week.get(
                "Coverage Week End"
            ) or ""

            payment_date = week.get(
                "Payment Date"
            ) or ""

            receipt_number = week.get(
                "Receipt Number"
            ) or ""

            contribution_id = week.get(
                "Contribution ID"
            ) or ""

            coverage_id = week.get(
                "Coverage ID"
            ) or ""

            transaction = {
                # IMPORTANT:
                # The displayed transaction date is the coverage
                # week start, so October coverage appears under October.
                "date": week_start,

                "time": "",

                "payment_type": "Weekly Contribution",

                "description": (
                    f"Contribution Coverage — "
                    f"Week {coverage_week}"
                    f" ({week_start} to {week_end})"
                ),

                "method": "Contribution Coverage",

                "amount": round(amount, 2),

                "receipt_number": receipt_number,

                "receipt_reference": receipt_number,

                "contribution_id": contribution_id,

                "coverage_id": coverage_id,

                "coverage_week": coverage_week,

                "coverage_week_start": week_start,

                "coverage_week_end": week_end,

                # This is the REAL cash payment date.
                "payment_date": payment_date,

                "source_payment_amount": (
                    week.get("Source Payment Amount") or 0
                ),

                "allocation_status": (
                    week.get("Allocation Status")
                    or "COVERED"
                ),

                "coverage_transaction": True,
            }

            coverage_transactions.append(
                transaction
            )

            monthly_coverage_rows.append({
                "member_id": str(member_id),
                "member_name": (
                    member.get("full_name")
                    or member.get("name")
                    or member.get("Full Name")
                    or week.get("Full Name")
                    or ""
                ),
                **week,
            })

            total_coverage_amount += amount
            total_coverage_weeks += 1
            total_coverage_transactions += 1

        # --------------------------------------------------------
        # Preserve fee/fine/other cash transactions.
        # Replace weekly-contribution cash rows with the coverage
        # rows for this selected month so they are not double-counted.
        # --------------------------------------------------------

        existing_transactions = member.get(
            "transactions"
        )

        if not isinstance(existing_transactions, list):
            existing_transactions = []

        non_weekly_transactions = []

        for transaction in existing_transactions:

            if not isinstance(transaction, dict):
                continue

            searchable = " ".join(
                str(
                    transaction.get(key) or ""
                )
                for key in (
                    "payment_type",
                    "transaction_type",
                    "description",
                    "type",
                )
            ).lower()

            if (
                "weekly contribution"
                in searchable
                or "weekly contribution" in searchable.replace("-", " ")
            ):
                continue

            non_weekly_transactions.append(
                transaction
            )

        member["transactions"] = (
            non_weekly_transactions
            + coverage_transactions
        )

        member["transaction_count"] = len(
            member["transactions"]
        )

        member["weekly_contributions"] = round(
            sum(
                float(
                    row.get("Allocated Amount") or 0
                )
                for row in weeks
            ),
            2
        )

        total_transactions += member[
            "transaction_count"
        ]

        if member["transaction_count"] > 0:
            members_with_transactions += 1

    # ------------------------------------------------------------
    # MONTHLY REPORT SUMMARY
    # ------------------------------------------------------------

    registration_fees = float(
        summary.get("registration_fees") or 0
    )

    fines = float(
        summary.get("fines") or 0
    )

    # Weekly contributions are now credited according to the
    # coverage weeks belonging to the requested month.
    summary["weekly_contributions"] = round(
        total_coverage_amount,
        2
    )

    summary["total_contributions"] = round(
        registration_fees
        + total_coverage_amount,
        2
    )

    summary["transactions"] = (
        total_transactions
    )

    summary["members_with_transactions"] = (
        members_with_transactions
    )

    # Coverage-specific fields are explicit so the distinction
    # between contribution coverage and actual cash is preserved.
    summary["coverage_total"] = round(
        total_coverage_amount,
        2
    )

    summary["coverage_week_count"] = (
        total_coverage_weeks
    )

    summary["coverage_transactions"] = (
        total_coverage_transactions
    )

    summary["cash_received_in_month"] = round(
        float(
            summary.get("total_money_in") or 0
        ),
        2
    )

    summary["cash_weekly_contributions_in_month"] = round(
        old_cash_weekly,
        2
    )

    # A clear reporting basis for the UI/export layer.
    report["report_basis"] = (
        "Contribution coverage month"
    )

    report["coverage"] = {
        "year": selected_year,
        "month": selected_month,
        "month_label": (
            f"{selected_year}-{selected_month:02d}"
        ),
        "total": round(
            total_coverage_amount,
            2
        ),
        "week_count": total_coverage_weeks,
        "transaction_count": total_coverage_transactions,
        "rows": monthly_coverage_rows,
    }

    return report

'''

text += wrapper

path.write_text(
    text,
    encoding="utf-8"
)

print("")
print("FINANCIAL REGISTER COVERAGE REPORTING INSTALLED.")
print("")
