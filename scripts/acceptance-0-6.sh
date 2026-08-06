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
# [[:space:]]는 자기 매칭 방지용: 이 스크립트 자신이 패턴 리터럴을 포함해 검출되는 것을 막되
# (파일명 자기 면제는 E1 사고 재현이라 금지), 대상 코드 검출력은 원 패턴과 동일함을
# git show 4d53eac:.claude/scripts/verify.js 로 확인함(5건 동일 검출).
if git ls-files | xargs grep -lE "rating:[[:space:]]8\.5|//[[:space:]]시뮬레이션|status:[[:space:]]'ok'" 2>/dev/null | grep -v "docs/engineering/"; then
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
