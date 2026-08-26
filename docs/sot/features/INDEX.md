# ValueHire 주요 기능 정본

최종 갱신: 2026-08-22

이 폴더는 “현재 저장소가 무엇을 할 수 있고, 무엇은 아직 할 수 없는가”의 단일 진입점이다.
기능 목록은 [`catalog.yaml`](catalog.yaml), 기능별 상태·경계·검증 명령은 카탈로그가 가리키는
각 YAML 문서가 소유한다.

## 읽는 순서

1. `catalog.yaml`에서 범주와 기능 ID를 고른다.
2. 해당 기능의 `document`를 연다.
3. `maturity`와 `availability`를 먼저 확인한다.
4. `authority`가 지정한 세부 정본만 추가로 연다.
5. 기능을 바꾸기 전에 `change_protocol.required_updates`와 `verification`을 실행한다.

## 상태 해석

- `implemented`: 현재 `HEAD`에 실행 코드 또는 저장소 강제 장치가 있다.
- `contract_only`: 허용·금지·후속 조건만 정해졌고 현재 `HEAD`에 실행 구현이 없다.
- `local_runtime`: 로컬에서 사람이 명령으로 실행할 수 있으나 운영 배포가 아니다.
- `library_only`: 함수는 구현됐지만 비시험 제품 소비자나 배포 진입점이 없다.
- `repository_control`: 커밋·push·CI 또는 수동 검증 단계에서 저장소 변경을 판정한다.
- `not_connected`: 정책 또는 계약만 있고 제품 호출 경로가 없다.

`implemented`는 “운영 중”을 뜻하지 않는다. 운영 연결 여부는 각 문서의 `boundaries`와
`non_goals`를 함께 읽어야 한다.

## 정본 소유 원칙

이 폴더는 기능의 분류, 현재 구현 상태, 기능 경계, 호출점, 검증 방법을 소유한다. 기존 상세 정본이
있는 경우 전문을 복제하지 않고 `authority.delegates`로 소유 경로를 지정한다.

충돌 시 적용 순서는 다음과 같다.

1. 현재 사용자의 명시 지시
2. `docs/sot/coding-principles.md`
3. 기능 YAML이 `authority.owns`로 선언한 범위
4. 기능 YAML이 `authority.delegates`로 지정한 상세 정본
5. 날짜가 붙은 `docs/engineering/` 기록
6. 기본 관례

서로 다른 문서가 서로 다른 범위를 소유하므로, 위 순서는 같은 주장에 충돌이 생겼을 때만 적용한다.
코드와 정본이 충돌하면 코드가 맞다고 추정하지 말고 정본과 코드를 같은 변경에서 정합화한다.

## 파일 형식

`*.yaml`은 YAML 1.2와 JSON 양쪽에서 읽을 수 있는 JSON 호환 부분집합으로 작성한다. 앵커, 태그,
중복 키, 암묵적 날짜 형식은 사용하지 않는다. 이 제한은 별도 YAML 라이브러리 없이 Python 표준
`json` 모듈로 구조를 검증하기 위한 것이다.

기능 문서 필수 키는 다음과 같다.

```text
schema_version
feature.id / name / category / maturity / availability / purpose
feature.authority / surface_coverage / entrypoints / inputs / outputs / errors
feature.invariants / boundaries / non_goals / verification / evidence
feature.change_protocol
```

`surface_coverage`는 완전성 장부다. `tracked_product_files`는 현재 추적 제품 파일 전량,
`ci_steps`는 `.github/workflows/verify.yml`의 이름 있는 검사 단계 전량, `ci_command_paths`는 그 워크플로가
언급하는 저장소 검사 명령 전량, `hooks`는 `hooks/`의 실행 파일 전량, `contract_surfaces`는 구현 전에도
독립 기능 경계를 만드는 HumanSearch 계약 전량을 기능 하나에 정확히 한 번 귀속한다. 이 목록은 기능 ID
상수와 대조하지 않고 실제 저장소 표면에서 역으로 유도한다.

## 주요 기능 선정 기준

다음 중 하나를 만족하는 현재 `HEAD`의 기능만 카탈로그에 둔다.

- 사람이 실행하거나 제품 코드가 호출하는 진입점이 있다.
- pre-commit, pre-push, CI 중 하나에서 저장소 전체 변경을 강제하는 결과 단위다. 개별 검사 스크립트는
  별도 기능으로 늘리지 않고 같은 결과를 보장하는 상위 기능의 `surface_coverage`에 귀속한다.
- 다음 구현이 반드시 따라야 하는 현재 기능 계약이며 미구현 경계를 명시한다.

역사 기록, 시험 fixture, 캐시, worktree, 미병합 브랜치, 후보자 산출물, 단독 helper는 주요 기능으로
세지 않는다.

## 변경 절차

- 기능을 추가·삭제·분할하면 `catalog.yaml`과 해당 기능 YAML을 같은 변경에서 수정한다.
- 구현 상태가 바뀌면 `maturity`, `availability`, `entrypoints`, `boundaries`, `verification`을 함께
  갱신한다.
- 제품 파일, 이름 있는 CI 단계, 훅, HumanSearch 기능 계약을 추가·삭제하면 담당 기능의
  `surface_coverage`를 같은 변경에서 갱신한다. 귀속되지 않거나 두 기능에 중복 귀속되면 검사는 실패한다.
- 상세 정본을 새로 만들면 기존 규칙을 복제하지 말고 `authority.delegates`에 소유권을 연결한다.
- `bash scripts/check-docs-sot.sh`와 기능 문서가 지정한 검증 명령을 실행한다.
- 운영 연결, 외부 발송, 개인정보 처리, 브라우저 능력 확대는 별도 L3 변경과 오너 승인을 요구한다.
