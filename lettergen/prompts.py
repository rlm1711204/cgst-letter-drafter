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
    "short": "06_short_task.md",
    "short_fact_check": "07_short_fact_check.md",
}

RULES_HEADER = ("{title}\n"
                "This source is an INSTRUCTION SHEET for drafting. It is NOT evidence: never cite it or take facts "
                "from it. Whenever a chat message refers to this sheet, follow it exactly. Values shown as "
                "\"(given in the chat message)\" come from that message.\n\n")
GIVEN = "(given in the chat message)"


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


# =========================================================================== short prompt + rules sheet
def rules_title(kind: str) -> str:
    return f"RULES SOURCE - CGST DRAFTER - {kind.upper().replace('_', ' ')}"


def letter_rules_sheet() -> str:
    """Full letter prompt with the dynamic parts generic, and the checklists of ALL letter types."""
    types = load_data("letter_types")["letter_types"]
    checklist = "\n".join(f"* If letter type is {k} ({v['label']}):\n" + "\n".join(f"  - {c}" for c in v["checklist"])
                          for k, v in types.items())
    body = fill(load("draft"), LETTER_TYPE_LABEL=GIVEN, LETTER_TYPE_KEY=" | ".join(types),
                INSTRUCTION=GIVEN, FROM_OFFICE=GIVEN, SIGNATORY=GIVEN, FILE_NO="", DIN="",
                FILE_NO_SHOW=GIVEN, DIN_SHOW=GIVEN, LETTER_DATE=GIVEN, CHECKLIST=checklist)
    return RULES_HEADER.format(title=rules_title("letter")) + body


def format_rules_sheet(fmt: str, prompt_file: str) -> str:
    body = fill(load(prompt_file), INSTRUCTION=GIVEN, FROM_OFFICE=GIVEN, SIGNATORY=GIVEN, LETTER_DATE=GIVEN,
                FILE_NO="", DIN="", FILE_NO_SHOW=GIVEN, DIN_SHOW=GIVEN, TODAY=GIVEN)
    return RULES_HEADER.format(title=rules_title(fmt)) + body


def short_prompt(kind: str, format_label: str, instruction: str, profile: dict, letter_date: str = "",
                 file_no: str = "", din: str = "", letter_type: str = "") -> str:
    sig = ", ".join(x for x in (profile.get("signatory_name"), profile.get("signatory_designation")) if x)
    type_line = ""
    if letter_type:
        key = key_for_label(letter_type)
        type_line = f" - letter type: {key} ({letter_type_keys().get(key, key)})"
    return fill(load("short"), RULES_TITLE=rules_title(kind), FORMAT_LABEL=format_label, TYPE_LINE=type_line,
                INSTRUCTION=instruction.strip() or "[describe the purpose]",
                FROM_OFFICE=office_line(profile) or "[my office]", SIGNATORY=sig or "leave blank",
                FILE_NO_SHOW=file_no or "not given", DIN_SHOW=din or "not given",
                LETTER_DATE=letter_date or dt.date.today().strftime("%d.%m.%Y"))


def draft_source_text(letter_text: str) -> str:
    return "DRAFT FOR FACT CHECK - not evidence; delete this source after checking.\n\n" + letter_text
