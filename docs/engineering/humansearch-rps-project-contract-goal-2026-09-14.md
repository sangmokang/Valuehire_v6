# RPS 프로젝트 확보 계약 — HS-11.04a

## 결론

프로젝트가 없으면 생성하고 있으면 조건을 갱신한다는 최신 결정을 실행 가능한 입력·복구 규칙으로 고정한다.
계약 본문은 독립 문서 감사와 V1 수정 후 재검토·V2를 통과했다. 원격 전달·CI는 아직 확인 전이다.
실제 프로젝트 생성·조건 변경·후보 검색은 미실행이다.

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

문서 증거는 Git 제외 `private-reviews/hs-v5-20260914/`에 원문·명령·시각·종료값·지문을 보존한다.
같은 UID가 쓰는 로컬 증거이므로 P17 OS 권한 격리·제품 최종 영수증을 대신하지 않는다.

| 검증 | 결과와 정확한 범위 |
|---|---|
| 원칙 직접 로드·acceptance-principles-check | exit 0, 34/34. 해당 정본 배선만 확인 |
| git diff --check·staged bash verify.sh | 수정 전 후보에서 exit 0; 아래 수정 후 커밋 직전 재실행 |
| brief-lint | 문서 2개 위반 0. 형식만 확인 |
| native Codeaudit | 원 계약 문서 PASS. 이후 V1이 누락을 발견했으므로 최종 근거로 단독 사용하지 않음 |
| 외부 V1 최초 | 조건부 합격 원문을 FAIL로 처리. 필터 쓰기 경계·STOP 재조회·복구/역사·연결 충돌 누락 수정 |
| 외부 V1 재검토 | PASS, session 7f4c6a8b-2107-4d1f-8989-c805bc5c576d. 제공한 사용자 원문 발췌와 계약 텍스트만 대조 |
| 새 맥락 Codex V2 | 원본 63d61e4와 수정 본문 대조, 현재 차단 0. 문서만 APPROVE |
| acceptance-0-5 | exit 1, origin/main fc6beed와 로컬 main f12ea33 불일치. Issue84 범위, 변경·우회 없음 |
| PR·현재 SHA CI·main 병합 | NOT_RUN. 각 단계별 재조회 필요 |
| 제품·라이브 | NOT_RUN. 문서 합격과 구분 |

→ 통과한 범위는 계약 문서의 일관성이다. 원격 CI·필수 병합·실제 동작의 미실행을 대신하지 않는다.

## 적대 검증 로그

V1 원문: `claude-v1-focused.jsonl`, 추출 `claude-v1-focused-review.md`.
session 67957465-1f17-44de-9eb5-0f4b2cd0091e, exit 0이나 필수 수정 지적이 있어 FAIL 판정이다.
재검토 원문 `claude-v1-recheck.jsonl`과 meta, V2 원문 `v2-review.md`를 보존한다.
두 검토의 대상 계약 SHA-256은 `a582c67762035b579b203cc652e7b17622f35e25dfb7a9e8bedac2cd4cd1d59f`다.
V1의 재승인 필요 제안은 최신 사용자 승인과 대조해 기각했다. 복구 입력을 고정하고 임의 자동 되돌림은 제거했다.
문서 변조 실험은 /tmp의 모순 문장을 모델이 발견하는 수동 검토이며 실행 가능한 제품 mutation이 아니다.
초기 무응답 timeout·API credit 부족 진단도 보존한다. 전역 설정 변경 없이 자식 프로세스에서만 API key
환경변수를 제외한 기존 로그인으로 실제 외부 검토를 실행했다. 연결 성공을 감사 PASS로 세지 않았다.

사용자가 제공한 대상 ClickUp 카드를 connector로 읽어 포지션/JD를 확인했다. 운영 입력은 보호 위치에만
저장했으며 계정·기존 프로젝트 연결·실제 UI 필터 의미는 미확인이다. 생성 여부 재승인 대기는 없다.
