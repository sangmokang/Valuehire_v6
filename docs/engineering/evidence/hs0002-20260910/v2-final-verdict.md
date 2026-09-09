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
- V1이 잡은 G 과장은 1건입니다: `final-g2.json/log`가 존재하지 않는 명령 실행 실패를 보존한 기록 결함입니다.
- V2가 잡은 V1 과장·누락은 1건입니다: V1 정보3의 n28 “사실상 등가 변이” 설명은 `v2-final-prefix-counterprobe`에서 반박됐습니다. 제품은 해당 입력을 거부하지만 n28 변이 사본은 허용하므로 시험 강도 한계입니다.
- V1 실행 신원은 `v1-final-identity-readback.json`이라는 root 제공 readback 파일을 대조한 것입니다. V2가 private raw CLI 원본을 직접 다시 열람했다는 뜻이 아닙니다.

## V1 항목 일치·불일치 표

| V1 항목 | V2 결과 | 증거 | 판정 |
|---|---|---|---|
| V1 실행 신원 | SOURCE_LIMITED | `v1-final-identity-readback.json` | root 제공 readback 파일을 대조했다. V2가 private raw CLI 파일을 직접 다시 읽었다고 주장하지 않는다. |
| 후보 5파일 지문 | MATCH | `final-candidate-files.json + v2-final-candidate-sha.log` | 현재 지문이 후보 manifest와 일치 |
| 원칙 직접 로드 | MATCH | `v2-final-principles-*.log/json` | SOT/ledger 로드 및 34/34 검사 통과 |
| 정조준 43개 | MATCH | `v2-final-adv-target-pytest.log, v2-final-adv-target-uv.log` | 두 경로 모두 43 passed |
| 기존 변이 37개 | MATCH | `v2-final-adv-mutations-37.log` | CHECKED: 37, exit 0 |
| G2 전체 회귀 | MATCH | `v2-final-adv-g2.log` | 262 collected/passed, ruff/mypy 통과 |
| V1 D1 final-g2 오기록 | MATCH_WITH_CLASSIFICATION | `final-ledger-reconciliation.md` | final-g2 실패는 실제 기록 결함이나 final-g2-recheck와 V2 G2가 같은 지문에서 통과 |
| 정적 검사 | MATCH | `v2-final-adv-static.log, v2-final-adv-ruff-product.log` | diff check, bash -n, ruff, mypy 통과 |
| 파일/함수 한도 | MATCH | `v2-final-adv-budget*.log` | hard600/100 이하 및 600/601, 100/101, 0대상 경계 통과 |
| 격리 변이 38개 | MATCH | `v2-final-adv-mutants.json` | V1과 같은 6개 생존, 원본 지문 불변 |
| 직접 CLI 93건 | MATCH | `v2-final-adv-cli-probes.json` | V1과 같은 expected-zero-width-space 1건만 스크립트 기대값 불일치 |
| negative 셸 경로 21건 | MATCH | `v2-final-adv-negative-path.json` | venv 재실행에서 mismatch 0 |
| V1 정보3 n28 등가 변이 설명 | MISMATCH | `v2-final-prefix-counterprobe.log/json` | 제품은 거부하지만 n28 변이는 허용한다. '사실상 등가' 설명은 반박됐고, 시험 강도 한계로 분류한다. |

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

## 증거 원문 연결

아래 표의 `log path` 파일이 전체 stdout/stderr 원문입니다. 표 안의 SHA256은 해당 전체 로그 파일의 지문입니다. 이 판정서는 중간부터 잘린 tail 발췌를 원문 증거로 쓰지 않습니다.

| label | exit | command | log path | log SHA256 |
|---|---:|---|---|---|
| v2-final-principles-md | 0 | `sed -n 1,260p docs/sot/coding-principles.md` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-principles-md.log` | 55b136c984d3f93b522b07b33a0f5f74427777eb0901e24acc38c22b2b0e8276 |
| v2-final-principles-yaml | 0 | `sed -n 1,420p docs/sot/principles.yaml` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-principles-yaml.log` | a19b29abaf6c61e403d2f1df5720b55ff477942dc9257cb2513043b20855ef22 |
| v2-final-principles-check | 0 | `bash scripts/acceptance-principles-check.sh` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-principles-check.log` | 31153ab17a665560a3a4e8a5f2a45bd58275e1d6f1e1d27a21fee40d74197dc2 |
| v2-final-status-head | 0 | `git status --short` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-status-head.log` | fdf2184014c0261089f399f31276a32494ab928aaa4e2984f5ffd7e9e43f234f |
| v2-final-candidate-sha | 0 | `shasum -a 256 scripts/acceptance-hs-kickoff-mutations.sh scripts/verify/has-kickoff-failure.py humansearch/tests/test_hs_0002.py humansearch/tests/test_hs_0002_boundaries.py docs/sot/verification-commands.md` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-candidate-sha.log` | c269ec15f0541598c7014d9e65209dff67b7968d7685da5100333e3d03a9a7a2 |
| v2-final-adv-target-pytest | 0 | `humansearch/.venv/bin/python -m pytest -q humansearch/tests/test_hs_0002.py humansearch/tests/test_hs_0002_boundaries.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-target-pytest.log` | 899b2f41a1139f160d1ab9b31a1f49e21e275d40b52df9d54c2ac92c8f2cb26e |
| v2-final-adv-target-uv | 0 | `bash -lc cd humansearch && uv run --no-sync pytest -q tests/test_hs_0002.py tests/test_hs_0002_boundaries.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-target-uv.log` | 5abebb9c7f7b6971d7d874011d746e97a8a690a6ccdea8939290d8d4c46767d8 |
| v2-final-adv-mutations-37 | 0 | `bash scripts/acceptance-hs-kickoff-mutations.sh` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-mutations-37.log` | 099ddbde4dae0766cbe5c527539429416d3b5d27e7ebbf96e9453d3dbe4cb252 |
| v2-final-adv-g2 | 0 | `bash scripts/acceptance-hs-gates.sh` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-g2.log` | 8600c696a30002e20a7e215572db3eefa81e3609bfacb02279f45382b3dbebd0 |
| v2-final-adv-static | 0 | `bash -lc git diff --check && bash -n scripts/acceptance-hs-kickoff-mutations.sh` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-static.log` | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| v2-final-adv-ruff-product | 0 | `bash -lc cd humansearch && uv run --no-sync ruff check src tests ../scripts/verify/has-kickoff-failure.py && uv run --no-sync mypy src tests ../scripts/verify/has-kickoff-failure.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-ruff-product.log` | dbc368600de0171ce2663a0c71500733e990794ea52a5e2ac10adef1e438d324 |
| v2-final-adv-budget | 0 | `python3 artifacts/hs0002-20260910/v2-final-adv-budget.py scripts/acceptance-hs-kickoff-mutations.sh scripts/verify/has-kickoff-failure.py humansearch/tests/test_hs_0002.py humansearch/tests/test_hs_0002_boundaries.py docs/sot/verification-commands.md` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-budget.log` | 8fd602169a68c6899b1e56b5289a8d898c8eaae7a89ccdb401b809d32822e072 |
| v2-final-adv-budget-boundaries | 0 | `python3 artifacts/hs0002-20260910/v2-final-adv-budget.py --boundaries` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-budget-boundaries.log` | 904472783a0ce0243de2cce70fb11e2b09dde58a06957756356eb6c303d52579 |
| v2-final-adv-mutants-run | 1 | `python3 artifacts/hs0002-20260910/v2-final-adv-mutants.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-mutants-run.log` | 9a8cec40e26eb5ad79dc939999ccc9b30d2a2a91f02a8cb273d567f4d493512a |
| v2-final-adv-cli-probes-run | 1 | `python3 artifacts/hs0002-20260910/v2-final-adv-cli-probes.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-cli-probes-run.log` | 479dcdfbdceefc56e575f3a8d6d120da30e0cfa71a71e3d3d505fb9a28bfb308 |
| v2-final-adv-negative-path-run | 1 | `python3 artifacts/hs0002-20260910/v2-final-adv-negative-path.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-negative-path-run.log` | 1a5a7a0ca8a5a9c63e44802ca2ca3f0d7570ef734f8c4e3965cf0fee80a9a6b4 |
| v2-final-adv-negative-path-rerun | 0 | `humansearch/.venv/bin/python artifacts/hs0002-20260910/v2-final-adv-negative-path.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-adv-negative-path-rerun.log` | 95e65ea303c83f95938c1f0bdb85e44ae876881ca2158edb88e05995c527481c |
| v2-final-prefix-counterprobe | 0 | `python3 artifacts/hs0002-20260910/final-prefix-counterprobe.py` | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0002-20260910/artifacts/hs0002-20260910/v2-final-prefix-counterprobe.log` | 91957ec77956b6619f9c1564e74684906a1d44a396f011b403746a92daaec3e1 |

## 미실행·범위 밖

- 원격 CI, push, PR, 병합은 실행하지 않았습니다.
- 실제 포털·DB·브라우저·메시지 호출은 실행하지 않았습니다.
- HS-00.03 동형·보이지 않는 문자 정책, HS-00.04 workflow 실행 의미, HS-00.05 앞 단계 환경은 이 판정의 범위 밖입니다.
- V1/V2는 같은 UID 로컬 검토이며 OS/P17 별도 러너 영수증이 아닙니다.
