"""Correct VP-APP-SHARE-002 traceability without changing case content."""

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
CASE_ID = "VP-APP-SHARE-002"
COMPACT_REQUIREMENT = "DI-103 / DO not assigned (gap)"
FULL_REQUIREMENT = "DI-103 (DO ID not assigned in the controlled DI/DO workbook — gap)"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    cases_path = OUT / "PRT-0701-cases.json"
    order_path = OUT / "PRT-0701-run_order.json"
    html_path = OUT / "PRT-0701-Console-source.html"

    cases = load(cases_path)
    order = load(order_path)
    compact = [row for row in cases if row.get("id") == CASE_ID]
    full = [row for row in order if row.get("id") == CASE_ID]
    if len(compact) != 1 or len(full) != 1:
        raise RuntimeError(f"Expected one {CASE_ID} in each JSON file")

    compact[0]["req"] = COMPACT_REQUIREMENT
    full[0]["requirement"] = FULL_REQUIREMENT
    save(cases_path, cases)
    save(order_path, order)

    html = html_path.read_text(encoding="utf-8-sig")
    embedded = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    pattern = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.DOTALL)
    html, count = pattern.subn(lambda match: match.group(1) + embedded + match.group(2), html, count=1)
    if count != 1:
        raise RuntimeError("Embedded case list was not found")
    html_path.write_text(html, encoding="utf-8")
    shutil.copy2(html_path, ROOT / "PRT-0701-Console-source.updated.html")
    print(f"Updated {CASE_ID} traceability")


if __name__ == "__main__":
    main()
