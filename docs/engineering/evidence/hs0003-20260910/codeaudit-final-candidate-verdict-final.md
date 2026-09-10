VERDICT: PASS

## 결론

현재 후보는 통과로 봅니다. 전각 글자나 비슷하게 생긴 다른 문자로 보호 이름을 속이는 입력은 막혔고, 정상 이름은 계속 허용됐습니다.

건너뛴 것과 한계는 세 가지입니다. 원격 검사는 확인하지 않았고, AST 기반 검색 도구는 설치되어 있지 않아 일반 텍스트 검색으로 대체했습니다. LSP 진단 도구는 호출했지만 Python을 실제 분석하지 않고 타입스크립트 설정 파일이 없다는 메시지로 끝났으므로, 실질 타입 근거는 엄격 타입 검사입니다. 첫 수동 fixture 재현은 루트 Python에 시험 도구가 없어 실패했고, 같은 재현을 저장소가 쓰는 가상 환경에서 다시 실행해 성공했습니다.

## 요구사항·주장 대조표

| ID | 요구 | 판정 | 근거 | 공백/위험 | 중요도 |
|---|---|---|---|---|---|
| R1 | `PR #13１`, `ｘPR #13`, `ｘhs-kickoff (`를 거부 | 구현 확인 | `docs/engineering/humansearch-hs0003-goal-2026-09-10.md:56`은 앞뒤 치환 경계도 거부해야 한다는 합격 조건입니다. `scripts/verify/check-hs-kickoff-identities.py:143`은 토큰 양옆 치환 경계를 잡는 함수입니다. | 없음 | 낮음 |
| R2 | 정상 다국어, `PR #131`, `ＰR #131`, `hs-kickoff-other`, `hｓ-kickoff-other` 허용 | 구현 확인 | `docs/sot/verification-commands.md:102`가 정상 허용 경계를 정합니다. 직접 helper 호출에서 모두 종료값 0이었습니다. | 없음 | 낮음 |
| R3 | 빈 입력·빈 줄·깨진 UTF-8은 종료값 2 | 구현 확인 | `scripts/verify/check-hs-kickoff-identities.py:185`는 표준입력을 바이트로 읽고, `:190`은 UTF-8 strict 해독을 수행하며, `:197`은 실제 이름 줄 없음 오류를 냅니다. | 없음 | 낮음 |
| R4 | 토큰 내부 전각·Greek·Cyrillic 계속 거부 | 구현 확인 | `scripts/verify/check-hs-kickoff-identities.py:149`은 비교 사본에서 보호 토큰을 찾고, `:156`은 토큰 span 내부 치환을 거부합니다. 직접 호출에서 세 경우 모두 종료값 1이었습니다. | 없음 | 낮음 |
| R5 | mapping/data fail-closed | 구현 확인 | `scripts/verify/check-hs-kickoff-identities.py:61`은 데이터 파일을 읽고, `:66`은 SHA-256을 대조하며, `:75` 이후는 metadata·개수·target 계약을 확인합니다. | 같은 권한으로 코드와 데이터를 동시에 바꾸는 악의적 변경은 이 장치만으로 막지 못합니다. | 낮음 |
| R6 | 실제 shell 배선 유지 | 구현 확인 | `scripts/acceptance-hs-kickoff.sh:81`은 처분표 대상 칸을 helper에 넘기고, `:162`는 workflow/SOT 이름 칸을 넘기며, `:181`은 위장 또는 검사 오류를 전체 실패로 만듭니다. | 없음 | 낮음 |
| R7 | 기존 37 기대값 유지 | 구현 확인 | `bash scripts/acceptance-hs-kickoff-mutations.sh`가 `CHECKED: 37`로 통과했습니다. | 없음 | 낮음 |
| R8 | 공식 데이터·생성물 지문·라이선스·hard600/hard100 | 구현 확인 | manifest SHA `41aa89...aead4`, bundle `0ccf996...8c85`, Unicode JSON SHA `687cd7...cdfd`, 라이선스 SHA `e7a93...d96` 재현. 새 직접 작성 코드 파일은 600줄 아래, 함수는 100줄 아래입니다. | 600/601 고장 사본을 재실행하는 저장소 공식 검사기는 확인하지 못했습니다. 직접 줄 수와 함수 길이만 확인했습니다. | 낮음 |

→ 모든 핵심 요구는 현재 작업트리에서 구현 확인입니다. 남은 위험은 원격 CI 미확인과 아직 untracked인 새 파일들이 커밋 때 빠질 수 있다는 운영 위험입니다.

## 핵심 해설

이번 수정의 실제 흐름은 단순합니다. `acceptance-hs-kickoff.sh`가 처분표 대상 칸, workflow 스텝 이름, 정본 문서의 스텝 이름을 뽑아 `check-hs-kickoff-identities.py`에 넘깁니다. helper는 원문을 승인 값으로 바꾸지 않고, 비교용 사본만 만들어 전각 문자와 Unicode 17.0.0의 단일 글자 혼동 문자를 보호 ASCII로 바꿔 봅니다.

중요한 보강은 토큰 안쪽뿐 아니라 토큰 바로 앞뒤도 본다는 점입니다. 이전 V2 FAIL의 핵심이었던 `PR #13１`, `ｘPR #13`, `ｘhs-kickoff (`는 원문 기준으로는 보호 이름처럼 선택될 수 있지만, 비교 사본 기준으로는 보호 토큰 옆 경계 문자가 바뀐 상태입니다. 현재 코드는 이를 `SPOOF`로 실패시킵니다.

## 놓친 더 나은 답

초기 V1 PASS와 초기 V2 FAIL 산출물은 같은 후보 단계가 아닙니다. evidence 폴더의 초기 V1은 15/277 수치를 말하고, 초기 V2는 경계 우회를 FAIL로 잡았습니다. 현재 후보는 그 뒤 `d1058ca` 테스트 커밋과 구현 보강이 반영되어 21/283으로 올라간 상태입니다. 그래서 초기 판정 원문은 “과거 후보의 증거”로 읽어야 하고, 최종 결론은 현재 작업트리 실행 결과에 귀속해야 합니다.

더 좋은 최종 보고에는 이 구분이 명시돼야 합니다. 그렇지 않으면 “V2가 FAIL이라는데 왜 PASS인가”라는 오해가 생깁니다.

## 적대 반박

가장 강한 반론은 “helper만 통과하고 실제 acceptance는 여전히 raw 선택으로 속을 수 있다”입니다. 이 반론은 직접 재현으로 깼습니다.

```text
rc= 1
SPOOF: workflow-step line=29 token=hs-kickoff
SPOOF: sot-step line=29 token=hs-kickoff
FAIL: CI·정본 스텝 이름 Unicode 위장 또는 검사 오류
CHECKED: 12
FAIL(run-acceptance): scripts/acceptance-hs-kickoff.sh 종료값 1
```

→ workflow와 정본에 `ｘhs-kickoff (`를 함께 넣은 전체 acceptance가 실패했습니다. helper 단위가 아니라 실제 shell 경로가 실패한 증거입니다.

두 번째 반론은 “항상 허용/항상 거부 같은 가짜 구현도 시험을 통과할 수 있지 않나”입니다. 임시 사본에서 무력화했을 때 반대 결과가 나타났고, 현재 시험의 단언에 걸리는 것을 확인했습니다.

```text
always_allow_spoof_workflow caught= True rc= 0 expect= 0
always_reject_normal_baseline caught= True rc= 1 expect= 1
boundary_guard_removed caught= True rc= 0 expect= 0
strict_utf8_decode_removed rc= 0
```

→ 항상 허용, 항상 거부, 경계 삭제, UTF-8 strict 삭제는 모두 잘못된 결과를 만들었습니다. 현재 테스트는 그 반대 동작을 요구하므로 이 무력화들은 새 시험에 잡힙니다.

## 결정 카드

**무엇을** — 원문 파일은 그대로 두고, 같은 독립 검토자의 판정과 내용을 줄이지 않는 형식 보정본을 별도 evidence 파일로 둡니다.

**왜** — 원문에는 결론 제목 위치와 표 해석 누락이라는 형식 위반이 있지만, 판정 자체와 증거 내용은 유지해야 하기 때문입니다.

**버린 길** — 원문을 직접 고치는 방법은 원문 보존 요청을 어기므로 버렸습니다.

**대가** — 같은 판정이 두 파일에 남아 이후 커밋 때 둘 다 포함해야 합니다.

**되돌리기** — 형식 보정본 파일만 삭제하면 원문 보존 상태로 돌아갑니다.

## 근거 장부

| 주장 | 판정 | 1차 근거 | 근거 강도 | 미확인 |
|---|---|---|---|---|
| target test는 21개 | 확인 | `21 passed in 17.23s` | 강함 | 없음 |
| 정조준 묶음은 72개 | 확인 | `72 passed in 30.07s` | 강함 | 없음 |
| 전체 G2는 283개 | 확인 | `PASS: pytest collected 283 and passed`, `COLLECTED: 283` | 강함 | 원격 CI |
| 기존 kickoff 변이는 37개 | 확인 | `CHECKED: 37` | 강함 | 없음 |
| ruff/mypy 통과 | 확인 | `All checks passed!`, `Success: no issues found in 46 source files` | 강함 | LSP Python 실진단 |
| manifest 재계산 일치 | 확인 | 모든 파일 `OK`, bundle `0ccf996...8c85`, manifest SHA `41aa89...aead4` | 강함 | 없음 |
| 비밀값 검사 | 확인 | `PASS: no secret-pattern match in any tracked file, .env not tracked` | 중간 | untracked evidence 전체에 대한 별도 비밀 스캔은 하지 않음 |
| ast-grep | 미확인 | 도구 응답: `ast-grep not installed` | 낮음 | `rg` 패턴 검색으로 대체 |

→ 근거 장부는 실행 수치와 미확인 범위를 분리합니다. 좋은 소식은 핵심 시험·정적 검사·manifest 지문이 맞는다는 점이고, 남은 한계는 원격 CI와 Python LSP 실진단을 확인하지 못했다는 점입니다.

## 반복 질문 조사

이번 하위 감사에서는 사용자 보관 세션 검색을 하지 않았습니다. 확인 범위는 현재 작업 지시, 지정 worktree, SOT/goal/evidence 파일, 현재 실행 결과입니다. 따라서 “같은 질문이 몇 번째인지”는 미확인입니다.

## 검증 신뢰도와 우선순위

실행 원문 핵심은 다음과 같습니다.

```text
uv run --no-sync pytest -q tests/test_hs_0003.py
21 passed in 17.23s
```

→ 새 HS-00.03 단위 시험 21개가 모두 통과했습니다.

```text
uv run --no-sync pytest -q tests/test_hs_0003.py tests/test_hs_0001.py tests/test_hs_0001_main_compat.py tests/test_hs_0002.py tests/test_hs_0002_boundaries.py
72 passed in 30.07s
```

→ 사용자가 요구한 정확한 정조준 묶음 72개가 통과했습니다.

```text
bash scripts/acceptance-hs-gates.sh
PASS: ruff clean in 46 python files
PASS: mypy strict clean in 46 source files
PASS: pytest collected 283 and passed
COLLECTED: 283
```

→ 전체 HumanSearch G2가 통과했습니다.

```text
bash scripts/acceptance-hs-kickoff-mutations.sh
CHECKED: 37
```

→ 기존 37개 kickoff 변이 기대값이 유지됐습니다.

```text
bundle 0ccf996ee201ecabe4b1a66b6c00f2a04a669c5476960f8c1feca026f12b8c85
41aa89efa6c883a64d333d9428fea33a22a1f13f8fe1142364e58521649aead4  docs/engineering/evidence/hs0003-20260910/candidate-product-manifest.json
```

→ 후보 manifest와 명시 bundle 지문이 요청값과 일치합니다.

최종 권고는 `APPROVE / PASS`입니다. 커밋할 때는 현재 untracked 새 파일들, 특히 `scripts/verify/check-hs-kickoff-identities.py`, `scripts/verify/generate-hs-kickoff-confusables.py`, `scripts/verify/hs-kickoff-confusables-17.0.0.json`, `docs/licenses/unicode-license-v3.txt`, evidence manifest가 빠지지 않아야 합니다.
