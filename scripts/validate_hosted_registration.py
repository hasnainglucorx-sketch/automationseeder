import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ids = [f"VP-APP-HOSTED-REG-{n:03d}" for n in (1, 2, 3, 4, 5, 6, 8, 9)] + ["VP-APP-REGISTER-CONSENT-005", "VP-APP-HOSTED-REG-016", "VP-APP-HOSTED-REG-018"]
for b in (root / "output" / "console-update", root / "Claude-Handoff-2026-10-02" / "latest"):
    c = {r["id"]: r for r in json.loads((b / "PRT-0701-cases.json").read_text(encoding="utf-8-sig"))}
    o = {r["id"]: r for r in json.loads((b / "PRT-0701-run_order.json").read_text(encoding="utf-8-sig"))}
    h = (b / "PRT-0701-Console-source.html").read_text(encoding="utf-8-sig")
    e = {r["id"]: r for r in json.loads(re.search(r"var EMBEDDED_CASES = (\[.*?\]);\n\n  function startWithCases", h, re.S).group(1))}
    ok = all(c[i] == e[i] and o[i]["expected"] == c[i]["exp"] and o[i]["procedure"] == c[i]["proc"]
             and o[i]["preconditions"] == c[i]["pre"] and o[i]["title"] == c[i]["t"] for i in ids)
    stale = [i for i in ids if "Please specify this field." in c[i]["exp"] and "No Please specify" not in c[i]["exp"]]
    print(b.name, len(c), len(o), len(e), "synced:", ok, "stale:", stale)
a = (root / "PRT-0701-Console-source.updated.html").read_bytes()
print("root html identical:", a == (root / "output" / "console-update" / "PRT-0701-Console-source.html").read_bytes())
