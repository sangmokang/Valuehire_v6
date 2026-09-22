# JD Aside 운영 절차

2026-09-22 실제 저장·재조회에서 확인했습니다. 정본 계약은 [통합 SOT](jd-connected-registration.md)입니다. 선택자는 실행 시 화면을 다시 확인하며, 화면이 바뀌면 아래 값만 믿고 저장하지 않습니다.

## 공통

- `aside repl`에서 `openTab(url)`로 작업 전용 탭을 열고 반환된 탭 ID를 기록합니다. 사용자가 쓰는 탭은 닫거나 이동하지 않습니다.
- 실제 브라우저 조작은 메인 작업자 한 명이 맡습니다. 다른 에이전트는 원문 조사·코드·검증만 맡습니다.
- 같은 로그인 계정의 데이터는 탭 사이에 공유됩니다. 저장 직전 회사·직무·포지션 ID를 재확인합니다.
- 원문, 의미 단위, 채널 패킷, 저장 전 상태, 입력 직후 상태, 새로 연 저장본, 메일 보낸편지함 확인을 포지션별로 기록합니다.
- REPL 호출은 페이지 렌더링이 끝나기 전에 반환할 수 있습니다. 클릭 직후 빈 목록을 중복 없음의 증거로 사용하지 않습니다.
- 폼과 포지션 목록만 조회합니다. 후보자 이력서 본문을 운영 로그에 수집하지 않습니다.

## 사람인

진입: `https://www.saramin.co.kr/zf_user/memcom/talent-pool/main/candidate-manage`

1. `input[placeholder="포지션 및 생성자명을 검색해주세요"]`에 회사/직무를 넣고 `button.btn_search`를 클릭합니다. 렌더링 후 `input[id^=position_chk]`의 상위 `li`에서 제목과 ID를 확인합니다.
2. 기존 포지션 수정: 해당 `li`의 `.btn_position_option`을 열고 텍스트가 `포지션 수정`인 버튼을 누릅니다. 신규: `button.btn_add_position`.
3. `#position_title`에 hiringTitle, `#position_content`에 offerComment, `#work_content`에 chargeWork를 넣습니다.
4. 직무 `#job_select`, 경력 `#offer_career_min`/`max`는 원문에 근거해 선택합니다. 연봉 상·하한을 임의로 채우지 않습니다.
5. 상세 직무 입력을 클릭해 현재 노출된 label을 확인하고 선택합니다. `.btn_autocomplete_close`가 여러 개면 보이는 요소를 사용합니다. `.selected_job_keyword`에 선택값이 남았는지 확인합니다.
6. `button.btn_save` 저장 후 목록 URL을 새로 열고 검색합니다. 저장된 ID의 수정창을 다시 열어 세 필드와 선택값을 읽습니다.
7. `readback_kind=persisted_reopen`, `fresh_saved_position=true`는 실제 새 조회를 한 경우에만 기록합니다.

관측 분류 예시: QA는 IT개발·데이터/QA·테스터, Global Team Lead는 기획·전략/사업기획·사업개발. 회사 이름이나 과거 포지션에 따라 기본값을 재사용하지 않습니다.

## 잡코리아

로그인한 인재검색 화면의 `button.dev-positionoffer`에서 포지션 제안 화면을 엽니다. 중간 안내의 `a.dev-open-position-offer`는 제안 화면 열기이며 실제 발송과 구분합니다.

1. 목록이 접힌 상태라면 `input#posgtitle`(placeholder `등록 포지션 명 검색`)에 검색어를 넣고 `button.devposgsearch`를 클릭해 목록을 엽니다. 입력만으로 목록이 열리지 않을 수 있습니다. `input.dev_lb_postion_info`의 value(포지션 ID), `data-title`, `data-pstn-group-no`를 비교해 중복을 확인합니다.
2. 기존 항목의 상위 `li` 내 `.devPositionEdit`로 수정합니다. 신규는 `button.positionadd`입니다.
3. `#GI_PSTN`, `#EXEC_WORK`, `#ST`에 패킷 값을 입력합니다. 기존 제목이 disabled이면 속성을 해제하지 않습니다. 기존 제목과 동일 포지션임을 확인해 명시적으로 바인딩합니다.
4. 고용형태와 `button.devListContainer` 직무 선택은 현재 화면의 label을 확인해 결정합니다. 직무 선택의 `button.devSubmitBtn`은 선택 확인 버튼입니다. 이것을 후보자 발송 버튼과 혼동하지 않습니다.
5. `#btnSave`는 포지션 등록/수정입니다. 저장 후 화면을 새로 열어 동일 그룹의 현재 ID를 찾습니다. 수정 시 ID가 바뀔 수 있으므로 이전 ID만 찾지 않습니다.
6. 제안 내용 UI는 `#posg_cntnt`이며 패킷 이름은 `proposalMessage`입니다. `maxlength=3000`을 확인하고 정확히 넣습니다.
7. `#lb_save` 체크만으로 제안 내용이 영구 저장된다고 가정하지 않습니다. 실제 관측에서는 다시 열면 기본 문구로 복원됐습니다. 저장된 포지션과 제안 문안 결과를 나눠 보고합니다.
8. 후보자 발송은 별도 명시 요청이 있을 때만 합니다. 등록·보고 메일 요청만으로 제안 보내기 버튼을 누르지 않습니다. 다음 승인된 발송에서는 해당 포지션 패킷의 제안 내용을 다시 넣고, 선택 포지션 ID와 본문을 검증합니다.

## 보고 메일

보고 메일은 현재 작업이 명시적으로 발송을 승인한 경우에만 포지션마다 한 통을 보냅니다. Gmail 후보자 JD는 별도의 독립 전문이며 운영 보고 메일로 대체하지 않습니다. JobKorea 제안 내용은 영구 저장을 확인하지 못했다면 `NOT_SAVED` 또는 준비된 문안으로 표시합니다.

Gmail 전송 응답 ID만으로 완료하지 않습니다. 해당 ID를 `format=full`로 읽어 SENT 라벨, 수신자, 제목, 본문 전체가 예상과 같은지 비교하고 메일 ID와 비교 결과를 증거로 저장합니다.

## 이번 정정의 추가 확인 계약

- 사람인 편집에는 포지션명 `#position_title`(35), 제안 내용 `#position_content`(2000), 업무 내용 `#work_content`(2000)가 관찰됐다. 본문은 두 개다. 편집 관찰만으로 후보자 표시 순서를 확정하지 않고 상세/미리보기도 따로 캡처한다.
- 원문 source-unit와 fresh readback을 문장별 대조한다. 제외 문구는 등록 필드뿐 아니라 메일 본문 전체에서 검사하고 raw 원문 부록을 만들지 않는다.
- 잡코리아의 제안 화면 진입은 현재 검색 화면→이력서 화면의 `button.dev-positionoffer`→`a.dev-open-position-offer` 확인으로 관찰됐다. 이력서 본문을 수집하지 않고 편집 폼만 읽는다. 발송 버튼은 누르지 않는다.
- Aside 일회성 REPL 사이에는 변수가 유지되지 않는다. 작업용 대화형 `aside repl`을 유지하고, 파일은 그 세션 폴더에 저장한 뒤 작업 워크트리의 ignored artifacts로 복사한다.
- 사용자가 기존 브라우저에서 로그인한 뒤 작업 탭을 다시 조회하면 인증이 반영되는지 확인한다. 로그인 수행 권한은 최신 사용자 지시를 따른다. 비밀번호/세션을 로그에 기록하지 않는다.
