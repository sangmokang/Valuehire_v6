# phone 일일 이어가기와 Chrome 비점유

인수 기준: 기존 USB 수집과 별개로 일일 연결 스레드 이어가기 예약이 등록되고, 실행 요청에서 사용자 Chrome 점유와 인증 없는 신규 Gemini 전사가 금지되며 실제 완료는 별도 영수증으로 확인된다.

원인: 설치된 device_ingest_runner.py는 복사·큐 등록만 수행했다. 후속 작업은 사람이 다시 phone을 호출해야 했다. Gemini 웹 처리에 사용자 Chrome의 activeTabIndex/JXA를 사용해 화면을 점유했다.

변경: 기본 macOS LaunchAgent 설정으로 매일09:00 codex queue --resume를 전달한다. 새 코드 런너는 추가하지 않는다. 기존 수집 주기5분·모델·영구 로그인 프로필은 유지한다. 전용 헤드리스 인증은 별도 전제이며 사용자 세션을 복제하지 않는다.

검증: plutil -lint, launchctl print, 설치/정본 SKILL.md 일치, quick_validate, 첫 큐 전달 결과와 경고 확인. 실제 처리 완료는 PhoneDaily/last-completion.json만 근거로 보고한다.

한계: 예약은 Mac 사용자 로그인과 Codex 데몬이 필요하다. 별도 Gemini 인증은 현재 없으며 신규 음성 전사는 AUTH_REQUIRED다. 기존 전문 정제·Docs 작업은 계속할 수 있다. GitHub issue 도구는403을 반환했으며 이 변경은 새 프로그램 코드가 아닌 로컬 실행 설정과 스킬 지침이다.
