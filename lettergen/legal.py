"""Citation scanning against the quick reference, FY-vs-section sanity rules and limitation dates."""
from __future__ import annotations

import datetime as dt
import re

from dateutil.relativedelta import relativedelta

from .config import load_data
from .schema import parse_date

_SEC_RE = re.compile(
    r"\b(?:Sections?|Secs?\.?|u/s\.?|U/s\.?|S\.)\s*(\d{1,3}[A-Z]{0,2})((?:\s*\(\s*[0-9A-Za-z]{1,4}\s*\))*)")
_MORE_RE = re.compile(r"\s*(?:,|and|&|/|or|to)\s*(\d{1,3}[A-Z]{0,2})((?:\s*\(\s*[0-9A-Za-z]{1,4}\s*\))*)")
_RULE_RE = re.compile(r"\bRules?\s*(\d{1,3}[A-Z]{0,2})((?:\s*\(\s*[0-9A-Za-z]{1,4}\s*\))*)")
_FORM_RE = re.compile(r"\b(?:GST\s+|FORM\s+GST\s+)?((?:ASMT|ADT|DRC|APL|REG|RFD|MOV|PMT|CMP|ITC)\s*-\s*\d{2}[A-C]?)\b",
                      re.I)
_FY_RE = re.compile(r"\b(20[12]\d)\s*[-–/]\s*(20)?(\d{2})\b")

ACT_PATTERNS = [
    ("IGST", r"IGST|Integrated Goods"),
    ("UTGST", r"UTGST|Union Territory Goods"),
    ("TNGST", r"TNGST|Tamil Nadu Goods|SGST Act|State Goods"),
    ("CGST", r"CGST|Central Goods and Services|Central Goods & Services"),
    ("RTI", r"Right to Information|RTI Act"),
    ("OTHER", r"Customs Act|Central Excise Act|Finance Act|Finance \(No|Income[- ]tax|Limitation Act|"
              r"General Clauses|Code of Civil|CPC|Cr\.?P\.?C|BNSS|Indian Penal|IPC|Companies Act|"
              r"Constitution|Service Tax|Chapter V"),
]


def _which_act(window: str) -> str:
    best, pos = "UNSPECIFIED", 10 ** 6
    for act, pat in ACT_PATTERNS:
        m = re.search(pat, window, re.I)
        if m and m.start() < pos:
            best, pos = act, m.start()
    return best


def _sub(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def scan_citations(text: str) -> list[dict]:
    """Find statutory citations in text. Each item: kind, number, sub, act, raw, title, verify, status."""
    ref = load_data("legal_reference")
    secs, rules, forms = ref.get("cgst_sections", {}), ref.get("cgst_rules", {}), ref.get("forms", {})
    max_sec = ref.get("cgst_act_max_section", 174)
    out, seen = [], set()

    def add(kind, num, sub, raw, window):
        act = _which_act(window)
        if kind == "rule":
            act = "CGSTR" if act in ("CGST", "UNSPECIFIED", "TNGST") else act
        key = (kind, num.upper(), _sub(sub), act)
        if key in seen:
            return
        seen.add(key)
        item = {"kind": kind, "number": num.upper(), "sub": _sub(sub), "act": act, "raw": raw.strip(),
                "title": "", "verify": False, "status": "ok"}
        base = num.upper()
        if kind == "section":
            if act in ("CGST", "TNGST", "UNSPECIFIED"):
                entry = secs.get(base)
                digits = int(re.match(r"\d+", base).group())
                if entry:
                    item["title"], item["verify"] = entry["title"], entry.get("verify", False)
                elif digits > max_sec:
                    item["status"] = "error"
                    item["title"] = f"The CGST Act, 2017 has only {max_sec} sections - check this number"
                else:
                    item["status"] = "unknown"
                    item["title"] = "Not in quick reference - verify in bare Act"
                if act == "UNSPECIFIED":
                    item["status"] = "no_act" if item["status"] == "ok" else item["status"]
            elif act == "IGST":
                digits = int(re.match(r"\d+", base).group())
                item["title"] = "IGST Act, 2017 provision"
                if digits > 25:
                    item["status"] = "error"
                    item["title"] = "The IGST Act, 2017 has 25 sections - check this number"
            elif act == "RTI":
                key2 = f"RTI {base}{_sub(sub)}"
                item["title"] = ref.get("other_provisions", {}).get(key2) or \
                    ref.get("other_provisions", {}).get(f"RTI {base}", "RTI Act, 2005 provision")
            else:
                item["title"] = "Provision of another enactment - verify"
                item["status"] = "unknown"
        elif kind == "rule":
            entry = rules.get(base)
            if act == "CGSTR" and entry:
                item["title"], item["verify"] = entry["title"], entry.get("verify", False)
            else:
                item["status"] = "unknown"
                item["title"] = "Not in quick reference - verify in the Rules"
        elif kind == "form":
            k = re.sub(r"\s+", "", num.upper())
            item["number"] = k
            item["title"] = forms.get(k, "Form not in quick reference - verify")
            item["status"] = "ok" if k in forms else "unknown"
        out.append(item)

    for m in _SEC_RE.finditer(text):
        window = text[m.end(): m.end() + 120]
        add("section", m.group(1), m.group(2), m.group(0), window)
        pos = m.end()
        while True:
            m2 = _MORE_RE.match(text, pos)
            if not m2:
                break
            window = text[m2.end(): m2.end() + 120]
            add("section", m2.group(1), m2.group(2), m2.group(0), window)
            pos = m2.end()
    for m in _RULE_RE.finditer(text):
        add("rule", m.group(1), m.group(2), m.group(0), text[m.end(): m.end() + 120])
    for m in _FORM_RE.finditer(text):
        add("form", m.group(1), "", m.group(0), "")
    return out


def financial_years(text: str) -> list[int]:
    """'2023-24', 'FY 2024-2025' -> [2023, 2024] (start years). Ignores non-consecutive pairs."""
    years = set()
    for m in _FY_RE.finditer(text):
        start, end = int(m.group(1)), int(m.group(3))
        if (start + 1) % 100 == end:
            years.add(start)
    return sorted(years)


def fy_rules(citations: list[dict], fys: list[int]) -> list[tuple[str, str]]:
    """Return (level, message) tuples for section-vs-period mismatches."""
    issues = []
    if not fys:
        return issues
    nums = {c["number"] for c in citations if c["kind"] == "section" and c["act"] in ("CGST", "TNGST", "UNSPECIFIED")}
    late = [y for y in fys if y >= 2024]
    early = [y for y in fys if y <= 2023]
    if late and ({"73", "74"} & nums):
        issues.append(("WARN", f"Section 73/74 cited, but the period includes FY {late[0]}-{str(late[0] + 1)[2:]}. "
                               "For FY 2024-25 onwards demands are under Section 74A (Finance (No. 2) Act, 2024). "
                               "Confirm the correct section."))
    if early and "74A" in nums:
        issues.append(("WARN", f"Section 74A cited, but the period includes FY {early[0]}-{str(early[0] + 1)[2:]}. "
                               "Section 74A applies to FY 2024-25 onwards; earlier years fall under Section 73/74."))
    if "128A" in nums and any(y > 2019 for y in fys):
        issues.append(("WARN", "Section 128A waiver covers demands under Section 73 for FY 2017-18 to 2019-20 only. "
                               "Check the period."))
    return issues


def limitation_table(order_date=None, communication_date=None) -> list[dict]:
    """Compute statutory last dates. Dates are 'within N months/days from' the base date."""
    ref = load_data("legal_reference")
    od, cd = parse_date(order_date), parse_date(communication_date)
    rows = []
    for r in ref.get("limitation_rules", []):
        base = cd if r["from"] == "communication" else od
        if base is None:
            continue
        if "months" in r:
            last = base + relativedelta(months=r["months"])
        else:
            last = base + dt.timedelta(days=r["days"])
        rows.append({"provision": r["label"], "counted_from": f"{r['from']} {base:%d.%m.%Y}",
                     "last_date": last, "days_left": (last - dt.date.today()).days})
    return rows


MONETARY_LIMITS = [("Supreme Court", 2_00_00_000), ("High Court", 1_00_00_000),
                   ("Tribunal", 20_00_000), ("GSTAT", 20_00_000)]


def monetary_limit_note(text: str, amount) -> str | None:
    """Department appeal monetary limits (Circular 207/1/2024-GST dated 26.06.2024 - verify exceptions)."""
    from .numbers import parse_amount, indian_format
    amt = parse_amount(amount)
    if amt is None:
        return None
    for forum, limit in MONETARY_LIMITS:
        if re.search(forum, text, re.I):
            if amt < limit:
                return (f"Amount ₹{indian_format(amt)} is below the ₹{indian_format(limit)} monetary limit for "
                        f"departmental appeals before the {forum} (Circular No. 207/1/2024-GST dated 26.06.2024). "
                        "File only if an exception in the circular applies.")
            return None
    return None
