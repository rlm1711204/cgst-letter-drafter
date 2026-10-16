# 📨 CGST Letter Drafter: NotebookLM → checked Word letter on your letterhead

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rlm1711204/cgst-letter-drafter/blob/main/CGST_Letter_Drafter.ipynb)
![tests](https://github.com/rlm1711204/cgst-letter-drafter/actions/workflows/tests.yml/badge.svg)

A Google Colab tool for the **Legal Section of a CGST & Central Excise Commissionerate (CBIC)**. It turns source documents (incoming letters, OIO/OIA, SCNs, writ petitions, court orders) into a **properly formatted official letter (.docx)** that matches your office's own letterhead and format, and then has it **cross-verified by AI**.

```
 Source PDFs ──► NotebookLM ──(Prompt 01)──► JSON: extracted facts + drafted body
                                                    │ paste
                                                    ▼
                         Colab: parse ─► 15+ automatic checks ─► preview ─► quick edit
                                                    │
                                                    ▼
             Word letter (your sample's letterhead / fonts / labels)  + PDF + register entry
                                                    │
                     ┌──────────────────────────────┴──────────────────────────────┐
           Prompt 02 → NotebookLM                                     Prompt 03 → ChatGPT / Claude / Gemini
           (every fact vs. the source)                                (sections, amendments, limitation, format)
                     └────────────── corrections ──► Prompt 05 → NotebookLM ──► re-generate ┘
```

No API key is needed. The AI work happens in NotebookLM and the AI tool you verify with; Colab only checks and formats.

## Quick start
1. Click **Open in Colab** → *File ▸ Save a copy in Drive*.
2. Run **Step 0 (Setup)**. It asks for Google Drive access, where your profile, templates, letters and register are kept.
3. Try it immediately: in Step 3 pick `DEMO_FILE = Demo sample letter (clone)`, in Step 5a pick a demo example, then run Steps 5b → 6 → 7.
4. Real use: follow Steps 1 → 7 in the notebook.

## Document formats
| Format | What you get | Sources the AI can use |
|---|---|---|
| **Letter (generic)** | Any official letter in your sample letter's style or a theme (5 letter types below) | PDFs in NotebookLM |
| **SOP checklist** ⭐ | *Filing of Intelligence & Investigation under GST Act, 2017 (as per SOP)*: your exact 20-row table, filled | **Screenshots** (GST Prime / BO profile, returns, ledgers) + complaint / notes in Gemini, ChatGPT, Claude or NotebookLM |
| **Letter + Notesheet** ⭐ | Letter to the taxpayer **and** the notesheet for approval, in your exact format with your letterhead | Same |

The exact formats use [`templates/formats/`](templates/formats/README.md). More of your formats can be added the same way. The checker also flags demand **time limits** by financial year (Section 73 / 74 / 74A), e.g. *"FY 2022-23 under Section 73: SCN time limit passed - only Section 74 remains"*.

## Letter types (presets with tailored extraction checklists)
| Key | For |
|---|---|
| `taxpayer` | Letters to taxpayers: requests, intimations, reminders, replies (DIN mandatory) |
| `appeal_review` | Review of OIO/OIA, Section 107(2) / 112(3) applications, acceptance, forwarding appeal papers |
| `court_writ` | Writ petitions, para-wise comments, Standing Counsel, compliance with court orders |
| `scn_adjudication` | SCN correspondence, personal hearing, adjournment (Section 75), reminders |
| `admin` | Inter-office letters, reports, RTI replies |

Add more by editing [`data/letter_types.json`](data/letter_types.json). No code change is needed.

## Four ways to match your format
| Mode | You upload | What is kept |
|---|---|---|
| **Clone sample letter** ⭐ | any existing letter of your office (.docx) | letterhead (header or top of page), footer, margins, font, size, line spacing, labels such as `C.No.` / `Sub:`, salutation position, numbering style |
| **Placeholder template** | .docx with `{{ TAGS }}` ([guide](templates/PLACEHOLDERS.md)) | everything: exact layout |
| **Letterhead image + theme** | PNG/JPG | image as first-page header + theme |
| **Text letterhead + theme** | nothing | office profile lines as the letterhead |

Themes ([`data/themes.json`](data/themes.json)): *CBIC Classic, Modern Arial, Bookman Formal, Compact One-Page, Bilingual (Hindi-English), Cambria Clean*, plus "From my sample letter". Override font, size, spacing, numbering, labels and date style in the form, and save the result as your own theme.

## Automatic checks (Step 5)
- Required parts: subject, addressee, body, file no., signatory
- **DIN** required on taxpayer communications (Circular 122/41/2019-GST)
- **GSTIN check-digit** validation (catches one-character typos), state code
- Impossible dates (31.06.2026), future or very old letter dates
- **Amount in words vs figures**, western vs Indian digit grouping, **table totals**
- Every **Section / Rule / Form** cited is looked up in a quick reference; section numbers beyond the Act are flagged; the Act should be named at first mention
- **Section 73/74 vs 74A** against the financial year; Section 128A period
- **Limitation**: Section 107(2) (6 months from communication) / 112(3) (6 months from order); flags it if the letter date is after the last date
- **Monetary limits** for departmental appeals (Circular 207/1/2024-GST)
- `[TO BE CONFIRMED]` placeholders, and everything NotebookLM itself marked as uncertain or "suggested"

## Repository layout
```
CGST_Letter_Drafter.ipynb   the notebook (generated by tools/make_notebook.py)
lettergen/                  python package: parser, schema, checks, legal, themes, builders, slots (exact-format engine), formats, ui
prompts/                    all prompts as editable markdown (00 setup … 05 revise, 10 SOP, 11 letter+notesheet)
data/                       letter types, themes, legal quick reference (edit freely)
examples/                   demo JSON for each letter type
templates/                  starter placeholder template, demo letterhead, demo sample letter
templates/formats/          exact-format templates with [[MARKERS]] (SOP checklist, letter + notesheet)
tests/                      pytest suite (runs on every push via GitHub Actions)
tools/                      build_assets.py, make_notebook.py
```

## Future-proofing
- **Versioned schema** (`schema_version`) and a tolerant normaliser: field aliases, NotebookLM citation markers `[1]`, smart quotes and trailing commas are all handled.
- **Prompts, letter types, themes and legal references are data files**, so the law and the formats can be updated without touching code.
- Set `VERSION` in Step 0 to a git tag to freeze a version that works for you.
- CI tests every push on Python 3.10 and 3.12.

### Updating the legal quick reference
`data/legal_reference.json` was last reviewed **16.10.2026**. Entries marked `"verify": true` were amended recently. When the law changes (new section, new circular), edit this file on GitHub. The next Setup picks it up.

## ⚠️ Disclaimer
This is a drafting aid. The quick reference and checks are not a substitute for the bare Act, Rules, notifications and circulars on [cbic-gst.gov.in](https://cbic-gst.gov.in). **The signing officer is responsible for the content.** Follow your office's instructions on which documents may be uploaded to NotebookLM or other AI services.

## Development
```bash
pip install -r requirements.txt pytest nbformat
python tools/build_assets.py     # regenerate templates/
python tools/make_notebook.py    # regenerate the notebook
pytest -q
```
