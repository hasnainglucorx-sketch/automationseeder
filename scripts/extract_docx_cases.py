"""Extract VP-APP-* test case tables from the PRT-0392 source docx.

Reads the docx, walks the body in document order, and for each test-case
table builds a dict matching the run-order JSON schema:
  id, title, requirement, preconditions, procedure, expected, evidence

Procedure/expected are built from the numbered Test Steps / Expected Result
rows. Evidence is a fixed placeholder line already used across the suite
("Screenshot(s)/recording as applicable; execution record") unless the row
table carries something else (not expected in this doc).

Writes output/console-update/PRT-0392-docx-extract.json
"""
import json
import re
import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = sys.argv[1] if len(sys.argv) > 1 else (
    r"C:\Users\Hasnain\Downloads\PRT-0392_Modus_Mobile_Apps_UI_Test_Cases_ver-0_1_2w_FINAL-17.docx"
)
OUT = r"C:\Users\Hasnain\Downloads\Automation seeder\output\console-update\PRT-0392-docx-extract.json"

ID_RE = re.compile(r"\b(VP-[A-Z0-9-]+)\b")


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag.endswith('}p'):
            yield Paragraph(child, parent)
        elif child.tag.endswith('}tbl'):
            yield Table(child, parent)


def main():
    doc = Document(SRC)
    cases = []
    pending_title = None
    pending_id_from_heading = None

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name if block.style else ""
            text = block.text.strip()
            if style.startswith("Heading") and text:
                m = ID_RE.search(text)
                if m:
                    pending_id_from_heading = m.group(1)
                    rest = text[m.end():].strip(" -\u2013\u2014:")
                    pending_title = rest if rest else None
            continue

        # Table block
        if not block.rows:
            continue
        row0 = [c.text.strip() for c in block.rows[0].cells]
        if not row0 or row0[0] != "Test Case ID":
            continue
        case_id = row0[1].strip() if len(row0) > 1 else ""
        m = ID_RE.search(case_id)
        if not m:
            continue
        case_id = m.group(1)

        # requirement: row0 col index 3 (label "Requirements Tested") value col 3 or 4
        requirement = ""
        if len(row0) >= 4:
            requirement = row0[3].strip()

        # precondition row(s): "Precondition" row, optionally followed by a
        # "Test Data" row before the "Test Steps" header row.
        precondition_parts = []
        header_idx = None
        for ri in range(1, len(block.rows)):
            cells = [c.text.strip() for c in block.rows[ri].cells]
            if not cells:
                continue
            label = cells[0]
            if label == "Test Steps":
                header_idx = ri
                break
            if label == "Precondition" and len(cells) > 1:
                precondition_parts.append(cells[1].strip())
            elif label == "Test Data" and len(cells) > 1:
                precondition_parts.append(f"Test data: {cells[1].strip()}")
        precondition = "\n".join(p for p in precondition_parts if p)

        # steps rows: everything after the header row
        proc_lines = []
        exp_lines = []
        if header_idx is not None:
            for r in block.rows[header_idx + 1:]:
                cells = [c.text.strip() for c in r.cells]
                if not cells or not cells[0]:
                    continue
                step = cells[0]
                result = cells[1] if len(cells) > 1 else ""
                if step:
                    proc_lines.append(step)
                if result:
                    exp_lines.append(result)

        title = pending_title if (pending_id_from_heading == case_id and pending_title) else ""

        cases.append({
            "id": case_id,
            "title": title,
            "requirement": requirement,
            "preconditions": precondition,
            "procedure": "\n".join(proc_lines),
            "expected": "\n".join(exp_lines),
        })

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(cases)} cases -> {OUT}")
    ids = [c["id"] for c in cases]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print("WARNING duplicate ids:", dupes)


if __name__ == "__main__":
    main()
