# task/merge-verify-reimpl 병합 독립 적대 검증 보고서

- 검증일: 2026-08-06
- 대상 브랜치/HEAD: `task/merge-verify-reimpl` / `6e52c77`
- 병합 대상: `main=2f45b7b`, `task/gptreview-real-impl=3cffb4d`
- 병합/후속 커밋: `843cde3`, `6e52c77`
- 검증 방식: Git object 직접 비교, 셸 문법·실행 검사, historical blob 회귀 비교, 양성/음성 반례 주입, fresh-context 독립 verifier

## 최종 판정

**PASS — 요청된 세 가지 병합 조건을 모두 충족한다.**

차단 결함은 발견되지 않았다. 다만 병합 회귀는 아니지만 `--no-test` 옵션 미구현과 check3 파일명 처리 한계가 남아 있으므로 아래 “잔여 결함·한계”를 별도 이슈로 추적하는 편이 안전하다.

## 1. 양쪽 브랜치 의도 보존

**판정: PASS**

### 계보와 파일 보존

- `git merge-base --is-ancestor 2f45b7b 843cde3` → exit `0`
- `git merge-base --is-ancestor 3cffb4d 843cde3` → exit `0`
- 병합의 두 parent는 `4eafcd3`과 `3cffb4d`이며, `4eafcd3`은 `main=2f45b7b`의 후속이다.
- `verify.sh`는 `2f45b7b`과 `843cde3`에서 byte-identical이다.
- 다음 재구현 파일은 `3cffb4d`과 `843cde3`에서 byte-identical이다.
  - `.claude/skills/gptreview/SKILL.md`
  - `.claude/skills/verify/SKILL.md`
  - `.claude/skills/verify/local-checks.sh`
- 다음 구형/가짜 파일은 최종 tree에 모두 없다.
  - `.claude/scripts/gptreview.js`
  - `.claude/scripts/verify.js`
  - `.claude/settings.json`
  - `.claude/skills/gptreview.md`
  - `.claude/skills/verify.md`

### 평문 비밀번호 재유입 검사

비밀번호 자체는 보고서에 재기록하지 않고 Git object에서 추출해 비교했다.

| Revision | `SKILLS_GUIDE.md`의 원래 전체 평문 자격증명 exact hit |
|---|---:|
| main 수정 직전 `2f45b7b^` | 2 |
| main `2f45b7b` | 0 |
| 재구현 브랜치 `3cffb4d` | 1 |
| 병합 `843cde3` | 0 |
| 후속 `6e52c77` | 0 |

- `843cde3`과 `6e52c77` 전체 tracked tree에서 원래 전체 평문 자격증명은 각각 `0 files / 0 lines`다.
- `verify.sh`가 검사하는 금지 리터럴을 `verify.sh` 자신만 제외하고 다시 검색한 결과도 `843cde3=0 files`, `6e52c77=0 files`다.
- `SKILLS_GUIDE.md:64-74`는 `CHATGPT_EMAIL=`과 `CHATGPT_PASSWORD=`를 빈 placeholder로만 남긴다.
- `SKILLS_GUIDE.md:24-33`은 비밀번호 자동 입력을 명시적으로 금지한다.
- 재구현 브랜치 가이드의 평문 값은 병합 시 제거됐고, 옵션명도 실제 skill과 같은 `--gpt`로 정리됐다.

### Fresh 실행

```text
$ bash verify.sh
PASS: no plaintext password in any tracked file, .env not tracked
exit=0

$ bash scripts/acceptance-0-6.sh
PASS: no plaintext password in any tracked file, .env not tracked
PASS: 병합 완료, 가짜 검증 스크립트 0건
exit=0
```

## 2. `local-checks.sh` 실제 실행 가능성

**판정: PASS**

| 검사 | 결과 |
|---|---|
| Git mode (`843cde3`, `6e52c77`) | `100755` |
| filesystem mode | `755` (`-rwxr-xr-x`) |
| shebang | `#!/usr/bin/env bash` |
| `bash -n .claude/skills/verify/local-checks.sh` | exit `0` |
| 직접 실행 | exit `0` |
| `bash` 명시 실행 | exit `0` |
| ShellCheck warning 이상 | exit `0` |

현재 저장소에는 `package.json`이 없으므로 직접 실행은 의도된 N/A 경로를 탔다.

```text
⏭️  package.json (설정 없음, 스킵)

요약: pass=0 fail=0 skip=1 (package.json 없음 — 자동 검증 대상 아님)
```

이는 통과를 조작한 출력이 아니라 `local-checks.sh:19-24`의 명시적 skip/exit 경로와 일치한다. ShellCheck 전체 기본 실행은 종료코드 직접 검사 방식에 대한 `SC2181` style 경고 5건을 냈지만 문법·실행 오류는 없었다.

Skill Creator의 `quick_validate.py`는 로컬 환경에 `PyYAML`이 없어 `ModuleNotFoundError`로 실행되지 않았다. 대체로 Ruby 표준 YAML parser를 사용해 두 `SKILL.md`의 frontmatter를 검사했고, 두 파일 모두 필수 필드 `name`, `description`만 가진 유효 YAML로 판정됐다.

## 3. acceptance check3 검출력

**판정: PASS**

`4eafcd3`의 원 패턴은 각 토큰 사이에 리터럴 공백 1개를 사용했고, `6e52c77`은 그 공백을 `[[:space:]]` 1개로 바꿨다. historical target `4d53eac:.claude/scripts/verify.js`에 두 정규식을 각각 실행한 결과:

- 원 패턴: `5`건
- 수정 패턴: `5`건
- 검출 line set: 양쪽 모두 `117, 120, 177, 183, 189`
- exact line set equality: `yes`
- 원 acceptance 스크립트의 자기 매칭: `1`건
- 수정 acceptance 스크립트의 자기 매칭: `0`건

따라서 이 변경은 historical target에 대한 검출을 잃지 않고 스크립트의 자기 매칭만 제거했다. `[[:space:]]`에는 수량자 `+`가 없으므로 “한 글자의 공백 종류”를 일반화한 것이며, 복수 공백까지 허용한다고 과장해서는 안 된다.

### 실제 acceptance 반례 주입

`README.md`에 각 금지 패턴을 하나씩 임시 주입하고 실제 `scripts/acceptance-0-6.sh`를 실행한 뒤 매번 원복했다.

| Probe | 실제 종료코드 | 판정 |
|---|---:|---|
| 하드코딩 rating 패턴 | 1 | 검출 성공 |
| 시뮬레이션 주석 패턴 | 1 | 검출 성공 |
| 하드코딩 status 패턴 | 1 | 검출 성공 |
| 무해한 유사 문자열 3종 | 0 | 오탐 없음 |

최종 원복 후 `git diff -- README.md`는 비어 있다.

## 독립 교차검증

### Claude CLI 시도

엄격 검증 절차에 따라 `env -u ANTHROPIC_API_KEY claude -p "<동일 검증 요청>"`을 실행했으나 다음 오류로 판정 본문을 얻지 못했다.

```text
Not logged in · Please run /login
SessionEnd hook ... EPERM: operation not permitted ... broker.json
exit=1
```

이 결과는 PASS 증거로 사용하지 않았다. 로그인 또는 홈 디렉터리 권한 변경은 이번 읽기 전용 병합 검증의 범위 밖이다.

### Fresh-context native verifier

기존 goal/판정을 신뢰하지 않고 raw commit과 실행 결과만 보도록 별도 verifier에 요청했다. 독립 판정도 세 항목 모두 `PASS`였으며 다음 수치가 본 검증과 일치했다.

- 전체 평문 자격증명: 병합/후속 각각 `0 files / 0 lines`
- `local-checks.sh`: mode `100755`, `bash -n=0`, 직접 실행 `0`, `pass=0 fail=0 skip=1`
- historical check3: 원/수정 각각 `5`건, 같은 line set
- 자기 매칭: 원본 `1`, 수정본 `0`

## 잔여 결함·한계

1. **`--no-test` 계약 불일치 — 비차단, 병합 전 재구현 브랜치에도 존재**
   - `.claude/skills/verify/SKILL.md:17`은 `--no-test`를 `local-checks.sh`에 전달한다고 명시한다.
   - `local-checks.sh`에는 인자 parsing이나 `--no-test` 분기가 없고, 테스트 script가 있으면 `local-checks.sh:42-48`에서 항상 실행한다.
   - 이번 병합이 새로 만든 회귀는 아니지만 skill 문서와 실제 동작의 결함이다.

2. **check3 파일명 견고성 — 비차단**
   - `scripts/acceptance-0-6.sh:19`는 newline 기반 `git ls-files | xargs grep`을 쓴다.
   - 현재 tracked tree에는 공백 또는 dash로 시작하는 경로가 없어 이번 판정은 유효하다.
   - 향후 특수 파일명이 추가되면 `git ls-files -z | xargs -0` 형태가 더 안전하다.

3. **check3 범위 예외 — 기존 정책**
   - `scripts/acceptance-0-6.sh:19`는 `docs/engineering/` 결과를 제외한다.
   - 따라서 “저장소 어디에도 없음”은 이 경로를 제외한 표현으로 이해해야 한다.

4. **동적 실행 범위**
   - 현재 저장소에 `package.json`이 없어 `local-checks.sh`의 타입체크/린트/테스트/빌드/npm audit 분기는 실제 프로젝트 구성으로 실행하지 못했다.
   - 이번 필수 판정은 셸 실행 가능성과 현재 저장소 경로에 한정한다.

## 재현 명령 요약

```bash
git merge-base --is-ancestor 2f45b7b 843cde3
git merge-base --is-ancestor 3cffb4d 843cde3
git diff --quiet 2f45b7b 843cde3 -- verify.sh
git diff --quiet 3cffb4d 843cde3 -- \
  .claude/skills/verify/SKILL.md \
  .claude/skills/verify/local-checks.sh \
  .claude/skills/gptreview/SKILL.md
git ls-tree 6e52c77 .claude/skills/verify/local-checks.sh
bash -n .claude/skills/verify/local-checks.sh
./.claude/skills/verify/local-checks.sh
bash verify.sh
bash scripts/acceptance-0-6.sh
```

## 결론

`843cde3`과 `6e52c77`은 main의 평문 비밀번호 제거 성과를 되돌리지 않으면서 재구현 브랜치의 구형 가짜 스크립트 제거와 실제 skill 폴더 도입을 보존했다. `local-checks.sh`는 실제 실행 가능한 Bash 스크립트이고, check3의 `[[:space:]]` 변경은 지정 historical target의 5건 검출을 그대로 유지하면서 자기 매칭을 제거했다.

**PR 병합 결과 판정: PASS**
