VERDICT: PASS

## 결론

현재 최종 후보는 요청하신 여덟 항목을 모두 직접 재실행한 결과 합격입니다. 전각·동형 문자로 보호 이름을 위장한 입력 세 가지(끝에 전각 숫자 1을 붙인 PR 13, 앞에 전각 x를 붙인 PR 13, 앞에 전각 x를 붙인 hs-kickoff 스텝 이름)와 보호 토큰 양옆의 치환 경계 우회는 helper와 실제 acceptance 경로 양쪽에서 모두 거부됐고, 정상 한글·일본어·아랍어·라틴 이름과 PR 131, 전각 P로 시작하는 PR 131, hs-kickoff-other, 전각 s가 섞인 hs-kickoff-other는 모두 허용됐습니다. 빈 입력·빈 줄·공백뿐인 줄·깨진 UTF-8은 모두 종료값 2로 닫혔습니다. 요청하신 고장 사본 세 종류(shell이 helper 결과 무시, 경계 치환 검사 제거, 첫 정상 토큰에서 탐색 중단)는 모두 시험에 잡혔습니다. 검증 전후 작업트리와 bundle 지문은 바뀌지 않았습니다.

합격을 뒤집을 결함은 찾지 못했습니다. 다만 낮은 심각도 두 건을 남깁니다. 하나는 helper가 데이터 오류(종료값 2)를 냈을 때 처분표 경로와 스텝 경로가 서로를 가려서, 한쪽 경로의 오류 처리만 약화한 고장 사본이 시험에 살아남는다는 점입니다. 두 경로를 함께 약화하면 잡히므로 현재 제품에 거짓 합격 경로는 없습니다. 다른 하나는 매핑 개수 재검사가 SHA 고정 뒤에 있는 죽은 방어선이라 그 제거 사본이 살아남는다는 점입니다.

## 판단 근거

**먼저 밝힐 건너뜀·미확인·재시도·추정입니다.**

- `NOT_RUN`: 제공 증거의 "소유 파일 hard600/hard100 통과, 경계 600 통과·601 실패·대상 0개 실패"는 해당 도구를 저장소 스크립트에서 찾지 못해 재실행하지 못했습니다. 제가 직접 읽은 줄 수만 아래에 남깁니다.
- `NOT_RUN`: 원격 CI, push, PR, 병합 상태, 사용자 보관 세션의 반복 질문 조사, LSP 실진단은 하지 않았습니다.
- 재시도 1: 첫 pytest 실행에서 zsh의 `PIPESTATUS` 표기 차이로 종료값이 비어 나와 파일 리다이렉트로 다시 실행했습니다. 두 번 모두 23 passed였습니다.
- 재시도 2: 첫 `/tmp` 복사본 구성이 zsh 단어 분리와 미추적 `docs/licenses` 경로 때문에 실패해 bash 스크립트로 다시 구성했습니다. 실패한 첫 시도의 결과(19 failed)는 복사본이 비어 있어서 나온 값이며 판정에 쓰지 않았습니다.
- 추정 없음: 아래 숫자는 모두 이 세션의 직접 실행값입니다. 제공된 결과와 일치했지만 제공 결과를 근거로 쓰지 않았습니다.

**선택한 해석.** "정상 대조군 허용"은 helper 종료값 0뿐 아니라 실제 acceptance가 `CHECKED: 12`와 exit 0을 내는 것으로 보았습니다. "경계 우회 거부"는 helper의 `SPOOF:` 출력만이 아니라 shell의 `FAIL:` 행과 종료값 1까지 이어지는 것으로 보았습니다. "시험에 잡힌다"는 고장 사본에서 pytest 종료값이 0이 아니고 실패 시험이 그 결함과 대응하는 것으로 보았습니다.

**버린 해석.** 계약이 명시적으로 제외한 U+3000·NBSP·ZWSP·결합 문자 위장이 통과하는 것을 결함으로 세지 않았습니다. 이 네 가지가 실제로 통과함은 재현해 두었으므로, 그 위장은 여전히 막히지 않는다는 사실만 기록합니다. 또한 SHA 고정 뒤의 헤더·개수 재검사가 죽은 방어선인 것도 결함이 아니라 설계 여유로 보았습니다.

**틀리면 깨지는 것.** 만약 처분표 경로와 스텝 경로가 서로 다른 helper나 다른 데이터를 쓰도록 나중에 갈라지면, 지금 살아남은 종료값 2 고장 사본 두 개가 실제 거짓 합격 경로가 됩니다. 그때는 아래 낮음 1번의 시험 보강이 필요합니다.

**결함 목록(심각도순)**

1. 낮음 · "종료값 2를 한 경로만 무시해도 시험이 살아남는다" · 원인: `scripts/acceptance-hs-kickoff.sh:122`(처분 대상 helper 오류 분기)와 `scripts/acceptance-hs-kickoff.sh:181`(스텝 helper 오류 분기)이 같은 helper·같은 데이터 파일을 쓰므로 한쪽 분기를 `-gt 2`나 `-eq 1`로 약화해도 다른 쪽이 데이터 오류 시험 4개를 여전히 실패시킴 · 사업 영향: 현재 제품에서는 거짓 합격 경로가 없으며, 향후 한쪽 경로만 손댈 때 조용히 약화될 수 있는 시험 공백입니다.
2. 낮음 · "매핑 개수 재검사 제거 사본이 살아남는다" · 원인: `scripts/verify/check-hs-kickoff-identities.py:111`(구축된 매핑 수 대조)은 `:67`(파일 SHA 대조)이 먼저 모든 내용 변경을 잡기 때문에 도달할 수 없는 방어선임 · 사업 영향: 없음. 방어선 중복일 뿐입니다.
3. 정보 · "시험 이름이 단언과 반대로 읽힌다" · `humansearch/tests/test_hs_0003.py:189`(경계 치환 우회 거부 시험)의 이름은 "대상으로 세지 않는다"로 읽히지만 실제 단언은 거부(`SPOOF`)입니다 · 사업 영향: 없음. 읽는 사람의 오해 가능성만 있습니다.

**설계 지적(낮음 1번)**
- 무엇을 — 데이터 오류 시험 네 개가 처분표 경로와 스텝 경로 각각의 `FAIL:` 문구까지 단언하지 않습니다.
- 왜 — 두 경로가 동일 helper를 공유해 한쪽만 약화해도 전체 종료값이 0이 아니기 때문입니다.
- 버린 길 — 이번 검증에서 시험을 고쳐 넣는 것은 읽기 전용 지시라 하지 않았습니다.
- 대가 — 향후 리팩터링에서 한 경로의 오류 처리가 조용히 사라져도 현재 시험은 초록입니다.
- 되돌리기 — `test_mapping_data_errors_fail_closed`에 "처분 대상 Unicode 검사 오류"와 "CI·정본 스텝 이름 Unicode 위장 또는 검사 오류" 두 문구를 함께 단언하면 두 사본 모두 잡힙니다.

## 기술 상세와 증거 원문

**1. 후보 동일성**

```text
HEAD e99b4549ddf617d0d79acdd63880438cfbf9a7c8  branch task/hs-0003-20260910
git status --short: M goal doc, M verification-commands.md, M acceptance-hs-kickoff.sh,
  M acceptance-hs-kickoff-mutations.sh, ?? evidence/, ?? docs/licenses/, ?? 3 scripts/verify files
manifest sha256 c466946aad003159a07c052979e8e0034ec4eeb0d3445d5a9ccb7952a6b7e6d4
9 files ALL OK (per-file sha256 + bytes)
bundle   9517376e3755a69e4e9dfca8ac5ad859654cbb94dda8cd3b610075c61b40e23d  MATCH
```

→ 요청서의 manifest·bundle 기대값과 제 재계산이 모두 일치했습니다. 같은 후보를 본 것입니다.

**2. 정상 검증 재실행**

```text
uv run --no-sync pytest -q tests/test_hs_0003.py                 23 passed  exit 0
정조준 5파일 (0003·0001·0001_main_compat·0002·0002_boundaries)     74 passed  exit 0
bash scripts/acceptance-hs-gates.sh                                exit 0
  PASS: ruff clean in 46 python files / mypy strict clean in 46 source files
  PASS: pytest collected 285 and passed / COLLECTED: 285
bash scripts/acceptance-hs-kickoff-mutations.sh                    exit 0, PASS 37, FAIL 0, CHECKED: 37
bash scripts/acceptance-principles-check.sh                        exit 0, CHECKED: 34, VERDICT: PASS
bash scripts/acceptance-principles-mutations.sh                    exit 0, CHECKED: 41, VERDICT: PASS
bash verify.sh                                                     exit 0
  PASS: no secret-pattern match in any tracked file, .env not tracked
```

→ 제공된 수치와 모두 같은 값이 제 환경에서 새로 나왔습니다. 좋은 증거입니다.

**3. helper 직접 공격(41건, 예상 밖 0건)**

```text
OK rc=1 | PR #13１            → SPOOF: disposition-target line=1 token=PR #13
OK rc=1 | ｘPR #13            → SPOOF: disposition-target line=1 token=PR #13
OK rc=1 | 인수 검사 ｘhs-kickoff (…) → SPOOF: workflow-step line=1 token=hs-kickoff
OK rc=0 | PR #131 / ＰR #131 / hs-kickoff-other / hｓ-kickoff-other
OK rc=0 | 정상 한글 山田太郎 · محمد · Überprüfung · hs-kickoff 설명
OK rc=0 | ＡＢＣ　전각　문장입니다！　ＸＹＺ－１２３   (보호 토큰 밖 무관 전각)
OK rc=1 | hs-kickoff 정상 · hѕ-kickoff 위장   (같은 줄 정상 뒤 위장)
OK rc=1 | PR #13 정상 · PＲ #13 위장
OK rc=1 | hs-kісkoff / hs－kickoff / hs‐kickoff(U+2010) / PR ＃13 / task／hs-d1-permit / ｈｓ－ｋｉｃｋｏｆｆ
OK rc=0 | ＃PR #13 (＃→# 는 경계 문자가 아니므로 raw·shadow 판정이 같음) / 가PR #13
OK rc=2 | b"" / b"\n" / b"   \n" / b"\t" / b"\n\n\n"  → ERROR: 입력 이름 줄 없음
OK rc=2 | hs-kickoff\xff / UTF-16 BOM / latin1 0xE9 / overlong C0 80 → ERROR: 입력 UTF-8 해독 실패
OK rc=2 | --token "PR #99" / "" / "pr #13" → ERROR: 지원하지 않는 보호 토큰
OK rc=0 | 계약 제외: PR　#13(U+3000) / PR\u00a0#13 / hs-\u200bkickoff / hs-kickoff+결합문자 / 유효 줄 사이의 공백 줄
```

→ 요청한 우회 3종과 정상 4종, 다국어, 무관 전각, 같은 줄 동시 존재, 입력 오류 4종이 모두 계약대로 동작했습니다. 마지막 줄의 계약 제외 항목은 실제로 통과하므로 그 위장은 여전히 막지 못한다는 점을 기록합니다.

**4. 실제 acceptance fixture 재현(임시 복사본, 원본 미변경)**

```text
normal: hs-kickoff-other ASCII step          rc=0  CHECKED: 12  OK(run-acceptance)
normal: hｓ-kickoff-other step                rc=0  CHECKED: 12  OK(run-acceptance)
normal: ＰR #131 disposition extra row       rc=0  CHECKED: 12  OK(run-acceptance)
normal: 다국어 + 무관 전각 step              rc=0  CHECKED: 12  OK(run-acceptance)
normal: PR #131 replaces PR #13              rc=1  FAIL: 처분표에 PR #13 행 없음  (SPOOF 없음 — 기존 기대값)
bypass: PR #13１                             rc=1  SPOOF: disposition-target line=1 token=PR #13 / FAIL: PR #13 처분 대상에 보호 이름 위장 있음
bypass: ｘPR #13                             rc=1  SPOOF: disposition-target line=1 token=PR #13 / FAIL: …위장 있음
bypass: ｘhs-kickoff (                       rc=1  SPOOF: workflow-step line=29, sot-step line=29 / FAIL: CI·정본 스텝 이름 Unicode 위장 또는 검사 오류
same line 정상 뒤 위장                       rc=1  SPOOF disposition line=7, workflow line=31, sot line=31
helper 파일 삭제 / 데이터 파일 삭제           rc=1  처분 6건 "Unicode 검사 오류" + 스텝 FAIL, CHECKED: 12
```

→ 위장 거부가 helper 출력에서 끝나지 않고 shell의 `FAIL:` 행과 종료값 1로 이어집니다. helper나 데이터가 없으면 열린 실패가 아니라 닫힌 실패입니다. 좋은 증거입니다.

**5. RED 보존과 고장 사본(모두 `/tmp` 복사본, venv python 직접 실행)**

```text
head-only(RED, GREEN 없이 HEAD만)         rc=1  22 failed, 1 passed
baseline(후보 복사본)                      rc=0  23 passed ; test_hs_0001 7 passed
--- 요청한 세 종류 ---
ignore-workflow-shell-result              rc=1  6 failed
ignore-sot-shell-result                   rc=1  6 failed
ignore-disposition-shell-result           rc=1  9 failed
drop-confusable-boundary                  rc=1  3 failed
only-first-occurrence                     rc=1  1 failed
--- 추가 ---
shell-only-first-disposition-name         rc=1  7 failed
shell-skips-sot-helper                    rc=1  6 failed
drop-token-boundary                       rc=1  1 failed
allow-whitespace-name                     rc=1  1 failed
bypass-data-sha                           rc=1  1 failed
helper-always-exit0                       rc=1  14 failed
drop-fullwidth-fold                       rc=1  9 failed
replace-invalid-utf8                      rc=1  1 failed
confusable-boundary-before-only           rc=1  1 failed
confusable-boundary-after-only            rc=1  2 failed
--- 살아남음 ---
shell-treats-rc2-as-pass (처분 경로만)     rc=0  23 passed
shell-step-rc2-as-pass (스텝 경로만)       rc=0  23 passed
drop-mapping-count-check                  rc=0  23 passed
combined-rc2-as-pass (두 경로 동시)        rc=1  4 failed (mapping_data_errors 4종 전부)
```

→ HEAD만으로는 22개가 실패하므로 세 RED 커밋은 GREEN 없이 요구 동작을 실패시킵니다. 요청하신 세 종류를 포함한 15종은 잡혔습니다. 살아남은 셋 중 두 개는 두 경로를 함께 약화하면 잡히므로 현재 거짓 합격 경로가 없고, 나머지 하나는 SHA 고정 뒤의 죽은 방어선입니다. 낮음 1·2번의 근거입니다.

**6. Unicode 17.0.0 원본·생성물·라이선스 대조(네트워크 읽기만)**

```text
curl confusables.txt  sha256 091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a  (# Version: 17.0.0, # Date: 2025-07-22, 05:49:37 GMT)
generate-hs-kickoff-confusables.py → regen.json sha256 687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd  cmp: REGEN_IDENTICAL
JSON selection: mapping_count 628, groups 26, 실제 항목 합 628, protected_ascii "#-/1345PRabcdefhiklmnoprstuvx"
unicode.org/license.txt sha256 e7a93b0095…bc53d96 == docs/licenses/unicode-license-v3.txt  LICENSE_IDENTICAL
```

→ 원본 SHA, 생성물 SHA, 선택 수 628, 라이선스 원문이 모두 요청값과 일치하고 재생성이 바이트 단위로 같습니다.

**7. 기존 기대값·의존성·CI 단계**

```text
git diff HEAD --numstat mutations.sh: +2 -0 (sandbox FILES에 helper·데이터 두 파일 추가뿐)
EXPECTED=12 (acceptance-hs-kickoff.sh:30) / "CHECKED 37" 머리말 유지
첫 RED(396cd2b)의 test_hs_0001 변경: OPTIONAL_RUNTIME_FILES 복사 10줄뿐, MUTATIONS 6종 기대 문구 불변
39cc8df..HEAD 에서 verify.yml·pyproject.toml·uv.lock 변경 커밋 없음; 작업트리에서도 미변경
helper·생성기 import: argparse hashlib json re sys dataclasses pathlib typing (표준 라이브러리만)
직접 센 줄 수: helper 222, acceptance shell 267, 생성기 125, test_hs_0003 305, mutations 593+2=595
```

→ 37종 기대값은 바뀌지 않았고 새 의존성·새 CI 단계는 없습니다. 줄 수는 hard600 도구를 대신하지 못하는 제 직접 계수이며 모두 600 미만입니다.

**8. 검증 전후 불변성과 정리**

```text
HEAD before/after  e99b4549ddf617d0d79acdd63880438cfbf9a7c8 (동일)
git status --short sha256 before/after 236ba9393d2a…8e6945 (동일)
bundle after 9517376e…e23d MATCH / manifest after c466946a…e6d4
git worktree list: hs-0003-20260910 항목 동일. 변이 37종 실행 중 다른 워크트리 hs-13-stack-20260910의 HEAD가 7e873e9→2211c1c로 바뀐 것을 관찰 — 이 세션의 행위가 아닌 외부 활동
임시 사본: /tmp/hs0003-review 삭제, fixture 임시 디렉터리 11개 삭제(잔여 0). /tmp의 이전 세션 hs0003-* 파일 17개는 제가 만든 것이 아니라 두었음
```

→ 검증이 제품 파일이나 작업트리를 바꾸지 않았고, 제가 만든 임시물은 모두 정리했습니다.

**9. 증거 보존 경로**

```text
임시 harness·로그(삭제됨): /tmp/hs0003-review/attack_helper.py, build_and_mutate.sh, combined_and_fixture.sh,
  pytest-target.log, pytest-focus.log, mutations.log, g2.log, principles.log, principles-mut.log, verify-sh.log, mutants.log, fixture.log
추적 보존 경로(구현 세션이 이 판정 원문을 저장할 위치):
  docs/engineering/evidence/hs0003-20260910/claude-v1-final-v2-response.md
세션 지문 메타 경로(구현 세션이 세션 지문을 저장할 위치):
  docs/engineering/evidence/hs0003-20260910/claude-v1-final-v2-meta.json
판정 대상 지문: HEAD e99b4549ddf617d0d79acdd63880438cfbf9a7c8, manifest c466946a…e6d4, bundle 9517376e…e23d
```

→ 임시 경로의 파일은 세션 종료로 사라지므로 근거가 되지 않습니다. 이 판정의 원문과 세션 지문은 위 두 추적 경로에 보존될 때 HEAD·manifest·bundle 지문과 함께 재검토 가능한 근거가 됩니다. 이 두 파일은 이 세션이 작성하지 않았으며, 작성은 구현 세션의 몫입니다.