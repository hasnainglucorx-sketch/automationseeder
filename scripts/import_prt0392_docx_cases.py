"""Import PRT-0392 case content from the controlled Word protocol.

The DOCX supplies the case ID, requirements, test equipment/test data,
procedure, and expected result. Console-only metadata such as title, section,
method, execution order, duration, and evidence guidance is preserved.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "console-update"
COMPACT_PATH = OUT / "PRT-0701-cases.json"
RUN_ORDER_PATH = OUT / "PRT-0701-run_order.json"


def normalized_cell_text(cell) -> str:
    return "\n".join(line.rstrip() for line in cell.text.splitlines()).strip()


def extract_cases(source: Path) -> list[dict[str, str]]:
    document = Document(source)
    extracted: list[dict[str, str]] = []

    for table in document.tables:
        if len(table.rows) < 4 or len(table.columns) < 5:
            continue
        header = table.rows[0].cells
        if normalized_cell_text(header[0]) != "Test Case ID":
            continue

        steps = table.rows[3:]
        extracted.append(
            {
                "id": normalized_cell_text(header[1]),
                "requirement": normalized_cell_text(header[3]),
                "preconditions": normalized_cell_text(table.rows[1].cells[1]),
                "procedure": "\n".join(
                    normalized_cell_text(row.cells[0])
                    for row in steps
                    if normalized_cell_text(row.cells[0])
                ),
                "expected": "\n".join(
                    normalized_cell_text(row.cells[1])
                    for row in steps
                    if normalized_cell_text(row.cells[1])
                ),
            }
        )

    return extracted


def validate_ids(
    extracted: list[dict[str, str]],
    compact: list[dict],
    run_order: list[dict],
) -> None:
    doc_ids = [item["id"] for item in extracted]
    compact_ids = [item["id"] for item in compact]
    run_order_ids = [item["id"] for item in run_order]

    duplicates = [case_id for case_id, count in Counter(doc_ids).items() if count != 1]
    if duplicates:
        raise RuntimeError(f"DOCX case IDs are not unique: {duplicates}")
    if doc_ids != compact_ids:
        raise RuntimeError("DOCX case IDs/order do not exactly match the compact case source")
    if doc_ids != run_order_ids:
        raise RuntimeError("DOCX case IDs/order do not exactly match the run-order source")


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Latest PRT-0392 DOCX")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Backup directory (default: output/import-backups/<timestamp>)",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    compact = json.loads(COMPACT_PATH.read_text(encoding="utf-8-sig"))
    run_order = json.loads(RUN_ORDER_PATH.read_text(encoding="utf-8-sig"))
    extracted = extract_cases(source)
    validate_ids(extracted, compact, run_order)

    backup_dir = args.backup_dir or (
        ROOT / "output" / "import-backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(COMPACT_PATH, backup_dir / COMPACT_PATH.name)
    shutil.copy2(RUN_ORDER_PATH, backup_dir / RUN_ORDER_PATH.name)
    console_path = ROOT / "CGMX1-Console.html"
    if console_path.exists():
        shutil.copy2(console_path, backup_dir / console_path.name)

    extracted_by_id = {item["id"]: item for item in extracted}
    run_order_by_id = {item["id"]: item for item in run_order}

    changed_ids: list[str] = []
    for compact_item in compact:
        case_id = compact_item["id"]
        source_item = extracted_by_id[case_id]
        full_item = run_order_by_id[case_id]

        new_values = {
            "req": source_item["requirement"],
            "pre": source_item["preconditions"],
            "proc": source_item["procedure"],
            "exp": source_item["expected"],
        }
        full_values = {
            "requirement": source_item["requirement"],
            "preconditions": source_item["preconditions"],
            "procedure": source_item["procedure"],
            "expected": source_item["expected"],
            # The DOCX has no title/evidence fields. Preserve the compact
            # console metadata and synchronize its run-order representation.
            "title": compact_item["t"],
            "evidence": compact_item["ev"],
        }

        if any(compact_item[key] != value for key, value in new_values.items()) or any(
            full_item[key] != value for key, value in full_values.items()
        ):
            changed_ids.append(case_id)

        compact_item.update(new_values)
        full_item.update(full_values)

    write_json(COMPACT_PATH, compact)
    write_json(RUN_ORDER_PATH, run_order)

    print(f"Imported {len(extracted)} cases from {source}")
    print(f"Changed {len(changed_ids)} cases")
    print(f"Backup: {backup_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
