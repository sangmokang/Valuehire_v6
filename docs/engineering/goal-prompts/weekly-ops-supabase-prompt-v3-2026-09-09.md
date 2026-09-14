# 착수 프롬프트 v3 — 죽은 Supabase 파이프를 되살려 위클리를 DB에서 낸다

작성 2026-09-09 · 대상 저장소 `/Users/kangsangmo/Desktop/Valuehire_v6`
**v1(09-08)·v2(09-09 오전)를 모두 대체한다.** v2는 전제 두 개가 틀렸다 — 아래 §1에 정정을 적었다.
모든 수치는 2026-09-09 Supabase 실측이다.

---

## 0. 상위 목표 (한 문장)

Supabase에는 위클리에 필요한 테이블이 **이미 다 있다. 그런데 데이터를 넣는 파이프가 전부 죽어 있다.**
그 파이프를 되살려, 위클리 수치를 사람이 ClickUp·Gmail을 손으로 세지 않고 DB 조회로 낸다.

**성공 신호**: FY26W38 위클리에서 "포지션 몇 개, 후보 몇 명"을 DB 한 번 조회로 답하고,
그 값의 **기준시각이 회의일 당일**이다(지금은 8/31에 멈춰 있다).

---

## 1. ⚠️ v2의 전제 2개가 틀렸다 — 정정

| v2에 쓴 것 | 실측 결과 |
|---|---|
| "Supabase 자격증명이 저장소에 없다" | **틀림.** `~/Desktop/Valuehire_v5/.env.local`과 `~/Desktop/Valuehire_v4/.env.local`에 있고 **동일 프로젝트**다. 다만 아래 ⓐ 참조 |
| "주차 스냅샷 테이블이 없어 4주 트렌드 불가" | **틀림.** `weekly_snapshot`·`weekly_growth_snapshots`·`weekly_growth_metrics`·`pipeline_stage_history`가 **전부 이미 있다.** 문제는 스키마가 아니라 **데이터가 안 쌓인다는 것** |

**ⓐ 키 상태 (값은 절대 출력·커밋 금지)**

```
NEXT_PUBLIC_SUPABASE_URL         존재
NEXT_PUBLIC_SUPABASE_ANON_KEY    존재하나 무효 → {"message":"Invalid API key"} (401)
SUPABASE_SERVICE_ROLE_KEY        작동 (200)
```

⚠️ 지금 읽히는 유일한 키가 **service_role**이다. 이건 RLS(행 수준 보안)를 우회하는 최고 권한이라
**대시보드·프런트엔드에 절대 쓰면 안 된다.** 서버 측 배치에서만 쓰고, 조회용으로는 anon 키를
재발급받아 RLS 정책과 함께 쓴다. → WU-0.

---

## 2. 실측 — 인프라는 훌륭한데 전부 멈춰 있다

DB에 테이블 **253개**가 있다. 위클리에 필요한 것만 추리면:

| 테이블 | 행수 | 최신 데이터 | 판정 |
|---|---:|---|---|
| `pipeline_position_cards` | 1,136 | **2026-08-31 23:05** | 🔴 9일 정지 |
| `pipeline_candidates` | 13,085 | — | 🔴 (동일 배치) |
| `gmail_messages` | 803 | **2026-07-25** | 🔴 **6주 정지** |
| `gmail_threads` | 724 | — | 🔴 |
| `gmail_derived_events` | 155 | — | 🔴 |
| `gmail_reconciliation_ledger` | 949 | — | 🔴 |
| `pipeline_stage_history` | **56** | **2026-05-20** | 🔴 **3개월 반 정지** |
| `weekly_growth_metrics` | 18 | **2026-W21** | 🔴 **16주 정지** |
| `weekly_growth_snapshots` | 100 | — | 🔴 |
| `weekly_snapshot` | 55 | — | 🟡 소싱 채널용(포지션·후보 아님) |
| `gmail_position_requests` | **0** | 없음 | 🔴 **한 번도 안 채워짐** |
| `consultant_weekly_metrics` | **0** | 없음 | 🔴 빈 테이블 |
| `weekly_meetings` | 245 | — | 🟢 노션 회의록 적재됨 |

**증명 — 9월 데이터가 통째로 없다**:
```
9/1 이후 갱신된 포지션 카드: 0건
프랙탈라이즈 카드: 0건          ← 9/1 계약한 신규 고객사가 DB에 없음
8/25 이후 갱신: 27건            ← 8월 말이 마지막
```

**⚠️ 중요한 자기정정**: 조사 중 "FY26 LIVE = 131건, 메모리의 W36 값과 일치"라고 보고했는데,
이는 정확하다는 뜻이 **아니다**. 같은 낡은 데이터를 본 것이다.
**131은 2026-08-31 기준값이지 오늘 값이 아니다.** 오늘 값은 DB로 알 수 없다.

---

## 3. Live 포지션 정의 — 이미 DB에 구현돼 있다 (지시 ③)

사장님 지시: SCRAPED · CLOSEDPOSITIONS · Complete 제외. **DB의 `stage` 컬럼으로 그대로 된다.**

`pipeline_position_cards.stage` 실측 분포(전체 1,136행):

| stage | 수 | 구분 |
|---|---:|---|
| `complete` | 315 | ❌ 제외 |
| `scraped` | 308 | ❌ 제외 |
| `closed` | 75 | ❌ 제외 (ClickUp `CLOSEDPOSITIONS`) |
| `reviewing` | 219 | ✅ Live |
| `holding` | 21 | ✅ Live |
| `etc` | 13 | ✅ Live |
| `ai_ml_data` | 12 | ✅ Live |
| `backend` / `designer` | 8 / 8 | ✅ Live |
| `frontend` | 6 | ✅ Live |
| `marketing` | 5 | ✅ Live |
| `po_pm` / `matching` | 4 / 4 | ✅ Live |
| `hr_finance` | 2 | ✅ Live |

**`board_id`로 연도를 나눈다**: `FY26_Clients` 880행 / `FY25_Clients` 256행.

```
FY26_Clients  LIVE=131  DEAD=749     ← 이 131이 8/31 기준값
FY25_Clients  LIVE=185  DEAD=71      ← 작년 것이 Live로 남아 있음(정리 대상인지 확인 필요)
```

**질의 정의(확정)**:
```sql
board_id = 'FY26_Clients' AND stage NOT IN ('complete','scraped','closed')
```

⚠️ FY25가 185건이나 Live로 남아 있다. **의도인지 방치인지 사장님 확인 필요** — 트렌드에 섞이면 왜곡된다.

---

## 4. 사장님 지시 6건 → 실측 근거와 착지점

### 지시 ① `mail_events`는 절대 `NOT_RUN`이 되면 안 된다 / 신규 포지션을 파악해야 한다

**정확한 타겟을 찾았다**: `gmail_position_requests` 테이블이 **0행**이다. 스키마는 있는데
한 번도 안 채워졌다. 이게 "신규 포지션이 뭔지 모른다"의 실체다.

**해석**: "못 읽었는데 PASS라고 하라"가 아니라 **필수 소스로 승격**하라는 뜻.
`mail_events`가 PASS가 아니면 **브리프 발행을 막는다**(fail-closed). NOT_RUN으로 조용히
넘어가는 경로를 없앤다.

**메일 분류 규칙(실측 기반)** — ⚠️ `[포지션]` 접두 하나가 두 가지로 쓰인다:

| 제목 | 수신자 | 의미 |
|---|---|---|
| `[추천]{회사}, {직무} - {이름} 님` | 고객사 도메인 | 고객사 추천 발송 |
| `[포지션]{회사}, {직무} - {이름} 님` | 개인 gmail | 후보자 제안 |
| `[포지션]비스텔리전스, FDE /FSE` | **valueconnect.kr 팀 4명** | **신규/재정의 포지션 의뢰** |

→ **수신자 도메인으로 분기해야 한다.** 제목 접두만으로는 구분 불가.

### 지시 ② AI Search 메일 제목 통일

실측 — 현재 **6가지 제목**이 돌아다닌다:

| 실제 제목 | 접두 | 인원 |
|---|---|---|
| `[Candidate Search] 워트인텔리전스 Data Engineer (Ontology/KG, 7년+) — 20명 Shortlist + 7명 Market Map` | `[Candidate Search]` | 20+7 |
| `[Candidate Search] 매드업 Senior AI Engineer — 석사 이상 후보 리스트` | 같음 | **없음** |
| `[비스텔리전스 FDE] 후보 20명 점수순 검토·기추천 5명 상태 / 1촌·이메일 확인 (2026-09-08)` | `[회사 직무]` | 20+5 |
| `[후보자 서치] 워트인텔리전스 Data Analytics Engineer 후보군` | `[후보자 서치]` | **없음** |
| `[워트인텔리전스] Ontology·Knowledge Graph Data Engineer 후보자 Shortlist (10명)` | `[회사]` | (10명) |
| `[워트인텔리전스] Ontology Data Engineer 후보자 Shortlist (8명)` | `[회사]` | (8명) |

⚠️ **수신자도 제각각**이다. 팀 4명 전체로 간 것, **자기 자신에게만 보낸 것**
(`toRecipients: ["sangmokang@valueconnect.kr"]`), `Fwd:`로 재전송한 것이 섞여 있다.
자기 앞으로만 보낸 건 팀이 못 본다.

**통일 규격(제안 — 승인 필요)**:
```
[Candidate Search] {회사} · {직무} — shortlist {N} / market map {M} ({YYYY-MM-DD})
수신: sangmokang, rogan, kcs, julian @valueconnect.kr  (팀 전원 고정)
```

### 지시 ③ Live 포지션 + 4주 트렌드 → §3 참조. 트렌드는 지시 ⑤와 함께 WU-6

### 지시 ④ 후보자 리포팅은 FY26W36 양식

정본에서 실측한 섹션: 경영진 판단 → 고객 신호·우선순위(P0/P1) → 운영 변경 → 소싱 실행 →
**§1 신규 카드**(등록일/제목/상태) → **§2 이동**(면접진입·과제검토·클로징·탈락) →
**§3 면접 중·최종합격**(단계/후보자/비고) → **§4 면접 직전**(고객사추천/추천/제안) →
채널별 가시성 → 채용페이지 관측 → 경영 액션 → 데이터 메모.

⚠️ **§2는 `pipeline_stage_history`가 있어야 만들어진다.** 그 테이블이 5/20에 멈춰 56행뿐이다.
→ WU-4가 선행 조건.

### 지시 ⑤ 면접 단계 수익화 두께 4주 트렌드

⚠️ **지금은 불가능하다.** `pipeline_stage_history` 56행(5/20 정지)·`weekly_growth_metrics`
18행(W21 정지)으로는 4주를 못 만든다. WU-4·WU-6으로 파이프를 살린 뒤 **4주가 실제로 쌓여야**
첫 트렌드가 나온다. 그 전까지는 `NOT_COLLECTED`로 표기한다(0으로 채우지 않는다).

참고 손집계: 9/8 기준 면접자 11 + 최종합격 4 = 15명 / W36은 13명.

### 지시 ⑥ 모든 것은 Supabase 안에서 → 전 WU의 전제. 산출물은 DB 조회로만 만든다

---

## 5. 동기화 코드의 위치 (되살릴 대상)

```
$ grep -l "pipeline_position_cards|pipeline_stage_history|gmail_position_requests"
Valuehire_v4/scripts/import-clickup-to-position-boards.py   ← ClickUp 적재기
Valuehire_v4/src/admin/sourceCollectionActions.ts
Valuehire_v4/src/lib/owner/metrics.ts
Valuehire_v5  → 0건
Valuehire_v6  → 0건
```

⚠️ **적재 코드가 v4에만 있고 v6에는 없다.** v6에서 "Supabase 안에서" 하려면 이 코드를
v6로 가져오거나(포팅), v4의 스크립트를 정식 러너로 승격해야 한다. **어느 쪽인지 결정 필요**(WU-0).

---

## 6. 작업 단위 — 순서 고정

각 WU는 **AC 1개 = 검증 명령 1개**. 표의 4요소(명령/기대출력·최소건수/양성·음성 사례/우회 불가)를
모두 만족해야 닫힌다.

### WU-0 — 키 정리와 코드 위치 결정 (코드 0줄, 사장님 확정 2건)

| 항목 | 내용 |
|---|---|
| 결정 ① | **anon 키 재발급**(현재 무효). service_role은 서버 배치 전용으로 격리하고 조회는 anon+RLS로 |
| 결정 ② | 적재 코드를 **v4에서 v6로 포팅**할지, **v4 스크립트를 정식 러너로 승격**할지 |
| 검증 명령 | `curl -s -o /dev/null -w "%{http_code}" "$URL/rest/v1/" -H "apikey: $ANON" -H "Authorization: Bearer $ANON"` |
| 기대 출력 | `200` (현재는 `401`) |
| 음성 사례 | service_role 키가 프런트엔드 번들·공개 설정·커밋에 들어가면 즉시 FAIL |
| 우회 불가 | 키 **값**을 출력·로그·커밋에 남기지 말 것. 존재 여부와 상태코드만 보고 |

### WU-1 — ClickUp → `pipeline_position_cards` 동기화 재가동

| 항목 | 내용 |
|---|---|
| 사전조건 | WU-0 결정 ②, ClickUp rate limit 해제(2026-09-09 기준 `464분 대기` 상태였음) |
| 실행 명령 | 적재기 실행 후 `last_updated_at` 최댓값 조회 |
| 기대 출력 | 최댓값이 **실행 당일**로 갱신. 9/1 이후 갱신 건수 > 0 |
| 양성 사례 | 9/1 계약한 **프랙탈라이즈 SWE 카드가 DB에 나타난다**(현재 0건) |
| 음성 사례 | ① 적재 실패를 빈 결과로 접으면 FAIL ② `has_more` 페이지를 다 안 돌면 FAIL ③ 기존 행을 덮어써 과거 `stage`를 잃으면 FAIL(WU-4와 충돌) |
| 우회 불가 | 적재 후 **독립 조회**로 readback. 적재기 로그의 "성공" 문자열은 증거가 아니다 |

### WU-2 — Gmail → `gmail_messages` 동기화 재가동 (7/25 정지)

| 항목 | 내용 |
|---|---|
| 실행 명령 | 수집기 실행 후 `sent_at` 최댓값 조회 |
| 기대 출력 | 최댓값이 최근 7일 이내 |
| 양성 사례 | 9/8자 `[Candidate Search]` 메일 2건이 DB에 들어온다 |
| 음성 사례 | ① 인증 만료를 빈 목록으로 바꾸면 FAIL ② 6주 공백을 건너뛰고 최근 것만 넣으면 FAIL(공백 구간 명시 필요) |
| 우회 불가 | 후보자 원문·개인 이메일 주소를 리뷰 산출물·git에 넣지 말 것 |

### WU-3 — `gmail_position_requests` 채우기 = 신규 포지션 탐지 (지시 ①)

| 항목 | 내용 |
|---|---|
| 사전조건 | WU-2 |
| 실행 명령 | 분류기 실행 후 `gmail_position_requests` 행수 조회 |
| 기대 출력 | 행수 > 0, 그리고 `mail_events` 상태가 `PASS` |
| 양성 사례 | 세 유형이 **각각 최소 1건**씩 올바르게 분류된다 — 팀 내부 수신 `[포지션]비스텔리전스, FDE /FSE` → 신규/재정의 · 고객사 도메인 `[추천]...` → 고객 발송 · 개인메일 `[포지션]...` → 후보자 제안 |
| 음성 사례 | ① `mail_events`가 `NOT_RUN`인데 브리프가 **발행되면 FAIL**(fail-closed 확인) ② 수신자 도메인을 안 보고 제목 접두만 쓰면 `[포지션]` 두 종류가 섞여 FAIL ③ 커넥터 오류를 빈 목록으로 바꾸면 FAIL |
| 우회 불가 | 실제 메일 3종을 fixture로 고정. 제목만으로 분류하는 구현은 반드시 실패해야 함 |

### WU-4 — `pipeline_stage_history` 재가동 (§2 이동 + 트렌드의 기반)

| 항목 | 내용 |
|---|---|
| 실행 명령 | 동기화 1회 후 `changed_at` 최댓값과 행수 조회 |
| 기대 출력 | 최댓값이 실행 당일, 행수가 56보다 증가 |
| 양성 사례 | 카드가 단계를 옮기면 `(candidate_id, from_stage, to_stage, changed_at)` 1행이 남는다 |
| 음성 사례 | **RED 먼저** — ① 현재는 단계가 바뀌어도 이력이 안 남는 것을 커밋으로 남긴다 ② 같은 변경을 두 번 적재하면 중복 행이 생기는지(멱등성) ③ 이력 없이 §2를 만들 수 있다고 가정하면 FAIL |
| 우회 불가 | `pipeline_candidates`의 현재 stage만으로 §2를 만들려는 구현은 실패해야 함 |

### WU-5 — AI Search 제목 통일 + 파서 (지시 ②)

| 항목 | 내용 |
|---|---|
| 실행 명령 | `cd humansearch && uv run pytest -q` |
| 기대 출력 | 통일 규격 파싱 성공, 구형 5종은 `LEGACY` 또는 명시적 `FAIL` |
| 양성 사례 | `— shortlist 20 / market map 7` → 회사·직무·20·7 추출 |
| 음성 사례 | ① 숫자 없는 제목을 **0으로 추정하면 FAIL**(명시적 실패여야 함) ② 구형 5종이 조용히 통과하면 FAIL ③ `Fwd:` 재전송이 별건으로 세지면 FAIL(스레드 dedupe) |
| 우회 불가 | 위 §4 지시②의 **실제 제목 6개를 그대로 fixture로** 넣고 각각 기대 결과 고정 |

### WU-6 — 주간 지표 재가동 + 4주 트렌드 (지시 ③·⑤)

| 항목 | 내용 |
|---|---|
| 사전조건 | WU-1·WU-4 |
| 실행 명령 | 주간 집계 실행 후 `weekly_growth_metrics` 조회 |
| 기대 출력 | 최신 `week_iso`가 현재 주차(현재는 `2026-W21`에 멈춤) |
| 양성 사례 | Live 포지션 수와 면접 단계 수익화 두께가 주차별 행으로 쌓인다 |
| 음성 사례 | ① 데이터가 2주치뿐인데 4주 트렌드를 그리면 FAIL — **없는 주차는 `NOT_COLLECTED`**, 0으로 채우지 않는다 ② 동기화가 멈춘 주차를 정상값처럼 그리면 FAIL(→ WU-7의 `STALE`) ③ FY25가 FY26 트렌드에 섞이면 FAIL |
| 우회 불가 | 결측 주차가 있는 fixture로 검사. 빈 주차를 0으로 채우는 구현은 반드시 실패 |

### WU-7 — 상태 어휘에 `STALE` 추가 (거짓 초록 방지)

이번 조사가 바로 그 사례다: DB는 200을 주지만 데이터는 8/31자다.

| 항목 | 내용 |
|---|---|
| 실행 명령 | `cd humansearch && uv run pytest -q` |
| 기대 출력 | `>= 234 passed` |
| 양성 사례 | 마지막 동기화 시각이 주간 창보다 오래되면 `STALE`로 분류 |
| 음성 사례 | **RED 먼저** — ① 8/31 데이터를 9/9에 조회하면 현재는 `PASS`가 나오는 것을 커밋으로 남긴다 ② `STALE`을 `PASS`로 접으면 FAIL |
| 우회 불가 | enum 추가만으로 통과 금지. **실제 정지 시각을 담은 입력**으로 분류가 일어나는지 검사. `NOT_RUN_ONLY_REASONS`(9개)/`FAIL_ONLY_REASONS`(6개) 분류표도 갱신 |

### WU-8 — 리포트 렌더 (노션 + 웹)

| 항목 | 내용 |
|---|---|
| 사전조건 | WU-1·3·4·6 |
| 기대 출력 | FY26W36 §1~§4 구조 + 4주 트렌드 표 2개, readback 일치 |
| 음성 사례 | ① 파이프라인 전주 대비 비교가 빠지면 FAIL(2026-09-07 실사고) ② 후보자 실명이 git·이메일·admin·로그에 들어가면 FAIL ③ readback 없이 "발행됨"이라 하면 FAIL |
| 우회 불가 | write-ahead intent → 쓰기 → readback → 영수증 저장. HTTP 200은 영수증이 아니다 |

---

## 7. 하지 말 것

- **service_role 키를 프런트엔드·공개 설정·커밋에 넣지 마라.** 서버 배치 전용이다.
- **자격증명 값을 출력·로그·커밋에 남기지 마라.** 이름과 상태코드만.
- **DB가 200을 준다고 데이터가 최신이라고 하지 마라.** 이번 조사의 교훈이다.
- **`mail_events`를 `NOT_RUN`으로 두고 브리프를 발행하지 마라.**
- **없는 주차를 0으로 채우지 마라.** `NOT_COLLECTED`.
- **FY25를 FY26 트렌드에 섞지 마라.** `board_id`로 분리.
- **후보자 실명·연락처를 스냅샷·git·이메일·admin·로그·리뷰 산출물에 넣지 마라.**
- **병합을 에이전트가 실행하지 마라.** `USER_MERGE_ONLY`.
- **테스트를 약화시켜 초록을 만들지 마라.**
- **워크트리에서 bare `git stash` / `git stash pop` 금지.**

---

## 8. 완료 조건

- WU-0~WU-8 각각 focused test PASS + 독립 GREEN 커밋
- `bash verify.sh` PASS · `cd humansearch && uv run pytest -q` ≥ 234 passed
- **`pipeline_position_cards.last_updated_at` 최댓값이 실행 당일**
- **`gmail_messages.sent_at` 최댓값이 최근 7일 이내**
- **`gmail_position_requests` 행수 > 0**
- **`weekly_growth_metrics`의 최신 `week_iso`가 현재 주차**
- 4주 트렌드는 **4주가 실제로 쌓인 뒤에만** 그린다(그 전엔 `NOT_COLLECTED`)
- PR 생성, CI `push`·`pull_request` **양쪽** SUCCESS
- 상태 `READY TO MERGE` 보고, **병합은 사장님이**

---

## 9. 보고 형식

절차는 내부용. 사장님께는 쉬운 한국어로 짧게: 무엇을 / 왜 / 증거(명령과 출력 숫자 그대로) / 다음.
자격증명은 존재 여부만. **데이터의 기준시각을 항상 함께 보고한다**(값만 말하지 않는다).
