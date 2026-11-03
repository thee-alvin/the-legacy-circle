from pathlib import Path
from datetime import datetime, date
from copy import copy
import re
from openpyxl import load_workbook

path = Path(r".\data\spreadsheets\03_ANNOUNCEMENTS.xlsx")
backup = path.with_name(
    path.stem + "_before_october_welcome.xlsx"
)

# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------

if not backup.exists():
    backup.write_bytes(path.read_bytes())
    print(f"Backup created: {backup}")

# ------------------------------------------------------------
# LOAD WORKBOOK
# ------------------------------------------------------------

wb = load_workbook(path)
ws = wb["Announcements"]

headers = [
    ws.cell(1, col).value
    for col in range(1, 11)
]

expected = [
    "Announcement ID",
    "Announcement Date",
    "Title",
    "Message",
    "Announcement Type",
    "Priority",
    "Status",
    "Posted By",
    "Expiry Date",
    "Created At",
]

if headers != expected:
    raise SystemExit(
        "Announcement headings do not match the expected structure.\n"
        f"Found: {headers}"
    )

# ------------------------------------------------------------
# PREVENT DUPLICATE
# ------------------------------------------------------------

title = "WELCOME TO OCTOBER 2026"

for row in range(2, ws.max_row + 1):
    existing_title = ws.cell(row, 3).value

    if str(existing_title or "").strip().upper() == title:
        print(
            f"October welcome announcement already exists at row {row}."
        )
        raise SystemExit(0)

# ------------------------------------------------------------
# NEXT ANNOUNCEMENT ID
# ------------------------------------------------------------

highest_number = 0

for row in range(2, ws.max_row + 1):

    value = str(
        ws.cell(row, 1).value or ""
    ).strip()

    match = re.search(
        r"(\d+)$",
        value
    )

    if match:
        highest_number = max(
            highest_number,
            int(match.group(1))
        )

announcement_id = (
    f"ANN-{highest_number + 1:06d}"
)

# ------------------------------------------------------------
# ANNOUNCEMENT
# ------------------------------------------------------------

message = """Dear Members,

A new month is here, and we appreciate every member for the commitment, support, and contributions that helped us through September.

As we begin October 2026, let us continue with the same spirit of unity, responsibility, and consistency. Every contribution strengthens The Legacy Circle and helps us build a stronger group together.

We encourage every member to keep up with their weekly contributions throughout the month and honour their commitments on time.

Let us make October even better than the month before.

United in Purpose. Built to Last.

— THE LEGACY CIRCLE TREASURY"""

now = datetime.now()

next_row = ws.max_row + 1

values = [
    announcement_id,
    date(2026, 10, 1),
    title,
    message,
    "GENERAL",
    "NORMAL",
    "PUBLISHED",
    "THE LEGACY CIRCLE TREASURY",
    date(2026, 10, 31),
    now,
]

for col, value in enumerate(values, start=1):
    ws.cell(
        next_row,
        col,
        value
    )

# ------------------------------------------------------------
# FORMATTING
# ------------------------------------------------------------

ws.cell(next_row, 2).number_format = "dd mmmm yyyy"
ws.cell(next_row, 9).number_format = "dd mmmm yyyy"
ws.cell(next_row, 10).number_format = "dd mmmm yyyy hh:mm:ss"

# Copy basic formatting from previous row where available.
if next_row > 2:
    for col in range(1, 11):
        source = ws.cell(next_row - 1, col)
        target = ws.cell(next_row, col)

        if source.has_style:
            from copy import copy

            target._style = copy(source._style)

        if source.number_format:
            target.number_format = source.number_format

        if source.alignment:
            target.alignment = copy(source.alignment)

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

wb.save(path)

print("")
print("OCTOBER WELCOME ANNOUNCEMENT ADDED SUCCESSFULLY.")
print(f"Announcement ID : {announcement_id}")
print(f"Row             : {next_row}")
print(f"Date            : 01 October 2026")
print(f"Expiry          : 31 October 2026")
print("Status          : PUBLISHED")
print("Posted By       : THE LEGACY CIRCLE TREASURY")
print("")

