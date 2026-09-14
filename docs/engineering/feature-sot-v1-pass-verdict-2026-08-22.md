# Claude V1-C 적대검증 원문 — PASS

- 실행 신원: Claude Code 2.1.238
- 세션: `439ce87b-e8ba-4857-bb35-ee566c854d59`
- 인증 환경: `ANTHROPIC_API_KEY=UNSET`
- 모드: `--safe-mode --dangerously-skip-permissions --permission-mode bypassPermissions --tools Bash,Read,Grep,Glob --effort medium`
- 종료값: `0`
- 실행 전후 상태 SHA-256: `5082437fb182072173836bf20adfba3f1c676b8874cfc091d325722cc6f96f61`
- 실행 전후 산출물 SHA-256: `8003a9a4fdec33c99f9077d1019af69f2549f180567f8712be6eaca66290bdce`

## 원문

VERDICT: PASS

## 건너뜀·미확인·추정 (판정 앞 선언)

- 저장소 파일은 하나도 고치지 않았습니다. 변이 실험은 전부 작업트리 사본(`rsync` → `/tmp/vh_mut`, 별도 `git init`)에서만 했고 종료 후 삭제했습니다. 세션 종료 시점 `git status --porcelain`이 시작 시점과 동일함을 확인했습니다.
- 지시대로 세 명령만 실행했고, 그 밖에 짧은 판정기 두 개(`scripts/verify/check-mechanism-registry.sh`, `scripts/verify/check-ci-step-integrity.sh`)만 추가로 돌렸습니다. `verify.sh`·pre-push 전량 번들·CI 실행은 돌리지 않았습니다.
- **원격 main 브랜치 보호는 확인하지 않았습니다.** 이는 카탈로그가 `known_gaps`에 스스로 적어 둔 미검증 항목이므로 은폐가 아니라 자인으로 취급했습니다.
- `docs/sot/features/`와 goal 문서는 아직 **git에 추적되지 않은 상태**(`??`)입니다. 판정은 작업트리 기준입니다.

---

## 결론

이전 실패의 세 가지 지적이 모두 실제로 고쳐졌습니다.

빠져 있던 강제 장치 세 가지(옛 저장소 이름 차단, 전역 지침 파일 잠금, 억제 기한 만료 검사)는 이제 각각 담당 기능 문서 안에 이름·호출 경로·불변조건·근거 파일까지 붙어 들어갔습니다. 이름만 적어 놓고 실제 배선이 없는 자리는 찾지 못했습니다.

기능 이름 6개를 검사 코드 안에 상수로 박아 두던 방식은 사라졌습니다. 지금은 저장소에서 제품 파일 11개, CI 단계 23개, CI가 언급하는 명령 29개, 훅 2개, 계약 문서 2개를 **직접 세어 와서** 문서가 적어 놓은 목록과 한 글자씩 맞춰 봅니다. 그래서 하나라도 빠지거나 두 기능이 같은 것을 가져가면 그 자리에서 빨간불이 납니다. 저는 이걸 열 가지 방식으로 깨려 했고 전부 막혔습니다. 실제 새 제품 파일을 동반한 일곱 번째 기능은 검사 코드를 한 줄도 안 고치고 추가되어 통과했습니다.

지시한 세 명령은 모두 통과했습니다(구조 검사 종료값 0, 시험 64개 전부 통과, 공백 오류 0건).

남은 문제는 세 가지인데 전부 심각도 낮음이고, 계약을 어기지는 않습니다. 하나는 CI 단계를 평범하지 않은 형식으로 일부러 적으면 귀속 검사를 피해 갈 수 있다는 점, 나머지 둘은 문서 안의 숫자와 날짜가 최신 상태보다 하루 뒤처져 있다는 점입니다.

---

## 판단 근거

**선택한 해석** — T 계약이 요구한 것은 "지금 HEAD의 기능이 빠짐없이, 과장 없이, 정확히 한 번씩 귀속되는가"이고, 그 완전성이 **사람의 선언이 아니라 저장소에서 유도된 기준**으로 강제되는가입니다. 그래서 저는 카탈로그를 읽고 믿는 대신, 다섯 종류 표면을 제 손으로 독립 수집한 뒤 문서와 집합 비교했습니다. 이 방식이 틀리면(=제 수집 규칙이 검사 코드와 같은 맹점을 공유하면) 제 PASS도 같이 깨집니다. 그 위험을 줄이려고 `.github/workflows/verify.yml`의 `- name:` 줄을 검사 코드 정규식과 **다른 방식**(들여쓰기 무관 grep)으로도 세어 23개가 동일함을 따로 확인했고, YAML 파서로 파싱되는 형태의 회피형 스텝까지 별도로 주입해 봤습니다.

**버린 해석 1 — "귀속은 됐지만 이름만 옮겨 적은 것 아닌가"** — 이 가능성을 D-1 세 장치 각각에 대해 검사했고 기각했습니다. 클린룸은 이름(`ci_steps`)만이 아니라 위임 대상(`contracts/cleanroom-deny-patterns.txt`), 진입점(`kind: cleanroom_boundary`, `path`+`contract`+`ci_anchor`), 불변조건 `CDG-INV-6`, 근거 9개 경로까지 들어갔습니다. 전역 스킬 잠금은 잠금 본체·판정기·인수 시험 세 파일이 전부 진입점으로 들어갔고 억제 만료는 `suppressions.yaml`을 계약으로 지정합니다. 그리고 이 근거 경로들은 검사가 **실제 존재를 확인**하므로 빈 이름은 통과하지 못합니다.

**버린 해석 2 — "일곱 번째 기능 추가 가능 주장은 goal 문서의 자기 보고일 뿐"** — goal의 출력 블록을 인용만 하지 않고, 새 제품 파일 `apps/reports/report.js`를 실제로 만들고 카탈로그·기능 문서·`product_roots`만 손대서 재현했습니다. `git diff --stat HEAD -- scripts/check-docs-sot.sh`가 비어 있는 상태로 `features=7 product_files=12`로 통과했습니다.

**버린 해석 3 — "회피형 CI 스텝 우회는 곧 FAIL 사유"** — 기각했습니다. 그 우회는 (a) `name:`을 `- ` 줄이 아닌 둘째 줄에 쓰고 (b) 그 스텝이 어떤 저장소 스크립트 경로도 부르지 않아야만 성립합니다. 스크립트를 부르는 순간 `ci_command_paths` 대조에서 잡힙니다(M4로 확인). 즉 정직하게 작성된 변경에서는 미귀속 CI 단계가 반드시 실패하며, T가 요구한 "미귀속 CI 단계는 실패해야 한다"는 충족됩니다. 다만 의도적 은폐에는 열려 있으므로 설계 지적으로 남깁니다.

**제가 틀리면 깨지는 것** — 만약 `coverage.product_roots`·`control_roots` 자체가 좁게 잡혀 있어 그 밖에 실제 제품/제어 표면이 있다면, 제 "빠짐없음" 판단은 무너집니다. 그래서 `git ls-files apps contracts`, `git ls-files humansearch/src`, `ls hooks/`, `ls docs/sot/humansearch-*-contract.md`로 뿌리 밖까지 훑었고 `.github/workflows/verify.yml`이 단일 job임을 확인했습니다. 제품 표면 밖으로 새는 파일은 찾지 못했습니다.

---

## 기술 상세와 증거 원문

### 1. 지시한 세 명령 — 실행 결과

```text
$ bash scripts/check-docs-sot.sh
PASS: docs/sot/INDEX.md 존재, 1863바이트 (<=20000)
… (필수 파일 7개 전부 PASS)
PASS: feature SOT structure catalog=1 features=6 categories=3 invariants=32
      product_files=11 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2 paths=validated
PASS: hooks/pre-commit … (계약 참조 5개 전부 PASS)
OK: docs/sot 재구성 AC 전부 충족
EXIT=0
```
→ 검사 항목은 필수 파일 7건 + 구조 1건 + 계약 참조 5건 = **13건**이고 전부 PASS, 종료값 0입니다. `features=6`은 카탈로그 기능 수, 뒤의 숫자들은 저장소에서 유도한 표면 개수입니다.

```text
$ cd humansearch && uv run --no-sync pytest -q
................................................................ [100%]
64 passed in 7.94s
EXIT=0
```
→ 시험 **64개** 전부 통과, 종료값 0입니다. 0개 통과(빈 수집)가 아님을 개수로 확인했습니다.

```text
$ git diff --check
EXIT=0
```
→ 공백 오류·충돌 표식 0건입니다.

### 2. D-1/D-2/D-3 재현 시도 — 셋 다 해소됨

**D-1(분류 누락 3건) → 해소.** 이전 판정이 "기능 폴더 전체에 문자열 0건"이라고 적었던 세 장치가 지금은 이렇게 들어가 있습니다.

```text
docs/sot/features/engineering/change-delivery-guardrails.yaml:37   "HumanSearch G1 클린룸 경계"        ← CI 단계 귀속 줄
docs/sot/features/engineering/change-delivery-guardrails.yaml:46-55 클린룸 8종 스크립트 경로 귀속 줄
docs/sot/features/engineering/change-delivery-guardrails.yaml:101   "kind": "cleanroom_boundary"      ← 진입점 선언 줄
docs/sot/features/engineering/change-delivery-guardrails.yaml:197   "id": "CDG-INV-6"                 ← 클린룸 불변조건 줄
docs/sot/features/engineering/verification-evidence-system.yaml:98  "global_strict_skill_lock"        ← 전역 스킬 잠금 진입점 줄
docs/sot/features/engineering/verification-evidence-system.yaml:172 잠금·검사·해제 전이 불변조건 줄
docs/sot/features/engineering/repository-data-protection.yaml:37    "억제 만료 스캔 (suppressions.yaml)" ← CI 단계 귀속 줄
docs/sot/features/engineering/repository-data-protection.yaml:82    "contract": "suppressions.yaml"   ← 계약 파일 지정 줄
```
→ 세 장치가 각각 담당 기능의 표면 장부·진입점·불변조건에 동시에 들어갔습니다. 그리고 이 경로들은 검사가 존재를 강제하므로 빈 문자열 귀속이 불가능합니다.

**D-2(기능 6개 상수) → 해소.** `EXPECTED_FEATURE_IDS`/`EXPECTED_CATEGORY_IDS` 문자열 검색 0건입니다. 대체된 자리는 다음입니다.

```text
scripts/check-docs-sot.sh:286-298  git ls-files 로 제품 파일 실집합을 만드는 줄
scripts/check-docs-sot.sh:302-311  verify.yml 에서 CI 단계·명령 경로를 뽑는 줄
scripts/check-docs-sot.sh:313-319  hooks/ 와 humansearch-*-contract.md 를 훑는 줄
scripts/check-docs-sot.sh:327-332  다섯 표면의 실집합 vs 귀속집합을 대칭 비교해 missing/extra 를 내는 줄
```
→ 완전성 기준이 코드 안 상수에서 저장소 실제 상태로 옮겨졌습니다. `claim_surface`(:198-212)가 중복 귀속을, :205-206이 범주 위반을, :253-254가 표면 0개 기능을 각각 막습니다.

**D-3(URL 무검증) → 해소.**
```text
scripts/check-docs-sot.sh:109-110  if value.startswith(("http://","https://")): raise ValueError(…)
```
→ 예외 통과 분기가 **거부 분기로 뒤집혔습니다.** 기능 폴더 전체에 `http` 문자열은 `admin-weekly-dashboard.yaml:58`의 `"kind": "http"`(진입점 종류 이름) 1건뿐이고 URL 근거는 0건입니다. 정본 문구도 맞춰졌습니다 — `docs/sot/verification-commands.md:74`(외부 URL은 근거 경로로 허용하지 않는다고 적은 줄).

### 3. 표면 독립 수집 대조 — 전량 일치

| 표면 | 제가 독립 수집한 값 | 검사가 보고한 값 | 귀속처 |
|---|---:|---:|---|
| 추적 제품 파일 | 11 (`apps/admin` 3, `contracts/admin-weekly-dashboard` 1, `humansearch/src` 7) | 11 | 대시보드 9, 인증분류 2 |
| 이름 있는 CI 단계 | 23 (`grep -n -- "- name:"`, 전부 6칸 들여쓰기, 단일 job) | 23 | 보호 9, 검증 10, 전달 4 |
| CI가 언급하는 명령 | 29, 모두 실재(`exists()==True`) | 29 | 보호 6, 검증 13, 전달 10 |
| 훅 | 2 (`hooks/pre-commit`, `hooks/pre-push`) | 2 | 보호 1, 전달 1 |
| HumanSearch 계약 | 2 (`humansearch-{browser,l0-surface}-contract.md`) | 2 | 브라우저 1, 인증분류 1 |

→ 다섯 줄 모두 제 수집값과 검사 보고값이 같고, 귀속 합계도 총계와 같습니다. 누락·중복 0건입니다.

**"이름만 있고 배선 없는 귀속" 공격 결과 — 전부 실패:**
- 각 기능의 `verification.command`에 적힌 파일 경로 16개를 전수 확인했습니다. 전부 실재합니다(`cd humansearch` 뒤 상대경로인 `tests/test_*.py` 8개 포함, `ls humansearch/tests/`로 확인). 표본으로 `HAS-V1`을 실제 실행해 25 passed를 받았습니다.
- `humansearch/src/humansearch/__init__.py`를 인증분류 기능이 가져간 것이 옳은지 파일을 열어 확인했습니다. `from .auth_surface import (…)` 재수출만 있고 대시보드 심볼은 없습니다 → 귀속 정확합니다.
- 대시보드의 `local_runtime` 표기를 깨려 했으나 실패했습니다. `shadow_server.py:29 SAFE_HOSTS={"127.0.0.1","localhost"}`(허용 호스트 정의 줄), `:173 if host not in SAFE_HOSTS`(거부 줄), `:293 --host default="127.0.0.1"`(기본 바인딩 줄), `:303 "LOCAL SHADOW · 운영 아님"`(비운영 고지 줄). 과장 없습니다.
- 파일 형식 주장("YAML 1.2와 JSON 양쪽에서 읽힌다")을 Ruby Psych로 검증했습니다. `catalog.yaml`과 기능 문서가 YAML 파서로도 정상 로드됩니다 → 주장 사실입니다.
- 비밀·개인정보 스캔: 기능 폴더 전체에서 토큰·비밀번호·이메일·전화번호 패턴 실값 0건. 히트는 전부 `"secret_patterns"` 같은 **검사 대상의 이름**입니다.

### 4. 변이 대조 — 요구된 실패가 전부 실패함 (작업트리 사본에서)

```text
M1 필수키(invariants) 삭제           EXIT=1  required keys missing in …: ['invariants']
M2 기능 문서 전량 삭제               EXIT=1  catalog document for admin-weekly-dashboard does not exist
M3 미귀속 CI 스텝 추가               EXIT=1  ci_steps ownership mismatch missing=['몰래 추가한 스텝']
M4 미귀속 CI 명령 추가               EXIT=1  ci_command_paths ownership mismatch missing=['scripts/newthing.sh', …]
M5 URL 근거 추가                     EXIT=1  external URL is not permitted as repository evidence
M6 훅을 두 기능에 중복 귀속          EXIT=1  duplicate hooks surface: hooks/pre-push (change-delivery-…, verification-…)
M7 제품 파일을 저장소보증에 귀속     EXIT=1  product file assigned to engineering_assurance
N1 미귀속 신규 제품 파일             EXIT=1  tracked_product_files ownership mismatch missing=['apps/admin/new.js']
N2 표면 0개 기능                     EXIT=1  feature owns no derived repository surface
N3 CI 스텝 이름 전멸(중복화)         EXIT=1  CI named steps must be unique for feature ownership
N4 카탈로그 features 비움            EXIT=1  catalog features must be non-empty
N5 verification 비움                 EXIT=1  …verification must be a non-empty array
N6 존재하지 않는 근거 경로           EXIT=1  evidence for change-delivery-guardrails does not exist: scripts/nope.sh
N7 카탈로그-문서 상태 불일치         EXIT=1  catalog mismatch for change-delivery-guardrails.maturity
M8 실제 새 제품 표면 + 7번째 기능    EXIT=0  features=7 … product_files=12  (검사 코드 diff 0줄)
```
→ T가 "실패해야 한다"고 못박은 항목(필수 키 삭제, 기능 문서 0개, 미귀속 CI 단계/명령, 검사 대상 0개, 중복 귀속)이 **전부 종료값 1**이고, "가능해야 한다"고 한 7번째 기능 확장만 종료값 0입니다.

**goal 문서와의 양쪽 대조** — `docs/engineering/feature-sot-catalog-goal-2026-08-21.md:419-431`(변이 스위트 출력 블록)이 주장하는 `mutation unmapped-ci-step rejected (exit=1)`, `unmapped-ci-command rejected (exit=1)`, `seventh feature … accepted`를 제가 M3·M4·M8로 독립 재현했고 결과가 일치합니다. `:406`이 적은 `features=6 … ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2`도 제 실행 출력과 문자 단위로 같습니다. 자기 보고가 부풀려진 자리를 찾지 못했습니다.

---

## 결함 (전부 심각도 낮음 — PASS를 뒤집지 않음)

### F-1 · 심각도: 낮음 — "미귀속 CI 단계 실패" 강제가 스텝 표기 형식에 의존한다 (설계 지적)

```text
scripts/check-docs-sot.sh:302  ci_step_list = re.findall(r"^      - name: (.+)$", workflow_text, flags=re.MULTILINE)
```
→ CI 단계 이름을 "6칸 들여쓰기 + `- name:`"으로 시작하는 줄에서만 뽑는 자리입니다.

재현(작업트리 사본):
```yaml
      - run: echo '조용히 추가된 게이트'
        name: 회피형 스텝
```
```text
$ bash scripts/check-docs-sot.sh
PASS: feature SOT structure … ci_steps=23 …
EXIT=0
$ ruby -ryaml …   → 파서가 본 스텝 이름: ["a", "evasive"]   ← 유효한 GitHub Actions 스텝
$ bash scripts/verify/check-ci-step-integrity.sh .github/workflows/verify.yml
PASS: 조건부·오류무시 스텝 없음 (job·step 26개 검사)   ← 정상 파일에서는 25개
```
→ 같은 저장소의 다른 판정기는 Psych로 YAML을 파싱해 이 스텝을 **26번째로 세었는데**, 구조 검사는 여전히 23으로 세고 통과시킵니다. 즉 이름 있는 CI 단계 하나가 아무 기능에도 귀속되지 않은 채 초록불이 됩니다.

- **무엇을** — CI 단계 완전성을 YAML 구조가 아니라 텍스트 정규식으로 유도합니다.
- **왜** — 외부 YAML 패키지 없이 Python 표준 라이브러리만 쓰겠다는 제약(:48 주석)에서 나온 선택으로 보이며, 그 제약 자체는 정당합니다.
- **버린 길** — 이미 저장소에 있는 `scripts/verify/check-ci-step-integrity.sh:26-68`의 Ruby Psych 열거를 재사용해 스텝 이름 목록을 받아오는 길을 택하지 않았습니다. 그 길이었다면 표기 형식과 무관해집니다.
- **대가** — 우회에는 (a) `name:`을 둘째 줄에 두고 (b) 어떤 저장소 스크립트 경로도 부르지 않는 두 조건이 동시에 필요합니다. 스크립트를 부르면 `ci_command_paths` 대조(M4)에서 잡히므로, 실제 위험은 인라인 셸만 쓰는 은폐 스텝에 한정됩니다.
- **되돌리기** — :302 한 줄을 Psych 열거 호출로 바꾸면 되고, 기능 문서·카탈로그는 그대로입니다.

**사업 영향** — 정직한 변경에서는 발생하지 않습니다. 다만 "검사를 조용히 끄는 것을 막는다"가 이 저장소의 반복 주제(P23·P24, 커밋 #35)인 만큼, 그 방어선에 형식 의존 틈이 남아 있습니다.

### F-2 · 심각도: 낮음 — 기능 개수 6이 정본 산문에 상수로 남아 있다

```text
docs/sot/INDEX.md:6  - [features/catalog.yaml](features/catalog.yaml) — 주요 기능 6개의 범주와 상태를 기계가 읽는 카탈로그
```
→ SOT 진입점이 기능 수를 문장 안에 고정한 줄입니다.

**원인** — D-2를 코드에서는 제거했으나 문서 산문에 같은 성격의 숫자가 남았습니다. 제 M8 실험에서 기능이 7개가 되어도 이 줄은 검사되지 않으므로 조용히 거짓이 됩니다(`features/INDEX.md`에는 개수 고정이 없어 그쪽은 문제없습니다). **사업 영향** — 다음 세션이 진입점만 읽고 기능 수를 오인할 수 있는 수준이며, 강제 장치를 무력화하지는 않습니다.

### F-3 · 심각도: 낮음 — 정본의 변이 실행 기록이 최종 상태보다 하루 뒤처져 있다

```text
docs/sot/verification-commands.md:3   최종 갱신: 2026-08-21 (기능 정본 구조 검사 추가; …)
docs/sot/verification-commands.md:82-83  정상 사본과 네 고장 사본을 2026-08-21에 격리 실행해 정상만 종료값 0임을 확인했다.
```
→ 검사의 검증 이력을 적은 줄입니다. 실제로는 2026-08-22에 D-1~D-3을 고치면서 변이가 6종 + 7번째 기능 확장으로 늘었고(goal `:419-431`), 카탈로그 `updated_at`과 `features/INDEX.md`는 2026-08-22입니다.

**원인** — 기능 문서 쪽 날짜는 갱신했으나 기존 SOT의 이력 문장은 그대로 두었습니다. 문장 자체는 과거 사실로서 거짓은 아니지만 현재 보장 범위를 실제보다 **작게** 보고합니다(과장이 아니라 과소 보고입니다). **사업 영향** — 문서 신뢰도 수준이며 판정에 영향을 주지 않습니다.

---

## 반증 기록 — 깨려다 실패한 것

| 공격 | 방법 | 결과 |
|---|---|---|
| D-1 재현: 세 장치가 여전히 빠졌는가 | 기능 폴더 전수 grep + 진입점/불변식/근거 확인 | 실패. 세 장치 모두 이름·경로·불변조건·근거로 귀속됨 |
| D-2 재현: 기능 ID 상수가 남았는가 | `EXPECTED_*` 검색 + 7번째 기능 실제 추가 | 실패. 상수 0건, 검사 코드 무수정으로 `features=7` 통과 |
| D-3 재현: URL 근거가 통과하는가 | URL 근거 주입(M5) | 실패. `external URL is not permitted`로 exit 1 |
| 표면 누락: 검사가 못 보는 제품/제어 표면 | `git ls-files apps contracts humansearch/src`, `ls hooks/`, 계약 glob, verify.yml 단일 job 확인 | 실패. 다섯 표면 개수가 검사 보고와 전부 일치 |
| 이름뿐인 귀속 | verification 명령 16개의 경로 실재 전수 확인 + 표본 실행 | 실패. 전부 실재, 표본 25 passed |
| 근거 경로 위조 | 없는 경로(N6)·절대경로·`..` 시도 | 실패. `:113-114`가 절대경로와 `..`을 거부, `:122-123`이 존재를 강제 |
| 범주 경계 무시 | 제품 파일을 저장소보증에(M7), 제어 표면을 제품에 | 실패. `:205-208`이 양방향으로 거부 |
| 중복 귀속 | 훅 하나를 두 기능이 소유(M6) | 실패. `duplicate hooks surface` + 소유자 두 명 이름 출력 |
| 상태 과장 | 대시보드 `local_runtime`, 인증분류 `library_only`, 브라우저 `contract_only` 재확인 | 실패. 바인딩·호출자·소스 파일 목록이 표기와 일치 |
| 검사 대상 0개 | 기능이 표면 0개 소유(N2), 카탈로그 features 비움(N4), verification 비움(N5) | 실패. 세 경우 모두 exit 1 |
| 기존 SOT 소유권 충돌 | `authority.owns`/`delegates` vs `docs/sot/*` 대조, `check-mechanism-registry.sh` 실행 | 실패. 충돌 없음, 명부 검사 `CHECKED: 13` exit 0 |
| 비밀·개인정보 유입 | 기능 폴더 전체 패턴 스캔 | 실패. 실값 0건 |
| CI 스텝 형식 우회 | `name:`을 둘째 줄에 둔 인라인 스텝 주입 | **성공(F-1)**. 단 스크립트 경로를 부르면 M4에서 잡힘 |

## 조건 없는 결론

T 계약이 요구한 필수 실패 6종과 필수 성공 1종이 모두 재현되고, 이전 판정의 D-1·D-2·D-3이 실제 파일에서 해소됐으므로 **PASS**입니다. F-1은 다음 변경에서 `:302`를 YAML 파서 열거로 교체하는 것을 권고하고, F-2·F-3은 문장 두 줄 수정으로 끝납니다. 세 항목 모두 이번 인수를 막을 사유는 아닙니다.
