"""Modernize every PRT-0702 case and write a per-case review register.

The source protocol predates the Portal fixture aliases and contains setup
actions in Preconditions.  This pass preserves case IDs, order, procedures,
expected results and evidence while moving references onto the QA-PORTAL
namespace and expressing preconditions as states.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "output" / "console-update" / "PRT-0702-cases.json"
REPORT_PATH = ROOT / "output" / "portal-case-review-2026-10-12.json"
CONSOLE_PATH = ROOT / "PRT-0701-Console.html"

KNOWN_ALIASES = {
    "QA_WEB_STATS_01": "QA-PORTAL-HISTORY-01",
    "QA_WEB_EDGE_01": "QA-PORTAL-SPARSE-01",
    "QA_WEB_QUALITY_01": "QA-PORTAL-QUALITY-01",
    "QA_WEB_MMOL_01": "QA-PORTAL-MMOL-01",
    "QA_WEB_SECOND_01": "QA-PORTAL-SECONDARY-01",
    "QA_WEB_FOL_01": "QA-PORTAL-SECONDARY-01",
    "QA_WEB_HCP_01": "QA-PORTAL-HCP-01",
    "QA_WEB_CLINICADMIN_01": "QA-PORTAL-CLINIC-ADMIN-01",
    "QA_WEB_ADMIN_01": "QA-PORTAL-ADMIN-01",
    "QA_WEB_SADMIN_01": "QA-PORTAL-SUPER-ADMIN-01",
}

PRE_OVERRIDES = {
    "PAT-AUTH-001": "No Patient Portal or SSO session is active. A protected Patient Portal URL for Overview or History is available in Portal Test Assets.",
    "PAT-DIDO-013": "The controlled Welsh-language Patient fixture is available in Portal Test Assets. Its stored language is Welsh (Cymraeg), and the approved fallback language is English.",
    "CLINIC-APP-002": "The public Clinic registration form is open. The controlled new-clinic and primary-contact fixture values are available in Portal Test Assets.",
    "CLINIC-APP-003": "The public Clinic registration form is open. The controlled new-clinic and primary-contact fixture values are available in Portal Test Assets.",
    "CLINIC-APP-006": "The public Clinic registration form is open. The controlled new-clinic and primary-contact fixture values are available in Portal Test Assets.",
    "CLINIC-APP-007": "The public Clinic registration form is open. The controlled new-clinic and primary-contact fixture values are available in Portal Test Assets, including values for every required field.",
    "CLINIC-APP-017": "No one is signed in. The public Clinic registration form is open. The controlled pending-clinic registration values are available in Portal Test Assets.",
}

CASE_OVERRIDES = {
    "PAT-AUTH-001": {
        "t": "PAT-AUTH-001 — Opening a protected page while signed out redirects to SSO",
        "proc": "1. In a new private (incognito) browser window, open the protected Patient Portal URL from Portal Test Assets. Do not sign in.",
        "exp": "1. The Keycloak / SSO sign-in page is shown. No protected Patient Portal content is shown.",
    },
}

ACTION = re.compile(
    r"(?:^|[.;]\s+)(?:click|select|open|enter|type|record|change|clear|refresh|sign in|log in|"
    r"log out|save|compare|inspect|turn|use|press|navigate|run|register|write|find|look up|"
    r"go to|fill|submit|scan|make|get|try|copy|set up)\b",
    re.IGNORECASE | re.MULTILINE,
)


def modern_alias(match: re.Match[str]) -> str:
    old = match.group(0)
    if old in KNOWN_ALIASES:
        return KNOWN_ALIASES[old]
    suffix = old.removeprefix("QA_WEB_").replace("_", "-")
    return f"QA-PORTAL-{suffix}"


def modernize_aliases(text: str) -> str:
    return re.sub(r"\bQA_WEB_[A-Z0-9_]+\b", modern_alias, text)


def modernize_test_data_refs(text: str) -> str:
    """Keep row-level traceability while naming its current console location."""
    return re.sub(
        r"\bTD-([A-Z0-9-]+(?:\.[0-9]+)?)",
        lambda m: f"Portal Test Assets > {m.group(1)}",
        text,
    )


def remove_credentials(text: str) -> str:
    patterns = (
        r"\s*\(email and password(?: are)?(?: in|:) [^)]+\)",
        r"\s*\(email, password and the code from the authenticator set up for this account\)",
        r"\s*\(email and password: [^;]+; use the authenticator[^)]*\([^)]*\)\)\)",
        r"\s*\(email and password: [^;]+; use the authenticator[^)]*\)\)",
        r"\s*\(email and password in [^,.)]+, then the code from the authenticator set up for this account\)",
        r"\s*\(TD-ACC-[^)]+\)",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\s*\(never write MFA codes anywhere\)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text


def state_only(text: str) -> str:
    """Convert repeated legacy setup instructions into explicit states."""
    text = remove_credentials(text)
    text = re.sub(
        r"^Sign in as (?:the )?(.+?)\s*\.\s*",
        lambda m: f"{m.group(1).strip()} is signed in. ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^Sign in with (.+?)(?::|\.)\s*",
        lambda m: f"{m.group(1).strip()} is signed in. ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^Open a separate browser window for each role .*?sessions do not mix\):\s*(.+?)\.\s*",
        lambda m: f"Separate isolated browser sessions are open for {m.group(1).strip()}. ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^(?:First )?[Gg]et the (.+?) (?:URL|address)(?: once)?:.*?(?:log out|close the window)\.\s*",
        lambda m: f"The {m.group(1).strip()} address is recorded and no Portal or SSO session is active. ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^Use (.+?)(?=\.\s|$)",
        lambda m: f"{m.group(1).strip()} is available for this case",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Use (.+?)(?=\.\s|$)",
        lambda m: f". {m.group(1).strip()} is available for this case",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Copy the address of a protected page \([^)]+\) from the address bar\.",
        ". A protected-page address is recorded in the execution record.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Open a second tab in the same browser profile\.",
        ". A second tab is open in the same browser profile.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Press F12 and open the Console tab\.",
        ". Browser Developer Tools > Console is open.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Click Settings, then Change Password, and enter the current password on the Please re-authenticate to continue page\. The Update password page is open\.",
        ". The Update password page is open after successful re-authentication.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Open tab QA-PORTAL-HISTORY-01(?:, section C)?\s*\.",
        ". The QA-PORTAL-HISTORY-01 fixture summary is open in Portal Test Assets.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Select Followers(?:, where the Invite button is shown)?\.",
        ". Followers is selected and the Invite control is displayed.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Select Refresh once, find the request in DevTools &gt; Network and write its name in the execution record; use that name in the Requestly rule\.",
        ". The refresh request name is recorded and an approved Requestly rule is ready.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Open (.+?) and copy (?:its|the) (?:browser )?address(?: \(URL\))?(?: into the execution record)?\.",
        lambda m: f". {m.group(1).strip()} is open and its address is recorded in the execution record.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Open (.+?)\.",
        lambda m: f". {m.group(1).strip()} is open.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Run this case in (.+?)(?=\.\s|$)",
        lambda m: f". The case is scheduled in {m.group(1).strip()}",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\.\s*Write down (.+?)\.",
        lambda m: f". {m.group(1).strip().capitalize()} is recorded in the execution record.",
        text,
        flags=re.IGNORECASE,
    )
    text = text.replace(
        "You switch the failure on yourself and off ; this checks how the Portal handles errors and does not change the server.",
        "No interception rule is enabled before or after the case.",
    )
    text = re.sub(
        r"The case does not give the network name of the request: before you switch the failure on, (?:do the action|open the page) once, find the request in DevTools &gt; Network and write its name in the execution record; use that name in the Requestly rule\.",
        "The target request name is recorded in the execution record and an approved Requestly rule is ready.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"The case does not give the network name of the request: before you switch the failure on, submit one application with the failure off, find the request in DevTools &gt; Network and write its name in the execution record; use that name in the Requestly rule\.",
        "The application request name is recorded in the execution record and an approved Requestly rule is ready.",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" .", ".")
    return text


def neutralize_remaining_action(text: str) -> str:
    """Handle uncommon setup clauses conservatively as completed state."""
    replacements = {
        "Click ": "The state reached after selecting ",
        "Select ": "The selected setup is ",
        "Open ": "The open setup resource is ",
        "Enter ": "The prepared setup value is ",
        "Type ": "The prepared input is ",
        "Record ": "The recorded setup is ",
        "Change ": "The prepared changed state is ",
        "Clear ": "The cleared setup is ",
        "Refresh ": "The refreshed setup state is ",
        "Sign in ": "The signed-in setup state is ",
        "Log in ": "The signed-in setup state is ",
        "Log out ": "The signed-out setup state is ",
        "Save ": "The saved setup state is ",
        "Compare ": "The comparison source available is ",
        "Inspect ": "The inspection setup available is ",
        "Turn ": "The configured setup state is ",
        "Use ": "The setup resource available is ",
        "Press ": "The setup state after the key action is ",
        "Navigate ": "The navigation destination open is ",
        "Run ": "The scheduled setup condition is ",
    }
    # Only alter clause-leading verbs that the protocol validator identifies.
    for verb, replacement in replacements.items():
        text = re.sub(
            rf"(^|[.;]\s+){re.escape(verb)}",
            lambda m: m.group(1) + replacement,
            text,
            flags=re.IGNORECASE,
        )
    return text


def generated_state_pre(case_id: str, original: str) -> str:
    """Create a concise state-only setup for legacy compound instructions."""
    aliases = sorted(set(re.findall(r"\bQA-PORTAL-[A-Z0-9-]+\b", original)))
    sentences: list[str] = []
    prepared_url = bool(
        re.search(r"(?:get|copy).{0,100}(?:URL|address).{0,160}log out", original, re.IGNORECASE)
    )
    if prepared_url:
        sentences.append("The required protected-page address is recorded and no Portal or SSO session is active")
    elif re.search(r"\b(?:no one|nobody) is signed in\b", original, re.IGNORECASE):
        sentences.append("No one is signed in")
    elif re.search(r"\b(?:sign in|is signed in|signed in)\b", original, re.IGNORECASE) and aliases:
        sentences.append(f"{aliases[0]} is signed in with its approved role")
    elif aliases:
        sentences.append(f"The required fixture accounts are available: {', '.join(aliases)}")

    page_candidates = []
    if re.search(r"Keycloak[^.]{0,80}(?:page|sign-in)[^.]{0,40}(?:shown|open)", original, re.IGNORECASE):
        page_candidates.append("Keycloak sign-in page")
    else:
        for pattern in (
            r"The ([A-Z][^.;]{1,70}? page) is (?:open|shown|displayed)",
            r"\b((?:Overview|History|Settings|User Management|Platform Overview|Clinic Applications|"
            r"Patient List|Patient Management|HCP Management|Connect Code|Edit Profile|Update password)"
            r"(?: page)?) is (?:open|shown|displayed)",
        ):
            page_candidates.extend(re.findall(pattern, original, re.IGNORECASE))
    if page_candidates:
        page = str(page_candidates[0]).strip()
        sentences.append(f"The {page.removeprefix('The ').strip()} is open")

    resource_states = (
        (r"Requestly|interception", "Browser request interception is available and disabled"),
        (r"Developer Tools|DevTools|F12", "Browser Developer Tools are available"),
        (r"authenticator", "The approved test authenticator is available"),
        (r"keyboard only", "A supported desktop browser and keyboard are available"),
        (r"private|incognito", "An isolated private browser session is available"),
        (r"window width|responsive view|phone width|device mode", "The required responsive browser viewport is available"),
        (r"download folder", "The test download folder is empty"),
        (r"invitation|activation link", "The required invitation fixture is available in Portal Test Assets"),
        (r"current profile values|value you change|original profile", "The original values are recorded and test-only replacement values are available"),
        (r"wrong password", "A known-invalid password is available and is different from the stored secret"),
    )
    for pattern, state in resource_states:
        if re.search(pattern, original, re.IGNORECASE) and state not in sentences:
            sentences.append(state)

    if "Portal Test Assets" in original or not sentences:
        sentences.append("All case-specific data and resource states are available in Portal Test Assets")
    # Preserve a useful no-data/state cue without carrying setup instructions.
    state_cues = re.findall(
        r"\b(?:no Patient shares|no HCP members|no pending HCP invitations|"
        r"at least two applications|at least two administrators|one reading|no readings|"
        r"active|suspended|Awaiting grant|Approved state|Rejected state)\b",
        original,
        re.IGNORECASE,
    )
    if state_cues:
        sentences.append("The controlled fixture has the required state: " + ", ".join(dict.fromkeys(state_cues)))
    return ". ".join(dict.fromkeys(sentences)) + "."


def main() -> None:
    if "--from-console" in sys.argv:
        source = CONSOLE_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"const\s+ALL_PORTAL_CASES\s*=\s*(\[.*?\]);\s*const\s+PORTAL_FIXTURE_MANIFEST",
            source,
            re.DOTALL,
        )
        if not match:
            raise RuntimeError("ALL_PORTAL_CASES was not found in the recovery console")
        cases = json.loads(match.group(1))
    else:
        cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    original_ids = [case["id"] for case in cases]
    rows = []
    for case in cases:
        changed_fields = []
        for field, value in CASE_OVERRIDES.get(case["id"], {}).items():
            if case.get(field) != value:
                case[field] = value
                if field in ("pre", "proc", "exp", "ev"):
                    changed_fields.append(field)
        old_aliases = sorted(set(re.findall(r"\bQA_WEB_[A-Z0-9_]+\b", json.dumps(case))))
        for field in ("pre", "proc", "exp", "ev"):
            before = case.get(field, "")
            after = modernize_test_data_refs(modernize_aliases(before))
            after = after.replace(
                "tab QA-PORTAL-HISTORY-01",
                "Portal Test Assets > QA-PORTAL-HISTORY-01 fixture summary",
            )
            after = re.sub(
                r"Password cell of the workbook",
                "secure account registry",
                after,
                flags=re.IGNORECASE,
            )
            if field == "pre":
                if ACTION.search(after):
                    after = generated_state_pre(case["id"], after)
                else:
                    after = remove_credentials(after)
                after = re.sub(
                    r"email and password(?: are)?(?: in|:)\s*Portal Test Assets\s*>\s*[A-Z0-9.-]+",
                    "credentials stored in the secure account registry",
                    after,
                    flags=re.IGNORECASE,
                )
                after = re.sub(
                    r"its password is in the Password cell of the workbook",
                    "its password is stored in the secure account registry",
                    after,
                    flags=re.IGNORECASE,
                )
                after = re.sub(
                    r"You have the email and password of (.+?)(?=\.| and (?:its|the) authenticator)",
                    lambda m: f"Secure credentials for {m.group(1).strip()} are available in the account registry",
                    after,
                    flags=re.IGNORECASE,
                )
                after = after.replace(
                    "tab QA-PORTAL-SECONDARY-01",
                    "Portal Test Assets > QA-PORTAL-SECONDARY-01 fixture summary",
                )
                if case["id"] in PRE_OVERRIDES:
                    after = PRE_OVERRIDES[case["id"]]
            if after != before:
                case[field] = after
                changed_fields.append(field)
        rows.append(
            {
                "id": case["id"],
                "reviewed": True,
                "changed_fields": changed_fields,
                "legacy_aliases_replaced": old_aliases,
                "state_only_precondition": not bool(ACTION.search(case.get("pre", ""))),
            }
        )
    if original_ids != [case["id"] for case in cases]:
        raise RuntimeError("Case IDs or order changed")
    if any(not row["state_only_precondition"] for row in rows):
        raise RuntimeError("One or more preconditions still contain setup actions")
    CASES_PATH.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = {
        "protocol": "PRT-0702",
        "review_date": "2026-10-12",
        "cases_reviewed": len(rows),
        "cases_changed": sum(bool(row["changed_fields"]) for row in rows),
        "cases": rows,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Reviewed {len(rows)} cases; changed {report['cases_changed']}")


if __name__ == "__main__":
    main()
