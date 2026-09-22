---
name: jd
description: Build candidate-facing JD registration packets from a pasted JD or official job URL, then guide Saramin/JobKorea registration, readback, and one approved owner email per position through the shared ValueConnect SOT.
---

# JD Connected Registration

Use this skill when the user asks to turn a JD into portal-ready candidate-facing text for Saramin, JobKorea, LinkedIn RPS, or an owner report. First resolve the repository root with `git rev-parse --show-toplevel`, then read `docs/sot/jd-connected-registration.md` from that root before acting. If the repository root, SOT, required scripts, or required contracts are missing, stop with `BLOCKED_DEPENDENCY` instead of falling back to another copy.

This is the shared entrypoint for Codex and Claude. Do not fork separate logic by runtime. The model may differ; the source contract, field limits, packet schema, readback rules, and reporting gates do not.

## Non-Negotiables

- Treat supplied JD sources as one job only when company, role, and current source identity match, or when the user explicitly says they are the same. A pasted JD and a URL are often the same job; do not split or merge blindly.
- Preserve the raw source identity. For pasted text, save the text as the source. For URLs, fetch the official page and verify that the current page title/company/role matches the requested job before using it.
- Remove employer direct-apply routes from every candidate-facing field: ATS links, apply buttons, career-page CTAs, direct emails, QR codes, and "apply here" language. Route the next step through ValueConnect only.
- Keep JD facts and company facts separate. Employer JD text is evidence for role requirements; company briefing facts need their own sources or must be marked unknown.
- Do not fabricate company briefing facts. Check current evidence for business/products, customer·transaction·revenue scale, investment·financial state, and growth direction; select only facts that help a candidate judge the role, with dates and actual-versus-target labels.
- Saramin, JobKorea, and Gmail require a substantive company introduction that explains what the company does and why the role is worth considering. Concise means removing repetition and long endings, not replacing the introduction with a company-name/industry label. LinkedIn RPS keeps the same core meaning in compressed form.
- When the user corrects copy against a golden sample or asks to preserve a writing/style rule, create or update a machine-readable `copy-style-spec.json` artifact for the position. The spec must name the affected fields, company-introduction style, prohibited patterns, preferred patterns, explicit exclusions, source captures, and the golden basis used for style only.
- Remove generic application boilerplate and obvious candidate-facing filler by default when it does not materially change the candidate decision, including generic support-document sections, `정규직`, `채용 시 마감`, and self-evident office labels. Keep the raw fact in `excluded_units` with an `explicit_user_exclusion` or `standing_user_exclusion` reason instead of putting it in portal fields. Preserve material exceptions such as contract status, meaningful location constraints, mandatory documents, portfolios, licenses, travel constraints, or eligibility requirements.
- Do not send candidate messages or publish broadly unless the user explicitly authorizes that external action. A portal registration or owner report email is authorized only when the user has asked for it.
- Live browser operation and final owner-email sending are main-operator-only actions. Helper lanes may create local artifacts, drafts, and verification inputs, but must not operate live portal sessions or send owner/candidate emails unless the main operator explicitly transfers that exact action.
- One position produces one owner report email covering its requested portal outcomes when already authorized. Include the source URL and coverage summary (never an excluded raw-source appendix), exact entered fields, and partial status when readback is partial; do not ask for a second approval just to send the already-requested owner report.

## Source coverage and standing exclusions

- Inspect the current logged-in Saramin edit and preview/detail UI before interpreting "three sections". Record labels, DOM IDs, limits, persistence and display order; never use the title as body or invent another body field.
- Map every original sentence/item to a source-unit ID in `source-coverage.json`, with original text, target field/section, actual fresh saved counterpart, status (verbatim / equivalent edit / explicit exclusion / unplaced), and evidence. Packet-to-packet equality alone is not coverage. Unplaced role facts block completion.
- Exclude the full generic application/footer block, generic document instructions, cancellation/protected-applicant notices, direct employer email, and designated ordinary conditions. Preserve material conditions such as contract status, probation, overseas work/relocation, mandatory travel or shifts, licenses and portfolios once in the clean body.
- Exclude hiring-stage addition/omission language, including punctuation, whitespace and semantic paraphrases. Retain the core stages and consent-based reference checks. Run the shared `jd_channels.copy_policy.exclusion_hits` on portal copy and the entire report body; also review semantics because finite patterns cannot prove every paraphrase absent.
- Deleted source text belongs only in local raw-source/excluded_units evidence. Never append it to the owner email under any preservation/original-source heading. Report exclusion IDs, categories and counts instead.
- An operation ID must be checked against sent mail before sending a single final report. An uncertain send requires sent-mail readback before retry.

## Workflow

1. Create a raw source record for each job under the current task artifacts path. Include `source_status`, `source_url` or `source_kind=pasted_text`, capture time, company, position, and a hash of the raw text.
2. Research current company evidence whenever candidate-facing copy needs company context. Keep sources and dates in evidence; omit unverified claims. Select role-relevant business/product, scale, investment/financial and growth facts instead of mechanically listing every researched category, and never reduce the result to a company-name/industry label.
3. Convert the JD into semantic units. Units are the only input to packet generation; do not trim text by substring to fit portal limits. For explicitly excluded boilerplate, add `excluded_units` with `reason` beginning `explicit_user_exclusion`.
4. Run the shared CLI:

   ```bash
   PYTHONPATH=scripts python3 -m jd_channels packet --source <units.json> --channel saramin --output <saramin-packet.json>
   PYTHONPATH=scripts python3 -m jd_channels packet --source <units.json> --channel jobkorea --output <jobkorea-packet.json>
   ```

   If `python3 -m jd_channels` or the documented packet/readback implementation is missing in the active tree, report `BLOCKED_DEPENDENCY`. Do not silently fall back to legacy CDP, automatic login, fixed June copy, or old position-register defaults.
5. For portal work, the main operator uses the Aside browser with the user's logged-in session. Do not delegate live browser operation to subagents. Fill exactly the packet fields, save, reopen/read the saved view, and compare with:

   ```bash
   PYTHONPATH=scripts python3 -m jd_channels readback --packet <packet.json> --observed <observed.json> --output <readback.json>
   ```

6. Only report a portal registration as complete when saved UI readback matches the packet, portal character transformations are accounted for, and duplicate/position identity checks have been recorded.
7. Send an owner email only when the current task explicitly authorizes it. A Gmail candidate JD and an owner operation report are separate artifacts; never substitute one for the other.

## Field Contract Summary

- Saramin: title <= 35 chars, two candidate-facing body fields <= 2,000 chars each. Split a substantive company introduction and maintained JD units across both fields without losing facts; move whole units with explicit headings when the normal section runs out of room.
- JobKorea: title <= 50 chars. Proposal message HTML `maxlength` is 3,000 chars including spaces and line breaks. Permanent `입사 후 업무` and `우대사항` fields are each 1,000 chars. Fill permanent fields with every whole substantive JD unit that fits before leaving it only in transient proposal content; record per-unit required and remaining characters. Keep requirement/preference headings when content crosses fields.
- Gmail: no portal/RPS cap. Produce a standalone candidate JD with a substantive company introduction and all maintained substantive units.
- LinkedIn RPS: internal authoring limit 1,900 characters for subject + blank line + body; do not present it as a verified current platform limit. Keep a compressed company introduction and clear responsibility/requirement/preference structure.

For full rules, transient JobKorea proposal handling, field names, and statuses, use the SOT. Read `docs/sot/jd-aside-operations.md` for the verified browser operation sequence.
