# codeitsearch 이어받기 검토 — codex V1 판정 원문 (2026-09-30)

호출: `codex exec -s read-only -C <worktree> -o verdict.md <prompt>` (codex-cli 0.155.1). 원문을 수정 없이 보존한다.

## 1차 — 대상 0f83c64 (sha256 ecf62904bef86993)

VERDICT: FAIL

## 결론

현재 변경은 그대로 병합하기 어렵습니다. 실제 입력으로 확인한 결과, **서로 다른 학교를 명문대로 판정**하고, 회사 정보가 어긋난 채용 자료에 **다른 회사의 공고 주소를 붙이며**, 이전 실행분이 아닌 행도 **삭제 대상으로 고릅니다**. 인증이 막힌 검색을 후보가 0명인 검색처럼 보고하는 경로도 남아 있습니다.

**건너뜀·미확인·재시도:** 요청하신 `python3 -m pytest -q tests`는 pytest가 없어 종료값 1로 끝났습니다. 기존 가상환경으로 재시도한 결과 139개가 통과했고, 8개는 읽기 전용 환경에서 임시 파일을 만들 수 없어 준비 단계에서 오류가 났습니다. 실제 Supabase 쓰기·삭제, 사람인 검색, 메일 발송은 실행하지 않았습니다. 아래 삭제 결과는 **실제 `main()` 함수에 모의 DB 응답을 넣어 얻은 요청**이며, 운영 DB에서 삭제가 일어났다는 주장이 아닙니다. 코드 읽기만으로 내린 결함 판정은 없습니다.

## 판단 근거

- **선택한 해석:** 학교명은 계약에 적힌 *학교*와 일치해야 하고, `#run-`으로 식별되는 이전 적재분만 정리해야 합니다. 인증 차단은 검색을 마쳐 후보 0명을 얻은 상태와 다릅니다. 이는 각각 학교 계약, 적재 코드의 설명, [재개 목표 문서](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/docs/engineering/goal-prompts/codeitsearch-minfix-resume-2026-09-28.md:27)에 근거합니다.
- **버린 해석:** 시험한 입력이 모두 정상 운영 자료라는 가정은 하지 않았습니다. 회사 정보 충돌과 날짜 뒤에 `-archive`가 붙은 출처는 **경계 입력**입니다. 다만 현재 함수가 이 입력을 거부하지 않고 적재·삭제 요청을 만드는지는 재현됩니다.
- **이 판단이 틀리면 깨지는 것:** 별도 학교인 Berkeley College까지 UC Berkeley와 같은 점수를 주기로 의도했다면 학교 결함 판정은 달라집니다. 그러나 두 기관은 각각 [Berkeley College](https://berkeleycollege.edu/about/at-a-glance/index.html)와 [UC Berkeley](https://www.berkeley.edu/)가 명시하는 별도 학교이며, 기존 테스트도 `Berkeley College Woodland Park`를 명문대에서 제외합니다.

## 기술 상세와 증거 원문

### 1. MAJOR — “Berkeley College가 세계 명문대로 올라갑니다”

**위치·역할:** [학교 계약:84](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/contracts/humansearch/in-seoul-universities.json:84)은 `Berkeley`를 명문대 항목으로 두고, [학교 계약:108](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/contracts/humansearch/in-seoul-universities.json:108)은 뒤따르는 `college`를 허용합니다. [scoring.py:168](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/scoring.py:168)은 남은 단어가 모두 허용 목록에 있으면 일치시킵니다.

**원인:** 4차 수정의 허용 단어 규칙이 정식 명칭을 살리는 동시에, 별도 학교 이름도 통과시킵니다. `school_tier()`로 분류하고 `score()`로 등록 판정까지 실행했습니다. 다음은 동일한 경력·키워드 입력에서 학교만 바꾼 원문입니다.

```text
'Berkeley College'                  -> school_25=25, total=65, eligible=True
'Berkeley College Woodland Park'    -> school_25=10, total=50, eligible=False
'University of California, Berkeley'-> school_25=25, total=65, eligible=True
```

→ 해석: Berkeley College의 기대값은 `other`, 학력 10점, 총점 50점, 등록 제외입니다. 현재는 15점이 더해져 등록됩니다. [기존 테스트:139](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/tests/test_scoring.py:139)은 지명이 붙은 이름만 막아 이 짧은 정식 학교명을 놓칩니다. **사업 영향:** 후보의 학력과 등록 여부가 잘못 보고됩니다.

### 2. MAJOR — “회사 정보가 어긋나면 다른 회사의 공고 주소가 적재됩니다”

**위치·역할:** [ingest_positions.py:68](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:68)은 `company_key`로 등록 정보를 고르지만, [같은 파일:66](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:66)의 회사명과 [같은 파일:64](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:64)의 플랫폼은 입력값을 그대로 받습니다. [같은 파일:90](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:90)은 선택된 등록 정보로 상세 주소를 만듭니다.

**재현 입력:** 뤼튼의 출처·회사명·플랫폼·`posting_id="abc"`를 유지하고 `company_key`만 `codeit`으로 바꿔 `build_rows()`를 호출했습니다.

```text
정상 입력:
{"company":"뤼튼테크놀로지스","company_norm":"wrtn",
 "platform":"wrtn_careers","url":null}

company_key="codeit":
{"company":"뤼튼테크놀로지스","company_norm":"codeit",
 "platform":"wrtn_careers","url":"https://careers.codeit.com/c/abc"}
```

→ 해석: 기대 출력은 정보 불일치 오류입니다. 현재는 뤼튼 행에 코드잇 주소와 회사 식별값을 붙입니다. 회사명만 `코드잇`으로 바꾸거나 플랫폼만 `codeit_careers`로 바꾼 입력도 각각 불일치 상태로 통과했습니다. [기존 테스트:52](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/tests/test_ingest_positions.py:52)는 서로 일치하는 뤼튼 값만 시험합니다. **사업 영향:** 공고 링크와 회사별 집계가 오염되고, 이후 회사별 검색의 출발점이 틀어집니다.

### 3. MAJOR — “이전 실행분이 아닌 행까지 삭제 대상으로 고릅니다”

여기서 *접두사*는 `source_file` 앞부분인 `codeitsearch/recruit/2026-09-28`을 뜻합니다. [ingest_positions.py:195](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:195)은 회사 식별값을 확인하지만, [같은 파일:198](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:198)은 이전 실행 표지 `#run-` 없이 접두사 일치만 확인합니다. [같은 파일:204](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:204)이 고른 ID로 삭제를 요청합니다. 요약 행도 [같은 파일:212](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:212)에서 같은 방식으로 골라집니다.

**재현 입력:** 같은 날짜·플랫폼 조회 결과에 이전 실행 `id=1`, 다른 회사 `id=2`, 같은 회사의 별도 보관 출처 `id=3`을 넣었습니다. `main()`에 모의 조회·삽입·삭제 함수를 연결해 실제 호출을 기록했습니다.

```text
id=1 source_file=codeitsearch/recruit/2026-09-28#run-OLD
id=2 source_file=codeitsearch/recruit/2026-09-28#run-FOREIGN company_norm=someoneelse
id=3 source_file=codeitsearch/recruit/2026-09-28-archive company_norm=codeit

main() -> 0
DELETE jobmarket_positions:
  platform=eq.codeit_careers, snapshot_date=eq.2026-09-28, id=in.(1,3)
DELETE jobmarket_snapshots:
  source_file=eq.codeitsearch/recruit/2026-09-28-archive
```

→ 해석: 기대 삭제 대상은 `id=1`뿐입니다. ID 기반 삭제 덕분에 `id=2`는 보호됐지만, `id=3`과 그 요약 행은 보호되지 않았습니다. **사업 영향:** 같은 회사·날짜의 별도 보관 자료가 정리 과정에서 지워질 수 있습니다. 이는 모의 DB 재현이므로 실제 운영 자료에 해당 출처가 있는지는 미확인입니다.

### 4. MAJOR — “인증 차단이 후보 0명 보고서로 바뀝니다”

**위치·역할:** [compose_mail.py:153](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/compose_mail.py:153)은 결과를 받지만 검색 상태를 검사하지 않고, [같은 파일:188](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/compose_mail.py:188)은 빈 후보 목록을 곧바로 0명 문구로 바꿉니다. [page_trace.py:106](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/page_trace.py:106)은 `blocked` 상태를 기록할 수 있습니다.

**재현 입력과 출력:** `compose()`에 `status="blocked"`, `error="사람인 기업회원 미인증"`, `candidates=[]`를 넣었습니다.

```text
subject: [aisearch]Claude-win 코드잇 – 백엔드 개발자 – 0 candidates
body:    - 이번 실행에서 등록 문턱(60점)을 넘은 후보 없음.
         - 사유: 사유 미기재
```

→ 해석: 기대 동작은 보고서 생성을 거부하거나 인증 차단을 명시하는 것입니다. 현재 출력은 검색을 완료했다는 잘못된 인상을 줍니다. [기존 테스트:86](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/tests/test_compose_mail.py:86)는 오히려 인증 차단 사유가 든 0명 보고서를 기대합니다. **사업 영향:** 검색하지 못한 포지션을 후보가 없는 포지션으로 오판할 수 있습니다.

### 5. MAJOR — “다른 회사의 직무명이 검색어 없이 적재될 수 있습니다”

**위치·역할:** [segmentation.py:95](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/segmentation.py:95)은 정해진 한국어 직무명만 분류하고, [같은 파일:107](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/segmentation.py:107)은 나머지를 `unsegmented`로 둡니다. [keywords.py:246](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/keywords.py:246)의 해당 검색어는 비어 있습니다. [ingest_positions.py:85](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:85)은 그 상태를 거부하지 않고 적재 행을 만듭니다.

```text
job="소프트웨어 엔지니어링" -> segment=software_engineering, searchable=True, query_terms=다수
job="Software Engineering" -> segment=unsegmented, searchable=True, query_terms=[]
뤼튼 build_rows()              -> keyword=null, core_keywords_json=[], searchable=True
```

→ 해석: 영어 직무명이 잘못된 분류라는 뜻은 아닙니다. **검색 대상이라고 표시하면서 검색어 0개인 행을 통과시키는 것**이 결함입니다. 기대 동작은 적재 전 직무 매핑을 요구하거나 검색 불가 상태를 분명히 표시하는 것입니다. [기존 테스트:78](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/tests/test_segmentation.py:78)는 코드잇 스냅샷에서 나온 직무만 검사합니다. **사업 영향:** 다른 회사 공고는 저장되어도 후보 검색에서 조용히 빠질 수 있습니다.

### 6. MINOR — “전문학사의 영어 학위명 한 종류가 제외되지 않습니다”

**위치·역할:** [학교 계약:145](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/contracts/humansearch/in-seoul-universities.json:145)은 `Associate Degree` 형태만 표지로 두고, [scoring.py:251](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/scoring.py:251)은 학위명에 그 표지가 있는지 검사합니다.

```text
degree="경영전문대학원 석사" -> hard_exclude_reason=None
degree="전문학사"           -> hard_exclude_reason=two_year_college
degree="Associate Degree"   -> hard_exclude_reason=two_year_college
degree="Associate of Science" -> hard_exclude_reason=None, total=82, eligible=True
degree="Associate of Arts"    -> hard_exclude_reason=None, total=82, eligible=True
```

→ 해석: 전문대학원 예외는 유지됐습니다. 반면 두 Associate 학위 표기의 기대 출력은 사람인 채널에서 `two_year_college` 제외입니다. 실제 학위 표기라는 점은 [Berkeley College의 학위 안내](https://berkeleycollege.edu/about/at-a-glance/index.html)에서도 확인됩니다. **사업 영향:** 전문학사 후보가 학교명에 별도 표지가 없으면 등록될 수 있습니다.

## 깨지지 않은 영역과 검증 한계

직접 호출에서 `University of California, Berkeley`, `Harvard Medical School`, `MIT Sloan School of Management`는 `world_top`으로 남았습니다. `University of Michigan-Flint`와 `University of California, Merced`는 `other`였습니다. `연세대학교 국제캠퍼스`는 `other`, `연세대학교 신촌캠퍼스`는 `in_seoul`, `서울대학교 경영전문대학원`은 `in_seoul`, `영진전문대학`은 `two_year`였습니다. 일치하는 뤼튼 입력은 코드잇 주소 없이 만들어졌고, 위 삭제 재현에서는 다른 회사의 `id=2`가 삭제 요청에서 빠졌습니다. → 해석: 이전 수정 전체가 되돌아간 것은 아니며, 위 결함은 그 주변 경계에서 재현됩니다.

```text
요청 명령: python3 -m pytest -q tests
종료값 1: No module named pytest

기존 가상환경 재시도, 종료값 1:
139 passed, 8 errors in 0.39s
8 errors: No usable temporary directory found
```

→ 해석: 8건은 테스트 준비용 임시 파일을 만들 수 없는 환경 오류입니다. 전체 테스트 성공을 주장할 수 없고, 실제 DB·브라우저·메일까지 검증한 결과로도 볼 수 없습니다. 검토 전후 HEAD는 `0f83c64d964f6d0df17699f3dc9fa70903b30414`, 작업공간은 변경 없음으로 확인했습니다.

**수정 방향을 설계로 정리하면:**

무엇을: 학교의 정식 명칭과 허용 부속 명칭을 구분하고, 적재 시 회사 정보·검색어·이전 실행 표지를 검증합니다.  
왜: 현재 경계 입력이 점수 상승, 잘못된 주소, 검색 누락, 삭제 요청으로 이어집니다.  
버린 길: `college` 같은 일반 단어를 더 허용하거나 접두사 일치만 넓히는 방식은 같은 반례를 다시 만듭니다.  
대가: 새 학교·직무·출처 형식은 명시적으로 등록하거나 오류를 처리해야 합니다.  
되돌리기: 계약 항목과 입력 검증을 작은 변경으로 분리하면 해당 규칙만 되돌릴 수 있습니다.
## 2차 — 대상 415260a (sha256 47ce832a1fbf464e)

VERDICT: FAIL

## 결론

HEAD `415260a`의 수정은 학교 표기와 적재 처리의 상당 부분을 고쳤지만, **별개 학교를 명문대로 올리고 실제 4년제 학력자를 제외하는 오판**이 남아 있습니다. 사유가 공백뿐인 후보 0명 메일도 통과합니다. 현재 코드는 병합 전 수정이 필요합니다.

판정 전에 검증 한계를 밝힙니다. 지정하신 `uv` 시험은 읽기 전용 환경의 캐시 접근 오류로 **종료값 2**였고, 시스템 `python3`에는 `pytest`가 없어 대체 실행도 실패했습니다. 함수 직접 호출은 재시도해 성공했습니다. 실제 Supabase 연결·메일 발송·포털 실검색·원격 검사는 수행하지 않았습니다. 포털에 아래의 공격용 영문 확장 표기가 실제 존재하는지는 미확인입니다. 검토 전후 HEAD는 `415260a`이고 작업 파일 변경은 0개입니다.

## 판단 근거

선택한 해석은 **학교 이름보다 명시된 학력과 학교의 실제 학위 과정을 우선 확인해야 한다**는 것입니다. 목표 문서의 “서울 소재 전문대 이름” 규칙을 학위와 무관한 무조건 제외로 읽는 해석은 버렸습니다. 서울여자간호대학교는 [공식 모집요강](https://www.snjc.ac.kr/public_2017/process/file_download.jsp?fileName=%ED%8E%B8%EC%9E%85%ED%95%99+%EB%AA%A8%EC%A7%91%EC%9A%94%EA%B0%95.pdf)에 4년제 간호학과 승격을 명시합니다. 버린 해석이 맞다면 이 결함 판정은 달라지지만, 명시적으로 4년제 졸업인 후보까지 제외해도 된다는 사업 규칙이 필요합니다.

| 기준 | 판정 | 직접 확인한 핵심 |
|---|---|---|
| AC-1 | 충족 | 명문대 하위 기관 표기 15개 모두 `world_top` |
| AC-2 | **불충족·MAJOR** | 별개 학교의 확장 표기가 `world_top` |
| AC-3 | 지정 사례 충족, 새 오판 **MINOR** | 분교 16개는 `other`; 서울 학교의 일반 괄호 표기도 내려감 |
| AC-4 | **불충족·MAJOR** | 전문대 표기는 잡지만 명시적 4년제 학력도 하드제외 |
| AC-5 | 충족 | 정상 스냅샷 62행 생성; 회사·플랫폼 불일치 거부 |
| AC-6 | 충족 | 이전 `#run-` 행만 모의 삭제; 보관·무표지 행 보존 |
| AC-7 | 충족 | 검색어 없는 검색 대상에서 모의 DB 호출 0회, 반환 1 |
| AC-8 | **불충족·MAJOR** | 사유가 공백뿐이어도 후보 0명 메일 생성 |

→ 해석: 테스트 목록의 정상 사례만으로는 AC-2·AC-4·AC-8의 경계 입력을 막았다고 볼 수 없습니다. AC-5~AC-7에서는 요청하신 정상 스냅샷과 이전 실행분을 막는 회귀를 재현하지 못했습니다.

## 기술 상세와 증거 원문

### 재현된 결함

**MAJOR — “별개 학교의 확장 표기가 명문대로 승격”**  
원문 제목: AC-2, “이름만 겹치는 별개 학교이면 `other`”. [계약의 `tech` 허용어](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/contracts/humansearch/in-seoul-universities.json:129)와 [정확한 전체 이름만 거부한 뒤 명문대 판정하는 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/scoring.py:207)이 원인입니다. `world_top`은 명문대 등급입니다. 사업 영향은 별개 학교 후보의 학력 점수 과대평가입니다. 확장 표기의 포털 실재 여부는 미확인이나, **이전 `other`에서 현재 `world_top`으로 바뀐 함수 오판**은 재현됐습니다.

```text
school_tier("Berkeley College", 이전 계약)       → world_top
school_tier("Berkeley College", 현재 계약)       → other
school_tier("Berkeley College Tech", 이전 계약)  → other
school_tier("Berkeley College Tech", 현재 계약)  → world_top
school_tier("Cornell College Tech", 이전 계약)   → other
school_tier("Cornell College Tech", 현재 계약)   → world_top
school_tier("UC Berkeley College of Engineering", 현재 계약) → world_top
```

→ 해석: 단독 이름 차단과 UC Berkeley 소속 기관 보존은 성공했습니다. 그러나 새 허용어가 붙으면 별개 학교의 기대 출력 `other`를 지키지 못합니다. 기존 허용어만으로도 `Berkeley College School of Business`는 `world_top`이어서, 정확 일치 목록만으로는 AC-2 전체를 보증하지 못합니다.

**MAJOR — “4년제 졸업자를 전문대 학력으로 하드제외”**  
원문 제목: AC-4의 counter-AC, “4년제·대학원을 하드제외하지 않음”. [학교 이름 표지](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/contracts/humansearch/in-seoul-universities.json:168)를 [학력보다 먼저 `two_year`로 판정하는 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/scoring.py:193)과 [하드제외 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/scoring.py:268)이 원인입니다. `two_year_college`는 후보를 검색 결과에서 강제로 빼는 사유입니다. 서울여자간호대학교의 4년제 과정은 [학교 공식 자료](https://www.snjc.ac.kr/public_2017/process/file_download.jsp?fileName=%ED%8E%B8%EC%9E%85%ED%95%99+%EB%AA%A8%EC%A7%91%EC%9A%94%EA%B0%95.pdf)로 확인됩니다. 사업 영향은 적격 4년제 학사 후보의 누락입니다.

```text
score(학교="서울여자간호대학교", 학력="대학교(4년) (졸업)", 채널="saramin")
→ (hard_exclude_reason="two_year_college", eligible=False, school_25=0)
기대 → hard_exclude_reason=None

score(학교="한양여자대학교", 학력="대학교(4년) (졸업)", 채널="saramin")
→ ("two_year_college", False, 0)
기대 → hard_exclude_reason=None

score(학교="서울예술대학교", 학력="대학교(4년) (졸업)", 채널="saramin")
→ (None, True, 10)

score(학교="부산대학교", 학력="경영전문대학원 석사", 채널="saramin")
→ (None, True, 10)
```

→ 해석: 일반 대학의 대학원과 서울예대 4년제 예외는 보존됐습니다. 새로 이름 표지를 넣은 학교에서는 학력 필드가 명시적으로 4년제여도 기대 출력인 “하드제외 없음”이 나오지 않습니다. 한양여자대학교도 [공식 안내](https://www.hywoman.ac.kr/resources/PV/guide_book_2019.pdf)에 4년제 학사학위 취득 과정을 명시합니다.

**MAJOR — “공백 사유로 후보 0명 보고 허용”**  
원문 제목: AC-8, “후보 0명 보고에 사유가 없으면 거부”. [메일의 참·거짓 검사 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/compose_mail.py:159)은 공백 문자열을 사유로 인정합니다. 사업 영향은 검색 결과가 없는 이유를 밝히지 않은 메일이 정상 보고처럼 만들어지는 것입니다.

```text
compose({"company":"코드잇","position":"백엔드","candidates":[],
         "no_candidate_reason":"   "})
→ subject: '[aisearch]Claude-win 코드잇 – 백엔드 – 0 candidates'
→ body 후보 부분: '## 후보\n- 이번 실행에서 등록 문턱(60점)을 넘은 후보 없음.\n- 사유:    '
기대 → ValueError
```

→ 해석: `None`·빈 문자열 거부 시험은 통과하더라도, 내용이 없는 공백 문자열은 같은 요구를 우회합니다.

**MINOR — “분교 표지가 다른 서울 학교의 괄호 표기까지 내림”**  
원문 제목: AC-3의 counter-AC, “괄호가 붙은 모든 이름을 `other`로 내리지 않음”. [학교 구분 없이 검사하는 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/scoring.py:146)과 [전역 괄호 표지](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/contracts/humansearch/in-seoul-universities.json:221)이 원인입니다. 사업 영향은 해당 표기가 들어온 서울 학교 후보의 학력 점수 하락입니다. 이 정확한 괄호 표기의 포털 사용 빈도는 미확인입니다.

```text
school_tier("서울대학교(자연)", 이전 계약)     → in_seoul
school_tier("서울대학교(자연)", 현재 계약)     → other
school_tier("연세대학교(국제)", 이전 계약)     → in_seoul
school_tier("연세대학교(국제)", 현재 계약)     → other
school_tier("고려대학교(세종)", 현재 계약)     → other
school_tier("한양대학교(서울)", 현재 계약)     → in_seoul
```

→ 해석: 목표로 한 고려대 세종 표기는 내려갔습니다. 같은 문자열 규칙이 다른 대학의 일반 표기에도 적용되므로, 학교와 캠퍼스의 짝을 확인하지 못합니다.

설계 지적:  
무엇을: 별개 학교 거부와 분교 표지는 학교별 이름·캠퍼스 조합으로 묶고, 전문대 이름 표지는 명시적 4년제 학력과 함께 판정하며, 메일 사유는 공백 제거 후 검사하십시오.  
왜: 현재 규칙은 각각 전역 허용어, 전역 괄호 표지, 학교명 우선 하드제외, 문자열의 참·거짓 값에 의존합니다.  
버린 길: 허용어를 더 추가하거나 정확 일치 거부 목록만 늘리는 방식은 새 확장 표기를 다시 열 수 있습니다.  
대가: 계약에 학교별 예외와 학력 우선순위를 명시하고 그 조합을 시험해야 합니다.  
되돌리기: 변경 범위를 계약 JSON과 해당 판정·메일 함수로 제한하면 각 규칙을 독립적으로 되돌릴 수 있습니다.

### 통과한 경계와 반증 기록

아래는 `python3 -B -c`에서 **현재 `load_school_contract()`와 실제 `school_tier()`**를 호출한 출력입니다. AC-1의 15개와 AC-3의 16개를 전부 넣었습니다.

```text
AC1 [('UC Berkeley', 'world_top'), ('U.C. Berkeley', 'world_top'),
('Berkeley Haas', 'world_top'), ('UC Berkeley Haas School of Business', 'world_top'),
('Haas School of Business, UC Berkeley', 'world_top'), ('UCLA Anderson', 'world_top'),
('UCLA Anderson School of Management', 'world_top'),
('UCLA Samueli School of Engineering', 'world_top'), ('Stanford GSB', 'world_top'),
('Harvard Kennedy School', 'world_top'), ('Cornell Tech', 'world_top'),
('University of Michigan, Ann Arbor', 'world_top'),
('University of Michigan Ross School of Business', 'world_top'),
('Said Business School, University of Oxford', 'world_top'),
('Judge Business School, University of Cambridge', 'world_top')]
AC3 [('한국외국어대학교(용인)', 'other'), ('한국외국어대학교(글로벌)', 'other'),
('연세대학교(원주)', 'other'), ('연세대학교(미래)', 'other'),
('고려대학교(세종)', 'other'), ('홍익대학교(세종)', 'other'),
('중앙대학교(안성)', 'other'), ('경희대학교(국제)', 'other'),
('경희대학교(수원)', 'other'), ('성균관대학교(자연과학)', 'other'),
('명지대학교(자연)', 'other'), ('명지대학교(용인)', 'other'),
('상명대학교(천안)', 'other'), ('동국대학교(경주)', 'other'),
('건국대학교(충주)', 'other'), ('한양대학교(안산)', 'other')]
```

→ 해석: 명문대 하위 기관의 누락과 지정된 분교 표지의 미차단을 깨려 했으나 재현되지 않았습니다. `University of Michigan-Flint`, `University of California, Merced`, `University of Toronto Mississauga`도 각각 `other`여서, 확인한 지명 우회는 열리지 않았습니다.

AC-4 이름 표지 8개와 학력 경계는 `school_tier()`·`score()`로 호출했습니다.

```text
school_tier: 삼육보건대학(2,3년)→two_year
서강정보대학(2,3년)→two_year
한양여자대학(2,3년)→two_year
한양여자대학교→two_year
삼육보건대학교→two_year
서강정보대학교→two_year
서울여자간호대학교→two_year
서울예술대학교(2,3년)→two_year

score: 부산대학교 + 초대졸 + saramin→two_year_college
부산대학교 + 대학(2,3년) + saramin→two_year_college
부산대학교 + 경영전문대학원 석사 + saramin→하드제외 없음
서울대학교 경영전문대학원→in_seoul
서울예술대학교(4년)→other
```

→ 해석: `2,3년`·`초대졸` 누락, 일반 대학원 오차단, 서울예대 이름만으로의 제외를 각각 깨려 했으나 재현되지 않았습니다. 위의 4년제 학교 결함은 이 정상 사례들 사이에서 발견됐습니다.

**AC-5: 실제 스냅샷을 `build_rows()`에 전달한 결과**

```text
입력 헤더 {'company_key':'codeit','company':'코드잇',
'platform':'codeit_careers','source':'https://careers.codeit.com/recruit',
'snapshot_date':'2026-09-28'}
positions 62
normal rows 62 searchable 15 unmapped []
first_source codeitsearch/recruit/2026-09-28#run-PROBE
wrong_company ValueError snapshot disagrees with registry entry 'codeit'
wrong_platform ValueError snapshot disagrees with registry entry 'codeit'
wrong_key ValueError snapshot disagrees with registry entry 'wrtn'
english_name rows 62 searchable 15 unmapped []
```

→ 해석: [레지스트리 대조 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:68)은 저장소의 정상 코드잇 스냅샷과 허용된 영문 회사명을 막지 않았고, 회사명·플랫폼·키의 불일치는 각각 행 생성 전에 거부했습니다.

**AC-6: `main()`의 `select`·`insert`·`delete`를 메모리 함수로 바꾼 호출**입니다. 이전 포지션 입력은 같은 회사의 `#run-OLD`, `-archive`, 무표지, 다른 회사의 `#run-OTHER` 각 1행이고, 요약 입력은 앞의 세 종류입니다.

```text
positions 62
searchable 15
wrote 62 rows, verified 62, then removed 1 from earlier runs
main_return 0
calls [
 ('insert','jobmarket_positions',62),
 ('insert','jobmarket_snapshots',1),
 ('delete','jobmarket_positions',
  {'platform':'eq.codeit_careers','snapshot_date':'eq.2026-09-28','id':'in.(1)'}),
 ('delete','jobmarket_snapshots',
  {'snapshot_date':'eq.2026-09-28',
   'source_file':'eq.codeitsearch/recruit/2026-09-28#run-OLD'})
]
```

→ 해석: [포지션·요약 정리 조건](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:215)은 정상 이전 `#run-` 실행분을 지우고 보관·무표지·다른 회사 행은 보존했습니다. 기준 커밋의 생성 코드도 이미 `#run-` 접미사를 썼으므로 정상 이전 실행분이 새 조건 때문에 남는 회귀는 확인되지 않았습니다. 실제 DB 삭제 결과는 확인하지 않았습니다.

**AC-7: 원본 스냅샷의 검색 대상 공고 한 건에서 직무만 미매핑 값으로 바꾸고, 모든 DB 함수를 호출 시 오류를 내는 함수로 교체한 `main()` 호출**

```text
chosen 1 '기업교육 어카운트 매니저' '교육 운영'
old_core ['교육 운영', '교육 기획', '교육 매니저', '과정 운영',
          '프로그램 매니저', '부트캠프 운영', '러닝 매니저',
          'Education Operations', 'Program Manager', 'Training Operations']
new_core []
searchable postings without keywords — map these jobs in keywords.py first:
['Unmapped Probe Role']
main_return 1
DB 함수 호출 0회
```

→ 해석: [검색어 사전 차단 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/ingest_positions.py:154)이 검색 가능한 공고의 매핑 누락을 DB 호출 전에 막았습니다.

**AC-8: `compose()` 정상·차단·실패 입력 반증**

```text
후보 1명, 정상 입력 → '... – 1 candidates', 재계산 점수 97
후보 0명, status=done, 사유='검색 완료, 통과자 없음'
→ '... – 0 candidates'
→ '이번 실행에서 등록 문턱(60점)을 넘은 후보 없음.'
후보 0명, status=blocked, 사유='기업회원 미인증'
→ '... – 0 candidates [BLOCKED]'
→ '검색 미완료(status: blocked) — 후보 유무를 판단할 수 없음.'
후보 0명, status=failed, 사유='포털 오류'
→ '... – 0 candidates [FAILED]'
후보 0명, 사유 없음 → ValueError
후보 0명, status=blocked, 사유 없음 → ValueError
```

→ 해석: [메일 상태 분기](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/codeitsearch-review/tools/codeitsearch/compose_mail.py:192)는 정상 보고를 막지 않았고 차단·실패를 제목과 본문에 표시했습니다. 다만 공백 사유 반례 때문에 AC-8 전체는 충족하지 못합니다.

**요청 시험과 재시도 원문**

```text
$ uv run --no-project --with pytest python -m pytest tools/codeitsearch/tests -q -p no:cacheprovider
error: Failed to initialize cache at `/Users/kangsangmo/.cache/uv`
  Caused by: failed to open file `/Users/kangsangmo/.cache/uv/sdists-v9/.git`:
  Operation not permitted (os error 1)
종료값 2

$ PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tools/codeitsearch/tests -q -p no:cacheprovider
/opt/homebrew/opt/python@3.14/bin/python3.14: No module named pytest
종료값 1
```

→ 해석: 전체 시험의 통과 여부는 **미확인**입니다. 읽기 전용 셸에서 임시 파일이 필요한 here-document도 실패해 `python3 -B -c` 직접 호출로 재시도했습니다. 직접 호출에서 한 차례 결과 객체에 없는 `school_tier` 속성을 읽어 실패한 시도는 `school_tier()`를 별도로 호출해 바로잡았습니다. 현재 작업 파일 변경은 없습니다.