# Prompt 05 — NotebookLM: revise after verification

After running prompts 02/03, paste the reviewer's corrections here. NotebookLM returns a corrected JSON, which you paste into Colab Step 5 again.

---
<!-- PROMPT START -->
Revise the letter JSON you produced earlier, using the corrections below. Rules:
- Apply a correction only if the sources support it. If a correction contradicts the sources, do NOT apply it; add a note to "missing_or_uncertain" explaining why.
- Change nothing else.
- Return the complete JSON again (same schema, every key), as ONE valid ```json code block with no citation markers.

CORRECTIONS:
{{CORRECTIONS}}
<!-- PROMPT END -->
