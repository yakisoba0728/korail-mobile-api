# Changelog

이 문서는 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르고,
이 프로젝트는 [유의적 버전](https://semver.org/lang/ko/)을 따릅니다.
1.0.0 이전 기록은 당시 형식·언어 그대로 보존합니다.

## 1.1.0 - 2026-07-31

APK 디컴파일 산출물과 코드를 다시 대조한 감사 한 바퀴입니다. 공개 API 는 그대로고,
버그 두 건이 고쳐졌고, 소스에서 약 3,100줄이 빠졌고, 마지막 미검증 전송 두 개가
실서버 왕복으로 닫혔습니다.

### Fixed

- **오프라인 게이트가 로케일에 따라 죽던 것.** `_collected_offline_test_count` 가
  자식 pytest 에게 자기 개수를 물을 때, 자식은 stdout 이 파이프면 인코딩을 로케일에서
  가져오므로 한국어 Windows 에서 cp949 로 씁니다. 부모가 `encoding="utf-8"` 로 읽어서
  `subprocess` 의 reader 스레드가 죽고 `result.stdout` 이 `None` 이 되고, 개수를 찾던
  정규식이 `TypeError` 를 냈습니다. 이 저장소는 테스트 이름이 전부 ASCII 라 우연히
  통과하던 잠재 버그였고, 자매 저장소 `srt-mobile-api` 는 한글 테스트명 때문에 같은
  이유로 실제로 실패하고 있었습니다. 자식 환경에 `PYTHONIOENCODING=utf-8` 을 못박아
  발생 지점에서 고쳤습니다. 부모에 `errors="replace"` 를 주면 크래시는 멈추지만 깨진
  글자를 통과시켜 놓고 고쳐진 척하므로, 어긋남을 알아채는 것이 일인 검사에서는 더
  나쁩니다.
- **맞는 운임을 결제 직전에 거부하던 것.**
  `scripts/reserve_pay_refund_roundtrip.py` 의 `confirm_amount` 가 서버가 말하는
  청구액과 예약 홀드의 금액을 **문자열로** 비교했습니다. 둘은 같은 금액인데 폭이
  다릅니다 — `tk.SelTicketInfo` 는 `h_tot_rcvd_amt` 를 16자리 0채움으로,
  `TicketReservation` 은 `h_rcvd_amt` 를 채움 없이 보냅니다. 그래서 첫 실카드 왕복이
  8,400원이 맞는데도 `'0000000000008400' != '8400'` 으로 (d) 단계에서 멈췄습니다.
  게이트 자체는 제대로 작동해 홀드를 풀고 아무것도 청구하지 않았지만, 멈춘 이유가
  틀렸습니다. 이제 수로 비교하며, 읽을 수 없는 값은 `None` 입니다 — 0 으로 접으면
  "0원이 맞다"고 통과시켜 버립니다. `refunds.CommissionView` 의 `ret_amt`·`ret_fee`
  는 14자리로 채워 오므로 배너도 `0` 으로 찍습니다.
  회귀는 아닙니다. 필드 매핑과 그 `str` 타입은 `1.0.0` 이후 그대로고, 이 경로가
  실서버에서 도는 것이 처음이었으며, 오프라인 스텁이 **양쪽 다** `"8400"` 이라
  드러날 수 없었습니다.

### Changed

- **소스 20개 모듈에서 3,117줄이 빠졌습니다** (4,283줄 삭제 / 1,166줄 추가). 동작
  변경은 없습니다 — 공개 표면, 라우트, 필드, 봉투 처리가 모두 그대로고 오프라인
  개수도 리팩토링 자체로는 바뀌지 않았습니다. 같은 규칙을 세 곳에서 반복하던 설명,
  코드를 변호하던 주석, 이전 판이 무엇을 했는지 돌아보던 서술을 지웠습니다.
  `read_parsers.py` 의 인라인 `_optional_string` 171건 중 약 100건이 이미 있던
  `_nullable_string_fields` 헬퍼를 타는 필드맵이 됐고
  (`_parse_train_schedule_item` 124줄 → 5줄), `client.py` 는 3,046줄 → 2,109줄로
  줄면서 읽기 20개와 mutation 3개가 `_post_read`·`_get_read`·`_mutation` 을
  지납니다. **APK 인용(`Foo.java:123`)과 안전 게이트는 하나도 지우지
  않았습니다** — 인용은 독자가 필드명을 앱과 대조할 수 있는 유일한 근거입니다.
- `dynapath.py` 는 주석이 늘었습니다. 토큰의 `rt` 필드를 `"0"` 으로 고정하는 것은
  앱이 요청 간 간격 배열을 보내고 비면 필드를 생략하는 것(`B/C1229b.java:118-127`)에
  대한 **의도된 무상태 단순화** 이고, 실서버 성공 응답에서 얻은 기준 토큰이 그것을
  고정합니다. 소스에 그 말이 없어서 감사에서 여섯 번째로 "버그"로 재발견됐습니다.

### Added

- `scripts/reserve_pay_refund_roundtrip.py --reserve-cancel-only` — 예약하고 바로
  취소하는, **결제 단계가 없고 카드를 읽지도 않는** 모드. 라이브러리를 고친 뒤
  예약·취소 와이어 형태를 다시 확인하는 용도입니다. 공짜라 반복할 수 있고, 항상
  실카드를 지나는 기존 경로는 그럴 수 없습니다. 실제 홀드를 만들므로 상태 변경 옵트인
  두 개는 그대로 필요하지만, 청구할 것이 없으므로 `KORAIL_LIVE_REAL_CHARGE` 와
  `KORAIL_MAX_FARE` 는 요구하지 않습니다. 결제 동의를 구성하지 않고 `pay()` 에
  도달하지도 않으므로 청구는 금지된 것이 아니라 도달 불가능합니다.

### Verified

이 절은 코드 변경이 아니라 **이번에 실서버가 답한 것** 입니다.

- **`pay_with_card` 와 `refund`.** `1.0.0` 에서 "구현했으나 전송한 적 없음"으로
  분류돼 있던 마지막 두 경로입니다. 2026-07-31, 서울→광명 8,400원 KTX 좌석 하나를
  2026-08-31(예약 창 1개월의 끝, 반환 수수료가 0원이 되게 고름) 로 잡아
  결제(`SUCC`/`IRT000000`, `정상발매처리,정상발권처리`)하고
  반환(`SUCC`/`IRT200277`, 수수료 0원)했으며, 별도 세션에서 예약 0건을 확인했습니다.
  확인된 범위는 **개인 신용카드 일시불 1건·1여정·1인** 입니다. 할부, 법인카드, 복수
  승객, 부분 환불, 수수료가 붙는 출발 임박 반환은 여전히 미확인입니다.
- **합성 DynaPath 기기 신원.** 맨손 `KorailConfig(enable_dynapath=True)` —
  `device_model="Android"`, `os_version="15"`, 합성 16-hex 기기 id — 로도
  `login.Login` 과 `logout` 이 성공합니다. 그때까지는 실제 `Build.MODEL` 값을 쓰는
  `build_config_from_env()` 경로만 검증돼 있어 기본값 경로는 열린 질문이었습니다.
- **APK 대조.** 인용 약 270건을 디컴파일된 6.5.0 트리에서 확인했습니다. 정정 0건,
  와이어 포맷 불일치 0건. 근거 미확인 11건은 모두 이미 "번들 0-hit" 또는 "실서버
  관측"으로 표기돼 있던 것입니다.
- **관측만 하고 고치지 않은 것.** `refunds.CommissionView` 의 `prg_psb_flg` 가
  실서버에서 빈 문자열로 옵니다(픽스처는 `"Y"` 를 가정). 마일리지 분기(`"M"`)가
  구현돼 있지 않아 동작에 영향은 없지만, 이 필드는 채워진다고 믿을 수 없습니다.

## 1.0.0 - 2026-07-28

읽기 전용 경계가 라우트 60개, `KorailClient` 공개 메서드 77개가 됐습니다. 로그인·읽기
64개와 동의 게이트가 걸린 mutation 13개입니다.

### Changed

- **DynaPath 는 이제 명시적으로 켜야 합니다.** `KorailConfig()` 의 기본값이 꺼짐이 되고,
  켜는 것은 `KorailConfig(enable_dynapath=True)` 라고 말한 호출자뿐입니다. 이 토큰은
  자동화 탐지를 통과하기 위한 값이라 보낼지 말지를 패키지가 대신 정하지 않습니다.
- 켜지 않은 채 `login.Login` 을 부르면 요청이 나가기 전에 새 예외
  `KorailDynaPathRequiredError` 로 막히고, 메시지가 `enable_dynapath=True` 와
  `build_config_from_env()` 를 가리킵니다. 헤더를 빼고 보내면 서버의 거절이 "앱을 최신
  버전으로 업데이트"(`MACRO ERROR`)로 위장돼 오므로 설정 문제가 버전 문제로 오진됩니다.
- **막는 경로는 허용목록 전체가 아니라 `DYNAPATH_REQUIRED_PATHS` 하나입니다.** 토큰 없이
  거절이 관측된 것은 `login.Login` 뿐이고, 검색을 비롯한 읽기는 토큰 없이 성공했습니다.
- `enable_dynapath` 는 필드 목록 **맨 끝** 에 붙였습니다. `dynapath` 는 여덟 번째 위치
  인자로 남습니다.

### Added

- `KorailDynaPathRequiredError` — 토큰이 필요한 경로를 꺼진 설정으로 불렀을 때. 서버가
  거절한 `KorailDynaPathError` 와 달리 아직 아무것도 보내지 않았습니다.
- `enabled_dynapath_config()` — `enable_dynapath=True` 가 내부에서 부르는 것.
  `DynapathConfig` 를 직접 구성할 때 씁니다.
- `korail_mobile_api.constants.DYNAPATH_REQUIRED_PATHS`. 형제인
  `DYNAPATH_ALLOWLIST_PATHS` 와 마찬가지로 전송 계층 상수라 최상위에 올리지 않습니다.
- **환승 검색과 환승 예약.** `KorailClient.search_transfer_trains`,
  `search_trains_with_transfer_fallback`, `reserve_transfer`, 그리고
  `TransferItinerary`, `TransferSearchResult`, `pair_transfer_itineraries` 와 코드 넷
  (`KORAIL_DIRECT_ITINERARY_CODE`/`KORAIL_TRANSFER_ITINERARY_CODE` = `"1"`/`"2"`,
  `KORAIL_DIRECT_JOURNEY_TYPE_CODE`/`KORAIL_TRANSFER_JOURNEY_TYPE_CODE` = `"11"`/`"14"`,
  `KORAIL_MAX_JOURNEY_LEGS` = `2`). **구현했고 NOT live-verified** 입니다.
  - 앱은 직통과 환승에 요청 빌더 하나를 씁니다(`C5/a.java:52-119`). 한 다리짜리 폼은 키
    순서까지 이전과 바이트 단위로 같고, 계약 테스트가 키 56개를 순서째로 고정합니다.
    여정 순번은 `DecimalFormat("000")` 을 거쳐 전선에 `"001"`/`"002"` 로 닿습니다.
  - **환승의 두 다리 모두 `txtJrnyTpCd="14"` 를 싣습니다.** jadx 가 값이 같은 무관한
    상수 뒤에 이것을 숨기므로 `smali/C5/a.smali:306-338` 과 `smali/K4/e.smali:68` 에서
    바이트코드로 다시 읽었습니다.
  - **두 다리는 앱의 천장이지 여기서 고른 제약이 아닙니다.** 폼에 여정 3 의 철자가
    없습니다 — `OSeat.java:32-35` 와 `OSrcar.java:21-30` 이 "여정 1 이냐 아니냐" 로
    갈리므로 세 번째 다리는 다리 2 를 덮어씁니다. 그 밖의 다리 수는 거절합니다.
  - 환승 **검색** 이 옮기는 필드는 `radJobId` 하나뿐입니다
    (`DirectInquiryActivity.java:284-296`). `search_trains_with_transfer_fallback` 는 앱
    자신의 흐름을 그대로 옮긴 것이고 `KorailNoDirectTrainError` 만 삼킵니다.
  - 환승 응답의 모양은 다르지 않습니다. 같은 평탄한 목록을 자리로 짝지어 0/1, 2/3 순으로
    묶고 홀수로 남은 마지막 행은 버립니다(`a5/k.java:156-170`).
  - **예약대기(`1102`)는 조합되지 않고 거절됩니다.** 앱이 두 곳에서 막습니다 —
    `a5/k.java:120-127` 과 `DirectInquiryActivity.java:434`.
- **병합예약.** `KorailClient.reserve_merge`, `build_merge_reservation_form`,
  `is_merge_eligible`, `KorailReservationJobType.MERGE_STANDING` (`"1202"`), 병합 선행·후행
  여정 코드(`"21"`/`"22"`), `KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`,
  `TrainSummary.merge_seat_application_flag`. **전송한 적 없습니다.**
  - 병합은 한 열차를 중간역에서 나눠 두 구간의 좌석을 다르게 잡는 것이지 환승이 아닙니다.
    탑승은 한 번입니다(`res/values/strings.xml:702,577`).
  - 병합 폼은 `DirectInquiryActivity.java:576-601` 이 만들고 환승과 네 군데에서 갈립니다.
    `setArvTm` 호출이 아예 없어서 `arvTm_1` 에 입석 예약의 전 구간 도착시각이 그대로
    남습니다. 그래서 빌더가 입석 예약의 `TrainSummary` 를 함께 받습니다.
  - `reserve_merge` 는 자신이 대체하는 입석 예약을 취소하지 않습니다. 그 취소는 `"cancel"`
    동의 아래의 `cancel_unpaid_hold` 입니다.
- **할인카드(N카드) 예약.** `KorailClient.reserve_with_discount_card`,
  `build_discount_card_reservation_form`, `KORAIL_DISCOUNT_CARD_DISCOUNT_CODE` (`"153"`),
  `KORAIL_DISCOUNT_CARD_MENU_ID` (`"A2"`). N카드 전용 예약 엔드포인트는 없고 평범한 예약
  라우트를 씁니다(`w4/a.java:93-104`). 기존 `"reserve"` 동의로 게이트합니다.
  **전송한 적 없습니다** — 이 프로젝트가 닿을 수 있는 계정 중 N카드를 가진 것이 없습니다.
  - 라이브로 확인된 성인 1명 폼과 다른 것은 승객 행이 접히는 것과 `txtMenuId` 뿐입니다.
    빌더는 `build_reservation_form` 의 출력에 치환하는 방식이고, 테스트가 두 폼을 순서까지
    비교합니다.
  - **`txtCardNo_1` 에만 끝에 언더스코어가 붙습니다**(`OPsg.java:7-10`). `txtCardNo1` 로 쓴
    예약은 할인 코드만 있고 카드는 없는 예약이 됩니다.
- **할인카드 구매와 기간연장을 동의 게이트가 걸린 mutation 으로 추가했습니다.**
  `KorailClient.register_discount_card`, `extend_discount_card`, 관련 요청·응답 타입과
  `KORAIL_MAX_DISCOUNT_CARD_SECTIONS` (`3`), 그리고 다섯 번째 동의 범주 `"discount_card"`.
  `"reserve"` 재사용이 아닙니다 — 좌석이 아니라 상품을 사는 것입니다.
  **전송한 적 없습니다.**
  - `research.dcntCrdInfo.do` 는 이름과 달리 **구매** 입니다. `lumpStlTgtNo` 와 `rcvdAmt`
    로 답하므로(`NCardReservationDao.java:127-134`) 이 호출이 만드는 것은 정산을 기다리는
    미결제 구매입니다.
  - **열려 있고, 운영자가 확인해야 합니다.** v6.5.0 의 어떤 호출 지점도
    `jrnyInfo`/`apdUsrInfo` 를 채우지 않습니다. 연장 성공 시의 응답과 그 비용도 알 수
    없습니다.
- `KorailHttpClient.get_mutation_query`. 앱이 GET 으로 수행하는 mutation 의 전송 경로입니다.
  `reservation.dcntCrdExtn.do` 는 `@GET` 으로 선언돼 있고 실제로 상태를 바꿉니다
  (`ResearchService.java:65-66`). 잘못 등록한다고 mutation 이 안전해지지 않으므로
  `post_mutation_form` 의 모든 게이트가 그대로 적용됩니다.
- **할인카드(N카드) 읽기 둘.** `get_discount_card_usage_history`,
  `get_discount_card_schedule` 와 관련 모델. **구현했고 NOT live-verified** 입니다 — 닿을 수
  있는 어떤 계정도 N카드를 갖고 있지 않아 두 모양 모두 APK 의 DAO 에서 왔습니다.
  - 카드번호는 사용자가 입력하는 값이 아니라 N카드 승차권 상세가 실어 오는 값이고, 이제
    나타날 수 있는 모든 곳에서 마스킹됩니다.
  - **열네 개 `@Query` 파라미터 중 둘은 보내지 않습니다. 앱이 보내지 않기 때문입니다.**
    고정하지 않고 `KORAIL_OPTIONAL_REQUEST_FIELDS` 에 등록합니다.
  - **카드 상품코드를 내려주는 엔드포인트는 없습니다.** 앱이 보낼 수 있는 값은 전부
    클라이언트 쪽 리터럴입니다.
  - 상태를 바꾸는 `dcntCrd*` 라우트 둘은 읽기 전용 허용목록에 일부러 넣지 않았고, 없다는
    것을 테스트가 고정합니다.
- `RefundTicketDetailResponse.discount_card` 와 `DiscountCardOnTicket`,
  `DiscountCardSection`. 새 라우트가 아니라 이미 받아 놓고 버리던 `dcnt_crd_info` 를 읽는
  것입니다(`dao/refund/TicketDetailDao.java:233`). 구간 목록의 전선 키는 게터 철자가 아니라
  Gson 이 직렬화하는 Java 필드 이름 `appSegList` 입니다(`TicketDetailDao.java:124`).
- **마일리지·포인트 읽기.** `get_korail_point_summary`, `get_mileage_history` 와
  `KORAIL_MILEAGE_*` 선택자 상수 다섯.
- **장바구니 담기를 동의 게이트가 걸린 mutation 으로 추가했습니다.** `add_to_cart`,
  `POST cart.addCartList` (`CartService.java:11-13`), `CartAddRequest`,
  `build_cart_add_form`, 그리고 일곱 번째 동의 범주 `"cart"`. 카드번호를 싣지 않으므로
  `KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 의 원소가 아닙니다. 2026-07-27 손으로
  실검증했습니다 — `SUCC` / `IRZ000002` 가 왔고 그 행을 `get_cart_list` 로 다시 읽었습니다.
- **운임 재계산을 동의 게이트가 걸린 mutation 으로 추가했습니다.** `recalculate_price`,
  `POST certification.PriceReCalculation`, 관련 요청 타입과 여섯 번째 동의 범주
  `"price_recalculation"`. `"payment"` 재사용이 아닙니다 — 결제 동의는 산정된 금액을
  정산하는 것이고 이 라우트는 산정 자체를 다시 씁니다. 전송한 적 없습니다.
  - **여섯 개의 병렬 `List` `@Field` 는 인덱스로 짝지어지며 좌석 하나가 한 행입니다**
    (`a6/C1042B.java:275-283`, `smali/a6.1/B.smali` 에서 확인).
  - **인덱스 키가 아니라 반복 키로 나갑니다.** Retrofit 1.x 가 `Iterable` `@Field` 를 루프
    불변인 이름으로 펼치므로(`RequestBuilder.smali:1537-1601`) 본문이
    `psg_tp_dv_cd=..&psg_tp_dv_cd=..` 입니다.
- **승차권 변경 체인의 읽기 둘.** `get_self_seat_change_info`
  (`TicketService.java:54-56`)와 `get_original_ticket_inquiry`
  (`ResearchService.java:61-63`).
  - `psrmClCd` 는 OPTIONAL 로 등록합니다. 앱이 일반실·특실일 때만 설정하고 그 밖에는
    Retrofit 이 버리기 때문입니다.
  - 원표 조회의 `@FieldMap` 키는 이미 `_` 로 끝나고 여기에 1부터 세는 행 번호가 붙습니다.
    키 집합이 승차권 수에 따라 늘어나므로 이름 집합이 아니라
    `safety.py` 의 `_is_original_ticket_field_order` 로 고정합니다.
  - **`tkCnt` 는 묶음 개수에 고정하지 않습니다.** 앱 자신이 의미를 두고 엇갈립니다 —
    승객 수, 행 수, 하드코딩된 `1` 이 각각 나옵니다.
- **NetFunnel 가상대기실 클라이언트 `KorailNetFunnelClient`.** 게이트에 걸린 연산이
  실패하는 대신 차례를 기다릴 수 있습니다. **기본은 꺼짐이고, 2026-07-26 실서버 프로브로
  절반이 확인됐습니다.** 전선 형식은 네이티브 SDK 의 `<code>:<params>` 이고, 진입 순서는
  `5101` → `5002` → 게이트된 호출 → `5004` 이며, 큐는 호스트 하나가 아니라 여럿의 풀입니다.
  **201 대기 경로(queued path)는 여전히 NOT live-exercised** 입니다 — 그날 서버가 줄을
  세우지 않아서 폴링 루프와 ttl 대기와 두 상한은 오프라인 픽스처로만 덮여 있습니다.
  - **큐는 풀이고 세션은 그 풀의 노드 하나에 삽니다.** `nf.letskorail.com` 은 진입 호출을
    부하분산하는 정문(front door)입니다. 세션을 끝낼 수 있는 것은 그 호출이 떨어진
    노드뿐이고, 모든 응답이 자기 `ip`/`port` 로 그 노드를 알려 줍니다. 이 클라이언트는 모든
    opcode 를 정문으로 보내고 있었으므로 자리 반납이 **절반쯤, 비결정적으로 (half the time,
    non-deterministic)** 실패했습니다.

    ```
    acquire said ip=rnf12.letskorail.com  -> release 503
    acquire said ip=rnf14.letskorail.com  -> release 200
    acquire on nf.letskorail.com (reply said ip=rnf13.letskorail.com)
      release via nf.letskorail.com    -> 503:msg="Wrong Server ID"
      release via rnf13.letskorail.com -> 200:key=&nwait=0&…
    ```

    **`Wrong Server ID` 는 문자 그대로(literal)의 뜻입니다.** 자격증명이나 파라미터
    불평처럼 읽히지만 둘 다 아니고, 큐 노드가 발급한 세션을 정문이 갖고 있지 않다는
    말입니다. 앱은 처음부터 그 이름을 따라갑니다 — `T6/d.makeURL`(`T6/d.java:17-19`)이
    직전 응답의 `getHost()`/`getPort()` 로 URL 을 다시 만들고 그 플래그는 기본
    `false`(`T6/h.java:43`)입니다. 따르지 않으면 잡은 자리의 절반쯤이 새고(leaked), 그것이
    NetFunnel 이 막으려고 있는 일입니다. 그래서 `5101` 은 정문으로, `5002` 와 `5004` 는
    세션을 발급한 노드로 갑니다. 노드는 키와 같은 방식으로 뒤엣것이 앞엣것을
    덮습니다(supersede).
  - **리다이렉트는 믿는 것이 아니라 좁히는 것입니다.** 응답이 고르는 이름은 큐 자신의 풀
    안으로만 받아들입니다 — `rnf<1-99>.letskorail.com`, 소문자, 앞자리 0 없음, 라벨 단위로
    일치, 아니면 정문 자신. 스킴은 `https`, 포트는 `443` 뿐입니다. 규칙 밖은 무엇이든
    **hard error** 이고 정문으로 조용히 되돌아가는 일은 없습니다. 조용한 폴백이 바로 그
    오락가락하는 반납을 만든 것이고, 샌 자리는 아무 소리도 내지 않습니다.
  - **`5101` 의 키는 세션이 아니라 표(ticket)입니다 — 프로브가 드러낸 첫 번째 결함.**
    완료할 수 있는 키는 `chkEnter` 가 발급한 것뿐이라, `acquire` 는 `5101` 이 `nwait=0`
    이라고 해도 항상 `5002` 를 수행하고 매 단계의 키가 앞 단계의 키를 덮습니다(supersede).
    `503` 에는 원인이 둘 있고 전선으로는 구별할 수 없어서 예외 메시지가 둘 다 말합니다.
  - **KORAIL 은 JavaScript 방언을 쓰지 않습니다.** SRT 는 `netfunnel.js` 위의 WebView 라
    브라우저 방언을 보내지만, `korail.apk` 는 STCLab 의 네이티브 안드로이드 SDK(`T6`/`U6`)를
    품고 있어 그중 아무것도 보내지 않습니다. `sid`/`aid` 는 `5101` 에만 실리고, `ttl` 은
    되보내지 않고 얼마나 잘지 정하려고 읽을 뿐입니다.
  - **키는 KORAIL 요청에 절대 실리지 않습니다.** 큐는 호출을 게이트할 뿐 호출에 파라미터를
    더하지 않습니다. 예약·결제·취소·환불이 이전과 정확히 같은 것을 보내는 이유입니다.
  - **기본은 꺼짐이고 생성 시점에 강제합니다.** 성수기용이며, 앱이 성수기 조회 큐
    (`act_8_2`)를 따로 들고 있는 이유도 그것입니다.
  - **대기는 두 겹으로 제한됩니다** — 폴 20회와 60초 중 먼저 오는 쪽. 큐는 재시도가 아니라
    기다림이므로 재시도 로직은 넣지 않았습니다.
  - **자리는 두 경로 모두에서 반납되고, 반납 실패는 예외로 올라갑니다.** 형제 저장소가 키를
    128자로 묶어 두는 바람에 실서버 실행이 드러낼 때까지 모든 자리를 조용히 흘린 적이
    있습니다. 가드는 512자에 둡니다.
- **서버 쪽 실패를 하나의 `KorailAppError` 로 받는 대신 `h_msg_cd` 로 분류합니다.** 새
  타입은 `KorailNoResultsError`(그 아래 `KorailNoDirectTrainError`),
  `KorailSoldOutError`, `KorailSeatUnavailableError`, `KorailReservationRefusedError`,
  `KorailInvalidRequestError`, `KorailNotEntitledError`, `KorailServiceUnavailableError`,
  `KorailAppUpdateRequiredError` 이고 `classify_app_error` 를 함께 내보냅니다. 어느 것이
  재시도 무의미이고 어느 것이 재로그인인지는 README 의 에러 분류표에 있습니다.
  - **기존 코드가 깨지지 않습니다.** 새 타입은 전부 `KorailAppError` 의 하위입니다.
  - **실패를 지어내지 않습니다.** 응답이 실패인지는 여전히 `strResult` 와 앱 자신의
    `WRC000288` 이 정합니다. 경고가 붙은 성공은 여기서도 성공입니다 — `strResult=SUCC` 와
    취소 가능한 진짜 PNR 을 달고 왔던 `WRR664296` 이 테스트로 고정돼 있습니다.
  - **재시도 로직은 넣지 않았습니다.** `reserve` 는 절대 재시도하지 않습니다. 재시도한
    예약은 중복 예약이기 때문입니다.
  - 안티매크로는 코드가 아니었습니다. `BaseDaoHelper.java:59-86` 이 `DynaPath-Result`
    헤더를 읽고 본문의 `message` 를 띄우므로 기존 `KorailDynaPathError` 가 곧 안티매크로
    거절입니다. srtgo_plus 의 `MACRO` 부분문자열 규칙과 srtgo 의 `IRT010110` 은 제3자
    주장으로만 기록하고 채택하지 않았습니다.
  - `[3]인증정보에 문제가 있습니다.` 는 일부러 분류하지 않고 둡니다. 분류하려면 이 변경이
    없애려는 바로 그 한국어 문구 맞추기를 해야 합니다.
- **`reserve` 가 예약 화면의 job type 셋에 모두 닿습니다.** 키워드 전용
  `job_type`(`KorailReservationJobType`) 으로 고르고 기본은 `IMMEDIATE`(`txtJobId="1101"`)
  이라 기존 호출은 바이트 단위로 그대로입니다. **변형 둘은 2026-07-26 에 실서버로
  확인됐습니다** — 매진 열차의 `1102` 는 `IRR000014` 로, `confirm_standby_hold` 는
  `IRZ000003` 으로 답했습니다.
  - `SEAT_DESIGNATED`(`"1103"`)는 좌석을 지정해 잡습니다. `seats`
    는 승객 한 명당 `KorailSeatAssignment` 하나를 받고, 폼은 `txtSrcarCnt`(*좌석* 수) 뒤에
    색인 1부터 `txtSrcarNo{i}`/`txtSeatNo{i}` 를 붙입니다. 보통 hold 는 그 키를 하나도
    보내지 않으므로 srtgo 의 무조건적인 `txtSrcarCnt="0"` 은 앱이 만들지 않는 모양입니다.
    잡을 때 대조하는 것은 재고의 `seat_spec` 과 상세의 `h_seat_no` 이지 `seat_no` 가
    아닙니다.
  - `STANDBY`(`"1102"`)는 예약대기입니다. 자격 조건은 "매진" 이 아니라 검색 행의
    `h_wait_rsv_flg` 가 두 글자 리터럴 `" 9"`(`KORAIL_STANDBY_WAIT_FLAG`)인 것이며, 그것도
    일반실 탭에서만입니다. 예약대기는 **members-only** 이고, 이 클라이언트는 모든 상태
    변경이 로그인된 회원 세션을 요구하므로 구조적으로 만족합니다.
- `confirm_standby_hold`. 예약대기 예약에 필요한 두 번째 호출입니다. `"1102"` hold 가
  `IRR000014` 를 달고 돌아오면 `reservationWait.ReservationWait` 로 좌석등급 변경 동의와
  SMS 필드를 POST 합니다. 전화번호는 SMS 를 켰을 때만, 10자리 또는 11자리로 보내고 그 밖에는
  아예 뺍니다. 새 범주를 만들지 않고 **`reserve` 범주** 를 함께 쓰는 것은, 새 범주를 만들면
  예약대기를 걸기로 옵트인한 호출자가 그것을 끝맺지 못하게 되기 때문입니다.
- **`reserve` 가 임의의 승객 구성을 두 좌석등급 어느 쪽으로든 예약합니다.**
  `KorailPassengerCounts`(어른, 청소년, 어린이, 동반유아, 경로, 1~3급 장애, 4~6급 장애,
  안내견)와 `KorailSeatClass`(일반실 `"1"` / 특실 `"2"`)를 받습니다. 둘 다 키워드 전용이고
  기본값이 일반실 어른 1명이라 기존 호출은 같은 폼을 보냅니다.
  - `txtTotPsgCnt` 는 무릎 위 유아와 안내견을 포함해 모든 행을 더한 값입니다. 구성은 음수가
    아니어야 하고 `KORAIL_MAX_PASSENGERS_PER_RESERVATION`(9) 안이어야 합니다.
  - 할인 승객 행에 할인카드 필드가 따라붙지 않습니다. korail2 와 srtgo 의
    `txtCardCode_`/`txtCardPw_` 는 디컴파일한 앱 어디에도 없습니다.
  - 2026-07-26 예약→취소 왕복으로 실서버 확인했습니다 — 일반실 어른 2명과 특실 어른 1명.
    특실 hold 는 결제 금액이 왜 `h_tot_rcvd_amt` 에서 와야 하는지도 보여 줍니다. 종류가
    섞인 구성은 여전히 정적 근거뿐입니다.
- **과금되는 실카드 결제.** `MutationConsent.real_card_acknowledged`(기본 `False`)와
  `KorailClient.pay_with_card` 입니다. 새 메서드는 `real_card_acknowledged=True` 와
  `fake_card_only=False` 를 둘 다 요구하고, `pay_with_fake_card` 는 그대로 옆에 있으며
  여전히 테스트 카드가 아니면 거절합니다. 기본이 `False` 이므로 이전에 쓰인 consent 는 전과
  정확히 같은 뜻입니다. `pay_with_card` 는 FAIL 에 예외를 올리는 대신 파싱된 결제 봉투를
  돌려줍니다. 그 봉투가 돈에 무슨 일이 있었는지에 대한 유일한 기록이기 때문입니다.
- `scripts/reserve_pay_refund_roundtrip.py`. 실카드로 예약 → 결제 → 환불 왕복을 한 번 도는
  운영자용 스크립트입니다. 환경변수 옵트인 셋이 모두 필요하고 카드는 환경변수에서만
  읽습니다. 계정에 예약이 0건이 아니면 시작하지 않고, PNR 이 생기는 즉시 찍고, 결제 전에
  청구액을 독립된 서버 읽기와 대조하고, 실패하면 복구 명령을 담은 배너를 찍습니다. PAN,
  비밀번호 자릿수, 유효기간, 생년월일은 모든 출력 경로에서 지워집니다. PNR 은 일부러 지우지
  않습니다.
- **환불 사전 확인을 만드는 읽기 셋.** `get_ticket_reservation_detail`
  (`certification.ReservationList`), `get_refund_commission`(`refunds.CommissionView`),
  `get_refund_ticket_detail`(`refunds.SelTicketInfo`). 뒤의 둘을 합치면 `refund` 가 한 번도
  가져 본 적 없는 "얼마가 돌아오고 수수료는 얼마인가" 사전 확인이 됩니다. 참조 클라이언트
  넷 중 어느 것도 이 둘을 구현하지 않았습니다.
- **상태 변경 요청을 위한 consent·safety 토대.** frozen `MutationConsent`(범주별 `allow_*`
  기본 `False`, `dry_run` 기본 `True`, `fake_card_only` 기본 `True`)와 frozen
  `MutationPreview`(생성 시점에 `redact_payload` 를 통과)가 `consent.py` 에 있습니다. 라우트
  등록부가 층을 갖게 됐고, `KORAIL_MUTATION_ROUTE_CATEGORIES` 와
  `assert_mutation_route_category` 가 한 범주의 consent 로 다른 범주의 라우트를 POST 할 수
  없게 합니다.
- **consent 게이트가 걸린 상태 변경 메서드 넷**: `reserve`, `cancel_unpaid_hold`,
  `pay_with_fake_card`, `refund`. 각각 인증된 세션과 자기 범주로 옵트인한 `MutationConsent`
  를 요구하고, 그렇지 않으면 무엇을 만들기 전에 거절합니다. 기본 `dry_run=True` 에서는
  마스킹한 `MutationPreview` 만 돌려주고 아무것도 보내지 않습니다. 읽기 전송 경로
  (`post_form`/`get_json`)는 모든 상태 변경 라우트를 여전히 거절합니다.
- `refund` 를 같은 게이트 전송 경로에 올렸습니다. 완전히 살아 있는 코드이지만 실서버로 돌아
  본 적이 없습니다 — 이 패키지의 가짜카드 결제는 언제나 거절되므로 여기서 결제된 승차권이
  생기지 않습니다. 실서비스에 대해서는 미검증으로 다뤄야 합니다.
- **인증이 필요한 일회성 승차권 참조 읽기 다섯.** 배송 수령인 상세, 승차권 중복 건수, PBP
  인수 명세, 승강장 번호, 최근 배송 이력입니다. 정확한 정적 계약은 `repr` 에서 가려진 타입
  붙은 출처만 받고, 반복되는 `tkRetNo` 의 순서를 개수까지 같게 보존하며, DynaPath 를
  끕니다. 승차권 참조 구현 자체는 실서버 입출력을 쓰지 않았고 상태 변경 능력을 더하지
  않았습니다.
- **정적 근거에서 나온 읽기 묶음들.** P0 열차 읽기 넷(자유석 객차 안내, 안내 좌석 조건,
  좌석배정 일정, 병합좌석 조회), 선물하기 승차권 목록 모드와 정기권 job `a`/`b`/`c` 와
  운임 견적, 고정형·계정형 읽기 넷(다자녀 할인 대상, 고객 여정 정보, MaaS 서비스 상세,
  여행변경 가능일), 리무진버스 읽기 셋. 모두 닫힌 요청 dataclass, 정확한 POST 허용목록,
  `repr` 안전한 frozen 모델, 엄격한 `SUCC` 파서, 합성 전용 픽스처를 갖췄고 DynaPath 는
  꺼져 있습니다. R39 의 NetFunnel 라우트와 R54 는 여전히 쓸 수 없게 두었습니다.
- 타입 붙은 정기권 메뉴·정기권 종류 메뉴·승무원 요청 옵션 읽기. 세션 요구 여부가 확인되지
  않은(session-unverified) 것들이고 호출자가 런타임 구분 코드를 직접 줘야 합니다. 실서버
  검증은 로그인 이후에만 시작합니다.
- **이 패키지에 라이선스가 생겼습니다.** `LICENSE` 가 Apache License 2.0 원문을 담고,
  `pyproject.toml` 이 PEP 639 SPDX 형식으로 선언합니다. 빌드 최소 버전이 `setuptools>=77`
  로 올라간 것은 그 이전 버전이 `license-files` 를 조용히 무시해 라이선스 본문 없는 wheel 을
  만들기 때문입니다. `License ::` 분류자는 함께 쓰지 않습니다. `NOTICE` 를 `LICENSE` 와
  나란히 선언하는 것은 Apache-2.0 §4(d) 가 귀속 고지를 이어 나르도록 요구하기 때문이고,
  두 산출물 모두 두 파일을 싣습니다.
- 소유자와 표준 URL 메타데이터. 철자는 `pyproject.toml` 에만 있고 여기 옮겨 적지 않습니다.
  `[project.urls]` 는 Homepage, Repository, Issues, Changelog 를 고정합니다. 그리고
  `korail_mobile_api.__version__` — `project.version` 과 같은지를 단언하는 테스트가 함께
  있고, `__all__` 에는 일부러 넣지 않았습니다.
- **`tests/test_public_surface_rule.py`.** 공개면이 편리한 이름 하나를 export 하고 싶은
  다음 사람에 의해 되돌려지는 것을 막습니다. 이름 목록을 들고 있지 않고, `ast` 로
  `__init__.py` 에서 `__all__` 의 기대 내용을 유도하며, 공개 메서드 애너테이션의 추이 폐포에
  있는 패키지 정의 타입이 전부 export 되기를 요구합니다.
- `tests/test_default_login_config.py`. 잘못돼 있었고 오프라인으로 확인 가능한 세 가지 —
  DynaPath 켜짐, 앱 모양의 UA, UA 의 단말과 토큰의 단말이 일치하는 것 — 과 인스턴스별 기기
  ID 를 고정합니다. 로그인 성공에 대해서는 아무것도 단언하지 않습니다.
- `build_config_from_env` 를 패키지에서 내보냅니다. 실제 기기 신원을 고정하는 지원되는
  방법이고, 프로세스 사이에서 기기 ID 를 유지하는 유일한 방법입니다.
  `read_credentials_from_env`, `live_enabled`, `run_live_smoke_from_env` 는 내보내지
  않습니다.
- `scripts/README.md`. 커밋된 스크립트 넷 중 셋이 라이브 서버와 통신하고 그중 하나는 돈을
  움직이는데, 어느 것이 어느 쪽인지 저장소 어디에도 적혀 있지 않았습니다. 넷 모두에
  적용되는 규칙(스위치 최소 둘, 자격증명은 환경변수에서만, 호출 간격, 임포트 안전성, 본인
  계정에 대해서만 실행)을 적습니다.
- 문서 사이트. `mkdocs.yml` 이 `docs/` 아래 여섯 쪽을 만들고, API 레퍼런스는 docstring 에서
  생성합니다. 빌드 도구는 `docs` extra 로 들어가므로 런타임 의존성은 늘지 않습니다.

### Changed

- **동작 변경. 맨손 `KorailClient()` 로 로그인할 수 있습니다.** 전에는 되지 않았고, 그래서
  README 의 빠른 시작은 거짓이었습니다. 2026-07-27 실검증에서 기본 `KorailConfig()` 는
  DynaPath 를 끈 채 `User-Agent: korail-mobile-api/0.2.0` 을 보냈고 `login.Login` 이
  `**MACRO ERROR**` 를 돌려줬습니다. 이 실패는 **위장돼 있어서** 읽기 어렵습니다 — 서버가
  매크로 거부를 "원활한 서비스 이용을 위해 앱을 최신 버전으로 업데이트한 뒤…" 로 돌려주고,
  계정과 무관한 읽기는 같은 설정에서 계속 성공하므로 버전 게이트처럼 보입니다. 기본값 셋이
  바뀌었습니다.
  - `KORAIL_USER_AGENT` 가 플랫폼 기본 Dalvik 문자열이 됐습니다. 앱은 UA 를 하드코딩하지
    않고 Retrofit v1 이 `HttpURLConnection` 위에서 돌기 때문입니다(`ExecuteDao.java:7-11`).
    이 값은 DynaPath 토큰의 `dm`·`os` 와 같은 상수에서 유도하므로, 한 요청 안에서 UA 와
    토큰이 다른 단말을 말할 수 없습니다.
  - **DynaPath 가 기본으로 켜집니다.** 이제 모든 클라이언트가 허용된 여섯 경로에
    `x-dynapath-m-token` 을 붙입니다. 어디에 토큰을 보내는지는 그대로이고 보내느냐 마느냐만
    바뀝니다. (Unreleased 에서 다시 옵트인으로 바뀌었습니다.)
  - 기본 토큰 설정은 기기 신원을 `KorailConfig` **인스턴스마다** 생성합니다. 고정된 기기
    ID 는 넣지 않습니다 — `di` 는 단말의 `Settings.Secure.ANDROID_ID` 이고, 모든 설치본이
    공유하는 식별자야말로 이 헤더가 잡으려는 봇 서명입니다. srtgo 의 고정값에 이 저장소가
    이미 제기한 비판이 그것입니다.
- **`scripts/reserve_pay_refund_roundtrip.py` 는 운임 상한 없이는 시작하지 않습니다.**
  `KORAIL_MAX_FARE` 는 "권장" 으로 적혀 있었지만 이 스크립트가 결제하는 금액을 막는 것은
  이것뿐입니다. 값이 없으면 비교를 건너뛰므로, 문서대로 따른 운영자는 상한 없는 실카드
  결제를 돌리고 있었습니다. 이제 결제 경로에서, 카드를 읽기 전에, 로그인 전에
  강제합니다. `--recover` 는 영향을 받지 않습니다.
- `scripts/reserve_pay_refund_roundtrip.py` 는 운임 조회를 만들 수 없을 때 검색 행 자신의
  가격 필드로 열차를 고릅니다. 지어내는 것은 없습니다 — `KORAIL_TRAIN_NO`, 가장 싼 운임
  조회, 검색 행 기준 최저가, 첫 예약 가능 열차 순이고 어느 분기가 실행됐는지 항상 출력에
  나옵니다. 검색 행 값은 곧 청구될 금액으로 읽힐 수 없게 힌트라고 찍습니다. 권위 있는
  금액은 여전히 결제 전에 다시 읽은 값이고, 상한은 여전히 `KORAIL_MAX_FARE` 입니다.
- **문서가 디컴파일된 KORAIL 앱 코드를 그대로 싣지 않습니다.** Java 메서드 본문·smali 와
  Retrofit 인터페이스 선언을 붙여넣었던 두 곳이 이제 관찰한 내용을 서술합니다. 기계 생성
  카탈로그 둘도 예외를 두지 않아 약 660 줄이 더 나왔습니다. 모든 `file:line` 인용과
  바이트코드 수준의 세부는 그대로이므로, 바뀐 것은 근거의 형식이지 근거의 힘이 아닙니다.
  라우트 애너테이션 셀은 그대로 둡니다. 라우트는 클라이언트가 맞춰야 하는 인터페이스입니다.
- 문서의 절대경로에 로컬 사용자명이 남지 않습니다. 14개 전부 저장소 기준 상대경로로 다시
  썼으므로 예외 목록이 없습니다.
- 히스토리 재작성이 남긴 벤더 키 자리표시자가 문장으로 읽힙니다. 자리마다 원래 어떤
  필드였고 왜 값이 없는지 적고, 아직 평문으로 남은 값 하나(GCM sender id — 자격증명이 아니라
  Firebase 프로젝트 *번호*)는 일부러 남긴 것임을 기록합니다.
- `EXCLUDED_API_DOMAINS` 가 `"points-mileage"` 대신 `"points-mileage-write"` 를 담습니다.
  옛 이름은 잔액 읽기까지 막았습니다. 새 이름이 가리키는 다섯은 계속 닿을 수 없습니다 —
  `mlg.lpotAthn.do` 와 `xPoint.XPointView` 는 사용자가 입력한 포인트 **비밀번호** 를 받고
  실패 횟수로 답하므로 화면 제목이 무엇이든 틀린 추측 한 번이 적립 사업자 쪽 상태
  변경이며, 나머지 셋은 등록·적립 쓰기입니다.
  - **`xPoint.MyXPointView` 는 이 프로젝트가 가진 줄 몰랐던 계정 자격 읽기입니다.**
    `h_hdcp_flg` 하나로 앱이 장애인 절 전체를 드러내므로(`MyPageActivity.java:206-212`),
    플래그가 `"Y"` 가 아닌 계정은 두 등록 중 어느 것도 갖고 있지 않습니다. 라이브
    `ERR299943` 의 설명이 될 만한 모양이지만 **발견이 아니라 가설** 입니다.
  - 마일리지 읽기의 페이지 크기는 앱이 하드코딩한 `"20"` 이고, `qryDvVal` 은 코드가 아니라
    드롭다운 **인덱스** 입니다. 기간에는 기본값이 없습니다. 기본값을 주면 페이로드 빌더 안에
    시계를 넣는 셈이기 때문입니다.
- 전송 게이트가 결제 동의에 카드 주장 **하나** 만 있을 것을 요구합니다. 둘 다 설정하지 않은
  경우는 원래대로 거부이고, 둘 다 설정한 경우는 모순으로 거부합니다. 모호한 동의로 결제하는
  것이야말로 이 게이트가 막으려는 실수입니다.
- `ReservationSeatDetail` 은 승객 유형을 `h_psg_tp_cd` 에서 가져옵니다. 어떤 참조
  클라이언트가 쓰는 `h_psg_tp_dv_nm` 은 디컴파일된 앱 어디에도 없고 라이브에서도 관찰되지
  않아 일부러 매핑하지 않습니다. 매핑하지 않은 키는 `raw` 로 닿을 수 있습니다.
- `logout()` 이 로컬 상태를 지우기 전에 맨 `GET` `login.Logout` 으로 서버 세션을
  무효화합니다. 전송 오류나 이미 만료된 세션에서 실패하지 않도록 best-effort 입니다.
  `KORAIL_DYNAPATH_SDK_VERSION` 도 디컴파일된 앱에 맞춰 `v1` 에서 `v1.0.3` 으로
  고쳤습니다. 이 상수가 본문 필드 `sv` 와 `dyn_key` 양쪽의 씨앗입니다.
- R17 의 알려진 HTTP 404 는 재시도·대체·우회 없이 요청 한 번짜리 `KorailTransportError` 로
  둡니다. R17 과 R31 은 로컬 세션을 요구하고, R52 는 세션을 지어내지 않습니다.
- 로그인 응답의 `strCustNo` 는 고객 여정 요청용 세션 고객번호로 `repr` 에서 숨긴 채
  보관합니다. 회원·회원카드 식별자는 대체값이 아닙니다.
- Java Retrofit 이름은 문서용 별칭으로만 두고, `TrainSummary` 편의 연결과 인접한 모든 상태
  변경은 일부러 뺐습니다.
- 기존의 `FAIL`, `P058`, `WRC000288` 오류를 보존한 뒤 P0 메뉴와 리무진의 모든 타입 파서가
  정확한 `strResult=SUCC` 를 요구하도록 좁혔습니다. 리무진 질의는 하위 클래스를 거부하고,
  검증기를 전송 전에 비가상으로 호출합니다.
- 라이브에서 확인된 JSON 정수와 ASCII 10진 문자열 형태의 값을 더 넓은 강제 변환 없이
  정규화합니다.
- **`scripts/verify_distribution.py` 가 PEP 639 메타데이터를 금지하는 대신 검증합니다.**
  `License-Expression`, `License-File`, `Author-email`, `Project-URL` 이 금지 목록에서
  나와 `pyproject.toml` 기반 정확값 검사로 들어갔습니다. `License`, 맨 `Author`,
  `Home-page`, `Download-URL`, `Maintainer`, `Maintainer-email` 은 계속 금지입니다 — 그
  헤더가 있다는 것은 이 pyproject 가 아닌 무언가가 썼다는 뜻입니다. 두 산출물은 선언한
  라이선스 파일을 비어 있지 않은 일반 멤버로도 실어야 합니다.
- `Development Status :: 3 - Alpha` → `5 - Production/Stable`.
- **`MutationNotAllowedError` → `KorailMutationNotAllowedError` 로 이름을 바꿨습니다(파괴적
  변경).** 예외 타입 스무 개 중 패키지 접두사가 없는 유일한 이름이었습니다. 별칭은 남기지
  않습니다. 1.0.0 에서 더한 별칭은 그 자체로 영구 계약이 되며, 지금 바꾸는 이유가 바로 아직
  공짜라는 것입니다.

### Fixed

- `get_ticket_reservation_detail` 가 라이브 성공 본문을 거부했습니다. 성공 형태를 APK 의
  DAO 선언에서 만들었는데 거기서는 모든 필드가 Java `String` 이고, 실제 서버는 좌석 행의
  `h_srcar_no` 를 JSON 숫자로 보냅니다. 같은 이음매에서 나온 세 번째 라이브 발견이라
  필드별로가 아니라 체계적으로 고쳤습니다 — `certification.ReservationList`,
  `refunds.CommissionView`, `refunds.SelTicketInfo` 의 모든 단언된 스칼라가 JSON 문자열과
  JSON 숫자를 함께 받습니다. 앱이 못 느낀 이유는 Gson 의 `nextString()` 이 숫자를 String
  으로 강제하기 때문입니다. 스칼라 자리의 bool, float, 리스트, 객체는 여전히 프로토콜
  오류입니다.
- `parse_reservation_hold_response` 가 예약 목록에서 예약을 다시 읽어내지 못했습니다. PNR
  을 잃었을 때 문서가 안내하는 복구 경로가 바로 그것인데, 목록은 `h_jrny_cnt` 를 정수 `1`
  로 보내고 예약 응답은 `"0001"` 로 보냅니다. 이제 예약·결제 파서의 모든 스칼라가 둘 다
  받아 폼 빌더가 기대하는 문자열로 정규화하고, 같은 관용이 PNR·발권창구 번호·job 시퀀스·
  정산 금액에도 적용됩니다. 이 값들은 서버에 이미 존재할 수 있는 예약을 가리키므로 하나를
  거부하면 그 예약이 붕 뜹니다.
- `scripts/reserve_pay_refund_roundtrip.py` 가 정작 출력해야 할 PNR 을 가리고 있었습니다.
  콘솔 스크러버가 13~19 자리 카드번호 패턴을 아무 텍스트에나 적용했는데 KORAIL PNR 이 10진수
  15자리라, 복구 명령줄 안의 PNR 까지 가려져 식별자 없는 미결제 예약만 남는 셈이었습니다.
  이제 스크러버는 실제로 건네받은 카드 값 네 개만 값으로 치환하고 자릿수 패턴은 적용하지
  않습니다. `redact_payload` 와 패키지의 `CARD_RE` 는 그대로입니다 — 일반 패턴은 알 수 없는
  키 아래의 PAN 으로부터 mutation 페이로드를 지키는 자리에 있을 때 옳습니다.
- 철회된 NetFunnel 주장 둘을 고쳤습니다. Korail 이 NetFunnel 을 전혀 쓰지 않는다는 서술은
  지나쳤습니다 — 앱은 실제로 그 왕복을 배선해 두고 있고, 참인 것은 어떤 Retrofit 요청
  본문도 토큰 필드를 싣지 않는다는 것입니다. `service_1`/`act_6` 게이트를 "아직 구현되지
  않았다" 고 적은 주석도 함께 고쳤습니다. 게이트는 있고, R39 를 막고 있는 것은 등록되지 않은
  라우트입니다.

### Removed

- **여행변경 mutation 체인과 `ticket_change` 동의 범주** — `change_trip_reservation`,
  `rollback_trip_change`, `change_reservation_passengers`,
  `MutationConsent.allow_ticket_change`. 만들었다가 같은 날 거뒀습니다. 실행하려면 결제된
  승차권이 있어야 하고 변경수수료가 나가며 깨끗한 되돌리기가 없어서, 미검증 경로에 돈을
  쓰지 않고는 검증할 방법이 없었습니다. 체인이 시작되는 읽기 둘은 남았습니다. 중간 커밋을
  가져간 사람에게는 **파괴적 변경** 입니다.
- **비회원 오프라인 반환 짝과 비회원 세션** — `verify_offline_refund_ticket`,
  `execute_offline_refund`, `begin_non_member`, `end_non_member`,
  `KorailNonMemberSession`. 역시 만들었다가 같은 날 거뒀습니다. 전제가 종이 승차권 실물이고
  verify 호출이 거기 인쇄된 반환번호를 소모하므로 어느 쪽도 실행해 볼 수 없습니다. 반환번호
  철자들은 `redaction.py` 에 등록된 채로 둡니다 — 민감 키 집합에서 빠진 철자는 무언가가
  그것을 다시 들여오는 날 새어 나갑니다. 같은 조건으로 **파괴적 변경** 입니다.
- **최상위 `__all__` 에서 이름 47개가 빠져 263 → 216 이 됐습니다(파괴적 변경).** 빠진
  이름은 전부 정의된 모듈에서 그대로 임포트할 수 있으므로 이동이지 삭제가 아닙니다.
  달라진 것은 패키지가 *약속하는* 범위입니다. 1.0.0 이후로는 내보낸 이름을 거두면 누군가가
  깨지므로, 표면에는 호출자가 반드시 이름으로 부를 수 있어야 하는 것만 남깁니다.
  - 전송 계층 상수(base URL, 앱 키, API 버전, NetFunnel·DynaPath 상수). 전부 `KorailConfig`
    필드의 기본값으로 닿을 수 있습니다.
  - DynaPath 토큰 기계. `DynapathConfig` 와 `DynapathTokenSettings` 는 `KorailConfig` 의
    필드 타입이라 남습니다.
  - 내부 라우트·정책 표(`KORAIL_MUTATION_ROUTES` 등). 짝인 `KORAIL_READ_ONLY_ROUTES` 는
    애초에 내보낸 적이 없고, 분류의 절반만 공개하는 것은 둘 다 `safety.py` 에 함께 두는
    것보다 나쁩니다.
  - 클라이언트가 대신 호출해 주는 파서. 이들의 *반환* 타입은 모두 그대로 내보냅니다.
  - `redact_mapping` 과 `redact_payload`. `MutationPreview` 가 생성 시점에 마스킹하므로 기본
    동작에서 잃는 것은 없고, 자기 로깅에 쓰려면 `korail_mobile_api.redaction` 에서
    임포트하면 됩니다.

### Security

- 원표 반환번호 네 값이 마스킹 대상이 됐습니다. `ogtkRetPwd` 는 세 경로로 오가며 셋 다
  가려지지 않았습니다. `ogtkSaleWctNo`/`ogtkSaleDd`/`ogtkSaleSqno`/`ogtkSaleDt` 를 함께
  등록합니다 — 반환번호의 4분의 3만 가리면 나머지로 복원되기 때문입니다. 지연증명 튜플,
  정산 행의 `stlCrdNo`/`prepCrdNo`/`apvNo`, `lumpStlTgtNo` 의 두 철자도 등록했습니다.
- `hidDscpNo`, `hidCustNo`, `hidFmlyNo`, `psrm_cl_cd` 가 `SENSITIVE_KEYS` 에 들어갔습니다.
  첫째는 이미 가려지던 `h_cpn_no` 가 나가는 쪽이고, 나머지 셋은 고객번호, 가족 구성원
  일련번호, 이미 가려지던 `psrmClCd` 의 언더스코어 철자입니다.
- `redact_payload` 가 리스트 값을 `str()` 로 뭉개는 대신 원소 단위로 가리고 길이를
  유지합니다. 리스트를 문자열로 만들면 모든 원소가 리스트 자신의 따옴표 뒤로 숨어
  `redact_text` 에 닿지 않습니다.
- `txtCardNo_1..N` 이 `SENSITIVE_KEYS` 에 들어갔습니다. 들어오는 철자는 이미 가려지고
  있었지만 나가는 폼 키는 아니었고, 할인카드 예약의 dry-run 미리보기가 쓸 수 있는 카드번호를
  평문으로 찍었습니다.
- `redact_payload` 가 `txtCpNo` 와 인덱스가 붙은 `txtSrcarNo{i}`/`txtSeatNo{i}` 를
  가립니다. mutation 미리보기가 예약대기 통보번호와 지정 좌석을 드러내지 않습니다.

### 알려진 제약과 넣지 않은 것

- **`cancel_unpaid_hold` 는 환승 예약을 풀지 못합니다.** `h_jrny_cnt` 가 수치로 1 이어야
  하기 때문입니다. 앱에는 그런 제약이 없습니다 —
  `DReservationConfirmActivity.java:269-278` 이 `getH_jrny_cnt()` 를 그대로 `txtJrnyCnt` 로
  넘깁니다. 고치는 방법은 예약 자신의 여정 수를 넘기는 것이지만, 환승 작업의 범위 밖인 취소
  경로를 건드리므로 고치지 않고 보고합니다. **이 수정이 들어오기 전에 보낸 라이브 환승
  예약은 KORAIL 앱이나 웹사이트에서 취소해야 합니다.**
- `pay_with_card` 도 `refund` 도 라이브로 확인된 성공 봉투가 없습니다. 이 저장소에 기록된
  어떤 실행도 실제 결제를 성사시키거나 돈을 돌려받은 적이 없습니다.
- **특실 업그레이드의 `myTicket.reqUpgradeSeat` 는 일부러 넣지 않았습니다.** 요청만 보면
  읽기 같지만 응답이 `lumpStlTgtNo` 를 발급하고(`SpecialRoomUpgradeDao.java:13,19`)
  `procUpgrade` 가 그것을 결제 필드와 함께 받습니다. 결제가 소모할 정산 대상을 만드는 것은
  가격 조회가 아니라 미결제 구매를 만드는 것입니다. mutation 으로도 등록하지 않았습니다 —
  구매 체인의 절반만 있으면 호출자가 정산 대상을 만들어 놓고 정산할 수도 버릴 수도 없게
  됩니다.
- **정기권 구매는 개시하지 않습니다.** 구매 짝(`pass.passReserve` / `pass.passPayIssue`)은
  개시 전 같은 주기 안에서 구현했다가 다시 지웠습니다. 관련 메서드·타입·동의 범주는
  존재하지 않고, 전송한 적도 개시된 버전이 실은 적도 없습니다.
  - **되돌릴 수 없는 돈을 쓰지 않고는 정확성을 증명할 수 없습니다.** 1개월 정기권이 대략
    ₩150,000~₩250,000 이고 이 패키지에는 정기권 환불도 취소 라우트도 없습니다.
  - **비교할 캡처도 없습니다.** 개시된 앱조차 `passPayIssue` 를 낼 수 없습니다 —
    `PaymentActivity.isCommPaymentRequest()` 가 Request 가 와야 할 자리에서 Response 타입을
    검사하므로(`PaymentActivity.java:502-503`) 항상 거짓이고 DAO 가 실행되지 않습니다.
  - **정기권 읽기는 그대로입니다.** `get_pass_menu`, `get_pass_available_dates`,
    `get_pass_schedule` 는 바뀌지 않았습니다.
  - **알아낸 것은 버리지 않고 남깁니다.** README 의 정기권 절이 `passReserve` 필드 20개와
    `passPayIssue` 의 `@FieldMap` 둘, `isCommPaymentRequest()` 결함, 그리고 이 기능을
    되살리려면 무엇을 증명해야 하는지를 기록합니다.
  - `KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 는 이름 있는 집합으로 남습니다. 원소가
    둘이어서가 아니라 `category == "payment"` 가 잘못된 질문이어서 도입한 것이기
    때문입니다.
  - `h_cust_nm`, `usernames`, `h_chg_mg_no` 와 그 모델 속성 이름이 `SENSITIVE_KEYS` 에서
    빠졌습니다. 전부 정기권 결제 폼 때문에 들어온 것들이고 이 패키지에 남은 어떤
    응답·폼·모델도 이 값들을 싣지 않습니다. `h_cust_no` / `customer_no` 는 그대로입니다.
- `certification.ReservationList` 에는 쓰기 성격의 두 번째 Retrofit 오버로드
  `applyDisabilityCertification` 이 있습니다. 여기서는 읽기 오버로드만 옮겼고, 이 라우트의
  `KORAIL_EXACT_REQUEST_FIELDS` 항목이 읽기의 정확한 네 필드를 고정하므로 경로가 같더라도
  쓰기 오버로드의 더 넓은 형태는 전송 전에 거부됩니다.
- `refunds.SelTicketInfo` 는 앱이 선언한 대로 POST 로 보내고 `h_purchase_history` 를
  싣습니다. srtgo 가 보내는 방식(GET, 이 필드 없음)과 다릅니다. 앱의 모든 호출 지점이 이
  플래그를 설정합니다.
- 상태를 바꾸는 승무원 호출 라우트는 제외된 채로 둡니다. 라이브에서 얻은 상수, 좌석지정,
  발권, 그 밖의 상태 변경 기능은 넣지 않았고 새 계약은 합성 픽스처로만 덮입니다.

### 검증 기록

범위를 정해 돌린 실서버 확인이 무엇을 확정했고 무엇을 확정하지 못했는지입니다. 같은 내용이
근거 인용까지 붙어 `docs/verification-record.md` 와 `docs/IMPLEMENTATION_PROGRESS.md` 에
있습니다.

- **서버 규칙 둘은 이 패키지의 결함이 아닙니다.** `ERR299943 예약할인이 지원되지 않습니다`
  는 청소년 단독과 1~3급 장애+안내견 조합을 거절했고 다른 여섯 조합은 받아들여졌습니다. 이
  코드는 디컴파일한 APK 어디에도 없고 폼은 앱과 정확히 같았으므로 요청 모양이 아니라 계정
  자격의 문제입니다. 별개로, hold 응답이 `WRR664296`(주말 할인 안내)을 달고 왔는데 그것은
  취소 가능한 진짜 예약이었습니다. 성공의 기준은 `strResult = SUCC` 와 PNR 입니다.
- **승차권 참조 읽기 셋은 요청 모양까지만 확정됐습니다.** 예약이 0건인 계정으로 셋 다 HTTP
  200 으로 받아들여졌고 DynaPath 거절도 없었습니다. 일부러 틀린 인자에 대해 서버는 키 세
  개짜리 FAIL 봉투로 답했습니다 — `WRG200018`, `WRT100002`, `WRT100124`. 각 코드가 서버가
  실제로 파싱한 필드를 지목하므로 이것이 요청 모양의 근거입니다. **성공 본문은 미확인이고**
  APK 가 선언한 합성 픽스처로만 덮여 있습니다.
- **`reserve` → `cancel_unpaid_hold` → `pay_with_fake_card` 왕복이 실서버에서 끝까지
  돌았습니다.** hold 는 `IRR000018`, 취소는 `IRG000000`, 가짜카드 결제는 `strResult=FAIL`
  과 `WRT200342` 로 거절됐고 청구는 없었습니다. 여기서 두 가지가 드러났습니다 — 실서버 hold
  응답의 `h_jrny_cnt` 는 `"0001"` 이므로 취소 폼 빌더는 1 과 같은 숫자 문자열이면 무엇이든
  받고, 서버가 이미 hold 를 만든 뒤 엄격 파싱이 실패하면 `reserve` 는 PNR 만 실은 최소 hold
  로 물러섭니다.
- **네 `KorailReservationJobType` 이 모두 실서버 hold 를 만들었습니다.** 좌석지정은
  `IRR000014`, 예약대기 확정(`confirm_standby_hold`)은 `IRZ000003` 이었습니다. 여기서 좌석
  식별자의 함정이 확인됐습니다 — 폼에 나가는 것은 `KorailSeatAssignment.seat_no` 이고 서버가
  `h_seat_no` 로 돌려주는 것은 사람이 읽는 표시 `seat_spec` 입니다. 둘을 맞대면 제대로 된
  예약이 틀린 것처럼 보입니다. 입석+좌석은 `txtSrcarCnt` 를 요구하고, 할인카드 예약은
  members-only 자격이 없는 계정에서 `ERR299943` 로 거절됩니다.
- **읽기 표면의 실행 상태는 세어서 관리합니다.** Retrofit 항목 165개 가운데 현재 성공 32,
  실패 10, 미실행 123 입니다. 이 수치는 손으로 적는 대신 `docs/api-status-by-service.md` 의
  서비스별 표에서 유도합니다.
- **인증 읽기 재검증에서 확정된 응답 형태.** R13 은 `WRC800029` 를 돌려주고 `KorailAppError`
  로 올라오며 재시도되지 않습니다. R32 와 현행 R43 은 0행, R45 는 15행, 안전한 열차 검색은
  10행으로 성공했습니다. R52 는 타입 붙은 여정이 없어 `skipped_no_typed_leg` 로 남았고
  R149 는 1행으로 성공했습니다. `strCustNo` 는 로그인 응답에서만 오고 `customer_no` 는
  `repr` 에서 가려집니다. 어느 재검증도 상태변경 라우트를 부르지 않았고 자격증명·식별자·원본
  응답을 남기지 않았습니다.
- **P0 읽기 표면은 오프라인 재생까지 확인됐습니다.** R30 `getFresScar` 는 정확히
  `strResult="SUCC"` 로 파싱됐고, R33 `getGuideSeatCnd` 는 서버가 준 좌석속성에 대해 완전한
  `FAIL` 봉투를 돌려주며 재시도 없이 `KorailAppError` 로 올라왔습니다. R37 과 R51 은
  미실행입니다. 저장한 원본을 오프라인으로 재생하면 27개가 파싱되고 예상된 `KorailAppError`
  하나가 나며 예상 밖 실패는 0입니다.

## 0.2.0 - 2026-07-14

- Added the static R20 pass-schedule candidate read with a closed
  caller-supplied request, exact DynaPath-disabled form, strict `SUCC` parser,
  and frozen repr-safe nested train models. A conservative login gate remains
  while the server session requirement is unverified; reservation and payment
  calls stay excluded.
- Added authenticated typed car-list and physical-seat inventory reads for the
  fixed main-menu/general-room contract.
- Registered only the two exact read-only POST forms, with validation before
  Sid generation or transport and DynaPath disabled on both routes.
- Added frozen repr-safe response models, strict synthetic-fixture parsers, and
  a separately opted-in bounded evidence command that persists sanitized
  statuses, call counts, bounded counts, and type-presence booleans only.
- Accepted live-evidenced missing floor values, empty window collections, and
  repeated seat labels, plus statically evidenced empty car containers and
  strict numeric strings, while preserving response order.

## 0.1.0 - 2026-07-14

- Prepared the existing installable, typed, read-only KORAIL mobile API client
  for reproducible internal builds and offline verification.
- Retained the 25-route safety boundary and its 28 public client methods;
  mutation operations remain excluded.
