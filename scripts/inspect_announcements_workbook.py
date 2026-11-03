from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import re

path = Path(r".\data\spreadsheets\03_ANNOUNCEMENTS.xlsx")

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}

def col_number(ref):
    letters = re.match(r"[A-Z]+", ref).group()
    number = 0
    for ch in letters:
        number = number * 26 + ord(ch) - 64
    return number

with ZipFile(path, "r") as z:

    # Shared strings
    shared = []

    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(
            z.read("xl/sharedStrings.xml")
        )

        for item in root.findall("main:si", NS):
            text = "".join(
                node.text or ""
                for node in item.iter("{%s}t" % NS["main"])
            )
            shared.append(text)

    # Workbook
    workbook = ET.fromstring(
        z.read("xl/workbook.xml")
    )

    relationships = ET.fromstring(
        z.read("xl/_rels/workbook.xml.rels")
    )

    rel_map = {}

    for rel in relationships:
        rel_map[rel.attrib["Id"]] = rel.attrib["Target"]

    print("")
    print("=" * 70)
    print("03_ANNOUNCEMENTS.xlsx — WORKBOOK STRUCTURE")
    print("=" * 70)

    for sheet in workbook.find("main:sheets", NS):

        name = sheet.attrib["name"]
        rid = sheet.attrib[
            "{%s}id" % NS["rel"]
        ]

        target = rel_map[rid]

        if target.startswith("/"):
            target = target[1:]

        if not target.startswith("xl/"):
            target = "xl/" + target

        print("")
        print(f"SHEET: {name}")
        print(f"XML:   {target}")
        print("-" * 70)

        xml = ET.fromstring(
            z.read(target)
        )

        rows = xml.findall(
            ".//main:sheetData/main:row",
            NS
        )

        for row in rows[:12]:

            values = []

            for cell in row.findall("main:c", NS):

                ref = cell.attrib.get("r", "")

                cell_type = cell.attrib.get("t")
                value_node = cell.find("main:v", NS)
                inline_node = cell.find("main:is", NS)

                value = ""

                if cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(
                        node.text or ""
                        for node in inline_node.iter(
                            "{%s}t" % NS["main"]
                        )
                    )

                elif value_node is not None:
                    raw = value_node.text or ""

                    if cell_type == "s":
                        try:
                            value = shared[int(raw)]
                        except (ValueError, IndexError):
                            value = raw
                    else:
                        value = raw

                if value != "":
                    values.append(
                        f"{ref}={value}"
                    )

            if values:
                print(" | ".join(values))

    print("")
    print("=" * 70)
    print("END")
    print("=" * 70)
