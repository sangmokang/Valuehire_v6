# 하네스 감사 — Anthropic Engineering 24편 기준 v6 하네스 진단·결정·재발 원장 (2026-10-31)

## 상위 목표 1문장

v6 하네스가 "틀린 것을 못 넘어가게 하는 힘"은 충분하지만 "맞는 것을 빨리 넘기는 힘"과 "세션 간 기억"이 부족하다는 가설을 실측으로 판정하고, 다음 작업 단위 7개와 그 순서를 결정한다.

성공 신호 1개: 이 문서의 결정 카드 D1~D7 각각에 대해 "실행 여부"를 다음 세션이 git log 만으로 판정할 수 있다.

## 근거 자료

- Anthropic Engineering 24편 요약: `evidence/harness-audit-20261031/anthropic-articles-{01-08,09-16,17-24}.md`
- 포멀 검증 글 사실검증 + 24편→v6 대조표: `anthropic-engineering-to-v6-methodology-2026-10-31.md`
- (부수) ABB Robotics 조사 원본 3종: `evidence/harness-audit-20261031/report_*.md` — 2026-10-28 발송 브리핑의 출처 보존용. 하네스와 무관하나 세션 산출물 휘발 방지(아래 재발 원장 R-1)로 함께 보관.

## 현재 상태 (실측, 2026-10-31 22:00~23:00 KST)

| 지표 | 값 | 명령 |
|---|---|---|
| 열린 PR | **63** (8/27 진단 12 → 5배) | `gh pr list --state open --limit 200 --json number -q length` |
| 그중 제품 코드(humansearch/src·apps·tools·supabase) 건드림 | 19 (30%) | 경로 분류 |
| 그중 문서·검증·테스트만 (SOT도 없음) | 14 (22%) | 경로 분류 |
| 병합 PR 누적 / 8-27 이후 | 33 / 12 | `gh pr list --state merged` |
| goal 문서 / verdict 문서 | 40 / 16 | `ls docs/engineering` |
| 제품 LOC(좁은 정의: humansearch/src+apps) / (넓은 정의: +tools+supabase) | 2,987 / 8,627 | `find <dirs> -type f \( -name "*.py" -o "*.js" -o "*.sh" -o "*.sql" -o "*.yml" -o "*.yaml" -o "*.json" -o "*.html" -o "*.css" \) -not -path "*/.venv/*" \| xargs cat \| wc -l` |
| 하네스 LOC(scripts+hooks+.github+verify.sh+suppressions) / 제품 테스트(humansearch/tests) / contracts | 8,665 / 3,190 / 390 | 동일. **초판의 2,685/15,764는 재현 불가라 폐기**(V1 A6·A7). 테스트는 하네스가 아니라 별도 열 |
| 문서 LOC(origin/main 시점 docs/**/*.md) | 29,165 | `git ls-tree -r --name-only origin/main -- docs \| grep .md$ \| xargs -I{} git show origin/main:{} \| wc -l` |
| 세션 시작 검사(session-status.sh) | **189~399초** (1차 399초: 다른 세션·백그라운드 push 병행 중 / V1 재측정 189초: user 62·sys 35, I/O 대기 절반) | `/usr/bin/time -p bash scripts/session-status.sh`. **1회 관측을 구조 원인으로 단정하지 않는다** — 조건 통제 반복 측정은 D1 WU의 첫 단계 |
| RED | 메인 체크아웃 0/29, 이 워크트리 **1/29** (`acceptance-0-2.sh` — gitignored `.secret-patterns`가 워크트리에 없음) | 환경 의존 결함. 워크트리 생성 시 로컬 전용 파일 링크 규칙 부재(R-7 후보) |
| 워크트리(작업용) / 로컬 task 브랜치 / 원격 task 브랜치 | 3 / 3 / **160** (8/27: 69 / 91 로컬) | `git worktree list`, `git branch --list "task/*"`, `git branch -r`. 로컬은 정리됐으나 원격 브랜치 160개는 미회수 |
| GitHub main 룰셋 | pull_request + required_status_checks(verify) | `gh api repos/.../rules/branches/main` |

### 게이트 적중 측정 (최근 verify.yml 실행 200회)

결과 분포: 성공 96 · 실패 95 · 취소 9. 실패 95회(고유 SHA 63개, push/pull_request 이벤트가 같은 SHA를 두 번 셈)의 첫 실패 스텝:

| 스텝 | 실패 |
|---|---|
| 억제 만료 스캔(suppressions.yaml) | 85 |
| 히스토리 전량 스캔 | 4 |
| 셸 스크립트 문법 검사 | 2 |
| 비밀 스캔(verify.sh) | 2 |
| hs-1305 후보자 PII 0건 | 1 |
| P3 조용한 실패 lint | 1 |
| 그 외 전 스텝 | 0 |

- **가림 효과(정정, V1 B1)**: 실패 run은 첫 실패 스텝에서 멈춘다. 억제 만료(13번)에서 멈춘 85회에서는 14번 이후가 실행되지 않았고, 스텝 1·5·8에서 멈춘 7회는 그 뒤가 실행되지 않았다. 또한 12번 `acceptance-0-5`는 `if: github.ref == 'refs/heads/main'`이라 **main 외 브랜치에서 항상 skipped**(성공 96회 중 94회). 따라서 "2~12번이 200회 전부 실행됐다"는 초판 문장은 거짓이다. 성립하는 문장은 "2~11번은 성공 96회 + 억제 전 단계 통과 85회 = 181회에서 실행됐고 적중 0"이다. 14~26번은 성공 96회에서만 실행·통과했다. 취소 9회의 진행 범위는 미확인.
- **고유 사건 단위(정정, V1 B2)**: 억제 만료 실패 85 run = 고유 SHA 59개(40개 브랜치). 실제 결함 적중 10 run = 고유 SHA 6개(비밀 1·히스토리 blob 2·문법 1·PII 1·P3 lint 1). 비율은 run 단위와 SHA 단위에서 비슷하나 절대 수는 run 단위가 약 2배 부풀어 있다.
- **원인 구조(정정, V1 B2)**: 억제 만료 실패 95회 중 54회는 **2026-10-21 이전**이다. 억제 기한이 10-13(#111) → 10-20(#130)으로 두 번 연장됐지만, main을 rebase하지 않은 브랜치는 옛 기한으로 계속 실패했다. 즉 "10-20 만료 단일 사건"이 아니라 **"기한 연장 → 미반영 브랜치 연쇄 실패"가 3회 반복된 구조 문제**다. 10-21 이후 41회는 현재 main의 10-20 기한 만료에 따른 실패다.
- **해석**: 실제 결함 적중은 고유 6건이며 비밀·히스토리·문법·PII·조용한 실패(P3) 계열이다. 메타 게이트(검사가 검사기·CI·원칙·스킬을 검사하는 스크립트, 목록은 아래)의 실측 적중은 181회 실행 범위에서 0이다. 이것은 "뚫린 적이 없다"는 뜻이지 "막은 적이 있다"는 뜻이 아니며, 억제력은 D3에서 뮤테이션으로 따로 측정한다.
- **메타 게이트 목록(21개, 분모 명시)**: `acceptance-principles-check.sh`, `acceptance-principles-mutations.sh`, `acceptance-guard-global-skill-files.sh`, `acceptance-silent-failure-lint-mutations.sh`, `acceptance-hs-cleanroom*.sh` 8종, `acceptance-hs-gates-mutations.sh`, `acceptance-hs-gates-antiforge.sh`, `acceptance-0-5.sh`, `acceptance-0-6.sh`, `acceptance-0-7.sh`, `acceptance-ci-step-integrity.sh`, `acceptance-semantic-mutations.sh`, `acceptance-verified-sha.sh`, `acceptance-verify-ac-m.sh`. 비메타 8개: `0-2`, `0-2-unreachable-content`, `hs-a3`, `hs-a4`, `hs-gates`, `invoice`, `secret-webhook-vendor`, `silent-failure-lint`. (초판 "17개"는 산출 근거 없이 적은 수였다.)
- 명령: `gh run list --workflow verify.yml --limit 200 --json databaseId,conclusion,headSha,createdAt` → 실패 run마다 `gh api repos/.../actions/runs/<id>/jobs -q '.jobs[].steps[]|select(.conclusion=="failure")|.name'`; 고유 SHA는 `headSha` 기준 `sort -u`; 날짜 분할은 `createdAt < 2026-10-21`.

### 원칙 ↔ 기계 장치 실존 대조

| 원칙 | 문서 | 코드 실존 |
|---|---|---|
| 비밀 스캔(P4·P22), P3 lint, P13 약화 패턴(추가 줄), P14 LLM→판정 금지, 억제 만료, 데이터 노출, 런타임 import 증명(P16 일부), CI 스텝 무결성, SHA 귀속(P23), 뮤테이션(P13⑥), 속성 테스트 4파일 | ○ | **○** |
| P11 코드 크기 예산 | ○ | ✗ (검색 적중은 문서 크기 주석) |
| P12 미참조 export·고아 스캔, capabilities.yaml | ○ | ✗ (단 P12 문면의 "SessionStart → session-status.sh HEAD 재확인"은 **존재** — P12는 일부 ○) |
| P16 `.contract.test` 접미사 강제 | ○ | ✗ |
| P19 외부 경계 라이브 스모크, V-3 `make ship` | ○ | ✗ (Makefile 없음) |
| SOT diff 동봉 | ○ | ✗ (check-docs-sot.sh는 구조 검사·CI 미연결) |
| P5 RED 후 테스트 불변, P15④ 기대값 단독 커밋 | ○ | ✗ |
| P8 lease, P9 멱등키·readback, P10 외부 감시자 | ○ | ✗ |
| 삭제 대칭(화면→하위 모듈) | ○ | ✗ |

`principles.yaml` 머리말이 이미 "mechanism_expected의 실제 구현 여부는 PASS 범위가 아니다"라고 면제한다. P1("장치 없는 원칙은 삭제") 문면과 충돌하며, P13④("검사기는 자신을 제외할 수 없다")에 해당한다.

### 진입점 드리프트

전역 `~/.claude/skills/strict/SKILL.md`가 참조하는 경로형 참조 **14개**(파일 9: `docs/sot/30-strict-mode-contract.md`, `docs/sot/31-strict-recurrence-ledger.md`, `.claude/hooks/stop-evidence-gate.py`, `.claude/strict-active.json`, `.claude/skills/strict`, `.claude/commands/st.md`, `.codex/skills/st`, `tools/install-strict-skill.sh`, `guards/runner-lease.py` + npm 스크립트 5: `wt`, `wt:done`, `red-ledger`, `strict:gate`, `check`) 중 v6에 존재하는 것은 **0개**다. 초판의 "11개 중 1개 존재(local-checks.sh)"는 오류였다 — 그 파일은 strict 스킬이 참조하지 않는다(V1 A22). `scripts/verify/check-strict-principles-skills.sh`는 Codex/Claude 사본의 원칙 블록 동치만 보고 경로 실존은 보지 않는다. harness 스킬의 `make red-ledger/task/ship`도 v6에 없다(`verification-commands.md`가 대체표를 두고 있음).

## 근본 원인

1. **하네스가 자기 자신을 재는 장치가 없다.** 게이트 적중, 세션 시작 비용, 장치 실존, 진입점 유효성, 병합 처리량 — 다섯 가지 전부 오늘 처음 측정됐다.
2. **신뢰 기반이 축소되지 않고 확장됐다.** 포멀 검증 글의 구조(Rocq 커널·스펙만 신뢰, 나머지는 검사 대상)와 반대로 29개 게이트가 서로를 검사하며 전부 신뢰 대상이 됐다. 그 결과 세션 시작 399초, 실제 적중 0인 메타 게이트 17개.
3. **세션을 넘기는 기계 파일이 없다.** features.json·init.sh·progress 파일 부재. 결정이 goal 문서 40개에 산문으로 남아 다음 세션이 다시 읽고 다시 판단한다.
4. **병합 게이트가 사람 1명이고, 하네스가 그 사람이 읽을 양을 늘린다.** 63건 중 44건이 제품 코드를 안 건드린다. 판정서가 PR 본문에 실린다.

## 결정 카드 (오너 결정 — 2026-10-31 토론 결과. 미실행은 "결정"이 아니라 "안"이다)

| ID | 결정 | 근거 글 | 되돌리기 |
|---|---|---|---|
| D1 | **세션 시작 검사를 증분화한다**: 마지막 성공 SHA 이후 변경 파일에 걸린 검사만 실행, 전수는 `--full` 옵션. 목표 <30초 | 장기 실행 하네스(세션 시작 = pwd·git log·progress) | 옵션 기본값 되돌림 |
| D2 | **features.json·init.sh·progress 도입**: 제품별 기능 목록(category/description/steps/passes), 에이전트는 passes만 변경(P5 동일 규칙) | 장기 실행 하네스 | 파일 삭제 |
| D3 | **메타 게이트 회수 검토**: 위 목록의 메타 게이트 21개를 "러너 1개 + 뮤테이션 1종"으로 통합할 수 있는지 WU로 평가. 비메타 8개는 유지. 평가 방법은 뮤테이션 적용 시 빨개지는지(억제력)이지 과거 적중 횟수가 아니다 | 하네스 설계(부품 하나씩 제거·load-bearing 검증) | 게이트 복원 |
| D4 | **병합 티어링은 보류(조건부)**: 가장 좁은 티어(SOT 미포함)에서 수혜 14건(22%), docs/sot까지 자동 티어에 넣으면 44건(70%). 효과는 티어 정의에 달려 있고 그 정의가 오너 결정이므로 보류. 대신 판정서·fixture를 PR 본문에서 분리(AC-2)하고 결정 큐를 둔다 | 소스 컨트롤 | — |
| D5 | **P1 자기 적용**: principles.yaml 면제 단서를 제거하고, 장치 없는 원칙은 `status: PLANNED`로 표기해 PASS에서 제외. SOT 추가는 장치가 생긴 뒤에만 | 포멀 검증(신뢰 기반 최소화) | yaml 되돌림 |
| D6 | **진입점 유효성 검사**: strict/harness 스킬이 참조하는 경로가 현재 저장소에 존재하는지 세션 시작 시 확인, 없으면 `verification-commands.md` 대체표로 안내 | 4월 포스트모템(환경 게이팅) | 스크립트 제거 |
| D7 | **배포 단계 장치화**: 릴리스 태그 `v6.YYYY.MM.DD-N` → CI artifact digest → `releases/<digest>/` 설치 → 이전 digest 한 명령 롤백(P6·P7). 현재 문서만 존재 | 소스 컨트롤(post-merge·pre-deploy 자동 테스트) | 태그 삭제 |

실행 순서: D1 → D6 → D2 → D5 → D3 → D4 → D7. 각각 워크트리 1개 = AC 1개.

## 인수 기준 (각 WU 착수 시 goal에 복제)

- AC-D1 (EARS) 세션 시작 시, 마지막 성공 SHA 이후 변경 파일이 10개 이하이면, `session-status.sh`가 30초 안에 `RED: n/m (incremental)`을 출력한다. counter-AC: `--full`이 기본값과 같은 결과를 내지 않으면 실패. 검사 0개면 NOT_RUN.
- AC-D2 (EARS) features.json이 있을 때, 코딩 에이전트가 `passes` 외 필드를 바꾸면 pre-commit이 차단한다. counter-AC: steps 삭제가 통과하면 실패.
- AC-D6 (EARS) strict 스킬이 참조한 경로가 저장소에 없으면, session-status.sh가 `ENTRYPOINT: n missing`을 출력한다. counter-AC: 0개를 "OK"로 내면 실패(P20).

## 재발 원장 (이 세션에서 관측, 2026-10-31)

| # | 사건 | 글의 경고 | 승격 |
|---|---|---|---|
| R-1 | 세션 산출물(방법론·요약·보고서 8개 파일)이 세션 전용 scratchpad에만 있어 종료 시 휘발될 뻔함 | 장기 실행 하네스(상태는 파일로 외부화) | 이 PR로 저장소 이관. 규칙 후보: "세션 산출물은 종료 전 저장소 또는 메모리에" |
| R-2 | 서브에이전트 3개가 보고서 본문 대신 "완료." 한 줄을 반환, 파일 저장을 재요청해 2라운드 소모 | 멀티에이전트(산출물은 파일, 리드에겐 참조만) | 위임 템플릿에 "출력 파일 경로 반환 필수" 고정(strict R8) |
| R-3 | 붙여넣은 기사 본문의 "pipeline" 단어가 매직 키워드 훅을 오발동 | 격리 글(외부 콘텐츠는 지시가 아니다) | 훅이 pasted_content 블록 내부 키워드를 무시하도록 개정 검토 |
| R-4 | 리서치 결과(ABB 브리핑)가 검증 없이 동료 2인에게 발송됨. 추정치 다수 포함 | 하네스 설계(자기평가의 관대함) | noncode 산출물에도 strict L1(주장-근거 매핑·반례) 적용. 재검증 결과는 `evidence/harness-audit-20261031/abb_recheck.md` |
| R-5 | 보고자(Claude)가 "검증 장치가 이미 있다"고 원칙 표를 근거로 단언 → 오너 되물음 한 번에 6개 중 4개 부재 확인 | 하네스 설계(평가자는 생성자와 분리) | 완료 주장에 "장치 파일 경로" 첨부 의무(strict §4 배선 증명의 하네스 버전) |
| R-6 | 억제 기한 연장(#111 10-13, #130 10-20)이 두 번 있었고, 연장마다 main을 rebase하지 않은 브랜치가 옛 기한으로 연쇄 실패(95회 중 54회가 10-21 이전). 10-20 현행 기한 만료 후 41회 추가 실패(이 PR 3커밋 6 run 포함, P23 UNVERIFIED). **단 PR #139(task/mail-governance-20261021)는 10-22에 suppressions.yaml을 비우고(억제 3건 해소 주장) verify 전 스텝 success** — "어떤 PR도 통과 불가"는 거짓이며, 해소안이 10-20부터 열린 채 미병합 상태다. 결정 부재가 아니라 **결정(해소 PR)의 미병합**이 원인 | 소스 컨트롤(병합 적체가 곱셈 손실을 만든다), 4월 포스트모템 | PR #139 검토·병합이 억제 연장보다 우선 후보. 연장 PR에는 "다음 만료 전 결정 책임·결정일" 필드 의무화 |
| R-7 | 워크트리에서 gitignored 로컬 전용 파일(`.secret-patterns`)이 없어 `acceptance-0-2.sh`가 RED 1/29 — 메인 체크아웃 0/29와 불일치 | 장기 실행 하네스(init.sh) | 워크트리 생성 시 로컬 전용 파일 링크·복사 규칙(D2 init.sh 범위) |

## 현재 CI 상태 (2026-10-31 23:10 KST)

이 PR의 CI는 R-6 때문에 빨간불이다. 문서 내용과 무관하다. 통과 경로는 두 가지다: ① PR #139(억제 해소)를 검토·병합하고 이 브랜치를 rebase, ② 억제 기한 연장 PR 후 rebase. 어느 쪽도 P13 영역이라 오너 결정이다.

## 비범위

- 하네스 게이트 삭제·통합 실행(D3는 평가 WU만).
- git-workflow.md "자동 병합 금지" 개정(D4 보류).
- 전역 스킬 파일 수정(저장소 밖).

## 적대 검증 정조준

- 반대 가설 A: "메타 게이트 적중 0은 억제 만료 가림 효과 때문이다." → 2~12번 스텝은 가림 없이 200회 실행됐고 적중 5회. 14~26번은 재측정 필요(성공 run 105회에서는 전부 실행·전부 통과).
- 반대 가설 B: "적중 0은 억제력(deterrence)의 증거다 — 있으니까 안 뚫린다." → 반증 불가능한 주장. D3에서 뮤테이션 1종으로 억제력을 측정 가능하게 바꾼다.
- 반대 가설 C: "399초는 오너 PC 성능 문제다." → 29개 전수 실행 구조 자체가 원인. CI도 같은 전수 구조로 4~6분.

## 적대 검증 로그

### V1 (2026-10-31 23:30~11-01 00:20, fresh·read-only, 판정서 `evidence/harness-audit-20261031/v1-verdict.md`) — **PASS 불가 → 정정 후 재판정 대기**

- 재현된 것(MATCH 18항목): 열린 PR 63, 제품 PR 19, 병합 33/12, goal 40/verdict 16, 실패 95·억제 85·결함 스텝 4/2/2/1/1, 룰셋, 인수 스크립트 29, hypothesis 4, Makefile/npm 부재, 면제 단서, 장치 부재 9행 전부.
- 틀린 것(MISMATCH 9항목)과 조치:
  - LOC 3종(2,685/15,764) 재현 불가 → 정의·명령 명시해 2,987(좁은)/8,627(넓은), 하네스 8,665, 테스트 3,190으로 교체.
  - 399초 → V1 재측정 189초. 1회 관측을 범위(189~399)로 바꾸고 반대가설 C 기각을 철회.
  - RED 0/29 → 워크트리 1/29(환경 의존). R-7 신설.
  - "성공 105회" → 96 + 취소 9. "2~12번 전부 실행" → 0-5는 main 외 skipped, 실패 run은 첫 실패 후 중단. 181회 범위로 재서술.
  - 85 run → 고유 SHA 59, 10 run → 6. 사건 단위 병기.
  - "10-20 만료 단일 사건" → 54/95가 10-21 이전. 기한 연장 미반영 연쇄로 재서술. "어떤 PR도 통과 불가" → PR #139 반례 확인(8d8b8bc success 2회, suppressions.yaml 삭제) 후 철회.
  - strict 참조 "11개 중 1개 존재" → 14개 중 0개. local-checks.sh 언급 삭제.
  - "메타 게이트 17개" 산출 근거 없음 → 21개 목록 명시.
  - D4 "효과 제한" → 티어 정의 의존(14 vs 44) 명시.
- V1 주장 중 저자가 재확인한 것: PR #139 상태(`gh run list --branch task/mail-governance-20261021` → 8d8b8bc success ×2), suppressions.yaml 해당 브랜치 부재, 실패 95회 중 10-21 이전 54회(V1은 44회로 보고 — 분할 기준이 createdAt 날짜라 경계 차이, 결론 불변).
- 유지된 결론: 원칙↔장치 부재 9행, 진입점 드리프트 방향, 메타 게이트 적중 0, 결정 카드 D1·D2·D5·D6·D7. D3는 분모 교체, D4는 조건부로 약화.
