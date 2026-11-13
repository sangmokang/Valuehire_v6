# 기존 관리자 앱 통합

이 디렉터리는 기존 Next.js 관리자 앱에 추가하는 소스와 설치기다. 기존 화면·레이아웃·로그인과
`requireInternalOpsAccess`, `getRequestUser`, `getServerPageUser`를 재사용한다.
별도 shadow 서버가 제품 진입점이 아니다. 기존 Draft PR #140에서 함께 검토한다.

```sh
python3 apps/admin-integration/install.py "$ADMIN_CHECKOUT"
```

`ADMIN_CHECKOUT`은 기존 관리자 저장소의 **격리된 작업트리**로 지정한다. 설치기는 메뉴와 탐색
manifest의 예상 문맥을 먼저 확인하고 페이지·API·테스트·추가 마이그레이션을 복사한다.
메뉴와 기존 페이지는 유지된다. 이 명령은 DB migration 실행·머지·배포를 하지 않는다.
반복 설치 시 동일 모듈 파일을 갱신하므로 대상의 별도 수정은 먼저 검토한다.

기존 관리자 서버의 환경변수 `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`를 사용한다.
로컬 실증에 한해 `AI_SEARCH_REST_BASE_URL`로 loopback 읽기 RPC 어댑터를 지정할 수 있다.
어떤 환경에서도 관리자 세션 검사를 생략하지 않는다. Gmail 인증은 수집 작업 서버에만 둔다.

관리자 저장소에서 다음을 실행한다.

```sh
node_modules/.bin/vitest run tests/aiSearchWeekly.test.ts tests/adminMenuIa.test.ts tests/adminNavigationRouteManifest.test.ts
node_modules/.bin/tsc --noEmit
```

화면은 `/admin/ai-search-weekly`, API는 `/api/admin/ai-search/`의 weeks, weekly/{week},
candidates/{id}, batches/{id}, high-score-uncontacted, review-queue, collection-status다.
모든 API는 GET이며 서버 측 pagination/filter/sort와 private/no-store 정책을 적용한다.

수집·정규화·DB 적재는 `tools/admin-ai-search/`의 서버 작업으로 실행한다.
정본은 [현재 관리자 계약](../../docs/sot/admin-ai-search-evidence.md), 실행과 제한은
[통합 명세](../../docs/engineering/admin-ai-search-native-spec-2026-10-30.md)와
[검증 보고](../../docs/engineering/admin-ai-search-native-validation-2026-10-30.md)에 기록한다.
