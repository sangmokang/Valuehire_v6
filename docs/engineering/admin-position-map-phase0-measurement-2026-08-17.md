MEASURED: 4/4 — codex 자체 실행 0/4(네트워크 차단, 본문) + V1(Claude) 재실행 4/4(하단 부록, 2026-08-18)

# 결론

네 가지 운영 확인은 이번 실행에서 한 건도 끝내지 못했습니다. 운영 주소를 찾는 단계에서 연결이 막혀 자료를 읽기 전에 멈췄으며, 이를 0건이나 “문제없음”으로 바꾸어 적지 않았습니다.

기존 초안에는 네 항목이 성공했다는 수치와 출력이 있었지만, 그 수치를 만든 원본 실행 흔적을 이번 세션에서 확인하지 못했습니다. 따라서 그 초안을 제 실측으로 인정하지 않고 모두 **NOT_RUN — 실행하지 못함**으로 바로잡았습니다.

사람이 별도 읽기 가능 환경에서 아래 네 조회문을 그대로 실행해야 설계서의 데이터 의존 결정을 확정할 수 있습니다. 그 전까지 중복 방지 방식, 배치 연결, 후보 연결 비율, 상태 목록은 모두 미확정입니다.

후보 실명·연락처·프로필 주소는 읽거나 출력하지 않았고, 어떤 운영 자료도 바꾸지 않았습니다. 첫 관리 주소와 기존 프로젝트 주소를 각각 한 번 확인했으나 둘 다 같은 이름 조회 오류로 실패했습니다.

## 판단 근거

### 결정 1 — 확인하지 못한 수치를 실측으로 인정하지 않았습니다

- **무엇을**: 이번 실행에서 운영 응답을 받은 항목만 성공으로 세고, 네 항목을 모두 NOT_RUN으로 판정했습니다.
- **왜**: 기존 초안의 성공 출력이 실제 명령에서 나온 것인지 재현하거나 원본 실행 로그로 입증하지 못했기 때문입니다.
- **버린 대안**: 초안에 적힌 숫자를 그대로 믿는 길은 “실행하지 않은 결과를 실행했다고 쓰지 않는다”는 정본 원칙과 충돌해 버렸습니다.
- **대가**: 스펙 v2는 일부 구현 방식을 지금 확정하지 못하고, 실측 완료 전 중단 문지기를 가져야 합니다.
- **되돌리는 법**: 읽기 가능한 환경에서 아래 SELECT가 성공하면 원 출력과 실행 시각을 붙이고 MEASURED 수를 실제 성공 건수로 올립니다.

### 결정 2 — 쓰기 권한이 있는 우회 접속은 사용하지 않았습니다

- **무엇을**: Supabase 관리 API의 읽기 전용 질의 주소와 기존 프로젝트의 읽기 주소까지만 확인했습니다.
- **왜**: 작업 계약이 운영 자료 변경 가능성을 열지 않고 조회만 허용하기 때문입니다.
- **버린 대안**: 서비스 역할 키나 새 접속 정보를 이용한 우회는 읽기 문장만 보내더라도 접속 주체가 쓰기 능력을 가지므로 사용하지 않았습니다.
- **대가**: 현재 샌드박스에서는 운영 수치를 얻지 못했습니다.
- **되돌리는 법**: 네트워크와 읽기 자격이 있는 격리 환경에서 같은 SELECT만 실행하면 됩니다.

## 증거 전문

### 1. 찾은 기존 접속 관례

Valuehire_v4의 **tools/clickup-sync/mirror-boards.mjs:36-47**은 저장소의 `.env.local`과 `.env`를 읽는 기존 환경 변수 적재 관례이고, 같은 파일 **93-96줄**은 기존 Supabase 주소와 키를 요구합니다. 이 값 자체는 출력하지 않았습니다.

이번 실행은 쓰기 가능한 서비스 역할 키 대신, 로컬 Supabase CLI 토큰을 화면에 노출하지 않고 읽는 관리 API의 읽기 전용 주소를 먼저 사용했습니다.

~~~bash
node - <<'NODE'
const fs = require('fs');
const token = fs.readFileSync('/Users/kangsangmo/.supabase/access-token', 'utf8').trim();
const endpoint = 'https://api.supabase.com/v1/projects/sjldbyfcesinrbkgkqwv/database/query/read-only';
const query = 'select version() as postgres_version;';
fetch(endpoint, {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ query }),
}).then(async (response) => {
  console.log(`HTTP ${response.status}`);
  console.log(await response.text());
  if (!response.ok) process.exit(1);
}).catch((error) => {
  console.error(error);
  process.exit(1);
});
NODE
~~~

→ 뭘 시켰나: 로컬 토큰 값을 출력하지 않고 운영 프로젝트의 읽기 전용 질의 주소로 버전 SELECT 한 문장만 보내게 했습니다.  
→ 뭐가 나왔나: 데이터베이스에 닿기 전 주소 이름 조회에서 실패했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 자료를 바꾸지 않은 것은 좋지만, M1을 실행한 것으로 셀 수 없어 나쁜 소식입니다.

~~~text
TypeError: fetch failed
    at node:internal/deps/undici/undici:13510:13
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
    at async [stdin]:88:17 {
  [cause]: Error: getaddrinfo ENOTFOUND api.supabase.com
      at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26) {
    errno: -3008,
    code: 'ENOTFOUND',
    syscall: 'getaddrinfo',
    hostname: 'api.supabase.com'
  }
}
~~~

→ 뭘 시켰나: 위 명령의 전체 오류를 숨기지 않고 남겼습니다.  
→ 뭐가 나왔나: 호스트 이름을 찾지 못했다는 ENOTFOUND 오류이며 운영 SQL 응답은 0건입니다.  
→ 좋은 소식인가 나쁜 소식인가: 네 SELECT의 내용 문제가 아니라 현재 실행 환경의 네트워크 차단이지만, 성공으로 간주할 수 없습니다.

기존 `.env.local`의 프로젝트 주소에도 후보 stage 한 열만 읽는 GET을 보내 보았으나 같은 단계에서 실패했습니다.

~~~bash
node - <<'NODE'
const fs = require('fs');
const env = {};
for (const line of fs.readFileSync('.env.local', 'utf8').split('\n')) {
  const match = /^([A-Z0-9_]+)=(.*)$/.exec(line.trim());
  if (match) env[match[1]] = match[2].replace(/^["']|["']$/g, '');
}
const url = env.NEXT_PUBLIC_SUPABASE_URL;
const key = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
fetch(`${url}/rest/v1/pipeline_candidates?select=stage&limit=1`, {
  headers: { apikey: key, Authorization: `Bearer ${key}` },
}).then(async (response) => {
  console.log(`HTTP ${response.status}`);
  console.log(await response.text());
  if (!response.ok) process.exit(1);
}).catch((error) => {
  console.error(error);
  process.exit(1);
});
NODE
~~~

→ 뭘 시켰나: 기존 프로젝트 주소에서 후보 stage 한 열·한 행만 읽고, 환경 변수 값은 출력하지 않도록 했습니다.  
→ 뭐가 나왔나: 아래처럼 주소 이름 조회에서 실패했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 관리 주소만의 장애가 아니라 현재 샌드박스의 외부 연결 차단임을 확인했습니다.

~~~text
TypeError: fetch failed
    at node:internal/deps/undici/undici:13510:13
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
  [cause]: Error: getaddrinfo ENOTFOUND sjldbyfcesinrbkgkqwv.supabase.co
      at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26) {
    errno: -3008,
    code: 'ENOTFOUND',
    syscall: 'getaddrinfo',
    hostname: 'sjldbyfcesinrbkgkqwv.supabase.co'
  }
}
~~~

→ 뭘 시켰나: 위 대체 조회의 전체 오류를 숨기지 않고 남겼습니다.  
→ 뭐가 나왔나: 프로젝트 주소도 이름 조회에서 막혀 운영 응답은 없었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 안전한 대체 조회 길도 현재 환경에서는 없다는 뜻입니다.

### M1 — 운영 PostgreSQL 버전

**NOT_RUN — api.supabase.com 이름 조회가 실패해 운영 데이터베이스에 도달하지 못했습니다.**

~~~sql
select version() as postgres_version;
~~~

→ 뭘 시켰나: 사람이 운영 데이터베이스 제품과 버전만 읽도록 하는 전문입니다.  
→ 뭐가 나왔나: 이번 실행에서는 결과가 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: PostgreSQL 15 이상 여부를 확인하지 못해 유일성 제약의 문법 분기를 확정할 수 없습니다.

### M2 — 배치 포지션 키와 포지션 카드 원본 ID 대조

**NOT_RUN — 같은 네트워크 차단으로 운영 행을 읽지 못했습니다.** 아래 문장은 서로 다른 키 전체의 일치·불일치 건수와 최근 표본 열 건을 함께 반환합니다.

~~~sql
with batch_ids as (
  select position_id, count(*)::int as step_rows, max(created_at) as last_seen_at
  from public.position_batch_steps
  group by position_id
),
card_ids as (
  select raw_clickup_payload->>'id' as clickup_task_id, count(*)::int as card_rows
  from public.pipeline_position_cards
  where raw_clickup_payload->>'id' is not null
  group by raw_clickup_payload->>'id'
),
joined as (
  select b.position_id, b.step_rows, b.last_seen_at,
         coalesce(c.card_rows, 0) as matched_card_rows
  from batch_ids b
  left join card_ids c on c.clickup_task_id = b.position_id
)
select jsonb_build_object(
  'distinct_position_ids', count(*)::int,
  'matched_distinct_ids', count(*) filter (where matched_card_rows > 0)::int,
  'unmatched_distinct_ids', count(*) filter (where matched_card_rows = 0)::int,
  'sample', coalesce((
    select jsonb_agg(to_jsonb(sample_rows) order by sample_rows.last_seen_at desc)
    from (
      select position_id, step_rows, matched_card_rows, last_seen_at
      from joined
      order by last_seen_at desc
      limit 10
    ) sample_rows
  ), '[]'::jsonb)
) as m2
from joined;
~~~

→ 뭘 시켰나: 모든 배치 키를 카드 원본 ID와 대조하고, 전체 판정과 다섯 건 이상의 표본을 한 번에 내게 합니다.  
→ 뭐가 나왔나: 이번 실행에서는 결과가 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: 일치 여부가 미확정이므로 v1 외곽선 조인을 채택할 수 없고 NOT_RUN으로 막아야 합니다.

### M3 — ClickUp 미러 후보의 연결값·이름 상태·출처 분포

**NOT_RUN — 같은 네트워크 차단으로 운영 행을 읽지 못했습니다.** 아래 문장은 실명을 반환하지 않고 이름의 존재 상태와 건수만 반환합니다.

~~~sql
with clickup_rows as (
  select name, source, jd_id
  from public.pipeline_candidates
  where sync_origin = 'clickup'
),
name_distribution as (
  select case
    when name is null then 'NULL'
    when btrim(name) = '' then 'BLANK'
    else 'PRESENT'
  end as name_state,
  count(*)::int as row_count
  from clickup_rows
  group by 1
),
source_distribution as (
  select coalesce(nullif(btrim(source), ''), '<NULL_OR_BLANK>') as source_value,
         count(*)::int as row_count
  from clickup_rows
  group by 1
)
select jsonb_build_object(
  'clickup_rows', (select count(*)::int from clickup_rows),
  'jd_id_null_rows', (select count(*)::int from clickup_rows where jd_id is null),
  'jd_id_null_pct', (
    select case when count(*) = 0 then null
                else round(100.0 * count(*) filter (where jd_id is null) / count(*), 2)
           end
    from clickup_rows
  ),
  'distinct_nonblank_names', (
    select count(distinct btrim(name))::int
    from clickup_rows
    where name is not null and btrim(name) <> ''
  ),
  'name_distribution', coalesce((
    select jsonb_agg(to_jsonb(name_rows) order by name_state)
    from name_distribution name_rows
  ), '[]'::jsonb),
  'source_distribution', coalesce((
    select jsonb_agg(to_jsonb(source_rows) order by row_count desc, source_value)
    from source_distribution source_rows
  ), '[]'::jsonb)
) as m3;
~~~

→ 뭘 시켰나: ClickUp 미러 후보만 골라 직접 연결 빈값 비율, 이름 유무, source 값별 건수를 실명 없이 계산하게 합니다.  
→ 뭐가 나왔나: 이번 실행에서는 결과가 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: 직접 연결의 실제 비율을 모르므로 3순위 연결은 계약하되 성공률을 단정할 수 없습니다.

### M4 — 후보 stage 전체 분포

**NOT_RUN — 같은 네트워크 차단으로 운영 행을 읽지 못했습니다.**

~~~sql
select stage, count(*)::int as row_count
from public.pipeline_candidates
group by stage
order by stage nulls first;
~~~

→ 뭘 시켰나: 저장된 후보 상태 전체를 값별 건수로 묶게 합니다.  
→ 뭐가 나왔나: 이번 실행에서는 결과가 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: 백필 마이그레이션에 없는 운영 값을 확인하지 못해, 어떤 미등록 값이든 색 집계를 NOT_RUN으로 멈춰야 합니다.

## 측정 판정 요약

| 항목 | 실행 | 판정 | 연결 감사 결함 | 사업 영향 |
|---|---:|---|---|---|
| M1 | 실패 | NOT_RUN — 네트워크 차단 | R7 | 발송 원장 유일성 문법 분기를 확정할 수 없습니다. |
| M2 | 실패 | NOT_RUN — 네트워크 차단 | R8 | 배치 횟수 외곽선을 계산하면 안 됩니다. |
| M3 | 실패 | NOT_RUN — 네트워크 차단 | R5 | 직접 연결 비율을 수치로 말할 수 없습니다. |
| M4 | 실패 | NOT_RUN — 네트워크 차단 | R4 | 운영 상태 집합을 완결된 목록으로 말할 수 없습니다. |

→ 뭘 시켰나: 네 항목의 실행 여부와 설계 영향을 한 표로 대조했습니다.  
→ 뭐가 나왔나: 실제 성공 0건, NOT_RUN 4건입니다.  
→ 좋은 소식인가 나쁜 소식인가: 정직한 중단에는 성공했지만 운영 실측 자체는 미완료입니다.

## 확인하지 못한 것

- ※ 운영 PostgreSQL 버전과 `UNIQUE NULLS NOT DISTINCT` 사용 가능 여부.
- ※ 배치 position_id와 포지션 카드 ClickUp 원본 ID의 일치·불일치 건수 및 표본.
- ※ ClickUp 미러 후보의 jd_id NULL 비율, 이름 상태와 source 분포.
- ※ pipeline_candidates.stage의 운영 distinct 전수와 각 건수.
- ※ 기존 초안의 17.6, 88/109, 4,088/4,089, 24종이라는 숫자는 이번 실행에서 재현되지 않아 근거로 채택하지 않았습니다.

## 개인정보와 쓰기 부작용 확인

- 후보 실명·연락처·프로필 URL은 출력하지 않았습니다.
- 실행을 시도한 SQL은 SELECT 한 문장뿐이고, M2·M3의 WITH도 마지막 동작이 SELECT입니다.
- 관리 API와 프로젝트 주소 모두 네트워크 이름 조회에서 멈춰 운영 데이터베이스 응답은 0건입니다.
- Supabase·ClickUp·Gmail·그 밖의 외부 서비스에 INSERT, UPDATE, DELETE, UPSERT, 발송, 등록을 실행하지 않았습니다.

→ 뭘 시켰나: 이번 시도가 금지된 쓰기나 개인정보 노출을 만들었는지 대조했습니다.  
→ 뭐가 나왔나: 운영 쓰기 0건, 외부 발송 0건, 후보 개인정보 출력 0건입니다.  
→ 좋은 소식인가 나쁜 소식인가: Phase 0의 안전 경계는 지켰지만 실측 완료 조건은 충족하지 못했습니다.

## 부록 — V1(Claude) 재실행 결과 (2026-08-18 00:10~00:20 KST, 네트워크 가용 환경)

codex가 남긴 조회문 4건을 검증자(Claude, V1)가 수정 없이 그대로 실행했다. 전부 읽기 전용(SELECT)이며, 관리 API의 읽기 전용 질의 주소를 사용했다. 실행자·시각을 §8-1 보관 규칙에 따라 명시한다.

### M1 — 성공

~~~text
=== M1 HTTP 201 ===
[{"postgres_version":"PostgreSQL 17.6 on aarch64-unknown-linux-gnu, compiled by gcc (GCC) 15.2.0, 64-bit"}]
~~~
→ 운영 데이터베이스는 PostgreSQL 17.6이다. 15 이상이므로 발송 원장 유일성은 본 스펙 §3-7의 `NULLS NOT DISTINCT` 분기를 채택한다. COALESCE 대체 분기는 폐기.

### M2 — 성공

~~~text
=== M2 HTTP 201 ===
[{"m2":{"matched_distinct_ids":88,"distinct_position_ids":109,"unmatched_distinct_ids":21,
"sample":[{"step_rows":17,"position_id":"wrtn-japan-accounting-2026-08-12","matched_card_rows":0},
{"step_rows":1,"position_id":"fastview-content-mgr-jp-20260812","matched_card_rows":0},
{"step_rows":1,"position_id":"fastview-po-20260812","matched_card_rows":0},
{"step_rows":1,"position_id":"fastview-content-mgr-en-20260812","matched_card_rows":0},
{"step_rows":4,"position_id":"fastview-hr-generalist-20260812","matched_card_rows":0},
{"step_rows":18,"position_id":"86exxxqc1","matched_card_rows":0},
{"step_rows":52,"position_id":"86exa9uhq","matched_card_rows":1},
{"step_rows":55,"position_id":"86exp7b5m","matched_card_rows":1},
{"step_rows":55,"position_id":"86exp7bw9","matched_card_rows":1},
{"step_rows":55,"position_id":"86exa9uhr","matched_card_rows":1}]}}]
~~~
→ 109개 배치 키 중 88개만 포지션 카드와 일치, 21개 불일치. 불일치는 수기 슬러그 형식(`wrtn-japan-…`, `fastview-…`)과 카드에 없는 ClickUp ID(`86exxxqc1`) 두 부류다. **§3-6의 분기 2가 확정된다** — v1 조인 단독 채택 불가, `position_card_id` 필수화 + 기존 키 전수 교정이 P0 범위다.

### M3 — 성공

~~~text
=== M3 HTTP 201 ===
[{"m3":{"clickup_rows":4089,"jd_id_null_pct":99.98,"jd_id_null_rows":4088,
"source_distribution":[{"row_count":4081,"source_value":"clickup"},{"row_count":8,"source_value":"clickup_import"}],
"distinct_nonblank_names":3375}}]
~~~
→ ClickUp 미러 후보 4,089명 중 4,088명(99.98%)이 직접 연결값(jd_id) 빈값. 직접 연결은 사실상 AI 서치 유래 후보에만 존재하므로 **§3-5의 3순위 연결 계약이 필수임이 수치로 확정**된다.

### M4 — 성공

~~~text
=== M4 HTTP 201 ===
[{"stage":"ai_search","row_count":7877},{"stage":"code_test","row_count":4},{"stage":"code_test_fail","row_count":133},
{"stage":"coding_test","row_count":1},{"stage":"document","row_count":543},{"stage":"document_fail","row_count":1862},
{"stage":"document_review","row_count":1},{"stage":"final_pass","row_count":23},{"stage":"interview_1","row_count":44},
{"stage":"interview_2","row_count":15},{"stage":"interview_3","row_count":1},{"stage":"interview_fail","row_count":836},
{"stage":"joined","row_count":201},{"stage":"pool","row_count":1},{"stage":"position_stop","row_count":41},
{"stage":"recommend_fail","row_count":75},{"stage":"recommended","row_count":104},{"stage":"reference_check","row_count":1},
{"stage":"resigned","row_count":9},{"stage":"self_drop","row_count":35},{"stage":"self_drop_early","row_count":123},
{"stage":"self_drop_late","row_count":47},{"stage":"sourced","row_count":61},{"stage":"talent_pool","row_count":709}]
~~~
→ 운영 stage는 영문 키 24종. 계약 매핑 15종 밖의 값 9종(ai_search·document·document_review·pool·position_stop·recommend_fail·sourced·talent_pool·reference_check)과 이상값 2종(`coding_test` 1행 — `code_test`와 중복 표기, `self_drop` 35행 — 미러 합침 산물)이 실재한다. **스펙 v2의 미지값 NOT_RUN 문지기가 없었다면 이 값들이 조용히 투명 처리될 뻔했다** — 문지기 설계가 실측으로 정당화됐다.

### 초안 숫자 검증 (정직성 판정)

codex가 "재현 못 해 폐기"한 초안 숫자 4개(17.6 / 88/109 / 4,088/4,089 / 24종)는 **V1 재실행 결과와 전부 일치**한다. 초안 실측은 조작이 아니라 실제 실행이었고, 이후 샌드박스 네트워크 차단으로 재현만 실패한 것이다. codex의 폐기 결정은 "재현 불가면 주장하지 않는다" 원칙의 올바른 적용이었으며, 이제 V1 재실행이 그 수치를 독립 확증했다.
