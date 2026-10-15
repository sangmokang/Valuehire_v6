# HS-04.02a HumanSearch runner boundary — goal (2026-09-14)

## 결론

HS-04.02a는 HS-04.03이 Git 밖 보호 경로에 원본 출력과 영수증을 저장할 때 쓸 최소 쓰기 경계를 만든다. 이 WU는 계정 생성, sudo, 기존 권한 변경, 실제 별도 UID EACCES 실증을 하지 않는다. 현재 환경에서 `id -u hsrunner`는 `id: hsrunner: no such user`로 실패했으므로 별도 계정 경계 실증은 `NOT_RUN`이다.

V2 보안 결론: caller가 임의 `runner_uid`나 `current_uid`를 public API로 넣어 OS 신원 증거를 위조할 수 없어야 한다. runner 신원은 미리 준비된 실제 OS 계정 이름 `hsrunner` lookup 결과에만 결합한다. `hsrunner` 계정이 없으면 쓰기를 하지 않고 `not_run`을 반환한다.

## 범위

소유 파일은 아래 세 개다.

- `humansearch/src/humansearch/runner_boundary.py`
- `humansearch/tests/test_hs_0402a.py`
- `docs/engineering/humansearch-runner-boundary-goal-2026-09-14.md`

공유 SOT, CI, 계정, 서비스, 권한 설정은 수정하지 않는다.

## API 계약

입력은 명시적인 `implementer_uid`, `protected_root`, `relative_path`, `payload`다. `runner_uid`와 `current_uid`는 caller 입력이 아니다. runner UID는 OS의 `hsrunner` 계정 lookup으로만 얻는다.

상태는 `written`, `denied`, `not_run`이다.

- `hsrunner` 계정 lookup이 실패하면 OS runner 경계를 실행할 수 없으므로 `not_run`이다.
- lookup된 runner UID와 `implementer_uid`가 같으면 OS 권한 분리를 증명할 수 없으므로 `not_run`이다.
- 현재 실제 프로세스 UID가 lookup된 runner UID가 아니면 보호 파일 쓰기는 `denied`다.
- `protected_root`는 절대 경로, symlink 아님, owner가 lookup된 runner UID, mode가 정확히 `0700`이어야 한다.
- 대상 상대 경로는 root 밖으로 escape할 수 없고, 부모 디렉터리와 대상 파일 경로 자체의 symlink를 거부한다. 새로 만드는 부모 디렉터리는 restrictive umask에서도 최종 mode `0700`으로 확인한다.
- 기존 파일 overwrite는 하지 않는다. 새 파일은 restrictive umask에서도 최종 mode `0600`으로 만들고 write 뒤 owner/mode/regular-file 상태를 다시 확인한다.
- 일반 로그와 반환값에는 raw payload를 넣지 않는다. 반환값은 경로, 상태, reason, sha256, byte count, 그리고 쓴 파일의 device/inode만 허용한다.
- device/inode는 payload를 담은 file descriptor의 `fstat`에서 얻는다. 게시된 최종 이름을 다시 stat해서 얻지 않는다. 같은 runner UID의 다른 실행이 그 이름을 차지하면 원문 hash와 남의 파일 식별값이 한 영수증에 묶이기 때문이다.
- device/inode는 파일을 여는 값(locator)이 아니라 대조용 검증값이다. 소비자는 경로나 고정된 디렉터리 fd로 연 뒤 이 쌍과 sha256으로 같은 파일인지 확인한다.
- 소유를 증명할 수 없는 최종 이름은 어떤 실패 경로에서도 unlink하지 않는다. 게시 대조가 실패하면 임시 이름만 제거한다. 대조를 통과한 파일은 임시 정리에 실패해도 그대로 둔다.
- 정리에 실패해 임시 파일이 남으면 반환값에 그 경로를 `temp_path`로 담는다. `path`는 게시 시점 경로이며 이후 다른 파일을 가리킬 수 있으므로, 소비자는 `path`와 `temp_path` 후보를 차례로 열어 device/inode/sha256이 맞는 것을 우리 파일로 본다.
- `recovery_required`는 러너 프로세스를 더 믿을 수 없다는 뜻이다. 호출자는 순회를 중단하고 러너 프로세스를 폐기한다. 임시 파일 file descriptor의 `close` 실패도 여기에 해당한다. `close`가 오류를 내면 descriptor 상태가 POSIX상 미정의라 회수하지 못한 손잡이가 남을 수 있다.
- `written`은 현재 프로세스가 파일을 썼다는 제품 경계 결과다. 구현자 UID의 외부 별도 process `EACCES`와 runner process write 성공이 실증되기 전까지 OS 격리 검증 완료 상태로 승격하지 않는다.

## 인수 기준

### AC-1 hsrunner 계정 없음은 NOT_RUN

When OS에 `hsrunner` 계정이 없으면, 시스템은 runner 권한 경계를 실행하지 않고 쓰기 전에 `not_run`을 반환해야 한다.

### AC-2 caller 신원 위조 표면 없음

When caller가 임의 implementer UID를 넣어도, 시스템은 public `runner_uid`나 `current_uid` 입력 없이 실제 `hsrunner` lookup과 `os.getuid()`만으로 실행 여부를 판정해야 한다.

### AC-3 같은 UID는 NOT_RUN

When lookup된 runner UID와 implementer UID가 같으면, 시스템은 같은 UID agent 검토를 OS 격리로 인정하지 않고 쓰기 전에 `not_run`을 반환해야 한다.

### AC-4 current process runner 아님 거부

When 현재 실제 프로세스 UID가 lookup된 runner UID가 아니면, 시스템은 보호 파일 쓰기를 `denied`로 반환하고 파일을 만들지 않아야 한다.

### AC-5 보호 root 검사

When 보호 root가 symlink이거나 root 밖 escape 상대 경로가 들어오거나 target 파일 경로가 symlink이거나 대상 일반 파일이 이미 존재하면, 시스템은 쓰기를 거부해야 한다.

### AC-6 runner 경계 통과 시 실제 파일 생성

When 현재 프로세스 UID가 lookup된 runner UID이고 implementer UID가 다르며 보호 root owner/mode와 대상 경로가 유효하면, 시스템은 새 보호 파일을 mode `0600`으로 쓰고 payload hash, byte count, 그리고 그 파일을 쓴 file descriptor에서 얻은 device/inode만 반환해야 한다.

## trusted bootstrap 경계

`hsrunner` 계정과 `hsrunner` 소유 `0700` 보호 root는 이 WU가 만들지 않는다. 운영 bootstrap 또는 후속 root-owned 준비 작업이 계정, 디렉터리 소유권, 권한, 실행 위임을 Git 밖에서 준비해야 한다. 이 WU는 그 준비가 없을 때 `not_run`을 반환하고, 준비가 있을 때만 현재 프로세스가 실제 runner UID인지 확인한다.

## 검증

```bash
cd humansearch && uv run --no-sync pytest -q tests/test_hs_0402a.py
cd humansearch && uv run --no-sync ruff check
cd humansearch && uv run --no-sync mypy src tests
cd humansearch && uv run --no-sync pytest -q
bash verify.sh
```

테스트의 `hsrunner` lookup은 unit 합성이다. mock/unit 성공은 실제 OS 별도 계정 증명이 아니다.

## 후속 NOT_RUN

실제 `hsrunner` 계정 소유 디렉터리, 구현자 UID 쓰기 `EACCES`, runner 쓰기 성공, sudo-free 실행 위임은 별도 계정 경계 준비 전까지 `NOT_RUN`이다. HS-04.03은 이 경계를 사용해 원본 출력을 Git 밖 보호 경로에 저장하되 일반 보고에는 원문을 노출하지 않고 hash와 PII 없는 요약만 남겨야 한다.

## 결정 카드 — 같은 UID 동시 실행 창은 HS-05.04 로 이관

- **무엇을**: 같은 러너 UID 의 다른 실행이 보호 root 나 최종 이름을 바꾸는 창은 이 WU 안에서 닫지 않는다. HS-05.04 사용권(채널당 러너 인스턴스 1개)이 선행 조건이다.
- **왜**: 이름 기반 연산으로는 닫히지 않는 창이다. 확인과 행동 사이에는 언제나 틈이 있고, 확인을 한 번 더 해도 같은 틈이 그대로 남는다. 잠금 파일로 게시 구간을 직렬화해도 협조하지 않는 같은 UID 실행을 막지 못하며, 잠금 파일 자체가 새 보호 대상이 된다.
- **그때까지의 계약**: 영수증의 `path` 와 `temp_path` 는 **게시 시점 경로**이며 이후 다른 파일을 가리킬 수 있다. 소비자는 두 후보를 차례로 열어 `device`/`inode`/`sha256` 이 맞는 것을 우리 파일로 판별한다. 경계는 (1) 소유를 증명할 수 없는 최종 이름을 어떤 실패 경로에서도 unlink 하지 않고, (2) 식별값을 payload 를 담은 file descriptor 에서만 얻으며, (3) 정리에 실패하면 남은 임시 경로를 함께 준다.
- **대가**: 단일 인스턴스 보장이 서기 전까지 이 창은 열려 있다. 그동안의 피해는 "성공 영수증이 남의 파일을 가리킴" 이 아니라 "우리 파일이 임시 이름으로 남고 영수증이 그 사실을 밝힘" 으로 한정된다.
- **되돌리기**: HS-05.04 에서 인스턴스 1 개가 보장되면 이 창은 사라지고 위 세 방어는 이중 안전장치로 남는다.
