# Valuehire v6 — strict 재발 원장 (SOT)

최종 갱신: 2026-10-13
등록: `docs/sot/INDEX.md` (글로벌 스킬의 참조 연결은 아직 없음)

## 이 문서의 역할

반복되는 `strict` 지적의 발생 이력과 후속 조치를 대조하는 파일이다. 현재 글로벌
`strict` 스킬의 R4는 제품 호출 경로 검증 규칙이며 이 원장을 읽으라는 지시는 없다.
따라서 스킬에서 이 파일을 참조하도록 연결하는 작업은 별도로 필요하다.

**기록 기준**: 앞으로 재발 여부를 판단하려면 **최초 1회부터 행을 만들어 둬야** 다음 세션이
"이거 전에 지적된 건가?"를 이 표 하나로 대조할 수 있다. 그래서 이 원장은 **1회차부터** 기록한다
(1회성으로 끝날지도 모르는 사소한 지적까지 전부 올리지는 않는다 — 대상은 "같은
스킬/장치가 반복해서 틀리는 지적"으로 한정하고, 그 밖의 1회성 사건은 해당
`docs/engineering/*.md` goal 문서에만 남긴다). **2회째부터**가 이 원장의 승격 의무 발동
시점이다 — 그 세션은 "승격 상태" 칸을 `승격 완료`로 바꾸거나, 왜 아직 못 바꿨는지(부채 이관
근거: 이슈 번호·기한)를 같은 행에 적어야 한다.

## 원장

| # | 지적 내용 | 발생 이력 | 승격 상태 |
|---|---|---|---|
| L1 | `strict`/`harness` 계열 스킬이 "이 저장소의 유일 정본"이라고 선언한 파일이 실제로는 저장소에 없다(phantom SOT 참조) | 2026-08-25(`docs/engineering/gate-integrity-codex-handoff-2026-08-25.md`:20-21), 2026-08-27(`docs/engineering/backlog-recovery-goal-2026-08-27.md`:5), 2026-09-05(`docs/engineering/main-green-suppression-floor12-goal-2026-09-05.md`:17), 2026-09-07(이번 수정의 goal 문서) | **승격 필요, 부채로 이관** — [이슈 #62](https://github.com/sangmokang/Valuehire_v6/issues/62)(자동 검사기: 스킬 파일이 인용하는 경로가 `git ls-files`에 없으면 FAIL, pre-push 편입). 이번 PR은 인용 텍스트 직접 수정까지만 하고, 자동 검사기는 별도 WU로 분리(스코프 과확장 방지, R9) |
| L2 | 글로벌 `strict` 스킬이 이 저장소에 없는 도구를 정본 명령처럼 서술한다 — `npm run wt`(당시 트리에 `package.json`이 없었음), `SOT-19 §4`(이 저장소의 해당 SOT 없음), `tools/install-strict-skill.sh`(당시 트리에 없음) | 2026-08-25(`docs/engineering/gate-integrity-codex-handoff-2026-08-25.md`:19), 2026-08-27(`docs/engineering/backlog-recovery-goal-2026-08-27.md`:5), 2026-09-07(이번 수정의 goal 문서) | **승격 필요** — 재발 방지 검사 및 이슈·기한 미정 |
| L3 | 글로벌 `strict` 스킬 §2 "Stop 게이트 마커" 문단 전체(`.claude/hooks/stop-evidence-gate.py`, `.claude/strict-active.json` 자동 생성/해제)가 이 저장소엔 배선돼 있지 않다 — L1/L2 수정을 codeaudit으로 자체 점검하던 중 추가 발견 | 1차 2026-09-07(이번 세션, `find . -iname stop-evidence-gate.py`·`find . -iname "strict-active.json*"` 둘 다 0건) | 1회 — 미도달. §2에 "레포에 hook 파일 없으면 이 문단 미적용" 캐비트만 추가하고, 실제 hook 신설은 이번 PR 범위 밖(부채로 남김) |

## 이 원장의 승격 규칙

같은 번호(#)의 지적이 **2번째로**(= 이 표에 이미 있는 행에 "발생 이력"이 하나 더 붙으면) 나오면, 그 시점 세션은 **보고만 하지 않고** 아래 중 하나를 그 PR에서 완료해야 승격 상태를 `승격 완료`로 바꿀 수 있다. L1과 L2는 이미 이 상태다(각각 2026-08-25, 2026-08-27에 기록됨).

- 산문 지적이 반복되면 자동 검사로 막을 수 있는지 판단한다.
- 검사가 있는데도 실행되지 않아 반복되면 훅이나 CI에 연결할 필요를 판단한다.

## 비범위

- 이 원장은 `docs/engineering/*.md`에 이미 날짜 기록된 개별 사건의 전문(全文)을 복제하지 않는다. 요약 + 근거 문서 링크만 남긴다.
- 이 원장 자체의 각 행 추가는 L2+ code-change가 아니므로 워크트리 요구는 있으나(문서도 소스), Full Strict/Codeaudit/Adversarial 풀 사이클을 매 행마다 요구하지는 않는다 — 다만 이 파일을 처음 만드는 이번 PR은 코드 리뷰 스킬(codeaudit/humanreview)로 검토받는다.
