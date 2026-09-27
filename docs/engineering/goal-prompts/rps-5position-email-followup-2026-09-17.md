# LinkedIn Recruiter(RPS) 후속 서치 실행 프롬프트 — 5개 포지션 신규 후보 이메일 확보 (2026-09-17)

> **[SUPERSEDED]** Codex·Gemini 적대적 리뷰에서 이 프롬프트가 유도하는 결과물 구조(레코드 파편화, 필드 상태값 뭉뚱그림, 기컨택 미검증)에 결함이 확인됐다. 이 문서 그대로 실행하지 말고 `rps-candidate-ledger-v2-2026-09-17.md`를 사용할 것.

너는 Valuehire v6 저장소(/Users/kangsangmo/Desktop/Valuehire_v6)에서 Aside 브라우저(claude-in-chrome MCP)로 LinkedIn Recruiter(RPS) 라이브 조사를 이어서 수행한다. 2026-09-17 1차 조사(기존 40명 이메일 확보 + 5개 포지션 1촌 신규 발굴)의 후속 작업이다. **이번 작업 범위는 아래 "신규 발굴 후보 26명의 이메일·프로필 확정"에 한정한다** — 포지션 재정의나 재검색 기준 변경은 하지 않는다.

## 이번 프롬프트가 반영한 1차 조사 시행착오 (반드시 준수)

1. **2촌 이메일은 시도하지 마라.** 1차 조사에서 2촌 13명 전원이 "Add email" 버튼만 뜨고 실패했다 — LinkedIn 구조상 인메일 발송 전에는 이메일이 원천적으로 비공개다. 신규 발굴 후보 중 2촌으로 확인되는 사람은 이메일 확보를 시도하지 말고 즉시 "2촌·확보불가"로 표시하고 다음으로 넘어가라. 시간 낭비하지 마라.
2. **[1촌] 라벨을 믿지 마라.** 신재현 사례처럼 원 목록의 촌수 표기가 실제와 다를 수 있다(스냅샷이 오래됐거나 그사이 연결 상태가 바뀜). 아래 명단의 "1촌" 표기도 재검증 없이 신뢰하지 말고, 프로필 진입 시 실시간으로 연결 상태를 다시 확인한 뒤 이메일 시도 여부를 결정하라.
3. **InMail/메시지 히스토리는 상세 정보가 화면에 없는 경우가 많다.** 날짜·포지션명이 안 보이면 오래 뒤지지 말고 "메시지 N건·프로젝트 M건 연결(상세 미확인)"처럼 확인 가능한 것만 기록하고 넘어가라. 완벽한 이력 복원을 목표로 하지 마라.
4. **1촌 풀이 이미 충분히 크므로(28명~505명) 2·3촌 확장은 하지 않는다.** 이번에도 아래 26명 명단 밖으로 신규 인원을 더 발굴할 필요는 없다 — 순수하게 "이미 찾은 사람들의 프로필 URL·이메일·이력 확정"이 목표다.
5. **브라우저 세션이 끊기면 재로그인을 시도하지 마라.** 비밀번호 입력 금지 원칙. 로그인 화면이 뜨면 조사를 멈추고 세션이 자동 복구될 때까지 기다렸다가 이어가라(1차 조사에서 실제로 한 번 발생, 자동 복구로 데이터 손실 없이 재개됨).
6. **작업을 마칠 때 반드시 마지막 assistant 텍스트 메시지에 아래 "산출물" 포맷 그대로 최종 요약을 출력하라.** (1차 조사에서 fork 완료 알림의 result 필드가 빈 값("-")으로만 잡히는 현상이 있었다. 알림과 별개로, 이 세션의 마지막 텍스트 응답 자체에 요약이 반드시 있어야 상위 세션이 결과를 바로 읽을 수 있다.)
7. **발송 절대 금지.** 신규 InMail, 연결 요청, 이메일 발송 0건. 이번 작업은 조사·확인만 한다.

## 브라우저 접속

- Aside 브라우저, deviceId `0c136c08` (2026-09-14 재확인됨). claude-in-chrome MCP 도구 사용: 먼저 ToolSearch로 `tabs_context_mcp, navigate, computer, read_page, tabs_create_mcp, tabs_close_mcp, get_page_text, find`를 한 번에 로드.
- LinkedIn Recruiter RPS 진입: contract-chooser 화면에서 RPS 선택 (참고: reference_linkedin_recruiter_rps_entry.md 메모리).
- 검색 필터 재현: 포지션 타이틀 chip + "Network relationships" → "1st Connections" 순으로 적용. 이전 검색 상태가 남아있지 않게 새 검색 전 필터를 리셋할 것.

## 대상 — 신규 발굴 후보 26명 (포지션별)

각 후보에 대해: (a) 정확한 프로필 URL 재확보, (b) 실시간 연결 촌수 재확인, (c) 1촌이면 이메일 확보 시도, (d) InMail/메시지 이력 확인 가능한 만큼만 기록.

### Forward Deployed Engineer (1촌 풀 28명 중 발췌 6명)
- Simon Zabrocki — Ecole Polytechnique+TU Munich, Palantir 재직 (최우선 추천)
- MoonHyuk Hur — 서울대 학사, Biodance 재직
- Hyeri Jung — 국민대+UC Irvine, NAVER Cloud
- seungjae lee — 목포해양대, Enhans 재직
- Taehoon Kim — POSTECH 석사+중앙대, Kurly ML Engineer, open to work ⚠ 메시지 4건·프로젝트 2건 연결(과거 제안 이력 있음, 상세 확인 시도)
- Daehyun Baek — 고려대, BCG Lead Forward Deployed AI Engineer ⚠ 메시지 3건·프로젝트 4건 연결(복수 포지션 제안 이력 추정, 상세 확인 시도)

### Full Stack Engineer (1촌 풀 505명 중 발췌 6명)
- 박예진 — 가톨릭대, 삼성 청년 SW아카데미 이수
- Jayce Park — 가톨릭대, 캐나다 거주(Hatch Innovations Canada)
- Aurélien Toussaint — Epitech(프랑스)+계명대, LUX PM 재직
- Eunkyoung Lim — 연세대, 24년+ 경력 ⚠ 메시지 1건·프로젝트 1건 연결(상세 확인 시도)
- JoongYong Kim — 참고용(인서울/국공립 기준 미달이나 확보 시도)
- LOGAN LEE — 참고용(인서울/국공립 기준 미달이나 확보 시도)

### Data Scientist — Manufacturing AI (1촌 풀 479명 중 발췌 5명)
- Rose Mihyun Jang — Edinburgh 석사, Applied Materials(반도체 장비) 재직 (최우선 추천)
- Youngkeun Yoon — Columbia 석사+고려대, Yanolja NEXT Data Scientist
- Hunhwa Song — 충북대(국립대), LLM·RAG·LangGraph 전문
- HyunKyung Boo — 참고용
- Namu Kim — 참고용

### Technical Architect (1촌 풀 50명 중 발췌 4명 — Dawoon Jung 제외, 기존 40명에 포함되어 이메일 이미 확보됨)
- Joon Hyung Kim — 도쿄농공대, AWS Senior Solutions Architect(AWS 인증)
- 이곤호 — 한국항공대, 과거 KT NexR Technical Architect 경력
- SUKHO KIM — 용인대, Infra Architect
- 황재건 — 생성형AI Technical Lead(학력 미확인)

### AI LLM Engineer (1촌 풀 34명 중 발췌 4명 — 백혜림·Jihye Back은 기존 40명에 포함되어 이메일 이미 확보됨)
- Sungmin Rhee — 서울대 박사, Kakao Corp LLM Research Engineer (최우선 추천)
- Yeonjung Hong — 고려대 박사, LG AI Research AI Product & Technical PM
- Jaehun Choe — 성균관대 박사, Samsung Electronics On-Device AI·LLM RAG Agent
- Wonbeom Jang — 상세 미확인(이름만 확보, 프로필 재검색 필요)

## 참고 — 이미 처리 완료된 사항 (재작업 불필요)

- 기존 40명 중 이메일 신규 확보 10명(Seungmin Ahn, taeyun Kang, Seongjin Kim, Benjamin Vasseur, Kyunghoon Cha, Dawoon Jung, 백혜림, Jihye Back, 김민아, Yeul-ho(Richard) S.) — 완료.
- 기존 40명 중 2촌 13명(Taekbeom Yoo, Joon Pyo Hong, Jeonghoon Lee, Beom Jin An, Daejune Ko, Eugene Lee, Myeongseon Kwak, Minsoo Choi, Giho Shin, 안창현, 남현수, CHANG KEUN LEE, 신재현) — 이메일 확보 불가 확인 완료, 재시도 금지.
- InMail 이력 제외 권고 2명 확정: Taekbeom Yoo(2025-10-30 발송, 무응답), Kiburm Song("ML/DL Engineer" 프로젝트 contacted). Dawoon Jung은 다른 포지션(STCLab) 이력 있으나 제외 안 함 — 이 3명 관련 재조사 불필요, 판단은 사장님 몫.

## 산출물 (마지막 assistant 텍스트에 반드시 이 포맷으로 출력)

1) 26명 중 이메일 확보 성공/실패 인원 수와 명단 (실패 사유: 2촌 구조적 불가 / 프로필 재발견 실패 / 기타)
2) InMail·메시지 이력이 새로 확인된 사람과 내용
3) Gmail로 sangmokang@valueconnect.kr 앞 발송 완료 여부와 message id
4) 막힌 부분·미완료 항목

## 안전선

- 발송(제안/InMail/이메일) 자동 클릭 0회.
- 자격증명 입력 0회, 재로그인 시도 0회.
- 같은 후보에서 2회 이상 같은 방식으로 막히면 "확인 실패"로 기록하고 다음 후보로 넘어간다(rabbit hole 금지).
