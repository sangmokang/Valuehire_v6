/strict

[VALUEHIRE-V6-JEV-EVIDENCE-ASSESSMENT-WU1 v8 — v6 FAIL 잔여 결함 2건 + 시험 공백 2건 마감] L3

v7 과 같은 범위다. v7 에서 바뀐 것: 규모 한도 칸을 채웠고, 낡은 0단계 항목 두 개를 고쳤다(16:37 세션 92017 은
22:05 실측으로 이미 종료됨, 원칙 검사의 VERDICT 는 마지막 줄이 아니라 첫 줄에 찍힘). 결함 위치는 22:05 에 코드로 재확인했다.

사장님 결정:
- 규모 한도: 2,000 줄 (권고값. 다른 값이면 이 숫자만 바꿔서 보낸다. 빈칸이면 0단계에서 멈춤)
  측정: git diff --numstat 6d7afa0 HEAD -- . ':!docs/engineering' 의 추가+삭제 합. 22:05 기준 1,845.
  줄 접기·서식 압축으로 맞추는 것은 금지(v6 58f6c74 사고).

0단계 (하나라도 어긋나면 코드 0줄, 불일치표만 보고하고 멈춤):
a. 작업트리 worktrees/jev-evidence-assessment-wu1, 브랜치 task/jev-evidence-assessment-wu1.
   git log --oneline f5a1224..HEAD 가 이 v8 지시 파일을 추가한 커밋 1개뿐인지. 모르는 커밋이 있으면 멈춤.
   git status --porcelain 이 0줄인지.
b. 이 작업트리를 cwd 로 쓰는 codex/claude 가 자기 자신뿐인지:
   lsof -a -d cwd -Fpcn | awk 로 (pid, command, cwd) 를 뽑아 경로가 worktrees/jev-evidence-assessment-wu1 인 행을 세고
   자기 pid·부모 pid 를 뺀다. 양성 대조로 Valuehire_v6 전체 경로 행 수가 1 이상인지 함께 적는다(0이면 도구 고장 → 멈춤).
c. 루트 작업트리 git status --porcelain | shasum -a 256 을 기록한다(22:05 기준 ebf967e6…). 끝날 때 같은 값이어야 한다.
   루트는 읽기만 한다. ~/valuehire-private 는 열지 않는다.
d. bash scripts/acceptance-principles-check.sh → rc 0 이고 출력에 "VERDICT: PASS" 줄이 있는지(위치는 보지 않음).
e. gh pr list --state open --search "jev" → 같은 목적 PR 이 없는지.
f. 기반 9커밋(6d7afa0 이하)이 미푸시·CI 미통과라는 사실을 보고 1층에 적는다.

닫을 결함 (항목마다 실패하는 시험을 먼저 커밋하고, 그다음 최소 구현. RED 는 TypeError 가 아니라 동작 실패여야 한다):

F16 [높음] 저장소 계약 덮어쓰기.
    현재: humansearch/src/humansearch/evidence_assessment_cli.py:52 의 출력 충돌 비교 목록이
    [args.input, args.config, *TIER_PATHS.values()] 라서, --config 를 다른 파일로 주면 CONTRACT_PATH 가 목록에서 빠진다.
    재현: python -m humansearch.evidence_assessment_cli --input in.json --config other.json --output contracts/jev-evidence-assessment.json → rc 0.
    수정: 비교 목록에 CONTRACT_PATH 를 항상 넣는다.
    시험: 외부 --config + 출력=저장소 계약 → rc 2, 오류 코드 output_collision, 계약 파일 바이트 불변.
          시험은 tmp 사본을 CONTRACT_PATH 로 바꿔 끼워 실행한다(실제 저장소 계약을 건드리지 않음).

F17 [높음] 승인 등급표의 별칭 충돌이 조용히 덮어써진다.
    현재: humansearch/src/humansearch/tier_table.py:65-66 의 dict 컴프리헨션이 정규화 뒤 같은 별칭 키를 뒤의 값으로 덮어쓰고,
    별칭 키가 다른 항목 이름과 같아도 막지 않는다. resolve_tier(:82) 는 별칭을 먼저 찾기 때문에 T1 학교가 T3 로 매겨진다
    (v6 V2 재현: 30점 중 15점).
    수정: 두 경우 모두 ValueError 로 거부한다.
      (1) 정규화한 별칭 키가 정규화한 항목 이름과 같은데 가리키는 항목이 자기 자신이 아닌 경우
      (2) 두 별칭이 정규화 뒤 같은 키가 되는 경우
    합법 경계쌍(양성 대조): 별칭이 자기 항목 이름과 같은 경우, 서로 다른 별칭이 같은 항목을 가리키는 경우는 통과해야 한다.
    시험: 학교·회사 × (1)(2) 4종 거부 + 양성 대조 2종 통과 + 명령줄 경로에서 종료값 2.

F18 [시험 공백] evidence_assessment_cli.py 의 _same_file 에서 resolve() 비교를 지워도 기존 시험 167개가 통과한다.
    시험 추가: 출력 경로 <tmp>/없는폴더/../in.json (입력과 같은 파일) → rc 2, output_collision. AC-20 선택자에 넣는다.

F19 [시험 공백] 저장소 밖 설정 파일의 live=true 거부 시험이 파일 이름 cfg.json 하나뿐이다.
    "이름만 같으면 저장소 계약으로 인정" 변이가 초록으로 살아남는다(v6 V2 X13).
    시험 추가: 다른 폴더의 같은 이름 jev-evidence-assessment.json(live_calls_allowed=true) → rc 2.

비범위 (goal 백로그 절에 기록만): 보이지 않는 글자 변형(U+3164·U+115F·U+034F), 한국어 "합성" 표식, 전송 표기 시험
X1·X3·X9, 순위·basis 시험 X4·X5·X10, 보호 목록 밖 파일(다른 계약·소스) 덮어쓰기, 라이브 문 위치(설계 1),
라이브 Jev 호출, 영속화, Gmail·ClickUp·Supabase 읽기/쓰기, review_candidate 수정.

검증 (한 바퀴, ADR 0012):
1. 회귀 5종 원명령과 출력 숫자 그대로:
   bash scripts/acceptance-hs-gates.sh / python3 -m unittest discover -s tests -v / bash verify.sh /
   bash scripts/acceptance-principles-check.sh / bash scripts/acceptance-evidence-assessment-mutations.sh
2. 변이 목록에 역변이 5종 추가: F16(목록에서 CONTRACT_PATH 제거), F17(항목 가림 허용), F17b(별칭끼리 충돌 허용),
   F18(resolve 비교 제거), F19(이름만 비교). 변이마다 __pycache__ 삭제, 생산 호출 형태(명령줄)로 실행, 생존 0.
   생존이 나오면 손으로 1회 재현해 등가 변이인지 가린다.
3. AC 선택자별 "N passed" 를 원문으로 기록한다. 0개 수집은 FAIL.
4. V1 1회: git clone --no-local 격리 사본 + uv sync --frozen 후
   env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u CLAUDECODE perl -e 'alarm shift; exec @ARGV' 900 \
     claude -p "<프롬프트>" --setting-sources user --dangerously-skip-permissions </dev/null \
     > .omx/artifacts/jev-ea-v8-v1-<시각>.md 2>&1 ; echo "EXIT=$?"
   프롬프트에 구현자 결론·의심을 넣지 않고 strict §8-7 블록을 붙인다. 출력이 비었거나 EXIT≠0 이면 BLOCKED(원문 보존).
   V1 이 높음·중간 결함을 내면 V2(새 맥락)로 재현만 하고 추가 라운드는 돌리지 않는다.
5. goal 문서의 규모·검증 장부·적대 검증 로그·최종 판정 칸을 갱신한다. 커밋 순서표에 모든 SHA 를 적는다(58f6c74 포함).

판정 (셋 중 하나):
- PASS: F16~F19 시험 GREEN, 회귀 5종 PASS, 변이 생존 0, V1 PASS, 루트 해시 불변, 규모 ≤ 결정값
  → 6d7afa0 위 작업 커밋 전부를 로컬 커밋 1개로 합친다. trailer 에 RED SHA 들, 시험 전용 변경 사유, 사장님 규모 결정값을 남긴다.
- FAIL: 남은 항목과 재현 명령만 보고한다. 커밋을 합치지 않는다.
- BLOCKED: 0단계 불일치, 결정값 빈칸, V1 실행 불가 → 결정 1개를 적고 멈춘다.
push·PR·메일·라이브 Jev 호출은 하지 않는다.

보고: strict §8 3층, 결정은 최대 2개.
1층에 기반 9커밋 미푸시·CI 미통과, 라이브 Jev 품질 NOT_RUN, 학교·회사 등급표는 합성 자리값이라 미확정임을 적는다.

WU3 착수 전제 (이번에는 하지 않음, 기록만): Gmail 원장은 검색어로 골라 수집했고 Gmail 원본 대비 누락 대조가 없다.
미해석 [추천] 제목 423건, 인보이스 미연결 약 19건, 회사|이름 키로 같은 회사 여러 포지션이 합쳐짐, 첨부 0개 추천 178건,
거절 라벨에 후보 자진 철회가 섞임. WU3 는 이 보정부터 한다.
