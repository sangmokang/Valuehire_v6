VERDICT: PASS

## 결론

HEAD 013a552의 수정분(999187e, 013a552)은 별도 검토 세션이 재현한 다섯 가지 반례를 모두 실제 실행으로 막습니다. 기준 74e1830 사본에서는 그대로 뚫리던 입력이 HEAD 사본에서는 거부되고, 새로 추가된 시험이 그 거부를 고정합니다. 이 판정은 이 수정분의 실행 합격에 한정되며, 정본 문서의 미완료 항목과 원격 CI 결과는 별도 진행 중이므로 여기에 포함하지 않습니다.

## 판단 근거

**먼저 밝히는 항목(건너뜀·재시도·추정).**
- 재시도 2건: 첫 배치에서 F 항목(강화된 양성 검사)의 acceptance 패치가 인용 오류로 적용되지 않은 채 결과가 출력됐고, C 항목의 renderer 문법 오류 측정은 인수를 2개 넘겨 "invalid arguments" 경로로 잘못 측정됐습니다. 두 항목은 두 번째 배치에서 올바르게 재실행했고, 아래 증거는 재실행 결과입니다. 첫 배치의 해당 두 결과는 무효로 취급합니다.
- 실행 안 함: 전체 pre-push, 원격 CI, 하위 에이전트, 외부 API. 요청대로 제외했습니다.
- 환경: ruby 2.6.10, macOS. root가 아니므로 읽기 불가 시험이 유효했습니다. root 환경에서는 "unreadable" 계열 시험이 뜻을 잃습니다.
- 원문 v1-native.jsonl은 grep으로 반례 입력(`<<: {claims_per_unit: 2}`, `def(; end`)의 존재만 대조했고 전체를 읽지 않았습니다.
- 소스·git·전역 파일은 수정하지 않았고, 종료 시 `git status`는 clean이었습니다. 모든 반례는 /tmp/wup-review.joAblI 아래 사본에서만 실행했습니다.

**선택한 해석.** 공유 T의 "병합 키 << 금지"를 "YAML 파서가 병합을 수행하기 전에 원문 AST 단계에서 거부해야 한다"로 읽었습니다. 파싱 후 결과 해시만 검사하면 그림자 키(`<<`로 넣은 값이 원문 키에 가려지는 경우)를 구별할 수 없기 때문입니다. HEAD는 실제로 그렇게 구현했습니다.

**버린 해석.** "양성 acceptance 자체가 가짜 PASS를 잡아야 한다"는 해석은 버렸습니다. T는 양성 검사 강화를 메타 시험이 막지 않아야 한다고만 요구하며, 가짜 PASS 거부는 음성 실행 시험의 책임입니다. HEAD의 acceptance는 여전히 가짜 PASS22를 통과시키지만(OBSERVED exit=0), 이는 T가 허용한 경계입니다.

**틀리면 깨지는 것.**
- 시드 무작위화가 기억형 가짜를 막는다는 결론은 "공격자가 시험 실행 시점의 시드를 미리 알 수 없다"에 의존합니다. 환경변수 `WORK_UNIT_PROPERTY_SEED`를 CI에서 고정해 버리면 이 방어는 다시 무너집니다.
- 실패 계수 시험은 4개 고정 사례(0, 1, 18, 22)만 봅니다. 진단 메시지까지 정확히 흉내 내는 표 기반 가짜는 이론상 통과하지만, 그런 가짜는 사실상 실제 검증기와 같은 일을 해야 합니다.
- 동일 권한으로 구현과 시험을 함께 고칠 수 있는 한계는 그대로입니다. 메타 시험은 저장소를 복사해 돌리지만 한 사람이 구현·시험·메타 시험을 모두 바꿀 수 있습니다.

## 기술 상세와 증거 원문

**기록.** 2026-09-10T05:14:51+0900, HEAD 013a552a74be3f7841fcb37020e00df42aa133fc, 브랜치 task/pr37-resolution-fixes-20260910, status clean. diff는 6파일 +71/−5.

**변경 위치와 역할.**
- `scripts/verify/work_unit_policy.rb:92` 중복 키 순회 중 스칼라 키가 `<<`이면 POLICY_SCHEMA_INVALID를 쌓는 줄. Psych가 병합을 적용하기 전 AST 단계입니다.
- `scripts/verify/check-work-unit-policy.rb:11` require 실패 rescue 목록에 SyntaxError를 추가한 줄. renderer도 같은 줄(`render-work-unit-policy.rb:11`).
- `scripts/verify/work-unit-policy-contract-test.rb:58-60` alias·병합·그림자 병합 세 반례를 실패 입력으로 고정한 줄.
- `scripts/verify/work-unit-policy-contract-test.rb:75-77` 시드를 매번 새로 뽑고 출력하며 환경변수로 재현하는 줄.
- `scripts/verify/work-unit-policy-contract-test.rb:136-149` 실패 계수 4사례(0/1/18/22)를 실제 실행으로 확인하는 블록.
- `scripts/verify/work-unit-policy-contract-test.rb:151-172` 모듈 누락·빈·링크·디렉터리·읽기불가·문법오류 6종에 대해 checker·renderer 모두 NOT_RUN/exit 2를 요구하는 블록.
- `scripts/verify/work-unit-policy-gates-test.rb:69-70` 가짜 PASS22가 양성 관문을 통과해야 한다는 단언을 관찰 출력으로 바꾼 줄.
- `scripts/verify/work-unit-policy-gates-test.rb:79-96` 실패 계수 위조·aliases:true·실수 동등 비교 세 변이를 계약 시험이 FAIL로 잡는지 확인하는 블록.

**A. 계약 시험과 메타 시험 실행(05:17~05:19).**
```
A1 contract @HEAD  exit=0  PROPERTY_SEED: 202930171105186573233664593863930195682  CHECKED: 84  VERDICT: PASS
A2 replay same seed exit=0 CHECKED: 84 PASS / seed=37 exit=0 CHECKED: 84 PASS
A3 gates meta @HEAD exit=0  OBSERVED: fake PASS22 positive gate exit=0  CHECKED: 22  VERDICT: PASS
```
→ 해석: 계약 시험 84건, 메타 시험 22건 모두 통과했습니다. 기록된 시드로 동일 결과가 재현됐고, 시드 37로도 통과합니다. 기준 74e1830의 계약 시험은 62건, 메타 시험은 20건이었으므로 각각 22건, 2건이 추가됐습니다.

**B. 병합 키 반례(반례 1).** 원본 정책에서 work_unit 또는 root에 병합 키를 넣은 7가지 변형을 기준/HEAD 사본에 각각 넣었습니다.
```
[m1 <<: {claims_per_unit: 2} + claims_per_unit: 1 /base] exit=0 VERDICT: PASS|POLICY_CHECKED: 22
[m1 /head] exit=1 VERDICT: FAIL|POLICY_SCHEMA_INVALID: merge key at $[0][0].work_unit|POLICY_CHECKED: 0
[m2 <<: {claims_per_unit: 1} 단독 /base] exit=0 PASS      [m2 /head] exit=1 SCHEMA_INVALID merge key
[m3 root <<: {version: 1} /base] exit=0 PASS               [m3 /head] exit=1 merge key at $[0][0]
[m5 <<: &b {version: 9} 앵커 병합 /base] exit=0 PASS        [m5 /head] exit=1 merge key at $[0][0]
[m6 "<<" 따옴표 키 /base] exit=0 PASS                       [m6 /head] exit=1 merge key at $[0][0].work_unit
[m7 <<: [{claims_per_unit: 2}] 목록 병합 /base] exit=0 PASS [m7 /head] exit=1 merge key
[m4 앵커 정의용 추가 키 base/head] exit=1 SCHEMA_INVALID: root (양쪽 동일)
renderer head on m1: exit=1 stdout_bytes=0 stderr=VERDICT: FAIL|POLICY_SCHEMA_INVALID: merge key ...
```
→ 해석: 기준에서는 6가지 병합 변형이 모두 승인 정책처럼 exit 0으로 통과했습니다. HEAD에서는 모두 exit 1, POLICY_SCHEMA_INVALID로 거부되고 renderer도 stdout 없이 exit 1입니다. 따옴표로 감싼 `"<<"`는 Psych가 문자열 키로 다루지만 HEAD 순회는 값이 `<<`이면 무조건 거부하므로 동일하게 막힙니다. 실패 계수 0은 파싱 단계 거부이므로 T의 계수 규칙과 일치합니다.

**C. 모듈 문법 오류(반례 5).** 사본 모듈에 `module WorkUnitPolicy; def(; end`를 씀.
```
[syntax/base/checker]        exit=1 stderr=...require_relative': ...work_unit_policy.rb:1: syntax error (스택트레이스)
[syntax/head/checker]        exit=2 stderr=VERDICT: NOT_RUN|REASON: policy runtime unavailable (SyntaxError)
[syntax/base/renderer 1-arg] exit=1 stderr=...syntax error, unexpect... (스택트레이스)
[syntax/head/renderer 1-arg] exit=2 stderr=VERDICT: NOT_RUN|REASON: policy runtime unavailable (SyntaxError)
```
→ 해석: 기준의 스택트레이스/exit 1이 HEAD에서 NOT_RUN/exit 2로 바뀌었고 stdout은 비어 있습니다. 계약 시험의 module 블록 12건(6종 × 2프로그램)이 이를 고정합니다.

**D. 실패 계수 위조(반례 2).** 실패 경로의 `POLICY_CHECKED: #{checked}`를 상수 22로 바꾼 사본.
```
[forge/base contract]  exit=0 CHECKED: 62 VERDICT: PASS
[forge/head contract]  exit=1 FAIL: parse failure count / root failure count / nested schema failure count  CHECKED: 84 VERDICT: FAIL
직접 실행(head 위조본, broken YAML): VERDICT: FAIL ... POLICY_CHECKED: 22 (실제는 0이어야 함) exit=1
```
→ 해석: 기준 계약 시험은 위조를 통과시켰고 HEAD는 세 계수 단언에서 잡습니다. 양성 acceptance는 양쪽 모두 PASS인데, 이는 성공 경로 계수가 위조되지 않았기 때문이며 정상입니다. 메타 시험의 "forged failure count rejected by contract"가 이를 이중으로 고정합니다.

**E. aliases:true / 실수 동등 비교 변이.**
```
[aliases: true]              exit=1 FAIL: alias with valid schema, renderer rejects alias with valid schema
[unless actual == expected]  exit=1 FAIL: float units, float version (+renderer 2건)
```
→ 해석: 새로 추가된 "alias with valid schema" 사례가 aliases:true 변이를 잡는 유일한 단언입니다. 기존 "alias" 사례는 미지 키로도 걸리므로 이 추가가 없었다면 aliases:true는 통과했을 것입니다.

**F. 강화된 양성 검사 오차단(반례 3, 재시도 결과).** acceptance에 `/dev/null` 정책 음성 검사를 추가한 사본.
```
strong acceptance with real checker: PASS: negative /dev/null policy rejected  CHECKED: 6  VERDICT: PASS exit=0
strong acceptance with fake PASS22:  FAIL: negative /dev/null policy not rejected exit=0  VERDICT: FAIL exit=1
meta gates @HEAD with strong gate:   exit=0  OBSERVED: fake PASS22 positive gate exit=1  CHECKED: 22  VERDICT: PASS
meta gates @BASE with strong gate:   exit=1  FAIL: fake output can fool positive gate (known boundary)  CHECKED: 20  VERDICT: FAIL
```
→ 해석: 기준 메타 시험은 정상적인 강화를 오차단했고, HEAD 메타 시험은 강화된 관문이 가짜를 exit 1로 거부한 사실을 관찰만 하고 통과시킵니다. T의 요구와 일치합니다.

**G. 시드 37 기억형 가짜 checker+renderer(반례 4).** 보존된 v1-whitelist-fake-checker.rb를 그대로 쓰고, 같은 13개 해시를 기억하는 가짜 renderer를 사본에 작성했습니다.
```
fake acceptance (양성 관문): CHECKED: 5 VERDICT: PASS   ← 예상된 경계
[fake @base contract]     exit=0 CHECKED: 62 VERDICT: PASS   ← 기준에서는 통과
[fake @head seed=37]      exit=1 FAIL: parse/root/nested schema failure count + module 6종×2  CHECKED: 84 FAIL
[fake @head random seed]  exit=1 위 항목 + mapping permutation 0~11, deterministic rendering 0~11 모두 FAIL
```
→ 해석: 기준 계약 시험은 기억형 가짜를 통과시켰습니다. HEAD는 시드를 37로 고정해 줘도 실패 계수와 모듈 경계 시험에서 잡고, 무작위 시드에서는 순열 24건까지 추가로 잡습니다.

**H. 크기 한도.** work_unit_policy.rb 224줄, contract-test 176줄, gates-test 126줄, checker 40줄로 파일 hard 600 이내입니다. 함수 단위로 100줄을 넘는 정의는 없습니다(가장 긴 정의는 render 41줄).

**결함 및 잔여 관찰.**

1. 심각도 낮음. 제목: 모듈 로드 시 런타임 예외는 여전히 스택트레이스/exit 1. 원인: `check-work-unit-policy.rb:11`의 rescue가 LoadError·SyntaxError·SystemCallError만 잡습니다. 모듈이 로드 중 `raise`하거나 메서드가 없으면(NoMethodError) 기준과 HEAD 모두 exit 1 스택트레이스입니다. 사업 영향: T가 열거한 6종 밖이라 계약 위반은 아니지만, 실행 환경 손상을 "정책 실패"처럼 exit 1로 보고해 원인 분류를 흐릴 수 있습니다.
   ```
   [runtime-raise/head/checker] exit=1 stderr=...boom at load (RuntimeError)
   [no-methods/head/checker]    exit=1 stderr=...undefined method `load_policy' (NoMethodError)
   ```
2. 심각도 낮음. 제목: 시드 환경변수 오염 시 시험 크래시. 원인: `contract-test.rb:75`가 `Integer(ENV[...])`로 파싱하므로 숫자가 아닌 값이면 ArgumentError로 exit 1이 되고 CHECKED/VERDICT 없이 끝납니다. 사업 영향: CI에서 잘못된 변수 하나로 계약 시험이 NOT_RUN 구분 없이 FAIL처럼 보입니다.
3. 심각도 정보. 제목: 실패 계수 단언은 4개 고정 사례에 의존. 원인: `contract-test.rb:138-142`가 0/1/18/22 네 경우만 실행합니다. 사업 영향: 진단 종류별 계수표를 가진 가짜는 이 4건을 통과할 수 있으나, 그 가짜는 모든 다른 계약 사례의 진단도 정확해야 하므로 실질적 위협은 낮습니다.

**설계 지적: 가짜 PASS22 단언을 관찰 출력으로 교체.**
- 무엇을: `gates-test.rb:69-70`에서 "가짜가 양성 관문을 통과해야 한다"는 단언을 삭제하고 exit 값만 출력합니다.
- 왜: 그 단언은 양성 관문의 정상적 강화를 실패로 만들었습니다(F 항목 기준 결과).
- 버린 길: 단언을 "rc == 0 || rc == 1"로 완화하는 방법. 이러면 exit 2 같은 비정상 종료를 놓칩니다.
- 대가: 양성 관문이 가짜를 통과시키는 현재 경계가 자동 기록에서 사라지고 관찰 문자열로만 남습니다.
- 되돌리기: 두 줄을 원래 단언으로 복원하면 됩니다. 다른 시험에 의존성이 없습니다.

**반증 시도 기록.** 병합 키를 앵커·따옴표·목록·root 위치로 바꿔 우회하려 했으나 모두 거부됐습니다. 기억형 가짜에 시드 37을 명시적으로 주어 순열 시험을 통과시키려 했으나 실패 계수와 모듈 경계 시험에서 막혔습니다. 강화된 양성 관문을 기준 메타 시험에 넣어 오차단을 재현했고 HEAD에서는 재현되지 않았습니다. 이 수정분 안에서 T를 위반하는 입력은 찾지 못했습니다.

**별도 표시.** 정본 문서 `docs/engineering/pr37-resolution-goal-2026-09-10.md:74`는 스스로 "전체 PASS가 아니다"라고 적고 있으며, 원격 CI와 원본 전체 검토는 다른 세션에서 진행 중입니다. 이 판정은 수정분의 로컬 실행 합격만을 뜻합니다.
