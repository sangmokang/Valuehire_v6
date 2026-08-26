# Claude V1-K — GitHub 앵커 슬러그 경계 최종 재검증

V1-J가 찾은 underscore 제거와 연속 하이픈 축약을 교정했습니다. 현재 공유 작업 트리를 읽기 전용으로
확인하십시오. 정상 구조 검사와 `git diff --check`가 통과해야 하고 checker는 500줄 이하여야 합니다.
격리 사본에서 다음 기대를 직접 재현하십시오.

- `#14-구현not_run-장부`: PASS
- `#14-구현notrun-장부`: FAIL
- `#1층--결론`: PASS
- `#1층-결론`: FAIL
- 존재하지 않는 앵커: FAIL

fenced code의 `#` 줄을 제목으로 세지 않는지도 소스와 간단한 격리 반례로 확인하십시오. 새 결함이
없으면 PASS, 있으면 FAIL입니다. 첫 줄 `VERDICT: PASS|FAIL`, 한국어 300단어 이내로 작성하십시오.
