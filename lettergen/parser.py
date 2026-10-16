"""Robustly pull the JSON object out of whatever was copied from NotebookLM."""
from __future__ import annotations

import json
import re

try:  # optional dependency, installed from requirements.txt
    from json_repair import repair_json
except Exception:  # pragma: no cover
    repair_json = None

# NotebookLM inserts citation markers such as [1], [2, 3] or [4-6].
CITATION_RE = re.compile(r"\s?\[(?:\d{1,3}(?:\s*[,\-–]\s*\d{1,3})*)\]")
FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.S)


class ParseError(ValueError):
    pass


def _candidates(text: str):
    for m in FENCE_RE.finditer(text):
        yield m.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        yield text[start:end + 1]


def strip_citations(obj):
    """Remove NotebookLM citation markers from every string inside the parsed object."""
    if isinstance(obj, str):
        return CITATION_RE.sub("", obj).strip()
    if isinstance(obj, list):
        return [strip_citations(x) for x in obj]
    if isinstance(obj, dict):
        return {k: strip_citations(v) for k, v in obj.items()}
    return obj


def extract_json(text: str) -> tuple[dict, list[str]]:
    """Return (data, notes). notes explain any repair that was needed."""
    if not text or not text.strip():
        raise ParseError("Nothing was pasted. Copy the full NotebookLM answer (the JSON block) and paste it.")
    text = text.replace("﻿", "").replace(" ", " ")
    notes: list[str] = []
    last_err = None
    for cand in _candidates(text):
        attempts = [
            ("as-is", cand),
            ("citation markers removed", CITATION_RE.sub("", cand)),
        ]
        for label, src in attempts:
            try:
                data = json.loads(src)
                if isinstance(data, dict):
                    if label != "as-is":
                        notes.append(f"JSON parsed after: {label}.")
                    return strip_citations(data), notes
            except json.JSONDecodeError as e:
                last_err = e
        if repair_json is not None:
            for label, src in [
                ("automatic repair", CITATION_RE.sub("", cand)),
                ("smart-quote fix + repair", CITATION_RE.sub("", cand)
                 .replace("“", '"').replace("”", '"')),
            ]:
                try:
                    fixed = repair_json(src, return_objects=True)
                    if isinstance(fixed, dict) and fixed:
                        notes.append(f"JSON was not strictly valid - used {label}. "
                                     "Check the preview carefully.")
                        return strip_citations(fixed), notes
                except Exception as e:  # pragma: no cover
                    last_err = e
    hint = ""
    if isinstance(last_err, json.JSONDecodeError):
        lines = (last_err.doc or "").splitlines()
        ln = last_err.lineno
        snippet = lines[ln - 1] if 0 < ln <= len(lines) else ""
        hint = f"\nProblem near line {ln}, column {last_err.colno}: {snippet[:120]!r}"
    raise ParseError("Could not find a valid JSON object in the pasted text." + hint +
                     "\nTip: in NotebookLM send prompt 04 (fix invalid JSON) and copy the answer again.")
