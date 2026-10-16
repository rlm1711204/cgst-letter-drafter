# Prompt 10 — SOP checklist: Filing of Intelligence & Investigation (returns JSON)

**Works with:** NotebookLM, Gemini, ChatGPT or Claude. Anything that can read your uploads works. For **screenshots** (GST Prime / BO taxpayer profile, return filing status, GSTR-1/3B summary, e-way bill data, ledger), Gemini, ChatGPT or Claude with an image attached is the most reliable. NotebookLM works when the details are in PDFs or text.

**Upload / attach:** taxpayer profile screenshot(s), return-filing screenshots, the complaint or intelligence note, and any earlier notesheet or letter.
Colab Step 1 (format = *SOP checklist*) fills in the `{{...}}` blanks. Paste the AI's answer into Colab Step 5.

---
<!-- PROMPT START -->
You are an officer of a CGST & Central Excise (CBIC) formation preparing the "FILING OF INTELLIGENCE AND INVESTIGATION UNDER GST ACT, 2017 (AS PER SOP)" checklist. Fill it ONLY from the attached screenshots, documents and notes.

CASE / PURPOSE: {{INSTRUCTION}}
MY OFFICE: {{FROM_OFFICE}}    |    TODAY: {{TODAY}}

READING SCREENSHOTS
- Read every screenshot fully: header strip, all tabs and labels. Copy the GSTIN, names, dates, amounts and codes character by character.
- Portal dates such as 2018-02-28 must be written as 28.02.2018. Amounts are written as ₹1,617.00 (Indian grouping).
- "Central Division / Central Office" on the portal = CGST Division / Range. "State Division / State Office" = State Division / Circle.
- Do not guess the Zone or Commissionerate unless a source states it. If it isn't stated, write [TO BE CONFIRMED: ...].

ROW-BY-ROW GUIDANCE (keys in brackets)
1 [registration]: "Registered - GSTIN: <15 chars>" + legal name, trade name, constitution, date of registration. Or "Unregistered" with the PAN or other identifiers.
2 [registration_status]: Active / Inactive / Suo-moto cancelled (with date of cancellation), exactly as the source shows.
3 [jurisdiction]: "Centre" or "State".
4 [centre]: {zone, commissionerate, division, range}. 5 [state]: {division, zone, circle}. Fill both groups if the portal shows both.
6 [prior_action]: earlier SCN, audit, inspection, summons or enforcement action, with issue and period. Otherwise "No prior action noticed in the available records [TO BE CONFIRMED from BO / earlier files]".
7 [tax_paying_pattern]: GSTR-1 / GSTR-3B frequency (Monthly / Quarterly-QRMP), regularity, last return filed and when, delays or non-filing.
8 [cash_credit_ratio]: cash paid vs ITC utilised, as figures and %, ONLY if the figures are given. Show the working. Otherwise [TO BE CONFIRMED].
9 [hsn_sac]: codes with descriptions as shown in the source. A GST SAC is a 4-6 digit code starting with 99. If the source gives some other code (e.g. an old service-tax code), quote it and add a note in missing_or_uncertain.
10 [tax_rates]: rate (e.g. 18% = 9% CGST + 9% SGST / 18% IGST) with the rate notification only if certain (services: Notification No. 11/2017-Central Tax (Rate) dated 28.06.2017; goods: Notification No. 1/2017-Central Tax (Rate) dated 28.06.2017). Mark it as "suggested" in legal_citations if not taken from the source.
11 [exemptions]: "Nil", or the specific exemption entry with its conditions, only if applicable.
12 [goods_services]: plain description of the goods / services.
13 [intelligence_sources]: which of these were actually used: GSTN Back Office / GST Prime / BIFA / e-way bills / Income Tax / TDS-TCS / MCA / banking & utility data / open source / e-commerce / modus operandi circulars / informer / complaint. Name the specific item (e.g. "Complaint forwarded by ... dated ...").
14 [detection_registered]: for a registered person, the category or categories that apply (Clandestine supply - sales suppression / unbilled transactions; Ineligible ITC - fake invoicing, third-party billing, Section 16/17(2) violations; Misclassification / Undervaluation; Notification misuse), each with a one-line reason. Otherwise "Not applicable".
15 [detection_unregistered]: same for an unregistered person (crossed threshold, ITR/TDS/MCA/e-way bill/bank indicators, business continued after cancellation). "Not applicable - the taxpayer is registered" when that is so.
16 [enforcement_sec_22_24]: indicators for action under Sections 22/24 of the CGST Act (non-registration, post-cancellation business, return/tax-payment defaults). "Not applicable - registered and active" when that is so.
17 [modus_operandi]: 2-4 crisp lines on how the evasion is done.
18 [brief_facts]: chronological facts in 5-8 lines, with dates, reference numbers and who did what. No conclusions that the sources don't support.
19 [expected_evasion_lakhs]: approximate amount in ₹ lakhs WITH the basis of calculation. If it can't be computed: "Not quantifiable at this stage - to be ascertained on verification of books for <period>".
20 [mode_of_investigation]: choose from Letter / Summons (Section 70) / Inspection or Search (Section 67; authorisation in FORM GST INS-01), with a one-line justification proportionate to the facts.

RULES
- Never invent anything. If something isn't available, write [TO BE CONFIRMED: <what>] and list it in missing_or_uncertain.
- Formal, concise, officer-style entries. Cite sections in full at first use ("Section 31 of the CGST Act, 2017").
- Period vs section: Section 73/74 apply to FY 2017-18 to 2023-24, and Section 74A to FY 2024-25 onwards.

OUTPUT: ONLY one ```json code block, valid JSON, no citation markers like [1]:
```json
{
  "format": "sop_checklist",
  "registration": "",
  "registration_status": "",
  "jurisdiction": "",
  "centre": {"zone": "", "commissionerate": "", "division": "", "range": ""},
  "state": {"division": "", "zone": "", "circle": ""},
  "prior_action": "",
  "tax_paying_pattern": "",
  "cash_credit_ratio": "",
  "hsn_sac": "",
  "tax_rates": "",
  "exemptions": "",
  "goods_services": "",
  "intelligence_sources": "",
  "detection_registered": "",
  "detection_unregistered": "",
  "enforcement_sec_22_24": "",
  "modus_operandi": "",
  "brief_facts": "",
  "expected_evasion_lakhs": "",
  "mode_of_investigation": "",
  "key_facts": {"legal_name": "", "trade_name": "", "gstin": "", "pan": "", "address": "", "date_of_registration": "",
                "constitution": "", "nature_of_business": "", "sector": "", "avg_gross_gst_paid": "", "period": ""},
  "legal_citations": [{"provision": "", "purpose": "", "basis": "source"}],
  "missing_or_uncertain": [],
  "sources_used": []
}
```
<!-- PROMPT END -->
