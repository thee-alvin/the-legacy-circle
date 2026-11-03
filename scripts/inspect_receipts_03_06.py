import json
from pathlib import Path

path = Path("data/receipts/receipts.json")

with path.open("r", encoding="utf-8") as file:
    data = json.load(file)

receipts = data.get("receipts", []) if isinstance(data, dict) else data

targets = {
    "TLC/RCPT/2026/000003",
    "TLC/RCPT/2026/000006",
}

for receipt in receipts:

    number = str(
        receipt.get("receipt_number", "")
    ).strip()

    if number in targets:

        print()
        print("=" * 80)
        print(number)
        print("=" * 80)

        for key, value in receipt.items():
            print(f"{key}: {value}")
