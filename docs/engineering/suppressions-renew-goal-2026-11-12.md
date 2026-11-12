# 억제 원장 만료 해소 — gate-scope(1)·p13 삭제 탐지 실제 수정 + 승인 연장 2건 (goal, 2026-11-12)

모드 code-change · 등급 L3(검증 체계·억제 원장 수정) · 워크트리 `worktrees/suppressions-renew` · 브랜치 `task/suppressions-renew` · base `bb12d86`

## 현재 상태 (file:line)

- CI "억제 만료 스캔" `.github/workflows/verify.yml:152-172` 이 `suppressions.yaml` 3건(expiry 2026-10-20)으로 FAIL.
  증거: PR #153 run 43180648848 — `FAIL: 만료된 억제 (expiry 2026-10-20 < 오늘 2026-11-12)` × 3, exit 1.
- 자기제외 탐지 `hooks/pre-commit:80-91` case 패턴이 `verify.sh|scripts/*.sh|hooks/*` 뿐 —
  `.github/workflows/*`, `.claude/skills/*/local-checks.sh` 는 검사 밖(`suppressions.yaml` gate-scope-gaps (1)).
- 약화 탐지 `hooks/pre-commit:93-113` 은 `scan_added`(:42-52) 로 diff `+` 줄만 본다 → 삭제형 약화 미탐(p13-deletion-blindspot).
  게다가 staged 목록(:25)이 `--diff-filter=ACMR` 라 파일 삭제(D)는 아예 보지 않는다.
- Makefile·`make red-ledger`·재발 원장(`docs/sot/31-*`) 은 이 레포에 없다(파일 부재 확인) — 게이트 0 러너 부재로 기록.

## 근본 원인

억제 3건이 기한 내 해결되지 않았고, 과거 대응(#111, #130)은 기한 연장만 했다.

## 인수 기준 (EARS)

- AC-1: WHEN `.github/workflows/*` 또는 `.claude/skills/*/local-checks.sh` 가 `grep -v …<자기 파일명>` 을 담아 커밋되면
  THE pre-commit SHALL 차단한다. 검증: `bash scripts/verify/run-acceptance.sh scripts/acceptance-gate-scope-selfexempt.sh`
  counter-AC: 자기제외가 없는 워크플로 변경은 통과해야 한다. 기존 `scripts/*.sh` 자기제외 차단은 유지된다.
- AC-2: WHEN `.github/workflows/*` 에서 스텝·검사 줄이 삭제(수정에 의한 소멸·파일 삭제 포함)되어 커밋되면
  THE pre-commit SHALL 차단한다. 검증: `bash scripts/verify/run-acceptance.sh scripts/acceptance-p13-workflow-deletion.sh`
  counter-AC: 워크플로의 주석 삭제·비검사 스칼라 변경, 그리고 워크플로 밖 경로의 줄 삭제는 통과해야 한다.
- AC-3: CI "억제 만료 스캔" 스텝 본문을 로컬에서 그대로 실행하면 `PASS` · exit 0.

## 계약

- 입력: 스테이징 인덱스 vs HEAD. 출력: 기존 계약 그대로 `BLOCKED: <사유> — <경로>` (stderr), exit 1. 삭제된 줄 내용은 출력하지 않고 HEAD 기준 행 번호만 출력한다.
- "실행 단위" 정의(V1 반영 후): YAML 파싱 결과의 `jobs.*.steps[*]` 의 `name`·`uses`·`run` 줄(앞뒤 공백 제거, 주석·빈 줄 제외)과 job 수준 `uses`. env·with 등 다른 키의 문자열은 세지 않는다. (초판은 줄 텍스트 판정이었고 V1 에서 뚫렸다.)
- "삭제" 정의: HEAD 판 실행 단위 다중집합에서 인덱스 판에 남은 단위를 뺀 나머지. 순서 이동은 삭제가 아니다.
- 판정기: `scripts/verify/check-workflow-deletion.sh <old> <new>` → exit 0 OK / 1 DELETED / 2 판정 불가(훅은 차단).

## 입력 영역 표 (AC-2)

| 입력 | 처리 |
|---|---|
| 워크플로 M — 스텝 통째 삭제 | 차단 |
| 워크플로 M — run 블록 안 명령 1줄 삭제 | 차단 |
| 워크플로 M — 명령 수정(옛 줄 소멸) | 차단 (보수적 결정 D-1) |
| 워크플로 D(파일 삭제) / 워크플로 밖으로 rename | 차단 (`--no-renames` 로 D 로 본다) |
| 워크플로 M — 주석·빈 줄 삭제 | 통과 |
| 워크플로 M — 비검사 스칼라 변경(`timeout-minutes` 등) | 통과 (범위 밖, 비범위 참조) |
| 워크플로 M — 스텝 순서 이동 | 통과 |
| 워크플로 M — 삭제한 스텝 문구를 env 등 비실행 문자열에 남김 | 차단 (V1-1) |
| 워크플로 M — 앵커·flow 형식 스텝의 삭제 | 차단 (V1-2) |
| 워크플로 M — run 이 첫 키인 스텝의 형제 키 변경 | 통과 (V1-3) |
| 워크플로 M — YAML 파싱 실패 | 차단 (fail-closed) |
| 워크플로 T — 일반 파일 → symlink 등 타입 변경 | 차단 (V1 2차) |
| 워크플로 M — run 줄 인라인 주석만 변경 | 통과 (V1 2차) |
| 워크플로 A(신규) / 추가만 | 통과 (추가 줄은 기존 ③ 약화 패턴이 본다) |
| 워크플로 밖 경로의 삭제 | 통과 (오너 지시: 리팩터링 오탐 방지) |
| HEAD 없음(최초 커밋) | 삭제 개념 없음 → 통과 |
| HEAD/인덱스 blob 읽기 실패, awk 실행 실패 | 차단 (fail-closed) |
| 그 외 전부 | 차단 (fail-closed) |

## 결정 목록

- D-1 명령 줄 수정은 삭제로 본다(옛 검사 문구가 사라짐). 정당한 수정은 기존 P13 관례대로 사람이 판단한다. — 오너 지시 "스텝·검사 줄이 삭제되면 탐지"의 보수적 해석.
- D-2 탐지 위치는 pre-commit 만(기존 P13 ③과 동일 층). CI 이관은 비범위.
- D-3 회귀 테스트는 신규 인수 스크립트 2개로 두고 CI 고정 목록에 등록한다(pre-push 는 글로브로 자동 포함).

## 게이트 계획

RED1 커밋 → GREEN1 커밋 → RED2 커밋 → GREEN2 커밋 → 원장 정리 커밋 → `./verify.sh` + 관련 acceptance + 억제 만료 스캔 로컬 실행 → V1(Codex adversarial-review, read-only) → V2 → push/PR/CI 초록 → merge(오너) → #153 재실행.

## 적대검증 정조준

- 삭제를 주석 처리(`# - name:`)로 위장하면? → 주석화는 원래 줄 소멸 = 삭제로 잡혀야 한다.
- 삭제 + 같은 문자열을 주석/echo 안에 다시 추가하면? → 다중집합 비교가 정규화 문자열 기준이라 `echo "bash x"` 는 다른 줄 → 잡힘. 단 같은 줄을 다른 스텝(if: false 스텝)으로 옮기면 못 잡는다 — 그건 CI step-integrity 검사 몫.
- `--no-verify` 우회 — 기존 P13 전체와 같은 한계(비범위).

## 비범위

- gate-scope-gaps (2) import 그래프 기반 네트워크 검사 → 별도 억제 항목, expiry 2026-11-26 (오너 승인 2026-11-12).
- ci-transfer-guarantee 실행 증명 전환 → expiry 2026-11-26 (오너 승인 2026-11-12).
- 비검사 스칼라 약화(timeout 등), CI 측 삭제 탐지.

## 롤백 · 영향 반경

- 롤백: revert PR 병합. 영향: pre-commit 차단 범위 확대(워크플로 편집자), CI 스텝 2개 추가(수십 초).

## 적대 검증 로그

### V1 1차 — Codex adversarial-review (fresh, read-only, `--base origin/main`) · thread `01a1cffa-ad63-7011-8ab4-18b1d3fb08e7`

판정: **needs-attention** — "Do not ship: read-only repros demonstrate deletion bypasses, a legitimate-change false positive, and an AC-1 self-exclusion bypass."
- [high] 비실행 YAML 텍스트(top-level env 블록 스칼라)에 삭제한 스텝 문구를 남기면 줄 판정기가 삭제 0건.
- [high] `run: &checks |` 앵커 블록, `- {name:, run:}` flow 형식 스텝의 삭제를 못 잡음.
- [medium] `- run: |` 이 첫 키인 스텝에서 형제 `env: LABEL` 변경을 삭제로 오탐(runind 가 대시 들여쓰기).
- [medium] `grep -v 'local-checks\.sh'` 처럼 점을 이스케이프하면 자기제외 탐지 우회.

조치: 4건 전부 수용. 반례 6개를 RED(`9afec36`)로 고정 → GREEN(`8178735`): YAML 구조 판정기 + 점 3표기 대조.
잔여 한계(주장하지 않음): 같은 명령 줄을 실행되지 않는 run(heredoc 등)으로 옮기기, 임의 정규식 자기제외.


### V1 2차 — Codex adversarial-review (fresh, read-only) · thread `01a1d002-8dc8-74f2-b89f-591f265a63db`

판정: **needs-attention** — "workflow type changes bypass the hook, and comment-only edits can be falsely blocked. suppressions.yaml correctly retains only the two approved items, both expiring 2026-11-26."
- [high] 워크플로를 symlink 로 바꾸면(T) DM·ACMR 어느 목록에도 없어 훅이 검사 없이 exit 0.
- [medium] run 줄 인라인 주석 삭제를 실행 단위 삭제로 오탐.

조치: 2건 수용. RED(`8da3e1b`) → GREEN(`5db49de`): `--diff-filter=DMT` + 인덱스 mode 검사, 따옴표 인식 인라인 주석 제거.
자체 mutant F(판정 불가 → 통과)가 생존해 fail-closed 시연 추가(`624c3bb`) 후 사멸 확인.
