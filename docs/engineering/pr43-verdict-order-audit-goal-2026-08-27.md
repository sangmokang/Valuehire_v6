# PR #43 판정 순서·원격 조회 fail-closed 감사 goal (2026-08-27)

## 1층 — 결론

로컬 변경은 승인할 수 있습니다. 처음에는 뒤쪽의 깨진 검사 기록, 조회 명령의 부분 출력 뒤 실패, 빈 필드와 후속 추가 콜론을 시험이 놓쳤지만, 모두 재현한 뒤 판정기·36개 인수 검사·P23 기준 문서를 함께 고쳤습니다. Claude Code V1과 새 맥락 Codex V2도 각각 적대 검증 PASS를 냈습니다.

그러나 원격에는 아직 새 로컬 커밋이 없고 그 SHA의 GitHub Actions도 없습니다. 따라서 병합 상태는 변경 요청이며, 자동 실행은 push·PR 수정·병합·PR #29 종료를 하지 않고 정확한 수동 push 명령에서 멈춥니다.

## 2층 — 판단 근거

- 선택: 모든 원격 검사 레코드의 구조를 먼저 끝까지 검증한 뒤 성공 여부를 집계합니다.
- 버린 해석: 앞의 pending/failure만 보고 멈춰도 된다는 해석은 뒤의 오형식·알 수 없는 상태를 숨기므로 기각했습니다.
- 틀리면 깨지는 것: 일부 손상된 API 응답, 부분 출력 뒤 실패, pagination 누락이 정상적인 미검증 또는 거짓 성공으로 낮아질 수 있습니다.
- 확인한 것: 관련 검사 36개, 원칙 검사 34개, 원칙 변이 48개와 10종 구현 약화 공격이 모두 기대대로 작동했습니다.
- 남은 것: 사람이 로컬 커밋을 원격 후보 브랜치에 일반 push한 뒤 정확한 새 SHA의 Actions와 PR 상태를 읽기 전용으로 재검증해야 합니다.

## 모드·범위·중단 조건

- 모드: `$humanreview` + `$codeaudit` + Claude Code V1 + Strict L3
- 시작 HEAD: `5717f4ac67a64b25c3672fd990315611bf2cc39f`
- 브랜치: `task/pr29-history-scan-final-20260825`
- 대상: P23 정본·파생 장부, SHA 판정기, 인수 검사, 감사 장부, 다음 `$strict` 프롬프트
- 비범위: Issue #22 확대, 외부 push, PR 생성·수정·병합, PR #29 종료, 운영 배포
- 로컬 성공 중단: 필수 게이트·V1·V2가 모두 유효한 PASS이고 Lore 로컬 커밋이 생성됨
- 원격 성공 중단: 사람이 push한 뒤 로컬·원격·PR·Actions SHA가 같고 모든 `verify` 실행이 completed/success임

## 결정 카드

> **무엇을** — 모든 검사 기록의 구조와 모든 조회 명령 종료값을 먼저 검증하고 그 뒤 합격 여부를 집계합니다.
> **왜** — 부분 출력이나 뒤쪽 손상은 “검사 실패”가 아니라 “조회 불능”이며 순서에 따라 판정이 바뀌면 안 됩니다.
> **버린 길** — 첫 실패에서 멈추거나 문서 경고만 추가하는 길은 오분류와 거짓 초록을 남겨 기각했습니다.
> **대가** — 응답 하나가 깨지면 다른 유효 정보가 있어도 전체 조회를 다시 해야 하고 시험 수가 늘어납니다.
> **되돌리기** — 최종 로컬 커밋을 `git revert <checkpoint-sha>`로 되돌릴 수 있습니다.

## 3층 — 기술 상세와 증거 원문

### T 계약

1. 같은 SHA의 이름 `verify` 레코드는 집계 전에 전부 구조와 상태를 검증합니다.
2. malformed, 빈 status, 빈 conclusion, 콜론 둘 이상, 알 수 없는 status가 어느 위치에든 있으면 `NOT_RUN`, exit 2입니다.
3. 구조가 모두 유효하고 pending 또는 non-success completed가 있으면 `UNVERIFIED`, exit 1입니다.
4. 모든 실행이 `completed:success`이고 local=remote=ci, worktree clean일 때만 `VERIFIED`, exit 0입니다.
5. 실행 0개는 `UNVERIFIED`, exit 1입니다.
6. 실제 조회는 모든 페이지와 빈 레코드를 손실 없이 전달하고 Bash 3.2 빈 배열을 정상 처리합니다.
7. 브랜치·로컬 SHA·원격 SHA·작업트리·`gh`·필터 조회가 부분 출력 뒤 실패해도 `NOT_RUN`, exit 2입니다.
8. P23 정본, 파생 장부, 구현, 인수 검사와 실행 안내는 같은 계약을 말합니다.
9. 파일 600줄, 함수 100줄 hard 한도를 보존합니다.
10. 다음 실행문은 자동 원격 쓰기를 금지하고 사람의 정확한 수동 명령에서 멈춥니다.

### 발견·수정 장부

| ID | 최초 결함 | 수정·현재 상태 |
|---|---|---|
| F1 | pending/failure 뒤의 오형식·unknown을 보지 않음 | 구조 검증과 집계를 두 반복문으로 분리, GREEN |
| F2 | P23 SOT가 단일 success·옛 건수를 유지 | 전량 completed/success·36건으로 동기화, GREEN |
| F3 | 옛 다음 프롬프트가 자동 push·PR 수정을 지시 | 수동 명령과 `HUMAN_ACTION_REQUIRED`로 교체, GREEN |
| F4 | 다음 프롬프트 brief-lint 위반 1건 | `lint:skip` 제거·블록 해석 추가, 0건 |
| F5 | Bash 3.2에서 빈 배열 확장이 죽음 | 0건 명시 분기, GREEN |
| F6 | 빈 API 레코드가 파이프 전달 중 사라짐 | `R`/`X` 인코딩으로 빈 줄 보존, GREEN |
| F7 | `git status` 실패를 clean처럼 처리 | 종료값 확인 후 `NOT_RUN`, GREEN |
| F8 | 다음 프롬프트의 0-run 문구가 구현과 다름 | `UNVERIFIED` 계약으로 통일, GREEN |
| F9 | 감사 장부의 빈 줄 표현이 실제 계약과 어긋남 | 빈 레코드 손실 금지로 정정, GREEN |
| F10 | `gh` 부분 출력·필터 실패, dirty 변이 시험 누락 | 제품 경로 시험 추가, GREEN |
| F11 | 브랜치·로컬·원격 SHA 명령이 값 출력 뒤 실패해도 VERIFIED 가능 | 세 종료값 검사와 회귀 시험 추가, GREEN |
| F12 | 빈 필드 검사를 삭제해도 33개 시험 PASS | `:success`, `completed:` 추가, GREEN |
| F13 | 후속 레코드의 추가 콜론 검사를 약화해도 33개 시험 PASS | 정상 뒤 `completed:success:extra` 추가, GREEN |
| F14 | Claude V1 내용은 PASS였으나 최종 text byte 0/첫 줄 계약 위반 | 프롬프트 강화 후 새 세션 재실행, 유효 PASS |

→ F1~F14는 모두 현재 로컬 변경과 회귀 시험에서 해소됐습니다. 과거 PASS는 새 반례가 깨뜨린 범위에 대해 최종 근거로 재사용하지 않습니다.

### RED → GREEN

수정 전 직접 재현:

```text
in_progress:none + malformed              -> UNVERIFIED / exit 1 (잘못됨)
completed:failure + unknown:success       -> UNVERIFIED / exit 1 (잘못됨)
completed:success:extra                   -> UNVERIFIED / exit 1 (잘못됨)
빈 필드 검사 삭제 뒤 기존 33개 검사       -> PASS (시험 결함)
후속 추가 콜론 검사 약화 뒤 기존 33개 검사 -> PASS (시험 결함)
```

→ 조회 자체가 깨진 입력을 단순 불합격으로 낮추고, 두 구현 약화를 시험이 놓친 RED입니다.

수정 후 핵심 결과:

```text
acceptance-verified-sha.sh        CHECKED: 36  VERDICT: PASS
acceptance-principles-check.sh    CHECKED: 34  VERDICT: PASS
principles mutation              CHECKED: 48  VERDICT: PASS
빈 필드 검사 제거 변이            CHECKED: 36  VERDICT: FAIL
후속 콜론 검사 약화 변이           CHECKED: 36  VERDICT: FAIL
검증·집계 재결합 변이              CHECKED: 36  VERDICT: FAIL
```

→ 정상 구현은 GREEN이고, 일부러 약화한 구현은 RED로 뒤집힙니다.

### Claude Code V1

- 세션: `b80d0746-7822-464e-ab9f-0e9822515e29`
- 모델·CLI: `claude-sonnet-5`, Claude Code `2.1.245`
- 원시 JSONL SHA256: `6c88d7a3082646f1e0f51243b7a4b29dc60f7173ad69846b4888957c8490f2da`
- 최종 응답 SHA256: `ce509ab612e2ff6fa91ba77fe6739a53b3d49906e9bc16529c836449270e8bfc`
- 형식: byte 0부터 첫 줄 정확히 `VERDICT: PASS`
- 결과: 9종 약화 공격 차단, 구현 결함 0건
- 색인: `.omx/artifacts/claude-pr43-verdict-order-v1-final-2026-08-27.md`

Claude가 “34개 원칙 각각의 검사기가 pre-push·CI에 배선됐다”고 표현한 부분은 과장입니다. 34는 장부 항목이 하나의 원칙 검사기에 결속된 수이며, P23 배선은 CI 고정 명령과 pre-push 글로브 포함을 별도로 재현했습니다. 구현 PASS에는 영향이 없습니다.

### Codex V2

- 세션: `01a03fa8-4989-7fa2-a838-c2f31078f1e1`
- 모델·CLI: `gpt-5.6-sol` high, Codex CLI `0.148.0`
- 프롬프트 SHA256: `670e87008bb67eefb3ed2cf0f834ab6b93c90c4b0808ec30f91327daa593a39c`
- 사용량: `235,823 tokens`
- 결과: `VERDICT: PASS`, 구현 결함 0건, Claude 표현 과장 1건 교정
- 추가 공격: Claude의 9종에 검증·집계 한 루프 재결합을 더한 10종 모두 `VERDICT: FAIL`
- 색인: `.omx/artifacts/codex-pr43-verdict-order-v2-final-2026-08-27.md`
- 한계: `--ephemeral` 실행이라 별도 자식 JSONL은 보존되지 않았고 리더 PTY의 완료 출력과 exit 0을 회수했습니다.

### 넓은 로컬 게이트

최종 커밋 전 아래를 새로 실행해 모두 exit 0을 확인했습니다.

```text
history-scan-failclosed       CHECKED: 18
0-2-unreachable-content      CHECKED: 23
verify-ac-m                  CHECKED: 33
principles-check             CHECKED: 34
principles-mutations         CHECKED: 48
verified-sha                 CHECKED: 36
ci-step-integrity            CHECKED: 14
semantic-mutations           CHECKED: 10
verify.sh                    PASS
scan-history-secrets.sh      PASS
bash -n / shellcheck / diff  PASS
```

→ `scan-history-secrets.sh`는 도달 객체 4,968개에서 blob 1,641개를 전량 읽어 위반 0건이었습니다. `semantic-mutations`는 인수 검사 27개 각각에 5종 약화를 적용해 모두 차단했습니다. `verify.sh`, 변경 셸의 문법·ShellCheck warning, `git diff --check`도 모두 통과했습니다.

## codeaudit 반복 이력

- 같은 주제의 식별 가능한 과거 독립 감사 세션: `01a03b71-9413-78c3-ba2b-b72f800f671b`, `01a03d02-ca56-75d2-b9fb-9305af404375`, `01a03f01-5b17-7bf0-8510-a8212746998d`
- 직전 사용자 요청 `$codeaudit 내용 검토...`와 이번 `$humanreview $codeaudit...`를 포함하면 의미상 관련 감사 요청은 이번이 5번째입니다.
- 현재 확인 가능한 기록에서 이번 문장과 정확히 같은 문구의 반복은 0회입니다.
- 의미상 같은 감사가 반복된 이유는 새 반례가 이전 PASS를 뒤집었기 때문이며, 단순 중복 질문으로 축소하지 않습니다.

## 남은 위험·원격 상태

- 원격 후보에는 아직 이번 로컬 커밋이 없고 새 SHA의 GitHub Actions가 없습니다.
- 따라서 로컬 humanreview는 `APPROVE`, 원격 병합 판단은 `REQUEST_CHANGES`입니다.
- Claude의 36건 숫자 자동 결속 부재 관찰은 비차단 후속 개선입니다. 현재 SOT·파생 장부·실행 결과는 모두 36으로 일치합니다.
- push, PR 본문 수정, 병합, PR #29 종료는 수행하지 않았습니다.

## 다음 `$strict` 실행문

- 경로: `.omx/artifacts/pr43-strict-next-prompt-2026-08-27.md`
- SHA256: `645767c95686570845084688672b966f3802e967009f0c902185e38f00fee072`
- Strict brief-lint: 위반 0건
- 자동 실행 경계: 로컬 안전 커밋 뒤 `git push -u origin task/pr29-history-scan-final-20260825`를 정확한 수동 명령으로 출력하고 `HUMAN_ACTION_REQUIRED`에서 멈춤

## 제출 직전 §8 셀프 감사

- 결론에 전문용어가 있나? 아니오
- `→` 해석 없는 출력·코드·표가 있나? 아니오
- 결론에 결정할 사항이 빠졌나? 아니오
- 결정에 버린 길·대가가 빠졌나? 아니오
- `file:line`의 역할 설명이 빠졌나? 최종 응답에서 역할과 함께 제시
- 쉽게 쓰며 증거·수치·한계를 뺐나? 아니오
- 초등학생 비유로 내용을 깎았나? 아니오
- 건너뜀·미확인·실패 후 재시도가 빠졌나? 아니오
- 추정을 확인된 사실처럼 썼나? 아니오
