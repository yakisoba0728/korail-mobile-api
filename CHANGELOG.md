# 변경 이력

## [Unreleased]

이 판의 Git 태그와 릴리스는 아직 만들지 않았고, PyPI 에는 올리지 않습니다. v1.0.0~v1.1.1 은 GitHub 릴리스로 공개했으며 당시 기록은
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
- 최상위 공개 이름이 222개에서 223개가 됐습니다(36개 제거, 37개 추가). 선물 승차권·공항버스 일정 보기·승강장 번호·사전 동의 관련 이름과
  `SELF_SEAT_CHANGE_ROOM_CLASS_CODES`·`inquiry_action` 18개는 삭제했고, 상수·저수준 대기열·헬퍼 18개는 하위 모듈(`constants`, `config`,
  `errors`, `netfunnel`, `read_payloads`)에만 남겼습니다.
- 하위 모듈 `consent`, `redaction`, `safety` 를 없앴고, `live` 에서 `live_enabled`, `read_credentials_from_env`,
  `run_live_smoke_from_env` 를 없앴습니다.

**서명·반환 타입**

- `get_crew_request_list(query_division_code)` → `get_crew_request_list(*, timestamp_ms=None)`
- `get_station_info(device)` 인자 제거
- `refund` 의 `return_times_division_code` 제거. `commission`(`get_refund_commission` 의 응답)은 필수 키워드입니다. 앱은 두 환불
  화면 모두 수수료 조회가 성공해야 환불을 보냅니다. `settle_mileage=True` 는 사용 가능 마일리지가 수수료 이상일 때만 보내며 아니면
  `KorailProtocolError` 입니다.
- `reserve_merge` 의 둘째 인자 이름 `legs` → `merge_rows`
- `get_ticket_receipt` 의 식별값은 키워드로만 받습니다. 비슷한 `OriginalTicketReference` 와 날짜·창구번호 순서가 반대라 위치 인자로 넘기면
  서로 바뀌었습니다.
- `get_ticket_list` 의 `page_no` 기본값 0 → 1. `mode` 는 1·2 밖의 값도 거르지 않고 보냅니다(앱 호출 리터럴이 보호돼 있음).
- `get_ticket_list`·`refund`·`add_to_cart` 는 전용 응답 모델을 돌려줍니다. 모두 `BaseKorailResponse` 하위 형입니다.

**설정**

- `KorailConfig` 의 `enable_dynapath`·`live_env_var` 를 없앴습니다. DynaPath 는 합성 기기값으로 기본 켜짐이고(끄려면
  `disable_dynapath=True`), 비활성 `DynapathConfig` 를 직접 넘기면 `ValueError` 입니다. `netfunnel_enabled` 기본값은 `True` 입니다.
- 기기 기본값: 화면 1080×2400 → 1440×3120, `android_sdk_int` 35 → 37, 모델 `Android` → `SM-S948N`, OS `15` → `17`. 모두 같은
  실기기 표본에서 가져와 DynaPath 토큰과 대기열 User-Agent 가 한 기기를 가리킵니다.
- `user_agent` 기본값이 Dalvik 형식에서 앱의 `korailtalk` 로 바뀌었고, 대기열 요청의 User-Agent 는 새 `netfunnel_user_agent`(Dalvik
  형식)로 나눴습니다. `live.build_config_from_env` 의 `KORAIL_USER_AGENT` 는 API 값만 바꾸며, 기기 기반 대기열 값은
  `KORAIL_NETFUNNEL_USER_AGENT` 입니다. 이 값을 주지 않으면 `KORAIL_ANDROID_BUILD_ID`(Build.ID)가 필수입니다.
- `constants.build_dalvik_user_agent` 에 필수 키워드 `build_id` 가 생겼습니다.
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
- `SeatCar.car_no`·`remaining_seat_count` 와 `SeatWindow` 의 두 비율은 `None` 일 수 있습니다. 앱 DTO 에서 선택 String 이라 빠지면
  앱 기본값 "" 이 되는 값입니다(TrainResearchOutCarInfo.java:59-85, TResidualSeatsResearchOutWindow.java:51-56).

**예외와 입력 검증**

- 전송 전 입력 오류 상당수가 `ValueError`·`TypeError` 에서 `KorailProtocolError` 로 바뀌었습니다(예: `KorailPassengerCounts(adult=10)`,
  `KorailSeatAssignment(0, "1")`, `get_seat_cars(..., passenger_count=0)`, `get_maas_station_data("")`).
- 성공 봉투에 붙은 `WRC000288` 은 더 이상 예외가 아닙니다. 7.0.6 앱에는 이 분기가 없습니다.
- 닫힌 클라이언트로 호출하면 `RuntimeError` 대신 `KorailProtocolError` 이며 요청은 나가지 않습니다.
- `input_flag` 를 생략하면 숫자만도 이메일도 아닌 로그인 ID(예: 하이픈이 든 전화번호)는 앱처럼 보내지 않고 `KorailProtocolError` 입니다.

### 추가

- 메서드 4개: `cancel_product_reservation`, `reserve_limousine`, `verify_station_ticket_refund`, `execute_station_ticket_refund`.
- 앱에만 있던 경로의 메서드 7개.
  - `get_delay_certificate`·`get_delay_return_receipt`: 지난 승차권의 지연확인증과 지연료 반환 영수증(NetworkApi.java:347-357).
  - `get_self_checkin_info`·`check_self_checkin_seat`·`register_self_checkin`·`cancel_self_checkin`: 자유석 셀프 체크인
    (NetworkApi.java:288-290,674-684). 입력은 `get_refund_ticket_detail` 의 결과이며 좌석 확인·등록은 좌석 테이블 QR 이 필요합니다.
  - `retrieve_delivered_ticket`: 전달한 승차권 회수(NetworkApi.java:642-644). 입력은 `get_pbp_acceptance_specifications` 의
    승차권입니다.
  - 여행상품 검색(`/ebizcom/gdLstDtl.do`)은 서버가 보호된 `funcDvCd` 를 요구해 공개 API 에 넣지 않고 `_travel_search_unsupported.py` 에
    기록용으로 남겼습니다.
- 기존 메서드의 키워드 인자(예: `seat_attribute_code`, `use_special_schedule`, `peak_season`, `check_first`, `commission`, `txt_index`)와
  공개 모델 28개(예: `ProductCancelResponse`).
- `TrainSearchQuery` 의 `teenager_passengers`·`infant_passengers`·`guide_dog_passengers`: 앱처럼 청소년·안내견은 어른 칸, 유아는 어린이
  칸에 더해 조회합니다(TrainScheduleViewModel.java:280-306,3050-3075).
- `ReservationHoldResponse.payable`: 앱은 예약대기 홀드를 결제하지 않고 대기 옵션만 저장합니다. `reserve`·`reserve_transfer` 가 STANDBY
  홀드에 `False` 를 넣고 `pay_with_card` 는 전송 전에 거절합니다. 병합 첫 홀드는 앱의 병합 화면에서도 결제할 수 있어 `True` 입니다.
- 84개 공개 메서드의 합성 HTTP 스모크, 오프라인 패키징 검사, CI 의 최소 의존성 작업과 `mypy --strict`. CI 에는 업로드 작업이 없습니다.

### 수정

- 환불 결과의 `stlList` 와 정산수단 코드, 입금 은행 행, 고객 여행 정보의 `mainList`, 최근 대리수령 이력의 `acepList`(null 은 빈 목록)를
  필수로 읽습니다. 최근 대리수령 이력의 `chgePbpRsvNo` 는 2026-09-24 실서버 응답에 없어 선택으로 둡니다.
- 좌석 재고·호차 목록·역 목록에서 필수로 잘못 읽던 선택 필드 18개가 빠져도 응답을 거절하지 않고 앱 기본값처럼 읽습니다(문자열은 "",
  숫자는 `None`). 다른 선택 필드는 지금처럼 빠지면 `None` 입니다. 값이 있는데 null 이거나 타입이 틀리면 앱의 Json 설정이
  보호돼 있어 지금처럼 거절합니다. 인증번호(`mutMrkVrfCd`)는 다음 요청에 보내야 하므로 계속 필수입니다.
- 로그인 응답의 회원카드·고객번호가 JSON 정수여도 세션에 문자열로 남깁니다. 다른 String 필드와 같은 규칙입니다.
- 대기열 응답 코드를 SDK 의 `Integer.parseInt` 처럼 읽습니다. `0200`·`+200` 도 200 이고 앞의 0 은 몇 개든 받습니다. 보충 평면 숫자와
  int32 밖의 값은 `KorailNetFunnelError` 입니다.
- 요금 재계산 폼을 앱의 Retrofit 순서대로 보냅니다. 공통 필드와 선택 스칼라 4개 다음에 `psg_tp_dv_cd`, `psrm_cl_cd`, `dcnt_knd_cd1`,
  `hidDscpNo`, `hidDcntKndCd`, `hidFmlyNo` 목록이 옵니다(NetworkApi.java:584).
- 다른 요청도 앱 DTO 의 선언 순서대로 보냅니다. 앱은 DTO 를 선언 순서대로 평탄화합니다(NetworkService.java:15335-15392).
  - 예약(직통·환승·병합·공항버스·N카드): 승객 행 → 여정 행(객실 코드는 각 여정의 끝) → 좌석 쌍 → 중간역 순입니다
    (TicketReservationIn.java:80).
  - 환불·수수료 조회: 공통 필드(Device·Version·Key·lang)를 맨 뒤에 둡니다(RefundTicketIn.java:66, RefundCommissionIn.java:59).
  - 호차 조회·승차권 목록·병합 조회: 필드 순서를 DTO 에 맞췄습니다. `lang` 을 설정하면 모든 요청에서 Key 뒤에 옵니다.
- 응답 거절·파싱 실패 때 `.raw` 에 전체 응답이 남습니다. 변경 응답 파서를 직접 불러도 같고 부분 원문은 `.parser_raw` 에 남습니다.
- DynaPath 토큰의 `rt` 에 앱 SDK 처럼 요청 간 시간차(최근 5개, 첫 값은 앱 시작 시각과의 차)를 싣습니다. v1.1.1 은 `rt=0` 고정값이었습니다.
- API 요청 헤더를 앱과 맞췄습니다. 앱은 보호된 헤더 하나를 붙이는데, 보호 방식이 4바이트 키 반복 XOR 이라 같은 앱의 WebView 접미사
  평문으로 방식을 확인한 뒤 암호문 관계만으로 `User-Agent: korailtalk` 임을 확인했습니다(`constants.KORAIL_API_USER_AGENT`). APK 의 OkHttp
  기본 헤더에 맞춰 `Connection: Keep-Alive`, `Accept-Encoding: gzip` 을 보내고 `Accept` 는 보내지 않습니다.
- `recalculate_price(add_to_cart=True)` 로 앱처럼 재계산 성공 뒤 같은 PNR 을 장바구니에 추가할 수 있습니다(PayViewModel.java:14428-14436).
  결과는 새 필드 `ReservationHoldResponse.cart_addition` 에 담기며 FAIL 이어도 예외를 내지 않습니다. 2026-09-25 실서버: 재계산 21,500→15,000원,
  추가 SUCC/IRZ000002, 장바구니에 15,000원 행, 홀드 취소 뒤 장바구니 비움.
- `PriceRecalculationRequest.for_hold(hold, codes)` 는 앱처럼 홀드의 첫 여정 좌석마다 한 행을 만들고(유형·객실·현재 할인 코드 복사,
  `dcnt_reld_no` → `hidDscpNo`) 요청 코드 수가 좌석 수와 다르면 거절합니다(PayViewModel.java:5518,16856-16863,17469). 좌석 값은
  문자열과 JSON 정수만 받고 bool·객체 등은 거절합니다.
- 운임 조회(`get_price_fare_quote`)는 앱처럼 `gdNo` 칸을 늘 보냅니다. 상품번호가 없으면 빈 값이고 2구간은 구분자만 남습니다
  (PrcFareInItem.java:109, NetworkService.java:9895-9902). 2026-09-25 실서버에서 1·2구간 모두 이전과 같은 운임을 받았습니다.
- 대기열 요청도 앱과 맞췄습니다. SDK 는 User-Agent 를 넣지 않아 안드로이드 기본값이 나가므로 `korailtalk` 이 아니라 AOSP
  `RuntimeInit.getDefaultUserAgent` 형식 그대로 `Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)` 을 보냅니다.
  v1.1.1 에는 `Build/…` 가 빠져 있었습니다. SDK 는 GET 으로 부르지만 `setDoOutput(true)`(Client.java:257) 때문에 안드로이드
  HttpURLConnection 이 빈 본문 POST 로 바꾸므로 대기열 요청을 `POST`(인자는 URL, `Content-Length: 0`)로 보내고, 같은 구현이 붙이는
  `Content-Type: application/x-www-form-urlencoded`, `Connection: Keep-Alive`, `Accept-Encoding: gzip` 을 싣고 `Accept` 는 뺐습니다.
- 봉투의 JSON 정수를 전송 계층과 모든 파서가 같은 규칙으로 문자열로 읽습니다. 선택 문자열 필드의 JSON 정수도 문자열로 읽고, 필수 정수는
  따옴표 안의 앞 `-` 를 받습니다(kotlinx 와 같음).
- 전송 전 검사를 더했습니다: 카드번호 13~16자리, 할부 1~2자리 숫자, 카드 비밀번호·인증값은 숫자, 결제할 금액이 0원인 홀드의 카드 결제
  거절(앱은 0원이면 카드 요청을 만들지 않습니다, PayViewModel.java:15572), 마일리지로 환불 수수료를 낼 때 수수료 응답과 사용 가능
  마일리지 ≥ 수수료 요구(MyTicketDetailViewModel.java:1811-1823). 환승 구간은 서로 다른 열차이고 탑승
  순서여야 하며, 병합 행은 첫 홀드와 운행일이 같아야 합니다. 공항버스 예약에 같은 좌석번호를 두 번 넣으면 거절합니다.
- 대기열 응답의 노드가 허용 범위 밖이면 그 노드는 무시하고 정문으로 진행·반납합니다. 대기열 반납 실패는 API 쪽 원래 예외를 가리지 않고, NetFunnel
  생성이 실패하면 먼저 만든 HTTP 클라이언트를 닫습니다.
- 로그인 응답에 경로만 다른 `JSESSIONID` 가 둘 이상이면 httpx 예외로 로그인이 끝나지 않습니다.
- 두 좌석 조회가 좌석속성 명시값을 같은 규칙으로 처리합니다. 순서 있는 폼도 `None`·`bool` 을 매핑 폼과 같게 인코딩합니다. 원표 참조는 튜플뿐
  아니라 목록도 받습니다.
- `mypy --strict`, `pyright`, `ruff` 가 모두 통과하며 CI 가 셋을 모두 실행합니다.

### 검증 한계

- 오프라인 검증은 앱의 보호된 리터럴이나 운영 서버 수용을 증명하지 않습니다.
- 2026-09-24 에 이 판으로 실서버 조회만 다시 확인했습니다. 로그인·열차 조회·대기열·공항버스 조회 등 54건이 `rt` 가 든 DynaPath 토큰과
  `korailtalk` User-Agent 로 이전과 같은 결과였습니다. 예약·결제·환불은 이번에 다시 실행하지 않았습니다.
- 2026-09-25 에 자유석 호차 조회를 열차 203편으로 확인했습니다. 자유석 칸이 있는 183편은 호차 문구를, 없는 20편은 IRZ000005 를
  돌려줬고 조회 행의 `free_car_count` 와 모두 일치했습니다.
- 2026-09-25 에 정기권 스케줄(일반정기권·기간자유형 코드), 원표 조회(인쇄완료 승차권), 대리수령 인수 명세(대상 승차권 6장), 자율 좌석변경
  정보(운행 중 열차), 예약대기 옵션 저장(대기 홀드 → 옵션 저장 → 취소, 최종 P100)을 실서버에서 확인했습니다.
- 2026-09-25 에 바뀐 대기열 요청(POST·새 User-Agent·새 기기 기본값)으로 로그인, 열차 조회, 예약 목록, 로그아웃을 실서버에서 확인했습니다.
- 2026-09-25 에 같은 코드로 실결제·환불을 다시 했습니다. 서울→영등포 KTX 운임 조회 7,500원, 홀드 7,500원, 결제 IRT000000(7,500원),
  수수료 조회 환불 7,500원·수수료 0원, 환불 IRT200277 이었고 끝난 뒤 승차권·예약이 없었습니다.
- 2026-09-25 에 요금 재계산을 다시 확인했습니다(결제 없이 모두 취소). 무변경은 ERR930202, 평일 할인 변경은 SUCC/IRZ000008 로
  21,500→15,000원, 토요일은 같은 SUCC/IRZ000008 인데 금액이 그대로였습니다. 운임 조회는 표시용 기준 운임으로, 홀드의 h_tot_prc 와 같고
  정산액은 좌석 할인만큼 낮을 수 있었습니다(성인 2명은 정확히 두 배). 환승 두 구간 조회는 네 행을 돌려줬습니다.
- 2026-09-25 에 응답 읽기·재계산 순서를 고친 뒤 다시 확인했습니다. 로그인 식별자는 문자열, 최근 대리수령 이력은 `acepList` 가 있고
  `chgePbpRsvNo` 가 없었으며, 역 281개·호차 13개·좌석 56석과 창 6개를 빠진 값 없이 읽었습니다. 새 순서의 재계산은 SUCC/IRZ000008 로
  21,500→15,000원이었고 홀드는 결제 없이 취소했습니다.
- 2026-09-25 에 바뀐 요청 순서로 다시 확인했습니다(모두 이전과 같은 결과). 승차권 목록, 호차 13개·좌석 56석 조회, 좌석지정 홀드
  21,500원(지정 호차), 환승 홀드 2구간 48,100원, 공항버스 홀드 16,000원은 모두 취소했습니다. 서울→영등포 KTX 를 7,500원
  결제(IRT000000)한 뒤 수수료 조회 7,500원·수수료 0원, 환불 IRT200277 이었고 끝난 뒤 승차권·홀드가 없었습니다.
- 2026-09-25 에 새 조회를 지난 승차권으로 확인했습니다. 지연된 승차권 2장의 지연확인증은 SUCC/IAZ000006 과 행 1개였고 행에 `runDt` 가
  없어 선택으로 읽습니다. 지연되지 않은 승차권은 WRT400456, 지연료 반환 영수증은 IRZ000005, 셀프 체크인 정보는 WRZ000001 이었습니다.
  여행상품 검색은 WRR000100(입력값 오류(funcDvCd))이었습니다. 셀프 체크인 등록·좌석 확인·취소와 승차권 회수는 보내지 않았습니다.
- 일반실 매진·입석 가능 행의 입석 전용 홀드는 보내지 않습니다. 앱의 입석 판정은 보호된 운행중지·대기·병합 판정을 먼저 거치므로
  (TrainScheduleOutTrainInfo.java:2810-2885) 라이브러리가 같은 행을 가려낼 수 없습니다. 입석+좌석은 `MERGE_STANDING` 입니다.
- N카드 6개 기능의 미검증 상태와 기존 미지원 기능 범위를 유지합니다.
