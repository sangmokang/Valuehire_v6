# HS-00.04 로컬 검증 원장

## 최종 판정

`PASS`. 검증 워크플로의 필수 trigger 삭제·축소와 YAML 파서 의미 차이를 기존 ci-step-integrity 판정기가 fail-closed 한다. 이 판정은 로컬 후보에만 귀속되며 원격 CI·push·PR·merge·운영 쓰기를 승인하지 않는다.

## 후보와 계보

- 선행 완료: `c28270c1ea6153d4ea0aae83a8562981b2564269`.
- 유효 branch/worktree: `task/hs-0004-recovery-20260910`, `worktrees/hs-0004-recovery-20260910`.
- 구현 직전 HEAD: `c7c6332bc6debab5b83090ae0230f1de74b7f724`.
- Claude V1·Codex V2가 함께 본 동작 후보 4파일 diff SHA-256: `74fe789fb261e3bde20262695be9fb1f784ad48aac6daf9334bcb6419738f8ea`.
- 판정 원문과 최종 장부를 문서에 반영한 뒤의 구현 커밋 직전 4파일 diff SHA-256: `5005de153d779e84271d0ac007a37cfd9d1a3fe62e8dfa6340501d3b3ea01b38`.
- 구현 커밋 직전 파일 SHA-256: goal `94cfeee01d01a23825f9706d9f1fb145252e37257e8fd774f2f28e49e6871750`, acceptance `a179b235ace39c21a5ab08f5092207383edb0fc32a929dc9d083fc82a39dc906`, checker `2f48e44fb67def7832505b80d037c4a7217b946aea10b0fcf9df860eb8bba2fd`, SOT `9ba301fd782df45d3a4af6f85b5a85de861f2e9650a0747b6f39a1ae45852877`.

최초 worktree의 Spec 검토자가 읽기 전용 범위를 위반해 RED/GREEN 커밋을 만들었다. 해당 `task/hs-0004-20260910` lane은 오염 증거로 보존하고 어떤 코드·판정도 채택하지 않았다. recovery lane을 선행 완료 SHA에서 새로 만들고 Spec 검토부터 다시 수행했다.

## 계약·RED 커밋

Spec/계약 계열:

- `2aa2e2416d22694164bd2b65a30ffe8be7329dad` — 최초 EARS/DB N/A/WU/counter-AC/예산.
- `2da0ada` — sequence shorthand와 duplicate event 계약.
- `eb3d95d` — recovery lane 소유 정정.
- `47ddf7f` — 최초 V1/V2 구조 반례 계약.
- `6e3b2d156a5094f3b7d04ea4b4ef4f1190e5b0f1` — YAML boolean 전집·nested duplicate·scalar·BOM.
- `c2a6d64266021f0edcb21075d2a76e5151c8edf9` — explicit bool tag·alias·semantic trigger 후보.

RED 계열:

- `8d98ff5a8e22d42a2ef9958eac69676e3ab9debc` — 최초 37개 RED.
- `38703159505188946a059545ec5877d580c00deb` — 52개 RED.
- `36b4427c5cc7a775cae4d0adac4d1af8b46de059` — 90개 RED.
- `4db4fcf59c0dca9b88813b16e804f96ba3cce4a8` — nested semantic key, 92개 RED.
- `5d44870f11c6addacdbf35b3fd22422cb22cbca7` — explicit bool tag·alias, 100개 RED.
- `cadc39b225683fb119e26d1cecfb10c21015c98a` — binary semantic `on`, 101개 RED.
- `c7c6332bc6debab5b83090ae0230f1de74b7f724` — explicit non-string tag·inline merge, 105개 RED.

각 Spec addendum은 구현 전에 독립 Spec 검토 PASS를 받았다. 각 RED addendum은 기존 기대값을 바꾸지 않고 새 반례만 추가했으며, 독립 시험 검토 PASS 후 테스트 전용 커밋으로 고정했다.

## 최종 명령과 결과

후보 최종 변경 후 아래 순서를 새로 실행했다.

```text
cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py tests/test_hs_0001.py tests/test_hs_0001_main_compat.py tests/test_hs_0002.py tests/test_hs_0002_boundaries.py
74 passed

bash scripts/acceptance-hs-gates.sh
ruff clean in 46 python files
mypy strict clean in 46 source files
pytest collected 285 and passed
runtime import proof PASS

bash -n scripts/verify/check-ci-step-integrity.sh scripts/acceptance-ci-step-integrity.sh
git diff --check c28270c1ea6153d4ea0aae83a8562981b2564269 --
bash scripts/acceptance-principles-check.sh
bash verify.sh
모두 exit 0; principles CHECKED 34; tracked secret pattern 없음

bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh
CHECKED 105, VERDICT PASS

bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh
CHECKED 16, VERDICT PASS

bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-mutations.sh
CHECKED 41, VERDICT PASS

bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh
CHECKED 37, exit 0
```

검사기 핵심 치환 mutant 14종은 전부 acceptance에서 죽었다. 대상은 boolean 집합, recursive `on`, semantic key type, explicit tag type, merge, BOM, scalar event, required event, push filter, PR filter, boolean collision, alias, `on` tag, semantic `on` 후보 개수다.

독립 적대 fixture 16종은 모두 기대 종료값과 marker가 일치했다. 위험 대조에는 explicit bool 앞/뒤, `!!bool on`, alias-hidden duplicate, `!!binary b24=`, nested `!!bool`/`!!int`/`!!null`, inline merge, reverse duplicate branches, multi-document, invalid UTF-8이 포함됐다. 정상 대조에는 quoted boolean-looking root key, `!!str` root/nested key, scalar semantic failure, unknown extra event, BOM+CRLF가 포함됐다.

## 독립 판정

- Spec reviewer: 모든 최초/addendum 계약 PASS.
- RED reviewer: 37→52→90→92→100→101→105 단계마다 PASS.
- Codeaudit: nested numeric/boolean semantic key가 exit 0인 결함을 FAIL로 발견. RED `4db4fcf...`와 semantic scalar scanner 보강 뒤 PASS. 최종 explicit tags/merge 보강 뒤에도 PASS.
- Claude V1: 최종 원문은 `claude-v1-final-verdict.md`. 후보 `74fe789f...`에서 `VERDICT: PASS`, canonical 105, 독립 반례 55, RED replay를 재현했다.
- Fresh Codex V2: 최종 원문은 `codex-v2-final-verdict.md`. 같은 동작 후보 4파일 지문과 diff 지문을 확인하고 `VERDICT: PASS`했다.
- 판정 원문 저장과 goal/SOT의 완료 서술은 동작 코드·RED 기대값을 바꾸지 않는 문서 마감이다. 별도 독립 documentation-only readback은 최초 558/560 diff 숫자 불일치를 FAIL로 잡았고, 검토 당시/마감본 수치를 분리해 고친 뒤 재계산 지문 `5005de...`, canonical 105, NOT_RUN·오염 lane 기록에 `VERDICT: PASS`했다.

## 코드 예산

```text
checker: 280 lines / soft300 / hard600
acceptance: 299 lines / soft300 / hard600
max Ruby def upper bound: 27 / soft60 / hard100
max shell function: 15 / soft60 / hard100
WU 4-file diff before evidence/readback: 560 insertions, 20 deletions; full implementation-commit candidate including evidence: 893 insertions, 20 deletions / hard3000
same budget validator: 600 PASS, 601 FAIL, zero targets FAIL
```

생성 파일·fixture 예외는 없다. 모든 공격 YAML과 mutant는 `mktemp` 아래에서만 만들고 제거했다.

## 실패 후 재시도 기록

- 새 worktree의 빈 `.venv` 때문에 최초 pytest가 시작하지 못했다. `uv sync --frozen` 후 같은 명령이 PASS했다.
- SOT 표의 기존 step 이름을 바꾼 초안은 HS-00.01 회귀가 잡았다. 이름을 복구하고 설명만 보강했다.
- Codeaudit가 goal 문서의 trailing whitespace를 FAIL로 잡았다. `<br>`로 고친 뒤 PASS했다.
- 최초 `omx ask claude`는 API key credit 부족으로 실패했다. 비밀을 출력하지 않고 `ANTHROPIC_API_KEY`를 제거한 로컬 Claude 로그인 경로로 재시도했다.
- Claude V1은 여러 차례 FAIL하며 parser-equivalence 반례를 추가했다. 각 결함은 새 RED와 독립 검토 뒤에만 고쳤고 마지막 실행은 PASS했다.
- 첫 checker mutant harness는 `|` 구분자 충돌로 무효였고 폐기했다. 명명된 치환표로 재실행했다.
- 첫 적대 harness는 zsh 예약 변수 `path`로 PATH를 덮어써 무효였고 폐기했다. `fixture` 변수와 절대 명령 경로로 재실행했다.
- 후속 표 기반 적대 harness는 literal `\n`을 실제 개행으로 바꾸지 않아 무효였고 폐기했다. 실제 개행 fixture로 재실행해 16/16 PASS했다.
- 적대 harness의 Open3 상태를 `$?`에서 잘못 읽은 초안도 판정에서 폐기하고 반환된 status를 사용해 재실행했다.

## NOT_RUN과 잔여 위험

- 원격 push·draft PR·PR·merge·원격 CI·운영 쓰기: `NOT_RUN` — 사용자 승인이 없다.
- GitHub Actions 활성화, branch protection, required checks, fork approval, commit-message skip: `NOT_RUN`/WU 제외.
- 전체 GitHub Actions top-level/event schema와 HS-00.05 환경 오염: WU 제외.
- inherited RED `6/31`은 이 WU에서 고치지 않았다. `acceptance-0-7.sh`는 CI 담당 제외 상태다.
- `LC_ALL=C` Ruby inline 한글 literal 실패는 선행 검사기에도 존재하고 fail-closed 방향이다. 별도 후속 WU 위험이다.
- 기존 `ALLOWED_STEP_IF` 이름 재사용과 quoted `echo` 계열 스텝 본문 위장은 trigger WU 밖의 선행 위험이다.
- Ruby 3.4 배포판의 bundled `base64` 가용성과 원격 runner locale은 원격 CI를 실행하지 않아 확인하지 않았다.

## 커밋 후 readback

구현 커밋 `95bb942b0ecda4b4b03e3e49dcc93d91b30bac48` 후 SHA·Git blob·working file SHA 9개가 모두 일치했다. committed-tree에서 canonical 105, 실제 workflow 32, 원칙 34가 종료값 0으로 다시 PASS했고 readback 직전 worktree는 clean이었다. 전체 원문은 `implementation-readback.md`에 보존한다.
