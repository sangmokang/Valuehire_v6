# HS-03.02 후보 식별키 중복 없는 기록 — goal (2026-09-15)

위험등급 L3(저장 계층·개인정보 파생값·동시성). 착수 프롬프트 v8(`docs/engineering/goal-prompts/humansearch-next-prompt-v8-2026-09-15.md`, 브랜치 `task/hs-prompts-20260915`) §4-4 의 AC 를 그대로 옮긴 것이다.

## 1층 — 결론

PR #97 이 만든 SQLite 표 `hs_candidates` 에 후보 행을 넣는 함수는 아직 없다. 이 WU 는 그 함수 하나를 만들되, 같은 후보를 두 번 넣어도 행이 하나만 남고, 두 연결이 동시에 넣어도 하나만 남으며, 빈 값이나 허용 밖 채널은 행을 만들지 않게 한다. 새 표·새 마이그레이션은 만들지 않는다. 실제 포털 접속·후보 원문 저장·암호화는 하지 않는다.

제품 배송 상태 목표: `LOCAL_ONLY`. 운영 배포·운영 쓰기가 없고 합성 시험 데이터만 쓴다.

## 2층 — 판단 근거

WU 장부 168행(`worktrees/hs-0004-recovery-20260910/docs/engineering/humansearch-next-issues-wu-2026-09-10.md`)은 "같은 `(position,candidate,channel)` 2회→1행; 포지션·채널 다름 구분; 2연결 경쟁도 unique 제약 보장"을 요구한다. #97 스키마의 기본키는 `candidate_key_hmac` 하나이므로, 그 값을 세 입력의 HMAC 으로 정의하면 마이그레이션 없이 데이터베이스 자체의 기본키 제약이 경쟁을 막는다. 응용 코드에서 먼저 조회하고 넣는 방식은 두 연결이 동시에 조회하면 둘 다 "없음"을 보고 둘 다 넣으므로 기각한다.

틀리면 깨지는 것: HMAC 입력에서 `position_ref` 나 `channel` 이 빠지면 다른 포지션·다른 채널의 같은 후보가 한 행으로 합쳐진다(AC-2 위반). 기본키 충돌 예외를 삼키면 다른 무결성 오류까지 "중복"으로 둔갑한다(AC-3 위반).

## 현재 상태 (직접 확인, 기준 SHA 7473ec8 = PR #97 HEAD)

| 항목 | 확인 결과 |
|---|---|
| `humansearch/src/humansearch/storage_schema.py:52-62` | `hs_candidates` 표. 기본키 `candidate_key_hmac`(64자 hex 검사), 일반 열 `position_ref`·`channel`·`candidate_ref_state`·`candidate_ref_hash`·`storage_status`·`created_at`. `observed_at` 열 없음 |
| `storage_schema.py:55` | `channel` 허용값 `'saramin','jobkorea','linkedin_rps'` — `linkedin` 아님 |
| `storage_schema.py:59` | `storage_status` 기본값 `schema_only` |
| `storage_schema.py:192-213` | `_current_version` — 모르는 버전이면 `unsupported schema version` 으로 거부 |
| `grep -rn 'insert into hs_candidates' humansearch/src` | 0건. 행을 넣는 제품 코드가 없다 |
| `humansearch/tests/test_hs_0301.py:47-56` | 시험 보조 `_insert_valid_candidate` 만 직접 SQL 로 넣는다(제품 경로 아님) |
| `docs/sot/humansearch-storage-contract.md:127` | `candidate_key` = `(position_ref, channel, source_url_hash 또는 안정 후보 ref)` 에서 계산한 중복 방지 키 |
| `docs/sot/humansearch-storage-contract.md:109-110` | 키 원본은 데이터와 같은 디렉터리에 두지 않는다. 키 값을 로그·PR·Git 에 쓰지 않는다 |
| `docs/sot/humansearch-encryption-contract.md`(0303a, 773e795) | 키 누락은 암묵 생성으로 복구하지 않는다 |
| Python 3.14.1 · SQLite 3.51.1 | `uv run python -c` 실측 |
| 기준 시험 | `uv run pytest -q` → 241 passed (v8 §4-4 09:23 실측값) |

## 근본 원인

#97 은 "표를 만드는" WU 였고 "행을 넣는" WU 가 아니다. 그래서 중복 식별 규칙(HMAC 입력 정의)도 코드에 없다. RED 는 "기록 함수 부재"에서 시작한다.

## 인수 기준 (EARS) — v8 §4-4 원문

- AC-1: When 같은 `(position_ref, channel, candidate_ref)` 로 2회 기록하면 시스템은 `hs_candidates` 행 1개만 남겨야 한다. `candidate_key_hmac` 은 이 세 값의 HMAC 이어야 하며 HMAC 키는 러너 보호 디렉터리(#96)에서 읽는다.
- AC-2: When `position_ref` 또는 `channel` 이 다르면 시스템은 별도 행을 만들어야 한다. 이름·이메일이 같아도 합치지 않는다(HMAC 입력에 세 값이 모두 들어가야 성립).
- AC-3: While SQLite 연결 2개가 같은 키를 동시에 넣으면 시스템은 기본키 제약으로 1행을 보장하고, 진 쪽은 명시적 `duplicate` 결과를 돌려줘야 한다(`sqlite3.IntegrityError` 삼킴 금지, 다른 오류는 그대로 올림).
- AC-4: If 세 값 중 하나라도 비거나 `channel` 이 허용값 밖이면 시스템은 기록을 거부하고 DB 에 행을 만들지 않아야 한다.

counter-AC(2차 V1 로 4건 더 추가): DB 파일 마지막 구성요소를 symlink 로 만들어 경계 비교를 우회하는 것. 같은 글자의 다른 코드열(결합형/분해형)을 다른 후보로 두는 것. 반대로 NFKC 까지 적용해 호환문자가 다른 포털 ID 를 합치게 두는 것. 새 인수 스크립트를 CI 고정 목록·정본 명부에 넣지 않아 로컬에서만 돌게 두는 것. 인수 실행이 필수 시험을 `-k` 로 빼거나 통과 수를 하한으로만 보는 것. — 그리고 1차 목록: 필드 안에 구분자를 넣어 서로 다른 세 값이 같은 키가 되게 두는 것. 키를 DB 보호 루트의 **하위** 디렉터리에 두도록 허용하는 것. RFC3339 를 자리수만 세어 통과시키는 것. 인수 스크립트가 필수 비교·스캔을 못 한 채 건너뛰고 종료값 0 을 내는 것. — 그리고 원래 목록: 응용 코드에서 `SELECT` 뒤 `INSERT` 로만 막는 것(AC-3 경쟁 시험에서 2행 생김). HMAC 입력에서 `position_ref` 나 `channel` 을 빼는 것(AC-2 위반). HMAC 키를 코드 상수로 두는 것. 스키마 표를 새로 하나 더 만들어 기존 `hs_candidates` 를 우회하는 것. 기본키 예외뿐 아니라 모든 `IntegrityError` 를 `duplicate` 로 접는 것.

## 입출력·오류·경계 계약

- 입력: `CandidateIdentityInput(position_ref: str, channel: Literal["saramin","jobkorea","linkedin_rps"], candidate_ref: str, observed_at: str  # RFC3339)`. 네 문자열 모두 **strip 하기 전에** 제어문자(C0 `0x00-0x1F`·DEL `0x7F`·C1 `0x80-0x9F`)가 있으면 거부한다 — Python 의 `str.strip()` 은 `\x1c-\x1f` 와 `\x85` 를 공백으로 보고 조용히 잘라내며(실측), 잘라내면 키가 소리 없이 바뀐다. 그 다음 strip 하고 **NFC 정규화**한 뒤 비어 있으면 거부. NFC 는 제어문자를 만들지 않는다(실측).
- 출력: `Literal["inserted", "duplicate"]`.
- 오류: `CandidateIdentityError(StorageSchemaError)`. 메시지에 `candidate_ref`·`position_ref`·키 값을 넣지 않는다.
- HMAC(**v2, 2026-09-15 개정**): `hmac.new(key, msg, "sha256")`, `msg = b"hs-candidate-key-v2"` 뒤에 세 필드를 **길이 접두 정규 직렬화**로 이어 붙인다 — 필드마다 `len(utf8 bytes).to_bytes(4, "big") + utf8 bytes`. 키는 32바이트 이상 raw bytes.
  - 왜 바꿨나: 구분자 결합(v1)은 그 구분자가 필드 **안에** 들어오면 경계가 무너진다. Codex V1 이 `("a","saramin","x\x1fjobkorea\x1fy")` 와 `("a\x1fsaramin\x1fx","jobkorea","y")` 가 같은 바이트열이 되는 것을 실측했다(AC-2 위반). 길이는 내용에 섞일 수 없어 이 계열 주입이 원천 차단된다.
  - 도메인 태그를 v1→v2 로 올린다. 같은 세 값이라도 v1 이 만든 키 값과 다르다. 이 WU 는 운영 데이터가 없어(`LOCAL_ONLY`) 재계산 대상이 없다.
  - 제어문자 거부와 길이 접두는 **둘 다** 둔다. 하나가 뚫려도 다른 하나가 막는다.
- 키 파일: `hmac_key_path` 인자로 받는다. 파일은 소유자 = 현재 uid, 모드 0600, 부모 디렉터리 모드 0700. 검사는 `storage_schema._verify_path` 재사용. 없으면 `CandidateIdentityError("hmac key is missing")` — 암묵 생성 금지.
  - symlink: 키 파일과 부모뿐 아니라 **상위 사슬 전체**에 symlink 가 없어야 한다. `stat(follow_symlinks=False)` 는 마지막 구성요소만 따라가지 않으므로 조부모 symlink 를 못 본다(Codex V1). 사슬을 직접 걸어 확인한다.
  - 보호 루트 분리(정본 109행): 해석된 키 디렉터리가 DB 보호 루트와 같거나 **그 하위**여도 거부하고, 반대로 DB 루트가 키 디렉터리의 하위여도 거부한다(`Path.is_relative_to` 양방향). 동일 경로만 막으면 `dbroot/keys/k` 가 통과해, DB 루트를 한 번 복사·유출하면 키까지 함께 나간다.
- DB 경로(**2026-09-15 2차 개정**): 키를 읽기 전에 `_verify_db_location(db_path)` 가 `db_path` 의 **모든 구성요소(마지막 파일 포함)** 에 symlink 가 없음을 확인하고 `db_path.resolve(strict=True).parent` 를 돌려준다. 그 값을 키 루트와 양방향 비교한다.
  - 왜: `db_path.parent.resolve()` 만 보면 마지막 구성요소가 symlink 일 때 검사한 경로와 실제로 여는 파일이 갈라진다. Codex V1 2차가 `alias/humansearch.sqlite3 → 키 디렉터리 안 실제 DB` 를 지목했고, 실측에서 그 구성으로 행이 키 루트 안 DB 에 쓰였다. `sqlite3.connect` 는 마지막 링크를 따라간다.
  - 대가: 링크된 DB 를 쓰던 호출은 거부된다. 되돌리려면 이 보조 함수 하나만 바꾸면 된다.
- 저장 열 매핑: `candidate_ref_state='observed'`, `candidate_ref_hash = HMAC(key, b"hs-candidate-ref-v1\x1f"+candidate_ref)`(평문 sha256 은 추측 가능한 개인정보 지문이라 쓰지 않는다), `storage_status='pending'`(행은 있으나 증거 readback 전), `created_at` 은 DB 기본값.
- `observed_at` 검증은 두 겹이다. ① 정규식이 달력·시각·오프셋 **범위**까지 좁힌다(월 01-12, 일 01-31, 시 00-23, 분·초 00-59, 오프셋 ±00:00-23:59 또는 `Z`). ② `datetime.fromisoformat` 으로 실재를 확인하고 `tzinfo is None` 이면 거부한다. 한 겹으로는 부족하다 — 정규식만으로는 `2026-02-29`(윤년 아님)를, `fromisoformat` 만으로는 `24:00:00` 을 못 막는다(둘 다 실측).
- `observed_at` 은 검증만 하고 `hs_candidates` 에는 저장하지 않는다(열이 없고 버전 2 마이그레이션을 피한다). 증거 시각은 HS-03.04 가 `hs_evidence_manifests.observed_at` 에 기록한다.
- 동시성: `INSERT` 한 번. `sqlite3.IntegrityError` 중 `sqlite_errorname == "SQLITE_CONSTRAINT_PRIMARYKEY"` 만 `duplicate` 로 번역하고 나머지는 그대로 올린다. 연결마다 `pragma foreign_keys=on`, `busy_timeout` 은 기본값(5초) 유지.
- 기존 마이그레이션 1 은 수정하지 않는다. 열 추가가 필요하면 `_MIGRATIONS` 에 버전 2 로 추가하고 `_expected_schema_signature` 가 바뀐 표를 포함해야 한다 — 이 WU 는 열을 추가하지 않는다.

## 계약 충돌 기록 (2026-09-15)

V1 후속 지시는 Codex 충돌 쌍을 "둘 다 `inserted`, 행 2개"로 기록하라고 요구하면서, 같은 지시로 그 쌍이 담고 있는 U+001F 를 거부하라고 요구했다. **두 요구는 동시에 성립하지 않는다.** 제어문자를 거부하면 그 쌍은 애초에 기록되지 않는다. 또 허용 채널이 고정 집합이고 제어문자가 막히면, 구분자 결합에서 충돌하는 **합법** 입력쌍 자체가 존재하지 않는다 — 따라서 "둘 다 inserted" 는 거부를 포기해야만 도달한다.

더 보수적인 쪽(거부)을 택했다. DB 경로 시험은 "둘 다 거부·행 0"으로 두고, 직렬화가 실제로 충돌을 없앴는지는 순수 함수 시험이 따로 본다. 이어 붙이면 같아지는 **합법** 쌍(`("ab","saramin","c")` vs `("a","saramin","bc")`)이 별도 행으로 남는지 보는 DB 회귀 시험을 하나 더 뒀다 — 전부 거부하는 구현을 막는 양성 대조군이다.

## 결정 카드

> **무엇을** — HS-03.02 를 #97 SQLite 스키마 위 스택으로 두고, 기존 `hs_candidates` 기본키(`candidate_key_hmac`)를 세 값 HMAC 으로 정의해 중복을 막는다. 새 모듈 `humansearch/src/humansearch/candidate_identity.py` 에 둔다.
> **왜** — 장부 168행이 "2연결 경쟁도 unique 제약 보장"을 요구하고, 응용 코드 검사로는 경쟁 시험을 못 넘긴다. 표를 새로 만들면 #93·#94 증거 표가 참조하는 외래키가 갈라진다. `storage_schema.py`(294줄)에 넣지 않는 이유는 책임 분리(스키마 설치 vs 행 기록).
> **버린 길** — main 기준 새 브랜치: #97 마이그레이션 없이는 표가 없어 기각. 이름 기반 병합: 장부 AC-2 위반이라 기각. `unique(position_ref, candidate_key_hmac, channel)` 복합 제약 추가: 기본키가 이미 단독이라 HMAC 입력 정의로 같은 효과를 내는 쪽이 마이그레이션 0개라 채택.
> **대가** — #97 이 병합되기 전까지 이 PR 도 Draft 로 남고, #97 이 바뀌면 rebase 가 필요하다.
> **되돌리기** — 코드는 PR 을 닫으면 회수된다. 열을 추가하지 않으므로 버전 2 가 없고, 로컬 DB 재초기화가 필요 없다(적용된 마이그레이션이 1 그대로). 만약 후속에서 버전 2 를 넣으면 `storage_schema.py:192-213` 이 모르는 버전을 거부하므로 DB 파일을 지우고 재초기화해야 한다(Codex F-V8-02).

> **무엇을** — HMAC 키는 `hmac_key_path` 로 받은 별도 보호 디렉터리의 0600 파일에서 읽는다. 검사 규칙은 #96 러너 경계와 같다(소유자·모드·symlink 금지).
> **왜** — v8 AC-1 은 "러너 보호 디렉터리(#96)" 를 지목하지만 #96 은 이 스택(#89→#97)에 없다. #96 의 `RunnerBoundary` 를 import 하면 스택 베이스가 둘이 된다. 정본 109행은 키와 데이터의 디렉터리 분리를 요구한다.
> **버린 길** — #96 브랜치를 스택에 합치기: v8 §4-4 가 베이스를 #97 하나로 고정. 키를 DB 와 같은 루트에 두기: 정본 109행 위반. 키를 환경변수로 받기: 프로세스 목록·env dump 노출(0303a 7층). 키 없으면 생성: 0303a 6층 "암묵 생성 금지".
> **대가** — 호출자가 키 파일을 미리 만들어 둬야 한다. #96 병합 뒤 로더를 `RunnerBoundary` 로 위임하는 후속 WU 가 필요하다.
> **되돌리기** — `hmac_key_path` 인자와 검사 함수만 바꾸면 된다. 저장된 `candidate_key_hmac` 값은 키가 같으면 그대로 유효하다.

> **무엇을** — 후보 식별 세 필드를 **의미 문자열**로 취급하고, strip 뒤 **NFC** 로 정규화해 대표형을 정한다. NFKC 는 쓰지 않는다. 도메인 태그는 v2 를 유지한다.
> **왜** — 중복 제거는 "같은 후보면 항상 같은 바이트열" 이라는 전제 위에 선다. 유니코드는 같은 글자를 여러 코드열로 쓸 수 있어 전제가 저절로 성립하지 않는다 — `café`(결합형)와 `café`(분해형)가 다른 키가 되어 같은 후보가 두 행이 된다(실측). NFC 는 그 둘을 합치면서 글자 정체성은 바꾸지 않는다.
> **버린 길** — NFKC: 호환문자까지 합쳐 `①` 과 `1`, 전각 `Ａ` 와 `A` 를 같게 만든다. 포털 후보 ID 에 그런 문자가 들어오면 **서로 다른 후보가 한 행으로 합쳐진다**(오병합). 중복보다 오병합이 더 위험하다 — 중복은 두 번 접촉하는 것이고 오병합은 한 사람을 잃는 것이다. 비-NFC 입력을 아예 거부하는 길도 버렸다: 포털이 어떤 형태로 주는지 우리가 정하지 못한다.
> **대가** — v1 이 만든 키와 값이 다르다. 이 WU 는 `LOCAL_ONLY` 라 재계산 대상 데이터가 0 이다. 운영 데이터가 생긴 뒤 정규화를 또 바꾸면 도메인 태그를 올리고 전환 규칙을 따로 둬야 한다.
> **되돌리기** — `_NORMALIZATION_FORM` 상수 하나다. 다만 되돌리면 그 시점 이후의 키가 달라진다.

> **무엇을** — 새 인수 스크립트를 `verify.yml` 전용 스텝과 `docs/sot/verification-commands.md` 명부 27행에 **같은 커밋**으로 넣는다.
> **왜** — CI 는 고정 목록이고 로컬 `pre-push` 는 글로브다(정본 53행). 등록하지 않으면 로컬에서만 도는 검사가 되고 P15③ 은 그것을 없는 것으로 친다. 이 스크립트가 판정하는 것(HMAC 의미·스키마 무변경·우회 표·자기 fail-closed)이 전부 CI 밖에 있었다.
> **버린 길** — `pre-push` 글로브에 맡기기: 로컬 훅은 우회 가능하고 판정 권한은 CI 에 있다.
> **대가** — CI 실행 시간이 인수 검사 하나만큼 늘어난다.
> **되돌리기** — 두 파일에서 각각 한 줄·한 행을 지우면 된다. 지우면 `test_acceptance_script_runs_as_its_own_ci_step` 이 막는다.

## RED 시험 (`humansearch/tests/test_hs_0302_candidate_identity.py`, 현재 HEAD 에서 전부 실패해야 한다)

1. AC-1 같은 세 값 2회 → 결과 `inserted`, `duplicate`, 행 1개, `candidate_key_hmac` 이 시험이 독립 계산한 HMAC 과 일치.
2. AC-2 `position_ref` 만 다름 → 행 2개. `channel` 만 다름 → 행 2개(`saramin` vs `jobkorea`, `candidate_ref` 동일).
3. AC-3 ThreadPoolExecutor 2 워커, 각자 새 `sqlite3` 연결, 같은 키 동시 삽입 ≥20회 반복 → 매회 결과 집합 = {`inserted`,`duplicate`}, 행 1개, 예외 0.
4. AC-4 빈 `candidate_ref`·빈 `position_ref`·`channel="linkedin"` 각각 → `CandidateIdentityError`, 행 0.
5. 키 파일 없음 → `CandidateIdentityError`, 행 0. 키 파일이 DB 루트 안 → 거부.
6. `IntegrityError` 삼킴 금지: 기본키 충돌이 아닌 무결성 오류(예: monkeypatch 로 CHECK 위반 유도)는 `duplicate` 가 아니라 예외.

## 검증 명령 (v8 §4-4)

```
cd worktrees/hs-0302-candidate-identity-20260914/humansearch
uv run pytest tests/test_hs_0302*.py -q      # 기대: ≥5 passed (중복1·포지션다름1·채널다름1·2연결경쟁1·빈키거부1), RED 커밋에서는 전부 실패
uv run pytest -q                              # 기대: 241 + 새 시험 전부 passed
uv run ruff check src tests && uv run mypy src tests
cd .. && bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh   # 기대: PASS 줄 ≥1, CHECKED: ≥5
```

변이(각 GREEN 뒤 실제 실행, 생존 0): (1) 기본키 제약 줄(`storage_schema.py:53` 의 `primary key`)을 지운 사본에서 AC-3 시험 실패. (2) HMAC 입력에서 `channel` 을 뺀 사본에서 AC-2 채널 시험 실패. (3) `IntegrityError` 를 통째로 `duplicate` 로 접은 사본에서 6번 시험 실패. (4) 키 검사를 지운 사본에서 5번 시험 실패.

## Harness 게이트 계획

0 실측(v8 §0) → 1 이 문서 커밋 → 2 RED 커밋(시험만) → 3 GREEN 커밋(모듈 + 인수 스크립트) → 4 위 검증 명령 전부 → 5 push·Draft PR(base `task/hs-0301-sqlite-schema-20260914`) → V1 Codex 적대검증 → 6 병합은 사장님.

## 적대검증 정조준

HMAC 입력 누락, 예외 삼킴 범위, 키 파일 검사 우회(symlink·모드), 경쟁 시험이 실제로 두 연결을 쓰는지(같은 연결 재사용이면 무효), 오류 메시지의 개인정보 유출, 검사 대상 0개 인수 스크립트.

## 롤백·영향 반경·데이터 안전

- 롤백: PR 닫기. 마이그레이션 변경 0 이므로 DB 재초기화 불필요.
- 영향 반경: 새 모듈 1개 + 시험 1개 + 인수 스크립트 1개. `storage_schema.py` 는 수정하지 않는다(재사용만).
- 데이터 안전: 저장되는 값은 HMAC 두 개와 포지션·채널 식별자뿐. 후보 원문·이름·URL 은 입력에도 없다. 시험 데이터는 합성.

## 읽은 SOT

`docs/sot/coding-principles.md`(P11 파일 hard 600·함수 hard 100), `docs/sot/principles.yaml`, `docs/sot/humansearch-storage-contract.md` §4·127행, 0303a `docs/sot/humansearch-encryption-contract.md` 6·7층, WU 장부 168행, v8 §4-4.

## 비범위

증거 파일 암호화(HS-03.03), intent→readback(HS-03.04), 삭제(HS-03.05), 실제 포털 후보 읽기, #96 `RunnerBoundary` 연동, Supabase.

## 검증 장부

기준 커밋 7473ec8(#97 HEAD). 아래 명령은 워크트리
`worktrees/hs-0302-candidate-identity-20260914` 에서 2026-09-15 에 실제로 실행한 것이다.

| 단계 | 상태 | 증거 |
|---|---|---|
| strict 0.1 원칙 로드 | PASS | `bash scripts/acceptance-principles-check.sh` @6f8b98b 10:29:08 → `VERDICT: PASS`, `MECHANISMS: PASS 34/34`, `WIRING: PASS pre-push=1 ci=1`, `CHECKED: 34`, rc=0 |
| 기준선 재측정 | PASS(불일치 기록) | `uv run pytest -q` @23a4890 10:36:55 → `229 passed in 12.25s`, `229 tests collected`. 이 문서 "현재 상태" 표의 241 은 이 워크트리에서 재현되지 않는다 — 기준선은 **229** 다 |
| RED 커밋 | PASS | `838577b` (시험 파일 1개, 434줄). 직전 `uv run pytest tests/test_hs_0302_candidate_identity.py -q` 10:41:54 → `28 failed in 0.56s`, 실패 사유 28건 전부 `Failed: record function missing: humansearch.candidate_identity` — import/문법 오류가 아니라 빠진 동작이다 |
| GREEN 커밋 | PASS | `4f51ca6` (`humansearch/src/humansearch/candidate_identity.py` 178줄 + `scripts/acceptance-hs-0302.sh` 215줄). `storage_schema.py` 수정 0줄, 마이그레이션 추가 0개 |
| 검증 — 새 시험 | PASS | `uv run pytest tests/test_hs_0302*.py -q` 10:48:00 → `28 passed in 0.99s` |
| 검증 — 전체 시험 | PASS | `uv run pytest -q` 10:48 → `257 passed in 14.32s` (229 기준선 + 28 신규, 기존 시험 약화·삭제·skip 0) |
| 검증 — ruff·mypy | PASS | `uv run ruff check src tests` → `All checks passed!`; `uv run mypy src tests` → `Success: no issues found in 45 source files`, rc=0 |
| 검증 — 인수 스크립트 | PASS | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh` 10:48:27 → `PASS` 11줄, `CHECKED: 11`, `OK(run-acceptance): ... 판정 11건, CHECKED 11`, rc=0 |
| 변이 (1) 기본키 제약 제거 | 생존 0 | `storage_schema.py:53` 에서 `primary key` 삭제 10:46:14 → `test_ac1_same_triplet_twice_leaves_one_row`, `test_ac3_two_connections_racing_the_same_key_keep_one_row` 2건 실패. `AssertionError: round 0: ['inserted', 'inserted']`. `git checkout --` 로 복구, `git status --short` 0줄 |
| 변이 (2) HMAC 입력에서 channel 제거 | 생존 0 | `channel.encode("utf-8"),` 삭제 10:46:21 → `test_ac2_position_or_channel_difference_creates_separate_rows`, `test_ac1_key_hmac_separator_distinguishes_field_boundaries` 2건 실패. `assert 'duplicate' == 'inserted'` (채널만 다른 후보가 한 행으로 합쳐졌다). 복구 후 0줄 |
| 변이 (3) IntegrityError 통째로 duplicate | 생존 0 | 가드 삭제 10:46:32 → `test_non_primary_key_integrity_error_is_not_folded_into_duplicate` 실패 (`DID NOT RAISE IntegrityError`). 인수 스크립트도 같은 변이에서 `FAIL` 3줄 + rc=1. 복구 후 0줄 |
| 변이 (4) 키 검사 제거 | 생존 0 | `_load_hmac_key` 를 `read_bytes()` 한 줄로 치환 10:46:57 → 키 시험 6건 실패 (부재·DB 루트 내부·모드 0644·부모 0755·symlink·32바이트 미만). 복구 후 0줄 |
| counter-AC 검출 (변이와 별건) | PASS | 응용 코드 `SELECT`-then-`INSERT` + 기본키 제약 없음 사본 10:47:25 → `test_ac3...` 실패, `round 1: ['inserted', 'inserted']` (2행 생성). 복구 후 `git status --short` 0줄, `git diff 7473ec8 -- storage_schema.py` 0줄 |
| AC-3 독립 연결 실측 | PASS | 계측 스크립트 10:47:52 → `connect calls (worker)=2`, `distinct worker threads=2`, `distinct connection ids=2`, `same connection shared=False`, `rows in hs_candidates=1`. 같은 연결 공유가 아니다 |
| `sqlite_errorname` 실측 | PASS | Python 3.14.1 / SQLite 3.51.1 → 클래스 `hasattr(sqlite3.IntegrityError, "sqlite_errorname")` = `False`, 인스턴스는 기본키 충돌 `SQLITE_CONSTRAINT_PRIMARYKEY`, CHECK 위반 `SQLITE_CONSTRAINT_CHECK`, NOT NULL 위반 `SQLITE_CONSTRAINT_NOTNULL` |
| P11 코드 예산 | PASS | `candidate_identity.py` 178줄 / 최장 함수 `_insert_once` 29줄. 시험 파일 434줄 / 최장 함수 51줄. 인수 스크립트 215줄. hard 600·100 이내 |
| V1 (1차) | **FAIL** | Codex 독립 검증 @9ac10f9 11:01:55 → `VERDICT: FAIL`, 결함 4건(high 2·medium 2). AC-2 REPRODUCED, 나머지 3건 REPRODUCED. 판정 원문 `scratchpad/codex-v1-0302.log` |
| V1 결함 재현 | PASS | `v2_0302_codex.py` @9ac10f9 11:06:01 → `(1) separator collision: True`, `(1) db outcome: inserted duplicate | rows: 1`, `(2) key under db root: ACCEPTED inserted`, `(3) 2026-99-99T99:99:99: ACCEPTED inserted` — 3건 모두 내 손으로 재현 |
| 2차 RED | PASS | `efaefab`(새 파일 + 1차 독립 HMAC 을 계약 v2 로 재작성) → 새 파일 28 failed/9 passed, 1차 파일 4 failed/24 passed. 계약 충돌 정정 `6395056` 후에도 대상 시험은 여전히 RED |
| 2차 GREEN | PASS | `1396faf`(모듈 + 인수 스크립트) · `f03cbc7`(재귀 차단·판정 정밀화) · `b0f1805`(순환 제거·차단 독립·자기 검사) |
| 재검증 — 새 시험 | PASS | `uv run pytest tests/test_hs_0302*.py -q` 12:00:20 → `66 passed in 4.11s` (1차 28 + 2차 38) |
| 재검증 — 전체 | PASS | `uv run pytest -q` 12:00 → `295 passed in 14.58s` (229 기준선 + 66) |
| 재검증 — ruff·mypy | PASS | `All checks passed!` · `Success: no issues found in 46 source files`, rc=0 |
| 재검증 — 인수 | PASS | 12:00:45 → `PASS` 11줄, `CHECKED: 11`, rc=0. HMAC 판정을 문자열 탐지에서 실행 probe(16건)로 교체 |
| V2 재현기 (GREEN 후) | PASS(주의) | 원본 `v2_0302_codex.py` 는 (1) 에서 `CandidateIdentityError: candidate_ref must not contain control characters` 로 중단된다 — 계약 충돌 때문에 원본 기대 `(1) inserted inserted 2` 는 도달 불가. 사본 `v2_0302_codex_after_green.py` 11:25:31 → `(1a) collision False`·`(1b) 둘 다 REJECTED`·`(1c) rows 0`·`(1d) 합법쌍 둘 다 inserted`·`(1e) rows 2`·`(2) REJECTED`·`(3) REJECTED` |
| 변이 M1 제어문자 거부 제거 | 생존 0 | 11:27:09 → 11 failed. 길이 접두는 유지되므로 순수 함수 충돌 시험 3건은 여전히 통과 — 이중 방어가 실제로 독립임을 보여준다 |
| 변이 M2 길이 접두→구분자 결합 | 생존 0 | 11:27:42 → 6 failed. 인수 probe 도 `BAD` 6건으로 불합격 |
| 변이 M3 양방향 포함→동일 비교 | 생존 0 | 11:28:14 → 키 경계 2건 실패(중첩 하위·역방향) |
| 변이 M3b 상위 사슬 symlink 검사 제거 | 생존 0 | 11:28:25 → 조부모 symlink 시험 1건 실패 |
| 변이 M4 fromisoformat 제거 | 생존 0 | 11:28:26 → `2026-02-29T00:00:00Z` 1건 실패(정규식이 못 잡는 사례) |
| 변이 M4b 정규식 범위 제거 | 생존 0 | 11:28:42 → `2026-09-15T24:00:00Z` 1건 실패(fromisoformat 이 못 잡는 사례). M4 와 M4b 가 서로 다른 사례를 잡는다 |
| 변이 M5 fail-closed→skip | 생존 0 | 11:59:55 → 인수 스크립트 자기 검사 `FAIL` + rc=1, pytest 2건 실패, 9.56초 |
| 사고 — 인수 검사 무한 재귀 | 해소 | 1차 시도에서 인수 검사의 pytest 단계가 자기를 부르는 시험을 돌려 프로세스가 1,493개까지 늘었다(612초 타임아웃). 강제 종료 후 ① pytest 단계에서 자기 호출 시험 deselect ② 중첩 차단을 `abort_not_run` 과 분리 ③ subprocess timeout 300초 로 해소. 재실행 9.56초 |
| 원상복구 | PASS | 12:00:20 `git status --short` 0줄, `git diff --stat` 0줄, `git diff 7473ec8 -- storage_schema.py` 0줄 |
| P11 코드 예산 | PASS | 모듈 228줄/최장 29줄 · 1차 시험 435줄/51줄 · 2차 시험 414줄/27줄 · 인수 345줄. hard 600·100 이내 |
| V1 (2차) | **FAIL** | Codex @3061bd3 12:15:57 → F0302-1·F0302-3 해결, F0302-2·F0302-4 부분, 신규 2건(CI 배선·유니코드). 원문 `scratchpad/codex-v1-0302-r2.log` |
| 2차 결함 재현 | PASS | 12:20 실측. DB alias symlink → `ACCEPTED inserted`, 키 루트 안 실제 DB 행 1개. `café`(결합형) vs `café`(분해형) → `hmac 같은가: False`. `NFKC 동일=True` 쌍 2종 확인. `rg acceptance-hs-0302 verify.yml SOT` 0건 |
| 3차 RED | PASS | `3996dd8` — r3 8 failed/3 passed, probe 2 failed/3 passed @3061bd3. 통과 3건은 대조군(평범한 DB 경로 기록·NFKC 전용 쌍 2건 이미 분리) |
| 3차 GREEN | PASS | `55602f1`(모듈·인수·CI 배선) · `1b7e75d`·`234a1de`(fail-closed 판정 강화) |
| 재검증 — 새 시험 | PASS | `uv run pytest tests/test_hs_0302*.py -q` 12:31:25 → `79 passed in 1.65s` |
| 재검증 — 전체 | PASS | `uv run pytest -q` 12:31 → `308 passed in 10.61s` (229 기준선 + 79) |
| 재검증 — ruff·mypy | PASS | `All checks passed!` · `Success: no issues found in 48 source files`, rc=0 |
| 재검증 — 인수 | PASS | 12:31:09 → `PASS` 13줄, `CHECKED: 13`, rc=0. 수집 79건과 실행 79 passed 정확 일치 |
| 재검증 — ci-step-integrity | PASS | `bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh` 12:25 → `VERDICT: PASS`, `CHECKED: 24`, rc=0 |
| V2 재현기 (3차 후) | PASS | `v2_0302_codex_after_green.py` 12:25:21 → 2차와 동일한 9줄 전부 기대치 일치 |
| 변이 N1 DB 경로 검사 제거 | 생존 0 | 12:27:35 → DB symlink 2건 실패, 평범한 경로 1건은 통과(전부 거부 아님) |
| 변이 N2a NFC 제거 | 생존 0 | 12:27:47 → NFC 3건 실패 |
| 변이 N2b NFC→NFKC | 생존 0 | 12:27:48 → NFKC 전용 쌍 2건 실패(오병합). 정규화 선택이 양쪽에서 고정됐다 |
| 변이 N3a CI 스텝 삭제 | 생존 0 | 12:28:03 → 배선 2건 실패 |
| 변이 N3b CI 스텝 echo 대체 | 생존 0 | 12:28 → 조건부·echo 검사 1건 실패 |
| 변이 N3c 정본 명부 행 삭제 | 생존 0 | 12:28 → 명부 1건 실패 |
| 변이 N4a 필터 재주입 | 생존 0 | 12:28:23 → `'2/79 tests collected (77 deselected)'` 로 수집 요약 불합격, rc=1 |
| 변이 N4b 시험 1건만 제외 | 생존 0 | 12:28:53 → `'78 passed, 1 deselected'`. **옛 하한(passed ≥ 37)이면 통과했을 값**인데 정확 대조가 잡았다 |
| 변이 N5 스캔 자기 검사 제거 | 생존 0 | 12:29:14 → probe 1건 실패 |
| 변이 N6 판정기 완화 + fail-open | 생존 0 (강화 후) | 12:29 최초 실행에서 자기 검사 2건이 **통과**했다 — 첫 NOT_RUN 뒤에 중첩 차단이 바로 와서 "뒤따르는 PASS 0건" 이 우연히 성립. 판정을 "첫 NOT_RUN 뒤 어떤 판정 줄도 없어야 한다"로 바꾼 뒤 12:30:27 재실행 → probe 2건 모두 실패 |
| 원상복구 | PASS | 12:31:25 `git status --short` 0줄, `git diff 7473ec8 -- storage_schema.py` 0줄 |
| P11 코드 예산 | PASS | 모듈 251줄/최장 29줄 · 1차 435 · 2차 318 · 3차 292/25 · probe 146/24 · 인수 418줄. hard 600·100 이내 |
| V1 (3차) | NOT_RUN | 독립 검증 엔진 대기 |
| push·Draft PR | NOT_RUN | 공통 규칙상 이 세션은 push·PR 을 하지 않는다 |
