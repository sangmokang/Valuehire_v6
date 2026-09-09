VERDICT: FAIL

## 결론

정책 검사기와 렌더러 자체는 제가 만든 모든 정상·비정상 입력에 대해 계약대로 동작했고, 기존 main의 검사 29개도 전부 통과했습니다. 그러나 이 변경이 약속한 "출력만 꾸민 가짜 검사기는 독립 고장 입력 시험으로 잡아낸다"는 주장이 실제 실행으로 반증되었습니다. YAML을 전혀 읽지 않고 알려진 입력의 해시만 대조하는 86줄짜리 가짜 검사기로 바꾸고 실제 검사 모듈을 지워도, 로컬과 CI에 배선된 모든 관문이 초록으로 통과했습니다. 코딩 원칙 P13⑥은 살아남은 무력화가 하나라도 있으면 검증 체계 자체를 FAIL로 규정하므로 판정은 FAIL입니다. 그 외에 실패 시 처리 수 위조가 탐지되지 않는 점, 별칭 거부 시험이 실질적으로 비어 있는 점, 메타 시험이 관문의 약점을 고정해 향후 강화를 CI가 막는 점을 확인했습니다.

## 판정 앞에 밝히는 미실행·미확인·추정

- **NOT_RUN: Ruby 3.x 실행.** 이 기기에는 /usr/bin/ruby 2.6.10만 있습니다. CI 러너(ubuntu-latest)는 Ruby 3.2 이상이므로 Psych 4 호환은 코드 정독으로만 확인했습니다(키워드 인수·예외 클래스는 호환 범위로 판단). Ruby 의존 자체는 기준 main의 acceptance-principles-check.sh와 pre-commit이 이미 갖고 있어 이 PR의 신규 의존은 아닙니다.
- **NOT_RUN: 원격 GitHub CI.** push·PR 수정이 금지 범위라 verify.yml의 실제 원격 실행 결과는 없습니다. 로컬에서 동일 명령을 wrapper 포함해 실행했습니다.
- **실패 후 재시도 2건.** 카운트 위조 반례와 관문 강화 반례는 첫 시도에서 제 문자열 치환이 실패해 원본 그대로 실행됐습니다. 파일 기반 패치로 재실행한 결과만 채택했습니다. 화이트리스트 가짜 검사기도 첫 시도는 제 진단 문자열 형식 오류로 mutation 검사에 걸렸고, 형식을 고친 두 번째 실행 결과가 아래 D1입니다.
- **무효 시도 1건.** ruby 부재 상황을 run-acceptance.sh를 통해 시험한 실행은 제가 만든 PATH에 tee가 없어 무효입니다. 직접 acceptance 실행 결과만 채택했습니다.
- **추정 없음.** 아래 모든 결함은 실행 결과에 근거합니다.

## 판단 근거

**채택한 해석.** T 계약 문장 "출력만 꾸민 checker는 독립적인 고장 입력 시험으로 탐지합니다"와 "같은 사용자 권한으로 검사기·시험을 함께 수정하는 변조는 막지 않는다"를 함께 읽어, 검사기·렌더러만 바꾸고 시험 파일은 손대지 않는 변조를 방어 범위로 보았습니다. 제 가짜 검사기는 시험 파일을 하나도 바꾸지 않았으므로 방어 범위 안의 반례입니다.

**버린 해석.** "가짜가 해시 대조와 심볼릭 링크 검사를 하니 완전한 출력 위조는 아니다"라는 해석은 버렸습니다. 정책 YAML을 단 한 바이트도 해석하지 않고 실제 검사 모듈이 삭제된 상태이므로 정책 일관성 검사로서는 무의미합니다. 또 "12개 순열 시험이 고정 seed 37이라 예측 가능한 것은 재현성 설계다"라는 변호도 버렸습니다. 재현성은 seed를 출력하면 유지되므로 고정 seed의 대가를 정당화하지 못합니다.

**틀리면 깨지는 것.** 만약 오너가 "시험 입력이 고정돼 있어도 시험 파일을 손대지 않은 변조를 잡을 필요는 없다"고 P13⑥의 범위를 좁게 정한다면 D1의 심각도는 상에서 중으로 내려가고, 남은 결함(D2·D3·D4)만으로는 FAIL 대신 조건부 PASS가 가능합니다. 그 결정은 제 몫이 아니라 오너의 몫입니다.

**정상 통과 확인.** 검사기 정상 출력(exit 0, PASS, 22, SYNC PASS), acceptance CHECKED 5, mutation CHECKED 20(내부 계약 시험 62), 관문 메타 시험 20, semantic mutations 17, mechanism registry 23, AC-M 31, ci-step-integrity 14, 원칙 검사 34, docs-sot, git diff --check, Ruby/셸 문법, pre-push 전체 29개 검사 모두 exit 0. 22는 구조 6개와 값 16개의 합이며 실패 경로에서 18·1·0으로 실제 줄어드는 것을 확인했습니다. 파일 hard 600·함수 hard 100·PR diff 3000 한도 모두 준수(최대 파일 223줄, 변경 1607줄).

## 기술 상세와 증거 원문

### 시작 기록

```
Thu Sep 10 04:50:27 KST 2026
HEAD 74e183032352017b8ea8d205a58091b131d177b7
git status --porcelain=v1: (비어 있음)
기준 01495b3 대비 23 files changed, 1568 insertions(+), 39 deletions(-)
```
→ 해석: 검토 대상 HEAD가 지시된 커밋과 일치하고 작업트리는 깨끗했습니다. 검토 종료 시(05:12:54) 재확인해도 동일했습니다.

### 결함 목록

**D1 — 심각도 상. 원문 제목: "출력만 꾸민 checker는 독립적인 고장 입력 시험으로 탐지합니다"(docs/engineering/pr37-resolution-goal-2026-09-10.md:39, T 계약 문장)가 반증됨.**

원인: 부정 시험의 입력이 전부 고정돼 있습니다. `scripts/verify/work-unit-policy-contract-test.rb:72`(순열 난수를 `Random.new(37)`로 고정하는 줄)와 `:83`(12회 순열 생성) 때문에 "정상으로 통과해야 하는 입력"의 바이트가 실행마다 같고, `:64`(진단 문자열을 `include?`로 부분 일치하는 줄)와 `scripts/acceptance-work-unit-policy-mutations.sh:42`(`grep -q "$pattern"`로 부분 일치하는 줄)는 모든 진단을 한꺼번에 찍는 출력을 허용합니다. 따라서 "알려진 13개 해시면 PASS, 아니면 모든 진단과 FAIL"만 하는 검사기가 시험 전체를 통과합니다.

사업 영향: 정책 검사기를 속 빈 껍데기로 바꿔 main에 올려도 로컬 pre-push와 CI 29스텝이 전부 초록입니다. 이 상태에서는 CRLF나 키 순서만 다른 정당한 정책 입력도 거부되고, 검사기가 정책 의미를 본다는 문서 주장이 거짓이 됩니다. 단, 이 가짜만으로 잘못된 정책값(예: 상한 6)을 통과시킬 수는 없습니다. mutation 스크립트의 치환 패턴이 정본값을 암묵적으로 고정하고 있어 값 변경은 시험 수정 없이는 통과하지 못함을 함께 확인했습니다(반증 기록 R3 참조).

명령(격리 사본, 시각 05:09:12~05:12:11, 사본은 mktemp 디렉터리에 `git ls-files` 전체를 복사해 `git init` 후 실행, git 환경변수 unset):

```
# 가짜 검사기·렌더러로 교체하고 실제 모듈 삭제
cp /tmp/v1-whitelist-fake-checker.rb scripts/verify/check-work-unit-policy.rb   # 86줄, YAML 파싱 없음
rm scripts/verify/work_unit_policy.rb
bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-policy.sh
bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-policy-mutations.sh
ruby scripts/verify/work-unit-policy-gates-test.rb
bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh
bash scripts/verify/check-mechanism-registry.sh; bash scripts/verify/check-ci-step-integrity.sh
bash scripts/acceptance-principles-check.sh
```

전체 출력:

```
fake syntax OK
scripts/verify/check-work-unit-policy.rb
scripts/verify/render-work-unit-policy.rb
scripts/verify/work-unit-policy-contract-test.rb
scripts/verify/work-unit-policy-gates-test.rb
--- proof the fake does not parse: CRLF policy (real checker PASS) →
VERDICT: FAIL
--- acceptance:
OK(run-acceptance): scripts/acceptance-work-unit-policy.sh — 판정 6건, CHECKED 5
--- mutations(+contract):
CHECKED: 62
VERDICT: PASS
CHECKED: 20
VERDICT: PASS
OK(run-acceptance): scripts/acceptance-work-unit-policy-mutations.sh — 판정 84건, CHECKED 20
--- gates:
CHECKED: 20
VERDICT: PASS
--- semantic mutations:
PASS: Work Unit 검사·CI 무력화 차단 — 격리 실행 반례 exit=0
OK(run-acceptance): scripts/acceptance-semantic-mutations.sh — 판정 39건, CHECKED 17
--- registry/ci-step:
CHECKED: 23
CHECKED: 31
--- principles check:
VERDICT: PASS
```
→ 해석: work_unit_policy.rb가 존재하지 않고(ls-files 목록에 없음) CRLF 정책을 거부하는 등 정책을 해석하지 않는 가짜인데도, 이 PR이 추가하거나 배선한 관문 전부와 기존 관문이 PASS를 냈습니다. 가짜 본문은 /tmp/v1-whitelist-fake-checker.rb에 보존했습니다. 핵심 구조는 다음과 같습니다.

```ruby
KNOWN = %w[ <정본 YAML 해시 1개 + seed 37 순열 12개 해시> ]
def ok?(path, hashes)
  return false if File.symlink?(path) || !File.file?(path)
  hashes.include?(Digest::SHA256.hexdigest(File.binread(path)))
rescue SystemCallError; false; end
if ok?(pol, KNOWN) && ok?(doc, [DOCHASH]) then puts "VERDICT: PASS\nPOLICY_CHECKED: 22\nDOCUMENT_SYNC: PASS"; exit 0 end
puts "VERDICT: FAIL"; puts ALL   # 모든 진단 문자열을 한 줄씩 전부 출력
puts "POLICY_CHECKED: 22\nDOCUMENT_SYNC: FAIL"; exit 1
```

설계 지적:
- 무엇을: 순열 시험의 seed를 실행마다 달리 하고(출력에 seed 기록) 값 변조도 무작위 정수·무작위 키 이름으로 생성하며, 진단은 부분 일치가 아니라 "기대 진단 집합과 정확히 같음"으로 대조합니다.
- 왜: 미리 알 수 없는 정상 입력이 하나라도 있으면 해시 화이트리스트는 원리적으로 불가능해지고, 검사기가 YAML을 실제로 해석해야만 통과합니다.
- 버린 길: 시험 케이스를 더 늘리는 것. 유한한 고정 목록은 얼마를 늘려도 화이트리스트로 덮입니다.
- 대가: 실패 재현 시 seed를 지정하는 인수 하나가 필요합니다.
- 되돌리기: seed 인수 기본값을 37로 고정하면 현재와 동일합니다.

**D2 — 심각도 중. 원문 제목: "실패: exit 1, VERDICT FAIL, 원인과 실제 처리 수"(pr37-resolution-goal 문서:36) 중 "실제 처리 수"가 어떤 시험에서도 검증되지 않음.**

원인: `scripts/verify/check-work-unit-policy.rb:38`(실패 경로에서 처리 수를 출력하는 줄)을 상수 22로 바꿔도 통과합니다. 계약 시험은 성공 경로에서만 22를 정확히 요구하고(`work-unit-policy-contract-test.rb:42`), 실패 경로에서는 진단 문자열만 봅니다.

사업 영향: RED 커밋 68a016b의 제목 "고정 검사 건수의 실패를 먼저 증명한다"가 약속한 것과 달리, 실패 시 "몇 개를 실제로 검사했는가"는 여전히 꾸밀 수 있습니다. P20(0건 처리 통과 의심)의 취지가 실패 경로에는 미치지 않습니다.

명령(격리 사본, 05:02:30):

```
# 실패 경로 `puts "POLICY_CHECKED: #{checked}"` → `puts "POLICY_CHECKED: 22"` 로 치환
printf 'version: 1\n' > /tmp/v1-bad.yaml
ruby scripts/verify/check-work-unit-policy.rb /tmp/v1-bad.yaml docs/sot/work-unit-policy.md
bash scripts/acceptance-work-unit-policy.sh | tail -2
bash scripts/acceptance-work-unit-policy-mutations.sh | grep -E "^FAIL|CHECKED|VERDICT"
ruby scripts/verify/work-unit-policy-gates-test.rb | grep -E "^FAIL|CHECKED|VERDICT"
```

```
 scripts/verify/check-work-unit-policy.rb | 2 +-
--- fake checker on schema failure:
VERDICT: FAIL
POLICY_SCHEMA_INVALID: root
POLICY_CHECKED: 22
DOCUMENT_SYNC: FAIL
exit=1
--- acceptance:
CHECKED: 5
VERDICT: PASS
--- mutations(+contract):
CHECKED: 62
VERDICT: PASS
CHECKED: 20
VERDICT: PASS
--- gates:
CHECKED: 20
VERDICT: PASS
```
→ 해석: 루트 구조 실패는 실제로 1건만 처리했는데(원본 검사기 출력은 `POLICY_CHECKED: 1`) 22를 찍어도 세 시험 모두 PASS입니다.

**D3 — 심각도 중. 원문 제목: `scripts/verify/work-unit-policy-gates-test.rb:69` "fake output can fool positive gate (known boundary)" 단언이 관문의 약점을 통과 조건으로 고정함.**

원인: 이 줄은 가짜 PASS22 검사기가 `acceptance-work-unit-policy.sh`를 통과해야만(`rc == 0`) 메타 시험이 PASS입니다. 알려진 경계를 기록하는 것과 그 경계가 유지되어야 한다고 단언하는 것은 다릅니다.

사업 영향: 누군가 긍정 관문에 고장 입력 1건을 추가해 강화하면, 메타 시험이 FAIL하고 그것을 부르는 `acceptance-semantic-mutations.sh`가 FAIL해 CI 전체가 빨개집니다. P13 "검사는 약화될 수 없다"의 반대 방향인 "검사를 강화할 수 없다"가 기계로 고정된 셈입니다.

명령(격리 사본, 05:02:30~05:05:41): acceptance 스크립트의 CHECKED 출력 직전에 `ruby "$CHECKER" /dev/null "$DOCUMENT"`가 exit 1·VERDICT FAIL인지 확인하는 10줄을 추가하고 커밋 후 실행.

```
 scripts/acceptance-work-unit-policy.sh | 10 ++++++++++
PASS: checker rejects invalid input
CHECKED: 6
VERDICT: PASS
--- gates test against strengthened acceptance:
FAIL: fake output can fool positive gate (known boundary)
FAIL: checker accepted invalid input
CHECKED: 6
VERDICT: FAIL
CHECKED: 20
VERDICT: FAIL
--- semantic mutations in this copy (uses gates test):
FAIL: Work Unit 검사·CI 무력화 차단 — 격리 실행 반례 exit=1
CHECKED: 17
VERDICT: FAIL
```
→ 해석: 강화된 관문은 단독으로 PASS(CHECKED 6)인데, 메타 시험과 semantic mutations가 그 강화를 결함으로 판정했습니다.

설계 지적:
- 무엇을: 69행 단언을 "가짜 PASS22는 긍정 관문 또는 mutation 관문 중 최소 하나에서 반드시 거부된다"로 바꿉니다.
- 왜: 메타 시험의 목적은 무력화 저항이지 특정 관문의 무능을 보증하는 것이 아닙니다.
- 버린 길: 69행 삭제. 그러면 PASS22가 어디서도 잡히지 않아도 PASS가 되므로 더 나쁩니다.
- 대가: 없음. 현재 동작에서는 71행이 그대로 거부를 증명합니다.
- 되돌리기: 단언 한 줄 교체이므로 한 커밋으로 원복 가능합니다.

**D4 — 심각도 중. 원문 제목: `work-unit-policy-contract-test.rb:57` "alias" 케이스가 별칭 거부를 실제로 검증하지 않음.**

원인: 이 케이스는 `alias: *t`라는 루트 키를 덧붙이므로 별칭 처리와 무관하게 "알 수 없는 루트 키"로 실패합니다. 기대 패턴도 `POLICY_`뿐입니다. `work_unit_policy.rb:62`(`aliases: false`로 별칭을 막는 줄)를 `aliases: true`로 바꿔도 62건 전부 PASS입니다.

사업 영향: T가 요구한 "alias 실패"를 지키는 코드는 있지만, 그 코드가 사라져도 아무 시험이 알리지 않습니다. P5③ 표본 뮤테이션이 살아남은 사례입니다.

명령(격리 사본, 04:56:44):

```
# work_unit_policy.rb의 `aliases: false)` → `aliases: true)` 치환 후
ruby scripts/verify/work-unit-policy-contract-test.rb | grep -E "^FAIL|CHECKED|VERDICT"
```

```
### FAKE-ALIAS: aliases: true
--- contract test:
CHECKED: 62
VERDICT: PASS
```

대조군(원본 검사기, 05:02:16, `version: &v 1` + `claims_per_unit: *v`처럼 의미가 같은 순수 별칭 입력):

```
VERDICT: FAIL
POLICY_YAML_INVALID: Unknown alias: v
POLICY_CHECKED: 0
DOCUMENT_SYNC: FAIL
exit=1
```
→ 해석: 원본 검사기는 별칭을 올바르게 거부하지만, 시험은 그 거부가 사라져도 감지하지 못합니다. 위 대조군 입력을 시험 케이스로 넣으면 판별력이 생깁니다.

**D5 — 심각도 하. 원문 제목: pr37-resolution-goal 문서:24 "전체 출력은 증거 장부에 보존합니다" 및 :80 "docs/engineering/pr37-resolution-evidence-2026-09-10.md에 연결합니다"의 대상 파일이 없음.**

원인: `ls docs/engineering/pr37-resolution-evidence-2026-09-10.md` → "No such file or directory". `.omx/artifacts/...` 참조도 `.git/info/exclude`로 제외된 로컬 전용 경로입니다.

사업 영향: 추적되는 문서가 존재하지 않는 증거 장부를 근거로 제시합니다. P14④(실행하지 않은 것을 기록 금지)와 같은 결의 문제이며, 다음 세션이 근거를 찾을 수 없습니다.

**D6 — 심각도 하. 원문 제목: YAML 병합 키 `<<`가 "알 수 없는 키"로 거부되지 않음.**

원인: `work_unit_policy.rb:172`(정확한 키 집합을 검사하는 줄)는 Psych가 병합을 끝낸 뒤의 해시를 봅니다. `<<: {claims_per_unit: 2}` 뒤에 `claims_per_unit: 1`을 두면 사람 눈에는 2가 보이지만 기계는 1로 읽어 PASS입니다.

사업 영향: 정책 의미는 바뀌지 않으므로 우회는 아니지만, 원문 YAML과 생성 문서가 다른 숫자를 보여 줄 수 있어 "YAML이 유일한 정본"이라는 읽기 신뢰를 깎습니다. `walk_duplicates`에서 키 `<<`를 거부하면 닫힙니다.

명령·출력(04:56:20):

```
### merge key << with shadowed claims 2 + explicit 1
VERDICT: PASS
POLICY_CHECKED: 22
DOCUMENT_SYNC: PASS
exit=0
```

**D7 — 심각도 하. 원문 제목: "런타임 부재는 NOT_RUN/exit 2"(goal 문서:36)가 셸 계층에서는 FAIL/exit 1로 나타남.**

원인: `scripts/acceptance-work-unit-policy.sh:41`(ruby를 호출하는 줄)은 ruby 존재를 확인하지 않아 exit 127을 FAIL로 보고합니다. Ruby 스크립트 안에서 Ruby 부재를 NOT_RUN으로 낼 수는 없으므로 셸 계층이 담당해야 합니다.

사업 영향: P3의 3상태 구분이 흐려질 뿐 통과로 새지는 않습니다(fail-closed).

명령·출력(05:02:16, bash·git·grep 등만 있는 PATH):

```
PATH=$T/bin $T/bin/bash scripts/acceptance-work-unit-policy.sh
FAIL: structured policy checker — exit=127
scripts/acceptance-work-unit-policy.sh: line 41: ruby: command not found
CHECKED: 5
VERDICT: FAIL
exit=1
```

**D8 — 심각도 하. 원문 제목: `docs/sot/git-workflow.md:3` "최종 갱신: 2026-08-21"이 2026-09-10 변경과 불일치.**

기준 main은 2026-08-08이었고 이 PR이 본문을 바꾸면서 날짜를 8월 21일로 적었습니다. `docs/sot/INDEX.md:5`의 "P1~P22"는 기준 main에도 있던 기존 불일치라 이 PR의 회귀로 세지 않습니다.

### 계약 항목별 실행 결과

| 계약 항목 | 명령 | 결과 |
|---|---|---|
| 정수 5.0·문자열 "5"·null·"false"·48.0·1.0·"true" 거부 | 계약 시험 + 제 추가 입력 7건 | 전부 exit 1, POLICY_VALUE_INVALID |
| `!!float 5` 거부 / `!!int "5"`·`0x5`·`0b1`·`yes`·`off` 수용 | 제 입력 | 거부 1건, 수용 4건 모두 렌더 바이트 동일 |
| 객체 키 무순서·목록 순서 유지 | 순열 12회, 역순·중복 항목 | 순열 PASS, 역순·중복 항목 FAIL |
| 중복 키(루트·중첩)·미지 키·복합 키·심볼 키·날짜 값 | 제 입력 | 전부 exit 1 |
| 빈 파일·공백만·주석만·null 문서·명시적 빈 문서·여러 문서·잘못된 UTF-8·BOM | 제 입력 | 전부 exit 1 |
| 링크·누락·디렉터리·읽기불가·/dev/null·FIFO·빈 문자열 경로 | 제 입력 | 전부 exit 1, FILE_INVALID/MISSING/UNREADABLE |
| 모듈 심볼릭 링크·인수 초과 → NOT_RUN exit 2 | 제 입력 | 확인. 모듈 문법 오류는 exit 1 트레이스백(NOT_RUN 아님, fail-closed) |
| renderer 잘못된 입력 stdout 빈값·stderr FAIL | 제 입력 | rc=1, stdout 길이 0 |
| 정책+문서 동시 변조 거부 / fakechecker 5종 | 메타 시험 | PASS(단, D1의 화이트리스트형은 통과) |
| CI 스텝 삭제·echo·조건·오류무시 | 메타 시험 | 4종×2 스크립트 거부 |

→ 해석: `yes`·`off`·`0x5`를 정수·불리언으로 받는 것은 구현자가 "텍스트 형식"이 아니라 "YAML 의미"를 기준으로 삼은 결과입니다. T의 "정확한 형식"을 텍스트로 읽는다면 계약 차이가 되므로 오너 확인이 필요합니다.

### 반증 기록(깨려다 실패한 것)

- **R1 문서 비교 생략.** 검사기에서 문서 비교를 `false`로 바꾸자 mutation 관문의 문서 변조 3건이 FAIL로 잡았습니다(04:56:44).
- **R2 `eql?` → `==` 완화.** 5.0을 5로 받게 하자 계약 시험 "float units"·"float version"이 FAIL로 잡았습니다.
- **R3 중복 키 검출 제거.** mutation "중복 키 추가"와 계약 시험 "extra YAML document"·"duplicate nested key"가 FAIL로 잡았습니다.
- **R4 심볼릭 링크 허용.** 계약 시험 "symlink policy.yaml"·"symlink document.md"가 FAIL로 잡았습니다.
- **R5 처리 수 실제 계수.** high_risk 구조 실패 시 18, 루트 실패 시 1, 값 오류 2건 시 22를 출력해 실행 계수임을 확인했습니다.
- **R6 semantic-mutations·pre-push 전체.** 실제 저장소에서 CHECKED 17 PASS, pre-push 29개 검사 exit 0(05:08:36).
- **R7 nested VERDICT 혼동.** run-acceptance.sh는 마지막 CHECKED 줄만 취하므로 내부 시험의 PASS 줄이 외부 FAIL을 가리지 않음을 코드와 실행으로 확인했습니다.

### 범위 주장 점검

work-unit-policy.md, git-workflow.md, verification-commands.md, mechanism-registry.yaml에서 PR 개수·브랜치 나이·작업 장부의 자동 집행이나 고위험 경로 매처 구현을 주장하는 문장은 찾지 못했습니다. verification-commands.md:30은 오히려 자동 강제가 아님을 명시합니다. 복원된 methodology 문서의 `POLICY_CHECKED 19` 잔존(:120)은 :78에서 "과거 로그는 당시 값으로 보존"이라고 선언해 모순으로 세지 않았습니다.

### 검토 종료 상태

```
Thu Sep 10 05:12:54 KST 2026
git status --porcelain: (비어 있음)
HEAD 74e183032352017b8ea8d205a58091b131d177b7
보존 파일: /tmp/v1-whitelist-fake-checker.rb (86줄)
```
→ 해석: 소스·인덱스·브랜치를 변경하지 않았고, 모든 반례는 mktemp 사본에서만 실행했습니다.
