# Goal — Codex·Claude Strict 패리티와 SOT 고정 (2026-09-10)

## 결론

Codex와 Claude 두 도구가 엄격 작업을 할 때 같은 순서와 같은 판정 기준을 쓰도록, 그 순서를 저장소 안 정본 문서 한 곳에 고정한다. 2026-09-10 저녁 정정: 이 정본 문서가 아직 저장소에 없는 파일을 무조건 기준으로 지목하고 있어서, 그 파일이 정식 목록에 오른 뒤에만 기준으로 삼도록 문장을 고쳤다. 이 변경은 처음에 작업 가지 없이 본줄기에 직접 올라갔던 것을 가지로 옮긴 것이며, 본줄기 되돌리기와 원격 반영은 사람 승인 사안이다.

## 판단 근거

- 없는 파일을 정본으로 지목한 문장을 지우지 않고 한정했다. 지우면 나중에 그 파일이 병합됐을 때 다시 넣어야 하고, 두면 지금 읽는 사람이 없는 파일을 찾아 헤맨다. 한정 문구는 두 경우를 모두 다룬다.
- 틀리면 깨지는 것: 한정 문구의 기준을 "INDEX 등재"로 둔 것이 틀리면(예: 파일은 있는데 INDEX에 안 올리는 관행이 생기면) 정본이 있어도 무시된다. INDEX.md 첫머리가 "새 SOT 파일 추가의 유일한 트리거"를 INDEX 등재로 정의하므로 이 기준을 택했다.

> **무엇을** — 없는 파일 참조 3곳에 "INDEX에 등재된 경우에만 정본, 병합 전까지는 git-workflow.md" 한정 문구를 넣었다.
> **왜** — 정본 문서가 존재하지 않는 파일을 기준으로 지목하면 읽는 사람과 자동 검사 모두 헛돈다.
> **버린 길** — ① 참조 삭제(병합 시 재작업, 의도 소실) ② work-unit-policy.yaml을 이 가지에 같이 가져오기(PR #37의 3,139줄 문제를 이 가지가 떠안음) ③ 그대로 두기(없는 파일을 정본이라 부르는 상태 지속).
> **대가** — 문장이 길어졌고, 병합 뒤 한정 문구를 걷어내는 후속 수정이 필요하다.
> **되돌리기** — 커밋 0761f14 하나를 revert하면 원문으로 돌아간다.

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

f12ea33 시점의 장부는 "cmp·quick_validate·git diff --check·principles-check 실행"을 문장으로만 주장하고 출력이 없었다. 아래는 가지 `task/strict-workflow-sot-20260910`(HEAD 0761f14, SOT 문구 수정 직후)에서 실제로 실행한 명령과 전체 출력이다. 실행 주체: Claude 세션 `session_01CjNP65FKtFC1UXF42CcM8a`.

```text
## 검증 장부 실행 2026-09-10 22:00 KST HEAD=0761f14
$ cmp ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md; echo rc=$?
rc=0
$ shasum -a 256 ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md
a277178adaeb51e008bd1637a7be2d1d33649d113ddb2c750acf54f85856270a  /Users/kangsangmo/.codex/skills/strict/SKILL.md
a277178adaeb51e008bd1637a7be2d1d33649d113ddb2c750acf54f85856270a  /Users/kangsangmo/.claude/skills/strict/SKILL.md
$ uv run --with pyyaml ~/.claude/skills/skill-creator/scripts/quick_validate.py ~/.codex/skills/strict
Skill is valid!
rc=0
$ uv run --with pyyaml ~/.claude/skills/skill-creator/scripts/quick_validate.py ~/.claude/skills/strict
Skill is valid!
rc=0
$ git diff --check f12ea33 HEAD; echo rc=$?
rc=0
$ bash scripts/acceptance-principles-check.sh; echo rc=$?
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
rc=0
$ bash scripts/verify/check-strict-principles-skills.sh ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md; echo rc=$?
VERDICT: FAIL
CODEX_ENGINE_ORDER_INVALID
CLAUDE_ENGINE_ORDER_INVALID
CHECKED: 2
FAILURES: 2
rc=1
$ bash scripts/check-docs-sot.sh; echo rc=$?
PASS: docs/sot/INDEX.md 존재, 1800바이트 (<=20000)
FAIL: docs/sot/coding-principles.md 가 20000바이트 초과 (20476바이트) — 계약과 서술이 다시 섞였을 가능성
PASS: docs/sot/hook-contracts.md 존재, 4911바이트 (<=20000)
PASS: docs/sot/git-workflow.md 존재, 2225바이트 (<=20000)
PASS: docs/sot/verification-commands.md 존재, 9202바이트 (<=20000)
PASS: hooks/pre-commit 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: hooks/pre-push 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/install-hooks.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/session-status.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/acceptance-0-7.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
NOT_RUN이 아니라 FAIL — 위 FAIL 라인을 고친다
rc=1
```

→ 처음 여섯 항목(cmp·해시·quick_validate 양쪽·diff --check·principles-check)은 모두 종료값 0으로 합격이다. 마지막 두 항목은 불합격이며 아래에 따로 적는다.

### 이번 작업이 새로 찾은 불합격 2건 (둘 다 이 가지의 수정 범위 밖)

| 검사 | 결과 | 원인 | 처리 |
|---|---|---|---|
| `scripts/verify/check-strict-principles-skills.sh` 를 실제 전역 두 파일에 적용 | FAIL `CODEX_ENGINE_ORDER_INVALID` / `CLAUDE_ENGINE_ORDER_INVALID` | 저장소 검사기는 Codex판에 "Codex판은 `G=Codex → V1=Claude → V2=Codex`", Claude판에 "Claude판은 `G=Claude → V1=Codex → V2=Claude`" 문장을 요구한다(`scripts/verify/check-strict-principles-skills.sh:67-70`, 플랫폼별 엔진 순서 검사). f12ea33 세션이 두 전역 파일을 바이트 동일 사본으로 만들면서 플랫폼별 순서 문장이 양쪽 다 사라졌다. 이 검사기는 `acceptance-principles-mutations.sh`에서 임시 사본에만 쓰이고 실제 전역 파일에는 배선돼 있지 않아 CI가 잡지 못했다 | 전역 파일은 이 작업의 비범위(AC-5: 바이트 동일 유지)다. "패리티 완료" 주장은 이 검사기 기준으로는 **미달**이며, 후속 작업에서 두 파일에 플랫폼 순서 문장을 각각 넣고 같은 검사기로 재확인해야 한다 |
| `scripts/check-docs-sot.sh` | FAIL `coding-principles.md 20476바이트 > 20000` | origin/main(fc6beed)에서도 같은 20476바이트다. f12ea33도 이 가지도 그 파일을 건드리지 않았다. 이 검사기는 acceptance·pre-push·CI 어디에도 배선돼 있지 않다 | 기존 결함. 이 가지의 범위 밖이며 별도 처리 대상으로 기록만 한다 |

→ 두 검사기 모두 이 가지가 만든 파일을 보는 것이 아니라 기존 상태를 본다. 첫째는 f12ea33 세션의 "패리티 완료" 주장이 저장소 검사기 기준으로 미달임을 뜻하고(나쁜 소식, 후속 작업 필요), 둘째는 이 작업 전부터 있던 크기 초과다.

### R2 — 검사가 진짜 실패하는지 (뮤테이션)

`docs/sot/verification-commands.md:3`에서 한정 문구를 지운 고장 사본을 만들어 AC-3 검사를 돌렸다.

```text
mutant line3: ... Work Unit 값은 `work-unit-policy.yaml`이 소유한다. ...
무한정 매치 수(기대 1):        1
복원 후 무한정 매치 수(기대 0):        0
```

→ 한정 문구를 빼면 검사가 1건 실패로 바뀌고, 되돌리면 0건으로 돌아온다. AC-3 검사는 상시 통과가 아니다.

## 잔여 위험

- `work-unit-policy.yaml`은 아직 `docs/sot/`에 없다(미병합 가지 `task/wu-tdd-context-contract-20260910`에만 존재). 이 문서의 SOT 문구는 그 파일이 INDEX에 등재된 경우에만 정본으로 읽도록 한정했다. 병합되면 한정 문구를 걷어내는 후속 수정이 필요하다.
- 위 검증 장부의 불합격 2건(전역 스킬 플랫폼 순서 문장 누락, coding-principles.md 크기 초과)은 이 가지에서 고치지 않았다.
전역 스킬은 저장소 외부 파일이므로 Git PR만으로 배포되지 않는다. 새 머신이나 다른 계정에서는 이 SOT를 읽고 두 스킬을 다시 동기화해야 하며, 동기화 전에는 패리티를 주장하지 않는다.
