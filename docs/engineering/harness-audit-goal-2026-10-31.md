# 하네스 감사 — Anthropic Engineering 24편 기준 v6 하네스 진단·결정·재발 원장 (2026-10-31)

## 상위 목표 1문장

v6 하네스가 "틀린 것을 못 넘어가게 하는 힘"은 충분하지만 "맞는 것을 빨리 넘기는 힘"과 "세션 간 기억"이 부족하다는 가설을 실측으로 판정하고, 다음 작업 단위 6개와 그 순서를 결정한다.

성공 신호 1개: 이 문서의 결정 카드 D1~D6 각각에 대해 "실행 여부"를 다음 세션이 git log 만으로 판정할 수 있다.

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
| 제품 LOC / 검증 인프라 LOC / 문서 LOC | 2,685 / 15,764 / 29,165 | find+wc |
| 세션 시작 검사(session-status.sh) | **399초**, RED 0/29 | `/usr/bin/time -p bash scripts/session-status.sh` |
| 워크트리 / task 브랜치 | 3 / 2 (8/27: 69 / 91 → AC-3 달성) | `git worktree list` |
| GitHub main 룰셋 | pull_request + required_status_checks(verify) | `gh api repos/.../rules/branches/main` |

### 게이트 적중 측정 (최근 verify.yml 실행 200회)

실패 95회. 실패를 일으킨 스텝:

| 스텝 | 실패 |
|---|---|
| 억제 만료 스캔(suppressions.yaml) | 85 |
| 히스토리 전량 스캔 | 4 |
| 셸 스크립트 문법 검사 | 2 |
| 비밀 스캔(verify.sh) | 2 |
| hs-1305 후보자 PII 0건 | 1 |
| P3 조용한 실패 lint | 1 |
| 그 외 전 스텝 | 0 |

- **주의(가림 효과)**: 억제 만료는 13번째 스텝이다. 85회에서 14~26번 스텝은 실행되지 않았으므로 그 스텝들의 0은 과소 측정이다. 2~12번(원칙 검사·원칙 뮤테이션·스킬 잠금·P3·클린룸 8종·hs-gates 3종·히스토리·0-2·0-6·0-7·0-5)은 200회 전부 실행됐고 적중은 P3 1·히스토리 4뿐이다.
- **해석**: 85회(89%)는 외부 결함이 아니라 하네스 자체 사건(2026-10-13 억제 3건 만료, PR #129·#130 예고)이다. 실제 결함 적중은 200회 중 10회, 전부 비밀·PII·문법 계열이다. 메타 게이트(검사가 검사를 검사)의 실측 적중은 0이다.
- 명령: `gh run list --workflow verify.yml --limit 200 --json databaseId,conclusion` → 실패 run마다 `gh api repos/.../actions/runs/<id>/jobs -q '.jobs[].steps[]|select(.conclusion=="failure")|.name'`

### 원칙 ↔ 기계 장치 실존 대조

| 원칙 | 문서 | 코드 실존 |
|---|---|---|
| 비밀 스캔(P4·P22), P3 lint, P13 약화 패턴(추가 줄), P14 LLM→판정 금지, 억제 만료, 데이터 노출, 런타임 import 증명(P16 일부), CI 스텝 무결성, SHA 귀속(P23), 뮤테이션(P13⑥), 속성 테스트 4파일 | ○ | **○** |
| P11 코드 크기 예산 | ○ | ✗ (검색 적중은 문서 크기 주석) |
| P12 미참조 export·고아 스캔, capabilities.yaml | ○ | ✗ |
| P16 `.contract.test` 접미사 강제 | ○ | ✗ |
| P19 외부 경계 라이브 스모크, V-3 `make ship` | ○ | ✗ (Makefile 없음) |
| SOT diff 동봉 | ○ | ✗ (check-docs-sot.sh는 구조 검사·CI 미연결) |
| P5 RED 후 테스트 불변, P15④ 기대값 단독 커밋 | ○ | ✗ |
| P8 lease, P9 멱등키·readback, P10 외부 감시자 | ○ | ✗ |
| 삭제 대칭(화면→하위 모듈) | ○ | ✗ |

`principles.yaml` 머리말이 이미 "mechanism_expected의 실제 구현 여부는 PASS 범위가 아니다"라고 면제한다. P1("장치 없는 원칙은 삭제") 문면과 충돌하며, P13④("검사기는 자신을 제외할 수 없다")에 해당한다.

### 진입점 드리프트

전역 `~/.claude/skills/strict/SKILL.md`가 참조하는 경로 11개 중 v6에 존재하는 것은 `.claude/skills/verify/local-checks.sh` 1개. `npm run wt`, `docs/sot/30-strict-mode-contract.md`, `31-strict-recurrence-ledger.md`, `.claude/hooks/stop-evidence-gate.py`, `tools/install-strict-skill.sh`, `package.json`, `Makefile` 등은 v5 경로다. `scripts/verify/check-strict-principles-skills.sh`는 Codex/Claude 사본의 원칙 블록 동치만 보고 경로 실존은 보지 않는다. harness 스킬의 `make red-ledger/task/ship`도 v6에 없다(`verification-commands.md`가 대체표를 두고 있음).

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
| D3 | **메타 게이트 회수 검토**: 적중 0 게이트 17개를 "러너 1개 + 뮤테이션 1종"으로 통합할 수 있는지 WU로 평가. 비밀·PII·P3·히스토리·문법 5종은 유지 | 하네스 설계(부품 하나씩 제거·load-bearing 검증) | 게이트 복원 |
| D4 | **병합 티어링은 보류**: 수혜 14건(22%)으로 효과 제한. 대신 판정서·fixture를 PR 본문에서 분리(AC-2)하고 결정 큐를 둔다 | 소스 컨트롤 | — |
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

## 비범위

- 하네스 게이트 삭제·통합 실행(D3는 평가 WU만).
- git-workflow.md "자동 병합 금지" 개정(D4 보류).
- 전역 스킬 파일 수정(저장소 밖).

## 적대 검증 정조준

- 반대 가설 A: "메타 게이트 적중 0은 억제 만료 가림 효과 때문이다." → 2~12번 스텝은 가림 없이 200회 실행됐고 적중 5회. 14~26번은 재측정 필요(성공 run 105회에서는 전부 실행·전부 통과).
- 반대 가설 B: "적중 0은 억제력(deterrence)의 증거다 — 있으니까 안 뚫린다." → 반증 불가능한 주장. D3에서 뮤테이션 1종으로 억제력을 측정 가능하게 바꾼다.
- 반대 가설 C: "399초는 오너 PC 성능 문제다." → 29개 전수 실행 구조 자체가 원인. CI도 같은 전수 구조로 4~6분.

## 적대 검증 로그

(후기록)
