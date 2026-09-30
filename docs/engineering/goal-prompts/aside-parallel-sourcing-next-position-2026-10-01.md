# 다음 포지션 서치 착수 프롬프트 — Aside 병행 서치·프로필 전량 저장 (2026-10-01)

> 사용법: `/clear` 후 아래 "프롬프트 본문"의 `{…}` 를 채워서 붙여 넣는다.
> 직전 실행: 코드잇 "부트캠프 교육 운영 유닛 리드" — RPS 200/200 저장 완료, 사람인 570명 상세 저장 진행 중(아래 §6).

---

## 프롬프트 본문

```
/codeit-talent-archive-search
포지션: {채용공고 URL}  (회사 채용 목록: {목록 URL, 있으면})
이 포지션에 맞는 후보를 LinkedIn RPS·사람인 인재풀에서 찾고 목록·상세 프로필 모두 아카이버에 저장해.
다른 세션이 Aside 에서 서치 중이니 부딪히지 않게 해.
절차·규칙은 docs/engineering/goal-prompts/aside-parallel-sourcing-next-position-2026-10-01.md 를 먼저 읽고 그대로 따를 것.
도구는 같은 폴더의 aside-sourcing-kit/ 를 스크래치로 복사해 상수(창·탭·CG id)만 바꿔 쓸 것.
```

---

## 1. 쉘·브라우저 규칙 (사장님 지시 누적)

| 규칙 | 근거 |
|---|---|
| 브라우저는 **Aside 만**. Chrome·Playwright 금지. claude-in-chrome 확장에 Aside 가 안 잡히면(2026-09-30 은 Windows 기기 1대만 잡힘) **AppleScript** 로 조작 | 2026-09-28 지시 |
| **다른 세션의 메인 창·활성 탭을 절대 건드리지 않는다.** 착수 시 AppleScript 로 창/탭 id·URL·활성 탭을 읽고, 끝날 때 메인 창 활성 탭 id 가 그대로인지 재확인 | 2026-09-30 지시 "탭을 하나씩만 더 열어서 부딪히지 않게" |
| 내 작업은 **`make new window` 로 별도 창** 을 만들고 채널당 탭 1개. 만든 직후 메인 창 활성 탭 불변 확인 | 같은 날 실측(합쳐지지 않았음) |
| osascript 는 샌드박스에 막힘 → `dangerouslyDisableSandbox: true` | |
| JS 실행은 **argv 로 넘긴다**(`on run argv`). JSON 이스케이프를 AppleScript 문자열에 박으면 문법 오류 | aside.sh |
| AppleScript `execute javascript` 는 **격리 월드**: 페이지 전역(XHR 패치·Vue 상태·`self.__next_f`)은 안 보인다. DOM·동기 XHR·쿠키는 된다 | 2026-09-30 실측 |
| `timeout` 명령 없음(macOS). grep 은 `/usr/bin/grep` 절대경로 | 기존 메모리 |
| 확인 질문 최소화, 실행 방식(전경/백그라운드) 묻지 말 것. 긴 루프는 백그라운드 | 기존 메모리 |
| 저장은 확장 자동 캡처에 기대지 말고 **아카이버 직접 API** `POST http://127.0.0.1:7777/api/archive` `{url,pageTitle,textContent,screenshots?}` | 2026-09-30 자동 캡처 0건 |
| 서버 경로는 **Valuehire_v4**/tools/profile-archiver (v6 아님). DB: `.../server/data/archive.db` | |
| 발송(이직 제안·InMail)은 누르지 않는다. 저장만 | |

## 2. 착수 0단계 (필수)

1. `curl -s http://127.0.0.1:7777/api/health` → ok·archiveCount 기록
2. Aside 창/탭 목록 읽기 (aside-sourcing-kit 의 `aside.sh` 상단 스니펫 또는 아래)
   ```
   osascript -e 'tell application "Aside"
   set out to ""
   repeat with w in windows
   set out to out & "W " & (id of w) & linefeed
   try
   set out to out & "  active=" & (id of active tab of w as text) & linefeed
   end try
   repeat with t in tabs of w
   set out to out & "  T " & (id of t) & " | " & (URL of t) & linefeed
   end repeat
   end repeat
   return out
   end tell'
   ```
3. 채용공고는 `WebFetch` 로 읽어 포지션·필수·우대·연차 정리 → 검색어 설계
4. 내 창 2개 생성(RPS / 사람인), 각 창 id·탭 id 기록. `wins.swift`(`swift wins.swift`)로 **CG 창 번호**(screencapture 용) 확인

## 3. 화면 가시성 (중요)

- Chromium 은 **가려진 창을 다시 그리지 않는다** → `document.visibilityState=hidden` 이면 스크롤해도 캡처가 같은 화면.
- 2026-09-30 배치: 메인(다른 세션) 창 = 오른쪽 화면 `{2550,25,5110,1440}`. 내 창은 왼쪽 화면을 반씩 `{0,25,1280,1440}`(RPS) / `{1280,25,2560,1440}`(사람인), 사람인 창은 `set index of window id X to 1` 로 올림 → 둘 다 visible.
- 매 작업 전 두 탭 `document.visibilityState` 가 `visible` 인지 확인.

## 4. LinkedIn RPS

- URL `?keywords=` 파라미터는 **무시된다**. 상단 `#system-search-typeahead` 에 네이티브 setter + input + Enter 이벤트로 불린 입력 → 결과 URL(searchContextId…)로 바뀜.
- `rps_driver.py <tabId> list` : 목록 전 페이지(25명씩) 스크롤·저장·프로필 링크 수집 → `rps_profiles.json`
- `rps_driver.py <tabId> profiles` : 각 `/talent/profile/…` 방문, main innerText 저장. 이어하기 지원(`rps_run.jsonl`).
- 2026-09-30 실측: 200명 1명당 약 13~40초(부하에 따라), 실패 0.

## 5. 사람인 인재풀

- **검색 조건창을 건드리지 말 것.** 조건은 서버 임시저장(`get-condition-temp`)으로 **다른 세션과 공유**된다. UI 키워드 태그는 스크립트 이벤트로 안 들어간다.
- 대신 `sr_lib.js` 의 `__srSearch(kws, page, careerMin, careerMax)` 로 `POST /zf_user/memcom/talent-pool/search-list` 를 **직접 호출**(x-www-form-urlencoded, 중첩 객체는 JSON 문자열). `kws` = `[['and','KDT'],['and','교육운영']]` 형태. 한 페이지 20명, `data.total` 로 건수 먼저 재고 조합을 좁힌다.
  - 주의: `get-condition-temp` 를 읽어 틀로 쓰되 job_category·school·industry·hire_company·hiring_spec_seq 는 비운다(다른 세션 조건 오염 방지).
- 상세 `https://hiring.saramin.co.kr/applicant-view/position/resume/{res_idx}?t_ref=search` — **열람은 이직제안 건수 차감 없음**(267/330 그대로 확인).
- 이력서 본문은 스크립트로 텍스트를 못 읽는다(빈 div 높이 6,000px). → `sr_driver.py`: main 을 viewport 단위로 스크롤하며 `screencapture -x -o -l <CG id>` → `sips -Z 1600` → screenshots 로 POST(서버 OCR 대기열). "방금 본 이력서와 닮은 후보자" 위치에서 멈춤, 최대 10장.
- 1명당 약 20~25초.

## 6. 직전 실행 잔여 상태 (코드잇 포지션)

- RPS: 목록 9p + 상세 200/200 저장 완료.
- 사람인: 목록 40p 저장, 상세 570명 중 2026-10-01 기준 282명 저장·실패 0, 드라이버 백그라운드 진행 중.
  - 이어하기 파일(스크래치, 저장소 밖·PII 마스킹 명단 포함이라 커밋 안 함):
    `/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/9b0e3531-98ae-4421-8a3f-39bb69eed076/scratchpad/{saramin_lists.json,saramin_ids.json,sr_run.jsonl}`
  - 끊겼으면 그 폴더에서 `python3 sr_driver.py` 재실행(완료분 건너뜀). 단 창·탭·CG id 상수는 현재 값으로 교체.
- 확인 쿼리: `sqlite3 …/archive.db "SELECT count(DISTINCT url) FROM archives WHERE url LIKE 'https://hiring.saramin.co.kr/applicant-view%' AND captured_at > '2026-09-30T03:00';"`

## 7. 완료 보고 형식

상태 한 줄 + 채널별 (목록 페이지 수 / 상세 저장 수 / 실패 수, DB 재조회 숫자) + 결정 1~2개. 추정 숫자 금지, DB·로그로 확인한 숫자만.
