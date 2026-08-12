VERDICT PR#6-REV2: FAIL

# 결론

이 변경을 기본 코드에 아직 넣으면 안 됩니다. 요청하신 비밀 주소·열쇠 문자열 탐지와 정상 설정 통과는 실제 시험에서 모두 작동했지만, “검사가 저장소를 건드리지 않았다”는 확인을 속일 수 있고 기준 문서 두 곳이 실제 실행과 다릅니다.

결정 사항은 하나입니다. 아래 네 결함을 고치거나, 의도적으로 남길 범위를 책임자가 명시적으로 승인하기 전에는 합치지 마십시오.

# 판단 근거

## 확인하지 못한 것·건너뛴 것·다시 한 것

확인하지 못한 것은 GitHub(원격 코드 저장 서비스)에 표시된 현재 원격 검사 결과와 `weakens-check` 표시입니다. 이 환경에서 GitHub 화면은 내용을 돌려주지 않았고 명령행 조회도 네트워크 차단으로 실패했으므로, 로컬의 정확한 작업 이력 `08cc032389039d251e02bebf92b1f23bd79f88d8`만 판정했습니다.

건너뛴 저장소 관련 작업은 없습니다. 다만 금지된 `worktrees/humansearch-clean-room-plan`은 지시대로 읽지도 쓰지도 않았고, 관계없는 제품 코드·외부 서비스는 범위에서 제외했습니다.

중간에 실패해서 다시 한 것은 두 가지입니다. 첫 Bash(맥의 기본 명령 실행기) 문법 명령은 실행 위치를 잘못 잡아 대상 파일을 못 찾았고, 즉시 격리 복제본 안에서 다시 실행해 추적 중인 셸 파일 13개가 모두 통과함을 확인했습니다. `acceptance-0-2`(과거 이력 안전 검사)는 첫 깨끗한 복제본에 로컬 전용 패턴 파일이 없어 종료값 2가 나왔고, 원본과 같은 읽기 전용 연결을 새 깨끗한 복제본에 재현한 뒤 종료값 0을 확인했습니다.

원본 작업 폴더의 추적 파일과 현재 이력 위치는 시작과 끝이 같았습니다. 그러나 모든 작업 폴더가 함께 쓰는 Git 객체 저장소(저장 이력의 실제 내용 파일을 보관하는 공용 공간)의 파일 수는 다른 동시 작업 때문에 감사 중 늘었으므로, 원본의 객체 수만으로 이 감사의 무오염을 단정하지 않았습니다.

## 판정의 갈림길

첫 번째 갈림길은 “현재 인수 검사(요구 동작을 실제 입력으로 넣어 합격 여부를 보는 시험)가 29건 모두 초록이면 전체 합격인가”였습니다. 이 해석은 버렸습니다. 사용자는 단순 초록이 아니라 12개 항목별 실행·반례, 무오염 사각지대, 문서 일치, 시험 약화까지 요구하셨고 실제로 세 항목에서 반례가 나왔습니다.

두 번째 갈림길은 “무오염 세 축이 각각 고장을 잡으니 ‘저장소 무오염’이라는 문구를 그대로 믿어도 되는가”였습니다. 이 해석도 버렸습니다. 양성 대조군에서는 세 축이 각각 실패를 냈지만, 중간에 바꿨다가 되돌리기·이미 무시 중인 폴더 안에 파일 추가·현재 이력을 옮겼다가 복귀·객체 수를 같은 숫자로 맞춘 교체는 모두 세 축이 같다고 판단했습니다.

세 번째 갈림길은 “12자 하한은 오탐을 없애는 수정이므로 검사 약화가 아닌가”였습니다. 목적은 정당하지만 결과는 검사 범위 축소입니다. 같은 6~11자 입력 18개가 이전 커밋에서는 모두 차단되고 현재 커밋에서는 모두 통과했으므로, ‘약화 표식이 없다’와 ‘약화 자체가 없다’를 구분했습니다.

네 번째 갈림길은 “정본 문서의 13단계 상세 표만 맞으면 문서 일치인가”였습니다. 이 해석을 버렸습니다. 같은 문서의 상단 표는 서버 검사가 추가로 세 스크립트만 실행한다고 쓰고, 최종 갱신일도 8월 8일로 남아 있어 상세 표와 서로 모순됩니다.

## 이 판정이 틀리면 깨지는 것

제가 잘못 FAIL을 냈다면 합칠 시점이 늦어지는 비용이 생깁니다. 그러나 반대로 잘못 PASS를 내면 짧은 실제 비밀값이 저장소로 들어가도 검사가 통과하고, 검사가 숨김 파일이나 Git 내부 상태를 남겨도 “무오염”이라고 보고하며, 운영자는 낡은 문서로 실제 자동 검사를 오판합니다.

핵심 탐지 구현은 강합니다. Discord 버전 경로, 하위 도메인, GovSlack, Slack의 `services` 없는 주소, 39자 벤더 키가 모두 실제 검사기 종료값 1로 막혔고, 여섯 정상 입력은 종료값 0으로 통과했습니다.

시험의 판별력도 대체로 강합니다. 검사 세 개 삭제, 기존 `TOKEN` 분기 삭제, 신규 키워드 규칙 삭제, M1~M4 변형은 모두 정확히 빨개졌고 매회 격리 복제본을 원복했습니다.

그럼에도 전체 FAIL인 이유는 “일부가 잘 됨”과 “합칠 계약을 모두 만족함”이 다르기 때문입니다. 특히 저장소 무오염 계약과 검사 약화 금지 원칙은 보안 검사 자체를 신뢰하기 위한 상위 조건입니다.

## 12개 요구사항 대조

| 번호 | 요구 | 판정 | 실행 근거 | 반례·남은 공백 |
|---:|---|---|---|---|
| 1 | 직전 미탐 5종 탐지 | 구현 확인 | 5종 각각 `verify.sh` 종료값 1, 전체 인수 검사도 5종 `PASS` | 찾지 못함 |
| 2 | 직전 오탐 6종 통과 | 구현 확인 | 6종 각각 `verify.sh` 종료값 0, 전체 인수 검사도 6종 `PASS` | 찾지 못함 |
| 3 | 검사 3개 삭제 시 실패 | 구현 확인 | 끝단 검사 3개 삭제 후 `CHECKED: 26`, 종료값 1 | 찾지 못함 |
| 4 | 기존 TOKEN 삭제 시 BOT_TOKEN 실패 | 구현 확인 | 두 기존 `TOKEN` 선택지를 제거하자 BOT_TOKEN 한 건 실패, 종료값 1 | 찾지 못함 |
| 5 | 신규 키워드 삭제 시 3건 실패 | 구현 확인 | WEBHOOK·CREDENTIAL·PRIVATE_KEY 3건과 인라인 주석 1건까지 실패 | 요구보다 한 건 더 강함 |
| 6 | 무오염 3축과 사각지대 | 부분 구현 | 파일·HEAD·객체 축 각각 양성 대조군을 실패시킴 | 최종 상태만 비교하므로 반례 4종이 통과하고 공용 객체 저장소의 동시 작업에 흔들림 |
| 7 | RED→GREEN→보강 사이 시험 약화 없음 | 구현 확인 | 실제 종료값 `1→0→1→1→0→0`; 카나리 삭제·기대 종료값 완화 없음 | 3bbe4b9는 죽은 카나리를 더 강하게 바꿈 |
| 8 | 정본 문서와 실제 작업 파일 일치 | 불일치 | 13개 실행 단계의 순서·본문은 일치 | 같은 문서의 3행·14행이 낡았고 트리거·권한·실행 환경·checkout 버전이 빠짐 |
| 9 | M1~M4 재현 | 구현 확인 | 네 변형 모두 종료값 1; 현재 실패 수는 5·3·3·4 | 원래 3·1·2·3보다 카나리가 늘어 실패 수가 커짐 |
| 10 | macOS Bash 3.2 문법·전체 실행 | 구현 확인 | `/bin/bash 3.2.57`, 추적 셸 13개 문법 통과, AC-S1 `CHECKED: 29`, 종료값 0 | 전체 저장소의 main 전용 배송 검사는 PR 복제본에서 의도대로 실행 대상 아님 |
| 11 | 새 커밋의 검사 약화 표식 없음 | 불일치 | `|| true`·`continue-on-error`·`allow_failure`·`xfail`·`skip` 신규 추가는 없음 | d605f3c가 6~11자 값 탐지 18개를 실제로 제거; 억제 원장 기록도 없음 |
| 12 | 인수 검사가 저장소를 오염시키지 않음 | 구현 확인, 환경 한계 있음 | 독립 복제본에서 상태·HEAD·객체 파일 수가 실행 전후 같음 | 원본 공용 객체 수는 다른 동시 작업으로 변해 원본 축의 독립 귀속은 불가; `/private/tmp`에 작은 도구 캐시 1개 잔존 |

→ 뭘 시켰나: 사용자 요구 12개를 하나씩 실행 가능한 계약으로 나눴습니다. / 뭐가 나왔나: 8개는 확인, 2개는 부분·환경 한계, 2개는 명시적 불일치였습니다. / 좋은 소식인가 나쁜 소식인가: 핵심 탐지는 좋은 소식이지만 전체 합격 조건은 충족하지 못했습니다.

## 결함 목록

| 결함 | 심각도와 사업·운영 영향 | file:line | 실행 반례 |
|---|---|---|---|
| REV2-D1 무오염 세 축이 완전한 무오염을 증명하지 못함 | **중간 — 검사 결과를 믿고 원본을 계속 쓰다가 숨김 산출물·Git 내부 변경을 놓치거나, 반대로 다른 작업 폴더의 정상 커밋 때문에 거짓 실패할 수 있습니다.** | `scripts/acceptance-secret-webhook-vendor.sh:33-38`은 시작값을 찍는 역할, `:257-272`는 종료값만 비교하는 역할, `docs/engineering/secret-webhook-vendor-goal-2026-08-12.md:93`은 되돌린 오염도 가짜 완료라고 정한 역할 | 무시 폴더 내부 추가, 추적 파일 수정 후 복원, HEAD 왕복, 객체 동일 개수 교체가 모두 세 축 같음 |
| REV2-D2 정본 문서가 자기 자신 및 실제 작업 파일과 불일치 | **중간 — 운영자가 실제로 어떤 검사가 언제 도는지 잘못 판단하고, 새 검사 누락이나 서버 설정 드리프트를 발견하지 못할 수 있습니다.** | `docs/sot/verification-commands.md:3`은 갱신일 역할, `:14`는 게이트 4 요약 역할, `:18-40`은 13단계 상세 목록 역할, `.github/workflows/verify.yml:5-20`은 실행 조건·권한·환경 역할, `:22-156`은 실제 13단계 역할 | 상세 13단계는 맞지만 상단은 추가 스크립트를 0-5·0-6·0-7만 적고 갱신일은 8월 8일 |
| REV2-D3 12자 하한이 6~11자 비밀 탐지를 제거했으나 약화 원장에 없음 | **중간 — 짧지만 실제인 웹훅·자격증명·개인키 관련 값이 커밋되어도 자동 검사가 통과할 수 있습니다.** | `.secret-patterns.default:91-94`는 12자 하한을 정하는 역할, `docs/sot/coding-principles.md:28`은 검사 약화 통제 역할, `suppressions.yaml:1-4`는 줄인 검사를 기록하라는 역할, `hooks/pre-commit:102-109`는 일부 확장자만 신규 약화 문자열을 검사하는 역할 | 이전 패턴은 6~11자 18건 전부 종료값 1, 현재 패턴은 전부 종료값 0 |
| REV2-D4 인수 계약 문서의 검사 수와 무오염 정의가 낡음 | **낮음 — 다음 수정자가 17건을 정상으로 오해하거나 파일 상태 한 축만 맞추고 계약을 충족했다고 잘못 보고할 수 있습니다.** | `docs/engineering/secret-webhook-vendor-goal-2026-08-12.md:85-87`은 기대 출력 17건을 정하는 역할, `:153-160`은 계약 입력·출력·무오염을 정하는 역할, `scripts/acceptance-secret-webhook-vendor.sh:280-289`는 실제 29건을 강제하는 역할 | 문서 `CHECKED: 17` 대 실행 `CHECKED: 29`; 문서는 일반 status만, 구현은 ignored·HEAD·객체 수 |

→ 뭘 시켰나: 반례가 있거나 계약과 다른 항목만 결함으로 분리했습니다. / 뭐가 나왔나: 중간 3건, 낮음 1건입니다. / 좋은 소식인가 나쁜 소식인가: 즉시 비밀 유출이 확인된 것은 아니지만, 검사 신뢰와 운영 판단을 깨므로 합치기 전 처리해야 합니다.

## 설계 결정 카드 1 — 무오염 확인

**무엇을** — 실행 전후의 파일 상태·현재 이력 위치·Git 객체 파일 수 세 값을 비교했습니다.
**왜** — 남은 무시 파일, 현재 이력 이동, 객체 생성 흔적을 낮은 비용으로 잡기 위해서입니다.
**버린 대안** — 원본에 쓰기 권한을 주지 않는 폐기 가능한 복제본 또는 쓰기 제한 실행을 채택하지 않았습니다.
**대가** — 중간 변경 후 복구, 무시 폴더 내부 변화, 같은 개수의 객체 교체를 놓치고 다른 작업 폴더의 객체 생성에는 거짓 실패할 수 있습니다.
**되돌리는 법** — 인수 검사를 항상 폐기 가능한 독립 복제본에서 돌리고 원본은 읽기 전용으로 고정한 뒤, 현재의 절대적 “무오염” 문구를 제거하거나 보조 지표로 낮추십시오.

## 설계 결정 카드 2 — 12자 하한

**무엇을** — WEBHOOK·CREDENTIAL·PRIVATE_KEY 값의 최소 길이를 6자에서 12자로 올렸습니다.
**왜** — `keychain`과 `PKCS12` 같은 정상 설정 이름을 비밀로 오인하지 않기 위해서입니다.
**버린 대안** — 정상 설정 이름을 값 목록 또는 키·값 조합으로 좁게 예외 처리하는 방식을 쓰지 않았습니다.
**대가** — 6~11자의 실제 비밀도 정상값과 함께 통과하고, 이 축소가 약화 원장에 남지 않았습니다.
**되돌리는 법** — 6자 하한을 복구하고 정상 설정 이름을 좁은 대조 규칙으로 분리하거나, 책임자가 12자 정책을 승인해 만료·담당자·회수 계획과 함께 억제 원장에 기록하십시오.

## 설계 결정 카드 3 — 정본 문서 표현

**무엇을** — 실제 서버 검사 13단계를 상세 표로 추가하되 기존 상단 게이트 요약과 갱신일을 그대로 뒀습니다.
**왜** — 직전 D6의 직접 문제였던 누락된 인라인 단계를 빠르게 전수 표에 넣기 위해서입니다.
**버린 대안** — 상단 요약을 상세 표의 링크만 남기는 단일 출처 구조로 바꾸지 않았습니다.
**대가** — 한 문서 안에 서로 다른 두 실행 목록이 남아 독자가 어느 쪽을 믿어야 할지 판단해야 합니다.
**되돌리는 법** — 14행을 13단계 표 참조로 바꾸고 갱신일·트리거·권한·실행 환경·checkout 버전을 실제 작업 파일과 같은 커밋에서 맞추십시오.

# 기술 상세·명령·출력·file:line 전문

## 0. 범위, 기준점, 금지사항 준수

감사 대상은 `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/secret-webhook-vendor`이며, 브랜치(서로 다른 변경 줄을 가리키는 이름)는 `task/secret-webhook-vendor`, HEAD(현재 작업 위치가 가리키는 정확한 저장 이력)는 `08cc032389039d251e02bebf92b1f23bd79f88d8`입니다.

```text
$ git status --short --branch
## task/secret-webhook-vendor...origin/task/secret-webhook-vendor
$ git rev-parse HEAD
08cc032389039d251e02bebf92b1f23bd79f88d8
$ git rev-parse --abbrev-ref HEAD
task/secret-webhook-vendor
```

→ 뭘 시켰나: 원본의 브랜치·정확한 이력값·추적 변경을 읽었습니다. / 뭐가 나왔나: 사용자 지정값과 일치하고 추적 변경은 없었습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식이며 판정 기준점이 고정됐습니다.

변이 실험은 clone(폐기 가능한 독립 복제본)에서만 했습니다. 주요 위치는 `/private/tmp/pr6-rev2-root.TSjSpS/repo`, `/private/tmp/secret-webhook-vendor-audit.Mie5ex/repo`, `/private/tmp/pr6-mutations.H8CK6s/repo`, `/private/tmp/pr6-ac-s1-audit.kzpduo/repo`, `/private/tmp/acm10.clean.O5qRVy/repo`입니다.

`git gc`와 `git reflog expire`는 실행하지 않았습니다. 원본의 추적 파일, HEAD, 브랜치, 설정을 변경하지 않았습니다. 금지된 작업 폴더 경로는 접근하지 않았습니다.

## 1. 현재 HEAD의 전체 AC-S1 실행

AC-S1은 이 변경의 acceptance criteria(요구사항을 합격·불합격으로 나누는 인수 기준)입니다. macOS 기본 `/bin/bash`로 전체 스크립트를 실행했습니다.

```text
$ /bin/bash scripts/acceptance-secret-webhook-vendor.sh
PASS: 탐지됨 — discord 웹훅 URL
PASS: 탐지됨 — discordapp.com 변종(구 도메인)
PASS: 탐지됨 — Slack 웹훅 URL
PASS: 탐지됨 — Anthropic 벤더 키(하이픈 접두 · 중립 변수명)
PASS: 탐지됨 — WEBHOOK 계열 .env 대입(불투명 토큰)
PASS: 탐지됨 — CREDENTIAL 계열 .env 대입
PASS: 탐지됨 — PRIVATE_KEY 한 줄 형태
PASS: 탐지됨 — BOT_TOKEN (기존 TOKEN 규칙 회귀 앵커 · 신규 규칙에는 없음)
PASS: 탐지됨 — discord 버전 경로 /api/v10/ (공식 권장 형식)
PASS: 탐지됨 — discord 하위 도메인(canary)
PASS: 탐지됨 — Slack 공공기관용 GovSlack 도메인
PASS: 탐지됨 — Slack services 없는 형태(OAuth 응답 예시)
PASS: 탐지됨 — 벤더 키 39자 본문(길이 경계)
PASS: 탐지됨 — 인라인 주석이 붙은 .env 값
PASS: 오탐 없음 — 일반 discord 채널 URL(비밀 아님)
PASS: 오탐 없음 — 코드 대입(값이 아니라 호출)
PASS: 오탐 없음 — 환경변수 참조(값이 없다)
PASS: 오탐 없음 — 산문 속 키 형식 언급
PASS: 오탐 없음 — 일반 Slack 워크스페이스 URL
PASS: 오탐 없음 — .env.example 의 예시 주소
PASS: 오탐 없음 — 숫자만 있는 설정값(재시도 간격)
PASS: 오탐 없음 — 접미사 위장 도메인(notdiscord.com)
PASS: 오탐 없음 — 접미사 위장 도메인(not-hooks.slack.com)
PASS: 오탐 없음 — CREDENTIAL 저장 방식 이름(글자 설정값)
PASS: 오탐 없음 — PRIVATE_KEY 형식 이름(짧은 글자+숫자 설정값)
PASS: 스캐너 종단 — 벤더 키 파일을 verify.sh 가 차단 (verify.sh exit=1)
PASS: 스캐너 종단 — 대문자 표기 웹훅도 차단(-i 손실 감지) (verify.sh exit=1)
PASS: 스캐너 종단 — 정상 파일은 verify.sh 가 통과 (verify.sh exit=0)
PASS: 저장소 무오염 (파일 상태[무시 포함] · HEAD · 객체 수 3축 동일)
CHECKED: 29
ACCEPT_RC=0
BEFORE_HEAD=08cc032389039d251e02bebf92b1f23bd79f88d8
AFTER_HEAD=08cc032389039d251e02bebf92b1f23bd79f88d8
BEFORE_OBJECTS=2
AFTER_OBJECTS=2
```

→ 뭘 시켰나: 현재 패턴과 실제 `verify.sh` 끝단을 포함한 29개 인수 검사를 전부 실행했습니다. / 뭐가 나왔나: 29개가 모두 통과했고 종료값은 0, 격리 복제본의 세 기준값은 전후 동일했습니다. / 좋은 소식인가 나쁜 소식인가: 핵심 기능에는 좋은 소식이지만 무오염 문구의 완전성은 별도 반례에서 깨졌습니다.

관련 코드 역할은 다음과 같습니다. `scripts/acceptance-secret-webhook-vendor.sh:85-115`는 잡아야 할 것과 잡지 말아야 할 것을 판정하는 역할, `:216-250`은 실제 `verify.sh`를 부르는 끝단 역할, `:280-289`는 정확히 29건인지 강제하는 역할입니다. `.secret-patterns.default:78-80`은 Discord·Slack·벤더 키 모양을 정하는 역할이고, `:94`는 WEBHOOK·CREDENTIAL·PRIVATE_KEY 대입문을 정하는 역할입니다. `verify.sh:55-83`은 인덱스 또는 작업 파일을 실제로 스캔하는 역할입니다.

## 2. 항목 1 — 직전 미탐 5종 독립 끝단 실행

정규식(문자열 모양을 표현하는 규칙)만 따로 시험하지 않고, 각 입력을 새 임시 Git 저장소에 `payload.txt`로 올린 뒤 `VERIFY_SCAN_SOURCE=index /bin/bash verify.sh`를 실행했습니다. exit code(프로그램 종료값)는 비밀을 찾으면 1이어야 합니다.

```text
Discord /api/v10/                    expected=1 actual=1  FAIL: secret pattern matched in tracked files: payload.txt
Discord canary 하위 도메인           expected=1 actual=1  FAIL: secret pattern matched in tracked files: payload.txt
hooks.slack-gov.com                  expected=1 actual=1  FAIL: secret pattern matched in tracked files: payload.txt
Slack services 없는 형태             expected=1 actual=1  FAIL: secret pattern matched in tracked files: payload.txt
sk-ant- + 39자 본문                  expected=1 actual=1  FAIL: secret pattern matched in tracked files: payload.txt
```

→ 뭘 시켰나: 직전 판정에서 새던 다섯 문자열을 실제 파일 스캐너에 각각 넣었습니다. / 뭐가 나왔나: 다섯 건 모두 기대한 종료값 1과 파일명 보고가 나왔습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식이며 반례를 찾지 못했습니다.

`scripts/acceptance-secret-webhook-vendor.sh:166-175`는 다섯 카나리(canary, 일부러 넣는 가짜 비밀값)를 구성하는 역할입니다. `.secret-patterns.default:78`은 `/api/v10/`과 Discord 하위 도메인을 허용하면서 접미사 위장을 막는 역할, `:79`는 GovSlack과 `services` 선택형을 처리하는 역할, `:80`은 39자 본문을 포함하도록 길이 경계를 낮춘 역할입니다.

## 3. 항목 2 — 직전 오탐 6종 독립 끝단 실행

같은 실제 스캐너에 정상 입력을 각각 넣었고 종료값 0을 요구했습니다.

```text
.env.example 예시 주소               expected=0 actual=0  PASS: no secret-pattern match
숫자 설정값 300000                   expected=0 actual=0  PASS: no secret-pattern match
notdiscord.com                       expected=0 actual=0  PASS: no secret-pattern match
not-hooks.slack.com                  expected=0 actual=0  PASS: no secret-pattern match
CREDENTIAL_PROVIDER=keychain         expected=0 actual=0  PASS: no secret-pattern match
PRIVATE_KEY_FORMAT=PKCS12            expected=0 actual=0  PASS: no secret-pattern match
```

→ 뭘 시켰나: 직전 오탐 여섯 형태를 추적 파일로 만들고 실제 스캐너를 실행했습니다. / 뭐가 나왔나: 모두 종료값 0으로 통과했습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식이며 요청한 오탐 반례는 해소됐습니다.

`scripts/acceptance-secret-webhook-vendor.sh:195-210`은 여섯 정상 대조군을 정의하는 역할입니다. `.secret-patterns.default:72-79`는 도메인 앞 경계로 위장 주소를 배제하는 역할이고, `:84-94`는 URL·숫자·12자 미만 설정 이름을 배제하는 역할입니다.

## 4. 항목 3~5 — 검사 삭제와 카나리 판별력

mutation(규칙이나 시험을 일부러 망가뜨려 시험이 진짜 실패하는지 보는 변이 검사)은 매번 격리 복제본에서 적용하고 `git checkout -- <파일>`로 되돌린 뒤 `git status --short`가 비었음을 확인했습니다.

```text
[검사 3개 삭제]
변이: scripts/acceptance-secret-webhook-vendor.sh:243-250의 e2e 호출 3개 제거
실행: /bin/bash scripts/acceptance-secret-webhook-vendor.sh
결과: exit=1
FAIL: 검사 항목 26개 ≠ 계약값 29개 (검사가 사라졌거나 무단 추가됐다 · P20)
CHECKED: 26

[기존 TOKEN 선택지 삭제]
변이: .secret-patterns.default:9,11의 |TOKEN 제거
실행: /bin/bash scripts/acceptance-secret-webhook-vendor.sh
결과: exit=1
FAIL: 통과됨(놓침) — BOT_TOKEN (기존 TOKEN 규칙 회귀 앵커 · 신규 규칙에는 없음)
CHECKED: 29

[신규 키워드 규칙 삭제]
변이: .secret-patterns.default:94 한 줄 제거
실행: /bin/bash scripts/acceptance-secret-webhook-vendor.sh
결과: exit=1
FAIL: 통과됨(놓침) — WEBHOOK 계열 .env 대입(불투명 토큰)
FAIL: 통과됨(놓침) — CREDENTIAL 계열 .env 대입
FAIL: 통과됨(놓침) — PRIVATE_KEY 한 줄 형태
FAIL: 통과됨(놓침) — 인라인 주석이 붙은 .env 값
CHECKED: 29
```

→ 뭘 시켰나: 검사 3개, 기존 TOKEN 보호, 신규 키워드 규칙을 각각 제거했습니다. / 뭐가 나왔나: 정확 개수 강제와 각 카나리가 모두 실패를 냈고 원복 뒤 복제본은 깨끗했습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식이며 죽은 중복·죽은 카나리 반례를 찾지 못했습니다.

`scripts/acceptance-secret-webhook-vendor.sh:145-154`는 WEBHOOK·CREDENTIAL·PRIVATE_KEY·BOT_TOKEN 카나리를 정의하는 역할, `:243-250`은 세 끝단 검사를 호출하는 역할, `:280-286`은 29와 다르면 즉시 실패시키는 역할입니다.

## 5. 항목 6 — 무오염 세 축의 양성 대조군과 반례

### 세 축이 고장을 잡는지

종료 측정 직전에 한 축만 바꾸는 코드를 격리된 스크립트 복제본에 주입했습니다.

```text
status 축: 새 파일 .axis-status-positive.tmp 잔존
exit=1
FAIL: 이 검사가 작업트리를 오염시켰다 — 시작/종료 상태가 다르다
?? .axis-status-positive.tmp

HEAD 축: 최종 HEAD를 08cc032...에서 d605f3c...로 이동
exit=1
FAIL: 이 검사가 HEAD 를 옮겼다 (08cc032... -> d605f3c...) — 판정 무효

object 축: git hash-object -w 로 새 객체 1개 기록
exit=1
FAIL: 이 검사가 git 객체를 남겼다 (45 -> 46) — 되돌린 척한 오염 (판정 무효)
```

→ 뭘 시켰나: 파일·현재 이력·객체를 한 축씩 실제로 바꿨습니다. / 뭐가 나왔나: 각 축의 전용 실패 문구와 종료값 1이 나왔습니다. / 좋은 소식인가 나쁜 소식인가: 세 분기 자체는 실제로 작동하므로 좋은 소식입니다.

`scripts/acceptance-secret-webhook-vendor.sh:33-38`은 시작 상태를 찍는 역할, `:257-259`는 종료 상태를 다시 찍는 역할, `:261-270`은 축별로 실패시키는 역할입니다.

### 세 축이 놓치는 것

같은 측정식을 독립 실행해 다음 네 반례를 만들었습니다.

```text
ignored-dir-collapsed-internal-add
  시작: !! artifacts/
  변경: artifacts/after.txt 추가
  종료: !! artifacts/
  결과: PASS_EQ

tracked-file-edit-then-restore
  변경: 추적 파일 수정 후 원문으로 복구
  status 동일, HEAD 동일, object file count 동일
  결과: PASS_EQ

head-move-away-and-back
  변경: HEAD~1 이동 후 원래 08cc032... 복귀
  최종 HEAD 동일, reflog에는 왕복 기록
  결과: PASS_EQ

object-count-same-identity-swap
  변경: 새 loose object 1개 추가 + 기존 loose object 1개 임시 이동
  객체의 정체는 달라졌지만 파일 수 동일
  결과: PASS_EQ
```

→ 뭘 시켰나: 세 숫자가 같게 남도록 실제 저장소 상태를 네 방식으로 바꿨습니다. / 뭐가 나왔나: 네 경우 모두 “같음”으로 통과했습니다. / 좋은 소식인가 나쁜 소식인가: 나쁜 소식이며 무오염이 아니라 제한된 종료 사진 비교임을 증명합니다.

또한 원본은 여러 작업 폴더가 `/Users/kangsangmo/Desktop/Valuehire_v6/.git/objects`를 공유합니다. 감사 중 원본 추적 상태와 HEAD는 그대로였지만 객체 파일 수는 관측 시점 41 또는 45에서 최종 66으로 늘었고, 읽기 전용 객체 헤더 대조상 PR #6이 아닌 다른 동시 작업의 저장 이력이었습니다. 따라서 이 축은 다른 작업 폴더의 정상 활동에도 실패할 수 있습니다.

## 6. 항목 7 — 커밋 사이 RED·GREEN과 시험 약화

RED(구현 전이라 의도한 실패가 나는 상태)와 GREEN(구현 후 성공하는 상태)을 각 커밋에서 실제로 실행했습니다.

```text
COMMIT=0e96bcc RC=1 CHECKED=27 FAIL_LINES=9
  discord /api/v10/, GovSlack, services 없음, 39자 경계 등 실패
COMMIT=4fb61d0 RC=0 CHECKED=27 FAIL_LINES=0
COMMIT=d7888c4 RC=1 CHECKED=29 FAIL_LINES=2
  keychain, PKCS12 오탐 실패
COMMIT=3bbe4b9 RC=1 CHECKED=29 FAIL_LINES=2
  keychain, PKCS12 오탐 실패
COMMIT=d605f3c RC=0 CHECKED=29 FAIL_LINES=0
COMMIT=08cc032 RC=0 CHECKED=29 FAIL_LINES=0
FINAL_HEAD=08cc032389039d251e02bebf92b1f23bd79f88d8
FINAL_STATUS=<empty>
```

→ 뭘 시켰나: 여섯 커밋의 당시 파일을 그대로 꺼내 같은 Bash 3.2 인수 검사를 돌렸습니다. / 뭐가 나왔나: 새 시험이 먼저 빨개지고 구현 뒤 초록이 되는 두 구간이 정확히 재현됐으며 최종 복제본은 원복됐습니다. / 좋은 소식인가 나쁜 소식인가: 시험 순서와 기대 종료값에는 좋은 소식입니다.

`0e96bcc`에서 `4fb61d0` 사이에는 카나리 호출과 기대 종료값이 삭제·완화되지 않았습니다. `d7888c4`는 정상 대조군 2개를 추가하고 정확값을 27에서 29로 올리며 `-lt`를 `-ne`로 강화했습니다. `3bbe4b9`는 `${K_WH}_SECRET_VALUE`를 `${K_WH}_SIGNING_VALUE`로 바꿔 기존 SECRET 규칙의 가림을 제거했고 기대 종료값은 바꾸지 않았습니다. `d605f3c`와 `08cc032`은 인수 스크립트 카나리를 삭제하지 않았습니다.

## 7. 항목 8 — 정본 문서와 실제 verify.yml 대조

CI(원격 서버가 push·pull request 때 실행하는 자동 검사)의 실제 작업 파일에는 checkout 이후 이름 있는 검사 단계 13개가 있습니다. `docs/sot/verification-commands.md:18-36`의 상세 표는 이 13개 순서와 실행 본문을 맞게 적었습니다.

```text
verify.yml 실제:
  on: push / pull_request / workflow_dispatch
  permissions: contents: read
  runs-on: ubuntu-latest
  uses: actions/checkout@v4
  fetch-depth: 0
  named verification steps: 13

verification-commands.md:
  line 3: 최종 갱신 2026-08-08
  line 14: CI는 추가로 acceptance-0-5, 0-6, 0-7을 실행
  lines 18-36: 실제 13개 단계 전수 표
  line 38: checkout과 fetch-depth 0만 간략 언급
```

→ 뭘 시켰나: 실제 작업 파일의 실행 조건·권한·환경·13개 단계와 정본 문서를 의미 단위로 비교했습니다. / 뭐가 나왔나: 상세 13단계는 맞지만 같은 문서 상단 설명·갱신일·실행 메타정보가 불일치하거나 빠졌습니다. / 좋은 소식인가 나쁜 소식인가: D6은 부분 수정됐지만 “문서 전체 일치”에는 나쁜 소식입니다.

`docs/sot/verification-commands.md:14`는 CI 추가 실행을 요약하는 역할인데 hs-a3·데이터 노출·hs-a4·secret-webhook-vendor를 빠뜨립니다. `:18-36`은 상세 13단계를 전수 기재하는 역할이라 같은 문서 안에서 충돌합니다. `.github/workflows/verify.yml:5-20`은 실제 트리거·권한·러너·checkout을 정하는 역할이고, `:22-156`은 실제 검사 13단계를 정하는 역할입니다.

`bash scripts/check-docs-sot.sh`는 종료값 0이었지만, `scripts/check-docs-sot.sh:16-39`는 필수 문서 존재와 크기만 검사하는 역할이고 `:41-63`은 훅 계약 경로만 검사하는 역할입니다. 따라서 이 통과는 `verification-commands.md` 내용이 `verify.yml`과 같다는 증거가 아닙니다.

## 8. 항목 9 — M1~M4 재현

M1~M4의 원래 정의는 `aeea77d` 커밋 메시지에서 확인했습니다. M1은 Discord 줄 삭제, M2는 Slack 줄 삭제, M3은 `sk-ant-`를 `sk-anz-`로 변경, M4는 신규 환경변수 키워드 줄 삭제입니다.

```text
M1 Discord pattern delete
  exit=1
  실패 5건: 기본 Discord, discordapp, /api/v10/, canary 하위 도메인, 대문자 verify.sh 끝단

M2 Slack pattern delete
  exit=1
  실패 3건: 기본 Slack, GovSlack, services 없는 형태

M3 sk-ant- -> sk-anz-
  exit=1
  실패 3건: 기본 Anthropic 키, 39자 경계, 벤더 키 verify.sh 끝단

M4 env keyword pattern delete
  exit=1
  실패 4건: WEBHOOK, CREDENTIAL, PRIVATE_KEY, 인라인 주석
```

→ 뭘 시켰나: 원래 네 변이 정의를 현재 HEAD에 그대로 적용했습니다. / 뭐가 나왔나: 모두 종료값 1로 실패했고, 추가 카나리 때문에 원래 3·1·2·3보다 현재 5·3·3·4로 더 많이 빨개졌습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식이며 네 규칙의 판별력은 유지됐습니다.

각 회차 뒤 변이 파일을 되돌렸고 복제본 `git status --short`는 비었습니다. 원본의 추적 상태와 HEAD는 바뀌지 않았습니다.

## 9. 항목 10 — macOS 기본 Bash 3.2

첫 문법 명령은 복제본으로 이동하기 전에 상대 경로를 넘겨 다음처럼 실패했습니다.

```text
GNU bash, version 3.2.57(1)-release (arm64-apple-darwin24)
/bin/bash: scripts/acceptance-secret-webhook-vendor.sh: No such file or directory
SYNTAX_RC=1
```

→ 뭘 시켰나: Bash 버전과 추적 셸 문법을 확인하려 했습니다. / 뭐가 나왔나: 버전은 확인됐지만 실행 위치 오류로 파일을 못 찾았습니다. / 좋은 소식인가 나쁜 소식인가: 이 출력만으로는 나쁜 소식이 아니라 무효 실행이므로 올바른 위치에서 다시 했습니다.

재실행 결과입니다.

```text
$ /bin/bash --version | sed -n '1p'
GNU bash, version 3.2.57(1)-release (arm64-apple-darwin24)
$ while ...; do /bin/bash -n "$f"; done < <(git ls-files -z '*.sh')
TRACKED_SH_COUNT=13
SYNTAX_RC=0
$ /bin/bash -n hooks/pre-commit hooks/pre-push
exit=0
$ /bin/bash scripts/acceptance-secret-webhook-vendor.sh
CHECKED: 29
exit=0
$ /bin/bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
exit=0
```

→ 뭘 시켰나: 정확한 복제본 루트에서 13개 추적 셸 파일과 훅 2개 문법, 전체 AC-S1, 실제 스캐너를 macOS 기본 Bash로 실행했습니다. / 뭐가 나왔나: 모두 종료값 0이었습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식이며 Bash 3.2 반례를 찾지 못했습니다.

`scripts/acceptance-secret-webhook-vendor.sh:61-64`는 Bash 4 전용 대소문자 확장을 금지한 이유를 적는 역할, `:78-83`은 `tr`로 호환 변환하는 역할, `:159-162`는 Bash 3.2 조합식 사고를 피하는 역할입니다.

추가로 로컬에서 재현 가능한 CI 본문을 Bash 3.2로 실행했습니다. 비밀 스캔, 과거 blob 143개 스캔, 0-6, 0-7, 억제 만료, 훅 존재, 셸 문법, 패턴 실값, hs-a3 25건, 데이터 노출, hs-a4 30건, AC-S1 29건은 모두 통과했습니다. `acceptance-0-5`는 PR 복제본에 main 참조가 없어 종료값 1이었지만 `.github/workflows/verify.yml:81-84`가 main에서만 실행하도록 정한 단계이므로 PR HEAD 실패로 세지 않았습니다.

## 10. 항목 11 — 새 커밋의 약화 표식과 의미상 약화

새 diff에서 다음 문자열을 찾았지만 신규 추가는 없었습니다: `|| true`, `continue-on-error`, `allow_failure`, `allow-failure`, `xfail`, `skip`, `if: always()`. `EXPECTED_CHECKS`는 오히려 `-lt`에서 `-ne`로 강화됐고 죽은 WEBHOOK 카나리는 중립 키로 교체됐습니다.

그러나 `d605f3c`는 `.secret-patterns.default`의 값 꼬리 길이를 `{4,}`에서 `{11,}`로 올렸습니다. 이 변경 전후를 같은 18개 입력으로 실행했습니다.

```text
이전 3bbe4b9 패턴:
WEBHOOK_VENDOR=A12345       길이 6  exit=1
WEBHOOK_VENDOR=A123456      길이 7  exit=1
WEBHOOK_VENDOR=A1234567     길이 8  exit=1
WEBHOOK_VENDOR=A12345678    길이 9  exit=1
WEBHOOK_VENDOR=A123456789   길이 10 exit=1
WEBHOOK_VENDOR=A1234567890  길이 11 exit=1
CREDENTIAL_ALIAS=B12345       길이 6  exit=1
CREDENTIAL_ALIAS=B123456      길이 7  exit=1
CREDENTIAL_ALIAS=B1234567     길이 8  exit=1
CREDENTIAL_ALIAS=B12345678    길이 9  exit=1
CREDENTIAL_ALIAS=B123456789   길이 10 exit=1
CREDENTIAL_ALIAS=B1234567890  길이 11 exit=1
PRIVATE_KEY_FORMAT=C12345       길이 6  exit=1
PRIVATE_KEY_FORMAT=C123456      길이 7  exit=1
PRIVATE_KEY_FORMAT=C1234567     길이 8  exit=1
PRIVATE_KEY_FORMAT=C12345678    길이 9  exit=1
PRIVATE_KEY_FORMAT=C123456789   길이 10 exit=1
PRIVATE_KEY_FORMAT=C1234567890  길이 11 exit=1

현재 08cc032 패턴:
위의 같은 18개 입력 전부 exit=0, matched=no
```

→ 뭘 시켰나: 오탐 수정 직전 패턴과 현재 패턴에 6~11자 값 18개를 똑같이 넣었습니다. / 뭐가 나왔나: 이전에는 전부 차단됐고 현재는 전부 통과했습니다. / 좋은 소식인가 나쁜 소식인가: 오탐 감소의 대가가 실제 탐지 축소임을 확인한 나쁜 소식입니다.

`.secret-patterns.default:91-94`는 이 대가를 주석으로 밝히므로 숨긴 변경은 아닙니다. 다만 `suppressions.yaml:1-4`는 줄이는 모든 결정을 담당자·사유·만료·이슈와 함께 기록하라는 역할인데 이 항목은 없습니다. `hooks/pre-commit:102-109`는 `.sh`, `.yml`, `.yaml`, `hooks/*`의 추가 줄만 약화 문자열로 보는 역할이라 `.secret-patterns.default`의 의미상 범위 축소를 잡지 못합니다.

※ base `5b39816`에는 이 신규 WEBHOOK 계열 규칙 자체가 없었으므로 base 대비 현재 HEAD는 순증입니다. 그러나 사용자가 요구한 “새 커밋 사이 기존 검사 약화” 관점에서는 4fb61d0/3bbe4b9가 한 번 잡던 6~11자 범위를 d605f3c가 제거한 사실이므로 항목 11을 불일치로 판정했습니다.

## 11. 항목 12 — 실제 실행의 저장소 오염 여부

격리 복제본에서 AC-S1 전후를 직접 측정했습니다.

```text
BEFORE_HEAD=08cc032389039d251e02bebf92b1f23bd79f88d8
BEFORE_STATUS_BEGIN
BEFORE_STATUS_END
BEFORE_OBJECTS=2
ACCEPT_RC=0
AFTER_HEAD=08cc032389039d251e02bebf92b1f23bd79f88d8
AFTER_STATUS_BEGIN
AFTER_STATUS_END
AFTER_OBJECTS=2
```

→ 뭘 시켰나: 인수 검사 전후의 무시 포함 파일 상태·HEAD·객체 파일 수를 외부에서 한 번 더 측정했습니다. / 뭐가 나왔나: 폐기 가능한 독립 복제본 안에서는 세 값이 모두 같았습니다. / 좋은 소식인가 나쁜 소식인가: 실제 AC-S1 실행이 복제본 저장소를 남겨 오염시킨 반례는 찾지 못한 좋은 소식입니다.

원본 최종 상태는 다음과 같습니다.

```text
STATUS_IGNORED_BEGIN
!! .omc/
!! .secret-patterns
STATUS_IGNORED_END
HEAD=08cc032389039d251e02bebf92b1f23bd79f88d8
COMMON_OBJECT_FILES=66
```

→ 뭘 시켰나: 원본을 쓰지 않고 최종 파일 상태·HEAD·공용 객체 파일 수를 읽었습니다. / 뭐가 나왔나: 두 무시 항목은 감사 전부터 있던 상태이고 추적 변경·HEAD 이동은 없었지만, 공용 객체 수는 다른 동시 작업 때문에 증가했습니다. / 좋은 소식인가 나쁜 소식인가: 원본 파일·HEAD에는 좋은 소식이나 공용 객체 축은 독립 증거로 쓸 수 없어 한계입니다.

한 격리 실행에서 macOS 도구가 강제한 임시 폴더 아래 `xcrun_db` 491바이트가 남았습니다. 저장소 밖 `/private/tmp`의 도구 캐시이므로 “저장소 오염”은 아니지만, 생성물 0개라는 더 넓은 뜻이라면 잔존물이므로 숨기지 않습니다.

## 12. 이전 판정 원문과 주장 대조

이 저장소가 가리킨 직전 판정 파일 `/Users/kangsangmo/Desktop/valuehire-verdicts-2026-08-12/codex-v1-verdict-pr6.md`의 SHA-256은 다음과 같았습니다.

```text
c9b197ec47fe27d6447802a0f7475263ad953d8fbe98266fcb7e78505aa94610
```

→ 뭘 시켰나: 현재 목표 문서가 적은 직전 판정 지문과 실제 보관 파일 지문을 비교했습니다. / 뭐가 나왔나: 정확히 일치해 D1~D8과 M1~M4 정의를 같은 원문에서 재확인했습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식이며 잘못된 과거 판정서를 대조한 위험은 없습니다.

직전 D1·D2·D3·D5의 핵심 기능 결함은 이번 실행에서 해소됐습니다. D4는 세 축이 추가됐지만 원 계약의 “오염 후 되돌려 통과하면 가짜”를 완전히 만족하지 못합니다. D6은 13단계 상세 표가 추가됐지만 같은 문서의 상단 요약·갱신일이 남았습니다. D7은 새 RED와 후속 RED가 실제로 보존돼 해소됐습니다. D8의 수치 불일치는 현재 목표 문서의 17 대 실제 29로 여전히 남아 있습니다.

## 13. 전체 로컬 검증 장부

| 실행 | 결과 | 무엇을 증명함 | 증명하지 못함 |
|---|---|---|---|
| `/bin/bash verify.sh` | exit 0 | 현재 추적 파일에 비밀 패턴 없음 | 과거 원격 CI 상태 |
| AC-S1 | 29건, exit 0 | 요청한 탐지·오탐·끝단 기본 동작 | 세 축의 모든 오염 가능성 |
| 개별 5개 악성 입력 | 각 exit 1 | 실제 스캐너가 각 형식을 차단 | 세상 모든 벤더 형식 |
| 개별 6개 정상 입력 | 각 exit 0 | 지정 오탐 6종 해소 | 모든 정상 설정 |
| 검사 3개 삭제 | 26 대 29, exit 1 | 정확 개수 강제 | 검사 교체로 의미를 바꾸는 모든 경우 |
| TOKEN 삭제 | BOT_TOKEN 실패 | 기존 규칙 카나리 생존 | 따옴표·공백 등 계약 밖 BOT_TOKEN |
| 신규 키워드 삭제 | 핵심 3+1 실패 | 신규 카나리 생존 | 12자 미만 실제 비밀 |
| 무오염 양성 3종 | 각 exit 1 | 세 실패 분기 동작 | 중간 변경·동일 개수 교체 |
| 무오염 반례 4종 | PASS_EQ | 세 축 사각지대 실증 | 권한 격리 방식의 효과 |
| 커밋 6개 실행 | 1·0·1·1·0·0 | RED/GREEN 순서와 카나리 보존 | 원격 당시 CI 로그 |
| M1~M4 | 각 exit 1 | 네 핵심 규칙의 현재 판별력 | 모든 정규식 변종 |
| Bash 3.2 문법 | 셸 13개+훅 2개 exit 0 | macOS 기본 Bash 호환 문법 | Linux 전용 외부 명령 차이 전체 |
| `scan-data-exposure.sh all` | exit 0 | 추적 54개·과거 blob 143개·PII 위반 0 | GitHub 서버 자체 설정 |
| `acceptance-hs-a3.sh` | 25건, exit 0 | 병합된 세션 비밀 검사 회귀 없음 | 실제 외부 계정 |
| `acceptance-hs-a4.sh` | 30건, exit 0 | 병합된 데이터 노출 검사 회귀 없음 | 실제 원격 보호 규칙 |
| `check-docs-sot.sh` | exit 0 | 문서 존재·크기·계약 경로 | verify.yml 내용 일치 |
| GitHub PR 조회 | 실패 | 없음 | 현재 labels·checks·원격 HEAD |

→ 뭘 시켰나: 이번 판정에 사용한 실행과 증명 범위를 한 장부로 묶었습니다. / 뭐가 나왔나: 핵심 동작 증거는 충분하지만 원격 상태와 완전 무오염은 증명되지 않았습니다. / 좋은 소식인가 나쁜 소식인가: 실행 근거는 강하지만 FAIL 결함을 뒤집을 공백은 아닙니다.

## 14. GitHub 원격 확인 실패 원문

```text
$ gh pr view 6 --repo sangmokang/Valuehire_v6 --json number,state,headRefOid,baseRefName,headRefName,labels,statusCheckRollup,url
error connecting to api.github.com
check your internet connection or https://githubstatus.com
EXIT=1
```

→ 뭘 시켰나: PR #6의 현재 원격 이력·표시·자동 검사 결과를 읽으려 했습니다. / 뭐가 나왔나: 실행 환경의 네트워크 차단으로 실패했습니다. / 좋은 소식인가 나쁜 소식인가: 로컬 판정을 무효로 하지는 않지만 원격 표시 준수는 확인하지 못한 한계입니다.

## 15. 최종 판정과 수정 우선순위

1. **REV2-D1:** 원본 쓰기 권한이 없는 독립 실행으로 바꾸거나 “세 축 종료 상태 동일”이라고 정확히 낮춰 쓰십시오. 목표 문서의 “오염 후 되돌려 통과하면 가짜”를 유지한다면 격리 없이는 합격시킬 수 없습니다.
2. **REV2-D3:** 6~11자 비밀 탐지를 복구하는 좁은 규칙을 설계하거나, 12자 정책을 책임자가 승인해 약화 원장과 PR 표시로 남기십시오.
3. **REV2-D2:** `verification-commands.md:3,14`를 실제 13단계·갱신일과 맞추고 실행 조건·권한·환경·checkout 버전을 정본 범위에 포함하거나 명시적으로 비범위 처리하십시오.
4. **REV2-D4:** 목표 문서의 `CHECKED: 17`을 29로, 무오염 계약을 실제 세 축과 알려진 한계로 갱신하십시오.

위 네 항목을 반영한 새 HEAD에서 본 문서의 12개 실행을 다시 해야 합니다. 현재 HEAD `08cc032`은 핵심 스캐너 기능은 좋아졌지만, 합칠 수 있는 완결된 검증 계약은 아닙니다.
