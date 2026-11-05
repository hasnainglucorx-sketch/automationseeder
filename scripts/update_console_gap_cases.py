"""Build updated PRT-0701 console artifacts with seeded and manual gap cases."""
import json
from pathlib import Path


SOURCE = Path(r"C:\Users\Hasnain\Downloads")
OUT = Path(__file__).resolve().parents[1] / "output" / "console-update"

SEEDED_ID = "VP-APP-REPORT-DAY-004"
MANUAL_ID = "VP-APP-REPORT-DAY-005"

SEEDED_TITLE = "Break Day graph across an approved backend-seeded data gap"
SEEDED_PRE = (
    "Quality/Test Engineering approval for backend-seeded data is recorded before execution. "
    "Non-production QA environment only. Controlled Test Data: account "
    "rekod43112@maxtanie.com; report date 1 October 2026; Reports > Day; use the 24 Hours "
    "view when the interval is in range, otherwise navigate Day to the recorded date; no readings "
    "from 07:23 through 08:07 PKT; API reading immediately before the gap at 07:22 PKT = "
    "125.45 mg/dL; API reading immediately after the gap at 08:08 PKT = 128.16 mg/dL. "
    "The controlled backend read-back confirms zero readings inside the interval. Record any "
    "whole-number rounding shown by the app. The account is synchronized on the test device. "
    "Do not record the account password in the protocol."
)
SEEDED_PROC = (
    "1. Record the Quality/Test Engineering approval reference and the controlled Test Data values.\n"
    "2. Sign in with the controlled account and allow server data to synchronize.\n"
    "3. Open Reports > Day and navigate to 1 October 2026.\n"
    "4. Use the 24 Hours view where available and locate 07:22 through 08:08 PKT.\n"
    "5. Verify the readings immediately before and after the interval against Test Data.\n"
    "6. Inspect the glucose line immediately before, across and after the missing-data interval."
)
SEEDED_EXP = (
    "1. The approval and controlled Test Data reference are recorded.\n"
    "2. The readings surrounding the gap appear at their recorded times and values, subject only "
    "to the app's controlled display rounding.\n"
    "3. A visible line break is present across 07:23 through 08:07 PKT.\n"
    "4. The graph does not interpolate or imply a continuous glucose trend across the gap.\n"
    "5. Data from another account or session is not joined to the fixture."
)
SEEDED_EVIDENCE = (
    "Quality/Test Engineering approval reference; controlled Test Data record; backend read-back "
    "verification; Day graph screenshot showing the gap and surrounding timestamps; execution record."
)

MANUAL_TITLE = "Break Day graph across a manually created real-device data gap"
MANUAL_PRE = (
    "A physical sensor/transmitter session is active and producing normal readings. Controlled "
    "Test Data records the test-account alias, sensor/transmitter/session identifier, expected "
    "reading frequency, approved out-of-range interruption method and intended interruption start "
    "time. Use one of these acceptance paths: (A) at least five consecutive measurement indexes "
    "remain missing after reconnection and are not backfilled; or (B) the timestamps surrounding "
    "the gap are more than 30 minutes apart. Record the last valid reading value/time/index before "
    "interruption and the first valid reading value/time/index after reconnection. No backend reading "
    "is created, deleted or changed for this case."
)
MANUAL_PROC = (
    "1. Wait for a normal reading and record its value, timestamp, session identifier and measurement "
    "index where available.\n"
    "2. Move the phone outside reliable Bluetooth range using the approved normal-device method.\n"
    "3. Keep reception interrupted for at least five expected reading intervals.\n"
    "4. Restore communication and wait for the first valid reading after reconnection.\n"
    "5. Record its value, timestamp, session identifier and measurement index where available.\n"
    "6. Confirm whether the expected measurement indexes remain missing or were backfilled.\n"
    "7. If readings were backfilled or missing indexes cannot be demonstrated, repeat with an "
    "interruption that produces a time gap exceeding 30 minutes.\n"
    "8. Open Reports > Day, navigate to the documented date and locate the interruption.\n"
    "9. Inspect the glucose line immediately before, across and after the interval."
)
MANUAL_EXP = (
    "1. Valid readings exist before and after the interruption.\n"
    "2. Either at least five consecutive measurement indexes remain missing, or the timestamps "
    "surrounding the gap are more than 30 minutes apart.\n"
    "3. The Day graph contains a visible line break across the documented discontinuity.\n"
    "4. The graph does not interpolate or imply a continuous glucose trend across the interval.\n"
    "5. Normal graphing resumes when valid readings resume. If the five missed readings are "
    "backfilled and no greater-than-30-minute gap is produced, record the attempt as unsuitable "
    "test data rather than Pass."
)
MANUAL_EVIDENCE = (
    "Controlled Test Data record; reading before interruption; interruption start/end times and "
    "method; missing-index evidence or timestamps proving a gap exceeding 30 minutes; first reading "
    "after reconnection; Day graph screenshot; execution record."
)


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_cases():
    cases = json.loads((SOURCE / "PRT-0701-cases.json").read_text(encoding="utf-8"))
    cases = [case for case in cases if case.get("id") != MANUAL_ID]
    index = next(i for i, case in enumerate(cases) if case.get("id") == SEEDED_ID)
    seeded = cases[index]
    seeded.update(t=SEEDED_TITLE, method="Manual - Real Device · Controlled QA backend fixture",
                  req="DI-44 / DO-689", pre=SEEDED_PRE, proc=SEEDED_PROC,
                  exp=SEEDED_EXP, ev=SEEDED_EVIDENCE)
    manual = {
        "r": seeded["r"] + 1,
        "sec": seeded["sec"],
        "id": MANUAL_ID,
        "t": MANUAL_TITLE,
        "method": "Manual - Real Device",
        "req": "DI-44 / DO-689",
        "pre": MANUAL_PRE,
        "proc": MANUAL_PROC,
        "exp": MANUAL_EXP,
        "ev": MANUAL_EVIDENCE,
    }
    cases.insert(index + 1, manual)
    for number, case in enumerate(cases, 1):
        case["r"] = number
    write_json("PRT-0701-cases.json", cases)
    return cases


def update_run_order():
    rows = json.loads((SOURCE / "PRT-0701-run_order.json").read_text(encoding="utf-8"))
    rows = [row for row in rows if row.get("id") != MANUAL_ID]
    index = next(i for i, row in enumerate(rows) if row.get("id") == SEEDED_ID)
    seeded = rows[index]
    seeded.update(title=SEEDED_TITLE, requirement="DI-44 → DO-689",
                  preconditions=SEEDED_PRE, procedure=SEEDED_PROC,
                  expected=SEEDED_EXP, evidence=SEEDED_EVIDENCE, est="10")
    manual = {
        "run": seeded["run"] + 1,
        "day": seeded["day"],
        "phase": seeded["phase"],
        "id": MANUAL_ID,
        "recovery": seeded["recovery"],
        "est": "45",
        "section": seeded["section"],
        "title": MANUAL_TITLE,
        "requirement": "DI-44 → DO-689",
        "preconditions": MANUAL_PRE,
        "procedure": MANUAL_PROC,
        "expected": MANUAL_EXP,
        "evidence": MANUAL_EVIDENCE,
    }
    rows.insert(index + 1, manual)
    for number, row in enumerate(rows, 1):
        row["run"] = number
    write_json("PRT-0701-run_order.json", rows)
    return rows


def update_appendix():
    rows = json.loads((SOURCE / "PRT-0701-appendixC.json").read_text(encoding="utf-8"))
    rows = [row for row in rows if MANUAL_ID not in row]
    index = next(i for i, row in enumerate(rows) if SEEDED_ID in row)
    seeded = rows[index]
    manual = ["0", seeded[1], seeded[2], MANUAL_ID, seeded[4], "45"]
    rows.insert(index + 1, manual)
    for number, row in enumerate(rows, 1):
        row[0] = str(number)
    write_json("PRT-0701-appendixC.json", rows)
    return rows


def update_html(cases):
    html = (SOURCE / "PRT-0701-Console-source.html").read_text(encoding="utf-8")
    if not html.lstrip().lower().startswith("<meta charset="):
        html = '<meta charset="utf-8">\n' + html
    old_loader = '''  // ---------------- Load case data ----------------
  fetch("PRT-0701-cases.json").then(function(r){ return r.json(); }).then(function(data){
    CASES = data;
    CASES.forEach(function(c){ byId[c.id] = c; });
    init();
  }).catch(function(err){
    document.getElementById("list").innerHTML = "<div id='empty'>Could not load the case list.<br>" + esc(err.message||err) + "</div>";
  });'''
    alternate_loader = old_loader.replace('fetch("PRT-0701-cases.json")', 'fetch("cases.json")')
    embedded = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    new_loader = f'''  // ---------------- Load case data ----------------
  // Embedded so the console also works when opened directly through file://.
  var EMBEDDED_CASES = {embedded};

  function startWithCases(data){{
    CASES = data;
    CASES.forEach(function(c){{ byId[c.id] = c; }});
    init();
  }}

  if (window.location.protocol === "file:"){{
    startWithCases(EMBEDDED_CASES);
  }} else {{
    fetch("PRT-0701-cases.json").then(function(r){{
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }}).then(startWithCases).catch(function(err){{
      console.warn("Using embedded case data", err);
      startWithCases(EMBEDDED_CASES);
    }});
  }}'''
    if old_loader in html:
        html = html.replace(old_loader, new_loader, 1)
    elif alternate_loader in html:
        html = html.replace(alternate_loader, new_loader, 1)
    else:
        raise RuntimeError("Could not locate the console case-data loader")
    (OUT / "PRT-0701-Console-source.html").write_text(html, encoding="utf-8")


def validate(cases, run_order, appendix):
    assert len(cases) == 440 and len(run_order) == 479 and len(appendix) == 479
    assert sum(case.get("id") == SEEDED_ID for case in cases) == 1
    assert sum(case.get("id") == MANUAL_ID for case in cases) == 1
    assert sum(row.get("id") == SEEDED_ID for row in run_order) == 1
    assert sum(row.get("id") == MANUAL_ID for row in run_order) == 1
    assert sum(MANUAL_ID in row for row in appendix) == 1
    assert [case["r"] for case in cases] == list(range(1, len(cases) + 1))
    assert [row["run"] for row in run_order] == list(range(1, len(run_order) + 1))
    assert [int(row[0]) for row in appendix] == list(range(1, len(appendix) + 1))
    for name in ("PRT-0701-cases.json", "PRT-0701-run_order.json", "PRT-0701-appendixC.json"):
        json.loads((OUT / name).read_text(encoding="utf-8"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = update_cases()
    run_order = update_run_order()
    appendix = update_appendix()
    update_html(cases)
    validate(cases, run_order, appendix)
    print(json.dumps({"cases": len(cases), "run_order": len(run_order),
                      "appendixC": len(appendix), "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
