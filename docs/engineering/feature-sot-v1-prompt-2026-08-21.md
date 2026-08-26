# Valuehire 주요 기능 SOT — Claude V1 적대검증 요청

이 저장소를 읽기 전용으로 검증해 주십시오. 파일을 수정하거나 생성하거나 삭제하지 마십시오.

## 사용자 요구

현재 저장소의 주요 기능을 분류별로 나누고, 이후 판단이 흔들리지 않도록 각 기능의 정본 문서를
`docs/sot/` 아래에 YAML처럼 명확한 기계 판독 형식으로 체계화해야 합니다.

## 채점 계약 T

1. 주요 기능 선정은 현재 `HEAD`에 존재하는 사람/제품 진입점, 저장소 전체에 강제되는 훅·CI 통제,
   또는 후속 구현에 반드시 필요한 현재 계약 경계에 근거해야 합니다.
2. 과거 goal 문서, 시험 fixture, cache, ignored 개인정보/브라우저 증거, non-HEAD branch는 현재 구현
   기능으로 승격하면 안 됩니다.
3. 카탈로그와 기능 문서는 정확히 1:1이어야 하며, 분류·성숙도·가용성 용어는 닫힌 집합이어야 합니다.
4. 각 기능 문서는 목적, 소유권과 위임, 진입점, 입력, 출력, 오류, 불변식, 경계, 비목표, 검증,
   근거, 변경 절차를 명시해야 합니다.
5. 실행 코드가 없거나 제품 호출자가 시험에만 있으면 각각 `contract_only`/`not_connected` 또는
   `library_only`로 표시해야 하며 운영 배포를 암시하면 안 됩니다.
6. 모든 저장소 상대 경로 근거는 현재 작업트리에 존재해야 하고 URL·절대경로·상위경로 우회는
   허용하지 않아야 합니다.
7. 정상 문서는 통과하되 필수 의미 삭제, 중복 기능 ID, 없는 근거 경로, 기능 문서 0개 변이는
   실패해야 합니다. 검사 대상 0개가 성공해서는 안 됩니다.
8. 변경은 제품 동작을 깨뜨리지 않아야 하고 비밀·개인정보·ignored 증거 본문을 새 문서로 복사하면
   안 됩니다.
9. 기존 `docs/sot/` 정본의 소유권을 중복하거나 충돌시키지 말고, 상세 계약은 해당 정본으로
   명시적으로 위임해야 합니다.
10. 직접 작성 코드는 500줄 이하여야 하며 500줄은 허용하고 501줄은 거부하는 경계를 검토합니다.

## 산출물

- `docs/sot/INDEX.md`
- `docs/sot/verification-commands.md`
- `docs/sot/features/INDEX.md`
- `docs/sot/features/catalog.yaml`
- `docs/sot/features/product/admin-weekly-dashboard.yaml`
- `docs/sot/features/automation/humansearch-auth-surface.yaml`
- `docs/sot/features/automation/humansearch-browser-access.yaml`
- `docs/sot/features/engineering/repository-data-protection.yaml`
- `docs/sot/features/engineering/verification-evidence-system.yaml`
- `docs/sot/features/engineering/change-delivery-guardrails.yaml`
- `scripts/check-docs-sot.sh`
- `docs/engineering/feature-sot-catalog-goal-2026-08-21.md`

## 우선 공격할 반례

- 실제 제품·저장소 진입점이 카탈로그에서 빠졌는지 저장소 전체를 독립적으로 찾아 주십시오.
- 문서가 실행 상태나 배포 상태를 과장하는지 코드의 비시험 호출 경로까지 추적해 주십시오.
- 카탈로그가 문서와 함께 삭제되면 검사가 여전히 통과하는 자기복사형 검증인지 확인해 주십시오.
- 파일 존재만 확인하고 진입점·불변식·검증 명령의 의미나 배선을 확인하지 않는지 공격해 주십시오.
- 기존 SOT와 새 기능 SOT가 같은 규칙을 서로 다르게 소유하는지 확인해 주십시오.
- 정상/변이/제품 회귀/비밀·개인정보 검증 명령을 직접 재현하고 종료값과 실제 검사 수를 확인해
  주십시오. 명령을 실행하지 못한 경우 PASS로 간주하지 마십시오.
- PASS라면 무엇을 어떻게 깨려 했고 왜 실패했는지 반증 기록을 남겨 주십시오.

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
