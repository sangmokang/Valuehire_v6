# PR #109 리뷰 결함 수정 goal (2026-10-05)

## 결론
3엔진(Grok·ChatGPT·Gemini) 분할 리뷰 합본 결함 중 정본 계약이 분명한 5건(D1·D2·D3·D6·D7)을 최소 변경으로 고친다. 정본이 정하지 않은 D4(집단·근거 직무군 일치)와 D5(빈 근거 범주 허용)는 사장님 결정 전 손대지 않는다.

## 판단 근거
- 정본: `docs/engineering/jev-org-reference-shadow-goal-2026-09-22.md` "오류" 절 — judge timeout/API 오류는 A 정상 + B/C/D `ERROR`, 응답 범위·형식 위반은 A 정상 + `INVALID_RESPONSE`, 비밀·원문은 출력 금지.
- 비교 보고: `private-reviews/cursor-pr-review/pr109/ENGINE-COMPARISON.md`(gitignore).
- 비범위: D4·D5·D8~D10, 성능, SDK 내부.

## 현재 상태와 근본 원인
- D1 `organization_shadow_validation.py:96` `math.isfinite(큰 int)` 가 `OverflowError` → `organization_shadow.py:273` 은 `KeyError/TypeError/ValueError` 만 잡음 → A 결과가 파일로 남지 않음.
- D2 `organization_shadow_cli.py:109-110` `TypeSafeJevJudge()` 생성이 `run_shadow_review` 의 보존 경계 밖, `:121-122` `finally close()` 예외가 완성된 결과를 덮음.
- D3 `scripts/acceptance-hs-gates-antiforge.sh:38-42` 가 대시보드 계약 2개만 복사 → shadow 시험이 jev 계약을 못 찾아 pytest 실패 → 게이트가 spy 대조 전에 종료 → antiforge 는 "999 없음" 이라 PASS(공회전).
- D6 `organization_shadow_cli.py:283-289` 가 사용자 제어 키 문자열을 `field` 로 stderr 출력.
- D7 `organization_shadow_cli.py:46` `_same_file` 가 try 밖이라 심볼릭 링크 루프에서 traceback.

## 인수 기준 (EARS)
- AC1: If judge 응답의 숫자 필드가 float 로 표현 불가한 큰 정수이면, 시스템은 A 를 그대로 두고 `INVALID_RESPONSE`/`judge_response_invalid` 를 반환해야 한다. 검증: `pytest tests/test_organization_shadow.py -k invalid_jev_response` (큰 정수 2케이스 포함).
- AC2: If `--live-jev` 이고 judge 생성이 예외를 내면, CLI 는 종료값 0 으로 A 가 든 LOCAL_ONLY 출력을 쓰고 semantic 을 `error`/`judge_call_failed` 로 기록해야 한다. If judge.close() 가 예외를 내면, 이미 계산된 결과가 그대로 기록되어야 한다. 검증: `pytest tests/test_organization_shadow_cli.py -k judge_lifecycle`.
- AC3: When antiforge 가 위조 사본으로 게이트를 실행하면, 시스템은 사본이 저장소 수준 계약을 모두 가지게 하고, 사본이 위조 대조 단계에서 거부되어, 게이트의 마지막 판정 줄이 정확히 `FAIL: spy count [..] disagrees with independent count [..] (tampering)` 이고 종료값 1 인 경우에만 통과해야 한다(사본 시험 출력은 공격자 통제이므로 출력 전체 검색 금지). 검증: `bash scripts/acceptance-hs-gates-antiforge.sh` (계약 복사 제거 시 FAIL, 원복 시 PASS) + 조기 실패 출력 6종 차단·정상 탐지 1종 통과 대조.
- AC4: If 입력에 알 수 없는 키가 있으면, CLI 는 그 키가 필드 이름 모양(`[a-z][a-z0-9_]{0,63}\Z`, 개행 꼬리 불허)일 때만 이름을 보고하고 아니면 `<unknown>` 으로 보고해야 한다. 검증: `pytest tests/test_organization_shadow_cli.py -k unknown_key` + 기존 `school` 시험 유지.
- AC5: If 출력 경로 해석(`_same_file`)이 예외를 내면, CLI 는 traceback·경로 없이 JSON 오류와 종료값 2 를 내야 한다. (실제 심볼릭 링크 루프는 Python 3.14 에서 예외가 나지 않아 재현 불가 — 예외 주입으로 시험.) 검증: `pytest tests/test_organization_shadow_cli.py -k resolution_error`.

## counter-AC (가짜 완료)
- 시험이 예외를 `pytest.raises` 로 삼켜 초록이 되는 것. → 상태 값과 A 동일성을 단언.
- D2 를 judge=None(NOT_RUN) 으로 바꿔 통과시키는 것. → `error`/`judge_call_failed` 를 단언.
- D3 에서 검사를 빼서 통과시키는 것. → 파일 없음 실패를 잡는 음성 대조를 직접 실행.
- D6 에서 모든 키를 숨겨 기존 `school` 시험을 바꾸는 것. → 기존 시험 무수정 통과.

## 입출력·오류 계약
- 변경 함수: `_number`(검증), `_evaluate`(CLI), `_exact_keys`, `main`. 공개 서명 불변. 새 오류 코드 없음(기존 `judge_call_failed`, `invalid_input_or_config` 재사용).

## 배송 상태
NOT_APPLICABLE — 로컬 전용 CLI·시험·검사 스크립트. 운영 배포 없음.

## 적대 검증 로그
- V1 Codex (codex-cli 0.160.0, ChatGPT 구독 인증, OPENAI_API_KEY 제거, `-s read-only`), 대상 3443a74: **VERDICT: FAIL**.
  - 높음: antiforge 새 검사가 4개 단계만 차단하는 거부 목록이라 `FAIL: ruff/mypy/independent runtime import` 와 파일 없음 출력을 통과시킴 → 허용 목록(`(tampering)` 필수)으로 교체, 조기 실패 6종 BLOCKED·정상 탐지 ACCEPTED 실측.
  - 중간: `_same_file` 이 오류 경계 밖, AC5 시험 0건 → 경계 안으로 이동, 예외 주입 시험 추가(고장 사본 M6 에서 실패 확인).
  - 보조: D1 시험이 A 동일성 미단언 → `result.a_review == original` 추가.
  - 한계: 읽기 전용이라 uv 캐시·mktemp 불가 → 전체 시험·스크립트 미실행(V1 이 스스로 밝힘).
- 오케스트레이터 재실행: humansearch pytest 264 passed, ruff/mypy 통과, gates COLLECTED 263·mutations 6/6·antiforge 3/3.
- V2 Codex (`-s workspace-write`, `--no-local` 복제본 9f4c863, 구독 인증): **VERDICT: FAIL**.
  - V1 결함 2·보조 지적 해결 확인, AC1·AC2·AC4 추가 공격 반례 없음.
  - 높음(신규): 허용 목록이 출력 어디든 `(tampering)` 만 있으면 통과 → 사본 시험이 문자열을 섞으면 조기 실패도 합격. → 게이트 마지막 판정 줄 정확 일치 + 종료값 1 로 교체. 우회 5종 BLOCKED·정상 탐지 ACCEPTED·실제 PASS·계약 복사 제거 FAIL 실측.
  - 버린 길: 무작위 비밀값 판정 파일(별도 통로) — 게이트 스크립트까지 바꿔 검사 장치가 본체보다 커짐.
  - V2 환경 한계: 오프라인 캐시 부족으로 지정 명령 미완주, 소켓 권한으로 16건 실패(전부 PermissionError) — 오케스트레이터 환경에서 264 passed.
- 집중 재검증 Codex `-m gpt-5.5`(기본 gpt-6-sol 은 2회 "model at capacity" 로 판정 전 중단), 복제본 157101d: **VERDICT: PASS** — 판정 정규식이 게이트 127행 출력과 정확 일치, 변형 9종 실측, 모든 종료 경로의 마지막 줄이 게이트 자신의 출력이거나 `set -e` 무출력 사망(→ 판정 불일치로 FAIL, fail-closed). 의존성 준비 실패 환경에서 antiforge 가 FAIL 을 낸 것도 공회전 제거의 실증.
- 잔여 위험(낮음): gates.sh:107 이 `module_file`(사본 import 출력)을 실패 문구에 이어 붙여, 사본 코드가 종료 시점에 위조 판정 줄을 출력하면 마지막 줄이 될 수 있다. 이때도 게이트는 거부(종료값 1)하며 antiforge 사본은 antiforge 가 만드는 고정 파일이다.
- Gate 4: `./verify.sh` 종료값 0. humansearch pytest 264 passed · ruff · mypy(19 files) · gates COLLECTED 263 · mutations 6/6 · antiforge 3/3.

## 2차 작업 (2026-10-05 밤) — D4·D5 결정 반영, D6 부분 해결 보완

### 결론
사장님 지시로 D4 는 "막기(승인된 교차 직무군 계약이 있으면 판단 보류)", D5 는 "먼저 반증, 실제 거부일 때만 수정"으로 정해졌다. 정본·계약·시험 어디에도 교차 직무군 허용 조항이 없어 D4 를 fail-closed 로 고쳤고, D5 는 PR 원본에서 재현되어 고쳤다. 재검증 중 1차의 D6 수정이 부분 해결(필드 모양 식별자·이름·비밀값 노출)임을 발견해 보완했다.

### 판단 근거
- D4 정본: jev goal counter-AC "회사×직무군×seniority가 다른 관찰을 한 cohort로 합친다" 금지, 오류 절 "cohort 혼합: 명시적 validation error와 CLI nonzero". 교차 허용·별칭 매핑 계약 0건(`role_family|primary_role_family|alias` 검색). 정규화는 패턴 집계가 이미 쓰는 앞뒤 공백 제거만 적용 — 새 별칭 체계는 만들지 않음.
- D5 정본: 핵심 `RoleEvidence` 가 빈 범주를 허용하고(`_validate_observation` 은 존재하는 값의 공백만 검사), 핵심 시험이 빈 범주로 객체를 만들며, 계약 JSON 에 `insufficient_evidence` 선택지가 있다. CLI 만 빈 목록을 `invalid_input` 으로 거부 — 계약 불일치. 필수 항목(직무군·evidence_ids·키 존재·공백 문자열)은 그대로 거부.
- D6 보완: `[a-z][a-z0-9_]{0,63}` 모양 판정은 `person_12345`·`kim_minsu`·소문자 비밀값을 그대로 반사(실측). 개행 꼬리 변이는 시험 없이 생존. → 정본이 정한 금지 필드 이름 5개만 반사.

### 인수 기준 (EARS, 2차)
- AC6 (D4): If 관측치의 `role_evidence.primary_role_family` 가 앞뒤 공백 제거 후 `cohort.role_family` 와 다르면, 시스템은 snapshot 생성을 `ValueError("...role family...")` 로 거부하고 CLI 는 `invalid_input_or_config`·종료값 2·출력 없음이어야 한다. 후보·JD 직무군 차이와 다른 회사 cohort 는 거부하지 않는다. 검증: `pytest -k "role_family or another_role_family or another_company"`.
- AC7 (D5): When 근거 범주 6개 중 일부 또는 전부가 `[]` 이면, CLI 는 종료값 0 으로 A 와 shadow 결과를 써야 한다. If 직무군이 빈 문자열이거나, 범주 키가 없거나, 범주에 공백 문자열·비목록이 오거나, `evidence_ids` 가 비면 기존대로 거부해야 한다. 검증: `pytest -k "empty_optional or all_categories_empty or still_rejected"`.
- AC8 (D6): If 모르는 키가 `company_name|school|gender|age|nationality` 가 아니면, CLI 는 `<상위경로>.<unknown>` 만 보고하고 키 원문(이스케이프 형태 포함)을 stderr 에 남기지 않아야 한다. 검증: `pytest -k unknown_key` (공격 키 8종 + 진단 키 2종).
- AC9 (D2 보강, V1 지적으로 정정): If 판정이 유효하게 끝난 뒤 close 만 실패하면, CLI 는 `completed` 결과를 그대로 기록하고 stderr 에 `{"warning": "judge_close_failed"}` 한 줄을 남겨야 한다(예외 원문 금지). 검증: `pytest -k 'close_failure_after or lifecycle'`.

### counter-AC (2차)
- D4 를 대소문자 무시·별칭 추정으로 넓혀 "다른 직무군"을 통과시키는 것 → `Backend_Platform`·`backend` 거부 단언.
- D4 가 후보 직무군 차이까지 막아 B 판정 대상을 입력 오류로 만드는 것 → 후보 `data` 통과 단언.
- D5 를 위해 `_strings` 전체 또는 직무군·evidence_ids 까지 느슨하게 하는 것 → 필수 4종 거부 단언.
- D6 을 모든 키 숨김으로 바꿔 진단을 없애는 것 → `school`·`nationality` 반사 단언.

### 뮤테이션 (R2) — 고장 사본 16종
D1 가드 제거·D2 생성→NOT_RUN·D2 close 무보호·D6 원문 반사·D7 경계 밖·D4 검사 제거·D4 strip 제거·D4 casefold·D5 빈 목록 거부·D5 직무군 느슨화·D5 공백 허용·D6(신) 전부 반사·전부 숨김·식별자 모양 허용·nationality 제거: 전부 KILLED. 1차 판정식의 개행 꼬리(`\Z`→`$`) 변이는 1차 시험에서 SURVIVED → 2차 시험으로 대체.

### 재실측 (PR 원본 6ce1e6a vs 현재)
- 원본에 현재 시험을 얹으면 D1·D2·D6·D7 6건 RED(OverflowError·init/close RuntimeError·이메일 반사), D4·D5 9건 RED.
- D3: 원본 antiforge `PASS 3/3` 인데 위조 사본은 `FAIL: pytest exit 1`(계약 부재)에서 멈춤 — 공회전 재현. 현재: 정상 PASS(0), 계약 복사 제거·빈 계약·엉뚱한 계약 FAIL(1), 계약 없음 FAIL(2).
- D1: 점수·확률 필드는 큰 정수·NaN·±inf·bool·문자열 거부, 임의 정수 필드(`usage` 토큰)는 10**400 도 `completed`·A 동일.

### S3 처리
- 수정: 없음(D7 은 1차에서 수정). 보류: D8 시험 잠금 보강, D9 `as_of` 기본값(CLI 경로 무관), D10 순서 중복·문서 AC, argparse 오류의 JSON 경계 밖 출력(사용자 동작 변경).

### 적대 검증 로그 (2차)
- V1 Codex (codex-cli 0.160.0, `-m gpt-5.5`, `-s workspace-write`, `--no-local` 복제본 9741774, OPENAI_API_KEY 제거, 세션 01a10c0e-0ff1-7eb1-81ef-89d3bda777bc, 명령 57회): **VERDICT: FAIL** — 높음 1건: close 실패를 `contextlib.suppress` 로 삼켜 completed·error_code None 으로 은폐(구 AC9 가 이를 기대값으로 고정). D1·D4·D5·D6(2차)·D7 통과, D3 는 환경(소켓 bind 금지·uv 캐시·오프라인) 때문에 보조 shim 실행에서만 `PASS 3/3`. 원문은 private-reviews/pr109-review-fixes/V1-VERDICT.md.
  - 조치: 결과 보존 + stderr 경고(`judge_close_failed`)로 수정(f35196f 뒤 RED·c47cf5f GREEN), 뮤테이션 경고 삭제·원문 누설 2종 KILLED.
- V2 Codex (새 세션 01a10c17-fa23-7321-9df0-2d2f72936559, `--no-local` 복제본 4c29435, 명령 49회, V1 판정서 입력): **VERDICT: PASS** — V1 FAIL 해소 확인(제품 진입점 주입: rc 0·completed·stderr `{"warning": "judge_close_failed"}` 단일 JSON·원문 비노출), D1·D4·D5·D6·D7 PASS, 신규 중간 이상 결함 0. 독자 변이 3종(경고 삭제·casefold·allow_empty=False) KILLED. D3 는 V1 과 같은 샌드박스 제약(소켓 bind·오프라인)으로 전체 미재현 — 오케스트레이터 환경 실측(정상 rc 0 PASS 3/3, 계약 복사 제거·빈 계약·엉뚱한 계약 rc 1, 계약 없음 rc 2)으로 보완. 원문 private-reviews/pr109-review-fixes/V2-VERDICT.md.
- Gate 4 (4c29435): verify.sh · principles-check(34) · silent-failure-lint · hs-cleanroom · cleanroom-mutations 10/10 · hs-gates COLLECTED 290 · gates-mutations 6/6 · antiforge 3/3 — 전부 종료값 0.

## 남은 결정
- 없음(D4·D5 는 2026-10-05 사장님 지시로 결정됨). 배송(push·PR 반영)만 승인 대기.
