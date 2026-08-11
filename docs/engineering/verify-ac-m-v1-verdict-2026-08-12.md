VERDICT AC-M: FAIL

# 결론

현재 변경은 합치지 마십시오. 서버에서 돌 명령을 존재하지 않는 내용으로 바꾸거나, 사람이 직접 돌릴 파일을 실행할 수 없게 만드는 보호를 제거해도 전체 확인이 성공으로 끝났습니다.

또한 서버 자동검사 단계를 꺼 놓거나 아예 지워도 15개 확인은 모두 성공했습니다. 명부와 실제 실행이 다르면 막겠다는 이 작업의 핵심 약속을 지키지 못하므로 불합격입니다.

아홉 가지 요청 항목은 모두 로컬에서 실행해 확인했습니다. 원본과 대상 작업 공간은 시작 전후 파일 목록·내용·상태가 같았고, 금지하신 다른 작업 공간은 읽지도 쓰지도 않았습니다.

# 판단 근거

- ※ GitHub 서버에 접속해 PR #8의 과거 실행 기록을 조회하지는 않았습니다. 현재 .github/workflows/verify.yml을 YAML(사람이 읽는 설정 형식)로 실제 해석해 조건 없는 단계인지 확인했고, 격리 복제본에서 비활성화·삭제 반례를 실행했습니다.
- worktrees/secret-webhook-vendor는 지시대로 완전히 제외했습니다. 그 경로를 나열하거나 상태를 조회하지도 않았습니다.
- 저장소 루트에서 git status를 한 번 실행했으나 이 위치가 작업 공간이 아닌 bare 저장소(체크아웃 파일 상태를 관리하지 않는 저장소)라 종료값 128이 나왔습니다. 대상 워크트리의 전후 상태·전체 파일 지문으로 대체했습니다.
- 첫 git clone 뒤 체크아웃 명령을 복제본이 아닌 상위 임시 폴더에서 실행해 한 번 실패했습니다. 복제본 안에서 다시 실행해 지정 HEAD와 깨끗한 상태를 확인했습니다.
- 첫 ID 규칙·서버 작업명 규칙 변형은 if 문 자체까지 깨뜨려 문법 오류가 났습니다. 이 둘은 증거에서 제외하고 문법을 유지한 채 조건만 항상 거짓으로 바꿔 다시 실행했습니다.
- 임시 YAML 파일을 apply_patch로 만들려 했으나 프로젝트 밖 쓰기가 정책상 거부됐습니다. 원본 안에 쓰지 않고 /private/tmp에 printf로만 만들었습니다.
- 변형 실행 래퍼를 처음 구성할 때 도구의 문자열 치환 오류가 셸 실행 전에 한 번 발생했습니다. 저장소나 격리 복제본에는 아무 변경도 생기지 않았고 수정 후 다시 실행했습니다.

## 판정 선택 이유

판정 기준은 “현재 정상 입력이 통과하는가”가 아니라 “틀린 명부나 약해진 검사도 성공으로 보고되는가”입니다. docs/sot/coding-principles.md:18은 NOT_RUN(검사를 하지 못한 상태)도 전체 성공으로 보지 말라고 하고, 같은 파일 :28은 검사 약화를 잡아야 하며, :30은 로컬에만 있는 검사는 없는 것으로 보라고 정합니다.

가장 강한 반대 해석은 “구현자가 기록한 정확한 여섯 변형은 실제로 모두 잡혔으니 주장은 맞다”입니다. 이 해석은 버렸습니다. docs/engineering/verify-ac-m-goal-2026-08-12.md:154-165는 여섯 변형을 근거로 검사 장식이 아니라 각 규칙 삭제를 감지한다고 일반화하지만, 수동 파일 실행권한만 제거한 변형과 CI(코드를 서버에서 자동 검사하는 절차) 항목의 거짓 target(실제로 실행된다고 명부에 적는 명령 문자열)은 둘 다 CHECKED: 15, 종료값 0으로 살아남았습니다.

명부 target의 “문자 그대로 일치”는 파일 한 줄 전체가 완전히 같아야 한다는 뜻이 아니라, 정본 docs/engineering/verify-unification-goal-2026-08-10.md:80이 요구한 grep -qF(정해진 문자열이 파일 안에 그대로 포함됐는지 찾는 명령) 방식으로 해석했습니다. 줄 전체 일치를 택하면 현재 세 항목 모두 들여쓰기나 뒤쪽 명령 때문에 실패하므로 정본과 충돌합니다.

높음 결함이 하나라도 있으면 FAIL이라는 사용자 기준을 적용했습니다. 이 판정이 틀려서 합쳐지면, 명부에 적힌 서버 명령이 거짓이거나 서버 검사가 아예 꺼져도 담당자가 15개 성공 표시를 근거로 정상이라고 오판할 수 있습니다.

## 설계 결정 카드 1 — CI 항목의 명령 문자열

- **무엇을** — stage: ci 항목도 target 문자열이 해당 워크플로 파일에 실제로 있는지 확인해야 합니다.
- **왜** — 현재는 작업 이름만 맞으면 존재하지 않는 명령을 명부에 써도 통과합니다.
- **버린 대안** — 작업 이름만 확인하고 target은 설명용으로 두는 안은 정본의 “실제 명령 문자열” 계약과 충돌해 버렸습니다.
- **대가** — 워크플로 명령을 바꿀 때 명부도 함께 고쳐야 하므로 변경 작업이 한 줄 늘어납니다.
- **되돌리는 법** — ci 분기에서 고정 문자열 확인을 제거하면 현재 동작으로 돌아가지만, 그러면 정본 계약도 함께 축소해야 합니다.

## 설계 결정 카드 2 — 수동 단계의 음성 시험

- **무엇을** — 존재하지만 실행권한이 없는 파일을 가리키는 수동 단계 fixture(고정 시험 입력)를 추가해야 합니다.
- **왜** — 현재 시험은 사유가 없는 경우와 정상 파일만 있어 실행권한 검사 한 줄을 지워도 성공합니다.
- **버린 대안** — 수동 규칙 전체 삭제만 시험하는 안은 사유 검사 하나가 대신 실패해 실행권한 누락을 가리므로 버렸습니다.
- **대가** — 확인 항목 수가 16으로 늘어나므로 정확값과 문서 증거를 함께 갱신해야 합니다.
- **되돌리는 법** — 새 fixture와 기대값을 되돌리면 현재 15개 체계로 복귀하지만 같은 조용한 통과가 다시 생깁니다.

## 설계 결정 카드 3 — 서버 자동검사 배선

- **무엇을** — .github/workflows/verify.yml에 AC-M 인수 명령이 정확히 한 번, 조건 없이 존재하는지 인수 검사에서 확인해야 합니다.
- **왜** — 현재 단계를 if: false로 끄거나 삭제해도 로컬 인수 검사는 모두 성공합니다.
- **버린 대안** — 문서와 코드 검토만으로 배선을 보장하는 안은 P15의 “로컬에만 있는 검사는 없는 것으로 친다”는 원칙 때문에 버렸습니다.
- **대가** — 워크플로 단계 이름이나 배치를 바꾸면 인수 검사도 함께 갱신해야 합니다.
- **되돌리는 법** — 배선 단언을 제거하면 현재 상태로 돌아가지만 서버 실행 누락을 다시 자동으로 못 잡습니다.

## 설계 결정 카드 4 — 입력 형식과 경로 경계

- **무엇을** — 중복 필드·인라인 주석·짝이 안 맞는 따옴표·빈 값·단계와 맞지 않는 필드·절대경로를 명시적으로 거부해야 합니다.
- **왜** — 지금 파서는 뒤에 나온 값을 덮어쓰거나 일부 문자를 ID로 흡수해 계약 밖 입력을 성공으로 처리합니다.
- **버린 대안** — “현재 정본 파일만 깨끗하면 된다”는 안은 이 검사기의 목적이 향후 명부 불일치를 막는 것이므로 버렸습니다.
- **대가** — 간이 셸 파서가 길어지거나 검증 가능한 단순 형식으로 계약을 더 좁혀야 합니다.
- **되돌리는 법** — 엄격 검증을 제거하면 현재 관대한 해석으로 돌아가지만 조용한 통과를 다시 허용합니다.

# 결함 목록

## D1 — 높음: CI 항목의 거짓 target이 전체 성공합니다

그대로 두면 서버에서 실제로 돌지 않는 명령을 명부가 실행 중이라고 표시해도 담당자가 정상으로 승인할 수 있습니다.

- scripts/verify/check-mechanism-registry.sh:91-96 — ci 단계에서 ci_mirror_job 작업 이름만 확인하고 target 문자열은 읽지 않습니다.
- docs/sot/mechanism-registry.yaml:21 — 실제 명부의 CI target 값입니다.
- docs/engineering/verify-ac-m-goal-2026-08-12.md:154-165 — “registry_fake_target”을 포함한 여섯 변형이 전부 감지됐다고 기록한 증거 절입니다.
- 실행 반례: ci-secret-scan의 target을 run: bash scripts/fake-never-called.sh로 바꾼 뒤 전체 인수 검사가 CHECKED: 15, 종료값 0이었습니다.

## D2 — 높음: 수동 파일 실행권한 검사만 제거하면 전체 성공합니다

그대로 두면 사람이 직접 실행해야 하는 필수 검사가 실행 불가능해져도 시험 묶음은 정상이라고 보고합니다.

- scripts/verify/check-mechanism-registry.sh:101-102 — 수동 파일의 실행권한을 확인하는 실제 한 줄입니다.
- scripts/acceptance-verify-ac-m.sh:90-110 — 사유 없음과 정상 실행 파일만 시험하고, 존재하지만 실행 불가능한 파일은 시험하지 않습니다.
- 실행 반례: elif [ ! -x "$e_path" ]를 elif false로 바꾸자 비실행 파일 직접 검사는 잘못 통과했고, 전체 15개 인수 검사도 종료값 0이었습니다.

## D3 — 높음: AC-M 서버 자동검사를 끄거나 지워도 전체 성공합니다

그대로 두면 로컬에서는 모두 성공하지만 서버에서는 AC-M이 한 번도 실행되지 않는 상태가 조용히 배포 판단 자료로 남습니다.

- .github/workflows/verify.yml:152-156 — 현재는 조건 없이 AC-M 인수 명령을 실행하는 활성 단계입니다.
- docs/sot/verification-commands.md:28 — 같은 명령을 서버 목록에 적은 SOT(팀이 최종 기준으로 삼는 문서) 줄입니다.
- scripts/acceptance-verify-ac-m.sh:148-164 — 실제 명부 통과와 항목 수만 확인하며 자기 CI 단계 존재·조건은 확인하지 않습니다.
- 실행 반례: 단계에 if: ${{ false }}를 넣은 경우와 단계 전체를 삭제한 경우 모두 CHECKED: 15, 종료값 0이었습니다.

## D4 — 중간: 저장소 밖 절대경로가 명부 경로 계약을 통과합니다

그대로 두면 명부가 저장소 안의 검사가 아니라 각 실행 기계의 임의 파일을 가리켜 재현성과 통제 범위가 깨집니다.

- docs/engineering/verify-ac-m-goal-2026-08-12.md:108 — path를 저장소 루트 기준 상대경로로 정한 계약 줄입니다.
- scripts/verify/check-mechanism-registry.sh:79-80 — 상대경로·상위 이동을 확인하지 않고 파일 존재만 봅니다.
- 실행 반례: path: "/bin/sh", stage: "manual" 입력이 PASS, 종료값 0이었습니다.

## D5 — 중간: 계약 밖 YAML 여러 형태가 조용히 성공합니다

그대로 두면 중복 값 중 마지막 값이 몰래 이기거나, 잘못 닫힌 따옴표와 주석이 ID·사유에 섞여도 명부가 정상으로 승인됩니다.

- scripts/verify/check-mechanism-registry.sh:37-43 — 따옴표의 짝을 검사하지 않고 앞뒤 문자를 각각 떼는 부분입니다.
- scripts/verify/check-mechanism-registry.sh:133-149 — 필드 중복을 기록하지 않고 같은 변수에 마지막 값을 덮어쓰며 인라인 주석을 금지하지 않는 파서(설정 문서를 읽는 부분)입니다.
- 실행 반례: 중복 path, 중복 ci_mirror_job, ID 뒤 인라인 주석, 수동 사유 뒤 인라인 주석, 닫히지 않은 ID 따옴표, 값 없는 비해당 필드, 단계와 맞지 않는 추가 필드가 모두 종료값 0이었습니다.

## D6 — 중간: 문법 오류만 있고 인식된 항목이 0개면 잘못된 종료값 2를 냅니다

그대로 두면 잘못 쓴 명부가 “위반”이 아니라 “검사를 하지 못함”으로 분류돼 상태 집계와 원인 대응이 달라집니다.

- docs/engineering/verify-ac-m-goal-2026-08-12.md:104-105 — 계약 밖 형식은 종료값 1, 없는 명부·빈 명부·0항목만 종료값 2로 정한 줄입니다.
- scripts/verify/check-mechanism-registry.sh:158-163 — syntax_fail=1을 반영한 뒤에도 checked=0이면 먼저 종료값 2로 끝내는 부분입니다.
- 실행 반례: 첫 항목을 두 칸 들여쓴 입력은 FAIL:을 출력하고도 마지막에 NOT_RUN, 종료값 2였습니다.

## D7 — 중간: §10의 “항목·규칙마다 출력” 계약보다 출력이 적습니다

그대로 두면 한 항목에서 다섯 규칙 중 무엇을 실제로 확인했는지 실행 기록만으로 구분할 수 없어 검증 증거의 추적성이 떨어집니다.

- docs/engineering/verify-ac-m-goal-2026-08-12.md:103 — 항목·규칙마다 PASS:/FAIL: 줄을 요구합니다.
- scripts/verify/check-mechanism-registry.sh:111-115 — 항목 전체에 대해 결과 한 줄만 냅니다.
- 실행 결과: 실제 명부 3항목은 결과 줄도 3개뿐이었고 규칙별 결과 줄은 없었습니다.

## D8 — 낮음: 격리한 임시 폴더에 xcrun_db가 남습니다

그대로 두면 저장소 내용은 안전하지만 반복 실행 시 운영체제 도구의 임시 캐시가 실행별 임시 경로에 남아 “잔존물 없음”을 엄밀히 만족하지 못합니다.

- scripts/acceptance-verify-ac-m.sh:22 — 시작 상태를 읽는 git status가 macOS에서 xcrun_db를 만들었습니다.
- scripts/acceptance-verify-ac-m.sh:29-30 — 스크립트가 만든 $TMP 디렉터리만 지우고 상위 TMPDIR의 캐시는 지우지 않습니다.
- 최소 재현: 빈 TMPDIR에서 git status만 실행해도 491바이트 xcrun_db가 생겼고, 검사기만 실행했을 때는 생기지 않았습니다.

## D9 — 낮음: 함수 크기 권고선을 7줄 넘습니다

그대로 두면 즉시 잘못 동작하지는 않지만 규칙 추가 때 한 함수의 조건 흐름을 검토하기 어려워져 이후 결함 가능성이 높아집니다.

- docs/sot/coding-principles.md:26 — 함수 soft 60줄, hard 100줄을 정합니다.
- scripts/verify/check-mechanism-registry.sh:52부터 :118 — flush_entry 함수가 실행 측정상 67줄입니다.

# 9개 검증 항목 판정 요약

| 번호 | 무엇을 어떻게 실행했나 | 판정 | 반례 |
|---|---|---|---|
| 1 | /bin/bash 3.2.57로 두 스크립트 문법 검사 후 실제 명부·전체 인수 검사 실행 | 통과 | 찾지 못함 |
| 2 | 정상·경로 없음·죽은 명령 fixture를 직접 실행하고 규칙 2·3 제거 시 서로의 결과가 분리되는지 확인 | 통과 | 찾지 못함 |
| 3 | 다섯 규칙을 격리 복제본에서 각각 무력화하고 매회 복원 확인 | 실패 | 수동 실행권한 한 줄만 제거하면 전체 성공; CI target 거짓값도 전체 성공 |
| 4 | 인수 검사 한 줄을 삭제해 CHECKED가 14가 되게 실행 | 통과 | 종료값 1로 막음 |
| 5 | 전후 Git 상태, 경로·권한 목록, 전체 파일 SHA-256(파일 내용 지문), 전용 임시 폴더 비교 | 부분 실패 | 저장소는 동일하나 xcrun_db 잔존 |
| 6 | Ruby YAML 해석 뒤 각 target을 해당 파일에서 고정 문자열로 검색하고 줄 수 출력 | 통과 | 세 값 모두 정확히 한 번 발견 |
| 7 | 4칸, 탭, 인라인 주석, 빈 값, 중복 필드, 잘못 닫힌 따옴표, 절대경로 등 직접 실행 | 실패 | 계약 밖 입력 8종 이상 종료값 0 |
| 8 | 기본·명시 입력, WORKFLOW_FILE, 정상·위반·없음·0건·문법 오류의 출력과 종료값 실행 | 실패 | 절대경로, 0항목 문법 오류의 종료값, 규칙별 출력 불일치 |
| 9 | 워크플로를 YAML로 해석해 정확한 단계 수·조건 키를 확인하고 SOT 문자열 대조 | 현재 상태 통과 | 단계를 끄거나 삭제해도 인수 검사가 성공하는 보호 공백 |

→ 뭘 시켰나: 사용자가 지정한 아홉 항목을 각각 실행 가능한 시험으로 바꿨습니다.  
→ 뭐가 나왔나: 1·2·4·6은 반례가 없었고, 3·5·7·8에서 결함, 9에서 현재 상태는 정상이나 삭제 방어 공백을 찾았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 높은 결함 세 개 때문에 전체적으로 나쁜 소식이며 FAIL입니다.

# 기술 상세·명령·출력

## 0. 대상과 기준 커밋 고정

    $ git rev-parse HEAD
    f038c24daf07a02c976bb8895cd7cd2df1da4c09
    $ git rev-parse task/verify-ac-m
    f038c24daf07a02c976bb8895cd7cd2df1da4c09
    $ git merge-base 0459a37 HEAD
    0459a371ca2504bb0e61c091f7dfbdcd355f089f
    $ git status --porcelain=v1 --untracked-files=all
    [출력 없음]

→ 뭘 시켰나: 지정 브랜치·HEAD·기준 커밋과 시작 상태를 확인했습니다.  
→ 뭐가 나왔나: 세 SHA가 사용자 지정값과 일치했고 대상 워크트리는 깨끗했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 올바른 대상을 검증했다는 좋은 소식입니다.

    $ git diff --name-status 0459a37..f038c24 -- [지정 산출물]
    M	.github/workflows/verify.yml
    A	docs/engineering/verify-ac-m-goal-2026-08-12.md
    A	docs/sot/mechanism-registry.yaml
    M	docs/sot/verification-commands.md
    A	scripts/acceptance-verify-ac-m.sh
    A	scripts/verify/check-mechanism-registry.sh
    A	scripts/verify/fixtures/mechanism-registry/dead-target.yaml
    A	scripts/verify/fixtures/mechanism-registry/missing-path.yaml
    A	scripts/verify/fixtures/mechanism-registry/normal.yaml

→ 뭘 시켰나: 기준 커밋부터 HEAD까지 지정 산출물의 변경 종류를 확인했습니다.  
→ 뭐가 나왔나: 요청에 적힌 신설·수정 파일이 모두 해당 변경 범위에 있었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 검증 범위가 PR 산출물과 맞습니다.

    $ git status --porcelain=v1  # 저장소 루트
    fatal: this operation must be run in a work tree
    RC=128
    $ git rev-parse --is-bare-repository
    true

→ 뭘 시켰나: 원본 루트의 작업 공간 상태를 읽으려 했고 실패 원인을 확인했습니다.  
→ 뭐가 나왔나: 루트는 bare 저장소라 작업 공간 상태를 낼 수 없었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 첫 방법은 실패했지만 대상 워크트리 전체 지문 비교로 대체해 판정 공백은 없습니다.

## 1. bash 3.2 문법과 실제 실행

    $ /bin/bash --version | sed -n '1p'
    GNU bash, version 3.2.57(1)-release (arm64-apple-darwin24)
    $ /bin/bash -n scripts/verify/check-mechanism-registry.sh
    SYNTAX_CHECKER_RC=0
    $ /bin/bash -n scripts/acceptance-verify-ac-m.sh
    SYNTAX_ACCEPTANCE_RC=0
    $ /bin/bash scripts/verify/check-mechanism-registry.sh docs/sot/mechanism-registry.yaml
    PASS: secrets-scan-precommit (pre-commit)
    PASS: acceptance-glob-prepush (pre-push)
    PASS: ci-secret-scan (ci)
    CHECKED: 3
    RC=0

→ 뭘 시켰나: macOS 기본 bash 3.2에서 문법 검사와 실제 명부 실행을 모두 했습니다.  
→ 뭐가 나왔나: 문법 오류가 없고 실제 명부 3항목이 종료값 0으로 실행됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 항목 1에는 반례를 찾지 못했습니다.

    scripts/verify/check-mechanism-registry.sh:15
    # bash 3.2 호환 — ${VAR^^} 계열 금지, 연관배열 금지.
    scripts/verify/check-mechanism-registry.sh:122
    line=$(printf '%s' "$raw" | tr -d '\r')

→ 뭘 시켰나: 호환 동작을 담당하는 줄을 실행 결과와 대조했습니다.  
→ 뭐가 나왔나: bash 3.2에 없는 대문자 치환 대신 tr을 사용합니다.  
→ 좋은 소식인가 나쁜 소식인가: 코드와 실행 증거가 일치합니다.

## 2. fixture 3종의 독립 실패 경로

    $ checker normal.yaml
    PASS: secrets-scan-precommit (pre-commit)
    PASS: ci-secret-scan (ci)
    CHECKED: 2
    RC=0
    $ checker missing-path.yaml
    FAIL: ghost-mechanism — path 실존하지 않음 — scripts/this-file-does-not-exist.sh
    CHECKED: 1
    RC=1
    $ checker dead-target.yaml
    FAIL: dead-target-mechanism — 죽은 target — 'bash scripts/nonexistent-check-never-called-anywhere.sh' 이(가) hooks/pre-commit 안에 없다
    CHECKED: 1
    RC=1

→ 뭘 시켰나: 세 고정 입력을 검사기에 직접 넣었습니다.  
→ 뭐가 나왔나: 정상은 0, 경로 없음과 죽은 명령은 각기 다른 문구로 1이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 한 원인으로 셋 다 빨간 것이 아닙니다.

    CASE=R2_PATH_EXISTENCE_REMOVED
    FAIL: fixture path 없는 항목 → 불합격 (기대 exit=1, 실제 0)
    PASS: fixture 죽은 target → 불합격 (exit=1)
    CHECKED: 15
    CASE_RC=1
    RESTORED_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09 RESTORED_DIRTY_LINES=0
    CASE=R3_DEAD_TARGET_REMOVED
    PASS: fixture path 없는 항목 → 불합격 (exit=1)
    FAIL: fixture 죽은 target → 불합격 (기대 exit=1, 실제 0)
    CHECKED: 15
    CASE_RC=1
    RESTORED_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09 RESTORED_DIRTY_LINES=0

→ 뭘 시켰나: 규칙 2와 3을 한 번에 하나씩 제거했습니다.  
→ 뭐가 나왔나: 제거한 규칙의 fixture만 잘못 성공하고 다른 fixture는 계속 실패했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 두 음성 fixture가 서로 독립입니다.

## 3. 규칙별 변형과 구현자 주장 반증

    CASE=R1_ID_UNIQUENESS_NEUTRALIZED_VALID
    BASH_N_RC=0
    FAIL: id 중복 → 불합격 (기대 exit=1, 실제 0)
    CHECKED: 15
    CASE_RC=1
    RESTORED_DIRTY_LINES=0
    CASE=R2_PATH_EXISTENCE_REMOVED
    BASH_N_RC=0
    FAIL: fixture path 없는 항목 → 불합격 (기대 exit=1, 실제 0)
    CHECKED: 15
    CASE_RC=1
    RESTORED_DIRTY_LINES=0
    CASE=R3_DEAD_TARGET_REMOVED
    BASH_N_RC=0
    FAIL: fixture 죽은 target → 불합격 (기대 exit=1, 실제 0)
    CHECKED: 15
    CASE_RC=1
    RESTORED_DIRTY_LINES=0
    CASE=R4_CI_JOB_MATCH_NEUTRALIZED_VALID
    BASH_N_RC=0
    FAIL: ci_mirror_job 불일치 → 불합격 (기대 exit=1, 실제 0)
    CHECKED: 15
    CASE_RC=1
    RESTORED_DIRTY_LINES=0

→ 뭘 시켰나: ID 유일성, 경로 실존, 죽은 명령, 서버 작업명 조건을 각각 무력화했습니다.  
→ 뭐가 나왔나: 규칙 1~4는 담당 음성 입력이 잘못 성공한 것을 전체 인수 검사가 잡았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 규칙 1~4 시험 보호는 작동합니다.

처음 잘못 만든 변형 원문:

    CASE=R1_ID_UNIQUENESS_REMOVED
    scripts/verify/check-mechanism-registry.sh: line 115: syntax error near unexpected token '}'
    BASH_N_RC=2
    CASE=R4_CI_JOB_MATCH_REMOVED
    scripts/verify/check-mechanism-registry.sh: line 94: syntax error near unexpected token ';;'
    BASH_N_RC=2

→ 뭘 시켰나: 첫 시도에서 조건 블록 세 줄을 통째로 삭제했습니다.  
→ 뭐가 나왔나: 검증 행위가 아니라 셸 문법이 깨졌습니다.  
→ 좋은 소식인가 나쁜 소식인가: 유효한 증거가 아니어서 위의 문법 보존 변형으로 다시 했습니다.

수동 실행권한 조건만 제거한 반례의 전체 출력:

    CASE=BASELINE_MANUAL_NONEXEC
    -rw-r--r--@ 1 kangsangmo wheel 1157 ... docs/sot/mechanism-registry.yaml
    FAIL: manual-nonexec — manual path 가 실행권한 없음 — docs/sot/mechanism-registry.yaml
    CHECKED: 1
    BASELINE_CHECKER_RC=1
    CASE=R5_EXECUTABLE_CHECK_ONLY_NEUTRALIZED
    -        elif [ ! -x "$e_path" ]; then
    +        elif false; then
    BASH_N_RC=0
    PASS: manual-nonexec (manual)
    CHECKED: 1
    DIRECT_MUTANT_RC=0
    PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
    PASS: fixture 정상 명부 → 통과 (exit=0)
    PASS: fixture path 없는 항목 → 불합격 (exit=1)
    PASS: fixture 죽은 target → 불합격 (exit=1)
    PASS: id 중복 → 불합격 (exit=1)
    PASS: 알 수 없는 stage → 불합격 (exit=1)
    PASS: manual 인데 사유 없음 → 불합격 (exit=1)
    PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
    PASS: 항목 0개 명부 → NOT_RUN (exit=2)
    PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
    PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
    PASS: 빈 문자열 path → 불합격 (exit=1)
    PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
    PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
    PASS: 저장소 무오염 (시작/종료 상태 동일)
    CHECKED: 15
    CASE_RC=0
    RESTORED_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09 RESTORED_DIRTY_LINES=0

→ 뭘 시켰나: 존재하지만 실행할 수 없는 파일을 먼저 거부하는지 본 뒤 실행권한 조건만 거짓으로 바꿨습니다.  
→ 뭐가 나왔나: 직접 반례와 전체 15개 검사가 모두 성공했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 규칙 5가 시험으로 보호되지 않는 높은 결함입니다.

사전 커밋과 CI target을 각각 거짓으로 바꾼 결과:

    CASE=M5A_PRECOMMIT_REGISTRY_TARGET_FAKE
    +  target: "bash scripts/fake-never-called.sh"
    FAIL: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (기대 exit=0, 실제 1)
    CHECKED: 15
    CASE_RC=1
    RESTORED_DIRTY_LINES=0
    CASE=M5B_CI_REGISTRY_TARGET_FAKE
    +  target: "run: bash scripts/fake-never-called.sh"
    PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
    PASS: fixture 정상 명부 → 통과 (exit=0)
    PASS: fixture path 없는 항목 → 불합격 (exit=1)
    PASS: fixture 죽은 target → 불합격 (exit=1)
    PASS: id 중복 → 불합격 (exit=1)
    PASS: 알 수 없는 stage → 불합격 (exit=1)
    PASS: manual 인데 사유 없음 → 불합격 (exit=1)
    PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
    PASS: 항목 0개 명부 → NOT_RUN (exit=2)
    PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
    PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
    PASS: 빈 문자열 path → 불합격 (exit=1)
    PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
    PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
    PASS: 저장소 무오염 (시작/종료 상태 동일)
    CHECKED: 15
    CASE_RC=0
    RESTORED_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09 RESTORED_DIRTY_LINES=0

→ 뭘 시켰나: 구현자가 M5로 적은 “registry_fake_target”을 두 단계에 각각 적용했습니다.  
→ 뭐가 나왔나: 사전 커밋 거짓값은 잡고 CI 거짓값은 전체 성공했습니다.  
→ 좋은 소식인가 나쁜 소식인가: M5 일반화와 핵심 명부 계약을 반증했습니다.

## 4. CHECKED 정확값 15

    CASE=M6_ONE_ACCEPTANCE_CHECK_DELETED
    -expect_rc "빈 문자열 path → 불합격" "$TMP/empty-value.yaml" 1
    BASH_N_RC=0
    PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
    PASS: fixture 정상 명부 → 통과 (exit=0)
    PASS: fixture path 없는 항목 → 불합격 (exit=1)
    PASS: fixture 죽은 target → 불합격 (exit=1)
    PASS: id 중복 → 불합격 (exit=1)
    PASS: 알 수 없는 stage → 불합격 (exit=1)
    PASS: manual 인데 사유 없음 → 불합격 (exit=1)
    PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
    PASS: 항목 0개 명부 → NOT_RUN (exit=2)
    PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
    PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
    PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
    PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
    PASS: 저장소 무오염 (시작/종료 상태 동일)
    FAIL: 검사 수 14 ≠ 계약값 15 — 검사가 사라졌거나 무단 추가됐다
    CHECKED: 14
    CASE_RC=1
    RESTORED_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09 RESTORED_DIRTY_LINES=0

→ 뭘 시켰나: 인수 항목 한 줄을 실제로 삭제해 수를 14로 만들었습니다.  
→ 뭐가 나왔나: 마지막 정확값 확인이 종료값 1로 막았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 항목 4에는 반례를 찾지 못했습니다.

정상 전체 인수 출력:

    PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
    PASS: fixture 정상 명부 → 통과 (exit=0)
    PASS: fixture path 없는 항목 → 불합격 (exit=1)
    PASS: fixture 죽은 target → 불합격 (exit=1)
    PASS: id 중복 → 불합격 (exit=1)
    PASS: 알 수 없는 stage → 불합격 (exit=1)
    PASS: manual 인데 사유 없음 → 불합격 (exit=1)
    PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
    PASS: 항목 0개 명부 → NOT_RUN (exit=2)
    PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
    PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
    PASS: 빈 문자열 path → 불합격 (exit=1)
    PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
    PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
    PASS: 저장소 무오염 (시작/종료 상태 동일)
    CHECKED: 15
    ACCEPTANCE_RC=0

→ 뭘 시켰나: 변형 전 HEAD에서 전체 인수 검사를 실행했습니다.  
→ 뭐가 나왔나: 현재 산출물은 15개 성공과 종료값 0을 냅니다.  
→ 좋은 소식인가 나쁜 소식인가: 정상 기준선은 서지만 위 반례 때문에 합격증은 아닙니다.

## 5. 저장소 무오염과 임시 파일 잔존

    TREE_IDENTICAL_RC=0
    HASH_IDENTICAL_RC=0
    STATUS_IDENTICAL_RC=0
    TMP_IDENTICAL_RC=1
    BEFORE_STATUS_BEGIN
    !! .omc/
    !! .secret-patterns
    BEFORE_STATUS_END
    AFTER_STATUS_BEGIN
    !! .omc/
    !! .secret-patterns
    AFTER_STATUS_END
    TMP_AFTER_BEGIN
    /private/tmp/codex-v1-ac-m.JYXMvL/acceptance-tmp/xcrun_db
    TMP_AFTER_END

→ 뭘 시켰나: Git 상태뿐 아니라 모든 경로·권한과 파일 내용 지문, 빈 전용 임시 폴더를 전후 비교했습니다.  
→ 뭐가 나왔나: 저장소 내부 세 비교는 동일했지만 전용 임시 폴더에는 xcrun_db가 남았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 저장소 무오염은 확인됐으나 임시 잔존물은 낮은 결함입니다.

    $ stat acceptance-tmp/xcrun_db
    TYPE=Regular File MODE=-rw------- SIZE=491
    GIT_ONLY_BEFORE=0
    TMPDIR=tmp-git-only git status --porcelain
    GIT_ONLY_RC=0
    Regular File|-rw-------|491|tmp-git-only/xcrun_db
    CHECKER_ONLY_BEFORE=0
    TMPDIR=tmp-checker-only checker registry.yaml
    CHECKER_ONLY_RC=0
    CHECKER_ONLY_AFTER=[출력 없음]

→ 뭘 시켰나: git status와 검사기를 각각 빈 임시 폴더에서 단독 실행했습니다.  
→ 뭐가 나왔나: macOS git status만 491바이트 캐시를 만들었고 검사기 단독은 만들지 않았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 원인은 인수 검사의 상태 확인에서 호출되는 운영체제 도구로 좁혀졌습니다.

## 6. 명부 target 3항목 문자 일치

    ENTRY_COUNT=3
    ID=secrets-scan-precommit
    PATH=hooks/pre-commit
    TARGET=SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh
    MATCH_COUNT=1
    MATCH_LINE=73:  SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh >/dev/null 2>&1 || vrc=$?
    ID=acceptance-glob-prepush
    PATH=hooks/pre-push
    TARGET=-name 'verify.sh' -o -name 'acceptance-*.sh'
    MATCH_COUNT=1
    MATCH_LINE=112:found=$(find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \) \
    ID=ci-secret-scan
    PATH=.github/workflows/verify.yml
    TARGET=run: bash verify.sh
    MATCH_COUNT=1
    MATCH_LINE=26:        run: bash verify.sh

→ 뭘 시켰나: 명부를 YAML로 읽은 뒤 각 target을 지정 path 파일에서 고정 문자열로 찾았습니다.  
→ 뭐가 나왔나: 세 문자열이 각각 정확히 한 줄에서 발견됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 명부 값에는 반례를 찾지 못했습니다.

## 7. 계약 밖 YAML 입력

4칸 들여쓰기·탭·값 없는 필수 path·모르는 키의 거부 출력:

    CASE=four-space-indent.yaml
    FAIL: 파서 계약 밖의 줄 —     path: "hooks/pre-commit"
    FAIL: 파서 계약 밖의 줄 —     target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
    FAIL: 파서 계약 밖의 줄 —     stage: "pre-commit"
    FAIL: 파서 계약 밖의 줄 —     required: true
    FAIL: four-space — path 누락/빈 값
    CHECKED: 1
    CASE_RC=1
    CASE=tab-indent.yaml
    FAIL: 파서 계약 밖의 줄 — [TAB]path: "hooks/pre-commit"
    FAIL: 파서 계약 밖의 줄 — [TAB]target: "SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh"
    FAIL: 파서 계약 밖의 줄 — [TAB]stage: "pre-commit"
    FAIL: 파서 계약 밖의 줄 — [TAB]required: true
    FAIL: tab-indent — path 누락/빈 값
    CHECKED: 1
    CASE_RC=1
    CASE=empty-path.yaml
    FAIL: empty-path — path 누락/빈 값
    CHECKED: 1
    CASE_RC=1
    CASE=unknown-key.yaml
    FAIL: 알 수 없는 키 — surprise
    PASS: unknown-key (pre-commit)
    CHECKED: 1
    CASE_RC=1

→ 뭘 시켰나: 사용자가 지정한 4칸·탭·값 없음과 추가 모르는 키를 넣었습니다.  
→ 뭐가 나왔나: 이 네 종류는 종료값 1로 거부했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 이 경계들은 잘 막습니다.

조용히 성공한 계약 밖 입력 전체:

    CASE=duplicate-path.yaml
    INPUT: path: "scripts/does-not-exist.sh"
    INPUT: path: "hooks/pre-commit"
    PASS: duplicate-path (pre-commit)
    CHECKED: 1
    CASE_RC=0

    CASE=duplicate-ci-job.yaml
    INPUT: ci_mirror_job: "not-a-job"
    INPUT: ci_mirror_job: "verify"
    PASS: duplicate-ci-job (ci)
    CHECKED: 1
    CASE_RC=0

    CASE=inline-comment-id.yaml
    INPUT: - id: "inline-comment" # parser contract allows only whole-line comments
    PASS: "inline-comment" # parser contract allows only whole-line comments (pre-commit)
    CHECKED: 1
    CASE_RC=0

    CASE=inline-comment-manual-reason.yaml
    INPUT: manual_reason: "human run" # inline comments are outside the parser contract
    PASS: inline-comment-manual (manual)
    CHECKED: 1
    CASE_RC=0

    CASE=unbalanced-id-quote.yaml
    INPUT: - id: "unbalanced-id
    PASS: "unbalanced-id (pre-commit)
    CHECKED: 1
    CASE_RC=0

    CASE=empty-optional-key.yaml
    INPUT: ci_mirror_job:
    INPUT: stage: "pre-commit"
    PASS: empty-optional (pre-commit)
    CHECKED: 1
    CASE_RC=0

    CASE=extra-manual-reason.yaml
    INPUT: stage: "pre-commit"
    INPUT: manual_reason: "manual is not this entry stage"
    PASS: extra-manual-reason (pre-commit)
    CHECKED: 1
    CASE_RC=0

    CASE=outside-repository-path.yaml
    INPUT: path: "/bin/sh"
    INPUT: stage: "manual"
    PASS: outside-repository (manual)
    CHECKED: 1
    RC=0

→ 뭘 시켰나: 중복 필드, 인라인 주석, 닫히지 않은 따옴표, 값 없는 비해당 키, 단계와 맞지 않는 필드, 절대경로를 넣었습니다.  
→ 뭐가 나왔나: 여덟 입력이 모두 PASS와 종료값 0을 냈습니다.  
→ 좋은 소식인가 나쁜 소식인가: “유일한 형식 밖은 종료값 1”이라는 §10 계약을 직접 깨는 나쁜 소식입니다.

성공은 아니지만 종료값이 틀린 입력:

    CASE=leading-indent-item.yaml
    INPUT:   - id: "leading-indent-item"
    FAIL: 파서 계약 밖의 줄 —   - id: "leading-indent-item"
    NOT_RUN: 항목 0개 — 0건 대조로 통과는 금지한다 (P20)
    CHECKED: 0
    CASE_RC=2
    CASE=document-marker.yaml
    INPUT: ---
    FAIL: 파서 계약 밖의 줄 — ---
    PASS: document-marker (pre-commit)
    CHECKED: 1
    CASE_RC=1

→ 뭘 시켰나: 인식되지 않는 항목 시작과 YAML 문서 시작 표시를 넣었습니다.  
→ 뭐가 나왔나: 둘 다 FAIL 문구가 나왔지만, 인식 항목 0개인 첫 경우는 계약상 1이 아니라 2였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 조용한 성공은 아니어도 종료값 계약 불일치입니다.

## 8. 입력·출력·종료값 계약

    CASE=DEFAULT_INPUT
    PASS: secrets-scan-precommit (pre-commit)
    PASS: acceptance-glob-prepush (pre-push)
    PASS: ci-secret-scan (ci)
    CHECKED: 3
    RC=0 RESULT_LINES=3 LAST=CHECKED: 3
    CASE=MISSING_REGISTRY
    NOT_RUN: 명부 없음 — .../does-not-exist.yaml
    CHECKED: 0
    RC=2 LAST=CHECKED: 0
    CASE=COMMENTS_ONLY
    NOT_RUN: 항목 0개 — 0건 대조로 통과는 금지한다 (P20)
    CHECKED: 0
    RC=2 LAST=CHECKED: 0
    CASE=PARSER_ERROR_ZERO_ENTRIES
    FAIL: 파서 계약 밖의 줄 —   - id: "leading-indent-item"
    NOT_RUN: 항목 0개 — 0건 대조로 통과는 금지한다 (P20)
    CHECKED: 0
    RC=2 LAST=CHECKED: 0
    CASE=WORKFLOW_OVERRIDE_MISSING
    PASS: secrets-scan-precommit (pre-commit)
    FAIL: ci-secret-scan — ci_mirror_job 'verify' 이(가) .../does-not-exist.yml 의 jobs: 키에 없다
    CHECKED: 2
    RC=1 LAST=CHECKED: 2

→ 뭘 시켰나: 기본 입력, 없는 명부, 주석뿐인 명부, 문법 오류 0항목, WORKFLOW_FILE(시험할 서버 설정 파일을 바꾸는 환경값) 교체를 실행했습니다.  
→ 뭐가 나왔나: 기본 0·일반 위반 1·없음과 빈 명부 2·마지막 CHECKED 줄은 작동했지만 문법 오류 0항목도 2였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 입력 환경값과 마지막 줄은 맞고, 문법 오류 종료값과 규칙별 출력은 계약과 다릅니다.

출력 수 대조:

    실제 명부 항목 수=3
    PASS/FAIL/NOT_RUN 결과 줄 수=3
    goal §10 요구=항목·규칙마다 PASS:/FAIL: 줄
    checker 실제=scripts/verify/check-mechanism-registry.sh:111-115에서 항목마다 한 줄

→ 뭘 시켰나: 실행 결과 줄 수와 goal의 출력 계약을 직접 비교했습니다.  
→ 뭐가 나왔나: 항목별 한 줄만 있고 다섯 규칙별 줄은 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: 검사 결과 추적성이 계약보다 약합니다.

## 9. 현재 CI 단계와 SOT, 삭제 방어

현재 워크플로를 Ruby YAML로 실제 해석한 출력:

    MATCHING_STEPS=1
    NAME=인수 검사 verify-ac-m (mechanism 명부 대조 · AC-M)
    RUN=bash scripts/acceptance-verify-ac-m.sh
    HAS_IF=false
    IF_VALUE=nil
    CI_IF_COUNT=0 CI_EXACT_RUN_COUNT=1 SOT_EXACT_COUNT=1
    .github/workflows/verify.yml:156:        run: bash scripts/acceptance-verify-ac-m.sh
    docs/sot/verification-commands.md:28:bash scripts/acceptance-verify-ac-m.sh

→ 뭘 시켰나: 서버 설정을 구조로 읽어 정확한 실행 단계 수와 조건 유무를 확인하고 SOT의 명령과 대조했습니다.  
→ 뭐가 나왔나: 현재는 정확히 한 번, 조건 없이 활성화돼 있고 SOT에도 같은 명령이 한 번 있습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 상태 자체는 항목 9를 만족합니다.

조건을 항상 거짓으로 만든 반례의 전체 출력:

    CASE=CI_ACM_STEP_DISABLED_WITH_FALSE_CONDITION
    if: ${{ false }}
    run: bash scripts/acceptance-verify-ac-m.sh
    PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
    PASS: fixture 정상 명부 → 통과 (exit=0)
    PASS: fixture path 없는 항목 → 불합격 (exit=1)
    PASS: fixture 죽은 target → 불합격 (exit=1)
    PASS: id 중복 → 불합격 (exit=1)
    PASS: 알 수 없는 stage → 불합격 (exit=1)
    PASS: manual 인데 사유 없음 → 불합격 (exit=1)
    PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
    PASS: 항목 0개 명부 → NOT_RUN (exit=2)
    PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
    PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
    PASS: 빈 문자열 path → 불합격 (exit=1)
    PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
    PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
    PASS: 저장소 무오염 (시작/종료 상태 동일)
    CHECKED: 15
    CASE_RC=0
    RESTORED_DIRTY_LINES=0

→ 뭘 시켰나: AC-M 서버 단계에 항상 거짓 조건을 넣어 영구히 실행되지 않게 했습니다.  
→ 뭐가 나왔나: 전체 인수 검사는 15개 성공과 종료값 0을 냈습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 배선을 지키는 보호가 없다는 높은 결함입니다.

단계를 삭제한 반례의 전체 출력:

    CASE=CI_ACM_STEP_DELETED
    -      - name: 인수 검사 verify-ac-m (mechanism 명부 대조 · AC-M)
    -        run: bash scripts/acceptance-verify-ac-m.sh
    PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
    PASS: fixture 정상 명부 → 통과 (exit=0)
    PASS: fixture path 없는 항목 → 불합격 (exit=1)
    PASS: fixture 죽은 target → 불합격 (exit=1)
    PASS: id 중복 → 불합격 (exit=1)
    PASS: 알 수 없는 stage → 불합격 (exit=1)
    PASS: manual 인데 사유 없음 → 불합격 (exit=1)
    PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
    PASS: 항목 0개 명부 → NOT_RUN (exit=2)
    PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
    PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
    PASS: 빈 문자열 path → 불합격 (exit=1)
    PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
    PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
    PASS: 저장소 무오염 (시작/종료 상태 동일)
    CHECKED: 15
    CASE_RC=0
    RESTORED_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09 RESTORED_DIRTY_LINES=0

→ 뭘 시켰나: AC-M 서버 단계 다섯 줄을 완전히 삭제했습니다.  
→ 뭐가 나왔나: SOT는 그대로인데도 전체 인수 검사가 성공했습니다.  
→ 좋은 소식인가 나쁜 소식인가: P15③이 요구하는 서버 배선 보장이 비어 있습니다.

## 코딩 원칙과 변경 위생

    $ git diff --check 0459a37..f038c24
    DIFF_CHECK_RC=0
    $ git diff --numstat 0459a37..f038c24 -- [지정 산출물]
    6   0 .github/workflows/verify.yml
    176 0 docs/engineering/verify-ac-m-goal-2026-08-12.md
    24  0 docs/sot/mechanism-registry.yaml
    1   0 docs/sot/verification-commands.md
    184 0 scripts/acceptance-verify-ac-m.sh
    167 0 scripts/verify/check-mechanism-registry.sh
    7   0 scripts/verify/fixtures/mechanism-registry/dead-target.yaml
    10  0 scripts/verify/fixtures/mechanism-registry/missing-path.yaml
    13  0 scripts/verify/fixtures/mechanism-registry/normal.yaml
    flush_entry_start=52 end=118 lines=67
    expect_rc_start=37 end=48 lines=12

→ 뭘 시켰나: 공백 오류, 변경 크기, 함수 줄 수를 실행으로 측정했습니다.  
→ 뭐가 나왔나: 공백 오류와 파일 hard 600줄은 문제없고 flush_entry만 soft 60줄을 7줄 넘었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 즉시 실패는 아니지만 낮은 유지보수 위험입니다.

## 최종 원복·원본 무오염 증거

    TARGET_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09
    TARGET_BRANCH=task/verify-ac-m
    TARGET_TRACKED_DIFF_RC=0
    TARGET_STATUS_BASELINE_MATCH_RC=0
    TARGET_TREE_BASELINE_MATCH_RC=0
    TARGET_HASH_BASELINE_MATCH_RC=0
    TARGET_FINAL_STATUS_BEGIN
    !! .omc/
    !! .secret-patterns
    TARGET_FINAL_STATUS_END
    CLONE_HEAD=f038c24daf07a02c976bb8895cd7cd2df1da4c09
    CLONE_DIRTY_LINES=0
    SOURCE_BARE=true
    SOURCE_TASK_REF=f038c24daf07a02c976bb8895cd7cd2df1da4c09

→ 뭘 시켰나: 모든 실험 뒤 대상 HEAD·브랜치·추적 차이·무시 파일 포함 상태·경로·내용 지문과 격리 복제본 상태를 다시 확인했습니다.  
→ 뭐가 나왔나: 대상은 시작 기준과 전부 같고 복제본도 지정 HEAD의 깨끗한 상태이며 원본 브랜치 참조도 그대로입니다.  
→ 좋은 소식인가 나쁜 소식인가: 원본과 대상 워크트리를 변경하지 않았다는 좋은 소식입니다.

# 최종 판정

확인된 현재 정상 동작은 bash 3.2 실행, fixture 분리, CHECKED 15 강제, 실제 target 3개 일치, 현재 CI·SOT 등록입니다. 그러나 수동 실행권한 보호, CI target 진실성, CI 배선 보호라는 핵심 세 지점에서 전체 성공 반례가 있으므로 PR #8 AC-M은 FAIL입니다.

※ 이 판정은 지정 HEAD f038c24daf07a02c976bb8895cd7cd2df1da4c09의 로컬 실행 결과입니다. GitHub 원격 실행 기록은 확인하지 않았습니다.

# 판정문 형식 확인

    $ bash /Users/kangsangmo/.claude/skills/strict/brief-lint.sh codex-v1-verdict-ac-m.md
    코드블록 0개 (예시 제외 0개) / 해석 누락 0개 · 부실 0개
    표 해석: 이상 없음
    1층(결론): 줄 3 / 본문 229자
    1층 전문용어: 0개
    결정 카드 4건 완비 / 불완전 0건
    증거 보관 경로: 이상 없음 (실재 확인 3건)
    브리핑 계약 기계 검사: 위반 0건 (문서 1개)
    BRIEF_LINT_RC=0

→ 뭘 시켰나: strict 브리핑 형식 검사로 결론 표현, 표 해석, 결정 카드, 증거 경로를 점검했습니다.  
→ 뭐가 나왔나: 형식 위반 0건이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 판정문 형식에는 좋은 소식이지만, 이 수치는 문서 형식만 증명하며 회사 차원의 코드 합격 근거는 아닙니다.
