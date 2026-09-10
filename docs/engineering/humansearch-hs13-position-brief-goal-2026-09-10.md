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
| 8 | RPS 프로젝트·South Korea·Boolean AND/OR 반복 서치 | **부분 채택** | Boolean 검색식 생성은 순수 함수(HS-13.07)로 지금 만든다. RPS 화면 조작은 D0 §4·§5가 D1 이후 허용하는 **프로젝트 확인·필터 순회·후보 목록 넘겨보기**까지만 **HS-13.11로 예정**(선행 HS-05·HS-11.04~06). 지시의 "프로젝트 **생성**"은 사이트 변경(되돌리기·중복 방지 필요)이라 별도 L3 결정·오너 승인 없이는 **비범위** — 사장님이 RPS에서 프로젝트를 만들어 두면 코드는 그 프로젝트 id를 확인만 한다. "멈추지 말고 계속"은 D0 §9(사람 입력·권한 회수)와 2026-09-08 사장님 결정 ⑨(1초 멈춤 장치, `project_humansearch_owner_decisions_20260908`) 아래에서만 가능. |
| 9 | 후보별 1,900자 InMail 준비 + 이메일로도 전달 | **채택** | `build_inmail()` 순수 함수(HS-13.08). 발송은 절대 자동화하지 않는다(D0 §4 "발송은 별도 L3 승인 없이 항상 금지"). 브리프 메일 하단에 후보별 InMail 초안을 붙인다. |

지시 문장 중 코드 계약으로 옮긴 것: ⓐ **"후보자 입장과 관점에서 회사의 매력도가 충실히 드러나야"** → §6 1절 머리에 후보자 관점 소개 2문단 + `[회사 매력 포인트]` 3개 이상(각각 출처 id 필수, `compose_brief_mail(attraction_points=…)` 이 3개 미만·출처 없음이면 거부, D10). ⓑ **"축약해야 한다면 어미·어조·말투 등 빼도 되는 한국어 구조를 빼거나, 프로세스·복리후생 등 부수적인 것을 생략"** → 두 방식 모두 계약화: 절 생략은 `omittable_sections`(호출자가 절 이름 지정), 어미 축약은 `verify_linkedin_fidelity` 가 **핵심 토큰 열**(어미·조사 목록을 뗀 뒤의 토큰 순서)이 같으면 같은 줄로 인정(D11). 명사·숫자·고유명사 삭제는 축약이 아니라 누락.

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
| JD 원문(이미지·PDF) | 러너가 사람이 읽어 옮긴 text + 원본 파일 sha256 | 원본 없음 | — | OCR 불가·저해상도 | — | — | 코드는 이미지를 열지 않는다. `JdSource.provided_by="U1-image"` + `raw_sha256`=원본 파일 해시. 옮긴 text에 `[판독 불가]` 표식이 1개라도 있으면 **거부**(추정 금지) |
| JD 합본(한 문서에 2개 이상 포지션) | 러너가 출처 페이지 경계대로 분리한 text 각각 + `JdSource.position_count=1` | — | 경계 모호 | `position_count≠1` | — | — | **구조화 입력이 판정 근거**: 러너가 관찰한 포지션 수를 `JdSource.position_count` 에 적고, 1 이 아니면 타입이 거부(HS-13.01b). 머리 줄 휴리스틱(`포지션:`·`Position:`·`직무:`·`## ` 제목 2개 이상)은 **경고 필드**(`FidelityReport.multi_position_hint`, 13.02 후속)로만 쓰고 거부 근거로 쓰지 않는다 — 단일 JD 의 `포지션:`+`직무:` 오탐, `## A`/`## B` 미탐이 Codex 2차 실측 반례 |
| JD 언어(영문·일문·혼합) | 그대로 처리 | — | — | — | — | — | 충실도·1,899자·2필드 판정은 언어 무관(줄·코드포인트 단위). 번역본을 만들 때는 **원문과 별개의 JdSource**로 두고 충실도는 원문 기준으로만 판정(번역본은 `provided_by="U1-ko"` 등으로 표시) |
| ClickUp description 공백·요약뿐 | — | 공백만 | 요약 1줄만 | — | — | — | **거부** — 러너는 고객 메일·공고 URL에서 JD 원문을 확보해 `provided_by`에 출처 id를 적는다. ClickUp 요약 문단을 JD로 쓰지 않는다 |
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
    position_count: int = 1   # 러너가 출처 문서에서 관찰한 포지션 수. 정확히 1 만 허용, 0·2 이상 → 거부 (HS-13.01b, §4 합본 행)
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
    search_filters: SearchFilters; created_on: date   # HS-13.01b·13.09c. packet_id 에 날짜를 넣지 않는다(아래 packet.py)
```

```python
# jd_fidelity.py
def content_lines(text: str) -> tuple[str, ...]          # 공백·글머리표·마크다운 기호 정규화 후 빈 줄 제외
@dataclass(frozen=True) class FidelityReport:  missing: tuple[str,...]; extra_condition: tuple[str,...]
    jd_line_count: int; rendered_line_count: int; extra_lines: tuple[str,...]   # ok = not missing and not extra_condition and not extra_lines
    multi_position_hint: tuple[str,...] = ()   # JD 원문에 `포지션:`·`Position:`·`직무:`·`## ` 머리 줄이 2개 이상이면 그 줄들(경고 전용, ok 무관 — HS-13.02c)
def verify_fidelity(jd: JdSource, rendered: str, *, allowed_extra: tuple[str,...] = ()) -> FidelityReport
#   missing = JD 내용 줄 중 rendered 에 없는 줄. extra_lines = rendered 에만 있고 allowed_extra 도 아닌 줄 **전부**(비숫자 "재택근무 가능" 포함).
#   extra_condition = extra_lines 중 연차·학력·연봉 조건 패턴(EXTRA_CONDITION_PATTERNS) 매치 — extra_lines 의 부분집합
def extract_block(text: str, start_marker: str, end_marker: str) -> str   # `[JD 원문 시작]`…`[JD 원문 끝]` 사이만. 마커 부재·중복·역순 → 거부
#   (HS-13.02b, tests/test_hs_1302b.py — 2026-09-10 Codeaudit D-8 편입)
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
def packet_id(position: PositionSpec, jd: JdSource) -> str   # "{clickup_id}-{sha8(jd.raw_sha256)}" — **날짜 없음**(Codex 5차: 날짜가 들어가면 자정 뒤 같은 포지션이
#   새 장부 파일명이 되어 승인 없이 재발송된다). 날짜는 SearchPacket.created_on 메타데이터. 같은 포지션·같은 JD 는 언제 만들어도 같은 id → 같은 묘비
def to_json(packet) / from_json(text)  # 왕복 동일성. PII는 파일에만, 로그 0
# send_ledger.py  (D9 발송 at-most-once — HS-13.09 소유)
class SendState(Enum): INTENT | SENT_UNVERIFIED | VERIFIED | ABANDONED   # ABANDONED 는 종단
@dataclass(frozen=True) class Approval:  approved_by: str; search_query: str; search_checked_at: datetime; reason: str
    packet_id: str; from_attempt: int   # 승인은 패킷·attempt 에 결합. approved_by 는 team-recipients.json 의 주소여야 함. 4개 문자열 공백 금지
@dataclass(frozen=True) class Transition:  at: datetime; state: SendState; evidence: str
@dataclass(frozen=True) class SendIntent:  packet_id: str; channel: str; attempt: int  # 1부터
    recipients_sha256: str; body_sha256: str; recorded_at: datetime; state: SendState
    message_id: str | None; transitions: tuple[Transition, ...]; approval: Approval | None
#   파일 `<packet_id>.<channel>.a<attempt>.sent.json` 은 **영구 묘비** — 이름 변경·삭제·덮어쓰기 없음(추가 전이만 append)
def record_intent(dir, intent) -> tuple[SendIntent, bool]   # attempt 1 을 O_CREAT|O_EXCL 로 생성 → (intent, True). 파일이 하나라도 있으면 (latest, False)
def may_send(dir, packet_id, channel) -> bool                # attempt 파일이 **하나도 없을 때만** True (프리플라이트 전용)
#   **발송 허가 = 같은 프로세스에서 `created is True` 를 받은 그 attempt 뿐.** 파일에서 읽은 INTENT(message_id 없음)는 "불확실 전송"이라 발송 불가
def mark(dir, packet_id, channel, attempt, state, message_id, at, evidence) -> SendIntent   # INTENT→SENT_UNVERIFIED(message_id 필수)→VERIFIED 단방향, transitions append
def open_new_attempt(dir, packet_id, channel, *, approval: Approval, at) -> tuple[SendIntent, bool]
#   최신 attempt 가 INTENT·message_id 없음(불확실)일 때만. **순서: attempt N+1 파일을 O_EXCL 로 먼저 생성 → 그 다음 attempt N 에
#   ABANDONED 전이 append.** 두 작업 사이에 끊기면 "N 은 INTENT, N+1 도 INTENT" 가 남는데, 최신 attempt = 번호 최대이고
#   읽기 시 "N+1 이 있는 N" 은 ABANDONED 로 복구(append)한다 — 어느 지점에서 끊겨도 영구 복구 불능 상태가 없다(Codex 4차 중간).
#   approval.packet_id·from_attempt 가 현재 패킷·최신 attempt 와 다르거나 approved_by 가 수신자 계약 밖이면 거부.
#   SENT_UNVERIFIED·VERIFIED·ABANDONED 에서 호출 → 거부. 사람이 Gmail in:sent 를 확인해 "찾았다" 면 mark(SENT_UNVERIFIED, message_id),
#   "못 찾았다" 면 이 함수(승인 증거 필수)가 유일한 재발송 경로다. 자동 reconcile·released 파일·재발송 자동화는 없다.
# ── D9 가 보장하는 것과 보장하지 않는 것 (Codex 4차 높음 2건에 대한 명시적 한계) ──
#   보장: 코드 경로에서 자동 재발송 0 · 같은 프로세스가 O_EXCL 생성에 성공한 attempt 에 대해서만 발송 · 모든 attempt 가 묘비로 남아 감사 가능.
#   보장하지 않음 ①: **승인 재발송은 사람의 결정이며 at-least-once 다.** Gmail MCP `send_message` 에는 멱등키·결정적 Message-ID 가 없어
#     원 발송 성공을 코드가 증명할 수 없다. 사람이 in:sent 를 잘못 읽으면 중복이 난다 — 그래서 승인 증거 4개+패킷 결합을 요구하고
#     첫 라이브는 수신 1명(D2)으로 반경을 줄인다. 공급자 멱등키가 생기면 이 한계는 없어진다.
#   보장하지 않음 ②: 장부는 러너와 **같은 UID 의 로컬 파일**이다. 파일을 지우면 at-most-once 가 깨진다. **같은 이유로 `Approval` 은 러너가 스스로
#     만들 수 있는 데이터다** — 사람이 아닌 러너가 승인 4필드를 채워 `open_new_attempt` 를 부르면 코드는 구분하지 못한다(Codex 6차). 별도 주체(HS-04.02
#     러너 격리 계정)가 발급하는 승인 영수증 없이는 이 경계를 기계로 세울 수 없다 → 그때까지 승인 재발송은 사장님 세션에서만, 승인 파일은 보고에 첨부. 코드는 삭제·이름변경 함수를
#     갖지 않고(정적 검사) `_latest` 는 중간 attempt 결손을 "변조" 로 판정하지만, 외부 unlink 는 막지 못한다. 러너 격리(HS-04.02, 별도 계정)
#     병합 전까지 D9 는 **LOCAL_ONLY 보증**이며, `created=True` 는 소비되는 capability 가 아니라 발송이 코드 밖(D8)에 있어 생기는 감사 불리언이다.
#     → Issue #82 부채: HS-04.02 선행 뒤 장부를 러너 격리 계정 소유 디렉터리로 옮긴다(기한 = HS-04.02 병합 시).
# __main__.py  (HS-13.10 소유 — 유일한 CLI)
#   uv run --no-sync python -m humansearch.brief verify --packet <path> --sent <readback.txt>
#   stdout 1줄: `VERIFIED packet_id=<id> body_sha256=<hex>` (exit 0) | `SENT_UNVERIFIED packet_id=<id> expected=<hex> actual=<hex>` (exit 1)
#   비교 전 **양쪽 본문에 같은 정규화**(HS-13.10b, 2026-09-10 초안 readback 실측으로 확정): ① CRLF→LF ② Gmail 리다이렉트 언랩
#   `https://www.google.com/url?q=<URL>&source=gmail&ust=<digits>&sa=<alnum>` → unquote(<URL>) (꼬리를 정확히 고정 — 느슨하면 뒤의 `)` 를 삼킨다)
#   ③ 줄 오른쪽 공백 제거 ④ 끝 빈 줄 제거 후 마지막 `packet-id: …` 줄 제거(러너가 §10 ③에서 붙이는 꼬리) ⑤ 전체 strip. 이 규칙 밖의 차이는 전부 불일치
#   인자 누락·파일 없음·패킷 손상 → stderr 사유 + exit 2. 다른 하위 명령 없음(발송 명령 없음).
# types (HS-13.01b 소유 추가)
@dataclass(frozen=True) class SearchFilters:  location: str = "South Korea"; seniority_years: tuple[int, int] | None = None
#   SearchPacket.search_filters: SearchFilters — location 은 brief-policy.json `allowed_search_locations` 안의 값만(D12, HS-13.01c). 러너가 RPS 좌측 필터에 그대로 옮긴다
# policy.py  (P22 — HS-13.01b 소유)
def load_brief_policy(path=contracts/humansearch/brief-policy.json) -> BriefPolicy
#   linkedin_max=1899, subject_prefixes, profile_url_prefixes, team_domain, clickup_position_list_id 를 한 곳에서 소유.
#   types_*.py 의 리터럴은 이 계약값으로 대체(HS-13.01b). 검사기·런타임·시험이 같은 파일을 읽는다
```

### 6. 출력 계약 — 팀 메일 본문 순서 (황금 표본 `1a085e8e789eaf79`에서 도출)

```text
{고객사} {포지션명} | 밸류커넥트 내부 공유
작성·확인 기준일: {YYYY년 M월 D일}
(인사 1문단 + 핵심 1줄)
원문 반영 기준 (글머리표 4줄 이내)
====================================================
1. 일반 Gmail용 | 후보자 전달용        ← 후보자 관점 소개 2문단 + [회사 매력 포인트] ≥3(출처 id) + [JD 원문 시작]…[JD 원문 끝] 블록(verify_fidelity PASS·블록 안 임의 추가 줄 0)
====================================================
2. LinkedIn RPS용 | 공백·줄바꿈 포함 {n}자   ← [복사 시작]…[복사 끝], n ≤ 1,899
====================================================
3. 사람인·잡코리아용 | 2개 필드          ← [필드 1: 회사 소개] / [필드 2: JD 내용]
====================================================
[회사 리서치 | {날짜} 확인]  1.개요·근무지·**인원** 2.매출·영업이익·투자(단계·금액) 3.연혁 4.제품 5.뉴스 6.대표·C레벨(LinkedIn URL) 7.YouTube 8.확인할 항목
[서치 기준]  지역 필터: South Korea(SearchFilters.location, 기본값) / 키워드 / LinkedIn 검색식(boolean_queries 3종) / 초도 인터뷰 질문
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
| D3 | 제목 | 브리프 `[포지션]{고객사}, {포지션명}` / 서치 결과 단독 메일 `[ValuehireSearch][포지션]…`. 브리프에 후보가 포함되면 제목 끝에 ` | ValuehireSearch`를 붙여 라벨 필터 가능하게. `packet-id: <id>` 꼬리 줄의 **단일 소유자는 러너(§10 ③)** — `TeamMail.body`(해시 대상)에는 넣지 않으며 `compose_brief_mail` 은 `packet-id:` 로 시작하는 줄이 본문에 있으면 거부한다. readback 정규화는 마지막 꼬리 1줄만 제거한다(2줄이면 불일치 = 러너 오류로 드러남) | — |
| D4 | 1,899자 계산 | Python `len()`(코드포인트), 개행 포함, `[복사 시작]/[복사 끝]` 제외. LinkedIn 실측(09-09 표본 1,710자 표기)과 ±0 일치를 HS-13.03 라이브에서 1회 확인 | — |
| D5 | JD "100% 정확"의 판정 단위 | **내용 줄**(공백·글머리표·마크다운 기호 정규화 후). 순서 보존은 요구하지 않음. 외부 공고의 연차·학력·연봉 조건 혼입은 FAIL | 순서까지 요구하면 검사 강화 |
| D6 | 점수 4축 | 역할 40·학력 20·안정성 20·프로필 20. 학교 계층은 계약 파일. 성별·나이·사진 0 | 축·가중치는 계약 파일로 이동 가능 |
| D7 | 후보 PII 보관 | git 밖 `~/.humansearch/packets/`, 0700/0600. 저장소·PR·판정에는 packet_id·해시·건수만 | HS-03.01 병합 후 SQLite로 이관(HS-13.09) |
| D8 | 러너 경계 | 리서치(WebSearch)·Gmail 발송·readback은 Claude 세션이 MCP로 수행. 코드는 발송 API를 갖지 않는다 | Python Gmail API 도입은 별도 L3 |
| D10 | 회사 매력도 표현 | Gmail 판 머리 = 후보자 관점 소개 2문단 + `[회사 매력 포인트]` 3~5개, 각 포인트에 CompanyBrief 출처 id. 3개 미만·출처 없음 → 조립 거부 | — |
| D12 | 서치 지역 | `SearchFilters.location` 은 `brief-policy.json` 의 `allowed_search_locations`(초기값 `["South Korea"]`) 안의 값만 허용(타입 거부). 기본값도 계약에서 읽는다. 지역을 넓히는 것은 계약 파일 편집 = 오너 결정(P13 라벨) | 허용 목록 확장 |
| D11 | 어미 축약 인정 기준 | 줄의 **핵심 토큰 열**(공백 분리 토큰에서 목록의 어미·조사·존칭 접미를 뗀 것)이 JD 줄과 같으면 축약으로 인정. 목록은 `linkedin_limit.KOREAN_ENDINGS`(언어 상수, P22 운영 상수 아님). 명사·숫자·영문 토큰 하나라도 빠지면 누락 | 목록 조정 |
| D9 | 발송 at-most-once(코드 경로) | intent 파일은 영구 묘비(attempt 번호). 발송 허가 = 같은 프로세스에서 O_EXCL 생성 `True` 를 받은 attempt 뿐. 파일에서 읽은 INTENT 는 불확실 전송이라 발송 불가. 끊긴 패킷은 사람이 Gmail `in:sent` 를 확인해 찾았으면 `mark(SENT_UNVERIFIED, message_id)`, 못 찾았으면 패킷·attempt 에 결합된 승인 증거(수신자 계약 안의 승인자·검색식·확인 시각·사유)를 가진 `open_new_attempt` 만이 새 attempt 를 연다(N+1 먼저 생성, N 은 ABANDONED). crash-point 4곳 각각 재실행 → 발송 0 이 13.09 AC. **명시된 한계**: 승인 재발송은 사람의 at-least-once 결정(Gmail 멱등키 없음), 장부는 같은 UID 로컬 파일이라 삭제되면 보증이 깨짐(HS-04.02 러너 격리 전까지 LOCAL_ONLY) | 공급자 멱등키·러너 격리 |

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
| 러너가 `linkedin.com` 프로필 페이지를 직접 열어야 하는 상황 | **열지 않는다**(D0 §5 exact-origin 목록 NOT_RUN). 검색엔진 스니펫·논문·기사·회사 페이지만. 그래서 얻지 못한 값은 `None`/빈 튜플로 두고 점수는 0으로 깎인다(추정 금지). 실측 2026-09-10: WebFetch 는 linkedin.com 에서 HTTP 999 |
| **그 외 전부** | **명시적 중단 + 이 표 갱신 후 재개** |

## 9. Issue HS-13 — WU 카드

성공: 실제 포지션 1건의 브리프 메일이 검증된 형식으로 발송·readback 일치. 소유: `humansearch/src/humansearch/brief/`, `humansearch/tests/test_hs_13xx.py`,
`contracts/humansearch/team-recipients.json`, `contracts/humansearch/schools-tier.json`.
선행: 없음(순수 로직). 라이브(13.10)는 D2 수신 규칙과 §8 예외표 아래에서만.
공통 인수 명령 꼬리: `cd humansearch && uv run --no-sync ruff check src tests && uv run --no-sync mypy src tests`.

**검사기의 경계(HS-13.00, Codex 4차 중간 지적에 대한 답):** `acceptance-hs-1300.sh` 는 이 문서가 *구조·결합·실존*(카드 14·ID↔파일명·참조 파일과 브랜치 실존·결정 ID·타입/함수 시그니처·D9 문구)을 갖췄는지만 기계로 판정한다. 양성/음성 서술과 결정 기본값의 **의미 적합성은 정규식으로 판정할 수 없다** — 그것은 Codeaudit(읽기 전용 감사)과 사장님 검토의 몫이며, 이 문서는 그 두 검토를 `## 적대 검증 로그` 에 남긴다. 검사기는 무의미 반복(같은 3자 이상 조각 3회 반복, 같은 단어 반복)만 추가로 거른다.

| WU | 행동 하나 | 인수 명령 (저장소 루트에서 그대로 실행) | 정상 / 반례 | 상태 |
|---|---|---|---|---|
| HS-13.00 | 이 스펙·타입·장부를 저장소에 남긴다 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1300.sh` (exit 0, `CHECKED: 87`) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1300-mutations.sh` (`CHECKED: 30`) | 양성: 이 문서 그대로 → 검사기 exit 0 (CHECKED 87). 음성: 문서 부재·WU 행 삭제·§4 catch-all 삭제·WU 셀 비움·D 셀 비움·토큰만 남긴 최소 문서·catch-all 부정어 반전·가짜 명령 경로·무의미 D값·정상/반례 셀 `x`·**id 접미 위장 파일명·정상/반례 셀을 '없음'으로만 채움·D값을 한글 1자+숫자로·IMPLEMENTED 뒤 괄호로 실존 검사 회피** → 각 exit 1 | IMPLEMENTED |
| HS-13.01 | 타입을 fail-fast로 검증한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1301.py` (`>= 20 passed`) | 양성: 합성 SearchPacket 1건 생성. 음성: Claim 출처 0·후보 URL 도메인·이메일 출처 없음·중복 URL·수신자 타 도메인·1,900자 거부; Hypothesis: `linkedin.com/in/` 아닌 URL 전부 거부 | LOCAL_COMMITTED(task/hs-1301-types-20260910) |
| HS-13.01b | 운영 상수를 계약 파일로 옮긴다(P22) | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1301b.py` (`>= 8 passed`) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1301b-literals.sh` (`CHECKED: 5` — 1899·valueconnect.kr·linkedin.com/in·[포지션]·ClickUp list id 리터럴이 brief/*.py 에 0) | 양성: `contracts/humansearch/brief-policy.json` 로드 → 13.01 시험 전부 유지·`JdSource.position_count` 기본값 1 통과·`SearchFilters` 기본 South Korea. 음성: 파일 없음·version 다름·도메인 형식 위반 → `BriefInputError`; `position_count` 0·2 거부; 계약값을 바꾼 임시 사본으로 1,899→1,000 이 실제 반영 | LOCAL_COMMITTED(task/hs-1301b-policy-20260910) |
| HS-13.02 | JD 충실도를 줄 단위로 판정한다(13.02b: 블록 안 임의 추가 줄 전부 검출) | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1302.py tests/test_hs_1302b.py` (`>= 23 passed`) | 양성: 합성 JD 원문 그대로·`•`↔`-`·공백 차이 → PASS·`extract_block` 정상. 음성: 1줄 삭제·어순 변경·"경력 2년 이상" 추가·**비숫자 "재택근무 가능" 추가 → extra_lines**·마커 부재/중복/역순 거부; 빈 JD 거부 | LOCAL_COMMITTED(task/hs-1302-jd-fidelity-20260910) |
| HS-13.02c | 합본 JD 경고 필드를 더한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1302c.py` (`>= 5 passed`) | 양성: 단일 JD → `multi_position_hint == ()`·`ok` 불변. 음성: `포지션:`+`직무:` 2줄·`## A`/`## B` 를 경고 hint 2줄로 보고하고 `ok` 는 원문 기준 유지(hint 항상 () 변이 검출) | LOCAL_COMMITTED(task/hs-1309c-packet-id-20260910) |
| HS-13.03 | LinkedIn 1,899자 한도와 생략 정책을 강제한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1303.py` (`>= 12 passed`) | 양성: 1,899자 PASS·지정 절(`혜택 및 복지`·`채용 전형`) 생략 PASS·어미 축약 줄("…을 찾습니다"→"…을 찾음") PASS(D11). 음성: 1,900자 FAIL(경계 Hypothesis)·미지정 절 누락 FAIL·명사 1개 삭제 FAIL | PLANNED |
| HS-13.04 | 사람인·잡코리아 2필드로 나눈다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1304.py` (`>= 8 passed`) | 양성: 합성 JD → 필드1·필드2, 필드2 충실도 PASS. 음성: 마커 없음·필드2 빈값 거부 | PLANNED |
| HS-13.05 | 팀 메일 제목·수신자·평문 본문을 조립한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1305.py` (`>= 12 passed`) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1305-pii.sh` (`CHECKED: 4` — git ls-files 텍스트 파일 전체(팀 수신자 계약 파일만 allowlist)에서 ① linkedin.com/in/<slug> 중 slug 가 example- 로 시작하지 않는 것 0 ② 이메일 중 holder@valueconnect.kr·@example.com 외 0 ③ 전화 패턴 0 ④ 한국 휴대폰 010- 0) | 양성: 제목 2형 정확 일치·§6 절 순서·`[회사 매력 포인트]` 3개(출처 id)·수신자 계약 로드·body_sha256 왕복·HTML 0. 음성: 타 도메인 수신자 거부·절 누락 거부·매력 포인트 2개/출처 없음 거부(D10)·PII 게이트 음성 fixture 4종 각 FAIL | PLANNED |
| HS-13.06 | 후보를 순수 함수로 채점한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1306.py` (`>= 15 passed`, Hypothesis 포함) | 양성: 같은 입력 100회 동일·학교 계층 계약(`contracts/humansearch/schools-tier.json`) 로드. 음성: None 학력 = 0(기본값 변이 검출)·축 상한 40/20/20/20 초과 거부·total 0 거부·손상 계약 파일 5종 거부 | PLANNED |
| HS-13.07 | Boolean 검색식 3종을 만든다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1307.py` (`>= 8 passed`) | 양성: 필수어 전부 포함·괄호/따옴표 균형(Hypothesis). 음성: 빈 필수어·따옴표 포함 용어·exclude 중복 거부 | PLANNED |
| HS-13.08 | 후보별 InMail 초안을 만든다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1308.py` (`>= 8 passed`) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1308-nosend.sh` (`CHECKED: 3` — brief/*.py 에 smtplib·requests·send( 0) | 양성: ≤1,899·후보 이름·매칭 이유 1개 포함. 음성: 초과 시 거부·발송 API 부재 | PLANNED |
| HS-13.09 | 패킷·발송 장부를 git 밖에 저장·readback한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1309.py` (`>= 12 passed`) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1309-paths.sh` (`CHECKED: 3` — .gitignore·scan-data-exposure.sh 가 *.packet.json·*.sent.json 차단, ~/.humansearch 경로 리터럴 코드 0) | 양성: 임시 디렉터리 0700/0600·JSON 왕복·D9 a1 INTENT→SENT_UNVERIFIED→VERIFIED·`open_new_attempt` 정상(a1 ABANDONED 전이 append·a2 생성·a1 파일 보존)·O_EXCL 동시 2호출 중 1개만 생성. 음성: 손상 파일 거부·같은 packet_id 재저장 → 파일 1개·역전이·건너뛰기 거부·파일에서 읽은 INTENT 로 재실행 → `record_intent` False·발송 0·approval 공백 거부·SENT_UNVERIFIED/VERIFIED/ABANDONED 에서 open_new_attempt 거부·crash-point 4곳 재실행 발송 0·묘비 파일 이름 변경/삭제 함수 부재(정적) | PLANNED |
| HS-13.09c | packet_id 에서 날짜를 뺀다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1309c.py` (`>= 6 passed`) | 양성: 같은 포지션·JD 는 날짜가 달라도 같은 id·`created_on` JSON 왕복. 음성: 옛 형식 `20260910-…` 거부·날짜 A 에 intent 뒤 날짜 B 재실행 → `may_send` False·created False(발송 0, 날짜 재삽입 변이 검출) | LOCAL_COMMITTED(task/hs-1309c-packet-id-20260910) |
| HS-13.10b | readback 정규화 5단계를 고정한다 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1310b.py` (`>= 6 passed`) | 양성: Gmail 리다이렉트 1개·여러 개·괄호 안 URL 복원, 퍼센트 인코딩 URL 이 `%` 유지/`%25` 재인코딩 두 변형 모두 일치(양쪽 대칭 unquote). 음성: 느슨한 꼬리가 `)` 를 삼키는 반례·다른 URL 은 exit 1(언랩 생략 변이 검출) | LOCAL_COMMITTED(task/hs-1309c-packet-id-20260910) |
| HS-13.01c | 서치 지역을 계약 허용 목록으로 고정한다(D12) | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1301c.py` (`>= 5 passed`) | 양성: `South Korea` 통과·계약 기본값 로드. 음성: `Japan` 거부·빈값 거부·계약 목록을 바꾼 임시 정책으로 허용값이 실제 반영(허용 검사 생략 변이 검출) | PLANNED |
| HS-13.10 | 실제 포지션 1건 라이브 | §10 절차 + `cd humansearch && uv run --no-sync python -m humansearch.brief verify --packet <path> --sent <readback.txt>` (exit 0, 출력 `VERIFIED packet_id=… body_sha256=…`) | 양성: 발송 1·readback 해시 일치 1. 음성: 불일치 → exit 1 `SENT_UNVERIFIED`; 같은 패킷 재실행 → 발송 0 | PLANNED |
| HS-13.11 | RPS 프로젝트 확인·필터 순회·후보 목록 읽기(D0 §4 허용 범위만) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-1311-rps-readonly.sh` (`CHECKED: 4` — 프로젝트 id readback 1·필터 적용 readback 1·캡차/2FA fixture 즉시 STOP 1·발송·저장 호출 0 정적 1) | 양성: 사장님이 만든 프로젝트 1개 확인 → 후보 목록 1페이지 읽기. 음성: 없는 프로젝트 → 순회 0·프로젝트 생성 호출 0 | BLOCKED(선행 HS-05·HS-11.04~06 병합) |
| HS-13.12 | 패킷 → SQLite 이관 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_1312.py` (`>= 8 passed`) | 양성: 패킷 1건 → `search_packets`·`candidate_leads` 행 → 재조회 왕복 동일. 음성: 같은 packet_id 2회 → 1행·손상 패킷 거부·PII 열이 암호화 경계(HS-03.03) 밖에 평문 0 | BLOCKED(선행 HS-03.01 병합) |

→ 00 → 01 → (01b, 02, 06, 07 병렬) → 03 → 04 → 05 → 08 → 09 → 10. 11·12는 선행 병합 뒤. 카드 수 = 18(00~12 + 01b·01c·02c·09c·10b).
각 WU = 워크트리 1개 = PR 1개. 선행 PR 미병합이면 그 브랜치를 base로 잡고 PR 본문에 SHA를 적는다.

## 10. HS-13.10 러너 절차 (R3 — 손 조작은 러너, 판단은 코드)

1. ClickUp 포지션 1건 선택(D1 목록에서 사장님 지시 또는 최상위) → JD 원문 확보(ClickUp description 또는 고객 메일) → `JdSource`.
2. WebSearch로 회사 사실 수집. 모든 값에 출처 id. 미확인은 `None`.
3. 공개 LinkedIn 프로필 검색(WebSearch, `site:linkedin.com/in`) → 후보 3~5명. 구조화 `CandidateEvidence` 추출.
4. 코드: `verify_fidelity`·`check_linkedin`·`split_two_field`·`score_candidate`·`build_boolean_queries`·`build_inmail`·`compose_brief_mail` → 패킷 저장.
5. 러너(D9 순서 고정): ① `record_intent` 가 `(…, False)` 면 **아무것도 보내지 않고** 상태를 보고(INTENT·message_id 없음이면 Gmail `in:sent` 에서 제목+`packet_id` 토큰을 사람 눈으로 확인 → 찾았으면 `mark(SENT_UNVERIFIED, message_id)`, 못 찾았으면 사장님 승인 증거를 받아 `open_new_attempt`; 그 외 상태는 종료) → ② `record_intent`/`open_new_attempt` 가 **이 프로세스에서** `(…, True)` 를 돌려준 attempt 에 대해서만 ③ `send_message`(subject·to·body 를 패킷에서 그대로, 본문 끝에 `packet_id` 토큰 1줄) → 즉시 `mark(SENT_UNVERIFIED, message_id)` → ④ `get_thread(PLAIN_TEXT)` 로 readback → `verify --sent` 해시 일치만 `mark(VERIFIED)` = `PRODUCTION_VERIFIED`. 불일치는 `SENT_UNVERIFIED` 유지·보고. 어느 지점에서 끊겨도 재실행은 ①에서 멈춘다(발송 0).
6. 보고: packet_id·해시·수신자 수·후보 수·글자 수만. 이름·URL·이메일은 보고에 0.

## 11. 게이트 계획·적대검증 정조준

- 게이트: 각 WU RED 커밋 → GREEN 커밋 → ruff/mypy → `bash verify.sh` → Codeaudit(읽기 전용) → `/codex:adversarial-review --fresh` → PR.
- 변이 정조준: ① `verify_fidelity`가 항상 `missing=()`(항상 허용) ② `check_linkedin`이 `>=` 대신 `>`(경계) ③ `score_candidate`가 None 학력에 기본 10점(추정) ④ `compose_brief_mail`이 CC를 떨어뜨림 ⑤ `load_recipients`가 도메인 검사 생략. 각각 해당 WU 시험이 FAIL해야 한다.
- V1은 표 자체도 공격: "§4에 없는 현실 입력이 있는가?"(예: JD가 이미지 파일, 두 포지션 합본 JD, 일본어 JD) — 2026-09-10 Codex V1 지적으로 §4에 4행 편입.
- PII 게이트(HS-13.05 `acceptance-hs-1305-pii.sh`) 범위: **`git ls-files` 의 모든 텍스트 파일**(`humansearch/src/`·`contracts/`·`docs/`·`scripts/`·`tests/` 포함) 에서 LinkedIn 프로필 slug 는 `example-` 접두만, 이메일은 `holder@valueconnect.kr`·`@example.com`·팀 수신자 계약 파일(`contracts/humansearch/team-recipients.json`)의 4개 주소만, 전화 패턴 0. 음성 fixture 는 `humansearch/src/`·`contracts/` 에 실제형 URL·이메일을 주입한 사본에서 FAIL 해야 한다. **사람 이름은 정규식으로 잡을 수 없다** — 이름은 리뷰어 육안 + 후보 데이터가 저장소 파일에 들어갈 경로 자체를 만들지 않는 구조(D7)로 막는다고 정직하게 적는다.
- P22: 채널 한도·제목 접두·허용 URL 접두·팀 도메인·ClickUp 목록 id 는 `contracts/humansearch/brief-policy.json` 한 곳(HS-13.01b). 13.01이 먼저 리터럴로 구현됐으므로 01b 가 리터럴 0건 검사(`acceptance-hs-1301b-literals.sh`)로 회수한다.

## 12. 배송 상태·비범위

- HS-13.00~09: `NOT_APPLICABLE`(내부 로직). HS-13.10: `PRODUCTION_VERIFIED`는 readback 일치 시에만, `BUSINESS_USED`는 사장님이 실제 그 메일을 팀에 전달·활용한 뒤에만.
- 비범위: 후보 자동 발송, LinkedIn 로그인·RPS 조작, ChatGPT 브라우저 자동화, 사람인·잡코리아 등록 자동화, Supabase 업로드, Discord.
- 롤백: 코드는 `humansearch/brief/` 패키지 삭제로 원복. 발송된 메일은 회수 불가 → D2 첫 라이브 수신 1명 제한이 영향 반경.
- 배포 후 관측: 브리프 메일 1통당 `verify` exit 0 여부와 LinkedIn 글자 수. 둘 중 하나라도 실패가 2회 반복되면 HS-13.02/03 스펙 재검토.

## 적대 검증 로그

### 2026-09-10 Codex V1 (adversarial-review, fresh·read-only, job `review-mtuuqi93-ou251w`, 커밋 7efd6c6 대상)

`VERDICT: FAIL` — 높음 4·중간 4. 처분(같은 PR 에서 수정):
- [높음] 검사기가 빈 셀·토큰만 남긴 문서를 통과 → 검사기에 의미 검사(WU 5셀 비어있지 않음·명령 형식·상태값, D 기본값 셀 ≥10자, 타입 토큰은 코드 펜스 안) 추가, 자기 변이 ⓓ WU 셀 비움·ⓔ D 셀 비움·ⓕ 최소 문서 3종 편입(`CHECKED: 7`).
- [높음] WU 명령이 루트에서 실행 불가(`tests/` 상대경로·래퍼 경로) → §9 전 행을 `cd humansearch && …`·`bash scripts/verify/run-acceptance.sh …` 전체 명령·기대 출력·최소 건수·양성/음성으로 재작성. 13.11·12 에도 인수 명령 부여, 카드 수 14 로 정정.
- [높음] RPS "프로젝트 생성" 이 D0 §4·§5 범위 초과 → §2 8행·§9 13.11 을 허용 범위(확인·필터·목록 읽기)로 축소, 생성은 별도 L3.
- [높음] 발송 재시도 중복 → D9·`send_ledger.py`(write-ahead intent·유일키·발송 전 sent 검색·단방향 상태) 신설, §10 5단계 순서 고정, HS-13.09 AC 편입.
- [중간] §4 밖 현실 입력 → 이미지·합본·다국어·ClickUp 공백 4행 추가.
- [중간] PII 게이트가 이름·URL 미검사 → §11 범위 확장(slug `example-`·이메일 placeholder·전화 0), 이름은 정규식 불가를 명시.
- [중간] P22 리터럴 → HS-13.01b 신설(`brief-policy.json` + 리터럴 0건 검사).
- [중간] `verification-commands.md` 스텝 수 27→28·PostgreSQL 준비 행 누락·래퍼 명령 누락 → 표 재생성.
Codex 샌드박스는 mktemp 불가라 파일 사본 변이는 NOT_RUN, 인메모리 변이 3종으로 재현함(memory: codex 샌드박스 mktemp 차단).

### 2026-09-10 Codex V1 2차 (job `review-mtuvgnje-2xmdoe`, 6889553 대상)

`VERDICT: FAIL` — 높음 2·중간 3. 처분(같은 PR):
- [높음] 가짜 명령 경로·전부 PLANNED·무의미 D값(`1234567890`)·정상/반례 `x` 가 CHECKED 66 통과 → 검사기에 **WU id↔명령 파일명 결합**(`test_hs_<id>.py`·`acceptance-hs-<id>-*.sh`), PLANNED/BLOCKED 이 아닌 상태는 참조 파일 실존, 행동 셀 6자 이상, 정상/반례 셀에 `양성`·`음성` 둘 다, D 기본값에 한글 1자 이상·서로 다른 문자 3종 이상, 전 행 PLANNED 금지 추가(CHECKED 70) + 자기 변이 ⓗ 가짜 경로·ⓘ 숫자 D값·ⓙ `x` 셀(CHECKED 11).
- [높음] D9 `may_send` 가 INTENT 에서 True 인 문장과 13.09 AC 가 상충 → at-most-once 로 단일화: intent 파일 부재일 때만 발송, O_EXCL 원자 생성, 끊긴 패킷은 사람 확인 후 `reconcile` 로만, crash-point 4곳 AC. 13.09 구현자에게 동일 계약 전달.
- [중간] 합본 머리 줄 휴리스틱 오탐·미탐 → `JdSource.position_count`(구조화 입력, 13.01b) 가 판정, 휴리스틱은 경고 필드.
- [중간] PII 게이트 범위가 `humansearch/src/`·`contracts/` 제외 → `git ls-files` 전체 텍스트 파일로 확장.
- [중간] registry 에 mutations 미등재·표 건수 55/7 → mutations 항목 등재, 표 70/11 로 동기화. "CI 의 모든 run-acceptance 대상이 registry 에 정확히 1회" completeness 검사는 **부채**로 남긴다(Issue #82 코멘트, 기한 2026-09-24).

### 2026-09-10 Codex V1 3차 (job `review-mtuw6gqt-53uaag`, 06e3d40 대상)

`VERDICT: FAIL` — 병합 차단 4건. 처분(같은 PR):
- [높음] 검사기 우회 4종(`tests/test_hs_1305_zzz.py`·`양성:없음 음성:없음`·`가123456789`·`IMPLEMENTED(x)`) 통과 → 정확 파일명 결합(`tests/test_hs_13<id>.py` 글자 그대로), 양성/음성 뒤 `없음·N/A·해당없음·-·x` 거부 + 각 10자 이상, D값 한글 단어(2음절+) 2개 이상, 괄호는 `LOCAL_COMMITTED(task/…)` 만 허용·그 외 상태는 괄호 무관 파일 실존. 변이 ⓚⓛⓜⓝ 편입(CHECKED 15).
- [높음] `reconcile(sent_found=False)` 가 재발송을 다시 염 → 폐기. intent 파일 = 영구 묘비(attempt 번호), 발송 허가 = 같은 프로세스 O_EXCL True 뿐, 재발송은 승인 증거 4개를 가진 `open_new_attempt` 로 새 attempt(이전 attempt ABANDONED 전이). 13.09 구현자에게 최종 계약 전달.
- [높음] 13.02b(`extra_lines`·`extract_block`)가 §5·WU 표에 없음 → §5 `FidelityReport`·`verify_fidelity`·`extract_block` 계약 명시, 13.02 행에 `test_hs_1302b.py` 편입.
- [중간] `JdSource.position_count` 가 §5 타입에 없음 → 필드 명시, 13.01b AC 에 0·2 거부 편입.

### 2026-09-10 Codex V1 4차 (job `review-mtuwqskx-itm154`, 82b7eb4 대상)

`VERDICT: FAIL` — 높음 4·중간 2. 처분:
- [높음] `tests/test_hs_1305.py.bak`·`LOCAL_COMMITTED(task/fake-branch)` 통과 → 토큰 경계(`.py` 뒤는 공백·백틱·끝만)·`git show-ref` 브랜치 실존·`git cat-file -e <ref>:humansearch/<path>` 파일 실존 검사 추가, 변이 ⓞⓟ.
- [높음] 13.02b·position_count 토큰 미게이트 → 검사기에 `position_count: int`·`extra_lines: tuple`·`def extract_block`·13.02 행의 `tests/test_hs_1302b.py` 정확 참조 추가, 변이 ⓠⓡ(각각 삭제 → exit 1).
- [높음] 승인 재발송이 불확실 전송에서 중복 허용 → **고칠 수 없는 한계로 명시**(Gmail MCP 멱등키 없음). Approval 을 packet_id·from_attempt·수신자 계약 승인자에 결합, 첫 라이브 수신 1명으로 반경 축소. D9 를 "코드 경로 at-most-once + 사람 승인 재발송은 at-least-once" 로 정직하게 재기술.
- [높음] 같은 UID 로컬 파일 삭제로 우회 → **명시된 한계·부채**: HS-04.02 러너 격리 전까지 LOCAL_ONLY 보증, `created=True` 는 capability 가 아니라 감사 불리언(발송이 코드 밖 D8). Issue #82 부채 행.
- [중간] 무의미 반복 텍스트 → 3자 조각 3회 반복·같은 한글 단어 반복 거부(변이 ⓢⓣ) + **검사기 경계 문단**(§9 머리) 신설: 의미 적합성은 Codeaudit·사장님 검토.
- [중간] open_new_attempt 내부 crash → 순서를 "N+1 먼저 생성 → N ABANDONED" 로 고정하고 읽기 시 복구 규칙 명시(13.09 구현은 이미 이 순서).

### 2026-09-10 Codex V1 5차 (job `review-mtuxjipq`, 63b8ac3 대상, 판정 규칙: 명시된 한계 3종 제외)

`VERDICT: FAIL` — 높음 5·중간 1. 처분:
- [높음] `true # cd humansearch && …python -m humansearch.brief` 로 결합 통과 → 명령 셀은 백틱 안 전체 명령을 ID 별 문법으로 고정(제어 연산자 `#`·`;`·`|`·`||`·`&` 거부, `&&` 는 `cd humansearch &&` 뒤 1회만), CLI 는 HS-13.10 행에만 허용, 그 외 행은 결합 파일 1개 이상 추출 필수. 변이 ⓤⓥ.
- [높음] `O_CREAT\|O_EXCL` BRE 교대로 하나만 있어도 통과 → 두 문자열을 각각 `grep -F` 로. 변이 ⓦ(O_EXCL 삭제).
- [높음] packet_id 에 날짜 → 자정 뒤 승인 없는 재발송. **코드 결함 인정** → HS-13.09c: `packet_id = clickup_id-sha8`(날짜 제거), `created_on` 메타데이터, 날짜 A 발송 후 날짜 B 재실행 발송 0 AC.
- [높음] `packet-id` 꼬리가 해시를 깨뜨림 → 초안(draft) readback 실측으로 확정한 정규화 5단계(Gmail 리다이렉트 언랩 포함)를 §5 CLI 계약에 명시(HS-13.10b). 실측: 언랩 후 초안 본문 = 패킷 본문(해시 일치).
- [높음] `SearchPacket.search_filters`·`FidelityReport.multi_position_hint` 가 타입 정의에 없음 → §5 정의에 편입, 검사기 토큰·변이 ⓧ.
- [중간] D10·D11 내용 미검사 → D 내용 검사를 D1~D11 로, 변이 ⓨ.

### 2026-09-10 Codex V1 6차 (job `review-mtuxrf`, e0ec67f 대상, 한계 3종 제외 규칙)

`VERDICT: FAIL` — 높음 4·중간 1. 처분:
- [높음] 미분류 백틱 조각 무시·셀 전체 ID 미끼·백틱 밖 `; true` → 모든 백틱 조각을 명령/기대출력 문법으로 분류(그 외 거부), ID 결합은 검증된 명령의 인자에서만, 백틱 밖 `#;|&` 거부. 변이 3종.
- [높음] 러너가 Approval 을 위조 가능 → **명시된 한계 ②의 확장으로 기록**(같은 UID·같은 세션에서는 승인자와 러너를 코드가 구분할 수 없다). HS-04.02 전까지 승인 재발송은 사장님 세션에서만, 승인 파일을 보고에 첨부. 별도 주체 영수증은 HS-04.02 이후 부채.
- [높음] packet-id 꼬리 이중 소유 → D3 정정: 소유자는 러너 1곳, compose 는 `packet-id:` 줄 거부. 퍼센트 인코딩(`%7E`↔`~`)은 13.10b 가 양쪽 대칭 unquote 로 이미 처리(시험 2건).
- [높음] 새 불변식이 WU 카드에 없음 → HS-13.02c·09c·10b 카드(실제 시험 파일·LOCAL_COMMITTED 브랜치)·HS-13.01c 카드 추가, 카드 18.
- [중간] South Korea 가 기본값일 뿐 → D12: 계약 허용 목록(`allowed_search_locations`)으로 고정, HS-13.01c.

### 2026-09-10 Claude Codeaudit (읽기 전용·별도 컨텍스트, 7efd6c6 대상)

`VERDICT: PARTIAL` — 높음 3·중간 10·낮음 7. Codex V1 과 겹치는 D-1·D-4·D-5·D-6·D-10·D-11·D-13 은 위 처분으로 해소. 추가 처분:
- [높음 D-2] catch-all 부정어 반전("명시적 거부 안 함") 통과 → 검사기에 부정어 금지 검사·자기 변이 ⓖ 편입.
- [높음 D-3] 지시 "후보자 관점 매력도"·"어미 축약" 누락/대체 → D10·D11 신설, §2·§6·13.03·13.05 반영.
- [중간 D-7] CLI 계약 없음 → §5 `__main__.py` 인자·출력·exit 계약. [중간 D-8] 비숫자 임의 추가 미검출 → 13.02b `extra_lines`·`extract_block`. [중간 D-9] South Korea → `SearchFilters`. [중간 D-12] 러너 linkedin.com 열람 금지 → §8 행.
- [낮음 D-14·15·16] 인용·경로·인원 정정. [낮음 D-19] mechanism-registry 등재. [낮음 D-18] PR 라벨 `weakens-check` 는 사람이 붙인다(기계 강제 없음 — 선행 공백). [낮음 D-17] 고객사 실명은 공개 기업명이라 유지, 후보자 PII 는 0.
