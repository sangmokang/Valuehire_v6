VERDICT: FAIL

## 결론

여덟 개 주장 가운데 일곱 개는 실행으로 확인됐습니다. 구조 검사는 요구된 숫자를 정확히 내고 종료값 0을 냈으며, 여섯 가지 고장 사본은 모두 종료값 1, 실제 새 표면을 동반한 일곱 번째 기능 사본은 검사 코드를 한 줄도 고치지 않고 종료값 0을 냈습니다. 문서가 "지금 되는 것"과 "아직 안 되는 것"을 구분하는 방식도 사실과 맞았습니다.

다만 사람인 관측기가 문서에 적힌 실패 규칙을 한 가지 경로에서 지키지 않습니다. 브라우저가 넘긴 탭 주소가 특정 모양으로 망가져 있으면, 프로그램은 "사람을 부르는 정상 실패"로 끝나지 않고 파이썬 오류 화면을 여러 줄 토해내며 예정에 없는 값으로 종료합니다. 문서가 약속한 "항상 한 줄, 항상 0 아니면 2"가 깨집니다. 그래서 FAIL입니다. 부수적으로 문서 링크 하나가 목적지에 닿지 않습니다.

**건너뜀·재시도·추정 고지**: 실제 사람인 브라우저에 붙는 라이브 실행은 하지 않았습니다(로컬 진단 포트·로그인 세션 없음). 게이트 스크립트를 처음에 `humansearch/` 안에서 실행해 종료값 127이 나왔고, 저장소 루트에서 재실행해 0을 확인했습니다. 결함 재현은 `_fetch_targets`만 대체한 격리 스크립트로 했습니다 — 이 함수는 로컬 진단 포트의 JSON 본문을 그대로 돌려주므로, 그 본문에 해당 값이 들어오는 상황과 동치라고 추정했습니다.

## 판단 근거

- **택한 해석**: 기능 YAML의 `outputs.exit_code.allowed_values: [0, 2]`(`humansearch-browser-access.yaml:88`, 종료값 허용 집합을 규정하는 줄)와 `errors[0].behavior`(`:96`, 모든 관측 실패를 DRIFTED 한 줄 + 종료값 2로 정규화한다고 선언하는 줄)는 **런타임 전 경로에 대한 주장**입니다. 파일 자체를 대상 목록의 신뢰 경계로 다루는 코드(본문 크기 상한, 타입 검사, `_cdp.py:31-35`의 `urlsplit` ValueError 포획)가 이미 그 해석을 뒷받침합니다.
- **버린 해석**: "정상적인 Chrome이라면 그런 URL을 내놓지 않으니 계약 위반이 아니다". 버립니다 — 같은 코드가 `_cdp.py`에서는 동일한 예외를 명시적으로 잡고, `observe.py`는 대상 목록의 다른 모든 이상값을 정규화하므로, 이 한 곳만 무방비인 것은 의도가 아니라 누락입니다.
- **틀리면 깨지는 것**: 제 판단이 틀리려면 `select_single_target`이 받는 대상 목록이 신뢰 입력이어야 합니다. 그러면 `_fetch_targets`의 방어적 검증 전부가 불필요해집니다.
- **앵커 건**: 검사기가 `#` 뒤를 잘라내고 경로만 본다는 사실(`scripts/check-docs-sot.sh:111`, `value.split("#", 1)[0]`로 fragment를 버리는 줄)을 확인했으므로, 자동 검사로는 잡히지 않는 수동 확인 대상으로 봤습니다.

## 결함

### 결함 1 — 심각도 중

**원문 제목**: `docs/sot/features/automation/humansearch-browser-access.yaml` — `outputs.exit_code`(`:86-90`, 허용 종료값을 0과 2로 못 박는 블록), `errors[0]`(`:93-97`, "traceback 없이 exit 2로 정규화"를 선언하는 블록), `HBA-INV-4`(`:119-122`, 출력이 항상 한 줄임을 주장하는 불변조건)

**원인**: `humansearch/src/humansearch/observe.py:244`(`_origin`이 대상 URL을 `urlsplit`으로 파싱하는 줄)이 `ValueError`를 잡지 않습니다. `main()`의 예외 처리(`:157`, `except (CdpReadError, ObservationError)`)는 이 예외를 포함하지 않아 그대로 새어 나갑니다. `_cdp.py:31-35`는 같은 예외를 잡는데 `observe.py`는 잡지 않는 비대칭입니다.

재현(격리 실행, 저장소 미변경):

```text
File ".../observe.py", line 244, in _origin
    parsed = urlsplit(url)
ValueError: Invalid IPv6 URL
MAIN_EXIT=1
```

입력은 `[{"type":"page","url":"https://[oops","webSocketDebuggerUrl":"[REDACTED SYNTHETIC LOOPBACK DEVTOOLS ENDPOINT]"}]` 하나뿐입니다. 원문의 합성 로컬 endpoint도 저장소의 무인증 DevTools URL 금지 패턴에 해당해 증거 의미를 보존한 채 가렸습니다.

**사업 영향**: 진단 포트가 예상 밖 대상 하나를 내놓는 순간, 운영자는 "사람을 불러라"라는 한 줄 대신 파이썬 스택 트레이스를 봅니다. 종료값 1은 계약에 없는 값이라 후속 자동화가 이 상태를 "인증 필요"로도 "성공"으로도 분류하지 못합니다. 또한 스택 트레이스는 탭 URL 원문(`https://[oops`)을 그대로 로그에 남겨, 개인정보 제거를 통과하지 않은 값이 처음으로 밖으로 나가는 경로가 됩니다.

### 결함 2 — 심각도 하

**원문 제목**: `docs/sot/features/automation/humansearch-browser-access.yaml:131` — `HBA-INV-6`의 `evidence` 값 `docs/sot/humansearch-browser-contract.md#자격증명과-명령-능력-경계`(관측이 검색·입력·재시도 능력을 부여하지 않는다는 불변조건의 유일한 근거를 가리키는 줄)

**원인**: 대상 제목은 `docs/sot/humansearch-browser-contract.md:254`의 `### 10. 자격증명과 명령 능력 경계`(번호가 붙은 절 제목)입니다. 실제 앵커는 `#10-자격증명과-명령-능력-경계`이므로 현재 fragment는 어디에도 닿지 않습니다. 같은 저장소의 `humansearch-auth-surface.yaml`이 쓰는 fragment 넷(`#입력`, `#출력`, `#완전-결정표`, `#공개-기능`)은 전부 번호 없는 제목이라 정상 해석되므로, 이 한 건만 규약에서 벗어났습니다. 검사기는 fragment를 버리므로 잡지 못합니다.

**사업 영향**: 능력 경계라는 가장 민감한 불변조건의 근거를 클릭한 사람이 442줄 문서의 맨 위로 떨어져 §10을 직접 찾아야 합니다. 검토자가 근거 확인을 건너뛸 확률이 올라갑니다.

## 설계 지적 — 결함 1의 수정 방향

- **무엇을**: `select_single_target`이 대상 URL 파싱 실패를 `TargetSelectionError`로 정규화하도록 `_origin`을 `try/except ValueError` 안에 두고, 실패한 후보를 "일치하지 않음"으로 취급합니다.
- **왜**: 대상 목록은 이미 신뢰하지 않는 입력으로 설계돼 있고(`_fetch_targets`의 크기·타입 검증), `_cdp.py`가 같은 예외를 이미 그렇게 다룹니다.
- **버린 길**: `main()`에 `except ValueError`를 넓게 추가하는 방법. 분류기의 `InvalidObservation`(ValueError 하위)까지 삼켜 진짜 프로그래밍 오류를 DRIFTED로 위장시키므로 버립니다.
- **대가**: 망가진 URL이 조용히 "후보 아님"이 되므로, 잘못 설정된 포트를 진단하려면 그 사실이 별도 상태로 드러나야 합니다.
- **되돌리기**: 해당 `try/except`와 회귀 시험을 같은 변경에서 함께 되돌립니다.

## 기술 상세와 증거 원문

**주장 1 — 확인**. `PASS: feature SOT structure catalog=1 features=6 categories=3 invariants=33 product_files=14 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2 paths=validated`, `OK: docs/sot 재구성 AC 전부 충족`, `EXIT=0`.

**주장 2 — 확인**. `auth_surface.py:64-73`(`classify_auth_surface` 본문)은 외부 상태를 읽지 않습니다. `humansearch-auth-surface.yaml:97`(`boundaries` 항목)이 "The one-shot Saramin observer is the only current non-test runtime consumer"라고 밝히며, `HAS-V2`의 `rg` 명령을 실행한 결과가 구현·패키지 내보내기·`observe.py` 세 곳뿐이라는 `expected`와 일치했습니다.

**주장 3 — 부분 확인**. 소유 파일 3개, `implemented/local_runtime`, 포트 계약 대조(`observe.py:130`, 계약 포트 집합에 없으면 `ObservationError`를 올리는 줄), 정확히 하나의 target(`observe.py:71-74`, 개수가 1이 아니면 중단하는 줄), exact origin(`observe.py:244-247`, scheme+netloc만으로 origin을 만드는 줄), 한 줄 출력 형식(`observe.py:120-123`)은 모두 사실입니다. 종료값 0/2 규정만 결함 1로 깨집니다.

**주장 4 — 확인**. `humansearch-browser-contract.md:363-381`의 장부는 L1 endpoint 계약·단일 target 관측·target 0/1/2+ 경계를 `IMPLEMENTED_LOCAL`로, 자동 운영 origin·포트 발견·재시도·자동 재개·잡코리아·LinkedIn 실제 코드·C1 캡처를 `NOT_RUN`으로 분리합니다. `:11-14`(현재 HEAD 범위를 선언하는 결론 문단)와 `:165-167`(채널별 표)도 같은 구분을 반복하며 모순이 없습니다.

**주장 5 — 확인**. `PYTEST_EXIT=0`(81 passed), `RUFF=0`(All checks passed), `MYPY=0`(9 source files), `GATES_EXIT=0`(ruff 24 파일 / mypy strict 24 파일 / pytest 81 / runtime import proof, `COLLECTED: 81`).

**주장 6 — 확인**. 격리 사본 결과: 새 추적 제품 파일 `EXIT=1 tracked_product_files ownership mismatch missing=['humansearch/src/humansearch/newmod.py']` · marker 미귀속 `EXIT=1 missing=['contracts/humansearch/saramin-markers.json']` · 새 CI 단계 `EXIT=1 ci_steps ownership mismatch missing=['Unattributed new step']` · 두 번째 workflow `EXIT=1 CI workflow coverage changed` · 기능 문서 삭제 `EXIT=1 catalog document for admin-weekly-dashboard does not exist` · 없는 근거 `EXIT=1 evidence for humansearch-auth-surface does not exist`. 일곱 번째 기능 확장은 `EXIT=0 features=7 invariants=34 product_files=15`이며 검사 스크립트는 손대지 않았습니다.

**주장 7 — 확인**. 검사기 431줄(≤500). 외부 URL 거부(`:110`), 절대 경로·`..` 거부(`:113`), 중복 키 거부(`:92-98`, `object_pairs_hook`), 기능 ID 상수 없음 — 표면은 `git ls-files`·workflow 파싱·`hooks/` 순회·`docs/sot/humansearch-*-contract.md` glob로 역유도합니다(`:329-374`). 추적 symlink 0건(`git ls-files -s`에 `120000` 없음). 기능 YAML에 외부 URL·절대 경로 근거 없음.

**주장 8 — 확인**. `git diff --check` 종료값 0. 실행 전후 `git rev-parse HEAD`가 `c59bad7b16…`로 동일하고, 상태 항목 21개(수정 5 + 미추적 16)가 초기 스냅샷과 글자 단위로 일치합니다. `git stash list` 비어 있고, 모든 변이는 `mktemp -d` 사본에서만 수행한 뒤 삭제했습니다(`TEMP_CLEAN`).
