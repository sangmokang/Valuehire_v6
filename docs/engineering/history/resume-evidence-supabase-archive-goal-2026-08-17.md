> **v4 전제 역사 기록 — 실행 금지.** 이 문서는 2026-08-17 에 `task/resume-evidence-supabase-prompt` 워크트리의 미추적 파일로 작성됐고, "기존 ValueHire v4 프로필 아카이버를 재사용"을 전제로 한다. 사장님 결정(2026-08-14 v1~v5 의존 0)과 충돌하므로 v6 설계서가 아니다. 보존 이유: 8개 counter-AC(구간 무누락 manifest·마지막 화면·NULL 구분·회사별 duty·검색 조건 보존·원격 경로 금지·readback·회사 별칭)와 2026-08-17 실측 수치가 v6 클린룸 계약(WU-0B, `docs/sot/humansearch-evidence-contract.md`)의 시험 문제로 쓰인다. 2026-09-09 회수, 본문은 원문 그대로(sha256 아래).
> 원문 sha256: 0dc136b99df6f4a41d007e29eff51517b27ca740d96190701af319f271ed6d4b

# 채용 증거 아카이브·조직분석 구현 프롬프트 goal

## 1층 결론

이번 작업의 산출물은 사람인·잡코리아·LinkedIn Recruiter/RPS의 검색 결과와 후보자 상세 페이지를 재현 가능한 증거로 보존하고, 연봉·회사별 수행업무를 SQLite 정본에서 Supabase 파생본과 Organization Analysis로 안전하게 연결하는 **검증된 구현 프롬프트**다. 기존 ValueHire v4 프로필 아카이버를 재사용하되, 단순히 스크린샷 장수를 늘리는 것으로 완료하지 않는다. 긴 페이지의 처음부터 끝까지 구간 무누락, 검색 페이지별 필터·페이지네이션 보존, 민감정보 보존·삭제 계약, 배치 적재 후 원격 readback, 회사 식별자 정규화와 분석 뷰를 합격 조건으로 만든다.

원문 이미지와 이력서 원문은 민감한 원본 자산이다. SQLite를 정본으로 유지하고, Supabase에는 승인된 열만 보내며, 원본 이미지는 암호화된 객체 저장소와 보존기간·삭제 영수증이 준비된 뒤에만 전송한다. 그 전에는 로컬 원본과 해시·구간 메타데이터만 유지한다.

## 2층 판단 근거

### 결정 카드

> **무엇을** — v4의 동작 중인 프로필 아카이버를 기반으로 증거 manifest, 검색결과 archive, salary observation, career duty observation, company identity, export batch/readback, Organization Analysis 뷰를 보강하는 구현 계약을 작성한다.
>
> **왜** — v6에는 실행 파이프라인이 없지만 v4에는 이미 실제 로컬 캡처와 SQLite→Supabase 배치가 있다. 새로 만드는 것보다 검증되지 않은 경계만 닫는 편이 빠르고 안전하다.
>
> **버린 길** — ① v6에서 전면 재작성: 작동 중인 796건·12,848장 자산을 버리고 회귀 위험을 만든다. ② 스크린샷 파일을 Supabase 행의 로컬 경로로만 저장: 원격에서 읽을 수 없는 거짓 자산이다. ③ 후보자 원본을 곧바로 공개 스키마에 복제: 보존·삭제·접근통제 계약이 없어 개인정보 위험이 크다.
>
> **대가** — 구간별 좌표/해시와 readback 검증 때문에 캡처·동기화 시간이 늘고, 원본/구조화 데이터의 보존 정책을 분리 운영해야 한다.
>
> **되돌리기** — 이번 작업은 문서·시험 설계만 추가한다. 제품 변경은 후속 구현 worktree에서 독립 커밋으로 수행하며, 해당 커밋 revert와 export feature flag 비활성화로 되돌린다.

## 메타

- 작성일: 2026-08-17
- branch/worktree: `task/resume-evidence-supabase-prompt` / `worktrees/resume-evidence-supabase-prompt`
- 위험등급: L3 — 실제 후보자 PII, 외부 채용 플랫폼, Supabase 파생본, 조직 분석에 영향
- SQLite: 유일한 정본
- Supabase: 승인된 파생본, 역방향 갱신 금지
- 배송 중단선: 구현 프롬프트·검증 증거·Notion 저장·이메일 초안까지. 제품 코드 구현, 라이브 후보자 원본의 신규 Supabase 전송, 이메일 자동 발송은 비범위다.

## 현재 사실과 근본 원인

| 사실 | 증거 | 의미 |
|---|---|---|
| v6 HumanSearch는 패키지 경계와 게이트만 있고 캡처 런타임이 없다 | `humansearch/src/humansearch/__init__.py`, `humansearch/tests/test_package_boundary.py` | v6에 새 캡처를 바로 구현할 SOT가 없다 |
| v4에는 프로필 스크린샷·DOM·SQLite·명시적 Supabase batch가 있다 | `Valuehire_v4/tools/profile-archiver/README.md`, `server/index.js`, `extension/background.js` | 기존 구현을 기준선으로 삼아야 한다 |
| 운영 로컬 DB에 796 archives, 유효 연결 screenshots 12,848개가 있다 | 2026-08-17 로컬 SQLite 집계(식별정보 미출력). 부모 없는 screenshot 행 6개와 DB 미참조 파일 2개도 확인 | 장기 운영과 다장 캡처는 가능하지만 정합성 청소가 필요하다 |
| live `profile_archives`는 1,386행이며 salary/career/structured 필드가 존재한다 | 2026-08-17 Supabase PostgREST schema + HEAD count | 스키마를 새로 복제하기보다 실제 필드를 확장해야 한다 |
| 현 캡처는 `doc_height`·구간 좌표·coverage manifest를 완전하게 남기지 않는다 | v4 schema와 append 경로 검사 | 장수만으로 전체 페이지 무누락을 증명할 수 없다 |
| 현 batch는 행 upsert 후 원격 readback을 하지 않는다 | `server/index.js`, `server/sync-batch.js` | 성공 응답과 실제 원격 정합성을 구분할 수 없다 |
| 검색 목록 전체 보존은 플랫폼별 일관된 합격 조건이 아니다 | v4 host-permission smoke와 resume-detail 판정 | 사람인·잡코리아·RPS 페이지네이션 자산화가 부분 구현이다 |
| `profile_archives` 생성 migration에 RLS enable/policy가 없다 | `supabase/migrations/20260530000000_profile_archives_sync.sql` | live policy 확인 전 raw Supabase export를 안전하다고 볼 수 없다 |

**근본 원인:** 현재 아카이버의 완료 정의가 “요청이 저장되고 스크린샷 배열이 늘었다”에 가깝고, 사용자가 필요한 “전 구간 재현 가능성·구조화된 영업 인텔리전스·원격 정합성”을 계약으로 강제하지 않는다.

## 원자적 AC

**When 후속 구현 프롬프트가 실행 완료됐을 때, the system은 지원 플랫폼의 검색 페이지와 후보자 상세 페이지를 SQLite 정본에 재현 가능한 evidence manifest로 저장하고 승인된 파생 필드를 Supabase에 idempotent batch export한 뒤 readback으로 검증해야 하며, If 화면 구간 누락·필수 연봉/회사별 수행업무 상태 미분류·회사 식별자 미해결·원본 보존정책 미승인·원격 불일치 중 하나라도 있으면 then 해당 archive/export/analysis를 `PASS`로 표시해서는 안 된다.**

### counter-AC

1. 스크린샷이 여러 장이지만 스크롤 delta가 viewport보다 커 중간이 비었다 → FAIL.
2. 긴 페이지 마지막 화면을 찍지 않았지만 요청이 200이라 완료 처리했다 → FAIL.
3. salary가 없다는 사실과 추출 실패를 둘 다 `NULL`로 저장했다 → FAIL.
4. 회사별 수행업무를 전체 resume text 안에만 묻어두고 회사 단위로 조회할 수 없다 → FAIL.
5. 검색 URL만 저장하고 필터·페이지 번호·결과 수·목록 텍스트/이미지를 저장하지 않았다 → FAIL.
6. Supabase에 로컬 파일 경로만 적어 원격에서 원본을 읽을 수 없다 → FAIL.
7. Supabase upsert 응답만 성공이고 row count/hash readback이 없다 → FAIL.
8. 동명이인 회사 또는 한·영문 별칭을 free-text로 합쳤다 → manual review 전 분석 제외.
9. 보존기간 만료 후 원본은 삭제됐는데 파생 테이블과 링크가 계속 노출된다 → FAIL.
10. LinkedIn/RPS에서 허용되지 않은 자동화 범위를 사람이 승인한 캡처와 구분하지 않는다 → FAIL.

## 검증 계약

- 긴 페이지 fixture: 최소 3종(약 4k/20k/100k px), iframe·sticky header·동적 확장·가상 목록 변형 포함.
- 구간 증거: `scroll_top`, `viewport_height`, `document_height`, `content_hash`, `image_hash`, `previous_segment_id`, `overlap_px`, `captured_at_monotonic`.
- 합격: 첫 구간 `scroll_top=0`, 마지막 구간이 문서 하단 도달, 인접 구간 gap 0, 순서 연속, 중복은 명시적으로 dedupe, text와 screenshot manifest 모두 존재.
- 검색 증거: 플랫폼·검색 실행·필터 snapshot·페이지 index/cursor·표시 결과 수·목록 item identity hash·텍스트·스크린샷을 페이지마다 저장.
- 구조화 필드: salary observation과 company-duty observation은 원문 evidence span과 extractor version을 가진다.
- batch: SQLite high-water mark, whitelist version, source row count, accepted/rejected, payload hash, retry, remote readback count/hash를 기록한다.
- 개인정보: 원본의 저장 위치·암호화·접근 역할·보존기간·삭제 작업·삭제 영수증이 승인되지 않으면 live raw export는 `NOT_RUN`이다.

## Harness 상태

| Gate | 상태 |
|---|---|
| 0. SOT·기존 구현·live schema 읽기 | PASS |
| 1. goal/AC/중단선 | PASS |
| 2. 기존 테스트와 장문 캡처 RED/기준선 계측 | PASS |
| 3. 구현 프롬프트·DB/비즈니스 계약 작성 | PASS |
| 4. Claude 1차 공격 감사 | BLOCKED_FILTER/NO_VERDICT |
| 5. Codex 2차 재공격·수정 확인 | PASS(교차엔진 일치 판정은 NOT_RUN) |
| 6. 저장소 verify + Notion readback + 이메일 draft readback | PASS |

## 비범위와 안전선

- 실제 후보자 PII나 원본 스크린샷을 git에 저장하지 않는다.
- 본 작업에서 새로운 live 원본을 Supabase에 전송하지 않는다.
- LinkedIn/RPS 자동화의 약관·권한이 불명확한 경로는 human-driven evidence capture로 제한한다.
- 이메일은 strict 모드 안전선에 따라 발송하지 않고 draft까지만 만든다.
- Supabase RLS 정책은 DB 권한으로 직접 확인하지 못하면 추측하지 않고 `NOT_RUN`으로 남긴다.

## 검증 로그

후속 정적 검증·적대검증·Notion/Gmail readback 결과를 이 절에 누적한다. 빈 출력 또는 실행 불가를 통과로 간주하지 않는다.

### 2026-08-17 기준선

- 기존 smoke 5종: archive append, auto capture, human capture, host permission, mock Supabase explicit batch 모두 exit 0.
- 기존 smoke 반례: manual/채널 capture의 첫 screenshot이 900~1,800px여도 통과.
- 최종 강화 재검증 2회: 4,261px 9~10장/11.839~14.159s, 20,061px 59~60장/46.780~48.493s, 100,061px 279~293장/181.945~209.276s.
- 세 case 모두 실제 browser document height 기준 start 0, bottom reach, gap 0, geometry 유효, sequence 연속, session/archive/row 장수 일치, image hash 고유로 PASS.
- 1차 run의 screen capture latency p50 56~57ms, p95 최대 266ms, max 559ms. 2차 독립 run은 p50 55~57ms, p95 최대 294ms, max 1,155ms였다. retry와 flush를 포함한 실효 장당 평균은 실행별 변동이 있으므로 총시간/장수를 함께 저장해야 한다.
- 20k/100k는 보조 이벤트 retry 비율 48.3%/46.2%로 높아 제품 상태기계의 bounded retry가 필수.
- 최초 validator의 `doc_height=NULL` false PASS와 마지막 memory frame/DB 장수 비교 누락을 순차 공격으로 발견해 수정하고 전 case 재실행.
- 현재 fixture는 긴 단일 합성 본문만 검증한다. iframe, sticky header, 동적 확장, virtualized list, 검색 pagination, 연봉 variant, 실제 채널 DOM은 구현 후 별도 RED/GREEN fixture와 승인된 live sample 검증 대상이며 현재 `NOT_RUN`이다.
- 운영 유효 screenshots 12,848의 연결 파일 누락 0. 부모 archive 없는 screenshot 행 6, DB 미참조 file 2는 정합성 결함.
- 운영 image file 12,850개: 평균 255,403 bytes, p50 241,132, p95 448,556, max 1,570,371.

## 적대 검증 로그

### V1 — Claude 다른 엔진

검증 명령 계열은 모두 `env -u ANTHROPIC_API_KEY claude -p`로 실행했고 §8-7 출력 형식 전문을 stdin 끝에 붙였다.

| 시도 | 명령 | 결과 |
|---|---|---|
| 1 | `env -u ANTHROPIC_API_KEY claude -p --add-dir /Users/kangsangmo/Desktop/Valuehire_v4 --allowedTools Read,Grep,Glob,Bash` + 전체 사업/코드 조준 prompt | 안전 필터 차단, exit 1, VERDICT 없음 |
| 2 | 같은 명령 + 비공개 웹 증거 보존 설계로 재표현 | 안전 필터 차단, exit 1, VERDICT 없음 |
| 3 | `env -u ANTHROPIC_API_KEY claude -p --model sonnet --add-dir /Users/kangsangmo/Desktop/Valuehire_v4 --allowedTools Read,Grep,Glob,Bash` | 6분 이상 판정 출력 없음, 중단, VERDICT 없음 |
| 4 | `env -u ANTHROPIC_API_KEY claude -p --model haiku --max-turns 8 --allowedTools Read,Grep` | 3분 이상 판정 출력 없음, 중단, VERDICT 없음 |

→ 뭘 시켰나: goal·구현 프롬프트·benchmark와 v4 기준선을 읽고 거짓 완료와 개인정보/DB 경계를 감사하게 했다.
→ 뭐가 나왔나: 두 번은 아래 안전 필터 원문, 두 번은 판정 없이 장기 정지했다.
→ 좋은 소식인가 나쁜 소식인가: 나쁜 소식이다. 다른 엔진 판정 본문을 확보하지 못했으므로 strict의 교차엔진 검증은 통과가 아니라 `BLOCKED_FILTER/NO_VERDICT`다.

### 최종 전달 readback

- Notion: 지정된 `2025 박지원님 AI 강의` 페이지의 연결 데이터베이스에 `핵심구현내용-260817` 새 항목을 만들고 본문을 저장했다.
- Notion side-peek URL: `https://app.notion.com/p/valueconnect/2025-AI-254345c17dca80018999e20b3a9c605b?p=3bf345c17dca807d95faed3f5dc91a80&pm=s`
- readback: title 일치, `사장님용 결론`, `100,061px`, `Organization Analysis`, `구현 에이전트에게 전달할 프롬프트` marker 모두 확인.
- Gmail: 수신자 `sangmokang@valueconnect.kr`, 제목 `핵심구현내용-260817`의 미발송 draft를 만들고 목록에서 수신자·제목·`DRAFT` label을 재확인했다. draft id `r-3398285565755090013`.
- strict 안전선에 따라 메일 발송은 실행하지 않았다.

필터 출력 원문(시도 1·2 동일 문구, Request ID만 다름):

```text
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606
```

→ 뭘 시켰나: Claude의 비대화식 판정을 요청했다.
→ 뭐가 나왔나: 업무 내용 판정이 아니라 서비스 안전 필터 차단이 나왔다.
→ 좋은 소식인가 나쁜 소식인가: 검증 결과가 아니므로 PASS/FAIL 어느 쪽으로도 쓰지 않았다.

※ 긴 stdin prompt 전문은 이 세션 tool transcript에 남아 있으나 저장소 파일에는 재복제하지 않았다. 따라서 strict §5의 “명령 전문을 저장소 장부에 보존”까지는 충족하지 못했다.

### V2 — Codex가 Claude 빈 판정과 자체 validator를 재공격

| 조준점 | 직접 재현 | 판정/조치 |
|---|---|---|
| `doc_height=NULL`인데 하단 도달로 볼 수 있는가 | 최초 validator가 `cursor >= null`을 참으로 만들 수 있음을 코드 검사로 확인 | 결함 확정. 실제 browser document height를 사용하도록 수정 후 3종 재실행 |
| 마지막 memory frame이 SQLite에 모두 저장됐는가 | 두 번째 validator가 session count와 DB row count를 직접 비교하지 않음을 확인 | 결함 확정. `stopHumanCaptureSession` flush 후 session=archive=row 일치 단언 추가, 3종 재실행 |
| geometry null/음수가 숫자 계산에 섞이는가 | `every(Number.isFinite...)` 부재를 확인 | 결함 확정. geometry 완전성 단언 추가 |
| sync가 원격 readback을 하는가 | v4 `sync-batch.js:124-135`, `server/index.js:1722-1726` 직접 확인 | 문서 지적과 일치. upsert error 없음만 보고 local synced 처리 |
| human capture가 document height를 보내는가 | v4 `background.js:649-653`과 `server/index.js:2175` 직접 대조 | 문서 지적과 일치. scrollPlan에 viewport만 있어 DB doc_height가 null |
| `profile_archives` migration에 RLS가 있는가 | `20260530000000_profile_archives_sync.sql` 전체와 repository 정책 검색 | 문서 지적과 일치. 생성 migration에 RLS enable/policy 없음; live policy는 NOT_RUN |
| 문서 내부 숫자 일치 | Organization Analysis view 9개를 두고 “7개”라고 쓴 문구 발견 | 과장/불일치 확정, 고정 숫자를 제거하고 “위 뷰”로 수정 |

→ 뭘 시켰나: Claude가 결과를 못 낸 상태에서 Codex가 문서의 핵심 주장과 benchmark 판정기를 반대 방향으로 직접 공격했다.
→ 뭐가 나왔나: validator 결함 3개와 문서 숫자 불일치 1개를 찾아 수정했고, v4 사실 주장 3개를 file:line으로 재현했다.
→ 좋은 소식인가 나쁜 소식인가: 수정 후 시험은 강해졌지만 다른 엔진과의 일치/불일치 표는 만들 수 없다. 이 작업은 “Codex 직접 적대검증 PASS, Claude 교차검증 미완”이다.

최종 강화 benchmark는 exit 0이며, 3종 모두 실제 browser height·geometry·sequence·hash·session/archive/row count 단언을 통과했다. 저장소 검증은 `git diff --check`, `node --check scripts/experiments/profile-archiver-long-page-benchmark.mjs`, `bash verify.sh` 모두 exit 0이었다.
