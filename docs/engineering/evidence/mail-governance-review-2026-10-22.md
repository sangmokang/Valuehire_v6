# PR #139 수정 검증 — 2026-10-22

## 결론

기존 우회 반례를 RED 커밋으로 고정하고 수정했다. Python 56개·Node 16개와 지정 변이 13개가 통과했다. dev 표본 7건의 레이블을 추가·독립 조회했으며 추가 발송은 0건이다. 전사 자동화는 미배포다.

검증 코드: `ac293550fb4da09b2cfb7023fd62aca88136a2f4`. 이 문서 이후 코드가 바뀌면 해당 SHA에서 재검증한다. 추적: [PR #139](https://github.com/sangmokang/Valuehire_v6/pull/139), [Issue #138](https://github.com/sangmokang/Valuehire_v6/issues/138). 자동 병합하지 않고 Issue를 닫지 않는다.

## 반례와 변경

| 항목 | 현재 계약·근거 |
|---|---|
| CE1 | 한 글자 인용·빈 HTML·숨긴 HTML·이름 치환·뒤쪽 개인화는 Golden 실패. 풍부한 plain/HTML 정상 예시 유지 |
| CE2 | 코드 소유 버전 `2026-10-21.v1`만 허용. 공백·임의 버전 거절. upstream 수정을 보존 |
| CE5 | RFC-ID 부재 시 로컬 identity·중복 위험을 명시하고 자동 공유 보류. 원본 레이블만 계획 |
| CE7 | 여섯 테이블의 INSERT/REPLACE·UPDATE/DELETE 방어를 일반·별도 연결에서 검증. DB 소유자의 파일 교체까지 보호한다는 주장은 없음 |
| CE12 | 유효한 표시명 주소를 엄격 파싱·정규화. 기존 dev 수신자·발신자·계정은 재전달하지 않음. 여러 주소·깨진 주소는 거절 |
| 마커 시험 | marker/dev-source/dev-sender 각각 새 fixture. 마커 방어만 제거해도 지정 시험 실패 |
| 최소 보존 | 일반 메일의 Golden 인용은 offset/SHA로 저장. Ontology 사건 인용·이유·직접 고객 원문 유지. 과거 행은 재작성하지 않음 |
| 표본 복구 | 원문 SHA/RFC를 실제 ZIP에서 검증. zero-effect 사전 실패를 기록하고 수신본 ID에 묶인 별도 레이블 작업만 생성 |

→ 구조 하한은 사소한 인용과 빈 HTML을 막는다. 회사 사실·직무 충실도·경력 적합성의 의미 판단이나 브라우저 computed CSS를 증명하지 않는다. 검토자의 축별 판단·후보자 적합성 선언이 필요하며 사람 승인 단계를 새로 추가하지 않았다. 기존 Golden 레이블은 추가 방식 계약에 따라 자동 삭제하지 않는다.

## 새 실행 증거

- Python discovery: **56/56**, Node MIME/ZIP: **16/16**. compileall, Node 구문 검사, diff 공백 검사, `verify.sh` 통과.
- 변이: **13 killed / 0 survived / 0 invalid**. 각 변이는 별도 합성 사본·새 interpreter에서 실행하며 지정 회귀 시험의 assertion 실패를 확인했다. 전체 가능한 변이의 커버리지 수치가 아니다.
- 필수 다섯 변이: 마커 단독, met 근거 필수, PLANNED→VERIFIED, source message ID, 표시명 정규화 제거 모두 적발. 추가 여덟 개는 버전·레이아웃 단락·RFC 부재·INSERT 방어·최소 보존·인용 하한·개인화 순서·레이블 부분집합이다.
- RED 커밋: `e7f43d94` 입력 반례, `14804937` 장부 반례, `25637b5a` 복구 계약, `bfc28b23` 수신 RFC 검사, `633f5757` legacy 관측, `14362eab` 수신본 바꿔치기, `30db337f` 옛 원문의 혼합 줄바꿈.

## 실제 표본과 남은 범위

2026-10-22 별도 인증한 원본·dev GET에서 원문 7건의 실제 RFC 바이트·SHA·Message-ID와 공유 작업 마커를 대조했다. 과거 plain 본문에 없고 HTML에만 있던 RFC 선언 때문에 멈춘 사전 검사를 실제 ZIP 원문 검증으로 교체했다. 기존 두 사전 실패 기록은 provider 변경 시도·추가 발송 모두 0이다.

기존 receiver-label 작업 7건에 사전 실패 근거를 append하여 `FAILED`로 남기고, 별도 후속 작업 7건을 `VERIFIED`로 완료했다. 레이블은 이름으로 계정별 조회·생성하고 추가만 적용했으며 실제 같은 수신본의 후속 GET으로 검증했다. 복구 전 존재한 여섯 테이블의 모든 행이 그대로 보존됨을 비교했고 SQLite integrity는 `ok`였다. 원본 레이블 작업 7건도 기존 `VERIFIED`를 유지한다. 이번 실행의 발송은 0건이다.

이전 share 7건과 share_repair 2건은 `SENT_UNVERIFIED`를 유지한다. 옛 send intent에 원문 SHA가 없어 새 코드의 공유 VERIFIED로 소급 승격하지 않았다. 원문 보존·수신 레이블의 실제 관측과 옛 발송 장부 상태를 구별한다. coverage 페이지 0·Ontology 미확정 2건·전사 backfill/수집 어댑터/스케줄러 미배포 상태도 유지한다.

현재 인증·읽기 근거는 원본 계정과 dev에서 직접 확인한 범위다. 전사 명단 관측은 계정별 전체 읽기·쓰기 성공을 뜻하지 않는다. 다른 계정의 readonly 성공을 근거 없이 주장하지 않는다. 실제 메일·ID·명단·원문·자격증명은 Git 제외 private 근거에만 보존한다.

일반 `verify` CI는 변경하지 않은 `suppressions.yaml`의 기존 세 항목이 2026-10-20에 만료되어 실패한다. 만료를 연장하거나 게이트를 끄지 않았다. mail-governance CI는 새 discovery와 변이 실행을 포함하며 원격 실행 결과는 PR checks에서 확인한다. 독립 Claude 검수 결과와 병합 판단도 PR에 별도로 기록한다.
