from pathlib import Path

ROOT = Path(".")

targets = [
    "TLC-CON-000003",
    "TLC-CON-000004",
    "TLC/RCPT/2026/000004",
    "TLC/RCPT/2026/000005",
]

extensions = {
    ".json",
    ".txt",
    ".log",
    ".csv",
    ".xlsx",
}

print("=" * 80)
print("SEARCHING FOR HISTORICAL CONTRIBUTION / RECEIPT 4–5 RECORDS")
print("=" * 80)

found_any = False

for path in ROOT.rglob("*"):

    if not path.is_file():
        continue

    if path.suffix.lower() not in extensions:
        continue

    if any(part.lower() in {
        ".venv",
        "node_modules",
        "__pycache__"
    } for part in path.parts):
        continue

    try:
        if path.suffix.lower() == ".xlsx":
            continue

        content = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        matches = [
            target
            for target in targets
            if target in content
        ]

        if matches:
            found_any = True

            print()
            print("FILE:", path)

            for match in matches:
                print("  FOUND:", match)

    except Exception:
        pass

print()

if not found_any:
    print("NO HISTORICAL TEXT/JSON/LOG RECORDS FOUND FOR 4 OR 5.")

print("=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)
