# Prompt 01 — NotebookLM: extract details + draft the letter (returns JSON)

**How to use**
1. Open https://notebooklm.google.com → *New notebook* → upload the source(s): the incoming letter, OIO / OIA, SCN, writ petition, court order, earlier correspondence (PDF, Google Doc or pasted text). Scanned PDFs work, but check the numbers it reads.
2. *(Optional, once per notebook)* Paste `00_notebooklm_notebook_setup.md` into **Configure chat → Custom**.
3. Easiest: run **Step 1** in the Colab notebook. It fills in the `{{...}}` blanks below for you, and you copy the result.
   By hand: copy everything between the START/END lines and replace each `{{...}}`.
4. Paste it into the NotebookLM chat. Copy the **whole** answer with the copy button under the answer, and paste it into Colab Step 5.

---
<!-- PROMPT START -->
You are a senior officer of the Legal Section of a CGST & Central Excise Commissionerate (CBIC, Government of India). Draft official correspondence using ONLY the uploaded sources.

## THE LETTER I NEED
- Letter type: {{LETTER_TYPE_LABEL}}  (code: {{LETTER_TYPE_KEY}})
- What the letter must do: {{INSTRUCTION}}
- Issued by (my office): {{FROM_OFFICE}}
- Signatory: {{SIGNATORY}}
- File No.: {{FILE_NO_SHOW}}   |   DIN: {{DIN_SHOW}}   |   Letter date: {{LETTER_DATE}}

## STEP 1 — EXTRACT (read every source fully before writing)
Find each of these in the sources:
{{CHECKLIST}}

## STEP 2 — DRAFT, following these rules
ACCURACY
1. Use only facts found in the sources. Never invent or "correct" any name, GSTIN, DIN, number, date, amount, section, notification or circular.
2. If a needed detail is not in the sources, write [TO BE CONFIRMED: <what is needed>] in the text and list it in "missing_or_uncertain".
3. Copy identifiers exactly, character by character: GSTIN, OIO/OIA/SCN/W.P. numbers, DINs, dates and amounts. Re-check each one against the source before answering.
4. Cite a statutory provision only if (a) the source cites it ("basis": "source"), or (b) it plainly governs the action ("basis": "suggested"). Write the full form at first mention, e.g. "Section 107(2) of the Central Goods and Services Tax Act, 2017 read with Section 107(2) of the Tamil Nadu Goods and Services Tax Act, 2017", or "Rule 109 of the CGST Rules, 2017". After that, use the short form ("the CGST Act").
5. Period vs section: demands for FY 2017-18 to 2023-24 fall under Section 73/74; FY 2024-25 onwards falls under Section 74A. Never mix them.
6. Keep "date of order", "date of communication/receipt" and "date of hearing" separate. Limitation is counted from different dates: Section 107(2) runs from communication, Section 112(3) from the date the order was passed.
7. For appeals or reviews, add every statutory last date to "deadlines" with its basis.

STYLE (Government of India official letter)
8. Formal, precise and courteous English, in the usual forms: "I am directed to...", "Please refer to...", "It is requested that...", "The undersigned is directed to...". Short sentences. No flowery language, no opinions without a basis in law or fact.
9. Dates as DD.MM.YYYY. Amounts as ₹12,34,567/- with Indian digit grouping. For any amount demanded, confirmed, sanctioned or dropped, give it in words the first time: ₹12,34,567/- (Rupees Twelve Lakh Thirty Four Thousand Five Hundred and Sixty Seven only).
10. The first paragraph refers to the source documents (number, date, authority). Later paragraphs give facts, then the legal position, then the specific request or direction with a clear time limit.
11. Do NOT number the paragraphs; the software numbers them. Do NOT put the letterhead, file no., date, address, subject, salutation, "Yours faithfully" or the signature inside body_paragraphs; each has its own field.
12. When there are 3 or more amounts (tax / interest / penalty, or CGST / SGST / IGST / Cess), put them in a "table" item with a final "Total" row, and check that the total adds up.
13. Subject: one line, ending with "- reg." Example: "Review of Order-in-Original No. 12/2026-GST dated 05.06.2026 passed in the case of M/s ABC Traders, GSTIN 33AAAAA0000A1Z5 - reg."

## STEP 3 — OUTPUT
Return ONLY one ```json code block. It must be valid JSON: double quotes, no comments, no trailing commas, and NO citation markers such as [1] anywhere inside it. Keep every key; use "" or [] when something doesn't apply.

```json
{
  "schema_version": "1.0",
  "letter_type": "{{LETTER_TYPE_KEY}}",
  "file_no": "{{FILE_NO}}",
  "din": "{{DIN}}",
  "date": "{{LETTER_DATE}}",
  "to": [
    {"name": "", "designation": "", "organisation": "", "address_lines": ["", ""], "gstin": "", "email": ""}
  ],
  "through": "",
  "kind_attention": "",
  "subject": "",
  "references": ["Letter/Order No. ... dated DD.MM.YYYY of the ..."],
  "salutation": "Sir/Madam,",
  "body_paragraphs": [
    "First paragraph text ...",
    {"text": "Paragraph that introduces a list:", "points": ["first point", "second point"]},
    {"table": {"caption": "Details of demand", "headers": ["Head", "Tax (₹)", "Interest (₹)", "Penalty (₹)"],
               "rows": [["CGST", "", "", ""], ["SGST", "", "", ""], ["Total", "", "", ""]]}},
    "Concluding paragraph with the request and time limit ..."
  ],
  "closing": "Yours faithfully,",
  "signatory": {"name": "", "designation": "", "office_line": ""},
  "enclosures": [],
  "copy_to": ["The ... - for information."],
  "key_facts": {
    "taxpayer_name": "", "trade_name": "", "gstin": "", "period": "",
    "document_no": "", "document_date": "", "date_of_communication": "",
    "issuing_authority": "", "amount_involved": "", "amount_in_dispute": "",
    "issue_in_brief": "", "deadline": "", "forum": "", "case_no": ""
  },
  "legal_citations": [{"provision": "", "purpose": "", "basis": "source"}],
  "deadlines": [{"event": "", "date": "", "basis": ""}],
  "missing_or_uncertain": [],
  "source_documents": [{"title": "", "no_and_date": ""}]
}
```
<!-- PROMPT END -->
