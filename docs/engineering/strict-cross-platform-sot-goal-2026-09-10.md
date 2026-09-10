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

## RED — 실패하는 검사 고정 (2026-09-10 21:57 KST, 가지 착수 시점)

이 작업은 문서(SOT 문구) 전용이라 별도 시험 파일을 만들지 않는다. 사유: 검사 대상이 코드 동작이 아니라 정본 문장이며, 아래 grep 한 줄이 그대로 기계 검사(AC-3)다. 시험 파일을 만들면 문장을 복제한 텍스트 단언(P16 금지 패턴)이 된다.

### 착수 시점 두 SHA (0-1)

```text
$ git rev-parse --short main ; git rev-parse --short origin/main
f12ea33
fc6beed
```

→ 로컬 main이 origin/main보다 1커밋(f12ea33) 앞서 있고, 그 커밋은 워크트리 없이 main에 직접 올라간 미전송 커밋이다. 이 상태가 모든 새 워크트리의 `acceptance-0-5`를 FAIL로 만든다.

### AC-3 검사의 착수 시점 출력 (무한정 매치 3건 — 착수 프롬프트의 "2건"은 실측으로 정정)

```text
$ grep -n 'work-unit-policy.yaml' docs/sot/strict-workflow.md docs/sot/verification-commands.md
docs/sot/strict-workflow.md:5:이 문서는 `$strict`가 Codex와 Claude에서 동일한 판정·순서·승인 경계를 사용하도록 고정하는 운영 정본입니다. 원칙의 수치와 Work Unit의 필드는 각각 `coding-principles.md`, `principles.yaml`, `work-unit-policy.yaml`이 소유합니다. 이 문서는 그 값을 복제하지 않고 실행 순서와 플랫폼 공통 의미만 소유합니다.
docs/sot/strict-workflow.md:60:Strict 실행 시작 시 `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/work-unit-policy.yaml`, 이 문서를 직접 읽고 관련 acceptance/hook/CI 배선을 실행합니다. Codex와 Claude의 전역 `SKILL.md`는 이 공통 계약을 읽는 동일한 사본이어야 하며, 동기화 후 `cmp`와 `skill-creator`의 `quick_validate.py`로 각각 검증합니다.
docs/sot/verification-commands.md:3:`$strict`의 Codex·Claude 공통 순서와 패리티 계약은 [strict-workflow.md](strict-workflow.md)를 정본으로 읽는다. 원칙 수치는 `coding-principles.md`, Work Unit 값은 `work-unit-policy.yaml`이 소유하며 이 문서에 복제하지 않는다.
```

→ 세 줄 모두 `work-unit-policy.yaml`을 아무 한정 없이 정본으로 지목한다. 그 파일은 origin/main과 f12ea33 어느 쪽 `docs/sot/`에도 없다(`git ls-tree origin/main docs/sot/ | grep -c work-unit` → 0). 미병합 가지 `task/wu-tdd-context-contract-20260910`에만 있다. 이것이 고쳐야 할 RED다. 합격 조건: 각 매치 줄에 "INDEX에 등재된 경우" 또는 "병합 전까지는 git-workflow.md" 한정 문구가 있고, 무한정 매치가 0건.

## 검증 장부

- `cmp`로 Codex/Claude 전역 스킬 동일성 확인.
- `skill-creator` `quick_validate.py`로 양쪽 스킬 구조 검사.
- `git diff --check` 및 `bash scripts/acceptance-principles-check.sh` 실행.

## 잔여 위험

전역 스킬은 저장소 외부 파일이므로 Git PR만으로 배포되지 않는다. 새 머신이나 다른 계정에서는 이 SOT를 읽고 두 스킬을 다시 동기화해야 하며, 동기화 전에는 패리티를 주장하지 않는다.
