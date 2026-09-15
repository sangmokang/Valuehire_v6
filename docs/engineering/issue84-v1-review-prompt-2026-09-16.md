독립 읽기 전용 적대검증을 수행하세요. 작업 대상은 현재 임시 clone의 HEAD입니다.
원본 작업 공간 파일을 쓰거나 원격 push/PR을 만들지 마세요. 파괴적 Git 실증은
Git 환경변수를 제거한 mktemp 임시 저장소에서만 하세요. 이 작업의 작성자 결론은
받지 않았으므로 직접 명령과 출력을 보고 판단하세요.

T 계약(합격 기준):
1. HEAD=refs/heads/main에서 staged change로 일반 git commit을 하면 종료값 비0,
   stderr에 `BLOCKED: direct commit to main`, 전후 HEAD 동일. 이는 GitHub 이슈 #84의
   원문 중심 A입니다.
2. 분리 worktree의 task/example staged commit은 종료값 0과 HEAD 전진.
3. 기본 worktree의 task/* staged commit은 A와 다른 stderr인
   `BLOCKED: development commit in primary worktree`, 종료값 비0, HEAD 불변.
   이는 이번 요청에서 추가된 B입니다. 기본 식별은 실제 git-dir==git-common-dir.
4. fixture/대상/실행 사례가 0이면 PASS 출력 금지.
5. 기존 비밀 스캔과 workflow 약화 검사의 정상·차단 판정 유지.
6. 새 인수 파일은 실제 pre-push 실행, verify.yml 고정 CI 목록,
   verification-commands.md 및 기존 인수 무결성 계약(run-acceptance +
   semantic-mutations)에 연결. 원본 main의 미커밋 새 지문 명부는 이 clone의
   정본이 아니므로 연결된다고 주장하지 마세요.
7. 프로젝트 전용 허용 우회 변수/설정 추가 금지. 로컬 표준 훅은 Git 옵션으로
   우회 가능하고 CI는 개발자 로컬의 기본 worktree를 관찰하지 못함. 실제
   GitHub branch protection 설정은 아직 미확인.

읽을 파일: docs/sot/git-workflow.md, hook-contracts.md,
verification-commands.md, coding-principles.md, principles.yaml,
hooks/pre-commit, hooks/pre-push, scripts/install-hooks.sh,
scripts/acceptance-commit-worktree-guards.sh,
scripts/acceptance-0-7.sh, scripts/acceptance-hs-a4.sh,
scripts/acceptance-silent-failure-lint-mutations.sh,
scripts/verify/run-acceptance.sh, scripts/acceptance-semantic-mutations.sh,
.github/workflows/verify.yml. docs/sot/strict-workflow.md는 origin/main에
없고 원본 main의 미전송 커밋에만 있으므로 이 clone에서 없음을 근거로
비밀리에 요구사항을 낮추지 마세요.

실행 증거: docs/engineering/issue84-commit-guards-red-output-2026-09-15.txt,
issue84-commit-guards-green-output-2026-09-15.txt,
issue84-final-ac-output-2026-09-15.txt,
issue84-unborn-main-output-2026-09-16.txt,
issue84-main-predicate-mutation-output-2026-09-15.txt,
issue84-primary-predicate-mutation-output-2026-09-15.txt,
issue84-prepush-output-2026-09-15.txt,
issue84-hs-a4-diagnosis-output-2026-09-16.txt,
issue84-silent-lint-diagnosis-output-2026-09-16.txt.
최종 SHA의 새 AC·pre-push 출력 두 파일은 임시 clone에 별도 복사됩니다.

반드시 스스로 무언가를 깨려는 명령을 실제 실행하고 원문을 보고하세요.
정조준: 설치 누락 가짜 허용, wrong-reason 차단, main의 분리 worktree,
unborn main, primary 식별의 경로 정규화, detached/non-task 경계,
CHECKED 위조/0건, CI 스텝 주석·삭제·조건부/echo 치환, 새 인수 파일의
pre-push 글로브 수집, 기존 회귀 fixture가 위치 정책에 가려진 경우,
정본 P11 hard 600 정상/601 고장, 원본 상태 불변. PASS를 낼 경우에도
시도한 반례와 왜 깨지지 않았는지 실행 출력으로 기록하세요. 결함 후보는
심각도, file:line의 줄 역할, 원인, 사업 영향을 적으세요.

[출력 형식 — 반드시 지킬 것]
첫 줄은 VERDICT: PASS|FAIL.
그다음 결론 → 판단 근거 → 기술 상세와 증거 원문 순서로 쓴다.
결론에는 전문용어를 쓰지 않는다. 판단 근거에는 선택·버린 해석·틀리면 깨지는 것을 쓴다.
전문용어는 첫 등장 문장 안에서 풀고, 출력·코드·표 바로 아래에는 → 해석을 붙인다.
file:line에는 줄의 역할을 붙인다. 결함마다 심각도, 원문 제목, 원인, 사업 영향을 쓴다.
설계 지적은 무엇을/왜/버린 길/대가/되돌리기 다섯 줄로 쓴다.
건너뜀·미확인·실패 후 재시도와 추정을 판정 앞부분에 밝힌다.
증거를 생략하지 말고 무엇을 어떻게 깨려다 실패했는지 반증 기록을 남긴다.
한국어 존칭체로 쓰되 내용을 축소하거나 초등학생 비유를 쓰지 않는다.
