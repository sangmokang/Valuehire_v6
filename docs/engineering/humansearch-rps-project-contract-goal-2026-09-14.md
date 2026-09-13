# RPS 프로젝트 확보 계약 — HS-11.04a

## 결론

프로젝트가 없으면 생성하고 있으면 조건을 갱신한다는 최신 결정을 실행 가능한 입력·복구 규칙으로 고정한다.
현재는 계약 작성 단계이며 실제 프로젝트 생성·조건 변경·후보 검색은 미실행이다.

## 판단 근거

과거 HS-13의 생성 비범위를 그대로 적용하면 최신 요구를 이행할 수 없다.
반대로 금지 문구만 지우면 검색 오류와 응답 유실이 중복 생성을 만들 수 있어 별도 쓰기 계약이 필요하다.
정본은 [RPS 프로젝트 계약](../sot/humansearch-rps-project-contract.md)이다.

- 위험: L3, 외부 쓰기·계정·원본 저장·계약 변경. 배송 상태 NOT_APPLICABLE(이번 WU는 문서만).
- 사용자 원문: 2026-09-14 v5 §1/6/7. 새 생성 승인을 다시 묻지 않는다.
- 기준: origin/main fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b. main의 별도 f12ea33을 이동하지 않는다.
- 작업 소유: task/hs-1104a-rps-project-contract-20260914, Codex root. 다른 워크트리를 수정하지 않는다.
- 읽은 규칙: 사용자 AGENTS, strict SKILL, coding-principles.md, principles.yaml,
  git-workflow.md, verification-commands.md, humansearch-browser-contract.md,
  humansearch-l0-surface-contract.md, 회수한 HS-00~12 장부와 9월 8일 kickoff.
- work-unit-policy.yaml은 현재 기준에서 누락. 정책 숫자를 임의로 만들지 않는다.
- 코드·시험·CI·DB 변경 없음. 문서 WU라 제품 RED/GREEN은 비해당이며 문서 검토를 수행한다.
- 범위 밖: 외부 호출, 후보 열람, 메시지, 병합, 신규 검사 플랫폼, 암호화 방식 선택.

## 계약·검증 계획

단일 AC: When 최신 프로젝트 생성·기존 필터 변경 결정을 소비할 때 시스템 설계는
입력·정상·실패·경합·재시도·저장·독립 재조회 경계를 모두 명시하고 기존 읽기 경계를 보존해야 한다.
정조준 기준은 계약 A1~A16이며 각 자식 WU로 추적한다.
counter-AC: 생성 호출 금지 문자열만 삭제, 조회 실패=없음, 저장 없는 성공,
사용권만으로 서버 경합까지 해결했다고 주장, 동일 UID 검토를 OS 격리로 표현.

검증: git diff --check, bash verify.sh, 원칙 검사, brief-lint(형식만),
독립 Codeaudit, 다른 엔진 V1, 새 맥락 V2. 문서 결함 주입은 격리 사본에서 핵심 문장 제거 후
독립 검토가 이를 지적하는지 확인하며 런타임 결함 주입과 구분한다.
필수 검사 미충족은 그대로 기록하고 제품 완료를 선언하지 않는다.

## 결정·롤백

무엇을 — HS-11.04를 입력 계약·순수 판정·의도 저장·생성·필터·검색 연결로 분할한다.
왜 — 각 단계가 독립 실패·재검증·되돌리기를 가질 수 있어야 한다.
버린 길 — 한 PR에 브라우저·DB·서치를 모두 넣으면 선행 미충족을 숨기므로 기각한다.
대가 — 준비 계약 이후 실제 구현과 라이브 증거가 별도로 남는다.
되돌리기 — 이 문서 커밋을 revert하고 연결된 후속 작업을 멈춘다. 외부 삭제 없음.

## 현재 환경 관측

2026-09-14 Aside AppleScript 창 2개·탭 5개 읽기 성공. origin만 로컬에서 집계했다.
기존 새 탭의 무변경 JavaScript 계산은 {"probe":2}를 반환했다.
Aside 프로세스의 루프백 진단 listener는 현재 응답하나 /json/version은 403 인증 요구다.
내장 브라우저의 JavaScript 도구는 현재 세션에 노출되지 않았다.
원본 요약은 Git 제외 private-reviews/hs-v5-20260914/preflight.json에 있다.
이 관측은 같은 사용자 권한의 도구 시험이며 제품의 독립 실행기 증거가 아니다.
프로젝트 내부·후보 상세는 읽지 않았고 Chrome 제어 호출은 하지 않았다.

## 검증 장부

작성 중. 실행 명령·시각·종료값·전체 출력·대상 지문은 검증 후 연결한다.
V1/V2/Codeaudit/PR/현재 SHA CI: NOT_RUN. 라이브: NOT_RUN.
