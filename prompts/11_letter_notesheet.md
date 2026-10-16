# Prompt 11 — Letter to taxpayer + Notesheet for approval (returns JSON)

**Works with:** NotebookLM (source PDFs) or Gemini / ChatGPT / Claude (screenshots plus documents).
**Upload / attach:** the complaint or reference, taxpayer profile screenshot (GST Prime / BO), return-filing details, and any earlier correspondence.
Colab Step 1 (format = *Letter + Notesheet*) fills in the `{{...}}` blanks. Paste the answer into Colab Step 5.

---
<!-- PROMPT START -->
You are an officer of a CGST & Central Excise (CBIC) formation. From the attached sources, draft TWO documents in one JSON:
(A) a LETTER to the taxpayer, and (B) an internal NOTESHEET proposing the action for approval of the competent authority.

PURPOSE: {{INSTRUCTION}}
MY OFFICE: {{FROM_OFFICE}}   |   SIGNATORY: {{SIGNATORY}}
File No.: {{FILE_NO_SHOW}}   |   DIN: {{DIN_SHOW}}   |   Letter date: {{LETTER_DATE}}

EXTRACT FIRST (copy exactly, character by character)
- Legal name, trade name, GSTIN, PAN (characters 3-12 of the GSTIN), full address with PIN, constitution, date of registration, status.
- Jurisdiction: Range / Division / Commissionerate (Centre) or State Circle / Division.
- Nature of supply with SAC/HSN as in the source (a GST SAC starts with 99; quote any other code exactly and flag it).
- Source of the complaint or intelligence: who forwarded it, letter numbers and dates, and the chronology.
- Return-filing facts (GSTR-1 / GSTR-3B period and filing dates) and the period proposed for verification.

LETTER RULES
- "to_lines": ["M/s LEGAL NAME IN CAPITALS", "(GSTIN: ... / PAN: ...)", "address line 1", "...", "District, State - PIN."].
- "subject": one sentence in the house style: "GST — <topic> — <specific issue> — <action> under Section __ of the CGST Act, 2017 – Regarding."
- "letter_body" is a list of blocks: {"style": "first"} = opening paragraph (unnumbered), {"style": "numbered"} = paragraphs 2, 3... (do NOT type the numbers), {"style": "item"} = items of a numbered list such as documents called for (auto-numbered; do not type numbers).
- Put the period in bold and underline like this: **__Financial Year 2021-22 to Financial Year 2025-26__**.
- Give a specific time limit for compliance and the consequence of non-compliance, citing the correct penal provisions.
- Authority for calling documents: quote the provision the source or instruction uses. If none is given, propose one, mark it "basis": "suggested" in legal_citations, and add to missing_or_uncertain: "Confirm the provision for calling documents: summons under Section 70, or an order under Section 151 of the CGST Act, 2017".
- A letter to a taxpayer must carry a DIN (Circular No. 122/41/2019-GST dated 05.11.2019). If no DIN is given, leave "din" as "" (the software will warn).

NOTESHEET RULES
- "notesheet_subject": "Complaints – M/s <LEGAL NAME> (Legal Name: ...), GSTIN: ... – <issue in brief> – reg." (adapt "Complaints" to the source type).
- "notesheet_body" blocks: {"style": "para"} = normal paragraph (first-line indent), {"style": "plain"} = paragraph without indent, {"style": "item"} = numbered list item.
- Order: (1) taxpayer profile with registration date, services with SAC and jurisdiction; (2) source of the complaint/intelligence with chronology, numbers and dates; (3) facts found on verification; (4) legal position: provisions contravened (e.g. Section 31 of the CGST Act, 2017 read with Rule 46 of the CGST Rules, 2017), recovery with interest under Section 50, demand under Section 73/74 for FY up to 2023-24 and Section 74A from FY 2024-25, penalty provisions; (5) the proposal, with the documents list as items; (6) last line: "... submitted for perusal and approval of the competent authority."
- Time limits: for each FY proposed, note in "deadlines" the Section 73/74/74A time limit counted from the annual-return due date (31 December after the FY), marked "verify". Flag in missing_or_uncertain any FY where the Section 73 SCN time limit may already have passed.

GENERAL
- Use only facts in the sources. Missing facts → [TO BE CONFIRMED: ...] + missing_or_uncertain.
- Dates DD.MM.YYYY; amounts ₹12,34,567/-; formal Government of India English.

OUTPUT: ONLY one ```json code block, valid JSON, no citation markers like [1]:
```json
{
  "format": "letter_notesheet",
  "file_no": "{{FILE_NO}}",
  "din": "{{DIN}}",
  "date": "{{LETTER_DATE}}",
  "to_lines": [],
  "salutation": "Sir / Madam,",
  "subject": "",
  "letter_body": [
    {"style": "first", "text": ""},
    {"style": "numbered", "text": ""},
    {"style": "item", "text": ""},
    {"style": "numbered", "text": ""}
  ],
  "closing": "Yours faithfully,",
  "signatory_lines": [],
  "notesheet_subject": "",
  "notesheet_body": [
    {"style": "para", "text": ""},
    {"style": "item", "text": ""},
    {"style": "plain", "text": ""}
  ],
  "notesheet_signatory_lines": [],
  "key_facts": {"legal_name": "", "gstin": "", "pan": "", "address": "", "date_of_registration": "", "sac_hsn": "",
                "jurisdiction": "", "complaint_ref": "", "period": ""},
  "legal_citations": [{"provision": "", "purpose": "", "basis": "source"}],
  "deadlines": [{"event": "", "date": "", "basis": ""}],
  "missing_or_uncertain": []
}
```
<!-- PROMPT END -->
