/strict

[VALUEHIRE-V6-WU3-7 — 같은 Jev 판정으로 점수 공식만 바꿔 72쌍 역전율 비교] L1(분석). WU1 코드·계약·DB 스키마·Git 변경 없음. Jev 재호출 없음.

## 0. 시작 상태 (확인만, 다시 검증하지 않는다)

- WU3-6(2026-10-11) 결과: ~/valuehire-private/wu3/WU3-6-result-2026-10-11.txt
  - Jev 실제 판정 1,492/1,494(jev-1.13.0, TypeSafe 직접). 결과 wu35/jev_results.jsonl.
  - 역전율 PROXY 37.5% = Jev 37.5%(72쌍, Jev 38/7/27). 시점 민감도 35.5~38.0%.
  - 점수 중앙값 HIRED 0.78 / INTERVIEWED 0.61 / CLIENT_DECLINED 0.67 → 거절군이 더 높다.
  - 결론: 판정자가 아니라 점수 공식이 결과를 못 가른다.
- WU3-2: 거절 사유 SKILL_DEPTH 8·LEVEL 5·DOMAIN 4 등 "깊이·수준" 사유가 많았다.
- 현행 공식(recount_wu35.py scores): 가중치 required 2 / preferred 1 / duty 1, SUPPORTED 1·PARTIAL 0.5·NOT_STATED 0·CONTRADICTED 0, 충돌·실패는 분자·분모 제외, 점수 = 충족합 / 가중치합.
- 실행 파이썬: worktrees/jev-ea-wu1-split/humansearch/.venv/bin/python

## 1. 질문 하나

같은 Jev 판정 1,492건으로 점수 공식만 바꾸면 72쌍 역전율이 37.5%에서 의미 있게 내려가는가?

## 2. 후보 공식 (미리 고정, 추가·수정 금지)

| ID | 공식 |
|----|------|
| F0 | 현행 (기준선, 37.5% 재현 필수 — 다르면 멈추고 보고) |
| F1 | required 요건만으로 점수 (preferred·duty 제외) |
| F2 | PARTIAL = 0 (SUPPORTED 만 인정) |
| F3 | required 중 NOT_STATED·CONTRADICTED 개수가 적을수록 높음 (점수 = −미충족 required 수, 동률은 F0로) |
| F4 | F0 × confidence (각 요건 기여도에 Jev confidence 곱) |

## 3. 절차

1. ~/valuehire-private/wu3/wu37/score_variants.py 하나만 새로 만든다. recount_wu35.py 의 입력·쌍 규칙·라벨(wu34/labels_after.json)·시점 민감도 5종을 import 해서 그대로 쓰고, 공식 함수만 바꿔 끼운다. recount_wu35.py 는 수정하지 않는다.
2. F0~F4 각각: 주 결과(higher/tie/lower/역전율), 시점 민감도 5종, 결과군별 중앙값.
3. 우연 방지 점검 1개: group_key 를 sha256 순으로 정렬해 홀/짝 두 묶음으로 나누고, 각 묶음에서 역전율을 따로 낸다.

## 4. 해석 기준 (미리 고정, 사후 변경 금지)

- 어떤 공식이 F0 보다 10%p 이상 낮고, 홀/짝 두 묶음 모두에서 F0 보다 낮고, 시점 민감도 5종 모두에서 F0 보다 낮음 → 그 공식을 다음 단계 후보로 채택. 다음: 563건 풀로 표본 확대해 같은 비교.
- 해당 공식 없음 → "요건 충족 여부" 계열 공식으로는 못 가른다. 다음: 요건별 판정에 깊이·수준(그 요건을 주 업무로 한 기간·역할 수준) 한 칸을 추가하는 설계 1장(구현 아님).
- 두 공식 이상이 통과하면 역전율이 가장 낮은 것 하나만 채택하고, 나머지는 숫자만 적는다.
- 72쌍 소표본이다. 통과해도 "가설 지지"로만 쓰고 "확정"이라 쓰지 않는다.

## 5. 하지 말 것

Jev 재호출·다른 모델 호출, WU1 코드/계약 수정, 가중치 미세조정(F0~F4 외 공식 금지), 라벨 재보정, 새 DB·스키마,
Supabase/ClickUp, V1/V2/뮤테이션·Codex 재검증, 기준 사후 변경, push/PR,
개인정보(이름·이력서 문장)를 ~/valuehire-private 밖으로 내는 것.

## 6. 최종 보고 (짧게)

1. F0 재현 여부(37.5%)
2. F0~F4 역전율 표(주 결과 + 홀/짝 + 시점 민감도 최소~최대)
3. 결론 하나(채택 공식 / 해당 없음)와 다음 작업 하나
결과 파일: ~/valuehire-private/wu3/WU3-7-result-<날짜>.txt
