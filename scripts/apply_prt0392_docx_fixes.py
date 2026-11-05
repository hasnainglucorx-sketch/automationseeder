"""Apply the PRT-0392 docx reconciliation to PRT-0701-cases.json and
PRT-0701-run_order.json.

- Updates ONLY the fields that differ, for the exact case IDs in the diff
  report (output/console-update/PRT-0392-docx-diff-report.json).
- Adds the two new cases found only in the docx (VP-APP-SETUP-GUIDE-001/002)
  as NEW entries, appended at the end of the run order with fresh run
  numbers so no existing case's run number changes (an execution is in
  progress against the current run-order sequence).
- Loads files fresh at execution time. Fails loudly if an expected id is
  missing. Writes UTF-8 JSON with the same formatting style as the source.
"""
import json

BASE = r"C:\Users\Hasnain\Downloads\Automation seeder\output\console-update"
COMPACT_PATH = f"{BASE}\\PRT-0701-cases.json"
RUN_ORDER_PATH = f"{BASE}\\PRT-0701-run_order.json"
DIFF_PATH = f"{BASE}\\PRT-0392-docx-diff-report.json"
EXTRACT_PATH = f"{BASE}\\PRT-0392-docx-extract.json"

RUN_ORDER_FIELD = {
    "title": "title",
    "requirement": "requirement",
    "preconditions": "preconditions",
    "procedure": "procedure",
    "expected": "expected",
}
COMPACT_FIELD = {
    "title": "t",
    "requirement": "req",
    "preconditions": "pre",
    "procedure": "proc",
    "expected": "exp",
}

NEW_SECTION = "24-Step Setup - Setup Guide"
NEW_DAY = "Day 4"
NEW_PHASE = "Phase 3"
NEW_METHOD = "Manual - Real Device"
NEW_RECOVERY = "R3"
NEW_CASE_META = {
    "VP-APP-SETUP-GUIDE-001": {
        "est": "10",
        "evidence": (
            "Screenshots of each guide step shown in steps 1, 3 and 4-6; "
            "network state before/after airplane mode; execution record."
        ),
    },
    "VP-APP-SETUP-GUIDE-002": {
        "est": "12",
        "evidence": (
            "Screenshots of each of the 11 sensor-setup steps with their "
            "step counters; TRANSMITTER card state before and after; "
            "execution record."
        ),
    },
}
NEW_CASES = list(NEW_CASE_META.keys())


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    diff_report = load(DIFF_PATH)
    extract = {c["id"]: c for c in load(EXTRACT_PATH)}
    compact = load(COMPACT_PATH)
    run_order = load(RUN_ORDER_PATH)

    compact_by_id = {c["id"]: c for c in compact}
    run_order_by_id = {c["id"]: c for c in run_order}

    changed_ids = sorted(diff_report["diffs"].keys())
    missing = [cid for cid in changed_ids if cid not in compact_by_id or cid not in run_order_by_id]
    if missing:
        raise SystemExit(f"FATAL: missing ids in one of the JSON files: {missing}")

    applied = {}
    for cid in changed_ids:
        fields_changed = list(diff_report["diffs"][cid].keys())
        src = extract[cid]
        ro_case = run_order_by_id[cid]
        co_case = compact_by_id[cid]
        for field in fields_changed:
            new_val = src[field]
            ro_case[RUN_ORDER_FIELD[field]] = new_val
            co_case[COMPACT_FIELD[field]] = new_val
        applied[cid] = fields_changed

    # --- new cases ---
    max_run = max(c["run"] for c in run_order)
    max_r = max(c["r"] for c in compact)
    added = []
    for cid in NEW_CASES:
        src = extract[cid]
        meta = NEW_CASE_META[cid]
        max_run += 1
        max_r += 1
        run_order.append({
            "run": max_run,
            "day": NEW_DAY,
            "phase": NEW_PHASE,
            "id": cid,
            "recovery": NEW_RECOVERY,
            "est": meta["est"],
            "section": NEW_SECTION,
            "title": src["title"],
            "requirement": src["requirement"],
            "preconditions": src["preconditions"],
            "procedure": src["procedure"],
            "expected": src["expected"],
            "evidence": meta["evidence"],
        })
        compact.append({
            "r": max_r,
            "sec": NEW_SECTION,
            "id": cid,
            "t": src["title"],
            "method": NEW_METHOD,
            "req": src["requirement"],
            "pre": src["preconditions"],
            "proc": src["procedure"],
            "exp": src["expected"],
            "ev": meta["evidence"],
        })
        added.append(cid)

    save(RUN_ORDER_PATH, run_order)
    save(COMPACT_PATH, compact)

    print(f"Updated fields for {len(applied)} existing cases:")
    for cid, fields in applied.items():
        print(f"  {cid}: {fields}")
    print(f"\nAdded {len(added)} new cases: {added}")
    print(f"\nFinal counts: compact={len(compact)} run_order={len(run_order)}")


if __name__ == "__main__":
    main()
