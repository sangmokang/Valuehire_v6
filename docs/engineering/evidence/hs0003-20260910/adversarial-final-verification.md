# HS-00.03 보강 후 최종 적대 검증

## 결론

공백 입력과 같은 줄 동시 존재를 보강한 최종 후보는 정상 시험 23개를 통과했고, 결함 열한 가지를 각각 넣은 임시 사본은 모두 시험에 잡혔다. 제품 작업트리는 실행 전후에 바뀌지 않았다.

## 판단 근거

- 검증한 제품 묶음은 manifest SHA-256 `c466946aad003159a07c052979e8e0034ec4eeb0d3445d5a9ccb7952a6b7e6d4`, bundle SHA-256 `9517376e3755a69e4e9dfca8ac5ad859654cbb94dda8cd3b610075c61b40e23d`다.
- 고장 사본은 Git HEAD에 manifest의 제품 파일을 덮어쓴 임시 디렉터리에서 한 결함씩 만들었다.
- 첫 실제 Claude V1이 찾은 공백-only 입력 허용과 첫 정상 토큰 뒤 탐색 중단 약점을 새 사본 두 개로 추가했다.
- 결합 문자, 양방향 문자, 보이지 않는 문자, 다중문자 skeleton은 이 작업 계약의 제외 범위다.

## 기술 상세와 증거

```text
baseline                         rc=0  23 passed
always-allow                     rc=1  14 failed, 9 passed
always-reject                    rc=1  1 failed, 22 passed
drop-fullwidth                   rc=1  9 failed, 14 passed
drop-confusables                 rc=1  6 failed, 17 passed
drop-token-boundary              rc=1  1 failed, 22 passed
drop-confusable-boundary         rc=1  3 failed, 20 passed
replace-invalid-utf8             rc=1  1 failed, 22 passed
allow-whitespace-name            rc=1  1 failed, 22 passed
only-first-occurrence            rc=1  1 failed, 22 passed
bypass-data-sha                  rc=1  1 failed, 22 passed
ignore-workflow-shell-result     rc=1  5 failed, 18 passed
ADVERSARIAL: PASS normal=1 mutants_killed=11/11 product_workspace_untouched=true
```

→ 정상 후보만 전부 통과했다. 경계·입력·데이터·shell 배선의 핵심 효과를 하나씩 뺀 열한 사본은 모두 비정상 종료해 시험의 해당 단언에 잡혔다.

```text
temporary harness: /tmp/hs0003-final-adversarial.py
harness sha256: 7ea448a33742b914ae0f3a4a99dfd03881b609b9b300d1ca13aa1ef5cbec9e5e
raw log: /tmp/hs0003-final-adversarial-v2.log
log sha256: 13f50ea0226149ade64918bd96424ee15b762479ffe9a814d9b9da5775c3668b
tracked ledger: docs/engineering/evidence/hs0003-20260910/adversarial-final-verification.md
```

→ 임시 harness는 저장소의 제품·시험·CI에 추가하지 않았다. 이 추적 장부, 후보 manifest와 실행 지문이 세션 종료 뒤 남는 근거다.

## 확인하지 않은 범위

- 원격 CI, push, PR, 병합은 실행하지 않았다.
- 실제 포털, 메시지, 운영 저장소는 호출하지 않았다.
- 같은 사용자 권한의 임시 사본 검증이며 운영체제 권한을 분리한 감사가 아니다.
