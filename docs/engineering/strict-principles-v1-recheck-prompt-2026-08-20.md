# V1 결함 수정 재검증 요청

같은 저장소의 현재 미커밋 변경을 읽기 전용으로 다시 검증하십시오. 직전 V1에서 발견한 주석·echo·최상위 exit 뒤 죽은 코드·`if false` 분기 결함, 후속 Codex V2가 발견한 고정 Git 지문 우회, 그리고 직전 V1이 발견한 고정 임시경로 접두사 우회를 구현자가 무작위 실행 probe 방식으로 수정했습니다.

반드시 다음을 직접 수행하십시오.

1. 직전 재현 절차처럼 실제 pre-push 글로브를 깨고 정확한 target 문자열을 주석에만 남긴 격리 사본에서 `acceptance-principles-check.sh`와 `check-mechanism-registry.sh`가 모두 FAIL하는지 확인하십시오.
2. target 문자열을 활성 `echo` 줄에만 남기는 변형도 두 검사기가 실행 배선으로 오판하지 않는지 공격하십시오.
3. 실제 글로브를 깨고 정상 collector를 최상위 `exit` 뒤에만 남기는 직전 공격도 두 검사기가 FAIL시키는지 확인하십시오.
4. 실제 collector를 `found=""`로 무력화하고 정상 collector를 `if false; then ... fi` 안에만 남기는 직전 공격도 FAIL시키는지 확인하십시오.
5. `scripts/verify/check-pre-push-runtime.sh`가 격리 Git 저장소에서 probe 스크립트를 글로브로 실제 발견·실행하고 실패 종료값을 전파하는지 확인하십시오.
6. 실제 collector를 고정된 Git email `strict-probe@example.invalid` 및 commit subject `runtime probe fixture`일 때만 실행하고 평소에는 `found=""`로 두는 공격이 두 검사기에서 FAIL하는지 확인하십시오.
7. runtime helper가 probe 경로, Git user/email, commit subject, marker/token, 실패 종료값을 매 실행 바꾸고 `PRE_PUSH_RUNTIME_MARKER` 같은 고정 환경 지문을 hook에 전달하지 않으며, 현재 저장소의 실제 CI workflow를 sandbox에 복제하는지 확인하십시오. helper를 연속 두 번 실행해 서로 다른 probe가 모두 PASS하는지 확인하십시오.
8. 실제 collector가 `pwd | grep -q 'pre-push-runtime\.'`일 때만 실행되는 공격이 두 검사기에서 FAIL하는지 확인하십시오. helper의 `mktemp` 경로에는 더 이상 의미 있는 고정 접두사가 없어야 하고, 임시 루트의 직접 자식·일반 디렉터리 검증으로 정리 안전성을 유지해야 합니다.
9. 정상 저장소에서 `acceptance-principles-check.sh`, `acceptance-principles-mutations.sh`, `check-mechanism-registry.sh`, `acceptance-verify-ac-m.sh`, `check-strict-principles-skills.sh`, `verify.sh`를 다시 실행하십시오.
10. 새 반례가 실제 줄바꿈을 포함해 입력을 변조하며, 원본 저장소를 바꾸지 않는지 확인하십시오.
11. 다른 회귀나 새로운 우회가 있으면 같은 수준으로 보고하십시오. 단, 임의의 적대 코드가 자신이 검증 중임을 어떤 방식으로든 알아내는 일반적인 결정불가능성 자체가 아니라, 이 구현이 공개한 고정 지문 또는 명시된 계약을 실제로 우회하는 재현 가능한 결함을 판정 대상으로 삼으십시오.

첫 줄은 `VERDICT: PASS|FAIL`로 쓰고, 직전 결함의 재현 결과와 전체 명령 종료값을 생략하지 마십시오. 파일을 수정하거나 생성하지 마십시오.
