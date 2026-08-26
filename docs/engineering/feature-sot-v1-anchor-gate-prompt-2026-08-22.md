# Claude V1-J — Markdown 앵커 회귀 방지 최종 검증

V1-G가 찾은 잘못된 §10 근거 링크를 단순 교정하는 데서 그치지 않고 `scripts/check-docs-sot.sh`에
Markdown 제목 앵커 존재 검사를 추가했습니다. 현재 공유 작업 트리를 읽기 전용으로 확인하십시오.

1. 정상 `bash scripts/check-docs-sot.sh`는 exit 0과 표면 수 `6/3/33/14/23/29/2/2`를 유지해야 합니다.
2. 격리 사본에서 `HBA-INV-6` fragment를 없는 앵커로 바꾸면 `Markdown anchor does not exist`와
   exit 1이어야 합니다.
3. 외부 URL·절대 경로·없는 파일 검사와 checker 500줄 경계가 유지돼야 합니다.
4. Python 표준 라이브러리만 쓰고 현재 기능 문서의 한국어·숫자·하이픈 앵커를 실제 제목에서
   유도해야 합니다.
5. `git diff --check`가 통과하고 공유 작업 트리는 변하지 않아야 합니다.

첫 줄 `VERDICT: PASS|FAIL`, 한국어 300단어 이내로 결론·증거·잔여 위험을 작성하십시오.
