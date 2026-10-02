---
name: grokreview
description: Grok으로 PR 또는 지정 파일의 모든 줄을 리뷰한다. GitHub Actions가 PR마다 자동 실행하고, 로컬에서는 같은 스크립트를 돌린다. "그록 리뷰", "grok review", "라인 리뷰", "코드리뷰 자동화"에서 트리거.
---

# Grok 라인 리뷰

리뷰 대상 파일의 **모든 줄**을 청크로 나눠 Grok에 보내고, 결함만 PR 인라인 코멘트로 남긴다.
스타일 지적은 하지 않는다. 줄을 표본으로 뽑거나 조용히 잘라내지 않는다.

## 자동 실행

`.github/workflows/grok-review.yml` 이 두 경로로 돈다.

- PR을 열거나 커밋을 올리면 그 PR의 변경 파일 전 줄을 리뷰한다.
- 월–금 09:00과 17:00(KST)에 열린 PR을 다시 훑는다. 같은 head SHA 에 이미 리뷰 표식이 있으면 그 PR은 다시 보내지 않고 `ALREADY` 로 남긴다.

기본 브랜치에 이 워크플로가 머지된 뒤부터 적용된다. schedule 은 기본 브랜치에서만 돈다.

사용자 PC 브라우저에 Grok이나 GitHub가 로그인돼 있어도, 그 세션은 GitHub 러너로 넘어오지 않는다. 정기 실행은 브라우저 조작이 아니라 이 워크플로다.

일회 설정: 저장소 Actions secret `XAI_API_KEY`.
모델은 기본 `grok-4.6`. 바꾸려면 Actions variable `XAI_MODEL`.

시크릿을 받는 스크립트는 PR 브랜치가 아니라 기본 브랜치 사본이다.
PR이 스크립트를 바꿔 키를 빼가지 못하게 하기 위해서다.

## 로컬 실행

```bash
# 커버리지만. API 호출 없음.
python3 scripts/grok_review/review.py plan --paths path/to/file.py

# 변경 파일 전 줄. XAI_API_KEY 필요. 키가 없으면 실패하고 리포트를 만들지 않는다.
XAI_API_KEY=... python3 scripts/grok_review/review.py review

# 저장소 추적 파일 전 줄. 비용이 크다. PR 이벤트에서는 돌리지 않는다.
REVIEW_SCOPE=full XAI_API_KEY=... python3 scripts/grok_review/review.py review
```

키를 저장소, 문서, 커밋에 적지 않는다.

## 판정

- 체크 초록 = 대상 줄을 모두 보냈다. 결함 0건이 아니다.
- 결함은 PR 코멘트다. 기본값에서는 머지를 막지 않는다.
- high 지적에서 체크를 실패시키려면 `GROK_REVIEW_FAIL_ON=high`.
- 텍스트 줄은 용량이 커도 청크로 나눠 모두 보낸다. 빼는 파일은 비밀(`.env`), 바이너리, UTF-8이 아닌 파일뿐이고, 사유를 코멘트에 남긴다.
