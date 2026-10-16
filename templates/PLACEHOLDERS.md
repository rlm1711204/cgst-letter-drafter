# Placeholder template guide (exact-layout mode)

Want full control of the layout? Make a Word file with your letterhead and put these **tags** where the content should go. Upload it in Step 3 and the notebook detects the tags automatically.
Start from `CBIC_placeholder_template.docx` in this folder (Step 3 → tick `DOWNLOAD_STARTER_PLACEHOLDER_TEMPLATE`).

## Simple text tags (use inside any line)
| Tag | Filled with |
|---|---|
| `{{ FILE_NO }}` | File number |
| `{{ DIN }}` | DIN |
| `{{ DATE }}` | Letter date (in the theme's date style) |
| `{{ SUBJECT }}` | Subject |
| `{{ SALUTATION }}` | Sir/Madam, |
| `{{ CLOSING }}` | Yours faithfully, |
| `{{ THROUGH }}`, `{{ KIND_ATTENTION }}` | as named |
| `{{ SIGNATORY_NAME }}`, `{{ SIGNATORY_DESIGNATION }}`, `{{ SIGNATORY_OFFICE }}` | signature lines |
| `{{ kf.gstin }}`, `{{ kf.period }}`, `{{ kf.document_no }}` ... | any key in `key_facts` |

## Block tags (must be ALONE in their own paragraph; note the `p`)
| Tag | Inserts (formatted with the Step 4 theme) |
|---|---|
| `{{p TO_BLOCK }}` | "To," + addressee lines (+ GSTIN), Through, Kind attention |
| `{{p REF_BLOCK }}` | Ref: 1. ... 2. ... |
| `{{p BODY }}` | Numbered paragraphs, (i)(ii) sub-points and amount tables |
| `{{p SIGNATURE_BLOCK }}` | Yours faithfully + name + designation |
| `{{p ENCL_BLOCK }}` | Encl.: ... |
| `{{p COPY_BLOCK }}` | Copy to: 1. ... |
| `{{p FULL_LETTER }}` | Everything below the letterhead in one go |

## Conditional lines
```
{%p if DIN %}
DIN: {{ DIN }}
{%p endif %}
```
Each `{%p ... %}` must be in its own paragraph.

## Lists in your own format
```
{%p for r in REFERENCES %}
{{ loop.index }}. {{ r }}
{%p endfor %}
```
Also available: `TO_LINES`, `ENCLOSURES`, `COPY_TO`.

**Tip:** type each tag in one go. If Word's spell-check or autocorrect splits a tag (e.g. changing the straight quotes), retype it. Unknown tags are reported after generation.
