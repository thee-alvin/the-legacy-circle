from pathlib import Path
import ast
from datetime import datetime

ROOT = Path(".")

API = ROOT / "app" / "financial_register" / "statements" / "api.py"
JS = ROOT / "frontend" / "assets" / "tlc_member_statements.js"
CSS = ROOT / "frontend" / "assets" / "tlc_member_statements.css"

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# ------------------------------------------------------------
# SAFE BACKUPS
# ------------------------------------------------------------

for path in (API, JS, CSS):
    backup = path.with_name(f"{path.name}.bak_{stamp}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Backup: {backup}")

# ------------------------------------------------------------
# ADMIN API
# Uses the EXISTING TLC contribution coverage ledger.
# ------------------------------------------------------------

api_text = API.read_text(encoding="utf-8")

if "_attach_coverage_to_admin_statement" not in api_text:

    tree = ast.parse(api_text)

    blueprint_end = None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "member_statement_api":
                    blueprint_end = node.end_lineno
                    break
        if blueprint_end:
            break

    if not blueprint_end:
        raise SystemExit(
            "Could not locate member_statement_api Blueprint safely."
        )

    handler = r'''

@member_statement_api.after_request
def _attach_coverage_to_admin_statement(response):
    """Attach the existing TLC coverage ledger to admin statements."""

    if request.path != "/api/tlc/member-statement":
        return response

    try:
        payload = response.get_json(silent=True)

        if not isinstance(payload, dict):
            return response

        statement = payload.get("statement")

        if not isinstance(statement, dict):
            return response

        # The admin API already knows the selected member. Prefer
        # request arguments, then fall back to the returned statement.
        member_id = (
            request.args.get("member_id")
            or request.args.get("memberId")
            or request.args.get("member")
        )

        if not member_id:
            member = statement.get("member") or {}

            member_id = (
                member.get("member_id")
                or member.get("memberId")
                or member.get("Member ID")
                or member.get("id")
            )

        year = request.args.get("year")
        month = request.args.get("month")

        try:
            year_int = int(year)
            month_int = int(month)
        except (TypeError, ValueError):
            return response

        if not member_id or not 1 <= month_int <= 12:
            return response

        from app.financial_register.contribution_coverage.service import (
            get_member_monthly_coverage
        )

        coverage = get_member_monthly_coverage(
            str(member_id).strip().upper(),
            year_int,
            month_int
        )

        if not isinstance(coverage, dict):
            return response

        weeks = coverage.get("weeks") or []

        statement["coverage"] = coverage
        statement["coverageWeeks"] = weeks
        statement["coverageAmount"] = coverage.get("amount", 0)
        statement["coverageWeekCount"] = coverage.get(
            "week_count",
            len(weeks)
        )

        # --------------------------------------------------------
        # Find the original payment(s) that created this coverage.
        # They remain cash transactions dated on their real payment
        # date and are NOT converted into new cash in this month.
        # --------------------------------------------------------

        receipt_numbers = {
            str(row.get("Receipt Number")).strip().upper()
            for row in weeks
            if row.get("Receipt Number")
        }

        contribution_ids = {
            str(row.get("Contribution ID")).strip().upper()
            for row in weeks
            if row.get("Contribution ID")
        }

        try:
            from app.financial_register.statements.service import (
                build_member_statement
            )

            yearly = build_member_statement(
                member_id=str(member_id).strip().upper(),
                year=str(year_int),
                month=None
            )
        except Exception:
            yearly = None

        if isinstance(yearly, dict):

            yearly_member = yearly.get("member") or {}

            history = yearly_member.get("transactions")

            if not isinstance(history, list):
                history = yearly.get("transactions")

            if not isinstance(history, list):
                history = []

            def identities(tx):
                found = set()

                for key in (
                    "receipt",
                    "receipt_number",
                    "receiptNumber",
                    "Receipt Number",
                    "reference",
                    "payment_reference",
                    "paymentReference",
                    "contribution_id",
                    "contributionId",
                    "Contribution ID",
                ):
                    value = tx.get(key)

                    if value not in (None, ""):
                        found.add(
                            str(value).strip().upper()
                        )

                return found

            source_transactions = []

            for tx in history:

                if not isinstance(tx, dict):
                    continue

                ids = identities(tx)

                if (
                    ids.intersection(receipt_numbers)
                    or ids.intersection(contribution_ids)
                ):
                    source_transactions.append(tx)

            member = statement.setdefault("member", {})

            current = member.get("transactions")

            if not isinstance(current, list):
                current = []

            existing = set()

            for tx in current:
                if isinstance(tx, dict):
                    existing.update(identities(tx))

            for tx in source_transactions:

                ids = identities(tx)

                if not ids.intersection(existing):
                    current.append(tx)
                    existing.update(ids)

            member["transactions"] = current
            statement["transactions"] = current
            statement["coverage_source_transactions"] = source_transactions

        payload["statement"] = statement
        response.set_json(payload)

    except Exception as exc:
        print(
            "[ADMIN MEMBER STATEMENT COVERAGE]",
            repr(exc),
            flush=True
        )

    return response
'''

    lines = api_text.splitlines(keepends=True)

    insertion_index = blueprint_end

    api_text = (
        "".join(lines[:insertion_index])
        + handler
        + "".join(lines[insertion_index:])
    )

    API.write_text(api_text, encoding="utf-8")

    print("Admin API coverage connection installed.")

else:
    print("Admin API coverage connection already exists.")

# ------------------------------------------------------------
# ADMIN JS
# ------------------------------------------------------------

js_text = JS.read_text(encoding="utf-8")

if "coverage-admin-block" not in js_text:

    marker = "function renderStatement(statement) {"

    if marker not in js_text:
        raise SystemExit(
            "Could not locate admin renderStatement() safely."
        )

    coverage_code = r'''
function renderStatement(statement) {

    const coverage = statement.coverage || {};

    const coverageWeeks = Array.isArray(coverage.weeks)
        ? coverage.weeks
        : [];

    const coverageAdminBlock = coverageWeeks.length
        ? `
        <section class="coverage-admin-block">

            <div class="coverage-admin-heading">

                <div>
                    <span class="coverage-admin-kicker">
                        CONTRIBUTION COVERAGE
                    </span>

                    <h3>Weeks Catered For</h3>
                </div>

                <strong>
                    ${coverage.week_count || coverageWeeks.length} WEEKS
                </strong>

            </div>

            <div class="coverage-admin-summary">

                <span>MONTHLY COVERAGE</span>

                <strong>
                    KSh ${Number(
                        coverage.amount || 0
                    ).toLocaleString("en-KE", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}
                </strong>

                <small>
                    ${coverage.month || ""}
                </small>

            </div>

            <div class="coverage-admin-note">
                Already Paid — these weeks were funded by earlier
                payment(s). They are not counted again as new cash
                received in the selected month.
            </div>

            <div class="coverage-admin-list">

                ${coverageWeeks.map((week) => `

                    <article class="coverage-admin-row">

                        <div class="coverage-admin-week">

                            <span>
                                WEEK ${week["Coverage Week #"] ?? ""}
                            </span>

                            <strong>
                                ${week["Coverage Week Start"] || ""}
                            </strong>

                            <small>
                                Ends ${week["Coverage Week End"] || ""}
                            </small>

                        </div>

                        <div class="coverage-admin-source">

                            <span>
                                Payment received
                            </span>

                            <strong>
                                ${week["Payment Date"] || ""}
                            </strong>

                            <small>
                                ${week["Receipt Number"]
                                    || week["Contribution ID"]
                                    || ""}
                            </small>

                        </div>

                        <div class="coverage-admin-amount">

                            KSh ${Number(
                                week["Allocated Amount"] || 0
                            ).toLocaleString("en-KE", {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            })}

                        </div>

                    </article>

                `).join("")}

            </div>

        </section>
        `
        : "";

'''

    js_text = js_text.replace(
        marker,
        coverage_code,
        1
    )

    table_marker = '<div class="statement-table-wrap">'

    if table_marker not in js_text:
        raise SystemExit(
            "Could not locate admin statement table safely."
        )

    js_text = js_text.replace(
        table_marker,
        '${coverageAdminBlock}\n\n' + table_marker,
        1
    )

    JS.write_text(js_text, encoding="utf-8")

    print("Admin statement coverage UI installed.")

else:
    print("Admin statement coverage UI already exists.")

# ------------------------------------------------------------
# ADMIN CSS
# ------------------------------------------------------------

css_text = CSS.read_text(encoding="utf-8")

if "coverage-admin-block" not in css_text:

    css_text += r'''

/* ============================================================
   FINANCIAL ADMIN — CONTRIBUTION COVERAGE
   ============================================================ */

.coverage-admin-block {
    margin: 24px 0;
    border: 1px solid rgba(20, 35, 55, .12);
    border-radius: 18px;
    overflow: hidden;
    background: #fff;
    box-shadow: 0 10px 28px rgba(15, 25, 40, .06);
}

.coverage-admin-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 18px 22px;
    background: linear-gradient(135deg, #111d33, #1d2d49);
    color: #fff;
}

.coverage-admin-kicker {
    display: block;
    margin-bottom: 5px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .14em;
    text-transform: uppercase;
    opacity: .78;
}

.coverage-admin-heading h3 {
    margin: 0;
    font-size: 20px;
}

.coverage-admin-heading > strong {
    padding: 9px 13px;
    border-radius: 999px;
    background: rgba(255, 255, 255, .12);
    font-size: 13px;
}

.coverage-admin-summary {
    display: flex;
    align-items: baseline;
    gap: 12px;
    padding: 18px 22px 4px;
}

.coverage-admin-summary span {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .12em;
    color: #687386;
}

.coverage-admin-summary strong {
    font-size: 24px;
    color: #17385e;
}

.coverage-admin-summary small {
    color: #7b8492;
    font-weight: 700;
}

.coverage-admin-note {
    margin: 12px 22px 18px;
    padding: 12px 14px;
    border-radius: 10px;
    background: #f3f6fa;
    color: #596575;
    font-size: 13px;
    line-height: 1.55;
}

.coverage-admin-list {
    border-top: 1px solid #e8ecf1;
}

.coverage-admin-row {
    display: grid;
    grid-template-columns: 1fr 1.2fr auto;
    gap: 18px;
    align-items: center;
    padding: 16px 22px;
    border-bottom: 1px solid #edf0f4;
}

.coverage-admin-row:last-child {
    border-bottom: 0;
}

.coverage-admin-week span,
.coverage-admin-source span {
    display: block;
    margin-bottom: 4px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: .1em;
    color: #7b8492;
    text-transform: uppercase;
}

.coverage-admin-week strong,
.coverage-admin-source strong {
    display: block;
    color: #182235;
}

.coverage-admin-week small,
.coverage-admin-source small {
    display: block;
    margin-top: 3px;
    color: #7b8492;
}

.coverage-admin-amount {
    white-space: nowrap;
    font-weight: 800;
    color: #1d6a48;
}

@media (max-width: 760px) {

    .coverage-admin-row {
        grid-template-columns: 1fr;
        gap: 10px;
    }

    .coverage-admin-heading {
        align-items: flex-start;
        flex-direction: column;
    }

    .coverage-admin-amount {
        justify-self: start;
    }
}
'''

    CSS.write_text(css_text, encoding="utf-8")

    print("Admin coverage CSS installed.")

else:
    print("Admin coverage CSS already exists.")

print("")
print("==============================================")
print("FINANCIAL ADMIN STATEMENT PATCH COMPLETE")
print("==============================================")
