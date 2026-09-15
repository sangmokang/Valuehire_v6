# 착수 프롬프트 v2 — HS-03.03 암호화 저장: 계약 충돌을 먼저 푼다 (2026-09-15 20:05)

## 결론

v1(16:10)은 그대로 실행하면 안 된다. 별도 브랜치 `task/hs-0303a-encryption-contract-20260914`(HEAD 773e795, 베이스는 이 브랜치가 아니라 hs-0401 저장 정책 브랜치)에 **승인대기초안** `docs/sot/humansearch-encryption-contract.md` 가 이미 있고, v1 과 네 군데에서 다르다 — 키 보관 방식, 일회성 값(nonce) 중복 방지, 인증 정보(AAD) 구성, 마이그레이션 범위. 게다가 v1 의 RED 시험 한 줄("암호문 1바이트 변조 → 잘못된 키 오류와 **다른 종류**의 오류")은 AES-GCM 으로는 증명할 수 없다 — 잘못된 키든 손상된 암호문이든 같은 인증 실패(InvalidTag) 하나만 나온다. 그래서 이 문서는 코드 착수 전에 **사장님 결정 4개**를 받고, 오류 계약을 "인증 실패·원인 미확정"으로 고쳐 쓰자고 제안한다. 결정 전에는 암호화 방식·키 보관을 확정하지도, 의존성을 설치하지도 않는다.

## v1 ↔ 승인대기초안 대조 (사실만)

| 항목 | v1 프롬프트(이 브랜치 b8e458a) | 승인대기초안(0303a 브랜치 773e795) | 충돌 여부 |
|---|---|---|---|
| 의존성 | `cryptography` 추가(A안 권고), 버전 미지정 | `cryptography>=50.0.1,<51`, 설치는 승인 뒤 | 같은 방향, 버전 고정만 초안이 더 좁다 |
| 키 보관 | A안 = 키 **파일** 0600, DB 보호 root 밖(HS-03.02 `_load_hmac_key` 규칙 재사용) | 키 provider 인터페이스(`get/current/describe`) + **macOS Keychain 권장**, Keychain 접근·별도 프로세스 readback 은 `NOT_RUN` | **충돌** — 파일 vs Keychain. 결정 필요 |
| 일회성 값(nonce) | 검토 공격 항목에 "nonce 재사용"만 있고 예방 장치 없음 | CSPRNG 96비트 + SQLite 에 `unique(key_id, nonce)` **원자적 예약** 필수, 재시도 시 새 nonce | **충돌** — 초안은 새 표(마이그레이션)를 요구한다 |
| 인증 정보(AAD) | `(position_ref, channel, candidate_key_hmac)` 길이 접두 직렬화 | 버전 있는 canonical bytes = manifest id/version + candidate HMAC + position ref + key id + payload kind + schema version. `associated_data=None` 금지. ciphertext·tag·해시는 AAD 에 넣지 않음 | **충돌** — 필드 집합과 버전 표식이 다르다 |
| 오류 구분 | 6종(키 원본 없음/복호화 권한 없음/키 없음/잘못된 키/손상 암호문/권한 없음), RED 시험이 "잘못된 키 ≠ 손상 암호문"을 요구 | 표 9층: 변조·키 누락·잘못된 key·nonce/AAD 불일치·손상은 모두 "독립 decrypt readback 실패"; ciphertext/tag 손상은 `InvalidTag` 계열 | **충돌** — v1 은 구분을 요구하고 초안은 하나로 접는다. 저장 정본 §4 "키 없음, 잘못된 키, 손상 암호문, 권한 없음의 오류는 서로 구분한다"와도 맞물린다 |
| 마이그레이션 범위 | `storage_schema.py`·마이그레이션 **비범위**, 방식 교체 시 재암호화 1회 | nonce 장부 표 + AAD schema version 승격 시 구버전 readback 명시 지원 또는 닫힌 실패, PC 별 distinct writer key | **충돌** — 초안대로면 HS-03.03 이 마이그레이션을 소유하거나 HS-03.01 에 되돌려 보내야 한다 |
| 다른 PC 인계 | 언급 없음 | 키 자동 이관 금지, 공유 nonce 권위 없으면 PC 마다 다른 writer key | v1 누락 |

→ 저장 정본 `docs/sot/humansearch-storage-contract.md` 는 두 브랜치에서 동일하다(`git diff 00b440e:… 773e795:…` 출력 0줄). 갈리는 것은 정본이 아니라 v1 프롬프트와 초안 사이다.

## 제안 — 오류 계약을 "인증 실패·원인 미확정"으로 (승인 전 초안)

AES-GCM 은 키가 틀려도, 암호문이 한 바이트 변조돼도, AAD 가 달라도 똑같이 태그 검증 실패 하나만 돌려준다. 그 실패 하나로 셋을 가르면 **추측을 사실로 기록**하게 된다. 그래서:

| 상황 | 신뢰 가능한 별도 근거 | 기록할 오류 |
|---|---|---|
| envelope 의 `key_id` 가 provider 의 현재/조회 `key_id` 와 불일치 | 키 식별자 대조(비밀 아님) | `wrong_key_id` — 잘못된 키(식별자 불일치) |
| 키 provider 가 키를 못 돌려줌 / 길이 32바이트 아님 | provider 응답·길이 | `key_missing` / `key_invalid_length` |
| manifest 의 encrypted file hash ≠ 실제 파일 해시 | 암호화 뒤 별도 저장한 파일 지문 | `ciphertext_corrupted` — 손상 암호문(파일 변조 확인) |
| 위 근거가 전부 없고 태그 검증만 실패 | 없음 | **`auth_failed_cause_unknown`** — 인증 실패·원인 미확정. 순회 중단, readback 실패 |
| 키 파일/Keychain 접근 거부 | OS 오류 종류(경로·키 값 없이) | `key_access_denied` |

원칙: 근거 없는 구분은 금지. 저장 정본 §4 의 "잘못된 키·손상 암호문을 구분한다"는 문장은 **"별도 근거가 있을 때만 구분하고, 없으면 원인 미확정으로 남긴다"** 로 개정하는 변경을 같은 PR 에 동봉한다(정본을 조용히 약화시키지 않고 개정 사유를 남긴다). v1 RED 의 "잘못된 키 오류와 다른 종류" 단언은 "파일 해시 불일치가 있을 때만 `ciphertext_corrupted`, 없으면 `auth_failed_cause_unknown`" 두 시험으로 바꾼다.

> **무엇을** — 인증 실패를 원인 미확정 상태로 두고, 키 식별자·파일 지문이라는 별도 근거가 있을 때만 세분한다.
> **왜** — AES-GCM 태그 실패 하나로는 잘못된 키와 손상 암호문을 구분할 수 없다. 억지로 가르면 잘못된 원인이 장부에 남고 복구 판단이 틀어진다.
> **버린 길** — ① 키 지문(KCV)을 envelope 에 넣어 잘못된 키를 판별: 오프라인 키 추측 오라클이 되고 정본 §4 "키 값을 파일에 쓰지 않는다"와 경계가 흐려진다 ② 복호화 두 번 시도(다른 키로)로 추정: 근거 없는 추측이다.
> **대가** — 운영자가 원인 미확정 오류를 보면 사람이 키·파일을 따로 확인해야 한다.
> **되돌리기** — 오류 열거형에 값 하나를 더하는 변경이라, 분류만 바꾸면 되고 저장 데이터는 손대지 않는다.

## 사장님이 결정할 것 (코드 착수 전, 4개)

| # | 결정 | 선택지 | 권고와 이유 |
|---|---|---|---|
| D1 | 의존성 `cryptography>=50.0.1,<51` 추가 승인 | 승인 / 보류 | 승인. 표준 라이브러리에 AEAD 가 없고, 두 문서가 같은 패키지를 가리킨다. 설치는 승인 뒤 단독 커밋 |
| D2 | 키 보관 | 키 파일(0700/0600, DB root 밖) / macOS Keychain / 둘 다(파일 provider 먼저, Keychain provider 는 후속 WU) | **키 파일 먼저**. HS-03.02 가 이미 실측한 경계 규칙을 재사용하고 CI(리눅스)에서 재현된다. Keychain 은 초안 스스로 `NOT_RUN` 이라 별도 WU 로 |
| D3 | nonce 예약 장부 | HS-03.03 이 마이그레이션 1건 소유 / HS-03.01 브랜치에 되돌려 보냄 / 예약 없이 CSPRNG 만(초안 위반) | **HS-03.03 이 마이그레이션 1건 소유**. 초안이 예약을 필수로 못 박았고, 표 하나(`hs_nonces(key_id, nonce) unique`)라 범위가 작다. 단 HS-03.02 goal 의 "새 마이그레이션 없음"은 03.02 에만 적용 |
| D4 | 오류 계약 개정 | 위 제안 채택 / v1 6종 구분 유지 | 채택. 유지하면 증명 불가능한 시험을 쓰게 된다 |

결정 없이는 아래 실행 프롬프트를 시작하지 않는다. D2 가 Keychain 이면 3~5단계를 다시 쓴다.

## 실행 프롬프트 (결정 4개 원문을 맨 위에 붙인 뒤 새 세션에 붙여넣는다)

```text
$strict

역할: HS-03.03 담당. HS-03.02 코드(candidate_identity.py)·HS-03.01 storage_schema.py 기존 마이그레이션은 수정하지 않는다(D3 승인 시 새 마이그레이션 1건 추가만). "통과했다" 대신 명령·종료값·출력 원문. push·PR 은 사장님이 이 세션에서 명시 승인할 때만.

저장소: /Users/kangsangmo/Desktop/Valuehire_v6
작업 위치: 새 워크트리 worktrees/hs-0303-encrypted-storage-<YYYYMMDD>, 브랜치 task/hs-0303-encrypted-storage-<YYYYMMDD>, 스택 베이스 = task/hs-0302-candidate-identity-20260914 최종 HEAD(사장님 승인 뒤 push 된 값, 승인 전이면 로컬 HEAD 를 적고 PR 베이스는 NOT_RUN). 메인 작업트리·다른 워크트리 수정 금지. 파괴적 실증은 mktemp 아래에서만, GIT_* 환경변수 unset. macOS 임시 폴더는 /var→/private/var symlink 라 경로 시험은 resolve(strict=True) 한 실경로에서 한다.

0. 착수 조건: v1 0단계 그대로 + 결정 D1~D4 원문이 이 프롬프트 맨 위에 있는지. 없으면 착수하지 않는다.
1. 회수 커밋: 이 v2 와 0303a 브랜치의 초안 두 파일(docs/sot/humansearch-encryption-contract.md, docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md)을 이 브랜치로 가져온다(cherry-pick 773e795 또는 파일 복사, 출처 SHA 를 커밋 본문에). 초안 머리글의 "승인대기초안" 표기는 D1·D2·D4 결정 원문을 붙이며 "승인됨(날짜·결정 번호)"으로 바꾼다.
2. 계약 문서 docs/engineering/humansearch-hs-0303-encrypted-storage-goal-<날짜>.md: 초안 4~9층을 EARS AC 로 옮기고, 오류 계약은 위 "인증 실패·원인 미확정" 표로. 저장 정본 §4 문장 개정을 같은 커밋에 동봉하고 개정 사유를 goal 에 적는다. AAD = 초안 canonical bytes(버전 필드 포함), 길이 접두 직렬화는 HS-03.02 candidate_key_hmac 과 같은 방식.
3. RED: tests/test_hs_0303_encrypted_storage.py — 정상 왕복(양성 대조군) / 키 식별자 불일치 → wrong_key_id / 파일 해시 불일치 → ciphertext_corrupted / 해시는 맞는데 태그만 실패(다른 키로 복호화) → auth_failed_cause_unknown / AAD 버전 불명 → 닫힌 실패 / nonce 예약 중복 → 저장 거부 / 키 파일 0644·DB root 하위·symlink → 거부 / 암호문을 Git 폴더 아래에 쓰기 → 거부 / 키 바이트·평문이 str(exc) 와 traceback.format_exc() 어디에도 없음. 필수 시험 명부 + acceptance-hs-0303.sh + verify.yml 스텝 + verification-commands.md 표·머리글(27→28) 동반.
4. GREEN: 의존성 단독 커밋 → 구현. 쓰기 직전·쓰기 뒤(확정 전) 경계 재확인은 HS-03.02 _verify_db_boundary 패턴을 따른다. 파일 hard 600줄, 함수 100줄.
5. 검증·독립 검토·장부·(승인 시) push·Draft PR: v1 5단계 그대로. Codex 는 --no-local 클론 + codex exec -s workspace-write --add-dir, 위조 표본 지시 금지·diff 인용 금지.

중단 조건: 결정 미답 / 0단계 불일치 / 다른 세션 변경 / 검사기 FAIL / 변이 생존 / REQUEST_CHANGES / 저장 정본과 초안이 코드와 세 갈래로 갈림.
비범위: HS-03.02 코드, intent/readback(HS-03.04), 삭제(HS-03.05), 키 회전, Keychain provider(별도 WU), Supabase, 실제 후보 읽기, merge.
```

## HS-03.02 에서 새로 넘기는 사실 (2026-09-15 20시, ced77fe)

- 쓰기 직전 검사만으로는 부족했다. INSERT 와 반환 사이에 DB 가 0644 로 완화돼도 `inserted` 를 돌려줬다(19:27:46 격리 재현). ced77fe 가 명시적 트랜잭션 안에서 commit 직전에 `_verify_db_boundary` 를 다시 부르고, 위반이면 close() 자동 롤백으로 행을 남기지 않는다. 명시적 `rollback` 줄은 변이가 생존해 뺐다(동작 동일). HS-03.03 의 암호문 파일 쓰기도 "쓰기 뒤 재확인"을 확정 전에 둔다 — 파일은 트랜잭션이 없으므로 임시 이름에 쓰고 재확인 뒤 rename 하는 식으로.
- 키 파일 소멸 경쟁의 오류 메시지(`str(exc)`)에는 경로가 없지만 `traceback.format_exc()` 의 원인 사슬(`__cause__` = FileNotFoundError)에는 키 파일 절대 경로가 남는다(19:27:46 실측, R5a·R5b·R5c). 저장 정본은 "키 값"을 금지하지 경로는 금지하지 않아 계약 위반은 아니지만, HS-03.03 은 키 파일 경로도 원인 사슬에서 지울지(`from None` + errno 이름만 메시지에) 결정 카드로 다룬다.
- HS-03.01 `test_sqlite_rollback_journal_is_created_with_restricted_mode` 는 5초 마감의 시간 민감 시험이라 부하(load average 700+)에서 `TimeoutError` 로 흔들린다(19:42·19:58 실측, 시험·스키마 파일은 베이스 7473ec8 과 동일). HS-03.03 시험은 벽시계 마감을 두지 않는다.
- 보조 파일(journal/wal/shm) 소유자는 코드가 따로 보지 않는다 — 0700 부모 안에 다른 UID 가 파일을 만들 수 없고, 같은 UID 로는 다른 UID 파일을 만들어 재현할 수도 없다(chown → EPERM). 계약의 "같은 UID 분리는 NOT_RUN" 조항 그대로다.
- "승인된 보호 root" 목록은 코드에 없다. Git 밖·0700·0600·symlink 없음·키 root 와 분리를 만족하면 어느 폴더든 통과한다(19:27:46 R2). 정본 §3 첫 문단이 기본 경로를 "후속 HS-03/04 구현 WU 가 승인한 운영 설정"에 맡겼으므로 HS-03.04 또는 운영 설정 WU 가 소유한다 — HS-03.03 도 같은 전제를 쓴다.
