from openpyxl import Workbook
from pathlib import Path

file = Path("data/spreadsheets/01_MEMBERS.xlsx")

wb = Workbook()
ws = wb.active
ws.title = "Members"

headers = [
    "Member ID",
    "Full Name",
    "Email Address",
    "Phone Number",
    "Password Hash",
    "Membership Status",
    "Registration Date",
    "Last Login",
    "Account Status"
]

ws.append(headers)

for cell in ws[1]:
    cell.font = cell.font.copy(bold=True)

wb.save(file)

print("TLC MEMBERS SPREADSHEET CREATED")
