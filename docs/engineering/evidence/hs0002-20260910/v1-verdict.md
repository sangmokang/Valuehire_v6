VERDICT: PASS

# HS-00.02 실제 Claude V1 독립 적대 검증 판정

검증자: Claude V1(실제 도구 실행, 같은 UID 로컬 검토). OS/P17/라이브 영수증이 아닙니다.
대상 HEAD `0263108eab043dbb4780f7c9ca6ac0528808b31d`(RED), base `6cef849`. 시작 2026-09-09T22:03:34Z, 종료 22:15:35Z(UTC).
원본 다섯 파일 SHA256은 시작·종료 시점에 동일하며 candidate-files.json과 일치합니다. RED 커밋의 시험 파일과 현재 시험 파일은 지문 `8817487d…8be43`으로 같습니다.

## 결론

기대한 실패 사유가 실제 FAIL 줄에 그대로 있을 때만 성공으로 세고, 다른 사유 안에 끼어든 문구·정규식·PASS 줄 미끼·빈 값은 거부합니다. 기존 37건 시험과 새 시험 20건, 전체 회귀 239건이 모두 통과했고, 제가 격리 사본에 넣은 고장 24종 가운데 핵심 고장 16종은 고정된 시험이 잡았습니다. 살아남은 8종은 제품이 틀린 것이 아니라 시험이 그 조항을 따로 못 박지 않은 것이며, 제품 원문에 직접 입력을 넣어 모두 올바르게 거부됨을 확인했습니다. 높음·중간 결함은 없습니다.

## 건너뜀·미확인·재시도

- 재시도 3건(모두 제 검증 절차 오류, 제품 무관): 변이 37건 1차는 작업 폴더 오류로 스크립트 자체가 실행되지 않음 → 루트에서 재실행. CLI 공격 스크립트 1차는 제 파일의 바이트 리터럴 문법 오류 → 수정 후 재실행. negative 본문 경유 공격 1차는 시스템 python에 pytest 없음 → uv 가상환경 python으로 재실행. 실패 원문은 `v1-*-attempt1-failed.*`에 보존.
- 미실행(범위 밖): 원격 CI, 병합, 실제 포털/DB/메시지/브라우저, HS-00.03 동형 문자, HS-00.04 workflow 실행 의미, HS-00.05 앞 단계 환경, WU0-B 출력 진위 인증.
- 추정: "정규 출력"이란 검사기 `scripts/acceptance-hs-kickoff.sh`가 pass/failc/CHECKED로만 stdout을 내며 stderr가 합쳐진다는 사실을 grep으로 확인한 것에 근거합니다.

## 판단 근거

- 선택한 해석: 계약 §T의 "FAIL 행의 정규 문구에 나타나면"을 "`FAIL: ` 뒤에서 기대 문구로 시작하고 끝/공백/탭/슬래시 경계"로 읽었고, 짧은 사유 3종은 검사기 109/111/113행이 내는 전체 문구의 정규식 fullmatch로 읽었습니다. 제품이 정확히 이 해석을 구현합니다.
- 버린 해석: "FAIL 행 어디에든 문구가 있으면 인정"은 계약이 명시적으로 거부(부분문자열)하며, m12 변이로 넣었을 때 시험이 잡았습니다. "전체 행 완전 일치"는 상세 설명이 붙는 정상 사유를 과잉 차단하며, m20 변이로 시험이 잡았습니다.
- 틀리면 깨지는 것: 제가 정규 형식이라 부른 문구가 검사기 실제 출력과 다르면 37건 변이 실행이 빨개져야 합니다. 실제 실행에서 37/37 PASS, 특히 음성4(처분이 둘 이상)·음성9/15/19(행 없음)·음성20(대상 칸에 다른 대상)·음성6(판정 문서 없음)이 기대 사유로 차단됐습니다. 6개 대상 × 3개 legacy 정규 문구 18건을 CLI로 직접 넣어 모두 exit 0이었습니다.
- 단순 PASS가 아닌 근거: 옛 grep 복원(m06)은 12건, 항상 허용(m01) 11건, 항상 거부(m02) 9건, 정규식 복원(m03) 8건, 경계 삭제(m05) 2건, 셸 인수 순서 바꿈(m18) 9건, 셸 따옴표 제거(m19) 9건의 실제 단언 실패를 냈습니다.

## 기술 상세와 증거

### 정상 대조군 (모두 직접 실행)

| 실행 | 명령 | 종료값 | 결과 | 보존 |
|---|---|---|---|---|
| 정조준 | `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0002.py` | 0 | 20 passed | v1-target-pytest.log/json |
| 기존 변이 | `bash scripts/acceptance-hs-kickoff-mutations.sh` | 0 | PASS 37 / FAIL 0 / CHECKED 37 | v1-mutations-37.log/json |
| G2 | `bash scripts/acceptance-hs-gates.sh` | 0 | ruff·mypy 44 clean, 239 수집·통과, hs_0002 노드 20 | v1-g2.log/json |
| 정적 | ruff, mypy(+helper 45파일), bash -n, git diff --check | 0 | 모두 clean | v1-static.log |
| 한도 | budget-check.py candidate/boundaries/자체 코드 | 0 | 593/51/178줄, 함수 최대 32줄, 600허용·601거부·0거부 | v1-budget.log |

→ 해석: 구현자 green-*.log와 같은 결과를 현재 지문에서 제가 다시 얻었습니다. 과거 지문으로 승인하지 않았습니다.

### 격리 사본 변이 24종 (`v1-mutants.py`, mktemp 사본, GIT_*/BASH_ENV/ENV 제거, 원본 무변경)

| 변이 | 대상 | 결과 | 실패 시험 수 |
|---|---|---|---|
| m00 정상 사본 | – | PASS | 20 passed |
| m01 항상 허용 | helper `return True` 삽입 | KILLED | 11 |
| m02 항상 거부 | helper `return False` 삽입 | KILLED | 9 |
| m03 정규식 복원 `re.search(expected)` | helper | KILLED | 8 |
| m04 FAIL 행 필터 삭제 | helper 25–26행 | **SURVIVED** | 0 |
| m05 경계 삭제 (startswith만) | helper 32–34행 | KILLED | 2 |
| m06 옛 grep 복원 | mutations.sh 189행 | KILLED | 12 |
| m07 빈 기대값 가드 삭제 | helper 22행 | **SURVIVED** | 0 |
| m08 legacy 부분문자열 | helper 29행 | KILLED | 3 |
| m09 legacy `re.match`(끝 비고정) | helper 29행 | **SURVIVED** | 0 |
| m10 legacy `re.search` | helper 29행 | KILLED | 3 |
| m11 경계를 비영숫자 전체로 확대 | helper 33행 | **SURVIVED** | 0 |
| m12 행 중간 부분문자열+경계 | helper | KILLED | 3 |
| m13 legacy 대상 정규식 `.*` | helper 7행 | KILLED | 2 |
| m14 `/` 경계 삭제 | helper 33행 | KILLED | 1 |
| m15 개행 가드 삭제 | helper 22행 | SURVIVED(동등) | 0 |
| m16 파일 못 읽으면 exit 0 | helper 46행 | **SURVIVED** | 0 |
| m17 셸 판정 반전 | mutations.sh 189행 | KILLED | 20 |
| m18 셸 인수 순서 바꿈 | mutations.sh 189행 | KILLED | 9 |
| m19 셸 `$expect` 따옴표 제거 | mutations.sh 189행 | KILLED | 9 |
| m20 전체 행 완전 일치만 | helper 33행 | KILLED | 6 |
| m21 PASS 행도 대조 | helper 25행 | **SURVIVED** | 0 |
| m22 `FAIL: ` 접두 제거 생략 | helper 27행 | KILLED | 9 |
| m23 legacy 표 비움 | helper 8행 | KILLED | 3 |
| m24 legacy 개수 0 허용 | helper 11행 | SURVIVED(동등) | 0 |

→ 해석: 카드가 정의한 가짜 합격 조건(항상 허용/거부, 경계 생략, 정규식, 옛 grep, legacy 부분문자열, 과잉 차단)은 모두 잡힙니다. 살아남은 8종은 아래 결함 항목으로 분류했습니다. diff와 전체 출력은 `v1-mutant-<이름>.diff/.log`.

### 제품 원문 직접 공격 (`v1-cli-probes.py` 63건, `v1-negative-extra.py` 13건)

- CLI 입력 오류: 인수 1개/4개 → 2, 파일 없음 → 2, 디렉터리 → 2, UTF-8 깨진 바이트 → 2. 셸에서 `!`로 감싸므로 2는 실패로 닫힙니다.
- FAIL 행 시작: `FAIL:CI…`(공백 없음)·` FAIL: …`(앞 공백)·`fail:`·BOM 접두 → 1. 뒤쪽 줄의 FAIL도 인정(0). CRLF 허용(0).
- 문자 경계: `불량XYZ`·`불량—상세`·`불량-상세` → 1. `불량\t상세`·줄 끝·`없음/빈 파일` → 0.
- 정규식 메타: 기대 `.*`는 아무 행에도 안 맞음(1), 기대 `^…$`·`[CI]`는 문자 그대로만 인정(0), `A|B`는 인정 안 됨(1).
- 빈값/개행: 기대 ``·`…\n`·`…\r` → 1. `FAIL: `(빈 메시지)+빈 기대 → negative 본문에서 FAIL, CHECKED 1.
- legacy 3형식: 6개 대상 × 3문구 정규 형식 18건 → 0. `PR #131` 허용, `PR #`·`task/hs d1`·`행이 1개`·`다른 대상 0개`·끝 잘림·`행 없음XYZ`·앞 미끼 → 1.
- PASS/CHECKED 미끼: PASS만 있는 로그, `CHECKED: CI 배선 불량` 줄, 접두 없는 생 줄 → negative 본문에서 모두 FAIL.
- 실제 negative 본문: 검사기 실제 문구 6종(CI 배선 불량/CI 스텝 불일치/자리표시자/실재하지 않음/경로 없음/판정 문서 없음) → PASS 한 건·CHECKED 1·exit 0. `PR #54` 사유에 `PR #13` 기대 → FAIL.

→ 해석: 계약 §T의 합격·거부 조건을 제품 원문이 그대로 만족합니다. 예상과 다른 1건(공백 한 칸 기대값)은 F4에 적었습니다.

### 결함 목록

**F1 · 낮음 · FAIL 행 제한과 빈 기대값 가드가 시험으로 독립 고정되지 않음**
- 위치: `humansearch/tests/test_hs_0002.py:104`(PASS 미끼 사례, 미끼 문구가 줄 시작이 아님), `:116`(빈 기대값 사례, 메시지가 경계 검사로도 거부됨).
- 원인: 접두 대조가 PASS 줄을 이미 배제하고 경계 검사가 빈 기대값을 이미 거부해 helper 22·25–26행이 시험상 잉여가 됩니다. 구현자도 g-retry-explanation.md에서 같은 무효과를 기록했고, 자기 empty-allowed 변이는 더 강한 `return True` 형태로 만들어 잡았습니다.
- 사업 영향: 제품은 정상(생 줄 미끼·`FAIL: ` 빈 메시지 직접 확인). 향후 리팩터에서 두 줄이 사라져도 시험이 침묵하는 시험 강도 부채입니다. 다음 회귀 파일에서 `FAIL: `(빈 메시지)와 접두 없는 생 줄 사례를 추가하면 닫힙니다.

**F2 · 낮음 · legacy 끝 경계와 경계 문자 집합이 시험으로 고정되지 않음**
- 위치: `humansearch/tests/test_hs_0002.py:155`(bait는 앞 미끼만), `:173`(확장 알파벳이 영숫자만).
- 원인: `fullmatch`→`match`(m09)와 `" \t/"`→비영숫자 전체(m11)가 시험 입력 공간 밖입니다.
- 사업 영향: 제품은 정상(`행 없음XYZ`·`불량—상세` 직접 거부). 시험 강도 부채.

**F3 · 낮음 · 파일 누락/입력 오류 경로가 시험으로 고정되지 않음**
- 위치: `scripts/verify/has-kickoff-failure.py:39-46`(usage/읽기 오류 exit 2), 시험은 harness가 항상 out.log를 씁니다.
- 원인: 시험이 helper CLI를 직접 호출하지 않고 negative 본문만 호출합니다.
- 사업 영향: 제품은 정상(exit 2 직접 확인). run_target이 항상 out.log를 쓰므로 실제 경로에서 발현 가능성은 낮습니다.

**F4 · 정보 · 공백만 있는 기대값이 빈 값으로 거부되지 않음**
- 위치: `scripts/verify/has-kickoff-failure.py:22`(`not expected`만 검사).
- 원인: 기대 `" "`와 메시지 `"  x"`는 startswith·경계 검사를 모두 통과해 exit 0입니다.
- 사업 영향: 31개 호출은 모두 비공백 상수라 영향 없음. 계약 "비었거나"를 좁게 읽은 것이며 강화하려면 `expected.strip()` 검사와 새 RED가 필요합니다.

**F5 · 정보(설계) · 접두 대조의 짧은 기대값**
- 무엇을: 기대 `CI`가 `CI 배선 불량 …`과 `CI 스텝 불일치 …` 둘 다에 인정됩니다.
- 왜: 계약이 "기대 문구로 시작+경계"를 요구하고 31개 문자열 유지를 명시합니다.
- 버린 길: 전체 행 완전 일치는 상세 설명이 붙는 정상 사유를 과잉 차단(m20에서 6건 실패로 확인).
- 대가: 기대 문자열이 사유 전체를 담아야 구분력이 생깁니다. 현재 31개는 사유 첫 절 전체를 담습니다.
- 되돌리기: 별도 WU에서 기대 문자열을 더 길게 바꾸면 되며, 이 WU 범위 밖입니다.

### 반증 기록 (깨려다 실패한 것)

옛 grep과 같은 거짓 합격을 만들려고 부분문자열(m12), PASS 미끼(negative-extra), 정규식(m03, CLI `.*`·`A|B`), 경계 없는 확장(CLI `XYZ`·`—`·`-`), legacy 앞/뒤 미끼(CLI), 셸 인용 깨기(m19, `$HOME`·공백 경로), 인수 뒤바꿈(m18), 잘못된 대상 번호(`PR #54`↔`PR #13`)를 모두 시도했고 제품 원문은 전부 거부했습니다. 제품이 정상 사유를 과잉 차단하게 만들려는 시도(6종 실제 문구, CRLF, 탭, 줄 끝, 슬래시, 18개 legacy 정규 문구)도 모두 인정됐습니다.

### 보존 경로

artifacts/hs0002-20260910/ 아래 `v1-fingerprints-before/after.txt`, `v1-target-pytest.*`, `v1-mutations-37.*`, `v1-g2.*`, `v1-static.log`, `v1-budget.*`, `v1-mutants.py/.json`, `v1-mutant-*.diff/.log`, `v1-cli-probes.py/.json`, `v1-negative-extra.py/.json`, `v1-*-attempt1-failed.*`, `v1-evidence.json`.
