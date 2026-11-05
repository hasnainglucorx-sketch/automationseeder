"""Validate selected PRT-0702 cases and their embedded console copies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "output" / "console-update" / "PRT-0702-cases.json"
HTML = ROOT / "CGMX1-Console.html"
NUMBER = re.compile(r"(?m)^\s*(\d+)\.\s+")
ACTION = re.compile(
    r"(?:^|[.;]\s+)(?:click|select|open|enter|type|record|change|clear|refresh|sign in|log in|"
    r"log out|save|compare|inspect|turn|use|press|navigate|run|register|write|find|look up|"
    r"go to|fill|submit|scan|make|get|try|copy|set up)\b",
    re.IGNORECASE | re.MULTILINE,
)


def embedded_portal_cases(source: str) -> list[dict]:
    match = re.search(
        r"const\s+ALL_PORTAL_CASES\s*=\s*(\[.*?\]);\s*const\s+PORTAL_FIXTURE_MANIFEST",
        source,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError("ALL_PORTAL_CASES was not found in the console")
    return json.loads(match.group(1))


def main() -> None:
    selected = sys.argv[1:]
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in cases}
    if len(by_id) != len(cases):
        raise RuntimeError("Duplicate PRT-0702 case IDs")
    ids = selected or [case["id"] for case in cases]
    findings: list[str] = []
    embedded = {case["id"]: case for case in embedded_portal_cases(HTML.read_text(encoding="utf-8"))}
    for case_id in ids:
        case = by_id.get(case_id)
        if not case:
            findings.append(f"{case_id}: missing from PRT-0702-cases.json")
            continue
        procedure = NUMBER.findall(case.get("proc", ""))
        expected = NUMBER.findall(case.get("exp", ""))
        if procedure != expected:
            findings.append(
                f"{case_id}: procedure numbers {procedure} != expected numbers {expected}"
            )
        if ACTION.search(case.get("pre", "")):
            findings.append(f"{case_id}: actionable precondition")
        if embedded.get(case_id) != case:
            findings.append(f"{case_id}: embedded console object differs")
    for finding in findings:
        print("FAIL", finding)
    print(f"cases checked: {len(ids)}")
    print(f"violations: {len(findings)}")
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
