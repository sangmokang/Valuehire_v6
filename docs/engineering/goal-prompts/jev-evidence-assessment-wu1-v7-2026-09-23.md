/strict

[VALUEHIRE-V6-JEV-EVIDENCE-ASSESSMENT-WU1 v7 — 남은 결함 2건 + 시험 공백 2건 마감] L3

사장님 결정 (착수 전 채움. 비어 있으면 0단계에서 멈춤):
- 규모 한도: ______ 줄 (현재 1,845. 권고 2,000 — 아래 4건 수정분 포함. 줄 접기로 맞추는 것은 금지)

0단계 (하나라도 어긋나면 멈추고 보고):
a. worktrees/jev-evidence-assessment-wu1 HEAD 가 1400506 이후인지. `git log --oneline 1400506..HEAD` 에 모르는 커밋이 있으면 멈춤
   (2026-09-23 17:36 다른 세션이 이 작업트리에 9d6d00e 를 커밋한 사고가 있었다).
b. 이 작업트리를 cwd 로 쓰는 codex/claude 가 자기 자신뿐인지 (`lsof -a -d cwd -Fpcn` + awk 로 경로 필드 대조).
   추가로 `ps -axo pid,lstart,command | /usr/bin/grep -E "claude|codex"` 에서 16:37 시작 세션(92017)이 살아 있으면
   그 세션이 이 작업트리를 git -C 로 쓰는지 사장님께 먼저 확인.
c. 루트 작업트리 `git status --porcelain | shasum -a 256` 기록(9/23 기준 ebf967e6…). ~/valuehire-private 는 읽기만.

닫을 결함 (각 항목 실패 시험 먼저 커밋, 그다음 최소 구현):
F16 [높음] 저장소 계약 덮어쓰기 — `--config other.json --output contracts/jev-evidence-assessment.json` 이 rc 0 으로 덮어쓴다
    (evidence_assessment_cli.py:52 비교 목록에 CONTRACT_PATH 가 없음). 비교 목록에 CONTRACT_PATH 를 항상 넣는다.
    시험: 외부 --config + 출력=저장소 계약 → rc 2·output_collision·계약 바이트 불변(시험은 tmp 사본을 CONTRACT_PATH 로 교체해 실행).
F17 [높음] 별칭 충돌 — 승인 표에서 정규화 별칭 키가 항목 키와 같거나(항목을 가림) 별칭끼리 정규화 뒤 같으면 로더가 조용히 덮어써
    T1 학교를 T3(30점 중 15점)로 매긴다 (tier_table.py:65-69, 조회 :82). 두 경우 모두 ValueError 로 거부.
    시험: 학교·회사 × (별칭=항목명, 별칭끼리 충돌) 4종 + 명령줄 경로에서 종료값 2.
F18 [시험 공백] `_same_file` 의 resolve() 비교를 지워도 167 통과. 출력 `<tmp>/없는폴더/../in.json` 사례를 AC-20 에 추가.
F19 [시험 공백] 저장소 밖 설정 live=true 거부 시험이 파일 이름 cfg.json 하나뿐(이전 V2 X13: 이름만 같으면 통과하게 바꿔도 초록).
    다른 폴더의 같은 이름 `jev-evidence-assessment.json` 사례 추가.

비범위 (다음 WU 백로그로 goal 에 기록만): 보이지 않는 글자 변형(U+3164·U+115F·U+034F), 한국어 "합성" 표식, 전송 표기 시험 X1·X3·X9,
순위·basis 시험 X4·X5·X10, 보호 목록 밖 파일 덮어쓰기(다른 계약·소스), 라이브 문 위치(설계 1).

그다음 (한 바퀴, ADR 0012):
- 회귀 5종 원명령·숫자: acceptance-hs-gates, unittest, verify.sh, principles-check, acceptance-evidence-assessment-mutations.sh.
  변이 목록에 F16·F17(항목 가림)·F17b(별칭끼리)·F18(resolve 제거)·F19(이름 비교) 역변이 5종 추가, 생존 0.
- V1 1회: 격리 `git clone --no-local` + `uv sync --frozen`, env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u CLAUDECODE
  perl -e 'alarm shift; exec @ARGV' 900 claude -p "<프롬프트>" --setting-sources user --dangerously-skip-permissions </dev/null
  > .omx/artifacts/jev-ea-v7-v1-<시각>.md. 구현자 결론 금지, strict §8-7 블록. V1 이 높음·중간 결함을 내면 V2 로 재현.
- goal 의 규모·장부·V1(·V2)·최종 판정 칸 갱신. 커밋 순서표에 모든 SHA(줄 접기 커밋 58f6c74 포함)를 적는다.

PASS(F16~F19 AC·회귀 5종·변이 생존 0·V1 PASS·루트 불변·규모 ≤ 결정값) → 작업 중 커밋 전부를 로컬 커밋 1개로 합치고
trailer 에 RED SHA 들·시험 전용 변경 사유·사장님 규모 결정값을 남긴다. push·PR·라이브 Jev 호출 하지 않는다.
FAIL → 남은 항목과 재현 명령만 보고, 커밋 합치지 않음.
보고: §8 3층, 결정 최대 2개. 1층에 기반 9커밋 미푸시·CI 미통과, 라이브 Jev 품질 NOT_RUN, 등급표 미확정 명시.

WU3 착수 전제 (이 WU 에서는 하지 않음, 기록만): Gmail 원장(~/valuehire-private/valuehire_sot_gmail.sqlite3)은 검색어로 골라 수집했고
Gmail 원본 대비 누락 대조가 없다. 미해석 [추천] 제목 423건, 인보이스 미연결 ~19건, 회사|이름 키로 같은 회사 여러 포지션 합쳐짐,
첨부 0개 추천 178건, 거절 라벨에 후보 자진 철회 혼입. WU3 는 이 보정부터 한다.
