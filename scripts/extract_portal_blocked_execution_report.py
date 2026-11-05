"""Extract BLOCKED cases from the supplied PAT-0701 Web Portal run report.

The PDF is evidence of which cases were blocked and why.  The current
PRT-0702 cases JSON remains the authoritative protocol text.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber


DEFAULT_PDF = Path(
    r"C:\Users\Hasnain\Downloads\adnroid verificagtion"
) / (
    "PAT-0701 · Web Portal Verification Protocol · Web portal.pdf"
)
DEFAULT_OUTPUT = Path("output/portal-fixtures/execution-report-blocked-142.json")
CASE_ID = re.compile(r"^[A-Z][A-Z0-9-]+$")


def clean(value: object) -> str:
    return str(value or "").replace("\n", " ").strip()


def extract(pdf_path: Path) -> list[dict[str, object]]:
    blocked: list[dict[str, object]] = []
    with pdfplumber.open(pdf_path) as document:
        for page_number, page in enumerate(document.pages, start=1):
            for table in page.extract_tables() or []:
                result_column = None
                for row in table:
                    cells = [clean(cell) for cell in row]
                    if "RESULT" in cells:
                        result_column = cells.index("RESULT")
                        continue
                    if result_column is None or len(cells) <= result_column:
                        continue
                    case_id = cells[0]
                    if not CASE_ID.fullmatch(case_id):
                        continue
                    if cells[result_column] != "BLOCKED":
                        continue
                    title = cells[1] if len(cells) > 1 else ""
                    note_column = result_column + 2
                    note = cells[note_column] if len(cells) > note_column else ""
                    blocked.append(
                        {
                            "id": case_id,
                            "title_at_execution": title,
                            "blocker_note": note,
                            "report_page": page_number,
                        }
                    )

    duplicates = sorted(
        case_id
        for case_id in {item["id"] for item in blocked}
        if sum(item["id"] == case_id for item in blocked) > 1
    )
    if duplicates:
        raise RuntimeError(f"Duplicate blocked IDs extracted: {duplicates}")
    if len(blocked) != 142:
        raise RuntimeError(f"Expected 142 blocked cases, extracted {len(blocked)}")
    return blocked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    blocked = extract(args.pdf)
    payload = {
        "source": str(args.pdf),
        "source_run_label": "YN Test Run",
        "source_test_date": "2026-09-21",
        "blocked_count": len(blocked),
        "cases": blocked,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Extracted {len(blocked)} blocked cases to {args.output}")


if __name__ == "__main__":
    main()
