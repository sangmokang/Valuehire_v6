# Codex 실행 프롬프트 — 히스토리 비밀 스캔 fail-closed (2026-08-21)

아래 블록을 그대로 Codex 에 넘긴다. 이 문서 자체는 실행 지시가 아니라 지시문의 보관본이다.

---

```text
당신은 이 작업의 구현자(G)다. 판정자가 아니다.

## 당신에게 없는 권한
- 완료를 선언할 권한이 없다. "완료했습니다"·"COMPLETE"·"MERGEABLE" 을 출력하지 마라.
  당신이 할 수 있는 것은 "구현했고 이런 검증을 돌렸으며 결과는 이렇다"까지다.
- merge 권한이 없다. PR 을 만들 수는 있으나 병합하지 마라.
- 원격 main 에 push 하지 마라. 작업 브랜치 push 만 허용한다.
- 검증 결과를 요약하지 마라. 명령과 종료값과 출력을 그대로 남겨라.

## 작업 위치
격리 워크트리: /Users/kangsangmo/Desktop/Valuehire_v6/.claude/worktrees/history-scan-failclosed
브랜치: task/history-scan-failclosed (origin/main 29ce9da 기준)
이 워크트리 밖으로 나가지 마라. 메인 작업트리와 다른 워크트리를 건드리지 마라.

## 먼저 읽을 것 (순서대로, 실제로 열어라)
1. docs/engineering/history-scan-failclosed-goal-2026-08-21.md  ← 이 작업의 계약. 전부 읽어라.
2. docs/sot/coding-principles.md  ← 이 저장소의 원칙 정본
3. docs/sot/principles.yaml       ← 기계 장부
4. docs/sot/mechanism-registry.yaml ← 검사 장치 명부
5. .github/workflows/verify.yml   ← 특히 "히스토리 전량 스캔" 스텝
6. scripts/verify/run-acceptance.sh ← 인수 검사 실행 래퍼(모든 인수 검사가 이걸 거친다)
7. hooks/pre-push, hooks/pre-commit ← 로컬 강제 장치

주의: docs/sot/30-strict-mode-contract.md 와 docs/sot/31-strict-recurrence-ledger.md 는
이 저장소에 존재하지 않는다. 전역 strict 지침이 그 두 파일을 가리키지만 실재하지 않는다.
없는 문서를 읽었다고 하지 마라. 이 저장소의 실제 정본은 위 2~4번이다.

## 무엇을 고치는가
.github/workflows/verify.yml 의 "히스토리 전량 스캔" 스텝이 비밀을 찾고도 통과한다.

  :61  set -o pipefail
  :94  [ "$(git cat-file -t "$sha" 2>/dev/null)" = blob ] || continue
  :96  if git cat-file blob "$sha" 2>/dev/null | grep -qEif "$CLEAN"; then

grep -q 가 매치를 찾자마자 종료하면 git cat-file 이 SIGPIPE 로 죽고, pipefail 이 그 실패를
파이프라인 전체 실패로 만들어 if 조건이 거짓이 된다. 즉 "찾았다"가 "못 찾았다"로 뒤집힌다.
20MB blob 첫 줄에 합성 자격증명을 넣어 재현했다(rc=141, 미탐지).

주의: 파이프를 유지한 채 `grep -Eif ... >/dev/null` 로만 바꾸는 수정안은 BSD grep 에서는
고쳐지지만 ugrep 에서는 여전히 rc=141 이었다. 실측으로 확인했다. 파이프 자체를 없애라.

## 해야 할 일 (goal 의 WU 표를 따른다. 각 WU 는 독립 커밋)

WU-1. 히스토리 스캔 본문을 scripts/scan-history-secrets.sh 로 추출한다.
      - 파이프를 쓰지 않는다. blob 을 임시 파일로 받아 grep 에 파일로 넘긴다.
      - 종료값을 3분기한다: 0=위반 발견, 1=정상(위반 0건), 2=검사기 오류/스캔 무효
        (호출부에서 어떻게 매핑할지는 당신이 정하되, 세 상태가 반드시 구분돼야 한다)
      - git cat-file -t 실패, git cat-file blob 실패, grep 종료값 2 이상, 유효 패턴 0개,
        도달 객체 2개 미만, blob 0개 — 전부 "스캔 무효"로 실패시킨다. continue 로 넘기지 마라.
      - 바이너리는 grep -a 로 텍스트 취급한다. 크기로 건너뛰지 마라.

WU-2. scripts/acceptance-history-scan-failclosed.sh 를 만든다.
      - mktemp 아래 합성 저장소를 만들어 검사한다. 실제 비밀값을 쓰지 마라. 합성값만 쓴다.
      - 차단과 통과를 한 쌍으로 재라:
        차단 — 큰 blob(20MB 이상) 첫 줄 매치 / 작은 blob 매치 / 깨진 정규식 /
               읽을 수 없는 객체 / 유효 패턴 0개 / 도달 객체 부족
        통과 — 깨끗한 합성 저장소는 종료값 정상
      - CHECKED: N 을 출력하고 N 은 8 이상이어야 한다. VERDICT: PASS|FAIL 을 마지막에 낸다.
      - 시작·종료 시 원본 저장소의 git status --porcelain 이 같은지 확인하고 그 결과도 세라.

WU-3. 배선한다.
      - .github/workflows/verify.yml 의 인라인 스캔 스텝을 스크립트 호출로 바꾼다.
      - 새 인수 검사를 래퍼 경유로 추가한다:
        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-history-scan-failclosed.sh
      - docs/sot/mechanism-registry.yaml 에 등록한다(기존 항목 형식을 그대로 따를 것).
      - hooks/pre-push 는 acceptance-*.sh 를 글로브로 전량 실행하므로 별도 배선이 필요 없다.
        다만 새 검사가 pre-push 에서 돌아도 문제가 없는지 확인하라.

WU-4. PR #29 의 개선분 중 깨끗하게 적용되는 것을 가져온다.
      - task/gate0-reachable-large-blob-sigpipe 브랜치의
        scripts/acceptance-0-2-unreachable-content.sh 와 scripts/acceptance-0-2.sh 변경분.
      - 확인된 사실: 이 두 파일은 현재 main 에 충돌 없이 적용된다.
        .github/workflows/verify.yml 과 docs/sot/verification-commands.md 는 충돌한다 —
        그 두 개는 이식하지 말고 WU-1~3 의 결과로 대체하라.

## 반드시 지킬 순서 (건너뛰면 이 작업은 무효다)
1. WU-2 의 인수 검사를 **먼저** 만들고, 현재 main 코드에서 **실패하는 것을 보여라**(RED).
   실패 이유가 "빠진 동작" 때문이어야 한다. 문법 오류나 파일 없음으로 실패하면 RED 가 아니다.
   RED 를 커밋한 뒤에 구현을 시작하라.
2. 그 다음 WU-1 을 구현해 RED → GREEN.
3. 그 다음 WU-3 배선, WU-4 이식.
4. 매 단계 후 기존 인수 검사가 깨지지 않았는지 확인하라.

## 이 저장소의 함정 (모르면 반드시 막힌다)
- pre-commit 이 diff 에서 검사 약화 패턴을 탐지한다. mutation 을 주입하는 테스트 코드가
  `|| true`, `continue-on-error: true`, `if: always()` 같은 문자열을 소스에 그대로 담으면
  커밋이 차단된다. 저장소 선례대로 문자열을 조립해서 써라(.check-weakening-patterns 주석 참조).
  suppressions.yaml 에 등록하지 마라 — 유예는 구멍을 승인하는 것이다.
- 워크플로 스텝에 if 나 continue-on-error 를 붙이면 scripts/verify/check-ci-step-integrity.sh
  가 차단한다. 붙이지 마라.
- 인수 검사는 종료값 0 으로 끝나면 판정 출력을 최소 한 줄 남겨야 한다(run-acceptance.sh 계약).
- 파괴적 실증은 mktemp 아래에서만 하고 git 환경변수를 unset 하라. 끝나면 원본 저장소의
  git status --porcelain 이 시작과 같은지 확인하라.
- branch protection·CODEOWNERS 는 이 계정에서 HTTP 403 이다. 제안하지 마라.

## 검증 (전부 실제로 돌리고 출력을 그대로 남겨라)
  bash verify.sh
  bash scripts/scan-history-secrets.sh
  bash scripts/verify/run-acceptance.sh scripts/acceptance-history-scan-failclosed.sh
  bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh
  bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh
  bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh
  bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh
  bash scripts/verify/check-ci-step-integrity.sh

각 명령의 종료값을 적어라. 하나라도 실패하면 그 상태로 멈추고 보고하라.
"대체 명령으로 확인했다"는 원명령 통과가 아니다.

## 비범위 (건드리지 마라)
- verify.sh / scan-data-exposure.sh / acceptance-0-6.sh 의 목록 생산자 실패 결함
- 인수 검사 성공문구 위조 차단
- CI 계약 검사기 확장(on: 트리거·주석 처리·|| true·예외 이름 도용)
- git cat-file --batch 성능 최적화
이것들은 별도 작업으로 이미 분리돼 있다. 범위를 넓히지 마라.

## 출력 형식 — 반드시 지킬 것
첫 줄은 STATUS: IMPLEMENTED|BLOCKED|NOT_RUN.
그다음 결론 → 판단 근거 → 기술 상세와 증거 원문 순서로 쓴다.
결론에는 전문용어를 쓰지 않는다. 판단 근거에는 선택·버린 길·틀리면 깨지는 것을 쓴다.
전문용어는 첫 등장 문장 안에서 풀고, 출력·코드·표 바로 아래에는 → 해석을 붙인다.
file:line 에는 그 줄의 역할을 붙인다.
설계 결정은 무엇을/왜/버린 길/대가/되돌리기 다섯 줄로 쓴다.
건너뜀·미확인·실패 후 재시도와 추정을 앞부분에 밝힌다.
RED 가 실제로 실패한 출력과 GREEN 으로 바뀐 출력을 둘 다 남겨라.
한국어 존칭체로 쓰되 내용을 축소하거나 초등학생 비유를 쓰지 마라.

다시 말한다: 당신은 완료를 선언할 권한이 없다. 구현하고 검증을 돌리고 결과를 보고하라.
합격 여부는 별도 판정자가 정한다.
```

---

## 이 프롬프트를 쓴 뒤 할 일 (Claude 몫)

1. Codex 결과를 받아 **V1 판정**을 Claude 가 수행한다 — 증거를 격리 환경에서 재현한다.
2. 재현되지 않는 주장은 무효로 처리한다.
3. V1 이 FAIL 이면 최종 PASS 를 만들지 않고 V2 를 실제로 실행한다.
4. 판정 원문·명령·종료값·세션 식별자를 goal 의 `## 적대 검증 로그` 에 그대로 append 한다.
5. PR 생성 후 원격 CI 초록을 `scripts/verify/check-verified-sha.sh` 로 확인한다.
   세 SHA 가 일치하고 결론이 success 일 때만 READY TO MERGE 로 보고한다.
6. **merge 는 사장님께 남긴다.**
