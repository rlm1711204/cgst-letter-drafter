"""Colab-facing step functions. Each notebook cell calls one of these. Works outside Colab too
(prints instead of widgets), which is how the test-suite exercises it."""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
import uuid
from pathlib import Path

from . import builders, checks, legal, prompts, register, themes
from .config import EXAMPLES_DIR, TEMPLATES_DIR, Workspace, load_data
from .numbers import indian_format, rupees_in_words
from .parser import ParseError, extract_json
from .preview import citations_html, issues_html, letter_html
from .schema import iter_text, normalise

try:
    from IPython.display import HTML, Markdown, display
except Exception:  # pragma: no cover
    HTML = Markdown = None

    def display(x):
        print(x)

IN_COLAB = False
try:  # pragma: no cover
    import google.colab  # noqa: F401
    IN_COLAB = True
except Exception:
    pass

MODES = {
    "Auto (decide from what I upload)": "auto",
    "Clone my sample letter (.docx)": "clone",
    "Placeholder template (.docx with {{TAGS}})": "placeholder",
    "Letterhead image + theme": "theme_image",
    "Text letterhead from office profile + theme": "theme_text",
}
FROM_SAMPLE = "From my sample letter (auto-detected)"


class Session:
    ws: Workspace | None = None
    letter: dict | None = None
    raw: dict | None = None
    issues: list = []
    citations: list = []
    notes: list = []
    last_docx: Path | None = None
    last_pdf: Path | None = None
    paste_box = None
    edit_box = None
    edit_original = ""
    instruction = ""


S = Session()


# =========================================================================== small UI helpers
_CSS = ("<style>.lgx td,.lgx th{text-align:left !important;vertical-align:top}"
        ".lgx table{margin-left:0 !important}</style>")


def _html(s):
    if HTML is not None:
        display(HTML(f"{_CSS}<div class='lgx'>{s}</div>"))
    else:  # pragma: no cover
        print(re.sub(r"<[^>]+>", "", s))


def copy_box(text: str, title: str, filename: str | None = None, height: int = 220):
    """Read-only text box with Copy and Download buttons."""
    bid = "cb" + uuid.uuid4().hex[:8]
    esc = html.escape(text)
    dl = ""
    if filename:
        import base64
        b64 = base64.b64encode(text.encode("utf-8")).decode()
        dl = (f"<a download='{html.escape(filename)}' href='data:text/plain;charset=utf-8;base64,{b64}' "
              "style='margin-left:8px'>⬇️ Download .txt</a>")
    _html(f"""
<div style="font-family:Arial,sans-serif;margin:8px 0;padding:8px;border:1px solid #c6dafc;border-radius:8px;background:#f8fbff">
  <b>{html.escape(title)}</b>
  <button style="margin-left:10px;padding:3px 10px;cursor:pointer" onclick="
    const t=document.getElementById('{bid}'); const b=this;
    const ok=()=>{{b.innerText='✅ Copied'; setTimeout(()=>b.innerText='📋 Copy',2000);}};
    if(navigator.clipboard){{navigator.clipboard.writeText(t.value).then(ok).catch(()=>{{t.select();document.execCommand('copy');ok();}});}}
    else{{t.select();document.execCommand('copy');ok();}}">📋 Copy</button>{dl}
  <span style="color:#666;font-size:12px;margin-left:8px">{len(text):,} characters</span>
  <textarea id="{bid}" readonly style="width:100%;height:{height}px;margin-top:6px;font-family:Consolas,monospace;font-size:12px">{esc}</textarea>
</div>""")


def _say(msg, kind="info"):
    col = {"ok": "#1e7e34", "warn": "#8a5300", "err": "#b00020", "info": "#0b5394"}[kind]
    _html(f"<div style='font-family:Arial,sans-serif;color:{col};margin:4px 0'>{msg}</div>")


def _need_ws():
    if S.ws is None:
        setup(use_drive=False, quiet=True)
    return S.ws


# =========================================================================== step 0: setup
def setup(use_drive: bool = True, quiet: bool = False):
    root = None
    if IN_COLAB and use_drive:  # pragma: no cover
        from google.colab import drive
        if not Path("/content/drive/MyDrive").exists():
            drive.mount("/content/drive")
        root = Path("/content/drive/MyDrive/CGST_Letter_Drafter")
    elif IN_COLAB:  # pragma: no cover
        root = Path("/content/CGST_Letter_Drafter")
    S.ws = Workspace(root)
    if not quiet:
        st = S.ws.settings()
        prof = S.ws.profile()
        _say(f"✅ Ready. Workspace: <code>{S.ws.root}</code>"
             + (" (Google Drive - your settings and letters are kept)" if "drive" in str(S.ws.root)
                else " (temporary - files are lost when the Colab session ends)"), "ok")
        _say(f"Office profile: <b>{html.escape(prompts.office_line(prof) or 'not set')}</b> · "
             f"Signatory: <b>{html.escape(prof.get('signatory_name') or 'not set')}</b> · "
             f"Template mode: <b>{html.escape(st.get('mode_label', 'not set'))}</b> · "
             f"Theme: <b>{html.escape(st.get('theme', themes.BASE))}</b>")
    return S.ws


# =========================================================================== step 1: NotebookLM prompt
def step1_prompt(letter_type: str, instruction: str, letter_date: str = "", file_no: str = "", din: str = ""):
    ws = _need_ws()
    S.instruction = instruction
    ws.save_settings(last_letter_type=letter_type, last_instruction=instruction)
    p = prompts.notebooklm_prompt(letter_type, instruction, ws.profile(), letter_date, file_no, din)
    _say("1️⃣ Upload your source document(s) to NotebookLM. 2️⃣ Copy this prompt and paste it into the "
         "NotebookLM chat. 3️⃣ Copy the whole answer and paste it in Step 5.")
    copy_box(p, "PROMPT 01 → NotebookLM (extract + draft)", "01_notebooklm_prompt.txt", 260)
    copy_box(prompts.load("setup"), "Optional, once per notebook → NotebookLM ▸ Configure chat ▸ Custom",
             None, 110)
    t = load_data("letter_types")["letter_types"].get(prompts.key_for_label(letter_type), {})
    if t.get("example_instructions"):
        _say("Example instructions for this type: " + " · ".join(f"<i>{html.escape(x)}</i>"
                                                                  for x in t["example_instructions"]))
    return p


# =========================================================================== step 2: office profile
def step2_profile(**fields):
    ws = _need_ws()
    prof = ws.profile()
    lines = [x.strip() for x in str(fields.pop("office_lines", "")).split("|") if x.strip()]
    if lines:
        prof["office_lines"] = lines
    for k, v in fields.items():
        if v is not None and str(v).strip() != "":
            prof[k] = str(v).strip()
    ws.save_profile(prof)
    _say("✅ Office profile saved. It fills the text letterhead and signature when NotebookLM leaves them blank.",
         "ok")
    _html("<pre style='background:#f6f6f6;padding:6px'>" + html.escape(json.dumps(prof, indent=2,
                                                                                ensure_ascii=False)) + "</pre>")
    return prof


# =========================================================================== step 3: template
def _upload(dest: Path, exts: tuple) -> Path | None:
    if not IN_COLAB:  # pragma: no cover
        _say("Upload works inside Google Colab only.", "warn")
        return None
    from google.colab import files  # pragma: no cover
    up = files.upload()  # pragma: no cover
    for name, data in up.items():  # pragma: no cover
        if not name.lower().endswith(exts):
            _say(f"Skipped {html.escape(name)} - expected {', '.join(exts)}", "warn")
            continue
        safe = re.sub(r"[^\w.\- ]", "_", name)
        path = dest / safe
        path.write_bytes(data)
        return path
    return None  # pragma: no cover


def step3_template(mode_label: str, upload_new: bool = False, keep_top_blocks: int = -1,
                   file_path: str | None = None):
    ws = _need_ws()
    mode = MODES.get(mode_label, mode_label)
    st = ws.settings()
    path = None
    if mode in ("auto", "clone", "placeholder", "theme_image"):
        exts = (".png", ".jpg", ".jpeg") if mode == "theme_image" else (".docx",)
        if mode == "auto":
            exts = (".docx", ".png", ".jpg", ".jpeg")
        if file_path:
            src = Path(file_path)
            path = ws.templates / src.name
            if src.resolve() != path.resolve():
                shutil.copy(src, path)
        elif upload_new:
            _say(f"Choose your file ({', '.join(exts)}) ...")
            path = _upload(ws.templates, exts)
        else:
            key = "letterhead_path" if mode == "theme_image" else "template_path"
            path = Path(st[key]) if st.get(key) and Path(st[key]).exists() else None
            if path is None:
                path = st.get("template_path") and Path(st["template_path"])
                path = path if path and path.exists() else None
        if path is None and mode != "auto":
            _say("No file yet - tick UPLOAD_NEW_FILE and run this cell again.", "warn")
            return None
    settings = {"mode": mode, "mode_label": mode_label, "keep_top_blocks": int(keep_top_blocks)}
    if path is not None:
        if path.suffix.lower() == ".docx":
            settings["template_path"] = str(path)
        else:
            settings["letterhead_path"] = str(path)
            settings["mode"] = "theme_image"
    ws.save_settings(**settings)
    _say(f"✅ Template setting saved: <b>{html.escape(mode_label)}</b>" +
         (f" · file <code>{html.escape(path.name)}</code>" if path else ""), "ok")
    if path is not None and path.suffix.lower() == ".docx":
        rep = builders.analyze_sample(path)
        ws.save_settings(detected=rep["detected"])
        _show_analysis(rep, settings["keep_top_blocks"], mode)
        return rep
    return settings


def _show_analysis(rep, keep_override, mode):
    if rep["placeholders"]:
        _say("🔖 This file contains <b>{{ TAGS }}</b>: it will be rendered as a <b>placeholder template</b> "
             "(Auto / Placeholder mode).", "ok")
        return
    keep = rep["anchor_index"] if keep_override is None or keep_override < 0 else keep_override
    rows = []
    for el in rep["elements"][:18]:
        kept = el["index"] < keep
        rows.append(f"<tr style='background:{'#e6f4ea' if kept else '#fff'}'><td>{el['index']}</td>"
                    f"<td>{'KEEP (letterhead)' if kept else 'replace'}</td><td>{el['kind']}"
                    f"{' 🖼️' if el['image'] else ''}</td><td>{html.escape(el['text'])}</td></tr>")
    det = rep["detected"]
    _html("<div style='font-family:Arial,sans-serif;font-size:13px'>"
          f"<b>Sample analysis</b> - header images: {rep['header_images']} · margins (cm): {rep['margins_cm']}<br>"
          f"Detected style: font <b>{html.escape(str(det.get('font')))}</b> {det.get('size')} pt · "
          f"line spacing {det.get('line_spacing', '-')} · justify {det.get('justify', '-')} · "
          f"para numbering <b>{det.get('para_numbering', '-')}</b> · signature {det.get('signature_align', '-')} · "
          f"salutation {det.get('salutation_position', '-')}<br>"
          f"Labels found: {html.escape(json.dumps(rep['labels'], ensure_ascii=False))}<br>"
          f"<table border='1' cellpadding='3' style='border-collapse:collapse;margin-top:6px'>"
          f"<tr><th>#</th><th>Action</th><th>Block</th><th>Text</th></tr>{''.join(rows)}</table>"
          "<i>Green rows (your letterhead block) are kept exactly. Everything from the first white row is "
          "replaced by the new letter. If this is wrong, set KEEP_TOP_BLOCKS to the first # to replace.</i></div>")
    for n in rep["notes"]:
        _say("⚠️ " + html.escape(n), "warn")


# =========================================================================== step 4: theme
def theme_choices() -> list[str]:
    ws = _need_ws()
    return [FROM_SAMPLE] + themes.theme_names(ws.user_themes())


DATE_STYLES = {"16.10.2026": "%d.%m.%Y", "16/10/2026": "%d/%m/%Y", "16-10-2026": "%d-%m-%Y",
               "16 October 2026": "%d %B %Y", "October 16, 2026": "%B %d, %Y"}
LABEL_KEYS = {"file_no_label": "file_no", "subject_label": "subject", "ref_label": "reference", "to_label": "to"}


def step4_theme(preset: str, save_as: str = "", **overrides):
    ws = _need_ws()
    clean, labels = {}, {}
    for k, v in overrides.items():
        if v in (None, "", "(theme default)", "(keep)"):
            continue
        if isinstance(v, str) and v.lower() in ("yes", "no"):
            v = v.lower() == "yes"
        elif isinstance(v, str) and v.replace(".", "", 1).isdigit():
            v = float(v) if "." in v else int(v)
        if k == "date_style":
            v = DATE_STYLES.get(v, v)
        if k in LABEL_KEYS:
            labels[LABEL_KEYS[k]] = v
            continue
        clean[k] = v
    if labels:
        clean["labels"] = labels
    ws.save_settings(theme=preset, theme_overrides=clean)
    th = current_theme()
    if save_as.strip():
        ws.save_user_theme(save_as.strip(), {k: v for k, v in th.items() if not k.endswith("_override")})
        _say(f"💾 Saved as your own theme '<b>{html.escape(save_as)}</b>' (appears in the preset list).", "ok")
    _say(f"✅ Theme: <b>{html.escape(preset)}</b> → {html.escape(th.get('font'))} {th.get('size')} pt, "
         f"line spacing {th.get('line_spacing')}, numbering {th.get('para_numbering')}, "
         f"labels {html.escape(th['labels'].get('subject', ''))} / {html.escape(th['labels'].get('file_no', ''))}",
         "ok")
    if S.letter:
        _html(letter_html(S.letter, th))
    return th


def current_theme() -> dict:
    ws = _need_ws()
    st = ws.settings()
    preset = st.get("theme", themes.BASE)
    detected = st.get("detected") if preset == FROM_SAMPLE or (
        st.get("mode") == "clone" and preset == themes.BASE and st.get("detected")) else None
    name = themes.BASE if preset == FROM_SAMPLE else preset
    return themes.resolve(name, st.get("theme_overrides"), ws.user_themes(), detected)


# =========================================================================== step 5: paste & check
def step5_paste_box():
    try:
        import ipywidgets as w
    except Exception:  # pragma: no cover
        _say("ipywidgets not available - use the PASTE_HERE variable in the next cell.", "warn")
        return None
    S.paste_box = w.Textarea(placeholder="Paste the COMPLETE NotebookLM answer here (Ctrl+V) ...",
                             layout=w.Layout(width="100%", height="260px"))
    examples = sorted(p.stem for p in EXAMPLES_DIR.glob("*.json"))
    dd = w.Dropdown(options=["(load a demo example)"] + examples, layout=w.Layout(width="320px"))

    def load_example(change):
        if change["new"] in examples:
            S.paste_box.value = (EXAMPLES_DIR / f"{change['new']}.json").read_text(encoding="utf-8")
    dd.observe(load_example, names="value")
    display(w.VBox([w.HTML("<b>Paste NotebookLM answer</b> - then run the next cell. "
                           "No NotebookLM output yet? Try a demo example →"), dd, S.paste_box]))
    return S.paste_box


def step5_check(pasted: str | None = None, show_preview: bool = True):
    ws = _need_ws()
    text = pasted if pasted and pasted.strip() else (S.paste_box.value if S.paste_box is not None else "")
    if not text.strip():
        _say("Nothing pasted yet - paste NotebookLM's answer in the box of Step 5a (or pick a demo), "
             "then run this cell again.", "warn")
        return None
    try:
        raw, notes = extract_json(text)
    except ParseError as e:
        _say("⛔ " + html.escape(str(e)).replace("\n", "<br>"), "err")
        copy_box(prompts.load("fix_json"), "PROMPT 04 → NotebookLM (fix invalid JSON)", None, 120)
        return None
    letter, notes2 = normalise(raw, ws.profile())
    return _analyse(letter, notes + notes2, raw, show_preview)


def _analyse(letter, notes, raw=None, show_preview=True):
    ws = _need_ws()
    S.letter, S.raw, S.notes = letter, raw or letter, notes
    S.issues = checks.run_checks(letter, ws.profile())
    full = "\n".join(t for _, t in iter_text(letter))
    S.citations = legal.scan_citations(full)
    for n in notes:
        _say("ℹ️ " + html.escape(n))
    _say(f"<b>Result:</b> {checks.summary(S.issues)}",
         "err" if any(i["level"] == "ERROR" for i in S.issues) else "ok")
    _html(issues_html(S.issues))
    _html(citations_html(S.citations))
    if letter.get("deadlines"):
        rows = "".join(f"<li><b>{html.escape(str(d.get('event', '')))}</b>: {html.escape(str(d.get('date', '')))}"
                       f" <i>({html.escape(str(d.get('basis', '')))})</i></li>" for d in letter["deadlines"])
        _html(f"<div style='font-family:Arial,sans-serif;font-size:13px'><b>⏰ Deadlines stated by NotebookLM"
              f"</b> (recheck with the limitation tool at the end)<ul>{rows}</ul></div>")
    if show_preview:
        _html("<h4 style='font-family:Arial'>Preview (approximate - the Word file follows your template)</h4>")
        _html(letter_html(letter, current_theme()))
    _show_edit_box(letter)
    return letter


def _show_edit_box(letter):
    try:
        import ipywidgets as w
    except Exception:  # pragma: no cover
        return
    S.edit_original = json.dumps(letter, indent=2, ensure_ascii=False)
    S.edit_box = w.Textarea(value=S.edit_original, layout=w.Layout(width="100%", height="240px"))
    display(w.VBox([w.HTML("<b>✏️ Quick edit (optional)</b> - fix anything here; Step 6 uses your edited "
                           "version and re-checks it."), S.edit_box]))


# =========================================================================== step 6: generate
def _slug(s, n=50):
    s = re.sub(r"[^\w\s-]", "", s or "letter").strip()
    return re.sub(r"[\s_-]+", "_", s)[:n].strip("_") or "letter"


def step6_generate(make_pdf: bool = False, download: bool = True, add_to_register: bool = True,
                   allow_errors: bool = False):
    ws = _need_ws()
    if S.edit_box is not None and S.edit_box.value.strip() and S.edit_box.value != S.edit_original:
        try:
            raw, notes = extract_json(S.edit_box.value)
        except ParseError as e:
            _say("⛔ Your quick edit is not valid JSON: " + html.escape(str(e)), "err")
            return None
        letter, n2 = normalise(raw, ws.profile())
        _say("Using your edited version - re-checking ...")
        _analyse(letter, notes + n2, raw, show_preview=False)
    if not S.letter:
        _say("Run Step 5 first.", "err")
        return None
    errs = [i for i in S.issues if i["level"] == "ERROR"]
    if errs and not allow_errors:
        _say(f"⛔ {len(errs)} error(s) must be fixed first (or tick ALLOW_WITH_ERRORS to make a draft anyway): "
             + "; ".join(html.escape(i["msg"][:90]) for i in errs[:4]), "err")
        return None
    st = ws.settings()
    th = current_theme()
    mode = st.get("mode", "auto")
    tpl = st.get("template_path") if st.get("template_path") and Path(st["template_path"]).exists() else None
    lh = st.get("letterhead_path") if st.get("letterhead_path") and Path(st["letterhead_path"]).exists() else None
    if mode == "theme_image":
        mode, tpl = "theme", None
    elif mode == "theme_text":
        mode, tpl, lh = "theme", None, None
    elif mode in ("clone", "placeholder") and not tpl:
        _say("Template file missing - redo Step 3. Falling back to theme mode.", "warn")
        mode = "theme"
    keep = st.get("keep_top_blocks", -1)
    doc, rep = builders.generate(S.letter, th, ws.profile(), mode=mode, template_path=tpl,
                                 letterhead_image=lh, keep_top=keep)
    d = dt.date.today()
    folder = ws.outputs / d.strftime("%Y-%m")
    folder.mkdir(parents=True, exist_ok=True)
    base = f"{d:%Y%m%d}_{S.letter.get('letter_type') or 'letter'}_{_slug(S.letter.get('subject'))}"
    out = folder / f"{base}.docx"
    i = 2
    while out.exists():
        out = folder / f"{base}_v{i}.docx"
        i += 1
    doc.save(str(out))
    (out.with_suffix(".json")).write_text(json.dumps(S.letter, indent=2, ensure_ascii=False), encoding="utf-8")
    S.last_docx = out
    _say(f"✅ Word file created ({rep['mode']} mode): <code>{html.escape(str(out))}</code>", "ok")
    if rep.get("unknown_tags"):
        _say("⚠️ Template tags not filled: " + html.escape(", ".join(rep["unknown_tags"])), "warn")
    if add_to_register:
        reg = register.append(ws.root, S.letter, S.issues, out)
        _say(f"📒 Added to register: <code>{html.escape(str(reg))}</code>")
    if make_pdf:
        ensure_libreoffice()
        pdf = builders.to_pdf(out)
        S.last_pdf = pdf
        _say(f"📄 PDF: <code>{html.escape(str(pdf))}</code>" if pdf else
             "PDF export failed (LibreOffice not available).", "ok" if pdf else "warn")
    if download and IN_COLAB:  # pragma: no cover
        from google.colab import files
        files.download(str(out))
        if make_pdf and S.last_pdf:
            files.download(str(S.last_pdf))
    return out


# =========================================================================== step 7: verification prompts
def step7_verify_prompts():
    if not S.last_docx:
        _say("Generate the Word file first (Step 6).", "err")
        return None
    text = builders.docx_text(S.last_docx)
    p2 = prompts.fact_check_prompt(text)
    p3 = prompts.verification_prompt(S.letter, text, S.issues, S.citations, S.instruction)
    copy_box(p2, "PROMPT 02 → same NotebookLM notebook (facts vs. source)", "02_fact_check.txt", 200)
    copy_box(p3, "PROMPT 03 → ChatGPT / Claude / Gemini (legal provisions, limitation, format)",
             "03_legal_verification.txt", 240)
    copy_box(prompts.load("revise"), "PROMPT 05 → NotebookLM (apply the corrections, then repeat Step 5)", None, 120)
    for name, body in (("02_fact_check", p2), ("03_legal_verification", p3)):
        S.last_docx.with_name(S.last_docx.stem + f"__{name}.txt").write_text(body, encoding="utf-8")
    return p2, p3


# =========================================================================== tools
def tool_limitation(order_date: str, communication_date: str):
    rows = legal.limitation_table(order_date, communication_date)
    if not rows:
        _say("Enter at least one valid date (DD.MM.YYYY).", "err")
        return []
    body = "".join(
        f"<tr><td>{html.escape(r['provision'])}</td><td>{html.escape(r['counted_from'])}</td>"
        f"<td><b>{r['last_date']:%d.%m.%Y}</b> ({r['last_date']:%A})</td>"
        f"<td style='color:{'#b00020' if r['days_left'] < 0 else '#1e7e34' if r['days_left'] > 15 else '#8a5300'}'>"
        f"{r['days_left']}</td></tr>" for r in rows)
    _html("<div style='font-family:Arial,sans-serif;font-size:13px'><table border='1' cellpadding='4' "
          "style='border-collapse:collapse'><tr><th>Provision</th><th>Counted from</th><th>Last date</th>"
          f"<th>Days left</th></tr>{body}</table><i>Simple calendar arithmetic. Check the exact wording of the "
          "section, Section 9/10 of the General Clauses Act (excluding the first day, holidays) and any extension "
          "notified under Section 168A.</i></div>")
    return rows


def tool_amount(amount: str):
    s = f"₹{indian_format(amount)}/- ({rupees_in_words(amount)})"
    copy_box(s, "Amount in Indian format + words", None, 60)
    return s


def tool_gstin(gstin: str):
    why = checks.validate_gstin(gstin)
    _say(f"✅ {html.escape(gstin.upper())} is a structurally valid GSTIN (state {gstin[:2]}, PAN {gstin[2:12].upper()})."
         if not why else f"⛔ {html.escape(gstin)}: {html.escape(why)}", "ok" if not why else "err")
    return why


def tool_reference(search: str = ""):
    ref = load_data("legal_reference")
    q = search.lower().strip()
    rows = []
    for group, items in (("CGST Act", ref["cgst_sections"]), ("CGST Rules", ref["cgst_rules"])):
        for k, v in items.items():
            label = f"{'Section' if group == 'CGST Act' else 'Rule'} {k}"
            if not q or q in label.lower() or q in v["title"].lower():
                rows.append((group, label, v["title"] + (" ⚠️ verify (amended)" if v.get("verify") else "")))
    for k, v in ref["forms"].items():
        if not q or q in k.lower() or q in v.lower():
            rows.append(("Form", k, v))
    for c in ref["circulars"]:
        if not q or q in c["no"].lower() or q in c["subject"].lower():
            rows.append(("Circular", f"{c['no']} dt. {c['date']}", c["subject"] + " ⚠️ verify"))
    body = "".join(f"<tr><td>{html.escape(a)}</td><td><b>{html.escape(b)}</b></td><td>{html.escape(c)}</td></tr>"
                   for a, b, c in rows)
    _html(f"<div style='font-family:Arial,sans-serif;font-size:13px'>Quick reference (last reviewed "
          f"{ref.get('last_reviewed')}) - {len(rows)} match(es)<table border='1' cellpadding='3' "
          f"style='border-collapse:collapse;width:100%'>{body}</table></div>")
    return rows


def tool_register():
    ws = _need_ws()
    rows = register.read(ws.root)
    if not rows:
        _say("Register is empty.")
        return rows
    head = "".join(f"<th>{h}</th>" for h in rows[0])
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r.values()) + "</tr>"
                   for r in rows[-30:][::-1])
    _html(f"<table border='1' cellpadding='3' style='border-collapse:collapse;font-size:12px'>"
          f"<tr>{head}</tr>{body}</table>")
    return rows


def starter_template_path() -> Path:
    return TEMPLATES_DIR / "CBIC_placeholder_template.docx"


def download_file(path):
    path = Path(path)
    if IN_COLAB:  # pragma: no cover
        from google.colab import files
        files.download(str(path))
    else:
        _say(f"File: <code>{html.escape(str(path))}</code>")


def ensure_libreoffice() -> bool:
    if shutil.which("soffice") or shutil.which("libreoffice"):
        return True
    if not IN_COLAB:
        return False
    import subprocess  # pragma: no cover
    _say("Installing LibreOffice for PDF export (one time per session, ~1-2 min) ...")  # pragma: no cover
    subprocess.run("apt-get -qq update && apt-get -qq install -y libreoffice-writer-nogui >/dev/null",
                   shell=True, check=False)  # pragma: no cover
    return bool(shutil.which("soffice"))  # pragma: no cover
