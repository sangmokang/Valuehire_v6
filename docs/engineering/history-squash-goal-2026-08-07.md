# GOAL — 0-2: 비밀번호 히스토리 청소 (squash) + 스캐너 리터럴 외부화

**작성**: 2026-08-07 · **등급**: L3 (파괴적 git history rewrite + 보안 경로) · **승인**: 사장님 "어 청소기록 해 0-2" (2026-08-07)

## ① 현재 상태 (실측, 추측 아님)

- `git log --all -S'<리터럴>' --oneline | wc -l` = **5** (2f45b7b, ce81445, e951c59, c32d5fd, 4d53eac)
- 리터럴 보유 지점 전수 (grep -rl, .git 제외):
  - `verify.sh:7` — 추적 파일. 하드코딩 + `grep -v '^verify\.sh$'` 자기 면제 (E1 패턴)
  - `docs/engineering/goal-prompts/2026-08-06-merge-verify-gptreview-reimpl.md:82` — 비추적, NOT-IGNORED (2026-08-06 /verify HIGH F1)
- 잔존 ref: `refs/heads/task/gptreview-verify-skills` = 4d53eac (게이트0에서 발견, 어제 회수 누락분)
- 원격: `origin/main` = 9d0ffd9(초기화 커밋)만. 오염 히스토리는 전량 미push → 유출 범위 로컬 국한
- gitleaks 미설치 (`command -v gitleaks` 실패)

## ② 근본 원인

비밀번호가 (a) 커밋 히스토리 5개에, (b) 스캐너 자신에 하드코딩된 채 자기 면제로, (c) 비추적 문서에 평문으로 존재. (b)가 원인의 핵심 — 스캐너가 리터럴을 품고 있는 한 히스토리를 청소해도 다음 커밋에서 재유입된다.

## ③ 인수 기준 (AC) — `scripts/acceptance-0-2.sh` exit 0

- **EARS**: When 0-2 완료 시, then ⑴ `git log --all -S"$(head -1 .secret-patterns)"` 결과가 0건이어야 하고 ⑵ verify.sh는 리터럴 하드코딩·자기 면제 없이 통과해야 하며 ⑶ 리터럴을 심은 파일을 스테이징하면 verify.sh가 exit 1로 잡아야 하고(뮤테이션) ⑷ `docs/` 실파일에 리터럴이 0건이어야 한다.
- **검증 명령**: `bash scripts/acceptance-0-2.sh` (RED 커밋 후 → 완료 시 PASS exit 0)
- **counter-AC (가짜 완료 시나리오, 최소 목록)**:
  - 스캐너에서 리터럴만 지우고 패턴 파일을 안 만들어 스캔이 조용히 무력화(no-op) → ⑶ 뮤테이션 체크가 잡는다
  - refs만 지우고 reflog에 옛 커밋 잔존 → `--all`은 refs 기준이므로 별도로 reflog expire + gc를 절차에 포함
  - acceptance 스크립트가 리터럴을 자기 몸에 품어 재유입 → 스크립트는 `.secret-patterns`에서 런타임에 읽는다(2026-08-06 자기 매칭 사고 재발 방지)

## ④ Harness 게이트 계획

0(완료: 이 문서 ①) → 2: `worktrees/history-squash`에 acceptance RED 커밋 → 3: verify.sh 재설계 + .gitignore에 `.secret-patterns` + docs 새니타이즈 → V1(codex)·V2(Claude 재공격) **파괴 단계 이전에** → 4-실행: 백업 번들 → 병합 → `reset --soft 9d0ffd9` 단일 커밋 → 잔존 브랜치 삭제 → reflog expire + gc → acceptance PASS → 5: **push는 하지 않는다**(0-5 별도) → 정본 문서 0-2 행 실출력 기입.

## ⑤ codex 적대검증 정조준 항목

⑴ 새 verify.sh가 리터럴 0개로도 검출력을 유지하는가(뮤테이션 실증) ⑵ 패턴 파일 부재 시 조용한 no-op이 아니라 시끄러운 실패인가 ⑶ acceptance가 자기 몸에 리터럴을 품지 않는가 ⑷ squash 절차가 놓치는 ref/reflog 경로가 없는가.

## ⑥ SOT 체크리스트

- `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §5 Phase 0 표 0-2 행 — 완료 시 실출력으로 갱신(이 변경의 SOT diff에 해당. docs는 비추적이라 PR 동봉 불가 — 파일 직접 갱신으로 갈음)
- `docs/sot/` 디렉터리는 현재 없음(확인함)

## ⑦ 비범위

- ❌ 원격 push (0-5 별도 — 완료 후 push가 "가능"해질 뿐, 실행은 별도 승인)
- ❌ gitleaks 도입(미설치, brew 필요) — 후속 이슈. 이번엔 `grep -f .secret-patterns`로 동등 목적 달성
- ❌ CI 연결(0-5 이후), Makefile 정비, `.gitignore`의 기존 미커밋 5줄 훅(2026-08-06 /verify 보류 판정분 — 별도 처리)

## ⑧ 롤백 절차 (L3)

파괴 단계 직전 `git bundle create ~/Desktop/Valuehire_v6-pre-squash-20260807.bundle --all` 생성. 복구:
```bash
cd ~/Desktop && git clone Valuehire_v6-pre-squash-20260807.bundle Valuehire_v6_restored
```
⚠️ 이 번들은 비밀번호 히스토리를 포함한다 — 로컬 보관 전용, 절대 업로드 금지. 0-5(push) 완료 후 사장님 승인 하에 파기.

## ⑨ 영향 반경 (L3)

로컬 저장소 히스토리 전량 재작성. 원격은 무변경(미push 상태라 협업자 영향 0). 깨질 수 있는 것: 옛 SHA를 참조하는 문서들(docs/engineering/* 의 2f45b7b·6e52c77 등 SHA 언급) — 역사 기록으로 유지하되 정본 문서 0-2 행에 "구 SHA는 squash 전 기준" 명기. 데이터 안전 AC: ③⑷(docs 실파일 리터럴 0건)가 해당.

## ⑩ 계약 스펙 (verify.sh v2)

- **입력**: `git ls-files` 추적 파일 전체 + 패턴 파일(기본 `.secret-patterns`, `SECRET_PATTERNS_FILE` 환경변수로 대체 가능 — 향후 CI용). 패턴 파일 형식: 한 줄당 ERE 패턴 1개, gitignore 대상.
- **출력**: 전부 통과 시 `PASS: ...` + exit 0 / 리터럴 검출 또는 .env 추적 시 `FAIL: ...` + exit 1 / **패턴 파일 부재 시 `FAIL: secret patterns file missing` + exit 2** (조용한 스킵 금지)
- **경계값**: 패턴 파일이 빈 파일이면 exit 2 (no-op 방지). 자기 면제 없음 — verify.sh 자신도 스캔 대상(리터럴이 없으므로 통과해야 정상).

## 실행 절차 (V1·V2 판정 반영 최종본)

⚠️ `rm -rf`로 워크트리를 지우지 않는다 — stale admin dir가 `gc --prune=now`를 무력화하는 gc root가 된다(V2-④b 실증).

1. 사전 인벤토리 기록: `git for-each-ref`, `git worktree list --porcelain`, pseudoref 파일 목록, 오염 blob/커밋 SHA (사후 대조 기준선)
2. 백업 번들: `git bundle create ~/Desktop/Valuehire_v6-pre-squash-20260807.bundle --all` (⚠️ 비밀 포함, 업로드 금지)
3. 회수: 판정서 2건(V1·V2) + `.secret-patterns` + 미커밋 `.gitignore` 훅을 main 쪽으로 보존
4. `git merge task/history-squash` (fast-forward)
5. `git worktree remove worktrees/history-squash` → `git worktree prune` → `git worktree list --porcelain`에 prunable 0건 확인
6. 브랜치 삭제: `task/history-squash`, `task/gptreview-verify-skills`
7. `git reset --soft 9d0ffd9` → 단일 커밋 생성
8. 공통 `ORIG_HEAD` 삭제 (per-worktree는 5단계에서 동반 삭제됨을 확인)
9. `git reflog expire --expire=now --expire-unreachable=now --all`
10. `git gc --prune=now`
11. main에서 `bash scripts/acceptance-0-2.sh` → PASS(exit 0) 확인. 실패 시 2번 번들로 복구

## 범위 밖으로 분리된 발견 (V2-⑤, 사장님 보고 사항)

V2 실측: 동일 리터럴이 **다른 저장소(`Valueconnect-Ops`)의 GitHub 원격 브랜치 2개**
(`origin/fix/clickup-candidate-posting-qa477`, `origin/fix/nudge-daily-dedup`)와 로컬 90여 개 파일
(Claude 세션 트랜스크립트·리포트 HTML 등)에 평문 존재. `~/Desktop`의 iCloud 동기화는 배제됨(실측).

→ **goal ①의 "유출 범위 로컬 국한"은 거짓**이다. 0-2가 PASS해도 이 저장소만 깨끗해진다.
비밀번호 회전은 2026-08-04 결정으로 거부됨 — 재요구하지 않고 **사실관계가 그 결정의 전제와 다르다는 점만** 보고한다.
후속 조치는 별도 태스크(0-10 후보)로 분리.

## 적대 검증 로그

### V1 (codex, 2026-08-07) — 대상 `965f084`
판정서 본문: `docs/engineering/history-squash-v1-verdict-2026-08-07.md` (81줄, 워크트리에서 회수)
- ① 스캐너 검출력 PASS / ② fail-closed PASS / ③ acceptance 신호 원복 **FAIL** / ④ 잔존 경로 **FAIL**
- transcript: `~/.claude/projects/-Users-kangsangmo-Desktop-Valuehire-v6/c24114c0-*/subagents/agent-a9c48f2b0fcf95d2e.jsonl` (agentId `a9c48f2b0fcf95d2e`, duration 2188s)

### V2 (Claude 무맥락 재공격, 2026-08-07) — 대상 `2f4bf04`
판정서 본문: `docs/engineering/history-squash-v2-verdict-2026-08-07.md` (301줄)
**VERDICT: NO-GO** — V1의 PASS 2건을 뒤집음(REFUTED):
- ① 파일명 공백/개행/선행하이픈으로 스캐너 우회 exit 0 (`xargs` 분할 + `2>/dev/null||true` 은폐)
- ② 패턴 파일이 디렉터리·읽기불가·CRLF·주석뿐이면 fail-open exit 0 (`-s`는 크기만 검사)
- ③ trap 수정은 **유효 확인**(TERM 143 / INT 130 / HUP 129, 잔존 0)
- ④ V1 목록은 오히려 불완전 — stale worktree admin dir가 gc 무력화, per-worktree ORIG_HEAD 사각지대, `fsck --no-reflogs` 누락(실측 3 vs 보고 0), 검사 대상이 blob이 아니라 커밋 SHA뿐
- ⑤ 상관 블라인드스팟(치명): 위 "범위 밖으로 분리된 발견" 참조
- transcript: `agent-a96f7cce727eb62ff.jsonl` (agentId `a96f7cce727eb62ff`, 34 tool_uses, 1117s)

### G 대응 (2026-08-07, 커밋 `434039a`)
V2 NO-GO 4건 전부 보완 후 V2의 공격을 격리 저장소·합성 토큰(`SYNTHSECRET42`)으로 재현한 실측:

| 공격 | 보완 전 | 보완 후 (434039a) |
|------|---------|-------------------|
| A2 공백 파일명 | exit 0 (우회 성공) | **exit 1 검출** |
| A3 개행 파일명 | exit 0 | **exit 1 검출** |
| A4 선행 하이픈 | exit 0 | **exit 1 검출** |
| B1 패턴=디렉터리 | exit 0 | **exit 2** |
| B6 퍼미션 000 | exit 0 | **exit 2** |
| B8 CRLF 패턴 | exit 0 | **exit 1 검출**(정규화) |
| B5 주석뿐 | exit 0 | **exit 2** |
| TERM 원복 | (V1 FAIL) | **exit 143, 잔존 0건 유지** |

acceptance는 현재 예상대로 RED(23건 FAIL) — squash 미실행 상태이므로 정상.

### V2 2차 재판정 (2026-08-07) — 대상 `434039a` · **VERDICT: NO-GO**

①②④ 보완은 **CLOSED**(재현 실패 = 방어 유효) 확인. 그러나 **더 치명적인 신규 결함**을 발견:

> `check3`(뮤테이션)이 실제 리터럴을 `git add`하면서 **blob을 이 저장소 object DB에 영구 기록**한다.
> ⑴ 절차 10(`gc --prune=now`) 다음의 절차 11(acceptance 실행)이 방금 지운 평문을 **다시 써 넣어**
> 0-2의 목적 명제 자체를 파괴한다. ⑵ 그 unreachable blob을 `check5`의 `fsck --no-reflogs --unreachable`이
> 자기 자신의 잔존으로 세어 **어떤 상태에서도 exit 0이 불가능**하다(완벽한 종료상태 모사에서 run1~3 모두 exit 1,
> check3만 제거하면 동일 저장소가 exit 0 — 실측). 그 결과 파괴적 squash 직후 무조건 롤백 조건이 발동한다.

→ 검증 도구가 스스로 오염원이 되는 구조. **이 상태로 squash했으면 "청소 완료 후 재오염"이 됐다.**

### G 대응 2차 (2026-08-07, 커밋 `236f657`)

뮤테이션 검증을 `mktemp -d` 격리 저장소 + 합성 카나리(`ACCEPTANCE-MUTATION-CANARY-42`)로 이전.
실제 리터럴은 디스크·object DB 어디에도 쓰지 않는다. 실제 `.secret-patterns`에는 "유효 패턴 ≥1" 검사만 남김.

| 실측 항목 | 결과 |
|-----------|------|
| acceptance 실행 전후 `git count-objects -v` | **count 84 → 84 (증가 0)** |
| 실행 후 `git status --short` | 인덱스 오염 **0건** |
| squash 종료상태 모사 저장소에서 acceptance | **exit 0 PASS** — GREEN 도달 가능성 증명 |
| 신호 원복 | TERM=143 / HUP=129 / 잔존 0건 (INT=1은 zsh가 백그라운드 잡에 SIGINT를 SIG_IGN으로 물려주는 셸 아티팩트 — V2 1차 관찰과 동일) |

**교훈(P 원칙 후보)**: 검증 스크립트가 검증 대상 상태를 변경하면 그 자체가 오염원이다.
파괴적 정리 작업의 인수 스크립트는 **읽기 전용이거나 격리 샌드박스에서만** 부작용을 낸다.

### V2 3차 재판정 (2026-08-07) — 대상 `236f657` · **VERDICT: GO**

2차 NO-GO 2건 모두 실측 해소 확인:
- 실저장소 스냅샷 전후 **IDENTICAL** (객체 88→88, refs·reflog·index·pseudoref 전부 무변화)
- 무결점 종료 상태에서 **exit 0 PASS 3회 멱등**
- 12개 개별 위반 주입 시 **전부 exit 1** (위양성 없음)
- TMPDIR·CDPATH·OLDPWD·PWD·mktemp 실패·서브셸 중 TERM/KILL·excludesFile 탈출 전부 fail-closed
- 절차 순서(gc → acceptance) 안전 확인

잔여 지적 2건(이번 실행 비차단):
1. `GIT_DIR`/`GIT_INDEX_FILE`/`GIT_OBJECT_DIRECTORY`가 환경에 있으면 sandbox가 실저장소로 샘 →
   **커밋 `71b1186`에서 스크립트 상단 `unset`으로 선제 차단함**(V2 권고보다 앞당겨 조치)
2. AC는 `.secret-patterns`가 실제 비밀과 일치함을 보증하지 않고 ERE 메타문자에서 check1·4가 눈이 멂 →
   이번 실행분은 "실패턴 → 실리터럴 매치 YES, 메타문자 0개" 직접 확인됨. 후속 이슈로 분리

---

## 실행 결과 (2026-08-07, 파괴 단계 완료)

**최종 히스토리**: `8e80a64` (부모 = `9d0ffd9` 초기화 커밋 단독) — 오염 커밋 5개가 있던 체인 폐기.

| 검증 | 실제 출력 |
|------|-----------|
| `bash scripts/acceptance-0-2.sh` | `PASS: 0-2 완료 — 히스토리·객체·refs·pseudoref·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인` **exit 0** |
| 오염 blob 6개 `cat-file -e` | 전부 **GONE** |
| 오염 커밋 6개 `cat-file -e` | 전부 **GONE** |
| `git log --all -S"$LIT"` | **0건** |
| object DB blob 전수 스캔 | **0건** |
| `fsck --full --no-reflogs --unreachable` | **0** |
| `bash scripts/acceptance-0-6.sh` (회귀 확인) | **exit 0** |
| 워크트리/pseudoref | prunable 0, admin dir 0, ORIG_HEAD·FETCH_HEAD 없음 |

**실행 중 발견·수정한 사고 1건**: `.gitignore` 미커밋분을 백업본으로 복원할 때 백업본이 커밋본의
`.secret-patterns` 무시 규칙을 덮어써 패턴 파일이 추적 후보(`??`)로 노출됐다. 즉시 `git checkout --` 후
양쪽 규칙을 병합하고 `git check-ignore -v`로 무시 동작을 실측 확인함. → **교훈: 파일 단위 백업·복원은
그 사이에 일어난 커밋 변경을 덮어쓴다. 복원 후 반드시 무시/동작을 재실측할 것.**

**백업 번들**: `~/Desktop/Valuehire_v6-pre-squash-20260807.bundle` (41K, `git bundle verify` 통과).
⚠️ 비밀 히스토리 포함 — 로컬 전용, 업로드 금지. 0-5(push) 안정화 후 사장님 승인 하에 파기.

---

# 후속: 0-5 (push + CI 연결) — 2026-08-07

## 설계 판단 — CI에 실제 비밀을 올리지 않는다

GitHub Secrets에 비밀번호를 넣는 것은 유출 경로를 **늘리는** 일이다. 대신 패턴을 2계층으로 나눴다.

| 파일 | 추적 | 내용 | 사용처 |
|------|------|------|--------|
| `.secret-patterns.default` | ✅ 커밋됨 | 자격증명의 **모양**(ERE 패턴)만. 실제 값 없음 | CI + 로컬 |
| `.secret-patterns` | ❌ gitignore | 이 프로젝트의 알려진 **실제 리터럴** | 로컬 전용 |

`verify.sh`는 `SECRET_PATTERNS_FILE` 미지정 시 두 파일의 합집합을 쓰고, 둘 다 없으면 exit 2(조용한 스킵 금지).
CI에는 후자가 없으므로 전자만으로 동작한다.

## 패턴 검증 실측

로컬(BSD grep) 16/16, **컨테이너 GNU grep 3.12(CI와 동일) 10/10** 통과.

- 검출: env 대입 · export · yaml 소문자 · JSON · AWS · GitHub 토큰 · OpenAI 키 · URL 자격증명 · 개인키
- 오탐 배제: 빈 값 · 셸 기본값 문법(`${VAR:-...}`) · 함수호출 대입(`token = getToken()`) · 변수 대입 · 주석 · env 참조

이 맥의 `grep`은 셸 함수로 ugrep에 연결돼 있고 `verify.sh` 안에서는 BSD grep이 쓰인다. CI는 GNU grep이라
방언 차이 리스크가 있어 **Docker로 CI와 동일한 환경에서 재검증**했다. (`verify.sh`는 grep stderr 발생 시
fail-closed라 방언 문제가 조용히 통과될 수는 없는 설계이지만, 실측으로 확인했다.)

## 실행 중 발견·수정한 결함 3건

1. **인수 스크립트 자기 매칭** — `acceptance-0-5.sh`가 카나리 문자열 `CHATGPT_PASSWORD=...`를 파일에
   그대로 담아 자기 자신이 스캔에 걸렸다. `printf 'CHATGPT_%s=' 'PASSWORD'` 로 조립하도록 수정.
   (2026-08-06 `acceptance-0-6.sh`와 **같은 종류의 사고 3회째** — 검증 스크립트는 자기가 찾는 것을 몸에 담지 말 것)
2. **패턴 오탐** — 초판 패턴이 셸 기본값 문법(`SECRET_FILE:-...`)과 코드 대입(`token = getToken()`)을 잡았다.
   값 첫 글자 영숫자 제한 + 따옴표 형태/앵커 형태 2개로 분리해 해소.
3. **0-2 인수 스크립트가 상시 테스트로 부적합** — check 6·7·8(ref 화이트리스트·pseudoref 부재·워크트리 0개)은
   청소 **직후**에만 참인 종료상태 조건인데 상시 조건으로 걸려, 새 워크트리를 파자마자 6건 FAIL했다.
   → `ACCEPTANCE_ENDSTATE=1`일 때만 실행하도록 분리하고, 대신 **내용 기반 상시 검사**를 추가:
   `git rev-list --all --reflog --objects`의 모든 blob을 열어 스캔한다.
   판별력 실증: 격리 클론에서 비밀 커밋 후 브랜치 삭제 → `git log --all -S`는 **0건(눈 멈)**,
   새 검사는 `FAIL: 도달 가능 blob에 리터럴 잔존`으로 **검출**.

## push 전 실측 (구현자 자체 검증)

- `git rev-list origin/main..main --objects` = **32개 객체**, 전 blob을 `cat-file`로 열어 스캔 → 실제 리터럴 **0건**, 기본 패턴 매치 **0건**
- `.secret-patterns` 추적 여부 → **추적 안 됨**
- `.secret-patterns.default`에 실제 리터럴 → **없음**
- main 인수 상태: 0-2 exit 0 / 0-6 exit 0 / 0-5는 push 항목만 FAIL(예정된 미완료)

> ⚠️ 자체 검증 도중 즉석 스캔 명령이 주석 줄을 패턴으로 넘겨 grep 오류를 냈고, 그 결과의 "0건"은
> **거짓 음성**이었다. 주석 제거 후 재실행해 정정했다. — 검증 명령 자체도 검증 대상이다.

## 0-5 실행 결과 (2026-08-07 완료)

**push**: `9d0ffd9..7e20bd4 main -> main` (exit 0). 원격 브랜치는 `main` 단독.

| 검증 | 실제 출력 |
|------|-----------|
| `bash scripts/acceptance-0-5.sh` | `PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건` exit 0 |
| CI run 31138625358 (main) | **success** 9s — `PASS: 히스토리 전량 blob 스캔 0건 (blob 21개 검사)` / `스캔 대상 객체: 52개` / `PASS: 병합 완료, 가짜 검증 스크립트 0건` / `PASS: 기본 패턴 파일에 실값 없음` |
| CI run 31138691067 (카나리) | **failure** — `FAIL: secret pattern matched in tracked files: - ci-canary.txt` |
| 최종 인수 상태 | 0-2 exit 0 / 0-5 exit 0 / 0-6 exit 0 |

### CI 강제력 실증 (초록불이 의미를 가지려면 빨간불도 돼야 한다)

`ci-canary-test` 브랜치에 AWS 공식 문서의 공개 예제 키(`AKIA...EXAMPLE`, 실제 자격증명 아님)를
넣어 push → **CI가 `verify.sh` 스텝에서 잡아 job을 실패시킴**을 확인. 확인 즉시 원격·로컬 브랜치를
삭제하고 `reflog expire` + `gc --prune=now`로 잔재 3개 객체(blob/commit/tree)까지 회수했다
(`fsck --no-reflogs --unreachable` = 0건). 이 카나리에 실제 리터럴은 0건임을 별도 확인.

### V1(codex)·V2(독립 Claude) 판정 — 둘 다 **SAFE-TO-PUSH**

판정서: `docs/engineering/ci-push-v1-verdict-2026-08-07.md`, `ci-push-v2-verdict-2026-08-07.md`

V2가 push 전 지적한 4건 중 3건을 **push 전에 반영**(커밋 `9eb9fef`, `7e20bd4`):
1. `fetch-depth: 0` 주석 과대주장 → 주석 수정에 그치지 않고 **히스토리 전량 스캔 스텝을 실제 추가**
2. `acceptance-0-5.sh` 카나리의 `&&` 체인 잠복 위양성(심기 실패를 검출 성공으로 오독) → plant/add/staged rc 분리
3. `.gitignore` 보호막 미커밋(원격에 보호막 없이 올라갈 뻔) → `worktrees/` 포함해 커밋

남은 1건은 후속 이슈: **프로젝트 고유 리터럴이 산문·주석에 맨몸으로 적히면 CI가 못 잡는다**
(`.secret-patterns.default`는 `KEY=값` 형태와 형식 키만 잡는다). 과거 사고(E1)가 정확히 그 형태였으므로
로컬 pre-push 훅으로 `verify.sh`(실제 리터럴 포함)를 강제하는 것이 다음 과제다.

### 이번에도 검증이 잡은 결함 (구현자 자체 발견 포함)

- **CI 히스토리 스캔이 git 실패 시 조용히 PASS** — 컨테이너 실측에서 `git rev-list`가 실패했는데
  루프가 0회 돌고 `PASS ... 0건`을 출력했다. `rev-list` 실패·객체 2개 미만·blob 0개를 각각 exit 2로
  잡도록 fail-closed 전환하고, 검사한 blob 개수를 출력에 포함시켜 "실제로 돌았다"는 증거를 남겼다(`7e20bd4`).
- **환경 차이**: 이 맥의 `grep`은 셸 함수→ugrep, `verify.sh` 안에서는 BSD grep. CI는 GNU grep이라
  Docker(ubuntu, GNU grep 3.12)로 CI 동일 환경 재검증 — 10/10 통과.
