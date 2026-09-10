# HS-00.04 Claude V1 최종 판정

- 실행 주체: 로컬 Claude CLI 로그인 세션 (`env -u ANTHROPIC_API_KEY claude -p ...`).
- 실행 세션: Codex PTY `91192`.
- 대상: HEAD `c7c6332bc6debab5b83090ae0230f1de74b7f724` + 미커밋 GREEN 후보.
- 검토 당시 4파일 diff SHA-256: `74fe789fb261e3bde20262695be9fb1f784ad48aac6daf9334bcb6419738f8ea`.
- 종료: CLI exit 0, 최종 출력 첫 줄 `VERDICT: PASS`.

아래는 CLI 최종 출력 원문이다.

---

VERDICT: PASS

## 결론

현재 GREEN 후보(검사기 `2f48e44f…`, SOT `d245e8d3…`, 누적 diff `74fe789f…` 모두 제시값과 일치)는 Spec 안에서 재현 가능한 HIGH/MEDIUM 결함이 없습니다. canonical은 제 환경에서 `CHECKED: 105 / VERDICT: PASS / rc=0`으로 재현됐고, HEAD `c7c6332`의 커밋된 검사기(RED 상태)로는 같은 acceptance가 91건 FAIL로 빨갛게 나와 RED→GREEN 사슬이 닫힙니다. 독립 반례 55건과 검사기 변조 20건에서 항상 허용·항상 거부·데이터 오류 접힘·과잉 차단은 발견되지 않았습니다. 발견한 것은 전부 LOW이거나 이번 WU 이전부터 있던 범위 밖 사항입니다. 검사 중 저장소 파일 쓰기와 원격 쓰기는 하지 않았고, 종료 시 `git status`·HEAD·4파일 해시가 시작 시와 동일합니다.

## 재현 명령·종료값·핵심 출력

| 항목 | 명령 | 종료값 | 핵심 출력 |
|---|---|---|---|
| canonical | `bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh` | 0 | `CHECKED: 105`, `VERDICT: PASS`, `OK(run-acceptance): 판정 106건` |
| RED 실증 | HEAD `c7c6332`를 `git archive`로 격리 사본에 풀고 같은 명령 | 1 | `VERDICT: FAIL`, FAIL 91건(trigger 관련 전량 exit 0으로 통과됨) |
| 원칙 검사 | `bash scripts/acceptance-principles-check.sh` | 0 | `WIRING: PASS pre-push=1 ci=1`, `CHECKED: 34` |
| 독립 반례 | 임시 디렉터리에 YAML 55건 생성 후 검사기 직접 호출 | 기대값과 일치 53건 | 아래 발견사항 참고. Ruby 스택트레이스 0건 |
| 검사기 변조 | GREEN 검사기 사본에 변이 20종 주입 후 acceptance | 17건 `VERDICT: FAIL` | 생존 3건은 등가 변이(아래) |
| 배선 | `.github/workflows/verify.yml:227-232` | 정적 확인 | 스텝 23 → `run-acceptance.sh` → acceptance → 검사기. SOT 표 23행과 일치 |

독립 반례에서 확인한 계약별 결과는 다음과 같습니다.

- **계약 1(축소 exit 1)**: scalar `on: push`, `branches: ["main","**"]`, `tags`, PR 기본 `types` 명시, `push: []`, `paths: []`, `branches: "**"` scalar, 키릴 문자 `pusһ`, `Push` 대문자, `on: {}`, `on: ""`, 시퀀스 누락 모두 exit 1 + `TRIGGER_CONTRACT` + `CHECKED: 3`.
- **계약 2(정상 허용)**: `!!str on`, quoted `on`, 시퀀스 + 추가 event, block 스타일 `branches`, anchor만 있고 alias 없는 `on`, key에 anchor, `push: !!null ""`, `%YAML 1.1` 지시자, `---` 문서 시작, CRLF, BOM, `pull_request_target` 추가, 값 위치의 `yes`/`on` 모두 exit 0.
- **계약 3(구조 오류 exit 2 + CHECKED 0)**: `on: ~`, `on: 7`, `on: *alias`, 시퀀스 안 mapping, quoted/plain 중복 event, `!!bool "on"`, `On`만 존재, `!!binary b24=`만 존재, 빈 파일, 2문서, UTF-16, 잘못된 UTF-8, NUL 바이트, 시퀀스 내부 mapping 중복, complex key, 심볼 key, plain 날짜 key, 60진수 key, `on` 아래 `on` key, `!!str on` + plain `on`, `!!bool 1` 충돌, step quoted 중복 `run`, job `<<`, `jobs: {true: …}`, `jobs: *alias`, 디렉터리 입력 모두 기대대로.
- **계약 4(문자열 key 허용)**: quoted `"7"`, `!!str true`, quoted `"2026-01-01"` inputs key 모두 exit 0.
- **계약 5(원본 불변)**: acceptance 자체 스냅샷 판정 PASS이며 제 최종 대조에서도 동일.

변조 생존 3건은 다음과 같습니다. m18(`on` 값 계층 문자열 key 검사 제거)과 m19(`jobs` 값 계층 문자열 key 검사 제거)는 AST 계층이 같은 입력을 먼저 exit 2로 막아 종료값이 바뀌지 않는 중복 방어입니다. m20(scalar `on`을 `{}`로 취급)은 메시지만 바뀌고 exit 1은 유지됩니다. 커버리지 부족이 아니라 등가 변이로 판단하지만, 독립 방어선으로 설계했다면 그 사실을 주석에 남기는 편이 좋습니다.

## 발견사항

1. **LOW, 사전 존재, 범위 밖 · Ruby 인라인 스크립트가 C 로케일에서 컴파일 실패.** `LC_ALL=C`로 canonical을 돌리면 검사기가 모든 입력에서 `-e:246: invalid multibyte char (US-ASCII)`로 exit 1이 되어 acceptance 전체가 FAIL입니다. 선행 커밋 `c28270c`의 검사기도 같은 위치 유형(`-e:78`)에서 동일하게 깨지므로 이번 WU가 만든 것이 아닙니다. 실패 방향은 fail-closed(빨간불)라 우회가 아닙니다. `LANG=C.UTF-8`에서는 105건 PASS입니다. 처방은 `-e` 스크립트 첫 줄에 `# encoding: utf-8` 매직 코멘트를 넣는 것이며 로컬에서 동작을 확인했습니다. 같은 노출 패턴을 가진 스크립트가 8개 더 있습니다.
2. **LOW, 문서 · 결정 카드의 "이미 CI와 pre-push에 배선된" 서술은 절반만 사실.** `hooks/pre-push`와 `verify.sh`에는 `ci-step-integrity` 호출이 0건입니다. 배선은 CI 스텝 23 하나입니다. 계약 자체는 CI 단일 배선을 전제로 하므로 판정에는 영향이 없습니다.
3. **LOW, 과잉 차단(입력 형식) · `%YAML 1.2` 지시자는 libyaml이 "incompatible YAML document"로 거부**해 exit 2입니다. GitHub 파서와 해석이 다를 수 있으나 현재 verify.yml에 지시자가 없고 실패 방향이 닫혀 있습니다.
4. **LOW, 과잉 차단(의미) · `branches: ["main","**"]`처럼 전체 브랜치를 포함하는 다른 표기와 scalar `branches: "**"`는 exit 1.** Spec이 "현재 의미"의 정확한 형태 고정을 택했으므로 계약 위반은 아닙니다.
5. **관찰 · GREEN 검사기와 SOT는 아직 미커밋 상태.** HEAD에는 Spec과 RED만 있고 검사기 195줄 변경은 작업트리에만 있습니다. 이 판정은 위 파일 해시에 귀속되며, 커밋 후 지문이 바뀌면 만료됩니다. 또한 goal 문서의 "적대 검증 로그" 절이 "아직 구현 전이다"로 남아 있고 evidence 디렉터리에는 프롬프트 파일 1개만 있습니다.

제시된 결과 중 제가 직접 재검증하지 않은 항목은 NOT_RUN입니다: targeted regression 74건, G2(Ruff/mypy/pytest 285), mutation group 105/16/41/37, 고장 사본 14/14, Codeaudit, 별도 적대 반례 16/16, 코드 예산 600/601 경계 실증. 이번 WU가 Python을 건드리지 않아 G2 결과가 바뀔 이유는 없으나 증거로 세지 않았습니다.

## 남은 범위 밖 위험

- **`ALLOWED_STEP_IF` 이름 재사용 구멍(HS-00.04 이전부터 존재).** 임의 스텝 이름을 "인수 검사 0-5 (push · CI 연결)"로 바꾸고 `if: ${{ false }}`를 붙이면 `ALLOWED`로 통과합니다(exit 0, `CHECKED: 33` 실측). 스텝 조건 계약이라 trigger WU 밖이지만 별도 WU 가치가 있습니다.
- **Ruby `base64` 의존.** Ruby 3.4부터 `base64`는 bundled gem이라 배포판 패키징에 따라 `-rbase64`가 LoadError를 낼 수 있습니다. 실패 방향은 닫혀 있습니다. `"b24=".unpack1("m")`로 대체하면 의존이 사라집니다(로컬 확인). 원격 러너의 Ruby 버전과 `LANG` 값은 NOT_RUN입니다.
- **원격 CI·PR·merge·branch protection**은 이번 범위 밖이며 확인하지 않았습니다.
