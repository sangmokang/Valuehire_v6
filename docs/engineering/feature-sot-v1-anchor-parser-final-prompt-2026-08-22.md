# Claude V1-M — Markdown 앵커 파서 최종 판정

V1-L의 혼합 닫힘 marker와 backtick info 결함을 교정했습니다. 현재 공유 작업 트리를 읽기 전용으로
검증하십시오. 정상 `check-docs-sot`, checker 500줄, `git diff --check`를 확인하십시오.

격리 fixture에서 반드시 다음을 재현하십시오.

- backtick 블록 안 ` ```~ ` 뒤 가짜 제목: FAIL
- 정상 backtick 닫힘 뒤 실제 제목: PASS
- `` ```py``` `` 같은 backtick 포함 info 문단 뒤 실제 제목: PASS
- tilde 블록 안 ` ``` ` 뒤 가짜 제목: FAIL
- 정상 tilde 닫힘 뒤 실제 제목: PASS
- underscore·연속 하이픈·없는 앵커의 기존 5종 기대 유지

현재 기능 SOT가 쓰는 앵커는 ATX 제목만입니다. Setext·리스트 컨테이너 등 현재 비사용 문법은 새
기능으로 확대하지 말고 잔여 위험으로만 구분하십시오. 지정 반례나 현재 사용 앵커에 결함이 있으면
FAIL, 없으면 PASS입니다. 첫 줄 `VERDICT: PASS|FAIL`, 한국어 350단어 이내로 작성하십시오.
