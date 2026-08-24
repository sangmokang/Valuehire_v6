# Repository Data Protection — Codex V2 1차 판정

VERDICT: FAIL

## 실행 신원과 미확인

- 대상 SHA: `1c83438997d9c03554516fc5f26ab8a24286e970`
- 실행 시각: 2026-08-24 11:47 KST
- 독립 clone: `/tmp/valuehire-rdp-v2-1c834.3zmbrG`
- 검증기: 새 맥락 Codex `verifier` subagent
- 시작/종료 HEAD와 status: 동일, clean
- 실제 GitHub Actions runner는 실행하지 않고 로컬 CI 무결성·semantic mutation으로 대체했다.
- clone에는 top-level `AGENTS.md`와 `CLAUDE.md`가 없어서 주입된 AGENTS 지침과 저장소 SOT를 사용했다.
- 합성 fixture 값은 `[REDACTED]`로 취급하고 이 기록에 복사하지 않았다.

## 차단 결함

`scripts/scan-data-exposure.sh`의 당시 `collect_history_inventory`는 `git ls-tree`의 text 출력을 줄 단위 `awk`로 파싱했다. 줄바꿈 포함 경로는 Git이 인용한 문자열로 바뀌어 `.csv`로 끝나지 않는 것처럼 보였고 공용 PII 판정 호출에서 제외됐다.

| 독립 fixture | 기대 | 실제 |
|---|---:|---:|
| 정상 삭제 CSV, `history` | exit 1 | exit 1 |
| 줄바꿈 포함 삭제 CSV, `history` | exit 1 | exit 0, `PASS`, `CHECKED: 2` |
| 정상 삭제 CSV, `all` | exit 1 | exit 1 |
| 줄바꿈 포함 삭제 CSV, `all` | exit 1 | exit 0, `PASS`, `CHECKED: 4` |

따라서 AC-3와 AC-6, counter-AC 3·4·7·14는 FAIL이었다. V1의 “실행 가능한 계약 위반 없음” 주장도 이 SHA에서는 반박됐다.

## 원명령과 기존 주장 반박

원명령은 모두 exit 0이었다: principles 34, docs SOT, secret acceptance 35, data acceptance 46, verify 191, tracked 191, history 996, pii 191, all 1378, CI integrity 14, semantic mutations 10, `git diff --check`. 즉 당시 acceptance가 실제 결함을 감시하지 못한 거짓 초록이었다.

반면 빈 verify/tracked/history, Git 읽기 실패, 정상 경로의 삭제 CSV·TSV·SQL, 동일 blob 안전 확장자 alias, 정상 대조군, 현재/history 비출력, 공용 함수 공유, `CHECKED` 위조, history 호출 제거, 본문 출력 주입, CSV-only 약화, 1-column 임계값, acceptance 호출 제거, CI 비활성화 mutation은 모두 기존 방어로 막혔다.

## 조치 요구

history tree 경로를 NUL-safe로 열거하고 raw 경로로 확장자를 분류하며 안전하게 표시해야 한다. 줄바꿈·탭·인용 경로를 history/all acceptance로 고정한 뒤 V1과 새 맥락 V2를 다시 실행해야 한다.
