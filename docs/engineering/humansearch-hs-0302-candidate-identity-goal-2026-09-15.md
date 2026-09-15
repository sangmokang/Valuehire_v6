# HS-03.02 후보 식별키 중복 없는 기록 — goal (2026-09-15)

위험등급 L3(저장 계층·개인정보 파생값·동시성). 기준은 `task/hs-0301-sqlite-schema-20260914`의 `7473ec8`이며, 제품 배송 상태는 `LOCAL_ONLY`다. 운영 배포·운영 쓰기·실제 후보 원문 저장은 이 WU 범위가 아니다.

## 1층 — 결론

`hs_candidates`에 후보 식별 행을 기록하는 제품 경로를 추가한다. 같은 `(position_ref, channel, candidate_ref)`는 한 행만 남고, 포지션이나 채널이 다르면 별도 행이어야 한다. 두 SQLite 연결이 동시에 같은 키를 넣어도 기본키 제약과 잠금 후 readback으로 `inserted`/`duplicate` 중 하나를 돌려야 한다. 빈 값, 허용 밖 채널, 느슨한 키·DB·sidecar 경계, Git 안 DB, symlink, 검사 뒤 경계 변경은 닫힌 오류로 거부한다. 11차 보강은 Git 밖의 0700/0600 호환 DB라도 `StorageSchemaResult.protected_root`가 승인한 root가 아니면 거부하고, connect 직전 DB 경로를 다른 호환 DB symlink로 바꿨다가 되돌리는 swap-back 경쟁도 거부하도록 고정한다. 12차는 승인 root를 호출자 인자가 아니라 초기화 장부에 결합한다 — `approved_root=db_path.parent`로 스스로 채운 값과 승인 root 안의 다른 파일명도 거부한다.

## 2층 — 판단 근거

기준 스키마의 `hs_candidates` 기본키는 `candidate_key_hmac` 하나다. 새 마이그레이션 없이 중복을 막으려면 세 식별값을 모두 HMAC 입력에 넣고 SQLite 기본키를 그대로 사용해야 한다. 응용 코드의 선조회 뒤 INSERT 방식은 두 연결이 동시에 "없음"을 볼 수 있어 AC-3을 만족하지 못한다.

검증 중 독립 리뷰는 세 차례 결함을 닫았다. 첫째, DB 마지막 구성요소 symlink와 Unicode 정규화 문제가 있었고 길이 접두 HMAC·NFC·마지막 파일 symlink 거부로 닫았다. 둘째, 쓰기 직전 DB 권한·위치 검사와 commit 전 재검증을 추가했다. 셋째, 장기 잠금에서 `SQLITE_BUSY` 원문이 새고 키 경로가 원인 사슬에 남는 문제를 닫힌 도메인 오류와 잠금 후 readback으로 닫았다. 11차 RED(`604974d`)는 "외부 private DB 자동 승인"과 "verify 뒤 connect 대상 swap-back"을 다시 열었고 `e25ac5e`가 닫았다. 다만 그 RED는 `approved_root` 인자가 없어 `TypeError`로 실패한 것이라 빠진 동작을 증명하지 못했고, `approved_root=db_path.parent`로 채우면 어떤 0700/0600 DB든 통과했다. 12차 RED(`3d936fd`)는 이 두 구멍을 "DID NOT RAISE"로 고정하고 `c146b78`이 초기화 장부 결합으로 닫았다.

## 현재 상태

기준 SHA는 `7473ec8c343cb906b3f510c2d50f72dc8004cedd`, 제품 코드는 `humansearch/src/humansearch/candidate_identity.py`다. 기준 `hs_candidates`만 쓰며 새 표·마이그레이션은 없다. 저장값은 HMAC 파생값과 포지션·채널 상태뿐이고 후보 원문·이름·URL·`observed_at`은 저장하지 않는다. 역사적 V1 6회차 원문(eb0b225 대상, 292줄, sha256 `a5feee91cc9ab3e39aa2063d26cf2230a540e00ae9de0ff36817ded3b298dede`)은 P11③ 3,000줄 상한 때문에 추적 파일에서 빼고 `private-reviews/hs-0302/`에 그대로 둔다. 현재 HEAD의 승인 근거는 아래 12차 장부의 새 V1·V2뿐이다.

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

## 입출력·오류·경계 계약

- 입력: `CandidateIdentityInput(position_ref: str, channel: Literal["saramin","jobkorea","linkedin_rps"], candidate_ref: str, observed_at: str)`, `hmac_key_path: Path`, `approved_root: Path`.
- `approved_root`: `initialize_humansearch_storage(...)`가 검사를 통과한 뒤 프로세스 장부 `_APPROVED_DB_PATHS[protected_root] = db_path`에 남긴 root여야 하고, `db_path`는 그 장부의 바로 그 파일이어야 한다(`storage_schema.approved_db_path`). 함수는 DB 경로에서 승인 root를 추론하지 않으며, 장부는 같은 프로세스 안의 코드까지 막는 보안 경계가 아니라 경로 입력만으로는 승인이 생기지 않게 하는 설정 결합이다.
- 정규화: C0·DEL·C1 제어문자는 strip 전에 거부한다. 그 뒤 strip, NFC 정규화를 적용하고 빈 값·길이 초과를 거부한다. NFKC는 사용하지 않는다.
- `observed_at`: RFC3339 정규식으로 범위를 좁히고 `datetime.fromisoformat`으로 실제 날짜·시각·UTC offset을 확인한다. 검증만 하고 `hs_candidates`에는 저장하지 않는다.
- HMAC: `b"hs-candidate-key-v2"` 도메인 태그와 세 필드의 4바이트 big-endian 길이 접두 UTF-8 바이트열을 `sha256` HMAC으로 계산한다. 키는 32바이트 이상 raw bytes다.
- 키 파일: 현재 uid 소유, 부모 0700, 파일 0600, regular file, 전체 상위 사슬 symlink 없음. DB 보호 root와 양방향 포함 관계면 거부한다. 없거나 읽기 실패하면 경로 없는 `CandidateIdentityError`로 닫는다.
- DB 파일: Git worktree 밖, 현재 uid 소유, 부모 0700, 파일 0600, regular file, 전체 상위 사슬과 마지막 파일 symlink 없음. SQLite sidecar(`-journal`, `-wal`, `-shm`)도 같은 owner/mode/root/regular/symlink 규칙으로 본다.
- DB 승인 root: `db_path.parent == approved_root`를 검사하고, `approved_root` 자체도 owner 0700 regular directory boundary를 만족해야 한다. Git 밖 0700/0600 DB라도 approved root가 다르면 거부한다.
- connect 경계: verification 직후의 DB 실제 파일과 SQLite가 여는 대상이 같은 안정 파일이어야 한다. connect 전후 swap-back으로 경로 표면만 정상화하는 공격은 허용하지 않는다.
- 동시성: `BEGIN IMMEDIATE` 뒤 INSERT 한 번, commit 직전 `_verify_db_boundary` 재확인. 기본키 충돌만 `duplicate`로 접고 다른 무결성 오류는 그대로 올린다. `SQLITE_BUSY` 뒤 승자 행이 보이면 `duplicate`, 없으면 `CandidateIdentityError("db write lock wait exceeded")`.
- 오류: `CandidateIdentityError(StorageSchemaError)`. 메시지와 일반 traceback에 `candidate_ref`, `position_ref`, key bytes, HMAC hex, 보호 경로 원문을 넣지 않는다.

## 검증 명령

필수: `uv run --frozen pytest tests/test_hs_0302*.py -q`, `uv run --frozen pytest -q`, `uv run --frozen ruff check src tests`, `uv run --frozen mypy src tests`, `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh`, `bash scripts/acceptance-hs-gates-mutations.sh`, `bash scripts/acceptance-hs-gates.sh`, `bash scripts/acceptance-hs-gates-antiforge.sh`, `bash scripts/acceptance-ci-step-integrity.sh`, `bash scripts/acceptance-principles-check.sh`, `git diff --check 7473ec8..HEAD`.

## 검증 장부

| 단계 | 상태 | 증거 |
|---|---|---|
| strict 원칙 로드 | PASS | `bash scripts/acceptance-principles-check.sh` → `CHECKED: 34`, rc=0. `docs/sot/coding-principles.md`, `docs/sot/principles.yaml` 직접 로드 |
| 1~6차 | PASS | `838577b`→`c14638d`: 중복·경쟁·입력·Unicode·CI 배선·명부 약화 방어. 주요 출력: 28→311 passed, 인수 `CHECKED: 11/20/22`, gates mutations `blocked 6/6`, 변이 생존 0 |
| 7차 DB 경계 | PASS | WU-D 재현: DB 0644/부모 0755 및 Git 안 DB가 `inserted rows=1`. `29f5f74`/`a70bee8` RED, `09602ac` GREEN. commit 전 경계 재확인과 sidecar 단일 lstat 적용. 전체 329 passed |
| 8차 키 경로 경쟁 | PASS | `58d8cb2` RED, `d84dc41` GREEN. 최종 검증: `331 passed`, ruff/mypy rc0, 인수 `CHECKED: 22`, ci-step `CHECKED: 24`, principles `CHECKED: 34`, gates `COLLECTED: 331` |
| V1 4회차 | 역사적 APPROVE | @`d84dc41`, 전용 102 passed, 인수 `CHECKED: 22`, LOW 1건. 더 최신 V1 6회차와 11차 RED가 있어 원문 파일은 diff 축소 과정에서 제거 |
| 9차 commit 전 재검증 | PASS | `acc3869` RED, `ced77fe` GREEN. DB 권한이 INSERT 뒤 완화되면 commit 전 거부·행 0. r4 22 passed, 전체 333 passed, ruff/mypy rc0, 인수 `CHECKED: 22` |
| V1 5회차 | REQUEST_CHANGES | @`ced77fe`: 장기 잠금 `SQLITE_BUSY`, 닫힌 오류 원인 사슬, sidecar owner 검사 결함. 원문은 superseded라 diff 축소 과정에서 삭제하고 6회차 최종 원문을 보존 |
| 10차 최종 GREEN | PASS | `352de58`/`f36c722` RED 7 failed, `eb0b225` GREEN. 잠금 초과 readback, `from None`, sidecar `st_uid` 대조. 변이 9종 전용 4파일 기준 생존 0 |
| 10차 최종 검증 | PASS | 인수 `CHECKED: 22`, principles `CHECKED: 34`, `git diff --check` rc0, ci-step-integrity 재실행 `CHECKED: 24 VERDICT: PASS`, hs-gates-mutations `blocked 6/6`, hs-gates `COLLECTED: 340`, antiforge `3/3` |
| V1 6회차 | 역사적 APPROVE | @`eb0b225`, AC-1~4·저장 경계·검증 연결 PASS, OS 분리 NOT_RUN, variant 생존 0, 명부 111=수집 111. 원문은 보존하되 `604974d` 이후 현재 HEAD 승인 근거로 쓰지 않는다 |
| 11차 approved-root/swap-back | PASS(부분) | `604974d` RED → `e25ac5e` GREEN. 재검증: 604974d의 r5 2건은 `TypeError: unexpected keyword argument 'approved_root'`로 실패해 빠진 동작의 RED가 아니었다(2026-09-15T15:54Z 격리 재실행). `pragma database_list`가 symlink를 실제 경로로 푸는 것은 sqlite 3.51.1에서 실측 |
| 12차 승인 장부 결합 | PASS | `3d936fd` RED: `test_self_approved_private_compatible_db_is_refused`·`test_other_db_filename_inside_approved_root_is_refused` "DID NOT RAISE" 2 failed·32 passed. `c146b78` GREEN: 전용 116 passed, ruff·mypy rc0. 인수 검사에 약화 변이 2종(승인 장부 대조 제거 → 3건 검출, 열린 연결 대조 제거 → 1건 검출)과 마이그레이션 블록 대조·음성 대조군 추가, run-acceptance `CHECKED: 25` rc0 |
| 범위 밖 변경 회수 | PASS | `b25a68d`가 바꾼 전역 검사기 `scripts/acceptance-principles-mutations.sh`·`scripts/verify/check-strict-principles-skills.sh`(파일 한도 500→P11 600)와 정본 3행은 HS-03.02 인수 기준 밖이고 검사 강도를 낮추므로 기준 커밋 상태로 되돌린다. P11 hard 600과 검사기 500의 드리프트는 별도 WU 대상이다 |
| push·Draft PR | NOT_RUN | 사용자 지시와 공통 규칙상 이 세션에서는 push·PR 갱신을 하지 않는다 |

## 롤백·영향 반경·데이터 안전

- 롤백: PR 닫기 또는 이 WU 커밋 되돌리기. 마이그레이션 변경이 없어 DB 재초기화는 필요 없다.
- 영향 반경: `candidate_identity.py`, `storage_schema.py`(승인 장부 3줄·`approved_db_path`), HS-03.02 전용 시험 5파일, 인수 스크립트, CI wiring checker, 필수 node-id 명부, `verify.yml`, verification SOT.
- 데이터 안전: 후보 원문·이름·URL은 입력·저장·로그에 없다. 저장되는 후보 참조 파생값은 키 기반 HMAC이다. 시험 데이터는 합성이다.

## 변경량 축소 계획

116건 명부·인수 검사 25건·약화 변이 2종으로 동작을 잠근 뒤, 시험 함수·매개변수·단언·검사 명령은 유지한 채 빈 줄·중복 설명, 범위 밖 전역 검사기 변경, 역사적 V1 원문(→ `private-reviews/`)만 뺀다.

**무엇을** — 역사적 V1 원문을 추적 파일에서 빼고 해시만 남긴다. **왜** — P11③ 3,000줄 상한이 절대 금지이고 그 원문은 현재 HEAD의 승인 근거가 아니다. **버린 길** — 시험 docstring·인수 검사 항목을 줄이는 길(필수 시험 약화), 원문을 요약본으로 바꾸는 길(원문 100% 보존 규칙 위반). **대가** — 원문이 저장소 밖에 있어 다른 PC에서는 해시로만 대조한다. **되돌리기** — `git show e25ac5e^:docs/engineering/…verdict-eb0b225…md`로 복원 가능.

## 비범위

HS-03.03 암호화 저장, HS-03.04 readback, HS-03.05 삭제, 실제 포털 후보 읽기, #96 `RunnerBoundary` 연동, Supabase, 운영 배포, merge, push.
