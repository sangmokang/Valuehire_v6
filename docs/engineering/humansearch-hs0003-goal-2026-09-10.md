# HS-00.03 — 보호 이름을 전각·동형 문자로 위장하지 못하게 한다

## 결론

현재 착수 검사는 정상 이름과 나란히 추가한 전각·키릴 문자 위장 스텝 및 전각 처분 대상을 정상으로 통과시킨다. HS-00.03은 파싱된 이름 칸만 검사하여 이 입력을 거부하고, 정상 한글·다국어 이름과 무관한 전각 설명은 계속 허용한다.

이번 세션은 HS-00.03 한 개 작업 단위만 구현한다. 원격 전송·병합·운영 쓰기는 하지 않으며, 종료 상태는 로컬 커밋과 커밋 후 지문 대조가 끝난 `LOCAL_COMMITTED`로 제한한다.

## 판단 근거와 WU 카드

- 위험 등급: L3. 합격 여부를 결정하는 공유 착수 검사와 Unicode 식별 경계를 바꾼다.
- 기준 SHA: HS-00.02 완료 기록 `f75038830b6680f618c5250b0f04faecac77289d`; 그 안의 구현 SHA는 `69801528d794aabfe8ceb84e1ee073d71ceec442`다.
- 소유: `task/hs-0003-20260910`, `worktrees/hs-0003-20260910`, 세션 `hs0003-20260910`.
- 상태: PLAN. 시작 시 main과 origin/main은 `4379b2ff30afa2e37627e85af0b96920af3a38cd`, HS-00.02 작업트리는 보존돼 있으며 추적 파일은 깨끗하고 준비 자료는 무시된 `artifacts/`에만 있다.
- 사용자 결과: 보호 스텝 이름·정본 스텝 이름 칸·처분 대상 칸에 보호 토큰처럼 보이는 비ASCII 문자를 섞으면 착수 검사가 거부한다.
- 포함: 파싱된 workflow step name, 검증 정본의 step-name cell, 처분표 target cell; U+FF01~U+FF5E 전각 ASCII와 Unicode 17.0.0 혼동표의 단일 비ASCII 코드포인트→단일 보호 ASCII 문자 매핑; 기존 토큰 경계; 정상 한글·다국어·무관한 전각 설명; 정상 이름과 위장 이름의 동시 존재; 데이터 오류.
- 제외: 일반 산문·근거·결론·명령 본문, 전체 문자열 정규화, ASCII `rn`/`m`, 다중문자 매핑, 결합 문자, bidi skeleton, default-ignorable·보이지 않는 문자 전체, U+3000 및 다른 공백 치환, 전체 UTS #39 준수.
- 부작용: 저장소 파일 읽기와 판정 출력뿐이다. 네트워크·브라우저·DB·후보자 데이터·메시지 전송은 0건이다.
- 배송 상태: `NOT_APPLICABLE`. 내부 검증 도구 변경이라 운영 주소·인증·DB·배포·라이브 업무 영수증은 해당하지 않는다.
- 기존 미해결: HS-00.02 고장 사본 37종 중 6종 생존 기록, 과거 인증 값 노출 사고 OPEN, 누적 diff 3,000줄 초과에 따른 후속 전달 방식은 그대로 유지한다.

## 현재 상태와 근본 원인

`scripts/acceptance-hs-kickoff.sh`의 처분표 선택은 파싱된 대상 칸을 ASCII 보호 문자열로 먼저 거른다. workflow/SOT 이름은 원문 1:1 일치만 확인하고, 배선 판정도 ASCII 부분문자열로 보호 스텝을 고른다. 따라서 정상 보호 행을 남긴 채 같은 위장 이름을 workflow와 정본에 함께 추가하거나 위장 처분 행을 추가하면 검사 대상에서 빠진다.

현재 SHA에서 실제 착수 검사 경로를 실행한 결과는 다음과 같다.

```text
baseline: EXIT=0
CHECKED: 12
OK(run-acceptance): scripts/acceptance-hs-kickoff.sh — 판정 12건, CHECKED 12
fullwidth_step_and_sot: EXIT=0
CHECKED: 12
OK(run-acceptance): scripts/acceptance-hs-kickoff.sh — 판정 12건, CHECKED 12
cyrillic_step_and_sot: EXIT=0
CHECKED: 12
OK(run-acceptance): scripts/acceptance-hs-kickoff.sh — 판정 12건, CHECKED 12
fullwidth_disposition_target: EXIT=0
CHECKED: 12
OK(run-acceptance): scripts/acceptance-hs-kickoff.sh — 판정 12건, CHECKED 12
```

→ 정상 사본과 세 위장 사본이 모두 같은 성공 결과를 냈다. 위장 입력이 기존 검사 대상 선택 전에 탈락하는 현재 결함은 `REPRODUCED`다.

## T 계약 — 합격 조건과 가짜 합격 조건

### EARS 합격 조건

1. When 파싱된 workflow step name의 비ASCII 문자 치환 사본이 보호 스텝 토큰을 만들면, 시스템은 원문을 승인된 이름으로 바꾸지 않고 착수 검사를 실패시켜야 한다.
2. When 검증 정본의 step-name cell에 같은 위장이 있으면, 시스템은 workflow와 정본이 서로 같은지와 무관하게 착수 검사를 실패시켜야 한다.
3. When 처분 target cell의 비ASCII 문자 치환 사본이 기존 여섯 보호 대상을 만들면, 시스템은 기존 ASCII 행 선택 전에 해당 위장을 실패시켜야 한다.
4. When 정상 한글·다국어 이름, 보호 토큰 밖 전각 설명, 기존 `PR #131`, `hs-kickoff-other`가 입력되면, 시스템은 이 규칙만으로 거부하지 않아야 한다.
5. When 정상 보호 이름과 위장 이름이 동시에 존재하면, 시스템은 정상 이름의 존재를 면제 사유로 쓰지 않고 위장 이름을 거부해야 한다.
6. If 매핑 데이터가 없거나 비었거나 손상됐거나 선언한 출처·개수·대상 문자 계약과 다르면, 시스템은 빈 정상 결과로 접지 않고 입력/실행 오류로 실패해야 한다.
7. While 기존 HS-00.01·02 시험과 37종 동결 변이 기대값을 실행하면, 시스템은 그 기대값과 단언을 바꾸지 않고 기존 결과를 유지해야 한다.

정조준 인수 명령은 다음 한 개다.

```text
cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py tests/test_hs_0001.py tests/test_hs_0001_main_compat.py tests/test_hs_0002.py tests/test_hs_0002_boundaries.py
```

기대 결과는 수집 0건이 아닌 전체 PASS다. 기존 37종 변이는 `bash scripts/acceptance-hs-kickoff-mutations.sh`, 전체 Python 회귀와 정적 검사는 `bash scripts/acceptance-hs-gates.sh`, 저장소 정본 검사는 `bash verify.sh` 및 `docs/sot/verification-commands.md`의 실제 명령으로 확인한다.

### counter-AC

- 정상 ASCII 보호 스텝이 함께 있으면 위장 스텝을 무시한다.
- workflow와 정본을 같은 위장 문자열로 고치면 1:1 일치라고 통과한다.
- 처분 target을 ASCII로 먼저 선택해 위장 행은 아예 검사하지 않는다.
- raw 이름을 정규화한 뒤 정상 이름으로 승인한다.
- 모든 비ASCII 또는 모든 전각 문자를 거부해 정상 한글·다국어 이름을 막는다.
- `PR #131`을 `PR #13`, `hs-kickoff-other`를 `hs-kickoff`로 오인한다.
- 매핑 파일이 깨졌을 때 빈 매핑으로 계속 실행한다.
- helper 단위 시험만 통과하고 실제 `acceptance-hs-kickoff.sh`에서 호출하지 않는다.
- 항상 허용 또는 항상 거부 구현이 정상/음성 대조군 중 한쪽만 통과한다.

## 입출력·오류·문자 경계 계약

새 판정기의 호출 형태는 다음으로 고정한다.

```text
python3 scripts/verify/check-hs-kickoff-identities.py \
  --kind <workflow-step|sot-step|disposition-target> \
  --token <ASCII 보호 토큰> [--token ...]
```

- 입력: UTF-8 표준입력의 이름/대상 한 줄씩. 토큰은 비어 있지 않은 ASCII 문자열이며 고정 데이터의 보호 ASCII 문자 집합 안에 있어야 한다.
- 출력: 정상은 출력 없음·종료값 0. 위장은 `SPOOF: <kind> line=<1-based> token=<ASCII token>` 한 줄 이상·종료값 1. 입력/데이터/읽기 오류는 `ERROR: ...`를 표준오류에 쓰고 종료값 2.
- 원문: 저장·표시·기존 1:1 대조에는 그대로 둔다. 비교 사본은 위장 탐지에만 쓰며 정상 이름으로 승인하지 않는다.
- 문자 지원: U+FF01~U+FF5E는 코드포인트에서 `0xFEE0`을 빼 ASCII로 대응한다. 그 밖에는 Unicode 17.0.0 `confusables.txt`에서 source 1개·target 1개·source 비ASCII·target이 보호 ASCII 집합인 항목만 쓴다. ASCII source 및 다중문자 target은 제외한다.
- 경계: 보호 토큰 앞뒤가 ASCII 문자·숫자 또는 `_ . / -`이면 그 span은 보호 토큰으로 보지 않는다. 따라서 `PR #131`과 `hs-kickoff-other`는 유지한다. 한글 등 비ASCII 접두·접미는 ASCII 토큰 경계를 침범하지 않는다.
- 위장 판정: 비교 사본에서 경계를 지킨 보호 토큰 span이 생기고 그 span 안에 비ASCII→ASCII 치환이 한 개 이상 있으면 거부한다.
- 빈 입력: 실제 이름/대상 줄이 0개면 종료값 2. 개별 빈 이름의 기존 형식 오류는 기존 검사와 함께 실패한다.

## Unicode 데이터·라이선스·재생성 계약

- 정본 데이터 URL: `https://www.unicode.org/Public/17.0.0/security/confusables.txt`.
- 원본 헤더: Version 17.0.0, Date 2025-07-22 05:49:37 GMT.
- 원본 SHA-256: `091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a`.
- 준비 사본: HS-00.02의 무시된 `artifacts/hs0002-20260910/hs0003-confusables-17.0.0.txt`; 공식 파일과 지문이 같다. 준비 사본 자체는 커밋하지 않는다.
- 라이선스: Unicode License v3. 공식 `https://www.unicode.org/license.txt`의 저작권·허가 고지를 파생 데이터와 함께 저장한다.
- 생성물: `scripts/verify/hs-kickoff-confusables-17.0.0.json`. 생성 데이터이며 직접 작성 제품 코드가 아니다. 그래도 파일 600줄 경계를 넘기지 않는 읽을 수 있는 target별 그룹 형식으로 둔다.
- 생성기: `scripts/verify/generate-hs-kickoff-confusables.py SOURCE`. 원본 지문·헤더를 확인하고 정렬된 JSON을 표준출력으로 만든다. 보호 ASCII 집합, 선택 규칙, 선택 개수와 출처를 메타데이터에 남긴다.
- 재생성: 버전 URL에서 별도 임시 파일을 내려받고 SHA-256을 확인한 뒤 생성기를 실행한다. `/latest/`는 비교에만 쓰며 정본으로 저장하지 않는다.

## 소유 파일과 파일 예산

- 시험 전용: `humansearch/tests/test_hs_0003.py`.
- 제품/검사: `scripts/acceptance-hs-kickoff.sh`, `scripts/verify/check-hs-kickoff-identities.py`.
- 생성/데이터: `scripts/verify/generate-hs-kickoff-confusables.py`, `scripts/verify/hs-kickoff-confusables-17.0.0.json`, `docs/licenses/unicode-license-v3.txt`.
- 정본/기록: `docs/sot/verification-commands.md`, 이 goal, `docs/engineering/evidence/hs0003-20260910/`.
- 새 패키지나 별도 acceptance/CI 단계는 추가하지 않는다. 기존 workflow parser, HS-00.01 fixture, pytest 수집, G2 게이트를 재사용한다.
- 현재 정본 한도는 직접 작성 코드 파일 hard 600줄, 함수 hard 100줄이다. 같은 검사기로 600줄 정상 사본, 601줄 고장 사본, 대상 0개 실패를 검증한다.

## Harness 게이트와 검토 계획

1. Gate 0: 기준 SHA·중복·Issue/PR·소유권·과거 artifact 회수, 현재 위장 반례 RED 원장.
2. Gate 1: 이 문서의 EARS 조건, counter-AC, 입출력·오류·문자 경계 고정.
3. Gate 2: 격리 작업트리에서 실제 acceptance 경로의 새 시험이 빠진 동작 때문에 실패하는지 확인한다. 독립 시험 검토 뒤 시험과 필요한 fixture 선언만 RED 커밋한다.
4. Gate 3: helper·고정 데이터·기존 shell 배선의 최소 변경으로 RED→GREEN을 만든다. RED 시험 기대값은 바꾸지 않는다.
5. Gate 3.5: `acceptance-hs-kickoff.sh`에서 파싱된 세 입력 종류가 helper까지 실제 전달되는 경로를 실행 출력으로 증명한다.
6. Gate 4: 정조준·기존 37종·G2·Ruff·mypy·shell·diff·비밀·원칙·파일/함수 한도와 정상/고장 사본을 확인한다.
7. AUDIT: 독립 Codeaudit, 정상/항상허용/항상거부/핵심배선생략/데이터오류 변이, 실제 Claude V1, 새 맥락 Codex V2를 실행한다. 실행하지 못한 도구를 대신 작성하지 않는다.
8. CHECKPOINT: 감사한 제품 지문과 같은 후보만 Lore 형식으로 GREEN 커밋하고 Git에서 다시 읽어 지문을 대조한다.

## 결정 카드

> **무엇을** — 원문은 보존하고 보호 토큰 span에만 고정 Unicode 데이터를 적용한 비교 사본으로 위장을 탐지한다.  
> **왜** — 전체 이름을 바꾸지 않으면서 전각·그리스·키릴 등 실제 동형 문자를 넓게 잡고, 정상 한글·다국어 이름을 유지할 수 있다.  
> **버린 길** — 전체 NFKC/UTS #39 skeleton은 공백·결합·보이지 않는 문자와 다중문자 span 정책까지 넓어져 이번 한 작업 단위의 계약을 넘는다. 전각+U+0455 손목록은 알려진 Greek/Cyrillic 반례를 남긴다.  
> **대가** — 고정 버전 데이터의 재생성·라이선스 보존이 필요하고, 다중문자·bidi·보이지 않는 문자 공격은 계속 비지원이다.  
> **되돌리기** — GREEN 구현 커밋만 revert하고 RED 시험을 유지해 위장 반례가 다시 실패하는지 확인한다.

## Strict 원칙 직접 로드 장부

- 명령: `sed`로 `docs/sot/coding-principles.md`와 `docs/sot/principles.yaml`을 현재 HS-00.02 기준에서 순서대로 직접 읽었다.
- 시각: 2026-09-10T09:49:57+0900.
- commit/hash: `f75038830b6680f618c5250b0f04faecac77289d`.
- 세션: `hs0003-20260910`.
- 상태: PASS.

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 정본 두 파일과 34개 원칙 장부 및 로컬/CI 배선이 현재 기준 SHA에서 직접 확인됐다. 이 PASS는 개별 제품 기능 구현 완료를 뜻하지 않는다.

첫 기준 회귀는 새 작업트리에 pytest가 없어 종료값 2로 시작하지 못했다. `uv sync --locked --offline`으로 잠금 파일 그대로 15개 패키지를 설치한 뒤 같은 원명령을 재실행하여 51개 PASS를 확인했다. `omx explore`는 Rust 실행기 부재로 종료값 1이었으며, 같은 읽기 범위는 현재 파일 직접 조회와 native subagent 조사로 전환했다.

## 적대 검증 로그

아직 구현 전이다. Codeaudit, Claude V1, Codex V2는 `NOT_RUN`이며 이 절은 실제 실행 결과만 추가한다.

