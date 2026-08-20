# V1 독립 적대검증 요청

현재 저장소 `/Users/kangsangmo/Desktop/Valuehire_v6`의 미커밋 변경을 읽기 전용으로 검증하십시오. 파일을 수정하거나 생성하지 마십시오.

구현 결론을 전달받지 않았습니다. 채점 기준 T와 원시 산출물만 드립니다.

## T와 산출물

- T: `docs/engineering/strict-principles-contract-goal-2026-08-20.md`
- 원칙 정본: `docs/sot/coding-principles.md`
- 기계 장부: `docs/sot/principles.yaml`
- 핵심 검사기: `scripts/acceptance-principles-check.sh`
- 반례 시험: `scripts/acceptance-principles-mutations.sh`
- 로컬 배선: `hooks/pre-push`
- CI 배선: `.github/workflows/verify.yml`
- 장치 명부: `docs/sot/mechanism-registry.yaml`
- 명부 검사기: `scripts/verify/check-mechanism-registry.sh`
- 스킬 계약 검사기: `scripts/verify/check-strict-principles-skills.sh`
- 판정 장부 검사기: `scripts/verify/check-strict-verdict-ledger.sh`
- Codex Strict: `/Users/kangsangmo/.codex/skills/strict/SKILL.md`
- Claude Strict: `/Users/kangsangmo/.claude/skills/strict/SKILL.md`

## 반드시 직접 실행·공격할 것

1. 정본의 P1~P22, `1-B-1~5, V-1~5가 정확히 32개인지와 장부 문구가 일치하는지 독립 확인하십시오.
2. 장부 누락·빈 파일·YAML 오류·ID 삭제/중복/미지 ID·빈 mechanism·잘못된 path/check/stages·존재하지 않는 경로가 거짓 PASS를 만들 수 있는지 공격하십시오.
3. 검사기 자기 제외, 검사 대상 0개, pre-push 글로브 약화, 명시적 실행 줄 제거가 탐지되는지 공격하십시오.
4. CI 단계의 주석/echo/조건부 실행, `if`, `continue-on-error`, `|| true`, `if exists`, 여러 줄 우회가 탐지되는지 공격하십시오.
5. `bash scripts/acceptance-principles-check.sh`, `bash scripts/acceptance-principles-mutations.sh`, `bash scripts/acceptance-verify-ac-m.sh`, `bash scripts/verify/check-mechanism-registry.sh`, `bash scripts/verify/check-strict-principles-skills.sh`, `bash verify.sh`를 직접 실행하십시오.
6. 직접 작성 코드의 500줄 PASS / 501줄 FAIL과 검사 대상 0개를 재현하십시오.
7. 두 Strict 파일의 공통 블록이 바이트 동일하고, 메모리를 정본으로 보지 않으며 현재 파일 직접 로드 실패를 PASS로 만들지 않는지 확인하십시오.
8. Codex는 `G=Codex → V1=Claude → V2=Codex`, Claude는 `G=Claude → V1=Codex → V2=Claude`만 다른지 확인하십시오.
9. V1 FAIL을 최종 PASS로 기록하거나 V1 FAIL 뒤 V2 NOT_RUN인 fixture가 거부되는지 확인하십시오.
10. 테스트가 구현을 복사한 상시 참인지, 입력을 실제로 변조하지 못한 반례가 있는지 공격하십시오.
11. 현재 작업트리 변경 범위를 읽고 기존 기능 파손, 고아 배선, CI에서만 발생할 환경 차이를 찾으십시오.
12. 단순 PASS는 무효입니다. 무엇을 어떤 방법으로 깨려 했고 왜 실패했는지 반증 기록과 실행 전체 결과를 남기십시오.

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
