# 실행 프롬프트 — codeaudit 후속 3건 수정 + 다음 작업 브리핑 (2026-08-15)

> 이 문서는 **다음 세션(또는 codex)이 그대로 읽고 실행할 자율 프롬프트**다. /strict 모드로 돈다.
> 위험 등급 **L3** — SOT 문서 3개(`mechanism-registry.yaml`·`git-workflow.md`·두 goal 문서) 수정 + 두 열린 PR(#13·#14)에 영향.
> 근거 감사: `.claude/private-reviews/codex-session-audit-2026-08-15.md`(지문 `5b26a361`) + 이 세션 Claude 직접 재현.

---

## 결론 (사장님 브리핑 — 먼저 읽는 요약)

**결론.** 이번에 만든 두 문지기(파일 500줄 게이트·G3 검사기)를 감사했더니, 만든 것 자체는 진짜인데 **세 곳을 고쳐야** 합니다. ⑴ G3 검사기가 "검사 장치 명부"에 빠져 있어 누가 그 검사를 지워도 명부 대조가 못 잡습니다. ⑵ 제가 문서에 "마지막으로 막는 것은 서버 검사"라고 적었는데, 이 저장소는 요금제 때문에 서버 검사가 병합을 못 막습니다 — 그 문구를 사실대로 고쳐야 합니다. ⑶ G3의 "아직 못 막은 우회 목록"이 문서마다 개수가 달라(6개 vs 7개) 통일해야 합니다.

**왜 지금.** 세 곳 다 작은 수정이고, 특히 ⑴ 명부 누락은 그대로 두면 "명부가 실제를 지킨다"는 약속에 구멍이 남습니다("유예를 기본 처리로 삼지 마라" 원칙). ⑵는 잘못된 안심을 주는 문구라 병합 전에 바로잡는 게 맞습니다.

**틀리면 뭐가 깨지나.** ⑵를 안 고치면, 다음에 이 문서를 읽는 사람이 "서버 검사가 지켜주니 병합 규율을 느슨히 해도 된다"고 오해합니다. 실제로는 아무도 안 막습니다.

---

## 공통 진행 규칙 (/strict)

- 각 작업은 **해당 워크트리 안에서만** 파일을 고친다. 메인 작업트리 직접 수정 금지, `git push`는 각 작업 검증 통과 후에만.
- 문서 변경도 **RED→GREEN**을 흉내 낸다: 먼저 "현재 문구가 틀렸음을 잡는 grep 검사"를 만들어 실패(현재 상태에서 잡힘)를 확인 → 고친 뒤 그 검사가 통과.
- 각 작업 완료 후 **V1(codex) 적대검증**을 돌린다(`codex:codex-rescue` 에이전트, `name` 파라미터 금지, model opus). 판정을 `.claude/private-reviews/`에 파일로 저장. 프롬프트 끝에 §8-7 출력 형식 블록 첨부.
- **codex가 우회 탐색류 프롬프트를 자기 사이버보안 필터로 거부하면**(이 세션에서 실측된 알려진 벽), 그 검증은 **Claude 격리 세션(general-purpose)으로 대체**하고 장부에 "V1 불가 → V2급 대체"로 적는다.
- codex는 워크트리 밖 `index.lock`에 쓰기 권한이 없다 → **커밋은 실행자(나)가 직접** 한다. 셸 작업 위치를 대상 워크트리에 두지 않으면 codex가 그 폴더에 못 쓴다.

---

## 작업 A — G3를 검사 장치 명부에 등재 (심각도 중간)

**현재 상태.** `worktrees/humansearch-g3-portal-constants/docs/sot/mechanism-registry.yaml`에 `portal-constants` 관련 항목이 **0건**이다(실측: `grep -c "portal-constants" ... → 0`). 반면 같은 워크트리의 `.github/workflows/verify.yml`에는 G3 검사가 **8곳** 배선돼 있다. 즉 G3의 CI 배선은 실재하는데, "명부와 실제가 일치하는지" 대조하는 장치(AC-M)의 감시 밖에 있다. 500줄 게이트는 `ci-file-size-gate`로 등재됐는데(대칭 참고) G3만 빠졌다.

**AC-A1.** When G3 검사기가 CI에 배선돼 있으면, then 그 사실이 `mechanism-registry.yaml`에 항목으로 존재하고 대조기가 통과해야 한다.
- 등재 형식(기존 `ci-file-size-gate` 항목과 동형):
  ```yaml
  - id: "ci-portal-constants-gate"
    path: ".github/workflows/verify.yml"
    target: "bash scripts/acceptance-hs-portal-constants.sh"
    stage: "ci"
    ci_mirror_job: "verify"
    required: true
  ```
  → 이 블록은 명부에 그대로 추가할 항목의 형식이다. `target`은 verify.yml 안에 문자 그대로 존재하는 명령이어야 대조기가 실제 실행 칸과 맞춰볼 수 있다(함수명·요약 금지).
- 검증: `bash scripts/verify/check-mechanism-registry.sh` → exit 0, 그리고 `grep -c "portal-constants" docs/sot/mechanism-registry.yaml` ≥ 1.
- counter-AC: 항목만 넣고 대조기가 실제로 verify.yml의 그 문자열을 확인하지 않으면 가짜. **명부 target 문자열을 verify.yml에서 지웠을 때 대조기가 exit 1(불합격)로 잡는지** 뮤테이션으로 확인.

**추가 확인 (codex 지적 C — 대조기 자체 약점).** codex 감사가 "명부 대조기가 주석 속 문자열도 합격시킨다"고 지목했다(`.claude/private-reviews/codex-session-audit-2026-08-15.md` C절). G3 target을 verify.yml의 **주석 줄에만** 두고 실행 칸에서 지운 표본으로 대조기를 돌려, 대조기가 이를 통과시키면 **별도 결함으로 기록**(이번 작업 범위에 넣을지는 실행자 판단 — 넣으면 대조기가 주석이 아닌 실제 `run:` 칸을 보도록 보강). 범위 밖으로 두면 그 사실을 장부에 명시.

**SOT 체크리스트.** `mechanism-registry.yaml`은 SOT다. 변경이 곧 SOT diff이므로 같은 PR(#13)에 포함.

---

## 작업 B — "CI가 최종 강제선" 표현 정정 (심각도 높음)

**현재 상태 (틀린 문구 위치, 실측).**
- `worktrees/file-size-gate/docs/engineering/file-size-gate-goal-2026-08-15.md:119` — "이 게이트의 최종 강제선은 서버 검사(CI)다."
- `worktrees/humansearch-g3-portal-constants/docs/engineering/humansearch-g3-portal-shell-runs-on-goal-2026-08-15.md:363` — "최종 강제선은 서버 검사(CI)다."
- `docs/sot/git-workflow.md:28,33` — main 보호가 GitHub에서 기계 강제되는지 "미확인"으로 남겨둠.

**근본 원인.** 이 저장소는 개인 계정(User)의 비공개(private) 저장소라 "검사 통과해야 병합(required status check)" 기능이 요금제로 잠겨 있다. 실측: `gh api repos/sangmokang/Valuehire_v6/branches/main/protection` → `403 "Upgrade to GitHub Pro or make this repository public…"`. 따라서 CI는 **병합을 강제하지 못하는 신호**이고, 실질 강제는 로컬 pre-push 훅뿐이며 그것도 `git push --no-verify`로 우회 가능(협조적 잠금).

**AC-B1.** When goal 문서가 게이트의 강제력을 서술하면, then "CI가 최종 강제선"이라 단정하지 않고 위 실측(403)과 "CI=신호·pre-push=협조적 실질강제·진짜 강제는 요금제 업글/public 전환 필요"를 함께 적어야 한다.
- 두 goal 문서(119행·363행)의 해당 문장을 정정.
- 검증: `grep -rn "최종 강제선은 서버 검사(CI)다" <두 goal 파일>` → 0건. 그리고 새 문장에 `403` 또는 `required status check` 또는 `요금제` 근거가 존재.
- counter-AC: 문장만 부드럽게 바꾸고 403 실측 근거를 안 넣으면 불완전(codex-file-size-verdict7과 git-workflow의 내부 모순이 그대로 남음).

**AC-B2.** `git-workflow.md:28,33`의 "미확인"을 이번 403 실측 결과로 갱신(미확인 → "실측: required check 강제 불가, 개인+private 요금제 제약. 강제하려면 Pro 업글 또는 public").
- 검증: `git-workflow.md`에 `403` 또는 `Pro` 또는 `required` 강제불가 취지 문장 존재.

**SOT 체크리스트.** `git-workflow.md`는 SOT. 같은 커밋에 포함. goal 문서 2개는 각 PR(#14·#13)에.

---

## 작업 C — G3 잔여 한계 목록 문서 간 통일 (심각도 중간)

**현재 상태.** G3 goal `:362`의 잔여 우회 목록(5개 나열: `max-parallel:0`·`timeout-minutes:0`·`container`·`runs-on ${{ }}`·`concurrency`)과, 정본 판정서 `.claude/private-reviews/claude-g3-v2-verdict9-2026-08-15.md`의 §잔여 우회 목록이 **항목이 다르다**(codex 감사 E절: 한쪽은 `runs-on 식`, 다른 쪽은 `environment: production` — 실제 후보 7종). 문서끼리 어긋나면 다음 사람이 어느 게 맞는지 모른다.

**AC-C1.** When 두 문서가 같은 잔여 우회를 서술하면, then 항목 집합이 일치해야 한다.
- verdict9의 §잔여 우회 목록을 **정본**으로 삼아 G3 goal `:362` 목록을 그에 맞춰 통일(7종 전부, 각 항목 "모델 안/밖" 구분 유지).
- 검증: 두 문서의 잔여 우회 키 목록을 뽑아 정렬 비교 → 동일.
- counter-AC: 개수만 맞추고 항목 이름이 다르면 가짜.

**SOT 체크리스트.** goal 문서는 SOT 아님(엔지니어링 기록). PR #13에 포함.

---

## 배송 (작업 A·B·C 공통)

1. 각 워크트리에서 위 검증 전부 통과 확인(출력 숫자 첨부).
2. 커밋(실행자 직접). pre-push 훅 통과 확인 — G3 워크트리는 시험이 많아 push가 5분+ 걸리니 백그라운드로.
3. push → PR #13·#14 자동 갱신. **CI 초록 확인**(로컬 초록 ≠ CI 초록 — 이 세션에서 Ruby/Psych 버전차로 CI가 한 번 깨졌다. `YAML.safe_load`는 키워드 인자 형태만 CI 호환).
4. 각 작업의 V1(codex) 또는 V2 판정을 goal 문서 `## 적대 검증 로그`에 append(지문·경로 포함).
5. **머지는 사장님 지시("머지해") 전까지 하지 않는다.**

---

## 마지막 단계 — 다음 작업 브리핑 (작업 A·B·C 완료 후 실행)

작업 A·B·C가 끝나고 두 PR CI가 초록이면, **아래를 §8 3층 브리핑(결론 → 판단 근거 → 증거)으로 사장님께 보고하고, 다음 착수 후보를 결정 카드로 제시**하라. 스스로 다음 코드를 시작하지 말고, 사장님 결정을 받는다.

브리핑에 반드시 담을 것:

1. **지금 상태 한 줄.** 두 문지기(500줄·G3)가 감사 후속 3건까지 반영돼 병합 준비됐는지, 남은 결정(병합 여부)이 무엇인지.
2. **다음 착수 후보 — 클린룸 계약 로드맵의 실제 서치 구현.** 순서와 각 한 줄 설명을 표로:
   - **D0** (선행 문서 1건): 브라우저 접속 방식을, 사장님이 2026-08-14 확정하신 무인 방식(전용 브라우저 상시 + 진단 포트 접속)으로 공식 개정하는 계약 변경 기록. 코드 아님, 위험 낮음.
   - **L0**: 로그인 상태 뼈대(UNKNOWN/HUMAN_AUTH/AUTHENTICATED/CHALLENGE/DRIFTED 전이표)를 화면 요소 없이 먼저 고정. 클린룸 goal `:377`.
   - **C1**: 사람인 현재 화면 실캡처 → 개인정보 제거 구조 fixture 생성. 클린룸 goal `:386`.
   - **L1~L3**: 미로그인 정지 / 사람 로그인 후 진행 / 캡차·2FA terminal. 클린룸 goal `:396-398`.
   - **V1**: 후보 1명 실제로 열고 목록 복귀 증거 — 여정 첫 라이브 실증. 클린룸 goal `:404`.
   - **S1~S3**: 점수(서울권대·이직안정성 등) 순수 함수 계산 + 합격선 넘은 후보만 등록. 클린룸 goal `:413-415`.
3. **결정 카드 (판단 필요).** 다음 착수를 ⑴ D0 문서부터(권장 — 위험 낮고 무인 확정을 공식화) ⑵ 바로 L0 코드부터 ⑶ 다른 우선순위(상류 U 트랙 먼저 등) 중 무엇으로 할지 선택지를 좁혀 제시. 각 선택의 대가·되돌리기 포함.
4. **정직 표기.** 이번 감사에서 남긴 것(자기개조 공격 방어 미비 = 검사 통과 개수 고정값 미잠금, 낮음)과, 두 게이트의 실제 강제력 한계(로컬 pre-push까지, CI는 요금제상 비강제)를 다시 한 줄로.

---

## 적대 검증 로그 (실행자가 append)

(작업 A·B·C의 V1/V2 판정을 여기 또는 각 goal 문서에 append)
