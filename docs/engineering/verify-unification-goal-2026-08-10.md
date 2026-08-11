# goal — verify·codeaudit 통합 (로컬 품질검사 도구, 강제장치 없음)

**작성일**: 2026-08-10 22:54 KST (v5: 2026-08-11 — 외부 적대검증에서 required-check 강제장치 자체가 이 GitHub 요금제에서 불가능함이 실측 확인됨. 사장님 결정: **Pro 업그레이드/공개전환 안 함 → 강제장치를 아예 뺀다.** 목표를 "강제 검증 시스템"에서 "로컬 품질검사 도구"로 축소)
**위험 등급**: **L2** (v4까지는 L3였으나, 머지를 막는 장치가 전부 빠지면서 "라이브 동작 변경" 성격이 사라짐. 단 SOT 수정은 여전히 있어 L2 상한 유지)
**베이스 커밋**: `ec201dc`
**정본 원칙**: `docs/engineering/v6-coding-principles-goal-2026-08-06.md` (P1~P22), 특히 P1·P3·P4·P11·P13
**검증 이력(별도 문서)**: `docs/engineering/verify-unification-verification-log-2026-08-10.md` — v1~v5 적대검증 전체 로그, 정정 기록
**장기 보류 문서**: `docs/engineering/verify-independent-trust-boundary-goal-2026-08-11.md` — 옛 AC-8·AC-18(로컬 봇 독립 신뢰경계). **착수 시점 미정으로 격하** — 진짜 강제장치가 필요해지는 시점(예: 팀원 합류, GitHub Pro 전환)까지 보류.

## 이번 v5에서 뭐가 왜 빠졌는가 (외부 적대검증 + 사장님 결정)

2026-08-11 외부 적대검증(Codex 세션, 이 세션 밖에서 실행)이 실측으로 확인:
- `gh api repos/.../branches/main/protection` → `403 Upgrade to GitHub Pro or make this repository public`
- `gh api repos/.../rulesets` → 동일 403
- 즉 **이 저장소 요금제에서는 GitHub 쪽 required-check/branch protection 자체를 설정할 수 없다.**

사장님 결정: "Pro를 안 쓸 거라면 required-check 강제 장치는 아예 빼는 편이 낫다. 우회 가능한 로컬 훅을 강제 장치라고 포장하는 것보다 훨씬 정직하고 단순하다." 이에 따라:
- **삭제**: AC-4(required-check 강제), AC-6(검증기 PR ↔ 제품 PR 서버측 분리), AC-7(AC-6을 보호하던 base-pinned 뮤테이션 코퍼스)
- **명칭 변경**: `enforced_by` → `checked_by` (강제한다는 인상을 주지 않기 위해 — 이 필드는 "이 규칙을 검사하는 스크립트가 어디 있는가"만 가리키지, "위반 시 머지를 막는다"는 뜻이 아니다)
- **역할 축소**: AC-5는 "머지 허가 판정기"가 아니라 "로컬/CI 검사 결과를 정직하게 집계해서 보여주는 도구"로만 남는다
- **장기 보류**: 독립 신뢰경계 문서(옛 AC-8·AC-18) 착수 시점 미정

**남는 구조**:
```
로컬 verify.sh / git hook   → 실수 방지용 (우회 가능, --no-verify로 건너뛸 수 있음을 인지)
GitHub Actions              → 결과 표시용 (머지를 막지 않음)
최종 머지 판단              → 사장님이 CI 결과와 diff를 직접 보고 결정
```
**감수하는 한계**: `--no-verify`로 로컬 검사를 우회할 수 있다. 순차 2-PR 공격(검증기를 먼저 약화 → 다음 PR에서 악용)도 못 막는다. 이걸 막으려면 진짜 독립 판정자가 필요하고, 그건 장기 보류된 분리 문서의 몫이다.

## AC 번호 대응표 (결번 이유)

| 번호 | 상태 |
|---|---|
| AC-4, AC-6, AC-7 | **v5에서 삭제** — required-check 강제장치 및 그 보호 장치. 이 GitHub 요금제에서 불가능함이 실측 확인됨(위 참조) |
| AC-8, AC-18 | `verify-independent-trust-boundary-goal-2026-08-11.md`로 분리, 장기 보류 |
| AC-10 | AC-2로 병합됨 |

---

## ① 현재 상태 (실측, file:line)

| 파일 | 확인된 사실 |
|---|---|
| `.claude/skills/verify/SKILL.md:58` | 판정 기준이 "1~3단계 중 하나라도 ❌면 배포 보류"로만 정의됨. `NOT_RUN`(스킵)은 이 조건에 안 걸림 |
| `.claude/skills/verify/local-checks.sh:19-24` | `package.json` 없으면 전부 skip 후 `exit 0` |
| `verify.sh:55` | `SCAN_SOURCE="${VERIFY_SCAN_SOURCE:-worktree}"` — 기본 입력이 작업트리 |
| `verify.sh:92` | 비밀 스캔만 하고도 "PASS" 출력 |
| `verify.sh` (worktree 모드) | `git ls-files` 기반이라 미추적 파일은 스캔 안 하고도 PASS 출력 |
| `.secret-patterns.default` | Discord/Slack 웹훅 URL, `sk-ant-` 키 패턴을 탐지 못함(2026-08-11 보안 리뷰 실측). 수정안이 `stash@{0}`에 보존돼 있고, 별도 워크트리 PR로 다시 진행 예정(비범위 참조 — PR #4와 조율 필요) |
| `docs/sot/coding-principles.md:18`(P3) | "NOT_RUN 하나라도 있으면 전체 PASS 불가" — verify 정의와 직접 충돌 |
| `docs/sot/coding-principles.md:26`(P11) | 파일 300/600줄·함수 60/100줄·PR 3,000줄 초과 절대금지·생성물/마이그레이션/픽스처 면제 — verify·codeaudit 어디에도 없음 |
| `suppressions.yaml:50-66` | `gate-scope-gaps` 항목이 `.github/workflows/*`, `.claude/skills/*/local-checks.sh`가 이미 검사 범위 밖임을 자인 |
| `.github/workflows/verify.yml:16,18` | `ubuntu-latest`, `actions/checkout@v4` — SHA/digest 고정 없음 |
| **`gh api .../branches/main/protection`, `.../rulesets`** | **2026-08-11 실측: 둘 다 403 "Upgrade to GitHub Pro or make this repository public"** — required-check 계열 전부 이 요금제에서 불가능 |
| **Gate 0** | `bash scripts/session-status.sh` → `RED: 1/4`. 원인: `acceptance-0-2.sh` → "unreachable 객체 61건 잔존". **이 goal의 Phase 1 착수 전 별도로 해소 필요**(⑥ 비범위 참조 — 이 문서가 만드는 문제 아님, 기존 미해결) |
| **PR #4**(`task/secret-session-patterns`) | OPEN. 세션 쿠키류 자격증명(LinkedIn/CDP/Playwright 산출물 형식) 탐지 패턴 — 이 문서가 다루는 Discord/sk-ant 패턴과 대상은 다르지만 같은 파일(`.secret-patterns.default`)을 건드림. 착수 시 이 PR과 순서 조율 필요 |
| 지시 원장(`task-contract.yaml` 류) | 존재하지 않음 |

## ② 근본 원인 (v5: 정직하게 재정의)

검증의 "실행"과 "판정 권한"이 같은 신뢰경계 안에 있다는 근본 문제는 **이 문서로 해결하지 않는다.** v3~v4에서 이 문제를 GitHub required-check로 저장소 안에서나마 강화하려 했으나, 그 메커니즘 자체가 이 요금제에서 동작하지 않는다는 게 확인됐다. **이 문서가 실제로 하는 일은 훨씬 작다** — 사장님이 머지 여부를 판단할 때 참고할 정보(로컬 검사 결과, LOC 예산, 억제장부 상태)를 더 정직하고 완전하게 보여주는 것뿐이다. 최종 판단은 기계가 아니라 사장님이 diff와 CI 결과를 보고 내린다.

## ③ 인수 기준 (EARS + 검증 명령 + counter-AC)

> **이 저장소 SOT(`docs/sot/git-workflow.md:15,21`)에 따라 AC 1개 = 워크트리 1개 = 브랜치 1개 = PR 1개다.** Phase(④)는 실행 순서를 묶어 보여주는 그룹일 뿐, 워크트리 단위가 아니다 — 오해로 v4까지 "Phase 1개 = 워크트리 1개"로 잘못 설계돼 있었다(외부 적대검증이 잡음, 정정 완료).

**AC-1 (항상적용 최소규칙 계층)**
When verify가 실행되면, then `docs/sot/always-apply-rules.yaml`의 각 규칙은 `mechanism_id`(AC-M 레지스트리 id), `negative_canary`(그 규칙을 어긴 샘플이 실제로 FAIL 나는지 확인하는 고정 샘플), `required`(true|false) 필드를 가져야 한다. `required: true`인 규칙만 AC-5의 `NOT_RUN` 집계에 들어간다.
검증: 각 규칙의 `negative_canary` 샘플을 실행해 전부 FAIL 나는지 확인 + `required: true` 규칙 수와 AC-5 출력의 해당 항목 수 일치 확인
counter-AC: 무효한 규칙 1건을 넣고 "1건 대조 완료"만 출력하면 가짜.

**AC-2 (영향범위 기반 지시·코드 검색 — 舊 AC-2+AC-10 병합)** — *제품코드 도입 후 착수, 지금 스캐폴딩도 안 지음*
When verify가 diff를 받으면, then diff의 변경 심볼 + 그 호출자/피호출자(impact closure)를 기준으로 원장의 관련 지시를 검색해야 한다.
검증: (착수 안 함)
counter-AC: 직접 호출자 1건만 포함하고 간접호출을 누락하면 가짜(착수 시 적용).

**AC-M (mechanism_id / checked_by 레지스트리)**
When AC-1의 규칙이 `mechanism_id`를 선언하거나 AC-3 원장 항목이 `checked_by`를 선언하면, then 그 값은 `docs/sot/mechanism-registry.yaml`의 `id` 필드와 정확히 문자열 일치해야 한다. 각 레지스트리 항목은 `id, path, target, stage(pre-commit|pre-push|ci|manual), required, ci_mirror_job(stage:ci일 때만 필수)`를 가진다. **`target`은 함수명이 아니라 그 `path` 파일 안에서 실제로 나타나는 정확한 명령 문자열이다**(예: 실제 `hooks/pre-commit:71`의 `SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh`처럼 — 존재하지 않는 함수를 지어내지 않는다). `stage: manual`은 git hook도 CI job도 아니고 goal 작성 시점에 사람이 실행하는 검사(예: AC-20)를 위한 것이며, 이 경우 "훅 파일에서 호출되는지" 검사는 면제되고 대신 "그 검사 스크립트가 실행 가능한 파일로 실제 존재하는지"만 확인한다. **`checked_by`는 "이 검사가 어디서 도는지"만 가리킨다 — 위반 시 머지를 막는다는 의미는 어디에도 없다.**
검증: `scripts/verify/check-mechanism-registry.sh`(신설, 이 AC의 GREEN 산출물)가 다음을 수행한다 — (1) YAML 파싱 후 `id` 유일성 확인, exit 1 if 중복 (2) 각 항목의 `path`가 `[ -f "$path" ]`로 실존하는지 확인, 없으면 exit 1 (3) `stage`가 `pre-commit|pre-push`면 `grep -qF -- "$target" "$path"`로 `target` 문자열이 그 훅 파일 안에 있는지 확인, 없으면 exit 1(죽은 target) (4) `stage: ci`면 `ci_mirror_job` 값이 `.github/workflows/verify.yml`의 `jobs:` 키 중 하나와 일치하는지 확인 (5) `stage: manual`이면 `path`가 실행권한(`-x`)을 가진 파일인지만 확인. fixture 3종: 정상 항목(exit 0), `path` 없는 항목(exit 1), `target` 문자열이 실제 훅에 없는 항목(exit 1) — 이 셋을 `scripts/verify/fixtures/mechanism-registry/`에 두고 `check-mechanism-registry.sh`가 각각 기대한 exit code를 내는지 RED 테스트가 확인한다.
counter-AC: 레지스트리에 없는 임의 문자열을 ID로 써도 통과하거나, 아무도 안 부르는 죽은 target이 통과하면 가짜. `stage: manual`을 아무 항목에나 붙여서 "훅에서 호출되는지" 검사를 회피하면 가짜 — `manual`은 AC-M 구현 시점에 실제로 `stage: manual`이 필요한 항목(AC-20 하나)에만 예외적으로 허용되고, 그 근거를 원장 자체에 `manual_reason` 필드로 남겨야 한다.

**AC-3 (지시 원장 스키마 + 시맨틱 검증기)**
When 지시가 원장에 등록되면, then `id, text, status, supersedes, repo, scope, file_or_module_tags, expiry, checked_by` 필드를 가져야 하고, 별도 시맨틱 검증기가 ID 유일성·`supersedes` 참조/순환 없음·`repo`/`scope` 정합·`expiry` 의미(달력 파싱)까지 검사해야 한다. `checked_by`의 레지스트리 존재 여부 검사는 AC-M 완료 전까지 "비어있지 않은 문자열"만 확인하는 완화 모드로 동작하고, AC-M 완료 후 전체 검증으로 전환된다.
검증: 빈 문자열·잘못된 repo·중복 ID·dangling supersedes·순환 참조 샘플이 전부 거부되는지 확인
counter-AC: 필드가 채워지기만 하면(값 검증 없이) 통과하면 가짜.

**AC-5 (3상태 집계기 — 로컬 리포트 전용, 머지 게이트 아님)**
When verify가 실행되면, then `docs/sot/mechanism-registry.yaml`에 등록되고 `required: true`로 표시된 항목 전부를 실행하고, 각각의 `PASS|FAIL|NOT_RUN`을 있는 그대로 출력해야 한다. **하나라도 `NOT_RUN`이면 최종 요약을 "전체 통과"라고 쓸 수 없다** — 이건 머지를 막는 규칙이 아니라, 사장님께 보여주는 리포트가 실제 상태를 정직하게 반영해야 한다는 규칙이다(P3).
검증: `required: true` 규칙 중 하나를 일부러 `NOT_RUN` 상태로 만들고, verify 최종 요약이 "통과"가 아니라 "NOT_RUN 존재"로 나오는지 확인. **AC-1 원장의 `required:true` 규칙 수와 AC-M 레지스트리의 `required:true` 항목 수를 비교할 때 개수가 아니라 `mechanism_id`/`checked_by` 값의 집합(set) 자체가 정확히 일치하는지 확인**(개수만 같고 ID가 다른 경우를 잡기 위함)
counter-AC: `required: true` 검사를 레지스트리에서 통째로 지워서 `NOT_RUN`조차 안 만들면 가짜. `NOT_RUN`이 있는데도 최종 줄에 "PASS"나 "통과"라고 쓰면 가짜. **원장의 규칙 A(`required:true`)를 지우고 무관한 규칙 B(`required:true`)를 새로 만들어 개수를 맞추면(ID는 다른데 개수만 같음) 지금처럼 개수만 비교하면 못 잡는다 — ID 집합 비교로 잡아야 한다.**

**AC-20 (과거 프롬프팅 지시 대조 — MEMORY.md 회수 자동화)**
When 새 AC의 goal/RED 작성 시점(게이트 0~1)이 오면, then `scripts/memory-recall-check.sh "<AC 제목·키워드>"`가 이 프로젝트의 auto-memory 인덱스(`~/.claude/projects/<이 저장소 경로>/memory/*.md`, `MEMORY.md`)를 키워드로 전수 검색해, 관련 가능성 있는 메모리 파일을 전부 나열해야 한다. **이건 "코드가 과거 지시와 충돌하는지" 자동 판정이 아니다** — 코드 호출관계 분석 없이 순수 텍스트 검색만으로 관련 후보를 놓치지 않고 goal 문서 앞에 늘어놓는 것까지가 기계의 역할이고, "정말 어긋나는가"는 그 목록을 보고 사람(또는 goal 작성자)이 판단한다. 검색 결과는 goal 문서의 회수(C) 절에 그대로 첨부돼야 한다.
검증: 알려진 feedback 메모리 파일(예: `feedback_no_tool_boundary_redesign.md`)의 키워드로 검색했을 때 그 파일이 결과 목록에 실제로 나오는지 확인 + goal 문서에 그 결과가 첨부됐는지 확인
counter-AC: 검색을 안 하거나, 검색은 했는데 결과를 goal 문서에 옮겨적지 않으면 가짜. 검색 범위를 `MEMORY.md`의 인덱스 목록으로만 제한하고 실제 메모리 파일 본문은 안 읽으면(제목만 보고 관련 없다고 오판할 위험) 가짜 — 본문까지 grep해야 한다.
**AC-M 연동**: 이 스크립트는 `docs/sot/mechanism-registry.yaml`에 `stage: manual`(AC-M §manual 정의, `manual_reason` 필드 포함)로 등록돼야 AC-5의 집계 대상이 된다 — git hook이나 CI job이 아니라 goal 작성 시점에 사람이 직접 실행하는 유일한 `required: true` 항목이다.

**AC-9 (검증 대상 diff 시작 시 고정)**
When verify가 AC-11의 격리 스냅샷을 확보하면, then base/head SHA·diff SHA-256을 그 스냅샷 시점에 고정하고, 이후 모든 단계는 이 고정된 스냅샷만 참조해야 한다.
검증: 스냅샷 확보 후 원본 작업트리를 변경해도 판정이 그대로인지 확인
counter-AC: HEAD는 그대로 두고 작업트리 파일만 단계 사이에 바꿔치기해도 안 잡히면 가짜.

**AC-11 (검증 실행 격리)**
When local-checks.sh가 테스트/빌드를 실행하면, then OS/컨테이너 수준의 실제 읽기전용 마운트에서 실행하고, writable 출력 경로는 allowlist로 제한하며, tracked blob hash뿐 아니라 untracked/ignored 파일·`.git` 메타데이터까지 실행 전후 비교해야 한다. 네트워크는 기본적으로 전면 차단하고, 특정 명령만 명시적 allowlist로 예외 허용한다.
검증: 실행 중 소스 파일 쓰기 시도가 OS 권한 오류로 실패하는지, untracked 파일 생성이 탐지되는지, allowlist 밖 네트워크 호출이 연결 자체에서 실패하는지 확인
counter-AC: `git diff --stat`만 보고 파일을 변경 후 원복하거나 untracked/ignored 파일을 바꾸면 안 잡히면 가짜.

**AC-12 (서브에이전트 원문-요약 무결성)**
When 품질/보안 리뷰 서브에이전트가 finding을 반환하면, then finding은 즉시 구조화 스키마로 정규화·해시 보존되고, 최종 보고서는 원문을 수정하지 않고 전체 record의 multiset이 원문과 일치해야 한다.
검증: 원문 5건 중 1건의 severity만 낮춘 샘플이 불일치로 탐지되는지 확인
counter-AC: ID 집합만 대조하고 내용이 바뀌어도 안 잡히면 가짜.

**AC-13 (프롬프트 인젝션 내성 시험)** — *제품코드 도입 후 착수*
When verify가 서브에이전트 리뷰를 돌리면, then 코퍼스 각 항목의 기대 결함 ID 집합을 미리 정의하고, 반복 N회 중 최소 성공률을 충족해야 리뷰 채널이 유효로 인정된다.
검증: (착수 안 함)
counter-AC: "안전합니다" 한 문구만 피하고 무관한 경고 하나로 때우면 가짜.

**AC-14 (테스트 효과성 정량 게이트)** — *제품코드 도입 후 착수*
Where 제품 테스트가 존재하면, then 언어별 mutation engine으로 최소 kill score·critical mutant 100% 규칙을 적용한다.
검증: (착수 안 함)
counter-AC: assertion 수 감소만 보고 mutation score를 안 보면 가짜.

**AC-15 (브라우저 증거 ↔ DB readback 결합)** — *제품코드 도입 후 착수*
Where 외부 경계 코드가 변경되면, then nonce/run ID·intent record·실행시각·artifact hash·독립 read-only credential로 재조회한 값을 하나의 receipt 스키마로 묶어야 한다.
검증: (착수 안 함)
counter-AC: 상관관계 ID 없이 로그와 DB 값을 나열만 하면 가짜.

**AC-16 (억제장부 스키마 검증)**
When `suppressions.yaml`에 항목이 등록되면, then owner·reason·issue·expiry가 모두 채워지고, expiry는 미래의 유효한 달력 날짜여야 하며 owner/issue/check는 등록된 레지스트리를 참조해야 한다. expiry 경과 시 CI가 즉시 FAIL해야 한다.
검증: 빈 owner, 과거 날짜, `2026-02-31`, 존재하지 않는 issue/check ID 샘플이 전부 거부되는지 확인
counter-AC: 필드 존재 여부만 보고 값의 의미를 안 보면 가짜.

**AC-17 (실행환경 전체 고정)**
When CI가 실행되면, then `verify.yml`의 모든 `uses:` 항목이 40자 SHA로 고정되고, 러너/컨테이너 이미지 digest·OS/toolchain 버전·lockfile hash가 자체 완결된 별도 manifest에 포함돼야 한다. manifest에 적힌 digest 값은 그 CI run이 실제로 사용한 이미지 digest와 readback으로 일치해야 한다.
검증: `verify.yml`에서 SHA가 아닌 태그 잔존 여부 전수 grep + manifest의 digest 값을 실제 CI run의 로그에서 readback한 digest와 대조
counter-AC: `checkout` 하나만 SHA로 바꾸고 나머지가 남으면 가짜.

**AC-19 (P11 코드 예산 전체)**
When PR이 파일을 추가/수정하면, then 파일 hard 600/soft 300줄·함수 hard 100/soft 60줄을 검사하고(생성파일·마이그레이션·픽스처는 면제), PR 전체 diff가 3,000줄을 초과하면 예외 없이 hard FAIL해야 한다. soft 초과는 AC-16 원장에 등록된 예외만 통과하고, 미등록 soft 초과는 명시적으로 FAIL한다(3상태 계약 밖 상태 없음).
검증: 700줄 초과 무예외 샘플(FAIL), 3,000줄 초과 PR(예외 등록해도 FAIL), 생성파일 700줄(면제로 PASS), 함수 61/101줄 경계값 확인
counter-AC: 큰 경고만 출력하고 exit 0으로 끝나면 가짜.

## ④ Harness 게이트 진행 계획

| Phase(순서 그룹) | 포함 AC (각 AC = 별도 워크트리·PR) | 선행조건 |
|---|---|---|
| **Phase 1** | AC-M → AC-3 → AC-16 → AC-19 → AC-1 → AC-20 → AC-5 | AC-M이 AC-1·AC-3의 전제. AC-16이 AC-19의 전제. AC-20(과거지시 대조)은 다른 AC와 독립이라 아무 데나 둬도 되나 편의상 여기. AC-5(집계기)는 항상 마지막(AC-20의 스크립트도 레지스트리에 등록돼야 집계 대상이 됨) |
| **Phase 2** | AC-11 → AC-9 → AC-17 | AC-11(격리)이 AC-9의 전제. AC-17은 자체완결 |
| **Phase 3** | AC-12 | 독립 |
| *(제품코드 도입 후, 별도 goal 문서)* | AC-2, AC-13, AC-14, AC-15 | |
| *(장기 보류)* | 舊 AC-8·AC-18 | `verify-independent-trust-boundary-goal-2026-08-11.md` |

## ⑤ SOT 체크리스트

- `docs/sot/verification-commands.md` — 게이트 4 명령 정본, 수정 필요
- `docs/sot/coding-principles.md` — P3·P11과 정합화. **추가(2026-08-11 외부 검증 지적): P13 등에 남아있는 "시스템으로 강제", "CI가 최종 방어선" 같은 문구가 v5의 "강제장치 없음" 결정과 충돌한다 — AC-1~AC-20 배송 시 이 문구들을 "리포트 도구, 최종 판단은 사람" 톤으로 diff 동봉**
- `docs/sot/hook-contracts.md` — 동일 사유로 "판정 권한은 CI" 류 문구 정합화 필요
- 신설: `docs/sot/instruction-ledger.schema.json`, `docs/sot/always-apply-rules.yaml`, `docs/sot/mechanism-registry.yaml`(AC-M), `docs/sot/verify-environment-manifest.json`(AC-17)
- 신설(정보용, CI 강제 아님): `docs/sot/verify-known-limitations.md` — "순차 2-PR 공격은 이 도구로 못 막는다"는 사실만 기록. 존재 여부를 어떤 check도 조건으로 삼지 않는다(v4에서는 AC-6이 이걸 조건으로 삼았으나 AC-6 자체가 삭제됨)

## ⑥ 비범위

- 舊 AC-4·AC-6·AC-7(required-check 강제 계열) — GitHub Pro/공개 전환을 안 하기로 결정해 완전 삭제
- 舊 AC-8·AC-18(독립 신뢰경계) — 장기 보류, 착수 시점 미정
- AC-2·13·14·15 — 스캐폴딩도 지금 짓지 않음
- **Gate 0 해소(`acceptance-0-2.sh` unreachable 객체 61건)** — 이 문서가 만든 문제가 아니라 기존 미해결 상태. `git gc`류 되돌리기 어려운 작업이 필요할 수 있어 별도로 사장님 확인 후 처리(이 goal의 Phase 1 착수 전제조건이지만, 이 goal 자체의 작업은 아님)
- **`.secret-patterns.default`의 Discord/sk-ant 패턴 추가** — `stash@{0}`에 보존됨. PR #4(세션 쿠키 패턴)와 순서·범위 조율 후 별도 워크트리 PR로 재작업(이 goal 문서의 AC는 아님, 별도 트랙)
- codeaudit을 v4·v5 저장소에도 강제 전환

## ⑦ 롤백 절차

AC별 PR이므로 문제 AC만 revert. 병합 전 상태를 태그(`pre-verify-unify-2026-08-11`)로 보존.

## ⑧ 영향 반경

verify가 고장 나도 **아무것도 자동으로 막히지 않는다**(강제장치가 없으므로) — 대신 사장님이 참고하는 리포트가 부정확해질 뿐이다. 순차 2-PR 공격, `--no-verify` 우회는 이 도구로 못 막는 것으로 확정하고 `verify-known-limitations.md`에 기록만 한다(강제하지 않음).

## ⑨ 계약 스펙

**판정 상태는 정확히 3개뿐이다: `PASS | FAIL | NOT_RUN`.**

원장(`instruction-ledger.jsonl`) 스키마:
```json
{
  "id": "R-0142", "text": "...", "status": "active", "supersedes": null,
  "repo": "Valuehire_v6", "scope": "always", "file_or_module_tags": [],
  "created": "2026-08-04", "expiry": null,
  "checked_by": "secrets-render-check"
}
```
verify 최종 판정 스키마:
```json
{ "check_id": "string", "subject_sha": "string(40)", "status": "PASS|FAIL|NOT_RUN", "detail": "string|null" }
```
mechanism 레지스트리(`docs/sot/mechanism-registry.yaml`) 스키마 (AC-M, 실제 훅 문구로 정정됨):
```yaml
- id: "secrets-scan-precommit"
  path: "hooks/pre-commit"
  target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"   # hooks/pre-commit:71과 문자 그대로 일치해야 함
  stage: "pre-commit"    # pre-commit | pre-push | ci | manual
  required: true
- id: "memory-recall-check"     # AC-20용 — stage:manual의 유일한 정당 사례
  path: "scripts/memory-recall-check.sh"
  target: "scripts/memory-recall-check.sh"
  stage: "manual"
  manual_reason: "goal 작성 시점(게이트 0~1)에 사람이 실행하는 검사라 git hook/CI 어디에도 배선되지 않는다 — AC-M §manual 정의 참조"
  required: true
```

> 봇 승인 manifest 스키마는 이 문서 범위 밖 — `verify-independent-trust-boundary-goal-2026-08-11.md`(장기 보류) 참조.
