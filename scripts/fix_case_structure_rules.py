"""Bring cases I edited this session into the CLAUDE.md structure: state-only preconditions, one-to-one Procedure/Expected numbering,
identical compact and run_order text. Loads the latest files at run time and touches only the IDs below."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
LATEST = ROOT / "Claude-Handoff-2026-10-02" / "latest"

D = "Create an account is disabled and cannot be selected, even though it is shown in blue."
NOTICE = "This sets where your health data is stored. It can't be changed later, so choose carefully."
LANGS = "English (UK), English (US), Cymraeg, العربية and Español"

U = {
"VP-APP-SIGNIN-001": dict(
 pre="The user is signed out and the native Welcome back screen is displayed.",
 proc=("1. Inspect the image, CGMx 1 logo, heading and introduction at the top of the screen.\n"
       "2. Inspect the Sign in action and the Forgot your password? link.\n"
       "3. Inspect the data-protection card.\n"
       "4. Inspect the Create an account link and the app version at the bottom of the screen.\n"
       "5. Compare the whole screen with the approved iOS reference."),
 exp=("1. The lifestyle image, CGMx 1 logo, Welcome back heading and Sign in to pick up where you left off. are shown.\n"
      "2. Sign in and Forgot your password? are shown.\n"
      "3. The card reads Your health data is protected and Your information is encrypted in transit and at rest.\n"
      "4. New to Modus? Create an account and the app version are shown. The reference version is Version 1.0.4 (202609301).\n"
      "5. No content is missing, duplicated, clipped, overlapping or corrupted."),
 ev="Full screen compared with the approved iOS reference; displayed version; execution record."),
"VP-APP-SIGNIN-002": dict(
 pre="The user is signed out, internet is available and the native Welcome back screen is displayed.",
 proc="1. Select Sign in once.",
 exp="1. The hosted GlucoRx Sign in page opens in the in-app browser with Email and Password fields, without a blank page, crash or native credential form.",
 ev="Welcome back screen before the action; hosted Sign in page; execution record."),
"VP-APP-SIGNIN-003": dict(
 pre="The user is signed out and the native Welcome back screen is displayed.",
 proc="1. Select Create an account.\n2. Select Sign in in Already have an account? Sign in.",
 exp="1. The native Create your account screen opens with its content displayed.\n2. The Welcome back screen opens again with its content restored.",
 ev="Create your account and Welcome back screenshots or recording; execution record."),
"VP-APP-HOSTED-REG-001": dict(
 pre="Hosted Registration is displayed and the user is signed out.",
 proc=("1. Inspect the page from the GlucoRx logo down to the Region field.\n"
       "2. Inspect the notice below Region, Create an account, Back to sign in and the language selector.\n"
       "3. Open the Region list, then close it without making a selection.\n"
       "4. Open the language list, then close it without making a selection."),
 exp=("1. The page shows Create your account, the required-fields note, Email, Password, Confirm password, Given name(s), Family name(s), Region and two password-visibility controls. Email, Password, Confirm password, Given name(s) and Region are marked required. Family name(s) is not marked required.\n"
      "2. The notice reads: " + NOTICE + " " + D + " It remains unavailable until every required field is complete and valid. Back to sign in and the language selector are shown.\n"
      "3. Region offers United Kingdom and United States and stays empty when closed without a selection.\n"
      "4. The language selector offers " + LANGS + " and the page language is unchanged when it is closed without a selection."),
 ev="Full Hosted Registration page; Region and language lists; execution record."),
"VP-APP-HOSTED-REG-008": dict(
 pre="Hosted Registration is displayed and valid test values are available.",
 proc=("1. Inspect Create an account on the empty form.\n"
       "2. Complete Email, Password, Confirm password, Given name(s) and Region with valid values.\n"
       "3. Clear Email, then restore it.\n"
       "4. Clear Password, then restore it.\n"
       "5. Clear Confirm password, then restore it.\n"
       "6. Clear Given name(s), then restore it.\n"
       "7. Clear Region, then restore it.\n"
       "8. Enter a value in Family name(s), then clear it. Do not create the account."),
 exp=("1. " + D + " No Please specify this field. message is shown on the empty form.\n"
      "2. Create an account becomes available only after all five required fields contain acceptable values.\n"
      "3. Create an account is unavailable while Email is empty and available again when Email is restored.\n"
      "4. Create an account is unavailable while Password is empty and available again when Password is restored.\n"
      "5. Create an account is unavailable while Confirm password is empty and available again when it is restored.\n"
      "6. Create an account is unavailable while Given name(s) is empty and available again when it is restored.\n"
      "7. Create an account is unavailable while Region is empty and available again when it is restored.\n"
      "8. Create an account stays available whether Family name(s) contains a value or is empty."),
 ev="Empty-form action state, each cleared-field state and the completed valid form; execution record."),
}
RUN = {"t": "title", "pre": "preconditions", "proc": "procedure", "exp": "expected", "ev": "evidence"}


def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    cp, rp, hp = OUT / "PRT-0701-cases.json", OUT / "PRT-0701-run_order.json", OUT / "PRT-0701-Console-source.html"
    cases, order = load(cp), load(rp)
    before = ([r["id"] for r in cases], [r["id"] for r in order])
    for rows, run in ((cases, False), (order, True)):
        seen = set()
        for r in rows:
            if r["id"] in U:
                for k, v in U[r["id"]].items():
                    r[RUN[k] if run else k] = v
                seen.add(r["id"])
        if seen != set(U):
            raise RuntimeError(f"missing {set(U) - seen}")
    if before != ([r["id"] for r in cases], [r["id"] for r in order]):
        raise RuntimeError("case ids changed")
    save(cp, cases)
    save(rp, order)
    html = hp.read_text(encoding="utf-8-sig")
    emb = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html, n = re.compile(r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)", re.S).subn(
        lambda m: m.group(1) + emb + m.group(2), html, count=1)
    if n != 1:
        raise RuntimeError("embedded case list not found")
    hp.write_text(html, encoding="utf-8")
    shutil.copy2(hp, ROOT / "PRT-0701-Console-source.updated.html")
    for name in ("PRT-0701-cases.json", "PRT-0701-run_order.json", "PRT-0701-Console-source.html"):
        shutil.copy2(OUT / name, LATEST / name)
    shutil.copy2(hp, LATEST / "PRT-0701-Console-source.updated.html")
    print("ok")


if __name__ == "__main__":
    main()
