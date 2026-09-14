# 밀린 산출물 회수와 관문 급소 수리 — goal (2026-08-27)

> 등급 L1(이 문서 자체는 계획·분석) · 실행 WU는 L2~L3 · 기준 HEAD `3094eef`
> 읽은 SOT: `docs/sot/coding-principles.md` · `docs/sot/git-workflow.md` · `docs/sot/verification-commands.md` · `docs/sot/mechanism-registry.yaml`
> **이 저장소에 `docs/sot/30-strict-mode-contract.md`·`31-strict-recurrence-ledger.md`·`package.json` 은 없다**(실측). strict SOT-30 §2의 `npm run wt`·`npm run check`·`strict:gate` 는 이 레포에 배선되지 않았으므로 core 계약만 적용하고 워크트리는 `git worktree add`, 검증은 `docs/sot/verification-commands.md` 의 실제 명령을 쓴다. R4 재발 원장은 이 레포에 없으므로 `docs/engineering/` 의 과거 판정서를 대체 근거로 인용한다.

## 상위 목표 (1문장)

**완성됐는데 git 밖에 있는 작업을 되찾고, 그것을 통과시킬 관문이 가짜 합격을 막게 만든다.**
성공 신호 1개: 미추적 산출물 0건 + 가짜 합격 스크립트가 관문에서 종료값 1로 거부됨.

## 현재 상태 (실측 · 추측 금지)

### 사실 1 — 완성된 코드가 git 밖에 있다 (가장 심각)

```
?? tools/strict/checkpoint-gate.mjs
?? tools/strict/checkpoint-js-scan.mjs
?? tests/checkpoint-gate.test.mjs
?? tests/checkpoint-gate-mutation.test.mjs
?? docs/sot/features/            ← SOT 디렉토리 통째로 미추적
 M scripts/check-docs-sot.sh     ← +410줄 (기능 정본 카탈로그 검사)
 M docs/sot/humansearch-browser-contract.md  (+85/-38)
```

제품 코드·시험·**SOT 정본**이 커밋되지 않은 채 5일 방치. `docs/sot/coding-principles.md` P15①(작업트리가 커밋 상태와 일치할 때만 배송)과 정면 충돌한다.

### 사실 2 — 문서 왕복이 26개 쌓였다

미추적 39건 중 **26건이 `feature-sot-v1-*`/`v2-*` 프롬프트·판정서**다. 한 작업의 검증 왕복이 파일 26개로 남았다. 이 저장소는 이미 문서 22,971줄 대 제품 코드 636줄이다.

### 사실 3 — 관문이 가짜 합격을 통과시킨다 (재현됨)

```
scripts/verify/run-acceptance.sh:47   pass_lines=$(grep -c 'PASS' "$out")
```
→ 출력에 `PASS` 글자가 1회 있으면 합격. `echo "PASS: forged"; exit 0` 스크립트가 종료값 0으로 통과함을 실행으로 확인(2026-08-27).
CI에서 이 관문을 거치는 검사 **26개**. 거치지 않는 독립 방어선은 2개(`verify.sh`, `scan-data-exposure.sh`).

```
scripts/verify/check-ci-step-integrity.sh:85-96
```
→ 막는 것은 `if` 조건부·`continue-on-error`·`echo bash *.sh`·`bash -n *.sh` 4종뿐. `run: true` 는 통과함을 실행으로 확인.

```
scripts/acceptance-semantic-mutations.sh:68-73
```
→ 무력화 표본 5종(`exit 0`/`true`/no-op/빈 파일/`echo "검사했습니다"`)이 **전부 PASS 글자를 안 찍는 형태**다. 관문이 그것만 잡는다.

### 사실 4 — 좀비 codex 작업이 이어받기를 막는다

`task-mt2fczj5-uvnd1j` 가 132시간째 `running`. 이후 Resume 요청 2건이 각각 2초·1초 만에 실패(`Task ... is still running`).
**단, 그 좀비가 파일을 남기지는 않았다** — 좀비 로그 마지막은 `2026-08-21T04:09:23Z`(KST 13:09)이고 미추적 파일 수정 시각은 `08-22 00:33~01:51`로 11시간 뒤다. 좀비가 만들던 `docs/engineering/audit-six-wu-goal.md` 는 현재 존재하지 않는다.

### 사실 5 — 급소 수리 범위는 처음 추정보다 작다 (자기 정정)

2026-08-27 1차 조사에서 "판정 형식 불명 3개"라 적었으나, 실제로 돌려 보니 `acceptance-0-5.sh` 는 `PASS: 0-5 완료 — …` 를 찍고 관문을 정상 통과한다. `acceptance-ci-step-integrity.sh:31` 도 `printf 'PASS: %s — %s\n'` 을 갖고 있다. 1차 조사의 grep 이 줄머리 앵커(`^\s*`)를 써서 조건문 뒤 출력들을 놓쳤다. **"반나절이라는 추정에 근거가 없다"는 지적은 유지하되, 형식 불일치의 규모는 축소 정정한다.**

## 근본 원인

배송의 마지막 구간(커밋 → PR → 병합)만 사람 손에 있고 기계 강제가 없다. `docs/sot/git-workflow.md:23` 이 자동 병합을 금지한 것은 의도된 설계지만, **커밋조차 안 된 산출물을 잡는 장치는 없다.** P15①은 `make ship` 을 전제하는데 이 레포에는 `make` 도 `package.json` 도 없다.

## 상태 갱신 — 2026-08-27 01:40 실측 (계획보다 현실이 앞섰다)

이 문서를 쓰는 사이 저장소가 움직였다. **작성 시점 가정 3개가 이미 무효다.**

| 원래 WU | 갱신된 실제 상태 | 근거 |
|---|---|---|
| WU-0 좀비 취소 | **불필요** — `task-mt2fczj5-uvnd1j` 가 active 목록에서 사라졌고 새 rescue `task-mtabcm85-ylxk5e` 가 Task 모드로 정상 기동(1m37s, phase=verifying) | `codex-companion.mjs status --all` |
| WU-1b SOT 회수 | **완료** — `8720a41` "기능 정본 카탈로그를 도입하고 검사기가 그 구조를 강제하게 한다" (13파일 +1,895/-38, 2026-08-27 01:34, author=acceptance) | `git show --stat 8720a41` |
| WU-1a 코드 회수 | **진행 중** — checkpoint 4파일이 staged(`A `) 상태, 커밋 직전 | `git status --short` |

→ **다른 세션이 지금 이 저장소에서 작업 중이다.** staged 영역을 건드리면 그 작업을 망친다. 아래 WU는 그 사실을 전제로 재편했다.

## WU 분해 (AC 1개 = 검증 1개 = 커밋 1개)

**레인 구분** — 같은 파일을 건드리지 않는 WU만 병렬이다. 실측으로 판정했다:
`scripts/acceptance-semantic-mutations.sh` 가 `run-acceptance.sh` 를 참조하므로(grep 확인) **A레인 내부는 순차 필수**. C레인은 `.github/workflows/` 만 건드리고 A레인과 겹치지 않는다(`git diff --name-only | grep -c workflows` = 0).

| WU | 레인 | AC (EARS) | 검증 명령 | 등급 | 선행 |
|---|---|---|---|---|---|
| **WU-1a** | — | If checkpoint 4파일이 staged 이면, then 시험 통과 확인 후 커밋해야 한다 | `node --test tests/checkpoint-gate*.test.mjs` exit 0 | L2 | (타 세션 진행 중 — 침범 금지) |
| **WU-2a** | **A①** | If 인수 검사가 종료값 0인데 판정 형식이 계약과 다르면, then 관문이 종료값 1로 거부해야 한다 | 위조 표본 `echo "PASS: forged"; exit 0` → 관문 exit 1 | L2 | WU-1a |
| **WU-2b** | **A②** | If 무력화 표본에 "PASS 글자를 찍는 위조"가 없으면, then 6번째 표본으로 추가하고 차단돼야 한다 | `acceptance-semantic-mutations.sh` 6종 × 전량, CHECKED 증가, exit 0 | L2 | **WU-2a** (같은 파일 참조 — 병렬 불가) |
| **WU-2c** | **C** | If CI 스텝이 `run: true`·`printf PASS` 같은 no-op 이면, then 무결성 검사가 거부해야 한다 | 반례 워크플로 → `check-ci-step-integrity.sh` exit 1 | L2 | WU-1a (A레인과 **병렬 가능**) |
| **WU-1c** | **D** | If `feature-sot-v1/v2-*` 문서가 미추적이면, then 최종본만 남기고 폐기안을 제시해야 한다 | `git status --short \| grep -c '^??'` 가 5 이하 | L1 | 무의존 (**전부와 병렬**) |
| **WU-3** | **D** | If 충돌 PR(#14·#15·#29)이 열려 있으면, then 산출물 확인 후 닫기안을 제시해야 한다 | `gh pr list` CONFLICTING 0건 | L1 | 무의존 (**전부와 병렬**) |
| **WU-4** | **E** | If `~/.codex/config.toml` 의 `pre_tool_use` 가 `enabled=false` 이면, then 원인 확인 후 오너 승인으로만 되돌려야 한다 | 오너 판단 기록 + 전후 해시 | L3(외부 환경) | 무의존 (**이 레포 밖**) |

### 실행 순서도

```
[타 세션] WU-1a (staged 커밋)  ← 침범 금지, 완료 대기
                │
        ┌───────┴───────┐
   A레인 (순차)      C레인 (독립)
   WU-2a 관문           WU-2c CI무결성
     ↓ (같은 파일)
   WU-2b 표본

   D레인 (언제든 병렬): WU-1c 문서정리 · WU-3 PR정리
   E레인 (레포 밖):     WU-4 codex 설정
```

### V1 반영 게이트 (사장님 지시 2026-08-27)

**codex 적대 검증(`task-mtabcm85-ylxk5e`) 결과를 받기 전에는 A·C레인 코딩을 시작하지 않는다.**
검증 결과가 위 AC를 뒤집으면 AC부터 고치고 시작한다. D레인(문서·PR 정리)은 코드와 무관하므로 대기 없이 진행 가능하다.

## 예외 케이스 표 (R1 — 표에 없는 상황은 임의 판단 금지, 중단 후 표 갱신)

| 상황 | 처리 |
|---|---|
| 좀비 취소가 실패한다 | **명시적 중단.** 강제 종료 시도 금지 — 프로세스 정체 미확인 |
| checkpoint-gate 시험이 실패한다 | **명시적 중단.** 미완성 코드일 수 있으므로 커밋하지 않고 보고 |
| `docs/sot/features/` 가 기존 SOT 계약과 충돌한다 | **명시적 중단.** SOT 우선(§7), 오너 확정 필요 |
| feature-sot 문서 26건 중 어느 것이 최종본인지 모호하다 | **명시적 중단.** 폐기 판단은 오너 몫 |
| 관문을 엄격하게 바꿨더니 기존 검사 중 일부가 빨간불이 된다 | **자동 처리** — 그 검사의 판정 출력을 계약 형식에 맞춘다(검사 약화 금지) |
| 관문 수정이 26개 검사 전량 재실행을 요구한다 | **자동 처리** — 전량 실행하고 출력 숫자 그대로 기록 |
| 충돌 PR 안에 본선에 없는 유일한 산출물이 있다 | **명시적 중단.** 닫기 전 오너 확인 |
| codex 훅이 꺼진 이유가 확인 안 된다 | **명시적 중단.** 켜지 않는다 |
| 그 외 전부 | **명시적 중단 + 사유 기록 + 이 표 갱신안 제시** |

## 비범위

- PR 병합 실행(USER_MERGE_ONLY)
- HumanSearch 기능 추가(L2 서치 순회 등) — 이 goal과 무관, 병행 가능
- GitHub 요금제 변경이 필요한 branch protection 강제 — 개인 계정+비공개는 403(기확인)
- codex 환경 파일의 임의 수정

## WU-6 배송 — 로컬에만 있는 5커밋을 원격으로 (2026-08-27 추가, 등급 L3)

### 왜 이것이 관문 수리보다 먼저인가

2026-08-27 02:2x 실측:
```
main         c59bad7   origin/main  c59bad7
HEAD         472c276   (브랜치 rescue/main-mixed-20260825T200952)
main 에 없는 커밋: 5개 · 원격에 rescue 브랜치 없음 · 해당 PR 없음
```
→ 어젯밤 회수 작업 전체가 **이 컴퓨터에만 존재한다.** 컴퓨터 고장 = 전량 소실. 관문이 뚫린 것보다 즉각적인 손실이다.
근거 인용(창립 스펙 §7·§4): v5 에서 로그인 하드닝 5,800줄이 "GREEN" 으로 기록됐으나 main 의 조상이 아니었고, 라이브 수정 2,305줄은 push 조차 안 됐다. **"고쳤다"는 merge 된 SHA 를 댈 때만 참이다.**

### P11③ 위반 실측 — 한 PR 로 올릴 수 없다

```
git diff --numstat main..HEAD → 59 files changed, 8373 insertions(+)
```
P11③: **3,000줄 초과 PR 절대 금지**(v4 실측 60일 결함률 100%, n=4). 8,373줄은 2.8배다.

### 분할안 — 파일 겹침 0 확인, 커밋별 독립 PR

| PR | 커밋 | 크기 | 주제 | 등급 | P11③ |
|---|---|---|---|---|---|
| ① | `9d7e872` | +1,865 · 4파일 | checkpoint 게이트·JS 스캐너 (코드+시험) | L2 | OK |
| ② | `3094eef` | +777 · 6파일 | finding-runner — 재현 안 된 감사 의견 차단 (코드+시험) | L2 | OK |
| ③ | `8720a41` | +1,895 · 13파일 | 기능 정본 카탈로그 + 검사기 강제 | **L3**(SOT) | OK |
| ④ | `210d704` + `472c276` | +3,836 · 36파일 | 검증·판정 기록 회수 (**전부 문서**) | L1 | **★ 위반 3,836줄** |

**④ 의 P11③ 위반은 숨기지 않는다.** 두 갈래이고 오너 판단이 필요하다:
- (a) 그대로 올리고 위반을 PR 본문에 명시 — P11③ 근거(n=4)는 **코드 PR** 실측이고 ④는 100% 문서라 "두 달 뒤 원인 추적 불가" 위험이 다르다는 논거.
- (b) 문서를 주제별로 쪼개 재커밋 — 다른 세션의 커밋을 재작성해야 해서 그 작업을 망칠 위험이 있다.
→ **권고는 (a)**. 다만 P11③ 에 문서 면제 조항이 없다는 사실은 그대로 남는다(P11① 의 면제 목록은 "생성 파일·마이그레이션·픽스처"뿐).

### AC-6 (딱 1개)

> If 로컬에만 있는 커밋이 존재하면, then 주제별 PR 로 원격에 올라가 있고 각 PR HEAD SHA 의 CI 가 GREEN 이어야 한다.

검증:
```
git log --oneline main..HEAD          # 기대: 빈 출력 아님 → PR 로 커버됨을 목록으로 대조
git ls-remote --heads origin | grep <각 브랜치>   # 기대: 4건 존재
gh pr checks <각 PR>                  # 기대: 전부 pass
```

### 예외 케이스 표 (WU-6 전용)

| 상황 | 처리 |
|---|---|
| 다른 세션이 미커밋 변경을 들고 있다 | **대기.** 그 파일을 커밋하거나 되돌리지 않는다. 감시만 한다 |
| 대기 중 HEAD 가 또 움직인다 | **자동 처리** — 분할표를 다시 계산한다. 새 커밋도 주제별로 배정 |
| cherry-pick 이 충돌한다 | **명시적 중단.** 커밋 순서 의존이 있다는 뜻이므로 순차 PR 로 전환하고 보고 |
| PR 의 CI 가 빨간불이다 | **명시적 중단.** READY 선언 금지, 원인 보고 |
| ④ 의 P11③ 위반 처리 | **오너 결정 대기.** 임의로 쪼개거나 임의로 올리지 않는다 |
| 그 외 전부 | **명시적 중단 + 사유 + 이 표 갱신안** |

### 비범위

- **merge 실행** — `USER_MERGE_ONLY`. PR 생성까지만 한다.
- 다른 세션의 미커밋 6파일을 커밋·되돌림·수정하는 일체의 행위.
- 기존 열린 PR 12건의 정리(별도 WU-3).

## 적대 검증 로그

### V1 — codex `task-mtabcm85-ylxk5e` (session `01a03eeb-e827-7d22-80a5-8c5ef631568d`, 2026-08-27)

**판정: REQUEST_CHANGES** — 높음 3건 · 중간 3건.

#### Claude 재현 결과 (V-4: 재현 전까지 결함으로 세지 않는다)

| codex 지적 | Claude 재현 | 결과 |
|---|---|---|
| 높음① `PASS` 한 줄 위조로 빈 인수검사 통과 | 재현함(2026-08-27, 종료값 0) | **확인** — 이미 알고 있던 급소. codex가 **확장**: 실제 `acceptance-hs-a4.sh` 본문에 두 줄을 삽입하면 `pre-commit`·무력화 회귀(26/26)·`VERDICT: PASS` 까지 전부 통과 |
| 높음② CI 스텝 **삭제** 또는 **예외 이름 도용**으로 무력화 | **재현함** — 아래 증거 | **확인 · 신규**(Claude 미발견) |
| 높음③ SHA 귀속 CI가 실조회부가 아닌 자기 진리표만 검사 | 코드로 확인(가상 SHA `1111…`/`2222…` 진리표), 무력화 주입은 미재현 | **부분 확인** |
| 중간 대문자 확장자(`.JS`)로 pre-commit 우회 | 미재현 | codex 주장 |
| 중간 guard `rm` 실패를 성공으로 보고 | 미재현 | codex 주장 |
| 중간 C15가 `/Users`·`/home` 접두사만 탐지 | 미재현 | codex 주장 |

#### 높음② 재현 증거 (임시 사본만 사용 — 저장소 무수정)

반례 A — 개인정보 노출 스캔 스텝을 통째로 삭제:
```
원본:  PASS: 조건부·오류무시 스텝 없음 (job·step 25개 검사) / CHECKED: 25
삭제본: PASS: 조건부·오류무시 스텝 없음 (job·step 24개 검사) / CHECKED: 24 / 종료값=0
```

반례 B — 그 스텝 이름을 허용 예외 `인수 검사 0-5 (push · CI 연결)` 로 바꾸고 `if: ${{ false }}` 부착:
```
ALLOWED: 인수 검사 0-5 (push · CI 연결) — if 허용 (…)
PASS: 조건부·오류무시 스텝 없음 (job·step 25개 검사) / CHECKED: 25 / 종료값=0
```

**위임 실패 확인 (이번 재현의 핵심)** — `scripts/verify/check-ci-step-integrity.sh:15-16` 은 주석으로 이렇게 위임한다:

> "막지 못하는 것: 스텝 자체를 삭제하는 것. 그것은 mechanism-registry 와 pre-push 의 실행줄 검사가 맡는다."

그런데 실측하면 위임받은 쪽에 그 검사가 **없다**:
```
grep scan-data-exposure docs/sot/mechanism-registry.yaml  → 없음
grep scan-data-exposure hooks/pre-push                    → 없음
grep scan-data-exposure .github/workflows/verify.yml      → verify.yml:204 (유일)
```
→ **개인정보 노출 스캔은 어느 장부에도 등재되지 않은 고아 검사다.** 지우면 아무도 모른다.

#### 이 판정이 뒤집은 Claude의 이전 주장

2026-08-27 humanreview 에서 "관문을 위조해도 `verify.sh` 와 `scan-data-exposure.sh` 두 독립 방어선은 계속 돈다"고 적었다. **틀렸다.** 그 스텝 자체를 지우거나 이름을 바꾸면 두 방어선도 함께 사라지고, 그것을 잡을 장부가 없다. 위험 수준을 낮춰 보고한 것을 정정한다.

#### AC 갱신 (사장님 지시 — V1 반영 후 코딩)

- **WU-2c 의 AC 를 확대한다.** 기존 "no-op 명령 차단"만으로는 반례 A·B 를 못 잡는다. 새 AC:
  > If 필수 CI 스텝이 삭제되었거나, 예외 이름을 도용해 조건이 붙었으면, then 검사가 종료값 1로 거부해야 한다.
  구현 방향: 예외를 **이름 문자열이 아니라 스텝 ID + 허용 조건의 정확한 값**에 묶고, 필수 스텝 집합이 **정확히 1회씩** 존재하는지 대조한다.
- **WU-2a 의 AC 에 반례를 1건 추가한다.** 위조 두 줄을 **실제 인수검사 파일 본문에 삽입**했을 때도 거부되어야 한다(codex 확장 반례).
- **WU-5 신설(중간 3건)** — 대문자 확장자 우회 · guard `rm` 실패 은폐 · C15 접두사 한계. 각각 별도 WU, D레인과 병렬 가능. 착수 전 Claude 재현 필수.

#### 미확인 (codex 자신이 명시)

- 원격 GitHub 상태·branch protection: 네트워크 차단으로 미확인
- `check-verified-sha.sh:100` 의 `head -1` 이 재실행 시 옛 성공을 고를 가능성: fixture 필요
- 조사 중 원본 checkout 이 외부 동시 작업으로 `8720a41` → `210d704` 이동 — 시작·종료 동일성 증명 불충분
