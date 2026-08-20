# 원칙 복구 커밋 후보 Codex V2 판정 — 2026-08-20

## 결론

V2 판정은 PASS다. 현재 index와 고정 격리 snapshot의 tree가 같고, clean pre-push 21개와 문서 lint가 모두 통과했다. 기존 사용자 자산과 직전 작업도 index 밖에 보존됐다.

## 실행 신원과 경과

- 실행: fresh Codex verifier `/root/commit_prep_v2`
- 방식: 읽기 전용 cached diff·작업공간·격리 snapshot 재현
- 최초 판정: FAIL — V1 문서 추가 뒤 첫 snapshot이 현재 index와 달랐다.
- 두 번째 판정: FAIL — 동작 증거는 일치했지만 staged 장부가 이전 경로와 lint 수치를 가리켰다.
- 최종 판정: PASS — 장부 정정 뒤 현재 index와 snapshot tree를 다시 일치시키고 전체 검사했다.

## 최종 증거

- 대상 HEAD: `858b96d510cf9e4da393b85446871448b4c1dfa6`
- staged tree와 snapshot tree: `a9f41f414219941ede66308bcc266ad8c12bded7`
- snapshot: `/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/va-commit-prep-v2.Ogd6EZ`
- snapshot status: clean
- `.validation-logs/pre_push.log`: exit 0, 21개 실행, 21개 `ok`
- `.validation-logs/brief_lint.log`: 위반 0건, 문서 4개
- 기존 사용자 자산 42개 결합 지문: `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`
- mutation: 반례 29 + 대조군 5 = `CHECKED: 34`, `VERDICT: PASS`
- pre-commit과 cached diff check: exit 0

## V1 대비 판정

- F1: FIXED. exact tree와 durable log가 일치한다.
- F2: V1 과장. 현재 45개는 기존 42개와 직전 작업 3개로 재현된다.
- F3: FIXED. 숫자·머리말·실행 결과가 29+5=34로 일치한다.
- cached 제외, 실행권한, HEAD 불변: PASS.

남은 차단 결함은 발견하지 못했다. 현재 혼합 작업공간 pre-push exit 1은 사용자 자산을 보존하는 P15 기대 동작이며, clean snapshot 통과와 섞지 않는다.
