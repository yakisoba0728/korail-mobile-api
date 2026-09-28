# 7.0.8 공개 메서드 실서버 검증

2026-09-28 기준 `KorailClient`의 공개 메서드 84개를 대상으로 한 결과입니다. 아래의 2026-09-24~26 확인 이력은 7.0.6 시기의 별도 근거이며, 이 표의 7.0.8 실서버 확인으로 합산하지 않았습니다.

| 분류 | 메서드 수 | 판정 기준 |
|---|---:|---|
| 실서버 응답 파싱 | 59 | 7.0.8 설정으로 호출해 반환 객체를 받음. 빈 결과 코드도 포함하며, 모든 분기·데이터가 검증됐다는 뜻은 아님. |
| 서버 거절 확인 | 10 | 요청은 서버에 도달했으나 유효한 결과를 받지 못함. |
| 7.0.8 미실행 | 13 | 활성 여행상품·보유 N카드·좌석 QR·결제수단 등 전제 자료가 없음. |
| 로컬 메서드 | 2 | 네트워크를 사용하지 않음. |

모든 84개 공개 호출 경로는 별도의 합성 계약 테스트(`tests/test_public_api_smoke.py::test_f8_all_public_methods`)에서 실제 빌더·파서와 필요한 경우 대기열을 거쳐 검사합니다. 이는 실서버 결과가 아닙니다. 이전 버전의 메서드별 실서버 상태는 [기존 확인표](status.md)에 있습니다.

실서버 기록은 요청 경로·HTTP 상태·폼 **필드 이름**·응답 결과 코드만 저장했습니다. 계정, 비밀번호, 쿠키, PNR, 카드 정보, 응답 본문은 저장하지 않았습니다. 본문 또는 기록된 URL 쿼리에서 `Device`가 보이는 요청 158건은 모두 `AppVersion=7.0.8`이 함께 있었습니다. 앞선 배치의 URL 쿼리와 본문 없는 POST는 이 수치에 넣지 않았습니다.

근거 파일: [P](evidence/live-708/live_708_public_batch.json) 비로그인, [A](evidence/live-708/live_708_auth_batch.json) 인증, [R](evidence/live-708/live_708_reversible_batch.json) 임시 예약, [S](evidence/live-708/live_708_standby_merge_probe.json) 예약대기·병합 1차·재계산, [M](evidence/live-708/live_708_merge_second_probe.json) 병합 2차, [D](evidence/live-708/live_708_seat_designated_probe.json) 좌석 지정, [H](evidence/live-708/live_708_history_probe.json) 3개월 이내 과거 승차권 및 후속 조회, [E](evidence/live-708/live_708_account_deep_probe.json) 여행상품·대리수령·카드 식별자 재조사, [C](evidence/live-708/live_708_discount_schedule_probe.json) N카드 상품 코드 조회. [상세 JSON](evidence/live-708/live_708_method_matrix.json)에 메서드별 호출과 근거 파일이 있습니다.

임시 예약은 일반·예약대기·좌석 지정·환승·병합·공항버스로 확인했고, 생성된 홀드는 모두 취소했습니다. 각 예약 배치의 최종 예약 이력은 `P100`·0건입니다. 과거 승차권 조회는 3개월 이내 기간으로 바로잡자 첫 기간에 7개 예약·8장 승차권을 받았습니다. [일곱 기간의 추가 조회](evidence/live-708/live_708_history_scan.json)에서는 승차권 126장을 파싱했고 종류 코드는 모두 `72`였습니다. 이 코드의 업무 의미를 확정하거나 모든 과거 연도를 조회한 것은 아닙니다. 실제 계정의 여행상품 예약 1건은 이미 고객 취소 상태였으나 상세 조회는 성공했습니다. 과거 승차권의 대리수령 명세 2건은 모두 회수 가능 플래그 `N`이었습니다. 결제·환불·실물 좌석 QR을 쓰는 체크인은 이번에 실행하지 않았습니다.

| 공개 메서드 | 7.0.8 판정 | 관측 결과 코드 | 근거 또는 미확인 조건 |
|---|---|---|---|
| `close` | 로컬 메서드 | — | 로컬 테스트 |
| `login` | 실서버 응답 파싱 | — | A, R, S, M, D |
| `clear_session` | 로컬 메서드 | — | 로컬 테스트 |
| `logout` | 실서버 응답 파싱 | — | A, R, S, M, D |
| `get_seat_cars` | 실서버 응답 파싱 | `IRG000000` | P, A, D |
| `get_seat_inventory` | 실서버 응답 파싱 | `IRG000000` | A, D |
| `get_limousine_schedules` | 실서버 응답 파싱 | `IRG000000`, `WRG000000` | P, R |
| `get_limousine_seat_inventory` | 실서버 응답 파싱 | `IRG000000` | R |
| `get_service_status` | 실서버 응답 파싱 | `S100` | P |
| `get_cart_list` | 실서버 응답 파싱 | — | A, R |
| `get_deposit_banks` | 실서버 응답 파싱 | `API.I00000` | A |
| `get_delay_discount_tickets` | 실서버 응답 파싱 | — | A |
| `get_discount_coupons` | 실서버 응답 파싱 | `WRG000000` | A |
| `get_korail_point_summary` | 실서버 응답 파싱 | `IRZ000001` | A |
| `get_mileage_history` | 실서버 응답 파싱 | `IRZ000001` | A |
| `get_discount_card_usage_history` | 7.0.8 미실행 | — | 보유 N카드 없음 |
| `get_discount_card_schedule` | 서버 거절 확인 | `EAZ000028` | C; 상품 코드로 조회했으나 보유 N카드가 없어 성공 경로 미확인 |
| `get_pass_available_dates` | 실서버 응답 파싱 | — | A |
| `get_pass_schedule` | 실서버 응답 파싱 | — | A |
| `get_trip_menu` | 실서버 응답 파싱 | `API.I00000` | A |
| `get_pass_menu` | 실서버 응답 파싱 | — | A |
| `get_crew_request_list` | 실서버 응답 파싱 | — | P |
| `get_commuter_kind_menu` | 실서버 응답 파싱 | `IRZ000001` | A |
| `get_product_reservations` | 실서버 응답 파싱 | — | A |
| `get_product_detail` | 실서버 응답 파싱 | — | E; 이미 취소된 여행상품 1건의 상세 |
| `cancel_product_reservation` | 7.0.8 미실행 | — | 활성 여행상품 예약 없음; 확인된 1건은 이미 취소됨 |
| `get_ticket_receipt` | 실서버 응답 파싱 | `IRT000000` | H |
| `get_reservation_history` | 실서버 응답 파싱 | `IRR000001`, `P100` | A, R, S, M, D |
| `get_free_seat_car_info` | 실서버 응답 파싱 | `IRZ000005` | P |
| `get_guide_seat_condition` | 서버 거절 확인 | `MRR800011`, `P058` | P, A; 인증 후에도 `FAIL` |
| `get_seat_assignment_schedule` | 실서버 응답 파싱 | `WRG000000` | A |
| `get_merge_seats_inquiry` | 실서버 응답 파싱 | — | A, S, M |
| `get_multi_child_discount_targets` | 서버 거절 확인 | `WRC800029` | A |
| `get_customer_trip_info` | 실서버 응답 파싱 | `IRS100002` | A |
| `get_maas_service_details` | 실서버 응답 파싱 | — | P, A |
| `get_trip_change_dates` | 실서버 응답 파싱 | `API.I00000` | A |
| `get_commuter_info` | 서버 거절 확인 | `ERR000100` | A |
| `get_price_fare_quote` | 실서버 응답 파싱 | `API.I00000` | P |
| `get_delivery_recipient` | 서버 거절 확인 | `IRZ000005` | H; 일반 과거 승차권으로는 수령자 없음 |
| `check_ticket_duplication` | 실서버 응답 파싱 | — | R |
| `get_pbp_acceptance_specifications` | 실서버 응답 파싱 | `MRR800018` | H, E; 대상 2건의 명세 파싱 |
| `retrieve_delivered_ticket` | 7.0.8 미실행 | — | 과거 대리수령 명세 2건 모두 회수 가능 플래그 `N` |
| `get_original_ticket_inquiry` | 실서버 응답 파싱 | `IRT000001` | H |
| `get_self_seat_change_info` | 서버 거절 확인 | `WRT800176` | H; 운행 시간 밖 |
| `get_recent_delivery_history` | 실서버 응답 파싱 | — | A |
| `get_ticket_reservation_detail` | 실서버 응답 파싱 | `IRZ000001` | R |
| `get_refund_commission` | 서버 거절 확인 | `WRT200022` | H; 승차일 경과 |
| `get_refund_ticket_detail` | 실서버 응답 파싱 | `IRZ000001` | H |
| `get_delay_certificate` | 실서버 응답 파싱 | `IAZ000006` | H |
| `get_delay_return_receipt` | 서버 거절 확인 | `IRZ000005` | H; 반환 자료 없음 |
| `get_self_checkin_info` | 서버 거절 확인 | `WRZ000001` | H; 체크인 정보 없음 |
| `check_self_checkin_seat` | 7.0.8 미실행 | — | 실제 좌석 QR 및 해당 승차권 없음 |
| `register_self_checkin` | 7.0.8 미실행 | — | 실제 좌석 QR 및 해당 승차권 없음 |
| `cancel_self_checkin` | 7.0.8 미실행 | — | 체크인한 승차권 없음 |
| `get_common_code` | 실서버 응답 파싱 | `API.I00000` | P |
| `get_app_data` | 실서버 응답 파싱 | — | P |
| `get_notice` | 실서버 응답 파싱 | — | P |
| `get_uuid` | 실서버 응답 파싱 | — | P |
| `get_maas_menu_list` | 실서버 응답 파싱 | `API.I00000` | P |
| `get_maas_station_data` | 실서버 응답 파싱 | — | P |
| `get_station_info` | 실서버 응답 파싱 | — | P |
| `get_station_data` | 실서버 응답 파싱 | — | P |
| `get_train_calendar` | 실서버 응답 파싱 | `API.I00000` | P |
| `search_trains` | 실서버 응답 파싱 | `IRG000000` | P, A, R, S, M, D |
| `search_transfer_trains` | 실서버 응답 파싱 | `IRG000000` | P, R |
| `search_trains_with_transfer_fallback` | 실서버 응답 파싱 | `IRG000000` | P |
| `get_train_schedule` | 실서버 응답 파싱 | `IRZ000001` | P |
| `get_transfer_stations` | 실서버 응답 파싱 | `IRZ000001` | P |
| `get_ticket_list` | 실서버 응답 파싱 | `IRG000000`, `WRT100101`, `WRT300005` | A, H; 과거 조회의 처음 실패는 3개월 초과 기간 때문 |
| `reserve` | 실서버 응답 파싱 | `IRR000014`, `IRR000018` | R, S, M, D |
| `confirm_standby_hold` | 실서버 응답 파싱 | `IRZ000003` | S |
| `reserve_transfer` | 실서버 응답 파싱 | `IRR000018` | R |
| `reserve_merge` | 실서버 응답 파싱 | `ERI411321`, `IRR000018` | S, M; 첫 열차 매진, 다른 열차 성공 |
| `reserve_limousine` | 실서버 응답 파싱 | `IRR000018` | R |
| `cancel_unpaid_hold` | 실서버 응답 파싱 | `IRG000000` | R, S, M, D |
| `pay_with_card` | 7.0.8 미실행 | — | 실제 카드 결제 수단 없음; 금전 청구 |
| `refund` | 7.0.8 미실행 | — | 환불할 발권 승차권 없음 |
| `verify_station_ticket_refund` | 7.0.8 미실행 | — | 역 발권 승차권 없음 |
| `execute_station_ticket_refund` | 7.0.8 미실행 | — | 역 발권 승차권 없음 |
| `add_to_cart` | 실서버 응답 파싱 | `IRZ000002` | R |
| `register_discount_card` | 7.0.8 미실행 | — | 실구매/발권으로 이어지는 N카드 등록 |
| `extend_discount_card` | 7.0.8 미실행 | — | 보유 N카드 없음 |
| `reserve_with_discount_card` | 7.0.8 미실행 | — | 보유 N카드 없음 |
| `recalculate_price` | 서버 거절 확인 | `ERR930202`, `WZZ000001` | R, S; `000`은 `WZZ000001`, 빈 코드는 `ERR930202` |

현재 계정의 과거 발권 승차권으로 영수증·원표·환불 상세·지연확인증 조회를 검증했고 취소된 여행상품의 상세도 읽었습니다. 현재 유효한 승차권·활성 여행상품 예약·보유 N카드가 없어 실제 환불 수수료, 여행상품 취소, N카드 이용 성공은 검증하지 못했습니다. 좌석 QR 체크인과 대리수령 회수는 유효한 현장·회수 가능 상태가 필요합니다. 7.0.8의 새 요청 계약과 별도로, 이 조건을 채운 뒤 해당 성공 경로를 다시 확인해야 합니다.
