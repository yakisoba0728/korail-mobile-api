# API 레퍼런스

`KorailClient`의 공개 메서드 84개를 주제별로 나눠 설명합니다. 모든 메서드는 동기식이며 네트워크 요청이 끝날 때까지 반환하지 않습니다.

## 클라이언트

::: korail_mobile_api.client.KorailClient
    options:
      members: false
      show_root_heading: true
      heading_level: 3

## 표기

각 메서드 설명 아래의 표는 다음을 뜻합니다.

| 항목 | 뜻 |
|---|---|
| 로그인 | 호출 전에 `login()`이 필요한지 여부입니다. 대부분의 메서드는 로그인하지 않았으면 요청을 보내지 않고 `KorailAuthError`를 발생시킵니다. 그렇지 않은 메서드는 설명에 따로 적었습니다. |
| 대기열 | 요청 전에 통과하는 NetFunnel 관문 이름입니다. 관문이 없으면 `-`입니다. 자세한 내용은 [설정](../guide/configuration.md)을 참고하세요. |
| 상태 변경 | 호출하면 좌석 점유·결제·환불처럼 서버의 상태가 실제로 바뀌는지 여부입니다. |
| 실서버 확인 | 실제 서버에서 이 메서드의 응답을 확인했는지 여부입니다. 자세한 기록은 [실서버 확인 현황](../status.md)에 있습니다. |

## 공통 예외

다음 예외는 여러 메서드에서 공통으로 발생할 수 있습니다. 각 메서드 설명에는 그 메서드에만 해당하는 예외를 따로 적었습니다.
예외 계층과 처리 방법은 [오류 처리](../guide/errors.md)를 참고하세요.

| 예외 | 발생 조건 |
|---|---|
| [`KorailTransportError`][korail_mobile_api.errors.KorailTransportError] | 네트워크 오류가 나거나 서버가 2xx가 아닌 HTTP 상태로 응답했을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 요청 전 입력 검사에 실패했을 때, 응답이 JSON이 아니거나 필수 값이 없어 읽을 수 없을 때 |
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인이 필요한 메서드를 로그인하지 않고 호출했을 때 |
| [`KorailSessionExpiredError`][korail_mobile_api.errors.KorailSessionExpiredError] | 서버 세션이 만료됐을 때(결과 코드 `P058`). 로컬 세션도 비웁니다. |
| [`KorailAppError`][korail_mobile_api.errors.KorailAppError]와 하위 예외 | 서버가 실패(`FAIL`)로 응답했을 때. 결과 코드에 따라 하위 예외로 나뉩니다. 실패를 응답으로 돌려주는 메서드는 예외를 발생시키지 않습니다. |
| [`KorailDynaPathError`][korail_mobile_api.errors.KorailDynaPathError] | DynaPath 보호 경로의 응답이 차단 신호였을 때 |
| [`KorailDynaPathRequiredError`][korail_mobile_api.errors.KorailDynaPathRequiredError] | `KorailConfig(disable_dynapath=True)`로 토큰이 필요한 로그인을 호출했을 때. 로그인 요청은 보내지 않습니다. |
| [`KorailNetFunnelError`][korail_mobile_api.errors.KorailNetFunnelError] | 대기열을 통과하지 못해 요청을 보내지 않았을 때. `reserve`·`pay`·`reservation_view` 관문은 대기열 서버 오류나 통과 외 응답에서, 모든 관문은 누적 대기 시간이 `netfunnel_wait_limit`를 넘거나 대기 응답에 입장 키가 없을 때 발생합니다. 열차 조회 관문은 대기열 서버 오류 시 대기열 없이 요청을 보냅니다. |
| [`KorailQueueRejectedError`][korail_mobile_api.errors.KorailQueueRejectedError] | 대기열 서버가 요청을 차단했을 때(`301`, `302`) |

## 전체 메서드

### [세션·공통](session.md)

로그인과 세션, 서버 상태·역 목록·운행 달력 같은 공통 정보.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`login`](session.md#login) | 회원 계정으로 로그인하고 세션을 만듭니다. | 필요 없음 | 아니요 | 확인됨 |
| [`logout`](session.md#logout) | 서버에 로그아웃을 요청하고 로컬 세션을 비웁니다. | 필요 없음 | 아니요 | 확인됨 |
| [`clear_session`](session.md#clear_session) | 서버에 알리지 않고 로컬 세션과 쿠키만 비웁니다. | 필요 없음 | 아니요 | 해당 없음 |
| [`close`](session.md#close) | HTTP 연결 풀과 대기열 연결 풀을 닫습니다. | 필요 없음 | 아니요 | 해당 없음 |
| [`get_service_status`](session.md#get_service_status) | 예매 서비스가 열려 있는지 확인합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_app_data`](session.md#get_app_data) | 앱 메인 화면이 쓰는 캐시 파일(버전 정보, 공지, 안내 문구)을 받아 옵니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_notice`](session.md#get_notice) | 앱 메인 캐시에 들어 있는 공지를 읽습니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_common_code`](session.md#get_common_code) | 공통 코드 이름으로 서버의 앱 설정값을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_uuid`](session.md#get_uuid) | 서버가 발급하는 단말 검증값을 받아 옵니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_station_info`](session.md#get_station_info) | 역 데이터의 판본과 수록 역 수를 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_station_data`](session.md#get_station_data) | 전체 역 목록을 코드·이름·좌표와 함께 받아 옵니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_train_calendar`](session.md#get_train_calendar) | 지금 예매할 수 있는 운행일 달력을 받아 옵니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_crew_request_list`](session.md#get_crew_request_list) | 승무원 호출 화면에 띄울 요청 사유 목록을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |

### [열차 조회·좌석](trains.md)

직통·환승 열차 조회, 정차역, 호차·좌석 배치, 운임.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`search_trains`](trains.md#search_trains) | 한 구간·한 날짜의 직통 열차를 한 페이지 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`search_transfer_trains`](trains.md#search_transfer_trains) | 같은 조회 조건으로 환승 여정을 한 페이지 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`search_trains_with_transfer_fallback`](trains.md#search_trains_with_transfer_fallback) | 직통 열차가 없을 때만 같은 조건으로 환승 여정을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_transfer_stations`](trains.md#get_transfer_stations) | 한 구간에서 환승할 수 있는 역 목록을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_train_schedule`](trains.md#get_train_schedule) | 열차 한 편의 정차역과 도착·출발 시각, 지연 정보를 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_seat_cars`](trains.md#get_seat_cars) | 열차 한 편의 호차 목록과 호차별 잔여석·좌석 속성을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_seat_inventory`](trains.md#get_seat_inventory) | 한 호차의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_free_seat_car_info`](trains.md#get_free_seat_car_info) | 열차 한 편의 자유석 호차 안내를 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_seat_assignment_schedule`](trains.md#get_seat_assignment_schedule) | 좌석배정 예매 화면의 열차 목록을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_merge_seats_inquiry`](trains.md#get_merge_seats_inquiry) | 병합 예약으로 이어 붙일 수 있는 열차 구간과 좌석이 갈리는 중간역을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_guide_seat_condition`](trains.md#get_guide_seat_condition) | 도우미석 이용 안내를 조회합니다. | 필요 | 아니요 | 서버 응답만 확인 |
| [`get_price_fare_quote`](trains.md#get_price_fare_quote) | 열차 한두 편의 운임을 예매 전에 조회합니다. | 필요 없음 | 아니요 | 확인됨 |

### [예약](reservations.md)

결제 전 예약(홀드)을 만들고, 조회하고, 취소하기.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`reserve`](reservations.md#reserve) | 열차 한 편에 결제 전 예약(홀드)을 만듭니다. | 필요 | 예 | 확인됨 |
| [`reserve_transfer`](reservations.md#reserve_transfer) | 환승 여정의 두 열차를 한 PNR로 홀드합니다. | 필요 | 예 | 확인됨 |
| [`reserve_merge`](reservations.md#reserve_merge) | 병합 예약의 후속 홀드를 만듭니다. | 필요 | 예 | 확인됨 |
| [`confirm_standby_hold`](reservations.md#confirm_standby_hold) | 예약대기 홀드에 문자 알림과 객실 등급 변경 옵션을 저장합니다. | 필요 | 예 | 확인됨 |
| [`cancel_unpaid_hold`](reservations.md#cancel_unpaid_hold) | 결제하지 않은 홀드를 취소합니다. | 필요 | 예 | 확인됨 |
| [`get_reservation_history`](reservations.md#get_reservation_history) | 로그인 계정에 남아 있는 예약(결제 전 홀드 포함)을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_ticket_reservation_detail`](reservations.md#get_ticket_reservation_detail) | PNR로 예약 하나의 여정과 좌석 상세를 다시 읽습니다. | 필요 | 아니요 | 확인됨 |
| [`check_ticket_duplication`](reservations.md#check_ticket_duplication) | 같은 PNR로 잡혀 있는 예약 건수를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_cart_list`](reservations.md#get_cart_list) | 로그인 계정의 장바구니를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`add_to_cart`](reservations.md#add_to_cart) | 결제 전 홀드를 장바구니에 담습니다. | 필요 | 예 | 확인됨 |

### [결제·환불](payments.md)

카드 결제, 할인 재계산, 환불 수수료 조회와 환불.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`pay_with_card`](payments.md#pay_with_card) | 홀드를 카드로 결제합니다. | 필요 | 예 | 확인됨 |
| [`recalculate_price`](payments.md#recalculate_price) | 홀드의 할인 조합을 바꿔 결제 금액을 다시 계산합니다. | 필요 | 예 | 확인됨 |
| [`get_refund_ticket_detail`](payments.md#get_refund_ticket_detail) | 환불할 승차권의 여정·좌석·운임 상세를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_refund_commission`](payments.md#get_refund_commission) | 승차권 한 장의 예상 환불액과 수수료를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`refund`](payments.md#refund) | 발권된 승차권 한 장을 환불합니다. | 필요 | 예 | 확인됨 |
| [`verify_station_ticket_refund`](payments.md#verify_station_ticket_refund) | 역에서 발권한 승차권을 온라인으로 환불할 수 있는지와 금액을 확인합니다. | 필요 | 아니요 | 미확인 |
| [`execute_station_ticket_refund`](payments.md#execute_station_ticket_refund) | 역에서 발권해 확인을 마친 승차권의 환불을 요청합니다. | 필요 | 예 | 미확인 |

### [승차권·계정](account.md)

승차권 목록과 영수증, 포인트·마일리지·쿠폰, 여정 변경, 지연확인증.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`get_ticket_list`](account.md#get_ticket_list) | 로그인 계정의 승차권 목록 한 페이지를 예약별로 묶어 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_ticket_receipt`](account.md#get_ticket_receipt) | 승차권 한 장의 영수증과 결제수단을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_korail_point_summary`](account.md#get_korail_point_summary) | 계정의 포인트, 쿠폰·지연할인권 개수, 복지 할인 자격 같은 요약 정보를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_mileage_history`](account.md#get_mileage_history) | 기간 안의 마일리지 적립·사용 내역 한 페이지를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_discount_coupons`](account.md#get_discount_coupons) | 계정이 가진 할인쿠폰 목록 한 페이지를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_delay_discount_tickets`](account.md#get_delay_discount_tickets) | 계정이 가진 지연할인권 목록을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_deposit_banks`](account.md#get_deposit_banks) | 입금 가능한 은행의 코드와 이름 목록을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_customer_trip_info`](account.md#get_customer_trip_info) | 로그인 계정에 저장된 여행 편의설정을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_multi_child_discount_targets`](account.md#get_multi_child_discount_targets) | 다자녀 할인 대상으로 등록된 가족 구성원을 조회합니다. | 필요 | 아니요 | 서버 응답만 확인 |
| [`get_trip_change_dates`](account.md#get_trip_change_dates) | 여정 변경으로 옮겨 갈 수 있는 날짜 목록을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_original_ticket_inquiry`](account.md#get_original_ticket_inquiry) | 여정 변경의 기준이 되는 원표를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_self_seat_change_info`](account.md#get_self_seat_change_info) | 자율 좌석·열차 변경으로 옮겨 갈 수 있는 승차역과 변경 사유를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_delay_certificate`](account.md#get_delay_certificate) | 지난 승차권의 지연확인증(열차가 몇 분 늦게 도착했는지)을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_delay_return_receipt`](account.md#get_delay_return_receipt) | 열차 지연으로 돌려받은 지연료의 반환 영수증을 조회합니다. | 필요 | 아니요 | 서버 응답만 확인 |

### [대리수령·셀프 체크인](delivery-checkin.md)

승차권 전달·대리수령과 자유석 셀프 체크인.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`get_recent_delivery_history`](delivery-checkin.md#get_recent_delivery_history) | 최근에 승차권을 전달했던 수령자 목록을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_delivery_recipient`](delivery-checkin.md#get_delivery_recipient) | N카드 2인 승차권을 전달하기 전에 수령자 후보를 조회합니다. | 필요 | 아니요 | 미확인 |
| [`get_pbp_acceptance_specifications`](delivery-checkin.md#get_pbp_acceptance_specifications) | 전달한 승차권 여러 장의 대리수령 내역을 여정·좌석 단위로 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`retrieve_delivered_ticket`](delivery-checkin.md#retrieve_delivered_ticket) | 다른 회원에게 전달한 승차권을 회수합니다. | 필요 | 예 | 미확인 |
| [`get_self_checkin_info`](delivery-checkin.md#get_self_checkin_info) | 셀프 체크인으로 등록한 자유석 좌석 정보를 조회합니다. | 필요 | 아니요 | 서버 응답만 확인 |
| [`check_self_checkin_seat`](delivery-checkin.md#check_self_checkin_seat) | 좌석의 QR 코드를 스캔한 문자열로 셀프 체크인할 수 있는 좌석을 확인합니다. | 필요 | 아니요 | 미확인 |
| [`register_self_checkin`](delivery-checkin.md#register_self_checkin) | [`check_self_checkin_seat`](delivery-checkin.md#check_self_checkin_seat)로 확인한 좌석으로 셀프 체크인을 등록합니다. | 필요 | 예 | 미확인 |
| [`cancel_self_checkin`](delivery-checkin.md#cancel_self_checkin) | 등록한 셀프 체크인을 취소합니다. | 필요 | 예 | 미확인 |

### [정기권·패스·N카드·여행상품](passes.md)

정기권·패스 조회, N카드 구매·예약, 여행상품 예약 관리.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`get_pass_menu`](passes.md#get_pass_menu) | 정기권·패스 메뉴 한 갈래의 화면 구성 항목을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_pass_available_dates`](passes.md#get_pass_available_dates) | 정기권 상품 하나의 사용 개시 가능일과 발권 가능일을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_pass_schedule`](passes.md#get_pass_schedule) | 정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_commuter_kind_menu`](passes.md#get_commuter_kind_menu) | 정기권 종류 하나의 안내 문구와 조회 파라미터를 받아 옵니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_commuter_info`](passes.md#get_commuter_info) | 정기권 예매에 필요한 조건을 세 단계 중 하나로 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_trip_menu`](passes.md#get_trip_menu) | 여행상품 메뉴 화면에 그릴 항목과 그 안의 문구 묶음을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_discount_card_usage_history`](passes.md#get_discount_card_usage_history) | N카드 한 장을 이미 사용한 여행 내역을 조회합니다. | 필요 | 아니요 | 미확인 |
| [`get_discount_card_schedule`](passes.md#get_discount_card_schedule) | N카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회합니다. | 필요 | 아니요 | 미확인 |
| [`register_discount_card`](passes.md#register_discount_card) | 결제 전 N카드 구매를 만듭니다. | 필요 | 예 | 미확인 |
| [`extend_discount_card`](passes.md#extend_discount_card) | N카드의 유효기간을 실제로 연장합니다. | 필요 | 예 | 미확인 |
| [`reserve_with_discount_card`](passes.md#reserve_with_discount_card) | N카드로 좌석을 홀드합니다. | 필요 | 예 | 미확인 |
| [`get_product_reservations`](passes.md#get_product_reservations) | 로그인 계정이 예약한 여행상품 목록 한 페이지를 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`get_product_detail`](passes.md#get_product_detail) | 여행상품 예약 한 건의 상세와 취소 조건을 조회합니다. | 필요 | 아니요 | 확인됨 |
| [`cancel_product_reservation`](passes.md#cancel_product_reservation) | 여행상품 예약을 취소합니다. | 필요 | 예 | 확인됨 |

### [공항버스·부가서비스](airport-bus.md)

공항버스(리무진) 조회·예약과 부가서비스 메뉴·내역.

| 메서드 | 설명 | 로그인 | 상태 변경 | 실서버 확인 |
|---|---|:-:|:-:|:-:|
| [`get_limousine_schedules`](airport-bus.md#get_limousine_schedules) | 공항버스 운행 편 한 페이지를 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_limousine_seat_inventory`](airport-bus.md#get_limousine_seat_inventory) | 공항버스 한 편의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`reserve_limousine`](airport-bus.md#reserve_limousine) | 공항버스 좌석을 잡아 결제 전 예약(홀드)을 만듭니다. | 필요 | 예 | 확인됨 |
| [`get_maas_menu_list`](airport-bus.md#get_maas_menu_list) | 부가서비스 메뉴를 조회합니다. 전체 메뉴나 승차권 한 건에 대한 메뉴를 받을 수 있습니다. | 필요 | 아니요 | 확인됨 |
| [`get_maas_station_data`](airport-bus.md#get_maas_station_data) | 부가서비스 하나를 이용할 수 있는 역 목록을 조회합니다. | 필요 없음 | 아니요 | 확인됨 |
| [`get_maas_service_details`](airport-bus.md#get_maas_service_details) | 로그인한 계정이 신청한 부가서비스 내역을 조회합니다. | 필요 | 아니요 | 확인됨 |
