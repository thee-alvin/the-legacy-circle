
from calendar import monthrange
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from openpyxl import load_workbook

from app.auth.session import get_current_member_id
from app.financial_register.contribution_coverage.service import (
    build_coverage_ledger,
)
from app.financial_register.contribution_coverage.workbook import (
    COVERAGE_FILE,
)

contribution_calendar_bp = Blueprint(
    "contribution_calendar", __name__
)

MEMBERS_FILE = COVERAGE_FILE.parent / "01_MEMBERS.xlsx"

WEEKDAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


def _date_value(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).date()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(text[:10])
        except (ValueError, TypeError):
            return None


def _read_member(member_id):
    if not MEMBERS_FILE.is_file():
        raise FileNotFoundError("The member workbook is unavailable.")

    workbook = load_workbook(
        MEMBERS_FILE, read_only=True, data_only=True
    )

    try:
        if "Members" not in workbook.sheetnames:
            raise ValueError("The Members worksheet is missing.")

        sheet = workbook["Members"]
        iterator = sheet.iter_rows(values_only=True)
        headers = next(iterator, None)

        if not headers:
            return None

        columns = {
            str(value).strip(): index
            for index, value in enumerate(headers)
            if value is not None and str(value).strip()
        }

        required = {"Member ID", "Full Name", "Registration Date"}
        if not required.issubset(columns):
            raise ValueError("Required member workbook columns are missing.")

        for row in iterator:
            row_id = str(
                row[columns["Member ID"]] or ""
            ).strip().upper()

            if row_id == member_id:
                return {
                    "member_id": row_id,
                    "name": str(
                        row[columns["Full Name"]] or ""
                    ).strip(),
                    "registration_date": _date_value(
                        row[columns["Registration Date"]]
                    ),
                }

        return None
    finally:
        workbook.close()


def _first_group_week(rows):
    starts = []
    week_one = []

    for row in rows:
        start = _date_value(row.get("Coverage Week Start"))
        if start is None:
            continue

        starts.append(start)

        try:
            number = int(row.get("Coverage Week #"))
        except (ValueError, TypeError):
            number = None

        if number == 1:
            week_one.append(start)

    return min(week_one) if week_one else (
        min(starts) if starts else None
    )


def _first_due_thursday(start_date, weekday_number):
    if start_date is None:
        return None
    offset = (weekday_number - start_date.weekday()) % 7
    return start_date + timedelta(days=offset)


@contribution_calendar_bp.get(
    "/api/member/contribution-calendar"
)
def get_member_contribution_calendar():
    # Never accept the member identity from a URL parameter.
    member_id = str(
        get_current_member_id() or ""
    ).strip().upper()

    if not member_id:
        return jsonify({
            "success": False,
            "message": "Please sign in to view your contribution calendar.",
        }), 401

    today = date.today()

    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))

        if not 2000 <= year <= 2100:
            raise ValueError("Year must be between 2000 and 2100.")
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12.")
    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "message": str(error) or "Invalid calendar month.",
        }), 400

    try:
        member = _read_member(member_id)
        if member is None:
            return jsonify({
                "success": False,
                "message": "Your TLC member record was not found.",
            }), 404

        # This builds the existing allocation ledger in memory only.
        # It does not write or regenerate the coverage workbook.
        ledger = build_coverage_ledger()
        rows = ledger.get("coverage_rows", [])
        settings = ledger.get("settings", {}) or {}

        weekday_name = str(
            settings.get("Contribution Weekday", "THURSDAY")
        ).strip().upper()

        if weekday_name not in WEEKDAYS:
            raise ValueError("Invalid configured contribution weekday.")

        weekday_number = WEEKDAYS[weekday_name]

        try:
            weekly_amount = float(
                str(settings.get("Weekly Contribution Amount", "100"))
                .replace(",", "").strip()
            )
        except (ValueError, TypeError):
            weekly_amount = 100.0

        if weekly_amount <= 0:
            raise ValueError("Invalid weekly contribution amount.")

        group_first_week = _first_group_week(rows)
        registration_date = member["registration_date"]

        if registration_date and group_first_week:
            start_basis = max(registration_date, group_first_week)
        else:
            start_basis = registration_date or group_first_week

        first_due = _first_due_thursday(start_basis, weekday_number)

        # Index covered weeks for this member, using the actual
        # Coverage Week Start date produced by TLC's existing service.
        covered = {}

        for row in rows:
            row_member = str(
                row.get("Member ID") or ""
            ).strip().upper()

            if row_member != member_id:
                continue

            if str(
                row.get("Allocation Status") or ""
            ).strip().upper() != "COVERED":
                continue

            week_start = _date_value(row.get("Coverage Week Start"))
            if week_start is None:
                continue

            try:
                amount = float(row.get("Allocated Amount") or 0)
            except (ValueError, TypeError):
                amount = 0.0

            entry = covered.setdefault(
                week_start,
                {"amount": 0.0, "allocations": 0},
            )
            entry["amount"] += amount
            entry["allocations"] += 1

        items = []
        days_in_month = monthrange(year, month)[1]

        for day_number in range(1, days_in_month + 1):
            due_date = date(year, month, day_number)

            if due_date.weekday() != weekday_number:
                continue

            allocation = covered.get(due_date)

            if first_due is None:
                status = "START_DATE_REQUIRED"
            elif due_date < first_due:
                status = "NOT_DUE"
            elif allocation:
                status = "PAID"
            elif due_date <= today:
                status = "UNPAID"
            else:
                status = "UPCOMING"

            items.append({
                "date": due_date.isoformat(),
                "day": due_date.strftime("%A"),
                "status": status,
                "amount_due": (
                    round(weekly_amount, 2)
                    if status not in (
                        "NOT_DUE", "START_DATE_REQUIRED"
                    )
                    else 0.0
                ),
                "amount_covered": round(
                    allocation["amount"], 2
                ) if allocation else 0.0,
                "allocation_count": (
                    allocation["allocations"] if allocation else 0
                ),
            })

        summary = {
            status.lower(): sum(
                item["status"] == status for item in items
            )
            for status in (
                "PAID", "UNPAID", "UPCOMING",
                "NOT_DUE", "START_DATE_REQUIRED",
            )
        }

        return jsonify({
            "success": True,
            "member": {
                "member_id": member["member_id"],
                "name": member["name"],
            },
            "calendar": {
                "year": year,
                "month": month,
                "month_label": date(year, month, 1).strftime("%B %Y"),
                "contribution_weekday": weekday_name.title(),
                "weekly_amount": round(weekly_amount, 2),
                "first_due_date": (
                    first_due.isoformat() if first_due else None
                ),
                "items": items,
                "summary": summary,
            },
        })

    except FileNotFoundError:
        current_app.logger.exception(
            "Contribution calendar workbook unavailable."
        )
        return jsonify({
            "success": False,
            "message": "Contribution records are temporarily unavailable.",
        }), 503
    except Exception:
        current_app.logger.exception(
            "Unable to calculate contribution calendar."
        )
        return jsonify({
            "success": False,
            "message": "The contribution calendar could not be calculated.",
        }), 500
