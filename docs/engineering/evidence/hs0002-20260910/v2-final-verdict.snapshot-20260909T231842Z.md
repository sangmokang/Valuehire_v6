VERDICT: PASS

# HS-00.02 V2 최종 독립 재공격 판정

## 결론

제품 후보는 통과입니다. 같은 후보 지문에서 정조준 43개, 기존 변이 37개, G2 전체 262개, 정적 검사, 파일·함수 한도와 한도 경계, 직접 입력 93건, 실제 `negative()` 셸 경로 21건을 다시 실행했습니다. 제품 차단 결함은 재현되지 않았습니다.

다만 V1의 기록 지적과 시험 강도 한계는 사실입니다. `final-g2.json`의 잘못된 명령 기록은 REPRODUCED이지만, `final-g2-recheck`와 이번 V2의 `scripts/acceptance-hs-gates.sh` 실행이 같은 후보 지문에서 262개 통과를 보였으므로 제품 판정을 막지는 않습니다. n28 no-space 접두 변이는 동결 시험 43개가 못 잡지만, 추가 반례에서 현재 제품 helper는 같은 입력을 거부했습니다.

## 판단 근거

- 현재 HEAD: `8bef581b2ee64dd57345f92f11f241e0c927b759`. 후보 5파일의 현재 SHA256은 `final-candidate-files.json`과 일치합니다.
- `docs/sot/coding-principles.md`와 `docs/sot/principles.yaml`을 직접 읽고 `bash scripts/acceptance-principles-check.sh`를 실행했습니다. 결과는 `VERDICT: PASS`, `MECHANISMS: PASS 34/34`, `CHECKED: 34`입니다.
- 정조준 시험은 `humansearch/.venv/bin/python -m pytest -q humansearch/tests/test_hs_0002.py humansearch/tests/test_hs_0002_boundaries.py`와 `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0002.py tests/test_hs_0002_boundaries.py` 두 경로 모두 `43 passed`입니다.
- 전체 회귀는 `bash scripts/acceptance-hs-gates.sh` 종료값 0, `PASS: pytest collected 262 and passed`, `COLLECTED: 262`입니다.
- hard 600/100 한도는 후보 파일 593/51/178/73/96줄 및 함수 최대 31줄입니다. 같은 검사기로 600줄·100줄 정상 사본은 통과했고 601줄·101줄·0대상은 거부됐습니다.
- 격리 변이 38개는 V1과 같이 6개 생존했습니다. 생존 변이는 제품 사본을 틀리게 만들어도 동결 시험이 못 잡는 지점이지만, 직접 CLI/추가 반례로 현재 제품 동작은 별도 확인했습니다.
- `v2-final-adv-negative-path-run`은 시스템 Python에 pytest가 없어 실패했습니다. 이 실패는 제품이 아니라 검증자 실행 환경 문제이며, 같은 스크립트를 `humansearch/.venv/bin/python`으로 재실행한 `v2-final-adv-negative-path-rerun`은 21건 모두 일치했습니다.

## V1 항목 일치·불일치 표

| V1 항목 | V2 상태 | 증거 | 판정 |
|---|---|---|---|
| V1 실행 신원 | REPRODUCED | `v1-final-identity-readback.json` | session fd...310a, apiKeySource none, raw hash verified |
| 후보 5파일 지문 | REPRODUCED | `final-candidate-files.json + v2-final-candidate-sha.log` | 현재 지문이 후보 manifest와 일치 |
| 원칙 직접 로드 | REPRODUCED | `v2-final-principles-*.log/json` | SOT/ledger 로드 및 34/34 검사 통과 |
| 정조준 43개 | REPRODUCED | `v2-final-adv-target-pytest.log, v2-final-adv-target-uv.log` | 두 경로 모두 43 passed |
| 기존 변이 37개 | REPRODUCED | `v2-final-adv-mutations-37.log` | CHECKED: 37, exit 0 |
| G2 전체 회귀 | REPRODUCED | `v2-final-adv-g2.log` | 262 collected/passed, ruff/mypy 통과 |
| V1 D1 final-g2 오기록 | REPRODUCED | `final-ledger-reconciliation.md` | final-g2 실패는 실제 기록 결함이나 final-g2-recheck와 V2 G2가 같은 지문에서 통과 |
| 정적 검사 | REPRODUCED | `v2-final-adv-static.log, v2-final-adv-ruff-product.log` | diff check, bash -n, ruff, mypy 통과 |
| 파일/함수 한도 | REPRODUCED | `v2-final-adv-budget*.log` | hard600/100 이하 및 600/601, 100/101, 0대상 경계 통과 |
| 격리 변이 38개 | REPRODUCED | `v2-final-adv-mutants.json` | V1과 같은 6개 생존, 원본 지문 불변 |
| 직접 CLI 93건 | REPRODUCED | `v2-final-adv-cli-probes.json` | V1과 같은 expected-zero-width-space 1건만 스크립트 기대값 불일치 |
| negative 셸 경로 21건 | REPRODUCED | `v2-final-adv-negative-path.json` | venv 재실행에서 mismatch 0 |
| n28 prefix 반례 | REPRODUCED | `v2-final-prefix-counterprobe.log/json` | 제품은 거부, n28 변이는 허용; 시험 강도 한계 |

## 결함·지적

| ID | 상태 | 심각도 | 제목 | 분류 | 그대로 둘 때 영향 |
|---|---|---|---|---|---|
| F1 | REPRODUCED | low | final-g2 기록 하나가 존재하지 않는 명령을 보존한다 | 기록 결함, 제품 차단 아님 | 이 파일만 근거로 완료를 말하면 실행하지 않은 검증을 통과로 착각할 수 있음 |
| F2 | REPRODUCED | info | 동결 시험 43개가 n28 no-space FAIL 접두 변이를 잡지 못한다 | 검증 강도 한계, 제품 결함 아님 | 현재 제품은 올바르게 거부하지만, 같은 종류 회귀를 시험만으로는 놓칠 수 있음 |
| F3 | REPRODUCED | info | U+200B만 있는 기대값은 현재 helper가 문자 그대로 허용한다 | 범위 밖 정책 결정, 제품 결함 아님 | HS-00.02 상수 호출처에는 영향이 없고 보이지 않는 문자 정책은 HS-00.03 범위 |

## file:line 역할

- `scripts/verify/has-kickoff-failure.py:21` — 기대 실패 사유와 출력 파일을 비교하는 핵심 함수입니다.
- `scripts/verify/has-kickoff-failure.py:22` — 빈 값·공백만·줄바꿈 포함 기대값을 거부합니다. U+200B는 이 조건에서 공백으로 보지 않습니다.
- `scripts/verify/has-kickoff-failure.py:25` — `FAIL: ` 접두가 있는 정규 실패 줄만 봅니다. n28 반례는 이 줄의 공백을 제거한 변이가 시험을 통과한다는 점을 보였습니다.
- `scripts/verify/has-kickoff-failure.py:31`~`33` — 일반 사유는 메시지 시작과 끝/공백/탭/슬래시 경계만 허용합니다.
- `scripts/acceptance-hs-kickoff-mutations.sh:176`~`180` — 기존 음성 변이가 실제로 대상 출력을 만들고 기대 사유로 실패했는지 확인하는 경로입니다.
- `humansearch/tests/test_hs_0002_boundaries.py:11` — 빈 값·공백만 기대값 거부 회귀 시험입니다.
- `humansearch/tests/test_hs_0002_boundaries.py:47` — 실제 `negative()` 호출 경로로 경계·legacy 사유를 검증합니다.
- `humansearch/tests/test_hs_0002_boundaries.py:55` — helper CLI의 파일 없음·디렉터리·UTF-8 오류 처리를 검증합니다.

## 증거 원문 요약

```text
v2-final-adv-target-pytest.log
...........................................                              [100%]
43 passed in 6.17s

```
→ 동결 시험 43개가 현재 후보에서 통과했습니다.

```text
v2-final-adv-g2.log
PASS: ruff clean in 45 python files
PASS: mypy strict clean in 45 source files
PASS: pytest collected 262 and passed
PASS: runtime import proof /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/humansearch/src/humansearch/__init__.py
COLLECTED: 262

```
→ 전체 G2 회귀가 262개 수집·통과와 ruff/mypy 통과를 냈습니다.

```text
v2-final-adv-mutants-run.log
h                 exit=1 failed=2 2 failed, 41 passed in 5.96s
KILLED           n32-cli-swallow-unicode-error-exit1      exit=1 failed=1 1 failed, 42 passed in 5.77s
KILLED           n33-cli-mismatch-exit0                   exit=1 failed=25 25 failed, 18 passed in 11.58s
SURVIVED         n34-cli-usage-exit0                      exit=0 failed=0 43 passed in 9.12s
SURVIVED         n35-split-lines-universal                exit=0 failed=0 43 passed in 5.89s
KILLED           n36-shell-ignore-helper-rc               exit=1 failed=25 25 failed, 18 passed in 11.97s
KILLED           n37-shell-helper-path-wrong              exit=1 failed=14 14 failed, 29 passed in 12.40s
product_unchanged: True survived: ['n27-drop-cr-suffix-strip', 'n28-fail-prefix-without-space', 'n29-legacy-fallthrough-to-literal', 'n30-legacy-count-allow-one', 'n34-cli-usage-exit0', 'n35-split-lines-universal'] unexpected: []

```
→ 격리 변이 38개 중 6개가 생존했고 원본 제품 지문은 변하지 않았습니다.

```text
v2-final-adv-cli-probes-run.log
                   wanted=2 got=2
OK  invalid-utf8-after-match             wanted=2 got=2
OK  utf16-encoded-file                   wanted=2 got=2
OK  nul-byte-in-file                     wanted=1 got=1
OK  short-expected-prefix-of-word        wanted=0 got=0
OK  short-expected-C-only                wanted=1 got=1
OK  nfd-decomposed-hangul                wanted=0 got=0
OK  missing-file                         wanted=2 got=2
OK  directory                            wanted=2 got=2
OK  no-args                              wanted=2 got=2
OK  one-arg                              wanted=2 got=2
OK  three-args                           wanted=2 got=2
total=93 mismatches=['expected-zero-width-space']

```
→ 직접 입력 93건 중 V1과 같은 `expected-zero-width-space` 1건만 스크립트 기대값 불일치로 남았습니다.

```text
v2-final-adv-negative-path-rerun.log
  wanted=0 got=0
OK  legacy-canonical                         wanted=0 got=0
OK  legacy-zero                              wanted=1 got=1
OK  legacy-bare                              wanted=1 got=1
OK  legacy-multi-one                         wanted=1 got=1
OK  blank-expected                           wanted=1 got=1
OK  empty-expected                           wanted=1 got=1
OK  extension                                wanted=1 got=1
OK  emdash-attached                          wanted=1 got=1
OK  slash-detail                             wanted=0 got=0
OK  unreadable-out-log-fail-closed           wanted=1 got=1
OK  wrong-cwd-helper-missing-fail-closed     wanted=1 got=1
total=21 mismatches=[]

```
→ 실제 `negative()` 셸 경로 21건은 venv 재실행에서 불일치가 없습니다.

```text
v2-final-prefix-counterprobe.log
ees/hs-0002-20260910/scripts/verify/has-kickoff-failure.py",
        "/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/hs0002-prefix-counterprobe-w8ia3xzf/out.log",
        "FAIL:reason"
      ],
      "expected_rc": 1,
      "actual_rc": 1,
      "stdout": "",
      "stderr": ""
    },
    {
      "case": "n28-mutant",
      "command": [
        "/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/humansearch/.venv/bin/python",
        "/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/hs0002-prefix-counterprobe-w8ia3xzf/mutant.py",
        "/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/hs0002-prefix-counterprobe-w8ia3xzf/out.log",
        "FAIL:reason"
      ],
      "expected_rc": 0,
      "actual_rc": 0,
      "stdout": "",
      "stderr": ""
    }
  ],
  "source_sha256": "4e43ea810cbbfd4a93aea8ac857790a23cc67557e30f693687a2e672cbbab2d0",
  "source_unchanged": true
}

```
→ 현재 제품은 `FAIL:reason`/`FAIL:reason`을 거부하지만 n28 변이 사본은 허용합니다. 제품 결함이 아니라 시험 강도 한계입니다.

## 미실행·범위 밖

- 원격 CI, push, PR, 병합은 실행하지 않았습니다.
- 실제 포털·DB·브라우저·메시지 호출은 실행하지 않았습니다.
- HS-00.03 동형·보이지 않는 문자 정책, HS-00.04 workflow 실행 의미, HS-00.05 앞 단계 환경은 이 판정의 범위 밖입니다.
- V1/V2는 같은 UID 로컬 검토이며 OS/P17 별도 러너 영수증이 아닙니다.
