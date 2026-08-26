# 다음 작업 프롬프트 — 검증 체계 보강 (2026-08-27)

출처: Codex 적대 감사(VERDICT: REQUEST_CHANGES)가 제안한 프롬프트 + Claude 재검증에서 추가한 정정 1건.
아래 코드 블록을 그대로 새 세션에 붙여 넣는다.

## Claude 가 추가한 정정 (Codex 원안에 없던 것)

**WU-0 을 맨 앞에 넣었다.** Codex 원안은 브랜치를 현재 상태 그대로 두고 시작하는데, 그러면 AC9(제품 테스트 감소 금지)가 처음부터 실패한다.

```
내 브랜치 pytest 파일   8개
origin/main pytest 파일 15개
```
→ 테스트가 삭제된 것이 아니라 브랜치가 main 보다 뒤처진 것이다(PR #38 이 7개를 추가했다). 리베이스하지 않고 AC9 를 걸면 "7개가 사라졌다"는 거짓 실패가 나온다. 그래서 리베이스를 첫 단위로 못박는다.

---

```text
/strict

ValueHire v6 검증 체계 보강 작업입니다. 위험등급 L3로 수행해 주세요.

작업 위치:
- 저장소: /Users/kangsangmo/Desktop/Valuehire_v6
- 작업트리: /Users/kangsangmo/Desktop/Valuehire_v6/.claude/worktrees/history-scan-failclosed
- 현재 브랜치: task/history-scan-failclosed
- 시작 HEAD 기대값: 743f276806208ba7585c03799d300d63c13d3fbe
- 비교 기준 origin/main: c59bad7b160c473cda5545e76e6fa6bcc711a7ea

권한:
- 위 작업트리 안의 로컬 코드·테스트·문서 수정은 허용합니다.
- 바깥 기본 체크아웃은 수정하지 마세요.
- push, PR 생성·수정, 병합, 배포, GitHub 설정 변경은 금지합니다.
- 파괴적 실증은 mktemp 아래 격리 사본에서만 수행하세요.
- 시작과 종료의 git status --porcelain을 원문으로 남기세요.
- 새 의존성 도입은 하지 말고, 필요하면 별도 선택지로 보고하세요.

시작 계약:
1. docs/sot/coding-principles.md와 docs/sot/principles.yaml을 직접 읽으세요.
2. bash scripts/acceptance-principles-check.sh를 실행하고 실패하면 하위 원인 분해 후 같은 원명령을 재실행하세요.
3. CLAUDE.md, AGENTS.md, verification-commands.md, mechanism-registry.yaml, verify.yml, pre-push 및 관련 검사기 역사를 회수하세요.
4. 현재 브랜치의 acceptance-history-scan-failclosed.sh가 CI와 명부에 없는 상태를 RED로 고정하세요.
5. goal 문서에 EARS AC, counter-AC, 입출력·오류·경계 계약, 롤백과 영향 반경을 먼저 작성하세요.

WU-0 (다른 무엇보다 먼저):
- 이 브랜치는 origin/main(c59bad7)보다 뒤처져 있습니다. pytest 파일이 main 15개 대 브랜치 8개인데,
  이는 삭제가 아니라 PR #38이 추가한 7개가 아직 없기 때문입니다.
- 리베이스하지 않고 AC9를 걸면 "테스트 7개 사라짐"이라는 거짓 실패가 납니다.
- 따라서 origin/main 위로 리베이스하고, 리베이스 직후 기존 검사 전부를 다시 돌려
  회귀 0건을 확인한 뒤에 WU-1로 넘어가세요.
- 리베이스 후 pytest 수집 파일 수와 테스트 함수 수를 출력해 기준선으로 고정하세요.

설계 제약:
- verify.yml 전체를 mechanism-registry.yaml에서 생성하지 마세요.
- verify.yml은 사람이 읽고 수정하는 파일로 유지하세요.
- 표시 이름이 아니라 안정된 job ID와 step ID를 판정 기준으로 쓰세요.
- 필수 실행 조건과 필수 스텝만 담는 작은 manifest를 두고 workflow와 양방향 대조하세요.
- YAML 구조를 파싱해 검사하세요. grep/awk로 실행 의미를 추정하지 마세요.
- manifest에 없는 acceptance 스크립트와, manifest에는 있지만 workflow에 없는 항목을 모두 실패시키세요.
- actionlint는 선택적 보조안으로만 평가하고 이번 작업에 새 의존성으로 추가하지 마세요.
- 저장소 내부 장치만으로 같은 커밋에서 검사기와 장부를 함께 약화하는 공격을 완전히 막았다고
  주장하지 마세요. 외부 필수 검사·승인 규칙은 NOT_RUN 또는 별도 운영 AC로 분리하세요.
  (실측: 이 계정은 개인 비공개 저장소라 branch protection·ruleset API가 HTTP 403입니다.)

필수 AC:
AC1. When 손대지 않은 workflow를 검사할 때, 시스템은 exit 0과 양수 CHECKED를 출력해야 합니다.
AC2. When push/pull_request를 제거하고 workflow_dispatch만 남길 때, 구조 검사는 실패해야 합니다.
AC3. When 필수 step을 삭제하거나 주석 처리하거나 비활성 job으로 옮길 때, 구조 검사는 실패해야 합니다.
AC4. When 필수 run에 `|| true`, `; true`, `if: false`, 항상 거짓 YAML anchor, continue-on-error를
     붙일 때, 구조 검사는 모두 실패해야 합니다.
AC5. When 허용된 표시 이름을 다른 step에 복사할 때, 예외 권한이 이동하지 않아야 합니다.
AC6. When acceptance 본문을 `exit 0`, `true`, 빈 파일, `검사했습니다`, `VERDICT: PASS`,
     `PASSWORD 검사 없음`, 가짜 PASS/CHECKED 출력으로 교체할 때, 검증 체계는 모두 실패해야 합니다.
AC7. When 새로운 scripts/acceptance-*.sh가 추가되면, CI·pre-push·manifest에서 명시적으로
     실행 또는 제외되지 않는 한 실패해야 합니다.
AC8. When 등록 항목이 실제 파일·job·step·정확한 명령과 맞지 않으면 실패해야 하며
     검사 대상 0개도 실패해야 합니다.
AC9. When 제품 pytest 파일 또는 수집 케이스가 승인된 기준보다 감소하면, 이유와 명시적
     기준 갱신 없이는 실패해야 합니다. (기준선은 WU-0의 리베이스 직후 값으로 고정합니다.)
AC10. When 관리자 JavaScript의 API 호출 또는 화면 표시를 고장 내면, 최소 한 개의 실행 기반
      시험이 실패해야 합니다. 새 런타임 의존성이 필요하면 구현을 강행하지 말고 별도
      결정 카드로 올리세요.
AC11. verification-commands.md의 단계 목록은 실제 workflow와 구조적으로 일치해야 하며
      수동 숫자만 적지 마세요.

counter-AC:
- registry, manifest, 생성 결과를 함께 약화해 diff 0을 만드는 경우
- workflow 실행 조건 자체를 없애 검사가 시작되지 않는 경우
- step 표시 이름만 허용 이름으로 위조하는 경우
- run 앞부분은 유지하고 뒤에 오류 무시 명령을 붙이는 경우
- acceptance가 아무 동작 없이 합격 문구만 출력하는 경우
- 새 acceptance가 pre-push에서만 실행되고 CI에는 없는 경우
- 테스트 1개만 남겨 수집 수 > 0 조건을 만족하는 경우
- checker가 파일 0개를 읽고 합격하는 경우

검증:
- 각 AC마다 정상 사본 통과와 고장 사본 실패를 모두 실행하세요.
- RED→GREEN 뒤 핵심 검사기 한 줄을 일부러 고장 내 mutation을 실행하고 다시 원복하세요.
- origin/main 대조군과 작업 브랜치 결과를 분리해 기록하세요.
  (대조군이 통과하지 않으면 그 실험은 결론을 낼 수 없습니다. NOT_RUN으로 남기세요.)
- 전체 pytest 수집 파일 수와 테스트 함수/케이스 수를 출력하세요.
- V1은 실제 Claude CLI로 독립 실행하고, V2는 새 Codex 맥락에서 V1의 명령과 file:line을 재현하세요.
- V1 또는 V2가 실행되지 않으면 PASS로 끝내지 마세요.
- 기존 검사기 전부, pre-push 경로, CI 구조 검사, 문서 일치 검사를 마지막에 다시 실행하세요.

완료 보고:
첫 줄은 VERDICT: PASS|FAIL|NOT_RUN.
결론 → 판단 근거 → 기술 상세와 증거 원문 순서로 작성하세요.
결론에는 전문용어를 쓰지 마세요.
결함마다 심각도, 원인, 사업 영향을 적으세요.
```

---

## 이 프롬프트가 겨냥하는 결함 (근거)

| AC | 겨냥하는 결함 | 근거 |
|---|---|---|
| AC2·AC3·AC4 | 워크플로 무력화 4종이 현재 main 에서 전부 통과 | 2026-08-27 재현, 대조군 통과로 실험 성립 |
| AC5 | 스텝 표시 이름만 바꾸면 예외 권한이 따라옴 | `check-ci-step-integrity.sh` 예외 목록이 이름 문자열로 판정 |
| AC6 | 래퍼가 `VERDICT: PASS`·`PASSWORD` 한 줄에 통과 | `run-acceptance.sh` 가 `PASS` 를 부분 문자열로 셈 |
| AC7 | 새 인수 검사가 pre-push 에만 잡히고 CI·명부에 없음 | Codex F1 |
| AC9 | 제품 테스트를 1개만 남겨도 관문 통과 | `acceptance-hs-gates.sh:54` 가 `collected < 1` 만 검사 |
| AC10 | 관리자 화면 시험이 JS 문자열 존재만 확인 | Codex F3 |
| AC11 | 검증 지침이 CI 20단계라는데 실제 24스텝 | Codex F4 |

## 반려된 제안 — 기록으로 남긴다

Claude 가 제안한 **"verify.yml 을 명부에서 생성하는 산출물로 내린다"**는 Codex 가 반려했다.

> **무엇을** — 생성 대신 필수 실행 조건·필수 스텝만 담는 작은 manifest 를 두고 workflow 와 양방향 대조한다.
> **왜** — 생성기 자체가 새 단일 실패점이 되고, matrix·secrets·복합 run 블록처럼 명부 스키마로 표현하기 어려운 요소가 있으며, 워크플로를 사람이 읽고 고칠 수 없게 된다.
> **버린 길** — 전체 생성물화(Claude 원안). 드리프트는 원천 차단되지만 위 대가가 크다.
> **대가** — manifest 와 workflow 두 곳을 함께 유지해야 하고, 양방향 대조 검사기가 필요하다.
> **되돌리기** — manifest 와 대조 검사기를 지우면 지금 구조로 돌아간다.
