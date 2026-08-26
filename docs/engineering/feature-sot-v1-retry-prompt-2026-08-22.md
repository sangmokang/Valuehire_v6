# Valuehire 주요 기능 SOT — Claude V1 재시도

읽기 전용 적대검증입니다. 파일을 수정·생성·삭제하지 마십시오.

## T 계약

현재 `HEAD`의 주요 기능을 빠짐없이 분류하고 `docs/sot/features/`에 기계 판독 가능한 정본으로
고정해야 합니다. 과거 문서·시험 fixture·ignored 증거·non-HEAD 코드는 구현 기능이 아닙니다.
실행 코드가 없으면 `contract_only/not_connected`, 시험 밖 호출자가 없으면 `library_only`여야 하며
운영 상태를 과장하면 안 됩니다. 카탈로그와 기능 문서는 정확히 1:1이어야 합니다. 각 기능에는 목적,
소유권/위임, 진입점, 입력, 출력, 오류, 불변식, 경계, 비목표, 검증, 근거, 변경 절차가 있어야 합니다.
경로는 현재 저장소에 존재해야 하고 기존 SOT와 소유권이 충돌하면 안 됩니다. 검사 대상 0개, 필수
의미 삭제, 중복 ID, 없는 근거 경로는 실패해야 합니다. 비밀·개인정보를 복사하면 안 됩니다.

## 검증 대상

- `docs/sot/INDEX.md`, `docs/sot/verification-commands.md`
- `docs/sot/features/INDEX.md`, `docs/sot/features/catalog.yaml`
- `docs/sot/features/{product,automation,engineering}/*.yaml`
- `scripts/check-docs-sot.sh`
- `docs/engineering/feature-sot-catalog-goal-2026-08-21.md`

## 반드시 할 일

1. 저장소의 비시험 제품 진입점과 훅·CI 진입점을 독립 검색해 기능 누락을 찾으십시오.
2. 여섯 기능의 상태·진입점·위임·근거를 실제 코드와 대조하십시오.
3. 아래 세 명령만 직접 실행하십시오. 장시간 acceptance mutation bundle은 재실행하지 말고 goal에
   기록된 결과와 스크립트 원문을 대조하십시오.
   - `bash scripts/check-docs-sot.sh`
   - `cd humansearch && uv run --no-sync pytest -q`
   - `git diff --check`
4. 필수 키 삭제와 기능 문서 0개 반례가 검사 코드상 거부되는지 정적으로 확인하십시오.
5. PASS라면 무엇을 깨려 했고 왜 실패했는지, FAIL이면 정확한 `file:line`과 재현 근거를 쓰십시오.

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
