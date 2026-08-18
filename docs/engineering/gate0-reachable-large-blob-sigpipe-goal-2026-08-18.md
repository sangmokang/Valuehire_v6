# 결론

큰 기록 조각의 앞부분에 금지값이 있어도 검사 두 곳을 모두 빠져나가는 결함을 새 후속 변경으로 막습니다.
같은 변경이 서버에서도 성공하기 전에는 다음 HumanSearch 선행 작업을 시작하지 않습니다.

## 판단 근거

PR #23은 현재 작업에서 가리키지 않는 임시 Git 객체(= 저장소에는 남았지만 현재 기록에서는 찾아갈 수
없는 조각)의 검사를 강하게 만들었습니다. 그러나 현재 기록에서 직접 찾아갈 수 있는 큰 blob(= Git이
파일 내용을 저장하는 객체)은 별도 경로에서 `grep -q`로 검사합니다. `grep -q`는 값을 찾는 순간 읽기를
끝내므로 큰 객체를 내보내던 앞 명령이 SIGPIPE(= 받는 쪽이 먼저 닫혀 쓰기가 중단됐다는 신호)로 끝납니다.
두 검사 경로는 이 신호를 값 없음으로 오판해 합격시킵니다.

이 결함은 이슈 #22의 현재 commit 설명문·tree 경로·tag 설명문 확대와 다릅니다. 이번 대상은 직접 참조가
가리키는 blob 내용이며, 기존 문서가 이미 "도달 가능한 모든 blob"을 검사한다고 약속한 범위입니다.

### 결정 카드

**무엇을** — 로컬 시작 검사와 서버 자동 검사의 큰 blob 판정을 함께 고치고, 같은 결함을 재현하는 합성 시험을 기존 AC-19 시험에 추가합니다.
**왜** — 한쪽만 고치면 로컬과 서버가 서로 다른 답을 내며, 새 시험을 별도 파일로 만들면 실제 호출 경로와 떨어진 고아 검사가 될 수 있기 때문입니다.
**버린 길** — PR #23을 되돌리면 무해한 임시 객체 허용과 강한 객체형 검사를 함께 잃습니다. 이슈 #22에 섞으면 서로 다른 경계를 한 승인에 숨기므로 둘 다 버립니다.
**대가** — 큰 객체 검사는 값을 찾은 뒤에도 입력을 끝까지 읽어야 하므로 작은 추가 실행 시간이 들지만, 읽기 실패와 값 발견을 구분할 수 있습니다.
**되돌리기** — 후속 구현 기록을 되돌리면 PR #23 병합 직후 상태로 돌아갑니다. RED 시험 기록은 결함 증거로 남기고 이슈를 다시 미해결로 표시합니다.

## 검증 원문

### 1. 현재 상태

- 기준 브랜치: `origin/main`
- 기준 기록: `34e4ccff88ce776d06e3001734005a34b169f7eb`
- 이슈: `#27 도달 가능한 대용량 blob의 금지값 가짜 합격을 막는다`
- 작업 브랜치: `task/gate0-reachable-large-blob-sigpipe`
- 작업 공간: `worktrees/gate0-reachable-large-blob-sigpipe`

시작 검사는 다음 결과로 끝났습니다.

```text
START=2026-08-18T02:28:45Z
HEAD: 34e4ccf (synced)
ORIGIN: 34e4ccf
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
END=2026-08-18T02:48:09Z
RC=0
```

→ 현재 main과 원격 main이 같고 미해결 검사는 0건입니다. 다른 셀의 동시 검사 부하 때문에 19분 24초가
걸렸지만, 하위 검사가 계속 바뀌며 끝까지 실행됐고 원명령의 성적은 0이었습니다.

현재 결함은 다음 세 위치에 있습니다.

- `scripts/acceptance-0-2.sh:137-146` — 도달 가능한 blob을 `grep -qF`로 읽어 큰 객체의 앞부분 매치를
  파이프 실패로 오판합니다.
- `.github/workflows/verify.yml:48-83` — 서버의 같은 검사가 `grep -qEif`를 사용해 같은 오판을 합니다.
- `scripts/acceptance-0-2-unreachable-content.sh:48-70,215-221` — 차단 사례는 실패 이유를 확인하지 않고,
  예정 사례 수와 실제 실행 수가 달라도 출력만 하고 합격할 수 있습니다.

작은 blob과 50MiB blob을 직접 tag가 가리키게 한 합성 감사 결과는 다음과 같습니다.

```text
small listed=1 rc=1 result=BLOCKED
large listed=1 rc=0 result=ALLOWED
ci_small hit=1 result=BLOCKED
ci_large hit=0 result=ALLOWED
```

→ 두 큰 객체는 실제 검사 목록에 포함됐지만 로컬과 서버 등가 경로에서 모두 합격했습니다. 실제 비밀값은
사용하지 않았고 고정 합성 카나리만 사용했습니다.

### 2. 근본 원인

1. 큰 blob 앞부분에서 값을 찾으면 `grep -q`가 조기 종료합니다.
2. `set -o pipefail` 때문에 앞의 `git cat-file`이 받은 SIGPIPE가 파이프 전체 실패가 됩니다.
3. 현재 코드는 파이프 실패를 "값 없음"과 구분하지 않습니다.
4. 기존 13개 시험의 큰 객체 사례는 안전하게 고쳐진 unreachable 경로만 실행해 reachable 경로를 덮지
   않습니다.
5. 시험 하네스는 차단의 정확한 이유와 실행 사례 수를 종료 성적으로 강제하지 않습니다.

### 3. 단일 인수 기준 AC-27

합성 저장소에서 직접 tag가 가리키는 작은 blob과 50MiB blob 앞부분에 합성 금지값을 넣었을 때, 실제
로컬 판정기와 서버 워크플로의 실제 실행 본문이 모두 0이 아닌 성적으로 차단해야 합니다. 같은 경로에서
blob 읽기를 일부러 실패시키면 값 없음으로 합격하지 않아야 합니다. 모든 차단 사례는 예정한 실패 문구를
함께 확인해야 하고, 예정 사례 수와 실제 실행 수가 다르면 전체 시험이 실패해야 합니다.

기계 확인 조건은 다음과 같습니다.

- RED 기록에서는 대용량 reachable blob과 reachable blob 읽기 실패가 로컬·서버 양쪽에서 가짜 합격해
  전체 시험이 실패합니다.
- GREEN 기록에서는 기존 13개 보호를 유지하면서 새 사례를 포함한 전체 사례가 정확한 수로 합격합니다.
- `bash -n`은 변경한 모든 셸 파일에 대해 성적 0을 냅니다.
- `bash scripts/session-status.sh`는 `RED: 0/N`, `N>0`, `UNKNOWN` 0건과 성적 0을 냅니다.
- `bash verify.sh`와 일반 push가 실행하는 전체 검사가 성적 0을 냅니다.
- 서버의 push 검사와 pull request 검사가 최종 원격 기록과 같은 기록을 검사해 모두 성공합니다.

### 4. Harness 게이트

- Gate 0 — 시작 자격: 위 원문처럼 `RED: 0/20`, 현재 main과 원격 main 동일로 통과했습니다.
- Gate 1 — 스펙: GitHub 이슈 #27과 이 문서의 AC-27을 정본으로 사용합니다.
- Gate 2 — 격리: 이 문서에 적은 전용 worktree·브랜치만 사용합니다.
- Gate 3 RED: 실제 대상 코드보다 먼저 reachable 작은/큰 blob, 읽기 실패, 사례 수 불일치 시험을
  고정하고 실패 원문을 남깁니다.
- Gate 3 GREEN: RED 시험 기대값을 바꾸지 않고 두 판정 경로와 하네스만 최소 수정합니다.
- Gate 4: 작은 대상 시험부터 문법, 시작 검사, verify, pre-push, 변조 시험 순서로 실행합니다.
- Gate 4.5: Claude V1이 다른 엔진으로 공격하고 Codex V2가 모든 근거를 재현해 다시 공격합니다.
- Gate 5: 일반 push와 한국어 PR, 같은 기록의 서버 검사 성공까지만 진행합니다.
- Gate 6: merge·branch 삭제·배포는 오너 승인 전 실행하지 않습니다.

### 5. 적대검증 항목

1. 50MiB unreachable 사례만 통과시키고 reachable 경로는 여전히 빠뜨리는가.
2. 로컬만 고치고 서버 워크플로는 같은 `grep -q` 오판을 남기는가.
3. 작은 blob 차단이나 기존 13개 객체형·도구 실패·환경 격리 보호를 약화하는가.
4. `git cat-file` 읽기 실패를 금지값 없음으로 통과시키는가.
5. 차단 사례가 관련 없는 실패로 끝나도 성공으로 인정하는가.
6. 사례가 생략돼 실제 실행 수가 예정 수보다 적어도 합격하는가.
7. 실제 비밀 패턴·원본 객체·바깥 저장소를 합성 시험이 읽거나 바꾸는가.
8. 이슈 #22 또는 HumanSearch 제품 분류기 범위를 섞는가.

### 6. SOT 체크리스트

- [x] `docs/sot/INDEX.md` — 사건 기록은 이 goal 문서에, 다음 세션의 영구 명령은 SOT에 둡니다.
- [x] `docs/sot/coding-principles.md` — P2 실행 가능한 인수 기준, P3 조용한 실패 금지, P5 RED 불변,
  P13 검사 약화 표시, P15 로컬·서버 동시 방어, P20 0건 가짜 합격 금지를 적용합니다.
- [x] `docs/sot/git-workflow.md` — main 직접 수정 없이 작업 1개·worktree 1개·브랜치 1개로 격리합니다.
- [x] `docs/sot/hook-contracts.md` — pre-push 전체 검사와 session-status 출력 계약을 보존합니다.
- [x] `docs/sot/verification-commands.md` — make/npm이 아닌 실제 저장소 명령과 CI 단계 목록을 사용합니다.

### 7. 비범위

- PR #23 되돌리기, force-push, rebase, 이력 재작성
- 이슈 #22의 reachable commit message·tree path·annotated tag message 구현
- HumanSearch `auth_surface.py` 또는 제품 시험 생성·수정
- 실제 포털·브라우저·로그인·세션·후보자 정보·실제 비밀값 접근
- merge, auto-merge, 배포, main 직접 push

### 8. RED→GREEN 실행 로그

#### 8-1. RED — 실제 판정기보다 시험을 먼저 고정

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
START=2026-08-18T02:57:33Z
[1/20] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> PASS (exit=0)
[2/20] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> PASS (exit=0)
[3/20] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/20] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/20] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[6/20] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[7/20] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[8/20] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/20] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/20] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[11/20] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/20] 직접 참조가 가리키는 작은 blob의 금지값을 차단 -> BLOCKED (exit=1)
[13/20] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[14/20] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[15/20] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[16/20] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
스캔 대상 객체:        9개
PASS: 히스토리 전량 blob 스캔 0건 (blob 5개 검사)
[17/20] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> UNEXPECTED (exit=0, expected=blocked)
스캔 대상 객체:        9개
PASS: 히스토리 전량 blob 스캔 0건 (blob 5개 검사)
[18/20] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[19/20] 예정 사례 수와 실제 실행 수가 다르면 전체를 차단 -> BLOCKED (exit=1)
[20/20] Git hook 환경에서도 바깥 저장소 무오염 -> UNEXPECTED (exit=1, head_same=YES, status_same=YES)
[1/16] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/16] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/16] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[4/16] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[5/16] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[6/16] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[7/16] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[8/16] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[9/16] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[10/16] 직접 참조가 가리키는 작은 blob의 금지값을 차단 -> BLOCKED (exit=1)
[11/16] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[12/16] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[13/16] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[14/16] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
스캔 대상 객체:        9개
PASS: 히스토리 전량 blob 스캔 0건 (blob 5개 검사)
[15/16] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> UNEXPECTED (exit=0, expected=blocked)
스캔 대상 객체:        9개
PASS: 히스토리 전량 blob 스캔 0건 (blob 5개 검사)
[16/16] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 16
FAIL: AC-19 예상과 다른 사례 4건
CHECKED: 20
FAIL: AC-19 예상과 다른 사례 5건
END=2026-08-18T03:02:09Z
RED_RC=1
```

→ 기존 13개 보호와 작은 reachable blob 대조군은 예상대로 동작했습니다. 로컬·서버의 큰 reachable blob과
읽기 실패 네 경계는 모두 가짜 합격했고, 훅 내부 재실행도 같은 네 결함을 재현해 전체 시험을 실패시켰습니다.
사례 수 불일치 자체도 예정 문구와 성적으로 차단됐으며 바깥 HEAD·파일 상태는 같았습니다.

#### 8-2. GREEN 이후 기록 위치

이 절 아래에 GREEN 명령·전체 출력, 변조 시험과 원복 확인을 순서대로 추가합니다.

### 9. 적대 검증 로그

이 절 아래에 실제 `claude -p` 명령 전문과 판정 원문, Codex V2 재현 명령·출력·일치 여부를 순서대로
추가합니다.
