# Claude 1차 적대검증 원문

실행 명령 전문:

```text
env -u ANTHROPIC_API_KEY claude -p --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands < docs/engineering/verification-authority-claude-prompt-2026-08-19.md
```

→ 사용자 지시의 `env -u ANTHROPIC_API_KEY claude -p`를 유지하면서 불필요한 MCP 서버만 비활성화했습니다. Claude 프로세스 종료값은 0이었습니다.

## 판정 원문

VERDICT: FAIL

# 결론

가장 중요한 결정 사항부터 말씀드리겠습니다. **"검증기 자신이 고장 나서 아무 검사도 안 하고 무조건 통과라고 거짓말해도 잡아내는가"라는 첫 번째 공격에 대해, 이 구현은 실제로는 잡아내지 못합니다.** 검증기 파일(`scripts/verify/verification_authority.rb`) 맨 위에 한 줄(`exit 0`, "무조건 성공 종료")만 몰래 끼워 넣으면, 로컬에서 커밋할 때도 안 걸리고, `git push`할 때(pre-push 훅)도 "정상"이라고 표시되며, 아무 경고 없이 원격 저장소로 올라갑니다. 문서와 자체 테스트 보고서는 이 공격이 "BLOCKED"(차단됨)라고 자랑스럽게 표시하지만, 그건 검증 도구가 자기 자신을 상대로 좁게 짜놓은 셀프테스트에서만 그런 것이고, 실제로 사람이 커밋하고 푸시하는 경로에서는 그 방어가 작동하지 않는다는 것을 제가 직접 재현해서 확인했습니다. 유일하게 이 사고를 뒤늦게 알아챌 수 있는 지점은 GitHub Actions(원격 자동 검사 서버)에서, 결과 파일이 안 만들어져서 "증거 업로드" 단계가 실패하는 것뿐인데, 이 저장소는 요금제 제한 때문에 "CI가 빨간불이면 병합을 막는다"는 장치 자체가 꺼져 있는 상태(`UNAVAILABLE`)이므로, 그 빨간불도 사람이 눈으로 봐야만 의미가 있습니다. 즉 "검증기가 스스로 고장 났다는 사실을 스스로 감출 수 없게 한다"는 이번 작업의 핵심 목표 하나가, 적어도 로컬 단계에서는 원래 막으려던 바로 그 방식(자기선언만으로 통과)으로 뚫립니다.

두 번째로 말씀드릴 것은 심각도가 훨씬 낮은 항목입니다. 검증 스크립트에 특정 옵션(`--no-mutations`, "고장 주입 검사를 생략하라"는 뜻)을 주고 결과 파일을 만들면, 실제로는 고장 주입 검사를 한 건도 안 돌렸는데도 결과 파일에는 "18건 중 17건 차단, 생존 0건"이라는 숫자가 마치 방금 측정한 것처럼 박혀 나옵니다. 다만 이 조합은 실제 CI나 pre-push 어디에서도 자동으로 쓰이지 않으므로, 지금 당장 사람을 속일 경로는 없습니다. 사람이 나중에 수동으로 이 옵션을 써서 확인 파일을 만들면 그 사람이 속을 수 있다는 잠재 위험입니다.

세 번째로, "검증 장치를 지키는 파일 목록(manifest)과 그 목록을 검사하는 코드(checker)를 동시에 약화시키면 보호를 무력화할 수 있는가"라는 공격은, 문서가 이미 정직하게 "그렇다, 이건 구조적 한계이고 외부 강제라고 부르지 않는다"라고 밝히고 있었고, 제가 직접 재현해서 그 한계가 진짜로 존재함을 확인했습니다. 이건 숨겨진 결함이 아니라 미리 고지된 한계이며, 사업적으로는 "이 파일들을 건드릴 수 있는 사람은 이 검증 장치 전체를 우회할 수 있다"는 사실로 이해하시면 됩니다. GitHub 쪽의 진짜 외부 강제(branch protection·ruleset)는 오늘 날짜(2026-08-19) 기준으로 제가 직접 GitHub API를 조회해 403(요금제 제한으로 접근 불가)임을 재확인했고, 문서는 이를 "UNAVAILABLE"(사용 불가)이라고 정확히 표기하고 있어 과장이 없습니다.

나머지 공격 항목들 — 과거 SHA 재사용, 워크플로/필수 체크 이름 위조, merge-group SHA 관계 오검증, 롤백 중 상태 삭제, LLM 보고서만으로 VERIFIED 발급, 배선이 문자열 언급만으로 통과하는지 — 은 제가 직접 격리된 복제 저장소에서 재현했고, 모두 설계대로 방어되고 있음을 확인했습니다.

# 판단 근거

가장 먼저 부딪힌 갈림길은 "도구가 스스로 '통과했다'고 보고하는 숫자를 그대로 믿을 것인가, 아니면 그 숫자가 실제로 무엇을 측정했는지 코드를 읽어 재구성할 것인가"였습니다. 사용자 지시에 "LLM의 판정은 정책 게이트 입력으로 인정하지 마라"는 원칙이 명시되어 있었고, 같은 논리를 검증 도구 자신의 자기 보고("MUTATIONS: total=18 blocked=17 survived=0")에도 적용해야 한다고 판단했습니다. 그래서 `run-verification-authority-mutations.sh`가 "BLOCKED"라고 표시한 17건 중, 가장 핵심적인 1번 공격(검증기 자체 무력화)에 대해서는 도구의 자체 판정을 그대로 받아들이지 않고, 실제 운영 경로(`scripts/acceptance-verification-authority.sh` → `hooks/pre-push`)를 거쳐서 같은 공격을 처음부터 다시 재현했습니다. 그 결과 도구의 자체 판정과 실제 운영 경로의 결과가 달랐습니다 — 이것이 이번 판정을 FAIL로 정한 결정적 근거입니다.

이 해석을 고른 이유는, 도구 내부의 "mutation_group_files" 코드(아래 기술 상세 참고)가 검사하는 것은 "격리된 복사본에서 `ruby verification_authority.rb contract-self-test`를 직접 실행했을 때 출력에 특정 문자열이 있는가"라는 매우 좁은 조건이었기 때문입니다. 이 조건은 정의상 항상 참이 되기 쉬운 자기충족적 검사(주입한 고장이 그 즉시 출력 문자열을 없애 버리므로, "문자열이 없다"는 사실을 확인하는 것 자체가 트리비얼함)였고, 실제 소비자인 `verify_all`(전체 검증 실행 함수)과 `hooks/pre-push`가 그 문자열을 조금이라도 확인하는지는 별도로 검증해야 했습니다. 코드를 읽어보니 두 소비자 모두 종료 코드(exit code)만 보고 출력 내용은 보지 않았습니다(`hooks/pre-push`는 아예 `>/dev/null 2>&1`로 출력을 버립니다). 이 시점에서 "도구의 자체 판정이 실제 방어를 과장하고 있을 가능성이 크다"고 보고, 버리지 않고 직접 격리 재현으로 넘어갔습니다.

버린 해석은 "도구가 이미 이 공격을 카탈로그에 넣고 BLOCKED라고 표시했으니 충분하다"는 해석입니다. 이걸 버린 이유는, 그 표시가 사실은 "고장 주입 검사 하네스가 자기 자신의 좁은 조건문을 만족시켰다"는 뜻일 뿐, "실제 커밋·푸시 경로에서 이 고장이 사람 눈에 보이는 형태로 걸린다"는 뜻이 아니었기 때문입니다. 이 둘을 구분하지 않으면 정확히 이번 작업이 막으려던 문제(자기선언 검증을 신뢰하는 것)를 검증 도구 자신이 저지르게 됩니다.

이 판정이 틀렸다면 무엇이 깨지는가: 만약 제가 잘못 재현했거나 pre-push가 실제로는 이 고장을 잡아낸다면, 이 보고서의 최상위 결론(FAIL)이 뒤집혀야 하고 심각도도 재조정해야 합니다. 그래서 아래 기술 상세에 재현 명령과 출력을 전부 남겼으니, 재현이 정확한지 직접 다시 돌려 확인하시길 권합니다. 재현은 원본 작업공간이 아니라 `mktemp`로 만든 임시 복제본에서만 수행했고, 작업이 끝난 뒤 `git status --porcelain`으로 원본이 그대로임을 확인했습니다.

# 기술 상세

## 건너뛴 것 / 확인 못 한 것 (판정 앞부분에 명시)

- ※ 17개 고장 주입(mutation) 케이스 중 대부분(항목 2, 4~9, 14 관련 케이스)은 `run-verification-authority-mutations.sh`의 자체 보고를 신뢰하되, `mutations.rb`의 해당 케이스 소스 코드를 직접 읽어 "트리비얼하게 항상 통과하는 검사"가 아님을 확인하는 방식으로 검증했습니다. 1번 공격(검증기 무력화)만 별도로 실제 운영 경로 전체를 독립적으로 재현했습니다 — 이것이 문제를 발견한 항목이라 나머지도 같은 방식으로 전수 재현하는 것이 이상적이었지만, 시간상 3번(manifest+checker 동시 약화)과 `--no-mutations` 조합만 추가로 독립 재현했습니다.
- ※ CI(GitHub Actions) 자체를 실제로 실행해보지는 못했습니다(원격에 새 커밋이 없으므로 애초에 실행 불가). CI에서 "증거 업로드 실패로 그 자체가 빨간불이 된다"는 것은 `.github/workflows/verify.yml`의 `if-no-files-found: error` 설정(actions/upload-artifact 공식 문서 기준 동작)에 대한 코드 판독이며, 실제 GitHub Actions 실행으로 재확인하지는 않았습니다.
- 확인한 사실(추정 아님): branch protection·repository ruleset이 오늘(2026-08-19) 기준 HTTP 403인 것, CODEOWNERS 부재, 원본 작업공간이 이번 조사로 전혀 바뀌지 않은 것 — 모두 명령 재실행으로 직접 확인했습니다.

## 항목 1 — 검증기 자체 무력화 (가장 심각, CRITICAL)

**심각도: CRITICAL — 방치 시 결과:** 저장소 쓰기 권한이 있는 누구나(또는 권한이 탈취된 계정이) 검증기 파일 맨 위에 한 줄만 넣으면, 이후의 모든 로컬/CI 검증이 "무조건 통과"로 둔갑하고, 이 사실이 로컬에서는 전혀 드러나지 않습니다.

도구 자신의 판정부터 보면 이렇게 "차단됨(BLOCKED)"이라고 나옵니다.

```
BLOCKED: verifier_early_exit_zero
  broke: verifier line 2 exits zero before checking
  command: ruby scripts/verify/verification_authority.rb contract-self-test
  actual_exit: 0
  expected: exit 0 without output contract must be rejected by outer runner
  survived: false
```
→ 뭘 시켰나: `bash scripts/verify/run-verification-authority-mutations.sh`(고장 주입 검사 실행기)를 그대로 돌렸습니다. → 뭐가 나왔나: "BLOCKED"(막혔다)로 표시됩니다. → 좋은 소식인가 나쁜 소식인가: 표면적으로는 좋은 소식처럼 보이지만, 아래에서 보듯 이 판정 자체가 좁은 자기검사일 뿐이라 실제로는 나쁜 소식입니다.

이 판정의 근거 코드는 `scripts/verify/verification_authority/mutations.rb:65-72`입니다.

```ruby
when 'verifier_early_exit_zero'
  path = File.join(copy, 'scripts/verify/verification_authority.rb')
  lines = File.readlines(path).insert(1, "exit 0\n")
  File.write(path, lines.join)
  out, _err, status = run_mode(copy, 'contract-self-test')
  result('ruby scripts/verify/verification_authority.rb contract-self-test',
         'exit 0 without output contract must be rejected by outer runner', status,
         !(status && status.success? && out.include?('CONTRACT_SELF_TEST:')))
```
`scripts/verify/verification_authority/mutations.rb:70-72` — 이 줄은 "격리 복사본에서 `contract-self-test`를 직접 실행했을 때, 종료코드가 0이면서 동시에 출력에 `CONTRACT_SELF_TEST:` 문자열이 있는가"만 확인합니다. `exit 0`을 파일 두 번째 줄에 넣으면 그 즉시 프로세스가 죽으므로 출력이 비고, 이 조건은 항상(정의상) 거짓이 되어 "blocked=true"가 됩니다. 즉 이 검사는 "고장이 실제 운영 경로에서 잡히는가"가 아니라 "직접 호출했을 때 출력 문자열이 없다는 사실을 확인할 수 있는가"만 증명합니다.

실제 소비자 코드인 `scripts/verify/verification_authority.rb:512-521`(`verify_all` 함수)을 보면:
```ruby
contract['requirements'].each do |entry|
  next if !include_mutations && entry['id'] == 'VA-004'
  out, err, status = command(entry['verifier'], root)
  rc = status ? status.exitstatus : 255
  captured << "$ #{entry['verifier']}\n#{out}#{err}EXIT=#{rc}\n"
  raise "required verifier #{entry['id']} failed exit=#{rc}" unless status && status.success?
```
`scripts/verify/verification_authority.rb:521` — 이 줄이 유일한 성공/실패 판정 기준인데, `status.success?`(종료코드 0인지)만 봅니다. 출력 문자열은 나중에 `puts captured`로 화면에 찍기만 할 뿐, 판정에는 전혀 쓰이지 않습니다.

`hooks/pre-push`(로컬 push 차단 훅)의 실제 실행부는 이렇습니다.
```
SECRET_PATTERNS_FILE= bash "$c" >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then block "$c exit=$rc"; else printf '  ok  %s\n' "$c"; fi
```
`hooks/pre-push` (176번째 줄 부근) — 출력을 `/dev/null`로 완전히 버리고, 종료코드만 봅니다.

이 두 코드를 근거로, 저는 원본을 건드리지 않고 `mktemp` 임시 저장소에 전체 복제본을 만든 뒤 **직접** 같은 고장을 주입하고 실제 운영 경로 전체(`verify-all` → `acceptance-verification-authority.sh` → 사실상 `hooks/pre-push`가 부를 경로)를 재현했습니다.

```
=== 1) direct verify-all (as acceptance script would run it) ===
EXIT=0
report file exists? NO
=== 2) via acceptance-verification-authority.sh (as pre-push glob calls it, no args) ===
acceptance script EXIT=0
```
→ 뭘 시켰나: 임시 복제본에서 `verification_authority.rb` 2번째 줄에 `exit 0`을 심고, ①결과 파일 생성 옵션을 준 `verify-all`을 직접 실행 ②pre-push가 실제로 부르는 `acceptance-verification-authority.sh`를 인자 없이 실행. → 뭐가 나왔나: 둘 다 종료코드 0("성공"), 결과 파일은 아예 생성되지 않음, 어떤 오류 메시지도 출력 안 됨. → 좋은 소식인가 나쁜 소식인가: 나쁜 소식입니다 — pre-push가 이 스크립트를 부르면 rc=0이므로 "ok"로 처리되고, push가 그대로 원격까지 올라갑니다.

이걸 잡을 수 있는 유일한 지점은 CI의 마지막 두 단계뿐입니다(`.github/workflows/verify.yml:189-199`):
```
189	      - name: 검증 권한·SHA 귀속 후보 증거 생성
192	        run: bash scripts/acceptance-verification-authority.sh --output "verification-results/verification-authority-${GITHUB_SHA}.json"
194	      - name: 검증 권한 후보 증거 보관
195	        uses: actions/upload-artifact@v4
199	          if-no-files-found: error
```
`.github/workflows/verify.yml:192` — 증거 파일을 만드는 실행 줄. `:199` — 파일이 없으면 이 업로드 단계 자체를 에러로 처리하는 설정. 검증기가 고장 나 있으면 192번 줄은 "성공"(exit 0)하지만 파일을 안 만들므로, 195번 줄의 업로드 단계가 실패해 CI 전체가 빨간불이 됩니다. 이것은 실재하는 방어이지만, 이미 확인했듯 이 저장소는 branch protection·ruleset이 `UNAVAILABLE`(요금제 제한 403)이라 **CI 빨간불이 병합을 실제로 막지 못합니다.** 즉 사람이 CI 화면을 눈으로 보고 알아채야만 이 사고가 잡힙니다 — pre-commit·pre-push라는 "자동" 방어선은 이 특정 공격에 대해 전혀 작동하지 않습니다.

`hooks/pre-commit`도 확인했으나 `verification_authority`라는 문자열도, 내용 검증 로직도 전혀 없어 커밋 단계에서도 잡히지 않습니다.

## 항목 2 — 낮은 심각도, `--no-mutations`와 `--output` 조합의 허위 수치 (MEDIUM, 현재는 도달 불가능한 경로)

**심각도: MEDIUM — 방치 시 결과:** 지금 당장 자동 경로에서 악용되지는 않지만, 나중에 누군가 수동으로 이 옵션 조합을 써서 산출물을 남기면, 실제로 고장 주입 검사를 한 건도 안 돌렸는데도 "18건 중 17건 차단"이라는 숫자가 실측치처럼 박혀 사람을 오도할 수 있습니다.

```
$ ruby scripts/verify/verification_authority.rb verify-all --no-mutations --output verification-results/result.json
...
"mutation_total": 18,
"mutation_blocked": 17,
"mutation_survived": 0,
"normal_controls": 1,
```
→ 뭘 시켰나: 고장 주입 검사를 생략(`--no-mutations`)하면서 결과 파일도 함께 요청. → 뭐가 나왔나: 실제로는 VA-004(고장 주입 검사)를 건너뛰었는데도, JSON에는 마치 18건을 다 실행해서 17건을 막았다는 숫자가 그대로 박힙니다. → 좋은 소식인가 나쁜 소식인가: 나쁜 소식이지만 영향 범위는 좁습니다.

근거 코드는 `scripts/verify/verification_authority.rb:523-527`입니다.
```ruby
mutation_summary = if include_mutations
                     mutation_summary_from(captured)
                   else
                     { 'total' => 18, 'blocked' => 17, 'survived' => 0, 'controls' => 1 }
                   end
```
`scripts/verify/verification_authority.rb:526` — 이 줄이 "생략했다"는 표시 없이 실측치와 동일한 모양의 하드코딩 숫자를 그대로 채워 넣습니다. 다만 확인 결과 `.github/workflows/verify.yml:192`(CI)도, `hooks/pre-push`가 부르는 무인자 호출도 `--no-mutations`를 쓰지 않으므로, 현재 이 저장소의 자동화된 두 경로 어디에도 이 조합이 실제로 쓰이지 않습니다. 즉 지금은 "지뢰가 묻혀 있지만 아무도 밟는 경로가 없는" 상태입니다.

## 항목 3 — manifest·checker 동시 약화 (정직하게 고지된 구조적 한계, 재현으로 실재 확인)

**심각도: 정보성(경계 확인) — 방치 시 결과:** 없음(이미 고지되어 있고 설계 트레이드오프로 받아들여진 상태). 다만 사업적으로 "이 파일들에 쓰기 권한이 있는 사람은 이 보호 장치 전체를 우회할 수 있다"는 사실 자체는 인지하고 계셔야 합니다.

문서 `docs/sot/verification-authority.md:94`가 이렇게 명시합니다: "manifest와 checker를 함께 약화하는 지정 공격은 제3의 계약 목록이 잡지만, 동일 권한 사용자가 세 목록을 모두 바꿀 수 있는 구조적 한계는 남는다. 이 한계를 외부 차단이라고 표현하지 않는다." — 이 줄은 "manifest(보호 대상 파일 목록)와 checker(그걸 검사하는 코드)를 같이 고쳐도, 세 번째 독립 목록이 있어서 2곳만 고치면 걸리지만, 3곳을 전부 고치면 못 막는다"는 한계를 스스로 인정하는 문장입니다.

저는 이걸 실제로 재현해 진짜임을 확인했습니다: manifest(`docs/sot/verification-protected-surface.yaml`), checker 내부 상수(`scripts/verify/verification_authority.rb`의 `INTRINSIC_PROTECTED` 목록), 계약 파일(`docs/sot/verification-requirements.yaml`의 `protected_surface` 목록) 세 곳에서 동시에 `.github/workflows/verify.yml` 항목을 지운 뒤 `protected-check`를 돌렸습니다.

```
=== running protected-check after 3-way weakening ===
PROTECTED: paths=11 enforcement=DETECT_ONLY external=4
EXIT:0
```
→ 뭘 시켰나: 세 목록을 동시에 손대 CI 워크플로 파일을 보호 대상에서 빼기. → 뭐가 나왔나: 오류 없이 통과(`paths=11`, 원래는 12). → 좋은 소식인가 나쁜 소식인가: 예상대로 나쁜 소식이지만, 문서가 이미 이 한계를 "외부 차단이 아니다"라고 정확히 밝히고 있으므로 과장은 아닙니다.

## 항목 10 — 외부 강제 상태 과장 여부 (사실 확인, 과장 없음)

```
gh api repos/sangmokang/Valuehire_v6/branches/main/protection
{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.", "status":"403"}
gh api repos/sangmokang/Valuehire_v6/rulesets
{"message":"Upgrade to GitHub Pro ...", "status":"403"}
CODEOWNERS: ABSENT
```
→ 뭘 시켰나: 오늘 날짜로 GitHub API를 직접 조회(읽기 전용). → 뭐가 나왔나: branch protection·ruleset 모두 403, CODEOWNERS 없음. → 좋은 소식인가 나쁜 소식인가: `docs/sot/verification-protected-surface.yaml:41-52`(외부 통제 4종 상태 선언)가 이 셋을 정확히 `UNAVAILABLE`로 적어놓았으므로, 문서와 실측이 일치합니다 — 과장 없음(좋은 소식).

## 나머지 공격 항목 — 재현 요약 (2, 4~9, 11~14)

명령 9개는 모두 요청하신 대로 실행했고 전부 성공(EXIT 0)했습니다.

| 명령 | 결과 |
|---|---|
| `git status --porcelain` | 31개 파일 staged, 원본 그대로(작업 종료 시점까지 불변 확인) |
| `git diff --cached --check` | 출력 없음(공백/충돌 마커 없음) |
| `contract-self-test` | `negative_cases=6 blocked=6` |
| `wiring-check` | `ci_direct=1 pre_push_runtime=1 artifact=1` |
| `run-verification-authority-mutations.sh` | `total=18 blocked=17 survived=0 controls=1` |
| `sha-fixtures` | 11개 전부 기대값과 일치 |
| `recovery-fixtures` | 8개 전부 기대값과 일치 |
| `derived-state-check` | `tamper_overwritten=1 required_fields=6` |
| `authority-check` | `llm_report=FAIL local_verified_emitter=0 protected=DETECT_ONLY` |

→ 뭘 시켰나: 사용자가 지정한 9개 명령 그대로. → 뭐가 나왔나: 전부 통과. → 좋은 소식인가 나쁜 소식인가: 항목 1(검증기 자체 무력화)을 빼면 대체로 좋은 소식이며, 아래 세부 항목도 코드/픽스처를 직접 읽어 트리비얼(공허하게 항상 통과하는) 검사가 아님을 확인했습니다.

- **항목 2(CI `echo` 위장)**: `mutations.rb:73-86`의 `ci_echo_command`/`ci_comment_only` 케이스가 실제로 `.github/workflows/verify.yml`의 실행 줄을 `echo bash ...`나 주석으로 바꾼 뒤 `wiring-check`를 돌려 실패를 확인합니다. `wiring_check`(`verification_authority.rb:344-373`)는 `run:` 필드를 셸 토큰 단위로 분해해 `argv[0]=='bash' && argv[1]==스크립트경로`인지 봅니다 — 문자열 포함 여부가 아니라 실제 실행 동사를 봅니다.
- **항목 4(mutation 개수·목록 동시 축소)**: `mutation_catalog_check`(`verification_authority.rb:245-255`)가 계약 파일의 `mutation_catalog`와 checker 내장 상수 `REQUIRED_MUTATIONS`를 상호 대조합니다. `mutation_expected_count`만 낮추거나 카탈로그만 줄이는 것으로는 못 뚫습니다(단, 이것도 항목 3과 같은 원리로 checker 내장 상수까지 동시에 고치면 별개의 논의가 필요하나, 이는 항목 3에서 이미 확인한 동일한 구조적 한계의 연장선입니다).
- **항목 5·6·7(SHA/워크플로/체크이름/merge-group)**: `policy_state`(`verification_authority.rb:375-400`)가 판정 로직 본체입니다. 픽스처 원문을 직접 읽어 `09-forged-success.yaml`은 `source: llm_report`(로컬/LLM 출처)로 표시된 "성공"을 담고 있고, `10-unrelated-merge-group.yaml`은 `pr_head_sha`와 `merge_group_pr_head_sha`를 일부러 다르게(`a...`/`b...`) 넣어 관계 위조를 흉내 냅니다 — 트리비얼한 목업이 아니라 실제 위조 시나리오를 담고 있음을 확인했습니다.
- **항목 8(롤백 실패 계열)**: `recovery.rb`의 `RecoveryJournal#run`이 각 실패 지점(권한 복구 실패, 반복 재시도, 상태 삭제 시도)마다 상태 파일을 남긴 채 특정 상태 문자열을 반환하도록 되어 있고, `delete_if_recovered`(`recovery.rb:27-31`)는 `status=='RECOVERED'`가 아니면 삭제를 거부합니다. 실제로 미완료 상태에서 삭제를 시도하면 예외가 나서 `DELETE_REFUSED`로 잡힙니다.
- **항목 9(LLM 보고서 단독으로 VERIFIED)**: `authority_check`(`verification_authority.rb:489-504`)가 `source: llm_report`인 위조 증거를 넣고 `policy_state`가 `FAIL`을 반환하는지 확인하며, 추가로 checker 파일 자체에 `return 'VERIFIED'` 문자열이 없는지도 검사합니다. 다만 이 마지막 검사는 `__FILE__`(자기 자신)만 스캔하고 `mutations.rb`·`recovery.rb`는 스캔하지 않는데, `build_report`(`verification_authority.rb:434-459`)가 상태값을 오직 `protected_changed`(보호 파일 변경 여부, git diff로 객관적으로 계산됨) 하나로만 결정하고 `mutations.rb`/`recovery.rb`의 반환값을 전혀 참조하지 않으므로, 실질적으로 악용 가능한 구멍은 아닙니다(경미한 코드 위생 문제로만 기록합니다).
- **항목 11(배선이 실제 실행인지)**: `prepush_runtime_wiring`(`verification_authority.rb:306-342`)이 실제로 임시 git 저장소를 만들어 `hooks/pre-push`를 진짜로 실행시키고, 마커 파일이 생겼는지 확인합니다 — 문자열 언급만으로는 통과할 수 없는 런타임 증명입니다. 다만 이 테스트는 "pre-push가 그 경로의 파일을 실행하는가"만 증명하고, "그 파일 내부 로직이 고장을 실제로 잡아내는가"는 증명하지 않는다는 점이 항목 1의 구멍과 맞물립니다.
- **항목 12(정상 변경 오탐)**: `normal_control` 케이스(`mutations.rb:173-178`)가 깨끗한 격리 저장소에서 `verify-all --no-mutations`이 `AUTHORITY_RESULT: LOCAL_CANDIDATE`(정상 통과)를 내는지 확인합니다. 이번 브랜치 자체를 대상으로도 직접 돌려본 결과(`AUTHORITY_RESULT: POLICY_REVIEW_REQUIRED`)는 보호 파일을 실제로 바꾸고 있으므로 정확한 판정이며 오탐이 아닙니다. 다만 pre-push에서 매 push마다 전체 스위트가 약 37초 걸리는 것을 실측했습니다(`time (SECRET_PATTERNS_FILE= bash scripts/acceptance-verification-authority.sh)` → `36.989 total`) — 오탐은 아니지만 운영 마찰(모든 push마다 18개 격리 저장소를 새로 만들고 git init하는 비용)로 참고하시기 바랍니다.
- **항목 13(보고서·아티팩트가 대상 SHA에 묶였는가)**: `.github/workflows/verify.yml:192,197-198`이 실행 줄과 업로드 `name`/`path` 모두에 `${{ github.sha }}`/`$GITHUB_SHA`를 사용하고, `wiring_check`(`verification_authority.rb:362-369`)가 이를 정적으로 강제합니다. 확인됨.
- **항목 14(필수 파일 삭제·이름변경, mutation 조기성공)**: `required_checker_deleted`/`required_registry_renamed`(`mutations.rb:87-96`)는 각각 checker 파일 삭제, 계약 파일 이름변경 후 `contract-self-test`가 실패하는지 봅니다. 다만 이건 "파일이 없으면 Ruby 인터프리터가 그 자체로 실행에 실패한다"는 당연한 성질에 의존하는 것이어서 정교한 회피 시도를 막는 검사라기보다는 최소한의 존재 확인 수준입니다 — 그 자체로는 문제없으나 방어의 깊이를 과대평가하지 않도록 참고해 주십시오.

## 설계 결정 노트 — 항목 1에 대한 권고 (무엇/왜/버린 대안/대가/되돌리는 법)

- 무엇: `verify_all`과 `hooks/pre-push`가 각 검사 명령의 **종료코드만** 신뢰합니다.
- 왜: 셸 스크립트 조합 환경에서 종료코드는 가장 단순하고 이식성 높은 성공/실패 신호이기 때문입니다.
- 버린 대안: 출력에 특정 마커 문자열이 있는지까지 확인하는 방식은 `mutations.rb`의 자체 테스트에서만 쓰이고, 실제 소비자에는 적용되지 않았습니다.
- 대가: 검증기 파일 맨 위 한 줄만 바뀌어도 로컬에서 전 검사가 무증상으로 무력화됩니다.
- 되돌리는 법: `verify_all`이 각 검사 명령의 stdout에서 해당 요구사항이 스스로 선언한 "완료 마커"(예: 각 모드가 이미 출력하는 `CONTRACT_SELF_TEST:`, `WIRING:`, `SHA_FIXTURES:` 같은 태그)가 실제로 존재하는지도 함께 확인하도록 `command()` 호출 지점(`verification_authority.rb:518-521`)에 한 줄만 추가하면, 종료코드 위조만으로는 더 이상 통과할 수 없습니다. `hooks/pre-push`도 `>/dev/null` 대신 출력을 캡처해 같은 마커를 확인하도록 바꾸면 로컬 단계에서부터 막힙니다.
