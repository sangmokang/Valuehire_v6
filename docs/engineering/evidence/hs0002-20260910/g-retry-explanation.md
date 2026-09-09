# 고장 주입 재실행

최초 g-adversarial 실행은 FAIL입니다. omit-fail-prefix는 행 필터에 PASS를 더했지만 message의 FAIL 접두 제거는 그대로 두었습니다. 따라서 정상 사유 문자열 입력에서 PASS 문구를 실패 사유로 바꾸는 의도한 효과를 만들지 못했습니다. 이를 검사가 결함을 잡았다는 증거로 세지 않습니다. 초기 스크립트·실행 원문·diff는 그대로 보존합니다.

제품이나 고정 RED 시험은 바꾸지 않았습니다. 유효한 여섯 고장(always-allow/always-reject/omit-boundary/legacy-substring/empty-allowed/restore-grep)과 정상 사본을 같은 원명령으로 다시 실행합니다. 첫 무효 주입은 제외된 역사이며 합격한 변이 수에 포함하지 않습니다. PASS 행 경계의 추가 독립 공격은 Codeaudit/V1/V2에서 따로 판정합니다.
