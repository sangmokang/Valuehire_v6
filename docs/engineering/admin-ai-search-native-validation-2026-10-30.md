# AI Search 실제 관리자 통합 — 검증 보고

작성일 2026-10-30 KST. **전체 완료가 아닌 Draft 검토 상태**다. 실제 Gmail 전수 읽기와 DB 적재,
기존 관리자 앱의 소스 통합을 수행했다. 브라우저 직접 확인과 개별 채널 이력 완료는 남아 있다.
머지·배포하지 않았다. 모든 수치는 이번 private staging/PostgreSQL readback이며 제품 기본값이 아니다.

## 1. 변경 파일

- `apps/admin-integration/`: 실제 관리자 페이지·표·Raw/고점수 모달·인증 API·URL 검사·테스트·설치기.
- `humansearch/src/humansearch/admin_ai_search/{collection,registry,normalize,contact_reports,storage_encoding}.py`:
  수집 장부, 영구 관계·표시번호, MIME 정규화, 보고서·Sent 컨택 근거, JSONB 문자 처리.
- 기존 `gmail_candidates.py`, `gmail_sent_contacts.py`, `gmail_subject.py`, `scoring.py`를 확장했다.
  stable identity·URL 정규화·기존 점수 계산·실행 주체·기존 shadow 소스는 유지한다.
- `tools/admin-ai-search/`: Gmail GET bridge, 첨부 파서 재사용, 서버 작업, DB 적재·검증·로컬 실제 RPC.
- `contracts/admin-ai-search/evidence-contract-v1.json`: v2 주간 행 정체성·고점수 90 기준·필수 네 채널.
- 관련 focused pytest, SQL 실증, 관리자 Vitest, SOT 및 통합 명세.

기존 작업트리와 PR을 이어받았다. 실제 관리자 호스트 소스 위치 및 격리 방법은
[통합 명세](admin-ai-search-native-spec-2026-10-30.md)에 있다. 기존 관리자 메인 작업트리의 사용자 변경은 보존했다.

## 2. DB migration과 테이블

`supabase/migrations/20261029090000_admin_ai_search_weekly.sql`을 추가했다.
실제 PostgreSQL 16의 격리 DB에 적용·적재했다. 연결된 기존 Supabase PostgreSQL 17에서도 추가 migration을
트랜잭션 안에서 실행하고 **ROLLBACK**해 제약을 확인했다. 프로덕션 schema는 적용하지 않았다.

`admin_ai_search_` 접두사의 collection_runs, source_messages, source_attachments, batches,
batch_source_messages, positions, candidates, candidate_batches, candidate_position_evaluations,
score_components, contact_events, contact_evidence, review_queue, collection_checkpoints, settings 총 15개다.
영구 표시번호 unique constraint, FK, 점수·상태 check, RLS, anon/authenticated 접근 차단을 포함한다.

## 3. 실제 Gmail 수집 범위

run `inbox-union-20261029`. 현재 계정에서 `02aisearch`를 다시 조회해
`Label_206388205034958356`임을 확인했다. 처음부터 끝까지 ID와 메타데이터·본문을 읽었다.

| 범위 | 최초 전체 페이지/메시지 | 마무리 확인 | 합산 고유 메시지 |
|---|---:|---|---:|
| Inbox | 154 / 76,577 | 시작 epoch 이후 delta 1페이지 / 5 | 76,582 |
| 02aisearch | 1 / 396 | 현재 라벨 전체 재확인 1페이지 / 397 | 397 |
| Inbox ∪ 02aisearch | — | message ID 교집합 15 제거 | **76,964** |
| Sent 별도 컨택 범위 | 49 / 24,315 | delta 1페이지 / 1 | 24,316 |
| 세 범위 전체 | — | 범위 간 중복 제거 | **100,085** |

6개 원장 범위 모두 `exhausted=true`, 마지막 next_page_token 없음. 모든 페이지 이력·조회 조건·label ID·
마지막 성공시각·체크포인트를 저장했다. 수집 시작은 10/29 22:12:21 KST,
마지막 성공은 **10/30 00:42:12 KST**다. 이 시간 이후 새 메일은 이 스냅샷에 포함하지 않는다.

기록된 retry_count는 9다. 초기 실행 HTTP 400 뒤 체크포인트로 재개했다. 최초 bridge가 Google 원문
오류 body를 남기지 않은 한계가 있어 그 최초 원문 전체는 복원할 수 없다. 현재 구현은 후속 실패의
원문·시도 이력을 보존한다. 일시 중단 후 저장된 페이지 ID부터 실제 재개한 것을 확인했다.

## 4. 처리 결과와 멱등성

| 범위 | PROCESSED | EXCLUDED | FAILED | REVIEW_REQUIRED |
|---|---:|---:|---:|---:|
| Inbox ∪ 02aisearch | 429 | 65,860 | 0 | 10,675 |
| Sent 포함 전체 | **437** | **79,400** | **0** | **20,248** |

EXCLUDED는 본문까지 읽고 비관련으로 분류한 메일 및 명시적 테스트 등이다. “검토용”만으로 제외하지 않는다.
검토 항목에는 후보 링크는 있으나 AI Search 여부가 입증되지 않은 메일, 읽기 어려운 본문·첨부가 포함된다.

- 현재 집계에 유효한 Batch: 확정 **0**, provisional **437**. 실행 ID/정확한 실행 증거가 없어 임의 확정하지 않았다.
- 현재 원문 해석의 관찰된 canonical 후보 **7,487명**, 후보+포지션 고유 조합 **8,977**.
- 주차별 후보+포지션 행 합계 **8,981**. 같은 조합의 복수 주차 등장을 보존한다.
- 과거 parser 해석도 보존해 저장된 후보 테이블 9,811명·평가 58,329건이다. 이 값은 현재 총 후보가 아니다.
- source_attachments 53,707개: PARSED 334 / REVIEW_REQUIRED 53,373. 비관련 메일 첨부도 메타데이터를 보존했다.
- review queue OPEN **44,519건**. 메일 수와 다르며 한 메일에 여러 사유가 있을 수 있다.
- 정상화 재실행: **100,085 unchanged**, 신규·갱신·실패 0. 실제 PostgreSQL 재적재 전후 ID/표시번호 hash와
  후보+포지션·주차 행·컨택·원문 수가 같은지 비교했다. 근거 로그는 private artifacts에 보존한다.

기존 해석의 provisional 번호도 예약을 유지한다. 실제 자료의 100 이상 순번에서 문자열 잘림을 발견해
최소 두 자리 표시로 수정했고, 이후 ID/표시번호를 재수집으로 정렬하거나 재사용하지 않았다.

## 5. 주차별 집계

기존 주간 회의 W라벨과 실제 일~토 기간을 함께 표시한다. 모든 선택 주차에서 후보 해석 또는 컨택/점수
검증이 불완전하므로 총 후보·JD 발송·고점수 미컨택자를 확정 숫자로 표시하지 않는다.

| 주차 / 기간(2026) | 확정 Batch | provisional | 확인 포지션 | 관찰된 고유 후보 | 후보+포지션 행 | 총 후보 / JD 발송 / 고점수 미컨택 |
|---|---:|---:|---:|---:|---:|---|
| W45 / 10.25~10.31 | 0 | 47 | 37 | 449 | 595 | 미확인 / NOT_RUN / NOT_RUN |
| W44 / 10.18~10.24 | 0 | 120 | 60 | 797 | 805 | 미확인 / NOT_RUN / NOT_RUN |
| W43 / 10.11~10.17 | 0 | 110 | 74 | 957 | 1,036 | 미확인 / NOT_RUN / NOT_RUN |
| W42 / 10.04~10.10 | 0 | 59 | 54 | 4,115 | 4,586 | 미확인 / NOT_RUN / NOT_RUN |

확정 0은 “확정 근거를 충족한 Batch가 없음”이다. provisional 실행이 없다는 뜻이 아니다.
포지션 수는 고객사+포지션이 확인된 조합만 포함한다. 미확인 고객사·포지션은 추정하지 않는다.

## 6. 채널별 실제 컨택 확인

| 채널 | 개별 후보+포지션에 귀속된 양성 컨택 | 완전한 음성 확인 | 현재 상태 |
|---|---:|---:|---|
| 사람인 | 0 | 0 | NOT_RUN · 개별 이력 보고 연결 전 |
| 잡코리아 | 0 | 0 | NOT_RUN · 개별 이력 보고 연결 전 |
| LinkedIn | 0 | 0 | NOT_RUN · 개별 이력 보고 연결 전 |
| Gmail | 0 | 0 | 29개 미연결/의도 검토 이벤트 보존 |

Sent 전수 중 인식된 직접 제안 원문은 **23건 = AI 7 / OWNER 14 / UNKNOWN 2**다.
추가 `[포지션]` 메일 **6건(OWNER)**은 발송 의도가 명확하지 않아 직접 제안으로 확정하지 않았다.
이 29개는 모두 안전한 후보+포지션 연결이 없어 REVIEW_REQUIRED다. 이름·수신자만으로 연결하지 않았다.

기존 자유 형식 보고에서 사람인 기발송 17건, 잡코리아 해당 일자 발송 2건이라는 **메일 보고 수치**를
발견해 출처와 원문으로 보존했다. 이 수치는 검증된 개별 후보 컨택이나 채널 누적 총계가 아니다.
새 그록봇의 전 채널 개별 근거가 완비된 보고는 현재 수집 스냅샷에서 확인하지 못했다.
`ai-search-contact-report/v1`을 지원하며, 자유 형식 보고도 삭제하지 않고 검토 대기로 보존한다.

## 7. 미확인 필드와 NOT_RUN

- 네 구성 점수의 증거가 모두 있는 실제 후보는 0명이다. 메일 원본 총점과 별개로 검증 점수는 NOT_RUN이다.
- 실행시각 근거가 없으면 received_at_fallback과 LOW confidence를 표시한다. 수신시각을 실제 실행시각으로 단정하지 않는다.
- 모든 채널의 후보+포지션별 이력 pagination 완료가 없다. 미컨택 확정과 고점수 미컨택 집계는 NOT_RUN이다.
- 이름·학력·전체/핵심 경력·필수요건·대안 포지션·사람 후속 조치가 원문에 없으면 원문과 사유를 보존하고 미확인으로 표시한다.
- 학력·경력 문장의 모든 형태를 해석한 것은 아니다. 지원하지 못한 구간·첨부는 review queue와 Raw에 남긴다.
- source total이 없거나 후보를 일부 파싱하지 못한 장부는 counts_status NOT_RUN이다. 확인 가능한 장부에만 등식을 검증한다.

## 8. 원문 표본 대조

비공개 `source-audit.json`에 10개 범주(일부 동일 원문)를 기록했다. 상세 후보형, 축약 8명 목록,
HTML 표, 첨부, 테스트, 후보 0명, 과거 parser 실패 후 재처리, AI 발송, OWNER 발송, 미연결 발송이다.
원문 checksum·canonical URL·후보 구간의 원문 포함 여부를 확인한 표본은 모두 일치했다.
테스트는 제외 사유를 유지했고, 첨부가 해석돼도 AI Search 결과임이 확정되지 않으면 후보를 생성하지 않았다.

실제 다중 고객사/포지션을 안전하게 분리한 표본과 동일 실행 다중 알림의 확정 표본은 확보하지 못했다.
해당 두 항목은 인위적으로 만든 단위 fixture에서 검증했으며 실제 원문 대조 PASS로 보고하지 않는다.

## 9. 실행한 테스트와 검증

- focused pytest RED → GREEN: 수집 합집합·checkpoint·실패 이력·재개, URL 식별자, 주차 경계,
  Batch 영구번호·확정 전환, 다중 포지션·점수 구간, 불완전/상충 컨택, 원문 NUL.
- HumanSearch 전체 pytest **300 passed**. ruff PASS, mypy strict **66 source files PASS**.
- 저장소 Python 전체 및 Invoice/배선 pytest: **357 passed, 94 subtests passed**.
- 기존 관리자 Vitest **20 passed / 3 files**, 기존 앱 TypeScript `tsc --noEmit` PASS.
- `bash verify.sh`: `PASS: no secret-pattern match in any tracked file, .env not tracked`.
- 기존 acceptance-hs, mutation/antiforge, Invoice 57 단위 및 실제 PostgreSQL integrity PASS.
- 실제 PostgreSQL migration/check PASS. 100 이상 번호, provisional 확정 후 P번호 예약, 현재/과거 parser 분리,
  0명 Batch, 필터·집계 범위, 오래된 미발송 근거 배제, 완전한 양성 고점수 미컨택 fixture, RLS와 익명 권한을 SQL로 검증했다.
- 실제 service-role RPC 7종과 비인가 RPC 403, 원문 이력·Gmail 링크·빈 결과·고점수 미확인 readback PASS.
- 실제 Next 익명 API **401**, 익명 페이지는 로그인 redirect를 스트리밍하고 보호 표를 렌더링하지 않음을 확인했다.
  인증 성공 분기는 기존 세션 guard 단위 테스트와 실제 service-role PostgreSQL readback으로 확인했다.
- pre-push 27개 검사 중 semantic mutation은 검사 중 문서가 변경돼 한 차례 실패했다. 변경 없이 재실행한
  semantic mutation **16 checks PASS**. 최종 정상 push에서 전체 **27개 검사 PASS**. 훅 우회 없이 기존 브랜치에 push했다.

2026-10-30 과거 검증에서는 페이지 진입 전에 Chromium이 종료됐다. 실패 원문은 private `browser-validation.log`에 저장했다.

```text
browserType.launch: Target page, context or browser has been closed
FATAL:base/apple/mach_port_rendezvous_mac.cc:159
Check failed: kr == KERN_SUCCESS.
bootstrap_check_in org.chromium.Chromium.MachPortRendezvousServer: unknown error code (141)
```

따라서 당시 로그인 후 목록·Raw·고점수 모달·빈/오류·모바일 가로 스크롤의 **직접 브라우저 확인은 NOT_RUN**이었다.
이번 직접 확인 결과는 §16에서 구분한다.
정적 코드·API 테스트를 브라우저 성공으로 대체하지 않았다. 참고 사이트 열기도 도구 오류로 실패해 숫자·후보를 복제하지 않았다.

## 10. 외부 변경

- 외부 이메일·제안·InMail 발송 **0건**.
- Gmail 라벨 변경·보관·삭제 **0건**.
- 사람인·잡코리아·LinkedIn 수정 **0건**.
- 프로덕션 영구 DB 변경 **0건**. 모듈 migration 원격 실증은 ROLLBACK, 실데이터는 격리 로컬 PostgreSQL에 저장했다.
- 머지·배포 **0건**. GitHub의 기존 작업 브랜치·Draft PR·Issue 갱신만 수행한다.

## 11. 접속 URL

- 실제 기존 관리자 앱의 로컬 경로: http://127.0.0.1:8767/admin/ai-search-weekly (기존 관리자 로그인 필요).
- 향후 제품 경로: https://admin.valuehire.cc/admin/ai-search-weekly — **미배포**, 현재 운영 화면에 추가됐다고 주장하지 않는다.
- 기존 shadow 8766은 제품 완료 증거가 아니다.

## 12. Issue

https://github.com/sangmokang/Valuehire_v6/issues/142 — 남은 인수 조건이 있어 open 유지.

## 13. Draft PR

https://github.com/sangmokang/Valuehire_v6/pull/140 — 기존 브랜치·Draft를 유지한다. 중복 PR을 만들지 않는다.

## 14. 남은 위험과 다음 작업

1. 실행 근거가 완비된 원문으로 provisional을 확정하고 다중 알림·다중 고객사 실제 표본을 추가 검증한다.
2. 그록봇 채널별 보고의 후보 식별자·포지션·발송 reference·전체 조회 완료 근거를 연결한다. 미연결 수치만으로 미컨택/발송을 확정하지 않는다.
3. 대량 review queue를 원문 근거로 정리하고 지원 본문·첨부 형식을 늘린다. 점수 네 축은 정본 근거가 생길 때만 계산한다.
4. Chromium 실행이 가능한 환경에서 실제 관리자 로그인 후 필수 브라우저 시나리오를 수행한다.
5. 운영 적용은 별도의 검토 대상이다. 기존 관리자 호스트 소스 통합과 추가 migration을 검토한 뒤 승인된 절차로 적용한다. 이번 작업에서 merge/deploy하지 않는다.

## 15. 2026-10-31 후속 — 실행 주체 전체 분류와 주차 공통 Batch 번호

Gmail을 다시 내려받지 않았다. 저장된 원문 100,085건을 parser `2026-10-31.5`로 재정규화했다(7분 38초,
PROCESSED 437 / EXCLUDED 79,400 / REVIEW_REQUIRED 20,248 / FAILED 0 — 처리 상태 수치는 이전과 동일).

- 실행 주체: 제목 첫 실행 토큰 → 발신자(OpenAI 작업 알림) → 본문 `실행 주체:` 라벨 순으로 명시 근거만 쓴다.
  충돌·미지원·판단 불가는 OTHER와 사유를 남긴다. `CODEX`, `ASIDE`를 추가했다.
- 결과 메일(PROCESSED 437): ChatGPT 143 · Claude Code 109 · Codex 39 · Grokbot 30 · Aside 11 ·
  일반 AI Search 29 · OTHER 76(제목에 도구 표시 없음 60, `Claude-win` 16 — Claude Code 여부 원문상 미확정).
- 검토 대기 원문에도 분류를 기록한다. ChatGPT 작업 알림 138건은 발신자 근거로 CHATGPT지만
  후보 프로필 링크가 없어 Batch를 만들지 않고 검토 대기로 둔다.
- Batch 번호: 실행 주체·확정 여부와 무관하게 주차 공통 순번이다. 기존 895개 P번호 Batch는 내부 ID를
  유지한 채 한 번만 새 번호를 받았고 이전 번호는 `display_number_history`에 남았다(남은 P번호 0,
  연도+주차+순번 중복 0). 확정 Batch는 여전히 0이다. 과거 parser 해석의 비활성 Batch도 번호를
  보존하므로 활성 목록에는 빈 번호가 있다(예: W45-02).
- PostgreSQL은 `sequence NOT NULL`이고 표시번호는 주차+순번에서 파생됨을 CHECK로 강제한다. 레거시 P 전환은
  적재 전 SQLite 등록기에서만 한다. 적재기는 Batch 등록과 SQLite 표시번호 대조를 한 트랜잭션으로 수행하며
  하나라도 다르면 Batch 쓰기 전체를 되돌린다(스크래치 DB에서 불일치 시 롤백 실증). 실데이터 895건 대조 통과,
  migration-check(공통 순번·확정 시 번호 유지·NULL 순번 거부·W45-100 무잘림) 및 runtime-check PASS.
- 주차별 실행 주체별 Batch(활성 원문 기준): W45 Grokbot 26 · ChatGPT 10 · 일반 7 · 기타 4 /
  W44 ChatGPT 73 · Aside 11 · Codex 7 · Claude Code 7 · Grokbot 4 · 일반 13 · 기타 5 /
  W43 ChatGPT 54 · Claude Code 23 · Codex 12 · 일반 3 · 기타 18 / W42 Claude Code 44 · Codex 12 · ChatGPT 1 · 기타 2.
- 컨택 보고서 41건에 보고 실행 주체를 컨택 발송 주체와 따로 기록했다(Claude Code 7 · 일반 3 · Aside 2 ·
  ChatGPT 1 · Codex 1 · Grokbot 1 · OTHER 26). 총계만 있는 보고는 후보에게 배분하지 않는다.
  Sent 직접 제안 29건(AI 7 / OWNER 20 / UNKNOWN 2)은 후보+포지션 안전 연결이 없어 모두 REVIEW_REQUIRED다.
  개별 후보에 귀속된 양성·완전 음성 컨택은 네 채널 모두 0건 → 화면은 '확인 필요(NOT_RUN)'.

### 브라우저 직접 확인 (기존 CDP 127.0.0.1:9333, 새 탭 1개만 사용 후 닫음)

로그인 후 http://127.0.0.1:8767/admin/ai-search-weekly 에서 확인했다. 관리자 API 응답 10건 모두 200.

- 최근 4주 2026 W45(10.25~10.31)~W42(10.04~10.10), 일~토 기간 표시. W45 595행, 2페이지 51~100 이동.
- Batch 칸: `W45-55 (provisional)` · Grokbot · 근거 `subject_marker:grok` · 이전 표시번호 `W45-P55`.
- W44 실행 주체 Codex 필터 17행(요약 Codex 7), Batch 번호 `W44-88` 필터 14행 전부 해당 번호 포함.
- 상세 Raw: 포지션별 평가·메일 원본 점수·계약 점수 구성 4개·Gmail 원문 링크·검토 대기 사유 표시.
- 고점수 미컨택: 'NOT_RUN · 점수 또는 채널별 이력 확인이 완료되지 않았습니다.'
- 이전 세션의 390px 확인에서는 페이지 가로 넘침이 있었다. 당시에는 공통 레이아웃 문제로 남겼다.
  이번 후속에서는 이 페이지에 한정해 수정했고 §16에 실제 측정값을 남긴다.

로컬 Google 로그인 콜백은 `127.0.0.1:8767`에서 세션을 발급했다. `localhost:8767`로 시작하면 운영
로그인 화면으로 이동해 즉시 중단했다(운영 쪽 조작 0건).

### 검증

- HumanSearch pytest 345 passed, ruff PASS, mypy strict 27 source files PASS.
- 관리자 Vitest 17 passed(2 files). `tsc --noEmit`: AI Search 관련 오류 0. 단, dev 서버가 생성한
  기존 `/weekly` 페이지 타입에서 TS2344 1건이 나온다(이번에 수정하지 않은 기존 파일).
- `bash verify.sh` PASS. Codex 적대 검증 V1(needs-attention 2건) → 수정. 리셋 컨텍스트 V2는 3회 FAIL
  (본문 다중 도구 라벨, PG NULL 제약, 적재 번호 대조·원자성, 부분 일치 토큰 등) → 매번 RED→수정, 4회차 PASS.
- 남은 하 등급: 적재 실패 시 Batch보다 먼저 적재된 원문·포지션·후보 테이블은 남는다(번호 무관).
  본문 라벨이 `Codex (검증 완료)`처럼 부가어가 붙으면 OTHER로 보수 처리한다.
- CI `verify`는 `suppressions.yaml` 억제 3건의 기한(2026-10-20) 경과로 실패한다. 지시대로 연장하지 않았다.

## 16. 2026-10-31 후속 재개 — Gmail 증분과 실제 모바일 수정

시작 HEAD f509ca98dd1248c988acc10b1dbb02f279acf8c8. 위 §1~15의 수치는 이전 세션 이력이다.
기존 관리자와 사용자 변경을 비교한 뒤 같은 CSS/표시 수정만 반영했다. 호스트 migration에 누락됐던
표시번호 CHECK 한 줄을 PR의 migration과 맞췄다. next-env.d.ts·메뉴 등 기존 사용자 변경은 보존했다.

### 실제 새 수집과 정규화

- 수집 run `incremental-20261031`, 마지막 성공 **2026-10-31 21:36:46 KST**.
- Inbox/Sent query `after:1793279541`(이전 성공 run 시작시각), AI 라벨은 전체 ID 재확인.
  Inbox 102 / 02aisearch 408 / Sent 27, 각 1페이지, 모두 마지막 토큰 없음.
- 세 범위 ID 합집합 531. 새 본문 **128**, 정상 저장 본문 재사용 **403**, 본문 갱신 0.
  도구명 검색 0, 기존 100,085건 전수 본문 재다운로드 0. 원문 총 **100,213**.
- PROCESSED **449** / EXCLUDED **79,492** / REVIEW_REQUIRED **20,272** / FAILED **0**.
  새 원문 128건은 12 / 92 / 24 / 0이며, 새 결과는 일반 AI Search·Grokbot·OTHER로 분류됐다.
  Claude Code·Codex·ChatGPT·Aside도 같은 전 범위 수집/분류 경로를 유지한다. 이번 신규분이 없다고
  과거 해당 도구 결과를 제외하지 않는다.
- 파서 `.6`은 증분 run의 531건부터 적용했다. 나머지 저장 원문을 모두 재정규화하지 않았다.
  맹그로브·코드잇·토트의 다중 고객사 제목을 단일 고객사로 확정하지 않는다. ABB Robotics Korea
  라운드 보고는 회사 전체 이름을 보존하고 개별 포지션은 NOT_RUN이다. 일반 브리핑 제목을
  고객사/포지션으로 분해하지 않는다. 세 실제 제목을 회귀 입력으로 사용했다.
- 기존 **895**개 Batch의 내부 ID·표시번호 전부 보존. 총 **907**, 모두 provisional,
  연도·주차·순번 중복 **0**. 과거 번호를 메우거나 다시 정렬하지 않았다.
- 격리 로컬 PostgreSQL `127.0.0.1:6544` 적재 PASS. source/normalized 각각 100,213.

### 실제 컨택 근거의 한계

Gmail 이벤트는 **30**건이며 모두 후보+포지션 연결 대기다. 네 채널의 확정 양성/완전 음성은
새로 입증하지 못했다. 사람인·잡코리아 응답 알림의 이름/수신자만으로 연결하지 않았다.
비스텔리전스 보고의 발송 주장 **42**(사람인 6 / 잡코리아 36), 토트 보고의 사람인 발송 주장 2,
두나무 보고의 LinkedIn 개별 컨택 주장은 원문 증거로 보존한다. 플랫폼 발송 reference 또는
정확한 후보+포지션 연결이 부족해 검증 컨택 수로 승격하지 않는다. `sent_log.md` 언급만으로
그 파일을 확인했다고 주장하지 않는다. 새로운 보고도 contact_evidence/review queue에 남긴다.
지원하지 않는 새 보고 첨부(xlsx/markdown 4개)는 검토 대기다. 네 점수 축은 생성하지 않는다.

### 이번 직접 브라우저 확인

기존 CDP **127.0.0.1:9333**과 기존 로그인 세션을 사용했다. 전용 임시 탭만 사용 후 닫았고
기존 창·탭·세션을 보존했다. 접속 URL은 **http://127.0.0.1:8767/admin/ai-search-weekly**.

- 최근 4주 W45~W42와 실제 일~토 기간, W45 **718행**, 다음 페이지 **51~100**, 이전 이동.
- W44 Codex 필터 **17행**, `W44-88` Batch 필터 **14행**, 전체 Batch/과거 번호 표시.
- 상세 Raw의 포지션별 평가·메일 점수·네 구성 점수·전체 이력·검토 사유와 Gmail 링크 확인.
- 네 독립 채널, LinkedIn/NOT_RUN 필터, 미확인 점수·고점수 미컨택 모달, 검색 빈 결과 확인.
- 실제 정상 관리자 API 응답 **17건 200**. 오류 표시는 브라우저에서 의도적으로 503을 주입한
  **통제 시나리오 1건**이며 실제 서버 장애였다고 주장하지 않는다. pageerror 0.
- 390px: 문서 scrollWidth **375**, 표 clientWidth **326** / scrollWidth **2450**,
  scrollLeft **400**. 페이지 전체 가로 넘침 없이 표 내부 가로 스크롤. 사이드바 접힘 높이 0.
  CSS는 이 페이지를 포함한 shell에만 적용하고 기존 관리자 공통 소스는 수정하지 않았다.
- 첫 시도는 DB 적재 도중 부분 상태를 읽었다. 이후 적재 성공 후 확인했다. 추가 자동 검증에서는
  React 반영/전환 완료 전에 측정한 문제를 응답·geometry 대기로 교정했고, 통과한 시나리오는 반복하지 않았다.

### 이번 변경 검증

collection/정규화/컨택/실제 제목 focused **42 passed**, 재개·빈 ID 반례 수정 후 collection **13 passed**.
ruff PASS, mypy strict **14 source files PASS**. 관리자 Vitest **21 passed / 3 files**.
TypeScript는 기존 `.next/dev/types/app/weekly/page.ts:37`의 **TS2344 1건**이 현재 재현되며
이번 변경 파일 오류는 없다. `bash verify.sh` PASS. 캐시 재사용을 끈 수동 mutant는 회귀 테스트가 차단했다.
Claude CLI 적대검증은 미로그인 exit 1로 실행 불가였고, fresh Codex V1/V2로 대체한다.
V1의 Sent 범위 추가 반례, V2의 pending refresh 누락·빈 run ID 전수 fallback을 각각
임시 DB에서 RED로 재현한 뒤 최소 수정했다. 같은 범위/refresh 재개는 저장된 본문부터 복구한다.
옵션 필드가 없던 기존 run도 checkpoint/active scope로 첫 pending delta를 감지하는 legacy 회귀를 통과했다.
최종 fresh Codex V1/V2 PASS. V2는 collection/followup 31 tests와 임시 16개 중단·재개 사례를
독립 확인했다. 별도 엔진의 검토를 실제 Gmail/브라우저 확인으로 확대해 주장하지 않는다.
기존 suppressions.yaml 만료 3건은 그대로이며 만료일을 연장하지 않았다.
필수 배송 게이트·교차 판정의 최종 결과는 기존 PR #140의 최신 본문에도 기록한다.
최초 pre-push에서 격리 mutation fixture의 normalize CLI 미복사와 기존 macOS UID501 조회 문제가
드러났다. 실제 CLI를 fixture에 추가했고, PostgreSQL은 기존 artifacts/pg-bin wrapper를
`PG_BINDIR`로 지정해 원래 검사를 실행했다(Invoice 8항목 PASS). 검사·assertion은 약화하지 않았다.

외부 발송·Gmail/채용사이트 변경·프로덕션 DB 적용·merge/deploy는 수행하지 않았다.
UI 구현·직접 브라우저 확인과 실제 전 채널 컨택/점수 근거 확보를 구분한다. 후자는 여전히 미완료다.
