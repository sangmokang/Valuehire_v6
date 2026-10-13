# checkout v7 SHA pin — fresh V1 적대검증 판정 (2026-09-07)

## 판정

**REQUEST_CHANGES** — 현재 `verify.yml:18`의 실제 값은 의도한 `actions/checkout` v7.0.1 커밋 SHA와 일치하고, 입력 호환성 및 diff 약화 징후도 발견되지 않았다. 그러나 goal 문서가 AC-1 증거로 제시한 grep은 실행 스텝·정확한 40자 끝 경계·유일성을 강제하지 않아 거짓 초록으로 우회되며, 인증된 `gh api`가 이 실행 환경에서 실패하여 AC-2의 PR `pull_request` CI SUCCESS도 fresh 증명되지 않았다. 코드 결함 발견과 원격 증거 부재를 구분하면, **워크플로 변경 자체는 양호하지만 goal/병합 증거 사슬은 닫히지 않았다.**

- 검토 대상: branch `task/checkout-v7-sha-pin-20260907`, commit `569ab8988e2c3e41be7c7b9789c537b9a008602e`, PR #67
- 기준 커밋: `01495b3eae76d3e43e4a6cc8a481ee78258502c6`
- 검토 시각: `2026-09-07T09:23:46+0900`
- 방식: 원본 코드·Git·PR을 변경하지 않는 `humanreview` V1. 반례는 파이프 입력에서만 만들었다.
- 검토 시작 상태: HEAD와 로컬 원격 추적 ref가 모두 `569ab898...`; worktree clean.

## 결함 및 차단 사유

### M-1 — AC-1 grep이 malformed/commented/duplicate 참조를 거짓 통과시킨다

- 위치: `docs/engineering/checkout-v7-sha-pin-goal-2026-09-07.md:29-30`
- 깨지는 주장: AC-1 검증 명령이 `actions/checkout@<40자 SHA> # v7.0.1` 형태를 충분히 검증한다는 주장
- 원인: 패턴 `uses: actions/checkout@[0-9a-f]{40}`에 행 시작, SHA 뒤 경계, 버전 주석, 정확히 1건이라는 조건이 없다.
- 영향: 실제 action ref가 41자 이상이거나, checkout 스텝이 주석 처리되거나, 두 checkout이 공존해도 명령 종료값은 0이다. 이 명령만으로는 AC-1을 증명할 수 없다.
- 최소 수정 방향: 실행 스텝 전체 행을 anchor한 패턴으로 정확히 1건인지 검증하고, 별도로 모든 workflow YAML의 `actions/checkout@` 참조가 1건인지 확인한다. 현재 파일은 아래 강화 패턴에서 1건으로 통과했다.

```text
^[[:space:]]*-[[:space:]]+uses:[[:space:]]+actions/checkout@[0-9a-f]{40}[[:space:]]+# v7\.0\.1[[:space:]]*$
```

### E-1 — PR #67의 pull_request CI SUCCESS를 fresh 재조회하지 못했다

- 위치: `docs/engineering/checkout-v7-sha-pin-goal-2026-09-07.md:31`
- 깨지는 주장: AC-2
- 재현: `gh api`로 tag, action metadata, PR, Actions runs 엔드포인트를 각각 조회했으나 모두 exit 1과 `error connecting to api.github.com`을 반환했다. `gh auth status`도 저장된 `sangmokang` 토큰이 invalid라고 보고했다. 독립 `git ls-remote` 역시 `Could not resolve host: github.com`으로 exit 128이었다.
- 영향: 로컬 `origin/task/...` ref가 대상 HEAD와 같다는 사실은 PR 이벤트 CI의 event/status/conclusion을 증명하지 않는다. 기존 초록불 또는 goal 문서의 서술을 재사용하지 않았다.
- 판정: **AC-2 NOT_RUN**. 인증된 GitHub API에서 `event=pull_request`, `head_sha=569ab898...`, workflow/job/checkout step의 `conclusion=success`를 다시 얻기 전에는 병합 증거가 완성되지 않는다.

## 요구사항별 판정

| 항목 | 판정 | fresh 증거 / 반증 결과 |
| --- | --- | --- |
| (1) 현재 grep 매치와 저장소 내 checkout 유일성 | PASS | 지정 grep은 `verify.yml:18` 한 줄, count 1. 전체 tracked `*.yml`/`*.yaml`의 `actions/checkout@` 검색도 그 한 줄뿐이었다. 전체 tracked 텍스트 검색에는 과거 판정/goal 문서의 문자열이 있으나 실행 action은 아니다. |
| (2) SHA가 v7.0.1 tag commit인지 `gh api` 재조회 | NOT_RUN (`gh`), 공식 웹으로 보강 | 요청한 `gh api`는 네트워크/인증 문제로 exit 1. 대신 공식 v7.0.1 release 페이지가 `3d3c42e` 커밋으로 링크하고 그 링크가 전체 SHA `3d3c42e5aac5ba805825da76410c181273ba90b1` commit 페이지로 연결됨을 fresh 확인했다. 사실관계 신뢰도는 높지만 요청한 API 증거와 동일시하지 않는다. |
| (3) `fetch-depth: 0`, `persist-credentials: false` 입력 유효성 | PASS | exact SHA의 공식 `action.yml`이 두 입력을 선언한다. exact SHA의 `src/input-helper.ts`도 각각 `core.getInput('fetch-depth')`, `core.getInput('persist-credentials')`로 소비한다. `action.yml`은 `using: node24`이다. |
| (4) diff의 검사 약화 은닉 여부 | PASS | `verify.yml` diff는 `@v4` 삭제 1줄, SHA 고정 추가 1줄뿐이다. 추가행에서 `skip`, `continue-on-error`, `if:false`, `|| true`, `exit 0`, `timeout-minutes:0` 스캔은 무매치(exit 1). `git diff --check`는 exit 0. 입력 블록과 이후 26개 검증 스텝은 변경되지 않았다. |
| (5) PR #67 pull_request CI SUCCESS | NOT_RUN | PR/Actions API를 인증된 `gh`로 읽지 못했다. SUCCESS라고 판정하지 않는다. |

## AC / counter-AC 판정

- **AC-1 실제 상태: PASS.** `verify.yml:18`에서 추출한 ref는 `3d3c42e5aac5ba805825da76410c181273ba90b1`, 길이 40이며 기대 SHA와 byte-for-byte 동일하다. 강화한 전체 행 패턴도 정확히 1건이다.
- **AC-1 제시 검사기: FAIL.** 현재 정상값에는 통과하지만 M-1의 세 우회를 모두 놓친다.
- **AC-2: NOT_RUN.** fresh `pull_request` CI 증거 없음.
- **counter-AC (`@v7`): PASS.** 메모리에서 SHA를 `@v7`로 바꾸자 원 grep은 match 0, exit 1.
- **counter-AC (`@v4`): PASS.** 메모리에서 SHA를 `@v4`로 바꾸자 원 grep은 match 0, exit 1.

## 실제 diff와 위험 분류

`git diff-tree --raw 569ab89`와 `git diff --numstat 569ab89^ 569ab89` 기준 커밋에는 두 파일이 있다.

1. `.github/workflows/verify.yml`: `1 insertion, 1 deletion` — 실행 경계/서드파티 공급망 참조 변경. 고위험 검토 대상.
2. `docs/engineering/checkout-v7-sha-pin-goal-2026-09-07.md`: 신규 `63 lines` — 실행 영향 없음, 검증 주장 자체는 M-1 대상.

따라서 “변경은 verify.yml 한 줄뿐”은 **실행 동작 변경** 기준으로는 맞지만, commit 파일 목록 기준으로는 goal 문서 추가까지 두 파일이다.

## 정상 검증 실행 기록

| 명령 요약 | exit | 핵심 출력 / 해석 |
| --- | ---: | --- |
| `grep -nE 'uses: actions/checkout@[0-9a-f]{40}' .github/workflows/verify.yml` | 0 | `18: ...@3d3c42e...ba90b1 # v7.0.1` |
| 같은 grep의 `-c` | 0 | `1` |
| `git grep -n -I -i -E 'actions/checkout@' -- '*.yml' '*.yaml'` | 0 | `.github/workflows/verify.yml:18`만 출력 |
| SHA 추출 + 길이/기대값 대조 | 0 | `length=40`; exact SHA 일치 |
| 강화된 전체 행 패턴 count + `test count -eq 1` | 0 | `anchored-match-count=1` |
| `git diff --check 569ab89^ 569ab89` | 0 | 출력 없음; whitespace 오류 없음 |
| 실제 추가행 약화 키워드 스캔 | 1 | 출력 없음; 금지 패턴 무매치이므로 기대한 종료값 |
| Ruby `YAML.safe_load` 구문 파싱 | 0 | `workflow-yaml=valid`; 단 YAML 1.1 해석 때문에 `on`이 `true` key로 보이므로 GitHub Actions 의미 검증 증거로 과장하지 않음 |
| `bash verify.sh` | 0 | `PASS: no secret-pattern match in any tracked file, .env not tracked` |

## 반증·검사기 공격 기록

모든 변이는 원본 worktree를 쓰지 않고 `sed`/`printf`의 파이프 출력에서만 실행했다.

| 변이 입력 | 원 AC-1 grep 결과 | 해석 |
| --- | --- | --- |
| ref를 `actions/checkout@v7`로 변경 | match 0, exit 1 | 명시된 counter-AC 방어 성공 |
| ref를 `actions/checkout@v4`로 변경 | match 0, exit 1 | 명시된 counter-AC 방어 성공 |
| 올바른 40자 SHA 뒤에 `x` 추가 | 변이 행 매치, exit 0 | **우회 성공** — 정확히 40자인지 보장하지 못함 |
| checkout 실행 행을 `# uses: ...` 주석으로 변경 | 주석 행 매치, exit 0 | **우회 성공** — 실제 실행 스텝인지 보장하지 못함 |
| 두 번째 40자 checkout 행 추가 | 두 행 모두 출력, exit 0 | **우회 성공** — 유일성 보장 없음 |
| 약화 탐지기에 `continue-on-error: true`, `if: false`, `run: check \|\| true`, `skip: true` 주입 | 네 줄 모두 탐지, exit 0 | 이번 diff에 사용한 약화 스캔이 대표 반례를 놓치지 않음을 확인 |

## 업스트림 보강 증거

CLI/API 실패 후에도 공개 업스트림 사실을 기억이나 goal 문서에서 복사하지 않고 공식 GitHub 원문으로 다시 확인했다.

- [actions/checkout v7.0.1 release](https://github.com/actions/checkout/releases/tag/v7.0.1) — release가 `3d3c42e`에 연결됨.
- [full commit 3d3c42e5aac5ba805825da76410c181273ba90b1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1) — `prep v7.0.1 release` commit.
- [exact SHA action.yml](https://raw.githubusercontent.com/actions/checkout/3d3c42e5aac5ba805825da76410c181273ba90b1/action.yml) — `persist-credentials`, `fetch-depth`, `using: node24` 확인.
- [exact SHA input-helper.ts](https://raw.githubusercontent.com/actions/checkout/3d3c42e5aac5ba805825da76410c181273ba90b1/src/input-helper.ts) — 두 입력을 실제로 읽는 코드 확인.

이 보강은 공개 `actions/checkout` 사실에만 유효하다. 비공개로 보이는 `sangmokang/Valuehire_v6` PR #67/Actions 페이지는 익명 외부 경로에서도 읽지 못했다.

## 미실행·잔여 위험

- `gh api` exact tag object의 `object.type=commit` 및 full `object.sha`를 이번 환경에서 직접 얻지 못했다.
- PR #67의 head SHA, `event=pull_request`, workflow/job/checkout step 결론을 fresh API로 얻지 못했다.
- `actionlint`가 설치되어 있지 않아 actionlint 검증은 `NOT_RUN`; 단 실제 YAML 변경은 기존 scalar 값 하나의 교체다.
- GitHub-hosted runner에서 워크플로 전체를 로컬 재현하지 않았다. `bash verify.sh`는 해당 CI 전체의 대체 증거가 아니다.
- SHA 고정은 가변 태그 공격면을 줄이는 대신 자동 보안 업데이트를 받지 않는다. goal 문서가 Dependabot을 별도 WU로 미룬 사실은 확인했으나 이번 V1은 그 후속 작업 완료를 증명하지 않는다.

## 병합 전 닫아야 할 증거

1. M-1의 AC-1 명령을 전체 행 anchor + exact count로 교체하거나, 현재 강화 검증 결과를 authoritative evidence로 명시한다.
2. 유효한 GitHub 인증/네트워크에서 tag ref API를 다시 조회해 `object.type=commit`, full `object.sha=3d3c42e...ba90b1`를 저장한다.
3. PR #67의 대상 head가 `569ab898...`인지 확인한 뒤, 그 SHA의 `pull_request` Actions run과 `verify` job 및 checkout step이 모두 `conclusion=success`인지 저장한다.
4. 위 재조회 뒤 HEAD가 바뀌지 않았음을 다시 고정한다. HEAD가 바뀌면 이 V1 판정은 만료된다.

## 종료 상태 계약

원본 tracked 파일은 수정하지 않았다. 이 판정 문서 자체만 새 untracked 파일로 생성한다. 최종 `git diff --quiet -- .`는 tracked diff 없음(exit 0)이어야 하며, `git status --short`에는 이 보고서 한 건만 `??`로 보여야 한다.
