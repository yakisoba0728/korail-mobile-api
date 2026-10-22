# 동작 계약과 확인 한계

2.6.2부터 기본 DynaPath는 SDK 2.0.1 `2!` native-unavailable 진단입니다. 기기값은 기본 토큰에 합성하지 않으며
profile/env로 제공한 값만 padding 없는 Base64url로 추가합니다. 명시적 v1/외부 공급자·기존 경로 gate·필수 토큰·대기열·무재시도 계약은 유지합니다.
[실서버 관측의 버전·입력·한계](../docs/verification-7010.md#diagnostic-20261023)는 별도로 기록합니다.

## 전송과 원문

DTO 필드는 선언 순서로 평탄화하고 배열은 1기반 인덱스를 사용합니다
(`NetworkService.java:15335–15392`). Retrofit의 별도 목록 인자는 `@FieldMap` 뒤에 옵니다.
7.0.10 정적 검토에 따라 환불·수수료 조회는 상위 공통 필드를 먼저 보냅니다. 생성자 인자 순서는 직렬화 순서의 근거가 아닙니다.
은행 직접 `@Field` 경로는 `Device, Version, Key, AppVersion` 순서이며 공통 폼과 구분합니다.
두 순서 정정은 앱 근거와의 정합성 수정으로, 보호된 최종 map과 서버 순서 민감성·실서버 영향은 미확인입니다.
빈 문자열을 생략하는 기본 규칙과 빈 값을 명시적으로 보내야 하는 운임 조회 등 예외를 구분합니다.
`lang=None`이면 언어값을 추측하지 않고 생략합니다.
2.6.2부터 폼에 들어갈 값이 `None`인 요청 필드는 `key=`로 보내지 않고 요청 전에 `KorailProtocolError`로 거절합니다.
`""`은 이전처럼 생략합니다. `lang=None`처럼 폼을 만들기 전에 생략을 정한 선택값은 이 규칙과 별개입니다.
숫자 입력은 ASCII 숫자만 받습니다. `²`·`١`·전각 `１` 같은 유니코드 숫자는 요청 전에 `KorailProtocolError`로 거절합니다
(이전에는 일부가 일반 `ValueError`로 끝나거나 그대로 전송됐습니다).

좌석배정 조회의 `seatAttCdN/psgNumN/stlbDturDvNmN` 중 `*2` 이상은 기존 SDK 확장입니다.
7.0.10 앱 DTO에서 확인한 한 묶음과 동등하다고 주장하지 않으며, 1~9명 지원을 제거하거나 무음 축소하지 않습니다.
패키지 버전은 `2.6.2`이며 요청 기본 `AppVersion=7.0.8`과 API `Version=250601003`은 유지합니다.
`KorailConfig(app_version=..., version=...)` override와 `build_config_from_env()`의 `KORAIL_APP_VERSION`(`app_version`)·
`KORAIL_API_VERSION`(`version`)은 지원하지만 새 버전의 실서버 호환을 뜻하지 않습니다.
2026-10-21부터 보고된 `-8204` 거절과 기록된 관측 범위는 [실서버 확인 현황](../docs/status.md#current)에 둡니다.

API User-Agent는 운영 관측값 `korailtalk`, 대기열 User-Agent는 기기 기반 Dalvik 형식입니다.
둘 다 `Connection: Keep-Alive`, `Accept-Encoding: gzip`을 사용하며 `Accept`는 보내지 않습니다.
보호된 헤더 리터럴은 해독하거나 추정하지 않습니다.

`KorailConfig.proxy`를 지정하면 API와 대기열 요청이 같은 프록시를 쓰고 httpx 환경변수 프록시는 무시합니다.
지정하지 않으면 httpx 기본 동작(환경변수 프록시 포함)을 그대로 따릅니다. 사용자 `transport`와 함께 쓰면 조용히 한쪽을
버리지 않고 클라이언트 생성 시 `ValueError`로 거절합니다. 프록시 URL은 오류 메시지와 `repr`에 싣지 않습니다.

`timeout`은 0보다 큰 유한한 수 또는 `None`(httpx 제한 시간 없음, 기존과 같음), `netfunnel_timeout`은 0보다 큰 유한한 수,
`netfunnel_wait_limit`은 `None` 또는 0 이상의 유한한 수여야 하며, 아니면 설정 생성 시 `ValueError`입니다.
httpx가 해석하지 못하는 대기열 URL은 `httpx.InvalidURL`을 그대로 전파하지 않고 `KorailTransportError`로 처리합니다.
DynaPath `token_provider`가 문자열이 아니거나 ASCII가 아닌 값을 돌려주면 아무것도 보내지 않고 `KorailProtocolError`입니다.
DynaPath 차단 판정 경로는 내장 목록이 아니라 `config.dynapath.allowlist_paths`이며 사용자 지정 목록도 그대로 따릅니다.

네트워크 단계 실패의 `KorailTransportError.__cause__`(httpx 예외)는 예외 종류·객체를 유지하되, 붙은 요청에는
메서드와 쿼리를 뺀 URL만 남기고 본문·쿠키·DynaPath 토큰을 제거합니다. 응답 모델·`raw`·`dataclasses.asdict`·pickle은 마스킹하지 않습니다.

응답 모델은 자동 마스킹하지 않습니다. `frozen=True`는 중첩 사전·목록의 불변성을 뜻하지 않습니다.
공개 `raw` 타입은 읽기 인터페이스인 `Mapping[str, object]`입니다. 조회 응답은 대체로 원문 객체를 그대로 참조하지만,
변경 응답 파서(`_domains/*/parsers.py`)의 변경 응답·기존 홀드 복원과 일부 하위 행·검색 메타데이터는 사전을 얕게 복사합니다.
어느 쪽도 중첩 객체를 복사하거나 동결하지 않습니다.
거절한 응답의 전체 원문은 예외 `raw`, 파서가 남긴 부분 원문은 `parser_raw`입니다.

## 스칼라·봉투와 선택값

앱의 String 필드가 JSON 정수로 오는 관측에 따라 문자열로 정규화합니다
(예: 예약 응답의 `h_jrny_cnt` 가 `"0001"`, 예약 이력에서는 `1`). 불리언을 정수로 간주하지 않습니다.
선택 스칼라의 누락·null·잘못된 타입은 `None`, 후속 요청에 필요한 필수값의 잘못된 타입은
`KorailProtocolError`입니다. 선택 목록은 해당 DTO·파서의 빈 목록 규칙을 따릅니다.
Python의 정수 문자열 변환 한도를 넘는 봉투 값도 `KorailProtocolError`로 처리하고 원문을 남깁니다.

`BaseKorailResponse.from_raw`는 객체·봉투 타입을 검사하되 성공·실패를 판정하지 않습니다.
`_core.http.parse_base_response`는 `FAIL` 또는 필수 `strResult`의 누락을 실패로 봅니다.
`null`·빈 문자열·미지의 결과 코드를 임의로 `FAIL`로 바꾸지는 않습니다.
서버 코드 `-8204`(#32 관측값, 앱 리터럴 아님)는 로그인을 포함한 모든 경로에서 `KorailAppUpdateRequiredError`이며
서버 메시지를 보존합니다. `SUPDATE`와 같은 하위 예외이고 자동 재시도나 버전 자동 변경으로 이어지지 않습니다.
CommonOut 경로의 `FAIL/P058` 또는 결과 누락/P058은 `raise_on_fail=False`여도 세션 만료이며,
성공 봉투의 P058만으로 만료되지 않습니다(`CommonOut.java:361,426–438,455–463`).
공항버스처럼 정확한 SUCC를 요구하는 파서는 별도 규칙을 유지합니다.

7.0.8 일반 오류 분기의 복원값은 `FAIL` 기본값·실패 비교, 로그인 요구 `P058`, 서비스 오류 목록 `S000`·`S003`입니다.
Java 정수·바이트 연산 결과를 원본 smali 연산과 대조했습니다. `S000`·`S003`을 서비스 오류로 추가하며,
혼잡 `S001`·`S002`, 요청 제한 `BT019`·`BT023`, 처리 확인 필요 `WRT900900`, 기처리 `EZZ000014`·`EVZ000102`는
메시지에 근거한 라이브러리 분류입니다. 계정 잠금 `WRC000390`은 로그인에서만 `KorailAccountLockedError`입니다.
어떤 분류도 API 자동 재시도나 상태 변경 요청의 성공 간주로 이어지지 않습니다.

패키지 메시지 사전은 앱 7.0.10의 일반 결과 코드 10,305개·메시지 17,256개와 원본 SHA-256을 보관합니다.
7.0.8 대비 `WRD000058` 한국어만 1개월→2개월로 변경됐으며 영어·오류 분류·요청 날짜 제한은 유지합니다.
`checks/build_error_catalog.py`로 로컬 `assets/error_json.json`에서 재생성하며 앱 설정·임의 리소스 키는 제외합니다.
`get_error_message`는 사전 원문을 조회하고 `resolve_error_message`·`display_message`는 읽을 서버 메시지를 우선해
일반 텍스트를 표시합니다. 태그·스크립트·스타일을 표시에서 제외하고 원문 필드·예외 문자열은 유지합니다.
사전에는 성공·안내·과거 코드도 있으므로 사전 등록 여부나 메시지로 실패·세션 만료·재시도를 추론하지 않습니다.

### 앱 기본값을 쓰는 18개 필드

아래는 **누락** 시의 예외입니다. 문자열은 `""`, 정수·비율로 변환하는 필드는 `None`입니다.
명시 null·잘못된 타입의 거절 규칙은 유지합니다. 다른 선택 필드로 이 예외를 확장하지 않습니다.

| 위치 | 전송 필드 | 개수 | 근거 |
|---|---|---:|---|
| 역 행 | `stn_cd`, `stn_nm` | 2 | `StationDataOutStnItem.java:60–65`; 7.0.8의 일반 DTO 문자열 복원으로 누락 기본값 `""` 확인 |
| 호차·속성 행 | `h_srcar_no`, `h_rest_seat_cnt`, `h_psrm_cl_nm`, `seatAttNm` | 4 | `TrainResearchOutCarInfo.java:59–85`, `TrainResearchOutSeatInfo.java:51–56` |
| 좌석 재고 봉투 | `layout_type`, `seat_ary_cd` | 2 | `TResidualSeatsResearchOut.java:61–82` |
| 좌석 행 | `seat_no`, `sale_psb_flg`, `dir_seat_att_cd`, `rq_seat_att_cd`, `seat_spec`, `sqr_no`, `intg_msg_cd`, `intg_msg` | 8 | `TResidualSeatsResearchOutSeat.java:62–104` |
| 창문 행 | `st_loc_rt`, `cls_loc_rt` | 2 | `TResidualSeatsResearchOutWindow.java:51–56` |

지연확인증의 `runDt`는 앱 필수 마스크와 달리 누락된 운영 응답이 있어 선택값으로 읽습니다
(`DelayCertificate.java:57–60`; 입력 관측 기록). 나머지 필수 지연 필드는 계속 검증합니다.

## 로그인과 변경 흐름

로그인은 기존 세션 폐기→서비스 상태→암호화 파라미터→로그인 순서입니다. 비밀번호 타입은 첫 요청 전에 검사합니다.
관측된 성공 코드와 JSESSIONID를 요구합니다. 휴면 해제·비밀번호 변경은
`KorailAuthContinuationRequired`와 `session.pending`에 남기며 웹 조치를 자동으로 이어 가지 않습니다.
일반 실패는 세션·쿠키를 비우지만 이 웹 단계에서는 응답 쿠키를 보존합니다.

`close`는 연결만 닫습니다. `clear_session`은 로컬 상태만 폐기합니다.
`logout`은 서버 요청이 실패해도 로컬 상태를 정리하며 서버 무효화 성공을 보장하지 않습니다.

예약대기는 좌석 확보와 다르고 `payable=False`입니다. `set_standby_options`는 기존 대기 홀드에 옵션만 저장합니다.
일반 열차 예약의 승객 종류는 `PassengerType.basicList()`의 일곱 종류입니다. `teenager > 0`은 직통·좌석 지정·
예약대기·환승·병합 예약과 간편 API에서 대기열·예약 요청 전에 `KorailProtocolError`로 거절합니다.
검색에서는 기존처럼 청소년을 어른 인원에 합산하지만 예약 인원을 자동으로 어른으로 바꾸지 않습니다.
`P11`은 청소년드림 상품(`SpecialOffer.YOUTH`, 발권 할인 코드 `508`)과 다른 경로입니다.
`ERR299943`은 지원하지 않는 예약 할인으로 `KorailReservationRefusedError`에 속하며,
회원 자격 코드 `WRC000419`·`WRC800030`은 `KorailNotEntitledError`로 유지합니다.
병합은 첫 홀드→병합 조회→첫 홀드 취소→후속 홀드 순서이며 첫 홀드는 호출자가 취소해야 합니다.
`reserve_merge`는 작업 유형 인자 없이 항상 `MERGE_STANDING`으로 보냅니다(3.0에서 `job_type=` 제거).
이전에는 `STANDBY`·`IMMEDIATE`도 그대로 보내 결제 가능한 홀드가 반환될 수 있었습니다.
`cancel_unpaid_hold`는 기본적으로 가능 여부 확인 후 실제 취소합니다.
예약 응답의 파싱 실패 때 PNR은 예외 `raw`에 남지만 `get_reservation_hold`도 같은 파서로 실패할 수 있습니다.
알려진 한계로, 취소는 `ReservationHoldResponse(str_result="SUCC", pnr_no=..., journey_count=...)`를 직접 만들어 넘기는 방법뿐이며
전용 API는 3.0에서 제공할 예정입니다.

카드 결제액은 홀드 `received_amount`이며 기준 운임이나 `total_price`로 대체하지 않습니다.
카드 거절은 FAIL 모델입니다. 환불은 성공한 수수료 응답을 명시적으로 받아 승차권 한 장씩 수행합니다.
`get_refund_fee` 반환 시 응답에 비공개 조회 문맥을 연결하고 `repr`에서 숨깁니다.
`refund`는 그 문맥과 환불 대상의 원표 창구번호·반환일·일련번호·비밀번호·동반자 이름·증빙번호 일치를 요구합니다.
직접 생성·직접 파싱한 수수료 응답, 다른 대상의 응답, 원표 반환일이 없는 입력은 요청 전에
`KorailProtocolError`로 거절하는 fail-closed 동작 변경입니다. 자동 조회·재시도는 하지 않습니다.
이는 대상 혼용 방지이며 수수료 금액의 유효기간·서버 승인이나 임의 변조 방지를 보장하는 인증 수단이 아닙니다.
조회 문맥의 개인정보는 파일로 저장하지 않습니다. `repr` 숨김은 속성·`raw`·직렬화 결과 전체의 마스킹이 아닙니다.

`get_reservation_hold(pnr_no)`는 예약 상세 한 번의 조회로 카드 결제용 홀드를 가져옵니다.
응답 PNR 일치·실제 창구번호·여정 수와 행 수 일치·여정별 좌석 행·양수 정산액을 요구합니다.
2026-09-29 실서버 상세에서 생략된 결제 플래그는 `None`으로 보존하며, 명시된 경우에만 `Y`를 요구합니다.
총액이 명시됐다면 유효한 정수이며 좌석 합과 같아야 합니다. 좌석번호 없는 0원 행은 거절합니다.
이는 기존 예약을 가져오는 기능의 보수적 정책으로, 보호된 앱 상태 판정의 재현이 아닙니다.
기존 홀드 파서를 재사용해 작업번호·예약변경번호·여정·원문을 보존하며, 창구번호를 추측하거나
목록 마지막 예약을 자동 선택하지 않습니다. 기존 예약 조회와 로컬 결제 폼 생성은 확인했으며,
실제 결제는 별도 호출입니다. 이 흐름의 실제 카드 결제와 N카드 예약 복원은 미검증입니다.

마일리지로 수수료를 정산하려면 사용 가능 마일리지가 수수료 이상이어야 합니다.
비교할 수치는 SDK의 기존 규칙대로 부호 있는 ASCII 정수만 읽습니다. int32 범위·실패 시 `0` 보완은 앱
`TextHelper.getInteger`를 따릅니다. 긴 선행 0은 허용하며 Python의 전역 정수 변환 한도를 변경하지 않습니다.
비교를 위해 정규화한 수치는 응답 모델의 문자열 필드나 `raw`에 다시 쓰지 않습니다.
환불 입력의 현재 판매일과 수수료 조회의 원표 반환일은 서로 다릅니다
(`MyTicketDetailViewModel.java:277,1521`). 반환 식별자는 라우트에 따라 MMDD 또는 YYYYMMDD를 요구합니다.
`PaidTicket`의 키워드 전용 `return_sale_date: str | None = None`, `companion_name: str = ""`,
`companion_certificate_no: str = ""`는 `repr`에서 숨깁니다. `from_refund_detail()`은 상세의
`original_sale_date`→`return_sale_date`, `companion_name`→동명 필드,
`companion_birth_date`→`companion_certificate_no`를 복사하고 현재 `sale_date`는 별도로 유지합니다.
수동 생성한 `PaidTicket`으로 환불하려면 원표 반환일을 명시해야 하며 현재 판매일로 대신하지 않습니다.
기존 `get_refund_fee(ticket, companion=RefundCompanion())` 시그니처는 유지하고,
간편 API는 `TicketResource.refund_quote(ticket, *, companion=RefundCompanion())`로 같은 동반자 정보를 받습니다.

재계산의 승객별 여섯 목록은 동일 인덱스를 유지하도록 빈 문자열도 보존합니다.
`for_hold`는 첫 여정의 좌석 정보를 복사하며 요청 할인 수가 좌석 수와 같아야 합니다. `payable=False`(예약대기) 홀드는 `KorailProtocolError`로 거절합니다.
`recalculate_price`는 재계산 요청 하나만 보냅니다. 앱처럼 장바구니에 담으려면 호출자가 재계산 성공 뒤 `add_to_cart`를 따로 부릅니다.

간편 검색의 `continuation`에는 첫 페이지의 `depart_after`가 필요하며(없으면 `ValueError`) 이어보기를 지난 시각으로 거절하지 않습니다.
간편 검색은 역 목록을 받기 전에 승객 구성을 검사하고, 역 목록은 한 번만 받아 간편 API와 클라이언트가 공유합니다.

## 대기열과 미확인 항목

대기열은 빈 본문 POST와 URL 쿼리를 사용합니다. SDK의 `setDoOutput(true)` 동작을 반영했습니다
(`com/netfunnel/api/http/Client.java:252–260`). 5101 진입, 201/202일 때만 TTL 대기와 5002 반복,
API 처리 후 finally에서 5004 반납을 수행합니다(`Netfunnel.java:610–664,848–880`).
반납 실패가 원래 API 예외를 가리지는 않습니다. 키를 API 폼에 싣지 않습니다.

TTL·대기 인원은 SDK의 Java int32 규칙으로 읽고 TTL을 1–30초로 제한합니다
(`Response.java:59–66,147–154`). 잘못된 두 숫자를 0으로 읽는 것은 라이브러리의 관용 정책입니다.
SDK는 잘못된 숫자에서 전체 응답을 거절하므로, 이 차이는 남겨 둡니다.
응답 앞뒤 공백 제거와 키 값의 `=` 보존도 라이브러리 정책이며 SDK의 분할과 다릅니다.

301/302 차단은 항상 거절합니다. 성공 전용 관문은 비성공 결과를 통과시키지 않습니다.
라이브러리가 제공하는 누적 대기 상한은 SDK의 상한이 아닙니다.
서버가 준 노드가 허용 범위를 벗어나면 정문을 사용합니다.

승객 요청 할인 값과 N카드 요청 코드 `153`은 7.0.8의 일반 할인 상수 복호화로 확인했습니다.
요청의 `ReqDiscount.CHILD=000`·`N_CARD=153`과 발권 응답의 `ResDiscount.CHILD=201`·`N_CARD=443`은 구분합니다.
일부 보호된 aid·mode·enum·JSON 설정, DynaPath 차단 키의 정확한 범위, 결제·환불 제어값은 미확인입니다.
DynaPath 차단 판정은 보호된 키 대신 최상위 정수를 검사하므로 다른 필드의 같은 값을 오인할 수 있습니다.
접근 제한 관련 보호 문자열은 해독하지 않습니다.

7.0.10의 DynaPath 조건부 문자열·nullable code, 통합결제의 일반 회원 분기,
서비스 상태 요청의 기본값 실제 전송 여부, N카드·보호 기본값은 확정하지 않았으며 임의 변경하지 않습니다.
N카드 예약 메뉴 ID `A2`는 좌석배정 값을 재사용한 미확인 값이고, `DiscountCardScheduleRequest.for_card()`의 `B2N`·`MMM` 구분은
7.0.6 정적 근거(`B2N1906…` 네 상품)와 다릅니다. N카드 일정 조회의 `usable_trip_count` 생략은 7.0.6 시기 실서버에서 `WRR000100(usePsbTno)`로 거절됐습니다.
Android push ACK·비회원 UI·진단 화면은 이식하지 않습니다.
공개 메서드 85개 행의 정적 검토는 완전한 wire 계약·모든 분기·실서버 검증이 아닙니다.
범위와 한계는 [7.0.10 정적 검토](../docs/verification-7010.md)에 정리합니다.

N카드 일부 기능, 채워진 지연료 영수증, 셀프 체크인 좌석 확인·등록·취소 및 전달표 회수는 실서버 수용을 확인하지 않았습니다.
저장소의 테스트와 검사기는 모두 오프라인이며 실서버 수용을 증명하지 않습니다.
세 `_*_unsupported.py`와 그 호출만 쓰는 빌더·파서·모델은 기록용으로 `tests/records/`에 두며 배포 패키지에 넣지 않고
패키지 소스에서 import하지 않습니다.
