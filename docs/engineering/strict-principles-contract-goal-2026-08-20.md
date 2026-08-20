# Strict 원칙 직접 로드·강제 배선 goal — 2026-08-20

## 결론

현재 작업트리 기준 목표는 **연결됨**이다. `docs/sot/coding-principles.md`를 정본으로, `docs/sot/principles.yaml`을 기계 장부로 Strict가 매 실행 직접 읽고 검사한다. 로컬 pre-push와 CI가 검사기를 명시적으로 실행하며, 실제 Claude V1과 새 맥락 Codex V2까지 최종 PASS했다.

이 PASS는 P1~P22의 모든 제품 기능이 새로 구현됐다는 뜻이 아니다. 32개 원칙이 현재 정본에서 빠짐없이 추출되어 Strict 실행 계약·검사·pre-push·CI에 강제로 편입됐음을 뜻한다.

## 시작 상태와 main 기준

- 시작 기준: `HEAD=main=origin/main=7bd3298695c93e0e60bdabd2500840da47c4db05`.
- 시작 당시 `docs/sot/coding-principles.md`는 존재했지만 Strict 직접 로드 계약이 없었다.
- `docs/sot/principles.yaml`과 `scripts/acceptance-principles-check.sh`는 main 실행 경로에 없었고 최초 검사 시 exit `127`, 즉 `NOT_RUN`이었다.
- `worktrees/strict-principles-yaml` 초안은 참고만 했고 완료·병합 구현으로 간주하지 않았다.
- `.omx/project-memory.json`, Claude memory, 과거 대화와 보고서는 정본으로 사용하지 않았다.
- 위험등급은 **L3**다. SOT, 전역 Strict 스킬 2개, pre-push, CI, mechanism registry를 함께 바꾼다.
- push·PR·병합·배포는 이 작업 범위가 아니다.

## 결정 카드

> **무엇을** — 장부의 `status`를 개별 제품 기능 완성도가 아니라 현재 정본 문구와 Strict·검사·pre-push·CI 배선의 검증 상태로 정의한다.
> **왜** — 이번 목표는 원칙 계약의 직접 로드와 fail-closed 실행 배선이다.
> **버린 길** — 별도 worktree 초안의 제품 구현 재고표를 그대로 병합하는 안은 정상 저장소에서도 영구 실패를 남겨 기각했다.
> **대가** — 장부 PASS만으로 모든 제품 원칙 구현 완료를 주장할 수 없다.
> **되돌리기** — 신규 파일과 호출 줄, registry 항목, 두 Strict의 공통 마커 블록을 역패치한다.

## T 계약

### 입력

- 정본: `docs/sot/coding-principles.md`
- 기계 장부: `docs/sot/principles.yaml`
- 배선: `hooks/pre-push`, `.github/workflows/verify.yml`, `docs/sot/mechanism-registry.yaml`
- 검사기: `scripts/acceptance-principles-check.sh`
- 실행 스킬: `/Users/kangsangmo/.codex/skills/strict/SKILL.md`, `/Users/kangsangmo/.claude/skills/strict/SKILL.md`
- 선택 보조정보: OMX/Claude memory, 과거 대화·보고서

### 출력

- 각 필수 검사는 `PASS`, `FAIL`, `NOT_RUN`과 검사 건수를 구분한다.
- 정상 장부는 exit `0`, `VERDICT: PASS`, `CHECKED: 32`다.
- 계약 위반은 exit `1`, `FAIL`이다.
- 실행 환경 때문에 판정할 수 없으면 exit `2`, `NOT_RUN`이다.
- 검사 대상 0개는 PASS가 아니다.

### 오류·경계

- 파일 누락·빈 파일·YAML 파싱 실패·필수 필드 누락·중복/누락/알 수 없는 ID는 FAIL이다.
- 모든 항목은 `id`, `principle`, `mechanism_expected`, `mechanism_found`, `status`, `evidence`를 가진다.
- `mechanism_found` 원소는 정확한 `path/check/stages` 구조와 실존 파일을 가져야 한다.
- YAML 원칙 문구는 정본에서 추출한 문구와 바이트 단위로 같아야 한다.
- pre-push와 CI는 `bash scripts/acceptance-principles-check.sh`를 직접 실행한다.
- CI의 해당 단계에 `if`, `continue-on-error`, `|| true`, `if: exists`가 있으면 FAIL이다.
- 직접 작성 코드 파일은 500줄까지 PASS, 501줄부터 FAIL이다.
- 검사와 fixture는 원본 저장소를 바꾸지 않아야 한다.

## EARS 인수 기준

1. **정본·장부 일치** — 원칙 검사 실행 시 현재 저장소의 두 파일을 직접 읽고 P1~P22, §1-B-1~5, V-1~5의 32개 ID와 문구를 일치시킨다.
2. **장치 구조·실존** — 모든 mechanism의 필드, 경로, 검사기, stage를 검증한다.
3. **명시적 실행 배선** — pre-push와 CI의 활성 실행 줄 및 실패 전파를 검증한다.
4. **Strict 직접 로드** — memory 성공을 SOT 로드 성공으로 대체하지 않는다.
5. **플랫폼 대칭성** — 공통 원칙 계약은 byte-identical이고 엔진 순서만 다르다.
6. **판정 fail-closed** — V1 FAIL/NOT_RUN 또는 V2 NOT_RUN은 최종 PASS가 아니다.
7. **RED→GREEN** — 누락 검사기 RED, 정상·고장 fixture, 500/501 경계를 실행한 뒤 같은 원명령을 GREEN으로 만든다.

## 필수 반례와 확장 반례

1. `principles.yaml` 삭제 → FAIL
2. `coding-principles.md` 삭제 → FAIL
3. YAML 문법 오류 → FAIL
4. 원칙 ID 하나 삭제 → FAIL
5. 중복 ID → FAIL
6. mechanism 경로 미존재 → FAIL
7. CI 실행 줄 삭제 → FAIL
8. 검사기 파일 삭제 → FAIL/NOT_RUN을 suite가 FAIL로 집계
9. 검사 대상 0개 → FAIL
10. `|| true` 또는 `continue-on-error` → FAIL
11. V1 FAIL을 최종 PASS로 기록 → FAIL
12. V1 FAIL 뒤 V2 NOT_RUN → FAIL
13. Codex/Claude 공통 계약 불일치 → FAIL
14. memory 삭제·잘림에서도 현재 SOT 직접 로드 → PASS
15. 주석·echo·최상위 exit 뒤·`if false` collector 미끼 → FAIL
16. 고정 Git 신원/커밋 지문에서만 정상 실행 → FAIL
17. 고정 임시경로 접두사에서만 정상 실행 → FAIL
18. runtime marker/output/exit만 위조하거나 실패를 삼킴 → FAIL
19. 500줄 → PASS, 501줄 → FAIL

## Harness 게이트

- G0: 기준 SHA, 작업트리, 별도 worktree 초안, 최초 RED 기록.
- G1: 이 문서의 T/EARS/counter-AC/오류/경계 고정.
- G2: `mktemp` 격리 사본에서 실패 반례 실행.
- G3: 최소 구현으로 원명령 GREEN.
- G3.5: Strict → 검사기 → pre-push/CI → registry 경로를 정적·런타임으로 증명.
- G4: 40개 원칙 mutation, 31개 registry fixture, 500/501, 전체 검증 실행.
- G5: 실제 Claude CLI V1과 새 맥락 Codex V2 실행.
- G6: 원본 작업트리와 전역 Strict guard 무오염 확인.

## G/V1/V2/T 검증 장부

| 단계 | 주체 | 상태 | 증거 |
|---|---|---|---|
| T | G Codex | PASS | 이 goal의 입력·출력·오류·경계·반례 |
| G | Codex | PASS | core `32`, mutation `40`, registry `6`, registry fixture `31` |
| V1 | Claude CLI | PASS | session `fc479ae5-4368-47d5-91d1-65c0e75fde6e`; 최종 exit `0`, API 오류 없음 |
| V2 | 새 맥락 Codex | PASS | `/root/strict_principles_v2_final_r2`; 독립 재현·재공격 |

Codex판 엔진 순서는 `G=Codex → V1=Claude → V2=Codex`, Claude판은 `G=Claude → V1=Codex → V2=Claude`다. 공통 계약은 byte-identical이다.

## 최종 증거

- G: `docs/engineering/strict-principles-g-evidence-2026-08-20.md`
- V1 전체 판정 원문: `docs/engineering/strict-principles-v1-verdict-2026-08-20.md`
- V2 원문: `docs/engineering/strict-principles-v2-verdict-2026-08-20.md`
- 기계 판정: `docs/engineering/strict-principles-verdict-2026-08-20.yaml`
- 최종 보고: `docs/engineering/strict-principles-verification-2026-08-20.md`

## 남은 FAIL/NOT_RUN

없음. 최종 ledger 검사는 G/V1/V2/T 모두 PASS일 때만 이 문장을 유지할 수 있다.

## 롤백

1. 신규 장부·검사·fixture·검증 문서를 제거한다.
2. `hooks/pre-push`, `.github/workflows/verify.yml`, mechanism registry와 검사기의 이번 추가 줄만 역패치한다.
3. 두 Strict의 `STRICT_PRINCIPLES_CONTRACT` 공통 블록을 제거한다.
4. 원칙 검사기 제거 전 CI·pre-push 참조를 먼저 제거해 고아 호출을 남기지 않는다.
