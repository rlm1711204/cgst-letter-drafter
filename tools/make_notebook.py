"""Generate CGST_Letter_Drafter.ipynb (edit here, then run: python tools/make_notebook.py)."""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OWNER_REPO = "rlm1711204/cgst-letter-drafter"
COLAB = f"https://colab.research.google.com/github/{OWNER_REPO}/blob/main/CGST_Letter_Drafter.ipynb"

cells = []


def md(s):
    cells.append(nbf.v4.new_markdown_cell(s.strip()))


def code(s):
    cells.append(nbf.v4.new_code_cell(s.strip()))


md(f"""
# 📨 CGST Letter Drafter (NotebookLM → Word)
**Source documents → NotebookLM extracts the details and drafts → this notebook checks and formats → Word letter on your letterhead → verified by a second AI.**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB})

| Step | Where | What you do |
|---|---|---|
| 0 | Colab | Run **Setup** once per session |
| 1 | Colab → NotebookLM / Gemini | Choose the **document format** (Letter · SOP checklist · Letter + Notesheet) and copy the prompt into NotebookLM (PDFs), or into Gemini / ChatGPT with **Prime portal screenshots** attached |
| 2 | Colab | *(first time only)* Office profile: office name, signatory |
| 3 | Colab | *(first time only)* Upload your **sample letter .docx** or **letterhead image** |
| 4 | Colab | Choose a theme: fonts, spacing, numbering, labels |
| 5 | NotebookLM → Colab | Paste NotebookLM's answer, then see the **automatic checks and preview** |
| 6 | Colab | Generate the **Word file** (+PDF), saved to Drive and added to the register |
| 7 | Colab → NotebookLM / other AI | Copy the **verification prompts** (fact check + legal check) |

> 💡 **First time:** *File ▸ Save a copy in Drive* so your form settings stay. Your profile, templates, letters and register are saved in **My Drive ▸ CGST_Letter_Drafter**.
> ⚠️ The software checks a lot, but **the signing officer remains responsible**. Always read the final letter and confirm citations with the bare Act and CBIC circulars.
""")

code("""
#@title ⚙️ STEP 0 · Setup (run once per session) { display-mode: "form" }
USE_GOOGLE_DRIVE = True  #@param {type:"boolean"}
VERSION = "main"  #@param {type:"string"}
#@markdown *VERSION: leave as `main` to get the latest version, or give a tag such as `v1.0.0` to freeze it.*

import os, sys, subprocess, importlib
REPO = "https://github.com/""" + OWNER_REPO + """.git"
APP = os.environ.get("LETTERGEN_APP", "/content/cgst-letter-drafter")
if "LETTERGEN_APP" not in os.environ:
    if os.path.isdir(os.path.join(APP, ".git")):
        subprocess.run(["git", "-C", APP, "fetch", "-q", "--depth", "1", "origin", VERSION], check=True)
        subprocess.run(["git", "-C", APP, "checkout", "-q", "-f", "FETCH_HEAD"], check=True)
    else:
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", VERSION, REPO, APP], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", os.path.join(APP, "requirements.txt")],
                   check=True)
if APP not in sys.path:
    sys.path.insert(0, APP)
for _m in [m for m in sys.modules if m == "lettergen" or m.startswith("lettergen.")]:
    del sys.modules[_m]          # pick up updates without restarting
import lettergen
from lettergen import ui
print("CGST Letter Drafter v" + lettergen.__version__)
ui.setup(use_drive=USE_GOOGLE_DRIVE)
""")

md("""
## 📝 STEP 1 · Get the prompt
1. Choose a **DOCUMENT_FORMAT**:
   * **Letter (generic)**: any official letter; pick a LETTER_TYPE as well. Uses your sample letter / theme.
   * **SOP checklist**: the 20-row *Filing of Intelligence & Investigation* table, in your exact format.
   * **Letter + Notesheet**: letter to the taxpayer plus a notesheet for approval, in your exact format with your letterhead.
2. Sources: upload PDFs to **[NotebookLM](https://notebooklm.google.com)**, **or** attach screenshots (GST Prime / BO taxpayer profile, return filing, ledgers) and documents to **Gemini / ChatGPT / Claude**.
3. Run the cell, press **📋 Copy**, paste into the AI, and copy its whole answer into Step 5.
""")

code("""
#@title 📝 STEP 1 · Build the prompt for NotebookLM { display-mode: "form" }
DOCUMENT_FORMAT = "Letter (generic - choose a letter type)"  #@param ["Letter (generic - choose a letter type)", "SOP checklist - Filing of Intelligence & Investigation", "Letter to taxpayer + Notesheet (for approval)"]
LETTER_TYPE = "Appeal / Review (OIO / OIA)"  #@param ["Letter to Taxpayer", "Appeal / Review (OIO / OIA)", "Court / Writ Matter", "SCN / Adjudication", "Administrative / Inter-office"]
WHAT_SHOULD_THE_LETTER_DO = "Forward the application under Section 107(2) against the OIO to the Commissioner (Appeals)"  #@param {type:"string"}
LETTER_DATE = ""  #@param {type:"string"}
FILE_NO = ""  #@param {type:"string"}
DIN = ""  #@param {type:"string"}
#@markdown *LETTER_TYPE is used only for the generic Letter. Leave LETTER_DATE blank for today, and FILE_NO / DIN blank if you'll add them later; the checker reminds you.*
ui.step1_prompt(LETTER_TYPE, WHAT_SHOULD_THE_LETTER_DO, LETTER_DATE, FILE_NO, DIN, doc_format=DOCUMENT_FORMAT);
""")

md("""
## 🏢 STEP 2 · Office profile *(first time only - saved to Drive)*
Used for the **text letterhead** (if you have no letterhead image) and as the default **signatory**. Blank fields keep the saved value, so re-running this cell never wipes your profile.
""")

code("""
#@title 🏢 STEP 2 · Office profile { display-mode: "form" }
OFFICE_LINES = ""  #@param {type:"string"}
#@markdown *Letterhead lines separated by `|` e.g. `भारत सरकार / GOVERNMENT OF INDIA | OFFICE OF THE COMMISSIONER OF CGST & CENTRAL EXCISE | TIRUNELVELI COMMISSIONERATE`*
OFFICE_ADDRESS = ""  #@param {type:"string"}
OFFICE_CONTACT = ""  #@param {type:"string"}
SECTION = ""  #@param {type:"string"}
SIGNATORY_NAME = ""  #@param {type:"string"}
SIGNATORY_DESIGNATION = ""  #@param {type:"string"}
SIGNATORY_OFFICE_LINE = ""  #@param {type:"string"}
HOME_STATE_CODE = "33"  #@param {type:"string"}
ui.step2_profile(office_lines=OFFICE_LINES, office_address=OFFICE_ADDRESS, office_contact=OFFICE_CONTACT,
                 section=SECTION, signatory_name=SIGNATORY_NAME, signatory_designation=SIGNATORY_DESIGNATION,
                 signatory_office_line=SIGNATORY_OFFICE_LINE, home_state_code=HOME_STATE_CODE);
""")

md("""
## 🖼️ STEP 3 · Letterhead / template *(first time only - remembered)*
| Mode | Upload | Result |
|---|---|---|
| **Clone my sample letter** ⭐ | any old letter of your office (.docx) | Keeps its letterhead, header/footer, margins, **fonts, labels (C.No./Sub:), numbering style**, and replaces only the letter content |
| **Placeholder template** | a .docx with `{{ SUBJECT }}`, `{{p BODY }}` ... tags | Exact layout, 100% under your control (see `templates/PLACEHOLDERS.md`) |
| **Letterhead image + theme** | PNG/JPG of the letterhead | Builds a clean letter with the theme from Step 4 |
| **Text letterhead + theme** | nothing | Uses the office profile lines as the letterhead |

Tick **UPLOAD_NEW_FILE** the first time, or whenever you change the file. To try it out, pick a **DEMO_FILE**.

**Exact formats (SOP checklist, Letter + Notesheet)** keep their own fixed layout. They only need your **letterhead picture**: upload any of your letters (.docx) here and the letterhead is taken from it automatically, or upload the letterhead image (PNG/JPG). It stays in your Drive and is never put on GitHub.
""")

code("""
#@title 🖼️ STEP 3 · Choose template mode { display-mode: "form" }
TEMPLATE_MODE = "Auto (decide from what I upload)"  #@param ["Auto (decide from what I upload)", "Clone my sample letter (.docx)", "Placeholder template (.docx with {{TAGS}})", "Letterhead image + theme", "Text letterhead from office profile + theme"]
UPLOAD_NEW_FILE = False  #@param {type:"boolean"}
DEMO_FILE = "(none)"  #@param ["(none)", "Demo sample letter (clone)", "Demo placeholder template", "Demo letterhead image"]
KEEP_TOP_BLOCKS = -1  #@param {type:"integer"}
DOWNLOAD_STARTER_PLACEHOLDER_TEMPLATE = False  #@param {type:"boolean"}
#@markdown *KEEP_TOP_BLOCKS: -1 = automatic. Clone mode keeps that many blocks at the top of your sample (your letterhead) and replaces the rest.*
_demo = {"Demo sample letter (clone)": "sample_letter_for_clone_demo.docx",
         "Demo placeholder template": "CBIC_placeholder_template.docx",
         "Demo letterhead image": "sample_letterhead.png"}.get(DEMO_FILE)
ui.step3_template(TEMPLATE_MODE, UPLOAD_NEW_FILE, KEEP_TOP_BLOCKS,
                  file_path=os.path.join(APP, "templates", _demo) if _demo else None)
if DOWNLOAD_STARTER_PLACEHOLDER_TEMPLATE:
    ui.download_file(ui.starter_template_path())
""")

md("""
## 🎨 STEP 4 · Theme: fonts and format
`From my sample letter` copies the style detected in Step 3. Any option other than *(theme default)* overrides the preset. Type a name in **SAVE_AS_MY_THEME** to save the combination as your own preset.
""")

code("""
#@title 🎨 STEP 4 · Theme { display-mode: "form" }
THEME_PRESET = "CBIC Classic"  #@param ["From my sample letter (auto-detected)", "CBIC Classic", "Modern Arial", "Bookman Formal", "Compact One-Page", "Bilingual (Hindi-English)", "Cambria Clean"] {allow-input: true}
FONT = "(theme default)"  #@param ["(theme default)", "Times New Roman", "Arial", "Bookman Old Style", "Cambria", "Calibri", "Garamond", "Georgia", "Tahoma", "Verdana", "Century Gothic"] {allow-input: true}
FONT_SIZE = "(theme default)"  #@param ["(theme default)", "10", "10.5", "11", "11.5", "12", "13", "14"]
LINE_SPACING = "(theme default)"  #@param ["(theme default)", "1.0", "1.15", "1.5", "2.0"]
PARAGRAPH_NUMBERING = "(theme default)"  #@param ["(theme default)", "all", "from_second", "none"]
FIRST_LINE_INDENT_CM = "(theme default)"  #@param ["(theme default)", "0", "1.0", "1.27", "2.0"]
SALUTATION_POSITION = "(theme default)"  #@param ["(theme default)", "after_subject", "before_subject"]
SUBJECT_UNDERLINE = "(theme default)"  #@param ["(theme default)", "yes", "no"]
SIGNATURE_ALIGN = "(theme default)"  #@param ["(theme default)", "right", "left"]
NAME_IN_CAPITALS = "(theme default)"  #@param ["(theme default)", "yes", "no"]
DATE_STYLE = "(theme default)"  #@param ["(theme default)", "16.10.2026", "16/10/2026", "16-10-2026", "16 October 2026", "October 16, 2026"]
FILE_NO_LABEL = "(theme default)"  #@param ["(theme default)", "F.No.", "C.No.", "File No.", "O.C. No."] {allow-input: true}
SUBJECT_LABEL = "(theme default)"  #@param ["(theme default)", "Sub:", "Subject:"] {allow-input: true}
LETTERHEAD_ON = "(theme default)"  #@param ["(theme default)", "first page", "all pages"]
PAGE_NUMBERS = "(theme default)"  #@param ["(theme default)", "yes", "no"]
BILINGUAL_LABELS = "(theme default)"  #@param ["(theme default)", "yes", "no"]
SAVE_AS_MY_THEME = ""  #@param {type:"string"}
ui.step4_theme(THEME_PRESET, SAVE_AS_MY_THEME, font=FONT, size=FONT_SIZE, line_spacing=LINE_SPACING,
               para_numbering=PARAGRAPH_NUMBERING, first_line_indent=FIRST_LINE_INDENT_CM,
               salutation_position=SALUTATION_POSITION, subject_underline=SUBJECT_UNDERLINE,
               signature_align=SIGNATURE_ALIGN, name_uppercase=NAME_IN_CAPITALS, date_style=DATE_STYLE,
               file_no_label=FILE_NO_LABEL, subject_label=SUBJECT_LABEL, letterhead_on=LETTERHEAD_ON,
               page_numbers=PAGE_NUMBERS, bilingual_labels=BILINGUAL_LABELS);
""")

md("""
## 📋 STEP 5 · Paste NotebookLM's answer → automatic checks
Run **5a**, paste into the box (or pick a demo example), then run **5b**.
5b checks: required fields · **DIN** for taxpayer letters · **GSTIN check digit** · impossible dates · **amount in words vs figures** · **table totals** · Indian digit grouping · every **Section/Rule/Form** cited (against a quick reference) · **Sec 73/74 vs 74A by financial year** · **limitation date** for reviews · **monetary limits** for departmental appeals · `[TO BE CONFIRMED]` placeholders · items NotebookLM marked as uncertain.
""")

code("""
#@title 📋 STEP 5a · Paste box { display-mode: "form" }
ui.step5_paste_box();
""")

code("""
#@title 🔍 STEP 5b · Check & preview { display-mode: "form" }
ui.step5_check();
""")

code("""
#@title ↪️ (Fallback) Paste here if the box above doesn't work { display-mode: "form" }
PASTE_HERE = r'''

'''
if PASTE_HERE.strip():
    ui.step5_check(PASTE_HERE)
""")

md("""
## 📄 STEP 6 · Generate the Word letter
Errors from Step 5 block generation unless you tick **ALLOW_WITH_ERRORS** (useful for a rough draft). Edits made in the ✏️ box in Step 5 are used automatically.
""")

code("""
#@title 📄 STEP 6 · Generate Word (.docx) { display-mode: "form" }
DOWNLOAD = True  #@param {type:"boolean"}
ALSO_MAKE_PDF = False  #@param {type:"boolean"}
ALLOW_WITH_ERRORS = False  #@param {type:"boolean"}
ADD_TO_REGISTER = True  #@param {type:"boolean"}
ui.step6_generate(make_pdf=ALSO_MAKE_PDF, download=DOWNLOAD, add_to_register=ADD_TO_REGISTER,
                  allow_errors=ALLOW_WITH_ERRORS);
""")

md("""
## ✅ STEP 7 · Verify with AI (two independent checks)
* **Prompt 02 → the same NotebookLM notebook:** checks every fact against your sources (it has the PDFs).
* **Prompt 03 → ChatGPT / Claude / Gemini** (preferably with web search on and the source PDF attached): checks provisions, amendments, limitation working, format and risk.
* Got corrections? **Prompt 05 → NotebookLM** gives back corrected JSON → repeat Steps 5–6.
""")

code("""
#@title ✅ STEP 7 · Verification prompts { display-mode: "form" }
ui.step7_verify_prompts();
""")

md("## 🧰 Tools")

code("""
#@title ⏰ Limitation calculator (Sec 107 / 112 / 117 / RTI) { display-mode: "form" }
DATE_OF_ORDER = ""  #@param {type:"string"}
DATE_OF_COMMUNICATION_OR_RECEIPT = ""  #@param {type:"string"}
ui.tool_limitation(DATE_OF_ORDER, DATE_OF_COMMUNICATION_OR_RECEIPT);
""")

code("""
#@title 💰 Amount → Indian format + words { display-mode: "form" }
AMOUNT = "825000"  #@param {type:"string"}
ui.tool_amount(AMOUNT);
""")

code("""
#@title 🆔 GSTIN validator (check digit) { display-mode: "form" }
GSTIN = "33AABFS1234K1ZH"  #@param {type:"string"}
ui.tool_gstin(GSTIN);
""")

code("""
#@title 📚 Legal quick reference (sections, rules, forms, circulars) { display-mode: "form" }
SEARCH = "appeal"  #@param {type:"string"}
ui.tool_reference(SEARCH);
""")

code("""
#@title 📒 Letter register (last 30) { display-mode: "form" }
ui.tool_register();
""")

md("""
## ❓ Help & troubleshooting
* **"Could not find a valid JSON object"** → in NotebookLM send *Prompt 04* (it appears automatically), then copy again. Use the copy icon under the answer, not a mouse selection.
* **Clone mode removed my letterhead / kept old text** → look at the table in Step 3 and set `KEEP_TOP_BLOCKS` to the number of the first row that should be replaced.
* **Font looks different on screen** → Word substitutes fonts that aren't installed. The file still asks for your chosen font, so it prints correctly on an office PC that has the font.
* **Hindi text** uses the `hindi_font` of the theme (Nirmala UI by default; Mangal also works).
* **Add your own theme / letter type / legal reference entry** → edit `data/themes.json`, `data/letter_types.json`, `data/legal_reference.json` in the GitHub repo. Every user picks it up on the next Setup.
* **Freeze a version** → set `VERSION` in Step 0 to a release tag.
* **Privacy** → nothing is sent anywhere by this notebook. Your files stay in your Colab session and your Google Drive. Follow your office's instructions on which documents may be uploaded to NotebookLM or other AI tools.
""")

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"] = {"colab": {"provenance": [], "toc_visible": True, "name": "CGST_Letter_Drafter.ipynb"},
                  "kernelspec": {"name": "python3", "display_name": "Python 3"},
                  "language_info": {"name": "python"}}
nbf.write(nb, ROOT / "CGST_Letter_Drafter.ipynb")
print("notebook written")
