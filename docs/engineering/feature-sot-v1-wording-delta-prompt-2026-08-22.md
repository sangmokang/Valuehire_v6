# Claude V1-I — known-gap 노출 범위 문구 최종 확인

V1-H의 잔여 리스크 지적만 반영했습니다. 카탈로그, 기능 YAML, 브라우저 SOT의 “raw URL 전체가
traceback에 포함된다”는 표현을 “malformed URL의 호스트 등 URL 조각이 노출될 수 있다”로 좁혔습니다.
현재 공유 작업 트리를 읽기 전용으로 확인하고, 이 문구가 실제 `urlsplit` ValueError 동작보다 과장되지
않으면서 known defect·exit 1·PII 제거 우회 위험을 숨기지 않는지 판정하십시오. 제품 코드는 바뀌지
않아야 합니다. `bash scripts/check-docs-sot.sh`와 `git diff --check`도 실행하십시오. 새 결함이 없으면
PASS, 있으면 FAIL입니다. 첫 줄 `VERDICT: PASS|FAIL`, 한국어 250단어 이내로 작성하십시오.
