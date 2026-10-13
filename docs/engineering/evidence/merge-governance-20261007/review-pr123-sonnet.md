VERDICT: FAIL

# PR #123 llmcodereview 스킬 병합 가능 여부 판정서 (head 2bdfca7, base 55240f7)

## 1. 결론 (전문용어 없이)
지금 상태로는 병합하시면 안 됩니다. 돈이 새는 경로는 찾지 못했습니다. 그러나 이 도구의 핵심 약속인 "모델이 다 봤다는 말을 믿지 말고 기계가 대조한다"가 실제로는 지켜지지 않습니다. 재현한 사실은 다음과 같습니다.

- 검사 대상이 0건이어도 "합격"이 나옵니다. 변경 파일 0개, 확인할 경계 0개, 첨부 파일 0개인 입력이 모두 통과했습니다.
- 마지막 통합 단계와 재감사 단계는 검사기가 사실상 아무것도 확인하지 않습니다. 모델이 "SHA 일치"만 쓰면 확인할 경계가 전부 "미확인"이어도 "COVERAGE_OK(검사 충족)"가 찍힙니다.
- 첨부 원문을 만드는 스크립트는 git 조회에 실패해도 오류 없이 빈 첨부를 만듭니다. 빈 첨부에 모델이 "0줄까지 봤다"고 쓰면 "끝까지 읽었음" 검사도 통과합니다.
- 통합 단계 준비 스크립트가 WU(리뷰 단위) 9개로 고정되어 있습니다. 10개 이상이면 10번째부터 조용히 빠지고, 9개 미만이면 오류가 나도 옛 결과를 다시 써서 통합 프롬프트를 만듭니다.
- PR 본문의 확인 주장 일부는 사실과 다릅니다("PR 번호를 110으로 바꾸면 옛 PR 값이 하나도 남지 않는다"는 거짓이고, "검사기를 정상 1개·고장 2개로 시험했다"는 시험 파일이 PR에 없습니다).
- 브라우저 조작 안전장치 중 "실제 클릭" 대체 경로는 코드가 문법 오류라 동작하지 않고, 실행되면 사장님 화면을 3번 가로채고 원래 앱으로 되돌리지도 못합니다.

비용 경계와 공개 노출은 큰 문제가 없었습니다. 수정 범위는 작아 보입니다(약 5~6곳, 새 시험 파일 추가). 수정 후 같은 재현 입력으로 다시 판정하시길 권합니다.

## 2. 판정 앞부분 공개 사항 (건너뜀·미확인·재시도·추정)
- 실행하지 않은 것: 브라우저·Aside·osascript·cliclick을 쓰는 모든 스크립트(지시에 따라 실행 금지). 따라서 glaunch.sh, driver.sh, gdriver.sh, poll 계열의 동작은 코드 정독과 shellcheck, node 문법 검사, 따옴표 전개 재현으로만 판단했습니다. 실제 화면에서의 동작은 미확인입니다.
- 실제로 돌린 것: check_coverage.py, check_wu.py, check_seen.py, gpt_bundle.py, make_wu_prompt.py, integ.sh(osascript 호출 없음, 파이썬만 실행). 모두 스크래치패드 임시 디렉터리에서 PR 브랜치 원본을 `git show`로 풀어 실행했고, 저장소 파일은 건드리지 않았습니다.
- 재시도: make_wu_prompt 확인 1회차는 제 셸 인자 분리 실수로 IndexError가 나서 인자를 명시해 다시 실행했습니다(제품 결함 아님). integ.sh의 "WU 5개 + 낡은 요약" 시험은 제 준비 코드가 먼저 오류를 냈으나, 실제로 오류를 낸 것은 integ.sh 내부 파이썬이었고 결과 판독은 유효합니다(출력은 5.2 참조).
- 건너뜀: Gemini 경로(mpoll.sh, gem_js.sh)는 gpoll2.sh와 diff 해서 엔진 이름과 JS 파일만 다름을 확인하고 별도 결함 분석은 하지 않았습니다. 장부(ledger) 위조 가능성, 모델 프롬프트 주입(PR 안의 문구가 모델을 조종하는 경우)은 범위 밖입니다.
- 추정(※): ※ 표시한 항목은 실행 없이 코드로 추정한 것입니다.
- CI 상태: `gh pr view`로 verify 2건 SUCCESS, Cursor Bugbot NEUTRAL, mergeable=MERGEABLE, reviewDecision 없음. 초록불은 시험이 없는 PR이라 이 도구의 정확성을 증명하지 않습니다.

## 3. 판단 근거
- 선택: "병합 가능"을 이 PR이 스스로 정한 승인 기준(PR 본문 "사장님이 반드시 볼 부분" 3개)과 SKILL.md가 선언한 약속("대조는 스크립트가 한다", "첨부를 끝까지 읽었는지 기계로 검사")으로 판단했습니다. 외부 기준을 새로 들이지 않았습니다.
- 버린 해석 1: "개발 보조 도구이니 결함이 있어도 병합해도 된다"는 해석을 버렸습니다. 이 도구의 산출물은 "이 PR을 끝까지 검토했다"는 보증이고, 거짓 보증은 이후 다른 PR의 병합 판단에 직접 쓰이기 때문입니다.
- 버린 해석 2: "모델 자기신고라서 검사기가 못 막는 것은 결함이 아니다"는 해석을 부분적으로 버렸습니다. 0건 통과·빈 첨부 통과·단계 누락은 자기신고와 무관하게 검사기 코드가 막을 수 있습니다. 반면 모델이 거짓 줄 수를 쓰는 것 자체는 설계 한계로 따로 적었습니다(6절 설계 지적 1).
- 틀리면 깨지는 것: (a) 이 도구를 운영자가 항상 사람이 최종 확인한다면 S1 등급이 S2로 내려갑니다. SKILL.md 4절에 "S2 이상은 오케스트레이터가 직접 읽거나 재현"이 있으나 "파일 커버리지" 자체는 사람이 확인하라는 문구가 없습니다. (b) 비용 PASS는 Cursor 화면 문구(영어 "On-demand spending is currently disabled", "N% used")가 유지된다는 가정에 기댑니다. 문구가 바뀌면 차단 쪽으로 실패하므로 돈은 새지 않지만 도구가 멈춥니다.
- 심각도 기준: S0=금전·개인정보 즉시 피해, S1=이 도구의 핵심 보증이 거짓이 되는 결함, S2=기능 오작동·잘못된 결과·거짓 문서, S3=품질·경미.

## 4. review unit 별 판정 요약
| unit | 판정 | 핵심 |
|---|---|---|
| (1) 비용 경계 | PASS(S3 2건) | 유료 경로를 자동으로 켜는 코드 없음. 차단 방향으로 실패 |
| (2) 검사기 3종 | FAIL | S1 2건, S2 3건. 0건 통과·단계 누락 재현 |
| (3) 브라우저 조작 | FAIL | S2 2건, S3 3건. 실제 클릭 경로 고장·포커스 가로채기 |
| (4) 공개 저장소 노출 | PASS(S2 1건 별도) | 개인 경로·토큰·탭 id 없음. 임시 파일이 ignore 안 됨 |
| (5) 프롬프트 생성 | FAIL | S1 1건(빈 첨부), S2 2건(PR #109 고정, 통합 9개 고정) |

## 5. 결함 목록 (심각도 순)

### D1. [S1] 원문 제목: "check_wu.py 가 INTEG/AUDIT 단계에서 아무것도 검사하지 않고 COVERAGE_OK 를 출력"
- 원인: check_wu.py:43 `if tag == "WU_JSON":` 안에서만 파일 커버리지를 대조합니다. INTEG_JSON·AUDIT_JSON 태그는 SHA 한 줄(:41-42)만 보고 :67 `COVERAGE_OK; exit 0`에 도달합니다. SKILL.md:33은 "경계마다 VERIFIED/ISSUE/NOT_CHECKED, NOT_CHECKED가 남으면 HOLD — REVIEW COVERAGE GAP"이라고 쓰지만 이를 집행하는 코드가 없습니다. driver.sh:18도 INTEG 검사 결과를 장부에 적을 뿐 멈추지 않습니다.
- 재현 입력과 출력(스크래치패드 t/, LCR_SHA=aaaa1111):
```
# 확인할 경계가 0개
<<<INTEG_JSON {"head_sha_checked":"aaaa1111","boundaries":[],"verdict":"PASS"} INTEG_JSON>>>
$ check_wu.py i0.txt ... INTEG o.json INTEG_JSON
INTEG verdict=PASS findings={} tests_exec=0 conf=None
COVERAGE_OK   rc=0
# 경계가 전부 미확인
boundaries: B01 NOT_CHECKED, B02 NOT_CHECKED
  B01 NOT_CHECKED ::
  B02 NOT_CHECKED ::
COVERAGE_OK   rc=0
# 재감사: SHA만 쓰고 아무것도 안 함
{"head_sha_checked":"aaaa1111"}  ->  COVERAGE_OK rc=0
```
→ 해석: 통합 단계(여러 WU 사이 경계를 보는 마지막 방어선)와 재감사가 "하나도 안 했는데도 합격"입니다. 출력의 `COVERAGE_OK`는 검사기가 확인한 것이 SHA 문자열뿐이라는 뜻입니다.
- 반증 시도: 프롬프트 에코(모델이 답하지 않고 템플릿만 남은 경우)는 `"head_sha_checked":"..."` 때문에 GAP(rc=1)로 정상 차단됨(T2e, T2f). 즉 "답을 안 한 경우"는 막지만 "SHA만 맞춘 빈 답"은 못 막습니다.
- 사업 영향: 여러 PR의 "경계 검토 완료" 보고가 근거 없이 나갑니다. 이 도구로 병합 판단을 하면 경계 결함을 놓친 채 승인할 수 있습니다.
- 수정 방향: INTEG는 Planner의 cross_wu_boundaries id 전부가 boundaries에 있고 NOT_CHECKED가 0일 때만 0, 아니면 새 종료값(예: 1)으로 차단. AUDIT는 직전 Reviewer finding id 전부가 reclassified에 있는지 대조.

### D2. [S1] 원문 제목: "gpt_bundle.py 가 git show 실패를 삼켜 빈 첨부를 정상 생성, check_seen.py 는 0건 첨부도 SEEN_OK"
- 원인: gpt_bundle.py:32-33 `show()`가 `subprocess.run(..., capture_output=True).stdout`만 반환하고 returncode·stderr를 버립니다. 파일이 없거나 SHA가 로컬에 없으면 빈 문자열이 되어 :41에서 `FILE: x (0 lines)`/`END FILE: x (last line 0)`로 정상처럼 포장됩니다. check_seen.py:4 정규식은 표식이 0개여도 `want={}`가 되어 :10-11 `SEEN_OK`를 냅니다.
- 재현(존재하지 않는 SHA aaaa1111, 파일 x.py는 실제로는 있음):
```
$ gpt_bundle.py wu WU01 wu.txt        -> wu.txt 3344 chars True   rc=0
===== FILE: ghost.py (0 lines) =====   / ===== END FILE: ghost.py (last line 0) =====
===== FILE: x.py (0 lines) =====       / ===== END FILE: x.py (last line 0) =====
$ git -C repo show aaaa1111:x.py      -> fatal: invalid object name 'aaaa1111'. (git rc=128)
$ check_seen.py wu.txt rs.json  (모델이 last_line_seen=0 보고)
bundle files=2 seen_ok=2   SEEN_OK   rc=0
# 첨부 표식 0개 프롬프트
$ check_seen.py p0.txt r0.json   -> bundle files=0 seen_ok=0  SEEN_OK  rc=0
$ check_seen.py p0.txt r00.json ({}) -> SEEN_OK rc=0
```
→ 해석: git은 128로 실패했는데 스크립트는 rc=0과 "정상 첨부"를 냈고, 검사기는 "2개 파일 모두 끝까지 읽음"이라고 말합니다. 실제로 모델이 본 내용은 0줄입니다.
- 사업 영향: LCR_SHA 오타, 아직 fetch하지 않은 커밋, PR에서 삭제·이름 변경된 파일이면 ChatGPT가 빈 첨부로 "중대한 결함 미발견"을 내고도 "끝까지 읽음" 도장이 찍힙니다.
- 수정 방향: returncode≠0이면 즉시 종료. 삭제 파일은 별도 표기. check_seen은 want가 0건이면 실패(2) 처리하고 want 파일 수와 전달한 첨부 수를 비교.

### D3. [S2] 원문 제목: "check_coverage.py 가 변경 0건·Primary WU 불일치를 PASS 처리"
- 원인: check_coverage.py:48-65. 인벤토리가 비어 있으면 모든 반복문이 돌지 않아 :65 PASS. 또 :57-59는 "모든 변경 파일이 어떤 WU의 files에든 있다"만 보고, 장부의 primary_wu가 가리키는 WU가 그 파일을 실제 files에 갖는지는 보지 않습니다.
- 재현:
```
# (a) 인벤토리 0건 + 빈 계획
diff_files=0 ledger_unique=0 wus=0   PASS rc=0
# (b) a.py, b.py 모두 primary_wu=WU01 인데 WU01.files=[] (고위험 WU가 빈 WU), 파일은 WU02.files에만 존재
  WU01 HIGH lines=None files=0 auditor=None :: None
  WU02 LOW lines=None files=2 auditor=None :: None
PASS rc=0
```
→ 해석: "파일마다 Primary WU 정확히 1개"라는 SKILL.md:31 통과 조건이 코드로는 지켜지지 않습니다. (b)는 위험도 HIGH로 표시된 WU가 파일을 하나도 갖지 않아도 통과합니다.
- 추가: 인벤토리 줄에 `-`(바이너리 numstat)가 있으면 :39 `int('-')` 파이썬 오류로 종료되어 판정 대신 traceback만 남습니다(rc 1, 실제 GAP과 구분 불가).
- 사업 영향: 이 검사기는 "리뷰 단위 설계가 틀렸다"를 가장 먼저 막는 문입니다. 열려 있으면 이후 모든 단계가 틀린 분할 위에서 진행됩니다.

### D4. [S2] 원문 제목: "driver.sh 가 GAP(커버리지 부족) 판정 후에도 멈추지 않고 ALL_DONE"
- 원인: driver.sh:20-22는 `check_wu` 종료값 c를 장부에 기록하지만 `c -eq 2`(파싱 실패)만 정지시킵니다. c=1(GAP, 또는 traceback)이면 이어서 :23 감사 필요 여부 계산으로 넘어가 :31 `echo ALL_DONE`에 도달합니다(정적 판독, 이 줄은 실행하지 않음). gdriver.sh:37-40도 동일하고 `seen_rc`는 기록만 합니다.
- 근거 출력: check_wu가 GAP일 때 rc=1을 내는 것은 실행으로 확인(T2e `GAP - SHA '...'  rc=1`). 이후 흐름은 코드 정독입니다 ※.
- 사업 영향: 일부 WU가 덜 읽혔는데도 "ALL_DONE"이 뜹니다. 장부에는 check_rc=1이 남지만 SKILL.md:34가 FINAL_DONE 전에 이 값을 확인하라는 단계가 없습니다.
- 관련: check_wu.py:43-51은 WU files가 빈 배열이면 읽을 파일이 0개라 COVERAGE_OK입니다(재현: WU02 files=[] -> COVERAGE_OK rc=0). 같은 "0건 합격" 계열입니다.

### D5. [S2] 원문 제목: "integ.sh / gdriver.sh 통합 요약이 WU01~WU09 로 고정"
- 원인: integ.sh:6 `for w in [f"WU0{i}" for i in range(1,10)]`, gdriver.sh:23 동일. 계획의 실제 WU 수와 무관합니다. integ.sh에는 `set -e`가 없어 파이썬이 중간에 실패해도 :14 `make_wu_prompt.py integ`가 이어서 실행됩니다.
- 재현(LCR_SHA=newsha99):
```
# 10개 WU, WU10 에 S0 finding (REPRODUCED)
summary WUs: ['WU01'..'WU09']      WU10 in integ prompt? -> 0
# 5개 WU 계획 + 이전 실행이 남긴 낡은 wu-summary.json (WU01={"verdict":"STALE_OLD_SHA_RESULT"})
FileNotFoundError: .../WU06.json
(그래도 integ-prompt.txt 2763자 생성)    stale 요약이 새 프롬프트에 들어갔나? -> 1
```
→ 해석: 10번째 이후 WU의 S0 결함이 통합 단계에 전달되지 않습니다. 9개 미만이면 오류가 나지만 낡은 요약으로 프롬프트가 만들어집니다. 이 PR이 #109를 9개 WU로 쪼갠 경험을 상수로 굳힌 것입니다 ※(출처 추정).
- 사업 영향: 큰 PR일수록 WU가 늘어 정확히 이 도구가 필요한 큰 PR에서 마지막 WU들이 조용히 빠집니다.

### D6. [S2] 원문 제목: "PR 본문의 검증 주장 2건이 사실과 다름 / 검사기 시험 없음"
- (a) PR 본문: "PR 번호를 110으로 바꾸면 옛 PR 값(109·SHA)이 하나도 남지 않습니다." 실행: LCR_PR=110 으로 make_wu_prompt 를 돌리면
```
== wu     1:[역할] WU Reviewer — WU01 (PR #109, 새 세션, 읽기 전용)
== audit  1:[역할] Adversarial Auditor — WU01 (PR #109, 새 세션, 읽기 전용)
== integ  1:[역할] Cross-WU Integration Reviewer (PR #109, 새 세션, 읽기 전용)
```
(make_wu_prompt.py:74,106,123 하드코딩. Planner는 정상). PR 본문 하단 Bugbot 요약이 같은 지적을 이미 남겼으나 PR 본문의 확인 주장은 정정되지 않았습니다.
- (b) PR 본문: "각각 정상 1개·고장 표본 2개로 시험해 고장만 잡는 것을 확인했습니다." PR의 25개 파일에 시험 파일이 없고, 위 D1~D3은 그 표본 밖에 있습니다. 하네스 규칙(RED 먼저)에도 맞지 않습니다.
- (c) 같은 파일에 PR #109 고유 문구가 남아 있습니다: make_wu_prompt.py:8 `--live-jev`, :9 `typesafe_sdk`, :91 `cd humansearch && uv run --frozen pytest`. 다른 PR에서는 모델에게 존재하지 않는 경로를 실행하라고 지시합니다.
- 사업 영향: 사장님이 PR 본문의 확인 사항을 믿고 승인하는 구조인데 그 일부가 거짓입니다.

### D7. [S2] 원문 제목: "glaunch.sh 의 실제 클릭 대체 경로: 문법 오류 JS + 앞 앱 복귀 실패 + 화면 가로채기"
- 원인 1(문법): glaunch.sh:48 의 `querySelectorAll("button[aria-label="파일 등 추가"]")`는 bash 작은따옴표 안이라 이스케이프가 없어 JS 문자열이 깨집니다(:6의 같은 JS는 `\"`로 정상). 실행:
```
$ node --check fb.js
SyntaxError: missing ) after argument list      ("파일 등 추가" 주변에 ^^^^ 표시)
```
→ 해석: 이 경로의 좌표 계산 JS는 항상 오류입니다. 결과로 `cliclick c:` 에 빈 좌표가 전달되어(※ 정적 추정) 클릭은 일어나지 않고 "menu_closed"로 3회 반복 후 실패합니다. 클릭이 엉뚱한 곳에 가는 위험은 이 문법 오류 때문에 현재는 발생하지 않지만, 문법을 고치면 아래 경쟁 상태가 현실이 됩니다.
- 원인 2(복귀 실패): glaunch.sh:54 `osascript -e "tell application "$FRONT" to activate"` 는 따옴표가 풀려 "tell application Google Chrome to activate"로 전개됩니다(실행 출력 확인). 이름에 공백·한글이 있는 앱은 AppleScript 문법 오류이고 stderr는 :54 `2>/dev/null`로 숨깁니다. engines.md:9 "⑦ 원래 앱 activate" 약속이 지켜지지 않습니다(shellcheck SC2027 경고와 일치).
- 원인 3(가로채기): :37-46이 `activate`와 `set index of w to 1`로 Aside를 맨 앞으로 올립니다. 이 단계는 JS 오류와 무관하게 3회 실행됩니다. 사장님 작업 화면이 3번 뺏기고 돌아오지 않습니다.
- 원인 4(경쟁 상태, ※): :47 전면 앱 확인과 :49 `cliclick` 사이에 :48 JS 호출(osascript)이 끼어 있어 그 사이 사용자가 앱을 바꾸면 클릭이 그 앱에 떨어집니다. PR 본문이 약속한 "클릭 직전 재확인"과는 다릅니다. 확인과 클릭이 같은 순간이 아닙니다.
- 이 경로가 도달되는 조건: SKILL.md:43이 "GitHub 연결이 꺼져 있으면 켜지 말고 묶음만 붙인다"고 안내하는 바로 그 경우, @GitHub 칩이 안 생겨 이 대체 경로로 들어갑니다. 그런데 :56은 칩이 없으면 `BLOCKED_CHATGPT_UI_NO_CHIP exit 4`로 종료합니다. 즉 안내된 경우에 도구가 가로채기만 하고 실패합니다(SKILL.md:43과 glaunch.sh:56의 모순).
- 사업 영향: 사장님 업무 화면 방해, 문법 수정 후에는 오클릭 가능성.

### D8. [S2] 원문 제목: "임시 JS 파일이 추적 디렉터리에 쓰이고 .gitignore 에 없음 (PR 전문이 base64 로 남음)"
- 원인: usage.sh:6(_u.js), insert_prompt.sh:4(_ins.js), glaunch.sh:4(_q.js)·:58(_p.js), gpoll2.sh:6·:23(_gh.js·_rt.js), poll2.sh:4(_all.js), launch.sh:6(_rdy.js)가 모두 `$S`, 즉 스킬 폴더 `.claude/skills/llmcodereview/scripts/aside/`에 씁니다. `_p.js`·`_ins.js`에는 지시문 전체(ChatGPT 경로는 첨부 원문 포함)의 base64가 들어갑니다.
- 확인: `git check-ignore -v .claude/skills/llmcodereview/scripts/aside/_p.js` → 출력 없음, rc=1(무시 규칙 없음). `_all.js`, `_u.js`도 동일.
- 사업 영향: 이 저장소는 공개입니다. `git add -A` 나 `make ship`이 모델에게 보낸 프롬프트(LCR_EXTRA_FILES로 PR 밖 파일을 넣은 경우 포함)를 커밋할 수 있습니다. 같은 폴더에서 엔진 2개를 동시에 돌리면 `_q.js`·`_rt.js`를 서로 덮어씁니다(※, gpoll2.sh:23와 mpoll.sh:23이 같은 `_rt.js`에 씀).
- 수정 방향: `$LCR_ROOT/tmp/`로 옮기거나 `.gitignore`에 `.claude/skills/llmcodereview/scripts/aside/_*.js` 추가.

### D9. [S2] 원문 제목: "고위험 WU 감사 대상이 WU04·WU05 로 고정, 나머지는 모델 자기신고에 의존"
- 원인: driver.sh:23, gdriver.sh:41 `'$W' in ('WU04','WU05') or ... severity in (S0,S1) or confidence=='low'`. SKILL.md:32의 기준("외부 전송·권한·삭제·개인정보 WU")과 다릅니다. Planner JSON에 이미 `needs_auditor`(make_wu_prompt.py:60)가 있는데 쓰이지 않습니다. 모델이 confidence="high", findings=[]라고 쓰면 감사를 피합니다(check_wu.py가 이 값을 검증하지 않음, 재현 T2b: verdict·findings 없이 COVERAGE_OK).
- 사업 영향: PR #109의 WU04/05 분할을 본 적 없는 다른 PR에서는 엉뚱한 WU가 감사받고 위험 WU가 빠집니다.

### D10. [S3] 비용 경계의 작은 틈 (PASS 판정에 영향 없음)
- usage.sh:7은 읽기 실패 시 `echo UNKNOWN`을 출력하고 종료값 0입니다. SKILL.md:26은 사람이 읽고 판단하라는 구조이고, 자동 차단은 driver.sh:8-10(숫자 아님 -> 정지, od_disabled≠true -> 정지, 90% 이상 -> 정지)에서만 이뤄집니다. gdriver.sh(ChatGPT)에는 사용량 확인 단계가 없고 poll 결과의 문구 감시(gpoll2.sh:12)뿐입니다. 구독 한도형이라 추가 과금은 아니지만 "한도 화면이면 멈춘다"는 사후 검출입니다.
- poll2.sh:10, gpoll2.sh:12의 문구 감시는 페이지 전체 텍스트에서 `on-demand spending|usage limit` 같은 단어를 찾습니다. 모델이 이 스킬 자체(usage.sh 문구 인용)를 리뷰하면 거짓 경보로 멈춥니다(차단 방향 오탐). 정확도 문제이지 비용 누수는 아닙니다 ※.
- launch.sh:6은 모델 버튼을 `/^Grok [0-9]/`로만 확인합니다. 포함 사용량을 많이 쓰는 모델 변형이 같은 접두어라면 구별하지 못합니다 ※.

### D11. [S3] 공개 저장소 노출
- env.sh:7 `https://chatgpt.com/g/g-p-68bad2bd651c8191a5a67b685d639c7f/project`: 개인 ChatGPT 프로젝트 주소가 기본값으로 박혀 있습니다. 로그인 없이는 열리지 않지만 계정 식별자를 공개합니다. 환경변수 필수(`:?`)로 바꾸면 됩니다.
- launch.sh:6, make_wu_prompt.py:13, gpt_bundle.py:20 의 `sangmokang/Valuehire_v6`는 공개 저장소명이라 노출 문제가 아닙니다(이식성 문제만).
- 탭 id·창 id·토큰·이메일·`/Users/` 경로: 전체 정규식 검색에서 0건(`kangsangmo|/Users/|@valueconnect|token|api_key|secret|Bearer|sk-…|숫자 8자리 이상`, 검색 대상 `.claude/` 전체). 검색 자체가 작동하는지 양성 대조로 env.sh의 `g-p-…` 패턴이 1건 잡혔습니다.

### D12. [S3] 브라우저 조작 기타
- glaunch.sh:23 `focus_tab`이 사용자 창의 활성 탭을 바꾸고 :56 `restore_tab`까지(재시도 포함 약 10~25초 ※) 유지합니다. SKILL.md:14 "사장님 활성 탭을 빼앗지 않는다"와 PR 본문 "화면·마우스를 쓰지 않는" 표현이 부분적으로 어긋납니다. 복원은 탭 id가 아니라 번호(PREV_IDX)라서 그 사이 탭이 열리고 닫히면 엉뚱한 탭으로 돌아갑니다 ※.
- glaunch.sh:36 `until [ "$(js 'document.readyState')" = complete ]` 에 제한 시간이 없어 탭이 닫히면 무한 대기합니다.
- gpt_bundle.py:39 `str.splitlines()`는 \f, \x1c-\x1e, \x85,   에서도 줄을 나눕니다. 해당 문자가 있는 파일은 첨부의 줄번호가 GitHub 줄번호와 달라집니다 ※(미재현).
- gpt_bundle.py adapt() 이후에도 WU 프롬프트 25행에 `git diff … -- <파일> 로 확인`이 남아(재현 T3d), git을 못 쓰는 엔진에게 불가능한 지시를 합니다.

## 6. 설계 지적 (다섯 줄 형식)
### 설계 1. 읽었다는 증거를 모델 자기신고로 받는 구조
- 무엇을: check_wu.py:46 `changed_lines_read`, check_seen.py `last_line_seen`을 모델이 쓴 숫자로 비교합니다.
- 왜: 외부 모델 화면에서 읽기 로그를 기계적으로 얻을 방법이 없어서 자기신고를 대조하는 최선의 방법으로 보입니다 ※.
- 버린 길: 화면에서 도구 호출 로그 파싱(UI 의존이 큼), 질문-정답식 확인(첨부 속 임의 문장을 되묻는 방식).
- 대가: 모델이 거짓 숫자를 써도 통과합니다. 재현: 변경 8줄 파일에 `changed_lines_read:9999`를 써서 COVERAGE_OK(T2b). 이 한계는 SKILL.md가 "모델이 다 봤다는 말은 증거가 아니다"(:8)라고 쓴 문장과 충돌합니다.
- 되돌리기: 쉽습니다. 첨부 안에 파일별 무작위 확인 문구를 심고 응답이 그 문구를 인용했는지 대조하는 것을 추가하면 자기신고를 보강합니다.

### 설계 2. 통합·감사 단계 검사를 하나의 스크립트에서 태그 분기로 처리
- 무엇을: check_wu.py 하나가 WU/AUDIT/INTEG를 `tag` 인자로 다르게 취급합니다.
- 왜: 코드 재사용과 파서 공유 때문으로 보입니다 ※.
- 버린 길: 단계별 전용 검사기.
- 대가: 분기가 약한 쪽(INTEG/AUDIT)이 검사 없이 통과합니다(D1).
- 되돌리기: 쉽습니다. 단계별 검사 함수와 "0건이면 실패" 공통 가드를 둡니다.

## 7. 반증 기록 (무엇을 어떻게 깨려다 실패했는지)
| 시도 | 결과 |
|---|---|
| 모델이 답하지 않고 프롬프트 에코만 남은 raw를 Planner·INTEG·AUDIT에 투입 | 막힘. Planner는 템플릿의 `N` 때문에 PARSE_FAIL rc=2(T1e), INTEG는 `head_sha_checked:"..."`로 GAP rc=1(T2e). 에코가 합격으로 새는 경로는 못 찾음 |
| 답이 잘린(깨진) JSON 앞에 에코 템플릿을 두어 "마지막 블록 -> 앞 블록 폴백"으로 합격시키기 | 막힘. 폴백 블록의 SHA가 `...` 라서 GAP(T2f) |
| check_coverage에 같은 파일 중복 장부 행, 장부에 없는 파일, 줄 수 불일치 | 코드상 DUP_PRIMARY·MISSING·EXTRA·LINES로 차단(:49-56 정독). 직접 입력은 만들지 않음 ※ |
| SHA 접두 일치로 통과시키기 | 불가. check_coverage.py:41, check_wu.py:41은 완전 일치(.strip() 후) |
| 유료 경로 자동 활성: 코드 전체에서 upgrade·purchase·buy·결제·credit·enable 검색 | 클릭·이동·URL 설정은 모두 읽기 화면(`/dashboard/spending`, `/agents`, 프로젝트 URL)과 전송 버튼, 재시도 버튼뿐. 업그레이드·충전·On-Demand 켜기 동작 0건 |
| Cursor 한도 화면 문구가 바뀌면 유료로 흘러가는가 | 안 흘러감. driver.sh:8-10은 숫자 미판독·od_disabled≠true를 모두 정지로 처리(차단 방향 실패). 단 이는 코드 정독이며 실제 화면에서는 미실행 |
| gpt_bundle이 모델이 만든 planner.json 경로로 로컬 비밀 파일을 읽는가 | 불가. `git show {SHA}:{경로}`만 쓰므로 커밋된 파일로 한정됨. 경로가 없으면 D2의 빈 첨부로 이어질 뿐 |
| 개인 탭 id·토큰·개인 경로 검색 | 0건(D11) |

## 8. 파일 위치
- 판정서: /private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/review-pr123.md
- 재현 입력·출력 작업 폴더(임시): /private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/t/ , PR 브랜치 원본 사본: .../scratchpad/pr/.claude/skills/llmcodereview/
- 리뷰 대상 원본(저장소 내): .claude/skills/llmcodereview/ (origin/task/llmcodereview-skill @ 2bdfca7)

## 9. 병합 조건 (다시 판정할 때 쓸 것)
1. D1·D2 수정 + 위 재현 입력 5건(INTEG 빈 경계, INTEG 전부 NOT_CHECKED, AUDIT 빈 답, 빈 첨부, 표식 0개)이 모두 실패로 바뀐 출력.
2. D3·D4·D5·D9 수정 + 0건·primary 불일치·WU 10개·WU 5개+낡은 요약 재현이 실패 또는 정상 처리로 바뀐 출력.
3. D6 PR 본문 정정 + 검사기 시험 파일 추가(위 재현 입력을 시험으로 고정).
4. D7·D8 수정(문법·복귀·임시 파일 ignore). D10~D12는 같은 PR 또는 후속 이슈.
