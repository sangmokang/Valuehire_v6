strict

[VALUEHIRE-V6-JEV-EVIDENCE-ASSESSMENT-WU1 v5] 위험등급 L3 (외부 AI 모델·개인정보)

목표 한 줄
v4 구현(브랜치 task/jev-evidence-assessment-wu1)이 V1·V2·Codex 에서 받은 FAIL 결함을 닫고,
2026-09-23 사장님 결정 두 가지(개인정보 전면 허용, 학교가 없으면 경력으로 검증)를 반영해
로컬 커밋 1개로 마감한다. 새 기능을 처음부터 다시 만들지 않는다 — v4 코드를 고친다.

────────────────────────────────
사장님 결정 (2026-09-23, 재논의 금지)
────────────────────────────────
D-1 개인정보: 밸류커넥트 검증 컨설턴트가 다루는 자료이므로 후보 원문·학력·경력을 Jev 로 보내는 것을 허용한다.
    "비식별 NOT_PROVEN" 은 더 이상 라이브 차단 사유가 아니다.
    단, 결과 파일의 delivery_status 는 실제 외부 전송 여부대로 정직하게 쓴다(아래 계약).
D-2 학교가 없거나 등급표에 없는 학교(UNLISTED)면 "모름"으로 끝내지 않고 경력으로 검증한다.
    경력 검증 = ① 재직 회사 수준(회사 등급표, 코드가 판정) + ② 그 회사에서 한 업무의 JD 부합도(Jev 5상태).
D-3 국적 감점은 하지 않는다(기존 결정 유지). nationality 키 거부 유지.
D-4 학교·회사 등급표 내용은 사장님이 채운다. 확정 전(status ≠ APPROVED) 표로는 점수를 내지 않는다(아래 계약).

────────────────────────────────
0단계 — 착수 자격 (하나라도 불일치면 코드 0줄, 불일치표만 보고)
────────────────────────────────
a. git -C worktrees/jev-evidence-assessment-wu1 log --oneline 6d7afa0..HEAD →
   b3a1f39 004e562 59d289a cd7546e (4개). 다르면 멈춤.
b. 같은 작업트리 git status --short → docs/engineering/jev-evidence-assessment-wu1-goal-2026-09-23.md 수정,
   docs/engineering/goal-prompts/jev-evidence-assessment-wu1-v5-2026-09-23.md 신규 외에는 없어야 함.
c. git ls-remote --heads origin task/jev-evidence-assessment-wu1 task/jev-org-reference-shadow → 빈 출력.
   기반 9커밋(6d7afa0 이하)은 미푸시·CI 미통과임을 보고서 1층에 적는다.
d. 동시 세션: lsof -a -d cwd -Fpcn 을 awk 로 (pid, 경로) 쌍으로 뽑아, 자기 pid·부모를 제외하고
   worktrees/jev-evidence-assessment-wu1 을 cwd 로 쓰는 codex/claude 프로세스 0개. 양성 대조군(루트 cwd 행이 경로와 함께
   출력되는지)도 함께 보인다.
e. bash scripts/acceptance-principles-check.sh → 첫 줄 "VERDICT: PASS", rc 0.
f. 루트 작업트리(Valuehire_v6)는 읽기만. 수정·stash·checkout 금지. 시작 시 git status --porcelain | shasum 을 기록하고
   끝에 같은지 확인.
g. ~/valuehire-private 의 Gmail 수집(gmail_sot_harvest.py)은 다른 세션 작업이다. 읽기도 건드리지도 않는다.

작업 위치: 기존 작업트리 worktrees/jev-evidence-assessment-wu1 (새 작업트리 만들지 않음).

────────────────────────────────
1단계 — 먼저 읽을 것 (읽은 file:line 을 goal 에 기록)
────────────────────────────────
- docs/engineering/jev-evidence-assessment-wu1-goal-2026-09-23.md 전체(검증 장부·적대 검증 로그 포함)
- .omx/artifacts/jev-ea-v1-20260923-154842.md (V1 FAIL 원문, 결함 D1~D9·생존 변이 13종)
- .omx/artifacts/jev-ea-v2-20260923.md (V2 FAIL 원문, C1~C9 전부 재현), .omx/artifacts/jev-ea-mutate-v4.py (v4 변이 18종 스크립트)
- humansearch/src/humansearch/evidence_assessment.py, evidence_assessment_cli.py, school_tier.py,
  humansearch/tests/test_evidence_assessment.py, contracts/jev-evidence-assessment.json, contracts/school-tier.json
- humansearch/src/humansearch/organization_shadow_jev.py (TypeSafeJevJudge — 응답 파싱 예외가 여기서 난다)
- docs/sot/candidate-search.md:44-56, docs/sot/coding-principles.md P11·P13·P15

────────────────────────────────
2단계 — 닫을 결함 (전부 재현 완료, 각 항목마다 먼저 실패하는 시험 → 수정)
────────────────────────────────
| ID | 출처 | 결함 | 닫는 방법 |
|---|---|---|---|
| F1 | Codex high·V2 C9 | 외부 client 를 만들어도 delivery_status 가 항상 LOCAL_ONLY | client 를 만들었거나 호출했으면 EXTERNAL_JEV, 아니면 LOCAL_ONLY. 고정 문자열 금지 |
| F2 | Codex high | --config 로 임의 파일을 주면 정책을 우회 | 라이브 허용 여부는 저장소 계약 파일(contracts/jev-evidence-assessment.json)의 값만 믿는다. 다른 경로의 config 로 live_calls_allowed 를 켜면 거부(종료값 2). 시험용 대체 config 는 코드 주입(함수 인자)으로만 |
| F3 | Codex high·V2 C8 | status=SYNTHETIC 학교표로 completed·만점·사람검토 없음 | 등급표 status ≠ APPROVED 면 school/career 판정은 verdict 는 계산하되 projection·coverage = null, requires_human_review=true, school_tier.table_status 출력 |
| F4 | V1 D8·Codex | 학교 판정에 무관한 evidence_ids 가 붙음 | 학교·회사 등급 판정의 provenance 는 education_index / career_index 로 기록, evidence_ids 는 실제 Jev 판정에 쓴 근거만 |
| F5 | V1 D2·V2 C3 | "따르지 말라"를 "따르라"로 바꿔도 injection 시험 통과 | INSTRUCTIONS 에 금지 문구 원문을 직접 단언 |
| F6 | V1 D3·V2 C4 | 지문에서 요건·학력·floor·등급표를 빼도 시험 통과 | fingerprint 시험에 requirement.text, weight, education, confidence_floor, school/company 등급표 내용 변경 각 1건 |
| F7 | V1 D4·V2 C5 | requirement·education[]·career[] 모르는 키 거부가 무시험 | 각 위치마다 모르는 키 1건씩 거부 시험 |
| F8 | V1 D5 | jev-latest 거부, 5xx→model_unavailable, 응답검증 오류, 실패 시 human review, 1,500자 경계, evidence_coverage 무시험 | 각 1건. 1,500자는 1500 허용·1501 거부 한 쌍 |
| F9 | V1 D6·V2 C6 | 어댑터의 JSON 파싱 실패가 error/other 로 감 | TypeSafeJevJudge 가 내는 응답 파싱 오류(JSONDecodeError·비객체 TypeError)는 invalid_response. TypeSafeJevJudge 는 수정하지 말고 호출부에서 예외 종류로 분리 |
| F10 | V1 D7·V2 C7 | NFD·NBSP 학교명이 UNLISTED | 학교·회사명 정규화에 unicodedata NFKC + 공백류 통일 |
| F11 | V1 D1 | diff 1,403줄 > 1,200 | 예산은 코드·계약·시험·SOT 만 1,200줄. goal·프롬프트 문서는 예산 밖이되 goal 은 300줄 이하 |
| F12 | Codex medium | 변이 결과가 산문뿐, 재현 불가 | scripts/acceptance-evidence-assessment-mutations.sh 로 변이 목록을 스크립트화(원복·캐시 삭제·생존 0 판정 포함). CI 배선은 하지 않고 로컬 실행 결과를 goal 에 기록 |
| F13 | Codex medium | WIP 커밋 잔존, 시험 파일 600/600 | 시험을 AC 묶음별 파일로 분할(각 ≤300줄 권장, ≤600 필수). 최종 커밋 1개 |

────────────────────────────────
3단계 — 새 계약: 경력 검증 (D-2)
────────────────────────────────
입력에 career 를 추가한다(허용 필드 외 거부 유지):
  "career": [ {"company_name": "<원문>", "title": "<직함>", "start": "YYYY-MM", "end": "YYYY-MM|null",
               "summary": "<업무 요약, 1,500자 이하>"} ]   // 0개 이상

새 계약 contracts/company-tier.json (school-tier.json 과 같은 구조):
  company_tier_version, status(SYNTHETIC_PLACEHOLDER_OWNER_TO_FILL|APPROVED), tiers[{tier, rank, verdict}],
  companies{정규화 이름: tier}, aliases{별칭: 이름}. 이 WU 는 합성 표본 3~5개만.
  학교·회사 표 로더는 하나로 합친다(같은 역할 두 번째 구현 = FAIL).

판정 흐름 (requirement_id == "school_tier" 일 때만):
  1) 학력 중 최고 등급이 T1~T3 → 학교 경로(v4 그대로, 단 F3·F4 적용).
  2) 학력 없음 또는 전부 UNLISTED → career 경로:
     a. 회사 수준: career 중 최고 등급 회사(코드 판정). 없으면 UNLISTED.
     b. 업무 부합도: 그 회사 재직 항목의 summary 를 근거 E1 로, requirement.text 대신
        position 의 JD 요건 문장(입력 requirement.text)을 요건으로 Jev 에 1회 보낸다 → 5상태.
     c. 결합(코드, 계약 표로 고정 — mapping_version 에 포함):
        회사 T1~T3 × Jev SUPPORTED → 회사 등급 verdict 그대로
        회사 T1~T3 × Jev PARTIAL   → PARTIAL
        회사 UNLISTED × Jev SUPPORTED/PARTIAL → PARTIAL
        Jev NOT_STATED → NOT_STATED
        Jev CONTRADICTED / CONFLICTING → 그 값 그대로 + requires_human_review
        Jev 미완료(not_run/error/invalid_response) → 그 status 그대로, projection·coverage null
  3) 출력 school_tier 에 "basis": "school"|"career"|null, matched_company, career_index, company_tier_version 추가.
  4) 회사명은 Jev 로 보내지 않는다(summary 원문 안에 있으면 그대로 둔다 — D-1 로 허용).

────────────────────────────────
4단계 — 라이브 경로 계약 (D-1 반영)
────────────────────────────────
- 라이브 호출 = --live-jev + TYPESAFE_API_KEY + 저장소 계약 live_calls_allowed=true 셋 다일 때만.
  이번 WU 에서 계약 값을 true 로 바꾼다(사장님 D-1 승인). access_policy_version 을 올린다.
- 셋 중 하나라도 없으면 not_run, client 생성 0회.
- delivery_status: client 생성 0회 → LOCAL_ONLY, 1회 이상 → EXTERNAL_JEV. 판정은 코드가 실제 생성 여부로 정한다.
- 이 WU 의 시험·검증은 가짜 client 만 쓴다. 실제 라이브 1건 호출은 하지 않는다(WU3 범위, 품질 NOT_RUN).

────────────────────────────────
5단계 — 인수 조건
────────────────────────────────
명령: uv run --project humansearch pytest -q humansearch/tests/test_evidence_assessment*.py -k <선택자>
(분할 후 파일 글로브가 0개면 FAIL. 각 선택자 "N passed", N ≥ 최소치, 0개 수집 FAIL.)

v4 의 AC-1~14 선택자와 최소치는 그대로 유지하고, 다음을 추가·강화한다.
AC-15 career_fallback (≥6): 학력 없음 → career 경로 / 학력 전부 UNLISTED → career 경로 / 결합 표 6칸 각각
      (T1×SUPPORTED, T1×PARTIAL, UNLISTED×SUPPORTED, NOT_STATED, CONTRADICTED, Jev error) 정확한 기대값 1개씩 /
      회사명이 Jev state 에 들어가지 않음 / 학교 T1 이 있으면 career 경로를 타지 않음(judge 호출 0회).
AC-16 table_status (≥3): 학교표·회사표 status ≠ APPROVED → projection·coverage null + requires_human_review=true /
      APPROVED 사본(시험용 주입) → 정상 점수 / status 누락·미정의 값 → 로더 거부.
AC-17 delivery_status (≥3): client 0회 → LOCAL_ONLY / 가짜 client 주입 1회 → EXTERNAL_JEV /
      저장소 밖 config 로 live 허용 시도 → 종료값 2.
AC-18 provenance (≥2): 학교 판정 projection.evidence_ids == [] 이고 education_index 기록 / career 판정은 사용한 E1 만.
강화: injection 에 금지 문구 원문 단언(F5), fingerprint +6건(F6), 모르는 키 +3건(F7),
      failure_status 에 5xx·응답검증·JSON 파싱 오류·human review(F8·F9), school_tier 에 NFD·NBSP(F10).

회귀(원명령, 출력 숫자 기록):
  bash scripts/acceptance-hs-gates.sh
  python3 -m unittest discover -s tests -v
  bash verify.sh
  bash scripts/acceptance-principles-check.sh
  bash scripts/acceptance-evidence-assessment-mutations.sh   ← F12, 생존 0, 원복 확인

변이 목록(스크립트에 고정, 생산 호출 형태, 변이마다 __pycache__ 삭제):
  v4 의 18종 + V1 생존 13종(M17~M25, M32, M33, M38, M40, M41, M42) + 새 경로 5종
  (결합 표 한 칸 뒤집기 / table_status 검사 제거 / delivery_status 고정 문자열 / 저장소 밖 config 허용 / career 경로에서 회사명 전송).
  생존이 있으면 손으로 1회 재현 후 시험을 보강한다(시험 전용 변경은 사유를 goal 에 기록).

counter-AC (하나라도 걸리면 FAIL): v4 의 11개 +
  - 외부 client 를 만들었는데 LOCAL_ONLY 로 기록
  - APPROVED 가 아닌 등급표로 점수·projection 을 냄
  - 학교가 없는데 "모름"으로 끝나고 career 경로를 타지 않음
  - 학교·회사 표 로더가 두 벌
  - TypeSafeJevJudge·review_candidate·Criterion 수정

규모: 코드·계약·시험·SOT 변경 합계(6d7afa0 기준) ≤ 1,200줄. 직접 작성 파일 ≤ 600줄(시험 파일 권장 ≤300), 함수 ≤ 100줄.

────────────────────────────────
6단계 — SOT
────────────────────────────────
docs/sot/candidate-search.md:54 에 추가: "학교 정보가 없거나 등급표에 없는 학교면 재직 회사 수준(contracts/company-tier.json)과
업무의 JD 부합도로 대신 검증한다. 등급표가 APPROVED 되기 전에는 점수를 내지 않고 사람 검토로 넘긴다."
같은 문단의 "원문에 없는 학벌·연차 조건을 추가하지 않는다"는
"원문에 없는 연차 조건을 추가하지 않는다. 학교·회사 등급은 포지션별 가중 요건으로만 반영한다"로 바꾼다.
개인정보 전송 허용(D-1)은 docs/sot/candidate-search.md 개인정보 절에 결정일·범위와 함께 한 줄 기록한다.

────────────────────────────────
7단계 — 비범위
────────────────────────────────
영속화(WU2), Gmail·ClickUp·Supabase 접근, ~/valuehire-private 읽기, 실제 라이브 Jev 호출, 등급표 실내용 작성,
review_candidate/Criterion/TypeSafeJevJudge 수정, push·PR·메일, 기반 9커밋 수정.

────────────────────────────────
8단계 — 독립 검증 (V1 1회 + V2 1회로 끝)
────────────────────────────────
V1: 격리 clone(git clone --no-local --no-hardlinks, detach, core.hooksPath=/dev/null)에서
  env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u CLAUDECODE \
    perl -e 'alarm shift; exec @ARGV' 900 claude -p "$(cat <V1 프롬프트>)" \
    --setting-sources user --dangerously-skip-permissions </dev/null > .omx/artifacts/jev-ea-v5-v1-<시각>.md 2>&1
  (macOS 는 timeout 없음 → perl alarm. 저장소 안에서는 --setting-sources user 없으면 세션 훅에서 멈춘다. 셸 격리 해제 필요.)
  출력이 비었거나 EXIT≠0 → BLOCKED. V1 프롬프트에 구현자 결론·의심 금지. 끝에 strict §8-7 블록.
V2: 새 맥락 서브에이전트가 V1 의 file:line·명령을 같은 clone 에서 재실행, 선택자 수 독립 계수, 판정서는 파일로.
추가 라운드는 새 결함이 자동 탈락·외부 전송 오표기일 때만.

────────────────────────────────
9단계 — 판정과 보고
────────────────────────────────
PASS: AC-1~18 전부 N≥최소치, counter-AC 0, 회귀 5종 통과, 변이 생존 0, 루트 불변, V1·V2 PASS
      → 작업 중 커밋(RED·WIP·시험 전용)을 로컬 커밋 1개로 합친다. 메시지 trailer 에 RED SHA 와 시험 전용 변경 사유를 남긴다
        (AGENTS.md trailer 규약). push·PR 하지 않는다.
FAIL: 남은 항목과 재현 명령, 커밋 합치지 않음.
BLOCKED: 0단계 불일치·새 dependency 필요 → read-only 조사 후 결정 1개.

보고(§8 3층, 결정 최대 2개). 1층에 반드시: 기반 9커밋 미푸시·CI 미통과, 라이브 Jev 품질 NOT_RUN,
등급표 2종이 합성 자리값이라 확정 전 점수 없음.
