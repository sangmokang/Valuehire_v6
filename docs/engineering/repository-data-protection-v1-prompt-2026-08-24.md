# Repository Data Protection — Claude V1 독립 공격 프롬프트

현재 작업 폴더의 `HEAD`를 검증 대상 SHA로 확정하고 첫머리에 그 전체 SHA, 실행 시각, 작업 폴더, Claude CLI 버전을 적으십시오. 이 검증은 읽기 전용입니다. 파일 수정, 커밋, push, PR, 병합, 배포를 하지 마십시오.

## 독립 검증 목표

`repository-data-protection` 변경이 아래 계약을 실제로 만족하는지 저장소 코드·정본·Git 기록·실행 결과를 직접 대조해 공격 검증하십시오. 작업 보고의 결론을 전제로 삼지 말고 원본 코드를 읽고 필요한 합성 임시 Git 저장소와 고장 사본을 직접 만드십시오. 실제 후보자 개인정보나 실제 자격증명은 읽거나 출력하지 말고 합성 canary만 사용하십시오.

1. `verify.sh`는 기본 모드에서 추적 파일, `VERIFY_SCAN_SOURCE=index`에서 인덱스 blob을 검사합니다. 대상 1개 이상·위반 없음만 `PASS`, 양수 `CHECKED`, exit 0입니다. 비밀/금지 파일은 `FAIL`, exit 1입니다. 패턴 없음, Git 읽기 실패, 대상 0개 등 검사 불성립은 `NOT_RUN`, exit 2입니다. 실제 비밀값은 출력하지 않습니다.
2. `scan-data-exposure.sh history`는 도달 가능한 Git blob을 하나 이상 실제로 열고 크기·금지 경로뿐 아니라 과거 `.csv`, `.tsv`, `.sql` 후보자 개인정보 적재 내용도 검사합니다. 현재 `pii`와 같은 판정 함수를 공유해야 합니다. 커밋 후 삭제된 PII blob도 history와 all에서 exit 1이어야 합니다. 정상 지표 CSV와 schema-only SQL은 통과해야 합니다. 위반 출력은 안전한 경로·blob 지문·컬럼 종류 수·형태만 허용하며 합성 개인정보 원문도 stdout/stderr에 없어야 합니다. blob 0개나 Git 기록의 불완전 읽기는 exit 2입니다.
3. 다음 거짓 합격을 각각 공격하십시오: zero-target 차단 제거, history PII 호출 제거, `CHECKED` 상수 1 위조, 개인정보 본문 출력 주입, CSV만 탐지하고 TSV/SQL 누락, 정상 대조군 오탐, 특정 과거 blob 임의 제외, 현재/과거 PII 판정 복제, 테스트 호출/fixture 제거, Git 열거·blob 읽기 실패의 PASS 접힘.
4. `.github/workflows/verify.yml`과 훅이 공용 검사기에 연결돼 있고 비활성화되지 않았는지 확인하십시오. 관련 원명령과 semantic mutation 검사를 실행하십시오.
5. 직접 작성 코드 파일은 600줄 이하, 함수는 100줄 이하인지 세고, 같은 판정으로 600줄 정상 사본과 601줄 고장 사본을 확인하십시오.
6. `docs/sot/features/engineering/repository-data-protection.yaml`, `docs/sot/verification-commands.md`, goal이 실제 코드의 입력·출력·오류·경계·불변조건과 같은지 확인하십시오.

## 최소 실행 증거

- `bash scripts/acceptance-principles-check.sh`
- `bash scripts/check-docs-sot.sh`
- `bash scripts/acceptance-secret-webhook-vendor.sh`
- `bash scripts/acceptance-hs-a4.sh`
- `bash verify.sh`
- `bash scripts/scan-data-exposure.sh tracked`
- `bash scripts/scan-data-exposure.sh history`
- `bash scripts/scan-data-exposure.sh pii`
- `bash scripts/scan-data-exposure.sh all`
- `bash scripts/acceptance-ci-step-integrity.sh`
- `bash scripts/acceptance-semantic-mutations.sh`
- `git diff --check`

필수 명령의 `FAIL`, `NOT_RUN`, 비정상 종료가 하나라도 남거나 계약 위반·증거 공백이 있으면 `VERDICT: FAIL`로 판정하십시오. 공격이 통과하지 못했을 때도 어떤 고장을 주입했고 어떤 acceptance가 어떤 이유로 실패했는지 전체 증거를 남기십시오. 개인정보 canary 값 자체는 판정서에 복사하지 마십시오.

<!-- lint:skip -->
```text
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
```
