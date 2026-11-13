# 로컬 산출물 폴더 git 무시 — goal (2026-11-14)

등급: L3 (후보자 PII가 PUBLIC 저장소로 나갈 수 있는 판단) · 모드: mixed

## 현재 상태 (실측)

- 메인 작업트리에 미추적 폴더 2개: `audit_work/`(4파일, 16K), `.playwright-mcp/`(21파일, 332K).
- `git log --all -- audit_work .playwright-mcp` → 0건. 과거 커밋 이력 없음(유출 없음).
- `gh repo view --json visibility` → `PUBLIC`.
- `audit_work/candidates_raw.csv`·`fu_audit.csv`·`progress.json`: 사람인 후보 ID, Gmail 메일 링크, 점수 — 후보자 PII/업무 데이터.
- `.playwright-mcp/`: Playwright MCP 도구가 자동 생성한 메르카리(일본) 페이지 스냅샷·콘솔 로그. 비밀 패턴 없음(`cookie` 4건은 공개 정적 URL `static.jp.mercari.com/global_cookie`). 레포 코드와 무관.
- `.gitignore`에 두 경로 규칙 없음 → `git add -A` 한 번이면 PUBLIC 저장소로 push된다.

## 근본 원인

도구·감사 작업이 레포 루트에 산출물을 남기는데, `.gitignore`의 P21 블록(`/artifacts/`, `/data/`)이 이 두 경로를 덮지 않는다.

## 인수 기준 (EARS, 1개)

- AC: WHEN 최상위 `audit_work/` 또는 `.playwright-mcp/` 아래에 파일이 생기면, git SHALL 그 파일을 무시한다.
- counter-AC: **새 규칙은** 하위 동명 폴더(`docs/audit_work/…`, `humansearch/.playwright-mcp/…`)를 무시하지 않는다(최상위 앵커, P3 조용한 실패 방지). 기존 `*.log` 같은 확장자 규칙이 하위 경로를 무시하는 것은 이 AC의 범위 밖이다.
- AC-2 (V1 지적 반영): WHEN 두 경로의 파일을 `git add -f`로 강제 추가하면, pre-commit 훅과 공용 판정기(`scan-data-exposure.sh tracked`, CI 실행)가 SHALL 차단한다. 두 금지 목록의 동치는 `acceptance-hs-a4.sh`(CI)가 검사한다.
- 검증 명령: `bash scripts/acceptance-ignore-local-scratch.sh` (RED: 변경 전 FAIL, GREEN: 변경 후 PASS).

## 결정

- 두 폴더는 커밋하지 않는다(P21). 로컬 파일은 지우지 않고 그대로 둔다.
- 오너 지시 "커밋 push 해줘"는 `.gitignore` 변경 PR로 처리한다. PII push는 하지 않는다.

## 비범위

- 로컬 `audit_work/` 내용의 보관·삭제 판단(오너 몫).
- 하위 경로 산출물 차단 훅 추가.

## 롤백 / 영향 반경

- 롤백: 이 PR revert. 영향: `.gitignore` 2줄, 최상위 두 경로만.

## 적대 검증 로그

(아래에 V1·V2 결과를 추가)
