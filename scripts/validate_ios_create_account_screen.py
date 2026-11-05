import json
import pathlib
import re

root = pathlib.Path(r"C:\Users\Hasnain\Downloads\Automation seeder")
out = root / "output" / "console-update"
cases = json.loads((out / "PRT-0701-cases.json").read_text(encoding="utf-8-sig"))
order = json.loads((out / "PRT-0701-run_order.json").read_text(encoding="utf-8-sig"))
ids = [f"VP-APP-REGISTER-CONSENT-{i:03d}" for i in range(1, 6)]
case_map = {case["id"]: case for case in cases}
order_map = {case["id"]: case for case in order}

html = (out / "PRT-0701-Console-source.html").read_text(encoding="utf-8-sig")
root_html = (root / "PRT-0701-Console-source.updated.html").read_text(encoding="utf-8-sig")
selected = "\n".join(json.dumps(case_map[case_id]) for case_id in ids)
expected = [
    "Create your account",
    "Please accept both to continue.",
    "Your health data is protected",
    "Version 1.0.4 (202609301)",
    "Create account",
]

embedded_match = re.search(
    r"var EMBEDDED_CASES = (\[.*?\]);\n\n  function startWithCases", html, re.S
)
embedded = json.loads(embedded_match.group(1)) if embedded_match else []
embedded_map = {case["id"]: case for case in embedded}

print("IDs in cases:", all(case_id in case_map for case_id in ids))
print("IDs in run order:", all(case_id in order_map for case_id in ids))
print("IDs embedded:", all(case_id in embedded_map for case_id in ids))
print(
    "Cases and embedded match:",
    all(case_map[case_id] == embedded_map[case_id] for case_id in ids),
)
print(
    "Titles match run order:",
    all(case_map[case_id]["t"] == order_map[case_id]["title"] for case_id in ids),
)
print("Titles:", [case_map[case_id]["t"] for case_id in ids])
print("HTML copies match:", html == root_html)
print("Stale wording absent:", "Register with GlucoRx" not in selected)
print("Expected phrases:", {phrase: phrase in html for phrase in expected})
