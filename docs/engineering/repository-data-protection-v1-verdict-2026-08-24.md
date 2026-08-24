# Repository Data Protection — Claude V1 최종 판정

VERDICT: PASS

## 실행 신원

- 대상 SHA: `b979c5be8419af07fb8b4d982cb34badc77bdcfc`
- 실행 시각: 2026-08-24 11:36 KST
- 독립 clone: `/tmp/valuehire-rdp-v1-b979.TOKH81`
- 검증기: Claude Code 2.1.239, Sonnet, high effort, safe-mode, session persistence off
- 코드 훼손 위치: 별도 `/tmp/rdp-v1-attack*` mirror만 사용
- 시작/종료 HEAD: 동일
- 시작/종료 소스 상태: 동일. 선행 `$ask-claude` 실패가 만든 untracked `.omx` artifact 한 건만 양쪽에 존재했다.

## 선행 NOT_RUN

정본 `$ask-claude` 경로인 `omx ask claude`의 첫 호출은 구현을 읽기 전에 `Credit balance is too low`로 exit 1이었다. 이 호출은 V1 증거로 세지 않았다. 같은 로컬 Claude CLI에서 `ANTHROPIC_API_KEY`만 해제한 기존 인증 경로로 재실행해 아래 판정을 얻었다.

## 필수 원명령

| 명령 | 안전한 결과 | 종료값 |
|---|---:|---:|
| `bash scripts/acceptance-principles-check.sh` | `VERDICT: PASS`, `CHECKED: 34` | 0 |
| `bash scripts/check-docs-sot.sh` | `OK` | 0 |
| `bash scripts/acceptance-secret-webhook-vendor.sh` | `CHECKED: 35` | 0 |
| `bash scripts/acceptance-hs-a4.sh` | `CHECKED: 46` | 0 |
| `bash verify.sh` | `PASS`, `CHECKED: 190` | 0 |
| `bash scripts/scan-data-exposure.sh tracked` | `PASS`, `CHECKED: 190` | 0 |
| `bash scripts/scan-data-exposure.sh history` | `PASS`, `CHECKED: 994` | 0 |
| `bash scripts/scan-data-exposure.sh pii` | `PASS`, `CHECKED: 190` | 0 |
| `bash scripts/scan-data-exposure.sh all` | `PASS`, `CHECKED: 1374` | 0 |
| `bash scripts/acceptance-ci-step-integrity.sh` | `VERDICT: PASS`, `CHECKED: 14` | 0 |
| `bash scripts/acceptance-semantic-mutations.sh` | `VERDICT: PASS`, `CHECKED: 10` | 0 |
| `git diff --check` | 출력 없음 | 0 |

CHECKED의 절대값은 독립 clone이 가진 refs/reflogs에 따라 달라질 수 있다. 계약은 실제 양수와 완전 읽기, 올바른 종료값이다.

## 독립 공격과 반증

| 공격 | 실행 결과 |
|---|---|
| data tracked zero-target 가드 제거 | data acceptance가 빈 tracked 계약 불일치로 exit 1 |
| data `CHECKED`를 상수 1로 위조 | 빈 tracked/history, 실제 blob 2개, Git 실패 사례가 함께 exit 1 |
| history 공용 PII 호출 제거 | 삭제 CSV·TSV·SQL과 alias 2건 및 공유 구조 검사가 exit 1 |
| 공용 PII 위반 경로에 본문 출력 주입 | 현재 3건, history 3건, alias 2건의 비출력 검사가 exit 1 |
| Git rev-list 실패를 성공으로 접기 | 후속 완전 읽기 방어가 NOT_RUN을 유지해 우회 실패 |
| PII 컬럼 임계값 2에서 1로 완화 | 현재/history 1-column 정상 대조군이 exit 1 |
| 함수 상한 100을 999로 완화 | 합성 101줄 함수 경계가 exit 1 |
| verify zero-target 가드 제거 | 빈 Git 저장소에서 훼손본의 거짓 PASS를 secret acceptance가 exit 1로 탐지 |
| 자체 alias fixture: 같은 blob을 `leads.csv`와 후행 `archive.dat`로 커밋 후 삭제 | 무훼손 history/all이 안전한 경로·blob·컬럼 수 메타데이터만 출력하고 각각 exit 1 |
| 무훼손 빈 history/tracked 및 깨진 ref | 각각 `NOT_RUN`, `CHECKED: 0`, exit 2 |

합성 fixture의 이름·이메일·전화번호 값은 이 기록에 복사하지 않았다. Claude 최종 출력도 `[가림]`으로 표시했고, 실제 후보자 데이터는 읽거나 만들지 않았다.

## 미확인과 경계

- 실제 GitHub Actions 러너 실행은 관측하지 않았다. 워크플로 정적 배선과 로컬 CI 무결성·semantic mutation으로 대체했다.
- 프롬프트 최소 목록 밖의 다른 CI acceptance 전체는 실행하지 않았다.
- 로컬 CLI 원응답 3,502 token 중 도구 회수 상한을 넘은 중간 일부가 terminal capture에서 생략됐다. 판정, 명령 표, 각 공격의 결론, alias 원문, 데이터 안전과 미확인 항목은 회수됐으며 위 표는 그 안전한 내용만 보존한다.

## 결론

실행 가능한 계약 위반이나 남은 V1 주장은 발견되지 않았다. 이전 세 회차에서 수용한 모든 주장은 현재 acceptance가 고장 사본에서 실패하도록 고정했고, 동일 blob 안전 확장자 alias 반례도 무훼손 history/all에서 차단된다.
