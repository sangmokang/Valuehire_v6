# Jev 조직 참조 집단 shadow 평가기 L3 goal

## 결론

외부 재직자 수집이나 후보 연락 없이, 기존 JD 평가를 그대로 보존하는 로컬 shadow 평가기를 만든다.
조직 유사도가 낮거나 Jev가 실행되지 않아도 기존 점수·필수조건·추천 상태는 바뀌지 않아야 한다.

배송 목표는 로컬 전용이다. 라이브 Jev 호출과 실제 평가셋 실행이 없으면 Jev 품질은 합격으로
표시하지 않으며, 운영 배포·외부 저장·포털·메일 동작은 하지 않는다.

## 2층 판단 근거

현재 v6에는 JD 직접 적합도를 결정적으로 계산하는 코드와 공개 재직자 관찰을 조직 패턴으로 묶는
코드가 있지만, 두 결과를 A/B/C/D로 분리해 재실행하는 제품 경계와 Jev 응답 검증은 없다. 따라서
기존 점수 함수를 수정하지 않고, 구조화된 역할 근거만 받는 별도 shadow 경로를 추가한다.

**무엇을** — 공식 Python SDK를 정확 버전으로 고정한 교체 가능한 Jev 어댑터와 로컬 CLI를 만든다.
**왜** — v6는 Python 3.14가 주 실행 환경이고 공식 SDK 0.7.1이 Python 3.14를 명시 지원한다. SDK는
요청·응답 타입과 인증 오류를 제공하므로 임의 HTTP 구현보다 계약 이탈 가능성이 작다.
**버린 길** — 이동 별칭 `jev-latest`는 동일 입력의 의미가 바뀔 수 있어 버린다. 비공식 SDK와 직접
HTTP 어댑터도 공식 호환 SDK가 확인됐으므로 버린다. 기존 `Criterion`에 B/C 값을 넣는 방식은 A 점수
분모와 gate에 섞일 위험이 있어 버린다.
**대가** — 새 런타임 의존성의 잠금 파일이 바뀌고, 실제 모델 품질은 키와 승인된 평가셋 없이는
검증할 수 없다. SDK 디버그 로그는 요청·응답 본문을 가리지 않으므로 제품 경계에서 debug logging을
사용하지 않고 원문 응답을 저장하지 않는다.
**되돌리는 법** — 이 작업의 로컬 커밋을 되돌리면 된다. DB migration·운영 데이터·외부 상태를 만들지
않으므로 별도 데이터 복구는 없다.

## 3층 계약과 증거

### 세션과 위험 등급

- 위험 등급: `L3` — 개인정보, 외부 AI 모델, SOT 경계, 3개 이상 파일 변경 가능성.
- 세션 식별자: `01a0c7bd-2cf3-7341-996e-129f045ee57f`.
- 기준 commit: `eaaee6219ed63d8ed4be1d52a3977216a15e5a03`.
- 격리 branch: `task/jev-org-reference-shadow`.
- 격리 worktree: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-org-reference-shadow`.
- 원본 worktree에는 착수 당시 사용자 변경 7개가 있었다. 이 작업은 해당 파일을 수정·복원·포맷하지
  않는다.
- 코드 예산: 정본 P11의 직접 작성 파일 hard 600줄, 함수 hard 100줄.

### 읽은 정본과 현재 구현 상태

- `AGENTS.md`: 짧은 task branch, 기존 훅/CI, 후보 자료·자격증명·로컬 DB commit 금지.
- `README.md`, `docs/engineering/development-setup.md`, `docs/sot/INDEX.md`: Python 3.14.1,
  `uv 0.11.3`, HumanSearch 실제 검증 명령을 확인했다.
- `docs/sot/strict-workflow.md`: goal → 계약 → RED → 최소 GREEN → 회귀 → V1/V2 → checkpoint 순서.
- `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`: P11 hard 600/함수 100, P14의 기존
  결정 점수 보호, P20의 0건 가짜 통과 금지를 확인했다.
- `docs/sot/candidate-search.md`, `docs/sot/company-intelligence.md`: A는 고정 100점, B는 비차단,
  C는 전이 경험, D는 추가 확인이며 소표본·학력·출신 회사는 gate가 될 수 없다.
- `docs/sot/humansearch-browser-contract.md`: 이번 범위에는 실제 포털 접속 권한이 없다.
- `.agents/skills/search/SKILL.md`: 회사 조사와 외부 후보 원장을 분리하고 A/B/C/D를 별도 기록한다.
- `humansearch/src/humansearch/recruiting_review.py`: `review_candidate()`가 A의 100점·필수조건 gate·
  날짜/경력 합산·추천·입력 hash를 결정적으로 계산한다.
- `scripts/company_intelligence.py`: 서로 다른 사람의 직접 근거를 세고, 소표본·중복·오래된 사실을
  제한하며 `organization_match_changes_jd_score=true`를 거부한다.
- `tests/test_company_intelligence.py`, `humansearch/tests/test_recruiting_review.py`,
  `scripts/acceptance-hs-gates.sh`, `.github/workflows/verify.yml`, `hooks/pre-commit`,
  `hooks/pre-push`, `docs/sot/verification-commands.md`: 관련 회귀와 실제 게이트를 확인했다.
- v4 경계: 위 v6 정본이 이 기능을 위해 v4 구현을 운영 근거로 지정하지 않으므로 v4 코드는 읽거나
  수정하지 않는다.

### 현재 상태와 근본 원인

현재 A 평가는 존재하지만 조직 패턴의 역할 근거를 고정된 질문으로 Jev에 보내고 B/C/D로 검증해
반환하는 호출 경로가 없다. 회사 조사 snapshot도 검색 가설용이며, 회사×직무군×seniority cohort의
canonical input hash, 질문·모델·threshold version, 원시 primitive answer 장부를 소유하지 않는다.

근본 원인은 기존 회사 조사와 후보 점수 사이에 의미 판정용 독립 경계가 없다는 것이다. 이 경계 없이
Jev 값을 기존 `Criterion`에 넣으면 조직 유사도가 A 점수나 추천 gate를 오염시킬 수 있다.

### 범위

1. 회사×직무군×seniority 기본 단위의 reference cohort 계약.
2. 중복 인물을 제거하고 서로 다른 사람의 반복 관찰만 pattern으로 승격하는 snapshot.
3. official SDK를 감싼 교체 가능한 semantic judge 경계.
4. 공식 Choice/Score/Noul 응답을 엄격 검증해 별도 B/C/D 결과로 변환.
5. `contracts/*.json` 한 곳의 model/question/threshold/pattern version.
6. canonical input hash와 개인정보 없는 결과 장부.
7. synthetic 단위·통합·적대 시험과 기존 A 회귀.
8. `python -m humansearch.organization_shadow_cli` 로 재실행 가능한 로컬 진입점.

### 비범위

- LinkedIn·Gmail·ClickUp·Supabase 라이브 접근 또는 쓰기.
- 실제 프로필 수집, 로그인, 포털 등록, 후보 연락, 자동 탈락·자동 병합.
- production 배포, 운영 DB migration, 실제 Jev 호출.
- raw profile·이메일·후보 개인정보를 git fixture나 로그에 저장.
- 특정 회사 목록 하드코딩.
- 회사·학교·성별·연령·국적을 조직 유사 근거로 사용.

### Work Unit

- WU-1 PLAN/SKELETON: goal, 중앙 계약, 실패하는 CLI/계약 시험을 고정한다.
- WU-2 BUILD: cohort snapshot과 canonical hash를 최소 구현한다.
- WU-3 BUILD: SDK adapter, 응답 검증, A/B/C/D orchestration과 CLI를 연결한다.
- WU-4 AUDIT: 회귀, mutation, 파일/함수 한도, 개인정보·비밀·diff 검사, R4 호출 추적.
- WU-5 AUDIT/CHECKPOINT: 독립 V1, 새 맥락 V2, 수정·재검증, Lore 로컬 commit.

각 WU의 거짓으로 만들 수 있는 단언은 각각 “계약이 실제 실행에서 실패한다”, “중복 인물이 패턴을
부풀리지 않는다”, “A 결과가 동일 객체 값으로 보존된다”, “고장 한 줄에서 시험이 실패한다”,
“독립 엔진의 판정이 재현된다”이다.

## EARS 인수 조건과 검증 명령

### AC-1 — hash 안정성

When 동일한 JD·후보·pattern snapshot·version이 입력되면 시스템은 동일한 canonical input hash를
생성해야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k hash`
- 기대값: 선택 시험 1개 이상 수집, 종료값 0, 동일 입력 hash 같음.

### AC-2 — A 불변

When 조직 유사도가 낮거나 unknown이면 시스템은 기존 JD 100점, 필수조건 gate, recommendation,
경력 월수와 A input hash를 그대로 반환해야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k a_review`
- 기대값: 종료값 0, shadow 전후 `ReviewResult` equality.

### AC-3 — 소표본 경계

When pattern이 소표본·직무 편중·근거 없음이면 시스템은 이를 회사 전체 패턴으로 승격하지 않아야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k sample`
- 기대값: `LIMITED` 또는 `NO_EVIDENCE`, company-wide 표식 없음.

### AC-4 — 명시 대리변수 field 배제

When 회사명·학교명·성별·나이·국적 field가 입력되면 시스템은 이를 Jev state에 포함하지 않고 입력
경계에서 거부해야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k forbidden`
- 기대값: 금지 field 입력은 runtime validation 실패, semantic state에는 canonical company/person ID 없음.

### AC-5 — Jev 미실행/실패 fallback

When API key가 없거나 judge 호출이 실패하면 시스템은 기존 A 결과를 정상 반환하고 B/C/D만 `NOT_RUN`
또는 `ERROR`로 표시해야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k fallback`
- 기대값: 종료값 0, A equality, semantic status 명시.

### AC-6 — 응답 shape 검증

When Jev 응답이 primitive 불일치, 범위 밖 score, 알 수 없는 Choice, 누락 answer를 포함하면 시스템은
runtime validation을 실패시키고 성공 결과를 만들지 않아야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k response`
- 기대값: 각 반례에서 `INVALID_RESPONSE` 또는 명시적 validation 예외.

### AC-7 — 중복 인물

When 같은 사람의 여러 관찰만 존재하면 시스템은 이를 반복 조직 패턴으로 계산하지 않아야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k duplicate`
- 기대값: unique sample 1, repeated patterns 0.

### AC-8 — version/hash 변화

When pattern snapshot 또는 질문 문구/version이 바뀌면 시스템은 pattern/question version 또는 input hash를
다르게 만들어야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py -k version`
- 기대값: 변경 전후 hash 다름.

### AC-9 — 추적 장부

Where shadow 결과가 저장되면 시스템은 model/question/threshold/pattern version, input hash, primitive
answer, probability/confidence 제공 여부, human-review 상태를 추적해야 한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow_cli.py`
- 기대값: synthetic CLI output readback에서 필수 field 존재, 종료값 0.

### AC-10 — 외부 부작용 0

While shadow mode이면 시스템은 외부 DB, ClickUp, Gmail, LinkedIn, 후보 연락 workflow를 변경하지 않아야
한다.

- 명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow_cli.py -k local_only`
- 기대값: 주입된 judge 외 network surface 없음, 명시 output 파일 외 쓰기 없음.

## counter-AC

- B score를 A의 100점 분모나 획득점에 가산한다.
- 낮은 B로 recommendation을 바꾸거나 후보를 제외한다.
- 명시 company/school/demographic field를 허용하거나 cohort/person/evidence ID를 Jev state에 넣는다.
- 한 사람의 중복 관찰을 서로 다른 표본처럼 센다.
- Noul answer에서 존재하지 않는 `confidence`를 읽거나 허용한다.
- key 부재·timeout·schema mismatch를 0점이나 성공으로 접는다.
- 시험에서만 호출되고 CLI가 부르지 않는 고아 모듈을 만든다.
- raw profile·이메일·API key·응답 원문을 git 또는 로그에 남긴다.
- 수집/검사 대상이 0개인데 통과한다.
- 기존 `review_candidate()`의 서명·계산·threshold를 조용히 바꾼다.
- 회사×직무군×seniority가 다른 관찰을 한 cohort로 합친다.
- stale/conflict 관찰을 반복 패턴으로 승격한다.

## 입력·출력·오류·권한·개인정보 경계

### 입력

CLI JSON은 기존 A 평가 입력과 다음 구조화된 field만 받는다.

- cohort: `canonical_company_id`, `role_family`, `seniority`, 선택적 `team_product_scope`, `as_of`,
  `known_denominator`.
- observation: 안정 `observation_id`, 가명 `person_id`, employment 상태, observation/source 시각,
  evidence ID, 역할·책임·문제·ownership·운영·제품 단계·도메인 문제·기술 환경 tag.
- candidate/JD semantic evidence: 같은 역할 중심 allowlist field만 허용. 문자열은 upstream에서 이미
  비식별화된 역할·책임·ownership·문제·운영 근거여야 한다.
- company name, school, gender, age, nationality와 알 수 없는 field는 입력 검증에서 거부한다.
- 이 모듈은 자유문장 속 임의 고유명사를 단어 목록으로 추정하지 않는다. upstream 비식별화가 지켜지지
  않은 입력은 계약 위반이며, 실제 표본과 오탐 기준 없이 자연어 탐지기로 보완하지 않는다.

### 출력

- A: 기존 `ReviewResult`의 값 그대로.
- B: role family Choice와 ownership/production/product-stage/domain/technical Score 관찰.
- C: transferable experience Score 관찰.
- D: direct evidence Noul, human verification Noul, 표본·최신성·충돌·실행 한계.
- ledger: schema/version/hash/status, primitive answer, Choice/Score에만 confidence, probability 제공 여부,
  human-review 상태. Noul에는 confidence field가 없어야 한다.

### 오류

- config/schema/hash/cohort 혼합: 명시적 validation error와 CLI nonzero.
- judge disabled/key 부재: A 정상 + B/C/D `NOT_RUN`.
- timeout/API 오류: A 정상 + B/C/D `ERROR`; 비밀과 원문 본문은 출력하지 않는다.
- 응답 누락/범위/Choice/model mismatch: A 정상 + B/C/D `INVALID_RESPONSE`.
- 재시도: SDK 기본 재시도에 맡기되 local shadow는 한 orchestration 호출만 기록한다.

### 권한과 개인정보

- 라이브 flag가 없으면 네트워크 client를 만들지 않는다.
- API key는 `TYPESAFE_API_KEY` 환경변수에서 SDK가 읽으며 파일·출력·예외에 기록하지 않는다.
- Jev state에는 구조화된 회사/person/evidence ID, 이름, 학교, 성별, 나이, 국적 field를 넣지 않는다.
- git에는 synthetic fixture와 계약만 둔다. raw 후보/profile 자료는 ignored artifact에만 둘 수 있다.
- 동시성은 제공하지 않는다. CLI 1회는 입력 1건을 직렬 처리하고 output은 지정한 한 파일에 원자적으로
  쓴다.

## 중앙 version 계약

`contracts/jev-org-reference-shadow.json` 한 파일이 다음을 소유한다.

- `model_version = jev-1.13.0`
- `question_version`, 각 atomic question의 primitive/instructions/criteria
- `threshold_version`, 관찰용 low/high 및 Noul human-review threshold
- `pattern_version`, 최소 unique cohort·반복 인물 수·stale 일수

특정 회사명은 넣지 않는다. 설정 변경은 hash 변화와 회귀시험을 요구한다.

## SDK 공식 근거와 선택

- 공식 repository: `https://github.com/typesafe-ai/typesafe-sdk-python`
- 공식 SDK 문서: `https://docs.typesafe.ai/sdk/python`
- 공식 API: `https://docs.typesafe.ai/api`
- 공식 model 목록: `https://docs.typesafe.ai/models`
- 확인 시각: 2026-09-22 KST.
- 공식 package `typesafe-sdk` 0.7.1은 `requires-python >=3.10`과 Python 3.14 classifier를 갖고,
  2026-09-21 changelog가 있다.
- 공식 API는 Noul=`noul`만, Choice=`choice/probabilities/confidence`,
  Score=`score/legend/probabilities/confidence`를 반환한다.
- current pinned model은 `jev-1.13.0`; `jev-latest`/`jev-preview` alias는 이동할 수 있다.

## RED→GREEN과 Harness 계획

1. Gate 0: 정본 직접 로드, 원칙 acceptance, 과거 goal/history, dirty baseline을 기록한다.
2. Gate 1: 이 goal과 EARS/counter-AC/입출력·오류·권한 계약을 고정한다.
3. Gate 2: 격리 worktree에서 synthetic 시험과 CLI smoke를 먼저 작성해 빠진 동작 때문에 RED인지
   확인하고 로컬 RED commit을 보존한다.
4. Gate 3: 테스트 파일을 바꾸지 않고 최소 구현으로 GREEN을 만든다.
5. Gate 3.5: CLI → `review_candidate()` → cohort snapshot → judge 경계 → runtime validation →
   A/B/C/D JSON까지 실행 추적한다.
6. Gate 4: targeted, full HumanSearch, root unittest, ruff, mypy, static/data/secret, diff check를 실행한다.
7. R2: 구현 한 줄을 임시 고장 내 원 시험 실패를 확인하고 원상 복구한다. 파일 600/601과 함수
   100/101 경계는 저장소 판정기 또는 동일 규칙의 임시 사본으로 실증한다.
8. Gate 5: V1/V2 finding을 해결하고 clean local Lore commit과 SHA를 남긴다.

## G/V1/V2/T 적대검증

- T: 이 goal의 EARS AC·counter-AC, 읽은 SOT, 중앙 JSON 계약.
- G: 현재 구현 엔진. 자기 검사는 합격 근거가 아니다.
- V1: 구현 맥락을 주지 않은 독립 엔진에 diff, T, 실행 증거만 주고 가짜 완료·고아 배선·A 오염·
  개인정보·0건·한도·Noul 오독을 공격시킨다.
- V2: 새 맥락 엔진이 V1의 모든 file:line/명령을 재실행하고 PASS 누락과 FAIL 오탐을 양방향 공격한다.
- V1/V2가 실제 독립 엔진으로 실행되지 않으면 `NOT_RUN` 또는 권한 밖 확정 시 `BLOCKED`이며 품질
  `PASS`로 대체하지 않는다.
- Jev 라이브 평가셋은 이번 범위에서 `NOT_RUN`이다. synthetic schema/배선 시험의 PASS를 Jev의 실제
  매칭 품질 PASS로 부르지 않는다.

## SKELETON과 배송 상태

새 표면은 로컬 CLI뿐이다. production URL·인증·DB·배포 SHA·운영 readback은 사용자가 명시한
비범위이므로 배송 상태는 `LOCAL_ONLY`를 넘지 않는다. SKELETON은 live flag 없는 CLI가 synthetic
입력에서 A를 계산하고 semantic `NOT_RUN`을 반환하며 외부 효과가 0임을 RED→GREEN으로 증명한다.

## rollback·영향 반경·데이터 안전

- rollback: 최종 local commit 한 건을 revert한다. lockfile도 같은 revert에 포함한다.
- 영향 반경: HumanSearch Python dependency, 새 shadow 모듈/CLI/contract/tests/docs. 기존 A 모듈은
  동작 변경하지 않는다.
- 데이터 안전 AC: When 실제 후보/profile 원문 또는 credential pattern이 추적 파일에 나타나면 기존
  secret/data exposure gate는 commit을 실패시켜야 한다.
- 외부 부작용 AC: While `--live-jev`가 없으면 network adapter가 생성되지 않아야 하며, 라이브 호출은
  이번 검증에서 실행하지 않는다.

## 검증 장부

### 원칙 직접 로드

명령: `sed`로 `docs/sot/coding-principles.md`, `docs/sot/principles.yaml` 전체를 직접 읽음.

- 시각: 2026-09-22 KST
- commit: `eaaee6219ed63d8ed4be1d52a3977216a15e5a03`
- 상태: `PASS`

### 원칙 acceptance

명령: `bash scripts/acceptance-principles-check.sh`

```text
2026-09-22T15:13:49+0900
eaaee6219ed63d8ed4be1d52a3977216a15e5a03
task/jev-org-reference-shadow
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT_CODE=0
```

→ 정본 두 파일과 34개 배선이 실제로 검사됐고 프로그램의 성적인 종료값은 0이었다. 이 결과는 각
제품 원칙의 구현 완료가 아니라 strict 계약 배선의 통과만 뜻한다.

### `omx explore` 우선 시도

명령: `omx explore --prompt 'Map the repository-local files, tests, CI jobs, hooks, and verification commands relevant to humansearch recruiting_review, company_intelligence, Python packaging, CLI entrypoints, file-size limits, secret/PII checks, and strict workflow. Return paths and symbols only; read-only.'`

```text
Error: [explore] cargo was not found. Install a Rust toolchain, use a compatible packaged omx-explore prebuilt, or set OMX_EXPLORE_BIN to a prebuilt harness binary.
```

→ 단순 탐색 우선 경로는 Rust 실행기 부재로 실패해 저장소 기본 도구로 전환했다.

- 종료값: 1
- 상태: `FAIL` 후 일반 `rg`/`sed` 읽기 전용 탐색으로 전환.

### Gate 2 RED

명령: `uv run --project humansearch --no-sync pytest -q humansearch/tests/test_organization_shadow.py humansearch/tests/test_organization_shadow_cli.py`

```text
FFFFFFF.FFFFFFFFFFF                                                      [100%]
18 failed, 1 passed in 0.52s
EXIT_CODE=1
대표 원인: NotImplementedError: shadow config loading is not implemented
CLI 원인: NotImplementedError: organization shadow CLI is not implemented
```

→ 시험 19개 중 18개가 구현 부재 때문에 실패해 올바른 RED를 증명했다.

- 상태: `RED` (의도한 구현 부재)
- 수집 오류, syntax 오류, fixture 개인정보 의존이 아니라 config/cohort/hash/orchestration/CLI의 실제
  미구현 때문에 실패했다.
- 이 시점의 테스트를 RED commit에 고정하고 첫 GREEN까지 변경하지 않는다.

### Gate 3 first GREEN

명령: `cd humansearch && uv run --no-sync ruff check src && uv run --no-sync mypy src && uv run --no-sync pytest -q tests/test_organization_shadow.py tests/test_organization_shadow_cli.py`

```text
All checks passed!
Success: no issues found in 20 source files
...................                                                      [100%]
19 passed in 0.62s
EXIT_CODE=0
```

→ 같은 시험 19개가 최소 구현 뒤 모두 통과했으며, 라이브 Jev 품질은 증명하지 않는다.

- RED commit `148b5af`의 두 시험 파일은 변경하지 않았다.
- 이 GREEN은 synthetic 계약·배선 검증이며 Jev 라이브 품질 검증은 아니다.

### R2 mutation과 P11 경계

반복 패턴 판정의 `distinct_people >= minimum_distinct_people`를 임시로 `>= 1`로 고장 내고
중복 인물 시험 두 개를 실행했다.

```text
FF                                                                       [100%]
2 failed in 0.44s
EXIT_CODE=1
```

→ 반복 인물 경계를 일부러 고장 내자 두 시험이 실패해 검사 민감도를 증명했다.

같은 한 줄을 복구한 뒤 targeted suite는 `22 passed in 0.70s`, 종료값 0이었다.

P11의 정본 규칙과 같은 AST/`splitlines()` 판정으로 직접 작성 파일·함수를 검사했다.

```text
organization_reference.py 318/600
organization_shadow.py 563/600
organization_shadow_cli.py 371/600
organization_shadow_jev.py 42/600
organization_shadow_validation.py 111/600
test_organization_shadow.py 494/600
test_organization_shadow_cli.py 142/600
LIMIT_PASS: direct files <=600 lines and Python functions <=100 lines
BOUNDARY_FILE_600=True
BOUNDARY_FILE_601=False
BOUNDARY_FUNCTION_100=True
BOUNDARY_FUNCTION_101=False
BOUNDARY_VERDICT: PASS
EXIT_CODE=0
```

→ 당시 직접 작성 파일·함수와 한도 경계 사본이 모두 정본 P11을 통과했다.

### Gate 4 회귀·정적·노출 검사

- `cd humansearch && uv run --no-sync pytest -q tests/test_recruiting_review.py` → `19 passed`, exit 0.
- `cd humansearch && uv run --no-sync pytest -q` → `252 passed in 10.24s`, exit 0.
- `bash scripts/acceptance-hs-gates.sh` → ruff/mypy 51개, pytest 252개, 독립 import 증명 모두
  `PASS`, exit 0.
- `python3 -m unittest discover -s tests -v` → `Ran 111 tests`, `OK`, exit 0.
- `bash verify.sh` → tracked secret pattern 및 `.env` 검사 `PASS`, exit 0.
- `bash scripts/acceptance-principles-check.sh` → 34/34 mechanism과 pre-push/CI wiring `PASS`, exit 0.
- `git diff --check` → 출력 없음, exit 0.
- 새 contract/source/test에서 고정 조사 대상 회사명, LinkedIn URL, Gmail 주소, 내장 API key 검색 →
  0건, exit 0.
- `bash scripts/scan-data-exposure.sh all` → current tracked 328개 위반 0건, current CSV/TSV/SQL
  개인정보 적재 0건. 다만 과거 reachable blob `docs/decisions/finding-events.jsonl`
  (`d8148f1065ecf5244e3a41585313165a4f13b2ae`) 때문에 history 단계는 exit 1. 해당 blob은 기준
  commit 이전 이력이며 이번 diff나 현재 추적 파일이 아니고, history rewrite는 비범위·파괴적이라 수정하지 않는다.

## 적대 검증 로그

### V1 — 외부 독립 엔진

- Claude 역할 래퍼 첫 실행: 지원하지 않는 옵션으로 실패. 원문 artifact를 `.omx/artifacts/`에 보존했다.
- Claude API key 경로 재실행: `Credit balance is too low`, 유효 판정 없음.
- API key를 제거한 OAuth 경로: 약 10분 동안 출력 없이 대기하여 중단(exit 130), 유효 판정 없음.
- Gemini 대체 경로: `gemini: command not found`.
- 판정: `BLOCKED`. 독립 엔진의 PASS/FAIL을 얻지 못했으므로 V1 PASS와 전체 품질 PASS를 주장하지 않는다.
  같은 Codex 세션의 하위 에이전트는 독립 엔진으로 대체하지 않는다.

### V2 — 최초 공격과 범위 정정

독립 V1 결과를 PASS로 가정하지 않은 채, fresh-context verifier가 계약·diff·실행 증거를 공격했다.

1. `HIGH`: 자유문장 속 회사/학교/브랜드를 막는 결정론적 경계가 없었다. 후속으로 만든 키워드
   탐지기는 정상 `company-wide` 경험을 차단하면서 `Acme Corp`은 통과시켜 오탐·누락이 함께
   재현됐다. 이 탐지 계층은 제거하고 명시 field 거부 + upstream 비식별화 입력 계약으로 범위를
   정정했다. 자유문장 고유명사 완전 탐지를 주장하지 않는다.
2. `MEDIUM`: snapshot과 config의 `pattern_version` 불일치를 허용해 장부가 입력과 다른 버전을
   표기할 수 있었다. hash 생성 전에 불일치를 거부하도록 수정했다.
3. `MEDIUM`: AC-5의 정확한 `-k fallback` 명령이 0개를 선택했다. 시험명을 명시적으로
   `fallback`으로 바꾸고 key 부재/호출 실패 두 경로가 수집되도록 수정했다.

3,017줄이 될 예정이던 dirty 상태에서 자연어 탐지 계층을 제거해 P11의 3,000줄 상한 아래로 되돌린다.
수정 뒤 exact AC 선택자와 전체 gate를 다시 실행하며, 외부 V1이 `BLOCKED`인 사실은 바꾸지 않는다.

### 코드 다이어트와 최종 로컬 검증

- 자연어 키워드 탐지 모듈·분기·시험을 삭제했다. 명시 field 거부와 upstream 비식별화 입력 계약은
  유지했고, A/B/C/D·hash/version·validator·CLI는 보존했다.
- targeted ruff + strict mypy + shadow/CLI/recruiting review: `42 passed`, exit 0.
- exact AC 선택자: hash 2, A 3, sample 3, forbidden 1, fallback 2, response 5, duplicate 2,
  version 2개가 각각 1개 이상 수집되어 모두 exit 0. CLI 2개와 local-only 1개도 exit 0.
- `bash scripts/acceptance-hs-gates.sh`: ruff/mypy/import와 pytest `253 passed`, exit 0.
- `python3 -m unittest discover -s tests -v`: `Ran 111 tests`, `OK`, exit 0.
- `bash verify.sh`, tracked exposure 328개, PII 5개, principles 34/34, `git diff --check`: 모두 exit 0.
- P11: 직접 코드·시험 파일 600줄 이하, 함수 100줄 이하, 600/601·100/101 경계 PASS.
  base 대비 `2,855 insertions`, untracked 0개로 3,000줄 상한 아래다.

### V2 — 정리 후 재공격

새 맥락 verifier가 현재 dirty tree를 독립적으로 읽고 exact AC, CLI probe, mismatch-before-judge,
forbidden-field 비노출, no-key 출력의 ID 비노출, P11을 재실행했다.

- 판정: `VERDICT PASS` — 요청 범위에서 blocking finding 없음.
- A는 모든 success/fallback/error 경로에서 원본 `ReviewResult`로 반환됐다.
- snapshot/config pattern version 불일치는 judge 실행 전에 거부됐다.
- Jev state와 local-only 출력에 company/person/evidence ID가 없었다.
- `candidate_evidence.school`은 CLI exit 2, output 미생성, 거부값 비노출로 재현됐다.
- V2는 로컬 구현 판정일 뿐 외부 독립 V1을 대체하지 않는다. V1은 계속 `BLOCKED`이며 라이브
  Jev 품질은 `NOT_RUN`이다.
