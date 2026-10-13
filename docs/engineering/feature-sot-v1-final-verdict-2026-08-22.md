# Claude V1-F 최종 적대검증 원문 — PASS

- 실행 신원: Claude Code 2.1.238
- 세션: `8f137725-34a2-499c-93ee-abc92937bdb2`
- 인증 환경: `ANTHROPIC_API_KEY=UNSET`
- 종료값: `0`
- 실행 전후 상태 SHA-256: `c38d64fff82435933a31d1eda133ce20d0b89c7f2704017ec4f6ef8761ad65f4`
- 실행 전후 산출물 SHA-256: `c8a8f86db166237a849f321b33938ccdc1a432ff9a494014f8a07d983fdad6bf`

## 원문

VERDICT: PASS

## 결론

요청한 네 가지 확인을 모두 실행했고, 전부 기대대로 동작했습니다. 저장소 원본에서 구조 검사는 통과(종료값 0)했고, 공백 오류도 없었습니다. 임시 사본에 새 CI 설정 파일을 하나 더 넣으면 검사가 즉시 실패(종료값 1)하면서 `CI workflow coverage changed` 메시지와 함께 발견된 파일 목록을 그대로 보여줍니다. 검사 스크립트는 431줄로 500줄 한도 안에 있고, 앞선 회차에서 확인된 표면 개수 6/3/32/11/23/29/2/2가 그대로 유지됩니다. 새로 생긴 결함은 없습니다.

작업 중 밝혀둘 점: 첫 임시 사본은 Git이 추적하는 파일만 복사해 아직 커밋되지 않은 `docs/sot/features/`가 빠졌고, 그 탓에 엉뚱한 실패가 났습니다. 전체 디렉터리를 통째로 복사해 다시 실행했으며, 아래 증거는 재실행 결과입니다. 임시 사본은 모두 삭제했고 원본 저장소는 손대지 않았습니다.

## 판단 근거

- **택한 해석**: "구조 검사가 종료값 1과 해당 문구를 낸다"를 스크립트 전체의 최종 종료값과 표준출력 문구로 판정했습니다. 개별 체크 함수의 예외 타입이 아니라, 사용자가 실제로 보는 결과를 기준으로 삼았습니다.
- **버린 해석**: 원본 저장소에 직접 `synthetic.yml`을 만들어 검증하는 방식은 읽기 전용 지시에 어긋나므로 버렸습니다. Git이 추적하는 파일만 복사하는 방식도, 미추적 상태인 기능 문서가 빠져 검증 대상 자체가 달라지므로 버렸습니다.
- **틀리면 깨지는 것**: 이 판정은 "새 CI 설정 파일이 늘어나면 사람이 명시적으로 분류하기 전까지 검사가 막는다"는 전제 위에 서 있습니다. 이 전제가 깨지면, 분류되지 않은 CI 단계가 조용히 늘어나 카탈로그가 실제 파이프라인과 어긋나도 아무도 모르게 됩니다.

## 기술 상세와 증거

원본 저장소 실행 결과입니다.

```text
PASS: feature SOT structure catalog=1 features=6 categories=3 invariants=32 product_files=11 ci_steps=23 ci_commands=29 hooks=2 contract_surfaces=2 paths=validated
OK: docs/sot 재구성 AC 전부 충족
EXIT=0
```
→ 해석: 기능 6개, 분류 3개, 불변조건 32개, 제품 파일 11개, CI 단계 23개, CI 명령 29개, 훅 2개, 계약 표면 2개. V1-E가 확인한 숫자와 완전히 일치합니다.

`git diff --check`는 EXIT=0, `wc -l scripts/check-docs-sot.sh`는 431줄이었습니다.

임시 사본에 `.github/workflows/synthetic.yml`을 추가한 결과입니다.

```text
FAIL: feature SOT structure — CI workflow coverage changed; explicitly classify workflow files: ['.github/workflows/synthetic.yml', '.github/workflows/verify.yml']
EXIT=1
```
→ 해석: 요구된 문구와 종료값이 정확히 나왔고, 어떤 파일이 늘었는지까지 알려 줍니다.

해당 로직은 `scripts/check-docs-sot.sh:344`(workflows 디렉터리의 실제 파일 집합 수집)와 `scripts/check-docs-sot.sh:347`(집합이 `verify.yml` 하나와 다르면 예외 발생)에 있습니다.

## 반증 기록 — 깨뜨리려다 실패한 시도

1. **`.yaml` 확장자로 우회**: 차단됨. 동일 문구로 실패했습니다.
2. **추가 파일을 `verify.yml`을 가리키는 심볼릭 링크로 위장**: 차단됨. 링크 대상이 같아도 파일 수가 늘어난 사실을 잡아냈습니다.
3. **`verify.yml` 자체를 심볼릭 링크로 치환**: 통과. 이는 의도된 동작입니다(내용이 동일하므로 표면이 바뀌지 않음).
4. **`verify.yml` 삭제**: 차단됨. `catalog coverage.control_roots does not exist: .github/workflows/verify.yml`로 실패하여, 파일이 늘어나는 방향뿐 아니라 사라지는 방향도 막힘을 확인했습니다.
5. **하위 디렉터리 `.github/workflows/sub/x.yml`**: 통과. GitHub Actions는 하위 디렉터리의 워크플로를 실행하지 않으므로 결함이 아닙니다.
6. **`.YML` 대문자 확장자**: 통과했습니다. 다만 GitHub Actions는 소문자 `.yml`/`.yaml`만 인식하므로 실제 CI에서 실행되지 않는 파일이며, 검사 회피 경로가 되지 못합니다. 결함으로 계상하지 않고 관찰 사항으로만 남깁니다.

되돌리기 확인: 임시 사본에서 `synthetic.yml`을 지우자 곧바로 `OK: docs/sot 재구성 AC 전부 충족`과 종료값 0으로 복귀했습니다. 즉 검사는 일단 실패하면 계속 실패하는 상태에 갇히지 않고, 원인을 제거하면 정확히 원상 복구됩니다.
