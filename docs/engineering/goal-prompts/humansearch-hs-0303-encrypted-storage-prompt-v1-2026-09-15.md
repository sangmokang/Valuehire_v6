# 착수 프롬프트 v1 — HS-03.03 암호화 저장: 계약 확정 → 구현 (2026-09-15 16:10)

## 결론

HS-03.02(후보 동일성·중복 방지)는 2026-09-15 16시 기준 코드·시험·인수·독립 검토까지 로컬에서 끝났고 PR #100(Draft) 갱신만 사장님 승인 대기다. 다음은 HS-03.03 — 후보 원문·캡처·추출물을 **보호 저장소에 암호화해 저장**하는 일이다. 저장 정본 §4는 "암호화 방식과 키 보관은 이 문서에서 고르지 말고 별도 계약으로 먼저 확정하라"고 못 박았고, 현재 `humansearch` 는 런타임 의존성이 0개(개발 도구 4개뿐)라 **암호화 라이브러리가 없다**. 그래서 이 작업은 코드보다 **결정 카드 1장이 먼저**다. 아래를 새 세션에 그대로 붙여넣는다.

## 사장님이 먼저 결정할 것 (코드 착수 전, 1장)

> **무엇을** — 후보 원문 암호화 방식과 키 보관 위치를 고른다.
> **왜** — 저장 정본 §4가 "표준 라이브러리 · OS 키 저장소 · 이미 승인된 의존성 중 하나를 별도 계약으로 확정한 뒤 구현"을 요구한다. Python 표준 라이브러리에는 대칭 암호(AES 등)가 없다(`hashlib`·`hmac`·`secrets` 뿐). 그래서 셋 중 하나를 골라야 한다.
> **선택지** —
>   A. `cryptography` 패키지 추가(AES-256-GCM, 키 파일 0600, 보호 root 밖). 새 의존성 1개, 승인 필요. 가장 흔한 길.
>   B. macOS 키체인(`security` CLI)에 키 보관 + `openssl enc` 로 암호화. 의존성 0개이나 셸 호출·macOS 종속·CI(리눅스) 재현 불가.
>   C. `age` CLI(외부 실행 파일). 의존성은 코드 밖이나 설치 관리·경로 검증이 추가로 필요.
> **권고** — A. 이유: 순수 파이썬 호출이라 시험·변이·CI 재현이 되고, 키 파일 경계는 HS-03.02가 만든 `_load_hmac_key` 규칙(0700 폴더·0600 파일·DB 루트와 분리)을 그대로 재사용한다.
> **대가** — 의존성 1개(uv.lock 갱신, 공급망 검토 1회). 키 회전은 이 WU 비범위.
> **되돌리기** — 암호문 형식에 `alg` 필드를 넣어 두면 방식 교체 시 재암호화 마이그레이션 1회로 복구된다.

결정 없이는 2단계 이후를 착수하지 않는다. 결정이 A가 아니면 이 프롬프트의 3~5단계를 그 방식에 맞게 다시 쓴다.

## 역할

너는 HS-03.03 담당이다. HS-03.02 코드(`candidate_identity.py`)·마이그레이션·`storage_schema.py` 는 수정하지 않는다. "통과했다" 대신 명령·종료값·출력 원문만 기록한다. push·PR 은 사장님이 이 세션에서 명시 승인할 때만 한다.

저장소: /Users/kangsangmo/Desktop/Valuehire_v6
작업 위치: 새 워크트리 `worktrees/hs-0303-encrypted-storage-<YYYYMMDD>` (브랜치 `task/hs-0303-encrypted-storage-<YYYYMMDD>`), 스택 베이스 = `task/hs-0302-candidate-identity-20260914` 최종 HEAD(PR #100). 메인 작업트리·다른 워크트리 수정 금지. 파괴적 실증은 mktemp 아래에서만, git 환경변수 unset.

## 0. 착수 조건 (값을 전부 기록, 불일치면 착수하지 않고 §8 형식 보고)

- `pwd; git branch --show-current` → 위 브랜치
- `git status --short` → 출력 없음
- `git log --format='%h %ci %s' -3` → 베이스가 PR #100 최종 HEAD 인지(`gh pr view 100 --json headRefOid`)
- `stat -f '%Sm' -t '%F %T' "$(git rev-parse --git-dir)/index"` → 10분 이내면 `lsof +D "$PWD"`·`ps` 로 다른 쓰기 세션 확인, 입증될 때만 중단
- `git fetch origin | tail -1; git rev-list --left-right --count HEAD...origin/<branch>` → 오른쪽 0
- `git config core.hooksPath` → hooks
- `cd humansearch && uv run --frozen pytest -q | tail -1` → `331 passed`(2026-09-15 17시 기준, HEAD d84dc41 이후), `ruff check`·`mypy` 종료값 0
- `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh | tail -3` → `CHECKED: 22` rc 0
- `docs/sot/humansearch-storage-contract.md` §3·§4·§5 를 직접 읽고 `rg -n '암호화|키 원본|키 없음|잘못된 키|손상 암호문' docs/sot/humansearch-storage-contract.md` 원문 기록
- strict 0.1: `docs/sot/coding-principles.md`·`principles.yaml` 직접 로드, `bash scripts/acceptance-principles-check.sh` → `CHECKED: 34`

## 1. 프롬프트 회수 커밋

이 파일을 `docs/engineering/goal-prompts/humansearch-hs-0303-encrypted-storage-prompt-v1-2026-09-15.md` 로 두고 커밋: "HS03.03 암호화 저장 착수 프롬프트 v1 을 저장소에 둔다". `git show --stat HEAD` 에 파일 1개만.

## 2. 계약 문서 (코드 전) — `docs/engineering/humansearch-hs-0303-encrypted-storage-goal-<날짜>.md`

포함: 결정 카드(위 A/B/C 중 사장님 결정 원문), 암호문 파일 형식(`alg`·`nonce`·`ciphertext`·`aad`= `(position_ref, channel, candidate_key_hmac)` 길이 접두 직렬화 — HS-03.02 와 같은 방식), 키 파일 경계(0700/0600, DB 보호 root 와 양방향 비포함, symlink 사슬 거부 — `candidate_identity._load_hmac_key` 규칙과 동일하되 **다른 키 파일**), 오류 6종 구분(키 원본 없음 / 복호화 권한 없음 / 키 없음 / 잘못된 키 / 손상 암호문 / 권한 없음 — 정본 §4 문구 그대로), EARS AC 각 1 단언 + 검증 명령 + counter-AC, 입출력 JSON 스키마, 비범위(intent/readback=HS-03.04, 삭제=HS-03.05, 키 회전, Supabase).

키 값·평문 후보 원문은 오류 메시지·로그·PR 본문·Git 에 쓰지 않는다(정본 §4).

## 3. RED (커밋 "HS03.03 암호화 저장 계약을 시험으로 먼저 고정한다")

`humansearch/tests/test_hs_0303_encrypted_storage.py` — 최소 반례:
- 정상: 평문 → 암호문 파일 0600 · 보호 root 안 · 복호화 = 원문 (양성 대조군)
- 잘못된 키로 복호화 → 구분된 오류, 평문 0바이트 유출
- 암호문 1바이트 변조 → "손상 암호문" 오류(잘못된 키 오류와 **다른** 종류)
- aad 불일치(다른 후보 키로 복호화 시도) → 거부
- 키 파일 0644 / 키 폴더가 DB 보호 root 하위 / symlink → 거부
- 암호문 파일을 Git 작업 폴더 아래에 쓰려 하면 → 거부(HS-03.02 `_verify_db_boundary` 와 같은 규칙, 재사용 가능하면 재사용)
- 필수 시험 명부 `scripts/verify/fixtures/hs-0303-required-tests.txt` + 인수 스크립트 `scripts/acceptance-hs-0303.sh`(HS-03.02 스크립트를 본떠 fail-closed·명부 정확 대조·CI 배선 YAML 대조) + `verify.yml` 스텝 + `docs/sot/verification-commands.md` 표 행·머리글 숫자 동반 갱신(27→28)

RED 증거: 실행 시각·`N failed, M passed`·실패 사유가 "빠진 동작"(ModuleNotFoundError 가 아니라 `pytest.fail("... missing")` 형태)인지.

## 4. GREEN (커밋 "HS03.03 후보 원문을 승인된 방식으로 암호화해 저장한다")

의존성 추가는 결정 A 일 때만, 단독 커밋("HS03.03 승인된 암호화 의존성을 추가한다")으로 `pyproject.toml`+`uv.lock` 만. 구현 파일 hard 한도 600줄(정본 P11), 함수 100줄.

AC: 전체 pytest 초록 · ruff·mypy 0 · `run-acceptance.sh scripts/acceptance-hs-0303.sh` PASS · 변이(격리 사본에서 복호화 검증·aad·키 경계 각 줄 삭제) 생존 0 · `acceptance-hs-gates-mutations.sh` 6/6 · `acceptance-ci-step-integrity.sh` PASS.

## 5. 독립 검토 → 장부 → (승인 시) push·Draft PR

`/humanreview` 로 베이스..HEAD 읽기 전용. 최소 공격: 키 바이트·평문이 예외 메시지·로그에 새는가 / 변조 암호문이 잘못된 키로 오분류되는가 / nonce 재사용 / 명부·상수 동반 약화 / CI 스텝 꼬리 주입. REQUEST_CHANGES 면 멈추고 보고. APPROVE 이고 사장님 승인 시에만 `git push` + `gh pr create --draft --base task/hs-0302-candidate-identity-20260914`, 본문은 §8-8 순서.

## 중단 조건

결정 카드 미답 / 0단계 불일치 / 다른 세션 변경 / 검사기 FAIL / 변이 생존 / REQUEST_CHANGES.

## 비범위

HS-03.02 코드 변경, `storage_schema.py`·마이그레이션, intent/readback(HS-03.04), 삭제(HS-03.05), 키 회전, Supabase, 실제 포털 후보 읽기, merge.

## HS-03.02 에서 넘기는 사실 (2026-09-15 16시 실측)

- `candidate_identity._verify_db_boundary` 가 쓰기 직전 부모 0700·DB 0600·UID·일반 파일·Git 밖·보조 파일을 본다. 보조 파일은 **한 번의 lstat** 로만 본다 — HS-03.01 `_verify_existing_sidecars` 를 재사용하면 경쟁 연결의 journal 이 사이에 사라져 20회 중 7회 오거부된다(실측). HS-03.03 도 같은 함정을 피한다.
- 필수 시험 명부는 하한이 아니라 **정확 기대값**(`EXPECTED_REQUIRED_IDS`, 현재 102)으로 대조한다. 시험 함수+명부+상수 3개를 함께 지우는 약화는 잡지 못한다(알려진 한계, Codex 2회차 실측 `99 passed`·`CHECKED: 22` 통과).
- 검사 통과 뒤 읽기 전에 키 파일·키 폴더가 사라지는 경쟁에서 `FileNotFoundError` 가 절대 경로째 새어 나왔다(Codex 2회차 probe, 16:42 재현, d84dc41 에서 닫힌 오류로 수정). HS-03.03 의 키 파일 읽기·암호문 파일 쓰기도 **OS 호출을 전부 닫힌 오류로 감싸고**, 그 감싸기 각 줄을 변이로 검증한다.
- Codex 상자는 임시 폴더 생성과 `uv` 캐시 쓰기를 막고(1회차 NOT_RUN), 보안 어휘가 많은 보고서는 정책 차단으로 종료된다(2회차, 138k 토큰 소진 뒤 판정 유실). 검토는 `--no-local` 클론 + `codex exec -s workspace-write --add-dir <임시>` 로 띄우고, 프롬프트에 **단계별 파일 저장**과 중립 어휘(mutation·variant·negative control)를 지시한다.
- G2 게이트는 `humansearch/src`·`tests` 만 사본으로 복사한다 — 시험 파일에 `scripts/`·`docs/sot`·`.github` 경로 문자열이 주석에라도 있으면 인수 검사가 FAIL 이다.
