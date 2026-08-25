# 히스토리 비밀 스캔을 fail-closed 로 되돌린다 — goal (2026-08-21)

**모드** `code-change` · **등급 L3**
등급 근거: 보안 검사(비밀 유출 탐지) 본문 변경 + CI 워크플로 변경 + 로컬/서버 양쪽 판정 경로에 걸침.

**실행 주체**: Codex (G). 판정은 Claude(V1) → Codex(V2) 순서로 교차한다.
**merge 는 사장님 몫이다. 이 작업은 READY TO MERGE 까지만 간다.**

---

## 1층 결론

지금 main 의 비밀 스캔은 **비밀을 찾고도 통과합니다.** 큰 파일에서 재현했습니다.

고칠 코드는 **이미 PR #29 에 있습니다.** 다만 그 PR 이 4일 동안 열려 있는 사이 main 이 10커밋 앞서가 충돌 상태가 됐습니다. 그래서 "그대로 병합"이 아니라 "현재 main 위에 다시 얹기"가 필요합니다.

이 작업에서 결정할 것은 하나입니다 — **인라인 코드를 파일로 빼낼 것인가.** 빼면 충돌이 거의 사라지고, 우리 원칙 P16(판정기는 한 벌)도 같이 지켜집니다. 빼지 않으면 지금 구조가 유지되고 충돌을 손으로 풉니다.

---

## 2층 판단 근거

### 현재 상태 (실측, 추측 아님)

`.github/workflows/verify.yml:96` — 도달 가능한 모든 blob 을 열어 비밀 패턴과 대조하는 줄

```
            if git cat-file blob "$sha" 2>/dev/null | grep -qEif "$CLEAN"; then
```

`.github/workflows/verify.yml:61` — 같은 스텝 위쪽

```
          set -o pipefail
```

`.github/workflows/verify.yml:94` — 객체 타입을 못 읽으면 조용히 건너뛰는 줄

```
            [ "$(git cat-file -t "$sha" 2>/dev/null)" = blob ] || continue
```

**재현 실측 (2026-08-21)**: 20MB blob 첫 줄에 합성 자격증명을 넣고 돌렸습니다.

| 구현 | 결과 |
|---|---|
| 현재 main (`grep -q` + `pipefail`) | `rc=141` — **미탐지, False Green** |
| 외부 리뷰가 제시한 수정안 (`grep -Eif ... >/dev/null`) | BSD grep 에서는 정상, **ugrep 에서는 여전히 rc=141** |
| 파이프 자체를 제거 (임시 파일 경유) | 정상 탐지 + 정규식 오류를 rc=2 로 분리 |

→ `rc=141` 은 SIGPIPE 입니다. `grep -q` 가 매치를 찾자마자 종료해 `git cat-file` 이 파이프가 끊긴 채 죽고, `pipefail` 이 그 실패를 파이프라인 전체 실패로 만들어 `if` 조건이 거짓이 됩니다. **비밀을 찾은 것이 못 찾은 것으로 뒤집힙니다.**

→ 외부 수정안을 그대로 붙이면 grep 구현에 따라 안 고쳐집니다. **파이프를 없애는 것만이 구현 무관하게 안전합니다.**

### 근본 원인

세 가지가 겹쳤습니다.

1. **파이프 종료값 소실** — `set -o pipefail` 아래에서 소비자(grep)의 조기 종료가 생산자(git)를 죽이고, 그 죽음이 판정을 뒤집는다.
2. **검사기 오류와 "매치 없음"을 구분하지 않음** — `grep` 종료값 0(위반)·1(정상)·2 이상(정규식 오류)이 전부 `if` 의 참/거짓으로만 뭉개진다. `git cat-file` 실패도 마찬가지.
3. **판정기가 두 벌** — CI 는 워크플로 안 인라인 코드를 실행하고, 인수 검사 `acceptance-0-2-unreachable-content.sh` 는 자기 안의 별도 로직을 검사한다. 인수 검사가 완벽해도 CI 인라인은 별개다(P16 위반).

### 과거 회수 (R4 — 같은 지적 2회째)

- `task/gate0-reachable-large-blob-sigpipe` (PR #29, 커밋 6개, 2026-08-18) — 같은 결함을 이미 고쳐 놓았습니다. verify 초록, 원격 HEAD `996e097`. **미병합 상태로 4일 경과.**
- 그 PR 의 goal: `docs/engineering/...-goal-2026-08-18.md` (760줄) — 이 작업은 그것을 **대체하지 않고 현재 main 위로 옮깁니다.**
- 관련 원칙: **P3**(조용한 실패 금지 · 3상태 판정), **P16**(판정기 한 벌), **P20**(0건 처리로 통과를 스스로 의심), **P13⑥**(무력화 저항).

### 이번 작업의 제약 — 반드시 읽을 것

- **`docs/sot/30-strict-mode-contract.md` 와 `docs/sot/31-strict-recurrence-ledger.md` 는 이 저장소에 없습니다.** 전역 strict 스킬이 그 두 파일을 정본·재발 원장으로 지목하지만 실재하지 않습니다(2026-08-21 실측: `docs/sot/` 에는 coding-principles.md, principles.yaml, mechanism-registry.yaml, verification-commands.md, git-workflow.md, hook-contracts.md, humansearch-* 만 존재). **없는 문서를 읽었다고 하지 마십시오.** 이 저장소의 실제 원칙 정본은 `docs/sot/coding-principles.md` 이고 기계 장부는 `docs/sot/principles.yaml` 입니다.
- **인수 검사는 실행 래퍼를 거칩니다.** CI·pre-push 모두 `bash scripts/verify/run-acceptance.sh <검사>` 형태입니다. 새 검사를 추가하면 이 형태로 배선해야 하고, `docs/sot/mechanism-registry.yaml` 에도 등록해야 합니다.
- **워크플로 스텝에 조건·오류무시를 붙이면 `scripts/verify/check-ci-step-integrity.sh` 가 차단합니다.**
- **pre-commit 이 약화 패턴을 diff 에서 탐지합니다.** mutation 을 주입하는 테스트 코드가 `|| true`, `continue-on-error: true` 같은 문자열을 그대로 담으면 커밋이 차단됩니다. 저장소 선례대로 **문자열을 조립해서** 쓰십시오(`.check-weakening-patterns` 주석 참조).

---

## 결정 카드 — 인라인을 파일로 뺄 것인가

> **무엇을** — 워크플로 안 히스토리 스캔 본문을 `scripts/scan-history-secrets.sh` 로 추출하고, CI 와 인수 검사가 **같은 파일**을 실행한다.
> **왜** — ① 판정기가 한 벌이 되어 P16 을 지킨다 ② 인수 검사가 CI 가 실제로 돌리는 그 코드를 검사하게 된다 ③ verify.yml 변경이 한 줄로 줄어 PR #29 충돌이 사실상 사라진다.
> **버린 길** — 인라인을 유지한 채 손으로 충돌을 푸는 방법. 지금 한 번은 되지만 판정기가 계속 두 벌이라 다음 변경에서 또 갈라진다.
> **대가** — 파일 하나가 늘고, 명부(mechanism-registry)와 배선을 함께 고쳐야 한다. PR #29 원본과 diff 가 달라져 그 PR 은 닫고 이 브랜치로 대체해야 한다.
> **되돌리기** — 추출 커밋 하나만 `git revert` 하면 인라인으로 돌아간다. 스크립트 파일은 남지만 아무도 부르지 않는다.

**사장님 결정 사항**: 추출한다 / 인라인 유지한다. 이 goal 은 **추출을 전제로** 작성했습니다. 인라인 유지를 택하시면 AC-3 을 빼고 AC-1·AC-2 만 수행합니다.

---

## 인수 기준

### AC-1 — 비밀을 찾으면 반드시 실패한다

**When** 도달 가능한 blob 안에 자격증명 패턴과 일치하는 내용이 있으면, 스캐너는 종료값 1 로 실패하고 그 blob 의 SHA 와 과거 경로를 출력해야 한다.
**While** blob 이 커서 소비자가 먼저 끝나는 상황에서도, 스캐너는 그 매치를 놓치지 않아야 한다.

- 검증 명령: `bash scripts/verify/run-acceptance.sh scripts/acceptance-history-scan-failclosed.sh`
- 기대: `VERDICT: PASS` 와 `CHECKED: N` (N ≥ 8)
- counter-AC:
  - 20MB 이상 blob 첫 줄에 합성 자격증명을 넣었을 때 통과하면 **실패**
  - 파이프를 다시 도입해 `rc=141` 이 나오는데 통과하면 **실패**
  - 매치를 찾고도 종료값이 0 이면 **실패**

### AC-2 — 검사기 오류를 "매치 없음"으로 세지 않는다

**If** 패턴 검사기가 종료값 2 이상(정규식 오류 등)을 내면, 스캐너는 종료값 2 로 실패해야 한다.
**If** `git cat-file` 이 객체를 읽지 못하면, 스캐너는 그 객체를 건너뛰지 않고 종료값 2 로 실패해야 한다.

- 검증 명령: 위와 동일
- 기대: 같은 인수 검사 안에서 오류 주입 케이스가 `PASS` 로 보고됨
- counter-AC:
  - 깨진 정규식(`AKIA[0-9A-Z{16}`)을 패턴 파일에 넣었을 때 스캐너가 통과하면 **실패**
  - 존재하지 않는 객체 SHA 를 목록에 넣었을 때 `continue` 로 건너뛰고 통과하면 **실패**
  - 유효 패턴이 0개인 패턴 파일에서 통과하면 **실패**

### AC-3 — 판정기는 한 벌이다 (추출을 택한 경우만)

**Where** CI 와 인수 검사가 히스토리 비밀 스캔을 수행할 때, 시스템은 **동일한 파일** `scripts/scan-history-secrets.sh` 를 실행해야 한다.

- 검증 명령: `bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh`
- 기대: `CHECKED: 33` 정확히, 명부 항목 수 = 검사기 보고 수
- counter-AC:
  - 워크플로에 스캔 본문이 인라인으로 다시 남아 있으면 **실패**
  - 명부(`docs/sot/mechanism-registry.yaml`)에 스캐너가 등록되지 않았으면 **실패**
  - 인수 검사가 CI 와 다른 코드를 검사하면 **실패**

---

## 종료값 계약 (2026-08-22 정정)

`scripts/scan-history-secrets.sh` 의 종료값은 **0 = 정상(위반 0건) · 1 = 위반 발견 · 2 = 검사기 오류 또는 스캔 무효** 다.

초안 WU-1 설명에 `0=위반` 으로 적었으나 AC-1·AC-2 의 문구, 그리고 현재 워크플로 인라인 관례(`exit $hit`, 무효는 `exit 2`)와 어긋났다. 일반 관례로 통일했고 인수 검사도 이 값으로 고정돼 있다.

이 방향을 택한 이유: CI 가 `bash scripts/scan-history-secrets.sh` **한 줄로** 부를 수 있어야 한다. 호출부에서 종료값을 뒤집는 군더더기가 붙으면 그 줄 자체가 새로운 약화 지점이 된다.

## 작업 분해표 (R1)

| WU | 작업 | AC | 검증 1개 |
|---|---|---|---|
| WU-1 | 히스토리 스캔 본문을 `scripts/scan-history-secrets.sh` 로 추출하고 파이프 제거 + 종료값 3분기(**0 정상 / 1 위반 / 2 검사기오류·스캔무효**) | AC-1, AC-2 | `bash scripts/scan-history-secrets.sh` 가 현재 저장소에서 종료값 0 |
| WU-2 | 인수 검사 `scripts/acceptance-history-scan-failclosed.sh` 신설 — 합성 저장소로 차단·통과를 한 쌍으로 | AC-1, AC-2 | `VERDICT: PASS`, `CHECKED` ≥ 8 |
| WU-3 | CI·명부 배선 — verify.yml 스텝을 스크립트 호출로 교체, 새 인수 검사를 래퍼 경유로 추가, mechanism-registry 등록 | AC-3 | `acceptance-verify-ac-m.sh` 통과 |
| WU-4 | PR #29 의 `acceptance-0-2*` 개선분(깨끗하게 적용됨) 이식 | AC-1, AC-2 | 해당 인수 검사 통과 |

각 WU 는 **독립 커밋**이다. WU 하나가 실패하면 그 WU 만 되돌린다.

---

## 예외 케이스 표 (R1) — 표에 없는 상황은 임의 판단 금지, 중단 후 표 갱신

| 상황 | 처리 |
|---|---|
| `git rev-list` 가 실패하거나 빈 목록 | **명시적 중단** — 종료값 2, "스캔 무효" (0건 통과 금지 · P20) |
| 도달 가능 객체가 2개 미만 | **명시적 중단** — 종료값 2 |
| blob 을 한 개도 못 읽음 | **명시적 중단** — 종료값 2 |
| 유효 패턴 0개 | **명시적 중단** — 종료값 2 |
| 패턴 파일에 깨진 정규식 | **명시적 중단** — 종료값 2, 어느 패턴인지 출력 |
| `git cat-file -t` 실패 | **명시적 중단** — 종료값 2 (`continue` 금지) |
| `git cat-file blob` 실패 | **명시적 중단** — 종료값 2 |
| 매우 큰 blob (수십 MB) | **자동 처리** — 임시 파일로 받아 전량 검사. 크기로 건너뛰지 않는다 |
| 바이너리 blob | **자동 처리** — `grep -a` 로 텍스트 취급 |
| 임시 파일 생성 실패 | **명시적 중단** — 종료값 2 |
| `GIT_DIR`등이 다른 저장소를 가리킴 | **자동 격리** — 상속 재지정을 제거하고 현재 체크아웃을 스캔 |
| 스캔 시간이 CI 한도를 넘음 | **명시적 중단** — 사장님께 보고 후 `git cat-file --batch` 최적화를 별도 WU 로 |
| pre-commit 이 약화 패턴으로 커밋 차단 | **자동 처리** — 문자열 조립으로 회피하고 그 사실을 커밋 메시지에 남긴다. suppressions 등록 금지 |
| 원본 저장소가 오염됨 | **명시적 중단** — 즉시 복구하고 보고 |
| 그 외 전부 | **명시적 중단** — 사유를 적고 사장님께 보고 |

---

## 게이트 계획

| 게이트 | 통과 조건 |
|---|---|
| 0 시작 자격 | 격리 워크트리 `task/history-scan-failclosed`, 작업트리 깨끗, 이 goal 읽음 |
| 1 스펙 | AC-1~3 + counter-AC 고정 (이 문서) |
| 2 RED | 인수 검사를 먼저 만들어 **현재 main 코드에서 실패**하는 것을 보인다. 실패 이유가 "빠진 동작"이어야 하고 문법 오류면 안 된다 |
| 3 GREEN | 스캐너 수정으로 RED → GREEN. 기존 검사 회귀 0 |
| 3.5 배선 | CI·pre-push·명부에서 실제로 호출되는 경로 증명 |
| 4 검증 | `bash verify.sh`, 관련 인수 검사 전량, 숫자 그대로 기록 |
| 5 배송 | PR 생성, 원격 CI 초록 확인. **merge 는 사장님** |
| 6 종료 | PR #29 를 닫고 이 브랜치가 대체한다는 사유를 그 PR 에 남긴다 |

---

## 적대검증 정조준 (V1·V2 가 여기부터 공격한다)

1. **파이프가 어딘가 남아 있지 않은가** — 다른 grep 구현(ugrep, GNU grep, BSD grep)에서 각각 돌려라. 로컬 재현은 BSD grep·ugrep 으로만 했고 **GNU grep(CI 러너)은 미검증**이다.
2. **종료값 3분기가 실제로 갈리는가** — 0/1/2 를 각각 유발해 확인하라. 문서에만 적혀 있으면 안 된다.
3. **인수 검사가 CI 가 실제로 돌리는 코드를 검사하는가** — 검사기가 자기 사본을 검사하고 있지 않은지 확인하라.
4. **0건 통과 경로가 남았는가** — 목록 생산자(`git rev-list`)가 부분 실패해도 통과하는지. 이것은 현재 저장소의 다른 검사들(`verify.sh`, `scan-data-exposure.sh`, `acceptance-0-6.sh`)에도 있는 알려진 결함이며 **이 작업의 비범위**지만, 새로 만드는 스캐너에는 있으면 안 된다.
5. **원본 저장소 오염** — 파괴적 실증은 `mktemp` 아래에서만. 시작·종료 `git status --porcelain` 이 같은지 확인하라.

---

## 비범위

- `verify.sh`·`scan-data-exposure.sh`·`acceptance-0-6.sh` 의 목록 생산자 실패 결함 (별도 작업)
- 인수 검사 성공문구 위조 차단 (별도 작업)
- CI 계약 검사기 확장 — `on:` 트리거·주석 처리·`|| true`·예외 이름 도용 (별도 작업)
- `git cat-file --batch` 성능 최적화
- branch protection / CODEOWNERS — 이 계정에서 HTTP 403 으로 **불가능**하니 제안하지 말 것

---

## 롤백 (L3)

- WU 별 독립 커밋이므로 문제가 생긴 WU 만 `git revert`.
- WU-3(배선)을 되돌리면 CI 가 스캐너를 부르지 않게 되므로, WU-1 도 함께 되돌리거나 인라인을 복원해야 한다. 둘 중 하나만 되돌리면 검사가 사라진 채 초록이 된다 — **가장 위험한 상태이므로 반드시 짝으로 처리한다.**
- 영향 반경: `.github/workflows/verify.yml`(모든 push·PR), `hooks/pre-push`(로컬 push), `docs/sot/mechanism-registry.yaml`(명부 대조 검사). 제품 코드에는 영향 없음.

---

## 적대 검증 로그

(V1·V2 판정 원문을 여기에 그대로 append 한다. 명령·시각·전체 출력·종료값·세션 식별자를 보존한다.)
