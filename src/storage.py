"""Shared JSON checkpoint persistence for single-process seed runs."""
import json
from pathlib import Path


def write_json(path: Path, value: object, *, indent: int | None = 2) -> None:
    """Replace a checkpoint only after serialization and writing succeed.

    The temporary file is beside the destination so replacement stays on the
    same filesystem. This does not provide locking: use one writer per run.
    """
    payload = json.dumps(value, indent=indent)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)
