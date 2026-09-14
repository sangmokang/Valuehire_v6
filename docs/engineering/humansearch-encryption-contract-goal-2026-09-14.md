# HS-03.03a HumanSearch 암호화 계약 승인대기초안 — goal (2026-09-14)

## 1층 — 결론

HS-03.03a는 `docs/sot/humansearch-encryption-contract.md`를 새 승인대기초안으로 추가한다. 이 WU는 새 crypto
dependency와 key boundary를 검토 가능하게 만드는 문서 작업이다. 런타임 의존성 설치, lockfile 변경, 키 생성,
macOS Keychain 조작, 후보 원문 암호화 저장, 다른 PC key 이관은 하지 않는다.

제품 배송 상태: `NOT_APPLICABLE`. 운영 포털 접속, RPS 프로젝트 생성, 후보 저장, 이메일 전송과 무관한 문서 WU다.

## 2층 — 판단 근거

`docs/sot/humansearch-storage-contract.md`는 후보 원문을 Git 밖 보호 저장소에 암호화하고 독립 readback으로
검증해야 한다고 정했지만, crypto algorithm과 key provider 선택은 후속 WU로 남겼다. 현재 HumanSearch
`pyproject.toml`에는 런타임 crypto 의존성이 없고, 기존 사용자 승인 중 RPS 프로젝트 생성·필터 업데이트 승인은
새 dependency나 key 저장 방식 승인이 아니다.

이번 WU는 PyCA `cryptography`의 `AESGCM` 256-bit를 최소 표준 초안으로 제안하고, macOS Keychain을 권장 후보로
기록한다. 다만 일반 Apple Keychain 문서만으로 임의 HumanSearch key의 iCloud 자동 동기화를 보장할 수 없으므로
다른 PC 보호 이관과 재등록 검증은 `NOT_RUN`으로 남긴다. 또한 96-bit CSPRNG nonce만으로 절대 재사용 금지를
증명했다고 보지 않고, 암호화 전 persistent atomic `unique(key_id, nonce)` 예약을 요구한다.

## 현재 상태

| 항목 | 확인 결과 |
|---|---|
| 기준 SHA | `52285558809295b83c21928aa05e629606cbce20` |
| 브랜치 | `task/hs-0303a-encryption-contract-20260914` |
| HumanSearch Python 요구 | `>=3.14` |
| 현재 런타임 crypto dependency | 없음 |
| 새 dependency 승인 | 없음. 이 WU가 권한을 만들지 않음 |
| key 생성/설치/Keychain 접근 | `NOT_RUN` |
| 다른 PC key 이관/readback | `NOT_RUN` |

## 읽은 근거

- `docs/sot/humansearch-storage-contract.md`
- `docs/engineering/humansearch-storage-policy-goal-2026-09-14.md`
- `humansearch/pyproject.toml`
- Python 3.14 cryptographic services: https://docs.python.org/3.14/library/crypto.html
- PyPI `cryptography`: https://pypi.org/project/cryptography/
- PyCA installation: https://cryptography.io/en/latest/installation/
- PyCA AEAD/AESGCM: https://cryptography.io/en/latest/hazmat/primitives/aead/
- PyCA security policy: https://cryptography.io/en/latest/security/
- Apple Keychain Access 개요: https://support.apple.com/guide/keychain-access/what-is-keychain-access-kyca1083/mac
- Apple Keychain item import/export: https://support.apple.com/guide/keychain-access/import-and-export-keychain-items-kyca35961/mac

## 범위

쓰기 범위는 아래 두 파일뿐이다.

- `docs/sot/humansearch-encryption-contract.md`
- `docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md`

비범위:

- `humansearch/pyproject.toml`, `uv.lock`, runtime source 변경.
- 새 dependency 설치.
- Keychain item 생성, 조회, export, import.
- 실제 후보 암호화 파일 생성.
- RPS 내부 조작, ClickUp 변경, 브라우저 자동화.
- 다른 PC에서 key 복호화 검증.

## 인수 기준

### AC-1 승인대기와 권한 경계

When 이 문서가 추가될 때 새 dependency, key provider, macOS Keychain, 다른 PC key 이관은 승인대기초안으로만
기록되어야 하며, 기존 RPS 생성 승인과 혼동하지 않아야 한다.

검증 명령:

```bash
rg -n '승인대기초안|권한을 만들지 않는다|RPS.*승인.*아니다|설치|키 생성|Keychain.*NOT_RUN|다른 PC.*NOT_RUN' docs/sot/humansearch-encryption-contract.md docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md
```

counter-AC: 이 문서를 근거로 `pyproject.toml`을 수정하거나 key를 생성한다.

### AC-2 dependency와 알고리즘 초안

When HS-03.03 구현자가 crypto 선택을 검토할 때 문서는 `cryptography>=50.0.1,<51`, `AESGCM`, 32-byte key,
96-bit nonce, persistent atomic `unique(key_id, nonce)` 예약, nonce 재사용 금지, `InvalidTag` 계열 decrypt
실패를 명시해야 한다.

검증 명령:

```bash
rg -n 'cryptography>=50\\.0\\.1,<51|AESGCM|32바이트|96비트|unique\\(key_id, nonce\\)|nonce.*재사용|InvalidTag|Python 3\\.14|macOS' docs/sot/humansearch-encryption-contract.md docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md
```

counter-AC: 표준 라이브러리만으로 AEAD 파일 암호화를 구현한다고 선언한다.

### AC-3 AAD와 manifest 결합

When payload를 암호화할 때 문서는 버전 있는 canonical AAD metadata가 암호화 전 확정되어야 하며 manifest
id/version, candidate HMAC, position ref, key id를 결합해야 한다고 요구해야 한다. AAD는 ciphertext, tag,
ciphertext hash를 포함하지 않아야 하며, plaintext digest를 비민감하다고 단정하지 않아야 한다.

검증 명령:

```bash
rg -n 'canonical AAD|manifest id/version|candidate HMAC|position ref|key id|ciphertext.*포함하지 않는다|tag|ciphertext hash|plaintext digest|비민감하다고 단정하지' docs/sot/humansearch-encryption-contract.md
```

counter-AC: ciphertext나 ciphertext hash를 literal AAD 입력에 넣는 순환 계약을 만든다.

### AC-4 key provider와 노출 금지

When key provider가 정의될 때 문서는 32-byte key를 메모리에 반환하는 명시 get-by-keyid 동작, 누락 시 암묵 생성
금지, 원시 key의 argv/stdout/stderr/log/Git/SQLite/manifest 저장 금지를 요구해야 한다.

검증 명령:

```bash
rg -n 'get\\(key_id\\)|32-byte key|암묵 생성하지 않는다|원시 key|argv|stdout|stderr|로그|Git|SQLite|manifest' docs/sot/humansearch-encryption-contract.md
```

counter-AC: `-w raw-key` 같은 CLI 옵션을 허용한다.

### AC-5 다른 PC 이관 과장 금지

When 다른 PC handoff를 설명할 때 문서는 GitHub handoff가 key 자동 이관이 아니며 iCloud 자동 동기화, profile 복사,
Keychain DB 복사를 금지하고 보호 이관·재등록 검증을 `NOT_RUN`으로 남겨야 한다. 과거 key로 복호화만 하는 것과
새 writer key provisioning을 구분하고, 여러 PC가 같은 key로 새 암호문을 쓰려면 공유 nonce uniqueness authority가
필요하거나 PC마다 distinct writer key가 필요하다고 명시해야 한다.

검증 명령:

```bash
rg -n '자동 이관|iCloud.*보장|profile 복사|Keychain DB|재등록|보호 이관|NOT_RUN|원시 key를 메일|GitHub handoff|distinct writer key|nonce uniqueness authority|cross-PC nonce safety' docs/sot/humansearch-encryption-contract.md docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md
```

counter-AC: iCloud Keychain이 HS key를 자동 동기화한다고 사용자에게 안내한다.

## 검증 계획

```bash
bash scripts/acceptance-principles-check.sh
rg -n '승인대기초안|권한을 만들지 않는다|RPS.*승인.*아니다|설치|키 생성|Keychain.*NOT_RUN|다른 PC.*NOT_RUN' docs/sot/humansearch-encryption-contract.md docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md
rg -n 'cryptography>=50\\.0\\.1,<51|AESGCM|32바이트|96비트|unique\\(key_id, nonce\\)|nonce.*재사용|InvalidTag|Python 3\\.14|macOS' docs/sot/humansearch-encryption-contract.md docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md
rg -n 'canonical AAD|manifest id/version|candidate HMAC|position ref|key id|ciphertext.*포함하지 않는다|tag|ciphertext hash|plaintext digest|비민감하다고 단정하지' docs/sot/humansearch-encryption-contract.md
rg -n 'get\\(key_id\\)|32-byte key|암묵 생성하지 않는다|원시 key|argv|stdout|stderr|로그|Git|SQLite|manifest' docs/sot/humansearch-encryption-contract.md
rg -n '자동 이관|iCloud.*보장|profile 복사|Keychain DB|재등록|보호 이관|NOT_RUN|원시 key를 메일|GitHub handoff|distinct writer key|nonce uniqueness authority|cross-PC nonce safety' docs/sot/humansearch-encryption-contract.md docs/engineering/humansearch-encryption-contract-goal-2026-09-14.md
git diff --check
```

## 승인 질문 초안

```text
HS-03.03에서 새 런타임 의존성 `cryptography>=50.0.1,<51`을 추가하고, 후보 증거 파일 암호화 알고리즘을
`AESGCM` 256-bit로 고정해도 될까요?

키 provider는 32-byte key를 `key_id`로 명시 조회하고 누락 시 암묵 생성하지 않는 계약으로 구현하겠습니다.
초기 권장안은 macOS Keychain이지만, 실제 접근 주체·권한·별도 process readback·다른 PC 보호 이관은 구현 전
별도 검증 대상으로 남기겠습니다. iCloud 자동 동기화나 PC 프로필 복사는 사용하지 않겠습니다. 여러 PC에서
같은 key로 새 암호문을 쓰는 것은 공유 nonce uniqueness authority가 없으면 금지하고, 필요하면 PC별 distinct
writer key로 분리하겠습니다.
```

## 현재 검증 제한

이 WU는 문서 초안과 로컬 grep/diff 검증만 목표로 한다. dependency 설치, Python import test, runtime encrypt/decrypt,
Keychain 접근, 별도 process readback, 다른 PC readback, 외부 V1, push, PR, CI는 후속 지시 전까지 `NOT_RUN`이다.
