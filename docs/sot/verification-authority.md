# Valuehire v6 — 검증 권한과 신뢰 경계 (SOT)

최종 갱신: 2026-08-19

근거와 실행 기록: `docs/engineering/verification-authority-goal-2026-08-19.md`

## 상위 원칙

**LLM의 자기 판정에는 공식 권한이 없다.** LLM은 구현자·시험 작성자·반례 제안자·검토자로 일할 수 있지만, 같은 권한으로 작성한 보고서의 `PASS`, `COMPLETE`, `MERGEABLE` 문구는 정책 입력이 아니다. 문자열을 금지해서가 아니라, 판정 권한이 그 문구의 작성자에게 없기 때문이다.

공식 상태 `VERIFIED`는 저장소 밖의 신뢰된 정책 게이트만 다음 튜플에 귀속해 발급할 수 있다.

```text
VERIFIED(repository, workflow identity, required check, target SHA, run identity)
```

SHA 없는 단독 `PASS`는 공식 상태가 아니다. 과거 SHA의 성공 기록은 새 SHA로 승계되지 않는다.

## 상태 모델

### 구현자·LLM·로컬 검사에서 생성 가능한 상태

| 상태 | 뜻 |
|---|---|
| `LOCAL_CANDIDATE` | 대상 SHA와 검사 증거가 맞지만 외부 정책 승인을 받지 않은 후보 |
| `FAIL` | 입력·관계·필수 이름·실행 결과가 계약을 위반 |
| `VERIFIER_FAIL` | 막아야 할 고장 주입이 살아남아 검증 장치 자체를 신뢰할 수 없음 |
| `STALE` | 성공 증거가 현재 대상 SHA가 아닌 과거 SHA에 귀속 |
| `POLICY_REVIEW_REQUIRED` | 보호 영역이 바뀌었거나 별도 승인·외부 정책 확인이 필요 |
| `BLOCKED` | 권한·요금제·원격 부재 때문에 필수 확인을 수행할 수 없음 |
| `UNVERIFIED` | 필수 check가 아직 끝나지 않았거나 결과가 없음 |

### 외부 정책만 생성 가능한 상태

| 상태 | 뜻 |
|---|---|
| `VERIFIED` | 신뢰된 workflow, 필수 check, 대상 SHA, run identity, merge 대상 관계, 보호 영역 승인 증거를 외부 정책이 모두 확인한 상태 |

저장소 안의 스크립트는 `VERIFIED`를 출력하지 않는다. 로컬 fixture의 성공은 `LOCAL_CANDIDATE`이며, 이번처럼 보호 파일을 함께 바꾼 변경은 `POLICY_REVIEW_REQUIRED`다.

## 판정 입력과 SHA 귀속

필수 입력은 `repository`, `workflow_identity`, `required_check`, `target_sha`, `check_sha`, `run_identity`, `check_status`, `check_conclusion`, `target_kind`, PR HEAD 관계다.

- 일반 PR: `target_sha == check_sha == pr_head_sha`여야 한다. 과거 check SHA면 `STALE`다.
- Merge Queue: GitHub가 만든 `merge_group_sha`와 그 그룹에 포함된 `pr_head_sha`의 관계가 증거에 있어야 한다. 관계를 확인하지 못하면 `FAIL`이다.
- check가 미완료면 `UNVERIFIED`; 필수 이름 또는 workflow identity가 다르면 `FAIL`; SHA가 없으면 `FAIL`이다.
- GitHub 성공값을 복사한 LLM 보고서나 수동 fixture는 외부 권한 증거가 아니므로 `VERIFIED`로 승격할 수 없다.

## 보호된 검증 영역

정확한 내부 파일 목록은 `docs/sot/verification-protected-surface.yaml`이 관리한다. 범주는 다음과 같다.

- GitHub Actions 검증 workflow와 필수 check 선언
- 요구사항·상태 변환·SHA 대조 규칙
- mutation catalog, fixture, runner
- 보호 영역 manifest와 이를 검사하는 checker
- 로컬 pre-push 연결과 merge 정책 정본
- branch ruleset·branch protection·CODEOWNERS 가용성 선언

manifest, checker, workflow는 같은 저장소와 같은 쓰기 권한 아래 있다. 따라서 이 장치는 변경 사실과 지정된 약화를 **탐지**하지만 비협조적 작성자의 수정을 **차단**하지 않는다. 내부 결과의 보장 수준은 `DETECT_ONLY`다.

외부 상태는 다음 네 값만 쓴다.

| 상태 | 사용 조건 |
|---|---|
| `ENFORCED` | 읽기 전용 조회로 실제 외부 정책 차단이 확인됨 |
| `DETECT_ONLY` | 저장소 내부 검사로 변경 사실만 발견함 |
| `UNAVAILABLE` | 요금제·제품 제약 또는 장치 부재가 확인됨 |
| `BLOCKED` | 조회 권한 부족 등으로 가용 여부를 확인할 수 없음 |

2026-08-19 읽기 전용 조회에서 branch protection과 repository ruleset은 모두 private 저장소 요금제 제한 HTTP 403을 반환했다. `.github/CODEOWNERS`도 없다. 따라서 현재 외부 강제는 `UNAVAILABLE`, 내부 manifest와 checker는 `DETECT_ONLY`다.

## 실행 가능한 요구사항 계약

`docs/sot/verification-requirements.yaml`의 각 요구사항은 정확히 다음 필드를 가진다.

- `id`
- `invariant`
- `counterexamples`
- `verifier`
- `stage`
- `authority`
- `coverage_status`: `COVERED`, `MANUAL`, `UNREGISTERED`, `BLOCKED`

빈 invariant·빈 counterexample·존재하지 않거나 실행 실패한 verifier·실제 CI/pre-push에 연결되지 않은 stage·중복 키·계약 밖 필드는 실패다. YAML은 Ruby Psych로 파싱하고 셸 문자열 분해로 흉내 내지 않는다.

이번 검증 권한 요구사항은 완전 계약으로 등록한다. 아직 전환하지 않은 기존 P1~P22는 `UNREGISTERED`로 자동 집계하며, 하나라도 남아 있으면 저장소 전체에 대한 공식 `VERIFIED`를 발급할 수 없다.

## 검증 시스템 자기 실패

mutation runner는 `mktemp` 격리 복사본만 고장 내고 원본을 수정하지 않는다. 지정 mutation이 기대한 실패 또는 제한 상태를 만들지 못하면 대상 기능이 아니라 검증 장치를 `VERIFIER_FAIL`로 판정한다.

상위 실행기는 mutation 집계 한 줄만 믿지 않는다. 내장된 각 필수 case의 상세 결과와 원본 무변경 증거가 모두 존재하고, 전체 수·차단 수·생존 수·정상 대조군 수가 내장 목록과 일치해야 한다. acceptance 진입점은 core 검증기의 종료값뿐 아니라 허용된 후보 상태, 대상 SHA, 생존 mutation 0건이라는 출력 계약을 별도로 확인한다. 이 장치는 조기 `exit 0`과 가짜 집계의 대표형을 탐지하지만, 같은 저장소 쓰기 권한으로 모든 검사 층과 목록을 함께 바꾸는 행위를 외부에서 차단하지는 않는다.

runner의 조기 성공 종료, case 삭제, case와 기대 수 동반 하향은 요구사항 계약의 고정 catalog와 실행 출력 수를 교차 확인한다. manifest와 checker를 함께 약화하는 지정 공격은 제3의 계약 목록이 잡지만, 동일 권한 사용자가 세 목록을 모두 바꿀 수 있는 구조적 한계는 남는다. 이 한계를 외부 차단이라고 표현하지 않는다.

`structural-limit-check`는 세 목록을 함께 약화한 격리 복사본이 실제로 살아남는지 매번 실행하고 `DETECT_ONLY`로 기록한다. 살아남음은 보호 장치의 합격이 아니라 외부 강제가 없는 현재 신뢰 경계의 재현 증거다.

## 파생 결과와 merge 권한

집계 상태, 대상 SHA, workflow identity, required check, 미충족 항목, mutation 생존 수는 실행 결과로 생성한다. 사람이 쓰는 판단 설명과 생성 JSON을 분리한다. 생성 파일을 손으로 고쳐도 다음 실행이 덮어쓴다.

merge 가능 여부는 외부 정책의 별도 입력과 출력이다. LLM, 구현 스크립트, 일반 테스트, 이 저장소의 로컬 JSON은 merge 권한을 갖지 않는다. 현재 GitHub 외부 강제가 확인되지 않았으므로 이 구현을 “merge 차단”이라고 부르지 않는다.

## 이번 변경의 자기모순 처리

이 최초 구현은 앞으로 보호할 workflow, manifest, checker, fixture와 runner를 직접 추가·수정한다. 그러므로 로컬 검사가 전부 성공해도 상태는 `POLICY_REVIEW_REQUIRED`다. 새 commit SHA가 원격에 없고 신뢰된 GitHub Actions 결과도 없으면 공식 원격 검증은 `BLOCKED`다.
