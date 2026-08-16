# HumanSearch L0 인증 화면 분류 계약 (SOT)

최종 갱신: 2026-08-16

근거: `docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md`의 Phase L0와 로그인
전체 흐름을 계층별로 분리한다. 일반 개발·검증·Git 규칙은 `docs/sot/`의 다른 SOT가 우선하고,
HumanSearch L0 상태 의미는 이 문서가 정본이다.

## 1층 — 결론

첫 기능은 현재 화면이 로그인 전인지, 로그인됐는지, 사람 확인이 필요한지, 알 수 없는지, 화면 구조가
바뀌었는지만 답한다. 로그인 뒤 실행 순서와 중단 절차는 이 기능에 넣지 않는다.

## 2층 — 판단 근거

L0는 시간에 따른 전체 run 상태기계가 아니다. 현재 화면에서 인증 관련 의미 role을 관측한 결과를
분류하는 **순수 함수**다.

이 분리는 다음 모순을 없앤다.

- Phase L0는 다섯 상태만 요구한다.
- 전체 로그인 흐름은 후속 단계의 `RECHECK`, `RUNNING`, `STOP`, `AUTH_CONFLICT`도 표현한다.
- 두 집합을 한 enum에 넣으면 L0가 후속 단계의 책임을 선점하고 `AUTHENTICATED`를 전체 run의
  terminal로 오해하게 된다.

따라서 L0는 아래 세 input role, 하나의 관측 유효성, 다섯 output state만 소유한다.

## 3층 — 정본 계약

### 1. 입력 계약

관측값 `SurfaceObservation`은 두 필드로 고정한다.

- `matched_roles`: `frozenset[SurfaceRole]`
- `contract_valid`: `bool`

`SurfaceRole`은 정확히 세 값이다.

- `AUTHENTICATED_SURFACE = "authenticated_surface"`
- `HUMAN_AUTH_SURFACE = "human_auth_surface"`
- `CHALLENGE_SURFACE = "challenge_surface"`

이 이름은 클린룸 계획의 의미 role schema에서 직접 가져왔다. CSS, XPath, URL, 포털명, accessible
name, 화면 문구는 L0 입력이 아니다.

`contract_valid`는 상위 계약 판정기가 구조 마커를 계약대로 평가할 수 있었는지를 뜻한다.
`False`이면 role 집합과 관계없이 구조가 바뀐 것으로 분류한다. 이것은 `structure_drift`라는 가짜
화면 role을 추가하지 않고도 drift를 표현한다.

런타임 입력이 `SurfaceObservation`이 아니거나, `contract_valid`가 실제 bool이 아니거나,
`matched_roles` 안에 `SurfaceRole`이 아닌 값이 있으면 `InvalidObservation`을 발생시킨다. 문자열 값이
우연히 enum 값과 같아도 enum 인스턴스가 아니면 거부한다. 프로그래머 입력 오류를 화면 상태로
위장하지 않는다.

### 2. 출력 계약

`AuthSurfaceState`는 정확히 다섯 값이다.

- `UNKNOWN`: 계약은 유효하지만 인증 role을 하나도 관측하지 못했다.
- `HUMAN_AUTH`: 사람의 로그인이 필요한 화면을 유일하게 관측했다.
- `AUTHENTICATED`: 인증된 화면을 유일하게 관측했다.
- `CHALLENGE`: 캡차·2FA 등 사람 확인 화면을 유일하게 관측했다.
- `DRIFTED`: 계약 판정 자체가 유효하지 않거나 상호 배타적인 role을 둘 이상 동시에 관측했다.

`AUTHENTICATED`는 L0의 분류 결과일 뿐 전체 run의 terminal이 아니다. 후속 runner가 fresh proof와
lease 조건을 확인한 뒤 `RUNNING` 여부를 정한다.

`DRIFTED`는 input role이 아니다. 관측의 계약 불일치에서 계산되는 output이다.

### 3. 완전 결정표

| `contract_valid` | `matched_roles` | 결과 |
|---|---|---|
| `False` | 8개 부분집합 전부 | `DRIFTED` |
| `True` | `{}` | `UNKNOWN` |
| `True` | `{AUTHENTICATED_SURFACE}` | `AUTHENTICATED` |
| `True` | `{HUMAN_AUTH_SURFACE}` | `HUMAN_AUTH` |
| `True` | `{CHALLENGE_SURFACE}` | `CHALLENGE` |
| `True` | 크기 2 또는 3인 부분집합 전부 | `DRIFTED` |

→ 세 role의 부분집합 8개와 유효성 2개를 곱한 16개 정상 입력이 모두 정의됐다. 위험 role에 임의
우선순위를 두지 않으므로 모순 관측이 인증 성공으로 축소되지 않는다.

### 4. 공개 API 계약

구현 모듈은 `humansearch/src/humansearch/auth_surface.py`다. 공개 이름은 다음으로 제한한다.

- `AuthSurfaceState`
- `SurfaceRole`
- `SurfaceObservation`
- `InvalidObservation`
- `classify_auth_surface(observation: SurfaceObservation) -> AuthSurfaceState`

`transition(current, signal)`, `decide_role`, `is_terminal`은 L0 API가 아니다. 시간 전이, 재확인,
park/release, retry, stop, run 진입은 L2/L3/runner의 별도 계약과 PR이 소유한다.

분류 함수는 네트워크, 파일, 환경변수, 시계, 난수, DOM, 브라우저에 접근하지 않는다. 같은 값의 입력은
항상 같은 enum 결과를 반환한다.

### 5. 실행 가능한 인수 기준

**AC-L0-1 — 정상 입력 전수.** 16개 정상 입력을 모두 매개변수화해 결정표와 같은 결과를 단언한다.

**AC-L0-2 — 잘못된 입력 거부.** 지원하지 않는 role 문자열, bool이 아닌 유효성, 잘못된 관측 객체는
전부 `InvalidObservation`을 발생시킨다.

**AC-L0-3 — 속성 검증.** Hypothesis가 세 role 부분집합과 bool을 생성해 다음을 증명한다.

- 함수가 항상 다섯 상태 중 하나를 반환한다.
- 유효하지 않은 계약은 항상 `DRIFTED`다.
- 유효한 빈 관측은 항상 `UNKNOWN`이며 `AUTHENTICATED`가 아니다.
- 유효한 다중 role은 항상 `DRIFTED`다.
- 같은 관측은 반복 호출해 같은 결과를 반환한다.

**AC-L0-4 — 경계.** 모듈과 테스트는 런타임 import를 사용하며 제품 코드에 portal명, URL, CSS,
XPath, DOM API, 화면 문구가 없다. 기존 G3 acceptance가 새 파일을 실제로 검사해야 한다.

**AC-L0-5 — mutation.** 정상 인증 단일 role의 기대 결과를 임시로 `UNKNOWN`으로 바꾸면 targeted
test가 실패해야 하고, 원복 뒤 같은 명령이 통과하고 작업트리가 clean이어야 한다.

### 6. RED/GREEN 불변식

- RED 커밋은 테스트, Hypothesis dependency, lockfile만 바꾼다.
- RED는 `auth_surface` 기능 부재 또는 명시적인 미구현 때문에 실패해야 한다. 문법, 잘못된 cwd,
  dependency 설치 실패, collection 0건은 유효한 RED가 아니다.
- GREEN 커밋은 제품 모듈과 공개 export만 바꾼다.
- GREEN은 RED의 기대값, skip, xfail, test selection을 바꾸지 않는다.
- 추가 결함을 발견하면 새 RED 단독 커밋을 먼저 만들고 그 뒤 별도 GREEN 커밋으로 고친다.

### 7. 후속 계층 소유권

- L2: `HUMAN_AUTH` 뒤 사람 로그인 완료를 fresh observation으로 재확인하는 절차와 `RECHECK` 의미.
- L3: challenge와 session conflict의 terminal 행동, 자동 제출·재시도 0회.
- runner: `AUTHENTICATED` 뒤 lease와 proof를 확인하고 `RUNNING`에 들어갈지 결정.
- portal contract: 실제 DOM/ARIA를 세 의미 role과 `contract_valid`로 바꾸는 판정.

L0 PR은 위 동작을 구현하거나 enum에 추가하지 않는다.

### 8. 비범위

- 실제 채용 포털, 브라우저, 로그인, 세션, 자격증명, 캡처, 후보자 개인정보
- selector·locator·portal contract 생성
- park/release/retry/stop/run 전이
- C1 및 그 이후 라이브 검증
- merge와 배포

### 9. 충돌 해소 규칙

날짜가 있는 `docs/engineering/` 계획·프롬프트가 이 문서와 다르면 L0 구현에서는 이 문서를 따른다.
이 계약을 바꾸려면 같은 PR에서 이 파일, 인수 테스트, 해당 구현 prompt를 함께 바꾸고 검사 약화 여부를
명시한다. 실행 중 충돌을 발견한 agent는 임의로 중간안을 만들지 않고 제품 변경 없이 중단한다.
