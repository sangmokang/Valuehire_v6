/strict

[VALUEHIRE-V6-JEV-GATEWAY → 공급자 경계·배송 WU] L3

새 세션(/clear 직후)에서 실행한다. 아래 "확정 사실"은 2026-09-26 05:3x KST 세션의 주장이다.
0단계에서 다시 확인하고, 어긋나면 그 항목을 보고하고 판단이 필요하면 멈춘다.

## 확정 사실 (0단계에서 재확인할 것)

작업 위치
- 워크트리 worktrees/jev-ea-wu1-split, 브랜치 task/jev-evidence-assessment-wu1-split (PR #110, base task/jev-shadow-base-split = PR #109).
- 원격 origin 은 dbc7fd0 까지. 로컬 미push 커밋(실측 18개 + 이 프롬프트): 39a66bf → 18a5aa1 → 402c4cb → d4b3517 → 1f32f8a → f00de09 → 4bffc70(이전 세션)
  → c648416(RED) → 5330ad7(GREEN) → 72ec917(변이 기준점) → d409bfb(V1 RED) → d983434(V1 GREEN)
  → 0ee7510(V1 2차 RED) → 432a0d0(V1 2차 GREEN) → 2788c66(시험 보강)
  → 43098e3(V1 3차 RED) → 9c76c38(V1 3차 GREEN) → 이 프롬프트 직전 시험 보강 커밋 → 이 프롬프트 커밋.
- push·PR 수정·병합·배포는 하지 않았다. 원격 CI 빨간불 원인(억제 만료 2건, #74→#75→#77 체인)은 그대로다.

이번 WU 에서 바뀐 것 (2026-09-26 사장님 결정: 모델 이름 jev 사용, 외부 전송은 합성 데이터만)
- evidence_assessment_cli.py: AI_GATEWAY_API_KEY 가 있으면 TypeSafeJevJudge(api_key=, base_url="https://ai-gateway.vercel.sh/typesafe"),
  없으면 TYPESAFE_API_KEY 기존 경로. 둘 다 있으면 Gateway 우선. 저장소 live_calls_allowed 는 여전히 최종 결정권.
  결과 파일에 "jev_call"(endpoint·requested_model·response_model·gateway_trace, 요청 없으면 null) 추가.
  gateway_trace 는 provider_metadata 원본이 아니라 허용 목록(original_model·final_provider·provider_attempts[provider,status,success]·
  generation_id·market_cost)만 식별자 문자(영숫자·_./-, 64자 이하) 검사로 뽑는다 — 오류 문구·라우팅 설명 같은 자유 문장은 버림.
  사용한 키(Gateway 또는 TYPESAFE)와 6글자 이상 겹치는 값은 null. 시도 목록은 10개까지, 넘친 수는 provider_attempts_dropped.
  SDK 재시도 끔(RetryPolicy(max_retries=0)) → request_attempts = 실제 HTTP 요청 수.
- organization_shadow_jev.py: 생성자에 api_key·base_url·retry 키워드 추가(기본 동작 불변).
- organization_shadow_cli.py: CountingJudge.last_response 보관.
- organization_shadow_validation.py: validate_response(gateway_metadata=True) 일 때만 provider_metadata(객체) 추가 허용 — 근거평가만 켠다.
  조직 shadow 경로는 기존처럼 정확히 3키. 공식 문서 응답 예시에 이 키가 있다.
- evidence_assessment.py: 모델 로더가 "jev" 또는 고정 버전 jev-X.Y.Z 허용(jev-latest·jev-1.13·gpt-1.13.0 은 계속 거부).
- contracts/jev-evidence-assessment.json: model_version "jev". contracts/jev-org-reference-shadow.json 은 jev-1.13.0 그대로(범위 밖).
- scripts/acceptance-evidence-assessment-mutations.sh: 기준점 4개 갱신(G6·M33·N7 은 이번 변경, S3 는 f00de09 이후 이미 rc 2 로 멈춰 있던 결함).

검증(이번 세션)
- RED c648416: 새 시험 7건이 동작 누락으로 실패(Gateway 요청 0, 모델 불일치 invalid_response, jev_call 없음).
- V1(Codex) 1차 FAIL 3건(높음 키 되돌림 저장, 중간 재시도 과소 기록, 중간 조직 경로 완화) → d409bfb RED 3건 → d983434 GREEN.
  고장 사본 3종(재시도 켬·키 차단 끔·조직 경로 완화) 각각 시험이 잡음.
- V1 재확인 1회차 FAIL 1건(중간: 키 일부 되돌림이 결과에 남음) → 0ee7510 RED → 432a0d0 허용 목록 기록 → 2788c66 허용 필드 자유문장 반례.
  고장 사본 T1~T5(원본 저장·필터 제거·오류문구 보존·길이 해제·참거짓 상태코드) 전부 잡힘(T2 는 처음 생존 → 2788c66 로 닫음).
  최종(2788c66): hs-gates rc 0(ruff·mypy strict 58파일 0, pytest 449 passed). 근거평가 변이 86 생존 0·원칙 34/34 는 432a0d0 기준(이후 시험 파일만 변경).
- V1 재확인 2회차 FAIL 2건(중간: 허용 필드의 키 조각 식별자 통과, 중간: 시도 목록 무제한 5.4MB) → 43098e3 RED → 9c76c38 GREEN
  → 직접 경로 키 조각 반례 추가. 고장 사본 F1~F3(조각 검사 끔·상한 제거·직접 키 제외) 전부 잡힘(F3 는 처음 생존 → 반례 추가로 닫음).
  9c76c38 기준 hs-gates rc 0(pytest 450), 변이 86 생존 0, 원칙 34/34. 이후 시험 1건 추가(시험 파일만).
  실제 라이브 응답 메타데이터를 새 추출기에 오프라인으로 넣어 digitalocean 503 → typesafe-ai 200 이 그대로 뽑힘을 확인.
- GREEN 5330ad7 뒤(1차): humansearch 시험 444 passed, ruff 0, mypy 22파일 0, hs-gates rc 0(mypy strict 58, pytest 444),
  원칙 34/34, 근거평가 변이 86 생존 0(rc 0). 고장 사본 5종(Gateway 키 무시·추가 키 전부 허용·메타데이터 형식 미검사·
  안전 스위치 무시·호출 기록 누락) 모두 시험이 잡음.
- 라이브 합성 1건(2026-09-25T20:17:07Z, 코드 72ec917 — V1 수정 전. 수정 뒤 라이브 재호출은 하지 않았다): 제품 CLI `python -m humansearch.evidence_assessment_cli --live-jev`,
  계약 스위치를 그 1건 동안만 true → 종료 후 false 복구(git diff 0 확인). 결과 rc 0, EXTERNAL_JEV·request_attempts 1,
  completed, verdict SUPPORTED, confidence 0.39(기준 0.6 미만 → requires_human_review true), response_model "jev",
  generationId gen_01M3D3DW6CTRPNDVKA9CNJYKHD, marketCost 0.000021924, 출력 파일에 키 0회.
  입력: 가명 cand-pseudo-0001, 근거 "Ran the payment API on call." (ea_support.payload()). 실제 후보자 데이터 0.
- 라우팅: 두 번 모두 digitalocean(503 실패) → typesafe-ai(200). 즉 합성 근거가 제3 공급자에게 도달했을 수 있다.

공급자 고정 조사(공식 문서, 2026-09-26 확인)
- https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe : 공급자 제한 옵션 언급 없음.
- https://vercel.com/docs/ai-gateway/modalities/evaluation : 다른 주소 POST /v1/evaluate 에서만
  providerOptions.gateway {"zeroDataRetention": true, "only": ["typesafe-ai"]} 문서화. 이 주소는 요청·응답 모양이 다르다
  (boolean/probability, usage camelCase, providerMetadata) → 지금 쓰는 TypeSafe SDK 로 못 부른다.
- 따라서 현재 안전 경계: 실제 후보자 데이터는 Jev/Gateway 로 보내지 않는다.

남은 결함·제약
- [중간, 결정 필요] 공급자 경계 미고정 — 위 조사 참조.
- [낮음] 모델 "jev" 는 떠다니는 이름 → 같은 입력도 날짜별 결과가 다를 수 있다. jev_call.gateway_trace 의 generation_id 로만 추적.
- [낮음, 남은 한계] 키와 5글자 이하만 겹치는 조각은 걸러지지 않는다(6글자 창 기준). 실제 키로 실제 응답을 넣었을 때 오탐 0.
- [낮음, 범위 밖] organization_shadow_cli 는 SDK 기본 재시도(max_retries 2)를 그대로 써서 실패 시 요청 수를 과소 기록할 수 있다.
- [낮음] organization_shadow_cli 는 아직 Gateway 를 모른다(계약 jev-1.13.0, 키 확인 TYPESAFE_API_KEY 만).
- [낮음, 기존] evidence_assessment_cli.main(config=...) 주입이 저장소 스위치보다 우선 — 제품·셸 호출자 0건(재확인 필요).
- [중간, 기존] organization_reference.py:118-125 표본 2명(LIMITED)에서도 B classification=high — 미착수.
- [낮음, 기존] 근거 평가 not_run 결과 error_reason None — 미착수.

## 0단계 — 재확인 (수정 없음)
a. 워크트리 HEAD·status, 이 워크트리를 cwd 로 쓰는 다른 세션(lsof -a -d cwd -Fpcn + awk 경로 대조). 있으면 멈춘다.
b. 위 사실을 명령으로 표로(일치/불일치/확인 불가). 키는 `security find-generic-password -s valuehire-ai-gateway -a sangmokang >/dev/null` 로 존재만.
c. `git grep -n 'jev-1.13.0\|"model_version": "jev"' contracts humansearch/src` 로 계약 상태 확인.

## 1단계 — 사장님 결정 (코드 전, 최대 2개)
1) 공급자 경계: (A) 합성 데이터만 계속 — 코드 변경 없음 / (B) /v1/evaluate 로 옮겨 only:["typesafe-ai"]+zeroDataRetention 을 걸고
   실데이터 허용 검토 — TypeSafe SDK 를 못 쓰므로 새 HTTP 호출 코드와 응답 변환이 필요(작지 않다) / (C) BYOK(TypeSafe 키 직접 등록) 가능 여부 확인.
2) 배송: 로컬 커밋 19개(이 프롬프트 커밋 포함, `git rev-list --count dbc7fd0..HEAD` 로 재확인)를 PR #110 에 push 할지(push 는 승인 후만). 억제 만료 체인이 풀리기 전엔 원격 CI 는 빨강.
결정 없이는 2단계로 가지 않는다.

## 2단계 — 결정된 범위만
- (A) 이면 코드 변경 없이 push 준비만: 로컬 게이트 재실행(hs-gates, 변이, 원칙) → 승인 시 push → gh pr view 로 원격 재확인.
- (B) 이면 실패 시험 먼저(요청 본문에 providerOptions.gateway.only 가 반드시 들어감, 없으면 거부) → 최소 구현 → 합성 1건 라이브로
  finalProvider 가 typesafe-ai 이고 providerAttempts 에 다른 공급자가 없음을 확인. 금지: 새 프레임워크·범용 라우터·npm·TypeScript.
- 실제 후보자 데이터 라이브는 이 프롬프트 범위 밖이다.

## 보고
§8 3층, 결정 최대 2개, A VERIFIED / B DEFERRED(외부) / C FAILED.
끝나면 다음 프롬프트를 이 폴더에 새 파일로 쓰고 로컬 커밋(push 는 승인 후).

## V1 기록 (이번 WU)

| 회차 | 대상 | Codex 세션 | 명령 실행 수 | 판정 | 결함 | 처분 |
|---|---|---|---|---|---|---|
| 사전(설계) | main 작업트리(잘못된 cwd) | 01a0da2f-480e-7450-9694-ab40deb373c4 | — | needs-attention | 높음 2(제품 CLI 가 Gateway 모름, 모델 충돌) | 5330ad7 로 해결 |
| 1 | 4bffc70..72ec917 | (codex-v1.txt) | 34 | FAIL | 높음 1 키 되돌림 저장 · 중간 1 재시도 과소 · 중간 1 조직 경로 완화 | d409bfb→d983434 |
| 2 | 72ec917..d983434 | 01a0da3d-2e57-7100-ae95-d42bf084fabe | 29 | FAIL | 중간 1 키 일부 되돌림 | 0ee7510→432a0d0→2788c66 |
| 3 | d983434..2788c66 | 01a0da43-2b5c-7050-88a8-84ed08953f72 | 23 | FAIL | 중간 2 허용 필드 키 조각, 시도 목록 무제한 | 43098e3→9c76c38→시험 보강 |
| 4 | 9c76c38 이후 | — | — | NOT_RUN | — | 검증 계층 제한(사장님 2026-09-18 지시)으로 미실행 |

V2 는 NOT_RUN. 다음 세션 0단계에서 V1 4회차(키 조각 6글자 창·목록 상한 대상)를 1회만 돌리고, 새 결함이 없으면 멈춘다.
판정 원문은 /private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/9ae55d08-927b-4bb6-bdb1-f6cfc6cae32a/scratchpad/codex-v1*.txt (임시 폴더 — 사라질 수 있음).
