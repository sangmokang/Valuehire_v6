VERDICT: FAIL

**결론** — 지시된 3개 시나리오는 모두 기대대로 재현되었으나, 같은 fence 처리 로직에 **새 결함**이 남아 있어 FAIL입니다.

**확인한 정상 상태**
- 공유 트리 `bash scripts/check-docs-sot.sh` → 전 항목 PASS, `OK: docs/sot 재구성 AC 전부 충족` (exit 0).
- `wc -l scripts/check-docs-sot.sh` = **475줄** (500줄 경계 이내), `git diff --check` 출력 없음(exit 0).
- 격리 사본(`/tmp/v1l.Xana6E`, `.git` 복사 + 변경/미추적 파일 반영)에서 evidence 항목을 주입해 검사:
 1. `humansearch-l0-auth-surface-goal-2026-08-18.md#taskhumansearch-l0-surface-classifieroriginmain-ahead-5`(257행 `~~~text` 내부 가짜 앵커) → **FAIL** ✔
 2. `#claude-v1--증거-결함-보완-명령과-프롬프트`(401행 `~~~` 종료 후 406행 실제 제목) → **PASS** ✔
 3. V1-J 4종 유지: `#14-구현not_run-장부` PASS / `#14-구현notrun-장부` FAIL / `#1층--결론` PASS / `#1층-결론` FAIL, 존재하지 않는 앵커 FAIL ✔

**새 결함 1 (앵커 위조 가능, 중대)** — `scripts/check-docs-sot.sh:131`의 닫는 fence 정규식이 ``[`~]{3,}``로 **혼합 문자**를 허용하고 첫 글자만 비교합니다. 따라서 CommonMark/GFM상 닫는 fence가 아닌 `````~`` 같은 줄이 백틱 블록을 조기 종료시킵니다. 최소 재현: 본문이 `````text / ```~ / ## forged anchor / ``` ``인 문서의 `#forged-anchor`를 evidence로 넣으면 검사기가 **PASS**(위조 앵커 인정). 이는 V1-K가 고치라고 지시받은 결함과 동일 계열입니다. 현재 추적 중인 `*.md`에는 혼합 fence 줄이 없어 잠복 상태입니다.

**새 결함 2 (오탐, 경미)** — 여는 fence 정규식이 백틱 fence의 info string 내 백틱을 금지하지 않아 `````py``` `` 같은 문단 줄을 블록 시작으로 오인하고, 이후 실제 제목 앵커를 FAIL 처리합니다(재현 확인).

**잔여 위험** — 오프라인에 cmark/pandoc이 없어 판정 근거는 GFM 사양과 검사기 동작 비교입니다. setext 제목·리스트 내부 들여쓴 fence도 여전히 미지원입니다. 공유 트리는 수정하지 않았습니다.
