# HS-03.02 독립 검토(V1) 6회차 판정 원문 — 2026-09-15 (검토 대상 eb0b225, 최종)

검토 엔진: Codex CLI 0.154.0 (`codex exec -s workspace-write`, `--no-local` 클론 @eb0b225, nohup, 21:24:24~22:18, 28단계). 5회차(@ced77fe) REQUEST_CHANGES 3건이 닫혔는지 원문 판정 없이 스스로 재현하도록 지시했다. 원문 100% 보존, 클론 절대 경로는 저장소 상대 경로로 정규화.

---

VERDICT: APPROVE

# 결론

앞서 지적된 세 문제는 모두 다시 나타나지 않았습니다. 기록 중 보호 조건이 바뀌면 저장을 확정하기 전에 멈추고, 오래 기다린 뒤에도 내부 오류나 경로를 그대로 내보내지 않으며, 곁에 생기는 파일의 소유자도 직접 확인합니다. 요구된 검사와 고의 훼손 시험에서 현재 변경을 막아야 할 새 문제는 재현되지 않았으므로 받아들여도 됩니다.

건너뛴 것은 실제 다른 사용자 계정으로 실행하는 분리 시험과 원격 자동 검사 상태 확인입니다. 전자는 현재 한 사용자 계정만 쓸 수 있어 실행하지 못한 항목으로 분리했고, 후자는 이 로컬 독립 검토 범위 밖입니다. 첫 수용 검사 시도는 지정된 임시 저장 위치를 전달하지 않아 시험 목록을 읽지 못한 채 멈췄고, 올바른 위치를 전달해 재시도한 뒤 22건 모두 통과했습니다. 필수 명부 첫 수동 비교에서는 주석·빈 줄 12개를 잘못 포함했으며, 명부 자체의 제외 규칙대로 다시 비교해 111 대 111, 차이 0을 확인했습니다. 이 실패와 재시도를 판정에서 숨기지 않았습니다.

# 판단 근거

선택한 해석은 다음과 같습니다.

- 비밀키로 입력의 지문을 만드는 HMAC(Hash-based Message Authentication Code, 키 기반 메시지 인증 코드)은 세 식별값 모두를 길이와 함께 묶어 계산해야 하며, 같은 세 값만 한 행으로 합쳐져야 합니다.
- SQLite(단일 파일형 데이터베이스)의 `BEGIN IMMEDIATE`는 쓰기 예약 잠금을 트랜잭션 시작 때 얻는 명령입니다. 잠금 획득이 실패한 뒤 승자 행이 보이면 `duplicate`, 보이지 않으면 경로 없는 닫힌 오류를 내는 것이 인수 기준 AC-3의 “패자는 명시적 duplicate”와 오류 폐쇄를 함께 만족합니다.
- 쓰기 뒤 검사는 확정 뒤가 아니라 확정 직전이어야 합니다. 확정 뒤에 검사하면 오류를 내도 잘못된 행이 남습니다.
- “승인된 보호 루트(root, 기준 디렉터리)”의 구체 허용 목록(allowlist)이 코드에 없다는 사실은 확인했습니다. 다만 저장 계약 76~77행은 기본 경로 결정을 후속 HS-03/04 운영 설정에 위임합니다. 따라서 이번 함수가 구성된 DB 경로를 받는 범위에서 목록 부재만으로 현재 변경을 불합격 처리하지 않았습니다.
- 오류 폐쇄는 goal 50행과 이번 지시가 지정한 `str(exc)`, 일반 오류 이력을 렌더링하는 `traceback.format_exc()`, 명시적 원인 필드 `__cause__`를 기준으로 판정했습니다. Python이 억제 상태로 보관하는 문맥 필드 `__context__` 객체까지 물리적으로 삭제해야 한다는 더 강한 해석은 계약 문구와 다르므로 버렸습니다. 다만 비표준 수집기가 억제된 `__context__`를 직접 순회하면 경로를 읽을 수 있다는 잔여 위험은 아래에 공개합니다.

버린 해석은 다음과 같습니다.

- 시험 111건 통과만으로 승인하는 해석을 버렸습니다. 9개 제품 변형과 2개 CI 무력화 사본을 실제로 실행했습니다.
- 5.0초 설정을 함수 전체가 정확히 5.0초 안에 끝난다는 약속으로 읽는 해석을 버렸습니다. 계약은 SQLite 잠금 대기 설정의 기본값을 말하며 전체 응답시간 약속은 두지 않습니다. 실측 호출은 5.834초와 5.951초였습니다.
- R4 파일 하나가 모든 경계를 단독 보장한다는 해석을 버렸습니다. 키·DB 보호 루트 공유 거부를 제거한 variant는 R4 29건을 통과했지만 전용 4파일 전체에서 3건 실패했습니다.
- 같은 사용자 계정 안의 시험을 서로 다른 운영체제 사용자 분리 증거로 세는 해석을 버렸습니다. 저장 계약 89~91행이 이를 명시적으로 금지합니다.

이 판단이 틀리면 깨지는 것은 다음과 같습니다.

- 세 식별값 중 하나가 지문 입력에서 빠지면 서로 다른 포지션이나 채널의 후보가 한 사람으로 합쳐집니다.
- 확정 전 재확인이 빠지거나 뒤로 이동하면 완화된 권한으로 행이 남습니다.
- 잠금 초과 원문 오류가 다시 노출되면 호출자는 중복과 저장 장애를 안정적으로 구분하지 못합니다.
- 보조 파일 소유자 대조가 빠지면 다른 UID의 journal을 정상 보호 파일로 오인합니다.
- 필수 명부나 CI(Continuous Integration, 지속적 통합 자동 검사) 단일 명령 검사가 약해지면 시험을 지우거나 `|| true`를 붙여도 초록 상태가 될 수 있습니다.

# 기술 상세

## 검토 범위와 무결성

시작과 종료 상태는 같습니다.

```text
시작 2026-09-15 21:26:06 KST
git status --short: 출력 없음
git rev-parse HEAD: eb0b22523cef73a365270cb419a7a51133b84cff

종료 2026-09-15 22:18:05 KST
git status --short: 출력 없음
git rev-parse HEAD: eb0b22523cef73a365270cb419a7a51133b84cff
TRACKED_DIFF_RC=0
```

→ 해석: 클론의 추적 파일을 편집·커밋·push·stash하지 않았고, 판정 대상 SHA도 바뀌지 않았습니다. 모든 variant와 보고서는 지정 `review-scratch` 아래에만 만들었습니다.

검토 범위 `7473ec8..eb0b225`는 제품 코드, 전용 시험 4파일, 수용 검사기, CI 연결 검사기, 111건 명부, 워크플로 연결을 포함합니다. 세 수정 커밋은 `352de58`(RED 시험), `f36c722`(재포장 경로 RED 보강), `eb0b225`(GREEN 구현)입니다.

## 앞선 세 결함의 폐쇄 판정

### 1. 앞선 심각도 높음 — 원문 제목: 잠금 대기 초과 원문 오류

- 원인: `begin immediate`가 `SQLITE_BUSY`를 내면 `sqlite3.OperationalError: database is locked`가 그대로 올라왔습니다.
- 현재 코드: `humansearch/src/humansearch/candidate_identity.py:334` — 5초 timeout 연결, `:338-342` — BUSY를 `_outcome_after_lock_wait`로 보냄, `:366-383` — 승자 행이면 `duplicate`, 아니면 닫힌 오류.
- 반증: BUSY 후속 호출을 제거한 variant (f)는 R4 2건·전체 2건 실패했고, 승자 `duplicate` 반환을 제거한 variant (g)는 R4 1건·전체 1건 실패했습니다.
- 사업 영향: 중복 후보 기록이 저장 장애로 보이거나 내부 DB 오류가 상위 로그에 노출되는 일을 막습니다.
- 판정: CLOSED.

### 2. 앞선 심각도 중간 — 원문 제목: 원인 사슬 경로

- 원인: 키 파일 소멸 시 표시 메시지는 닫혀도 `FileNotFoundError`를 명시적 원인으로 연결해 일반 traceback에 키 절대 경로가 남았습니다.
- 현재 코드: `humansearch/src/humansearch/candidate_identity.py:192-201` — errno 이름만 담는 변환, `:215`, `:244`, `:261`, `:270` — `from None`으로 일반 traceback 사슬 차단.
- 반증: 세 OS 오류 경로를 `from exc`로 되돌린 variant (h)는 R4 3건·전체 3건 실패했습니다. 별도 키 소멸 실측에서 표시 문자열과 일반 traceback 모두 경로가 없고 `__cause__`는 `None`이었습니다.
- 사업 영향: 보호 키 저장 위치가 장애 로그를 통해 공개되는 일을 막습니다.
- 판정: CLOSED. 단, 억제된 `__context__` 객체의 내부 경로는 잔여 위험으로 별도 기록합니다.

### 3. 앞선 심각도 중간 — 원문 제목: 보조 파일 소유자

- 원인: 0700 부모 접근성만으로 보조 파일 소유자를 추론하고 파일 자체 `st_uid`를 보지 않았습니다.
- 현재 코드: `humansearch/src/humansearch/candidate_identity.py:302-314` — rollback journal, 선행 기록 로그인 WAL, 공유 메모리 파일인 SHM을 한 번의 `stat(follow_symlinks=False)`로 읽고 symlink, UID(user identifier, 운영체제 사용자 식별 번호) 값인 `st_uid`, mode 0600, 일반 파일을 확인.
- 반증: `st_uid` 대조를 제거한 variant (i)는 R4 1건·전체 1건 실패했습니다.
- 사업 영향: 다른 실행 주체가 소유한 보조 파일을 정상 파일로 오인하는 일을 막습니다.
- 판정: CLOSED.

현재 HEAD에서 새로 재현된 병합 차단 결함은 없습니다.

## 요구사항별 판정

### AC-1 — PASS

- `humansearch/src/humansearch/candidate_identity.py:83-100` — `position_ref`, `channel`, `candidate_ref` 세 값을 각각 UTF-8 바이트 길이 4바이트와 내용으로 직렬화해 HMAC-SHA256을 계산합니다.
- `humansearch/src/humansearch/candidate_identity.py:111-119` — 검증된 세 값으로 키와 후보 참조 지문을 만든 뒤 단일 기록 경로로 전달합니다.
- `humansearch/src/humansearch/storage_schema.py:53` — `candidate_key_hmac`가 기본키입니다.
- `humansearch/tests/test_hs_0302_candidate_identity.py:147` — 같은 세 값 두 번이 `inserted`, `duplicate`, 1행인지 확인합니다.
- `humansearch/tests/test_hs_0302_candidate_identity.py:173` 및 R2 162·175행 — 길이 접두 직렬화가 필드 경계 충돌을 막는지 확인합니다.

→ 해석: 같은 식별값은 DB 기본키 한 행으로 수렴하고, 키는 보호 파일에서 읽은 32바이트 이상 원시 바이트를 사용합니다.

### AC-2 — PASS

- `humansearch/src/humansearch/candidate_identity.py:95-100` — 지문 입력 반복문에 세 필드가 모두 들어갑니다.
- `humansearch/tests/test_hs_0302_candidate_identity.py:186` — 포지션만 다름과 채널만 다름이 각각 별도 행인지 확인합니다.

→ 해석: 이름·이메일 같은 외부 정보가 아니라 포지션·채널·후보 참조의 조합으로 동일성을 정합니다.

### AC-3 — PASS

- `humansearch/src/humansearch/candidate_identity.py:333-360` — 쓰기 직전 검사, 별도 트랜잭션, 단일 INSERT, 기본키 위반만 `duplicate`, 확정 전 재검사를 수행합니다.
- `humansearch/src/humansearch/candidate_identity.py:353-356` — `SQLITE_CONSTRAINT_PRIMARYKEY`만 중복으로 번역하고 다른 `IntegrityError`는 다시 올립니다.
- `humansearch/tests/test_hs_0302_candidate_identity.py:218` — 두 연결의 실제 경쟁 결과·1행·예외 0을 확인합니다.
- 지정 경쟁 시험을 독립 pytest 프로세스로 20회 반복해 20/20 통과했습니다.

```text
ITERATION 1..20: 각 RC=0
개별 시간: 6.11, 4.23, 4.64, 4.03, 3.88, 1.64, 0.78, 1.24,
4.58, 5.29, 6.45, 4.94, 4.05, 3.93, 0.30, 3.13, 2.39, 2.26,
2.18, 2.14초
RESULT ok=20 fail=0
```

→ 해석: 두 연결 경쟁에서 기본키 충돌과 잠금 경로를 포함해 매회 결과 집합과 1행 계약이 유지됐습니다. 시간에는 pytest 기동과 fixture 준비가 포함됩니다.

기본 5초 잠금 직접 계측은 다음과 같습니다.

```text
NO_WINNER CandidateIdentityError db write lock wait exceeded elapsed=5.834 cause=None
WINNER_PRESENT inserted duplicate elapsed=5.951
ROWS 1
LOCK_WAIT_SECONDS 5.0
```

→ 해석: 두 번째 연결은 잠금 초과 뒤 기본키 오류나 원문 BUSY를 내지 않습니다. 승자 행이 없으면 닫힌 오류, 있으면 `duplicate`입니다. 함수 전체 시간은 5초를 약 0.8~1.0초 넘길 수 있으므로 5초 전체 응답시간 보장은 없습니다.

### AC-4 — PASS

- `humansearch/src/humansearch/candidate_identity.py:129-151` — strip 전 제어문자 거부, strip 후 NFC(Normalization Form C, 유니코드 정준 결합 정규화), 빈 값·길이·허용 채널 검증을 합니다.
- `humansearch/src/humansearch/candidate_identity.py:154-189` — 인터넷 날짜·시간 표준 형식인 RFC3339 모양과 실제 달력·시간대 존재를 두 단계로 확인합니다.
- `humansearch/tests/test_hs_0302_candidate_identity.py:284` — 빈 세 필드와 허용 밖 채널을 거부하고 행 0인지 확인합니다.

→ 해석: 잘못된 입력은 HMAC 계산·INSERT 전에 거부되어 DB에 행을 남기지 않습니다.

### 저장 경계 — PASS, 운영 분리 증거 일부 NOT_RUN

- `docs/sot/humansearch-storage-contract.md:76-78` — Git 밖 저장과 운영 설정이 정할 기본 경로.
- `humansearch/src/humansearch/candidate_identity.py:240-265` — DB 전체 symlink 사슬·실제 부모와 키 루트 분리를 확인합니다.
- `humansearch/src/humansearch/candidate_identity.py:276-290` — 기록 직전 DB 부모·DB 자체 owner/mode/symlink/일반 파일/Git 밖/보조 파일을 확인합니다.
- `humansearch/src/humansearch/candidate_identity.py:359-360` — INSERT 뒤 같은 경계를 다시 확인한 다음에만 commit합니다.
- `humansearch/src/humansearch/storage_schema.py:274-285` — 재사용 검사기가 대상 자체 `st_uid`, symlink, mode를 확인합니다.
- `humansearch/src/humansearch/candidate_identity.py:50,302-314` — journal, WAL(Write-Ahead Log, 선행 기록 로그), SHM(shared memory, 공유 메모리 보조 파일)의 owner/mode/symlink/일반 파일을 확인합니다.

승인 root 상수·목록 검색 결과는 0건입니다. 이는 운영 기본 경로 선택이 후속 설정에 위임된 현재 범위에서는 결함이 아니지만, 호출자가 임의의 Git 밖 호환 DB를 넘길 수 있다는 뜻입니다. 실제 UID는 `501 (kangsangmo)` 하나였으므로 다른 UID 실행기의 `EACCES` 실패와 실행기 성공 쌍은 실행하지 못했습니다. 시험은 `st_uid`를 다르게 주입해 코드 분기만 검증합니다.

→ 해석: 이번 기록 함수의 파일 경계는 연결되어 있지만, 운영 배치 시 승인 root 설정과 실제 계정 분리 증거를 별도로 닫아야 합니다. 같은 UID 환경을 운영체제 격리 완료로 간주하지 않았습니다.

### 검증 연결 — PASS

- `scripts/acceptance-hs-0302.sh:93` — 개별 pytest 시험 식별자인 node-id 기대값을 정확히 111로 고정합니다.
- `scripts/acceptance-hs-0302.sh:351-369` — 전용 4파일을 실제 수집하고 단순 수집 요약만 허용합니다.
- `scripts/acceptance-hs-0302.sh:525-540` — 명부 주석·빈 줄 제외 후 실제 수집 node-id와 누락·추가를 양방향 비교합니다.
- `scripts/verify/check-hs-0302-ci-wiring.rb:16-18,43-62` — 실행 스텝 정확히 1개, 정확한 단일 명령, 셸 제어 연산자·조건·오류 무시 부재를 요구합니다.
- `.github/workflows/verify.yml:234` — HS-03.02 수용 검사를 정확한 단일 명령으로 실행합니다.

```text
REQUIRED_IDS=111
COLLECTED_IDS=111
SYMMETRIC_DIFF_LINES=0

WIRING_OK: verify 스텝 20 의 run 이 정확한 단일 명령이다
|| true 사본: WIRING_BAD, rc=1
; echo ok 사본: WIRING_BAD, rc=1
```

→ 해석: 명부 111건은 실제 pytest 수집과 정확히 비교되며, CI 실패를 성공으로 바꾸는 두 주입은 모두 차단됐습니다.

## 기준선 실행 증거

모든 `uv` 실행은 `UV_CACHE_DIR=.../review-scratch/uv-cache uv run --frozen --offline`로, pytest는 `-p no:cacheprovider`로 순차 실행했습니다.

```text
test_hs_0302_candidate_identity.py: 28 passed in 6.50s, rc=0
test_hs_0302_r2_hardening.py:      35 passed in 10.77s, rc=0
test_hs_0302_r3_hardening.py:      19 passed in 6.80s, rc=0
test_hs_0302_r4_db_boundary.py:    29 passed in 5.16s, rc=0
합계: 111 passed

ruff check src tests: All checks passed!, rc=0
mypy src tests: Success: no issues found in 48 source files, rc=0

수용 검사 첫 시도:
NOT_RUN: pytest 수집 실패 — 무엇을 돌려야 하는지 모른 채로는 합격시키지 않는다
CHECKED: 8
FAIL(run-acceptance): ... 종료값 2

지정 캐시 전달 재시도:
PASS: 검사 전후 저장소 상태 동일 — 검증기가 대상을 오염시키지 않았다
CHECKED: 22
OK(run-acceptance): ... 판정 22건, CHECKED 22

CI 단계 무결성:
CHECKED: 24
VERDICT: PASS
```

→ 해석: 제품 시험·정적 검사·타입 검사·수용 검사·CI 단계 무결성 검사가 현재 HEAD에서 새로 실행되어 통과했습니다. 첫 수용 실패는 검사 불능을 성공으로 바꾸지 않는 fail-closed가 정상 작동한 환경 실패이며 지정 캐시로 같은 검사를 완주했습니다.

## 9개 variant(원본 밖 사본에서 규칙 하나를 바꾼 변형) 반증 기록

각 사본에서 먼저 아래 명령 형태로 import 위치를 확인했고, 출력 경로가 모두 해당 사본의 `humansearch/src/humansearch/candidate_identity.py`였습니다.

```text
PYTHONPATH=<사본>/humansearch/src uv run --frozen --offline \
  python -c 'import humansearch.candidate_identity as m; print(m.__file__)'
```

→ 해석: 원본 모듈을 잘못 시험한 variant는 없습니다.

1. variant (a), `_insert_once`의 commit 직전 DB 경계 재확인 제거: R4 `2 failed, 27 passed`; 전체 `2 failed, 109 passed`. DB 파일·부모 권한 완화 두 경우가 성공 오류 미발생으로 잡혔습니다.
2. variant (b), 재확인을 commit 뒤로 이동: R4 `2 failed, 27 passed`; 전체 `2 failed, 109 passed`. 오류 뒤에도 `rows=1`이 남아 잡혔습니다.
3. variant (c), `begin immediate` 경계와 명시적 commit 제거로 자동 확정 허용: R4 `4 failed, 25 passed`; 전체 `4 failed, 107 passed`. 행 잔존 2건과 원문 `database is locked` 2건이 잡혔습니다.
4. variant (d), 쓰기 직전 DB 경계 호출 제거: R4 `5 failed, 24 passed`; 전체 `5 failed, 106 passed`. 비일반 DB, 느슨한 journal, symlink journal, 비일반 journal/WAL이 잡혔습니다.
5. variant (e), 키·DB 보호 루트 공유 거부 제거: R4 `29 passed`; 전체 `3 failed, 108 passed`. 같은 루트·키 하위·DB 하위 세 경우가 전체 묶음에서 잡혔습니다.
6. variant (f), BUSY 후 `_outcome_after_lock_wait` 호출 제거: R4 `2 failed, 27 passed`; 전체 `2 failed, 109 passed`. 두 잠금 시험에서 원문 `OperationalError`가 잡혔습니다.
7. variant (g), 잠금 대기 후 승자 행의 `duplicate` 반환 제거: R4 `1 failed, 28 passed`; 전체 `1 failed, 110 passed`.
8. variant (h), 닫힌 OS 오류 세 경로를 `from exc`로 복원: R4 `3 failed, 26 passed`; 전체 `3 failed, 108 passed`. 키 파일·키 디렉터리·DB 경로가 traceback에 나타나 잡혔습니다.
9. variant (i), 보조 파일 `st_uid` 대조 제거: R4 `1 failed, 28 passed`; 전체 `1 failed, 110 passed`.

→ 해석: 전용 4파일 전체 기준 variant 생존은 0건입니다. variant (e)는 R4 단독에서 생존했으므로 경계 회귀 검증에는 4파일 전체 묶음이 필요합니다. 이는 시험 분할의 범위 사실이며 전체 필수 명부가 네 파일을 모두 강제하므로 현재 검사 우회는 아닙니다.

## 닫힌 오류 AST와 키 소멸 실측

AST(Abstract Syntax Tree, 소스 문법 구조 트리)로 27개 `raise`와 21개 `CandidateIdentityError(...)` 생성 지점을 열거했습니다. 메시지 식에서 `db_path`, `hmac_key_path`, `key`, `key_hmac`, `candidate_ref`, `position_ref`, `candidate_ref_hash`를 직접 참조한 지점은 0건입니다.

```text
CandidateIdentityError 생성 지점 COUNT 21
전체 raise 지점 27
sensitive=[] (21/21)
```

→ 해석: 경로·식별 원문·키 바이트·HMAC을 직접 보간하는 도메인 오류 메시지는 없습니다. `CandidateIdentityError(str(exc))` 경로는 `storage_schema._verify_path`의 고정 label 문구를 받고 `from None`으로 하위 원인을 숨깁니다.

원본과 같은 별도 사본에서 키 검증 후 파일을 삭제한 결과입니다.

```text
STR hmac key is unreadable (ENOENT)
STR_HAS_KEY_PATH False
TRACE_HAS_KEY_PATH False
CAUSE None
CONTEXT FileNotFoundError(2, 'No such file or directory')
TRACE_LAST humansearch.candidate_identity.CandidateIdentityError: hmac key is unreadable (ENOENT)

SUPPRESS_CONTEXT True
CONTEXT_HAS_KEY_PATH True
```

→ 해석: 요구된 표시 문자열·일반 traceback·명시적 `__cause__`에는 키 절대 경로가 없습니다. 다만 Python의 억제된 `__context__` 객체 자체에는 원래 `FileNotFoundError.filename`이 남습니다. 현재 코드가 쓰는 일반 traceback은 이를 표시하지 않지만, 향후 오류 수집기가 억제 문맥을 직접 직렬화하면 다시 노출될 수 있습니다. R4 시험 474행 docstring의 “`__context__`에도 없다”는 표현은 실제 보장보다 강하고, 시험 본문은 렌더링 traceback만 확인합니다. 현 goal의 메시지 계약과 지정 검사는 충족하므로 병합 차단 결함으로 판정하지 않았습니다.

## 설계 판단 카드

### 잠금 초과 처리

- 무엇을: `BEGIN IMMEDIATE` BUSY 뒤 한 번 읽어 승자 확정 여부를 `duplicate` 또는 닫힌 오류로 정합니다.
- 왜: 기본키 충돌 이전 단계에서 잠금 시간이 끝날 수 있어 AC-3 결과와 오류 폐쇄를 함께 지켜야 합니다.
- 버린 길: 원문 BUSY 재노출과 무한 재시도는 각각 호출 계약 파괴와 무기한 지연 때문에 버렸습니다.
- 대가: 기본 설정에서 호출 전체가 실측 약 5.8~6.0초 걸릴 수 있고, 승자 행이 있어도 timeout을 기다린 뒤 확인합니다.
- 되돌리기: `_LOCK_WAIT_SECONDS`와 `_outcome_after_lock_wait`만 교체하면 정책을 바꿀 수 있으나, AC-3·오류 시험을 함께 갱신해야 합니다.

### 운영 승인 root 위임

- 무엇을: 제품 함수는 구체 allowlist 대신 전달받은 DB의 Git 밖·권한·키 분리 경계를 확인합니다.
- 왜: 저장 계약이 기본 경로 결정을 후속 HS-03/04 운영 설정에 위임했고 현재 WU에는 그 설정 입력이 없습니다.
- 버린 길: 저장소에 임의 절대 경로를 고정하는 방식은 환경별 배치를 깨뜨리므로 버렸습니다.
- 대가: 운영 설정 연결 전에는 호출자가 임의의 Git 밖 호환 DB를 넘길 수 있습니다.
- 되돌리기: 승인 root를 명시 입력으로 추가하고 `resolve(strict=True)` 결과를 그 root 아래로 제한할 수 있으며 호출 API와 시험 변경이 필요합니다.

# 증거 원문 위치

단계별 명령·시각·종료값·마지막 출력은 다음 파일에 즉시 저장했습니다.

- `review-scratch/steps/step-1.md` — 시작 SHA·상태·범위
- `step-2.md` — 계약·수정 코드
- `step-3.md`~`step-8.md` — 4개 기준선 pytest, Ruff, mypy
- `step-9.md`~`step-11.md` — 수용 첫 실패·재시도·CI 무결성
- `step-12.md`~`step-20.md` — 9개 variant 두 단위 결과
- `step-21.md`~`step-22.md` — 경쟁 20회와 기본 5초 직접 계측
- `step-23.md`~`step-24.md` — AST와 키 소멸 오류 경로
- `step-25.md`~`step-26.md` — 111건 명부와 CI 우회 주입
- `step-27.md` — 저장 계약 §3 문장별 대조
- `step-28.md` — 종료 SHA·상태

→ 해석: 원격 CI와 실제 다른 UID 분리 외에는 요청된 최소 검사를 모두 실행했습니다. 현재 판정은 오직 `eb0b225`에 유효하며 HEAD가 바뀌면 만료됩니다.
