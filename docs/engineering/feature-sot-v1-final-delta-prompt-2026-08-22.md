# Valuehire 기능 SOT — Claude V1-E 최종 판정

읽기 전용입니다. 이전 V1-D가 보고한 F-1R(둘째 줄 name, 대시 뒤 여러 공백, flow mapping 우회)과
F-4(goal의 fail-closed 과장)가 현재 모두 닫혔고 기존 T 계약이 유지되는지 판정하십시오.

직접 실행할 명령은 `bash scripts/check-docs-sot.sh`, `cd humansearch && uv run --no-sync pytest -q`,
`git diff --check`입니다. 또한 임시 사본에서 아래 유효 YAML 세 변형을 각각 추가해 구조 검사가 모두
종료값 1로 거부하는지 확인하십시오. 원본은 수정하지 마십시오.

```yaml
      - run: true
        name: Synthetic second-line name
      -   name: Synthetic spaced dash
          run: true
      - {name: Synthetic flow mapping, run: "true"}
```

Ruby Psych 구조 파싱 실패·검사 대상 0개·기능 표면 개수 회귀·500줄 초과가 없어야 합니다. 새 결함이
있으면 FAIL, 없으면 공격과 실패 이유를 포함해 PASS를 주십시오. 1,200단어 이내로 쓰십시오.

[출력 형식 — 반드시 지킬 것]
첫 줄은 VERDICT: PASS|FAIL.
그다음 결론 → 판단 근거 → 기술 상세와 증거 원문 순서로 쓴다.
결론에는 전문용어를 쓰지 않는다. 판단 근거에는 선택·버린 해석·틀리면 깨지는 것을 쓴다.
전문용어는 첫 등장 문장 안에서 풀고, 출력·코드·표 바로 아래에는 → 해석을 붙인다.
file:line에는 줄의 역할을 붙인다. 결함마다 심각도, 원문 제목, 원인, 사업 영향을 쓴다.
설계 지적은 무엇을/왜/버린 길/대가/되돌리기 다섯 줄로 쓴다.
건너뜀·미확인·실패 후 재시도와 추정을 판정 앞부분에 밝힌다.
증거를 생략하지 말고 무엇을 어떻게 깨려다 실패했는지 반증 기록을 남긴다.
한국어 존칭체로 쓰되 내용을 축소하거나 초등학생 비유를 쓰지 않는다.
