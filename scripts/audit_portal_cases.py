"""Audit every PRT-0702 case and build the console's referenced-asset register.

The audit is deliberately case-by-case.  It removes the old catch-all Test
Assets sentence, keeps every concrete reference visible in the precondition,
and writes a review row for every case so later edits cannot silently leave a
dangling test-data reference.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "output" / "console-update" / "PRT-0702-cases.json"
CATALOG_PATH = ROOT / "output" / "portal-test-assets.json"
REPORT_PATH = ROOT / "output" / "portal-case-content-audit-2026-10-12.json"
ACCOUNTS_PATH = ROOT / ".secrets" / "portal-test-accounts.json"
FIXTURE_PATH = ROOT / "output" / "portal-fixtures" / "fixture-manifest.json"

GENERIC_SENTENCE = "All case-specific data and resource states are available in Portal Test Assets."
ASSET_RE = re.compile(r"Portal Test Assets\s*>\s*([A-Z0-9.-]+)", re.I)
ACCOUNT_RE = re.compile(r"\bQA-PORTAL-[A-Z0-9-]+\b")

PURPOSES = {
    "ACC": "Account identity, role, or lifecycle state",
    "ADMIN": "Administrator lifecycle or permission fixture",
    "A11Y": "Accessibility tool or acceptance criteria",
    "AUDIT": "Approved audit evidence source",
    "CLINIC": "Clinic, application, membership, or invitation fixture",
    "DEVICE": "Device identity or device-status fixture",
    "EVT": "Controlled event fixture",
    "EXT": "External dependency or integration setting",
    "FAULT": "Approved request-failure simulation rule",
    "GLU": "Controlled glucose readings or no-data state",
    "HEALTH": "Platform health response fixture",
    "HCP": "HCP identity, membership, or successor fixture",
    "HELP": "Approved help or support content",
    "INVITE": "Controlled invitation or activation link",
    "KC": "Keycloak policy or session configuration",
    "LOCALE": "Language, locale, or translation fixture",
    "PERF": "Performance measurement threshold or dataset",
    "PERM": "Role and permission expectation",
    "PLATFORM": "Platform aggregate source data",
    "REPORT": "Report generation fixture or passphrase",
    "RUN": "Environment URL, mailbox, browser, or run setting",
    "SHARE": "Patient sharing relationship or limit fixture",
    "TIMEZONE": "Time-zone and daylight-saving fixture",
    "TIR": "Time-in-range calculation fixture",
}

DATA_FIXTURE_ALIASES = {
    "QA-PORTAL-CLINIC-01", "QA-PORTAL-CLINIC-02",
    "QA-PORTAL-CLINICAPP-01", "QA-PORTAL-CLINICAPP-09", "QA-PORTAL-CLINICAPP-10",
    "QA-PORTAL-HCPMEMBER-01", "QA-PORTAL-HCPMEMBER-02", "QA-PORTAL-HCPMEMBER-03",
    "QA-PORTAL-HCPMEMBER-04", "QA-PORTAL-HCPMEMBER-05",
    "QA-PORTAL-ADMINSUSPEND-01", "QA-PORTAL-ADMINREMOVE-01",
    "QA-PORTAL-ADMINGRANT-01", "QA-PORTAL-ADMINGRANT-02", "QA-PORTAL-ADMINGRANT-03",
    "QA-PORTAL-FIRSTADMIN-01", "QA-PORTAL-SUCCESSOR-01",
}

SUPER_ADMIN_TARGETS = {
    "QA-PORTAL-CLINICAPP-01",
    "QA-PORTAL-ADMINSUSPEND-01", "QA-PORTAL-ADMINREMOVE-01",
    "QA-PORTAL-ADMINGRANT-01", "QA-PORTAL-ADMINGRANT-02", "QA-PORTAL-ADMINGRANT-03",
}


def numbered_count(text: str) -> int:
    return len(re.findall(r"(?m)^\d+\.\s", text or ""))


def normalize_text(text: str, field: str) -> str:
    if field not in {"proc", "exp", "ev"}:
        return re.sub(r"\s+", " ", text).strip()
    # Keep existing step boundaries, and restore lists flattened by older audits.
    text = re.sub(r"[^\S\n]+", " ", text).strip()
    markers = list(re.finditer(r'''(?m)(?:^|(?<=[.!?"”’]) +)(\d+)\.\s+''', text))
    if markers and [int(m[1]) for m in markers] == list(range(1, len(markers) + 1)):
        return "\n".join(
            text[m.start(1):markers[i + 1].start() if i + 1 < len(markers) else len(text)].strip()
            for i, m in enumerate(markers)
        )
    return text


def clean_asset_ref(value: str) -> str:
    return value.rstrip(".")


def purpose_for(ref: str) -> str:
    prefix = ref.split("-", 1)[0]
    return PURPOSES.get(prefix, "Controlled PRT-0702 test resource")


def account_purpose(alias: str) -> str:
    name = alias.removeprefix("QA-PORTAL-").replace("-", " ").title()
    return f"Controlled {name} account fixture"


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    configured_accounts = {}
    if ACCOUNTS_PATH.exists():
        for row in json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8")):
            if row.get("alias"):
                configured_accounts[row["alias"]] = row.get("email", "")
    fixture_aliases = set()
    if FIXTURE_PATH.exists():
        fixture_aliases = {
            row.get("alias")
            for row in json.loads(FIXTURE_PATH.read_text(encoding="utf-8")).get("fixtures", [])
            if row.get("alias")
        }

    asset_cases: dict[str, list[str]] = defaultdict(list)
    account_cases: dict[str, list[str]] = defaultdict(list)
    reviews = []
    changed = 0

    for case in cases:
        before = json.dumps(case, ensure_ascii=False, sort_keys=True)
        for field in ("t", "pre", "proc", "exp", "ev"):
            text = case.get(field, "")
            text = text.replace(GENERIC_SENTENCE, "")
            text = re.sub(r"\bis recorded in the execution record\b", "is listed in the execution record", text, flags=re.I)
            text = re.sub(r"\bare recorded in the execution record\b", "are listed in the execution record", text, flags=re.I)
            text = re.sub(r"\brecorded\b", "listed", text, flags=re.I)
            text = normalize_text(text, field)
            case[field] = text

        # Some legacy preconditions named the target record before the acting
        # Super Admin.  The earlier mechanical conversion interpreted that
        # target as the signed-in user.  Restore the actor/target distinction.
        for target in SUPER_ADMIN_TARGETS:
            wrong = f"{target} is signed in with its approved role."
            if case["pre"].startswith(wrong):
                case["pre"] = case["pre"].replace(
                    wrong,
                    f"QA-PORTAL-SUPER-ADMIN-01 is signed in with its approved role. {target} is available as the target record fixture.",
                    1,
                )
        if case["id"] == "PAT-SHARE-013" and case["pre"].startswith("QA-PORTAL-CLINIC-01 is signed in"):
            case["pre"] = case["pre"].replace(
                "QA-PORTAL-CLINIC-01 is signed in with its approved role.",
                "QA-PORTAL-HISTORY-01 is signed in with its approved Patient role. QA-PORTAL-CLINIC-01 is available as the active Clinic-share fixture.",
                1,
            )
        if case["id"] == "CLINIC-PAT-021" and case["pre"].startswith("QA-PORTAL-CLINIC-01 is signed in"):
            case["pre"] = case["pre"].replace(
                "QA-PORTAL-CLINIC-01 is signed in with its approved role.",
                "QA-PORTAL-CLINIC-ADMIN-01 is signed in with its approved role. QA-PORTAL-CLINIC-01 is available as its Clinic fixture. A unique unregistered email is available from the tester mailbox.",
                1,
            )

        full_text = " ".join(case.get(k, "") for k in ("pre", "proc", "exp", "ev"))
        assets = sorted({clean_asset_ref(v) for v in ASSET_RE.findall(full_text)})
        accounts = sorted(set(ACCOUNT_RE.findall(full_text)))
        for ref in assets:
            asset_cases[ref].append(case["id"])
        for alias in accounts:
            account_cases[alias].append(case["id"])

        if assets and "Required Portal Test Assets:" not in case["pre"]:
            case["pre"] = case["pre"].rstrip(".") + ". Required Portal Test Assets: " + ", ".join(assets) + "."
        missing_pre_accounts = [alias for alias in accounts if alias not in case["pre"]]
        if missing_pre_accounts:
            case["pre"] = case["pre"].rstrip(".") + ". Required account fixtures: " + ", ".join(missing_pre_accounts) + "."

        auth_additions = {
            "PAT-AUTH-006": "A unique email address that has never been registered is available from the approved tester mailbox.",
            "PAT-AUTH-009": "A unique email address that has never been registered is available from the approved tester mailbox.",
            "PAT-AUTH-014": "QA-PORTAL-NEW-01 is registered and verified, and its tester mailbox is accessible.",
            "PAT-AUTH-016": "QA-PORTAL-UNVERIFIED-01 is registered but not verified, and its tester mailbox is accessible.",
        }
        addition = auth_additions.get(case["id"])
        if addition and addition not in case["pre"]:
            case["pre"] = case["pre"].rstrip(".") + ". " + addition

        proc_count = numbered_count(case.get("proc", ""))
        exp_count = numbered_count(case.get("exp", ""))
        issues = []
        if not case.get("pre"):
            issues.append("missing precondition")
        if not case.get("proc"):
            issues.append("missing procedure")
        if not case.get("exp"):
            issues.append("missing expected result")
        if proc_count != exp_count:
            issues.append(f"procedure/expected step mismatch ({proc_count}/{exp_count})")
        if re.search(r"\bQA_WEB_|\bTD-", full_text):
            issues.append("legacy reference remains")
        if re.search(r"\brecorded\b", full_text, re.I):
            issues.append("disallowed wording remains")
        if GENERIC_SENTENCE in full_text:
            issues.append("vague Test Assets sentence remains")

        after = json.dumps(case, ensure_ascii=False, sort_keys=True)
        if after != before:
            changed += 1
        reviews.append({
            "id": case["id"],
            "section": case.get("sec", ""),
            "title": case.get("t", ""),
            "procedure_steps": proc_count,
            "expected_steps": exp_count,
            "account_aliases": accounts,
            "test_asset_references": assets,
            "content_status": "reviewed" if not issues else "needs-attention",
            "issues": issues,
        })

    catalog = {
        "generated_for": "PRT-0702",
        "instructions": "Every reference used by a Web Portal case is listed here. If a required value is unavailable, mark the case Blocked and name the missing reference.",
        "accounts": [],
        "resources": [],
    }
    for alias in sorted(account_cases):
        configured = bool(configured_accounts.get(alias))
        verified_fixture = alias in fixture_aliases
        catalog["accounts"].append({
            "reference": alias,
            "kind": "data fixture" if alias in DATA_FIXTURE_ALIASES else "login account",
            "purpose": ("Controlled portal record fixture" if alias in DATA_FIXTURE_ALIASES else account_purpose(alias)),
            "availability": "Configured" if configured else ("Verified fixture" if verified_fixture else "QA provisioning required"),
            "email": configured_accounts.get(alias, ""),
            "cases": account_cases[alias],
        })
    for ref in sorted(asset_cases):
        embedded = bool(configured_accounts.get(ref)) or ref in fixture_aliases
        catalog["resources"].append({
            "reference": ref,
            "purpose": purpose_for(ref),
            "availability": ("Embedded in console" if embedded else
                             "Confirm value in the approved controlled source before execution"),
            "cases": asset_cases[ref],
        })

    CASES_PATH.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "protocol": "PRT-0702",
        "review_date": "2026-10-12",
        "cases_reviewed": len(reviews),
        "cases_changed": changed,
        "cases_needing_attention": sum(r["content_status"] != "reviewed" for r in reviews),
        "account_references": len(catalog["accounts"]),
        "resource_references": len(catalog["resources"]),
        "cases": reviews,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
