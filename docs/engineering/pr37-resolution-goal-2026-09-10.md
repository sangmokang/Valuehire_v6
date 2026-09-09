# PR #37 최신 기준 복구

## 결론

기존 정책 작업을 보존하면서 최신 변경과 통합하고, 정책 입력과 검사 결과의 허점을 보완했습니다. 독립 재검토와 전체 로컬 검사를 마쳤으며 원격 반영과 병합은 하지 않았습니다.

## 판단 근거

원격 PR은 0b4dd2c에서 충돌 상태이고 main은 01495b3입니다. 정책 검사는 통과하지만 목표 문서가 약속한 공개 출력이 없고 실수 5.0을 정수 5처럼 받아들입니다. 기존 구현·시험을 재사용하고 새 계약 위반만 보완합니다.

> **무엇을** — 기존 PR 이력은 원본과 복구 참조로 보존하고 별도 브랜치에 최신 main 기준 변경을 회수합니다.
> **왜** — 다른 Claude 세션과 기존 PR 작업 공간의 변경을 보존해야 합니다.
> **버린 길** — 원본 브랜치 강제 갱신과 전체 재작성은 기존 증거와 최신 기능을 손상할 수 있습니다.
> **대가** — 충돌별 의미 확인과 최신 전체 검사 재실행이 필요합니다.
> **되돌리기** — 새 브랜치는 원본 PR과 main에 영향을 주지 않습니다. 수정은 개별 커밋으로 역적용하고 병합 뒤 복구는 PR 전체 경계로 수행합니다.

## 범위·정본·시작 장부

- L3: 정책 정본, 검사기, 공통 CI 연결 변경. SKELETON과 운영 배송은 NOT_APPLICABLE: 내부 정책 검사이며 운영 화면·DB·후보자 데이터를 변경하지 않습니다.
- 사용자 요청: .omx/artifacts/pr37-resolution-prompt-2026-09-10.md 실행.
- 작업 공간: worktrees/pr37-resolution-codex-20260910. 원본 work-unit-rebased는 읽기만 합니다.
- 시작 main: 01495b3eae76d3e43e4a6cc8a481ee78258502c6. PR: 0b4dd2c57411a4f3eabc967fb27af071d54f2dfe.
- 세션: 01a0879f-b739-7bf0-b947-5ac4a184d87b. 2026-09-09T19:31:21Z부터 회수.
- 읽은 정본: docs/sot/coding-principles.md → docs/sot/principles.yaml. bash scripts/acceptance-principles-check.sh 실행 결과 PASS, CHECKED 34, 배선 pre-push=1 ci=1. 전체 출력은 증거 장부에 보존합니다. 검증 중 main이 4379b2f로 갱신되어 재통합하고 두 정본을 다시 직접 읽은 뒤 같은 검사를 재실행했습니다.
- 적용 규칙: 사용자 제공 AGENTS.md, 현재 strict, git-workflow.md, verification-commands.md, mechanism-registry.yaml, hook-contracts.md. 루트 AGENTS.md·CLAUDE.md는 디스크에 없습니다.
- 회수: 기존 methodology goal·V1·재검토 문서, 기존 RED dc2dad9 / GREEN 28155fc, git log --all, 이전 프롬프트의 진단. V1 비용 제한 기록은 역사 증거이며 새 판정으로 승격하지 않습니다.
- 파일 hard 600줄, 함수 hard 100줄, PR diff 3000줄 이하. 생성 정책 문서는 파생 산출물이며 파일 한도 예외가 필요하지 않습니다.

## T: 입력·출력·오류·경계 계약

T는 작성자와 독립 검증자가 공유하는 채점 기준입니다. 정책값 정본은 work-unit-policy.yaml, 문서는 결정적 생성 결과입니다. EXPECTED_*는 승인된 v1 의미가 몰래 바뀌지 않도록 고정하는 검증 계약이며 렌더러의 정책 입력은 YAML뿐입니다. 승인된 정책 변경에는 독립 시험 기대값 변경이 먼저 필요합니다.

- 입력: UTF-8 YAML 단일 문서, 정확한 필수 키, 정수 version/claims/max units/hours, 문자열·불리언·순서 있는 목록. 객체 키 순서는 의미가 없으며 목록 순서는 의미가 있습니다. 5.0과 문자열 5는 정수 계약 위반입니다. 형식은 파싱된 자료형 기준이며 YAML의 yes/off/0x5처럼 같은 불리언·정수로 읽히는 표기를 금지하는 어휘 규칙은 아닙니다.
- YAML 중복 키·알 수 없는 키·빈 문서·여러 문서·별칭·잘못된 자료형을 실패시킵니다. 병합 키(<<)는 원문 키·값을 가리는 추가 지시이므로 허용하지 않습니다.
- 정책·생성 문서·검사 모듈은 일반 비어 있지 않은 파일이어야 합니다. 심볼릭 링크·누락·빈 파일·읽기 실패는 성공하지 않습니다.
- checker 성공: exit 0, VERDICT PASS, POLICY_CHECKED 22, DOCUMENT_SYNC PASS. 6개 객체 구조와 16개 정책값 단언을 실제 실행해 센다. 종전 19는 실행 계수가 아닌 상수였다. 실패: exit 1, VERDICT FAIL, 원인과 실제 처리 수. 잘못된 CLI 인수 또는 런타임 부재는 NOT_RUN/exit 2.
- acceptance 성공: exit 0, VERDICT PASS, CHECKED 양수. 내부 checker 세부 출력과 외부 acceptance 공개 출력을 문서에서 구분합니다.
- renderer는 검증된 입력만 표준 출력에 내보내며 파일을 직접 쓰지 않습니다. 잘못된 입력이면 표준 출력은 비고 오류 출력만 남습니다. 호출자가 셸 리다이렉션으로 대상 파일을 먼저 비우는 동작까지 보호하지 않으므로 파일 교체는 성공한 임시 출력 확인 후 수행해야 합니다. 같은 입력을 두 번 생성해도 바이트가 같아야 합니다.
- 처리 개수는 실행한 단언으로부터 계산합니다. 고정 성공 출력·빈 구현·상수 계수·기록된 정상 입력만 외운 가짜 checker를 실제 반례로 공격합니다. 임의의 악성 프로그램을 전부 증명하거나 모든 검사기·시험을 함께 수정할 수 있는 같은 사용자 권한의 변조까지 방지한다고 주장하지 않습니다. 정상 키 순열은 실행마다 시드를 기록하고 WORK_UNIT_PROPERTY_SEED로 재현합니다.
- 범위: 정책 정본과 소비 경로의 일치. 실제 작업 단위 장부/PR 개수/시간/승인 기록 자동 강제 시스템은 이 PR에 없습니다. 정책 검사 통과를 그 시스템 구현으로 보고하지 않습니다.
- 고위험 목록은 정책 설명이며 자동 경로 분류에 사용하는 소비자는 현재 없습니다. 실제 매처가 없는 한국어 항목을 실행 가능한 경로 규칙이라고 설명하지 않습니다.

## AC: 합격 조건과 가짜 합격 반례

각 명령은 이 작업 공간에서 실행하며 구체적 출력 수는 시험 추가 후 실행 결과로 기록합니다.

1. When 승인된 정책을 읽으면 checker와 renderer는 같은 정책 의미·문서 바이트를 산출해야 합니다.
   명령: ruby scripts/verify/check-work-unit-policy.rb; bash scripts/acceptance-work-unit-policy.sh.
   기대: 위 공개 출력 계약 및 exit 0. 반례: 목표 문서에 내부 출력이 공개 출력처럼 적혀 있음.
2. If 정책 자료형·값·구조·문서가 위반되면 검사기는 exit 1과 해당 원인으로 실패해야 합니다.
   명령: ruby scripts/verify/work-unit-policy-contract-test.rb; bash scripts/acceptance-work-unit-policy-mutations.sh.
   기대: 정상 대조군과 고장 사본 전부 기대 결과, CHECKED 양수, VERDICT PASS. 반례: 실수/여러 문서/위조 성공 checker/문서 동시 변조.
3. When 객체 키 순서·주석·공백만 달라지면 정책 의미와 생성 문서는 같아야 합니다.
   명령: 동일 mutation 검사 및 renderer 두 번 실행 비교.
   반례: 의미 없는 키 순서 변경을 정책 위반으로 차단.
4. If 로컬/CI 정책 관문이 삭제·비활성화·echo·무동작으로 바뀌면 통합 검사는 실패해야 합니다.
   명령: acceptance-ci-step-integrity.sh, acceptance-semantic-mutations.sh, acceptance-verify-ac-m.sh와 정책 회귀시험.
   반례: 스텝 이름만 존재, PASS 출력만 위조, 검사 대상 0개.
5. When 최신 main과 합치면 기존 기능·검사와 Work Unit 정책 검사를 모두 보존해야 합니다.
   명령: bash hooks/pre-push (깨끗한 커밋에서), bash scripts/check-docs-sot.sh, git diff --check, 셸/Ruby 문법, CI 표 대조.
   기대: 필수 검사 전체 성공. 기존 main 자체 결함은 별도 재현하고 이 작업으로 인한 회귀와 구분합니다.

## Work Unit과 검증 순서

- WU-R1: 최신 main 통합, 충돌 설명, 기존 정책 검사 유지.
- WU-R2: 입력/오류 계약을 시험으로 먼저 고정하고 checker 최소 보완.
- WU-R3: 검사 무력화와 실제 연결 검증, 문서 기대 출력·범위 정합성 보완.
- 기존 RED는 보존하고 새 시험은 구현과 분리된 RED 커밋으로 기록합니다.
- Harness 0/1: 이 계약과 회수. 2: 격리와 RED. 3: GREEN. 3.5: pre-push/CI → acceptance → checker → YAML/renderer 경로 실행. 4: 전체 로컬 검사. 5/6: 원격 전달 준비만 하며 실행하지 않습니다.
- R2: 고장 사본, 정상 대조군, 600/601 경계. R3: 근거·반례·한계. R4: 실제 실행 경로. R5: 실패를 장부에 남기고 같은 실패 두 번이면 다른 접근.

## 적대 검증 로그

74e1830은 첫 독립 검토 대상으로 고정합니다. 검토 중 발견된 반례 수정은 별도 worktrees/pr37-resolution-fixes-20260910에서 수행하고, 원본 검토 종료 뒤 검증된 후속 커밋을 회수합니다. 병합 키 우회, 실패 건수 위조의 시험 누락, 양성 검사 강화를 오차단하는 메타 시험을 재현 중이며 전체 PASS가 아닙니다.

G=Codex, V1=Claude CLI, V2=새 Codex 맥락. 실제 Claude API 키는 제거하고 기존 로그인 경로만 사용합니다. auth status는 현재 claude.ai/max 로그인입니다. 추가 과금 경로는 사용하지 않습니다. 실제 실행 실패 시 NOT_RUN/BLOCKED를 유지합니다.

검증자는 구현자의 결론 대신 T와 산출물·원문 증거를 받고 독립 명령을 실행합니다. 판정과 재현을 연결해 기록하고 모든 필수 검증이 끝나기 전 전체 PASS를 선언하지 않습니다.

## 검증 장부와 종료

현재: CHECKPOINT. 최신 main4379b2f를 포함한 594b595에서 전체 로컬29 검사 PASS, 계약86·메타22와 Claude 후속2회·Codex V2 PASS입니다. 원격은 미반영·미검증입니다. 상세 명령·전체 출력·시각·커밋·세션은 [증거 장부](pr37-resolution-evidence-2026-09-10.md)에 연결합니다. 최초 V1 FAIL 원문은 [첫 판정서](pr37-resolution-v1-verdict-2026-09-10.md)에 보존하며 수정 후 판정과 구분합니다.
로컬 검증된 CHECKPOINT까지 진행하고 PR 수정안·충돌 정리·복구 절차를 제공합니다. 원격 PR 상태와 로컬 결과는 분리합니다.
