# HumanSearch L0 인증 화면 분류 구현 목표 — 2026-08-18

## 1층 — 결론

이번 작업은 현재 화면의 로그인 관련 의미만 다섯 결과 중 하나로 고릅니다. 실제 채용 사이트와 사람
자료는 건드리지 않고, 검토 요청을 만든 뒤 멈춥니다.

제가 앞서 일곱 가지 상태를 한꺼번에 구현하라고 한 판단은 취소합니다. 저장소의 더 구체적인 계약을
끝까지 읽은 결과, 첫 기능과 후속 실행 절차를 섞은 과장이었습니다.

## 2층 — 판단 근거

현재 화면을 읽은 결과와 로그인 이후 실행 흐름은 바뀌는 이유와 검증 방법이 다릅니다. 첫 기능은
화면 의미 세 가지의 가능한 조합을 모두 셀 수 있지만, 재확인·세션 충돌·실행 시작은 시간, 좌석,
사람 개입을 포함하는 후속 단계입니다.

이번에는 화면 분류만 순수 함수(= 외부 접속이나 저장 없이 입력값만으로 결과를 내는 함수)로
고정합니다. 역할이 서로 충돌하면 하나를 임의로 고르지 않고 화면 구조가 달라진 것으로 멈춥니다.

**무엇을** — 세 의미 역할과 관측 유효성을 다섯 화면 결과로 분류하는 기능 하나를 구현합니다.

**왜** — 정상 입력이 16개뿐이라 빠짐없이 시험할 수 있고, 미로그인이나 모순 화면이 인증 성공으로
새는 경로를 먼저 막을 수 있습니다.

**버린 길** — 일곱 가지 전체 로그인 상태를 한 코드에 넣는 길을 버렸습니다. 후속 실행 순서를 첫
화면 분류가 소유하게 되어 책임과 시험이 섞이기 때문입니다.

**대가** — 이번 결과만으로 실제 후보자를 찾을 수 없습니다. 실제 화면을 의미 역할로 바꾸는 다음
계층이 아직 없기 때문입니다.

**되돌리기** — 검토 요청을 합치지 않으면 현재 원격 기본선에는 아무 영향이 없습니다. 계약이 틀린
경우 이 작은 요청에서 문서·시험·구현을 함께 고치면 됩니다.

## 3층 — 기술 계약과 증거

### 현재 상태와 스캔 범위

스캔 범위는 원격 기본선 `origin/main`, 현재 저장소의 `docs/sot/`, `docs/engineering/`,
`humansearch/`, `scripts/`, 열린 HumanSearch 관련 변경 요청과 로컬 작업공간 목록이다. 실제 포털,
후보자 데이터, 다른 저장소의 제품 코드는 범위 밖이다.

- `humansearch/src/humansearch/__init__.py:1-6`은 패키지 경계 설명과 빈 공개 목록만 갖고 있다.
  → 제품 상태 분류 구현과 공개 호출 경로가 아직 없다는 뜻이다.
- `humansearch/pyproject.toml:6-8`은 순수 판정 함수가 생길 때 Hypothesis를 추가하라고 기록한다.
  → 지금이 그 개발 의존성을 실제 시험과 함께 추가할 시점이다.
- `docs/sot/coding-principles.md`의 P5는 순수 판정 함수에 속성 기반 시험(= 자동 생성 입력으로 공통
  성질을 검사)을 요구한다.
  → 정상 예시 몇 개만 고르는 시험으로는 합격할 수 없다.
- `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md:236-275`는 주소가 아니라 화면 구조
  마커로 인증을 판단하고, 화면 구조 변경과 세션 충돌을 명시 실패로 처리하라고 기록한다.
  → L0는 포털별 문자열 없이 의미 역할만 소비해야 한다.

기존 실행 지시 두 개는 다섯 화면 결과와 일곱 실행 상태를 서로 다르게 적었다. 열린 PR #15에는 이
충돌을 “다섯 결과의 화면 분류와 후속 실행 상태를 분리”하는 정본 초안이 있다. 이번 변경은 그 작은
계약과 구현만 원격 기본선에서 독립된 변경 요청으로 만든다. PR #13, #14, #15를 합치거나 대신
수정하지 않는다.

### 근본 원인

L0의 이름을 “로그인 상태”라고 넓게 부르면서 현재 화면 분류와 시간에 따른 실행 전이를 같은 열거형에
넣었다. 그 결과 `AUTHENTICATED`가 화면 관측 결과인지 실행 종료인지 모호해졌고, 화면에 존재하지 않는
`human_login_done`과 `structure_drift`를 화면 역할처럼 만들었다.

### 단일 인수 기준

이슈: <https://github.com/sangmokang/Valuehire_v6/issues/25>

> 세 의미 역할과 관측 유효성으로 만들 수 있는 정상 입력 16개를 모두 정본 결정표대로 분류하고,
> 잘못된 입력은 전부 명시적으로 거부하며, 같은 입력은 항상 같은 결과를 낸다.

반대 사례는 다음과 같다.

- 빈 관측이 인증 성공으로 분류된다.
- 서로 다른 역할 두 개 이상이 보일 때 한쪽에 우선순위를 줘 정상 상태로 축소한다.
- 문자열이 열거형 값과 같다는 이유만으로 잘못된 입력을 허용한다.
- 같은 입력이 시계, 난수, 파일, 환경에 따라 다른 결과를 낸다.
- 제품 코드에 포털명, 주소, 화면 요소, 네트워크나 파일 접근이 들어간다.

### Harness 게이트 진행

`bash scripts/session-status.sh`를 기존 기본 작업공간에서 처음 실행한 결과는 다음과 같다.

```text
HEAD: 74bde5c (ahead 6 / behind 0)
ORIGIN: 4fdef31
RED: 2/19 (acceptance-0-7.sh 제외 — CI 담당)
```
→ 프로그램 종료 성적은 0이었지만 빨간불 수치가 2라 시작 자격은 불합격이다. 하나는 복구용 Git
흔적 211개, 다른 하나는 로컬 기본선이 원격보다 문서 커밋 6개 앞선 문제였다.

중복 실행을 정리하는 과정에서 한 회차는 종료 성적 143을 남겼다. 이 숫자는 정상 완료가 아니라
중단을 뜻하므로 합격 근거에서 제외했다.

기존 자료를 삭제하거나 기본선을 되돌리지 않기 위해 원격 기준의 깨끗한 복제본을 만들었다. 첫
재실행은 개인 비밀 패턴 파일이 없어 다음처럼 판정 불가였다.

```text
HEAD: 4fdef31 (synced)
ORIGIN: 4fdef31
RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)
FAIL: .secret-patterns 없음/빈 파일 — AC 판정 불가
```
→ 코드 결함이 아니라 로컬 전용 검사 입력이 복제되지 않은 상태였다. 파일 내용은 출력하거나 Git에
넣지 않고 권한 0600으로 복제본에만 배치했다.

동일한 원명령을 다시 실행한 최종 결과는 다음과 같다.

```text
HEAD: 4fdef31 (synced)
ORIGIN: 4fdef31
RED: 0/19 (acceptance-0-7.sh 제외 — CI 담당)
```
→ 전체 19개 중 미해결 빨간불이 0개이고 알 수 없음 표시가 없어 게이트 0을 통과했다.

GitHub 이슈 생성은 두 번의 화면 명령과 한 번의 공식 요청 명령에서 HTTP 503으로 실패했다. 저장소
조회가 복구된 뒤 공식 요청 명령을 재실행해 이슈 #25를 만들었다.

현재 작업공간은
`worktrees/humansearch-l0-surface-classifier`, 브랜치는
`task/humansearch-l0-surface-classifier`, 기준 지문은
`4fdef31fe75c8519091cebe8a6c4cbf5be1893ae`다.

최종 검증 직전 `origin/main`에 복구 흔적 검사 보정 PR #23이 합쳐져 기준선이
`6a4f2f09098f8c42dbe584d451091edc076152d1`로 바뀌었다. L0 제품 파일과 겹치지 않음을 확인한 뒤
아직 원격에 올리지 않은 작업 브랜치를 최신 기준선 위로 재배치했다. 최종 제품 검증 기준 지문은
`84050bf28ff89039c771be70a950a1a4e4da9a4a`이며, 재배치 뒤 원명령 결과는 다음과 같다.

```text
HEAD: 84050bf (ahead 5 / behind 0)
ORIGIN: 6a4f2f0
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 기본선 뒤처짐 0, 현재 20개 로컬 시작 검사 중 빨간불 0으로 최종 기준을 다시 고정했다.

### 구현 순서

1. 이 목표와 L0 정본 계약을 코드보다 먼저 커밋한다.
2. 시험과 Hypothesis 의존성만 추가해 기능 부재로 실패하는 RED를 커밋한다.
3. 시험을 바꾸지 않고 최소 제품 코드와 공개 내보내기만 추가해 GREEN을 만든다.
4. 부분 시험, 전체 HumanSearch 검사, 저장소 검증, 변조 시험을 실행한다.
5. Claude가 다른 엔진으로 1차 공격하고, Codex가 모든 판정을 같은 명령으로 재현한다.
6. 증거를 이 문서에 보존하고 일반 push와 한국어 검토 요청까지만 진행한다.

### 적대 검증 항목

- 정상 입력 16개가 정말 전부 수집되는가.
- 잘못된 타입이 `UNKNOWN`이나 `DRIFTED`로 위장되지 않고 프로그래머 오류로 거부되는가.
- 유효하지 않은 관측과 다중 역할이 항상 `DRIFTED`인가.
- 속성 기반 시험이 실제로 수집·실행되는가.
- RED 이후 GREEN에서 시험·의존성·잠금 파일을 바꾸지 않았는가.
- 공개 내보내기가 실제 패키지 불러오기 경로에 연결됐는가.
- 제품 모듈에 네트워크, 파일, 환경변수, 시계, 난수, 화면 요소나 포털 문자열이 없는가.
- 목표 문서가 실행하지 않은 검사나 결과를 합격으로 과장하지 않았는가.

### 읽은 정본

- `docs/sot/INDEX.md`
- `docs/sot/coding-principles.md`
- `docs/sot/git-workflow.md`
- `docs/sot/hook-contracts.md`
- `docs/sot/verification-commands.md`
- `docs/sot/mechanism-registry.yaml`
- `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md`
- `~/.claude/skills/harness/SKILL.md`
- `~/.codex/skills/strict/SKILL.md`

### 비범위와 선택 검사 상태

- 실제 포털, 브라우저, 로그인, 세션, 자격증명, 화면 캡처, 후보자 개인정보: `SKIPPED`. 첫 검사
  실행 전에 사용자와 이 목표가 순수 내부 로직으로 범위를 고정했다.
- 재확인, 세션 충돌의 종료 행동, 실행 시작, 후보 검색·저장·발송: `SKIPPED`. 별도 후속 계약이다.
- 화면 변경과 사용자 화면: `SKIPPED`. 이번 변경에는 사용자 화면이 없다.
- 합치기, 배포, 운영 반영: 권한 밖이며 실행하지 않는다.

순수 함수의 실제 호출 경로는 패키지 공개 내보내기와 별도 런타임 프로세스에서 한 건을 실행해
증명한다. 이것은 실제 채용 포털 라이브 증거라고 부르지 않는다.

## 적대 검증 로그

아래 기록은 최종 제품 기준 지문 `84050bf28ff89039c771be70a950a1a4e4da9a4a`에서 실행했다. 재배치
전 Claude 검증은 최종 판정 근거에서 제외했고, 같은 검증을 최종 지문에서 새로 실행했다.

### Claude V1 — 실행 명령과 프롬프트

명령:

`env -u ANTHROPIC_API_KEY claude -p "<아래 프롬프트 전문>"`

프롬프트 전문:

~~~text
당신은 Valuehire_v6 HumanSearch L0 변경의 1차 적대 검증자입니다. 반드시 읽기 전용으로 검증하고, 대상 작업트리 파일은 수정하지 마십시오.

대상:
- 저장소: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-l0-surface-classifier
- 브랜치: task/humansearch-l0-surface-classifier
- 최종 기준: 현재 HEAD, origin/main 기준 diff
- 사용자 요청: "$strict L0 시작"
- Issue: #25
- goal: docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md
- SOT: docs/sot/humansearch-l0-surface-contract.md
- 구현: humansearch/src/humansearch/auth_surface.py
- 테스트: humansearch/tests/test_auth_surface.py

판단 계약:
1. L0는 포털 접속/로그인 자동화가 아니라 이미 정규화된 현재 인증 화면 관측을 순수 함수로 5상태(unknown, human_auth, authenticated, challenge, drifted)로 분류하는 최소 기능이다.
2. 입력 역할은 authenticated_surface, human_auth_surface, challenge_surface 정확히 3개다.
3. contract_valid=false 또는 역할 복수 매칭은 drifted다. 유효한 무매칭은 unknown이다.
4. 외부 I/O, DOM/URL/포털 문자열, 시간/랜덤/환경 의존은 금지한다.
5. AC는 "모든 정상 16조합과 잘못된 입력이 결정적으로 분류/거부되고, 정적 검사·테스트·게이트·비밀/노출 검사·변조 시험이 통과한다" 하나다.
6. RECHECK, AUTH_CONFLICT, RUNNING, STOP, 실제 사람인 접속/세션/후보 수집은 후속 계층이며 이번 범위가 아니다.
7. 변경은 최소·명시적이어야 하며 테스트가 구현 결함을 실제로 잡아야 한다.

필수 검증:
- git status --short --branch
- git diff --check
- git diff --stat origin/main...HEAD
- bash scripts/acceptance-hs-gates.sh
- bash scripts/acceptance-hs-gates-mutations.sh
- bash scripts/acceptance-hs-gates-antiforge.sh
- bash scripts/acceptance-hs-cleanroom.sh
- bash verify.sh
- bash scripts/scan-data-exposure.sh all
- gh issue view 25 --json number,state,title,url
- 코드/SOT/goal/테스트를 직접 읽고 계약 일치, 누락, 과잉 구현, 테스트 독립성, 공개 API, 실패 안전성을 공격적으로 검토한다.
- 대상 작업트리를 건드리지 않는 별도 임시 복제본에서 최소 3개 의미 변조를 주입해 테스트가 실패하는지 확인한다:
  A. 복수 역할 DRIFTED 가드를 제거
  B. contract_valid=false를 UNKNOWN으로 바꿈
  C. 잘못된 observation 타입 검사를 제거
  각 변조 뒤 원본 복원/대상 clean 여부를 확인한다.
- 첫 문서에 기록된 재배치 전 검증 숫자를 믿지 말고 현재 HEAD에서 직접 재현한다.

출력 형식:
VERDICT: PASS 또는 FAIL
결론:
추론:
발견사항:
- [심각도] 파일:줄 — 내용 (없으면 "차단 결함 없음")
검증 증거:
- 실행한 각 명령을 정확히 적고, 종료코드와 전체 출력을 생략 없이 붙인다.
변조 증거:
- A/B/C 각각 정확한 변조/실행 명령, 종료코드, 전체 테스트 출력을 붙인다.
불일치/한계:
- 문서/코드/테스트/기존 주장과의 불일치, 확인하지 못한 항목을 명시한다.
최종 판단:
- PASS/FAIL 이유를 요구사항·결정 기준·증거에 연결한다.

요약만 하지 말고 재현 가능한 명령과 전체 출력을 보존하십시오.
~~~

### Claude V1 — 1차 출력 원문

~~~text
# HumanSearch L0 적대 검증 보고 (1차)

VERDICT: **PASS**

## 결론

현재 HEAD(84050bf)는 판단 계약 1~7을 모두 충족합니다. 정상 입력 16조합 전수 시험, 잘못된 입력 5종 거부, Hypothesis 속성 시험, 패키지 공개 경로 시험이 모두 현재 HEAD에서 재현 통과했고, 게이트·변조·위조방지·클린룸·비밀·노출 검사 전부 통과했습니다. 별도 임시 복제본에 주입한 의미 변조 A/B/C 3종은 모두 테스트가 잡아냈습니다. 대상 작업트리는 검증 전후 clean이며 한 파일도 수정하지 않았습니다.

## 추론

- **범위 일치**: `auth_surface.py`는 `dataclasses`, `enum`만 import하는 73줄 순수 모듈입니다. 네트워크/파일/시간/난수/환경/DOM/URL/포털 문자열이 전혀 없습니다(파일 전문 직접 확인). 상태기계 요소(`transition`, `RECHECK`, `RUNNING` 등)는 존재하지 않고 SOT가 명시한 5개 공개 이름만 내보냅니다.
- **결정표 일치**: 구현의 분기(`not contract_valid or len(roles) > 1 → DRIFTED`, 빈 집합 → `UNKNOWN`, 단일 역할 → 매핑)는 SOT 결정표와 정확히 일치합니다. 위험 역할 우선순위가 없어 모순 관측이 `AUTHENTICATED`로 축소될 경로가 없습니다.
- **테스트가 실제로 결함을 잡는가**: 테스트의 `_expected_state`는 구현과 같은 로직을 복제한 오라클이라 "구현 미러링" 위험이 있지만, 16조합 전수 파라미터화 + 불변식 단언(`DRIFTED`/`UNKNOWN` 직접 단언, `not _is_authenticated`)이 별도로 있어 변조 A/B/C 모두 오라클이 아닌 독립 단언에서도 잡혔습니다.
- **타입 거부의 엄격성**: `type(...) is` 동일성 검사라 `contract_valid=1`(bool 아님), `set`, 문자열이 열거형 값과 같은 경우(`"authenticated_surface"`)까지 거부합니다. `SurfaceRole`이 `str` 서브클래스라 문자열이 frozenset 안에서 해시 충돌로 위장할 수 있는데, 테스트 5번째 케이스는 서로 다른 값의 역할+문자열 혼합을 써서 이 함정을 피해 실제 거부를 검증합니다.
- **RED→GREEN 경계**: RED(3487d3a)는 테스트+의존성+잠금만, GREEN(c42ccd7)은 제품 모듈+공개 내보내기만 변경 — 불변식 준수. GREEN 이후 테스트를 바꾼 84050bf는 diff 전문 확인 결과 import 재배치(모듈 직접 → 패키지 경유) 5줄뿐이며 기대값·단언·수집 수 무변경입니다(아래 불일치 항목 참조).

## 발견사항

- 차단 결함 없음
- [정보] humansearch/tests/test_auth_surface.py:9 — 커밋 84050bf(Phase: FIX)가 GREEN 이후 테스트 파일을 변경. goal 문서의 "GREEN은 RED의 기대값을 바꾸지 않는다" 불변식과 표면상 긴장이 있으나, diff 전문 검토 결과 import 그룹 재배치만 있고 기대값·단언은 동일. 검사 약화 아님.
- [정보] humansearch/tests/test_auth_surface.py:27 — `_expected_state`가 구현 로직을 미러링하는 오라클. 단독이었다면 약점이나, 16조합 명시 파라미터화와 독립 불변식 단언이 병존해 변조 시험에서 실효성이 증명됨.
- [정보] humansearch/src/humansearch/__init__.py:11 — `PACKAGE_NAME`이 `__all__` 밖에 남아 있음(기존 코드 유지). SOT의 "공개 이름 제한" 위반으로 보기 어려운 수준.

## 검증 증거

**1. `git status --short --branch`** — exit 0
```
## task/humansearch-l0-surface-classifier...origin/main [ahead 5]
```

**2. `git diff --check`** — exit 0, 출력 없음(공백 오류 0).

**3. `git diff --stat origin/main...HEAD`** — exit 0
```
 .../humansearch-l0-auth-surface-goal-2026-08-18.md | 169 +++++++++++++++++++++
 docs/sot/INDEX.md                                  |   1 +
 docs/sot/humansearch-l0-surface-contract.md        | 142 +++++++++++++++++
 humansearch/pyproject.toml                         |   1 +
 humansearch/src/humansearch/__init__.py            |  19 ++-
 humansearch/src/humansearch/auth_surface.py        |  73 +++++++++
 humansearch/tests/test_auth_surface.py             | 141 +++++++++++++++++
 humansearch/uv.lock                                |  69 +++++++++
 8 files changed, 612 insertions(+), 3 deletions(-)
```

**4. `bash scripts/acceptance-hs-gates.sh`** — exit 0
```
PASS: ruff clean in 4 python files
PASS: mypy strict clean in 4 source files
PASS: pytest collected 25 and passed
PASS: runtime import proof /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-l0-surface-classifier/humansearch/src/humansearch/__init__.py
COLLECTED: 25
```
(25 = test_auth_surface.py 24건 + test_package_boundary.py 1건, `pytest --collect-only -q`로 구성 확인: `25 tests collected in 0.17s`)

**5. `bash scripts/acceptance-hs-gates-mutations.sh`** — exit 0
```
PASS: gates mutations blocked 6/6
```

**6. `bash scripts/acceptance-hs-gates-antiforge.sh`** — exit 0
```
PASS: gates antiforge 3/3 (evidence forgery + CI disable blocked)
```

**7. `bash scripts/acceptance-hs-cleanroom.sh`** — exit 0
```
PASS: forbidden runtime refs 0
PASS: escaping symlinks 0
CHECKED: 58
```

**8. `bash verify.sh`** — exit 0
```
PASS: no secret-pattern match in any tracked file, .env not tracked
```
(verify.sh 본문을 직접 읽어 비밀 패턴 스캔 전용 스크립트임을 확인 — fail-closed 설계, 자기 면제 없음)

**9. `bash scripts/scan-data-exposure.sh all`** — exit 0
```
PASS: 추적 파일 90개 검사, 위반 0건
PASS: 기록 전량 blob 498개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 90개 중), 개인정보 적재 0건
```

**10. `gh issue view 25 --json number,state,title,url`** — 1·2차 시도 HTTP 503(exit 1), 3차 성공(exit 0)
```
{"number":25,"state":"OPEN","title":"HumanSearch L0 인증 화면 분류 계약을 순수 함수로 고정한다","url":"https://github.com/sangmokang/Valuehire_v6/issues/25"}
```

## 변조 증거

복제본 준비: `git clone --branch task/humansearch-l0-surface-classifier /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/.l0-harness-base /tmp/hs-l0-adv.k9zKYl/clone` → HEAD `84050bf28ff89039c771be70a950a1a4e4da9a4a` 일치 확인. `uv sync --frozen` 후 기준선 `uv run --frozen pytest tests/test_auth_surface.py -q` → **24 passed in 0.82s** (exit 0).

**A. 복수 역할 DRIFTED 가드 제거** — `or len(validated.matched_roles) > 1` 조건 삭제(다중 역할이 sorted 첫 역할로 분류되도록 변조). pytest 결과(exit 1):
```
E       AssertionError: assert <AuthSurfaceState.AUTHENTICATED: 'authenticated'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E       Failing test case: test_classification_properties(
E           roles=frozenset({AUTHENTICATED_SURFACE, HUMAN_AUTH_SURFACE}), contract_valid=True)
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-2-4]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-2-5]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-2-6]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-3-7]
FAILED tests/test_auth_surface.py::test_classification_properties
5 failed, 19 passed in 0.23s
```
→ **검출됨.** `git checkout -- …auth_surface.py` 원복, `git status --short` 출력 없음(CLEAN).

**B. contract_valid=false → UNKNOWN으로 변조** — `not contract_valid` 분기를 `UNKNOWN` 반환으로 교체, 다중 역할 가드는 유지. pytest 결과 `PYTEST_EXIT=1`:
```
E       Failing test case: test_classification_properties(roles=frozenset(), contract_valid=False)
FAILED …[valid-False-roles-0-0] / [valid-False-roles-1-1] / [valid-False-roles-1-2]
FAILED …[valid-False-roles-1-3] / [valid-False-roles-2-4] / [valid-False-roles-2-5]
FAILED …[valid-False-roles-2-6] / [valid-False-roles-3-7]
FAILED tests/test_auth_surface.py::test_classification_properties
9 failed, 15 passed in 0.22s
```
→ **검출됨** (contract_valid=False 8조합 전부 + 속성 시험). 원복 후 CLEAN 확인.

**C. observation 타입 검사 제거** — `_validated` 본문을 `return observation`으로 교체(런타임 검증 전부 삭제). pytest 결과 `PYTEST_EXIT=1`:
```
E       Failed: DID NOT RAISE InvalidObservation
FAILED tests/test_auth_surface.py::test_rejects_invalid_observations[observation0]
FAILED tests/test_auth_surface.py::test_rejects_invalid_observations[observation1]
FAILED tests/test_auth_surface.py::test_rejects_invalid_observations[observation2]
FAILED tests/test_auth_surface.py::test_rejects_invalid_observations[observation3]
FAILED tests/test_auth_surface.py::test_rejects_invalid_observations[observation4]
5 failed, 19 passed in 0.43s
```
→ **검출됨** (잘못된 입력 5종 전부). 원복 후 CLEAN 확인.

종료 처리: 복제본 최종 `git status --short` 출력 없음 → `/tmp/hs-l0-adv.k9zKYl` 삭제. 대상 작업트리 최종 확인: `## task/humansearch-l0-surface-classifier...origin/main [ahead 5]`, HEAD `84050bf…`, 변경 파일 0 — **대상 무접촉 유지**.

## 불일치/한계

- **goal 문서의 "RED 0/19" vs 현재 세션 훅 "RED 0/20"**: 게이트 수가 19→20으로 늘었습니다. 문서 숫자는 작성 시점 기준이며, 이번 판정은 문서 숫자가 아니라 현재 HEAD에서 위 명령을 직접 재실행한 결과에만 근거했습니다.
- **GREEN 이후 테스트 변경(84050bf)**: goal 불변식의 문자적 해석("GREEN에서 시험 파일 변경 금지")과 어긋나 보이나, 커밋 자체가 GREEN이 아닌 별도 FIX 단계로 표시됐고 diff는 import 재배치뿐임을 전문 확인했습니다. 검사 약화 아님으로 판정합니다.
- **출력 절단**: 변조 A/B/C의 pytest 출력은 `tail`로 마지막 12~20줄만 캡처했습니다(실패 요약과 종료코드는 온전히 보존). uv.lock diff는 검증 명령이 아닌 참고 확인이라 100줄로 절단했습니다.
- **미확인 항목**: PR 생성/CI/merge는 이번 범위가 아니고 실행하지 않았습니다. Codex 2차 재현(goal 구현 순서 5단계 후반)은 이 보고 이후의 몫입니다. gh 503이 간헐 발생하므로 Codex 재현 시 이슈 조회 재시도가 필요할 수 있습니다.

## 최종 판단

**PASS.** 근거: (1) AC의 세 축 — 16조합 결정적 분류(전수 파라미터화 + Hypothesis 통과), 잘못된 입력 거부(5종 전부 `InvalidObservation`), 결정성(같은 입력 반복 호출 동일 결과 단언) — 이 현재 HEAD에서 전부 재현 통과했습니다. (2) 판단 계약 1~4(순수 함수, 3역할, DRIFTED/UNKNOWN 규칙, 외부 의존 금지)는 코드 전문 검토로 확인했고, 계약 5의 게이트·비밀·노출·변조·위조방지 검사가 모두 exit 0입니다. (3) 계약 6의 후속 계층 선점 없음, 계약 7의 최소 변경(diff 8파일, 전부 이번 작업 소유물)도 확인했습니다. (4) 테스트 실효성은 문서 주장 재인용이 아니라 독립 복제본에서의 변조 3종 전멸(5·9·5개 실패)로 직접 증명했습니다.
~~~

### Claude V1 — 증거 결함 보완 명령과 프롬프트

1차 출력은 결론은 냈지만 변조 출력 일부를 절단했고, C에서 요구한 두 줄보다 넓은 검증 전체를
지웠다. Codex가 이를 그대로 합격 처리하지 않고 다음 보완 명령을 실행했다.

명령:

`env -u ANTHROPIC_API_KEY claude -p "<아래 프롬프트 전문>"`

프롬프트 전문:

~~~text
방금 HumanSearch L0 최종 HEAD 84050bf 검증 보고는 VERDICT PASS였지만 증거 형식에 두 결함이 있습니다. 코드 판정을 다시 넓게 분석하지 말고 아래 증거만 읽기 전용으로 즉시 보완하십시오.

대상:
- /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-l0-surface-classifier
- HEAD 84050bf28ff89039c771be70a950a1a4e4da9a4a
- 대상 작업트리 절대 수정 금지. 별도 임시 복제본만 사용.

기존 보고 결함:
1. A/B/C pytest 출력을 tail로 절단해 "전체 출력 생략 없이" 요구를 어겼습니다.
2. C는 "observation exact-type guard 두 줄만 제거"가 요구였는데 _validated 전체를 return observation으로 바꿔 과잉 변조했습니다.

보완 요구:
- 동일 HEAD의 새 임시 복제본에서 humansearch/tests/test_auth_surface.py만 실행해 기준선과 A/B/C를 재현하십시오.
- A: classify_auth_surface의 조건에서 정확히 "or len(validated.matched_roles) > 1"만 제거.
- B: contract_valid=false이면 UNKNOWN, 복수 역할이면 DRIFTED가 되도록 두 분기로 바꿈.
- C: _validated의 첫 exact observation type guard 두 줄만 제거하고 나머지 runtime validation은 그대로 둠.
- 각 경우 정확한 변조 명령 또는 패치 전문, 정확한 pytest 명령, 종료코드, stdout/stderr 전체를 생략·tail·요약 없이 붙이십시오.
- 각 변조 후 파일 원복과 clean을 확인하고, 대상 HEAD/status 불변을 끝에 확인하십시오.
- 임시 복제본을 삭제하십시오.

출력 형식:
SUPPLEMENT VERDICT: PASS 또는 FAIL
기존 보고 교정:
기준선 증거:
A 전체 증거:
B 전체 증거:
C 전체 증거:
대상 무접촉 증거:
최종 판단:

숫자나 결론을 이전 보고에서 복사하지 말고 지금 직접 실행하십시오.
~~~

### Claude V1 — 증거 보완 출력 원문

~~~text
SUPPLEMENT VERDICT: PASS

## 기존 보고 교정

1. **출력 절단 결함 교정**: 이번 보고의 기준선·A·B·C 네 번의 pytest 실행 모두 stdout/stderr 전체를 tail·생략·요약 없이 아래에 그대로 붙였습니다. 각 실행 직후 `echo "PYTEST_EXIT=$?"`로 종료코드를 같은 출력 안에 고정했습니다.
2. **C 과잉 변조 결함 교정**: 이전 보고는 `_validated` 전체를 `return observation`으로 바꿔 4개 guard를 모두 무력화했습니다. 이번에는 요구대로 **첫 exact observation type guard 두 줄**(`if type(observation) is not SurfaceObservation:` / `raise InvalidObservation("observation must be a SurfaceObservation")`)만 제거하고 나머지 3개 runtime validation(contract_valid bool 검사, matched_roles frozenset 검사, 원소 SurfaceRole 검사)은 그대로 두었습니다. 그 결과 실패가 정확히 1건(`test_rejects_invalid_observations[observation0]`, `object()` 입력)으로 좁혀져, 해당 guard를 죽이는 변조를 테스트가 개별적으로 검출함이 이전 보고보다 정밀하게 증명됐습니다.

실행 환경: 대상 작업트리는 읽기 전용으로만 접근했고, `git clone`으로 만든 임시 복제본 `/tmp/hs-l0-supp-84050bf`에서 `git checkout --detach 84050bf28ff89039c771be70a950a1a4e4da9a4a` 후 모든 변조·실행을 수행했습니다. 변조는 `git apply` + heredoc 패치(전문 아래 첨부), 실행 명령은 모두 복제본의 `humansearch/` 디렉터리에서 `uv run pytest tests/test_auth_surface.py`입니다.

참고(정직 보고): B 패치 1차 제출 시 제가 hunk 카운트를 `-65,8 +65,10`으로 잘못 적어 `error: corrupt patch at line 15`(APPLY_EXIT=128)가 났습니다. `git apply`는 원자적이라 파일은 전혀 변경되지 않았고, 카운트를 `-65,7 +65,9`로 교정한 2차 패치가 APPLY_EXIT=0으로 적용됐습니다. 아래 B 증거에는 실제 적용된 2차 패치 전문을 실었습니다.

## 기준선 증거

복제본 생성·checkout:

```
Cloning into '/tmp/hs-l0-supp-84050bf'...
done.
HEAD is now at 84050bf 검사 복제본에서도 같은 가져오기 경계를 사용한다
84050bf28ff89039c771be70a950a1a4e4da9a4a
CLONE_STATUS_EXIT=0
```

(`git status --porcelain` 출력 없음 = clean)

실행 명령: `cd /tmp/hs-l0-supp-84050bf/humansearch && uv run pytest tests/test_auth_surface.py; echo "PYTEST_EXIT=$?"` — 전체 출력:

```
Using CPython 3.14.1 interpreter at: /opt/homebrew/opt/python@3.14/bin/python3.14
Creating virtual environment at: .venv
Installed 14 packages in 32ms
============================= test session starts ==============================
platform darwin -- Python 3.14.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /private/tmp/hs-l0-supp-84050bf/humansearch
configfile: pyproject.toml
plugins: hypothesis-6.165.10
collected 24 items

tests/test_auth_surface.py ........................                      [100%]

============================== 24 passed in 0.73s ==============================
PYTEST_EXIT=0
```

## A 전체 증거

적용 패치 전문(`git apply` 입력, APPLY_EXIT=0) — 조건에서 정확히 `or len(validated.matched_roles) > 1`만 제거:

```diff
diff --git a/humansearch/src/humansearch/auth_surface.py b/humansearch/src/humansearch/auth_surface.py
--- a/humansearch/src/humansearch/auth_surface.py
+++ b/humansearch/src/humansearch/auth_surface.py
@@ -65,7 +65,7 @@ def classify_auth_surface(observation: SurfaceObservation) -> AuthSurfaceState:
     """Classify one observation without consulting external state."""

     validated = _validated(observation)
-    if not validated.contract_valid or len(validated.matched_roles) > 1:
+    if not validated.contract_valid:
         return AuthSurfaceState.DRIFTED
     if not validated.matched_roles:
         return AuthSurfaceState.UNKNOWN
```

적용 후 `git diff`가 위와 동일함을 확인했습니다(도구 로그 원문 참조).

실행 명령: `cd /tmp/hs-l0-supp-84050bf/humansearch && uv run pytest tests/test_auth_surface.py; echo "PYTEST_EXIT=$?"` — 전체 출력:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /private/tmp/hs-l0-supp-84050bf/humansearch
configfile: pyproject.toml
plugins: hypothesis-6.165.10
collected 24 items

tests/test_auth_surface.py ............FFFF.....F..                      [100%]

=================================== FAILURES ===================================
________ test_classifies_all_normal_observations[valid-True-roles-2-4] _________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=True)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.HUMAN_AUTH: 'human_auth'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.HUMAN_AUTH: 'human_auth'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=True))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-True-roles-2-5] _________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=True)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.CHALLENGE: 'challenge'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.CHALLENGE: 'challenge'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=True))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-True-roles-2-6] _________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=True)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.HUMAN_AUTH: 'human_auth'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.HUMAN_AUTH: 'human_auth'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=True))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-True-roles-3-7] _________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=True)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.HUMAN_AUTH: 'human_auth'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.HUMAN_AUTH: 'human_auth'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=True))

tests/test_auth_surface.py:56: AssertionError
________________________ test_classification_properties ________________________

    @given(roles=ROLE_SET_STRATEGY, contract_valid=st.booleans())
>   def test_classification_properties(
                   ^^^
        roles: frozenset[SurfaceRole], *, contract_valid: bool
    ) -> None:

tests/test_auth_surface.py:100:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

roles = frozenset({<SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>, <SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>})
contract_valid = True

    @given(roles=ROLE_SET_STRATEGY, contract_valid=st.booleans())
    def test_classification_properties(
        roles: frozenset[SurfaceRole], *, contract_valid: bool
    ) -> None:
        observation = SurfaceObservation(
            matched_roles=roles,
            contract_valid=contract_valid,
        )

        first = classify_auth_surface(observation)
        second = classify_auth_surface(observation)

        assert isinstance(first, AuthSurfaceState)
        assert first is second
>       assert first is _expected_state(roles, contract_valid=contract_valid)
E       AssertionError: assert <AuthSurfaceState.HUMAN_AUTH: 'human_auth'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.DRIFTED: 'drifted'> = _expected_state(frozenset({<SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>, <SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>}), contract_valid=True)
E       Failing test case: test_classification_properties(
E           roles=frozenset(
E               set(
E                   [<SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>,
E                    <SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>],
E               ),
E           ),
E           contract_valid=True,
E       )

tests/test_auth_surface.py:113: AssertionError
=========================== short test summary info ============================
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-2-4]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-2-5]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-2-6]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-True-roles-3-7]
FAILED tests/test_auth_surface.py::test_classification_properties - Assertion...
========================= 5 failed, 19 passed in 0.28s =========================
PYTEST_EXIT=1
```

원복 확인: `git checkout -- humansearch/src/humansearch/auth_surface.py` 후 `git diff --stat` 출력 없음(변경 0), `git status --porcelain` 출력 없음(clean).

## B 전체 증거

적용 패치 전문(2차, APPLY_EXIT=0) — contract_valid=false → UNKNOWN, 복수 역할 → DRIFTED의 두 분기로 교체:

```diff
diff --git a/humansearch/src/humansearch/auth_surface.py b/humansearch/src/humansearch/auth_surface.py
--- a/humansearch/src/humansearch/auth_surface.py
+++ b/humansearch/src/humansearch/auth_surface.py
@@ -65,7 +65,9 @@ def classify_auth_surface(observation: SurfaceObservation) -> AuthSurfaceState:
     """Classify one observation without consulting external state."""

     validated = _validated(observation)
-    if not validated.contract_valid or len(validated.matched_roles) > 1:
+    if not validated.contract_valid:
+        return AuthSurfaceState.UNKNOWN
+    if len(validated.matched_roles) > 1:
         return AuthSurfaceState.DRIFTED
     if not validated.matched_roles:
         return AuthSurfaceState.UNKNOWN
```

실행 명령: `cd /tmp/hs-l0-supp-84050bf/humansearch && uv run pytest tests/test_auth_surface.py; echo "PYTEST_EXIT=$?"` — 전체 출력:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /private/tmp/hs-l0-supp-84050bf/humansearch
configfile: pyproject.toml
plugins: hypothesis-6.165.10
collected 24 items

tests/test_auth_surface.py FFFFFFFF.............F..                      [100%]

=================================== FAILURES ===================================
________ test_classifies_all_normal_observations[valid-False-roles-0-0] ________

observation = SurfaceObservation(matched_roles=frozenset(), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset(), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-False-roles-1-1] ________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-False-roles-1-2] ________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>}), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>}), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-False-roles-1-3] ________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-False-roles-2-4] ________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>}), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-False-roles-2-5] ________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-False-roles-2-6] ________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________ test_classifies_all_normal_observations[valid-False-roles-3-7] ________

observation = SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False)
expected = <AuthSurfaceState.DRIFTED: 'drifted'>

    @pytest.mark.parametrize(("observation", "expected"), NORMAL_CASES)
    def test_classifies_all_normal_observations(
        observation: SurfaceObservation, expected: AuthSurfaceState
    ) -> None:
>       assert classify_auth_surface(observation) is expected
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.UNKNOWN: 'unknown'> = classify_auth_surface(SurfaceObservation(matched_roles=frozenset({<SurfaceRole.HUMAN_AUTH_SURFACE: 'human_auth_surface'>, <SurfaceRole.AUTHENTICATED_SURFACE: 'authenticated_surface'>, <SurfaceRole.CHALLENGE_SURFACE: 'challenge_surface'>}), contract_valid=False))

tests/test_auth_surface.py:56: AssertionError
________________________ test_classification_properties ________________________

    @given(roles=ROLE_SET_STRATEGY, contract_valid=st.booleans())
>   def test_classification_properties(
                   ^^^
        roles: frozenset[SurfaceRole], *, contract_valid: bool
    ) -> None:

tests/test_auth_surface.py:100:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

roles = frozenset(), contract_valid = False

    @given(roles=ROLE_SET_STRATEGY, contract_valid=st.booleans())
    def test_classification_properties(
        roles: frozenset[SurfaceRole], *, contract_valid: bool
    ) -> None:
        observation = SurfaceObservation(
            matched_roles=roles,
            contract_valid=contract_valid,
        )

        first = classify_auth_surface(observation)
        second = classify_auth_surface(observation)

        assert isinstance(first, AuthSurfaceState)
        assert first is second
>       assert first is _expected_state(roles, contract_valid=contract_valid)
E       AssertionError: assert <AuthSurfaceState.UNKNOWN: 'unknown'> is <AuthSurfaceState.DRIFTED: 'drifted'>
E        +  where <AuthSurfaceState.DRIFTED: 'drifted'> = _expected_state(frozenset(), contract_valid=False)
E       Failing test case: test_classification_properties(
E           roles=frozenset(),
E           contract_valid=False,
E       )
E       Explanation:
E           These lines were always and only run by failing test cases:
E               /private/tmp/hs-l0-supp-84050bf/humansearch/src/humansearch/auth_surface.py:69

tests/test_auth_surface.py:113: AssertionError
=========================== short test summary info ============================
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-0-0]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-1-1]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-1-2]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-1-3]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-2-4]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-2-5]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-2-6]
FAILED tests/test_auth_surface.py::test_classifies_all_normal_observations[valid-False-roles-3-7]
FAILED tests/test_auth_surface.py::test_classification_properties - Assertion...
========================= 9 failed, 15 passed in 0.25s =========================
PYTEST_EXIT=1
```

원복 확인: `git checkout -- ...` 후 `git diff --stat` 출력 없음(변경 0).

## C 전체 증거

적용 패치 전문(APPLY_EXIT=0) — `_validated`의 첫 exact observation type guard 두 줄만 제거, 나머지 3개 runtime validation 유지:

```diff
diff --git a/humansearch/src/humansearch/auth_surface.py b/humansearch/src/humansearch/auth_surface.py
--- a/humansearch/src/humansearch/auth_surface.py
+++ b/humansearch/src/humansearch/auth_surface.py
@@ -50,8 +50,6 @@ _SINGLE_ROLE_STATES = {


 def _validated(observation: object) -> SurfaceObservation:
-    if type(observation) is not SurfaceObservation:
-        raise InvalidObservation("observation must be a SurfaceObservation")
     if type(observation.contract_valid) is not bool:
         raise InvalidObservation("contract_valid must be a bool")
     if type(observation.matched_roles) is not frozenset:
```

실행 명령: `cd /tmp/hs-l0-supp-84050bf/humansearch && uv run pytest tests/test_auth_surface.py; echo "PYTEST_EXIT=$?"` — 전체 출력:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /private/tmp/hs-l0-supp-84050bf/humansearch
configfile: pyproject.toml
plugins: hypothesis-6.165.10
collected 24 items

tests/test_auth_surface.py ................F.......                      [100%]

=================================== FAILURES ===================================
_______________ test_rejects_invalid_observations[observation0] ________________

observation = <object object at 0x104d2d940>

    @pytest.mark.parametrize("observation", INVALID_OBSERVATIONS)
    def test_rejects_invalid_observations(observation: Any) -> None:
        with pytest.raises(InvalidObservation):
>           classify_auth_surface(observation)

tests/test_auth_surface.py:87:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
src/humansearch/auth_surface.py:65: in classify_auth_surface
    validated = _validated(observation)
                ^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

observation = <object object at 0x104d2d940>

    def _validated(observation: object) -> SurfaceObservation:
>       if type(observation.contract_valid) is not bool:
                ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'object' object has no attribute 'contract_valid'

src/humansearch/auth_surface.py:53: AttributeError
=========================== short test summary info ============================
FAILED tests/test_auth_surface.py::test_rejects_invalid_observations[observation0]
========================= 1 failed, 23 passed in 0.20s =========================
PYTEST_EXIT=1
```

원복 확인: `git checkout -- ...` 후 `git diff --stat` 출력 없음(변경 0), `git status --porcelain` 출력 없음(exit 0, clean), 복제본 HEAD `84050bf28ff89039c771be70a950a1a4e4da9a4a` 유지.

## 대상 무접촉 증거

모든 작업 종료 후 대상 작업트리에서 직접 실행한 결과:

```
84050bf28ff89039c771be70a950a1a4e4da9a4a
TARGET_STATUS_EXIT=0
```

(`git status --porcelain` 출력 없음 = 추적/미추적 변경 0. 대상에는 시작 시점 확인과 파일 Read 외 어떤 쓰기 명령도 실행하지 않았습니다.)

임시 복제본 삭제 확인:

```
"/tmp/hs-l0-supp-84050bf": No such file or directory (os error 2)
LS_EXIT=2 (0이 아니면 삭제 완료)
```

## 최종 판단

동일 HEAD 84050bf의 새 임시 복제본에서 직접 실행한 결과, 기준선은 24 passed(exit 0)이고 세 변조는 각각 정확한 실패 패턴으로 검출됐습니다 — A(복수 역할 DRIFTED 조건 제거): 5 failed, 정확히 contract_valid=True·역할 2개 이상 4개 케이스 + hypothesis 속성 테스트. B(contract 위반을 UNKNOWN으로 강등): 9 failed, 정확히 contract_valid=False 8개 케이스 전부 + hypothesis 속성 테스트. C(첫 exact type guard 두 줄만 제거): 1 failed, 정확히 `object()` 입력이 `InvalidObservation` 대신 `AttributeError`로 새는 케이스. 세 변조 모두 테스트가 요구 지점에서 최소 범위로 잡아내므로, 기존 VERDICT PASS는 유지되며 두 증거 형식 결함(출력 절단, C 과잉 변조)은 위 전체 증거로 교정 완료입니다. 대상 작업트리는 HEAD·status 모두 불변이고 임시 복제본은 삭제했습니다.
~~~

### Codex V2 — 독립 재공격

Codex는 Claude의 문장을 복사해 판정하지 않고 최종 제품 지문에서 같은 주장과 반례를 다시
실행했다. 변조는 대상 파일에 `apply_patch`로 한 번에 하나씩 넣고, 각 시험 직후 같은
`apply_patch`로 원복했다. 세 회차 뒤 `git diff --check`와 `git status --porcelain=v1`로 제품
파일 변경 0을 확인했다.

| Claude V1 주장 | Codex V2 재현 명령/검사 | Codex 결과 | 차이 판정 |
| --- | --- | --- | --- |
| 정상·오류·속성·공개 경로 시험 통과 | `bash scripts/acceptance-hs-gates.sh` | ruff 4/4, mypy 4/4, pytest 25/25, 공개 패키지 런타임 경로 통과 | 없음 |
| 게이트 변조 차단 | `bash scripts/acceptance-hs-gates-mutations.sh` | 6/6 차단 | 없음 |
| 증거 위조·CI 비활성화 차단 | `bash scripts/acceptance-hs-gates-antiforge.sh` | 3/3 차단 | 없음 |
| 클린룸 경계 | `bash scripts/acceptance-hs-cleanroom.sh` | 금지 참조 0, 이탈 심볼릭 링크 0, 58개 검사 | 없음 |
| 비밀 없음 | `bash verify.sh` | 추적 파일 비밀 패턴 0, `.env` 미추적 | 없음 |
| 데이터 노출 없음 | `bash scripts/scan-data-exposure.sh all` | 추적 90개 위반 0, 이력 blob 498개 위반 0, 표/SQL·개인정보 0 | 없음 |
| 이슈 #25 열림 | `gh issue view 25 --json number,state,title,url` | OPEN, 제목·주소 일치 | Claude의 일시적 HTTP 503은 재시도로 해소 |
| A: 복수 역할 가드 제거를 시험이 잡음 | 해당 조건만 제거 후 `uv run --no-sync pytest -q` | exit 1, 5 failed / 20 passed | Claude는 대상 파일만 돌려 5/19, Codex는 전체 25개를 돌려 통과 수가 1개 많음. 결함 수 일치 |
| B: 무효 계약을 UNKNOWN으로 바꾸면 잡음 | 두 분기로 교체 후 같은 전체 시험 | exit 1, 9 failed / 16 passed | Claude 9/15와 결함 수 일치; 전체 경계 시험 1개 차이 |
| C: 첫 입력 타입 가드 두 줄만 제거하면 잡음 | 정확히 두 줄 제거 후 같은 전체 시험 | exit 1, 1 failed / 24 passed | Claude 보완 1/23과 결함 수 일치; 전체 경계 시험 1개 차이 |
| 대상 작업트리 무접촉 | 세 변조 원복 뒤 `git diff --check && git status --porcelain=v1` | 출력 없음, exit 0 | 없음 |

#### V2 추가 공격

- `humansearch/src/humansearch/auth_surface.py` 전문과 import 목록을 다시 읽었다. 제품 모듈은
  `dataclasses`, `enum`만 사용하며 포털명·주소·DOM·네트워크·파일·환경·시간·난수 문자열은
  0건이다.
- 공개 열거값을 별도 런타임 프로세스에서 읽어 상태 5개, 역할 3개가 정확함을 확인했다.
- GREEN 이후 시험 변경을 `git show 84050bf -- humansearch/tests/test_auth_surface.py`로 재공격했다.
  기대값·단언·수집 수 변경은 0이고 import 경계만 제품 공개 경로로 강화됐다.
- 일반 게이트 변조 스크립트는 게이트 자체의 실패 감지를 검증하며 L0 의미 분기를 자동 변조하지는
  않는다. 그러나 이번 계약은 자동 변조 도구를 인수 기준으로 요구하지 않고, Claude 임시 복제본과
  Codex 대상 원복 시험에서 L0 의미 변조 A/B/C를 각각 독립 검출했다. 새 도구 추가는 범위 확대라
  기각했다.

#### V1/V2 불일치 수

- 제품 코드 결함: 0
- 테스트 미검출 결함: 0
- Claude 최초 증거 형식 결함: 2
  1. 변조 출력 일부 절단
  2. C 변조 범위 과잉
- 위 두 건은 Claude 보완 원문과 Codex 독립 재현으로 교정: 2/2
- 보완 뒤 남은 판정 불일치: 0

### 로컬 최종 판정

단일 인수 기준은 충족됐다. 이 판정은 실제 사람인 로그인이나 후보 검색의 성공을 뜻하지 않는다.
L0가 책임지는 것은 이미 정규화된 한 화면 관측을 다섯 결과로 안전하게 분류하는 데까지다. 다음
기능은 이 계약을 소비하는 실제 화면 어댑터를 별도 goal과 별도 검토 요청으로 시작해야 한다.
