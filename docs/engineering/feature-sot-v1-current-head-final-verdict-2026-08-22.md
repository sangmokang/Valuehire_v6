VERDICT: PASS

**건너뜀·재시도·추정 고지**: 실제 사람인 포털 라이브 접속은 하지 않았습니다(진단 포트·로그인 세션 없음). `main()` 경로의 종료값 1 재현은 `_fetch_targets`만 메모리에서 대체한 격리 실행으로 했고(저장소·네트워크 미접촉), 진단 포트 JSON 본문이 그 값을 돌려주는 상황과 동치라고 추정했습니다. pytest는 첫 실행에서 zsh `PIPESTATUS` 판독이 비어 종료값만 다시 확인했습니다(둘 다 81 passed).

## 결론
여섯 요구가 모두 실행으로 확인됐습니다. 두 결함은 교정됐고, 새 결함은 찾지 못했습니다.

## 검증 증거
- **제품 코드 무변경**: `git diff HEAD --stat -- humansearch contracts apps hooks` 빈 결과. 추적 변경은 `scripts/check-docs-sot.sh`(mtime 00:52, 이번 교정 이전) 하나뿐이고, 교정 대상 세 파일만 01:20:13에 갱신됐습니다.
- **세 문서의 동일 서술**: `catalog.yaml:128`, `humansearch-browser-access.yaml:104-106`·`:150`, `humansearch-browser-contract.md:18-22`·`:373`이 `urlsplit`의 `ValueError`가 정규화되지 않아 traceback·exit 1로 샐 수 있다는 같은 현재 제한을 말합니다. 모두 "허용된 동작이 아님"(`:105`), `KNOWN_DEFECT`(`:373`)로 표기하고 해결 완료로 쓰지 않습니다.
- **exit 계약 분리**: `outputs`가 `handled_exit_code`(`allowed_values [0,2]`, `:86-90`)와 `known_unhandled_exit`(`observed_value 1`, `:91-96`)로 나뉘고, `errors[0]`(`:101`)은 "except for the separately documented malformed-target-URL defect"로 예외를 명시합니다. 혼합 없음.
- **제거 조건**: `change_protocol.rollback:209`("regression test and code fix in the same change"), `HBA-V1-GAP.expected:169`, `browser-contract.md:21`·`:373`("회귀 시험 + 좁은 예외 정규화")이 동시 변경을 요구합니다.
- **앵커**: `#10-자격증명과-명령-능력-경계` ↔ `browser-contract.md:260 ### 10. 자격증명과 명령 능력 경계`. 동일 제목 1건, 나머지 fragment 5개도 실제 제목에 닿습니다.
- **명령**: `check-docs-sot.sh` exit 0 / `features=6 categories=3 invariants=33 product_files=14 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2`, checker 431줄(≤500). `pytest -q` exit 0, 81 passed. `git diff --check` exit 0.
- **결함 실재 확인**: `HBA-V1-GAP` 명령 exit 1, `ValueError: Invalid IPv6 URL`. 격리 `main()` 경로도 exit 1이며 한 줄 출력이 나오지 않습니다 — 문서가 실제와 일치합니다.
- **작업 트리 불변**: 실행 전후 `HEAD=c59bad7b16…`, `git status --porcelain` 24항목(수정 5 + 미추적 19 = V1-G의 21항목 + 사용자가 추가한 판정·지문 3개), `git stash list` 비어 있음. 임시 산출물은 `/tmp`에만 두었습니다.

## 잔여 리스크
- 문서가 쓰는 "raw URL이 포함된 traceback"은 정밀하지 않습니다. `HBA-V1-GAP`의 `https://[oops`는 프로그램 프레임만으로는 URL 문자열을 노출하지 않고(그 예시에서 URL이 보인 것은 명령줄 자체가 traceback에 찍힌 탓), 실제 유출은 `https://[secret-tenant-42]/…` 같은 대괄호 호스트 변형에서 `'secret-tenant-42' does not appear to be…`로 호스트 조각만 새어 나옵니다. 방향은 안전 측이라 결함으로 보지 않았지만, 수정 시 회귀 시험은 이 변형을 써야 합니다.
- 이 PASS는 커밋된 HEAD가 아니라 `c59bad7` 위 현재 dirty 작업 트리에 대한 판정이며, 원격 CI·브랜치 보호는 조회하지 않았습니다.
- `check-docs-sot.sh`는 `verification[].command` 문자열을 경로 검사하지 않으므로 `HBA-V1-GAP`의 URL 인자가 검사에 걸리지 않습니다(기존 설계, 이번 교정과 무관).
