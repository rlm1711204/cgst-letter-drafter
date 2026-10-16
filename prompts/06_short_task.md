# Prompt 06 — SHORT chat prompt (for NotebookLM's chat box limit)

Use this together with the **rules sheet** (Colab Step 1 ▸ "Rules sheet"), added ONCE to the notebook as a source: *Add source ▸ Copied text ▸ paste*. The short prompt below then fits easily in the chat box.

---
<!-- PROMPT START -->
Use the source that begins "{{RULES_TITLE}}" ONLY as your instruction sheet (it is not evidence). Take facts only from the other sources.
Document: {{FORMAT_LABEL}}{{TYPE_LINE}}
Task: {{INSTRUCTION}}
Office: {{FROM_OFFICE}} | Signatory: {{SIGNATORY}}
File No: {{FILE_NO_SHOW}} | DIN: {{DIN_SHOW}} | Date: {{LETTER_DATE}}
Follow every rule and the row/field guidance in that sheet. Return ONLY the ```json block in the exact schema of that sheet: valid JSON, no [1] citation markers, missing facts as [TO BE CONFIRMED: ...].
<!-- PROMPT END -->
