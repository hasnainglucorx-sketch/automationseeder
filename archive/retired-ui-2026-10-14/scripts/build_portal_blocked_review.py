"""Build the live review register for the 142 blocked execution-report rows."""

from __future__ import annotations

import json
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "output" / "portal-fixtures" / "execution-report-blocked-142.json"
PLAN = ROOT / "output" / "portal-fixtures" / "blocked-case-status.json"
CASES = ROOT / "output" / "console-update" / "PRT-0702-cases.json"
OUTPUT = ROOT / "output" / "portal-fixtures" / "blocked-case-review.json"


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))["cases"]
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    current = {
        case["id"]: case
        for case in json.loads(CASES.read_text(encoding="utf-8"))
    }
    rewritten: set[str] = set()
    for script in (
        "rewrite_portal_blocked_batch1.py",
        "rewrite_portal_blocked_batch2.py",
        "rewrite_portal_blocked_batch3.py",
    ):
        rewritten.update(
            runpy.run_path(str(ROOT / "scripts" / script))["UPDATES"].keys()
        )
    planned_status = {
        case_id: group["status"]
        for group in plan["groups"]
        for case_id in group["case_ids"]
    }
    rows = []
    for item in report:
        case_id = item["id"]
        if case_id in rewritten:
            status = "rewritten_fixture_ready"
        elif case_id not in current:
            status = "superseded_absent_from_current_protocol"
        else:
            status = planned_status.get(case_id, "review_pending")
        rows.append(
            {
                **item,
                "current_title": current.get(case_id, {}).get("t"),
                "current_protocol_present": case_id in current,
                "review_status": status,
            }
        )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["review_status"]] = counts.get(row["review_status"], 0) + 1
    payload = {"blocked_count": len(rows), "status_counts": counts, "cases": rows}
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
