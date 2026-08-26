# Claude V1-H — malformed target URL known-gap 교정 재검증

읽기 전용으로 현재 저장소를 검증하십시오. 공유 작업 트리를 변경하지 마십시오. 이전 V1-G 세션
`6cdf497c-8ea6-4a7a-ac30-61dc9913bab2`가 찾은 두 결함만 교정됐습니다.

반드시 확인하십시오.

1. 제품 코드는 이번 문서 요청에서 바꾸지 않았고, malformed target URL의 `ValueError`·traceback·raw
   URL·exit 1 결함을 카탈로그, 기능 YAML, 브라우저 SOT가 같은 현재 제한으로 명시합니다.
2. 정상/처리된 경로의 exit 0/2 계약과 알려진 비처리 exit 1을 섞지 않으며, 이 결함을 허용된 안전
   동작이나 해결 완료로 표현하지 않습니다.
3. 결함 제거 조건이 회귀 시험과 좁은 제품 수정의 동시 변경으로 명시됩니다.
4. HBA-INV-6 링크가 실제 §10 앵커 `#10-자격증명과-명령-능력-경계`에 닿습니다.
5. `bash scripts/check-docs-sot.sh`, `cd humansearch && uv run --no-sync pytest -q`,
   `git diff --check`가 통과합니다.
6. 이전 V1-G가 검증한 6/3/14/23/29/2/2 표면 수와 checker 500줄 경계가 유지됩니다.

실제 라이브 포털 접속은 하지 마십시오. 새 결함이나 과장이 있으면 FAIL, 없으면 PASS입니다.
첫 줄은 `VERDICT: PASS|FAIL`이고, 한국어 존칭체로 결론·검증 증거·잔여 리스크를 500단어 이내로
작성하십시오. 건너뜀, 재시도, 추정을 판정 앞부분에 밝히십시오.
