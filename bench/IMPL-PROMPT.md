# 구현 과제 — aisearch 코어 모듈 5개

아래 스펙 문서 5개만 읽고 파이썬 모듈을 구현하라.

## 읽을 것 (이것만)

```
<SPEC_DIR>/SPEC-boolean_builder.md
<SPEC_DIR>/SPEC-intervention.md
<SPEC_DIR>/SPEC-pagination_store.md
<SPEC_DIR>/SPEC-portal_search.md
<SPEC_DIR>/SPEC-recorders.md
```

## 금지 (위반 시 이 작업은 무효)

- `/Users/kangsangmo/Desktop/Valuehire_v5` 아래 **어떤 파일도 열지 마라.** 원본 구현과 테스트가 거기 있다. 열면 이식이 아니라 복사가 되어 측정이 무의미해진다.
- 다른 저장소에서 같은 이름의 모듈을 찾아 참고하지 마라.
- 채점용 테스트를 찾으려 하지 마라.

스펙에 없어 판단이 필요한 부분은 **스펙의 설계 의도에 맞게 스스로 결정하라.** 질문하지 말고 진행하라.

## 산출물

`<OUT_DIR>/` 아래에 다음 6개 파일:

```
apps/aisearch/core/boolean_builder.py
apps/aisearch/core/intervention.py
apps/aisearch/core/pagination_store.py
apps/aisearch/core/portal_search.py
apps/aisearch/core/recorders.py
apps/aisearch/core/data/seoul_universities.py
```

패키지 초기화 파일(`__init__.py`)은 만들지 않아도 된다 — 채점 환경이 제공한다.

## 구현 요건

1. **스펙에 적힌 공개 이름을 정확히 그대로 쓴다.** 함수·클래스·상수·인자 이름이 하나라도 다르면 불러올 수 없다.
2. `boolean_builder` 는 `from apps.aisearch.core.data.seoul_universities import SEOUL_UNIVERSITIES` 로 대학 목록을 가져온다. 그 데이터 모듈도 스펙에 실린 값 그대로 만들어라.
3. **표준 라이브러리만 사용한다.** 외부 패키지를 설치하거나 import하지 마라.
4. 스펙에 명시된 **검증 순서**를 지켜라. 어느 오류가 먼저 나는지가 계약이다.
5. 스펙의 **경계값 포함/배제**를 정확히 지켜라 (예: 범위의 양 끝값이 허용인지 거부인지).
6. 스펙의 **불변식**을 지켜라 (예: 방어적 복사로 무엇이 보호되어야 하는지).
7. 파이썬 3.12에서 동작해야 한다.

## 자기 점검 (제출 전)

- 6개 파일이 모두 있는가
- 각 파일이 문법 오류 없이 import 되는가 (`python3 -c "import ast,pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('<OUT_DIR>').rglob('*.py')]"`)
- 스펙의 공개 이름 중 빠진 것이 없는가
- 외부 패키지를 쓰지 않았는가

## 보고

작업이 끝나면 파일별 줄 수와, 스펙에서 판단이 갈려 스스로 결정한 부분이 있으면 그 목록을 보고하라.
