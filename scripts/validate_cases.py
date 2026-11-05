"""Usage: python scripts/validate_cases.py ID [ID ...]  - checks cases.json, run_order.json and the embedded console data agree."""
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ids = sys.argv[1:]


def embedded_app_cases(source):
    """Read either the current unified console or the legacy console format."""
    patterns = (
        r"const\s+ALL_APP_CASES\s*=\s*(\[.*?\]);\s*const\s+ALL_PORTAL_CASES",
        r"var\s+EMBEDDED_CASES\s*=\s*(\[.*?\]);\s*function\s+startWithCases",
    )
    for pattern in patterns:
        match = re.search(pattern, source, re.S)
        if match:
            return json.loads(match.group(1))
    raise RuntimeError("No supported embedded PRT-0701 case array was found in the console")


for b in (root / "output" / "console-update", root / "Claude-Handoff-2026-10-02" / "latest"):
    c = {r["id"]: r for r in json.loads((b / "PRT-0701-cases.json").read_text(encoding="utf-8-sig"))}
    o = {r["id"]: r for r in json.loads((b / "PRT-0701-run_order.json").read_text(encoding="utf-8-sig"))}
    h = (b / "PRT-0701-Console-source.html").read_text(encoding="utf-8-sig")
    e = {r["id"]: r for r in embedded_app_cases(h)}
    ok = all(c[i] == e[i] and o[i]["expected"] == c[i]["exp"] and o[i]["procedure"] == c[i]["proc"]
             and o[i]["preconditions"] == c[i]["pre"] and o[i]["title"] == c[i]["t"] and o[i]["evidence"] == c[i]["ev"] for i in ids)
    print(b.name, len(c), len(o), len(e), "synced:", ok)
same = (root / "PRT-0701-Console-source.updated.html").read_bytes() == (root / "output" / "console-update" / "PRT-0701-Console-source.html").read_bytes()
print("root html identical:", same)
