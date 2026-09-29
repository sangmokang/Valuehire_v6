# codeitsearch — OOOsearch 파이프라인

자사 채용 페이지를 성실히 업데이트하는 기업의 포지션을 전량 수집 → Supabase 적재 →
세그멘테이션 → 채용 포털 인재풀 서치 → 채점 → 내부 보고 메일까지 잇는 파이프라인.

`codeitsearch`는 첫 인스턴스이고, 회사만 바꾸면 `wrtnsearch` / `spoonlabssearch` /
`goodchoicesearch` / `bunjangsearch` 가 같은 절차로 돈다.

실행 절차 전체는 **`.claude/skills/codeitsearch/SKILL.md`** 에 있다. 이 문서는 모듈 지도다.

## 모듈

| 파일 | 역할 |
|---|---|
| `keywords.py` | 세그먼트별 국문·영문 키워드 4계층 (`core`/`expanded`/`stack`/`preferred`) |
| `segmentation.py` | 포지션 → 세그먼트 매핑, 경력범위 파싱, `searchable` 판정 |
| `ingest_positions.py` | 스냅샷 JSON → `jobmarket_positions` + `jobmarket_snapshots` (멱등) |
| `supabase_io.py` | PostgREST 전송 (stdlib only, service-role key는 환경변수) |
| `page_trace.py` | `search_jobs` 생성/마감, 방문·리스팅 페이지를 `page_snapshots`에 기록 |
| `scoring.py` | 하드제외 게이트 + 100점 배점 + triage 순서 |
| `compose_mail.py` | 리스팅 형태 보고 메일 본문 합성 (표 금지) |

## 계약 파일 (코드 바깥)

| 파일 | 내용 |
|---|---|
| `contracts/humansearch/company-careers-sources.json` | 대상 기업·채널 레지스트리, harvest 규칙 |
| `contracts/humansearch/in-seoul-universities.json` | 인서울/세계명문/과기원 분류, 전문대 하드컷 |
| `contracts/humansearch/saramin-markers.json` | 사람인 인증 surface 마커 |

값을 바꿀 때는 **계약 파일만** 고친다. 코드에 학교명·회사명을 하드코딩하면 러너마다 기준이 갈린다.

## 환경변수

```
SUPABASE_URL            (또는 NEXT_PUBLIC_SUPABASE_URL)
SUPABASE_SERVICE_ROLE_KEY  (또는 SUPABASE_SECRET_KEY)
```

## 실행

```bash
# 1. 적재 (먼저 --dry-run 으로 세그먼트 분포 확인)
python tools/codeitsearch/ingest_positions.py tools/codeitsearch/data/<snapshot>.json --dry-run
python tools/codeitsearch/ingest_positions.py tools/codeitsearch/data/<snapshot>.json

# 2. 서치 잡 열기 → 방문 페이지 기록 → 마감
JOB=$(python tools/codeitsearch/page_trace.py open-job --command codeitsearch \
        --params-file params.json --requested-by claude-win)
python tools/codeitsearch/page_trace.py record --job-id "$JOB" --snapshot-file snaps.json
python tools/codeitsearch/page_trace.py close-job --job-id "$JOB" --status done --summary-file summary.json

# 3. 메일 본문 합성 (발송은 에이전트가 Gmail MCP 로)
python tools/codeitsearch/compose_mail.py --results results.json --out mail.json

# 테스트
uv run --with pytest python -m pytest tools/codeitsearch/tests -q
```

Windows / macOS 모두 같은 명령으로 돈다. 표준 라이브러리 외 런타임 의존성은 없다
(pytest는 테스트 전용).

## 알려진 제약

- **사람인 인재풀은 기업회원(`ut=c`) 로그인 + 이용권이 필요하다.** 개인회원 로그인으로는 못 들어간다.
  `/talent-pool/main/tutorial` 로 리다이렉트되는 것은 로그인 증거가 **아니다** — 공개 페이지다.
  판정은 `인재풀 바로가기` CTA의 href가 `auth?ut=c` 인지로 한다.
- **Gmail 커넥터 스코프 부족** — `gmail.labels`/`gmail.modify` 미승인 상태라 `aisearch` 라벨
  생성·부착이 거부된다. 스코프 승인 또는 수동 라벨 생성 필요.
- `jobmarket_positions` 의 자연 유니크 키 **`uq_jmp`** 는 `COALESCE(...)` 표현식 위의
  인덱스라 PostgREST 의 `on_conflict`(컬럼 목록)로 지정할 수 없다 — upsert 불가(42P10).
- 그래서 적재는 **실행마다 `source_file` 에 `#run-<UTC타임스탬프>` 접미사**를 붙여 새 행을
  **먼저 쓰고**, 성공한 뒤에 같은 prefix 의 이전 실행분을 지운다. PostgREST 에 트랜잭션이
  없으므로 이 순서가 유일한 안전장치다 — insert 가 실패하면 이전 실행분이 그대로 남는다.
- `jobmarket_positions.id` 시퀀스가 과거 벌크 적재로 어긋나 있어 `insert(assign_ids="id")`
  로 명시 할당하고, **PK 충돌 시에만** max 를 다시 읽어 재시도한다.
- 학교 판정: 이름에 `캠퍼스` 가 있으면 **서울 캠퍼스 허용목록**에 있을 때만 인서울(표지 나열
  방식은 국제·자연과학캠퍼스를 놓쳤다). 영문 항목은 단일 토큰이면 토큰 완전일치, 다중
  토큰이면 **연속 토큰 부분수열** 일치(`University of Michigan` ≠ `Michigan State University`).
- 포털 표기: 사람인·잡코리아는 캠퍼스를 `학교명(지역)`, 전문대를 `대학(2,3년)` 으로 준다.
  괄호째 분교 표지(`(용인)`·`(원주)`·`(세종)` 등)와 `2,3년`·`초대졸` 전문대 표지를 계약에 둔다.
  이름만 같은 별개 학교(`Berkeley College`)는 `not_world_top_exact` 로 이름 전체 일치 시만 막는다.
- 적재는 스냅샷의 회사명·플랫폼이 레지스트리 항목과 다르면 거부하고, 검색 대상인데 검색어가
  0개인 공고가 있으면 Supabase 를 건드리지 않고 멈춘다. 정리 대상은 `<prefix>#run-` 표지가 있는 행뿐이다.
- 메일 합성은 `score_breakdown` 의 **축 이름·상한·합계·문턱**을 전부 검증한다. 손으로 쓴
  점수나 지어낸 축은 `UnverifiedCandidate` 로 거부된다.

## 적대 검증 이력

- 2026-09-30 이어받기 검토(다른 PC 작업 인수): codex V1 FAIL(MAJOR 5·MINOR 1) + 독립 재현 MAJOR 3.
  4차가 3차 회귀 18건 중 3건만 되살린 것(전수 생성 비교), 포털 괄호 분교·`(2,3년)` 전문대 미인식
  (수집 기록 실측 343건·107건), 레지스트리 불일치 적재, run 표지 없는 삭제 선택, 검색어 0개 적재,
  사유 없는 0명 보고를 고쳤다. 테스트 147 → 225개, 수정 부위 뮤테이션 11종 전부 검출.
- 2026-09-28 `codex exec` 적대 리뷰 **2차**: BLOCKER 1(적재 데이터 손실) / MAJOR 4 PARTIAL.
  → 삭제-우선을 버리고 run 접미사 기반 쓰기-우선으로 재설계, 캠퍼스 허용목록 규칙,
  연속 토큰 부분수열 매칭, `대학원` 예외, 메일 축·상한 검증까지 반영. 테스트 50 → 126개.
  codex 가 지적한 "테스트 위장" 2건(복구 테스트가 실제 경로 우회, 재시도 테스트가 next_id 고정)도
  실제 순서·재조회를 단언하도록 다시 썼다.
- 2026-09-28 `codex exec` 적대 리뷰 1차: BLOCKER 2 / MAJOR 6 / MINOR 1 → 전부 수정, 회귀 테스트 고정.
  주요 실측 결함: 분교 캠퍼스 in_seoul 오분류, 짧은 영문 약어(MIT/ETH/NUS) 부분일치,
  `산업대학` 표지가 한국산업기술대(4년제)를 전문대로 하드제외, `degree` 미검사,
  하드제외 시 총점≠내역합, 재입사 이직 2회 계산, 메일 경로의 점수 미검증,
  삭제 후 삽입 실패 시 데이터 손실, `max(id)+1` 경쟁.
