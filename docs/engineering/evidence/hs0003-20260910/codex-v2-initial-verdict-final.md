VERDICT: FAIL

## 결론

HS-00.03 후보는 지금 그대로 커밋하면 안 됩니다. 사용자가 요구한 “전각·동형 문자로 착수 검사 대상 이름을 위장하는 입력 거부”가 처분표뿐 아니라 workflow와 정본 이름 경로에서도 깨집니다.

기본 검사들은 통과했습니다. 착수 검사는 12건, 정조준 시험은 15건, 전체 시험은 277건, 기존 착수 변이는 37건을 통과했고 정적 검사와 원칙 검사도 통과했습니다. 하지만 임시 사본 반례에서 전각 문자를 보호 이름 바로 앞뒤에 붙이면 전체 착수 검사가 합격으로 끝났습니다.

V1의 PASS 판정과 제 V2 판정은 갈립니다. V1은 PR 번호 13 뒤에 전각 숫자 1을 붙인 반례를 “계약 밖 잔여 위험”으로 봤지만, 저는 이 반례와 추가 workflow/SOT 반례가 HS-00.03 종료 조건 안쪽이라고 판단합니다.

## 판단 근거

제가 선택한 해석은 “보호 이름처럼 보이도록 전각·동형 문자를 섞은 착수 검사 대상 이름은 거부해야 한다”입니다. T 계약의 제목과 사용자 목표가 같은 방향이고, `docs/engineering/humansearch-hs0003-goal-2026-09-10.md`의 counter-AC도 `PR #131`과 `hs-kickoff-other`를 보호하면서 위장 입력은 막으라고 요구합니다.

버린 해석은 “치환 문자가 보호 토큰 span 바깥이면 모두 계약 밖”입니다. 이 해석을 택하면 `ｘPR #13`과 `ｘhs-kickoff (`처럼 사람이 보호 이름 앞에 붙은 전각 문자까지 포함해 다른 이름으로 읽을 수 있는 입력을 기존 raw 선택이 보호 이름으로 인정하는 문제를 남깁니다.

틀리면 깨지는 것은 raw 선택과 shadow 판정의 경계입니다. helper는 shadow 비교 사본에서 보호 토큰 span 내부에 치환이 있을 때만 거부하지만, shell은 raw 문자열 정규식과 substring으로 처분 행과 CI 배선을 계속 선택합니다. 그래서 두 기준이 갈라지는 이름은 helper를 통과하고 shell 판정에서는 보호 이름으로 인정됩니다.

## V1 대비 일치와 불일치

| 항목 | V1 | V2 |
|---|---|---|
| 최종 판정 | PASS | FAIL |
| `PR #13１` | 재현, 계약 밖 중간 위험 | 재현, 계약 안쪽 종료 차단 결함 |
| workflow/SOT 우회 | 처분표만 해당한다고 판단 | `ｘhs-kickoff (`로 전체 acceptance 종료값 0 재현 |
| 정상 control | 유지 | 유지 확인 |
| 빈 줄 helper 입력 | 낮음 | 재현, shell empty disposition 경로는 별도 실패 |
| invalid UTF-8 helper 입력 | 낮음 | 재현, shell invalid suffix 경로는 별도 실패 |
| metadata-skip mutant | 생존, blocker 아님 | 재현, blocker 아님 |
| 묶음 지문 | 재현 못 함 | 재현 못 함 |

→ V1의 세 반례 중 세 개는 재현됐습니다. 다만 첫 반례의 범위 판단은 뒤집혔고, workflow/SOT에서도 같은 raw 선택과 shadow 경계 불일치가 우회로 이어지는 추가 반례를 찾았습니다.

## 결함 1 — raw 선택과 shadow 경계 불일치로 보호 이름 위장이 통과함

- 상태: REPRODUCED
- 중요도: 높음
- HS-00.03 종료 조건 필수 수정 여부: 예
- file:line 역할: `scripts/verify/check-hs-kickoff-identities.py:138`은 helper가 입력 한 줄의 shadow 비교 사본을 만들고 보호 토큰을 찾는 함수입니다. `scripts/verify/check-hs-kickoff-identities.py:145`는 보호 토큰 span 내부에 치환이 있을 때만 실패로 세는 줄입니다. `scripts/acceptance-hs-kickoff.sh:87`은 처분표 raw 대상 칸에서 보호 행을 정규식으로 고르는 줄입니다. `scripts/acceptance-hs-kickoff.sh:227`은 workflow raw 스텝 이름에서 `hs-kickoff (` substring이 있는 스텝을 배선 대상으로 고르는 줄입니다.
- 원인: helper는 shadow 기준으로 `PR #13１`을 `PR #131`로 보고 보호 토큰이 아니라고 허용합니다. shell은 raw 기준에서 전각 숫자 `１`을 ASCII 경계 밖 문자로 보고 `PR #13` 행으로 인정합니다. 같은 불일치가 `ｘPR #13`과 `ｘhs-kickoff (`에서도 나타납니다.
- 사업 영향: 처분표나 workflow/SOT 정본 이름에 사람이 다른 이름으로 읽는 항목을 넣어도 착수 검사가 보호 대상 완료로 인정할 수 있습니다. 착수 검사의 “대상 이름 위장 거부”라는 목적이 깨집니다.

### 증거 원문 — 결함 1

```text
CASE disp_suffix_fullwidth_digit rc=0
PASS: 처분 PR #13 → 결론=재작성 (근거 경로 1 건·커밋 0 건)
PASS: CI 스텝 수·이름·순서 정본=30 실제=30 표 행=30 빈 이름 0 번호 1..30 이름 1:1
PASS: CI 배선 2건 — 이름과 명령이 같은 스텝에서 일치하고 조건·오류무시 없음
CHECKED: 12
CASE disp_prefix_fullwidth_x rc=0
PASS: 처분 PR #13 → 결론=재작성 (근거 경로 1 건·커밋 0 건)
PASS: CI 스텝 수·이름·순서 정본=30 실제=30 표 행=30 빈 이름 0 번호 1..30 이름 1:1
PASS: CI 배선 2건 — 이름과 명령이 같은 스텝에서 일치하고 조건·오류무시 없음
CHECKED: 12
CASE wf_sot_prefix_fullwidth_x rc=0
PASS: 처분 PR #13 → 결론=재작성 (근거 경로 1 건·커밋 0 건)
PASS: CI 스텝 수·이름·순서 정본=30 실제=30 표 행=30 빈 이름 0 번호 1..30 이름 1:1
PASS: CI 배선 2건 — 이름과 명령이 같은 스텝에서 일치하고 조건·오류무시 없음
CHECKED: 12
CASE wf_sot_inner_cyrillic_s rc=1
SPOOF: workflow-step line=29 token=hs-kickoff
SPOOF: sot-step line=29 token=hs-kickoff
FAIL: CI·정본 스텝 이름 Unicode 위장 또는 검사 오류
FAIL: CI 배선 불량 — 본 검사=없음 자기 변이=OK
CHECKED: 12
```

→ 임시 사본에서 전각 숫자 suffix, 전각 x prefix, workflow/SOT 전각 x prefix가 모두 전체 acceptance 종료값 0으로 통과했습니다. span 내부 키릴 문자 위장은 종료값 1로 잡혔으므로 helper가 아예 죽은 것은 아니고 경계 불일치가 원인입니다.

## 결함 2 — helper에 빈 줄 하나만 들어오면 입력 0건 오류가 아님

- 상태: REPRODUCED
- 중요도: 낮음
- HS-00.03 종료 조건 필수 수정 여부: 단독으로는 아니오
- file:line 역할: `scripts/verify/check-hs-kickoff-identities.py:178`은 stdin을 줄 목록으로 읽는 줄입니다. `scripts/verify/check-hs-kickoff-identities.py:179`는 줄 목록이 완전히 비었을 때만 오류로 보는 줄입니다.
- 원인: `printf '\n'`은 빈 문자열 한 줄을 만들기 때문에 `lines=[""]`가 되고 helper는 종료값 0으로 끝납니다.
- 사업 영향: helper 단독 계약의 “실제 이름/대상 줄 0개면 종료값 2”와 어긋납니다. 다만 shell에서 처분표 실제 행을 모두 제거한 경우에는 뒤의 “행 없음” 판정이 6건 실패해 전체 통과로 새지는 않았습니다.

### 증거 원문 — 결함 2

```text
python3 scripts/verify/check-hs-kickoff-identities.py --kind workflow-step --token hs-kickoff < /dev/null; echo rc=$?
ERROR: Unicode 매핑 데이터 입력 줄 없음
rc=2
printf '\n' | python3 scripts/verify/check-hs-kickoff-identities.py --kind workflow-step --token hs-kickoff; echo rc=$?
rc=0
CASE empty_disp rc=1
FAIL: 처분표에 PR #13 행 없음
FAIL: 처분표에 PR #54 행 없음
FAIL: 처분표에 PR #15 행 없음
FAIL: 처분표에 task/hs-d1-permit 행 없음
FAIL: 처분표에 task/hs-l1-malformed-url-fix 행 없음
FAIL: 처분표에 task/hs-observe-url-crash 행 없음
CHECKED: 12
```

→ helper 직접 호출은 빈 파일과 빈 줄 하나를 다르게 처리합니다. 실제 shell 처분표 경로는 빈 처분표를 전체 실패로 닫았습니다.

## 결함 3 — helper가 invalid UTF-8 stdin을 읽기 오류로 닫지 않음

- 상태: REPRODUCED
- 중요도: 낮음
- HS-00.03 종료 조건 필수 수정 여부: 단독으로는 아니오
- file:line 역할: `scripts/verify/check-hs-kickoff-identities.py:178`은 `sys.stdin` 텍스트 스트림을 그대로 순회합니다.
- 원인: 실행 환경에서 깨진 바이트가 Python 텍스트 입력 경로에서 오류로 닫히지 않고 대체되거나 통과해 helper가 종료값 0으로 끝납니다.
- 사업 영향: helper 단독 계약의 “읽기 오류는 종료값 2”와 어긋납니다. 다만 제가 만든 실제 처분표 invalid byte suffix 사본은 raw 선택에서 `PR #13` 행이 없어져 전체 acceptance가 종료값 1로 실패했습니다.

### 증거 원문 — 결함 3

```text
printf 'hs-kickoff\377\n' | python3 scripts/verify/check-hs-kickoff-identities.py --kind workflow-step --token hs-kickoff; echo rc=$?
rc=0
CASE disp_invalid_byte_suffix rc=1
FAIL: 처분표에 PR #13 행 없음
PASS: CI 스텝 수·이름·순서 정본=30 실제=30 표 행=30 빈 이름 0 번호 1..30 이름 1:1
PASS: CI 배선 2건 — 이름과 명령이 같은 스텝에서 일치하고 조건·오류무시 없음
CHECKED: 12
```

→ helper 직접 호출은 invalid UTF-8을 오류로 닫지 않았습니다. 실제 처분표 파일 변형 경로는 다른 검사에서 실패했습니다.

## 결함 4 — metadata-skip mutant는 생존하지만 병합 차단 사유는 아님

- 상태: REPRODUCED
- 중요도: 낮음
- HS-00.03 종료 조건 필수 수정 여부: 아니오
- file:line 역할: `scripts/verify/check-hs-kickoff-identities.py:61`은 JSON 파일의 SHA-256을 먼저 계산하는 줄입니다. `scripts/verify/check-hs-kickoff-identities.py:76`은 메타데이터 객체를 기대값과 비교하는 줄입니다.
- 원인: SHA 검사가 메타데이터 검사보다 먼저 실행됩니다. 파일 내용이 조금이라도 바뀌면 메타데이터 분기까지 가기 전에 실패하므로, 메타데이터 비교 분기를 단독으로 죽여도 현재 테스트가 잡지 못합니다.
- 사업 영향: SHA 검사가 유지되는 한 데이터 변조는 먼저 막힙니다. 방어 심층 분기의 시험 공백이므로 이번 FAIL의 주원인은 아닙니다.

### 증거 원문 — 결함 4

```text
metadata 비교를 `if False and ...`로 죽인 임시 사본:
...............                                                          [100%]
15 passed in 11.85s
```

→ V1의 metadata-skip 생존 기록은 재현됐습니다. 하지만 앞선 SHA 검사 때문에 이 생존만으로 제품 통과 여부를 뒤집지는 않습니다.

## 정상 control과 회귀 증거

```text
bash scripts/acceptance-hs-kickoff.sh
PASS: 처분 PR #13 → 결론=재작성 (근거 경로 1 건·커밋 1 건)
PASS: 처분 PR #54 → 결론=재작성 (근거 경로 1 건·커밋 1 건)
PASS: 처분 PR #15 → 결론=폐기 (근거 경로 1 건·커밋 1 건)
PASS: 처분 task/hs-d1-permit → 결론=재작성 (근거 경로 1 건·커밋 2 건)
PASS: 처분 task/hs-l1-malformed-url-fix → 결론=폐기 (근거 경로 1 건·커밋 1 건)
PASS: 처분 task/hs-observe-url-crash → 결론=폐기 (근거 경로 2 건·커밋 0 건)
PASS: CI 스텝 수·이름·순서 정본=30 실제=30 표 행=30 빈 이름 0 번호 1..30 이름 1:1
PASS: CI 배선 2건 — 이름과 명령이 같은 스텝에서 일치하고 조건·오류무시 없음
CHECKED: 12

cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py
15 passed in 11.43s

cd humansearch && uv run --no-sync pytest -q
277 passed in 35.33s

cd humansearch && uv run --no-sync ruff check . && uv run --no-sync mypy .
All checks passed!
Success: no issues found in 46 source files

bash scripts/acceptance-hs-kickoff-mutations.sh
CHECKED: 37

bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 정상 후보 자체의 기본 검사, 정조준 테스트, 전체 pytest, 정적 검사, 기존 37개 변이, strict 원칙 직접 로드는 통과했습니다. 이 통과는 위 반례의 acceptance 우회를 덮지 못합니다.

## 파일 지문과 미확인

```text
53e0f1e0610c3446a5062b4770ffdb4e1cac1b5c0cfc4af525167e16b6f0c22a  scripts/acceptance-hs-kickoff.sh
09fc5e28c650f4968c77e95dc72d3bd4126d92caa6c483210e30f2bb0674696e  scripts/acceptance-hs-kickoff-mutations.sh
337a598116943ca353f5f81c10a5269cc2bd083821d287b964e182c8a624712d  scripts/verify/check-hs-kickoff-identities.py
7694d91b0af2c7d6ee1e791474a393b8e7a14d9b27542e06315009e6d0f0449d  scripts/verify/generate-hs-kickoff-confusables.py
687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd  scripts/verify/hs-kickoff-confusables-17.0.0.json
e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96  docs/licenses/unicode-license-v3.txt
14998dea0d52845931f3e69c647608a73f99554147bb7a80bc0f66df5f7734c4  humansearch/tests/test_hs_0003.py
08d9adeb9f63ee2aae332229266ca38ca8924eab8b596add0eac406dc99d7a8f  docs/sot/verification-commands.md
```

→ 파일별 SHA는 V1이 남긴 값과 일치했습니다. 구현자가 제시한 묶음 지문 `07ce9970f7bce791d2f63cc41786abe64d8ad79a38546ca2a2cacbabc8ab6776`은 계산 방식이 없어 재현하지 못했습니다.

## 최종 판정

현재 GREEN 후보는 커밋 가능한 상태가 아닙니다. raw 선택과 helper shadow 판정을 같은 비교 기준으로 맞추고, 토큰 바로 앞뒤의 치환 문자가 shadow에서 ASCII 경계 문자가 되는 경우도 실패로 닫아야 HS-00.03 종료 조건을 만족합니다.
