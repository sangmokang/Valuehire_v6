# 다음 세션 프롬프트 — PII SOT 예외 재작성 외부 독립 검증과 push 승인 (2026-09-15)

## 결론

B안(무단 생성 브랜치 bd1c812 폐기 후 정식 재작성)이 완료됐다. `task/pii-sot-exception-redo-20260915`(HEAD `6e7ba6c`, origin/main `fc6beed` 기준)에서 3대 결함(①범위: 승인 목록 밖 `.md` 통과 ②신뢰경계: 검토 원장 자유 텍스트 자가승인 ③시점: CI에서만 차단)을 모두 고쳤다. `bash scripts/acceptance-hs-a4.sh`가 CHECKED: 45로 통과했고, 세 결함 각각 변이 테스트(구현을 일부러 고장 낸 사본)로 관련 시험이 실패로 뒤집힘을 확인했다. 로컬 안전 커밋까지만 했고 push·PR은 하지 않았다 — 이 문서는 다음 세션이 외부 독립 검증(V1→V2)을 거쳐 push·PR 승인을 받도록 고정한다.

아래를 새 세션에 그대로 붙여넣는다.

```text
$strict

저장소: /Users/kangsangmo/Desktop/Valuehire_v6
시작 위치: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/pii-sot-exception-redo-20260915

먼저 확인한다(자기선언을 믿지 말고 지금 상태를 다시 본다).
git merge-base --is-ancestor fc6beed HEAD   → 성공(0)이어야 한다.
git status --short                          → 비어 있어야 한다.
git log --oneline fc6beed..HEAD             → 2개(d6129ab, 6e7ba6c)여야 한다.

먼저 읽을 문서(순서대로):
1. docs/engineering/pii-sot-exception-redo-goal-2026-09-15.md — 이 작업의 원 계약(AC-1/2/3, counter-AC, 정직한 한계)
2. `git show 6e7ba6c` 전문(diff 포함) — 무엇이 어떻게 바뀌었는지 직접 읽는다
3. docs/sot/coding-principles.md P21 — 수정된 절

## WU-1 — 외부 독립 검증 (V1 → V2)

- V1: 별도 Claude CLI 세션(기존 로그인, ANTHROPIC_API_KEY unset)에 `fc6beed..HEAD` diff와 §8-7 출력 형식 블록만 넘긴다. 정조준:
  - AC-1(범위): `md_prose_pii_signal`을 무력화(예: 항상 `false` 반환)한 사본에서 `scripts/acceptance-hs-a4.sh`의 "승인 목록 밖 .md 의 라벨+사외연락처를 잡는다" 시나리오가 exit 1 대신 0으로 뒤집히는지 재현.
  - AC-2(신뢰경계): `approved_doc_decision_id`에서 `DECISION_REGISTRY`/SOT 본문 대조를 제거한 사본에서 "결정 ID 대신 자유 텍스트 자가 기입은 막는다" 시나리오가 뒤집히는지 재현.
  - AC-3(시점): `hooks/pre-commit`의 §9(개인정보 판정기 배선) 블록을 제거한 사본에서 정적 배선 검사와 실제 git commit 실행 검사가 둘 다 뒤집히는지 재현.
  - 오탐 재확인: `git ls-files '*.md' | xargs grep -lE '담당자|이름|연락처'`로 나온 파일들에 대해 실제로 `bash scripts/scan-data-exposure.sh pii`가 오탐 없이 통과하는지.
  - 새로 건드린 `scripts/verify/check-pre-push-runtime.sh`가 자기 본래 목적(probe 발견·실행 증명)을 여전히 검증하는지, 내가 추가한 스텁이 그 증명을 무력화하지 않는지.
- V2: 새 맥락 Codex에 V1 판정과 같은 범위를 넘겨 V1의 PASS/FAIL을 재공격한다.
- 판정은 파일로 받는다(채팅 응답 유실 반복 확인됨 — 워크트리 안 문서로 저장, 채팅에는 경로+한 줄 요약만).

## WU-2 — push·PR 승인

WU-1이 V1/V2 모두 PASS이면, 사람에게 다음을 승인받는다: `task/pii-sot-exception-redo-20260915`를 origin에 push, PR 생성(§8-8 형식). "사장님이 반드시 볼 부분"에 다음을 반드시 포함한다: (1) bd1c812 폐기·재작성 경위(절차 위반), (2) 3대 결함과 각각의 수정·반증, (3) DECISION_REGISTRY 한계(동일 작성자가 레지스트리+SOT를 같은 커밋에서 고치면 여전히 우회 가능 — 저장소 밖 통제 필요), (4) 이 브랜치엔 실제 weekly-brief 파일이 없어 PII_APPROVED_DOCS 항목이 실제로 REVIEWED되는 것은 그 파일이 병합되는 시점에 `.data-exposure-reviewed`에 실제 내용 해시가 추가돼야 확인된다는 것. 승인 전에는 push·PR을 실행하지 않는다.

비범위: force-push, 히스토리 재작성, `.md` 전반에 대한 PII 스캔 확장, weekly-brief 파일 자체의 병합.

중단 조건: `git merge-base --is-ancestor fc6beed HEAD`가 실패한다 / 작업트리가 깨끗하지 않다 / V1·V2 중 하나가 FAIL이다. 어느 하나면 멈추고 §8 형식으로 보고한다.
```
