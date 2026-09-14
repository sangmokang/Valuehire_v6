# RPS 프로젝트 확보 판정 — HS-11.04b

## 결론

이번 작업은 RPS 화면이나 DB를 쓰지 않고, 조회 결과만으로 프로젝트 확보 상태를 판정하는 순수 코드를 만든다.
부모 계약 브랜치 `task/hs-1104a-rps-project-contract-20260914` 위에 쌓인 stacked 작업이며 부모 PR이 아직 병합되지 않았으므로 단독 main 병합 완료로 주장하지 않는다.

## 판단 근거

RPS 프로젝트는 있으면 재사용하고 없으면 만들어야 하지만, 조회 실패나 이름만 같은 결과를 “없음”으로 착각하면 중복 생성이 생긴다.
그래서 이번 WU는 외부 쓰기 전에 REUSE, CREATE_REQUIRED, AMBIGUOUS, QUERY_FAILED, MAPPING_CONFLICT, RECONCILE_REQUIRED 같은 닫힌 상태를 먼저 계산한다.

- 위험: L2. 순수 코드와 CLI, 합성 테스트만 추가한다. 외부 브라우저·DB·필터·후보 저장은 없음.
- 기준: 부모 계약 브랜치 `task/hs-1104a-rps-project-contract-20260914`.
- 한계: 선행 계약은 Codeaudit PASS였지만 외부 V1 재시도와 V2는 미완료라는 한계를 유지한다.
- 배송 상태: NOT_APPLICABLE. 제품·운영 사이트 쓰기 없음.
- 읽은 정본: strict SKILL, `docs/sot/strict-workflow.md`, `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/verification-commands.md`, `docs/sot/humansearch-rps-project-contract.md`, 사용자 v5 프롬프트.
- 누락: `docs/sot/work-unit-policy.yaml`은 현재 기준 커밋에 없어 NOT_RUN 한계로 기록한다.

## 입력·출력 계약

입력은 JSON 또는 Python 객체로 같은 구조를 가진다.
`position_id`, `customer_id`, `customer_name`, `position_title`, `account_scope`, `observation`, `observation_limit`, `project_links`, `mapped_project_id`, `pending_creation_intent`를 받는다.
문자열 ID는 비어 있으면 안 된다. 조회는 같은 `account_scope`여야 하고, 오류가 없으며, 모든 페이지가 끝났고, 관측 ID·관측 시각·검색 범위·프로젝트 목록이 같은 observation 객체 안에 결합돼야 한다.
최신 부모 계약에서 요구한 `observation_limit`과 `project_links`를 별도 추가 범위로 반영한다.
프로젝트 항목은 `project_id`, 고객 근거, 포지션 근거를 가진다. 이름만 같은 항목은 일치 근거가 아니다.
선택된 프로젝트가 같은 계정의 `project_links`에서 다른 포지션에 이미 연결돼 있으면 재사용하지 않는다.

출력은 `status`, `position_id`, `project_id 또는 null`, `reason`, `plan_only=true`, `allows_write=false`를 가진다.
CLI 출력은 다음 쓰기 단계의 참고 자료일 뿐 쓰기 권한이 아니다.

## 인수 기준

When 매핑 ID가 조회 결과의 같은 고객·포지션 근거와 일치하면 시스템은 REUSE를 반환해야 한다.
counter-AC: 같은 이름의 다른 프로젝트를 대신 선택한다.

When 매핑이 없고 완전한 최신 조회에서 일치 프로젝트가 0개면 시스템은 CREATE_REQUIRED를 반환해야 한다.
counter-AC: 검색 오류나 페이지 누락을 0개로 바꿔 생성한다.

When 매핑 없이 일치 프로젝트가 정확히 하나면 REUSE, 둘 이상이면 AMBIGUOUS를 반환해야 한다.
counter-AC: 첫 행을 무조건 선택한다.

If 매핑 ID가 조회에 없거나 다른 대상이면 시스템은 MAPPING_CONFLICT를 반환해야 한다.
counter-AC: 이름 후보로 자동 대체한다.

If 조회 오류·오래된 관측·페이지 누락·같은 ID의 충돌 내용이 있으면 시스템은 QUERY_FAILED를 반환해야 한다.
counter-AC: 실패를 빈 성공 목록으로 취급한다.

If 미확정 생성 의도가 있으면 시스템은 RECONCILE_REQUIRED를 반환해야 한다.
counter-AC: 응답 유실 뒤 새 생성을 준비한다.

## 검증 계획

RED: 호출 가능한 안전 골격을 만들고, 위 행동 단언이 실제 상태 불일치로 실패하는 pytest를 먼저 커밋한다.
GREEN: 순수 판정 구현과 최소 CLI를 추가한다. Hypothesis로 순서 독립성과 상태의 닫힌성을 검증한다.
검증: `uv run pytest`, `uv run ruff check`, `uv run mypy src`, `git diff --check`, 원칙 검사.

## 비범위와 되돌리기

외부 생성, 필터 업데이트, SQLite 연결, Aside 조작, Chrome 조작, 후보 저장은 하지 않는다.
되돌리기는 이 stacked 브랜치 커밋을 revert하거나 브랜치를 폐기하면 된다. 외부 효과가 없으므로 운영 복구는 없다.
