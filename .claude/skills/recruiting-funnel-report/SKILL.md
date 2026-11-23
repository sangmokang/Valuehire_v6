---
name: recruiting-funnel-report
description: 채용 퍼널 실적을 LinkedIn Recruiter·멤버 Gmail·AI 서치 원장과 일대일 대조해 주간·월간·분기·반기·연간 슬라이드와 검증표를 만든다.
---

# 채용 퍼널 리포트

저장소 루트의 tools/recruiting_funnel/를 사용한다. Codex와 Claude에서 동일한 스킬명으로 호출한다. 실행 환경은 Python 3.10 이상이며 requirements.txt를 설치한다. 데이터와 산출물은 저장소 밖의 사용자 지정 비공개 디렉터리에 둔다.

1. 기간은 서울 시간 ISO 주차·달력월·분기·반기·연도다. 진행 중인 기간은 자료 기준일까지로 표시하고 전년 동분기는 양쪽 모두 같은 월·일까지 자른다. 발송자 개인과 팀, 활동일과 제안 코호트를 구별한다.
2. Aside의 기존 RPS 탭을 읽어 Inbox, Awaiting Reply, Archived와 프로젝트·보고서에서 수신인, 메시지 식별자, 최초 제안일, 직무·고객사, 수락·거절·대기를 기록한다. 이전 메시지와 더 보기의 끝을 확인한다. 전체 범위를 검증하지 못한 폴더는 부분 집계로 표시한다. 프로젝트 생성일·최근 회신일을 제안일로 사용하지 않는다. 수락은 플랫폼의 명시 기록을 쓴다.
3. gmailscraping에서 등록된 전 멤버 사서함과 일치하는 계정만 읽는다. 보관본 이후 기간을 실메일에서 보완한다. 원문 본문·발신·외부 고객사 수신·후보자·직무·메시지/스레드 ID를 확인한다. 내부 전달, 소개 요청, 단순 회신, 고객사 서명, 파일명만의 일치와 테스트 자료를 배제한다. 동일 인물+고객사+직무가 중복 추천된 경우 원문을 한 코호트에 연결한다. 다른 역할이나 재지원은 별도 에피소드로 검증한다.
4. 제안→이력서 접수, 제안→추천, 접수→추천, 추천→서류통과, 추천→성사를 코호트별로 표시한다. 실제 이력서 수신·명시 통과 또는 면접 초청·입사 확인 근거를 따로 보관한다. 오퍼·계약 문의는 입사로 인정하지 않는다. AI 추천 비중은 최초 AI 탐색 행이 추천보다 빠르고 동일인·고객사·직무가 독립 확인된 추천 / 전체 추천이다. AI 발견자 추천 전환율의 분모는 해당 기간 AI 발견 코호트다.
5. 주차별 고객사·직무 상위 집중도와 변화는 해당 날짜 메일에 연결한다. 고민·병목은 근거 날짜와 업무 내용이 있는 경우에만 쓰고, 제안량 감소만으로 원인을 단정하지 않는다. 법인명 변형과 동명이인, 날짜 역전, 회신 중복, 신규 코호트의 짧은 노출기간 및 채널 간 중복을 검사한다.
6. 자료를 events.csv와 coverage.json으로 전달해 report.py를 실행한다. 각 지표에 분자·분모·출처·미확인 범위를 표시한다. 불완전한 결과의 비율은 확정 KPI에서 제외한다. 카드별 판단 근거는 비공개 원장으로 보존한다. 주기별 생성 시 schedule.py가 완료 기간과 마지막 성공 상태를 확인한다. 새 기간마다 원천을 새로 조사한다. 결과 파일의 체크섬, 재실행 중복 여부, PPTX 재열기, 집계표 합계를 대조한다. 외부 공유는 별도 지시에 따른다.

## 실행

저장소를 체크아웃하고 해당 디렉터리에서 다음을 실행한다. Windows에서는 활성 Python 환경의 python 명령을 사용한다.

```sh
python -m pip install -r tools/recruiting_funnel/requirements.txt
python tools/recruiting_funnel/report.py PRIVATE_INPUT PRIVATE_OUTPUT --through YYYY-MM-DD
python tools/recruiting_funnel/schedule.py PRIVATE_SNAPSHOTS PRIVATE_OUTPUT --start YYYY-MM-DD
```

events.csv의 헤더는 date,case,stage,source,client,role이다. 날짜는 서울 현지 YYYY-MM-DD, case는 채널 간 검증된 동일 지원 건 식별자, source는 원문 고유 식별자다. 단계 값은 offer, accepted, awaiting, resume, referral, pass, placed, ai_origin이다. awaiting은 기준일 현재 상태로 재확인한다. coverage.json은 scope(조사 범위 설명), verified_through(기준일), complete(단계별 완결 여부), joins_complete(전체 연결 검증 여부), slides(제목과 본문 문자열 목록의 쌍)를 담는다. 주차별 고민과 AI 관여 방식은 날짜가 있는 근거로 추가 슬라이드에 명시한다.

정기 실행은 로컬 일정 관리자에서 매일 서울 시간 기준 전날까지의 마감을 확인한다. 종료일별 PRIVATE_SNAPSHOTS/YYYY-MM-DD 아래에 해당 날의 상태로 검증한 두 입력 파일을 놓는다. 누락된 마감일은 schedule.py가 종료 오류에 명시한다. 주간은 일요일, 나머지는 해당 달력 기간 말일 마감이다. 기간별 폴더에 기준일 누적 덱과 해당 기간을 포함한 상세표가 함께 저장된다. 입력이 바뀌면 새 버전을 보존한다.

인증된 PC의 수집 명령이 있으면 schedule.py 마지막에 `--refresh python LOCAL_COLLECTOR.py`를 붙인다. 수집기는 기준일과 스냅샷 경로를 인수로 받는다. 날짜별 업무 이슈를 근거와 함께 남기려면 선택 파일 issues.csv(date,client,role,issue,source)를 준비한다. Windows 작업 스케줄러, macOS launchd 또는 Linux cron에 동일한 Python 명령을 매일 등록한다. 각 기기의 비공개 입력 경로와 승인된 계정 연결은 현지에서 설정한다.
