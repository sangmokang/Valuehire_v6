#!/usr/bin/env python3
"""planner.json + WU id -> WU Reviewer / Auditor / Integration 지시문 출력."""
import json, os, sys
PR, SHA, BASE = os.environ["LCR_PR"], os.environ["LCR_SHA"], os.environ["LCR_BASE"]

COMMON = f"""[절대 금지 — 읽기 전용]
- 파일 수정, git commit/push, 브랜치·PR 생성, PR 코멘트·리뷰·승인, 병합 금지. 수정이 필요하면 '최소 수정 권고'로 글만 쓰세요.
- 외부 유료 API(xAI/OpenAI/Anthropic 등)·외부 전송(--live-jev 등) 실행 금지. 비밀값 읽기·출력 금지.
- 외부 SDK(typesafe_sdk 등) 설치·import·실행 금지. SDK 동작은 저장소 코드와 lock 정보로 정적으로만 판단하세요. 같은 실험·명령을 2회 넘게 반복하지 마세요. 막히면 NOT_TESTED 로 적고 진행하세요.
- 실행하지 않은 테스트를 실행했다고 쓰지 마세요. 실행했다면 명령과 출력 원문(요약 말고)과 종료값을 붙이세요.

[대상]
- PR: https://github.com/sangmokang/Valuehire_v6/pull/{PR}  base {BASE}
- 먼저 실행: git fetch origin pull/{PR}/head && git checkout --detach {SHA} && git rev-parse HEAD
  결과가 다르면 STALE_SHA 라고 쓰고 멈추세요. 저장소 코드를 읽을 수 없으면 BLOCKED_CODEBASE_CONTEXT 라고 쓰고 멈추세요.
"""

FINDING = """Finding 형식(각 항목 필수): id, severity(S0 치명/S1 높음/S2 중간/S3 낮음), evidence(REPRODUCED|NOT_TESTED|NOT_REPRODUCIBLE|UNRESOLVED),
file_func(file:line + 그 줄의 역할), condition(발생 조건), impact(사업 영향), counter_evidence(다른 위치에서 이미 막는지 확인한 결과),
minimal_fix(최소 수정 권고), verify(검증 방법). 반대 증거로 막히면 철회, 확인 못 하면 '조건부 위험'으로 낮추세요. 억지로 문제를 만들지 마세요."""

PLANNER_TMPL = """[역할] Review Planner (PR #{PR}, 읽기 전용)

당신은 코드 리뷰 "계획자"입니다. 결함을 깊게 찾지 마세요. 변경 전체를 빠짐없이 Review Unit(WU)으로 나누는 것만 합니다.

[절대 금지 — 읽기 전용]
- 파일 수정, git commit, git push, 브랜치 생성, PR 생성/수정, PR 코멘트·리뷰·승인, 병합 금지.
- 외부 유료 API(xAI/OpenAI/Anthropic 등) 호출 금지. XAI_API_KEY 등 비밀값 읽기·출력 금지.
- 패키지 설치·네트워크가 필요한 테스트 실행 금지(이 단계는 계획만).

[대상]
- PR: https://github.com/sangmokang/Valuehire_v6/pull/{PR}
- base: main @ {BASE}
- HEAD SHA: {SHA}
- 먼저 실행: git fetch origin pull/{PR}/head && git checkout --detach {SHA}
  그리고 git rev-parse HEAD 결과를 그대로 보고하세요. 다르면 STALE_SHA 라고 쓰고 멈추세요.
- 변경 목록은 반드시 직접 계산: git diff --numstat {BASE} {SHA}
  (실행한 명령과 출력 원문을 그대로 붙이세요. 저장소 전체 코드를 읽을 수 없으면 BLOCKED_CODEBASE_CONTEXT 라고 쓰고 멈추세요.)

[할 일]
1. 변경 파일 전체 목록과 파일별 추가/삭제 줄 수.
2. 변경된 주요 symbol(함수·클래스·CLI 명령·계약 키).
3. 주요 호출 관계: 각 새 모듈을 누가 import/호출하는지(rg 로 확인, 명령과 결과 줄 수 기재). 제품 진입점(CLI·pyproject entry point 등)에서 닿는지.
4. 데이터 흐름: 입력 → 검증 → 핵심 로직 → 저장/외부 → 출력.
5. API/schema/DB/권한/외부 전송 경계.
6. 테스트 영향: 어떤 시험이 어떤 모듈을 덮는지.
7. Review Unit 분할: 파일 수로 기계적으로 자르지 말고 기능·데이터 흐름·계약·경계 단위로. 권장 WU 크기 변경 300~800줄, 1000줄 넘으면 재분할 검토. 고위험(권한·삭제·외부 전송·개인정보·마이그레이션)은 작아도 독립 WU.
   문서·lock 등 생성물은 "직접 변경 위험 낮음"으로 별도 분류하되 Primary WU 는 반드시 배정.
8. Risk Map(HIGH/MEDIUM/LOW)과 각 WU 의 blast radius(local/module/service/database/organization-wide/external).
9. 리뷰 순서(HIGH→MEDIUM→LOW).

[Coverage 검증 — 필수]
- 모든 변경 파일이 정확히 하나의 Primary WU 를 가져야 합니다.
- "diff 변경 파일 수 = Coverage Ledger 고유 파일 수" 를 숫자로 대조하고, 추가/삭제 줄 합계도 대조하세요.

[출력 형식 — 반드시]
사람이 읽는 요약은 한국어로 짧게. 그리고 마지막에 아래 두 표식 사이에 JSON 하나만 출력하세요(코드펜스 없이 표식 줄 그대로).
<<<PLANNER_JSON
{{"pr":{PR},"head_sha_checked":"<git rev-parse HEAD 결과>","numstat_cmd_output":"<원문>","files_total":N,"additions_total":N,"deletions_total":N,
 "wus":[{{"id":"WU01","title":"...","purpose":"...","risk":"HIGH|MEDIUM|LOW","blast_radius":"...","files":["path",...],"changed_lines":N,"symbols":["..."],"invariants":["지켜야 할 규칙"],"related_wus":["WU02"],"needs_auditor":true|false,"auditor_reason":"..."}}],
 "coverage_ledger":[{{"file":"path","added":N,"deleted":N,"primary_wu":"WU01","related_wus":["..."],"class":"code|test|doc|generated|config"}}],
 "coverage_check":{{"diff_files":N,"ledger_unique_files":N,"match":true|false,"lines_match":true|false}},
 "cross_wu_boundaries":[{{"id":"B01","between":["WU01","WU02"],"what":"계약/호출/타입 경계 설명"}}],
 "review_order":["WU.."],"risk_map":{{"영역":"HIGH|MEDIUM|LOW"}},"unknowns":["확인 못 한 것"]}}
PLANNER_JSON>>>
"""

def planner_prompt():
    return PLANNER_TMPL.format(PR=PR, SHA=SHA, BASE=BASE)

def wu_prompt(plan, wid):
    w = next(x for x in plan["wus"] if x["id"] == wid)
    others = [f"{x['id']} {x['title']}" for x in plan["wus"] if x["id"] != wid]
    return f"""[역할] WU Reviewer — {wid} (PR #109, 새 세션, 읽기 전용)
{COMMON}
[이 WU]
- 목적: {w.get('purpose')}
- 위험: {w.get('risk')} / blast radius: {w.get('blast_radius')}
- 변경 파일(이 WU 의 Primary): {json.dumps(w['files'], ensure_ascii=False)}
- 변경 symbol: {json.dumps(w.get('symbols', []), ensure_ascii=False)}
- 지켜야 할 불변조건: {json.dumps(w.get('invariants', []), ensure_ascii=False)}
- 관련 WU(경계만 참고, 리뷰 대상 아님): {json.dumps(w.get('related_wus', []), ensure_ascii=False)} / 전체 WU: {json.dumps(others, ensure_ascii=False)}

[할 일]
A. 이 WU 변경 파일의 모든 변경 줄을 읽으세요(샘플링 금지). git diff {BASE[:8]}..HEAD -- <파일> 로 확인하고, 읽은 파일별 줄 수를 보고하세요.
B. Dependency Expansion: 변경된 함수·클래스·CLI·계약 키·설정마다 callers/callees/importers/의존·검증·시험을 rg 로 추적(명령과 결과 줄 수 기재).
C. 데이터 흐름: 입력 → 검증 → 핵심 로직 → 저장/외부 → 출력, 그리고 실패 흐름.
D. 요구사항 검증: PR 설명·goal 문서 주장 → 실제 코드 → 시험을 대조(설명을 사실로 가정 금지).
E. 관련 위험만: 정확성·경계·null·타입·시간대·상태전이·권한·개인정보/외부전송·계약·원자성·동시성·중복실행·재시도·타임아웃·부분성공·비밀유출·비용폭증·시험회귀.
F. 적대적 검증: "이 구현이 틀렸다면 어떤 입력·순서·장애에서 드러나는가?" 시나리오마다 규칙/사전조건/입력순서/기대/코드상 예상/실제 실행 여부.
G. 가능하면 관련 시험만 실행: cd humansearch && uv run --frozen pytest <해당 시험> -q (네트워크·설치가 막히면 NOT_RUN 과 이유).
{FINDING}

[출력] 한국어 요약(코드 판단/아키텍처 판단/진행 판단 각 한 줄 포함) 뒤, 마지막에 표식 사이 JSON 하나:
<<<WU_JSON
{{"wu":"{wid}","head_sha_checked":"...","code_judgement":"중대한 결함 미발견|수정 필요|판단 보류","arch_judgement":"현재 조건에 적합|일부 보완 필요|구조 재검토 필요|판단 보류","progress_judgement":"다음 개발 단계 진행 가능|조건부 진행|운영 배포 보류|배포 준비 조건 충족",
 "files_reviewed":[{{"file":"...","changed_lines_read":N}}],"traced_files":["..."],"core_flow":"...",
 "findings":[{{"id":"{wid}-F1","severity":"S2","evidence":"NOT_TESTED","file_func":"...","condition":"...","impact":"...","counter_evidence":"...","minimal_fix":"...","verify":"..."}}],
 "adversarial":[{{"rule":"...","pre":"...","sequence":"...","expected":"...","code_predicts":"...","executed":false}}],
 "tests_executed":[{{"cmd":"...","exit":0,"summary":"... passed"}}],"tests_not_executed":["..."],"uncertainty":["..."],"confidence":"high|medium|low","verdict":"PASS|HOLD|FAIL"}}
WU_JSON>>>
"""

def auditor_prompt(plan, wid, reviewer_json):
    w = next(x for x in plan["wus"] if x["id"] == wid)
    return f"""[역할] Adversarial Auditor — {wid} (PR #109, 새 세션, 읽기 전용)
{COMMON}
이전 Reviewer 의 결론을 믿지 마세요. 목표: Reviewer 결론을 반증할 실제 경로가 있는가?
- Reviewer 가 PASS/철회한 것은 누락·과소평가를, finding 으로 낸 것은 과장·오탐을 공격하세요.
- 각 finding 을 코드로 다시 확인해 CONFIRMED / REFUTED / CONDITIONAL / NEEDS_MORE_EVIDENCE 로 분류.
- Reviewer 가 보지 않은 새 반례도 최소 3개 시도(시도 내용과 왜 실패/성공했는지 기록).
WU 파일: {json.dumps(w['files'], ensure_ascii=False)}
불변조건: {json.dumps(w.get('invariants', []), ensure_ascii=False)}
Reviewer 결과(JSON): {json.dumps(reviewer_json, ensure_ascii=False)}
{FINDING}
[출력] 한국어 요약 뒤 마지막에:
<<<AUDIT_JSON
{{"wu":"{wid}","head_sha_checked":"...","reclassified":[{{"id":"...","status":"CONFIRMED|REFUTED|CONDITIONAL|NEEDS_MORE_EVIDENCE","reason":"..."}}],"new_findings":[],"attempts":[{{"attack":"...","result":"..."}}],"tests_executed":[],"verdict":"PASS|HOLD|FAIL"}}
AUDIT_JSON>>>
"""

def integration_prompt(plan, results):
    return f"""[역할] Cross-WU Integration Reviewer (PR #109, 새 세션, 읽기 전용)
{COMMON}
전체 코드를 처음부터 다시 읽지 마세요. WU 사이 경계를 공격하세요. WU PASS 의 합은 PR PASS 가 아닙니다.
확인할 경계(관련된 것만): API↔Service 인자/반환/오류, Service↔저장 스키마·null·원자성, 계약 JSON↔런타임, 권한·개인정보 전송↔업무 로직,
생산자↔소비자 형식, 재시도↔부작용(중복), CLI↔모듈 계약, 설정/환경변수↔런타임 기본값, 시험↔제품(mock 이 실제 실패를 숨기는지), LLM 판정↔도구(모델 결과가 위험 행동을 직접 결정하는지).
Planner 경계 목록: {json.dumps(plan.get('cross_wu_boundaries', []), ensure_ascii=False)}
WU 결과 요약: {json.dumps(results, ensure_ascii=False)}
각 경계를 실제 코드(file:line)로 양쪽 끝까지 연결해 확인하고, 경계마다 VERIFIED / ISSUE / NOT_CHECKED 로 표시하세요.
{FINDING}
[출력] 한국어 요약 뒤 마지막에:
<<<INTEG_JSON
{{"head_sha_checked":"...","boundaries":[{{"id":"B01","status":"VERIFIED|ISSUE|NOT_CHECKED","evidence":"file:line ↔ file:line","note":"..."}}],"new_findings":[],"tests_executed":[],"verdict":"PASS|HOLD|FAIL"}}
INTEG_JSON>>>
"""

if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "planner":
        print(planner_prompt(), end=""); sys.exit(0)
    plan_path = sys.argv[2]
    plan = json.load(open(plan_path))
    if kind == "wu":
        print(wu_prompt(plan, sys.argv[3]))
    elif kind == "audit":
        print(auditor_prompt(plan, sys.argv[3], json.load(open(sys.argv[4]))))
    elif kind == "integ":
        print(integration_prompt(plan, json.load(open(sys.argv[3]))))
