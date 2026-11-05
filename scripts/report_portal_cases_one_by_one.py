"""Create a human-readable, case-by-case readiness report for PRT-0702."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "output" / "console-update" / "PRT-0702-cases.json"
CATALOG_PATH = ROOT / "output" / "portal-test-assets.json"
MD_PATH = ROOT / "output" / "PRT-0702-case-by-case-report.md"
CSV_PATH = ROOT / "output" / "PRT-0702-case-by-case-report.csv"
JSON_PATH = ROOT / "output" / "PRT-0702-case-by-case-report.json"


def step_count(text: str) -> int:
    return len(re.findall(r"(?m)^\d+\.\s", text or ""))


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    accounts = {row["reference"]: row for row in catalog.get("accounts", [])}
    resources = {row["reference"]: row for row in catalog.get("resources", [])}
    rows = []

    for case in cases:
        text = " ".join(str(case.get(k, "")) for k in ("t", "pre", "proc", "exp", "ev"))
        aliases = sorted(set(re.findall(r"\bQA-PORTAL-[A-Z0-9-]+\b", text)))
        login_aliases = [a for a in aliases if accounts.get(a, {}).get("kind", "login account") == "login account"]
        record_aliases = [a for a in aliases if accounts.get(a, {}).get("kind") == "data fixture"]
        asset_refs = sorted({v.rstrip(".") for v in re.findall(
            r"Portal Test Assets\s*>\s*([A-Z0-9.-]+)", text, re.I
        )})
        missing_accounts = [
            alias for alias in login_aliases
            if accounts.get(alias, {}).get("availability") not in {"Configured", "Verified fixture"}
        ]
        unresolved_assets = [
            ref for ref in asset_refs
            if resources.get(ref, {}).get("availability") != "Embedded in console"
        ]
        unresolved_records = [
            alias for alias in record_aliases
            if accounts.get(alias, {}).get("availability") not in {"Configured", "Verified fixture"}
        ]
        unresolved_assets = sorted(set(unresolved_assets + unresolved_records))

        content_findings = []
        pc, ec = step_count(case.get("proc", "")), step_count(case.get("exp", ""))
        if pc != ec:
            content_findings.append(f"Procedure/expected steps differ ({pc}/{ec})")
        if re.search(r"\bQA_WEB_|\bTD-", text):
            content_findings.append("Legacy reference remains")
        if re.search(r"\brecorded\b", text, re.I):
            content_findings.append("Disallowed wording remains")
        if "All case-specific data and resource states" in text:
            content_findings.append("Vague Test Assets wording remains")
        if not case.get("pre", "").strip():
            content_findings.append("Missing precondition")
        if not case.get("proc", "").strip():
            content_findings.append("Missing procedure")
        if not case.get("exp", "").strip():
            content_findings.append("Missing expected result")

        traceability = "Mapped"
        if "gap:" in case.get("req", "").lower() or "(gap" in case.get("req", "").lower():
            traceability = "Requirement gap identified"
        if re.search(r"FORMAL / EXTERNAL EVIDENCE|\[Record\]|supporting check", text, re.I):
            traceability = "Formal evidence or requirement review"

        manual_setup = []
        for phrase, label in (
            ("tester mailbox", "tester mailbox"),
            ("Requestly", "Requestly / browser interception"),
            ("Developer Tools", "browser Developer Tools"),
            ("responsive browser viewport", "responsive viewport"),
            ("download folder", "empty download folder"),
            ("approved test authenticator", "test authenticator"),
        ):
            if phrase.lower() in text.lower():
                manual_setup.append(label)

        if content_findings:
            status = "CONTENT REVIEW REQUIRED"
        elif missing_accounts and unresolved_assets:
            status = "BLOCKED — ACCOUNT AND TEST ASSET"
        elif missing_accounts:
            status = "BLOCKED — ACCOUNT"
        elif unresolved_assets:
            status = "BLOCKED — TEST ASSET"
        elif manual_setup:
            status = "READY — MANUAL SETUP"
        else:
            status = "READY"

        blockers = []
        if missing_accounts:
            blockers.append("Provision account(s): " + ", ".join(missing_accounts))
        if unresolved_assets:
            blockers.append("Supply controlled value(s): " + ", ".join(unresolved_assets))
        rows.append({
            "run": case.get("r"),
            "id": case["id"],
            "section": case.get("sec", ""),
            "title": case.get("t", ""),
            "status": status,
            "content_check": "PASS" if not content_findings else "REVIEW",
            "traceability": traceability,
            "procedure_steps": pc,
            "expected_steps": ec,
            "accounts": ", ".join(login_aliases) or "None",
            "record_fixtures": ", ".join(record_aliases) or "None",
            "test_assets": ", ".join(asset_refs) or "None",
            "manual_setup": ", ".join(manual_setup) or "None",
            "blockers": "; ".join(blockers) or "None",
            "content_findings": "; ".join(content_findings) or "None",
        })

    status_counts = Counter(row["status"] for row in rows)
    trace_counts = Counter(row["traceability"] for row in rows)
    report = {
        "protocol": "PRT-0702",
        "review_date": "2026-10-12",
        "cases_reviewed": len(rows),
        "status_counts": dict(status_counts),
        "traceability_counts": dict(trace_counts),
        "cases": rows,
    }
    JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    sections: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        sections[row["section"]].append(row)
    out = [
        "# PRT-0702 Web Portal — case-by-case review",
        "",
        "Review date: 2026-10-12",
        "",
        f"Cases checked individually: **{len(rows)}**.",
        "",
        "## Execution-readiness summary",
        "",
        "| Status | Cases |",
        "|---|---:|",
    ]
    out.extend(f"| {status} | {count} |" for status, count in sorted(status_counts.items()))
    out.extend([
        "",
        "A content check of PASS means the case has a precondition, numbered procedure and matching numbered expected results, and contains no legacy QA_WEB/TD references or vague catch-all Test Assets sentence. Execution can still be blocked by an unprovisioned account or a controlled Test Asset whose value is not embedded in the console.",
        "",
    ])
    for section, section_rows in sections.items():
        out.extend([
            f"## {section}",
            "",
            "| # | Case | Status | Content | Login accounts | Record fixtures | Test Assets | Blocker / setup |",
            "|---:|---|---|---|---|---|---|---|",
        ])
        for row in section_rows:
            blocker = row["blockers"] if row["blockers"] != "None" else row["manual_setup"]
            out.append(
                f"| {row['run']} | {row['id']} | {row['status']} | {row['content_check']} | "
                f"{row['accounts']} | {row['record_fixtures']} | {row['test_assets']} | {blocker} |"
            )
        out.append("")
    MD_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases_reviewed": len(rows),
        "status_counts": dict(status_counts),
        "content_review_required": sum(row["content_check"] != "PASS" for row in rows),
        "markdown": str(MD_PATH),
        "csv": str(CSV_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()
