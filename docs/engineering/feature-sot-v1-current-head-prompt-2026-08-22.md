# Claude V1-G — current HEAD HumanSearch L1 정합화 최종 검증

읽기 전용으로 현재 저장소를 독립 검증하십시오. 공유 작업 트리 파일, 브랜치, index, 설정을 변경하지
마십시오. 변이는 `mktemp -d` 아래의 격리 복제본에서만 수행하고 종료 전에 삭제하십시오.

현재 HEAD는 `c59bad7...`이며, 이전 V1-F의 `29ce9da...` 기준선 뒤에 HumanSearch 사람인 L1 일회 관측
코드가 fast-forward로 추가됐습니다. 검증 대상은 현재 작업 트리의 기능 SOT 변경 전체입니다.

반드시 확인할 주장:

1. `bash scripts/check-docs-sot.sh`가 현재 HEAD 표면을 `features=6`, `categories=3`,
   `product_files=14`, `ci_steps=23`, `ci_commands=29`, `hooks=2`, `contract_surfaces=2`로 완전 귀속하고
   종료값 0을 냅니다.
2. `humansearch-auth-surface`가 순수 분류 책임을 유지하면서 L1 observer라는 현재 비시험 소비자를
   사실대로 밝힙니다.
3. `humansearch-browser-access`가 `implemented/local_runtime`으로서 `saramin-markers.json`, `_cdp.py`,
   `observe.py`를 정확히 소유하고, 한 번 읽기·단일 target·exact origin·계약 port·한 줄 개인정보 제거
   출력·exit 0/2를 규정합니다.
4. 브라우저 SOT가 현재 구현된 L1과 여전히 미구현인 검색·입력·재시도·브라우저 생명주기·D1/C1·
   잡코리아·LinkedIn을 모순 없이 구분합니다.
5. `cd humansearch && uv run --no-sync pytest -q`, ruff, mypy 및
   `bash scripts/acceptance-hs-gates.sh`가 통과합니다.
6. 격리 사본에서 다음을 각각 깨면 구조 검사가 종료값 1을 냅니다: 새 추적 제품 파일 미귀속,
   marker 계약 미귀속, 이름 있는 CI 단계 미귀속, 두 번째 workflow 추가, 기능 문서 삭제, 존재하지 않는
   근거 경로. 실제 새 추적 제품 표면과 함께 7번째 기능을 추가하면 검사 코드 변경 없이 종료값 0이어야
   합니다.
7. 외부 URL·절대 경로·symlink·중복 키·기능 ID 상수 같은 자기완결 우회가 없고 checker가 500줄
   이하입니다.
8. `git diff --check`가 통과하고 공유 작업 트리가 실행 전후 동일합니다.

결함이 하나라도 있으면 `VERDICT: FAIL`, 없으면 `VERDICT: PASS`입니다. 낮은 심각도라도 숨기지
마십시오. 900단어 이내로 쓰십시오.

[출력 형식 — 반드시 지킬 것]
첫 줄은 `VERDICT: PASS|FAIL`.
그다음 결론 → 판단 근거 → 기술 상세와 증거 원문 순서로 씁니다.
결론에는 전문용어를 쓰지 않습니다. 판단 근거에는 선택·버린 해석·틀리면 깨지는 것을 씁니다.
결함마다 심각도, 원문 제목, 원인, 사업 영향을 씁니다.
설계 지적은 무엇을/왜/버린 길/대가/되돌리기 다섯 줄로 씁니다.
건너뜀·미확인·실패 후 재시도와 추정을 판정 앞부분에 밝힙니다.
파일과 줄을 인용할 때 그 줄의 역할을 함께 적습니다.
한국어 존칭체로 씁니다.
