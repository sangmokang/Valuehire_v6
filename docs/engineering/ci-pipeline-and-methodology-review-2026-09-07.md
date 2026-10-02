# CI 파이프라인·개발 방법론 점검 — 2026-09-07

Claude(Sonnet 5)가 사장님 질의에 답하며 실행 확인한 내용을 기록한다. 산문 설명이 아니라
"무엇을 실제로 실행해서 무엇을 확인했는가"만 남긴다.

## 1. `.github/workflows/verify.yml`의 역할

로컬 검증(사람/AI의 자기 신고)과 GitHub Actions의 원격 재실행(제3자 판정)을 분리하는
장치. 워크플로 자체 주석: "로컬 검증은 실행자가 주장하는 것이고, 이 워크플로우는 GitHub이
판정하는 것이다." 2026-09-07 기준 origin/main(`01495b3`)의 워크플로는 32개 스텝이며,
전체 표는 `docs/sot/verification-commands.md`의 "CI가 실제로 돌리는 것" 절이 정본이다
(이 문서에 다시 베끼지 않는다 — 두 곳에 같은 표를 적으면 갈라진다는 게 그 문서 자체의
경고).

## 2. 전체 파이프라인 (실행 확인)

```
GitHub 이슈(인수 기준 1개)
  → goal 문서(docs/engineering/<주제>-goal-<날짜>.md)
  → git worktree add worktrees/<name> -b task/<name>  (이 저장소 실제 명령 — 3절 참고)
  → WU 반복: RED 테스트 커밋 → 최소 구현 → GREEN 커밋
  → 전체 WU 완료 후 1회: Full Strict(로컬) → Codeaudit(읽기전용) → 적대검증 V1→V2
  → git push + gh pr create
  → GitHub Actions verify.yml (원격 재실행 = 수문장)
  → local HEAD == PR HEAD == CI가 검사한 SHA 일치 확인
  → READY TO MERGE 보고, merge는 사용자만 실행
```

## 3. 명령어 3계 불일치 — 실행으로 확인한 사실

세 군데가 서로 다른 워크트리/명령 규약을 말한다.

| 출처 | 주장하는 명령 | 이 저장소에서 실행해본 결과 |
|---|---|---|
| 전역 `harness` 스킬(`~/.claude/skills/harness/SKILL.md`) | `make red-ledger` / `make task NAME=...` / `make ship` | `Makefile` 없음 → 전부 실행 불가 |
| 전역 `strict` 스킬(`~/.claude/skills/strict/SKILL.md` §2) | `npm run wt -- <issue>-<slug>` (규약 `../wt/…`, SOT-19 §4) | `package.json` 없음 → 실행 불가. `SOT-19`도 이 저장소 `docs/sot/INDEX.md`에 없음(2026-09-07 확인 — phantom) |
| 이 저장소의 실제 SOT(`docs/sot/git-workflow.md`, `docs/sot/verification-commands.md`) | `git worktree add worktrees/<name> -b task/<name>` | **이것만 실제로 동작함** — `worktrees/` 아래 60개 이상 디렉터리가 이 패턴으로 만들어져 있음(실행 확인) |

**쉬운 설명**: `harness`와 `strict`라는 두 "일반 매뉴얼"이 각자 "이 명령을 써라"라고
말하는데, 둘 다 이 저장소엔 없는 도구(make, npm 스크립트)를 전제로 쓰여 있다. 반면 이
저장소 자신의 매뉴얼(`docs/sot/`)은 "우리는 그 두 개 다 아니고, 그냥 `git worktree add`를
직접 쓴다"라고 이미 8월 초부터 적어 놨다. 즉 문제는 "두 매뉴얼이 다르다"가 아니라
"**두 매뉴얼 다 이 저장소 현실과 안 맞는다**"였다. 해결은 두 매뉴얼을 통일하는 게 아니라,
전역 매뉴얼이 레포별 실제 규약(`docs/sot/`)을 인용하도록 고치는 것 — 자세한 조치는
`docs/engineering/strict-sot-phantom-reference-fix-goal-2026-09-07.md` 참고.

## 4. SOT-30/31/19 phantom 참조 — 실행으로 확인한 사실

`~/.claude/skills/strict/SKILL.md`가 "이 저장소의 유일 정본"이라고 지목한 파일 3개 중
2개(`docs/sot/30-strict-mode-contract.md`, `docs/sot/31-strict-recurrence-ledger.md`)와
도구 1개(`tools/install-strict-skill.sh`)가 이 저장소에 존재한 적이 없었다(`git log --all`
0건, `find` 0건). 이 중 30번 phantom은 2026-08-27에 한 번 발견됐던 것과 **동일 사건의
재발**(메모리 `feedback-verify-skill-sot-reference-exists`). 조치는
`docs/engineering/strict-sot-phantom-reference-fix-goal-2026-09-07.md` + 신설
`docs/sot/31-strict-recurrence-ledger.md`에 기록.

**추가 기록(2026-09-07, `/codex:rescue` 1차 검토가 FAIL 판정)**: 최초 수정(3~4곳)은
불완전했다 — `SOT-30`이라는 라벨 자체가 프론트매터·본문 7곳에 근거 없이 남아 있었고,
Full Strict 절(§5)의 `npm run strict:gate`/`npm run check`가 여전히 무조건 명령이었으며,
재발 원장이 "2회 이상만 기록"이라 선언해놓고 스스로 1회짜리 행(L2/L3)을 올려 자기모순이었고,
"이 저장소엔 `package.json`이 없다"는 문구도 과거 이력(admin 워크스페이스용으로 한때 존재)을
빼먹어 부정확했다. 2차 수정에서 SOT-30 라벨 제거·조건부 문구 일괄 적용·원장 기록 기준 재정의·
`package.json` 문구 정밀화까지 마쳤다 — 근거는 같은 goal 문서의 적대 검증 로그.

## 5. 로컬 main 지연 — 실행으로 확인한 사실

이번 세션 시작 시점 로컬 `main`(`f4ea5f6`)이 `origin/main`(`01495b3`)보다 19커밋 뒤처져
있었다(인보이스 PR#59 병합분 포함). `git pull --ff-only origin main`으로 fast-forward
완료, 충돌 0건. 이 지연 동안 로컬에서 확인한 "파일 없음" 판정 중 최소 1건
(`scripts/acceptance-invoice.sh`)이 실제로는 원격엔 있었던 오탐이었다 — 이 사실 자체가
"작업 전 반드시 origin과 동기화 상태를 먼저 확인해야 한다"는 근거다.

## 6. Best practice 평가 요약

**강점**(실행 확인됨): 검사기 자기 무력화 저항(`acceptance-semantic-mutations.sh`),
초록불의 커밋 SHA 귀속 강제(`acceptance-verified-sha.sh`, P23), 억제 만료일 강제(CI가
`suppressions.yaml`을 매 push마다 훑음), 히스토리 전량 blob 스캔.

**약점**:
1. 병목이 제작이 아니라 병합 — 2026-09-07 기준 열린 PR 10건, 최근 병합 정체.
2. 전역 스킬(`harness`/`strict`)이 레포 고유 값을 하드코딩해 phantom 참조를 반복 생산 —
   이번 문서 3~4절이 그 사례.
3. 정책 실체가 레포 밖 개인 설정(`~/.claude/skills/`)에 있어 레포만 clone해서는 규칙
   전체를 볼 수 없음 — `docs/sot/`가 실제 동작 명령의 정본 역할을 대신 해주고 있으나,
   `strict`가 요구하는 R1~R9류 절차 규율은 레포에 없음.

## 비범위 / 확인하지 못한 것

- "핵심 지표 정의를 한 곳으로 통합"의 구체적 authority 파일 위치는 특정하지 못함.
- "Preview 대상 Playwright smoke 3개"라는 구체적 규칙은 저장소 어디에서도 확인 못 함 —
  원문 대화 출처를 알려주면 재대조 가능.
