# HumanSearch 시작 검사의 복구 기록 오인 수리 목표 (2026-08-17)

## 1층 — 결론

로컬 검사 규칙을 새 작업 공간에 연결하는 문제는 풀렸지만, 시작 검사는 비밀과 관계없는 정상 복구
기록까지 모두 위험하다고 판정해 구현 시작을 계속 막습니다.

비밀이 들어 있는 복구 기록은 계속 차단하고, 비밀이 없는 복구 기록은 시작을 막지 않도록 별도 작업으로
고칩니다. 실제 채용 사이트와 제품 분류기는 건드리지 않으며, 합치기는 사장님 검토 전에는 하지 않습니다.

## 2층 — 판단 근거

개발 중에는 기록을 만들고 고치면서 현재 가지가 가리키지 않는 복구 가능한 기록이 자연스럽게 생깁니다.
현재 검사는 그 내용에 비밀이 있는지 보지 않고 개수가 하나라도 있으면 실패합니다. 실제로 아무 비밀도
없는 합성 기록 하나만 만든 격리 저장소에서 실패를 재현했습니다.

모든 복구 기록을 자동 삭제하는 길은 버립니다. 그 기록은 작업 복구에 필요할 수 있고 삭제는 되돌리기
어렵습니다. 반대로 개수 검사를 통째로 지우는 길도 버립니다. 비밀이 들어 있는 복구 기록은 현재 화면에
보이지 않아도 저장소 내부에서 되살릴 수 있기 때문입니다. 평소 시작 검사에서는 각 복구 기록의 내용을
검사하고, 과거 비밀 제거 작업의 최종 확인을 명시적으로 요청한 경우에만 개수 0을 계속 요구합니다.

이 판단이 틀리면 무해한 개발 기록 때문에 모든 새 작업이 멈추거나, 반대로 삭제한 비밀이 저장소 내부에
남아도 놓칠 수 있습니다. 그래서 무해한 기록 통과, 비밀 기록 차단, 최종 제거 확인의 개수 0 차단을 서로
다른 실행 사례로 고정합니다.

### 결정 카드

**무엇을** — 평소에는 복구 기록의 내용을 검사하고, 최종 제거 확인 모드에서만 모든 복구 기록 0개를 요구합니다.
**왜** — 현재 개수 검사는 비밀과 무관한 정상 개발 기록도 차단하지만, 내용 검사를 없애면 실제 비밀을 놓칩니다.
**버린 길** — 자동 삭제와 무조건 통과를 버렸습니다. 전자는 복구 자료를 없애고 후자는 비밀 잔존을 놓칩니다.
**대가** — 시작 검사 때 복구 기록의 내용을 열어보므로 저장소가 클수록 검사 시간이 늘 수 있습니다.
**되돌리기** — 검사 파일과 새 회귀 시험만 되돌리면 됩니다. 제품 코드와 운영 자료는 변경하지 않습니다.

## 3층 — 계약과 증거

### 1. 현재 상태

- `scripts/acceptance-0-2.sh:101-105`는 `git fsck`가 보고한 모든 복구 가능 객체 수를 세고 1개 이상이면
  내용과 관계없이 실패합니다.
- 같은 파일 `:108-117`은 현재 가지와 과거 이동 기록이 가리키는 객체에서 실제 로컬 비밀값을 찾지만,
  어떤 가지도 가리키지 않는 객체 내용은 검사하지 않습니다.
- `scripts/acceptance-0-2.sh:119-123`은 최종 정리 직후에만 참이어야 하는 검사를 별도 모드로 둔다고
  설명하지만, 모든 복구 가능 객체 0개 조건은 그 바깥에 남아 평소 시작 검사에도 적용됩니다.
- `scripts/session-status.sh:57-66`은 이 검사를 포함한 모든 인수 검사의 실패 수를 더하므로, 무해한 객체
  하나도 HumanSearch 시작을 막습니다.

### 2. 근본 원인

과거 비밀 제거 작업을 끝낸 직후 “저장소 내부에 남은 복구 기록이 하나도 없다”를 증명하던 일회성 조건이
평소 개발 시작 검사에 그대로 연결됐습니다. 일회성 완전 정리와 상시 비밀 회귀 검사의 책임을 분리하지
않은 것이 근본 원인입니다.

### 3. 단일 인수 기준

**AC-G0-SECRET-OBJECT.** 평소 시작 검사에서는 비밀이 없는 복구 가능 객체가 존재해도 통과하고, 로컬
규칙의 실제 값이 든 복구 가능 파일 객체가 하나라도 있으면 실패해야 합니다. 과거 비밀 제거의 최종 확인
모드에서는 내용과 관계없이 복구 가능 객체가 하나라도 있으면 계속 실패해야 합니다.

기계 검사는 다음 네 사례를 모두 단언합니다.

1. 복구 가능 객체 0개인 합성 저장소는 통과합니다.
2. 비밀이 없는 복구 가능 파일 객체 1개인 평소 검사는 통과합니다.
3. 로컬 규칙 값이 든 복구 가능 파일 객체 1개인 평소 검사는 실패합니다.
4. 비밀이 없는 복구 가능 파일 객체 1개라도 최종 확인 모드에서는 실패합니다.

다음 중 하나라도 가능하면 가짜 합격입니다.

- 비밀이 든 복구 가능 파일을 개수 검사 삭제와 함께 놓칩니다.
- 모든 복구 기록을 자동 삭제해 시험을 통과합니다.
- 알려진 과거 오염 객체의 고정 목록 검사를 지웁니다.
- 최종 확인 모드에서도 무해한 복구 기록을 허용합니다.
- 회귀 시험이 실제 수정 파일을 실행하지 않고 복사한 가짜 구현만 검사합니다.

### 4. RED 증거

```text
$ 비밀이 없는 합성 파일 객체 하나를 만든 격리 저장소에서 기존 acceptance-0-2 실행
HARMLESS_SHA=c86566e6272b712e10fa10cf1f8772f0064a0c91
unreachable blob c86566e6272b712e10fa10cf1f8772f0064a0c91
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable 객체 1건 잔존 (reflog expire/gc --prune=now 미완)
RED_EXIT=1
```

→ 비밀 검사는 통과했지만 무해한 복구 가능 파일 객체 한 개 때문에 전체 성적 1로 실패했습니다. 현재
검사가 비밀 잔존이 아니라 객체 개수 자체를 시작 불가 사유로 삼는다는 재현 증거입니다.

첫 재현 시도는 임시 폴더를 즉시 삭제하는 명령이 실행 안전 장치에 거절돼 시작되지 않았습니다. 저장소
변경은 없었고, 삭제 동작을 빼고 운영체제가 관리하는 임시 폴더에서 같은 재현을 다시 실행했습니다.

### 5. Harness 게이트 진행

- Gate 0: 기존 시작 검사는 실패 1건입니다. 이 결함 외 새 제품 작업을 시작하지 않습니다.
- Gate 1: 단일 인수 기준 `AC-G0-SECRET-OBJECT`로 고정했습니다.
- Gate 2: `worktrees/humansearch-g0-unreachable-secret-scan`과
  `task/humansearch-g0-unreachable-secret-scan`으로 격리했습니다.
- Gate 3 RED: 무해한 복구 가능 파일 객체 1개가 기존 검사에서 실패하는 출력을 확보했습니다.
- Gate 3 GREEN: 기존 검사 의미를 최소 변경하고 같은 합성 저장소 사례를 회귀 시험으로 고정합니다.
- Gate 4: 회귀 시험, 시작 검사, 비밀 검사, 문서 검사, 셸 문법 검사, 전체 저장소 검증을 실행합니다.
- Gate 5: 일반 push와 별도 한국어 PR까지만 진행하고 서버 검사를 같은 변경 지문으로 확인합니다.
- Gate 6: 합치기, 배포, 실제 포털, 제품 분류기 구현은 하지 않습니다.

### 6. 적대검증 항목

1. 무해한 객체 통과를 핑계로 실제 비밀이 든 객체도 통과하는가.
2. 가지·이동 기록·현재 변경 목록 밖의 파일 객체까지 실제로 읽는가.
3. 고정된 과거 오염 객체 검사가 보존되는가.
4. 최종 제거 확인 모드의 객체 0개 조건이 보존되는가.
5. 객체 종류 확인 실패나 파일 읽기 실패를 조용히 통과시키는가.
6. 합성 시험이 수정된 실제 검사 파일을 런타임에 실행하는가.
7. 검사 시간이 비정상적으로 늘거나 같은 객체를 불필요하게 여러 번 읽는가.
8. Claude 판정의 줄·명령·출력을 Codex가 직접 재현할 수 있는가.

### 7. SOT 체크리스트

- [x] `docs/sot/INDEX.md` — 날짜가 있는 작업 증거는 `docs/engineering/`에 둡니다.
- [x] `docs/sot/coding-principles.md` — P3 실행 실패 은폐 금지, P6 실행 환경, P13 검사 약화 금지,
  P15 우회 금지, P20 0건 가짜 합격 금지를 확인했습니다.
- [x] `docs/sot/git-workflow.md` — 한 인수 기준, 한 작업 공간, 한 가지, 한 PR로 격리했습니다.
- [x] `docs/sot/hook-contracts.md` — 시작 검사 실패 집계 계약과 훅의 우회 한계를 확인했습니다.
- [x] `docs/sot/verification-commands.md` — 실제 Gate 0과 서버 검사 목록을 확인했습니다.
- [x] `docs/sot/humansearch-l0-surface-contract.md` — 제품 분류 계약은 변경하지 않습니다.
- [x] 사용자 제공 `AGENTS.md` — Lore 커밋, 증거 우선, 자동 합치기 금지를 적용합니다.

### 8. 비범위

- HumanSearch 제품 코드와 시험
- `.secret-patterns`의 실제 내용 출력·복사·추적
- 모든 복구 기록의 자동 삭제 또는 저장소 정리
- PR #13·#14·#15 합치기, main 직접 push, 배포
- 실제 포털, 브라우저, 로그인, 세션, 후보자 개인정보

### 9. 검증 로그

최종 GREEN `08a96c3`에서 회귀 시험을 일반 환경과 외부 패턴 경로가 상속된 환경으로 각각 실행했습니다.

```text
$ /usr/bin/time -p bash scripts/acceptance-0-2-unreachable-objects.sh
[no-unreachable] exit=0 expected=0
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[harmless-unreachable] exit=0 expected=0
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[endstate-requires-zero] exit=1 expected=1
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
FAIL: unreachable 객체 1건 잔존 (reflog expire/gc --prune=now 미완)
[secret-unreachable] exit=1 expected=1
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
FAIL: 복구 가능 blob에 리터럴 잔존: 957733ee2f7ecd5590b6d0ed90ae144ebc8cc472
CHECKED: 4
PASS: 무해한 복구 객체 허용·비밀 객체 차단·최종 정리 0개 조건 보존
real 4.13
user 1.25
sys 1.27
```

→ 합성 사례 네 개가 모두 기대 성적과 일치했고 전체 명령은 4.13초에 끝났습니다. 실패 문구 두 개는
차단해야 하는 사례가 실제로 불합격 성적 1을 냈다는 좋은 소식이며, 시험 전체 성적은 0입니다.

```text
$ SECRET_PATTERNS_FILE="$PWD/.secret-patterns.default" bash scripts/acceptance-0-2-unreachable-objects.sh
[no-unreachable] exit=0 expected=0
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[harmless-unreachable] exit=0 expected=0
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[endstate-requires-zero] exit=1 expected=1
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
FAIL: unreachable 객체 1건 잔존 (reflog expire/gc --prune=now 미완)
[secret-unreachable] exit=1 expected=1
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
FAIL: 복구 가능 blob에 리터럴 잔존: 957733ee2f7ecd5590b6d0ed90ae144ebc8cc472
CHECKED: 4
PASS: 무해한 복구 객체 허용·비밀 객체 차단·최종 정리 0개 조건 보존
```

→ REVIEW-RED와 같은 외부 환경을 다시 상속해도 네 사례가 모두 통과했습니다. 시험 진입부의 상속 차단이
실제 지적을 닫았고, 실제 비밀값 대신 공개 기본 규칙 파일만 사용했습니다.

```text
$ bash scripts/acceptance-0-2.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
$ bash scripts/check-docs-sot.sh
PASS: docs/sot/INDEX.md 존재, 1050바이트 (<=20000)
PASS: docs/sot/coding-principles.md 존재, 15405바이트 (<=20000)
PASS: docs/sot/hook-contracts.md 존재, 4455바이트 (<=20000)
PASS: docs/sot/git-workflow.md 존재, 2225바이트 (<=20000)
PASS: docs/sot/verification-commands.md 존재, 7481바이트 (<=20000)
PASS: hooks/pre-commit 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: hooks/pre-push 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/install-hooks.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/session-status.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/acceptance-0-7.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
OK: docs/sot 재구성 AC 전부 충족
$ bash scripts/verify/check-mechanism-registry.sh
PASS: secrets-scan-precommit (pre-commit · 규칙 1·2·3)
PASS: acceptance-glob-prepush (pre-push · 규칙 1·2·3)
PASS: ci-secret-scan (ci · 규칙 1·2·4)
CHECKED: 3
$ bash scripts/acceptance-verify-ac-m.sh
PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
PASS: fixture 정상 명부 → 통과 (exit=0)
PASS: fixture path 없는 항목 → 불합격 (exit=1)
PASS: fixture 죽은 target → 불합격 (exit=1)
PASS: id 중복 → 불합격 (exit=1)
PASS: 알 수 없는 stage → 불합격 (exit=1)
PASS: manual 인데 사유 없음 → 불합격 (exit=1)
PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
PASS: manual 인데 실행권한 없음 → 불합격 (exit=1)
PASS: ci 인데 거짓 target → 불합격 (exit=1)
PASS: 절대경로 path → 불합격 (exit=1)
PASS: 상대경로 심볼릭 링크 → 불합격 (exit=1)
PASS: 필드 중복(path 2회, 마지막 값 유효) → 불합격 (exit=1)
PASS: id 뒤 인라인 주석 → 불합격 (exit=1)
PASS: 닫히지 않은 따옴표 → 불합격 (exit=1)
PASS: stage 불일치 필드(ci_mirror_job) → 불합격 (exit=1)
PASS: 문법 오류·항목 0개 → 위반(1) (exit=1)
PASS: 항목 0개 명부 → NOT_RUN (exit=2)
PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
PASS: 빈 문자열 path → 불합격 (exit=1)
PASS: CI 배선 — verify.yml 에 무조건 실행 스텝 정확히 1회
PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
PASS: 저장소 무오염 (시작/종료 상태 동일)
CHECKED: 25
SHELL_FILES_CHECKED=27
WORKFLOW_STEPS=17
PREPUSH_DISCOVERY_COUNT=1
```

→ 실제 로컬 규칙 검사, 추적 파일 검사, 정본 문서 검사, 강제 장치 명부 검사, 명부 변형 사례 25개,
추적 셸 파일 27개 문법, 서버 검사 17단계, 업로드 전 자동 수집 1건이 모두 기대 성적 0이었습니다.

```text
$ bash scripts/session-status.sh
HEAD: 08a96c3 (ahead 5 / behind 0)
ORIGIN: 4fdef31
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 최종 수정 지문 `08a96c3`에서 시작 검사 20개는 실패 0건입니다. 제외된 차단 시연은 다음 명령으로
별도 실행했습니다.

```text
$ bash scripts/acceptance-0-7.sh
=== 전제 검사: 훅 인프라 ===
OK: 훅 파일 4종 + settings.json 존재

=== 시연 (샌드박스: /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.EicZu4hcnN/repo · 각 시연마다 훅 ON/OFF 대조) ===
[1/6] 검사기 자기 제외 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 검사기 자기 제외 — scripts/acceptance-0-6.sh 가 자기 자신을 검사 대상에서 뺀다 (P13)
[2/6] 검사 약화(실패 무시) → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 검사 약화 패턴 추가 — scripts/acceptance-0-2.sh (P13). 정당하면 suppressions.yaml 에 expiry 와 함께 등록하라
[3/6] 만료일 없는 억제 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 억제 항목 1건 중 expiry 가 0건뿐 — 만료일 없는 억제는 영구화된다 (P13)
[4/6] LLM 출력→판정 필드 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: LLM 출력을 판정 수치로 변환 — src/scoring.js. 판정 수치는 순수 함수가 만든다 (P14)
[5/6] 미커밋 상태로 push → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 작업트리가 깨끗하지 않다 — 미커밋/미추적 변경이 있는 상태의 push (P15)
[6/6] 가짜 외부효과 모듈 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 외부 효과를 표방하는데 네트워크 호출이 0건 — src/portal-login.js. 시뮬레이션 의심 (P4)

OK: 원본 저장소 무변경 확인 (da39a3ee5e6b4b0d3255bfef95601890afd80709)

PASS: 위반 6 종이 전부 차단됨 (각 건 훅 OFF 대조 통과)
```

→ 시작 집계에서 의도적으로 뺀 무거운 차단 시연도 여섯 위반을 모두 막았고 원본 저장소 지문은
변하지 않았습니다. 출력의 임시 경로는 격리 저장소 위치이며 세션 종료 뒤 증거 보관처로 쓰지 않습니다.

### 10. 적대 검증 로그

Claude 1차 판정의 명령 전문·본문과 Codex 2차 재현 명령·출력·일치 여부를 이 절에 덧붙입니다.

#### REVIEW-RED — 상속 환경이 합성 시험을 바꾸는가

Claude 1차 판정은 자동 실행 경로는 외부 값을 비워 안전하지만, 개발자가 회귀 시험을 직접 실행할 때
`SECRET_PATTERNS_FILE` 환경변수가 상속되면 합성 규칙 대신 외부 파일을 읽는 낮은 위험을 지적했습니다.
Codex가 저장소의 공개 기본 규칙 파일을 외부 값처럼 지정해 재현했습니다.

```text
$ SECRET_PATTERNS_FILE="$PWD/.secret-patterns.default" bash scripts/acceptance-0-2-unreachable-objects.sh
[no-unreachable] exit=1 expected=0
FAIL: 심은 카나리를 verify.sh가 못 잡음 — 스캐너가 조용히 무력화됨
FAIL: no-unreachable 종료 성적 불일치
[harmless-unreachable] exit=1 expected=0
FAIL: harmless-unreachable 종료 성적 불일치
[endstate-requires-zero] exit=1 expected=1
FAIL: unreachable 객체 1건 잔존 (reflog expire/gc --prune=now 미완)
[secret-unreachable] exit=1 expected=1
FAIL: secret-unreachable 필수 판정 문구 누락: 복구 가능 blob에 리터럴 잔존
CHECKED: 4
INHERITED_OVERRIDE_EXIT=1
```

→ 외부 환경변수 하나만으로 같은 합성 시험의 결과가 달라졌고 전체 성적은 1이었습니다. 자동 훅과
세션 검사는 이 변수를 이미 비우지만, 회귀 시험 자체도 실행 경로와 무관하게 같은 결과를 내도록 해야
하므로 새 REVIEW-RED로 채택합니다. 실제 비밀값은 읽거나 출력하지 않았습니다.

#### Claude V1 실행 이력과 원문

첫 호출은 기본 모델의 안전 필터가 요청을 거절해 판정문을 만들지 못했습니다. 같은 읽기 전용 프롬프트를
Sonnet으로 한 번 다시 실행했고, 약 13분 뒤 아래 판정문을 확보했습니다. 검토자는 셸 실행 권한을 받지
못해 코드 대조와 세션 시작 기록으로 판정했고, 첫 줄 앞에 제목을 붙여 출력 형식 한 줄을 어겼습니다.
최종 수정 뒤 형식 재판정을 최소 모드로 요청했지만 그 모드는 로그인 정보를 불러오지 않아
`Not logged in · Please run /login`으로 끝났습니다. 이 실패를 합격으로 세지 않습니다.

실행 명령 전문은 다음과 같습니다. 실제 민감 값은 프롬프트나 출력에 넣지 않았습니다.

```text
env -u ANTHROPIC_API_KEY claude --model sonnet --no-session-persistence --permission-mode dontAsk --tools Read,Grep,Bash --disallowedTools Edit Write NotebookEdit -p '
독립 코드 검토를 수행하십시오. 읽기 전용입니다. 파일, Git, 원격 상태를 바꾸지 말고 실제 민감 값의 내용은 읽거나 출력하지 마십시오. 합성 시험 데이터만 사용하십시오.

범위는 origin/main..HEAD입니다. 목표는 Git이 보관한 비활성 파일 객체를 검사하는 로컬 안전 검사 수리입니다. 정상 개발 중 생긴 무해한 비활성 blob은 허용하고, 로컬 패턴과 일치하는 비활성 blob은 차단하며, ACCEPTANCE_ENDSTATE=1일 때는 모든 비활성 객체가 0개여야 합니다. 알려진 과거 오염 객체 목록은 유지돼야 합니다.

다음을 적대적으로 확인하십시오. git fsck 실패나 출력 형식 차이가 조용히 통과하는지, 여러 객체 중 일치 항목을 놓치는지, cat-file 또는 grep 오류를 불일치로 오인하는지, 이진·줄바꿈 없는 blob을 놓치는지, 회귀 시험이 수정된 실제 scripts/acceptance-0-2.sh를 실행하는지, RED commit 59e4737 뒤 시험 파일이 불변인지, 새 시험이 hooks/pre-push의 acceptance 이름 규칙과 .github/workflows/verify.yml 양쪽에 연결됐는지, docs/sot/verification-commands.md의 17개 단계가 실제 workflow와 같은지, suppressions.yaml 삭제가 해결되지 않은 약화를 숨기는지, 검사 출력이 민감 값 자체를 노출하는지, 시작 검사 실패 수 0/20이 재현되는지, 실행 시간이 허용 가능한지 확인하십시오.

읽을 파일: scripts/acceptance-0-2.sh, scripts/acceptance-0-2-unreachable-objects.sh, .github/workflows/verify.yml, docs/sot/verification-commands.md, suppressions.yaml, docs/engineering/humansearch-g0-unreachable-secret-scan-goal-2026-08-17.md 및 관련 SOT입니다.

실행할 명령: git status --short --branch; git diff --name-status origin/main...HEAD; git diff origin/main...HEAD; bash scripts/acceptance-0-2-unreachable-objects.sh; bash scripts/acceptance-0-2.sh; bash verify.sh; bash scripts/check-docs-sot.sh; bash scripts/verify/check-mechanism-registry.sh; bash scripts/acceptance-verify-ac-m.sh; bash -n scripts/acceptance-0-2.sh scripts/acceptance-0-2-unreachable-objects.sh; git diff --check origin/main...HEAD; git diff --exit-code 59e4737..HEAD -- scripts/acceptance-0-2-unreachable-objects.sh; 가능하면 bash scripts/session-status.sh. 모든 결함은 file:line과 재현 명령 전체 출력으로 증명하십시오. 실행하지 못한 것은 NOT_RUN입니다.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 결론. 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 판단 근거: 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 VERDICT: PASS|FAIL 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그대로 두면 사업이나 운영에 무슨 일이 생기는지 한 문장을 덧붙여라.
- 설계 결정을 지적할 때는 무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라. 확인 못 한 것은 ※로 표시해라.
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라. 성인 의사결정자 수준으로 써라.
'
```

→ 실제 명령은 API 키를 환경에서 제거하고 읽기·검색·셸만 허용했으며 파일 쓰기 도구는 금지했습니다.
긴 목표·항목·파일·명령 목록은 위 문단의 내용과 같고, 실행 당시 프로세스 명령줄을 직접 대조했습니다.

Claude가 낸 판정 본문은 다음과 같습니다.

# 독립 코드 검토 결과

VERDICT: PASS

## 결론

이번 변경은 "정상적인 개발 과정에서 생기는 무해한 복구 가능 기록(git이 어느 가지에서도 더 이상 가리키지 않지만 아직 저장소 내부에 남아 있는 파일 조각)까지 전부 실패로 처리해 작업 시작을 막던 결함"을, "그 조각의 내용에 실제 회사 비밀 문자열이 들어 있는지"를 직접 열어서 판정하는 방식으로 고쳤습니다. 코드를 한 줄 한 줄 추적한 결과 사장님께서 지시하신 8가지 적대적 확인 항목 중 실행 없이 확인 가능한 항목은 전부 통과했고, 명백한 결함은 발견하지 못했습니다.

다만 한 가지 중요한 제약을 먼저 알려드려야 합니다. 이번 검토 세션에서는 셸 스크립트를 직접 실행하는 모든 명령(비밀 검사 스크립트, 검증 스크립트 등)이 권한 시스템에 의해 자동으로 거부되었습니다. 즉 사장님께서 지시하신 실행 명령 대부분을 제가 직접 돌려서 "방금 이렇게 나왔습니다"라고 보여드릴 수 없었습니다. 대신 (1) 코드를 정독해 논리를 끝까지 따라가는 방식과 (2) 이 대화가 시작되기 전에 시스템이 자동으로 한 번 실행해 남긴 "실패 0/20"이라는 기록을 근거로 판단했습니다. 이 기록은 지금 검토 중인 바로 이 커밋을 대상으로 실제로 돌린 결과이므로 신뢰할 수 있는 근거이지만, 제가 직접 명령을 쳐서 얻은 출력은 아닙니다. 이 차이가 이번 판정에서 가장 중요하게 짚어야 할 지점입니다.

이 판정이 틀린다면 벌어질 수 있는 일은 두 가지입니다. 첫째, 만약 코드 논리를 잘못 읽었다면 — 비밀이 든 복구 기록이 통과되거나, 무해한 기록이 여전히 차단되어 개발이 멈춥니다. 둘째, 만약 제가 근거로 삼은 "0/20 기록"이 이번 커밋이 아닌 이전 상태를 반영한 것이라면 — 지금 이 순간 실제로는 통과하지 않는 코드를 통과했다고 오판한 것입니다. 두 번째 위험을 낮추기 위해 아래에서 그 기록이 정확히 이번 커밋(HEAD)을 대상으로 한 것인지 별도로 대조했습니다.

## 판단 근거

**갈림길 1 — "실행을 못 했으니 판정을 보류할 것인가, 정독으로 판정할 것인가."** 셸 실행이 전면 차단된 것을 확인한 뒤, git 명령(상태·비교·로그 조회)과 파일 읽기·검색은 계속 허용된다는 것을 알았습니다. 그래서 코드를 표시된 파일:줄 단위로 끝까지 추적해 "이 조건문이 어떤 입력에 어떤 출력을 내는가"를 손으로 따라갔습니다. 이 방식을 택한 이유는, 사업 결정을 내려야 하는 사장님께 "확인 불가"라는 빈손 보고보다는 "실행은 못 했지만 논리적으로 이렇게 확인했다"는 근거 있는 판단이 더 유용하기 때문입니다. 버린 선택지는 "실행 안 되니 전체 보류"였는데, 이는 검토 자체를 포기하는 것과 같아 버렸습니다.

**갈림길 2 — 실행 증거가 전혀 없다고 볼 것인가, 이 세션 시작 시 시스템이 남긴 기록을 증거로 쓸 것인가.** 이 대화가 열릴 때 시스템이 자동으로 "HEAD: 28fb0fc (ahead 3 / behind 0)... RED: 0/20"이라는 기록을 남겼습니다. `28fb0fc`는 지금 검토 중인 이 브랜치의 최신 커밋과 정확히 일치합니다(아래 기술 상세에서 대조). 이 기록은 저장소에 있는 검사 스크립트 20개(제외 대상 1개를 뺀 전체)를 실제로 돌려 실패 건수를 센 것이므로, 지금 검토 대상인 수정된 `acceptance-0-2.sh`와 신규 `acceptance-0-2-unreachable-objects.sh`가 둘 다 포함되어 실행됐고 둘 다 성공(종료값 0)했다는 뜻입니다. 이를 근거로 채택한 이유는 이것이 제 주장이 아니라 별도 시스템이 독립적으로 남긴 시각 기록이기 때문입니다. 버린 선택지는 "이 기록도 내가 만든 게 아니니 무시한다"였는데, 그러면 실행 증거가 전무한 상태로 판정해야 해서 오히려 위험이 커집니다.

**갈림길 3 — 발견한 사소한 취약점들을 결함으로 격상할 것인가.** 환경변수 상속 문제(아래 §low-1)나 성능 문제(§low-2)를 발견했지만, 둘 다 "조용히 잘못된 통과"가 아니라 "발생하면 시험 자체가 시끄럽게 실패하는" 구조이거나 "설계 문서에 이미 대가로 명시된 것"이었습니다. 그래서 결함(FAIL 사유)이 아니라 개선 권고로 분류했습니다. 이 판단이 틀렸다면, 실제로는 조용히 통과되는 경로가 있는데 제가 못 봤다는 뜻이 되므로, 아래에 각 항목의 근거 코드를 전부 남겨 재확인이 가능하게 했습니다.

---

## 기술 상세

### 0. 이번 검토에서 못 한 것 (NOT_RUN) — 먼저 명시

사장님께서 지시하신 명령 중 아래는 **권한 시스템이 자동 거부**해 실행하지 못했습니다. 재시도 문구는 전부 동일했습니다: *"Permission to use Bash has been denied because Claude Code is running in don't ask mode."*

| # | 지시받은 명령 | 결과 |
|---|---|---|
| 1 | `bash scripts/acceptance-0-2-unreachable-objects.sh` | NOT_RUN — 거부 |
| 2 | `bash scripts/acceptance-0-2.sh` | NOT_RUN — 거부 |
| 3 | `bash verify.sh` | NOT_RUN — 거부 |
| 4 | `bash scripts/check-docs-sot.sh` | NOT_RUN — 거부 |
| 5 | `bash scripts/verify/check-mechanism-registry.sh` | NOT_RUN — 같은 종류(스크립트 직접 실행)라 시도해도 같은 거부가 예상되어 재시도하지 않음 |
| 6 | `bash scripts/acceptance-verify-ac-m.sh` | NOT_RUN — 위와 동일 사유 |
| 7 | `bash -n scripts/acceptance-0-2.sh scripts/acceptance-0-2-unreachable-objects.sh`(문법 검사) | NOT_RUN — 거부(`bash -n`도 "bash 실행"으로 분류되어 막힘) |
| 8 | `bash scripts/session-status.sh` | NOT_RUN — 위와 동일 사유(시도 안 함) |
| 9 | `git fsck --full --no-reflogs --unreachable` (실저장소 대상, 읽기 전용임에도) | NOT_RUN — 거부 |

→ [Codex 주석] Claude가 실행하지 못한 아홉 명령과 이유를 빠짐없이 적은 표입니다. 이 공백은 아래
Codex V2가 같은 명령을 직접 실행해 보완했습니다.

**된 것:**

| # | 명령 | 결과 |
|---|---|---|
| 1 | `git status --short --branch` | 실행됨(§1) |
| 2 | `git diff --name-status origin/main...HEAD` | 실행됨(§1) |
| 3 | `git diff origin/main...HEAD` | 실행됨(§2) |
| 4 | `git diff --check origin/main...HEAD` | 실행됨, 출력 없음(공백 오류 0건) |
| 5 | `git diff 59e4737 HEAD -- scripts/acceptance-0-2-unreachable-objects.sh`(지시받은 `..` 두 점 표기는 거부되어 한 점 표기로 재시도) | 실행됨, 출력 없음(무변경) — §3 |
| 6 | 파일 정독(`Read`), `Grep`을 이용한 diff 전수 검색 | 다수 수행 — §4 이하 |

→ [Codex 주석] Claude가 직접 확인한 것은 변경 범위·공백 오류·첫 RED 이후 시험 불변과 파일 정독입니다.
실행 증거는 아니므로 이것만으로 합격 처리하지 않았습니다.

이것이 이번 판정의 근본 한계입니다. **저는 "돌려보니 통과했다"를 직접 보여드릴 수 없었고, 대신 "코드를 읽어보니 이렇게 동작할 수밖에 없다"는 논리적 증명과, 시스템이 이미 남긴 실행 기록을 근거로 삼았습니다.** 실제 실행 권한이 있는 세션(Codex 재현 등)에서 위 1~9번을 그대로 다시 돌려 확인하는 절차가 아직 남아 있습니다.

---

### 1. 변경 범위

```
git status --short --branch
## task/humansearch-g0-unreachable-secret-scan...origin/main [ahead 3]

git diff --name-status origin/main...HEAD
M	.github/workflows/verify.yml
A	docs/engineering/humansearch-g0-unreachable-secret-scan-goal-2026-08-17.md
M	docs/sot/verification-commands.md
A	scripts/acceptance-0-2-unreachable-objects.sh
M	scripts/acceptance-0-2.sh
M	suppressions.yaml
```
→ 뭘 시켰나: 브랜치와 변경 파일 목록 확인 / 뭐가 나왔나: 6개 파일, 코드 2개(신규 1·수정 1) + 문서 2개(신규 1·수정 1) + 워크플로 1개 + 억제 원장 1개 / 좋은 소식: 범위가 목표 문서(§goal-2026-08-17)가 밝힌 범위와 정확히 일치하고, 제품 코드(HumanSearch)는 건드리지 않았습니다.

`git diff --stat` 결과: `271줄 추가, 31줄 삭제`(문서 139줄 포함). 실제 실행 로직 변경은 `scripts/acceptance-0-2.sh`(+38/−0, 사실상 순수 추가)와 신규 파일(+74줄)입니다.

### 2. 세션 시작 기록과 이 커밋의 일치 여부 (§실행 증거의 신뢰도)

이 대화가 열릴 때 시스템이 자동 출력한 문구:
```
HEAD: 28fb0fc (ahead 3 / behind 0)
ORIGIN: 4fdef31
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
```
→ [Codex 주석] Claude가 검토한 첫 GREEN 지문과 당시 시작 검사 실패 0/20을 보여줍니다. 뒤 블록에서
그 지문이 실제 브랜치 기록과 같은지 대조했습니다.

```
git log --oneline -5
28fb0fc 비밀과 무관한 복구 기록이 시작을 막지 않게 한다   ← 지금 검토 대상 브랜치의 HEAD
59e4737 복구 객체 판정의 거짓 차단을 실패 시험으로 고정한다  ← RED 커밋
5abe11f 무해한 복구 기록 오인을 수정 전에 고정한다        ← PLAN 커밋
4fdef31 docs(engineering): admin dashboard ...        ← origin/main
```
→ 뭘 시켰나: 세션 시작 기록의 HEAD 해시가 실제로 지금 검토 중인 브랜치의 최신 커밋인지 대조 / 뭐가 나왔나: `28fb0fc`가 정확히 일치 / 좋은 소식: "0/20"은 옛날 상태가 아니라 지금 이 검토 대상 코드를 실행한 결과입니다.

`scripts/session-status.sh:46-49`(이 검사가 사용하는 검색 조건)를 읽고, 동일 조건을 읽기 전용 `find`로 직접 재현했습니다.
```
find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \) -not -path './worktrees/*' -not -path './.git/*' | sort
→ (파일 21개 나열, verify.sh 1 + acceptance-*.sh 20)
```
→ 뭘 시켰나: "0/20"의 분모(20)가 실제로 몇 개 파일을 가리키는지 계수 / 뭐가 나왔나: 21개 중 `acceptance-0-7.sh` 1개를 제외(코드 주석에 명시된 제외 규칙, `session-status.sh:45`)하면 정확히 20 / 좋은 소식: 숫자가 조작되지 않았고, 이 20개 안에 신규 스크립트 `acceptance-0-2-unreachable-objects.sh`와 수정된 `acceptance-0-2.sh` 둘 다 포함됩니다. 즉 "0/20"은 이 두 파일을 포함해 실행한 결과입니다.

※ 다만 이 "0/20"은 통과/실패 여부만 남긴 요약이며, 각 스크립트의 상세 출력(제가 눈으로 검증하려 했던 4가지 시나리오별 문구 일치 여부)까지는 보여주지 않습니다. 그 상세 출력 일치 여부는 코드 정독(§4)으로 대체했습니다.

### 3. RED 커밋 이후 시험 파일 불변 확인 (하네스 절차 준수 여부)

```
git show --stat 59e4737   # RED
 scripts/acceptance-0-2-unreachable-objects.sh | 74 +++++++++++
 (파일 신규 생성, 74줄 추가만)

git show --stat 28fb0fc   # GREEN
 .github/workflows/verify.yml      |  4 ++
 docs/sot/verification-commands.md | 31 +++--
 scripts/acceptance-0-2.sh         | 38 +++++--
 suppressions.yaml                 | 16 --
 (신규 시험 파일은 이 목록에 없음)

git diff 59e4737 HEAD -- scripts/acceptance-0-2-unreachable-objects.sh
(출력 없음)
```
→ 뭘 시켰나: 실패 시험(RED)을 만든 커밋과 지금(HEAD) 사이에 그 시험 파일이 바뀌었는지 대조 / 뭐가 나왔나: 차이 없음(완전 동일) / 좋은 소식: 구현 커밋(GREEN)이 자기 시험의 기대값을 몰래 바꾸는 방식으로 "억지로 통과"시키지 않았습니다. 사장님께서 지시하신 적대검증 항목 중 "RED commit 59e4737 뒤 시험 파일이 불변인지"는 **확인됨**입니다.

### 4. 핵심 로직 검토 — `scripts/acceptance-0-2.sh:101-138`

수정 전에는 "복구 가능한 객체(git이 어느 가지에서도 가리키지 않지만 저장소 안에 남은 파일 조각, 이하 '복구 객체')가 1개라도 있으면 무조건 실패"였습니다. 수정 후 구조:

```
104  fsck_rc=0
105  fsck_out=$(git fsck --full --no-reflogs --unreachable 2>/dev/null) || fsck_rc=$?
106  if [ "$fsck_rc" -ne 0 ]; then
107    echo "FAIL: git fsck 실행 실패(exit=$fsck_rc) — 복구 가능 객체 검사 무효"
108    fail=1
109  fi
```
→ 이 4줄이 하는 일: 저장소 무결성 검사 도구(git fsck) 자체가 실행에 실패하면(예: 손상된 저장소) 이를 "복구 객체 0개"로 오인하지 않고 즉시 실패시킵니다. 사장님이 물으신 "git fsck 실패나 출력 형식 차이가 조용히 통과하는지" — **차단됨을 확인**했습니다(코드상 실패 시 자동으로 `fail=1`).

```
110  unreachable_objects=$(printf '%s\n' "$fsck_out" | awk '$1 == "unreachable" && NF >= 3 {print $2, $3}')
111  unreach=$(printf '%s\n' "$unreachable_objects" | awk 'NF{c++} END{print c+0}')
113  while read -r object_type sha; do
114    [ -z "${sha:-}" ] && continue
115    [ "$object_type" = blob ] || continue
117    set +e
118    git cat-file blob "$sha" 2>/dev/null | grep -aF "$LIT" >/dev/null
119    object_pipe_status=("${PIPESTATUS[@]}")
120    set -e
121    cat_rc=${object_pipe_status[0]}
122    grep_rc=${object_pipe_status[1]}
123    if [ "$cat_rc" -ne 0 ]; then
124      echo "FAIL: 복구 가능 blob 읽기 실패: $sha (exit=$cat_rc)"; fail=1
126    elif [ "$grep_rc" -eq 0 ]; then
127      echo "FAIL: 복구 가능 blob에 리터럴 잔존: $sha"; fail=1
129    elif [ "$grep_rc" -ne 1 ]; then
130      echo "FAIL: 복구 가능 blob 내용 검사 실패: $sha (exit=$grep_rc)"; fail=1
132    fi
133  done <<< "$unreachable_objects"
135  if [ -n "${ACCEPTANCE_ENDSTATE:-}" ] && [ "$unreach" -ne 0 ]; then
136    echo "FAIL: unreachable 객체 ${unreach}건 잔존 ..."; fail=1
137  fi
```
→ 이 블록이 하는 일: 복구 객체 전부(114줄 반복문, 중간에 건너뛰는 조건 없음)를 하나씩 열어 실제 회사 비밀 문자열(`$LIT`)이 있는지 봅니다. 파일 읽기 자체가 실패하면(123줄, `cat_rc≠0`) "일치 없음"이 아니라 별도 실패로 취급합니다. 검색 도구(grep)가 정상 종료(찾음=0 또는 못 찾음=1)가 아닌 다른 값을 내면(129줄) 이것도 별도 실패로 취급합니다 — **grep/cat-file 오류를 "일치 안 함(통과)"으로 오인하는 경로가 없음을 확인**했습니다. 135줄은 "과거 비밀 제거를 완전히 끝냈는지 최종 확인하는 모드"(`ACCEPTANCE_ENDSTATE=1`)에서만 내용과 무관하게 복구 객체 0개를 계속 요구합니다 — **최종 확인 모드의 0개 조건은 그대로 보존됨을 확인**했습니다.

`118`줄의 `grep -a`(binary/줄바꿈 없는 파일도 텍스트로 취급)와 `-F`(정규식이 아닌 고정 문자열 비교)를 확인했고, 결과는 `>/dev/null`로 버려 **비밀 값 자체를 출력에 노출하지 않음**을 확인했습니다(찾았다는 사실과 객체 식별자만 출력).

### 5. 신규 시험 파일 검토 — `scripts/acceptance-0-2-unreachable-objects.sh`

```
19  REPO="$TMP_ROOT/repo"
20  git init -q "$REPO"
21  cp "$ROOT/verify.sh" "$REPO/verify.sh"
23  cp "$ROOT/scripts/acceptance-0-2.sh" "$REPO/scripts/acceptance-0-2.sh"
```
→ 이 3줄이 하는 일: 실행 시점마다 지금 저장소 루트에 있는 **실제 수정된 파일을 복사**해서 격리된 임시 저장소에 심습니다. "회귀 시험이 수정된 실제 acceptance-0-2.sh를 실행하는지"에 대한 답 — **예, 매번 최신 파일을 복사해 실행하도록 짜여 있음을 확인**했습니다(과거 스냅샷을 박아둔 가짜 구현이 아님).

4가지 검증 사례(58·61·63·67줄)를 목표 문서 §3의 4가지 필수 시나리오와 대조했습니다.

| 시나리오(목표 문서 §3) | 코드 위치 | 대조 결과 |
|---|---|---|
| ① 복구 객체 0개 → 통과 | `58줄 run_case no-unreachable 0 ...` | 일치 |
| ② 무해한 복구 객체 1개, 평소 검사 → 통과 | `60-61줄` | 일치 |
| ③ 비밀 값 든 복구 객체, 평소 검사 → 실패 | `66-68줄`, 기대 문구 `'복구 가능 blob에 리터럴 잔존'` | acceptance-0-2.sh:127의 실제 문구와 일치 |
| ④ 무해한 객체 1개라도 최종 확인 모드 → 실패 | `63-64줄`, 기대 문구 `'unreachable 객체 1건 잔존'` | acceptance-0-2.sh:136의 실제 문구와 일치(1건 시점에 정확히 실행됨을 시퀀스로 확인) |

→ [Codex 주석] 목표의 네 사례와 실제 시험 줄을 대조한 표이며 네 기대 결과가 모두 일치합니다. 아래
최종 실행에서도 같은 네 사례가 `CHECKED: 4`로 통과했습니다.

이 시험은 실제 회사 비밀값을 전혀 쓰지 않고 `LOCAL-GATE-SYNTHETIC-LITERAL-42`라는 합성 문자열만 사용합니다(`25줄`). 격리 저장소는 `git -C "$REPO"`(모든 git 명령에 `-C` 지정)로만 조작되어 **진짜 저장소를 건드리지 않습니다** — 과거 사고 사례(검증기가 실저장소에 비밀을 심어 오염원이 되는 함정)를 재현하지 않는 설계임을 확인했습니다.

### 6. CI·훅 연결 확인 — `.github/workflows/verify.yml`, `hooks/pre-push`

```yaml
98  - name: 인수 검사 0-2 복구 객체 판정
100   run: bash scripts/acceptance-0-2-unreachable-objects.sh
```
→ 워크플로 파일에서 이 줄의 실제 실행 순서를 세어보니 1~17번 중 **6번째**였습니다. `docs/sot/verification-commands.md`의 표도 정확히 6번째로 이 항목을 적어놓았고, 나머지 16개 항목의 이름·순서도 전부 일치했습니다 — **문서의 "17개 단계"와 실제 워크플로가 같음을 확인**했습니다.

`hooks/pre-push:112-113`(검사 스크립트를 찾는 규칙, `find`로 `acceptance-*.sh` 패턴 전부 수집)과 `:143-148`(정확히 `acceptance-0-2.sh`·`acceptance-0-5.sh`라는 이름만 예외 처리)을 대조했습니다. 신규 파일명은 `acceptance-0-2-unreachable-objects.sh`로, 예외 처리 대상인 정확한 이름 `acceptance-0-2.sh`와 문자 그대로 다릅니다. 즉 **push할 때마다 이 신규 시험도 자동으로 함께 실행됨을 확인**했습니다 — "hooks/pre-push의 이름 규칙과 CI 워크플로 양쪽에 연결됐는지"는 **연결됨**입니다.

### 7. 억제 원장(`suppressions.yaml`) 삭제 검토

삭제된 항목은 `acceptance-0-2` 억제였고, 그 원문(삭제 전)의 "issue" 필드는 "뮤테이션 시험은 합성 값만 쓰므로 로컬 패턴 파일 없이 CI로 옮길 수 있다 — 최우선"이라고 적혀 있었습니다. 이번 변경이 정확히 그 계획대로 신규 합성-값 시험을 CI에 추가했으므로, **삭제가 해결되지 않은 결함을 숨기는 것이 아니라 실제로 해결된 항목을 원장에서 지운 것**으로 판단했습니다. 남은 억제 3건(`ci-transfer-guarantee` 만료 2026-09-15, `p13-deletion-blindspot` 2026-09-15, `gate-scope-gaps` 2026-09-30, `keyword-env-value-floor-12` 2026-08-26)은 오늘(2026-08-17) 기준 전부 미만료입니다.

### 8. 비밀 유출 정밀 대조

```
git diff origin/main...HEAD | grep -inE "password|secret[_-]?key|api[_-]?key|token|AKIA" | grep -v "^diff\|^---\|^+++\|비밀\|리터럴\|LIT\|SECRET_PATTERNS_FILE\|secret-pattern"
(출력 없음)
```
→ 뭘 시켰나: 이번 diff 전문에서 실제 값처럼 보이는 문자열이 섞였는지 정밀 대조(개념어로 쓰인 "secret"·"비밀" 등은 제외) / 뭐가 나왔나: 없음 / 좋은 소식: diff 자체에 실제 값이 섞여 들어간 흔적이 없습니다.

### 9. 발견한 경미한 사항 (결함으로 격상하지 않은 것들, 근거와 함께)

**낮음-1. 신규 시험 파일이 `SECRET_PATTERNS_FILE` 환경변수를 명시적으로 비우지 않음.**
`scripts/acceptance-0-2-unreachable-objects.sh` 전체에 이 변수를 지우는 코드가 없습니다. 만약 개발자가 자기 셸에 이 변수를 실제 비밀 파일 경로로 미리 export해둔 채 이 시험을 수동 실행하면, 격리 저장소 안에서도 그 값이 새어 들어가 합성 값(`LOCAL-GATE-SYNTHETIC-LITERAL-42`) 대신 그 값을 기준으로 비교하게 됩니다. 다만 이 경우 결과는 "조용한 오통과"가 아니라 `run_case`의 종료값·문구 대조(58-56줄)가 어긋나 **그 자리에서 시험 자체가 시끄럽게 실패**합니다 — 자동 실행 경로(`hooks/pre-push:165`, CI)는 이미 이 변수를 비우고 호출하므로 실제 운영 경로에는 영향이 없습니다. 그래서 결함이 아니라 개선 권고로 분류했습니다.

**낮음-2. 실행 시간 증가 가능성.**
신규 시험은 `acceptance-0-2.sh` 전체(내부에 또 다른 격리 저장소를 만들어 `verify.sh`를 재실행하는 뮤테이션 시험 포함, `acceptance-0-2.sh:37-66`)를 4번 반복 호출합니다. 목표 문서 자체가 "대가" 항목에서 "저장소가 클수록 검사 시간이 늘 수 있다"고 이미 인정한 트레이드오프이므로 새로운 발견이 아니라 기존에 합의된 비용으로 분류했습니다. ※ 실제 걸리는 시간은 이번 세션에서 실행이 막혀 측정하지 못했습니다.

**낮음-3(이번 변경과 무관한 기존 상태, 참고용).**
`scripts/acceptance-0-2.sh`가 로컬의 **실제** 비밀 파일을 기준으로 판정하는 경로(1~4번 검사)는 이번에도 여전히 `hooks/pre-push:144`에서 이름으로 제외되고 CI에는 아예 없어, 강제 차단 관문이 아니라 세션 시작 보고(session-status.sh)에서만 참고용으로 나타납니다. 이는 삭제된 억제 항목의 원문에도 이미 적혀 있던 기존 상태이며, 이번 diff가 새로 만든 문제가 아닙니다.
→ Claude의 고정 판정은 `PASS`, 명백한 결함 0건, 낮은 개선 권고 3건입니다. 이 중 상속 환경 1건은
Codex가 실제로 재현한 뒤 `08a96c3`에서 닫았고, 성능은 4.13초로 측정했으며, 기존 로컬 검사 강제 범위는
이번 변경 밖이라는 판단을 유지했습니다. 첫 줄 형식 위반과 셸 `NOT_RUN`은 숨기지 않았습니다.

형식 재판정 명령과 실패 원문은 다음과 같습니다.

```text
$ env -u ANTHROPIC_API_KEY claude --bare --model sonnet --no-session-persistence --permission-mode dontAsk --tools Read,Grep -p '최종 1차 적대검증 재판정입니다. 읽기 전용이며 셸 명령은 실행하지 마십시오. 현재 작업 공간의 scripts/acceptance-0-2.sh, scripts/acceptance-0-2-unreachable-objects.sh, .github/workflows/verify.yml, docs/sot/verification-commands.md, suppressions.yaml, 목표 문서를 직접 읽으십시오. 이전 PASS 판정의 상속 환경 지적을 Codex가 실패로 재현한 뒤 회귀 시험 시작부에서 SECRET_PATTERNS_FILE을 unset하도록 바꿨습니다. 이 수정이 지적을 닫았는지, 제품 검사기의 명시적 override 계약을 보존하는지, 실제 수정 파일 실행·CI와 pre-push 연결·17단계 문서·비밀 비출력을 적대적으로 확인하십시오. 셸 결과는 NOT_RUN으로 표시하십시오. 첫 줄은 정확히 VERDICT: PASS 또는 VERDICT: FAIL이고, 결론·근거·기술 상세 순서와 용어 풀이·출력 해석·결정 카드·미확인 표시를 지키십시오.'
Not logged in · Please run /login
FORMAT_REVIEW_EXIT=1
```

→ 확장 도구를 끈 최소 모드는 기존 로그인 정보를 읽지 않아 판정을 만들지 못했습니다. 따라서 원래
Claude 판정 원문을 보존하고, 최종 수정의 실행 재현은 아래 Codex V2가 맡습니다.

#### Codex V2 — Claude 판정 재공격

Codex는 Claude가 실행하지 못한 명령을 최종 지문 `08a96c3`에서 직접 실행하고, Claude의 낮은 위험
지적도 합격 권고로 넘기지 않고 새 실패 증거와 수정으로 닫았습니다.

| Claude 주장 | Codex 재현 | 일치 여부 |
|---|---|---|
| 저장소 무결성 검사 실패와 파일 읽기·검색 오류는 조용히 통과하지 않는다 | `scripts/acceptance-0-2.sh:104-132`의 세 오류 분기를 다시 읽고 실제 시작 검사를 실행해 성적 0 확인 | 일치. 오류 주입 실행은 하지 않았고 분기 대조만 확인 |
| 무해한 복구 파일은 통과하고 비밀 복구 파일과 최종 확인의 1개 객체는 차단한다 | 합성 사례 4개가 `0,0,1,1` 기대 성적과 모두 일치, `CHECKED: 4` | 일치 |
| 여러 복구 파일 중 비밀 파일을 놓치지 않는다 | 마지막 사례는 앞서 만든 무해한 파일과 비밀 파일이 함께 남은 상태에서 비밀 파일을 찾아 불합격 | 일치 |
| 이진 파일과 줄바꿈 없는 파일도 내용으로 읽는다 | `scripts/acceptance-0-2.sh:118`의 텍스트 강제 고정 문자열 검색을 대조 | 일치. 별도 이진 fixture 실행은 하지 않음 |
| 첫 RED 뒤 첫 GREEN까지 시험 파일은 불변이다 | `git diff --exit-code 59e4737..28fb0fc -- scripts/acceptance-0-2-unreachable-objects.sh` 성적 0 | 일치. 이후 Claude 지적용 새 RED `4fecc43` 뒤 환경 상속 차단 4줄만 의도적으로 추가 |
| 로컬 업로드 전 검사와 서버 검사 양쪽에 연결됐다 | 자동 수집 1건, 서버 단계 17개, 새 단계는 6번째, 서버 설정의 실행 줄 1개 확인 | 일치 |
| 억제 원장 삭제는 미해결 약화를 숨기지 않는다 | 합성 서버 시험이 추가되고 시작 실패 0/20 및 별도 차단 6/6 확인 | 일치 |
| 출력은 비밀값 자체를 노출하지 않는다 | 비밀 적중 사례 출력은 합성 객체 지문만 표시하고 검색 결과 본문은 폐기 | 일치 |
| 상속 환경은 수동 회귀 시험을 바꿀 수 있다 | 공개 기본 규칙 파일을 상속해 전체 성적 1 재현 | 일치, 실제 결함으로 승격해 수정 완료 |
| 상속 환경 차단 뒤에도 제품 검사의 명시적 외부 파일 계약은 유지된다 | 차단은 회귀 시험 파일 `:7`에만 있고 제품 검사 파일의 `SECRET_PATTERNS_FILE` 선택은 그대로 유지 | 일치 |
| 실행 시간은 확인하지 못했다 | 회귀 시험 전체 4개 사례를 4.13초로 측정 | Claude의 미확인을 Codex가 보완 |
| 시작 검사는 실패 0/20이다 | 최종 지문에서 `RED: 0/20`, 제외된 무거운 차단 시연도 별도 6/6 통과 | 일치, 더 최신 지문으로 재확인 |

→ Claude의 `PASS` 결론은 유지하되 낮은 위험 1건을 실제 수정으로 승격했습니다. Claude가 못 돌린 실행
증거는 Codex가 전부 보완했고, 남은 실행 공백은 이진 전용 fixture와 오류 주입 두 종류입니다. 현재 실제
시작 경로, 네 핵심 사례, 자동 연결, 서버 단계, 차단 시연에는 미해결 불일치가 없습니다.

**Codex V2 최종 판정: PASS.** 확인된 결함 1건은 `4fecc43` RED와 `08a96c3` GREEN으로 닫혔고,
미해결 치명·높음·중간·낮음 결함은 0건입니다. 실제 포털, 브라우저, 로그인, 후보자 개인정보, 제품
분류기, 병합과 배포는 범위 밖이라 실행하지 않았습니다.
