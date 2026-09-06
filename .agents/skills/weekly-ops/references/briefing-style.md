# CEO briefing style

This style governs the future Notion Golden projection. It does not alter the general Weekly v1
renderer or its existing Markdown contract. Write Golden output as an operating brief for a CEO,
not as an analyst transcript.

## Order

1. 결론 — only the material, evidenced changes.
2. 최근 고객 인입 — chronological facts, never an LLM priority list.
3. 마감 후 경보 — events after the closed metric window.
4. 컨설턴트별 몰입 — verified sent count, active days, largest position focus share, and inline
   `comparison_status`; unequal coverage forbids peer-ranking language in this section.
5. 채용 페이지 관측 — explicitly non-client staging signals.
6. 데이터 커버리지 — missing source, stale data, manual review, or failed publication.

## Voice

- Use short declarative Korean sentences.
- Name the company, position, observed decision, and timing.
- Put numbers next to the fact they measure.
- Distinguish fact, inference, and unavailable evidence.
- Prefer “확인되지 않았다” to invented certainty.
- Omit greetings, process narration, generic recommendations, and LLM self-reference.
- Do not issue management priorities or action directives.

## Banned filler

- “분석 결과 중요한 인사이트를 발견했습니다.”
- “종합적으로 볼 때.”
- “도움이 되었기를 바랍니다.”
- “AI가 판단하기에.”
- unsupported words such as “매우”, “획기적”, “압도적”.

## Example

```text
결론
신규 의뢰 3건이 확인됐다. Codeit 백엔드와 SpoonLabs AI Creative Director는 8월 31일에
공유됐다. FastView Product BD는 레퍼런스 체크 완료 상태이며 고객 결정일은 확인되지 않았다.
```
