# HS-03.02 후보 식별키 중복 없는 기록 — goal (2026-09-15)

위험등급 L3(저장 계층·개인정보 파생값·동시성). 기준은 `task/hs-0301-sqlite-schema-20260914`의 `7473ec8`이며, 제품 배송 상태는 `LOCAL_ONLY`다. 운영 배포·운영 쓰기·실제 후보 원문 저장은 이 WU 범위가 아니다.

## 1층 — 결론

`hs_candidates`에 후보 식별 행을 기록하는 제품 경로를 추가한다. 같은 `(position_ref, channel, candidate_ref)`는 한 행만 남고, 포지션이나 채널이 다르면 별도 행이어야 한다. 두 SQLite 연결이 동시에 같은 키를 넣어도 기본키 제약과 잠금 후 readback으로 `inserted`/`duplicate` 중 하나를 돌려야 한다. 빈 값, 허용 밖 채널, 느슨한 키·DB·sidecar 경계, Git 안 DB, symlink, 검사 뒤 경계 변경은 닫힌 오류로 거부한다. 11차 보강은 Git 밖의 0700/0600 호환 DB라도 `StorageSchemaResult.protected_root`가 승인한 root가 아니면 거부하고, connect 직전 DB 경로를 다른 호환 DB symlink로 바꿨다가 되돌리는 swap-back 경쟁도 거부하도록 고정한다. 12차는 승인 root를 호출자 인자가 아니라 초기화 장부에 결합한다 — `approved_root=db_path.parent`로 스스로 채운 값과 승인 root 안의 다른 파일명도 거부한다.

## 2층 — 판단 근거

기준 스키마의 `hs_candidates` 기본키는 `candidate_key_hmac` 하나다. 새 마이그레이션 없이 중복을 막으려면 세 식별값을 모두 HMAC 입력에 넣고 SQLite 기본키를 그대로 사용해야 한다. 응용 코드의 선조회 뒤 INSERT 방식은 두 연결이 동시에 "없음"을 볼 수 있어 AC-3을 만족하지 못한다.

검증 중 독립 리뷰는 세 차례 결함을 닫았다. 첫째, DB 마지막 구성요소 symlink와 Unicode 정규화 문제가 있었고 길이 접두 HMAC·NFC·마지막 파일 symlink 거부로 닫았다. 둘째, 쓰기 직전 DB 권한·위치 검사와 commit 전 재검증을 추가했다. 셋째, 장기 잠금에서 `SQLITE_BUSY` 원문이 새고 키 경로가 원인 사슬에 남는 문제를 닫힌 도메인 오류와 잠금 후 readback으로 닫았다. 11차 RED(`604974d`)는 "외부 private DB 자동 승인"과 "verify 뒤 connect 대상 swap-back"을 다시 열었고 `e25ac5e`가 닫았다. 다만 그 RED는 `approved_root` 인자가 없어 `TypeError`로 실패한 것이라 빠진 동작을 증명하지 못했고, `approved_root=db_path.parent`로 채우면 어떤 0700/0600 DB든 통과했다. 12차 RED(`3d936fd`)는 이 두 구멍을 "DID NOT RAISE"로 고정하고 `c146b78`이 초기화 장부 결합으로 닫았다.

## 현재 상태

기준 SHA는 `7473ec8c343cb906b3f510c2d50f72dc8004cedd`, 제품 코드는 `humansearch/src/humansearch/candidate_identity.py`다. 기준 `hs_candidates`만 쓰며 새 표·마이그레이션은 없다. 저장값은 HMAC 파생값과 포지션·채널 상태뿐이고 후보 원문·이름·URL·`observed_at`은 저장하지 않는다. 이전 APPROVE·시험은 현재 SHA의 증거로 사용하지 않는다.

## 인수 기준 (EARS)

- AC-1: When 같은 `(position_ref, channel, candidate_ref)`로 2회 기록하면 시스템은 `hs_candidates` 행 1개만 남기고 두 번째 결과를 `duplicate`로 돌려야 한다.
- AC-2: When `position_ref` 또는 `channel`이 다르면 시스템은 이름·이메일이 같아도 별도 행을 만들어야 한다.
- AC-3: While SQLite 연결 2개가 같은 키를 동시에 넣으면 시스템은 기본키 제약과 잠금 후 readback으로 1행을 보장하고 진 쪽을 `duplicate`로 돌려야 한다.
- AC-4: If 세 값 중 하나라도 비거나 `channel`이 허용값 밖이면 시스템은 행을 만들지 않고 `CandidateIdentityError`를 내야 한다.
- AC-5: When DB 또는 key path가 Git 안, symlink, wrong owner, wrong mode, non-regular file, key/DB root 중첩, 또는 검사 뒤 완화 상태이면 시스템은 commit 전에 닫힌 오류로 거부해야 한다.
- AC-6: When CI·명부·인수 검사·필수 node-id가 약화되면 시스템은 fail-closed로 막아야 한다.
- AC-7: When 호출자가 Git 밖의 별도 0700 directory와 0600 호환 DB를 직접 넘겨도 그 directory가 trusted `StorageSchemaResult.protected_root`와 같지 않으면 시스템은 행을 만들지 않고 `CandidateIdentityError`를 내야 한다.
- AC-8: When `_verify_db_boundary`가 끝난 뒤 `sqlite3.connect`가 열기 직전에 DB 경로가 다른 호환 DB symlink로 바뀌었다가 곧바로 원상복구되면 시스템은 원본·대체 DB 어느 쪽에도 행을 만들지 않고 `CandidateIdentityError`를 내야 한다.
- AC-9: When 호출자가 `approved_root`를 DB 부모 경로로 스스로 채워도 그 root가 이 프로세스에서 `initialize_humansearch_storage`를 통과한 root가 아니면 시스템은 행을 만들지 않고 `CandidateIdentityError`를 내야 한다.
- AC-10: When 승인 root 안이라도 초기화가 돌려준 DB 파일이 아닌 다른 0600 파일을 넘기면 시스템은 행을 만들지 않고 `CandidateIdentityError`를 내야 한다. 초기화 결과의 `(db_path, protected_root)` 쌍은 그대로 `inserted`여야 한다.
- AC-11: When 승인 DB 파일 또는 sidecar 가 hard link 로 다른 이름을 하나라도 더 가지면(`st_nlink != 1`) 시스템은 쓰기 직전과 확정 전에 행을 만들지 않고 `CandidateIdentityError`를 내야 한다. 밖으로 건 링크와 다른 DB 를 승인 자리에 건 링크 모두 해당한다.
- AC-12: When 승인 DB 를 치우고 다른 호환 DB 를 같은 이름으로 rename 해 두면(경로·권한·nlink 는 모두 정상) 시스템은 초기화 때 장부에 남긴 파일 정체성(`st_dev`·`st_ino`)과 달라 행을 만들지 않고 `CandidateIdentityError`를 내야 한다.
- AC-13: When 검사 직후 일반 파일 inode 교체 또는 connect 직후 swap-back이 일어나면 시스템은 SQLite가 연 새 파일의 OS descriptor 정체성을 승인 장부와 대조하고, 불명확하거나 다르면 쓰기 전에 닫힌 오류를 내야 한다. 초기화 결과의 정상 DB는 `inserted`여야 한다.
- AC-14: When 필수 R5 시험·명부·최소 기준·총 기준을 단독 또는 함께 낮추면 시스템은 인수 검사를 거부해야 한다. 검사기에서 R5 보호를 제거한 사본도 음성 fixture가 거부해야 한다.

## counter-AC

- HMAC 입력에서 `position_ref`나 `channel`을 빼서 다른 포지션·다른 채널 후보를 합친다.
- 구분자 결합으로 필드를 직렬화해 필드 안 구분자 주입이 같은 바이트열을 만든다.
- 제어문자 strip 또는 Unicode 분해형을 그대로 둬 같은 후보가 다른 키가 된다.
- NFKC까지 적용해 호환문자만 같은 서로 다른 포털 ID를 한 행으로 합친다.
- `_verify_db_boundary` 뒤 DB 경로·권한·sidecar를 바꾸고 commit 전에 다시 확인하지 않는다.
- DB path의 부모가 0700이고 DB가 0600이면 trusted config에서 나온 root인지 보지 않고 승인한다.
- 열린 연결의 `pragma database_list` main 경로를 승인 DB 경로와 대조하지 않아 swap-back이 검사 뒤 사라진다.
- 잠금 초과 `sqlite3.OperationalError`나 `FileNotFoundError` 경로를 공개 traceback으로 흘린다.
- 새 인수 스크립트·CI 스텝·필수 명부·기대 상수를 함께 낮춰 필수 시험을 조용히 지운다.
- `approved_root=db_path.parent`처럼 호출자가 승인 root를 스스로 채우면 통과한다.
- 승인 장부 대조나 열린 연결 `pragma database_list` 대조를 지워도 전용 시험이 초록이다(약화 변이 생존).
- 승인 경로에 다른 호환 DB 를 같은 이름으로 rename 해 두면 경로·권한·nlink 만 보고 승인한다(V1 7회차 결함 1).
- 열린 연결의 경로만 승인하고 새 descriptor의 inode를 보지 않아 regular-file swap-back이 통과한다.
- 필수 R5 시험 1개·명부 ID 1개·`MIN_R5_TESTS`와 `EXPECTED_REQUIRED_IDS`를 함께 낮춰도 118/118로 통과한다.

## 입출력·오류·경계 계약

- 입력: `CandidateIdentityInput(position_ref: str, channel: Literal["saramin","jobkorea","linkedin_rps"], candidate_ref: str, observed_at: str)`, `hmac_key_path: Path`, `approved_root: Path`.
- `approved_root`: `initialize_humansearch_storage(...)`가 검사를 통과한 뒤 프로세스 장부 `_APPROVED_DBS[protected_root] = ApprovedDb(db_path, st_dev, st_ino)`에 남긴 root여야 하고, `db_path`는 그 장부의 바로 그 파일(경로와 정체성)이어야 한다(`storage_schema.approved_db`). 검사 순서는 장부 → symlink 사슬 → owner/mode → regular → hard link → 정체성 → Git 밖 → sidecar 다. 함수는 DB 경로에서 승인 root를 추론하지 않으며, 장부는 같은 프로세스 안의 코드까지 막는 보안 경계가 아니라 경로 입력만으로는 승인이 생기지 않게 하는 설정 결합이다.
- 정규화: C0·DEL·C1 제어문자는 strip 전에 거부한다. 그 뒤 strip, NFC 정규화를 적용하고 빈 값·길이 초과를 거부한다. NFKC는 사용하지 않는다.
- `observed_at`: RFC3339 정규식으로 범위를 좁히고 `datetime.fromisoformat`으로 실제 날짜·시각·UTC offset을 확인한다. 검증만 하고 `hs_candidates`에는 저장하지 않는다.
- HMAC: `b"hs-candidate-key-v2"` 도메인 태그와 세 필드의 4바이트 big-endian 길이 접두 UTF-8 바이트열을 `sha256` HMAC으로 계산한다. 키는 32바이트 이상 raw bytes다.
- 키 파일: 현재 uid 소유, 부모 0700, 파일 0600, regular file, 전체 상위 사슬 symlink 없음. DB 보호 root와 양방향 포함 관계면 거부한다. 없거나 읽기 실패하면 경로 없는 `CandidateIdentityError`로 닫는다.
- DB 파일: Git worktree 밖, 현재 uid 소유, 부모 0700, 파일 0600, regular file, 전체 상위 사슬과 마지막 파일 symlink 없음. SQLite sidecar(`-journal`, `-wal`, `-shm`)도 같은 owner/mode/root/regular/symlink 규칙으로 본다.
- DB 승인 root: `db_path.parent == approved_root`를 검사하고, `approved_root` 자체도 owner 0700 regular directory boundary를 만족해야 한다. Git 밖 0700/0600 DB라도 approved root가 다르면 거부한다.
- connect 경계: 초기화 장부의 `(st_dev, st_ino)`와 connect 동안 새로 열린 승인 DB descriptor 1개와 검증된 journal/WAL 보조 descriptor의 `os.fstat` 값을 대조한다. `/dev/fd` 열거가 없거나 승인 DB descriptor가 0개·2개 이상·불일치하거나 추가 descriptor가 보호된 sidecar가 아닐 때이면 쓰기 전 실패한다. connect/close descriptor 교체의 자가 경쟁은 lock으로 막는다. `PRAGMA database_list`는 추가 경로 검사일 뿐 inode 증거가 아니다.
- 동시성: `BEGIN IMMEDIATE` 뒤 INSERT 한 번, commit 직전 `_verify_db_boundary` 재확인. 기본키 충돌만 `duplicate`로 접고 다른 무결성 오류는 그대로 올린다. `SQLITE_BUSY` 뒤 승자 행이 보이면 `duplicate`, 없으면 `CandidateIdentityError("db write lock wait exceeded")`.
- 오류: `CandidateIdentityError(StorageSchemaError)`. 메시지와 일반 traceback에 `candidate_ref`, `position_ref`, key bytes, HMAC hex, 보호 경로 원문을 넣지 않는다.

공식 근거: [Python sqlite3.connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect)는 path/URI만 받으며 열린 FD를 넘기는 공개 API가 없다. [SQLite open_v2](https://www.sqlite.org/c3ref/open.html)는 filename을 열고, [database_list](https://www.sqlite.org/pragma.html#pragma_database_list)는 이름을 반환한다. [Apple fstat](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fstat.2.html)은 열린 descriptor의 dev/inode를 반환한다.
실행 근거(macOS 15.7.3, Python 3.14.1, SQLite 3.51.1): `/proc/self/fd` 없음, `/dev/fd` 열거 가능, path 연결 직후 새 일반 파일 FD 1개·승인 inode 일치. int/file-object connect는 TypeError, `/dev/fd/N?mode=rw` URI는 OperationalError. 따라서 URI 우회 대신 단일 새 FD 관측이 불가능하면 fail-closed다.

## 검증 명령

필수: `uv run --frozen pytest tests/test_hs_0302*.py -q`, `uv run --frozen pytest -q`, `uv run --frozen ruff check src tests`, `uv run --frozen mypy src tests`, `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh`, `bash scripts/acceptance-hs-gates-mutations.sh`, `bash scripts/acceptance-hs-gates.sh`, `bash scripts/acceptance-hs-gates-antiforge.sh`, `bash scripts/acceptance-ci-step-integrity.sh`, `bash scripts/acceptance-principles-check.sh`, `git diff --check 7473ec8..HEAD`.

## 검증 장부

이전 장부의 PASS·APPROVE는 역사 기록이며 이번 최종 판정에 사용하지 않는다. 이번 세션의 RED는 `a0a2cdc`에서 R5 2 failed/8 passed와 검사기 변이 1 failed였고, 현재 GREEN은 R5 10 passed·인수 30/30이다. 최종 SHA 검증과 새 V1/V2만 최종 판정한다.

| 단계 | 상태 | 증거 |
|---|---|---|
| 현재 HEAD 반례 | REPRODUCED | 일반 inode를 검사 사이에 바꾸면 `inserted`, 교체 DB 1행·승인 inode 0행. R5 시험·명부·MIN·총 기준을 함께 낮추면 인수 27/27 통과(별도 임시 worktree). |
| RED `a0a2cdc` | EXPECTED_FAIL | R5 2 failed/8 passed (`DID NOT RAISE`); 독립 기준 검사 시험은 약화 생존으로 rc1. |
| 첫 GREEN | PASS(부분) | R5 10 passed, 전용 121 passed, ruff/mypy rc0, 인수 30/30. 최종 SHA 전체 게이트·V1/V2 전에는 완료 판정 금지. |

## 롤백·영향 반경·데이터 안전

- 롤백: PR 닫기 또는 이 WU 커밋 되돌리기. 마이그레이션 변경이 없어 DB 재초기화는 필요 없다.
- 영향 반경: `candidate_identity.py`(승인 장부·파일 정체성 결합, hard link 거부), `storage_schema.py`(`ApprovedDb` 장부·`approved_db`), HS-03.02 전용 시험 5파일, 인수 스크립트, CI wiring checker, 필수 node-id 명부, `verify.yml`, verification SOT.
- 데이터 안전: 후보 원문·이름·URL은 입력·저장·로그에 없다. 저장되는 후보 참조 파생값은 키 기반 HMAC이다. 시험 데이터는 합성이다.

## 결정 카드

**무엇을** — 초기화 장부의 inode와 connect 동안 새로 열린 승인 DB descriptor 1개 및 보호된 sidecar descriptor를 `fstat`으로 대조하고 불명확하면 쓰기 전에 거부한다.
**왜** — 경로·PRAGMA에는 실제 열린 inode가 없다.
**버린 길** — `/proc/self/fd` URI: macOS에 `/proc`가 없고 `/dev/fd` URI도 쓰기 연결에 실패했다.
**대가** — `/dev/fd` 열거로 단일 새 descriptor를 식별할 수 없는 VFS·환경·경쟁 상황에서는 정상 요청도 거부한다. 같은 프로세스의 악성 코드까지 막는 경계는 아니다.
**되돌리기** — 로컬 구현 커밋을 revert한다. 스키마·운영 데이터 변경은 없다.

## 비범위

HS-03.03 암호화 저장, HS-03.04 readback, HS-03.05 삭제, 실제 포털 후보 읽기, #96 `RunnerBoundary` 연동, Supabase, 운영 배포, merge, push.
