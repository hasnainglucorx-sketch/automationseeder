"""Usage: python scripts/check_case_rules.py [ID ...]  (no IDs = list rule violations in all cases)
Checks CLAUDE.md rules: sync of both JSONs and embedded console, 1:1 numbering, state-only preconditions."""
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "output" / "console-update"
case_rows = json.loads((out / "PRT-0701-cases.json").read_text(encoding="utf-8-sig"))
order_rows = json.loads((out / "PRT-0701-run_order.json").read_text(encoding="utf-8-sig"))
cases = {r["id"]: r for r in case_rows}
order = {r["id"]: r for r in order_rows}
html = (root / "CGMX1-Console.html").read_text(encoding="utf-8-sig")


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


emb = {r["id"]: r for r in embedded_app_cases(html)}
ids = sys.argv[1:] or sorted(set(cases) | set(order))
VERBS = r"(?:tap|open|enter|select|record|clear|install|remove|refresh|click|launch|press|navigate|perform|run|restore|reset|log in)"
# an instruction: verb at the start of a sentence/clause, or "tap" anywhere
ACTION = re.compile(r"(?:^|[.;:(]\s*|\bthen\s+|\band\s+)" + VERBS + r"\b|\btap\b", re.I)


def items(text):
    return re.findall(r"^\s*(\d+)\.\s", text, re.M)


bad = []
for label, rows in (("compact", case_rows), ("run_order", order_rows)):
    seen = set()
    for row in rows:
        case_id = row["id"]
        if case_id in seen:
            bad.append((case_id, f"duplicate ID in {label}"))
        seen.add(case_id)

for i in ids:
    c, o = cases.get(i), order.get(i)
    if c is None or o is None:
        bad.append((i, "missing in a JSON file"))
        continue
    for a, k in (("t", "title"), ("pre", "preconditions"), ("proc", "procedure"), ("exp", "expected"), ("ev", "evidence")):
        if c[a] == o[k]:
            continue
        bad.append((i, f"{a} differs between compact and run_order"))
    if emb.get(i) != c:
        bad.append((i, "embedded console object differs"))
    for label, p, e, pre in (("compact", c["proc"], c["exp"], c["pre"]), ("run_order", o["procedure"], o["expected"], o["preconditions"])):
        pi, ei = items(p), items(e)
        if p.startswith("Removed") or not pi:
            continue
        if pi != [str(n) for n in range(1, len(pi) + 1)] or pi != ei:
            bad.append((i, f"{label}: procedure steps {len(pi)} vs expected items {len(ei)}"))
        m = ACTION.search(pre)
        if m:
            bad.append((i, f"{label}: precondition contains action word '{m.group(0)}'"))
print("cases", len(cases), "run_order", len(order), "embedded", len(emb))
for i, why in bad:
    print(" FAIL", i, why)
print("violations:", len(bad))
print("affected cases:", len({i for i, _ in bad}))
