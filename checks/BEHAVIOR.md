# 동작 계약과 확인 한계

## 전송과 원문

DTO 필드는 선언 순서로 평탄화하고 배열은 1기반 인덱스를 사용합니다
(`NetworkService.java:15335–15392`). Retrofit의 별도 목록 인자는 `@FieldMap` 뒤에 옵니다.
빈 문자열을 생략하는 기본 규칙과 빈 값을 명시적으로 보내야 하는 운임 조회 등 예외를 구분합니다.
`lang=None`이면 언어값을 추측하지 않고 생략합니다.

API User-Agent는 운영 관측값 `korailtalk`, 대기열 User-Agent는 기기 기반 Dalvik 형식입니다.
둘 다 `Connection: Keep-Alive`, `Accept-Encoding: gzip`을 사용하며 `Accept`는 보내지 않습니다.
보호된 헤더 리터럴을 이 정리에서 해독하거나 새로 추정하지 않습니다.

응답 모델은 자동 마스킹하지 않습니다. `frozen=True`는 중첩 사전·목록의 불변성을 뜻하지 않습니다.
공개 `raw` 타입은 읽기 인터페이스인 `Mapping[str, object]`이며 원문 객체의 동일성과 기존 복사 정책은 유지합니다.
거절한 응답의 전체 원문은 예외 `raw`, 기존 부분 원문은 `parser_raw`입니다.

## 스칼라·봉투와 선택값

앱의 String 필드가 JSON 정수로 오는 관측에 따라 문자열로 정규화합니다
(입력 자료 `SESSION_CONTEXT.md` §3.6). 불리언을 정수로 간주하지 않습니다.
선택 스칼라의 누락·null·잘못된 타입은 `None`, 후속 요청에 필요한 필수값의 잘못된 타입은
`KorailProtocolError`입니다. 선택 목록은 해당 DTO·파서의 빈 목록 규칙을 따릅니다.
Python의 정수 문자열 변환 한도를 넘는 봉투 값도 `KorailProtocolError`로 처리하고 원문을 남깁니다.

`BaseKorailResponse.from_raw`는 객체·봉투 타입을 검사하되 성공·실패를 판정하지 않습니다.
`http.parse_base_response`는 `FAIL` 또는 필수 `strResult`의 누락을 실패로 봅니다.
`null`·빈 문자열·미지의 결과 코드를 임의로 `FAIL`로 바꾸지는 않습니다.
CommonOut 경로의 `FAIL/P058` 또는 결과 누락/P058은 `raise_on_fail=False`여도 세션 만료이며,
성공 봉투의 P058만으로 만료되지 않습니다(`CommonOut.java:361,426–438,455–463`).
공항버스처럼 정확한 SUCC를 요구하는 파서는 별도 규칙을 유지합니다.

### 앱 기본값을 쓰는 18개 필드

아래는 **누락** 시의 예외입니다. 문자열은 `""`, 정수·비율로 변환하는 필드는 `None`입니다.
명시 null·잘못된 타입의 거절 규칙은 유지합니다. 다른 선택 필드로 이 예외를 확장하지 않습니다.

| 위치 | 전송 필드 | 개수 | 근거 |
|---|---|---:|---|
| 역 행 | `stn_cd`, `stn_nm` | 2 | `StationDataOutStnItem.java:60–65`; 보호된 누락 기본값은 기존 정책 유지 |
| 호차·속성 행 | `h_srcar_no`, `h_rest_seat_cnt`, `h_psrm_cl_nm`, `seatAttNm` | 4 | `TrainResearchOutCarInfo.java:59–85`, `TrainResearchOutSeatInfo.java:51–56` |
| 좌석 재고 봉투 | `layout_type`, `seat_ary_cd` | 2 | `TResidualSeatsResearchOut.java:61–82` |
| 좌석 행 | `seat_no`, `sale_psb_flg`, `dir_seat_att_cd`, `rq_seat_att_cd`, `seat_spec`, `sqr_no`, `intg_msg_cd`, `intg_msg` | 8 | `TResidualSeatsResearchOutSeat.java:62–104` |
| 창문 행 | `st_loc_rt`, `cls_loc_rt` | 2 | `TResidualSeatsResearchOutWindow.java:51–56` |

지연확인증의 `runDt`는 앱 필수 마스크와 달리 누락된 운영 응답이 있어 선택값으로 읽습니다
(`DelayCertificate.java:57–60`; 입력 관측 기록). 나머지 필수 지연 필드는 계속 검증합니다.

## 로그인과 변경 흐름

로그인은 기존 세션 폐기→서비스 상태→암호화 파라미터→로그인 순서입니다.
관측된 성공 코드와 JSESSIONID를 요구합니다. 휴면 해제·비밀번호 변경은
`KorailAuthContinuationRequired`와 `session.pending`에 남기며 웹 조치를 자동으로 이어 가지 않습니다.
일반 실패는 세션·쿠키를 비우지만 이 웹 단계에서는 응답 쿠키를 보존합니다.

`close`는 연결만 닫습니다. `clear_session`은 로컬 상태만 폐기합니다.
`logout`은 서버 요청이 실패해도 로컬 상태를 정리하며 서버 무효화 성공을 보장하지 않습니다.

예약대기는 좌석 확보와 다르고 `payable=False`입니다. `confirm_standby_hold`는 기존 대기 홀드에 옵션만 저장합니다.
병합은 첫 홀드→병합 조회→첫 홀드 취소→후속 홀드 순서이며 첫 홀드는 호출자가 취소해야 합니다.
`cancel_unpaid_hold`는 기본적으로 가능 여부 확인 후 실제 취소합니다.

카드 결제액은 홀드 `received_amount`이며 기준 운임이나 `total_price`로 대체하지 않습니다.
카드 거절은 FAIL 모델입니다. 환불은 성공한 수수료 응답을 명시적으로 받아 승차권 한 장씩 수행합니다.
마일리지로 수수료를 정산하려면 사용 가능 마일리지가 수수료 이상이어야 합니다.
환불 입력의 현재 판매일과 수수료 조회의 원표 반환일은 서로 다릅니다
(`MyTicketDetailViewModel.java:277,1521`). 반환 식별자는 라우트에 따라 MMDD 또는 YYYYMMDD를 요구합니다.

재계산의 승객별 여섯 목록은 동일 인덱스를 유지하도록 빈 문자열도 보존합니다.
`for_hold`는 첫 여정의 좌석 정보를 복사하며 요청 할인 수가 좌석 수와 같아야 합니다.
`add_to_cart=True`는 재계산 성공 후 장바구니에 추가하고 추가 실패를 `cart_addition`에 남깁니다.

## 대기열과 미확인 항목

대기열은 빈 본문 POST와 URL 쿼리를 사용합니다. SDK의 `setDoOutput(true)` 동작을 반영한 기존 정책입니다
(`com/netfunnel/api/http/Client.java:252–260`). 5101 진입, 201/202일 때만 TTL 대기와 5002 반복,
API 처리 후 finally에서 5004 반납을 수행합니다(`Netfunnel.java:610–664,848–880`).
반납 실패가 원래 API 예외를 가리지는 않습니다. 키를 API 폼에 싣지 않습니다.

TTL·대기 인원은 SDK의 Java int32 규칙으로 읽고 TTL을 1–30초로 제한합니다
(`Response.java:59–66,147–154`). 잘못된 두 숫자를 0으로 읽는 것은 기존 라이브러리의 관용 정책입니다.
SDK는 잘못된 숫자에서 전체 응답을 거절하므로, 이 차이는 남겨 둡니다.
응답 앞뒤 공백 제거와 키 값의 `=` 보존도 기존 정책이며 SDK의 분할과 다릅니다.

301/302 차단은 항상 거절합니다. 성공 전용 관문은 비성공 결과를 통과시키지 않습니다.
라이브러리가 제공하는 누적 대기 상한은 SDK의 상한이 아닙니다.
서버가 준 노드가 허용 범위를 벗어나면 정문을 사용합니다.

보호된 aid·mode·enum·JSON 설정, DynaPath 차단 키의 정확한 범위, 일부 결제·환불 제어값은 미확인입니다.
DynaPath 차단 판정은 보호된 키 대신 최상위 정수를 검사하므로 다른 필드의 같은 값을 오인할 수 있습니다.
기존 토큰 공식을 바꾸거나 보호 문자열을 해독하지 않습니다.

N카드 일부 기능, 채워진 지연료 영수증, 셀프 체크인 좌석 확인·등록·취소 및 전달표 회수는 실서버 수용을 확인하지 않았습니다.
기존 실서버 상태표는 입력 자료이며 이번 정리의 검사는 전부 오프라인입니다.
세 `_*_unsupported.py`는 기록용으로 유지하고 공개 클라이언트에서 import하지 않습니다.
