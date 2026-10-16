# Exact-format templates

Each `.docx` here is one of the office's own formats. The original paragraphs, tables, fonts, spacing and Word numbering are kept as they are, and only the content was replaced by `[[MARKERS]]`. The notebook fills the markers, so the output looks **exactly** like the original.

| File | Format | Prompt |
|---|---|---|
| `sop_checklist.docx` | Filing of Intelligence & Investigation under GST Act, 2017 (as per SOP), 20 rows | `prompts/10_sop_checklist.md` |
| `letter_notesheet.docx` | Letter to taxpayer + Notesheet for approval | `prompts/11_letter_notesheet.md` |

Letterheads are **not** stored here, because the repo is public. The notebook inserts your letterhead from Google Drive at `[[IMG:LETTERHEAD]]` (Step 3 extracts it from any letter you upload).

## Marker syntax: make your own format in Word
| Marker | Meaning |
|---|---|
| `[[KEY]]` | value inserted in place, keeping that run's font. Dotted keys work: `[[centre.zone]]` |
| `[[?KEY]]` at the start of a paragraph | whole paragraph is removed when KEY is empty |
| `[[@KEY]]` alone in a paragraph | paragraph repeated once per item of the list KEY |
| `[[%REGION:style]]` alone in a paragraph | prototype paragraph. The JSON gives `"REGION": [{"style": "...", "text": "..."}]` and each block is laid out like the prototype of that style (numbering prefixes are set in `data/formats.json`) |
| `[[IMG:KEY]]` | picture (e.g. the letterhead) |

Inside any value: `**bold**`, `__underline__`, a newline gives a line break, and a tab character gives a tab. Word auto-numbered lists restart at 1 for each separate list.

## Adding a new format (checklist)
1. Copy the office's Word file and replace the variable content with markers. Keep the formatting.
2. Save it here as `<key>.docx`.
3. Write `prompts/<nn>_<key>.md` with the JSON schema, using the same keys as the markers.
4. Add a block for `<key>` in `data/formats.json` (label, template, prompt, din_required, regions).
5. Add a fictional `examples/<key>.json` and a test. **Never commit real taxpayer data.**
