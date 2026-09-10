# HS-00.04 최종 후보 Claude V1 독립 적대검증 요청

첫 줄을 `VERDICT: PASS` 또는 `VERDICT: FAIL`로 쓰십시오. 저장소를 수정하지 말고 읽기 전용으로 직접 재현하십시오.

## 대상과 범위

- 작업공간: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0004-recovery-20260910`
- 현재 HEAD: `c7c6332bc6debab5b83090ae0230f1de74b7f724`
- 선행 완료: `c28270c1ea6153d4ea0aae83a8562981b2564269`
- Spec: `docs/engineering/humansearch-hs0004-goal-2026-09-10.md`
- RED: `scripts/acceptance-ci-step-integrity.sh`
- GREEN 후보: `scripts/verify/check-ci-step-integrity.sh`
- 정본 배선: `docs/sot/verification-commands.md`
- 제품 4파일 누적 diff SHA-256: `74fe789fb261e3bde20262695be9fb1f784ad48aac6daf9334bcb6419738f8ea`
- 파일 SHA-256: goal `caa80d6024423e3bdb009406ede9e076dae20347af9d7d4e3e77f4a3010501ba`, acceptance `a179b235ace39c21a5ab08f5092207383edb0fc32a929dc9d083fc82a39dc906`, checker `2f48e44fb67def7832505b80d037c4a7217b946aea10b0fcf9df860eb8bba2fd`, SOT `d245e8d3ce89e0737781959c23bd6dc8d97b0a79f7c2b7b5ea14e5528e1559a8`.

이번 WU는 정확히 HS-00.04 하나입니다. GitHub Actions 전체 schema allowlist, 저장소 설정, concurrency/timeout, HS-00.05, 원격 CI/push/PR/merge는 제외합니다. 알 수 없는 추가 event는 필수 세 event가 유지되면 허용합니다.

## 반드시 공격할 계약

1. 모든 branch push, filter 없는 기본 pull_request, workflow_dispatch가 모두 있어야 하며 축소는 exit 1입니다.
2. plain/quoted/tagged `on` 정상 표현과 scalar/sequence shorthand, UTF-8 BOM을 과잉 차단하지 않아야 합니다.
3. top-level YAML 1.1 boolean-slot과 명시적 `!!bool`/`!!binary b24=` semantic `on` 충돌, `!!bool on`, `on` 하위 모든 alias와 모든 mapping의 duplicate/inline merge/implicit·explicit non-string key(`!!bool`/`!!int`/`!!null` 포함), duplicate/nonmapping jobs·steps는 exit 2와 `CHECKED: 0`이어야 합니다.
4. nested quoted numeric key와 explicit string-tag boolean-looking key는 문자열이므로 허용되어야 합니다.
5. 정상 입력과 모든 반례에서 원본 worktree가 바뀌지 않아야 합니다.

## 제공 결과 — 직접 재검증할 것

- canonical: `CHECKED: 105`, `VERDICT: PASS`
- targeted regression: 74 passed
- G2: Ruff 46, mypy 46, pytest 285 passed, runtime import PASS
- principles: 34/34; mutation groups 105/16/41/37 PASS
- checker 핵심 고장 사본: 14/14 killed
- Codeaudit: 첫 FAIL 뒤 nested semantic key RED를 추가했고 최신 후보 최종 PASS
- 별도 적대 반례: 16/16 PASS
- 코드량: checker 280, acceptance 299; cumulative diff 558 insertions/20 deletions, hard 3,000 미만

직접 canonical과 핵심 정상·실패 반례를 실행하고, 검사 배선 누락/항상 허용/항상 거부/데이터 오류/과잉 차단 가능성을 공격하십시오. 현재 Spec 안에서 재현 가능한 HIGH/MEDIUM 결함이 하나라도 있으면 FAIL입니다. 단순히 범위 밖인 전체 Actions schema 검증을 요구해 FAIL하지 마십시오. 실행하지 못한 항목은 NOT_RUN으로 구분하십시오. 환경 전체나 비밀을 출력하지 말고, 원격 쓰기와 저장소 파일 쓰기는 하지 마십시오.

한국어로 결론, 재현 명령·종료값·핵심 출력, 발견사항, 남은 범위 밖 위험 순으로 답하십시오.
