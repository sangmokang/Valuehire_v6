# Strict 공통 실행 계약 (SOT)

최종 갱신: 2026-09-10

이 문서는 `$strict`가 Codex와 Claude에서 동일한 판정·순서·승인 경계를 사용하도록 고정하는 운영 정본입니다. 원칙의 수치와 Work Unit의 필드는 각각 `coding-principles.md`, `principles.yaml`, `work-unit-policy.yaml`이 소유합니다. 이 문서는 그 값을 복제하지 않고 실행 순서와 플랫폼 공통 의미만 소유합니다.

## 1. 플랫폼 패리티

Codex와 Claude는 같은 입력 계약, EARS acceptance criteria(AC), counter-AC, WU 경계, 검증 상태, 증거 형식, 승인 경계를 사용합니다. 엔진 이름과 호출법은 어댑터 차이이며, 플랫폼별 차이는 독립 검증 엔진의 순서뿐입니다. 두 전역 스킬 사본이 이 문서와 충돌하거나 서로 다르면 조용히 선택하지 말고 `BLOCKED`로 기록한 뒤 동기화합니다.

## 2. 적응형 Strict 프롬프트

`$strict`는 매번 고정된 장문 템플릿을 복사하지 않고 위험등급과 변경 표면에 맞춰 필요한 섹션만 생성합니다.

- L0: 동작 불변 여부, 범위, 자체 점검, 중단 조건
- L1: 목표·근거·출처·반례·한계
- L2: 계약·Type·counter-AC·WU·RED→GREEN·회귀·독립 검증
- L3: 전체 게이트, V1→V2, 데이터 안전·롤백·영향반경·최종 SHA·운영 readback

등급을 낮추기 위해 섹션을 생략하지 않습니다. 해당 없음은 `NOT_APPLICABLE`, 미실행은 `NOT_RUN`, 권한 밖은 `BLOCKED`로 구분합니다.

## 3. 기능 구현의 정본 순서

다음 순서를 기본값으로 사용합니다. 의존성이 없는 단계는 병렬화할 수 있지만, 선행 계약과 검증이 끝나기 전 다음 상태로 승격하지 않습니다.

1. Issue/goal과 범위·성공 기준·중단 조건 고정
2. 기존 DB/API·마이그레이션·제약·권한·호출자를 조사
3. DB/API 계약 고정: 스키마, 입력, 출력, 오류, 경계, 멱등성
4. Type과 런타임 검증 고정 — Type은 DB/API 계약의 표현이며 별도 권위나 새 P-원칙이 아님
5. EARS AC와 counter-AC(반례·실패·권한·동시성·재시도) 고정
6. Work Unit으로 분해하고 각 WU의 falsifiable claim과 완료 조건 고정
7. 기대 동작을 먼저 시험해 RED를 확인하고 로컬 RED 커밋 보존
8. 최소 구현 후 첫 GREEN 커밋
9. 회귀시험·작은 적대검증·경계/한도 검사
10. WU 완료 커밋, 전체 Strict, 읽기 전용 codeaudit, 통합 적대검증
11. 위 로컬 게이트와 clean 상태가 모두 PASS인 뒤에만 push 및 Draft/Ready PR 생성
12. PR의 현재 HEAD SHA를 기준으로 CI·GitHub 검증, Owner review, squash merge
13. 승인된 배포 후 실행 중 SHA·DB/API 결과·독립 readback 확인

RED는 로컬 증거이며 원격 PR의 완료 증거가 아닙니다. 현재 `pre-push`가 acceptance 실패를 차단하므로 RED 직후 push/PR을 위해 `--no-verify`를 사용하지 않습니다.

## 4. 코드량과 변경 크기

파일·함수·PR 크기 한도는 `docs/sot/coding-principles.md`의 P11만 읽습니다. `$strict` 프롬프트나 이 문서에 숫자를 복제하지 않으며, 초과 시 분할·삭제·기존 유틸 재사용을 먼저 검토하고 우회하지 않습니다.

## 5. 자동화와 사람 승인

자동 실행은 로컬 검증과 되돌릴 수 있는 checkpoint까지입니다. push, PR 생성, merge, deploy, 외부 데이터 쓰기는 현재 정본상 수동 승인 경계이며 자동화했다고 주장하지 않습니다. 원격 CI는 반드시 PR의 최종 SHA를 읽어 귀속합니다.

## 6. LLMOps와 운영 증거

실제 LLM 호출·평가셋·회귀 하네스가 존재하는 작업에서만 LLMOps 게이트를 적용합니다. 실행 가능한 평가셋이 없으면 `NOT_IMPLEMENTED` 또는 `NOT_RUN`으로 기록하며, 일반 CI·HumanSearch 테스트를 LLMOps 실행 증거로 오인하지 않습니다. 운영 데이터 쓰기와 독립 readback 없이는 `PRODUCTION_VERIFIED`를 주장하지 않습니다.

## 7. 필수 반례

다음 주장은 금지합니다: RED 상태의 원격 PR, `--no-verify` 우회, Type만 맞는 가짜 계약, mock/fixture를 운영 증거로 부르기, 기대값을 구현에 맞춰 GREEN 만들기, stale SHA의 CI를 현재 변경 검증으로 부르기, P11 초과를 숨기기, 실행하지 않은 V1/V2·LLMOps를 PASS로 표기하기.

## 8. 드리프트 검증

Strict 실행 시작 시 `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/work-unit-policy.yaml`, 이 문서를 직접 읽고 관련 acceptance/hook/CI 배선을 실행합니다. Codex와 Claude의 전역 `SKILL.md`는 이 공통 계약을 읽는 동일한 사본이어야 하며, 동기화 후 `cmp`와 `skill-creator`의 `quick_validate.py`로 각각 검증합니다.
