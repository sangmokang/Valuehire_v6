# Valuehire v6 — 이 저장소의 실제 게이트 명령 (SOT)

최종 갱신: 2026-08-24 (0건 비밀 스캔 차단·도달 가능한 과거 PII blob 내용 검사; 아래 명령은 실행으로 확인)
근거: `docs/engineering/docs-sot-restructure-goal-2026-08-08.md`

## 현재 규칙

**이 저장소는 make 레포도 npm 레포도 아니다.** `Makefile`·`package.json`이 없고, `make -n red-ledger`는 `No rule to make target` 로 실패한다(2026-08-08 실행 확인). `~/.claude/skills/harness/SKILL.md`가 기본 전제하는 `make task` / `make verify` / `make ship` 은 이 저장소에 아직 없다 — 아래가 대신 쓰는 실제 명령이다.

| 게이트 | harness 스킬의 기본 명령 | 이 저장소의 실제 명령 |
|---|---|---|
| 0 — 시작 자격(RED 미해결 확인) | `make red-ledger` | `bash scripts/session-status.sh` (stdout 3번째 줄 `RED: N/M`) |
| 2 — 워크트리 파기 | `make task NAME=...` | `git worktree add worktrees/<name> -b task/<name>` |
| 4 — 검증 | `./verify.sh` | `bash verify.sh` (비밀 스캔) — 대상 1개 이상을 모두 읽어 위반이 없을 때만 `PASS`, `CHECKED: N`, exit 0이다. 비밀/금지 파일은 `FAIL`, exit 1이고, 유효 패턴 없음·Git 읽기 실패·대상 0개는 `NOT_RUN`, exit 2다. CI(`verify.yml`)가 실제로 도는 검사 전체는 아래 "CI가 실제로 돌리는 것" 표가 정본이다. `scripts/acceptance-0-2.sh`는 로컬 전용(`.secret-patterns`에 실제 리터럴이 있어야 해서 CI에 못 올림, 스크립트 주석에 명시) |
| 5 — 배송 | `make ship` | 아직 스크립트 없음 — `git push -u origin task/<name>` 후 `gh pr create` 수동 실행. push 시 `hooks/pre-push`가 verify.sh + acceptance-*.sh 전량(glob)을 재실행 |
| 6 — 종료 | `make task-done NAME=...` | `git worktree remove worktrees/<name>` 수동 실행 |

### CI(`​.github/workflows/verify.yml`)가 실제로 돌리는 것

**워크플로의 이름 있는 스텝 24개 전부**를 적는다(2026-08-12 V1 D6: 이전 판은 `bash ...` 직접 명령만 적어 인라인 본문 스텝이 목록에서 빠졌고, 운영자가 실제로 무엇이 도는지 잘못 판단할 수 있었다). 아래는 `verify.yml` 의 `- name:` 스텝 순서 그대로다.

| # | 스텝 이름 | 실행 내용 |
|---|---|---|
| 1 | 비밀 스캔 (verify.sh) | `bash verify.sh` — 추적 파일 전체 |
| 2 | Strict 원칙 정본·장부·배선 검사 | `bash scripts/acceptance-principles-check.sh` — 32개 정본 문구·장치·명시적 pre-push/CI 배선 |
| 3 | Strict 원칙 적대 fixture·500/501 경계 | `bash scripts/acceptance-principles-mutations.sh` — 정상 fixture와 14개 반례·500/501 경계 |
| 4 | Strict 전역 스킬 잠금 장치 격리 회귀 | `bash scripts/acceptance-guard-global-skill-files.sh` — lock/check/unlock/recover와 동일 UID 한계 |
| 5 | HumanSearch G1 클린룸 경계 | 인라인 8개 — `scripts/acceptance-hs-cleanroom.sh`, `scripts/acceptance-hs-cleanroom-mutations.sh`, `scripts/acceptance-hs-cleanroom-absolute-paths.sh`, `scripts/acceptance-hs-cleanroom-absolute-contexts.sh`, `scripts/acceptance-hs-cleanroom-colon-paths.sh`, `scripts/acceptance-hs-cleanroom-file-urls.sh`, `scripts/acceptance-hs-cleanroom-hook-env.sh`, `scripts/acceptance-hs-cleanroom-hook-env-mutations.sh` |
| 6 | HumanSearch G2 테스트 게이트 | 인라인 — `uv` 설치 후 `scripts/acceptance-hs-gates.sh`, `scripts/acceptance-hs-gates-mutations.sh`, `scripts/acceptance-hs-gates-antiforge.sh` (정적 ruff/mypy + pytest 수집·runtime import 증명) |
| 7 | 히스토리 전량 스캔 | 인라인 — 도달 가능한 모든 blob 을 열어 자격증명 패턴 대조 |
| 8 | 인수 검사 0-2 상시/종료상태 분리 | `bash scripts/acceptance-0-2-unreachable-content.sh` — 환경 격리·네 객체형·도구 실패·큰 객체·종료상태·훅 환경 무오염 13개 합성 사례 (AC-19) |
| 9 | 인수 검사 0-6 | `bash scripts/acceptance-0-6.sh` |
| 10 | 인수 검사 0-7 | `bash scripts/acceptance-0-7.sh` — 훅 위반 6종 시연 |
| 11 | 인수 검사 0-5 | `bash scripts/acceptance-0-5.sh` — **`main` 브랜치에서만** (`if: github.ref == 'refs/heads/main'`) |
| 12 | 억제 만료 스캔 | 인라인 — `suppressions.yaml` 의 expiry 형식·경과 |
| 13 | 강제 장치 존재 검사 | 인라인 — `hooks/pre-commit`·`pre-push` 존재·실행권한 |
| 14 | 셸 스크립트 문법 검사 | 인라인 — `git ls-files '*.sh'` 전부 `bash -n` |
| 15 | 패턴 파일 자체 실값 검사 | 인라인 — `.secret-patterns.default` 에 값 리터럴 없는지 |
| 16 | 인수 검사 hs-a3 | `bash scripts/acceptance-hs-a3.sh` — 세션 계열 자격증명 (AC-A3) |
| 17 | 데이터 노출 스캔 | `bash scripts/scan-data-exposure.sh all` — 크기·금지경로·기록·개인정보 (AC-A4) |
| 18 | 인수 검사 hs-a4 | `bash scripts/acceptance-hs-a4.sh` — 차단이 실제로 도는가 (AC-A4) |
| 19 | 인수 검사 repository-data-protection | `bash scripts/acceptance-repository-data-protection.sh` — 부분 Git 목록·SQL 주석/문자열·경로 가명·all 집계 계약 |
| 20 | 인수 검사 secret-webhook-vendor | `bash scripts/acceptance-secret-webhook-vendor.sh` — 웹훅·벤더 키 (AC-S1) |
| 21 | 인수 검사 verified-sha | `bash scripts/acceptance-verified-sha.sh` — 로컬·원격·CI SHA 귀속 진리표 (P23) |
| 22 | 인수 검사 ci-step-integrity | `bash scripts/acceptance-ci-step-integrity.sh` — 조건부·오류무시·출력 대체 차단 |
| 23 | 인수 검사 semantic-mutations | `bash scripts/acceptance-semantic-mutations.sh` — 인수 검사 무력화 6종 차단과 정확한 Git 대상 수집 |
| 24 | 인수 검사 verify-ac-m | `bash scripts/acceptance-verify-ac-m.sh` — mechanism 명부 대조 (AC-M) |

*(1번 앞에 `actions/checkout` 이 있고 `fetch-depth: 0` 이다 — 4번이 과거 blob 을 열려면 필요하다.)*

**CI는 고정 목록이고 로컬 `pre-push`는 글로브(이름 규칙 자동 수집)다.** 그래서 새 인수 스크립트를 만들면 로컬에서는 저절로 돌지만 CI에서는 한 줄도 안 돈다 — P15③("로컬에만 있는 검사는 없는 것으로 친다")에 걸린다. **새 `scripts/acceptance-*.sh`를 추가하는 PR은 `verify.yml`과 이 표 양쪽에 자기 줄을 함께 넣어야 한다.**

### 데이터 노출 판정기 — `scripts/scan-data-exposure.sh`

후보자 데이터가 git으로 새는 세 경로를 **한 판정기**로 막는다. CI도 인수 검사도 **같은 파일을 실행**한다 — 규칙을 두 벌로 적으면 반드시 갈라진다(2026-08-12 실측: 인라인 본문 시절엔 CI 스텝에 `if: ${{ false }}`를 넣어 영구히 꺼도 로컬 방어 셋이 전부 초록이었다).

| 모드 | 무엇을 보나 |
|---|---|
| `tracked` | 지금 추적 중인 파일의 크기(1MB)·금지 경로 |
| `history` | **도달 가능한 모든 blob과 모든 commit-tree 경로 연결**의 크기·금지 경로와 `*.csv`·`*.tsv`·`*.sql` 개인정보 내용 — 커밋 후 지운 파일의 과거 본문 및 동일 내용의 안전 확장자 alias까지 |
| `pii` | 현재 추적 `*.csv`·`*.tsv`·`*.sql`의 **개인정보 컬럼 조합** — 크기·확장자로는 안 잡히는 것 |
| `all` | 셋 다 (CI가 쓰는 모드) |

종료값 `0=PASS / 1=FAIL / 2=NOT_RUN`. 모든 모드는 마지막에 실제 처리 수 `CHECKED: N`을 한 번 출력한다. **검사 대상 0건이나 Git 객체 열거·형식·크기·본문 읽기 실패는 통과가 아니라 `NOT_RUN`이다**(P3·P20).

현재 `pii`와 `history`는 `scan_pii_content` 한 함수를 재사용한다. history는 모든 도달 가능 commit tree의 blob-경로 연결을 NUL 경계로 열거하므로 제어문자가 든 경로와 안전 확장자 alias도 숨지 못한다. SQL은 판정용 사본에서 `--`·`#`·`/* */` 주석과 작은따옴표 문자열 내용을 제거하고 줄바꿈·탭을 공백으로 정규화한 뒤, 같은 사본에서 완전한 개인정보 컬럼 낱말과 단일 세미콜론 경계 안의 `INSERT INTO ... VALUES` 또는 테이블 대상 `COPY ... FROM`을 판정한다. `COPY (SELECT ... FROM ...) TO` 내보내기와 서로 다른 SQL 문장의 키워드는 적재로 합치지 않는다. CSV·TSV도 완전한 컬럼 낱말 2종 이상과 데이터 행이 함께 있어야 차단한다. 따라서 `username,mailer`, 개인정보 낱말이 주석·문자열에만 있는 SQL, schema-only SQL은 통과한다.

`scripts/acceptance-repository-data-protection.sh`는 42개 사례를 정확히 요구한다. 여기에는 현재·삭제 history·all의 여러 줄 `COPY ... FROM` 적재문, `copy` 컬럼 schema-only SQL, 완전한 개인정보 낱말 경계, 주석·문자열 개인정보 대조군, 문장 경계, COPY query export 대조군이 포함된다. 부분 문자열을 개인정보 낱말로 세거나 서로 다른 문장을 합치거나 COPY 내보내기를 적재로 판정하면 이 acceptance가 실패한다.

scanner는 금지경로·크기초과·PII 위반·경로 관련 NOT_RUN에서 원문 경로를 출력하지 않는다. `path <12hex>`는 `printf '%s' "$path" | shasum -a 256` 결과의 앞 12자리인 결정론적 가명이며 비식별화가 아니다. 같은 경로는 current/history에서 같은 지문이다. 운영자는 로컬에서만 `bash scripts/resolve-data-path-fingerprint.sh <12hex>`를 실행해 현재 추적 경로와 삭제된 commit-tree 경로를 역조회한다. 2개 이상이 나오면 도구는 모든 shell-escaped 후보와 `COLLISION`을 출력하고 성공으로 접지 않는다. 이 로컬 출력은 CI·goal·판정서에 복사하지 않는다.

**금지 경로 목록은 `hooks/pre-commit`과 이 판정기 두 곳에 있다**(훅은 '스테이지된 것'만 보므로 별도 코드다). 한쪽만 넓히면 조용히 갈라지므로 `scripts/acceptance-hs-a4.sh`가 두 목록의 동치를 검사한다.

`scripts/acceptance-hs-a4.sh`는 49개 사례를 정확히 요구한다. 기존 48개 회귀에 더해 전용 repository-data-protection acceptance가 CI의 `run-acceptance.sh`와 이 표에 정확히 한 번 연결됐는지 독립 확인한다. `scripts/acceptance-repository-data-protection.sh`는 42개 사례를 정확히 요구하며, 정상 CSV/SQL 대조군과 부분 Git·SQL·경로 가명·집계 계약을 함께 검증한다. 추적 대상은 `git ls-files -z`의 성공한 전체 NUL 목록을 먼저 저장하고 그 실제 수와 처리 수를 정확히 비교한다. 같은 파일 판정 함수로 직접 작성 파일 600줄 이하와 합성 600/601 경계, 함수 100/101 경계를 확인하며 신규 전용 acceptance와 로컬 역조회 도구도 코드 예산 대상이다.

### 주요 기능 정본 구조 검사 — `scripts/check-docs-sot.sh`

```bash
bash scripts/check-docs-sot.sh
```

현재 71줄 검사기는 필수 SOT 파일 5개의 존재·20,000바이트 상한과 훅 관련 실행 파일 5개의
`docs/sot/hook-contracts.md` 계약 참조만 검사한다. 각 항목의 `PASS:`/`FAIL:`과 마지막 전체 판정을
출력하며 하나라도 어긋나면 exit 1이다. 기능 문서 구조나 제품 표면을 검사하지 않는다.

이 명령은 현재 수동 검사이며 pre-push와 CI에는 연결하지 않았다. 따라서 exit 0은 위 10개 정적 항목만
통과했다는 뜻이고 repository-data-protection 완료나 병합 준비 근거로 사용하지 않는다. 전역 기능 문서·제품
표면 검증 부재는 별도 `REQUEST_CHANGES`이며, 각 기능 YAML의 `verification` 원명령을 따로 실행해야 한다.

## 시행 지점

이 문서 자체가 "가정 대신 실행 확인"의 산출물이다. 명령이 바뀌면(예: `Makefile`이 나중에 생기면) 이 표를 그 시점에 다시 실행해서 갱신한다 — 표를 먼저 고치고 나중에 확인하지 않는다.

## 비범위 / 한계

- `main` 브랜치 GitHub 보호 규칙의 실제 활성화 여부는 확인하지 않았다(`docs/sot/git-workflow.md` 한계와 동일).
- 이 표는 2026-08-20 실행 결과의 스냅샷이다. 스크립트가 추가/삭제되면 다시 확인해야 한다.
