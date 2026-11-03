from pathlib import Path
from datetime import datetime

ROOT = Path(".")
api = ROOT / "app" / "financial_register" / "statements" / "api.py"
js = ROOT / "frontend" / "assets" / "tlc_member_statements.js"
css = ROOT / "frontend" / "assets" / "tlc_member_statements.css"

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for p in (api, js, css):
    backup = p.with_name(f"{p.name}.bak_{stamp}")
    backup.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Backup: {backup}")

# ============================================================
# 1. FINANCIAL ADMIN API
#    Reuse TLC's existing contribution coverage ledger.
# ============================================================

text = api.read_text(encoding="utf-8")

import_line = (
    "from app.financial_register.contribution_coverage.service "
    "import get_member_monthly_coverage\n"
)

if import_line not in text:
    anchor = "from app.financial_register.statements.service import build_member_statement\n"
    if anchor not in text:
        raise SystemExit("API import anchor not found.")
    text = text.replace(anchor, anchor + import_line, 1)

handler = r'''

@member_statement_api.after_request
def _attach_coverage_to_admin_statement(response):
    """Attach ledger-based coverage to Financial Admin member statements."""

    if request.path != "/api/tlc/member-statement":
        return response

    try:
        payload = response.get_json(silent=True)

        if not isinstance(payload, dict):
            return response

        statement = payload.get("statement")

        if not isinstance(statement, dict):
            return response

        member_id = (
            request.args.get("member_id")
            or request.args.get("memberId")
            or request.args.get("member")
        )

        if not member_id:
            member_info = statement.get("member") or {}
            member_id = (
                member_info.get("member_id")
                or member_info.get("id")
                or member_info.get("Member ID")
            )

        year = request.args.get("year")
        month = request.args.get("month")

        if not member_id or not year or not month:
            return response

        try:
            year_int = int(str(year))
            month_int = int(str(month))
        except (TypeError, ValueError):
            return response

        if not 1 <= month_int <= 12:
            return response

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
        statement["coverageWeekCount"] = coverage.get("week_count", len(weeks))

        # Load the whole year's statement so the admin view can show the
        # original cash transaction that created the coverage.
        try:
            history_statement = build_member_statement(
                member_id=str(member_id).strip().upper(),
                year=str(year_int),
                month=None
            )
        except Exception:
            history_statement = None

        if isinstance(history_statement, dict) and weeks:
            history_member = history_statement.get("member") or {}
            history_transactions = history_member.get("transactions")

            if not isinstance(history_transactions, list):
                history_transactions = history_statement.get("transactions")

            if not isinstance(history_transactions, list):
                history_transactions = []

            source_receipts = {
                str(row.get("Receipt Number") or "").strip().upper()
                for row in weeks
                if row.get("Receipt Number")
            }

            source_contributions = {
                str(row.get("Contribution ID") or "").strip().upper()
                for row in weeks
                if row.get("Contribution ID")
            }

            source_transactions = []

            def tx_identity(tx):
                values = []

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
                    value = tx.get(key) if isinstance(tx, dict) else None
                    if value not in (None, ""):
                        values.append(str(value).strip().upper())

                return set(values)

            for tx in history_transactions:
                if not isinstance(tx, dict):
                    continue

                identity = tx_identity(tx)

                if (
                    identity.intersection(source_receipts)
                    or identity.intersection(source_contributions)
                ):
                    source_transactions.append(tx)

            member = statement.setdefault("member", {})
            current = member.get("transactions")

            if not isinstance(current, list):
                current = []

            existing_ids = set()

            for tx in current:
                if isinstance(tx, dict):
                    existing_ids.update(tx_identity(tx))

            for tx in source_transactions:
                ids = tx_identity(tx)

                if not ids.intersection(existing_ids):
                    current.append(tx)
                    existing_ids.update(ids)

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

if "_attach_coverage_to_admin_statement" not in text:
    # Put the handler immediately after blueprint creation.
    marker = (
        'member_statement_api = Blueprint(\n'
        '    "member_statement_api",\n'
        '    __name__\n'
        ')\n'
    )

    if marker not in text:
        raise SystemExit("Admin blueprint marker not found.")

    text = text.replace(
        marker,
        marker + handler,
        1
    )

api.write_text(text, encoding="utf-8")

# ============================================================
# 2. FINANCIAL ADMIN JAVASCRIPT
# ============================================================

text = js.read_text(encoding="utf-8")

if "coverage-admin-block" not in text:

    render_marker = "function renderStatement(statement) {\n"

    if render_marker not in text:
        raise SystemExit("Admin renderStatement() marker not found.")

    declarations = r'''
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
                        <span class="coverage-admin-kicker">CONTRIBUTION COVERAGE</span>
                        <h3>Weeks Catered For</h3>
                    </div>
                    <strong>${coverage.week_count || coverageWeeks.length} WEEKS</strong>
                </div>

                <div class="coverage-admin-summary">
                    <span>MONTHLY COVERAGE</span>
                    <strong>KSh ${Number(coverage.amount || 0).toLocaleString("en-KE", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}</strong>
                    <small>${coverage.month || ""}</small>
                </div>

                <div class="coverage-admin-note">
                    Already Paid — these weeks were funded by earlier
                    payment(s) and are not counted again as new cash received
                    in the selected month.
                </div>

                <div class="coverage-admin-list">
                    ${coverageWeeks.map((week) => `
                        <article class="coverage-admin-row">
                            <div class="coverage-admin-week">
                                <span>WEEK ${week["Coverage Week #"] ?? ""}</span>
                                <strong>${week["Coverage Week Start"] || ""}</strong>
                                <small>Ends ${week["Coverage Week End"] || ""}</small>
                            </div>

                            <div class="coverage-admin-source">
                                <span>Payment received</span>
                                <strong>${week["Payment Date"] || ""}</strong>
                                <small>
                                    ${week["Receipt Number"] || week["Contribution ID"] || ""}
                                </small>
                            </div>

                            <div class="coverage-admin-amount">
                                KSh ${Number(week["Allocated Amount"] || 0).toLocaleString("en-KE", {
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
    text = text.replace(
        render_marker,
        declarations,
        1
    )

    table_marker = '<div class="statement-table-wrap">'

    if table_marker not in text:
        raise SystemExit("Admin statement table marker not found.")

    text = text.replace(
        table_marker,
        '${coverageAdminBlock}\n\n            ' + table_marker,
        1
    )

js.write_text(text, encoding="utf-8")

# ============================================================
# 3. FINANCIAL ADMIN CSS
# ============================================================

text = css.read_text(encoding="utf-8")

if "coverage-admin-block" not in text:

    text += r'''

/* ============================================================
   CONTRIBUTION COVERAGE — FINANCIAL ADMIN MEMBER STATEMENTS
   ============================================================ */

.coverage-admin-block {
    margin: 24px 0;
    padding: 0;
    border: 1px solid rgba(20, 35, 55, 0.12);
    border-radius: 18px;
    overflow: hidden;
    background: #ffffff;
    box-shadow: 0 10px 28px rgba(15, 25, 40, 0.06);
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
    flex: 0 0 auto;
    padding: 9px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.12);
    font-size: 13px;
    letter-spacing: .04em;
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

    .coverage-admin-amount {
        justify-self: start;
    }

    .coverage-admin-heading {
        align-items: flex-start;
        flex-direction: column;
    }
}
'''

    css.write_text(text, encoding="utf-8")

print("")
print("FINANCIAL ADMIN MEMBER STATEMENTS PATCHED.")
print("")
print("Backend:")
print("  Existing TLC contribution coverage ledger connected.")
print("  Cash totals remain tied to payment date.")
print("  Coverage is shown separately.")
print("  Original source payment is preserved in history.")
print("")
print("Frontend:")
print("  Contribution Coverage section added.")
print("  Coverage rows use the existing ledger.")
print("")
