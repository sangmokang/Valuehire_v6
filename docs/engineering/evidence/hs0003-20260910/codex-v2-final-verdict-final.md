VERDICT: PASS

## 결론

현재 후보는 HS-00.03 계약 검증에서 PASS다. 직접 실행한 핵심 시험과 적대 공격에서 결함을 찾지 못했다.

# HS-00.03 Codex V2 final adversarial verification

결론: 현재 HEAD `e99b4549ddf617d0d79acdd63880438cfbf9a7c8` 위 working tree GREEN 후보는 HS-00.03 계약을 충족한다. Claude V1의 PASS 주장은 판정 근거로 쓰지 않았고, 제품 파일 지문, shell 배선, pytest, acceptance, G2, Unicode 재생성, 대표 고장 사본 공격을 직접 실행해 반박을 시도했다. 직접 확인한 결함은 없다.

→ PASS 영향: 병합/원격/운영 승인은 아니다. 이 판정은 로컬 작업트리 후보가 계약상 핵심 검증을 통과했다는 뜻이다.

## 판단 근거

| 항목 | 성공 기준 | 직접 증거 | 판정 |
|---|---:|---|---|
| HEAD | 요청 HEAD와 일치 | `git rev-parse HEAD` → `e99b4549ddf617d0d79acdd63880438cfbf9a7c8` | PASS |
| manifest 파일 | SHA `c466946a...e6d4` | `sha256(candidate-product-manifest.json)` → `c466946aad003159a07c052979e8e0034ec4eeb0d3445d5a9ccb7952a6b7e6d4` | PASS |
| 제품 bundle | listed order path UTF-8 + NUL + raw bytes + NUL | 재계산 bundle → `9517376e3755a69e4e9dfca8ac5ad859654cbb94dda8cd3b610075c61b40e23d` | PASS |
| 사후 불변성 | 검증 뒤 manifest 파일/bytes/bundle 불변 | `post_manifest_all_files_match True`, `post_bundle_sha256 951737... match True` | PASS |
| target | HS-00.03 단독 23건 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py` → `23 passed in 15.56s` | PASS |
| 정조준 | HS-00.01/02/03 묶음 74건 | `uv run --no-sync pytest -q tests/test_hs_0003.py tests/test_hs_0001.py tests/test_hs_0001_main_compat.py tests/test_hs_0002.py tests/test_hs_0002_boundaries.py` → `74 passed in 26.93s` | PASS |
| shell acceptance | 실제 hs-kickoff 배선 12건 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh` → `CHECKED: 12`, `OK(...)` | PASS |
| 기존 변이 | 양성 6 + 음성 31 = 37 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh` → `CHECKED: 37`, `OK(...)` | PASS |
| G2 | ruff/mypy/pytest/runtime import | `bash scripts/acceptance-hs-gates.sh` → `COLLECTED: 285`, `pytest collected 285 and passed` | PASS |
| G2 변이 | gates mutation 차단 | `bash scripts/acceptance-hs-gates-mutations.sh` → `PASS: gates mutations blocked 6/6` | PASS |
| G2 antiforge | evidence forgery/CI disable 차단 | `bash scripts/acceptance-hs-gates-antiforge.sh` → `PASS: gates antiforge 3/3` | PASS |
| 비밀 스캔 | 추적 파일 비밀 패턴 없음 | `bash verify.sh` → `PASS: no secret-pattern match in any tracked file, .env not tracked` | PASS |

→ 핵심 명령은 모두 종료값 0으로 끝났다. 원격 push/PR/merge/운영/메시지/포털 작업은 실행하지 않았다.

## shell 입력 경계

| 입력 | 기대 | 직접 결과 |
|---|---:|---|
| `PR #13１` | rc 1 | `SPOOF: disposition-target line=1 token=PR #13` |
| `ｘPR #13` | rc 1 | `SPOOF: disposition-target line=1 token=PR #13` |
| `ｘhs-kickoff (` | rc 1 | `SPOOF: workflow-step line=1 token=hs-kickoff` |
| `PR #131` | rc 0 | 출력 없음 |
| `ＰR #131` | rc 0 | 출력 없음 |
| `hs-kickoff-other` | rc 0 | 출력 없음 |
| `hｓ-kickoff-other` | rc 0 | 출력 없음 |
| `정상 한글 山田太郎 محمد Überprüfung ＡＢＣ 설명` | rc 0 | 출력 없음 |
| 정상 토큰 뒤 위장 `hs-kickoff and hѕ-kickoff` | rc 1 | `SPOOF: workflow-step line=1 token=hs-kickoff` |
| 정상+위장 동시 `PR #13 and PＲ #13` | rc 1 | `SPOOF: disposition-target line=1 token=PR #13` |
| 0바이트 | rc 2 | `ERROR: 입력 이름 줄 없음` |
| 빈 줄 | rc 2 | `ERROR: 입력 이름 줄 없음` |
| 공백-only | rc 2 | `ERROR: 입력 이름 줄 없음` |
| invalid UTF-8 | rc 2 | `ERROR: 입력 UTF-8 해독 실패...` |

→ helper 단위 경계는 요청한 거부/허용/오류 케이스를 그대로 만족했다.

## 실제 shell 배선 재현

임시 git worktree에 현재 후보 파일을 덮어쓴 뒤, 제품 파일을 건드리지 않고 각 입력 칸만 변조했다.

| 변조 | 직접 결과 |
|---|---|
| workflow step name + SOT step-name cell을 `ｘhs-kickoff`로 동시 변조 | rc 1, `SPOOF: workflow-step line=29 token=hs-kickoff`, `SPOOF: sot-step line=29 token=hs-kickoff`, `FAIL: CI·정본 스텝 이름 Unicode 위장 또는 검사 오류`, `CHECKED: 12` |
| disposition target cell을 `PR #13１`로 변조 | rc 1, `SPOOF: disposition-target line=1 token=PR #13`, `FAIL: PR #13 처분 대상에 보호 이름 위장 있음`, `CHECKED: 12` |
| 세 칸 동시 변조 | rc 1, disposition/workflow/SOT `SPOOF` 모두 출력, `CHECKED: 12` |

→ 실제 `acceptance-hs-kickoff.sh`가 파싱한 세 입력 칸이 helper까지 전달되고, helper 실패가 acceptance 실패로 연결된다.

## 대표 고장 사본 공격

| 독립 임시 고장 사본 | 공격 입력 | 관찰 결과 | 해석 |
|---|---|---|---|
| boundary check 제거 | `ＰR #131` | faulty rc 1 | 정상 허용 케이스를 과잉 거부하므로 계약 위반이 드러난다. |
| first occurrence 뒤 탐색 중단 | `hs-kickoff and hѕ-kickoff` | faulty rc 0 | 같은 줄 정상 토큰 뒤 위장을 놓치므로 계약 위반이 드러난다. |
| whitespace-only 입력 허용 | `   \n` | faulty rc 0 | 입력 오류 rc 2 계약을 깨므로 드러난다. |
| shell helper 결과 무시 | workflow+SOT `ｘhs-kickoff` | faulty rc 0, `SPOOF` 출력 뒤 `PASS: CI 스텝...`, `CHECKED: 12` | helper 출력만 내고 판정에 반영하지 않는 결함은 실제 shell wiring 공격에서 녹색으로 새므로 현재 제품의 rc 연결이 필수다. |

→ 네 대표 고장 사본 모두 독립 임시 위치에서 계약 위반으로 노출됐다. 실제 후보는 같은 공격에서 실패한다.

## Unicode 데이터와 재생성

| 항목 | 직접 증거 | 판정 |
|---|---|---|
| 공식 원본 URL | `https://www.unicode.org/Public/17.0.0/security/confusables.txt` | PASS |
| 공식 원본 SHA-256 | 다운로드 후 `091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a` | PASS |
| 생성기 | `python3 scripts/verify/generate-hs-kickoff-confusables.py <download>` → rc 0 | PASS |
| 생성물 SHA-256 | generated `687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd`, committed same | PASS |
| 바이트 비교 | `regeneration_exact_match True` | PASS |
| mapping count | JSON actual 628, selection 628 | PASS |
| 라이선스 | `docs/licenses/unicode-license-v3.txt` 첫 줄 `UNICODE LICENSE V3`, copyright/permission notice 포함 | PASS |
| 데이터 손상 | 임시 JSON 바이트 변경 | rc 2, `파일 sha256 불일치` | PASS |
| 동일 count 변조 | `mapping_count`는 유지하고 codepoint 1개 변경 | rc 2, `파일 sha256 불일치` | PASS |

→ Unicode 17.0.0 출처, 고정 SHA, 생성물, 628개 매핑, 라이선스, 재생성이 모두 직접 확인됐다.

## 크기·의존성·RED 확인

| 항목 | 직접 증거 | 판정 |
|---|---|---|
| hard600 | 직접 코드/시험 파일 최대 `scripts/acceptance-hs-kickoff-mutations.sh` 595줄 | PASS |
| hard100 | 최대 Python 함수 27줄, 최대 shell 함수 20줄 | PASS |
| 새 JS 의존성 | `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` 없음 | PASS |
| 새 Python 의존성 | `pyproject.toml`, `uv.lock`, `requirements.txt` diff 변경 없음 또는 파일 없음 | PASS |
| RED commits 존재 | `git cat-file -t` for `396cd2b...`, `d1058ca...`, `e99b454...` → 모두 `commit` | PASS |

→ 새 패키지/락파일 의존성 추가 증거는 없고, 크기 제한도 지킨다.

## 확인 못한 범위

- 원격 CI, push, PR, merge, 배포, 운영 포털, DB, 메시지 전송은 요청상 금지라 NOT_RUN이다.
- SOT의 전체 30개 CI 스텝을 모두 재실행하지는 않았다. HS-00.03 계약에 직접 연결된 `verify.sh`, hs-kickoff acceptance, hs-kickoff mutations, G2 기본/변이/antiforge를 실행했다.
- Claude V1 원문/보정본/메타 파일은 존재하지만, 해당 PASS 주장은 근거로 사용하지 않았다.

## 작업트리 영향

제품·시험·SOT·goal 파일은 수정하지 않았다. 새로 작성한 파일은 이 증거 파일뿐이다. 검증 중 생성한 고장 사본과 shell 배선 사본은 임시 디렉터리/임시 worktree에서 만들고 제거했다.
