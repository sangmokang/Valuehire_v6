# HumanSearch D0 브라우저 접속 계약 목표 — 2026-08-18

## 1층 — 결론

이번 변경은 HumanSearch가 어느 브라우저에 어떻게 접근할지를 문서 한 곳에서 결정합니다. 사람인과
잡코리아의 정상 흐름은 사람이 매번 버튼을 누르지 않는 방향으로 고정하되, 로그인이나 보안 확인이
필요한 순간에는 자동 처리를 멈추고 사람을 부릅니다.

선택한 방식은 **채널별 상주 브라우저 + 로컬 진단 포트**입니다. 진단 포트는 이미 켜져 있는
브라우저를 외부 프로그램이 점검할 수 있게 하는 로컬 접속 통로입니다. 이번 변경은 그 통로를 실제로
열거나 브라우저에 접속하지 않습니다. 다음 단계가 따라야 할 권한·탭·중단·개인정보 경계만 정합니다.

이 문서와 새 정본이 검토 요청에 올라가도 D1 환경 실증, C1 실제 화면 관측, 로그인 자동화와 후보
검색은 시작되지 않습니다. 실제로 확인하지 않은 항목은 모두 미실행으로 남깁니다.

## 2층 — 왜 이 길인가

정상 명령마다 사용자가 현재 탭을 다시 선택하는 방식은 접근 범위가 좁지만, 원격 명령 뒤 사람 클릭
0회라는 운영 목표를 충족하지 못합니다. 반대로 진단 포트는 클릭 없이 기존 탭에 접근할 수 있지만,
브라우저 프로필과 열린 탭에 넓은 권한을 줄 수 있습니다. 편의가 아니라 이 보안 대가를 먼저 인정하고
작은 전용 프로필, 정확히 하나인 목표 탭, 짧은 사용권, 즉시 권한 회수를 계약으로 강제합니다.

**무엇을** — 사람인·잡코리아·LinkedIn Recruiter 모두 상주 브라우저에 로컬 진단 포트로 접속합니다. 사람인·잡코리아는 채널별 비기본 전용 프로필을, LinkedIn Recruiter는 사장님의 실제 로그인 프로필을 재사용합니다(이유는 아래 2-1 결정 카드).

**왜** — 정상 상황의 클릭 0회 목표와 기존 로그인 세션 재사용을 함께 만족시키면서, 탭 추측·자격증명 입력·브라우저 생성과 종료를 계약으로 금지할 수 있는 경계이기 때문입니다.

**버린 길** — PR #15의 Active Tab Bridge(사용자가 확장 버튼으로 현재 탭 하나를 넘기는 방식)는 정상 명령마다 사람 동작이 필요하므로 D0의 운영 목표와 맞지 않아 버립니다. `activeTab`의 좁은 권한 경계가 틀렸다는 뜻은 아닙니다.

**대가** — 사람 클릭이 제공하던 대상 확인과 브라우저 자체의 좁은 권한 강제가 사라지므로, 전용 비기본 프로필·단일 탭 확인·사용권 만료와 증가 번호·사람 입력 즉시 회수를 모두 증명해야 합니다.

**되돌리기** — 새 L3 결정 기록과 오너 승인으로 이 정본과 D1 이후 구현을 함께 중단한 뒤 Active Tab Bridge 또는 다른 좁은 접속 경계를 다시 선택합니다. 이전 PR #15 문서를 조용히 되살리지 않습니다.

**틀리면 무엇이 깨지는가** — 잘못된 탭이나 계정에 명령이 가거나, 사람이 개입한 뒤에도 자동 명령이
계속되거나, 프로필 전체의 인증 자료에 접근하는 능력이 제품에 생길 수 있습니다. 이 가운데 하나라도
막지 못하면 D1과 C1은 시작할 수 없습니다. LinkedIn의 경우 페이싱(사람 수준 접속 속도) 조건을 지키지
않으면 2026-07-18에 실제로 있었던 Cloudflare 봇 차단이 재발할 수 있습니다.

### 2-1. LinkedIn Recruiter 자동 순회 — 2026-08-19 정정 결정 카드

**무엇을** — LinkedIn Recruiter 사이트 내부의 프로젝트 확인·필터 순회·후보 목록 넘겨보기 자동화를 허용합니다. 조건: (1) 새 전용 프로필이 아니라 사장님 실제 로그인 프로필을 CDP로 재사용, (2) 카드 클릭 간격 지터·동일 URL 연속 재접속 금지·캡차/2단계 인증 즉시 중단. 메시지 발송 자동화는 여전히 금지입니다.

**왜** — 사장님이 이미 2026-08-14에 확정했고 2026-08-15에 페이싱과 함께 라이브로 실행된 선례가 있었는데, "금지" 문구는 이를 반영하지 않은 별도 미승인 제안서의 문구가 그대로 정본에 옮겨진 것이었습니다(근거는 아래 문단).

**버린 길** — "금지 유지"는 사장님 지시에 반해 버립니다. "속도 제한만 추가"도 기각합니다 — 실제 차단 원인은 속도가 아니라 전용 프로필 사용이었습니다(근거는 아래 문단).

**대가** — LinkedIn만 "실프로필 재사용"이라는 다른 프로필 전략을 쓰게 되어 채널별 전략이 통일되지 않습니다. 페이싱 조건을 D1이 실제로 증명하기 전까지 이 허용은 정책일 뿐 실제 자동화 코드는 여전히 `NOT_RUN`입니다.

**되돌리기** — 다시 막으려면 새 L3 결정과 오너 승인이 필요합니다. 2026-08-15 제안서 자체는 고쳐 쓰지 않고 "제안" 상태 그대로 역사 기록으로 남깁니다.

**근거 상세** — 이 goal의 2026-08-18 초판은 "LinkedIn 자동 순회는 허용 근거 확인 전까지 금지"라고
적었습니다. 추적해보니 사장님은 이미 2026-08-14에 이를 확정하셨고
(`docs/engineering/goal-prompts/humansearch-journey-nightshift-2026-08-14.md:8` 결정 ⑥ "RPS는
프로젝트 생성+필터 세팅 선행 후 필터순회→키워드교체"), 2026-08-15에는 사람 수준 페이싱과 함께 실제
라이브로 실행된 선례도 있었습니다
(`docs/engineering/goal-prompts/codex-5position-search-2026-08-15.md:3-33`, "봇 회피: 카드 클릭
간격 지터, 같은 URL 연속 2회 열지 말 것, 캡차·2FA 감지 즉시 STOP"). "금지" 문구는 이 두 근거를
반영하지 않고, 같은 2026-08-15에 별도로 작성된 검토용 제안서(문서 자신이 "승인 상태: 오너 승인
전"이라고 명시,
`docs/engineering/humansearch-journey-alternative-plan-2026-08-15.md:1-9,301-303`)의 미확정
제안을 그대로 정본에 옮긴 것이었습니다. 사장님이 2026-08-19에 직접 정정을 지시하셨고, Codex 독립
검증(V1)도 동일하게 VERDICT: FAIL(사용자 지시 근거 없음, 반대 증거 존재)로 판정했습니다. 실제 차단
원인은 2026-07-18 실측 정본
(`docs/engineering/humansearch-v6-founding-spec-2026-08-07.md:214-231`)에 근거합니다 — 속도가
아니라 "전용 프로필 사용"이었습니다.

## 3층 — 기술 계약과 증거

### 위험 등급과 소유 범위

- 위험 등급: **L3**. 인증 세션·개인정보·외부 포털에 닿는 후속 구현의 최상위 정본을 새로 만듭니다.
- 이번 변경이 소유하는 파일:
  - `docs/engineering/humansearch-d0-browser-contract-goal-2026-08-18.md`
  - `docs/sot/humansearch-browser-contract.md`
  - `docs/sot/INDEX.md`
- 이번 변경은 문서만 소유합니다. 제품 코드, 브라우저 설정, 프로필, 포트, 탭, 포털, 캡처 자료는
  변경하거나 읽지 않습니다.
- `AGENTS.md`는 현재 저장소 파일 목록에 없었습니다. 이번 실행에는 사용자가 대화에 제공한
  `AGENTS.md` 전문을 최상위 작업 계약으로 적용합니다. 저장소 파일로 존재한다는 식으로 과장하지
  않습니다.

### 착수 기준선과 시작 게이트

- PR #26은 2026-08-18 `b6aee6a352309cfd721cd3b3d63d31ff7c0787f9`로 squash merge됐습니다.
- `origin/main`에 `docs/sot/humansearch-l0-surface-contract.md`와 INDEX 등재가 존재합니다.
- PR #15는 확인 시점에 `OPEN`, `CONFLICTING`, `DIRTY`였습니다. 그 브라우저·로그인·PII 계약은
  현행 정본이 아니라 공개된 후보안·반례 근거입니다.
- 첫 Gate 0은 공유 객체 저장소에서 여러 독립 검사와 경합해 15분 이상 완료되지 않아 우리 세션의
  프로세스만 종료했습니다. 검사 명령을 바꾸지 않고 `origin/main` 단일 브랜치 격리 복제본에서
  재실행했습니다.
- 격리 복제본에는 실제 비밀값 대신 비추적 합성 카나리 한 줄만 사용했고 실행 뒤 제거했습니다.

```text
HEAD: b6aee6a (synced)
ORIGIN: b6aee6a
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 무엇을 시켰나: `bash scripts/session-status.sh`가 원격 기준선과 20개 시작 검사를 확인하게 했습니다.

→ 뭐가 나왔나: 원격과 같은 기준선에서 미해결 빨간불 0개였습니다.

→ 좋은가 나쁜가: D0 문서 변경을 시작할 수 있는 합격 결과입니다. 제외된 `acceptance-0-7.sh`는
저장소 정본대로 서버 검사 담당이며 이번 PR의 서버 검사에서 별도로 확인합니다.

### 읽은 정본과 근거 범위

다음 범위를 읽고 현재 상태와 충돌을 대조했습니다.

- 사용자가 제공한 `AGENTS.md` 전문
- `docs/sot/git-workflow.md`
- `docs/sot/coding-principles.md`
- `docs/sot/verification-commands.md`
- `docs/sot/INDEX.md`
- `docs/sot/humansearch-l0-surface-contract.md`
- `docs/engineering/humansearch-journey-master-plan-2026-08-14.md`
- `docs/engineering/humansearch-journey-alternative-plan-2026-08-15.md`
- `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md`
- PR #15의 `humansearch-v6-clean-room-rebuild-goal-2026-08-12.md`
- Chrome for Developers의 현재 원격 디버깅 보안 변경, 기존 세션 연결, 자동 연결 문서
- Chrome DevTools Protocol의 현재 브라우저·탭 발견 문서

v1~v5 코드·경로·설계는 복사·불러오기·실행하지 않습니다. 과거 문서에 적힌 실패·충돌은 금지 능력과
반대 사례를 찾는 근거로만 사용합니다.

### 근거 우선순위

이번 PR이 병합된 뒤 브라우저 접속 문제의 우선순위는 다음과 같습니다.

1. `docs/sot/humansearch-browser-contract.md` — 브라우저 접속·권한·중단·채널 차이의 현행 정본
2. `docs/sot/humansearch-l0-surface-contract.md`와 공통 SOT — 화면 분류와 저장소 공통 불변식
3. `humansearch-journey-master-plan-2026-08-14.md` — D0 필요성과 클릭 0회 사업 목표의 역사 기록
4. `humansearch-journey-alternative-plan-2026-08-15.md` — 미검증 항목·반례·후속 계획의 역사 기록
5. PR #15의 clean-room 문서 — Active Tab Bridge와 개인정보 경계의 병합되지 않은 후보 기록
6. `humansearch-v6-founding-spec-2026-08-07.md` — 과거 실패와 초기 raw CDP 후보의 역사 기록

아래 문서들은 삭제하거나 소급 수정하지 않습니다. 새 정본과 충돌할 때 브라우저 접속 결정에는 1번이
우선하며, 다른 요구까지 자동으로 대체하지 않습니다.

### 공식 Chrome 근거와 제품 계약의 경계

2026-08-18 확인 기준 공식 문서가 증명하는 사실은 다음과 같습니다.

- Chrome 136부터 기본 Chrome 데이터 디렉터리에 `--remote-debugging-port` 또는
  `--remote-debugging-pipe`를 붙여도 무시되며, 비기본 `--user-data-dir`가 함께 필요합니다.
- 기존 브라우저 세션 자동 연결은 사용자가 Chrome 설정에서 원격 디버깅을 켜고 허용해야 하며,
  연결 도구는 열린 탭·세션·로컬 저장소·쿠키 등 프로필 자료에 넓게 접근할 수 있습니다.
- 수동 진단 포트 연결 예시는 별도 사용자 자료 폴더를 사용합니다.
- 진단 프로토콜의 `/json` 또는 `/json/list`는 탭 대상을 열거하고, 브라우저 수준 접속 주소는
  `/json/version`에서 얻을 수 있습니다. `--remote-debugging-port=0`은 선택된 포트를
  `DevToolsActivePort`에 기록할 수 있습니다.
- 진단 프로토콜은 탭 열기·활성화·닫기 같은 넓은 명령도 제공할 수 있습니다.

공식 문서는 HumanSearch의 목표 탭 선택 규칙, 사람 입력 감지, 사용권 만료, LinkedIn 허용 범위를
정하지 않습니다. 이것들은 Chrome이 보증한 사실로 표현하지 않고 HumanSearch가 D1 이후 증명해야 할
제품 계약으로 분리합니다.

공식 링크:

- <https://developer.chrome.com/blog/remote-debugging-port>
- <https://developer.chrome.com/docs/devtools/agents/get-started/configuration>
- <https://developer.chrome.com/docs/devtools/agents/use-cases/auto-connect>
- <https://chromedevtools.github.io/devtools-protocol/>

### 해소할 충돌과 목표 판정

| 충돌 | 목표 판정 | 남는 대가·한계 |
|---|---|---|
| Active Tab Bridge 대 상주 브라우저 진단 포트 | 상주 브라우저 + 로컬 진단 포트 채택 | 브라우저가 탭 하나로 강제하던 좁은 권한을 잃으므로 전용 프로필·단일 탭·금지 능력을 제품이 증명해야 함 |
| 정상 흐름 사용자 클릭 필요 대 클릭 0회 | 사람인·잡코리아의 준비된 정상 세션은 클릭 0회 | 최초 브라우저 준비·사람 로그인과 인증 예외는 사람 작업이며 자동 재개는 NOT_RUN |
| raw CDP 금지 후보 대 진단 포트 사용 | 임의 프로토콜 전달·전체 대상 제어 능력은 금지하고, D1이 증명한 최소 접속 어댑터만 허용 | 진단 포트 자체의 넓은 능력은 사라지지 않으므로 capability 부재 시험 필요 |
| 채널별 전용 프로필 대 기존 사람 세션 | 사람인·잡코리아는 채널별 비기본 전용 프로필에 사람이 직접 로그인한 세션 사용 | 평소 기본 프로필이나 다른 사람 세션에 자동 접속 금지; 세션 충돌은 중단 |
| 사람인·잡코리아 대 LinkedIn Recruiter | 셋 다 D1 이후 준비된 정상 흐름을 허용하되 LinkedIn은 실프로필 재사용+페이싱 조건이 추가로 붙음(§2-1) | LinkedIn은 전용 새 프로필을 쓰지 않고, 저장·발송은 계속 사람이 수행 |

→ 표가 말하는 것: 다섯 충돌은 하나를 숨기거나 합치지 않고 각각 채택안, 대가, 채널별 한계로 해소합니다.

### 단일 인수 기준

> 새 SOT 한 곳이 상주 브라우저 + 로컬 진단 포트를 유일한 접속 방식으로 정하고, 충돌한 후보안의
> 지위와 보안 대가를 공개하며, 사람인·잡코리아·LinkedIn의 서로 다른 허용 범위, 단일 목표 탭,
> 사용권·중단·사람 개입·자격증명·개인정보 경계와 모든 미실증 항목의 `NOT_RUN` 상태를 빠짐없이
> 명시한다.

반대 사례는 다음과 같습니다.

- 검사 성공이나 포트 응답만으로 장기 세션·재부팅·업데이트·자동 재개를 완료라고 씁니다.
- 여러 탭 중 URL이나 순서가 그럴듯한 하나를 자동으로 고릅니다.
- 코드가 비밀번호·쿠키·토큰을 읽거나 입력할 수 있습니다.
- 사람 입력 뒤 남아 있던 명령이나 이전 증가 번호의 명령이 계속 실행됩니다.
- 진단 포트 사용을 이유로 임의 raw CDP 명령 전달, 새 탭·창 생성, 브라우저 종료 능력이 생깁니다.
- 기본 사람 프로필 전체를 정상 접속 대상으로 간주합니다.
- LinkedIn Recruiter 자동 순회를 계약·계정 허용 근거 없이 추정합니다.
- C1이 이 D0 문서만으로 실제 포털에 접속하거나 개인정보를 저장할 수 있다고 씁니다.

### D1이 구현 전에 따라야 할 접속 계약 모양

문서 계약의 최소 입력은 다음 필드입니다. 실제 타입과 저장 방식은 D1이 별도 goal과 시험으로
결정합니다.

```json
{
  "channel": "saramin | jobkorea | linkedin",
  "lease_id": "opaque-id",
  "fencing_number": "strictly-increasing-integer",
  "expires_at": "timestamp",
  "allowed_origins": ["channel-specific exact origins"],
  "browser_instance_proof": "fresh D1 proof",
  "profile_instance_proof": "fresh D1 proof (linkedin은 사장님 실프로필 증거여야 함)",
  "target_tab_proof": "exactly one fresh matching target"
}
```

→ 무엇을 시켰나: D1이 기억한 포트·경로·탭 번호 대신 매 작업에서 새 증거를 입력으로 받게 했습니다.

→ 뭐가 나와야 하나: 채널당 살아 있는 사용권 하나, 만료 시각, 이전 권한을 무효화하는 증가 번호,
허용 주소와 정확히 하나인 목표 탭 증거가 함께 있어야 합니다.

→ 좋은가 나쁜가: 하나라도 빠지면 실행하지 않는 것이 합격입니다. 포트 번호와 프로필 경로의 실제
발견 방식은 D1 실증 전까지 `NOT_RUN`입니다.

LinkedIn Recruiter도 D1이 실프로필 재사용·페이싱 조건을 증명한 뒤에는 같은 입력 구조로 사용권을
얻을 수 있습니다(§2-1). 그 전까지는 사이트 밖 로컬 준비만 가능합니다.

### 허용 능력과 금지 능력

후속 제품 코드는 다음 능력을 가져서는 안 됩니다.

- 비밀번호·쿠키·토큰을 읽거나 입력하는 능력
- 로그인·보안문자·2단계 인증을 제출하거나 우회하는 능력
- 새 창·새 탭을 만들거나 브라우저·사람 탭을 닫는 능력
- 목표 탭이 0개 또는 2개 이상일 때 임의 대상을 고르는 능력
- 허용 도메인 밖으로 이동하거나 접근하는 능력
- 임의 raw CDP 명령을 문자열로 전달하는 범용 통로
- 만료됐거나 더 작은 증가 번호를 가진 권한으로 명령을 계속하는 능력
- 사람 입력이 감지된 뒤 대기열·재시도·콜백을 계속 실행하는 능력

사람인·잡코리아의 후속 정상 흐름은 다음 조건을 모두 만족할 때만 시작할 수 있습니다.

1. 채널별 비기본 전용 프로필의 이미 실행 중인 브라우저입니다.
2. 사람이 직접 로그인한 정상 세션입니다.
3. 포트가 로컬 주소에만 열려 있다는 새 증거가 있습니다.
4. 허용 도메인과 화면 종류를 실행 전에 확인합니다.
5. 목표 탭이 정확히 하나입니다.
6. 채널당 활성 작업이 하나이고 사용권이 만료되지 않았으며 증가 번호가 최신입니다.
7. 사람 입력 감지와 즉시 권한 회수가 D1 중립 시험에서 증명됐습니다.

### 중단 계약

다음 중 하나면 사람을 한 번 호출하고 자동 처리를 중단합니다.

- 로그인 만료 또는 미로그인
- 보안문자·캡차
- 2단계 인증·추가 인증
- 세션·좌석·프로필 충돌
- 허용 도메인 또는 목표 화면 불일치
- 목표 탭 0개 또는 2개 이상
- 브라우저·프로필·포트 증거 불일치
- 사용권 만료·증가 번호 역전·채널 중복 작업
- 사람 입력 감지
- 화면 계약 불일치 또는 `DRIFTED`

중단 뒤 자동 재개하지 않습니다. 사람이 문제를 해결하더라도 새 작업 권한, 새 증가 번호, 새
브라우저·프로필·탭·로그인 증거로 처음부터 다시 확인하는 동작이 D1 이후 별도 승인되기 전에는
`NOT_RUN`입니다.

### C1이 사용할 최소 접속 경계

C1은 다음 선행 조건을 모두 만족할 때만 별도 승인으로 실제 화면 하나를 관측할 수 있습니다.

1. L0와 이 D0 SOT가 `main`에 병합돼 있습니다.
2. 추적되는 C1 캡처·개인정보 계약이 현재 `main`에 있습니다.
3. 오너가 해당 C1 실행을 명시적으로 승인했습니다.
4. 사람이 D0가 지정한 채널 전용 프로필에 직접 로그인했습니다.
5. 원본의 저장 위치·암호화·0700 디렉터리·0600 파일 권한이 준비됐습니다.
6. 보존기간·삭제 작업·삭제 결과 영수증 계약이 승인되고 시험됐습니다.
7. raw DOM·ARIA·스크린샷이 Git·로그·PR로 나가지 않는 차단 검사가 통과했습니다.
8. 개인정보 제거 fixture가 이름·본문·placeholder 없이도 판정 가능한 전략을 정본으로 가집니다.
9. C1 실행 직전에 사람이 승인한 일회성 증거로 브라우저·프로필·로컬 포트·목표 탭 하나를 다시
   확인합니다. 자동 탐지와 자동 재확인은 D1 전까지 사용하지 않습니다.

C1의 최소 허용 동작은 별도 C1 정본에 기록된 exact origin과 정확히 하나인 허용 탭에서 현재 화면을
읽는 것뿐입니다. 이 일회성 확인을 D1 자동 탐지 완료라고 부르지 않습니다. 새 탭·창 생성,
브라우저 종료, 로그인 제출, 검색어·필터 입력, 후보 상세 열기, 저장·등록·발송은 금지합니다. raw
DOM·ARIA·스크린샷은 모두 개인정보 자료로 취급하고 Git 밖 보호 위치에만 둘 수 있습니다.

C1은 로그인 만료, 보안문자, 2단계 인증, 세션 충돌, 사람 입력, 목표 탭 수 불일치, 주소 불일치,
저장·보존 계약 불충족 중 하나라도 만나면 포털 조작 없이 중단합니다.

### `NOT_RUN` 장부

이번 D0에서 다음 항목은 실행하거나 확인하지 않았습니다.

| 항목 | 상태 | 다음 증명 주체 |
|---|---|---|
| 실제 포트·프로필 경로 자동 발견과 재확인 | NOT_RUN | D1 중립 실증 |
| 재부팅 뒤 브라우저 자동 기동 | NOT_RUN | D1 |
| 브라우저 업데이트 뒤 호환성 | NOT_RUN | D1 |
| 세션 장기 유지·채널별 기존 사람 세션과 충돌 없음 | NOT_RUN | D1 및 안전한 사람 실증 |
| 사람 입력 감지 즉시 권한 회수·잔여 명령 0 | NOT_RUN | D1 중립 시험 |
| 인증 복구 뒤 자동 재개 | NOT_RUN | 별도 결정 전 금지 |
| 사람인·잡코리아 실제 탭 단일 선택 | NOT_RUN | D1/C1 선행 계약 뒤 실증 |
| LinkedIn Recruiter 자동 순회 — 정책 허용(§2-1)의 실제 코드 구현 | NOT_RUN | D1이 실프로필 재사용·페이싱 조건을 중립 시험으로 증명 |
| 실제 포털·로그인·후보 검색·화면 캡처 | NOT_RUN | C1 이후 각 별도 단계 |

→ 표가 말하는 것: 문서 결정과 실제 동작 증명을 분리하며, 미실행 항목을 D0 완료로 올려 쓰지 않습니다.

### 적대 검증 질문

Claude V1과 Codex V2는 새 최종 지문에서 최소한 다음을 공격합니다.

1. 자격증명 또는 전체 프로필 접근 능력이 몰래 다시 생겼는가.
2. 목표 탭을 추측하거나 여러 탭 중 임의로 선택하는가.
3. 사람 개입 뒤 자동 명령이 계속될 수 있는가.
4. 검증하지 않은 세션 지속성·재부팅·업데이트·자동 재개를 완료라고 적었는가.
5. LinkedIn 허용 범위를 추정했는가.
6. 진단 포트 사용과 임의 raw CDP 전달 금지를 모순 없이 구분했는가.
7. C1 경계가 D1 증거와 개인정보 계약 없이 실제 접속을 허용하는가.
8. 기존 역사 문서와 새 SOT의 우선순위가 브라우저 접속 문제에만 한정되는가.

중간 이상 결함이 하나라도 있으면 문서를 고치고 새 지문에서 V1과 V2를 다시 실행합니다.

### 검증 명령과 완료 조건

필수 로컬 검증:

```bash
bash verify.sh
git diff --check
bash ~/.claude/skills/strict/brief-lint.sh docs/engineering/humansearch-d0-browser-contract-goal-2026-08-18.md
```

→ 무엇을 시키나: 비밀 노출, 공백 오류, 사장님 브리핑 계약 위반을 각각 검사합니다.

→ 합격 기준: 모든 명령 종료값 0, brief-lint 위반 0건입니다.

사람 검토가 필요한 항목:

- 새 SOT의 충돌표가 다섯 충돌을 모두 공개했는가.
- 미결정과 `NOT_RUN`이 실제 미실증 상태를 숨기지 않는가.
- Active Tab Bridge를 버린 이유·보안 대가·되돌리기가 충분한가.
- C1 접속·중단·개인정보 경계가 실제 포털 실행 권한으로 과장되지 않는가.
- LinkedIn 자동 순회 허용(§2-1)이 실제 오너 확정(2026-08-14)·라이브 선례(2026-08-15)에 근거하며,
  실프로필 재사용·페이싱 조건이 충분한가.

배송은 일반 push와 한국어 PR 생성, 서버 검사 성공 확인까지만 수행합니다. D0 PR의 `main` 병합,
브라우저 실행, 포털 접속, C1, D1 구현은 금지합니다.

완료 표현은 모든 검증과 서버 검사가 성공하고 PR이 열렸을 때만 다음 문장을 그대로 사용합니다.

> 브라우저 접속 계약은 문서로 확정됐고 D1·C1 구현은 아직 시작하지 않았다.

## 적대 검증 로그

최종 SOT 초안과 INDEX가 준비된 뒤, 새 지문에서 Claude V1 전체 출력과 Codex V2 재공격 결과를 이
절에 원문으로 추가합니다. 문서 전체에 대한 새 V1/V2는 아직 `NOT_RUN`입니다.

### §2-1 LinkedIn 정정에 대한 Codex 독립 리뷰 (2026-08-19)

정정 전 "LinkedIn 자동 순회 금지" 조항이 사장님 지시인지, AI 자체 제안인지를 Codex(`/codex:rescue`,
격리된 맥락, 제 결론은 알리지 않음)에게 독립적으로 물었습니다.

```
VERDICT: FAIL

(a) No explicit user instruction prohibiting LinkedIn Recruiter automated traversal was found.
    The strongest-supported lineage is: AI-reviewed risk proposal → D0 acceptance criterion →
    categorical proposed-SOT rule. ... the repository contains user-attributed evidence
    supporting automated RPS traversal with controlled behavior.
(b) The single Cloudflare incident supports profile/session redesign and cautious pacing, not
    a universal traversal ban; the founding document itself proposed a different profile
    strategy as the remedy. ... The evidence therefore supports an interim compliance/risk gate
    plus owner acknowledgment—not silently replacing the recorded product requirement with an
    absolute prohibition.
(c) Yes, controlled traversal is technically compatible with the other safeguards ... The
    LinkedIn profile clause should use the approved existing single-seat owner profile rather
    than assuming a fresh automation-only profile, because the latter is the profile type
    recorded as blocked.

RECOMMENDATION: replace the LinkedIn-wide prohibition with conditional traversal permission:
one approved single-seat session and exact target, serial execution, measurable human-like
pacing/jitter and cooldown, no rapid repeat URLs, and immediate stop on human input, login,
CAPTCHA, 2FA, security checkpoint, or session conflict. Retain the credential, arbitrary-CDP,
tab creation/closure, storage, and automatic-message-sending prohibitions; preserve the
August 15 proposal as historical risk analysis rather than rewriting it as an approved decision.
```

→ 무엇을 시켰나: Codex에게 이 저장소 안에서 "금지 조항의 진짜 근거가 사용자 지시인지 AI 제안인지"와
"사용자가 요구한 수정(허용+속도제한)이 타당한지"를 독립적으로 판정하게 했습니다.

→ 뭐가 나왔나: FAIL(=금지 조항은 사용자 지시가 아니었다) — 제 자체 분석과 결론이 일치했고, 오히려
제가 못 찾았던 2026-08-14 사장님 확정 결정 ⑥과 2026-08-15 라이브 실행 선례를 Codex가 추가로 찾아
근거를 보강했습니다. 프로필 재사용 조건("전용 새 프로필 대신 기존 단일 좌석 프로필")도 동일하게
권고했습니다.

→ 좋은가 나쁜가: 좋은 소식입니다 — 서로 다른 두 엔진(Claude, Codex)이 독립적으로 같은 결론에
도달했고, §2-1의 수정 내용이 Codex 권고와 정확히 일치합니다. 이 검증은 §2-1 하나만 겨냥한
정조준 검증이며, 정정된 문서 전체에 대한 새 V1/V2 전체 재공격은 여전히 `NOT_RUN`입니다.
