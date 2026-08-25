# Worktree `.secret-patterns` 자동 bootstrap goal — 2026-08-25

VERDICT: COUNTER_RED_PENDING

## T 계약

새 linked worktree가 checkout될 때 저장소의 기존 `scripts/install-hooks.sh`를 자동 실행해
main worktree의 ignored `.secret-patterns`를 symlink하고 `core.hooksPath=hooks`를 readback한다.
실제 로컬 secret 원본이 없으면 `.secret-patterns.default`를 대신 연결하지 않고 실패한다.

## 불변조건

- 실제 `.secret-patterns` 내용은 출력하거나 커밋하지 않는다.
- main worktree의 `.secret-patterns`를 삭제·덮어쓰기하지 않는다.
- 기존 `install-hooks.sh`의 수동 설치 경로를 재사용한다.
- linked worktree 밖의 파일과 다른 Work Unit을 변경하지 않는다.
- RED 테스트는 구현 전에 commit하고 GREEN을 위해 약화하지 않는다.

## EARS AC

- AC1: When 실제 main `.secret-patterns`가 있는 저장소에서 linked worktree를 만들면, 새 worktree에 symlink가 자동 생성되어야 한다.
- AC2: When symlink를 readback하면, 대상은 main worktree의 실제 `.secret-patterns`여야 하고 존재해야 한다.
- AC3: When bootstrap이 끝나면, `core.hooksPath`는 `hooks`여야 한다.
- AC4: When 실제 main `.secret-patterns`가 없으면, linked worktree checkout hook은 nonzero로 실패해야 한다.
- AC5: When `.secret-patterns.default`만 있으면, 이를 실제 secret의 fallback으로 연결하지 않아야 한다.
- AC6: When 변경 범위를 diff하면 이 goal, 테스트, `hooks/post-checkout`, `scripts/install-hooks.sh`, `verify.sh`, hook SOT의 6파일뿐이어야 한다.
- AC7: When hook 실패 뒤 linked worktree가 등록된 채 남아도, 그곳의 `verify.sh`는 실제 main `.secret-patterns` 연결 없이는 `.secret-patterns.default`만으로 PASS하지 않아야 한다.
- AC8: When linked worktree의 symlink가 상대 경로로 같은 실제 main secret을 가리키면, 문자열 표현이 다르다는 이유만으로 차단하지 않아야 한다.

## counter-AC

- 새 worktree 생성은 성공했지만 `.secret-patterns`가 없다.
- 끊어진 symlink를 존재로 오인한다.
- `.secret-patterns.default`를 실제 secret으로 연결해 false-green을 만든다.
- hook 오류를 출력만 하고 exit 0으로 삼킨다.
- 수동 실행할 때만 동작하고 `git worktree add`에서는 실행되지 않는다.
- hook은 nonzero였지만 남은 linked worktree에서 `.secret-patterns.default`만으로 `verify.sh`가 false-green을 낸다.
- 같은 실제 파일을 가리키는 상대 symlink를 raw `readlink` 문자열 차이만으로 거부한다.

## 입출력·오류·경계 계약

- 입력: Git `post-checkout` 인자 3개와 현재 linked worktree.
- 출력: 성공 시 exit 0, 누락·실행 불가·readback 불일치 시 exit nonzero와 `BLOCKED` 메시지.
- 경계: 일반 main worktree checkout에서는 로컬 secret을 새로 만들지 않는다. linked worktree에서만 main 원본을 공유한다.
- 롤백: task branch/ref를 보존한 채 후속 GREEN commit을 되돌릴 수 있다.

## 소유권

- `docs/engineering/worktree-secret-bootstrap-goal-2026-08-25.md`
- `tests/worktree-secret-bootstrap.test.mjs`
- `hooks/post-checkout`
- `scripts/install-hooks.sh`
- `docs/sot/hook-contracts.md`
- `verify.sh`

## 검증 명령

```text
node --test tests/worktree-secret-bootstrap.test.mjs
bash -n hooks/post-checkout scripts/install-hooks.sh
bash scripts/acceptance-principles-check.sh
bash verify.sh
bash scripts/check-docs-sot.sh
git diff --check
git show --check HEAD
```

## 판정 장부

- RED: `2026-08-25T22:05:14+09:00`, `node --test tests/worktree-secret-bootstrap.test.mjs`, tests 2, pass 0, fail 2, exit 1.
- RED 원문: `/tmp/vhrec-bootstrap-red.PyuDAw/full.log`, SHA-256 `a8897d7a4c586ecfe5b0bc3d7be575393c6cf384f245124b30a3e5878e2f101f`.
- RED 해석: 자동 hook이 없어 실제 main secret link가 생성되지 않았고, 실제 secret 부재도 fail-closed하지 않았다.
- macOS `/var` 경로 별칭을 `realpath` 동일성으로 교정한 RED commit: `b5276cfac49ee3c7d7cdb3b6acb52a350efbd9f6`.
- 잘못된 symlink와 일반 파일 counter-test를 추가한 canonical RED commit: `a3680e1629d459d7a3d67b56df20e5c9892e57da`.
- canonical RED: tests 4, pass 0, fail 4, exit 1. 원문 `/tmp/vhrec-bootstrap-counter-red.A3zTpJ/full.log`, SHA-256 `027605a909db3aafd96a611b2666526f7c32148531abccd03203ec7d460d56b0`.
- frozen test SHA-256: `6a640d8e5ae3f967b711bb16fee25f825fe0ee71851d6ef4116dab693f0b92ee`.
- GREEN candidate: `2026-08-25T22:10:01+09:00`, tests 4, pass 4, fail 0, exit 0; shell syntax, principles 34/34, verify, docs SOT, cached diff 모두 exit 0.
- GREEN 원문: `/tmp/vhrec-bootstrap-precommit.rPCqAF/full.log`, SHA-256 `9b91f939d9eae4b9968245385e2bbf9932fced3f6d27653f070df29ca762a045`.
- V1 `a9573ec8-ac7b-4274-b93b-37da3bafd5a6` finding `V1-F002`: hook 실패 잔여 linked worktree에서 실제 secret 없이 `.secret-patterns.default`만으로 `verify.sh` exit 0. 로컬 재현 `/tmp/vhrec-bootstrap-v1f002-repro.MRGWGz/full.log`, SHA-256 `18e6e021168e6873983cbdc7f9039ebef2cdfdc485393bc15f554ed6c65d50e7`.
- V1 finding `V1-F004`: 실제 main secret을 가리키는 상대 symlink가 raw target 문자열 차이로 차단됨. 로컬 재현 `/tmp/vhrec-bootstrap-v1f004-repro.hOJKAD/full.log`, SHA-256 `fabc89613b7ce6fb300450763f7ea7c50f29267d024033053e8756b3c1f5ccc1`.
- V1-F002/F004 counter RED: `2026-08-25T23:02:04+09:00`, exact HEAD `6bb8e1e4998b0cc79ee879e8e18b9fb4a66e40ac`, `node --test tests/worktree-secret-bootstrap.test.mjs`, tests 6, pass 4, fail 2, exit 1.
- counter RED 원문: `/tmp/vhrec-bootstrap-v1f002-f004-red-canonical.ankQYV/full.log`, SHA-256 `bf7ac6707cff33b12ec50a925bbfe11cd8d8eeb0fef7d321a037edb0b0067891`; frozen test SHA-256 `e18025eecd8cd40d1b5aa8c930b9f171443a01fdb64acab62a9a0b3bf1be10ff`.
- counter RED 해석: 기존 4개 bootstrap 단언은 모두 통과했고, 잔여 linked worktree의 default-only false-green과 의미상 동일한 상대 symlink 수용 두 동작만 실패했다.
- G: `NOT_RUN`
- V1: `NOT_RUN`
- V2: `NOT_RUN`
- T: `NOT_RUN`
