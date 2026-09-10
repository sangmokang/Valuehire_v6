# HS-00.03 로컬 구현 완료 증거

## 결론

보호 스텝 이름·정본 스텝 이름 칸·처분 대상 칸에서 전각 또는 닮은꼴 문자로 보호 이름을 위장한 입력은 이제 실패한다. 정상 한글·다국어 이름과 기존 이름 경계는 통과하며, 빈 입력과 깨진 입력·매핑 데이터 오류는 오류로 닫힌다.

현재 상태는 로컬 검증 완료 후 커밋 대기다. 원격 전송·PR·병합·운영 쓰기는 이번 작업에 포함하지 않는다.

## 판단 근거

- 원문은 승인 값으로 바꾸지 않고 탐지용 비교 사본만 만든다.
- U+FF01부터 U+FF5E까지의 전각 ASCII와 Unicode 17.0.0의 단일 비ASCII 문자에서 단일 보호 ASCII 문자로 가는 고정 매핑만 지원한다.
- 보호 토큰 안의 치환과 토큰 양옆에서 ASCII 식별 경계로 바뀌는 치환을 모두 거부한다.
- 정상 `PR #131`, `ＰR #131`, `hs-kickoff-other`, `hｓ-kickoff-other`와 한글·일본어·아랍어·라틴 이름은 허용한다.
- 0바이트, 빈 문자열 한 줄, 공백뿐인 이름 한 줄, 해독할 수 없는 UTF-8은 종료값 2다.
- 결합 문자, 양방향 문자, 보이지 않는 문자, 다중문자 skeleton 전체는 지원 범위가 아니다.

## RED와 독립 시험 검토

| 단계 | 커밋 | 재현 | 독립 검토 |
|---|---|---|---|
| 계약 | `39cc8df54b0095ec85931a547c7dac68188feddc` | WU·EARS·counter-AC·입출력·문자 경계 고정 | 계약 자체 |
| 최초 RED | `396cd2b7e92f755d65c34cf103d07b8741259cfc` | 14 failed, 1 passed | `initial-red-independent-review.md`, SHA `db781f88ef4dd49a5774a956c2eaee7b2fb774397017562dbb63d5be4139aaf7` |
| 경계·입력 RED | `d1058cadb764056c4f52696ea0321038c660a12c` | 5 failed, 16 passed | `boundary-red-independent-review.md`, SHA `d686d21d230849015a7d8d11e0c070c772410fabdec724ac0375f359e4946aa0` |
| 공백·동시 존재 RED | `e99b4549ddf617d0d79acdd63880438cfbf9a7c8` | 1 failed, 22 passed | `claude-followup-red-independent-review.md`, SHA `bfb11c6d719825624d6fb97ccaeb475c6604c5d606553214c9032b4396cac4b1` |

→ 새 제품 동작을 넣기 전에 실패를 세 번 나눠 고정했다. 독립 검토자는 시험 파일과 실제 실패 원인을 확인했고 제품 파일을 수정하지 않았다.

## GREEN 검증

```text
HS-00.03 target: 23 passed
targeted HS-00.01~03: 74 passed
G2: ruff 46 files, mypy 46 source files, pytest collected 285 and passed
kickoff mutations: CHECKED 37
principles: CHECKED 34, VERDICT PASS
principle mutations: CHECKED 41, VERDICT PASS
verify.sh: no tracked secret-pattern match, .env not tracked
budget: authored files <= hard600, Python functions <= hard100
budget boundaries: 600 pass, 601 fail, zero target fail
adversarial: baseline 23 passed, mutants killed 11/11, workspace untouched
```

→ 정상·경계·입력·데이터·shell 배선을 포함한 현재 후보가 통과했다. 항상 허용·항상 거부와 핵심 효과 열한 가지 제거 사본은 각각 최소 한 시험에 잡혔다.

## 후보 지문

```text
manifest: docs/engineering/evidence/hs0003-20260910/candidate-product-manifest.json
manifest sha256: c466946aad003159a07c052979e8e0034ec4eeb0d3445d5a9ccb7952a6b7e6d4
bundle sha256: 9517376e3755a69e4e9dfca8ac5ad859654cbb94dda8cd3b610075c61b40e23d
algorithm: listed path UTF-8 + NUL + raw bytes + NUL
```

→ 제품·시험·정본 9개 파일을 파일별 SHA와 byte 수로 고정했다. 최종 감사와 커밋 후 재읽기는 이 manifest와 같은 후보만 합격으로 센다.

## Unicode 데이터

| 항목 | 값 |
|---|---|
| 공식 버전 | Unicode 17.0.0 |
| 원본 | `https://www.unicode.org/Public/17.0.0/security/confusables.txt` |
| 원본 SHA-256 | `091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a` |
| 선택 수 | 628 |
| 생성물 SHA-256 | `687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd` |
| 라이선스 | Unicode License v3 |
| 라이선스 SHA-256 | `e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96` |

→ 고정 원본을 생성기에 다시 넣은 결과가 커밋 후보 JSON과 byte 단위로 같았다. 버전·원본 지문·선택 계약이 다르면 생성기와 실행 helper가 실패한다.

## 독립 감사

- 최종 Codeaudit: `codeaudit-final-v2-verdict.md`, PASS, SHA `5edbe04b586b0617ea0df41b1033557bd079bad3600d693eb001c168c27f35d2`, brief-lint 0건.
- 실제 Claude V1: Claude Code 2.1.267, 모델 `claude-fable-5-1`, 세션 `ab9f164b-5474-4a48-a7af-88c473281083`, PASS.
- 실제 실행 프롬프트 원문 보관본: `claude-v1-final-v2-prompt-raw.json`, 내부 원문 SHA `2047a051e773203bbeb151f66fab7ca7c6cc24cfcc33680a576c2be73c1c3825`.
- Claude 원문: `claude-v1-final-v2-response.md`, SHA `333c99b849696eeda3ebf3996e25207ad17cc96c3bf07ccf0328b884276748f2`.
- 같은 세션 형식 보정본: `claude-v1-final-v2-response-final.md`, SHA `2465850b642de964b598ea0147501eaa0b686deb4bfa531281873216b4e7967e`, brief-lint 0건.
- Claude 실행 메타: `claude-v1-final-v2-meta.json`, SHA `57e322b8c284a2a6be3dfa9a9cebf2a2e4149204e7148a56c431d270be6d65f4`.
- 새 Codex V2 원문: `codex-v2-final-verdict.md`, PASS, SHA `1f04cf9cc10d11dc14014f7715acf2e6e53257d13bc9a1c9846b830a777860b7`.
- Codex V2 형식 보정본: `codex-v2-final-verdict-final.md`, SHA `f4a44554252a3c0b1b706bf20e40e340f6713d0557baf6897914aa3a9423cc93`, brief-lint 0건.

→ Codeaudit, 실제 Claude V1, 새 Codex V2가 같은 manifest를 재계산하고 직접 시험한 뒤 PASS했다. Claude가 남긴 낮은 위험은 한 경로의 오류 처리만 약화한 사본과 SHA 뒤의 중복 방어 제거 사본이 시험에 살아남는다는 시험 강도 한계이며, 현재 제품의 fail-closed 결과는 유지된다. Codex V2는 helper 입력 16개, 실제 shell 변조 3개, 대표 고장 사본 4개를 추가로 확인했다.

## 실패·복구 이력

- 새 작업트리의 첫 pytest는 가상환경이 없어 시작하지 못했다. `uv sync --locked --offline`으로 잠금 파일 그대로 복구한 뒤 같은 명령을 통과시켰다.
- `omx explore`는 Rust 실행기 부재로 실패해 현재 파일 직접 조회와 native subagent 검토로 전환했다.
- 제품 소유권 밖 하위 에이전트가 만든 중복 커밋 `9747881507e6de319109bcf35cc359f7ad1fedec`은 후보에서 제외했다. 현재 브랜치는 HS-00.02 완료 SHA에서 계약과 RED를 순서대로 다시 만들었다.
- 첫 Codeaudit·Claude V1 PASS 뒤 새 Codex V2가 경계와 입력 반례를 찾아 FAIL했다. 해당 반례를 두 번째 RED로 고정하고 수정했다.
- 보강 후보의 실제 Claude V1은 PASS하면서 공백-only 입력과 같은 줄 첫 정상 토큰 뒤 탐색의 시험 공백을 찾았다. 세 번째 RED와 독립 검토 뒤 최소 수정했으며, 적대 사본 11/11로 다시 확인했다.
- 프로젝트 디렉터리에서 시작한 Claude 사전 시도 두 번은 SessionStart 훅이 전체 acceptance를 실행해 각 10분 뒤 중단됐다. `/tmp`에서 시작한 실제 세션으로 검증을 완료했으며 실패 시도는 PASS로 세지 않았다.

## 남은 제한과 전달 상태

- HS-00.02의 기존 37종 고장 사본 중 6종 생존 기록은 이전 작업의 시험 강도 한계로 남아 있다. 이번 HS-00.03의 기존 기대 37종 통과와 혼동하지 않는다.
- 과거 인증 값 노출 사고는 OPEN이다. 현재 키 유효성과 교체 여부는 확인하지 않았고 값도 조회하거나 기록하지 않았다.
- HS-00.01·02 증거를 포함한 main 대비 누적 diff가 PR 3,000줄 한도를 넘는 전달 문제가 남아 있다. 이번 작업을 원격 배송 완료로 주장하지 않는다.
- 원격 CI, push, Issue/PR 작성, 병합, 실제 포털·메시지·운영 저장소 쓰기, 키 교체는 `NOT_RUN` 또는 `NOT_APPLICABLE`이다.
- 결합 문자, bidi, default-ignorable·보이지 않는 문자, 다중문자 매핑과 전체 UTS #39 준수는 이 WU의 해결 범위가 아니다.
- `scripts/acceptance-hs-kickoff-mutations.sh`는 595줄로 hard600까지 5줄 남았다.
