# ChatGPT 검증체계 피드백 8항목 — 채택 판정 (2026-08-20)

위험등급: **L1**(분석·조언, 코드 변경 없음) — 다만 권고 대상은 L3 검증 인프라다.
원문: `~/.claude/paste-cache/59ab0e48542961f4.txt` (337줄, 2026-08-20 15:56 수신).
정본 로드: `docs/sot/coding-principles.md`(72줄) · `docs/sot/principles.yaml`(32항목) 직접 읽음.
`bash scripts/acceptance-principles-check.sh` → `VERDICT: PASS`, exit=0, 2026-08-20 15:58 KST, HEAD `7bd3298` — **정정: 세션 중 `69c1849`로 이동함(PR #16 병합). 아래 수치는 V2에서 `69c1849` 기준으로 재측정했다.**

## 결론

ChatGPT의 8개 지적 중 **실제로 지금 구멍인 것은 3개**(#2 검사 무력화, #4 SHA 귀속, #7 복구 상태 보존)이고,
그중 #7은 이 문서를 쓰면서 **고장 주입으로 재현에 성공**했다. 나머지 5개는 이미 있는 규칙과 중복이거나,
이 저장소의 GitHub 요금제 때문에 제안한 형태로는 **구현 자체가 불가능**하다.

사장님이 "복잡하다"고 보신 라벨 5종(`IMPLEMENTATION_DONE`/`LOCAL_VERIFIED`/`CI_VERIFIED`/`LIVE_VERIFIED`/`MERGEABLE`)은
**기각한다.** P3가 이미 3상태(PASS/FAIL/NOT_RUN)를 쓰고 V-3가 라이브 1건을 요구하므로 4개는 이름만 바뀐 중복이다.
새로 얻는 것은 딱 하나 — **"어느 커밋에서 초록이 났는가"** 뿐이고, 그건 라벨이 아니라 값(SHA) 하나면 된다.

**사장님이 결정하실 것 2개:**
1. GitHub Pro(월 $4)로 올릴 것인가. 지금 branch protection·rulesets가 **둘 다 403**이라, ChatGPT의 #1·#9·#10(구현자에게 병합권 없음)은
   기계로 강제할 방법이 없다. 스크립트로 흉내내면 그 스크립트를 구현자가 고칠 수 있어 같은 문제가 재발한다.
2. 아래 3개 중 어디부터 착수할 것인가(권고 순서: R2 → R1 → R3).

## 판단 근거

ChatGPT의 진단은 정확하다 — "검사의 존재를 검증했지 의미를 검증하지 않았다"가 이 저장소의 현재 상태다. 실측:

- CI 워크플로에서 `bash`로 무언가를 실행하는 줄은 **21개**인데(V2 재측정, `69c1849` 기준), 그중 어떤 검사기든 배선을 지키는 것은 **8개**(`run: bash verify.sh`, `run: bash scripts/acceptance-principles-check.sh`)다. 나머지 **13개**는 `run: echo bash ...`로 바꿔도 아무 검사기가 말을 하지 않는다.
- `hooks/pre-push`는 `echo` 대체를 막는 방어가 있지만 **대상이 2개뿐**(`acceptance-0-5`, `acceptance-0-7`)이고,
  그 훅 자신이 주석으로 한계를 자백하고 있다(`hooks/pre-push:87-90`):
  *"뚫린 것: `if: ${{ false }}`·임의 항상-거짓 조건·파이프 변형. 근본은 실행 증명이며 후속 이슈로 남긴다."*

즉 ChatGPT가 제안한 "10종 뮤테이션 목록"을 그대로 추가하는 것은 **이미 실패가 기록된 길**이다.
훅 주석이 말하듯 문자열 패턴을 하나 늘릴 때마다 우회도 하나씩 는다. 그래서 방향은 채택하되 방법은 바꾼다 —
**목록을 늘리지 말고 실행 영수증을 센다.**

버린 길: ChatGPT의 10종 뮤테이션 목록 전량 구현. 이유는 위 훅 주석의 실측(4종 막았더니 3종이 새로 뚫림).

## 채택 판정표

| # | ChatGPT 지적 | 판정 | 근거 |
|---|---|---|---|
| 1 | 구현자/판정자/병합게이트 분리, 보호 경로 쓰기 금지 | **부분 채택 · 형태 변경** | branch protection·rulesets 403(실측). 같은 UID라 로컬 쓰기 금지도 강제 불가 — `guard-global-skill-files.sh:9-12`가 스스로 자백. 실현 가능한 축소판은 P13①(`weakens-check`)의 CI 배선뿐인데 **현재 배선 0건** |
| 2 | 뮤테이션 철학을 "존재"→"의미"로 | **채택 · 최우선 · 방법 변경** | 24개 중 2개만 보호(실측). 단 11종 목록이 아니라 실행 영수증 대조로 |
| 3 | LLM에게 완료 판정권 없음 + 라벨 5종 | **원칙 채택 · 라벨 기각** | P3 3상태·V-3 라이브 1건과 4/5 중복. 새 정보는 SHA 하나 |
| 4 | 초록은 SHA에 귀속된다 | **전면 채택** | 현재 없음. `acceptance-0-5.sh:84-91`은 `origin/main==main`만 보고 "CI가 검사한 SHA"는 안 본다 |
| 5 | 작업 단위 극소화(1 invariant/1 PR) | **규칙 중복 · 기계 장치는 없음** | harness가 이미 "워크트리 1개 = 인수 기준 1개". 그런데 `b6aee6a`는 8파일 1,450줄 — 규칙이 안 지켜진 증거. P1 자기적용이 필요 |
| 6 | Adversarial TDD | **중복** | `/strict` R2 + Harness 게이트 2와 동일 |
| 7 | guard를 트랜잭션·불변조건으로 | **채택 · 결함 실증됨** | 아래 증거 원문 참조. 복구 실패 후에도 상태 파일을 지워 `recover`가 영구 불가능해진다 |
| 8 | 문서를 검사 결과에서 생성 | **부분 채택 · 축소** | 생성기 1벌 추가는 유지비가 붙는다. 더 싼 해법은 산문에서 숫자를 빼는 것 |

## 결정 카드

### R1. 초록불을 커밋에 묶는다 (ChatGPT #4)

> **무엇을** — `scripts/acceptance-ci-sha.sh` 신설. `gh api`로 PR HEAD의 SHA와 성공한 검사 실행(check run)의 `head_sha`를 대조하고, 다르면 `UNVERIFIED`로 실패시킨다.
> **왜** — 지금은 "PR이 초록"이라는 문장이 어느 커밋 얘기인지 아무도 안 본다. 옛 커밋의 초록을 새 커밋의 합격증으로 쓰는 오판이 실제로 있었다.
> **버린 길** — GitHub required check(branch protection)로 강제. 403이라 불가(요금제 결정 전까지).
> **대가** — 이 스크립트도 구현자가 고칠 수 있다. 완전한 해결이 아니라 **오판 방지**다. 그리고 `gh` 인증이 없는 환경에서는 `NOT_RUN`이 되므로 그 자체를 실패로 처리해야 한다.
> **되돌리기** — 파일 1개 삭제 + 명부 항목 1줄 제거. 5분.

### R2. 검사 목록을 늘리지 않고 실행 영수증을 센다 (ChatGPT #2)

> **무엇을** — 각 `acceptance-*.sh`가 성공 시 `$VH_RECEIPT_DIR/<파일명>`을 쓰고, CI 마지막 스텝이 "글로브로 찾은 스크립트 수 == 영수증 수"를 대조해 다르면 실패시킨다.
> **왜** — `echo bash X`·`if: ${{ false }}`·`cat X | bash`·스텝 삭제가 **전부 같은 증상(영수증 없음)** 으로 잡힌다. 문자열 패턴을 하나씩 늘리는 군비경쟁을 끝낸다. P20("0건 처리로 통과 금지")을 CI 스텝 자체에 적용하는 것이다.
> **버린 길** — ChatGPT의 10종 뮤테이션 목록 전량 구현. `hooks/pre-push:87-90`이 이 길에서 이미 실패한 기록을 남겼다.
> **대가** — 영수증 쓰기 코드를 24개 스크립트에 넣어야 한다(또는 공통 래퍼 1벌). 그리고 이 방식은 **"스크립트 내용을 `exit 0`으로 비운" 공격은 못 잡는다** — 그건 R3처럼 스크립트별 뮤테이션이 따로 필요하다. 두 공격은 다른 장치가 필요하며 하나로 합쳐지지 않는다.
> **되돌리기** — 래퍼 1벌 + CI 스텝 1개 제거. 영수증 디렉터리는 CI 안에서만 살아 있어 잔재가 없다.

### R3. 복구가 끝나기 전에는 상태를 지우지 않는다 (ChatGPT #7)

> **무엇을** — `scripts/guard-global-skill-files.sh`의 `rollback_lock`이 `restore_from_state` 실패 시 상태 파일을 **남기고** `RECOVERY_REQUIRED`로 종료하게 고친다.
> **왜** — 지금은 복구가 실패해도 상태 파일을 지운다. 그러면 원래 권한 기록이 사라져 `recover`가 "복구할 lock 상태 없음"만 뱉고 파일이 444에 영구히 갇힌다. 아래 실증 참조.
> **버린 길** — "chmod가 실패할 일이 없다"고 두는 것. 실패 주입으로 실제 재현됐으므로 성립하지 않는다.
> **대가** — 상태 파일이 남으면 다음 `lock`이 "이미 lock 상태"로 거부된다. 사람이 `recover`를 한 번 돌려야 하는데, 그게 정확히 의도된 동작이다(조용히 넘어가지 않음).
> **되돌리기** — `rm -f` 한 줄 위치 변경. 1분.

### R4. 라벨 5종 → 기각, 산문 숫자 → 삭제 (ChatGPT #3·#8)

> **무엇을** — 상태 라벨 체계는 도입하지 않는다. 문서 생성기도 만들지 않는다. 대신 `docs/engineering/*`의 집계 숫자("완전 6/부분 12/없음 5")를 산문에서 지우고 검사 출력을 그대로 붙인다.
> **왜** — 라벨 5종 중 4종이 P3·V-3와 중복이고, 유일하게 새로운 정보(SHA)는 R1이 값 하나로 처리한다. 생성기는 새 파일 1벌 + CI 스텝 1개의 영구 유지비인데, 막으려는 사고(숫자 드리프트)는 숫자를 안 쓰면 0이 된다.
> **버린 길** — `render_status.py` + `git diff --exit-code` 방식(ChatGPT #8 원안). 유지비 대비 효과가 낮다.
> **대가** — 사람이 문서를 읽을 때 요약 숫자가 없어 검사 출력을 봐야 한다.
> **되돌리기** — 해당 없음(삭제 작업).

## 인수 기준 초안 (EARS)

- **AC-CI-SHA**: `When PR의 HEAD SHA와 성공한 검사 실행의 head_sha가 다르면, 시스템은 UNVERIFIED로 실패해야 한다.`
  검증 명령: `bash scripts/acceptance-ci-sha.sh` — 기대 exit 0(일치) / exit 1(불일치).
  counter-AC: `gh` 인증 실패·네트워크 차단을 exit 0으로 처리하면 가짜(= NOT_RUN을 통과로 셈).
- **AC-RECEIPT**: `When CI에서 실행돼야 할 acceptance 스크립트 수와 영수증 수가 다르면, 시스템은 실패해야 한다.`
  검증 명령: 워크플로 최종 스텝. counter-AC: 영수증을 스크립트가 아니라 워크플로가 대신 써주면 가짜.
- **AC-GUARD-TX**: `If lock 롤백 중 복구가 실패하면, 시스템은 복구 상태 파일을 삭제해서는 안 되며 RECOVERY_REQUIRED로 종료해야 한다.`
  검증 명령: 아래 고장 주입 재현 스크립트 — 기대 "상태 파일 존재" + `recover` exit 0.
  counter-AC: 정상 경로만 시험하고 통과라 하면 가짜(현재 결함이 정확히 그렇게 통과 중).

## 비범위

- ChatGPT #1·#9·#10의 완전 구현(구현자에게서 병합권 회수)은 GitHub 요금제 결정 전까지 범위 밖.
- ChatGPT #5(작업 단위)의 기계 장치는 이번 판 범위 밖 — 규칙은 이미 있고, 강제 장치 설계는 별도 AC.
- 31개 원칙 전체 구현 착수는 여전히 보류(ChatGPT 결론과 동의).

---

## 증거 원문 (3층)

### E1. 원칙 정본 직접 로드 + 검사 실행

```
2026-08-20 15:57:48 KST / HEAD 7bd3298695c93e0e60bdabd2500840da47c4db05
docs/sot/coding-principles.md      72 줄
docs/sot/principles.yaml          324 줄 / 32 항목 / status 전부 PASS

$ bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
exit=0
```

→ 원칙 정본 2개를 현재 저장소에서 직접 읽었고 검사기가 32항목 전부를 대조해 통과했다는 뜻이다. 좋은 소식이지만
범위가 좁다 — 이 PASS는 "원칙 문구와 Strict 배선이 일치한다"만 말하고, 각 원칙의 제품 장치가 실제로 있다는 뜻이 아니다
(`docs/sot/principles.yaml:2-3`의 자기 한정 주석이 이를 명시).

### E2. CI 24개 실행 줄 중 명부가 지키는 것은 2개

```
CI 의 bash 실행 줄:            21 개 (69c1849) (.github/workflows/verify.yml)
어떤 검사기든 배선을 지키는 대상: 8 개 / 무방비 13 개
  - "run: bash verify.sh"
  - "run: bash scripts/acceptance-principles-check.sh"
hs-a4 가 명부에 있는가:        없음 (docs/sot/verification-commands.md 에만 문서로 언급)
```

→ `docs/sot/mechanism-registry.yaml:8-41`이 명부 전체다. 이 명부에 없는 CI 스텝은 `echo bash ...`로 바꿔도
`check-mechanism-registry.sh`가 침묵한다. ChatGPT의 #2 지적이 사실이라는 뜻이며, 나쁜 소식이다.

### E3. pre-push 훅 스스로의 한계 자백

`hooks/pre-push:87-90` — 이 줄들은 CI 스텝이 무력화됐는지 문자열로 판별하는 정규식 바로 위의 주석이다:

```
# 이것으로 근본 해결은 안 된다. `run: cat s | bash` 류 변형이 남는다.
# 워크플로를 문자열로 파싱하는 접근은 규칙을 하나 추가할 때마다 우회도 하나씩 는다
# (막힌 것: 주석 처리·if: false·본문 삭제·echo 대체 / 뚫린 것: if: ${{ false }}·임의
#  항상-거짓 조건·파이프 변형). 근본은 실행 증명이며 후속 이슈로 남긴다.
```

→ 저장소가 ChatGPT의 지적을 이미 알고 있었고, 해법이 "목록 추가"가 아니라 "실행 증명"이라는 결론까지 내려두었다는 뜻이다.
R2가 그 미룬 숙제를 하는 것이다.

### E4. guard 복구 상태 삭제 결함 — 고장 주입 재현 (2026-08-20 KST)

`chmod`를 PATH shim으로 가로채 ① codex 쪽 파일의 444 적용 실패 ② claude 쪽 파일의 644 복구 실패를 동시에 주입했다.
`mktemp` 격리 + `HOME` 치환 + git 환경변수 unset.

```
--- lock 전 권한 ---
644 .../home/.claude/skills/strict/SKILL.md
644 .../home/.codex/skills/strict/SKILL.md
--- lock 실행(고장 주입) ---
FAIL: lock 권한 적용 실패 — .../home/.codex/skills/strict/SKILL.md
lock exit=1
--- lock 후 권한 ---
444 .../home/.claude/skills/strict/SKILL.md     ← 되돌아가지 않음
644 .../home/.codex/skills/strict/SKILL.md
--- 복구 상태 파일이 남아 있는가 ---
(출력 없음 — 디렉터리가 비어 있다)
--- recover 시도 ---
FAIL: 복구할 lock 상태 없음
recover exit=1
=== 원본 저장소 오염 여부 ===
CLEAN: git status 시작과 동일
```

→ 무엇을 시켰나: 잠금 도중 권한 변경이 실패하는 상황을 인위적으로 만들었다. 무엇이 나왔나: 첫 번째 파일은 444에 갇혔는데
원래 권한 644를 적어둔 상태 파일이 지워져, 복구 전용 명령인 `recover`조차 "복구할 상태가 없다"며 거부한다.
나쁜 소식이다 — 이건 ChatGPT #7의 "Invariant 1: 복구가 100% 성공하기 전까지 recovery state를 삭제할 수 없다"가
가정이 아니라 **지금 살아 있는 결함**임을 뜻한다. 원인 위치는 `scripts/guard-global-skill-files.sh`의 `rollback_lock`으로,
`restore_from_state` 실패를 무시하고 곧바로 `rm -f "$STATE_FILE" "$CHECKED_FILE"`을 실행한다.

사업 영향: 사장님의 `/strict` 지침 파일이 읽기전용으로 잠긴 채 원래 권한 기록이 사라진다. 수동으로 `chmod`를 되돌리면
되지만, 어떤 권한이었는지는 사람이 추측해야 한다. 심각도 **중간**(데이터 손실 없음, 자동 복구 경로 소실).

### E5. GitHub 요금제 — 병합 게이트 강제 불가 (실측, 기억 아님)

```
$ gh api repos/sangmokang/Valuehire_v6 --jq '{private,plan:.owner.type}'
{"plan":"User","private":true,"visibility":"private"}

$ gh api repos/sangmokang/Valuehire_v6/branches/main/protection
403 Upgrade to GitHub Pro or make this repository public to enable this feature.

$ gh api repos/sangmokang/Valuehire_v6/rulesets
403 Upgrade to GitHub Pro or make this repository public to enable this feature.

$ ls .github/CODEOWNERS CODEOWNERS
없음
```

→ 개인 계정 + 비공개 저장소라 "검사가 초록이어야만 병합 가능"을 GitHub이 강제해주지 못한다는 뜻이다.
ChatGPT의 #1·#9·#10은 이 조건에서는 스크립트 흉내로만 가능하고, 그 스크립트를 구현자가 고칠 수 있으므로
원래 막으려던 문제가 그대로 남는다. 사장님 결정 사항 1번의 근거다.

### E6. `weakens-check` 라벨 — 규칙만 있고 배선 0건

```
docs/sot/coding-principles.md:28   P13① 로 명문화
docs/sot/principles.yaml:128       mechanism_expected 에 기록
.sh / .yml 안의 배선:              0 건
```

→ "검사 파일을 고치는 PR은 `weakens-check` 라벨 없이 머지 불가"가 원칙에는 있는데 그것을 확인하는 코드가 없다는 뜻이다.
ChatGPT가 말한 "헌법 개정 취급"은 이 저장소에 이미 이름이 있고 몸이 없는 상태다. P1(기계 장치 없는 원칙은 삭제한다)의
자기 적용 대상이다 — 배선하거나 지우거나 둘 중 하나여야 한다.

### E7. 작업 단위 규칙과 실제의 괴리

```
b6aee6a  8 files changed, 1450 insertions(+), 7 deletions(-)
cf633bb  2 files changed, 281 insertions(+)
7bd3298  1 file changed, 16 insertions(+), 9 deletions(-)
```

→ harness 규칙은 "워크트리 1개 = 인수 기준 1개"인데 `b6aee6a`는 8파일 1,450줄이다.
ChatGPT #5의 지적은 새 규칙이 아니라 **기존 규칙이 안 지켜진다는 관찰**이며, 필요한 것은 규칙 추가가 아니라 기계 장치다.

## 한계 / 확인하지 못한 것 (R3)

- ChatGPT 원문이 인용한 PR #31 HEAD `929247a`·로컬 `26ad98c`·PR #32 문서 드리프트는 **이 세션에서 재현하지 않았다.**
  원문이 근거로 삼은 보고서를 받지 못했고, 현재 HEAD는 `7bd3298`이다. #4 채택 판정은 그 인용이 아니라
  `acceptance-0-5.sh`에 SHA 대조가 없다는 독립 실측(E1~E2 계열)에 근거한다.
- `acceptance-hs-a4.sh`를 실제로 `exit 0`으로 바꿔 CI가 통과하는지는 **원격 CI에서 실행하지 않았다.** 명부 미포함(E2)으로
  로컬 검사기가 침묵한다는 것까지만 확인했다. 원격 CI는 `hooks/pre-push` 글로브가 로컬에서 잡으므로
  `--no-verify` 경로에서만 성립하는 시나리오다 — 이 차이는 R2 설계 시 반영해야 한다.
- 뮤테이션 하네스는 4벌 존재(`*-mutations.sh`)하나 각각이 어떤 공격을 실제로 재현하는지 전수 확인하지 않았다.

---

# V2 (Claude 재공격) — codex(V1) 판정 재현 결과

V1 판정 원문: `docs/engineering/chatgpt-verify-feedback-v1-verdict-2026-08-20.md`
(job `task-mt16e1qt-lqogel`, thread `01a01dfc-bd18-7fa2-b2b3-6b7908d7db9a`, **VERDICT: FAIL**)
검증 중 전역 지침 파일 2개 잠금 상태: 시작·종료 모두 해시·권한 동일(`guard ... check` PASS).

## V1이 잡은 G(내) 과장·오류 10건 / V2가 잡은 V1 과장 1건

| # | V1 지적 | V2 재현 | 판정 |
|---|---|---|---|
| 1 | HEAD가 `7bd3298`이 아니라 `69c1849` | `git rev-parse HEAD` → `69c18499f4a5…` (PR #16 병합) | **V1 정당 — 내 오류** |
| 2 | CI "24개 중 2개"는 자의적 집계 | `69c1849` 기준 21개, 보호 8 / 무방비 13. 24는 미커밋 작업트리 값 | **V1 정당 — 내 과장 약 1.7배** |
| 3 | 명부 밖도 다른 검사기가 지킴 | `hs-a4:334`(scan-data-exposure) · `antiforge:107`(G2 3종) · `ac-m:314`(자기) · `pre-push:98`(DEFERRED 2종) 실재 확인 | **V1 정당** |
| 4 | 원문 공격 예시는 11종이 아니라 10종 | 원문 직접 계수 = 10 | **V1 정당** |
| 5 | `hooks/pre-push:95-101` 인용 오류(실제 87~) | 87~90이 한계 주석, 95~96은 정규식 설명 | **V1 정당** |
| 6 | `acceptance-0-5.sh:76-83` 인용 오류(실제 84~) | 84행이 `# 5. 배송 — origin/main…` | **V1 정당** |
| 7 | guard 결함에 동시 실행 경합 누락 | **재현 성공 — 더 심각.** `lock` 도중 `recover`가 끼어들면 `lock`이 **PASS exit=0**을 내면서 두 파일 444 + 상태 삭제 + 이후 `recover` 불가 | **V1 정당 · 심각도 중간→높음 상향** |
| 8 | 라벨 "4/5 중복"은 오판 — 결과값 축과 단계 축이 다름 | 저장소에 로컬/CI 성공을 기계적으로 분리 저장하는 곳 없음(`verify.yml:4`는 주석뿐) | **V1 정당 — 아래 수정판 참조** |
| 9 | R2(영수증 수 대조)는 정상 실행도 실패시킴 | 글로브 24개 중 CI 미등록 4개(`acceptance-0-2` 의도적 + 신규 3개), 조건부 1개 | **V1 정당 — R2 원안 폐기** |
| 10 | R1은 요금제 때문에 불가능한 게 아님 | `gh api …/check-runs` → `{"conclusion":"success","head_sha":"69c1849…","name":"verify"}` **현재 인증으로 동작** | **V1 정당 — R1 즉시 구현 가능** |
| 11 | `b6aee6a`를 규칙 위반 증거로 쓴 것은 P11 위배 | 실제 내용은 goal 1,003줄 + SOT 계약 + 모듈 + 테스트 = **인수 기준 1개**. 크기로 위반을 추론한 것은 부당 | **V1 정당 — 근거 철회** |
| V2-a | V1: "판정문의 `acceptance-principles-check.sh` PASS가 이 환경에서 재현 안 됨 → 재현 증거 아님" | V1 환경에서 `mktemp: Operation not permitted`로 exit=2. 구현자 환경에서는 exit=0 PASS 재현됨 | **V1 과장** — 이는 검증자 샌드박스 제약이므로 `FAIL`이 아니라 `BLOCKED`다(`/strict` §3 환경 차이 절차). 단 **새 사실 1건**: 이 검사는 `mktemp`가 막힌 검증자 환경에서 독립 재현이 불가능하다 |

## 수정된 권고

- **R1(초록불의 커밋 귀속) — 승격, 즉시 착수 가능.** 요금제 제약 없음이 실측으로 확인됐다. 단 V1 지적대로 계약을 채워야 한다:
  워크플로에 `checks: read` 추가, 판정 주체는 **실행이 끝난 뒤의 별도 주체**(같은 실행 안에서 자기 성공을 조회할 수 없다),
  신뢰할 워크플로·잡 이름을 고정.
- **R2(실행 영수증) — 원안 폐기, 재설계 필요.** 단순 개수 대조는 정상 요청을 막고 삭제·선기입·0건 위조를 통과시킨다.
  성립하려면 `스크립트 경로 + 내용 해시 + 커밋 + 실행 번호`를 묶은 증거여야 하고, 기대 목록이 **변경 주체가 못 고치는 정본**이어야 한다.
  현재 개인 저장소 권한 구조에서는 완전 강제가 어렵다 — 착수 순서를 1순위에서 내린다.
- **R3(복구 상태 보존) — 승격, 1순위.** 가장 싸고(한 줄~), 유일하게 **재현된 실동작 결함**이며, 동시 실행 경합까지 포함하면
  `lock/check/unlock/recover` 전체를 하나의 소유권 잠금으로 직렬화해야 한다.
- **R4(라벨) — 부분 철회.** 5개 라벨을 그대로 쓰지는 않되, **로컬 성공 / CI 성공(커밋 값 포함) / 라이브 증거**는
  서로 대체 불가한 별개 필드로 남긴다. "1개(SHA)로 충분하다"는 원 판정은 철회한다.
- **철회**: `b6aee6a`를 작업 단위 규칙 위반 증거로 삼은 서술(P11 위배).
- **추가 채택**: ChatGPT의 "검증 코드 변경 = 헌법 개정"을 권고로 승격한다 — `weakens-check`가 규칙만 있고 배선 0건이므로
  배선하거나 P1에 따라 삭제하거나 둘 중 하나여야 한다.

## V2 시점의 미확인 (한계)

- 무방비 13개 각각에 대해 `echo` 치환 실증을 개별 수행하지 않았다(정적 배선 검사 부재로만 판정).
- R2 재설계안(해시+커밋+실행번호)은 설계만이며 구현·시험하지 않았다.
- 동시 실행 경합은 `chmod` 가로채기로 **순서를 결정론적으로 고정**해 재현했다. 각 동작(`lock`·`recover`)은 실제 지원 명령이며
  동작을 위조하지 않았으나, 실제 두 프로세스의 자연 발생 경합 확률은 측정하지 않았다.
- V1이 지적한 "10가지 법칙 중 3·4(모든 안전장치에 변이, 하나라도 생존하면 체계 FAIL)"의 채택 여부는 이번 판에서 결론 내지 않았다.
