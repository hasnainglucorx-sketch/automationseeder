from pathlib import Path
import json, re, copy
from docx import Document

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"C:\Users\Hasnain\Downloads\PRT-0392 Modus Mobile Apps UI Test Cases ver-0 1 (1).docx")
COMPACT_PATH = ROOT / "output/console-update/PRT-0701-cases.json"
RUN_PATH = ROOT / "output/console-update/PRT-0701-run_order.json"

doc = Document(str(SOURCE))
old_compact = json.loads(COMPACT_PATH.read_text(encoding="utf-8-sig"))
old_run = json.loads(RUN_PATH.read_text(encoding="utf-8-sig"))
old_c_by_id = {x["id"]: x for x in old_compact}
old_r_by_id = {x["id"]: x for x in old_run}

def cell(row, label):
    for i, c in enumerate(row.cells[:-1]):
        if c.text.strip().casefold() == label.casefold():
            return row.cells[i + 1].text.strip()
    return ""

def paragraphs_and_tables(document):
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    body = document.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)

items = []
current_section = ""
pending_title = ""
for block in paragraphs_and_tables(doc):
    if isinstance(block, type(doc.paragraphs[0])):
        text = block.text.strip()
        if not text:
            continue
        if re.match(r"^VP-APP-[A-Z0-9-]+\b", text):
            pending_title = text
        elif not re.match(r"^\d+(?:\.\d+)*\s", text) and not text.upper() in {
            "PURPOSE", "SCOPE", "IN SCOPE", "OUT OF SCOPE", "RELATED ITEMS",
            "RELATED DOCUMENTS AND RECORDS", "DEFINITIONS AND ACRONYMS",
            "ENVIRONMENT HEALTH AND SAFETY", "ENVIRONMENTAL HEALTH AND SAFETY",
            "RISK ASSESSMENT RATIONALE", "EXPERIMENTAL DESIGN", "ACCEPTANCE CRITERIA",
            "EQUIPMENT AND MATERIALS", "CONTROLLED EQUIPMENT", "MATERIALS", "TEST DATA",
            "PROCESS", "APPENDICES", "APPENDIX A: EXECUTION EVIDENCE",
        }:
            if not text.startswith("This protocol") and not text.startswith("The protocol") and not text.startswith("Execution "):
                current_section = text.strip()
    else:
        table = block
        sample = " ".join(c.text for row in table.rows[:2] for c in row.cells)
        match = re.search(r"VP-APP-[A-Z0-9-]+", sample)
        if not match:
            continue
        tcid = match.group(0)
        rows = table.rows
        requirement = cell(rows[0], "Requirements Tested") if rows else ""
        pre = ""
        test_data = ""
        proc, exp = [], []
        for i, row in enumerate(rows):
            labels = [c.text.strip() for c in row.cells]
            if labels and labels[0].casefold() == "precondition":
                pre = row.cells[1].text.strip()
            elif labels and labels[0].casefold() == "test data":
                test_data = row.cells[1].text.strip()
            elif any(x.casefold() == "test steps" for x in labels):
                for detail in rows[i+1:]:
                    action = detail.cells[0].text.strip()
                    expected = detail.cells[1].text.strip() if len(detail.cells)>1 else ""
                    if re.match(r"^\d+\.", action):
                        proc.append(action)
                        if expected:
                            exp.append(expected)
        title = pending_title
        pending_title = ""
        title = re.sub(r"^VP-APP-[A-Z0-9-]+\s*", "", title).strip() or tcid
        evidence = "Screenshot(s)/recording as applicable; execution record"
        if test_data:
            pre = (pre + "\nTest data: " + test_data).strip()
        prior = old_c_by_id.get(tcid, {})
        prior_run = old_r_by_id.get(tcid, {})
        sec = current_section.strip().strip("- ") or prior.get("sec", "Additional Coverage")
        # Keep a concise section label but take its content from the protocol's ordering.
        compact = {
            "r": len(items) + 1,
            "sec": sec,
            "id": tcid,
            "t": title,
            "method": prior.get("method", "Manual - Real Device"),
            "req": requirement or prior.get("req", "N/A"),
            "pre": pre or prior.get("pre", ""),
            "proc": "\n".join(proc) or prior.get("proc", ""),
            "exp": "\n".join(exp) or prior.get("exp", ""),
            "ev": prior.get("ev", evidence),
        }
        compact.update({k: v for k, v in prior.items() if k not in compact and k not in {"r", "id"}})
        items.append(compact)

assert len(items) == 451, f"Expected 451 protocol cases; extracted {len(items)}"
ids = [x["id"] for x in items]
assert len(set(ids)) == len(ids), "Duplicate test case IDs in source protocol"

run_items = []
for i, item in enumerate(items, 1):
    prior = old_r_by_id.get(item["id"], {})
    full = {
        "run": i,
        "day": prior.get("day", "Day 1"),
        "phase": prior.get("phase", "Phase 1"),
        "id": item["id"],
        "recovery": prior.get("recovery", "R1"),
        "est": prior.get("est", "10"),
        "section": item["sec"],
        "title": item["t"],
        "requirement": item["req"],
        "preconditions": item["pre"],
        "procedure": item["proc"],
        "expected": item["exp"],
        "evidence": item["ev"],
    }
    run_items.append(full)

COMPACT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
RUN_PATH.write_text(json.dumps(run_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Imported {len(items)} unique cases from {SOURCE.name}")
