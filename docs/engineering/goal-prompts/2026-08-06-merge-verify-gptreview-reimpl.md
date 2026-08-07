# GOAL PROMPT — main에 verify/gptreview 재구현본 병합 (Phase 0-6)

**작성**: 2026-08-06 · **작성자**: Claude(이 세션) · **지위**: `/strict` 관행에 따라 남기는 goal 프롬프트.
이 파일 하나가 인수 기준 1개다. 실행자는 이 파일과 아래 명령들만으로 시작할 수 있어야 한다 — 대화 기록을 몰라도 된다.

**먼저 읽을 것**: `docs/engineering/v6-coding-principles-goal-2026-08-06.md`가 유일한 정본이다.
단, **그 문서를 포함해 이 프롬프트도 실행 전 재검증 대상**이다 — 초판 §0 E7은 diff를 안 열어보고 쓴
틀린 주장이었고(오늘 정정됨), Phase 0 표의 "완료" 표시도 실제로 커밋/파일을 확인하기 전엔 믿지 않는다.
**"문서에 그렇게 적혀 있다"는 "그 상태다"의 증거가 아니다.** 아래 명령을 실행자가 직접 다시 돌려서 확인하고 시작할 것.

---

## 0. 왜 (컨텍스트, 재추론 불필요)

`main`(현재 `2f45b7b`)은 `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §0의 E1·E3·E4·E5가
지적한 가짜 검증 스크립트(`verify.sh`의 자기 면제, `.claude/scripts/verify.js`의 하드코딩 8.5점·시뮬레이션
security·미실행 단계 ✅ 표시, `.claude/scripts/gptreview.js`의 네트워크 호출 0건)를 **지금도 그대로 갖고 있다.**

동시에 `worktrees/gptreview-real-impl`(브랜치 `task/gptreview-real-impl`, 커밋 `3cffb4d`)에
**이미 검증된 진짜 재구현본**이 존재한다 — `.claude/skills/verify/SKILL.md` + `local-checks.sh`,
`.claude/skills/gptreview/SKILL.md`. 이 세션이 오늘 그 3개 파일 전문을 직접 읽고 확인했다:
하드코딩 점수 0건, 실제 `Agent`/`Skill` 도구 호출, 미실행 단계는 "⏭️ 스킵"으로 정직 표기.

**단, 이 브랜치는 main에 병합된 적이 없다.** 그리고 main은 그 사이 별도로
`ce81445`~`2f45b7b` 커밋들로 "비밀번호 리터럴 제거"를 **다른 방식**(TDD RED→GREEN)으로 이미 끝냈다.
두 브랜치가 **같은 4개 파일**을 다르게 고쳐서 갈라졌다 — 그래서 이건 단순 파일 교체가 아니라 **병합**이다.

## 1. 인수 기준 (실행 가능한 명령 + 기대 출력, P2)

아래 스크립트가 **exit 0**이어야 "완료"다. 산문 판단 금지.

```bash
#!/usr/bin/env bash
set -euo pipefail
fail=0

# 1. 가짜 스크립트가 사라졌는가
for f in .claude/scripts/verify.js .claude/scripts/gptreview.js .claude/skills/verify.md .claude/skills/gptreview.md; do
  if [ -f "$f" ]; then echo "FAIL: $f 가 아직 존재함 (구버전 잔존)"; fail=1; fi
done

# 2. 진짜 재구현본이 main에 들어왔는가
for f in .claude/skills/verify/SKILL.md .claude/skills/verify/local-checks.sh .claude/skills/gptreview/SKILL.md; do
  if [ ! -f "$f" ]; then echo "FAIL: $f 가 없음 (재구현본 미병합)"; fail=1; fi
done

# 3. 하드코딩 점수/시뮬레이션 패턴이 저장소 어디에도 없는가
if git ls-files | xargs grep -lE "rating: 8\.5|// 시뮬레이션|status: 'ok'" 2>/dev/null | grep -v "docs/engineering/"; then
  echo "FAIL: 하드코딩/시뮬레이션 패턴이 추적 파일에 남아있음"; fail=1
fi

# 4. main의 기존 비밀번호-제거 성과가 회귀하지 않았는가 (기존 verify.sh 그대로 통과해야 함)
if [ -f verify.sh ]; then
  bash verify.sh || { echo "FAIL: verify.sh 회귀"; fail=1; }
else
  echo "FAIL: verify.sh 가 사라짐 (E1 재발 방지 장치 소실)"; fail=1
fi

# 5. settings.json에 죽은 스킬 트리거가 안 남아있는가
if [ -f .claude/settings.json ] && grep -q '"command": "node .claude/scripts' .claude/settings.json; then
  echo "FAIL: settings.json이 삭제된 스크립트를 여전히 가리킴"; fail=1
fi

[ "$fail" -eq 0 ] && echo "PASS: 병합 완료, 가짜 검증 스크립트 0건" || exit 1
```

## 2. 하네스 게이트 순서 (건너뛰지 않는다)

1. **게이트0 시작자격**: `git status` 로 다른 미완료 작업이 없는지 확인. 위 명령들(merge-base, diff --stat)을
   실행자가 스스로 다시 돌려 4개 충돌 파일 목록을 재확인한다 — 이 문서의 목록을 베끼지 말 것.
2. **게이트2 RED 먼저**: 새 워크트리(`worktrees/merge-verify-reimpl/`, 브랜치 `task/merge-verify-reimpl`)를 파고,
   위 §1 스크립트를 `scripts/acceptance-0-6.sh`로 커밋한다. **이 시점엔 반드시 FAIL이어야 한다**(아직 병합 전이므로).
   FAIL이 안 뜨면 스크립트가 틀린 것 — 병합했다고 착각하고 있는 것이다.
3. **게이트3 구현**: `git merge task/gptreview-real-impl`을 그 워크트리에서 실행. 충돌 4개 파일 해소 원칙:
   - `.claude/scripts/gptreview.js` → **삭제**(워크트리 쪽이 삭제를 선택했으므로 그걸 따른다. main의 비밀번호 제거 커밋은
     "삭제될 파일 안의 비밀번호를 지운 것"이므로 파일 자체가 없어지면 그 우려는 자동 해소된다)
   - `.claude/settings.json` → **워크트리 버전 채택**(스킬 폴더 방식은 settings.json 등록이 필요 없음 — 이 세션에서
     `.claude/skills/*/SKILL.md`가 별도 등록 없이 자동 인식되는 것을 이미 확인함)
   - `.claude/skills/gptreview.md` → **삭제**(`.claude/skills/gptreview/SKILL.md`로 대체됨)
   - `SKILLS_GUIDE.md` → **수동 병합** — 워크트리 쪽 구조 설명 + main 쪽에 남은 "비밀번호 관련 서술"이 있다면
     그 문장만 워크트리 버전에 옮겨붙인다. 자동 병합에 맡기지 말고 최종본을 사람이 읽을 수 있게 직접 정리.
4. **게이트4 검증**: 위 §1 스크립트가 이제 **PASS**해야 한다. 추가로 `git log --all -S"$(head -1 .secret-patterns)" --oneline`
   (verify.sh가 검색하는 실제 리터럴 — `.secret-patterns` 참조, 문서에 평문으로 적지 않는다)로 새로 유입된 평문이 없는지 확인.
   <!-- 2026-08-07 0-2 작업에서 새니타이즈: 이 자리에 있던 평문 리터럴을 제거함 -->

5. **적대검증(`/strict` 요구사항)**: `/codex:rescue`로 이 병합 diff를 독립 재검증 요청. 최소 확인 항목 —
   ① 충돌 해소가 두 브랜치의 의도를 모두 보존했는가 ② `.claude/skills/verify/local-checks.sh`가
   실제로 실행 가능한 셸 스크립트인가(`bash -n`으로 문법 확인) ③ P13("적대검증 판정서 첨부 CI 필수")을
   미리 시연하는 셈 치고, 이 병합 PR 본문에 Codex 판정 파일 경로를 직접 첨부.
6. **게이트5 배송**: `make ship` 또는 동등 절차로 PR. **squash는 하지 않는다** — 0-2(커�밋 5개 정리)는
   이 작업과 별개의, 더 파괴적인(git history rewrite) 작업이라 별도 goal 프롬프트로 분리한다(§3 참조).

## 3. 이 프롬프트가 하지 않는 것 (범위 고정)

- ❌ `.env` 회전, 커밋 히스토리 squash(0-2) — 별도 goal 프롬프트 필요, 여기서 섞지 않는다(harness: PR = 인수기준 1개)
- ❌ `gitleaks` 도입, 원격 push(0-5) — 이것도 별개 작업
- ❌ `/strict` 3벌 통합(0-8) — **오늘 재확인 결과 여전히 살아있는 문제이나 v6 저장소 범위 밖.**
  `~/.claude/skills/strict`·`~/.codex/skills/strict`·`~/.codex/prompts/strict.md` 3벌이 **글로벌 설정**에 있고
  v4·v5·v6 전부에 영향을 준다. 별도 goal 프롬프트로 분리하되, 대상은 이 저장소가 아니라 `~/.claude`·`~/.codex`다

## 4. 완료 후 정본 문서에 남길 것

`docs/engineering/v6-coding-principles-goal-2026-08-06.md` §5 Phase 0 표의 0-6 행 "완료 판정" 칸을
위 §1 스크립트의 **실제 실행 출력**으로 채운다("시뮬레이션 코드 0건"이라는 산문이 아니라 `PASS: ...` 문자열 그대로).
