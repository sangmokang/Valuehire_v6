# Valuehire v6 — strict 재발 원장 (SOT)

최종 갱신: 2026-09-07
근거: `~/.claude/skills/strict/SKILL.md` §3.5 R4("착수 시 이 문서를 읽고 관련 행을 goal에 인용")

## 이 문서의 역할

`strict` 모드(글로벌 스킬 `~/.claude/skills/strict/SKILL.md`) R4가 매 L2+ 작업 착수 시 읽으라고
요구하는 파일이다. 지금까지 이 파일 자체가 저장소에 없어 R4가 실행 불가능했다 — 이 파일의
생성이 그 갭을 메우는 첫 조치다.

**기록 기준**: 앞으로 재발 여부를 판단하려면 **최초 1회부터 행을 만들어 둬야** 다음 세션이
"이거 전에 지적된 건가?"를 이 표 하나로 대조할 수 있다. 그래서 이 원장은 **1회차부터** 기록한다
(1회성으로 끝날지도 모르는 사소한 지적까지 전부 올리지는 않는다 — 대상은 R4가 다루는 "같은
스킬/장치가 반복해서 틀리는 지적"으로 한정하고, 그 밖의 1회성 사건은 해당
`docs/engineering/*.md` goal 문서에만 남긴다). **2회째부터**가 R4의 "승격 의무" 발동
시점이다 — 그 세션은 "승격 상태" 칸을 `승격 완료`로 바꾸거나, 왜 아직 못 바꿨는지(부채 이관
근거: 이슈 번호·기한)를 같은 행에 적어야 한다.

## 원장

| # | 지적 내용 | 발생 이력 | 승격 상태 |
|---|---|---|---|
| L1 | `strict`/`harness` 계열 스킬이 "이 저장소의 유일 정본"이라고 선언한 파일이 실제로는 저장소에 없다(phantom SOT 참조) | 1차 2026-08-27(`docs/sot/30-strict-mode-contract.md` — 메모리 `feedback-verify-skill-sot-reference-exists`), 2차 2026-09-07(같은 파일 + `docs/sot/31-strict-recurrence-ledger.md`(이 파일, 당시 부재) + `SOT-19` + `npm run wt` + `tools/install-strict-skill.sh` — 아래 L2 참고, 사장님 질의 중 발견) | **승격 필요, 부채로 이관** — [이슈 #62](https://github.com/sangmokang/Valuehire_v6/issues/62)(자동 검사기: 스킬 파일이 인용하는 경로가 `git ls-files`에 없으면 FAIL, pre-push 편입). 이번 PR은 인용 텍스트 직접 수정까지만 하고, 자동 검사기는 별도 WU로 분리(스코프 과확장 방지, R9) |
| L2 | 글로벌 `strict` 스킬이 이 저장소에 없는 도구를 정본 명령처럼 서술한다 — `npm run wt`(이 저장소엔 `package.json` 자체가 없음, `docs/sot/verification-commands.md` 2026-09-02판이 이미 "make 레포도 npm 레포도 아니다"라고 명시), `SOT-19 §4`(이 저장소 SOT는 번호가 아니라 주제명으로 파일을 나눔 — `docs/sot/INDEX.md` 참고, 19번은 존재한 적 없음), `tools/install-strict-skill.sh`(§7이 진입점 수정 시 실행하라고 지시하지만 저장소 전체에 이 경로가 없음) | 1차 2026-09-07(이번 세션) | 1회 — 아직 승격 임계(2회) 미도달. 이 행 자체가 다음 재발 시 즉시 참조할 근거 |
| L3 | 글로벌 `strict` 스킬 §2 "Stop 게이트 마커" 문단 전체(`.claude/hooks/stop-evidence-gate.py`, `.claude/strict-active.json` 자동 생성/해제)가 이 저장소엔 배선돼 있지 않다 — L1/L2 수정을 codeaudit으로 자체 점검하던 중 추가 발견 | 1차 2026-09-07(이번 세션, `find . -iname stop-evidence-gate.py`·`find . -iname "strict-active.json*"` 둘 다 0건) | 1회 — 미도달. §2에 "레포에 hook 파일 없으면 이 문단 미적용" 캐비트만 추가하고, 실제 hook 신설은 이번 PR 범위 밖(부채로 남김) |

## 승격 규칙 (R4 원문 그대로 적용)

같은 번호(#)의 지적이 **2번째로**(= 이 표에 이미 있는 행에 "발생 이력"이 하나 더 붙으면) 나오면, 그 시점 세션은 **보고만 하지 않고** 아래 중 하나를 그 PR에서 완료해야 승격 상태를 `승격 완료`로 바꿀 수 있다. L1이 이미 이 상태다(1차 2026-08-27, 2차 2026-09-07).

- **H2 → H3**: 산문 문서 지적 → 러너(스크립트)가 자동 검사
- **H3 → H4**: 러너가 있는데도 실행 안 됨 → pre-commit/pre-push 훅 또는 CI 스텝으로 강제

## 비범위

- 이 원장은 `docs/engineering/*.md`에 이미 날짜 기록된 개별 사건의 전문(全文)을 복제하지 않는다. 요약 + 근거 문서 링크만 남긴다.
- 이 원장 자체의 각 행 추가는 L2+ code-change가 아니므로 워크트리 요구는 있으나(문서도 소스), Full Strict/Codeaudit/Adversarial 풀 사이클을 매 행마다 요구하지는 않는다 — 다만 이 파일을 처음 만드는 이번 PR은 코드 리뷰 스킬(codeaudit/humanreview)로 검토받는다.
