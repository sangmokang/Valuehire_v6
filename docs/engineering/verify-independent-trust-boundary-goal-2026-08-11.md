# goal (설계 중, 장기 보류) — verify 독립 신뢰경계 (前 Phase 5: AC-D1~D4)

**분리 사유**: `verify-unification-goal-2026-08-10.md`(이하 "본 goal")의 Phase 5(AC-D1~D4, 로컬 Discord 봇 서명)가 두 라운드 연속(V1 codex) "재작성 필요" 판정을 받았고, 반면 Phase 1~4는 대부분 닫혔다. `/strict` R5에 따라 이 부분만 별도 문서로 분리했다.

**2026-08-11 격상 정정 — 장기 보류로 전환**: 이 문서가 의존하던 "GitHub 브랜치 보호 + `app_id` 고정"이라는 전제 자체가, 외부 적대검증 실측(`gh api .../branches/main/protection` → 403 "Upgrade to GitHub Pro or make this repository public") 결과 **이 저장소 요금제에서 아예 동작하지 않는다.** 본 goal(v5)은 required-check 계열 전체를 삭제하고 "로컬 품질검사 도구"로 목표를 축소했다. 이 문서가 다루는 독립 신뢰경계는 그 축소된 목표보다 훨씬 무거운 장치라 **착수 시점을 미정으로 둔다** — GitHub Pro 전환, 팀원 합류, 또는 진짜 강제장치가 사업상 필요해지는 시점 중 하나가 오면 재검토.

**착수 조건(재정의)**: 위 트리거 중 하나가 발생하면, 본 goal의 Phase 1~3(AC-M·AC-3·AC-16·AC-19·AC-1·AC-20·AC-5·AC-11·AC-9·AC-17·AC-12, 총 11개)이 배송된 뒤 착수. 지금은 지금까지 발견된 사실을 잃지 않기 위한 기록용.

---

## 지금까지 확인된 사실 (2026-08-10~11, codex V1 2라운드 + Claude V2 검증)

### 실패한 접근 (다시 시도하지 말 것)

1. **GitHub 브랜치 보호만으로 판정 권한 분리** — 필수 상태검사는 `skipped`/`neutral`도 통과로 침. [GitHub 공식문서]
2. **GitHub Secret에 서명키 저장** — 그 저장소의 모든 워크플로가 접근 가능. [GitHub 공식문서]
3. **GitHub Environment 필수승인자** — private repo에서 Enterprise Cloud 필요. `sangmokang`은 개인 계정이라 Enterprise Cloud 자체가 구매 불가능한 상품. **구조적으로 이 저장소에서 불가능.**
4. **저장소 Settings → Actions → Workflow permissions를 read-only로 고정** — 이건 **default일 뿐**, 워크플로 파일의 `permissions:` 키가 덮어씀. 포크 아닌 동일 저장소 PR(이 저장소의 모든 task 브랜치가 이 경우)은 강등 대상도 아님. [GitHub 공식문서, 2026-08-10 재확인]
5. **로컬 봇이 결과를 "전달받아" 승인·서명** — 봇이 독립적으로 재계산 안 하면, PR이 조작한 거짓 PASS를 승인자가 요약만 보고 승인해도 그대로 서명됨(P17 취지 미충족).

### 실제로 되는 것으로 확인된 것 (다음 설계의 출발점)

1. **GitHub 브랜치 보호는 required check의 예상 source를 특정 GitHub App으로 고정할 수 있다** (`checks[].app_id`, REST API 확인). 다른 identity가 같은 이름으로 게시해도 무시됨. **단, PAT/개인 계정 credential이 아니라 정식 GitHub App이어야 한다.**
2. Discord는 이 생태계에 이미 알림 어댑터로 존재(`registration_adapters: ["clickup","discord"]`, `humansearch-v6-founding-spec-2026-08-07.md:512`). 단 그 정본은 Discord가 "선택적"이며 꺼져도 파이프라인이 완결돼야 한다고 규정 — 승인의 유일한 경로로 쓰려면 이 전제와 재조정 필요.
3. 과거 Discord 웹훅 URL이 대화기록에 평문 노출돼 15개 파일에 영구 보존된 사고 이력(`evidence-2026-08-06/llm-failure-cases.md:32`) — 이번 설계는 자격증명을 macOS Keychain 등에만 저장하고 절대 대화·코드에 리터럴로 넣지 않아야 함.

### 다음 설계가 반드시 포함해야 할 것 (codex V1 2라운드 최종 권고 그대로 보존)

1. Credential 생명주기(Keychain 프로비저닝·회전·폐기·재부팅 후 자동기동)를 **가장 먼저** 설계 — 서명·승인보다 선행.
2. 로컬 프로세스의 GitHub credential을 **전용 GitHub App**으로 명시하고, required check를 정확한 `app_id`에 고정.
3. repo workflow permission read-only 설정은 "방어심도"로만 취급하고 신뢰경계로 세지 않는다.
4. 승인자(봇)는 PR이 보낸 결과를 그대로 서명하지 말고, **base/head SHA와 trusted verifier/corpus digest를 갖고 직접 재검증**해야 한다.
5. manifest에 base/head, check별 상태·증거 hash, 실행 명령, environment digest, nonce 발급자·만료·재사용 방지를 전부 포함.
6. Discord 승인에 허용 사용자 allowlist, guild/channel/message binding, run/head SHA binding, timeout·거부 규칙을 명시.
7. P6(`doctor/install/reconcile/status/uninstall`) 전체를 갖춘 실행 환경 스크립트 — `uninstall.sh` 하나로는 불충분하다고 이미 확인됨.
8. 봇이 오류/timeout일 때 `neutral`/`skipped`가 아니라 명시적 `failure`를 게시해야 함(그렇지 않으면 required check가 통과로 침).

### 미해결로 남을 수 있는 잔여 위험 (Phase 1~4만으로는 못 닫음, 참고용)

- **순차 2-PR 공격**: 검증기/코퍼스를 약화하는 PR을 먼저 병합하고, 다음 PR에서 그 약화를 악용하는 공격은 본 goal의 AC-6·7(동일 PR 감지)만으로는 못 막는다. 진짜 독립 판정자(이 문서의 주제)가 있어야 완전히 닫힌다.

---

## 다음 세션 시작 시 할 일

1. 이 문서를 goal 문서 정식 포맷(①현재상태~⑩계약스펙)으로 완성
2. GitHub App 등록 실습(무료, 개인 계정도 가능 — Environment/Enterprise와 다름 주의)부터 시작해 실제로 되는지 먼저 확인 후 설계
3. codex V1 1라운드로 다시 검증
