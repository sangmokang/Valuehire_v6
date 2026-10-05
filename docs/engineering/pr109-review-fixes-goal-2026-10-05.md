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
- AC3: When antiforge 가 위조 사본으로 게이트를 실행하면, 시스템은 사본이 저장소 수준 계약을 모두 가지게 하고, 사본이 위조 대조 단계에서 `(tampering)` 으로 거부된 경우에만 통과해야 한다(그 밖의 모든 조기 실패는 FAIL — 허용 목록). 검증: `bash scripts/acceptance-hs-gates-antiforge.sh` (계약 복사 제거 시 FAIL, 원복 시 PASS) + 조기 실패 출력 6종 차단·정상 탐지 1종 통과 대조.
- AC4: If 입력에 알 수 없는 키가 있으면, CLI 는 그 키가 필드 이름 모양(`^[a-z][a-z0-9_]{0,63}$`)일 때만 이름을 보고하고 아니면 `<unknown>` 으로 보고해야 한다. 검증: `pytest tests/test_organization_shadow_cli.py -k unknown_key` + 기존 `school` 시험 유지.
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
