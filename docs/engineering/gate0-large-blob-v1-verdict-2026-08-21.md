<!-- codex(V1) 원문 보존 — codex exec --ephemeral --json --sandbox read-only, 종료값 0 -->
<!-- 판정 대상 커밋: c29dc13..bbccfd2 (감사 중 9a128c7 추가됨, 소급 반영하지 않음) -->

VERDICT: FAIL.

## 결론

제출된 두 변경만으로는 승인하실 수 없습니다. 큰 파일에서 금지값을 놓치던 문제는 바로잡았지만, 실패 이유를 한 환경의 결과로 고정해 서버 시험이 깨지고 반드시 막아야 할 한 갈래도 시험으로 보호하지 못했습니다.

### 판정 전 공개

- 판정 대상은 요청하신 `c29dc13..bbccfd2`로 고정했습니다.
- 감사 도중 다른 작업자가 `9a128c7`을 추가해 브랜치가 한 커밋 전진했습니다. 이 후속 커밋은 제가 찾은 주결함을 보완하지만, 원 제출물의 합격 근거로 소급하지 않았습니다.
- 읽기 전용 지시 때문에 임시 저장소를 만들고 지우는 21사례 전체 시험은 재실행하지 않았습니다. 대신 기존 객체를 사용하는 파이프 실험, 커밋별 원문, 셸 의미, YAML 구조를 읽기 전용으로 검증했습니다.
- 실제 GitHub 실행 결과 조회는 네트워크 차단으로 실패했습니다. 이후 추가된 `9a128c7` 커밋 기록이 리눅스 실행 실패를 독립적으로 확인합니다.
- 처음 작성한 파이프 실험 2개는 따옴표 오류로 실행되지 않았습니다. 해당 결과는 버리고 단순화해 재실행했습니다.
- `.github/workflows/verify.yml`을 Bash 문법으로 검사한 시도는 대상 형식이 달라 무효입니다. YAML은 Ruby Psych 파서로 다시 확인했습니다.
- 저장소 파일은 수정하지 않았습니다.

## 판단 근거

| ID | 계약 | 판정 | 핵심 근거 | 심각도 |
|---|---|---|---|---|
| T1 | 작은 파일과 50MiB 파일을 로컬·서버 모두 차단 | 부분 확인 | 현재 파이프는 50MiB에서 생산자 0·검사기 0, 옛 방식은 141·0으로 재현됐습니다. | 중간 |
| T2 | 읽기·내용 대조 실패를 통과시키지 않음 | 구현 확인·검증 불충분 | 판정 분기는 존재하지만 내용 대조 종료값 2 전용 시험은 없습니다. | 높음 |
| T3 | 예정 수와 실행 수 불일치 시 실패 | 구현 확인·우회 가능 | 정상 외부 21, 내부 17 계산은 맞지만 환경변수 하나로 전체 시험을 1사례로 축소할 수 있습니다. | 중간 |
| T4 | 차단 사례는 예정 실패 문구까지 확인 | 불일치 | 깨진 패턴 사례가 macOS 사유만 요구하여 리눅스에서 다른 정상 차단 사유가 나오면 시험이 실패합니다. | 높음 |
| T5 | 로컬·서버 등가 검사 | 동작 사례 확인·설계 불일치 | 동일 합성값은 잡지만 판정 코드와 패턴 의미가 서로 다른 두 벌입니다. | 중간 |

→ 무엇을 대조했나: 계약 5개를 입력·판정·출력 문구·사례 계수까지 나눴습니다.  
→ 무엇이 나왔나: 실제 큰 파일 결함은 고쳤지만 서버 운영환경의 실패 사유와 시험 기대값이 충돌합니다.  
→ 판정: T4가 직접 깨지고 T2의 필수 분기가 보호되지 않아 FAIL입니다.

선택한 해석은 “차단만 되면 되는 것이 아니라, 계약에 적힌 예정 사유까지 환경에 맞게 확인해야 한다”입니다. “어느 사유든 0이 아니므로 통과”라는 해석은 버렸습니다. `run_case`가 종료값과 `expected_marker`를 함께 요구하도록 제출자가 직접 계약을 강화했기 때문입니다.

이 판단이 틀리면 리눅스 서버에서도 깨진 패턴이 항상 `cat-file=141`로 나와야 합니다. 그러나 후속 커밋 `9a128c7`은 실제 리눅스에서 `cat-file=0`, `grep=2`가 나와 원 제출 시험이 실패했다고 기록하고 그 차이를 수정했습니다.

## 기술 상세와 증거 원문

### D1 — 높음: “서버 본문도 대조 불능 패턴을 값 없음으로 통과하지 않음”

- 원문 제목: `서버 본문도 대조 불능 패턴을 값 없음으로 통과하지 않음`
- 원인: `bbccfd2:scripts/acceptance-0-2-unreachable-content.sh:267-276`은 깨진 정규식의 예정 사유를 오직 `히스토리 blob 읽기 실패`로 고정합니다.
- 사업 영향: GitHub 서버에서 올바르게 차단되더라도 시험이 실패해 배송이 막힙니다. 반대로 이 시험을 단순 완화하면 내용 대조 실패 분기가 다시 무방비가 됩니다.
- 판정: 원 제출물의 직접 차단 결함입니다.

관련 원문:

```bash
# bbccfd2:scripts/acceptance-0-2-unreachable-content.sh:267-276
# 역할: 깨진 정규식의 예상 실패 문구를 고정
printf '%s\n' '[' > "$ci_pattern_error/.secret-patterns.default"
run_case '서버 본문도 대조 불능 패턴을 값 없음으로 통과하지 않음' blocked \
  'FAIL: 히스토리 blob 읽기 실패' "$ci_pattern_error" \
  run_ci_history_scan "$ci_pattern_error"
```

→ 깨진 패턴이 “내용 대조 실패”로 보고되면 올바른 비정상 종료여도 이 사례는 `UNEXPECTED`가 됩니다.

직접 재현:

```text
small-invalid producer=0 grep=2 reason=compare-failure
large-invalid producer=141 grep=2 reason=read-failure
drain-then-2 producer=0 grep=2 reason=compare-failure
producer-71 producer=71 grep=1 reason=read-failure
```

→ 같은 검사기 오류라도 입력 크기와 실행 순서에 따라 “내용 대조 실패”와 “읽기 실패”가 갈립니다. 실패 사유 하나만 고정할 수 없습니다.

감사 도중 추가된 후속 커밋 원문:

```text
9a128c7 test(AC-19): grep 구현 차이를 계약에 반영하고 대조 실패 경로를 결정적으로 덮는다

서버 검사(리눅스·GNU grep)가 로컬(macOS·BSD grep)과 다르게 실패했다.
리눅스는 cat-file 이 정상 종료하고 grep 만 2 를 내 '내용 대조 실패'로 표면화된다.
고정 문자열 하나로 기대하면 한쪽 플랫폼에서 반드시 깨진다.
```

→ 원 제출물 `bbccfd2`의 알려진 한계가 실제 서버 차이였고, 별도 커밋이 필요했음이 확인됐습니다.

### D2 — 높음: “grep 종료값 2 전용 분기는 덮이지 않는다”

- 원문 제목: `알려진 한계: grep 종료값 2 전용 분기는 뮤테이션으로 덮이지 않는다`
- 원인: 구현 분기는 있지만 기존 깨진 패턴 사례가 macOS에서 앞단 종료값 141로 먼저 분류됩니다.
- 사업 영향: 누군가 `grep_rc != 1` 분기를 삭제해도 제출자가 보고한 뮤테이션 결과처럼 전체 시험이 계속 성공합니다.
- 판정: 분기를 빼면 안 됩니다. 입력을 끝까지 소비한 뒤 2를 반환하는 대역 검사기로 반드시 고정해야 합니다.

구현 원문:

```bash
# bbccfd2:.github/workflows/verify.yml:108-119
# 역할: 읽기 실패·일치·내용 대조 실패를 서로 다른 상태로 판정
cat_file_rc=${blob_scan_status[0]:-1}
grep_rc=${blob_scan_status[1]:-2}
if [ "$cat_file_rc" -ne 0 ]; then
  echo "FAIL: 히스토리 blob 읽기 실패: $sha (exit=$cat_file_rc)"
  hit=1
elif [ "$grep_rc" -eq 0 ]; then
  echo "FAIL: 히스토리 blob에 자격증명 패턴 매치: $sha"
  hit=1
elif [ "$grep_rc" -ne 1 ]; then
  echo "FAIL: 히스토리 blob 내용 대조 실패: $sha (exit=$grep_rc)"
  hit=1
fi
```

→ 구현은 실패 방향으로 닫혀 있습니다. 결함은 마지막 분기를 삭제해도 시험이 잡지 못한다는 점입니다.

`grep`은 정상적으로 일치하면 0, 불일치하면 1, 오류면 보통 2를 반환합니다. 다른 구현은 2보다 큰 오류값도 허용하므로 `-ne 1` 분기는 유지해야 합니다. 또한 `-q`는 첫 일치에서 즉시 종료하므로 앞단 쓰기 프로세스를 깨뜨릴 수 있습니다. [GNU grep 공식 설명](https://www.gnu.org/s/grep/manual/grep.html)

### D3 — 중간: “이 수정이 실제로 SIGPIPE를 없애는가”

`SIGPIPE`는 파이프를 읽는 쪽이 먼저 닫혔을 때 쓰는 쪽 프로세스가 받는 종료 신호입니다. 정상적인 일치 경로에서는 실제로 제거됐습니다.

```text
current-50MiB branch=then producer=0 grep=0
old-q-50MiB branch=else producer=141 grep=0
current-nomatch branch=else producer=0 grep=1
```

→ 무엇을 시켰나: GitHub와 같은 `bash -e`, `pipefail` 조합에서 앞부분에 금지값이 있는 50MiB 입력을 흘렸습니다.  
→ 무엇이 나왔나: 현재 방식은 양쪽 모두 0, 옛 `-q` 방식은 생산자만 141이었습니다.  
→ 판정: 정상 일치에서 원 결함은 고쳐졌습니다.

`PIPESTATUS`는 Bash가 파이프를 구성한 각 명령의 종료값을 보관하는 배열입니다. 두 분기에서 파이프 직후 배열로 복사하므로 값이 보존됩니다. `pipefail`은 구성 명령 중 하나가 실패하면 전체 파이프를 실패로 만들지만, `if` 조건 안의 실패는 `-e`가 셸을 즉시 끝내는 예외입니다. [Bash 파이프 공식 문서](https://www.gnu.org/software/bash/manual/html_node/Pipelines.html), [Bash `-e` 공식 문서](https://www.gnu.org/s/bash/manual/bash.html)

GitHub에서 `shell`을 지정하지 않은 리눅스 단계는 `bash -e {0}`로 실행됩니다. 이 워크플로 본문이 직접 `set -o pipefail`을 실행하므로 실제 조합은 의도와 맞습니다. [GitHub Actions 셸 공식 문서](https://docs.github.com/en/enterprise-server%403.21/actions/reference/workflows-and-actions/workflow-syntax)

다만 비교 도구가 자체 오류로 조기에 종료하면 141은 다시 생길 수 있습니다. 현재 코드는 이를 차단하므로 보안상 통과하지는 않지만, 실패 사유는 환경마다 달라집니다.

### D4 — 중간: “grep -a 도입으로 놓치게 되는 것은 없는가”

`-a`는 이진 데이터를 텍스트처럼 처리하는 옵션입니다. 합성 사례처럼 `금지값 + 줄바꿈 + NUL`인 입력은 직접 공격했지만 놓치지 못했습니다.

```text
default_binary_rc=0
text_binary_rc=0
bsd_default_qnul_rc=0
bsd_text_qnul_rc=0
bsd_default_envnul_rc=0
bsd_text_envnul_rc=0
```

→ macOS BSD grep에서는 기본 방식과 `-a` 방식 모두 해당 입력을 탐지했습니다. 이 공격은 실패했습니다.

다만 ※GNU 공식 설명상 이진 모드와 텍스트 모드는 NUL을 줄 경계로 보는 방식이 달라 `q$` 같은 끝 고정 패턴의 일치 여부가 달라질 수 있습니다. 실제 패턴 파일에도 `^...$` 형태가 있으므로 “놓치는 것이 전혀 없다”고 단정할 수 없습니다. 서버 판정기는 `LC_ALL=C`도 고정하지 않았습니다. [GNU grep 이진 처리 설명](https://www.gnu.org/s/grep/manual/html_node/File-and-Directory-Selection.html)

이는 현재 합성 계약을 깨뜨린 확정 반례는 아니며, 별도 이진·NUL 경계 사례가 필요한 중간 위험입니다.

### D5 — 중간: “TOTAL 17/21이 실제 실행 수와 어긋날 수 있는가”

표준 경로의 수치는 맞습니다.

- 외부 실행: `run_case` 호출 20개 + 훅 무오염 수동 증가 1개 = 21개
- 내부 훅 실행: 환경 격리 2개, 수 불일치 1개, 바깥 훅 1개를 제외 = 17개
- 수 불일치 대역: `TOTAL=2`지만 실제 1개만 실행하므로 최종 검사에서 실패

```bash
# bbccfd2:scripts/acceptance-0-2-unreachable-content.sh:332-339
# 역할: 예정 사례 수와 실제 증가 횟수를 마지막에 대조
printf 'CHECKED: %d\n' "$checked"
if [ "$checked" -ne "$TOTAL" ]; then
  printf 'FAIL: AC-19 실행 사례 수 불일치 (expected=%d, actual=%d)\n' \
    "$TOTAL" "$checked"
  failed=$((failed + 1))
fi
```

→ 정상 실행의 21/17 계산과 의도적인 불일치 탐지는 성립합니다.

하지만 `AC19_PATTERN_ENV_PROBE=1`이 외부 환경에 이미 있으면 `TOTAL=1`로 바뀌고 핵심 사례 전체가 건너뛰어집니다. `run-acceptance.sh`는 `CHECKED >= 1`이면 받아들이며, pre-push도 이 내부 제어변수를 지우지 않습니다. 수치 자체는 맞지만 “정상 시험이 21개여야 한다”는 독립 계약은 없습니다.

또한 문서 수치가 세 갈래입니다.

- `bbccfd2:scripts/acceptance-0-2-unreachable-content.sh:26` — 21
- `bbccfd2:.github/workflows/verify.yml:130` — 20
- `bbccfd2:docs/sot/verification-commands.md:31` — 13

→ 실행 차단에는 직접 영향이 없지만, 운영자가 실제 검증 범위를 잘못 보고하게 됩니다.

### D6 — 중간: “로컬 검사와 서버 본문이 두 벌의 판정기인가”

예, 두 벌입니다.

- `bbccfd2:scripts/acceptance-0-2.sh:12-14,151-168` — 로컬 파일 첫 줄만 읽어, 대소문자를 구분하는 고정 문자열로 검사합니다.
- `bbccfd2:.github/workflows/verify.yml:76-119` — 기본 패턴 전체를 확장 정규식(ERE, 정규식 기능을 확장한 문법)과 대소문자 무시 방식으로 검사합니다.
- 합성 시험은 같은 카나리를 양쪽 파일에 넣어 두 구현이 특정 사례에서 같은 결과를 내는지만 확인합니다.

실제로 `c29dc13`은 로컬 판정기를 먼저 고쳤고, 서버 판정기는 다음 커밋 `bbccfd2`에서 별도로 고쳤습니다. 이미 한쪽만 수리되는 분리가 발생했습니다.

설계 지적:

- 무엇을: 도달 가능한 Git 객체 내용 검사와 종료값 분류를 공용 스크립트 하나로 옮겨 로컬과 CI가 호출해야 합니다.
- 왜: 현재 세 군데의 유사 코드가 같은 조기 종료 결함을 서로 다른 시점에 고쳤습니다.
- 버린 길: 인라인 본문 두 벌을 유지하고 합성 시험으로 동치만 확인하는 길은 편집·패턴 의미 차이를 계속 남기므로 버립니다.
- 대가: 패턴 소스와 고정 문자열·정규식 모드를 공용 인터페이스로 명시하고 기존 호출부를 이관해야 합니다.
- 되돌리기: 공용 호출을 기존 인라인 블록으로 되돌릴 수 있도록 판정 출력과 종료값 계약을 유지하면 됩니다.

### D7 — 낮음: “워크플로 본문을 awk로 추출하는 방식”

`awk`는 정확한 한국어 단계명, 정확한 들여쓰기, `run: |`만 인식합니다.

```bash
# bbccfd2:scripts/acceptance-0-2-unreachable-content.sh:55-66
# 역할: YAML 원문에서 특정 단계의 run 블록을 문자열로 잘라 bash -c로 실행
/^      - name: 히스토리 전량 스캔/ { in_step=1; next }
in_step && /^      - name:/ { exit }
in_step && /^        run: \|/ { in_run=1; next }
in_run { sub(/^          /, ""); print }
...
(cd "$fixture" && bash -c "$ci_step")
```

→ 이름 변경이나 블록 표기 변경은 빈 본문으로 끝나 종료값 2가 되므로 조용히 통과하지는 않습니다. 다만 YAML이 지정하는 `shell`, `working-directory`와 실제 GitHub의 `-e`를 재현하지 않아 완전한 서버 등가 실행은 아닙니다.

설계 지적:

- 무엇을: 이미 저장소에서 사용하는 Psych로 YAML을 파싱해 `run`, `shell`, 조건, 오류 무시 설정을 함께 읽어야 합니다.
- 왜: 원문 들여쓰기 파서는 정상적인 YAML 편집과 실행 의미를 구분하지 못합니다.
- 버린 길: 단계명과 공백 수를 계속 정규식으로 보강하는 길은 새 YAML 표현마다 다시 깨지므로 버립니다.
- 대가: Ruby 사용이라는 기존 도구 의존성이 명시되고, 추출 실패 진단 코드가 조금 늘어납니다.
- 되돌리기: 파싱된 `run` 문자열의 해시와 기존 추출 결과를 한동안 병행 비교한 뒤 기존 경로를 제거할 수 있습니다.

## 반증 기록

깨뜨리려 했지만 실패한 항목도 남깁니다.

- 50MiB 앞부분 일치: 현재 방식은 생산자·검사기 모두 0이어서 깨뜨리지 못했습니다.
- `PIPESTATUS` 양쪽 분기: 일치·불일치 모두 파이프 직후 값이 정확히 보존됐습니다.
- `set -e`와 `pipefail`: `if` 조건 안에서는 의도대로 셸이 조기 종료하지 않았습니다.
- 이진 NUL 입력: 현재 합성값과 고정 문자열은 BSD grep에서 `-a` 유무 모두 탐지됐습니다.
- 객체 읽기 실패: 생산자 71·검사기 1이 별도로 잡혀 읽기 실패로 분류됐습니다.
- 구문·형식: `bash -n scripts/acceptance-0-2-unreachable-content.sh`는 0, `git diff --check c29dc13^..bbccfd2`도 0, Psych YAML 파싱도 성공했습니다.
- 저장소 상태: 감사 시작 시 `bbccfd2`였으나 외부에서 `9a128c7`이 추가됐습니다. 현재 브랜치는 원격보다 1커밋 앞이며 작업트리는 깨끗합니다.

최종 중단 조건은 명확합니다. 원 제출물에는 `9a128c7`에 해당하는 플랫폼 독립 실패 사유 검사와 종료값 2 전용 사례가 없으므로 승인할 수 없습니다.
