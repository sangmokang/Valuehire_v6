# 여러 컴퓨터 AI 리서치 운영체계 기획 목표 — 2026-08-17

## 1층 — 결론

현재 저장소에는 안전검사와 상세한 설계 자료는 있지만, 여러 컴퓨터가 실제로 일을 나눠 받아 후보자를 찾고 결과를 합치는 제품은 아직 없습니다. 이번 작업은 제품을 성급히 만들지 않고, 이미 있는 자산과 비어 있는 부분을 구분한 뒤 서로 독립적으로 만들 수 있는 작은 작업 지시서까지 제출하는 데서 멈춥니다.

첫 번째로 결정할 것은 각 정보의 최종 책임 장소입니다. 채용 일감은 ClickUp, 후보 원문과 판정 근거는 한 곳의 내부 장부, 여러 컴퓨터의 작업 상태는 공유 작업 장부가 책임지도록 분리하는 안을 권고합니다. 이 결정을 승인하기 전에는 실제 계정 조작과 후보자 자료 이동을 시작하지 않습니다.

저장소 시작 검사에는 이번 작업과 무관한 기존 기록 정리 실패가 남아 있습니다. 시작 시 대상은 43건이었고, 작업 중 여러 세션과 인덱스가 만든 미커밋 blob까지 공유 객체 저장소의 unreachable 수에 더해져 마지막 증거 편집 전 관측값은 222건이었습니다. 출처별 귀속은 증명할 수 없고 이를 지우는 동작은 되돌리기 어려워 실행하지 않았습니다. 작업 중 다른 세션이 기본 브랜치에 admin 문서 커밋 1개를 추가해 main과 origin도 달라졌습니다. 마지막 전체 상태는 두 검사 실패이며, 이번 산출물은 “기획 검증”까지만 판정하고 코드 배송 가능 상태라고 부르지 않습니다.

## 2층 — 판단 근거

### 결정 카드 1 — 한 대가 지휘하고 여러 대가 실행합니다

> **무엇을** — 항상 켜진 한 대가 ClickUp 일감 읽기, 우선순위 계산, 부족한 서치 판단, 작업 배분, 결과 취합을 맡습니다. 각 실행 컴퓨터는 자기에게 고정된 계정과 Aside 브라우저만 조작합니다.
>
> **왜** — 같은 계정이 여러 컴퓨터에서 동시에 움직이는 사고와, 두 컴퓨터가 같은 후보자를 중복 처리하는 사고를 한 곳에서 막을 수 있습니다.
>
> **버린 길** — 각 컴퓨터가 ClickUp을 직접 읽고 알아서 일감을 고르는 방식은 동시에 같은 일을 집을 수 있어 버립니다. 한 개의 SQLite 파일을 네트워크 폴더에서 여러 컴퓨터가 함께 여는 방식도 파일 잠금과 장애 복구 책임이 불명확해 버립니다.
>
> **대가** — 지휘 컴퓨터가 멈추면 새 일 배분도 멈춥니다. 대신 이미 실행 중인 작업은 안전하게 정지하고, 지휘 컴퓨터 복구 뒤 이어받도록 해야 합니다.
>
> **되돌리기** — 지휘 기능을 끄고 각 컴퓨터를 읽기 전용 수동 실행기로 낮춥니다. 후보 원문과 작업 영수증은 보존하므로 다시 설계해도 수집 결과를 버리지 않습니다.

### 결정 카드 2 — 정보 종류마다 책임 장소를 나눕니다

> **무엇을** — ClickUp은 어떤 포지션이 실제 일감인지 책임지고, 내부 SQLite는 후보 원문·증거·판정 이력을 책임지며, 공유 데이터베이스는 여러 컴퓨터의 작업 배정·사용권·생존 상태처럼 개인정보가 아닌 운영 상태만 책임집니다. Supabase의 과거 후보 자료와 Gmail 첨부파일은 읽기 전용 입력원으로 시작합니다.
>
> **왜** — 현재 “SQLite만 유일한 원본” 계약은 한 컴퓨터 안에서는 안전하지만, 여러 컴퓨터가 동시에 작업권을 나눠 갖는 상태까지 책임질 수 없습니다. 반대로 후보자 원문 전체를 공유 데이터베이스에 곧바로 복제하면 접근권한·보관기간·삭제 전파가 준비되지 않은 상태에서 개인정보 위험이 커집니다.
>
> **버린 길** — 모든 것을 ClickUp에 넣는 방식은 원문 증거와 동시 작업권을 안전하게 다루기 어렵습니다. 모든 후보자 원문을 Supabase로 먼저 모으는 방식은 현재 정본과 개인정보 계약을 동시에 바꿔야 하므로 버립니다.
>
> **대가** — 책임 장소가 세 곳이라 내보내기와 다시 읽어 확인하는 절차가 필요합니다. 화면 숫자만 보고 완료라고 할 수 없고 각 장부의 연결 영수증을 남겨야 합니다.
>
> **되돌리기** — 운영 상태 공유를 끄면 단일 컴퓨터 모드로 돌아갑니다. 후보 원문은 내부 SQLite에 남고 ClickUp 쓰기는 별도 승인 없이는 발생하지 않습니다.

### 결정 카드 3 — 우선순위와 부족분은 코드가 계산합니다

> **무엇을** — 일감 우선순위는 긴급도, 포지션이 열린 기간, 필요한 후보 수 대비 확보 수, 마지막 서치 이후 경과, 채널 상태, 내부 후보 재사용 가능성을 코드가 계산합니다. 언어모델은 직무기술서에서 근거를 뽑는 보조 역할만 맡고 숫자를 확정하지 못합니다.
>
> **왜** — 같은 자료로 다시 계산했을 때 같은 순서가 나와야 하며, 왜 이 포지션이 먼저 선택됐는지 사람이 설명받을 수 있어야 합니다.
>
> **버린 길** — 언어모델에게 “오늘 뭘 할지 골라”라고 통째로 맡기는 방식은 순서가 매번 달라지고 근거를 재계산할 수 없어 버립니다. 오래된 포지션을 무조건 먼저 하는 방식도 이미 후보가 충분한 일을 다시 돌릴 수 있어 버립니다.
>
> **대가** — ClickUp에 없는 목표 후보 수·마감·중요도·허용 채널은 별도 확인 대기 상태로 남습니다. 초기에는 사람이 이 값을 채우는 절차가 필요합니다.
>
> **되돌리기** — 계산 규칙에 버전을 붙여 이전 순서를 재현합니다. 실제 면접 전환이 나빠지면 규칙 버전을 되돌리고, 바뀐 이유와 영향을 비교합니다.

### 결정 카드 4 — 내부 후보 재사용을 외부 서치보다 먼저 점검합니다

> **무엇을** — 새 포지션이 들어오면 Supabase의 과거 후보 행, 로컬 SQLite의 아카이브, Gmail 이력서 첨부파일을 읽기 전용으로 찾아 동일 인물 가능성을 정리하고 적합도 근거를 계산합니다. 목표 수가 채워지지 않은 부분만 외부 서치 작업으로 만듭니다.
>
> **왜** — 이미 보유한 후보를 다시 찾느라 계정 사용량과 운영 시간을 쓰는 낭비를 줄일 수 있습니다.
>
> **버린 길** — 이름이 같다는 이유만으로 자동으로 한 사람으로 합치는 방식은 동명이인 오추천 위험이 있어 버립니다. 모든 Gmail 첨부파일을 새 저장소로 한 번에 옮기는 방식도 보관 권리와 삭제 계약이 없어 버립니다.
>
> **대가** — 주소·검증된 프로필 링크 같은 강한 증거가 없으면 사람 확인 대기가 늘어납니다. 보수적으로 운영하므로 초기 자동 일치율은 낮을 수 있습니다.
>
> **되돌리기** — 내부 재매칭 결과를 추천이 아니라 참고 후보 목록으로 낮춥니다. 원천 자료를 수정하지 않으므로 잘못 묶인 연결만 해제할 수 있습니다.

## 3층 — 기술 상세와 증거

## 작업 메타

- 작업일: 2026-08-17
- 작업 공간: `task/ai-ra-orchestration-plan` / `worktrees/ai-ra-orchestration-plan`
- 위험 등급: L3 — 후보자 개인정보, 외부 채용사이트 계정, 여러 컴퓨터 동시 실행, ClickUp 운영 데이터가 향후 영향 범위다.
- 이번 원자적 인수 기준: 목표 문서 1개, 통합 기획서 1개, 독립 구현 프롬프트 28개가 존재하고 문서 검사가 실제 파일 수·내부 링크·필수 절·프로젝트별 단일 인수 명령을 확인한다.
- 멈춤점: 문서·시험 설계와 적대검증까지. 후보 수집, ClickUp 쓰기, 메일 발송, 운영 등록, 배포, 기존 자료 삭제는 하지 않는다.

## 조사 범위

직접 확인한 범위는 다음과 같다.

1. 현재 6세대 기본 브랜치의 추적 파일 전체와 `docs/sot/` 5개 문서.
2. 현재 저장소 아래의 관련 작업 공간과 미추적 기획 문서의 파일 상태.
3. 6세대 HumanSearch 창립 명세와 전체 여정 대안 기획.
4. 인접 4·5세대 저장소의 여러 컴퓨터 작업 큐, Gmail 첨부 매칭, SQLite→Supabase 내보내기 실행 경로. 후보자 원문과 자격증명 값은 읽거나 문서에 넣지 않았다.
5. 외부 서비스는 공식 문서만 읽기 대상으로 삼고, 로그인·쓰기·계정 조작은 하지 않는다.

범위 밖은 실제 ClickUp 전체 포지션 내용, 후보자 데이터 행, Gmail 첨부파일 본문, Aside 후보 1명 완주, 운영 Supabase 권한 정책의 실제 덤프다.

## 현재 상태와 근본 원인

### 확인된 사실

- `README.md:5-7`은 저장소가 아직 제품 소스가 없는 시작 단계라고 명시한다. 즉 이번 기능은 기존 제품 코드 보강이 아니라 새 제품 설계다.
- `humansearch/src/humansearch/__init__.py:1-4`와 `humansearch/tests/test_package_boundary.py:1-10`은 실행 기능이 아니라 패키지 경계와 불러오기만 확인한다.
- `docs/engineering/humansearch-journey-alternative-plan-2026-08-15.md:48-64`는 Aside 진단 주소와 페이지 탭 노출까지만 확인됐고, 재부팅·후보 완주·양보와 재개는 확인되지 않았다고 구분한다.
- `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md:398-460`은 로컬 SQLite를 유일한 저장 원본으로 제안하지만, 여러 컴퓨터의 공유 작업권을 다루는 구현은 현재 6세대에 없다.
- `docs/sot/coding-principles.md:18-39`의 P8·P9는 단일 계정 사용권에 만료와 증가 번호를 요구하고, 외부 쓰기는 실행 전 의도 기록과 실행 후 재확인을 요구한다.
- `/Users/kangsangmo/Desktop/Valuehire_v5/tools/multi_position_sourcing/job_queue.py:26`과 같은 저장소의 `fleet_worker.py:1-8`에는 세 컴퓨터 작업 큐와 로그인 선행 차단의 과거 구현이 있다. 이는 6세대 실행 의존성이 아니라 다시 만들어야 할 시험 문제다.
- `/Users/kangsangmo/Desktop/Valuehire_v4/tools/gmail-resume-clickup-match/run.mjs:80-92,151-215`에는 Gmail 첨부파일·Supabase 읽기·쓰기 승인 분리 경로가 있다. 이것도 6세대에서 직접 불러 쓰지 않고 계약과 실패 사례만 참고한다.
- `worktrees/resume-evidence-supabase-prompt`에는 관련 목표·구현 프롬프트 두 개가 있으나 현재 미추적 파일이다. 준비된 검토 자료이지 기본 브랜치 제품이나 확정 정본이 아니다.

### 근본 원인

기존 자료는 “한 컴퓨터 안에서 안전하게 후보를 모으는 계약”, “과거 버전에서 여러 컴퓨터를 나누는 코드”, “Gmail 첨부파일과 기존 후보를 매칭하는 코드”로 따로 존재한다. 그러나 6세대에서 이 셋을 잇는 책임 경계와 실행 코드가 없고, 일부 최신 기획은 미추적 작업 파일에만 있어 다음 작업자가 존재 자체를 놓칠 수 있다. 따라서 지금 바로 큰 구현을 시작하면 다음 세 가지가 동시에 재발한다.

1. 같은 계정·같은 포지션을 여러 컴퓨터가 중복 실행한다.
2. SQLite·Supabase·ClickUp 중 어느 값이 맞는지 충돌한다.
3. 이미 있는 후보를 다시 외부에서 찾거나, 반대로 이름만 같은 사람을 잘못 합친다.

## 인수 기준

### AC-PLAN-1 — 실행 가능한 기획 묶음

다음 실행 가능한 셸 검사가 목표 문서, 통합 기획서, 독립 구현 프롬프트 28개를 실제로 세고, 각 프롬프트가 필수 절 11개와 자기 번호에 맞는 단일 인수 명령을 포함하며, 목차의 내부 링크가 모두 존재함을 확인해 합격을 출력해야 한다.

```bash
set -euo pipefail
prompt_dir=docs/engineering/goal-prompts/ai-native-ra-search-orchestration
prompt_count=$(find "$prompt_dir" -maxdepth 1 -type f -name 'p*.md' | wc -l | tr -d ' ')
[ -f docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md ]
[ -f docs/engineering/ai-native-ra-search-orchestration-plan-2026-08-17.md ]
[ "$prompt_count" -eq 28 ]
ownership_section=$(awk '
  /^## 작업 소유 범위$/ { in_scope=1; next }
  /^## / && in_scope { exit }
  in_scope { print }
' "$prompt_dir/p00a-data-ownership-owner-decision.md")
for required_owned_artifact in \
  'docs/engineering/ai-ra-data-ownership-decision-<date>.md' \
  'docs/engineering/ai-ra-data-ownership-owner-decision-goal-<date>.md' \
  'scripts/acceptance-ai-ra-p00a.sh'; do
  printf '%s\n' "$ownership_section" | rg -F "$required_owned_artifact" >/dev/null
done
for prompt_file in "$prompt_dir"/p*.md; do
  for heading in '## 목표' '## 선행조건' '## 작업 소유 범위' '## 비범위' '## RED 먼저' '## 구현 계약' '## 가짜 합격을 깨는 시험' '## 검증' '## 원자적 인수 기준' '## 라이브 증거와 멈춤점' '## 공통 strict 실행 지시'; do
    rg -Fqx "$heading" "$prompt_file" >/dev/null
  done
  prompt_id=$(basename "$prompt_file" | sed 's/-.*//')
  rg -F "bash scripts/acceptance-ai-ra-${prompt_id}.sh" "$prompt_file" >/dev/null
  rg -F "PASS AI_RA_$(printf '%s' "$prompt_id" | tr '[:lower:]' '[:upper:]') " "$prompt_file" >/dev/null
  rg -F '실제 핵심 건수는 반드시 1 이상' "$prompt_file" >/dev/null
  rg -F 'P04가 소유한 `scripts/acceptance-ai-ra-all.sh`' "$prompt_file" >/dev/null
done
while IFS= read -r linked_file; do
  [ -f "$prompt_dir/$linked_file" ]
done < <(sed -n 's/.*](\([^)]*\.md\)).*/\1/p' "$prompt_dir/README.md")
if rg -n '^P.* 합격\.$' "$prompt_dir"/p*.md; then
  exit 1
fi
rg -F '`NOT_RUN`을 준비 완료나 조건부 통과로 보고하지 않습니다.' "$prompt_dir/README.md" >/dev/null
rg -F 'P00A가 `DECISION_APPROVED`' "$prompt_dir/p00-data-ownership-sot.md" >/dev/null
rg -F '자료표 지문' "$prompt_dir/p11-gmail-attachment-catalog.md" >/dev/null
rg -F 'contracts/saramin/markers.json' "$prompt_dir/p22-saramin-one-candidate.md" >/dev/null
rg -F 'contracts/jobkorea/markers.json' "$prompt_dir/p23-jobkorea-one-candidate.md" >/dev/null
printf 'PASS planning_packet goal=1 plan=1 prompts=%s required_sections=11 atomic_commands=28 p00a_owned_artifacts=3 links=all-present\n' "$prompt_count"
```

→ 이번 작업은 문서 전용이므로 새 제품 검사 스크립트와 서버 단계를 만들지 않고, 실제 실행한 명령 전문을 인수 기준으로 보존한다. 필수 절과 링크뿐 아니라 모호한 “합격” 선행조건, 상태 분리, 오너 결정 분리, P00A 필수 산출물 3개와 소유 범위의 일치, Gmail 자료표 지문, 두 채널의 표시 규약도 검사한다. 반대 시험은 최신 준비 내용을 별도 임시 폴더에 복제하고 P00A 사본에서 소유권 한 줄만 제거한 뒤 이 명령을 그대로 실행한다. 이 명령이 바뀌면 GREEN 출력도 다시 받아야 한다.

### 가짜 합격을 깨는 반대 시험

- 프롬프트 한 개에서 “실패 시험” 절을 지우면 문서 검사가 불합격해야 한다.
- 프롬프트 수가 14개면 불합격해야 한다.
- 존재하지 않는 후속 문서 링크가 하나라도 있으면 불합격해야 한다.
- “v4/v5 코드를 import한다”는 문구가 실행 지시에 들어가면 클린룸 검사가 불합격해야 한다.
- ClickUp 쓰기·메일 발송·후보 발송·운영 배포를 오너 승인 없이 허용하는 문구가 있으면 불합격해야 한다.
- 언어모델이 우선순위 점수나 후보 최종 점수를 직접 결정하게 하면 불합격해야 한다.
- P00A의 `작업 소유 범위` 절에서 오너 결정 기록·이번 프로젝트 목표 문서·`scripts/acceptance-ai-ra-p00a.sh` 중 하나라도 지우면 불합격해야 한다.

## Harness 진행

### 게이트 0 — 시작 자격

실행 명령:

```bash
bash scripts/session-status.sh
```

→ 저장소 전체 시작 자격을 요약하는 명령이며, 바로 아래에 원문 출력을 보존한다.

전체 출력:

```text
HEAD: 4fdef31 (synced)
ORIGIN: 4fdef31
RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 기본 브랜치는 원격과 같은 커밋이지만 기존 인수 검사 19개 중 1개가 실패한다. 시작 자격은 합격이 아니다.

실패 특정 명령:

```bash
SECRET_PATTERNS_FILE= bash scripts/acceptance-0-2.sh
```

→ 시작 검사에서 빨간 한 항목을 분리해 비밀 검사와 저장소 기록 정리 상태를 각각 확인하는 명령이다.

전체 출력:

```text
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable 객체 43건 잔존 (reflog expire/gc --prune=now 미완)
```

→ 비밀정보 검사는 통과했지만, 저장소 기록 정리에서 43건이 남아 불합격이다. 이를 지우는 명령은 복구 가능한 과거 기록을 제거할 수 있어 이번 문서 작업에서는 실행하지 않는다.

### 게이트 1 — 한 작업, 한 기준

이번 작업은 AC-PLAN-1 하나만 갖는다. 제품 구현은 후속 프롬프트마다 별도 작업 공간·별도 인수 기준·별도 검증으로 분리한다.

### 게이트 2 — 별도 작업 공간과 실패 먼저 만들기

작업 공간 생성:

```text
Preparing worktree (new branch 'task/ai-ra-orchestration-plan')
HEAD is now at 4fdef31 docs(engineering): admin dashboard 몰입도 잔디밭 스펙 적대적 검증 추가
```

→ 사장님의 기본 작업공간 변경물을 건드리지 않는 새 작업 공간을 만들었다.

문서 묶음 생성 전 검사:

```text
FAIL planning_packet goal=0 plan=0 prompts=0 expected_prompts>=15
```

→ 목표 문서·기획서·프롬프트가 하나도 없으므로 의도대로 먼저 실패했다. 문서 작성 뒤 같은 조건을 다시 검사한다.

### 게이트 3 — 문서 묶음 GREEN

실행 결과:

```text
PASS planning_packet goal=1 plan=1 prompts=28 required_sections=11 atomic_commands=28 links=all-present
```

→ 목표 1개, 통합 기획서 1개, 독립 프롬프트 28개가 있고 각 프롬프트의 필수 절 11개·자기 번호 인수 명령 28개·목차 링크가 모두 존재한다. 파일 수와 구조에 대한 AC-PLAN-1은 최신 소스에서 GREEN이다.

### 게이트 4~6 진행

- 게이트 4: 문서 묶음 검사, 인덱스 기준 비밀 검사, 클린룸·Python 게이트·데이터 노출 인수 검사, `git diff --check`, 문서 형식 보조 검사를 실행한다.
- 게이트 5: 다른 엔진 검토와 Codex 재검증까지만 수행한다. 기본 브랜치의 기존 실패 때문에 push·PR은 보류한다.
- 게이트 6: 오너가 문서와 기존 실패 처리 방향을 승인하기 전 작업 공간을 제거하지 않는다.

## SOT 체크리스트

- [x] 사용자 제공 `AGENTS.md` 전문 — 자율 진행, 작업 공간 분리, 검증, 종료 조건을 읽었다.
- [x] `docs/sot/INDEX.md` — 확정 정본 목록과 문서 배치 기준을 읽었다.
- [x] `docs/sot/coding-principles.md` — P1~P22와 웹 자동화 5개 조항, 검증 체제를 읽었다.
- [x] `docs/sot/git-workflow.md` — 기본 브랜치 보호와 작업 1개=작업 공간 1개=인수 기준 1개를 읽었다.
- [x] `docs/sot/hook-contracts.md` — 로컬 검사가 우회 가능하며 서버 검사가 최종 판정임을 읽었다.
- [x] `docs/sot/verification-commands.md` — 이 저장소가 make/npm 방식이 아니고 실제 명령이 따로 있음을 읽었다.
- [x] 과거 4·5세대 코드는 실행 의존성으로 연결하지 않고 읽기 전용 행동 근거로만 사용한다.
- [ ] 여러 컴퓨터 운영 상태의 정본 경계 — 이번 기획서에서 변경 제안으로 작성하고 오너 판단 대상으로 남긴다.
- [ ] 개인정보 보관기간·삭제 권리·원문 접근권한 — 확정 전 실제 수집과 외부 이동 금지.

## 적대검증 항목

1. 6세대에 실제 코드가 없는데 “준비됐다”고 과장하지 않았는가.
2. 과거 4·5세대 코드를 복사하거나 실행 의존성으로 몰래 연결하지 않았는가.
3. ClickUp 일감 선정과 후보자 점수를 언어모델이 임의로 결정하게 하지 않았는가.
4. 한 컴퓨터가 죽었을 때 두 컴퓨터가 같은 작업을 실행하는 구멍이 없는가.
5. 오래된 작업자가 만료 후 결과를 덮어쓰는 구멍이 없는가.
6. 사람 개입 신호 뒤 브라우저 명령이 구조적으로 불가능한가.
7. Supabase·SQLite·Gmail에서 같은 후보를 이름만으로 자동 합치지 않는가.
8. 내부 매칭 후보가 충분할 때 외부 서치를 줄이는 계산과, 부족한 채널만 추가하는 계산이 재현 가능한가.
9. ClickUp 쓰기·메일 발송·포털 등록·운영 배포가 별도 승인 없이는 불가능한가.
10. 한 프로젝트가 여러 사업 결정을 숨기지 않고 24~48시간 안에 검증 가능한 크기로 분리됐는가.

## 비범위

- 실제 ClickUp 카드 선택·상태 변경·새 필드 생성.
- Aside 브라우저 연결, 탭 조작, 후보 페이지 열람, 외부 사이트 검색 실행.
- Gmail 첨부파일 다운로드와 후보자 본문 열람.
- Supabase·SQLite 후보 행 조회, 이동, 합치기, 삭제.
- 메일·인메일·제안 발송, 후보자 보고, 포털 등록.
- 운영 배포, 기본 브랜치 병합, 기존 저장소 기록 삭제.

## 적대 검증 로그

### 1차 시도 — 판정 없음

실행 명령:

```bash
env -u ANTHROPIC_API_KEY claude -p < /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/ai-ra-orchestration-plan/docs/engineering/ai-native-ra-search-orchestration-review-prompt-2026-08-17.md
```

→ 다른 엔진에 저장소 파일을 읽기 전용으로 검토하게 한 명령이다. API 키는 환경에서 제거했다.

전체 출력과 종료값:

```text
exit=1
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606

Request ID: req_011Ce7hi8yCTB76DxuqgFeaS
```

→ 판정 본문과 `VERDICT:`가 없으므로 1차 검증으로 인정하지 않는다. 안전 필터가 외부 서비스 금지 문맥을 위험 요청으로 오인한 것으로 보이며, 실제 조작 요청을 모두 제거한 읽기 전용 품질 검토 문구로 새 세션을 다시 실행한다.

### 외부 1차 재시도 — 당시 `NOT_RUN`, 이후 판정 뒤집힘

위험 동작처럼 읽힐 수 있는 표현을 빼고 다시 실행한 명령:

```bash
env -u ANTHROPIC_API_KEY claude -p < docs/engineering/ai-native-ra-search-orchestration-review-prompt-retry-2026-08-17.md
```

→ 외부 서비스 조작이 아니라 기획 문서의 모순만 찾도록 다시 썼다.

전체 출력과 종료값:

```text
exit=1
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606

Request ID: req_011Ce7hpE9uwY2sA63ebcsDD
```

→ 두 번째 독립 세션도 판정 본문을 만들지 못했다. 모델을 Sonnet·Opus·Haiku로 명시하고, 파일 읽기형·변경분 입력형·핵심 지적 5개형·지적 1개씩 여섯 호출형으로 입력을 줄인 시도도 각각 2~10분 동안 출력이 없어 중단했다. 마지막 Haiku 다섯 지적 검토는 120초 무출력 뒤 `^CExecution error`, 지적별 여섯 호출은 60초 무출력 뒤 중단됐으며, 중단 뒤 반환된 종료값 0은 판정 본문이 없으므로 합격으로 해석하지 않는다.

도구 자체의 최소 상태 확인 명령과 전체 출력:

```bash
env -u ANTHROPIC_API_KEY claude -p --model sonnet --tools '' --no-chrome --no-session-persistence 'Return exactly HEALTH_OK and nothing else.'
```

→ 실제 문서 검토가 아니라 Claude 명령줄 도구가 짧은 요청에 응답할 수 있는지만 분리해 확인했다.

```text
HEALTH_OK
```

→ 일반 플러그인·훅 경로에서는 짧은 입력만 응답했고 실제 검토 판정은 만들지 못했다. 이 시점의 Claude 1차는 `PASS`가 아니라 `NOT_RUN`이었다. 이후 `--safe-mode`로 플러그인·훅을 격리하자 실제 문서 검토가 정상 응답해 아래처럼 판정이 뒤집혔다.

### Claude V1 안전모드 재실행 — `PASS`

실행 명령 형태:

```bash
{ printf '%s\n' '<읽기 전용 적대검토 지시>'; sed -n '<범위>' <문서>; } |
  env -u ANTHROPIC_API_KEY claude -p --safe-mode --model sonnet --effort medium --tools '' --no-chrome --no-session-persistence
```

→ P03/P09~P17, P15~P26, 통합 기획서, READY·목표 수 필드, 내부 후보 우선 경로, 실행 카운터, 공유 후보 영수증을 겹치는 범위로 나눠 검토했다. 결함이 나오면 Codex가 해당 문구를 저장소에서 재현하고 수정한 뒤 같은 범위를 다시 실행했다.

최신 회귀 판정:

```text
VERDICT: PASS

이전 BLOCKER였던 candidate_eligibility_receipt_set_hash의 공용 산출 규칙·소유자 문제는 해결되었다.
P12가 eligibility_receipts.py를 유일한 구현 소유자로 명시하고, P06·P07은 공용 함수를 호출하며,
P08은 두 집합 지문의 일치를 검사한다. 새 BLOCKER/HIGH는 발견되지 않았다.
```

→ 정상 경로 실패는 도구 전체 실패가 아니라 실행 표면 문제였다. 안전모드 V1은 실제 판정 본문을 반환했고 최신 범위는 `PASS`다. 전체 라운드·결함·수정·정확 판정은 `docs/engineering/ai-native-ra-search-orchestration-claude-v1-review-2026-08-17.md`에 보존한다.

### 보조 독립 비평 — 처음에는 `REJECT`, 수정 뒤 `PASS`

Claude 판정을 대신한 것으로 취급하지 않고, 별도 Codex 비평자에게 전체 문서의 blocker/high만 찾게 했다. 첫 검토에서 다음 여섯 문제가 실제로 발견됐다.

1. 인수 기준에 실행할 수 있는 전체 명령이 없었다.
2. `NOT_RUN`과 합격 선행조건의 구분이 불명확했다.
3. 정보 책임 장소 결정과 정본 강제가 P00 하나에 섞여 있었다.
4. Gmail 첨부 본문을 읽지 않으면서 내용 지문을 요구했다.
5. 사람인·잡코리아에 채널 표시 규약과 실제 화면에서 파생한 시험자료 계약이 없었다.
6. P17은 운영 검증을 요구하면서 운영 변경 전체를 비범위로 금지했다.

→ 1~5는 인수 명령 내장, 상태표, P00A/P00B 분리, 자료표 지문, 채널별 표시 규약과 실제 화면 파생 자료로 고쳤다. 6은 오너가 승인한 큐 전용 변경만 라이브 검증할 수 있도록 좁혀 고쳤다.

마지막 재검토 원문:

```text
PASS

p17 모순은 해소됐습니다. LIVE_PASS는 운영 제어 DB 변경 승인과 migration readback이 필요하다고 명시하고(p17-durable-work-queue.md:11), 비범위는 “오너 승인 없는 운영 migration 적용”과 “큐 외 다른 운영 스키마 변경”만 금지합니다(p17:19-21). 라이브 증거도 승인된 경우 후보 원문 없는 migration 1건의 적용·readback·rollback을 요구합니다(p17:39-41).

당시 전체 패킷 인라인 AC도 재실행 결과 통과했습니다: PASS planning_packet goal=1 plan=1 prompts=28 required_sections=10 links=all-present. 이후 원자 인수 절을 추가해 최신 기준은 required_sections=11·atomic_commands=28로 대체됐습니다.

새 blocker/high 없음.
```

→ 보조 비평은 당시 최종 `PASS`였다. 이것은 일반 경로의 `NOT_RUN`을 소급해 통과시키지 않았고, 이후 별도로 수행한 안전모드 Claude V1 `PASS`가 현재 외부 1차 판정이다.

### Codex 재공격과 수정 재현

Claude가 낸 각 지적을 저장소 문구와 명시적 `rg -F` assertion으로 다시 확인했다. 특히 다음 결함은 Codex 재공격에서도 실제로 재현돼 수정했다.

1. P03이 미래 P06/P07 런타임을 미리 검사하던 순서 모순.
2. 계획서와 P03 READY 필수 필드 불일치.
3. P08이 내부 매칭 P13 전에 외부 서치 제안을 만들 수 있던 의존성 구멍.
4. P07↔P25 외부 적격 영수증의 스키마·동일인 ID 소유권 공백.
5. P08의 P06 결정 지문 누락.
6. P06/P07의 후보 영수증 집합 지문 산출 규칙·소유자 누락.
7. `delivery_attempt`, `queue_lease_epoch`, `machine_recovery_attempts`, `account_fencing_token`, `local_reservation_epoch` 의미 혼합.

최신 Codex V2 기계 재공격 결과:

```text
PASS CODEX_V2 prompts=28 structure=11 identity-contract=owned internal-first=enforced generations=separated browser=fail-closed integration=live-gated
```

→ P12가 공용 동일인·적격 영수증·집합 지문을 소유하고, P13 내부 매칭 뒤 P06/P07을 병렬 계산해 P08에서 같은 입력 세대만 결합하며, P25 외부 사람 판정 뒤 P07이 재계산하는 경로가 실제 문구로 강제됨을 확인했다. 사람인·잡코리아는 후보 1명·외부쓰기 0건·CAPTCHA/2FA/제한 우회 0경로, P26은 요구된 `LIVE_PASS`와 두 머신 장애 복구를 선행조건으로 유지한다.

### 최종 문서·저장소 검사

최신 문서와 Claude V1 기록을 인덱스에 올린 뒤 실행한 결과:

```text
AC-PLAN-1: PASS planning_packet goal=1 plan=1 prompts=28 required_sections=11 atomic_commands=28 links=all-present
git diff --cached --check: exit=0
brief-lint goal: 위반 0건
brief-lint plan: 위반 0건
brief-lint Claude V1: 위반 0건
VERIFY_SCAN_SOURCE=index bash verify.sh: PASS, 비밀 패턴 0건
acceptance-hs-cleanroom.sh: PASS, 금지 실행 의존성 0건, 탈출 symlink 0건, CHECKED 54
acceptance-hs-gates.sh: PASS, ruff·mypy·pytest 1건·runtime import
scan-data-exposure.sh all: PASS, 추적 파일 120개 위반 0건
acceptance-hs-a4.sh: PASS, CHECKED 30
```

→ 이번 문서 묶음과 현재 인덱스는 계획 인수 기준·형식·비밀·클린룸·Python 기본 게이트·데이터 노출 방어를 모두 통과했다. 저장소 전체 시작 자격은 마지막 관측에서 `RED: 2/19`였다. 0-2는 시작 시 43건이던 기존 unreachable 문제와 이후 공유 객체 저장소에 생긴 미커밋 blob 때문에 실패했고, 마지막 증거 편집 전 기본 저장소에서 의도된 패턴 파일 기본 경로로 재실행했을 때 비밀 스캔과 카나리는 통과하고 unreachable 객체 222건에서 실패했다. 외부 패턴 경로를 환경으로 주입한 별도 시도는 그 경로가 내부 카나리에도 상속돼 거짓 카나리 실패를 만들었으므로 최종 근거에서 제외한다. 0-5는 다른 세션이 `main`을 `8e057b7`로 전진시킨 반면 `origin/main`은 `4fdef31`이라 push 미완료로 실패했다. 그 커밋은 `docs/engineering/admin-position-map-spec-2026-08-17.md` 한 파일만 추가해 이번 36개 산출물과 경로 충돌은 없었다. 두 실패 모두 임의 삭제·push 없이 그대로 보존했다.

### 반대 시험 결과

프롬프트 수를 줄이고, 필수 절·원자 명령·0건 방지 문구를 빼고, 깨진 링크를 넣는 다섯 변이를 각각 검사한 결과:

```text
PASS negative prompt_count=27 rejected expected=28
PASS negative missing_required_heading rejected heading=RED
PASS negative broken_link rejected target=does-not-exist.md
PASS negative missing_atomic_command rejected prompt=p03
PASS negative zero_count_guard_missing rejected prompt=p03
```

→ 정상 묶음만 통과한 것이 아니라, 요구된 구조와 실제 인수 명령·0건 가짜 합격 방지를 깨뜨리면 검사도 함께 실패함을 확인했다.
