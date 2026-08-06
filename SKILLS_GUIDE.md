# /gptreview + /verify 스킬 사용 가이드

Valuehire v6에 적대적 코드 검증 스킬 2개가 추가되었습니다.

- `.claude/skills/gptreview/SKILL.md`
- `.claude/skills/verify/SKILL.md`

Claude Code가 프로젝트의 `.claude/skills/<이름>/SKILL.md`를 자동으로 인식합니다. 별도 설치 절차는 없습니다.

## 중요 — 이 스킬들은 Node.js 스크립트가 아닙니다

브라우저는 코드가 아니라 **Claude Code 세션 자신이 `mcp__claude-in-chrome__*` 도구를 직접 호출**해서 제어합니다.
`/verify`의 1단계(로컬 검증)만 실제 셸 스크립트(`local-checks.sh`)를 실행합니다.

## 스킬 1: `/gptreview` — ChatGPT 적대적 리뷰

```bash
/gptreview src/auth.ts          # 특정 파일
/gptreview                      # git diff 대상
```

### 흐름
1. 대상 코드 읽기 (파일 또는 git diff)
2. ChatGPT.com 탭 열기 (사용자의 기존 Chrome 세션 사용)
3. **로그인 확인** — 안 되어 있으면 사용자에게 직접 로그인 요청 (비밀번호는 Claude가 절대 입력하지 않음)
4. 적대적 리뷰 프롬프트 + 코드 자동 입력
5. 응답 생성 완료까지 대기 후 자동으로 텍스트 추출
6. `gptreview-<timestamp>.md`로 저장 + 핵심 지적사항 요약 보고

### 로그인 관련 정책
- claude-in-chrome은 사용자의 실제 Chrome 브라우저를 사용하므로, 평소 로그인되어 있으면 아무것도 할 필요 없습니다.
- 로그인이 필요한 경우, Claude는 **비밀번호를 입력하지 않습니다** (Anthropic 안전 정책상 예외 없음). 사용자가 브라우저에서 직접 로그인해야 합니다.
- `.env`에 `CHATGPT_EMAIL`/`CHATGPT_PASSWORD`가 있어도 이 값은 자동 로그인에 사용되지 않습니다 — 참고용으로만 로컬에 보관됩니다.

---

## 스킬 2: `/verify` — 종합 코드 검증

```bash
/verify                  # git 변경사항 전체
/verify src/auth.ts      # 특정 파일
/verify --quick          # 1단계(로컬 자동 검증)만
/verify --strict         # 2단계를 Opus architect로 심화
/verify --gpt            # 4단계(ChatGPT 리뷰) 포함
```

### 4단계

| 단계 | 내용 | 방식 |
|------|------|------|
| 1️⃣ 로컬 자동 검증 | 타입체크/린트/테스트/빌드/npm audit | 실제 셸 실행 (`local-checks.sh`), 설정 없으면 정직하게 스킵 |
| 2️⃣ Architect/품질 리뷰 | 구조·복잡도·리팩토링 | 실제 서브에이전트(`quality-reviewer` 또는 `--strict` 시 `architect`) 호출 |
| 3️⃣ Security 리뷰 | OWASP Top 10, 인증/인가 | 실제 서브에이전트(`security-reviewer`) 호출 |
| 4️⃣ ChatGPT 리뷰 | 적대적 비판 | `--gpt` 옵션 시에만, `/gptreview` 재사용 |

가짜 점수나 하드코딩된 결과는 없습니다. 설정이 없어 실행 못 한 검사는 "스킵"으로 표시되고 "통과"로 집계되지 않습니다.

### 판정 기준
- 1~3단계 중 하나라도 실패 → 🛑 배포 보류
- 4단계는 선택 사항이라 판정에 포함하지 않되, 발견 사항은 함께 제시

---

## 환경 변수 (`.env`, gitignore 처리됨 — 절대 커밋하지 않음)

`.env` 파일에 아래 키를 채워 넣는다. **실제 값은 문서/git에 적지 않는다:**

```env
CHATGPT_EMAIL=
CHATGPT_PASSWORD=
```

이 값들은 자동 로그인에 쓰이지 않습니다 (정책상 금지). 사용자가 수동 로그인 시 참고용으로만 로컬에 둡니다.
`.gitignore`의 `.env` 규칙으로 GitHub에는 올라가지 않습니다.

## 결과 파일

- `gptreview-<timestamp>.md` — ChatGPT 리뷰 결과
- 커밋하지 않으려면 `.gitignore`에 `gptreview-*.md` 추가 권장
