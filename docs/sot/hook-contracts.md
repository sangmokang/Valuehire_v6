# Valuehire v6 — 로컬 강제 장치(git hook) 계약 (SOT)

최종 갱신: 2026-08-08
근거(도입 배경·적대검증·6종 위반 시연): `docs/engineering/hook-enforcement-goal-2026-08-07.md`

## 현재 규칙 — 입출력 계약

### `hooks/pre-commit`
```
입력  : stdin 없음. 스테이징된 파일 목록(git diff --cached --name-only)
출력  : exit 0 (통과) | exit 1 (차단)
        차단 시 stderr: "BLOCKED: <검사이름> — <파일경로> (패턴: <패턴이름>)"
        ※ 매칭된 실제 값은 절대 출력하지 않는다
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
