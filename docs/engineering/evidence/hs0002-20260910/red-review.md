VERDICT: PASS

## 결론

HS-00.02 테스트는 구현 전 RED로 적합하다. pytest가 20개를 정상 수집했고, import·문법·수집 오류가 아니라 기존 제품 함수의 사유 대조 결함 때문에 12개가 실패했다. 정상 대조군 8개는 통과해 "항상 실패" 테스트도 아니다.

한계는 sameUID localreview다. 이 검토는 같은 로컬 사용자 권한의 독립 검토이며, OS 권한 분리나 P17 러너 전용 영수증은 아니다.

## 성공 기준

- `docs/engineering/humansearch-next-issues-wu-2026-09-10.md:124` — HS-00.02는 "다른 실패 사유의 부분문자열 일치→거짓 통과 재현·차단; 실제 기대 사유는 통과"를 요구한다.
- `docs/engineering/humansearch-hs0002-goal-2026-09-10.md:20` — 기대 사유가 실제 FAIL 행의 정규 문구에 있으면 PASS, 없거나 부분문자열·정규식·PASS 행 미끼뿐이면 FAIL이어야 한다.
- `docs/engineering/humansearch-hs0002-goal-2026-09-10.md:24` — `불량XYZ`를 `불량`으로 세면 안 되고, 기존 짧은 사유 3종은 기존 검사기가 출력하는 대상·행 문구 전체의 정규 형식에서만 인정해야 한다.
- `docs/engineering/humansearch-hs0002-goal-2026-09-10.md:40` — 정조준 명령은 `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0002.py`다.

## 시험 파일 검토

- `humansearch/tests/test_hs_0002.py:38` — 실제 `negative` 함수 호출용 harness를 만든다.
- `humansearch/tests/test_hs_0002.py:55` — `scripts/acceptance-hs-kickoff-mutations.sh`에서 추출한 현재 `negative()` 함수 본문을 실행 harness에 넣는다.
- `humansearch/tests/test_hs_0002.py:56` — `negative fixture 'printf changed > "$WT/changed.txt"' "$EXPECT"`로 실제 negative 함수 경로를 호출한다.
- `humansearch/tests/test_hs_0002.py:71` — 정상/반례 표본 10개가 기대 사유, 다른 사유 부분문자열, 문자 경계, 정규식 미끼, PASS 미끼, 공백·따옴표·달러, 빈 기대값, 빈 로그, 백슬래시를 포함한다.
- `humansearch/tests/test_hs_0002.py:146` — 기존 짧은 사유 3종과 `판정 문서 없음`의 정상 문구 및 unrelated-context 미끼를 대조한다.
- `humansearch/tests/test_hs_0002.py:164` — Hypothesis 속성 시험으로 정규식 메타문자 조합의 literal 통과를 확인한다.
- `humansearch/tests/test_hs_0002.py:172` — Hypothesis 속성 시험으로 앞 문맥·뒤 문자 확장이 기대 사유로 세어지지 않음을 확인한다.

→ 테스트는 제품 구현 문자열 복사가 아니라 현재 shell 함수의 런타임 결과를 보고 판정한다. 단, 전체 mutation 스크립트를 source하지 않고 함수 본문을 추출해 harness에 넣는 방식이라 full-script wiring 증거는 아니다. 이번 WU의 범위가 사유 대조 함수의 RED 고정이므로 차단 결함은 아니다.

## 기존 결함 연결

- `scripts/acceptance-hs-kickoff-mutations.sh:176` — 현재 제품의 `negative()` 함수 시작점이다.
- `scripts/acceptance-hs-kickoff-mutations.sh:189` — 현재 구현은 `/usr/bin/grep -q -- "$expect" "$TMP/out.log"`로 찾는다.
- `scripts/acceptance-hs-kickoff-mutations.sh:192` — grep이 잡으면 기대 사유로 차단됐다고 PASS 처리한다.

→ 이 구현은 기본 정규식 grep과 전체 파일 검색이라 부분문자열, 정규식 메타문자, PASS 행 미끼, 빈 기대값 문제를 만들 수 있다. pytest 실패는 이 줄들과 직접 연결된다.

## 실행 증거

- `bash scripts/acceptance-principles-check.sh` — 종료값 0. 출력: `VERDICT: PASS`, `CHECKED: 34`.
  → Strict 원칙 정본과 원칙 장부 직접 로드 조건은 충족했다.

- `cd humansearch && uv run --no-sync pytest --collect-only -q tests/test_hs_0002.py` — `artifacts/hs0002-20260910/red-review-collect.log`, 시작 `2026-09-09T21:51:50Z`, 종료값 0, 전체 출력 보존, sha256 `1d763ed2774ceef122c11cca3b77e8d8cafd826ba86c3bd12026015879e4178a`.
  → 20개 테스트가 수집됐다. 수집 0개, import 오류, 문법 오류가 아니다.

- `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0002.py` — `artifacts/hs0002-20260910/red-review-pytest.log`, 시작 `2026-09-09T21:50:52Z`, 종료값 1, 전체 출력 보존, sha256 `3451b9a9b947ea373ffb63e8bd56903316a7c6e0c608232db584609a78067dd8`.
  → 결과는 `12 failed, 8 passed in 7.25s`다. 실패는 `tests/test_hs_0002.py:141`, `:161`, `:169`, `:178`의 기대 returncode 단언에서 발생했다.

- `cd humansearch && uv run --no-sync ruff check tests/test_hs_0002.py` — `artifacts/hs0002-20260910/red-review-ruff.log`, 시작 `2026-09-09T21:51:28Z`, 종료값 0, 전체 출력 보존, sha256 `ebf40f8e59f7ea58313cb13bfd3dc24cc2b0533defe33fb9bd7ab7255893bdf2`.
  → 테스트 파일 형식 문제나 import 정렬 문제로 RED가 된 것이 아니다.

- `artifacts/hs0002-20260910/red-review-meta.log` — HEAD, status, 파일 지문, 줄수, 기존 RED 메타를 보존했다. sha256 `30a07e18f7b433a603e51e257b39477892ddebbef6009938b403e6fedb51c4b1`.
  → 현재 HEAD는 `6cef849b36e4dc11fd272e4bfe50af2f5e8db537`이며 기존 `red.json`도 head_before/head_after가 같은 SHA라고 기록한다.

## 파일 지문과 범위

- `humansearch/tests/test_hs_0002.py` — sha256 `8817487d8aa6d5dcc741ba3306541cb3addf4db1d754dec87af77f789ed8be43`, 178줄.
- `scripts/acceptance-hs-kickoff-mutations.sh` — sha256 `4569309a6e2a5614e43d7442d80bf9808d221995081c2097cf813e6ac0c9181e`, 593줄.
- 기존 RED 산출물 `artifacts/hs0002-20260910/red.log` — sha256 `86f7e355117dbdc42b23c1c09b779725030bf250154db21bcd9f5f914e5b3629`.

→ 원칙 정본의 파일 hard limit은 600 LOC다. 새 테스트 파일은 한도 아래다. 기존 shell 스크립트는 593줄로 매우 가깝기 때문에 GREEN 구현은 목표 문서의 계획처럼 helper 분리 방향이 맞다.

## Gaps

- 이 검토는 RED 테스트 적합성 검토다. 제품 수정, GREEN 검증, mutation diff, Claude V1, 새 맥락 Codex V2, 원격 CI, OS 권한 분리 영수증은 실행하지 않았다.
- full-script acceptance 실행은 하지 않았다. 이번 검토 대상은 `humansearch/tests/test_hs_0002.py`가 구현 전 RED인지이며, 제품 전체 acceptance 통과 여부가 아니다.

## Risks

- `test_hs_0002.py`는 `negative()` 함수 본문을 원본 shell 파일에서 추출해 실행한다. 함수 본문 내부 결함을 정확히 잡지만, shell 파일의 전체 하단 호출 목록이나 전역 변수 초기화 변화까지 증명하지는 않는다.
- `scripts/acceptance-hs-kickoff-mutations.sh`는 593줄이라 직접 구현을 추가하면 600줄 hard limit을 넘길 위험이 있다. helper 분리 없이 이 파일에 8줄 이상 추가하면 별도 파일 한도 실패가 된다.
