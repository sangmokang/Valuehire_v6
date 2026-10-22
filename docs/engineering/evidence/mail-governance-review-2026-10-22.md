# PR #139 수정 검증 — 2026-10-22~23

기존 CE1·CE2·CE5·CE7·CE12와 마커 누적 시험 결함을 수정한 뒤, 남아 있던 HTML·공통 CI·과거 발송 미해소를 추가로 검증했다. 자동 병합하지 않으며 [Issue #138](https://github.com/sangmokang/Valuehire_v6/issues/138)은 전사 수집 배포까지 열린 상태로 둔다. [PR #139](https://github.com/sangmokang/Valuehire_v6/pull/139).

첫 추가 수정은 `02321732`이며 후속 검수 반례는 `09d81565`, `e4d9b15f` RED로 먼저 고정했다. 최종 Git HEAD의 고정 코드 파일 SHA256와 별도 검수 입력을 대조하며, 원격 실행 결과는 PR checks와 후속 검증 댓글에서 정확한 SHA로 대조한다. 이전 SHA의 성공을 현재 코드의 성공으로 대체하지 않는다.

## 보존한 수정과 새 반례

- 원격 `400a9558`의 계정/RFC 동치 식별자·숨김 수치 표현 보강을 fast-forward로 보존했다.
- `eaeee74c`, `70b6e199`에서 교차 종료·비 void 자기종료·중복 속성·CI 실행 증거·과거 해소·P13 삭제/범위 반례를 먼저 RED로 커밋했다.
- `ba4a9702`는 모호한 HTML을 골든 근거에서 제외한다. 지원하는 생략 문단/목록, 실제 void 태그, 엔티티와 부분 인용의 정상 대조군은 유지한다.
- 별도 검수는 기본 닫힌 `details`의 본문이 실제 Chromium에서 모두 보이지 않는데 골든이 되는 반례를 재현했다. 닫힘·중첩 반례와 명시적 `open` 정상 대조군을 추가해 `082ebd44` RED 뒤 수정했다. `open="false"`도 boolean 속성이 있으므로 열린 상태다.
- 구조 하한은 사소한 인용과 숨김 우회를 거절한다. 회사 사실·직무 충실도·개인화 의미나 완전한 HTML5/CSS 렌더링을 증명하지 않는다. 사람 승인 단계를 새로 추가하지 않았으며 기존 Golden 레이블은 자동 삭제하지 않는다.

## 역사적 발송 해소 — 실제 실행

기존 share 7건에는 이전 형식 `raw_sha256`가 있었다. 이전 보고의 “원문 SHA가 없다”는 표현은 부정확했다. 새 계약 필드 `original_sha256`와 구별해 기존 값을 대조했으며 영수증을 바꾸지 않았다. 보완 전송 2건에는 자체 발송 전 해시가 없어 현재 원본과 parent의 기존 해시를 대조했다.

- 별도 인증한 원본·보낸편지함·dev 수신본 **9건**을 readonly로 다시 조회했다. 기존 송수신 ID·작업 marker·현재 원본 RFC 바이트와 실제 수신 ZIP 내부 원문 SHA를 대조했다.
- **5개 기존 원본 + 2개 기존 보완본 = 7개**의 ZIP 원문 일치와 필수 레이블을 확인했다. 처음 실패한 2개 복사본은 원문 보존 실패를 계속 명시한다. 이 2개를 양호한 ZIP으로 세지 않는다.
- 복제 장부에서 먼저 해소한 뒤 운영 장부에 불변 `delivery_resolutions` **9행**을 추가했다. 결과는 `ARCHIVE_CONFIRMED_AFTER_DELIVERY` **7건**, `REPAIRED_BY_CONFIRMED_DELIVERY` **2건**, 고유 원본 **7건**이다.
- 이전 여섯 테이블의 모든 행·열 값·순서를 전수 비교해 보존했다. 기존 발송 상태는 여전히 `SENT_UNVERIFIED`; 별도 해소 결과를 새 계약의 `VERIFIED` 영수증으로 소급 표시하지 않는다. 새 발송 **0건**, 이번 관측·해소 과정의 provider 변경 **0건**이다.
- 앞선 레이블 복구에서는 원본 7건·유효 dev 수신본 7건의 요청한 동일 레이블 이름을 독립 조회했다(**14/14**). 이번 재조회도 유효 수신본 7건의 레이블을 확인했다. 실패 복사본 2건의 레이블까지 일치한다고 주장하지 않는다.

해소 API는 source/RFC/내용 해시, 실제 송수신 ID, 원문 SHA, marker, 독립 레이블, 보완 prior 연결을 검증한다. 관측 JSON과 보고서 해시는 신뢰된 어댑터 주장이지 Gmail의 암호학적 증명은 아니다. SQLite 방어는 일반 UPDATE/DELETE/INSERT OR REPLACE를 막지만 DB 소유자의 테이블 삭제/파일 교체를 막는다고 주장하지 않는다.

## 공통 CI의 실제 원인 수정

만료일 연장이나 검사 비활성화 없이 아래 세 억제의 원인을 수정했다. 해당 회귀의 통과 근거를 확인하고 활성 억제를 원장에서 제거했다.

| 기존 억제 | 수정과 검증 |
|---|---|
| `ci-transfer-guarantee` | 성공한 실제 wrapper가 경로/SHA 마커를 남기고 **같은 run/attempt**의 마지막 단계에서 현재 파일과 전량 대조한다. 직전 성공 run은 현재 SHA의 증거가 아니다. verify.sh도 포함하고 CI 기대 목록 축소를 거절한다. 0-2 로컬 전용·0-5 main 조건 면제 이유는 코드에 명시한다. |
| `p13-deletion-blindspot` | HEAD와 staged workflow 전체의 실행 명령/uses multiset을 비교한다. 스텝/파일/명령 삭제, no-op 치환, Actions 밖 이동, symlink 교체를 거절하고 이름 변경/Actions 안 이동은 허용한다. |
| `gate-scope-gaps` | workflow/skill 자기제외를 검사한다. 파일명 대신 명시된 외부효과 entry의 지원되는 정적 import/호출 경로를 검사하며 순수 타입을 오탐하지 않는다. 선언 삭제/축소·그림자 함수·동적/분석 불가 경로를 거절한다. |

외부효과 검사는 제한된 문법의 호출 경로 증거다. 선언되지 않은 의도, 조건 분기의 실제 실행, 인증·응답·전달 성공은 추론하지 않는다. 마커도 workflow 편집 권한자의 위조를 암호학적으로 막지 않는다. 삭제/약화 검사와 오너의 diff 검토를 함께 적용한다. [선언 및 분석 범위](../../../scripts/verify/external-effect-contract.md).

## 실행 증거와 남은 범위

- 현재 확인된 Python **127/127**, MIME/ZIP Node **16/16**.
- 방어 제거 변이 **44 killed / 0 survived / 0 invalid**. 전체 discovered 정상 baseline을 한 번 실행하고 각 변이는 새 사본에서 지정 회귀와 정상 대조 시험을 수행한다. 지정 회귀의 `AssertionError`만 적발로 인정하며 runtime/import/setup 오류는 무효다. 전 가능한 변이의 coverage 수치가 아니다. 닫힌 `details`·`dialog`, UA 숨김, 전체 과거 영수증 충돌, 지원 HTML/표/wrapper/script 문맥과 정상 대조군을 포함해 재실행했다. 부모 단일 방어만 제거한 별도 진단 **2건은 기대 생존**이며 핵심 44건 집계에 섞지 않는다. 약했던 own-receipt 적발도 실제 `ValueError not raised`로 바뀐 것을 확인했다.
- CI 실행 증명 **CHECKED 18**, workflow 우회 8종 차단, 구조 검사 **35**, mechanism 명부 **24**. P13 경계 **30/30**과 실제 선언 **3개** 확인. 실제 JS 바인딩 호환 변경 뒤 영향받는 4건과 실제 선언 3개도 재검증했다. 기존 0-7은 행동 6종이 모두 통과했으나 당시 동시 편집으로 원본 상태 보존 검사에서 실패했으므로, 이전 결과를 최종 성공으로 세지 않는다. 이 문서를 포함한 고정 커밋에서 실행할 pre-push·0-7 전체 exit 0·원격 CI를 별도 SHA 귀속 PR 증거로 남긴다. 억제 0건 정상 입력과 실제 억제의 날짜 필수·빈 값·잘못된 값·만료·미래 날짜 회귀 3개도 통과했다. 최종 P13 경계 suite는 이를 포함해 33개이며 전체 실행 결과는 같은 PR 기록에 남긴다.
- 현재 명단 9계정 모두 `gmail.readonly`·`gmail.modify` scope token과 일치하는 profile/label-list 조회가 성공했다. 일시적인 한 계정의 429는 별도 재시도로 성공했고 첫 실패 관측도 보존했다. scope 인증은 모든 계정의 실제 label modify 성공과 다르다. 실제 변경 검증은 기존 원본·dev 표본 범위다.
- **coverage 페이지 0, Ontology entity 미확정 2건, 전사 backfill/수집 어댑터/스케줄러 미배포**다. 전체 멤버 과거·신규 메일 정리가 완료됐다고 주장하지 않는다.
- 실제 메일·명단·ID·원문·인증 정보는 Git 제외 private 근거만 사용한다. private 파일/디렉터리는 0600/0700으로 점검했다. 후보자 발송·자동 병합은 없다.

Claude의 최초 32파일 도구 기반 검수는 600초 시간 초과로 판정을 받지 못했다. 이를 승인으로 표시하지 않는다. 읽기 전용 코드 본문 검수 재시도와 최종 SHA의 실행 검증 결과는 PR 후속 댓글에 구분해 남긴다. 코드 스냅샷과 Git blob의 SHA256를 대조해 검수 대상의 일치를 확인한다.


## Claude 후속 반례와 수정

코드 본문 17파일 정적 검수는 `REQUEST_CHANGES`였다. Claude는 코드를 실행하지 않았고, 실행 증거는 별도 로컬 시험이다.

- **H1:** job 수준 `env`에서 허용되지 않는 `runner.temp` 참조를 제거했다. checkout 뒤 첫 wrapper 이전에 runner 셸의 `RUNNER_TEMP`와 run/attempt로 경로를 만들고 `GITHUB_ENV`에 전달한다. 새 단위 3건 RED 뒤 전체 6/6 GREEN이며 공백 경로와 attempt 격리도 확인했다. [GitHub context availability](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#context-availability).
- **M1:** 보완 발송이 원본과 같은 송신/수신 ID를 재사용하지 못하게 했다. sender만 동일·receiver만 동일·둘 다 동일한 3개 독립 회귀를 RED 후 수정했다. 역사적 발송 14/14 시험을 통과했고 기존 운영 해소 9건도 readonly로 재검증했다. 실제 보완 2건은 송신/수신 ID가 각각 구분되며 DB 바이트는 불변이었다.
- **M2:** Chromium에서 기본 숨김인 `dialog`, `datalist`, `rp`, `noembed`, `noframes`, `iframe` 본문을 확인했다. 숨김 인용과 보이는 중복 layout을 분리한 반례까지 6종을 RED 후 막았다. 열린 dialog/일반 본문을 포함한 visibility 18/18은 통과했다.
- **빈 억제 원장:** here-string이 항목 0건에도 빈 행을 만들어 오류로 처리하던 훅을 process substitution으로 수정했다. 실제 빈 expiry를 거절하는 방어는 유지했다. 만료일을 추가하거나 연장한 것이 아니다.

두 번째 정적 검수도 `REQUEST_CHANGES`였고, 같은 결함의 일반형 M1′·M2′와 표 재배치 M3를 추가로 발견했다. `aacd613b`에서 실패를 먼저 고정하고 `d75c475a`에서 다음을 수정했다.

- **M1′:** 모든 share/share_repair의 과거 `SENT_UNVERIFIED` 영수증을 검사한다. 계정을 정규화한 sender ID와 dev 수신 ID의 다른 작업 충돌, 자기 작업의 모순된 쌍, legacy 별칭 충돌을 막는다. 다른 계정의 같은 sender ID와 동일 관측 반복은 정상으로 유지한다. 역사 회귀 **25/25**와 독립 회귀 **6/6**을 통과했다.
- **M2′·M3:** 지원 HTML 태그 목록과 엄격한 표 부모/자식 관계를 적용한다. 미지원 요소는 인용 밖에 있어도 거절하며, 표의 직접 텍스트와 문자 참조도 HTML 공백만 허용한다. caption/thead/tfoot과 ruby 등 복잡한 표시 구조를 지원 범위에서 제외한다. 정상 표, 부분/엔티티 인용, 일반 본문은 유지한다. 초기 22개 및 추가 18개 subcase의 실패를 확인한 뒤 visibility **26/26**을 통과했다.
- 운영 장부의 9건 전체를 계정 범위까지 적용해 readonly로 대조했다. 작업 간 sender/receiver ID 충돌은 **0건**이며, 일반화한 새 guard로 해소 9건도 다시 검증했다. DB 바이트는 불변이고 새 발송·provider 변경은 각각 **0건**이다.
- 독립 브라우저 검수는 뒤에 붙인 `body hidden`/`html hidden` 속성이 기존 본문으로 병합되는 추가 반례를 재현했다. 정상 문서와 선행 metadata 대조를 유지하며 문서 wrapper의 위치와 반복을 검사한다.

세 번째 정적 검수는 앞선 일반화와 wrapper 수정을 해소로 판정했지만, script 이중 이스케이프 **M4**를 추가로 발견했다. `d38ff2e9`에서 닫힘/EOF 공격을 RED로 고정했다. 각 script의 raw data에서 `<!--`를 콜백 경계까지 검사하며, 별도 script에는 상태를 초기화해 정상 metadata를 보존한다. 전체 HTML5 토크나이저를 추가한 것은 아니다. 최종 visibility **30/30**, 역사적 발송 **27/27**을 통과했다. 독립 Chromium 재검증도 숨김 반례 2개 거절·정상 4개 표시를 확인하고 exit 0으로 종료했다.

예비 43개 변이 중 own-receipt 1개의 실패는 예외 문구 차이뿐이었다. 이를 최종 적발 근거로 사용하지 않는다. `d38ff2e9`는 원본/최신 영수증에 각각 일치하는 proof를 독립 fixture에서 검사하도록 보강했다. 삭제 변이에서 실제 `ValueError not raised`가 발생하고 정상 대조 4개가 통과하는 것을 별도로 확인했다. 핵심 변이와 부모 단일 방어만 제거한 중복 방어 진단의 기대 생존은 분리해 집계한다.

M4·시험 충실도를 대상으로 실제 코드 4파일을 제공한 마지막 정적 검수는 **APPROVE**였다. Claude는 코드를 실행하지 않았고, 앞선 일반화 검수의 나머지 해소 판정과 이번 한정 범위를 구분한다. 낮은 위험의 script 꼬리 초기화 단위 대조 한계는 남으며, 분할 콜백과 초기화는 별도 합성 진단으로 확인했다. 최종 변이의 실제 미거절 메시지와 현재 SHA verify의 마지막 마커 단계 성공은 실행 증거로 따로 확인한다. 고정 SHA의 최종 결과는 PR 검증 댓글에 별도 기록한다. 이는 전사 수집 배포 완료를 뜻하지 않는다.
