# WU-0B 클린룸 레쥬메 증거 계약 — goal (2026-09-10)

> 모드 `code-change`(문서 + 검사 스크립트 + CI 배선, 제품 코드 0) · 등급 **L2**
> 워크트리 `worktrees/hs-resume-evidence-contract` · 브랜치 `task/hs-resume-evidence-contract`
> 읽은 정본: `docs/sot/INDEX.md`, `docs/sot/git-workflow.md:27`, `docs/sot/verification-commands.md`,
> `docs/sot/coding-principles.md`, `docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md:96`
> 읽은 재발 원장: `docs/sot/31-strict-recurrence-ledger.md` (미병합 브랜치 `task/sot-strict-contract-fix`, 커밋 `5b1088a`) — L1·L2·L3 인용은 §9

## 상위 목표 (1문장)

후보자 이력서를 한 번 열람했을 때 **나중에 그 열람이 실제로 무엇을 봤는지 증명할 수 있는 최소 단위**를
문서로 확정해, 다음 작업(WU-1 이후)이 저장 코드를 짤 때 "무엇을 남겨야 충분한가"를 두고 헤매지 않게 한다.

**성공 신호 1개**: WU-7(사람인 후보 1명 실증)에서 저장한 증거 행 하나만 보고, 그 열람이
"화면 전체를 봤는지 / 어디까지만 봤는지"를 사람이 판단할 수 있다. 판단이 안 되면 계약이 부족한 것이다.

기능 완료(문서가 생김) ≠ 사업 효과(증거로 판단이 됨). 후자가 기준이다.

## 현재 상태 (실측, 추측 없음)

| 항목 | 실측 | 확인 명령 |
|---|---|---|
| `docs/sot/humansearch-evidence-contract.md` | **없음** | `ls` → No such file |
| `scripts/acceptance-hs-resume-contract.sh` | **없음** | `ls` → No such file |
| 시험 문제가 될 역사 설계서 2건 | **있음**(WU-0A 가 `docs/engineering/history/` 로 보존, "v4 전제 역사 기록" 머리말 + 원문 sha256) | `head -3` |
| WU-0A(선행 단위) | **미종료** — 판정 문서 미작성, push·PR·CI 0 | `bash scripts/acceptance-hs-kickoff.sh` → 11 PASS / 1 FAIL, `CHECKED: 12` |

## 인용 경로의 출처 (원장 L1 재발 방지 — 전수 확인함)

이 브랜치는 `main`(`01495b3`)에서 갈라졌다. **이 문서가 인용한 경로 중 3건은 아직 `main` 에 없고
미병합 브랜치에만 있다** — 인용만 하고 확인하지 않은 경로는 0건이다.

| 경로 | 어디 있나 |
|---|---|
| `docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md` | `task/hs-kickoff-ledger`(WU-0A, 미병합) |
| `docs/engineering/history/` 설계서 2건 | `task/hs-kickoff-ledger`(WU-0A, 미병합) |
| `docs/sot/31-strict-recurrence-ledger.md` | `task/sot-strict-contract-fix` `5b1088a`(미병합) |
| `.claude/hooks/stop-evidence-gate.py` | **저장소 어디에도 없음** — 부재 자체를 근거로 인용했다 |
| 나머지 8건 | 이 브랜치에 실존(또는 이 작업이 만들 산출물) |

확인 명령: 문서의 코드 스팬에서 저장소 경로를 뽑아 `[ -e ]` → `git cat-file -e <ref>:<path>` 순으로 전수 대조.
결과 `이 브랜치에 있음/정상: 8건 · 미병합 브랜치에만: 3건 · 팬텀: 0건`.

**따라서 이 작업의 구현은 WU-0A 병합 이후에 시작한다**(R5 단위 관문과 같은 결론, 근거는 다르다 —
R5 는 순서 규율이고 이것은 인용 경로의 실존 문제다).

## 근본 원인 (왜 이 작업이 필요한가)

2026-08-17 에 레쥬메 증거 설계가 이미 한 번 작성됐으나 **ValueHire v4 프로필 아카이버 재사용을 전제**로 했고,
사장님 결정(2026-08-14 "v1~v5 의존 0")과 충돌해 v6 설계서로 쓸 수 없다.
버리면 그 안의 **8개 counter-AC 와 실측 수치**까지 함께 사라진다. 그래서 WU-0A 가 원문을 해시와 함께 보존했고,
이 작업은 그것을 **시험 문제로만 쓰고 답은 v6 클린룸으로 다시 쓴다**.

## 인수 기준 (2026-09-14 회수로 대체됨)

아래 9개 검사기 중심 기준은 2026-09-10 착수 당시 계획이다. 2026-09-14 최신 지시가 문서 WU는
필드/반례 대조 검토로 충분하고 신규 범용 parser/검사기를 만들지 말라고 좁혔으므로, 현재 유효 기준은
이 문서 하단의 `2026-09-14 회수와 최신 지시 반영` 섹션이다. 아래 내용은 회수 전 역사 기록으로만 남긴다.

`bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-resume-contract.sh` 가 **exit 0**,
출력에 `CHECKED: 9` 줄이 있다. (래퍼가 뒤에 `OK(run-acceptance)` 한 줄을 덧붙이므로 "마지막 줄"이 아니라 "출력에 포함")

9 = counter-AC 8개 + 금지어 1개.

### counter-AC 8개 — 각각 계약 문서에 `검사 명령:` 줄이 있어야 한다

| # | counter-AC | 무엇을 막는가 | 역사 설계서 출처 |
|---|---|---|---|
| 1 | 구간 무누락 manifest | 긴 페이지를 나눠 캡처하고 사이 구간이 빠졌는데 "다 봤다"고 기록하는 것 | `…archive-goal-2026-08-17.md:16`, `…implementation-prompt-2026-08-17.md:22` |
| 2 | 마지막 화면 | 마지막 스크롤 위치를 남기지 않아 "어디까지 봤는지" 복원 불가 | `archive:57`, `impl:38` |
| 3 | NULL 구분 | "값이 없음"과 "안 봐서 모름"을 같은 빈칸으로 적는 것 | `archive:58`, `impl:64` |
| 4 | 회사별 duty | 경력 여러 건의 담당 업무를 하나로 뭉개 어느 회사 것인지 잃는 것 | `archive:16`, `impl:132` |
| 5 | 검색 조건 보존 | 어떤 검색으로 나온 후보인지 안 남겨 재현 불가 | `archive:8`, `impl:15` |
| 6 | 원격 경로 금지 | 증거 원본을 우리가 통제하지 않는 곳에 두는 것 | `archive:8`, `impl:16` |
| 7 | readback | 저장했다고만 하고 다시 읽어 대조하지 않는 것 | `archive:8`, `impl:16` |
| 8 | 회사 별칭 | 같은 회사를 다른 표기로 적어 중복·누락이 생기는 것 | `archive:63`, `impl:239` |

### 금지어 1개

계약 문서 안에 `v4` · `Valuehire_v4` · `profile-archiver` 가 **0회**여야 한다.
v4 재사용 전제가 문장 하나로도 다시 들어오면 클린룸이 깨진다.

### counter-AC (인수 기준 자체를 공격하는 조건)

- 8개 항목이 **제목만** 있고 `검사 명령:` 이 자리표시자면 FAIL 이어야 한다.
- 금지어가 **코드 블록 안**에 숨어 있어도 잡아야 한다.
- 항목이 하나 빠지면 `CHECKED: 8 ≠ 9` 로 스스로 exit 1 이어야 한다.

## 계약 (입출력 모양 먼저 — SDD)

`docs/sot/humansearch-evidence-contract.md` 는 "증거 한 건"의 모양을 먼저 정의한다.
필드 목록·타입·필수 여부를 표로 적고, 각 counter-AC 를 그 표의 어느 필드가 막는지 연결한다.
**저장 구현(SQLite·원격)은 이 작업의 범위가 아니다** — 모양만 확정한다.

## 결정성 규율 — 입력 영역 표 (§3 ①, 2026-09-14 회수 전 기록)

아래 입력 표는 새 검사 스크립트를 만들던 원래 계획의 결정성 규율이다. 현재 실행에서는 새 검사기를 추가하지
않았고, SOT 문서의 필드와 반례를 `rg` 대조·형식 lint·독립 codeaudit로 검토한다.

이 작업의 "입력"은 계약 문서 자신이다. 검사기가 받는 입력을 전부 열거한다.

| 입력 | 처리 |
|---|---|
| 정상: 8개 항목 + `검사 명령:` + 금지어 0회 | 통과 |
| 문서 없음 | 명시적 거부(8개 전부 FAIL, 통과 아님) |
| 항목 제목은 있고 `검사 명령:` 없음 | 거부 |
| `검사 명령:` 이 자리표시자(빈 값·`-`·8자 미만) | 거부 |
| 금지어가 본문·코드 블록·표 어디에든 1회 이상 | 거부 |
| 항목 수가 8개가 아님 | `CHECKED ≠ 9` 로 스스로 exit 1 |
| **그 외 전부** | 명시적 거부 |

## 결정 목록 (오너 확정 필요 — §3 ②)

| # | 결정 | 기본값(반대 없으면 이대로) |
|---|---|---|
| 1 | 계약 문서에 필드 표를 넣을 것인가, counter-AC 목록만 둘 것인가 | **필드 표 + counter-AC 연결** (WU-1 이후가 바로 쓰게) |
| 2 | 금지어에 `v5` 도 넣을 것인가 | **넣지 않는다** (정본 §3 은 v4 계열만 지정) |
| 3 | 8개 항목의 이름을 정본 문구 그대로 쓸 것인가 | **그대로 쓴다** (정본과 글자 단위 대조 가능하게) |

## 게이트 계획 (2026-09-14 회수로 대체됨)

아래 RED/GREEN 검사기 계획은 더 이상 현재 실행 게이트가 아니다. 현재 실행 게이트는 새 검사기 없는 문서 대조,
strict 원칙 검사, 비밀 스캔, 기존 acceptance, 독립 codeaudit 지적 5건 회수다.

`RED`(검사기 먼저, 문서 없어 FAIL) → `GREEN`(계약 문서 작성) → 자기 변이 검사
(`scripts/acceptance-hs-resume-contract-mutations.sh`, 정본 §3 공통 꼬리) → Full Strict →
Codeaudit → Adversarial(V1) → push → PR → CI.

## 적대검증 정조준 (여기를 때려라)

1. 8개 항목이 **서로 겹치는가** — 겹치면 하나가 죽어도 다른 게 가려서 검사가 무의미해진다.
2. `검사 명령:` 이 **실행 가능한 명령인가**, 아니면 산문인가. WU-0A 에서 "산문 AC → Codex FAIL" 이 이미 났다.
3. 금지어 검사가 **파일명·URL·주석**까지 보는가.
4. 계약이 **WU-7 이 실제로 쓸 수 있는 모양인가** — 쓸 수 없으면 문서만 늘어난 것이다.

## 비범위

- **WU-0A 종료 전 이 작업의 구현 착수 금지**(R5 단위 관문). WU-0A 는 판정 문서·push·PR·CI 가 남았다.
  이 문서 작성까지가 지금 허용 범위다.
- 저장 구현(SQLite 스키마·Supabase·마이그레이션), 브라우저 접속, 실제 후보 데이터.
- 미병합 6건의 병합·폐기 실행(사장님 몫).

## §9. 재발 원장 인용 (R4)

| 원장 행 | 이 작업에 주는 제약 |
|---|---|
| L1 phantom SOT 참조(2회 → 승격 필요) | 이 문서가 인용한 경로는 **전부 실존을 확인**했다. 인용만 하고 확인 안 한 경로 0건. |
| L2 없는 도구를 정본 명령처럼 서술 | 검증 명령은 `docs/sot/verification-commands.md` 가 정의한 것만 쓴다(`npm`·`make` 없음). |
| L3 Stop 게이트 hook 미배선 | 이 저장소엔 `.claude/hooks/stop-evidence-gate.py` 가 없다 — 마커 강제가 없으므로 커밋 규율을 손으로 지킨다. |

**원장 자체가 main 에 없다**(미병합 브랜치 `task/sot-strict-contract-fix`, `5b1088a`). R4 가 매 작업마다 읽으라는
파일이 main 에 없는 상태가 계속되면 L1 이 3회째가 된다. 이 작업의 PR 본문에 그 사실을 적어 병합을 재촉한다.

## 부채 이관 (R9 — WU-0A 에서 넘어온 것)

WU-0A 의 Codex 적대검증 7회차까지에서 닫지 못한 지적:

| 지적 | 상태 |
|---|---|
| 음성 대조군의 기대 실패 사유가 여전히 부분문자열 대조 | 부채 — 별도 WU |
| 전각·동형 문자로 스텝 이름·표 열을 속이는 입력 미검사 | 부채 — 별도 WU |
| 워크플로 트리거(`on:`)·파일 경로 변경으로 워크플로 자체를 안 돌게 하는 경로 미검사 | 부채 — 별도 WU |

이 세 건은 WU-0B 와 무관한 축(검사기 강화)이므로 여기서 다루지 않는다. WU-0A PR 본문과 후속 이슈에 남긴다.

## 적대 검증 로그

(후기록 — V1/V2 판정 본문을 그대로 append)

## 2026-09-14 회수와 최신 지시 반영

최신 실행 문서 `/Users/kangsangmo/Desktop/hs-next-prompt-v5-20260914.md`를 끝까지 읽고 이 WU를
HS-02.01 최소 열람 증거 계약으로 회수했다. 이번 범위는 `docs/sot/humansearch-evidence-contract.md`와
이 goal 연결만 소유한다. RPS 프로젝트 생성·기존 필터 업데이트 입력 계약, Aside 전용 브라우저 정책,
합성 runtime 스키마 시험은 다른 WU가 소유한다.

원래 goal은 새 인수 검사 스크립트 생성을 계획했지만, 최신 작업 지시는 문서 WU에 대해 필드/반례 대조
검토면 충분하고 신규 범용 parser/검사기를 만들지 말라고 좁혔다. 따라서 이번 회수에서는 새 검사기를
추가하지 않고, 계약 문서 안의 `검사 명령:` 줄과 아래 대조 명령으로 확인한다.

### 최신 인수 기준

`docs/sot/humansearch-evidence-contract.md`는 아래를 모두 포함해야 한다.

1. 출처 URL, 관측 시각, 문서 높이, 캡처 구간 좌표와 해시.
2. `complete` / `partial` / `failed` 구분과 실패 사유.
3. NULL, 빈 값, 미관측, 제공 안 됨, 가림 상태의 구분.
4. 회사별 담당 업무와 회사 별칭의 근거 상태.
5. 후보가 나온 검색 조건 참조와 RPS 필터 적용 결과 재조회 증거 참조.
6. 독립 재조회 상태와 저장 실패 시 중단 사유.
7. 조건부 필드의 상태와 값 모양: `candidate_ref`, `document_height_px`, `company_duties`.
8. 동적 문서 높이와 실패·가림 구간이 `complete`를 만들지 못하는 판정 기준.
9. 화면에 보인 연락처 관측 필드와 연락처 수집·패킷 사용의 후속 소유권.
10. 8개 counter-AC와 각 항목의 `검사 명령:`.

검증 명령:

```bash
rg -n '`source_url`|`observed_at`|`document_height_px`|`height_state`|`segments`|`coverage_status`|`coverage_reason`|`last_observed_y_px`|observed_empty|not_observed|not_available|`company_duties`|`company_duties_state`|`company_aliases`|`observed_contact_fields`|`search_condition_ref`|`readback_status`' docs/sot/humansearch-evidence-contract.md
rg -n '구간 무누락 manifest|마지막 화면|NULL 구분|회사별 duty|검색 조건 보존|원격 경로 금지|readback|회사 별칭' docs/sot/humansearch-evidence-contract.md
rg -n '조건부|observed_changed|`segment_status=observed`|추정하지 않는다|후속 저장·패킷 계약' docs/sot/humansearch-evidence-contract.md
rg -c '검사 명령:' docs/sot/humansearch-evidence-contract.md
bash scripts/acceptance-principles-check.sh
git diff --check
```

기대값: 첫 두 `rg` 명령은 필요한 필드와 8개 반례를 모두 찾고, `rg -c`는 8 이상을 출력한다.
Strict 원칙 검사는 `VERDICT: PASS`, `CHECKED: 34`를 출력한다. `git diff --check`는 출력 없이 종료값 0이어야 한다.

### 현재 제한

- `docs/sot/strict-workflow.md`는 이 워크트리에 없어 직접 로드하지 못했다. strict 스킬의 저장소 SOT
  우선 요구는 `NOT_RUN`으로 기록한다.
- 최신 v5 문서는 main 병합 전 로컬 stacked 작업을 허용하지만, main 병합 조건을 충족했다고 주장하지 않는다.
- 실제 브라우저 조작, 후보 개인정보 저장, RPS 프로젝트 쓰기, merge는 이번 WU에서 하지 않는다.
