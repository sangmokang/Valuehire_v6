PASS.

실행 결과:

- `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py` -> `5 failed, 16 passed`
- `cd humansearch && uv run --no-sync ruff check tests/test_hs_0003.py` -> `All checks passed!`
- 정상 대조군 직접 확인: `test_normal_multilingual_and_unrelated_fullwidth_step_name_passes` -> `1 passed`

실패 5개는 모두 새 RED 행동 실패입니다.

- `humansearch/tests/test_hs_0003.py:188` `PR #13１`: acceptance가 `returncode=0`으로 통과. 실제 `scripts/acceptance-hs-kickoff.sh` 처분표 경로에서 `PR #13`이 confusable suffix와 붙어도 정상 대상처럼 카운트되는 행동 결함입니다.
- `humansearch/tests/test_hs_0003.py:188` `ｘPR #13`: acceptance가 `returncode=0`으로 통과. confusable prefix가 붙은 대상도 정상 `PR #13`처럼 인정되는 행동 결함입니다.
- `humansearch/tests/test_hs_0003.py:201` workflow+SOT `ｘhs-kickoff (`: acceptance가 `returncode=0`으로 통과. 실제 workflow/SOT 이름 대조 경로에서 보호 토큰 앞 confusable boundary를 놓칩니다.
- `humansearch/tests/test_hs_0003.py:267` helper `b"\n"`: helper가 rc0. 빈 이름 한 줄을 오류로 거부해야 한다는 V2 재현 결함을 고정합니다.
- `humansearch/tests/test_hs_0003.py:267` helper `b"hs-kickoff\xff\n"`: helper가 rc0. invalid UTF-8 bytes를 오류로 거부해야 한다는 V2 재현 결함을 고정합니다.

`git diff -- humansearch/tests/test_hs_0003.py` 확인 결과, 기존 동결 기대를 바꾸지 않고 import/Protocol 추가, 새 helper 2개, 새 RED 케이스만 추가했습니다. 기존 정상 대조군인 `ＰR #131`, `hｓ-kickoff-other`, 한글/일본어/아랍어/독일어 혼합 문자열은 별도 타깃 실행에서 통과해 훼손되지 않았습니다.

시험 약점은 하나 있습니다. helper 입력 테스트는 `b""`까지 같은 테스트에 포함하지만, 현재 구현이 이미 `입력 줄 없음`으로 rc2를 반환해서 RED 실패에는 포함되지 않습니다. 과잉 계약은 아닙니다. "입력 없음"도 helper의 fail-closed 계약으로 자연스럽고, 실제 실패 개수는 요청한 5개 행동 실패와 정확히 일치합니다.
