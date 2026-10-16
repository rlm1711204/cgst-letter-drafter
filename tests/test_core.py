import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lettergen import builders, checks, config, legal, numbers, parser, prompts, schema, themes  # noqa: E402

EXAMPLES = sorted((ROOT / "examples").glob("*.json"))
PROFILE = dict(config.DEFAULT_PROFILE, signatory_name="Test Officer", signatory_designation="Superintendent")
TODAY = dt.date(2026, 10, 16)


def load(name):
    raw, _ = parser.extract_json((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8"))
    letter, _ = schema.normalise(raw, PROFILE)
    return letter


# ---------------------------------------------------------------- parser
def test_parser_handles_notebooklm_noise():
    text = 'Here is the JSON [1]\n```json\n{"subject": "Test [2] - reg.", "body": "Para one [3, 4].",}\n```\nDone'
    data, notes = parser.extract_json(text)
    assert data["subject"] == "Test - reg."
    assert data["body"] == "Para one."
    assert notes


def test_parser_error_is_helpful():
    with pytest.raises(parser.ParseError):
        parser.extract_json("no json here at all")


# ---------------------------------------------------------------- numbers
@pytest.mark.parametrize("n,fmt,words", [
    (825000, "8,25,000", "Rupees Eight Lakh Twenty Five Thousand only"),
    (1234567, "12,34,567", "Rupees Twelve Lakh Thirty Four Thousand Five Hundred and Sixty Seven only"),
    (10_00_00_000, "10,00,00,000", "Rupees Ten Crore only"),
    (999, "999", "Rupees Nine Hundred and Ninety Nine only"),
])
def test_indian_numbers(n, fmt, words):
    assert numbers.indian_format(n) == fmt
    assert numbers.rupees_in_words(n) == words


# ---------------------------------------------------------------- GSTIN
def test_gstin_checksum_known_valid():
    assert checks.validate_gstin("27AAPFU0939F1ZV") is None
    assert checks.validate_gstin("29AAGCB7383J1Z4") is None


def test_gstin_typo_detected():
    assert "Check digit" in checks.validate_gstin("27AAPFU0939F1ZA")
    assert checks.validate_gstin("27AAPFU0939F1Z") is not None


# ---------------------------------------------------------------- normalise
def test_normalise_aliases_and_numbering():
    raw = {"type": "SCN", "sub": "X - reg.", "addressee": "M/s A\nStreet\nTown", "body": ["1. First", "2. Second"],
           "cc": "Office copy"}
    letter, _ = schema.normalise(raw, PROFILE)
    assert letter["letter_type"] == "scn_adjudication"
    assert letter["to"][0]["address_lines"] == ["M/s A", "Street", "Town"]
    assert letter["body_paragraphs"] == ["First", "Second"]
    assert letter["copy_to"] == ["Office copy"]
    assert letter["signatory"]["name"] == "Test Officer"


# ---------------------------------------------------------------- checks
@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_examples_have_no_errors(path):
    letter = load(path.stem)
    errs = [i for i in checks.run_checks(letter, PROFILE, today=TODAY) if i["level"] == "ERROR"]
    assert not errs, errs


def _levels(letter):
    return [(i["level"], i["msg"]) for i in checks.run_checks(letter, PROFILE, today=TODAY)]


def test_missing_din_on_taxpayer_letter_is_error():
    letter = load("taxpayer")
    letter["din"] = ""
    assert any(lv == "ERROR" and "DIN" in m for lv, m in _levels(letter))


def test_section_73_for_fy_2024_25_warns():
    letter = load("scn_adjudication")
    letter["body_paragraphs"].append("The demand is proposed under Section 73 of the CGST Act, 2017 for 2024-25.")
    assert any("74A" in m for lv, m in _levels(letter))


def test_section_74A_for_old_years_warns():
    letter = load("court_writ")
    letter["body_paragraphs"].append("Section 74A of the CGST Act, 2017 is invoked for 2019-20.")
    assert any("74A applies" in m for lv, m in _levels(letter))


def test_wrong_amount_in_words_is_error():
    letter = load("appeal_review")
    letter["body_paragraphs"].append("An amount of ₹8,25,000/- (Rupees Eight Lakh Fifty Thousand only) is involved.")
    assert any(lv == "ERROR" and "words" in m for lv, m in _levels(letter))


def test_bad_table_total_is_error():
    letter = load("admin")
    letter["body_paragraphs"][1]["table"]["rows"][-1][1] = "61"
    assert any(lv == "ERROR" and "Total" in m for lv, m in _levels(letter))


def test_impossible_date_and_bad_section_number():
    letter = load("admin")
    letter["body_paragraphs"].append("Hearing on 31.06.2026 under Section 199 of the CGST Act, 2017.")
    msgs = _levels(letter)
    assert any(lv == "ERROR" and "Impossible date" in m for lv, m in msgs)
    assert any(lv == "ERROR" and "174 sections" in m for lv, m in msgs)


def test_limitation_107_2():
    rows = legal.limitation_table("30.07.2026", "04.08.2026")
    r = next(r for r in rows if "107(2)" in r["provision"])
    assert r["last_date"] == dt.date(2027, 2, 4)
    r = next(r for r in rows if "112(3)" in r["provision"])
    assert r["last_date"] == dt.date(2027, 1, 30)


def test_citation_scan_multiple():
    c = legal.scan_citations("under Sections 73 and 74 of the CGST Act, 2017 read with Rule 142(1A) and FORM GST DRC-01A")
    keys = {(x["kind"], x["number"], x["sub"]) for x in c}
    assert ("section", "73", "") in keys and ("section", "74", "") in keys
    assert ("rule", "142", "(1A)") in keys
    assert ("form", "DRC-01A", "") in keys


# ---------------------------------------------------------------- builders
@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_build_all_modes(path, tmp_path):
    letter = load(path.stem)
    th = themes.resolve("CBIC Classic")
    tdir = ROOT / "templates"
    outs = {
        "theme": builders.generate(letter, th, PROFILE, mode="theme", letterhead_image=tdir / "sample_letterhead.png"),
        "text": builders.generate(letter, th, PROFILE, mode="theme"),
        "clone": builders.generate(letter, th, PROFILE, mode="clone",
                                   template_path=tdir / "sample_letter_for_clone_demo.docx"),
        "placeholder": builders.generate(letter, th, PROFILE, mode="auto",
                                         template_path=tdir / "CBIC_placeholder_template.docx"),
    }
    for name, (doc, rep) in outs.items():
        out = tmp_path / f"{name}.docx"
        doc.save(str(out))
        text = builders.docx_text(out)
        assert letter["subject"][:40] in text.replace("\n", " "), name
        assert "{{" not in text and "{%" not in text, name
        if name == "clone":
            assert "old body paragraph" not in text
            assert rep["kept_blocks"] == 1


def test_clone_detects_sample_style():
    rep = builders.analyze_sample(ROOT / "templates" / "sample_letter_for_clone_demo.docx")
    d = rep["detected"]
    assert d["font"] == "Bookman Old Style"
    assert d["labels"]["file_no"] == "C.No."
    assert d["labels"]["subject"] == "Subject:"
    assert d["salutation_position"] == "before_subject"
    assert d["para_numbering"] == "all"


def test_bilingual_theme_labels():
    th = themes.resolve("Bilingual (Hindi-English)")
    assert th["labels"]["subject"].startswith("विषय")


# ---------------------------------------------------------------- prompts
def test_prompts_fill_all_placeholders():
    p = prompts.notebooklm_prompt("Appeal / Review (OIO / OIA)", "do X", PROFILE, "16.10.2026")
    assert "{{" not in p and "Section 107(2)" in p
    letter = load("appeal_review")
    v = prompts.verification_prompt(letter, "LETTER", [], legal.scan_citations("Section 107(2) of the CGST Act"), "x")
    assert "{{" not in v and "LETTER" in v
    assert "{{" not in prompts.fact_check_prompt("abc")


def test_data_files_are_valid_json():
    for f in (ROOT / "data").glob("*.json"):
        json.loads(f.read_text(encoding="utf-8"))
