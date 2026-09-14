# 다른 PC에서 이어서 하기 — 정정판 (2026-09-14 16:10 KST, Codex 적대 검증 반영)

이 문서가 2026-09-14 인수인계 메일보다 우선한다. 메일의 누락 2건(훅 설치, 워크트리 생성)과 부정확 3건(수치 기준·detached HEAD·메모리 원인)을 고친다.

## 0. 전제 (없으면 먼저 준비)
- `gh` CLI 로그인(`gh auth status`), git 2.40+, Python 3.12+, `uv`, `rg`
- 스킬 정본 복사: 이 PC의 `~/.claude/skills/harness`, `~/.claude/skills/strict`(+ `~/.codex/skills/strict`)를 새 PC 같은 경로로. 저장소에는 없다.
- 자격증명: `Valuehire_v4/.env.local`의 `CLICKUP_API_TOKEN`·`SUPABASE_URL`·`SUPABASE_SERVICE_ROLE_KEY`를 안전한 경로로 옮긴다. 값은 어떤 문서·메일·커밋에도 넣지 않는다.
- 로컬 비밀 패턴 파일(`.secret-patterns`, 홈 폴더)이 있어야 훅의 비밀 스캔이 이 PC와 같은 강도로 돈다. 없으면 훅이 설치 시 연결하지 못한다.

## 1. 받기 (URL을 복사할 때 메일 클라이언트의 리다이렉트 링크가 섞이지 않도록 `gh` 사용)
```bash
gh repo clone sangmokang/Valuehire_v6
cd Valuehire_v6
git fetch origin
bash scripts/install-hooks.sh        # ← 필수. core.hooksPath=hooks 설정과 실행 권한. 이것 없이는 커밋·푸시 자동 검사가 돌지 않는다
git config core.hooksPath             # 'hooks' 가 나와야 한다
```

## 2. 문서 읽기 (읽기 전용 워크트리, detached HEAD여도 무방)
```bash
git worktree add --detach worktrees/weekly-handoff-20260914 origin/task/weekly-handoff-20260914
```
- `docs/engineering/weekly-prep-briefing-2026-09-14.md` — 상태 브리핑
- `docs/engineering/goal-prompts/weekly-ops-delivery-prompt-2026-09-14.md` — 다음 작업 프롬프트(결정 카드 2건)
- `docs/engineering/goal-prompts/weekly-ops-supabase-prompt-v3-2026-09-09.md` — 그다음 프롬프트(결정 3건)
- `docs/engineering/weekly-brief-FY26W38-2026-09-14.md` — W38 검증 원문

## 3. 구현 워크트리 (한 작업 = 한 워크트리 = 새 브랜치)
```bash
git worktree add -b task/weekly-ops-skill-local worktrees/weekly-ops-skill origin/task/weekly-ops-skill   # 정본 소스
git worktree add -b task/<NAME> worktrees/<NAME> origin/main                                             # 새 작업
```
배송 프롬프트의 경로 `/Users/kangsangmo/Desktop/Valuehire_v6`는 새 PC의 clone 경로로 바꿔 읽는다.

## 4. 수치 기준 (메일의 숫자를 이렇게 읽는다)
| 항목 | 명령 | 값 |
|---|---|---|
| weekly-ops vs main | `git diff --shortstat origin/main...origin/task/weekly-ops-skill` | +11,813 −44 (합계 11,857), 67커밋 |
| stack-1 vs main | 같은 명령, stack-1 | +8,739 −36 (합계 8,775) → 3,000줄 규칙 위반 |
| split/p1 vs main | 같은 명령, split/p1 | +2,807 −18 (합계 2,825) |
| e1 뒤처짐 | `git rev-list --count origin/task/admin-dashboard-position-cards-e1..origin/main` | 12 (origin/main fc6beed 기준; 로컬 main f12ea33 기준 13) |

## 5. 푸시 주의
- pre-push 훅은 **현재 워크트리의 검사**를 돌린다. 브랜치 여러 개를 한 명령에 묶으면 검사는 한 번만 돌고, 묶인 다른 브랜치 각각이 검증됐다는 뜻은 아니다. 병합 전에는 브랜치별로 CI(pull_request 이벤트)를 본다.
- 이 PC에서 검사 2개를 동시에 돌린 푸시 2건은 harness가 "메모리 부족"으로 강제 종료했다(2026-09-14 09:1x KST). 세 번째 시도는 비밀 스캔 검사가 exit=1로 막혔고 단독 실행에서는 통과(CHECKED 32)했다 — 원인은 ※추정(동시 실행 부하). 순차 실행·한 명령 묶음으로 성공.
- 푸시 1회 소요 10분 이상은 이 PC(2026-09-14) 측정값이다.

## 6. 결정 카드 (코드 전에 답)
1. PII 게이트: (A) 제거 = 3fc86cc 방향 / (B) 유지 = weekly-ops HEAD 방향
2. 첫 PR base: (A) split/p1(권장) / (B) 13커밋 새로 3등분
3. Supabase anon 키 재발급 / 4. 적재 코드 v4→v6 포팅 / 5. FY25 Live 185건 트렌드 제외

## 7. 알려진 공백
- Golden v2 발행 엔진 미구현(`contracts/weekly-ops/notion-golden-sample-v1.json` publication_allowed=false) → 병합해도 노션 자동 발행 NOT_RUN
- Supabase 적재 8/31 정지. 자동 메모리(`~/.claude/projects/.../memory`)는 이 PC에만 있음
