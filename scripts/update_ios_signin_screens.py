"""Update native Sign In (Welcome back) and hosted Sign In cases from the iOS screenshots (version 1.0.4 (202609301))."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
LATEST = ROOT / "Claude-Handoff-2026-10-02" / "latest"

# compact-case keys: t, pre, proc, exp, ev
U = {
"VP-APP-SIGNIN-001": dict(
 t="Welcome back screen content",
 pre="User is signed out and the native Welcome back screen is displayed.",
 proc="1. Inspect the complete screen from top to bottom.\n2. Compare the image, text, controls and version with the approved iOS reference.",
 exp=("1. The screen shows the lifestyle image, CGMx 1 logo, the Welcome back heading and Sign in to pick up where you left off.\n"
      "2. Sign in and Forgot your password? are shown.\n"
      "3. The security card reads Your health data is protected and Your information is encrypted in transit and at rest.\n"
      "4. New to Modus? Create an account and the app version are shown. The reference version is Version 1.0.4 (202609301).\n"
      "5. No content is missing, duplicated, clipped, overlapping or corrupted."),
 ev="Full screen compared with the approved iOS reference; displayed version; execution record"),
"VP-APP-SIGNIN-002": dict(
 exp=("1. The native Welcome back screen opens.\n"
      "2. The hosted GlucoRx Sign in page opens in the in-app browser with Email and Password fields, without a blank page, crash or native credential form.")),
"VP-APP-SIGNIN-003": dict(
 t="Navigate between Welcome back and Create your account screens",
 proc=("1. Launch CGMx 1 to reach the Welcome back screen.\n"
       "2. Select Create an account.\n"
       "3. Select Sign in in Already have an account? Sign in."),
 exp=("1. CGMx 1 opens on the native Welcome back screen.\n"
      "2. The native Create your account screen opens with its content displayed.\n"
      "3. The Welcome back screen opens again with its content restored.")),
"VP-APP-HOSTED-SIGNIN-001": dict(
 exp=("1. The page shows GlucoRx branding, the Sign in heading and Welcome back. Use your GlucoRx account to continue.\n"
      "2. Email and Password are marked required. Email shows the placeholder you@example.com. Password has a visibility (eye) control and Forgot password? is shown beside its label.\n"
      "3. A Sign in button and New to GlucoRx? Create an account are shown below the fields.\n"
      "4. The language selector offers English (UK), English (US), Cymraeg, العربية and Español.\n"
      "5. All content is readable and no control is missing, duplicated, clipped or corrupted.")),
}
# run_order cases start from the Welcome back screen instead of launching the app
R = {
"VP-APP-SIGNIN-002": dict(
 pre="Start: the native Welcome back screen is displayed (from Welcome: tap Sign in). The user is signed out. Internet is available.",
 exp="1. The hosted GlucoRx Sign in page opens in the in-app browser with Email and Password fields, without a blank page, crash or native credential form."),
"VP-APP-SIGNIN-003": dict(
 pre="Start: the native Welcome back screen is displayed (from Welcome: tap Sign in). The user is signed out.",
 proc="1. Select Create an account.\n2. Select Sign in in Already have an account? Sign in.",
 exp="1. The native Create your account screen opens with its content displayed.\n2. The Welcome back screen opens again with its content restored."),
}
RUN = {"t": "title", "pre": "preconditions", "proc": "procedure", "exp": "expected", "ev": "evidence"}


def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    cp, rp, hp = OUT / "PRT-0701-cases.json", OUT / "PRT-0701-run_order.json", OUT / "PRT-0701-Console-source.html"
    cases, order = load(cp), load(rp)
    for rows, run in ((cases, False), (order, True)):
        seen = set()
        for r in rows:
            if r["id"] in U:
                for k, v in {**U[r["id"]], **(R.get(r["id"], {}) if run else {})}.items():
                    r[RUN[k] if run else k] = v
                seen.add(r["id"])
        if seen != set(U):
            raise RuntimeError("missing cases")
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
    shutil.copy2(Path(__file__), LATEST.parent / "scripts" / Path(__file__).name)
    print("ok")


if __name__ == "__main__":
    main()
