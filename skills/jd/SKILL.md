---
name: jd
description: 채용공고(JD) 원문·파일·스크린샷·URL이 들어오면 그 JD 하나를 후속 업무 전체(서치·아웃리치·채널등록·조직매핑·과거이력)가 재사용하는 기준 데이터로 변환한다. 원문을 단위(Unit)로 쪼개 `outputs/_units/` 아래 회사·포지션 슬러그 JSON 에 넣고, 코드 파이프라인(`scripts/jd_channels/`)이 Gmail·LinkedIn RPS InMail·사람인·잡코리아 4채널 원고를 문자열을 자르지 않고 조립한다. ClickUp FY26ClientsPosition(901814621569) 중복을 먼저 확인하고 기존 태스크가 있으면 새로 만들지 않고 갱신한다. 회사·대표·투자 브리핑은 saramin-talent-sourcing §17 계약을 재사용한다. 트리거 — "이 JD 정리해줘", "JD 인텔리전스", "골든샘플로 만들어줘", "클릭업에 등록해줘", "이 공고 4채널로 만들어", 원티드/공식 채용페이지 URL + JD 원문 붙여넣기, JD 스크린샷. 이 스킬은 산출물만 만들고 발송·게시는 하지 않는다 — 실제 채널 등록/발송은 saramin-talent-sourcing · jobkorea-talent-sourcing · linkedin-rps-jd-set-builder · recruit-post-builder · position-register 가 이 스킬의 산출물을 이어받아 수행한다.
---

# JD — Recruiting Intelligence 정규화 스킬

> 이 스킬은 JD 요약기가 아니다. JD 하나를 **후속 전 업무가 다시 조사하지 않고 그대로 재사용할 기준 데이터**로 만드는 조립 라인이다.
>
> **Claude Code 와 Codex 가 같은 계약을 쓴다.** 플랫폼별 차이는 브라우저 조작 도구 이름뿐이다.

## 0. 절대 규칙

| # | 규칙 | 근거 |
|---|------|------|
| R0 | **산출물만 만든다 — 발송·게시 금지.** 후보자 메시지 발송, 사람인/잡코리아 포스팅 게시, LinkedIn Send 는 범위 밖 | 채널 스킬들의 R0와 동일 선상 |
| R1 | **원문 정보 손실 금지.** 회사소개·팀소개·포지션명·주요업무·자격요건·우대사항·근무조건·채용절차는 어느 것도 빠뜨리지 않는다 | 사장님 명시 |
| R2 | **지원 방법(자사 이메일·ATS 링크·"많은 지원 바랍니다")은 후보자용 산출물에서 100% 제거.** ClickUp 사내 원장에는 남겨도 된다 | 자사 직접 지원 = 서치펌 개입 무의미 |
| R3 | **숫자는 출처 있는 것만, 기준연도 명시, 추정 금지.** 소스가 갈리면 둘 다 병기 | saramin-talent-sourcing §17.6 |
| R4 | **문자열을 잘라 길이를 맞추지 않는다.** 줄이는 수단은 ① 단위의 compact/rps 표현 ② 비-core 단위 생략 두 가지뿐. 그래도 한도를 못 맞추면 `NEEDS_LENGTH_DECISION` 으로 드러낸다 | `render.py` STRATEGIES |
| R5 | **`core` 단위는 어떤 채널에서도 삭제 금지.** `rps_drop` 을 core 에 쓰면 `UnitError` 로 즉시 멈춘다 | `units.py` `_check_unit` |
| R6 | **ClickUp 은 중복 확인이 먼저다.** 기존 태스크가 있으면 새로 만들지 않고 갱신한다 | 2026-09-22 실측: 번개장터 2건 모두 이미 존재 |
| R7 | **회사 조사는 회사당 1회, 캐시 우선** (`~/.cache/saramin-company-research/<slug>.json`, TTL 30일) | §17.4~17.5 |
| R8 | **완료는 검사기 종료값으로만 말한다.** `bash scripts/acceptance-rps-inmail.sh` 가 0이 아니면 완료가 아니다 | 증거 없는 완료 금지 |

## 1. 입력

JD 원문 텍스트 · 파일 · 스크린샷 · URL 중 무엇이든 받는다.

| 입력 | 처리 |
|---|---|
| 원문 텍스트 | 그대로 SoT |
| 파일(.txt/.md/.pdf/.docx) | 읽어서 SoT. PDF 는 `pdf` 스킬 |
| 스크린샷 | 이미지를 읽어 텍스트를 옮긴다. **옮긴 뒤 원문과 한 줄씩 대조**하고, 못 읽은 구간은 추정하지 말고 사장님께 되묻는다 |
| URL | WebFetch/브라우저로 원문 확보. 실패하면 추정하지 않고 원문을 요청한다 |

SoT 우선순위: ①사장님이 직접 준 원문/캡처 ②Supabase `pipeline_position_cards.jd_text` ③회사 공식 채용페이지.

## 2. 절차

### Step A — ClickUp 중복 확인 (가장 먼저)

```
clickup_search(keywords="<회사명>", filters={asset_types:["task"], location:{subcategories:["901814621569"]}})
```

- 리스트: **FY26ClientsPosition** `901814621569` (Space `90182734130` Team Space / Folder `90183281517` Projects)
- 회사명만으로 먼저 훑고, 포지션명으로 좁힌다. **제목 표기가 `[회사] 포지션` 과 `[포지션]회사, 포지션` 두 가지로 섞여 있으므로 둘 다 본다.**
- 결과 분기:
  - 같은 포지션 태스크가 **있으면** → `clickup_update_task` 로 갱신한다. 새로 만들지 않는다(R6).
  - **없으면** → `clickup_create_task(list_id="901814621569", ...)`.
  - 제목이 다른데 같은 포지션으로 보이는 게 있으면 → 갱신 본문의 `## 중복 확인` 절에 후보로 적고 사장님 확인을 요청한다. 임의로 종료·삭제하지 않는다.
- status 는 직무군으로 고른다: `backend/fullstack/cto` · `ai/ml/data` · `po/pm/기획` · `frontend` · `designer` · `sales/bd` · `marketing` · `devops/sre/security/qa` · `hr/finance/strategy/etc` · `c-level` · `app` · `etc` · `closedpositions` · `complete`.

### Step B — 단위(Unit) 정의 작성

`outputs/_units/<company_slug>__<position_slug>.json`

필수 키: `company` `position` `source_url` `captured_at` `source_status` `jd_id` `company_slug` `position_slug` `units`.
`jd_id` 는 **ClickUp 태스크 id** 를 쓴다(원장과 산출물이 같은 키로 묶인다).

단위 하나의 키:

| 키 | 뜻 |
|---|---|
| `id` `section` `kind` `meaning` `full` `compact` `source` | 필수. `section` 은 company/team/domain/role/duties/requirements/preferred/growth/conditions/process/documents |
| `kind` | `core`(삭제 금지) · `company` · `extra` |
| `heading` `note` `merge_group` `drop_rank` | 선택 |
| `rps` | RPS InMail 전용 표현. 영문 용어와 `**볼드**` 보존 |
| `rps_drop` | RPS 본문에서 제외. **core 금지** |
| `rps_block` | `intro`/`mission`/`responsibilities`/`requirements`/`preferred`/`note`/`process`/`conditions`/`footnote` |
| `rps_order` | 같은 블록 안 순서(0=원문 순서) |

문서 최상위 `rps_labels` 로 섹션 제목을 갈아끼운다(예: `{"requirements": "Looking for"}`).

**Keep / Compress / Remove**
- Keep: 사실·숫자·역할·책임·자격요건·기술스택·조직구조·근무조건 전부 (R1)
- Compress: 미사여구 → 팩트 bullet. `compact` 는 `full` 보다 짧아야 한다(아니면 `UnitError`)
- Remove: 지원 이메일·ATS 링크·"지원해주세요"류 (R2). 단 ClickUp 본문에는 남긴다

### Step C — 회사 브리핑

`~/.cache/saramin-company-research/<slug>.json` 캐시 확인 → hit(≤30일)이면 재사용, miss면 [saramin-talent-sourcing §17.1~17.2](../saramin-talent-sourcing/SKILL.md) 10항목 조사. 여기서 조사 절차를 다시 정의하지 않는다.

**후보자용 본문에는 네거티브 지표(영업손실·인원수)를 싣지 않는다** — 매출·성장·투자·사용자 규모만. 검사기 `INMAIL_NEGATIVE_METRIC` 이 강제한다. 회사 units 는 `rps_drop: true` 로 빼고, ClickUp 본문에는 그대로 남긴다.

### Step D — 4채널 렌더

```bash
python3 -c "
import sys; sys.path.insert(0,'scripts')
from jd_channels.pipeline import run, format_reports
print(format_reports(run('outputs/_units/<slug>.json','outputs/run-<YYYYMMDD>')))
"
```

기대: 4줄 모두 `PASS ... READY_DRAFT`, `core 누락` 0건, `금지 문구` 0건.
`FAIL` 이 하나라도 있으면 원고를 손대지 말고 **단위 정의를 고친다**.

| 채널 | 한도 | 구조 |
|---|---|---|
| `gmail` | 없음 | 전체 섹션, full 표현 |
| `linkedin_rps` | 1,900 (hard 1,899) | **골든 구조** — `docs/sot/linkedin-rps-inmail.md` G1~G12 |
| `saramin` | 4,000 | 화살표(→) 삭제 위험 → `>` 치환 |
| `jobkorea` | 4,000 | 작은따옴표→백틱, en dash→물음표 위험 → 제거 |

### Step E — 검사

```bash
bash scripts/verify/run-acceptance.sh scripts/acceptance-rps-inmail.sh
```

종료값 0 + `VERDICT: PASS` 여야 다음으로 간다(R8). 골든 2건 통과(양성 대조군)와 AI 티 원고·산문 일색 원고 차단(음성 대조군)을 한 쌍으로 잰다.

RPS 본문 개별 확인:

```bash
python3 -c "
import sys,re; sys.path.insert(0,'scripts')
from jd_channels.units import load
from jd_channels.render import render
from jd_channels.checks import scan_inmail, inmail_structure
b=render(load('outputs/_units/<slug>.json'),'linkedin_rps').body
print('섹션',len(re.findall(r'^■ ',b,re.M)),'불릿',len(re.findall(r'^• ',b,re.M)),'볼드',len(re.findall(r'\*\*',b))//2,'자',len(b))
print('금지',sorted({h.rule for h in scan_inmail(b)}),'구조',[(h.rule,h.match) for h in inmail_structure(b)])
"
```

기대: 섹션 ≥4, 불릿 ≥8, 볼드 ≥5, 자 ≤1,899, 금지 `[]`, 구조 `[]`.

### Step F — ClickUp 반영

`scripts/jd_channels/clickup.py` 의 `render_task_body()` 로 본문을 만든다. 사내 원장이므로 **원문을 전량 보존**한다(네거티브 지표·지원 경로 포함).

Step A 의 분기대로 `clickup_update_task` 또는 `clickup_create_task` 를 호출하고, status 를 직무군으로 맞춘다.

> **ClickUp MCP 일일 한도 100콜.** 소진되면 본문을 `outputs/_clickup/<task_id>.md` 로 보존하고 `outputs/_clickup/PENDING.md` 에 남긴 뒤 `BLOCKED` 로 보고한다. 반영했다고 말하지 않는다.

### Step G — RPS 템플릿 저장 (선택, 승인 필요)

발송(Send)은 절대 누르지 않는다. 저장 절차는 [linkedin-rps-jd-set-builder](../linkedin-rps-jd-set-builder/SKILL.md) + `docs/sot/linkedin-rps-inmail.md` §5.

실측으로 확인된 함정 3가지(2026-09-22):
1. **컴포저는 Quill 리치텍스트다.** `**볼드**` 를 그대로 넣으면 별표가 그대로 보인다. `scripts/jd_channels/richtext.py` 의 `to_html()` 로 `<strong>` 으로 바꿔 넣는다.
2. **Quill 이 `<ul><li>` 를 지운다.** 붙여넣으면 불릿 0개·본문 손실(1,445자 → 1,073자). 골든 원문과 같은 `• ` 문자 불릿을 `<p>` 로 넣는다.
3. **타인 소유 템플릿은 수정하지 않는다.** Shared Templates 의 다른 소유자 템플릿은 건드리지 말고 `Save as new template` 로 제목을 달리해 새로 만든다. 저장 시 `Anyone in my organization` 을 명시 선택하고 `Only me` 가 꺼졌는지 **양방향으로** 확인한다.

## 3. 완료 보고 형식

산문 금지, 상태 줄 단위로:

```
units:     outputs/_units/<slug>.json (단위 N개, core M개)
channels:  gmail PASS / linkedin_rps PASS / saramin PASS / jobkorea PASS
rps:       섹션 5 · 불릿 N · 볼드 M · X자 · 금지 0 · 구조 0
acceptance: VERDICT PASS (9/9)  또는  FAIL(항목)
clickup:   updated <task_id> / created <task_id> / BLOCKED(사유)
rps_template: saved <이름> / not attempted / BLOCKED(사유)
```

## 4. 참고 (재정의하지 않고 참조만)

- RPS InMail 골든 규칙 G1~G12: `docs/sot/linkedin-rps-inmail.md`
- 코드: `scripts/jd_channels/` (`units` `render` `inmail` `checks` `measure` `pipeline` `richtext` `clickup`)
- 인수 검사: `scripts/acceptance-rps-inmail.sh` (CI `.github/workflows/verify.yml` 에 등록됨)
- 회사 조사 10항목·F1~F13: [saramin-talent-sourcing §17](../saramin-talent-sourcing/SKILL.md)
- 온톨로지 적재: [ontology](../ontology/SKILL.md) — 스키마를 새로 만들지 않고, 확인된 테이블에만 upsert
- 조직 구성원 매핑: [codeit-talent-archive-search](../codeit-talent-archive-search/SKILL.md)
- 채널 발송/등록: saramin-talent-sourcing · jobkorea-talent-sourcing · linkedin-rps-jd-set-builder · recruit-post-builder · position-register
