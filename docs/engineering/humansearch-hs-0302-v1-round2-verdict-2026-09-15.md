# HS-03.02 독립 검토(V1) 5회차 판정 원문 — 2026-09-15 (검토 대상 ced77fe)

검토 엔진: Codex CLI 0.154.0 (`codex exec -s workspace-write`, `--no-local` 클론 @ced77fe). 1회차(20:05, 3단계)·2회차(20:22, 13단계)는 시스템 메모리 부족으로 강제 종료됐고, 3회차(20:48~21:05, nohup)가 2회차의 step-1~13 기록을 이어받아 완주했다. 원문 100% 보존. 클론 절대 경로는 저장소 상대 경로로 읽는다. 이 판정의 결함 3건은 352de58·f36c722(RED)·eb0b225(GREEN)에서 닫았고, 그 HEAD 에 대한 재검토는 별도 파일이다.

---

VERDICT: REQUEST_CHANGES

## 결론

현재 상태로는 승인할 수 없습니다. 같은 대상을 동시에 오래 기록할 때 약속한 결과 대신 내부 실패가 그대로 나오고, 실패 기록에는 보호 정보가 놓인 절대 위치가 남습니다. 또한 본 저장 파일 옆에서 함께 생기는 파일은 소유자가 맞는지 직접 확인하지 않습니다. 반면 같은 대상을 두 번 기록해 한 건만 남기는 기본 동작, 서로 다른 채용 자리나 출처를 분리하는 동작, 잘못된 입력 거부, 필수 검사 104건의 실제 실행 연결, 검사 명령 뒤에 성공을 위장하는 두 꼬리 차단은 확인됐습니다.

## 판단 근거

### 실행 범위·재시도·추정

앞선 step 1~13은 원 지시대로 다시 실행하지 않고 그 기록을 증거로 채택했습니다. 이번 재개에서 건너뛴 필수 검사는 없습니다. 다만 서로 다른 운영 사용자 계정으로 쓰기 권한을 나누는 검사는 같은 사용자 환경이므로 `NOT_RUN`이며, 원격 CI 실행 상태와 운영 배포는 확인하지 않았습니다. step-8은 최초 전체 시험의 종료값을 도구가 회수하지 못해 같은 시험을 한 번 재실행했고, step-12는 최초 임시 경로가 상위 링크 검사에 걸려 링크 없는 지정 경로에서 다시 측정했으며, step-13은 최초 복사 원본 경로를 잘못 써 import가 원본을 가리킨 실행을 폐기하고 올바른 사본에서 다시 실행했습니다. 이 재시도들은 모두 기록돼 있고 최종 채택 결과가 분명합니다.

코드만으로 내린 판단도 미리 밝힙니다. 승인된 저장 뿌리 목록이 없다는 사실, 보조 파일 소유자 검사가 없다는 사실, 예외 원인 기록에 절대경로가 남는 사실은 코드와 실행 출력의 직접 증거입니다. 승인된 저장 뿌리 목록의 부재 자체를 결함으로 보지는 않았습니다. 정본이 기본 경로 선정을 후속 운영 설정에 맡기고 이번 작업이 운영 쓰기를 제외했기 때문입니다. 다만 현재 함수만으로 승인된 설정에서 온 경로인지는 증명할 수 없으므로 부분 구현으로 남겼습니다.

첫째, AC-3의 “두 연결이 같은 키를 동시에 넣으면 진 쪽은 `duplicate`”를 빠른 경쟁에만 한정하지 않았습니다. SQLite(파일 하나로 동작하는 내장형 데이터베이스)의 기본 5초 대기 시간을 넘긴 경우도 문언상 두 연결의 경쟁입니다. “기본 대기 시간을 넘긴 경쟁은 다른 오류 그대로 올림”이라는 좁은 해석은 goal 64행의 구현 메모와 맞지만, AC-3 41행에는 그 예외가 없고 step-12가 실제로 약 5.689초 뒤 약속한 결과가 사라짐을 보였으므로 버렸습니다. 이 판단이 틀리면, 호출자는 부하가 높을 때 정상 중복과 저장 장애를 구분하지 못한 채 후보 순회를 중단할 수 있습니다.

둘째, `str(exc)`만 오류 경계로 보지 않았습니다. traceback(예외가 거쳐 온 호출과 원인 기록)은 운영 로그와 장애 수집기에 흔히 저장되는 관측 출력입니다. `CandidateIdentityError`의 직접 문장은 안전하지만 `__cause__`에 붙은 `FileNotFoundError`가 키 파일 절대경로를 포함하므로 닫힌 오류가 완성됐다는 해석을 버렸습니다. 이 판단이 틀리면, 일반 오류 문구만 검사하는 시험은 통과하면서 실제 장애 로그에 보호 위치 구조가 남습니다.

셋째, sidecar(SQLite가 본체 옆에 만드는 WAL·SHM·journal 보조 파일)의 소유자를 부모 디렉터리 권한에서 추론하지 않았습니다. 저장 계약 85~87행은 대상 파일 자체에 같은 owner/mode/root/symlink 규칙을 요구합니다. 코드 주석 278~279행은 부모가 0700이므로 소유자를 따로 보지 않는다고 명시하지만, 이것은 요구 문장을 대체하지 못합니다. 이 판단이 틀리면 잘못된 소유권·ACL·특권 프로세스가 만든 보조 파일을 계약상 거부했다고 보고할 근거가 없습니다.

넷째, 승인된 보호 root 목록을 지금 하드코딩해야 한다는 해석은 버렸습니다. 저장 계약 76~77행은 기본 경로를 후속 HS-03/04의 승인된 운영 설정에서 정하도록 하고, goal 140행은 운영 쓰기를 이번 범위에서 제외합니다. 따라서 목록 부재는 사실이지만 독립 결함은 아닙니다. 다만 운영 연결 시에는 설정이 공급한 root와 실경로를 대조하는 별도 증거가 필요합니다. 이 판단이 틀리면 임의의 Git 밖 0700 디렉터리에 놓인 호환 DB가 승인된 위치처럼 취급될 수 있습니다.

## 기술 상세와 증거 원문

### 1. 결함 — HIGH

원문 제목: **AC-3: While SQLite 연결 2개가 같은 키를 동시에 넣으면 시스템은 기본키 제약으로 1행을 보장하고, 진 쪽은 명시적 `duplicate` 결과를 돌려줘야 한다.**

- 원인: [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:312)의 연결은 별도 timeout을 주지 않고, [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:315)의 `begin immediate`가 쓰기 잠금을 먼저 요구합니다. 기본 5초를 넘기면 [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:326)의 기본키 충돌 처리까지 도달하지 못합니다.
- 재현 입력: 별도 연결이 `begin immediate` 잠금을 잡은 상태에서 같은 보호 DB에 `record_candidate_identity`를 호출했습니다.
- 실제 결과: OperationalError(데이터베이스 작업 실패 예외)이며 SQLite 오류 이름은 `SQLITE_BUSY`, 메시지는 `database is locked`, 경과는 약 5.689초였습니다.
- 사업 영향: 평소 경쟁에서는 한 행만 남지만 느린 쓰기·백업·장애 복구와 겹치면 후보 저장 호출이 약속된 중복 결과 대신 예외로 끝나 상위 순회를 중단하거나 재시도 정책을 우회할 수 있습니다.
- 최소 수정 방향: 잠금 대기와 재시도 상한을 계약에 명시하고, 상한 안에서는 승자의 확정 뒤 INSERT를 재시도해 기본키 충돌을 `duplicate`로 번역하십시오. 상한 초과가 허용된다면 AC-3에 그 예외와 닫힌 도메인 오류를 명시하고 `sqlite3.OperationalError` 원문을 경계 밖으로 내보내지 않아야 합니다.

설계 지적:

- 무엇을 — 잠금 대기·재시도·최종 오류 상태를 명시적 정책으로 만듭니다.
- 왜 — 현재 동작은 Python/SQLite의 암묵적 5초 기본값에 제품 계약이 좌우됩니다.
- 버린 길 — 짧은 경쟁 시험 400라운드 통과만으로 모든 경쟁을 대표하는 해석은 장기 잠금 실측이 반증했습니다.
- 대가 — 최악 지연과 재시도 횟수가 늘며, 호출자 취소·전체 마감시간과 조율해야 합니다.
- 되돌리기 — 연결 생성과 트랜잭션 시작 주위의 작은 정책 경계로 격리하면 기존 HMAC·스키마는 건드리지 않고 회수할 수 있습니다.

step-12 원문:

```text
RUN 20
. [100%]
1 passed in 0.89s
RUN_RESULT 20 rc=0
RACE_SUMMARY failures=0/20

exception_type=OperationalError
sqlite_errorname=SQLITE_BUSY
message=database is locked
elapsed_seconds=5.689
```

→ 해석: 시험 한 번이 내부 20라운드이므로 순차 20회, 총 400라운드의 짧은 경쟁은 통과했습니다. 그러나 잠금이 기본 대기보다 길면 같은 경로가 `duplicate`가 아닌 원문 오류로 끝납니다. 이는 데이터 중복은 막지만 AC-3 출력 계약을 전 구간에서 보장하지 못한다는 반증입니다.

### 2. 결함 — MEDIUM

원문 제목: **오류: `CandidateIdentityError(StorageSchemaError)`. 메시지에 `candidate_ref`·`position_ref`·키 값을 넣지 않는다.**

- 원인: [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:248)에서 키 파일을 읽고, 실패하면 [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:250)이 고정 문구로 감싸지만 `from exc`로 원인 예외를 보존합니다.
- 재현 입력: 검사 통과 직후 키 파일을 지우고 `read_bytes()`에 도달시키는 격리 사본 경쟁을 만들었습니다.
- 실제 결과: 직접 오류 문자열에는 절대경로가 없지만 `traceback.format_exc()`와 `__cause__`의 `FileNotFoundError`에는 키 파일 절대경로가 있습니다. HMAC(비밀키를 사용한 메시지 인증 해시) 키 바이트 자체는 노출되지 않았습니다.
- 사업 영향: traceback을 저장하는 일반 장애 수집기에서 키 저장소의 전체 위치가 드러나 공격자에게 파일 배치 구조를 제공합니다. 후보 참조나 키 바이트가 직접 노출된 것은 아닙니다.
- 최소 수정 방향: 공개 경계에서는 `from None` 또는 경로가 제거된 원인으로 변환하고, 내부 진단이 필요하면 접근 통제된 별도 감사 채널에 비민감 오류 코드만 남기십시오.

설계 지적:

- 무엇을 — 오류의 직접 문자열뿐 아니라 원인 사슬까지 공개 로그 계약에 포함합니다.
- 왜 — Python의 기본 traceback은 원인 예외를 함께 출력하므로 현재 시험 범위보다 실제 관측 범위가 큽니다.
- 버린 길 — `str(exc)`가 안전하므로 닫혔다고 보는 길은 step-13의 traceback 실측 때문에 버렸습니다.
- 대가 — 원래 OS 오류의 세부 경로가 사라져 현장 진단 정보가 줄어듭니다.
- 되돌리기 — 키 읽기·경로 해석 두 오류 포장 지점만 바꾸면 되며 저장 데이터 형식에는 영향이 없습니다.

step-13 원문:

```text
AST_RAISE_COUNT=20
AST_SENSITIVE_NAMES=[]
RACE_EXCEPTION_TYPE=CandidateIdentityError
RACE_STR=hmac key is unreadable
RACE_STR_HAS_KEY_ABSPATH=False
RACE_TRACEBACK_HAS_KEY_ABSPATH=True
CAUSE_0_TYPE=FileNotFoundError
CAUSE_0_HAS_KEY_ABSPATH=True
CAUSE_0_STR=[Errno 2] No such file or directory: '.../key-root/hs-candidate.key'
```

→ 해석: AST(파이썬 문법 구조 트리)로 확인한 직접 `CandidateIdentityError` 20곳은 경로·두 참조·키 바이트·HMAC을 메시지 식에 보간하지 않습니다. 직접 문자열도 안전합니다. 실패는 원인 사슬과 traceback에만 존재하며, 그래서 “직접 문구 PASS / 운영 오류 출력 FAIL”로 구분합니다.

### 3. 결함 — MEDIUM

원문 제목: **DB와 같은 보호 범위 안의 WAL, SHM, rollback journal도 부모 디렉터리와 대상 파일 경로 자체에 같은 owner/mode/root/symlink 규칙을 따라야 한다.**

- 원인: [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:282)은 세 suffix를 순회하고 284행에서 stat을 이미 얻지만, 287~292행은 링크·mode·일반 파일만 검사합니다. 278~279행 주석은 부모 0700을 이유로 owner 확인을 의도적으로 생략했다고 적습니다. 반면 본체 검사가 재사용하는 [storage_schema.py](humansearch/src/humansearch/storage_schema.py:281)은 `st_uid == os.getuid()`를 직접 확인합니다.
- 재현 입력: 다른 UID로 파일을 만들 권한이 없는 동일 UID 환경이므로 실제 소유자 변경 재현은 `NOT_RUN`입니다. 결함 근거는 계약의 명시 요구와 도달 코드의 명시적 누락입니다.
- 사업 영향: mode 0600인 다른 소유자의 보조 파일이 존재하는 비정상·복구·특권 작업 뒤 상태를 함수가 계약 위반으로 판정하지 못합니다.
- 최소 수정 방향: 이미 얻은 `info.st_uid`를 현재 UID와 비교하고 닫힌 오류로 거부하는 시험을 권한 격리 가능한 실행기에서 추가하십시오.

설계 지적:

- 무엇을 — 보조 파일도 DB 본체와 같은 대상별 owner 검사를 수행합니다.
- 왜 — 계약은 부모의 접근 가능성 추론이 아니라 대상 파일 자체의 owner 확인을 요구합니다.
- 버린 길 — 0700 부모면 다른 UID 파일이 불가능하다는 가정은 ACL·특권 복구·기존 이상 상태를 포함하지 않아 버렸습니다.
- 대가 — 추가 시스템 호출은 필요하지 않고 이미 얻은 stat 비교 한 번이 늘어납니다. 다른 UID fixture는 별도 실행 환경이 필요합니다.
- 되돌리기 — `_verify_sidecars`의 owner 비교와 해당 회귀 시험만 독립적으로 회수할 수 있습니다.

### 4. 잔여 위험 — LOW

원문 제목: **키·DB 보호 root 공유 거부 회귀의 시험 분류**

step-11에서 키·DB 보호 root의 양방향 포함 거부를 제거한 variant(규칙 하나를 의도적으로 약화한 음성 대조군)는 r4 파일 단독에서는 `22 passed`로 살아남았고, 전용 네 파일 전체에서는 `3 failed, 101 passed`로 잡혔습니다. 필수 104건 명부와 CI는 전체 네 파일을 실행하므로 제품 게이트 우회는 아닙니다. 다만 “DB 저장 경계”만 빠르게 실행하는 개발자는 이 회귀를 놓칠 수 있습니다.

→ 해석: 병합 차단의 독립 원인은 아니지만, 시험 파일의 의미 분류가 완전하지 않습니다.

### 5. 저장 계약 §3 문장별 1:1 대조

| 계약 문장 역할 | 코드 역할 | 판정 |
|---|---|---|
| DB와 암호화 파일 저장소는 Git 밖 | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:268)이 DB 부모의 Git worktree 포함을 거부합니다. 암호화 파일은 HS-03.02 비범위입니다. | DB PASS / 암호화 파일 NOT_RUN |
| 보호 디렉터리 0700, DB 0600 | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:264)의 부모 검사와 265행의 DB 검사, [storage_schema.py](humansearch/src/humansearch/storage_schema.py:274)의 공통 검사기가 owner와 정확 mode를 봅니다. | PASS |
| 쓰기 직전 부모·대상 owner/mode/symlink | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:311)이 연결 전 검사합니다. DB 사슬은 220행에서도 검사됩니다. | PASS, 상위 사슬 동시 교체 창은 잔여 위험 |
| 실제 경로가 승인된 보호 root 안 | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:220)은 실제 부모를 계산하지만 승인 root 목록·인자와 비교하지 않습니다. Git 밖과 키 root 분리만 확인합니다. | 부분 구현, 이번 WU 독립 결함으로는 미판정 |
| 생성은 restrictive mode 또는 umask | [storage_schema.py](humansearch/src/humansearch/storage_schema.py:108)은 root 0700과 umask 0077, 138행은 DB 0600 생성을 담당합니다. HS-03.02는 기존 DB를 받습니다. | DB PASS / 보조 파일 부분 구현 |
| 쓰기 뒤 owner/mode 재확인 | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:332)이 INSERT 뒤 commit 전에 같은 경계를 다시 봅니다. | DB·부모 PASS |
| 권한 완화·owner 불일치·symlink·root 탈출은 저장 실패 | DB·부모의 owner/mode/직접 symlink/Git 경계는 264~270행에서 거부합니다. 승인 root 설정과의 동일성은 증명하지 않습니다. | 부분 구현 |
| WAL/SHM/journal/temp/backup/export/recovery도 같은 규칙 | 48행과 273~292행은 journal/WAL/SHM의 링크·0600·일반 파일을 봅니다. owner는 누락됐습니다. temp/backup/export/recovery는 정본 263~265행상 후속 WU 소유이며 이 실행에서는 만들지 않았습니다. | journal/WAL/SHM FAIL(owner), 나머지 NOT_RUN/비범위 |
| 다른 UID, EACCES, 실행기 성공, symlink 우회 | 동일 UID 환경입니다. 정본은 이런 환경의 OS 격리를 `NOT_RUN`으로 정합니다. | NOT_RUN |

→ 해석: `ced77fe`의 핵심인 쓰기 뒤·확정 전 DB/부모 재확인은 구현됐고 변형 시험도 이를 잡습니다. 그러나 보조 파일 owner는 정본 문장과 1:1로 닫히지 않습니다. 승인 root 목록은 없지만 정본 76~77행의 후속 운영 설정 위임 때문에 그 사실만으로 이번 WU를 실패시키지는 않았습니다.

승인 root 후속 설계 지적:

- 무엇을 — 운영 설정이 승인 root를 정하는 시점에 실제 DB 부모와 그 root의 동일성 또는 포함 관계를 검증합니다.
- 왜 — 지금의 “Git 밖”은 “운영에서 승인된 위치”와 같은 뜻이 아닙니다.
- 버린 길 — 현재 코드에 경로 문자열 목록을 하드코딩하는 길은 정본이 결정을 후속 설정에 맡겼으므로 버렸습니다.
- 대가 — 기록 함수나 상위 storage 객체가 승인 root를 함께 전달해야 해 인터페이스 결합이 늘어납니다.
- 되돌리기 — 운영 설정 어댑터와 root 대조 경계를 분리하면 제품 HMAC·스키마를 바꾸지 않고 교체할 수 있습니다.

### 6. 요구사항별 최종 판정

| 요구사항 | 판정 | file:line 역할 | 실행 근거 |
|---|---|---|---|
| AC-1 같은 세 값 2회 → 1행·세 값 HMAC·보호 키 | PASS | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:78) 세 필드 길이 접두 HMAC, 106행 검증값 사용, [storage_schema.py](humansearch/src/humansearch/storage_schema.py:53) HMAC 기본키, [test_hs_0302_candidate_identity.py](humansearch/tests/test_hs_0302_candidate_identity.py:147) 반복 기록 | 전용 104건 PASS |
| AC-2 position/channel 다름 → 별도 행 | PASS | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:90) 세 필드 직렬화, [test_hs_0302_candidate_identity.py](humansearch/tests/test_hs_0302_candidate_identity.py:186) 분리 시험 | 전용 104건 PASS |
| AC-3 두 연결 경쟁 → 1행·진 쪽 duplicate | FAIL | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:312) 기본 timeout 연결, 315행 즉시 쓰기 잠금, 326행 기본키 예외 번역, [test_hs_0302_candidate_identity.py](humansearch/tests/test_hs_0302_candidate_identity.py:218) 짧은 경쟁 | 400라운드 PASS이나 5.689초 장기 잠금 반례에서 raw `SQLITE_BUSY` |
| AC-4 빈 값·허용 밖 채널 거부·행 0 | PASS | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:124) 선검증, 139행 입력 묶음, [test_hs_0302_candidate_identity.py](humansearch/tests/test_hs_0302_candidate_identity.py:284) 거부 시험 | 전용 104건 PASS |
| 저장 경계 | FAIL | [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:256) DB 경계, 273행 보조 파일 경계, [humansearch-storage-contract.md](docs/sot/humansearch-storage-contract.md:80) 정본 요구 | DB/부모는 PASS, sidecar owner와 오류 원인 경계는 FAIL, 승인 root는 부분, 다른 UID는 NOT_RUN |
| 검증 연결 | PASS | [acceptance-hs-0302.sh](scripts/acceptance-hs-0302.sh:346) 수집·실행 정확 대조, 521행 고정 명부 집합 대조, [check-hs-0302-ci-wiring.rb](scripts/verify/check-hs-0302-ci-wiring.rb:43) 단일 run·제어연산자 차단, [verify.yml](.github/workflows/verify.yml:227) 전용 스텝 | 명부 104=수집 104, 누락 0·추가 0; 두 꼬리 모두 rc=1 |

→ 해석: 네 AC 중 AC-3이 장기 잠금 반례로 실패하고 저장 경계도 명시 규칙 두 곳이 닫히지 않아 전체 판정은 `REQUEST_CHANGES`입니다. 검증 연결 자체는 우회 반례까지 통과했습니다.

### 7. 기준선 검증 증거

시작 상태와 범위:

```text
git status --short: 출력 없음
ced77fe11fab78e4bf823dd5483d1eb74a936ce5
14 files changed, 3180 insertions(+), 1 deletion(-)
```

→ 해석: 검토 시작 시 원 지시의 HEAD와 일치했고 클론은 깨끗했습니다. 직접 검토한 핵심 대상은 제품 모듈 1개, 전용 시험 4개, 인수 스크립트, CI 배선 검사기, 필수 시험 명부, workflow, goal·저장 정본입니다.

전용 pytest 네 파일:

```text
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 5.20s
```

→ 해석: pytest(파이썬 시험 실행기)는 `-p no:cacheprovider`로 한 프로세스씩 실행했으며 기준선 104건이 전부 통과했습니다.

정적 검사와 타입 검사:

```text
All checks passed!
Success: no issues found in 48 source files
```

→ 해석: `ruff check src tests`와 `mypy src tests`는 각각 종료값 0이었습니다.

인수 검사와 CI 스텝 무결성:

```text
PASS: 검사 전후 저장소 상태 동일 — 검증기가 대상을 오염시키지 않았다
CHECKED: 22
OK(run-acceptance): scripts/acceptance-hs-0302.sh — 판정 22건, CHECKED 22

CHECKED: 24
VERDICT: PASS
```

→ 해석: `pipefail`을 켠 래퍼 기준 인수 판정 22건과 CI 스텝 무결성 24건이 종료값 0으로 통과했습니다. fail-closed(검사 불능이나 오류를 합격으로 바꾸지 않는 방식) 래퍼의 앞단 실패도 파이프에 숨지 않습니다.

### 8. 제품 규칙을 깨뜨린 반증 기록

| variant | 깨뜨린 규칙 | r4 결과 | 전용 네 파일 결과 | 생존 |
|---|---|---:|---:|---|
| (a) | commit 직전 `_verify_db_boundary` 재확인 제거 | 2 failed, 20 passed | 2 failed, 102 passed | 없음 |
| (b) | 재확인을 commit 뒤로 이동 | 2 failed, 20 passed | 2 failed, 102 passed | 없음 |
| (c) | `begin immediate` 제거 | 4 failed, 18 passed | 31 failed, 73 passed | 없음 |
| (d) | 쓰기 직전 `_verify_db_boundary` 제거 | 5 failed, 17 passed | 5 failed, 99 passed | 없음 |
| (e) | 키·DB 보호 root 공유 거부 제거 | 22 passed | 3 failed, 101 passed | r4 단독만 생존 |

→ 해석: `acc3869`이 고정한 쓰기 뒤 권한 완화 시험과 `ced77fe`의 확정 전 재확인은 (a)·(b)를 각각 잡았습니다. (b)는 오류가 나도 행이 남는 것을, (c)는 자동 확정과 트랜잭션 오류를, (d)는 경계 오류가 원문 DB 오류로 새는 것을 드러냈습니다. (e)는 전체 필수 묶음이 막지만 r4 분류만으로는 잡지 못했습니다. 모든 사본은 지정 `copies/<이름>`에서 import 경로를 확인했습니다.

핵심 실패 원문:

```text
(a) 2 failed, 20 passed / 2 failed, 102 passed
(b) E AssertionError: 확정 전에 잡아야 하므로 행이 남으면 안 된다
    E assert 1 == 0
(c) r4: 4 failed, 18 passed
    E sqlite3.OperationalError: cannot commit - no transaction is active
    전체: 31 failed, 73 passed
(d) E sqlite3.OperationalError: unable to open database file
    E Failed: DID NOT RAISE CandidateIdentityError
    E sqlite3.OperationalError: disk I/O error
(e) r4: 22 passed
    전체: 3 failed, 101 passed
```

→ 해석: 무엇을 어떻게 깨려 했는지와 실패 건수가 모두 남아 있으며, 제품 보호 규칙 네 개는 전용 전체 묶음에서 생존하지 않았습니다. 다섯 번째는 시험 분류의 LOW 잔여 위험입니다.

### 9. 명부 104건의 실제 수집 대조

node-id(pytest가 각 시험 사례를 식별하는 전체 이름)를 고정 명부와 실제 수집 결과의 정렬 집합으로 비교했습니다.

```text
collect_rc=0
required_count=104
actual_node_count=104
missing_count=0
extra_count=0
pytest_summary=104 tests collected in 0.28s
missing_sample=|
extra_sample=|
```

→ 해석: 단순히 “104”라는 숫자만 본 것이 아닙니다. [acceptance-hs-0302.sh](scripts/acceptance-hs-0302.sh:525)이 명부를 정렬하고 530행이 실제 수집 node-id를 정렬한 뒤 531~532행이 양방향 차집합을 냅니다. 527행은 명부 자체의 기대값도 정확히 104로 고정합니다.

### 10. verify.yml 꼬리 주입 2종

두 격리 사본에는 각각 `humansearch/src`, `humansearch/tests`, workflow를 복사했고, 두 사본 모두 `PYTHONPATH` import가 사본의 `candidate_identity.py`를 가리킴을 확인했습니다. variant 파일의 diff나 본문은 인용하지 않습니다.

```text
VARIANT=ci_or_true
WIRING_BAD: run 이 정확한 단일 명령이 아니다: "bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh || true"
WIRING_BAD: run 에 셸 제어 연산자 || 가 있다
WIRING_BAD: run 에 셸 제어 연산자 | 가 있다
RESULT import_rc=0 checker_rc=1

VARIANT=ci_echo_ok
WIRING_BAD: run 이 정확한 단일 명령이 아니다: "bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh ; echo ok"
WIRING_BAD: run 에 셸 제어 연산자 ; 가 있다
RESULT import_rc=0 checker_rc=1
```

→ 해석: 실패를 참으로 바꾸는 꼬리와 뒤에서 성공 문구를 실행하는 꼬리는 모두 동일 검사기에서 FAIL(exit 1)했습니다. [check-hs-0302-ci-wiring.rb](scripts/verify/check-hs-0302-ci-wiring.rb:50)은 정확한 단일 명령을 요구하고 51~55행은 셸 제어 연산자·조건·오류 무시를 별도로 차단합니다.

### 11. 변경 목적과 위험 분류

- [candidate_identity.py](humansearch/src/humansearch/candidate_identity.py:98): 후보 동일성 HMAC 계산과 한 번의 INSERT, 중복 번역, 입력·키·DB 경계를 구현한 고위험 저장·동시성 코드입니다.
- [test_hs_0302_candidate_identity.py](humansearch/tests/test_hs_0302_candidate_identity.py:147), `test_hs_0302_r2_hardening.py`, `test_hs_0302_r3_hardening.py`, [test_hs_0302_r4_db_boundary.py](humansearch/tests/test_hs_0302_r4_db_boundary.py:362): 중복·직렬화·정규화·경로·쓰기 뒤 재확인 회귀를 고정하는 시험입니다.
- [acceptance-hs-0302.sh](scripts/acceptance-hs-0302.sh:338), [check-hs-0302-ci-wiring.rb](scripts/verify/check-hs-0302-ci-wiring.rb:33), `hs-0302-required-tests.txt`, [verify.yml](.github/workflows/verify.yml:227): 시험을 실제 수집·실행하고 CI 무력화를 차단하는 검사기 자체입니다.
- [humansearch-hs-0302-candidate-identity-goal-2026-09-15.md](docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md:37)와 [humansearch-storage-contract.md](docs/sot/humansearch-storage-contract.md:74): 판정 기준과 후속 WU 경계를 정하는 문서입니다.

### 12. 미확인과 남은 위험

- 다른 UID(운영체제가 프로세스 소유자를 구분하는 사용자 번호)에서 구현자 쓰기는 `EACCES`, 실행기 쓰기는 성공하는지 확인하지 못했습니다. 계약이 동일 UID 환경에서는 `NOT_RUN`으로 두라고 정합니다.
- 원격 CI의 현재 실행 SHA·보호 규칙·실제 성공 상태는 확인하지 않았습니다. 로컬 동등 검사만 수행했습니다.
- 전체 저장소 pytest는 원 지시의 최소 검사에 없고 이번 재개에서도 실행하지 않았습니다. HS-03.02 전용 네 파일 104건, ruff, mypy, 인수, CI 무결성은 step 2~6의 채택 증거입니다.
- SQLite temp, backup, export staging, recovery quarantine, 암호화 파일과 독립 readback은 정본 263~265행과 goal 138~140행상 후속 WU 범위여서 실행하지 않았습니다.
- 승인된 운영 root가 정해진 뒤의 설정 연결은 아직 증거가 없습니다. 이번 판정은 `LOCAL_ONLY` HEAD에 한정됩니다.
- 후속 커밋으로 HEAD가 바뀌면 이 판정은 만료됩니다. 이 판정은 병합이나 배포 권한을 부여하지 않습니다.

### 13. 종료 증거

```text
timestamp=2026-09-15 21:00:19 KST
HEAD=ced77fe11fab78e4bf823dd5483d1eb74a936ce5
STATUS_BEGIN
STATUS_END
```

→ 해석: 종료 HEAD는 원 지시의 `ced77fe`와 일치하고 `git status --short`는 빈 출력입니다. 클론의 추적·미추적 파일을 편집하지 않았으며 기록과 variant는 지정된 `review-scratch` 아래에만 있습니다.
