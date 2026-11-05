"""Update registration-launch and hosted registration cases from the iOS screenshots (system prompt, consented screen, hosted form)."""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
LATEST = ROOT / "Claude-Handoff-2026-10-02" / "latest"

NOTICE = "This sets where your health data is stored. It can't be changed later, so choose carefully."

U = {
"VP-APP-REGISTER-CONSENT-005": {
"title": "Open hosted registration after consent",
"pre": "The native Create your account screen is displayed, both consent controls are selected and internet is available.",
"procedure": (
"1. Select Create account once.\n"
"2. Read the iOS sign-in prompt.\n"
"3. Select Continue.\n"
"4. Observe the hosted page."
),
"expected": (
"1. Create account responds once and changes to a disabled Opening secure page... state with a progress indicator.\n"
"2. iOS shows \u201cModus\u201d Wants to Use \u201ckeycloak.dev.platform.glucorx.co.uk\u201d to Sign In, with the text This allows the app and website to share information about you. and Cancel and Continue buttons.\n"
"3. After Continue, the hosted GlucoRx Create your account page opens in the in-app browser with Email, Password, Confirm password, Given name(s), Family name(s) and Region. No duplicate page opens.\n"
"4. No account is created and the user is not signed in."
),
"evidence": "Opening secure page... state, iOS prompt, hosted registration page; execution record."},

"VP-APP-REGISTER-CONSENT-006": None,
}
del U["VP-APP-REGISTER-CONSENT-006"]

# Only the changed text inside existing cases; fields not listed stay as they are.
def reg001(row, run):
    k = "expected" if run else "exp"
    v = row[k]
    v = v.replace("3. The Region notice states that the selection determines where health data are stored and cannot be changed later.",
                  f"3. The notice below Region reads: {NOTICE}")
    v = v.replace("4. Create an account is unavailable while required fields are incomplete.",
                  "4. Create an account and Back to sign in are shown below the notice.")
    row[k] = v

def reg018(row, run):
    k = "expected" if run else "exp"
    row[k] = row[k].replace("2. The notice says the selection determines where health data are stored and cannot be changed later.",
                            f"2. The notice reads: {NOTICE}")

def reg016(row, run):
    k = "procedure" if run else "proc"
    row[k] = "1. Select the X (close) button at the top left of the hosted page."

PATCH = {"VP-APP-HOSTED-REG-001": reg001, "VP-APP-HOSTED-REG-018": reg018, "VP-APP-HOSTED-REG-016": reg016}

def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    cp, rp, hp = OUT/"PRT-0701-cases.json", OUT/"PRT-0701-run_order.json", OUT/"PRT-0701-Console-source.html"
    cases, order = load(cp), load(rp)
    want = set(U) | set(PATCH)
    for rows, run in ((cases, False), (order, True)):
        found = set()
        for row in rows:
            i = row["id"]
            if i in U:
                v = U[i]; found.add(i)
                if run: row.update(title=v["title"], preconditions=v["pre"], procedure=v["procedure"], expected=v["expected"], evidence=v["evidence"])
                else: row.update(t=v["title"], pre=v["pre"], proc=v["procedure"], exp=v["expected"], ev=v["evidence"])
            elif i in PATCH:
                PATCH[i](row, run); found.add(i)
        if found != want: raise RuntimeError(f"missing {want-found}")
    save(cp, cases); save(rp, order)
    html = hp.read_text(encoding="utf-8-sig")
    emb = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\u003c")
    html, n = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.S).subn(lambda m: m.group(1)+emb+m.group(2), html, count=1)
    if n != 1: raise RuntimeError("embed not found")
    hp.write_text(html, encoding="utf-8")
    shutil.copy2(hp, ROOT/"PRT-0701-Console-source.updated.html")
    for name in ("PRT-0701-cases.json","PRT-0701-run_order.json","PRT-0701-Console-source.html"):
        shutil.copy2(OUT/name, LATEST/name)
    shutil.copy2(hp, LATEST/"PRT-0701-Console-source.updated.html")
    shutil.copy2(Path(__file__), LATEST.parent/"scripts"/Path(__file__).name) if Path(__file__).parent != LATEST.parent/"scripts" else None
    print("updated", sorted(want))

if __name__ == "__main__": main()
