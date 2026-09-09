VERDICT: FAIL

# HS-00.02 Codex V2 독립 적대 재검증

## 결론

현재 후보는 기대한 실패 사유가 실제 `FAIL: ` 줄에 있어야 한다는 핵심 동작 대부분을 만족합니다. 정조준 시험 20개, 기존 변이 37개, G2 전체 239개, 24개 고장 주입, 63개 직접 입력 공격, 13개 negative 본문 공격은 V1의 주요 숫자와 재현됐습니다.

그래도 최종 완료 판정은 실패입니다. 공백만 있거나 탭만 있는 기대값이 “실패 사유 없음”인데도 성공으로 인정됩니다. 또한 카드의 가짜 합격 조건에 적힌 `FAIL` 줄 제한 생략과 빈 기대값 수락은 현재 제품이 직접 입력에서는 막지만, 고정된 pytest가 그 고장을 잡지 못합니다.

이 실패는 실제 포털·DB·브라우저 문제가 아닙니다. 내부 검증 도구의 입력 경계와 시험 강도 문제입니다. 현재 31개 호출처는 모두 비공백 상수라 즉시 사업 동작을 깨지는 않지만, 검증 게이트가 “엉뚱한 이유로 실패했는데도 성공”을 막는 작업이므로 완료 주장을 막습니다.

초기 V2 환경 확인에서 비밀값이 들어 있는 환경 전체를 불필요하게 출력했습니다. 해당 `v2-env.log/json`은 공개 증거에서 제외했고, 값을 가린 메모만 남겼습니다. 최초 도구 응답에도 실제 값이 출력됐으므로 노출 범위는 “로컬 v2-env 원본 로그 생성 및 도구 응답 표시”입니다. 이후 값 재수집은 하지 않았고, 마지막 검사에서 v2 산출물 104개 중 비가림 환경 라인 0개를 확인했습니다.

## 판단 근거

V1의 큰 줄기는 재현됐습니다. 종료값은 프로그램의 성적이며 0은 합격, 0이 아니면 불합격입니다. `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0002.py`는 종료값 0으로 20개를 통과했고, `bash scripts/acceptance-hs-kickoff-mutations.sh`는 종료값 0으로 `CHECKED: 37`을 냈습니다. `bash scripts/acceptance-hs-gates.sh`는 종료값 0으로 `COLLECTED: 239`를 냈습니다.

고장 주입 결과도 V1과 같습니다. 뮤테이션은 일부러 코드를 고장 내서 시험이 진짜 실패하는지 보는 검사입니다. 24개 중 16개는 시험이 잡았고, 8개는 살아남았습니다. 살아남은 목록은 `m04-omit-fail-line-filter`, `m07-accept-empty-expected`, `m09-legacy-match-unanchored-end`, `m11-boundary-any-non-alnum`, `m15-drop-newline-guard`, `m16-unreadable-file-exit0`, `m21-pass-lines-also-count`, `m24-legacy-count-allow-zero`입니다.

V1과 다른 판단은 F4입니다. V1은 공백 한 칸 기대값을 정보로 낮췄지만, T 계약은 기대 사유가 없으면 거부하라고 합니다. V2 독립 공격은 공백 한 칸뿐 아니라 탭 한 칸도 종료값 0으로 받아들이는 것을 확인했습니다. 이것은 현재 호출처가 쓰지 않는 입력이라 사업 영향은 낮지만, 입력·오류·경계 계약 위반입니다.

V1의 F1~F3은 재현됐고 제품 직접 입력은 현재 맞습니다. 다만 “검사 강도 충족” 주장은 과합니다. 카드의 counter-AC는 가짜 합격 시나리오이며, 그중 FAIL 행 제한 생략과 빈 기대값 수락은 고정 pytest에서 독립적으로 죽지 않았습니다. 직접 probe로 현 제품이 맞다는 사실과, 회귀 시험이 그 고장을 고정하지 못한다는 사실은 다릅니다.

V1의 F5는 재현됐지만 현재 실패로 보지는 않습니다. 기대값 `CI`처럼 너무 짧은 문자열은 `CI 배선 불량`과 `CI 스텝 불일치`를 모두 통과시킬 수 있습니다. 그러나 실제 31개 호출처는 그런 짧은 기대값을 쓰지 않고, V2 호출처 추출에서도 고유 기대값 9종 모두 의미 있는 문구였습니다.

## V1 대 V2 대조

| 항목 | V1 주장 | V2 결과 | 판정 |
|---|---|---|---|
| 정조준 pytest | 20 passed | 20 passed | 일치 |
| 기존 변이 | PASS 37 / CHECKED 37 | 종료값 0 / CHECKED 37 | 일치 |
| G2 | 239 수집·통과 | COLLECTED 239 / 종료값 0 | 일치 |
| 한도 | 593/51/178줄, 600 허용·601 거부·0 거부 | 같은 수치 재현 | 일치 |
| 24개 변이 | 16 killed / 8 survived | 같은 16/8, unexpected 0 | 일치 |
| CLI 63건 | expected-space-only 1 불일치 | 같은 1 불일치 | 일치 |
| negative 13건 | mismatch 0 | mismatch 0 | 일치 |
| F1 | 낮음, 제품 정상 | REPRODUCED, 시험 강도 결함 | 부분 불일치 |
| F2 | 낮음, 제품 정상 | REPRODUCED, 시험 강도 결함 | 부분 불일치 |
| F3 | 낮음, 제품 정상 | REPRODUCED, 시험 강도 결함 | 부분 불일치 |
| F4 | 정보 | REPRODUCED, 입력 경계 제품 결함(공백 1건 재현, 탭 1건 확장 공격 추가) | 불일치 |
| F5 | 정보(설계) | REPRODUCED, 현재 호출처 영향 없음 | 일치 |

→ 해석: V1의 실행 숫자는 대체로 맞습니다. 뒤집힌 부분은 결함의 의미와 최종 PASS입니다.

## 결함 목록

### D1 · 낮음 · 공백/탭 기대값이 실패 사유 없이 성공한다

- 위치: `scripts/verify/has-kickoff-failure.py:22` — 빈 기대값만 거부하고 공백만 있는 문자열은 거부하지 않습니다.
- 원인: `not expected`는 `""`만 잡고 `" "`나 `"\t"`는 잡지 못합니다. 이후 `message.startswith(expected)`와 경계 검사가 통과합니다.
- 사업 영향: 현재 31개 호출처는 비공백 상수라 즉시 오작동하지 않습니다. 그러나 기대 사유가 변수로 들어오는 다음 호출처가 생기면, 실패 사유가 없는데도 “기대한 사유로 실패했다”고 셀 수 있습니다.
- 증거: `v2-cli-probes.json`의 `expected-space-only`, `v2-shared-blindspot.json`의 `space-only-expected`, `tab-only-expected`.

### D2 · 낮음 · counter-AC 일부가 고정 pytest에서 독립적으로 죽지 않는다

- 위치: `humansearch/tests/test_hs_0002.py:103`, `humansearch/tests/test_hs_0002.py:115`, `scripts/verify/has-kickoff-failure.py:21`, `scripts/verify/has-kickoff-failure.py:24`.
- 원인: PASS 미끼와 빈 기대값 사례가 현재 제품 결과는 확인하지만, `FAIL` 줄 필터 삭제와 빈 기대값 가드 삭제라는 구체 고장을 독립적으로 실패시키지 못합니다.
- 사업 영향: 현재 제품은 raw line bait와 empty expected를 직접 probe에서 거부합니다. 하지만 같은 줄을 리팩터링으로 잃어도 기존 pytest만으로는 침묵할 수 있습니다.
- 증거: `v2-mutants.json`에서 `m04-omit-fail-line-filter`, `m07-accept-empty-expected`, `m21-pass-lines-also-count`가 살아남았습니다.

### D3 · 낮음 · legacy 경계·파일 읽기 오류 경로가 고정 pytest 바깥에 있다

- 위치: `humansearch/tests/test_hs_0002.py:155`, `humansearch/tests/test_hs_0002.py:172`, `scripts/verify/has-kickoff-failure.py:42`.
- 원인: `fullmatch`를 `match`로 낮추거나 경계를 비영숫자 전체로 넓히거나 파일 읽기 오류를 성공으로 바꿔도 정조준 pytest가 실패하지 않습니다.
- 사업 영향: 직접 CLI 공격은 현재 제품이 `행 없음XYZ`, em dash, missing file, directory, invalid UTF-8을 거부함을 보였습니다. 시험 강도 부채입니다.
- 증거: `v2-mutants.json`의 `m09`, `m11`, `m16` 생존과 `v2-cli-probes.json`의 대응 직접 probe.

## 증거 원문 위치

- `v2-evidence.json` — 명령, 종료값, 출력 파일, 지문 요약.
- `v2-target-pytest.log/json` — 20개 정조준 시험.
- `v2-mutations-37.log/json` — 기존 변이 37개.
- `v2-g2.log/json` — G2 239개 수집·통과.
- `v2-mutants.py`, `v2-mutants.json`, `v2-mutant-*.diff`, `v2-mutant-*.log` — 24개 고장 주입 원문.
- `v2-cli-probes.py/json`, `v2-cli-probes-run.log` — 63개 직접 CLI 공격.
- `v2-negative-extra.py/json`, `v2-negative-extra-run.log` — 13개 negative 본문 공격.
- `v2-shared-blindspot.py/json`, `v2-shared-blindspot-run2.log` — V1과 다른 독립 공격.
- `v2-budget-*.log/json`, `v2-wc.log/json` — 파일 한도와 600/601/0 경계.
- `v2-env-redaction-note.json` — 제외된 환경 출력의 가림 기록.
- `v2-final-privacy-zero-match.json` — 완료 직전 v2 산출물 값 일치 0개 확인.

## 미검증과 한계

- 원격 CI, push, PR, 병합, 운영 DB, 실제 포털, 브라우저, 라이브 readback은 실행하지 않았습니다. 이번 범위가 HS-00.02 내부 expected-failure matcher였기 때문입니다.
- HS-00.03 동형 문자, HS-00.04 workflow 실행 의미, HS-00.05 앞 단계 환경, WU0-B 출력 진위 인증은 별도 장부 범위입니다.
- 같은 UID 로컬 검토이며 P17 독립 영수증이 아닙니다.
- 첫 번째 `v2-shared-blindspot-run`은 스크립트를 잘못된 루트에 만든 제 절차 오류로 종료값 2를 냈고, 원문은 보존했습니다. 파일을 지정 작업트리의 v2 경로로 옮긴 뒤 `v2-shared-blindspot-run2`에서 정상 실행했습니다.
