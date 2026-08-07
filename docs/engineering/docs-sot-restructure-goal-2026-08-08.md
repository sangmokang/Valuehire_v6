# goal — `docs/` 를 SOT(영구)와 engineering(일시적 세션기록)으로 분리

**작성일**: 2026-08-08
**위험 등급**: **L3** (SOT 신설·수정 + 변경 파일 8개 이상 + 로컬 강제 장치 5개의 계약 참조 경로 변경)
**베이스 커밋**: `e7b6f3a` (main, 미추적 0건 확인)

## ① 현재 상태 (실측, 2026-08-08)

- `docs/engineering/`에 성격이 다른 문서 11개(당시 기준)가 평평하게 섞여 있고, `docs/sot/`는 존재하지 않았다(`find docs -type d` 확인).
- `hooks/pre-commit`(4행), `hooks/pre-push`(4행), `scripts/install-hooks.sh`(4행), `scripts/session-status.sh`(7행), `scripts/acceptance-0-7.sh`(9행) **5개 실행 파일 전부**가 `# 계약: docs/engineering/hook-enforcement-goal-2026-08-07.md ⑩`을 계약으로 참조하고 있었다 — 날짜 박힌 goal 문서(536줄, 36KB)의 10번째 섹션이 실제 강제 장치의 계약 정본 역할을 겸하는 구조.
- `current-coding-principles-briefing-2026-08-07.html`은 본문에서 스스로를 "정본(canonical)"이라 칭하면서도 파일명에 날짜가 박혀 있어, 매 "정본화" 커밋마다 새 파일이 생긴다(git log: `39ceb03 코딩 원칙 브리핑 HTML 정본화`). `v6-coding-principles-goal-2026-08-06.md` §0-E가 이미 이 패턴("정본 문서 자체가 오늘 중복 생성됨")을 자체 진단했다.
- `v6-coding-principles-goal-2026-08-06.md`(595줄/61,550바이트) 중 실제 "확정 규칙"은 §1+§1-B+검증체제(150~201행, 약 52줄)뿐이고 나머지는 유도과정·판정표·적대검증 로그다.
- 이 저장소는 `Makefile`도 `package.json`도 없다. `make -n red-ledger`는 실행 시 `No rule to make target 'red-ledger'`로 실패한다(2026-08-08 실행 확인) — harness 스킬이 기본 전제하는 `make task/verify/ship`이 이 저장소엔 없다.
- (작업 중 발견) 같은 세션 구간에 별도 작업(`e7b6f3a`, `/strict` 정본화)이 병행되어 `docs/engineering/strict-unification-goal-2026-08-08.md`가 새로 추가됐다. 파일 범위가 겹치지 않아(글로벌 `~/.claude`·`~/.codex` 파일 대상) 이 작업과 충돌 없음을 확인.

## ② 근본 원인

`docs/`에 "다음 세션도 참조해야 할 답"과 "이번 세션에 무슨 일이 있었는지의 기록"을 담을 자리가 분리돼 있지 않았다. 그 결과 실제로 반복 참조되는 계약(hook 5종)이 날짜 박힌 세션 스냅샷(goal 문서) 안에 얹히는 사고가 이미 벌어졌다 — 다음 "오래된 문서 정리"에서 이 goal 문서를 아카이브/삭제 대상으로 취급하면 강제 장치의 계약이 조용히 증발할 수 있는 구조였다.

## ③ 인수 기준(AC)

**AC-1**: When `docs/sot/` 재구성이 완료되면, then `docs/sot/{INDEX,coding-principles,hook-contracts,git-workflow,verification-commands}.md` 5개 파일이 모두 존재하고 각각 20,000바이트를 넘지 않으며, `hooks/pre-commit`·`hooks/pre-push`·`scripts/install-hooks.sh`·`scripts/session-status.sh`·`scripts/acceptance-0-7.sh` 5개 파일 전부가 옛 goal 문서 경로가 아니라 `docs/sot/hook-contracts.md`를 계약으로 참조해야 한다.

- **검증 명령**: `bash scripts/check-docs-sot.sh`
- **counter-AC(가짜 완료 시나리오)**: ① `docs/sot/` 파일만 새로 만들고 5개 스크립트의 주석은 그대로 옛 경로를 가리키는 경우(계약 참조가 갈라진 채 방치) ② SOT 파일에 판정 로그·세션 서사를 그대로 옮겨 담아 300줄대 문서가 재발하는 경우(바이트 상한으로 검사) ③ 원본 goal 문서를 삭제해 근거 링크가 끊기는 경우(이번 작업은 삭제하지 않고 이관 각주만 추가 — 별도 검사는 없으나 diff로 확인 가능)

## ④ Harness 게이트 진행 계획

게이트 0(세션 상태 확인) → 1(본 문서, AC 1개) → 2(워크트리 `worktrees/docs-sot-restructure`, RED 커밋 `c078210`) → 3(구현) → 4(`check-docs-sot.sh` + `verify.sh`) → 5(push→PR) → 6(merge 후 /clear).

## ⑤ codex 적대검증 정조준 항목

1. `docs/sot/coding-principles.md`가 원본 §1(150~201행)과 문구가 정말 동일한지, 판정·수치가 누락·변형되지 않았는지.
2. 5개 스크립트의 계약 주석 변경이 **로직에는 손대지 않았는지**(주석 한 줄 외 diff가 없는지) — 훅의 실제 차단 동작이 이번 변경으로 흔들리지 않아야 한다.
3. `docs/sot/*.md`가 실제로 20,000바이트 이하인지, 그리고 그 상한 자체가 "적당히 큰 파일도 통과시키는 느슨한 게이트"로 무력화되지 않았는지(예: 상한을 임의로 크게 잡아 사실상 검사가 없는 것과 같은 효과인지).
4. 원본 goal 문서 2개에 추가한 "이관" 각주가 실제로 두 파일 모두에 정확히 걸려 있는지(빠뜨린 섹션 없는지).

## ⑥ SOT 체크리스트

이 작업 자체가 `docs/sot/`를 새로 만드는 것이므로 기존 SOT는 없었다(회수 확인: `find docs -type d` 2026-08-08 결과 `docs/sot` 부재). 관련 원본: `docs/engineering/v6-coding-principles-goal-2026-08-06.md`, `docs/engineering/hook-enforcement-goal-2026-08-07.md`.

## ⑦ 비범위

- `docs/engineering/`을 월별 하위 폴더로 쪼개는 것 — 지금 파일 수(13개)로는 불필요, 40~50개 넘을 때 재검토.
- `current-coding-principles-briefing-2026-08-07.html`을 옮기거나 지우는 것 — 유효한 날짜 박힌 스냅샷으로 그대로 둔다. 앞으로 새 브리핑이 필요하면 이 markdown SOT를 소스로 Artifact를 즉석 생성하는 쪽을 권장(비범위이므로 이번 PR에서 구현하지 않음).
- `docs/sot/*.md`를 CI(`verify.yml`)에 상시 게이트로 연결하는 것 — 문서 재구성이지 신규 상시 게이트 신설이 아니다. `scripts/check-docs-sot.sh`는 지금은 수동 실행 스크립트로만 존재한다.
- `main` 브랜치 GitHub 보호 규칙의 실제 활성화 여부 확인 — `docs/sot/git-workflow.md`·`verification-commands.md`에 한계로 명시, 별도 확인 필요.

## ⑧ 롤백 절차

`git revert <이 PR의 squash 커밋 SHA>` 한 번. `docs/sot/`가 통째로 사라지고 5개 스크립트 주석이 옛 경로로 되돌아간다 — 로직 변경이 없으므로 revert에 부작용 없음.

## ⑨ 영향 반경

이 변경이 깨지면(예: 계약 주석 경로가 스크립트마다 다르게 남으면) 다음 세션이 "훅의 계약이 어디 있는지" 헷갈릴 수 있다. 단 **훅의 실행 로직 자체는 이번 diff에서 주석 줄 외에 변경되지 않았으므로**, P4·P13·P14·P22를 강제하는 실제 차단 동작에는 영향이 없다(⑤-2에서 codex가 재확인).

## ⑩ 계약 스펙 — `scripts/check-docs-sot.sh`

```
입력  : 없음(저장소 루트에서 실행)
출력  : exit 0 (AC 전부 충족) | exit 1 (하나라도 위반)
        각 검사 항목마다 "PASS: ..." 또는 "FAIL: ..." 한 줄씩 stdout/stderr에 출력
불변식: 조용한 통과 금지 — 무엇을 검사했는지 전부 나열한다
```

---

## 실행 결과 (2026-08-08)

### RED 확인
```
$ bash scripts/check-docs-sot.sh
FAIL: 필수 SOT 파일 없음: docs/sot/INDEX.md  (외 9건, 파일 부재 5 + 옛 경로 잔존 5×2)
NOT_RUN이 아니라 FAIL — 위 FAIL 라인을 고친다
EXIT CODE: 1
```

### 구현 중 자체 발견 — 검사 지표 결함(V2 자체발견)
최초 AC-1은 `wc -l <= 300`(줄 수)로 구현했다. `coding-principles.md`를 실제로 만들어보니 원본 표의 각 행이 개행 없이 한 줄에 긴 문장을 담고 있어 **70줄인데 15,424바이트**였다 — 줄 수 기준으로는 통과하지만 실제로는 큰 파일을 놓치는 지표였다. `wc -c`(바이트 수, 상한 20,000)로 즉시 교정하고 재실행해 확인했다.

### GREEN 확인
```
$ bash scripts/check-docs-sot.sh
PASS: docs/sot/INDEX.md 존재, 1050바이트 (<=20000)
PASS: docs/sot/coding-principles.md 존재, 15424바이트 (<=20000)
PASS: docs/sot/hook-contracts.md 존재, 3137바이트 (<=20000)
PASS: docs/sot/git-workflow.md 존재, 2248바이트 (<=20000)
PASS: docs/sot/verification-commands.md 존재, 2505바이트 (<=20000)
PASS: hooks/pre-commit 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: hooks/pre-push 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/install-hooks.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/session-status.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/acceptance-0-7.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
OK: docs/sot 재구성 AC 전부 충족
EXIT CODE: 0
```

## 적대 검증 로그

### V1 — Codex (격리)
(진행 예정 — 이 절은 `/codex:rescue` 실행 후 판정 본문 그대로 append)

### V2 — Claude 재현
(V1 이후 진행)
