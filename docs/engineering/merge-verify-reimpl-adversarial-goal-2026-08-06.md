# merge-verify-reimpl 독립 적대 검증 Goal

## 모드와 위험

- 산출물 모드: `noncode`
- 위험등급: `L1` (근거형 병합 검증)
- 검증 대상: `843cde3` 및 후속 `6e52c77`
- 기준 커밋: `main=2f45b7b`, `task/gptreview-real-impl=3cffb4d`

## 현재 상태와 SOT

- 현재 브랜치 `task/merge-verify-reimpl`의 HEAD는 `6e52c77`이다.
- 저장소 SOT는 `README.md`이며, 실제 비밀번호 회귀 검증 진입점은 `verify.sh`다.
- `README.md:7`은 저장소가 부트스트랩 단계임을 명시한다.
- `verify.sh:6-24`는 추적 파일의 금지된 평문 비밀번호 리터럴과 추적된 `.env`를 검사한다.
- 병합 후 문서 `SKILLS_GUIDE.md:24-33`은 브라우저 로그인을 사용자에게 맡기고 자동 비밀번호 입력을 금지한다.
- 병합 후 `.claude/skills/verify/local-checks.sh:1-66`은 로컬 검증 헬퍼로 배치되어 있다.
- 후속 `scripts/acceptance-0-6.sh:15-20`은 하드코딩 점수/시뮬레이션 패턴을 전수 검색한다.

## 검증 질문

병합 충돌 해소가 `main`의 평문 비밀번호 제거 성과와 재구현 브랜치의 가짜 스크립트 제거/진짜 스킬 재구현 의도를 동시에 보존했는지, 그리고 후속 acceptance 패턴 수정이 자기 매칭만 제거하고 대상 코드 검출력은 유지했는지를 독립적으로 재현한다.

## 인수 기준

1. `843cde3`과 `6e52c77`에서 금지된 평문 비밀번호 리터럴이 `SKILLS_GUIDE.md`를 포함한 추적 파일에 재유입되지 않는다.
2. 병합 결과에는 구형 가짜 스크립트/단일 파일 스킬이 없고 재구현된 skill 폴더와 로컬 검증 스크립트가 존재한다.
3. `.claude/skills/verify/local-checks.sh`는 실행 비트, 셸 문법, 실제 실행 종료코드와 출력이 모두 일관된다.
4. `scripts/acceptance-0-6.sh` check3의 수정 패턴은 스크립트 자신을 검출하지 않으면서 `4d53eac:.claude/scripts/verify.js`에서 원래 찾던 대상을 같은 개수와 위치로 검출한다.
5. check3은 임시 추적 파일에 주입한 각 금지 패턴을 실제로 거부하고, 무해한 유사 문자열은 거부하지 않는다.
6. 저장소의 `verify.sh`, `scripts/acceptance-0-6.sh`, skill frontmatter 검증이 fresh 실행에서 통과한다.

## 주장별 증거·반례·한계

| 주장 | 요구 증거 | 반례 시도 | 한계 |
|---|---|---|---|
| 양쪽 브랜치 의도 보존 | merge parent별 diff, 파일 존재/부재, 비밀번호 스캔 | 삭제된 가짜 파일 잔존 및 문서 재유입 검색 | 커밋에 기록된 저장소 범위만 판정 |
| local-checks 실행 가능 | mode, shebang, `bash -n`, 직접 실행 | package.json 부재 경로와 실패 전파 확인 | 외부 npm 프로젝트 전체 조합은 범위 밖 |
| check3 검출력 유지 | 구/신 정규식의 동일 대상 비교 | 각 패턴 주입 양성, 유사 문자열 음성 | GNU/BSD grep 차이는 현재 환경에서만 실행 검증 |

## Harness 게이트

- Gate 0/1: 기존 워크트리와 커밋 범위를 확인하고 본 문서에 계약을 고정한다.
- Gate 2/3: 구현 변경은 하지 않는다. 검증용 임시 파일은 작업 후 원복한다.
- Gate 4: 명령, 종료코드, 검출 개수를 판정 보고서에 기록한다.
- Gate 5/6: push, merge, 배포는 범위 밖이다. PR에 첨부할 보고서 경로만 제공한다.

## 적대 검증 항목

- 병합 커밋 메시지를 증거로 간주하지 않고 tree와 실행 결과로 재검증한다.
- `verify.sh`가 자기 자신을 제외한다는 점을 이용한 누락이 없는지 별도 Git object 스캔으로 확인한다.
- check3의 자기 매칭 회피가 파일 면제나 탐색 범위 축소로 구현되지 않았는지 확인한다.
- 원 정규식과 수정 정규식의 매치 집합을 동일 historical blob에서 비교한다.
- Claude 1차 판정을 받은 뒤 Codex가 모든 근거를 재현하고 과장·누락을 재공격한다.

## 비범위

- 커밋 수정, 리베이스, 머지, push, 배포
- 실제 브라우저 로그인 및 ChatGPT 리뷰 실행
- 저장소 밖 프로젝트에서의 `local-checks.sh` 전체 호환성 보장

## 적대 검증 로그

### Claude CLI 1차 시도

실행 명령:

```text
env -u ANTHROPIC_API_KEY claude -p "이 저장소를 읽기 전용으로 독립 적대 검증하라. 대상은 main 2f45b7b에서 task/gptreview-real-impl 3cffb4d을 병합한 843cde3과 후속 6e52c77이다. 반드시 직접 git tree/diff와 실행 결과를 확인하라: (1) main의 평문 비밀번호 제거와 상대 브랜치의 가짜 스크립트 제거/진짜 skill 재구현 의도가 모두 보존됐는지, 특히 SKILLS_GUIDE.md 평문 비밀번호 재유입 여부 (2) .claude/skills/verify/local-checks.sh가 실제 실행 가능한 셸인지, mode/shebang/bash -n/직접 실행 (3) scripts/acceptance-0-6.sh check3의 리터럴 공백→[[:space:]] 변경이 4d53eac:.claude/scripts/verify.js에서 원 패턴과 같은 대상을 검출하는지 및 자기매칭만 제거하는지. 커밋 메시지를 증거로 쓰지 말고, 소스 수정도 하지 마라. 첫 줄은 VERDICT: PASS 또는 VERDICT: FAIL. 이후 각 항목에 실행 명령, exit code/개수, file:line, 결함 또는 잔여 위험을 한국어로 구체적으로 써라. 빈 답이나 Done 금지."
```

실행 결과:

```text
Not logged in · Please run /login
SessionEnd hook ... EPERM: operation not permitted ... broker.json
exit=1
```

판정 본문을 얻지 못했으므로 이 실행은 교차검증 증거에서 제외했다.

### Fresh-context native verifier 판정

```text
VERDICT: PASS

1. PASS — main의 verify.sh는 byte-identical이고 구형 5개 파일은 제거됐으며
   재구현 skill 3개 파일은 3cffb4d의 blob과 동일하다.
   SKILLS_GUIDE.md의 원래 전체 평문 자격증명 exact hit는
   2f45b7b^=2, 2f45b7b=0, 3cffb4d=1, 843cde3=0, 6e52c77=0이다.
2. PASS — local-checks.sh는 100755, bash -n=0, 직접 실행=0이며
   현재 출력은 pass=0 fail=0 skip=1이다.
3. PASS — historical target에서 원/수정 패턴은 같은 5개 line을 검출하고
   자기 매칭은 1건에서 0건으로 줄었다.

잔여 결함: --no-test 문서 계약은 local-checks.sh에 구현되지 않았다.
한계: check3의 newline 기반 git ls-files | xargs는 특수 파일명에 취약하다.
```

### Codex 2차 재현·재공격

| verifier 주장 | Codex 재현 | 결과 |
|---|---|---|
| 두 기준 커밋이 merge ancestor | `git merge-base --is-ancestor` 각각 exit `0` | 일치 |
| main `verify.sh` 보존 | `git diff --quiet 2f45b7b 843cde3 -- verify.sh` exit `0` | 일치 |
| 재구현 skill 3개 보존 | `git diff --quiet 3cffb4d 843cde3 -- <3 files>` exit `0` | 일치 |
| 평문 자격증명 미재유입 | commit별 object scan 및 `SKILLS_GUIDE.md` exact count 재현 | 일치 |
| local-checks 실행 가능 | mode `100755`, `bash -n=0`, 직접 실행 `0` | 일치 |
| check3 검출 5건 유지 | line `117,120,177,183,189`, exact set equality `yes` | 일치 |
| 자기 매칭만 제거 | 원 `1`, 수정 `0` | 일치 |
| `--no-test` 미구현 | SKILL에는 1건, script 인자 parsing은 0건 | 일치 |

Codex 추가 재공격:

- 세 금지 패턴을 추적 파일에 하나씩 주입했을 때 actual acceptance가 각각 exit `1`인지 확인했다.
- 유사하지만 금지 대상이 아닌 문자열은 actual acceptance가 exit `0`인지 확인했다.
- `[[:space:]]`가 복수 공백까지 허용한다는 과장 가능성을 확인해, 정확히 “한 글자의 whitespace 종류 일반화”로 판정을 제한했다.
- `docs/engineering/` 제외와 newline 기반 `xargs`를 잔여 한계로 공개했다.

Claude CLI 판정은 확보하지 못했지만, 독립 native verifier의 모든 근거를 Codex가 다시 실행해 같은 결과를 얻었고 누락된 두 한계를 추가 확인했다.
