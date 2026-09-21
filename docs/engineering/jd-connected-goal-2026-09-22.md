# JD 연결 등록 목표 — 2026-09-22

## 결론·범위
진행 중. 뤼튼 QA Manager와 번개장터 Product Manager(Global)를 사람인·잡코리아 후보 제안용 포지션으로 등록하고 포지션마다 원문·실제 문안·영수증을 sangmokang@valueconnect.kr로 보낸다. 후보자 발송 없음. RPS는 1900자 원고 검증까지. jd를 단일 진입점으로 연결한다. L3, 내부 코드 LOCAL_ONLY. 배포·DB 변경·원격 push/PR 범위 밖.

## 확인한 원인·계약
jd는 원문 정리, jd-channels는 단일4000자 본문 생성뿐이며 실필드 배분/제안내용 영속성/서버 재조회가 미연결이다. 구 position-register는 CDP와 기본 정규직 등 과거 지침이라 현재 Aside 절차와 충돌한다. v4 코드는 사용하지 않는다.
입력: 사용자 원문 우선, 회사/제목/원문해시/의미단위/출처/제외장부. URL NPLSRGT2는 실제 Global Team Lead이며 요청 PM과 다르므로 사용자 PM 원문을 기준으로 하고 혼합하지 않는다.
출력: 채널 packet, 개별필드 측정과 단위 배치, 저장/초안 상태, readback, 이메일 receipt.
한도: NFC/LF 공백·줄바꿈 포함 Unicode와 UTF16 중 큰 값. 사람인2000+2000, 잡코리아 제안내용3000+업무1000+우대1000. 제안내용은 별도 저장 여부를 직접 확인한다. 공백제외2351은2999자 본문의 진단수치이며 한도 아님. RPS1900.
오류: 누락/필드초과/중복모호/저장미확인은 해당 쓰기 차단; timeout시 재조회 후 재시도. 기계검증은 등록/발송 허가를 생성하지 않는다.

## EARS와 반례
- When 배치하면 JD의 모든 실질 단위를 보존해야 한다. 반례: non-core 회사/성장 문장 몰래삭제.
- When 길이를 검사하면 각 칸을 개별 검사해야 한다. 반례: 총5000자만 맞고 업무1200자.
- When 저장하면 새로 연 화면 값을 정확 대조해야 한다. 반례: 작성중 DOM을 서버재조회라 주장.
- When 잡코리아 포지션만 저장하면 제안내용 영속저장으로 표시하면 안 된다. 반례: checkbox만으로 성공 선언.
- When URL과 원문이 충돌하면 다른 직무를 섞지 않아야 한다. 반례: Team Lead6년을 PM5년에 덮어씀.
- When 메일을 보내면 수신자/원문/실제입력값을 SENT에서 대조해야 한다.
- While 운영하면 두 지정포지션 이외 수정·후보발송을 하지 않는다.

## WU·검증·복원
WU1 계약/실패시험/RED커밋, WU2 배치CLI/GREEN, WU3 스킬/SOT 연결, WU4 Aside 2포지션×2채널 저장·재조회·메일, WU5 V1/V2·회귀·로컬커밋.
시험: python3 -m unittest discover -s tests -p test_jd_registration.py -v 및 기존 test_jd_channels.py. 원칙검사34/34 PASS, artifacts/jd-connected-20260922/principles.json. strict-workflow/coding-principles/principles.yaml 직접읽음. hard600/function100. 자동LLM 호출코드 없음 LLMOps NOT_APPLICABLE.
격리worktree 사용, 사용자 root변경 보존. 전역스킬 변경전 사본 보존. 포털은 leader만 조작. DB lease 미구현이므로 무인병렬서비스로 주장하지 않는다. 쓰기 전 기존ID/본문 보존 후 같은 그룹현재ID로 복원 가능. 메일은 포지션별 receipt로 중복방지.

## 검증 장부
시작HEAD f1f7a01. 원칙검사 PASS34/34. V1/V2 NOT_RUN. 첫 goal 쓰기는 상대경로 중복으로 실패하여 절대경로로 복구, 코드/포털 변화 없음.
