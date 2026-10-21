# PR #139 현재 검수와 재개 기준

## 결론

현재 변경을 문제없다고 승인할 수 없다. 시험은 통과하지만 불충분한 근거로 우수 문서가 될 수 있고 검토 기록도 우회할 수 있다. 이 결함을 먼저 고친 뒤 수신함 레이블 복구와 전사 적용을 검증해야 한다.

## 검수 대상

판정: **REQUEST_CHANGES**. 코드 검수 REQUEST_CHANGES, 설계 검수 BLOCK.
검수 대상: `6139d61a19ebcf7c046be9a3e0e3828dff4406fb`, 기준 커밋 `bb12d8662b534f1ea6978dc2c7b2400910ee3471`.
추적: [Issue #138](https://github.com/sangmokang/Valuehire_v6/issues/138), [PR #139](https://github.com/sangmokang/Valuehire_v6/pull/139).
확인일: 2026-10-21 KST. 이 문서 작성은 결함 수정이나 운영 완료가 아니다.

## 검수 범위와 근거

Codex의 코드 검수와 설계 검수를 독립된 두 읽기 전용 경로로 수행했다. 같은 SHA에서 Python 21개와 Node 11개 시험을 다시 실행해 전부 통과했다. 코드 검수자는 합성 입력으로 버전 우회·Golden 우회·REPLACE를 재현했다. 이 결과는 새 Claude 검수의 대체물이 아니며, 후속 Claude 프롬프트를 별도로 제공한다.

아래 위치는 위 검수 SHA 기준이다. 문서만 추가된 후속 커밋과 코드가 변경된 후속 커밋을 구별하고, 코드가 바뀌면 새 SHA에서 다시 검수한다. 실제 메일·고객/후보자 이름·계정별 메시지 ID·자격증명·원문 인용은 공개하지 않는다.

## 병합 전 해결할 결함

| 우선순위 | 위치 | 재현 및 필요한 수정 |
|---|---|---|
| 높음 | `tools/mail_governance/core.py:78`, `journal.py:77` | 같은 메일의 비골든 검토 후 `rule_version` 끝에 공백을 붙여 골든 검토를 넣으면 새 검토와 Golden 계획이 생긴다. 실행 설정이 허용 버전을 소유해야 한다. 단순 trim만으로 임의 버전 변경 권한을 해결하지 못한다. SOT의 `2026-10-21.v1`과 예시의 `20261021-v1`도 불일치한다. |
| 높음 | `tools/mail_governance/core.py:118` | 회사·직무·개인화 근거 각 한 글자와 HTML `<br>`로 Golden이 된다. SOT의 HTML 존재만으로 통과 금지 조건과 충돌한다. 실제 구성과 내용 검토를 분리해 책임을 정하고 반례를 막아야 한다. 최소 길이만 늘리는 수정은 충분하지 않다. |
| 중간 | `tools/mail_governance/test_core.py:274` | dev 계정 검사 후 같은 fixture를 계속 변경해 marker-only 검사가 가려진다. 각 방어를 독립 입력으로 검증해야 한다. |
| 중간 | `tools/mail_governance/journal.py:79` | 내부 메일의 본문 필드는 제거하지만 layout evidence quote로 전문이 남을 수 있다. 해시·위치·필요한 인용을 보존하면서 저장 정책을 일관되게 적용해야 한다. 현재 시험은 필드 제거만 확인한다. |
| 중간 | `tools/mail_governance/journal.py:43` | UPDATE/DELETE 트리거가 있어도 `INSERT OR REPLACE`로 기존 review를 교체할 수 있다. 로컬 DB 연결에서 재현했으며 원격 공격 경로를 입증한 것은 아니다. 동일 연결 및 재접속의 보장 범위를 명시하고 검증해야 한다. |

→ 버전 권한과 Golden 판정이 병합을 막는 핵심이다. 시험 보강과 기록 보존 수정도 다음 실행에 포함하며, 이 문서 추가를 수정 완료로 보지 않는다.

동일 검수 SHA의 앞선 변이 시험 5개 중 미러 marker·met 근거 필수·PLANNED→VERIFIED 금지·원본 message ID 일치 검사를 각각 제거한 4개가 시험을 통과했다. 레이블 부분집합 검사 제거는 시험이 잡았다. 과거 Claude 보고서의 21개 중 9개 생존 수치를 최신 전수 결과로 사용하지 않는다.

후속 회귀 시험은 충분한 다른 조건을 모두 만족한 상태에서 방어 하나만 위반해야 한다. 상태 전이 검사는 올바른 receiver/label/archive 관측을 넣고도 PLANNED→VERIFIED가 거절되는지 확인한다. 원본 message ID 검사는 계정·해시·레이블 등이 일치하고 ID만 다른 경우를 만든다.

## 운영 장부와 인증의 현재 관측

2026-10-21 22:10 KST에 운영 SQLite를 읽기 전용 집계했다. 이번 검수에서 메일 발송·레이블 변경·장부 변경은 하지 않았다.

| 항목 | 현재 증거와 한계 |
|---|---|
| 원본 레이블 | source_labels 7건 VERIFIED |
| 원공유 / 보완공유 | share 7건 / share_repair 2건 모두 SENT_UNVERIFIED |
| dev 레이블 | receiver_labels 7건 SENDING. 두 실행 모두 사전 원본 식별자 검사에서 중단했으며 provider 변경 시도와 추가 발송은 각각 0건. 확인된 적용·검증은 0건 |
| 원문 보존 | 앞선 독립 수신 재조회에서 7개 고유 원문의 ZIP 내부 바이트 일치를 확인. 최초 첨부 실패 2건의 관측과 보완 전송을 유지 |
| Golden / Ontology | 새 Golden 0건. Ontology 사건 2건은 미확정. 기존 Golden 레이블 삭제는 실행하지 않음 |
| 전사 수집 | coverage 페이지 0건. 운영 어댑터·전체 backfill·스케줄러 미배포 |
| 권한 | 10:57 KST 증거에서 대표와 dev의 gmail.modify 토큰·프로필·레이블 조회가 각각 200. 실제 dev 메시지 변경 성공이나 전체 계정 쓰기 성공의 증거는 아님 |
| 명단 | 11:01 KST 관리자 UI에서 전체 조직 1/1페이지의 활성 9계정 관측. 계정별 Gmail 처리 가능성과 전체 메일 소진은 별도 검증 필요 |

→ 권한 설정은 진전됐지만 dev의 같은 레이블과 전사 처리는 아직 입증되지 않았다. 이미 수신된 원문을 재발송하지 않고 기존 작업부터 조정해야 한다.

02:47 스냅샷의 share 6건 SENDING과 현재 receiver_labels 7건 SENDING은 다른 작업이다. 권한 거절을 현재 중단 원인으로 반복하지 않는다. 현재 중단점은 dev 레이블 적용 전 원본 식별자 대조 실패다. plain text와 HTML 표현 차이가 원인일 가능성이 있지만 확정하지 않았다. ZIP 내부 실제 RFC Message-ID와 저장 원문의 SHA-256을 엄격하게 대조해 조사해야 한다.

실제 private 근거는 저장소 루트의 Git 제외 경로 `artifacts/mail-governance-20261021/`에 있다. 인증은 `auth-after-modify.private.json`, 명단은 `admin-roster.private.json`, 중단은 `receiver-label-apply*.private.json`, 장부는 `pilot.sqlite`, 반례는 `claude-findings-repro-6139.private.json`이다. 이 파일들은 공개 Git에 복사하지 않는다. PRIVATE 파일 없이도 합성 반례와 코드 검수는 가능하다.

## 결함으로 단정하지 않을 계약

- RFC-ID 없는 계정별 identity는 보수적 중복 방지의 한계다. 본문 유사도만으로 서로 다른 메일을 합치지 않는다.
- 검증된 정상 검색의 결과 0건은 유효하다. 명단·인증·query·끝 페이지 관측 없이 전사 완료라고 말하는 것이 문제다.
- 고객사가 후보자 철회를 직접 알린 사건은 현 계약상 허용된다. 출처와 사건 당사자를 구별한다.
- Golden 사람 승인 의무는 기존 요구가 아닌 새 제안이다. 자동 승인 절차를 추가하지 않는다.

## 다음 실행과 종료 조건

버전 권한·Golden 반례·독립 회귀 시험·보존 계약을 먼저 수정한다. 이후 기존 SENDING 작업의 실제 효과 유무를 근거로 append-only 조정하고, 이미 수신된 원문에 dev 레이블을 추가해 독립 GET으로 검증한다. 원문 식별 조건을 약화하거나 무조건 재발송하지 않는다. FAILED 작업의 재개는 명시적 보완/후속 작업 계약으로 설계하며 버전 변경으로 우회하지 않는다.

수정 전후 반례, 방어 제거 변이, 정상 시험, 구문 검사, 저장소 필수 게이트와 새 SHA의 CI 결과가 갖춰져야 수정 검증을 보고한다. 로컬 계약 통과·표본 복구·전사 완료를 각각 보고한다. PR을 자동 병합하지 않으며, 원래 전사 작업을 마치기 전 Issue #138을 닫지 않는다.
