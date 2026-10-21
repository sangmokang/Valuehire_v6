# Claude 독립 검수 프롬프트

실행 프롬프트와 별도 세션에서 사용한다. 구현자의 결론을 승인하는 역할이 아니라 같은 요구를 독립적으로 깨뜨리는 역할이다.

```text
밸류커넥트 메일 분류·공유 PR을 읽기 전용 적대 검수해라. 코드를 고치거나 커밋·발송·레이블 변경·운영 DB 변경·권한 설정을 하지 마라. 합성 입력과 임시 DB에서만 실행 시험을 해라. 기존 로그인과 작업자의 변경을 보존해라.

저장소: /Users/kangsangmo/Desktop/Valuehire_v6
worktree: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/mail-governance-20261021
PR: https://github.com/sangmokang/Valuehire_v6/pull/139
Issue: https://github.com/sangmokang/Valuehire_v6/issues/138

먼저 AGENTS.md, docs/sot/git-workflow.md, docs/sot/mail-governance.md, tools/mail_governance/README.md를 읽어라. git status와 원격 PR base/head를 확인하고 검수 SHA를 고정해라. 6139d61a는 과거 검수 코드다. 로컬 HEAD·원격 HEAD·미커밋 diff가 다르면 각각 밝히고 새 변경을 놓치지 마라. 코드가 검수 중 바뀌면 SHA 사본에서 재현하고 한계를 보고해라.

docs/engineering/evidence/mail-governance-pr139-current-review-2026-10-21.md는 과거 근거와 미해결점의 출발점으로만 읽고 결론을 그대로 복사하지 마라. 원래 요구는 JD/면접/온톨로지/일간주간 분류, 후보자용 Golden의 네 축, 고객/포지션/후보자/지원회차별 근거 보존, dev 공유 및 같은 레이블, 전 멤버 과거·향후 적용이다. 오프라인 코어와 실제 운영을 분리해 검수해라.

반드시 재현할 경계
1. 같은 내용의 비골든 검토 뒤 rule_version 끝 공백·임의 새 값·다른 표기로 불변 검토를 우회하거나 Golden 계획을 만들 수 있는가? 버전 권한이 코드/실행 설정에 있는가? SOT·예시·코드가 같은 버전 계약인가? 진짜 버전 이관은 과거 검토를 보존하는가?
2. 각 축 한 글자와 HTML <br>, 긴 무관한 인용, 이름만 치환, 다른 직무 개인화, 인용된 옛 JD, 비공개 내부 메모가 Golden으로 통과하는가? 정상적인 풍부한 plain text와 정돈된 HTML은 통과하는가? Golden 내용 검토와 구조 검증을 최소 길이 하나로 대체하지 않았는가?
3. 미러 marker만 있음, dev account만 있음, dev sender만 있음의 입력이 서로 독립되어 있는가? met 근거 필수, PLANNED→VERIFIED 금지, 원본/수신 식별, 수신 레이블 포함 검사를 각각 삭제해 시험이 실패하는가? source_labels는 원본 account/message_id와 일치해야 한다. receiver/share의 receiver_observation·label_observation·archive_observation은 필요한 관측끼리 같은 실제 수신 message_id를 가리키고 source_identity는 계획 원본과 일치해야 한다. 서로 다른 메일함의 provider message ID가 같아야 한다는 뜻은 아니다. 다른 오류 때문에 우연히 거절된 시험은 방어 검증으로 인정하지 마라. 필요한 다른 관측은 모두 정상으로 채워라.
4. INSERT OR REPLACE와 REPLACE INTO, 일반 UPDATE/DELETE, 재접속·동시 선점에서 장부 보장이 유지되는가? 앱 계약과 악의적 DB 소유자 방어의 차이를 구별해라. 내부 메일 전문이 evidence quote나 다른 경로로 남는가? 필요한 정확한 인용과 직접 고객 Ontology 원문 보존도 지켜지는가?
5. 이미 수신된 메일에 레이블을 붙이는데 재발송하는가? SENDING/AMBIGUOUS를 재실행 허가로 취급하는가? 실제 효과가 없는 사전 실패와 실행 여부 미확정을 구분하는가? 기존 실패 관측을 덮거나 버전 변경으로 재시도하는가?
6. 수신 ZIP의 실제 original.eml 바이트·SHA·RFC identity를 독립 검증하는가? 발신 payload를 수신 관측으로 복사하지 않았는가? 다른 메시지/계정/해시/레이블을 넣으면 거절하는가? 레이블 추가 후 독립 GET이 있는가? 최초 실패 2건과 보완 공유가 정직하게 구별되는가?
7. 전사 명단·계정별 접근·query/cursor 끝·cap/429/오류·미확정·스케줄러/운영 어댑터 배포가 실제 근거로 확인되는가? 정상 빈 검색을 무조건 결함으로, 혹은 검사하지 않은 범위를 완료로 판단하지 마라.

운영 증거는 필요할 때 /Users/kangsangmo/Desktop/Valuehire_v6/artifacts/mail-governance-20261021/에서 읽기 전용으로 보아라. Git 밖에 있어도 본문·이름·실제 메시지 ID·명단·토큰을 보고서나 공개 Git에 복사하지 마라. pilot.sqlite는 mode=ro로만 열어라. auth-after-modify.private.json은 두 계정의 토큰·프로필·레이블 조회 200을 보여주며 모든 계정 메시지 변경 성공을 입증하지 않는다. 과거 401을 현재 원인으로 단정하지 마라. receiver-label-apply*.private.json, dev-label-before.private.json, 현재 장부를 교차 확인해라. 접근할 수 없으면 운영 주장은 미확인으로 표시하고 합성 코드 검수는 계속해라.

과거 상태를 그대로 인용하지 마라. 인계 시점 장부는 source_labels 7 VERIFIED, receiver_labels 7 SENDING, share 7와 share_repair 2 SENT_UNVERIFIED였다. receiver 레이블 사전 검사 두 번은 변경 시도/추가 발송 0이었다. 이후 구현자가 복구했다면 최신 provider 관측과 append-only 장부로 반증해라. 과거 share 6 SENDING과 혼동하지 마라.

다음은 그 자체로 자동 결함이 아니다: 고객사가 후보자 철회를 알리는 사건, RFC-ID 없는 계정별 보수적 identity, 정상적으로 끝난 검색의 결과 0건. Golden 사람 승인 의무는 기존 사용자 요구가 아닌 새 제안이다. 필요하다고 생각하면 요구 누락과 구별해 제안으로 적어라.

Python/Node 정상 시험을 직접 실행하고 필요한 합성 반례·방어 제거 변이를 실행해라. 초록 시험만으로 승인하지 마라. 과거 21개 중 9개 생존, 14개 통과 같은 수치를 최신 실행 결과로 사용하지 마라. 실제 실행한 변이 수, 살아남은 수, 의미 없는 변이, 실행하지 못한 검사를 각각 밝혀라. 가드/checker를 변경했다면 그것 자체를 우회하는 반례도 시험해라.

결과 형식
- 첫 줄: APPROVE / COMMENT / REQUEST_CHANGES, 검수 SHA, 병합 가능 여부.
- HIGH 이상 결함부터 file:line·요구사항·최소 재현·실제 결과·영향·수정 권고를 적어라. 근거 없는 위험은 확정 결함으로 쓰지 마라.
- 수정 전 지적별 FIXED / STILL_REPRODUCIBLE / CONTRACT_TRADEOFF / NOT_VERIFIED 표를 제시해라.
- 정상 시험 및 변이 결과, 운영 관측 시각, 현재 코드/표본/전사 상태, 아직 검증 못한 점을 밝혀라.
- 코드 검수 추천과 설계 CLEAR/WATCH/BLOCK을 별도로 적고, BLOCK이나 HIGH 미해결이면 REQUEST_CHANGES로 종합해라.
- 보고서는 /Users/kangsangmo/Desktop/Valuehire_v6/artifacts/mail-governance-20261021/ 아래 새 이름으로 0600 저장하고 경로를 알려라. 기존 근거를 덮어쓰지 마라. 공개용 요약은 개인 식별 정보를 제거해라.
```
