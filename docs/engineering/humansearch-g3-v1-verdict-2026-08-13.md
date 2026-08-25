VERDICT G3: FAIL

# 결론

이 변경은 지금 합치시면 안 됩니다. 서버 검사를 아예 실행하지 않으면서도 정상으로 인정되게 하는 방법과, 실제 제품 파일 안의 주소·화면 위치 값이 그대로 통과하는 방법을 확인했습니다.

현재 버전은 깨끗했고 흔한 정상 값과 기본 위반 값은 대체로 구분했습니다. 그러나 새 제품 폴더, 여러 일반적인 작성 방식, 일부 고장 상황을 놓칩니다.

이번 환경은 파일 쓰기를 막아 별도 복사본과 처음부터 끝까지의 전체 실행을 하지 못했습니다. 실제 서버 실행도 확인하지 못했으며, 판정 파일 쓰기도 거부되어 아래 전문을 화면에 남깁니다.

결정 사항은 하나입니다. 아래 치명·높음 결함을 고치고 쓰기 가능한 격리 환경에서 전체 시험을 다시 실행하기 전에는 PR #13을 병합하지 마십시오.

# 판단 근거

## 확인 범위와 한계

- [확인] 대상은 `task/humansearch-g3-portal-constants`, HEAD `f10c8c4e3ceee7f9095c3bd74009434aae823855`, 기준 `main` `682f00e981dc2e23515dbdd0b1b3f807a48daa3b`였습니다.
- [확인] 시작과 종료 때 대상 작업 공간은 모두 깨끗했습니다. 파일을 바꾸는 실험은 한 번도 실행하지 않았으므로 원복할 변조도 없었습니다.
- [확인] `worktrees/humansearch-clean-room-plan` 등 금지된 다른 작업 공간에는 접근하지 않았습니다.
- [확인] macOS 기본 Bash 3.2(= 이 저장소가 실제로 쓰는 셸 프로그램 버전)는 여섯 파일의 문법을 모두 받아들였습니다.
- [확인] 실제 금지 패턴, 개수 판정 구간, 서버 설정 판독 함수, 로컬 업로드 직전 검사 자기점검 조건은 파일 생성 없이 그대로 실행했습니다.
- ※ `/private/tmp` 격리 복제본은 쓰기 정책 때문에 생성하지 못했습니다. 따라서 검사기와 다섯 시험 파일의 처음부터 끝까지 전체 실행은 확인하지 못했습니다.
- ※ GitHub의 실제 CI(= GitHub 서버가 파일을 받아 자동으로 검사하는 절차) 실행 기록과 PR 라벨은 확인하지 못했습니다.
- [재시도] 셸의 임시 파일을 쓰는 입력 방식이 차단되어 메모리 문자열 실행으로 바꿨습니다.
- [재시도] 실제 판정 구간을 `source`로 읽은 첫 시도는 macOS Bash가 내용을 실행하지 않아 잘못된 0을 냈습니다. 그 결과는 폐기하고 같은 줄을 `eval`로 실행해 정상 결과를 얻었습니다.
- [재시도] 서버 설정 입력을 `/dev/fd`로 전달한 한 시도는 `awk`가 파일을 열지 못했습니다. 그 결과는 폐기하고 표준입력으로 다시 실행했습니다.
- [확인] 판정 파일 쓰기는 `read-only sandbox` 정책으로 거부됐습니다. 따라서 개인용 형식 검사도 실행할 파일이 없어 ※ 미실행입니다.

## 왜 FAIL인가

현재 `.github/workflows/verify.yml`에는 G3 실행 줄 여섯 개가 조건 없이 들어 있습니다. 이것만 보면 정상입니다.

그러나 요구사항은 현재 줄의 존재뿐 아니라 그 줄을 주석, 거짓 조건, 오류 무시 등으로 무력화했을 때 검사기가 거부하는 것까지 포함합니다. YAML(= GitHub 작업 설정을 적는 구조화된 문서 형식)에서 같은 의미를 따옴표나 작업 전체 조건으로 표현하자 검사기는 정상으로 오인했습니다.

정규식(= 특정 문자 모양을 찾는 검색 규칙)도 흔한 입력은 잡았습니다. 하지만 셀렉터(selector, 화면에서 버튼·입력칸 같은 요소를 찾는 표현)를 JavaScript식 이름, 공백, 단순 클래스, 분할 문자열로 적으면 놓쳤고, 주소도 분할·인코딩·미등재 도메인으로 적으면 놓쳤습니다.

“현재 제품 파일은 두 경로뿐이므로 충분하다”는 해석은 버렸습니다. 직접 요구와 반대 사례가 `humansearch/cli/` 같은 새 제품 경로를 명시했고, 실행 결과 그 경로에는 제품 전용 규칙이 적용되지 않았습니다.

“구현 문서가 이 한계를 비범위라고 선언했으므로 결함이 아니다”라는 해석도 버렸습니다. 상위 요구는 제품 파일 어디에도 운영값을 두지 못하게 하라고 했고, 같은 goal 문서의 반대 합격 사례도 새 제품 경로의 조용한 누락을 금지합니다.

이 판정이 틀리면 다음이 깨집니다.

- 서버 검사가 실제로 실행되지 않아도 병합 화면은 정상으로 보일 수 있습니다.
- 새 제품 폴더에 주소·포트·화면 위치가 들어가도 검사가 초록으로 끝날 수 있습니다.
- 검사 자체가 고장 난 상황을 정책 위반으로 잘못 분류하여 자동화가 잘못 대응할 수 있습니다.
- “각 규칙을 일부러 죽여도 시험이 잡는다”는 보고를 믿고 실제 미탐을 놓칠 수 있습니다.

## 결함 요약

| ID | 판정 | 위치 | 그대로 두면 생기는 일 |
|---|---|---|---|
| D1 | 치명 | `scripts/acceptance-hs-portal-constants.sh:188-243` — 서버 실행 줄을 텍스트로 판독하는 부분 | 서버 검사를 실행하지 않는 설정이 정상으로 인정될 수 있습니다. |
| D2 | 높음 | `scripts/acceptance-hs-portal-constants.sh:257-267` — 로컬 업로드 직전 검사의 생존 여부를 확인하는 부분 | 개발자 컴퓨터의 사전 차단을 꺼도 검사기가 온전하다고 보고합니다. |
| D3 | 높음 | `scripts/acceptance-hs-portal-constants.sh:31,143-150` — 제품 경로를 두 곳으로 고정하는 부분 | 새 제품 폴더에 운영 주소를 넣어도 제품 검사를 받지 않습니다. |
| D4 | 높음 | 전역 패턴 `:10-25`, 제품 패턴 `:22-32` — 화면 찾기 표현을 열거한 부분 | 일반적인 JavaScript·Selenium·공백·단순 클래스 표현이 통과합니다. |
| D5 | 높음 | 제품 패턴 `:7-20` — 주소·도메인·호스트와 포트를 찾는 부분 | 분할·인코딩 주소와 목록에 없는 정상 도메인이 통과합니다. |
| D6 | 높음 | `docs/sot/coding-principles.md:26` — 변경량 3,000줄 초과를 금지하는 원칙 | 이번 변경 4,332줄은 저장소 자체 병합 기준을 넘습니다. |
| D7 | 중간 | mutation 파일들 `:80-116` 및 mutation 본체 `:158` — 원본 규칙을 복사하고 같은 두 제품 경로를 다시 세는 부분 | 시험과 구현이 같은 가정을 공유해 새 경로 누락 같은 결함이 함께 초록이 됩니다. |
| D8 | 중간 | 검사기 `:107-153,165-166` — 파일 정보와 G3 목록을 읽는 부분 | 읽기 실패가 약속한 검사 불능 2가 아니라 위반 1로 끝납니다. |
| D9 | 중간 | 검사기 `:129-138` — 일반 문서 다섯 형식을 통째로 건너뛰는 부분 | “저장소 전체” 규칙과 달리 문서 안의 화면 찾기·포털 주소는 검사되지 않습니다. |
| D10 | 낮음 | 제품 패턴 `:17,19` — 숫자 주소와 포트를 찾는 두 규칙 | 17행을 지워도 19행이 같은 값을 잡아 규칙별 고장 시험이 독립적으로 빨개질 수 없습니다. |
| D11 | 낮음 | goal 문서 172개 행과 마지막 빈 줄 | 기본 변경 검사 명령이 실패해 불필요한 검토 잡음이 생깁니다. |

→ 가장 중요한 사실은 D1·D3·D4·D5입니다. 현재 설정이 정상이라는 사실은 확인했지만, 보호 장치가 스스로 약화되는 것을 막지 못하고 실제 금지값도 여러 형태로 놓칩니다.

# 설계 결정 검토

## 서버 설정을 텍스트 줄로 읽는 결정

**무엇을** — GitHub 작업 설정을 구조로 읽지 않고 들여쓰기와 몇 개 문자열로 판정합니다.
**왜** — 새 부품을 추가하지 않고 기본 `awk`만으로 검사하려는 선택입니다.
**버린 대안** — 설정을 구조적으로 읽어 실제 작업·단계·실행 칸·조건을 구분하는 방법을 채택하지 않았습니다.
**대가** — 따옴표 붙은 키, 작업 전체 조건, 실행 시점 설정 같은 동등한 표현이 계속 새 우회가 됩니다.
**되돌리는 법** — 구조 판독기나 저장소의 단일 G3 진입 스크립트를 두고, 실제 서버 실행 결과를 독립적으로 확인해야 합니다.

## 제품 경로를 두 곳으로 고정한 결정

**무엇을** — 제품 파일을 `humansearch/src/`와 `humansearch/tests/`로 고정했습니다.
**왜** — 현재 제품 파일이 그 두 곳에만 있어 간단히 하한을 세울 수 있기 때문입니다.
**버린 대안** — 제품 경계를 저장소 계약 파일에 선언하거나 패키지 구조에서 자동으로 찾는 방법을 후속 과제로 미뤘습니다.
**대가** — `humansearch/cli/` 같은 새 경로는 별도 공지 없이 일반 파일로 취급되어 모든 일반 주소가 통과합니다.
**되돌리는 법** — 제품 루트 목록을 저장소 계약으로 승격하고, 새 `humansearch/*` 코드 경로가 생기면 미등록 경로로 거부하도록 바꿔야 합니다.

## 문자 모양만으로 운영값을 찾는 결정

**무엇을** — 주소·도메인·화면 위치를 미리 적은 문자 모양으로 찾습니다.
**왜** — 언어별 분석기 없이 빠르게 전 파일을 검사할 수 있기 때문입니다.
**버린 대안** — 제품이 계약 로더 외에는 주소·포트·화면 위치를 만들지 못하게 구조적으로 제한하는 방식을 채택하지 않았습니다.
**대가** — 문자열 분할·인코딩·다른 API 철자·CSS 이스케이프처럼 실행 시 같은 값이 되는 표현을 놓칩니다.
**되돌리는 법** — 계약 로더 호출만 허용하는 구조 검사와 언어별 정적 검사를 함께 두고, 단순 문자 검색은 보조 장치로 낮춰야 합니다.

## 시험 저장소에 원본 규칙을 그대로 복사하는 결정

**무엇을** — 매 사례마다 현재 검사기와 패턴 파일을 그대로 복사한 뒤 입력값만 바꿉니다.
**왜** — 알려진 금지·허용 사례의 회귀를 빠르게 반복할 수 있기 때문입니다.
**버린 대안** — 패턴 한 줄, 경로 분기, 개수 하한, 서버 판독 조건을 각각 제거해 시험이 실제로 실패하는지 확인하는 방식을 채택하지 않았습니다.
**대가** — 구현과 시험이 같은 경로 목록과 범주 가정을 공유해 같은 결함을 함께 놓칩니다.
**되돌리는 법** — 규칙별 제거 시험과 독립 제품 경로 열거를 추가하고, 제거 후 해당 시험이 반드시 실패하는지 확인해야 합니다.

# 요구사항별 판정

종료값(exit code, 프로그램이 끝나며 남기는 숫자)은 이 검사에서 0=정상, 1=위반, 2=검사 불능을 뜻합니다. 카나리(= 검사 여부를 확인하려고 일부러 넣는 가짜 금지값)는 파일 쓰기 없이 실제 패턴 입력으로 실행했습니다.

| 번호 | 무엇을 어떻게 확인했나 | 판정 |
|---|---|---|
| 1 | 기존 정당한 파일 3개와 정상 카나리 7종을 실제 두 패턴에 입력했습니다. 정당한 파일은 전역 규칙에 걸리지 않았고 정상 카나리는 맞는 계층에서 잡혔지만 우회 9종을 찾았습니다. | 부분 충족 / 반례 발견 |
| 2 | 현재 서버 설정 여섯 줄과 판독 함수를 확인하고 주석·echo·후미 성공·일반 `if:false`를 넣었습니다. 이 네 종류는 잡았지만 따옴표·공백 키, 작업 전체 조건·오류 무시, 수동 실행 전용 변경은 놓쳤습니다. | 불일치 |
| 3 | 실제 판정 구간을 0·1·하한 미달·정상 최소치로 실행했습니다. 하한은 돌지만 같은 수의 안전한 파일 교체는 구분하지 못합니다. | 하한 충족, 개체 교체는 한계 |
| 4 | 설정된 제품 경로가 없을 때 실제 경로 검사 구간은 2였습니다. 그러나 새 `humansearch/cli/`는 일반 파일 계층만 타고 URL을 놓쳤습니다. | 불일치 |
| 5 | 기존 시험 소스와 규칙별 제거 실험을 대조했습니다. 기존 시험은 검사 규칙을 제거하지 않고 원본을 복사하며, 자체 제품 수 대조도 같은 두 경로를 반복합니다. | 검증 불충분 |
| 6 | 여섯 G3 파일 자체를 전역 규칙으로 검사하고 가상으로 셀렉터를 덧붙였습니다. 현재는 자기 일치가 없고 덧붙인 값은 잡혀 파일명 면제가 아님을 확인했습니다. | 충족 |
| 7 | 누락·빈 패턴과 임시 공간 실패는 2, 위반과 배선 훼손은 1, 정상 최소치는 0이었습니다. 파일 정보·G3 목록 읽기 실패는 1이 새어 나왔습니다. | 부분 충족 / 계약 위반 |
| 8 | 실제 `/bin/bash` 3.2.57로 여섯 파일을 `bash -n` 검사하고 금지된 신문법을 검색했습니다. 문법은 모두 통과했지만 전체 실행은 쓰기 차단 때문에 ※ 미확인입니다. | 문법 확인, 전체 실행 미확인 |
| 9 | 대문자, 공백, JavaScript·Selenium 표기, 단순 클래스, 분할·인코딩 URL, 미등재 도메인, 분할 XPath를 입력했습니다. 대문자와 괄호 URL만 잡고 나머지를 놓쳤습니다. | 실패 |

→ 9개 중 완전 충족으로 판단한 것은 자기검사 한 항목뿐입니다. Bash 문법과 기본 계층 분리는 긍정적이지만, 합격의 핵심인 서버 무력화 방지와 모든 제품 운영값 차단에 반례가 있습니다.

## goal 문서의 반대 합격 사례 11개

goal에는 현재 9개가 아니라 `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:55-66`에 11개가 적혀 있어 11개 모두를 기준으로 삼았습니다. 해당 줄들은 가짜 합격 모습을 열거합니다.

| 사례 | 판정 | 근거 |
|---|---|---|
| 1. 서버 등록 없음 | 현재 등록은 있음 | `verify.yml:48-58` |
| 2. 제품 가짜 값 미탐 | 실패 | 여러 직접 표현·분할·인코딩 값 미탐 |
| 3. 검사 대상 0개인데 0 | 방어 확인 | 실제 판정 꼬리에서 2 |
| 4. 서버 줄 무력화 | 실패 | 따옴표·공백 키, 작업 전체 조건·오류 무시, 실행 계기 변경 통과 |
| 5. 존재하지 않는 제품 루트 조용한 건너뜀 | 설정된 루트는 방어, 새 루트는 실패 | 미등록 `humansearch/cli/` 누락 |
| 6. 검사기·scripts·contracts 통 면제 | 검사기와 scripts 자기면제 없음 | 현재 파일 6개 전역 검사, 가상 삽입 적중 |
| 7. contracts 정당 값 오탐 | 방어 확인 | 루트 contracts는 구역 규칙만 적용 |
| 8. 무관 파일로 제품 수 부풀림 | 현재 값은 방어 | 독립 제품 수 2와 보고 경로 수 2 일치 |
| 9. 깨진·빈 규칙을 위반 없음으로 오해 | 주 경로 방어 | 검색 엔진 결과 2·0을 코드가 2로 변환 |
| 10. 고정 시험 파일명만 겨냥 | 기존 경로 안에서는 방어 | 무작위 이름·깊은 경로 시험 존재, 단 제품 루트 자체는 고정 |
| 11. 2·127을 차단 성공으로 계산 | 소스상 방어 | `want`와 정확히 같아야 성공, 다만 전체 시험은 ※ 미실행 |

→ goal의 자기 기준으로도 2·4·5가 실패하고 10은 제품 경로 고정 때문에 부분 충족입니다.

# 결함 상세

## D1 — [치명] 서버 검사를 실행하지 않는 설정을 정상으로 인정합니다

`scripts/acceptance-hs-portal-constants.sh:188-243`은 서버 작업의 실제 구조가 아니라 줄의 들여쓰기와 문자열을 판정합니다. `:219`는 `- `로 시작하는 줄을 단계 경계로 보고, `:222`는 정확한 `run: |`만 실행 칸으로 보며, `:232`는 따옴표 없는 `if:`와 `continue-on-error`만 조건으로 인식합니다.

실행 결과:

```text
baseline => ci_line_ok=0
step_if_false => ci_line_ok=1
step_continue => ci_line_ok=1
quoted_step_if_false => ci_line_ok=0
quoted_step_continue => ci_line_ok=0
job_if_false => ci_line_ok=0
job_continue => ci_line_ok=0
manual_trigger => ci_line_ok=0
YAML_KEY_CHECK
["name", "if", "run"]
["if", "runs-on", "steps"]
```

→ 뭘 시켰나: 검사기의 실제 `ci_line_ok` 함수에 정상·단계 조건·따옴표 조건·작업 전체 조건·오류 무시·수동 실행 전용 설정을 넣었습니다.
→ 뭐가 나왔나: 1은 거부, 0은 정상 인정입니다. 정상 표기의 단계 조건은 거부했지만 동등한 따옴표 키와 작업 전체 무력화는 정상으로 인정했습니다.
→ 나쁜 소식입니다. 로컬 YAML 해석기도 따옴표 키를 실제 `if`로 읽었습니다.

일반 변형은 다음처럼 잡혔습니다.

```text
commented => ci_line_ok=1
echo_prefixed => ci_line_ok=1
suffixed => ci_line_ok=1
spaced_step_if_false => ci_line_ok=0
YAML_SPACED_KEY_CHECK
{"name"=>"g3", "if"=>false, "run"=>"bash scripts/acceptance-hs-portal-constants-hardening.sh\nbash scripts/acceptance-hs-portal-constants-hardening2.sh\nbash scripts/acceptance-hs-portal-constants-hardening3.sh\nbash scripts/acceptance-hs-portal-constants-hardening4.sh\nbash scripts/acceptance-hs-portal-constants-mutations.sh\nbash scripts/acceptance-hs-portal-constants.sh\n"}
```

→ 뭘 시켰나: 주석·echo·뒤에 성공 강제·`if : false`처럼 공백만 바꾼 설정을 넣었습니다.
→ 뭐가 나왔나: 앞의 세 가지는 거부했지만 YAML 해석 결과가 실제 `if=false`인 공백 표기는 정상으로 인정했습니다.
→ 나쁜 소식입니다. counter-AC 4가 완전히 닫히지 않았습니다.

현재 설정 자체는 정상으로 판정됐습니다.

```text
scripts/acceptance-hs-portal-constants-hardening.sh => ci_line_ok=0
scripts/acceptance-hs-portal-constants-hardening2.sh => ci_line_ok=0
scripts/acceptance-hs-portal-constants-hardening3.sh => ci_line_ok=0
scripts/acceptance-hs-portal-constants-hardening4.sh => ci_line_ok=0
scripts/acceptance-hs-portal-constants-mutations.sh => ci_line_ok=0
scripts/acceptance-hs-portal-constants.sh => ci_line_ok=0
```

→ 뭘 시켰나: 현재 `verify.yml`의 여섯 G3 줄을 실제 판독 함수에 넣었습니다.
→ 뭐가 나왔나: 여섯 줄 모두 현재는 정상입니다.
→ 좋은 소식이지만, 위 무력화 반례 때문에 보호 장치의 완결성을 증명하지는 못합니다.

현재 등록 줄은 `verify.yml:48-58`이며 G3 여섯 파일을 조건 없이 실행하는 역할입니다.

## D2 — [높음] 로컬 사전 차단을 여러 방식으로 끌 수 있습니다

`scripts/acceptance-hs-portal-constants.sh:260-266`은 로컬 pre-push(= 파일을 원격에 올리기 직전 자동 실행되는 검사)가 수집 문자열을 포함하는지, 그리고 정확히 `exit 0` 한 줄이 있는지만 봅니다.

실행 반례:

```text
baseline | glob=present plain_exit0=not_detected selfcheck=accepted
exec_true | glob=present plain_exit0=not_detected selfcheck=accepted
exec_true | actual_hook_exit=0
exit_00 | glob=present plain_exit0=not_detected selfcheck=accepted
exit_00 | actual_hook_exit=0
compound_exit | glob=present plain_exit0=not_detected selfcheck=accepted
compound_exit | actual_hook_exit=0
if_false | glob=present plain_exit0=not_detected selfcheck=accepted
if_false | actual_hook_exit=0
```

→ 뭘 시켰나: 실제 자기점검 조건에 `exec true`, `exit 00`, `true; exit 0`, 거짓 조건 안의 검사 수집식을 넣고 같은 훅 본문을 실행했습니다.
→ 뭐가 나왔나: 네 변형 모두 자기점검은 정상으로 인정했고 실제 훅도 아무 검사 없이 0으로 끝났습니다.
→ 나쁜 소식입니다. 최종 권한은 서버에 있더라도 “로컬·서버 양쪽” 요구 중 로컬 절반이 깨집니다.

`hooks/pre-push:112-113`은 이름 규칙으로 검사 파일을 자동 수집하는 글로브(glob, 이름 모양에 맞는 파일을 모두 찾는 방식)를 정의하고, `:165`는 각 파일을 실제 실행합니다. 현재 파일은 정상이나 G3 자기점검이 이 실행 흐름 자체를 보증하지 못합니다.

## D3 — [높음] 새 제품 경로는 조용히 빠집니다

`scripts/acceptance-hs-portal-constants.sh:31`은 제품 경로를 정확히 두 곳으로 고정합니다. `:143-150`은 그 두 접두 경로에만 제품 전용 규칙을 적용하는 부분입니다.

```text
humansearch/src/humansearch/client.py | tier=global-plus-product global=1 product=0 verdict=blocked
humansearch/tests/test_client.py | tier=global-plus-product global=1 product=0 verdict=blocked
humansearch/cli/client.py | tier=global-only global=1 product=not-run verdict=missed
```

→ 뭘 시켰나: 같은 URL을 `src`, `tests`, 새 `cli` 경로로 보내 실제 분기와 두 패턴을 실행했습니다.
→ 뭐가 나왔나: 앞의 두 경로는 제품 규칙이 잡았지만 `humansearch/cli/`에는 제품 규칙이 실행되지 않아 놓쳤습니다.
→ 나쁜 소식입니다. counter-AC 5의 명시적 반례입니다.

설정된 루트가 사라지는 경우는 올바르게 2였습니다.

```text
FAIL: product root missing: /definitely/missing/product-root
configured-missing-root exit=2
humansearch/src exists=yes
humansearch/tests exists=yes
```

→ 뭘 시켰나: 실제 루트 확인 구간에 없는 경로를 넣고 현재 두 경로의 존재도 확인했습니다.
→ 뭐가 나왔나: 등록된 경로가 사라지면 2지만, 등록되지 않은 새 제품 경로는 앞 실험처럼 알 수 없습니다.
→ 절반은 좋은 소식이고 절반은 나쁜 소식입니다.

goal 문서 `:100-101`은 두 경로를 계약으로 고정하고, `:177`은 자동 발견을 후속 과제로 미룹니다. 그러나 같은 문서 `:60`은 존재하지 않는 제품 루트의 조용한 누락을 가짜 합격으로 규정해 상위 목표와 긴장이 있습니다.

## D4 — [높음] 화면 찾기 표현을 여러 일반 표기로 우회할 수 있습니다

실제 패턴 실행 결과에서 0은 적중, 1은 미적중입니다.

```text
LEGEND: 0=pattern matched, 1=no pattern matched
EXPECTED_CANARIES
scheme URL | global=1 product=0 | LOGIN_URL = "https://career-portal.example/login"
bare domain | global=1 product=0 | HOST = "cdn.talent-hub.net"
IPv4 host-port | global=1 product=0 | REMOTE = "10.77.4.9:9444"
CSS id | global=1 product=0 | LOGIN = "#loginBtn"
CSS combinator | global=1 product=0 | LOGIN = ".card > input"
XPath | global=0 product=0 | LOGIN = "//input[@name=\\"email\\"]"
selector API | global=0 product=1 | BTN = page.get_by_role("button")
ADVERSARIAL_BYPASSES
upper-case selector API | global=0 product=1 | BTN = PAGE.LOCATOR(".LOGIN")
space before locator call | global=1 product=1 | BTN = page.locator (".login")
JavaScript camelCase role API | global=1 product=1 | BTN = page.getByRole("button")
Selenium camelCase selector API | global=1 product=1 | BTN = driver.findElement(By.cssSelector, ".login")
simple CSS class literal | global=1 product=1 | LOGIN = ".login"
split XPath | global=1 product=1 | LOGIN = "//" + "input[@name=email]"
CSS escaped id | global=1 product=1 | LOGIN = "#\\6c ogin"
```

→ 뭘 시켰나: 실제 전역·제품 패턴에 정상 예시와 대문자·공백·JavaScript·Selenium·단순 CSS·분할 XPath를 넣었습니다.
→ 뭐가 나왔나: 대문자는 대소문자 무시 검사로 잡았지만 나머지 여섯 직접 표현은 두 계층 모두 놓쳤습니다.
→ 나쁜 소식입니다. “CSS selector·XPath를 실제로 다 잡는다”는 주장은 반증됐습니다.

관련 줄:

- 전역 패턴 `:15`는 `.locator(` 사이에 공백이 없는 형태만 잡습니다.
- 전역 패턴 `:19-25`는 Python식 `get_by_*`만 열거하고 JavaScript식 `getByRole`을 잡지 않습니다.
- 제품 패턴 `:23-28`은 id·결합자·자손·속성형은 잡지만 단순 클래스 `.login`은 잡지 않습니다.
- 제품 패턴 `:31-32`는 연결된 XPath만 잡고 문자열 조립은 잡지 않습니다.

## D5 — [높음] 분할·인코딩 주소와 정상 도메인이 통과합니다

```text
parenthesized URL | global=1 product=0 | URL = ("https://portal.example.com/login")
split URL/domain | global=1 product=1 | URL = "https" + "://" + "portal" + ".example" + ".com"
percent-encoded URL/domain | global=1 product=1 | URL = "https%3A%2F%2Fportal%2Eexample%2Ecom"
unlisted two-label TLD | global=1 product=1 | HOST = "vendor.museum"
spaced host-port | global=1 product=1 | REMOTE = "portal : 8080"
```

→ 뭘 시켰나: 괄호, 분할, 퍼센트 인코딩, 목록 밖 정상 최상위 도메인, 콜론 주변 공백을 실제 패턴에 넣었습니다.
→ 뭐가 나왔나: 괄호로 감싼 정상 URL만 잡았고 나머지는 모두 놓쳤습니다.
→ 나쁜 소식입니다. “모든 URL·도메인·host:port 모양”이라는 계약을 충족하지 않습니다.

제품 패턴 `:10`은 최상위 도메인을 유한 목록으로 적습니다. `:13`의 보완 규칙은 따옴표로 감싼 세 라벨 이상만 잡아 `"vendor.museum"` 같은 두 라벨 정상 도메인을 놓칩니다.

## D6 — [높음] 저장소 자체의 3,000줄 변경 상한을 넘습니다

`docs/sot/coding-principles.md:26`은 PR 변경량 3,000줄 초과를 절대 금지한다고 명시합니다. 이 줄은 두 달 뒤 원인 추적이 불가능해지는 위험을 근거로 듭니다.

```text
12	0	.github/workflows/verify.yml
36	0	contracts/portal-constants-deny-patterns-product.txt
40	0	contracts/portal-constants-deny-patterns.txt
2737	0	docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md
15	14	docs/sot/verification-commands.md
255	0	scripts/acceptance-hs-portal-constants-hardening.sh
225	0	scripts/acceptance-hs-portal-constants-hardening2.sh
203	0	scripts/acceptance-hs-portal-constants-hardening3.sh
159	0	scripts/acceptance-hs-portal-constants-hardening4.sh
312	0	scripts/acceptance-hs-portal-constants-mutations.sh
324	0	scripts/acceptance-hs-portal-constants.sh
TOTAL added=4318 deleted=14 changed=4332
```

→ 뭘 시켰나: 기준 브랜치부터 현재 HEAD까지 파일별 추가·삭제 줄을 Git으로 계산했습니다.
→ 뭐가 나왔나: 총 4,332줄로 저장소 기준 3,000줄보다 1,332줄 많습니다.
→ 나쁜 소식입니다. G3 기능과 별개로 채점 기준상 병합 불가입니다.

## D7 — [중간] 기존 뮤테이션 시험은 규칙을 실제로 죽이지 않습니다

뮤테이션 시험(mutation test, 검사 규칙을 일부러 고장 내고 시험이 실패하는지 보는 방법)은 이름과 달리 대부분 입력값을 바꿉니다.

```text
scripts/acceptance-hs-portal-constants-hardening4.sh:80:  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
scripts/acceptance-hs-portal-constants-hardening4.sh:86:  cp "$GPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
scripts/acceptance-hs-portal-constants-hardening4.sh:87:  cp "$PPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
scripts/acceptance-hs-portal-constants-hardening2.sh:83:  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
scripts/acceptance-hs-portal-constants-hardening2.sh:88:  cp "$GPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
scripts/acceptance-hs-portal-constants-hardening2.sh:89:  cp "$PPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
scripts/acceptance-hs-portal-constants-hardening3.sh:97:  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
scripts/acceptance-hs-portal-constants-hardening3.sh:103:  cp "$GPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
scripts/acceptance-hs-portal-constants-hardening3.sh:104:  cp "$PPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
scripts/acceptance-hs-portal-constants-hardening.sh:85:  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
scripts/acceptance-hs-portal-constants-hardening.sh:88:  cp "$GPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
scripts/acceptance-hs-portal-constants-hardening.sh:89:  cp "$PPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
scripts/acceptance-hs-portal-constants-mutations.sh:99:  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
scripts/acceptance-hs-portal-constants-mutations.sh:102:  cp "$GPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
scripts/acceptance-hs-portal-constants-mutations.sh:103:  cp "$PPAT" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
scripts/acceptance-hs-portal-constants-mutations.sh:158:ind=$( (cd "$CASE_DIR" && find humansearch/src humansearch/tests -type f | wc -l | tr -d ' ') )
```

→ 뭘 확인했나: 다섯 시험 파일이 검사기·패턴을 어떻게 준비하고 제품 수를 무엇으로 독립 계산하는지 검색했습니다.
→ 뭐가 나왔나: 원본 규칙을 그대로 복사하고 구현과 동일한 두 제품 경로를 다시 사용합니다. 규칙 한 줄을 제거하는 시험은 없었습니다.
→ 나쁜 소식입니다. 새 제품 경로 누락처럼 구현과 시험이 공유하는 가정은 잡지 못합니다.

패턴 41개를 메모리에서 한 줄씩 제외한 결과입니다. `full=0`은 원본에서 적중, `without-own-line=1`은 그 줄을 빼자 미적중입니다.

```text
contracts/portal-constants-deny-patterns.txt:10 | querySelector | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:11 | getElementsBy | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:12 | getElementById | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:13 | CSS_SELECTOR | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:14 | find_element | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:15 | locator-call | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:16 | wait_for_selector | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:19 | get_by_role | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:20 | get_by_label | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:21 | get_by_test_id | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:22 | get_by_text | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:23 | get_by_placeholder | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:24 | get_by_title | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:25 | get_by_alt_text | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:28 | xpath-global | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:31 | remote-debug-flag | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:32 | cdp-922x | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:35 | saramin | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:36 | jobkorea | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:37 | linkedin | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:38 | wanted | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:39 | incruit | full=0 without-own-line=1
contracts/portal-constants-deny-patterns.txt:40 | jobplanet | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:7 | scheme-url | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:10 | listed-tld | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:13 | quoted-three-label | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:16 | localhost-port | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:17 | ipv4-port | full=0 without-own-line=0
contracts/portal-constants-deny-patterns-product.txt:18 | ipv6-port | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:19 | dotted-host-port | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:20 | quoted-single-host-port | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:23 | css-id | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:24 | css-combinator | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:25 | css-class-descendant | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:26 | css-id-descendant | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:27 | css-attribute | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:28 | css-element-attribute | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:31 | xpath-relative | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:32 | xpath-absolute | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:35 | port-assignment | full=0 without-own-line=1
contracts/portal-constants-deny-patterns-product.txt:36 | 92xx-93xx-assignment | full=0 without-own-line=1
```

→ 뭘 시켰나: 전역 23개·제품 18개 규칙을 하나씩 제외하고 그 규칙 전용 입력을 재검사했습니다.
→ 뭐가 나왔나: 40개는 제거 시 전용 입력을 놓쳤고, 제품 17행은 19행과 겹쳐 제거해도 계속 잡혔습니다.
→ 규칙들이 실제 역할을 한다는 점은 좋은 소식이지만, 기존 시험이 이 제거를 수행하지 않고 중복 규칙도 독립적으로 검증할 수 없다는 점은 나쁜 소식입니다.

시험 파일들은 각 RED 작성 뒤 수정되지 않은 이력은 확인했습니다.

```text
9bab751 G3 RED: portal-constants mutation contract fails on missing gate
37d2fa7 G3 RED2: hardening contract exposes five confirmed V1 defects
8e00bff G3 RED3: second adversarial round exposes ten expressions and a shell-wrap CI bypass
09c19b4 G3 RED4: third adversarial round exposes env-carrier CI bypass and semantic locators
f4b4bae G3 RED5: codeaudit exposes literal-scalar CI bypass beyond env
```

→ 뭘 확인했나: 다섯 시험 파일의 변경 이력을 조회했습니다.
→ 뭐가 나왔나: 각 파일은 대응 RED 커밋 한 번만 나타나 후속 GREEN에서 몰래 수정된 흔적은 찾지 못했습니다.
→ 좋은 소식입니다. 다만 시험 설계의 동어반복 문제는 남습니다.

## D8 — [중간] 일부 읽기 실패가 2가 아니라 1로 끝납니다

일반 전제 실패는 올바르게 2였습니다.

```text
MISSING_PATTERN_CASES
FAIL: portal pattern contract missing, unreadable, or empty: /definitely/not/present/g3-patterns
missing-pattern exit=2
FAIL: portal pattern contract missing, unreadable, or empty: /dev/null
empty-pattern exit=2
TEMP_FAILURE_CASE
mktemp: mkstemp failed on /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.sDIlhOqIYz: Operation not permitted
FAIL: temp workspace unavailable
mktemp-failure exit=2
REGEX_ENGINE_CASES
invalid-regex grep-exit=2
empty-match grep-exit=0
```

→ 뭘 시켰나: 실제 패턴 로드 함수에 없는 파일·빈 파일을 넣고 임시 공간 실패, 깨진 규칙, 빈 문자열 일치를 실행했습니다.
→ 뭐가 나왔나: 없는·빈 파일과 임시 공간 실패는 2였습니다. 검색 엔진의 깨진 규칙은 2, 빈 문자열 일치는 0이며 검사기 `:62-68`이 둘 다 검사 불능 2로 바꿉니다.
→ 좋은 소식입니다.

그러나 보호되지 않은 읽기 경로는 1이었습니다.

```text
UNGUARDED_METADATA_READ_CASE
git-mode-read-failure exit=1
UNGUARDED_G3_ENUMERATION_CASE
g3-find-failure exit=1
```

→ 뭘 시켰나: 실제 `:107-153` 반복문에서 Git 파일 모드 읽기를 실패시키고, 실제 `:165-166` G3 파일 열거에서 `find`를 실패시켰습니다.
→ 뭐가 나왔나: 둘 다 약속한 검사 불능 2가 아니라 1로 끝났습니다.
→ 나쁜 소식입니다. 차단 자체는 되지만 자동화가 “위반 발견”과 “검사기 고장”을 구분하지 못합니다.

개수 판정 구간은 다음처럼 작동했습니다.

```text
CASE clean minima => exit=0
FAIL: product files 0 (<2) — 검사 대상이 없어서 통과는 금지 (P20)
CASE zero product targets => exit=2
FAIL: product files 1 (<2) — 검사 대상이 없어서 통과는 금지 (P20)
CASE one product target => exit=2
FAIL: checked files 9 (<10)
CASE checked below floor => exit=2
FAIL: contract files 1 (<2) — 패턴 계약 2벌이 추적되고 있지 않다
CASE one contract file => exit=2
CASE one forbidden literal => exit=1
CASE one wiring failure => exit=1
CASE safe replacement same counts => exit=0
```

→ 뭘 시켰나: 검사기 `:305-324`의 실제 최종 판정 줄을 정상 최소치, 0개, 각 하한 미달, 위반, 배선 훼손으로 실행했습니다.
→ 뭐가 나왔나: 하한은 정확히 2, 위반은 1, 정상은 0이었습니다. 같은 수의 안전한 파일 교체는 0이므로 개수는 파일 정체성 보증이 아니라 최소 수 보증입니다.
→ 하한은 좋은 소식이고, 교체를 탐지하지 못하는 것은 계약 밖 한계입니다.

첫 `source` 방식 실행에서 모든 사례가 0으로 나온 결과는 macOS Bash가 `/dev/fd` 내용을 실행하지 않은 실험 오류라 폐기했습니다. 위 `eval` 재실행이 판정에 사용한 결과입니다.

## D9 — [중간] 문서는 “저장소 전체” 계층에서 제외됩니다

`scripts/acceptance-hs-portal-constants.sh:129-138`은 일반 파일 모드 `100644`인 `.md`, `.yaml`, `.yml`, `.txt`, `.html` 문서를 전역 검사 전에 `continue`로 건너뜁니다.

```text
contracts/portal-markers.json mode=contracts-zone-only
docs/portal-example.md mode=skip-document
docs/run-portal.py mode=scan-global
docs/executable-note.md mode=scan-global
```

→ 뭘 시켰나: 실제 경로 분기를 루트 계약 파일, 일반 문서, 문서 폴더의 실행 코드, 실행 권한 문서에 적용했습니다.
→ 뭐가 나왔나: 일반 문서는 전역 규칙을 전혀 받지 않고 코드·실행 문서는 검사됩니다.
→ 제품 실행 위험은 줄였지만, 직접 요구의 “저장소 전체 계층”이라는 표현과는 불일치합니다.

이 면제는 정당한 사례 문서를 허용하려는 명시적 선택이므로 D4·D5보다 낮게 평가했습니다.

## D10 — [낮음] IPv4 규칙 하나는 다른 규칙과 겹칩니다

제품 패턴 `:17`의 IPv4와 포트 규칙을 제거해도 `:19`의 점이 포함된 호스트와 포트 규칙이 같은 `10.1.2.3:81`을 잡았습니다.

```text
contracts/portal-constants-deny-patterns-product.txt:17 | ipv4-port | full=0 without-own-line=0
```

→ 뭘 시켰나: 17행만 제외하고 그 행의 IPv4 입력을 다시 검사했습니다.
→ 뭐가 나왔나: 19행이 계속 잡아 결과가 바뀌지 않았습니다.
→ 직접 미탐은 아니지만 “각 규칙을 하나씩 죽이면 해당 시험만 빨개진다”는 구조는 성립하지 않습니다.

## D11 — [낮음] 변경 기본 검사가 공백 오류로 실패합니다

```text
git-diff-check exit=2 trailing-whitespace=172 blank-line-at-eof=1
docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:487: trailing whitespace.
+→ 뭘 시켰나: 구현자가 쓰지 않은 값과 표현을 제품 규칙에 입력했습니다.
docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:488: trailing whitespace.
+→ 뭐가 나왔나: 대소문자 URL·localhost·FTP는 잡았지만 여러 포트·CSS·XPath 표현은 놓쳤습니다.
docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:506: trailing whitespace.
+→ 뭐가 나왔나: 코드·표 해석 누락 0개, 결론의 기계 검출 전문용어 없음, 설계 카드 2건, 전체 위반 0건이었습니다.
docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:2737: new blank line at EOF.
```

→ 뭘 시켰나: 기준 브랜치 대비 `git diff --check`를 실행하고 오류 종류를 집계했습니다.
→ 뭐가 나왔나: goal 문서에 줄 끝 공백 172개와 마지막 빈 줄 1개가 있어 종료값 2였습니다.
→ 핵심 기능 결함은 아니지만 저장소 기본 위생에는 나쁜 소식입니다.

# 긍정적으로 확인된 사항

## 두 계층의 기본 분리는 정상입니다

```text
SAFE_EXISTING_FILES
uv.lock PyPI URLs | global=1 product=0 | humansearch/uv.lock
example.com security fixture | global=1 product=0 | scripts/acceptance-secret-webhook-vendor.sh
ws loopback fixture | global=1 product=0 | scripts/acceptance-hs-a3.sh
```

→ 뭘 시켰나: 사용자가 지정한 정당한 기존 파일 세 개를 전역·제품 패턴에 각각 넣었습니다.
→ 뭐가 나왔나: 전역 규칙은 셋 모두 잡지 않았고, 제품 규칙을 저장소 전체에 잘못 적용하면 셋 모두 잡혔습니다.
→ 좋은 소식입니다. 두 계층을 나눈 이유와 현재 적용 방향은 타당합니다.

현재 파일 전체를 같은 경계로 독립 대조한 결과는 다음과 같습니다. 이는 전체 검사기 실행이 아니라 파일 생성이 필요 없는 독립 대조입니다.

```text
MIRROR_COUNTS checked=53 product=2 contracts=3 global_hits=0 product_hits=0
INDEPENDENT_PRODUCT_COUNT=2
```

→ 뭘 시켰나: 추적 파일을 계약·문서·제품·그 밖으로 나누고 실제 두 패턴을 적용했습니다.
→ 뭐가 나왔나: 검사 53개, 제품 2개, 계약 3개이며 현재 내용 적중은 0이었습니다. 독립 제품 파일 수도 2였습니다.
→ 좋은 소식입니다. 현재 저장 내용은 기본 패턴상 깨끗하지만 전체 검사기 0 실행을 대신하지는 않습니다.

계약 파일 세 개는 모두 일반 비실행 파일이었습니다.

```text
100644 9ff24d6f85ad7e8c126c51aabeaac4a836892a2a 0	contracts/cleanroom-deny-patterns.txt
100644 daf3d4d6ac75427a0f7bb2ba39d618476ddfe18d 0	contracts/portal-constants-deny-patterns-product.txt
100644 97b869bb5dd2daeba2d8651dfb7b60b202882ca0 0	contracts/portal-constants-deny-patterns.txt
```

→ 뭘 시켰나: 계약 폴더의 Git 저장 모드를 확인했습니다.
→ 뭐가 나왔나: 세 파일 모두 허용 모드 100644입니다.
→ 좋은 소식입니다. `CONTRACT_FILES≥2`도 현재는 3으로 충족합니다.

유효 패턴 수와 빈 문자열 검사는 정상입니다.

```text
contracts/portal-constants-deny-patterns.txt effective_patterns=23
contracts/portal-constants-deny-patterns-product.txt effective_patterns=18
contracts/portal-constants-deny-patterns.txt newline-probe-exit=1
contracts/portal-constants-deny-patterns-product.txt newline-probe-exit=1
```

→ 뭘 시켰나: 주석·빈 줄을 제외한 실제 규칙 수를 세고 빈 줄에 일치하는지 검사했습니다.
→ 뭐가 나왔나: 전역 23개·제품 18개이며 둘 다 빈 줄에는 일치하지 않았습니다.
→ 좋은 소식입니다.

## 자기면제는 파일명 제외가 아니라 문자열 조립으로 처리했습니다

```text
current-self-scan scripts/acceptance-hs-portal-constants.sh => grep=1
current-self-scan scripts/acceptance-hs-portal-constants-mutations.sh => grep=1
current-self-scan scripts/acceptance-hs-portal-constants-hardening.sh => grep=1
current-self-scan scripts/acceptance-hs-portal-constants-hardening2.sh => grep=1
current-self-scan scripts/acceptance-hs-portal-constants-hardening3.sh => grep=1
current-self-scan scripts/acceptance-hs-portal-constants-hardening4.sh => grep=1
virtual-append-selector scripts/acceptance-hs-portal-constants.sh => grep=0
virtual-append-selector scripts/acceptance-hs-portal-constants-mutations.sh => grep=0
RAW_LITERAL_SEARCH
```

→ 뭘 시켰나: 여섯 G3 파일을 실제 전역 패턴으로 검사하고, 본체와 mutation 파일 끝에 가상 셀렉터를 덧붙여 다시 검사했습니다.
→ 뭐가 나왔나: 현재 파일은 자기 일치가 없지만 가상 추가값은 잡혔습니다. 원문 리터럴 검색도 0건이었습니다.
→ 좋은 소식입니다. `scripts/`나 특정 파일명을 통째로 제외한 자기면제는 찾지 못했고, `mutations.sh:47-60`처럼 조각을 합치는 방식을 사용합니다.

## Bash 3.2 문법은 통과했습니다

```text
GNU bash, version 3.2.57(1)-release (arm64-apple-darwin24)
bash-3.2-syntax scripts/acceptance-hs-portal-constants.sh => exit=0
bash-3.2-syntax scripts/acceptance-hs-portal-constants-mutations.sh => exit=0
bash-3.2-syntax scripts/acceptance-hs-portal-constants-hardening.sh => exit=0
bash-3.2-syntax scripts/acceptance-hs-portal-constants-hardening2.sh => exit=0
bash-3.2-syntax scripts/acceptance-hs-portal-constants-hardening3.sh => exit=0
bash-3.2-syntax scripts/acceptance-hs-portal-constants-hardening4.sh => exit=0
UNSUPPORTED_FEATURE_SEARCH
```

→ 뭘 시켰나: 현재 HEAD의 여섯 셸 파일을 macOS Bash 3.2로 문법 검사하고 `${VAR^^}`, 연관 배열 등 후대 전용 문법을 검색했습니다.
→ 뭐가 나왔나: 여섯 파일 모두 0이고 금지 신문법 검색 결과는 비었습니다.
→ 좋은 소식입니다. 단, 처음부터 끝까지의 전체 실행은 ※ 미확인입니다.

## 문서와 현재 서버 등록은 일치합니다

`.github/workflows/verify.yml:48-58`은 G3 여섯 파일을 실행하고, `docs/sot/verification-commands.md:27`은 같은 여섯 파일을 서버 4번 단계로 기록합니다.

```text
      - name: HumanSearch G3 포털 상수·locator 경계
        run: |
          bash scripts/acceptance-hs-portal-constants.sh
          bash scripts/acceptance-hs-portal-constants-mutations.sh
          bash scripts/acceptance-hs-portal-constants-hardening.sh
          bash scripts/acceptance-hs-portal-constants-hardening2.sh
          bash scripts/acceptance-hs-portal-constants-hardening3.sh
          bash scripts/acceptance-hs-portal-constants-hardening4.sh
```

→ 뭘 확인했나: 현재 서버 실행 단계와 정본 문서의 등록 내용을 대조했습니다.
→ 뭐가 나왔나: 현재 여섯 줄은 조건 없이 존재하고 문서 목록도 일치합니다.
→ 좋은 소식입니다. D1은 현재 등록 누락이 아니라 향후 무력화를 스스로 잡지 못한다는 결함입니다.

# 실행 환경 실패와 재시도 기록

## 격리 복제본 생성 실패

```text
mktemp: mkdtemp failed on /private/tmp/codex-v1-g3.Unnzhf: Operation not permitted
```

→ 뭘 시켰나: `/private/tmp` 아래에 별도 디렉터리를 만든 뒤 `--no-local --no-hardlinks` 복제를 하려 했습니다.
→ 뭐가 나왔나: 복제 전에 디렉터리 생성이 쓰기 정책으로 거부됐습니다.
→ 검증 환경에는 나쁜 소식이지만 원본 무변형에는 좋은 소식입니다.

```text
SCRATCH_EXISTS=yes
SCRATCH_WRITABLE_BIT=no
TMP_WRITABLE_BIT=no
TARGET_STATUS_BEGIN
TARGET_STATUS_END
```

→ 뭘 확인했나: 사용자가 지정한 판정 폴더와 `/private/tmp`의 쓰기 가능 여부, 원본 상태를 확인했습니다.
→ 뭐가 나왔나: 두 임시 위치 모두 쓰기 불가였고 원본 상태는 비어 있었습니다.
→ 이 때문에 파일 변조 실험과 판정 파일 생성이 불가능했습니다.

## 입력 전달 실패와 재시도

첫 긴 셸 입력은 임시 파일을 쓰는 here-document 방식 때문에 다음처럼 실패했습니다.

```text
zsh:1: can't create temp file for here document: operation not permitted
```

→ 뭘 시켰나: 패턴 카나리 목록을 셸 표준입력으로 전달하려 했습니다.
→ 뭐가 나왔나: 셸이 내부 임시 파일을 만들지 못했습니다. 이후 파일을 쓰지 않는 `bash -c` 인자로 다시 실행했습니다.
→ 첫 결과는 판정에 사용하지 않았습니다.

서버 설정 추가 실험의 첫 파일 설명자 방식도 실패했습니다.

```text
awk: can't open file /dev/fd/63
 source line number 2
commented => ci_line_ok=2
awk: can't open file /dev/fd/63
 source line number 2
echo_prefixed => ci_line_ok=2
awk: can't open file /dev/fd/63
 source line number 2
suffixed => ci_line_ok=2
awk: can't open file /dev/fd/63
 source line number 2
spaced_step_if_false => ci_line_ok=2
```

→ 뭘 시켰나: 변형된 YAML을 `/dev/fd` 경로로 `awk`에 전달했습니다.
→ 뭐가 나왔나: macOS에서 경로가 닫혀 2가 났습니다. 이 결과는 폐기하고 `/dev/stdin`으로 재실행해 D1의 1·1·1·0 결과를 얻었습니다.
→ 재시도 뒤 결함 재현에 성공했습니다.

## 판정 파일 쓰기 실패

```text
patch rejected: writing is blocked by read-only sandbox; rejected by user approval settings
```

→ 뭘 시켰나: 요청 경로 `.../scratchpad/codex-v1-verdict-g3.md`에 첫 줄부터 판정 파일을 만들려 했습니다.
→ 뭐가 나왔나: 읽기 전용 정책이 정확한 파일 쓰기를 거부했습니다.
→ 요청에 따라 이 화면 전문을 정본으로 삼아야 합니다.

# 최종 상태 확인

```text
HEAD=f10c8c4e3ceee7f9095c3bd74009434aae823855
BRANCH=task/humansearch-g3-portal-constants
STATUS_BEGIN
STATUS_END
```

→ 뭘 확인했나: 모든 검증 뒤 대상 버전·브랜치·변경 상태를 다시 읽었습니다.
→ 뭐가 나왔나: 처음과 같은 HEAD·브랜치이고 상태 출력은 비어 있습니다.
→ 좋은 소식입니다. 원본 파일은 수정되지 않았습니다.

# 최종 판정

G3의 현재 기본 배선, 기본 계층 분리, 자기면제 방지, 개수 하한, Bash 3.2 문법은 상당 부분 구현돼 있습니다.

그러나 다음 세 가지가 합격을 직접 뒤집습니다.

1. 서버 실행을 끄는 유효한 설정을 검사기가 정상으로 인정합니다.
2. 새 제품 경로와 여러 일반적인 주소·화면 위치 표현을 놓칩니다.
3. 저장소가 정한 3,000줄 변경 상한을 1,332줄 초과했습니다.

따라서 독립 판정은 `VERDICT G3: FAIL`입니다.
