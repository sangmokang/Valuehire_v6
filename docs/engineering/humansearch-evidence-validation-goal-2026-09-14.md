# HS-02.02 증거 manifest 형식검증 목표

## 범위

HS-02.01의 `docs/sot/humansearch-evidence-contract.md`가 정한 증거 한 건의 필드 이름과 상태/값 조합을 런타임 입력에서 검증한다.
이 WU는 형식과 조건부 필드만 다룬다. `coverage_status=complete`가 실제 구간으로 전체 문서 높이를 덮는지 계산하는 알고리즘은 HS-02.03 소유다.

## 소유 파일

- `humansearch/src/humansearch/evidence_validation.py`
- `humansearch/tests/test_hs_0202.py`
- `docs/engineering/humansearch-evidence-validation-goal-2026-09-14.md`

## 구현 계약

- 단일 공개 함수 `validate_evidence_manifest`가 입력 object와 schema version 인자를 받아 frozen typed result를 돌려준다.
- manifest payload에는 SOT에 없는 새 top-level schema key를 만들지 않는다. 지원 schema version은 함수 인자로만 닫는다.
- 입력 오류는 닫힌 result로 반환하고 예외를 외부로 흘리지 않는다.
- 오류에는 path, code, message만 담고 원본 개인정보 값을 복사하지 않는다.
- 파일, 브라우저, 저장소 I/O를 하지 않는다.
- 새 dependency, 범용 문서 검사기, coverage complete 계산 알고리즘을 만들지 않는다.

## RED 기준

테스트가 먼저 다음 반례를 고정한다.

- 정상 SOT-shaped manifest
- 필수값 누락
- 음수 integer
- bool-as-number
- unsupported schema version
- `candidate_ref` state/value 모순
- `document_height_px` state/value/note 모순
- `company_duties` state/array 모순
- 잘못된 segment 좌표, hash, failed reason
- 추출 필드와 연락처 field wrapper shape 오류
- 회사 duty와 alias shape 오류
- readback 조건부 필드 오류

## 검증 명령

```bash
cd humansearch && uv run pytest tests/test_hs_0202.py
```

→ targeted HS-02.02 테스트만 실행한다.

```bash
cd humansearch && uv run pytest
```

→ 기존 humansearch 회귀를 함께 본다.

```bash
cd humansearch && uv run ruff check src tests
```

→ Python lint를 본다.

```bash
cd humansearch && uv run mypy src tests
```

→ strict typecheck를 본다.
