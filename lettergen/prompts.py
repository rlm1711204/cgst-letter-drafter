"""Build the copy-paste prompts from prompts/*.md (edit those files to change wording)."""
from __future__ import annotations

import datetime as dt
import json
import re

from .config import PROMPTS_DIR, load_data

FILES = {
    "setup": "00_notebooklm_notebook_setup.md",
    "draft": "01_notebooklm_extract_and_draft.md",
    "fact_check": "02_notebooklm_fact_check.md",
    "verify": "03_other_ai_legal_verification.md",
    "fix_json": "04_fix_invalid_json.md",
    "revise": "05_notebooklm_revise.md",
}


def load(name: str) -> str:
    text = (PROMPTS_DIR / FILES.get(name, name)).read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->\s*(.*?)\s*<!-- PROMPT END -->", text, re.S)
    return (m.group(1) if m else text).strip()


def fill(template: str, **values) -> str:
    def rep(m):
        key = m.group(1)
        return str(values[key]) if key in values else m.group(0)
    return re.sub(r"\{\{([A-Z_]+)\}\}", rep, template)


def letter_type_keys() -> dict:
    return {k: v["label"] for k, v in load_data("letter_types").get("letter_types", {}).items()}


def key_for_label(label: str) -> str:
    for k, v in letter_type_keys().items():
        if label in (k, v):
            return k
    return label


_KEEP_UPPER = {"CGST", "GST", "SGST", "IGST", "CBIC", "GSTIN", "DGGI", "TN", "II", "III", "IV"}
_SMALL = {"of", "the", "and", "in", "for", "at", "&"}


def smart_title(s: str) -> str:
    """'OFFICE OF THE COMMISSIONER OF CGST & CENTRAL EXCISE' -> 'Office of the Commissioner of CGST & Central Excise'."""
    if not s.isupper():
        return s
    words = []
    for i, w in enumerate(s.split()):
        core = w.strip(",.()")
        if core in _KEEP_UPPER:
            words.append(w)
        elif i and w.lower() in _SMALL:
            words.append(w.lower())
        else:
            words.append(w.capitalize())
    return " ".join(words)


def office_line(profile: dict) -> str:
    lines = [l.split("/")[-1].strip() for l in profile.get("office_lines", []) if l.strip()]
    office = ", ".join(smart_title(x) for x in lines[-2:])
    sec = profile.get("section") or ""
    return ", ".join(x for x in (sec, office, profile.get("office_address", "")) if x and "[" not in x)


def notebooklm_prompt(letter_type: str, instruction: str, profile: dict, letter_date: str = "",
                      file_no: str = "", din: str = "") -> str:
    key = key_for_label(letter_type)
    t = load_data("letter_types")["letter_types"].get(key, {})
    checklist = "\n".join(f"- {c}" for c in t.get("checklist", []))
    sig = ", ".join(x for x in (profile.get("signatory_name"), profile.get("signatory_designation")) if x)
    return fill(load("draft"),
                LETTER_TYPE_LABEL=t.get("label", key), LETTER_TYPE_KEY=key,
                INSTRUCTION=instruction.strip() or "[describe what the letter must do]",
                FROM_OFFICE=office_line(profile) or "[my office]",
                SIGNATORY=sig or "take from source if mentioned, else leave blank",
                FILE_NO=file_no, DIN=din,
                FILE_NO_SHOW=file_no or "not given - leave \"\"",
                DIN_SHOW=din or "not yet generated - leave \"\"",
                LETTER_DATE=letter_date or dt.date.today().strftime("%d.%m.%Y"),
                CHECKLIST=checklist)


def fact_check_prompt(letter_text: str) -> str:
    return fill(load("fact_check"), LETTER_TEXT=letter_text)


def verification_prompt(letter: dict, letter_text: str, issues: list[dict], citations: list[dict],
                        instruction: str = "") -> str:
    labels = letter_type_keys()
    auto = "\n".join(f"   - [{i['level']}] {i['where']}: {i['msg']}" for i in issues) or "   - none"
    cites = "; ".join(sorted({f"{c['kind']} {c['number']}{c['sub']} ({c['act']})" for c in citations})) or "none found"
    for c in letter.get("legal_citations", []):
        if c.get("provision"):
            cites += f"; {c['provision']} [{c.get('basis', '')}]"
    facts = json.dumps({"key_facts": letter.get("key_facts", {}), "deadlines": letter.get("deadlines", []),
                        "source_documents": letter.get("source_documents", [])}, indent=2, ensure_ascii=False)
    return fill(load("verify"), LETTER_TYPE_LABEL=labels.get(letter.get("letter_type"), letter.get("letter_type")),
                INSTRUCTION=instruction or letter.get("subject", ""), TODAY=dt.date.today().strftime("%d.%m.%Y"),
                AUTO_CHECKS=auto, CITATIONS=cites, KEY_FACTS=facts, LETTER_TEXT=letter_text)
