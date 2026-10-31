# AI Search 관리자 후속 계약 — 2026-10-31

기존 Issue #142 / Draft PR #140 / task/admin-ai-search, 시작 HEAD f509ca98dd1248c988acc10b1dbb02f279acf8c8.
산출물 mixed, L3. 현재 사용자 지시는 로컬 증분 수집·정규화·격리 DB 적재와 기존 GitHub 본문 갱신의 승인이다.
메일/제안/댓글 발송, Gmail·채용사이트 수정, 운영 DB 적용, merge/deploy는 금지한다.

## 현재 증거와 원인

- collection.py:115 이후 이미 exhausted인 checkpoint는 재조회하지 않는다. 새 run은 기본 전수 조회다.
- tools/admin-ai-search/normalize.py:36 이후 checksum/parser/label 캐시를 재사용한다.
- weekly.css:1은 main min-width만 제한한다. 모바일 공통 shell 폭의 실제 원인은 CDP 측정 후 확정한다.
- host-admin overlay 파일은 동일하다. migration은 표시번호 CHECK 한 줄이 호스트에 누락됐다.
- SQLite 재조회: raw 100,085 / PROCESSED 437 / EXCLUDED 79,400 / REVIEW_REQUIRED 20,248,
  Batch 895 / Gmail contact_events 29. 최종 수집 성공 2026-10-30 00:42:12 KST.

## 단일 AC와 순차 단위

기존 관리자가 새 Gmail 결과를 안전하게 증분 반영하고, 근거 수준을 보존한 채 390px에서도 표 내부만
가로 스크롤되며, 기존 PR/Issue가 이번 직접 검증과 미확인을 정확히 설명하면 이번 후속 작업을 충족한다.
counter-AC: 전수 본문 재수집, 번호 변경, 이름 기반 연결, 미확인을 0/미발송으로 표현, 사용자 변경 덮어쓰기.

| 순서 | 계약 / 입력 → 출력 | 검증 |
|---|---|---|
| 1 | collect_mailbox(..., incremental=True): 성공 baseline + 현재 Gmail → 새 run/checkpoint, 원문 upsert | focused collection test + 실제 수집 readback |
| 2 | 기존 정규화/컨택 파서: 새 원문 → 개별 근거 또는 REVIEW_REQUIRED | 실제 원문 audit / 기존 focused tests |
| 3 | 기존 관리자의 viewport/필터 → 목록·이력·Raw, 페이지 폭 <=390 | 기존 CDP 로그인 세션에서 직접 검증 |
| 4 | 관련 소스 → test/lint/typecheck/필수 게이트 결과 | 재실행 가능한 로그, V1/V2 |
| 5 | 검증 결과 → 기존 PR/Issue 본문 | GitHub readback |

## 입력 영역·예외 표와 결정

| 입력(암묵 상태 포함) | 처리 | 대응 검증 |
|---|---|---|
| 성공 baseline와 새 메일 | 자동: baseline 시작시각부터 Inbox/Sent delta; 모든 도구 포함 | incremental test / 실제 수집 |
| AI 라벨에 뒤늦게 들어온 오래된 메일 | 자동: 전체 라벨 ID 확인, 기존 본문 캐시 재사용 | incremental test |
| 성공 baseline 없음 / Sent baseline 없음 | 명시적 거부, 임의 전수 전환 금지 | missing-baseline test |
| 경계 시각 / 중복·재시도·중단 | 자동: 이전 시작시각 overlap, ID dedup, pending-page/checkpoint 재개 | incremental / existing resume tests |
| API 장애 / 토큰 cycle / 잘못된 ID 응답 | 기존 retry 후 명시적 실패, 성공 watermark 진전 금지 | existing collection tests |
| 원문에 후보 URL·포지션·발송 reference 완비 | 기존 파서로만 연결, 채널 독립 | existing contact-report tests / source audit |
| 이름·수신자·총계만 있음 / 점수 축 없음 | REVIEW_REQUIRED / NOT_RUN 유지 | existing contact-report tests / real audit |
| CDP 인증 유지 / 만료·2FA | 기존 세션 재사용 / 로그인 필요 명시; 기존 탭 보존 | CDP DOM/URL readback |
| 390px / desktop | 이 페이지에만 shell 폭 제약, 표 내부 scroll | 실제 viewport 측정 |
| host 파일 동일 / 사용자 차이 | 비교 후 같은 변경만 동기화 / 차이는 보존 | hashes / diff |
| 그 외 전부 | 명시적 중단, 계약 갱신 후 재개 | V1/V2 표 공격 |

동일성·번호·점수·컨택 정책은 사용자 지시와 기존 SOT 그대로다. 증분 경계는 마지막 성공시각보다 앞선
baseline 시작시각으로 겹쳐 조회해 수집 중 도착 누락을 막는다. 기존 본문은 재다운로드하지 않는다.
새로운 framework·추상화·대규모 리팩터링은 비범위다. 각 단위를 검증한 뒤 다음으로 진행한다.

## SOT와 게이트

읽음: docs/sot/admin-ai-search-evidence.md, native-spec/validation-2026-10-30.md,
host-admin AGENTS.md, docs/README.md, product shared build plan, design guide, TDD harness, SOT-19/30/31.
SOT-31 관련: 숫자 상한을 총계로 표현 금지(2026-07-20), 부분 검증을 전체로 보고 금지(2026-07-21),
브라우저 세션 파괴 금지(2026-07-19). 사용자 지시상 새 Issue/PR 생성과 merge는 하지 않는다.
host strict:gate 실행. red-ledger는 다른 작업트리 65개를 검사하기 시작해 기존 작업 재개 범위를 넘으므로 중단했다.
검증: focused pytest, ruff/mypy, host Vitest/tsc, bash verify.sh, git hooks 필수 게이트.
strict:exit-gate script는 host package에 없으므로 존재 검사와 실제 지원 여부를 보고한다.
외부 효과 방지: Gmail bridge의 dispatch 허용목록과 고정 GET readApi, 관리자 GET API만 사용한다.
전수 본문 재수집/운영 DB 변경을 mutation·명시적 loopback DSN 대조로 반증한다.
