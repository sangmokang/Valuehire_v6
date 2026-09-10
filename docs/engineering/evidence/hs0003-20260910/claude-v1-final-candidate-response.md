제가 만든 임시 파일은 모두 정리했고, 남은 `/tmp/hs0003-*` 파일은 이전 세션이 만든 것이라 건드리지 않았습니다. 판정을 정리합니다.

VERDICT: PASS

## 결론

현재 후보는 보호 이름을 전각·닮은꼴 문자로 위장한 입력을 실제 검사 경로에서 거부하고, 정상 한글·일본어·아랍어·라틴 이름과 무관한 전각 문장, 그리고 `PR #131`·`ＰR #131`·`hs-kickoff-other`·`hｓ-kickoff-other` 네 가지 정상 대조군은 허용합니다. 빈 입력, 빈 이름 한 줄, 깨진 바이트는 종료값 2로 닫힙니다. 제공된 증거의 핵심 수치는 제가 직접 다시 실행해 모두 같은 값이 나왔습니다. 작업트리는 검증 전후로 바뀌지 않았습니다.

합격을 흔들지는 않지만 기록해야 할 약점이 두 가지 있습니다. 첫째, 같은 줄에 정상 이름과 위장 이름이 함께 있을 때 첫 등장만 보는 고장 사본이 시험을 통과합니다. 실제 코드는 이 경우를 잡지만, 시험이 이 동작을 지키지 못합니다. 둘째, 공백만 있는 이름 한 줄은 계약의 "빈 이름 한 줄"로 취급되지 않고 종료값 0입니다. 실제 shell 경로에서는 앞뒤 공백을 잘라 넘기므로 도달하지 않습니다.

## 판단 근거

**선택한 해석.** "같은 후보인지"는 manifest 파일별 SHA-256과 bundle SHA-256을 명시된 알고리즘으로 재계산해 판단했습니다. "실제 shell 경로에서 거부"는 helper 단독 호출이 아니라 `run-acceptance.sh` → `acceptance-hs-kickoff.sh` → helper 전체 경로를 임시 fixture에서 돌린 결과로 판단했습니다. "고장 사본이 시험에 잡히는가"는 제공된 harness를 재사용하지 않고 제가 별도로 쓴 변이 10종으로 판단했습니다.

**버린 해석.** 과거 Claude V1 PASS와 Codex V2 FAIL 산출물은 이전 후보의 증거로만 취급하고 현재 판정 근거에서 제외했습니다. 결합 문자·양방향 문자·보이지 않는 문자·다중문자 위장은 계약이 명시적으로 제외했으므로, 이 항목들이 통과되는 것을 결함으로 세지 않았습니다.

**틀리면 깨지는 것.** 원격 CI는 실행하지 않았으므로 CI 러너의 python3 버전 차이는 미확인입니다. 코드는 표준 라이브러리만 쓰고 `from __future__ import annotations`를 선언해 3.9 이상이면 동작할 것으로 추정합니다. 제 변이 harness는 fixture 파일만 복사한 임시 저장소에서 돌았으므로, 근거 커밋 실존 검사 같은 원본 저장소 의존 항목은 변이 대상이 아닙니다.

**건너뜀·미확인.** 원격 push·PR·병합·CI는 실행하지 않았습니다(`NOT_RUN`). 소유 파일 600/601 경계 고장 사본을 돌리는 저장소 공식 검사기는 찾지 못해 줄 수와 함수 길이를 직접 계산했습니다. `.env`·인증 값·환경 전체 목록은 읽지 않았습니다. 첫 실제 shell 재현 스크립트는 임시 디렉터리 생성 순서 오류로 한 번 실패했고, 순서를 고쳐 재실행해 성공했습니다.

## 기술 상세와 증거 원문

### 1. 후보 동일성

```text
HEAD d1058cadb764056c4f52696ea0321038c660a12c (= 두 번째 RED)
manifest sha256 41aa89efa6c883a64d333d9428fea33a22a1f13f8fe1142364e58521649aead4
bundle   sha256 0ccf996ee201ecabe4b1a66b6c00f2a04a669c5476960f8c1feca026f12b8c85  MATCH
9 files: all OK (path, sha256, bytes)
git status: M goal.md, M verification-commands.md, M mutations.sh, M acceptance-hs-kickoff.sh, ?? evidence/, ?? licenses/, ?? 3 verify files
```
→ 제공된 지문과 재계산 값이 파일별·묶음 모두 일치합니다. 요청받은 후보를 보고 있습니다.

### 2. 시험 실행 (직접 실행)

| 항목 | 제공된 값 | 직접 실행 |
|---|---|---|
| HS-00.03 `tests/test_hs_0003.py` | 21 passed | 21 passed in 14.45s |
| 정조준 5개 파일 | 72 passed | 72 passed in 25.93s |
| G2 gates | ruff 46, mypy 46, pytest 283 | ruff 46, mypy 46, pytest 283, rc=0 |
| 기존 착수 변이 | CHECKED 37 | CHECKED 37, 전부 PASS |
| 착수 검사 본체 | CHECKED 12 | CHECKED 12, OK(run-acceptance) |
| 원칙 검사 | CHECKED 34 PASS | CHECKED 34, VERDICT PASS |
| 원칙 변이 | CHECKED 41 PASS | CHECKED 41, VERDICT PASS |
| verify.sh 비밀 스캔 | 매치 없음 | PASS, .env not tracked |
| 원격 CI | 미제공 | NOT_RUN |

→ 제공된 수치와 직접 실행 결과가 전부 일치합니다.

### 3. 경계 우회·정상 대조군 (실제 shell 경로, 임시 fixture)

```text
[disposition PR #13１] rc=1  SPOOF: disposition-target line=1 token=PR #13 / FAIL: PR #13 처분 대상에 보호 이름 위장 있음
[disposition ｘPR #13] rc=1  SPOOF: disposition-target line=1 token=PR #13
[workflow+sot ｘhs-kickoff (] rc=1  SPOOF: workflow-step line=29 / SPOOF: sot-step line=29 / FAIL: CI·정본 스텝 이름 Unicode 위장 또는 검사 오류
[normal controls 山田太郎·محمد·Überprüfung ＡＢＣ·hｓ-kickoff-other·ＰR #131] rc=0  CHECKED: 12  OK(run-acceptance)
[coexist normal+spoof same line] rc=1  SPOOF: workflow-step line=31 token=hs-kickoff
[control: duplicate ASCII PR #13 row] rc=1  FAIL: PR #13 행이 2개 (기존 규칙이 발동, SPOOF 없음)
```
→ 세 우회는 helper 단독이 아닌 `scripts/acceptance-hs-kickoff.sh:122`(처분 대상 위장 판정 분기)와 `:181`(스텝 이름 위장 판정 분기)에서 실제로 실패합니다. 정상 대조군은 12건 모두 통과했고, 기존 ASCII 중복 규칙은 위장 규칙에 가려지지 않습니다.

helper 직접 호출 추가 탐침:

```text
PR #131 / ＰR #131 / hs-kickoff-other / hｓ-kickoff-other  → rc=0
한글 접두 착수hs-kickoff검사                                  → rc=0
U+2010 하이픈 hs‐kickoff, 수학굵은 𝐏R #13, ／task/hs-d1-permit, hs-kickoff１ → rc=1
두 번째 등장만 위장 "hs-kickoff 그리고 hѕ-kickoff"             → rc=1
hs-kickoff-mutatiοns → token=hs-kickoff-mutations 만 보고 (hs-kickoff 오인 없음)
CRLF 줄 끝, 10만 자 긴 줄                                       → rc=1 정상 탐지
PR＃13 (전각 #, 토큰 미형성) / PR #13＃                        → rc=0 (raw·비교 사본 선택 일치, 위장 아님)
결합문자·ZWSP·NBSP                                              → rc=0 (계약 제외 범위)
```
→ 지원 범위 안의 위장은 전부 잡히고 정상 이름은 통과합니다. 계약 밖 세 종류는 통과하지만 이는 문서가 선언한 대가입니다.

### 4. 입력·데이터 오류

```text
0바이트 rc=2  ERROR: 입력 이름 줄 없음
빈 이름 한 줄 rc=2 / 빈 줄 두 개 rc=2
잘못된 UTF-8 rc=2  ERROR: 입력 UTF-8 해독 실패
미지원 토큰 rc=2
같은 개수로 codepoint 하나 바꾼 JSON rc=2  ERROR: 파일 sha256 불일치
LC_ALL=C 환경: rc=2 유지 (한글 stderr는 \u 이스케이프로 출력)
공백만 "   \n" rc=0   ← 아래 결함 2
```
→ 계약의 세 오류 경로는 모두 닫힙니다. C 로케일에서도 종료값이 흔들리지 않습니다.

### 5. 고장 사본 (독립 harness, /tmp 임시 사본, 원본 미접촉)

```text
baseline                             rc=0 21 passed
shell-ignore-workflow-sot-rc         rc=1 5 failed
shell-ignore-disposition-rc1         rc=1 8 failed
shell-skip-sot-identity              rc=1 5 failed
shell-drop-disposition-token-grep    rc=1 8 failed
helper-drop-confusable-boundary      rc=1 3 failed
helper-always-allow                  rc=1 13 failed
helper-lenient-utf8                  rc=1 1 failed
helper-allow-empty                   rc=1 2 failed
helper-only-first-occurrence         rc=0 21 passed   ← 생존
```
→ 요청하신 두 종류(shell이 helper 결과 무시, 경계 치환 검사 제거)는 모두 잡힙니다. 10종 중 9종 사망, 1종 생존입니다.

### 6. Unicode 데이터·라이선스·재생성

```text
source ../hs-0002-20260910/artifacts/hs0002-20260910/hs0003-confusables-17.0.0.txt
  sha256 091c7f82…13ef22a  (# Version: 17.0.0, # Date: 2025-07-22, 05:49:37 GMT)
generate-hs-kickoff-confusables.py SOURCE → rc=0, 출력 sha256 687cd7d5…ae0cdfd  REGEN IDENTICAL (cmp)
mapping_count 선언 628 = 실제 합 628
docs/licenses/unicode-license-v3.txt sha256 e7a93b00…c53d96, 첫 줄 UNICODE LICENSE V3
```
→ 원본·생성물·개수·라이선스 지문이 모두 주장과 일치하고 생성기로 바이트 단위 재현됩니다.

### 7. 기존 기대값·의존성·한도

```text
mutations.sh diff: FILES 배열에 두 파일 경로 추가 2줄뿐, EXPECTED=37 유지
test_hs_0001.py / test_hs_0003.py: tracked, HEAD와 동일
pyproject/uv.lock/.github 변경 없음, helper import 표준 라이브러리만
줄 수: identities.py 222, generate 125, kickoff.sh 267, mutations.sh 595, test 290
함수 최장: build_mapping 20, build_document 27, append_workflow_and_sot_step 21
```
→ 37종 기대값은 바뀌지 않았고 새 의존성·CI 단계는 없습니다. 모든 파일이 hard 600, 함수는 hard 100 아래입니다.

### 8. 검증 후 상태

```text
bundle after: 0ccf996ee201ecabe4b1a66b6c00f2a04a669c5476960f8c1feca026f12b8c85
manifest after: 41aa89efa6c883a64d333d9428fea33a22a1f13f8fe1142364e58521649aead4
HEAD d1058cad…  git status --short 항목 검증 전과 동일
/tmp/hs0003-claude-v1* 제가 만든 파일 전부 삭제, 이전 세션 파일은 손대지 않음
```
→ 검증이 후보를 바꾸지 않았습니다.

### 결함 목록

**결함 1 — 심각도 낮음 (시험 공백).** 원문 제목: `helper-only-first-occurrence` 생존 변이. 원인: `humansearch/tests/test_hs_0003.py`에 정상 토큰과 위장 토큰이 **같은 줄**에 있는 사례가 없어, `scripts/verify/check-hs-kickoff-identities.py:162`(다음 등장 탐색 줄)를 `break`로 바꿔도 21개가 통과합니다. 실제 코드는 이 입력을 rc=1로 잡습니다. 사업 영향: 지금은 없음. 이후 리팩터링에서 EARS 5번(동시 존재 시 위장 거부)이 조용히 퇴행해도 시험이 알리지 못합니다.

**결함 2 — 심각도 낮음 (계약 문구 불일치).** 원문 제목: 공백만 있는 이름 한 줄. 원인: `scripts/verify/check-hs-kickoff-identities.py:197`(이름 줄 없음 판정)이 `any(lines)`로 판단해 `"   "`를 이름으로 셉니다. 실제 shell은 `awk`가 앞뒤 공백을 잘라 넘기므로 도달하지 않습니다. 사업 영향: 없음. 계약 문구 "빈 이름 한 줄"을 "빈 문자열 한 줄"로 좁혀 적거나 strip 판정으로 맞추면 됩니다.

### 설계 지적 (결함 1 보강 방향)

> **무엇을** — 같은 줄에 `hs-kickoff (정상) … hѕ-kickoff` 형태의 사례를 workflow·sot·disposition 세 kind 시험에 한 줄씩 추가합니다.
> **왜** — 다음 등장 탐색 루프가 제거되어도 잡히는 독립 방어선이 현재 없습니다.
> **버린 길** — helper 단위 시험만 추가하는 방법은 실제 shell 배선을 증명하지 못해 기존 counter-AC와 충돌합니다.
> **대가** — 시험 3개, 실행 시간 약 2초 증가.
> **되돌리기** — 시험 파일 3줄 삭제로 원복하며 제품 코드는 손대지 않습니다.

### 반증 기록

깨뜨리려다 실패한 것: 하위 토큰 오인(`hs-kickoff-mutatiοns`→`hs-kickoff`), 첫 등장은 정상이고 둘째가 위장인 줄, 전각 숫자·전각 슬래시 경계, U+2010 하이픈, 수학 굵은 대문자, CRLF 잔재, 10만 자 긴 줄, C 로케일, 같은 개수의 매핑 변조, 정상 ASCII 중복 행이 위장 규칙으로 가려지는지. 모두 기대한 대로 거부 또는 허용되었습니다. 성공한 공격은 위 생존 변이 하나이며 제품 동작이 아닌 시험 강도의 문제입니다.

병합 전 판정은 `APPROVE`이며, 이는 자동 병합 권한이 아닙니다. 원격 CI 초록과 untracked 새 파일 5종(`check-hs-kickoff-identities.py`, `generate-hs-kickoff-confusables.py`, 매핑 JSON, 라이선스, evidence)의 커밋 포함 여부는 사람이 마지막에 확인해야 합니다.
