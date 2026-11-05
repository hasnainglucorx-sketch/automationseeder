"""Document the earlier set of 71 blocked cases that were remediated or executed."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "output" / "portal-fixtures" / "blocked-case-review.json"
OUTPUT = ROOT / "output" / "PRT-0702-earlier-71-resolved-blocked-cases.md"

EXECUTED = {
    "HCP-LIST-004": "Executed — FAIL",
    "HCP-DATA-019": "Executed — PASS",
    "HCP-PROFILE-UPDATE-003": "Executed — FAIL",
    "HCP-PROFILE-UPDATE-005": "Executed — PASS with separate Save defect",
    "HCP-PROFILE-UPDATE-006": "Executed — PASS with separate Save defect",
    "HCP-PROFILE-UPDATE-008": "Executed — blocked by product defect",
    "HCP-PROFILE-UPDATE-009": "Executed — PASS",
    "HCP-PROFILE-UPDATE-010": "Executed — FAIL",
}


def main() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    rewritten = [
        row["id"] for row in review["cases"]
        if row["review_status"] == "rewritten_fixture_ready"
    ]
    resolved = rewritten + list(EXECUTED)
    if len(rewritten) != 63 or len(resolved) != 71 or len(set(resolved)) != 71:
        raise RuntimeError(
            f"Expected 63 rewritten plus 8 executed unique cases; got "
            f"{len(rewritten)} + {len(EXECUTED)} ({len(set(resolved))} unique)"
        )
    out = [
        "# PRT-0702 — earlier 71 blocked cases remediated",
        "",
        "This is the earlier cumulative count. It consists of 63 cases whose test definitions were rewritten with usable fixture steps and 8 previously blocked cases that were executed and assigned an actual result.",
        "",
        "## 63 rewritten cases",
        "",
    ]
    out.extend(f"- `{case_id}`" for case_id in rewritten)
    out.extend(["", "## 8 executed cases", ""])
    out.extend(f"- `{case_id}` — {result}" for case_id, result in EXECUTED.items())
    OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(json.dumps({"rewritten": len(rewritten), "executed": len(EXECUTED), "total": len(resolved), "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
