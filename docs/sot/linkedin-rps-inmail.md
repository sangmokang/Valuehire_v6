# LinkedIn RPS InMail 본문 정본

최종 확인: 2026-09-22(오후 개정 — 골든 샘플 역산). 적용 대상: LinkedIn Recruiter(RPS)에서 후보자에게 보낼 InMail 템플릿의 **본문 작성과 저장**.

## 결론과 완료 기준

RPS는 공고판이 아니라 사람과 사람이 연결되는 자리다. 그렇다고 조건을 산문에 녹여 묻으면 후보자가 읽어내지 못한다. 본문은 **`■ 섹션` + `• 불릿` + `**볼드**` 로 된 짧은 제안서**여야 한다. 원문의 조건은 하나도 바꾸지 않은 채, 30초 안에 조건이 눈에 들어오면 완료다. 저장 후 다시 불러와 확인했을 때만 등록 완료로 본다.

**2026-09-22 오전 판정 정정.** 이 문서의 L4·L5는 "불릿 없이 이어지는 글"을 요구했고, 그 규칙으로 만든 검사기가 사장님이 실제로 쓰시는 원고 2건(`outputs/_golden/`)을 **둘 다 불합격**시켰다. 골든 실측은 불릿 비율 0.444 / 0.462, 볼드 12쌍 / 7쌍, 섹션 5개 / 5개다. 규칙이 틀렸으므로 아래 G1~G12로 갈아끼운다.

발송(Send)은 이 문서의 범위가 아니다. 템플릿 저장까지만 한다.

## 1. 사장님 지시 (2026-09-22)

| # | 지시 | 기계 검사 |
|---|---|---|
| L1 | **1,900자 이내.** 제목 + 빈 줄 + 본문 합계. 실무 hard cap은 1,899자 | `measure.compose()` + `over_limit()` |
| L2 | **축약해도 핵심은 건드리지 않는다.** 필수/우대, 대체 인정 조건, 고용형태, 전형, 수습은 그대로 남긴다 | 핵심 조건 존재 검사 |
| L3 | **JD를 과도하게 변형하지 않는다.** 원문에 없는 보상·직급·조건을 만들지 않고, 있는 조건을 강화·약화하지 않는다 | `checks.scan()` + 원문 대조 |
| L4 | **인사 → 회사 → `■ Position` → Mission → 조건 → Process → 클로징** 순서를 지킨다. 조건은 불릿으로 보여 준다 | `checks.inmail_structure()` |
| L5 | **AI 티는 서식이 아니라 문구에서 난다.** 상투적 권유, 과장 홍보, 이모지, 원시 변수, 후보자 이름 박기를 쓰지 않는다. 볼드·`■`·`•`는 정상 서식이다 | `checks.scan_inmail()` |
| L6 | **봇 탐지에 걸리지 않게 한다.** 사람이 쓰는 속도로 조작하고, 한 포지션당 최소 60초, 25건마다 5분 휴식, 하루 30건을 넘기지 않는다 | `linkedin-rps-jd-set-builder` §16 준수 |

## 2. 골든에서 역산한 작성 규칙 G1~G12

정본 골든: `outputs/_golden/rps_wrtn_golden.txt`, `outputs/_golden/rps_bunjang_golden.txt`.
검사기: `scripts/jd_channels/checks.py` 의 `scan_inmail()`(금지 문구) + `inmail_structure()`(뼈대).
인수 시험: `bash scripts/acceptance-rps-inmail.sh` — 종료값 0이 합격, 0이 아니면 불합격.

| # | 규칙 | 기계 검사 |
|---|---|---|
| G1 | 섹션 헤더는 `■ ` 로 시작하고 5개 내외. `■ Position | {포지션명}` 줄은 반드시 있다 | `INMAIL_NO_SECTION`, `INMAIL_NO_POSITION_HEADER` |
| G2 | 불릿은 `• ` 를 쓴다. 골든 실측 비율 0.44~0.46, 최소 8개 | `INMAIL_NO_BULLET` |
| G3 | `**볼드**` 를 숫자·핵심 역량·포지션명에 건다. 골든 7~12쌍, 최소 5쌍 | `INMAIL_NO_BOLD` |
| G4 | 영문 업계 용어를 한글로 풀지 않는다 — KPI/Metric, SQL/Query, BI/Data Governance, FinOps, DW/BI, Audit Trail, Cross-functional, MVP, OKR, Reference Check, Offer, Culture Fit | `INMAIL_TERM_TRANSLATED` |
| G5 | 호칭은 "테크 전문 서치펌 밸류커넥트의 헤드헌터 강상모". "전문"·"헤드헌터"를 빼지 않는다 | `INMAIL_SIGNATURE` |
| G6 | 회사 소개는 2~4문장으로 압축한다. 불릿으로 늘어놓지 않는다 | intro 블록 렌더 |
| G7 | 네거티브 지표(영업손실·인원수)를 본문에서 뺀다. 매출·성장·투자·사용자 규모만 남긴다 | `INMAIL_NEGATIVE_METRIC` |
| G8 | `**Mission**` 블록에 역할의 본질과 "이 포지션이 무엇과 다른지"를 쓴다 | mission 블록 렌더 |
| G9 | 원문 Note(평가 우선순위)는 `※` 한 줄로 보존한다 | `pipeline.verify()` 평가 우선순위 검사 |
| G10 | 클로징은 "LinkedIn 수락 또는 간단한 회신". 이력서 요구를 앞세우지 않는다 | `INMAIL_CLOSING` |
| G11 | 소프트 터치 문장은 클로징 직전에 둔다 | `inmail.SOFT_TOUCH` |
| G12 | 길이 1,000~1,600자가 정상. 1,899자는 상한이지 목표가 아니다 | `INMAIL_TOO_LONG`, `measure.over_limit()` |

### 2.1 뼈대

`scripts/jd_channels/inmail.py` 가 뼈대를, 단위 정의(`outputs/_units/*.json`)가 문장을 담당한다.
골든 두 건을 하드코딩으로 재현할 수 없고, `rps_*` 필드가 하나도 없는 제3의 JD 를 넣어도 같은 뼈대가 나온다(인수 시험 CAC-1).

```
{인사}
현재 **{회사}** {포지션} 포지션을 제안드립니다.
{회사 압축 2~4문장}
■ Position | {포지션명}
**Mission** / {역할의 본질}
■ Key Responsibilities / • ...
■ Requirements (또는 Looking for) / • ...
■ Preferred / • ...
※ {평가 우선순위}
■ Process / {전형 한 줄} + {고용형태·수습·근무지}
※ {부가 안내}
{소프트 터치}
{클로징}
```

### 2.2 단위 정의의 RPS 필드

| 필드 | 뜻 |
|---|---|
| `rps` | RPS 본문에 실을 표현. 영문 용어와 `**볼드**` 를 보존한다. 없으면 `compact` 를 쓴다 |
| `rps_drop` | RPS 본문에서 뺀다. **`core` 에는 쓸 수 없다** — core 삭제 금지는 채널이 달라도 같다 |
| `rps_block` | 기본 블록을 덮어쓴다(`intro`/`mission`/`responsibilities`/`requirements`/`preferred`/`note`/`process`/`conditions`/`footnote`) |
| `rps_order` | 같은 블록 안에서의 순서. 0 이면 원문 순서 |
| `rps_labels`(문서 최상위) | 섹션 제목 치환. 예: `{"requirements": "Looking for"}` |

### 2.3 긴 JD 압축 기준

원문의 축과 Note는 **이름을 유지한 채** 한 줄로 접는다. 접어도 사라지면 안 되는 것:
필수/우대 구분, 연차, 대체 인정 조건, 고용형태, 수습, 전형 단계, Note의 평가 우선순위.
문자열을 잘라내지 않는다 — 줄이는 수단은 `rps` 압축 표현과 비-core 단위 생략 둘뿐이다.

## 3. 후보자 이름을 본문에 박지 않는다

템플릿에 특정 후보자 이름이 들어가면 다음 사람에게 그 이름이 그대로 나간다.
2026-09-22 실측에서 기존 저장본이 `안녕하세요 전혜인 매니저님`으로 시작하고 있었다.
이름을 모르면 자리표시자를 남기지 말고 `안녕하세요.`로 시작한다.
`{{first_name}}` 같은 원시 변수도 direct composer에서 깨지므로 쓰지 않는다.

## 4. 회사 브리핑 7요소

`linkedin-rps-jd-set-builder` R20을 그대로 따른다 — 회사명·연혁·대표·투자 단계·매출·인원·주요 뉴스.
매출과 영업손익을 구분하고, 실적과 전망을 구분한다. 출처가 갈리는 수치는 기준을 짧게 붙인다(예: 인원 179명(원티드 기준)).

## 5. 저장 절차와 검증

1. 같은 제목·템플릿명을 먼저 검색한다. **내 소유**이면 Update current, 없거나 **타인 소유**면 Save as new 로 제목을 달리해 만든다.
2. 템플릿 선택은 `[role=option]` 행으로만 한다. 본문을 잘못 클릭하면 `Replace content?` 모달이 뜬다.
3. visibility는 `Anyone in my organization`을 명시 선택하고 `checked`를 확인한다. 기본값을 믿지 않는다.
4. 저장 전에 제목+본문 길이, 금지 패턴 0건, 원시 변수 0개, 이모지 0개, 회사 직접지원 경로 0건을 확인한다.
5. 저장 후 **템플릿을 다시 검색해 Updated 날짜가 오늘로 바뀌었는지** 확인한다. 성공 알림만으로 완료하지 않는다.
6. 저장이 끝나면 composer를 닫는다. 열어두면 오발송 위험이 남는다.

## 6. 이번 실행 근거

2026-09-22 오전: 산문 8문단·불릿 0개 판을 Update current로 저장했다. **골든 기준 불합격이다**
(`inmail_structure` 가 `INMAIL_NO_SECTION`·`INMAIL_NO_BULLET`·`INMAIL_NO_BOLD`·`INMAIL_NO_POSITION_HEADER` 를 띄운다).

2026-09-22 오후: 골든 역산으로 로직을 다시 세웠다. 생성 원고 실측은 아래와 같다.

| JD | 섹션 | 불릿 | 볼드 | 본문 | 제목+본문 |
|---|---|---|---|---|---|
| 뤼튼 Finance Data Analyst (FP&A) | 5 | 11 | 25쌍 | 1,545자 | 1,598자 |
| 번개장터 Product Manager (Core Product) | 5 | 10 | 18쌍 | 1,592자 | 1,643자 |

같은 이름의 `ver1.0` 템플릿이 다른 소유자(Sanghyuk Lee) 앞으로 따로 있다. 타인 소유 템플릿은
수정하지 않는다. 당시에는 제목을 달리해 ver2를 신규 저장했지만, 이후 작업은 기존 ver2를 먼저 조회하며 같은 이름으로 추가 생성하지 않는다.
2026-09-22 실행 결과: `[제안]뤼튼, Finance Data Analyst (FP&A) ver2.0` 신규 저장(섹션 5·불릿 11·볼드 30·1,497자,
`Anyone in my organization` checked / `Only me` unchecked, Send 미클릭). ver1.0 은 건드리지 않았다.

## 7. 컴포저는 Quill 리치텍스트다 — 마크다운을 그대로 넣지 않는다

RPS 컴포저 본문은 `div.ql-editor[aria-label="Compose a message"]`(Quill)다. 2026-09-22 실측:

| 넣은 것 | 결과 |
|---|---|
| `**볼드**` 원문 그대로 | 별표가 후보자에게 그대로 보인다 |
| `<strong>` | 정상 — 실제 볼드로 저장된다 |
| `<ul><li>` | **Quill 이 지운다.** 불릿 0개, 본문 1,445자 → 1,073자로 손실 |
| `<p>• ...</p>` | 정상 — 골든 원문과 같은 문자 불릿 |

변환기는 `scripts/jd_channels/richtext.py` 의 `to_html()` 이다. 입력 전
`<ul>` 이 0개인지, 붙여넣은 뒤 `innerText` 길이·불릿 수·볼드 수를 다시 세어 확인한다.

## 7. RPS 컴포저 입력 형식 (2026-09-22 실측)

RPS 컴포저는 Quill 에디터다. 마크다운을 해석하지 않으므로 `**볼드**` 를 그대로 넣으면
후보자에게 별표가 그대로 보인다. `scripts/jd_channels/richtext.py` 의 `to_html()` 로
`<strong>` 과 `<p>` 로 옮겨 넣는다.

| 표기 | 컴포저 처리 | 대응 |
|---|---|---|
| `**볼드**` | 별표가 그대로 보임 | `<strong>` 으로 변환 |
| `<ul><li>` | **통째로 삭제됨** (본문 1,445자 → 1,073자, 불릿 11개 유실) | `<p>• 텍스트</p>` 로 문자 불릿 사용 |
| `■` / `•` / `※` | 그대로 들어감 | 변환 없음 |

입력 절차: `.ql-editor[aria-label="Compose a message"]` 에 innerHTML 을 넣고
`input` 이벤트를 보낸다. 제목은 `input[aria-label="Message subject"]` 에
네이티브 setter 로 넣고 `input`·`change` 를 보낸다. 저장 전 본문 길이·볼드 수·불릿 수·
섹션 수·별표 0개를 DOM 으로 센다.

타인 소유 템플릿은 수정하지 않는다. 저장이 승인된 경우에도 회사·직무·소유자·기존 본문을 먼저 확인하고 같은 대상은 갱신한다. 신규 생성은 기존 대상이 없을 때만 한다. 저장 후 목록 노출이나 성공 알림은 완료 증거가 아니며, 새로 연 본문을 저장 전 원문과 대조해야 한다.

2026-09-22 후속 조회: Settings → Message templates → Shared의 View로 동일 이름 ver2.0 두 행을 각각 열었다. 두 본문 모두 `outputs/run-20260922/rps_inmail_wrtn.txt`와 일치했다. 허용 정규화는 짝지어진 볼드 표식 제거, CRLF→LF, 앞뒤 공백 제거뿐이다. 숫자·조건·URL은 바꾸지 않았다. 정규화 본문 1,445자, 회사·직무·5년+·대체 인정·정규직·수습 3개월·전형 보존. 본문 이메일/URL은 없고, 별도 서명에는 담당자 이메일이 있다. 과거 1,497자 기록 및 안정적 템플릿 ID와의 연결은 미확정이다. 새 저장·삭제·후보 발송은 하지 않았다. 원문 조회 증거는 `private-reviews/rps-fresh-1.json`, `rps-fresh-2.json`, 대조 결과는 `private-reviews/rps-roundtrip-compare.log`에 보존한다.
