# Repository Data Protection — Claude V1 최종 재검증

VERDICT: PASS

## 실행 신원과 미확인

- 대상 SHA: `ae4fba1ffe905720c1ecc41259d97b5d4449c4d5`
- 종료 시각: 2026-08-24 12:00:56 KST
- 독립 clone: `/tmp/valuehire-rdp-v1-final.RI49kD` (`git clone --no-local`)
- 검증기: Claude Code 2.1.239, Sonnet, high effort, safe-mode
- 시작/종료 HEAD와 status: 동일, clean
- 실제 GitHub Actions runner는 실행하지 않고 로컬 CI 무결성 acceptance로 대체했다.
- history/all blob 수는 task branch만 받은 독립 clone의 refs/reflogs 범위에 따라 작업 clone보다 작다.
- Claude 원응답은 합성 canary 식별자를 한 번 복사해 raw로 저장하지 않았다. 아래 기록은 모두 `[REDACTED]` 원칙으로 안전하게 재작성했으며 실제 후보자 데이터는 사용되지 않았다.

## 필수 원명령

| 명령 | 결과 | 종료값 |
|---|---:|---:|
| `bash scripts/acceptance-principles-check.sh` | `VERDICT: PASS`, `CHECKED: 34` | 0 |
| `bash scripts/check-docs-sot.sh` | `OK` | 0 |
| `bash scripts/acceptance-secret-webhook-vendor.sh` | `CHECKED: 35` | 0 |
| `bash scripts/acceptance-hs-a4.sh` | `CHECKED: 48` | 0 |
| `bash verify.sh` | `PASS`, `CHECKED: 192` | 0 |
| `bash scripts/scan-data-exposure.sh tracked` | `PASS`, `CHECKED: 192` | 0 |
| `bash scripts/scan-data-exposure.sh history` | `PASS`, `CHECKED: 332`, 73.07초 | 0 |
| `bash scripts/scan-data-exposure.sh pii` | `PASS`, `CHECKED: 192` | 0 |
| `bash scripts/scan-data-exposure.sh all` | `PASS`, `CHECKED: 716`, 74.42초 | 0 |
| `bash scripts/acceptance-ci-step-integrity.sh` | `VERDICT: PASS`, `CHECKED: 14` | 0 |
| `bash scripts/acceptance-semantic-mutations.sh` | `VERDICT: PASS`, `CHECKED: 10` | 0 |
| `git diff --check` | 출력 없음 | 0 |

## acceptance 밖 독립 fixture

| 공격 | 결과 |
|---|---|
| 빈 Git 저장소의 verify | `NOT_RUN`, `CHECKED: 0`, exit 2 |
| 안전 파일 한 개 verify | `PASS`, `CHECKED: 1`, exit 0 |
| 삭제 CSV·TSV·SQL PII와 정상 지표 CSV·schema-only SQL | PII 세 형식만 안전 메타데이터로 탐지, history/all exit 1, 정상 대조군 오탐 0 |
| 동일 blob의 `candidates.csv`와 `backup.dat` alias | 대표 경로가 안전 확장자여도 CSV를 탐지, 고유 blob 수 유지, exit 1 |
| 탭·따옴표·줄바꿈을 함께 가진 삭제 CSV 경로 | history/all exit 1, 출력 raw 탭 0개, 실제 줄 수 이외 raw 개행 0개, 합성 본문 값 0건 |

복합 경로는 `$'...\t...\n.csv'` 형태의 shell-escaped 한 줄 메타데이터로만 출력됐다. raw 경로로 확장자를 분류하고 표시 단계에서만 이스케이프하는 순서가 유지됐다.

## mutation mirror 8종

| mutation | 감시 결과 |
|---|---|
| `git ls-tree -rz`와 NUL read를 text/line read로 약화 | 복합 경로 history/all 두 사례 FAIL, acceptance exit 1 |
| raw 경로 대신 escaped 표시 문자열로 확장자 분류 | 복합 경로 두 사례 FAIL, exit 1 |
| history용 PII 함수 복제·연결 | 공유 구조 계약 FAIL, exit 1 |
| data tracked zero-target 가드 제거 | 빈 tracked 계약 FAIL, exit 1 |
| verify `CHECKED`를 상수 1로 위조 | 안전 blob 2개 대조 FAIL, exit 1 |
| 개인정보 위반 시 본문 출력 주입 | 현재/history/alias/복합 경로 비출력 10건 FAIL, exit 1 |
| 복합 경로 history/all acceptance 호출 제거 | 실제 46건과 계약 48건 불일치, exit 1 |
| 함수 상한 100을 999로 완화 | 100/101 경계 FAIL, exit 1 |

## AC와 counter-AC

AC-1부터 AC-6까지 PASS다. 추가 Strict 경계인 600/601 파일, 100/101 함수, 데이터 안전도 PASS다. counter-AC 1~14는 독립 fixture, mutation, exact count, SOT 대조로 반박됐다. 문서만 낮추는 mutation 자체는 만들지 않았지만 SOT의 NUL/raw-path/safe-display 선언과 코드·acceptance가 일치하고 `check-docs-sot.sh`가 통과했다.

## 결론

재현 가능한 계약 위반, 증거 공백, 개인정보 원문 노출은 발견하지 못했다. 남은 비차단 지적은 commit마다 `git ls-tree`를 실행해 독립 clone history/all이 약 73~74초 걸린다는 선형 성능 비용이다.
