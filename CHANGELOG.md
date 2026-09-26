# 변경 이력

## [2.0.0] - 2026-09-26

v1.1.1 이후의 변경입니다. 코레일+ 안드로이드 앱 7.0.6 기준이며, GitHub 릴리스로 공개하고 PyPI 에는 올리지 않습니다.
v1.0.0~v1.1.1 의 기록은
[v1.1.1 태그의 CHANGELOG](https://github.com/yakisoba0728/korail-mobile-api/blob/v1.1.1/CHANGELOG.md)에 있습니다.

### 달라진 요청과 동작

- 요청 필드를 앱 DTO 의 선언 순서로 보냅니다(`NetworkService.java:15335–15392`). 로그인, 예약 5종, 환불·수수료 조회
  (공통 필드를 맨 뒤), 호차 조회, 승차권 목록, 병합 조회가 해당하고, 요금 재계산은 Retrofit 목록 순서입니다. `lang` 은 `Key` 뒤에 옵니다.
- API 요청은 `User-Agent: korailtalk` 과 앱 OkHttp 기본 헤더(`Connection: Keep-Alive`, `Accept-Encoding: gzip`)를 보내고
  `Accept` 는 보내지 않습니다.
- 대기열 요청은 빈 본문 POST 에 안드로이드 기본 Dalvik User-Agent(`Build/…` 포함)를 싣고, 응답 코드와 TTL·대기 인원은
  Java `Integer.parseInt` 처럼 읽습니다. 허용 범위 밖 노드는 무시하고 정문으로 진행·반납합니다.
- DynaPath 토큰의 `rt` 에 요청 간 시간차(최근 5개)를 싣습니다. v1.1.1 은 `rt=0` 고정이었습니다.
- 운임 조회는 상품번호가 없어도 `gdNo` 칸을 보냅니다.
- 요청 전에 거절합니다: 카드 입력 형식, 0원·예약대기 홀드의 카드 결제, 수수료 조회 응답 없는 환불, 마일리지가 수수료보다 적은
  마일리지 정산, 탑승 순서가 아닌 환승 구간, 운행일이 다른 병합 행, 공항버스 좌석 중복.
- 좌석·호차·역의 선택 필드 18개가 빠지면 앱 기본값으로 읽습니다. 봉투와 String 필드의 JSON 정수는 문자열로 읽습니다.
  파싱에 실패하면 예외 `.raw` 에 전체 응답, `.parser_raw` 에 부분 원문이 남습니다.

### 수정

- `refund`는 `commission`이 `get_refund_commission`의 응답이 아니면(`None` 포함) 요청 전에 `KorailProtocolError`로 거절합니다.
  전에는 `commission=None`을 명시하면 수수료 값 없이 환불 요청을 보냈습니다.
- 로그인 폼에서 `txtInputFlg`를 회원번호 앞, `custId`를 `checkValidPw` 앞에 둡니다
  (`LoginIn.java:57–80,141–164`). 경로·필드·값·헤더는 유지합니다.
- 봉투와 `PriceRecalculationRequest.for_hold` 좌석의 과도하게 큰 JSON 정수도 원문을 보존한
  `KorailProtocolError`로 거절합니다. 재계산 실패에는 좌석 원문도 `parser_raw`로 남깁니다.
- `BaseKorailResponse.from_raw`는 봉투의 JSON 정수를 문자열로 읽고 잘못된 타입은 원문과 함께 거절합니다.
  성공·실패 판정은 하지 않습니다.
- 지연확인증의 선택 `runDt`는 다른 선택 문자열처럼 잘못된 타입이면 `None`입니다.
- 대기열 TTL·대기 인원은 부호·BMP 십진 숫자·긴 선행 0을 Java int32처럼 읽습니다.
  잘못된 값은 기존의 0 기본값을 유지하며 큰 정수 변환의 `ValueError`가 새어 나오지 않습니다.
- 공통 파싱·요청·재시도 정책은 [동작 계약](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/BEHAVIOR.md)에 모았습니다.

### 타입

- `KorailLoginInputFlag`와 `KorailRoomClassCode` 입력 타입 별칭을 공개합니다.
  로그인 종류·비밀번호 확인 여부·객실 종류를 타입으로 좁히며 런타임 검증은 추가하지 않습니다.
- 공개 응답 모델의 `raw`는 `Mapping[str, object]`입니다. 실제 원문 객체를 복사·동결하거나 마스킹하지 않습니다.
- `BaseKorailResponse.from_raw`와 `TrainSummary.from_raw`의 반환형은 `Self`입니다.
  서버 응답 코드 필드는 `str`/`str | None`을 유지합니다.

### 공개 API 추가

- 상품 예약 취소, 공항버스 예약, 역 발권 승차권 환불 검증·실행을 제공합니다:
  `cancel_product_reservation`, `reserve_limousine`, `verify_station_ticket_refund`, `execute_station_ticket_refund`.
- 지연확인증·지연료 반환 영수증, 셀프 체크인 정보·좌석 확인·등록·취소, 전달 승차권 회수를 제공합니다:
  `get_delay_certificate`, `get_delay_return_receipt`, `get_self_checkin_info`, `check_self_checkin_seat`,
  `register_self_checkin`, `cancel_self_checkin`, `retrieve_delivered_ticket`.
- `PriceRecalculationRequest.for_hold`는 첫 여정 좌석별 재계산 행을 만듭니다.
  `recalculate_price(add_to_cart=True)`는 재계산 성공 뒤 장바구니 추가를 요청하고 `cart_addition`에 결과를 남깁니다.
- `TrainSearchQuery`는 청소년·유아·안내견 인원도 받습니다. 조회 폼에서는 각각 어른·어린이·어른 인원에 합칩니다.
- `ReservationHoldResponse.payable`은 예약대기 결제를 막는 값입니다. 병합 첫 홀드는 결제할 수 있습니다.

### v1.1.1 과 호환되지 않는 변경

모델은 키워드 인자로 생성하십시오. 변경 메서드는 별도 사전 동의 없이 즉시 요청합니다.

- 제거 메서드: `get_gift_ticket_list`, `get_limousine_schedule_view`, `get_platform_numbers`, `pay_with_fake_card`.
- 제거 인자·이름: `consent=`, `MutationPreview`, `SELF_SEAT_CHANGE_ROOM_CLASS_CODES`, `inquiry_action`.
  제거 모듈: `consent`, `redaction`, `safety`.
  `live_enabled`, `read_credentials_from_env`, `run_live_smoke_from_env`도 제거했습니다.
- `get_crew_request_list`는 `query_division_code` 대신 키워드 `timestamp_ms`를 받습니다.
  `get_station_info`의 `device`, `refund`의 `return_times_division_code`는 제거했습니다.
- `refund`의 `commission`은 필수 키워드입니다. `reserve_merge`의 두 번째 인자 이름은 `merge_rows`입니다.
  `get_ticket_receipt`의 식별값은 키워드 전용이며 `get_ticket_list`의 `page_no` 기본값은 `1`입니다.
- `get_ticket_list`, `refund`, `add_to_cart`는 각각 전용 `BaseKorailResponse` 하위 모델을 반환합니다.
- `KorailConfig.enable_dynapath`·`live_env_var`는 제거했습니다. DynaPath를 끄려면 `disable_dynapath=True`를 씁니다.
  API의 `user_agent`와 대기열의 `netfunnel_user_agent`는 별도 설정입니다.
  `build_dalvik_user_agent`는 키워드 `build_id`가 필요합니다.
- 제거 모델 필드: `AppDataResponse.for_seat_intg`·`airport_bus_msg`, `DelayDiscountTicket.usable_until_date`,
  `DiscountCardScheduleTrain.station_string_info`, `DiscountCardSection.section_sequence`, `DiscountCoupon.discount_values`,
  `MileageHistoryResponse.rail_now_saved_point_1`, `PriceFareLeg.standing_train_classification_code`,
  `RefundTicketDetailResponse.mileage_save_flag`, `TrainSearchContinuation.page_count`,
  `TrainSearchMetadata.merge_reservation_available_flag`, `TripChangeDateResponse.trip_change_date`,
  `TripMenuContent.content_type`, `KorailAuthContinuationRequired.post_data`.
- `DiscountCoupon.discount_values` 대신 할인 구분·평일/주말 운임·요금 할인 속성을 사용합니다.
  `StationInfoResponse.count`, `SeatInventoryResponse.layout_type`, `CartItem.ticket_count`,
  `TicketDuplicationCheckResponse.reservation_count`, `KorailStation.popup_type`, `PassMenuItem.after_day`,
  `TrainScheduleStop.actual_arrival_delay_count`는 문자열입니다.
- `PbpAcceptanceJourney.member_card_no`, `PriceFareLeg.train_class_code`, `TicketReceipt.printed_discount_kind_code`·
  `ticket_kind_name`·`train_group_code`는 필수입니다. 선택 수량·좌석 비율은 `None`일 수 있습니다.
- 닫힌 클라이언트와 잘못된 도메인 입력은 `KorailProtocolError`로 거절합니다.
  `cancel_unpaid_hold`는 기본으로 확인과 취소를 순서대로 요청합니다.

### 검증 범위

오프라인 검사는 운영 서버의 수용을 보장하지 않습니다. 보호된 리터럴과 미관측 응답은 검증 못 함입니다.
셀프 체크인 변경·전달 승차권 회수·N카드의 실서버 검증 상태를 새로 확인하지 않습니다.
기록용 `_*_unsupported.py` 세 파일은 유지하며 보호된 값을 추측해 기능을 추가하지 않습니다.
버전 변경·태그 생성·배포는 하지 않습니다.
