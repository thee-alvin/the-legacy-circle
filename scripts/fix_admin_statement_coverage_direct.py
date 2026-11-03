from pathlib import Path
from datetime import datetime
import re

ROOT = Path(".")

API = ROOT / "app" / "financial_register" / "statements" / "api.py"
JS = ROOT / "frontend" / "assets" / "tlc_member_statements.js"
CSS = ROOT / "frontend" / "assets" / "tlc_member_statements.css"

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# ------------------------------------------------------------
# BACKUPS
# ------------------------------------------------------------

for path in (API, JS, CSS):
    backup = path.with_name(f"{path.name}.bak_{stamp}")
    backup.write_text(
        path.read_text(encoding="utf-8-sig"),
        encoding="utf-8"
    )
    print(f"Backup: {backup}")

# ------------------------------------------------------------
# 1. ADMIN API — DIRECT ROUTE PATCH
# ------------------------------------------------------------

api_text = API.read_text(encoding="utf-8-sig")

import_line = (
    "from app.financial_register.contribution_coverage.service "
    "import get_member_monthly_coverage\n"
)

if import_line not in api_text:
    api_text = import_line + api_text

if "# ADMIN DIRECT COVERAGE PATCH" not in api_text:

    lines = api_text.splitlines(keepends=True)

    function_index = None

    for i, line in enumerate(lines):
        if re.match(r"^\s*def\s+member_statement\s*\(", line):
            function_index = i
            break

    if function_index is None:
        raise SystemExit(
            "Could not locate def member_statement()."
        )

    target_index = None

    for i in range(function_index + 1, len(lines)):
        if re.match(r"^\s*def\s+", lines[i]):
            break

        if re.match(r"^\s*if\s+statement\s+is\s+None\s*:", lines[i]):
            target_index = i
            break

    if target_index is None:
        raise SystemExit(
            "Could not locate the statement-not-found check."
        )

    target_indent = re.match(
        r"^(\s*)",
        lines[target_index]
    ).group(1)

    patch = f'''{target_indent}# ADMIN DIRECT COVERAGE PATCH
{target_indent}if year and month:
{target_indent}    try:
{target_indent}        coverage = get_member_monthly_coverage(
{target_indent}            member_id,
{target_indent}            int(year),
{target_indent}            int(month)
{target_indent}        )
{target_indent}    except Exception as coverage_error:
{target_indent}        print(
{target_indent}            "[ADMIN COVERAGE ERROR]",
{target_indent}            repr(coverage_error),
{target_indent}            flush=True
{target_indent}        )
{target_indent}        coverage = None
{target_indent}else:
{target_indent}    coverage = None

{target_indent}if isinstance(coverage, dict):
{target_indent}    weeks = coverage.get("weeks") or []

{target_indent}    statement["coverage"] = coverage
{target_indent}    statement["coverageWeeks"] = weeks
{target_indent}    statement["coverageAmount"] = coverage.get("amount", 0)
{target_indent}    statement["coverageWeekCount"] = coverage.get(
{target_indent}        "week_count",
{target_indent}        len(weeks)
{target_indent}    )

{target_indent}    # Bring the original source payment into the statement
{target_indent}    # history without changing the selected month's cash totals.
{target_indent}    try:
{target_indent}        yearly_statement = build_member_statement(
{target_indent}            member_id=member_id,
{target_indent}            year=year,
{target_indent}            month=None
{target_indent}        )
{target_indent}    except Exception:
{target_indent}        yearly_statement = None

{target_indent}    if isinstance(yearly_statement, dict) and weeks:

{target_indent}        source_receipts = {{
{target_indent}            str(row.get("Receipt Number")).strip().upper()
{target_indent}            for row in weeks
{target_indent}            if row.get("Receipt Number")
{target_indent}        }}

{target_indent}        source_contributions = {{
{target_indent}            str(row.get("Contribution ID")).strip().upper()
{target_indent}            for row in weeks
{target_indent}            if row.get("Contribution ID")
{target_indent}        }}

{target_indent}        year_member = yearly_statement.get("member") or {{}}
{target_indent}        history = year_member.get("transactions")

{target_indent}        if not isinstance(history, list):
{target_indent}            history = yearly_statement.get("transactions")

{target_indent}        if not isinstance(history, list):
{target_indent}            history = []

{target_indent}        def _tx_ids(tx):
{target_indent}            found = set()

{target_indent}            for key in (
{target_indent}                "receipt",
{target_indent}                "receipt_number",
{target_indent}                "receiptNumber",
{target_indent}                "Receipt Number",
{target_indent}                "reference",
{target_indent}                "payment_reference",
{target_indent}                "paymentReference",
{target_indent}                "contribution_id",
{target_indent}                "contributionId",
{target_indent}                "Contribution ID",
{target_indent}            ):
{target_indent}                value = tx.get(key)
{target_indent}                if value not in (None, ""):
{target_indent}                    found.add(str(value).strip().upper())

{target_indent}            return found

{target_indent}        source_transactions = []

{target_indent}        for tx in history:
{target_indent}            if not isinstance(tx, dict):
{target_indent}                continue

{target_indent}            ids = _tx_ids(tx)

{target_indent}            if (
{target_indent}                ids.intersection(source_receipts)
{target_indent}                or ids.intersection(source_contributions)
{target_indent}            ):
{target_indent}                source_transactions.append(tx)

{target_indent}        member_block = statement.setdefault("member", {{}})
{target_indent}        current_transactions = member_block.get("transactions")

{target_indent}        if not isinstance(current_transactions, list):
{target_indent}            current_transactions = []

{target_indent}        existing_ids = set()

{target_indent}        for tx in current_transactions:
{target_indent}            if isinstance(tx, dict):
{target_indent}                existing_ids.update(_tx_ids(tx))

{target_indent}        for tx in source_transactions:
{target_indent}            ids = _tx_ids(tx)

{target_indent}            if not ids.intersection(existing_ids):
{target_indent}                current_transactions.append(tx)
{target_indent}                existing_ids.update(ids)

{target_indent}        member_block["transactions"] = current_transactions
{target_indent}        statement["transactions"] = current_transactions
{target_indent}        statement["coverage_source_transactions"] = source_transactions

'''

    lines[target_index:target_index] = patch.splitlines(
        keepends=True
    )

    api_text = "".join(lines)

API.write_text(api_text, encoding="utf-8")

# ------------------------------------------------------------
# 2. ADMIN JAVASCRIPT
# ------------------------------------------------------------

js_text = JS.read_text(encoding="utf-8-sig")

if "coverageAdminBlock" not in js_text:

    marker = "function renderStatement(statement) {"

    if marker not in js_text:
        raise SystemExit(
            "Could not locate admin renderStatement()."
        )

    coverage_declaration = r'''
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
                    Already Paid — these weeks were funded by
                    earlier payment(s). They are not counted again
                    as new cash received in this month.
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
        coverage_declaration,
        1
    )

    summary_marker = '<div class="statement-summary">'

    if summary_marker not in js_text:
        raise SystemExit(
            "Could not locate statement summary."
        )

    js_text = js_text.replace(
        summary_marker,
        '${coverageAdminBlock}\n\n            ' + summary_marker,
        1
    )

JS.write_text(js_text, encoding="utf-8")

# ------------------------------------------------------------
# 3. ADMIN CSS
# ------------------------------------------------------------

css_text = CSS.read_text(encoding="utf-8-sig")

if "coverage-admin-block" not in css_text:

    css_text += r'''

/* ============================================================
   FINANCIAL ADMIN CONTRIBUTION COVERAGE
   ============================================================ */

.coverage-admin-block {
    margin: 24px 0;
    border: 1px solid rgba(20,35,55,.12);
    border-radius: 18px;
    overflow: hidden;
    background: #fff;
    box-shadow: 0 10px 28px rgba(15,25,40,.06);
}

.coverage-admin-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 18px 22px;
    background: linear-gradient(135deg,#111d33,#1d2d49);
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
    background: rgba(255,255,255,.12);
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

@media (max-width:760px) {

    .coverage-admin-row {
        grid-template-columns: 1fr;
        gap: 10px;
    }

    .coverage-admin-heading {
        align-items: flex-start;
        flex-direction: column;
    }
}
'''

CSS.write_text(css_text, encoding="utf-8")

print("")
print("ADMIN COVERAGE DIRECT PATCH COMPLETE.")
