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

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
START=2026-08-18T03:05:23Z
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
[13/20] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> BLOCKED (exit=1)
[14/20] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[15/20] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[16/20] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> BLOCKED (exit=1)
[17/20] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[18/20] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[19/20] 예정 사례 수와 실제 실행 수가 다르면 전체를 차단 -> BLOCKED (exit=1)
[20/20] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 20
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
END=2026-08-18T03:09:36Z
GREEN_RC=0
```

→ RED 시험 파일을 바꾸지 않고 기존 보호와 새 여섯 실행 경계, 사례 수 불일치, 훅 환경을 모두 통과했습니다.
RED에서 가짜 합격했던 로컬·서버 대용량 blob과 읽기 실패 네 항목은 각각 예정한 실패 문구로 차단됐습니다.

#### 8-3. 후속 검증 기록 위치

실제 저장소의 로컬 패턴 파일은 내용을 복사하거나 출력하지 않고 main 작업공간의 무시된 파일을 가리키는
심볼릭 링크로만 연결했습니다.

```text
$ SECRET_PATTERNS_FILE= bash scripts/acceptance-0-2.sh
START=2026-08-18T03:11:22Z
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
END=2026-08-18T03:15:36Z
AC02_RC=0
```

→ 합성 시험뿐 아니라 실제 저장소의 시작 판정 경로도 끝까지 실행돼 성적 0을 냈습니다. 실제 패턴 내용은
읽거나 출력하지 않았습니다.

##### 8-3-1. 변조 Attempt 1 — 잘못된 로컬 위치를 공격해 승인 증거에서 제외

첫 변조는 로컬의 두 비슷한 검색 줄 중 reachable이 아니라 unreachable 큰 객체 줄을 바꿨습니다. 서버 줄은
정확히 바뀌었지만 로컬 목표를 공격하지 못했으므로 결과를 승인 증거에서 제외하고 실패 이력으로 남깁니다.

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
START=2026-08-18T03:16:10Z
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
[11/20] 큰 unreachable blob 앞쪽의 금지값도 차단 -> UNEXPECTED (exit=1, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[12/20] 직접 참조가 가리키는 작은 blob의 금지값을 차단 -> BLOCKED (exit=1)
[13/20] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> BLOCKED (exit=1)
[14/20] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[15/20] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[16/20] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> UNEXPECTED (exit=1, expected=blocked)
스캔 대상 객체:        9개
FAIL: 히스토리 blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[17/20] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
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
[9/16] 큰 unreachable blob 앞쪽의 금지값도 차단 -> UNEXPECTED (exit=1, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[10/16] 직접 참조가 가리키는 작은 blob의 금지값을 차단 -> BLOCKED (exit=1)
[11/16] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> BLOCKED (exit=1)
[12/16] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[13/16] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[14/16] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> UNEXPECTED (exit=1, expected=blocked)
스캔 대상 객체:        9개
FAIL: 히스토리 blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[15/16] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[16/16] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 16
FAIL: AC-19 예상과 다른 사례 2건
CHECKED: 20
FAIL: AC-19 예상과 다른 사례 3건
END=2026-08-18T03:23:59Z
MUTATION_RC=1
```

→ 시험 자체는 실패했지만 로컬 목표 줄을 공격하지 못했습니다. 이 결과를 근거로 로컬 reachable 검출력을
승인하지 않고, 원복 후 정확한 줄을 다시 공격했습니다.

##### 8-3-2. 변조 Attempt 2 — 로컬·서버 reachable 줄을 정확히 공격

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
START=2026-08-18T03:24:57Z
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
[13/20] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> UNEXPECTED (exit=1, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: 도달 가능 blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[14/20] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[15/20] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[16/20] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> UNEXPECTED (exit=1, expected=blocked)
스캔 대상 객체:        9개
FAIL: 히스토리 blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[17/20] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
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
[11/16] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> UNEXPECTED (exit=1, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: 도달 가능 blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[12/16] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[13/16] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[14/16] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> UNEXPECTED (exit=1, expected=blocked)
스캔 대상 객체:        9개
FAIL: 히스토리 blob 읽기 실패: 715094b63b611ca4e3a813970dba62c7f6f55dad (exit=141)
[15/16] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[16/16] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 16
FAIL: AC-19 예상과 다른 사례 2건
CHECKED: 20
FAIL: AC-19 예상과 다른 사례 3건
END=2026-08-18T03:32:29Z
REACHABLE_MUTATION_RC=1
```

→ 로컬과 서버의 큰 reachable blob 사례가 모두 값 발견이 아닌 읽기 실패로 뒤집혀 예정 문구 대조에서
잡혔고, 바깥 저장소 불변도 유지됐습니다. 작은 객체와 실제 읽기 실패 대조군은 계속 예정대로 차단됐습니다.

변조 두 줄을 원복한 직후 상태는 다음과 같습니다.

```text
HEAD=1b0b73e0678c8f6929982b24835713a353265fde
RED_TEST_IMMUTABLE=YES
MUTATION_RESTORED=YES
```

→ 추적 파일과 스테이지 차이는 0건이고, RED 시험은 `ae0f75b`와 같으며 두 구현 파일은 GREEN 커밋과 다시
일치합니다.

#### 8-4. 전체 게이트 기록 위치

변경한 셸과 서버 실행 본문의 문법은 다음과 같이 통과했습니다.

```text
GNU bash, version 3.2.57(1)-release (arm64-apple-darwin24)
AC02_SYNTAX_RC=0
AC20_SYNTAX_RC=0
CI_BLOCK_SYNTAX_RC=0
```

→ macOS 기본 Bash 3.2에서 로컬 판정기, 20개 합성 시험, 서버에서 꺼낸 실제 실행 본문 모두 문법 성적
0이었습니다.

Codex V2가 다시 실행한 20개 시험 원문은 다음과 같습니다.

```text
START=2026-08-18T04:20:08Z
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
[13/20] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> BLOCKED (exit=1)
[14/20] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[15/20] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[16/20] 서버 본문도 직접 참조의 50MiB blob 금지값을 차단 -> BLOCKED (exit=1)
[17/20] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[18/20] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[19/20] 예정 사례 수와 실제 실행 수가 다르면 전체를 차단 -> BLOCKED (exit=1)
[20/20] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 20
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
END=2026-08-18T04:20:47Z
AC20_RC=0
```

→ 20개를 모두 실행했고, 차단 사례는 정해 둔 이유 문구와 함께 차단됐습니다. 마지막 `CHECKED: 20`과
프로그램 성적 0이 함께 있어 일부 사례 생략을 합격으로 바꿀 수 없습니다.

구현 직후 `verify.sh` 원명령은 다음과 같이 통과했습니다.

```text
START=2026-08-18T03:53:38Z
PASS: no secret-pattern match in any tracked file, .env not tracked
END=2026-08-18T03:53:41Z
VERIFY_RC=0
```

→ 현재 추적 파일에 금지값이나 추적된 환경 파일이 없고 검증 프로그램 성적은 0입니다. 다만 공유
`main`이 뒤에서 바뀌었으므로 배송 직전에 같은 원명령을 다시 실행해야 합니다.

전체 시작 검사는 구현 코드가 아니라 공유 `main`의 동시 변경 때문에 아직 불합격입니다.

```text
START=2026-08-18T03:35:07Z
HEAD: f64e4e5 (ahead 4 / behind 0)
ORIGIN: 34e4ccf
RED: 1/20 (acceptance-0-7.sh 제외 — CI 담당)
END=2026-08-18T03:52:07Z
SESSION_RC=0
```

→ 상태 보고 프로그램 자체 성적은 0이지만 보고 내용이 `RED: 1/20`이므로 엄격 계약상 불합격입니다.

Claude V1 뒤 Codex가 실패한 한 검사를 다시 분리한 최신 원문은 다음과 같습니다.

```text
START=2026-08-18T04:21:47Z
FAIL: origin/main(34e4ccff88ce776d06e3001734005a34b169f7eb) != main(1e0f805652e114ff7104cd6c9fd9394422ea514f) — push 미완료
END=2026-08-18T04:21:52Z
AC05_RC=1
LOCAL_MAIN=1e0f805652e114ff7104cd6c9fd9394422ea514f
ORIGIN_MAIN=34e4ccff88ce776d06e3001734005a34b169f7eb
REMOTE_MAIN=34e4ccff88ce776d06e3001734005a34b169f7eb
DIVERGENCE=0/2
```

→ 다른 셀이 로컬 `main`에 문서 커밋 두 개를 추가했고 원격에는 아직 없어서 연결 검사만 실패합니다.
작업 시작 때는 0개, 첫 실패 때는 1개, 최신에는 2개로 늘어 동시 작업임이 재확인됐습니다. 이 작업은
공유 `main`을 reset·stash·checkout하거나 대신 push하지 않습니다.

따라서 `session-status` 원명령의 `RED: 0/N`과 pre-push 전체, 동일 기록 서버 검사는 아직 `NOT_RUN`이
아니라 **선행 실패가 확인된 진행 중 상태**입니다. 공유 작업 소유자가 `main`과 `origin/main`을 정상
동기화한 뒤 원명령부터 다시 실행하며, 그 전에는 push와 PR을 만들지 않습니다.

### 9. 적대 검증 로그

#### 9-1. Claude V1 실행 실패와 복구

기본 Claude 모델의 첫 두 새 세션은 같은 서비스 안전장치 오탐으로 각각 성적 1을 냈습니다.

```text
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606

Details: `[reasoning_extraction]`

Request ID: req_011Ce9YdtVuNQoBPRZCrTtxh
```

→ 첫 기본 모델 새 세션은 코드 검토를 시작하지 못하고 서비스 안전장치에서 성적 1로 끝났습니다.

```text
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606

Details: `[reasoning_extraction]`

Request ID: req_011Ce9Yxb2TMo1829FbaqCG3
```

→ 코드 판정은 시작되지 않았습니다. 같은 방법을 더 반복하지 않고 `--model sonnet --safe-mode` 새 세션으로
바꿨습니다.

모델을 바꾸는 첫 명령에서는 `--disallowedTools` 뒤의 가변 인자가 프롬프트까지 도구명으로 먹어 검증이
시작되지 않았습니다. 반복 경고 뒤 마지막 원문은 다음과 같습니다.

```text
Error: Input must be provided either through stdin or as a prompt argument when using --print
```

→ 대상 코드는 실행되지 않았고 파일도 바뀌지 않았습니다. 가변 도구 옵션을 제거하고 읽기 전용 지시를
프롬프트 안에 둔 새 명령으로 복구했습니다.

유효한 1차 검증 명령은 다음과 같습니다. 비밀 키 환경 변수는 제거했고, 다른 모델의 새 세션을 사용했습니다.

```text
env -u ANTHROPIC_API_KEY claude --model sonnet --safe-mode -p '<저장소와 origin/main..HEAD를 읽기 전용으로 검토하고, 로컬·서버 큰 blob 전체 읽기, 20개 사례 수와 정확한 차단 이유, 기존 #23 보호, RED 시험 불변, SOT·goal, #22·HumanSearch 격리, 공유 main 차단, Bash 3.2·PIPESTATUS를 확인하라는 프롬프트 + strict §8-7 출력 형식 전문>'
```

→ 실제 명령에는 위 항목과 strict §8-7 블록 전문이 들어갔습니다. 첫 응답은 `PASS`였지만 20개 출력과 객체
지문을 줄임표로 생략해 형식 미달로 판정했고, 같은 세션에 1회 보완을 요구했습니다.

보완 요청에서 백틱 세 쌍을 큰따옴표 안에 둔 실수로 셸이 세 표시를 명령으로 해석했습니다.

```text
zsh:1: command not found: …
zsh:1: command not found: dbb0...
zsh:1: command not found: →
```

→ 민감정보 노출과 파일 변경은 없었지만 프롬프트에서 세 표시가 빠졌습니다. 나머지 문장이 20개 원문과
전체 지문을 명시해 Claude가 완전한 보완 판정을 성적 0으로 반환했습니다. 이 명령 인용 실수는 승인
근거로 숨기지 않고 Codex V2의 별도 재현으로 다시 확인했습니다.

#### 9-2. Claude V1 보완 판정 원문

```text
VERDICT: PASS

# 결론

1. 이번 변경은 실제로 존재했던 결함(50MiB 크기의 대용량 기록 조각 앞부분에 금지된 값이 있어도 검사가 이를 "값 없음"으로 오판해 통과시키는 문제)을 코드 두 곳(로컬 판정 스크립트, 서버 자동검사 워크플로) 모두에서 고쳤습니다. 제가 이 문제를 재현하는 최소 실험을 직접 만들어 실행해본 결과, 수정 전 방식은 실제로 종료 코드 141(비정상 신호 종료)을 반환하며 값이 있어도 통과했고, 수정 후 방식은 종료 코드 0으로 정상 동작하며 정확히 차단했습니다. 코드 자체는 문제없이 동작합니다.

2. 시험 코드(20개 사례를 강제 실행하는 스크립트)를 실제로 돌려본 결과 20개 사례 모두 예정된 결과(정상 통과 또는 예정된 실패 문구로 차단)를 그대로 냈습니다. 기존에 보호하던 항목들(작은/큰 객체, 커밋 설명문, 파일경로, 태그, 도구 자체가 죽는 경우, 알 수 없는 객체 종류, 종료 후 정리 상태 검사, 검사 스크립트가 실행되는 저장소 밖의 다른 저장소를 건드리지 않는지)도 전부 그대로 유지되어 있습니다.

3. 이번 변경의 이력 기록(어떤 커밋이 무엇을 했는지)을 추적한 결과, "실패하는 시험을 먼저 고정하고 그 시험 파일은 이후 절대 손대지 않는다"는 원칙이 실제로 지켜졌습니다. 처음 실패를 고정한 커밋과 현재 커밋 사이에서 시험 파일 자체는 글자 하나도 바뀌지 않았습니다.

4. 이번 변경은 GitHub 이슈 #27(이번 작업 대상)에만 해당하는 범위이며, 별도로 열려 있는 이슈 #22(커밋 설명문·파일경로 안의 금지값을 도달 가능한 경로에서 추가로 잡는 작업, 아직 미착수)나 HumanSearch라는 별개 제품의 파일과는 전혀 섞이지 않았습니다. 실제로 변경된 파일 5개를 모두 확인했으며 그 범위를 벗어난 항목은 없습니다.

5. 세션 상태 점검에서 "20개 중 1개 실패"가 보고되는 현상을 직접 원인 추적했습니다. 이 실패는 이번 작업과 무관한 별도 작업(같은 컴퓨터에서 진행 중인 문서 정리 작업)이 만든, 아직 원격 저장소에 올리지 않은 커밋 2개 때문에 로컬의 `main` 브랜치가 원격과 어긋나 있어서 생기는 현상입니다. 이번 검토 대상인 큰 객체 결함 수정과는 관계가 없습니다. 다만 원인이 되는 커밋 개수는 문서가 암시한 "1개"가 아니라 정확히 "2개"였다는 점은 바로잡아 기록해 둡니다. 그리고 관련 작업 기록 문서는 "서버 쪽 검사까지 성공을 확인하기 전에는 다음 작업을 시작하지 않는다"고 스스로 못박아 놓았을 뿐, "배송이 끝났다"고 주장하는 곳은 어디에도 없었습니다. 오히려 문서 뒷부분에 "적대적 검증 결과"와 "전체 게이트 통과 기록"을 채워 넣을 자리를 비워둔 채로 남겨 두었는데, 이는 해당 절차가 아직 이 시점까지는 실행되지 않았다는 뜻이며, 정직하게 미완료를 표시해 둔 것으로 보입니다(과장된 완료 주장은 없었습니다).

6. macOS 특유의 오래된 bash(버전 3.2), 파이프 중간 명령의 종료 코드를 따로 잡아내는 기법(PIPESTATUS), 파이프 전체 실패 처리 옵션(pipefail), 따옴표 처리, 대용량 객체 처리 방식을 모두 직접 실행해 검증했지만 등급 "중간" 이상의 결함은 발견하지 못했습니다.
```

→ Claude의 고정 판정은 `PASS`, 중간 이상 결함 0건입니다. 기술 증거 전문은 아래 Codex V2 재현과 함께
보존하며, Claude가 바로잡은 공유 main 커밋 수 2개도 반영합니다.

Claude 보완 판정의 기술 상세까지 포함한 전체 원문은 다음 저장소 파일에 그대로 보존했습니다.

- `docs/engineering/gate0-reachable-large-blob-sigpipe-claude-v1-2026-08-18.txt`
- 내용 지문: `12228d8a85039357b6ff6c9fa059f5dd67840222a10256326afcf243e9ddd86d`

→ Claude 세션 장부의 최종 보완 응답과 위 파일을 바이트 단위로 대조해 저장했습니다. `VERDICT: PASS`,
20개 시험 전체, 전체 객체 지문, 실행하지 못한 서버 검사가 모두 들어 있습니다.

#### 9-3. Codex V2 독립 재현과 Claude 판정 재공격

Codex는 Claude가 쓴 객체를 재사용하지 않고 별도 임시 저장소에서 같은 결함을 다시 만들었습니다. 첫 시도는
임시 폴더 삭제 명령이 도구 안전 정책에 차단돼 실행 자체가 되지 않았고, 삭제 없는 새 임시 저장소로
접근을 바꿨습니다.

```text
PROBE_DIR=/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.00qcszLtIo
BLOB_SHA=bb5756ebb845a3417f953de18072f43b3180b3c4
OLD_CAT_FILE_RC=141 OLD_GREP_RC=0
NEW_CAT_FILE_RC=0 NEW_GREP_RC=0
CODEX_SIGPIPE_REPRO_RC=0
```

→ 수정 전에는 검색이 값을 찾았지만 앞 프로그램만 141로 끊겼고, 수정 후에는 둘 다 정상 성적 0입니다.
Claude와 다른 객체 지문으로 같은 원인을 재현했습니다.

범위와 시험 불변을 다시 확인한 원문은 다음과 같습니다.

```text
HEAD=f64e4e554c1b56b4b60354326a939f3c8483d68f
RED_TEST_DIFF_RC=0
DIFF_CHECK_RC=0
CHANGED_FILES=5
AUTH_SURFACE_ABSENT
AUTH_TEST_ABSENT
ISSUE_22_STATE=OPEN
PR_23_STATE=MERGED
BASH_VERSION=3.2.57
AC02_SYNTAX_RC=0
AC20_SYNTAX_RC=0
CI_BLOCK_SYNTAX_RC=0
```

→ RED 커밋 이후 시험 파일 차이는 0건이고, 변경은 검사·시험·SOT·goal 다섯 파일뿐입니다. HumanSearch
제품 파일은 없고 #22는 계속 별도 열린 작업이며 #23은 병합 상태입니다.

20개 시험의 전체 재실행은 §8-4 원문과 같이 `CHECKED: 20`, 성적 0이었습니다. 코드 대조 결과도 다음과
같습니다.

```text
AFFECTED_Q_SCAN
scripts/acceptance-0-2.sh:25:if grep -qF "$LIT" verify.sh; then echo "FAIL: verify.sh에 리터럴 하드코딩 잔존"; fail=1; fi
FULL_STREAM_SCAN
.github/workflows/verify.yml:80:            if git cat-file blob "$sha" 2>/dev/null | grep -aEif "$CLEAN" >/dev/null; then
scripts/acceptance-0-2.sh:118:     LC_ALL=C grep -aF "$LIT" >/dev/null; then
scripts/acceptance-0-2.sh:152:     LC_ALL=C grep -aF "$LIT" >/dev/null; then
```

→ 남은 `grep -qF` 한 줄은 큰 Git 객체를 읽는 경로가 아니라 작은 `verify.sh` 파일에 리터럴이 직접
박혔는지 보는 별도 검사입니다. 대상인 로컬·서버 Git 객체 경로와 기존 unreachable 경로는 모두 입력을
끝까지 읽습니다.

| Claude 주장 | Codex 재현 | 최종 판단 |
|---|---|---|
| 로컬과 서버의 큰 blob 결함이 닫힘 | 별도 50MiB 객체에서 수정 전 `141/0`, 수정 후 `0/0` | 일치 |
| 20개가 정확한 이유로 모두 실행됨 | `[1/20]`부터 `[20/20]`, `CHECKED: 20`, 성적 0 재현 | 일치 |
| 기존 RED 시험을 GREEN 뒤 고치지 않음 | `ae0f75b..HEAD` 시험 diff 0 | 일치 |
| #22와 HumanSearch 범위를 섞지 않음 | 변경 파일 5개, 제품 파일 두 개 모두 없음 | 일치 |
| 시작 검사 실패는 공유 main 상태 때문 | `acceptance-0-5.sh`만 실패, 원격보다 로컬 main 2개 앞섬 | 일치. 과거 1개 기록은 2개로 정정 |
| 서버 Ubuntu에서 실제 성공 | Claude도 실행하지 않았다고 명시 | 미확인. PR 서버 검사 전 완료 불가 |

→ Claude가 잡아준 구현 과장 0건, Claude가 바로잡은 stale 수치 1건, Codex가 Claude 판정에서 뒤집은
중간 이상 결함 0건입니다. 표의 서버 미확인은 push 뒤 같은 기록 검사로만 닫습니다.

#### 9-4. Codex V2 추가 공격 결과

- `[중간 이상 결함 0건]` 새 차단 사례는 실패 성적뿐 아니라 실패 이유 문구도 대조합니다.
- `[중간 이상 결함 0건]` 서버 시험은 워크플로 파일에서 현재 실행 본문을 추출하므로 복사된 가짜 판정기를
  시험하지 않습니다.
- `[낮은 잔여 위험]` 새 객체형 조회 실패와 검색 도구 자체 오류 분기는 안전하게 차단하도록 구현됐지만,
  이번 20개 묶음은 blob 읽기 실패를 중심으로 고정했습니다. 실제 서버 검사 전까지 이 사실을 완료로
  과장하지 않습니다.
- `[외부 차단]` 공유 로컬 `main`이 원격보다 두 커밋 앞서 있어 전체 시작 검사와 pre-push는 아직 합격
  상태가 아닙니다. 다른 셀의 커밋을 이 브랜치가 대신 처리하지 않습니다.

Codex V2 결론은 **구현 판정 PASS, 배송 판정 진행 중**입니다. 공유 `main` 동기화 뒤 원래
`session-status`·`verify`·pre-push를 다시 실행하고, 같은 원격 기록의 서버 검사까지 성공해야 배송 판정도
PASS로 바뀝니다.

#### 9-5. 공유 main 불일치의 비침범 복구

공유 `main` 소유 작업이 계속 실행 중인 사실을 확인했습니다.

```text
PROCESS=RUNNING
COMMAND=codex position-map P0 implementation
LOCAL_MAIN=1e0f805652e114ff7104cd6c9fd9394422ea514f
ORIGIN_MAIN=34e4ccff88ce776d06e3001734005a34b169f7eb
DIVERGENCE=0/2
```

→ 두 커밋을 되돌리거나 대신 push하면 다른 작업을 침범합니다. 기다리기만 하는 대신 원격에서 격리된
검증 복제본을 만들고, 이 브랜치 기록만 가져와 원래 명령을 실행했습니다.

격리 복제본의 자격은 다음과 같습니다.

```text
HEAD=332bbbaa2da1f25c3e07a229a1f728b672f70b3d
MAIN=34e4ccff88ce776d06e3001734005a34b169f7eb
ORIGIN_MAIN=34e4ccff88ce776d06e3001734005a34b169f7eb
HOOKS=hooks
```

→ 구현·시험·적대검증 증거가 든 당시 최종 브랜치 기록을 그대로 가져왔고, 검증 복제본의 로컬 main과
원격 main은 같습니다. 공유 루트의 ref·파일·프로세스는 바꾸지 않았습니다.

먼저 기존 실패 원명령을 다시 실행했습니다.

```text
START=2026-08-18T04:37:08Z
PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건
END=2026-08-18T04:37:12Z
AC05_ISOLATED_RC=0
```

→ 같은 연결 검사가 공유 루트에서는 성적 1, 깨끗한 격리 복제본에서는 성적 0이므로 구현 결함이 아니라
공유 ref 충돌이었다는 원인 분리가 끝났습니다.

전체 시작 검사 원명령 재실행 결과는 다음과 같습니다.

```text
START=2026-08-18T04:37:18Z
HEAD: 332bbba (ahead 5 / behind 0)
ORIGIN: 34e4ccf
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
END=2026-08-18T04:39:51Z
SESSION_ISOLATED_RC=0
```

→ 미해결 0건, 전체 20건, 알 수 없는 상태 0건, 프로그램 성적 0으로 엄격 시작 자격을 충족했습니다.

전체 검증 원명령 재실행 결과는 다음과 같습니다.

```text
START=2026-08-18T04:40:02Z
PASS: no secret-pattern match in any tracked file, .env not tracked
END=2026-08-18T04:40:03Z
VERIFY_ISOLATED_RC=0
```

→ 추적 파일 금지값 0건, 추적된 환경 파일 0건, 프로그램 성적 0입니다.

업로드 훅 전체 원명령 재실행 결과는 다음과 같습니다.

```text
START=2026-08-18T04:40:10Z
skip ./scripts/acceptance-0-2.sh (DEFERRED · CI 담당)
skip ./scripts/acceptance-0-5.sh (DEFERRED · CI 담당)
skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 18개 실행
ok ./scripts/acceptance-0-2-unreachable-content.sh
ok ./scripts/acceptance-0-6.sh
ok ./scripts/acceptance-hs-a3.sh
ok ./scripts/acceptance-hs-a4.sh
ok ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
ok ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
ok ./scripts/acceptance-hs-cleanroom-colon-paths.sh
ok ./scripts/acceptance-hs-cleanroom-file-urls.sh
ok ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
ok ./scripts/acceptance-hs-cleanroom-hook-env.sh
ok ./scripts/acceptance-hs-cleanroom-mutations.sh
ok ./scripts/acceptance-hs-cleanroom.sh
ok ./scripts/acceptance-hs-gates-antiforge.sh
ok ./scripts/acceptance-hs-gates-mutations.sh
ok ./scripts/acceptance-hs-gates.sh
ok ./scripts/acceptance-secret-webhook-vendor.sh
ok ./scripts/acceptance-verify-ac-m.sh
ok ./verify.sh
END=2026-08-18T04:41:30Z
PRE_PUSH_ISOLATED_RC=0
```

→ 훅이 실제 실행하는 18개가 모두 합격했습니다. 기존 훅의 `0-2`·`0-5` 안내 문구 결함은 PR #13의
별도 범위이며 이 작업에 섞지 않았습니다. 훅 앞에서 건너뛴 `0-2`는 §8-2 실제 로컬 실행, `0-5`는 위
복구 실행으로 따로 성적 0을 확보했습니다. `0-7`은 서버가 push 수행 중 확인할 항목입니다.

이 복구 뒤 배송 판정은 **로컬 필수 검사 PASS, 서버 검사 대기**로 승격합니다. 다음 커밋으로 이 증거를
포함한 최종 기록을 만든 뒤, 그 정확한 기록에서 세 원명령과 일반 push를 다시 실행합니다.

## 10. 2026-08-19 PR #29 `rev-list` 가짜 합격 후속 수리

### 결론

현재 로컬 검사는 검사할 기록 목록을 만드는 단계가 실패하거나 빈 목록을 돌려줘도 합격합니다. 서버가 이미
막는 두 실패와 1개뿐인 불완전 목록을 로컬에서도 같은 기준으로 차단하고, 기존 20개 사례를 포함한 전체 검증과 원격 검사가 모두
성공하기 전에는 이 후속 수리를 완료로 보지 않습니다.

### 판단 근거

`scripts/acceptance-0-2.sh:140-169`는 `git rev-list --all --reflog --objects`의 출력만 다음 반복문에
연결하고 프로그램이 끝나며 남긴 성적을 보존하지 않습니다. 따라서 명령이 73을 남기거나 성적 0과 빈
출력을 내도 반복문이 0회 실행되고 마지막 합격 문구까지 갑니다. 반면 `.github/workflows/verify.yml:57-65`는
목록 생성 실패와 고유 객체 2개 미만을 각각 차단합니다. 두 경로가 같은 답을 내도록 로컬에도 이 두 판정을
옮기되, 객체형 읽기·객체 본문 읽기·금지값 검색 성적을 각각 따로 보는 기존 분기는 건드리지 않습니다.

#### 결정 카드

**무엇을** — 로컬에서 도달 가능한 객체 목록 출력과 종료 성적을 따로 저장하고, 실패 또는 고유 객체 2개
미만을 서버와 같은 이유로 차단합니다.
**왜** — 검사할 입력이 만들어졌다는 사실부터 증명해야 “검사 대상 0건 합격”을 막을 수 있고, 로컬과 서버가
서로 다른 답을 내지 않기 때문입니다.
**버린 길** — 반복문 안에서 객체를 한 개라도 읽었는지만 세는 방식은 목록 생성 실패 성적을 이미 잃은 뒤라
정확한 원인을 구분하지 못하므로 버렸습니다.
**대가** — 객체 목록 전체를 셸 변수에 한 번 보관하므로 목록 크기만큼 메모리를 더 사용합니다.
**되돌리기** — 이번 후속 커밋만 되돌리면 원격 기록 `996e0979a348466f762110defe3986171eb5bf29` 상태로
돌아가지만, 새 세 회귀 시험이 다시 빨간불을 켜므로 결함 재개방이 즉시 드러납니다.

### 현재 상태와 근본 원인

- 현재 작업 기록과 PR #29 원격 기록은 모두 `996e0979a348466f762110defe3986171eb5bf29`입니다.
- 기준 원격 `main`은 `7bd3298695c93e0e60bdabd2500840da47c4db05`이고 작업공간 변경은 0건입니다.
- PR #29의 변경 범위는 기존 여섯 파일뿐이며 `weakens-check` 표식이 붙어 있습니다.
- 근본 원인은 프로세스 치환으로 목록만 넘기면서 목록 생성 명령의 종료 성적을 부모 셸이 판정하지 않은
  것입니다. 빈 성공 출력도 별도 최소 개수 판정이 없어 같은 가짜 합격 경로를 탑니다.

### 단일 인수 기준 AC-27-RL

- **EARS-1** — When `git rev-list --all --reflog --objects`가 73을 남기면, 시스템은 예정된
  `git rev-list 실패` 이유와 0이 아닌 성적으로 차단해야 합니다.
- **EARS-2** — When 같은 명령이 성적 0과 빈 출력을 내면, 시스템은 예정된 `도달 가능 객체가 0개`
  이유와 0이 아닌 성적으로 차단해야 합니다.
- **EARS-3** — While 기존 회귀 보호를 실행할 때, 시스템은 기존 20개 사례를 삭제하거나 기대를 완화하지
  않고 목록 실패·0개·1개 경계 세 사례를 더해 `CHECKED: 23`을 정확히 내야 합니다.
- **EARS-4** — Where 합성 검증을 실행할 때, 시스템은 합성 카나리와 `mktemp` 임시 저장소만 사용하고 Git
  관련 환경변수와 바깥 저장소의 기록·파일 상태를 바꾸지 않아야 합니다.
- **EARS-5** — While 로컬과 서버 검사를 비교할 때, 두 검사는 목록 생성 실패 및 고유 객체 2개 미만을
  모두 차단하고 객체형 읽기·객체 본문 읽기·금지값 검색 성적을 계속 별도로 판정해야 합니다.
- **EARS-6** — When 배송 자격을 판정할 때, `bash scripts/session-status.sh`는 `RED: 0/N`, `N>0`,
  `UNKNOWN` 0건을 내고 `bash verify.sh`, 업로드 전 검사 전체, Claude 1차 검증, Codex 2차 재공격,
  같은 새 원격 기록의 push·pull request 서버 검사가 모두 성공해야 합니다.

검증 명령은 `bash scripts/acceptance-0-2-unreachable-content.sh`이며 기대값은 새 세 사례가 예정 문구로
`BLOCKED`, 마지막이 `CHECKED: 23`, 전체 성적이 0인 것입니다. counter-AC(가짜 합격 시나리오)는
실패한 `rev-list`가 일부 출력을 남겼다는 이유로 그 일부를 정상 목록으로 쓰거나 마지막 합격 문구에
도달하는 경우, 0~1개 목록을 정상 저장소로 보는 경우, 새 세 사례를 내부 훅 모드에서 생략하는 경우입니다.

### 입출력·오류·경계 계약

- 입력은 `git rev-list --all --reflog --objects`의 표준 출력과 종료값입니다. 각 비어 있지 않은 출력 줄의
  첫 필드는 Git 객체 식별자이며, 경로 필드는 판정 입력이 아닙니다.
- 정상 출력은 고유 객체 식별자 2개 이상입니다. 0개와 1개는 서버 정본과 같이 저장소를 제대로 읽지 못한
  상태로 차단합니다.
- 목록 명령이 0이 아닌 값을 남기면 부분 출력 유무와 무관하게 목록 전체를 버리고 `fail=1`을 기록합니다.
- 목록이 유효할 때만 기존 객체형·blob 본문·금지값 검색 분기를 실행하며, 각 하위 명령의 종료값은 합치지
  않고 기존 오류 문구를 보존합니다.
- 출력 계약은 정상일 때 기존 최종 `PASS` 한 줄, 실패일 때 원인별 `FAIL` 한 줄 이상과 전체 0이 아닌
  종료값입니다. 재시도는 하지 않으며 동시성·권한·네트워크 입력은 없습니다.

### 영향 반경·데이터 안전·롤백

- 영향 반경은 로컬 `scripts/acceptance-0-2.sh`의 도달 가능한 객체 목록 생성 구간과 이를 직접 실행하는
  AC-19 합성 검사·pre-push뿐입니다. CI 서버 본문과 비밀 패턴 파일 형식은 바꾸지 않습니다.
- 데이터 안전 AC — While 실패 fixture와 변조 검증을 실행할 때, 시스템은 실제 저장소의 HEAD와
  `git status --porcelain --untracked-files=all`을 실행 전후 동일하게 유지해야 합니다.
- 롤백은 구현 커밋 하나를 되돌리는 것입니다. 롤백 뒤 새 세 RED 사례가 다시 실패해야 결함 재개방을
  숨기지 않은 것으로 판정합니다.

### Harness 게이트 진행

- Gate 0: 지정 작업공간, 현재 기록, 깨끗한 상태, 여섯 파일 범위를 확인했습니다.
- Gate 1: 이 절의 AC-27-RL 하나로 수리 범위를 고정했습니다.
- Gate 2: 기존 전용 worktree `gate0-reachable-large-blob-sigpipe`만 사용합니다.
- Gate 3 RED: 로컬 `rev-list` 부분 출력·성적 73, 성적 0·빈 출력, 성적 0·1개 출력 세 사례를 추가하고 정확한 실패 이유를
  원문으로 보존합니다.
- Gate 3 GREEN: RED 시험 기대값을 바꾸지 않고 로컬 목록 판정만 최소 수정합니다.
- Gate 4: 셸 문법, 23개 사례, 상태 보고, 전체 검증, 업로드 전 검사를 원명령으로 실행합니다.
- Gate 4.5: Claude가 1차로 공격하고 Codex가 모든 근거를 독립 재현하며 양방향으로 다시 공격합니다.
- Gate 5: 전부 합격한 뒤에만 Lore 형식 커밋, 일반 push, PR 본문 뒤 추가, 표식과 동일 기록 서버 검사
  성공을 확인합니다.
- Gate 6: 오너 승인 댓글·병합·정리는 이번 요청의 중단 지점 뒤이므로 실행하지 않습니다.

### 게이트 설계 3원칙

- [x] 자기 선언 검증 — 목록이 있다는 선언을 믿지 않고 생성 명령의 종료 성적과 고유 객체 수가 검증합니다.
- [x] 실패 방향 확인 — 목록 실패나 0개가 있으면 합격이 아니라 차단되는 안전장치입니다.
- [x] 차단·통과 쌍 — 새 실패·경계 3종 차단과 기존 정상 저장소·20개 사례 통과를 함께 잽니다.

### 적대검증 항목

- `rev-list`가 일부 출력을 남기고 실패해도 그 일부를 정상 목록으로 사용하지 않는가.
- 빈 출력뿐 아니라 서버와 같은 1개 객체도 비정상적으로 적다고 차단하는가.
- 목록 실패를 고쳤다는 이유로 객체형 읽기·본문 읽기·금지값 검색의 서로 다른 실패를 합치지 않았는가.
- 새 시험이 복사 판정기가 아니라 실제 `scripts/acceptance-0-2.sh`를 실행하는가.
- 기본 23개·내부 훅 19개·사례 수 불일치 모드의 `TOTAL`과 `CHECKED`가 실제 실행 수와 정확히 일치하는가.
- 실제 저장소, Git 관련 환경변수, #22, HumanSearch, `auth_surface.py`가 건드려지지 않았는가.

### SOT 체크리스트

- [x] `docs/sot/INDEX.md` — 사건·실행 기록은 기존 goal 문서 뒤에만 추가합니다.
- [x] `docs/sot/coding-principles.md` — P2, P3, P5, P13, P15, P20과 V-1~V-5를 적용합니다.
- [x] `docs/sot/git-workflow.md` — 전용 작업 브랜치만 일반 push하고 병합하지 않습니다.
- [x] `docs/sot/verification-commands.md` — 이 저장소의 실제 Gate 0·4·5 명령을 사용합니다.
- [x] `docs/sot/hook-contracts.md` — 업로드 훅 전체 실행과 0개 검사 차단 계약을 유지합니다.
- [x] `docs/sot/mechanism-registry.yaml` — AC-19의 로컬·서버 연결을 약화하지 않습니다.

### 비범위

- #22 구현, PR #13 병합, PR #29 병합과 오너 승인 댓글은 하지 않습니다.
- HumanSearch 제품 파일, `auth_surface.py`, `test_auth_surface.py`는 수정하지 않습니다.
- 실제 포털·브라우저·로그인·세션·후보자 정보에는 접근하지 않습니다.
- rebase, force-push, `main` 직접 push, 자동 병합은 하지 않습니다.
- 과거 goal·Claude·Codex 기록은 삭제·수정하지 않고 이 절부터 뒤에만 추가합니다.

### 후속 RED·GREEN·검증 원문

이 아래에는 새 실패 시험, 최소 구현, 전체 검증, 두 엔진의 교차 판정을 실행 순서대로 추가합니다.

#### 10-1. 읽기 전용 인수 감사와 RED 확정

보고서의 브랜치 `ahead 6 / behind 6`, 미커밋 파일 2개, `126 insertions / 2 deletions`, 기본 사례
20→22와 내부 훅 사례 16→18은 현재 작업공간과 일치했습니다. 새 시험을 수정 전 판정기에 실행한 결과는
자원 고갈 없이 두 결함을 같은 실행에서 재현했습니다.

```text
[15/22] 도달 가능한 객체 목록 생성 실패를 빈 검사로 통과하지 않음 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[16/22] 도달 가능한 객체 목록이 비면 검사 대상 0건으로 통과하지 않음 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
CHECKED: 18
FAIL: AC-19 예상과 다른 사례 2건
CHECKED: 22
FAIL: AC-19 예상과 다른 사례 3건
AC19_RC=1
```

→ 실제 판정기는 목록 명령이 73으로 실패한 경우와 성적 0·빈 목록인 경우를 모두 합격으로 잘못 처리했습니다.
바깥 저장소의 기록과 파일 상태는 실행 전후 같았습니다.

#### 10-2. 최소 구현과 V2 경계 보강

`scripts/acceptance-0-2.sh:140-155`는 목록 명령의 출력과 종료값을 부모 셸에서 따로 보존하고, 실패하면
부분 출력을 버리며, 성공해도 고유 객체가 2개보다 적으면 차단합니다. `:155-186`은 이 두 선행 조건을
통과한 목록만 기존 객체형·본문·검색 판정에 연결합니다.

Codex 2차 공격에서 기존 RED 두 개만으로는 “일부 출력을 남기고 실패”와 “성공·객체 1개”를 영구히
증명하지 못한다는 공백을 찾았습니다. 실패 fixture가 가짜 객체와 오류 출력을 함께 남기게 하고, 그 가짜
객체가 후속 스캔되지 않았다는 금지표식 단언을 추가했습니다. 객체 1개 경계도 별도 23번째 사례로
고정했습니다. 따라서 기본 사례는 23개, 내부 훅 사례는 19개가 됐고 SOT와 서버 주석도 같은 수로 바뀌었습니다.

#### 10-3. GREEN과 고장 주입

최종 원명령 출력은 다음과 같습니다.

```text
[1/23] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> PASS (exit=0)
[2/23] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> PASS (exit=0)
[3/23] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/23] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/23] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[6/23] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[7/23] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[8/23] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/23] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/23] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[11/23] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/23] 직접 참조가 가리키는 작은 blob의 금지값을 차단 -> BLOCKED (exit=1)
[13/23] 직접 참조가 가리키는 50MiB blob 앞쪽의 금지값을 차단 -> BLOCKED (exit=1)
[14/23] 도달 가능한 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[15/23] 도달 가능한 객체 목록 생성 실패를 빈 검사로 통과하지 않음 -> BLOCKED (exit=1)
[16/23] 도달 가능한 객체 목록이 비면 검사 대상 0건으로 통과하지 않음 -> BLOCKED (exit=1)
[17/23] 도달 가능한 객체 목록이 하나뿐이면 불완전한 검사로 차단 -> BLOCKED (exit=1)
[18/23] 서버 본문도 직접 참조의 작은 blob 금지값을 차단 -> BLOCKED (exit=1)
[19/23] 서버 본문도 직접 참조의 50MiB blob 앞쪽의 금지값을 차단 -> BLOCKED (exit=1)
[20/23] 서버 본문도 blob 읽기 실패를 값 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[21/23] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[22/23] 예정 사례 수와 실제 실행 수가 다르면 전체를 차단 -> BLOCKED (exit=1)
[23/23] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 23
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
RESTORED_FINAL_AC19_RC=0
```

→ 기존 보호 20개와 새 실패·경계 3개를 모두 실행했고, 예정 수와 실제 수가 같으며 전체 성적은 0입니다.

고장 주입은 두 갈래로 실행했습니다. 구현의 `< 2` 경계를 `< 0`으로 바꾸자 0개 사례가 `UNEXPECTED`로
뒤집히고 전체 성적이 1이 됐습니다. 부분 출력 금지표식을 정상 출력에 일부러 맞추자 15번째 사례와 내부 훅
13번째 사례가 `UNEXPECTED`로 뒤집히고 전체 성적이 다시 1이 됐습니다. 두 변조를 각각 원복한 뒤 같은
원명령이 위 23/23과 성적 0을 다시 냈습니다.

#### 10-4. 전체 로컬 검증

```text
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
FINAL_AC02_RC=0

PASS: no secret-pattern match in any tracked file, .env not tracked
FINAL_VERIFY_RC=0

HEAD: 996e097 (ahead 6 / behind 6)
ORIGIN: 7bd3298
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
FINAL_SESSION_RC=0

BASH_N_RC=0
SHELLCHECK_RC=0
DIFF_CHECK_RC=0
scripts/acceptance-0-2.sh LINES=231 PASS
scripts/acceptance-0-2-unreachable-content.sh LINES=375 PASS
BOUNDARY_500_RC=0
BOUNDARY_501_RC=1
```

→ 실제 저장소 경로, 비밀 스캔, 전체 시작 검사, 셸 문법·정적 검사·공백 검사와 500/501줄 경계가 모두
예정한 성적을 냈습니다. 전체 시작 검사의 `20`은 파일 개수이고 AC-19의 `23`은 그 파일 내부 사례 수라
서로 다른 수치입니다.

#### 10-5. Claude V1 실패와 Codex V2 판정

`env -u ANTHROPIC_API_KEY claude -p` 계열로 Sonnet 읽기 전용, Sonnet 무도구, 전체 원문 내장, 좁은 코드
심사, Opus 좁은 심사를 순서대로 시도했습니다. 기본 CLI 진단은 3.2초 안에 다음을 냈습니다.

```text
CLAUDE_CLI_OK
```

→ 인증과 짧은 응답은 정상이지만 코드 심사는 세 차례 장기 무출력, 한 차례 사용 불가능한 `Read` 호출문,
한 차례 90초 무출력으로 끝나 유효한 `VERDICT`를 받지 못했습니다. V1 상태는 `NOT_RUN`이며 PASS가 아닙니다.

전체 시도 원문과 최종 프롬프트는
`.omx/artifacts/claude-pr29-rev-list-v1-20260819T135416Z-prompt.md`에 보존했습니다. 해당 파일 지문은
`29f333d5d482fd35ef9b03dedde3abf3f944c33d89762068acb1f3c34aed0930`입니다.

Codex 독립 리뷰는 코드 경로 PASS와 낮은 위험 문서 날짜 1건을 판정했습니다. 문서 날짜는 실제 확인 범위를
붙여 2026-08-19로 고쳤습니다. 최종 코드 지문은 다음과 같습니다.

```text
25a8ebcd4f618f24949072e5cd690e436854b8884a3e8684702bede0b0f798d1  scripts/acceptance-0-2.sh
2e94fd260c412bfa9d32165298dd4768e2136543433d598a8560604d049b11d4  scripts/acceptance-0-2-unreachable-content.sh
82ca6d265a7264a35637886cecd24ad6e2011eb1cd14e047bf08c1c9b46bd8fd  .github/workflows/verify.yml
7a0881fdaf81f4cab984441c28feb9046d0f33cf7beef62dff4078a833730785  docs/sot/verification-commands.md
```

→ Codex는 부분 출력 폐기, 0~1개 경계, 기존 하위 판정 보존과 23/19 사례 수를 독립 실행으로 확인했습니다.
다만 G·V1·V2가 모두 같은 계약에 동의해야 한다는 strict 완료 조건은 V1 부재로 충족하지 못했습니다.

#### 10-6. 현재 정지점

- 코드와 로컬 검증은 끝났지만 Claude V1은 `NOT_RUN`이므로 엄격 완료가 아닙니다.
- 작업공간이 미커밋 상태라 깨끗한 기록을 요구하는 `hooks/pre-push` 원명령은 아직 실행하지 않았습니다.
- 이 상태에서 커밋·push·PR 본문 변경·병합을 실행하지 않습니다.
- 다음 실행은 Claude V1 복구 → 지적 재현과 V2 재공격 → Lore 커밋 → 깨끗한 최종 기록의 pre-push →
  사용자 승인 뒤 일반 push와 PR #29 본문 갱신 순서입니다.
