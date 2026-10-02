VERDICT: PASS

## 결론

현재 작업트리 기준 `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`에서 V2-C 재검증은 PASS입니다. 공유 트리는 수정하지 않았고, 격리 임시 사본(`/tmp/valuehire-v2c-anchor.V7tLrd`)에서만 변이 검증했습니다. 라이브 포털 접속은 수행하지 않았습니다.

## 판단 근거

- `bash scripts/check-docs-sot.sh` — PASS
  `catalog=1 features=6 categories=3 invariants=33 product_files=14 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2 paths=validated`

- `wc -l scripts/check-docs-sot.sh` — PASS
  `475`, 요구사항 `<=500` 충족

- `cd humansearch && uv run --no-sync pytest -q` — PASS
  `81 passed in 8.69s`

- `git diff --check` — PASS
  출력 없음

- 격리 변이 검증 — PASS

| 검증 항목 | 기대 | 결과 |
| --- | --- | --- |
| backtick fence 내부 `~~~` fake anchor 무시 + 정상 close 후 real anchor | PASS | PASS |
| ` ```py``` ` 문단 뒤 real anchor | PASS | PASS |
| tilde fence 내부 ``` fake anchor 무시 + 정상 tilde close 후 real anchor | PASS | PASS |
| underscore anchor 유지형 | PASS | PASS |
| underscore 제거형 | FAIL | FAIL |
| double-hyphen anchor 유지형 | PASS | PASS |
| double-hyphen 축약형 | FAIL | FAIL |
| missing anchor | FAIL | FAIL |

## 기술 상세 / 증거

- Markdown anchor checker는 fence 시작/종료를 동일 marker·길이 기준으로 추적합니다: `scripts/check-docs-sot.sh:124`
- underscore와 연속 hyphen을 보존하는 slug 생성입니다: `scripts/check-docs-sot.sh:144`
- 존재하지 않는 fragment는 실패 처리합니다: `scripts/check-docs-sot.sh:164`

KNOWN_DEFECT 명세도 유지되어 있습니다.

- catalog에 malformed URL의 `ValueError`/traceback/exit 1을 해결 완료나 허용 동작이 아닌 결함으로 명시: `docs/sot/features/catalog.yaml:128`
- handled `0/2`와 known unhandled `1` 분리: `docs/sot/features/automation/humansearch-browser-access.yaml:86`
- 제품 수정 + 회귀시험 동시 제거 조건 명시: `docs/sot/features/automation/humansearch-browser-access.yaml:209`
- contract 문서도 허용 동작이 아닌 known implementation defect로 유지: `docs/sot/humansearch-browser-contract.md:18`
- §10 anchor는 현재 `#10-자격증명과-명령-능력-경계`와 일치합니다: `docs/sot/humansearch-browser-contract.md:260`

## V1 / V2 비교표

| 항목 | V1 판정 | V2-C 재검증 |
| --- | --- | --- |
| V1-J/K/L checker 결함 | underscore, 연속 hyphen, fence 혼합, marker 혼합, backtick info 문제 발견 | 격리 변이에서 모두 기대 PASS/FAIL 재현 |
| V1-M | PASS | 일치: 정상 SOT와 변이 검증 모두 PASS |
| malformed URL 제품 결함 | V1-G에서 제품 결함 및 문서 anchor 문제 지적 | 제품 코드는 미수정, SOT는 KNOWN_DEFECT로 정확히 유지 |
| 과장/누락 집계 | V1이 잡은 G 과장 0건 | V2가 잡은 V1 과장·누락 0건 |

## 결함 기록

신규 실패 결함은 없습니다.

유지 중인 기존 제품 결함은 SOT 범위에서 정확히 KNOWN_DEFECT로 분류되어 PASS 근거입니다.

- 심각도: D1
- 원문 제목: malformed target URL failure normalization
- 원인: malformed URL 입력에서 `urllib.parse.urlsplit`의 `ValueError`가 제품 경계에서 정규화되지 않음
- 사업 영향: 실패가 one-line/exit 2 계약으로 수렴하지 않고 traceback 및 URL 조각 노출 가능성이 남음
- 역할: 결함 명세 `docs/sot/features/catalog.yaml:128`, 계약/제거 조건 `docs/sot/features/automation/humansearch-browser-access.yaml:167`, `docs/sot/humansearch-browser-contract.md:373`

## 남은 주의사항

현재 PASS는 dirty working tree 기준입니다. 미추적/수정된 SOT 산출물이 포함되어 있으므로, “커밋된 깨끗한 HEAD” 판정은 별도 대상입니다. 원격 CI 상태는 이번 요청 범위에 없어 확인하지 않았습니다.
