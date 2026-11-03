from pathlib import Path

p = Path("frontend/pages/dashboard.html")
text = p.read_text(encoding="utf-8")

if '/member/constitution' in text:
    print("CONSTITUTION ALREADY IN SIDEBAR")
    raise SystemExit

marker = '<a href="/member/elections" class="nav-item">'

insert = '''<a href="/member/constitution" class="nav-item">
                <span class="nav-icon">▣</span>
                <span>Constitution</span>
              </a>

              '''

if marker not in text:
    raise SystemExit("ELECTIONS SIDEBAR ITEM NOT FOUND")

text = text.replace(marker, insert + marker, 1)

p.write_text(text, encoding="utf-8")

print("CONSTITUTION ADDED TO DASHBOARD SIDEBAR")
