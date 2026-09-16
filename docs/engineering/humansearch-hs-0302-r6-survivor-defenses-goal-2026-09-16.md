# HS-03.02 R6 — V2 생존 방어 7곳 시험 편입 goal (2026-09-16)

위험등급 L3(저장 계층·개인정보 파생값 방어의 검증 장치). 기준은 `task/hs-0302-candidate-identity-20260914`의 HEAD(`4650886`, 장부 커밋)이며 이 WU 는 그 위에 쌓는 스택 브랜치 `task/hs-0302-r6-survivor-defenses-20260916` 이다. 제품 배송 상태는 `NOT_APPLICABLE`(제품 코드 무변경, 시험·인수 검사만 추가)이다.

## 1층 — 결론

HS-03.02 마감 검증의 V2 가 인수 변이 목록 밖에서 만든 새 변이 45종 중 7종이 살아남았다. 제품 코드는 일곱 경우 모두 올바르게 거부하지만, 그 방어 한 줄을 지워도 저장소의 어떤 시험도 빨개지지 않았다. 이 WU 는 그 7곳에 각각 시험 1건(길이 상한은 3+양성 1)과 인수 약화 변이 1종을 붙여 "지우면 빨개진다" 를 저장소 자산으로 만든다. 제품 동작은 바꾸지 않는다.

HS-03.02 브랜치에 직접 넣지 않은 이유는 P11③ 3,000줄 상한이다(2,980 + 약 280).

## 2층 — 판단 근거

- 변이는 목록이 아니라 생성으로 잡는다. 인수 스크립트의 변이 6종은 전부 잡혔지만 V2 가 방어 지점마다 새로 만든 변이에서 7종이 생존했다. 가장 무거운 것은 `candidate_identity.py:222`(commit 직전 승인 inode 대조)로, 단독으로 지우면 변이 사본이 보호 root 밖으로 옮겨진 파일에 행을 확정하는데도 127건이 전부 초록이었다.
- 버린 길: 시험을 HS-03.02 브랜치의 R5 파일에 얹기(P11③ 위반·R5 500줄 근접), 후속 WU 로만 적고 미루기(중간 결함을 알면서 병합). 인수 변이 판정을 전용 6차 파일까지 넓히되 전량 실행은 하지 않는다(변이당 수십 초).
- 틀리면 깨지는 것: 시험이 변이 사본이 아니라 원본 모듈을 읽으면 전부 초록이 된다. 그래서 인수 검사는 변이마다 `__file__` 이 사본 경로임을 확인한다.

## 인수 기준 (EARS)

- AC-R6-1: When INSERT 뒤 commit 전에 승인 DB 가 root 밖으로 rename 되고 호환 DB 가 그 자리에 놓이면 시스템은 `CandidateIdentityError("db file is not the approved file")` 를 내고 옮겨진 파일·승인 경로 어느 쪽에도 행을 남기지 않아야 한다.
- AC-R6-2: When 첫 경계 검사 뒤 DB 파일이 unlink 되면 시스템은 `_verify_db_location` 에서도 경로 없는 `CandidateIdentityError("db file is missing (ENOENT)")` 를 내야 하고 traceback 에 보호 경로가 없어야 한다.
- AC-R6-3: If 세 필드 중 하나가 513자 이상이면 시스템은 `too long` 으로 거부하고, 정확히 512자는 `inserted` 여야 한다.
- AC-R6-4: When `begin immediate` 가 `SQLITE_BUSY` 가 아닌 `OperationalError` 로 실패하면 시스템은 그 오류를 그대로 올려야 하며 `duplicate` 로 접지 않아야 한다.
- AC-R6-5: When 다른 연결이 EXCLUSIVE 잠금을 쥐어 승자 조회조차 BUSY 이면 시스템은 원문 `OperationalError` 대신 `CandidateIdentityError("db write lock wait exceeded")` 를 내야 한다.
- AC-R6-6: When 키 파일 자리나 `-journal` 자리에 FIFO 가 있으면 시스템은 5초 안에 `regular file` 거부를 내야 하며 읽기에서 멈추지 않아야 한다.
- AC-R6-7: When 위 방어 7곳 중 하나를 항상 통과하도록 바꾸면 `scripts/acceptance-hs-0302.sh` 의 약화 변이 판정이 그 사본에서 전용 시험 실패를 잡아 FAIL 이어야 한다. 명부는 137건이며 수집과 정확히 같아야 한다.

검증 명령: `cd humansearch && uv run --frozen pytest tests/test_hs_0302_r6_survivor_defenses.py -q` → 10 passed. `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh` → rc 0, CHECKED 36, 약화 변이 13종 "잡았다", 명부 137. 변이 사본 7종 각각 `pytest tests/test_hs_0302_r6_survivor_defenses.py` → 해당 시험 failed.

## counter-AC

- 시험이 사본이 아니라 설치된 원본 모듈을 import 해 변이가 무의미해진다.
- FIFO 시험이 구현이 멈추면 같이 멈춰 pytest 가 끝나지 않는다(스레드 마감 + 쓰기 쪽 열어 해제로 방지).
- 명부·상수·시험을 같이 낮추는 동반 약화(HS-03.02 goal 116행과 같은 한계, P13① 라벨 담당).
- 인수 변이의 sed 앵커가 원본에 없어 변이가 적용되지 않은 채 "잡았다" 가 된다(스크립트가 `cmp` 로 차단).

## 롤백·영향 반경

- 롤백: 이 브랜치의 커밋 2~3개 revert. 제품 코드·스키마 변경 없음.
- 영향 반경: `humansearch/tests/test_hs_0302_r6_survivor_defenses.py`(신규), `scripts/acceptance-hs-0302.sh`(변이 7종·6차 배선·명부 137), `scripts/verify/fixtures/hs-0302-required-tests.txt`(+10), `docs/sot/verification-commands.md` 27행 문구.

## 검증 장부

| 단계 | 상태 | 증거 |
|---|---|---|
| RED `974c711`(rebase 전 `b7f832c`) | 생존 7 | 인수 CHECKED 36 · FAIL 7(생존, 잡힌 시험 0) · rc 1 |
| GREEN `da45ff9`(rebase 전 `4fdae9a`) | PASS | 6차 10 passed, 변이 사본 7종 각각 전용 시험 failed(1·1·3·1·1·1·1), 인수 CHECKED 36 rc 0(변이 13종), 명부 137 정확, ruff·mypy rc 0 |
| 최종 SHA 검증 | 이 문서·프롬프트 커밋에서 실행 | 결과는 `private-reviews/hs-0302/claude-r6-closeout-<sha>/`(gitignored)와 다음 세션 재검증(프롬프트 v3)이 담는다 |

## 비범위

제품 코드 변경, 억제 만료 2건, HS-03.03 이후, decoy fd·키 지문·프로세스 장부·동반 약화(HS-03.02 goal 후속 WU 절).
