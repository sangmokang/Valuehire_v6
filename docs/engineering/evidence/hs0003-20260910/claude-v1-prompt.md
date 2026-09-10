# HS-00.03 Claude V1 독립 적대검증 요청

## 결론

현재 후보가 보호 이름 위장을 거부하면서 정상 다국어 이름을 계속 허용하는지 독립적으로 판정해 주십시오. 사용자가 지금 결정할 사항은 없으며, 읽기 전용 검증 결과만 필요합니다.

당신은 이 한 작업을 검증하도록 파견된 독립 하위 검사자입니다. 별도 계획·브레인스토밍·스킬 호출 없이 아래 계약과 증거를 바로 검토하십시오.

## 판단 근거

첫 예비 실행은 판정 원문 없이 10분을 넘겨 중단됐습니다. 아래 요청은 같은 제품 후보와 계약을 유지하면서 이미 별도로 통과한 장시간 전체 회귀의 반복을 필수에서 제외한 최종 재시도입니다.

> **무엇을** — 원문과 별도의 탐지용 비교 사본을 쓰는 보호 이름 검사 후보를 공격합니다.
> **왜** — 위장을 놓치거나 정상 이름을 막는 두 실패를 함께 찾아야 하기 때문입니다.
> **버린 길** — 전체 Unicode 보안 표준 구현은 이번 한 작업 단위의 범위를 넘으므로 판정 기준에서 제외합니다.
> **대가** — 결합 문자, 양방향 문자, 보이지 않는 문자, 다중문자 위장은 이번 판정으로 해결됐다고 말할 수 없습니다.
> **되돌리기** — 후보 구현을 되돌리고 RED 시험을 유지하면 빠진 동작이 다시 실패하는지 확인할 수 있습니다.

## 기술 상세와 증거

아래 작업트리를 읽기 전용으로 검증하십시오.

- 저장소: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910`
- 기준 HEAD와 RED 시험 커밋: `396cd2b7e92f755d65c34cf103d07b8741259cfc`
- 검증 대상: 위 HEAD 위의 현재 working tree GREEN 후보
- 후보 제품·시험·정본 묶음 지문: `07ce9970f7bce791d2f63cc41786abe64d8ad79a38546ca2a2cacbabc8ab6776`
- 계약: `docs/engineering/humansearch-hs0003-goal-2026-09-10.md`
- 정본: `docs/sot/verification-commands.md`
- 시험: `humansearch/tests/test_hs_0001.py`, `humansearch/tests/test_hs_0001_main_compat.py`, `humansearch/tests/test_hs_0002.py`, `humansearch/tests/test_hs_0002_boundaries.py`, `humansearch/tests/test_hs_0003.py`
- 제품: `scripts/acceptance-hs-kickoff.sh`, `scripts/acceptance-hs-kickoff-mutations.sh`, `scripts/verify/check-hs-kickoff-identities.py`, `scripts/verify/generate-hs-kickoff-confusables.py`, `scripts/verify/hs-kickoff-confusables-17.0.0.json`, `docs/licenses/unicode-license-v3.txt`

목표는 파싱된 workflow 스텝 이름, 검증 정본의 스텝 이름 칸, 처분표 대상 칸에서 전각 또는 Unicode 17.0.0 단일문자 동형 문자로 보호 토큰을 위장한 입력을 거부하는 것입니다. 원문은 승인 값으로 바꾸지 않고 탐지용 비교 사본만 사용해야 합니다. 정상 한글·일본어·아랍어·라틴 문자 이름, 보호 토큰 밖 전각 문장, 정상 이름과 위장 이름의 동시 존재를 구분해야 합니다. `PR #131` 및 `hs-kickoff-other` 경계는 유지해야 합니다. 매핑 파일 누락·손상·메타데이터나 실제 내용 불일치는 실패로 닫아야 합니다. 결합 문자, bidi, 보이지 않는 문자, 다중문자 skeleton 전체는 지원 범위가 아닙니다. 새 의존성과 별도 acceptance 단계는 허용하지 않습니다.

다음 관점에서 산출물을 직접 깨뜨려 보십시오.

1. 기존 ASCII 선택보다 먼저 세 입력 칸을 실제 호출 경로에서 검사하는지 확인하십시오.
2. 항상 허용, 항상 거부, fullwidth 처리 삭제, confusables 처리 삭제, 토큰 경계 삭제, shell이 helper 결과를 무시하는 변경, 데이터 SHA 검사를 우회하는 변경 중 대표 고장 사본이 시험에 잡히는지 확인하십시오.
3. 정상 다국어와 무관한 전각, 정상+위장 동시 존재, `ＰR #131`, `hｓ-kickoff-other`, 같은 mapping count를 유지한 내용 변조를 확인하십시오.
4. 공식 Unicode 17.0.0 원본 SHA `091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a`, 생성물 SHA `687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd`, 선택 수 628, Unicode License v3, 재생성 결과를 대조하십시오.
5. 기존 37개 변이 기대값과 HumanSearch 전체 회귀가 바뀌지 않았는지 확인하십시오.
6. 새 파일이 실제 최종 커밋 후보에 들어갈 수 있는지, 파일·함수 한도 hard600/hard100과 검사 대상 0개 차단을 확인하십시오.

현재 제공된 실행 증거는 다음과 같습니다. 액면 그대로 믿지 말고 필요한 명령을 직접 재실행하십시오.

```text
정조준: 66 passed
G2: ruff 46 files, mypy 46 source files, pytest collected 277 and passed
기존 착수 변이: CHECKED 37, exit 0
원칙 검사: CHECKED 34, VERDICT PASS
원칙 변이: CHECKED 41, VERDICT PASS
저장소 비밀 패턴 검사: tracked file match 없음, .env untracked
파일/함수 예산: 소유 파일 모두 hard600/hard100 통과, 600 통과·601 실패·대상 0개 실패
```

→ 구현 세션이 주장한 결과입니다. Claude V1은 짧은 정조준 시험과 코드 대조로 이 주장을 독립적으로 반박하거나 확인해야 하며, 실행하지 않은 장시간 명령은 제공된 증거로 명시해야 합니다.

최종 후보가 아직 커밋 전이므로 다음 읽기 전용 명령으로 포함 대상과 변경 범위를 확인할 수 있습니다.

```text
git status --short
git diff --check
cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py
```

→ 첫 두 명령은 새 파일 누락과 공백 오류를 찾고, 마지막 명령은 실제 착수 경로의 정상·위장·데이터 오류 15개를 검사합니다.

작업트리를 수정하거나 커밋하지 마십시오. 환경 전체, `.env`, 인증 값이나 원시 비밀을 읽거나 출력하지 마십시오. 원격 push·PR·병합·운영 쓰기는 하지 마십시오. 검증 도구를 실행하지 못하면 `NOT_RUN` 또는 `BLOCKED`라고 정확히 쓰십시오.

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
