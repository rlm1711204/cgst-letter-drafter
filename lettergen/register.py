"""Dispatch-style register (CSV in the workspace) of every letter generated."""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

FIELDS = ["generated_at", "letter_type", "file_no", "din", "letter_date", "subject", "addressees",
          "errors", "warnings", "docx_file"]


def append(root: Path, letter: dict, issues: list[dict], docx_path: Path) -> Path:
    path = Path(root) / "letter_register.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({
            "generated_at": dt.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "letter_type": letter.get("letter_type", ""),
            "file_no": letter.get("file_no", ""),
            "din": letter.get("din", ""),
            "letter_date": letter.get("date", ""),
            "subject": letter.get("subject", ""),
            "addressees": " / ".join(
                (a.get("name") or a.get("designation") or (a.get("address_lines") or [""])[0])
                for a in letter.get("to", [])),
            "errors": sum(1 for i in issues if i["level"] == "ERROR"),
            "warnings": sum(1 for i in issues if i["level"] == "WARN"),
            "docx_file": Path(docx_path).name,
        })
    return path


def read(root: Path) -> list[dict]:
    path = Path(root) / "letter_register.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))
