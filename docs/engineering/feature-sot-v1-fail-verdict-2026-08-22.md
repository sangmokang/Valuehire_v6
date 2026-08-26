# Claude V1-B 적대검증 원문 — FAIL

- 실행 신원: Claude Code 2.1.238
- 세션: `4d697200-803a-4002-ac9b-27f218565bc5`
- 인증 환경: `ANTHROPIC_API_KEY=UNSET`
- 모드: `--safe-mode --permission-mode dontAsk --tools Bash,Read,Grep,Glob --effort medium`
- 종료값: `0` (검증 판정은 아래 원문의 `FAIL`)
- 실행 전후 상태 SHA-256: `fc07fe17312bae5c2c32de95db93197a9049ea3d6a66e75a89fdc14011f4e79d`
- 실행 전후 산출물 SHA-256: `a1c84cd044fd83081998d16004809fd0f03da49ed37de21a1659249b1af93693`

## 원문

VERDICT: FAIL

## 실행하지 못한 것 (판정 앞 선언)

지시받은 세 명령을 **하나도 실행하지 못했습니다**. 첫 두 번의 `Bash` 호출(`git log`/`ls`/`wc`) 이후 세션이 don't-ask 모드로 전환되어 `bash scripts/check-docs-sot.sh`, `cd humansearch && uv run --no-sync pytest -q`, `git diff --check` 모두 권한 거부로 반환됐습니다. 우회 시도는 하지 않았습니다. 따라서 아래 판정은 **정적 대조만으로 성립하는 근거**에 한정합니다. 실행이 필요한 주장(시험 64개 통과 여부, 종료값, 공백 오류 여부)은 goal 기록을 인용만 하고 검증했다고 주장하지 않습니다.

아래 FAIL 근거는 명령 실행에 의존하지 않습니다. 파일 존재와 문자열 대조만으로 재현됩니다.

## 결론

이 작업이 만든 기능 목록은 "이 저장소가 지금 무엇을 하는가"의 단일 답으로 쓰겠다고 선언했지만, 지금 이 저장소가 모든 커밋과 모든 push에서 실제로 강제하고 있는 검사 세 종류가 목록에 아예 없습니다. 빠진 것 중 하나는 바로 직전 커밋(#36)이 추가한 장치이고, 다른 하나는 별도 계약 파일까지 갖춘 8단계 검사입니다. 그러면서 목록 자신은 "검사 대상 폴더는 `hooks`, `scripts`, `verify.yml` 전부"라고 적어 두었으므로, 읽는 사람은 그 폴더의 강제 장치가 모두 분류됐다고 오해하게 됩니다.

더 나쁜 것은, 이 누락을 잡아야 할 검사 스크립트가 기능 6개의 이름을 코드 안에 그대로 박아 두었다는 점입니다. 그래서 무엇이 빠졌는지 검사 스크립트가 원리적으로 알아낼 수 없고, 빠진 것을 나중에 넣으면 오히려 검사가 빨간불이 됩니다. "빠짐없이 분류했다"는 주장은 검사로 뒷받침되지 않고 사람의 선언으로만 남아 있습니다.

여섯 기능 각각의 상태 표기(구현됨/계약만, 로컬 전용/호출자 없음/미연결)는 코드와 대조한 범위에서 모두 사실이었고, 과장은 찾지 못했습니다. 실패 사유는 상태 거짓말이 아니라 **분류 누락**입니다.

## 판단 근거

**선택한 해석** — "주요 기능"의 판정 기준을 제가 새로 만들지 않고, 이 작업이 스스로 고정한 기준을 그대로 적용했습니다. goal 문서와 폴더 INDEX가 똑같이 "pre-commit, pre-push, CI 중 하나에서 저장소 전체 변경을 강제하면 주요 기능"이라고 선정 계약을 적었습니다(`docs/engineering/feature-sot-catalog-goal-2026-08-21.md:86` 선정 조건 2번 줄, `docs/sot/features/INDEX.md:67` 같은 조건의 사용자용 표현). 클린룸 경계·전역 스킬 잠금·억제 만료 세 장치는 전부 이 조건을 문자 그대로 만족하는데 카탈로그에 없습니다. 즉 외부 잣대가 아니라 **자기 규칙 위반**입니다.

**버린 해석 1** — "이 셋은 `verification-evidence-system` 기능이 우산처럼 덮고 있다"고 볼 여지가 있어 실제로 검증했고, 기각했습니다. 그 기능 문서의 `entrypoints`(7개), `evidence`(8개), `authority.delegates`(4개) 어디에도 클린룸·스킬 잠금·억제 만료가 없습니다. 위임 대상인 `docs/sot/mechanism-registry.yaml`에도 없습니다(문자열 검색 0건). 위임은 "경로를 명시적으로 가리키는 것"이라고 그 문서 스스로 정의했으므로(`docs/sot/features/INDEX.md:32` 위임 규칙 줄), 언급조차 없는 것은 위임이 아닙니다.

**버린 해석 2** — "클린룸은 비밀·개인정보 보호 기능의 일부"라는 해석도 기각했습니다. 클린룸이 막는 것은 비밀이 아니라 옛 저장소 이름(`Valuehire_v1-5`)과 `worktrees/` 경로 결합입니다(`contracts/cleanroom-deny-patterns.txt:4-11` 실제 금지 패턴 줄). `repository-data-protection.yaml`의 목적문(:9)은 "비밀, 세션 자격증명, 후보자 개인정보, 대용량 데이터, 금지 산출물 경로"이고 진입점 4개(:31-52)에 클린룸 스크립트가 없습니다. 다른 문제를 다른 계약 파일로 막는 별개 장치입니다.

**제가 틀리면 깨지는 것** — 만약 "주요 기능"을 "제품이 사용자에게 주는 값"으로만 좁게 읽어야 한다면, 저장소 보증 3개도 애초에 기능이 아니어야 합니다. 그런데 이 작업은 그 3개를 기능으로 올렸습니다. 따라서 저장소 강제 장치를 기능으로 세는 기준을 채택한 이상, 같은 성질의 장치를 빼면 기준이 일관되지 않습니다. 이 논리가 틀리려면 "CI에서 강제되지만 기능이 아닌 것"을 구분하는 규칙이 문서 어딘가에 있어야 하는데, 배제 목록(`catalog.yaml:109-115`, 제외 항목 5줄)에는 역사 기록·시험·worktree·후보자 자료·캐시만 있고 이 셋은 해당되지 않습니다.

---

## 기술 상세와 증거 원문

### 결함 D-1 — 심각도: 중대 · "빠짐없이 분류" 계약 위반 (분류 누락 3건)

**원인** — 기능 선정을 사람이 한 번 열거하고 끝냈으며, 열거 결과를 저장소 실제 강제 지점 목록과 기계적으로 대조하는 단계가 없습니다.

빠진 장치 ①: **HumanSearch G1 클린룸 경계**

```text
.github/workflows/verify.yml:40   - name: HumanSearch G1 클린룸 경계
.github/workflows/verify.yml:41-49  run: | (acceptance-hs-cleanroom*.sh 8개 순차 실행)
```
→ CI 잡 `verify`의 한 스텝이 클린룸 검사 8개를 실행하는 자리입니다. push·PR 전부에서 돕니다.

```text
scripts/acceptance-hs-cleanroom.sh:13   PATTERNS=contracts/cleanroom-deny-patterns.txt
scripts/acceptance-hs-cleanroom.sh:45   if ! git ls-files -z > "$FILES"; then
```
→ :13은 별도 계약 파일을 판정 기준으로 읽는 줄, :45는 검사 대상이 **추적 파일 전량**임을 정하는 줄입니다. 저장소 전체 강제가 맞습니다.

```text
contracts/cleanroom-deny-patterns.txt:4   Valuehire_v[1-5]
contracts/cleanroom-deny-patterns.txt:7   (…)/worktre[e]s(/|$|…)
```
→ 금지 대상이 비밀값이 아니라 옛 저장소 참조와 worktree 경로 결합임을 보여주는 실제 패턴 줄입니다.

```text
docs/sot/verification-commands.md:28  | 5 | HumanSearch G1 클린룸 경계 | 인라인 8개 — … |
```
→ 기존 정본이 이미 이 장치를 CI 게이트 5번으로 인정하고 있는 줄입니다. 즉 새 기능 카탈로그만 모르고 있습니다.

빠진 장치 ②: **전역 Strict 스킬 파일 잠금 장치** (직전 커밋 `29ce9da`(#36)의 산출물)

```text
.github/workflows/verify.yml:37-38  - name: Strict 전역 스킬 잠금 장치 격리 회귀
                                     run: bash scripts/verify/run-acceptance.sh scripts/acceptance-guard-global-skill-files.sh
scripts/guard-global-skill-files.sh:4-11  (보장 범위와 한계를 선언하는 계약 주석)
scripts/verify/check-strict-principles-skills.sh:7-9  (인자 없이 부르면 exit 2 — fail-closed 줄)
```
→ CI 스텝 하나가 이 잠금 장치의 회귀 시험을 돌리는 자리이고, 나머지 두 줄은 그 장치 본체와 판정기입니다. 카탈로그 기준 커밋이 바로 이 커밋인데(`feature-sot-catalog-goal-2026-08-21.md:40` 기준 SHA 줄) 그 커밋이 만든 장치가 목록에 없습니다.

빠진 장치 ③: **억제(suppressions) 만료 게이트**

```text
.github/workflows/verify.yml:134    - name: 억제 만료 스캔 (suppressions.yaml)
.github/workflows/verify.yml:143-151  (expiry 형식·만료일·건수 일치를 판정하는 본문)
suppressions.yaml                    (저장소 루트에 실재)
```
→ 억제 항목이 기한을 넘겨 방치되는 것을 매 push마다 막는 자리이며, 대상 파일도 실재합니다.

세 장치 모두에 대한 부재 증거(문자열 검색):

```text
rg -i 'cleanroom|guard-global|suppressions|…' docs/sot/features/
→ No matches found
rg -i 'cleanroom|guard-global|skill' docs/sot/mechanism-registry.yaml
→ No matches found
```
→ 기능 폴더 전체와 위임 대상 명부 어디에도 세 장치가 등장하지 않습니다.

동시에 카탈로그는 이 폴더들을 자기 검사 범위로 선언합니다.

```text
docs/sot/features/catalog.yaml:103-108  "control_roots": ["hooks","scripts",".github/workflows/verify.yml","verify.sh"]
```
→ 저장소 보증 기능이 훑었다고 선언하는 뿌리 경로 목록입니다. `scripts`와 `verify.yml`을 범위로 적어 놓고 그 안의 강제 장치 3종을 빠뜨린 것이라 단순 누락보다 오해 유발도가 큽니다.

**사업 영향** — 다음 작업자가 이 폴더 하나만 읽고 "이 저장소의 강제 장치는 6개 기능이 전부"라고 판단하면, 클린룸 금지 패턴을 모르는 채 옛 저장소 경로를 문서에 적었다가 push가 막히고 원인을 찾지 못합니다. 반대 방향이 더 위험합니다 — 목록에 없는 장치는 "없는 것"으로 취급되어, 리팩터링 중 조용히 제거되거나 CI 스텝이 삭제돼도 기능 정본상 아무 계약도 깨지지 않습니다. 이 저장소가 지금까지 반복해 막아 온 실패 유형(검사의 조용한 소멸)을 기능 정본이 재현합니다.

### 결함 D-2 — 심각도: 중 · 완전성 주장을 검사가 아니라 상수로 고정함 (설계 지적)

```text
scripts/check-docs-sot.sh:86-93   EXPECTED_FEATURE_IDS = { …6개 문자열 리터럴… }
scripts/check-docs-sot.sh:186     if set(catalog_by_id) != EXPECTED_FEATURE_IDS: raise ValueError(…)
scripts/check-docs-sot.sh:81-85   EXPECTED_CATEGORY_IDS = { …3개… }
scripts/check-docs-sot.sh:155     if set(category_ids) != EXPECTED_CATEGORY_IDS: raise ValueError(…)
```
→ :86-93은 기능 6개 이름을 검사 코드 안에 상수로 박아 둔 자리, :186은 카탈로그가 그 상수와 정확히 같아야 통과시키는 자리입니다.

- **무엇을** — 기능 목록의 완전성을 저장소 실제 진입점에서 유도하지 않고 검사 코드 안 상수 6개와의 일치로 판정합니다.
- **왜** — 기능이 조용히 삭제되는 것을 막으려는 의도로 보이며, 삭제 저항이라는 목적 자체는 실제로 달성됩니다.
- **버린 길** — CI 워크플로의 실행 줄과 `hooks/*`, `scripts/acceptance-*.sh`를 훑어 각 강제 지점이 어느 기능 문서에 귀속되는지 대조하는 방식을 택하지 않았습니다. 그 길을 택했다면 D-1의 3건이 이번 실행에서 잡혔습니다.
- **대가** — 누락은 원리적으로 검출 불가이고, 누락을 고쳐 7번째 기능을 넣는 순간 :186이 `current major feature coverage changed`로 종료값 1을 냅니다. 즉 검사가 개선을 막는 방향으로 작동합니다. 카탈로그가 자인한 "이 검사는 pre-push·CI에 연결되지 않았다"(`catalog.yaml:121`)와 겹쳐, 실제로는 사람이 기억할 때만 도는 스냅샷 고정입니다.
- **되돌리기** — :86-93과 :155/:186을 제거하고 귀속 대조로 바꾸면 됩니다. 카탈로그·기능 문서는 그대로 두어도 되고, 제품 코드에는 영향이 없습니다.

**사업 영향** — 이 저장소의 기존 원칙(검사의 존재가 아니라 판정을 본다)과 정면으로 어긋나며, 카탈로그가 커질수록 검사 코드를 매번 손대야 해 "검사를 고쳐서 통과시키는" 습관을 유도합니다.

### 결함 D-3 — 심각도: 낮음 · 근거 경로 존재 검사가 URL을 무검증 통과시키는데 정본은 그렇게 적지 않음

```text
scripts/check-docs-sot.sh:127-130  except ValueError as error:
                                     if value.startswith(("http://","https://")): return
```
→ 근거 항목이 URL이면 아무 검증 없이 조용히 통과시키는 자리입니다.

```text
docs/sot/features/product/admin-weekly-dashboard.yaml:160  "https://github.com/sangmokang/Valuehire_v6/pull/16"
docs/sot/features/automation/humansearch-browser-access.yaml:104  "…/pull/34"
```
→ 실제로 검증되지 않는 근거 2건입니다.

```text
docs/sot/verification-commands.md:72-74  "…호출점·세부 정본·근거 경로가 현재 저장소에 실제로 존재하는지 확인한다."
```
→ 예외를 밝히지 않은 채 근거 전부를 검증한다고 읽히는 문장입니다.

**원인** — 예외 분기를 코드에는 넣었으나 정본 문구에 반영하지 않았습니다. **사업 영향** — 오타나 폐기된 PR 링크가 근거로 남아도 검사는 초록입니다. 문서 신뢰도 저하 수준이며 강제 장치를 무력화하지는 않습니다.

---

## 반증 기록 — 깨려다 실패한 것 (모두 PASS 쪽 증거)

| 공격 | 방법 | 결과 |
|---|---|---|
| 상태 과장 ①: 대시보드가 실은 운영 연결 아닌가 | `shadow_server.py` 실제 바인딩·라우트 대조 | 깨지 못했습니다. `:29 SAFE_HOSTS={"127.0.0.1","localhost"}`(허용 호스트 정의 줄), `:293 --host default="127.0.0.1"`(기본 바인딩 줄), `:303 "LOCAL SHADOW · 운영 아님"`(사용자에게 비운영을 알리는 출력 줄). `local_runtime` 표기가 정확합니다. |
| 상태 과장 ②: 인증 분류기에 실제 제품 소비자가 있지 않은가 | `classify_auth_surface` 저장소 전역 검색(.venv 제외) | 깨지 못했습니다. 히트는 구현(`auth_surface.py:64` 함수 정의 줄), 패키지 공개(`__init__.py:8,18` 재수출 줄), 시험(`tests/test_auth_surface.py`), 문서뿐입니다. 비시험 호출자 0건 → `library_only` 정확합니다. |
| 상태 과장 ③: 브라우저 자동화가 실은 구현돼 있지 않은가 | `humansearch/src/**/*.py` 전량 열거 | 깨지 못했습니다. 파일은 `__init__.py`, `auth_surface.py`, `admin_weekly_dashboard/{__init__,contracts,shadow_server,snapshot,weekly_window}.py` 7개뿐이고 브라우저·포털 어댑터가 없습니다. `contract_only`/`not_connected` 정확합니다. |
| 제품 기능 누락 | 위 7개 파일이 두 제품 기능(대시보드·인증분류)으로 남김없이 귀속되는지 대조 | 깨지 못했습니다. 제품 코드 쪽 누락은 0건입니다. |
| 진입점 허위 | 문서가 적은 심볼·경로를 코드에서 확인 | 깨지 못했습니다. `shadow_server.py:289 def main`, `:313 if __name__ == "__main__"`(CLI 실행 줄), `:214 /api/dashboard`, `:217 /healthz`, `:193-194 /styles.css·/app.js`, `apps/admin/app.js:132 async function loadDashboard`, `:155 loadDashboard()`(호출 줄) 전부 실재합니다. |
| 필수 키 삭제 반례가 통과하는가 | `check-docs-sot.sh` 정적 추적 | 거부됩니다. `:217-219`가 `REQUIRED_FEATURE_KEYS`(:61-79, 필수 17키 집합) 차집합을 계산해 비지 않으면 `ValueError` → `:273-275`가 종료값 1. `purpose`는 `:224`에서 빈 문자열까지 별도 거부됩니다. |
| 기능 문서 0개 반례가 통과하는가 | 같은 방법 | 거부됩니다. 문서만 지우면 `:199-207`이 `actual_documents`(실제 `*.yaml` 집합)와 `catalog_documents` 불일치로 `catalog/document mismatch`를 냅니다. 카탈로그 `features`까지 비우면 그 전에 `:147-148`이 `catalog features must be non-empty`로 막습니다. 상수 대조(:186)까지 있어 삼중입니다. |
| 중복 ID가 통과하는가 | 같은 방법 | 거부됩니다. 카탈로그 내 중복은 `:172-173`, 문서 내 JSON 중복 키는 `:96-102 reject_duplicate_keys`(중복 키를 예외로 바꾸는 훅), 불변식 ID 중복은 `:256-259`가 막습니다. |
| 없는 근거 경로가 통과하는가 | 같은 방법 | 저장소 상대 경로에 대해서는 거부됩니다(`:131-132` 존재 확인 줄). 단 URL은 D-3대로 예외입니다. 앵커(`#입력` 등)는 `:115`가 `#` 앞부분만 잘라 파일 존재를 봅니다 — 앵커 자체는 미검증이나 문서가 그렇게 주장하지도 않습니다. |
| 경로 탈출로 위조 근거 통과 | `..`·절대경로 시도 가능성 확인 | 막혀 있습니다. `:117-118`이 절대경로와 `..`을 거부합니다. |
| 정본 이중화(같은 규칙 두 곳 기재) | 여섯 문서와 기존 정본 대조 | 깨지 못했습니다. 결정표·브라우저 허용 조건은 복제되지 않고 `authority.delegates`로 `humansearch-l0-surface-contract.md`, `humansearch-browser-contract.md`, `metric-contract-v1.json`을 가리키기만 합니다. AC-3은 충족됩니다. |
| 소유권 충돌 | 기존 SOT 7개와 신규 6개의 `owns` 범위 대조 | 충돌을 찾지 못했습니다. 신규 문서는 `feature_status`/`runtime_boundary`/`control_entrypoints` 계열만 소유합니다. |
| 개인정보·비밀 복사 | 여섯 문서 + 카탈로그 전문 육안 확인 | 없습니다. 후보자 정보, 토큰, 실제 자격증명, 무시된 증거 본문 인용 0건입니다. |
| 미연결 사실 은폐 | 검사 스크립트의 배선 여부 확인 | 은폐가 아니라 자인입니다. `catalog.yaml:121`(수동 검사임을 known_gaps에 명시한 줄), `verification-commands.md:81`(같은 사실을 정본에 적은 줄), `check-docs-sot.sh:10-11`(비범위 선언 줄) 세 곳이 일치합니다. pre-push 글로브(`hooks/pre-push:122` 검사 수집 줄)는 `verify.sh`와 `acceptance-*.sh`만 잡으므로 `check-docs-sot.sh`가 실제로 안 도는 것도 확인됩니다. |

## FAIL을 해소하려면

1. `contracts/cleanroom-deny-patterns.txt`를 위임 대상으로 삼는 클린룸 경계 기능, 전역 Strict 스킬 잠금 기능, 억제 만료 기능을 `engineering_assurance`에 추가하거나 — 기존 세 기능에 흡수시킬 경우 해당 문서의 `entrypoints`·`evidence`·`invariants`에 위 `file:line`들을 명시적으로 넣으십시오. 언급 없는 흡수는 위임이 아닙니다.
2. `scripts/check-docs-sot.sh:86-93`의 상수 대조를 귀속 대조로 교체하십시오. 최소 형태는 "`.github/workflows/verify.yml`의 실행 줄에 등장하는 각 스크립트 경로가 어느 기능 문서의 `entrypoints`/`evidence`에도 없으면 실패"입니다. 이것이 있었으면 D-1이 자동으로 잡혔습니다.
3. `docs/sot/verification-commands.md:72-74`에 URL 근거는 존재 검증 대상이 아니라는 예외를 한 문장 추가하십시오.
4. 세 명령(`check-docs-sot.sh`, `pytest -q`, `git diff --check`)은 제 환경에서 실행 권한이 없어 미검증으로 남았습니다. 실행 허가를 주시면 그 부분만 이어서 확인하겠습니다.
