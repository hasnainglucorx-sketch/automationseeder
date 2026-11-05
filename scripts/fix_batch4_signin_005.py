"""Batch 4 (Native Sign In): restructure VP-APP-SIGNIN-005 to the CLAUDE.md case structure.
Evidence: X (close) control at the top left of the in-app browser is visible in the iOS hosted-page screenshots.
Offline error wording is not verified, so the case asks the tester to record the exact text. Loads the latest files at run time."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
LATEST = ROOT / "Claude-Handoff-2026-10-02" / "latest"

ID = "VP-APP-SIGNIN-005"
NEW = dict(
 t="Hosted sign-in with no internet and recovery",
 pre="The user is signed out, the native Welcome back screen is displayed and internet is available.",
 proc=("1. Turn Airplane mode on and make sure Wi-Fi is off.\n"
       "2. Select Sign in on the Welcome back screen.\n"
       "3. Select the X (close) button at the top left of the in-app browser.\n"
       "4. Turn Airplane mode off and wait until Wi-Fi or mobile data is connected.\n"
       "5. Select Sign in again."),
 exp=("1. The device has no internet connection.\n"
      "2. Sign-in does not complete. The in-app browser shows a loading or connection error; record the exact text shown.\n"
      "3. The in-app browser closes and the Welcome back screen is shown. The user is still signed out.\n"
      "4. The device is connected and the Welcome back screen is still shown.\n"
      "5. The hosted GlucoRx Sign in page opens with Email and Password fields, without a blank page, crash or duplicate page."),
 ev="Offline error screenshot with the exact text; Welcome back screen after closing; hosted Sign in page after recovery; execution record.")
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
        hits = [r for r in rows if r["id"] == ID]
        if len(hits) != 1:
            raise RuntimeError(f"{ID} found {len(hits)} times")
        for k, v in NEW.items():
            hits[0][RUN[k] if run else k] = v
    if before != ([r["id"] for r in cases], [r["id"] for r in order]):
        raise RuntimeError("ids changed")
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
