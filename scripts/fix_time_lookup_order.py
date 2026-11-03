from pathlib import Path

path = Path(r".\app\financial_register\ledger_service.py")
text = path.read_text(encoding="utf-8-sig")

old = """    monthly_coverage_rows = []

    # Original recorded time for each source payment/receipt.
"""

new = """    monthly_coverage_rows = []

    all_time_members = (
        all_time_register.get("members") or []
    )

    # Original recorded time for each source payment/receipt.
"""

if old not in text:
    raise SystemExit("TIME LOOKUP INSERTION POINT NOT FOUND")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("TIME LOOKUP ORDER FIXED.")
