"""Reconcile PRT-0701 compact/run_order JSON against the PRT-0392 docx (latest version).
Reload-at-execution, fail if an expected ID is missing, update only intended fields,
write UTF-8 JSON, re-embed via generate_unified_console.py afterward.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
COMPACT_PATH = OUT / "PRT-0701-cases.json"
RUNORDER_PATH = OUT / "PRT-0701-run_order.json"
DIFF_REPORT = Path(r"C:\Users\Hasnain\AppData\Local\Temp\claude\C--Users-Hasnain-Downloads-Automation-seeder\59053f2d-91e8-442a-b7c1-a164e851e4a9\scratchpad\docx_review\diff_report.json")
DOCX_CASES = Path(r"C:\Users\Hasnain\AppData\Local\Temp\claude\C--Users-Hasnain-Downloads-Automation-seeder\59053f2d-91e8-442a-b7c1-a164e851e4a9\scratchpad\docx_review\docx_cases.json")

PRE_UPDATE_IDS = {"VP-APP-REMINDER-005", "VP-APP-SECURITY-006"}


def proc_text(steps):
    return "\n".join(steps)


def main():
    compact = json.loads(COMPACT_PATH.read_text(encoding="utf-8-sig"))
    runorder = json.loads(RUNORDER_PATH.read_text(encoding="utf-8-sig"))
    diff_report = json.loads(DIFF_REPORT.read_text(encoding="utf-8"))
    docx_cases = json.loads(DOCX_CASES.read_text(encoding="utf-8"))
    docx_by_id = {c["id"]: c for c in docx_cases}

    compact_by_id = {c["id"]: c for c in compact}
    runorder_by_id = {c["id"]: c for c in runorder}

    changed_ids = []

    for d in diff_report["diffs"]:
        cid = d["id"]
        fields = set(d["fields"])
        if cid not in docx_by_id:
            raise SystemExit(f"ABORT: {cid} not found in docx cases")
        if cid not in compact_by_id or cid not in runorder_by_id:
            raise SystemExit(f"ABORT: {cid} missing from a JSON file")
        dcase = docx_by_id[cid]
        c = compact_by_id[cid]
        o = runorder_by_id[cid]
        touched = False

        if "title" in fields:
            c["t"] = dcase["title"]
            o["title"] = dcase["title"]
            touched = True
        if "proc" in fields:
            c["proc"] = proc_text(dcase["procedure"])
            o["procedure"] = proc_text(dcase["procedure"])
            touched = True
        if "exp" in fields:
            c["exp"] = proc_text(dcase["expected"])
            o["expected"] = proc_text(dcase["expected"])
            touched = True
        if "pre" in fields and cid in PRE_UPDATE_IDS:
            c["pre"] = dcase["precondition"]
            o["preconditions"] = dcase["precondition"]
            touched = True

        if touched:
            changed_ids.append(cid)

    # --- Insert new case VP-APP-TX-PAIR-033 ---
    new_id = "VP-APP-TX-PAIR-033"
    if new_id not in compact_by_id:
        dcase = docx_by_id[new_id]
        anchor_id = "VP-APP-TX-PAIR-032"
        anchor_idx_c = next(i for i, x in enumerate(compact) if x["id"] == anchor_id)
        anchor_idx_o = next(i for i, x in enumerate(runorder) if x["id"] == anchor_id)
        anchor_c = compact[anchor_idx_c]
        anchor_o = runorder[anchor_idx_o]
        new_r = anchor_c["r"] + 1
        new_run = anchor_o["run"] + 1

        new_compact = {
            "r": new_r,
            "sec": anchor_c["sec"],
            "id": new_id,
            "t": dcase["title"],
            "method": "Manual - Real Device",
            "req": dcase["requirements"],
            "pre": dcase["precondition"],
            "proc": proc_text(dcase["procedure"]),
            "exp": proc_text(dcase["expected"]),
            "ev": "Screenshot(s)/recording as applicable; execution record",
        }
        new_runorder = {
            "run": new_run,
            "day": anchor_o["day"],
            "phase": anchor_o["phase"],
            "id": new_id,
            "recovery": anchor_o["recovery"],
            "est": "15",
            "section": anchor_o["section"],
            "title": dcase["title"],
            "requirement": dcase["requirements"],
            "preconditions": dcase["precondition"],
            "procedure": proc_text(dcase["procedure"]),
            "expected": proc_text(dcase["expected"]),
            "evidence": "Screenshot(s)/recording as applicable; execution record",
        }

        for row in compact[anchor_idx_c + 1:]:
            row["r"] += 1
        for row in runorder[anchor_idx_o + 1:]:
            row["run"] += 1

        compact.insert(anchor_idx_c + 1, new_compact)
        runorder.insert(anchor_idx_o + 1, new_runorder)
        changed_ids.append(new_id)

    COMPACT_PATH.write_text(json.dumps(compact, indent=1, ensure_ascii=False), encoding="utf-8")
    RUNORDER_PATH.write_text(json.dumps(runorder, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"Updated {len(set(changed_ids))} case IDs")
    print(sorted(set(changed_ids)))


if __name__ == "__main__":
    main()
