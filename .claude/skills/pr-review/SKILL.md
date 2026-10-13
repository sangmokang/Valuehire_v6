---
name: pr-review
description: Valuehire_v6 열린 PR 전부를 Claude·Codex 가 herdr 옆 창에서 함께 전수 리뷰하고, 실제 문제는 PR 브랜치에서 고쳐 push·댓글까지 남기는 자동 리뷰를 착수·중지·점검·1회 실행한다. "PR 리뷰 전부 돌려", "열린 PR 전수 리뷰", "PR 자동 리뷰 켜", "리뷰 루프 상태", "pr-review", "자동 리뷰 멈춰" 에서 사용.
---

# pr-review — 열린 PR 전수 자동 리뷰 (Claude + Codex · herdr)

## 무엇을 하나
- PR 한 건마다 herdr 새 탭을 열고 **왼쪽 Claude(1차, 읽기 전용)** → **오른쪽 Codex(2차, Claude 발견 재현·판정 + 수정 커밋)** 순으로 돌린 뒤 탭을 닫는다.
- 에이전트를 PR 마다 새로 띄우므로 문맥이 매번 비어 있다(= clear). 따로 /clear 할 필요가 없다.
- 기준: **사업 목적을 지킨다 · 변경 파일 전수 · 실제 문제만 최소 수정 · 오버엔지니어링 금지 · 사장님 결정이 필요한 건 고치지 않고 적는다.** 지시문 정본은 `scripts/pr-review/prompt-claude.md`, `prompt-codex.md`.
- 결과: PR 댓글 1개(판정 `병합 가능 | 수정 후 병합 가능 | 보류`), 수정은 PR 브랜치에 fast-forward push. 같은 SHA 는 다시 보지 않는다.
- 병합은 하지 않는다. 병합은 사람이 댓글을 보고 결정한다.

## 명령 (herdr 창 안에서, 저장소 루트 기준)
| 하려는 것 | 명령 |
|---|---|
| 착수(매시간) | `bash scripts/pr-review/start.sh` |
| 착수(하루 한 번) | `bash scripts/pr-review/start.sh 86400` |
| 중지 | `bash scripts/pr-review/start.sh --stop` |
| 지금 1회만 | `PR_REVIEW_MAX_PER_RUN=1 bash scripts/pr-review/run.sh` |
| 스크립트 수정 반영 | `--stop` 후 다시 `start.sh` (실행본은 `~/.valuehire-pr-review/bin/` 사본) |

## 상태 점검 — 보고는 이 숫자로
```bash
S=~/.valuehire-pr-review
tail -5 $S/loop.log                                   # 마지막 회차
jq -r '.status' $S/ledger.jsonl | sort | uniq -c      # REVIEWED / FAILED / HOLD_PII / GAVE_UP
gh pr list --state open --json number --jq length     # 열린 PR 수
```
남은 PR 수 = 열린 PR 중 현재 head SHA 가 장부에 REVIEWED·HOLD_PII·GAVE_UP 로 없는 것. PR 별 원자료는 `$S/runs/pr-<번호>-<시각>/`(claude.md · verdict.md · 두 창 로그 · push.log).

## 사람이 봐야 하는 것
- `HOLD_PII`: 판정문에 이메일·전화번호·프로필 URL 패턴 → 공개 저장소라 댓글을 올리지 않았다. `runs/` 의 verdict.md 를 보고 가려서 수동 게시.
- `GAVE_UP`: 같은 SHA 3회 실패. `runs/` 의 두 창 로그로 원인 확인.
- 댓글의 `결정 필요` 줄.

## 한도와 안전장치
- 회차당 3건(`PR_REVIEW_MAX_PER_RUN`). 화면에 사용량 한도 문구가 보이면 그 회차를 멈추고 다음 회차에 이어 간다.
- Claude: `dontAsk` + Read/Grep/Glob/git 조회 + 결과 폴더 쓰기만. Codex: `workspace-write` 샌드박스(네트워크 없음) + 결과 폴더. push·댓글은 스크립트만.
- 전용 clone(`~/.valuehire-pr-review/repo`)에서만 작업한다. 사람이 쓰는 작업트리·워크트리는 건드리지 않는다.
- 잠금으로 동시 실행을 막고, 잠금 주인이 죽었으면 넘겨받는다.

## 알려진 함정
- Claude 첫 실행 시 clone 폴더 신뢰 확인 창 → 스크립트가 '신뢰'로 넘긴다(우리 저장소 사본). Codex 훅 신뢰 창은 신뢰하지 않고 닫는다.
- `ANTHROPIC_API_KEY` 가 있으면 Claude 가 로그인 대신 API 잔액으로 돌다 죽는다 → 창에서 unset 후 띄운다.
- Claude Code 는 `.git` 안쪽 쓰기를 막는다 → 결과 폴더는 `.git` 밖(`runs/`).
- herdr 서버가 재시작되면 반복도 멈춘다 → `start.sh` 를 다시 돌린다.

## 시험
`bash scripts/verify/run-acceptance.sh scripts/acceptance-pr-review.sh` — 가짜 gh·herdr 로 약속 30건(SHA 중복·새 세션·탭 닫기·Claude 실패 시 Codex 생략·개인정보 보류·사용량 한도·잠금)을 실제 실행으로 본다. CI 에서도 돈다.
