"""Hosted registration: 'Create an account' is always enabled; with empty required fields it does not submit and shows no error (device observation)."""
import json, re, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
LATEST = ROOT / "Claude-Handoff-2026-10-02" / "latest"

# id -> {field: (old, new)} ; field names are compact-case keys
P = {
"VP-APP-HOSTED-REG-001": {"exp": [("4. Create an account and Back to sign in are shown below the notice.",
    "4. Create an account is enabled, and it and Back to sign in are shown below the notice.")]},
"VP-APP-HOSTED-REG-002": {"proc": [("2. Complete Email, Password, Confirm password and Region with valid test data, leaving Given name(s) empty.",
    "2. Complete Email, Password, Confirm password and Region with valid test data, leaving Given name(s) empty.\n3. Select Create an account.")],
  "exp": [("2. Keycloak shows Please specify this field. for Given name(s), and Create an account remains unavailable.",
    "2. The form is not submitted, no account is created and the page stays on Create your account.")]},
"VP-APP-HOSTED-REG-003": {"exp": [("3. With every required field valid, Create an account becomes available while Family name(s) remains empty.",
    "3. Create an account stays enabled while Family name(s) is empty.")]},
"VP-APP-HOSTED-REG-004": {"exp": [("3. Create an account remains unavailable while the email is malformed.",
    "3. No account is created while the email is malformed.")]},
"VP-APP-HOSTED-REG-005": {"exp": [("4. No password-format message is shown and Create an account becomes available.",
    "4. No password-format message is shown.")]},
"VP-APP-HOSTED-REG-006": {"exp": [("Create an account remains unavailable.", "No account is created.")]},
"VP-APP-HOSTED-REG-009": {"exp": [("1. Create an account becomes available when all required values are valid.",
    "1. Create an account is enabled.")]},
}
REG008 = dict(
proc=("1. With every field empty, select Create an account.\n"
"2. Complete all required fields, then clear Email and select Create an account.\n"
"3. Restore Email, clear Password and select Create an account.\n"
"4. Restore Password, clear Confirm password and select Create an account.\n"
"5. Restore Confirm password, clear Given name(s) and select Create an account.\n"
"6. Restore Given name(s), clear Region and select Create an account."),
exp=("1. Create an account is enabled in every state.\n"
"2. Each time a required field is empty, the form is not submitted, no account is created and the page stays on Create your account.\n"
"3. Family name(s) can stay empty without stopping registration."),
pre="Hosted Registration is open. Valid test values are available.")

def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
RUN = {"exp": "expected", "proc": "procedure", "pre": "preconditions"}

def main():
    cp, rp, hp = OUT/"PRT-0701-cases.json", OUT/"PRT-0701-run_order.json", OUT/"PRT-0701-Console-source.html"
    cases, order = load(cp), load(rp)
    for rows, run in ((cases, False), (order, True)):
        seen = set()
        for r in rows:
            i = r["id"]
            if i == "VP-APP-HOSTED-REG-008":
                for k, v in REG008.items(): r[RUN[k] if run else k] = v
                seen.add(i)
            elif i in P:
                for k, subs in P[i].items():
                    key = RUN[k] if run else k
                    for old, new in subs:
                        if old not in r[key]: raise RuntimeError(f"{i}: text not found: {old}")
                        r[key] = r[key].replace(old, new)
                seen.add(i)
        if seen != set(P) | {"VP-APP-HOSTED-REG-008"}: raise RuntimeError("missing")
    save(cp, cases); save(rp, order)
    html = hp.read_text(encoding="utf-8-sig")
    emb = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\u003c")
    html, n = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.S).subn(lambda m: m.group(1)+emb+m.group(2), html, count=1)
    if n != 1: raise RuntimeError("embed not found")
    hp.write_text(html, encoding="utf-8")
    shutil.copy2(hp, ROOT/"PRT-0701-Console-source.updated.html")
    for name in ("PRT-0701-cases.json", "PRT-0701-run_order.json", "PRT-0701-Console-source.html"): shutil.copy2(OUT/name, LATEST/name)
    shutil.copy2(hp, LATEST/"PRT-0701-Console-source.updated.html")
    for s in ("update_ios_hosted_registration_open.py", "update_ios_hosted_registration_button.py"): shutil.copy2(ROOT/"scripts"/s, LATEST.parent/"scripts"/s)
    print("ok")
if __name__ == "__main__": main()
