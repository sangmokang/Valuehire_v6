VERDICT: FAIL

**전제 확인 (공유 트리, 읽기 전용)**
- `bash scripts/check-docs-sot.sh` → exit 0, 14개 PASS 라인 전부 출력.
- `git diff --check` → exit 0. checker 463줄(≤500). 작업 트리는 검증 전후 동일(30개 항목, HEAD `c59bad7`).

**격리 재현 (tracked 파일 + `docs/sot/features/` 사본, 실제 checker 실행)**
V1-J 교정분 5건은 전부 기대와 일치했습니다.

| 앵커 | 기대 | 실제 |
|---|---|---|
| `#14-구현not_run-장부` | PASS | PASS |
| `#14-구현notrun-장부` | FAIL | FAIL |
| `#1층--결론` | PASS | PASS |
| `#1층-결론` | FAIL | FAIL |
| 존재하지 않는 앵커 | FAIL | FAIL |

저장소 md 107개의 앵커를 github-slugger 규칙(L/N/M/Pc + `-`/공백 유지)을 독립 구현해 대조한 결과, 실사용 앵커 6건은 전부 실제 GitHub 슬러그와 일치했습니다.

**새 결함 — fence 토글이 백틱/틸드를 구분하지 않음** (`scripts/check-docs-sot.sh:123`)

`re.match(r"^\s*(```|~~~)", line)`이 종류·길이를 무시하고 무조건 상태를 뒤집습니다. 여는 fence와 다른 문자로 된 줄이 블록 안에 있으면 상태가 어긋나며, 양방향으로 오판합니다.

1. **가짜 앵커를 PASS시킴**: `~~~text` 블록 안의 ` ``` ` 줄이 블록을 조기 종료시켜 그 뒤의 `##` 줄을 제목으로 셉니다. 격리 반례에서 `#코드-블록-안-두번째-가짜-제목`이 PASS했고, 이는 실제 저장소에서도 발생합니다 — `docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:285`의 코드 블록 안 `## task/humansearch-l0-surface-classifier...` 줄이 앵커로 등록되어, GitHub에서 깨진 링크인 `#taskhumansearch-l0-surface-classifieroriginmain-ahead-5`가 근거 경로로 통과합니다.
2. **진짜 앵커를 FAIL시킴**: ` ```text ` 블록 안에 `~~~` 한 줄이 있으면 이후 상태가 계속 뒤집힌 채 남아 블록 밖의 실제 제목을 놓칩니다. 격리 반례 `#이후의-진짜-제목`이 FAIL했습니다.

즉 "fenced code의 `#` 줄을 제목으로 세지 않는다"는 성질이 성립하지 않습니다. 여는 fence 문자와 길이를 기억했다가 같은 종류·같은 길이 이상일 때만 닫는 방식이 필요합니다.
