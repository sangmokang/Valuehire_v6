/strict

[VALUEHIRE-V6-JEV-GATEWAY → EVIDENCE ASSESSMENT 연결 WU] L3

새 세션(/clear 직후)에서 실행한다. 아래 "확정 사실"은 2026-09-25 22:0x KST 세션의 주장이다.
0단계에서 다시 확인하고, 어긋나면 그 항목을 보고하고 판단이 필요하면 멈춘다.

## 확정 사실 (0단계에서 재확인할 것)

작업 위치
- 워크트리 worktrees/jev-ea-wu1-split, 브랜치 task/jev-evidence-assessment-wu1-split (PR #110, base task/jev-shadow-base-split = PR #109).
- 이번 세션 로컬 커밋(미push): 402c4cb(RED) → d4b3517(GREEN) → 1f32f8a(RED) → f00de09(GREEN) → 이 프롬프트 커밋.
- push·PR 수정·병합·배포는 하지 않았다. 원격 CI 빨간불 원인(억제 만료 2건, #74→#75→#77 체인)은 그대로다.

Jev Gateway smoke — PASS (1회만 호출, 더 호출하지 않음)
- 2026-09-25T13:02:47Z, 합성 입력 1건(요건 "Experience developing backend systems in a high-traffic environment",
  근거 "Developed order APIs and payment systems for a service with 4M MAU."), 실제 후보자·JD 데이터 0.
- 우리 쪽 요청 1회: POST ai-gateway.vercel.sh/typesafe/v1/systemone → HTTP 200, 0.81초, 재시도 0.
- 응답 model "jev", q1 choice SUPPORTED, confidence 0.92, usage 입력 537·출력 67 토큰, 청구 cost "0"(marketCost 0.000022554),
  generationId gen_01M3CAJHTK68KEQTQQVZR4NDXD. 출력 파일에 키 문자열 0회.
- 호출 방식: 저장소 코드 수정 없이 임시 스크립트가 TypeSafeClient(api_key=키체인 값, base_url="https://ai-gateway.vercel.sh/typesafe",
  retry=RetryPolicy(max_retries=0))를 만들어 기존 TypeSafeJevJudge(client=...)에 주입. 즉 **제품 CLI 경로는 아직 Gateway 를 모른다.**
- 이전(12:44:20Z) 1차 호출은 출력 필터 버그로 결과 미관측(0~1회). 추가 승인된 재호출은 이전 세션에서 실행되지 않았다.

새로 드러난 경계 — 결정 필요
- Gateway 가 내부에서 공급자 digitalocean 에 먼저 보냈다가 503 실패 후 typesafe-ai 로 넘겼다
  (routing.planningReasoning: digitalocean(system) → typesafe-ai(system)). 실제 후보자 근거를 보내면 제3 공급자에게도 전달될 수 있다.
- 계약 두 개(contracts/jev-evidence-assessment.json, contracts/jev-org-reference-shadow.json)는 model_version "jev-1.13.0" 고정,
  evidence_assessment.py 는 고정 버전이 아니면 거부(_is_pinned_jev_model). Gateway 의 모델 이름은 "jev" 하나뿐(고정 버전 없음).

안전 결함 — 닫힘(로컬)
- [높음, Codex bjfunadwq] organization_shadow_cli 가 live_calls_allowed 를 보지 않던 문제: REPRODUCED(402c4cb RED 가 EXTERNAL_JEV·요청 1회로 실패)
  → d4b3517 에서 두 CLI 가 같은 저장소 스위치(contracts/jev-evidence-assessment.json)를 읽게 고쳤다.
  f00de09 에서 조직 shadow 출력 경로가 정책 파일이면 거부(V1 결함 1, output_collision).
  검증: 관련 시험 209 passed(f00de09 기준), ruff·mypy(src 22파일) 0, 고장 사본 3종(스위치 삭제·항상 켬·항상 끔) 모두 시험이 잡음,
  실제 CLI 를 가짜 키 + --live-jev 로 실행 → LOCAL_ONLY·요청 0.
- V1(Codex gpt-6-sol, 세션 01a0d8ab-790d-7613-b8a1-6636f3181053): 1차 FAIL(결함 2건) → 결함 1 수정 후 재확인 PASS. V2 는 NOT_RUN.
- [낮음, V1 결함 2 — 미착수] evidence_assessment_cli.main(config=...) 로 넘긴 설정 객체가 저장소 스위치보다 우선(evidence_assessment_cli.py:37,40).
  제품 코드·셸 호출자 0건(시험 도우미 ea_support.py 만 사용). 2단계에서 CLI 를 건드릴 때 시험 먼저: 주입 config 가 true 여도 저장소 false 면 요청 0.
- [중간, Codex bjfunadwq] organization_reference.py:118-125 표본 2명(LIMITED)에서도 B classification=high — 미착수.
- [낮음] 근거 평가 not_run 결과 error_reason None — 미착수.

## 0단계 — 재확인 (수정 없음)
a. 워크트리 HEAD·status, 이 워크트리를 cwd 로 쓰는 다른 세션(lsof -a -d cwd -Fpcn + awk 경로 대조). 있으면 멈춘다.
b. 위 사실을 명령으로 확인해 표로(일치/불일치/확인 불가). 키는 `security find-generic-password -s valuehire-ai-gateway -a sangmokang >/dev/null` 로 존재만.
c. `git grep -n EvidenceAssessmentV1` — 이 이름은 저장소에 없다(2026-09-25 기준). 있으면 그 정의를 정본으로, 없으면
   evidence_assessment.py 의 assess_evidence 출력을 "EvidenceAssessmentV1"로 부르는지 사장님께 한 줄로 확인한다. 새 타입을 만들지 않는다.

## 1단계 — 사장님 결정 2개 (코드 전)
1) 모델 고정 규칙: 계약의 "jev-1.13.0" 을 Gateway 이름 "jev" 로 바꿀지(버전 재현성 약화) / 고정 버전이 나올 때까지 라이브 보류할지.
2) 공급자 경계: 실제 후보자 근거를 보낼 때 Gateway 공급자를 typesafe-ai 하나로 고정할지(공식 문서에서 providerOptions/order·only
   지원 여부를 먼저 확인) / 합성 데이터만 계속 쓸지.
결정 없이는 2단계로 가지 않는다. 스스로 완화하지 않는다.

## 2단계 — 최소 구현 (결정된 범위만, 이 브랜치 위 새 커밋)
- organization_shadow_jev.py: AI_GATEWAY_API_KEY 가 있으면 TypeSafeClient(api_key=그 키, base_url="https://ai-gateway.vercel.sh/typesafe"),
  없으면 기존 동작. 두 CLI 의 키 확인을 두 키 중 하나로 넓힌다. 저장소 live_calls_allowed 는 false 유지.
- 실패 시험 먼저: 키 없음 → LOCAL_ONLY, Gateway 키 → base_url 설정, 스위치 false + Gateway 키 → 요청 0(소켓 차단 포함).
- 결정 1이 "jev" 로 바꾸기면 계약 두 파일과 _is_pinned_jev_model 을 함께, 시험 먼저.
- 금지: 새 모듈·추상화·TypeScript·npm·AI SDK, Supabase, review_candidate, 결정적 점수, 실제 후보자 데이터, push·PR·배포.

## 3단계 — 라이브 1건 (사장님이 이 세션에서 명시 승인한 경우만)
- 합성 입력 1건, 제품 CLI(evidence_assessment_cli --live-jev) 경로로. 스위치를 켜는 방법은 goal 문서
  (docs/engineering/jev-evidence-assessment-wu1-goal-2026-09-23.md) 결론 절 절차 그대로, 끝나면 false 복구.
- 키 가리기는 반드시 호출 프로세스 안에서 하고 결과는 파일에 먼저 쓴다(부모 셸 변수로 grep -v 하지 말 것 — 9/25 1차 호출 유실 원인).
- 성공하면 더 호출하지 않는다. NOT_RUN 기록을 실측 결과로 갱신.

## 보고
§8 3층, 결정 최대 2개, A VERIFIED / B DEFERRED(외부) / C FAILED.
끝나면 다음 프롬프트를 이 폴더에 새 파일로 쓰고 로컬 커밋(push 는 승인 후).

## V1 기록 (원문)

### 1차 (d4b3517 대상)
```text
VERDICT: FAIL

## 결론

현재 변경은 그대로 병합하기 어렵습니다. 저장소에서 외부 요청을 꺼 두어도 증거 평가 명령의 시험용 입력으로 요청 분기를 열 수 있습니다. 조직 검토 명령은 결과 파일의 경로로 정책 파일을 받아들여, 실행 결과로 그 파일을 덮어쓸 수 있습니다.

**검증 한계:** 실제 네트워크 호출과 파일 쓰기는 하지 않았습니다. pytest는 읽기 전용 환경에서 임시 디렉터리를 만들지 못해 시험 수집 전에 종료됐습니다. 이후 메모리 실행으로 재시도했습니다. 원격 검사 상태는 미확인입니다. 마지막 상태 확인에서 처음에는 없던 미추적 문서 1개가 보였으며, 이 검토에서는 만들거나 수정하지 않았습니다.

## 판단 근거

선택한 해석은 “두 명령의 모든 실행 경로가 저장소 정책을 따라야 한다”입니다. 시험용 인자는 운영자가 셸에서 넘기는 옵션은 아니지만, 공개된 `main` 호출 경로이며 실제로 요청 분기를 엽니다. 이를 단지 시험 편의 기능으로 보아 계약에서 제외하면 첫 결함의 범위는 줄어듭니다. 다만 그 해석에서는 다른 코드가 같은 진입점을 호출할 때 저장소의 차단 값이 효력을 잃습니다.

정상 경로가 작동하지 않는다는 해석은 버렸습니다. 현재 정책이 `false`인 상태에서 두 명령 모두 키와 `--live-jev`를 받아도 `LOCAL_ONLY`, 요청 0회였습니다. 정책 파일 읽기에 실패할 때도 요청 없이 오류로 종료됐습니다. 두 모듈을 함께 가져오는 실행에서도 순환 가져오기 오류는 없었습니다.

## 기술 상세와 증거 원문

### 1. 높음 — “조직 검토 결과가 저장소 정책 파일을 덮어쓸 수 있음”

- **원인:** [organization_shadow_cli.py:79](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/organization_shadow_cli.py:79)의 출력 충돌 검사는 입력과 그림자 설정 파일만 비교합니다. 새 정책 경로는 [같은 파일:34](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/organization_shadow_cli.py:34)에 정의되어 있지만 검사 대상에 없습니다. [같은 파일:92](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/organization_shadow_cli.py:92)는 그 경로로 결과를 쓰며, [같은 파일:405](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/organization_shadow_cli.py:405)는 실제 파일 교체 지점입니다.
- **사업 영향:** 이후 실행에서 정책 파일을 읽지 못해 평가 업무가 중단될 수 있습니다. 계약 파일 값을 변경하지 말라는 범위도 지키지 못합니다.

아래 명령은 쓰기 함수를 메모리 수집으로 바꾸고, 가상 입력을 사용해 분기를 재현합니다. `humansearch` 폴더에서 실행합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests .venv/bin/python -B -c '
import json
from pathlib import Path
from unittest.mock import patch
from humansearch import organization_shadow_cli as cli
from test_organization_shadow_cli import CONFIG, synthetic_payload
original = Path.read_text
def read(path, *args, **kwargs):
    return json.dumps(synthetic_payload()) if str(path) == "/virtual/input.json" else original(path, *args, **kwargs)
writes = []
with patch.object(Path, "read_text", read), patch.object(cli, "_write_atomic", lambda path, data: writes.append((path, data))):
    result = cli.main(["--input", "/virtual/input.json", "--output", str(cli.LIVE_POLICY_PATH), "--config", str(CONFIG)])
print(result, writes[0][0], "live_calls_allowed" in writes[0][1])
'
```

실행 결과 원문:

```text
0 /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/contracts/jev-evidence-assessment.json False
```

→ 해석: 명령이 성공으로 끝나며 정책 파일을 출력 대상으로 넘깁니다. 쓰려던 결과에는 정책 필드가 없으므로 실제 쓰기가 허용되면 계약 파일 형식이 깨집니다.

### 2. 중간 — “시험용 설정 입력이 저장소의 요청 금지를 우회함”

- **원인:** [evidence_assessment_cli.py:37](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/evidence_assessment_cli.py:37)은 직접 전달된 `config`를 파일 검사보다 우선합니다. [같은 파일:40](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/evidence_assessment_cli.py:40)은 그 값으로 요청 허용 여부를 결정합니다. 시험 도우미 [ea_support.py:148](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/tests/ea_support.py:148)는 저장소의 `false`를 `true`로 바꾸고, 기존 시험 [test_evidence_assessment_live.py:63](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/tests/test_evidence_assessment_live.py:63)은 이 경로에서 클라이언트 생성을 기대합니다.
- **사업 영향:** `main`을 호출하는 다른 코드가 설정 객체를 넘기면 저장소의 차단 결정과 달리 외부 요청을 시도하고 `EXTERNAL_JEV`를 기록합니다. 셸의 `--config` 파일 경로는 별도 검사로 막혀 있어 이 결함의 범위에는 포함하지 않았습니다.

메모리 실행에서는 가짜 클라이언트와 가짜 출력 함수를 사용하고 소켓 연결도 차단했습니다. 실행 결과 원문:

```text
EA_INJECTED rc 0 built [1] attempted [1] delivery EXTERNAL_JEV count 1
```

→ 해석: 저장소 파일은 `false`인데도 `main(..., config=live_config())`가 클라이언트를 만들고 요청 분기를 1회 실행했습니다. 실제 네트워크 요청이 나갔다는 주장은 아닙니다.

### 반증 기록과 재시도

```text
EA_DEFAULT 0 LOCAL_ONLY 0
SHADOW_DEFAULT 0 LOCAL_ONLY 0
MISSING_POLICY 2 {"delivery_status": "LOCAL_ONLY", "error_code": "invalid_input_or_config", "ok": false, "request_attempts": 0}
```

→ 해석: 키와 `--live-jev`만으로는 두 명령 모두 요청하지 않았습니다. 정책 파일 읽기 실패도 요청 허용으로 바뀌지 않았습니다. 조직 명령의 새 차단 시험 [test_organization_shadow_cli.py:187](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/tests/test_organization_shadow_cli.py:187)은 실제 차단 경로를 검사하므로, 그 시험 자체를 가짜 통과로 판정하지 않았습니다.

```text
FileNotFoundError: [Errno 2] No usable temporary directory found
```

→ 해석: `.venv/bin/python -m pytest -p no:cacheprovider tests/test_organization_shadow_cli.py tests/test_evidence_assessment_live.py -q`는 시험 실행 전에 종료됐습니다. 따라서 전체 시험 통과는 주장하지 않습니다.

**설계 지적**

- **무엇을:** 두 명령의 모든 요청 허용 판단과 출력 충돌 검사에 저장소 정책 파일을 포함해야 합니다.
- **왜:** 현재는 호출 방식에 따라 요청 허용 값이 달라지고, 출력 경로가 정책 자체를 손상할 수 있습니다.
- **버린 길:** 시험용 설정 객체를 운영 경로의 예외로 계속 인정하는 방식은 동일한 `main` 진입점의 보장을 약하게 합니다.
- **대가:** 허용 정책을 시험하는 방법은 저장소 파일을 건드리지 않는 별도 시험 경계가 필요합니다.
- **되돌리기:** 작은 경계 변경으로 제한하고, 두 명령의 차단·허용·정책 파일 충돌 사례를 다시 검증할 수 있습니다.```

### 2차 재확인 (f00de09 대상, 같은 세션 resume)
```text
VERDICT: PASS

## 결론

이번 변경분에서 **정책 파일 덮어쓰기 결함은 닫혔습니다.** 이전 재현 명령을 그대로 다시 실행하자 성공 대신 종료값 2와 `output_collision`이 나왔습니다. 추가 확인에서도 파일 쓰기 함수는 0회 호출됐습니다.

건너뜀·미확인: 이 읽기 전용 환경에서는 pytest가 임시 디렉터리를 만들지 못해 실행할 수 없었습니다. 실제 파일 교체와 네트워크 호출은 하지 않았습니다. 대신 이전 재현을 다시 실행하고 쓰기 횟수를 메모리에서 확인했습니다. `main(config=)` 문제는 요청대로 이번 판정에서 제외했습니다.

## 판단 근거

조직 검토 명령의 출력 경로 검사에 저장소 정책 파일이 추가된 점과, **동일한 재현 입력이 이제 쓰기 전에 거절된 결과**를 근거로 통과 판정했습니다. 시험 코드만 바뀌었다는 해석은 버렸습니다. 실제 명령 처리 코드도 바뀌었고, 이전에는 종료값 0이던 재현이 종료값 2로 바뀌었습니다. 이 판단이 틀리면 정책 파일을 출력으로 지정했을 때 쓰기 함수가 호출되어야 하지만, 계측 결과는 0회였습니다.

남은 `main(config=)` 우회는 시험 코드에서 재현되지만, 추적 중인 제품 코드와 셸 스크립트에서 호출자 0건을 확인했습니다. 따라서 현재 **운영 노출 심각도는 낮음**으로 낮추고 다음 작업으로 넘기는 판단이 적절합니다. 동적 호출이나 저장소 밖 호출자는 확인하지 못했습니다.

## 기술 상세와 증거 원문

### 닫힘 · 이전 심각도 높음 — “조직 검토 결과가 저장소 정책 파일을 덮어쓸 수 있음”

- **원인과 수정:** [organization_shadow_cli.py:79](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/organization_shadow_cli.py:79)의 출력 충돌 검사에 `LIVE_POLICY_PATH`가 추가됐습니다. [test_organization_shadow_cli.py:212](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/tests/test_organization_shadow_cli.py:212)는 정책 파일 사본을 출력으로 지정했을 때 거절되고 내용이 보존되는지 검사합니다.
- **사업 영향:** 확인한 경로에서는 명령 결과가 저장소의 요청 허용 정책을 손상시키지 않습니다.

이전 답변에 적은 재현 명령을 **수정 없이** 다시 실행한 원문입니다.

```text
종료값: 2
{"delivery_status": "LOCAL_ONLY", "error_code": "output_collision", "ok": false, "request_attempts": 0}
```

→ 해석: 이전의 종료값 0·정책 파일 출력 선택이 쓰기 전에 거절됐습니다. 같은 입력에서 출력 대상이 정책 파일인 경우를 확인한 결과입니다.

쓰기 함수를 메모리 계측으로 바꾼 추가 실행 결과입니다.

```text
EXIT 2 WRITE_CALLS 0 ERROR output_collision
SAME_FILE_REAL True
SAME_FILE_NORMALIZED True
```

→ 해석: 실제 경로와 `..`가 포함된 동일 경로 모두 충돌로 인식하며, 쓰기 함수 호출은 없었습니다.

### 범위 밖 · 심각도 낮음으로 갱신 — “시험용 설정 입력이 저장소의 요청 금지를 우회함”

- **원인:** [evidence_assessment_cli.py:37](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/src/humansearch/evidence_assessment_cli.py:37)의 직접 전달된 `config`가 저장소 파일보다 우선합니다. 이 동작은 이번 두 커밋에서 변경되지 않았습니다.
- **사업 영향:** 현재 확인된 사용자는 [ea_support.py:140](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split/humansearch/tests/ea_support.py:140)의 시험 도우미입니다. 제품 코드나 셸 호출에서 같은 주입 경로를 쓰는 증거는 없으므로 당장의 운영 노출은 낮습니다. 후속 작업에서 계약 보장은 여전히 다뤄야 합니다.

추적 파일을 검색하는 `git grep` 실행 결과입니다.

```text
$ git grep -n -E 'evidence_assessment_cli\.main\(|python[0-9 ]* -m humansearch\.evidence_assessment_cli|main\(.*config[[:space:]]*=' -- humansearch/src scripts
종료값: 1
일치 항목: 0건
```

→ 해석: 검색한 제품 코드와 셸 스크립트에는 해당 호출자가 없습니다. 시험 코드의 `cli.main(argv, config=cfg)` 호출은 별도로 확인했습니다.

**설계 판단**

- **무엇을:** 정책 파일을 출력 충돌 대상에 포함한 수정은 유지합니다.
- **왜:** 실제 출력 쓰기 전에 정책 파일 경로를 거절합니다.
- **버린 길:** 시험 통과만으로 닫혔다고 보는 해석은 동일 재현 실행 결과가 있어 채택하지 않았습니다.
- **대가:** `main(config=)`의 저장소 정책 우회는 후속 작업으로 남습니다.
- **되돌리기:** 이번 한 줄을 제거하면 이전 재현이 다시 성공하므로 보호가 사라집니다.

현재 HEAD는 `f00de09`입니다. 검토 중 코드 수정은 하지 않았습니다.```
