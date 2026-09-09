VERDICT: PASS

**결론**

검토를 요청하신 두 변경은 모두 계약대로 동작합니다. Ruby가 없는 환경에서 Work Unit 정책 검사는 "실행되지 않음"으로 정직하게 끝나고, 평소에는 이전과 똑같이 통과합니다. main에서 들어온 변경은 한 글자도 바뀌지 않고 그대로 살아 있으며, 이번 PR이 더한 것은 CI 실행 단계 두 줄뿐입니다. 소스 파일은 검토 전과 같은 상태이고, 제가 손댄 것은 임시 폴더 안의 사본뿐입니다.

**건너뜀·미확인·추정 (판정 앞에 밝힘)**

- 전체 pre-push와 전체 메타시험은 지시대로 실행하지 않았습니다. 요청 범위 밖의 다른 검사(P3, HumanSearch, Invoice 등)는 판정 대상이 아닙니다.
- 실제 GitHub Actions 러너에서 Ruby가 없을 때의 동작은 재현하지 않았습니다. PATH를 좁힌 로컬 격리 환경으로 대신했습니다. ubuntu-latest에는 Ruby가 기본 설치되어 있어 실제 CI에서는 이 경로가 열리지 않을 것으로 추정합니다.
- 문서 표 비교의 첫 시도에서 제 sed 표현식이 macOS에서 앞 공백을 벗기지 못해 29줄 전부가 차이로 표시되었습니다. 이는 제 도구 오류였고, 두 번째 배치에서 고쳐 29개 이름과 순서가 동일함을 확인했습니다. 재시도 1회입니다.
- 문서 변경(pr37-resolution-goal, INDEX, git-workflow, 미추적 verdict 파일)은 지시대로 검토 범위에서 제외했습니다.
- 명령 실행 배치는 2회, 확인용 배치 1회로 총 3회입니다. 3회째는 실행 검사 없이 비교 재확인과 임시 사본 삭제만 했습니다.

**판단 근거**

- 채택한 해석: "Ruby가 PATH에 없으면"을 PATH에 bash, git, grep, tee, mktemp, rm 등만 있는 격리 환경으로 해석했습니다. 계약서의 조건을 그대로 옮긴 것이며, 커밋 3019db7의 반례 시험도 같은 방식입니다.
- 버린 해석: `ruby` 이름의 가짜 실행 파일을 두어 실행 실패를 흉내 내는 방식은 "PATH 부재"가 아니므로 계약 대상이 아니라고 보고 시험하지 않았습니다. 이 경우는 가드를 통과해 checker 호출에서 실패하며, 그것은 이번 변경이 다루는 사건이 아닙니다.
- 틀리면 깨지는 것: 가드가 없으면 Ruby 부재가 exit 1, VERDICT FAIL, CHECKED 5로 보고되어 "검사가 돌았고 정책이 틀렸다"로 오해됩니다. 가드 삭제 사본으로 이를 실제 재현했고, 계약 시험 86건이 그 사본을 FAIL로 잡는 것도 확인했습니다.
- main 보존은 merge-base 기준으로 main이 바꾼 6개 파일을 병합 결과와 비교해 판정했습니다. 4개는 byte 동일, verify.yml과 verification-commands.md는 이번 PR이 의도적으로 추가한 부분만 다릅니다.

**기술 상세와 증거**

증거 원문 보존 경로는 아래 하나입니다. 실행별 전체 출력이 파일로 남아 있습니다.

```
/tmp/v1-ruby-guard.HCEGbM/{A1_direct,A2_wrapper,A3_contract,B1_direct_noruby,B2_wrapper_noruby,C1_noguard_direct,C2_noguard_wrapper,C3_contract_noguard,D1_p23,D2_ci}.out
```

1. **Ruby 부재 가드 (3019db7→e967df4)**

`scripts/acceptance-work-unit-policy.sh:8` 은 PATH에서 ruby를 찾지 못하면 NOT_RUN 세 줄을 찍고 exit 2로 끝내는 가드입니다. git 저장소 판별보다 앞에 놓여 있어, 어떤 검사도 세기 전에 빠져나갑니다. `scripts/verify/run-acceptance.sh:40` 은 대상이 0이 아닌 종료값이면 그 값을 그대로 넘기는 줄이라, wrapper도 exit 2가 됩니다.

```json
{"tag":"A1_direct","exit":0,"tail":"PASS: structured policy and generated document\nCHECKED: 5\nVERDICT: PASS"}
{"tag":"A2_wrapper","exit":0,"tail":"CHECKED: 5\nVERDICT: PASS\nOK(run-acceptance): ... 판정 6건, CHECKED 5"}
{"tag":"B1_direct_noruby","exit":2,"tail":"VERDICT: NOT_RUN\nREASON: ruby runtime unavailable\nCHECKED: 0"}
{"tag":"B2_wrapper_noruby","exit":2,"tail":"REASON: ruby runtime unavailable\nCHECKED: 0\nFAIL(run-acceptance): ... 종료값 2"}
{"tag":"A3_contract","exit":0,"tail":"PASS: Ruby unavailable scripts/verify/run-acceptance.sh\nCHECKED: 86\nVERDICT: PASS"}
```
→ 해석: 정상 경로는 exit 0, CHECKED 5, PASS로 유지됩니다. Ruby 부재는 직접 실행과 wrapper 모두 exit 2, NOT_RUN, CHECKED 0입니다. 계약 시험 86건은 "Ruby unavailable" 두 건을 포함해 전부 통과했습니다.

반증 기록으로, 가드 6줄을 지운 mktemp 사본을 같은 격리 PATH로 돌렸습니다.

```json
{"tag":"C1_noguard_direct","exit":1,"tail":"... line 42: ruby: command not found\nCHECKED: 5\nVERDICT: FAIL"}
{"tag":"C3_contract_noguard","exit":1,"tail":"FAIL: Ruby unavailable scripts/acceptance-work-unit-policy.sh ... CHECKED: 86\nVERDICT: FAIL"}
```
→ 해석: 가드가 없으면 도구 부재가 정책 실패(exit 1, FAIL, CHECKED 5)로 둔갑합니다. 이것이 e967df4가 고친 문제이며, 3019db7의 반례 시험이 이 회귀를 실제로 잡습니다. 이 사본으로 계약을 깨려 했고 실패했습니다.

checker와 renderer 정책 의미 변화는 없습니다. 3019db7→e967df4 diff는 셸 스크립트 7줄 추가뿐이며 Ruby 파일은 건드리지 않았습니다. POLICY_CHECKED 22 단언도 그대로입니다.

2. **main 4379b2f 통합 보존 (e967df4→7dec976)**

| 파일 | 4379b2f 대비 병합 결과 |
|---|---|
| scripts/acceptance-verified-sha.sh | byte 동일 |
| scripts/verify/check-verified-sha.sh | byte 동일 |
| docs/sot/principles.yaml | byte 동일 |
| docs/sot/coding-principles.md | byte 동일 |
| .github/workflows/verify.yml | PR37 스텝 2개(6줄) 추가만 |
| docs/sot/verification-commands.md | 문서 표 갱신 (범위 외) |
→ 해석: main이 바꾼 P23 판정기와 인수 검사, principles 두 파일은 그대로입니다. verify.yml의 concurrency 그룹 키(event_name과 ref 결합, main은 취소 제외)와 30분 timeout은 `verify.yml:23-24` 와 `verify.yml:33` 에 main 원문 그대로 남아 있습니다.

```json
{"tag":"D1_p23","exit":0,"tail":"CHECKED: 44\nVERDICT: PASS\nOK(run-acceptance): scripts/acceptance-verified-sha.sh — 판정 45건, CHECKED 44"}
{"tag":"D2_ci","exit":0,"tail":"CHECKED: 14\nVERDICT: PASS\nOK(run-acceptance): scripts/acceptance-ci-step-integrity.sh — 판정 15건, CHECKED 14"}
```
→ 해석: main의 P23 인수 검사 44건과 CI 스텝 무결성 검사 14건이 병합 결과에서 통과합니다. 문서 표의 29개 스텝 이름은 verify.yml의 name 순서와 완전히 같습니다.

3. **최종 소스 상태**

HEAD는 7dec976 그대로이며, scripts와 .github는 HEAD와 동일합니다. 작업 트리의 변경은 검토 시작 시점과 같은 문서 3개 수정과 미추적 verdict 문서 1개뿐입니다. git 환경변수는 실행 전 해제했고, 변조는 /tmp의 mktemp 사본에서만 했으며 그 사본들은 삭제했습니다. 증거 폴더 하나만 남겼습니다.

**결함**

이번 범위에서 결함은 발견하지 못했습니다. 설계 지적 한 가지를 남깁니다.

- 무엇을: Ruby 부재 시 wrapper는 exit 2로 CI를 빨갛게 만듭니다.
- 왜: NOT_RUN을 초록으로 보이게 두면 검사 없음이 통과로 읽히므로, 빨간 것이 계약에 맞습니다.
- 버린 길: 부재 시 스킵하고 초록으로 두는 방식은 P23의 "모르는 것을 통과로 세지 않는다" 원칙과 충돌합니다.
- 대가: 러너 이미지에서 Ruby가 빠지면 정책과 무관하게 CI 전체가 실패합니다.
- 되돌리기: 가드 6줄을 지우면 이전 동작으로 돌아가지만, 계약 시험 86건 중 2건이 즉시 실패합니다.
