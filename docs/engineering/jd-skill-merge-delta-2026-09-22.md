# jd 스킬 병합 델타 — 2026-09-22

## 결론

`jd` 스킬이 같은 날 두 갈래로 갈라졌다. 한쪽은 이 워크트리(골든 구조 + 검사기),
다른 쪽은 `.agents/skills/jd/SKILL.md` 단일 원본 + Claude·Codex 양쪽 심링크다.
**심링크 구조 쪽이 배포 방식으로 더 낫다** — 사본 두 개가 갈라질 일이 없다.
아래 네 가지는 2026-09-22 실측으로 확인한 내용이라 그쪽으로 옮겨야 한다.
옮기지 않으면 오늘 고친 사고가 그대로 재발한다.

옮기기 전 원본: `~/.claude/skills/jd/SKILL.md.bak-2026-09-22` (183줄)

## 옮겨야 할 것

| # | 내용 | 근거 | 위치 |
|---|---|---|---|
| D1 | **RPS InMail 골든 구조 G1~G12** — `■ 섹션` 5개 + `• 불릿` 8개+ + `**볼드**` 5쌍+. "1,900자 압축 메시지"만으로는 오늘 아침 산문판을 막지 못한다 | 검사기가 사장님 골든 2건을 둘 다 불합격시켰다 | `docs/sot/linkedin-rps-inmail.md` |
| D2 | **RPS 컴포저 Quill 계약** — `**볼드**`는 별표가 그대로 보이고, 붙여넣은 `<ul><li>`는 **통째로 삭제**된다(본문 1,445자 → 1,073자, 불릿 11개 유실) | 2026-09-22 DOM 실측 | `scripts/jd_channels/richtext.py` |
| D3 | **ClickUp 중복 확인 단계** — FY26ClientsPosition(901814621569)을 먼저 훑고, 있으면 갱신·없을 때만 생성 | 번개장터 2건 모두 이미 존재. 새로 만들었으면 3중 중복 | `scripts/jd_channels/clickup.py` |
| D4 | **원문 대조(provenance)** — 단위의 숫자·고용조건이 원문에 없으면 불합격 | 원문에 없는 `경력 6년 이상`·`정규직`·`채용 시 마감`이 단위에 들어갔고 `source_status`는 `FETCHED_VERBATIM`이었다 | `scripts/jd_channels/provenance.py` + `scripts/acceptance/rps_inmail_ac6_provenance.py` |

## 두 설계가 충돌하지 않는 지점

- 새 스킬의 `python3 -m jd_channels packet/readback` CLI 는 이 워크트리에 **없다**.
  이 워크트리는 `jd_channels.pipeline.run()` 을 쓴다. 둘 중 하나로 합쳐야 한다.
- 새 스킬의 사람인 2,000자 × 2필드 / 잡코리아 3,000자 제안 메시지 계약은
  이 워크트리의 `render.py` 채널 프로파일(사람인·잡코리아 4,000자)과 **다르다**.
  포털 실측은 새 스킬 쪽이 최신이므로 그쪽을 따른다.

## 2026-09-22 후속 감사

현재 실제 로드 경로는 사본 두 개가 아니라 루트 작업트리의 단일 원본이다. 루트에서
`.codex/skills/jd`, `.claude/skills/jd`, 전역 `~/.codex/skills/jd/SKILL.md`를 읽으면 모두
`/Users/kangsangmo/Desktop/Valuehire_v6/.agents/skills/jd/SKILL.md`로 이어진다.

그 단일 원본에는 회사 소개 불릿 우선, 명시 제외 단위 보존, readback 필드가 있다. 하지만 D3의 핵심 문장인
“FY26ClientsPosition(901814621569)을 먼저 훑고, 있으면 갱신·없을 때만 생성”은
구체적으로 들어 있지 않다. 현재 문장은 “duplicate/position identity checks have been
recorded” 수준이라, 운영자가 어떤 ClickUp 리스트를 먼저 조회해야 하는지와 신규 생성 금지
조건을 놓칠 수 있다.

ClickUp 후보 작업은 이 PR 마무리 범위와 분리한다. `outputs/_clickup/z8nfn6nu3c.md`는
Global Team Lead 본문 후보가 기존 태스크 `z8nfn6nu3c`에 대응하며 신규 생성 대상이
아니라고 기록한다. `outputs/_clickup/PENDING.md`에는 중복 후보 `z8nfn6nt2j`(글로벌팀 리더)와 `z8nfn6n3yz`(글로벌 BD PM)가 기록돼 있다. 대상 후보 ID는 회수했으나 실제 중복 여부 및 삭제 승인 근거는 확인되지 않았다. 따라서 삭제나 ClickUp 쓰기는 실행하지 않는다. Global Team Lead `z8nfn6nu3c`의 본문 후보는 보존돼 있다.

안전한 복구 방법은 심링크를 바꾸지 않고 main의 `.agents/skills/jd/SKILL.md` 단일 원본에
D3 문장을 좁게 되살리는 것이다. main 작업트리에 다른 세션의 미커밋 변경이 많으므로 이
PR worktree에서 symlink를 재지정하거나 main 파일을 덮어쓰면 안 된다. 복구 패치는 별도
세션 소유자가 `.agents/skills/jd/SKILL.md`의 Workflow 6번 앞에 ClickUp FY26ClientsPosition
조회·갱신 우선·신규 생성 조건을 한 문장으로 추가하는 형태가 가장 작다.

## 사장님 결정이 필요한 것

**무엇을** — `jd` 스킬 한 갈래로 합친다
**왜** — 두 갈래가 살아 있으면 다음 JD 에서 어느 쪽이 도는지 예측할 수 없다
**버린 길** — 두 스킬을 `jd` / `jd-golden` 으로 나눠 두기. 기각 이유: 같은 트리거를 두 스킬이 먹는다
**대가** — 합치는 동안 한쪽 계약이 잠깐 빠진다
**되돌리기** — `~/.claude/skills/jd/SKILL.md.bak-2026-09-22` 와 이 워크트리 커밋으로 복원

재개 중 다른 세션이 루트 작업트리를 `main`에서 `task/cross-pc-handoff-20260922`로 전환하고 커밋한 것을 관측했다. 이 작업에서는 그 전환·커밋·스테이징에 개입하지 않았다. 실제 로드 원본을 이 PR 사본으로 덮어쓰거나 심링크를 재지정하지 않는다. 승인된 PR 범위 밖 다른 세션 파일이라 active 스킬 복구는 미반영 상태다.

반영할 최소 문장(기존 Workflow 앞에 추가, 이 문서에 준비한 변경안이며 active 반영 증거가 아님):

> 0. ClickUp FY26ClientsPosition(901814621569)에서 회사명·영문/국문 직무명으로 중복을 먼저 확인한다. 기존 동일 포지션이 있으면 승인된 범위에서 그 ID를 갱신하고, 없음을 확인한 경우에만 신규 등록한다. 본문·직무군 status를 저장 후 새로 조회해 대조한다. 호출 한도나 접근 실패는 BLOCKED로 기록하며 중복 없음으로 간주하지 않는다. 삭제는 정확한 대상과 삭제 승인을 별도로 확인한다.
