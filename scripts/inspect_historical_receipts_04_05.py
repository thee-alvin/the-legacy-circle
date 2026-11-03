import json
from pathlib import Path

backup = Path(
    "data/cleanup_backups/"
    "receipts_before_duplicate_removal_20260918_002711.json"
)

targets = {
    "TLC/RCPT/2026/000004",
    "TLC/RCPT/2026/000005",
}

with backup.open("r", encoding="utf-8") as file:
    data = json.load(file)

if isinstance(data, dict):
    receipts = data.get("receipts", [])
else:
    receipts = data

print("=" * 80)
print("HISTORICAL RECEIPTS 4–5")
print("=" * 80)

found = set()

for receipt in receipts:

    number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if number not in targets:
        continue

    found.add(number)

    print()
    print("-" * 80)
    print("RECEIPT:", number)

    for key, value in receipt.items():
        print(f"{key}: {value}")

print()
print("=" * 80)
print("MISSING FROM HISTORICAL BACKUP")
print("=" * 80)

missing = targets - found

if missing:
    for number in sorted(missing):
        print(number)
else:
    print("NONE")
