# HS-03.02 후보자 저장 재설계(v2) — goal (2026-09-17)

> 모드 `code-change` · 등급 **L3**(개인정보 저장 스키마 신설)
> 워크트리 `worktrees/hs-0302-storage-v2-20260917` · 브랜치 `task/hs-0302-storage-v2-20260917`
> origin/main `fc6beed`에서 분기 (기존 `task/hs-0301-schema-20260917`→`hs-0302-core`→`hs-0302-boundary-hardening`
> 3개 브랜치와는 무관 — 아래 결정에 따라 그 스택은 병합하지 않고 보류한다)
> 읽은 정본: `docs/sot/strict-workflow.md`, `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`,
> `docs/engineering/humansearch-hs-0302-connection-broker-goal-2026-09-17.md`(폐기된 v1 설계 근거)

## 1층 — 결론

기존 3개 브랜치(HS-03.01 스키마 + HS-03.02 core/boundary-hardening)를 코드로 직접 열어 사장님이
지적하신 설계 오류를 확인했다: `hs_candidates` 테이블에 후보자 원본 식별값(이메일·URL 등)을 저장하는
컬럼이 하나도 없고, 되돌릴 수 없는 HMAC/해시 지문 두 종류만 저장한다. 즉 DB에 저장은 되지만 나중에
그 후보자에게 실제로 연락할 값을 DB에서 다시 꺼낼 방법이 없다 — 실사용 불가능한 저장소였다. 사장님
지시(옵션 3)에 따라 그 3개 브랜치는 병합하지 않고 로컬에 보류하며, 이 문서의 새 설계로 처음부터
다시 만든다. 새 설계는 원본값(raw) 보존을 최우선으로 하고, 파일시스템 위·변조 방어(디코이 fd,
rename 스왑 탐지, VFS 가로채기)는 전부 들어내며, HMAC은 선택적 보조 지문으로만 남긴다.

## 2층 — 판단 근거

### 결정 카드 1 — 원본값 저장 방식

- **무엇을** — `candidate_ref`(포지션·채널마다 후보자를 가리키는 원본 식별값)와, 있으면
  이메일·프로필 URL을 각각 `_raw`(원본 그대로)·`_normalized`(중복 판별용) 컬럼 쌍으로 저장한다.
- **왜** — v1 설계는 `candidate_ref_hash`(키 지문)만 저장해 원본을 영구히 잃었다. 원본이 없으면
  이 저장소 자체가 실제 업무(연락·검색)에 쓸모없다.
- **버린 길** — 해시만 저장하고 필요할 때 외부에서 원본을 재조회: 이 저장소가 애초에 "그 후보자를
  어디서 봤는지"를 보존하는 유일한 장부라 재조회할 원천이 없다. 기각.
- **대가** — DB 파일 자체에 평문 개인정보(PII)가 남는다. Git 밖 0700/0600 보호 root, 파일 권한
  검사는 유지하되, 파일시스템 레벨의 정교한 위·변조 방어(결정 카드 3 참고)는 하지 않는다 — 이
  트레이드오프는 사장님이 명시적으로 승인했다("지금 안 해도 됨").
- **되돌리기** — 스키마는 마이그레이션 버전 관리(`hs_schema_migrations`)로 관리한다. 컬럼 추가는
  후속 마이그레이션으로, 이번 스키마를 버릴 필요는 되돌리기가 아니라 새 마이그레이션이다.

### 결정 카드 2 — 후보자(candidate)와 관측(observation)의 분리

- **무엇을** — `hs_candidates`(후보자 정체성, 1행 = 1명×1포지션×1채널)와
  `hs_candidate_observations`(관측 사건, 후보자당 N행)를 분리한다. 같은 후보자를 다시 보면 후보자
  행을 재사용하고 관측 행만 추가한다. `unique(candidate_id, ingestion_id)`로 같은 수집 시도의
  재시도는 관측 행을 늘리지 않는다(idempotent).
- **왜** — v1은 이 구분이 없어 재관측 시 최초 관측 정보가 새로 덮이거나 사라질 위험이 있었다.
  사장님 원칙 5·7(중복은 막되 이력은 잃지 않는다, 출처 기록)과 직결된다.
- **버린 길** — 단일 테이블에 최신 관측만 유지(upsert-overwrite): 이전 소싱 채널·시점 이력이
  사라져 "이 정보 어디서 나왔는지" 역추적이 불가능해진다. 기각.
- **대가** — 조회 시 항상 후보자·관측 두 테이블을 봐야 한다(조인 비용). 이번 규모(로컬 SQLite,
  제품 진입점 0개)에서는 무시할 만하다.
- **되돌리기** — 두 테이블 다 마이그레이션으로 관리되므로 스키마 변경은 버전 추가로 되돌릴 수 있다.

### 결정 카드 3 — 파일시스템 위·변조 방어 범위 축소

- **무엇을** — v1의 단일 writer 브로커, `/dev/fd` 차분 검사, decoy fd 재현 방어, 키 지문
  파일로 쓰기를 막는 로직을 전부 삭제한다. 남기는 것: 보호 root가 symlink가 아닐 것, 0700/0600
  권한, DB 파일 생성 시 `O_CREAT|O_EXCL`(경합-안전 부트스트랩) — 이 정도는 비용이 거의 없는
  기본 위생이다.
- **왜** — 사장님 지적대로 이 코드가 `candidate_identity.py`의 절반 가까이를 차지했는데, 그 방어가
  막는 위협(같은 프로세스 안에서 파일을 바꿔치기)은 이 저장소를 실제로 부르는 제품 진입점이
  0줄인 지금 시점에 실무 가치가 없다. "SQLite를 안전하게 쓰기 위한 코드가 SQLite보다 복잡해지는"
  상황을 사장님이 직접 지적했다.
- **버린 길** — 기존 방어 로직을 그대로 유지하고 스키마만 raw 컬럼을 추가하는 절충안(대화 중
  옵션 1): 트랜잭션·원자성 로직은 재사용 가능했지만, 사장님이 "치명적 오류로 재작성 필요"로
  명시적으로 기각했다.
- **대가** — 같은 프로세스 내에서 파일을 심볼릭 링크나 rename으로 바꿔치기하는 정교한 공격에는
  다시 노출된다. AC-8(연결 신원 완전 증명)은 이번 범위에서 다루지 않는다 — apsw 도입 여부와
  무관하게 애초에 이번 재설계 범위 밖이다.
- **되돌리기** — 필요해지면(예: 다중 프로세스 동시 쓰기 운영 전환) 별도 WU로 재도입한다. 이번
  삭제로 스키마·API 계약이 바뀌지 않으므로 되돌리기는 값싸다.

### 결정 카드 4 — DB 엔진: SQLite 유지

- **무엇을** — 이번 재설계도 SQLite를 그대로 쓴다. Postgres 전환은 하지 않는다.
- **왜** — 사장님 원칙 10: "여러 worker가 동시에 장기간 핵심 시스템으로 쓸 거라면 Postgres"가
  기준인데, 이 저장소를 부르는 제품 진입점이 아직 0줄이라(§(d), 이전 goal 문서에서 이미 확인) 그
  운영 프로파일 자체가 없다.
- **버린 길** — Postgres로 지금 전환: 새 인프라(호스팅·자격증명·백업)가 필요해 이번 승인 범위를
  넘는다. 진입점이 정해지고 동시 쓰기 패턴이 확인된 뒤 재검토가 맞다.
- **대가** — 나중에 다중 프로세스 동시 쓰기가 필요해지면 SQLite의 파일 잠금 한계에 다시 부딪힌다.
- **되돌리기** — 스키마가 표준 SQL(체크 제약, FK, UNIQUE)이라 Postgres 이관 시 DDL 이식 비용은
  낮다.

## 인수 기준 (EARS)

- **AC-1** When 새 후보자 관측이 유효한 필수 필드(포지션·채널·candidate_ref·관측시각·수집ID)와
  함께 최초로 기록되면, 시스템은 `candidate_ref`의 원본값과 정규화값을 모두 저장하고
  `candidate_created`를 반환해야 한다.
  검증: `pytest tests/test_candidate_storage_v2.py::test_first_write_stores_raw_and_normalized_email_and_url`
- **AC-2** If `candidate_ref`가 비어 있으면, 시스템은 트랜잭션을 열기 전에 거부하고 어떤 행도
  남기지 않아야 한다.
  검증: `test_missing_candidate_ref_is_rejected_with_no_write` — counter-AC: 검증 실패 후에도
  부분 행이 남으면 이 AC는 깨진 것이다.
- **AC-3/AC-4** If 이메일 또는 프로필 URL이 주어졌지만 형식이 올바르지 않으면, 시스템은 쓰기 전에
  거부해야 한다. 검증: `test_invalid_email_format_is_rejected`, `test_invalid_url_format_is_rejected`.
- **AC-5** When 같은 (position_ref, channel, candidate_ref_normalized)가 다른 수집ID로 다시
  관측되면, 시스템은 기존 후보자 행을 재사용하고 새 관측 행을 추가해야 한다(후보자 행 수 불변,
  관측 행 수 증가). 검증: `test_reobservation_reuses_candidate_and_appends_observation`.
- **AC-6** When 같은 (candidate_id, ingestion_id)로 재시도(retry)가 들어오면, 시스템은 두 번째
  관측 행을 만들지 않고 `duplicate_observation`을 반환해야 한다(idempotent).
  검증: `test_retry_of_same_ingestion_id_is_idempotent`.
- **AC-7** While 커밋 단계에서 예기치 못한 오류가 나면, 시스템은 후보자 행과 관측 행 모두
  롤백해야 한다(부분 반영 금지). 검증: `test_mid_transaction_failure_rolls_back_candidate_and_observation`
  — counter-AC: 두 테이블 중 하나만 롤백되면(부분 가시성) 이 AC는 깨진 것이다.
- **AC-8** When 10개 스레드가 동시에 같은 후보자를 기록하면, 시스템은 정확히 1개의 후보자 행과
  각 시도별 관측 행(중복 없는 수집ID 기준)을 만들어야 한다. 검증:
  `test_ten_concurrent_writes_of_the_same_candidate_yield_one_candidate_row`.
- **AC-9** When 쓰기가 성공하면, 시스템은 커밋된 행을 다시 읽어 핵심 필드(정규화된 candidate_ref)가
  입력과 일치함을 확인한 뒤에만 성공을 반환해야 한다 — INSERT 문 실행 자체를 성공으로 보지
  않는다. 검증: `test_first_write_stores_raw_and_normalized_email_and_url`의 readback 단언.
- **AC-10** If SQLite 잠금(BUSY)이 재시도 상한(5회)을 넘도록 풀리지 않으면, 시스템은 무한정
  대기하거나 조용히 성공한 것처럼 반환하지 않고 명시적 오류(`CandidateStorageRetryExhausted`)를
  내야 한다. 검증: `test_persistent_lock_raises_after_retry_cap_instead_of_hanging`.
- **AC-11(회귀 방지)** 이전에 저장된 이메일/URL은 같은 후보자의 이후 관측에서 다른 값이 들어와도
  덮어써지지 않는다(원본=증거를 나중 관측이 훼손하면 안 된다). 검증:
  `test_reobservation_backfills_missing_email_without_overwriting_existing`.

## 입출력·오류·경계 계약

- 입력: `CandidateObservationInput(position_ref: str, channel: Literal["saramin","jobkorea","linkedin_rps"], candidate_ref: str, observed_at: str, ingestion_id: str, email: str | None = None, profile_url: str | None = None)`.
- 출력: `RecordResult(outcome: Literal["candidate_created","observation_added","duplicate_observation"], candidate: CandidateRecord, observation_id: int)`. `CandidateRecord`는 커밋 후 재조회한 원본+정규화 필드를 그대로 담는다.
- 오류: `CandidateStorageError`(검증·경계 위반), `CandidateStorageRetryExhausted`(잠금 상한 초과). 메시지에 원본 PII 값을 담지 않는다.
- 경계: `candidate_ref`만 필수. `email`/`profile_url`은 선택이며 생략 시 NULL(조작된 값으로 채우지 않음), 주어지면 형식 검증 통과가 필수. `hmac_key`는 완전히 선택이며 주어지지 않아도 모든 쓰기가 정상 동작한다(보조 지문일 뿐 저장의 중심이 아님).

## Harness 게이트 진행 로그

- 게이트 0: 이 문서 상단의 읽은 정본 목록, 위험등급 L3(개인정보 저장 스키마 신설) 명시.
- 게이트 2: RED 먼저 — `humansearch/tests/test_candidate_storage_v2.py`를 구현 모듈 부재 상태에서
  먼저 작성해 `ModuleNotFoundError`로 실패시켰다(빠진 기능 때문의 실패, 문법 오류 아님).
- 게이트 3: 최소 구현(`candidate_storage_schema.py`, `candidate_storage.py`)으로 12개 시험 전부
  GREEN. 회귀: 패키지 전체 `pytest` 223건 통과(기존 211건 + 신규 12건), 회귀 없음.
- R2(가짜 GREEN 방지): `_write_once`의 `except BaseException: _rollback(...); raise`를 일부러
  `pass`로 바꿔 원자성 시험이 실제로 실패하는지 확인한 뒤 원복했다(§ 위 Bash 로그 — 로컬 실행,
  저장소 상태는 원복 후 재검증으로 동일함을 확인).
- 게이트 4: `uv run ruff check` 전부 통과, `uv run mypy`(strict) 전부 통과, `uv run pytest tests/`
  223 passed, 0 failed.
- 게이트 5(CHECKPOINT): 이 커밋까지가 로컬 안전 커밋이다. push·PR 생성은 사람 승인 뒤 별도
  수동 실행 — 이 문서 제출 시점까지는 실행하지 않는다.

## L3 — 롤백·영향 반경·데이터 안전 AC

- 롤백: 이 브랜치는 아직 main에 병합되지 않았다 — 롤백은 병합하지 않는 것 자체다. 병합 후
  되돌릴 때는 `git revert`.
- 영향 반경: `humansearch/src/humansearch/{candidate_storage,candidate_storage_schema}.py` 신설.
  main의 기존 어떤 모듈도 이 코드를 아직 호출하지 않는다(제품 진입점 0줄, 아래 배송 상태 참고).
- 데이터 안전: DB 파일에 평문 이메일/URL이 남으므로 보호 root는 Git 밖·0700, DB 파일은 0600을
  유지한다. 이 파일이 실제 운영에 배치될 때는 디스크 암호화·백업 정책이 별도로 필요하다(이번
  범위 밖, 후속 결정 필요).

## 배송 상태

`NOT_APPLICABLE` — 순수 내부 API·시험 코드이며 이 코드를 부르는 제품 진입점이 아직 없다.
실제 후보자 관측→기록 파이프라인(어느 코드가 이 함수를 호출할지)은 사장님과 별도로 정할 미결
항목이다(원래 지시 4번, 이 브랜치의 범위 밖).

## 비범위

- apsw 커스텀 VFS 도입: 사장님이 "지금 안 해도 됨"으로 확정 — 이번 재설계에도 포함하지 않는다.
- 기존 `task/hs-0301-schema-20260917`→`hs-0302-core`→`hs-0302-boundary-hardening` 3개 브랜치:
  병합하지 않고 로컬에 보류한다. main 삭제·정리는 이번 WU 범위 밖.
- Postgres 전환, 다중 프로세스 동시 쓰기 아키텍처: 제품 진입점이 정해진 뒤 별도 WU.
- 실제 제품 진입점 배선(record_candidate_observation을 부를 파이프라인 결정): 별도 SKELETON WU.
