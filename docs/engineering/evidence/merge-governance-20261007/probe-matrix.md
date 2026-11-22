# 병합 규칙 격리 실험 원문 (2026-10-07 01:17~01:41 KST)

대상은 main 이 아닌 임시 브랜치 `probe/gate-20261007-*` 이다. 실험 후 브랜치 6개·ruleset 2개·환경 1개·배포 1건을 삭제하고 잔존 0을 확인했다(아래 마지막 절).
기준 커밋: 모든 임시 base 는 당시 main `55240f77ff52bb240ab1205e46ad2567c7f0b7ae` 에서 출발.

| 표본 | 커밋 | 내용 |
|---|---|---|
| green | 16ff748 | 문서 1줄 추가 (정상) |
| red | 09cc35b | `scripts/gate-probe-red-20261007.sh` 에 `if then fi` (셸 문법 오류 → verify 실패) |
| solo | 891e5b6 | PR 에 속하지 않은 문서 커밋 |
| behind | 582e4b2 | main 옛 기준에서 딴 정상 커밋 |

## 1. 기존 규칙 복제(`required_deployments: [acceptance]`, ruleset 24593112)

| 시험 | 명령 | 결과 원문 |
|---|---|---|
| A-1 정상 PR #125 병합(gh) | `gh pr merge 125 --merge` | `X Pull request ...#125 is not mergeable: the base branch policy prohibits the merge.` rc=1 |
| A-2 정상 PR #125 병합(서버 API) | `gh api -X PUT .../pulls/125/merge` | `Repository rule violations found  Missing successful active acceptance deployment.` HTTP 405 |
| B-1 같은 설정의 임시 환경 `probe-acc-20261007`(지정 승인자 + 자기승인 금지 + 보호 브랜치만 배포)으로 규칙 전환 후 병합 | 같은 API | `Missing successful active probe-acc-20261007 deployment.` HTTP 405 |
| B-2 API 로 배포 기록 생성 + 상태 success | `POST /deployments ref=16ff748 environment=probe-acc-20261007` → id 6889283005, `POST /deployments/6889283005/statuses state=success` | `success` — workflow 실행 0, 승인자 승인 0, 보호되지 않은 브랜치 |
| B-3 위조 직후 병합 | `gh api -X PUT .../pulls/125/merge` | `{"sha":"2a8523f...","merged":true,"message":"Pull Request successfully merged"}` |

→ 기존 규칙은 정직한 PR 을 영구히 막고(A), write 권한이 있으면 명령 두 줄로 통과된다(B). 보증 가치 0.

## 2. 새 규칙(`pull_request(승인 0)` + `required_status_checks[verify, integration 15368]`, ruleset 24593113)

| 시험 | 결과 원문 |
|---|---|
| POS-1 정상 PR #126 CI | verify 3건 SUCCESS → `mergeStateStatus: CLEAN` |
| NEG-1 실패 PR #127 병합 | `Required status check "verify" is failing.` HTTP 405 |
| (설계 오류) green 커밋으로 base ref 직접 갱신 | 통과. rule-suite 4390134370: `pull_request=pass` — green 은 열린 PR #126 의 head 이고 검사 통과 → GitHub 은 그 PR 의 로컬 병합으로 취급(#126 MERGED 로 자동 전환). 우회 아님 |
| NEG-2a PR 없는 새 커밋(검사 전) 직접 push | `Changes must be made through a pull request.  Required status check "verify" is expected.` HTTP 422 |
| NEG-2b 같은 커밋, verify 완료 후 직접 push | `Changes must be made through a pull request.` HTTP 422 |

## 3. strict(`strict_required_status_checks_policy: true`) 추가

| 시험 | 결과 원문 |
|---|---|
| STRICT-NEG 뒤처진 정상 PR #128 (verify 2건 SUCCESS, `BEHIND`) 병합 | `Required status check "verify" is expected.` HTTP 405 |
| STRICT-POS `gh pr update-branch 128` → 새 head 7fb79c5 verify 2건 SUCCESS → `CLEAN` → 병합 | `{"sha":"ff6d0ee...","merged":true}` |

## 4. 실제 main 적용 후(ruleset 23568184 → `main-pr-verify-gate`, 2026-10-06T16:39:27Z)

| PR | 상태 | 서버 판정 |
|---|---|---|
| #122, #123 (CI 초록·main 최신) | `CLEAN` | — (병합은 사람 몫, 시도하지 않음) |
| #116 (CI 실패) | `BEHIND` | 병합 시도 → `Required status check "verify" is expected.` 405 |
| #85 (9월 초록·main 보다 뒤처짐) | `BEHIND` | 병합 시도 → 같은 메시지 405 |
| #74 (충돌) | `DIRTY` | — |

## 5. 10-02 #111 병합과의 충돌 해소

- `gh api repos/:o/:r/rulesets/rule-suites?ref=refs/heads/main&time_period=month` → main 판정 기록은 `2026-10-02T22:26 cursor[bot] 55240f7→d3f45ae fail (Missing successful active acceptance deployment.)` 1건뿐.
- 같은 기간의 직접 push 2건(09-25 fc6beed→f1f7a01, 09-28 f1f7a01→f764a41)과 #111 병합(10-02 01:36Z, `gh pr merge 111 --squash`, `--admin` 없음)은 판정 기록 자체가 없다.
- 결론: 그 세 건은 규칙이 **평가되지 않은** 채 통과했다. 왜 평가되지 않았는지는 미확정(UNRESOLVED). ruleset 버전 기록은 09-17 1건뿐이라 설정 변경 때문은 아니다.

## 6. 정리 후 잔존 확인

```
rulesets: 23568184 main-pr-verify-gate active
environments: acceptance
deployments: 0
refs/heads/probe/*: 0
```
