from pathlib import Path

try:
    import fitz
except ImportError:
    raise SystemExit(
        "PyMuPDF is not installed. Run: pip install pymupdf"
    )

BASE_DIR = Path(__file__).resolve().parents[1]
PDF_FILE = BASE_DIR / "data" / "documents" / "TLC_Constitution.pdf"
TEXT_FILE = BASE_DIR / "data" / "documents" / "TLC_Constitution.txt"

if not PDF_FILE.exists():
    raise SystemExit("TLC Constitution PDF was not found.")

document = fitz.open(PDF_FILE)

pages = []

for page in document:
    text = page.get_text("text").strip()

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if "TLC CONSTITUTION" in line and "P a g e" in line:
            continue

        lines.append(line)

    pages.append("\n".join(lines))

document.close()

TEXT_FILE.write_text(
    "\n\n".join(pages),
    encoding="utf-8"
)

print("TLC CONSTITUTION TEXT CREATED SUCCESSFULLY")
print(TEXT_FILE)
