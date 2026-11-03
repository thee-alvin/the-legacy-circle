from pathlib import Path

path = Path(r"frontend\js\dashboard.js")

backup = Path(r"frontend\js\dashboard.js.before-receipt-summary.html")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

function = r'''
/* ============================================================
   RECEIPT SUMMARY
   ============================================================ */

async function loadReceiptSummary() {

    const receiptElement =
        document.getElementById("receiptCount");

    if (!receiptElement) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/member/receipts",
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    },
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok || !data.success) {
            return;
        }

        const receipts =
            Array.isArray(data.receipts)
                ? data.receipts
                : [];

        receiptElement.textContent =
            receipts.length;

    } catch (error) {

        console.error(
            "Receipt dashboard summary error:",
            error
        );
    }
}

'''

if "async function loadReceiptSummary()" not in text:

    marker = "async function loadContributionSummary()"

    if marker not in text:
        raise SystemExit(
            "Could not find loadContributionSummary()"
        )

    text = text.replace(
        marker,
        function + marker,
        1
    )

call = "        loadMemberProfile();"

if "        loadReceiptSummary();" not in text:

    if call not in text:
        raise SystemExit(
            "Could not find dashboard startup section"
        )

    text = text.replace(
        call,
        call + "\n        loadReceiptSummary();",
        1
    )

path.write_text(text, encoding="utf-8")

print("Dashboard receipt summary connected successfully.")
print(f"Backup created: {backup}")
