# 변경 이력

## [Unreleased] — 첫 PyPI 배포 준비

이 판의 PyPI·TestPyPI 업로드, Git 태그, 릴리스는 아직 만들지 않았습니다. v1.0.0~v1.1.1 은 GitHub 릴리스로 공개했으며 당시 기록은
[v1.1.1 태그의 CHANGELOG](https://github.com/yakisoba0728/korail-mobile-api/blob/v1.1.1/CHANGELOG.md)에 있습니다. 배포 버전은
`src/korail_mobile_api/__init__.py`의 `__version__`에서만 결정합니다.

### v1.1.1 과 호환되지 않는 변경

v1.1.1 에서 올리는 코드는 아래를 확인하십시오. 모델은 위치 순서가 많이 바뀌었으니 키워드 인자로 만드십시오.

**변경 메서드**

- 변경 메서드 12개의 사전 동의(`consent=`)와 미리보기(`MutationPreview`)를 없앴습니다. 이제 호출하면 바로 서버로 전송되며, `consent=` 를
  넘기면 `TypeError` 입니다. 동의를 받던 13번째 메서드 `pay_with_fake_card` 는 메서드째 없앴습니다.
- `cancel_unpaid_hold` 는 기본으로 확인(`ReservationCancel`)과 취소(`ReservationCancelChk`) 두 요청을 보냅니다. v1.1.1 은 취소 하나였습니다.

**메서드·공개 이름·모듈**

- 메서드 4개를 없앴습니다: `get_gift_ticket_list`, `get_limousine_schedule_view`, `get_platform_numbers`, `pay_with_fake_card`.
- 최상위 공개 이름이 222개에서 214개가 됐습니다(36개 제거, 28개 추가). 선물 승차권·공항버스 일정 보기·승강장 번호·사전 동의 관련 이름과
  `SELF_SEAT_CHANGE_ROOM_CLASS_CODES`·`inquiry_action` 18개는 삭제했고, 상수·저수준 대기열·헬퍼 18개는 하위 모듈(`constants`, `config`,
  `errors`, `netfunnel`, `read_payloads`)에만 남겼습니다.
- 하위 모듈 `consent`, `redaction`, `safety` 를 없앴고, `live` 에서 `live_enabled`, `read_credentials_from_env`,
  `run_live_smoke_from_env` 를 없앴습니다.

**서명·반환 타입**

- `get_crew_request_list(query_division_code)` → `get_crew_request_list(*, timestamp_ms=None)`
- `get_station_info(device)` 인자 제거
- `refund` 의 `return_times_division_code` 제거
- `reserve_merge` 의 둘째 인자 이름 `legs` → `merge_rows`
- `get_ticket_list` 의 `page_no` 기본값 0 → 1. `mode` 는 1·2 밖의 값도 거르지 않고 보냅니다(앱 호출 리터럴이 보호돼 있음).
- `get_ticket_list`·`refund`·`add_to_cart` 는 전용 응답 모델을 돌려줍니다. 모두 `BaseKorailResponse` 하위 형입니다.

**설정**

- `KorailConfig` 의 `enable_dynapath`·`live_env_var` 를 없앴습니다. DynaPath 는 합성 기기값으로 기본 켜짐이고(끄려면
  `disable_dynapath=True`), 비활성 `DynapathConfig` 를 직접 넘기면 `ValueError` 입니다. `netfunnel_enabled` 기본값은 `True` 입니다.
- 기기 기본값: 화면 1080×2400 → 1440×3120, `android_sdk_int` 35 → 37.
- v1.1.1 의 `base_url` 출처 검사(`safety`)는 없어졌습니다. 신뢰하지 않는 주소를 넣지 마십시오.

**모델**

- 필드 15개를 없앴습니다: `AppDataResponse.for_seat_intg`·`airport_bus_msg`, `DelayDiscountTicket.usable_until_date`,
  `DiscountCardScheduleTrain.station_string_info`, `DiscountCardSection.section_sequence`, `DiscountCoupon.discount_values`,
  `MileageHistoryResponse.rail_now_saved_point_1`, `PriceFareLeg.standing_train_classification_code`,
  `RefundTicketDetailResponse.mileage_save_flag`, `TrainSearchContinuation.page_count`,
  `TrainSearchMetadata.merge_reservation_available_flag`, `TripChangeDateResponse.trip_change_date`,
  `TripMenuContent.content_type`, 그리고 설정 필드 두 개(위).
- `DiscountCoupon.discount_values` 는 필드별 속성(`discount_rate_amount_division_code`, `weekday_fare_discount`,
  `weekday_price_discount`, `weekend_fare_discount`, `weekend_price_discount`)으로 나눴습니다. 온 값만 모은 튜플은 어느 필드의 값인지 알 수
  없었습니다.
- 정수였던 필드가 문자열이 됐습니다: `StationInfoResponse.count`, `SeatInventoryResponse.layout_type`, `CartItem.ticket_count`,
  `TicketDuplicationCheckResponse.reservation_count`, `KorailStation.popup_type`, `PassMenuItem.after_day`,
  `TrainScheduleStop.actual_arrival_delay_count`. `SeatInventoryResponse.remaining_count`·`total_count` 의 기본값은 0 → `None` 입니다.
- 새 필수 필드: `PbpAcceptanceJourney.member_card_no`, `PriceFareLeg.train_class_code`, `TicketReceipt` 의
  `printed_discount_kind_code`·`ticket_kind_name`·`train_group_code`. `TicketReceipt`·`ReceiptPayment`·PBP 모델 등은 기본값 없는 필드가
  늘었고, 모델 31개의 위치 순서가 바뀌었습니다.
- `KorailAuthContinuationRequired` 에서 `post_data` 를 없앴습니다.

**예외와 입력 검증**

- 전송 전 입력 오류 상당수가 `ValueError`·`TypeError` 에서 `KorailProtocolError` 로 바뀌었습니다(예: `KorailPassengerCounts(adult=10)`,
  `KorailSeatAssignment(0, "1")`, `get_seat_cars(..., passenger_count=0)`, `get_maas_station_data("")`).
- 성공 봉투에 붙은 `WRC000288` 은 더 이상 예외가 아닙니다. 7.0.6 앱에는 이 분기가 없습니다.
- 닫힌 클라이언트로 호출하면 `RuntimeError` 대신 `KorailProtocolError` 이며 요청은 나가지 않습니다.
- `input_flag` 를 생략하면 숫자만도 이메일도 아닌 로그인 ID(예: 하이픈이 든 전화번호)는 앱처럼 보내지 않고 `KorailProtocolError` 입니다.

### 추가

- 메서드 4개: `cancel_product_reservation`, `reserve_limousine`, `verify_station_ticket_refund`, `execute_station_ticket_refund`.
- 기존 메서드의 키워드 인자(예: `seat_attribute_code`, `use_special_schedule`, `peak_season`, `check_first`, `commission`, `txt_index`)와
  공개 모델 28개(예: `ProductCancelResponse`).
- `ReservationHoldResponse.payable`: 앱은 예약대기 홀드를 결제하지 않고 대기 옵션만 저장합니다. `reserve`·`reserve_transfer` 가 STANDBY
  홀드에 `False` 를 넣고 `pay_with_card` 는 전송 전에 거절합니다. 병합 첫 홀드는 앱의 병합 화면에서도 결제할 수 있어 `True` 입니다.
- 77개 공개 메서드의 합성 HTTP 스모크, 오프라인 패키징 검사, CI 의 최소 의존성 작업과 `mypy --strict`. CI 에는 업로드 작업이 없습니다.

### 수정

- 환불 결과의 `stlList` 와 정산수단 코드, 입금 은행 행, 고객 여행 정보의 `mainList` 를 필수로 읽습니다.
  최근 대리수령 이력은 2026-09-24 실서버 응답에 `chgePbpRsvNo` 가 없어 선택으로 둡니다.
- 응답 거절·파싱 실패 때 `.raw` 에 전체 응답이 남습니다.
- DynaPath 토큰의 `rt` 에 앱 SDK 처럼 요청 간 시간차(최근 5개, 첫 값은 앱 시작 시각과의 차)를 싣습니다. v1.1.1 은 `rt=0` 고정값이었습니다.
- 봉투의 JSON 정수를 전송 계층과 모든 파서가 같은 규칙으로 문자열로 읽습니다. 선택 문자열 필드의 JSON 정수도 문자열로 읽고, 필수 정수는
  따옴표 안의 앞 `-` 를 받습니다(kotlinx 와 같음).
- 전송 전 검사를 더했습니다: 카드번호 13~16자리, 할부 1~2자리 숫자, 카드 비밀번호·인증값은 숫자. 환승 구간은 서로 다른 열차이고 탑승
  순서여야 하며, 병합 행은 첫 홀드와 운행일이 같아야 합니다. 공항버스 예약에 같은 좌석번호를 두 번 넣으면 거절합니다.
- 대기열 응답의 노드가 허용 범위 밖이면 그 노드는 무시하고 정문으로 진행·반납합니다. 대기열 반납 실패는 API 쪽 원래 예외를 가리지 않고, NetFunnel
  생성이 실패하면 먼저 만든 HTTP 클라이언트를 닫습니다.
- 로그인 응답에 경로만 다른 `JSESSIONID` 가 둘 이상이면 httpx 예외로 로그인이 끝나지 않습니다.
- 두 좌석 조회가 좌석속성 명시값을 같은 규칙으로 처리합니다. 순서 있는 폼도 `None`·`bool` 을 매핑 폼과 같게 인코딩합니다. 원표 참조는 튜플뿐
  아니라 목록도 받습니다.
- `mypy --strict`, `pyright`, `ruff` 가 모두 통과하며 CI 가 셋을 모두 실행합니다.

### 검증 한계

- 오프라인 검증은 앱의 보호된 리터럴이나 운영 서버 수용을 증명하지 않습니다.
- 2026-09-24 에 이 판으로 실서버 조회만 다시 확인했습니다. 로그인·열차 조회·대기열·공항버스 조회(`rt` 가 든 DynaPath 토큰 포함)는 이전과
  같은 결과였습니다. 예약·결제·환불은 이번에 다시 실행하지 않았습니다.
- 일반실 매진·입석 가능 행의 입석 전용 홀드는 보내지 않습니다. 앱의 입석 판정은 보호된 운행중지·대기·병합 판정을 먼저 거치므로
  (TrainScheduleOutTrainInfo.java:2810-2885) 라이브러리가 같은 행을 가려낼 수 없습니다. 입석+좌석은 `MERGE_STANDING` 입니다.
- N카드 6개 기능의 미검증 상태와 기존 미지원 기능 범위를 유지합니다.
