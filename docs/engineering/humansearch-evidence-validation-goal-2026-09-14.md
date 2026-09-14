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


## V2 독립감사 반례 회수

`e087322`의 RED는 구현 모듈 부재를 확인한 collection error였고, SOT 계약 자체의 실패 증거는 아니었다. V2 독립감사는 구현 후보 `15d4e75`에서 다음 실제 계약 구멍을 찾았다.

- `segments`가 문자열 또는 null이어도 invalid array로 닫히지 않았다.
- `extracted_fields`와 `observed_contact_fields`가 null이어도 required object 오류가 나지 않았다.
- `company_aliases`가 null이어도 required array 오류가 나지 않았다.
- `readback_status=not_run`일 때 존재하는 `readback_at`의 잘못된 timestamp와 빈 `readback_failure_reason`을 검사하지 않았다.
- 알 수 없는 top-level key와 extracted field key가 오류 path에 원문으로 노출될 수 있었다. 이 key는 개인정보 형태일 수 있으므로 path는 schema 위치와 index로 sanitize해야 한다.

V2 수정은 위 반례 assertion을 먼저 RED로 남긴 뒤, 같은 3개 소유 파일 안에서 필수 array/object 검증과 sanitized path를 구현한다.

## V2 null-only segment mutant 확인

`segments` 문자열 반례와 다른 required object null 반례만으로는 `segments=None`만 허용하는 변이를 격리해 죽였다고 말할 수 없었다. 따라서 `test_rejects_segments_none_as_required_array`를 추가해 `segments=None` 단독 반례를 고정했다.

임시 변이:

```python
def _validate_segments(segments: object, errors: _Collector) -> None:
    if segments is None:
        return
    ...
```

결과:

```text
tests/test_hs_0202.py::test_rejects_segments_none_as_required_array FAILED
assert True is False
```

→ 이 결과는 `segments=None`만 허용하는 mutant가 새 테스트에 의해 죽는다는 뜻이다. 변이 파일은 즉시 원복했고, 원복 후 같은 단일 테스트는 PASS했다.
