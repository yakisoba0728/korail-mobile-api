# 실서버 확인 현황

메서드마다 실제 KORAIL 서버에 요청해 응답을 확인했는지 정리한 표입니다. 2026년 9월 24~26일 기준이며, 개인정보와 식별자는 적지 않았습니다.

| 상태 | 수 | 뜻 |
|---|---:|---|
| 확인됨 | 66 | 실서버에서 정상 응답을 받았습니다. |
| 서버 응답만 확인 | 4 | 요청은 서버까지 갔지만 계정에 해당 자료나 자격이 없어 오류 코드만 확인했습니다. |
| 미확인 | 12 | 필요한 카드·승차권·상태를 만들 수 없어 보내지 못했습니다. |
| 해당 없음 | 2 | 네트워크를 쓰지 않는 메서드입니다. |

실서버 확인은 그 시점의 결과입니다. KORAIL이 서버나 앱을 바꾸면 결과가 달라질 수 있습니다.

## 세션·공통

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`login`](api/session.md#login) | 확인됨 | 2026-09-26 앱 DTO 순서(txtInputFlg 먼저)로 로그인 SUCC · User-Agent korailtalk · 하이픈 든 ID는 요청 전 거절 |
| [`logout`](api/session.md#logout) | 확인됨 | 로그아웃 뒤 요청은 FAIL/P058 → 세션 만료 처리 |
| [`clear_session`](api/session.md#clear_session) | 해당 없음 | - |
| [`close`](api/session.md#close) | 해당 없음 | 닫은 뒤 호출은 요청 없이 KorailProtocolError |
| [`get_service_status`](api/session.md#get_service_status) | 확인됨 | SUCC/S100 |
| [`get_app_data`](api/session.md#get_app_data) | 확인됨 | - |
| [`get_notice`](api/session.md#get_notice) | 확인됨 | - |
| [`get_common_code`](api/session.md#get_common_code) | 확인됨 | SUCC/API.I00000 |
| [`get_uuid`](api/session.md#get_uuid) | 확인됨 | - |
| [`get_station_info`](api/session.md#get_station_info) | 확인됨 | - |
| [`get_station_data`](api/session.md#get_station_data) | 확인됨 | 281역 |
| [`get_train_calendar`](api/session.md#get_train_calendar) | 확인됨 | 32일 |
| [`get_crew_request_list`](api/session.md#get_crew_request_list) | 확인됨 | 3건 |

## 열차 조회·좌석

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`search_trains`](api/trains.md#search_trains) | 확인됨 | 서울→부산 10편 · 청소년·유아·안내견을 앱처럼 합쳐 조회 · peak_season=True 면 peak_season_inquiry, 특가 조회(use_special_schedule)면 product_inquiry 관문 — 이 두 관문은 실서버 미확인 |
| [`search_transfer_trains`](api/trains.md#search_transfer_trains) | 확인됨 | 강릉→목포 여정 2개 |
| [`search_trains_with_transfer_fallback`](api/trains.md#search_trains_with_transfer_fallback) | 확인됨 | 강릉→목포에서 환승으로 전환(여정 2개) |
| [`get_transfer_stations`](api/trains.md#get_transfer_stations) | 확인됨 | 2역 |
| [`get_train_schedule`](api/trains.md#get_train_schedule) | 확인됨 | 9역 |
| [`get_seat_cars`](api/trains.md#get_seat_cars) | 확인됨 | 13~14량 · 2026-09-25 앱 순서 요청으로 재확인 · 빠진 선택 필드는 앱 기본값 |
| [`get_seat_inventory`](api/trains.md#get_seat_inventory) | 확인됨 | 56석·창 6개 · 2026-09-25 재확인 · 잘못된 좌석속성은 요청 전 거절 |
| [`get_free_seat_car_info`](api/trains.md#get_free_seat_car_info) | 확인됨 | 2026-09-25 열차 203편 확인 · 자유석 칸이 있는 183편은 호차 문구(KTX 18호차·17·18호차, 산천 8·18호차, ITX-새마을 6호차 등), 없는 20편은 IRZ000005 · 조회 행의 자유석 칸 수와 모두 일치 |
| [`get_seat_assignment_schedule`](api/trains.md#get_seat_assignment_schedule) | 확인됨 | 10편 · 추석 기간(9/26)은 WRD000057 명절 할인 없음 · peak_season=True 면 peak_season_inquiry 관문(실서버 미확인) |
| [`get_merge_seats_inquiry`](api/trains.md#get_merge_seats_inquiry) | 확인됨 | 2편 |
| [`get_guide_seat_condition`](api/trains.md#get_guide_seat_condition) | 서버 응답만 확인 | 좌석코드와 무관하게 FAIL/MRR800011 — 대피도우미석 대상(만20~50세, 시발~종착 이용)이 아닌 계정 · 코드 999도 같음 · 로그인 전 P058 |
| [`get_price_fare_quote`](api/trains.md#get_price_fare_quote) | 확인됨 | SUCC/API.I00000 · 앱에선 표시용 기준 운임 · 홀드 h_tot_prc 와 같고 정산액은 좌석 할인만큼 낮을 수 있음 · 환승 2구간은 4행 · gdNo 빈 값도 앱처럼 전송 |

## 예약

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`reserve`](api/reservations.md#reserve) | 확인됨 | SUCC/IRR000018 · 바로 취소 · 2026-09-25 앱 순서로 일반·좌석지정 홀드 재확인 · 예약대기 홀드는 결제 불가 표시 · 입석만 남은 행은 거절 |
| [`reserve_transfer`](api/reservations.md#reserve_transfer) | 확인됨 | 2구간 · 2026-09-25 앱 순서로 48,100원 홀드 후 취소 · 구간은 서로 다른 열차·탑승 순서여야 함 |
| [`reserve_merge`](api/reservations.md#reserve_merge) | 확인됨 | 확인 후 취소 · 병합 행은 운행일이 같아야 함 · 첫 홀드도 결제 가능 |
| [`confirm_standby_hold`](api/reservations.md#confirm_standby_hold) | 확인됨 | 2026-09-25 ITX-새마을 1022 대기 홀드(IRR000014, 결제 불가 표시) → 옵션 저장 SUCC/IRZ000003 → 취소 IRG000000 → P100 |
| [`cancel_unpaid_hold`](api/reservations.md#cancel_unpaid_hold) | 확인됨 | SUCC/IRG000000 |
| [`get_reservation_history`](api/reservations.md#get_reservation_history) | 확인됨 | P100(홀드 없음) |
| [`get_ticket_reservation_detail`](api/reservations.md#get_ticket_reservation_detail) | 확인됨 | SUCC/IRZ000001 |
| [`check_ticket_duplication`](api/reservations.md#check_ticket_duplication) | 확인됨 | 홀드 PNR로 SUCC |
| [`get_cart_list`](api/reservations.md#get_cart_list) | 확인됨 | 담은 열차·공항버스 홀드가 행으로 보임 |
| [`add_to_cart`](api/reservations.md#add_to_cart) | 확인됨 | SUCC/IRZ000002 · 홀드 취소하면 장바구니도 비워짐 |

## 결제·환불

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`pay_with_card`](api/payments.md#pay_with_card) | 확인됨 | 2026-09-25 새 대기열·User-Agent 로 7,500원 결제 IRT000000 후 수수료 0원 환불 · 예약대기·0원 홀드·잘못된 카드 입력은 요청 전 거절 |
| [`recalculate_price`](api/payments.md#recalculate_price) | 확인됨 | 2026-09-25 평일 할인 변경 SUCC/IRZ000008 21,500→15,000원(Retrofit 목록 순서로 재확인) · 토요일은 같은 코드에 금액 그대로 · 변경 없음 ERR930202 · 결제에는 재계산 결과 홀드 사용 · add_to_cart 옵션·for_hold 실서버 확인 |
| [`get_refund_ticket_detail`](api/payments.md#get_refund_ticket_detail) | 확인됨 | - |
| [`get_refund_commission`](api/payments.md#get_refund_commission) | 확인됨 | 결제한 표 수수료 0원(2026-09-24, 2026-09-25 공통 필드를 뒤에 둔 앱 순서로 재확인) · 이미 환불된 표는 WRT200399 · 지난 표는 WRT200022 |
| [`refund`](api/payments.md#refund) | 확인됨 | 2026-09-25 앱 순서 요청으로 수수료 0원 환불 SUCC/IRT200277(두 번) · 수수료 조회 응답 필수 · 마일리지 정산은 마일리지 ≥ 수수료일 때만 |
| [`verify_station_ticket_refund`](api/payments.md#verify_station_ticket_refund) | 미확인 | 역 발권 승차권 없음 |
| [`execute_station_ticket_refund`](api/payments.md#execute_station_ticket_refund) | 미확인 | 역 발권 승차권 없음 |

## 승차권·계정

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_ticket_list`](api/account.md#get_ticket_list) | 확인됨 | 현재 0장 · 이력 131건 · 2026-09-25 앱 순서 요청으로 재확인 |
| [`get_ticket_receipt`](api/account.md#get_ticket_receipt) | 확인됨 | 1건 · 식별값은 키워드로만 받음 |
| [`get_korail_point_summary`](api/account.md#get_korail_point_summary) | 확인됨 | - |
| [`get_mileage_history`](api/account.md#get_mileage_history) | 확인됨 | - |
| [`get_discount_coupons`](api/account.md#get_discount_coupons) | 확인됨 | 0장 · 할인값을 주중·주말·운임·요금 필드로 나눔 |
| [`get_delay_discount_tickets`](api/account.md#get_delay_discount_tickets) | 확인됨 | 0장 · 값은 URL 쿼리로 보냄 |
| [`get_deposit_banks`](api/account.md#get_deposit_banks) | 확인됨 | 56개 |
| [`get_customer_trip_info`](api/account.md#get_customer_trip_info) | 확인됨 | SUCC/IRS100002 |
| [`get_multi_child_discount_targets`](api/account.md#get_multi_child_discount_targets) | 서버 응답만 확인 | WRC800029 — 이 계정은 다자녀 자격 없음 |
| [`get_trip_change_dates`](api/account.md#get_trip_change_dates) | 확인됨 | 15일 |
| [`get_original_ticket_inquiry`](api/account.md#get_original_ticket_inquiry) | 확인됨 | 2026-09-25 인쇄완료 승차권 2장 SUCC/IRT000001(원권조회완료) · 환불된 표는 WRT200399 |
| [`get_self_seat_change_info`](api/account.md#get_self_seat_change_info) | 확인됨 | 2026-09-25 운행 중인 KTX 023(행신→부산)으로 SUCC · 승차권 없이 열차 정보만 받음 · 운행 시간 밖은 WRT800176 |
| [`get_delay_certificate`](api/account.md#get_delay_certificate) | 확인됨 | 2026-09-25 지연 승차권 2장 SUCC/IAZ000006·행 1개(행에 runDt 없음) · 지연 안 된 표는 WRT400456 |
| [`get_delay_return_receipt`](api/account.md#get_delay_return_receipt) | 서버 응답만 확인 | IRZ000005 — 지연료를 돌려받은 승차권 없음 |

## 대리수령·셀프 체크인

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_recent_delivery_history`](api/delivery-checkin.md#get_recent_delivery_history) | 확인됨 | 1명 · acepList 필수, chgePbpRsvNo 는 없어도 됨(2026-09-25) |
| [`get_delivery_recipient`](api/delivery-checkin.md#get_delivery_recipient) | 미확인 | 검증 못 함 · N카드 2인 승차권 없음(서버는 IRZ000005) |
| [`get_pbp_acceptance_specifications`](api/delivery-checkin.md#get_pbp_acceptance_specifications) | 확인됨 | 2026-09-25 대리수령 대상(Y) 승차권 6장 → 6장 명세 · 대상 아닌 표는 0건 · 튜플·목록 모두 받음 |
| [`retrieve_delivered_ticket`](api/delivery-checkin.md#retrieve_delivered_ticket) | 미확인 | 검증 못 함 · 전달한 승차권 없음(전달하면 다른 회원에게 실제 승차권이 감) |
| [`get_self_checkin_info`](api/delivery-checkin.md#get_self_checkin_info) | 서버 응답만 확인 | WRZ000001 — 체크인한 승차권 없음 |
| [`check_self_checkin_seat`](api/delivery-checkin.md#check_self_checkin_seat) | 미확인 | 검증 못 함 · 열차 안 좌석 QR 이 필요해 보내지 않음 |
| [`register_self_checkin`](api/delivery-checkin.md#register_self_checkin) | 미확인 | 검증 못 함 · 좌석 QR 필요 · 앱 안내상 부정 사용 시 부가금이 있어 가짜 값은 보내지 않음 |
| [`cancel_self_checkin`](api/delivery-checkin.md#cancel_self_checkin) | 미확인 | 검증 못 함 · 체크인한 승차권 없음 |

## 정기권·패스·N카드·여행상품

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_pass_menu`](api/passes.md#get_pass_menu) | 확인됨 | 22항목 |
| [`get_pass_available_dates`](api/passes.md#get_pass_available_dates) | 확인됨 | - |
| [`get_pass_schedule`](api/passes.md#get_pass_schedule) | 확인됨 | 2026-09-25 일반정기권(0001)·기간자유형(0028) 다섯 조합 모두 SUCC(서울→부산 7편, 서울→대전 4편) · 9/24 실패는 내일로 코드(0046)를 넣은 탓 |
| [`get_commuter_kind_menu`](api/passes.md#get_commuter_kind_menu) | 확인됨 | SUCC/IRZ000001 |
| [`get_commuter_info`](api/passes.md#get_commuter_info) | 확인됨 | 초기·인원 IRZ000008 · 원표 단계는 ERR000100(정기권 아님) |
| [`get_trip_menu`](api/passes.md#get_trip_menu) | 확인됨 | 5메뉴 |
| [`get_discount_card_usage_history`](api/passes.md#get_discount_card_usage_history) | 미확인 | 검증 못 함 · N카드 없음(서버는 ERR000100) |
| [`get_discount_card_schedule`](api/passes.md#get_discount_card_schedule) | 미확인 | 검증 못 함 · N카드 없음(서버는 WRR000100) |
| [`register_discount_card`](api/passes.md#register_discount_card) | 미확인 | 검증 못 함 · 실제 구매가 되므로 시도하지 않음 |
| [`extend_discount_card`](api/passes.md#extend_discount_card) | 미확인 | 검증 못 함 · N카드 없음 |
| [`reserve_with_discount_card`](api/passes.md#reserve_with_discount_card) | 미확인 | 검증 못 함 · N카드 없음 |
| [`get_product_reservations`](api/passes.md#get_product_reservations) | 확인됨 | 웹에서 만든 결제 전 예약: 예약확정(03) → 취소 후 05 |
| [`get_product_detail`](api/passes.md#get_product_detail) | 확인됨 | 15,400원 · 취소 수수료 0원 · 포함 열차 2개 |
| [`cancel_product_reservation`](api/passes.md#cancel_product_reservation) | 확인됨 | 결제 전 예약 SUCC 취소 · 결제 후 환불은 결제 불가라 미확인 |

## 공항버스·부가서비스

| 메서드 | 상태 | 결과 |
|---|:-:|---|
| [`get_limousine_schedules`](api/airport-bus.md#get_limousine_schedules) | 확인됨 | 광명→인천공항 30편 |
| [`get_limousine_seat_inventory`](api/airport-bus.md#get_limousine_seat_inventory) | 확인됨 | 28석 |
| [`reserve_limousine`](api/airport-bus.md#reserve_limousine) | 확인됨 | 홀드 16,000원·24,000원 취소 · 16,000원 결제 후 수수료 0원 환불 · 2026-09-25 앱 순서로 재확인 |
| [`get_maas_menu_list`](api/airport-bus.md#get_maas_menu_list) | 확인됨 | 11개 |
| [`get_maas_station_data`](api/airport-bus.md#get_maas_station_data) | 확인됨 | 101역 |
| [`get_maas_service_details`](api/airport-bus.md#get_maas_service_details) | 확인됨 | 빈 목록 |
