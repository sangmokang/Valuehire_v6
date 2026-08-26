VERDICT: PASS

**공유 트리 상태(읽기 전용 확인)**
- `bash scripts/check-docs-sot.sh` → exit 0, 조용한 통과 없이 14개 PASS 라인 출력 (`features=6 categories=3 invariants=33 ... paths=validated`).
- `wc -l scripts/check-docs-sot.sh` → 475줄 (500줄 이내).
- `git diff --check` → exit 0, 공백 오류 없음. 검증 중 공유 트리는 변경하지 않았습니다(상태 34줄 그대로).

**격리 fixture 종단 검증**
추적/미추적 파일만 `/tmp`로 복제해 독립 저장소를 만들고(기준선 exit 0), fixture 문서 `docs/sot/anchor-fixture.md`의 앵커를 실제 기능 문서 `evidence`에 1건씩 주입해 **checker 자체를 11회 실행**했습니다. 파서 재구현 없이 실제 종단 경로(`require_existing` → `markdown_anchors`)로 판정했습니다.

| 사례 | 기대 | 실제 |
|---|---|---|
| backtick 블록 안 ` ```~ ` 뒤 가짜 제목 | FAIL | FAIL |
| 정상 backtick 닫힘 뒤 실제 제목 | PASS | PASS |
| `` ```py``` `` info 문단 뒤 실제 제목 | PASS | PASS |
| tilde 블록 안 ` ``` ` 뒤 가짜 제목 | FAIL | FAIL |
| 정상 tilde 닫힘 뒤 실제 제목 | PASS | PASS |
| underscore 보존 (`under_score-제목`) | PASS | PASS |
| 연속 하이픈 보존 (`연속----하이픈-제목`) | PASS | PASS |
| 하이픈 축약형 (`연속--하이픈-제목`) | FAIL | FAIL |
| 없는 앵커 | FAIL | FAIL |
| 중복 제목 2번째 (`중복-제목-1`) | PASS | PASS |
| 문서 루트 제목 | PASS | PASS |

11/11 일치. FAIL 사례는 모두 `Markdown anchor does not exist` 사유로 정확히 실패했습니다.

**현재 사용 앵커 점검**
기능 SOT가 참조하는 앵커는 7건(browser-contract 1, l0-surface-contract 4, git-workflow 1 + 중복)이며 대상 문서의 제목은 전부 ATX입니다. `#10-자격증명과-명령-능력-경계`처럼 숫자·마침표·조사 결합 슬러그도 GitHub 규칙(소문자화 → 공백 하이픈화 → `[\w-]` 외 제거)과 일치합니다.

**잔여 위험(신규 기능으로 확대하지 않음)**
- Setext 제목, 1~3칸 들여쓴 ATX, 인용/리스트 컨테이너 안 제목, 여러 줄 HTML 주석 안 `#` 시작 줄 — 앞 세 가지는 앵커를 놓치는 보수적 방향(오탐 FAIL), 마지막만 오탐 PASS 방향입니다.
- 위 네 문법 모두 `docs/sot/` 전체에서 사용 사례 0건임을 grep으로 확인했습니다. 4칸 들여쓴 코드 블록 안 `## x`는 열 위치 조건 때문에 오탐이 발생하지 않습니다.

지정 반례와 현재 사용 앵커 모두에서 결함이 없어 PASS로 판정합니다.
