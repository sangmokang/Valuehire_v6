VERDICT: FAIL

> 역사 판정 기록(현재 수치 아님): 아래 `완전 8 / 부분 10`은 이 V1 실행 당시의 과거 초안 집계다. 현재 정본 집계는 `완전 1 / 부분 12 / 없음 7 / 해당없음 4 / 미확인 8`이며 `docs/sot/principles.yaml`을 Psych로 다시 계산한다.

# 결론

지금 상태로는 승인하시면 안 됩니다. 필수 원칙 하나를 엉뚱한 이름으로 바꾸거나 문법이 깨진 값을 넣어도 검사가 정상이라고 보고합니다.

좋았던 상태를 나쁜 상태로 낮추는 시험은 작업 중인 파일에서는 막았지만, 실제 전송 때처럼 변경을 저장한 뒤에는 막지 못했습니다. 따라서 운영에서 가장 필요한 보호 기능이 작동하지 않습니다.

“완전”이라고 적힌 8개 중 직접 확인한 P11은 이번에 검토한 코드에 자동 확인 장치가 아예 없었고, P16은 요구한 세 장치 중 한 장치만 확인됐습니다. 상태표를 다음 작업의 사실 자료로 쓰면 이미 끝난 일로 오판할 수 있습니다.

# 판단 근거

## 확인 범위와 한계

※ 이번에 확인하지 못한 사항: V-1·V-2·V-5가 인용한 2026-08-18 과거 작업 전체는 다시 만들지 않았습니다. 두 strict SKILL.md 파일을 누가 01:34:33에 바꿨는지도 현재 자료만으로 특정하지 못했습니다. 원격 서버 검사는 PR이 없어 실행하지 않았습니다.

※ 중간 실패 후 다시 한 사항: P16 실행은 처음에 사용자 캐시 접근 권한 때문에 실행되지 않았습니다. 별도 임시 캐시와 오프라인 설정으로 다시 실행해 25개 시험과 실제 모듈 불러오기가 통과함을 확인했습니다. 임시 복제본 삭제는 시스템 휴지통 권한 때문에 두 번 실패한 뒤, 검증한 정확한 임시 경로만 삭제했고 저장소가 깨끗함을 다시 확인했습니다.

※ 문서 검증 재시도: 첫 형식 검사에서 결론에 기술 표기 2건이 잡혀 확인 범위 절로 옮겼고, 두 번째 검사는 위반 0건이었습니다. 새 파일을 임시 등록해 git diff --check를 실행하려던 시도는 공용 git 색인 잠금 권한 때문에 실패했습니다. 대신 새 파일과 빈 파일을 직접 비교하는 검사와 줄 끝 공백 독립 검사를 실행했고, 처음 발견된 공백 줄 14개를 제거한 뒤 위반 0건을 확인했습니다.

## 왜 FAIL로 판단했는가

AC1의 스키마(파일에 반드시 있어야 하는 항목과 형식) 기준은 현재 파일이 우연히 32개와 6개 필드를 갖는지만 묻는 것이 아닙니다. 검사기가 앞으로도 P1~P22, §1-B-1~5, V-1~V-5라는 정확한 32개 이름과 유효한 YAML(사람과 프로그램이 함께 읽는 설정 파일 형식)을 지켜야 합니다.

검사기는 항목 수와 중복만 셉니다. P1을 P999로 바꿔도 32개라는 숫자가 그대로여서 통과했습니다. 또 값의 맨 앞과 맨 뒤에 큰따옴표가 있다는 이유만으로 중간의 잘못된 큰따옴표를 받아들였습니다. 독립 YAML 해석기는 같은 파일을 문법 오류로 거부했습니다. 이는 fail-closed(계약 밖 입력은 통과시키지 않고 멈추는 방식)라는 선례와 반대입니다.

AC3의 좁은 시험만 보면 통과입니다. 커밋하지 않은 P11 상태를 완전에서 없음으로 바꾸자 종료값(exit code, 명령이 성공 또는 실패를 숫자로 돌려주는 값) 1로 막았습니다. 그러나 실제 pre-push(전송 직전에 자동으로 도는 검사)는 작업 중인 변경이 하나라도 있으면 먼저 멈추므로, 상태 하락은 이미 커밋된 뒤에 검사됩니다. 그때 스크립트는 이전 커밋이 아니라 HEAD(현재 커밋)의 파일과 현재 작업 파일을 비교합니다. 둘은 같은 파일이므로 실제 회귀 방지 장치(ratchet, 좋아진 상태가 다시 나빠지지 못하게 막는 장치)는 하락을 놓칩니다.

버린 해석은 “요청서에 적힌 작업 파일 변형 시험이 1을 반환했으므로 AC3는 합격”입니다. 이 해석은 실제 전송 시점에는 존재할 수 없는 더러운 작업 상태만 시험하고, 운영 경로에서 이미 커밋된 하락을 놓치므로 버렸습니다.

AC2의 glob(파일 이름 규칙으로 자동 수집하는 방식) 자동 편입은 실제로 확인됐습니다. 출력 목록에 새 스크립트가 나타났고, pre-push의 실행부는 검사 결과가 0이 아니면 전체 전송을 막도록 연결돼 있습니다. 다만 AC3 검사기 자체가 커밋된 하락에 0을 돌려주므로, 연결이 정상이어도 잘못된 성공을 그대로 전달합니다.

AC4·AC5는 “이번 판에서 두 SKILL.md를 손대지 않았다”는 주장을 확인할 수 없습니다. 두 파일 모두 goal 문서 작성 시각 01:26:59보다 뒤인 01:34:33에 함께 수정됐습니다. 8월 12일 백업과 현재 Claude 파일도 다릅니다. 수정 주체를 보여 주는 기록이 없으므로 거짓이라고 단정하지 않고 ※ 미확인으로 판정했습니다.

## 갈림길과 버린 해석

1. 현재 YAML이 정상인가와 검사기가 잘못된 미래 YAML을 막는가는 다른 질문입니다. 현재 파일은 독립 해석기로 32개·6개 필드가 맞았지만, 변조 파일도 검사기가 통과했으므로 AC1 보호 기능은 불합격으로 보았습니다.
2. P11 장치가 다른 브랜치에 있다는 사실을 현재 브랜치의 완전 판정으로 인정하지 않았습니다. 전송되는 대상 브랜치와 main에는 파일이 없고, 별도 task/file-size-gate 브랜치에만 있으므로 현재 운영 장치가 아닙니다.
3. P16에서 실행 가능한 실제 모듈 불러오기 하나가 통과했다는 이유로 세 요구를 모두 충족했다고 보지 않았습니다. 파일명 규칙 검사와 상관관계 계산 장치를 찾지 못했기 때문입니다.
4. SKILL.md의 수정 시각이 늦다는 이유만으로 이번 구현자가 바꿨다고 단정하지 않았습니다. 시각은 변경 사실만 보여 주고 변경 주체는 보여 주지 않으므로 미확인으로 남겼습니다.

## 이 판정이 틀리면 무엇이 깨지는가

- AC1 결함을 놓치면 원칙 하나가 사라지거나 설정 파일이 읽을 수 없게 망가져도 자동 검사가 승인합니다. 다음 작업자는 불완전한 상태표를 완전한 사실로 믿게 됩니다.
- AC3 결함을 놓치면 누군가 상태를 완전에서 없음으로 낮춰 커밋해도 전송이 허용됩니다. “한 번 확보한 보호 수준은 낮아지지 않는다”는 운영 약속이 실제로 지켜지지 않습니다.
- P11·P16 과장 판정을 놓치면 아직 없는 보호 장치를 이미 있다고 보고 후속 구현을 생략합니다. 큰 코드 변경과 약한 시험이 다시 들어올 가능성이 커집니다.
- AC4·AC5를 근거 없이 합격 처리하면 저장소 밖 핵심 지침이 언제, 누구에 의해 바뀌었는지 추적하지 못한 채 동기화됐다고 보고하게 됩니다.

## 결함과 사업 영향

| 번호 | 심각도 | 확인된 결함 | 그대로 두면 생기는 일 |
|---|---|---|---|
| D1 | 높음 | 필수 ID 집합을 검사하지 않아 P1을 P999로 바꿔도 통과 | 원칙이 빠진 상태표가 정상 자료로 배포됩니다. |
| D2 | 높음 | 깨진 큰따옴표가 든 YAML을 정상으로 판정 | 다른 표준 도구가 파일을 읽지 못해 자동화가 중단되거나 서로 다른 결과를 냅니다. |
| D3 | 치명적 | 커밋된 상태 하락을 현재 커밋과 비교해 놓침 | 보호 수준을 낮춘 커밋이 실제 전송 단계에서 그대로 승인됩니다. |
| D4 | 높음 | P11의 완전 근거 파일이 대상 브랜치와 main에 없음 | 코드 크기 제한이 있다고 믿고 큰 변경을 승인할 수 있습니다. |
| D5 | 중간 | P16의 세 요구 중 실제 모듈 불러오기만 확인 | 소스 문자열만 보는 약한 시험과 품질 악화 신호가 계속 남습니다. |
| D6 | 중간 | AC4·AC5 수정 주체를 확인할 기록 없음 | 저장소 밖 핵심 지침 변경을 책임 있게 추적할 수 없습니다. |

→ 무엇을 보여 주나 / D1~D6의 기술 심각도와 사업상 결과를 함께 적었습니다. / D3 때문에 전체 판정은 FAIL입니다.

## AC별 판정과 반증 기록

| AC | 판정 | 반증 시도와 결과 |
|---|---|---|
| AC1 | FAIL | evidence 필드를 삭제해 깨뜨리려 하자 실패로 막았습니다. 그러나 P1을 P999로 바꿔 깨뜨리자 정상으로 통과했고, 값 안에 잘못된 큰따옴표를 넣어 깨뜨리자 역시 정상으로 통과했습니다. |
| AC2 | PASS | 파일명이 자동 목록에 안 잡히거나 결과가 무시되는지 깨뜨리려 했습니다. 실제 목록 20번째에 나타났고, hooks/pre-push:165-169는 실패값을 전체 차단으로 바꾸므로 이 반증은 실패했습니다. |
| AC3 | FAIL | 작업 파일에서 완전→없음으로 낮추자 실패값 1이 나와 좁은 반증은 실패했습니다. 같은 하락을 격리 복제본에서 커밋한 뒤 다시 실행하자 정상값 0이 나와 실제 운영 반증은 성공했습니다. |
| AC4 | ※ 미확인 | 분리 계획이 goal 문서에 없도록 깨뜨릴 수 있는지 확인했으나 §분리 계획 표가 있어 이 반증은 실패했습니다. 다만 Claude SKILL.md는 goal 작성 뒤 수정돼 “이번 판 미수정” 주장은 확인하지 못했습니다. |
| AC5 | ※ 미확인 | 두 SKILL.md 중 한쪽만 이번에 바뀌었는지 시각과 백업 차이로 확인하려 했습니다. 두 파일 수정 시각은 같지만 goal보다 늦고 변경 주체 기록이 없어 합격·불합격 어느 쪽도 확정하지 못했습니다. |

→ 무엇을 보여 주나 / 각 기준을 어떤 방법으로 깨뜨렸고 성공 또는 실패했는지 한 줄씩 남겼습니다. / AC1과 AC3의 핵심 보호 기능이 실제로 깨졌습니다.

# 기술 상세와 증거 원문

## 1. 대상과 전체 변경 내용

확인 대상은 브랜치 task/strict-principles-yaml, 변경 범위 03ad76f..804a39c입니다. 검사 시작 전 git status --porcelain은 출력이 없어 깨끗했습니다.

명령:

    git branch --show-current
    git status --porcelain

출력:

    task/strict-principles-yaml

→ 무엇을 시켰나 / 브랜치 이름과 미커밋 변경 유무를 확인했습니다. / 대상 브랜치는 맞았고 시작 상태는 깨끗했습니다.

명령:

    git show 03ad76f..804a39c

출력 전문:

    commit 804a39c72cf96cbd1c88eb836a18f31245bdd564
    Author: acceptance <acceptance@local>
    Date:   Wed Aug 19 01:32:10 2026 +0900

        feat(sot): principles.yaml 신설 + 스키마/회귀 검사 스크립트 (GREEN)

        P1 키스톤 요구사항 구현: P1~P22+§1-B 5조+V1~V5 총 32항목을 2026-08-19 실측
        근거(fork 조사)로 채워 넣고, 스키마 완전성 + status 회귀(ratchet) 검사를
        pyyaml 의존 없이 표준 파이썬 파서로 구현. mechanism-registry.yaml 파서
        관례(fail-closed, 계약 밖 형태 거부)를 그대로 계승.

    diff --git a/docs/sot/principles.yaml b/docs/sot/principles.yaml
    new file mode 100644
    index 0000000..2f103df
    --- /dev/null
    +++ b/docs/sot/principles.yaml
    @@ -0,0 +1,229 @@
    +# docs/sot/principles.yaml
    +# P1의 키스톤 요구사항("principles.yaml 전 항목이 mechanism을 갖고 CI가 확인") 구현.
    +# 원문(principle 필드)의 정본은 docs/sot/coding-principles.md — 표현이 갈리면 그쪽이 맞다.
    +# status 값은 scripts/acceptance-principles-check.sh(AC3)가 이전 커밋 대비 회귀(등급 하락)를 차단한다.
    +# 최초 작성: 2026-08-19, 실측 근거: docs/engineering/strict-principles-yaml-goal-2026-08-19.md
    +
    +- id: P1
    +  principle: "기계 장치 없는 원칙은 삭제한다 (키스톤)"
    +  mechanism_expected: "principles.yaml 전 항목이 mechanism을 갖고 CI가 확인"
    +  mechanism_found: "docs/sot/mechanism-registry.yaml + scripts/verify/check-mechanism-registry.sh (pre-push+CI 등록); 본 파일 자체"
    +  status: "부분"
    +  evidence: "mechanism-registry.yaml은 존재하고 pre-push/CI에서 실행되나 등록 3항목뿐(secrets-scan-precommit 등). 본 파일이 P1~P22 전체를 덮는 확장판."
    +
    +- id: P2
    +  principle: "인수 기준은 실행 가능한 명령이다"
    +  mechanism_expected: "PR 본문에 검증 명령+기대 출력 없으면 CI 실패"
    +  mechanism_found: null
    +  status: "없음"
    +  evidence: "find . -iname PULL_REQUEST_TEMPLATE* 결과 없음. PR 본문 파싱 CI job 없음."
    +
    +- id: P3
    +  principle: "조용한 실패 금지 (3상태 PASS/FAIL/NOT_RUN)"
    +  mechanism_expected: "3상태 판정 + bare except/catch 금지 lint + 핸들러 DB 기록"
    +  mechanism_found: "scripts/session-status.sh, scripts/scan-data-exposure.sh 등 다수가 NOT_RUN 상태 출력"
    +  status: "부분"
    +  evidence: "grep 결과 다수 acceptance-*.sh에서 NOT_RUN 사용 확인. bare except/catch lint, ?? 기본값류 금지 lint는 미발견."
    +
    +- id: P4
    +  principle: "가짜 구현 금지 (네트워크 차단 CI 레인)"
    +  mechanism_expected: "외부 효과 모듈이 네트워크 차단 레인에서 반드시 실패"
    +  mechanism_found: null
    +  status: "없음"
    +  evidence: "acceptance-hs-cleanroom*.sh 등에서 network/offline 격리 레인 전용 CI job 미발견."
    +
    +- id: P5
    +  principle: "테스트 통과용 코드 금지"
    +  mechanism_expected: "RED 이후 테스트파일 불변 검사 + 속성기반 테스트 + 뮤테이션 표본"
    +  mechanism_found: "scripts/acceptance-hs-gates-mutations.sh, acceptance-hs-cleanroom-mutations.sh 등"
    +  status: "부분"
    +  evidence: "뮤테이션 시험 다수 존재·실행 확인(2026-08-18 PR#13 세션에서 직접 실행). 속성기반 테스트(hypothesis/fast-check)는 미발견."
    +
    +- id: P6
    +  principle: "실행 환경은 제품의 일부"
    +  mechanism_expected: "launchd plist가 저장소 경로 참조시 CI 실패 + doctor/install/reconcile/status/uninstall"
    +  mechanism_found: null
    +  status: "없음"
    +  evidence: "plist는 저장소 밖(~/Library/LaunchAgents)이라 이 저장소 CI가 원리적으로 검사 불가. install-hooks.sh는 있으나 doctor/reconcile/uninstall 풀세트 미발견."
    +
    +- id: P7
    +  principle: "되돌릴 수 있어야 배포다"
    +  mechanism_expected: "이전 digest로 한 명령 롤백 + N-1 마이그레이션 호환 검사"
    +  mechanism_found: null
    +  status: "해당없음"
    +  evidence: "v6에 태그 릴리스·digest 배포 파이프라인 자체가 아직 없음."
    +
    +- id: P8
    +  principle: "단일 좌석은 lease로만 접근한다"
    +  mechanism_expected: "TTL DB lease + fencing token, 오너 Chrome 점유 감지"
    +  mechanism_found: null
    +  status: "해당없음"
    +  evidence: "3사 계정 동시접속 라이브 소싱 기능이 이 저장소 코드에 아직 없음."
    +
    +- id: P9
    +  principle: "외부 효과는 멱등키 + readback"
    +  mechanism_expected: "(position,candidate,channel) DB unique 제약 + write-ahead + readback"
    +  mechanism_found: null
    +  status: "해당없음"
    +  evidence: "발송·DB 기능 자체가 이 저장소엔 아직 없음."
    +
    +- id: P10
    +  principle: "사업 결과를 매일 박스 밖으로"
    +  mechanism_expected: "일일 접촉 후보자 수 외부 감시자 전송, 24h 0건시 알림"
    +  mechanism_found: null
    +  status: "해당없음"
    +  evidence: "AI Search·발송 기능이 아직 없어 보낼 사업 데이터 자체가 없음."
    +
    +- id: P11
    +  principle: "코드 예산 (파일/PR 크기)"
    +  mechanism_expected: "파일 soft300/hard600, 함수 soft60/hard100, 3000줄 초과 PR 절대금지"
    +  mechanism_found: "scripts/acceptance-file-size.sh (PR#14, main 병합 완료)"
    +  status: "완전"
    +  evidence: "G·V1(codex)·V2(Claude) 수렴 PASS, main 병합 완료 확인(2026-08-15)."
    +
    +- id: P12
    +  principle: "회수 — 만들기 전에 기계가 확인"
    +  mechanism_expected: "capabilities.yaml 자동생성 + 미참조 export 스캔 + gitignore 산출물 포함 + session-status.sh HEAD 재확인"
    +  mechanism_found: "scripts/session-status.sh (HEAD·origin 동기·RED 자동출력)"
    +  status: "부분"
    +  evidence: "session-status.sh는 오늘도 다회 실행 확인. capabilities.yaml 없음. gitignore 산출물 회수는 /strict 규칙 C에도 repo에도 없음(2026-08-19 확인된 갭)."
    +
    +- id: P13
    +  principle: "검사는 약화될 수 없다"
    +  mechanism_expected: "weakens-check 라벨 강제 + 억제패턴 탐지 + suppressions.yaml expiry 강제 + 자기제외 금지 + 적대검증 첨부 CI 확인"
    +  mechanism_found: "hooks/pre-push (acceptance-0-7.sh 시연 [1/6][2/6][3/6])"
    +  status: "완전"
    +  evidence: "2026-08-18 PR#13 작업 중 bash scripts/acceptance-0-7.sh 실제 출력에서 3개 위반 시연 전부 BLOCKED 직접 확인."
    +
    +- id: P14
    +  principle: "판정 수치는 코드가 만든다"
    +  mechanism_expected: "LLM 출력→판정 필드 변환 금지 lint + 입력해시+계산함수버전 저장"
    +  mechanism_found: "hooks/pre-commit:137-144 (acceptance-0-7.sh [4/6])"
    +  status: "완전"
    +  evidence: "동일 실행 출력에서 '[4/6] LLM 출력→판정 필드 → BLOCKED ...(P14)' 직접 확인."
    +
    +- id: P15
    +  principle: "검증을 우회할 수 없다"
    +  mechanism_expected: "작업트리 청결 확인 + revert의 테스트/검사파일 변경 차단 + expect값 변경 단독커밋 강제"
    +  mechanism_found: "acceptance-0-7.sh [5/6]"
    +  status: "부분"
    +  evidence: "'[5/6] 미커밋 상태로 push → BLOCKED ...(P15)' 직접 확인. revert-커밋 차단, expect값 단독커밋 강제는 미발견."
    +
    +- id: P16
    +  principle: "테스트는 런타임 동작을 검사한다"
    +  mechanism_expected: ".contract.test.* 접미사 강제 + 런타임 import 필수 + 테스트/결함 상관계수 CI 계산"
    +  mechanism_found: "scripts/acceptance-hs-a4.sh, scripts/hs_import_spy.py"
    +  status: "완전"
    +  evidence: "731줄→17줄 스텁 변조시 테스트가 실제로 깨지는지 실증하는 스크립트 + 런타임 임포트 스파이 존재·실행 확인."
    +
    +- id: P17
    +  principle: "증거는 만든 자가 쓸 수 없다"
    +  mechanism_expected: "판정서 쓰기 경로는 러너 전용 권한, 에이전트 쓰기 권한 자체 없음"
    +  mechanism_found: null
    +  status: "없음"
    +  evidence: "현재 판정서(V1/V2 verdict) 파일은 에이전트가 Write 도구로 직접 쓸 수 있는 구조. 권한 분리 장치 없음(2026-08-18 PR#13에서 직접 목격)."
    +
    +- id: P18
    +  principle: "위험한 동작은 금지하지 않고 능력을 없앤다"
    +  mechanism_expected: "사후 가드 대신 구조적으로 불가능하게 권한·참조·토큰 회수"
    +  mechanism_found: null
    +  status: "미확인"
    +  evidence: "설계 철학에 가까워 grep으로 존재 확인이 어려움. 구체 사례(P8)가 해당없음이라 실증 사례 미발견."
    +
    +- id: P19
    +  principle: "외부 의존 경계는 라이브 스모크가 배송 조건"
    +  mechanism_expected: "파일경로 자동분류 → 해당 PR은 라이브 스모크 1건 CI 요구"
    +  mechanism_found: null
    +  status: "없음"
    +  evidence: "경로 기반 자동 분류 + 라이브 스모크 요구 CI job 미발견."
    +
    +- id: P20
    +  principle: "CI는 0건 처리 통과를 스스로 의심한다"
    +  mechanism_expected: "typecheck/test 스텝이 처리 건수 로그 + 최소치 미만시 FAIL"
    +  mechanism_found: "scripts/acceptance-hs-gates.sh (COLLECTED: 25 로그 패턴)"
    +  status: "부분"
    +  evidence: "처리 건수 로그 패턴 확인('PASS: pytest collected 25 and passed'). 최소치 미달시 자동 FAIL 임계값 검사는 전수 확인 못함."
    +
    +- id: P21
    +  principle: "데이터는 git에 넣지 않는다"
    +  mechanism_expected: "1MB 초과 데이터 파일 pre-commit 차단"
    +  mechanism_found: "hooks/pre-commit:183,202"
    +  status: "완전"
    +  evidence: "MAX_BYTES=1048576(183행), block '1MB 초과 파일...(P21)'(202행) 원문 확인."
    +
    +- id: P22
    +  principle: "하드코딩 금지 + 자격증명은 소스·화면 모두 금지"
    +  mechanism_expected: "운영상수 contracts/*.json 단일화 + JSX 렌더 대상까지 자격증명 검사"
    +  mechanism_found: "contracts/cleanroom-deny-patterns.txt, contracts/portal-constants-deny-patterns.txt"
    +  status: "부분"
    +  evidence: "contracts/ 기반 금지패턴 파일 존재 확인. 운영상수 전면 단일화·JSX 렌더 전용 검사는 별도 미확인."
    +
    +- id: "§1-B-1"
    +  principle: "셀렉터는 코드가 아니라 데이터다"
    +  mechanism_expected: "contracts/*/markers.json 단일화"
    +  mechanism_found: "contracts/*.txt (deny-patterns류, 동일 사상)"
    +  status: "부분"
    +  evidence: "정확히 markers.json 이름은 없으나 contracts/ 디렉터리에 데이터 파일로 패턴을 두는 동일 사상 파일 존재(PR#13이 이 계열 작업)."
    +
    +- id: "§1-B-2"
    +  principle: "판정기는 하나다 (자동로그인·증거캡처 동일 함수)"
    +  mechanism_expected: null
    +  mechanism_found: null
    +  status: "미확인"
    +  evidence: "소스 전체 확인이 필요해 이번 조사 범위에서 미확인으로 남김."
    +
    +- id: "§1-B-3"
    +  principle: "브라우저 계층은 한 벌이다"
    +  mechanism_expected: null
    +  mechanism_found: null
    +  status: "미확인"
    +  evidence: "동일 사유로 미확인."
    +
    +- id: "§1-B-4"
    +  principle: "테스트는 실캡처 스냅샷으로만"
    +  mechanism_expected: null
    +  mechanism_found: null
    +  status: "미확인"
    +  evidence: "동일 사유로 미확인."
    +
    +- id: "§1-B-5"
    +  principle: "개입 감지는 구조로 (드라이버 포트 감싸기)"
    +  mechanism_expected: null
    +  mechanism_found: null
    +  status: "미확인"
    +  evidence: "동일 사유로 미확인."
    +
    +- id: V-1
    +  principle: "검증자는 실행 산출물을 제출한다"
    +  mechanism_expected: "/strict §5"
    +  mechanism_found: "~/.claude/skills/strict/SKILL.md §5 — codex 실행 산출물(판정 파일) 수령·확인 체계"
    +  status: "완전"
    +  evidence: "2026-08-18 PR#13에서 codex-rescue 에이전트 실제 실행, 실행 로그·재현 명령 포함 판정 파일 수령·재현 확인."
    +
    +- id: V-2
    +  principle: "V1은 다른 모델 계열, V2는 재현 전담"
    +  mechanism_expected: "/strict §6"
    +  mechanism_found: "~/.claude/skills/strict/SKILL.md §6"
    +  status: "완전"
    +  evidence: "2026-08-18 codex(V1) FAIL 판정을 Claude(V2)가 동일 스크립트 재실행으로 재현·반박한 실제 사례."
    +
    +- id: V-3
    +  principle: "V3 = 라이브 1건, 기계 영수증 없이 완료 없음"
    +  mechanism_expected: "make ship 거부"
    +  mechanism_found: null
    +  status: "부분"
    +  evidence: "'make ship' 명령 자체는 이 저장소에 없음(make/npm 레포 아님). pre-push+CI가 유사 역할 수행하나 이름 그대로의 강제 명령은 없음."
    +
    +- id: V-4
    +  principle: "외부 모델 의견은 가설, 로컬 재현 전까지 결함 아님"
    +  mechanism_expected: "문서 규약 + PR 템플릿"
    +  mechanism_found: null
    +  status: "부분"
    +  evidence: "PR 템플릿 자체는 없음(P2와 동일 갭). 2026-08-18 세션에서 원칙대로 행동한 실천 사례는 있으나 문서화된 강제 장치는 없음."
    +
    +- id: V-5
    +  principle: "G·V1·V2가 갈리면 결론 내지 않는다"
    +  mechanism_expected: "/strict 기존 규칙"
    +  mechanism_found: "~/.claude/skills/strict/SKILL.md §6.5"
    +  status: "완전"
    +  evidence: "명문화돼 있고, 2026-08-18 codex FAIL vs Claude PASS 재현이 갈렸을 때 원인 규명 후 정정하는 방식으로 실제 적용."
    diff --git a/scripts/acceptance-principles-check.sh b/scripts/acceptance-principles-check.sh
    index b803b84..cfd3fd6 100755
    --- a/scripts/acceptance-principles-check.sh
    +++ b/scripts/acceptance-principles-check.sh
    @@ -14,34 +14,66 @@ if [ ! -f "$FILE" ]; then
       exit 1
     fi

    +# 외부 라이브러리(pyyaml) 의존 금지 — docs/sot/mechanism-registry.yaml 파서(scripts/verify/
    +# check-mechanism-registry.sh) 관례를 따라 이 파일 전용 최소 파서를 표준 파이썬으로 직접 짠다.
    +# 계약: 항목은 `- id: 값`으로 시작, 그 뒤 2칸 들여쓴 `key: 값` 줄이 항목당 정확히 6개(자기 자신 포함).
    +# 값은 큰따옴표로 감싸거나 `null` 리터럴만 허용(그 외 형태 = 파싱 실패로 fail-closed).
     result=$(python3 - "$FILE" "$REQUIRED_COUNT" <<'PYEOF'
    -import sys, json
    -try:
    -    import yaml
    -except ImportError:
    -    print("FAIL: pyyaml 미설치 — python3 -m pip install pyyaml 필요")
    -    sys.exit(1)
    +import re, sys

     path, required_count = sys.argv[1], int(sys.argv[2])
     required_fields = ["id", "principle", "mechanism_expected", "mechanism_found", "status", "evidence"]
     valid_statuses = {"완전", "부분", "없음", "해당없음", "미확인"}

     with open(path, encoding="utf-8") as f:
    -    data = yaml.safe_load(f)
    +    lines = f.readlines()
    +
    +item_start = re.compile(r'^- id:\s*(.+)$')
    +field_line = re.compile(r'^  ([a-z_]+):\s*(.*)$')
    +
    +BARE_OK = re.compile(r'^[A-Za-z0-9._-]+$')
    +
    +def unquote(raw):
    +    raw = raw.rstrip("\n").strip()
    +    if raw == "null":
    +        return None
    +    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
    +        return raw[1:-1]
    +    if BARE_OK.match(raw):
    +        return raw
    +    print(f"FAIL: 값이 계약 밖 형태(따옴표 없음/null 아님/영숫자._- 아님): {raw!r}")
    +    sys.exit(1)

    -if not isinstance(data, list):
    -    print("FAIL: 최상위가 배열이 아님")
    +items = []
    +current = None
    +for lineno, line in enumerate(lines, 1):
    +    if not line.strip() or line.lstrip().startswith("#"):
    +        continue
    +    m = item_start.match(line)
    +    if m:
    +        if current is not None:
    +            items.append(current)
    +        current = {"id": unquote(m.group(1))}
    +        continue
    +    m = field_line.match(line)
    +    if m and current is not None:
    +        key, val = m.group(1), m.group(2)
    +        if key in current:
    +            print(f"FAIL: {lineno}행 — 같은 항목에 필드 '{key}' 중복")
    +            sys.exit(1)
    +        current[key] = unquote(val)
    +        continue
    +    print(f"FAIL: {lineno}행 — 계약 밖 형태: {line.rstrip()!r}")
         sys.exit(1)
    +if current is not None:
    +    items.append(current)

    -if len(data) != required_count:
    -    print(f"FAIL: 항목 수 {len(data)} != {required_count}")
    +if len(items) != required_count:
    +    print(f"FAIL: 항목 수 {len(items)} != {required_count}")
         sys.exit(1)

     ids_seen = set()
    -for item in data:
    -    if not isinstance(item, dict):
    -        print(f"FAIL: 배열 원소가 dict 아님: {item!r}")
    -        sys.exit(1)
    +for item in items:
         missing = [k for k in required_fields if k not in item]
         if missing:
             print(f"FAIL: {item.get('id', '?')} 필드 누락: {missing}")
    @@ -54,10 +86,9 @@ for item in data:
             sys.exit(1)
         ids_seen.add(item["id"])

    -print(f"PASS: 스키마 32/32 유효, id 중복 0건")
    +print("PASS: 스키마 32/32 유효, id 중복 0건")
     PYEOF
    -)
    -rc=$?
    +) && rc=0 || rc=$?
     echo "$result"
     if [ "$rc" -ne 0 ] || ! echo "$result" | grep -q '^PASS:'; then
       exit 1
    @@ -67,17 +98,39 @@ fi
     # HEAD에 이 파일이 아직 없으면(최초 추가 커밋) 회귀 비교를 건너뛴다 — 비교 대상 자체가 없음.
     if git cat-file -e "HEAD:$FILE" 2>/dev/null; then
       regressed=$(python3 - "$FILE" <<'PYEOF'
    -import sys, subprocess
    -import yaml
    +import re, subprocess, sys

     path = sys.argv[1]
     order = {"완전": 4, "부분": 3, "미확인": 2, "해당없음": 2, "없음": 1}
    +item_start = re.compile(r'^- id:\s*(.+)$')
    +field_line = re.compile(r'^  ([a-z_]+):\s*(.*)$')
    +
    +def unquote(raw):
    +    raw = raw.rstrip("\n").strip()
    +    if raw == "null":
    +        return None
    +    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
    +        return raw[1:-1]
    +    return raw  # 회귀검사는 status 값(항상 bare 한글 단어)만 쓰므로 관용적으로 허용
    +
    +def parse_id_status(text):
    +    result = {}
    +    current_id = None
    +    for line in text.splitlines():
    +        m = item_start.match(line)
    +        if m:
    +            current_id = unquote(m.group(1))
    +            continue
    +        m = field_line.match(line)
    +        if m and current_id is not None and m.group(1) == "status":
    +            result[current_id] = unquote(m.group(2))
    +    return result

     old_raw = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout
    -old = {x["id"]: x["status"] for x in yaml.safe_load(old_raw)}
    +old = parse_id_status(old_raw)

     with open(path, encoding="utf-8") as f:
    -    new = {x["id"]: x["status"] for x in yaml.safe_load(f)}
    +    new = parse_id_status(f.read())

     bad = []
     for pid, new_status in new.items():

→ 무엇을 시켰나 / RED부터 GREEN까지 커밋의 전체 변경 내용을 읽었습니다. / 신규 YAML 229줄과 검사 스크립트 변경 97줄이 대상임을 확인했습니다.

## 2. AC1 기본 파일과 수량 확인

명령:

    bash scripts/acceptance-principles-check.sh
    printf 'COMMAND_EXIT=%s\n' "$?"
    grep -c '^- id:' docs/sot/principles.yaml
    grep -c '^  principle:' docs/sot/principles.yaml
    grep -c '^  mechanism_expected:' docs/sot/principles.yaml
    grep -c '^  mechanism_found:' docs/sot/principles.yaml
    grep -c '^  status:' docs/sot/principles.yaml
    grep -c '^  evidence:' docs/sot/principles.yaml

출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    COMMAND_EXIT=0
    32
    32
    32
    32
    32
    32

→ 무엇을 시켰나 / 기본 검사와 6개 필드를 각각 독립 계산했습니다. / 현재 파일 자체는 32개이며 각 필드도 32번 나옵니다.

명령:

    ruby -e 'require "yaml"; d=YAML.load_file(ARGV[0]); puts "RUBY_YAML_ITEMS=#{d.length}"; puts "RUBY_YAML_ALL_SIX_FIELDS=#{d.all? { |x| %w[id principle mechanism_expected mechanism_found status evidence].all? { |k| x.key?(k) } }}"' docs/sot/principles.yaml
    python3 -c 'import yaml'

출력:

    RUBY_YAML_ITEMS=32
    RUBY_YAML_ALL_SIX_FIELDS=true
    RUBY_BASELINE_EXIT=0
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
        import yaml
    ModuleNotFoundError: No module named 'yaml'
    PYYAML_IMPORT_EXIT=1

→ 무엇을 시켰나 / 독립 YAML 해석기로 현재 파일을 확인하고 Python용 외부 YAML 도구 설치 여부를 확인했습니다. / 현재 파일은 유효하지만 pyyaml이 없어 표준 도구만 쓰려는 제약은 실제입니다.

현재 ID와 상태 합계:

    - id: P1
    - id: P2
    - id: P3
    - id: P4
    - id: P5
    - id: P6
    - id: P7
    - id: P8
    - id: P9
    - id: P10
    - id: P11
    - id: P12
    - id: P13
    - id: P14
    - id: P15
    - id: P16
    - id: P17
    - id: P18
    - id: P19
    - id: P20
    - id: P21
    - id: P22
    - id: "§1-B-1"
    - id: "§1-B-2"
    - id: "§1-B-3"
    - id: "§1-B-4"
    - id: "§1-B-5"
    - id: V-1
    - id: V-2
    - id: V-3
    - id: V-4
    - id: V-5
    --- status totals ---
       5 미확인
      10 부분
       5 없음
       8 완전
       4 해당없음
    --- complete ids ---
    P11
    P13
    P14
    P16
    P21
    V-1
    V-2
    V-5

→ 무엇을 시켰나 / 정확한 현재 ID 목록과 상태별 수량, 완전 8개를 다시 뽑았습니다. / 현재 파일의 목록은 계약과 맞지만 검사기는 이 정확한 이름들을 고정하지 않습니다.

## 3. AC1 필드 누락 반증

임시 변경 전문:

    -  evidence: "mechanism-registry.yaml은 존재하고 pre-push/CI에서 실행되나 등록 3항목뿐(secrets-scan-precommit 등). 본 파일이 P1~P22 전체를 덮는 확장판."

명령과 출력:

    $ bash scripts/acceptance-principles-check.sh
    FAIL: P1 필드 누락: ['evidence']
    MISSING_FIELD_MUTATION_EXIT=1
     M docs/sot/principles.yaml

→ 무엇을 시켰나 / P1의 evidence를 임시 삭제해 필드 누락을 만들었습니다. / 검사기가 실패로 막았으므로 이 부분은 좋은 소식입니다.

복구 후 출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    MISSING_FIELD_TEST_RESTORED_EXIT=0
    --- git status --porcelain (필드 누락 시험 복구 직후) ---

→ 무엇을 시켰나 / 삭제한 필드를 원복하고 다시 검사했습니다. / 정상값 0이며 상태 출력이 비어 있어 원본이 복구됐습니다.

## 4. AC1 필수 ID 집합 반증

임시 변경 전문:

    - id: P1
    + id: P999

명령과 출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    REQUIRED_ID_MUTATION_EXIT=0
    32
     M docs/sot/principles.yaml

→ 무엇을 시켰나 / 필수 P1을 계약에 없는 P999로 바꾸되 항목 수 32개는 유지했습니다. / 잘못된 이름을 정상으로 승인했으므로 나쁜 소식이며 AC1 실패입니다.

scripts/acceptance-principles-check.sh:71-87은 항목 수, 필드 누락, 상태 값, ID 중복만 봅니다. P1~P22·§1-B-1~5·V-1~V-5라는 필수 목록과 대조하는 줄이 없습니다.

복구 후 출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    REQUIRED_ID_TEST_RESTORED_EXIT=0
    --- git status --porcelain (필수 ID 시험 복구 직후) ---

→ 무엇을 시켰나 / P999를 P1으로 되돌리고 다시 검사했습니다. / 정상값 0이며 상태 출력이 비어 있습니다.

## 5. 계약 밖 큰따옴표 반증

임시 변경 전문:

    -  evidence: "mechanism-registry.yaml은 존재하고 pre-push/CI에서 실행되나 등록 3항목뿐(secrets-scan-precommit 등). 본 파일이 P1~P22 전체를 덮는 확장판."
    +  evidence: "mechanism-registry.yaml은 "존재"하고 pre-push/CI에서 실행되나 등록 3항목뿐(secrets-scan-precommit 등). 본 파일이 P1~P22 전체를 덮는 확장판."

명령과 출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    QUOTE_MUTATION_CHECK_EXIT=0
    /System/Library/Frameworks/Ruby.framework/Versions/2.6/usr/lib/ruby/2.6.0/psych.rb:456:in `parse': (docs/sot/principles.yaml): did not find expected key while parsing a block mapping at line 7 column 3 (Psych::SyntaxError)
        from /System/Library/Frameworks/Ruby.framework/Versions/2.6/usr/lib/ruby/2.6.0/psych.rb:456:in `parse_stream'
        from /System/Library/Frameworks/Ruby.framework/Versions/2.6/usr/lib/ruby/2.6.0/psych.rb:390:in `parse'
        from /System/Library/Frameworks/Ruby.framework/Versions/2.6/usr/lib/ruby/2.6.0/psych.rb:277:in `load'
        from /System/Library/Frameworks/Ruby.framework/Versions/2.6/usr/lib/ruby/2.6.0/psych.rb:578:in `block in load_file'
        from /System/Library/Frameworks/Ruby.framework/Versions/2.6/usr/lib/ruby/2.6.0/psych.rb:577:in `open'
        from /System/Library/Frameworks/Ruby.framework/Versions/2.6/usr/lib/ruby/2.6.0/psych.rb:577:in `load_file'
        from -e:1:in `<main>'
    RUBY_YAML_EXIT=1
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
        import yaml; yaml.safe_load(open("docs/sot/principles.yaml")); print("PYYAML_ACCEPTED")
        ^^^^^^^^^^^
    ModuleNotFoundError: No module named 'yaml'
    PYYAML_EXIT=1
     M docs/sot/principles.yaml

→ 무엇을 시켰나 / 값 안에 이스케이프하지 않은 큰따옴표를 넣고 자체 검사와 독립 YAML 해석기를 차례로 실행했습니다. / 자체 검사는 정상이라고 했지만 독립 해석기는 문법 오류로 거부했으므로 나쁜 소식입니다.

scripts/acceptance-principles-check.sh:36-45의 unquote는 첫 글자와 마지막 글자만 큰따옴표인지 보고 가운데 큰따옴표를 검사하지 않습니다. 선례인 scripts/verify/check-mechanism-registry.sh:41-56은 큰따옴표 값에 다른 큰따옴표가 하나라도 있으면 거부합니다.

복구 후 출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    QUOTE_TEST_RESTORED_EXIT=0
    --- git status --porcelain (따옴표 시험 복구 직후) ---

→ 무엇을 시켰나 / 잘못 넣은 큰따옴표를 제거하고 다시 검사했습니다. / 정상값 0이며 상태 출력이 비어 있습니다.

## 6. “완전” 판정 증거 재현

### 6.1 P11 — 반증 성공

docs/sot/principles.yaml:77-82는 P11을 완전으로 적고 scripts/acceptance-file-size.sh가 main에 병합됐다고 주장합니다.

명령과 출력:

    $ rg --files | rg 'acceptance-file-size|acceptance-hs-a4|acceptance-0-7|hs_import_spy|pre-commit$|pre-push$'
    scripts/hs_import_spy.py
    scripts/acceptance-hs-a4.sh
    scripts/acceptance-0-7.sh
    hooks/pre-commit
    hooks/pre-push
    $ ls -l scripts/acceptance-file-size.sh scripts/acceptance-hs-a4.sh scripts/acceptance-0-7.sh scripts/hs_import_spy.py
    ls: scripts/acceptance-file-size.sh: No such file or directory
    -rwxr-xr-x@ 1 kangsangmo  staff  10486 Aug 19 01:27 scripts/acceptance-0-7.sh
    -rwxr-xr-x@ 1 kangsangmo  staff  20384 Aug 19 01:27 scripts/acceptance-hs-a4.sh
    -rw-r--r--@ 1 kangsangmo  staff    894 Aug 19 01:27 scripts/hs_import_spy.py

→ 무엇을 시켰나 / P11이 가리킨 파일을 현재 브랜치에서 찾았습니다. / 파일이 없으므로 완전 판정 근거가 성립하지 않습니다.

추가 명령과 출력:

    $ git branch --contains 57917da
    + task/file-size-gate
    $ git merge-base --is-ancestor 57917da HEAD
    FILE_SIZE_COMMIT_IN_HEAD=1
    $ git show main:scripts/acceptance-file-size.sh
    FILE_SIZE_EXISTS_ON_MAIN=128

→ 무엇을 시켰나 / 파일 추가 커밋이 현재 브랜치나 main에 들어왔는지 확인했습니다. / 별도 task/file-size-gate에만 있고 현재 브랜치의 조상이 아니며 main에도 파일이 없습니다.

### 6.2 P13·P14 — 반증 실패, 근거 확인

명령:

    bash scripts/acceptance-0-7.sh

출력 전문:

    === 전제 검사: 훅 인프라 ===
    OK: 훅 파일 4종 + settings.json 존재

    === 시연 (샌드박스: /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.Mtk5sIGgFL/repo · 각 시연마다 훅 ON/OFF 대조) ===
    [1/6] 검사기 자기 제외 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
             BLOCKED: 검사기 자기 제외 — scripts/acceptance-0-6.sh 가 자기 자신을 검사 대상에서 뺀다 (P13)
    [2/6] 검사 약화(실패 무시) → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
             BLOCKED: 검사 약화 패턴 추가 — scripts/acceptance-0-2.sh (P13). 정당하면 suppressions.yaml 에 expiry 와 함께 등록하라
    [3/6] 만료일 없는 억제 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
             BLOCKED: 억제 항목 1건 중 expiry 가 0건뿐 — 만료일 없는 억제는 영구화된다 (P13)
    [4/6] LLM 출력→판정 필드 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
             BLOCKED: LLM 출력을 판정 수치로 변환 — src/scoring.js. 판정 수치는 순수 함수가 만든다 (P14)
    [5/6] 미커밋 상태로 push → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
             BLOCKED: 작업트리가 깨끗하지 않다 — 미커밋/미추적 변경이 있는 상태의 push (P15)
    [6/6] 가짜 외부효과 모듈 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
             BLOCKED: 외부 효과를 표방하는데 네트워크 호출이 0건 — src/portal-login.js. 시뮬레이션 의심 (P4)

    OK: 원본 저장소 무변경 확인 (da39a3ee5e6b4b0d3255bfef95601890afd80709)

    PASS: 위반 6 종이 전부 차단됨 (각 건 훅 OFF 대조 통과)
    ACCEPTANCE_0_7_EXIT=0

→ 무엇을 시켰나 / P13의 세 위반과 P14의 숫자 변환 위반을 실제 임시 저장소에서 만들었습니다. / 모두 훅이 있을 때만 막혔으므로 좋은 소식입니다.

### 6.3 P16 — 일부 근거만 확인

첫 실행 출력:

    error: Failed to initialize cache at `/Users/kangsangmo/.cache/uv`
      Caused by: failed to open file `/Users/kangsangmo/.cache/uv/sdists-v9/.git`: Operation not permitted (os error 1)
    FAIL: environment sync
    ACCEPTANCE_HS_GATES_EXIT=2

→ 무엇을 시켰나 / 실제 모듈 불러오기 증거를 만드는 HumanSearch 검사를 기본 환경에서 실행했습니다. / 검사 자체가 실행되지 않아 이 결과만으로는 판정할 수 없었습니다.

재시도 명령:

    UV_CACHE_DIR=/private/tmp/vh-principles-v1-uv-cache UV_OFFLINE=1 bash scripts/acceptance-hs-gates.sh

재시도 출력:

    PASS: ruff clean in 4 python files
    PASS: mypy strict clean in 4 source files
    PASS: pytest collected 25 and passed
    PASS: runtime import proof /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-principles-yaml/humansearch/src/humansearch/__init__.py
    COLLECTED: 25
    ACCEPTANCE_HS_GATES_RETRY_EXIT=0

→ 무엇을 시켰나 / 쓰기 가능한 임시 캐시와 오프라인 설정으로 같은 검사를 다시 실행했습니다. / 25개 시험과 실제 모듈 불러오기는 확인됐으므로 이 부분은 좋은 소식입니다.

검색 출력:

    ./scripts/hs_import_spy.py:3:Loaded via ``pytest -p hs_import_spy`` with PYTHONPATH pointing at ``scripts/``.
    ./scripts/acceptance-hs-gates-mutations.sh:17:for required in "$GATES" "scripts/hs_import_spy.py" "humansearch/pyproject.toml" \
    ./scripts/acceptance-hs-gates.sh:72:# spy 플러그인(hs_import_spy)을 실제 실행에 배선해 세션 수집 수·모듈 파일을 기록시킨다.
    ./scripts/acceptance-hs-gates.sh:75:[ -e "$SPY_PLUGIN_DIR/hs_import_spy.py" ] || { echo "FAIL: import spy plugin missing"; exit 1; }
    ./scripts/acceptance-hs-gates.sh:81:  uv run --no-sync pytest -p hs_import_spy -q tests 2>&1) || pytest_rc=$?

→ 무엇을 시켰나 / P16의 실행 연결과 나머지 두 요구인 .contract.test 파일명 규칙·상관계수 계산을 저장소 전체에서 찾았습니다. / 실제 모듈 불러오기 연결은 있지만 나머지 두 자동 장치는 찾지 못했습니다.

docs/sot/principles.yaml:112-117은 acceptance-hs-a4.sh와 hs_import_spy.py를 근거로 완전이라 적습니다. acceptance-hs-a4.sh는 대용량 파일과 개인정보 경로 차단을 실행하는 AC-A4 검사이며, 731줄→17줄 변형 시험은 없습니다. 731→17 기록은 docs/engineering/v6-coding-principles-goal-2026-08-06.md:126의 과거 조사에만 있습니다.

### 6.4 P21 — 반증 실패, 근거 확인

명령과 출력:

    $ sed -n '183p;202p' hooks/pre-commit
    MAX_BYTES=1048576
            block "1MB 초과 파일 — $f (${sz} 바이트, P21). 데이터는 git 밖에 둔다"

→ 무엇을 시켰나 / P21이 가리킨 hooks/pre-commit:183과 hooks/pre-commit:202를 그대로 읽었습니다. / 183행은 1MB 기준을 정하고 202행은 이를 넘는 파일을 막습니다.

명령:

    bash scripts/acceptance-hs-a4.sh

출력 전문:

    PASS: gitignore 적용 — artifacts/x.png
    PASS: gitignore 적용 — data/humansearch.sqlite3
    PASS: gitignore 적용 — humansearch.db
    PASS: gitignore 적용 — run.sqlite
    PASS: gitignore 적용 — private-reviews/x.md
    PASS: 추적 파일 119개 중 1048576 바이트 초과 0건
    PASS: pre-commit 차단 확인 — 1MB 초과 파일 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — SQLite 파일 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — 아티팩트 스크린샷 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — 하위 경로 아티팩트 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — 하위 경로 데이터 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — SQLite WAL 사이드카 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — JSONL 덤프 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — 대문자 확장자 (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — 디렉터리 규칙(확장자 무해) (exit=1 · 사유 일치)
    PASS: pre-commit 차단 확인 — 비공개 리뷰 경로 (exit=1 · 사유 일치)
    PASS: 인덱스 blob 기준 측정 확인 (작업트리 덮어쓰기로 우회 불가)
    PASS: rename 도 검사 대상 (git mv 로 우회 불가)
    PASS: 하위 경로 정상 소스는 조용히 사라지지 않는다 (앵커 확인)
    PASS: 정상 파일은 통과 (차단과 통과가 한 쌍)
    PASS: 훅과 공용 판정기의 금지 경로 패턴이 동치 (하위경로·사이드카·덤프·비공개리뷰 포함)
    PASS: 판정기 실행 — 기록에만 남은 1MB 초과 파일을 잡는다 (D1) (exit=1)
    PASS: 판정기 실행 — 깨끗한 기록은 통과시킨다 (차단과 통과가 한 쌍) (exit=0)
    PASS: 판정기 실행 — 후보자 컬럼 CSV 를 잡는다 (D2) (exit=1)
    PASS: 판정기 실행 — 후보자 컬럼 SQL 을 잡는다 (D2) (exit=1)
    PASS: 판정기 실행 — 정상 지표 CSV 는 통과시킨다 (오탐 대조군) (exit=0)
    PASS: 판정기 실행 — 정상 마이그레이션 SQL 은 통과시킨다 (오탐 대조군) (exit=0)
    PASS: CI 가 공용 판정기를 실행 줄에서 호출한다
    PASS: 판정기 스텝에 비활성화 조건 없음
    PASS: 작업트리 무오염 (git status 기준 — git 설정·내부 객체·참조는 범위 밖)
    CHECKED: 30
    ACCEPTANCE_HS_A4_EXIT=0

→ 무엇을 시켰나 / 1MB 파일과 여러 데이터 경로를 실제 임시 저장소에서 차단하는지 실행했습니다. / 30개 검사가 모두 통과했고 원본도 바꾸지 않았으므로 P21 근거는 확인됐습니다.

## 7. AC2 pre-push 자동 편입과 실패 전달

명령:

    bash hooks/pre-push </dev/null 2>&1 | grep -n "acceptance-principles-check"

출력:

    20:  ok  ./scripts/acceptance-principles-check.sh
    GREP_PIPELINE_EXIT=0

→ 무엇을 시켰나 / 실제 pre-push 전체를 돌리고 새 검사 이름이 실행 목록에 나오는지 찾았습니다. / 20번째 출력에 ok로 나타났으므로 자동 편입은 좋은 소식입니다.

hooks/pre-push:112-113은 find로 acceptance-*.sh를 자동 수집합니다. hooks/pre-push:165는 각 스크립트를 실제 실행하고, hooks/pre-push:166-167은 결과가 0이 아니면 block을 호출하며, hooks/pre-push:174는 누적 실패값을 최종 반환합니다.

## 8. AC3 직접 변형과 실제 커밋 경로

### 8.1 요청서에 지정된 작업 파일 변형

임시 변경 전문:

    -  status: "완전"
    +  status: "없음"

출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    FAIL: status 회귀 발견 — REGRESSED:P11: 완전 -> 없음
    AC3_MUTATION_EXIT=1
     M docs/sot/principles.yaml

→ 무엇을 시켰나 / 작업 파일의 P11을 완전에서 없음으로 낮췄습니다. / 실패값 1로 막았으므로 요청서의 좁은 시험은 좋은 소식입니다.

복구 후 출력:

    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    AC3_RESTORED_EXIT=0
    --- git status --porcelain (복구 직후) ---

→ 무엇을 시켰나 / P11을 완전으로 원복하고 다시 검사했습니다. / 정상값 0이며 상태 출력이 비어 있습니다.

### 8.2 실제 전송과 같은 커밋된 상태 하락

격리 복제본에서 같은 변경을 커밋한 출력:

    [task/strict-principles-yaml 12647e4] test: committed status regression
     1 file changed, 1 insertion(+), 1 deletion(-)
    12647e4 test: committed status regression
     docs/sot/principles.yaml | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)
    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    AC3_COMMITTED_REGRESSION_EXIT=0

→ 무엇을 시켰나 / 원본과 분리된 복제본에서 P11 하락을 커밋한 뒤 검사했습니다. / 하락이 저장됐는데도 정상값 0이 나왔으므로 실제 AC3는 실패입니다.

원인은 scripts/acceptance-principles-check.sh:129가 git show HEAD로 현재 커밋을 읽고, scripts/acceptance-principles-check.sh:132-133이 현재 작업 파일을 읽어 비교하기 때문입니다. 커밋 뒤에는 두 내용이 같습니다. hooks/pre-push:35-41은 작업 파일이 더러우면 검사를 시작하기 전에 멈추므로, 작업 파일 변형에서만 작동하는 비교는 실제 전송에서 보호가 되지 않습니다.

## 9. AC4·AC5 SKILL.md 변경 여부

명령:

    diff -q ~/.claude/skills/strict/SKILL.md.bak-2026-08-12 ~/.claude/skills/strict/SKILL.md
    ls -la ~/.claude/skills/strict/SKILL.md ~/.codex/skills/strict/SKILL.md
    stat -f '%N | birth=%SB | modified=%Sm | changed=%Sc' -t '%Y-%m-%d %H:%M:%S %z' ...

출력 전문:

    Files /Users/kangsangmo/.claude/skills/strict/SKILL.md.bak-2026-08-12 and /Users/kangsangmo/.claude/skills/strict/SKILL.md differ
    CLAUDE_DIFF_EXIT=1
    -rw-r--r--@ 1 kangsangmo  staff  59744 Aug 19 01:34 /Users/kangsangmo/.claude/skills/strict/SKILL.md
    -rw-r--r--@ 1 kangsangmo  staff  35508 Aug 19 01:34 /Users/kangsangmo/.codex/skills/strict/SKILL.md
    /Users/kangsangmo/.claude/skills/strict/SKILL.md.bak-2026-08-12 | birth=2026-08-12 01:33:28 +0900 | modified=2026-08-12 01:33:28 +0900 | changed=2026-08-12 01:33:28 +0900
    /Users/kangsangmo/.claude/skills/strict/SKILL.md | birth=2026-08-12 15:56:47 +0900 | modified=2026-08-19 01:34:33 +0900 | changed=2026-08-19 01:34:33 +0900
    /Users/kangsangmo/.codex/skills/strict/SKILL.md | birth=2026-08-12 03:27:54 +0900 | modified=2026-08-19 01:34:33 +0900 | changed=2026-08-19 01:34:33 +0900
    /Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/strict-principles-yaml-goal-2026-08-19.md | birth=2026-08-19 01:26:59 +0900 | modified=2026-08-19 01:26:59 +0900 | changed=2026-08-19 01:26:59 +0900

→ 무엇을 시켰나 / 8월 12일 백업과 현재 파일을 비교하고 두 SKILL.md와 goal의 수정 시각을 확인했습니다. / 두 SKILL.md 모두 goal보다 7분 34초 늦게 수정돼 “이번 판 미수정”을 입증하지 못했습니다.

goal 문서에는 §분리 계획 표가 실제로 있어 계획 작성 자체는 확인했습니다. 다만 파일 변경 주체는 ※ 미확인입니다.

## 10. 복구와 오염 검사

각 원본 변형 직후의 git status --porcelain 출력은 위 3·4·5·8절에 그대로 첨부했으며 모두 비었습니다.

격리 복제본 정리 중 첫 두 시도 출력:

    trash: Error Domain=NSCocoaErrorDomain Code=513 ... couldn’t be moved to the trash because you don’t have permission to access it.
    gio: Unable to create trash directory /Users/kangsangmo/.local/share/Trash: Operation not permitted

→ 무엇을 시켰나 / 임시 복제본을 복구 가능한 휴지통으로 먼저 보내려 했습니다. / 환경 권한 때문에 실패했으며 저장소에는 임시 디렉터리가 남아 있었습니다.

정확한 두 임시 경로를 검증한 뒤 삭제한 출력:

    VALIDATED_WORKSPACE_TEMP=1
    VALIDATED_PRIVATE_TEMP=1
    --- git status --porcelain (격리 복제본 삭제 후) ---

→ 무엇을 시켰나 / .git이 있는 정확한 임시 경로 두 개만 확인한 뒤 깊이 우선 삭제하고 상태를 확인했습니다. / 상태 출력이 비어 검증 대상은 원상복구됐습니다.

## 11. 수정 우선순위

### 결정 카드 A — AC3 비교 기준

- **무엇을**: 현재 작업 파일과 HEAD 비교를 이전 커밋과 현재 커밋 비교로 바꿔야 합니다.
- **왜**: 실제 pre-push는 깨끗한 작업 상태만 허용해 현재 방식이 언제나 자기 자신을 비교하기 때문입니다.
- **버린 대안**: 작업 파일 변형 시험만 유지하는 안은 실제 전송 경로를 증명하지 못해 버립니다.
- **대가**: 최초 도입 커밋과 얕은 복제본에서 비교 기준이 없을 때의 처리 규칙을 추가해야 합니다.
- **되돌리는 법**: 별도 커밋으로 비교 기준만 원복하고, 격리 복제본 커밋 시험을 계속 빨간불로 유지합니다.

### 결정 카드 B — YAML 값 검사

- **무엇을**: 선례처럼 큰따옴표 내부의 추가 큰따옴표를 거부하고, 필수 ID 정확한 집합과 알 수 없는 필드도 검사해야 합니다.
- **왜**: 현재 검사는 실제 YAML이 읽을 수 없는 상태와 필수 원칙 누락을 정상으로 승인합니다.
- **버린 대안**: 외부 pyyaml 설치를 강제하는 안은 현재 환경에 모듈이 없고 기존 무의존 관례와 어긋나 버립니다.
- **대가**: 작은 전용 해석 코드와 변조 시험이 몇 줄 늘어납니다.
- **되돌리는 법**: 변경 전 스크립트로 한 커밋 되돌릴 수 있지만, D1·D2 변조 시험은 되돌리면 다시 실패해야 합니다.

### 결정 카드 C — “완전” 상태 정정

- **무엇을**: P11은 현재 브랜치에서 완전이 아니며, P16은 확인된 실제 모듈 불러오기만 남기고 부분으로 낮춰야 합니다.
- **왜**: 존재하지 않거나 요구 일부만 구현된 장치를 완전으로 쓰면 다음 계획이 잘못됩니다.
- **버린 대안**: 다른 브랜치와 과거 조사 기록을 현재 완전 근거로 인정하는 안은 실제 전송 코드가 아니므로 버립니다.
- **대가**: 상태표 숫자는 완전 8개보다 낮아지지만 실제 미완료 작업이 드러납니다.
- **되돌리는 법**: 해당 장치가 대상 브랜치에 병합되고 세 요구를 실행으로 입증한 뒤 완전으로 다시 올릴 수 있습니다.

# 최종 판정

AC2와 P13·P14·P21 증거는 확인됐고, 현재 YAML 파일 자체도 32개·6개 필드를 갖습니다. 그러나 AC1이 필수 원칙 누락과 깨진 YAML을 승인하고, AC3이 실제 커밋된 상태 하락을 승인하며, P11·P16의 완전 판정도 과장돼 있습니다.

따라서 804a39c는 현재 계약을 충족하지 못합니다. D1~D5를 수정한 뒤 동일 변조 시험을 다시 실행하고, AC4·AC5는 변경 주체를 확인할 수 있는 별도 기록이 없으면 계속 미확인으로 남겨야 합니다.

# 제출 전 형식·파일 검증

명령:

    bash ~/.claude/skills/strict/brief-lint.sh docs/engineering/strict-principles-yaml-v1-verdict-2026-08-19.md

출력 전문:

    === docs/engineering/strict-principles-yaml-v1-verdict-2026-08-19.md ===
      코드블록 0개 · 표 2개 (면제 0개) / 해석 누락 0개
      1층(결론): 줄 2 / 본문 237자
      1층 기술 표기: 없음 (※ 한글 전문용어는 못 잡는다 — 사람이 본다)
      결정 카드 3건 (※ 내용이 판단에 쓸 만한지는 못 잰다 — 사람이 본다)
      증거 보관 경로: 임시 외 실재 파일 7건 (※ 그 파일이 이 주장의 증거인지는 못 잰다)

    브리핑 계약 기계 검사: 위반 0건 (문서 1개)

    이 검사가 못 보는 것 (사람이 봐야 하는 것):
      · 설명이 실제로 말이 되는지 — 출력과 무관한 문장도 통과한다
      · 결정 카드 내용이 판단에 쓸 만한지 — 한 글자여도 통과한다
      · 증거 파일이 그 주장과 관련 있는지 — 존재하기만 하면 통과한다
      · 결론이 쉬운 말인지 — 한글 전문용어는 잡지 못한다
      ※ 이 검사는 홈 폴더에만 있어 서버 자동 검사에 없다 — 회사 차원의 합격 근거가 아니다(P15③).
    FINAL_BRIEF_LINT_EXIT=0

→ 무엇을 시켰나 / strict 브리핑 형식 검사를 실행했습니다. / 결론 기술 표기와 해석 누락이 0건이며, 이 숫자는 문서 형식만 확인하고 코드 합격을 뜻하지 않습니다.

첫 줄과 최종 원본 검사 출력:

    VERDICT: FAIL
    PASS: 스키마 32/32 유효, id 중복 0건
    PASS: 회귀 0건 (NO_REGRESSION)
    PASS: principles.yaml 32/32 스키마 유효, 회귀 0건
    FINAL_PRINCIPLES_EXIT=0

→ 무엇을 시켰나 / 판정서 첫 줄과 복구된 원본 검사 결과를 확인했습니다. / 첫 줄 계약은 맞고 원본 YAML은 정상 상태로 돌아왔습니다.

새 파일 검사 출력:

    FINAL_NO_INDEX_DIFF_CHECK_EXIT=1
    FINAL_TRAILING_WHITESPACE=0
    FINAL_TRAILING_WHITESPACE_EXIT=0

→ 무엇을 시켰나 / 빈 파일과 새 판정서를 직접 비교하면서 잘못된 줄 끝 공백을 검사했습니다. / Git의 1은 두 파일이 다르다는 뜻이며 오류 출력은 없었고, 독립 검사도 공백 위반 0건이었습니다.

최종 저장소 상태 출력:

    --- tracked changes excluding verdict ---
    --- git status --porcelain --untracked-files=no ---
    --- git status --porcelain ---
    ?? docs/engineering/strict-principles-yaml-v1-verdict-2026-08-19.md

→ 무엇을 시켰나 / 판정서 이외의 추적 파일 변경과 전체 상태를 확인했습니다. / 검증 대상 파일 변경은 0건이며, 사용자가 요구한 새 판정서 한 개만 남았습니다.
