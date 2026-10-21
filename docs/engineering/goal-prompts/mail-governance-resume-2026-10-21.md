# clear 후 Codex 실행 프롬프트

아래 본문을 새 세션에 전달한다. 고정된 상태 설명은 인계 기준이며, 실행 시작 시 Git·장부·provider 관측으로 다시 확인한다.

2026-10-22 후속: 아래 2026-10-21 스냅샷의 결함·표본 복구는 `a255c8bb`까지 RED 커밋·수정·추가 반례 검증으로 처리했다. Python 65·Node 16·지정 변이 16개를 통과했고, 원본·dev 각 7건의 동일 레이블을 새 readonly GET으로 확인했다. 원본의 영문 Ontology 레이블 2건은 별도 보완 intent로 한국어 정본을 추가했으며 기존 행은 보존했다. [최신 검증](../evidence/mail-governance-review-2026-10-22.md)을 먼저 읽고 해결된 작업을 재실행하지 않는다. 특히 receiver-label 옛 7건은 FAILED, 별도 후속 7건은 VERIFIED이며 추가 발송은 0건이다. 다음 세션은 최신 PR/CI·Claude 결과를 확인하고 전사 어댑터·coverage·배포의 남은 범위를 이어간다.

```text
밸류커넥트 메일 분류·공유 작업을 이어서 실행해라. 계획 제안으로 끝내지 말고, 이미 허가된 가역적 수정·시험·검증·의미 단위 커밋을 진행해라.

작업 위치
- 저장소: /path/to/Valuehire_v6
- 작업 worktree: /path/to/Valuehire_v6/worktrees/mail-governance-20261021
- 브랜치: task/mail-governance-20261021
- Issue: https://github.com/sangmokang/Valuehire_v6/issues/138
- PR: https://github.com/sangmokang/Valuehire_v6/pull/139
- 검수한 코드 SHA: 6139d61a19ebcf7c046be9a3e0e3828dff4406fb. 실행 시 최신 HEAD와 원격을 확인하고 후속 변경을 보존해라.

먼저 적용되는 AGENTS.md를 읽고 아래 문서를 읽어라.
1. docs/sot/git-workflow.md
2. docs/sot/mail-governance.md
3. docs/engineering/evidence/mail-governance-pr139-current-review-2026-10-21.md
4. tools/mail_governance/README.md
루트 main의 무관한 미커밋 변경은 건드리지 마라. 실제 메일·원문·명단·메시지 ID·자격증명은 공개 저장소에 넣지 마라.

원래 업무 계약
- JD는 01JD, 면접은 05인터뷰메일, 일간/주간은 04dailyweekly, 채용 이력은 06온톨로지다. 다중 레이블을 허용하고 기존 레이블은 보존한다.
- Golden은 후보자용 문서의 회사 설명·직무 충실도·상단 경력 기반 개인화·읽기 좋은 구성이 모두 충족되고 비공개 내부 메모가 섞이지 않을 때만 01JD/goldensample과 01JD를 부여한다. 내부 맥락이 풍부한 JD와 후보자용 Golden을 혼동하지 마라.
- 고객사/포지션/후보자/지원회차별 업데이트와 피드백·거절 이유를 출처·원문 근거와 연결해 append-only로 보존한다. 모르는 ID와 이유는 미확정으로 남긴다.
- 위 업무 메일은 dev@valueconnect.kr에 원문을 보존해 공유하고 원본과 dev에 같은 레이블 이름을 적용한다. 이미 사용자 허가가 있다. 후보자에게 보내는 연락은 허가 범위가 아니다.
- 원래 대상은 전 멤버의 과거·향후 메일이다. 표본 복구나 오프라인 코어를 전사 완료로 보고하지 마라.

현재 확인된 문제부터 수정해라.
1. rule_version을 입력 검토자가 임의로 정해 불변 검토를 우회한다. 같은 내용의 비골든 검토 후 버전 끝 공백으로 Golden 새 계획이 생긴다. 실행 설정이 버전을 소유하도록 하고 허용하지 않은 공백·형식·임의 버전은 거절해라. trim만 추가하지 마라. 진짜 버전 변경·재검토 이관은 명시적으로 설계하고 SOT/예시/코드를 통일해라.
2. 회사/직무/개인화 근거 각 한 글자와 HTML <br>로 Golden이 된다. SOT에 맞춰 내용 검토와 실제 레이아웃 검증의 책임을 구현해라. 길이만 늘린 근거·긴 무관한 인용·이름 치환·잘못된 직무·인용된 옛 JD·내부 메모를 반례로 포함해라. 의미를 regex 하나로 증명했다고 말하지 마라. 사람 승인 의무는 기존 요구가 아니므로 임의로 추가하지 마라.
3. marker-only, dev-source-only, dev-sender-only 시험은 서로 독립된 fixture를 써라. met인데 evidence가 없는 입력, 올바른 관측을 넣은 PLANNED→VERIFIED 시도, 계정/해시/레이블은 맞고 message ID만 다른 관측, 누락된 레이블을 각각 거절하는 회귀 시험을 먼저 고정해라. 방어를 하나씩 지우는 변이로 시험 자체를 검증해라.
4. 내부 메일 전문이 layout evidence quote로 그대로 저장되는 문제와 SQLite INSERT OR REPLACE로 기존 행이 바뀌는 문제를 재현 후 수정해라. 합법적인 정확한 인용·Ontology 보존·동시 선점·재접속 계약은 유지해라. 악의적 DB 소유자까지 보호한다고 과장하지 마라.

운영 복구는 코드 계약과 맞춘 뒤 진행해라.
- private 근거 위치: /path/to/Valuehire_v6/artifacts/mail-governance-20261021/ (Git 제외).
- pilot.sqlite를 먼저 read-only 집계해라. 인계 시점 source_labels 7 VERIFIED, receiver_labels 7 SENDING, share 7와 share_repair 2는 SENT_UNVERIFIED다. 새 Golden 0, Ontology 2 미확정, coverage 페이지 0이다.
- receiver-label-apply.private.json과 receiver-label-apply-v2.private.json은 사전 원본 식별 검사에서 중단했다. 두 기록의 provider 변경 시도와 추가 발송은 모두 0이다. 이 SENDING 7건을 과거 Claude의 share SENDING 6건과 혼동하지 마라.
- dev의 고유 원문 7개는 앞선 독립 수신 ZIP 바이트 검증을 통과했다. 이미 도착한 메일에 레이블을 붙이기 위해 재발송하지 마라. 최초 첨부 실패 2건과 별도 보완 작업을 유지해라.
- 기존 SENDING을 열어 실행할 권한으로 취급하지 마라. 실제 효과가 없다고 입증된 사전 실패와 실행 여부 불확실을 구별하고, 근거를 append해 조정해라. 기존 행을 UPDATE/DELETE/REPLACE하거나 버전을 바꿔 재시도를 만들지 마라. 명시적인 보완/후속 작업이 필요하면 계약·시험부터 추가해라.
- reconcile-dev-labels.mjs의 사전 검사 실패 원인을 확인해라. 본문의 plain/HTML 표현 차이 가능성은 가설이다. 수신 original.zip의 실제 original.eml RFC Message-ID와 저장 원문 SHA-256을 엄격히 대조해라. 발송측 선언이나 본문만 복사한 값을 독립 수신 관측으로 쓰지 마라.
- 원본/dev 각 계정의 레이블 ID를 이름으로 조회하고, 원본 출처·작업 marker·수신 원문을 검증한 뒤 추가만 적용해라. 독립 GET으로 동일 메시지와 필요한 레이블을 확인해야 VERIFIED다. 실패 또는 관측 불일치는 미확정으로 남겨라.

인증은 이미 진행됐다. auth-after-modify.private.json은 대표/dev 두 계정의 gmail.modify 토큰·프로필·레이블 조회 200 근거다. admin-roster.private.json에는 활성 9계정·전체 조직 1/1페이지 관측이 있다. 실제 모든 계정 메시지 변경까지 검증된 것은 아니다. 과거 401만 보고 인증을 처음부터 반복하지 마라. 새 호출로 필요한 권한을 확인하고 기존 로그인은 유지해라. 브라우저가 필요하면 aside-browser 스킬을 읽고 기존 세션을 사용해라. 비밀번호·토큰을 출력하지 마라.

전사 적용은 계정 명단, 계정별 접근, 읽기/분류/변경/공유, query별 cursor와 끝 페이지, 오류·cap·미확정, dev 수신 검증을 각각 기록해라. 정상 빈 결과는 허용하되 검사하지 않은 범위를 완료로 세지 마라. 기존 운영 저장소/동기화/스케줄러 구현을 확인한 뒤 연결하고, 이 PR의 오프라인 코어만으로 배포됐다고 주장하지 마라. 필요한 별도 PR은 의존성과 수용 기준을 Issue #138에 연결하되, 이미 가능한 작업을 미래 계획으로만 미루지 마라.

GitOps와 검증
- 현재 HEAD의 반례를 재현하고 회귀 시험을 작성한 뒤 수정해라. 의존 작업은 순서대로 하고 독립 검수는 병렬로 할 수 있다.
- Python unittest, Node MIME/ZIP 시험, compileall, Node 구문 검사, git diff --check, ./verify.sh와 저장소 필수 hook을 통과시켜라. hook을 끄거나 실패를 숨기지 마라.
- 논리 단위로 Lore 형식 커밋해라. 권장 단위는 (a) 버전/Golden 계약과 회귀 시험, (b) 장부/최소 보존과 회귀 시험, (c) 복구 어댑터와 합성 검증이다. 실제 diff에 맞게 나누고 근거 없는 커밋은 만들지 마라. 각각 Tested/Not-tested를 정직하게 적어라.
- task 브랜치에 push하고 PR 본문을 최종 동작·결함·검증·남은 범위에 맞게 갱신해라. 자동 merge와 main 직접 push는 금지다. 전사 완료 전 Issue #138을 닫지 마라.
- 수정 후 최신 SHA를 고정해 독립 Claude 검수 프롬프트로 검수받고 새 반례를 처리해라. 결함 수정 뒤 커밋이 생기면 해당 새 SHA에서 필요한 검사를 다시 해라.
- 완료 보고는 코드/표본/전사 상태를 나눠 실제 수치, 커밋, PR/CI, 남은 막힘만 간결하게 적어라. 60초 이상 작업하면 짧게 진척을 알려라. 외부 권한이나 오너 diff 검토가 실제로 막는 단계까지 허가된 작업을 마쳐라.
```
