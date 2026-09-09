# compat RED 독립 검토 보존

## Verdict

- **PASS, prior worktree state** — 이전 독립검토 시점의 `compat-draft.py`는 tests-only RED 커밋 근거로 승인 가능했다.
- **Current rerun is GREEN** — 이 보존 파일을 쓰는 동안 작업트리의 parser/product가 바뀌어 fresh 재실행은 통과했다. 따라서 현재 GREEN 출력은 RED 근거로 쓰지 않고, 이전 raw tool output을 별도 보존했다.

## Prior RED Fingerprints

- HEAD: `e2404d3732dfe6167907ebd5a1d76a7aa02ea26b`
- branch: `task/hs-0001-20260910`
- `compat-draft.py`: 55 lines, 1521 bytes, `sha256=0662357ecb0570bee47983b71afb968644ff22a5de7cd74a0ad550cf41a63070`
- `compat-draft-evidence.json`: 91 lines, 7506 bytes, `sha256=9403dda01c3b466b4c27fcee0e9839c7d8ada130ea2907bf959f5b97f32ac7ee`
- prior `scripts/verify/list-workflow-steps.py`: `sha256=a02cd98cc6afcc7a32ebeffc4ce942a5fa68c5bbd5d7ce389b99c56ae04a3263`
- current `scripts/verify/list-workflow-steps.py`: `sha256=5bf585f31b1ae2fa6915e82606bf8b0b2a1cd3a317d890bfcd6bdc6d541bd28f`

## Prior RED Commands Preserved

Full stdout/stderr is in `compat-red-review.json` (`sha256=3564facf945685df4c3a51fa30c43e92505eee0df127fd093b5654eb6894e133`). Key prior commands:

- `humansearch/.venv/bin/ruff check artifacts/hs-next-20260910/compat-draft.py` — 2026-09-09T20:43:15.108905Z..2026-09-09T20:43:15.158561Z, rc=0
- `humansearch/.venv/bin/mypy --strict --python-executable humansearch/.venv/bin/python artifacts/hs-next-20260910/compat-draft.py` — 2026-09-09T20:43:15.158936Z..2026-09-09T20:43:15.408079Z, rc=0
- `humansearch/.venv/bin/pytest --collect-only -q artifacts/hs-next-20260910/compat-draft.py` — 2026-09-09T20:43:15.408263Z..2026-09-09T20:43:15.821756Z, rc=0, 1 collected
- `humansearch/.venv/bin/pytest artifacts/hs-next-20260910/compat-draft.py -q --tb=short` — 2026-09-09T20:43:15.822044Z..2026-09-09T20:43:20.357226Z, rc=1
- `humansearch/.venv/bin/pytest humansearch/tests/test_hs_0001.py -q --tb=short` — 2026-09-09T20:43:20.357467Z..2026-09-09T20:43:25.482272Z, rc=0, 7 passed
- temp-copy collect as `humansearch/tests/test_hs_0001_main_compat.py` — 2026-09-09T20:43:27.123572Z..2026-09-09T20:43:27.453480Z, rc=0
- temp-copy run as `humansearch/tests/test_hs_0001_main_compat.py` — 2026-09-09T20:43:27.453697Z..2026-09-09T20:43:28.395139Z, rc=1

## Prior RED Failure Text

```text
FAIL: 워크플로를 정규 형식으로 읽지 못했다 — 형식 위반: 잡 수준 키 'timeout-minutes' (22행). runs-on 과 steps 만 쓴다 — 조건·기본 셸·전략으로 스텝 전체를 끌 수 있다
FAIL: CI 배선 불량 — 워크플로를 정규 형식으로 읽지 못했다
CHECKED: 12
FAIL(run-acceptance): scripts/acceptance-hs-kickoff.sh 종료값 1
```

## Current Fresh Rerun During Preservation

The same minimal commands were rerun while writing this file. At that time `scripts/verify/list-workflow-steps.py` had already changed to sha `5bf585f31b1ae2fa6915e82606bf8b0b2a1cd3a317d890bfcd6bdc6d541bd28f`, and both artifact placement and temp-copy placement passed. This confirms the RED was tied to the earlier parser state, while the compat draft bytes stayed unchanged.

## Gaps / Risks

- This file preserves the prior RED review. It is not a new product-fix verification verdict.
- The broader G2 mutation project-input issue remains separate.
- `compat-red-review.json` contains the full command outputs and should be the audit source for exact stdout/stderr.
