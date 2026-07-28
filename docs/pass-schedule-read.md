# 정기권 일정 후보 읽기

`KorailClient.get_pass_schedule()` 은
`POST /classes/com.korail.mobile.pass.passScheduleInfoList` 의 읽기 전용 계약을
드러낸다. 요청은 닫힌 frozen `PassScheduleRequest` 이고, 열차·구간·날짜·페이지·
정기권 값은 전부 호출자가 준다. 런타임 정기권 코드나 메뉴 코드를 하드코딩한 것은
하나도 없다.

## 요청

정확한 폼은 필드 15개다 — `Device`, `Version`, `Key`, `selGoTrain`,
`selGoAbrdDt`, `txtGoHour`, `radChgTrnDvCd`, `txtCmtrKndCd`, `txtCmtrUtlTrmCd`,
`txtCmtrUtlAgeCd`, `txtSelPage`, `txtCntPerPage`, `txtGoStart`, `txtGoEnd`,
`txtWkndUseFlg`. 클라이언트는 POST 를 한 번 보내고 이 라우트에서는 DynaPath 를
끈다.

## 응답

`strResult` 가 정확히 `SUCC` 인 봉투를 받아들이고, **빈 결과 모양 하나를 더**
받아들인다. `strResult=FAIL` 과 `h_msg_cd=WRG000000` 이 함께 오면 예외를 올리는
대신 빈 `PassScheduleResponse` 를 돌려준다. 앱이 그렇게 한다 —
`CommutationInquiryActivity.java:182` 가 이 DAO 에 대해 `WRG000000` 을
`setErrorMsgCdNotShowDialog` 로 등록하므로, 결과가 없는 조회는 오류가 아니라
"일정 없음" 으로 그려진다. 여기서 그것을 실패로 다루면 "가진 정기권이 없다" 가
예외가 된다. 그 밖의 `SUCC` 아닌 봉투는 여전히 예외를 올린다.

응답 타입은 정적 근거가 있는 `schedule_info[].train_list` 필드만 투영한다 —
`h_arv_rs_stn_cd`, `h_arv_rs_stn_nm`, `h_dpt_rs_stn_cd`, `h_dpt_rs_stn_nm`,
`h_dtour`, `h_schd_prc`, `h_trn_gp_cd`, `h_trn_no`. 컬렉션은 불변이고 요청·응답
값은 `repr` 출력에서 가려진다.

## 경계

**서버가 세션을 요구하는지는 확인되지 않았다.** 이 라우트는 계정 무관이
아니지만, 그렇게 만든 것은 서버가 아니라 이 패키지다 — 인증된 세션을 요구하는
보수적인 클라이언트 쪽 안전 게이트를 걸어 두었다. 실서버 검증은 로그인 이후에만
하고, 그 클라이언트 정책을 서버 자신의 세션 규칙에 대한 근거로 다시 읽지 마라.

이 표면은 후보 조회에서 멈춘다. 이웃한 정기권 예약이나 결제 호출은 드러내지
않으며, 후보를 고르거나 예약하거나 잡거나 결제하는 일은 없다.

## 정적 근거

- `PassService.java:27-29` 가 POST 경로와 전송되는 필드 15개를 고정한다.
- `CommRsvInquiryDao.java:207-208` 이 정확한 실행 순서를 확인해 준다. 이 DAO 의
  메모리상 요청 타입은 `txtCmtrUtlTrmNm` 도 들고 있지만 그 필드는 Retrofit
  메서드로 넘어가지 않으므로 여기에도 일부러 없다.
- `CommRsvInquiryDao.java:137-200` 이 중첩된 응답 래퍼와 투영하는 열차 필드
  여덟 개를 고정한다.
- `CommutationInquiryActivity.java:178-186` 이 이 읽기가 별개의 후보 선택 예약
  흐름보다 앞에 온다는 것을 보여 준다. 패키지는 읽기만 구현한다.
