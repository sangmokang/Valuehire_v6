# Anthropic Engineering 아티클 정리 (B: 9~16번)

> 작성일: 2026-10-31. 각 아티클은 WebFetch로 원문을 읽고(요약 모델 경유, 전문 축어 복제는 불가하여 핵심 수치·구조·인용은 별도 추출) 보고서체로 정리함. 인용은 영문 원문 그대로임.

---

## 9. Quantifying infrastructure noise in agentic coding evals
- URL: https://www.anthropic.com/research/infrastructure-noise (2026-02-05)

### (1) 핵심 주장
- 에이전트 코딩 벤치마크 점수는 모델 능력뿐 아니라 **인프라 설정(메모리·CPU 상한, 시간 제한)** 만으로도 모델 간 순위 차이보다 큰 폭으로 움직인다.
- Terminal-Bench 2.0에서 가장 빡빡한 설정과 가장 느슨한(uncapped) 설정 사이의 점수 차이는 **6%p(p < 0.01)** 였다.
- 발단은 GKE(Google Kubernetes Engine)에서 Terminal-Bench 2.0을 돌렸을 때 리더보드와 점수가 맞지 않고, 최대 6%의 태스크가 pod 에러로 실패한 사건이었다. 원인은 태스크별 리소스 스펙을 "보장 하한"이자 "강제 상한"으로 동시에 적용해, 순간적 메모리 스파이크에 컨테이너가 OOM-kill 당한 것이었다.
- 리소스를 약 **3배(3x)** 까지 늘리는 구간은 인프라 불안정을 제거할 뿐 점수 차이는 노이즈 범위(p = 0.40)에 머물렀고, 3x를 넘어서면 에이전트가 전에 못 풀던 문제를 풀기 시작해 "측정 대상 자체"가 바뀐다.
- 빡빡한 한도는 가볍고 효율적인 전략을, 넉넉한 한도는 무거운 툴체인(예: 전체 Python 데이터 사이언스 스택 설치)을 쓰는 에이전트를 보상한다. 즉 리소스 설정은 벤치마크가 무엇을 재는지를 결정하는 변수다.
- 결론: 리소스 설정을 프롬프트 포맷·temperature처럼 **통제된 실험 변수**로 다루고 문서화해야 하며, 설정이 매칭되지 않은 리더보드의 **3%p 미만 차이는 회의적으로** 봐야 한다.

### (2) 구체적 방법론 / 수치
- 실험 설계: Terminal-Bench 2.0을 1x(엄격) → 3x → uncapped 등 6개 리소스 구성으로 실행.
  - 인프라 에러율: 1x **5.8%** → 3x **2.1%**(1x→3x 감소는 p < 0.001) → uncapped **0.5%**.
  - 성공률: 1x~3x 구간 차이 없음(p = 0.40); 3x→uncapped 구간에서 성공률 약 +4%p; 전체 1x→uncapped 약 **+6%p(p < 0.01)**.
  - 메모리 여유에 민감했던 태스크 예: `rstan-to-pystan`, `compile-compcert`, `bn-fit-modify`(후자는 넉넉한 한도에서만 전체 데이터 사이언스 스택 설치가 성공).
- 교차 검증: SWE-bench에서 RAM을 최대 5x까지 변화, **227문제 × 10샘플**. 점수는 단조 증가하나 5x와 1x 차이는 **1.54%p**에 그침(태스크 자체가 덜 리소스 집약적이어서 예상된 결과).
- 그 외 점수에 영향을 주는 변수(정량화는 안 됨): 시간 제한, 클러스터 상태, 동시 실행 수(concurrency), egress 대역폭, 시간대(API 지연).
- 실무 체크리스트(권고 그대로):
  1. 태스크별로 **보장 할당량(request)과 별도의 kill 임계값(limit)을 분리**해 지정한다. 하나의 값으로 고정하지 않는다.
  2. 하한과 상한에서의 점수가 서로 노이즈 범위 안에 들어오도록 band를 **보정(calibrate)** 한다. Terminal-Bench 2.0에서는 3x 상한이 인프라 에러를 약 2/3 줄이면서 점수 상승은 노이즈 안에 머물렀다.
  3. 사용한 **multiplier를 보고서에 명시**한다(벤치마크·태스크 분포에 따라 값이 달라짐).
  4. 공개 비교용 코딩 평가라면 **여러 시간대·여러 날**에 나눠 실행해 노이즈를 평균화한다.
  5. 리소스 설정을 실험 변수로 기록·통제한다.

### (3) 원문 인용
- "Two agents with different resource budgets and time limits aren't taking the same test."
- "The band between them should be calibrated so that scores at the floor and ceiling fall within noise of each other."
- "A few-point lead might signal a real capability gap—or it might just be a bigger VM."

---

## 10. Building AI-resistant technical evaluations
- URL: https://www.anthropic.com/research/AI-resistant-technical-evaluations (저자: Tristan Hume, 성능 최적화팀)

### (1) 핵심 주장
- 2023년 11월에 설계한 성능 엔지니어 채용용 take-home 테스트(1,000명 이상 응시, 수십 명 채용)가 Claude 세대가 올라갈 때마다 무력화되었고, 세 차례의 재설계 과정에서 "AI에 강건한 평가"의 조건이 드러났다.
- Claude가 강했던 이유는 문제가 **훈련 데이터에 풍부한 전형적 주제**(메모리 계층, bank conflict 등)와 맞닿아 있고, 명확한 목표 수치(target cycle count)가 주어지면 탐색을 끝까지 밀어붙일 수 있었기 때문이다.
- 반대로 모델이 막힌 지점은 "스스로 병목이라고 결론 내리고 멈추는" 경우였다. 사람이 목표 수치를 알려주자 다시 돌파구를 찾았다 — 즉 **정답 존재에 대한 확신**이 테스트 시간 연산(test-time compute)의 효율을 좌우한다.
- 최종적으로 효과가 있었던 설계는 **Zachtronics류 퍼즐**: 매우 작고 제약된 명령어 집합, 디버깅 도구 미제공, 최소 명령어 수로 채점. "새로운 일(novel work)을 시뮬레이션"하기 때문에 AI 저항성이 생긴다.
- 대가는 현실성(realism)이다. 실제 업무와 닮은 문제일수록 훈련 데이터와 겹쳐 AI가 잘 푼다. 저자는 "현실성은 더 이상 누릴 수 없는 사치일 수 있다"고 말한다.
- 무제한 시간에서는 여전히 사람이 모델을 앞설 수 있다는 점을 공개 챌린지(GitHub 공개 + 기준 점수)로 검증하고 있다.

### (2) 구체적 방법론 / 수치
- 원 테스트 구조: 가상 가속기(TPU 유사)의 Python 시뮬레이터 + hot-reload Perfetto trace로 모든 명령 시각화. 기능: 수동 관리 scratchpad 메모리, VLIW(병렬 연산 패킹), SIMD, 멀티코어. 딥러닝 특화 지식은 배제.
- 버전 변천:
  - v1(2024~): 4시간 제한. 2025년 5월 Claude 3.7 Sonnet이 이미 강세, 사전 공개 Opus 4가 거의 모든 인간보다 나은 해법 산출.
  - v2: 2시간으로 단축, 멀티코어 제거, 깊이 추가. 수개월 유효.
  - v3 돌파(Opus 4.5): 내부 test-time compute 하네스 + Claude Code로 실행. 2시간 안에 최고 인간 점수와 동률. 메모리 대역폭 병목이라 판단하고 멈췄으나, 목표 cycle 수를 주자 문제 구조를 이용한 트릭을 찾아냄.
- 재설계 시도:
  - 시도 1: bank conflict가 있는 데이터 전치 문제 → Claude가 "데이터 대신 연산을 전치"해 해결; 패치 버전도 extended thinking으로 해결. 교훈: 훈련 데이터가 풍부한 주제는 피해야 함.
  - 시도 2(현행): Zachtronics 스타일 퍼즐 여러 개. 극소 명령어 집합, 디버깅 도구 없음(스타터 코드는 유효성 검사만 수행, print 문 삽입이나 코딩 모델로 디버거 생성은 응시자 몫). 초기 중상 난이도 퍼즐에서 Claude 실패.
- 공개 벤치마크(clock cycles, 낮을수록 좋음):
  - 2164: Opus 4, 수 시간 test-time compute
  - 1790: Opus 4.5, 캐주얼 Claude Code 세션
  - 1579: Opus 4.5, 하네스 2시간
  - 1548: Sonnet 4.5, 2시간 훨씬 초과
  - 1487: Opus 4.5, 하네스 11.5시간
  - 1363: Opus 4.5, 개선된 하네스, 수 시간
  - 1487 미만 달성 시 performance-recruiting@anthropic.com 으로 코드+이력서 제출 가능.
- 실무로 옮길 평가 설계 체크리스트:
  1. 훈련 데이터에 흔한 교과서적 주제(캐시, 전치, 정렬 등) 중심 문제는 피한다.
  2. 도메인 고유의 **인공 명령어 집합/규칙**을 만들어 "새 일"을 강제한다.
  3. 디버깅·관측 도구를 제공하지 않아 **도구를 스스로 만드는 능력**을 평가 항목에 포함한다.
  4. 채점은 결정적 지표(명령어 수, cycle 수)로 한다.
  5. 재설계 때마다 최신 모델 + 하네스(시간 2h, 11h 등)로 **레드팀 측정**을 먼저 수행하고 기준 점수를 기록한다.
  6. 제한 시간을 짧게(2h) 잡아 "무제한 compute" 이점을 차단한다.

### (3) 원문 인용
- "Then it stopped, convinced it had hit an insurmountable memory bandwidth bottleneck."
- "The replacement works because it simulates novel work."
- "But realism may be a luxury we no longer have."

---

## 11. Demystifying evals for AI agents
- URL: https://www.anthropic.com/research/demystifying-evals-for-ai-agents (2026-01-09)

### (1) 핵심 주장
- 평가(eval)란 "입력을 주고 출력에 채점 로직을 적용하는 것"이며, 에이전트는 다중 턴·툴 호출·상태 변경을 수반하므로 단일 턴 모델보다 평가가 어렵다.
- 평가 없이는 사용자 불만 뒤에야 문제를 발견하는 반응적 루프에 갇힌다. 평가는 기준선, 회귀 테스트, 노이즈와 실제 회귀의 구분, 신규 모델 도입 가속을 제공한다.
- 채점기는 코드 기반(빠르고 객관적이나 경직), 모델 기반(유연하나 비결정적·보정 필요), 사람(최고 품질이나 느리고 비쌈)의 세 가지이며, **가능하면 결정적 채점기, 필요할 때 LLM 채점기**를 쓴다.
- 능력 평가(capability eval)는 낮은 통과율에서 시작해 "오를 언덕"을 주고, 회귀 평가(regression eval)는 100% 근처를 유지해 퇴보를 잡는다.
- 비결정성 때문에 여러 trial을 돌리고 pass@k(k번 중 1회 이상 성공)와 pass^k(k번 모두 성공)를 구분해 본다. 신뢰성이 중요한 제품은 pass^k를 봐야 한다.
- 좋은 태스크는 "두 도메인 전문가가 독립적으로 같은 pass/fail 판정에 도달하는" 태스크다. 채점기는 결과(outcome) 중심, 부분 점수 허용, 해킹 방지로 설계하고, 반드시 **트랜스크립트를 직접 읽어** 채점기를 검증한다.
- 자동 평가는 프로덕션 모니터링, A/B 테스트, 사용자 피드백, 수동 리뷰, 인간 연구와 함께 "스위스 치즈 모델"처럼 겹겹이 운용해야 한다.

### (2) 구체적 방법론 / 수치
- 용어: Task(입력+성공 기준), Trial(1회 시도), Grader(채점기, 태스크당 복수 가능), Transcript(전체 기록), Outcome(환경의 최종 상태), Evaluation harness(평가 실행 인프라), Agent harness(모델을 에이전트로 만드는 시스템).
- 채점기 하위 유형:
  - 코드 기반: string match(exact/regex/fuzzy), binary tests(fail-to-pass, pass-to-pass), static analysis(lint/type/security), outcome verification(state check), tool call verification, transcript analysis.
  - 모델 기반: rubric 채점, natural-language assertions, pairwise comparison, reference-based, multi-judge consensus.
  - 사람: SME 리뷰, crowdsourcing, spot-check sampling, A/B, inter-annotator agreement.
  - 스코어링: weighted / binary / hybrid.
- 수치 예: 시도당 성공률 75% → pass^3 ≈ 42%. CORE-Bench에서 정답 "96.124991…"에 "96.12"를 오답 처리한 경직 채점·태스크 버그를 고치자 점수 42% → 95%. Opus 4.5는 τ2-bench 항공 예약 태스크에서 정책 허점을 찾아 사용자에게 더 나은 결과를 냈는데도 "실패"로 채점됨(채점기가 결과 품질을 못 잡은 사례).
- 에이전트 유형별 가이드:
  - 코딩(SWE-bench Verified, Terminal-Bench): 단위 테스트 등 결정적 채점 + 코드 품질 휴리스틱/툴 사용·사용자 상호작용 rubric. 메트릭: turns, tool calls, tokens, latency. 예시 태스크: "비밀번호 빈 문자열 인증 우회 수정" — 결정적 테스트, LLM 코드품질 rubric, static analysis(ruff, mypy, bandit), 보안 로그 state check, 필수 tool call.
  - 대화형(τ-Bench, τ2-Bench): 검증 가능한 최종 상태 + 완료/상호작용 품질 rubric, 두 번째 LLM이 사용자 시뮬레이션. 예시: "화난 고객 환불" — 공감·근거 rubric, 티켓/환불 상태 state check, 환불 상한을 둔 필수 tool call, 최대 10턴.
  - 리서치(BrowseComp): groundedness(주장이 출처로 뒷받침), coverage(필수 사실 포함), source quality. 객관식은 exact match, 종합은 LLM judge를 전문가 판단에 보정.
  - 컴퓨터 사용(WebArena, OSWorld): 실제/샌드박스 환경에서 URL·페이지 상태·백엔드 데이터·파일시스템·앱 설정·UI 속성으로 결과 검증. DOM 기반은 빠르나 토큰 많이 듦, 스크린샷은 느리나 토큰 절약.
  - 균형 세트 예(Claude.ai 웹 검색): 검색을 해야 하는 쿼리(날씨)와 하면 안 되는 쿼리("who founded Apple?")를 모두 넣어 under/over-triggering을 동시에 측정.
- 8단계 로드맵(체크리스트):
  0. 일찍 시작 — 실제 실패에서 뽑은 **20~50개 태스크**면 충분.
  1. 수동 점검과 사용자 신고 실패에서 출발.
  2. 모호하지 않은 태스크 + 참조 해답 작성.
  3. 행동이 일어나야/일어나지 말아야 하는 케이스 모두 포함한 균형 세트.
  4. 격리된 안정적 환경의 견고한 하네스.
  5. 채점기 설계 — 엄격한 단계 순서보다 결과 중심, 부분 점수, 해킹 방지.
  6. 트랜스크립트 읽기.
  7. 포화(saturation) 감시.
  8. 명확한 소유권으로 스위트 유지보수.
- 언급된 프레임워크: Harbor, Braintrust, LangSmith, Langfuse, Arize(Phoenix, AX).

### (3) 원문 인용
- "A good task is one where two domain experts would independently reach the same pass/fail verdict."
- "You won't know if your graders are working well unless you read the transcripts and grades from many trials."
- "In reality, 20-50 simple tasks drawn from real failures is a great start."

---

## 12. Effective harnesses for long-running agents
- URL: https://www.anthropic.com/research/effective-harnesses-for-long-running-agents (2025-11-26, Justin Young)

### (1) 핵심 주장
- 장시간 작업하는 에이전트는 세션 단위로 일하며 새 세션은 이전 기억이 없다. 컨텍스트 compaction만으로는 부족하고, Opus 4.5를 단순 루프로 돌려도 고수준 프롬프트에서 프로덕션 품질 웹앱을 완성하지 못했다.
- 두 가지 실패 패턴: ① 앱 전체를 한 번에 만들려다 컨텍스트가 바닥나 반쯤 만든 미문서화 기능을 남김 ② 후속 에이전트가 기존 진행 상황을 보고 **너무 일찍 "완료" 선언**.
- 해법은 Claude Agent SDK 위의 2단 하네스: **Initializer 에이전트**(첫 실행, 환경·기능 목록·진행 로그·git 초기화)와 **Coding 에이전트**(매 세션 증분 진행 + 구조화된 업데이트). 두 에이전트는 초기 사용자 프롬프트만 다르고 시스템 프롬프트·툴·하네스는 동일하다.
- 기능 목록은 Markdown이 아닌 **JSON**으로 두어 모델이 임의로 고치거나 덮어쓰는 것을 막고, `passes` 필드만 변경 허용한다.
- 각 세션은 "클린 상태(main 브랜치에 머지 가능한 수준)"로 끝내고, git 커밋 + 진행 요약을 남겨 다음 세션이 복구·회귀 가능하게 한다.
- 브라우저 자동화(Puppeteer MCP)로 **사람처럼 end-to-end 테스트**하도록 프롬프트하자 성능이 크게 개선되었다. 다만 브라우저 네이티브 alert 모달은 못 봐서 관련 기능은 버그가 많았다.

### (2) 구체적 방법론 / 수치
- Initializer 산출물: `init.sh`(개발 서버 실행 스크립트), `claude-progress.txt`(에이전트 작업 로그), 초기 git commit, 기능 목록 JSON(claude.ai 클론에서 **200개 이상 기능**, 모두 초기값 failing).
- 기능 목록 JSON 스키마(엔트리당):
  - `category` (예: "functional")
  - `description` (자연어 기능 설명)
  - `steps` (수동 테스트 단계 순서 목록)
  - `passes` (boolean, 초기 false)
  - 규칙: 코딩 에이전트는 `passes`만 변경 가능. 테스트 삭제·수정 금지.
- Coding 에이전트 세션 시작 체크리스트(프롬프트 원문 구조):
  1. `pwd`로 작업 디렉터리 확인(이 디렉터리 안에서만 편집 가능).
  2. git log와 progress 파일을 읽어 최근 작업 파악.
  3. 기능 목록을 읽고 **미완료 중 최우선 기능 1개** 선택.
  4. `init.sh`로 개발 서버 기동 후 기본 end-to-end 테스트를 먼저 실행 → 깨진 상태면 새 기능 전에 먼저 복구.
  5. 기능 1개 구현 → 브라우저 자동화로 스스로 검증 → `passes: true` → 설명적 메시지로 git commit → `claude-progress.txt` 갱신.
- 실패 모드 ↔ 하네스 대응표:

| 문제 | Initializer | Coding agent |
|---|---|---|
| 너무 이른 완료 선언 | 구조화된 JSON 기능 목록 생성 | 목록을 읽고 기능 1개씩 진행 |
| 버그·미문서화 진행 상황 | git repo + progress 노트 작성 | 노트·로그 읽기, 테스트, 커밋, progress 갱신 |
| 기능을 조기에 완료 표시 | 기능 목록 세팅 | "passing" 전 자기 검증 |
| 앱 실행법 파악에 시간 낭비 | `init.sh` 작성 | 세션 시작 시 `init.sh` 읽기 |

- 향후 과제: 단일 범용 코딩 에이전트 vs 테스트/QA/정리 전담 에이전트 분리 중 어느 쪽이 나은지; 과학 연구·금융 모델링 등으로 일반화 가능성.

### (3) 원문 인용
- "Claude declares victory on the entire project too early."
- "we landed on using JSON for this, as the model is less likely to inappropriately change or overwrite JSON files"
- "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality."

---

## 13. Introducing advanced tool use on the Claude Developer Platform
- URL: https://www.anthropic.com/research/advanced-tool-use (2025-11-24)

### (1) 핵심 주장
- 에이전트는 수백~수천 개 툴에 접근해야 하지만, 모든 정의를 선적재하면 컨텍스트가 소모된다. 5개 MCP 서버·58개 툴 구성이 대화 시작 전 약 55K 토큰을 썼고, 내부 사례는 134K 토큰에 달했다.
- **Tool Search Tool**: `defer_loading: true`로 표시한 툴은 필요할 때 검색으로 로드. 툴 정의 토큰 약 85% 절감, Opus 4 MCP 평가 49%→74%, Opus 4.5 79.5%→88.1%.
- **Programmatic Tool Calling**: Claude가 코드 실행 환경에서 Python으로 툴을 호출·가공하고 최종 결과만 컨텍스트로 반환. 매 툴 호출마다 전체 추론 패스가 필요하던 문제와 중간 결과의 컨텍스트 오염을 동시에 해소. 복잡 리서치 태스크 평균 토큰 43,588→27,297(37% 감소).
- **Tool Use Examples**: JSON Schema가 표현 못 하는 사용 패턴(날짜 형식, ID 규약, 파라미터 상관관계)을 `input_examples`로 제공. 복잡 파라미터 정확도 72%→90%.
- 셋 다 베타이며 헤더 `advanced-tool-use-2025-11-20`이 필요하다. 가장 큰 병목(컨텍스트 비대/대형 중간 결과/파라미터 오류)부터 하나씩 적용하라는 것이 권고다.

### (2) 구체적 방법론 / 수치
- Tool Search Tool
  - 요청 구조:
    ```json
    {"tools": [
      {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
      {"name": "github.createPullRequest", "description": "Create a pull request",
       "input_schema": {...}, "defer_loading": true}
    ]}
    ```
  - 검색 방식: regex, BM25, 커스텀 검색 지원.
  - 수치: 5개 서버 58툴 ≈ 55K 토큰(GitHub 35툴 ≈26K, Slack 11 ≈21K, Sentry 5 ≈3K, Grafana 5 ≈3K, Splunk 2 ≈2K); Jira 단독 ≈17K; 전통 방식 50+ MCP 툴 ≈72K(작업 전 총 ≈77K) vs 검색 방식 선적재 ≈500토큰 + 필요 시 3~5툴 ≈3K = 총 ≈8.7K; 컨텍스트 보존 191,300 vs 122,800 토큰(95% 보존).
  - 적용 기준: 툴 정의 10K 토큰 초과, 툴 10개 이상, 다중 MCP 서버, 툴 선택 오류가 잦을 때. 10개 미만의 소형 툴을 매 세션 모두 쓰면 검색 단계 지연만 추가되어 비효율.
  - 운영 팁: 자주 쓰는 3~5개 툴은 항상 로드 유지; 검색은 name/description을 매칭하므로 명확한 이름·설명 작성.
- Programmatic Tool Calling
  - 요청 구조:
    ```json
    {"tools": [
      {"type": "code_execution_20250825", "name": "code_execution"},
      {"name": "get_expenses", "input_schema": {...},
       "allowed_callers": ["code_execution_20250825"]}
    ]}
    ```
  - 예시: 예산 준수 점검 — 팀원 20명 × 50~100 라인아이템(2,000+ 항목, 50KB+), 원본 200KB → 결과 1KB; 20+ 툴 호출 워크플로에서 19+ 추론 패스 제거; 50개 엔드포인트 점검, 10MB 로그 파일 처리.
  - 벤치마크: 내부 지식 검색 25.6%→28.5%, GIA 46.5%→51.2%. Claude for Excel이 대형 스프레드시트에 이 방식 사용.
  - 적용 기준: 요약만 필요한 대형 데이터셋, 3개 이상 의존 호출이 있는 다단계 워크플로, 결과 필터/변환, 다수 항목 병렬 처리. 단일 호출·소형 응답·모든 중간 결과를 Claude가 봐야 하는 경우엔 비추천.
  - 운영 팁: 툴의 **반환 포맷을 문서화**해야 Claude가 올바른 파싱 코드를 쓴다.
- Tool Use Examples
  - 요청 구조:
    ```json
    {"name": "create_ticket", "input_schema": {...},
     "input_examples": [
       {"title": "Login page returns 500 error", "priority": "critical",
        "labels": ["bug", "authentication"],
        "reporter": {"id": "USR-12345", "name": "Jane Smith"},
        "due_date": "2024-11-06",
        "escalation": {"level": 2, "notify_manager": true, "sla_hours": 4}},
       {"title": "Update API documentation"}
     ]}
    ```
  - 툴당 1~5개 예시 권장; 현실적인 데이터로 모호한 케이스(중첩 구조, 많은 선택 파라미터, 도메인 규약, 유사 툴 구분)에 집중. URL/이메일 같은 표준 포맷이나 JSON Schema로 검증되는 것엔 불필요(토큰만 늘어남).

### (3) 원문 인용
- "Claude only sees the tools it actually needs for the current task."
- "Each tool call requires a full model inference pass."
- "Agents also need to learn correct tool usage from examples, not just schema definitions."

---

## 14. Code execution with MCP: Building more efficient agents
- URL: https://www.anthropic.com/research/code-execution-with-mcp (2025-11-04)

### (1) 핵심 주장
- 다수 MCP 서버에 연결된 에이전트는 두 곳에서 토큰을 낭비한다: ① 모든 툴 정의를 선적재 ② 모든 중간 결과가 모델을 통과. 2시간짜리 영업 회의 트랜스크립트를 Google Drive에서 읽어 Salesforce에 쓰면 같은 내용이 모델을 두 번 지나 약 50,000토큰이 추가된다.
- 해법은 MCP 서버를 **파일시스템 트리 형태의 코드 API**(`./servers/google-drive/getDocument.ts` 등)로 노출하고, 에이전트가 필요한 정의만 읽어 코드를 작성·실행하게 하는 것. 토큰 150,000 → 2,000(98.7% 절감). Cloudflare는 같은 접근을 "Code Mode"라 부른다.
- 이점: 점진적 공개(progressive disclosure), 컨텍스트 효율적 결과(10,000행 중 5행만 노출), 코드 내 제어 흐름(루프·조건·에러 처리, TTFT 지연 감소), 프라이버시(중간 결과가 실행 환경에 머물고 PII 토큰화 가능), 상태 유지와 스킬 축적(`./workspace/`, `./skills/`).
- 비용: 에이전트가 생성한 코드를 실행하려면 안전한 샌드박스, 리소스 제한, 모니터링이 필요하며 직접 툴 호출에는 없는 운영 부담이 생긴다.

### (2) 구체적 방법론 / 수치
- 디렉터리 구조:
  ```
  servers/
  ├── google-drive/   getDocument.ts, ..., index.ts
  ├── salesforce/     updateRecord.ts, ..., index.ts
  └── ...
  ```
- 툴 래퍼 패턴(`./servers/google-drive/getDocument.ts`):
  ```typescript
  import { callMCPTool } from "../../../client.js";
  interface GetDocumentInput { documentId: string; }
  interface GetDocumentResponse { content: string; }
  /* Read a document from Google Drive */
  export async function getDocument(input: GetDocumentInput): Promise<GetDocumentResponse> {
    return callMCPTool<GetDocumentResponse>('google_drive__get_document', input);
  }
  ```
- 사용 예(트랜스크립트 → Salesforce): `gdrive.getDocument` 결과를 모델에 보여주지 않고 바로 `salesforce.updateRecord({objectType:'SalesMeeting', recordId, data:{Notes: transcript}})`에 전달.
- 점진적 공개: 파일시스템 탐색 또는 `search_tools` 툴(상세 수준 파라미터: 이름만 / 이름+설명 / 전체 스키마).
- 결과 필터링:
  ```typescript
  const allRows = await gdrive.getSheet({ sheetId: 'abc123' });
  const pendingOrders = allRows.filter(row => row["Status"] === 'pending');
  console.log(`Found ${pendingOrders.length} pending orders`);
  console.log(pendingOrders.slice(0, 5)); // 상위 5행만 노출
  ```
- 제어 흐름(폴링):
  ```typescript
  let found = false;
  while (!found) {
    const messages = await slack.getChannelHistory({ channel: 'C123456' });
    found = messages.some(m => m.text.includes('deployment complete'));
    if (!found) await new Promise(r => setTimeout(r, 5000));
  }
  ```
- PII 토큰화: MCP 클라이언트가 이메일·전화·이름을 `[EMAIL_1]`, `[PHONE_1]`, `[NAME_1]`로 치환해 모델에 보여주고, 실제 값은 실행 환경에서 Salesforce로 그대로 전달. 모델이 `sheet.rows`를 로그해도 토큰화된 값만 본다.
- 상태·스킬:
  - 중간 파일: `./workspace/leads.csv` 등.
  - 재사용 함수: `./skills/save-sheet-as-csv.ts`에 `saveSheetAsCsv(sheetId)` 저장 → 이후 실행에서 import. 여기에 `SKILL.md`를 추가하면 구조화된 스킬이 된다(Agent Skills와 연결).
- 실무 체크리스트:
  1. MCP 툴마다 타입 정의가 포함된 TS 래퍼 파일을 자동 생성해 `servers/<server>/<tool>.ts`로 배치.
  2. 에이전트에게 `ls`/`cat`/`search_tools`로 필요한 것만 읽게 지시.
  3. 큰 결과는 코드에서 필터·집계 후 `console.log`로 요약만 출력.
  4. 클라이언트 레벨 PII 토큰화 레이어 구현.
  5. 샌드박스·리소스 제한·모니터링을 함께 설계.

### (3) 원문 인용
- "Every intermediate result must pass through the model."
- "Models are great at navigating filesystems."
- "Note that code execution introduces its own complexity."

---

## 15. Beyond permission prompts: making Claude Code more secure and autonomous
- URL: https://www.anthropic.com/research/claude-code-sandboxing (2025-10-20)

### (1) 핵심 주장
- Claude Code는 기본 read-only이며 파일 수정·명령 실행 전 승인을 요구하지만, 잦은 승인 요청은 **approval fatigue**를 낳아 사용자가 승인 내용을 검토하지 않게 만든다.
- 핵심 위협은 **prompt injection**이다. 샌드박스는 주입을 막는 것이 아니라 "주입이 성공해도 피해가 격리되도록" 설계된다.
- 샌드박스는 Claude가 자유롭게 행동할 수 있는 경계를 정하고, **파일시스템 격리**와 **네트워크 격리** 두 레이어로 강제한다. 하나만 있으면 뚫린다(네트워크 격리 없으면 SSH 키 유출, 파일시스템 격리 없으면 샌드박스 탈출 후 네트워크 접근).
- 내부 사용에서 샌드박스로 권한 프롬프트가 **84%** 감소했다.
- 샌드박스 런타임은 OS 기본 프리미티브(Linux bubblewrap, macOS seatbelt) 기반의 경량 구현으로 컨테이너가 필요 없고, 오픈소스(`anthropic-experimental/sandbox-runtime`)로 공개되었다. `/sandbox`로 활성화.
- Claude Code on the web은 세션마다 격리된 클라우드 샌드박스에서 돌며, git 자격증명과 서명 키를 샌드박스 밖에 두고 커스텀 프록시가 작업을 검증한 뒤 실제 토큰을 붙인다.

### (2) 구체적 방법론 / 수치
- 파일시스템 격리: 현재 작업 디렉터리에 읽기/쓰기 허용, 그 밖은 변경 차단. 특정 경로를 allow/deny 리스트로 커스터마이즈 가능.
- 네트워크 격리: 모든 인터넷 접근을 **Unix domain socket → 샌드박스 외부 프록시**로 라우팅. 프록시가 프로세스별 접근 가능 도메인을 확인하고 새 도메인은 사용자 확인 요청. 프록시를 커스터마이즈해 자체 egress 규칙 적용 가능.
- 자식 프로세스 포함: 명령이 띄우는 스크립트·프로그램·서브프로세스에도 OS 수준 제한이 동일 적용.
- 차단 시 UX: 샌드박스 밖 접근 시도가 있으면 즉시 사용자에게 알리고 허용 여부를 선택하게 함.
- 웹 버전의 git 보호 흐름:
  1. 샌드박스 내부 git 클라이언트는 **scoped credential**로 프록시에 인증.
  2. 프록시가 자격증명과 git 작업을 검증(예: 설정된 브랜치로만 push).
  3. 검증 통과 시 실제 토큰을 붙여 GitHub로 전달.
- 상태: 베타/리서치 프리뷰.
- 실무 적용 체크리스트:
  1. `/sandbox`로 활성화 후 허용 디렉터리·도메인 allowlist를 최소로 시작.
  2. 패키지 레지스트리 등 반복 승인 도메인은 allowlist에 추가하고 나머지는 프롬프트 유지.
  3. 비밀(SSH 키, 토큰)은 작업 디렉터리 밖에 두어 파일시스템 격리의 보호를 받게 함.
  4. CI/원격 실행에서는 자격증명을 프록시 측에 두고 scoped credential + 작업 검증 패턴을 모방.

### (3) 원문 인용
- "In our internal usage, we've found that sandboxing safely reduces permission prompts by 84%."
- "Sandboxing ensures that even a successful prompt injection is fully isolated, and cannot impact overall user security."
- "This way, even if the code running in the sandbox is compromised, the user is kept safe from further harm."

---

## 16. Equipping agents for the real world with Agent Skills
- URL: https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills (2025-10-16, Barry Zhang·Keith Lazuka·Mahesh Murag)

### (1) 핵심 주장
- Agent Skill은 에이전트가 동적으로 발견·로드하는 **지시·스크립트·리소스의 폴더**로, 신입 사원 온보딩 가이드에 비유된다. 이후 크로스 플랫폼 이식성을 위한 **오픈 표준**으로 공개되었다.
- 가장 단순한 스킬은 `SKILL.md` 하나를 담은 디렉터리이며, 파일은 `name`·`description` 필수 필드를 가진 YAML frontmatter로 시작한다.
- 핵심 설계 원리는 **점진적 공개(progressive disclosure)**: ① 시작 시 모든 스킬의 name/description만 시스템 프롬프트에 선적재 ② 관련 있어 보이면 `SKILL.md` 본문 읽기 ③ 필요 시 링크된 추가 파일만 열기. 이로써 컨텍스트 창에 들어가는 양을 필요한 만큼으로 제한한다.
- 스킬은 Claude가 재량으로 실행하는 **코드**를 포함할 수 있다. 결정적 코드는 반복 가능하며, 토큰 생성으로 정렬하는 것보다 정렬 알고리즘 실행이 훨씬 싸다.
- 개발 방법은 평가에서 시작해, 규모에 맞게 분할 구조화하고, Claude의 관점에서 name/description을 다듬고, Claude와 함께 반복 개선하는 것이다.
- 스킬은 취약점을 들여오거나 데이터 유출을 지시할 수 있으므로 신뢰할 수 있는 출처에서만 설치하고, 덜 신뢰되는 스킬은 의존성·번들 리소스·외부 네트워크 접속 지시를 감사한다.

### (2) 구체적 방법론 / 수치
- 파일 구조 예(PDF 스킬):
  - `pdf/SKILL.md` — 핵심 지시. frontmatter: `name`, `description`(필수).
  - `reference.md` — 참조 문서(링크).
  - `forms.md` — 폼 채우기 지시(폼 작업 때만 로드되도록 분리).
  - 사전 작성된 Python 스크립트 — PDF의 모든 폼 필드 추출. 스크립트나 PDF를 컨텍스트에 올리지 않고 실행만 한다.
- 컨텍스트 창 흐름 4단계: 시스템 프롬프트 + 전체 스킬 메타데이터 + 사용자 메시지 → Bash 툴로 `pdf/SKILL.md` 읽기 → 필요하면 `forms.md` 읽기 → 로드된 지시로 작업 수행.
- 스킬 개발·평가 절차:
  1. **평가 우선**: 대표 태스크에서 에이전트를 돌려 취약 지점을 찾고 그 지점을 메우는 스킬을 증분으로 작성.
  2. **규모를 위한 구조화**: 큰 `SKILL.md`는 참조 파일로 분할; 함께 쓰이지 않는 컨텍스트는 별도 경로로 분리해 토큰 절감; 코드는 "실행할 것"과 "읽을 것"을 명확히 표시.
  3. **Claude 관점에서 생각**: 실제 사용을 관찰하고, 트리거 판단의 근거인 `name`·`description`을 특히 신경 쓴다.
  4. **Claude와 반복**: 성공 패턴과 흔한 실수를 Claude가 스킬에 기록하게 하고, 이탈 시 자기 성찰 요청.
- 보안 체크리스트: 신뢰 출처만 설치 / 번들 파일(이미지·스크립트) 전부 읽기 / 코드 의존성 점검 / 외부 네트워크 접속을 지시하는 문구·코드 탐지.
- 지원 범위: Claude.ai, Claude Code, Claude Agent SDK, Claude Developer Platform. 향후 스킬 생성·편집·발견·공유 라이프사이클 전체 지원, MCP 서버와의 보완 관계 탐색, 장기적으로는 에이전트가 스스로 스킬을 만들고 평가하는 것을 목표로 한다.

### (3) 원문 인용
- "At its simplest, a skill is a directory that contains a `SKILL.md` file."
- "Progressive disclosure is the core design principle that makes Agent Skills flexible and scalable."
- "We recommend installing skills only from trusted sources."

---

## 종합: 8편을 관통하는 실무 패턴
1. **컨텍스트는 희소 자원** — 툴 정의(Tool Search), 중간 결과(Programmatic Tool Calling / Code Mode), 지시문(Skills의 점진적 공개) 모두 "필요할 때만 로드"로 수렴한다.
2. **상태는 파일로 외부화** — `init.sh`, `claude-progress.txt`, JSON 기능 목록, `./workspace/`, `./skills/` 등 세션을 넘어 살아남는 파일이 장시간 에이전트의 기억이다.
3. **평가는 결과(outcome) 중심 + 트랜스크립트 정독** — 결정적 채점기 우선, LLM 채점기는 보정, 20~50개 실제 실패 태스크로 시작, 인프라 설정은 실험 변수로 명시.
4. **격리는 2중(파일시스템 + 네트워크)** — 코드 실행·스킬·샌드박스 모두 "주입이 성공해도 피해를 가둔다"는 전제로 설계한다.
