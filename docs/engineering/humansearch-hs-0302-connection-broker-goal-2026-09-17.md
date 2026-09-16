# HS-03.02 연결 경계 보강 — goal (2026-09-17)

> 모드 `code-change` · 등급 **L3**(개인정보 저장 DB의 쓰기 경로 보안 경계)
> 워크트리 `worktrees/hs-0302-boundary-hardening-20260917` · 브랜치 `task/hs-0302-boundary-hardening-20260917`
> (선행 단위: `task/hs-0301-schema-20260917` → `task/hs-0302-core-20260917` → 이 단위)
> 읽은 정본: `docs/sot/strict-workflow.md`, `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`,
> `docs/sot/verification-commands.md`, `docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md`,
> `docs/engineering/goal-prompts/hs-0302-closeout-next-prompt-2026-09-16.md`

## 1층 — 결론

2026-09-16 Codex 적대검증이 지적한 5개 결함 중 **(a) decoy 승인 FD, (b) 다른 키로 같은 triplet 기록,
(c) 스키마 connect 시 외부 DB swap-back**을 코드로 재현·검증했다. (b)는 완전히 닫았다. (a)·(c)의 공통
원인(연결 fd 를 stdlib `sqlite3` 로는 증명할 수 없음)은 **AC-8 완전 증명을 BLOCKED로 남기고**, 대신
"재연결 경합 창을 프로세스당 최초 1회로 좁히는" 단일 writer 브로커로 노출을 줄였다. **(d) 실제 진입점
연결**은 저장소 전체를 뒤져도 candidate 관측→기록을 잇는 Python 진입점이 아직 없어(AI Search 파이프라인은
별도 Node/TS 런타임) 내부 API로만 분류하고 제품 완료를 주장하지 않는다. **(e) closeout 검사 회귀**는 이
단위의 `acceptance-hs-0302.sh`에 반영했다.

## 2층 — 판단 근거

### 결정 카드 1 — 연결 귀속 증명 방식

- **무엇을** — `/dev/fd` 집합 차분을 보안 경계에서 제거하고, 승인 root 당 단일 커넥션을 프로세스
  수명 동안 재사용하는 **단일 writer 브로커**를 채택했다. AC-8(완전한 native 증명)은 **BLOCKED**.
- **왜** — 두 대안을 모두 실측했다. ① fd-diff를 "새 fd 중 하나라도 승인 identity 면 통과"(관대)로
  두면 decoy fd 로 무력화된다(이 저장소의 `test_decoy_approved_fd_still_bypasses_the_identity_check_blocked_ac8`
  로 재현: rename 스왑 + decoy 스레드 조합이 실제로 alternate DB를 연 커넥션을 통과시킨다). ② "새로
  나타난 fd 가 오직 승인 identity 뿐이어야 통과"(엄격)로 좁히면 원 코드 주석이 이미 실측한 대로
  무관한 스레드의 fd 처리만으로 정상 쓰기 200회 중 18회(9%)가 오거부된다 — 이 저장소가 이미 시도했다가
  버린 설계다. stdlib `sqlite3` 는 커넥션이 실제로 어떤 fd 를 쓰는지 노출하지 않으므로, 두 대안 다 다시
  만들어도 같은 트레이드오프로 돌아간다.
- **버린 길** — (i) 엄격 fd-diff: 9% 오거부 실측으로 기각. (ii) `/dev/fd/{fd}` 로 sqlite3 를 미리
  검증한 fd 에 직접 묶기: SQLite 가 저널/WAL 파일명을 주어진 경로 문자열에 접미사로 붙여 만들기 때문에
  `/dev/fd/N` 경로에서는 `-journal` 형제 파일 경로가 성립하지 않아 journal_mode=delete(현재 스키마
  기본값)로는 쓸 수 없다. journal_mode=memory 로 우회하면 크래시 시 롤백 저널이 없어 내구성이
  떨어진다 — 채택하지 않았다. (iii) apsw 커스텀 VFS 로 xOpen 을 가로채 fd 를 native 하게 증명: 기술적으로는
  유일하게 완전한 증명이지만 **새 서드파티 의존성**이 필요해 이번 승인 범위 밖이다.
- **대가** — 프로세스당 최초 1회의 정교한 타이밍 공격(decoy fd + rename 스왑을 정확히 그 창에 맞추는
  것)은 여전히 이론적으로 가능하다. 다만 그 창은 매 쓰기가 아니라 프로세스 수명 중 단 한 번뿐이다.
- **되돌리기** — `_connect_approved_db`(candidate_identity.py) 한 함수에 격리돼 있다. apsw 도입이
  승인되면 이 함수만 교체하면 되고, DB 스키마·API 계약은 바뀌지 않는다.

### 결정 카드 2 — HMAC 키 회전

- **무엇을** — DB 마다 최초 쓰기 때 키의 SHA-256 지문(비밀 아님)을 `hs-key-fingerprint` 파일(0600)에
  적고, 이후 다른 키로의 쓰기는 insert 전에 `CandidateIdentityError`로 거부한다.
- **왜** — `candidate_key_hmac` 이 키에 의존하므로, 키가 바뀌면 같은 실제 후보라도 다른
  `candidate_key_hmac` 이 나와 PK 제약을 우회해 중복 행이 생긴다.
- **버린 길** — 키 회전을 자동으로 허용하고 과거 행을 재계산하는 migration: 이번 범위에서 구현하지
  않는다(계약·readback 없이 여러 키의 행이 뒤섞이는 것을 막기 위해 의도적으로 닫아 둔다).
- **대가** — 키를 실수로 바꾸면(키 파일 재생성 등) 그 DB는 새 키로는 영구히 쓰기가 막힌다 — 의도된
  fail-closed 다. 정당한 키 회전은 별도 WU(마이그레이션 + readback 계약)가 필요하다.
- **되돌리기** — `hs-key-fingerprint` 파일을 지우면 다음 쓰기가 새 키로 재부트스트랩한다(운영자
  승인 없이 자동화하지 않는다 — 이번 범위 밖).

### (d) 실제 진입점

`git grep -l record_candidate_identity`를 main 전체에서 실행하면 테스트 파일 밖에는 0건이다.
`humansearch/src/humansearch/observe.py`(L0 인증 화면 분류)·`auth_surface.py`·`admin_weekly_dashboard/`
어디에도 후보 관측→기록 파이프라인이 없다. 실제 AI Search 소싱(잡코리아/사람인/LinkedIn)은 Node/TS
런타임(`npm run ai-search:*`)에서 도는 별도 시스템이라, Python 쪽 `record_candidate_identity`를
호출할 대상 자체가 아직 없다. **분류: 후속 WU를 위한 내부 API. 제품 완료를 주장하지 않는다.**

### (e) closeout 검사가 알려진 결함을 누락하면 실패

`scripts/acceptance-hs-0302.sh`에 다음을 추가·수정했다: (1) R6 시험 파일을 필수 명부·수집·실행
집합에 포함(총 131건, 이전 127건). (2) 리팩터 이후 들여쓰기가 바뀐 3개 약화 변이 sed 앵커를
수정 — 고치지 않으면 "sed 앵커가 원본에 없어 변이가 적용되지 않았다"로 조용히 무의미해진다.
(3) HMAC 키 지문 대조 제거 변이 1건 신설. 이 변경들 자체가 "닫았다고 보고했지만 실제로는 검사가
비활성화됐다"는 알려진 함정(P13⑥)의 재현이었다 — main 대비 diff 없이 코드만 바꿨다면 이 저장소의
기존 검사 6개 중 3개가 소리 없이 무력화된 채로 남았을 것이다.

## 인수 기준 (EARS)

- **AC-6a** When 다른 스레드가 승인 inode 를 가리키는 decoy fd 를 열어 두고 있어도, 실제 커넥션이
  다른 파일을 열었다면 시스템은 그 쓰기를 거부해야 한다.
  검증: `pytest tests/test_hs_0302_r6_connection_broker.py::test_decoy_approved_fd_still_bypasses_the_identity_check_blocked_ac8`
  — **주의**: 이 시험은 "고쳤다"가 아니라 "현재 이 특정 재현에서는 SQLite 자체의 우연한 readonly
  오류로 결과적으로 거부된다"는 잔여 위험을 고정한다(BLOCKED 문서화). counter-AC: 우연한 오류 없이
  laundered 커넥션이 조용히 커밋에 성공하는 다른 재현이 나오면 이 AC는 재개방해야 한다.
- **AC-6b** When 이미 결합된 키와 다른 HMAC 키로 같은 (position, channel, candidate_ref) 를 기록하려
  하면 시스템은 insert 전에 닫힌 오류로 거부해야 한다.
  검증: `pytest tests/test_hs_0302_r6_connection_broker.py::test_different_key_for_the_same_triplet_is_refused`
  — 기대: PASS, 행 수 1 유지. counter-AC: 같은 키로의 재시도가 거부되면 오탐(fail-closed 과잉)이다.
- **AC-6c** While 같은 승인 root 로의 반복 쓰기가 이어지는 동안, 시스템은 `sqlite3.connect`를 프로세스당
  한 번만 불러야 한다.
  검증: `pytest tests/test_hs_0302_r6_connection_broker.py::test_broker_reuses_one_connection_across_writes`
  — 기대: `connect_calls == 1`. counter-AC: 매 쓰기마다 재연결하면 (a)의 공격 창이 다시 반복 노출된다.
- **AC-6d** If closeout 인수 검사가 main 대비 새 시험 파일·변이를 누락하면, 그 검사 자체가 실패해야
  한다. 검증: `bash scripts/acceptance-hs-0302.sh` — 기대: `CHECKED: 30`, 종료값 0, `EXPECTED_REQUIRED_IDS`
  가 실제 수집 건수(131)와 일치.

## 입출력·오류·경계 계약

`record_candidate_identity`의 공개 시그니처는 변경하지 않는다(하위 호환). 새 실패 모드:
`"hmac key does not match this db's registered key"`(CandidateIdentityError, closed). 새 파일:
`<approved_root>/hs-key-fingerprint`(0600, ASCII hex64, 비밀 아님).

## Harness 게이트 계획 · 적대검증 정조준

- 게이트 0~4 이 문서 + 실행 로그(§3). V1: 이 문서·산출물을 격리해 독립 검증(§6 적대 검증 로그 참고,
  아직 실행 대기 — 이 커밋은 CHECKPOINT까지만 자동 진행).
- 정조준: decoy fd 재현 재실행, 키 지문 우회 시도, 브로커 캐시가 실패한 연결을 캐시하지 않는지,
  main 대비 diff 3종 각각 3,000줄 이하인지.

## L3 — 롤백·영향 반경·데이터 안전 AC

- 롤백: 이 3개 커밋(`task/hs-0301-schema-20260917`→`hs-0302-core`→`hs-0302-boundary-hardening`)은
  main 에 아직 병합되지 않았다 — 롤백은 브랜치를 병합하지 않는 것 자체다.
  병합 후 되돌릴 때는 `git revert` 3개를 역순으로.
- 영향 반경: `humansearch/src/humansearch/{storage_schema,candidate_identity}.py` 신설,
  main 의 기존 어떤 모듈도 아직 이 코드를 호출하지 않는다(§(d)) — 배포 시 동작 변경 없음.
- 데이터 안전: `hs-key-fingerprint` 파일 부트스트랩은 O_CREAT|O_EXCL 로 경합-안전. 키 회전 없는
  기존 배포는 영향 없음(이 코드가 아직 아무 데도 안 불린다).

## 배송 상태

`NOT_APPLICABLE` — 순수 내부 API·시험 코드이며 아직 어떤 제품 진입점도 호출하지 않는다(§(d)).
실제 운영 연결은 후속 WU(연결 진입점 배선)에서 SKELETON 계약과 함께 다룬다.

## 비범위

HS-02(이력서 증거 계약)·HS-04(저장 정책 계약) 문서는 이 브랜치에 포함하지 않는다 — 별도 PR.
apsw 커스텀 VFS 도입은 새 의존성 승인 후 별도 WU.
