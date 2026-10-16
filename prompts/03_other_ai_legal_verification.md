# Prompt 03 — Second AI (ChatGPT / Claude / Gemini): legal, limitation & format audit

Use a **different** AI from the one that drafted the letter, so its mistakes aren't repeated. If you can, also attach the source PDF(s) and switch on web search, so it can check the current text of the Act and rules on cbic-gst.gov.in.
Colab Step 7 fills in all the `{{...}}` blanks automatically.

---
<!-- PROMPT START -->
Act as a meticulous reviewing officer (Assistant/Deputy Commissioner, Legal) of CBIC, with expert knowledge of the CGST Act, 2017, CGST Rules, 2017, IGST Act, 2017, the Tamil Nadu GST Act, 2017, CBIC circulars/instructions, and Government of India drafting practice (CSMOP). Audit the draft letter below before it is signed.

CONTEXT
- Letter type: {{LETTER_TYPE_LABEL}}
- Purpose: {{INSTRUCTION}}
- Today's date: {{TODAY}}
- Automatic checks already run by the software (verify these too, don't just trust them):
{{AUTO_CHECKS}}

TASKS
1. LEGAL PROVISIONS. For every Section / Rule / Form / Notification / Circular cited (list below, plus any you find):
   a) Is it the correct provision for the stated purpose? Is the sub-section/clause right?
   b) Is it still in force in that form today? Flag amendments, substitutions or omissions (e.g. Sections 73/74 vs 74A for FY 2024-25 onwards; Section 109 substituted in 2023; pre-deposit caps under Sections 107(6)/112(8); Section 128A).
   c) Is the Act named correctly at first mention, and is the corresponding State GST Act provision cited where needed?
   d) Is there a provision that SHOULD have been cited but wasn't?
   Cited provisions: {{CITATIONS}}
2. LIMITATION & DATES. Recompute every deadline and time limit from the base dates in the facts. Show the working, e.g. "communicated 12.04.2026 + 6 months = 12.10.2026". Check that dates are in a logical order and that no statutory time limit has expired.
3. INTERNAL CONSISTENCY. Names, GSTINs, document numbers and amounts must be identical everywhere. Totals must add up, and amounts in figures must match amounts in words. Also verify each GSTIN check digit.
4. MANDATORY ELEMENTS. File No., DIN (mandatory for communications to taxpayers — Circular 122/41/2019-GST), date, correct addressee and designation, subject ending "- reg.", references with number and date, a clear request with a time limit, signatory name and designation, enclosures, copy-to.
5. LANGUAGE & TONE. Formal Government of India English. Unambiguous, no admissions against Revenue's interest, no tone that is too strong or too weak for a legal communication.
6. RISK. Anything that could make the letter legally defective or open to challenge (e.g. natural justice, jurisdiction, limitation, wrong forum, monetary limits for departmental appeals under Circular 207/1/2024-GST).

RULES FOR YOU
- Do not assume facts. If something can only be checked against the source document, write "VERIFY WITH SOURCE".
- If you are not sure about the current legal position, say "UNSURE" and say what to check. Do not guess.
- Quote the exact wording you want changed.

OUTPUT FORMAT
A. Issues table: | # | Where (para/line) | Issue | Severity (Critical/Major/Minor) | Exact correction | Confidence (High/Med/Low) |
B. Provision-by-provision verdict: | Provision | Correct? | Current status | Comment |
C. Limitation working.
D. Corrected text — ONLY the paragraphs that change, ready to paste.
E. Final verdict: READY TO ISSUE / READY AFTER MINOR FIXES / NOT READY.

===== EXTRACTED FACTS (from source, via NotebookLM) =====
{{KEY_FACTS}}

===== DRAFT LETTER =====
{{LETTER_TEXT}}
===== END =====
<!-- PROMPT END -->
