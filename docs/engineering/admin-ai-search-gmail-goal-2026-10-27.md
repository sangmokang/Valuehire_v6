# AI Search Gmail evidence goal — 2026-10-27

## Goal / 단일 인수 기준

Gmail `subject:aisearch` 검색을 마지막 페이지까지 읽은 실제 메시지에서 적어도 한 개의
AI Search Batch를 만들고, `GET /api/ai-search` 목록과
`GET /api/ai-search/{stable_batch_id}` 상세가 같은 증거를 반환하며, 빈 상태와 오류 상태도
브라우저에서 구분된다. 수집이 부분적이거나 값의 근거가 없으면 0/PASS 대신 `NOT_RUN`과 사유를
반환한다.

## 현재 상태 증거와 근본 원인

- `humansearch/src/humansearch/admin_ai_search/evidence.py:214`에 기존
  `stable_batch_id(actor, source_run_id, executed_at)`가 있다.
- `humansearch/src/humansearch/admin_ai_search/evidence.py:279`는 주입된 `AiSearchRun`만 API
  payload로 바꾸며 Gmail 입력 경로가 없다.
- `humansearch/src/humansearch/admin_weekly_dashboard/shadow_server.py:189`는 주입값이 없으면
  항상 빈 run을 사용해 `/ai-search`가 `live_sources_not_connected`가 된다.
- rebase 뒤 `main..HEAD`에는 AI Search 커밋 3개만 있고 merge-base는 `bb12d86`이다.
- `uv run --no-sync pytest -q` 실측은 `219 passed`다.
- v6에는 ai-search 스킬이 요구하는 v5 SOT 22/24/25/26과
  `tools/multi_position_sourcing`가 없고 checker는 FAIL했다. v4/v5 구현을 복사하지 않고,
  v5 점수 계약의 공개 결정 필드만 입력 계약으로 참조한다.

근본 원인은 UI/API가 결정론적 projection까지만 있고 Gmail의 페이지 수집 결과를 검증·파싱해
`AiSearchRun`으로 연결하는 adapter와 런타임 입력 배선이 없다는 것이다.

## 입출력 계약

### Gmail collection input

```text
query: "subject:aisearch -in:spam -in:trash"
page: {
  request_page_token: str | null,
  message_ids: list[str],
  next_page_token: str | null
}
message: {
  message_id: str,
  thread_id: str,
  received_at: timezone-aware datetime,
  subject: str,
  sender: str,
  body_text: str
}
```

검색은 `next_page_token`이 없을 때까지 계속한다. 토큰 반복, 페이지 오류, 메시지 읽기 오류,
요청 ID와 응답 ID 불일치는 조용히 건너뛰지 않는다.

## 실제 Gmail 실측과 후속 수정 비교

- 동일 입력 비교는 최초 화면에 있던 immutable message ID 342개만 사용했다. 수정 전에는 Batch
  342개, 고객사 파싱 239개(69.9%), 상세 근거가 하나라도 채워진 후보 10/8,243명이었다.
- 수정 후 동일 342개 입력에서는 실행 메일 340통과 테스트 메일 2통을 구분했고 Batch 296개,
  고객사 파싱 281개(94.9%), 상세 근거 보유 후보 18/8,259명(0.22%)이 됐다. 수정 전 상세
  채움률은 10/8,243명(0.12%)이었다. 14개 Batch가 후보별 알림 58통을 근거 있는 실행 단위로
  묶었고 가장 큰 Batch는 8통이다.
- 동일 입력에서 후보 count가 확정된 234 Batch는
  `raw 8,735 = parsed 8,259 + duplicate 259 + unparsed 217 + excluded 0`이다. 테스트 메일 2통은
  후보 count ledger 밖의 message-level excluded이며 사유는 `subject_test_marker`다.
- 최신 Gmail query는 4페이지를 끝까지 읽었고 마지막 `next_page_token=null` 및 전체 page token
  chain을 검증했다. 총 345통 중 실행 메일 343통, 테스트 메일 2통, Batch 299개다.
- 최신 Batch 실행 주체는 `GROK 22`, `CLAUDE_CODE 100`, `CHATGPT 98`, `AI_SEARCH 30`,
  `OTHER 49`다. 고객사·포지션 파싱은 284/299개다. 각 Batch에 제목·발신자·thread/message
  ID·수신시각·판정 사유가 있다.
- 최신 후보 count가 확정된 236 Batch는
  `raw 8,961 = parsed 8,395 + duplicate 341 + unparsed 225 + excluded 0`이다.
- 최근 메일 10통의 본문을 표본 검사했다. 명시적 학력 라벨은 3통, 경력 라벨은 3통에 있었고
  적합 근거·핵심 경력 라벨은 없었다. 후보 경계를 확정할 수 있는 값은 학력 2건, 경력 3건을
  파싱했고, 서로 다른 후보 URL 2개 뒤의 학력 1건은 귀속 근거가 없어 `NOT_RUN`으로 유지했다.
- 번호 없는 후보 제목과 URL 없는 다음 후보를 적대 재현해, 다음 후보의 경력·4축 점수가 앞
  후보에게 붙지 않도록 단일 URL fallback 경계를 제한했다. `후보 검색결과` 같은 집계 제목은
  개인 경계로 취급하지 않아 실제 raw 후보 건수가 줄지 않는다.
- 4축 점수 계약 입력이 전부 있는 후보는 없었다. 따라서 최신 203개 후보 보유 Batch는
  `NOT_RUN:score_contract_evidence_missing`, 후보가 없는 96개 Batch는
  `NOT_RUN:no_parsed_candidates`이며 메일의 총점으로 대신하지 않았다.
- 검색 기간은 최신 299개 Batch 모두 `NOT_RUN:search_period_not_found`, 실제 FU도 비범위이므로
  `NOT_RUN:fu_portal_verification_not_run`이다.
- Gmail에는 검색/읽기만 수행했다. 외부 발송 0건, 채용사이트 변경 0건, 원격 DB 쓰기 0건이다.

### Batch output additions

- `search_period`: 메일 본문에 명시된 시작/종료. 없으면 값 `null`, 상태 `NOT_RUN`, 사유 저장.
- `actor`: `GROK | CLAUDE_CODE | CHATGPT | AI_SEARCH | OTHER`.
- `actor_evidence`: 제목, 발신자, thread ID, message ID, 수신시각, 판정 사유.
- count ledger: `raw = parsed + duplicate + unparsed + excluded`를 런타임 검증한다.
- `score_buckets`: v5 계약 입력이 확인되지 않은 후보가 있으면 숫자로 가장하지 않고 해당 상태와
  사유를 함께 반환한다.

### Candidate output additions

- 필수요건별 근거
- 전체 경력과 분리된 핵심 경력
- 더 적합한 포지션 존재 여부와 근거
- 컨택 출처, 컨택 확인시각, 컨택 의견 근거
- 점수 계약 버전과 결정론적 4축 breakdown 또는 `NOT_RUN` 사유

### API / 상태 전이

```text
Gmail pages incomplete -> payload.status=NOT_RUN(reason=gmail_pagination_incomplete)
Gmail complete, no matching messages -> NOT_RUN(reason=no_ai_search_messages)
message envelope valid, body partially parsed -> Batch exists; batch verification NOT_RUN
message fully parsed, portal FU checks out of scope -> Batch exists; FU fields NOT_RUN
malformed runtime snapshot -> server start fail-fast or explicit FAIL response; empty PASS 금지
```

## 입력 영역 표

| 입력 영역 | 사례 | 처리 |
|---|---|---|
| Gmail page | 정상 IDs + 다음 토큰 | 누적 후 다음 페이지 |
| Gmail page | 마지막 페이지, 토큰 없음 | `pagination_exhausted=true` |
| Gmail page | 빈 IDs + 다음 토큰 | 다음 페이지 계속; 완료로 간주하지 않음 |
| Gmail page | 반복 토큰 | `NOT_RUN:gmail_pagination_cycle` |
| Gmail page | 호출/응답 오류 | `NOT_RUN:gmail_page_read_failed` |
| Message | 모든 envelope 필드 + text body | parser로 전달 |
| Message | envelope 필드 누락/naive 시각 | 해당 메시지 `unparsed`; 사유 보존 |
| Message | 같은 message ID 재등장 | 메시지 중복 1건으로 계산, Batch 중복 생성 금지 |
| Actor | 제목/발신자에 명시 표식 | 고정 우선순위로 분류하고 입력 근거 보존 |
| Actor | 상충 표식 | `OTHER`, `actor_markers_conflict` |
| Actor | 판단 불가 또는 Codex 등 허용목록 밖 | `OTHER`, 구체 사유 |
| Search period | 시작·종료가 모두 명시되고 유효 | 두 값 저장 |
| Search period | 일부/모호/역전 | `NOT_RUN` + 사유 |
| Candidate block | 필수 identity와 profile URL 파싱 | parsed 후보 |
| Candidate block | 같은 canonical identity | duplicate 증가, 최고 근거 레코드만 유지 |
| Candidate block | 후보로 보이나 필수 필드 파싱 실패 | unparsed 증가, 원문은 Git/API에 노출하지 않음 |
| Candidate block | 메일이 명시적으로 제외 | excluded 증가 + 사유 |
| Score | 학력·직무적합성·고난도 업무·직무기술 논리성 정수 입력 | 코드가 40/40/10/10 가중 합계와 밴드 계산 |
| Score | 총점만 있거나 계약 입력 누락 | `NOT_RUN:score_contract_evidence_missing` |
| Contacts | Gmail 자체의 컨택 증거 | 출처/확인시각/의견 근거 저장 |
| Contacts | 채용사이트 검증 | 이번 범위 밖, `NOT_RUN:not_in_scope` |
| Runtime snapshot | 예상 schema/version | 로드하고 API 배선 |
| Runtime snapshot | 알 수 없는 필드/버전/형식 | fail-fast |
| 그 외 전부 | 표에 없는 현실 입력 | 임의 추정 금지; 명시적 중단 후 표 갱신 |

## 확정 결정 목록

1. 동일 메일의 `source_run_id`는 Gmail immutable message ID다. actor와 수신시각은 같은 message
   envelope에서 결정하므로 기존 `stable_batch_id()` 결과가 재실행에도 같다.
2. actor 우선순위는 상충 시 우선 선택하지 않고 `OTHER`다. 알 수 없는 actor도 `OTHER`이며 제목,
   발신자, thread/message ID, 수신시각, 판정 사유를 모두 남긴다.
3. `raw`는 메일에서 후보 레코드로 식별된 전체 개수이고 `parsed`는 최종 유지 후보 수다.
   `duplicate`, `unparsed`, `excluded`는 서로 배타적이며 등식 불일치는 예외다.
4. Gmail의 LLM/사람이 쓴 총점은 판정 수치 입력이 아니다. 학력 40%, 직무적합성 40%,
   고난도 업무 10%, 직무기술 논리성 10%의 네 축이 모두 없으면 점수·점수대는 `NOT_RUN`이다.
5. FU 채용사이트 검증과 Daily 재검증은 비범위다. 따라서 실제 증거가 없는 FU는 0이 아니라
   `NOT_RUN`이다.
6. Gmail/브라우저/채용사이트에는 쓰지 않는다. 허용 원격 쓰기는 owner가 명시한 branch push와
   Draft PR 1건뿐이다.

## 작업 분해와 단위 관문

| WU | 계약 | RED/GREEN 검증 |
|---|---|---|
| WU1 | Gmail envelope/parser + actor/count/score 계약 | focused pytest: pagination·actor·count 등식·score NOT_RUN |
| WU2 | payload/API 런타임 snapshot 배선 | focused pytest: 실제-shape snapshot → list/detail, malformed fail-fast |
| WU3 | 목록/상세/빈/오류 UI | 브라우저에서 네 상태를 직접 확인하고 콘솔 오류 0 |
| WU4 | 통합·배송 | pytest, ruff, mypy, verify.sh, adversarial V1/V2, clean push, Draft PR |

각 WU의 검증이 통과하기 전 다음 WU를 시작하지 않는다.

## 예외 케이스 표

| 예외 | 행동 |
|---|---|
| Gmail connector 권한/인증 실패 | `NOT_RUN:gmail_auth_unavailable`; 가짜 Batch 금지 |
| 검색 페이지 일부만 조회 | `NOT_RUN:gmail_pagination_incomplete`; PASS 금지 |
| 메시지 본문 MIME/HTML만 존재 | text 추출 근거가 없으면 message unparsed |
| 한 메일에 여러 포지션 | 명시 경계별 Batch 분할 근거가 없으면 한 Batch + NOT_RUN 사유 |
| 4축 점수 범위/축 누락/비정수 | 점수 NOT_RUN; 메일 총점 fallback 금지 |
| 후보 URL 없음 | unparsed 또는 excluded 근거에 따라 배타 분류 |
| 상세 후보 0명인 실제 메일 | Batch는 표시하되 원시 count ledger와 NOT_RUN 사유 표시 |
| 런타임 파일에 실제 후보 PII | Git 추적 금지; 0600 임시 파일만 사용 후 삭제 |
| 브라우저 오류 상태 확인 | 로컬 API 오류 주입만 사용; 외부 시스템 조작 금지 |
| 그 외 전부 | 명시적 중단 + 이 표 갱신 후 재개 |

## 표 ↔ 테스트 대응

- Gmail page 행: pagination success/empty-page-with-token/cycle/failure 테스트.
- actor 행: 각 5분류, 상충, 미지 actor 테스트.
- period 행: 정상/부분/역전 테스트.
- candidate 행: parsed/duplicate/unparsed/excluded 각각과 등식 property 테스트.
- score 행: 40/40/10/10 4축 정상/축 누락/비정수/총점-only 테스트.
- runtime 행: 정상 schema/list/detail와 version/field 오류 테스트.
- UI 행: PASS가 아닌 Gmail-only Batch, empty, injected error 화면 브라우저 확인.

## 비범위

- FU 채용사이트 검증과 Daily 재검증
- 이메일/제안/InMail 발송, draft 생성, 라벨 변경, archive/delete
- ClickUp/Supabase/원격 DB 쓰기
- v4 코드 복사 또는 실행
- merge/deploy

## 검증 명령

```bash
cd humansearch && uv run --no-sync pytest -q tests/test_admin_ai_search.py
cd humansearch && uv run --no-sync pytest -q
uv run --project humansearch --no-sync ruff check humansearch/src humansearch/tests
cd humansearch && uv run --no-sync mypy --strict src tests
bash verify.sh
bash scripts/acceptance-hs-gates.sh
```

## SOT 체크리스트

- [x] `docs/sot/` 현재 13개 파일 직접 확인
- [x] `st`, `harness`, `login`, `ai-search` 스킬과 ai-search 참조 2개 확인
- [x] strict 원칙 검사 `PASS 34/34`
- [x] recurrence ledger 부재 확인
- [x] 기존 worktree 재사용, ops-dashboard branch 무변경
- [x] 실제 Gmail pagination 4페이지 token chain 및 exhausted 증거
- [x] 외부 발송/채용사이트 변경/원격 DB write 0건 확인
- [x] 테스트 skip/only/todo 추가 0건, 삭제/약화 0건
- [x] Claude CLI 미인증 원문 확인 후 Codex V1 적대검증 PASS + V2 직접 재현
- [ ] 최종 HEAD/원격/CI SHA 귀속 확인

## 스펙 공격 질문

- `subject:aisearch` 밖의 실제 결과 메일이 존재하는가?
- MIME 본문/첨부에 후보가 있고 snippet에는 없는 형식이 존재하는가?
- 한 후보가 채널별 다른 URL로 반복되어 canonical identity가 갈리는가?
- 기존 메일의 점수가 40/40/10/10 네 축 입력 없이 숫자만 제공되는가?
- 검색 페이지 완료 후 메시지 batch read가 일부만 반환되는가?
- 수신시각과 메일 본문의 실행일시가 다른 경우 Batch ID와 실행일시를 무엇으로 구분해야 하는가?

위 질문은 실제 Gmail 표본을 읽은 뒤 답을 기록하고 parser fixture/테스트에 반영한다. 이 표가
완전하다고 선언하지 않는다.
