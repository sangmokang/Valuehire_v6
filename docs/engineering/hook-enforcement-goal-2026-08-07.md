# goal — 로컬 강제 장치(Hook) 도입 + 문서 정본화 + 시연

**작성일**: 2026-08-07 20:32 KST
**위험 등급**: **L3** (라이브 동작 변경 · 정본 문서(SOT) 수정 · 변경 파일 3개 이상)
**베이스 커밋**: `7e20bd4` (origin/main 과 동일, 미푸시 0)
**정본 원칙**: `docs/engineering/v6-coding-principles-goal-2026-08-06.md` (P1~P22)

---

## ① 현재 상태 (실측, 2026-08-07 20:32)

| 항목 | 관측 | 확인 명령 |
|---|---|---|
| HEAD / origin | `7e20bd4` 동일, 미푸시 0 | `git rev-parse --short HEAD origin/main` |
| 기존 검사 | `verify.sh` exit 0, `acceptance-0-2/0-5/0-6.sh` 전부 exit 0 | 각각 실행 |
| **`core.hooksPath`** | **미설정** | `git config --get core.hooksPath` → 빈 값 |
| **`.git/hooks/`** | **설치된 훅 0개** (sample 제외) | `ls .git/hooks/ \| grep -v '\.sample$'` → 빈 출력 |
| **`.claude/settings.json`** | **파일 없음** | `ls .claude/` → `private-reviews`, `skills` 뿐 |
| 미추적 산출물 | **11건** (`docs/engineering/` 전량 + 정본 원칙 문서 포함) | `git status --porcelain \| grep -c '^??'` |
| CI | `.github/workflows/verify.yml` — 5스텝. **push 이후에만 실행** | `grep -E '^\s*- name:' .github/workflows/verify.yml` |

**커밋 `9eb9fef` "V2 pre-push 지적 3건 반영"은 pre-push 훅을 만든 것이 아니다.**
변경 파일 4개는 `verify.yml` · `.gitignore` · `acceptance-0-5.sh` · 판정 문서이며, 훅은 포함되지 않았다.
"V2 검증자가 pre-push 시점에 지적한 내용을 반영했다"는 뜻이었다.

## ② 근본 원인

**강제 지점이 원격에만 있다.**

```
편집 → 커밋(무검사) → push(무검사) → GitHub Actions  ← 여기서 처음 검사
```

이 구조의 결함은 세 가지다.

1. **위반이 이미 원격에 올라간 뒤에 걸린다.** 비밀이 섞이면 push 시점에 이미 유출이다.
2. **P15("검증을 우회할 수 없다")가 로컬에서 전혀 강제되지 않는다.** 미추적 파일을 둔 채 push가 된다.
3. **정본 원칙 문서 자신이 미추적이다.** 문서가 "미추적이면 ship 거부"라고 규정하면서 스스로 그 상태다 —
   §0-E가 기록한 "경고하는 문서를 쓰는 도중에 재발" 유형의 세 번째 사례.

## ③ 인수 기준 (AC) — 실행 가능한 명령이 본체다

> **형식**: 검증 명령이 AC 그 자체이며, 산문은 그 명령이 무엇을 보장하는지에 대한 설명이다.
> counter-AC 는 알려진 가짜 완료 경로의 최소 목록이며, 검증자는 여기에 국한하지 않는다.

### AC-1 — 미추적 산출물 0건

- **검증**: `git status --porcelain | grep -c '^??'` → **`0`**
- **EARS**: When 작업 산출물이 생성되면, 시스템은 그것을 추적 상태로 커밋해야 한다.
- **counter-AC**: `.gitignore` 에 추가해서 `??` 를 0으로 만드는 것은 **가짜**. 실제 커밋 여부를
  `git ls-files docs/engineering/ | wc -l` 로 교차 확인한다(≥ 11).
- **counter-VERIFIER**: 이 명령은 `.gitignore` 우회를 구분하지 못하므로 위 교차 확인이 반드시 함께 간다.

### AC-2 — 정본 P12에 세션 중 HEAD 재확인 조항

- **검증**: `grep -c 'HEAD 재확인' docs/engineering/v6-coding-principles-goal-2026-08-06.md` → **≥ 1**
- **EARS**: While 긴 세션이 진행 중이면, 시스템은 보고 직전 HEAD 를 재확인해야 한다.
- **counter-AC**: 문서에만 적고 기계 장치가 없으면 **P1 위반**(기계 장치 없는 원칙은 삭제).
  → AC-5(SessionStart hook)가 이 조항의 기계 장치이며, 둘은 함께 통과해야 한다.

### AC-3 — pre-commit 훅이 위반 커밋을 실제로 거부

- **검증**: `bash scripts/acceptance-0-7.sh` 내 pre-commit 절 — 임시 clone 에서 비밀 패턴을 담은 파일을
  커밋 시도 → **exit ≠ 0** 이고 stderr 에 차단 사유가 출력됨
- **EARS**: If 커밋에 비밀 패턴이 포함되면, then 시스템은 커밋을 거부해야 한다.
- **counter-AC**: ① 훅 파일은 있으나 **실행 권한 없음** → 조용히 통과 ② `core.hooksPath` 가 다른 곳을 가리킴
  ③ 훅 내부 셸 문법 오류로 조용히 통과 ④ 훅이 **자기 자신·패턴 파일을 검사 대상에서 제외**
- **counter-VERIFIER**: "훅 파일이 존재한다"를 검사하는 것으로는 부족하다. **실제로 커밋을 시도해 거부되는지**를 본다.

### AC-4 — pre-push 훅이 전체 검사를 재실행하고 실패 시 거부

- **검증**: `bash scripts/acceptance-0-7.sh` 내 pre-push 절 — 임시 clone 에서 acceptance 하나를 의도적으로
  실패시킨 뒤 push 시도 → **exit ≠ 0**
- **EARS**: If 로컬 검사 중 하나라도 실패하면, then 시스템은 push 를 거부해야 한다.
- **counter-AC**: ① `|| true` · `2>/dev/null` 로 실패가 삼켜짐 ② `set -euo pipefail` 부재
  ③ 검사 스크립트가 없을 때(`command not found`) **통과로 흘러감**(fail-open) ④ `--no-verify` 우회
- **fail-closed 원칙**: 검사를 **실행하지 못한 경우도 실패로 판정**한다. 이는 `7e20bd4` 가 CI에서 이미 적용한 규칙이며,
  로컬 훅에도 동일하게 적용한다.
- **`--no-verify` 처리**: 로컬 훅으로는 막을 수 없다. **CI가 사후 탐지하는 것이 최종 방어선**이며,
  이 한계를 문서에 명시한다(숨기지 않는다).

### AC-5 — SessionStart hook 이 상태를 자동 보고

- **검증**: `bash scripts/acceptance-0-7.sh` 내 settings 절 — `.claude/settings.json` 이 존재하고
  `jq -e '.hooks.SessionStart'` 가 성공하며, 지정된 스크립트가 **실행 가능하고 exit 0** 이며
  출력에 `HEAD` · `origin` · `RED` 세 항목이 포함됨
- **EARS**: When 새 세션이 시작되면, 시스템은 현재 HEAD · origin 동기 상태 · 미해결 RED 를 자동 출력해야 한다.
- **counter-AC**: ① hook 이 등록만 되고 스크립트가 없음 ② 스크립트가 실패해도 조용히 넘어감
  ③ 출력이 하드코딩된 문자열(실제 git 조회를 하지 않음)

### AC-6 — 위반 6종 시연이 전부 거부됨

- **검증**: `bash scripts/acceptance-0-7.sh` → **exit 0** 이고, 6종 각각에 대해 `BLOCKED` 를 출력.
  하나라도 통과(=거부되지 않음)하면 스크립트 전체가 exit ≠ 0.

| # | 일부러 저지르는 위반 | 재현하는 과거 사고 | 막는 원칙 |
|---|---|---|---|
| 1 | 검사기가 자기 자신을 검사 대상에서 제외 | `verify.sh` 자기 면제 (§0 E1) | P13 |
| 2 | 검사를 `skip` / `if exists` 로 완화 | `48143a7` · `129f61d` | P13 |
| 3 | 만료일 없는 억제를 `suppressions.yaml` 에 추가 | `98d923f` (35일 방치) | P13 |
| 4 | LLM 출력의 숫자를 판정 필드에 기록 | v4 QA-094 | P14 |
| 5 | 커밋 안 된 변경을 둔 채 push | `78f3631` ② | P15 |
| 6 | 외부 효과 코드가 네트워크 차단 상태에서 통과 | `gptreview.js` (§0 E5) | P4 |

- **counter-AC**: 시연 스크립트가 **기대 출력을 하드코딩**하고 실제로는 거부를 유발하지 않는 것.
  → 각 시연은 반드시 **실제 명령의 종료 코드**로 판정하며, 문자열 비교만으로 판정하지 않는다.
- **counter-VERIFIER**: 시연이 원본 저장소를 오염시키면 안 된다. **임시 clone 에서만** 수행하고,
  종료 시 원본의 `git status` 가 시연 전과 동일함을 확인한다.

## ④ Harness 게이트 진행 계획

| 게이트 | 계획 |
|---|---|
| 0 | ✅ 완료 — 미해결 RED 0, 워크트리 0, 옆 쉘 활동 0 (2026-08-07 20:32) |
| 1 | 이 문서 (AC 6개 + 계약 스펙 ⑩) |
| 2 | 워크트리 `worktrees/hook-enforcement` · 브랜치 `task/hook-enforcement`. `scripts/acceptance-0-7.sh` 를 **RED 로 먼저 커밋** (훅이 없으므로 실패해야 정상) |
| 3 | `hooks/pre-commit` · `hooks/pre-push` · `scripts/session-status.sh` · `.claude/settings.json` · `scripts/install-hooks.sh` 구현 |
| 3.5 | 배선 증명 — `core.hooksPath` 가 `hooks/` 를 가리키고, 실제 커밋·push 시도가 훅을 통과함을 **실행 로그**로 |
| 4 | `acceptance-0-7.sh` exit 0 + 기존 검사 4종 전부 exit 0 (출력 그대로 첨부) |
| 5 | PR → CI 초록 → merge |
| 6 | merge 후 /clear |

## ⑤ codex 적대검증 정조준 항목 (V1 감시자에게 전달 완료)

1. 훅이 **실제로 실행되는가** — 실행 권한 · `core.hooksPath` · 셸 문법 오류로 인한 조용한 통과
2. 새 훅·스크립트의 **자기 면제** 여부
3. **fail-open 경로** — `|| true`, `2>/dev/null`, `set -e` 부재, 명령 부재 시 통과
4. AC-6 시연의 진정성 — 기대 출력 하드코딩 여부
5. AC-1 의 `.gitignore` 우회
6. P15 자기모순(정본 문서가 미추적)의 해소 여부

## ⑥ SOT 체크리스트

- 이 저장소에 `docs/sot/` 은 아직 없다. 현 SOT는 `docs/engineering/v6-coding-principles-goal-2026-08-06.md`(P1~P22).
- **이 변경은 SOT를 수정한다** — P12에 조항 추가(AC-2). 따라서 같은 PR에 문서 diff를 동봉한다(드리프트 차단).
- 저장소에 `CLAUDE.md` 가 없다. 3계층 배치(§3)의 계층 1이 비어 있으나, **이번 범위 밖**으로 둔다(⑦ 참조).

## ⑦ 비범위 (이번에 하지 않을 것)

- `CLAUDE.md` 20줄 작성 및 계층 1 정비 → 별건
- `principles.yaml` + P16~P22 의 CI 게이트 전량 구현 → Phase 1 잔여 작업으로 분리
- `/strict` 3벌 통합(E6) → 저장소 밖(`~/.claude`, `~/.codex`) 작업이라 별건
- 비밀번호 회전 → **오너가 2026-08-04 거부. 재요구하지 않음**
- Desktop 사본 `valuehire-coding-principles-2026-08-06.md` 의 SUPERSEDED 표기 → 저장소 밖

## ⑧ 롤백 절차 (L3)

1. 훅 무력화(즉시): `git config --unset core.hooksPath` — 훅이 개발을 막는 사고 시 1초 복구
2. 커밋 되돌리기: `git revert <merge-sha>` — 훅 파일·설정·스크립트가 함께 제거됨
3. `.claude/settings.json` 은 `.gitignore` 되지 않으므로 revert 로 함께 복구됨
4. **원격 되돌리기 불필요** — 이 변경은 실행물 배포가 아니라 개발 도구 변경이다

## ⑨ 영향 반경 (L3)

| 깨지면 무엇이 멈추나 | 완화 |
|---|---|
| pre-commit 이 오탐하면 **모든 커밋이 막힌다** | 롤백 1번(1초). 패턴은 기존 `.secret-patterns.default` 재사용 — 새 패턴을 만들지 않는다 |
| pre-push 가 오탐하면 **모든 push 가 막힌다** | 동일. 그리고 pre-push 는 **기존 검사 4종을 그대로 재실행**할 뿐 새 판정을 만들지 않는다 |
| SessionStart hook 이 느리면 세션 시작이 지연 | 조회 3개(`rev-parse`·`status`·`acceptance` 개수)만. 네트워크 호출 없음 |

**데이터 안전 AC**: 이 변경은 PII·인증·과금 경로를 건드리지 않는다. 다만 훅이 **비밀을 화면에 출력하면 안 되므로**,
차단 사유 출력 시 **매칭된 값이 아니라 패턴 이름과 파일 경로만** 표시한다(AC-3 검증에 포함).

## ⑩ 계약 스펙 — 입출력

### `hooks/pre-commit`
```
입력  : stdin 없음. 스테이징된 파일 목록(git diff --cached --name-only)
출력  : exit 0 (통과) | exit 1 (차단)
        차단 시 stderr: "BLOCKED: <검사이름> — <파일경로> (패턴: <패턴이름>)"
        ※ 매칭된 실제 값은 절대 출력하지 않는다
불변식: set -euo pipefail. 검사를 실행하지 못하면 exit 1 (fail-closed)
제외  : 없음. 자기 자신(hooks/)도 검사 대상이다
```

### `hooks/pre-push`
```
입력  : stdin 으로 <local ref> <local sha> <remote ref> <remote sha> (git 표준)
출력  : exit 0 | exit 1
        실행: verify.sh, scripts/acceptance-*.sh 전량 (glob — 새 스크립트 추가 시 자동 포함)
        차단 시 stderr: "BLOCKED: <스크립트경로> exit=<code>"
불변식: 스크립트가 0개 발견되면 exit 1 (fail-closed — "검사할 게 없어서 통과"를 금지)
        미추적 파일(??) 존재 시 exit 1 (P15)
한계  : git push --no-verify 로 우회 가능. CI 가 최종 방어선 (문서에 명시)
```

### `scripts/session-status.sh`
```
입력  : 없음
출력  : stdout 3줄 + exit 0
        HEAD: <sha> (<origin 대비: synced|ahead N|behind N>)
        ORIGIN: <sha>
        RED: <실패한 acceptance 스크립트 수>/<전체 수>
불변식: git 조회 실패 시 해당 줄에 "UNKNOWN" 을 출력하고 exit 1 (조용한 성공 금지)
```

### `scripts/acceptance-0-7.sh`
```
입력  : 없음
출력  : exit 0 (6종 전부 BLOCKED) | exit 1 (하나라도 통과)
        각 시연: "[N/6] <위반이름> → BLOCKED (exit=<code>)" 또는 "→ PASSED ← 결함"
불변식: 모든 시연은 mktemp -d 안의 clone 에서 수행.
        종료 시 원본 저장소의 git status 가 시연 전과 동일함을 확인하고, 다르면 exit 1
        판정은 종료 코드로만 한다. 문자열 비교 단독 판정 금지
```

### `scripts/install-hooks.sh`
```
입력  : 없음
동작  : git config core.hooksPath hooks && chmod +x hooks/*
출력  : exit 0 + 설치된 훅 목록
불변식: 실행 후 core.hooksPath 를 재조회해 실제로 설정됐는지 확인(readback). 불일치 시 exit 1
```

---

## 적대 검증 로그

*(V1 Codex 감시자 판정 · V2 Claude 재현 결과를 아래에 본문 그대로 append)*
