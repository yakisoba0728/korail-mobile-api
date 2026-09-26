# 실서버 확인 현황

메서드마다 실제 KORAIL 서버에 요청해 응답을 확인했는지 정리한 표입니다. 2026년 9월 24~26일 기준이며, 개인정보와 식별자는 적지 않았습니다.

| 상태 | 수 | 뜻 |
|---|---:|---|
| 확인됨 | 66 | 실서버에서 정상 응답을 받았습니다. |
| 서버 응답만 확인 | 4 | 요청은 서버까지 갔지만 계정에 해당 자료나 자격이 없어 실패 결과 코드만 확인했습니다. |
| 미확인 | 12 | 필요한 카드·승차권·상태가 없어 정상 응답을 확인하지 못했습니다. 일부는 요청을 보내 실패 결과 코드만 받았습니다. |
| 해당 없음 | 2 | 네트워크를 쓰지 않는 메서드입니다. |

실서버 확인은 그 시점의 결과입니다. KORAIL이 서버나 앱을 바꾸면 결과가 달라질 수 있습니다.

## 세션·공통

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`login`](api/session.md#login) | 확인됨 | 로그인에 성공했습니다. 하이픈이 든 ID는 요청 전에 거절합니다. |
| [`logout`](api/session.md#logout) | 확인됨 | 로그아웃한 뒤의 요청은 `FAIL`/`P058`을 받으며, 세션 만료로 처리합니다. |
| [`clear_session`](api/session.md#clear_session) | 해당 없음 | - |
| [`close`](api/session.md#close) | 해당 없음 | 닫은 뒤에 호출하면 요청을 보내지 않고 `KorailProtocolError`가 발생합니다. |
| [`get_service_status`](api/session.md#get_service_status) | 확인됨 | `SUCC`/`S100`을 받았습니다. |
| [`get_app_data`](api/session.md#get_app_data) | 확인됨 | - |
| [`get_notice`](api/session.md#get_notice) | 확인됨 | - |
| [`get_common_code`](api/session.md#get_common_code) | 확인됨 | `SUCC`/`API.I00000`을 받았습니다. |
| [`get_uuid`](api/session.md#get_uuid) | 확인됨 | - |
| [`get_station_info`](api/session.md#get_station_info) | 확인됨 | - |
| [`get_station_data`](api/session.md#get_station_data) | 확인됨 | 역 281개를 받았습니다. |
| [`get_train_calendar`](api/session.md#get_train_calendar) | 확인됨 | 32일치 날짜를 받았습니다. |
| [`get_crew_request_list`](api/session.md#get_crew_request_list) | 확인됨 | 요청 사유 3건을 받았습니다. |

## 열차 조회·좌석

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`search_trains`](api/trains.md#search_trains) | 확인됨 | 서울→부산 열차 10편을 받았습니다. 청소년·유아·안내견 인원은 앱과 같이 어른·어린이 인원에 합쳐 보냅니다. `peak_season=True`일 때의 `peak_season_inquiry` 관문과 `use_special_schedule=True`일 때의 `product_inquiry` 관문은 실서버에서 확인하지 못했습니다. |
| [`search_transfer_trains`](api/trains.md#search_transfer_trains) | 확인됨 | 강릉→목포 환승 여정 2개를 받았습니다. |
| [`search_trains_with_transfer_fallback`](api/trains.md#search_trains_with_transfer_fallback) | 확인됨 | 강릉→목포 조회가 환승 조회로 전환돼 여정 2개를 받았습니다. |
| [`get_transfer_stations`](api/trains.md#get_transfer_stations) | 확인됨 | 환승역 2개를 받았습니다. |
| [`get_train_schedule`](api/trains.md#get_train_schedule) | 확인됨 | 정차역 9개를 받았습니다. |
| [`get_seat_cars`](api/trains.md#get_seat_cars) | 확인됨 | 호차 13~14개를 받았습니다. 응답에 없는 호차 필드 가운데 네 개는 앱 기본값(문자열은 `""`, 숫자는 `None`)으로 읽습니다. |
| [`get_seat_inventory`](api/trains.md#get_seat_inventory) | 확인됨 | 좌석 56석과 창문 6개를 받았습니다. 세 자리 숫자가 아닌 좌석 속성 코드는 요청 전에 거절합니다. |
| [`get_free_seat_car_info`](api/trains.md#get_free_seat_car_info) | 확인됨 | 열차 203편을 조회했습니다. 자유석 칸이 있는 183편은 호차 안내 문구(KTX 18호차, KTX-산천 8·18호차, ITX-새마을 6호차 등)를 받았습니다. 자유석 칸이 없는 20편은 `IRZ000005`를 받았습니다. 모두 열차 조회 결과의 자유석 칸 수와 일치했습니다. |
| [`get_seat_assignment_schedule`](api/trains.md#get_seat_assignment_schedule) | 확인됨 | 열차 10편을 받았습니다. 추석 기간 날짜로 조회하면 `WRD000057`을 받았습니다. `peak_season=True`일 때의 `peak_season_inquiry` 관문은 실서버에서 확인하지 못했습니다. |
| [`get_merge_seats_inquiry`](api/trains.md#get_merge_seats_inquiry) | 확인됨 | 열차 2편을 받았습니다. |
| [`get_guide_seat_condition`](api/trains.md#get_guide_seat_condition) | 서버 응답만 확인 | `seat_attribute_code`와 관계없이 `FAIL`/`MRR800011`을 받았습니다. `seat_attribute_code`가 `"999"`일 때도 같았습니다. 로그인 전에는 `P058`을 받았습니다. |
| [`get_price_fare_quote`](api/trains.md#get_price_fare_quote) | 확인됨 | `SUCC`/`API.I00000`을 받았습니다. 받은 운임은 홀드의 `total_price`와 같았습니다. 실제 결제액인 홀드의 `received_amount`는 좌석 할인만큼 더 낮을 수 있습니다. 환승 2구간 조회는 운임 4행을 받았습니다. |

## 예약

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`reserve`](api/reservations.md#reserve) | 확인됨 | `SUCC`/`IRR000018`로 홀드를 만든 뒤 바로 취소했습니다. 일반 예약과 좌석 지정 예약 모두 홀드를 만들었습니다. 예약대기 홀드는 결제할 수 없는 상태로 표시됩니다. 선택한 객실에 빈 좌석이 확인되지 않는 행(입석만 남은 행 포함)은 요청 전에 거절합니다. |
| [`reserve_transfer`](api/reservations.md#reserve_transfer) | 확인됨 | 2구간 환승 홀드를 만든 뒤 취소했습니다. 두 구간이 같은 열차이거나 탑승 순서가 아니면 요청 전에 거절합니다. |
| [`reserve_merge`](api/reservations.md#reserve_merge) | 확인됨 | 병합 예약 홀드를 만든 뒤 취소했습니다. 첫 홀드도 결제할 수 있는 상태였습니다. 병합할 행의 운행일이 첫 홀드와 다르면 요청 전에 거절합니다. |
| [`confirm_standby_hold`](api/reservations.md#confirm_standby_hold) | 확인됨 | ITX-새마을 예약대기 홀드(`IRR000014`, 결제할 수 없는 상태)로 확인했습니다. 옵션 저장은 `SUCC`/`IRZ000003`을 받았습니다. 홀드 취소는 `IRG000000`을 받았고, 이후 예약 내역 조회는 `P100`을 받았습니다. |
| [`cancel_unpaid_hold`](api/reservations.md#cancel_unpaid_hold) | 확인됨 | `SUCC`/`IRG000000`을 받았습니다. |
| [`get_reservation_history`](api/reservations.md#get_reservation_history) | 확인됨 | 홀드가 없는 상태에서 `P100`을 받았습니다. |
| [`get_ticket_reservation_detail`](api/reservations.md#get_ticket_reservation_detail) | 확인됨 | `SUCC`/`IRZ000001`을 받았습니다. |
| [`check_ticket_duplication`](api/reservations.md#check_ticket_duplication) | 확인됨 | 홀드의 PNR로 `SUCC`를 받았습니다. |
| [`get_cart_list`](api/reservations.md#get_cart_list) | 확인됨 | 장바구니에 담은 열차 홀드와 공항버스 홀드가 행으로 나왔습니다. |
| [`add_to_cart`](api/reservations.md#add_to_cart) | 확인됨 | `SUCC`/`IRZ000002`를 받았습니다. 홀드를 취소하면 장바구니에서도 빠졌습니다. |

## 결제·환불

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`pay_with_card`](api/payments.md#pay_with_card) | 확인됨 | 7,500원 홀드를 결제해 `IRT000000`을 받았고, 수수료 0원으로 환불했습니다. 예약대기 홀드, 0원 홀드, 형식이 잘못된 카드 입력은 요청 전에 거절합니다. |
| [`recalculate_price`](api/payments.md#recalculate_price) | 확인됨 | 평일 열차의 할인을 바꾸자 `SUCC`/`IRZ000008`과 함께 금액이 21,500원에서 15,000원으로 바뀌었습니다. 토요일 열차는 같은 결과 코드를 받았지만 금액이 그대로였습니다. 할인이 바뀌지 않으면 `ERR930202`를 받았습니다. 결제에는 재계산 결과로 받은 홀드를 사용합니다. `add_to_cart=True`와 `PriceRecalculationRequest.for_hold()`로 만든 요청도 실서버에서 확인했습니다. |
| [`get_refund_ticket_detail`](api/payments.md#get_refund_ticket_detail) | 확인됨 | - |
| [`get_refund_commission`](api/payments.md#get_refund_commission) | 확인됨 | 결제한 승차권의 수수료로 0원을 받았습니다. 이미 환불한 승차권은 `WRT200399`, 승차일이 지난 승차권은 `WRT200022`를 받았습니다. |
| [`refund`](api/payments.md#refund) | 확인됨 | 수수료 0원 승차권 환불을 두 번 실행해 모두 `SUCC`/`IRT200277`을 받았습니다. `commission`이 [`get_refund_commission`](api/payments.md#get_refund_commission)의 응답이 아니면(`None` 포함) 요청 전에 `KorailProtocolError`가 발생합니다. `settle_mileage=True`는 사용할 수 있는 마일리지가 수수료 이상일 때만 받습니다. |
| [`verify_station_ticket_refund`](api/payments.md#verify_station_ticket_refund) | 미확인 | 역에서 발권한 승차권이 없어 확인하지 못했습니다. |
| [`execute_station_ticket_refund`](api/payments.md#execute_station_ticket_refund) | 미확인 | 역에서 발권한 승차권이 없어 확인하지 못했습니다. |

## 승차권·계정

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_ticket_list`](api/account.md#get_ticket_list) | 확인됨 | 현재 승차권 0장과 지난 이력 131건을 받았습니다. |
| [`get_ticket_receipt`](api/account.md#get_ticket_receipt) | 확인됨 | 영수증 1건을 받았습니다. |
| [`get_korail_point_summary`](api/account.md#get_korail_point_summary) | 확인됨 | - |
| [`get_mileage_history`](api/account.md#get_mileage_history) | 확인됨 | - |
| [`get_discount_coupons`](api/account.md#get_discount_coupons) | 확인됨 | 할인쿠폰 0장을 받았습니다. |
| [`get_delay_discount_tickets`](api/account.md#get_delay_discount_tickets) | 확인됨 | 지연할인권 0장을 받았습니다. |
| [`get_deposit_banks`](api/account.md#get_deposit_banks) | 확인됨 | 은행 56개를 받았습니다. |
| [`get_customer_trip_info`](api/account.md#get_customer_trip_info) | 확인됨 | `SUCC`/`IRS100002`를 받았습니다. |
| [`get_multi_child_discount_targets`](api/account.md#get_multi_child_discount_targets) | 서버 응답만 확인 | 다자녀 할인 대상이 아닌 계정에서 `WRC800029`를 받았습니다. |
| [`get_trip_change_dates`](api/account.md#get_trip_change_dates) | 확인됨 | 변경할 수 있는 날짜 15일을 받았습니다. |
| [`get_original_ticket_inquiry`](api/account.md#get_original_ticket_inquiry) | 확인됨 | 인쇄를 마친 승차권 2장으로 `SUCC`/`IRT000001`을 받았습니다. 환불한 승차권은 `WRT200399`를 받았습니다. |
| [`get_self_seat_change_info`](api/account.md#get_self_seat_change_info) | 확인됨 | 운행 중인 KTX 열차로 `SUCC`를 받았습니다. 운행 시간 밖의 열차는 `WRT800176`을 받았습니다. |
| [`get_delay_certificate`](api/account.md#get_delay_certificate) | 확인됨 | 지연된 승차권 2장으로 `SUCC`/`IAZ000006`과 지연 행 1개를 받았습니다. 받은 행에는 운행일이 없어 `run_date`가 `None`이었습니다. 지연되지 않은 승차권은 `WRT400456`을 받았습니다. |
| [`get_delay_return_receipt`](api/account.md#get_delay_return_receipt) | 서버 응답만 확인 | 지연료를 돌려받은 승차권이 없어 `IRZ000005`를 받았습니다. |

## 대리수령·셀프 체크인

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_recent_delivery_history`](api/delivery-checkin.md#get_recent_delivery_history) | 확인됨 | 수령자 1명을 받았습니다. 응답에 해당 값이 없어 `changed_acceptance_reservation_no`는 `None`이었습니다. |
| [`get_delivery_recipient`](api/delivery-checkin.md#get_delivery_recipient) | 미확인 | N카드 2인 승차권이 없어 수령자 응답을 확인하지 못했습니다. 서버는 `IRZ000005`를 반환했습니다. |
| [`get_pbp_acceptance_specifications`](api/delivery-checkin.md#get_pbp_acceptance_specifications) | 확인됨 | 대리수령 대상 승차권 6장으로 6장의 명세를 받았습니다. 대상이 아닌 승차권은 0건이었습니다. |
| [`retrieve_delivered_ticket`](api/delivery-checkin.md#retrieve_delivered_ticket) | 미확인 | 전달한 승차권이 없어 확인하지 못했습니다. 확인하려면 다른 회원에게 실제 승차권을 전달해야 합니다. |
| [`get_self_checkin_info`](api/delivery-checkin.md#get_self_checkin_info) | 서버 응답만 확인 | 체크인한 승차권이 없어 `WRZ000001`을 받았습니다. |
| [`check_self_checkin_seat`](api/delivery-checkin.md#check_self_checkin_seat) | 미확인 | 열차 좌석의 QR 코드가 필요해 요청을 보내지 않았습니다. |
| [`register_self_checkin`](api/delivery-checkin.md#register_self_checkin) | 미확인 | 열차 좌석의 QR 코드가 필요해 요청을 보내지 않았습니다. 앱 안내에 따르면 부정 사용 시 부가금이 있어 임의 값도 보내지 않았습니다. |
| [`cancel_self_checkin`](api/delivery-checkin.md#cancel_self_checkin) | 미확인 | 체크인한 승차권이 없어 확인하지 못했습니다. |

## 정기권·패스·N카드·여행상품

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_pass_menu`](api/passes.md#get_pass_menu) | 확인됨 | 메뉴 22항목을 받았습니다. |
| [`get_pass_available_dates`](api/passes.md#get_pass_available_dates) | 확인됨 | - |
| [`get_pass_schedule`](api/passes.md#get_pass_schedule) | 확인됨 | 일반정기권(`0001`)과 기간자유형(`0028`) 조합 다섯 가지 모두 `SUCC`를 받았습니다(서울→부산 7편, 서울→대전 4편). 내일로 상품 코드(`0046`)로는 실패했습니다. |
| [`get_commuter_kind_menu`](api/passes.md#get_commuter_kind_menu) | 확인됨 | `SUCC`/`IRZ000001`을 받았습니다. |
| [`get_commuter_info`](api/passes.md#get_commuter_info) | 확인됨 | 초기 단계와 인원 단계는 `IRZ000008`을 받았습니다. 원표 단계는 정기권이 아닌 승차권으로 요청해 `ERR000100`을 받았습니다. |
| [`get_trip_menu`](api/passes.md#get_trip_menu) | 확인됨 | 메뉴 5개를 받았습니다. |
| [`get_discount_card_usage_history`](api/passes.md#get_discount_card_usage_history) | 미확인 | N카드가 없어 확인하지 못했습니다. 서버는 `ERR000100`을 반환했습니다. |
| [`get_discount_card_schedule`](api/passes.md#get_discount_card_schedule) | 미확인 | N카드가 없어 확인하지 못했습니다. 서버는 `WRR000100`을 반환했습니다. |
| [`register_discount_card`](api/passes.md#register_discount_card) | 미확인 | 호출하면 결제 전 N카드 구매가 실제로 만들어지므로 요청을 보내지 않았습니다. |
| [`extend_discount_card`](api/passes.md#extend_discount_card) | 미확인 | N카드가 없어 확인하지 못했습니다. |
| [`reserve_with_discount_card`](api/passes.md#reserve_with_discount_card) | 미확인 | N카드가 없어 확인하지 못했습니다. |
| [`get_product_reservations`](api/passes.md#get_product_reservations) | 확인됨 | 웹에서 만든 결제 전 예약이 예약확정(`03`)으로 나왔고, 취소한 뒤에는 `05`로 나왔습니다. |
| [`get_product_detail`](api/passes.md#get_product_detail) | 확인됨 | 상품 금액 15,400원, 취소 수수료 0원, 포함 열차 2개를 받았습니다. |
| [`cancel_product_reservation`](api/passes.md#cancel_product_reservation) | 확인됨 | 결제 전 예약을 취소해 `SUCC`를 받았습니다. 상품을 결제할 수 없어 결제한 예약의 취소는 확인하지 못했습니다. |

## 공항버스·부가서비스

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_limousine_schedules`](api/airport-bus.md#get_limousine_schedules) | 확인됨 | 광명→인천공항 30편을 받았습니다. |
| [`get_limousine_seat_inventory`](api/airport-bus.md#get_limousine_seat_inventory) | 확인됨 | 좌석 28석을 받았습니다. |
| [`reserve_limousine`](api/airport-bus.md#reserve_limousine) | 확인됨 | 16,000원 홀드와 24,000원 홀드를 만든 뒤 취소했습니다. 16,000원 홀드는 결제한 뒤 수수료 0원으로 환불했습니다. |
| [`get_maas_menu_list`](api/airport-bus.md#get_maas_menu_list) | 확인됨 | 메뉴 11개를 받았습니다. |
| [`get_maas_station_data`](api/airport-bus.md#get_maas_station_data) | 확인됨 | 역 101개를 받았습니다. |
| [`get_maas_service_details`](api/airport-bus.md#get_maas_service_details) | 확인됨 | 빈 목록을 받았습니다. |
