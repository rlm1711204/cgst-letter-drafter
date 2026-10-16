"""Automatic pre-issue checks. Each issue = {'level': ERROR|WARN|INFO, 'where': str, 'msg': str}."""
from __future__ import annotations

import datetime as dt
import re

from . import legal
from .config import load_data
from .numbers import indian_format, normalise_words, parse_amount, rupees_in_words, words_indian
from .schema import PLACEHOLDER_RE, iter_text, parse_date

GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_LOOSE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]{3}\b")
DATE_IN_TEXT = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")
AMOUNT_RE = re.compile(r"(?:₹|Rs\.?|INR)\s?([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:/-)?(?:\s*\(([^)]*?only)\s*\))?", re.I)
WESTERN_GROUPING = re.compile(r"^\d{1,3}(,\d{3}){2,}(\.\d+)?$")
STATE_CODES = set(range(1, 39)) | {97, 99}


def gstin_checksum(g14: str) -> str:
    total = 0
    for i, ch in enumerate(g14):
        v = GSTIN_CHARS.index(ch) * (1 if i % 2 == 0 else 2)
        total += v // 36 + v % 36
    return GSTIN_CHARS[(36 - total % 36) % 36]


def validate_gstin(g: str) -> str | None:
    """None if valid, else a reason."""
    g = (g or "").strip().upper()
    if len(g) != 15:
        return f"GSTIN must have 15 characters (has {len(g)})"
    if not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z][A-Z0-9][0-9A-Z]", g):
        return "GSTIN pattern is wrong (expected 2 digits + PAN + entity no. + Z + check digit)"
    if int(g[:2]) not in STATE_CODES:
        return f"State code {g[:2]} is not valid"
    if any(ch not in GSTIN_CHARS for ch in g):
        return "GSTIN has invalid characters"
    exp = gstin_checksum(g[:14])
    if g[14] != exp:
        return f"Check digit fails (last character should be '{exp}', not '{g[14]}') - likely a typo"
    return None


def _issue(level, where, msg):
    return {"level": level, "where": where, "msg": msg}


def run_checks(letter: dict, profile: dict | None = None, today: dt.date | None = None,
               required: bool = True, din_required: bool | None = None) -> list[dict]:
    """required=False skips letter-layout checks (used for SOP / other formats).
    din_required overrides the letter-type rule."""
    profile = profile or {}
    today = today or dt.date.today()
    issues: list[dict] = []
    types = load_data("letter_types").get("letter_types", {})
    lt = letter.get("letter_type", "")
    tinfo = dict(types.get(lt, {}))
    if din_required is not None:
        tinfo["din_required"] = din_required
    if lt and lt not in types:
        issues.append(_issue("WARN", "letter_type", f"Unknown letter type '{lt}'. Known: {', '.join(types)}"))

    # ---- required fields -------------------------------------------------
    if not required:
        pass
    elif not letter.get("subject"):
        issues.append(_issue("ERROR", "subject", "Subject is empty."))
    if required:
        if not letter.get("to"):
            issues.append(_issue("ERROR", "to", "No addressee given."))
        if not letter.get("body_paragraphs"):
            issues.append(_issue("ERROR", "body", "Letter body is empty."))
        if not letter.get("file_no"):
            issues.append(_issue("WARN", "file_no", "File No. is empty - add the e-Office / file number."))
        sig = letter.get("signatory", {})
        if not sig.get("name"):
            issues.append(_issue("WARN", "signatory", "Signatory name is empty - add it (quick edit box) or in "
                                                      "the profile."))
        if not sig.get("designation"):
            issues.append(_issue("WARN", "signatory", "Signatory designation is empty (set it in the office "
                                                      "profile)."))

    # ---- date ------------------------------------------------------------
    d = parse_date(letter.get("date"))
    if letter.get("date") and d is None:
        issues.append(_issue("ERROR", "date", f"Letter date '{letter['date']}' could not be read. Use DD.MM.YYYY."))
    elif d and d > today + dt.timedelta(days=7):
        issues.append(_issue("WARN", "date", f"Letter date {d:%d.%m.%Y} is in the future."))
    elif d and (today - d).days > 30:
        issues.append(_issue("INFO", "date", f"Letter date {d:%d.%m.%Y} is more than 30 days old - intended?"))

    # ---- DIN ---------------------------------------------------------------
    din = (letter.get("din") or "").strip()
    to_taxpayer = tinfo.get("din_required") if din_required is not None else (
        any(a.get("gstin") for a in letter.get("to", [])) or tinfo.get("din_required"))
    if not din and to_taxpayer:
        issues.append(_issue("ERROR", "din", "No DIN. Communications to taxpayers must carry a DIN generated on "
                                             "the CBIC DDM portal (Circular No. 122/41/2019-GST dated 05.11.2019); "
                                             "without it the communication is treated as invalid."))
    elif din and not PLACEHOLDER_RE.search(din):
        core = re.sub(r"(?i)^CBIC-?DIN-?", "", din).replace(" ", "")
        if not re.fullmatch(r"[0-9A-Z]{16,24}", core.upper()):
            issues.append(_issue("WARN", "din", f"DIN '{din}' has an unusual format - verify on the CBIC DIN "
                                                "verification utility."))
    elif din:
        issues.append(_issue("WARN", "din", "DIN is still a placeholder - generate it before issue."))

    # ---- walk all text -------------------------------------------------
    all_text = []
    for where, text in iter_text(letter):
        all_text.append(text)
        for m in PLACEHOLDER_RE.finditer(text):
            issues.append(_issue("WARN", where, f"Placeholder to fill: {m.group(0)}"))
        for m in DATE_IN_TEXT.finditer(text):
            dd, mm, yy = map(int, m.groups())
            try:
                dt.date(yy, mm, dd)
            except ValueError:
                issues.append(_issue("ERROR", where, f"Impossible date '{m.group(0)}'."))
        for m in AMOUNT_RE.finditer(text):
            num, words = m.group(1), m.group(2)
            if WESTERN_GROUPING.match(num):
                issues.append(_issue("INFO", where, f"Amount {num} uses western grouping; Indian style is "
                                                    f"{indian_format(num)}."))
            if words:
                amt = parse_amount(num)
                if amt is not None and normalise_words(words) != normalise_words(rupees_in_words(amt)):
                    issues.append(_issue("ERROR", where, f"Amount in words does not match ₹{indian_format(amt)}. "
                                                         f"Should be: ({rupees_in_words(amt)})"))
    full = "\n".join(all_text)
    kf_text = " ".join(str(v) for v in (letter.get("key_facts") or {}).values())

    # ---- GSTINs --------------------------------------------------------------
    gstins = {a.get("gstin") for a in letter.get("to", []) if a.get("gstin")}
    gstins |= set(GSTIN_LOOSE.findall(full)) | set(GSTIN_LOOSE.findall(kf_text.upper()))
    home = str(profile.get("home_state_code") or "")
    for g in sorted(gstins):
        why = validate_gstin(g)
        if why:
            issues.append(_issue("ERROR", "GSTIN", f"{g}: {why}."))
        elif home and g[:2] != home:
            issues.append(_issue("INFO", "GSTIN", f"{g} is registered in state code {g[:2]}, "
                                                  f"not your home state {home}."))

    # ---- tables: totals ------------------------------------------------------
    for i, p in enumerate(letter.get("body_paragraphs", []), 1):
        if isinstance(p, dict) and "table" in p:
            issues += _check_table_total(p["table"], f"para {i} (table)")

    # ---- citations -------------------------------------------------------------
    cites = legal.scan_citations(full)
    for c in cites:
        label = f"{c['kind'].title()} {c['number']}{c['sub']}"
        if c["status"] == "error":
            issues.append(_issue("ERROR", "citation", f"{label}: {c['title']}"))
        elif c["status"] == "no_act":
            issues.append(_issue("INFO", "citation", f"{label} - name the Act in full at first mention "
                                                     f"(e.g. 'of the CGST Act, 2017')."))
    fys = legal.financial_years(full + " " + kf_text)
    for level, msg in legal.fy_rules(cites, fys):
        issues.append(_issue(level, "citation", msg))
    demand_secs = {c["number"] for c in cites if c["kind"] == "section"} & {"73", "74", "74A"}
    if demand_secs and fys:
        for row in legal.demand_time_limits(fys, today):
            if "section" not in row:
                issues.append(_issue("INFO", "time limit", f"FY {row['fy']}: {row['note']}"))
            elif row["section"] in demand_secs or (row["section"] == "73" and "74" in demand_secs):
                when = f"SCN by {row['scn_last_date']:%d.%m.%Y}"
                if row.get("order_last_date"):
                    when += f", order by {row['order_last_date']:%d.%m.%Y}"
                lvl = "WARN" if row["scn_expired"] else "INFO"
                msg = (f"FY {row['fy']} under Section {row['section']}: {when} (annual return due "
                       f"{row['annual_return_due']:%d.%m.%Y}; ignores any extension - verify).")
                if row["scn_expired"]:
                    msg = "TIME LIMIT PASSED - " + msg
                    if row["section"] == "73":
                        msg += " Only Section 74 (fraud / wilful misstatement / suppression) would remain available."
                issues.append(_issue(lvl, "time limit", msg))
    for c in letter.get("legal_citations", []):
        if str(c.get("basis", "")).lower().startswith("sugg"):
            issues.append(_issue("WARN", "citation", f"'{c.get('provision', '')}' was SUGGESTED by AI (not in the "
                                                     "source) - confirm before issue."))

    # ---- monetary limit (department appeals) ---------------------------------
    if lt == "appeal_review":
        kf = letter.get("key_facts") or {}
        amt = kf.get("amount_in_dispute") or kf.get("amount_involved")
        note = legal.monetary_limit_note(full, amt) if amt else None
        if note:
            issues.append(_issue("WARN", "monetary limit", note))
        od = kf.get("document_date") or kf.get("order_date")
        cd = kf.get("date_of_communication") or kf.get("date_of_receipt")
        is_oia = bool(re.search(r"Order[- ]in[- ]Appeal|\bOIA\b", f"{kf.get('document_no', '')} "
                                                               f"{letter.get('subject', '')}", re.I))
        wanted = "112(3)" if is_oia else "107(2)"
        for row in legal.limitation_table(od, cd):
            if wanted in row["provision"]:
                lvl = "ERROR" if d and d > row["last_date"] else "INFO"
                issues.append(_issue(lvl, "limitation", f"{row['provision']}: last date "
                                                        f"{row['last_date']:%d.%m.%Y} (from {row['counted_from']})."))

    # ---- AI's own uncertainty ------------------------------------------------
    for m in letter.get("missing_or_uncertain", []):
        issues.append(_issue("WARN", "AI flagged", m))

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    issues.sort(key=lambda x: order.get(x["level"], 3))
    return issues


def _check_table_total(t: dict, where: str) -> list[dict]:
    rows = t.get("rows") or []
    if len(rows) < 2:
        return []
    last = rows[-1]
    if not last or not re.search(r"total", str(last[0]), re.I):
        return []
    out = []
    for col in range(1, len(last)):
        vals = [parse_amount(r[col]) if col < len(r) else None for r in rows[:-1]]
        tot = parse_amount(last[col])
        if tot is None or not any(v is not None for v in vals):
            continue
        s = sum(v for v in vals if v is not None)
        if s != tot:
            head = t.get("headers", [])[col] if col < len(t.get("headers", [])) else f"column {col + 1}"
            out.append(_issue("ERROR", where, f"Total of '{head}' is {indian_format(tot)} but rows add up to "
                                              f"{indian_format(s)}."))
    return out


def summary(issues: list[dict]) -> str:
    c = {k: sum(1 for i in issues if i["level"] == k) for k in ("ERROR", "WARN", "INFO")}
    return f"{c['ERROR']} error(s), {c['WARN']} warning(s), {c['INFO']} note(s)"


__all__ = ["run_checks", "validate_gstin", "gstin_checksum", "summary", "words_indian"]
