/strict P13 자가승인·커버리지·인덱스 결함 3건을 닫는다.

## 시작 좌표 (새 세션이니 먼저 확인하라)

- 저장소: /Users/kangsangmo/Desktop/Valuehire_v6
- 착수 문서(정본): docs/engineering/p13-selfapproval-coverage-goal-2026-09-11.md
  → task/p13-patterns-scope 브랜치에 커밋됨(3ed2e4b). 이 문서를 **먼저 끝까지 읽어라.**
  AC 4개·counter-AC 5종·mutation 13종·WU 5개·결정 카드 3건이 이미 고정되어 있다.
  새로 설계하지 말고 그 계약을 실행하라.

- 작업 대상은 4-PR 체인이다. 순서가 곧 의존성이다:
    #74 task/p13-deletion-guard    (2862664) → main
    #75 task/gate0-loop-proof      (2dfa67e) → #74
    #77 task/ci-execution-proof    (8fe9dec) → #75
    #78 task/p13-patterns-scope    (3ed2e4b) → #77
  각 브랜치 워크트리: worktrees/<브랜치 이름에서 task/ 뗀 것>/

## 먼저 확인할 것 — 미푸시 커밋이 쌓여 있다

네 브랜치 모두 원격보다 앞서 있다: 2 / 6 / 14 / 19 커밋.
직전 세션이 로컬 커밋까지만 하고 끝냈다는 뜻이다.
`git rev-list --count origin/<브랜치>..<브랜치>` 로 직접 세어 확인하고,
push 는 사용자 승인 전에 하지 마라. 체인이라 force-with-lease 가 필요하다.

## 무엇을 닫는가 — Codex 적대검증 2라운드 높음 3건 (전부 재현 완료)

C1  삭제자가 같은 커밋에 은퇴 승인을 써 넣으면 233줄 검사가 통과한다 (실측 rc=0)
C2  비밀 규칙 25개 중 21개가 카나리에 연결되어 있지 않다 (실측 커버 4/25)
C3  탐지 축소 검사가 인덱스가 아니라 작업트리를 읽는다 (staged 2줄 / worktree 4줄 → 통과)

세 건은 같은 실수다 — 검사기는 보호하면서 **그 검사기가 읽는 대상**을 안 지켰다.
하나씩 고치면 네 번째가 나온다. 착수 문서의 WU 순서를 지켜라.

## 작업 순서 (착수 문서 WU 그대로)

WU-1  AC-3  인덱스 읽기 + 카나리 감소 차단      → #78 워크트리
WU-2  AC-2  capability manifest + 커버리지 검사기 + 배선  → #78
WU-3  AC-1  은퇴 승인 선재성 + 항목 스키마 검증  → #74 (체인 앞이라 이후 재정렬 필요)
WU-4  AC-4  독립 oracle 교차 대조               → #78
WU-5        mutation 13종 + 격리 clone 전체 스위트

WU-1 을 먼저 해야 WU-2 의 커버리지 판정이 올바른 입력을 본다.
거꾸로 하면 커버리지 검사가 작업트리를 읽고 초록을 낸다.

## 이 저장소에서 반복해서 당한 함정 (같은 실수 금지)

1. 변조가 파일에 실제로 적용됐는지 `diff -q` 로 확인하지 않으면 "생존"이 거짓 신호다.
   이번 세션에만 두 번 났다.
2. 격리 clone 은 HEAD 를 받는다. 지금 고치는 중인 검사기·고정물을 **작업트리 사본으로
   덮지 않으면** 어긋난 조합을 시험하게 되고 변이가 전부 생존한다.
3. 검사 실행 불가(rc=126·127·2)를 "차단됐다"로 세면 구현 0줄에서도 초록이 난다.
4. 체인 재정렬 충돌을 "둘 다 유지"로 자동 해소하면 **제거 의도가 되살아나고** 항목 뒤
   필드가 잘린다. 해소 후 반드시 `bash scripts/verify/check-mechanism-registry.sh` 재실행.
5. 명부(mechanism-registry) target 은 **활성 줄 맨 앞의 실행 배선**이어야 한다.
   메시지 문자열은 "죽은 target" 으로 거부되고, 값에 큰따옴표가 들어가도 거부된다.
6. 카나리 고정물은 자기 비밀 스캔에 걸린다. 쪼갠 위치가 패턴의 공백 허용 구간이면
   분할이 무의미하다. 변수명에 SECRET 같은 키워드를 쓰면 훅이 자기 코드를 막는다.

## 검증 명령 (추측 금지 — 이 저장소의 실제 명령)

  bash verify.sh                                          비밀 스캔
  bash scripts/verify/check-mechanism-registry.sh         장치 명부 대조
  bash scripts/verify/check-workflow-deletion.sh          워크플로 삭제 감시
  bash scripts/verify/check-secret-detection-regression.sh 탐지력 축소 감시
  bash scripts/acceptance-p13-deletion.sh                 은퇴 차단 인수 검사
  bash scripts/acceptance-secret-detection-regression.sh  탐지 축소 인수 검사
  bash scripts/acceptance-verify-ac-m.sh                  명부 계약 인수 검사

Makefile 은 없다. `make red-ledger` 를 시도하지 마라.
게이트 0 은 `bash scripts/session-status.sh` 이고 인수 검사 30여 개를 순차 실행해
**11분** 걸린다. 필요하면 백그라운드로 돌려라.

## 알려진 외부 문제 (내 코드 문제가 아니다)

2026-09-09 05:05 이후 GitHub Actions 가 시작조차 못 한다(startup_failure).
손대지 않은 main 에서 수동 실행해도 같다. 사용량 한도가 유력하고
https://github.com/settings/billing 에서 확인해야 한다.
CI 판정이 필요한 단계에서는 NOT_RUN 으로 기록하고 로컬 증거로 진행하라.

## 하지 말 것

- push·PR 생성·병합: 사용자 승인 전 금지
- 허용목록 브랜치(task/secret-allowlist-line-scope, 55커밋) 재정렬: 이번 체인 병합 후
- suppressions.yaml 에 새 유예 추가로 문제를 덮는 것: 개인정보·보안 결함은 유예 후보가 아니다
- 착수 문서의 AC 를 새로 설계하는 것: 이미 고정됐다

## 완료 조건 (착수 문서와 동일)

기존 F1/F2 RED 가 수정 후 GREEN · 정상 acceptance 전부 통과 ·
positive canary 전부 탐지 · negative canary 전부 미탐지 ·
suppression owner/reason/expiry 검증 · mutation 13종 전부 차단 ·
쓰기 가능한 격리 clone 에서 동일 결과 · Codex 재리뷰에서 3건 해결 확인 · 새 높음 0건
