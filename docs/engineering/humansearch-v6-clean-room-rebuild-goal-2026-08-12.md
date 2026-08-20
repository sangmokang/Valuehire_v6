# HumanSearch v6 클린룸 재구축 goal — v5 구현과 브라우저 구조를 함께 끊는다

- 작성일: 2026-08-12
- 작업 지시: `$strict 어 새로 클린룸 재구축 안을 잡아봐`
- 이번 산출물 위험 등급: L2(계획 문서만 작성, 제품 코드·포털 조작 0)
- 후속 구현 위험 등급: L3(인증 세션·후보자 PII·외부 채용 포털 조작)
- 상태: **계획안**. 구현·라이브 검증·PR·병합은 아직 하지 않았다.
- 상위 준수 SOT: `docs/sot/coding-principles.md`, `docs/sot/verification-commands.md`,
  `docs/sot/hook-contracts.md`, `docs/sot/git-workflow.md`

---

## 0. 결정

HumanSearch v6는 v5의 `cdp_driver.py`를 복사·분해·import·실행하지 않는다. 더 나아가 v5가 택한
**CDP 포트 기반 범용 브라우저 드라이버 구조도 계승하지 않는다.**

새 구조는 다음 세 문장으로 고정한다.

1. **브라우저 소유권은 포트가 아니라 사용자가 선택한 현재 탭의 lease다.**
2. **포털 지식은 코드가 아니라, 새로 캡처한 현재 실화면에서 생성한 계약 데이터다.**
3. **HumanSearch는 검색을 만들지 않는다. 로그인된 검색 결과를 열람·증거화·판정하는 좁은 수직 기능이다.**

따라서 v5에서 가져오는 것은 구현이 아니라 아래 네 가지 사업 불변식뿐이다.

- 발송 버튼은 자동화하지 않는다.
- 사람이 개입하면 즉시 양보하고 이후 재개한다.
- 캡차·2FA·세션 충돌은 fail-closed다.
- 증거 없는 후보는 채점·등록하지 않는다.

`docs/engineering/humansearch-v6-founding-spec-2026-08-07.md`는 당시 사고와 요구를 보존한 불변
사건 기록으로 남긴다. 이 문서는 그 기록의 §4 구현 이식 결론을 **2026-08-12의 새 오너 지시로
대체하는 후속 계획**이다. `docs/engineering/` 문서는 SOT가 아니므로 실제 구현 규칙은 위 4개 SOT가
우선한다(`docs/sot/INDEX.md:1-8`).

---

## 1. 현재 상태 — 직접 확인한 사실

| ID | 사실 | fresh evidence |
|---|---|---|
| C-1 | v6는 부트스트랩 단계이며 제품 소스가 없다. | `README.md:5-7`; `rg --files`에서 humansearch/aisearch/CDP 구현 0건 |
| C-2 | Gate 0은 현재 통과한다. | `bash scripts/session-status.sh` → `HEAD: 32ce698 (synced)`, `ORIGIN: 32ce698`, `RED: 0/4` |
| C-3 | 현 저장소의 검증은 make/npm이 아니라 bash 스크립트다. | `docs/sot/verification-commands.md:8-24` |
| C-4 | 기존 2026-08-08 계획은 외부 코드 참조 0을 선언했지만 `target_id`, CDP 포트 탐지, raw driver를 유지한다. | `git show origin/task/humansearch-plan:docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md`의 `target_id`/CDP 항목 |
| C-5 | 창립 스펙은 2,305줄 v5 브랜치 코드를 v6 근간으로 삼으라고 적었다. | `humansearch-v6-founding-spec-2026-08-07.md:311-315,389-394` |
| C-6 | 그 로컬 파일은 현재도 `cce9280`에 2,305줄로 존재한다. | `wc -l /Users/kangsangmo/Desktop/Valuehire_v5-aisearch-live-portal-wire/apps/aisearch/core/cdp_driver.py` → `2305`; `git rev-parse --short HEAD` → `cce9280` |
| C-7 | 이 컴퓨터의 Chrome은 151이다. | `Google Chrome --version` → `151.0.7922.76` |
| C-8 | Python 3.14.1, uv 0.11.3, stdlib SQLite 3.51.1이 실행된다. | 각 버전 명령 직접 실행 |
| C-9 | activeTab은 같은 origin 경로 이동에서 유지되고 다른 origin/탭 종료에서 회수된다. | Chrome 공식 activeTab 문서 lines 45-46; Chrome 151 실측은 B1 전까지 NOT_RUN |

### 현재 브라우저 전제가 이미 바뀌었다

Chrome은 136부터 기본 사용자 데이터 디렉터리에 대한 `--remote-debugging-port`와
`--remote-debugging-pipe`를 무시하고, 비표준 `--user-data-dir`을 요구한다. 따라서 창립 스펙의
"평소 쓰는 실제 기본 프로필에 CDP 포트를 붙인다"는 전제는 현재 Chrome에서 그대로 채택할 수 없다.

- 공식 근거: <https://developer.chrome.com/blog/remote-debugging-port>
- Chrome 144+는 사용자가 `chrome://inspect/#remote-debugging`에서 허용하는 auto-connect도 제공하지만,
  연결 주체가 프로필의 모든 열린 탭·쿠키·저장소에 접근할 수 있다고 공식 문서가 경고한다.
  <https://developer.chrome.com/docs/devtools/agents/use-cases/auto-connect>

이 변화는 단순 구현 차이가 아니라 **신뢰 경계 변경**이다. v6는 프로필 전체가 아니라 사용자가 선택한
탭 하나만 권한 대상으로 삼는다.

Chrome의 `activeTab`은 사용자의 명시적 동작 뒤 현재 탭에만 임시 host 권한을 부여하고, 같은 origin에서만
유지되며 다른 origin으로 이동하거나 탭을 닫으면 회수된다. 반대로 `debugger` permission은 optional로
둘 수 없고 설치 경고가 “모든 웹사이트의 데이터 읽기·변경” 범위다. 따라서 기본 extension manifest에는
`debugger`를 넣지 않는다.

- 공식 근거: <https://developer.chrome.com/docs/extensions/develop/concepts/activeTab>
- 권한 경고/optional 제한: <https://developer.chrome.com/docs/extensions/reference/api/permissions>,
  <https://developer.chrome.com/docs/extensions/reference/permissions-list>

---

## 2. 근본 원인

### R-1. “검증된 코드 재사용”이 구현 경계까지 재사용하는 구실이 됐다

2,305줄 파일은 하나의 설계가 아니라 로그인·렌더·입력·필터·스크롤·사이트별 셀렉터·체크포인트가
사고 때마다 쌓인 결과다. 이를 모듈로 나눠도 책임과 결합 방향은 그대로 남는다. **줄 수를 나누는 것은
클린룸이 아니다.**

### R-2. HumanSearch의 범위와 aisearch 드라이버의 범위가 섞였다

창립 스펙은 검색어·필터 생성/입력을 scope out으로 둔다(`humansearch-v6-founding-spec-2026-08-07.md:
78-80`). 그러나 §4는 키워드 입력, 필터 초기화, typeahead 조작까지 이식한다(`:317-356`). 이 모순이
범용 드라이버를 크게 만든다.

새 경계에서는 HumanSearch가 받는 것은 “이미 사람이 검색을 걸어 둔 현재 탭”이다. 검색 생성·필터
입력은 별도 aisearch 제품의 책임이며 HumanSearch 패키지에는 API조차 두지 않는다.

### R-3. “창을 찾는다”는 문제가 사실은 “권한을 넘긴다”는 문제였다

포트 탐지·프로세스 탐지·target 열거는 사용자가 어느 탭을 맡겼는지를 추측하는 방식이다. 추측을 더
정교하게 만드는 대신, 사용자가 확장 버튼을 눌러 **현재 탭 하나를 명시적으로 handoff**하게 한다.

### R-4. 셀렉터를 영구 코드처럼 다뤘다

셀렉터는 제품 로직이 아니라 현재 외부 화면에 대한 관찰값이다. SOT도 이를
`contracts/*/markers.json` 데이터로 두라고 요구한다(`docs/sot/coding-principles.md:39-49`).
새 구현은 old selector를 회수하지 않고, 각 채널의 현재 화면을 다시 캡처해 계약을 만든다.

---

## 3. 클린룸 경계

이 계획의 “클린룸”은 법률상 독립개발 증명이 아니라 **구현 오염을 줄이는 공학적 경계**다. 현재 대화
컨텍스트는 이미 창립 스펙의 일부 과거 셀렉터를 읽었으므로, 이 컨텍스트는 계획과 검증만 맡고 제품
구현을 맡지 않는다.

### 3-1. 구현자가 볼 수 있는 입력

- 4개 v6 SOT
- 이 goal 문서에서 추출한 selector-free 계약 스펙
- Chrome 공식 `activeTab`, Native Messaging, service worker 문서
- 2026-08-12 이후 v6 캡처 도구가 만든 fresh 구조 캡처
- 사업 불변식과 입출력 스키마

### 3-2. 구현자가 보지 않거나 사용하지 않는 입력

- `Valuehire_v1`~`Valuehire_v5`의 모든 제품 소스
- `cce9280` 및 v5 `cdp_driver.py`
- v5 테스트·fixture·selector 표
- v5 모듈명·함수 시그니처·파일 분해 구조
- v5 프로세스 또는 파일을 실행해서 얻은 출력

### 3-3. 기계적으로 강제할 수 있는 부분

후속 첫 인수 스크립트 `scripts/acceptance-hs-cleanroom.sh`는 `docs/engineering/**`를 제외한 추적 파일에
대해 다음을 차단한다.

- `Valuehire_v[1-5]`, `cce9280`, 외부 worktree 절대경로
- 저장소 밖을 가리키는 symlink
- v5 패키지 import 또는 subprocess 호출
- 제품 코드에서 포털 URL·포트·셀렉터 리터럴 사용
- fresh capture provenance가 없는 `live_confirmed` 계약

검사기 자기매칭은 패턴을 `contracts/cleanroom-deny-patterns.txt`에 데이터로 분리해 해결한다. 검사기
파일 자체를 제외하지 않는다(P13④).

### 3-4. 기계적으로 증명할 수 없는 부분

CI는 “아이디어를 기억해서 다시 썼는지”를 증명할 수 없다. 그래서 다음 운영 경계를 추가한다.

1. 구현은 이전 대화 이력이 없는 새 세션에서 시작한다.
2. 구현 세션에는 selector-free 계약만 전달한다.
3. v5 경로를 마운트하지 않은 격리 환경에서 정적 테스트를 수행한다.
4. 구현 후 별도 검증자가 v5와 정규화된 긴 구문 중복을 검사한다. 이 검사는 copy-paste 탐지 보조이며
   독립 구현의 완전한 증명이라고 과장하지 않는다.
5. fresh locator가 우연히 old locator와 같아도 결함으로 보지 않는다. 동일성보다 `captured_at`,
   Chrome 버전, raw capture SHA, 현재 DOM 매칭 건수라는 **획득 경로**를 판정한다.

---

## 4. 목표 아키텍처 — Active Tab Bridge

```text
사용자가 검색 결과 탭에서 확장 버튼 클릭
                │
                ▼
Chrome MV3 Extension
  - 사용자 click으로 activeTab 임시 권한 획득
  - content script로 허용된 의미 동작만 실행
  - 사용자 입력 감지 / 즉시 yield
  - fresh DOM·ARIA role·visible screenshot 캡처
                │ Native Messaging (길이-prefix JSON)
                ▼
HumanSearch Native Host
  - tab handoff 교환 / lease 정본 / command journal
  - portal contract 판정
  - evidence recorder / SQLite
  - hard exclude / scoring / eligible
                │
                ▼
선택적 Registration Adapter
  - Send 기능 없음
```

### 4-1. 브라우저 브리지

사용자는 확장 아이콘을 눌러 현재 탭의 `activeTab` 권한을 넘긴다. 이 권한은 브라우저가 탭과 origin에
묶어 강제한다. extension은 그 탭에 `scripting.executeScript()`로 좁은 bridge를 주입하고 일회용
`tab_handoff_token`을 host에 보낸다. host만 token을 원자적으로 교환해 `tab_lease_id`와 fencing
token을 발급한다. extension은 lease 발급자도 정본도 아니다.

기본 manifest permission은 `activeTab`, `scripting`, `nativeMessaging`, 최소 `storage`뿐이다.
`debugger`, `<all_urls>`, `tabs`, `cookies` permission은 금지하며 `chrome.debugger`와 raw CDP protocol도
제품 코드에 존재할 수 없다. `activeTab`으로 필요한 동작을 실증하지 못하면 permission을 몰래 넓히지
않고 B phase를 중단한다. debugger 기반 별도 extension은 새 L3 ADR과 오너 승인 없이는 대안이 아니다.

#### 브리지 명령 allowlist

초기 allowlist는 다음 의미 명령만 노출한다.

- `OBSERVE_SURFACE`
- `CAPTURE_SCREENSHOT`
- `ACTIVATE_SELECTED_TAB`
- `SCROLL_RESULTS`
- `OPEN_MATCHED_PROFILE`
- `RETURN_TO_RESULTS`
- `RELEASE_HANDOFF`

다음 능력은 문자열 검사가 아니라 manifest와 dispatch table 양쪽에 존재하지 않게 한다.

- 탭·창·브라우저 닫기 또는 생성
- 임의 URL navigation
- 자격증명 입력·submit
- 제안·InMail·메일 Send

`OPEN_MATCHED_PROFILE`과 `RETURN_TO_RESULTS`는 호출자가 selector나 URL을 고르는 API가 아니다. 해당
채널의 fresh contract가 허용한 같은 origin의 DOM 전이만 실행하고 이후 URL·surface를 readback한다.

### 4-2. Native Messaging 경계

확장은 `runtime.connectNative()`로 로컬 host와 연결한다. Native Messaging manifest는 정확한
extension origin만 `allowed_origins`에 둔다. Chrome 공식 계약상 서비스 worker에서 Native Messaging을
사용할 수 있고, 연결 포트는 worker 생존에 관여한다.

- 공식 근거: <https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging>
- 서비스 worker는 언제든 종료될 수 있으므로 메모리 전역을 정본으로 쓰지 않는다. Chrome 공식 문서는
  비활성 worker가 종료될 수 있고 상태를 storage에 보존하라고 요구한다.
  <https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle>
- 명령마다 `run_id`, `lease_id`, 단조 증가 `seq`, `expected_state`, `idempotency_key`를 포함한다.
- Native host manifest의 절대 실행 경로·extension origin·파일 owner/mode·배포 SHA를 install과 매 실행
  시 readback한다. host는 Chrome이 넘긴 extension origin 인자를 검증하고 불일치면 frame 해석 전 종료한다.
- host SQLite가 lease의 유일한 정본이다. extension token은 단 한 번만 교환되고 재사용·다른 tabId·다른
  origin 교환은 실패한다.
- host가 보내는 모든 command에는 lease에 묶인 `bound_tab_id`와 origin이 있다. extension은 매번
  `chrome.tabs.get(bound_tab_id)`와 content-script nonce probe로 탭·origin·activeTab grant를 재검증한다.
  service worker 재시작 뒤 probe가 실패하면 탭을 열거하거나 추측하지 않고 새 사용자 click을 요구한다.
- host가 동일 `idempotency_key`를 재수신하면 외부 동작을 반복하지 않고 기존 결과를 readback한다.
- host 또는 extension 재시작 후에는 무조건 `DISCOVER`로 돌아가 현재 탭·로그인·계약을 다시 관찰한다.

### 4-3. 로그인 — 자동 자격증명 입력을 코어에서 제거

v6 1차 제품은 비밀번호를 저장하거나 입력하지 않는다.

```text
UNKNOWN → AUTHENTICATED → RUNNING
    └──→ HUMAN_AUTH ──사람이 같은 탭에서 로그인──→ RECHECK → AUTHENTICATED
    └──→ CHALLENGE / AUTH_CONFLICT ──→ STOP
```

- 로그인 여부는 fresh portal contract의 구조 마커로만 판정한다.
- 미로그인이면 선택된 탭을 활성화하고 사람에게 한 번 알린 뒤 run을 `HUMAN_AUTH`로 park하고 active
  lease를 해제한다. 강제 로그인 timeout은 두지 않으며, 재개는 새 handoff/lease와 fresh auth proof로 한다.
- 로그인 화면에서는 observe/park/release만 가능하다.
- 캡차·2FA·세션 충돌은 자동 클릭·자동 제출·재시도 0회다.
- 자동 로그인은 코어 완성 이후 별도 ADR과 별도 권한 제품으로만 검토한다.

이 결정으로 Keychain·`.env.local`·로그인 폼 selector·submit·자격증명 유출 경로가 1차 코어에서
사라진다. “로그인을 범위 밖에 둔다”가 아니라 **로그인 상태기계는 코어에 두되 자격증명 조작 능력을
제거한다.** 이는 P18의 “위험한 동작은 능력을 없앤다”와 일치한다(`coding-principles.md:33`).

### 4-4. 포털 계약 — fresh capture compiler

코드에는 `saramin`, `jobkorea`, `linkedin` DOM 지식이 없다. 채널별 계약은 다음 의미 역할을 기술한다.

- `authenticated_surface`
- `human_auth_surface`
- `challenge_surface`
- `results_ready`
- `result_card`
- `profile_entry`
- `profile_ready`
- `next_page_or_scroll_boundary`
- `return_to_results_proof`

각 역할은 locator 후보, positive marker, negative marker, 최소/최대 매칭 수, 화면 전이 후 readback
조건을 가진다. locator는 CSS 하나를 정답으로 두지 않고 stable attribute → text 없는 ARIA role → 구조
관계의 순서로 평가한다. accessible name, textContent, placeholder 등 사람이 읽는 문자열은 v1 locator
입력에서 금지한다. 이 범위로 계약을 만족하지 못하면 text를 저장하지 않고 `DRIFTED`로 멈춘다.

#### 캡처와 PII

- raw DOM/ARIA/screenshot은 모두 PII로 취급한다. 암호화된 git 밖 `artifacts/`에 저장하고 0700/0600
  권한을 사용한다.
- 채널별 `retention_days`와 purge job/readback이 구성되지 않으면 raw capture 자체를 차단한다. 만료
  삭제마다 artifact SHA·삭제 시각·결과만 담은 PII 없는 purge receipt를 남긴다.
- 저장소에는 텍스트를 제거한 구조 fixture와 raw SHA만 둔다.
- screenshot 원본은 fixture가 될 수 없다. 필요한 시각 회귀 fixture는 text/image content를 마스킹한
  구조 파생물만 허용한다.
- 후보자 이름·회사·학교·계정명·쿠키·토큰은 fixture에 금지한다.
- `live_confirmed`에는 `captured_at`, Chrome version, extension version, origin, raw SHA,
  fixture path, matched node count가 모두 필요하다.

### 4-5. Host와 데이터

- 권장 host: Python 3.14 + stdlib SQLite. 브라우저 확장은 얇은 MV3 TypeScript로 작성한다.
- Python 런타임 의존은 stdlib를 기본으로 하고, 개발 의존은 SOT가 요구하는 ruff, mypy strict,
  pytest, Hypothesis로 제한한다.
- SQLite는 유일한 저장 정본이며 WAL + 단일 writer lease를 사용한다.
- tab lease·fencing token·handoff 소비 기록도 SQLite가 유일한 정본이다.
- extension은 브라우저 transport만 담당하고 후보자 데이터·채점·등록 정책을 갖지 않는다.
- LLM은 증거 span과 구조화 사실을 추출할 수 있지만 숫자 점수는 기록하지 않는다. D1~D8,
  total, tier, eligible은 버전이 붙은 순수 함수가 계산한다(P14).

---

## 5. 실행 입력·출력 계약

### RunRequest

```jsonc
{
  "channel": "saramin|jobkorea|linkedin_rps",
  "position_ref": "non-empty string",
  "tab_lease_id": "host-issued opaque id after one-time handoff exchange",
  "jd_contract_ref": "versioned local contract id"
}
```

- `target_id`, CDP port, search URL 입력은 없다.
- 현재 URL·origin·tab title은 extension 관찰값으로 receipt에 기록한다.
- 선택 탭 origin이 channel allowlist와 다르면 실행하지 않는다.
- 빈 값·만료 lease·다른 tabId·다른 origin·인증 미확인은 전부 명시 실패다.

### RunResult

```jsonc
{
  "run_id": "uuid",
  "status": "completed|aborted|preflight_failed|human_auth|drifted",
  "abort_reason": "required unless completed",
  "pages_visited": 0,
  "profiles_opened": 0,
  "evidence_saved": 0,
  "scored": 0,
  "eligible": 0,
  "registered": 0,
  "receipt_ref": "runner-owned reference"
}
```

수치는 모델이 쓰지 않고 DB/run journal에서 코드가 계산한다. 0건 완료는 `results_exhausted`와 현재
화면 계약의 readback이 함께 있을 때만 허용한다.

---

## 6. 단계별 구현 계획 — AC 1개 = worktree 1개 = PR 1개

아래 Phase는 마일스톤이고, 실제 작업 단위는 각 AC다. 모든 AC는 RED 테스트 커밋과 GREEN 구현
커밋을 분리하고 24~48시간 안에 끝낸다(`git-workflow.md:14-23`).
아래 명령·출력은 모두 **향후 acceptance 계약이며 현재 NOT_RUN**이다. 이번 계획에서 실제 실행한
저장소 검증은 §13에 별도로 기록한다.

### Phase G — 클린룸·게이트 골격

| AC | 실행 가능한 단언 | 계획 검증 명령과 기대 출력 |
|---|---|---|
| G1 | 비문서 추적 파일에서 v1~v5 경로/import/실행/symlink가 모두 거부된다. | `bash scripts/acceptance-hs-cleanroom.sh` → `PASS: forbidden runtime refs 0`, `PASS: escaping symlinks 0`, `CHECKED >= 2` |
| G2 | HumanSearch 정적·단위 테스트가 CI와 pre-push 양쪽에서 실제 import·실행되고 0건 수집이면 실패한다. | `bash scripts/acceptance-hs-gates.sh` → 명령 동등성 + runtime import spy + collected tests >=1; 테스트 명령 제거 mutation은 exit 1 |
| G3 | 운영 상수·portal locator는 `contracts/` 밖의 제품 코드에 존재할 수 없다. | mutation으로 코드에 가짜 selector/domain을 심으면 양쪽 게이트 exit 1 |

G2가 실제 명령을 만든 뒤에만 `docs/sot/verification-commands.md`를 실행 결과로 갱신한다. 문서를 먼저
고치고 나중에 명령을 맞추지 않는다(`verification-commands.md:27-34`).

### Phase B — 사이트와 무관한 Active Tab Bridge

| AC | 실행 가능한 단언 | 라이브/테스트 증거 |
|---|---|---|
| B1 | click으로 얻은 activeTab 하나에만 bridge가 주입되고 동일 tabId·same-origin 결과↔프로필 왕복·cross-origin revoke를 검증한다. | selected==observed, 왕복 뒤 grant 1, 다른 탭 event 0, cross-origin access 0 |
| B2 | manifest와 runtime에 debugger/all_urls/tabs/cookies/창 생성·닫기/임의 navigation capability가 없다. | manifest·AST·runtime spy + 금지 permission/call 하나씩 심은 mutation 전부 exit 1 |
| B3 | `RELEASE_HANDOFF` 후 원래 탭·창·Chrome 프로세스가 그대로 있고 token 재교환은 실패한다. | before/after tabId readback, closed targets 0, second exchange 0 |
| B4 | service worker와 native host를 각각 강제 재시작해도 같은 idempotency key의 동작이 두 번 실행되지 않는다. | fault-injection: journal intent 1, effect 1, readback 1 |
| B5 | 사용자 입력 이벤트가 오면 mutate capability가 회수되고, idle+fresh auth proof 없이는 복구되지 않는다. | synthetic owner event 뒤 mutation send count 0; resume proof 뒤 1 |

B1이 실패하면 raw CDP 또는 debugger 방식으로 즉시 돌아가지 않는다. 필요한 portal capability와
`activeTab` 한계를 분리해 기록하고 별도 L3 ADR 없이는 permission을 확대하지 않는다.

### Phase L0 — 상태·역할 의미 계약

| AC | 실행 가능한 단언 | 테스트 증거 |
|---|---|---|
| L0 | DOM locator 없이 `UNKNOWN/HUMAN_AUTH/AUTHENTICATED/CHALLENGE/DRIFTED` 전이와 의미 role schema를 먼저 고정한다. | transition table 전수 + illegal transition property test + 빈 locator fixture |

L0가 병합되기 전에는 fresh portal capture를 시작하지 않는다. 이로써 C가 만들 표면 계약과 L1~L3가
소비할 상태 의미가 순환 의존하지 않는다.

### Phase C — fresh capture와 계약 판정기

| AC | 실행 가능한 단언 | 라이브/테스트 증거 |
|---|---|---|
| C1 | 사람인 현재 화면에서 raw capture를 만들고 PII 제거 구조 fixture와 provenance manifest를 생성한다. | raw는 gitignore, fixture 텍스트 값 0, raw SHA 일치, live_confirmed role >= 1 |
| C2 | 같은 판정 함수가 로그인 preflight와 evidence capture 양쪽에서 동일 fixture를 판정한다. | call graph + runtime spy에서 evaluator implementation 1개 |
| C3 | marker 삭제·대소문자 변경·중복 노드 증가 시 `DRIFTED`; 결과 0건은 positive results fixture와 구별된 `results_exhausted` proof가 있어야 한다. | mutation 3종 exit 1 + positive fixture를 exhausted로 분류하는 mutation exit 1 |
| C4 | 잡코리아는 별도 fresh capture PR에서 추가된다. | 현재 fixture 기반 roles 전부 match >= 1 |
| C5 | LinkedIn RPS는 별도 fresh capture PR에서 추가된다. | session conflict/challenge/results 각 surface 판정 |

### Phase L1 — 사람 로그인 live 계약

| AC | 실행 가능한 단언 | 라이브/테스트 증거 |
|---|---|---|
| L1 | 미로그인 화면에서는 activate/read/park/release 외 명령이 0회이며 active lease를 계속 점유하지 않는다. | 사람인 미로그인 live receipt + mutation 0 + open lease 0 |
| L2 | 같은 탭에서 사람이 로그인한 뒤 fresh marker와 idle 조건을 만족해야만 RUNNING으로 간다. | 전이 journal `HUMAN_AUTH→RECHECK→AUTHENTICATED` 1회 |
| L3 | 캡차·2FA·세션 충돌은 terminal이고 자동 제출·재시도가 없다. | 각 fixture mutation + 가능할 때 안전한 live challenge observation; retry 0 |

### Phase V — 사람인 1명 수직 슬라이스

| AC | 실행 가능한 단언 | 라이브/테스트 증거 |
|---|---|---|
| V1 | 선택된 검색 결과 탭에서 후보 1명을 열고 결과 화면으로 복귀했다는 readback을 남긴다. | live run: profiles_opened=1, return proof=PASS |
| V2 | 상세 evidence가 저장되지 않으면 candidates에서 scores로 넘어갈 수 없다. | DB FK/transaction counter-example가 실패 |
| V3 | screenshot·구조 본문·manifest의 SHA를 저장 직후와 소비 직전에 각각 재계산한다. | 파일 1바이트 변조 시 scoring 호출 0 |
| V4 | 중단·드리프트·사람 개입 후 재시작하면 마지막 완결 checkpoint 다음부터 진행한다. | crash injection 뒤 duplicate profile effect 0 |

### Phase S — 판정·게이트

| AC | 실행 가능한 단언 | 테스트 증거 |
|---|---|---|
| S1 | LLM 숫자를 점수 필드에 넣는 경로가 없고 순수 함수가 D1~D8·total·tier를 계산한다. | property test + mutation test; input hash와 fn version readback |
| S2 | hard exclude와 `eligible()`가 유일한 등록 경계다. | 미달·URL 불량 후보의 adapter call 0 |
| S3 | 어댑터 0개로 V1~S2가 완주한다. | completed run, registered=0, evidence/scored >=1 |

### Phase X — 채널 확대와 운영화

| AC | 실행 가능한 단언 | 라이브/운영 증거 |
|---|---|---|
| X1 | 잡코리아 1명 수직 슬라이스가 사람인과 동일 host/runtime을 사용한다. | browser transport implementation count 1; live 1명 |
| X2 | LinkedIn RPS는 동일 선택 탭만 사용하고 동시 lease 2개를 거부한다. | concurrent acquire 2건 중 success 1, live 1명 |
| X3 | `install/doctor/status/reconcile/uninstall`이 extension+native host 경로·origin·owner/mode·SHA를 readback한다. | manifest 경로/파일/권한/SHA 변조 각각 doctor exit 1 + clean machine rollback |
| X4 | 각 채널 20페이지 순회는 1명 수직 슬라이스가 안정화된 뒤 별도 부하·개입 테스트로 승격한다. | pages_visited=20 또는 results_exhausted proof, 중복 profile 0 |

`Send` 기능은 Phase X 이후에도 비범위다. 등록 adapter는 후보 브리핑 저장까지만 담당한다.

---

## 7. Harness 게이트 진행

| Gate | 이번 계획 문서 | 후속 구현 |
|---|---|---|
| 0 | `HEAD==origin/main`, `RED 0/4`, clean 확인 | 각 AC 시작 전 재실행 |
| 0.5 | 창립 스펙·기존 3판 계획·4개 SOT·Chrome 공식 문서 회수 | selector-free 계약만 구현자에게 전달 |
| 1 | 이 goal에 AC와 입출력 계약 작성 | AC 하나를 issue 하나로 분리 |
| 2 | `task/humansearch-clean-room-plan` worktree에서 문서 작성 | AC마다 새 `task/<name>` worktree |
| 3 | 문서 변경만 수행 | RED commit 후 GREEN 최소 구현 |
| 4 | index `verify.sh` PASS; clean clone 0-2 PASS; 0-5/0-6 PASS; 0-7 위반 6/6 차단; Claude REVISE→Codex 계획 APPROVE | unit/integration/fault/live 순서 |
| 5 | 이번 요청에서는 push·PR 안 함 | PR+CI+오너 live 판단 전 완료 금지 |
| 6 | 해당 없음 | merge 후 worktree/branch 정리 |

---

## 8. 검증 전략

### Unit

- state transition table 전수
- command allowlist/denylist
- contract evaluator positive/negative/property tests
- score/hard-exclude/eligible property tests
- Native Messaging frame length·truncated JSON·duplicate seq

### Integration

- extension ↔ native host handshake
- service worker/host restart and replay
- SQLite transaction·WAL·single writer lease
- evidence write → SHA readback → score gate
- same-origin navigation and return proof

### E2E

- 로컬 중립 페이지: activeTab handoff/release/no-close/cross-origin revoke
- 사람인: human login handoff → 후보 1명 → evidence → score
- 잡코리아와 LinkedIn은 각자 별도 PR·별도 live 1명
- 20페이지는 각 채널 1명 수직 슬라이스 후에만 실행

### Observability

- 모든 명령에 run/lease/seq/idempotency key
- 모든 상태 전이에 before/after/reason
- owner intervention, drift, challenge, handoff release를 별도 terminal event로 기록
- 모델 텍스트가 아닌 journal 집계로 counts 생성
- PII 없는 요약 receipt와 git 밖 raw artifact 분리

---

## 9. Pre-mortem

| 실패 | 조기 신호 | 방지·중단 기준 |
|---|---|---|
| activeTab으로 수직 슬라이스 불가 | injection 거부, same-origin 전이 불가, cross-origin 회수 누락 | B1~B3 선행; handoff/release/no-close/revoke 미증명 시 C 금지. debugger/CDP/auto-connect는 자동 fallback이 아니며 새 L3 ADR 필요 |
| 계약이 selector 쓰레기장화 | contract 300줄 초과, role 중복, fallback 증가 | role/matched count/readback 고정; role당 전략 3개 초과 전 surface 재설계 |
| 기억으로 v5 복제 | old 이름·경로·magic number·출처 없는 live_confirmed | fresh context, deny gate, provenance, similarity audit. 의미 독립성을 CI가 완전 증명한다고 주장하지 않음 |
| human auth 병목 | 대기·재인증이 실패 원인 1위 | 기존 user session+알림 1회; 30일 journal 근거가 생길 때만 자동 로그인 ADR |
| PII 유출 | text node·계정명·쿠키·1MB 초과 fixture | allowlist serializer+scanner+retention; PII 카나리 1건 통과 시 live 전면 중단 |

---

## 10. SOT 체크리스트

아래 표시는 `계획 반영/구현 증거` 순서다. 이번 요청은 계획이므로 구현 증거는 전부 NOT_RUN이다.

- [x/NOT_RUN] P1/P2: 모든 원칙을 실행 가능한 AC로 번역했다.
- [x/NOT_RUN] P3/P20: PASS/FAIL/NOT_RUN과 검사 건수 하한을 요구한다.
- [x/NOT_RUN] P5/P16: runtime import, property test, mutation/fault injection을 포함한다.
- [x/NOT_RUN] P6/P7: install/doctor/reconcile/uninstall과 rollback rehearsal을 계획했다.
- [x/NOT_RUN] P8/P9: tab lease, idempotency key, intent/readback을 구조에 넣었다.
- [x/NOT_RUN] P11: 파일 300 soft/600 hard, 함수 60/100, PR 3,000 hard를 그대로 따른다.
- [x/NOT_RUN] P12: 기존 계획을 회수하고 차이를 명시했다.
- [x/NOT_RUN] P13/P15: 검사기 자기면제 금지, local+CI 동등 게이트를 요구한다.
- [x/NOT_RUN] P14: 모든 판정 수치를 순수 함수가 만든다.
- [x/NOT_RUN] P17/P18: activeTab으로 범위를 강제하고 debugger/all_urls/close/create/send/credential을 제거한다.
- [x/NOT_RUN] P19: 외부 포털 PR은 채널별 live 1건 전에는 완료가 아니다.
- [x/NOT_RUN] P21/P22: raw data는 git 밖, locator/상수는 contracts 한 곳이다.
- [x/NOT_RUN] 웹 자동화 5조: fresh contract, 판정기 하나, 브리지 한 벌, 실캡처 fixture, 개입 후 capability 회수.
- [x/NOT_RUN] Git SOT: AC 1개 = branch/worktree/PR 1개, main 직접 수정·자동 병합 없음.
- [x/NOT_RUN] Hook SOT: 신규 acceptance는 pre-push와 CI 모두 실행하며 0건이면 fail-closed다.

---

## 11. 비범위

- 이번 작업에서 제품 코드·extension·native host를 만들지 않는다.
- v5 소스를 push·복사·정리·삭제하지 않는다.
- 실제 포털에 connect·login·click·capture하지 않는다.
- 자격증명 자동 입력을 구현하지 않는다.
- 검색어·필터 생성/입력을 HumanSearch에 넣지 않는다.
- 후보자 등록·발송·메일·InMail을 실행하지 않는다.
- 원격 push·PR·merge·배포를 하지 않는다.
- 이 문서가 라이브 가능성을 증명했다고 주장하지 않는다. B1과 V1 live acceptance가 그 증명이다.

---

## 12. ADR

### Decision

HumanSearch v6 브라우저 계층은 v5 raw CDP driver가 아니라 **사용자 동작으로 현재 탭에 임시 권한을
얻는 activeTab MV3 extension + Native Messaging host**로 새로 구축한다. 로그인은 human-auth 상태기계로 처리하고
자동 자격증명 입력은 코어에서 제거한다. 포털 계약은 2026-08-12 이후 fresh live capture에서만 만든다.

### Drivers

1. 사용자가 보는 창과 자동화가 제어하는 창을 구조적으로 동일하게 만들 것
2. v5 2,305줄의 책임·셀렉터·우발적 복잡도를 가져오지 않을 것
3. 현재 Chrome의 remote debugging 보안 정책과 v6 P17/P18 신뢰 경계를 지킬 것

### Alternatives considered

1. **v5 파일 분해 이식 — REJECT.** 줄 수만 나뉘고 책임 경계와 사고 패치가 계승된다.
2. **raw CDP를 새 코드로 다시 작성 — REJECT.** 소스 출처는 깨끗하지만 포트·프로필·target 추측이라는
   old architecture를 유지한다.
3. **Chrome DevTools MCP auto-connect — 보류.** 최신 Chrome에서 가능하지만 프로필 전체 접근과
   개발 도구 의존을 제품 코어에 넣는다. 진단용 대안 spike로만 남긴다.
4. **debugger 기반 Selected Tab Bridge — REJECT.** tabId를 코드가 선택할 뿐 권한은 브라우저가 선택 탭에
   제한하지 않고, debugger permission은 optional이 아니며 설치 경고 범위가 너무 넓다.
5. **Active Tab Bridge — 채택.** 사용자의 명시적 동작과 Chrome의 임시 tab/origin 권한이 handoff 경계를 강제한다.

### Consequences

- 새 extension/native host 설치 경계가 생긴다.
- service worker 재시작과 native protocol을 새로 검증해야 한다.
- 자동 로그인 편의는 초기 범위에서 포기한다.
- 반대로 포트 탐지, 기본 프로필 디버깅, 전체 target 열거, 브라우저 launch, Keychain 자동로그인,
  검색어·필터 입력이라는 큰 복잡도 묶음이 코어에서 사라진다.

### Follow-ups

1. 이 계획의 Claude 1차 적대검증과 Codex 재현 공격을 완료한다.
2. 승인 후 G1만 별도 worktree/PR로 시작한다.
3. G1~G3 병합 전에는 B1 extension spike를 시작하지 않는다.
4. B1이 실제 Chrome 151에서 증명되기 전 portal contract나 SQLite 파이프라인을 만들지 않는다.

---

## 13. 적대 검증 로그

Claude 명령: `env -u ANTHROPIC_API_KEY claude --safe-mode --no-session-persistence --permission-mode dontAsk --tools Read,Grep --model sonnet --effort low -p '<adversarial prompt>'`

Claude 1차 수정본 재공격 원문(ANSI만 제거):

> [BLOCKING] activeTab이 동일 origin 내 페이지 전이 후에도 권한을 유지한다는 §1 핵심 전제(L65-66) — 문서의 C-1~C-8 fresh-evidence 표에 이 주장이 없고 인용 링크에 "동일 origin navigation 후 grant 유지" 원문 인용이 없음 — B1 착수 전 Chrome 151 공식 문서 원문 인용 또는 실측으로 이 전제를 fresh evidence로 검증·기록하라.
> [BLOCKING] C1/C3 AC는 "fixture 텍스트 값 0"을 요구(§4-4 캡처와 PII)하면서 동시에 locator 우선순위 2단계로 "accessibility role/name"(본질적으로 text)을 쓰라고 규정(§4-4) — accessible name 자체가 text라 마스킹된 fixture로는 role/name 기반 matcher의 positive/negative 판정을 재현 불가 — text-free fixture에서 검증 가능한 locator 전략 범위를 명시하거나 텍스트 매칭용 해시/토큰화 스킴을 별도 설계하라.
> [BLOCKING] scripts/acceptance-hs-cleanroom.sh와 scripts/acceptance-hs-gates.sh가 아직 저장소에 존재하지 않는데(§0 C-1: humansearch 구현 0건) G1/G2 AC 행에 그 미래 스크립트의 기대 출력을 이미 확정 사실처럼 기재 — C-1~C-8 표와 달리 fresh evidence 컬럼이 없어 검증 기준이 미검증 상태로 통과 판정처럼 읽힘 — 해당 AC 행에 "미검증/향후 AC" 표기를 추가하라.
> [MATERIAL] RETURN_TO_RESULTS로 결과 페이지에 돌아가는 것도 navigation이므로 §1 회수 규칙("다른 origin 이동 시 회수")과 별개로 "동일 origin 재진입 후 실제로 grant가 유지되는지"를 검증하는 AC가 B1~B5 어디에도 없음 — B3은 RELEASE_HANDOFF 이후 재교환 실패만 검증 — B1 또는 B3에 "정상 결과↔프로필 왕복 후 grant 지속 여부"를 직접 검증하는 AC를 추가하라.
> [MATERIAL] §4-2는 host SQLite를 lease의 유일한 정본이라 하면서도, `tabs` permission 없이 SW 재시작 후 현재 tabId를 재확인할 프로토콜 경로가 명시돼 있지 않음 — B4 AC(재시작 후 idempotency)가 이 재획득 경로를 커버하는지 불명확 — 매 명령이 자기 tabId를 함께 보내는지 등 재획득 절차를 §4-2에 구체화하라.
> [MINOR] §10 SOT 체크리스트 전항목이 [x]로 표시됐으나 §11은 구현 0%를 명시 — "계획 반영"과 "구현 검증"을 같은 체크박스로 섞어 P2(실행 가능한 검증 명령 없으면 실패)의 정신과 충돌할 위험 — 체크박스를 "계획 반영됨"/"구현으로 검증됨" 두 상태로 분리 표기하라.
> VERDICT: REVISE

Codex 재공격 결과:

| Claude finding | 재현 판정·조치 |
|---|---|
| activeTab same-origin | **일치.** 공식 문서 lines 45-46을 C-9에 기록하고 Chrome 151 실측은 B1 NOT_RUN으로 분리했다. |
| text-free vs accessible name | **일치.** name/text/placeholder를 v1 locator에서 제거했다. 이 제약으로 portal을 못 읽으면 C1이 실패하는 것이 맞다. |
| 미래 스크립트가 실행된 듯 보임 | **일치.** 모든 Phase 출력은 향후 계약·현재 NOT_RUN이라고 명시했다. |
| 결과↔프로필 왕복 누락 | **일치.** B1에 same-origin round trip과 cross-origin revoke를 함께 넣었다. |
| SW 재시작 탭 재확인 누락 | **일치.** bound_tab_id/origin + tabs.get + nonce probe, 실패 시 새 click 절차를 넣었다. |
| 체크박스 과장 | **일치.** `계획 x/구현 NOT_RUN`을 분리했다. |

Claude 2차 회귀검증도 `VERDICT: REVISE`였으나 남은 5건은 B1/C1/B4와 전체 구현이 아직 NOT_RUN이라는 계획의 명시적 중단선이었고, 1건은 당시 비어 있던 이 로그였다. Codex 판정은 **계획 APPROVE / 구현 NOT_RUN**이다.
