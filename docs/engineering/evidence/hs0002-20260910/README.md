# HS-00.02 검증 증거

## 결론

수정한 실패 사유 판정은 시험과 독립 검토를 통과했습니다. 인증 값 노출 사고는 아직 해결되지 않았습니다.

## 증거 연결과 한계

현재 제품 후보는 `final-candidate-files.json`의 다섯 파일이다. 최초 RED는 `0263108`, 공백 경계 추가 RED는 `8bef581`이다. 기존 두 시험 파일의 기대값은 각 RED 커밋 이후 유지한다. 새 Codeaudit·실제 Claude V1·새 Codex V2는 모두 PASS이며, GREEN SHA는 `69801528d794aabfe8ceb84e1ee073d71ceec442`이며, 커밋 후 지문 대조는 [green-readback.json](green-readback.json)에 연결한다. 운영 인증 값 노출 사고는 별도로 OPEN이다.

초기 Codeaudit·Claude V1 PASS와 Codex V2 FAIL을 그대로 보존한다. 후속 후보는 정조준 43개·전체 회귀 262개·기존 변이 37개를 통과했다. G의 고장 24종과 실제 후속 Claude V1의 고장 37종은 수와 범위가 다르다. Claude의 정상 사본 1개를 합치면 38번 실행이며, 고장 중 31개는 동결 시험에서 실패하고 6개는 살아남았다. 실제 구현의 직접 입력 결과와 검토자의 해석은 별도로 읽어야 한다.

새 Codex 재검토는 `v2-final-verdict.md`와 `v2-final-evidence.json`이다. n28 동등성에 관한 V1 설명은 직접 반례로 정정했으며, 잘린 출력 대신 전체 로그 경로·지문으로 대조한다.

새 Codeaudit는 `codeaudit-final-verdict.md`, 실제 Claude 후속 판정은 `v1-final-verdict.md`와 `v1-final-evidence.json`이다. CLI 실제 호출·시각·종료값·세션·원시 출력 지문은 `v1-final-cli.json`, 공개 원문은 `v1-final-cli-public-map.json`과 part 파일들이다. 작성된 판정서와 CLI 최종 응답(`v1-final-response.md`)은 별도 원본이다. 원시 CLI는 `.claude/private-reviews/hs0002-20260910/`에 제한 권한으로 보존하며, 공개본에서 뺀 항목은 불투명한 thinking signature뿐이고 각 지문을 명부에 남겼다.

`storage-map.json`은 artifacts 원본 상대 경로와 이 폴더의 보존 경로·SHA256을 연결한다. log/diff/script와 중첩 실행 산출물은 JSON의 `text` 값에 원래 바이트를 그대로 담는다. 이는 출력 자르기나 명령 재구성이 아니다. JSON에서 text를 꺼내 UTF-8로 쓰면 원본 SHA256과 같아야 한다. 파일은 각각 1MB 이하이며, 실행 검증 코드는 보존 전 원본 경로에서 파일 600줄·함수 100줄 한도를 별도로 측정한다.

실패·재시도·출처 갭도 보존한다. Codeaudit의 초기 불완전한 명령은 명시적 출처 갭이고 별도 exact/rerun 기록이 후속 근거다. `final-g2`의 잘못된 경로 실패와 `final-g2-recheck`의 실제 명령 통과를 구분한다. 대조는 `final-ledger-reconciliation.md`, 기타 재시도는 `final-retries.md`에 있다. 과거 파일을 마지막 성공으로 덮지 않는다.

초기 V2가 환경 목록을 조회하며 인증 값을 도구 응답과 로컬 로그에 노출했다. 해당 환경 로그는 가림 처리했고 Git 보존 대상에서 제외했다. 값 없는 지문·가림 처리 기록·재검사 결과만 보존한다. `privacy-key-scope.json`의 role 내용은 로컬 해독 결과이며 서명·현재 유효성을 검증한 증거가 아니다. 키 교체는 실행하지 않았고 현재 유효성에 관한 사용자 확인이 대기 중이다. 로컬 로그 가림은 이미 나온 도구 응답의 노출을 취소하지 않는다.

같은 UID의 로컬 검토이며 OS 권한 격리·P17·포털 완주·운영 배포·원격 CI·병합을 증명하지 않는다.
