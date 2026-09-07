# audit.yml 신설 — V1 fresh 적대검증 판정 (2026-09-07)

## 대상

- 워크트리: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/audit-workflow-20260907`
- 브랜치: `task/audit-workflow-20260907`
- 커밋(HEAD): `921923c47a523ffa3d1a6be2403f1a4c6298e8bf`
- PR: `sangmokang/Valuehire_v6#68` — `headRefOid=921923c...`(로컬 HEAD와 일치 확인), `baseRefName=main`, `state=OPEN`, `mergeable=MERGEABLE`
- goal 문서: `docs/engineering/audit-workflow-goal-2026-09-07.md`

## 무엇을 바꿨는지

1. `scripts/check-suppression-expiry.sh` 신규 — `verify.yml`의 억제 만료 인라인 스크립트를 그대로 추출.
2. `scripts/check-action-sha-drift.sh` 신규 — 서드파티 GitHub Action `uses:` 참조가 40자 SHA로 고정됐는지 검사.
3. `.github/workflows/verify.yml` — 억제 만료 스텝 본문만 `run: bash scripts/check-suppression-expiry.sh` 호출로 교체(20줄 삭제, 4줄 추가). 트리거·다른 스텝 불변.
4. `.github/workflows/audit.yml` 신규 — `schedule`(매일 KST 05:00) + `workflow_dispatch`, 위 스크립트 2개를 순서대로 실행.
5. `docs/sot/verification-commands.md`에 audit.yml 섹션 추가.

## 요구사항별 판정

| ID | 판정 | 근거 |
|---|---|---|
| AC-1 (추출 전/후 동일 입출력) | **PASS** | 아래 §1 |
| AC-2 (schedule+workflow_dispatch, YAML 구문, 구조 무결성 회귀) | **부분 PASS — 회귀 방어선 없음(§3)** |
| AC-3 (SHA 고정/가변 태그 정확 판정, fixture) | **REQUEST_CHANGES 대상 결함 2건 발견** | 아래 §2 |
| counter-AC (이 저장소에 대고 돌리면 FAIL) | **PASS, 재현됨** | 아래 §4 |
| 항목5 (audit.yml은 병합 게이트가 아니다) | **PASS, 정합** | 아래 §5 |
| 항목6 (verify.yml diff에 검사 약화 은닉 없음) | **PASS** | 아래 §6 |

## §1 — AC-1: 인라인 vs 추출 스크립트 대조

`main`(9de72b5, `verify.yml:139-159`)의 인라인 로직을 그대로 별도 파일로 떠서(`/private/tmp/.../ac1/inline_old.sh`), 5가지 경계값에서 추출된 `scripts/check-suppression-expiry.sh`와 병렬 실행해 stdout·종료값을 전부 대조했다.

| 케이스 | 인라인 | 추출본 | 일치 |
|---|---|---|---|
| `suppressions.yaml` 없음 | `PASS: 억제 없음` exit0 | 동일 | ✅ |
| 만료(2020-01-01) | `FAIL: 만료된 억제...` exit1 | 동일 | ✅ |
| 형식 오류(`not-a-date`) | `FAIL: expiry 형식 오류...` exit1 | 동일 | ✅ |
| check 2건 중 expiry 1건 | `FAIL: 억제 2건 중 expiry 가 1건뿐` exit1 | 동일 | ✅ |
| 미래 만료 정상 1건 | `PASS: 억제 1건...` exit0 | 동일 | ✅ |
| 실제 저장소 `suppressions.yaml`(3건) | `PASS: 억제 3건...` exit0 | 동일 | ✅ |

**해석**: 6/6 일치. AC-1은 실행 증거로 확인됨 — 단순 코드 비교가 아니라 실제 stdout+exit code 대조.

## §2 — AC-3: fixture 경계값 공격 (결함 2건)

격리된 임시 디렉터리(`/private/tmp/.../ac3/*`, 실제 저장소 미접촉)에 합성 workflow yml을 만들어 `scripts/check-action-sha-drift.sh <dir>`로 실행.

| 케이스 | 기대 | 실제 | 판정 |
|---|---|---|---|
| 정상 40자 소문자 SHA | PASS | `PASS: ... 1건 전부 SHA로 고정됨` exit0 | ✅ |
| **대문자 40자 SHA**(유효한 SHA, 대소문자만 다름) | PASS(git SHA는 대소문자 무관) | `FAIL: 가변 참조로 고정되지 않은 액션: ...AAAA...` exit1 | ❌ **결함** |
| **주석 처리된 `uses:` 줄**(`# uses: actions/checkout@v4`, 실행 안 됨) | 검사 대상에서 제외 | `FAIL: 가변 참조로 고정되지 않은 액션: actions/checkout@v4` exit1 | ❌ **결함** |
| `docker://` 액션 | 대상 제외 | 대상 0건 → `FAIL: 검사 대상 액션 참조 0건` exit2(의도된 fail-closed) | ✅ |
| 로컬 `./` 액션 | 대상 제외 | 대상 0건 → exit2(의도된 fail-closed) | ✅ |
| `uses:` 뒤 다중 공백 | 정상 파싱 | PASS exit0 | ✅ |
| 41자 SHA(무효한 길이) | FAIL(진짜 SHA 아님) | `FAIL: 가변 참조...` exit1 | ✅ |
| 유효 SHA 1건 + `@v4` 1건 혼재 | `@v4`만 FAIL로 지적 | 동일 | ✅ |

**결함 1 (MEDIUM, 재현됨)**: `scripts/check-action-sha-drift.sh:24`의 `grep -rhoE 'uses:...'`는 `#`로 시작하는 주석 줄도 매칭 대상에서 제외하지 않는다. 실행되지 않는 텍스트(문서용 예시, 마이그레이션 중 주석 처리된 옛 스텝)를 "가변 참조"로 오판해 FAIL을 낸다. `audit.yml`은 push/PR 게이트가 아니라 매일 새벽 이메일 알림 용도이므로, 이런 거짓 FAIL이 반복되면 "새벽 순찰"의 신호를 사람이 무시하게 만드는 방향으로 이 기능의 존재 목적(조용한 부패를 사람이 놓치지 않게 하는 것)을 정면으로 훼손한다. **현재 저장소의 실제 workflow 파일들에는 이 패턴이 없어 지금 당장의 오탐은 없음**(`grep -n '^\s*#.*uses:' .github/workflows/*.yml` → 매치 0건, 잠재 결함).

**결함 2 (LOW, 재현됨)**: `scripts/check-action-sha-drift.sh:21`의 `@[0-9a-f]{40}$` 정규식은 소문자 hex만 인정한다. git의 SHA는 대소문자를 구분하지 않으므로, 정당하게 고정된 대문자 SHA를 "가변 참조"로 오판한다. 실무에서 대문자 SHA를 쓸 일이 드물어 우선순위는 낮지만, "SHA로 고정됐는가"를 스스로 판정하는 스크립트가 유효한 SHA 형식 하나를 놓치는 것은 그 자체로 요구사항(AC-3 "SHA로 고정된 참조는 PASS")과 어긋난다.

## §3 — AC-2: 구조 무결성 회귀 방어선 미실측/미실장

goal 문서 AC-2는 "`acceptance-ci-step-integrity.sh`가 이 새 워크플로도 구조적으로 무결한지 확인(그 스크립트가 다중 워크플로 파일을 지원하는지 먼저 실측)"을 검증 방법으로 명시했다. 실제로 그 스크립트를 열어 실측했다:

```
scripts/acceptance-ci-step-integrity.sh:17: WF="$REPO/.github/workflows/verify.yml"
```

`verify.yml` 경로가 하드코딩되어 있다 — **다중 워크플로 파일을 지원하지 않는다**. `bash scripts/acceptance-ci-step-integrity.sh` 실행 결과도 14개 항목 전부 `verify.yml` 대상이었고 `audit.yml`은 한 번도 언급되지 않았다(원문 그대로 `CHECKED: 14 / VERDICT: PASS`).

그 결과 `audit.yml`에 나중에 누군가 `continue-on-error: true`나 `if: false`를 몰래 추가해도, 이 저장소의 **어떤 자동화된 회귀 검사도 잡지 못한다** — `audit.yml`은 정확히 이 스킬 문서(humanreview)가 "검사기 자체를 공격한다"에서 요구하는 방어선이 없는 상태로 병합된다. 제가 직접 `bash scripts/verify/check-ci-step-integrity.sh .github/workflows/audit.yml`을 수동 실행해 현재 시점 `audit.yml`은 구조적으로 문제없음(`PASS: 조건부·오류무시 스텝 없음 (job·step 4개 검사)`)을 확인했지만, 이는 이번 리뷰에서 제가 1회성으로 수행한 확인일 뿐 CI나 인수 검사에 편입되지 않았다. goal 문서 하단의 "적대 검증 로그" 섹션도 여전히 비어 있어(`(구현·검증 완료 후 기록)`), 구현자가 이 실측을 실제로 수행하고 기록했다는 증거가 없다.

## §4 — counter-AC: 실제 저장소에서 FAIL 재현

```
$ grep -n "uses:.*checkout" .github/workflows/verify.yml
18:      - uses: actions/checkout@v4
$ bash scripts/check-action-sha-drift.sh
FAIL: 가변 참조로 고정되지 않은 액션: actions/checkout@v4
EXIT=1
```

goal 문서 결정 목록 3의 주장("PR #67 병합 전이라 이 브랜치에서 돌리면 정상적으로 FAIL")이 실측으로 재현됨. 스크립트가 실제로 동작한다는 반증으로 유효.

## §5 — 병합 게이트 여부

```
$ gh api repos/sangmokang/Valuehire_v6/branches/main/protection
403 Upgrade to GitHub Pro or make this repository public to enable this feature.
$ gh api repos/sangmokang/Valuehire_v6/rulesets
403 (동일)
```

브랜치 보호·룰셋 자체가 이 저장소(개인 계정 private repo)에 없다 — `verify`든 `audit`이든 GitHub 차원의 "필수 체크"가 원천적으로 존재할 수 없다. `audit.yml`이 병합 게이트가 아니라는 goal 문서의 주장은 참이지만, 이는 `audit.yml`이 특별해서가 아니라 이 저장소에 애초에 강제 가능한 게이트가 없기 때문이다(이전 세션에서도 동일하게 확인된 사실). PR 병합 가능 여부는 여전히 사람의 "Merge" 클릭에만 달려 있다.

추가로 실측: `audit.yml`은 아직 default branch(`main`)에 없어 GitHub Actions 워크플로 목록에도, `workflow_dispatch` API로도 잡히지 않는다.

```
$ gh api repos/sangmokang/Valuehire_v6/actions/workflows --jq '.workflows[] | {name, path, state}'
{"name":"verify","path":".github/workflows/verify.yml","state":"active"}
$ gh workflow run audit.yml --repo sangmokang/Valuehire_v6 --ref task/audit-workflow-20260907
HTTP 404: workflow audit.yml not found on the default branch
```

goal 문서 "게이트 계획"이 정확히 이 상황("GitHub이 비-기본 브랜치의 신규 workflow_dispatch를 막을 수 있어, 안 되면 그 사실과 이유를 기록하고 로컬 fixture 증거로 갈음한다")을 예견했고 실제로 그대로 재현됐다 — **결함 아님**. 다만 이 사실 자체도 "적대 검증 로그"에 기록되지 않아, goal 문서가 스스로 세운 완료 기준을 문서상으로는 충족하지 못했다(§3과 같은 종류의 기록 누락).

## §6 — verify.yml diff 검사 약화 은닉 여부

```
$ git diff main...HEAD -- .github/workflows/ | grep -nE '^\+.*(skip|continue-on-error|if:\s*false|if:\s*\$\{\{\s*false)'
(매치 없음)
```

삭제 18줄/추가 4줄 전량을 직접 읽었다 — 인라인 본문을 스크립트 호출 1줄로 치환한 것 외 다른 변경 없음. 트리거(`on:`)·다른 스텝·permissions 블록 불변. 은닉된 약화 없음.

## 건너뛴 검증 / 미확인

- `audit.yml`의 `schedule` 트리거가 실제로 KST 05:00에 발화하는지는 병합 전에는 원천적으로 관측 불가(§5, GitHub 정책).
- `hooks/pre-commit`의 별도 만료 검사 로직은 이번 WU 비범위(goal 문서 결정 2)이므로 검토하지 않음.
- `lint-pr.yml`은 비범위.

## 현재 HEAD·작업공간 상태

리뷰 전 과정에서 `git status`는 시종 `nothing to commit, working tree clean`이었고, 원본 저장소 파일은 일절 수정하지 않았다(모든 fixture는 `/private/tmp/.../scratchpad/ac1`, `/ac3`에서만 생성·실행). 리뷰 종료 시점 HEAD도 `921923c`로 불변.

## 병합 전 판정: **REQUEST_CHANGES**

근거:
1. `scripts/check-action-sha-drift.sh`가 주석 처리된(비실행) `uses:` 텍스트를 실제 참조로 오판해 거짓 FAIL을 낸다(§2, MEDIUM, 재현됨) — 지금 당장 저장소를 깨뜨리진 않지만, 이 스크립트가 지키려는 "새벽 순찰이 사람에게 신뢰받는 신호를 보낸다"는 목적 자체를 훼손할 수 있는 잠재 결함.
2. 같은 스크립트가 유효한 대문자 SHA를 가변 참조로 오판한다(§2, LOW, 재현됨).
3. AC-2가 스스로 요구한 "audit.yml의 구조적 무결성을 자동으로 회귀 검사하는지" 실측이 수행되지 않았고(§3), 그 결과 audit.yml은 이 저장소의 다른 검사 파일들과 달리 무방비 상태로 병합된다. goal 문서의 "적대 검증 로그" 섹션도 비어 있어 완료 기준 미충족.

AC-1(핵심 로직 추출 무결성)과 counter-AC(FAIL 재현)는 결함 없이 통과했고, PR CI(push+pull_request 양쪽)도 현재 HEAD에서 green이다. 위 결함들은 병합을 막을 만큼 치명적이진 않지만(현재 저장소에 실제 오탐 트리거가 없고, audit.yml 자체는 현재 시점 수동 확인상 무결함), "재현 가능한 결함이 있으면 REQUEST_CHANGES"라는 이 리뷰 기준에 따라 있는 그대로 보고한다. 최소 수정 방향: `check-action-sha-drift.sh`의 grep 전에 `#`로 시작하는(선행 공백 허용) 줄을 제외하고, `[0-9a-f]`를 대소문자 허용(`[0-9a-fA-F]`)으로 바꾸면 §2의 두 결함이 해소된다. §3은 `acceptance-ci-step-integrity.sh`가 워크플로 파일 목록을 순회하도록 확장하거나, 별도 인수 스크립트로 `audit.yml`을 명시 검사 대상에 추가하면 해소된다.
