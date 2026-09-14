# strict 스킬 phantom 참조 수정 + 재발 원장 신설 — goal — 2026-09-07

## 상위 목표

`strict` 모드 진입점(`~/.claude/skills/strict/SKILL.md`)이 "이 저장소의 유일 정본"이라고
지목하는 파일·명령이 실제로 존재하도록 고쳐서, 다음 세션이 이 스킬을 읽고 없는 파일을
근거로 인용하거나(2026-08-27 재발 사례) 없는 명령(`npm run wt`)을 실행하려다 막히는 일을
없앤다. 성공 신호: 이 스킬 파일 안의 경로·명령 인용을 전부 뽑아 실존을 확인했을 때 0건 누락.

## 현재 상태 (file:line, 2026-09-07 실행 확인)

- `~/.claude/skills/strict/SKILL.md:8` — "정본 계약 = `docs/sot/30-strict-mode-contract.md`" → 이 저장소 히스토리 전체에 이 경로가 존재한 적 없음(`git log --all -- docs/sot/30-strict-mode-contract.md` 결과 0건)
- `~/.claude/skills/strict/SKILL.md:29` — "이 레포에서는 **`npm run wt -- <issue>-<slug>`**(규약 `../wt/…`, SOT-19 §4)만 쓴다" → 이 저장소엔 `package.json`이 없음(`find . -maxdepth 2 -iname package.json` 0건), `docs/sot/verification-commands.md`(2026-09-02 갱신판)가 이미 "이 저장소는 make 레포도 npm 레포도 아니다"라고 명시. `SOT-19`도 `docs/sot/INDEX.md`에 없음(이 저장소 SOT는 번호가 아니라 주제명 파일)
- `~/.claude/skills/strict/SKILL.md:48` — R4 "착수 시 `docs/sot/31-strict-recurrence-ledger.md`를 읽고" → 이번 커밋 전까지 이 파일 없음
- `~/.claude/skills/strict/SKILL.md:113` — "`tools/install-strict-skill.sh`를 실행" → 저장소 전체에 이 경로 없음(`find . -iname install-strict-skill.sh` 0건)
- 반면 이 저장소는 실제로 잘 도는 자기 완결 SOT를 이미 갖고 있다: `docs/sot/git-workflow.md`(워크트리 규약 = `git worktree add worktrees/<name> -b task/<name>`), `docs/sot/verification-commands.md`(게이트별 실제 명령 24개 CI 스텝까지 표로), `docs/sot/coding-principles.md`(P1~P24)

## 근본 원인

`strict` 스킬은 "core(범용)+overlay(레포별)"로 나눈다고 선언하지만, 실제 파일 안에서는
레포 고유 경로(`npm run wt`, `SOT-19`, `SOT-30`, `SOT-31`, `tools/install-strict-skill.sh`)를
core 본문에 그대로 하드코딩했다. 이 값들은 Valuehire_v6가 아닌 다른 저장소(번호 기반 SOT
파일명, `npm run wt` 스크립트, 설치 스크립트를 실제로 갖춘 저장소)에서 쓰던 값으로 보이며,
이 저장소로 넘어오면서 치환되지 않았다. 즉 "core/overlay 분리"가 선언만 있고 구조로
강제되지 않는다.

## 인수 기준 (EARS)

- **AC-1**: `~/.claude/skills/strict/SKILL.md`가 "이 저장소의 정본/명령"으로 인용하는
  모든 경로가, 이 저장소(Valuehire_v6)의 `git ls-files`에 실존해야 한다. 검증 명령:
  `grep -oE 'docs/sot/[a-zA-Z0-9._-]+\.md|tools/[a-zA-Z0-9._/-]+\.sh' ~/.claude/skills/strict/SKILL.md | sort -u`
  로 뽑은 각 경로를 `git ls-files --error-unmatch <path>`로 확인 — 전부 exit 0.
- **counter-AC**: 위 검사를 이 수정 *전*의 SKILL.md에 그대로 돌리면 최소 3건(30번,
  31번(수정 전), install-strict-skill.sh)이 실패해야 한다(수정이 실제로 뭔가 바꿨다는 증거).

## 계약 (입출력 모양)

- 입력: 없음(문서 텍스트 수정 + 신규 SOT 파일 1개 추가)
- 출력(2차 수정 반영): `~/.claude/skills/strict/SKILL.md`의 phantom 인용 수정(1차 4곳 + `/codex:rescue` FAIL 판정 후 2차로 SOT-30 라벨 7곳·§5 무조건 npm 2곳·재발 원장 자기모순·package.json 문구 정밀화 추가 반영), `docs/sot/31-strict-recurrence-ledger.md` 신설(기록 기준 재정의 포함), `docs/sot/INDEX.md` 1행 추가, 이 goal 문서 자신. **`docs/engineering/ci-pipeline-and-methodology-review-2026-09-07.md`는 이 PR 범위가 아니다 — codex가 스코프 무관 지적해 별도 PR(`task/ci-pipeline-review-doc`)로 분리했다.**

## 게이트 계획

- 코드(프로그램 로직) 변경 없음 → RED/GREEN 테스트 사이클 대상 없음. 대신 위 AC-1 검증 명령을 fresh 실행해 그 출력을 이 문서 `## 적대 검증 로그`에 원문 그대로 붙인다.
- 저장소 쪽 변경(`docs/sot/*`)은 워크트리(`worktrees/sot-strict-contract-fix`, 브랜치 `task/sot-strict-contract-fix`)에서 진행, PR로 배송.
- 글로벌 스킬 파일(`~/.claude/skills/strict/SKILL.md`) 수정은 `~/.claude/**` 경로라 리포 워크트리 규율 밖(직접 쓰기 허용 경로)이지만, 이 goal 문서에 diff 근거를 남겨 추적 가능하게 한다.

## 적대검증 정조준

- V1이 공격할 지점: "정말 이 저장소 전용 문제인가, 아니면 SKILL.md가 의도적으로 여러
  저장소를 가리키는 범용 값이고 내가 잘못 해석한 것 아닌가?" → 반박 근거: 헤더 블록쿼트
  자체가 "**이 레포(ValueHire)에서는** 그 문서가 유일 SOT다"라고 레포를 특정해서 선언함.
- "고친 값(`git worktree add worktrees/<name> -b task/<name>`)이 최신 관행과 실제로
  일치하는가?" → `worktrees/` 아래 실존 디렉터리 60개+ 전부 이 패턴과 일치하는지 대조.

## 비범위

- SOT 참조 무결성을 매 PR마다 자동으로 막는 CI 검사기(러너/훅) 신설은 이번 범위 밖 —
  원장(L1행)에 부채로 남기고 별도 GitHub 이슈로 추적한다(R4가 요구하는 "2회째 승격"은
  아직 임계 미도달 상태로 판단, 3회째부터 강제).
- `docs/sot/30-strict-mode-contract.md`라는 이름의 파일을 새로 만들지 않는다 — 이 저장소는
  번호 기반 SOT 파일명 관행이 없고(`docs/sot/INDEX.md` 확인), 새 이름을 추가하면 오히려
  SOT 중복이 생긴다(이미 있는 `coding-principles.md`+`verification-commands.md`+
  `git-workflow.md`가 그 역할을 이미 함).

## 적대 검증 로그 (후기록)

**자체 codeaudit 재실행 (2026-09-07, 커밋 반영 전 최종 확인)**

```
$ git log --all --oneline -- docs/sot/30-strict-mode-contract.md | wc -l
       0
$ find . -iname "install-strict-skill.sh" -not -path "*/worktrees/*" | wc -l
       0
```
→ AC-1의 counter-AC(수정 전 실패해야 함)가 여전히 유효함을 재확인. 두 경로 모두 이 저장소
히스토리에 존재한 적 없다.

**자체 codeaudit이 찾은 추가 반례(수정 커밋에 포함해 편입, R9)**: §2 "Stop 게이트 마커" 문단이
`npm run wt`뿐 아니라 `.claude/hooks/stop-evidence-gate.py`·`.claude/strict-active.json`
전체를 이 레포에 있는 것처럼 서술했다(`find` 둘 다 0건). 최초 3곳 수정에서 놓친 4번째
phantom이었다 — 원장 L3로 편입, 문단에 "hook 파일 없으면 미적용" 캐비트 추가로 마무리.

**남은 한계(정직하게 표기)**: 이 goal 문서와 codeaudit 모두 같은 세션(Claude)이 작성해
완전한 독립 검증이 아니다. `strict` §6이 요구하는 fresh V1(`/codex:adversarial-review`)은
별도로 `codex:rescue`를 호출해 진행한다 — 그 결과는 이 로그 아래에 이어 붙인다.

**V1 — `/codex:rescue` fresh 적대검증 (2026-09-07, commit 131a0b3 대상, Codex 세션
01a07788-c69d-7913-b769-ccdeb77375fb)**

**판정: FAIL — REQUEST_CHANGES.** 1차 수정(4곳)을 불충분하다고 정확히 잡아냈다. 반례
7건, 전부 재현 가능한 명령·출력 포함:

1. 프론트매터·본문에 "SOT-30" 라벨이 근거 없이 7곳 남음(§4 표·§1-11·§4.5·§1.5·§0 등
   존재하지 않는 절 인용) → **인정, 2차 수정에서 라벨 전체 제거**
2. Full Strict 절(§5)의 `npm run strict:gate`/`npm run check`가 여전히 무조건 명령 →
   **인정, 조건부(`package.json` 있으면/없으면)로 교체**
3. 재발 원장이 "2회 이상만 기록"이라면서 스스로 1회짜리 행(L2/L3)을 올린 자기모순 →
   **인정, 기록 기준을 "1회차부터 기록, 2회째부터 승격 의무"로 재정의**
4. "이 저장소엔 package.json이 없다"는 문구가 과거 이력(admin 워크스페이스용으로 한때
   존재, `packageManager: pnpm@11.22.0`만 있었고 `wt` 스크립트는 6개 히스토리 매니페스트
   전부에 없었음)을 안 밝혀 부정확 → **인정, "현재 트리에 없음"으로 정밀화**
5. `docs/engineering/ci-pipeline-and-methodology-review-2026-09-07.md`(83줄)이 이 goal의
   좁은 출력 계약과 무관한 스코프 크리프 → **인정, 별도 PR(`task/ci-pipeline-review-doc`)로
   분리**
6. 핵심 수정(`~/.claude/skills/strict/SKILL.md`)이 버전관리 밖이라 이 PR diff로 재현·롤백
   불가 → **구조적 한계로 인정하고 완화 못 함(범위 밖) — 이 goal 문서와 PR 설명에 명시해
   추적 가능하게 하는 것으로 대체**
7. `~/.codex/skills/strict/SKILL.md`(Codex 미러)와 해시가 다름 → **재확인 결과 무효**:
   그 파일은 애초에 Claude SKILL.md의 사본이 아니라 Codex 전용 독립 구현체("Codex는
   전역 `$strict`가 유일 구현체")이며, `grep`으로 대조한 결과 SOT-30/SOT-19/npm run wt/
   install-strict-skill.sh/stop-evidence-gate/30-strict-mode-contract/
   31-strict-recurrence-ledger 어느 것도 그 파일에 없다(0건) — 애초에 이번 결함군과
   무관한 별개 문서였다.

2차 수정 후 AC-1 재실행(`docs/sot/30-strict-mode-contract.md`, `tools/install-strict-skill.sh`
2건만 남고 둘 다 조건부/역사적 서술 문맥임을 `grep -n`으로 직접 확인, 정본 주장으로 쓰인
곳은 0건) — 나머지 4개 경로(`31-ledger`, `git-workflow.md`, `INDEX.md`,
`verification-commands.md`)는 전부 PASS.
