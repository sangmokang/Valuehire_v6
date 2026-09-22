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
- Do not fabricate the nine company briefing facts: history, financial state, funding stage, cumulative funding, product lineup, recent CEO interview, CEO profile, location, headcount.
- Do not send candidate messages or publish broadly unless the user explicitly authorizes that external action. A portal registration or owner report email is authorized only when the user has asked for it.
- One position produces one owner report email covering its requested portal outcomes when already authorized. Include the original JD source, exact entered fields, and partial status when readback is partial; do not ask for a second approval just to send the already-requested owner report.

## Workflow

1. Create a raw source record for each job under the current task artifacts path. Include `source_status`, `source_url` or `source_kind=pasted_text`, capture time, company, position, and a hash of the raw text.
2. Research the company briefing facts from current sources when the user requests a briefing or when candidate-facing portal text needs company context. If a value is unverified, write `unknown` internally and omit it from candidate copy.
3. Convert the JD into semantic units. Units are the only input to packet generation; do not trim text by substring to fit portal limits.
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
7. After each completed registration, send the approved owner email to the explicitly requested recipient. The email body must include channel, position id/proposal id when available, field names, counts, exact registered text, and readback result.

## Field Contract Summary

- Saramin: title <= 35 chars, two candidate-facing body fields <= 2,000 chars each. Split company briefing plus JD facts across the two fields without losing facts.
- JobKorea: title <= 50 chars. Proposal message HTML `maxlength` is 3,000 chars including spaces and line breaks. Permanent modal fields `입사 후 업무` and `우대사항` each have HTML `maxlength` 1,000 chars; they are not a combined 1,000-char budget. Use proposal message to carry substantial company/JD context because the permanent fields are tight. If the title field is disabled, bind the packet identity to the exact observed disabled title instead of overwriting it.
- LinkedIn RPS: 1,900 chars total. RPS is a compact candidate message, not a portal registration body.

For full rules, transient JobKorea proposal handling, field names, and statuses, use the SOT. Read `docs/sot/jd-aside-operations.md` for the verified browser operation sequence.
