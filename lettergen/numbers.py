"""Indian number formatting (12,34,567) and amount-in-words (Rupees ... Lakh ... only)."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
         "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
         "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def parse_amount(value) -> Decimal | None:
    """'₹12,34,567/-', 'Rs. 1,234.50', 12345 -> Decimal. Returns None if not a number."""
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    s = str(value)
    s = re.sub(r"(?i)(rs\.?|inr|₹|/-|\s)", "", s)
    s = s.replace(",", "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def indian_format(value, decimals: bool | None = None) -> str:
    """1234567 -> '12,34,567'; 1234.5 -> '1,234.50'."""
    d = parse_amount(value)
    if d is None:
        return str(value)
    neg = d < 0
    d = abs(d)
    whole = int(d)
    frac = d - whole
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = f"{head},{tail}"
    if decimals or (decimals is None and frac):
        s += f".{int((frac * 100).quantize(Decimal('1'))):02d}"
    return ("-" if neg else "") + s


def _two(n: int) -> str:
    if n < 20:
        return _ONES[n]
    return (_TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else "")).strip()


def _three(n: int) -> str:
    h, r = divmod(n, 100)
    parts = []
    if h:
        parts.append(_ONES[h] + " Hundred")
    if r:
        parts.append(("and " if h else "") + _two(r))
    return " ".join(parts)


def words_indian(n: int) -> str:
    """12345678 -> 'One Crore Twenty Three Lakh Forty Five Thousand Six Hundred and Seventy Eight'."""
    if n == 0:
        return "Zero"
    parts = []
    crore, n = divmod(n, 10_000_000)
    lakh, n = divmod(n, 100_000)
    thousand, n = divmod(n, 1000)
    if crore:
        parts.append(words_indian(crore) + " Crore")
    if lakh:
        parts.append(_two(lakh) + " Lakh")
    if thousand:
        parts.append(_two(thousand) + " Thousand")
    if n:
        parts.append(_three(n))
    return " ".join(parts)


def rupees_in_words(value) -> str:
    d = parse_amount(value)
    if d is None:
        return ""
    whole = int(abs(d))
    paise = int(((abs(d) - whole) * 100).quantize(Decimal("1")))
    s = f"Rupees {words_indian(whole)}"
    if paise:
        s += f" and Paise {_two(paise)}"
    return s + " only"


def rupees(value, with_words: bool = False) -> str:
    """-> '₹12,34,567/- (Rupees Twelve Lakh ... only)'."""
    d = parse_amount(value)
    if d is None:
        return str(value)
    s = f"₹{indian_format(d)}/-"
    if with_words:
        s += f" ({rupees_in_words(d)})"
    return s


def normalise_words(text: str) -> str:
    t = text.lower().replace("-", " ")
    t = re.sub(r"\b(rupees|rupee|only|and|rs)\b", " ", t)
    t = t.replace("lakhs", "lakh").replace("crores", "crore")
    return re.sub(r"[^a-z]+", " ", t).strip()
