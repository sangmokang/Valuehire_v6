# HS-00.03 최종 후보 적대 검증

## 결론

최종 후보의 정상 대조군은 통과했고, 서로 다른 결함 열 가지를 주입한 사본은 모두 시험에 잡혔다. 원본 작업트리는 변이 실행 전후에 바뀌지 않았다.

## 판단 근거

- 검증 대상은 후보 manifest SHA-256 `41aa89efa6c883a64d333d9428fea33a22a1f13f8fe1142364e58521649aead4`, bundle SHA-256 `0ccf996ee201ecabe4b1a66b6c00f2a04a669c5476960f8c1feca026f12b8c85`와 같은 제품 파일이다.
- 검증기는 제품 작업트리를 복사한 임시 사본만 바꾸고 `humansearch/tests/test_hs_0003.py`를 실행했다.
- 항상 허용·항상 거부뿐 아니라 전각, Unicode 동형 문자, 토큰 경계, 경계 치환, UTF-8 strict 입력, 빈 이름, 데이터 지문, 실제 shell 배선을 각각 무력화했다.
- 결합 문자, 양방향 문자, 보이지 않는 문자, 다중문자 skeleton은 계약에서 제외했으므로 이 검증의 해결 주장에 포함하지 않는다.

## 기술 상세와 증거

```text
baseline                         rc=0  21 passed
always-allow                     rc=1  13 failed, 8 passed
always-reject                    rc=1  1 failed, 20 passed
drop-fullwidth                   rc=1  8 failed, 13 passed
drop-confusables                 rc=1  5 failed, 16 passed
drop-token-boundary              rc=1  1 failed, 20 passed
drop-confusable-boundary         rc=1  3 failed, 18 passed
replace-invalid-utf8             rc=1  1 failed, 20 passed
allow-empty-name                 rc=1  1 failed, 20 passed
bypass-data-sha                  rc=1  1 failed, 20 passed
ignore-workflow-shell-result     rc=1  5 failed, 16 passed
ADVERSARIAL: PASS normal=1 mutants_killed=10/10 product_workspace_untouched=true
```

→ 정상 구현은 21개 시험을 통과했고, 열 가지 고장 사본은 각각 한 개 이상의 행동 단언을 깨뜨렸다. 실제 workflow·정본 경로에서 helper 결과를 무시하는 사본도 다섯 개 시험에 잡혔다.

```text
temporary harness: /tmp/hs0003-final-adversarial.py
harness sha256: 5bb7a48a21c20b8efe1a89a349848f26e1b2dfe18cd3a0825be0e357ada886d5
raw log: /tmp/hs0003-final-adversarial.log
log sha256: 6edb0a6d1137caf82aae9f2629f44655bf73d339d0484cc4032fcf12ebd64a7b
tracked ledger: docs/engineering/evidence/hs0003-20260910/adversarial-verification.md
```

→ 임시 harness는 저장소에 새 acceptance 체계를 추가하지 않았고, 지문만 장부에 남겼다. `/tmp` 원문은 로컬 세션 수명에 따르는 보조 증거이며, 위 결과와 후보 manifest가 추적 증거다.

## 확인하지 않은 범위

- 원격 CI, push, PR, 병합은 실행하지 않았다.
- 실제 포털, 메시지, 운영 저장소는 호출하지 않았다.
- 같은 사용자 권한의 임시 사본 검증이며 운영체제 권한을 분리한 감사가 아니다.
