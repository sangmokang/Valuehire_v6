# 다른 PC 개발 인계 — 2026-09-22

## 공유 범위

현재 루트의 미커밋 JD·채용 도구, 공유 스킬, 계약, 회귀시험 및 기존
검증 장치 개선을 보존한다. Cursor 규칙, AGENTS.md, 환경변수 예시와
설치 안내를 추가한다. 운영 제품 전체 배포나 별도 worktree의 자동 병합은 아니다.

미푸시 커밋 네 개 가운데 SOT 정리 커밋 하나만 공유 계보에 포함한다.
개인별 채용 조사 이력이 있는 세 커밋은 공개 저장소에 보내지 않는다.
원본은 로컬 main과 backup/pre-cross-pc-handoff-20260922에 보존한다.

## 검증과 한계

- HumanSearch: 230 tests, ruff, mypy strict 실행 통과.
- 루트 JD·채용 도구: 기존 106 tests 실행 통과.
- 로컬 출력 파일에 의존하던 InMail 검사 세 개를 추적 fixture로 전환.
- 루트 회귀시험을 GitHub verify workflow에 추가.
- 실제 사이트 로그인·메일·Supabase·아카이버 재연결과 타 PC 실기기 실행은 별도다.
- 최종 원격 판정은 PR의 해당 SHA에 대한 CI 결과로 확인한다.

## 비공개 로컬 보존

인벤토리 시점 worktree 159개, dirty 18개, origin에서 HEAD가 도달 불가능한
worktree 80개를 확인했다. 위치와 브랜치는 공개 문서에 복제하지 않는다.
`artifacts/cross-pc-handoff/`에는 브랜치 bundle, worktree 인벤토리,
루트 외 dirty worktree 17개의 binary patch/미추적 파일 archive, 공개 제외한
루트 업무 자료 archive가 있다. 이 디렉터리에는 개인정보가 포함될 수 있으므로
GitHub에 올리지 말고 본인 PC 사이의 비공개 경로로만 이전한다.

Bundle은 커밋 이력을 보존하며 실행 환경·자격증명·ignored 데이터 전체를
포함하지 않는다. 별도 worktree 작업을 재개할 때는 manifest의 HEAD를 먼저
checkout한 뒤 staged.patch를 `git apply --index`, unstaged.patch를
`git apply`로 적용하고 해당 untracked archive를 복원한다. 기존 작업이 없는
새 디렉터리에서 경로와 내용을 확인한 후 적용한다.

새 PC의 공개 코드 시작 절차는 [development-setup.md](development-setup.md)를 따른다.
