# 열린 PR 47건 · PR 없는 브랜치 111개 분류표 (2026-09-28)

> WU-0(`goal-prompts/software-factory-observer-2026-09-28.md` §5-2)의 1차 산출물. 기준 `origin/main` = `fc6beed`.
> 판정은 전부 `git` 실측: `git merge-tree --write-tree origin/main <br>`(충돌·흡수 여부),
> `git merge-base --is-ancestor`(다른 브랜치에 포함 여부), `git diff --name-only`(파일 종류).
> **NOT_RUN**: 각 PR 현재 HEAD의 verify CI 결과(P23) — 병합 직전에 PR마다 확인해야 한다.

## 1. 폐기 승인은 "유실 0" 절차로 바꾼다

폐기가 위험한 이유는 하나다 — **브랜치를 지우면 그 브랜치에만 있던 커밋이 사라진다.**
그래서 삭제 전에 전부 `archive/<브랜치명>` 태그로 박제한다. 태그가 커밋을 붙잡고 있으므로 브랜치를 지워도 아무것도 잃지 않고, 필요하면 `git checkout -b <이름> archive/<이름>`으로 언제든 되살린다.

```bash
# 1) 박제 (먼저, 전부)
for b in <목록>; do git tag "archive/$b" "origin/$b"; done
git push origin 'refs/tags/archive/*'
# 2) 박제 확인 후에만 삭제
for b in <목록>; do
  [ "$(git rev-parse "archive/$b")" = "$(git rev-parse "origin/$b")" ] && git push origin --delete "$b"
done
```

이렇게 하면 사장님이 정하실 것은 **"archive 태그로 박제하고 지워도 된다" 한 번의 예/아니오**로 줄어듭니다.

## 2. PR 없는 원격 브랜치 111개

| 분류 | 개수 | 뜻 | 처리 |
|---|---|---|---|
| 이미 main에 있음 | 15 | 커밋이 main 조상(7) 또는 병합해도 main과 트리가 같음(8, squash 병합됨) | 바로 삭제 (박제 불필요하나 해도 무방) |
| 다른 브랜치에 포함 | 30 | 끝 커밋이 다른 브랜치 안에 있음(스택의 아래층, `-a1/-a2` 재시도) | 박제 후 삭제 |
| 이 브랜치에만 있음 | 66 | 8월 31개 · 9월 35개 | **박제 후 삭제.** 되살릴 가치가 있는 것만 Observer가 골라 PR로 재제출 제안 |

이미 main에 있음(15): `task/ci-audit-closure-20260910` `task/gha-book-eval-20260909` `task/invoice-defect-closure-20260905` `task/p23-verify-recovery-20260910` `task/secret-floor-12-policy-20260905` `task/secret-webhook-vendor` `task/verify-ac-m` `deliver/docs-contracts` `task/admin-dashboard-phase-d` `task/cleanroom-doc-rescue-dryrun` `task/codeaudit-wrap-2026-08-19` `task/hs-cleanup-and-docs` `task/hs-observe-url-crash` `task/mutations-selfcontained` `task/retire-humansearch-l0-prompts`

"이 브랜치에만 있음" 중 되살리기 1순위(설계도가 갇혀 있는 것): `task/pr37-resolution-codex-20260910`(work-unit-policy.yaml), `task/wu-tdd-context-contract-20260910`(WU manifest 검사기) — 태스크 그래프(WU-B)의 선행.

## 3. 열린 PR 47건

### 3-1. 스택 — 닫지 말고 아래층부터 순서대로 병합 (의존성 그래프의 첫 데이터)

| 체인 | 순서 |
|---|---|
| HS 저장 | #85 → #89 → #97 → #100 · (#89 → #96) |
| HS 증거 | #85 → #93 → #94 |
| RPS | #88 → #87 |
| Jev | #109 → #110 |
| 게이트 억제 해제 | #75 → #77 · #75 → #78 |

아래층이 병합되면 위층 diff가 저절로 줄어든다. **위층부터 읽으면 같은 코드를 두 번 읽는다.**

### 3-2. 문서 전용 + 충돌 없음 (실행 파일 0개) — 가장 싸게 줄일 수 있는 묶음

#108 #107 #106 #102 #92 #91 #79 #65 #63 #61 #47 (11건, 스택 소속 문서 전용 #85 #88 #89 제외)

### 3-3. 충돌 있음 — base 머지로 재기반 필요 (리베이스·force-push 금지)

#78 #77 #68 #48 #43 #37 #29 #15 #14 #13 · #99

### 3-4. PR 닫기 후보 (브랜치는 §1 방식으로 박제)

| PR | 근거 |
|---|---|
| #29 | #43 제목이 "PR #29 대체" — 대체됨 |
| #13 | 47일째 · +16,437줄 · 충돌. P11③ "3,000줄 초과 PR 절대 금지"를 5.5배 초과 — 이대로는 병합 불가, 쪼개 재제출이 유일한 경로 |
| #99 | 스스로 "병합 대상 아님, 회수 보존" — 보존 목적은 archive 태그가 대신한다 |

### 3-5. 나머지 — 코드 포함, 오너 리뷰 등급 (high_risk 경로 포함 여부로 순서)

high_risk 0: #103 #95 #66 #54 #45 #44 · high_risk ≥1: #110 #109 #105 #104 #90 #86 #83 #74 #67
P11③ 3,000줄 초과(추가 줄 기준): #83 +15,670 · #105 +7,448 · #104 +7,390 · #110 +6,301 · #15 +5,559 · #100 +4,795 · #109 +3,435 · #96 +3,128 (+ 닫기 후보 #13·#99). 스택은 아래층 병합 후 위층 순증분으로 재측정한 뒤 분할 여부를 결정 카드로 올린다.
