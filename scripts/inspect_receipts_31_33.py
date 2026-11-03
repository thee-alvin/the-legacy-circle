import json
from pathlib import Path

path = Path("data/receipts/receipts.json")

with path.open("r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict):
    receipts = data.get("receipts", [])
else:
    receipts = data

wanted = {
    "TLC/RCPT/2026/000031",
    "TLC/RCPT/2026/000032",
    "TLC/RCPT/2026/000033",
}

print("=" * 80)
print("EXISTING RECEIPTS 31–33")
print("=" * 80)

for receipt in receipts:
    number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if number in wanted:
        print()
        print("RECEIPT:", number)

        for key, value in receipt.items():
            print(f"{key}: {value}")
