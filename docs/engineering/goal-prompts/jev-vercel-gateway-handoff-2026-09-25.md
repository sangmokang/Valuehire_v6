/strict

[VALUEHIRE-V6-JEV-VERCEL-GATEWAY — 인계 + 적대 검증 + 실행 + 다음 프롬프트] L3

이 프롬프트는 새 세션(/clear 직후)에서 실행한다. 아래 "확정 사실"은 2026-09-25 기준 이전 세션의 주장이다.
사실로 믿지 말고 0단계에서 전부 다시 확인한다. 어긋나면 그 항목을 보고하고, 판단이 필요하면 멈춘다.

## 확정 사실 (0단계에서 재확인할 것)

작업 줄기
- #109 https://github.com/sangmokang/Valuehire_v6/pull/109 — base main, 브랜치 task/jev-shadow-base-split,
  워크트리 worktrees/jev-shadow-base-split, head 0d92a8a. recruiting_review.py(eaaee62에서 이 파일과 전용 시험만 이식)
  + 조직 shadow 4커밋 + G2 변이 검사기 사본에 contracts/ 복사 + shadow CLI 시험 cwd + except 괄호.
- #110 https://github.com/sangmokang/Valuehire_v6/pull/110 — base task/jev-shadow-base-split, 브랜치
  task/jev-evidence-assessment-wu1-split, 워크트리 worktrees/jev-ea-wu1-split, head dbc7fd0(이 파일 커밋 전).
  근거 평가 WU1 + 후속(d3e05ad·be46261 이식본) + 변이 스크립트 PASS 줄 + except 괄호 + NOT_RUN 기록.
- 원래 작업트리 worktrees/jev-evidence-assessment-wu1 에는 다른 세션이 커밋한 이력이 있다. 수정하지 않는다.
- 로컬 검증(850cfb2 코드): hs-gates 437 passed, hs-gates-mutations 6/6, 변이 86 생존 0, verify.sh rc 0,
  원칙 34/34, 조용한 실패 검사 PASS, ruff·mypy 0. 이후 커밋은 문서만.
- 원격 CI: 두 PR 모두 15단계 통과 후 "억제 만료 스캔"에서 실패, 뒤 15단계 미실행.
  원인 suppressions.yaml 의 ci-transfer-guarantee·p13-deletion-blindspot (expiry 2026-09-15). Jev와 무관.
  해소 체인 #74(리뷰 대기·단독으로는 초록 불가) → #75(충돌) → #77(clean). main 보호: verify 필수 + 본인 외 승인 1건.
  gate-scope-gaps 는 2026-09-30 만료 예정.
- 미결 이슈(낮음): 근거 평가 not_run 결과에 error_reason 이 None (shadow 는 이유 기록). 수정하지 않았다.
- docs/sot/candidate-search.md 의 학교·회사 등급 문단은 그 문서가 main에 없어 #110에서 뺐다.

Jev 연결
- Jev = TypeSafe AI 의 System One 모델. 저장소는 Python 공식 SDK typesafe-sdk==0.7.1 을
  humansearch/src/humansearch/organization_shadow_jev.py 의 TypeSafeJevJudge 로 이미 연결했다.
  TypeSafeClient(api_key=, base_url=) 를 지원한다(실측 시그니처).
- 공급자 직접 가입·키 발급은 막혀 있다(2026-09-24 사장님 확인). 라이브 Jev 는 NOT_RUN 으로 기록돼 있다.
- 공식 대체 경로: Vercel AI Gateway 의 TypeSafe 호환 API. https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe
  base_url https://ai-gateway.vercel.sh/typesafe, 인증 AI_GATEWAY_API_KEY(또는 Vercel OIDC), 모델 이름 예시 "typesafe-ai/jev",
  모델 목록 GET /typesafe/v1/models. 요금은 Vercel 청구.
- 충돌: 계약 두 개(contracts/jev-evidence-assessment.json, contracts/jev-org-reference-shadow.json)가 model_version
  "jev-1.13.0" 고정이고 evidence_assessment.py 가 고정 버전이 아니면 거부한다(_is_pinned_jev_model).
- 저장소에는 package.json·vercel.json·.vercel 이 없다. Vercel CLI 는 설치돼 있다. EvidenceAssessmentV1 이라는 이름은 없다.
- 거부한 초안: TypeScript/npm/AI SDK 로 새 evaluateEvidence 모듈을 만드는 프롬프트 — 기존 Python 연결을 중복한다.

진행 원칙(사장님 합의)
- 검증 계층을 늘리지 않는다. 새 문서·gate·추상화·에이전트 반복 금지. 기본 한 바퀴: 실패 시험 → 최소 구현 → 관련 검사 → 적대 검토 1회.
- 병합·배포·메일·새 Vercel 프로젝트 생성·vercel link·env pull·push 는 각각 사장님 승인 전 금지.
- 비밀값은 출력·커밋 금지. 합성 입력만, 개인정보 전송 금지.

## 0단계 — 재확인과 적대 검증 (수정 없음)

a. 두 워크트리의 HEAD·status, 이 작업트리를 cwd 로 쓰는 다른 codex/claude 세션(lsof -a -d cwd -Fpcn + awk 경로 대조).
   다른 세션이 있으면 멈춘다.
b. 위 확정 사실을 하나씩 명령으로 확인하고 표로 남긴다(일치/불일치/확인 불가).
c. 이전 세션의 Codex 적대 검토 결과가 있으면 읽는다:
   /private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/f11ab6c3-04d1-4fb7-8d6c-6295178f905b/tasks/bjfunadwq.output
   없거나 비었으면 NOT_RUN 으로 적는다.
d. 흐름 전체를 공격한다: 이식 범위가 정말 최소인가, 빠진 의존이 있는가, 가짜 초록(시험이 대상을 안 봄)이 있는가,
   NOT_RUN 이 어딘가에서 PASS 로 접히는가, Gateway 경로가 계약·개인정보·과금 경계를 깨는가.
   재현 명령이 있는 것만 결함으로 센다. 결함은 심각도·file:line·재현·사업 영향으로.
e. "코딩 진척표": 완료 / 로컬만 / 원격 CI 미완 / 미착수 로 나눠 한 표로.

## 1단계 — Gateway 연결 준비 (키 없이 가능한 범위)

- Vercel 로그인·팀·AI Gateway 키 존재 여부만 확인(값 출력 금지). 키가 없으면 필요한 절차만 보고하고 2단계로 가지 않는다.
- 키가 있으면 GET /typesafe/v1/models 로 모델 이름만 확인. 고정 버전 이름이 없으면 멈추고 결정 카드로 묻는다
  (계약의 고정 버전 규칙 완화 여부). 스스로 완화하지 않는다.

## 2단계 — 최소 구현 (#110 브랜치 위 새 커밋, 승인된 경우만)

- organization_shadow_jev.py: AI_GATEWAY_API_KEY 가 있으면 TypeSafeClient(api_key=그 키, base_url="https://ai-gateway.vercel.sh/typesafe"),
  없으면 기존 동작 그대로. 두 CLI 의 키 확인을 두 키 중 하나로 넓힌다. live_calls_allowed 는 false 유지.
- 실패 시험 먼저: 키 없음 → LOCAL_ONLY 유지, 게이트웨이 키 → base_url 설정. 기존 시험 약화 금지.
- 관련 pytest·ruff·mypy·변이 스크립트만 다시 돌린다.
- TypeScript·npm·AI SDK·새 모듈·새 추상화 금지.

## 3단계 — 라이브 1건 (사장님이 이 세션에서 명시 승인한 경우만)

goal 문서(docs/engineering/jev-evidence-assessment-wu1-goal-2026-09-23.md) 결론 절의 5단계 절차 그대로.
합성 입력 1건씩, 끝나면 live_calls_allowed=false 복구, NOT_RUN 기록을 실측 결과로 갱신.

## 보고와 다음 프롬프트

§8 3층 보고, 결정 최대 2개. 반드시 A VERIFIED / B DEFERRED(외부) / C FAILED 로 나눈다.
마지막에 "다음 세션용 프롬프트"를 이 파일과 같은 폴더에 새 파일로 쓰고 로컬 커밋한다(push 는 승인 후).
다음 프롬프트는 이 파일과 같은 구조(확정 사실 → 0단계 재확인 → 실행 단계 → 보고)로, 이번에 바뀐 사실만 갱신한다.
