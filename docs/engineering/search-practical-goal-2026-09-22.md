# Search practical sourcing goal - 2026-09-22

## Conclusion

Search 문서의 목표는 빠른 실전 후보 발굴을 막던 운영 해석 공백을 닫는 것이다. 이번 변경은 새 프레임워크를 만들지 않고 Aside 실행, 막힘 처리, 실전 우선순위, 금지선을 SOT와 skill에 반영한다.

## Scope

- Target worktree: `/Users/kangsangmo/Desktop/Valuehire_search_ci_boundaries_20260922`
- Current HEAD at start: `eaaee6219ed63d8ed4be1d52a3977216a15e5a03`
- Start evidence time: `2026-09-22 15:27:13 KST`
- User target positions for the following live sourcing run:
  - `https://team.bgzt.co.kr/job_posting/OZwO7CPA`
  - `https://team.bgzt.co.kr/job_posting/02o6EksJ`

## Acceptance Criteria

- When a Search run starts and an approved recruiting channel is logged out, the workflow must try normal Aside saved-session or ordinary login recovery when available, then save the blocked channel checkpoint and continue other channels if MFA, CAPTCHA, access policy, or session limits block progress.
- When candidates are ranked for proposal priority, the workflow must keep practical preferences separate from the JD score and record field-level evidence for stability, current freelance/full-time readiness, Seoul work accessibility, and former target-company status.
- If nationality or national origin would be used as a ranking signal, the workflow must reject that signal and use only job-relevant Korean communication, domestic work authorization, or location accessibility when directly evidenced.
- If "인서울 후보자" is ambiguous, the workflow must treat it as Seoul work accessibility for this run unless a lawful job-related meaning is explicitly defined, and must not convert it into a school-prestige criterion.
- If a candidate is confirmed as a former employee of the target company, the workflow must preserve evidence but exclude the candidate from the new-proposal shortlist for that target company.

## Counter-AC

- The agent asks a routine question and stops despite having enough SOT guidance to continue a non-destructive search path.
- A candidate is favored or rejected because of inferred nationality from name, photo, school, language, or employer.
- "인서울" becomes an undocumented university-prestige filter.
- A current freelancer is automatically rejected without checking full-time readiness.
- A former target-company employee is deleted from evidence instead of preserved and excluded from the new-proposal shortlist.

## Boundary Contract

Inputs are JD URLs, current user run instructions, channel login state, and observed candidate/profile evidence. Outputs are updated SOT/skill instructions plus later run artifacts for each target position. External writes, email sending, candidate outreach, commits, pushes, and global installs are outside this document update.

## Validation Plan

- Read `docs/sot/strict-workflow.md`, `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, Search skill, and `docs/sot/candidate-search.md`.
- Run `bash scripts/acceptance-principles-check.sh`.
- Run `python3 /Users/kangsangmo/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/search`.
- Run `git diff --check`.
- Review the diff to confirm only the scoped Search skill, candidate-search SOT, and this goal document changed.

## Verification Ledger

- `bash scripts/acceptance-principles-check.sh` at strict start: `PASS`, output showed `CHECKED: 34`.
- `python3 /Users/kangsangmo/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/search`: `NOT_RUN`, default `python3` failed before validation with `ModuleNotFoundError: No module named 'yaml'`; no package install was performed.
- `git diff --check -- .agents/skills/search/SKILL.md docs/sot/candidate-search.md`: `PASS`, exit 0.
- Basic document scan for the two edited docs plus this goal: `PASS`, no trailing whitespace, tabs, or missing skill frontmatter opener.
- `bash scripts/acceptance-silent-failure-lint.sh ...`: `NOT_RUN_FOR_DOCS`, the script reported `CHECKED_FILES: 0` and fail-closed for these document targets.
- Independent V1/V2 were not run for this narrow document update; report as `NOT_RUN`, not `PASS`.
