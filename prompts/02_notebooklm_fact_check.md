# Prompt 02 — NotebookLM: fact-check the generated letter against the sources

NotebookLM has the source documents, so it is the best checker for **facts** (names, numbers, dates, amounts).
Colab Step 7 fills in the letter text below automatically. Paste the result into the **same** NotebookLM notebook.

---
<!-- PROMPT START -->
Below is the FINAL TEXT of a letter generated from the sources in this notebook. Fact-check it strictly against the sources.

For EVERY factual item in the letter (names, trade names, GSTINs, addresses, document numbers, DINs, dates, periods, amounts, section/rule numbers, authorities, case numbers, hearing dates):
1. Find it in the sources.
2. Compare character by character.

Reply in this format:

A. TABLE: | # | Item in letter | What the source says | Match (✅ exact / ❌ wrong / ⚠️ not in source) | Source reference |
   List every ❌ and ⚠️ first, then the ✅ items.
B. Important facts in the sources that the letter LEFT OUT but should mention.
C. Statements in the letter that the sources do not support (possible hallucinations).
D. The exact corrected sentence for each ❌.
E. One-line verdict: "FACTS VERIFIED" or "CORRECTIONS NEEDED (n)".

Do not rewrite the whole letter. Do not judge style. Facts only.

===== LETTER TEXT START =====
{{LETTER_TEXT}}
===== LETTER TEXT END =====
<!-- PROMPT END -->
