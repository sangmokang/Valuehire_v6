# 3사 발송 내역 원천 계약 (SOT)

최종 갱신: 2026-09-24 (Aside 로그인 세션 읽기 전용 실측, 발송·연락·이용권 차감 0건)

## 1층 — 결론

사람인·잡코리아·LinkedIn RPS의 "실제로 보낸 제안" 건수는 발송 버튼이 아니라 **각 포털이 스스로 보여주는 보낸 내역**에서 읽는다. 세 채널 모두 발송 1건마다 포털이 준 고유 번호가 있어 `(channel, provider_receipt_ref)` 조합으로 중복 없이 셀 수 있다. 단 잡코리아는 날짜까지만 알 수 있어 시간 단위 집계가 불가능하고, RPS는 로그인한 좌석(계정) 한 명의 발송만 보인다.

## 2층 — 판단 근거

- 발송 버튼 클릭 시점 기록은 사람이 직접 보낸 건(RPS는 전부 사람 발송)을 놓치고 클릭을 성공으로 오인하므로 원천으로 쓰지 않는다.
- 아래 원천은 모두 화면 DOM 또는 페이지가 쓰는 구조화 응답(JSON)에서 읽힌다. 스크린샷·OCR은 원천으로 쓰지 않는다.
- 비어 있는 응답을 "발송 0건"으로 접으면 안 된다. 세 채널 모두 실측에서 오류·범위 초과·요청 형식 오류가 **정상 응답 + 빈 목록**으로 돌아오는 경우가 있었다(아래 채널별 "0건 오판 위험").

## 3층 — 채널별 원천

### 사람인 — 메시지 관리(포지션 제안)

- 사람 진입 URL: `https://www.saramin.co.kr/zf_user/messenger/?ut=c`
- 방 목록: `GET /zf_user/messenger/index/get-rooms?page=<N>&filter_type=my|all` → `roomListInfoDtoList[]`, `totalRooms`, `totalPages` (페이지당 10)
  - `filter_type=my` 는 로그인 회원의 방, `all` 은 회사 전체 방.
- 제안 이력(발송 원천): `GET /zf_user/messenger/index/get-suggest-history-list?mem_no=<방.receiveMemNo>&room_no=<방.chttRoomNo>` → 배열
  - 제안 1건의 고유 번호: `hiring_spec_res_r_seq` (재조회 시 동일 확인)
  - 한 제안의 상태 변화가 같은 번호로 여러 행에 나온다. `hiring_status_action_cd=apl801`(요청) 행이 발송, `apl805`(거절) 등은 응답이다. **발송은 apl801 행만 센다.**
  - 발송 시각: `reg_dt` (`YYYY-MM-DD HH:MM:SS`, 초 단위)
  - 포지션: `hiring_spec_seq` (= 방의 `hispNo`), 후보 이력서: `res_idx`
- 발송자: `GET /zf_user/messenger/index/get-messages?mem_no=&room_no=&start_index=` 의 `messageInfoList[]`(`chttMsgNo` 메시지 번호, `createDateTime`, 회사측 `profileName`·`team`, `messageType=request_offer`). ※ `get-messages` 는 방을 여는 동작이라 읽음 처리가 생길 수 있다.
- 조회 범위: 가장 오래된 방이 정확히 1년 전(실측일 2026-09-24 → 2025-09-24).
- 0건 오판 위험: 범위 밖 페이지는 200 응답 + 빈 배열. 끝은 `totalPages` 로 판정하고 빈 배열로 판정하지 않는다. 로그인 만료 응답 형태는 미실측(※).
- 미확인(※): 같은 후보·같은 포지션에 다시 제안하면 새 `hiring_spec_res_r_seq` 가 생기는지(표본 50개 방에서 재제안 0건).

### 잡코리아 — 포지션 제안 인재

- 사람 진입 URL: `https://www.jobkorea.co.kr/corp/person/position`
- 목록(서버 렌더 표): `GET /corp/person/position?rPageCode=PA&rImptnt_Stat=0&rMemo_Stat=0&Page=<N>` (페이지당 10)
  - 행 속성: `data-posg-send-no`(발송 1건 고유 번호, 재조회 시 동일 확인), `data-r-no`(이력서), `data-posg-no`(포지션 제안 묶음), `data-m-id`(회원)
  - 열: `담당자/제안일`(발송자 이름 + `YY.MM.DD`), `제안답변상태`(읽음·거절·수락·미응답)
- 상세: `보낸제안` → `/corp/person/positionofferlist?PosgNo=<data-posg-no>&...` — `발송일`도 날짜만 있다.
- 시각 정밀도: **날짜만.** DOM·HTML 원문 어디에도 발송 시·분이 없다.
- 조회 범위: 기본 화면은 **최근 1개월**(2026-09-24 실측 150건 = 상단 "전체 150"). 화면 안내문상 보관은 발송일로부터 1년. 상단 "전체" 숫자는 조회 기간 필터에 따라 달라지므로 누적 건수로 쓰지 않는다.
- 0건 오판 위험: 마지막 다음 페이지는 행 0개 응답.
- 미확인(※): 같은 후보에게 재발송하면 별도 행이 되는지(150건 중 이력서 중복 0건). 1개월보다 긴 기간을 부르는 URL 파라미터.

### LinkedIn RPS — Recruiter 받은편지함

- 사람 진입 URL: `https://www.linkedin.com/talent/inbox/0` (Recruiter 헤더 "Go to message inbox" → "View all messages"). 후보 한 명의 메시지는 `https://www.linkedin.com/talent/profile/<회원 URN>/messages`. 사장님이 준 표본 프로필 URL은 후보 개인 식별자라 저장소에 기록하지 않는다.
- 목록: `GET /talent/api/graphql?queryId=talentConversations...&variables=(start:0,count:15,section:<INBOX|UNRESOLVED|ARCHIVED>[,paginationToken:<커서>])`
  - 헤더 필수: `csrf-token`(JSESSIONID 값), `x-restli-protocol-version: 2.0.0`, `accept: application/json`
  - 구역: `INBOX`=수락·답장, `UNRESOLVED`="Awaiting Reply"(PENDING), `ARCHIVED`. 세 구역을 모두 읽어야 전체 발송이다.
  - 페이지: **커서 방식**(`metadata.paginationToken`). `start` 를 바꾸면 GraphQL 오류가 난다.
  - 목록 응답에는 발송 시각이 없고 `lastActivityAt` 만 있다.
- 스레드: 같은 queryId에 `variables=(conversationUrn:<ts_mail_thread>,start:0,count:15,ownerSeat:<ts_seat>)`
  - 발송 1건 고유 번호: `initialMessages[0].entityUrn` (`urn:li:ts_msg_message:...`, 재조회 시 동일 확인)
  - 발송 시각: `initialMessages[0].deliveredAt` (epoch 밀리초)
  - `channel=INMAIL`, `state=SENT`, 발송자 `sender.entityUrn`, 수락 여부 `requestState`
  - 포지션: `conversationContextUrns` 의 `ts_hiring_project` (실측 195건 중 116건만 있음)
  - 후보: `participants[].entityUrn`
- 범위: 받은편지함은 **로그인 좌석 한 명 기준**(`ownerSeat`). 다른 팀원의 발송은 그 사람의 좌석으로 읽어야 한다.
- 0건 오판 위험: 짧은 시간에 13페이지를 연속 조회한 뒤 `Internal error fetching data from downstream` 오류가 1분 이상 이어졌다. 요청 간격을 두고, 오류 응답은 0건이 아니라 "미집계"로 처리한다. 잘못 만든 `variables` 도 200 응답 + 빈 목록으로 돌아온 적이 있다.
- 미확인(※): 구역별 전체 보관 기간(오류로 INBOX 195건에서 조회 중단, ARCHIVED 표본에는 2023-06 기록 있음).

## 중복 방지 키

| 채널 | provider_receipt_ref | sent_at 정밀도 |
|---|---|---|
| saramin | `hiring_spec_res_r_seq` (apl801 행) | 초 |
| jobkorea | `data-posg-send-no` | 날짜 |
| linkedin_rps | `initialMessages[0].entityUrn` | 밀리초 |

`channel + candidate + position + sent_at` 대체 키는 쓰지 않는다. 잡코리아는 날짜만 있어 같은 날 같은 후보·포지션 재발송을 구분하지 못하고, RPS는 포지션 URN이 빠진 대화가 있다.

## 관련

- 설계 조사: `docs/engineering/` 의 3사 발송 계측 goal(작성 예정)
- 기존 미병합 설계: 브랜치 `task/weekly-ops-outreach` 의 `contracts/weekly-ops/db-contract-v1.sql`(`proposal_send_attempts`), `runtime-contract-v1.json`(채널별 인정 화면)
- 브라우저 접속 경계: [humansearch-browser-contract.md](humansearch-browser-contract.md) — 메시지 발송 자동화 금지는 여기서도 유효하다.
