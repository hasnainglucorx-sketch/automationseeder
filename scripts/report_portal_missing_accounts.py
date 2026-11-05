"""Report every PRT-0702 case blocked by an unprovisioned login account."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "output" / "PRT-0702-case-by-case-report.json"
CATALOG_PATH = ROOT / "output" / "portal-test-assets.json"
MD_PATH = ROOT / "output" / "PRT-0702-missing-account-inspection.md"
CSV_PATH = ROOT / "output" / "PRT-0702-missing-account-inspection.csv"
JSON_PATH = ROOT / "output" / "PRT-0702-missing-account-inspection.json"


def split_refs(value: str) -> list[str]:
    return [] if not value or value == "None" else [part.strip() for part in value.split(",")]


def main() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    accounts = {row["reference"]: row for row in catalog.get("accounts", [])}
    blocked_rows = []
    alias_cases: dict[str, list[str]] = defaultdict(list)

    for row in report["cases"]:
        missing = [
            alias for alias in split_refs(row["accounts"])
            if accounts.get(alias, {}).get("availability") not in {"Configured", "Verified fixture"}
        ]
        if not missing:
            continue
        for alias in missing:
            alias_cases[alias].append(row["id"])
        blocked_rows.append({
            "run": row["run"],
            "case_id": row["id"],
            "section": row["section"],
            "missing_login_accounts": ", ".join(missing),
            "also_missing_test_asset": "Yes" if "TEST ASSET" in row["status"] else "No",
            "other_blockers": row["blockers"],
        })

    alias_counts = Counter({alias: len(cases) for alias, cases in alias_cases.items()})
    summary = {
        "protocol": "PRT-0702",
        "review_date": report["review_date"],
        "cases_inspected": len(report["cases"]),
        "cases_blocked_by_missing_login_account": len(blocked_rows),
        "account_only": sum(1 for row in blocked_rows if row["also_missing_test_asset"] == "No"),
        "account_and_test_asset": sum(1 for row in blocked_rows if row["also_missing_test_asset"] == "Yes"),
        "missing_login_aliases": len(alias_counts),
        "aliases": [
            {
                "reference": alias,
                "purpose": accounts.get(alias, {}).get("purpose", ""),
                "availability": accounts.get(alias, {}).get("availability", "Not catalogued"),
                "affected_cases": count,
                "case_ids": alias_cases[alias],
            }
            for alias, count in alias_counts.most_common()
        ],
        "cases": blocked_rows,
    }
    JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(blocked_rows[0]))
        writer.writeheader()
        writer.writerows(blocked_rows)

    out = [
        "# PRT-0702 — missing login-account inspection",
        "",
        f"Review date: {report['review_date']}",
        "",
        f"All **{len(report['cases'])}** Web Portal test cases were checked. **{len(blocked_rows)}** cases require at least one login account that is not configured in Run Setup.",
        "",
        f"- Account blocker only: **{summary['account_only']}**",
        f"- Account and separate Test Asset blocker: **{summary['account_and_test_asset']}**",
        f"- Distinct missing login aliases: **{len(alias_counts)}**",
        "",
        "Clinic, clinic-application, staff-member, transfer, and successor aliases classified as data fixtures are excluded from login-account blockers.",
        "",
        "## Missing login aliases",
        "",
        "| Login alias | Purpose | Availability | Affected cases |",
        "|---|---|---|---:|",
    ]
    for alias, count in alias_counts.most_common():
        item = accounts.get(alias, {})
        out.append(f"| {alias} | {item.get('purpose', '')} | {item.get('availability', 'Not catalogued')} | {count} |")
    out.extend([
        "",
        "## Case-by-case inspection",
        "",
        "| Run | Case | Section | Missing login account(s) | Separate Test Asset blocker |",
        "|---:|---|---|---|---|",
    ])
    for row in blocked_rows:
        out.append(
            f"| {row['run']} | {row['case_id']} | {row['section']} | "
            f"{row['missing_login_accounts']} | {row['also_missing_test_asset']} |"
        )
    MD_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "cases_inspected", "cases_blocked_by_missing_login_account", "account_only",
        "account_and_test_asset", "missing_login_aliases"
    )}, indent=2))


if __name__ == "__main__":
    main()
