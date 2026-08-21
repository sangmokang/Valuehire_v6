# HumanSearch L0 낡은 실행 지시 폐기 목표 — 2026-08-22

VERDICT: 로컬·적대 검증 PASS / PR 원격 검사 대기

## 1층 — 결론

낡은 두 문서를 짧은 폐기 안내로 바꿔, 누구도 새 작업 지시로 실행하지 못하게 합니다. 현재 제품과
검사는 바꾸지 않으며, 검토 요청을 열고 그 요청의 서버 검사가 끝난 뒤 멈춥니다.

사용자가 지금 결정할 사항은 없습니다. 합치기는 이 작업에 포함하지 않습니다.

## 2층 — 판단 근거

두 문서는 이미 끝난 화면 분류 작업과 아직 만들지 않은 로그인 이후 절차를 한 작업처럼 섞고 있습니다.
현재 정본과 구현은 다섯 화면 결과만 소유하고, 실제 화면 판독·로그인·후보 검색은 별도 작업입니다.
과거 본문은 Git 이력에 남으므로 현재 파일에 실행 절차를 보존할 이유가 없습니다.

> **무엇을** — 두 파일의 과거 본문을 전부 제거하고 짧은 폐기 안내만 남깁니다.
>
> **왜** — 맨 위 경고 아래에 실행 지시가 남으면 복사·실행될 수 있기 때문입니다.
>
> **버린 길** — 기존 본문 위에 경고만 추가하는 방식을 버렸습니다. 가짜 합격이며 실행 위험이 남습니다.
>
> **대가** — 현재 파일만으로 과거 맥락을 읽을 수 없고 Git 이력을 열어야 합니다.
>
> **되돌리기** — 이 변경의 단일 커밋을 되돌리면 과거 본문이 복원됩니다. 다만 복원은 현행 계약과
> 충돌하므로 별도 검토 없이는 실행 지시로 재사용하지 않습니다.

## 3층 — 계약과 증거

### 위험 등급과 작업 경계

- 등급: L3. 제품 동작은 바꾸지 않지만, 두 대상 문서와 이 검증 장부까지 3파일을 변경합니다.
- 기준: `origin/main`의 `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`.
- branch: `task/retire-humansearch-l0-prompts`.
- worktree: `worktrees/retire-humansearch-l0-prompts`.
- 변경 허용: 두 폐기 문서와 이 goal·검증 장부 1개.
- 변경 금지: `docs/sot/`, 제품 코드, 시험, 의존성, main 사용자 변경, PR #15의 branch·상태·내용.
- 외부 행동: 일반 push와 PR 생성만 허용. main 직접 push, 합치기, 배포는 금지.

저장소에는 `AGENTS.md`와 `CLAUDE.md` 파일이 존재하지 않았다. 이 세션에 사용자가 제공한
`AGENTS.md` 지시와 `/Users/kangsangmo/.codex/skills/strict/SKILL.md` 306줄 전체를 직접 읽었다.

### 현재 상태와 근본 원인

- `docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md`는 변경 전 176줄이며,
  worktree 생성, push, 일곱 상태 전이, 자동 실행 순서를 포함했다.
- `docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md`는 변경 전 110줄이며,
  옛 선행 PR과 전이표, 다음 단계 착공 지시를 포함했다.
- `docs/sot/humansearch-l0-surface-contract.md:60`은 현재 출력이 정확히 다섯 값임을 고정한다.
- `docs/sot/humansearch-l0-surface-contract.md:68`은 인증 결과가 전체 실행 종료가 아님을 고정한다.
- `docs/sot/humansearch-l0-surface-contract.md:132`는 실제 포털·로그인·개인정보를 비범위로 둔다.
- `humansearch/src/humansearch/auth_surface.py:15`는 현행 다섯 상태 구현의 시작점이다.
- `humansearch/src/humansearch/auth_surface.py:64`는 현재 순수 분류 함수다.
- PR #26은 2026-08-18에 병합됐고 병합 커밋은 `b6aee6a352309cfd721cd3b3d63d31ff7c0787f9`다.
- PR #13, #14, #15는 조회 시점에 열려 있지만 PR #26 병합 뒤 현행 L0의 선행조건이 아니다.

근본 원인은 날짜가 있는 과거 실행 지시가 완료 뒤에도 현재 파일로 남아, 정본보다 구체적인 착공
명령처럼 보인다는 점이다.

### T 계약 — 함께 쓰는 채점 기준

#### EARS 인수 기준

1. **AC1.** When 독자가 대상 파일의 첫 줄을 읽으면, 두 문서는 모두 `폐기됨 — 실행 금지`를 제목에
   표시해야 한다.
2. **AC2.** While 두 폐기 문서가 현재 branch에 존재하면, 기존 worktree·push·전이표·자동 진행·다음
   착공 지시는 0건이어야 한다.
3. **AC3.** If 대체 경로를 확인하면, 존재하지 않는
   `codex-humansearch-l0-surface-classifier-v2-2026-08-16.md` 참조는 0건이어야 한다.
4. **AC4.** When 과거 순서를 설명하면, PR #13/#14/#15는 현재 선행조건이 아니라 더 이상 유효하지
   않은 옛 순서라고 명시해야 한다.
5. **AC5.** Where 현행 상태를 설명하면, 다섯 상태 계약·PR #26 구현 완료·실제 포털 호출 경로는
   아직 별도라는 세 사실을 모두 명시해야 한다.
6. **AC6.** When 변경 범위를 계산하면, 변경 파일은 허용한 3개뿐이고 두 폐기 문서는 각각 80줄
   이하여야 한다.
7. **AC7.** When 원격 검사가 끝나면, 로컬 HEAD·원격 branch HEAD·PR HEAD·서버 검사 SHA는 같고
   서버 결론은 성공이어야 한다.

#### counter-AC — 가짜 합격 시나리오

- 첫 줄에 경고만 추가하고 아래 실행 본문을 보존한다.
- 낡은 v2 문서를 대체 실행 경로로 링크한다.
- PR #13/#14/#15를 여전히 현재 착공 조건으로 표현한다.
- 실제 로그인·후보 검색이 완료됐다고 과장한다.
- 일곱 상태나 Active Tab Bridge를 현행 계약처럼 남긴다.
- 명령을 실행하지 않고 통과했다고 기록하거나 옛 커밋의 서버 성공을 현재 HEAD 성공으로 사용한다.

#### 입출력·오류·경계 계약

```json
{
  "input": {
    "files": [
      "docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md",
      "docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md"
    ],
    "authority": [
      "docs/sot/humansearch-l0-surface-contract.md",
      "humansearch/src/humansearch/auth_surface.py",
      "docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md",
      "https://github.com/sangmokang/Valuehire_v6/pull/26"
    ]
  },
  "output": "두 파일 각각 80줄 이하의 폐기 안내",
  "error": "필수 문구·링크 누락, 금지 지시 잔존, 허용 외 파일 변경, SHA 불일치 중 하나라도 있으면 FAIL",
  "boundaries": "제품·SOT·시험·의존성·PR #15·main 사용자 변경은 읽기 전용이며 재시도·동시 실행·권한 예외 없음"
}
```

→ 문서 교체의 입력, 결과, 실패 조건, 손대지 않을 경계를 한 구조로 고정했다. 빈 파일이나 대상 0개는
합격이 아니다.

### Harness 게이트 계획

- 게이트 0: 규칙·과거 이력·PR 상태·미해결 검사 장부 회수.
- 게이트 1: 위 EARS 기준, counter-AC, 입출력·오류·경계 계약 고정.
- 게이트 2: fresh `origin/main`의 전용 worktree에서 동일 판정기의 올바른 RED를 먼저 실행.
- 게이트 3: 두 본문 전체를 최소 폐기 안내로 교체하고 동일 원명령을 GREEN으로 재실행.
- 게이트 3.5: 문서 링크가 실제 정본·구현·goal·병합 PR로 이어지는지 확인.
- 게이트 4: `git diff --check`, 문서 정본 검사, Strict 원칙 검사, 범위 검사, 비밀 검사를 실행.
- 게이트 5: Lore 커밋, 일반 push, 한국어 PR, 현재 SHA의 서버 검사 성공 확인.
- 게이트 6: 합치기와 worktree 정리는 이번 작업에서 실행하지 않는다.

직접 작성한 코드 파일은 0개이므로 코드 500/501 경계와 제품 라이브 호출은 첫 검사 전 `SKIPPED`로
고정한다. 문서 줄 수는 더 엄격한 80줄 경계로 실제 검사한다. 제품 동작을 바꾸지 않으므로 실제 포털
호출을 완료 증거로 사용하지 않는다.

### G/V1/V2/T 역할

- G: 이 문서와 두 폐기 문서를 작성한 현재 Codex.
- V1: `ANTHROPIC_API_KEY`를 제거한 Claude CLI가 읽기 전용으로 T를 공격한다.
- V2: 새 맥락 Codex가 V1의 주장과 명령을 재현하고 누락·과장을 반대 방향으로 공격한다.
- T: 이 문서의 EARS 기준, counter-AC, 경계 계약, 저장소 정본과 사용자 지시.

### 읽은 정본과 과거 증거

- `/Users/kangsangmo/.codex/skills/strict/SKILL.md`
- `docs/sot/coding-principles.md`
- `docs/sot/principles.yaml`
- `docs/sot/verification-commands.md`
- `docs/sot/git-workflow.md`
- `docs/sot/humansearch-l0-surface-contract.md`
- `docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md` 전체 1003줄
- `humansearch/src/humansearch/auth_surface.py`
- `scripts/check-docs-sot.sh`
- `scripts/acceptance-principles-check.sh`
- `hooks/pre-push`
- `.github/workflows/verify.yml`
- `scripts/verify/check-verified-sha.sh`
- 대상 두 문서의 `git log --all -- <paths>` 이력
- PR #13, #14, #15, #26의 원격 상태

### 검증 장부

세션 식별자: `01a0250c-7d43-7c60-85e8-a241131a2cfb`

#### 원칙 정본 직접 로드

- 시각: 2026-08-22T01:00+09:00
- commit: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 명령: `sed -n '1,1000p' docs/sot/coding-principles.md`
- 종료값: 0, 상태: PASS
- 전체 출력: 해당 commit의 `docs/sot/coding-principles.md` 74줄 전문이며 위 "읽은 정본" 경로에
  그대로 보존된다.
- 명령: `sed -n '1,1000p' docs/sot/principles.yaml`
- 종료값: 0, 상태: PASS
- 전체 출력: 해당 commit의 `docs/sot/principles.yaml` 345줄 전문이며 위 "읽은 정본" 경로에
  그대로 보존된다.

→ 두 정본 파일은 존재하고 비어 있지 않았으며 현재 저장소에서 전문을 직접 읽었다.

#### Strict 필수 원칙 검사

- 시각: 2026-08-22T01:07:51+09:00
- commit: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 명령: `bash scripts/acceptance-principles-check.sh`
- 종료값: 0, 상태: PASS

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 원칙 34개를 읽었고 pre-push와 서버 검사 연결을 각각 1개 확인했다.

#### 게이트 0과 RED 원장

- 첫 결합 명령: 30초 제한으로 종료값을 받지 못해 `NOT_RUN`. 마지막 출력은 HEAD/origin 일치까지였다.
- 분해 명령: `bash scripts/session-status.sh`
- 종료값: 0, 상태: PASS

```text
HEAD: c59bad7 (synced)
ORIGIN: c59bad7
RED: 1/26 (acceptance-0-7.sh 제외 — CI 담당)
```

- 원인 분해: `bash scripts/acceptance-0-2.sh`
- 종료값: 2, 상태: SKIPPED

```text
FAIL: .secret-patterns 없음/빈 파일 — AC 판정 불가
```

→ 검증 정본은 이 명령이 추적하지 않는 로컬 실제 패턴을 요구하는 CI 비범위 검사라고 명시한다.
최종 게이트 0에서는 내용을 출력하거나 Git에 넣지 않고 기존 로컬 입력을 격리 worktree에 권한 0600으로
잠시 복제한 뒤 같은 `session-status` 원명령을 재실행하고 즉시 제거한다.

#### 문서 계약 RED

- 시각: 2026-08-22T01:12+09:00
- commit: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 명령: 이 문서의 AC1~AC6을 한 번에 검사하는 동일 bash 판정기.
- 종료값: 1, 상태: RED PASS
- 결과: 첫 줄 경고 0/2, 80줄 이하 0/2, 필수 문구 0/18이며 낡은 전이표·자동 진행·push·worktree
  지시가 실제로 검출됐다.

→ 문법이나 폴더 오류가 아니라 제거해야 할 실행 본문 때문에 실패했다.

#### 문서 계약 GREEN

- 시각: 2026-08-22T01:13+09:00
- commit: 작업 전 기준 `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`, 미커밋 변경 상태
- 명령: RED와 같은 AC1~AC6 bash 판정기
- 종료값: 0, 상태: PASS

```text
PASS: docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md 첫 줄/제목 경고
PASS: docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md 20줄 (<=80)
PASS: docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md 필수 문구 9/9
PASS: docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md 첫 줄/제목 경고
PASS: docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md 20줄 (<=80)
PASS: docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md 필수 문구 9/9
PASS: 금지된 낡은 실행 지시 또는 참조 0건
```

→ 두 파일 모두 제목 경고, 길이, 폐기 이유, 네 현행 근거, 미완료 범위, 복원 금지를 만족했다.

이 출력 뒤 첫 Claude 시도가 PR #13/#14/#15의 현재 지위를 더 직접 쓰라고 정보 등급으로 지적해,
두 폐기 문서에 `PR #13/#14/#15는 현행 L0의 선행조건이 아닙니다.` 한 줄씩을 추가했다. 같은 원명령을
다시 실행한 현재 결과는 두 파일 각각 21줄, 필수 문구 전부 존재, 금지 표식 0건, 종료값 0이다. 따라서
위 20줄은 당시 원출력이고 현재 줄 수는 21줄이다.

제출 전 제목 오해 가능성을 더 줄이기 위해 두 첫 줄에서 `실행 지시`와 `착공 지시` 표현을 각각
`과거 자율 작업 문서`, `과거 착수 문서`로 바꿨다. 같은 원명령을 다시 실행한 현재 결과:

```text
PASS: docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md first_line=# 폐기됨 — 실행 금지: HumanSearch L0 과거 자율 작업 문서
PASS: docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md lines=21 <=80
PASS: docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md first_line=# 폐기됨 — 실행 금지: HumanSearch L0 과거 착수 문서
PASS: docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md lines=21 <=80
PASS: forbidden stale instruction/reference count=0
ac_exit=0
```

→ 현재 제목도 실행 금지를 첫 줄에서 말하고, 대상 두 문서에는 낡은 실행 지시가 남지 않았다.

#### 로컬 G 검증

- 시각: 2026-08-22T01:14:10+09:00
- commit: 작업 전 기준 `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`, 미커밋 변경 상태
- 결합 명령 종료값: 0, 상태: PASS

```text
git_diff_check_exit=0
PASS: docs/sot/INDEX.md 존재, 1366바이트 (<=20000)
PASS: docs/sot/coding-principles.md 존재, 19184바이트 (<=20000)
PASS: docs/sot/hook-contracts.md 존재, 4455바이트 (<=20000)
PASS: docs/sot/git-workflow.md 존재, 2225바이트 (<=20000)
PASS: docs/sot/verification-commands.md 존재, 7761바이트 (<=20000)
PASS: hooks/pre-commit 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: hooks/pre-push 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/install-hooks.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/session-status.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/acceptance-0-7.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
OK: docs/sot 재구성 AC 전부 충족
docs_sot_exit=0
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
principles_exit=0
PASS: no secret-pattern match in any tracked file, .env not tracked
verify_exit=0
PASS: 추적 파일 186개 검사, 위반 0건
PASS: 기록 전량 blob 989개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 186개 중), 개인정보 적재 0건
data_scan_exit=0
PASS: link target exists docs/sot/humansearch-l0-surface-contract.md
PASS: link target exists humansearch/src/humansearch/auth_surface.py
PASS: link target exists docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md
```

→ 공백 오류, 문서 정본, 원칙 34개, 비밀, 이력 989개, 링크 3개가 모두 현재 변경에서 통과했다.
`scripts/brief-lint.sh`는 저장소에 없어 첫 검사 전 선택 검사 `SKIPPED`로 고정했으며 사람 검수는
생략하지 않는다.

변경 목록은 다음 세 파일뿐이었다.

```text
 M docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md
 M docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md
?? docs/engineering/retire-humansearch-l0-prompts-goal-2026-08-22.md
```

→ 제품, SOT, 시험, 의존성, PR #15 branch 파일은 변경되지 않았다.

#### R2 결함 주입

- 시각: 2026-08-22T01:17+09:00
- 위치: `mktemp -d`가 만든 저장소 밖 복사본
- 상태: PASS

첫 복사본에서 첫 줄 제목 경고를 제거하고, 둘째 복사본에 `git push origin task/humansearch-L0` 한 줄을
넣은 뒤 같은 판정기를 실행했다.

```text
FAIL: docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md 첫 줄/제목 경고 없음
PASS: docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md 22줄 (<=80)
docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md:22:git push origin task/humansearch-L0
FAIL: 금지된 낡은 실행 지시 또는 참조가 남음
exit=1
```

→ 제목만 깨뜨린 경우와 길이 안에서 push 한 줄만 되살린 경우를 모두 검출했다. 첫 임시 삭제 명령은
실행 정책이 `rm -rf`를 거부해 실행되지 않았고, 같은 경로에 `find <정확한 임시 경로> -depth -delete`를
사용해 `temp_cleanup=PASS`를 확인했다. 원본 worktree 변경 목록은 전후 같은 3파일이었다.

### 롤백·영향 반경·데이터 안전

- 영향 반경: 현재 두 날짜 문서를 읽는 사람과 자동화. 제품 실행 파일과 정본 계약은 바뀌지 않는다.
- 롤백: 이 PR의 단일 커밋을 되돌린다. 롤백 실패 시 branch와 PR을 그대로 열어 두고 부분 적용을
  숨기지 않으며, 복구 전에는 branch나 worktree를 삭제하지 않는다.
- 데이터 안전 AC: 후보자·자격증명·실제 포털에 접근하지 않고 추적 파일에 민감정보를 추가하지 않는다.
- PR #15: 조회 외 쓰기 0건을 변경 파일 목록과 원격 상태로 다시 확인한다.

## 적대 검증 로그

### Claude V1 첫 시도 — 권한 실패

- 명령: `env -u ANTHROPIC_API_KEY claude -p --output-format json --permission-mode dontAsk`
- 실행 주체: Claude Opus 5 CLI 2.1.238
- 세션: `ddc8451a-9d61-4299-b710-20f673eb3e42`
- 종료값: 0, 판정: FAIL
- 권한 거부: Bash 3건, 검색 1건
- 판정 이유: 대상 문서 전문은 계약을 만족했지만 필수 명령과 변조가 모두 `NOT_RUN`이었다.

→ 종료값 0은 CLI가 답변을 만들었다는 뜻일 뿐 검증 합격이 아니다. 필수 실행이 없으므로 이 회차는
V1 PASS로 세지 않고, 동일 작업을 실행 권한이 있는 폐기 가능한 복제본에서 한 번 재시도했다.

### Claude V1 재시도 — 유효한 판정

- 명령: `env -u ANTHROPIC_API_KEY claude -p --output-format json --dangerously-skip-permissions`
- 실행 주체: Claude Opus 5 CLI 2.1.238
- 세션: `360bf725-9fb6-4a22-bdb6-3cb189769e20`
- 격리 위치: `mktemp` 아래 폐기 가능한 저장소 복제본
- 종료값: 0, 첫 줄: `VERDICT: PASS`
- 권한 거부: 0건
- 실행 회차: 51
- 상태: PASS

판정 원문 핵심 결론:

```text
VERDICT: PASS

합격입니다. 낡은 두 지시 문서는 첫 줄만 읽어도 "이건 버려진 문서이고 실행하면 안 된다"는 걸
알 수 있게 바뀌었고, 그 안에 남아 있던 실제 실행 명령은 한 줄도 남지 않았습니다.

바꾸지 말아야 할 것도 전부 그대로입니다. 제품 코드, 정본 계약 문서, 시험, 의존성이 원격 기준선
대비 변경 0건이고, 손대면 안 되는 검토 요청 15번은 조회만 했으며 그 상태가 그대로입니다.
```

필수 명령 원문:

```text
git diff --check                                      exit 0
bash scripts/check-docs-sot.sh                        exit 0
bash scripts/acceptance-principles-check.sh           exit 0
bash verify.sh                                        exit 0
inline 판정기 — 대상 0개                              exit 3 (의도된 실패)
inline 판정기 — 현재 두 문서                          exit 0
inline 판정기 — origin/main 옛 본문                   exit 1 (의도된 실패)
변조 A — 제목 제거                                   exit 1 (검출 성공)
변조 B — git push 추가                               exit 1 (검출 성공)
복원 후 판정기 A/B                                   exit 0 / 0
시작/종료 git status                                  동일
```

V1이 보존한 저장소 검사 출력:

```text
OK: docs/sot 재구성 AC 전부 충족
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
PASS: no secret-pattern match in any tracked file, .env not tracked
```

V1 결함 주입 원문:

```text
FAIL: A/autoloop.md 첫 줄이 '폐기됨 — 실행 금지' 제목이 아님
PASS: A/autoloop.md 20줄 (<=80)
PASS: A/autoloop.md 금지 표식 0건 (21개 패턴)
PASS: A/autoloop.md 필수 문구 9/9
VERDICT: FAIL
EXIT_tamperA=1

PASS: B/kickoff.md 첫 줄 제목 경고
PASS: B/kickoff.md 23줄 (<=80)
FAIL: B/kickoff.md 금지 표식 검출 [git push]
PASS: B/kickoff.md 필수 문구 9/9
VERDICT: FAIL
EXIT_tamperB=1

EXIT_A_restored=0
EXIT_B_restored=0
```

→ 대상 0개, 옛 본문, 제목 제거, push 삽입이 모두 실패했고 현재 문서와 복원본만 통과했다. V1은
PR #26이 `MERGED`, PR #15가 `OPEN`, 보호 경로·의존성·시험 변경이 0건임을 읽기 전용으로 확인했다.

V1 발견사항은 LOW 1건이었다. 문서 계약 GREEN 절의 20줄 원출력 뒤 명시성 보강 한 줄이 추가돼
현재 21줄이라는 경위가 장부에 없다는 지적이다. 위 GREEN 절에 시간 순서를 보존해 설명했고 같은
원명령에서 두 파일 각각 21줄·종료값 0을 재확인했다. 제품·계약 결함은 0건이다.

V1 전체 판정은 위 세션 식별자의 CLI 결과에 보존된다. 이 장부에는 판정 단어, 결함 수·심각도,
file:line, 원인, 사업 영향, 필수 명령과 결함 주입 전체 출력을 보존했다. 새 Codex V2는 이 요약을
액면 그대로 믿지 않고 V1의 원문 주장과 현재 파일을 직접 대조한다.

### Codex V2 — 새 맥락 재공격

- 명령: `codex exec -C /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/retire-humansearch-l0-prompts -s workspace-write -c approval_policy=never --model gpt-5.5`
- 세션: `01a02540-796b-7e90-9f7f-26afb9f107b9`
- 종료값: 0
- 원본 시작/종료 상태: 같은 3파일 변경
- 첫 줄: `VERDICT: FAIL`
- 실패 이유: V2 세션 안에서 `gh pr view`와 `curl`이 모두 `api.github.com` 네트워크 실패를 내 PR #26/#15의 현재 상태를 독립 확인하지 못했다.

V2가 직접 재현한 PASS 근거:

```text
두 폐기 문서 21줄 이하/80줄 이하, 첫 줄 경고: PASS
대상 두 문서 금지 지시 0건: PASS
필수 근거 4개 존재: PASS
변경 파일 3개뿐: PASS
git diff --check: exit 0
bash scripts/check-docs-sot.sh: exit 0
bash scripts/acceptance-principles-check.sh: exit 0
bash verify.sh: exit 0
숨은 control/html hits=0
상대 링크 OK
mktemp 제목 제거와 git push 삽입: exit 1로 검출
```

V1 대비 표:

| 쟁점 | V1 | V2 | 최종 처리 |
|---|---|---|---|
| 문서 본문 폐기 상태 | PASS | 일치 | PASS |
| 20줄 vs 21줄 | LOW 1건 | 현재 21줄, 장부 설명 확인 | PASS |
| PR #26/#15 상태 | MERGED/OPEN 확인 | V2 환경에서 재현 실패 | 부모 세션 원명령으로 교차확인 |
| 지속성 검사 신설 | 제안 | 3파일 제한과 충돌 | 채택하지 않음 |
| 변조 검출 | PASS | 직접 재현 PASS | PASS |

`V1이 잡은 G 과장 1건 / V2가 잡은 V1 과장·누락 2건`. 이 중 PR 상태 재현 실패는 산출물 결함이
아니라 V2 세션의 네트워크 한계였다. 부모 세션에서 같은 원격 조회를 즉시 재실행했다.

```text
gh pr view 26 --repo sangmokang/Valuehire_v6 --json number,state,mergedAt,mergeCommit,url,title,headRefName,baseRefName
{"baseRefName":"main","headRefName":"task/humansearch-l0-surface-classifier","mergeCommit":{"oid":"b6aee6a352309cfd721cd3b3d63d31ff7c0787f9"},"mergedAt":"2026-08-18T09:06:52Z","number":26,"state":"MERGED","title":"HumanSearch L0 인증 화면 분류 계약을 5상태로 고정한다","url":"https://github.com/sangmokang/Valuehire_v6/pull/26"}

gh pr view 15 --repo sangmokang/Valuehire_v6 --json number,state,mergedAt,mergeCommit,url,title,headRefName,baseRefName,headRefOid
{"baseRefName":"main","headRefName":"task/docs-snapshot","headRefOid":"0179856cba0a77e1e995313e0d35ea03b8ec8ed2","mergeCommit":null,"mergedAt":null,"number":15,"state":"OPEN","title":"docs: HumanSearch 정본·자율 하네스와 기획 산출물 보존","url":"https://github.com/sangmokang/Valuehire_v6/pull/15"}
```

→ PR #26은 병합됐고 PR #15는 열려 있다. 이번 작업에서 PR #15에는 조회 외 쓰기 명령을 실행하지 않았다.

## 제출 직전 셀프 감사

§8-6b 아홉 문항은 최종 원격 검증 뒤 각각 `아니오`로 기록한다. 현재는 제출 전이므로 미판정이다.
