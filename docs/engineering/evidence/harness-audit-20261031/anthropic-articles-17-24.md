# Anthropic Engineering 아티클 요약 보고서 (C: 17~24번)

작성일: 2026-10-31
조사 방법: 각 URL을 WebFetch로 2회(전문 요약 + 세부 수치·인용 추출) 읽어 정리하였다. 원문 인용은 영문 그대로 옮겼다.

---

## 17. Effective context engineering for AI agents
URL: https://www.anthropic.com/research/effective-context-engineering-for-ai-agents

### (1) 핵심 주장
- 프롬프트 엔지니어링의 다음 단계는 "컨텍스트 엔지니어링"이다. 프롬프트 문구뿐 아니라 시스템 프롬프트·도구·외부 데이터·메시지 이력 등 추론 시점에 컨텍스트 창에 들어가는 모든 토큰을 큐레이션하는 활동으로 정의된다.
- 컨텍스트는 유한한 자원이며 한계효용이 체감한다. 토큰이 늘수록 회상 정확도가 떨어지는 "context rot" 현상이 모든 모델에서 관찰되며, 이는 트랜스포머의 n² 쌍별 어텐션 구조와 장문 학습 데이터 부족에 기인한다.
- 좋은 컨텍스트의 구성 요소는 "적절한 고도(right altitude)"의 시스템 프롬프트, 겹침 없는 토큰 효율적 도구, 소수의 다양하고 전형적인 예시다.
- 검색은 사전 임베딩 검색(RAG)에서 에이전트가 파일 경로·쿼리·링크 같은 가벼운 식별자만 들고 필요할 때 도구로 불러오는 "just-in-time" 검색으로 이동하고 있다. 폴더 구조·파일명·타임스탬프 같은 메타데이터 자체가 신호가 된다.
- 장기 과업에는 압축(compaction), 구조화된 메모(structured note-taking), 서브에이전트 아키텍처 세 가지 기법이 있으며, 과업 성격에 따라 선택한다.
- 지도 원리는 "원하는 결과의 확률을 최대화하는 가장 작은 고신호 토큰 집합"을 찾는 것이며, 동작하는 가장 단순한 방법을 쓰라고 권고한다. 모델이 똑똑해질수록 규범적 엔지니어링은 줄어들 것으로 본다.

### (2) 구체적 방법론·패턴·수치
- 시스템 프롬프트의 두 가지 실패 모드: ① 취약한 하드코딩 if-else 로직 ② 구체적 신호가 없는 모호한 고수준 지침. 중간 지대를 찾되, XML 태그나 Markdown 헤더로 섹션을 구분한다. "최고 모델에서 최소 프롬프트로 시작 → 관찰된 실패를 근거로 지침·예시 추가". 최소(minimal)는 짧다(short)는 뜻이 아니다.
- 도구 설계 체크리스트: 토큰 효율적, 자기완결적, 오류에 견고, 기능 중복 최소화. "사람이 어떤 도구를 쓸지 명확히 고를 수 없으면 에이전트도 못 고른다".
- 예시(few-shot): 엣지케이스 규칙 목록을 쌓지 말고 소수의 다양하고 전형적인 예시를 사용한다.
- Just-in-time 검색의 Claude Code 실례: 대규모 DB를 전체 로드하지 않고 타깃 쿼리와 `head`/`tail` 같은 Bash 명령으로 분석, `glob`/`grep`으로 파일을 탐색·필요 시 로드. 단 `CLAUDE.md`는 사전 로드. 법률·금융처럼 덜 동적인 도메인에는 사전 검색+자율 탐색의 하이브리드를 권장.
- 압축(Compaction): Claude Code는 아키텍처 결정·미해결 버그·구현 세부를 보존하고, 중복 도구 출력은 버리며, 최근 접근 파일 5개를 유지. 튜닝 순서는 "재현율(recall) 먼저, 그다음 정밀도". 가장 가벼운 형태는 "tool result clearing"(오래된 도구 원시 출력 제거)으로 Developer Platform에 출시.
- 구조화된 메모: Claude Code의 할 일 목록, 커스텀 에이전트의 `NOTES.md`. 포켓몬 사례에서 1,234스텝 이상에 걸쳐 "피카츄 8레벨 상승/목표 10" 같은 정밀 집계와 지도·전투 전략 메모를 컨텍스트 리셋을 넘어 유지. Sonnet 4.5와 함께 파일 기반 memory tool 공개 베타 출시.
- 서브에이전트: 탐색에 수만 토큰을 쓰더라도 리드에게는 약 1,000~2,000 토큰의 압축 요약만 반환.
- 선택 기준: 긴 대화형 → 압축 / 마일스톤 있는 반복 개발 → 메모 / 병렬 탐색이 유리한 리서치 → 멀티 에이전트.

### (3) 원문 인용
- "Context, therefore, must be treated as a finite resource with diminishing marginal returns."
- "...finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."
- "For an LLM, examples are the 'pictures' worth a thousand words."

---

## 18. A postmortem of three recent issues
URL: https://www.anthropic.com/research/a-postmortem-of-three-recent-issues

### (1) 핵심 주장
- 2025년 8월~9월 초 Claude 응답 품질 저하는 수요·시간대·서버 부하에 따른 의도적 품질 조절이 아니라 세 개의 서로 겹친 인프라 버그 때문이었다.
- 버그 1: Sonnet 4 요청 일부가 1M 컨텍스트용 서버로 잘못 라우팅되었고, 8/29 로드밸런싱 변경으로 악화되어 최악 시간대에는 16%에 달했다. 라우팅이 "sticky"하여 후속 요청도 계속 잘못된 서버로 갔다.
- 버그 2: TPU 서버 설정 오류로 토큰 생성이 손상되어 영어 답변에 태국어·중국어 문자가 섞이거나 코드에 문법 오류가 발생했다.
- 버그 3: 토큰 선택 로직 변경이 XLA:TPU 컴파일러의 approximate top-k 잠재 버그를 노출시켰다. 2024년 12월의 임시 우회책이 그동안 이 버그를 가려왔다.
- 탐지가 어려웠던 이유는 평가가 저하를 포착하지 못했고(Claude가 개별 실수에서 자주 회복), 프라이버시 통제로 엔지니어가 사용자 대화에 접근할 수 없었으며, 플랫폼마다 증상이 달랐고, 노이즈가 많은 평가에 과도하게 의존했기 때문이다.
- 개선책으로 더 민감한 평가, 프로덕션 상시 품질 평가, 프라이버시를 지키는 커뮤니티 피드백 디버깅 도구를 약속했다.

### (2) 구체적 방법론·패턴·수치
- 타임라인(2025):
  - 8/5 버그1 시작, Sonnet 4 요청의 0.8% 오라우팅. 8/12 Bedrock에서 0.18% 피크. 8/27~9/16 Vertex AI는 0.0004% 미만.
  - 8/25 버그2(출력 손상) 발생: Opus 4.1·Opus 4는 8/25~8/28, Sonnet 4는 8/25~9/2 영향. 서드파티 플랫폼은 영향 없음. 9/2 롤백.
  - 8/25 버그3(approximate top-k) 트리거: Haiku 3.5 확인, Sonnet 4·Opus 3 가능성. 9/4 Haiku 3.5 롤백, 9/12 Opus 3 롤백, Sonnet 4는 재현 불가였으나 예방적 롤백. exact top-k + 정밀도 강화로 전환.
  - 8/29 로드밸런싱 변경 → 8/31 최악 시간대 Sonnet 4 요청 16% 영향. 해당 기간 Claude Code 사용자 약 30%가 최소 1건 오라우팅 경험.
  - 9/4 라우팅 수정 배포, 9/16 1P·Vertex AI 롤아웃 완료, 9/18 Bedrock 완료.
- 하드웨어 플랫폼: AWS Trainium, NVIDIA GPU, Google TPU 세 종류에서 동일 모델을 서빙하므로 플랫폼별 증상이 달랐다.
- 재발 방지 체크리스트: ① 정상/고장 구현을 구분할 만큼 민감한 평가 개발 ② 정기 테스트가 아닌 프로덕션 시스템에서 연속 품질 평가 ③ 프라이버시 보존형 피드백 디버깅 인프라 구축(향후 사고 시 재사용). 예외 문자 탐지 테스트도 추가.
- 사용자 피드백 채널: Claude Code `/bug`, 앱 thumbs-down, feedback@anthropic.com.
- 실무 교훈: "Claude가 자체 회복하는 특성"이 평가 민감도를 떨어뜨리므로, 개별 응답이 아니라 세션 단위·플랫폼 단위로 품질 지표를 분리해 모니터링해야 한다.

### (3) 원문 인용
- "We never reduce model quality due to demand, time of day, or server load."
- "More fundamentally, we relied too heavily on noisy evaluations."
- "We'll develop infrastructure and tooling to better debug community-sourced feedback without sacrificing user privacy."

---

## 19. Writing effective tools for agents — with agents
URL: https://www.anthropic.com/research/writing-tools-for-agents

### (1) 핵심 주장
- 에이전트용 도구는 개발자용 함수·API와 다르게 설계해야 한다. 도구는 결정론적 시스템과 비결정론적 에이전트 사이의 계약이다.
- 도구 개발 루프: 프로토타입(로컬 MCP 서버/데스크톱 익스텐션으로 감싸 직접 사용) → 평가(검증 가능한 다단계 과업) → 분석(트랜스크립트 읽기) → 에이전트와 함께 반복 개선(평가 트랜스크립트를 Claude에 투입해 도구를 고치게 함, 홀드아웃 세트로 과적합 방지).
- 도구가 많다고 좋은 결과가 나오지 않는다. 모든 API 엔드포인트를 감싸지 말고 고영향 워크플로를 위한 소수의 통합 도구를 만든다.
- 도구는 네임스페이스로 묶고, 저수준 ID 대신 의미 있는 이름·필드를 반환하며, 페이지네이션·필터링·절단으로 토큰 효율을 확보하고, 오류 메시지는 실행 가능하게 쓴다.
- 도구 설명은 신입 팀원에게 설명하듯 암묵적 맥락을 명시적으로 쓴다. 설명의 작은 변경만으로도 큰 성능 변화가 나타난다.

### (2) 구체적 방법론·패턴·수치
- 통합(consolidation) 예시: `list_users`+`list_events`+`create_event` → `schedule_event`; `read_logs` → `search_logs`(관련 줄+주변 문맥만); `get_customer_by_id`+`list_transactions`+`list_notes` → `get_customer_context`; `list_contacts` 대신 `search_contacts`/`message_contact`.
- 네임스페이스: 서비스 접두(`asana_search`, `jira_search`), 서비스+리소스 접두(`asana_projects_search`, `asana_users_search`). 접두/접미 선택이 평가에 유의미한 차이를 내며 모델마다 다르므로 테스트한다.
- 응답 포맷 제어: `ResponseFormat` enum `DETAILED="detailed"` / `CONCISE="concise"`. 예시에서 detailed 206토큰 vs concise 72토큰. detailed는 후속 호출에 필요한 `thread_ts`, `channel_id`, `user_id`를 노출.
- 토큰 효율: 페이지네이션·범위 선택·필터·절단에 합리적 기본값. Claude Code는 도구 응답을 기본 25,000토큰으로 제한. 오류는 불투명한 코드·트레이스백 대신 실행 가능한 안내.
- 평가 과업 설계: 좋은 예 — "Jane과 Acme Corp 프로젝트 회의를 잡고 지난 회의록을 첨부하고 회의실을 예약", "3회 중복 결제된 고객 조사 + 로그 확인 + 다른 고객 영향 확인", "해지 고객 리텐션 제안 준비". 나쁜 예 — "Customer ID 45892의 해지 요청 찾기"(단일 스텝·과소 명세).
- 평가 메트릭 5종: 최상위 정확도, 도구 호출/과업 런타임, 총 도구 호출 수, 총 토큰 소비, 도구 오류.
- 분석 신호: 중복 호출이 많으면 페이지네이션/limit 조정, 파라미터 오류가 많으면 설명 명확화.
- 설명 작성: 파라미터명은 `user`가 아니라 `user_id`처럼 모호하지 않게. 특수 쿼리 포맷·전문 용어 등 암묵 지식을 명시. 설명 개선만으로 Claude Sonnet 3.5가 SWE-bench Verified SOTA를 달성했다고 언급.

### (3) 원문 인용
- "Tools are a new kind of software which reflects a contract between deterministic systems and non-deterministic agents."
- "More tools don't always lead to better outcomes."
- "Each evaluation prompt should be paired with a verifiable response or outcome."

---

## 20. Desktop Extensions: One-click MCP server installation
URL: https://www.anthropic.com/research/desktop-extensions

### (1) 핵심 주장
- 로컬 MCP 서버 설치는 개발자 도구·수동 JSON 편집·의존성 관리·GitHub 탐색이 필요해 비개발자에게 장벽이 컸다.
- Desktop Extensions(`.mcpb`, 구 `.dxt`)는 MCP 서버와 의존성을 하나의 ZIP으로 묶어 더블클릭 → Install 한 번으로 설치하게 한다.
- Claude Desktop이 Node.js 런타임 내장, 자동 업데이트, 입력 검증이 있는 설정 UI, API 키의 OS 키체인 저장을 담당한다.
- 스펙(0.1), 툴체인, 레퍼런스 코드, TypeScript 타입을 오픈소스로 공개했고, 큐레이션된 익스텐션 디렉터리를 Claude Desktop에 내장했다.
- 기업용으로 그룹 정책/MDM, 사전 설치, 블록리스트, 디렉터리 비활성화, 사설 디렉터리를 지원한다.

### (2) 구체적 방법론·패턴·수치
- 아카이브 레이아웃(Node 예): `manifest.json`(필수), `server/index.js`(엔트리), `node_modules/`(번들 의존성), `package.json`(선택), `icon.png`(선택).
- `manifest.json` 필드: `mcpb_version`, `name`, `version`, `description`, `author{name 필수}`, `server{type: node|python|binary, entry_point, mcp_config{command, args, env}}`, `tools`, `prompts`, `user_config`(항목에 `sensitive: true`면 OS 키체인 저장), `compatibility`(Claude Desktop 버전, 플랫폼 darwin/win32/linux, 런타임 버전). 선택 필드: display_name, long_description, repository, homepage, icon, screenshots, keywords, license.
- 템플릿 변수: `${__dirname}`(설치 디렉터리), `${user_config.<key>}`, `${arguments.<name>}`(프롬프트 인자), `${HOME}`, `${TEMP}`, `${TMPDIR}`.
- CLI: `npm install -g @anthropic-ai/mcpb` → `mcpb init`(`--yes`로 프롬프트 생략) → `mcpb pack`(매니페스트 검증 + `.mcpb` 생성). `npx @anthropic-ai/mcpb init|pack`도 가능.
- 제출 절차: ① 제출 폼 가이드라인 준수 ② Windows·macOS 양쪽 테스트 ③ 폼 제출 ④ Anthropic 팀의 품질·보안 리뷰.
- 2025년 9월 `.dxt` → `.mcpb`로 명칭 변경, 기존 `.dxt`는 계속 동작. 저장소: github.com/anthropics/dxt.
- 사례: 내부 팀이 PyBoy 게임보이 에뮬레이터를 익스텐션으로 패키징해 Claude가 게임을 플레이.

### (3) 원문 인용
- "That's it. No terminal, no configuration files, no dependency conflicts."
- "The only required file in a Desktop Extension is a manifest.json."
- "Desktop Extensions (.mcpb files) solve these problems by bundling an entire MCP server."

---

## 21. Confidential Inference via Trusted Virtual Machines
URL: https://www.anthropic.com/research/confidential-inference-trusted-vms

### (1) 핵심 주장
- Pattern Labs와 공동 작성한 초기 연구로, 암호화된 데이터를 "신뢰할 수 있음을 증명한 서버 안에서만" 처리하는 Confidential Inference 체계를 제안한다. 목표는 ① 모델 가중치를 강력한 공격자로부터 보호 ② 사용자 민감 데이터의 비공개를 증명 가능하게 하는 것이다.
- 원칙은 데이터가 처리되는 순간을 제외하고 항상 암호화 상태를 유지하고, 소프트웨어 보안을 증명(attestation)하는 신뢰 사슬이 키 접근을 통제하는 것이다.
- 평문이 존재하는 곳은 API Server(토큰화·요청 로직)와 Inference Server(가속기에서 모델 실행) 두 곳뿐이며, 가중치는 Inference Server만 받는다.
- Inference Server 대부분은 신뢰하지 않는 영역에 두고, 작은 "model loader and invoker"만 하이퍼바이저로 격리된 VM에서 신뢰 영역으로 실행한다. 로더가 올바르게 실행되기만 하면 나머지 시스템이 무엇을 하든 기밀성이 유지되도록 설계한다.
- 신뢰 판단은 결국 키서버에 귀속되며, 제3자 검증·독립 키서버, 가속기 칩 자체에 confidential computing 내장을 향후 방향으로 제시한다.

### (2) 구체적 방법론·패턴·수치
- 신뢰 환경 3요건: ① 하드웨어로 다른 워크로드와 격리된 암호화 메모리 ② 디버깅 기능 비활성화 ③ 올바른 코드가 실행 중이라는 암호학적 증명.
- ②·③은 TPM을 신뢰 루트로 하는 measured boot로 달성: 각 부팅 단계를 측정해 최종 해시(attestation)를 산출 → 키서버가 검증 후에만 복호화 키 방출.
- ①은 물리 공격·악성 하이퍼바이저 방어용이나, 가속기와 암호화 호스트 메모리 공유가 아직 보편화되지 않아 당분간 컴퓨트 제공자의 데이터센터·하이퍼바이저 보안에 의존.
- 로더 설계: 암호화 데이터 수신 → 복호화 → 가속기 전달 → 연산 호출 → 암호화 결과 반환. 모델 아키텍처에 무관한 "virtual accelerator"로 보이며, Anthropic의 보안 CI 서버가 서명한(복수 엔지니어 리뷰 필수) 프로그램만 수용.
- 요청 수명주기: 클라이언트 암호화 → API Server 복호화·처리·재암호화 → Inference Server는 암호문 유지, 로더 전달 시에만 복호화 → 완료 토큰은 로더에서 암호화되어 API Server 경유 반환. 가중치는 암호화 저장, 로더에서만 복호화, 로더 밖으로 절대 유출 안 함.
- 향후 안전장치: 평문 가중치 보유 서버의 이그레스 대역폭 제한, 안전 분류기 서명이 있어야 추론 실행. 참조 문헌: RAND "Securing AI Model Weights", NVIDIA H100 confidential computing.
- 실무 교훈: 신뢰 경계(TCB)를 최소 컴포넌트로 좁히고, 그 컴포넌트의 "올바른 실행"을 증명하는 데 투자하라는 보안 설계 패턴.

### (3) 원문 인용
- "It's therefore critical to establish that the loader is run correctly."
- "A keyserver can check this proof and only release decryption keys when the recipient has proven itself secure."
- "Hardware designers (who have not already done so) should consider incorporating confidential computing into their chips."

---

## 22. How we built our multi-agent research system
URL: https://www.anthropic.com/research/multi-agent-research-system

### (1) 핵심 주장
- 리서치는 개방적·경로 의존적이라 고정 파이프라인이 맞지 않으며, 학습하면서 방향을 바꾸는 에이전트가 적합하다.
- 오케스트레이터-워커 구조(Opus 4 리드 + Sonnet 4 서브에이전트)가 단일 Opus 4 대비 내부 평가에서 90.2% 우수했다. BrowseComp에서 토큰 사용량이 성능 분산의 80%를, 도구 호출 수·모델 선택까지 합치면 95%를 설명한다. 멀티 에이전트의 효과는 본질적으로 "문제를 풀 만큼 토큰을 쓰게 해주는 것"이다.
- 에이전트는 채팅 대비 약 4배, 멀티 에이전트는 약 15배 토큰을 쓰므로 고가치·병렬화 가능한 과업에만 적합하고, 공유 컨텍스트나 의존성이 많은 과업에는 부적합하다.
- 프롬프트는 엄격한 규칙보다 좋은 휴리스틱을 심는 데 집중하며, 서브에이전트에 상세 위임, 복잡도에 비례한 노력 배분, 넓게→좁게 검색, 병렬화가 핵심이다.
- 평가는 작게 시작(약 20개 쿼리), LLM 판정자 + 사람 테스트를 병행하고, 절차가 아니라 결과(end-state)를 평가한다.
- 프로덕션에서는 오류 누적, 상태 유지형 장기 실행, 배포 중단 문제를 체크포인트·재시도·전체 트레이싱·레인보우 배포로 다룬다.

### (2) 구체적 방법론·패턴·수치
- 아키텍처: 리드가 계획 → 메모리에 저장 → 서브에이전트 병렬 스폰 → 결과 종합 → 계속/종료 판단. 별도 CitationAgent가 최종 보고 전 인용 귀속.
- 노력 배분 규칙(프롬프트에 명시): 단순 사실 확인 = 에이전트 1개, 도구 호출 3~10회 / 직접 비교 = 서브에이전트 2~4개, 각 10~15회 / 복잡 리서치 = 서브에이전트 10개 이상, 책임 명확 분할.
- 위임 명세 4요소: 목표, 출력 형식, 사용할 도구·소스 지침, 과업 경계. 모호하면 중복 작업·공백 발생.
- 8대 프롬프트 원칙: ① 에이전트 시뮬레이션(콘솔에서 동일 프롬프트·도구로 단계별 관찰) ② 상세 위임 ③ 복잡도 비례 노력 ④ 도구별 고유 목적·명확 설명 ⑤ 모델이 도구 설명을 고치게 함(완료 시간 40% 단축) ⑥ 넓게→좁게 ⑦ 리드는 extended thinking으로 계획, 서브는 interleaved thinking으로 결과 평가 ⑧ 리드가 서브에이전트 3~5개 동시 스폰, 서브는 도구 3개 이상 병렬 호출(복잡 쿼리 리서치 시간 최대 90% 단축).
- 평가: 약 20개 쿼리로 큰 효과 조기 탐지. LLM 판정 루브릭 = 사실 정확성, 인용 정확성, 완전성, 소스 품질, 도구 효율. 단일 프롬프트로 0.0~1.0 점수 + pass/fail 출력이 사람 판단과 가장 일치. 사람 테스트가 SEO 콘텐츠팜 선호 문제를 발견 → 소스 품질 휴리스틱 추가.
- 프로덕션: 체크포인트에서 재개 + 재시도, 도구 실패를 에이전트에 알려 적응, 대화 내용 대신 의사결정 패턴 모니터링(프라이버시), 레인보우 배포(구·신 버전 병행 후 점진 전환), 동기식 서브에이전트 실행이 병목 → 비동기 전환 예정.
- 부록: 영속 상태를 바꾸는 에이전트는 최종 상태로 평가·복잡 워크플로는 체크포인트로 분할 / 장기 대화는 완료 단계 요약·외부 메모리 저장·새 서브에이전트에 핸드오프 / 서브에이전트 출력은 파일시스템에 저장하고 가벼운 참조만 리드에 전달(코드·보고서·시각화에 특히 유효).

### (3) 원문 인용
- "...outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval"
- "Multi-agent systems work mainly because they help spend enough tokens to solve the problem."
- "Our prompting strategy focuses on instilling good heuristics rather than rigid rules."

---

## 23. Claude Code: Best practices for agentic coding
URL: https://www.anthropic.com/research/claude-code-best-practices (저자 Boris Cherny, 현재는 유지보수 종료·공식 문서로 안내)

### (1) 핵심 주장
- Claude Code는 의도적으로 저수준·비규범적이어서, 환경 설정(`CLAUDE.md`, 허용 도구 목록, 커스텀 명령)을 다듬는 것이 성과를 좌우한다.
- 어려운 문제일수록 "탐색 → 계획 → 코딩 → 커밋"의 선후를 지켜야 한다. 탐색·계획 단계 없이 두면 Claude는 곧바로 코드부터 쓴다.
- 테스트 우선(TDD)과 시각적 반복(스크린샷) 등 Claude가 스스로 결과를 검증할 수 있는 목표를 주면 품질이 크게 오른다.
- 지시는 구체적으로, 이미지·파일 참조·URL을 적극 제공하고, 일찍 개입해 궤도를 수정하며, 작업 간 `/clear`로 컨텍스트를 비운다.
- 헤드리스 모드(`-p`)로 CI·훅·스크립트에 통합하고, 여러 Claude를 작성자/리뷰어 분리, git worktree 병렬, fan-out·파이프라인으로 조합한다.

### (2) 구체적 방법론·패턴·수치
- `CLAUDE.md` 예시 내용: Bash 명령(`npm run build`, `npm run typecheck`), 코드 스타일(ES module import/export, CommonJS require 금지, 가능하면 destructure), 워크플로(변경 묶음 후 typecheck, 전체 대신 단일 테스트 실행).
- `CLAUDE.md` 위치: 레포 루트(커밋 공유) 또는 `CLAUDE.local.md`(gitignore) / 상위 디렉터리(모노레포) / 하위 디렉터리(진입 시 온디맨드 로드) / `~/.claude/CLAUDE.md`(전 세션). `/init`로 자동 생성. `#` 키로 세션 중 지침 추가. 프롬프트 개선기로 다듬고 "IMPORTANT", "YOU MUST" 같은 강조어로 준수율 향상.
- 허용 도구 관리 4가지: 세션 중 "Always allow" / `/permissions` / `.claude/settings.json` 또는 `~/.claude.json` 편집 / `--allowedTools` CLI 플래그. GitHub 사용 시 `gh` CLI 설치.
- 커스텀 슬래시 명령: `.claude/commands/fix-github-issue.md` → `/project:fix-github-issue 1234`. `$ARGUMENTS`로 인자 전달. 단계: `gh`로 이슈 조회 → 이해 → 코드베이스 검색 → 수정 구현 → 테스트 작성·실행 → lint/typecheck → 커밋 메시지 → 푸시·PR. MCP는 프로젝트/전역/체크인 `.mcp.json` 세 수준.
- 탐색-계획-코딩-커밋: ① 파일 읽기(코드 작성 금지 명시, 서브에이전트 활용) ② 계획 요청 — "think" < "think hard" < "think harder" < "ultrathink"로 사고 예산 증가 ③ 계획을 문서/GitHub 이슈로 저장(체크포인트) ④ 구현·검증 ⑤ 커밋·PR.
- TDD: 기대 입출력 쌍으로 테스트 작성(TDD임을 명시해 mock 방지) → 실패 확인 → 테스트 커밋 → 테스트 수정 없이 통과 코드 반복 → (선택) 독립 서브에이전트로 과적합 점검 → 커밋.
- 시각 반복: Puppeteer MCP·iOS 시뮬레이터 MCP 또는 수동 스크린샷 → 목업 제공 → 구현 → 스크린샷 → 일치할 때까지 반복.
- Safe YOLO: `claude --dangerously-skip-permissions`는 인터넷 차단 컨테이너(레퍼런스 Docker Dev Container)에서만. 데이터 손실·프롬프트 인젝션 위험.
- 궤도 수정: Escape(컨텍스트 유지 중단), 더블 Escape(이전 프롬프트로 돌아가 편집), undo 요청. 큰 작업은 체크리스트·Markdown 스크래치패드. 데이터 입력은 붙여넣기·파이프·도구 호출·파일 읽기.
- 헤드리스: `claude -p "<prompt>"`, `--output-format stream-json`. 세션 간 비영속. 용도: 이슈 트리아지, 주관적 코드 리뷰어.
- 멀티 Claude: 작성자/리뷰어 분리(새 컨텍스트) / `git worktree add ../project-feature-a feature-a` → 해당 디렉터리에서 `claude` → 완료 후 `git worktree remove ../project-feature-a`, 워크트리당 터미널 탭 1개 / fan-out: 작업 목록 생성 후 각 항목에 `claude -p` + 제한된 allowedTools + OK/FAIL 반환 규약 / 파이프라인: `claude -p` 출력을 다음 명령에 파이프, JSON 출력 권장.

### (3) 원문 인용
- "Steps #1-#2 are crucial—without them, Claude tends to jump straight to coding a solution."
- "Claude can infer intent, but it can't read minds."
- "Headless mode does not persist between sessions."

---

## 24. The "think" tool: Enabling Claude to stop and think
URL: https://www.anthropic.com/research/claude-think-tool

### (1) 핵심 주장
- "think" 도구는 응답 도중(특히 도구 결과 수신 후) Claude가 멈춰 필요한 정보를 다 갖췄는지 점검하는 전용 스크래치패드다. 응답 시작 전에 사고하는 extended thinking과 구분된다.
- τ-Bench 항공 도메인에서 think 도구 + 최적화 프롬프트가 베이스라인 대비 pass^1을 크게 끌어올렸고(0.584 vs 0.332), 리테일에서는 프롬프트 없이도 0.812 vs 0.783으로 개선됐다.
- 효과가 큰 조건은 도구 출력 분석(백트래킹 가능성), 정책이 많은 환경, 비용이 큰 순차 의사결정이다. 단일/병렬 도구 호출이나 단순 지시 따르기에서는 이득이 없다.
- 어려운 도메인에서는 프롬프팅이 결정적이다. 도메인 특화 예시를 시스템 프롬프트에 넣어야 효과가 극대화된다.
- 추가 비용은 프롬프트 길이·출력 토큰 증가 정도로 하방 위험이 적다. 다만 현재 Anthropic은 대부분의 경우 extended thinking을 대신 권장한다고 주석을 달았다.

### (2) 구체적 방법론·패턴·수치
- 도구 정의: `name: "think"`, 필수 문자열 파라미터 `thought` 하나. 설명 요지 — "새 정보를 얻거나 상태를 바꾸지 않고, 복잡한 추론이나 스크래치 메모가 필요할 때 생각을 기록만 한다". SWE-bench 변형은 "버그 수정 브레인스토밍, 실패 테스트 대응" 지침 추가.
- 항공 최적화 시스템 프롬프트 패턴 — `## Using the think tool` 섹션: "도구 결과를 받은 뒤, 행동/응답 전에 스크래치패드로 사용" + 체크리스트 ① 적용 규칙 나열 ② 필요 정보 수집 여부 확인 ③ 계획 행동의 정책 준수 검증 ④ 도구 결과 정합성 확인. 예시 2개: 항공편 취소(신원·예약·시간 규칙·운항 상태 확인), 다인 예약(수하물 요금·결제수단 제한).
- τ-Bench 항공 pass^k(k=1~5): think+prompt 0.584/0.444/0.384/0.356/0.340, think 0.404/0.254/0.186/0.140/0.100, extended thinking 0.412/0.290/0.232/0.192/0.160, baseline 0.332/0.206/0.148/0.116/0.100. (본문은 0.570 vs 0.370으로 표기해 표와 불일치.)
- τ-Bench 리테일 pass^k: think(프롬프트 없음) 0.812/0.735/0.685/0.650/0.626, extended thinking 0.770/0.681/0.623/0.581/0.548, baseline 0.783/0.695/0.643/0.607/0.583.
- SWE-bench: think 변형이 SOTA 0.623에 기여. 표본 n=30(도구 있음) vs n=144(없음)에서 평균 1.6% 개선, p<.001. Claude 3.5 Sonnet(New)에서도 유사 이득.
- 사용 권장: ① 도구 출력 정밀 분석 ② 정책 집약 환경 ③ 순차 의사결정. 비권장: ① 비순차/단일/병렬 호출 ② 단순 지시 따르기.
- 베스트 프랙티스: ① 도메인 특화 예시(추론 상세도, 단계 분해, 의사결정 트리, 정보 완전성 체크) ② 길고 복잡한 지침은 도구 설명이 아니라 시스템 프롬프트에 ③ 어려운 에이전트 시나리오로 먼저 테스트 → 도메인 맞춤 정의 추가 → 사용 양상 모니터링·개선.

### (3) 원문 인용
- "Extended thinking is all about what Claude does before it starts generating a response."
- "Prompting matters significantly on difficult domains."
- "The best part is that adding this tool has minimal downside in terms of performance outcomes."

---

## 공통 시사점(8편 종합)
1. 컨텍스트·토큰은 예산이다: 최소 고신호 토큰(17), 도구 응답 25k 제한·concise/detailed 포맷(19), 서브에이전트는 1~2k 토큰 요약만 반환(17·22), `/clear`·압축(23·17).
2. 평가는 작게·일찍·민감하게: 20개 쿼리(22), 검증 가능한 다단계 과업+5 메트릭(19), 노이즈 많은 평가 의존이 사고 탐지를 늦춤(18), 프로덕션 연속 평가(18).
3. 도구·프롬프트 설명은 "신입에게 설명하듯" 명시적으로 쓰고, 모델 스스로 고치게 한다(19·22).
4. 자기검증 루프를 설계에 넣는다: TDD·스크린샷(23), think 체크리스트(24), end-state 평가(22).
5. 신뢰 경계는 좁게: 로더 하나만 신뢰(21), YOLO 모드는 격리 컨테이너에서만(23), 민감 설정은 OS 키체인(20).
