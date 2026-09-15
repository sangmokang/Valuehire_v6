# 착수 목표 — PII SOT 예외 재작성(B안): 3대 결함 수정 (2026-09-15)

## 결론

`task/weekly-ops-pii-sot-exception-20260915-b`(bd1c812)는 절차 위반(읽기 전용 지시 위반)으로 사장님이 B안(폐기 후 재작성)을 결정했다. 내용 자체(사장님이 3차례 적대검증으로 확인)도 높음(high) 결함 3건이 있었다: ① 미승인 `.md` 문서의 개인정보가 통과됨 ② 검토 원장 사유가 자유 텍스트라 작성자 본인이 자가 승인 가능 ③ 로컬(커밋/push) 단계에서 전혀 안 걸리고 CI에서만(이미 원격에 올라간 뒤) 걸림. 이 작업은 bd1c812를 참고하되 그대로 가져오지 않고 `origin/main`(fc6beed) 기준 새 워크트리에서 위 3건을 고친 버전으로 다시 만든다.

## 현재 상태 (직접 확인)

- `origin/main` 기준 `scripts/scan-data-exposure.sh`에는 `PII_APPROVED_DOCS`/`is_pii_approved_doc` 자체가 없다(`grep` 0건) — bd1c812의 기능 자체가 폐기 대상이라 처음부터 다시 설계한다.
- `scripts/scan-data-exposure.sh:206-207`(구 bd1c812 기준): `.md`는 승인 경로가 아니면 전부 `continue` — 검사 대상에서 빠짐.
- `scripts/scan-data-exposure.sh:165-168`: 검토 원장 사유(`reason`)는 형식·출처 검증 없는 자유 텍스트.
- `hooks/pre-commit`·`hooks/pre-push`에 `scan-data-exposure.sh` 호출 0건(`grep` 확인) — `.github/workflows/verify.yml:222`의 CI에서만 실행.
- **사전 실측(오탐 범위 확인, 2026-09-15)**: `origin/main`의 추적 `.md` 113개 중 이메일 패턴 포함 6개, "담당자/이름/연락처" 라벨 포함 29개. 그런데 "라벨 + (사내 도메인이 아닌 이메일 또는 010 전화번호)"를 동시에 요구하면 **일치 0건** — 이 조합이 오탐 없이 기존 문서를 통과시키면서 새 개인정보 유입만 잡는다는 것을 실측으로 확인했다(무작정 "모든 이메일 차단"은 사내 이메일 6개를 즉시 오탐시킨다).

## 근본 원인

P21(`docs/sot/coding-principles.md`)은 "승인 없인 산문 문서에 개인정보를 커밋하지 않는다"고 선언하지만, 그 선언을 지키는 기계 장치가 ①범위(.md 전체가 검사 밖) ②신뢰 경계(원장 사유가 자기 발급 가능) ③시점(로컬이 아니라 CI) 세 군데에서 비어 있었다. P1(기계 장치 없는 원칙은 삭제한다)의 자기 적용에 따르면 이 세 구멍을 메우지 않으면 P21 문구 자체가 장식이다.

## 인수 기준 (EARS)

- **AC-1**: When 승인 목록(`PII_APPROVED_DOCS`) 밖의 `.md` 파일에 "개인정보 라벨(담당자·이름·연락처·후보자·지원자 등)"과 "사내 도메인이 아닌 이메일 또는 010 전화번호"가 함께 있으면, `bash scripts/scan-data-exposure.sh pii`는 그 파일 때문에 exit 1로 실패해야 한다.
  - 검증 명령: `scripts/acceptance-hs-a4.sh`의 `sc_unapproved_md_with_pii`(및 rename/copy 변형) 시나리오, 기대 exit 1.
- **AC-2**: When 승인 목록 문서의 검토 원장(`​.data-exposure-reviewed`) 항목의 사유가 `scan-data-exposure.sh`에 등록된 결정 ID 목록에도 없거나 `docs/sot/coding-principles.md` 본문에도 없으면, 그 문서는 `REVIEWED`로 통과하지 않고 exit 1이어야 한다.
  - 검증 명령: `sc_approved_doc_self_signed_reason`(자유 텍스트 자가 기입) 기대 exit 1, `sc_approved_doc_reviewed`(등록된 결정 ID) 기대 exit 0.
- **AC-3**: When 개인정보 위반이 있는 변경을 커밋하거나 push하려 하면, CI 도달 전에 `hooks/pre-commit` 또는 `hooks/pre-push` 단계에서 이미 차단되어야 한다.
  - 검증 명령: `hooks/pre-commit`·`hooks/pre-push`가 `scan-data-exposure.sh`를 실행 줄에서 호출하는지 정적 확인(새 acceptance 항목) + 임시 저장소에서 실제 pre-commit 훅을 심어 위반 커밋이 거부되는지 실행 확인.

## Counter-AC (가짜 완료 시나리오)

- **counter-AC-1**: "모든 이메일이 있는 `.md`를 차단" — 채택하지 않음. 사내 이메일 6개 파일이 즉시 오탐(위 실측). 라벨+사외 연락처 조합만 차단한다.
- **counter-AC-2**: 승인 문서 사유 검증을 `.data-exposure-reviewed` 파일 안에서만 완결 — 채택하지 않음(원장 파일 자체가 작성자 편집 가능이라 자기서명 우회가 그대로 재현됨). 사유는 반드시 `scan-data-exposure.sh`의 `DECISION_REGISTRY`와 `docs/sot/coding-principles.md` 본문 둘 다에 나타나야 한다.
- **counter-AC-3**: 확장자를 `.MD`·`.Md`로 바꾸거나 심볼릭 링크로 검사를 피하기 — 대소문자 정규화(기존 `tr 'A-Z' 'a-z'` 패턴 재사용)와 `git ls-files`(심볼릭 링크도 blob으로 추적) 특성으로 우회 불가함을 반례로 실행 확인한다.
- **counter-AC-4**: pre-commit/pre-push에 `scan-data-exposure.sh` 호출을 "이름만" 추가하고 실제 실행 줄에서 빠뜨리기 — `hooks/pre-push`의 기존 "실행 동사 뒤 첫 글자가 옵션이 아닐 것" 패턴과 동일한 정적 검사를 pre-commit/pre-push 배선 확인 항목에도 적용한다.

## 정직한 한계 (미리 밝힘)

결정 ID 레지스트리(`DECISION_REGISTRY`)는 `scan-data-exposure.sh` 자체에 하드코딩된 배열이다. 저장소 쓰기 권한이 있는 동일 작성자가 같은 커밋에서 이 배열과 `docs/sot/coding-principles.md`를 함께 고치면 여전히 자가 승인을 통과시킬 수 있다 — **진짜 위조 불가능한 외부 승인**(서명된 커밋, 별도 필수 리뷰어, 저장소 밖 승인 워크플로)은 이 스크립트의 권한 밖이며 별도 인프라가 필요하다(GitHub 브랜치 보호 등). 이번 수정은 "원장 한 줄 몰래 추가"라는 가장 쉬운 우회를 막고, 남은 우회에는 SOT 본문 변경이라는 더 눈에 띄는 흔적을 요구하는 수준까지다.

## 입출력·오류·경계 계약

- `scripts/scan-data-exposure.sh pii`: 입력 없음(현재 git 저장소의 추적 파일과 색인 blob). 출력: 파일마다 `PASS:`/`FAIL:`/`REVIEWED:` 줄, 마지막 요약 `PASS:`/`FAIL:` 한 줄. 종료값 0=합격, 1=위반 발견, 2=인자 오류.
- `hooks/pre-commit`/`hooks/pre-push`: 기존 계약(`docs/sot/hook-contracts.md`) 유지. 새로 추가하는 호출도 같은 fail-closed 원칙(검사 실행 실패 시 차단)을 따른다.

## Harness 게이트 계획

- 게이트 2(RED): `acceptance-hs-a4.sh`에 새 시나리오(AC-1·AC-2 기대값)를 먼저 추가·커밋해 현재 `scan-data-exposure.sh`(원장 관련 미구현)로 실패함을 확인한다.
- 게이트 3(구현): `scan-data-exposure.sh`에 산문 PII 휴리스틱 + 결정 ID 레지스트리, `hooks/pre-commit`·`hooks/pre-push`에 실행 배선을 최소 변경으로 추가한다.
- 게이트 4(검증): `bash scripts/acceptance-hs-a4.sh` 전체 재실행, 출력 숫자 원문 첨부.
- 적대검증 정조준: 오탐(사내 이메일 6개·라벨 29개 파일), 확장자 우회, 원장 자가 기입, 훅 배선 무력화.

## 읽은 SOT

`docs/sot/coding-principles.md`(P1·P11·P20·P21), `docs/sot/verification-commands.md`, `docs/sot/hook-contracts.md`(존재 확인 필요), `.github/workflows/verify.yml`, `hooks/pre-commit`, `hooks/pre-push`, `scripts/scan-data-exposure.sh`, `scripts/acceptance-hs-a4.sh`.

## 비범위

- 이미 알려진 다른 미해결 사안(예: "handoff 브랜치 PII in git" — 다른 브랜치의 기존 노출)은 이 작업 범위 밖이다. 이번 수정은 **앞으로의 신규 커밋**을 막는 장치이지, 과거 이력 전체를 소급 정화하지 않는다.
- push, PR, merge(사람 승인 전 실행하지 않음).
- 저장소 밖 인프라(서명 커밋 강제, 브랜치 보호 필수 리뷰어)는 별도 결정 사안.

## L3 롤백·영향 반경

- 영향 파일: `scripts/scan-data-exposure.sh`, `scripts/acceptance-hs-a4.sh`, `hooks/pre-commit`, `hooks/pre-push`, `docs/sot/coding-principles.md`.
- 롤백: 이 워크트리/브랜치(`task/pii-sot-exception-redo-20260915`)를 병합하지 않고 삭제하면 `origin/main`은 무영향(아직 push 전).
- 데이터 안전: 이 브랜치는 `origin/main` 기준이라 실제 개인정보 파일(`weekly-brief-FY26W38...`)이 없다 — 이 작업은 그 파일을 추가하지 않는다.
