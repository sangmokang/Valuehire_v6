# HS-13 — 포지션 브리프·서치 패킷 (Position Brief & Search Packet) 스펙·타입·WU 장부 (2026-09-10)

> 이 문서는 `docs/engineering/humansearch-next-issues-wu-2026-09-10.md`(브랜치 `task/hs-0003-20260910`, 미병합)의
> Issue 번호 체계 HS-00~HS-12 뒤에 **HS-13**을 덧붙이는 구현 지시서다. 아래 예정 파일·시험은 현재 존재하거나
> 통과한다고 주장하지 않는다. 각 WU 카드의 상태 열이 정본이며 초기값은 전부 `PLANNED`다.

## 0. 용어 풀이

- **브리프(brief)** = 한 포지션에 대해 팀에 보내는 내부 공유 메일 한 통. 회사 리서치 + 채널별 JD 3종 + 초도 후보 목록.
- **패킷(packet)** = 브리프를 만들기 위해 모은 구조화 자료 묶음(포지션·JD 원문·회사 사실·후보·메일 본문). 파일 하나.
- **JD 충실도(fidelity)** = 원문 JD의 내용 줄이 렌더링 결과에 빠짐없이 그대로 들어 있는가. "100% 정확히" 요구의 기계 판정.
- **RPS** = LinkedIn Recruiter(유료 서치 도구). **InMail** = RPS에서 후보에게 보내는 메시지(1,900자 제한).
- **러너(runner)** = 손 조작(메일 발송·브라우저)을 맡는 실행자. 이 Issue에서는 Claude 세션이 MCP 도구로 발송하고, 코드는 판정만 한다.

## 1. 상위 목표 (한 문장)

사장님이 ChatGPT "Search" 프로젝트에서 손으로 반복하는 "포지션 → 회사 리서치 → JD 3버전 → 팀 메일 → 초도 LinkedIn 후보" 작업을
**결정적 코드(검증·조립)와 러너(리서치·발송)로 분리**해, 한 포지션당 30분 안에 팀 메일 1통이 검증된 형식으로 나가고
그 결과가 로컬 장부에 남게 한다. 성공 신호 = 실제 포지션 1건에 대해 `[포지션]고객사, 포지션명` 메일이 발송되고
독립 readback(발송함 재조회)의 본문 해시가 패킷 해시와 일치한다.

## 2. 사장님 지시 9단계 검토 (2026-09-10 지시 vs 정본·기존 장부)

| # | 지시 | 판정 | 근거·수정안 |
|---|---|---|---|
| 1 | ClickUp·Gmail에서 포지션 파악 | **채택** | ClickUp `FY26ClientsPosition`(list 901814621569, 상태 `scraped` 100+건)과 Gmail `subject:"[포지션]" in:sent` 대조. 실측(09-10): 최근 14일 브리프 발송 13건, 클라이언트 직접 의뢰 중 미발송 = 번개장터 Product Manager(Core Product)·글로벌 BD PM·럭셔리 패션 리더, 스캐터랩 7건, 토트 전장 엔지니어, 역전에프앤씨 2건, BISTelligence Full Stack |
| 2 | 어떤 포지션을 할지 검토 | **채택(결정 D1)** | 우선순위 = 클라이언트가 메일로 직접 의뢰(`[포지션]` 접두) > 최근 14일 미발송 > 사장님 담당. 자동 선택은 하지 않고 **후보 목록을 브리프 메일 머리에 제안**한다. |
| 3 | 고객사 인재 밀도를 LinkedIn에서 확인 | **보류(HS-11 의존)** | D0 정본 §4·§5: LinkedIn 자동 접속은 D1 증명·exact-origin 정본화 전 금지. 지금은 **공개 웹 검색(WebSearch)으로 재직자 수·C레벨 공개 프로필**만 수집한다. RPS 안 "회사 인재 밀도" 화면은 HS-11.04 이후. |
| 4 | JD에 맞는 서치, 고학력·이직 적음·프로필 충실 우선 | **채택(순수 함수 채점)** | 장부 원칙 "채점은 계약으로 정한 순수 함수, LLM 점수 금지". 러너(LLM)는 **구조화 사실**만 추출하고 점수는 `score_candidate()`가 계산한다. 4축(직무 직결 40·학력 20·재직 안정성 20·프로필 충실도 20). 학교명 서열은 `contracts/humansearch/schools-tier.json`에 두고 코드에 두지 않는다(P22). |
| 5 | 1촌이면 Email Contact 확보 | **부분 채택** | 1촌 여부·연락처는 LinkedIn 로그인 화면에서만 보인다 → HS-11 이후. 지금은 **공개 출처(논문·연구실 페이지·회사 공지)에서 확인된 이메일**만 `EmailContact(source_url, provenance)`로 담고, 출처 없는 이메일은 타입이 거부한다. |
| 6 | URL·매칭 이유·점수·학력·경력을 DB에 쌓고 4명에게 메일, 제목에 ValuehireSearch | **채택(결정 D2·D3)** | 수신 4명은 `contracts/humansearch/team-recipients.json`(ClickUp 멤버 API 실측: sangmokang·rogan·julian·kcs @valueconnect.kr). DB = HS-03.01 SQLite 스키마가 병합되기 전까지는 **git 밖 패킷 파일**(`~/.humansearch/packets/<id>.json`, 0600)에 저장하고 HS-13.09에서 표로 옮긴다. |
| 7 | 사람인·잡코리아는 나중에 | **채택** | 사람인·잡코리아용 2필드 텍스트는 지금 만들고(HS-13.04), 사이트 등록 자동화는 기존 스킬 `position-register`·HS-11 범위. |
| 8 | RPS 프로젝트·South Korea·Boolean AND/OR 반복 서치 | **부분 채택** | Boolean 검색식 생성은 순수 함수(HS-13.07)로 지금 만든다. RPS 화면 조작(프로젝트 생성·필터·순회)은 D0 §4 LinkedIn 조항상 D1 이후 = HS-11.04~06 뒤 **HS-13.11로 예정**. "멈추지 말고 계속"은 D0 §9 사람 개입·1초 멈춤(⑨) 아래에서만 가능. |
| 9 | 후보별 1,900자 InMail 준비 + 이메일로도 전달 | **채택** | `build_inmail()` 순수 함수(HS-13.08). 발송은 절대 자동화하지 않는다(D0 §4 "발송은 별도 L3 승인 없이 항상 금지"). 브리프 메일 하단에 후보별 InMail 초안을 붙인다. |

추가로 지시에 없지만 필요한 것: ① JD 원문은 **첨부가 아니라 패킷에 해시와 함께 보존**(P9 readback) ② 메일은 **평문 텍스트**(사장님 요구 "디자인된 형식보다 텍스트") ③ 후보 PII는 Git·PR·판정 파일에 0건(P21·scan-data-exposure).

## 3. 현재 상태 (file:line, 추측 금지)

- 제품 코드: `humansearch/src/humansearch/` 최상위 `auth_surface.py`·`observe.py`·`_cdp.py` + `admin_weekly_dashboard/`. 브리프·JD·메일·채점 코드 **0줄**.
- 시험: 211 passed(2026-09-10 10:21, 워크트리 `hs-1300-brief-spec-20260910`, `uv run --no-sync pytest -q`).
- 계약: `contracts/humansearch/saramin-markers.json` 하나. 팀 수신자·학교 계층 계약 없음.
- 현재 프로세스: 사장님이 ChatGPT에서 손으로 생성 → Gmail로 발송. 09-09 하루 6건. 황금 표본 = Gmail thread `1a085e8e789eaf79`("[포지션]패스트뷰, AI Engineer", 2026-09-09 11:23Z). 이 메일의 구조가 §5 출력 계약의 원형이다.
- 근본 원인(왜 코드가 필요한가): 손 생성물은 ① LinkedIn 1,900자 초과 ② JD 문장 누락·임의 추가(외부 공고 조건 혼입) ③ 점수 근거 불일치 ④ 수신자 누락(09-09 메일 중 3건이 CC 없이 본인에게만) — 네 가지를 사람이 매번 눈으로 확인하고 있다.

## 4. 입력 영역 표 (결정성 규율 ①)

| 입력 | 정상 | 빈값·null | 경계 | 형식 위반 | 중복·재시도 | 외부 장애 | 처리 |
|---|---|---|---|---|---|---|---|
| ClickUp 포지션 id | `86e…`/`z8n…` 실존 | 없음 | — | 형식 아님 | 같은 id 2회 → 같은 패킷 id | API 불가 | 실존·필수 필드 없으면 **명시적 거부**; 네트워크 실패는 `NOT_RUN` |
| JD 원문(text) | 1줄 이상 내용 줄 | 빈 문자열 | 1줄, 50,000자 | 제어문자·HTML 태그 | — | — | 빈값·태그 잔존 → 거부. 화면 요소(로고·버튼) 제거는 러너가 하고 `JdSource.raw`엔 제거 후 텍스트 + 원본 sha256 |
| JD 원문(url/file) | http(s) URL, 로컬 파일 | — | — | 스킴 아님 | — | fetch 실패 | 코드는 URL을 열지 않는다. 러너가 열어 text로 넘긴다(R3) |
| 회사 사실(CompanyBrief) | 각 항목 `Claim(value, sources≥1)` | 항목 미확인 = `None` | 출처 0개 | 출처 URL 형식 위반 | 같은 출처 id 2회 | — | **출처 없는 값은 거부**, 미확인은 `None`으로 명시(추측 금지) |
| 후보(CandidateLead) | linkedin_url 필수 | url 없음 | 점수 0·100 | url이 linkedin.com/in/ 아님 | 같은 url 2회 | — | url 없거나 도메인 다름 → 거부; 중복 url → 거부 |
| 이메일 연락처 | 주소+출처 URL | 없음 = `None` | — | 주소 형식 위반·출처 없음 | — | — | 출처 없는 주소 → 거부 |
| LinkedIn 본문 길이 | ≤1,899자 | — | 1,899·1,900 | — | — | — | 1,900 이상 → 거부(`len()` 코드포인트 기준, 개행 포함) |
| 수신자 | 계약 파일의 주소 | 계약 파일 없음 | — | 주소 형식 위반·도메인 다름 | 중복 주소 | — | 계약 밖 주소·타 도메인 → 거부 |
| 시계 | 호출자가 `date` 주입 | — | — | — | — | — | 코드는 `datetime.now()`를 부르지 않는다 |
| **그 외 전부** | | | | | | | **명시적 거부(`BriefInputError`)** |

## 5. 계약 (SDD — 입출력 모양 먼저)

패키지: `humansearch/src/humansearch/brief/`. 전부 순수 함수·frozen dataclass. 네트워크·파일·시계 접근 0.
파일당 soft 300줄(P11). `__init__.py`는 아래 공개 이름만 노출한다.

```python
# types.py
class BriefInputError(ValueError): ...

@dataclass(frozen=True) class SourceRef:  id: str  # "C1","U1","L1","Y1","I1"
    url: str; title: str; checked_on: date
@dataclass(frozen=True) class Claim:  value: str; source_ids: tuple[str, ...]  # 비어 있으면 거부
@dataclass(frozen=True) class PositionSpec:
    clickup_task_id: str; client_name: str; title: str; department: str | None
    employment_type: str | None; location: str | None; recruiting_window: str | None
@dataclass(frozen=True) class JdSource:
    text: str; raw_sha256: str; provided_by: str  # "U1"
@dataclass(frozen=True) class CompanyBrief:   # 각 항목 Claim | None
    legal_name; founded; ceo; headquarters; headcount; revenue; operating_profit
    funding_stage; funding_total; products: tuple[Claim, ...]; history: tuple[Claim, ...]
    news: tuple[Claim, ...]; youtube: tuple[Claim, ...]; c_level: tuple[ExecProfile, ...]
    sources: tuple[SourceRef, ...]   # Claim.source_ids ⊆ sources.id 아니면 거부
@dataclass(frozen=True) class ExecProfile:  name_role: str; linkedin_url: str | None; summary: Claim
@dataclass(frozen=True) class EmailContact:  address: str; source_url: str; provenance: str
class ConnectionDegree(Enum): UNKNOWN, FIRST, SECOND, THIRD_PLUS
@dataclass(frozen=True) class CandidateEvidence:   # 러너가 추출하는 구조화 사실 (점수 입력)
    role_match_terms: tuple[str, ...]; jd_required_terms_hit: int; jd_required_terms_total: int
    highest_education: str | None; school_tier: int | None   # 계약 파일 기준 1~4, None=미확인
    tenure_months_per_job: tuple[int, ...]; jobs_last_5y: int
    profile_fields_filled: int; profile_fields_total: int
@dataclass(frozen=True) class ScoreBreakdown:  role: int; education: int; stability: int; profile: int
    @property total -> int  # 0..100, 각 축 상한 40/20/20/20
@dataclass(frozen=True) class CandidateLead:
    display_name: str; headline: str; linkedin_url: str; education: str; career: str
    match_reasons: tuple[str, ...]; check_points: tuple[str, ...]
    evidence: CandidateEvidence; score: ScoreBreakdown
    email: EmailContact | None; degree: ConnectionDegree; source_note: str
@dataclass(frozen=True) class JdPacket:   # 채널별 3종
    gmail_body: str; linkedin_body: str; two_field_company: str; two_field_jd: str
@dataclass(frozen=True) class TeamMail:
    subject: str; to: tuple[str, ...]; cc: tuple[str, ...]; body: str; body_sha256: str
@dataclass(frozen=True) class SearchPacket:
    packet_id: str; position: PositionSpec; jd: JdSource; company: CompanyBrief
    jd_packet: JdPacket; candidates: tuple[CandidateLead, ...]; mail: TeamMail
    boolean_queries: tuple[str, ...]; inmails: tuple[tuple[str, str], ...]  # (linkedin_url, body)
```

```python
# jd_fidelity.py
def content_lines(text: str) -> tuple[str, ...]          # 공백·글머리표·마크다운 기호 정규화 후 빈 줄 제외
def verify_fidelity(jd: JdSource, rendered: str) -> FidelityReport   # missing: tuple[str,...], extra_numeric: tuple[str,...]
#   합격 = missing == () 이고, rendered에만 있는 "연차·학력·연봉 숫자 조건"(extra_numeric)이 0개
# linkedin_limit.py
LINKEDIN_MAX = 1899
def check_linkedin(body: str) -> LinkedInReport      # length, ok, over_by
def verify_linkedin_fidelity(jd, body, omittable_sections: tuple[str, ...]) -> FidelityReport
#   생략은 호출자가 이름으로 지정한 절(예: "전형 절차","복리후생")의 줄만 허용. 그 밖의 누락은 FAIL
# two_field.py
def split_two_field(jd: JdSource, company_intro: str, section_markers: tuple[str, ...]) -> tuple[str, str]
#   필드1 = 회사 소개(company_intro), 필드2 = JD 본문(section_markers로 시작하는 절부터 끝까지). 필드2는 verify_fidelity 통과 필수
# mail.py
BRIEF_SUBJECT = "[포지션]{client}, {title}";  SEARCH_SUBJECT = "[ValuehireSearch][포지션]{client}, {title}"
def load_recipients(path) -> Recipients     # contracts/humansearch/team-recipients.json; 도메인 valueconnect.kr 외 거부
def compose_brief_mail(packet_without_mail, recipients, today: date) -> TeamMail   # §6 순서 그대로, 평문
# scoring.py
def score_candidate(ev: CandidateEvidence) -> ScoreBreakdown   # 결정적·순수. 동일 입력 → 동일 출력
# boolean_query.py
def build_boolean_queries(required_terms, synonyms: Mapping[str, tuple[str,...]], exclude: tuple[str,...]) -> tuple[str, ...]
#   최소 3식: 좁게(AND 위주)·표준·넓게(OR 확장). 각 식은 괄호 균형·따옴표 균형 검사
# inmail.py
def build_inmail(lead: CandidateLead, linkedin_body: str, greeting: str) -> str   # ≤1899 보장 못 하면 거부
# packet.py
def packet_id(position: PositionSpec, jd: JdSource, today: date) -> str   # "{yyyymmdd}-{clickup_id}-{sha8}"
def to_json(packet) / from_json(text)  # 왕복 동일성. PII는 파일에만, 로그 0
```

### 6. 출력 계약 — 팀 메일 본문 순서 (황금 표본 `1a085e8e789eaf79`에서 도출)

```text
{고객사} {포지션명} | 밸류커넥트 내부 공유
작성·확인 기준일: {YYYY년 M월 D일}
(인사 1문단 + 핵심 1줄)
원문 반영 기준 (글머리표 4줄 이내)
====================================================
1. 일반 Gmail용 | 후보자 전달용        ← JD 전문(verify_fidelity PASS)
====================================================
2. LinkedIn RPS용 | 공백·줄바꿈 포함 {n}자   ← [복사 시작]…[복사 끝], n ≤ 1,899
====================================================
3. 사람인·잡코리아용 | 2개 필드          ← [필드 1: 회사 소개] / [필드 2: JD 내용]
====================================================
[회사 리서치 | {날짜} 확인]  1.개요·근무지 2.매출·영업이익·투자 3.연혁 4.제품 5.뉴스 6.대표·C레벨 7.YouTube 8.확인할 항목
[서치 기준]  키워드 / LinkedIn 검색식(boolean_queries 전부) / 초도 인터뷰 질문
====================================================
[출처 목록]  [U1][I1][C#][L#][Y#]
====================================================
[초도 LinkedIn 후보자 | 내부 검토용]  후보마다: 이름|헤드라인 / LinkedIn / 잠정 매칭 n/100 (역할·학력·안정·프로필) / 학력 / 경력 / 매칭 이유 / 확인할 부분 / Email Contact(출처) / 1촌 여부
[후보별 InMail 초안 | 발송 전]  후보마다 ≤1,899자
```

## 7. 결정 목록 (결정성 규율 ② — 오너 확정 전엔 아래 기본값)

| id | 결정 | 기본값(이 문서) | 사장님 정정 시 |
|---|---|---|---|
| D1 | 다음 포지션 자동 선택? | **선택하지 않는다.** 우선순위 목록만 제안 | — |
| D2 | 브리프 메일 수신 방식 | To: 4명 전원(sangmokang·rogan·julian·kcs). **첫 라이브 1건은 To: sangmokang만**(새 코드 첫 출력을 사장님이 먼저 봄), 이후 4명 | 첫 라이브부터 4명이면 계약값 하나만 바꿈 |
| D3 | 제목 | 브리프 `[포지션]{고객사}, {포지션명}` / 서치 결과 단독 메일 `[ValuehireSearch][포지션]…`. 브리프에 후보가 포함되면 제목 끝에 ` | ValuehireSearch`를 붙여 라벨 필터 가능하게 | — |
| D4 | 1,899자 계산 | Python `len()`(코드포인트), 개행 포함, `[복사 시작]/[복사 끝]` 제외. LinkedIn 실측(09-09 표본 1,710자 표기)과 ±0 일치를 HS-13.03 라이브에서 1회 확인 | — |
| D5 | JD "100% 정확"의 판정 단위 | **내용 줄**(공백·글머리표·마크다운 기호 정규화 후). 순서 보존은 요구하지 않음. 외부 공고의 연차·학력·연봉 조건 혼입은 FAIL | 순서까지 요구하면 검사 강화 |
| D6 | 점수 4축 | 역할 40·학력 20·안정성 20·프로필 20. 학교 계층은 계약 파일. 성별·나이·사진 0 | 축·가중치는 계약 파일로 이동 가능 |
| D7 | 후보 PII 보관 | git 밖 `~/.humansearch/packets/`, 0700/0600. 저장소·PR·판정에는 packet_id·해시·건수만 | HS-03.01 병합 후 SQLite로 이관(HS-13.09) |
| D8 | 러너 경계 | 리서치(WebSearch)·Gmail 발송·readback은 Claude 세션이 MCP로 수행. 코드는 발송 API를 갖지 않는다 | Python Gmail API 도입은 별도 L3 |

## 8. 예외 표 (R1)

| 상황 | 처리 |
|---|---|
| JD 원문에 HTML 잔존·화면 요소 | 러너가 정리 후 재투입. 코드는 `<`/`>` 태그 발견 시 거부 |
| LinkedIn 본문 1,900자 이상 | 자동 축약 금지. 러너가 `omittable_sections`를 지정해 재생성, 그래도 초과면 중단·보고 |
| 회사 사실 출처 없음 | 값 삭제·`None`. 추정값 삽입 금지 |
| 후보 linkedin_url 미확인 | 후보 제외(URL 필수 지시) |
| 동명이인 | `source_note`에 식별 근거 필수, 없으면 제외 |
| 수신자 계약 파일 없음/타 도메인 | 발송 0, 중단 |
| Gmail 발송 후 readback 불일치 | 성공으로 기록 금지. `SENT_UNVERIFIED`로 남기고 보고 |
| 후보에게 직접 발송 요청 | 거부(D0 §4). InMail 초안만 |
| **그 외 전부** | **명시적 중단 + 이 표 갱신 후 재개** |

## 9. Issue HS-13 — WU 카드

성공: 실제 포지션 1건의 브리프 메일이 검증된 형식으로 발송·readback 일치. 소유: `src/brief/`, `tests/test_hs_13xx.py`,
`contracts/humansearch/team-recipients.json`, `contracts/humansearch/schools-tier.json`.
선행: 없음(순수 로직). 라이브(13.10)는 D2 수신 규칙과 §8 예외표 아래에서만.
공통 인수 명령 꼬리: `cd humansearch && uv run --no-sync ruff check src tests && uv run --no-sync mypy src tests`.

| WU | 행동 하나 | 인수 명령 | 정상 / 반례 | 상태 |
|---|---|---|---|---|
| HS-13.00 | 이 스펙·타입·장부를 저장소에 남긴다 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1300.sh` — §4 catch-all 행·§7 D1~D8·§9 카드 12개·§5 공개 이름 존재를 센다 | 문서 존재+절 8개 PASS; 결정 id 누락·카드 삭제 → FAIL | PLANNED |
| HS-13.01 | 타입을 fail-fast로 검증한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1301.py` (≥ 20 passed) | 정상 SearchPacket 1건 생성; Claim 출처 0·후보 URL 도메인·이메일 출처 없음·중복 URL·수신자 타 도메인 거부; Hypothesis: 임의 문자열 URL 중 linkedin.com/in/ 아닌 것 전부 거부 | PLANNED |
| HS-13.02 | JD 충실도를 줄 단위로 판정한다 | `pytest -q tests/test_hs_1302.py` (≥ 15 passed) | 황금 표본(패스트뷰 JD, 비식별)에서 Gmail판 PASS; 1줄 삭제·어순 바꿈·"2년 이상" 추가 → FAIL; 글머리표 `•`↔`-`·공백 차이는 PASS; 빈 JD 거부 | PLANNED |
| HS-13.03 | LinkedIn 1,899자 한도와 생략 정책을 강제한다 | `pytest -q tests/test_hs_1303.py` (≥ 12 passed) | 1,899 PASS·1,900 FAIL(경계 Hypothesis); 표본 LinkedIn판 1,710자 재계산 일치; 지정 절 생략 PASS·미지정 절 누락 FAIL | PLANNED |
| HS-13.04 | 사람인·잡코리아 2필드로 나눈다 | `pytest -q tests/test_hs_1304.py` (≥ 8 passed) | 표본에서 필드1·필드2 생성, 필드2 fidelity PASS; 마커 없음·필드2 빈값 거부 | PLANNED |
| HS-13.05 | 팀 메일 제목·수신자·평문 본문을 조립한다 | `pytest -q tests/test_hs_1305.py` (≥ 12 passed) + `run-acceptance.sh scripts/acceptance-hs-1305-pii.sh`(시험 fixture·판정 파일에 이메일·전화 패턴 0) | 제목 정확 일치 2형; §6 절 순서 정확; 수신자 계약 로드·타 도메인 거부; body_sha256 왕복; 본문에 HTML 0 | PLANNED |
| HS-13.06 | 후보를 순수 함수로 채점한다 | `pytest -q tests/test_hs_1306.py` (≥ 15 passed, Hypothesis 포함) | 같은 입력 100회 동일; 축 상한 40/20/20/20; 학교 계층 계약 파일 로드; None 학력 = 0점(추정 금지); 총점 0·100 경계 | PLANNED |
| HS-13.07 | Boolean 검색식 3종을 만든다 | `pytest -q tests/test_hs_1307.py` (≥ 8 passed) | 괄호·따옴표 균형 속성; 필수어 전부 포함; 제외어 `NOT`; 빈 필수어 거부 | PLANNED |
| HS-13.08 | 후보별 InMail 초안을 만든다 | `pytest -q tests/test_hs_1308.py` (≥ 8 passed) | ≤1,899 보장·초과 시 거부; 후보 이름·매칭 이유 1개 포함; 발송 API 부재(정적: `send`·`smtplib`·`requests` import 0) | PLANNED |
| HS-13.09 | 패킷을 git 밖에 저장·readback한다 | `pytest -q tests/test_hs_1309.py` (≥ 8 passed) + `run-acceptance.sh scripts/acceptance-hs-1309-paths.sh`(`.gitignore`·`scan-data-exposure.sh`가 `~/.humansearch` 경로·`*.packet.json` 차단) | 임시 디렉터리 0700/0600; JSON 왕복 동일; 손상 파일 거부; 같은 packet_id 2회 → 1파일 | PLANNED |
| HS-13.10 | 실제 포지션 1건 라이브 | 러너 절차 §10 + `uv run --no-sync python -m humansearch.brief verify --packet <path> --sent <readback.txt>` exit 0 | 발송 1·readback 해시 일치 1; 불일치 → `SENT_UNVERIFIED` | PLANNED |
| HS-13.11 | RPS 검색·프로젝트 순회 | **PLANNED — 선행 HS-05·HS-11.04~06**. 이 문서에서 명령 확정하지 않음 | — | BLOCKED(선행) |
| HS-13.12 | 패킷 → SQLite 이관 | **PLANNED — 선행 HS-03.01** | — | BLOCKED(선행) |

→ 00 → 01 → (02, 06, 07 병렬) → 03 → 04 → 05 → 08 → 09 → 10. 11·12는 선행 병합 뒤.
각 WU = 워크트리 1개 = PR 1개. 선행 PR 미병합이면 그 브랜치를 base로 잡고 PR 본문에 SHA를 적는다.

## 10. HS-13.10 러너 절차 (R3 — 손 조작은 러너, 판단은 코드)

1. ClickUp 포지션 1건 선택(D1 목록에서 사장님 지시 또는 최상위) → JD 원문 확보(ClickUp description 또는 고객 메일) → `JdSource`.
2. WebSearch로 회사 사실 수집. 모든 값에 출처 id. 미확인은 `None`.
3. 공개 LinkedIn 프로필 검색(WebSearch, `site:linkedin.com/in`) → 후보 3~5명. 구조화 `CandidateEvidence` 추출.
4. 코드: `verify_fidelity`·`check_linkedin`·`split_two_field`·`score_candidate`·`build_boolean_queries`·`build_inmail`·`compose_brief_mail` → 패킷 저장.
5. 러너: Gmail `send_message`(subject·to·body를 패킷에서 그대로) → `search_threads(in:sent)` → `get_thread(PLAIN_TEXT)` → 본문을 `verify --sent`에 투입 → 해시 일치만 `PRODUCTION_VERIFIED`.
6. 보고: packet_id·해시·수신자 수·후보 수·글자 수만. 이름·URL·이메일은 보고에 0.

## 11. 게이트 계획·적대검증 정조준

- 게이트: 각 WU RED 커밋 → GREEN 커밋 → ruff/mypy → `bash verify.sh` → Codeaudit(읽기 전용) → `/codex:adversarial-review --fresh` → PR.
- 변이 정조준: ① `verify_fidelity`가 항상 `missing=()`(항상 허용) ② `check_linkedin`이 `>=` 대신 `>`(경계) ③ `score_candidate`가 None 학력에 기본 10점(추정) ④ `compose_brief_mail`이 CC를 떨어뜨림 ⑤ `load_recipients`가 도메인 검사 생략. 각각 해당 WU 시험이 FAIL해야 한다.
- V1은 표 자체도 공격: "§4에 없는 현실 입력이 있는가?"(예: JD가 이미지 파일, 두 포지션 합본 JD, 일본어 JD).

## 12. 배송 상태·비범위

- HS-13.00~09: `NOT_APPLICABLE`(내부 로직). HS-13.10: `PRODUCTION_VERIFIED`는 readback 일치 시에만, `BUSINESS_USED`는 사장님이 실제 그 메일을 팀에 전달·활용한 뒤에만.
- 비범위: 후보 자동 발송, LinkedIn 로그인·RPS 조작, ChatGPT 브라우저 자동화, 사람인·잡코리아 등록 자동화, Supabase 업로드, Discord.
- 롤백: 코드는 `humansearch/brief/` 패키지 삭제로 원복. 발송된 메일은 회수 불가 → D2 첫 라이브 수신 1명 제한이 영향 반경.
- 배포 후 관측: 브리프 메일 1통당 `verify` exit 0 여부와 LinkedIn 글자 수. 둘 중 하나라도 실패가 2회 반복되면 HS-13.02/03 스펙 재검토.

## 적대 검증 로그

(후기록)
