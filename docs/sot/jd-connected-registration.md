# JD Connected Registration SOT

Last updated: 2026-09-23. Applies to Codex and Claude.

This document is the single source of truth for turning a JD source into candidate-facing registration text and proving that Saramin/JobKorea positions or a LinkedIn RPS message template contain what was intended. Runtime-specific skills should link here instead of copying their own portal logic.

## Scope

The workflow covers:

- raw JD capture from pasted text or an official job URL
- company briefing research for candidate-facing context
- semantic unit construction
- deterministic packet generation
- Aside browser portal entry
- saved UI readback
- LinkedIn RPS message-template save and fresh readback when explicitly requested
- one owner report email per registered position when explicitly requested


Live browser operation and final owner-email sending are main-operator-only actions. Subagents or helper lanes may create local owned artifacts, drafts, analyses, and verification inputs, but they must not operate live portal sessions or send owner/candidate emails unless the main operator explicitly transfers that exact action. If a helper sends an outdated or duplicate report, the main operator must send a correction and preserve both message IDs.

The workflow does not imply candidate outreach, bulk posting, unattended login automation, paid actions, ontology/org mapping, or reuse of old company caches unless the user asks for those actions in the current task. An explicit position/template registration request authorizes the requested portal writes and readback, but not any candidate proposal or InMail send. When company context is researched for a JD packet or owner report, attempt LinkedIn company/people organization research as a standard company-intelligence step, record the checked LinkedIn pages and visible organization signals, and report access limits or unknowns. Do not infer reporting lines or role ownership from visible employee names unless the profile evidence supports it.

## Source Identity

User-supplied sources are separate jobs only when the user says so or when company, role, and current source identity do not match. A pasted JD and a URL are often two references to the same job; do not split or merge blindly.

For pasted text:

- preserve the raw text exactly, including truncation
- set `source_kind=pasted_text`
- set `source_status=READY_SOURCE` only after company, position, and body are readable

For URL input:

- fetch the current official page
- verify company, position title, and page body against the user request
- set `source_kind=url`
- set `source_status=READY_SOURCE` only when the page currently matches the requested job
- if the page differs from the pasted prompt, do not blend them; record separate jobs only when identity differs, otherwise mark `NEEDS_SOURCE_REVIEW`

Do not use previous drafts, old generated copy, stale CDP flows, or hidden assumptions as source truth.

## Company Briefing

When company context is requested or needed for candidate copy, check current public sources or approved internal records for business/products, customer·transaction·revenue scale, investment·financial state, and growth direction. Select the facts that materially help a candidate judge the position; do not list every researched category mechanically. Separate `company_fact_status` from `jd_source_status`, dates from current claims, actual results from targets, and MAU from DAU. Unknown facts are omitted rather than softened into claims.

Candidate-facing copy may include sourced facts and careful date labels. Unknown facts are omitted. Do not soften an unknown into a claim. Candidate-facing text must not include internal uncertainty labels such as `unknown`, `not verified`, source IDs, or audit tags. Public measurement bases and dates, such as 국민연금 가입자 수, must remain when needed to avoid misleading headcount claims.

Company introductions in Saramin, JobKorea and Gmail must be substantive and role-linked. They explain what the company builds or sells, its relevant scale or financial/growth context, and why this role matters. A company-name/industry label is a blocked result. Prefer short sourced bullets and clear transitions over one long paragraph, but never treat concise style as permission to delete decision-useful facts. LinkedIn RPS keeps a compressed version of the same core meaning. Keep detailed source URLs and caveats in evidence JSON, not candidate copy.

## Candidate-Facing Removal Rules

Remove these from every portal field and owner email's "registered text" candidate body:

- employer apply URLs, ATS links, career page buttons, and QR codes
- employer direct emails and "apply here" wording
- "자사 지원", "지원하기", "채용페이지에서 지원" style CTAs

Replace next-step language with ValueConnect routing, for example: `후속 절차는 밸류커넥트를 통해 안내드립니다.`

Preserve material hiring process and condition facts such as interview stages, tasks, reference checks, non-standard employment type, meaningful location constraints, mandatory documents, portfolio requirements, licenses, travel constraints, or security/eligibility requirements. Do not spend candidate-facing portal space on generic application boilerplate that professional candidates already understand.

By default, remove generic or obvious candidate-facing boilerplate from Saramin/JobKorea fields and owner-email registered-text blocks when it does not materially change the candidate decision. This includes generic support-document sections, employment type `정규직`, `채용 시 마감`, and self-evident office labels such as a plain office name. Preserve each omitted raw fact in `excluded_units` with `reason` starting `explicit_user_exclusion` or `standing_user_exclusion`, including the instruction basis, source, and captured text. This is an intentional source-coverage exception, not a renderer drop.

## Semantic Units

Before generation, map every substantive raw JD statement to a unit ID or an explicit exclusion reason (direct application routing, site navigation, or duplicate display text). Check conditions and hiring stages line by line. A packet validates curated units, not the completeness of the upstream extraction; missing raw-source coverage blocks entry.

The unit file is the only input to deterministic packet generation. Required top-level fields:

- `company`
- `position`
- `source_url` or source marker
- `captured_at`
- `source_status`
- `jd_id`
- `company_slug`
- `position_slug`
- `units`
- optional `excluded_units`

Each unit must have:

- `id`
- `section`
- `kind`
- `meaning`
- `full`
- `compact`
- `source`

Each `excluded_units` item must have:

- `id`
- `section`
- `reason` beginning with `explicit_user_exclusion`
- `full`
- `source`

Supported sections, in display order: `company`, `team`, `domain`, `role`, `duties`, `requirements`, `preferred`, `growth`, `conditions`, `process`, `documents`.

Core hiring facts use `kind=core` and cannot be dropped. Company and extra units may move between fields to fit portal limits, but each source unit must appear exactly once across the packet fields for that portal unless the packet explicitly returns `BLOCKED` or the raw fact is represented in `excluded_units` under an explicit current-user exclusion.

## Shared CLI Contract

Preferred commands:

```bash
PYTHONPATH=scripts python3 -m jd_channels packet --source <units.json> --channel saramin --output <packet.json>
PYTHONPATH=scripts python3 -m jd_channels packet --source <units.json> --channel jobkorea --output <packet.json>
PYTHONPATH=scripts python3 -m jd_channels readback --packet <packet.json> --observed <observed.json> --output <readback.json>
```

The packet command returns:

- `READY_FOR_UI` when every generated field fits and contains no known forbidden text or portal-risk characters
- `BLOCKED` when length, source, unit assignment, direct-apply text, invisible characters, or portal-risk checks fail

The readback command returns:

- `COMPLETE` when every required persistent field and required transient field has been observed and matches
- `PARTIAL` only for JobKorea when persistent position fields match but transient proposal evidence is incomplete
- `FAIL` on mismatch

Required dependencies are this SOT, the active packet/readback script implementation, and any referenced contracts. If any required dependency is missing in the active tree, record `BLOCKED_DEPENDENCY` and stop that lane. Do not claim automation exists until the command is present and executed in the active tree.

## Portal Field Limits

### Saramin

Fields:

- `hiringTitle`: title, 35 characters max
- `offerComment`: body field 1, 2,000 characters max
- `chargeWork`: body field 2, 2,000 characters max

Use both 2,000-character fields as one candidate-facing surface. A good split usually places company briefing, team, role, growth, conditions, and process in field 1, then duties, requirements, and preferred qualifications in field 2. The split may change as long as facts are preserved exactly once and readback passes.

For candidate readability, `offerComment` should normally start with ValueConnect routing and a substantive `[회사 소개]`, then team/growth/process/remaining conditions. Use concise bullets, but include enough sourced business, product, scale or financial/growth context for the candidate to understand the company and opportunity. Move whole source units between the two body fields with explicit headings when capacity remains; do not leave a maintained unit out because of a fixed default section.

When a user supplies a golden sample, rejects a copy style, or asks to make the rule reusable, preserve the decision as a machine-readable position artifact such as `copy-style-spec.json`. The JSON spec must include the affected channel fields, required company-introduction style, prohibited patterns, preferred patterns, explicit exclusions, source capture paths/hashes where available, and a boundary that the golden sample controls style only, not role facts.

### JobKorea

Fields:

- `GI_PSTN`: title, 50 characters max
- `proposalMessage`: position proposal "제안 내용"; target 3,000 characters including spaces and LF
- `EXEC_WORK`: registration modal "입사 후 업무"; target 1,000 characters including spaces
- `ST`: registration modal "우대사항"; target 1,000 characters including spaces

Observed HTML limits are `proposalMessage maxlength=3000`, `EXEC_WORK maxlength=1000`, and `ST maxlength=1000`. `EXEC_WORK` and `ST` are each 1,000 characters, not a combined budget. Fill duties and requirements first, then preferred content, then any whole team/role/growth/process/condition/domain unit that fits in either permanent field. Keep explicit section headings so a qualification moved into `ST` is still shown as `[자격요건]`. For every unit left in transient `proposalMessage`, record its added character cost, remaining characters in each permanent field, whether a whole-unit move is possible, and the final reason. Any non-company unit that still fits but remains transient blocks completion.

`proposalMessage` retains the substantive company introduction because it is the candidate-facing proposal surface. Keep it concise and sourced, not label-only. Keep generic application-document boilerplate out; do not spend transient proposal space on statements professional candidates already know.

`proposalMessage` is transient proposal content unless a screen proves otherwise. It must be injected and verified for each candidate proposal or position proposal operation. Do not report it as saved permanent position content merely because the permanent modal saved.

If `GI_PSTN` is disabled in JobKorea, treat the observed disabled title as the canonical portal identity for that saved record. Do not overwrite it blindly. If the disabled title differs from the intended packet title, report the binding explicitly and decide whether the existing portal record is the correct target before saving.

### Gmail candidate JD

Gmail candidate copy has no portal or RPS length cap. Produce a standalone message with the substantive company introduction and every maintained team, mission, role, duty, requirement, preference, growth opportunity, material condition and core hiring stage. It is not an owner operation report, and an operation report cannot replace it. Excluded boilerplate remains only in restricted local evidence.

### LinkedIn RPS

Use 1,900 characters as an internal authoring limit, not a claim about the latest platform limit. Count the exact scope as subject + one blank line + body with `measure.compose()`. Keep a compressed company introduction and clear headings for duties, requirements and preferences. Preserve responsibility scope, years, core capabilities, key figures and material conditions; reduce repeated greetings, long endings and CTA repetition before considering any non-core omission. Do not run RPS external actions unless explicitly requested.

When template registration is explicitly requested, use the exact identity `[포지션]{회사명}, {포지션명}` for both template name and subject unless the user supplies another name. Search both personal and shared templates for that exact identity before creation. Save the message template as visible to `Anyone in my organization`, then reload the template-management page, search the exact name, reopen it, and compare template name, subject, body, visibility and measured length. Template registration never authorizes candidate selection or InMail sending.

## Aside Operation

Use the Aside browser and the user's existing logged-in portal sessions. The main operator owns live browser work; do not delegate live portal manipulation to subagents. Do not implement or call legacy automatic login, fixed browser credentials, old CDP snippets, or employment defaults.

Before saving:

- confirm the target portal and company/position identity
- check for duplicate existing position records
- paste packet field values exactly
- close autocomplete/chip UI only after the selected value is visibly committed
- capture field counts and any portal warnings

After saving:

- reopen the saved position or proposal
- read every field back from the UI
- for new observations, record both `fresh_saved_position` and `persisted_reopen`; a current-screen value without a persisted reopen is not saved readback
- normalize only documented portal transformations
- compare against the packet with the readback CLI
- preserve screenshot/HTML/text artifacts outside git if they contain portal or candidate data

For LinkedIn RPS template registration, a save toast is only intermediate evidence. Reload the message-template page, search the exact name, reopen the saved template, and record exact subject/body/visibility comparison. Do not use a candidate profile or send flow when the template-management page can perform the authorized save directly.

Success messages, toast notifications, and "button clicked" states are not completion evidence.

## Known Portal Transformations

Current measured transformations:

- JobKorea stores bullet `•` as `?` (2026-09-22 fresh reopen); render it as ASCII `-` before entry.
- JobKorea stores en dash as `?`
- JobKorea permanent fields convert ASCII `>` into `≫`. For interview process separators, use `→` in semantic units; it survives JobKorea and becomes `>` in Saramin. Do not silently normalize failed readback away.
- JobKorea stores single quotes as backticks
- Saramin deletes right arrow `→`
- Saramin encodes ASCII single quote as literal `&#39;` on edit readback. Adjust quotation formatting in semantic units before entry; do not normalize this away as successful exact storage.

The renderer should sanitize these before UI entry. If a new transformation appears during readback, record it and do not pass the registration until packet generation or expected comparison accounts for it.

## Live Observations

These are observed portal outcomes, not universal guarantees.

- Saramin QA Manager live save: saved position `1731926`; two body fields measured 1,107 and 1,048 characters; saved readback matched.
- JobKorea QA live save: existing title field was disabled and displayed `뤼튼, QA`; group `1505694`, old position `1598265` updated to `1600822`; permanent fields measured 571 and 475 characters; saved position readback matched exactly.
- JobKorea QA proposal: proposal text measured 1,103 characters and filled exactly on the active proposal screen, but after save-checkbox and reopen it reset to the 112-character default. No candidate was sent. Therefore position status was `COMPLETE`, proposal status was `NOT_SAVED`, and overall status was `PARTIAL`.

- Bunjang Global Team Lead live save: Saramin `1833171`, body fields 1810/1410; JobKorea group `1506767`, final position `1600840`, body fields 1000/715. Permanent fields matched fresh readback. Proposal1503 reset to112 on reopen, so proposal `NOT_SAVED`.
- Bunjang Global Business Manager LinkedIn RPS template: `[포지션]번개장터, Global Business Manager` saved organization-visible; fresh reload/search/reopen matched template name, subject and 1,051-character body exactly. Internal subject + blank line + body measurement was 1,087/1,900. No candidate InMail was sent.

This observation creates a rule: when JobKorea proposal text is required for a candidate send, replay the proposal packet into the proposal field during that authorized send operation and verify the active proposal screen. Do not mark the whole JobKorea job `COMPLETE` unless both the persisted position fields and the required proposal state are proven for the specific operation. Proposal completion additionally requires `fresh_saved_proposal=true` and a proposal ID; position reopen evidence alone is insufficient.

## Owner Report Email

Send only when the user explicitly requested it or the current task instruction already authorized it. If already authorized, do not ask for a second approval before the owner report. Send one email per position after its requested portal outcomes are verified, to the explicit recipient.

The email must include:

- portal name
- company and position
- saved position id and proposal id when available
- packet status and readback status
- field names and character counts
- the source URL/marker and per-item coverage summary; never excluded original text or a raw-source appendix
- exact registered text for each field
- partial status and reason, if any
- remaining caveats such as `proposalMessage` transient verification
- excluded-unit IDs/categories/counts and their instruction basis, without reproducing removed text
- LinkedIn/company organization research scope when requested, including sources checked and unresolved unknowns

Do not combine two positions into one report when the user asked to process them separately.

## Status Vocabulary

Use these exact labels in artifacts and reports:

- `READY_SOURCE`: source captured and suitable for unit extraction
- `NEEDS_SOURCE_REVIEW`: source missing, changed, or conflicting
- `READY_FOR_UI`: packet generated and safe to enter
- `BLOCKED`: packet cannot safely be entered
- `UI_ENTERED`: fields entered but not saved/read back
- `READBACK_COMPLETE`: saved UI readback matches packet
- `READBACK_PARTIAL`: only part of the required UI readback is proven
- `PROPOSAL_NOT_SAVED`: JobKorea proposal text was observed in the active proposal screen but did not persist after reopen
- `EMAIL_SENT_VERIFIED`: owner report sent and sent-mail/readback evidence recorded

For a Saramin registration, `READBACK_COMPLETE` plus `EMAIL_SENT_VERIFIED` completes a user request that asks for actual registration and report email. For JobKorea, permanent position readback can be complete while proposal readback is `PROPOSAL_NOT_SAVED`; that outcome is `READBACK_PARTIAL`, not whole-job complete.


## Evidence boundary and packet integrity

`source_hash_version=2` covers company, position, source URL/status, JD ID and unit IDs/sections/full text. Readback recomputes it, rejects unresolved packet errors, and validates raw counts and field content. It detects inconsistent or accidentally modified artifacts; it is not a signature or authority to write/send. The operator must capture real browser state. Fabricating `observed.json` can fabricate evidence, so retain the original capture and its time/URL outside git, and do not describe this as tamper-proof browser attestation.

Disabled-title binding only accepts the title value already in the reviewed packet. Adding `approved_bound_title`, `title`, or similar alias metadata cannot authorize a different title during comparison. Before an existing disabled-title update, verify the target record and construct the reviewed packet using its actual retained title, recording the source role and before/group IDs.

Readback JSON is the result artifact. Input packets remain immutable generation artifacts; their initial `NOT_VERIFIED` markers are not overwritten by the readback command. Read the result file. Exit code 3 requires inspection of `position_status` and `proposal_status`; it is never an unqualified success code.

See [Aside operations](jd-aside-operations.md) for the repeated browser procedure. The tested local/manual workflow does not provide unattended registration, server-side browser attestation, or candidate-send automation.

## 2026-09-22 원문 보존 및 보고 재노출 방지

사람인의 “3구획”은 현재 로그인 편집·미리보기/상세 UI에서 구획명·DOM ID·글자 제한·표시 순서·영구 저장을 먼저 확인한다. 제목을 본문으로 쓰지 않고 가상의 본문 필드를 만들지 않는다. 이번 편집 관찰은 포지션명/제안 내용/업무 내용, 35/2000/2000자다. 후보자 상세 화면의 확인 범위는 실행 증빙에 별도로 남긴다.

공식 원문 각 문장/항목과 실제 새 저장값의 대응을 source-coverage.json에 기록한다. ID, 원문, 대상 필드/의미 구획, 실제 대응 문장, 원문 유지/의미 동일 편집/명시 삭제/미배치, 출처 및 저장 증거가 필수다. 패킷끼리의 일치는 원문 추출의 완전성을 증명하지 않는다. 승인된 삭제 외 핵심 미배치는 완료를 차단한다. 임시 제안 입력은 저장 대응으로 계산하지 않는다.

상시 제외: 일반 지원 안내 구획과 지정 푸터 전체, 자유양식 이력서 안내, 직무 무관 개인정보 및 연봉 삭제 안내, 허위기재 취소, 취업보호 우대, 제출서류 삭제 안내, 직접 지원 이메일, 일반적인 정규직/마감/오피스 문구. 전형 단계의 추가/생략 안내는 공백·구두점·줄바꿈·같은 의미 변형까지 제외한다. 계약직·수습·해외 근무/이주·필수 출장·교대근무·필수 자격·포트폴리오 등 판단을 바꾸는 조건, 핵심 전형, 후보자 동의 후 레퍼런스 체크는 유지한다.

삭제 원문은 로컬 raw-source/excluded_units에만 보존한다. 보고 메일 전체에도 원문 보관 부록으로 재노출하지 않는다. 제외 내역은 ID·범주·건수로 보고한다. 계약 JSON의 copy_policy와 jd_channels.copy_policy.exclusion_hits를 포털 필드 및 전체 보고 본문에 적용하고, 정규식 밖 의미 변형은 직접 검토한다. 메일의 operation ID를 발송 전 보낸편지함에서 검색하고, 한 번 발송 후 수신자·본문 전체·ID·시각을 대조한다.

### 폐기된 2026-09-22 실행 판단과 사실 보존

과거 실행은 사람인 1833171 제목/제안/업무 21/932/1383자, 잡코리아 그룹 1506767·포지션 1601701 제목/업무/ST 21/982/582자, 제안 749자 입력 뒤 112자 기본값 복원을 관찰했다. 당시 유지 대상 37개 중 잡코리아 영구 필드 29개·임시 제안 8개로 보고했고 회사 소개를 라벨형으로 축소했다. 이 수치와 readback은 과거 사실로 보존하지만, 회사 소개 축소와 영구 필드 여유를 두고 원문을 transient에 남긴 판단은 `SUPERSEDED`이며 활성 작성 규칙으로 재사용하지 않는다.
