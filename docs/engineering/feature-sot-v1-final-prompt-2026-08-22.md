# Valuehire 주요 기능 SOT — Claude V1 최종 재검증

읽기 전용 적대검증입니다. 파일을 수정·생성·삭제하지 마십시오.

## T 계약

현재 `HEAD`의 주요 기능을 분류별로 빠짐없이 문서화하고 `docs/sot/features/`를 이후 판단의 정본으로
사용할 수 있어야 합니다. 구현/배포 상태를 과장하면 안 됩니다. 카탈로그와 기능 문서는 1:1이어야 하고
각 기능은 목적, 소유권/위임, 저장소 표면 귀속, 진입점, 입력, 출력, 오류, 불변식, 경계, 비목표, 검증,
근거, 변경 절차를 가져야 합니다. 실제 추적 제품 파일, 이름 있는 CI 단계, CI가 언급하는 저장소 명령,
훅, HumanSearch 계약은 정확히 한 기능에 귀속되어야 합니다. 기존 SOT와 소유권이 충돌하면 안 되고,
외부 URL·없는 경로·비밀·개인정보는 근거로 허용하면 안 됩니다. 검사 대상 0개와 누락·중복 귀속은
실패해야 합니다. 실제 새 표면을 동반한 새 기능은 검사 코드의 기능 ID 수정 없이 추가 가능해야 합니다.

## 검증 대상

- `docs/sot/INDEX.md`, `docs/sot/verification-commands.md`
- `docs/sot/features/INDEX.md`, `docs/sot/features/catalog.yaml`
- `docs/sot/features/{product,automation,engineering}/*.yaml`
- `scripts/check-docs-sot.sh`
- `docs/engineering/feature-sot-catalog-goal-2026-08-21.md`
- 이전 V1 원문: `docs/engineering/feature-sot-v1-fail-verdict-2026-08-22.md`

## 반드시 할 일

1. 이전 V1의 D-1(클린룸·전역 스킬 잠금·억제 만료 누락), D-2(6개 기능 상수), D-3(URL 무검증)를
   현재 파일에서 각각 재현하거나 해소됐음을 증명하십시오.
2. 저장소의 제품 파일·CI 단계·CI 명령·훅·HumanSearch 계약을 독립 수집해 `surface_coverage`와
   대조하십시오. 이름만 있고 실제 경로나 배선이 없는 귀속을 공격하십시오.
3. 아래 명령을 직접 실행하고 종료값·검사 수를 보고하십시오. 다른 장시간 bundle은 실행하지 마십시오.
   - `bash scripts/check-docs-sot.sh`
   - `cd humansearch && uv run --no-sync pytest -q`
   - `git diff --check`
4. 필수 키 삭제, 기능 문서 0개, 미귀속 CI 단계/명령이 실패하고 실제 새 제품 표면과 함께 7번째 기능이
   추가될 수 있는지 검사 코드와 goal의 변이 증거를 양쪽에서 대조하십시오.
5. PASS라면 무엇을 어떻게 깨려 했고 왜 실패했는지, FAIL이면 정확한 `file:line`과 재현 근거를
   남기십시오.

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
