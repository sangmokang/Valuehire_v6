VERDICT: PASS

## 결론

후보는 계약이 약속한 대로 동작합니다. 보호 이름을 전각 문자나 Unicode 동형 문자로 바꿔 넣은 입력은 실제 착수 검사 경로에서 거부되고, 정상 한글·일본어·아랍어·라틴 이름과 보호 이름 밖의 전각 문장은 그대로 통과합니다. 원문은 바꾸지 않고 탐지용 비교 사본만 씁니다. 매핑 데이터가 없거나 손상되면 검사가 실패로 닫힙니다. 기존 시험과 37종 변이 기대값은 바뀌지 않았습니다.

다만 계약 범위 밖의 잔여 위험 하나를 실험으로 확인했습니다. 보호 이름 바로 뒤에 붙는 경계 문자를 전각 숫자로 바꾸면(예: PR #13 뒤에 전각 숫자 1을 붙인 이름), 사람은 "PR #131"로 읽지만 기존 ASCII 선택은 이를 "PR #13"의 처분 행으로 인정합니다. 이는 이번 작업 단위가 고치기로 약속한 실패 유형(위장 통과·정상 차단)이 아니라 세 번째 유형(다른 이름을 보호 이름으로 오인)이며, 후보가 새로 만든 결함이 아니라 기존 검사가 원래 갖던 약점입니다. 병합을 막을 사유로 보지 않지만 후속 작업 단위로 남겨야 합니다.

## 판단 근거

**건너뜀·미확인·추정을 먼저 밝힙니다.**

- 묶음 지문 `07ce9970…`은 재현하지 못했습니다(`NOT_REPRODUCED`). 계산 방식이 요청서에 없어 13개 파일 결합·정렬·해시 여섯 가지 조합을 시도했지만 모두 달랐습니다. 대신 파일별 SHA-256을 아래 증거에 남겨 커밋 후 대조에 쓸 수 있게 했습니다.
- 파일·함수 한도 hard600/hard100 검사기는 저장소에서 찾지 못했습니다. `docs/sot/principles.yaml` P11 항목은 `mechanism_found`에 문서와 원칙 검사 스크립트만 두고 "제품 장치의 구현 완료를 주장하지 않는다"고 명시합니다. 구현 세션이 말한 "600 통과·601 실패·대상 0개 실패"는 어떤 검사기를 썼는지 확인할 수 없어 `NOT_VERIFIED`입니다. 저는 Python `ast`와 줄 수를 직접 세어 한도 자체는 확인했습니다.
- 원칙 검사(CHECKED 34)·원칙 변이(CHECKED 41)·저장소 비밀 패턴 검사는 재실행하지 않았습니다(`NOT_RUN`). 요청서가 장시간 전체 회귀 반복을 필수에서 제외했고 이 후보의 변경 파일과 무관하기 때문입니다. 대신 HumanSearch 전체 pytest·ruff·mypy와 37종 변이는 직접 재실행했습니다.
- 공식 Unicode 원본과 라이선스는 unicode.org에서 임시 디렉터리로 내려받아 대조했습니다. 이는 읽기 전용 네트워크 접근이며 저장소나 외부 서비스에 쓴 것은 없습니다.

**선택한 해석.** "위장 거부"는 계약의 EARS 1~3 그대로, 즉 비교 사본에서 경계를 지킨 보호 토큰 span 안에 치환이 있을 때로 읽었습니다. 경계 자리 자체가 치환된 경우는 계약이 "비ASCII 접두·접미는 토큰 경계를 침범하지 않는다"고 정한 바깥 영역이므로 FAIL 사유가 아니라 잔여 위험으로 분류했습니다.

**버린 해석.** 경계 자리 동형 문자를 이번 판정의 실패로 보는 해석은 버렸습니다. 그렇게 보면 계약이 명시한 counter-AC 아홉 항목 어디에도 없는 요구를 소급 적용하게 되고, 기존 검사가 원래 갖던 약점을 이번 후보의 회귀로 오인하게 됩니다.

**틀리면 깨지는 것.** 제 판정은 "처분표·워크플로·정본 세 입력 칸이 helper에 실제 전달된다"는 추적 결과, 13종 고장 사본 중 12종이 시험에 잡힌 결과, 재생성 JSON이 바이트 단위로 같다는 결과에 기대고 있습니다. 이 셋 중 하나라도 제가 잘못 실행했다면 PASS는 무효입니다. 각 명령과 출력을 아래에 그대로 둡니다.

## 기술 상세와 증거

### 1. 작업트리 상태와 포함 대상

```text
HEAD 396cd2b7e92f755d65c34cf103d07b8741259cfc
 M docs/sot/verification-commands.md
 M scripts/acceptance-hs-kickoff-mutations.sh
 M scripts/acceptance-hs-kickoff.sh
?? docs/engineering/evidence/hs0003-20260910/   (claude-v1-prompt.md 1개)
?? docs/licenses/unicode-license-v3.txt
?? scripts/verify/check-hs-kickoff-identities.py
?? scripts/verify/generate-hs-kickoff-confusables.py
?? scripts/verify/hs-kickoff-confusables-17.0.0.json
git diff --check → exit 0
git check-ignore -v (새 파일 5개) → exit 1
diff --stat: 3 files changed, 51 insertions(+), 1 deletion(-)
```
→ HEAD가 요청서의 RED 커밋과 같고, 공백 오류가 없으며, 새 파일 5개는 어느 gitignore 규칙에도 걸리지 않아 최종 커밋에 들어갈 수 있습니다. 검증 후 다시 확인한 상태도 동일하여 제가 작업트리를 바꾸지 않았음을 확인했습니다.

### 2. 정조준 시험과 회귀 직접 재실행

| 명령 | 결과 |
|---|---|
| `uv run --no-sync pytest -q tests/test_hs_0003.py` | 15 passed in 12.28s |
| `uv run --no-sync pytest -q` (전체) | 277 passed in 36.03s |
| `uv run --no-sync ruff check .` | All checks passed! |
| `uv run --no-sync mypy .` | Success: no issues found in 46 source files |
| `bash scripts/acceptance-hs-kickoff-mutations.sh` | CHECKED: 37, exit 0 (50초) |
| `bash scripts/acceptance-hs-kickoff.sh` (실제 작업트리) | PASS 12건, CHECKED: 12, exit 0 |

→ 구현 세션이 주장한 정조준·G2·37종 변이 결과가 제 실행에서도 같은 숫자로 재현됐습니다. 정조준 66개 주장은 HS-0001/0002 시험을 포함한 수치이며 전체 277개 안에 들어 있으므로 별도로 다시 세지 않았습니다.

### 3. 실제 호출 경로에서 세 입력 칸이 검사되는가(관점 1)

`bash -x scripts/acceptance-hs-kickoff.sh` 추적에서 helper 호출 3건을 확인했습니다.

```text
python3 scripts/verify/check-hs-kickoff-identities.py --kind disposition-target --token 'PR #13' --token 'PR #54' --token 'PR #15' --token task/hs-d1-permit --token task/hs-l1-malformed-url-fix --token task/hs-observe-url-crash
python3 scripts/verify/check-hs-kickoff-identities.py --kind workflow-step --token hs-kickoff --token hs-kickoff-mutations
python3 scripts/verify/check-hs-kickoff-identities.py --kind sot-step --token hs-kickoff --token hs-kickoff-mutations
```
→ 처분표 대상 칸, 워크플로 스텝 이름, 정본 스텝 이름 칸이 각각 helper에 전달됩니다.

- `scripts/acceptance-hs-kickoff.sh:78-85` — 처분표 칸을 파싱한 직후, 기존 ASCII 행 선택(87행) 전에 helper를 호출하고 결과 코드를 보관하는 줄입니다.
- `scripts/acceptance-hs-kickoff.sh:122-126` — 대상별 판정에서 helper 오류(rc>1)와 위장(rc=1이고 `token=$t` 출력)을 "행 없음"보다 먼저 실패로 세는 줄입니다. 기존 ASCII 선택보다 앞선 순서가 맞습니다.
- `scripts/acceptance-hs-kickoff.sh:162-176` — 워크플로 파싱 결과에서 이름 열만 뽑아 helper에 넘기고, 정본 표의 이름 칸을 기존과 같은 `^\| [0-9]+ \|` 선택으로 뽑아 helper에 넘기는 줄입니다.
- `scripts/acceptance-hs-kickoff.sh:181-182` — 항목 7에서 위장·오류를 1:1 대조보다 먼저 실패로 세는 줄입니다.
- `scripts/acceptance-hs-kickoff.sh:71` — 표 머리글 "대상"과 구분선 행을 제외하는 새 줄입니다. 이 덕분에 helper의 `line=N`이 표의 N번째 실제 행과 같아집니다(시험이 `line=7`을 기대).
- `scripts/verify/check-hs-kickoff-identities.py:115-129` — 원문을 바꾸지 않고 전각(0xFEE0 차감)과 고정 매핑으로 비교 사본과 치환 위치 표를 만드는 함수입니다.
- `scripts/verify/check-hs-kickoff-identities.py:138-149` — 비교 사본에서 토큰을 찾고, 경계를 지키며 span 안에 치환이 있을 때만 거부하는 함수입니다. 같은 줄에 정상 이름이 먼저 있어도 다음 위치를 계속 찾으므로 동시 존재를 면제 사유로 쓰지 않습니다.

### 4. 고장 사본이 시험에 잡히는가(관점 2)

작업트리를 `/tmp`에 복사한 뒤 사본마다 한 곳씩 바꾸고 원본 가상환경으로 `test_hs_0003.py`를 실행했습니다. 원본은 건드리지 않았습니다.

```text
M0-baseline                  | 15 passed
M1-always-allow              | 10 failed, 5 passed
M2-always-reject             | 1 failed, 14 passed
M3-no-fullwidth              | 5 failed, 10 passed
M4-no-confusables            | 5 failed, 10 passed
M5-no-boundary               | 1 failed, 14 passed
M6-ignore-changed            | 1 failed, 14 passed
M7-shell-steps-rc0           | 4 failed, 11 passed
M8-shell-disp-rc0            | 6 failed, 9 passed
M9-shell-step-branch         | 4 failed, 11 passed
M10-sha-bypass               | 1 failed, 14 passed
M11-no-sot-input             | 4 failed, 11 passed
M12-only-first-token         | 6 failed, 9 passed
M13-metadata-skip            | 15 passed  ← 생존
```
→ 요청서가 지목한 일곱 유형(항상 허용, 항상 거부, 전각 삭제, 동형 삭제, 경계 삭제, shell이 helper 결과 무시, SHA 우회)은 모두 최소 1개 시험에 잡혔습니다. 정본 입력 누락(M11), 토큰 하나만 검사(M12), 치환 위치 무시(M6)도 잡혔습니다.

M13 생존은 결함이 아닙니다. `check-hs-kickoff-identities.py:61-63`의 SHA 검사가 메타데이터 검사(76행)보다 먼저 실행되므로, 파일이 조금이라도 다르면 메타데이터 비교에 도달하기 전에 실패합니다. 메타데이터·개수·target 계약 검사는 SHA가 같을 때만 실행되는 방어 심층 코드이며 시험으로 단독 증명되지는 않습니다. 심각도 낮음, 사업 영향 없음, 기록만 남깁니다.

### 5. 정상·위장·경계 직접 판정(관점 3)

helper를 직접 호출한 결과입니다. `rc=0`은 허용, `rc=1`은 거부, `rc=2`는 오류입니다.

```text
rc=0 | 정상 한글 山田太郎 · محمد · hs-kickoff 설명 · hｓ-kickoff-other · Überprüfung ＡＢＣ
rc=0 | PR #131        rc=0 | ＰR #131       rc=0 | hs-kickoff-other      rc=0 | hｓ-kickoff-other
rc=0 | 한글hs-kickoff한글   rc=0 | ＡＢＣ ｄｅｆ 전각 설명만   rc=0 | ｈｓ－ｋｉｃｋｏｆｆ－ｏｔｈｅｒ
rc=1 | hs-kickoff · hѕ-kickoff 동시                    → token=hs-kickoff
rc=1 | ｈｓ－ｋｉｃｋｏｆｆ                               → token=hs-kickoff
rc=1 | hs‐kickoff (U+2010)                              → token=hs-kickoff
rc=1 | hs-kickoff-mutatiοns / hѕ-kickoff-mutations      → token=hs-kickoff-mutations
rc=1 | hs-kickoff (real) · hs-kickoff-mutations (real) · hs-kіckoff (spoof) → token=hs-kickoff
rc=1 | ＰＲ ＃１３ / РR #13 / task／hs-d1-permit / tаsk/hs-d1-permit / 한글 PR #13 · PＲ #54
rc=2 | --token 'PR #131'  → ERROR: 지원하지 않는 보호 토큰
rc=2 | 표준입력 0바이트    → ERROR: 입력 줄 없음
```
→ 정상 다국어·무관한 전각·동시 존재·`PR #131`·`hs-kickoff-other`가 모두 허용되고, 전각·키릴·그리스·유니코드 하이픈·슬래시 위장이 모두 거부됩니다.

같은 mapping count를 유지한 내용 변조는 시험 `same-count-content`가 잡습니다. 다만 잡는 주체는 개수 검사가 아니라 SHA 검사입니다(위 M10에서 SHA를 우회하면 이 시험이 실패하는 것으로 확인). 계약 EARS 6의 "실패로 닫는다"는 충족됩니다.

### 6. Unicode 원본·생성물·라이선스·재생성 대조(관점 4)

```text
공식 다운로드 confusables.txt  sha256 091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a
HS-00.02 준비 사본            sha256 091c7f82…(동일)   헤더 Version 17.0.0 / Date 2025-07-22, 05:49:37 GMT
생성기 재실행 결과             sha256 687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd
커밋 후보 JSON                 sha256 687cd7d5…(동일)   cmp → REGEN IDENTICAL
매핑 통계: total 628, 선언 628, target 26개, source 중복 0, ASCII source 0, 전각 source 0
공식 license.txt vs docs/licenses/unicode-license-v3.txt → LICENSE IDENTICAL (39줄)
```
→ 원본 지문, 생성물 지문, 선택 수 628, 라이선스 본문이 모두 요청서와 일치하고 재생성이 바이트 단위로 같습니다. 보호 ASCII 집합 중 `#`, `1`, `m`은 단일문자 매핑이 없어 전각 대응으로만 보호됩니다. 이는 Unicode 17.0.0 데이터의 실제 내용이며 결함이 아닙니다.

### 7. 기존 변이 기대값·한도·의존성(관점 5·6)

- `scripts/acceptance-hs-kickoff-mutations.sh` 변경은 FILES 배열에 새 파일 2개를 추가한 2줄뿐입니다(92~93행). 이 배열은 HEAD 워크트리 위에 현재 작업트리 파일을 덮어쓰는 목록이므로, 커밋 전 helper와 JSON이 변이 시험대에 들어가야 37종이 성립합니다. 실제 CHECKED 37로 확인했습니다. 기대 문자열은 바뀌지 않았습니다(diff 참조).
- 새 helper와 생성기는 표준 라이브러리만 씁니다(argparse, hashlib, json, re, sys, dataclasses, pathlib, typing). 새 의존성 0, 새 CI 스텝 0입니다. `verify.yml:273-287`의 기존 두 스텝이 그대로 호출합니다.
- 파일 길이: check 190, generate 125, test_hs_0003 212, JSON 44, acceptance 267, mutations 595. 함수 최장: `build_mapping` 20, `build_document` 27, `append_workflow_and_sot_step` 21, shell 함수 최장 20. 모두 hard600/hard100 안입니다. 변이 스크립트 595줄은 hard 600에 5줄 남은 상태이니 다음 작업 단위에서 주의가 필요합니다.

### 8. 파일별 SHA-256(커밋 후 대조용)

```text
53e0f1e0610c3446a5062b4770ffdb4e1cac1b5c0cfc4af525167e16b6f0c22a  scripts/acceptance-hs-kickoff.sh
09fc5e28c650f4968c77e95dc72d3bd4126d92caa6c483210e30f2bb0674696e  scripts/acceptance-hs-kickoff-mutations.sh
337a598116943ca353f5f81c10a5269cc2bd083821d287b964e182c8a624712d  scripts/verify/check-hs-kickoff-identities.py
7694d91b0af2c7d6ee1e791474a393b8e7a14d9b27542e06315009e6d0f0449d  scripts/verify/generate-hs-kickoff-confusables.py
687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd  scripts/verify/hs-kickoff-confusables-17.0.0.json
e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96  docs/licenses/unicode-license-v3.txt
14998dea0d52845931f3e69c647608a73f99554147bb7a80bc0f66df5f7734c4  humansearch/tests/test_hs_0003.py
08d9adeb9f63ee2aae332229266ca38ca8924eab8b596add0eac406dc99d7a8f  docs/sot/verification-commands.md
```
→ 제가 검증한 후보의 정확한 내용입니다. 커밋 뒤 이 값과 다르면 검증되지 않은 후보입니다.

### 9. 결함과 잔여 위험

**결함 1 — 심각도 중간(계약 밖 잔여 위험) — 경계 자리 동형 문자로 다른 이름이 보호 이름으로 오인됨**
- 원인: `scripts/acceptance-hs-kickoff.sh:87-88`의 기존 ASCII 행 선택은 비ASCII 문자를 모두 토큰 경계로 취급합니다. 반면 helper는 비교 사본에서 경계를 판정하므로 `PR #13１`(전각 1)은 사본 `PR #131`이 되어 토큰이 아니라고 봅니다. 두 판단이 어긋나 helper는 허용하고 raw 선택은 PR #13 행으로 인정합니다.
- 재현: 사본에서 처분표 1행의 `PR #13`을 `PR #13１`로 바꾸고 acceptance 실행 → `PASS: 처분 PR #13 → 결론=재작성 (근거 경로 1 건·커밋 0 건)`, CHECKED 12, exit 0.
- 사업 영향: 처분표에 사람이 "PR #131"로 읽는 행을 두고도 검사는 PR #13의 처분이 끝났다고 인정합니다. 워크플로·정본 경로는 1:1 대조와 `hs-kickoff (` 접두 일치가 있어 같은 수법이 통하지 않았고, 처분표 경로만 해당합니다. 후보가 새로 만든 문제가 아니라 기준 HEAD에도 있던 약점입니다.
- 설계 지적:
  > **무엇을** — helper가 "경계 자리에 치환이 있어 토큰이 깨진 span"도 별도 코드로 보고하고, shell의 raw 선택이 그 줄을 보호 행에서 제외하거나 실패로 세도록 한다.
  > **왜** — 위장을 거부하는 방향과 다른 이름을 보호 이름으로 오인하지 않는 방향을 같은 비교 사본으로 일관되게 판정하기 위해서다.
  > **버린 길** — raw 선택 정규식을 비교 사본 위에서 돌리는 방법은 "원문은 승인 값으로 쓰지 않는다"는 계약을 어긴다.
  > **대가** — 새 시험 1~2개와 shell 분기 1개가 늘고, 한글 접미가 붙은 정상 이름 처리 규칙을 다시 명시해야 한다.
  > **되돌리기** — 이번 후보와 무관한 후속 작업 단위이므로 그 단위의 GREEN 커밋만 revert하면 된다.

**결함 2 — 심각도 낮음 — 빈 줄 하나만 있는 입력이 오류가 아니라 정상으로 끝남**
- 원인: `check-hs-kickoff-identities.py:178-180`은 줄 목록이 비었을 때만 오류로 봅니다. shell의 herestring은 빈 값에도 개행 하나를 보내므로 `lines=[""]`가 되어 rc=0입니다. 계약의 "실제 이름 줄이 0개면 종료값 2"와 어긋납니다.
- 사업 영향: 처분표에 유효 행이 하나도 없으면 helper는 침묵하지만, 바로 뒤 "행 없음" 판정이 6건 모두 실패시키므로 통과로 새지 않습니다. 기록만 남깁니다.

**결함 3 — 심각도 낮음 — 잘못된 UTF-8 바이트가 오류가 아니라 정상으로 끝남**
- 원인: 표준입력을 텍스트 모드로 읽어 환경에 따라 대체 문자로 해독되며 `hs-kickoff\xff`가 rc=0이었습니다. 계약은 읽기 오류를 종료값 2로 정합니다.
- 사업 영향: 깨진 바이트로 보호 토큰을 만들 수는 없어 위장 통과는 아닙니다. 기록만 남깁니다.

### 10. 반증 기록(깨려다 실패한 것)

- 정상 이름 뒤에 한글 접미(`한글hs-kickoff한글`)를 붙여 경계 판정을 흔들려 했으나 계약대로 허용됐습니다.
- `ｘhs-kickoff`처럼 전각 접두를 붙여 비교 사본에서 경계를 없애 오탐을 유도했으나, 비교 사본 기준 경계 규칙으로 허용됐습니다.
- 정상 `hs-kickoff`와 `hs-kickoff-mutations`를 먼저 두고 세 번째에 위장을 숨겨 "동시 존재 면제"를 유도했으나 거부됐습니다.
- `hѕ-kickoff-mutations`로 짧은 토큰 `hs-kickoff`만 잡히고 긴 토큰이 빠지는지 시도했으나 긴 토큰으로 거부됐습니다.
- 지원 범위 밖으로 선언된 ZWSP(`hs-kick​off`), ZWNJ 접미, ASCII `rn`은 예상대로 허용됐습니다. 계약이 제외한 항목이므로 결함으로 세지 않았습니다.
- 매핑 JSON 내용을 바꾸면서 개수를 유지하는 변조는 SHA 검사에 잡혔고, SHA 우회 사본(M10)까지 시험이 잡았습니다.
