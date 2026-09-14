# HumanSearch evidence coverage goal — 2026-09-14

## 결론

HS-02.03은 이미 형식 검증을 통과할 수 있는 증거 manifest를 받아 전체 열람, 부분 열람, 실패를 결정론적으로
판정한다. 브라우저, 저장소, 네트워크, CLI, 새 의존성은 만들지 않는다.

## 범위

- 입력: HS-02.02 `validate_evidence_manifest`가 검증하는 manifest 객체.
- 출력: `coverage_status`, `coverage_reason`, `last_observed_y_px`를 담은 불변 결과.
- 오류: manifest 자체가 유효하지 않으면 원문 값을 노출하지 않고 `failed`와 `invalid_manifest`를 반환한다.
- 경계: `segment_status=observed` 구간만 전체 열람 덮개로 계산한다. `failed`와 `redacted`는 덮개가 아니다.
- 부작용: 입력 객체를 변경하지 않고 파일, 브라우저, 저장소, 네트워크를 사용하지 않는다.

## 판정 계약

- `height_state=observed_stable`이고 관측 구간이 `0..document_height_px`를 빈틈 없이 덮으면 `complete`다.
- 중간 구멍은 `partial`과 `segment_gap`이다.
- 마지막 관측 구간 끝이 문서 높이보다 작으면 `partial`과 `trailing_gap`이다.
- 관측 구간이 하나도 없으면 `partial`과 `no_observed_segments`다.
- 안정 높이가 0이면 전체 문서 경계를 신뢰하지 않고 `partial`과 `zero_document_height`다.
- 문서 높이가 바뀌었으면 `partial`과 `height_observed_changed`다.
- 문서 높이를 관측하지 못했으면 `partial`과 `height_not_observed`다.
- 문서 높이가 적용 불가이면 전체 문서 경계를 증명할 수 없으므로 `partial`과 `height_not_applicable`이다.

## Counter-AC

- complete 기본 승격 금지: 상태 필드가 complete여도 좌표가 덮지 못하면 partial이어야 한다.
- 실패·redacted 구간 덮개 금지: 관측되지 않은 구간은 전체 열람 증거로 쓰지 않는다.
- 순서 의존 금지: 구간 배열 순서가 뒤섞여도 좌표 덮개만으로 판단한다.
- 겹침 내성: 겹치는 관측 구간은 합쳐 계산하되 구멍을 메우지 못하면 partial이다.
- 높이 변경 금지: 스크롤 중 높이 변경은 complete가 될 수 없다.
- 원문 노출 금지: 유효성 오류 결과에 URL, 후보명, 연락처 같은 원문 값을 넣지 않는다.

## 검증

RED 테스트는 import 실패가 아니라 실제 판정 실패로 둔다. 최소 구현 뒤 targeted pytest, 전체 pytest, ruff,
mypy, diff check, 격리 결함 주입, 외부 Sonnet V1, root 독립 V2를 실행한다. 이 WU는 실제 운영 화면이나 OS 격리
증거를 제공하지 않는다.
