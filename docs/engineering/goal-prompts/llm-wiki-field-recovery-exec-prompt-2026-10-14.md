# 실행 프롬프트 — LLM 위키 필드 복구 ⓪→① (2026-10-14)

`/strict` L3. 정본: `docs/sot/llm-wiki.md`. 실측·판정: `docs/engineering/llm-wiki-field-recovery-goal-2026-10-14.md`. 이 프롬프트는 Codex·Claude 어느 쪽에 줘도 같은 결과가 나오도록 **명령·기대값·양성/음성 대조군**으로 쓴다. 산문 단언은 인수 기준이 아니다.

## 0. 시작 조건 (하나라도 다르면 멈추고 보고)

```bash
cd ~/Desktop/Valuehire_v6 && git fetch -q origin && git log -1 --format=%h origin/main
bash scripts/session-status.sh | sed -n 3p            # RED: 0/N 이어야 한다
bash scripts/acceptance-principles-check.sh | head -1   # VERDICT: PASS
bash scripts/acceptance-llm-wiki-fields.sh | tail -1    # VERDICT: PASS
lsof -d cwd -Fpcn | awk '/^p/{p=substr($0,2)}/^c/{c=substr($0,2)}/^n/{n=substr($0,2); if(n ~ /Valuehire_v6$/ && p!=ENVIRON["PPID"]) print p,c}'   # 다른 세션이 main cwd 면 착수 금지
```

## WU-⓪ anon 읽기 차단 (운영 권한 변경 — 사장님 승인 뒤에만 적용)

목표: 비로그인 anon 키로 `profile_archives`·`gmail_messages`·`pipeline_candidates_active`(뷰)의 **건수조차** 0 이어야 한다. 로그인 팀원(`authenticated`)과 `service_role` 경로는 깨지지 않아야 한다.

작업: v4 `supabase/migrations/<ts>_llm_wiki_anon_lockdown.sql` 하나.
- `profile_archives`: `enable row level security` + `service_role` all 정책 + `authenticated` select 정책(테넌트 함수 `valuehire_can_read_tenant` 재사용). anon 정책 없음.
- `pipeline_candidates_active`: `alter view … set (security_invoker = true)`.
- `gmail_messages`: 현재 anon 통과 원인을 `pg_policies`·`information_schema.role_table_grants` 로 먼저 조회해 기록한 뒤 같은 방식으로 막는다. 원인을 모르면 막지 말고 보고.
- down 마이그레이션 동봉.

RED 먼저(구현 전 실패해야 한다):
```bash
# 음성 대조군 — 지금은 206 */N 이 나와야 RED
for t in profile_archives gmail_messages pipeline_candidates_active; do curl -s -I "$URL/rest/v1/$t?select=id&limit=0" -H "apikey: $ANON" -H "Authorization: Bearer $ANON" -H "Prefer: count=exact" | grep -i content-range; done
```
GREEN 기대값: 세 줄 모두 `content-range: */0` 또는 401/403. 양성 대조군: 같은 호출을 service key 로 하면 `*/21651`·`*/35504`·`*/21771` 유지, 로그인 사용자 JWT 로 자기 테넌트 행이 보임(화면 `admin.valuehire.cc/ai-search-list` 1회 실조회 캡처).
counter-AC: 뷰만 막고 기본 테이블은 열린 채, 또는 기본 테이블만 막고 뷰·RPC가 열린 채. 셋을 전부 HTTP 로 확인한다.

## WU-① 구조화 프로필 13,600건 채움 (⓪ GREEN 뒤)

```bash
# dry-run 재확인 — 기대: "written": 0, "to_fill": 13600 ± 당일 신규
python3 scripts/llm_wiki/backfill_structured_profiles.py --db ~/Desktop/Valuehire_v4/tools/profile-archiver/server/data/archive.db --env ~/Desktop/Valuehire_v4/.env.local
# 표본 적용 10건 — 기대: "written": 10, "unmatched": 0, 장부 10줄
python3 scripts/llm_wiki/backfill_structured_profiles.py --db … --env … --apply --limit 10
# readback — 기대: 0-9/10
curl -s -I "$URL/rest/v1/profile_archives?select=id&structured_json=not.is.null&local_id=in.($(cut -d'"' -f4 ~/valuehire-private/llm-wiki/backfill-ledger.jsonl | paste -sd, -))" -H "apikey: $SERVICE" -H "Authorization: Bearer $SERVICE" -H "Prefer: count=exact" | grep -i content-range
# 전량 적용 → 감사기 → SOT 하한 상향 PR 동봉
python3 scripts/llm_wiki/backfill_structured_profiles.py --db … --env … --apply
python3 scripts/llm_wiki/field_audit.py --env ~/Desktop/Valuehire_v4/.env.local   # profile_archives.structured_json filled≈65%
```
음성 대조군: 같은 명령을 두 번 돌리면 두 번째는 `"written": 0, "skipped_filled": ≥13600`. 되돌리기: 장부의 local_id 를 `structured_json=null` 로 PATCH 한 뒤 감사기가 2.4%로 돌아오는지 확인.

## WU-② 동기화 코드 보강 (v4)

`tools/profile-archiver/server/index.js:1611` 페이로드에 `structured_json`(JSON 파싱 후 객체)·`career_companies_json`·`salary_man` 추가. RED: 가짜 Supabase 클라이언트로 upsert 인자에 세 키가 있는지 검사하는 시험이 먼저 실패해야 한다. counter-AC: 로컬 값이 `''` 이면 `null` 로 보내야 하며 `''` 문자열을 jsonb 에 넣어 통째 실패시키지 않는다(QA #192 재발 방지).

## 하지 말 것

새 테이블·새 마스터, 이름+회사로 사람 합치기, Jev 점수 공식 변경, LLM 이 숫자를 만들어 점수 칼럼에 쓰기(P14), `--no-verify`, 메인 작업트리 직접 수정, 후보자 원문을 `docs/` 에 붙이기.

## 보고

§8 형식. 결론 → 판단 근거 → 증거 원문. 각 WU 의 명령·시각·종료값·전체 출력을 `docs/engineering/evidence/llm-wiki-field-recovery-evidence-<날짜>.md` 에 덧붙인다. 메일은 `sangmokang@valueconnect.kr`, 제목 `[aisearch]claudecode …`.
