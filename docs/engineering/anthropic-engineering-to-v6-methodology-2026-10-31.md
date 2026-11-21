# Anthropic Engineering 블로그 → Valuehire v6 적용 방법론 (2026-10-31)

범위: anthropic.com/engineering 게시글 24편 + 사장님이 붙여넣은 Frontier Red Team 글 "LLMs are making formal software verification feasible at a much larger scale"(2026-10-22) 1편.
원칙: 모든 주장은 [확인]/[추정]/[미확인]으로 표기. v6 현재 상태는 2026-10-31 저장소 실측(docs/sot, scripts, humansearch, throughput 진단 2026-08-27) 기준.

---

## PART A. 포멀 검증 글 사실 검증 판정서

### A-1. 검증 결과 요약표

| # | 글의 주장 | 외부 검증 | 판정 |
|---|---|---|---|
| 1 | 글 존재·날짜·저자(Frontier Red Team, 2026-10-22) | anthropic.com/research/formal-verification 실페치 일치 | [확인] |
| 2 | 123개 라이브러리·239개 엔트리포인트 증명 | 공개 저장소(theorem-labs/oss-verify-proofs README)는 **26개 라이브러리·61개 엔트리포인트**만 증명 공개. 전체 statement 20,164개 중 proved 336 · known false 5 · blocked by model 229 · open 19,594 | [부분확인] 글도 "subset 공개"라고 명시하나, 외부에서 재검증 가능한 범위는 주장치의 약 1/4 |
| 3 | Rocq 1억 8천만 줄, 증명당 약 60만 줄, 총 작성 10억 줄 | 부록 PDF에서 10억 줄 작성·1.8억 줄 통과·cJSON 391줄 파서→63만 줄 증명·fftw3 5.1만 줄→48만 줄 확인. 저장소 README에는 줄 수 없음 | [내부자료 확인] 독립 재현 불가 |
| 4 | 가정: 단일 스레드·정적 링크·RISC-V·musl·64MB 입력 | README: riscv64 static, clang 20.1.8 + musl, LPS(Linux Process Semantics) "best effort and not complete", 메모리 예산 ASan 2GiB/UBSan 16GiB. 64MB·단일 스레드는 README에 없고 skill 문서에 "64MiB 이상 입력 거부"로 존재 | [확인] |
| 5 | CVE-2026-56132(libexpat) "재발견", deeply nested input | libexpat PR #1272(2026-06-20 머지): doProlog scaffold 인덱스 OOB write, 부모·서브파서 간 DTD 공유 + 중첩 깊이 차이가 원인. 메커니즘 일치 | [확인] 단 "재발견"이 Claude가 독립적으로 찾았다는 뜻인지는 외부 확인 불가 |
| 6 | "Linux 커널 최근 1,000개 이상 취약점 공개" | 인용된 LWN 링크는 Debian DSA-6528-1(2026-09-29) 한 건, CVE 약 550개 | [출처 약함] 숫자가 인용 출처에서 직접 확인되지 않음 |
| 7 | seL4 구현 2인년 vs 검증 20인년 | seL4 SOSP'09 논문의 공지 수치와 일치 | [확인·기존지식] |
| 8 | Opus 5.5가 Opus 5 대비 토큰 40% 절감, 공유 작업공간 17% 절감 | 부록이 36과제 설계(283~2,491 명령어, 12개×3그룹, mini-ASan, 5M 토큰 예산 3회 시도)는 기술하나 수치는 Anthropic 내부 측정 | [내부자료] 외부 재현 불가 |
| 9 | Theorem 로드맵: Nix 생태계 전체 | theorem.dev 블로그(2026-09-29): nixpkgs 95%를 약 $134M로 2027년 말까지 — **전부 투영치**, 현재 그 로드맵으로 검증 완료된 패키지 0개. 능력 2개월 배증 가정 | [확인·투영] |
| 10 | Theorem Claude 스킬 공개 | github.com/theorem-labs/oss-verify `.claude/skills/add-project/SKILL.md` 실존. C/C++/Rust/Python/Go, riscv64 정적 빌드 요구 | [확인] |
| 11 | OSS Verify 무료 제공 | theorem.dev/oss-verify "No cost. Qualifying open source projects pay nothing." 코어 메인테이너만 등록, 수 일 소요 | [확인] |
| 12 | Python 인터프리터 1.7M 프로그램 99.95% 일치 | 부록: 17 tier 전부 Verus 증명, 주입 버그 7개 중 테스트 생존 5·증명은 7개 모두 포착 | [내부자료] |
| 13 | 전문가 평가 | 부록: 에이전트가 요구보다 짧고 중요한 스펙(중앙값 110줄 vs 프로그램 86KB)을 먼저 합성한 점은 긍정. **그러나 증명이 장황하고 추상화가 없어 MachCSL 경험상 "복잡도 벽"에 부딪힐 수 있다**는 경고 | [확인] 본문은 이 한계를 "This is just the beginning"으로 희석 |
| 14 | 보상 해킹 방지 | 각주 6: 패치에 페널티, 변경 입력 증명에 가산점, 패치 로그 감사. 수치·공개 패치 목록 없음 | [미확인] 정량 근거 부재 |

### A-2. 종합 판정
- **핵심 사실관계(글 존재, 협력사, 공개 산출물, 가정, CVE 메커니즘, 무료 프로그램)는 확인됨.**
- **과장 또는 근거 약한 지점 4개**: ① 외부 재검증 가능한 증명은 주장의 약 1/4, ② "1,000개 취약점" 인용 출처 불일치, ③ 모델 세대·토큰 비교는 내부 데이터, ④ 전문가의 "복잡도 벽" 경고가 본문에서 약화.
- **가장 중요한 숨은 수치**: statement 인벤토리 20,164개 중 proved 336개(1.7%). 시도하지 않은 open이 대부분이라 실패율은 아니지만, "대규모"의 실제 분모를 보여줌.
- 결론: **"증명이 가능해졌다"는 참, "범용적으로 실용화됐다"는 아직 투영**. 2026년 기준 채택 조건은 C/C++/Rust/Go/Python + 퍼즈 하네스 + riscv64 정적 빌드.

### A-3. v6에 포멀 검증이 직접 적용되는가
- **직접 적용 불가**: v6 제품 코드는 Python(humansearch/src 2,525줄)·JS/HTML(apps/admin 462줄)·bash 인수 스크립트이며, 바이너리 수준 RISC-V 증명 대상이 아니다. Python은 OSS Verify에서 atheris 퍼즈 하네스로 지원하나, v6의 위험은 메모리 안전이 아니라 **외부 사이트 드리프트·조용한 실패·개인정보 노출**이다.
- **이전 가능한 방법론 5개** (PART C-5에 통합):
  1. "테스트를 스펙으로 바꾼다" → v6 P5②·P14③(순수 판정 함수 속성 기반 테스트 필수)의 상위 버전. `hypothesis` + **CrossHair**(Python 계약 기호실행, Z3) 로 `status_codes`·`weekly_window`·채점 함수에 `icontract` 사전/사후조건을 걸고 CI에서 반례 탐색. 비용 낮음, 즉시 가능.
  2. "증명기와 검사기 분리(Rocq 커널만 신뢰)" → v6 P17(증거는 만든 자가 쓸 수 없다)·P23(초록불은 SHA 귀속)과 동일 구조. 유지.
  3. "패치는 페널티, 스펙 재생성은 명시적" → P5①(RED 후 테스트 불변)·P15④(기대값 변경 단독 커밋). **추가**: `contracts/*.json` 변경도 단독 커밋 + PR 본문에 변경 필드 자동 노출.
  4. "증명 재사용으로 17% 절감" → v6 판정서·증거가 PR마다 재생산되어 12,008줄(PR#13) 적체. **공유 fixture·verdict 라이브러리**를 `scripts/verify/fixtures/`로 일원화하고 PR에는 참조만.
  5. "퍼즈 엔트리포인트 = 크래시 금지 스펙" → humansearch `observe()`·`auth_surface` 분류기에 **실캡처 HTML 코퍼스 기반 퍼징**(hypothesis 변이 + 저장 스냅샷): 어떤 입력에도 예외 전파·조용한 None 반환 금지(P3). §1-B 4조(실캡처 스냅샷만)와 합치.

---

## PART B. 24편 핵심 ↔ v6 현황 대조표

v6 현재 병목(2026-08-27 진단): 제품 코드 2,156줄 대비 검증 인프라 4.3배·문서 13.2배, 열린 PR 12건 중 9건 MERGEABLE인데 **오너 1인 병합 게이트** 포화, 워크트리 69개(v4 실패 기준선 재현율 90%), RED 0/29로 품질이 아니라 처리량이 막힘.

| 글 | 핵심 교훈 | v6 현 상태 | 적용점 | 우선 |
|---|---|---|---|---|
| 1 Redesigning source control | 사람 규모 워크플로(머지 큐·라인 리뷰)는 에이전트 규모에서 깨진다. 리뷰는 "의도" 단위, 툴이 comment-only vs 민감 로직을 구분해 승인 규칙 차등, post-merge 자동 테스트 | git-workflow.md:23 "자동 병합 금지 — 오너가 diff를 읽는다", 모든 PR 동일 게이트 → 34,511줄 적체 | **병합 티어링**: 경로 기반 자동 분류(docs/evidence/fixture-only → CI 초록 시 자동 병합 허용, contracts·hooks·scripts/verify·P19 외부경계 → 오너 필독). P11의 존재 이유는 "제품 diff를 읽는 것"이지 판정서 읽기가 아님 | ★★★ |
| 6 Harness design (long-running apps) | 생성자/평가자 분리, 평가자는 회의적으로 튜닝, **하네스 부품은 한 번에 하나씩 제거하며 load-bearing 검증**, 평가자는 Playwright로 앱을 직접 사용 | G→V1→V2 분리 있음. 인수 스크립트 29개·억제 3건. 어떤 게이트가 실제로 결함을 잡았는지 집계 없음 | **게이트 회수 감사**: 각 acceptance-*.sh가 실PR에서 RED를 낸 횟수를 git log로 집계, 0회 게이트는 P12 회수 후보. admin 대시보드 V-3는 Playwright로 사용자처럼 클릭하는 평가자로 | ★★★ |
| 12 Effective harnesses (long-running agents) | `features.json`(passes만 변경 가능)·`init.sh`·`claude-progress.txt`·세션마다 클린 종료·브라우저 e2e 자기검증 | session-status.sh(HEAD·RED 출력)만 존재. 저니 마스터플랜은 산문 문서. 워크트리 69개가 "반쯤 만든 미문서화 기능" | **features.json 도입**: HumanSearch·Dashboard 기능 목록을 JSON으로(category/description/steps/passes), 코딩 에이전트는 passes만 변경(P5와 동일 규칙). 워크트리마다 `init.sh`·progress 파일 필수, `make red-ledger`가 48h 초과 워크트리를 함께 출력(AC-3) | ★★★ |
| 11 Demystifying evals | 실제 실패에서 뽑은 20~50 과제, 결정적 채점기 우선, pass^k, 트랜스크립트 정독, 균형 세트(해야/하지 말아야) | strict §6 "실행 가능한 평가셋 없으면 NOT_IMPLEMENTED". contracts/humansearch/saramin-markers.json·fixtures 존재하나 평가셋 아님 | **HumanSearch L0 회귀 평가셋**: 실캡처 화면 20~50개 + 기대 라벨(인증/비인증/캡차/점유) → pass^3 측정. 균형: "제안 보내야 함/보내면 안 됨" 양쪽 포함. 결과를 verify.sh 숫자로 | ★★★ |
| 17 Context engineering · 16 Agent Skills | 최소 고신호 토큰, 점진적 공개(name/description→본문→참조파일), 서브에이전트는 1~2k 요약만 | 전역 CLAUDE.md(oh-my-claudecode 포함)+원칙 24개+SOT 11파일이 세션 시작에 로드. docs 28,457줄 | **세션 시작 토큰 예산 측정**(session-status.sh에 출력 추가) → SOT INDEX만 선적재, 원칙 상세는 참조 로드. strict/harness/verify SKILL.md의 description을 트리거 관점으로 재작성, 본문 분할 | ★★ |
| 19 Writing tools for agents · 8 C compiler | 도구 출력은 짧게·grep 가능하게(`ERROR <사유>` 한 줄), 상세는 파일로, concise/detailed 포맷, 25k 토큰 상한 | verify.sh "숫자 그대로" 원칙 있음. acceptance 출력 형식 통일 여부 미집계 | **run-acceptance.sh 출력 계약**: 1줄 요약(`PASS/FAIL/NOT_RUN n/m`) + 상세는 `artifacts/` 파일. humansearch observe 출력도 동일 | ★★ |
| 14 Code execution with MCP · 13 Advanced tool use | 중간 결과를 모델에 통과시키지 말고 코드에서 필터, **PII 토큰화**([NAME_1],[EMAIL_1]) 후 모델에 노출 | 후보자 개인정보가 핵심 데이터. v4에서 RLS 방치로 5테이블 노출(P9②) | **PII 토큰화 레이어**: 스크랩 결과를 LLM(채점·요약)에 넘기기 전 이름·이메일·전화를 토큰화, 역매핑은 실행 환경에만. P14(판정 수치는 코드가 만든다)와 결합 | ★★★ |
| 2 Containment · 5 Auto mode · 15 Sandboxing · 4 Managed agents | 확률적 방어 위에 **결정론적 경계**. allowlist는 "capability grant". 자격증명은 샌드박스에 아예 넣지 않는다. brain/hands 분리 `execute(name,input)→str`, 세션 로그는 append-only 외부 | P8 lease·P17·P18·§1-B 5조(드라이버 포트 감싸기) 정합. 브라우저 세션 쿠키·로그인 자격증명 저장 위치 계약 미명문 | **자격증명 경계 계약**: 사이트 쿠키·토큰은 에이전트 읽기 경로 밖(키체인/러너 전용), egress allowlist = saramin/jobkorea/linkedin/supabase만. humansearch 이벤트 로그를 append-only WAL로(P9 write-ahead 일반화) | ★★ |
| 3 Claude Code postmortem (4/23) | 프롬프트 한 줄이 평가 3% 하락. **변경마다 라인 단위 ablation, 모델별 게이팅, soak** | check-strict-principles-skills.sh가 SKILL.md 동기화는 검사. 프롬프트 변경 효과 측정 없음 | **프롬프트·스킬 변경 = 검사 변경**: P13 범위에 `.claude/skills/**`·strict 프롬프트 포함, 변경 PR은 20과제 평가 전후 수치 첨부 | ★★ |
| 7 Eval awareness | 평가 무결성은 설계 시점이 아니라 **지속적 적대 문제**. 카나리 문자열, URL 블록리스트는 무력 | 뮤테이션 테스트 5종 존재(P13⑥). fixture·기대값이 저장소에 있어 에이전트가 grep으로 맞출 수 있음 | **홀드아웃 fixture**: 일부 기대값을 CI secret/별도 저장소로, 저장소 fixture에 카나리 태그 | ★ |
| 9 Infrastructure noise | 리소스 request/limit 분리, 멀티플라이어 명시, 3%p 미만 차이는 노이즈 | CI 타임아웃·브라우저 지연이 NOT_RUN을 만드는지 미집계 | CI job에 timeout/메모리 상한을 기록 필드로, NOT_RUN 원인 코드 분류(P3·P20) | ★ |
| 22 Multi-agent research | 노력 배분 규칙(단순 1에이전트 3~10호출 / 비교 2~4 / 복잡 10+), 위임 4요소, 결과(end-state) 평가 | strict L0~L3 적응형 등급 존재 | strict 등급에 **에이전트 수·호출 예산**을 명시(L0 단일, L2 V1+V2, L3 10+). 서브에이전트 산출물은 파일 저장 + 참조만 반환(이미 2026-10-31 실측: 결과가 "완료." 한 줄로 유실됨) | ★★ |
| 24 Think tool | 정책 많은 순차 결정에서 행동 전 체크리스트(규칙 나열→정보 충족→정책 준수→결과 정합) | 85점 이상 자동 발송, 캡차·점유 게이트 등 정책 집약적 | 발송 직전 think 체크리스트를 humansearch 계약에 명문화(규칙 4항목) | ★ |
| 10 AI-resistant evals | 훈련데이터와 겹치는 과제는 AI가 푼다. 새 규칙 체계·도구 미제공·결정적 채점 | (제품 외) 밸류커넥트 고객사 채용 과제 설계 | **사업 적용점**: 고객사 기술 과제를 Zachtronics형 퍼즐로 재설계하는 컨설팅 상품 가능 | 참고 |
| 18 Postmortem 3 issues | 노이즈 많은 평가 의존이 탐지를 늦춤. 프로덕션 연속 평가 | P10(사업 결과를 매일 박스 밖으로) | P10 감시자에 "세션당 성공률·NOT_RUN율" 추가 | ★ |
| 20 Desktop Extensions · 21 Confidential inference | 비개발자 1클릭 설치 / TCB 최소화 | kcs·dev 비개발 사용자 | humansearch 조회 기능을 .mcpb로 패키징(장기). TCB 최소화는 P17과 동일 | 낮음 |
| 23 Claude Code best practices | 탐색→계획→코딩→커밋, TDD 명시, `/clear`, 워크트리 병렬, 헤드리스 fan-out | harness 게이트 0~6과 동일 철학 | 유지. 헤드리스 `claude -p` fan-out으로 acceptance 뮤테이션 검사 병렬화 | 유지 |

---

## PART C. v6 방법론 정립 — 5개 축

### C-1. 처리량: "병합은 사람 1명"을 깨지 않고 분모를 줄인다
1. **PR 3분류 자동 라벨**(경로 기반, CI): `docs-only` / `evidence-fixture` / `product-or-contract`. 앞 둘은 CI 초록 + 48h 무이의 시 자동 병합 허용. 뒤는 오너 필독 유지.
2. **판정서·증거는 PR 본문이 아니라 `docs/engineering/verdicts/` 별도 PR**(진단 AC-2 그대로).
3. **워크트리 TTL 48h**: `make red-ledger`가 초과 워크트리를 빨간불로 센다(AC-3).
- 검증 명령: `gh pr list --state open --json number -q 'length'` ≤ 4 (7일 내).

### C-2. 하네스 계약: 세션을 넘어 살아남는 파일 3개
- `features.json`(제품별, passes만 변경), `init.sh`(워크트리별), `claude-progress.txt`(세션별 append).
- 세션 시작 규칙: pwd → git log·progress 읽기 → features에서 미완료 1개 → init.sh로 기동·기본 e2e 먼저 → 1개 구현 → 자기검증 → passes:true → 커밋.
- **하네스 부품 감사(분기 1회)**: 게이트별 실제 RED 발생 횟수 집계 → 0회 부품 제거 또는 병합. 새 모델 도입 시 재실행.

### C-3. 안전 경계: 확률 위에 결정론
- 자격증명 경로 계약(에이전트 읽기 불가), egress allowlist(capability grant 관점), PII 토큰화 레이어, 이벤트 로그 append-only.
- 모든 항목은 P8·P9·P17·P18의 "기계 장치" 열에 파일 경로로 기입(P1: 장치 없는 원칙은 삭제).

### C-4. 평가: 20~50 과제에서 시작, 숫자로만 말한다
- L0 인증화면 분류 회귀셋(실캡처 20~50) → pass^3.
- 프롬프트·스킬 변경은 평가 전후 수치 첨부 없이는 머지 불가(P13 확장).
- 홀드아웃 fixture + 카나리.

### C-5. 형식성 강화(포멀 검증의 현실적 단계)
- 순수 판정 함수에 `icontract` 계약 + `hypothesis` + **CrossHair** CI 레인(반례 탐색).
- 파서·분류기에 실캡처 코퍼스 퍼징(예외·None 전파 0건을 스펙으로).
- 계약(`contracts/*.json`) 변경은 단독 커밋 + 변경 필드 자동 노출.

---

## PART D. 실행 순서 제안(각각 인수 기준 1개 = 워크트리 1개)
1. `merge-tiering`: 경로 기반 PR 라벨 CI + git-workflow.md 개정 — AC: docs-only PR이 CI 초록 후 자동 병합된 사례 1건.
2. `features-json`: HumanSearch features.json + init.sh + progress 계약 — AC: 새 세션이 progress만 읽고 다음 기능 1개를 고른 로그.
3. `l0-eval-set`: 실캡처 20개 + pass^3 스크립트 — AC: verify.sh 출력에 `L0 pass^3 = n/20`.
4. `pii-tokenize`: LLM 입력 전 토큰화 레이어 — AC: 네트워크 차단 레인에서 원문 이름이 LLM 요청 바디에 0건.
5. `gate-audit`: acceptance 29개의 실PR RED 횟수 집계 스크립트 — AC: 집계표 출력, 0회 게이트 목록.
6. `contracts-crosshair`: status_codes/weekly_window 계약 + CrossHair 레인 — AC: CI에서 반례 0건 또는 반례 1건을 RED로 보고.

## 출처
- 24편 요약: `evidence/harness-audit-20261031/anthropic-articles-{01-08,09-16,17-24}.md` (아티클별 원문 인용 포함)
- 포멀 검증: anthropic.com/research/formal-verification · 부록 PDF(www-cdn.anthropic.com/files/4zrzovbb/website/6867eadf760258fa8b42a504600cd3c036d16358.pdf) · github.com/theorem-labs/oss-verify-proofs · github.com/theorem-labs/oss-verify (.claude/skills/add-project/SKILL.md) · theorem.dev/blog/verified-software-stack · theorem.dev/oss-verify · github.com/libexpat/libexpat/pull/1272 · lwn.net/Articles/1097401
- v6 실측: docs/sot/coding-principles.md, strict-workflow.md, principles.yaml, docs/engineering/throughput-architecture-diagnosis-goal-2026-08-27.md, scripts/, humansearch/src
