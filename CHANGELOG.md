# 변경 이력

## [Unreleased]

- 앱 7.0.8의 일반 결과 코드 10,305개·메시지 17,256개를 패키지 사전에 포함하고 `get_error_message`·`resolve_error_message`를 추가했습니다. 한국어·영어·일본어·중국어와 번역 누락 시 한국어 보완을 지원합니다.
- 예외와 응답 모델에 `display_message`를 추가했습니다. 읽을 서버 메시지를 우선하고 빈 메시지는 사전으로 보완하며, 원문·기존 예외 문자열을 보존합니다. 표시에 HTML을 실행하지 않고 줄바꿈 태그는 개행으로 바꿉니다.
- 복원한 서비스 오류 `S000`·`S003`과 메시지상 혼잡 `S001`·`S002`를 서비스 오류로 분류합니다. `KorailRateLimitError`(`BT019`·`BT023`), `KorailProcessingError`(`WRT900900`), `KorailAlreadyProcessedError`(`EZZ000014`·`EVZ000102`), 로그인 문맥의 `KorailAccountLockedError`(`WRC000390`)를 추가했습니다. 성공 응답·세션 만료 판정과 API 자동 재시도 정책은 유지합니다.

- `ERR299943`("예약할인이 지원되지 않습니다")을 `KorailNotEntitledError`에서 `KorailReservationRefusedError`로 옮겼습니다. 회원 자격 코드 `WRC000419`·`WRC800030`의 분류는 유지합니다.
- 열차 예약의 `teenager > 0`을 직통·좌석 지정·예약대기·환승·병합·간편 API에서 대기열과 예약 요청 전에 `KorailProtocolError`로 거절합니다. 검색의 청소년 인원 합산은 유지하며, 청소년드림 상품과 일반 승객 코드를 구분해 안내합니다.
- 7.0.8 할인 상수 복호화로 확인된 요청·발권 코드와 N카드 요청 코드 `153`의 근거 설명을 고쳤습니다. 어린이 단독 예약 폼과 청소년 차단 회귀 테스트, 사용자 제공 2026-10-07 승객별 실측 기록을 추가했습니다. 수정 검증은 오프라인이며 새 실서버 예약은 실행하지 않았습니다.
- `CardPayment`의 모든 입력 필드를 `repr()`·`str()`에서 숨깁니다. 생성자, 필드 값, 결제 전 검증과 실제 결제 폼은 유지합니다.
- 보호 경로의 일반 응답 봉투가 아닌 이용제한 응답에서 문자열 `code="-2000"`도 `KorailDynaPathError`로 분류합니다. HTTP 상태와 무관하게 원문을 보존하며 자동 재시도하지 않습니다. 기존 정수 차단 코드와 경로 범위는 유지합니다.
- 간편 열차 검색에 `include_no_seats`·`include_waiting_list` 필터를 추가했습니다. 기본값은 전체 결과이며, 필터 전 목록을 보존해 다음 커서와 마지막 출발 시각 계산을 유지합니다.
- `TrainSummary`에 좌석·예약대기 가용 여부, 실제 날짜를 사용하는 소요 시간과 한 줄 요약을 추가했습니다.
- `KorailReserveOption`으로 일반실·특실 우선 선택 또는 객실 제한을 지원합니다. 객실은 즉시 예약 전에 선택하고 요청 후 다른 객실 재시도나 자동 예약대기는 하지 않습니다.
- 간편 API에 역 이름 집합 `stations.names()`와 직접 기존 예약 조회 `reservations.find(pnr)`를 추가했습니다.
- 출력 개인정보·오류 분류·필터와 페이지 이동·객실 선택 회귀 테스트 및 독립 Android 암호화 기준값 9개를 추가했습니다. 신규 동작은 오프라인 합성 테스트로 검증하며 실서버 예약·결제는 실행하지 않았습니다.

## [2.4.0] - 2026-10-02

- `KorailConfig.proxy`를 추가했습니다. KORAIL API 요청과 대기열 요청을 같은 프록시(`http`, `https`, `socks5`, `socks5h`)로 보내며 같은 프로세스의 다른 HTTP 요청에는 영향을 주지 않습니다([#15](https://github.com/yakisoba0728/korail-mobile-api/issues/15)). 기본값 `None`은 기존처럼 httpx의 환경변수 프록시(`HTTPS_PROXY` 등)를 따르고, 값을 지정하면 환경변수 프록시보다 우선합니다.
- 잘못된 프록시 URL은 설정을 만들 때 `ValueError`로 거절합니다. URL의 자격 증명은 오류 메시지와 `repr`에 싣지 않습니다. `proxy`와 사용자 `transport`를 함께 넘기면 `ValueError`가 발생합니다.
- SOCKS 프록시용 선택 설치 `korail-mobile-api[socks]`를 추가했습니다. 필수 의존성과 최소 버전은 그대로입니다. `https` 프록시는 httpx 0.25.0 이상, `socks5h`는 httpx 0.28.0 이상이 필요하며 낮은 버전에서는 클라이언트를 만들 때 거절합니다.
- `build_config_from_env`가 `KORAIL_PROXY`를 읽어 `proxy`에 넣습니다. 비어 있으면 지정하지 않습니다.
- 오류 처리 문서에 로그인의 `-8202` 차단과 데이터센터·VPN 대역 안내를 더하고, README에 클라우드 서버 질문을 추가했습니다.
- 프록시를 거친 실서버 요청은 이번 버전에서 확인하지 않았습니다. 프록시 연결과 요청 경로는 합성 테스트로 확인했습니다.

## [2.3.0] - 2026-09-29

- `KorailClient.get_reservation_hold(pnr_no)`를 추가했습니다. 앱이나 다른 도구에서 잡은 기존 예약의 상세를 읽어 카드 결제용 홀드를 반환합니다. 실제 창구번호·작업번호·여정과 정산액을 보존하고, PNR 불일치·필수값 누락·명시된 결제 플래그 오류·금액 불일치·0원 예약을 거절합니다. 새 예약이나 결제는 실행하지 않습니다.
- 2026-09-29 실서버에서 예약 상세가 `h_payment_flg`를 생략하는 것을 확인해, 누락은 `None`으로 보존하고 명시된 경우에만 `Y`를 요구하도록 수정했습니다. 수정 후 실제 기존 예약 조회와 로컬 결제 폼의 식별자·정산액 보존을 확인했습니다. 시험용 임시 예약은 취소했으며 카드 결제 요청은 보내지 않았습니다.
- 기존 예약 결제 가이드와 합성 테스트를 추가했습니다. N카드 예약 복원과 이번 흐름의 실제 카드 결제는 별도 검증하지 않았습니다.
- 환승·복수 좌석의 정산액 합과 서버 총액을 대조하고, 과도하게 큰 금액을 포함한 파싱 오류에는 전체 상세 응답을 보존합니다. 조회 실패나 결제 실패를 자동 재전송하지 않습니다.
- README, 예약·결제 API, 간편 API 안내, 오류 처리, 실서버 확인 현황과 배포 절차를 갱신했습니다. 기존 공개 API의 입력·반환형과 Python 3.11 이상 지원은 유지합니다.

## [2.2.0] - 2026-09-28

- 선택형 `Korail` 간편 API를 추가했습니다. 컨텍스트 관리, KST `datetime` 검색, 역 목록 캐시·검증, 로그인 실패 시 연결 정리, 예약·승차권 리소스를 제공합니다. 전체 기능은 기존 `KorailClient`에서 계속 사용할 수 있습니다.
- `TrainSearchQuery.include_nearby_stations`로 7.0.8 요청 DTO의 `adjStnScdlOfrFlg`를 선택할 수 있습니다. 기본값 `False`는 기존 `N` 요청을 유지합니다.
- `KorailDeviceProfile`과 `build_config_from_profile`로 DynaPath 기기값·대기열 User-Agent·화면/OS 정보를 한 번에 설정할 수 있습니다.
- PyPI 수동 배포에 태그와 패키지 버전 일치 검사 및 태그 기준 CI 재실행을 추가했습니다.

## [2.1.0] - 2026-09-28

- 코레일+ 7.0.8의 `AppVersion`을 기존 API `Version`과 분리해 요청에 포함합니다. 기본값은 `7.0.8`이며 설정에서 `None`으로 생략할 수 있습니다.
- 메인 캐시 요청에 공통 필드와 기존 앱의 `srtCheckYn=Y`를 반영하고, 은행 조회의 직접 `@Field` 경로에 `AppVersion`을 추가합니다.
- 예약 상세 여정의 `h_run_dt`를 `run_date`로 제공합니다. 누락은 빈 문자열, 명시적 null·잘못된 타입은 `None`으로 읽고 원문은 `raw`에 보존합니다.
- 7.0.8 실서버 재검증 결과를 `docs/verification-708.md`에 기록했습니다. 응답 파싱 59개, 서버 거절 10개, 전제 자료 부족으로 미실행 13개, 로컬 메서드 2개입니다. 결제·환불 성공은 이번 버전에서 재확인하지 않았습니다.
- 앱 화면 전용 QR·메뉴·진단·MaaS 캐시 동작은 Python API 요청·응답 변경에 포함하지 않습니다.

## [2.0.1] - 2026-09-27

코드는 2.0.0 과 같습니다.

- PyPI 에 올립니다. `pip install korail-mobile-api` 로 설치할 수 있습니다.
- README 의 이미지와 링크를 절대 주소로 바꿔 PyPI 페이지에서도 보이게 했습니다.
- 오류 처리 문서에 로그인의 `-2000` 차단이 접속한 네트워크의 IP 대역 때문에도 생길 수 있다는 안내를 더했습니다.

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
