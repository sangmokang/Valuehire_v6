# 배송 파이프라인 정본 — Issue → PR → CI → Merge

이 문서는 "다음 세션이 답으로 참조해야 하는" 것만 담는다. 측정 근거와 사건 경위는
`docs/engineering/delivery-pipeline-retrospective-2026-09-10.md`(적대검증 정정 2판).

## 1. 사슬의 빈 칸 3개 (현재 상태)

| 칸 | 상태 | 근거 |
|---|---|---|
| Issue → PR | **정상.** 1:1 연결 관행 정착 | `#71→#74` · `#72→#77` · `#73→#75` · `#76→#78` |
| PR → CI | **부분 무효.** `인수 검사 0-5 (push · CI 연결)` 이 병합 전 PR 에서 안 돈다 | `verify.yml:136` `if: github.ref == 'refs/heads/main'` |
| CI → Merge | **강제 없음.** required check 를 걸 수 없다 | rulesets·branch protection 둘 다 `403 Upgrade to GitHub Pro` |
| Merge | **사람 1명.** `USER_MERGE_ONLY` | strict 계약 §5 |

**required check 403 은 "구조적 제약"이 아니라 요금제 선택이다.** 403 응답이 해제 조건
두 개(Pro 전환 / public 전환)를 직접 명시한다. "구조"라고 부르면 대체 방어를 안 만들게 된다.

**병합 전 검증이 완전하지 않다는 사실을 전제로 판단한다.** PR 이 초록이어도
31스텝 중 1건은 건너뛴 상태다. `READY TO MERGE` 를 보고할 때는
"N스텝 중 M 통과, 건너뜀 K건(사유)"를 함께 적는다.

## 2. 지표를 낼 때 지키는 규칙

같은 데이터로 8월 대 9월 PR 크기가 **11.9배 축소도, 0.49배 역전도** 나왔다(2026-09-10 실측).
그러므로 비교 수치를 낼 때 다음을 숫자 옆에 반드시 함께 적는다.

1. **표본 선택 규칙** — "열린 것만"은 생존 편향이다. 열린 PR 은 "병합에 실패해 살아남은"
   집합이므로 평균이 전체보다 높다(2026-08: OPEN 3,150 vs 전체 2,262 vs 병합분 1,399).
   비교하려면 **전수** 또는 **같은 상태끼리**.
2. **측정 기준** — stacked PR(base ≠ main)의 `additions+deletions` 는 "앞 브랜치 대비 증분"이다.
   main 대비로 재려면 `git diff --numstat main...origin/<head>`. 최대 13.5배 차이가 났다.
3. **측정 시각** — 적체 지표는 조사 중에도 변한다(이 조사가 스스로 PR 을 +1 시켰다).

## 3. "없다"를 주장할 때 (전수 검색 계약)

2026-09-10 에 "오케스트레이터 전수 검색 0건"이 세 곳에서 뚫렸다.

- 확장자 목록(`.sh/.py/.ts`)이 `.rb`·`.mjs` 를 통과시켰다
- `-maxdepth 3` 과 `-not -path "./worktrees/*"` 가 **두 번째 워크트리 디렉터리**
  `.claude/worktrees/` 를 우연히 가렸다 (제외 패턴은 여기를 못 가리킨다)
- 정규식이 `adversarial-review`(하이픈)를 요구해, `adversarial` 만 있는 대상 파일을
  **범위를 무한히 넓혀도 원리적으로 못 잡았다**

**규칙: "0건"을 주장하기 전에 그물이 알려진 양성 사례를 잡는지 먼저 시험한다(양성 대조군).**
정규식은 눈으로 읽지 말고 돌린다.

## 4. 병렬 세션 4규칙

한 저장소에서 창을 여럿 띄우면 작업이 소실되거나 중복된다(2026-09-05 소실 1회·중복 1회,
2026-09-09 중복 1회 — 두 세션이 같은 CI 장애를 4분 간격으로 각자 조사).

1. **창마다 워크트리 이름을 선점한다.** 다른 창은 그 이름을 쓰지 않는다.
2. **`git stash` 금지.** 스택이 창끼리 공유된다. 꼭 필요하면
   `git stash push -u -m "<고유태그>"` + SHA 확보 + `apply`(pop 아님).
3. **main 병합 권한은 한 창이 독점한다.**
4. **공유 저장물(메모리·`docs/`)을 쓰기 전 `ls` 로 중복을 확인한다.**

## 5. 이미 만들어 둔 것 (새로 만들기 전에 확인)

WU 루프 실행체를 "0줄부터 만들자"고 하기 전에 아래를 먼저 본다. **둘 다 미병합이다.**

| 위치 | 내용 | 성격 |
|---|---|---|
| `origin/deliver/finding-runner` → `tools/strict/finding-runner.mjs` (233줄) | 적대검증·계약·런타임 지적을 받아 재현 명령을 `spawn` 으로 실행하고 REPRODUCED/BLOCKED/NOT_REPRODUCIBLE/NOT_TESTED/UNRESOLVED 를 확정 | 실행 드라이버 |
| `origin/task/work-unit-rebased` (PR #37) → `docs/sot/work-unit-policy.yaml` + `scripts/verify/*.rb` | WU 정책 정본(`claims_per_unit: 1`, `max_units_per_pr: 5`, `max_branch_lifetime_hours: 48`, `final_gates`) | 문서 동기화 검사기 (정책 준수는 미강제) |

## 6. 배송 병목의 성격

제작이 아니라 **병합**이 병목이다. 검사기를 하나 더 만드는 것보다 열린 PR 하나를 닫는 것이
가치 있는 구간이다. 이 판단이 바뀌는 조건: 열린 PR 이 10건 이하로 내려가고 병합이
주 1회 이상 일어날 때.
