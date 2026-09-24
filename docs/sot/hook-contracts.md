# Valuehire v6 — 로컬 강제 장치(git hook) 계약 (SOT)

최종 갱신: 2026-08-22
근거(도입 배경·적대검증·6종 위반 시연): `docs/engineering/hook-enforcement-goal-2026-08-07.md`

## 현재 규칙 — 입출력 계약

### `hooks/pre-commit`
```
입력  : stdin 없음. 스테이징된 파일 목록(git diff --cached --name-only --diff-filter=ACMR)
        ※ R(rename) 포함. 빼면 `git mv notes.txt leak.db` 가 목록에서 사라져 그대로 통과한다
출력  : exit 0 (통과) | exit 1 (차단)
        차단 시 stderr: "BLOCKED: <검사이름> — <파일경로> (패턴: <패턴이름>)"
        ※ 매칭된 실제 값은 절대 출력하지 않는다
검사  : ① 비밀 스캔(verify.sh 위임, VERIFY_SCAN_SOURCE=index) ② 검사기 자기 제외
        ③ 검사 약화 패턴 ④ 만료 없는/지난 억제 ⑤ LLM 출력→판정 수치 ⑥ 외부효과 모듈 네트워크 0건
        ⑦ 대용량 파일(1,048,576 바이트 초과) · 산출물 경로(artifacts/·data/·private-reviews/·
          *.db·*.sqlite·*.sqlite3) 차단 — P21. gitignore 가 `git add -f` 로 우회되므로
          차단 지점을 훅에도 둔다. 크기는 작업트리가 아니라 **인덱스 blob**에서 잰다
          (작업트리를 재면 add 후 덮어쓰기로 우회된다 — ①과 같은 이유).
          경로/확장자 비교는 **소문자로 정규화**한 뒤 수행한다(dump.DB 가 통과했다).
          디렉터리 규칙은 하위 경로까지 덮고, `.gitignore` 는 최상위로 앵커한다 —
          앵커가 없으면 src/data/schema.json 같은 정상 소스가 조용히 사라진다(P3).
          CI 등가물: `.github/workflows/verify.yml` 의 "대용량 파일 · 산출물 경로 스캔"
          (훅은 이번 커밋의 스테이지분만, CI 는 추적 파일 전체를 본다)
        ⑧ P3 조용한 실패 문법. 동일 block scope의 `const Map`만 제한적으로 예외 처리하고,
          확장자를 소문자로 정규화해 스테이지된 Python/JavaScript
          계열 blob을 같은 커밋의
          `scripts/acceptance-silent-failure-lint.sh`로 검사한다. 작업트리 사본은 판정에
          사용하지 않는다. CI는 같은 린터와 mutation 회귀를 전체 추적 파일에 실행한다
불변식: set -euo pipefail. 검사를 실행하지 못하면 exit 1 (fail-closed)
제외  : 없음. 자기 자신(hooks/)도 검사 대상이다
```

### `hooks/pre-push`
```
입력  : stdin 으로 <local ref> <local sha> <remote ref> <remote sha> (git 표준)
출력  : exit 0 | exit 1
        실행: verify.sh, scripts/acceptance-*.sh 전량 (glob — 새 스크립트 추가 시 자동 포함)
        차단 시 stderr: "BLOCKED: <스크립트경로> exit=<code>"
불변식: 스크립트가 0개 발견되면 exit 1 (fail-closed — "검사할 게 없어서 통과"를 금지)
        미추적 파일(??) 존재 시 exit 1 (P15)
한계  : git push --no-verify 로 우회 가능. CI 가 최종 방어선 (문서에 명시)
```

### `scripts/session-status.sh`
```
입력  : 없음
출력  : stdout 3줄 + exit 0
        HEAD: <sha> (<origin 대비: synced|ahead N|behind N>)
        ORIGIN: <sha>
        RED: <실패한 acceptance 스크립트 수>/<전체 수>
불변식: git 조회 실패 시 해당 줄에 "UNKNOWN" 을 출력하고 exit 1 (조용한 성공 금지)
```

### `scripts/acceptance-0-7.sh`
```
입력  : 없음
출력  : exit 0 (6종 전부 BLOCKED) | exit 1 (하나라도 통과)
        각 시연: "[N/6] <위반이름> → BLOCKED (exit=<code>)" 또는 "→ PASSED ← 결함"
불변식: 모든 시연은 mktemp -d 안의 clone 에서 수행.
        종료 시 원본 저장소의 git status 가 시연 전과 동일함을 확인하고, 다르면 exit 1
        판정은 종료 코드로만 한다. 문자열 비교 단독 판정 금지
```

### `scripts/install-hooks.sh`
```
입력  : 없음
동작  : git config core.hooksPath hooks && chmod +x hooks/*
출력  : exit 0 + 설치된 훅 목록
불변식: 실행 후 core.hooksPath 를 재조회해 실제로 설정됐는지 확인(readback). 불일치 시 exit 1
```

## 시행 지점

이 5개 파일 자체가 시행 지점이다. 각 파일 상단 주석의 `# 계약: docs/sot/hook-contracts.md`가 이 문서를 가리킨다 — 파일을 직접 읽으면 항상 최신 계약과 실제 구현이 같은지 대조할 수 있다.

## 비범위 / 한계

- 6종 위반 시연의 실제 실행 결과·적대검증 판정(V1 조건부 REJECT→승인까지 5차 판정)은 `docs/engineering/hook-enforcement-goal-2026-08-07.md` 실행 결과·적대 검증 로그 절에 있다. 이 문서는 재현하지 않는다.
- `git push --no-verify` 우회는 구조적으로 탐지 불가(2026-08-07 확정) — CI가 최종 방어선이라는 전제가 깨지면 이 문서 전체가 무효하다.

### `.claude/hooks/jev-command-gate.mjs` (에이전트 PreToolUse · Bash)
```
목적  : 에이전트가 실행하려는 셸 명령이 기존 데이터를 복구 불가능하게 지우거나 덮어쓰는지
        Jev(TypeSafe AI)에 물어 확률을 받고, 기준선 이상이면 실행 전에 막는다.
        git hook 이 아니라 .claude/settings.json 의 PreToolUse(matcher: Bash) 훅이다.
호출  : Vercel AI Gateway (https://ai-gateway.vercel.sh/v4/ai/evaluation-model, ai-model-id
        typesafe-ai/jev). Hobby(무료) 티어 키로 동작한다. 키: AI_GATEWAY_API_KEY (vck_…)
입력  : stdin JSON {session_id, tool_name, tool_input.command}
출력  : 확률 < 기준선  → 출력 없음, exit 0 (allow 를 내지 않는다 — 기존 권한 흐름 유지)
        확률 ≥ 기준선  → hookSpecificOutput.permissionDecision = deny (JEV_GATE_ACTION=ask 면 ask)
                         사유에 "jev 위험도 <p> ≥ 기준선 <t>" 를 적는다
        판정 불가(키 없음·HTTP 오류·시간 초과·응답 모양 이상)
                       → systemMessage "jev 게이트 NOT_RUN: <사유>" (세션·사유당 1회), exit 0
                         JEV_GATE_ON_ERROR=closed 면 deny
        설정 오류(JEV_GATE_THRESHOLD 범위 밖 등) → stderr, exit 1 (closed 면 exit 2)
설정  : JEV_GATE_THRESHOLD(기본 0.45) · JEV_GATE_ACTION(deny|ask) · JEV_GATE_ON_ERROR(open|closed)
        JEV_GATE_TIMEOUT_MS(기본 5000) · JEV_GATE=off(명시적 비활성) · JEV_ENDPOINT(테스트용)
한계  : 기본은 fail-open 이다 — 키가 없거나 게이트웨이가 죽으면 검사 없이 진행한다(대신 알린다).
        확률은 모델 추정이며 권한 체계를 대체하지 않는다. 차단 판정만 추가하고 허용은 하지 않는다.
        명령 문자열이 외부(Vercel·TypeSafe)로 전송된다. 비밀이 인자로 들어간 명령도 그대로 간다.
회귀  : scripts/acceptance-jev-gate.sh (로컬 mock 서버로 분기·요청 모양 검사)
```
