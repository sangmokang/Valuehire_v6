# checkout@v7 SHA 고정 — goal (2026-09-07)

## 상위 목표

`verify.yml`의 `actions/checkout@v4`는 GitHub 러너가 2026-09-23에 Node20을 제거하면 경고·불안정 상태로 넘어간다(v4는 `using: node20` 선언). v7.0.1(`using: node24` 선언, SHA `3d3c42e5aac5ba805825da76410c181273ba90b1`)로 올리고, 가변 태그가 아니라 커밋 SHA로 고정해서 이 저장소가 uv 0.11.3을 계약(C-8)으로 못박은 것과 같은 수준으로 서드파티 액션 교체를 막는다. **성공 신호**: `verify.yml`의 checkout 스텝이 SHA로 고정되고, CI(verify job)가 그 상태로 여전히 초록.

## 현재 상태 (file:line)

- `.github/workflows/verify.yml:18` — `uses: actions/checkout@v4` (가변 태그, node20 선언)
- `actions/checkout` 공식 저장소 실측(2026-09-07, `gh api` 직접 조회):
  - `gh api repos/actions/checkout/git/refs/tags/v7.0.1` → `object.sha = 3d3c42e5aac5ba805825da76410c181273ba90b1`, `object.type = commit` (라이트웨이트 태그 — 커밋을 직접 가리킴, `git/tags/<sha>` 조회는 404로 이를 확인)
  - `gh api "repos/actions/checkout/contents/action.yml?ref=v7.0.1"` → 116행 `using: node24` 확인
- Node20 GitHub Actions 러너 제거 확정일: 2026-09-23 (https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/)
- `gh api repos/actions/checkout/compare/v6.0.3...v7.0.1` + `CHANGELOG.md` 확인: v7.0.0의 유일한 동작 변경은 "Block checking out fork PR for `pull_request_target`/`workflow_run`" — 이 저장소 `verify.yml`은 `push`/`pull_request`/`workflow_dispatch`만 트리거로 쓰므로 해당 없음. `fetch-depth`·`persist-credentials` 입력 계약에 영향 없음(action.yml 입력 목록 동일).

## 근본 원인

`verify.yml` 작성 당시(2026-08 초) `checkout@v4`가 최신이었고, 이 저장소의 "액션 버전은 가변 태그로 둔다"는 암묵적 관행이 이후 uv처럼 정밀 고정이 필요해진 항목에 갱신되지 않았다. `tj-actions/changed-files` 공급망 사고(2025-03)가 정확히 이 가변 태그 방식을 악용했다.

## 읽은 SOT

- `docs/sot/coding-principles.md` P13 — 검사 파일·CI 워크플로 diff는 원칙적으로 `weakens-check` 라벨 요구. 단, 이 조항의 기계 장치는 `scripts/acceptance-principles-check.sh`가 강제하는 것은 "34개 정본 문구·배선"이며, `weakens-check` 라벨 자체를 CI가 강제로 확인하는 스크립트는 이 저장소에 없다(`/usr/bin/grep -rln "weakens-check" .` 로 `*.sh`/`*.yml` 실체 없음 확인, 2026-09-07) — **policy 수준**(산문 규칙, 기계 강제 없음)이지 hook/runner가 아니다. 이번 변경은 검사를 **약화**가 아니라 **강화**(가변 태그→SHA 고정)하므로 라벨 해당 없음으로 판단하고 이 근거를 PR 본문에 남긴다.
- `docs/sot/git-workflow.md` — 워크트리 생성 명령 `git worktree add worktrees/<name> -b task/<name>` 확인, 이 명령으로 `worktrees/checkout-v7-sha-pin-20260907` 생성.
- `docs/sot/verification-commands.md` — 이 저장소는 `make`/`npm` 레포가 아님, 검증 4단계는 `bash verify.sh`(로컬 비밀 스캔)이고 CI 전체 게이트는 `verify.yml`의 26개 스텝이 정본. 로컬에서 CI 전체를 재현할 수 없다는 점 확인.
- 재발 원장: 이 레포에는 `docs/sot/` 안에 별도 "재발 원장" 파일이 없다(`docs/sot/INDEX.md`에 등재된 8개 파일 중 없음). 이번 작업은 신규 실수 패턴이 아니라 예정된 인프라 갱신이므로 원장 신설 트리거(R4 "같은 지적 2회 반복") 해당 없음.

## 인수 기준 (EARS)

- **AC-1**: `verify.yml:18`의 `uses:` 값이 `actions/checkout@<40자 SHA> # v7.0.1` 형태여야 한다.
  검증 명령(초안): `/usr/bin/grep -E "uses: actions/checkout@[0-9a-f]{40}" .github/workflows/verify.yml` → 매치 1건.
  **검증 명령(V1 반례 반영 후 authoritative)**: 초안 패턴은 행 시작·SHA 뒤 경계·버전 주석·유일성을 강제하지 않아 41자 SHA·주석 처리된 줄·중복 checkout 행을 모두 거짓 통과시킨다(아래 "적대 검증 로그" M-1). 대신 아래 두 명령을 함께 쓴다.
  1. `/usr/bin/grep -cE '^[[:space:]]*-[[:space:]]+uses:[[:space:]]+actions/checkout@[0-9a-f]{40}[[:space:]]+# v7\.0\.1[[:space:]]*$' .github/workflows/verify.yml` → `1`
  2. `git grep -n -I -i -E 'actions/checkout@' -- '*.yml' '*.yaml'` → 저장소 전체 workflow YAML 중 `.github/workflows/verify.yml:18` 단 한 줄만 출력
- **AC-2**: 이 변경 뒤 CI(verify job)가 checkout 스텝을 포함해 처음부터 끝까지 성공해야 한다(로컬 재현 불가 — PR을 올려 실제 GitHub Actions 러너로 확인).
  검증 명령: `gh api repos/sangmokang/Valuehire_v6/commits/<head-sha>/check-runs --jq '.check_runs[] | "\(.name) \(.status) \(.conclusion)"'` — `push`·`pull_request` 두 이벤트 모두 `completed success`여야 한다(이벤트 종류를 구분해서 봐야 하는 이유는 "적대 검증 로그" 참고).
- **counter-AC**: SHA 대신 `@v4`나 `@v7`(태그) 같은 가변 참조로 되돌리면 AC-1 검증 명령이 매치 0건으로 실패해야 한다.

## 계약 (입출력 모양)

- 입력: 없음(워크플로 파일 1줄 수정)
- 출력: `.github/workflows/verify.yml`의 checkout 스텝 1줄만 변경

## 결정 목록 (③ 표↔테스트 대응 전 확정)

1. **weakens-check 라벨**: 미부착. 근거 — 위 SOT 절 참고, 강화이지 약화가 아니고 라벨 자체가 기계 강제 대상이 아님.
2. **Dependabot(github-actions 생태계) 추가 여부**: 이번 PR에는 **포함하지 않는다.** 사용자 goal 원문이 "적대검증 정조준"에서 트레이드오프 확인을 요구했지만, 같은 원문의 "비범위" 절이 "이번 PR은 checkout 버전+SHA 고정 1개 AC만"이라고 명시적으로 범위를 좁혔다 — 뒤 문장이 앞 문장의 제안을 이번 PR 범위에서 배제한다. `.github/dependabot.yml`은 이 레포에 아직 없음(확인함) — 별도 WU로 이슈 #64 잔여 항목과 함께 처리 대상으로 아래 "비범위"에 기록한다.
3. **AC-1 검증 명령의 항구화 여부**: 이 저장소는 CI 스텝을 "고정 목록"으로 관리하고(`docs/sot/verification-commands.md`), 새 `scripts/acceptance-*.sh`를 추가하면 `verify.yml`+해당 문서 표 양쪽에 등록해야 한다. 이번 변경은 값 1개 고정이며 회귀 위험(누군가 다시 가변 태그로 되돌림)은 P13④(검사기 자기제외 금지)와 무관한 "실수로 되돌림" 시나리오다 — 신규 상시 회귀 스크립트를 추가하는 것은 이슈 #64의 `weakens-check`·`shellcheck`/`zizmor` 도입 트랙과 겹치므로 이번 1줄 변경 PR에서는 만들지 않고, AC-1 grep은 이번 PR 검증 시점의 1회성 fresh 증거로만 남긴다(비범위에 기록).

## 게이트 계획

- 코드 로직 변경이 아니라 CI 설정 변경이라 RED/GREEN 유닛테스트 대상은 없다. 대신 AC-1의 grep 검증을 fresh 실행해 로그를 남기고, PR을 올려 실제 CI green을 라이브 증거로 삼는다(로컬 `verify.sh`로는 이 변경의 효과를 확인할 수 없음을 인지).
- `.github/workflows/verify.yml`은 P13이 "검사 파일" 취급하는 대상이므로 PR 라벨 `weakens-check` 요구 여부를 확인 — 위 "결정 목록 1"의 근거로 해당 없음.

## 적대검증 정조준

- "SHA를 고정하면 이후 checkout의 보안 패치가 자동으로 안 들어온다" — 트레이드오프 인정. Dependabot(`github-actions` 생태계, cooldown 권장)으로 SHA 고정과 자동 갱신을 동시에 만족시킬 수 있는지는 **이번 PR의 결정으로 별도 WU로 미룬다**(위 "결정 목록 2"). 이번 PR 자체는 이 트레이드오프를 새로 만드는 것이 아니라 v4 시절에도 동일하게 없었던 자동 갱신 장치의 부재를 그대로 이어받는 것뿐임을 확인.
- v7.0.1이 이 저장소의 현재 사용 패턴(`fetch-depth: 0`, `persist-credentials: false`)과 호환되는지 CHANGELOG(v6.0.3...v7.0.1)로 확인 완료 — breaking change 없음(위 "현재 상태" 절 근거).

## 비범위

- 이슈 #64의 다른 항목(ubuntu-24.04 고정, timeout-minutes/concurrency, push+pull_request 중복 트리거 제거, awk `'` 이식성, 자기오염 정규식, shellcheck/zizmor 도입, 브랜치 보호 API — GitHub Pro 업그레이드 없이는 막혀 있음)은 각각 별도 WU.
- `.github/dependabot.yml`(github-actions 생태계, cooldown) 신설 — 별도 WU.
- `scripts/acceptance-*.sh` 신설로 "서드파티 액션은 항상 SHA 고정"을 상시 CI 회귀로 강제 — 별도 WU(V1 M-1 반례 후속, 위 "적대 검증 로그" 참고).
- 이번 PR은 checkout 버전+SHA 고정 1개 AC만.

## 적대 검증 로그

### Codeaudit (읽기 전용, 2026-09-07)

PASS. 실제 diff(1 insertion/1 deletion)가 goal 문서 주장과 일치, AC-1/counter-AC를 fresh 재실행으로 확인, weakens-check 라벨 기계장치 부재를 재확인. 상세는 세션 기록 참고.

### V1 (`codex:rescue` → `humanreview`, fresh read-only, 2026-09-07)

**최초 판정: REQUEST_CHANGES.** 전문은 `docs/engineering/checkout-v7-sha-pin-v1-verdict-2026-09-07.md`.

- **M-1 (유효 반례, 채택)**: goal 문서 초안의 AC-1 grep 패턴 `uses: actions/checkout@[0-9a-f]{40}`은 (a) 정확한 SHA 뒤에 문자 추가, (b) checkout 행을 주석 처리, (c) 두 번째 checkout 행 추가 — 세 우회 모두 종료값 0(거짓 통과)이었다. → 위 "인수 기준" 절의 AC-1을 행 전체 anchor + exact-count 패턴 + 저장소 전체 유일성 검사로 교체해 반영했다. 교체 후 패턴으로 재실행: `anchored-match-count=1`, `git grep`도 `verify.yml:18` 단 한 줄만 출력 — M-1 반례가 더 이상 통하지 않음을 확인.
- **E-1 (V1 환경 한계, 코드 결함 아님)**: V1이 실행된 서브에이전트 샌드박스에서 `gh api`/`git ls-remote`가 네트워크 차단(`error connecting to api.github.com`, `Could not resolve host`)으로 전량 실패해 AC-2를 fresh 재현하지 못하고 NOT_RUN으로 판정했다. 이 세션(부모 세션)은 `gh` 인증·네트워크가 정상 동작하며, PR #67 생성 직후 및 이 정정 시점 두 차례 모두 `gh api .../commits/569ab89.../check-runs`로 `push`·`pull_request` 두 이벤트의 `verify` job이 각각 `completed success`임을 fresh 확인했다(로컬 HEAD=원격 PR HEAD=`569ab8988e2c3e41be7c7b9789c537b9a008602e` 일치, `mergeStateStatus=CLEAN`). CI 초록불이 이벤트 종류를 구분하지 않고 아무거나 하나만 보고 판단하는 실수를 피하기 위해 두 이벤트 모두 조회했다 — 결과: 둘 다 success. **AC-2 결론: PASS (부모 세션 fresh 증거로 종결, E-1은 V1 실행 환경 제약이었을 뿐 실제 결함이 아님).**
- 그 외 항목(SHA 정확성, node24, fetch-depth/persist-credentials 입력 호환성, 검사 약화 은닉 없음, counter-AC 2종)은 V1에서 전부 PASS로 확인됨.
- R9(발견 반례 영구 편입): M-1은 이 goal 문서(같은 PR)의 AC-1 검증 명령 자체를 교체하는 것으로 편입했다. 이 변경은 CI에 등록된 상시 회귀 스크립트가 아니라 1회성 수동 검증 문서이므로 `scripts/acceptance-*.sh` 신설은 하지 않았다(신설 시 `verify.yml`+`docs/sot/verification-commands.md` 양쪽 등록이 필요해 이번 PR의 명시적 비범위인 "checkout 버전+SHA 고정 1개 AC만"을 넘어선다) — 별도 WU 후보로 남긴다.

**정정 후 재판정**: 위 M-1 반영(문서만 수정, `.github/workflows/verify.yml`은 최초 커밋에서 변경 없음)과 E-1 종결로 두 차단 사유가 모두 닫혔다. L2 등급 요구(V1까지)를 충족.
