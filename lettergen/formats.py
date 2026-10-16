"""Document formats other than the generic letter: registry, prompts, normalisation, checks, build."""
from __future__ import annotations

import datetime as dt
import re

from . import checks, legal, prompts, slots
from .config import PROMPTS_DIR, TEMPLATES_DIR, load_data
from .schema import format_date, parse_date

FORMAT_DIR = TEMPLATES_DIR / "formats"
_NUM_PREFIX = re.compile(r"^\s*(?:\d{1,2}[.)]|\(\d{1,2}\)|\([ivx]{1,5}\))\s*\t?\s*", re.I)


def registry() -> dict:
    return load_data("formats").get("formats", {})


def labels() -> dict:
    return {k: v["label"] for k, v in registry().items()}


def key_for(label_or_key: str) -> str:
    for k, v in registry().items():
        if label_or_key in (k, v["label"]):
            return k
    return "letter"


def detect(raw: dict) -> str:
    f = str(raw.get("format") or raw.get("document_format") or "").strip().lower()
    if f in registry():
        return f
    keys = set(raw)
    if {"modus_operandi", "brief_facts"} & keys and ({"registration", "jurisdiction"} & keys):
        return "sop_checklist"
    if {"notesheet_body", "notesheet_subject", "letter_body"} & keys:
        return "letter_notesheet"
    return "letter"


# =========================================================================== prompts
def prompt(fmt: str, instruction: str, profile: dict, letter_date: str = "", file_no: str = "",
           din: str = "") -> str:
    cfg = registry()[fmt]
    sig = ", ".join(x for x in (profile.get("signatory_name"), profile.get("signatory_designation")) if x)
    return prompts.fill(prompts.load(cfg["prompt"]),
                        INSTRUCTION=instruction.strip() or "[describe the purpose]",
                        FROM_OFFICE=prompts.office_line(profile) or "[my office]",
                        SIGNATORY=sig or "leave blank (signature space kept)",
                        LETTER_DATE=letter_date or dt.date.today().strftime("%d.%m.%Y"),
                        FILE_NO=file_no, DIN=din,
                        FILE_NO_SHOW=file_no or "not given - leave \"\"",
                        DIN_SHOW=din or "not yet generated - leave \"\"",
                        TODAY=dt.date.today().strftime("%d.%m.%Y"))


# =========================================================================== normalisation
SOP_FIELDS = ["registration", "registration_status", "jurisdiction", "centre", "state", "prior_action",
              "tax_paying_pattern", "cash_credit_ratio", "hsn_sac", "tax_rates", "exemptions", "goods_services",
              "intelligence_sources", "detection_registered", "detection_unregistered", "enforcement_sec_22_24",
              "modus_operandi", "brief_facts", "expected_evasion_lakhs", "mode_of_investigation"]
SOP_ROW = {k: i for i, k in enumerate(SOP_FIELDS, 1)}


def _txt(v) -> str:
    return slots.as_text(v).strip()


def _blocks(items, first_style, other_style, item_style="item"):
    out = []
    for i, it in enumerate(items or []):
        if isinstance(it, str):
            out.append({"style": first_style if (i == 0 and first_style) else other_style,
                        "text": _NUM_PREFIX.sub("", it).strip()})
            continue
        it = dict(it)
        style = it.get("style") or (first_style if (i == 0 and first_style) else other_style)
        text = _NUM_PREFIX.sub("", str(it.get("text", ""))).strip()
        if text:
            out.append({"style": style, "text": text})
        for sub in it.get("list") or it.get("items") or it.get("points") or []:
            out.append({"style": item_style, "text": _NUM_PREFIX.sub("", _txt(sub)).strip()})
    return out


def _to_lines(raw) -> list[str]:
    to = raw.get("to_lines") or raw.get("to") or raw.get("addressee") or []
    if isinstance(to, str):
        return [x.strip() for x in to.split("\n") if x.strip()]
    if isinstance(to, dict):
        to = [to]
    lines = []
    for a in to:
        if isinstance(a, str):
            lines.append(a)
            continue
        if a.get("name"):
            lines.append(a["name"])
        ids = " / ".join(x for x in (f"GSTIN: {a['gstin']}" if a.get("gstin") else "",
                                     f"PAN: {a['pan']}" if a.get("pan") else "") if x)
        if ids:
            lines.append(f"({ids})")
        addr = a.get("address_lines") or a.get("address") or []
        lines += [addr] if isinstance(addr, str) else list(addr)
    return [str(x) for x in lines if str(x).strip()]


def normalise(fmt: str, raw: dict, profile: dict | None = None) -> tuple[dict, list[str]]:
    profile = profile or {}
    notes: list[str] = []
    d = dict(raw)
    d["format"] = fmt
    if fmt == "sop_checklist":
        for k in list(d):
            if str(k).isdigit() and 1 <= int(k) <= 20:
                d.setdefault(SOP_FIELDS[int(k) - 1], d.pop(k))
        if "center" in d and "centre" not in d:
            d["centre"] = d.pop("center")
        for grp in ("centre", "state"):
            g = d.get(grp) if isinstance(d.get(grp), dict) else {}
            d[grp] = {k: _txt(g.get(k, "")) for k in
                      (("zone", "commissionerate", "division", "range") if grp == "centre" else
                       ("division", "zone", "circle"))}
        for k in SOP_FIELDS:
            if k not in ("centre", "state"):
                d[k] = _txt(d.get(k, ""))
    elif fmt == "letter_notesheet":
        d["to_lines"] = _to_lines(raw)
        d["date"] = format_date(d.get("date"), "%d.%m.%Y") if d.get("date") else ""
        d["letter_body"] = _blocks(raw.get("letter_body") or raw.get("body_paragraphs"), "first", "numbered")
        d["notesheet_body"] = _blocks(raw.get("notesheet_body"), None, "para")
        for k in ("signatory_lines", "notesheet_signatory_lines"):
            v = d.get(k) or []
            d[k] = [v] if isinstance(v, str) else [str(x) for x in v if str(x).strip()]
        if not d["signatory_lines"] and (profile.get("signatory_name") or profile.get("signatory_designation")):
            d["signatory_lines"] = [x for x in (f"({profile['signatory_name']})" if profile.get("signatory_name")
                                                else "", profile.get("signatory_designation", "")) if x]
            notes.append("Signature lines taken from office profile.")
        for k in ("subject", "notesheet_subject", "salutation", "closing", "file_no", "din"):
            d[k] = _txt(d.get(k, ""))
        d["salutation"] = d["salutation"] or "Sir / Madam,"
        d["closing"] = d["closing"] or "Yours faithfully,"
    for k in ("missing_or_uncertain", "legal_citations", "deadlines", "sources_used"):
        v = d.get(k) or []
        d[k] = v if isinstance(v, list) else [v]
    d["key_facts"] = d.get("key_facts") if isinstance(d.get("key_facts"), dict) else {}
    return d, notes


# =========================================================================== context for the template
def context(fmt: str, d: dict) -> dict:
    cfg = registry()[fmt]
    if fmt != "letter_notesheet":
        return d
    L = cfg.get("labels", {})
    file_line = ""
    if d.get("file_no") or d.get("date"):
        left = f"{L.get('file_no', 'C.No.')} {d.get('file_no', '')}".strip() if d.get("file_no") else ""
        right = f"{L.get('date', 'Date:')} {d['date']}" if d.get("date") else ""
        file_line = f"{left}\t{right}" if right else left
    return dict(d, FILE_LINE=file_line,
                DIN_LINE=f"{L.get('din', 'DIN:')} {d['din']}" if d.get("din") else "",
                TO_BLOCK=d.get("to_lines", []), SALUTATION=d.get("salutation"), SUBJECT=d.get("subject"),
                LETTER_BODY=d.get("letter_body"), CLOSING=d.get("closing"),
                SIGNATORY_LINES=d.get("signatory_lines", []), NOTESHEET_SUBJECT=d.get("notesheet_subject"),
                NOTESHEET_BODY=d.get("notesheet_body"),
                NOTESHEET_SIGNATORY_LINES=d.get("notesheet_signatory_lines", []))


def build(fmt: str, d: dict, letterhead: str | None = None, template_override: str | None = None):
    cfg = registry()[fmt]
    tpl = template_override or (FORMAT_DIR / cfg["template"])
    doc = slots.render(tpl, context(fmt, d), images={"LETTERHEAD": letterhead} if letterhead else {},
                       regions=cfg.get("regions", {}))
    cp = doc.core_properties
    cp.title = (d.get("subject") or d.get("notesheet_subject") or cfg["label"])[:250]
    cp.comments = "Generated by CGST Letter Drafter. Verify before issue."
    return doc, {"mode": f"exact format: {cfg['label']}", "template": str(tpl),
                 "letterhead": "image" if letterhead else "none"}


# =========================================================================== checks
def _pseudo_letter(fmt, d):
    if fmt == "sop_checklist":
        body = [f"Row {SOP_ROW[k]}: {_txt(d.get(k))}" for k in SOP_FIELDS if _txt(d.get(k))]
        return {"letter_type": "", "subject": "", "to": [], "body_paragraphs": body, "date": "",
                "key_facts": d.get("key_facts", {}), "legal_citations": d.get("legal_citations", []),
                "missing_or_uncertain": d.get("missing_or_uncertain", [])}
    gst = re.findall(checks.GSTIN_LOOSE, " ".join(d.get("to_lines", [])))
    sig = d.get("signatory_lines") or []
    return {"letter_type": "taxpayer" if registry()[fmt].get("din_required") else "",
            "subject": d.get("subject"), "file_no": d.get("file_no"), "din": d.get("din"), "date": d.get("date"),
            "to": [{"address_lines": d.get("to_lines", []), "gstin": gst[0] if gst else ""}] if d.get("to_lines")
            else [],
            "body_paragraphs": [b["text"] for b in d.get("letter_body", []) + d.get("notesheet_body", [])]
            + ([d["notesheet_subject"]] if d.get("notesheet_subject") else []),
            "signatory": {"name": sig[0] if sig else "", "designation": sig[1] if len(sig) > 1 else "x"},
            "key_facts": d.get("key_facts", {}), "legal_citations": d.get("legal_citations", []),
            "missing_or_uncertain": d.get("missing_or_uncertain", [])}


def run_checks(fmt: str, d: dict, profile: dict | None = None, today=None) -> list[dict]:
    cfg = registry()[fmt]
    pl = _pseudo_letter(fmt, d)
    issues = checks.run_checks(pl, profile, today=today, required=(fmt != "sop_checklist"),
                               din_required=cfg.get("din_required", False))
    add = lambda lvl, where, msg: issues.append({"level": lvl, "where": where, "msg": msg})  # noqa: E731
    if fmt == "sop_checklist":
        blank = [str(SOP_ROW[k]) for k in SOP_FIELDS if k not in ("centre", "state") and not _txt(d.get(k))]
        if blank:
            add("WARN", "rows", "Rows left blank: " + ", ".join(blank) + " (write 'Not applicable' or 'Nil' "
                                                                         "if that is the answer).")
        j = _txt(d.get("jurisdiction")).lower()
        if "cent" in j and not any(d["centre"].values()):
            add("WARN", "row 4", "Jurisdiction is Centre but Zone / Commissionerate / Division / Range are blank.")
        if "state" in j and not any(d["state"].values()):
            add("WARN", "row 5", "Jurisdiction is State but Division / Zone / Circle are blank.")
        reg = _txt(d.get("registration")).lower()
        if reg.startswith("registered") and not re.search(checks.GSTIN_LOOSE, _txt(d.get("registration"))):
            add("ERROR", "row 1", "Registered, but no GSTIN is given in row 1.")
        if "unregistered" in reg and _txt(d.get("detection_registered")) and \
                "not applicable" not in _txt(d.get("detection_registered")).lower():
            add("WARN", "row 14", "Taxpayer is unregistered but row 14 (registered-person detection) is filled.")
    else:
        if not d.get("letter_body"):
            add("ERROR", "letter", "Letter body is empty.")
        if not d.get("notesheet_body"):
            add("ERROR", "notesheet", "Notesheet body is empty.")
        if not d.get("notesheet_subject"):
            add("WARN", "notesheet", "Notesheet subject is empty.")
        for i in issues:
            if i["where"] == "signatory":
                i["level"], i["msg"] = "INFO", "No signature lines - the signature space is left blank, as in " \
                                               "your format."
    if fmt == "sop_checklist":
        rows = [SOP_ROW[k] for k in SOP_FIELDS if _txt(d.get(k))]
        for i in issues:
            m = re.match(r"para (\d+)", i["where"])
            if m and int(m.group(1)) <= len(rows):
                i["where"] = f"row {rows[int(m.group(1)) - 1]}"
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    issues.sort(key=lambda x: order.get(x["level"], 3))
    return issues


def preview_html(doc) -> str:
    """Rough HTML of the generated document (paragraphs and tables in order)."""
    import html
    from docx.oxml.ns import qn
    out = []
    for el in doc.element.body:
        if el.tag == qn("w:p"):
            t = slots.p_text(el)
            has_img = el.find(f".//{qn('w:drawing')}") is not None
            out.append("<div style='color:#888;text-align:center'>[ letterhead ]</div>" if has_img else
                       f"<div>{html.escape(t) or '&nbsp;'}</div>")
        elif el.tag == qn("w:tbl"):
            rows = []
            for tr in el.iter(qn("w:tr")):
                cells = []
                for tc in tr.iter(qn("w:tc")):
                    cells.append("<br>".join(html.escape(slots.p_text(p)) for p in tc.iter(qn("w:p"))))
                rows.append("<tr>" + "".join(f"<td style='border:1px solid #999;padding:3px;vertical-align:top'>"
                                             f"{c}</td>" for c in cells) + "</tr>")
            out.append(f"<table style='border-collapse:collapse;width:100%;font-size:12px'>{''.join(rows)}</table>")
    return ("<div style=\"font-family:'Times New Roman',serif;font-size:13px;max-width:760px;background:#fff;"
            "color:#000;padding:20px;border:1px solid #ccc\">" + "".join(out) + "</div>")


__all__ = ["registry", "labels", "key_for", "detect", "prompt", "normalise", "build", "run_checks",
           "preview_html", "PROMPTS_DIR"]
