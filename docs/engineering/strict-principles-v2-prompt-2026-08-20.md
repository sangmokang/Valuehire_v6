# 새 맥락 Codex V2 적대검증 프롬프트

당신은 구현자가 아닌 독립 검증자다. 파일을 수정하지 말고 현재 작업트리를 직접 읽고 명령을 실행하라. 과거 대화·project memory·기존 보고서의 결론을 신뢰하지 말고 증거 원문만 사용한다.

검증 목표는 `docs/sot/coding-principles.md`의 P1~P22, §1-B-1~5, V-1~5가 `docs/sot/principles.yaml`과 정확히 일치하고, Strict 시작의 직접 로드·검사, explicit pre-push, unconditional exact CI step, mechanism registry, Codex/Claude 공통 계약에 fail-closed로 연결됐는지 재공격하는 것이다.

반드시 직접 확인한다.

1. 현재 HEAD, 작업트리, 별도 worktree를 구분한다.
2. 두 SOT 파일과 검사기, mutation suite, pre-push, workflow, registry 및 registry checker를 읽는다.
3. 글로벌 Codex/Claude Strict 파일을 직접 읽고 공통 marker block 및 엔진 순서만 다른지 확인한다.
4. `bash scripts/acceptance-principles-check.sh`, `bash scripts/acceptance-principles-mutations.sh`, `bash scripts/verify/check-mechanism-registry.sh`, `bash scripts/acceptance-verify-ac-m.sh`, `bash scripts/verify/check-strict-principles-skills.sh`, `bash scripts/acceptance-guard-global-skill-files.sh`, `bash verify.sh`를 실행한다. 실제 전역 파일 guard는 검증 시작 전에 `lock`, 전역 파일 검증 뒤 `check`, 마지막에 `unlock` 순서로 실행하고 각 종료값을 보존한다. 잠금이 없는 정상 종료 상태에서 단독 `check` 실패를 구현 결함으로 세지 않는다.
5. 정상/14개 고장 fixture, 500/501, 검사 대상 0개, 검사기 자기 제외, CI exact scalar command·조건·`continue-on-error`·`|| true`, 메모리 없음/잘림을 공격한다.
6. `docs/engineering/strict-principles-v1-verdict-2026-08-20.md`와 원본 Claude JSONL의 실제 CLI 종료값·토큰·API 상태·해시를 확인한다. V1이 실제 검증을 못 했으면 `NOT_RUN`이며 최종 PASS를 금지한다.
7. V2 자신의 호출·세션이 실제 실행 증거인지 밝힌다.
8. `principles.yaml`의 `mechanism_found/status`가 Strict 계약 편입 장치만 뜻한다는 범위가 정본·장부·출력·보고서에서 일관되는지 확인하고, 이를 제품별 `mechanism_expected` 구현 완료로 과장한 문구가 있으면 결함으로 잡는다.
9. 확장된 mutation suite가 빈 파일·미지 ID·문구 불일치·빈 mechanism·잘못된 check/stages·자기 제외·CI `if exists`/다중 줄·pre-push 약화까지 실제 변조하는지 확인한다.

출력 형식:

- `VERDICT: PASS|FAIL|NOT_RUN` 한 줄. 이는 V2 자체 검증 판정이다.
- 최종 Strict 전체 판정은 별도로 `OVERALL_STRICT: PASS|FAIL|NOT_RUN`으로 쓴다.
- 중요도순 finding, 정확한 `file:line`, 실행 명령·종료값·전체 핵심 출력, 반례 표, 대칭성, 메모리 독립성, 남은 FAIL/NOT_RUN을 쓴다.
- 프롬프트가 요구한 상태가 아니라 실제 저장소가 보인 상태를 판정한다.
