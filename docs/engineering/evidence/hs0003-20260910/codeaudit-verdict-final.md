VERDICT: PASS

## 결론

현재 작업트리 기준으로 사용자가 요구한 보호 이름 위장 차단은 작동한다. 큰 결함은 찾지 못했고, 남은 위험은 새 파일들이 아직 추적되지 않은 상태라 커밋 때 빠지면 깨진다는 운영 위험이다.

## 판단 근거

실제 흐름은 `acceptance-hs-kickoff.sh`가 workflow step name, SOT step-name cell, 처분표 target cell을 파싱한 뒤 `check-hs-kickoff-identities.py`에 넘기는 구조다. 검사기는 원문을 바꾸지 않고 별도 비교 사본만 만든다. 비교 사본에서 보호 토큰이 생기고 그 토큰 안에 치환된 글자가 있으면 `SPOOF`를 출력하고 실패한다.

데이터 쪽은 고정 Unicode 17.0.0 원본 SHA, 저장 JSON SHA, metadata, mapping count 628개를 모두 확인한다. 같은 개수로 보이는 데이터 변조도 저장 JSON SHA가 달라져 종료값 2로 실패했다.

구현 결함은 아니지만 커밋 준비 상태에는 주의가 필요하다. `git status` 기준 새 파일 `docs/licenses/unicode-license-v3.txt`, `scripts/verify/check-hs-kickoff-identities.py`, `scripts/verify/generate-hs-kickoff-confusables.py`, `scripts/verify/hs-kickoff-confusables-17.0.0.json`은 아직 untracked다. 이 파일들이 커밋에서 빠지면 현재 PASS는 재현되지 않는다.

가장 강한 반론은 “테스트가 구현과 같은 shadow 로직을 베껴서 거짓 초록을 만든 것 아닌가”다. 반박 근거는 테스트가 helper를 직접 검증하는 대신 fixture 저장소에서 `scripts/acceptance-hs-kickoff.sh`를 실행한다는 점이다. [test_hs_0003.py:107](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/humansearch/tests/test_hs_0003.py:107)은 실제 acceptance 실행 결과를 본다.

수정된 결론은 PASS다. 다만 내부 해시 검사는 같은 권한으로 코드 상수와 데이터 파일을 함께 바꾸는 악의적 변경까지 막는 장치는 아니다. 이 감사에서는 데이터 단독 손상과 재생성 불일치를 확인했다.

**결정 카드**

**무엇을** — 원문은 보존하고 보호 토큰 span에만 고정 Unicode 데이터를 적용한 비교 사본으로 위장을 탐지한다.

**왜** — 전체 이름을 바꾸지 않으면서 전각·그리스·키릴 등 실제 동형 문자를 넓게 잡고, 정상 한글·다국어 이름을 유지할 수 있다.

**버린 길** — 전체 NFKC/UTS #39 skeleton은 공백·결합·보이지 않는 문자와 다중문자 span 정책까지 넓어져 이번 한 작업 단위의 계약을 넘는다. 전각+U+0455 손목록은 알려진 Greek/Cyrillic 반례를 남긴다.

**대가** — 고정 버전 데이터의 재생성·라이선스 보존이 필요하고, 다중문자·bidi·보이지 않는 문자 공격은 계속 비지원이다.

**되돌리기** — GREEN 구현 커밋만 revert하고 RED 시험을 유지해 위장 반례가 다시 실패하는지 확인한다.

## 기술 상세와 증거

### 요구사항·주장 대조표

| ID | 요구 | 판정 | 근거 | 공백/위험 | 중요도 |
|---|---|---|---|---|---|
| R1 | 전각·동형문자 보호 이름 거부 | 구현 확인 | [check-hs-kickoff-identities.py:115](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/verify/check-hs-kickoff-identities.py:115) 비교 사본 생성, [acceptance-hs-kickoff.sh:162](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/acceptance-hs-kickoff.sh:162) workflow/SOT 이름 전달 | 없음 | 낮음 |
| R2 | 정상 한글·다국어·무관 전각 과잉 차단 금지 | 구현 확인 | [test_hs_0003.py:99](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/humansearch/tests/test_hs_0003.py:99) 정상 다국어 통과 시험 | 없음 | 낮음 |
| R3 | raw 보존, 승인값으로 정규화 금지 | 구현 확인 | [check-hs-kickoff-identities.py:138](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/verify/check-hs-kickoff-identities.py:138) shadow만 만들고 원문은 출력 승인에 쓰지 않음 | 없음 | 낮음 |
| R4 | 기존 ASCII 필터 전 검사 | 구현 확인 | [acceptance-hs-kickoff.sh:81](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/acceptance-hs-kickoff.sh:81) 처분 대상 전체를 먼저 검사, [acceptance-hs-kickoff.sh:181](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/acceptance-hs-kickoff.sh:181) 스텝 비교 전 실패 | 없음 | 낮음 |
| R5 | `PR #131`/`PR #13`, `hs-kickoff-other` 경계 유지 | 구현 확인 | [check-hs-kickoff-identities.py:132](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/verify/check-hs-kickoff-identities.py:132) ASCII 경계 검사 | 직접 호출에서 `ＰR #131` rc=0 확인 | 낮음 |
| R6 | 데이터 오류 fail-closed | 구현 확인 | [check-hs-kickoff-identities.py:56](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/verify/check-hs-kickoff-identities.py:56) 파일 지문 검사, [test_hs_0003.py:193](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/humansearch/tests/test_hs_0003.py:193) 오류 변이 시험 | 같은 권한으로 코드+데이터를 같이 바꾸는 공격은 별도 통제 필요 | 낮음 |
| R7 | 전체 bidi·결합·보이지 않는 문자 지원 주장 금지 | 구현 확인 | [humansearch-hs0003-goal-2026-09-10.md:16](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/docs/engineering/humansearch-hs0003-goal-2026-09-10.md:16) 범위 포함/제외 명시, [verification-commands.md:100](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/docs/sot/verification-commands.md:100) 비지원 명시 | 없음 | 낮음 |
| R8 | 새 의존성 금지 | 구현 확인 | Python 표준 라이브러리와 기존 shell만 사용 | 없음 | 낮음 |

→ 요구별 판정은 모두 구현 확인이다. 남은 위험은 R6의 같은 권한 코드+데이터 동시 변조와 커밋 누락 위험이며, 제품 코드 결함으로 인한 REQUEST CHANGES 사유는 찾지 못했다.

### 근거 장부

| 주장 | 판정 | 1차 근거 | 근거 강도 | 미확인 |
|---|---|---|---|---|
| Unicode 17.0.0 데이터 재현 가능 | 확인 | `curl` 원본 SHA `091c...22a`, 생성 JSON SHA `687c...dfd`, `cmp_rc=0` | 강함 | Unicode 사이트 장기 가용성 |
| 기존 회귀 유지 | 확인 | `66 passed`, `CHECKED: 37`, `COLLECTED: 277` | 강함 | 원격 CI |
| 비밀값 노출 없음 | 확인 | `bash verify.sh` 결과 `PASS: no secret-pattern match in any tracked file, .env not tracked` | 중간 | untracked 전체 비밀 스캔은 별도 미실행 |
| 정적 품질 | 확인 | `ruff check` 통과, `acceptance-hs-gates.sh` mypy strict 통과 | 강함 | LSP 전용 진단 도구는 없음 |

→ 근거는 로컬 실행과 공식 Unicode 17.0.0 원본 재생성으로 강하게 받쳐진다. 원격 CI, untracked 전체 비밀 스캔, LSP 전용 진단은 이 감사에서 확인하지 않았다.

### 반복 질문 조사

이 하위 감사에서는 별도 사용자 보관 세션을 검색하지 않았다. 확인 범위는 현재 전달받은 작업 지시, 현재 작업트리, 지정된 SOT/goal/test/script 파일, 실행 결과다. 따라서 “현재가 몇 번째 같은 질문인지”는 미확인이다.

### 검증 신뢰도와 우선순위

실행한 명령과 결과는 다음과 같다.

```text
cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py tests/test_hs_0001.py tests/test_hs_0001_main_compat.py tests/test_hs_0002.py tests/test_hs_0002_boundaries.py
66 passed
```

→ 새 Unicode 위장 시험과 기존 HS-00.01/02 회귀가 함께 통과했다.

```text
bash scripts/acceptance-hs-kickoff.sh
CHECKED: 12
exit 0
```

→ 실제 착수 acceptance가 현재 저장소에서 통과했다.

```text
bash scripts/acceptance-hs-kickoff-mutations.sh
CHECKED: 37
exit 0
```

→ 기존 37개 양성/음성 변이 기대값이 유지됐다.

```text
bash scripts/acceptance-hs-gates.sh
PASS: ruff clean in 46 python files
PASS: mypy strict clean in 46 source files
PASS: pytest collected 277 and passed
COLLECTED: 277
```

→ 기존 HumanSearch 게이트 전체가 통과했다.

```text
curl -fsSL https://www.unicode.org/Public/17.0.0/security/confusables.txt ...
source sha256=091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a
generated sha256=687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd
cmp_rc=0
```

→ 생성기가 공식 고정 원본에서 현재 JSON을 그대로 재생성했다.

우선순위는 하나다: 커밋 시 untracked 새 파일 4개를 반드시 포함해야 한다. 제품 코드 결함으로 인한 REQUEST CHANGES 사유는 찾지 못했다.
