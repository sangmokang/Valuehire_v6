# Repository Data Protection — 다음 Strict L3 공격감사 델타

이 문서는 `docs/engineering/repository-data-protection-strict-l3-followup-prompt-2026-08-25.md`의 대체본이 아니다. 다음 실행자는 그 문서의 **최초 Strict L3 프롬프트와 기존 공격감사 델타를 전문 그대로 먼저 적용한 뒤**, 아래 델타를 마지막에 추가한다. 앞선 요구를 삭제·완화·재해석하지 않는다.

```text
$strict $codeaudit $humanreview

추가 공격감사 델타 — 기존 Strict L3 프롬프트와 2026-08-25 델타를 하나도 삭제하거나 대체하지 않는다.

감사 기준은 이 프롬프트를 포함한 격리 브랜치의 fresh HEAD다. 기준 조상은 fdac401be104bc5d9454401edf0477fb478636dc이며, 이전 보완 커밋 1a3c384fb0d6f6715340a2deb8ec3d373c78e9b5를 보존한다. 시작 즉시 시각·PWD·HEAD·branch·git status와 원본 dirty worktree의 읽기 전용 상태 지문을 기록하고, 실행 도중 HEAD가 바뀌면 증거를 폐기하고 다시 시작한다.

이번 후속에서 다음 결함이 RED로 재현됐다.

1. CSV/SQL 개인정보 낱말 검사가 부분 문자열을 세어 username,mailer를 name,mail 두 종으로 오탐했다.
2. SQL 적재문은 주석·작은따옴표 문자열을 지운 사본에서 찾았지만 개인정보 낱말은 원문에서 세어, 주석이나 문자열에만 name/email이 있고 실제 적재 컬럼은 id/status인 정상 SQL을 오탐했다.
3. INSERT ... INTO ... VALUES 정규식이 세미콜론을 넘어 서로 다른 SQL 문장의 키워드를 결합했다.
4. COPY (SELECT ... FROM ...) TO STDOUT 내보내기를 COPY table ... FROM 적재로 오탐했다.
5. run-acceptance.sh는 PASS:/CHECKED:/VERDICT:만 출력하는 가짜 acceptance를 통과시켰다.

반드시 아래 계약을 독립 재검증한다.

- 개인정보 낱말은 name, email 등 정본 목록의 완전한 식별자 경계만 센다. username, mailer 같은 부분 문자열은 세지 않는다.
- SQL은 주석과 작은따옴표 문자열 내용을 제거한 같은 판정용 사본에서 개인정보 낱말과 적재문을 판정한다.
- INSERT/INTO/VALUES는 줄바꿈·탭을 포함한 공백을 허용하되 단일 세미콜론 경계 안에서만 결합한다.
- COPY는 테이블 대상 뒤의 FROM만 적재로 판정하고 COPY(query containing FROM) TO export는 통과시킨다.
- 현재와 삭제 history는 scan_pii_content 한 함수를 계속 공유한다.
- run-acceptance.sh는 기존 무력화 5종과 PASS/CHECKED/VERDICT 출력 전용 사본을 모두 거부한다. 이 래퍼가 임의의 거짓 로직 전부를 의미론적으로 증명한다고 과장하지 않는다.
- 기존 partial git ls-files, all FAIL/NOT_RUN/CHECKED 집계, 원문 경로 0건, fingerprint 역조회·충돌, exact target collection, 단일 CI 배선, 600/601·100/101 계약을 보존한다.

RED→GREEN 사례는 최소 다음을 포함한다.

- 현재 CSV username,mailer 정상 대조군
- 현재 SQL username,mailer 정상 대조군
- 주석에만 name/email + 실제 unrelated INSERT load 정상 대조군
- 문자열에만 name/email + 실제 unrelated INSERT load의 현재·삭제 history·all 정상 대조군
- 서로 다른 SQL 문장의 INSERT/VALUES 정상 대조군
- COPY query export의 현재·삭제 history 정상 대조군
- 기존 현재·삭제 history·all multiline INSERT 및 COPY FROM 실제 적재 차단군
- fake PASS/CHECKED/VERDICT-only acceptance 거부

mutation은 SQL 판정 삭제, COPY 계약 완화, PII 부분문자열 복귀, SQL raw-word-count 복귀, 세미콜론 횡단 복귀, COPY query export 오인, partial Git fail-open, 원문 경로 복원, CHECKED 고정, history PII 호출 삭제, acceptance 사례 삭제, CI 호출 삭제의 12종이다. 하나라도 살아남으면 FAIL이다. semantic mutations는 기존 5종에 fake-pass-output을 더한 6종을 Git으로 수집한 인수 검사 전량에 주입하고 정확한 대상 수를 비교한다.

예상 로컬 계약은 repository-data-protection CHECKED: 42, semantic mutations CHECKED: 11, hs-a4 CHECKED: 49다. 수치는 실행 전 SOT·코드와 대조하고, 하한이나 PASS 문자열 포함 여부만으로 합격시키지 않는다. 각 원명령의 시각·PWD·HEAD·exit·PASS/FAIL/NOT_RUN 개수·CHECKED·전체 출력을 새 verification log에 기록한다.

check-docs-sot.sh가 실제로 검사하지 않는 catalog와 surface_coverage를 완료 근거로 사용하지 않는다. 이 전역 검증 체계 결함을 이번 범위에서 고치지 않으면 명시적 잔여 REQUEST_CHANGES로 유지한다.

Claude V1, 새 맥락 Codex V2, fresh humanreview를 최종 동일 SHA에서 읽기 전용으로 실행한다. Claude가 정책·크레딧·도구 문제로 실행되지 않으면 V1은 NOT_RUN이며 대체 모델을 Claude라고 기록하지 않는다. 원격 브랜치와 GitHub-hosted Actions가 없으면 P23은 NOT_RUN이다. 원본 dirty worktree의 외부 변경 또는 분기된 ancestry도 공개한다.

push, PR, merge, deploy는 금지한다. Lore 형식의 로컬 커밋까지만 허용한다. FAIL 또는 필수 NOT_RUN이 하나라도 남으면 구현 일부가 로컬 GREEN이어도 완료·APPROVE·병합 가능이라고 보고하지 않는다.
```
