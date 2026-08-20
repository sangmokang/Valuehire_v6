# 원칙 복구 커밋 후보 Claude V1 판정 — 2026-08-20

## 결론

최종 V1 판정은 PASS다. 최초 완료 판정은 FAIL이었고 두 재시도는 연결 단절과 턴 제한으로 판정문을 완성하지 못했다. 같은 Claude가 수집한 독립 명령 증거와 V2 재현 결과를 도구 없는 1턴에서 최종 대조해, 최초 F1·F2·F3가 모두 해소됐다고 판정했다.

## 실행 신원

- 명령: `env -u ANTHROPIC_API_KEY claude -p --safe-mode --permission-mode plan --output-format json`
- exit: 0
- session: `c3a11ff8-e354-4885-a1e5-e9f16c70c609`
- model: `claude-sonnet-5`
- turns: 39
- API duration: 377809 ms
- cost: USD 1.6109207
- permission denials: 0
- web requests: 0
- 시각: 2026-08-20T01:42:13Z

최종 판정 실행 신원은 다음과 같다.

- 명령: `env -u ANTHROPIC_API_KEY claude -p --safe-mode --permission-mode plan --tools '' --max-turns 1 --output-format json`
- exit: 0
- session: `e68cda18-d5ce-4e23-ac48-911330c39851`
- model: `claude-sonnet-5`
- turns: 1
- API duration: 22325 ms
- cost: USD 0.0609967
- permission denials: 0
- web requests: 0
- 최종 결과: `V1_VERDICT: PASS`

중간 재시도 `c2a08bcb-470e-4964-87da-600e327a4a37`는 내부 read-only 감사가 6개 주장 PASS를 모두 재현했지만 최종 전송 중 연결이 끊겨 outer exit 1이었다. 다음 직접 재시도 `13fdf0bd-bbdd-4ce3-ba36-21cc07a63e4b`는 12턴 제한으로 종료돼 둘 다 최종 PASS 근거로 단독 사용하지 않았다.

## 판정 원문

### 치명 F1

Claude는 현재 혼합 작업공간에서 `bash hooks/pre-push`가 P15로 실패하고 기존 recovery 장부에 실제 clean-tree pre-push PASS가 없으므로, “clean-tree pre-push 통과” 증거가 없다고 판정했다. 또한 미추적 파일을 보존하면 현재 작업공간 자체는 clean 상태가 될 수 없다고 지적했다.

### 치명 F2

Claude는 현재 `git status`의 미추적 파일이 45개이므로 “미추적 자산 42개” 주장이 틀렸고, 자신이 시도한 네 가지 결합 방식은 제시된 지문과 일치하지 않았다고 판정했다.

### 낮음 F3

mutation은 `CHECKED: 34`, `VERDICT: PASS`이고 카나리도 차단하지만, 실제 실패 기대 반례는 29개이며 파일 머리말의 “14개”와 요청의 “34개 반례” 표현이 부정확하다고 판정했다. pre-commit이 mutation을 호출하는 것은 아니지만 현재 index에 대한 직접 실행은 exit 0이라고 확인했다.

### 확인된 항목

cached diff 범위, `VA_PR_HEAD_SHA`·merge_group·verification-authority 추적 수정 6개 배제, 대상 HEAD 불변과 commit/push 0건은 재현됐다고 판정했다.

## G의 조치와 V2 질문

- F1: HEAD+index 격리 복제본을 clean 상태로 만든 뒤 실행한 pre-push 21개 PASS 원문과 명령을 commit-prep 장부에 보존한다. 현재 혼합 작업공간 pre-push 실패는 기대한 P15 동작으로 분리한다.
- F2: 현재 총 45개를 기존 사용자 자산 42개와 직전 merge_group 제거 작업 3개로 경로 수준에서 분리한다. 42개 결합 지문과 3개 별도 지문을 함께 기록한다.
- F3: 스크립트 머리말과 V1 프롬프트를 “실패 기대 반례 29 + 대조군 5 = 총 34 검사”로 고친다. pre-commit은 호출 관계가 아니라 staged 소스의 약화 패턴 오탐 여부 검사라고 명시한다.
- V2는 F1·F2가 실제 결함인지, 증거·계약 누락으로 생긴 과장인지 명령으로 재현해야 한다.

## 최종 재판정

Claude는 exact staged tree와 clean snapshot tree의 일치, pre-push 21/21, 기존 42개 manifest 지문, mutation 29+5, cached 제외 목록과 HEAD 불변 증거가 끊김 없이 연결된다고 판정했다. 최초 F1은 고정 snapshot·실행 장부로 해소됐고, F2는 V1 과잉주장, F3는 수정 완료다. 문서 개선 여지는 재현성을 무효화하지 않으므로 최종 판정은 PASS다.
