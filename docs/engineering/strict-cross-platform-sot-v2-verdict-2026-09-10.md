<!-- V2(2차 적대 검증) 원문 보존. 엔진: Claude Opus 5, 새 맥락 서브에이전트. 호출자: Claude session_01CjNP65FKtFC1UXF42CcM8a. 2026-09-10 22:37~22:49 +0900. 대상 HEAD 7fc4334 -->

VERDICT: PASS

<!-- V2 (2차 적대 검증). 엔진: Claude Opus 5 (1M), session_01CjNP65FKtFC1UXF42CcM8a. 대상 워크트리 HEAD=7fc4334. 읽기 전용 수행. -->

## 0. 건너뜀·미확인·재시도·추정 (판정 앞에 먼저 밝힙니다)

- **재시도 1건**: AC-3 변이(고장 주입) 공격을 처음에 `perl -i -pe` 로 시도했는데 **치환이 조용히 실패**했습니다(파일이 그대로인데 명령은 종료값 0). 그대로 셌다면 "무한정 매치 0건"이 나와 **변이가 전부 생존한 것처럼 보이는 거짓 초록**이 됐을 것입니다. `python3` 로 다시 짜면서 ① 치환 대상 문자열이 없으면 `assert` 로 즉시 중단 ② 변이본과 원본을 `diff -q` 로 대조해 실제로 바뀌었는지 확인 ③ 그 다음에만 계수, 세 단계를 넣었습니다. 아래 증거는 재시도본입니다.
- **미확인**: 원격 CI 실행, PR, GitHub 브랜치 보호는 확인하지 않았습니다. 이 가지는 아직 push되지 않았습니다.
- **미확인**: `--no-verify` 실제 사용 여부는 Git 객체만으로 증명 불가입니다. 텍스트 흔적은 0건임만 확인했습니다.
- **추정 1건**: 결함 1(전역 스킬 엔진 순서 문장 부재)의 **발생 시점**은 추정입니다. 전역 `SKILL.md` 두 개는 Git 밖 파일이라 `git blame` 이 불가합니다. 다만 착수 프롬프트가 해시 `a277178…` 을 "작업 전 값"으로 못박았고 현재 값이 그와 같으므로, **이 가지의 3커밋이 만든 상태가 아니라는 것만은 확정**입니다.
- **실행하지 않음**: 전역 파일 잠금·수정 명령은 쓰기 동작이므로 실행하지 않았습니다. 저장소·전역·git 상태를 일절 변경하지 않았고, 임시 파일은 지정된 `v2tmp/` 아래에만 만들었습니다.
- **환경 차이 있음**: V1(Codex 엔진)은 샌드박스가 임시 폴더 생성과 캐시 쓰기를 막아 필수 명령 3건을 실행하지 못했습니다. 저는 같은 원명령이 **전부 정상 실행**됐습니다. 이것을 "환경 차이"라고 부르기 전에 §5.3에 종료값과 전체 출력을 그대로 붙였습니다.

---

## 1. 결론

**이 가지의 3커밋은 맡은 일을 해냈습니다. 합격입니다.**

맡은 일은 두 가지였습니다. 첫째, 정본 문서가 **저장소에 없는 파일**(`work-unit-policy.yaml`)을 아무 조건 없이 "이게 기준이다"라고 지목하던 문장 3곳을 고치는 것. 둘째, 앞선 커밋이 "검사를 돌렸다"고 말로만 적어둔 자리에 **진짜 실행 출력**을 채워 넣는 것. 둘 다 됐습니다. 고친 문장은 조건이 문법상 붙기만 한 게 아니라 실제로 작동하며, 조건 문구를 일부러 지운 고장 사본을 만들면 검사가 정확히 3건을 잡아냅니다. 채워 넣은 실행 출력은 제가 다시 돌려 **한 글자까지 같게 재현**됐습니다.

**앞선 검증자(V1)의 불합격 판정은 두 개의 큰 이유에 기대고 있었는데, 그 두 개가 제 환경에서 무너졌습니다.** V1은 필수 검사 하나가 "종료값 1, 불합격"이라고 적었지만, 제가 같은 명령을 그대로 돌리니 **종료값 0, 합격, 검사 34건**이 나왔습니다. V1이 재현 실패라고 적은 두 건도 제 환경에선 **"Skill is valid!" 종료값 0**으로 그대로 나왔습니다. V1 스스로 "현재 환경이 모든 파일 쓰기를 막아서"라고 원인을 적어 두었고, 실제로 그것이 원인이었습니다. 즉 **작업물의 결함이 아니라 검증자 쪽 환경의 결함**이었습니다. V1의 불합격 논리는 "필수 명령 하나라도 합격이 아니면 전체 합격 금지"였는데, 그 명령이 실은 합격이므로 논리의 전제가 사라집니다.

**V1이 적은 결함 5건은 모두 실제로 재현됩니다. 그러나 5건 중 이 가지가 만든 것은 0건이고, 이 가지가 고쳐야 할 것도 0건입니다.** 두 건은 저장소 밖 전역 파일 문제인데, 이번 작업의 계약은 그 파일을 **바꾸지 말라고 명시**합니다 — V1이 요구한 수정을 했다면 오히려 계약 위반으로 불합격이 됩니다. 나머지 세 건은 각각 5일 전·한 달 전부터 있던 기존 문제이고, 이 가지가 손댄 줄과 다른 줄에 있습니다. 게다가 그중 두 건은 **작업자 본인이 goal 문서 105~119행에 표로 자진 신고**해 둔 것이라 새 발견이 아닙니다.

**다만 V1도 저도 처음엔 놓쳤던 문제를 세 개 새로 찾았습니다.** 가장 뼈아픈 것은 이겁니다 — 이번에 새로 쓴 조건 문구는 "그 파일이 **INDEX 목록에 올라간 경우에만** 기준으로 삼는다"입니다. 그런데 지금 저장소에는 **INDEX 목록에 없는데도 정본으로 쓰이는 파일이 이미 두 개** 있습니다. 그중 하나(`principles.yaml`)는 바로 그 문장이 들어 있는 문서 자신이 "반드시 읽으라"고 지시하는 파일입니다. 작업자가 goal 문서에 **"이 기준이 틀리면 깨진다"고 스스로 적어둔 바로 그 조건이, 지금 이 순간 이미 참**입니다. 이 가지의 상태는 고치기 전(없는 파일을 무조건 기준이라 부름)보다 분명히 낫지만, 완성은 아닙니다. 합격을 뒤집을 정도는 아니라 판단해 **중간 심각도의 후속 과제**로 올립니다.

**결정: 병합해도 됩니다. 단 아래 후속 4건을 별도 이슈로 등록하는 조건입니다.** 그리고 이 가지를 origin에 올리기 전에, 본줄기에 워크트리 없이 직접 올라간 커밋 `f12ea33` 문제가 함께 정리돼야 합니다(§5.9).

---

## 2. 판단 근거

전문용어 먼저 풉니다. **정본(SOT, Source Of Truth)** 은 여러 문서가 같은 말을 할 때 최종 기준이 되는 문서입니다. **인수 기준(AC)** 은 "이 명령을 돌려서 이 출력이 나오면 합격"이라고 미리 못박은 조건입니다. **반례(counter-AC)** 는 겉보기 합격을 뒤집는 사례입니다. **변이(뮤테이션)** 는 일부러 코드나 문장을 망가뜨려서 검사가 그걸 잡아내는지 보는 기법입니다 — 안 잡아내면 그 검사는 항상 통과하는 껍데기입니다. **귀속(attribution)** 은 결함이 누가 만든 것인지 커밋 단위로 가리는 일입니다.

### 선택한 해석

**판정 기준을 "이 가지의 3커밋이 원 프롬프트 T 계약을 충족하는가"로 좁혔습니다.** T 계약이 AC-2·AC-3·AC-4·AC-5와 goal 장부 재현·RED 인용 정확성을 명시적으로 열거하고, 착수 프롬프트가 "전역 파일 수정 금지", "work-unit-policy 병합은 비범위"라고 못박았기 때문입니다. 범위 밖 결함은 **별도 표기하되 판정에 반영하지 않았습니다.**

### 버린 해석

**V1의 해석 — "프롬프트가 문서 간 충돌과 기존 검사 파손도 정조준하라고 했으니 전체 범위로 판정한다" — 을 버렸습니다.** 두 가지 이유입니다.

첫째, **자기모순입니다.** V1이 결함 1·2의 처방으로 요구한 것은 전역 `SKILL.md` 두 파일을 수정하는 것입니다. 그런데 같은 프롬프트의 AC-5는 그 두 파일의 해시가 `a277178…` 그대로여야 하고 **다르면 FAIL**이라고 규정합니다. V1의 처방을 따르면 AC-5가 깨집니다. 하나의 계약 안에서 "고쳐라"와 "건드리면 불합격"이 동시에 성립할 수 없으므로, "정조준" 항목은 **결함을 보고하라는 지시이지 이 가지에서 고치라는 지시가 아니다**로 읽는 것이 유일하게 모순 없는 해석입니다.

둘째, **작업 단위 규약과 충돌합니다.** 이 저장소의 규약(`docs/sot/git-workflow.md:15`)은 "작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개"입니다. 26 대 27 불일치, 20476바이트 초과, INDEX 원칙 개수 낡음은 각각 다른 인수 기준을 가진 다른 작업입니다. 이 가지에 얹으면 규약 위반입니다.

### 틀리면 깨지는 것

- **제 환경이 오히려 비정상이고 V1 환경이 정상인 경우** — 그러면 AC-4는 진짜 FAIL이고 제 PASS 판정이 무너집니다. 이 가능성은 낮습니다. V1의 실패 메시지는 `mktemp: mkdtemp failed … Operation not permitted` 로 **검사 로직이 아니라 운영체제 권한**을 가리키고, `TMPDIR=/tmp` 재시도에서도 같은 권한 거부가 났습니다. 반면 제 실행은 `CHECKED: 34`, `MECHANISMS: PASS 34/34`, `WIRING: PASS pre-push=1 ci=1` 처럼 **검사 대상 건수까지 채운 실질 출력**입니다. 0건 통과가 아닙니다.
- **"범위 밖"이 봐주기의 다른 이름인 경우** — 그러면 결함 5건을 방치하는 판정이 됩니다. 이 위험을 막으려고 5건 전부를 §4 대조표에 **재현 여부·귀속 커밋·처리 주체까지 적어 남겼고**, 3건은 후속 이슈 등록을 병합 조건으로 걸었습니다.
- **INDEX 등재 기준이 실제로는 잘 지켜지는 관행인 경우** — 그러면 제 새 발견 N1은 기우입니다. 이 가능성은 배제됐습니다. `docs/sot/` 12개 파일 중 `principles.yaml`·`mechanism-registry.yaml` 2개가 INDEX 미등재임을 전수 대조로 실측했습니다(§5.7).

---

## 3. 요구된 두 표

### 3-1. 과장 집계

| 구분 | 건수 |
|---|---|
| **V1이 잡은 G(구현자) 과장** | **0건** |
| **V2가 잡은 V1의 과장·누락** | **10건** (과장 7 + 누락 3) |

→ V1은 결함 5건을 적었지만 그중 **구현자가 사실과 다르게 주장한 것**은 하나도 없습니다. 결함 1·4는 구현자가 goal 문서 105~119행에 스스로 표로 신고했고, 결함 3·5는 구현자가 아무 주장도 하지 않은 선행 상태이며, 결함 2의 유일한 실체는 계약이 수정을 금지한 전역 파일입니다. 반대로 V1 쪽에서는 환경 산물을 작업물 불합격으로 적은 것 2건, 인용 문맥 오독 2건, 자진 신고분을 신규 발견처럼 제시한 것 1건, 심각도 부풀림 1건, 줄번호 오기 1건, 그리고 놓친 결함 3건이 나왔습니다.

### 3-2. V1 과장·누락 상세 10건

| # | 종류 | V1의 서술 | V2 실측 | 증거 |
|---|---|---|---|---|
| E1 | 과장 | "AC-4 실제 종료값 1, `VERDICT: FAIL`, 검사 대상 0건" | 종료값 **0**, `VERDICT: PASS`, `CHECKED: 34` | §5.3 |
| E2 | 과장 | "goal 검증 장부 재현 FAIL — 두 형식 검사 재현 안 됨" | 양쪽 `Skill is valid!` **종료값 0**, 장부와 동일 | §5.3 |
| E3 | 과장(오독) | "`strict-workflow.md:20` 이 BLOCKED를 **검사 결과**로 추가" | 20행은 §2 "적응형 Strict 프롬프트" 안, **프롬프트 섹션의 해당 여부** 표기 규칙. 같은 줄 앞부분이 "등급을 낮추기 위해 **섹션**을 생략하지 않습니다" | §5.5 |
| E4 | 과장(오독) | "`verification-commands.md:68` 이 충돌의 한 축" | 68행은 `0=PASS / 1=FAIL / 2=NOT_RUN` — P3의 3상태를 **재확인**하는 줄. 충돌 증거가 아니라 일치 증거 | §5.5 |
| E5 | 과장 | 결함 1·4를 새로 발견한 것처럼 서술 | goal 문서 **105~119행**이 표로 자진 신고(원인·처리 주체까지 명시) | §5.8 |
| E6 | 과장 | 결함 1·2 심각도 **높음** | 둘 다 실체는 전역 `SKILL.md`. AC-5가 **바이트 동일 유지를 요구**하므로 이 가지에서 고치면 계약 위반 | §5.4 |
| E7 | 과장(오기) | "`coding-principles.md:9` 가 실제 P1~P24 정본" | 실제 **8행**. 9행은 다른 문장 | §5.6 |
| E8 | 누락 | — | **INDEX 등재 기준이 이미 무효** — `principles.yaml` 등 2개가 docs/sot에 실존하나 INDEX 미등재. 새 조건 문구의 전제가 깨져 있음 | §5.7 |
| E9 | 누락 | 결함 4에서 `check-docs-sot.sh` 를 실행하고도 | 그 스크립트가 **5개 파일만 하드코딩**(21~25행). f12ea33이 추가한 새 정본 `strict-workflow.md` 는 아예 검사 대상 밖. 30387바이트짜리 초과 파일도 목록 밖이라 미검출 | §5.7 |
| E10 | 누락 | "원격·PR 미확인"으로 건너뜀 | `acceptance-0-5` **FAIL** — `origin/main(fc6beed) != main(f12ea33)`. 배송 전제 조건 | §5.9 |

### 3-3. V1 판정 대 V2 판정 1:1 대조

| # | V1 결함 | V1 심각도 | 재현 | 귀속 (누가 만들었나) | 이 가지 범위? | V2 판정 |
|---|---|---|---|---|---|---|
| 1 | 전역 지침에 플랫폼별 엔진 순서 문장 없음 → `check-strict-principles-skills.sh` FAIL | 높음 | **재현 O** (rc=1, `CODEX_ENGINE_ORDER_INVALID`/`CLAUDE_ENGINE_ORDER_INVALID`) | Git 밖 전역 파일. 해시가 착수 전 값 `a277178…` 그대로 → **3커밋 아님** (추정: f12ea33 세션의 전역 동기화) | **아니오** — AC-5가 그 파일 불변을 요구 | 유효한 결함이나 **범위 밖 + 자진 신고분**. 심각도 높음→**중간**으로 조정. 후속 이슈 |
| 2 | P3 3상태 대 5상태 충돌 | 높음 | **부분 재현** — 근거 3개 중 1개만 성립 | 전역 `SKILL.md:60`("검사 결과인 `PASS/FAIL/NOT_RUN/BLOCKED/SKIPPED`")만 P3와 진짜 충돌. **3커밋 아님** | **아니오** — 동일하게 AC-5가 금지 | `strict-workflow.md:20`·`verification-commands.md:68` 인용은 **오탐**. 남은 1건은 범위 밖. 심각도 높음→**중간** |
| 3 | 검사 단계 26 대 27 | 중간 | **재현 O** — CI `- name:` **27개**, 문서 표 **26행**, 누락분 = "PostgreSQL 서버 준비" | "26개 전부" 문장 = `b5eecc6`(2026-09-05 01:04). PostgreSQL 스텝 = `0ef232a`(2026-09-05 01:23). **19분 뒤 낡음, 5일 전 일** | **아니오** — 3커밋은 3행만 수정, 표(22~57행) 미접촉 | 유효한 선행 결함. 범위 밖. 심각도 **중간 유지**. 후속 이슈 |
| 4 | `check-docs-sot.sh` 자체 FAIL (coding-principles.md 20476 > 20000) | 중간 | **재현 O** (rc=1, 바이트 수까지 동일) | f12ea33도 3커밋도 그 파일 미접촉. origin/main에도 동일 | **아니오** | 유효하나 **자진 신고분**(goal 119행 부근). 범위 밖. 후속 이슈 |
| 5 | INDEX가 `P1~P22`, 실제 `P1~P24` | 낮음 | **재현 O** (INDEX.md:5 vs coding-principles.md:**8**) | `d574fb7`(2026-08-08) — **한 달 전** | **아니오** | 유효한 선행 결함. 줄번호 인용 오기(9→8). 범위 밖 |
| — | AC-2 f12ea33 4파일 보존 | PASS | **재현 O** | — | 예 | **PASS 유지** |
| — | AC-3 한정 문구 | PASS | **재현 O + 강화** | 3커밋 (`0761f14`) | 예 | **PASS 유지** — 변이 0→3건으로 상시 참 아님을 독립 확인 |
| — | AC-4 원칙 검사 | FAIL | **재현 실패 → 무효** | — | 예 | **PASS로 뒤집음** (종료값 0, CHECKED 34) |
| — | AC-5 전역 해시 | PASS | **재현 O** | — | 예 | **PASS 유지** |
| — | goal 장부 재현 | FAIL | **재현 실패 → 무효** | — | 예 | **PASS로 뒤집음** (7개 명령 전부 장부와 일치) |
| — | RED 인용 정확성 | PASS | **재현 O** | — | 예 | **PASS 유지** — f12ea33 실제 3줄과 문자 단위 일치 |
| — | 문서 간 기준 충돌 없음 | FAIL | 부분 | 전부 선행 | 아니오 | **범위 밖으로 분리**. 판정에 미반영 |

### 3-4. V2가 새로 올리는 결함 3건

| # | 심각도 | 제목 | 이 가지 범위? |
|---|---|---|---|
| N1 | **중간** | 「INDEX 등재」 게이트가 이미 무효인 관행 위에 세워졌습니다 | **예 — 이 가지가 쓴 문장** |
| N2 | **중간** | 새 정본 `strict-workflow.md` 가 정본 검사기의 목록에 없습니다 | 경계 (f12ea33 귀속) |
| N3 | 낮음 | `acceptance-0-5` FAIL — 본줄기 커밋 `f12ea33` 미전송 | 배송 전제 |

---

## 4. 결함 상세 (V2 신규 3건)

### N1. 중간 · 신규 — 「'INDEX에 등재된 경우에만' 이라는 조건이 이미 성립하지 않는 관행 위에 세워졌습니다」

**원인.** 이 가지가 새로 쓴 조건 문구는 세 곳 모두 "그 파일이 **INDEX에 등재된 경우에만** 정본으로 삼는다"입니다. 작업자는 goal 문서에서 이 선택의 위험을 스스로 이렇게 적었습니다 — *"틀리면 깨지는 것: 한정 문구의 기준을 'INDEX 등재'로 둔 것이 틀리면(예: **파일은 있는데 INDEX에 안 올리는 관행이 생기면**) 정본이 있어도 무시된다."*

그 관행은 **생길 예정이 아니라 이미 있습니다.** `docs/sot/` 12개 파일을 INDEX와 전수 대조한 결과, `principles.yaml` 과 `mechanism-registry.yaml` 두 개가 실존하는데 INDEX에 없습니다. 그리고 `principles.yaml` 은 **바로 그 조건 문구가 들어 있는 문서 자신이 "Strict 실행 시작 시 직접 읽으라"고 지시하는 파일**입니다(`strict-workflow.md:60`). 즉 "INDEX에 없으면 정본이 아니다"라는 방금 세운 규칙이, 같은 문서 같은 줄에서 이미 반증됩니다.

더 정확히는 **확장자 관행**으로 보입니다. INDEX에 등재된 9개는 전부 `.md` 이고, 미등재 2개는 전부 `.yaml` 입니다. 그리고 이번에 조건을 건 `work-unit-policy.yaml` 도 **`.yaml`** 입니다.

- [`docs/sot/strict-workflow.md:5` — Work Unit 필드 소유권에 INDEX 등재 조건을 건 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910/docs/sot/strict-workflow.md:5)
- [`docs/sot/strict-workflow.md:60` — 같은 조건을 읽기 대상에 건 줄. 동시에 `principles.yaml` 을 무조건 읽으라고 지시하는 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910/docs/sot/strict-workflow.md:60)
- [`docs/sot/verification-commands.md:3` — 같은 조건을 Work Unit 값 소유권에 건 줄](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910/docs/sot/verification-commands.md:3)
- [`docs/sot/INDEX.md:5~13` — 등재 목록 9개. `principles.yaml`·`mechanism-registry.yaml` 없음](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910/docs/sot/INDEX.md:5)

```text
INDEXED   coding-principles.md
INDEXED   git-workflow.md
INDEXED   hook-contracts.md
INDEXED   humansearch-browser-contract.md
INDEXED   humansearch-l0-surface-contract.md
NOT_INDEXED INDEX.md
INDEXED   invoice-storage.md
INDEXED   invoice.md
NOT_INDEXED mechanism-registry.yaml
NOT_INDEXED principles.yaml
INDEXED   strict-workflow.md
INDEXED   verification-commands.md
```

→ `docs/sot/` 실제 파일 전수를 INDEX.md 링크와 대조한 결과입니다. `.yaml` 두 개가 미등재이고, 그중 `principles.yaml` 은 34개 원칙 장부로 `acceptance-principles-check.sh` 가 매번 로드하는 살아 있는 정본입니다(§5.3 출력의 `LEDGER_LOAD: PASS docs/sot/principles.yaml`).

**사업 영향.** `work-unit-policy.yaml` 이 나중에 `docs/sot/` 로 병합되더라도 기존 `.yaml` 관행대로 INDEX에 오르지 않으면, 조건 문구가 **영구히 "아직 아님" 상태로 고정**됩니다. 그러면 Work Unit 정본이 실제로 존재하는데도 모든 Strict 세션이 계속 `git-workflow.md` 폴백만 읽습니다. 조용한 실패입니다 — 아무도 오류를 보지 못한 채 새 정본이 무시됩니다. 이것은 P3(조용한 실패 금지)가 막으려는 바로 그 형태입니다.

> **무엇을** — 조건의 기준을 "INDEX 등재"에서 "`docs/sot/work-unit-policy.yaml` 파일 실존"으로 바꾸거나, `principles.yaml`·`mechanism-registry.yaml` 을 INDEX에 등재해 기준을 실제로 유효하게 만들어야 합니다.
> **왜** — 지금 기준은 저장소의 실제 관행(.yaml은 INDEX에 안 올린다)과 어긋나며, 그 어긋남을 작업자 본인이 goal 문서에 위험으로 적어 두었습니다.
> **버린 길** — ① 지금 이 가지에서 INDEX.md를 함께 고치는 길: INDEX 수정은 f12ea33이 이미 건드린 파일이라 AC-2의 "INDEX diff 0건" 조건을 깨뜨립니다. ② 조건 문구를 아예 없애는 길: 없는 파일을 무조건 정본이라 부르던 원래 결함으로 되돌아갑니다.
> **대가** — "파일 실존" 기준으로 바꾸면 INDEX 등재를 강제하는 힘이 약해집니다. INDEX 등재를 늘리는 쪽은 별도 인수 기준이 필요합니다.
> **되돌리기** — 조건 문구는 `0761f14` 하나를 revert하면 원문으로 돌아갑니다. 다만 그러면 원래의 고아 참조가 부활합니다.

### N2. 중간 · 신규 — 「새 정본 문서가 정본 검사기의 시야 밖에 있습니다」

**원인.** `scripts/check-docs-sot.sh` 는 검사할 필수 파일을 **5개만 하드코딩**합니다. `f12ea33` 은 새 정본 `docs/sot/strict-workflow.md` 를 만들고 INDEX.md에 등재까지 했지만, 이 목록에는 넣지 않았습니다. 결과적으로 새 정본은 존재 여부도 크기 예산도 **전혀 검사받지 않습니다.**

같은 구멍이 더 큰 것도 가립니다. `docs/sot/humansearch-browser-contract.md` 는 **30387바이트**로 검사기의 20000바이트 예산을 52% 초과하지만, 목록에 없어서 통과도 실패도 하지 않고 그냥 안 보입니다.

- [`scripts/check-docs-sot.sh:16` — "필수 파일 **5개**"라고 스스로 선언하는 주석](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910/scripts/check-docs-sot.sh:16)
- [`scripts/check-docs-sot.sh:21-25` — 하드코딩된 5개 배열. `strict-workflow.md` 없음](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910/scripts/check-docs-sot.sh:21)

```text
   20476 docs/sot/coding-principles.md      ← 검사 대상, FAIL
    2225 docs/sot/git-workflow.md           ← 검사 대상
    4911 docs/sot/hook-contracts.md         ← 검사 대상
   30387 docs/sot/humansearch-browser-contract.md  ← 목록 밖, 예산 52% 초과인데 미검출
    7407 docs/sot/humansearch-l0-surface-contract.md ← 목록 밖
    1800 docs/sot/INDEX.md                  ← 검사 대상
    8742 docs/sot/invoice-storage.md        ← 목록 밖
   16413 docs/sot/invoice.md                ← 목록 밖
    5233 docs/sot/strict-workflow.md        ← 목록 밖 (f12ea33이 새로 추가한 정본)
    9202 docs/sot/verification-commands.md  ← 검사 대상
    4817 docs/sot/mechanism-registry.yaml   ← 목록 밖
   18629 docs/sot/principles.yaml           ← 목록 밖
```

→ 12개 중 5개만 검사받습니다. 검사기가 "5개 중 4개 통과"라고 초록에 가까운 인상을 주지만, 실제로는 **예산 초과 파일 1개가 시야 밖에서 통과 처리**되고 있습니다. 이것은 메모리에 기록된 "표본은 '그 규칙만 잡는가'까지 봐라" 와 같은 계열의 함정입니다 — 검사가 도는 것과 검사가 대상을 보는 것은 다릅니다.

**보강.** 이 검사기는 애초에 `hooks/pre-push` 에도 `.github/workflows/verify.yml` 에도 배선돼 있지 않습니다(V1 결함 4가 맞게 지적한 부분). 즉 **아무도 돌리지 않는 검사기가, 돌더라도 절반 이하만 봅니다.**

**사업 영향.** 앞으로 정본을 추가할 때마다 검사 사각지대가 늘어납니다. "정본 체계가 검사받고 있다"는 믿음이 근거를 잃고, 계약 문서에 서술이 섞여 비대해지는 것을 막으려던 20000바이트 예산이 새 파일에는 전혀 적용되지 않습니다.

> **무엇을** — 목록 하드코딩을 `docs/sot/*.md` 글롭 순회로 바꾸고, 예산 초과분(`humansearch-browser-contract.md`, `coding-principles.md`)의 처리 계획을 함께 세워야 합니다.
> **왜** — 정본을 추가할 때 검사기 목록 갱신을 사람이 기억해야 하는 구조는 반드시 갈라집니다.
> **버린 길** — 목록에 `strict-workflow.md` 한 줄만 추가하는 길: 같은 구멍이 다음 파일에서 그대로 재발합니다.
> **대가** — 글롭으로 바꾸면 기존 초과 파일 2개 때문에 검사기가 즉시 빨개집니다. 그 자체는 정직한 상태지만 배선 전에 정리가 필요합니다.
> **되돌리기** — 배열을 원래 5줄로 되돌리면 됩니다.

### N3. 낮음 · 신규 — 「본줄기 커밋 `f12ea33` 이 원격에 없어 배송 검사가 빨갛습니다」

**원인.** 로컬 `main` 이 `f12ea33` 을 가리키는데 `origin/main` 은 `fc6beed` 입니다. 워크트리 없이 본줄기에 직접 올린 커밋이 아직 전송되지 않은 상태입니다.

```text
$ bash scripts/acceptance-0-5.sh
FAIL: origin/main(fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b) != main(f12ea335a0fd323bb3eec3ca0e300ae1ca9b0717) — push 미완료
```

→ `acceptance-0-5` 는 "push가 완료됐는가"를 보는 검사입니다. 다만 `hooks/pre-push:65` 의 `DEFERRED="acceptance-0-5 acceptance-0-7"` 목록에 들어 있어 **push 자체는 막히지 않습니다**(push 직전에 "push가 끝났나"를 묻는 건 논리적으로 성립할 수 없어 CI 담당으로 넘긴 설계).

**사업 영향.** 이 가지가 `f12ea33` 을 조상으로 담고 있으므로 이 PR이 병합되면 자연히 해소됩니다. 다만 병합 전까지는 이 저장소에서 새로 파는 **모든 워크트리의 `acceptance-0-5` 가 계속 FAIL**로 뜹니다. goal 문서 RED 절도 이 점을 명시했습니다. **작업물의 결함이 아니라 배송 순서의 전제 조건**으로 기록합니다.

---

## 5. 기술 상세와 증거 원문

### 5.1 실행 신원

```text
workdir=/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910
engine=Claude Opus 5 (1M) · session_01CjNP65FKtFC1UXF42CcM8a
start=2026-09-10 22:37:24 +0900
HEAD=7fc4334a794c72ebf294d0f7df44f377272ebc3c
branch=task/strict-workflow-sot-20260910
git status --porcelain=v1 = (빈 출력)
```

→ V1이 검증한 것과 **같은 HEAD, 같은 브랜치**이고 작업공간은 깨끗했습니다. 두 판정이 같은 대상을 본 것이 맞습니다.

```text
$ git log --oneline -6
7fc4334 strict SOT goal 문서의 검증 장부를 실제 실행 출력으로 채운다
0761f14 strict SOT가 없는 work-unit-policy.yaml을 무조건 정본으로 지목하지 않게 한정한다
feb16a5 strict SOT 없는 파일 참조를 RED로 고정한다
f12ea33 Unify strict workflow across Codex and Claude
fc6beed 실패 누락과 main 대기 검사 취소를 막는다 (#81)
```

→ 기준 커밋 `f12ea33` 위에 정확히 3커밋입니다. RED 고정 → 수정 → 장부 채움 순서로, 게이트 2(RED 먼저)를 지킨 순서입니다.

### 5.2 이 가지 3커밋이 실제로 무엇을 건드렸는가 (범위 이탈 공격)

```text
$ git diff --stat f12ea33 HEAD
 .../strict-cross-platform-sot-goal-2026-09-10.md   | 112 ++++++++++++++++++++-
 docs/sot/strict-workflow.md                        |   4 +-
 docs/sot/verification-commands.md                  |   2 +-
 3 files changed, 111 insertions(+), 7 deletions(-)
```

→ 착수 프롬프트가 선언한 변경 파일 3개와 **정확히 일치**합니다. 소스 코드·스크립트·CI 워크플로·훅은 한 줄도 건드리지 않았습니다.

정본 문서 쪽 실제 변경은 **딱 3줄**입니다(`strict-workflow.md` 5행·60행, `verification-commands.md` 3행). 나머지 111줄은 전부 `docs/engineering/` goal 문서입니다. 즉 **SOT 문구 외에 다른 것을 건드리지 않았습니다.**

```text
$ git show --stat --oneline 7fc4334
7fc4334 strict SOT goal 문서의 검증 장부를 실제 실행 출력으로 채운다
 .../strict-cross-platform-sot-goal-2026-09-10.md   | 87 +++++++++++++++++++-
 1 file changed, 83 insertions(+), 4 deletions(-)
```

→ 요청받은 확인입니다. **마지막 커밋 `7fc4334` 는 `docs/engineering/` 한 파일만 바꿨습니다.** 정본(`docs/sot/`)은 `0761f14` 에서 확정된 뒤 변하지 않았습니다. 이것이 §5.10의 장부 유효성 판정을 뒷받침합니다.

```text
$ git log -p f12ea33..HEAD | grep -n 'no-verify'
[매치 0건, rc=1]
```

→ 3커밋의 본문·메시지 어디에도 `--no-verify` 흔적이 없습니다. 다만 §0에 적었듯 Git 객체만으로 훅 우회 부재를 증명할 수는 없습니다.

### 5.3 AC-4와 형식 검사 — V1의 FAIL 2건을 뒤집은 실측

V1이 환경 제약으로 실패했다고 적은 세 명령을, **같은 원명령 그대로** 실행했습니다.

```text
$ bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT=0
```

→ **AC-4 합격입니다.** 종료값 0, `VERDICT: PASS`, 검사 대상 34건. V1이 적은 "종료값 1, `CHECKED: 0`" 은 재현되지 않습니다. 중요한 것은 `CHECKED: 34` 라는 숫자입니다 — 0건 통과(검사 대상이 없어서 그냥 통과)가 아니라 34개 원칙 전부에 대해 정본 문구·기계 장치·pre-push/CI 배선을 실제로 대조한 결과입니다. `TMPDIR` 을 손대지 않은 기본 환경에서 나온 값입니다.

```text
$ uv run --with pyyaml ~/.claude/skills/skill-creator/scripts/quick_validate.py ~/.codex/skills/strict
Skill is valid!
EXIT=0

$ uv run --with pyyaml ~/.claude/skills/skill-creator/scripts/quick_validate.py ~/.claude/skills/strict
Skill is valid!
EXIT=0
```

→ **양쪽 다 합격**입니다. goal 문서 장부가 적어 둔 출력(`Skill is valid!` / `rc=0`)과 문자 단위로 같습니다. V1의 `Failed to initialize cache at /Users/kangsangmo/.cache/uv … Operation not permitted (os error 1)` 은 재현되지 않습니다.

**환경 차이라는 결론의 근거.** V1의 두 실패 메시지는 `Operation not permitted` (운영체제 권한 거부)이고, 하나는 `mktemp: mkdtemp failed`, 다른 하나는 `failed to open file .../.cache/uv/sdists-v9/.git` 입니다. 둘 다 **검사 로직이 아니라 파일 쓰기 자체**가 거부된 형태이고, V1은 `TMPDIR=/tmp` 로 재시도했으나 같은 거부를 받았습니다. 제 환경에서는 같은 명령이 임시 폴더와 캐시를 정상 생성하며 실질 출력을 냈습니다. 따라서 **작업물의 결함이 아니라 V1 실행 환경(Codex 샌드박스)의 쓰기 차단**이 원인이라고 판정합니다. 이는 메모리에 이미 기록된 "codex 샌드박스가 mktemp를 막는다" 와 같은 계열의 반복 사고입니다.

### 5.4 AC-2 · AC-5 재현

```text
$ git diff --stat f12ea33 task/strict-workflow-sot-20260910 -- docs/sot/INDEX.md
[출력 없음] rc=0

$ git merge-base --is-ancestor f12ea33 HEAD
rc=0

$ git show --stat --oneline f12ea33
 .../strict-cross-platform-sot-goal-2026-09-10.md   | 36 +++++++++++++
 docs/sot/INDEX.md                                  |  1 +
 docs/sot/strict-workflow.md                        | 60 ++++++++++++++++++++++
 docs/sot/verification-commands.md                  |  2 +
 4 files changed, 99 insertions(+)
```

→ **AC-2 합격.** `f12ea33` 이 HEAD의 조상이고, 그 커밋이 만든 INDEX 변경은 한 글자도 손실되지 않았습니다. `strict-workflow.md` 가 60줄짜리 **신규 파일**로 만들어진 것도 확인됩니다 — 이 사실이 §5.5·§5.6의 귀속 판정에 결정적입니다.

```text
$ shasum -a 256 ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md
a277178adaeb51e008bd1637a7be2d1d33649d113ddb2c750acf54f85856270a  /Users/kangsangmo/.codex/skills/strict/SKILL.md
a277178adaeb51e008bd1637a7be2d1d33649d113ddb2c750acf54f85856270a  /Users/kangsangmo/.claude/skills/strict/SKILL.md

$ cmp ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md
cmp rc=0
```

→ **AC-5 합격.** 두 전역 파일이 착수 전 해시 그대로이고 서로 바이트 동일합니다. **이 결과가 V1 결함 1·2의 범위 판정을 결정합니다** — 계약이 "이 해시를 유지하라, 다르면 FAIL" 이라고 규정한 파일을, V1은 "고쳐야 한다"고 요구했습니다. 두 요구는 동시에 만족될 수 없습니다.

### 5.5 AC-3 — 문법상 한정인가, 진짜 작동하는 한정인가

```text
$ grep -n 'work-unit-policy.yaml' docs/sot/strict-workflow.md docs/sot/verification-commands.md
docs/sot/strict-workflow.md:5:… Work Unit의 필드는 `work-unit-policy.yaml`이 `docs/sot/`에 실존하고 INDEX에 등재된 경우에만 그 파일이 소유하며, 병합 전까지는 git-workflow.md 의 "작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개" 규약이 Work Unit 경계의 정본입니다. …
docs/sot/strict-workflow.md:60:… `docs/sot/work-unit-policy.yaml`은 INDEX에 등재된 경우에만 함께 읽으며(병합 전까지는 git-workflow.md 의 작업 단위 규약을 대신 읽는다), …
docs/sot/verification-commands.md:3:… Work Unit 값은 `work-unit-policy.yaml`이 INDEX에 등재된 경우에만 그 파일이 소유한다(병합 전까지는 git-workflow.md 의 작업 단위 규약이 정본). …

무한정 매치 = 0
```

→ 세 줄 모두 한정됐습니다. 그런데 counter-AC가 묻는 것은 **"문법상만 붙었는가"** 입니다. 그래서 폴백이 실체가 있는지 직접 확인했습니다.

```text
$ grep -n '작업 1개' docs/sot/git-workflow.md
15:작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개.
```

→ **폴백은 실체가 있습니다.** `strict-workflow.md:5` 가 인용한 문장이 `git-workflow.md:15` 에 **글자 그대로 존재**합니다. 즉 읽는 사람은 없는 파일을 찾아 헤매는 대신 실존하는 규약으로 안내받습니다. 문법상 한정이 아니라 **작동하는 한정**입니다.

**파일 삭제로 통과시킨 것 아닌가** (counter-AC):

```text
$ ls docs/sot/
coding-principles.md  git-workflow.md  hook-contracts.md
humansearch-browser-contract.md  humansearch-l0-surface-contract.md
INDEX.md  invoice-storage.md  invoice.md  mechanism-registry.yaml
principles.yaml  strict-workflow.md  verification-commands.md

$ git ls-tree origin/main docs/sot/ | grep -c work-unit
0
```

→ 아닙니다. `work-unit-policy.yaml` 은 origin/main에도 원래 없었습니다. 삭제된 적이 없으므로 삭제로 통과시킨 것이 아닙니다.

**다른 고아 참조가 남아 있는가** (counter-AC):

`strict-workflow.md` 전문(60줄)에서 참조하는 파일 경로는 `coding-principles.md`, `principles.yaml`, `git-workflow.md`, `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, 그리고 한정된 `work-unit-policy.yaml` 이 전부입니다. 스크립트 경로 참조는 0건입니다. 한정된 것 하나를 빼면 **전부 `ls` 로 실존이 확인됩니다.** 새 고아 참조 0건입니다.

**변이 공격 — 검사가 상시 참인가** (§0에 적은 재시도본):

```text
대조군 무한정매치 = 0
MUTATION_APPLIED_OK
--- 변이가 실제로 파일을 바꿨는지(대조) ---
sw.md 변경됨 OK
vc.md 변경됨 OK
변이 후 무한정매치 = 3
```

→ 조건 문구를 3곳 모두에서 제거한 고장 사본에서 검사가 **0건 → 3건**으로 정확히 뒤집힙니다. `MUTATION_APPLIED_OK` 는 치환 대상 문자열이 실제로 발견됐다는 `assert` 통과 표시이고, `변경됨 OK` 는 변이본이 원본과 다르다는 `diff -q` 대조 결과입니다. **이 두 단계가 없었다면 첫 시도의 조용한 치환 실패가 "변이 전부 생존"으로 오독됐을 것입니다.** AC-3 검사는 껍데기가 아닙니다.

**V1 결함 2의 근거 3개를 원문으로 대조합니다:**

```text
docs/sot/coding-principles.md:18
| **P3** | **조용한 실패 금지** | ① 판정은 `PASS / FAIL / NOT_RUN` **3상태**. `NOT_RUN` 이 하나라도 있으면 전체 판정은 PASS 불가 ② …

docs/sot/strict-workflow.md:20
등급을 낮추기 위해 섹션을 생략하지 않습니다. 해당 없음은 `NOT_APPLICABLE`, 미실행은 `NOT_RUN`, 권한 밖은 `BLOCKED`로 구분합니다.

docs/sot/verification-commands.md:68
종료값 `0=PASS / 1=FAIL / 2=NOT_RUN`. **검사 대상 0건은 통과가 아니라 `NOT_RUN`이다**(P20).
```

→ 세 줄을 나란히 놓으면 V1의 판정이 갈라집니다.

- `strict-workflow.md:20` 은 **§2 "적응형 Strict 프롬프트"** 안에 있고(§2 제목은 11행), 같은 줄의 앞 문장이 **"등급을 낮추기 위해 **섹션**을 생략하지 않습니다"** 입니다. 즉 여기서 말하는 `NOT_APPLICABLE`/`NOT_RUN`/`BLOCKED` 는 **프롬프트의 어느 섹션이 이번 작업에 해당하는가**를 표기하는 라벨이지, **검사 명령의 판정**이 아닙니다. V1은 이 둘을 같은 것으로 읽었습니다. **오탐입니다.**
- `verification-commands.md:68` 은 `0=PASS / 1=FAIL / 2=NOT_RUN` 으로 **P3의 3상태를 그대로 재확인**합니다. V1은 이 줄을 충돌의 한 축으로 인용했는데, 실제로는 **일치의 증거**입니다. **오탐입니다.**
- 남는 것은 전역 파일 한 줄뿐입니다:

```text
$ sed -n '60p' ~/.codex/skills/strict/SKILL.md
검사 결과인 `PASS / FAIL / NOT_RUN / BLOCKED / SKIPPED`와 제품 배송 상태를 섞지 않는다. …
```

→ 이것은 **"검사 결과"라고 명시하며 5개를 나열**하므로 P3의 3상태와 **진짜 충돌**합니다. V1의 지적 자체는 옳습니다. 다만 ① 이 파일은 Git 밖 전역 파일이고 ② 해시가 착수 전 값 그대로이므로 이 가지가 만든 것이 아니며 ③ AC-5가 그 파일의 변경을 금지합니다. **유효하나 범위 밖**입니다.

한 가지 덧붙이면, 저장소 검사기 `scripts/verify/check-strict-principles-skills.sh` 는 필수 토큰 목록에 `"PASS / FAIL / NOT_RUN"` 을 요구하는데, 전역 `SKILL.md:24` 에 그 문자열이 있어 이 토큰 검사는 통과합니다. 즉 **검사기도 5상태 줄을 잡아내지 못합니다** — 결함 2는 기계 장치가 없는 상태입니다.

### 5.6 V1 결함 3(26 대 27) 재현과 귀속 — `git blame` 실측

```text
$ grep -c '^\s*- name:' .github/workflows/verify.yml
27

$ awk 'NR>=24 && /^\| *[0-9]+ *\|/' docs/sot/verification-commands.md | wc -l
26
```

→ **재현됩니다.** CI 워크플로에 이름 있는 스텝이 27개인데 문서 표는 26행입니다. 누락된 하나는 `verify.yml:260` 의 `- name: PostgreSQL 서버 준비 (Invoice 런타임 검사용)` 입니다. 문서 22행이 "**워크플로 스텝 26개 전부**를 적는다" 고 스스로 선언하므로, 이것은 어림수가 아니라 틀린 수치입니다.

**귀속 — 이 가지가 만든 것인가:**

```text
$ git blame -L 20,27 docs/sot/verification-commands.md
b5eecc60 (acceptance 2026-09-05 22) **워크플로 스텝 26개 전부**를 적는다(…)
4fb61d07 (acceptance 2026-08-12 24) | # | 스텝 이름 | 실행 내용 |

$ git log -1 --format='%h %ad %s' --date=iso b5eecc6
b5eecc6 2026-09-05 01:04:15 +0900 인보이스 저장·검증 작업분을 결함 종결 브랜치로 고정한다

$ git log -1 --format='%h %ad %s' --date=iso 0ef232a
0ef232a 2026-09-05 01:23:10 +0900 게이트가 글자가 아니라 실행을 보게 한다 (WU-3 · D-C, D-G, D-H)
```

→ **아닙니다.** "26개 전부" 문장은 `b5eecc6`(2026-09-05 01:04)이 썼고, PostgreSQL 스텝은 `0ef232a`(2026-09-05 01:23)가 추가했습니다. **19분 뒤에 낡았고, 그로부터 5일이 지났습니다.** `f12ea33` 이 이 파일에 넣은 것은 2줄(3행 SOT 포인터)뿐이고, 이 가지가 바꾼 것도 3행 한 줄뿐입니다. **표(22~57행)는 f12ea33도 이 가지도 건드리지 않았습니다.** V1 자신도 "이 불일치는 이번 가지 전부터 존재했지만" 이라고 인정했습니다.

### 5.7 V1 결함 4·5 재현과 귀속

```text
$ bash scripts/check-docs-sot.sh
PASS: docs/sot/INDEX.md 존재, 1800바이트 (<=20000)
FAIL: docs/sot/coding-principles.md 가 20000바이트 초과 (20476바이트) — 계약과 서술이 다시 섞였을 가능성
PASS: docs/sot/hook-contracts.md 존재, 4911바이트 (<=20000)
PASS: docs/sot/git-workflow.md 존재, 2225바이트 (<=20000)
PASS: docs/sot/verification-commands.md 존재, 9202바이트 (<=20000)
PASS: hooks/pre-commit 가 docs/sot/hook-contracts.md 를 계약으로 참조
… (이하 4줄 PASS)
NOT_RUN이 아니라 FAIL — 위 FAIL 라인을 고친다
rc=1
```

→ **재현됩니다. 바이트 수까지 goal 문서 장부와 동일합니다.** 다만 이 출력에서 **오직 5개 파일만 검사된다**는 점이 V1이 지나친 부분이고, 제 신규 결함 N2의 근거입니다(§4 N2).

```text
$ grep -n 'docs/sot' scripts/check-docs-sot.sh
16:# AC-1: docs/sot/ 필수 파일 5개가 존재하고 각각 20,000바이트를 넘지 않는다.
21:  "docs/sot/INDEX.md"
22:  "docs/sot/coding-principles.md"
23:  "docs/sot/hook-contracts.md"
24:  "docs/sot/git-workflow.md"
25:  "docs/sot/verification-commands.md"
```

→ 하드코딩 5개. `strict-workflow.md` 없음.

**결함 5 재현과 줄번호 정정:**

```text
$ git blame -L 5,5 docs/sot/INDEX.md
d574fb7c (sangmokang 2026-08-08 5) - [coding-principles.md](coding-principles.md) — P1~P22 확정 원칙 표 …

$ grep -n 'P1~P24' docs/sot/coding-principles.md
8:## §1. 확정 원칙 — … v4 전수조사 자체제안 12개를 **P1~P24**로 통합
```

→ 재현됩니다. INDEX는 `P1~P22`, 실제 정본은 `P1~P24` 입니다. 다만 **V1이 인용한 `coding-principles.md:9` 는 틀렸고 실제로는 8행**입니다. 귀속은 `d574fb7`(2026-08-08) — **한 달 전**입니다.

**INDEX 등재 자격 (counter-AC):** V1은 "strict-workflow.md는 두 전역 지침에서 다음 세션의 답으로 참조되므로 등재 자격 충족" 이라고 했습니다. 검증했습니다.

```text
$ grep -rln 'strict-workflow' scripts .github hooks
[매치 0건]

$ grep -n 'strict-workflow' ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md
…/.codex/skills/strict/SKILL.md:10:> **공통 계약:** 저장소 정본 `docs/sot/strict-workflow.md`가 Codex·Claude의 순서·판정·승인 경계를 고정한다. …
…/.codex/skills/strict/SKILL.md:14:`docs/sot/strict-workflow.md`를 먼저 읽고 그 순서를 따른다: …
…/.claude/skills/strict/SKILL.md:10: (동일)
…/.claude/skills/strict/SKILL.md:14: (동일)
```

→ **V1의 판정이 맞습니다.** 스크립트·훅·CI 어디도 이 문서를 참조하지 않지만, INDEX.md:15가 정한 트리거는 "스크립트/훅/CI/**다음 세션이 답으로 참조**" 중 **어느 하나**이고, 두 전역 `SKILL.md` 의 10행·14행이 매 Strict 세션에서 이 문서를 답으로 지목합니다. 등재 자격 충족입니다. 다만 **기계 장치가 없다**는 점(스크립트/훅/CI 참조 0건)은 N2와 함께 후속 과제로 기록합니다.

### 5.8 V1 결함 1 재현과 "자진 신고분" 확인

```text
$ bash scripts/verify/check-strict-principles-skills.sh ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md
VERDICT: FAIL
CODEX_ENGINE_ORDER_INVALID
CLAUDE_ENGINE_ORDER_INVALID
CHECKED: 2
FAILURES: 2
rc=1

$ grep -n 'G=Codex\|G=Claude' ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md
[매치 0건, rc=1]
```

→ **재현됩니다.** 검사기가 요구하는 플랫폼별 엔진 순서 문장이 양쪽 전역 파일에 없습니다.

**배선 확인 — CI가 이걸 잡을 수 있었나:**

```text
$ grep -rn 'check-strict-principles-skills' --include='*.yml' --include='*.sh' . hooks
scripts/acceptance-principles-mutations.sh:267: … "$SKILL_TMP/codex.md" "$SKILL_TMP/claude-mismatch.md" …
scripts/acceptance-principles-mutations.sh:295: … "$SKILL_TMP/codex-500.md" "$SKILL_TMP/claude-500.md" …
scripts/acceptance-principles-mutations.sh:307: … "$SKILL_TMP/codex-501.md" "$SKILL_TMP/claude-500.md" …
```

→ 이 검사기는 **임시 사본(`$SKILL_TMP/...`)에만 적용**되고 실제 전역 파일에는 배선돼 있지 않습니다. 그래서 CI가 못 잡습니다. 이것은 메모리의 "몽키패치로 치운 함수는 무방비가 된다"·"시험이 대상을 안 보면 전부 초록" 과 같은 계열입니다 — **검사기는 존재하고 mutations 시험도 통과하지만, 진짜 대상은 아무도 안 봅니다.**

**자진 신고분 확인:**

```text
$ sed -n '117,121p' docs/engineering/strict-cross-platform-sot-goal-2026-09-10.md
| 검사 | 결과 | 원인 | 처리 |
|---|---|---|---|
| `scripts/verify/check-strict-principles-skills.sh` 를 실제 전역 두 파일에 적용 | FAIL `CODEX_ENGINE_ORDER_INVALID` / `CLAUDE_ENGINE_ORDER_INVALID` | … 이 검사기는 `acceptance-principles-mutations.sh`에서 임시 사본에만 쓰이고 실제 전역 파일에는 배선돼 있지 않아 CI가 잡지 못했다 | 전역 파일은 이 작업의 비범위(AC-5: 바이트 동일 유지)다 … |
| `scripts/check-docs-sot.sh` | FAIL `coding-principles.md 20476바이트 > 20000` | … | 기존 결함. 이 가지의 범위 밖이며 별도 처리 대상으로 기록만 한다 |
```

→ **V1의 결함 1과 4는 구현자가 goal 문서 105~119행에 표로 이미 신고한 내용입니다.** 원인 분석("임시 사본에만 쓰여 CI가 못 잡았다")과 범위 판단("AC-5 때문에 비범위")까지 적혀 있고, 그 분석은 제 실측(§5.8 배선 확인)과 일치합니다. 구현자는 "패리티 완료"를 주장하지 않고 오히려 **"이 검사기 기준으로는 미달"** 이라고 명시했습니다. **숨긴 것이 아니라 드러낸 것입니다.** V1이 이를 신규 발견처럼 제시하고 "높음"을 매긴 것은 과장입니다.

### 5.9 배송 게이트 실측

```text
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked

$ bash scripts/acceptance-0-5.sh
FAIL: origin/main(fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b) != main(f12ea335a0fd323bb3eec3ca0e300ae1ca9b0717) — push 미완료

$ grep -n 'DEFERRED' hooks/pre-push
65:DEFERRED="acceptance-0-5 acceptance-0-7"
154:    acceptance-0-2.sh|acceptance-0-5.sh)
155:      printf '  skip %s (DEFERRED · CI 담당)\n' "$c"
```

→ 비밀 스캔은 통과합니다. `acceptance-0-5` 는 FAIL이지만 `pre-push` 의 DEFERRED 목록에 있어 push를 막지 않습니다(§4 N3).

**기존 검사 파손 여부 — 이 가지가 뭔가 망가뜨렸나:**

```text
$ bash scripts/acceptance-principles-mutations.sh
… PASS: BOUNDARY-501 직접 작성 코드 501줄 — FAIL
PASS: SOURCE-TREE 원본 저장소 상태 불변
CHECKED: 41
VERDICT: PASS

$ bash scripts/acceptance-ci-step-integrity.sh
… PASS: 이유가 적힌 예외는 통과 — 0-5 의 main 전용 조건
PASS: 원본 저장소 상태 불변 — before/after 동일
CHECKED: 24
VERDICT: PASS
```

→ 정본 문구를 실제로 소비하는 두 인수 검사가 각각 41건·24건을 검사하고 **전부 통과**합니다. **이 가지가 기존 검사를 파손하지 않았습니다.** `SOURCE-TREE 원본 저장소 상태 불변` 은 검사기 자신이 대상 저장소를 오염시키지 않았다는 자기 확인입니다(메모리의 "검증기가 오염원이 되는 함정" 대비 장치).

### 5.10 새 각도 공격 — 장부가 다른 HEAD의 출력을 붙여 놓은 것 아닌가

요청받은 상관 맹점입니다. goal 문서 장부는 머리글에 **"HEAD=0761f14"** 라고 적어 두었는데, 현재 HEAD는 `7fc4334` 입니다. **다른 상태에서 나온 출력을 현재 상태의 증거처럼 붙여 놓았다면 그 자체가 가짜 완료**입니다.

깨뜨리려 한 방법과 결과:

1. **마지막 커밋이 정본을 건드렸는가** → 아닙니다. `git show --stat 7fc4334` 가 `docs/engineering/` 한 파일만 보여줍니다(§5.2). 정본 `docs/sot/` 두 파일은 `0761f14` 이후 불변입니다.
2. **장부의 7개 명령을 현재 HEAD에서 재실행했을 때 출력이 갈리는가** → 갈리지 않습니다. 전수 대조:

| 장부가 적은 명령 | 장부의 출력 | V2가 HEAD=7fc4334에서 재실행 | 일치 |
|---|---|---|---|
| `cmp` 전역 두 파일 | `rc=0` | `rc=0` | 일치 |
| `shasum -a 256` 양쪽 | `a277178…` 두 줄 | 동일 | 일치 |
| `quick_validate.py` codex | `Skill is valid!` `rc=0` | 동일 | 일치 |
| `quick_validate.py` claude | `Skill is valid!` `rc=0` | 동일 | 일치 |
| `git diff --check f12ea33 HEAD` | `rc=0` | `rc=0` | 일치 |
| `acceptance-principles-check.sh` | `VERDICT: PASS … CHECKED: 34` `rc=0` | 동일 (§5.3) | 일치 |
| `check-strict-principles-skills.sh` | `VERDICT: FAIL … FAILURES: 2` `rc=1` | 동일 (§5.8) | 일치 |
| `check-docs-sot.sh` | 5줄 판정 + 바이트 수 | 동일, 바이트까지 (§5.7) | 일치 |

→ **8건 전부 일치합니다.** 특히 `check-docs-sot.sh` 의 `1800`·`20476`·`4911`·`2225`·`9202` 바이트가 전부 같다는 것은 장부가 **꾸며낸 출력이 아니라 실제 실행 결과**임을 뒷받침합니다. `9202` 는 이 가지가 3행을 고친 **뒤**의 크기이므로, 장부가 수정 이전 상태에서 나온 것도 아닙니다. 정직하게 실패까지(FAIL 2건) 적은 점도 확인됩니다.

3. **RED 절 인용이 f12ea33 실제 내용과 맞는가** → 맞습니다.

```text
$ git show f12ea33:docs/sot/strict-workflow.md      → sw.md
$ git show f12ea33:docs/sot/verification-commands.md → vc.md
$ grep -n 'work-unit-policy.yaml' sw.md vc.md
sw.md:5:… 원칙의 수치와 Work Unit의 필드는 각각 `coding-principles.md`, `principles.yaml`, `work-unit-policy.yaml`이 소유합니다. …
sw.md:60:Strict 실행 시작 시 `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/work-unit-policy.yaml`, 이 문서를 직접 읽고 관련 acceptance/hook/CI 배선을 실행합니다. …
vc.md:3:… 원칙 수치는 `coding-principles.md`, Work Unit 값은 `work-unit-policy.yaml`이 소유하며 이 문서에 복제하지 않는다.
```

→ goal 문서 RED 절이 인용한 착수 시점 3줄과 `f12ea33` 실제 내용이 **문자 단위로 같습니다.** 3줄 모두 조건 없이 `work-unit-policy.yaml` 을 정본으로 지목하고 있어, 이것이 고쳐야 할 RED였다는 주장도 사실입니다. **RED를 사후에 만들어 붙인 흔적은 없습니다.**

4. **착수 프롬프트는 "2건"이라 했는데 장부는 "3건"으로 정정했다** → 실측이 맞습니다. 위 grep이 3줄을 보여줍니다. **프롬프트를 실측으로 정정한 것이므로 정직한 방향의 정정**입니다.

**결론: 장부의 HEAD 불일치는 실질적 문제가 아닙니다.** 마지막 커밋이 정본을 건드리지 않았고, 8개 명령 전부가 현재 HEAD에서 동일하게 재현되기 때문입니다. **다만 장부에 `HEAD=0761f14` 라고만 적고 "이후 `7fc4334` 는 `docs/engineering/` 만 변경하므로 이 출력은 유효" 라는 한 줄이 없는 것은 흠**입니다 — 다음 독자가 이 대조를 처음부터 다시 해야 합니다. 낮은 심각도의 문서 개선 사항으로 기록합니다.

---

## 6. 반증 기록 — 깨뜨리려다 실패한 것들

작업물을 불합격시키려고 시도한 공격과 그 결과입니다. 성공한 것만 결함으로 올렸습니다.

| # | 공격 | 결과 |
|---|---|---|
| 1 | AC-3 한정이 **문법상만** 붙었다고 보고, 폴백으로 지목된 `git-workflow.md` 규약이 실제로는 없음을 보이려 함 | **실패** — `git-workflow.md:15` 에 인용 문장이 글자 그대로 존재 |
| 2 | AC-3 검사가 **상시 참**(뭘 해도 통과)임을 보이려 변이 주입 | **실패** — 0건 → 3건으로 정확히 뒤집힘. 단 1차 시도의 조용한 치환 실패는 §0에 재시도로 기록 |
| 3 | `strict-workflow.md` 에 **다른 고아 참조**가 남아 있음을 보이려 전체 참조를 `ls` 대조 | **실패** — 참조 파일 전부 실존, 스크립트 경로 참조 0건 |
| 4 | 3커밋이 **SOT 문구 외 다른 것**을 건드렸음을 보이려 diff 전문 검토 | **실패** — 정본 변경은 정확히 3줄, 나머지는 goal 문서. 소스·CI·훅 0줄 |
| 5 | goal 장부가 **다른 HEAD의 출력**을 붙였음을 보이려 8개 명령 전수 재실행 | **실패** — 8건 전부 일치, 바이트 수까지 동일 |
| 6 | RED 절이 **사후 조작**임을 보이려 `git show f12ea33:` 로 원본 대조 | **실패** — 3줄 문자 단위 일치 |
| 7 | 이 가지가 **기존 검사를 파손**했음을 보이려 관련 인수 검사 2종 실행 | **실패** — 41건·24건 전부 통과 |
| 8 | AC-5 전역 해시가 **몰래 바뀌었음**을 보이려 해시·cmp 재측정 | **실패** — 착수 전 값과 동일, 바이트 동일 |
| 9 | 커밋에 **`--no-verify` 흔적**이 있음을 보이려 `git log -p` 전량 grep | **실패** — 0건 (단, 부재의 증명은 불가) |
| 10 | 새 조건 문구의 **기준(INDEX 등재)이 무효**임을 보이려 docs/sot 전수 대조 | **성공** → 결함 N1 |
| 11 | `check-docs-sot.sh` 가 **대상을 다 보지 않음**을 보이려 목록과 실제 파일 대조 | **성공** → 결함 N2 |
| 12 | **원격 상태**로 배송이 막힘을 보이려 `acceptance-0-5` 실행 | **성공(부분)** → 결함 N3, 단 pre-push는 DEFERRED로 통과 |

---

## 7. 후속 이슈 등록 권고 (병합 조건)

| 우선순위 | 항목 | 출처 |
|---|---|---|
| 1 | 전역 `SKILL.md` 두 파일에 플랫폼별 엔진 순서 문장을 넣고, `check-strict-principles-skills.sh` 를 **실제 전역 파일에** 배선한다. 같은 작업에서 5상태 줄과 P3 3상태의 충돌을 정리한다 | V1 결함 1·2 |
| 2 | `check-docs-sot.sh` 를 글롭 순회로 바꾸고 CI/pre-push에 배선한다. 예산 초과 2건(`coding-principles.md` 20476, `humansearch-browser-contract.md` 30387) 처리 계획을 함께 세운다 | V1 결함 4 + V2 N2 |
| 3 | `verification-commands.md` 스텝 표를 27개로 갱신하고, 워크플로 변경 시 표 동기화를 강제하는 검사를 붙인다 | V1 결함 3 |
| 4 | 조건 문구의 기준을 재검토한다 — "INDEX 등재" 대신 "파일 실존", 또는 `principles.yaml`·`mechanism-registry.yaml` INDEX 등재로 기준을 실제 유효하게 만든다 | **V2 N1 (이 가지 범위 내)** |
| 5 | `INDEX.md:5` 의 `P1~P22` 를 `P1~P24` 로 갱신한다 | V1 결함 5 |
| 6 | goal 장부에 "이후 `7fc4334` 는 `docs/engineering/` 만 변경하므로 이 출력은 현재 HEAD에서도 유효" 한 줄을 추가한다 | V2 §5.10 |

**배송 전제:** 병합 전 본줄기 직접 커밋 `f12ea33` 의 처분(이 PR로 흡수 / main revert)이 사람 승인 사안으로 남아 있습니다.

---

## 8. 실행 신원 (마감)

```text
verifier=V2 (2차 적대 검증)
engine=Claude Opus 5 (1M context), claude-opus-5[1m]
caller_session=session_01CjNP65FKtFC1UXF42CcM8a
workdir=/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-workflow-sot-20260910
start=2026-09-10 22:37:24 +0900
end=2026-09-10 22:49:07 +0900
HEAD (시작)=7fc4334a794c72ebf294d0f7df44f377272ebc3c
HEAD (종료)=7fc4334a794c72ebf294d0f7df44f377272ebc3c
branch=task/strict-workflow-sot-20260910
git status --porcelain (시작) = (빈 출력)
git status --porcelain (종료) = (빈 출력)
전역 SKILL.md 해시 (종료) = a277178adaeb51e008bd1637a7be2d1d33649d113ddb2c750acf54f85856270a (양쪽 동일, 착수 전 값 유지)
임시 파일 위치=/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/29caa2f2-214f-497b-aa7f-2d4decb53d28/scratchpad/v2tmp/
저장소·전역 파일·git 상태 변경=없음 (읽기 전용 수행)
```

→ 시작과 종료 모두 HEAD가 같고 작업공간이 깨끗하며, 전역 파일 해시도 착수 전 값 그대로입니다. **검증자인 제가 검증 대상을 오염시키지 않았습니다** — 메모리에 기록된 "검증기가 오염원이 되는 함정" 을 피하기 위한 자기 확인입니다.
