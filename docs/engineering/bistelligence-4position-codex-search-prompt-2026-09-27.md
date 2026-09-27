# 코덱스 전달 프롬프트 — 비스텔리전스 4개 포지션 실서치 (2026-09-27)

## 결론

비스텔리전스(BISTelligence)가 현재 모집 중인 **FDE / FSE / Data Scientist / Technical Architect** 4개 포지션을,
코덱스가 **Aside 브라우저로 직접 사람인과 LinkedIn RPS를 열어** 실제 후보자를 찾아오도록 하는 프롬프트입니다.

아래 `=== 프롬프트 시작 ===` 부터 `=== 프롬프트 끝 ===` 사이를 **그대로 복사해 코덱스에 붙여넣으면** 됩니다.
JD는 ClickUp 실데이터(4개 태스크)에서 읽어 반영했고, 과거 진행 이력 11명은 중복 방지 블록리스트로 넣었습니다.

## 근거 — ClickUp 원본 태스크

| 포지션 | ClickUp Task | 상태 라벨 | 경력 요건 |
|---|---|---|---|
| Forward Deployed Engineer | [86ey7ch7v](https://app.clickup.com/t/86ey7ch7v) | ai/ml/data | 3년+ |
| Full Stack Engineer | [86ey7cmgd](https://app.clickup.com/t/86ey7cmgd) | ai/ml/data | 3년+ |
| Data Scientist (Manufacturing AI) | [z8nfn6p2ke](https://app.clickup.com/t/z8nfn6p2ke) | ai/ml/data | 3년+ |
| Technical Architect | [z8nfn6p2kf](https://app.clickup.com/t/z8nfn6p2kf) | backend/fullstack/cto | **7년+** |

포지션 리스트: `FY26ClientsPosition` (901814621569) / 후보자 상태 리스트: `FY26CandidstesStatus` (901814621142)

## 작성 시 내가 정한 전제 (틀리면 프롬프트에서 해당 줄만 고치면 됩니다)

1. **"외국인 배제"의 운영 방식** — 프로필에서 국적은 확인할 수 없습니다. 그래서 국적 자체를 판정하지 않고,
   JD가 실제로 요구하는 **한국어 비즈니스 커뮤니케이션 가능 + 국내 근무 가능 + 국내 대학 학위**로 치환해 필터링하도록 썼습니다.
   FDE JD에 "한국어와 영어로 기술적, 비즈니스적 커뮤니케이션이 가능한 분"이 명시돼 있고, 고객사가 대기업 내부망·보안 정책 환경이라
   이 기준이 실무적으로도 법적으로도 더 안전합니다. 국적 기준 자체를 명시적으로 쓰길 원하시면 알려주세요.
2. **"인서울권"에 4대 과기원 포함** — KAIST·POSTECH을 빼면 직전 서치에서 상위로 올라온 후보들이 전부 탈락합니다.
   그래서 `인서울 + 과기원(KAIST/POSTECH/GIST/UNIST/DGIST)`을 Tier 1~2로 묶었습니다.
3. **"컴퓨터공학 전공"의 예외 1건** — Data Scientist JD는 *"산업공학, 통계학, 컴퓨터공학, 전기전자, 수학 등 관련 전공 석사 이상"*을
   명시하고 있어, DS 포지션만 인접 전공을 허용했습니다. 나머지 3개 포지션은 컴퓨터공학·소프트웨어 계열로 고정입니다.

---

=== 프롬프트 시작 ===

# 임무: 비스텔리전스 4개 포지션 후보자 실서치

너는 ValueConnect의 리크루팅 리서처다. 아래 4개 포지션에 맞는 **실제 후보자**를 **Aside 브라우저로 직접 사이트를 열어** 찾아온다.
추측·기억·생성으로 후보자를 만들어내지 마라. **브라우저에서 눈으로 본 프로필만** 결과에 넣는다.

## 0. 도구 제약 (반드시 지킬 것)

- 모든 서치는 **Aside 브라우저**로 수행한다. 탭을 열고, 검색어를 입력하고, 결과 목록을 스크롤하고, 프로필을 클릭해 읽는다.
- 로그인 세션이 필요한 사이트(LinkedIn Recruiter, 사람인 기업회원)는 **이미 로그인된 기존 탭/세션을 재사용**한다.
  로그인 화면이 뜨면 거기서 멈추고 사용자에게 알린다. 자격증명을 입력하거나 추측하지 마라.
- 프로필 URL은 **주소창에서 실제로 복사**한다. URL을 조합해서 만들지 마라.
- **후보자에게 메시지·이메일·InMail·연결요청을 절대 보내지 마라.** 이번 작업은 발굴까지다.
- 페이지 로딩이 느리면 기다린다. 결과가 0건이면 0건이라고 보고한다. 빈 결과를 채우지 마라.

## 1. 대상 포지션 (ClickUp에서 JD 원문 재확인 가능)

ClickUp 리스트 `FY26ClientsPosition`에 원문이 있다. 필요하면 해당 태스크를 열어 JD를 다시 읽는다.

### A. Forward Deployed Engineer — task `86ey7ch7v`
- 핵심: 고객 업무를 **Ontology로 모델링**하고 **Agent가 실행 가능한 구조**로 번역하는 역할. 단순 구현자가 아님.
- 요건: 3년+ SWE/솔루션/데이터 엔지니어링, 고객 직접 커뮤니케이션 경험, Python·SQL·TS 중 1개 이상
- 우대: Ontology / Knowledge Graph / semantic layer, LLM Agent·RAG·tool calling·evaluation, B2B SaaS·enterprise AI·solution architecture, PoC→Production 리드

### B. Full Stack Engineer — task `86ey7cmgd`
- 핵심: 설계된 AI 아키텍처를 **고객사 환경에서 실제 동작하는 시스템으로 구현**. Application + Integration Layer + UI/UX + 품질 최적화.
- 요건: 3년+ 풀스택(FE+BE 둘 다), React/Next.js, Python(FastAPI/Django) 또는 Node.js, REST API 연동, ETL 파이프라인, SQL, Docker/CI-CD
- 우대: 제조(반도체·철강·조선·배터리) 납품, MES·SAP ERP·SCADA·Historian(OSIsoft PI) 연동, Neo4j/Cypher, Kafka·MQTT, K8s/Helm 온프레미스, SSO/LDAP/RBAC, SI 납품

### C. Data Scientist (Manufacturing AI) — task `z8nfn6p2ke`
- 핵심: 제조 공정·설비·품질 데이터에서 신호를 찾아 **예측·진단·최적화 모델**로 연결. 현장 엔지니어가 신뢰할 수 있는 결과.
- 요건: 3년+ DS/ML/통계 모델링, Python + SQL, 통계적 추론·시계열·이상탐지, 대규모 실데이터 정제·Feature 설계
- 우대: 반도체·디스플레이·철강·배터리 데이터, **FDC·SPC·MES·설비로그·시계열**, 예지보전·이상탐지·공정최적화·수율/품질예측, MLOps·Model Monitoring, PyTorch/TF/XGBoost/LightGBM, 관련 전공 석사+

### D. Technical Architect — task `z8nfn6p2kf`
- 핵심: **밀리초 단위 고빈도 설비 데이터**의 수집→Streaming→Processing→Storage→Serving 전 경로 아키텍처 설계. 온프레미스·보안 제약 하 Production 품질.
- 요건: **7년+** Backend/Data Platform/분산시스템/인프라/솔루션아키텍처, 대용량·실시간 스트리밍 아키텍처 설계, Linux·네트워크·DB·스토리지·컨테이너 깊은 이해, Docker/K8s Production, RDB+NoSQL/시계열/분산스토리지, Event-driven·Message Broker, 온프레미스/Private Cloud 구축
- 우대: 반도체·디스플레이·배터리 고빈도 데이터, Kafka·MQTT, Flink·Spark Streaming, Time-series/Columnar DB·분산캐시, MES·SCADA·Historian·Edge Gateway(OT/IT), K8s/Helm 온프레미스 표준화, 대기업 보안환경 Architecture Review

## 2. 하드 필터 — 하나라도 어기면 제외 (예외 없음)

| 항목 | 기준 | 판정 방법 |
|---|---|---|
| 국내 인재 | 한국어 비즈니스 커뮤니케이션 가능 + 국내 근무 가능 + **국내 대학 학위 보유** | 프로필 언어, 학력 소재지, 경력지 국가로 판정. 해외 학위만 있고 국내 학력·경력이 전무하면 제외 |
| 학력 | **인서울 + 4대 과기원** (아래 Tier 표) | 학사 기준. 학사가 지방대라도 석사가 Tier 1~2면 통과 |
| 전공 | **컴퓨터공학·소프트웨어·전산 계열** | DS 포지션만 예외: 산업공학·통계학·전기전자·수학 허용 (JD 명시) |
| 경력 | FDE/FSE/DS 3년+, **TA 7년+** | 현재 재직 기준 누적 연차 |
| 중복 | 아래 §5 블록리스트에 없어야 함 | 이름 + 소속으로 대조 |

**Tier 정의**
- **Tier 1**: 서울대, KAIST, POSTECH, 연세대, 고려대
- **Tier 2**: 서강대, 성균관대, 한양대, 중앙대, 경희대, 한국외대, 서울시립대, GIST, UNIST, DGIST
- **Tier 3**: 건국대, 동국대, 홍익대, 숭실대, 세종대, 국민대, 광운대, 이화여대, 숙명여대, 서울과학기술대, 아주대, 인하대
- Tier 3 밖은 제외. 단 Tier 3는 우대사항(제조 도메인/Ontology/Kafka 등)이 **2개 이상** 실증될 때만 통과.

## 3. 플랫폼별 실행 절차

### 3-1. LinkedIn Recruiter (RPS) — 주력
1. Aside 브라우저로 LinkedIn Recruiter 검색 화면을 연다.
2. **Locations**: South Korea 고정. **Years of experience**: 포지션별 최소 연차 이상.
3. Keywords 칸에 §4의 Boolean 쿼리를 넣는다. `Current company` / `Past company` / `School` 필터를 조합한다.
4. 결과 수(`N results`)를 먼저 기록한다. **500건 초과면 쿼리가 너무 넓으니 좁히고, 20건 미만이면 너무 좁으니 넓힌다.**
5. 상위 결과를 순회하며 프로필을 열어 §2 하드 필터를 적용한다. 통과자만 기록한다.
6. **1촌(1st degree)·2촌 여부를 기록**한다. 1촌은 직접 연락 가능 자산이므로 별도 표시한다.
7. School 필터로 Tier 1~2 대학을 직접 지정한 쿼리도 **반드시 1회 이상** 돌린다 (인서울 요건 충족률이 급상승한다).

### 3-2. 사람인 (Saramin) — 보조·상호보완
1. Aside 브라우저로 사람인 기업회원 **인재검색**을 연다.
2. 검색 조건: 지역(서울·경기), 경력(포지션별 최소 연차), 학력(대졸 이상), 전공(컴퓨터공학 계열).
3. 키워드에 §4의 **한글 키워드 세트**를 넣는다. 사람인은 Boolean을 제대로 못 받으므로 **단일/2단어 키워드를 여러 번 나눠** 검색한다.
4. 이력서 공개 후보 위주로 순회하고, 최종학교·전공·재직사를 확인해 하드 필터를 적용한다.
5. LinkedIn에서 이미 찾은 사람과 **동일인 여부를 이름+회사+학교로 대조**해 중복을 제거한다.

두 플랫폼의 동일인은 하나로 합치고, `출처: LinkedIn+사람인`으로 표기한다. (양쪽 모두 등록 = 이직 의향이 높다는 신호)

## 4. 키워드 변이 루프 — 이 작업의 핵심

**한 번 검색하고 끝내지 마라.** 포지션별로 최소 **6회 이상** 키워드를 바꿔가며 돌린다. 규칙:

### 변이 사이클
```
[시드 쿼리 실행] → [결과 수 + 통과자 수 기록] → [수율 계산] → [다음 쿼리 결정] → 반복
수율 = 하드필터 통과자 수 / 검토한 프로필 수
```

### 다음 쿼리 결정 규칙
| 관측 | 다음 행동 |
|---|---|
| 결과 500건+ | 우대사항 키워드를 **AND로 추가** (예: `+ ("Kafka" OR "MQTT")`) |
| 결과 20건 미만 | 가장 희귀한 키워드를 **OR로 완화**하거나 삭제 |
| 수율 30% 미만 | 키워드가 엉뚱한 직군을 잡고 있다. **동의어를 교체** (아래 축 참고) |
| 수율 높은데 결과 적음 | 그 키워드를 **고정축으로 두고** 나머지를 회전시킨다 |
| 같은 사람만 반복 등장 | 회사축을 전환한다 (경쟁사 → 인접 도메인 → SI/컨설팅) |

### 회전시킬 4개 축
1. **직무명 축** — 같은 일의 다른 이름을 계속 바꿔 넣는다
   - FDE: `Forward Deployed Engineer` / `Solutions Engineer` / `Solution Architect` / `Implementation Engineer` / `Technical Consultant` / `Data Engineer` / `Delivery Engineer`
   - FSE: `Full Stack` / `Fullstack` / `Software Engineer` / `Web Developer` / `Application Engineer` / `Product Engineer`
   - DS: `Data Scientist` / `ML Engineer` / `Machine Learning Engineer` / `Research Engineer` / `데이터분석` / `공정분석`
   - TA: `Technical Architect` / `Solution Architect` / `Software Architect` / `Data Platform Lead` / `Principal Engineer` / `Tech Lead` / `Infrastructure Architect`
2. **기술 축** — JD 우대사항을 하나씩 넣고 뺀다 (Ontology / Knowledge Graph / Neo4j / Kafka / MQTT / Flink / Spark / K8s / Helm / FDC / SPC / MES / SCADA / Historian / OSIsoft PI / LangGraph / RAG / XGBoost / LightGBM / PyTorch / TimescaleDB / ClickHouse)
3. **도메인 축** — `반도체` / `semiconductor` / `디스플레이` / `display` / `철강` / `steel` / `조선` / `shipbuilding` / `배터리` / `battery` / `secondary battery` / `제조` / `manufacturing` / `smart factory` / `스마트팩토리` / `공정` / `수율` / `yield` / `예지보전` / `predictive maintenance`
4. **회사 축** — 인재가 실제로 고여 있는 곳을 돌아가며 지정
   - 제조 대기업: 삼성전자, SK하이닉스, LG에너지솔루션, 삼성SDI, 포스코, 현대제철, LG디스플레이, 삼성전기, HD현대
   - 제조 AI/솔루션: 원프레딕트(OnePredict), 가우스랩스(Gauss Labs), 마키나락스, 인이지, 슈퍼브에이아이, 알체라
   - SI/플랫폼: 삼성SDS, LG CNS, SK AX(SK C&C), 현대오토에버, 포스코DX, 롯데이노베이트
   - 플랫폼/온톨로지: Palantir 출신, 토스, 네이버, 카카오, 쿠팡, 라인, 우아한형제들

### 시드 쿼리 (여기서 시작해 변이시킨다)

**FDE**
```
("Forward Deployed Engineer" OR "Solutions Engineer" OR "Solution Architect" OR "Implementation Engineer")
AND (Ontology OR "Knowledge Graph" OR "semantic layer" OR "data modeling")
AND (Python OR SQL OR TypeScript)
```
변이 예: `Ontology` → `RAG`, `Agent`, `LangGraph`, `tool calling` / 회사축에 `Palantir`, `토스`, `SK AX` 투입

**FSE**
```
("Full Stack" OR Fullstack) AND (React OR "Next.js")
AND (FastAPI OR Django OR "Node.js")
AND (Docker OR Kubernetes OR Kafka)
```
변이 예: `+ (MES OR SCADA OR ERP OR Historian)` 로 제조 연동 경험자 압축 / `+ Neo4j` 로 그래프DB 보유자 압축

**DS (Manufacturing AI)**
```
("Data Scientist" OR "Machine Learning Engineer")
AND (제조 OR manufacturing OR 반도체 OR semiconductor OR 배터리 OR battery OR 디스플레이)
AND ("anomaly detection" OR "predictive maintenance" OR 이상탐지 OR 예지보전 OR 수율 OR yield)
```
변이 예: `+ (FDC OR SPC)` ← 이게 제조 DS 진성 후보를 가장 정확히 잡는 키워드다. 반드시 1회 이상 넣어라.

**TA**
```
("Technical Architect" OR "Solution Architect" OR "Software Architect" OR "Data Platform")
AND (Kafka OR MQTT OR Flink OR "Spark Streaming")
AND (Kubernetes OR Helm OR "on-premise" OR 온프레미스)
```
변이 예: `+ ("time series" OR TimescaleDB OR ClickHouse OR InfluxDB)` / `+ (Historian OR SCADA OR "Edge")`

**사람인용 한글 키워드 세트** (Boolean 안 되니 낱개로 나눠 검색)
- FDE: `온톨로지`, `지식그래프`, `솔루션엔지니어`, `데이터모델링`, `RAG`, `AI에이전트`, `PoC`
- FSE: `풀스택`, `리액트`, `Next.js`, `FastAPI`, `장고`, `쿠버네티스`, `MES연동`, `SI개발`
- DS: `데이터사이언티스트`, `공정데이터`, `이상탐지`, `예지보전`, `수율예측`, `품질예측`, `시계열분석`, `FDC`, `SPC`
- TA: `아키텍트`, `솔루션아키텍트`, `대용량처리`, `분산시스템`, `카프카`, `온프레미스`, `실시간처리`

## 5. 블록리스트 — 이미 진행된 비스텔리전스 후보 (중복 발굴 금지)

ClickUp `FY26CandidstesStatus`에 기록된 기존 후보다. 같은 사람이 검색에 나와도 **결과에 넣지 말고 "기존 진행자"로만 표시**한다.

| 이름 | 포지션 | 상태 | 재접촉 |
|---|---|---|---|
| 인정우 | FDE | 서류탈락 | 금지 |
| 김현균 | FDE | 서류탈락 | 금지 |
| 오정석 | FDE | 서류탈락 | 금지 |
| 권대화 | FDE | 면접후탈락 | 금지 |
| 최준호 | FDE | 셀프드롭 | 금지 |
| 김호엽 | FDE | 셀프드롭 | 금지 (진행 의사 낮음) |
| 김선범 | FDE | 고객사추천 | 진행 중 |
| 김건우 | FDE Jr. | 제안(추천대기) | 진행 중 |
| 정희민 | FDE Jr. | 제안(추천대기) | 진행 중 |
| 채완수 | FDE | 제안(추천대기) | 진행 중 |
| 홍성의 | AI Engineer | 1차 면접/coffee chat | 진행 중 |

작업 시작 전 ClickUp `FY26CandidstesStatus` 리스트를 한 번 조회해 **그 사이 추가된 후보가 있는지 확인**하고 블록리스트를 갱신한다.

## 6. 후보자 평가 — 100점

| 항목 | 배점 | 판정 기준 |
|---|---|---|
| JD 직무 적합도 | 40 | 주요업무 5개 항목 중 실제로 해본 것의 개수와 깊이 |
| 우대사항 실증 | 25 | JD 우대사항 중 프로필에서 **문장으로 확인되는** 항목 수 (추측 금지) |
| 제조/엔터프라이즈 도메인 | 15 | 반도체·디스플레이·철강·조선·배터리 또는 대기업 온프레미스 납품 경험 |
| 학력 Tier | 10 | Tier 1 = 10 / Tier 2 = 7 / Tier 3 = 4 |
| 안정성·성장성 | 10 | 재직기간 패턴, 직급 상승, 잦은 이직 여부 |

**70점 미만은 결과에 넣지 마라.** 70점을 못 넘기면 그 키워드 조합이 실패한 것이니 §4로 돌아가 키워드를 바꾼다.

## 7. 산출물

포지션별로 아래 표를 만든다. **포지션당 최소 8명, 목표 12명.**

| # | 이름 | 점수 | 1촌 | 출처 | 프로필 URL | 학력(학사/석사) | 현재 소속·직책 | 연차 | 핵심 적합 근거 (JD 항목 인용) | 리스크 |
|---|---|---|---|---|---|---|---|---|---|---|

표 아래에 반드시 함께 보고할 것:

1. **검색 로그** — 실행한 모든 쿼리를 순서대로: `쿼리 문자열 | 플랫폼 | 결과 수 | 검토 수 | 통과 수 | 수율%`
   (키워드를 실제로 변이시켰다는 증거다. 이 로그가 없으면 작업 미완료로 간주한다.)
2. **버려진 키워드와 이유** — 수율이 낮아 폐기한 조합
3. **포지션별 난이도 판정** — 어느 포지션이 인재풀이 얇은지, 왜 그런지
4. **하드필터 탈락 통계** — 학력/전공/연차/국내인재 중 무엇 때문에 가장 많이 걸렸는지
5. **추천 우선순위 Top 5** — 포지션별, 접촉 순서와 그 이유

## 8. 금지 사항

- 브라우저에서 확인하지 않은 후보자를 만들어내는 것
- URL을 조합해 만드는 것
- 후보자에게 메시지/이메일/InMail/연결요청 발송
- 하드 필터를 "아깝다"는 이유로 완화하는 것 (완화하려면 사용자에게 먼저 물어라)
- 검색 로그 없이 결과만 제출하는 것
- 한 포지션에 쿼리 1~2회만 돌리고 끝내는 것

=== 프롬프트 끝 ===

---

## 부록 — 실행 순서 권장

1. **TA부터** 시작한다. 7년+ 요건 때문에 풀이 가장 얇고, 여기서 실패하면 조기에 알아야 한다.
2. 다음 **DS**. `FDC`/`SPC` 키워드로 진성 후보가 빠르게 압축된다.
3. **FDE**는 직무명 동의어 회전이 가장 많이 필요하다 (국내에 "FDE"라는 타이틀 자체가 드물다).
4. **FSE**는 풀이 가장 두꺼우니 마지막에 하되, 제조 연동 경험으로 조여야 변별력이 생긴다.

## 남은 확인 필요 사항

- 4개 포지션의 **연봉 밴드·처우 조건**이 ClickUp JD에 없다. 후보 설득 단계에서 필요하니 별도 확보가 필요합니다.
- AI Engineer(LLM) 포지션은 이번 4개 범위에서 제외했습니다 (홍성의 후보가 1차 면접 진행 중). 포함이 필요하면 알려주세요.
