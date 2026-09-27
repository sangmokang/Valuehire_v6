# Goal — Codex·Claude Strict 패리티와 SOT 고정 (2026-09-10)

## 결론

Codex와 Claude의 `$strict` 실행면을 동일한 저장소 정본에 연결하고, 기능 구현 순서를 DB/API 계약·Type·counter-AC·WU·TDD·적대검증·PR SHA 검증까지 고정한다.

## 발견된 드리프트

- 기존 전역 스킬은 Codex 352줄, Claude 133줄로 내용과 상태기계가 달랐다.
- RED 직후 Draft PR은 현재 `pre-push` acceptance 게이트와 충돌하므로 허용할 수 없다.
- Type은 별도 원칙이 아니라 DB/API 계약의 표현이며, 코드량 한도는 P11이 단일 소유한다.
- 실행 가능한 LLMOps 평가셋은 현재 저장소에서 확인되지 않으므로 구현 완료 증거로 사용할 수 없다.

## 고정한 변경

- `docs/sot/strict-workflow.md`: 공통 실행 순서·적응형 등급·Type/DB/API 관계·PR 경계·자동화/운영 증거·드리프트 판정의 SOT.
- `docs/sot/INDEX.md`, `docs/sot/verification-commands.md`: 새 SOT 참조.
- `~/.codex/skills/strict/SKILL.md`, `~/.claude/skills/strict/SKILL.md`: 동일 사본으로 동기화하고 SOT 우선 계약을 삽입.

## Acceptance / Counter-AC

- AC: 두 전역 `SKILL.md`가 byte-identical이다. Counter: 한쪽만 수정하면 `cmp`가 FAIL이어야 한다.
- AC: DB/API 계약과 Type이 WU·RED보다 선행한다. Counter: Type-only 또는 mock-only 검증은 PASS가 아니다.
- AC: 첫 GREEN과 로컬 게이트 전에는 push/PR을 만들지 않는다. Counter: RED PR·`--no-verify`를 완료 증거로 인정하지 않는다.
- AC: P11 수치를 재복제하지 않고 원 정본에서 읽는다. Counter: 초과 파일/함수/PR을 숨기거나 분할 없이 통과시키지 않는다.
- AC: LLMOps 미구현은 `NOT_IMPLEMENTED`/`NOT_RUN`이다. Counter: 일반 CI를 LLMOps 증거로 부르지 않는다.

## 검증 장부

- `cmp`로 Codex/Claude 전역 스킬 동일성 확인.
- `skill-creator` `quick_validate.py`로 양쪽 스킬 구조 검사.
- `git diff --check` 및 `bash scripts/acceptance-principles-check.sh` 실행.

## 잔여 위험

전역 스킬은 저장소 외부 파일이므로 Git PR만으로 배포되지 않는다. 새 머신이나 다른 계정에서는 이 SOT를 읽고 두 스킬을 다시 동기화해야 하며, 동기화 전에는 패리티를 주장하지 않는다.
