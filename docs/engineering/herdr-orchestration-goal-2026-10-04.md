# herdr 오케스트레이션 런처 — goal (2026-10-04)

등급: L2 (개발 도구·문서. 인증·PII·과금·외부 발송·마이그레이션 없음. 제품 코드·CI·SOT 미수정)
설명 문서: [herdr-adoption-2026-10-04.md](herdr-adoption-2026-10-04.md)

## 현재 상태

- 에이전트 병렬 작업 시 Claude·Codex·테스트 터미널을 각각 따로 띄우고, 어느 것이 승인 대기인지 사람이 돌아다니며 확인한다.
- worktree 규칙(`worktrees/<name>`, `task/<name>` — `docs/sot/git-workflow.md:20,27`)과 V1 규칙(fresh·read-only Codex — strict 스킬 §6)은 손으로 지킨다.

## 목표

herdr 워크스페이스 1개에 작업 1개(worktree·브랜치·pane 3개)를 띄우고, 테스트·적대 검증 결과를 종료 코드로 돌려주는 런처 `tools/herdr/vh-herdr.ps1`.

## 인수 기준 (EARS) · 검증 명령

| # | 기준 | 검증 |
|---|---|---|
| AC-1 | `task <name>`을 실행하면 `worktrees/<name>`에 `task/<name>` 브랜치 worktree가 생기고 라벨 `<name>` 워크스페이스에 `coder/review/test` pane이 생긴다 | `task herdr-smoke -NoCoder` → `git worktree list`, `herdr pane list --workspace <id>` |
| AC-2 | `test <name>`은 test pane에서 명령을 돌리고 그 명령의 종료 코드가 0이면 0, 아니면 1로 끝난다 | 기본(verify.sh) → exit 0, `-Cmd "cmd /c exit 3"` → `test exit=3`, exit 1 |
| AC-3 | `review <name>`은 매번 새 pane에 Codex를 `--no-daemon --sandbox read-only`로 띄우고 마지막 `VH_VERDICT:` 줄로 판정한다. PASS면 0, FAIL이면 1, 판정 줄이 없으면 무효로 1 | 본 브랜치에 실제 수행(아래 로그) |
| AC-4 | `done <name>`은 에이전트 작업 중, 미커밋 변경, ignored 파일(동의 없이) 중 하나라도 있으면 거부하고 worktree를 지우지 않는다. 브랜치는 지우지 않는다 | working 에이전트 중 거부 → idle 후 제거 |

### counter-AC (일어나면 안 되는 것)

- 같은 라벨 워크스페이스가 이미 있으면 새로 만들지 않는다 (재실행 → 거부 확인).
- 기존 `worktrees/<name>` 경로가 다른 브랜치이면 열지 않는다 (`task/vh-other` 경로로 거부 확인).
- 명령줄 에코만으로 `test`가 완료 처리되지 않는다 (줄 전체 정규식 + 무작위 마커).
- herdr 호출 실패를 삼키지 않는다 (`pane_not_found` 시 즉시 throw 확인).

## 비범위

- CI·SOT·제품 코드 수정, 새 `scripts/acceptance-*.sh` 추가(추가 시 verify.yml 동시 배선 의무 — `docs/sot/verification-commands.md`).
- 원격 SSH 접속(작업 PC SSH 서버 개방은 보안 결정이 필요한 별도 작업).
- V2·codeaudit 자동화 — 기존 절차 그대로.

## 적대 검증 로그

- **V1-1** (Codex, herdr `review`로 실행, 2026-10-04 15:07) — FAIL. MAJOR 2: 기존 경로 브랜치 미확인, 작업 중 에이전트가 있어도 `done` 제거. → d502c17에서 해소, 실측 확인.
- **V1-2** (19:15) — FAIL. MAJOR 3: goal 문서 부재, `test` 기본값(verify.sh=비밀 스캔)을 게이트 전체처럼 서술, `done`이 ignored 파일 미확인. → 본 문서 추가, 서술 정정, `-IncludeIgnored` 동의 게이트 추가.
