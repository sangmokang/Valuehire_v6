# Admin Dashboard "몰입도 잔디밭" 구현 스펙 — 적대적 검증 (2026-08-16)

- 검토 대상: Codex가 작성한 "STRICT IMPLEMENTATION PROMPT: Admin Dashboard 몰입도 잔디밭" (strict/mixed/L3)
- 대상 URL(스펙 원문 기준): `https://admin.valuehire.cc/admin/dashboard`
- 검토자: Claude (Sonnet 5), Valuehire_v6 저장소 기준
- 결론: **구현 착수 전 3가지 전제 조건이 해결되어야 함.** 스펙의 데이터 모델/알고리즘 자체는 정교하지만, (1) 대상 코드베이스 확인, (2) 외부 사이트 무인 접근 아키텍처, (3) 멱등성 설계의 자기모순을 먼저 풀지 않으면 §3~§5 구현은 의미가 없음.

## 스펙 원문 요약 (검토 편의를 위한 압축)

AI Search 자동 발굴 프로필 수 + 제안 메시지(LinkedIn/Saramin/JobKorea) 발송/회신/지원 수를 주 단위(월요일 00:00 KST 시작)로 집계해 SQLite(1차 ledger) → Supabase(dashboard 조회용 mirror)에 저장하고, `/admin/dashboard`에 GitHub 잔디밭 스타일 히트맵으로 표시하는 스펙. 핵심 소스:

- `sourcing_runs` (Supabase/Postgres) — AI Search 자동 실행 수
- `pipeline_candidates` (admin DB, `source LIKE 'ai_search:%'`) — admin 적재 후보 수
- ClickUp list `FY26AI_Search` (`901818680208`) — 카드 생성 수
- LinkedIn talent inbox 2개 URL(awaiting reply / main-replied) — 발송/회신 스레드 수
- Saramin messenger URL(`room_no=55049271`), JobKorea position 페이지 — 지원/메시지 수

원칙: 추정 집계 금지, 공통 식별자 없는 시스템 간 "동일 인물" 주장 금지, 외부 사이트에 쓰기 액션(발송/지원/상태변경) 절대 금지, 소스 fetch 실패는 `0`이 아니라 `NOT_RUN`/`FAILED`로 기록. SQLite 스키마 3종(`engagement_source_events`, `engagement_weekly_rollups`, `engagement_fetch_runs`) + Supabase mirror 스키마 + RLS(authenticated만 read) 정의됨. 테스트 요구사항 7종, fail-fast 조건 8종 명시.

---

## 🔴 치명적 — 전제 붕괴

### 1. 대상 스키마/앱이 이 저장소(Valuehire_v6)에 존재하지 않는다

`pipeline_candidates`, `sourcing_runs`, `/admin/dashboard` 라우트, SQLite/Supabase 클라이언트 설정, ClickUp/LinkedIn/Saramin/JobKorea 연동 코드 — 전부 이 저장소에서 검색 시 **0건**. 저장소 루트는 `contracts/ docs/ hooks/ humansearch/ scripts/`뿐이고, `humansearch/src/humansearch/__init__.py`는 스스로 "G2 verification plumbing only — no business behavior lives here yet"라고 명시한다. Next.js 앱 자체가 없다.

`sourcing_runs`, `pipeline_candidates`와 유사한 명칭이 등장하는 유일한 곳은 `docs/engineering/v6-coding-principles-goal-2026-08-06.md`인데, 이는 **다른 저장소의 마이그레이션 94개를 감사한 회고 문서**의 인용이다(`pipeline_candidates`는 Claude가 잘못 지목했다가 Codex에게 반박당한 대상으로 등장; `sourcing_runs`는 RLS `USING (true)` 전면개방 감사 목록에 등장). 즉 실제로 존재하는 테이블이 아니라 다른 프로젝트에 대한 서술을 재활용한 것.

→ 스펙 §6의 fail-fast 조건 1~4("sourcing_runs table 없음 / pipeline_candidates table 없음 / source column 없음 / timestamp column 확정 불가")는 **이 저장소에서 시작 즉시 전부 트리거된다.** 스펙 저자가 자기가 정한 규칙을 자기 코드베이스에 대해 한 번도 실행해보지 않고 작성했다는 뜻이다.

**필요 조치**: admin.valuehire.cc가 실제로 배포되는 레포/브랜치/워크트리를 먼저 특정하고, 그 위에서 §6 fail-fast 조건을 실제로 돌려본 뒤에만 §3 이후 착수.

### 2. 무인 실행 아키텍처가 정의되지 않았다 (특히 로그인 세션 필요한 3개 소스)

LinkedIn talent inbox, Saramin messenger, JobKorea position 페이지는 REST API가 아니라 **개인 로그인 세션이 있어야 보이는 화면**이다. 스펙은 "주간 자동 집계"라고 하면서:

- 서버 cron이 무인으로 어떻게 인증하는지(세션 쿠키 서버 보관? 계정 자격증명 저장?) 다루지 않는다.
- 세션 만료/2FA/캡차 발생 시 동작을 정의하지 않는다.
- LinkedIn Recruiter/Talent 자동 스크레이핑은 ToS 위반 소지가 있고 계정 정지 리스크가 있다 — 절대원칙 9("읽기/카운트만 한다")로는 이 리스크가 해소되지 않는다. 이건 기술 구현 이전에 **사장님의 명시적 승인이 필요한 사업적 리스크**다.

참고로 `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md`에는 이런 소스들이 "**사람이 이미 로그인해둔 브라우저에 CDP로 붙는 방식**"으로 설계돼 있다고 명시되어 있다 — 이는 사람이 브라우저를 열어둔 상태에서만 작동한다는 뜻이며, 코덱스 스펙이 말하는 "무인 주간 배치 자동 upsert"와 근본적으로 모순된다.

**필요 조치**: 무인 서버 배치 vs 반자동(사람이 브라우저 열어둔 상태에서만 도는) 잡 중 아키텍처를 먼저 결정하고, ToS 리스크를 명시적으로 승인받는다.

---

## 🟠 심각 — 스펙이 자기 원칙을 스스로 위반

### 3. `payload_hash` 멱등성 설계가 원칙 8 / 테스트 2와 충돌

`engagement_source_events`의 UNIQUE 키는 `(source_system, source_primary_key, event_type, payload_hash)`이고 `payload_hash`는 "normalized source payload"에서 계산한다. 그런데 LinkedIn/Saramin류 스크레이핑 소스는 화면에 절대시각이 아니라 "2일 전", "방금" 같은 **상대시각 텍스트**로 노출되는 게 일반적이다. 이 상대시각이 payload에 섞여 해시에 들어가면 같은 이벤트를 재실행할 때마다 해시가 달라져 **새 row가 계속 쌓인다** — 원칙 8("재실행해도 중복 적재 금지")과 테스트 2("같은 payload 2회 실행해도 count 증가 안 함")를 정면 위반. "normalized payload"가 정확히 무엇을 제외하는지(상대시각, 조회수, 기타 UI 노이즈) 스펙에 정의가 없어 구현자가 그대로 구현하면 idempotency가 실전에서 깨진다.

**필요 조치**: payload_hash 계산에 포함될 필드를 화이트리스트로 명시(안정적 식별자 + 이벤트 타입만), 변동성 있는 표시 텍스트는 명시적으로 제외.

### 4. "AI Search 자동 실행" 판별 기준이 미정의 상태로 완료 기준에 이미 포함됨

§2.1은 "실제 스키마 확인 후 filter 결정, 없으면 fail-fast"라고 해놓고, 정작 "자동 vs 수동 실행을 구분하는 컬럼"이 뭔지 스펙 자신도 특정하지 못한다. 스키마를 아직 안 본 상태에서 필터 로직을 이미 확정 요구사항처럼 적어놓은 게 모순이다 — 완료 기준(§10)에는 이게 이미 동작하는 걸 전제로 넣어놨다.

---

## 🟡 중간 — 모호함 / 누락

- **소스 내부 부분 실패 처리 모호**: ClickUp 1페이지 성공, 2페이지 타임아웃처럼 한 소스 안에서 일부만 실패했을 때 그 소스 상태가 `FAILED`인지 `PARTIAL`인지 정의 없음. §5는 소스 단위로만 SUCCESS/FAILED를 말해서 페이지네이션 있는 소스엔 이분법이 안 맞는다.
- **JobKorea `snapshot_total` 첫 주 처리 미정의**: "이전 snapshot과 비교 가능한 경우에만 weekly delta 계산"인데, 최초 실행 시 이전 스냅샷이 없으면 그 주 값을 `0`으로 넣을지 `NOT_RUN`으로 넣을지 불명 — 원칙 10과 상충 소지.
- **개인 세션 URL 하드코딩**: LinkedIn inbox id, Saramin `room_no` 등은 특정 계정/세션에 종속된 값. 계정 변경·세션 만료 시 전부 깨지고, 내부 ID를 코드/문서에 남기는 것도 불필요한 노출.
- **`week_start_kst` 타입 불일치 위험**: SQLite `TEXT` vs Supabase `date`. 미러링 시 포맷(`YYYY-MM-DD` vs 타임스탬프 포함 문자열) 변환 규칙이 없으면 PK 매칭 실패 가능.
- **Supabase 서비스 키 관리 공백**: SQLite→Supabase upsert 프로세스가 쓰는 service-role key 보관 방식이 전혀 없음. RLS(read)는 정의했지만 write 경로 보안은 공백.

## ⚪ 경미

- **테스트 5("공통 식별자 없이 동일 집합 주장 금지")가 사실상 문자열 스냅샷 테스트**: 특정 문구("동일 후보" 등)만 안 쓰면 통과하므로 원칙의 의미론적 준수가 아니라 형식적 준수만 검증.
- **`payload_json` PII 보존 정책 없음**: 원본 스크레이핑 데이터(후보 이름, 메시지 내용 등)가 그대로 저장되는데, SQLite 파일을 git에 안 올린다는 것 외에 보존기간·접근권한 정책이 없음.

---

## 결론 및 다음 단계

데이터 모델(테이블 정의, upsert 순서, RLS 방향)은 꼼꼼하지만, **"이게 실제로 존재하는 시스템 위에서 돌아가는가"와 "로그인 세션이 필요한 3개 외부 사이트를 무인으로 어떻게 읽는가"**라는 가장 근본적인 두 질문에 답이 없다. 착수 전 필수 선행 작업:

1. admin.valuehire.cc 실제 배포 레포/경로 특정 → 그 레포에서 §6 fail-fast 조건 실제 실행.
2. LinkedIn/Saramin/JobKorea 무인 배치 vs 반자동 CDP 잡 아키텍처 결정 + ToS 리스크 승인.
3. `payload_hash` 정규화 규칙(변동 필드 제외) 구체화.

이 세 가지가 해결되기 전에는 §3~§5 스키마/알고리즘 구현 착수는 의미가 없음.
