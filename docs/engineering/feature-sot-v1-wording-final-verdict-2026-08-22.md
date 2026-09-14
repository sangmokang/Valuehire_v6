VERDICT: PASS

## 결론
좁힌 문구가 실제 `urlsplit` 동작과 일치하며, 결함을 축소하지도 않습니다.

## 검증 증거
- **제품 코드 무변경**: `git diff HEAD --stat -- humansearch contracts apps hooks` 빈 결과, `HEAD=c59bad7b16…` 유지. 변경은 문서 세 곳뿐입니다.
- **실제 동작 대조**(격리 실행, 저장소·네트워크 미접촉): `https://[oops` → `ValueError: Invalid IPv6 URL`(URL 문자열 미노출), `https://[secret-tenant-42]/c/7788?token=abc` → `'secret-tenant-42' does not appear to be an IPv4 or IPv6 address`. 즉 노출은 대괄호 호스트 조각 수준이고, 전체 URL·경로·query는 나오지 않았습니다. `catalog.yaml:128`("traceback exposing URL fragments"), `humansearch-browser-access.yaml:105`("may expose malformed URL fragments"), `:150`, `humansearch-browser-contract.md:20`("호스트 조각 등이 포함된"), `:373`("URL 조각")은 모두 가능성 표현이라 관측을 넘지 않습니다.
- **은폐 없음**: `KNOWN_DEFECT`(`:373`), `known_unhandled_exit`(`:91-96`), "not an accepted safe behavior"(`:105`), "bypass the one-line privacy-reduced failure path"(`:150`), 회귀 시험+제품 수정 동시 변경 조건(`:169`, `:209`, `browser-contract.md:21`)이 그대로입니다. exit 1과 PII 제거 우회는 계속 명시됩니다.
- **명령**: `bash scripts/check-docs-sot.sh` exit 0, `features=6 categories=3 invariants=33 product_files=14 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2`. `git diff --check` exit 0.
- **작업 트리**: 미추적 26항목(직전 24 + 이번 판정·지문 2), 제 변경 없음.

## 잔여 리스크
- 영문 "URL fragments"는 같은 YAML `HBA-INV-4`의 "fragment"(URL `#` 조각)와 어휘가 겹쳐 오독 여지가 있습니다. 한국어 "호스트 조각"이 더 정확하니, 다음 변경 때 `host portion of the malformed URL`로 다듬으면 좋겠습니다. 판정을 바꿀 결함은 아닙니다.
- 라이브 포털 접속은 하지 않았고, 진단 포트 본문이 해당 값을 돌려주는 상황과 동치라는 추정은 유지됩니다.
