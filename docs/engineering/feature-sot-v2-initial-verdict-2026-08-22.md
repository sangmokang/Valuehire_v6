VERDICT: PASS

## 결론
현재 공유 작업트리는 `HEAD=c59bad7b160c473cda5545e76e6fa6bcc711a7ea` 기준 제품 표면과 기능 SOT 귀속 검사를 통과했습니다. 검증 중 `29ce9da`에서 `c59bad7`로 fast-forward되며 `humansearch/src/humansearch/_cdp.py`, `humansearch/src/humansearch/observe.py`, `contracts/humansearch/saramin-markers.json`가 새 제품 표면으로 들어왔고, 중간에는 SOT가 이를 따라가지 못해 실제 FAIL이 났습니다. 최종 SOT 갱신 뒤에는 누락·중복·없는 경로·URL 근거·둘째 줄 `name` 우회·7번째 기능 확장 반례가 모두 기대대로 판정됐습니다.

현재 잔존 결함은 찾지 못했습니다. 단, 이 PASS는 커밋된 깨끗한 HEAD가 아니라 `c59bad7` 위의 현재 dirty working tree 문서/스크립트 상태에 대한 판정입니다.

## 판단 근거
버린 해석: `29ce9da` 기준 V1 PASS를 그대로 신뢰하는 해석은 버렸습니다. 검증 중 HEAD가 바뀌었고, 새 HumanSearch L1 관측 표면이 생기면서 V1의 제품 파일 수 11개 주장은 즉시 낡았습니다.

틀리면 깨지는 것: 기능 SOT가 실제 제품 파일, CI 단계, CI 명령, 훅, HumanSearch 계약 표면을 하나라도 놓치면 다음 작업자가 “현재 기능 목록이 완전하다”고 오판합니다. 그래서 `scripts/check-docs-sot.sh`의 실집합 대조와 별도 임시 변이를 모두 다시 실행했습니다.

## 증거
- `git rev-parse HEAD` — `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- `bash scripts/check-docs-sot.sh` — exit 0, `features=6`, `invariants=33`, `product_files=14`, `ci_steps=23`, `ci_commands=29`, `hooks=2`, `contract_surfaces=2`
- `cd humansearch && uv run --no-sync pytest -q` — exit 0, `81 passed`
- `git diff --check` — exit 0
- `git status --short` — 원본 저장소에 제 변경은 없고, 기존/동시 작업자의 dirty 문서·스크립트 변경과 untracked SOT 파일이 남아 있습니다.

## 기술 상세
- `docs/sot/features/catalog.yaml:57-70` — HumanSearch L0 인증 분류와 L1 사람인 일회 관측이 각각 기능으로 남아 있고 둘 다 `implemented/local_runtime`입니다.
- `docs/sot/features/catalog.yaml:97-115` — 제품 루트, 제어 루트, 제품 파일·CI 단계·CI 명령·훅·계약 표면 귀속 규칙을 명시합니다.
- `docs/sot/features/automation/humansearch-browser-access.yaml:31-42` — 새 `contracts/humansearch/saramin-markers.json`, `_cdp.py`, `observe.py`, browser contract가 한 기능에 귀속됐습니다.
- `docs/sot/features/automation/humansearch-browser-access.yaml:44-60` — CLI/API/좁은 CDP transport 진입점을 선언합니다.
- `humansearch/src/humansearch/observe.py:126-165` — 한 번만 관측하고 상태를 출력하며, 성공은 `AUTHENTICATED`일 때만 exit 0입니다.
- `humansearch/src/humansearch/_cdp.py:20-84` — 임의 CDP 실행기가 아니라 계약된 marker 관측만 수행합니다.
- `scripts/check-docs-sot.sh:126-166` — CI step 이름을 Ruby Psych YAML 파서로 읽어 둘째 줄 `name`, spaced dash, flow mapping 우회를 잡습니다.
- `scripts/check-docs-sot.sh:329-360` — `git ls-files`, workflow 파일, CI 명령 경로 실집합을 유도합니다.

## 임시 변이 반증
임시 git-index 사본에서 재현했습니다.

| 공격 | 결과 |
|---|---|
| 필수 키 삭제 | exit 1, `required keys missing` |
| 기능 0개 | exit 1, `catalog features must be non-empty` |
| 미귀속 CI step | exit 1, `ci_steps ownership mismatch` |
| 미귀속 CI command | exit 1, `ci_command_paths ownership mismatch` |
| 둘째 workflow | exit 1, `CI workflow coverage changed` |
| 둘째 줄 `name` | exit 1, `ci_steps ownership mismatch` |
| spaced dash / flow mapping | exit 1, 각각 미귀속 step으로 실패 |
| URL 근거 | exit 1, `external URL is not permitted` |
| 없는 경로 | exit 1, `does not exist` |
| 중복 훅 귀속 | exit 1, `duplicate hooks surface` |
| 실제 새 제품 파일 + 7번째 기능 | exit 0, `features=7`, `product_files=15` |

## V1 대조
| 항목 | V1 주장 | V2 판정 |
|---|---|---|
| V1 FAIL D-1~D-3 | 강제 장치 누락, 6개 상수, URL 예외 | 현재는 해소됨. 실집합 대조·Psych parser·URL 거부 확인 |
| V1 PASS F-1 | 둘째 줄 `name` 우회 가능 | 현재는 해소됨. 둘째 줄/spaced/flow 모두 exit 1 |
| V1 PASS F-2 | `docs/sot/INDEX.md`에 “6개” 상수 문구 | 현재 해소됨: `docs/sot/INDEX.md:6`은 “현재 주요 기능”으로 표현 |
| V1 PASS F-3 | 변이 기록 날짜/범위 과소 보고 | 현재 해소됨: `docs/sot/verification-commands.md:82-83`이 2026-08-22 여섯 고장 사본 + 7번째 기능 확장을 기록 |
| V1 최신성 | 제품 파일 11개, pytest 64개 | 현재 HEAD에서는 낡음. 최종 값은 제품 파일 14개, pytest 81개 |

요약 수치: V1이 잡은 G 과장 3건(D-1~D-3) 중 현재 잔존 0건입니다. V2가 잡은 V1 과장·누락은 1건입니다. 즉 V1 PASS가 `c59bad7` fast-forward 뒤 새 L1 표면을 포함하지 못한 최신성 누락입니다. 이 누락은 최종 SOT 갱신 후 현재 PASS로 닫혔습니다.

## 리스크
- GitHub 원격 CI와 branch protection은 조회하지 않았습니다.
- 현재 working tree가 dirty/untracked 상태라, “커밋된 HEAD만 체크아웃한 새 clone”의 PASS로 확대하면 안 됩니다.
