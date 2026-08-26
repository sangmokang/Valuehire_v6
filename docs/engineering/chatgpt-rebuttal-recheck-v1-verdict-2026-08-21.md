VERDICT: FAIL

## 결론

먼저 제한을 밝힙니다. 실행용 복사본 생성은 환경의 쓰기 차단으로 실패했고, 자연 상태의 동시 실행 200회는 제가 다시 수행하지 못했습니다. 외부 서비스 재조회도 현재 인증 만료와 통신 차단으로 실패했습니다. 저장소 파일은 수정하지 않았으며, 처음부터 있던 미추적 문서 1개만 그대로 남았습니다.

네 주장 중 2와 3은 범위를 정확히 좁히면 살아남고, 4도 여러 정정이 이미 반영됐다는 점은 맞습니다. 그러나 주장 1의 `8/15`를 전체 안전 수준으로 부르는 것은 깨집니다. 바꾸는 방법에 따라 `8/15`, `9/14`, `23/0`으로 결과가 달라지며, 실제로 스크립트를 실행하는 다른 문법까지 실패로 세는 경우가 있습니다.

따라서 제출 전체는 실패입니다. 정확한 표현은 “선택한 여섯 검사에 대해 `echo` 치환 한 종류를 시험했더니 23개 중 8개가 실패했다”입니다.

## 판단 근거

| 주장 | 판정 | 선택한 해석 | 버린 해석 | 이 판단이 틀리면 깨지는 것 |
|---|---|---|---|---|
| 1. 8개 탐지·15개 무탐지 | **불완전·과장** | `echo` 치환이라는 한 가지 변조 시험 결과로는 맞습니다. | 이를 전체 보호 수준으로 부르는 해석 | 삭제·조건 비활성화·정상 파이프 실행에서 결과가 달라집니다. |
| 2. guard 동시 실행 | **조건부 확인** | 경합(두 실행 순서에 따라 결과가 달라지는 문제)은 코드상 가능합니다. | 2초 지연이 존재하지 않던 결과를 만들었다는 해석 | 원본에서도 상태 공개와 첫 권한 변경 사이에 실행권이 넘어갈 수 있습니다. |
| 3. GitHub 통제 장치 | **현재 구조에서는 확인** | 개인 비공개 무료 저장소에서는 요금제 제한이 원인이라는 증거가 강합니다. | 토큰 권한 부족만으로 동일 메시지가 나왔다는 해석 | 두 요청의 정확한 응답 본문과 공식 기능표를 함께 설명하지 못합니다. |
| 4. 문서 정정 반영 | **부분 확인** | 뒷부분 정정은 주요 오류 다수를 반영했습니다. | 정정 구간이 있으므로 문서 전체를 그대로 써도 된다는 해석 | 앞부분과 뒷부분의 우선순위·결론이 서로 충돌합니다. |

→ 무엇을 대조했나: 네 주장별로 실제 검사 코드, 문서 정정 구간, 공식 GitHub 기능표를 대조했습니다. 무엇이 나왔나: 주장 1과 4에는 의사결정을 바꾸는 과장이 남았고, 주장 2와 3은 범위 제한이 필요합니다. 전체 판정에는 나쁜 소식입니다.

## 기술 상세와 증거 원문

### 1. 주장 1 — `8/15`는 “보호 범위”가 아닙니다

현재 워크플로에는 `bash scripts/...` 실행 줄이 정확히 23개입니다. [verify.yml:29](/Users/kangsangmo/Desktop/Valuehire_v6/.github/workflows/verify.yml:29) 역할: 첫 번째 대상 실행 줄, [verify.yml:196](/Users/kangsangmo/Desktop/Valuehire_v6/.github/workflows/verify.yml:196) 역할: 마지막 대상 실행 줄입니다.

반증 과정에서 워크플로를 읽는 경로를 전수 검색했습니다. 실질적으로 추가되는 것은 다음뿐이었습니다.

- [acceptance-0-5.sh:15](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/acceptance-0-5.sh:15) 역할: `verify.sh`와 `acceptance-0-6.sh` 이름 존재를 확인합니다.
- [acceptance-hs-gates-mutations.sh:27](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/acceptance-hs-gates-mutations.sh:27) 역할: G2 두 실행 줄을 확인하지만, 제출 후보의 antiforge 검사와 범위가 겹칩니다.
- [check-pre-push-runtime.sh:48](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/verify/check-pre-push-runtime.sh:48) 역할: 격리된 훅 실행을 재현하지만, 제출 후보의 pre-push 판정과 동일한 범위입니다.
- 루트 `package.json`과 `Makefile`은 없습니다.
- `pre-commit`은 워크플로 전체 의미를 검사하지 않습니다. [pre-commit:103](/Users/kangsangmo/Desktop/Valuehire_v6/hooks/pre-commit:103) 역할: 추가된 줄만 약화 패턴과 대조합니다.

저장소가 삭제 공백을 이미 인정합니다. [suppressions.yaml:28](/Users/kangsangmo/Desktop/Valuehire_v6/suppressions.yaml:28) 역할: 삭제 탐지 공백을 등록하며, [suppressions.yaml:30](/Users/kangsangmo/Desktop/Valuehire_v6/suppressions.yaml:30) 역할: 추가된 줄만 검사하므로 삭제를 못 잡는다고 명시합니다.

#### 변조별 결과

| 변조 | 예상 결과 | 이유 |
|---|---:|---|
| `run: echo bash scripts/X` | **8 탐지 / 15 무탐지** | 제출 실측과 코드가 일치합니다. |
| 실행 단계 전체 삭제 | **9 탐지 / 14 무탐지** | 기존 8개에 `acceptance-0-6` 삭제를 `acceptance-0-5`가 추가로 잡습니다. |
| 부모 단계에 리터럴 `if: false` | **23 탐지 / 0 무탐지** | pre-push가 워크플로 어디든 리터럴 조건이 하나 있으면 차단합니다. |
| `cat scripts/X \| bash` | 보호 수치로 계산 불가 | 대상 파일을 읽어 Bash에 주면 실제 스크립트가 실행됩니다. 문자열 검사 일부가 이를 거부해도 안전 실패가 아니라 문법 오인입니다. |

→ 무엇을 시켰나: 변조 형태별로 현재 판정식이 반응하는 범위를 계산했습니다. 무엇이 나왔나: 결과가 `8/15`, `9/14`, `23/0`으로 바뀝니다. 따라서 하나의 수치를 전체 보호 정도로 쓰는 것은 나쁜 해석입니다.

읽기 전용으로 리터럴 `if: false` 판정식을 23줄 각각에 적용한 결과입니다.

```text
bash_n_rc=0
if_false_global_detector=23/23
acceptance_0_5_name_check baseline=0 echo=0 deletion=1
acceptance_0_6 direct_rc=1 cat_pipe_rc=1
```

→ 무엇을 시켰나: 현재 훅의 정규식(문자열 모양을 대조하는 규칙)을 각 실행 줄에 적용하고, `acceptance-0-6` 이름 검사도 비교했습니다. 무엇이 나왔나: `if: false`는 23개 모두 잡고, `acceptance-0-5`는 `echo`는 못 잡지만 삭제는 잡습니다. `cat … | bash`는 직접 실행과 동일한 종료값을 냈습니다.

#### `acceptance-0-5` 제외 판단

기준선(baseline, 변조 전 정상 결과)이 실패한 검사를 단순히 `exit!=0` 탐지기로 세면 모든 변조를 잡은 것처럼 보입니다. 따라서 제외 자체는 타당했지만, 기준선을 정상화하지 않은 채 검사 전체를 버린 것은 불완전합니다.

- `echo` 실험에는 영향이 없습니다. [acceptance-0-5.sh:18](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/acceptance-0-5.sh:18) 역할: 파일명 존재만 보므로 `echo` 뒤에도 이름이 남습니다.
- 단계 삭제 실험에는 영향이 있습니다. 같은 줄이 사라지면 추가로 실패합니다.
- 올바른 재시험은 복제본의 `main`과 `origin/main`을 맞춰 기준선을 성공시키거나, 배송 대조와 워크플로 이름 검사를 분리해 판정하는 것입니다.

**결함 — 심각도 중간**

- 원문 제목: **“CI 실행 줄 보호 범위 실측”**
- 원인: 한 변조에 대한 문자열 탐지율을 전체 보호 수준으로 이름 붙였습니다.
- 사업 영향: 이미 잡히는 공격과 정상 실행 문법을 구분하지 못해 보강 우선순위가 왜곡됩니다.

**결함 — 심각도 낮음**

- 원문 제목: **“acceptance-0-5 기준선 실패로 탐지기 집합에서 제외”**
- 원인: 관련 없는 배송 실패와 워크플로 배선 단언을 분리하지 않았습니다.
- 사업 영향: 삭제 변조에서 실제 탐지 한 건을 누락하게 됩니다.

**설계 지적 — 측정 이름**

- 무엇을: 결과를 `echo 치환 탐지율 8/23`으로 제한해 기록합니다.
- 왜: 변조마다 탐지 범위와 의미가 다릅니다.
- 버린 길: 단일 수치를 “보호/무방비”로 이름 붙이는 방식입니다.
- 대가: 변조별 표와 기준선 관리가 필요합니다.
- 되돌리기: 변조별 자료를 합치면 기존 단일 수치로 돌아갈 수 있습니다.

### 2. 주장 2 — sleep은 결함을 만들지 않았지만 발생 가능성을 부풀렸습니다

원본의 가능한 실행 순서는 다음과 같습니다.

1. [guard-global-skill-files.sh:112](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/guard-global-skill-files.sh:112) 역할: 임시 기록을 최종 상태 파일로 공개합니다.
2. `recover`가 [guard-global-skill-files.sh:227](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/guard-global-skill-files.sh:227) 역할: 복구를 시작합니다.
3. [guard-global-skill-files.sh:232](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/guard-global-skill-files.sh:232) 역할: 원래 권한을 복원합니다.
4. [guard-global-skill-files.sh:233](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/guard-global-skill-files.sh:233) 역할: 상태 파일을 삭제합니다.
5. 먼저 시작한 `lock`이 [guard-global-skill-files.sh:132](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/guard-global-skill-files.sh:132) 역할: 두 파일을 444로 바꿉니다.
6. [guard-global-skill-files.sh:140](/Users/kangsangmo/Desktop/Valuehire_v6/scripts/guard-global-skill-files.sh:140) 역할: 성공을 출력합니다.

따라서 최종 상태 “444 두 개 + 상태 없음 + lock 성공”은 원본 명령의 합법적인 실행 순서입니다. `sleep 2`는 그 사이를 넓혔지만 상태 전이 자체를 바꾸지는 않았습니다.

반면 자연 실행 `0/200`은 중요합니다. 이는 “불가능”의 증거가 아니라 “이 시험 조건에서는 관측하지 못함”의 증거입니다. ※ 각 시도가 독립이라는 강한 가정 아래에서도 0/200은 발생률의 95% 상한을 대략 1.5%로만 제한합니다. 실제 예약 방식이 반복마다 비슷하면 이 계산보다 증거가 더 약합니다.

**결함 — 심각도 낮음**

- 원문 제목: **“guard 동시 실행 경합”**
- 원인: “동시에 돌리면 된다”라고 필연적 결과처럼 표현했습니다.
- 사업 영향: 실제 결함은 남지만 운영 발생 가능성과 긴급도가 과장됩니다.

심각도는 **중간**이 적절합니다. 파일 내용 손실은 없고 수동 권한 복구가 가능하지만, 원래 권한 기록과 자동 복구 경로가 사라집니다. 문서의 “중간→높음 상향”은 자연 실행 0/200을 반영하면 근거가 약합니다.

**설계 지적 — 동시 실행 통제**

- 무엇을: 네 명령 전체에 상호 배제 장치(한 번에 한 실행만 들어가게 하는 잠금)를 둡니다.
- 왜: 상태 파일 보존만으로는 진행 중인 `lock`을 `recover`가 앞지르는 순서를 막지 못합니다.
- 버린 길: 실패 시 상태 파일 삭제 위치만 옮기는 수정입니다.
- 대가: 죽은 실행의 잠금을 회수하는 규칙이 필요합니다.
- 되돌리기: 잠금 파일과 회수 검사만 제거하면 현재 동작으로 돌아갑니다.

### 3. 주장 3 — 403은 요금제 원인이라는 판단이 가장 강합니다

현재 제 환경에서는 재시도가 실패했습니다.

```text
X Failed to log in to github.com account sangmokang
The token in default is invalid.
error connecting to api.github.com
```

→ 무엇을 시켰나: 현재 인증으로 저장소 정보와 두 보호 API를 다시 조회했습니다. 무엇이 나왔나: 서버의 403까지 도달하지 못했습니다. 따라서 사용자가 제시한 당일 응답을 독립 재현하지 못한 것은 나쁜 제한입니다.

그럼에도 제출된 정확한 응답 `"Upgrade to GitHub Pro or make this repository public"`은 요금제 제한을 직접 가리킵니다. 공식 문서도 비공개 저장소의 보호된 브랜치는 Pro·Team·Enterprise에서 제공된다고 명시합니다. [GitHub protected branches 문서](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches) 규칙셋도 비공개 저장소에서는 Pro·Team·Enterprise가 필요합니다. [GitHub rulesets 문서](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)

토큰 권한 범위(scope, 인증서가 허용하는 API 범위) 가능성을 공격했지만 완전한 반례가 되지 못했습니다.

- 보호 설정 조회는 세분화 토큰에 `Administration: read`가 필요합니다. [GitHub branch protection API](https://docs.github.com/en/enterprise-cloud@latest/rest/branches/branch-protection)
- 규칙셋 목록 조회는 `Metadata: read`만 필요합니다. [GitHub rulesets API](https://docs.github.com/en/rest/repos/rules)
- 권한 부족이라면 GitHub는 보통 `Resource not accessible by personal access token`과 필요한 권한 헤더를 제공합니다. [GitHub REST 문제 해결](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api)

따라서 두 API가 모두 정확히 업그레이드 메시지를 반환했고 같은 비공개 저장소의 검사 기록 조회가 성공했다면, 단순 토큰 권한 부족보다 요금제 원인이 훨씬 강합니다.

다만 신뢰의 뿌리(최종 판정을 구현자가 임의로 바꾸지 못하게 강제하는 독립 지점)라는 설계 자체가 불가능한 것은 아닙니다.

- 같은 저장소를 공개하면 무료 요금제에서도 가능합니다.
- 개인 계정을 Pro로 올리면 가능합니다.
- 무료 조직으로 이전만 해서는 비공개 저장소 제한이 그대로입니다. Team 이상이 필요합니다.
- GitHub App은 인증 주체를 분리할 수 있지만 요금제 잠금을 해제하지 못합니다.
- 검사 기록 조회 성공은 사후 확인을 가능하게 할 뿐, 병합 차단을 강제하지는 않습니다.

**설계 지적 — 외부 강제 지점**

- 무엇을: “현재 비공개 무료 구조에서는 불가”와 “구조 변경 후 가능”을 분리합니다.
- 왜: 현재 권고의 실행 가능성과 장기 설계 가능성은 다른 질문입니다.
- 버린 길: GitHub App만 추가하면 요금제 제한까지 우회된다는 해석입니다.
- 대가: 공개 전환은 정보 노출, 유료 전환은 비용, 유료 조직 이전은 운영 복잡성이 생깁니다.
- 되돌리기: 공개 저장소는 다시 비공개로, 앱은 제거할 수 있지만 공개 이력 자체는 완전히 회수되지 않을 수 있습니다.

### 4. 주장 4 — 정정은 실제로 들어갔지만 문서는 아직 그대로 쓰면 안 됩니다

반영된 내용은 분명합니다.

- [판정문:270](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:270) 역할: R2 영수증 원안을 폐기합니다.
- [판정문:273](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:273) 역할: R3를 1순위로 올리고 동시 실행 통제를 포함합니다.
- [판정문:275](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:275) 역할: 라벨 기각을 부분 철회합니다.
- [판정문:267](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:267) 역할: 검사 기록 조회 권한·시점·대상 이름 조건을 보강합니다.
- [판정문:277](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:277) 역할: 큰 변경량을 규칙 위반 증거로 삼은 서술을 철회합니다.
- [판정문:278](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:278) 역할: 검증 코드 변경을 별도 절차로 다루라는 요구를 추가 채택합니다.

하지만 앞부분은 여전히 반대 결정을 말합니다.

- [판정문:14](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:14) 역할: 라벨 5종을 기각합니다.
- [판정문:21](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:21) 역할: 우선순위를 `R2 → R1 → R3`로 권고합니다.
- 뒷부분은 R2 폐기, R3 1순위, 라벨 부분 철회입니다.

아직 반영되지 않은 새 지적은 다음과 같습니다.

1. 현재 23줄의 `8/15` 실측과 변조별 차이.
2. 자연 경합 `0/200`.
3. 문서는 `chmod` 가로채기로 순서를 고정했다고 적지만 [판정문:285](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:285) 역할: 재현 방법 기록, 이번 제출은 상태 확정 뒤 `sleep 2` 주입이라고 합니다. 어느 재현이 최종 증거인지 일치시켜야 합니다.
4. `cat 대상스크립트 | bash`가 실제 실행 문법이라는 구분.
5. 모든 안전장치의 본문 변조를 채택할지는 [판정문:287](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:287) 역할: 명시적 미결정으로 남아 있습니다.
6. 문서 생성·증거 식별값 요구와 “모델이 병합 가능 판정을 내리지 못하게 한다”는 요구는 대체 설계가 없습니다.
7. “옛 커밋의 성공을 새 커밋에 실제 사용한 일이 있었다”는 [판정문:56](/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/chatgpt-verify-feedback-verdict-2026-08-20.md:56) 역할: R1 필요성을 정당화하는 역사 주장에 독립 근거가 여전히 없습니다.

**결함 — 심각도 높음**

- 원문 제목: **“ChatGPT 검증체계 피드백 8항목 — 채택 판정”**
- 원인: 기존 결론을 교체하지 않고 문서 끝에 반대 결론을 덧붙였습니다.
- 사업 영향: 앞부분만 읽으면 이미 폐기된 R2를 먼저 착수하고, 뒤까지 읽으면 R3를 먼저 착수하게 됩니다.

**설계 지적 — 문서 판정 통합**

- 무엇을: 첫 결론과 결정 카드에 `SUPERSEDED`를 붙이거나 최종 결론으로 다시 씁니다.
- 왜: 한 문서에 상반된 실행 우선순위가 동시에 살아 있습니다.
- 버린 길: 끝에 정정 구간만 계속 추가하는 방식입니다.
- 대가: 감사 이력을 별도 원문 파일로 분리해야 합니다.
- 되돌리기: 통합본을 제거하고 현재 덧붙이기 형식으로 복귀할 수 있습니다.

## 검증 종료 기록

```text
HEAD=dcc71dd022cba9656cb1a4b6a0f825d8d99655a5
git status:
?? docs/engineering/adversarial-separation-goal-2026-08-21.md

workflow sha256=96fdff176e77c5775ed71b549f19d1fb2094af2a4c9708a20bcbc26abef07688
guard sha256=92909d4a38131cbeac9ab4a7ca9892aada8649a0d3af4cd34c8ef3d777621e66
verdict-doc sha256=c61b45918e178b0ac6a2a6baad74b1a0d5b42e918a75199cacc276f9a626ae34
```

→ 무엇을 시켰나: 종료 시 현재 위치와 핵심 파일 지문을 다시 읽었습니다. 무엇이 나왔나: 시작부터 존재한 미추적 문서 1개 외에 새 변경은 없습니다. 읽기 전용 조건은 지켜졌습니다.
