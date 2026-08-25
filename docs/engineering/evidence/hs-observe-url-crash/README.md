# 증거 재현 도구 — hs-observe-url-crash

이 폴더는 **게이트가 아니다.** CI 도 pre-push 도 이것을 실행하지 않는다. `docs/engineering/
hs-observe-url-crash-goal-2026-08-25.md` 와 `docs/engineering/verdicts/
hs-observe-url-crash.verdict.json` 이 인용한 숫자를 남이 다시 만들어 볼 수 있게 하는 것이
유일한 목적이다.

Codex 적대 검증이 지적했다: *"1,512 fuzz 와 24 mutation 은 seed·입력목록·runner 가 없어
재현 불가"*. 맞는 지적이라 도구를 저장소 안으로 옮겼다.

## 실행

```bash
cd humansearch
PYTHONPATH=src uv run --no-sync python ../docs/engineering/evidence/hs-observe-url-crash/fuzz_main.py
python3 ../docs/engineering/evidence/hs-observe-url-crash/mutation_sweep.py
```

| 스크립트 | 무엇을 재현하나 | 기대 출력 |
|---|---|---|
| `fuzz_main.py` | 적대적 타깃 목록을 `main()` 에 먹이는 퍼징 | `crash=0 bad_exit=0 multiline=0` |
| `mutation_sweep.py` | `except` 튜플 원소를 하나씩 빼는 전수 변조 | 생존 1건(`_cdp` 의 `TimeoutError`) |

→ 두 스크립트 모두 seed 와 입력 목록이 소스에 박혀 있다. 같은 커밋에서 같은 숫자가 나온다.
