# Valuehire v6 — 로컬 강제 장치(git hook) 계약 (SOT)

최종 갱신: 2026-08-18
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
불변식: set -euo pipefail. 검사를 실행하지 못하면 exit 1 (fail-closed)
제외  : 없음. 자기 자신(hooks/)도 검사 대상이다
```

### `hooks/pre-push`
```
입력  : stdin 으로 <local ref> <local sha> <remote ref> <remote sha> (git 표준)
출력  : exit 0 | exit 1
        후보 수집: verify.sh, scripts/acceptance-*.sh (glob — 새 스크립트 추가 시 자동 포함)
        직접 실행 제외:
        - acceptance-0-2.sh — 로컬 실제 패턴으로 별도 수동 실행. push 시점에는 정상 Git 작업이
          만든 unreachable 객체가 있을 수 있어 종료상태 0건 조건을 요구하지 않는다
        - acceptance-0-5.sh — push 완료 뒤 원격 상태를 보는 검사라 push 직전에는 성립하지 않는다
        - 헤더에 PUSH-PERFORMING을 선언한 검사 — push 재귀를 막기 위해 CI에서만 실행한다.
          현재 acceptance-0-7.sh가 이에 해당하며, CI 실제 실행 줄이 없으면 pre-push가 차단한다
        양쪽 실행: acceptance-0-2-unreachable-content.sh — 위 예외에 해당하지 않으므로 로컬
        push와 CI가 모두 실행해 AC-19 합성 사례 13개를 검사한다
        차단 시 stderr: "BLOCKED: <스크립트경로> exit=<code>"
불변식: 스크립트가 0개 발견되면 exit 1 (fail-closed — "검사할 게 없어서 통과"를 금지)
        미추적 파일(??) 존재 시 exit 1 (P15)
한계  : git push --no-verify 로 우회 가능. CI는 실패 표시를 만들지만, 현재 원격 main은
        보호되지 않았고 개인 계정의 비공개 저장소 요금제에서는 필수 성공 검사 지정이
        잠겨 있어 합치기를 기계적으로 막지 못한다. 현재 최종 강제 주체는 사람 검토다
        (`docs/sot/git-workflow.md`의 2026-08-15 원격 실측 참조).
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
- `git push --no-verify` 우회는 구조적으로 탐지 불가(2026-08-07 확정)다. 현재 CI는 필수 합치기 조건이 아니므로 로컬 우회 뒤에도 실패 표시만 남기며, 사람 검토가 합치기 차단을 맡는다. GitHub Pro로 올리거나 저장소를 공개한 뒤 `verify` 성공을 필수 상태 검사로 지정해야 원격 기계 강제가 생긴다.
