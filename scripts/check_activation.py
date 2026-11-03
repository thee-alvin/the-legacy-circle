from pathlib import Path
from openpyxl import load_workbook

file = Path("data/spreadsheets/01_MEMBERS.xlsx")

wb = load_workbook(file)
ws = wb["Members"]

headers = [cell.value for cell in ws[1]]

required = ["Member ID", "Phone Number", "Account Status"]

for name in required:
    if name not in headers:
        raise ValueError(f"Missing column: {name}")

print("TLC MEMBER ACTIVATION DATA: READY")
