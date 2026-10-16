"""HTML previews for Colab output: the letter, the check report and citation table."""
from __future__ import annotations

import html

from .docx_writer import ROMAN
from .schema import format_date

LEVEL_STYLE = {"ERROR": ("#b00020", "#fdecea", "⛔"), "WARN": ("#8a5300", "#fff4e0", "⚠️"),
               "INFO": ("#0b5394", "#e8f0fe", "ℹ️")}


def e(x) -> str:
    return html.escape(str(x or "")).replace("\n", "<br>")


def issues_html(issues: list[dict], title="Automatic checks") -> str:
    if not issues:
        return f"<div style='padding:8px;background:#e6f4ea;border-radius:6px'>✅ <b>{title}:</b> no problems found.</div>"
    rows = []
    for i in issues:
        fg, bg, icon = LEVEL_STYLE.get(i["level"], ("#333", "#eee", "•"))
        rows.append(f"<tr style='background:{bg}'><td style='color:{fg};font-weight:bold;white-space:nowrap'>"
                    f"{icon} {i['level']}</td><td style='white-space:nowrap'>{e(i['where'])}</td>"
                    f"<td>{e(i['msg'])}</td></tr>")
    return (f"<div style='font-family:Arial,sans-serif;font-size:13px'><b>{title}</b>"
            f"<table style='border-collapse:collapse;width:100%;margin-top:4px' cellpadding='4'>"
            + "".join(rows) + "</table></div>")


def citations_html(cites: list[dict]) -> str:
    if not cites:
        return ""
    colour = {"ok": "#1e7e34", "no_act": "#0b5394", "unknown": "#8a5300", "error": "#b00020"}
    rows = "".join(
        f"<tr><td><b>{e(c['kind'].title())} {e(c['number'])}{e(c['sub'])}</b></td><td>{e(c['act'])}</td>"
        f"<td style='color:{colour.get(c['status'], '#333')}'>{e(c['title'])}"
        f"{' <i>(recently amended - verify)</i>' if c.get('verify') else ''}</td></tr>" for c in cites)
    return ("<div style='font-family:Arial,sans-serif;font-size:13px;margin-top:8px'><b>Provisions cited in the letter"
            "</b> (quick reference - always confirm with the bare Act)<table cellpadding='4' style='border-collapse:"
            "collapse;width:100%' border='1'><tr style='background:#f1f3f4'><th>Citation</th><th>Act</th>"
            f"<th>Meaning / status</th></tr>{rows}</table></div>")


def letter_html(letter: dict, theme: dict) -> str:
    font = theme.get("font", "Times New Roman")
    size = theme.get("size", 12)
    L = theme.get("labels", {})
    date = format_date(letter.get("date"), theme.get("date_style", "%d.%m.%Y"))
    out = [f"<div style=\"font-family:'{font}',serif;font-size:{size}pt;line-height:{theme.get('line_spacing', 1.15)};"
           "max-width:720px;background:#fff;color:#000;padding:28px 36px;border:1px solid #ccc;"
           "box-shadow:0 1px 4px rgba(0,0,0,.15)\">",
           "<div style='text-align:center;color:#888;border-bottom:2px solid #000;padding-bottom:4px;"
           "margin-bottom:10px'>[ letterhead ]</div>",
           f"<div style='display:flex;justify-content:space-between'><span>{e(L.get('file_no', 'F.No.'))} "
           f"{e(letter.get('file_no'))}</span><span>{e(L.get('date', 'Date:'))} {e(date)}</span></div>"]
    if letter.get("din"):
        out.append(f"<div><b>{e(L.get('din', 'DIN:'))} {e(letter['din'])}</b></div>")
    out.append(f"<p>{e(L.get('to', 'To,'))}<br>")
    for a in letter.get("to", []):
        lines = [x for x in (a.get("name"), a.get("designation"), a.get("organisation")) if x]
        lines += a.get("address_lines", [])
        if a.get("gstin"):
            lines.append("GSTIN: " + a["gstin"])
        out.append("<span style='margin-left:24px;display:block'>" + "<br>".join(e(x) for x in lines) + "</span>")
    out.append("</p>")
    if letter.get("through"):
        out.append(f"<p>{e(L.get('through', 'Through:'))} {e(letter['through'])}</p>")
    sal = f"<p>{e(theme.get('salutation_override') or letter.get('salutation'))}</p>"
    if theme.get("salutation_position") == "before_subject":
        out.append(sal)
    sub_style = ("font-weight:bold;" if theme.get("subject_bold", True) else "") + \
                ("text-decoration:underline;" if theme.get("subject_underline") else "")
    out.append(f"<div style='display:flex;margin:8px 0;{sub_style}'><span style='min-width:80px'>"
               f"{e(L.get('subject', 'Sub:'))}</span><span>{e(letter.get('subject'))}</span></div>")
    for i, r in enumerate(letter.get("references", []), 1):
        lab = L.get("reference", "Ref:") if i == 1 else ""
        num = f"{i}.&nbsp;" if len(letter["references"]) > 1 else ""
        out.append(f"<div style='display:flex'><span style='min-width:80px'>{e(lab)}</span>"
                   f"<span>{num}{e(r)}</span></div>")
    if theme.get("salutation_position") != "before_subject":
        out.append(sal)
    n = 0
    mode = theme.get("para_numbering", "all")
    align = "justify" if theme.get("justify", True) else "left"
    for p in letter.get("body_paragraphs", []):
        if isinstance(p, dict) and "table" in p:
            t = p["table"]
            cap = f"<caption style='font-weight:bold;text-align:left'>{e(t.get('caption'))}</caption>" \
                if t.get("caption") else ""
            head = "".join(f"<th style='border:1px solid #000;padding:3px'>{e(h)}</th>" for h in t.get("headers", []))
            body = "".join("<tr>" + "".join(f"<td style='border:1px solid #000;padding:3px'>{e(c)}</td>" for c in r)
                           + "</tr>" for r in t.get("rows", []))
            out.append(f"<table style='border-collapse:collapse;margin:6px auto;font-size:{size - 1}pt'>{cap}"
                       f"<tr>{head}</tr>{body}</table>")
            continue
        n += 1
        num = f"{n}.&nbsp;&nbsp;" if mode == "all" or (mode == "from_second" and n > 1) else ""
        text = p if isinstance(p, str) else p.get("text", "")
        out.append(f"<p style='text-align:{align};text-indent:{theme.get('first_line_indent', 1.27)}cm'>"
                   f"{num}{e(text)}</p>")
        if isinstance(p, dict):
            for j, pt in enumerate(p.get("points", [])):
                rn = ROMAN[j] if j < len(ROMAN) else str(j + 1)
                out.append(f"<p style='margin-left:2.2cm;text-indent:-0.8cm;text-align:{align}'>({rn}) {e(pt)}</p>")
    sig = letter.get("signatory", {})
    side = "margin-left:55%" if theme.get("signature_align", "right") == "right" else ""
    name = sig.get("name", "")
    if name and theme.get("name_uppercase"):
        name = name.upper()
    if name and theme.get("name_in_brackets", True):
        name = f"({name})"
    out.append(f"<div style='{side};margin-top:10px'>{e(theme.get('closing_override') or letter.get('closing'))}"
               f"<br><br><br><b>{e(name)}</b><br>{e(sig.get('designation'))}<br>{e(sig.get('office_line'))}</div>")
    if letter.get("enclosures"):
        out.append(f"<p><b>{e(L.get('encl', 'Encl.:'))}</b> " + "; ".join(e(x) for x in letter["enclosures"]) + "</p>")
    if letter.get("copy_to"):
        out.append(f"<p><b>{e(L.get('copy_to', 'Copy to:'))}</b></p><ol>" +
                   "".join(f"<li>{e(x)}</li>" for x in letter["copy_to"]) + "</ol>")
    out.append("</div>")
    return "".join(out)
