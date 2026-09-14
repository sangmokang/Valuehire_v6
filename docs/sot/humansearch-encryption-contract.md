# HumanSearch 암호화 계약 승인대기초안 (SOT)

최종 갱신: 2026-09-14

## 1층 — 결론

이 문서는 HS-03.03 암호화 구현 전에 검토할 승인대기초안이다. 새 런타임 의존성, 암호화 알고리즘,
키 provider, macOS Keychain 사용 여부를 제안하지만 그 자체로 설치·키 생성·운영 권한을 만들지 않는다.

추천안은 `cryptography>=50.0.1,<51`의 `AESGCM`이다. 키는 32바이트, nonce는 96비트이며 같은 키에서
nonce를 절대 재사용하지 않는다. 암호화는 후보 원문 파일 단독 보호가 아니라 암호화 전 확정한 버전 있는
canonical AAD metadata로 manifest 식별자, candidate HMAC, position ref, key id를 함께 묶어 변조를 탐지해야 한다.

승인 전에는 `humansearch/pyproject.toml`, lockfile, 런타임 코드, 키 저장소, 실제 암호문 파일을 변경하지 않는다.
RPS 프로젝트 생성·필터 업데이트 승인은 이 새 dependency와 키 선택 승인이 아니다.

## 2층 — 판단 근거

현재 `humansearch/pyproject.toml`은 Python `>=3.14`만 요구하고 런타임 crypto 의존성이 없다. Python 3.14 표준
cryptographic services는 `hashlib`, `hmac`, `secrets`를 제공하지만 파일 payload를 기밀성·무결성으로 함께
보호하는 AEAD 저장 API를 제공하지 않는다.

PyCA `cryptography`는 PyPI 기준 `50.0.1`이 최신 안정 릴리스이며 Python 3.14와 macOS ARM64 wheel을 제공한다.
라이선스는 `Apache-2.0 OR BSD-3-Clause`다. PyCA 설치 문서는 `uv add cryptography`를 지원 경로로 제시하고,
AEAD 문서는 `AESGCM`이 128/192/256비트 키를 지원하며 96비트 nonce 권장과 nonce 재사용 금지를 명시한다.
복호화는 key, nonce, AAD, ciphertext가 맞지 않으면 `InvalidTag`로 실패해야 한다.

공식 근거:

- Python 3.14 cryptographic services: https://docs.python.org/3.14/library/crypto.html
- PyPI `cryptography`: https://pypi.org/project/cryptography/
- PyCA installation: https://cryptography.io/en/latest/installation/
- PyCA AEAD/AESGCM: https://cryptography.io/en/latest/hazmat/primitives/aead/
- PyCA security policy: https://cryptography.io/en/latest/security/

## 3층 — 승인 전 경계

이 초안은 아래 권한을 만들지 않는다.

- 새 dependency 설치 또는 lockfile 갱신.
- 실제 HS 키 생성, 조회, 가져오기, 내보내기.
- macOS Keychain item 생성, 권한 프롬프트 허용, iCloud 동기화 설정.
- 후보 원문, manifest, 캡처, LinkedIn/RPS payload 암호화 저장.
- CLI에 원시 key를 넘기는 실행 경로 추가.
- 다른 PC 프로필, 브라우저 프로필, Keychain DB, 쿠키, 토큰 복사.

승인 질문은 dependency 승인과 키 provider 승인으로 분리해야 한다. 기존 RPS 프로젝트 생성 승인, ClickUp 포지션
대상 확정, GitHub 인계 작업 승인은 이 문서의 새 dependency·키 선택을 대신하지 않는다.

## 4층 — 암호화 알고리즘 계약 초안

승인되면 HS-03.03은 아래 계약을 구현해야 한다.

| 항목 | 계약 |
|---|---|
| package | `cryptography>=50.0.1,<51` |
| primitive | `cryptography.hazmat.primitives.ciphers.aead.AESGCM` |
| key length | 32 bytes, AES-256 |
| nonce | 12 bytes, CSPRNG 생성 뒤 persistent atomic `unique(key_id, nonce)` 예약, 같은 key에서 절대 재사용 금지 |
| tag | AES-GCM tag 포함 ciphertext를 저장 |
| AAD | 암호화 전 확정한 버전 있는 canonical metadata bytes. manifest id/version, candidate HMAC, position ref, key id, payload kind, schema version을 결합 |
| decrypt failure | 변조, key 누락, 잘못된 key, nonce/AAD 불일치, ciphertext 손상은 독립 decrypt readback 실패 |

`AESGCM.encrypt()` 호출의 `associated_data`는 `None`이 아니어야 한다. AAD에는 평문 PII를 넣지 않고, 후보자 식별은
이미 승인된 HMAC 또는 비민감 ref만 사용한다. AAD schema가 바뀌면 version을 올리고 이전 version readback을
명시적으로 지원하거나 migration 전까지 읽기 실패로 닫아야 한다.

AAD는 ciphertext, AES-GCM tag, ciphertext hash를 포함하지 않는다. ciphertext와 tag는 AAD 이후에 생기므로
literal AAD 입력이 될 수 없다. 불변 manifest metadata는 같은 canonical AAD bytes를 저장하고, encrypted file hash는
암호화 뒤 별도 필드로 검증한다. plaintext digest는 추측 가능한 PII digest가 비민감하다고 가정하지 않는다.
필요하면 인증 metadata에 포함하거나 보호된 encrypted manifest 안에 넣되, 값의 민감도와 외부 노출 가능성을 따로
판정해야 한다.

nonce는 deterministic candidate key에서 파생하지 않는다. CSPRNG 96비트 nonce 생성만으로 "절대 재사용 금지"를
충족했다고 보지 않는다. 구현은 암호화 전에 SQLite 원본 또는 승인된 nonce 장부에 `unique(key_id, nonce)`를
atomic하게 예약해야 한다. 암호화 실패 뒤 재시도는 이미 저장된 ciphertext를 재사용하거나 새 nonce를 다시
예약해야 하며, 예약했던 nonce로 재암호화하지 않는다. 중복 방지는 SQLite 장부와 candidate HMAC이 담당하고,
nonce 재사용으로 중복 방지를 하지 않는다.

## 5층 — 파일·manifest 계약 초안

암호화 payload 파일과 manifest는 보호 root 안에만 있어야 하며 Git 밖이어야 한다. 경로·권한·symlink·owner
검증은 `docs/sot/humansearch-storage-contract.md`의 보호 저장 위치와 권한 계약을 따른다.

암호문 파일에는 최소한 아래 비밀이 아닌 envelope 정보만 포함할 수 있다.

| 필드 | 계약 |
|---|---|
| `version` | envelope schema version |
| `alg` | `AESGCM-256` |
| `key_id` | key provider가 발급한 비밀이 아닌 식별자 |
| `nonce` | 12-byte nonce의 encoding |
| `aad_schema` | AAD version |
| `ciphertext` | AES-GCM tag 포함 ciphertext |

manifest는 payload 종류, 암호문 ref, encrypted file hash, candidate HMAC, position ref, key id, readback 상태를
연결한다. plaintext digest가 필요하면 비밀 아닌 값이라고 단정하지 말고 인증 metadata 또는 보호된 encrypted
manifest로 취급한다. manifest 자체가 후보 원문, URL token, cookie, session header, 원시 key, 복호화 평문을
포함하면 저장 실패다.

## 6층 — 키 provider 계약 초안

키 provider는 아래 인터페이스 의미만 제공해야 한다. 실제 API 이름은 후속 구현에서 정하되 의미를 바꾸면 안 된다.

| 동작 | 계약 |
|---|---|
| `get(key_id)` | 기존 `key_id`로 32-byte key를 메모리에 반환한다. 없으면 명시 실패한다. |
| `current()` | 현재 쓰기용 `key_id`와 32-byte key를 반환한다. 승인된 provisioning 없이는 암묵 생성하지 않는다. |
| `describe(key_id)` | 로그 가능한 비밀 아닌 provider/type/status만 반환한다. key bytes를 반환하지 않는다. |

키 누락은 새 키 암묵 생성으로 복구하지 않는다. 잘못된 key, provider 접근 거부, 권한 prompt 거부, Keychain lock,
별도 process 접근 실패는 서로 구분한다. key bytes는 stdout, stderr, 일반 로그, argv, PR 본문, Git 파일, SQLite,
manifest, 암호문 envelope에 쓰지 않는다.

macOS Keychain은 권장 승인 초안일 뿐이다. 실제 접근 주체, keychain item class, access control, 등록 절차,
별도 process readback 권한은 아직 검증하지 않았으며 현재 상태는 `NOT_RUN`이다.

## 7층 — CLI와 프로세스 경계

CLI는 `-w`, `--key`, positional argument, 환경 출력 echo처럼 원시 key가 argv나 shell history에 노출되는 경로를
제공하지 않는다. 원시 key를 파일 경로, JSON literal, stdin dump로 받는 임시 디버그 모드도 금지한다.

독립 decrypt readback은 writer의 반환값, writer 메모리 객체, 같은 함수 내부 검증을 성공 증거로 쓰지 않는다.
후속 구현은 별도 process 또는 최소한 별도 DB 연결과 key provider 재조회로 SQLite ref, manifest metadata,
canonical AAD, ciphertext, encrypted file hash, plaintext 검증값의 보호 경계를 다시 검증해야 한다.

## 8층 — 다른 PC 인계 경계

다른 PC에서 이어가기 위한 GitHub handoff는 코드와 문서 이관만 의미한다. HS 암호화 key 자동 이관을 의미하지 않는다.

금지:

- iCloud Keychain이 임의 HS generic password key를 자동 동기화한다고 보장하는 문구.
- Mac/Chrome/Aside/브라우저 profile 복사.
- `~/Library/Keychains` 파일 복사.
- 원시 key를 메일, PR, GitHub issue, Slack, 로그, env dump로 전달.

허용 초안:

- 새 Mac에서 같은 `key_id`를 보호된 절차로 재등록한 뒤 독립 decrypt readback을 실행한다.
- 별도 보호 이관 절차는 사용자 승인 뒤 문서화한다.
- 실제 다른 PC 보호 이관 검증은 아직 `NOT_RUN`이다.
- 과거 key로 다른 PC에서 복호화만 하는 것은 허용될 수 있으나, 안전한 새 writer key provisioning 전에는 같은
  key로 새 암호문을 쓰지 않는다.
- 여러 writer PC가 같은 key를 쓰려면 공유 nonce uniqueness authority가 필요하다. 그 권한이 없으면 PC마다
  distinct writer key를 써야 하며, 이 문서는 cross-PC nonce safety를 주장하지 않는다.

Apple Keychain Access 문서는 일부 keychain item export/import를 설명하지만 password export 제한도 명시한다.
따라서 이 문서는 iCloud 자동 동기화나 일반 Keychain export로 HS 키 이관이 된다고 주장하지 않는다.

공식 근거:

- Keychain Access 개요: https://support.apple.com/guide/keychain-access/what-is-keychain-access-kyca1083/mac
- Keychain item import/export: https://support.apple.com/guide/keychain-access/import-and-export-keychain-items-kyca35961/mac

## 9층 — 오류 계약 초안

아래 오류는 서로 다른 실패로 남겨야 한다.

| 오류 | 처리 |
|---|---|
| key id 없음 | readback 실패, 순회 중단 |
| key provider 접근 거부 | readback 실패, 순회 중단 |
| key bytes 길이 32바이트 아님 | 저장 거부 |
| nonce 예약 실패·재사용 감지 | 저장 거부, 보안 오류 |
| AAD version 불명 | 저장 또는 readback 실패 |
| candidate HMAC/position ref/key id 불일치 | 변조 의심, readback 실패 |
| ciphertext/tag 손상 | `InvalidTag` 계열 실패 |
| plaintext 파일 생성 시도 | 저장 실패 |
| key argv 노출 경로 사용 | 실행 거부 |

오류 메시지는 candidate PII, 원문 URL, key bytes, token, cookie, session header를 포함하지 않는다.

## 10층 — 검증 명령

문서 초안 검증:

```bash
rg -n '승인대기초안|권한을 만들지 않는다|RPS.*승인.*아니다|cryptography>=50\\.0\\.1,<51|AESGCM|32바이트|96비트|unique\\(key_id, nonce\\)|AAD.*ciphertext.*포함하지 않는다|candidate HMAC|position ref|key id' docs/sot/humansearch-encryption-contract.md
rg -n '원시 key|argv|stdout|stderr|로그|Git|SQLite|manifest|암묵 생성하지 않는다|macOS Keychain.*NOT_RUN|iCloud.*보장|profile 복사|보호 이관.*NOT_RUN|distinct writer key|cross-PC nonce safety' docs/sot/humansearch-encryption-contract.md
```

구현 후 필수 검증은 별도 WU에서 추가한다. 이 초안 WU에서는 dependency 설치, runtime test, Keychain 접근,
다른 PC readback이 모두 `NOT_RUN`이다.
