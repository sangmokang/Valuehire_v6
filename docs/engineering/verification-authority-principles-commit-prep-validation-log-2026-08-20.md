# 원칙 복구 커밋 후보 실행 장부 — 2026-08-20

## 결론

이번 복구 변경은 index로 선별됐고 로컬 기능 검사는 통과했다. 기존 사용자 자산과 직전 merge_group 제거 작업은 작업공간에 보존되어 있다. 현재 혼합 작업공간의 pre-push 실패와, HEAD+index 격리 clean snapshot의 pre-push 통과를 서로 다른 계약으로 기록한다.

## 범위와 상태

- 기준 HEAD: `858b96d510cf9e4da393b85446871448b4c1dfa6`
- branch: `task/verification-authority`
- 현재 미추적 총수: 45개
- 기존 사용자 자산: 42개, sorted-path SHA-256 manifest 결합 지문 `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`
- 직전 merge_group 제거 작업: 3개, 결합 지문 `c0fd0b78cf37ae7ac6f522891ac799dd051e3e4af93df6a3bb6b76d62a5cb293`
- 전체 미추적 45개 결합 지문: `c644f266205ed6c3b6542192be288579b64b0cfa9dedddd19ee5192108b278d6`
- 대상 저장소 commit, push, PR, merge, deploy, mail: 0건

42개 지문 계산 계약은 “현재 미추적 경로를 정렬하고 아래 3개를 제외한 뒤, 각 경로의 `shasum -a 256` 출력 줄을 manifest에 쓰고, 그 manifest 파일을 다시 `shasum -a 256`”이다. 파일 원문을 단순 이어붙이는 해시는 이 계약이 아니다.

직전 작업 3개는 다음과 같다.

- `docs/engineering/verification-authority-remove-merge-group-goal-2026-08-20.md`
- `scripts/verify/verification_authority/pr_evidence.rb`
- `scripts/verify/verification_authority/pr_line_limits.rb`

## 실행 결과

첫 선별 snapshot은 staged 22개, tree `b32a7973c769889862f1bb6784afc426acd2a5b4`였다. mutation 소스의 의도적 약화 카나리가 pre-commit P13에 오인된 문제를 실행 시 문자열 조립으로 고친 뒤 다음 결과를 얻었다.

```text
acceptance-principles-check        exit 0  CHECKED 32
acceptance-principles-mutations    exit 0  CHECKED 34 = 반례 29 + 대조군 5
check-mechanism-registry           exit 0  CHECKED 6
acceptance-verify-ac-m              exit 0  CHECKED 25
acceptance-verification-authority  exit 0
verify.sh                           exit 0
hooks/pre-commit                    exit 0
git diff --cached --check           exit 0
bash -n tracked shell scripts       exit 0
brief-lint 4 documents              exit 0  violations 0
```

→ 기능·경계·배선·문서 형식 검사가 모두 기대 종료값과 일치한다.

권위 장부는 이 파일 `docs/engineering/verification-authority-principles-commit-prep-validation-log-2026-08-20.md`다. 격리 실행은 `/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/va-commit-prep-v2.Ogd6EZ`에서 HEAD+index를 물질화하고 임시 검증 커밋으로 clean 상태만 만든 뒤 수행한다. `bash hooks/pre-push`의 `pre-push: 검사 21개 실행`과 21개 `ok` 원문은 그 경로의 `.validation-logs/pre_push.log`에 둔다. 이 임시 커밋은 대상 저장소의 branch·HEAD·원격을 바꾸지 않는다.

V2는 첫 snapshot 이후 V1 prompt와 verdict가 index에 추가돼 당시 snapshot과 후보가 같지 않다고 지적했다. 위 권위 격리 경로는 이 장부를 포함한 index로 갱신해 같은 전체 검사를 다시 실행하는 고정 검증 위치다. 최종 사용자 보고에는 그 staged tree와 종료값을 기록한다. 이 문서는 현재 혼합 작업공간이 clean하거나 지금 직접 pre-push가 통과한다고 주장하지 않는다.

## 현재 작업공간과 격리 snapshot의 계약

- 현재 작업공간: 사용자 미추적 45개와 unstaged 이전 변경이 있으므로 `bash hooks/pre-push`는 P15로 exit 1이 정상이다.
- 격리 snapshot: HEAD+index만 포함하고 clean 상태이므로 실제 커밋 후보의 pre-push 실행 증거로 사용한다.
- 두 결과를 섞어 현재 작업공간이 clean하다고 표현하면 FAIL이다.

## V1·V2 상태

- Claude V1 최초 완료 판정: FAIL. F1은 실행 장부 부재, F2는 45개 분할 계약 오해, F3는 mutation 숫자 문구 문제였다.
- G 조치: 이 장부 추가, 45=42+3 분리 고정, mutation 머리말을 반례 29+대조군 5로 정정했다.
- fresh Codex V2 최초 판정: FAIL. F2는 V1 과장, F3는 수정됨으로 뒤집었고, F1은 snapshot 시점 불일치가 남았다고 재현했다.
- 최종 상태: 고정 격리 snapshot과 V2 재검증은 PASS했고, Claude 최종 1턴 재판정도 `V1_VERDICT: PASS`로 종료됐다. 최초 실패와 두 번의 미완료 재시도는 V1 판정서에 보존한다.

## 되돌리기

이번 선별 경로만 index에서 내리면 작업공간 본문과 사용자 미추적 자산은 그대로 남는다. 실제 되돌리기는 사용자가 요청할 때만 한다.
