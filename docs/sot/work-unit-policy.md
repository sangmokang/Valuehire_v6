# Work Unit 정책

이 문서는 `docs/sot/work-unit-policy.yaml`에서 생성한다.
손으로 고치지 말고 `ruby scripts/verify/render-work-unit-policy.rb docs/sot/work-unit-policy.yaml`로 다시 만든다.

## Work Unit

- Work Unit 하나는 주장 1개만 담는다.
- PR 하나는 Work Unit 1~5개만 담는다.
- Work Unit이 5개 미만이어도 브랜치는 48시간 안에 닫는다.
- 완료 조건:
  - `local_validation`
  - `adversarial_checks_1_to_3`
  - `completion_commit`

## Pull Request

- 최종 관문은 이 순서 그대로 실행한다:
  - `strict`
  - `codeaudit`
  - `integrated_adversarial`
  - `pull_request`
  - `github_verify`
  - `merge`
- squash 뒤 롤백 경계는 `pull_request` 전체다.

## 고위험 REVIEW

- 고위험 경로와 표면:
  - `.github/workflows/**`
  - `hooks/**`
  - `scripts/acceptance-*`
  - `verify*`
  - `mechanism-registry`
  - `비밀·후보자 데이터 노출 검사`
  - `배포·인증·로그인`
- 고위험 Work Unit은 실행 REVIEW가 필요하다: `true`.
- 문서 REVIEW만으로 고위험 Work Unit을 닫을 수 있다: `false`.
- 유료 외부 REVIEW가 기본 필수다: `false`.

## 강제 장치

- 정책 정본: `docs/sot/work-unit-policy.yaml`
- 생성 문서: `docs/sot/work-unit-policy.md`
- 검사기: `scripts/verify/check-work-unit-policy.rb`
- 렌더러: `scripts/verify/render-work-unit-policy.rb`
