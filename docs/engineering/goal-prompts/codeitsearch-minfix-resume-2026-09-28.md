# Codeit 서치 재개용 최소 수정 프롬프트 (2026-09-28)

`/clear` 후 새 세션(다른 PC 포함)에 아래 구분선 아래 전체를 그대로 준다.
검증 이력: 초안 → Codex read-only 적대 검증(판정 "수정 후 사용", session `01a0e640-63fe-7460-b06c-f936ccfbfed1`) → 지적 7건 반영.

---

이전 Codeit 후보 서치 작업을 이어간다. 목적은 시스템 개선이 아니라 **사람인 Codeit 후보 서치를 안전하게 재개하기 위한 치명적 실행 오류의 최소 수정**이다.

## 0. 시작 위치와 현재 상태 (먼저 확인, 믿지 말고 재조회)

- 저장소: Valuehire_v6 루트. 브랜치 `feat/codeitsearch-aisearch-module`. `git status`로 기존 변경부터 확인한다.
  남의 미커밋 변경(예: `scoring.py`·`test_scoring.py`·`in-seoul-universities.json`)이 있으면 **건드리지도 되돌리지도 않는다.**
- 코드 수정은 워크트리에서: `git worktree add worktrees/codeit-minfix -b task/codeit-minfix` (`docs/sot/git-workflow.md:27`).
- 정본: `.claude/skills/codeitsearch/SKILL.md`, 실행 프롬프트 `docs/engineering/goal-prompts/oooseach-codeitsearch-2026-09-28.md`.
- 테스트: `uv run --with pytest python -m pytest tools/codeitsearch/tests -q` (system python엔 pytest 없음).
- 2026-09-28 기록(현장 재조회 전까지 **미확인** 취급):
  - 사람인 인재풀은 확장이 붙은 Chrome("Browser 1")에서 **미인증**이었다 — `/talent-pool/main/search`가 tutorial로 튕기고, `인재풀 바로가기` href=`/zf_user/auth?ut=c&...`, 헤더에 `로그인` 링크. CDP 9225 꺼짐. 사장님 "로그인했어" 후 재확인에도 동일.
  - Supabase `search_jobs` id 597 = 이 차단 기록(`auth_wall` 스냅샷 2건, close-job `blocked`).

## 1. 먼저 경계를 구분한다 (가장 중요)

- **에이전트 절차**(코드 아님): 브라우저 조작, 사람인 로그인 판정, 검색 반복, Gmail 발송. SKILL.md와 `page_trace.py:7`이 이를 명시한다.
- **Python 코드**: 포지션 적재(`ingest_positions.py`), 방문 기록(`page_trace.py`), 채점(`scoring.py`), 메일 본문 합성(`compose_mail.py` — 발송은 하지 않음).
- 에이전트 절차에 해당하는 문제는 **러너·자동화 코드를 새로 만들지 말고**, 실행 프롬프트/SKILL의 절차 문구 최소 수정 + 라이브 확인 항목으로 처리한다.

## 2. 확인하고, 실제 결함일 때만 최소 수정

**① 인증 실패 ≠ 후보 0명.** 확인 대상: `compose_mail.py`가 빈 후보를 상태 구분 없이 "60점 문턱을 넘은 후보 없음"으로 합성하는 경로(`:73`, `:106`), `page_trace.py close-job`이 `done`을 제한 없이 받는 경로. 원하는 동작: 미인증 → `blocked` 기록 → 검색 중단 → **결과 메일 합성·발송 금지**. 정상 검색 후 0명 → 0명 메일 가능. 필요하면 compose의 0명 문구/인자 분기 또는 close-job 경계를 최소 수정 범위에 넣는다(이건 금지 목록의 "메일 재설계"가 아니다). 기존 `test_compose_mail.py:63` 기대값을 바꾸게 되면 이유를 보고한다 — 삭제·약화 금지.

**② 다른 회사 입력에 Codeit 값이 섞이지 않게.** `ingest_positions.py:28`(상세 URL), `:47-49`(`company_norm`, `location`)가 Codeit 고정이다. 회사명은 이미 입력을 쓴다(`:34`). 입력 스냅샷/`contracts/humansearch/company-careers-sources.json`에서 **확인되는 값만** 쓴다. 없는 위치·URL 형식은 지어내지 말고 비우거나 명시적으로 실패시킨다. 새 DB 구조·추상화 금지.

**③ 검색이 유한하게 끝나게.** 코드에는 검색 루프가 없다(`keywords.py:258`은 유한 목록일 뿐). 따라서 코드에 루프를 신설하지 말고, 실행 프롬프트에 **한 가지 종료 조건**만 명시한다: 포지션당 준비된 키워드 목록 1회 순회(키워드당 최대 20페이지, 재순회 금지) 후 종료, 종료 시 `close-job --summary-file`에 종료 사유 기록.

## 3. 하지 말 것

scoring.py CLI 신설, 채점 재설계, 메일 전면 재설계, SOT/strict gate/red-ledger 구축, 파일명 오타, Windows 특수문자, 전체 리팩터링, 새 범용 프레임워크, 검색 러너 신설, 필요 이상의 문서. 위 항목이 ①~③에 직접 필요함이 코드로 확인되면 이유를 먼저 쓰고 최소 범위만.

**안전선:** 후보에게 발송 0회 · 자격증명/MFA/캡차 입력·우회 0 · 테스트 중 Supabase 실적재(`ingest_positions.py` dry-run 아닌 실행)·실제 Supabase 요청·Gmail 발송 0.

## 4. 적대 검증 — 오프라인과 라이브를 분리

| 반례 | 오프라인(코드·테스트로 증명) | 라이브에서만 확인 |
|---|---|---|
| A 로그아웃 상태 인재풀 진입 | blocked 상태에선 compose가 결과 메일을 만들지 않거나 차단 사유를 명시, close-job blocked 경계 | 실제 인증 판정 → blocked 기록 → Gmail 미발송 |
| B 로그인 후 정상 검색, 적합 0명 | "검색 완료 0명"이 인증 차단과 다른 출력/상태로 구분됨 | 실제 검색 로그 + 0명 보고 |
| C Codeit 아닌 테스트 회사 | `build_rows()`에 합성 스냅샷 A/B를 넣어 `company`·`company_norm`·`location`·`url`·`source_file`에 Codeit 값 0건 | — (실적재 금지) |
| D 결과가 계속 불만족 | 실행 프롬프트에 종료 조건 1개가 명시됨 | 실제 순회가 조건에서 끝나고 종료 사유가 기록됨 |

순서: 현재 코드 확인 → 결함 여부 판정(오탐이면 수정 없이 오탐 보고) → 최소 수정 → 관련 테스트 → 기존 테스트 전체 회귀.

## 5. 완료 조건과 보고

완료 = ① 인증 실패 ≠ 후보 0명 ② 다른 회사에 Codeit 값 미혼입 ③ 검색 종료 조건 명시. 그 이상 개선하지 않는다.
보고(짧게): 실제 확인된 결함 / 오탐 / 수정 파일 / 테스트 결과(명령+숫자) / A~D를 **오프라인 결과**와 **라이브 결과**로 나눠서 / 남겨둔 문제 / Codeit 서치 재실행 가능 여부. 인증된 검색 접근·종료 로그·메일 미발송 증거가 없으면 "코드 수정 완료, 실제 검색 검증 미완료"라고 쓴다.
