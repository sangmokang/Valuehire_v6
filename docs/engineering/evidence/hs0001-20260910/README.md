# HS-00.01 검증 원문

## 결론

이 폴더는 로컬 착수 문서 검토의 명령과 원문을 보존합니다. 실제 후보 검색이나 온라인 실행 성공을 증명하지 않습니다.

## 판단 근거와 증거 읽는 법

`commands.json`은 실행기가 만든 기록입니다. 각 항목의 command·cwd·started/time·exit_code·commit·session과 output을 함께 읽습니다. output은 잘라내거나 다시 작성하지 않은 전체 표준 출력·오류입니다. 긴 줄을 줄인 요약이 아니라 JSON 문자열 안에 원래 줄바꿈을 보존한 기계 산출물입니다.

→ 원명령과 그 결과를 함께 보존했습니다. 종료값 0은 해당 명령 성공만 뜻하며, 파일 이름이 red인 의도된 실패와 최종 재실행을 구분해야 합니다.

`candidate-files.json`은 검토 대상으로 넘긴 파일의 SHA256(내용이 바뀌면 달라지는 지문)입니다. 기준 HEAD와 회수 브랜치도 함께 기록합니다. 커밋 직전에 실제 파일과 대조하며, 이 장부 자체는 같은 작성자의 재작성을 막는 권한 경계가 아닙니다.

→ 이 지문은 검토와 커밋의 내용 일치 확인용입니다. 독립 실행기 전용 권한이나 실제 운영 영수증의 대체물이 아닙니다.

원칙 직접 읽기와 시작 검사 원문은 commands.json의 principles-read/ledger-read/principles-check 기록에 있습니다. 읽은 두 파일의 정본을 기억·과거 보고로 대체하지 않았습니다.

범위: 회수 문서·검사·CI 연결, 기존 Python 제품 회귀. 미확인: 현재 변경의 원격 CI, 병합, 실제 포털·운영 저장·독립 OS 계정 경계. 위험한 외부 행동은 이번 작업에 포함되지 않습니다.

## 판정 변경과 원문

초기 Codeaudit PASS는 `codeaudit-initial-verdict.md`에 보존되며, 실행 환경 우회 재현 뒤 `codeaudit-reconsideration.md.json`의 FAIL로 대체됐습니다. `v1-verdict.md.json`와 `v2-verdict-formatted.md`도 옛 후보의 FAIL입니다. `v2-verdict.md`는 최초 출력 형식 그대로이고 formatted 파일은 검토자가 형식만 정정한 것입니다.
실제 Claude CLI 원본855713바이트는 `.claude/private-reviews/hs0001-20260910/v1-cli-original.jsonl`에 권한0600으로 보존하며 인증키 환경변수를 제거한 호출 정보는 v1-cli.json에 있습니다. CLI 종료값0은 호출 완료만 뜻하며 판정은 FAIL입니다. 공개용 사본은 JSONL로 추적합니다.
새6반례 RED는 e2404d3, 정상CI호환 RED는16e5d64에 시험만 커밋했습니다. `new-red-review.*`와 `compat-red-review.*`는 별도 검토자 원문입니다. 현재 GREEN 재실행을 과거 RED 증거로 바꾸지 않습니다.
`final-candidate-files.json`은 수정 후 재감사에 넘긴9개파일의 정확한 지문입니다. `budget-check.py`의 동일 판정 함수로 실제코드8파일과600정상/601실패/대상0개실패 경계를 실행했습니다. 이는 이번 로컬 검증이며 공용CI코드예산 강제 장치의 존재를 주장하지 않습니다.

→ 원문 판정과 호출 종료값을 구분했습니다. 최종 검토가 나오기 전까지 옛 FAIL을 지우거나 완료로 바꾸지 않습니다.

원문 끝 탭과 diff 공백은 삭제하지 않고 raw-storage-map.json에 적힌 JSON의 text 문자열로 손실 없이 보존합니다. 복원한 바이트의 SHA256은 각 파일에 있습니다. v1-cli-public.jsonl은 불투명한 서명 메타데이터11개만 가렸으며 명령 출력·판정 본문은 그대로입니다. 가린 항목과 원본 지문은 v1-cli-public-provenance.json에 있습니다. 초기 비밀 검사 종료값141과 공백 검사 실패도 보존합니다. 검사 규칙·억제·후크를 바꾸지 않았습니다.

## 최신 판정과 후속 부채
최신Codeaudit는codeaudit-final-recheck.md, 실제ClaudeV1는v1-final-verdict.md.json의text, 새CodexV2는v2-final-recheck-verdict.md입니다. 이전판정도역사대로보존합니다. V1의파일보고서와CLI최종응답은서로다른원문이므로v1-final-response.md.json을따로보존합니다. V1최종stream의불투명서명19개만가렸으며원문0600경로와지문은v1-final-cli-public-provenance.json에있습니다.
독립보고서가참조하는artifacts/hs-next-20260910의파일은이폴더의동명파일에서읽습니다. 원문끝공백/키이름오탐때문에JSONtext로보존한파일은raw-storage-map.json에서매핑하고text를복원해SHA를대조합니다. codeaudit-final-recheck.raw.json은원문내용을가리지않고text로보존한파일입니다.
상태검사의과거RED2는이름을복원할수없습니다. status-red-diagnosis.json은현재개별31개PASS원문/재사용증거와동시쓰기실패재현을구분합니다. 추가실행환경우회는../../humansearch-workflow-env-debt-2026-09-10.md의HS-00.05 OPEN부채이며해결주장이아닙니다.

커밋 후크는 후보자 덤프 형식인 .jsonl 확장자를 차단합니다. 공개 검토 stream 두 개는 v1-cli-public.json 및 v1-final-cli-public.json의 text에 원래 JSONL 바이트를 보존합니다. raw-storage-map.json과 각 sha256으로 원래 공개본을 복원·대조할 수 있습니다. 후보자 데이터나 실제 키를 포함한 사본이 아니며 후크의 제외 규칙은 추가하지 않았습니다.
