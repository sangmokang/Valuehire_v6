VERDICT: PASS

## 결론
현재 산출물은 V1-G 결함을 “해결됨”이나 “허용 동작”으로 과장하지 않고, `KNOWN_DEFECT`로 좁혀 문서화했습니다. 최신 문구 기준으로 `raw URL 전체` 표현은 사라졌고, 세 문서 모두 malformed target URL에서 `ValueError`가 정규화되지 않아 traceback·URL 조각·exit 1이 날 수 있다는 현재 제한으로 일치합니다.

실제 포털 접속은 하지 않았고, 공유 트리는 수정하지 않았습니다.

## 판단 근거
- `docs/sot/features/catalog.yaml:128` — catalog known gap이 “URL fragments + exit 1, handled one-line exit 2 아님”으로 기록되어 있습니다.
- `docs/sot/features/automation/humansearch-browser-access.yaml:86-95` — handled exit `0/2`와 known unhandled exit `1`을 분리합니다.
- `docs/sot/features/automation/humansearch-browser-access.yaml:100-105` — 일반 관측 실패는 exit 2 정규화 대상이지만 malformed URL은 별도 known defect라고 씁니다.
- `docs/sot/features/automation/humansearch-browser-access.yaml:167-169` — `HBA-V1-GAP`은 현재 실패를 기대값으로 기록하고, 제품 수정 뒤 제거해야 한다고 명시합니다.
- `docs/sot/features/automation/humansearch-browser-access.yaml:209` — known gap 제거 조건을 “회귀 시험 + 코드 수정 같은 변경”으로 묶었습니다.
- `docs/sot/humansearch-browser-contract.md:18-22` — 허용 동작이 아니라 현재 제한이며, 수정 전에는 “모든 관측 실패가 안전한 한 줄로 닫힌다”고 주장하지 않는다고 명시합니다.
- `docs/sot/humansearch-browser-contract.md:260` + `docs/sot/features/automation/humansearch-browser-access.yaml:141` — `#10-자격증명과-명령-능력-경계` anchor가 실제 §10 제목과 맞습니다.
- `docs/sot/humansearch-browser-contract.md:373` — 구현 장부에서 malformed URL 실패 정규화가 `KNOWN_DEFECT`로 분리되어 있습니다.

## 실행 증거
- `bash scripts/check-docs-sot.sh` — PASS, `features=6`, `product_files=14`, `ci_steps=23`, `ci_commands=29`, `hooks=2`, `contract_surfaces=2`
- `cd humansearch && uv run --no-sync pytest -q` — PASS, `81 passed`
- `git diff --check` — PASS, 출력 없음
- malformed URL 로컬 재현 — `ValueError: Invalid IPv6 URL`, traceback, `EXIT=1`

## V1/V2 비교표
| 항목 | V1-G 지적 | 현재 V2 재검증 |
|---|---|---|
| malformed target URL | uncaught `ValueError`/traceback/exit 1 제품 결함 | 사실로 재현됨. SOT가 `KNOWN_DEFECT`로 기록 |
| 문구 정밀도 | “raw URL 전체” 표현은 과할 수 있음 | 최신 문구는 “URL fragments/호스트 조각 등”으로 좁혀짐 |
| 해결 과장 | 결함을 허용 동작처럼 쓰면 실패 | 현재는 “not accepted safe behavior”, “current defect”, “must be fixed”로 명시 |
| 제거 조건 | 문서만 지우면 안 됨 | 회귀시험 + 제품수정 동시 제거 조건 있음 |
| §10 anchor | 잘못된 anchor 가능성 | 현재 `#10-자격증명과-명령-능력-경계`가 실제 제목과 일치 |
| V1-H | PASS 주장 | 현재 명령 3종과 문구 대조로 PASS 유지 |

## Gaps
- 원격 CI와 GitHub branch protection은 확인하지 않았습니다.
- malformed URL은 로컬 함수 호출로만 재현했습니다. 실제 포털 접속은 금지 조건에 따라 수행하지 않았습니다.

## Risks
- 현재 작업트리는 dirty/untracked 상태입니다. 이 PASS는 `c59bad7` 위의 현재 공유 작업트리 산출물 기준이며, 커밋된 clean checkout 기준 판정은 아닙니다.
