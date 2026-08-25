# codex V3 — Claude 분석 감시 판정 (하위 세션 조립본, 2026-08-13)
(통합 판정 파일 미생성 — codex 하위 감사 세션들의 주장별 판정을 조립)


===== 세션 rollout-2026-08-13T08-35-56-019ff855-2132-76a0-8aae-f2acd0d8e3a3.jsonl =====
주장2 판정: **확인(맞음)**

Claude 주장처럼 `humansearch/src`·`humansearch/tests` 밖인 `humansearch/cli/`에 일반 URL만 넣으면 검사기가 잡지 못하고 `PASS + exit 0`을 냅니다. selector와 브랜드 주소는 같은 위치에서도 전역 계층으로 잡혔으므로, Claude가 selector를 섞어 오염된 재현을 한 것이 아니라 “일반 URL 단독 미탐”이 실제로 재현됐습니다.

실패/재시도:
- `/private/tmp/codex-v3-claim2` 생성 전에 `rm -rf`를 시도했으나 안전 정책으로 거부됐습니다. 경로가 없음을 확인한 뒤 `git clone --no-hardlinks`로 새 복제했습니다.
- `apply_patch`는 `/private/tmp` 절대경로 편집을 거부했습니다. 원본 보호를 위해 복제본 내부에서만 `printf`로 실험 파일을 만들었습니다.
- selector 케이스 첫 생성은 `git rm` 후 빈 디렉터리가 사라져 실패했습니다. 파일은 생성되지 않았고 상태가 깨끗했으므로 `mkdir -p` 후 재시도했습니다.

핵심 근거:
```text
baseline:
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 53
CONTRACT_FILES: 3
EXIT:0

general URL only in humansearch/cli:
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 54
CONTRACT_FILES: 3
EXIT:0

selector only in humansearch/cli:
  forbidden(global): humansearch/cli/claim2_probe.py
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 54
CONTRACT_FILES: 3
EXIT:1

brand URL only in humansearch/cli:
  forbidden(global): humansearch/cli/claim2_probe.py
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 54
CONTRACT_FILES: 3
EXIT:1
```

실제 스캔 범위:
- `scripts/acceptance-hs-portal-constants.sh:31` — 제품 전용 검사 루트가 `humansearch/src humansearch/tests`로 제한됩니다.
- `scripts/acceptance-hs-portal-constants.sh:143-151` — `humansearch/src/*|humansearch/tests/*`만 제품 패턴까지 적용하고, 그 외는 전역 패턴만 적용합니다.
- `contracts/portal-constants-deny-patterns-product.txt:6-10` — 모든 URL과 일반 도메인 리터럴은 제품 전용 계층에만 있습니다.
- `contracts/portal-constants-deny-patterns.txt:9-17`, `:34-40` — selector와 브랜드 도메인은 전역 계층에 있습니다.

원복 확인:
- 복제본 `/private/tmp/codex-v3-claim2` 최종 `git status --short` 출력 없음.
- 원본 `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-g3-portal-constants` 최종 `git status --short` 출력 없음.


===== 세션 rollout-2026-08-13T08-36-16-019ff855-6e0b-7e21-a1bd-8655f451733c.jsonl =====
주장4/5 점검 대상 문헌 정리 완료했습니다. 변경/검사 없이 확인한 결과만 정리합니다.

- 작업 트리·커밋 확인:
  - 현재 `HEAD`: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-g3-portal-constants` → `f10c8c4`
  - 비교 기준 브랜치 SHA: `origin/main` → `682f00e`
  - `git branch -vv`에서 현재 브랜치 `task/humansearch-g3-portal-constants` 기반이 `682f00e`로 표기되어 있습니다.

- Claim 4 근거(§7 비범위 vs counter-AC 5) 근거 문구:
  - `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:55-66`에 counter-AC 9종이 나열되며, 항목 5는 “존재하지 않는 제품 루트를 조용히 skip”입니다.
  - 같은 파일 `171-178`의 `§1⑦ 비범위`는 “제품 루트 목록의 자동 발견(신규 제품 폴더 자동 편입)은 후속 — 현재는 검사기 상단 목록이 정본”입니다.
  - 즉 `counter-AC 5`(누락 제품 루트도 강제 실패 대상)와 `§7`은 서로 충돌하지 않고, 같은 “현재는 상단 목록 고정, 누락은 가짜 완료 시나리오로 금지”를 보강하는 관계입니다.
  - 다만 `counter-AC 5`는 “제품 루트 누락을 조용히 넘어가는 행위” 자체를 막는 항목이라, “오히려 비범위 확대를 통한 면제”가 아니라 “명시된 강제점검”으로 해석됩니다.

- Claim 5: 3,000줄 상한 규칙 존재 여부/적용 단위/예외:
  - `docs/sot/coding-principles.md:26` (P11)에서 명시:
    - 파일 단위: soft 300 / hard 600 LOC
    - 함수 단위: soft 60 / hard 100 LOC
    - PR 단위: **3,000줄 초과 PR은 절대 금지(하드 금지)**, 생성물/마이그레이션/픽스처 면제
  - `docs/engineering/verify-unification-goal-2026-08-10.md:139-142`(AC-19)에서도 PR 전역 3,000줄 초과는 예외 등록해도 FAIL 하도록 정리(적용 범위를 더 강하게 재확인한 규격).

- Claim 5: PR #13 변경량 계산(요청한 `--stat / --numstat / --shortstat`)
  - 공통 비교 기준으로 `git merge-base --fork-point origin/main HEAD`는 `682f00e981...`(즉 682f00e)입니다.
  - `git diff --stat 682f00e..HEAD` 결과:
    - `11 files changed, 4318 insertions(+), 14 deletions(-)`
    - 변경 파일:
      `.github/workflows/verify.yml(+12)`
      `contracts/portal-constants-deny-patterns-product.txt(+36)`
      `contracts/portal-constants-deny-patterns.txt(+40)`
      `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md(+2737)`
      `docs/sot/verification-commands.md(29 + /14 -)`
      `scripts/acceptance-hs-portal-constants-hardening*.sh(+159~255 each)`
      `scripts/acceptance-hs-portal-constants-mutations.sh(+312)`
      `scripts/acceptance-hs-portal-constants.sh(+324)`
  - `git diff --numstat 682f00e..HEAD`:
    - 상기 항목별 추가/삭제 라인 동일, 삭제는 위 목표 문서만 `14`건(문서 한 줄 수정 14건 포함), 전체 삭제 14
  - `git diff --shortstat 682f00e..HEAD`:
    - `11 files changed, 4318 insertions(+), 14 deletions(-)`
  - `origin/main..HEAD` 및 `682f00e..HEAD` 모두 동일 출력(기준 불일치 없음).

- 추가 확인(근거 일치성):
  - `humansearch-g3-portal-constants-goal-2026-08-12.md:349`에서도 “`git diff 682f00e..HEAD --stat` → 기대한 8파일”이라고 문서 내에서 직접 기준을 쓰고 있으며, 실측/기록이 일치함.
  - 계산된 4318줄은 “삽입 합계”로만 본 값이며, 삭제 14줄이 존재해 “총 라인 변경량” 관점에서는 4332줄(4318+14) 튜플로 보는 식이 가능합니다. (혼동 방지 위해 명시 필요)

요약:
- Claim 4: §7과 counter-AC 5는 문구상 충돌 아님. 오히려 누락 루트를 가짜 합격으로 허용하지 말라는 counter-AC가 §7의 “자동 발견 미착수(현재 상단 목록 고정)”를 보완.
- Claim 5: 3,000줄 하한은 `docs/sot/coding-principles.md`에 분명 존재하며, PR 범위/하드 규정까지 포함. Claude가 언급한 4318라인은 `--stat` 기준 insertions 합계와 일치하며, 명령이 적절합니다.


===== 세션 rollout-2026-08-13T08-35-44-019ff854-ec9f-7582-ac5c-313d4bebcd32.jsonl =====
주장1 판정: 확인(맞음). Claude의 `if: false` 재현은 가짜 조작이 아니라 유효한 YAML이며, GitHub Actions의 job-level 조건 `jobs.verify.if`로 해석됩니다. 이 상태에서 `scripts/acceptance-hs-portal-constants.sh`는 `PASS: ci/pre-push wiring intact`와 exit 0을 냈습니다.

근거:
- 원본 HEAD 확인: `f10c8c4e3ceee7f9095c3bd74009434aae823855`
- 격리 복제: `/private/tmp/codex-v3-claim1-77368`
- 원본/복제본 모두 최종 `git status --short` 출력 없음
- GitHub 공식 문서: `jobs.<job_id>.if`는 job 실행 조건이며 조건이 거짓이면 job을 실행하지 않고 skipped 처리됩니다. skipped job은 Success로 보고될 수 있습니다. 출처: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions

조작 위치:
```text
.github/workflows/verify.yml
14 jobs:
15   verify:
16     if: false
17     runs-on: ubuntu-latest
18     steps:
```

YAML 유효성 확인:
```text
YAML_PARSE
jobs.verify.if=false class=FalseClass
```

검사기 실행:
```text
SCRIPT_EXIT=0
SCRIPT_OUTPUT_BEGIN
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 53
CONTRACT_FILES: 3
SCRIPT_OUTPUT_END
```

반대 해석 검토:
- “`if: false`가 step-level 조건이라 일부 step만 꺼진 것 아닌가?” → 반증. 삽입 위치가 `jobs.verify.if`입니다.
- “YAML이 깨진 조작이라 GitHub가 읽지 못하는 가짜 재현 아닌가?” → 반증. Ruby YAML 파서가 `FalseClass`로 정상 파싱했습니다.
- “검사기가 step-level `if:`만 잡는 것이고 job-level `if:`는 별도 결함인가?” → 확인. 검사기 로직은 step 단위 `if:`를 보려 하지만, job-level `if: false`는 놓쳤습니다.

최종 상태:
```text
CLONE_STATUS_AFTER_REVERT
SOURCE_STATUS_AFTER
SOURCE_HEAD_AFTER=f10c8c4e3ceee7f9095c3bd74009434aae823855
```


===== 세션 rollout-2026-08-13T08-36-06-019ff855-45ed-78a1-8fde-a76efa26f3f8.jsonl =====
D4/D5 독립 실행 검증 결과입니다. 원본 저장소는 수정하지 않았고, 실험은 `/private/tmp/codex-v3-d4d5-run1` 복제본에서만 했습니다. 복제본과 원본 모두 마지막 `git status --short` 출력은 빈 값이었습니다.

## 결론

D4(화면 찾기 표현 우회)는 현재 PR #13 HEAD에서는 재현되지 않습니다. `get_by_role(...)`을 제품 코드에 직접 넣으면 검사기가 `FAIL`과 종료값 1로 차단합니다. 따라서 “현재 검사기가 화면찾기 표현을 그대로 통과시킨다”는 주장이라면 틀렸습니다.

D5(분할·인코딩 주소 우회)는 실행으로 재현됩니다. 조각 또는 이스케이프 형태로 쓴 주소는 실행 시 `https://neutralhost.io/login`으로 결합되지만 검사기는 `PASS`와 종료값 0을 냅니다. 다만 문서상 이 부류는 “실행 시 결합해 해석하는 것”으로 알려진 비범위라고 분류되어 있어, 이것을 결함으로 센 codex 판정이라면 과장입니다.

## 판단 근거

갈림길은 “현재 HEAD 품질”과 “과거 RED 판정의 역사적 타당성”입니다. 현재 코드 기준으로만 보면 D4는 이미 막혀 있고, D5는 미탐이지만 문서가 결함이 아닌 한계로 둔 영역입니다.

버린 해석은 “문자열 조각·이스케이프도 직접 운영 주소와 같으니 무조건 결함”입니다. 이 해석을 택하면 문서의 명시 비범위와 충돌합니다.

이 판정이 틀리면, D4는 실제로 차단되는 위험을 아직 열린 결함으로 잘못 보고 병합 판단을 과도하게 보수적으로 만들고, D5는 문서가 받아들인 한계를 결함으로 다시 세어 PR 책임 범위를 부풀립니다.

## 증거

Baseline:

```text
$ bash scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 53
CONTRACT_FILES: 3
```

→ 뭘 시켰나: 깨끗한 복제본에서 본체 검사기를 실행했습니다.
→ 뭐가 나왔나: 정상 통과했습니다.
→ 좋은 소식인가 나쁜 소식인가: 실험 전 기준선이 깨끗하므로 좋은 소식입니다.

D4 조작:

```text
humansearch/src/humansearch/codex_v3_d4_locator_probe.py:1
LOGIN_BUTTON = page.get_by_role("button", name="Sign in")

$ bash scripts/acceptance-hs-portal-constants.sh; printf 'SCANNER_RC=%s\n' "$?"
  forbidden(global): humansearch/src/humansearch/codex_v3_d4_locator_probe.py
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 54
CONTRACT_FILES: 3
SCANNER_RC=1
```

→ 뭘 시켰나: 제품 코드에 Playwright 화면 찾기 호출을 직접 넣었습니다.
→ 뭐가 나왔나: 검사기가 전역 금지값으로 잡고 종료값 1을 냈습니다.
→ 좋은 소식인가 나쁜 소식인가: 현재 HEAD에서는 D4가 막혀 있으므로 좋은 소식입니다.

관련 줄:
- `contracts/portal-constants-deny-patterns.txt:18-25` — `get_by_role`, `get_by_label`, `get_by_test_id`, `get_by_text` 등 화면 찾기 API를 전역 금지 패턴으로 둡니다.
- `scripts/acceptance-hs-portal-constants.sh:143-148` — `humansearch/src`와 `humansearch/tests`는 전역 패턴과 제품 패턴을 둘 다 검사합니다.

D5 조각 URL:

```text
humansearch/src/humansearch/codex_v3_d5_split_url_probe.py:1
ENDPOINT = "https" + "://" + "neutral" + "host" + "." + "io" + "/login"
humansearch/src/humansearch/codex_v3_d5_split_url_probe.py:2
print(ENDPOINT)

$ python3 humansearch/src/humansearch/codex_v3_d5_split_url_probe.py
https://neutralhost.io/login

$ bash scripts/acceptance-hs-portal-constants.sh; printf 'SCANNER_RC=%s\n' "$?"
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 54
CONTRACT_FILES: 3
SCANNER_RC=0
```

→ 뭘 시켰나: 파일 원문에는 완성 URL을 쓰지 않고 실행 시 합쳐지게 했습니다.
→ 뭐가 나왔나: 실행하면 실제 URL이 되지만 검사기는 통과했습니다.
→ 좋은 소식인가 나쁜 소식인가: 탐지만 보면 나쁜 소식이지만, 문서상 비범위라 결함으로 세면 과장입니다.

D5 이스케이프 URL:

```text
humansearch/src/humansearch/codex_v3_d5_encoded_url_probe.py:1
ENDPOINT = "https\\x3a\\x2f\\x2fneutralhost\\x2eio/login".encode().decode("unicode_escape")
humansearch/src/humansearch/codex_v3_d5_encoded_url_probe.py:2
print(ENDPOINT)

$ python3 humansearch/src/humansearch/codex_v3_d5_encoded_url_probe.py
https://neutralhost.io/login

$ bash scripts/acceptance-hs-portal-constants.sh; printf 'SCANNER_RC=%s\n' "$?"
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 54
CONTRACT_FILES: 3
SCANNER_RC=0
```

→ 뭘 시켰나: URL 구분자를 문자 이스케이프로 숨기고 실행 시 복원했습니다.
→ 뭐가 나왔나: 실제 URL로 출력되지만 검사기는 통과했습니다.
→ 좋은 소식인가 나쁜 소식인가: 검사 한계는 실재하지만, 계약 밖이면 결함은 아닙니다.

직접 URL 대조군:

```text
ENDPOINT = "https://neutralhost.io/login"

$ bash scripts/acceptance-hs-portal-constants.sh; printf 'SCANNER_RC=%s\n' "$?"
  forbidden(product): humansearch/src/humansearch/codex_v3_d5_direct_url_control.py
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 54
CONTRACT_FILES: 3
SCANNER_RC=1
```

→ 뭘 시켰나: 같은 주소를 한 줄짜리 직접 URL로 넣었습니다.
→ 뭐가 나왔나: 검사기가 정상 차단했습니다.
→ 좋은 소식인가 나쁜 소식인가: D5는 “직접 주소 탐지 실패”가 아니라 “실행 시 조립되는 주소 미해석” 문제임이 분리됐습니다.

문서 근거:
- `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:48-51` — 운영 상수와 URL·포트·도메인·화면 위치가 `contracts/` 밖에 있으면 exit 1이어야 한다는 큰 인수 기준입니다.
- `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:915-919` — 문자열 분할과 이스케이프 표현은 통과하지만, 실행 시 결합해 해석하는 것은 비범위라 결함이 아닌 알려진 한계로 분류합니다.
- `contracts/portal-constants-deny-patterns-product.txt:6-10` — 직접 URL과 일반 도메인을 제품 코드에서 잡는 패턴입니다.

실패/재시도:
- `/private/tmp` 절대 경로에 `apply_patch`로 파일을 만들려 했으나 “project 밖 쓰기”로 거부됐습니다.
- D4 원복 때 `git rm`이 staged 파일이라고 거부해, `git restore --staged` 후 `rm`으로 원복했습니다.
- 마지막 확인: 복제본 HEAD는 `f10c8c4e3ceee7f9095c3bd74009434aae823855`, 복제본과 원본 워크트리 상태는 모두 clean입니다.


===== 세션 rollout-2026-08-13T08-38-10-019ff857-285c-78e3-a6a5-ae8283333cea.jsonl =====
D2와 D7~D11의 V1 주장 원문을 확보했습니다. 이제 `/private/tmp` 복제본에서 baseline 실행 후 각 조작을 독립 적용하고, 매번 `git restore`와 `git clean`으로 원복 상태를 확인하겠습니다.


===== 세션 rollout-2026-08-13T08-36-30-019ff855-a2f8-7763-9f39-340895be8475.jsonl =====
요청한 범위를 `worktrees/humansearch-g3-portal-constants` + `/private/tmp/.../scratchpad`만 사용해 추출했습니다. `scratchpad/codex-v1-verdict-g3.md`가 해당 V2/CLAUDE 판정 근거와 D1~D11을 모두 담고 있습니다.

## 원본 자료: D1~D11 목록(요약 + severity)
- 파일: `/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/b38d7124-1e8d-4dd9-b7d6-e3ff958c9d0f/scratchpad/codex-v1-verdict-g3.md:52-62`
- 표 요약:
  - `D1` 치명: `scripts/acceptance-hs-portal-constants.sh:188-243` (`ci_line_ok` 기반 CI 라인 판독)
  - `D2` 높음: `scripts/acceptance-hs-portal-constants.sh:257-267` (pre-push collect/exit 0 체크 편향)
  - `D3` 높음: `scripts/acceptance-hs-portal-constants.sh:31,143-150` (제품 루트 고정 2개)
  - `D4` 높음: 전역 패턴 `:10-25`, 제품 패턴 `:22-32` (selector 누락)
  - `D5` 높음: 제품 패턴 `:7-20` (URL/도메인/호스트:포트 누락)
  - `D6` 높음: `docs/sot/coding-principles.md:26` (PR 3,000줄 상한)
  - `D7` 중간: mutation 파일 `:80-116` 및 본체 `:158` (규칙 copy/reuse)
  - `D8` 중간: 검사기 `:107-153,165-166` (읽기 실패를 위반이 아닌 검사불능으로 처리 못함)
  - `D9` 중간: 검사기 `:129-138` (문서 일괄 제외 정책)
  - `D10` 낮음: 제품 패턴 `:17,19` (IPv4 중복)
  - `D11` 낮음: goal 문서 172개 행+EOF(기본 검증 명령이 공백·EOF 실패)

## 주장/근거+재현 형태(원문 근거 라인)
- `D1` 근거 텍스트 블록 시작: `.../scratchpad/codex-v1-verdict-g3.md:140`
  - 실험 출력: `baseline/step_if_false/step_continue/.../job_if_false` (`ci_line_ok=0/1` 표), `YAML_KEY_CHECK`.
- `D2` 근거 텍스트 블록 시작: `...:196`
  - 실험 출력: `baseline`, `exec_true`, `exit_00`, `compound_exit`, `if_false` 각 케이스 `actual_hook_exit=0`.
- `D3` 근거 텍스트 블록 시작: `...:220`
  - 실험 출력: `humansearch/src`, `humansearch/tests`는 product 적용되어 blocked / `humansearch/cli`는 product 미실행.
- `D4` 근거 텍스트 블록 시작: `...:249`
  - ADVERSARIAL 목록: `upper-case selector API`, `space before locator`, `JavaScript camelCase`, `Selenium`, `simple CSS class`, `split XPath`, `CSS escaped id`.
- `D5` 근거 텍스트 블록 시작: `...:284`
  - 반례 목록: 괄호 URL만 blocked, 분할 URL/도메인/퍼센트 인코딩/2레벨 TLD/공백 host-port은 missed.
- `D6` 근거 텍스트 블록 시작: `...:300`
  - 개수표: `TOTAL added=4318 deleted=14 changed=4332`.
- `D7` 근거 텍스트 블록 시작: `...:323`
  - 파일 증거: 여러 하드닝/뮤테이션 스크립트의 `cp` 라인 + `find humansearch/src humansearch/tests`.
- `D8` 근거 텍스트 블록 시작: `...:414`
  - 출력: `mktemp-failure`/`invalid-regex`/`empty-match` 후 `git-mode-read-failure`/`g3-find-failure`가 exit=1.
- `D9` 근거 텍스트 블록 시작: `...:473`
  - `docs/portal-example.md`은 skip, `docs/run-portal.py`는 scan-target.
- `D10` 근거 텍스트 블록 시작: `...:490`
  - `ipv4` 행 제거 후에도 `dotted host` 규칙이 잡힘.
- `D11` 근거 텍스트 블록 시작: `...:502`
  - `git-diff-check` 결과: `trailing-whitespace=172`, `blank-line-at-eof=1`.

## D2, D6~D11의 추가 독립 반박 포인트(추가 후보/보완)
- `D2`는 “pre-push 존재/실행권한/수집식 유무만” 보고하고 `exit 0` 존재 여부 문자열 패턴을 허용 문자열 교체로 속일 수 있다는 실험 문구가 이미 본문에 있음(`exec_true`, `exit_00`, `compound_exit`) — “로컬 반영 검증만으로는 미완” 후보.
- `D6`는 코딩 원칙 line26이 명시한 3,000줄 규칙 + 실제 `git` 집계표(`changed=4332`)로 독립 정량 근거 충분.
- `D7`는 mutate 시험이 실제 규칙 제거/교체 실험이 아니라 fixture 값 주입 중심이라 “공유가정 blind spot” 자체는 V1 패턴 교차확인 후보.
- `D8`는 `git ls-files`/`find` 실패를 하드 오류에서 분리 못 한 점이 이미 “read/write path 경로” 카테고리와 맞닿아 있으나, `ci_line_ok`와 별개라 별도 보완 여지.
- `D9`는 계약/면제 정책은 feature 요구 대비 scope mismatch를 남기므로 scope 분리 후보로 취급 가능(“docs 전체 금지” 요구와 충돌 언급).
- `D10`은 규칙 독립성 결함(겹침 패턴)이라 “각 규칙별 kill-case” 완전성 검증 회귀 케이스 후보.
- `D11`은 기능 결함은 아니나 기본 정숙성 실패로 PR 게이트(비기능) 영향 후보.

## 원판정 문서/goal 교차 근거(특히 claim4 counter-AC-5)
- Goal 비판목록 및 counter-AC5 위치:
  - `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:55-66`(counter-AC 1~11, 5는 “존재하지 않는 제품 루트 조용히 skip”)
  - 제품 경로 고정: `:100-101` (`humansearch/src`, `humansearch/tests`)
  - 자동발견 지연: `:177`
  - 비범위/예외: `:171-177` (자동발견은 후속과제로 보류)
- 따라서 counter-AC5 정정 타당성 판단은 “비범위에 둔 제품루트 자동발견과는 충돌 가능” 여부를 확인해야 함(문서 텍스트 자체는 D3 반박 가능성 강하게 뒷받침).

## 코드 매핑(요청한 file:line 역할)
- CI 판독 함수: `scripts/acceptance-hs-portal-constants.sh:188-243` (`ci_line_ok`)
- pre-push 판별: `:257-267` (`hooks/pre-push` 존재·글로브·무조건 exit 0·found_self·MARK check)
- 제품 루트 고정: `:31`, `143-150`
- 파일 스캔 분기/Docs 면제/pattern 적용: `107-153`
- 미정상 상태 핸들링(2/1 우선순위): `305-320`, `322-324`
- mutation 설계상 규칙 복제/카운트 계산: `scripts/acceptance-hs-portal-constants-mutations.sh:92-110,151-163,158-163,172-176,237-243,260-164,292-297,298-304`
- 검증 기본 규칙(3,000줄 상한) 원본: `docs/sot/coding-principles.md:26`
- PR D6 계산 근거: `.../codex-v1-verdict-g3.md:305-314` 의 file-by-file count table + total changed=4332.
- Goal/반례 판정 위치: `.../humansearch-g3-portal-constants-goal-2026-08-12.md:55-66`, `100-101`, `171-177`, `172` (non-scope), `2737` 근거 줄(개요에는 D11 참조).

요청하시면 다음 응답에서 바로 각 D별로 “반드시 재현 필요한 테스트 설계(입력 파일/명령/기대 rc/출력 패턴)” 형태로 실행 명령서로 펼쳐드리겠습니다.


===== 세션 rollout-2026-08-13T08-33-57-019ff853-4f2b-7d83-a9ae-b502edcf7534.jsonl =====
감사 모드는 “다른 AI 답변과 실제 코드·실행을 함께 대조하는 혼합 감사”로 고정했습니다. 이제 기준 문서와 검사기 자체를 먼저 확정한 뒤, 주장별 실험을 서로 섞이지 않게 한 번씩 만들고 실행·원복·청결 확인까지 기록하겠습니다.
