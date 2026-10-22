# 변경 이력

## [3.0.0] - Unreleased

2.x와 호환되지 않는 변경을 한 번에 모은 판입니다. 옛 이름의 별칭은 없습니다. 바뀐 이름·인자·import 경로의 전체 표와 고치는 방법은 [3.0으로 옮기기](https://yaki.kr/korail-mobile-api/migration-3.0/)에 있습니다.

### 추가

- `KorailInvalidInputError`: 요청 전 입력 검사의 거절입니다. `KorailProtocolError`이자 `ValueError`라 기존 `except`도 잡습니다.
- 모든 라이브러리 예외의 `request_sent`: 요청을 전송 계층에 넘긴 뒤 전송·응답 해석에 실패하면 `True`, 요청 전에 거절했으면 `None`입니다. 상태를 바꾸는 메서드에서는 서버가 처리했을 수 있다는 note도 붙습니다.
- `KorailTransportError.status_code`: 2xx가 아닌 HTTP 응답의 상태 코드입니다. 네트워크 단계 실패는 `None`입니다.
- `KorailClient`의 `with` 문 지원: 블록이 끝나면 `close`만 부르고 서버 로그아웃은 하지 않습니다.
- `HoldReference(*, pnr_no, journey_count, journey_sequence=None, change_no=None)`와 `ReservationHoldResponse.reference`, PNR·여정 수만 요구하는 `HoldReference.from_raw(raw)`. `cancel_unpaid_hold`가 홀드 대신 받으며 같은 값이면 같은 요청을 보냅니다.
- 조회 결과를 옮기는 팩토리: `OriginalTicketReference.from_ticket`(원표 반환일을 판매일로 사용), `FreeSeatCarRequest.from_train`, `MergeSeatsInquiryRequest.from_train`, `AirportBusSeatInventoryQuery.from_schedule`.
- 간편 API: `korail.tickets.all(page_no, *, mode, boarding_date_from, boarding_date_to)`, `korail.tickets.detail`, `KorailClient.login`과 같은 키워드 옵션을 받는 `Korail.login`.
- `DynapathRequestContext`의 `body`(보낼 본문 바이트)와 `app_version`.

### 변경

- 공개 import 경로는 패키지 루트(`korail_mobile_api`)뿐입니다. 구현은 내부 패키지 `_core/`와 `_domains/<도메인>/{models,forms,parsers}.py`로 옮겼고, `device.py`·`live.py`는 `config.py`에, `error_messages.py`는 `errors.py`에 합쳤습니다. `korail_mobile_api.models`·`read_payloads`·`device` 같은 2.x 하위 모듈은 없습니다. 대기열 로거 이름 `korail_mobile_api.netfunnel`·`korail_mobile_api.netfunnel_safety`는 그대로입니다.
- `KorailClient` 메서드 38개의 이름을 바꿨습니다. 목록은 `list_`, 한 건은 `get_`, 읽기 전용 가능 여부 확인은 `check_`로 시작합니다(예: `get_reservation_history` → `list_reservations`, `get_ticket_list` → `list_tickets`, `get_refund_commission` → `get_refund_fee`, `get_limousine_schedules` → `list_airport_bus_schedules`). 간편 API는 `reservations.find` → `reservations.get`, `tickets.refund_fee` → `tickets.refund_quote`입니다. API 문서의 옛 메서드 앵커는 새 절로 이어집니다.
- 모델 이름: 공개 `Limousine*` 클래스 7개는 `AirportBus*`, `TrainSearchQuery.departure_station_code`·`arrival_station_code`는 `departure_station`·`arrival_station`입니다. 같은 전송 키를 읽는 응답 필드는 한 이름을 써서 응답 모델 25개의 필드 47개 이름이 바뀌었습니다(예: `TrainSearchMetadata.product_no` → `goods_no`, `TrainScheduleStop.planned_departure_time` → `departure_time`, `ProductReservation.payment_deadline` → `settlement_deadline`).
- 공개 입력·응답 모델과 설정 dataclass는 모두 `frozen=True, kw_only=True`라 키워드 인자로만 만듭니다. `raw`는 선언한 모델의 마지막 필드이며 `repr()`에 나오지 않습니다(비교 제외는 같음). `KorailSession.jsessionid`, 입력 모델의 반환 비밀번호·이름·전화번호·생년월일·고객번호, `DynapathTokenSettings.device_id`, `KorailConfig.advertising_id`도 `repr()`에서 숨깁니다.
- 2.x에서 pickle한 응답·입력 모델, `KorailConfig`(안의 `DynapathConfig` 포함), `KorailDeviceProfile`은 읽을 수 없습니다. 예외 pickle은 생성자를 거치지 않는 형식으로 바뀌었고 2.x가 만든 pickle도 읽습니다.
- 요청 전 입력 거절은 `KorailInvalidInputError`입니다. 입력 모델·폼 검사, 로그인 입력, `refund`의 수수료 응답 검사, 간편 API가 직접 내던 `ValueError`가 해당하며 메시지는 같습니다. 간편 API에서 인자 타입이 틀리면 계속 `TypeError`입니다.
- 만들 때 거절하는 입력 모델: `PassScheduleRequest`(`None`·비문자열 필드), `CardPayment`(카드 형식, `card_type`은 `str`), `PaidTicket`(필수 식별자 다섯), `FreeSeatCarRequest`·`MergeSeatsInquiryRequest`(열차 식별값), `AirportBusScheduleQuery`·`AirportBusSeatInventoryQuery`(필수 식별값), `PriceFareQuoteRequest`(`goods_no` 일관성). 올바른 입력의 요청 바이트는 같습니다.
- 요청 전 검사 추가: `get_train_schedule`·`list_seat_cars`·`get_seat_inventory`는 비었거나 `None`인 열차 번호·운행일·역 코드·운행 순서를, `list_tickets`의 `boarding_date_from`·`boarding_date_to`는 빈 문자열이나 ASCII 숫자 8자리가 아닌 값을 거절합니다.
- DynaPath 헤더는 `DynapathConfig.allowlist_paths`만으로 정합니다. 기본 목록에서 요청 바이트는 같습니다.

### 제거

- `get_notice`: `get_app_data().notice`를 쓰세요. 공지가 없으면 `None`이며 요청은 같습니다.
- `register_discount_card`와 `DiscountCardPurchaseRequest`·`DiscountCardSectionRequest`·`DiscountCardAdditionalUser`·`DiscountCardPurchaseResponse`. 실서버에서 확인하지 못했고 라이브러리로 결제·취소할 수 없는 구매만 만들었습니다.
- `DiscountCardTicket`: `extend_discount_card`는 같은 네 값을 `OriginalTicketReference`로 받고 같은 요청을 보냅니다.
- `reserve_merge(job_type=)`(항상 `MERGE_STANDING`), `recalculate_price(add_to_cart=)`와 2.6.2의 `ReservationHoldResponse.cart_addition`·`cart_addition_error`(재계산 뒤 `add_to_cart`를 따로 호출), `search_trains_with_transfer_fallback(continuation=)`.
- 항상 `None`이던 `DiscountCardScheduleResponse.following_page_exists`, 쓰이지 않던 `CartItem.usage_window`. 공개 메서드는 85개에서 83개입니다.
- 미지원 호출 기록 `_maas_unsupported`·`_social_login_unsupported`·`_travel_search_unsupported`와 그 호출만 쓰던 빌더·파서·모델은 `tests/records/`로 옮겨 wheel에 넣지 않습니다. sdist에는 테스트와 함께 들어갑니다.

### 수정

- `cancel_unpaid_hold`는 검사한 여정 수를 그대로 보냅니다. 이전에는 `" 1"`을 공백째 보냈습니다.
- `get_common_codes`는 `bytes`와 문자열이 아닌 항목을 거절합니다. 이전에는 바이트마다 `code`로 보냈습니다.
- `list_tickets`는 `date` 객체 같은 값을 거절합니다. 이전에는 `2026-07-01` 형태로 보냈습니다.
- `get_ticket_receipt`의 빈 `txt_index`는 조용히 빼지 않고 `get_refund_ticket_detail`과 같은 규칙·메시지로 거절합니다.
- 문자열이 아닌 출발·도착역, 카드 결제의 홀드가 아닌 값, 환불 수수료 금액의 정수가 `AttributeError`·`TypeError` 대신 요청 전 `KorailInvalidInputError`입니다.
- 공항버스 예약은 9자리를 넘는 잔여석 수를 알 수 없는 값으로 봅니다. 이전에는 매우 긴 숫자에서 `ValueError`가 났습니다.

### 안전·검증 한계

- 3.0.0은 배포 전이며 실서버에서 검증하지 않았습니다. 모든 변경은 합성 응답과 소켓 차단 환경에서만 검사했고 새 실서버 요청은 하지 않았습니다.
- 이름과 인자만 바뀐 메서드는 같은 입력에서 2.6.1과 같은 요청(본문·헤더·순서·횟수)을 보냅니다. 이는 SDK에서 캡처한 요청과의 비교(`tests/test_wire_equivalence.py`)이며 앱이나 서버의 근거가 아닙니다. 요청 전에 새로 거절하는 입력과 위 수정 항목은 예외입니다.
- 기본 요청 버전(`AppVersion=7.0.8`·API `Version=250601003`)은 그대로입니다. 2026-10-21부터 보고된 `-8204`(GitHub #32) 상황과 기록된 관측 범위는 [실서버 확인 현황](https://yaki.kr/korail-mobile-api/status/)에 있습니다.
- `repr()`에서 숨기는 것은 출력뿐입니다. 속성 값, `raw`, `dataclasses.asdict()`, pickle은 가리지 않습니다.
- `request_sent`가 `True`인 상태 변경 실패는 서버에서 처리됐을 수 있습니다. 라이브러리는 다시 보내지 않으며, 호출자가 상태를 확인한 뒤에 정해야 합니다.

## [2.6.2] - 2026-10-23

- GitHub #32: 2026-10-21부터 기본 요청 버전(AppVersion 7.0.8·Version 250601003)에 `-8204`("최신 버전으로 업데이트") 응답이 보고됐습니다. `-8204`를 로그인 포함 모든 경로에서 `KorailAppUpdateRequiredError`로 분류하고 서버 문구를 보존합니다. 앱 리터럴이 아니라 실서버 관측 코드입니다. `build_config_from_env()`는 `KORAIL_APP_VERSION`·`KORAIL_API_VERSION`을 읽습니다. 기본 요청 버전은 바꾸지 않았습니다. 기록된 성공은 AppVersion 7.0.10·Version 250722001·`2!` 헤더 조합의 병합 전 작업트리 관측 1건뿐이며, 현재 기본 조합은 실서버에서 확인하지 않았습니다.
- 결제 안전: `reserve_merge`는 `job_type=MERGE_STANDING`만 받습니다. 다른 값은 입석 플래그를 덮어써 예약대기 홀드가 결제 가능한 결과로 돌아올 수 있었습니다. `PriceRecalculationRequest.for_hold()`는 예약대기 홀드(`payable=False`)를 거절합니다. `recalculate_price(..., add_to_cart=True)`의 장바구니 단계가 라이브러리 예외로 끝나면 이미 반영된 재계산 홀드를 돌려주고 예외를 새 필드 `ReservationHoldResponse.cart_addition_error`에 담습니다.
- 개인정보: 네트워크 단계에서 실패한 요청의 `KorailTransportError.__cause__.request`는 메서드와 쿼리 없는 URL만 남깁니다. 본문(로그인 아이디·변환된 비밀번호·카드 필드), 쿠키, DynaPath 토큰, 쿼리가 오류 수집 도구에 남던 문제를 막습니다. 예외 타입과 identity는 그대로입니다. 모델·`raw`·`asdict`·pickle은 여전히 가리지 않습니다.
- 요청 전 검사: 값이 `None`인 요청 필드는 빈 값(`key=`)으로 보내지 않고 `KorailProtocolError`로 거절합니다. 빈 문자열 생략은 그대로입니다. 비ASCII 숫자, 문자열이 아니거나 ASCII가 아닌 DynaPath 토큰, httpx가 읽지 못하는 대기열 URL, 0·음수·nan인 시간 설정도 요청 전에 거절합니다. 로그인 입력과 열차 검색 승객 수는 서비스 확인·암호 키·역 목록 요청보다 먼저 검사합니다.
- DynaPath 차단 판별은 설정의 `allowlist_paths`를 따릅니다. 간편 API와 클라이언트가 역 목록을 한 번만 받아 함께 씁니다. `korail.trains.search(..., continuation=...)`는 첫 페이지의 `depart_after`를 요구하고 지난 시각으로 거절하지 않습니다. 검증한 날짜는 다시 포맷하지 않고 그대로 보냅니다.
- 기본 DynaPath를 SDK 2.0.1 `2!` native-unavailable 진단으로 전환합니다. 기본 헤더에 기기값을 합성하지 않고 profile/env로 제공한 값만 `os`·`dm`·`iid`에 넣습니다. 명시적 v1 설정·외부 공급자·기존 allowlist·대기열·무재시도 정책은 유지하며 env builder는 v1 전용 `KORAIL_DYNAPATH_AS_VALUE`를 더 이상 읽지 않습니다. 같은 헤더 형식의 실서버 관측은 [실행 당시 조건](https://github.com/yakisoba0728/korail-mobile-api/blob/main/docs/verification-7010.md#diagnostic-20261023)으로 별도 기록합니다.
- 테스트: 85개 공개 메서드와 설정 변형이 보내는 요청을 순서까지 v2.6.1 기준으로 고정하고(SDK 캡처, 앱 근거 아님), 순서 의존 테스트·로거 레벨 누수·조용한 skip을 고칩니다. 경고는 실패로 처리하고 CI 액션을 SHA로 고정합니다.

## [2.6.1] - 2026-10-19

- `PriceFareLeg.from_train()`으로 조회한 열차의 운임 입력을 만들고, `korail.trains.iter_search(..., max_pages=...)`로 직통 검색을 선택적으로 이어 읽습니다. 기존 한 페이지 검색·기본 필터는 유지하며, 이어보기는 요청 상한·복합 식별자 중복 제거·진전 없음 중단을 적용합니다.
- `korail.membership.mileage()`·`coupons()`와 `korail.airport_bus.stops()`·`search()`·`seats()`를 추가합니다. 기존 조회·파싱·응답 원문을 재사용하고, 정류장 이름·코드의 잘못된 짝이나 필수 편 식별자 누락은 거절합니다. 버스 운행 그룹은 호출자가 명시하며 보호된 기본값을 추측하지 않습니다. 새 간편 흐름은 오프라인 합성 응답으로 검증하며 실서버 성공을 새로 주장하지 않습니다.
- 예약 가이드에 검색·예약의 승객 구성을 각각 전달하고 실제 정산액·적용 할인을 확인하는 절차를 보강합니다. 객실 우선 선택 예제에도 같은 승객 구성을 전달하고, 두 예약 예제는 대안임을 명시합니다. 개인정보 출력·원문 보존·대기열·환불 대상 연결·변경 요청 무재전송 정책은 유지합니다.
- CI에 주간 검사, actionlint, 런타임 의존성·비밀·설정의 Trivy 검사와 테스트 보고서 보관을 추가합니다. Dependabot은 Python·문서·Actions 갱신 PR을 만들도록 설정합니다. 설치된 wheel에서도 신규 간편 조회 테스트를 실행하며, 게시·문서 배포는 계속 수동입니다.

## [2.6.0] - 2026-10-19

- README의 버전·설치·검증 범위를 최신화하고 이전 SRT 프로젝트 안내를 짧은 링크로 정리합니다. 에이전트용 `AGENTS.md`에 코드 지도·작업별 참고 문서·안전 경계·검증 기준을 추가합니다.
- 환불 마일리지 비교에서 매우 긴 숫자 문자열이 Python의 정수 변환 한도를 넘으면 `ValueError`가 나던 문제를 수정합니다. 부호 있는 ASCII int32와 범위 밖·잘못된 값의 `0` 처리 정책을 유지하고, 긴 선행 0이 붙은 정상 값은 읽습니다. 전역 변환 한도·응답 원문·수수료 조회 연결·재전송 정책은 바꾸지 않습니다.
- 공개 시그니처와 요청 동작을 유지하면서 변경 응답의 원문 보존과 MaaS 요청 생성을 기존 공통 구현으로 정리합니다. 테스트의 중복 전송·준비 코드를 줄이고 18개 기본값 필드의 누락·null·잘못된 타입 검사를 보강합니다. 변경 응답의 `raw`가 얕은 복사라는 기존 동작을 문서에 명시하며, 설치된 wheel에도 공개 호출·7.0.10 계약·환불 연결 검사를 적용합니다.
- 오류 사전만 앱 7.0.10 기준으로 갱신합니다. 일반 결과 코드 10,305개·메시지 17,256개는 같고 `WRD000058` 한국어 안내만 1개월에서 2개월로 바뀝니다. 영어 문구·오류 분류·요청 날짜 제한은 바꾸지 않습니다.
- 은행 조회 직접 필드를 `Device, Version, Key, AppVersion` 순서로, 환불·수수료 조회는 공통 필드가 먼저 오도록 정정합니다. 앱 직렬화 근거와의 정합성 수정이며 서버의 순서 민감성·실서버 영향은 미확인입니다.
- 환불은 `get_refund_commission`이 반환한 성공 응답에 비공개로 연결된 조회 대상과 원표 창구번호·반환일·일련번호·비밀번호·동반자 이름·증빙번호가 일치해야 합니다. 직접 생성·직접 파싱한 수수료 응답, 다른 승차권의 응답, 원표 반환일이 없는 입력은 요청 전에 거절하는 **fail-closed 동작 변경**입니다. 자동 수수료 조회나 재시도는 하지 않습니다.
- `PaidTicket`에 키워드 전용 `return_sale_date: str | None = None`, `companion_name: str = ""`, `companion_certificate_no: str = ""`를 추가하고 세 필드는 `repr`에서 숨깁니다. `from_refund_detail()`은 `original_sale_date`와 동반자 이름·생년월일을 복사하고 현재 `sale_date`는 따로 보존합니다. 수동 생성 시 원표 반환일을 명시해야 합니다. `TicketResource.refund_fee(ticket, *, companion=RefundCompanion())`를 지원하며 기존 `get_refund_commission` 시그니처는 유지합니다.
- 좌석배정 조회의 `*2` 이상 번호 그룹은 앱 DTO의 단일 묶음과 다른 기존 SDK 확장임을 명시하고 기능은 유지합니다.
- 관측한 7.0.10 계약의 독립 회귀 검사와 실제 조회 기반 환불 연결 검사를 추가합니다. 공통 폼의 `AppVersion="7.0.10"` 명시·`None` 생략도 검사하며, 보호된 기본값이나 실서버 수용을 증명하는 테스트로 취급하지 않습니다.
- [7.0.10 정적 검토 범위](https://yaki.kr/korail-mobile-api/verification-7010/)를 추가합니다. 공개 메서드 85개 행 검토는 전체 wire 계약·모든 분기·실서버 호환 검증이 아닙니다. 해당 정적 검토 당시의 패키지 버전은 `2.5.0`이며 그 기록을 보존합니다. 이번 패키지 버전은 `2.6.0`이고 요청 기본 `AppVersion=7.0.8`과 API `Version`은 유지합니다.

## [2.5.0] - 2026-10-07

- 로그인·초기화·컨텍스트 종료 중 연결 정리도 실패하면 원래 예외를 유지하고 후속 정리 실패를 예외 note에 남깁니다. `close()`는 두 연결의 정리를 모두 시도하고 첫 오류를 전달합니다.
- 자율 좌석 변경 객실 코드의 공개 타입을 현재 런타임 정책과 같은 `str`로 넓혔습니다. 정기권 승객 요청은 `from_response()`로만 생성하며, 공개 팩토리·빌더의 런타임 타입 해석을 보완했습니다.
- 읽기 파서와 독립 폼 빌더를 도메인별 내부 모듈로 분리했습니다. 기존 공개 import·함수 시그니처·pickle 경로와 요청 모델 위치는 유지합니다.
- 중복 테스트 전송·정리·네트워크 차단을 통합하고 기존 회귀 검사를 기능별 테스트로 옮겼습니다. 정리의 동시 실패, 소비자 타입 계약, 실제 문서 조회·페이지 이동 검사를 보강하고 문서의 연결 수명·실행 날짜·개발 버전 범위·원문 보존 설명을 수정했습니다.

- 앱 7.0.8의 일반 결과 코드 10,305개·메시지 17,256개를 패키지 사전에 포함하고 `get_error_message`·`resolve_error_message`를 추가했습니다. 한국어·영어·일본어·중국어와 번역 누락 시 한국어 보완을 지원합니다.
- 예외와 응답 모델에 `display_message`를 추가했습니다. 읽을 서버 메시지를 우선하고 빈 메시지는 사전으로 보완하며, 원문·기존 예외 문자열을 보존합니다. 표시에 HTML을 실행하지 않고 줄바꿈 태그는 개행으로 바꿉니다.
- 복원한 서비스 오류 `S000`·`S003`과 메시지상 혼잡 `S001`·`S002`를 서비스 오류로 분류합니다. `KorailRateLimitError`(`BT019`·`BT023`), `KorailProcessingError`(`WRT900900`), `KorailAlreadyProcessedError`(`EZZ000014`·`EVZ000102`), 로그인 문맥의 `KorailAccountLockedError`(`WRC000390`)를 추가했습니다. 성공 응답·세션 만료 판정과 API 자동 재시도 정책은 유지합니다.

- `ERR299943`("예약할인이 지원되지 않습니다")을 `KorailNotEntitledError`에서 `KorailReservationRefusedError`로 옮겼습니다. 회원 자격 코드 `WRC000419`·`WRC800030`의 분류는 유지합니다.
- 열차 예약의 `teenager > 0`을 직통·좌석 지정·예약대기·환승·병합·간편 API에서 대기열과 예약 요청 전에 `KorailProtocolError`로 거절합니다. 검색의 청소년 인원 합산은 유지하며, 청소년드림 상품과 일반 승객 코드를 구분해 안내합니다.
- 7.0.8 할인 상수 복호화로 확인된 요청·발권 코드와 N카드 요청 코드 `153`의 근거 설명을 고쳤습니다. 어린이 단독 예약 폼과 청소년 차단 회귀 테스트, 사용자 제공 2026-10-07 승객별 실측 기록을 추가했습니다. 승객 처리의 초기 수정은 오프라인으로 검증했으며, 출시 전 추가 실서버 검증 범위는 아래 기록에 구분했습니다.
- `CardPayment`의 모든 입력 필드를 `repr()`·`str()`에서 숨깁니다. 생성자, 필드 값, 결제 전 검증과 실제 결제 폼은 유지합니다.
- 보호 경로의 일반 응답 봉투가 아닌 이용제한 응답에서 문자열 `code="-2000"`도 `KorailDynaPathError`로 분류합니다. HTTP 상태와 무관하게 원문을 보존하며 자동 재시도하지 않습니다. 기존 정수 차단 코드와 경로 범위는 유지합니다.
- 간편 열차 검색에 `include_no_seats`·`include_waiting_list` 필터를 추가했습니다. 기본값은 전체 결과이며, 필터 전 목록을 보존해 다음 커서와 마지막 출발 시각 계산을 유지합니다.
- `TrainSummary`에 좌석·예약대기 가용 여부, 실제 날짜를 사용하는 소요 시간과 한 줄 요약을 추가했습니다.
- `KorailReserveOption`으로 일반실·특실 우선 선택 또는 객실 제한을 지원합니다. 객실은 즉시 예약 전에 선택하고 요청 후 다른 객실 재시도나 자동 예약대기는 하지 않습니다.
- 간편 API에 역 이름 집합 `stations.names()`와 직접 기존 예약 조회 `reservations.find(pnr)`를 추가했습니다.
- 출력 개인정보·오류 분류·필터와 페이지 이동·객실 선택 회귀 테스트 및 독립 Android 암호화 기준값 9개를 추가했습니다. 신규 동작의 기본 계약은 오프라인 합성 테스트로 검증했습니다.

- 2026-10-07 출시 전 `main`을 코레일+ 7.0.8 설정으로 [실서버 추가 검증](https://github.com/yakisoba0728/korail-mobile-api/blob/main/docs/verification-250.md)했습니다. 공개·회원 조회, 매진 필터, 날짜 기반 열차 요약과 일반실·특실 우선 임시 예약을 확인했습니다. 성인 1명 일반실·어린이 1명 특실 홀드를 각각 생성해 `reservations.find()`의 식별자·금액 보존을 확인하고 모두 취소했으며, 예약 이력은 전후 0건입니다. HTTP 105건은 모두 200이었고 카드 결제·환불은 실행하지 않았습니다. 예약대기 전용 행과 서버 커서의 실제 후속 조회는 이번 응답에서 관측하지 못했습니다.

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
