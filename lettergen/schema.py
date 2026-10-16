"""Canonical letter structure + tolerant normalisation of whatever NotebookLM returned."""
from __future__ import annotations

import copy
import datetime as dt
import re

SCHEMA_VERSION = "1.0"

EMPTY_LETTER = {
    "schema_version": SCHEMA_VERSION,
    "letter_type": "",
    "file_no": "",
    "din": "",
    "date": "",
    "from": {"office": "", "section": ""},
    "to": [],
    "through": "",
    "kind_attention": "",
    "salutation": "Sir/Madam,",
    "subject": "",
    "references": [],
    "body_paragraphs": [],
    "closing": "Yours faithfully,",
    "signatory": {"name": "", "designation": "", "office_line": ""},
    "enclosures": [],
    "copy_to": [],
    "key_facts": {},
    "legal_citations": [],
    "deadlines": [],
    "missing_or_uncertain": [],
    "source_documents": [],
}

ALIASES = {
    "body": "body_paragraphs", "paragraphs": "body_paragraphs", "letter_body": "body_paragraphs",
    "addressee": "to", "addressees": "to", "recipients": "to", "recipient": "to",
    "reference": "references", "ref": "references", "refs": "references",
    "cc": "copy_to", "copies_to": "copy_to", "copy": "copy_to",
    "encl": "enclosures", "enclosure": "enclosures", "annexures": "enclosures",
    "file_number": "file_no", "c_no": "file_no", "f_no": "file_no", "letter_no": "file_no",
    "letter_date": "date", "sub": "subject", "signature": "signatory", "signed_by": "signatory",
    "type": "letter_type", "citations": "legal_citations", "uncertain": "missing_or_uncertain",
    "missing": "missing_or_uncertain", "facts": "key_facts",
}

TYPE_ALIASES = {
    "taxpayer": "taxpayer", "letter_to_taxpayer": "taxpayer", "taxpayer_letter": "taxpayer",
    "appeal": "appeal_review", "review": "appeal_review", "appeal_review": "appeal_review",
    "court": "court_writ", "writ": "court_writ", "court_writ": "court_writ",
    "scn": "scn_adjudication", "adjudication": "scn_adjudication", "scn_adjudication": "scn_adjudication",
    "admin": "admin", "administrative": "admin", "inter_office": "admin", "interoffice": "admin",
}

DATE_FORMATS = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y",
                "%B %d, %Y", "%b %d, %Y", "%d.%m.%y", "%d/%m/%y", "%d-%m-%y", "%d %B, %Y"]

PLACEHOLDER_RE = re.compile(r"\[(?:TO BE CONFIRMED|TBC|CONFIRM|●|\.\.\.)[^\]]*\]|\[\s*\]|_{4,}|X{4,}",
                            re.I)


def parse_date(value) -> dt.date | None:
    if isinstance(value, dt.date):
        return value
    if not value:
        return None
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", str(value).strip())
    s = re.sub(r"\s+", " ", s)
    for f in DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def format_date(value, style: str = "%d.%m.%Y") -> str:
    d = parse_date(value)
    if d is None:
        return str(value or "")
    out = d.strftime(style)
    return out


def _as_list(v):
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return [x for x in v if x not in (None, "", [], {})]
    if isinstance(v, str):
        parts = [p.strip() for p in re.split(r"\n\s*\n|\n(?=\s*(?:\d+[.)]|\([ivx]+\)|[-•]))", v) if p.strip()]
        return parts if len(parts) > 1 else [v.strip()]
    return [v]


_LEAD_POINT = re.compile(r"^\s*(?:\((?:[ivx]{1,5}|[a-h]|\d{1,2})\)|(?:[ivx]{1,5}|[a-h]|\d{1,2})[.)])\s+")
_LEAD_NUM = re.compile(r"^\s*(?:\d{1,2}[.)]|\(\d{1,2}\)|para\s*\d+[.:])\s+", re.I)


def _clean_para(item):
    if isinstance(item, str):
        return _LEAD_NUM.sub("", item).strip()
    if isinstance(item, dict):
        item = dict(item)
        if "table" in item:
            t = item["table"] or {}
            if isinstance(t, list):  # list of rows
                t = {"headers": t[0] if t else [], "rows": t[1:]}
            t.setdefault("headers", [])
            t.setdefault("rows", [])
            t.setdefault("caption", "")
            t["headers"] = [str(h) for h in t["headers"]]
            t["rows"] = [[("" if c is None else str(c)) for c in r] for r in t["rows"] if r]
            return {"table": t}
        text = item.get("text") or item.get("para") or item.get("paragraph") or ""
        pts = item.get("points") or item.get("sub_points") or item.get("subpoints") or []
        return {"text": _LEAD_NUM.sub("", str(text)).strip(),
                "points": [_LEAD_POINT.sub("", str(p)).strip()
                           for p in _as_list(pts)]}
    return str(item)


def _norm_addressee(a):
    if isinstance(a, str):
        lines = [x.strip().rstrip(",") for x in re.split(r"\n|;", a) if x.strip()]
        return {"name": "", "designation": "", "organisation": "", "address_lines": lines,
                "gstin": "", "email": ""}
    a = dict(a or {})
    lines = a.get("address_lines") or a.get("address") or []
    if isinstance(lines, str):
        lines = [x.strip() for x in re.split(r"\n|;", lines) if x.strip()]
    out = {
        "name": str(a.get("name", "") or ""),
        "designation": str(a.get("designation", "") or ""),
        "organisation": str(a.get("organisation", "") or a.get("organization", "") or
                            a.get("office", "") or a.get("trade_name", "") or ""),
        "address_lines": [str(x) for x in lines if str(x).strip()],
        "gstin": str(a.get("gstin", "") or "").strip().upper(),
        "email": str(a.get("email", "") or ""),
    }
    return out


def normalise(raw: dict, profile: dict | None = None) -> tuple[dict, list[str]]:
    """Map aliases, fill defaults, coerce types. Returns (letter, notes)."""
    notes: list[str] = []
    profile = profile or {}
    data = {}
    for k, v in (raw or {}).items():
        key = ALIASES.get(str(k).strip().lower().replace(" ", "_"), str(k).strip())
        data[key] = v
    letter = copy.deepcopy(EMPTY_LETTER)
    for k, v in data.items():
        letter[k] = v

    lt = str(letter.get("letter_type") or "").strip().lower().replace(" ", "_").replace("/", "_")
    letter["letter_type"] = TYPE_ALIASES.get(lt, lt.split("|")[0] if lt else "")

    for k in ("file_no", "din", "date", "through", "kind_attention", "salutation", "subject", "closing"):
        v = letter.get(k)
        letter[k] = "" if v is None else (" ".join(map(str, v)) if isinstance(v, list) else str(v)).strip()
    letter["din"] = letter["din"].replace(" ", "") if letter["din"].upper().startswith("CBIC") else letter["din"]

    to = letter.get("to")
    if isinstance(to, (str, dict)):
        to = [to]
    letter["to"] = [_norm_addressee(a) for a in (to or []) if a]

    for k in ("references", "enclosures", "copy_to", "missing_or_uncertain"):
        letter[k] = [(_LEAD_NUM.sub("", x).strip() if isinstance(x, str) else
                      (x.get("text") or x.get("value") or str(x)) if isinstance(x, dict) else str(x))
                     for x in _as_list(letter.get(k))]

    body = letter.get("body_paragraphs")
    letter["body_paragraphs"] = [p for p in (_clean_para(x) for x in _as_list(body))
                                 if p and (not isinstance(p, dict) or p.get("text") or p.get("table"))]

    sig = letter.get("signatory")
    if isinstance(sig, str):
        parts = [x.strip() for x in sig.split("\n") if x.strip()]
        sig = {"name": parts[0] if parts else "", "designation": " ".join(parts[1:2]),
               "office_line": " ".join(parts[2:])}
    sig = dict(sig or {})
    sig.setdefault("name", "")
    sig.setdefault("designation", "")
    sig.setdefault("office_line", "")
    p_name, p_desig = profile.get("signatory_name", ""), profile.get("signatory_designation", "")
    if not sig["name"] and p_name:
        if not sig["designation"] or not p_desig or sig["designation"].strip().lower() == p_desig.strip().lower():
            sig["name"] = p_name
            notes.append("Signatory name taken from office profile.")
        else:
            notes.append(f"Signatory name left blank: the letter is signed by '{sig['designation']}', "
                         f"but your profile signatory is '{p_desig}'.")
    if not sig["designation"] and p_desig:
        sig["designation"] = p_desig
    if not sig["office_line"] and profile.get("signatory_office_line"):
        sig["office_line"] = profile["signatory_office_line"]
    letter["signatory"] = {k: str(v or "") for k, v in sig.items()}

    if not letter["salutation"]:
        letter["salutation"] = "Sir/Madam,"
    if not letter["closing"]:
        letter["closing"] = "Yours faithfully,"
    if not letter["date"]:
        letter["date"] = dt.date.today().strftime("%d.%m.%Y")
        notes.append("No letter date given - today's date used.")

    for k in ("key_facts",):
        if not isinstance(letter.get(k), dict):
            letter[k] = {"details": letter.get(k)} if letter.get(k) else {}
    for k in ("legal_citations", "deadlines", "source_documents"):
        v = letter.get(k)
        letter[k] = [x if isinstance(x, dict) else {"provision" if k == "legal_citations" else "event": str(x)}
                     for x in _as_list(v)]
    return letter, notes


def iter_text(letter: dict):
    """Yield (field, text) for every human-readable string in the letter."""
    for k in ("file_no", "din", "date", "through", "kind_attention", "subject", "salutation", "closing"):
        if letter.get(k):
            yield k, letter[k]
    for i, a in enumerate(letter.get("to", []), 1):
        for f in ("name", "designation", "organisation", "gstin", "email"):
            if a.get(f):
                yield f"to[{i}].{f}", a[f]
        for line in a.get("address_lines", []):
            yield f"to[{i}].address", line
    for i, r in enumerate(letter.get("references", []), 1):
        yield f"references[{i}]", r
    for i, p in enumerate(letter.get("body_paragraphs", []), 1):
        if isinstance(p, str):
            yield f"para {i}", p
        elif "table" in p:
            t = p["table"]
            yield f"para {i} (table)", " | ".join(t.get("headers", []))
            for row in t.get("rows", []):
                yield f"para {i} (table)", " | ".join(row)
        else:
            yield f"para {i}", p.get("text", "")
            for j, pt in enumerate(p.get("points", []), 1):
                yield f"para {i}({j})", pt
    for k in ("enclosures", "copy_to"):
        for i, x in enumerate(letter.get(k, []), 1):
            yield f"{k}[{i}]", x
    for k, v in (letter.get("signatory") or {}).items():
        if v:
            yield f"signatory.{k}", v
