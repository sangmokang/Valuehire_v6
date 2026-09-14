# HumanSearch 저장·보존·삭제 계약 (SOT)

최종 갱신: 2026-09-14

## 1층 — 결론

HumanSearch가 후보 상세, 이력서, LinkedIn Recruiter 상세, 검색 조건, 관측 연락처, 저장 의도를 기록하려면
원본은 Git 밖의 단일 SQLite 장부와 보호 파일 저장소에 암호화해 보존하고, Supabase는 그 장부에서 파생된
내보내기 결과로만 다룬다.

열람한 증거는 전량 저장 대상이다. 저장 또는 독립 readback이 실패하면 실행기는 다음 후보로 넘어가지 않고
순회를 중단해야 한다. 보존은 무기한이며 삭제는 명시적 purge 요청으로만 실행한다. purge 결과 영수증에는
후보자 PII를 넣지 않는다.

이 문서는 저장 정책과 후속 구현 경계를 확정한다. SQLite 마이그레이션, 암호화 알고리즘 구현, 키 저장 구현,
OS 계정 분리 실행기, Supabase 내보내기 코드는 후속 WU가 소유한다.

## 2층 — 판단 근거

후보 원문 저장의 실패 방식은 세 가지다. 하나는 저장 성공과 열람 완전성을 같은 상태로 접어 부분 열람 원문을
저장했다는 이유로 evidence를 complete로 승격하는 것이다. 둘째는 저장 거부 중 이미 열람한 원문을 잃어 재시도와
감사를 불가능하게 만드는 것이다. 셋째는 Git·로그·원격 파생 저장소에 후보자 PII나 세션 값을 남기는 것이다.
그래서 저장 정책은 열람 증거 계약 `docs/sot/humansearch-evidence-contract.md`의 complete/partial/failed 판정,
독립 readback, Git 금지 경계와 함께 움직여야 한다.

SQLite를 원본으로 두는 이유는 재시작, 중복 방지, 의도 기록, purge, Supabase 내보내기 outbox가 하나의
권위 장부를 공유해야 하기 때문이다. Supabase는 운영 공유와 결과 확인에 쓰되 원본 판정 권한을 갖지 않는다.

**무엇을** — 후보 저장의 원본 위치, 암호화·키 경계, 보존·삭제, readback, Git 유출 금지, 연락처 수집 범위를
정한다.

**왜** — HS-03 저장 구현이 "어디에 무엇을 평문으로 남겨도 되는가"를 다시 추측하지 않게 하기 위해서다.

**버린 길** — 파일 저장만으로 DB 통합 완료라고 부르는 길, Supabase를 원본으로 삼는 길, 만료일 자동 삭제를
기본값으로 두는 길, 보이지 않는 연락처를 추정하는 길을 버린다.

**대가** — 모든 저장은 암호화와 독립 readback을 거쳐야 하므로 첫 구현이 느려지고, OS 권한 분리는 같은 UID
안의 하위 에이전트 검토만으로 증명할 수 없다.

**되돌리기** — 후속 구현 전에는 이 문서와 연결 goal을 되돌리면 된다. HS-03 이후에는 SQLite migration,
암호화 저장 코드, readback 시험, purge 시험을 같은 변경에서 되돌려야 한다.

## 3층 — 정본 계약

### 1. 적용 범위

이 계약은 `saramin`, `jobkorea`, `linkedin_rps` 채널의 후보 상세, 이력서, 검색 조건, 관측 연락처, 저장 의도,
readback 결과, purge 결과에 적용한다.

브라우저 선택과 중단은 `docs/sot/humansearch-browser-contract.md`가 소유한다. 열람 증거 필드는
`docs/sot/humansearch-evidence-contract.md`가 소유한다. 이 문서는 그 증거를 저장하고 보존하는 정책만
소유한다.

### 2. 원본과 파생 저장

단일 원본은 로컬 SQLite 장부다. 후보 식별, 검색 실행, 저장 의도, 증거 manifest, 암호화 파일 참조,
readback 상태, purge 상태, Supabase outbox는 모두 이 원본 장부의 행으로 연결돼야 한다.

Supabase는 SQLite 원본에서 생성된 파생 저장이다. Supabase write 성공, remote row id, remote readback hash는
원본 SQLite의 outbox 상태를 갱신할 수 있지만, 로컬 저장 완료를 대신하지 않는다. Supabase 장애나 네트워크
차단은 로컬 저장 완료를 취소하지 않으며 outbox를 미확정 상태로 남긴다.

저장 상태와 열람 완전성은 독립이다. `storage_status=confirmed`는 원문과 manifest를 손실 없이 저장하고
독립 readback으로 검증했다는 뜻이다. `coverage_status=partial`인 원문도 성공 저장될 수 있지만, 그 저장 성공은
`coverage_status=complete`로 승격시키지 않는다. 반대로 `coverage_status=complete`라도 저장·복호화·관계 readback이
실패하면 `storage_status=confirmed`가 아니다.

검사 명령:

```bash
rg -n '단일 원본|SQLite|Supabase|파생|outbox|로컬 저장 완료를 대신하지 않는다|저장 상태와 열람 완전성은 독립|partial.*complete' docs/sot/humansearch-storage-contract.md
```

### 3. 보호 저장 위치와 권한

원본 DB와 암호화 파일 저장소는 Git 밖에 있어야 한다. 기본 경로는 후속 HS-03/04 구현 WU가 승인한
운영 설정에서 정하되, 저장소 안 `data/`, `artifacts/`, `private-reviews/`, 추적 파일, PR 본문, 일반 로그에
원본 후보 데이터·세션 값·키를 쓰지 않는다.

보호 디렉터리는 mode `0700`, 원본 DB·캡처·manifest·암호문 파일은 mode `0600`이어야 한다. 구현은 쓰기 전에
부모 디렉터리의 owner, mode, symlink 여부, 실제 경로가 승인된 보호 root 안인지 확인해야 한다. 생성은 restrictive
mode 또는 restrictive `umask` 안에서 수행하고, 쓰기 뒤 owner/mode가 바뀌지 않았는지 다시 확인한다. 권한 완화,
소유자 불일치, symlink, 승인 root 탈출은 저장 실패다.

권한 계약은 SQLite 본체만 보지 않는다. DB와 같은 보호 범위 안의 WAL, SHM, rollback journal, SQLite temp 파일,
백업, export staging, recovery quarantine 파일도 같은 owner/mode/root/symlink 규칙을 따라야 한다. HS-03 후속
구현은 이 보조 파일들이 평문 원본이나 완화 권한으로 생기지 않는지 시험해야 한다.

OS 권한 분리는 같은 사용자 안의 에이전트 분리와 다르다. 독립 실행기 WU는 쓰기 가능한 UID와 구현자 UID가
다른지, 구현자 쓰기가 `EACCES`로 실패하는지, 실행기 쓰기가 성공하는지, symlink 우회가 거부되는지 따로
증명해야 한다. 같은 UID 분리만 가능한 환경이면 OS 격리 상태는 `NOT_RUN`이다.

검사 명령:

```bash
rg -n 'Git 밖|0700|0600|umask|쓰기 전에|WAL|SHM|journal|temp|백업|EACCES|symlink|같은 UID|NOT_RUN' docs/sot/humansearch-storage-contract.md
```

### 4. 암호화와 키 경계

후보 원문, 캡처, 텍스트 추출물, 관측 연락처, 민감 URL 원문, 검색 조건 원문 중 후보 식별로 이어지는 값은
보호 저장소에 암호화해 저장한다. Git에는 비민감 지문, schema, 계약, 테스트 코드만 둔다.

현재 HumanSearch 코드에는 재사용 가능한 암호화 저장 구현이 없다. invoice 저장 코드는 채용 수수료 도메인의
SQLite/Supabase 동기화 코드이며 HumanSearch 후보 원문 암호화 구현으로 재사용하지 않는다. 따라서 HS-03.03은
새 crypto 라이브러리나 의존성을 이 문서에서 임의 선택하지 말고, Python 표준 라이브러리·OS 키 저장소·이미
승인된 프로젝트 의존성 중 하나를 별도 계약으로 확정한 뒤 구현해야 한다.

키 원본은 암호문과 같은 디렉터리에 두지 않는다. 키 원본, 복호화 권한, 키 없음, 잘못된 키, 손상 암호문,
권한 없음의 오류는 서로 구분한다. 키 값을 stdout, stderr, 일반 로그, PR 본문, Git 파일에 쓰지 않는다.

검사 명령:

```bash
rg -n '암호화|현재 HumanSearch 코드에는 재사용 가능한 암호화 저장 구현이 없다|새 crypto 라이브러리|키 원본|키 없음|잘못된 키|손상 암호문' docs/sot/humansearch-storage-contract.md
```

### 5. 입력 계약

저장 요청은 아래 논리 입력을 가져야 한다. 후속 구현은 타입이나 JSON schema로 같은 의미를 고정한다.

| 필드 | 필수 | 계약 |
|---|---:|---|
| `run_id` | 예 | 실행 또는 재개 실행 식별자다. |
| `position_ref` | 예 | ClickUp 포지션 또는 승인된 포지션 식별자다. |
| `channel` | 예 | `saramin`, `jobkorea`, `linkedin_rps` 중 하나다. |
| `candidate_key` | 예 | `(position_ref, channel, source_url_hash 또는 안정 후보 ref)`에서 계산한 중복 방지 키다. |
| `evidence_manifest` | 예 | evidence SOT의 필수 필드를 만족해야 한다. |
| `encrypted_payload_refs` | 예 | 암호화된 원문·캡처·추출물 참조 목록이다. Git 경로가 아니다. |
| `observed_contact_fields` | 예 | 화면에 보인 연락처의 상태만 담는다. 보이지 않는 값 추정은 금지다. |
| `storage_intent_id` | 예 | write-ahead intent 식별자다. |

토큰, 쿠키, Playwright storageState, CDP cookie dump, 세션 헤더, bearer 값은 저장 입력이 아니다. 입력 어댑터가
이 값을 발견하면 후보 저장을 계속하지 말고 금지 입력 오류를 기록해야 한다. 이미 열람한 후보 원문이 있다면
세션 비밀값을 제거한 암호화 recovery 격리로만 보존하고 intent 상태를 `forbidden_input`으로 남긴다. 세션 토큰,
쿠키, bearer, storageState 원문은 영구 격리 대상이 아니며 즉시 폐기하고 비밀값 제거 여부와 실패 사유만 기록한다.

LinkedIn/RPS 연락처는 화면에 표시된 1촌 연락처만 `observed_contact_fields`에 남긴다. 보이지 않는 이메일,
전화번호, 주소, 메신저 ID를 추정하거나 외부 lookup으로 보강하지 않는다. 연락처 공유는 저장과 별도 계약이
승인한 출력 경로에서만 가능하다.

검사 명령:

```bash
rg -n '`candidate_key`|`evidence_manifest`|`encrypted_payload_refs`|토큰|쿠키|storageState|recovery 격리|비밀값 제거|1촌|추정' docs/sot/humansearch-storage-contract.md
```

### 6. 출력 계약

저장 결과는 아래 상태 중 하나다.

| 상태 | 의미 | 다음 동작 |
|---|---|---|
| `confirmed` | SQLite intent, 암호화 파일 write, 독립 readback hash가 모두 일치했다. | 다음 후보 진행 가능 |
| `partial` | intent나 일부 파일은 남았지만 readback 또는 manifest 연결이 끝나지 않았다. | 순회 중단, 재시도 가능 상태로 남김 |
| `failed` | 저장 전에 실패했거나 복구 가능한 원본을 남기지 못했다. | 순회 중단 |
| `forbidden_input` | 토큰·쿠키·세션 값·미승인 연락처 등 금지 입력이 있었다. | 순회 중단, 비밀값 제거 후 후보 원문만 암호화 recovery 격리 |
| `recovery_required` | purge, 권한, 파일 손상, 중간 종료 뒤 사람이 확인해야 한다. | 자동 성공 보고 금지 |

`confirmed`가 아니면 저장 완료가 아니다. 저장 실패나 readback 실패 상태에서 실행기는 다음 후보 상세를 열거나
다음 채널 순회를 시작하지 않는다.

독립 readback은 저장한 ciphertext 파일의 hash만 대조하는 절차가 아니다. 별도 프로세스 또는 별도 DB 연결이
writer의 메모리 객체를 재사용하지 않고 SQLite intent, manifest, 암호화 파일 참조, 복호화 payload hash,
coverage 상태, candidate key 관계를 다시 읽어 일치해야 한다. readback 구현은 같은 함수의 반환값이나 writer
메모리 캐시를 성공 증거로 쓰지 않는다.

검사 명령:

```bash
rg -n '`confirmed`|`partial`|`failed`|`forbidden_input`|`recovery_required`|다음 후보|독립 readback|복호화 payload|writer의 메모리' docs/sot/humansearch-storage-contract.md
```

### 7. 오류 계약

후속 구현은 최소한 아래 오류를 구분해야 한다.

| 오류 | 판정 |
|---|---|
| 필수 evidence 필드 누락 | 저장 거부, 순회 중단 |
| coverage/readback 상태 불일치 | 저장 거부, 순회 중단 |
| 암호화 파일 쓰기 실패 | `partial` 또는 `failed`, 순회 중단 |
| 권한 mode가 0700/0600보다 넓음 | 저장 실패, 순회 중단 |
| 키 없음·잘못된 키·복호화 실패 | readback 실패, 순회 중단 |
| 토큰·쿠키·세션 값 입력 | 비밀값 즉시 폐기, 후보 원문은 비밀값 제거 뒤 암호화 recovery 격리, 순회 중단 |
| Supabase write 실패 | outbox 미확정, 로컬 저장 상태는 별도 유지 |
| purge 일부 실패 | `recovery_required`, PII 없는 영수증 |
| evidence 필수 필드 또는 coverage 오류 | intent와 암호화 recovery 격리 상태 보존, 순회 중단 |

오류는 빈 값, 성공, `None`, 기본값으로 접지 않는다. 상태와 실패 사유를 SQLite 원본에 기록하되 후보 원문 PII는
일반 로그에 쓰지 않는다.

검사 명령:

```bash
rg -n '필수 evidence|coverage 오류|recovery 격리|0700/0600|키 없음|forbidden_input|Supabase write 실패|purge 일부 실패|PII 없는 영수증' docs/sot/humansearch-storage-contract.md
```

### 8. 보존과 purge

보존 기간은 무기한이다. 자동 만료 삭제는 현재 계약에 없다. 삭제는 명시적 purge 요청으로만 실행한다.

purge는 대상 후보 또는 실행 범위가 모호하면 실행하지 않는다. 성공한 purge는 SQLite 원본에 tombstone,
대상 비민감 지문, 삭제 시각, 삭제한 보호 참조 수, 실패 참조 수를 기록한다. purge 영수증에는 이름, 이메일,
전화번호, 이력서 본문, 원본 URL 경로, 세션 값, 암호화 키를 넣지 않는다.

일부 파일이나 DB 행 삭제가 실패하면 성공으로 보고하지 않고 `recovery_required`를 남긴다. 같은 purge 요청을
다시 실행할 수 있어야 하며, 이미 삭제된 보호 참조는 멱등하게 처리한다.

purge는 SQLite 원본 행만 삭제 표시하는 작업이 아니다. 암호화 파일, manifest, recovery quarantine, Supabase
파생 row, pending outbox, export staging을 함께 처리해야 한다. Supabase 삭제나 remote tombstone write가 실패하면
파생 저장이 남아 있음을 `recovery_required`로 남긴다. purge된 후보의 outbox는 재생성되거나 재전송되지 않아야 하며,
tombstone은 후속 export가 같은 후보 PII를 다시 만들지 못하게 하는 차단 상태다. 단순 DB 삭제 표시만으로 모든 PII
삭제 완료라고 보고하지 않는다.

검사 명령:

```bash
rg -n '무기한|자동 만료 삭제|명시적 purge|모호|PII|recovery_required|멱등|tombstone|outbox|Supabase|재생성|단순 DB 삭제' docs/sot/humansearch-storage-contract.md
```

### 9. Git과 운영 프로젝트 입력 금지

원본 이력서, 후보 상세 본문, 캡처, ARIA/DOM 원문, 후보 이름, 연락처, 민감 URL, 토큰, 쿠키, 세션 값, 암호화 키,
운영 프로젝트 입력값은 Git에 넣지 않는다. PR 본문과 작업 보고에는 비민감 지문, 상태, count, 채널, 포지션 ref,
정규화 origin 수준의 provenance만 허용한다.

운영 프로젝트 입력을 Git fixture로 만들지 않는다. 합성 fixture가 필요하면 후보자 PII와 실제 프로젝트 값을
포함하지 않는 테스트 전용 값만 사용한다.

검사 명령:

```bash
rg -n 'Git에 넣지 않는다|운영 프로젝트 입력|PR 본문|비민감 지문|합성 fixture' docs/sot/humansearch-storage-contract.md
```

### 10. counter-AC

| # | counter-AC | 차단 조건 |
|---:|---|---|
| 1 | 평문 원본 저장 | 후보 원문·캡처·연락처를 암호화 없이 보호 저장소나 Git에 남긴다. |
| 2 | readback 없는 성공 | 파일 write만 보고 `confirmed`로 처리한다. |
| 3 | 저장 실패 뒤 순회 지속 | `partial`, `failed`, `forbidden_input`, `recovery_required` 뒤 다음 후보를 연다. |
| 4 | Supabase 원본화 | remote write/readback 성공을 로컬 SQLite 원본 성공으로 대체한다. |
| 5 | 자동 만료 삭제 | 명시적 purge 없이 보존 기간 만료로 원본을 삭제한다. |
| 6 | PII 영수증 | purge 영수증에 이름·연락처·원본 URL 경로·본문이 들어간다. |
| 7 | 같은 UID 독립 착각 | 같은 사용자 하위 에이전트 검토를 OS 쓰기 권한 분리 증거로 부른다. |
| 8 | 쿠키·토큰 수집 | CDP/Playwright 쿠키·세션 값을 후보 저장 payload에 넣는다. |
| 9 | 보이지 않는 연락처 추정 | LinkedIn/RPS에서 표시되지 않은 이메일·전화번호를 추정해 저장한다. |
| 10 | Git fixture 오염 | 실제 운영 프로젝트 입력이나 후보 PII를 테스트 fixture로 커밋한다. |
| 11 | partial 승격 | 부분 열람 원문을 성공 저장했다는 이유로 evidence complete로 바꾼다. |
| 12 | readback 캐시 재사용 | writer 메모리 객체나 같은 함수 반환값으로 독립 readback을 대신한다. |
| 13 | purge 파생 누락 | SQLite tombstone만 남기고 Supabase 파생 row나 pending outbox 재생성을 방치한다. |

검사 명령:

```bash
rg -n '평문 원본 저장|readback 없는 성공|저장 실패 뒤 순회 지속|Supabase 원본화|자동 만료 삭제|PII 영수증|같은 UID|쿠키|보이지 않는 연락처|Git fixture|partial 승격|readback 캐시|purge 파생' docs/sot/humansearch-storage-contract.md
```

### 11. 후속 구현 경계

HS-03.01은 SQLite migration, WAL/SHM/journal/temp/백업 권한, 원자성을 소유한다. HS-03.03은 이 문서의
암호화·키 경계를 구현 계약으로 확정한 뒤 암호화 저장을 소유한다. HS-03.04는 intent, 파일, 독립 readback
연결을 소유한다. HS-04.02~04는 독립 실행기 쓰기 권한, 대상 SHA, 원본 출력 보존, Git 유출 방지를 소유한다.

이번 문서 WU는 HS-02 필드를 복제해 새 범용 검사기를 만들지 않는다. evidence SOT 필드는 참조하고, 저장 정책과
실패 상태만 고정한다.
