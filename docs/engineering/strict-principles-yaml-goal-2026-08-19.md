# strict 스킬 실효성 강화 + principles.yaml 신설 — goal (2026-08-19)

## 사장님 브리핑 (여기부터 읽으면 됩니다)

**결론:** 지금 `/strict`(사장님이 매번 치시는 엄격 모드 지시문)는 524줄까지 커졌는데, 그중 상당수는 "왜 이 규칙이 생겼는지"의 옛날이야기이고, 정작 "P1~P22 원칙이 지금 실제 코드로 지켜지고 있는지"를 기계가 확인하는 장치(`principles.yaml`)는 여태 안 만들어져 있었습니다. 이번 작업은 두 가지를 합니다: ① 그 확인 장치를 실제로 만든다 ② `/strict` 파일에서 "매번 읽어야 하는 것"과 "필요할 때만 열어보면 되는 것"을 분리한다. 둘 다 사장님이 어제·오늘 말씀하신 방향(엑기스만 남기기, 그러나 효과가 검증된 문구는 지키기, 처음부터 잘 짜서 재작업을 줄이기)을 그대로 따릅니다.

**판단 근거(왜 이 순서로 하나):** 이번에 두 가지 다 하려고 하면 위험이 큽니다 — `/strict` 본문 압축은 과거 이미 5번 시도해서 5번 다 구멍이 뚫린 전례(§8-6a 기록)가 있는 파일을 다시 건드리는 일이라, 서두르면 효과가 검증된 문구까지 같이 날아갈 위험이 있습니다. 그래서 이번 판에서는 ① **위험이 낮고 가치가 확실한 것**(principles.yaml 신설 — 완전히 새로 만드는 것이라 기존 걸 망가뜨릴 위험이 없음)을 먼저 실제로 완성하고 ② `/strict` 본문 압축은 "무엇을 어디로 옮길지"까지만 이번에 확정하고, 실제 잘라내기는 codex 1차 검증까지 받은 뒤 진행합니다. 버린 선택지: "한 번에 다 갈아엎기" — 검증할 시간 대비 위험이 너무 큽니다.

**틀리면 뭐가 깨지나:** `principles.yaml`의 판정이 틀리면(예: 실제로 안 지켜지는 걸 "완전"이라 잘못 적으면) 다음에 이 파일만 믿고 검증을 건너뛰다가 진짜 결함을 놓칠 수 있습니다. 그래서 이번 판은 "완전"이라고 적는 항목마다 반드시 실행 증거를 남기고, 애매하면 "부분"이나 "미확인"으로 낮춰 적습니다(과장 방지).

---

## ① 현재 상태 (파일:줄 증거)

- `~/.claude/skills/strict/SKILL.md` — 524줄, 59,559바이트. 08-06 문서 §3이 정한 "스킬 계층 100줄 상한"의 5.24배.
- `~/.codex/skills/strict/SKILL.md` — 273줄, 37,919바이트. Claude판과 **다른 구조**(§5·§6 검증자 역할이 스왑돼 있음 — codex가 구현자일 땐 `claude -p`가 1차 검증, codex 자신이 2차 검증). 두 파일은 git 관리가 안 되는 `~/.claude`, `~/.codex` 밑에 있어 `diff`로만 대조 가능(`.bak-*` 스냅샷 존재).
- `docs/sot/coding-principles.md`(70줄) — P1~P22 + §1-B(5조) + V-1~V5, 이미 압축돼 있음. 원본: `docs/engineering/v6-coding-principles-goal-2026-08-06.md`(600줄).
- `docs/sot/principles.yaml` — **존재하지 않음**(`find` 확인, 2026-08-19). P1의 키스톤 요구사항("principles.yaml 전 항목이 mechanism을 갖고 CI가 확인")이 08-06일에 정해졌으나 13일째 미착수.
- 이미 존재하는 동형 장치: `docs/sot/mechanism-registry.yaml` + `scripts/verify/check-mechanism-registry.sh`(AC-M, `scripts/acceptance-verify-ac-m.sh:24`에서 호출) — pre-push 글롭(`hooks/pre-push`의 `scripts/acceptance-*.sh` 자동 수집)에 이미 편입돼 매 `git push`·CI에서 자동 실행됨. 단 등록 범위가 비밀스캔류 3개 항목뿐, P1~P22를 안 덮음.
- 2026-08-19 실측(fork 조사, `/private/tmp/.../principles-yaml-draft-2026-08-19.md`): P1~P22+§1-B 5조+V1~V5 총 32항목 중 **완전 8 / 부분 10 / 없음 5 / 해당없음 4 / 미확인 5**.

## ② 근본 원인

원칙을 "산문으로 적어두는 것"과 "기계가 그 원칙이 지켜지는지 매번 확인하는 것" 사이에 자동 연결이 없다. `docs/sot/coding-principles.md`는 사람이 읽기용 정본이지만, 그 자체를 CI가 파싱해서 "이 원칙 지금 코드로 지켜지나?"를 답해주지 않는다. `/strict`도 마찬가지로 "이렇게 하라"고 매번 다시 읽어주는 것뿐, 실측 상태를 기억하지 않는다 — 그래서 어제 fork가 32개를 손으로 세다가 계산을 틀렸다(사람이 세면 샌다, P1이 경고하는 바로 그 문제).

## ③ 인수 기준 (AC) — EARS + 검증 명령 + counter-AC

**AC1 — principles.yaml 스키마 신설**
- EARS: `When 저장소에 docs/sot/principles.yaml이 생성되면, then 그 파일은 P1~P22·§1-B 1~5·V-1~V5 총 32개 항목을 빠짐없이 담고 각 항목은 id·principle·mechanism_expected·mechanism_found·status·evidence 6개 필드를 가져야 한다.`
- 검증 명령: `python3 -c "import yaml,sys; d=yaml.safe_load(open('docs/sot/principles.yaml')); assert len(d)==32; [print('MISSING_FIELD',x['id']) for x in d if not all(k in x for k in ('id','principle','mechanism_expected','mechanism_found','status','evidence'))]"`
- counter-AC: 32개 미만이거나, 필드 하나라도 빠진 항목이 있는데 "완료"라고 보고하면 가짜.

**AC2 — check-principles.sh 신설 + 자동 편입**
- EARS: `When scripts/acceptance-principles-check.sh가 생성되면, then hooks/pre-push의 글롭이 이 파일을 자동으로 발견해 매 git push마다 실행해야 한다.`
- 검증 명령: `bash hooks/pre-push </dev/null 2>&1 | grep -c "acceptance-principles-check"` (0보다 커야 함 — 실행되거나 최소한 목록에 잡혀야 함)
- counter-AC: 스크립트만 만들고 이름이 `acceptance-*.sh` 패턴이 아니라서 글롭에 안 걸리면(예: `check-principles.sh`로만 저장) 가짜 편입.

**AC3 — status 회귀 방지(ratchet)**
- EARS: `If principles.yaml의 어느 항목이 이전 커밋보다 status가 나빠지면(완전→부분→없음 방향), then acceptance-principles-check.sh는 실패해야 한다.`
- 검증 명령: 워크트리에서 임의로 한 항목의 status를 "완전"→"없음"으로 낮춘 뒤 `bash scripts/acceptance-principles-check.sh` 실행, exit 1 확인. 원복 후 exit 0 확인.
- counter-AC: status를 낮췄는데도 exit 0이면 이 게이트는 있으나 마나 한 장식품.

**AC4 — Claude측 SKILL.md 핵심/부록 분리 계획 확정(이번 판은 계획까지, 실행은 V1 통과 후)**
- EARS: `When 이번 goal 작업이 끝나면, then docs/engineering/이 goal 문서에 "무엇을 core에 남기고 무엇을 references/로 옮길지"의 절 단위 목록이 남아 있어야 한다.`
- 검증 명령: 이 문서에 "§ 분리 계획" 절 존재 확인(아래 ⑩ 참조).
- counter-AC: 목록 없이 "다음에 하겠다"고만 적으면 미착수.

**AC5 — Codex측 SKILL.md 동기화 확인**
- EARS: `When Claude측 SKILL.md의 §8(브리핑 계약)이 바뀌면, then Codex측 SKILL.md의 §8도 같은 회차에 동일 내용으로 갱신돼야 한다(이미 §8-7-6에 명문화된 규칙 — 이번엔 위반 없음을 실제로 diff로 확인한다).`
- 검증 명령: `diff <(sed -n '/^### 8-1/,/^### 8-8/p' ~/.claude/skills/strict/SKILL.md) <(sed -n '/^### 8-1/,/^### 8-8/p' ~/.codex/skills/strict/SKILL.md)`
- counter-AC: 이번 판에서 Claude측 §8을 안 건드리면 이 AC는 "변경 없음 확인"으로 충분 — 실제로 건드릴 계획이 없으므로 이번엔 회귀 없음만 증명.

## ④ Harness 게이트 진행 계획

- `docs/sot/principles.yaml`·`scripts/acceptance-principles-check.sh`는 저장소 코드이므로 **워크트리**(`worktrees/strict-principles-yaml/`, 브랜치 `task/strict-principles-yaml`)에서 RED→GREEN.
- `~/.claude/skills/strict/SKILL.md`·`~/.codex/skills/strict/SKILL.md`는 저장소 밖 시스템 설정(git 미관리)이라 워크트리 대상이 아님 — CLAUDE.md 경로 규칙상 직접 수정 허용 경로. 단 편집 전 `.bak-2026-08-19` 스냅샷을 남긴다(기존 관례 계승).
- 게이트 4 검증: `bash scripts/session-status.sh`(RED 0/N 재확인) + `bash scripts/acceptance-principles-check.sh` 개별 실행.
- 게이트 5: PR 생성, CI 초록 확인 후 사장님께 병합 여부 보고(자동 병합 안 함 — 08-06 문서 §4 "자동 병합 금지" 원칙).

## ⑤ codex 적대검증(V1) 항목 — 정조준

1. `principles.yaml`의 32개 항목 각각의 `status` 판정이 과장이 아닌지 — 특히 "완전"이라 적은 8개(P11·P13·P14·P16·P21·V-1·V-2·V-5)를 직접 재현해서 확인.
2. `acceptance-principles-check.sh`가 진짜 pre-push 글롭에 걸리는지 실제 `bash hooks/pre-push` 실행으로 확인(문서 주장 아니라 실행).
3. status 회귀 방지(ratchet) 로직을 뮤테이션 테스트로 직접 깨보기 — 값을 낮췄는데 통과되는 우회가 있는지.
4. 이번 판에서 `/strict` 본문 자체는 안 건드렸다는 주장이 사실인지 `diff` 재현.

## ⑥ SOT 체크리스트

- `docs/sot/coding-principles.md` — 읽음. principles.yaml의 `principle` 필드는 이 파일의 문구를 그대로 인용(재작성 금지 — 표현이 갈리면 어느 게 정본인지 헷갈림).
- `docs/sot/mechanism-registry.yaml`, `docs/sot/verification-commands.md` — 읽음. 새 스크립트 이름 규칙(`acceptance-*.sh`)이 기존 관례와 일치하는지 확인 완료.
- `docs/sot/hook-contracts.md` — 이번 작업이 훅 계약을 바꾸는지 확인 필요(예상: 안 바꿈, pre-push는 기존 글롭으로 자동 편입되므로 훅 코드 자체 수정 불필요 — 이 가정을 게이트 4에서 검증).

## ⑦ 비범위 (이번엔 안 함)

- `/strict` 본문(Claude·Codex 양쪽)의 실제 절 이동/삭제는 이번 판에 하지 않는다. 계획(⑩)만 확정.
- P1~P22 중 "없음"·"부분"으로 나온 항목들의 실제 구현(예: P2 PR 템플릿, P4 네트워크 차단 레인, P17 러너 전용 쓰기 권한)은 이번 범위 밖 — 각각 별도 워크트리/AC로 이후 진행.
- `docs/engineering/v6-coding-principles-goal-2026-08-06.md` 본문 수정 없음(정본 유지, 손 안 댐).

## ⑧ 롤백 절차 (L3)

- `docs/sot/principles.yaml`·`scripts/acceptance-principles-check.sh`: PR revert 1건으로 원복(신규 파일이라 기존 동작에 영향 없음 — 있던 걸 지우는 게 아니라 새로 추가하는 것).
- `~/.claude/skills/strict/SKILL.md`·`~/.codex/skills/strict/SKILL.md`: 이번 판은 미수정이므로 롤백 대상 없음. (향후 실제 분리 작업 때는 `.bak-2026-08-19`로 원복.)

## ⑨ 영향 반경 (L3)

- 깨지면 무엇이 멈추나: `acceptance-principles-check.sh`가 잘못 짜여 항상 실패하면 **모든 `git push`가 막힌다**(pre-push 글롭에 자동 편입되므로). 그래서 게이트 4에서 훅 ON/OFF 대조를 반드시 하고, 처음엔 "정보 출력만 하고 항상 exit 0"으로 시작해 AC3(회귀 방지)만 별도로 격리 검증한 뒤 실패 조건을 켠다.
- PII·인증·과금 경로 접촉 없음 — 데이터 안전 AC 추가 불필요.

## ⑩ 계약 스펙 (Spec-Driven)

### principles.yaml 스키마

```yaml
# docs/sot/principles.yaml — 배열, 32개 원소
- id: string          # 예: "P1", "§1-B-1", "V-1"
  principle: string   # docs/sot/coding-principles.md 원문 그대로 인용(1줄 요약)
  mechanism_expected: string   # 원래 요구된 기계 장치
  mechanism_found: string|null # 실제로 찾은 file:line 또는 스크립트 경로. 없으면 null
  status: enum[완전, 부분, 없음, 해당없음, 미확인]
  evidence: string     # 실행 명령 또는 grep 결과 한 줄 요약
```

### scripts/acceptance-principles-check.sh 입출력

- 입력: `docs/sot/principles.yaml`(고정 경로), 환경변수 없음.
- 출력(stdout): `PASS: principles.yaml 32/32 스키마 유효, 회귀 0건` 또는 `FAIL: <사유>`.
- 종료값: 스키마 불충족 또는 status 회귀 시 1, 그 외 0.
- 에러 형태: yaml 파싱 실패 시 `FAIL: yaml 파싱 실패 — <원본 에러>`.

### §분리 계획 (AC4 — 이번 판은 계획만, 실행은 다음 판)

Claude측 `SKILL.md`에서 아래를 `references/`(신설)로 옮기고 본문엔 "필요하면 읽어라"는 한 줄 포인터만 남기는 안:

| 옮길 절 | 이유 | 본문에 남길 것 |
|---|---|---|
| §8 도입부 "왜 이 절이 있나"(2026-08-12 지시 경위) | 서사, 규칙 자체는 아래 §8-1~8-8에 이미 있음 | "§8 브리핑 계약(3층·용어풀이·해석·결정카드) — 위반 시 사장님이 못 읽는다" 한 줄 |
| §8-6a "네 번 연속 실패" 경위 문단 | 서사 | brief-lint.sh 사용법 + "참고용, 합격근거 아님" 한 줄은 남김(운영 규칙이라 유지) |
| §8-7 "전달 통로를 믿지 않는다" 이유 설명 | 서사 | 지시 블록 자체(복붙용)는 core에 남김 — 이건 매번 실제로 써야 하는 내용물 |
| §8-2 용어표 중 각 항목의 "2026-08-09 실측" 류 날짜 인용 | 서사 | 번역 자체(용어→쉬운말)는 core에 남김 — 매번 실제로 써야 함 |

**남길 것(효과가 검증된 것 — 안 자름):** §8-1 1층 계약 분량 규칙, §8-2 용어표 본문(번역), §8-3 해석 예시, §8-4 결정카드 5줄, §8-6b 셀프감사 9문항, §8-7 지시 블록 원문, §3-1 NOT_RUN 복구 절차 전체, 도구 라우팅표, 위험등급 매트릭스, 6.5 역할 매트릭스.

이 표가 다음 판의 실제 편집 지시서가 된다.

---

## 적대 검증 로그

(이 아래에 codex V1 판정 원문 + Claude V2 재현 결과를 append한다.)
