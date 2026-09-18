# HS-03.02 사전검사기 — 다음 실행 프롬프트 v2 (2026-09-18, /clear 뒤 그대로 붙여넣기)

## 결론

v1 프롬프트의 1단계(V2)가 끝났고 결과는 실패다: 검사기의 방어 조건을 하나씩 지운 변이 84개 중 60개가 인수 시험을 그대로 통과했다(진짜 구멍 58). 그 뒤 ChatGPT 가 제안한 "구멍 58개를 안전 규칙 몇 개로 묶어 적은 시험으로 막자" 는 처방은 세 독립 검토(Codex·codeaudit·humanreview 실측)에서 전부 기각됐다 — 규칙 수준 시나리오 8개로 잡힌 것은 8건뿐이고, 검사기의 "조건 여섯 개 전부 참" 식 결합 때문에 조건마다 시나리오가 따로 필요하다. 세 검토가 공통으로 가리키는 첫 작업은 둘이다. ① 인수 시험이 잘못된 검사기 앞에서 스스로 멈추게 만들기(지금은 영구 대기). ② 인수 시험이 "어느 검사가 무슨 판정으로 막았는지" 를 묻게 만들기(반례 27건 중 23건이 안 묻는다). 그 다음 방향은 사장님 결정이다: (가) 검사기 자체를 줄인다 — 세 검토 중 둘의 권고 · (나) 결합 조건을 조건별 판정 줄로 쪼갠다 · (다) 높음 등급 26~34건만 기존 파일에 봉인한다(572줄, 한도 안). 배송은 기준 브랜치가 원격보다 51커밋 앞서 있어 별도 결정 없이는 열지 않는다.

## 배경(확인된 사실)

- 묶음 A `task/hs-0302-r6-survivor-defenses-20260916`(6df142c), 묶음 B `task/hs0302-preflight-followup-20260917`(e36770d, 기준 A). 둘 다 미푸시. 0단계 사전검사기는 두 묶음 모두 11/11 PASS(2026-09-17 20:32).
- 증거 장부(gitignored): `private-reviews/hs-0302/claude-preflight-followup-e36770d-2026-09-17/README.md`. V2 산출물 `../v2-mutations-e36770d.tsv`(84행)·`v2-verdict-e36770d.md`(§7 생존 58건 반례 초안)·`logs/v2-mut/<ID>.diff`. 3중 검토: `adversarial-20260918/codex-adversarial-verdict-e36770d.md`, `codeaudit-chatgpt-review-20260918.md`, `humanreview-invariants-20260918.md`(+매트릭스 tsv 464행).
- 인수 시험 `scripts/acceptance-hs0302-preflight.sh` 402줄 / 검사기 `scripts/verify/hs0302-closeout-preflight.sh` 408줄 / P11 hard 600줄. 인수 시험에 timeout·alarm·ulimit 0건. run_case(:224-249) 호출 27건 중 검사 이름 인자가 빈 것 23건.
- 기준 브랜치 `task/hs-0302-candidate-identity-20260914` 로컬 4650886 은 원격 69648d4 보다 51커밋 앞선다. 억제 2건은 2026-09-15 만료.

## 프롬프트 본문

```text
$strict
대상: 묶음 B `task/hs0302-preflight-followup-20260917`(워크트리 worktrees/hs0302-preflight-followup-20260917, HEAD e36770d, 기준 A 6df142c). 증거 장부와 3중 검토 산출물은 private-reviews/hs-0302/claude-preflight-followup-e36770d-2026-09-17/ 아래 — 먼저 README 의 적대 검증 로그와 09-18 3중 검토 표를 읽고, 거기 없는 결과를 지어내지 않는다. 새 checker·ledger·reason-code·contract 계층을 만들지 않는다. 새 CI 스텝·새 acceptance 파일을 만들지 않는다(결정 (가)에서 파일 분할이 불가피하면 멈추고 보고). 인수 시험·검사기 모두 P11 hard 600줄 이내. 무거운 실행(인수 시험 30초·uv sync·codex)은 하나씩 직렬 — 이 기계는 동시 실행 시 메모리 킬이 난다. grep 은 /usr/bin/grep 절대경로, timeout 은 perl -e 'alarm shift; exec @ARGV' N. 사장님 결정 줄이 이 블록 뒤에 없으면 0단계·WU-1·WU-2 까지만 하고 멈춘다.

0단계(착수 자격): (a) 워크트리 B 에서 `bash scripts/verify/hs0302-closeout-preflight.sh --branch task/hs0302-preflight-followup-20260917 --base task/hs-0302-r6-survivor-defenses-20260916` → 마지막 두 줄 `CHECKED: N`·`VERDICT: PASS` 아니면 그 판정 그대로 보고하고 멈춘다. (b) `git fetch origin` 뒤 `git rev-parse task/hs-0302-candidate-identity-20260914 origin/task/hs-0302-candidate-identity-20260914` 두 값과 `git rev-list --count origin/task/hs-0302-candidate-identity-20260914..task/hs-0302-candidate-identity-20260914` 를 보고에 그대로 적는다(배송 결정 ③의 입력). (c) `bash scripts/acceptance-principles-check.sh` CHECKED 34. (d) 정상 기준선 `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs0302-preflight.sh` rc 0·CHECKED 44 — 이 숫자가 뒤 단계의 양성 대조군이다.

WU-1(인수 시험 자기 보호 — 결정 무관, 반드시): scripts/acceptance-hs0302-preflight.sh 의 run_case 와 반례18 실행부에 케이스별 제한시간(perl alarm, 120초)·전체 제한시간(600초)·프로세스 상한(ulimit -u, 현재 사용량 + 여유로 산정해 근거를 주석에)·프로세스 그룹 정리를 넣고, 제한 초과는 `FAIL: <반례명> — TIMEOUT` 줄과 rc 1 로 끝나게 한다. RED 먼저: 원본 밖 --no-local 클론에 logs/v2-mut/M25.diff(정지 표식 제거 → 행)와 M37.diff(재귀 깊이 완화 → 프로세스 폭주)를 적용한 사본으로 인수 시험을 돌려 현재는 멈추지 않음을 기록(외부 alarm 200 으로 감싸 rc 142 확인)한 뒤 구현. AC(전부 명령·기대값): ① M25 사본 → 인수 시험이 150초 이내 종료, rc 1, 출력에 `TIMEOUT` 포함, 마지막 줄 `VERDICT: FAIL`, 잔여 프로세스 0(`ps -axo pid,command | /usr/bin/grep -F <클론경로> | /usr/bin/grep -v grep | wc -l` = 0). ② M37 사본 → rc 1·FAIL, 실행 중 최대 프로세스 수가 상한 이하(표본기로 5초마다 `ps -axo pid= | wc -l` 기록). ③ 정상 사본 → rc 0·CHECKED 44·VERDICT PASS 유지, 소요 시간 기준선 대비 +10초 이내. ④ `bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh` 와 `bash scripts/acceptance-principles-check.sh` PASS 유지. 파일 줄수 ≤ 600.

WU-2(누가 막았는지 묻기 — 결정 무관, 반드시): run_case 에 "기대 검사 이름:판정" 인자(예: `BLOCKED:git.clean`, `FAIL:ac2.copy`)를 추가하고, 그 이름의 줄이 정확히 그 판정으로 출력에 있어야 통과로 친다. 빈 값 23건을 전부 채운다(각 반례가 겨눈 방어 이름은 인수 시험 머리글 주석과 V2 TSV caught_by 열로 확정). RED 먼저: codeaudit 가 지목한 반례 — bin-badgit(모든 git rc 128) 아래에서 M01.diff(git.clean 의 blocked→fail) 사본이 현재 초록임을 기록. AC: ① M01 사본 → 인수 시험 FAIL(rc 1), FAIL 줄에 반례2 포함. ② 반례25(하드링크 복제)에 `FAIL:ac2.copy` 를 요구했을 때 M52.diff(hardlink 검사 제거) 사본이 FAIL 로 잡히는지 — 잡히지 않으면 "엉뚱한 이유로 잡힘" 을 그대로 보고하고 반례25 의 대역을 hardlink 만 어기도록 고친다. ③ 정상 사본 rc 0·CHECKED 44 유지. ④ V2 생존 58건 전부에 대해 WU-1·WU-2 만 적용된 인수 시험을 다시 돌려(원본 밖 클론, 직렬, 58×30초) `private-reviews/hs-0302/v2-mutations-<새 SHA 7자>.tsv` 를 새로 쓴다. 이 잡힘 수는 목표가 아니라 보고값이다 — 부풀리지 않는다.

WU-3(사장님 결정에 따라 하나만):
 (가) 검사기 표면 축소: 먼저 코드 수정 없이 필수 검사 11개(+V1 모드 5개) 각각에 "이 결과가 마감 결정을 실제로 바꾸는가 / 다른 게이트가 이미 하는가 / 뺐을 때 잃는 것" 세 칸 표를 docs/engineering/hs-0302-preflight-surface-goal-2026-09-18.md 에 쓰고 커밋한다(결정 카드 5줄 포함). 그 표에서 "바꾼다" 로 남은 검사만 검사기에 유지하고, 뺀 검사는 삭제한다(별도 진단 스크립트 신설은 새 계층이므로 금지 — 필요하면 기존 명령 한 줄을 프롬프트에 남긴다). 남은 원자 조건(`&&` 항·순차 검사)마다 인수 시험에 독립 반례 행 1개(대역은 그 조건만 어기게). AC: 남은 방어 지점에 대해 V2 방식으로 변이를 다시 생성(목록이 아니라 생성, 지점당 ≥2)해 비등가 생존 0. 인수·검사기 각각 ≤600줄. REQUIRED_FULL 과 정본 명부·CI 스텝 주석의 검사 수가 일치. 실제 환경 1회(워크트리 B 에서 0단계 명령) 전부 PASS.
 (나) 결합 조건 분해: judge_new_shm 6조건(:221-222)·run_probe 4조건(:325)·ac2 순차 검사(:257-274)를 조건별 `pass/fail/blocked <이름.조건>` 줄로 쪼개고 REQUIRED_FULL 에 그 이름을 올려, 조건 하나가 사라지면 finish 의 MISSING 대조에 걸리게 한다. AC: M70~M75·M44~M47·M50·M52·M55 각 diff 사본이 인수 시험 FAIL(잡은 줄은 MISSING 또는 기대 이름 불일치). 정상 PASS 유지. 두 파일 ≤600줄. 시험 수가 늘지 않았음을 명시(이 안은 시험을 줄이지 않는다).
 (다) B 안 봉인: V2 판정서 §7 초안 중 높음 등급(결함 A·B·C·D·F = 공유메모리 6·조회 실패 10·트랩 3·V1 증거 7·장부 3, 최대 34건)을 표 기반 run_case 행으로 기존 파일에 추가(대역은 조건 하나만 어기게). AC: 해당 diff 사본 전부 FAIL, 정상 PASS, 파일 ≤600줄(예상 572). 나머지 24건은 README 에 "미봉인·후속" 으로 기록.

공통 마감(WU 마다): 커밋 전 `git diff --check`·bash -n 루프(`bad=0; for f in …; do bash -n "$f" || bad=1; done; [ "$bad" -eq 0 ]`)·`wc -l` 두 파일. 커밋 메시지는 무엇을 왜 + 반례 번호. 마감 프롬프트(hs-0302-r6-next-prompt-2026-09-16.md)가 검사 수·반례 수를 인용하면 같은 커밋에서 정정한다(git.prompt-tail 은 goal-prompts 밖 변경을 그 파일의 마지막 커밋 이후로 재므로). 모든 WU 뒤 Codex V1 1회(격리 --no-local 클론, `codex exec -s workspace-write` + stdin </dev/null, 판정은 파일 `private-reviews/hs-0302/codex-v1-<SHA 7자>.md` 첫 줄 VERDICT) → FAIL 이면 재현·수정·반례 봉인 후 재판정. 그 다음 `--check-v1 <SHA> --session <0단계 SESSION_DIR>` PASS.

배송(결정 ③ 없으면 하지 않는다): 0단계 (b)의 51커밋 문제를 사장님이 "기준 브랜치 먼저 push 승인" 또는 "A·B 를 origin 기준으로 재배치 승인" 으로 정한 뒤에만 hs-0302-r6-ship-prompt-2026-09-17.md v3 를 따른다. 재배치면 모든 검증 증거를 새 SHA 로 다시 만든다. PR 본문 "확인하지 못한 부분" 에 V2 재측정 TSV·3중 검토 결론·리눅스 CI·억제 만료를 적는다.

보고(상태 한 줄 + 결정 1~2개, 증거는 파일로): 1 0단계 (a)~(d) 결과와 (b) 세 숫자 2 WU-1·WU-2 RED→GREEN 명령·rc·줄수, 재측정 TSV 의 잡힘/생존 수 3 WU-3 실행 여부와 AC 결과 4 V1 판정 첫 줄·SHA 5 남은 위험 6 다음 행동. "push 가능" 은 승인이 아니다.
```

→ 위 블록이 붙여넣을 프롬프트 전체다. 결정은 블록 뒤에 한 줄로 붙인다 — WU-3 은 "(가) 축소" / "(나) 분해" / "(다) 봉인" 중 하나, 배송은 "기준 브랜치 먼저 push 승인" 또는 "origin 기준 재배치 승인". 없으면 WU-2 까지만 하고 멈춘다. 권고는 (가) — 세 검토 중 둘(Codex·codeaudit)이 "시험할 표면을 줄이는 것이 증명 비용을 줄이는 유일한 길" 로 일치했고, (나)·(다)는 시험 수를 줄이지 못한다.
