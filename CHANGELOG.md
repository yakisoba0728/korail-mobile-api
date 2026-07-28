# Changelog

## Unreleased

### Changed

- **DynaPath 는 이제 명시적으로 켜야 한다.** `KorailConfig()` 의 기본값이 꺼짐이 되고,
  켜는 것은 `KorailConfig(enable_dynapath=True)` 라고 말한 호출자뿐이다. 이 토큰은
  자동화 탐지를 통과하기 위한 값이라 보낼지 말지를 패키지가 대신 정하지 않는다.
  1.0.0 은 이것을 기본으로 켰고, 그때는 인자 없는 `KorailClient()` 로 로그인이
  되게 만드는 것이 목적이었다.
- 켜지 않은 채 `login.Login` 을 부르면 요청이 나가기 전에 새 예외
  `KorailDynaPathRequiredError` 로 막히고, 메시지가 `enable_dynapath=True` 와
  `build_config_from_env()` 를 직접 가리킨다. 그냥 헤더를 빼고 보내면 서버가 대신
  거절하는데 그 거절이 "앱을 최신 버전으로 업데이트"로 위장돼 오므로, 설정 문제가
  버전 문제로 오진된다 — 그 오진은 이 저장소에서 실제로 한 번 일어났다.
- **막는 경로는 허용목록 전체가 아니라 `DYNAPATH_REQUIRED_PATHS` 하나다.** 토큰 없이
  거절이 관측된 것은 `login.Login` 뿐이고 검색을 비롯한 읽기는 토큰 없이 성공한 것이
  관측됐다. 관측되지 않은 것까지 막으면 잘 되던 읽기를 이 패키지가 끊는 셈이라,
  근거가 있는 하나만 요구한다. 다른 경로에서 거절이 관측되면 그때 추가한다.
- `enable_dynapath` 는 필드 목록 **맨 끝** 에 붙였다. `dynapath` 는 여덟 번째 위치
  인자로 남아 있고, 중간에 끼웠다면 이미 위치 인자로 쓰던 호출의 뜻이 조용히 바뀌었을
  것이다. `tests/test_public_contract.py` 가 그것을 잡았다.

### Added

- `KorailDynaPathRequiredError` — 토큰이 필요한 경로를 꺼진 설정으로 불렀을 때.
  서버가 거절한 `KorailDynaPathError` 와 다르다. 이쪽은 아직 아무것도 보내지 않았다.
- `enabled_dynapath_config()` — `enable_dynapath=True` 가 내부에서 부르는 것.
  `DynapathConfig` 를 직접 구성할 때 쓴다.
- `korail_mobile_api.constants.DYNAPATH_REQUIRED_PATHS`. 형제인
  `DYNAPATH_ALLOWLIST_PATHS` 와 마찬가지로 전송 계층 상수라 최상위에 올리지 않는다.

이 문서는 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르고,
이 프로젝트는 [유의적 버전](https://semver.org/lang/ko/)을 따른다.
1.0.0 이전 기록은 당시 형식·언어 그대로 보존한다.

## 1.0.0 - 2026-07-27

### Added

- `scripts/README.md`. 커밋된 스크립트 넷 중 셋이 라이브 서버와 통신하고 그중 하나는 돈을
  움직이는데, 어느 것이 어느 쪽인지 저장소 어디에도 적혀 있지 않았다.
  `capture_live_read_surface.py` 는 테스트 주석에서만 언급됐다. 이 문서는 넷 모두에
  적용되는 규칙(스위치 최소 둘, 자격증명은 환경변수에서만, 호출 간격, 임포트 안전성, 본인
  계정에 대해서만 실행)을 적고, 변수는 중복해 적는 대신 각 스크립트의 docstring 을 가리킨다.
- `build_config_from_env` 를 패키지에서 내보낸다. **실제** 기기 신원
  (`KORAIL_DYNAPATH_DEVICE_ID` / `_OS_VERSION` / `_DEVICE_MODEL`)을 고정하는 지원되는
  방법이고, 여기서는 아무 상태도 저장하지 않으므로 프로세스 사이에서 기기 ID 를 유지하는
  유일한 방법이다. `read_credentials_from_env`, `live_enabled`,
  `run_live_smoke_from_env` 는 내보내지 않는다. 앞의 하나는 호출자의 자격증명이 어디 있어야
  하는지에 대한 의견을 패키지가 주장하게 만들고, 나머지 둘은 이 저장소 자신의 스모크
  발판이다.
- `tests/test_default_login_config.py`. 잘못돼 있었고 오프라인으로 확인 가능한 세 가지 —
  DynaPath 켜짐, 앱 모양의 UA, 그리고 UA 의 단말과 토큰의 단말이 일치하는 것 — 과 인스턴스별
  기기 ID 를 고정한다. 로그인 성공에 대해서는 **아무것도** 단언하지 않는다. 그것은 오프라인
  으로 확인할 수 없고 어디에서도 주장하지 않는다.
- 장바구니 담기를 동의 게이트가 걸린 mutation 으로 추가했다. `KorailClient.add_to_cart`,
  `POST cart.addCartList` (`CartService.java:11-13`), `CartAddRequest`,
  `build_cart_add_form`. 공통 세 필드 외에 요청 필드는 `hidPnrNo` 하나이며
  `AddCartDao.java:9-24` 와, 별도로 `AddCartDao$AddCartRequest.smali` /
  `CartService.smali` 로 확인했다. `get_cart_list` 가 이미 장바구니를 읽고 있었고 이것이 쓰는
  쪽이다. DAO 의 응답 타입이 맨 `BaseResponse` 라 `add_to_cart` 는 전용 응답 타입 대신 파싱
  하지 않은 봉투를 돌려준다. `extend_discount_card` 와 같다. 2026-07-27 손으로 실검증했다.
  잡아둔 PNR 이 깨끗이 담겼고 `SUCC` / `IRZ000002` 가 왔으며 그 행을 `get_cart_list` 로 다시
  읽었다. 이 저장소의 어떤 스크립트나 테스트도 이것을 보내지 않는다.
- 일곱 번째 mutation 동의 범주 `"cart"` 와 기본값 `False` 인
  `MutationConsent.allow_cart` 플래그. `"reserve"` 를 재사용하지 **않은** 것은 의도다. 이
  호출이 다루는 예약은 이미 존재하고, 호출 자체는 이 패키지가 관찰할 수 있는 무언가를
  만들지도 없애지도 않는다. 카드번호를 싣지 않으므로
  `KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 의 원소가 아니다.
- 승차권 변경 체인의 읽기 둘. 읽기 전용 경계가 60 라우트가 됐고 `KorailClient` 는 공개
  메서드 77개를 노출한다. 로그인·읽기 64개에 동의 게이트가 걸린 mutation 13개다.
  - `get_self_seat_change_info` — `POST self.seatChgInfo.do`
    (`TicketService.java:54-56`, `TicketService.smali:280-325`). 필드 여덟 개.
    `psrmClCd` 는 OPTIONAL 로 등록한다. `TCSOptionsActivity.java:135-138` 이 일반실(`"1"`)
    이나 특실(`"2"`)일 때만 설정하고 (`K4/o.java:7-8`, `K4/o.smali:34-82`) 그 밖에는
    Retrofit 이 버리기 때문이다. `trnNo` 는 0으로 채우지 않고 그대로 넘긴다. `:132` 가
    `h_trn_no` 를 있는 그대로 복사한다.
  - `get_original_ticket_inquiry` — `POST research.tripChgOgtk.do`
    (`ResearchService.java:61-63`). `@FieldMap` 키는
    `ROrtg.OGTK_SALE_WCT_NO`/`OGTK_SALE_DD`/`OGTK_SALE_SQ_NO`/`OGTK_RET_PWD`
    (`ROrtg.java:8-11`, `ROrtg.smali:20-26`)로 각각 이미 `_` 로 끝나고, 여기에 1부터 세는
    행 번호가 붙는다. 그래서 `ogtkSaleWctNo_1`, `ogtkSaleDd_1` 같은 식이다. 키 집합이
    승차권 수에 따라 늘어나므로 이름 집합이 아니라 `safety.py` 의
    `_is_original_ticket_field_order` 로 고정한다.
    - **`tkCnt` 는 묶음 개수에 고정하지 않는다.** 그리고 같은 이름을 문자열로 쓰는 이웃
      `tk.plfNo.do` 와 달리 `int` 로 보낸다 (`ResearchService.smali:613`, `I`). 앱 자신이
      의미를 두고 엇갈린다. `TCBookingActivity.java:179` 는 승객 수를,
      `PushHistoryActivity.java:357` 은 행 수를, `SeatSearchActivity.java:615` 는
      `f29962H.size()` 개 행에 대해 하드코딩된 `1` 을 보낸다. `tkCnt == N` 검사는 셋 중 둘을
      거부하게 된다.
    - **인덱스 키의 순서는 이 패키지의 선택이다.** 앱은 Retrofit 에 `HashMap` 을 넘기므로
      (`OgTkInquiryDao.java:15,52`) 와이어 순서가 정해져 있지 않고, 앱의 호출 지점끼리도
      같은 순서로 넣지 않는다. `ROrtg` 선언 순서대로 승차권 단위로 묶는 것이 결정적이다.
- 운임 재계산을 동의 게이트가 걸린 mutation 으로 추가했다. `KorailClient.recalculate_price`,
  `POST certification.PriceReCalculation` (`CertificationService.java:35-37`),
  `PriceRecalculationRequest`/`PriceRecalculationRow`,
  `build_price_recalculation_form`. 결제 화면에서 할인 선택이 바뀐 뒤, 이미 잡아둔 PNR 의
  가격을 다시 매긴다. 전송한 적 없고 라이브로 열려 있지도 않다.
  - **여섯 개의 병렬 `List` `@Field` 는 인덱스로 짝지어지며 좌석 하나가 한 행이다.**
    `k2()` (`a6/C1042B.java:275-283`)는 `DiscountPriceParams[]` 하나를 도는 단일 루프로
    같은 원소의 필드 하나씩을 여섯 `ArrayList` 에 넣는다. 그래서 여섯 리스트의 *i* 번째
    원소가 모두 좌석 *i* 의 것이다. jadx 출력이 아니라 `smali/a6.1/B.smali` 에서 확인했다.
    다자녀 변형(`a6/C1041A.java:57-80`)은 행을 다르게 만들지만 같은 `k2()` 를 부른다.
  - **인덱스 키가 아니라 반복 키로 나간다.** Retrofit 1.x 는 `Iterable` `@Field` 를 루프
    안에서 `addField(name, element)` 로 펼치는데 이름은 루프 불변이다
    (`RequestBuilder.smali:1537-1601`). 그래서 본문이 대괄호나 접미사 없이
    `psg_tp_dv_cd=..&psg_tp_dv_cd=..` 이다. 빌더는 리스트 값을 돌려주고, httpx 가 똑같이
    인코딩하며, mutation 전송 게이트는 바꿀 필요가 없었다.
  - `hiduserYn`/`hidCustNo` 는 비회원일 때만 보낸다 (`a6/C1042B.java:290-293`). Retrofit 은
    null `@Field` 를 빼므로 회원의 폼은 열네 키가 아니라 열두 키다.
- 여섯 번째 mutation 동의 범주 `"price_recalculation"` 과
  `MutationConsent.allow_price_recalculation` (기본 `False`). `"payment"` 를 재사용하지
  **않은** 것은 의도다. 결제 동의는 이미 산정된 금액을 정산하는 것을 허가하는데 이 라우트는
  그 산정 자체를 다시 쓴다. 둘을 합치면 금액을 결제해도 된다는 동의가 금액을 바꿔도 된다는
  허가가 된다.
- 병합예약. `KorailClient.reserve_merge`, `build_merge_reservation_form`,
  `is_merge_eligible`, `KorailReservationJobType.MERGE_STANDING` (`"1202"`),
  `KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE` (`"21"`),
  `KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE` (`"22"`),
  `KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`, `TrainSummary.merge_seat_application_flag`
  (`h_yms_apl_flg`).
  **병합은 한 열차를 중간역에서 나눠 두 구간의 좌석을 다르게 잡는 것이지 환승이 아니다.**
  좌석 연결역 선택 /
  "구간을 좌석+좌석 또는 좌석+입석으로 연결하여 이용하실 수 있습니다"
  (`res/values/strings.xml:702,577`). 탑승은 한 번이다.
  - `K4/e` 의 코드는 바이트코드(`analysis/apktool/smali/K4/e.smali:31-55`)에서 풀었다.
    **네 멤버 중 셋이 jadx 에서는 값만 같은 무관한 상수로 보이기** 때문이다. `TRANSFER` 는
    `TicketSelfCheckinStatusActivity.CHECKIN_STATUS_EXCEED` 로, `STANDING_SEAT_1` 은
    `I4.a.BEFORE_DEPARTURE` 로 나온다. 직통 `11`, 환승 `14`, 병합 선행 `21`, 병합 후행 `22`.
  - 병합은 예약 **둘**이다. 첫째는 `txtJobId="1202"` 만 다르고 나머지는 그대로인 평범한 직통
    폼이고 (`DirectInquiryActivity.java:448-451`, 태그는 `a5/u.java:394-397` 에서 설정),
    둘째는 그것을 같은 열차 위의 두 여정으로 바꾼다. 그 사이에 서버가 있다. KORAIL 이 첫
    예약의 메시지 본문에 리터럴 `<중간연결역 변경>` (`strings.xml:2018`)을 넣고, 확인 화면의
    span 표(`res/values/arrays.xml:421-438`, `K6/C5956a.java:74-77`)가 그 리터럴을 병합을
    시작하는 탭으로 만든다. 제안하는 쪽은 KORAIL 이지 클라이언트가 아니다.
  - 병합 폼은 `C5/a.java` 의 여정 루프가 아니라 `DirectInquiryActivity.java:576-601` 이
    만들고, 환승과 네 군데에서 갈린다. 넷 다
    `analysis/apktool/smali/…/DirectInquiryActivity.smali:5580-6010` 에서 다시 읽었다.
    `txtJrnyTpCd{i}` 가 루프 **인덱스**를 키로 삼아 두 구간이 달라지고(`21` 다음 `22`),
    환승은 양쪽 모두 `14` 다. `txtStndFlg` 는 `"Y"` 로 박힌다. 2구간의 실 등급은 구간마다
    읽는 대신 1구간의 것을 복사한다. 그리고 `setArvTm` 호출이 아예 없어서 `arvTm_2` 가
    존재하지 않고 `arvTm_1` 에는 입석 예약의 **전 구간** 도착시각이 그대로 남는다. 마지막
    항목 때문에 `build_merge_reservation_form` 이 나뉜 두 구간과 함께 입석 예약의
    `TrainSummary` 를 받는다. 그 낡은 값이 실제로 와이어에 실린다.
  - `reserve_merge` 는 자신이 대체하는 입석 예약을 취소하지 않는다. 앱은 취소한다. 그 취소는
    `"cancel"` 동의 아래의 `cancel_unpaid_hold` 이고, `"reserve"` 게이트가 걸린 메서드 안에서
    그것을 수행하면 예약 동의가 살아 있는 PNR 을 풀 수 있게 된다.
  - 예약 라우트를 건드리는 이유는 이 기능이 예약 라우트이기 때문이다. 같은 경로, 같은
    `"reserve"` 범주, 새 `txtJobId` 값 하나와 새 빌더 하나다. 기존 호출은 바이트 단위로
    동일하다. 계약 테스트가 라이브로 확인된 성인 1명 폼을 다시 만들어 키 단위로 비교한다.
  - **전송한 적 없다.** 이 기능의 어떤 폼도 KORAIL 에 닿은 적이 없다.
- `KorailClient.reserve_with_discount_card` 와 `build_discount_card_reservation_form`,
  그리고 `KORAIL_DISCOUNT_CARD_DISCOUNT_CODE` (`"153"`),
  `KORAIL_DISCOUNT_CARD_MENU_ID` (`"A2"`).
  **예약은 할인카드를 실을 수 있고, 그것을 평범한 예약 라우트로 한다.**
  `w4/a.java:93-104` 는 평범한 `ReservationRequest` 를 만든다. 유일한 호출자인
  `SeatAssignBookingActivity.java:153-163` 이 그것을 `NCardDirectInquiryActivity` 에
  넘기고, 그 상위 클래스가 평범한 `ReservationDao` (`c5/b.java:128-138`)로
  `certification.TicketReservation` (`CertificationService.java:52-54`)에 POST 한다. N카드
  전용 예약 엔드포인트는 없다. N카드 승객 블록이 있을 뿐이다.
  - 라이브로 확인된 성인 1명 일반실 폼과 다른 것은 정확히 둘이다. 승객 행 여덟 개가
    `txtTotPsgCnt="1"`, `txtCompaCnt1="1"`, `txtPsgTpCd1="1"`, `txtDiscKndCd1="153"`,
    `txtCardNo_1=<card>` (`w4/a.java:96-101`)로 접히고, `txtMenuId` 가 `"A2"` 가 된다
    (`SeatAssignBookingActivity.java:159`). 나머지 — 여정 블록, 좌석 블록, `txtJobId`,
    `txtStndFlg`, `hidFreeFlg`, `txtGdNo` — 는 동일하다. 앱이 같은 코드로 쓰기 때문이다
    (`c5/b.java:42-77`). 빌더는 `build_reservation_form` 의 출력에 **치환**하는 방식으로
    작성해 그것이 구조적으로 참이 되게 했고, 테스트가 두 폼을 순서까지 키 단위로 비교한다.
  - **`txtCardNo_1` 에만 끝에 언더스코어가 붙고 이웃 셋에는 붙지 않는다**
    (`OPsg.java:7-10`). `txtCardNo1` 로 쓴 예약은 할인 코드만 있고 카드는 없는 예약이 된다.
  - `passengers` 인자도 `seat_class` 인자도 없다. 앱이 둘 다 제공하지 않는다.
    `w4/a.java:97-98` 이 승객 한 명을 하드코딩하고 `:88` 이 일반실을 박는다.
  - 기존 `"reserve"` 동의로 게이트한다. 이것이 곧 예약 라우트이기 때문이다.
    **전송한 적 없다.** 이 프로젝트가 닿을 수 있는 계정 중 N카드를 가진 것이 없다.
- 할인카드(N카드) 구매와 기간연장을 동의 게이트가 걸린 mutation 으로 추가했다.
  `KorailClient.register_discount_card`, `KorailClient.extend_discount_card`,
  `DiscountCardPurchaseRequest`, `DiscountCardSectionRequest`,
  `DiscountCardAdditionalUser`, `DiscountCardTicket`, `DiscountCardPurchaseResponse`,
  `parse_discount_card_purchase_response`, `KORAIL_MAX_DISCOUNT_CARD_SECTIONS` (`3`).
  **전송한 적 없고, 이 저장소의 어떤 라이브 경로도 이것을 전송할 수 없다.**
- 다섯 번째 mutation 동의 범주 `"discount_card"` 와 기본값 `False` 인
  `MutationConsent.allow_discount_card` 플래그. 추가적이다. 이전에 작성된 모든 동의는
  전과 똑같은 의미를 유지한다. `"reserve"` 의 재사용이 아니다.
  `research.dcntCrdInfo.do` 는 좌석이 아니라 상품을 사는 것이고, 열차 예약에 옵트인한
  사람이 할인카드 구매에 옵트인한 것은 아니다.
- `KorailHttpClient.get_mutation_query`. 앱이 GET 으로 수행하는 mutation 의 전송 경로다.
  `reservation.dcntCrdExtn.do` 는 `@Query` 매개변수 일곱 개와 함께 `@GET` 으로 선언돼 있고
  (`ResearchService.java:65-66`) 실제로 상태를 바꾼다. POST 로 등록했다면 코드는 줄었겠지만
  허용 목록이 앱이 보내지 않는 요청을 서술하게 된다. 잘못 등록한다고 mutation 이 안전해지지
  않는다. `post_mutation_form` 의 모든 게이트가 그대로 적용된다. 동의, dry-run 거부, 정확한
  `(method, path)` 쌍에 대한 `assert_mutation_route`, 라우트·범주 교차 확인이다.
  - `research.dcntCrdInfo.do` 는 이름과 달리 **구매**다. `lumpStlTgtNo` 와 `rcvdAmt` 로
    답하고 (`NCardReservationDao.java:127-134`) 앱이 그 대상 번호를 결제 화면에 넘긴다
    (`SectionNCardInquiryActivity.java:213-257`). 즉 이 호출이 만드는 것은 정산을 기다리는
    미결제 구매다.
  - 두 `@FieldMap` 은 DAO 자신의 인덱스 키 철자로 펼친다
    (`NCardReservationDao.java:74-124`). `jrnyCnt` + `jrnyTpCd_N` / `runDt_N` / `trnNo_N` /
    `dptRsStnCd_N` / `arvRsStnCd_N`, 그리고 `apdUsrCnt` + `custMgNo_N` / `apdCustName_N` /
    `apdCustTeln_N`. `mCustomData` 는 일부러 뺐다. `executeDao` 에 전달되지 않고 (`:180`)
    와이어에 닿지 않는다.
  - **열려 있고, 운영자가 확인해야 한다.** v6.5.0 의 어떤 호출 지점도
    `jrnyInfo`/`apdUsrInfo` 를 채우지 않는다. 채울 세터만 있다. 1구간 카드도 구간을 보내야
    하는지, 1인용 카드에서 `apdUsrCnt` 를 빼는 대신 `"0"` 으로 보내야 하는지는 알 수 없다.
    `dcntCrdExtn.do` 의 DAO 응답 타입이 맨 `BaseResponse` 라, 연장 성공 시의 응답과 그
    비용도 알 수 없다.
- `RefundTicketDetailResponse.discount_card` 와 `DiscountCardOnTicket`,
  `DiscountCardSection`. 새 라우트도 새 메서드도 아니다 — `SelTicketInfo` 가 이미
  `TicketDetailDao.TicketDetailResponse` 를 돌려주고, 읽는 "승차권" 자체가 할인카드일
  때 그 안에 `dcnt_crd_info` 가 실려 온다(`dao/refund/TicketDetailDao.java:233`).
  패키지는 그 객체를 이미 받아 놓고 버리고 있었다.
  - 할인카드 표면의 나머지 전부가 여기서 시작한다. 카드번호는
    `get_discount_card_usage_history` 의 유일한 입력이고, 구간 행은
    `get_discount_card_schedule` 의 역 **이름** 이 나오는 곳이며,
    `h_dcnt_crd_trm_extn_psb_flg` 는 앱에서 기간연장을 열어 주는 유일한 값이다
    (`Y4/C0907b.java:301` → `Y4/Q.java:1013-1026`).
  - 구간 목록의 전선 키는 `appSegList` — Gson 이 직렬화하는 Java **필드** 이름이다
    (`TicketDetailDao.java:124`). 게터 철자는 `getAppSeg_info()` 이고 전선 이름이
    아니다. 게터를 따랐다면 구간을 하나도 찾지 못하면서 조용히 성공하는 파서가
    됐을 것이다.
- 마일리지·포인트 **읽기**와 그중 하나가 드러내는 복지 자격.
  `KorailClient.get_korail_point_summary` 와 `KorailClient.get_mileage_history`,
  그리고 `KorailPointSummaryResponse`, `MileageHistoryRequest`,
  `MileageHistoryEntry`, `MileageHistoryResponse` 와 `KORAIL_MILEAGE_*` 선택자 상수
  다섯. 읽기 전용 경계가 58 라우트가 됐다.
- 할인카드(N카드) 읽기 — `KorailClient.get_discount_card_usage_history` 와
  `KorailClient.get_discount_card_schedule`, 그리고
  `DiscountCardScheduleRequest`, `DiscountCardUsage`,
  `DiscountCardUsageListResponse`, `DiscountCardScheduleTrain`,
  `DiscountCardScheduleResponse`. 읽기 전용 경계가 56 라우트가 됐다.
  **구현했고 NOT live-verified** — 이 프로젝트가 닿을 수 있는 어떤 계정도 N카드를
  갖고 있지 않아서, 두 모양 모두 관측된 본문이 아니라 APK 의 DAO 에서 왔다.
  - `GET ticket.dcntCrdUseQry.do`(`ResearchService.java:51-52`)는 식별자 하나
    `dcntCrdNo` 만 받고, 그 카드번호를 사용자가 입력하는 일은 없다. N카드 승차권
    자신의 상세 응답이 `dcnt_crd_info.h_dcnt_crd_no` 로 싣고 오는 것을
    `Y4/C0907b.java:303` 이 intent extra 에 넣으면
    `TicketNCardHistoryActivity.java:138,109` 가 그대로 `setDcntCrdNo` 로 되읽는다.
    그 번호는 이제 나타날 수 있는 모든 곳에서 마스킹된다.
  - `GET research.dcntCrdScheduleView.do`(`ResearchService.java:54-55`)는 보통의
    열차 검색이 아니다. N카드는 고정된 구간 한 개에서 세 개까지에 대해 팔리고, 이
    라우트는 "이 구간에서 이 카드가 덮는 열차는 무엇인가"에 답한다. 역코드가 아니라
    카드 상품으로 키가 걸리는 이유가 그것이다.
  - **열네 개 `@Query` 파라미터 중 둘은 보내지 않는다. 앱이 보내지 않기
    때문이다.** 두 빌더(`u4/b.java:52-65`, `:67-81`) 어느 쪽도 `setQryPgNo` 를
    부르지 않고, 1구간 빌더는 `setUseTrmDno` 도 부르지 않아 Retrofit 이 null 을
    떨군다. 고정하지 않고 `KORAIL_OPTIONAL_REQUEST_FIELDS` 에 등록하는 것은, 그
    둘을 실은 요청도 똑같이 규격에 맞기 때문이다 — 앱 자신의 페이징 신호는 응답의
    `fllwPgExt` 다(`SectionNCardInquiryActivity.java:406-408`).
  - `dcntCrdKndCd` 는 앱 전체에서 값이 정확히 둘이다. `u4/b.java:60-61` 이 원래의
    1구간 상품 둘(`B2N18120402`, `B2N18120403`)에 `"B2N"` 을, 나머지 전부에 `"MMM"`
    을 보내고 `:76` 은 `"MMM"` 을 하드코딩한다. `DiscountCardScheduleRequest.for_card`
    가 그 규칙을 그대로 옮긴 것이다.
  - **카드 상품코드를 내려주는 엔드포인트는 없다.** 앱이 보낼 수 있는
    `dcntCrdKndMgNo` 는 전부 클라이언트 쪽 리터럴이고
    (`NCard1SectionBookingActivity.java:28`, `NCard2SectionBookingActivity.java:34`,
    `NCard3SectionBookingActivity.java:28`, `q5/ViewOnClickListenerC6267a.java:73,76`),
    `pass.passMenu.do` 는 코드 목록이 아니라 Activity 를 고르는 `detailType` 문자열만
    돌려준다.
  - 상태를 **바꾸는** `dcntCrd*` 라우트 둘 — `research.dcntCrdInfo.do` 와
    `reservation.dcntCrdExtn.do` — 은 읽기 전용 허용목록에도
    `KORAIL_MUTATION_ROUTES` 에도 일부러 넣지 않았다. 없다는 것을 테스트가 고정한다.
- 환승 검색과 환승 예약 — `KorailClient.search_transfer_trains`,
  `KorailClient.search_trains_with_transfer_fallback`,
  `KorailClient.reserve_transfer`, 그리고 `TransferItinerary`,
  `TransferSearchResult`, `pair_transfer_itineraries` 와 확정된 코드 넷
  `KORAIL_DIRECT_ITINERARY_CODE`/`KORAIL_TRANSFER_ITINERARY_CODE`(`"1"`/`"2"`),
  `KORAIL_DIRECT_JOURNEY_TYPE_CODE`/`KORAIL_TRANSFER_JOURNEY_TYPE_CODE`
  (`"11"`/`"14"`), `KORAIL_MAX_JOURNEY_LEGS`(`2`). 예약이 더 이상 한 다리 전용이
  아니다. **구현했고 NOT live-verified** — 여기의 무엇도 KORAIL 로 보낸 적이 없다.
  - 앱은 두 경우에 요청 빌더 하나를 쓴다. `C5/a.java:52-119`(`N0`)는 열차 배열을
    도는 반복문이고, 배열의 **길이** 가 모든 것을 정한다. `txtJrnyCnt` 는 `:55` 에서
    `(length == 1 ? "1" : "2")` 이고, 반복문이 `i + 1` 에 쓰므로 여정 색인은 1부터이며,
    `OJrny` 키 열여섯 개가 다리마다 반복된다. `build_reservation_form` 은 이제 다리
    나열 코어를 한 다리로 부르는 것이고 `build_transfer_reservation_form` 은 같은
    코어를 두 다리로 부르는 것이라서, **한 다리짜리 폼은 키 순서까지 바이트 단위로
    이전과 같다** — 그것을 믿는 대신 계약 테스트가 키 56개를 순서째로 고정한다.
  - 코드 넷은 가정이 아니라 **바이트코드** 에서 읽었다. `K4/d` 는 `"1"`/`"2"` 이고
    (`smali/K4/d.smali:36,64`) 같은 두 값으로 서로 무관한 일 셋을 한다 — 검색
    `radJobId`, `txtJrnyCnt`, 그리고 `txtJrnySqno` 의 씨앗. `K4/e` 는 `"1"`/`"2"` 가
    **아니다**. DIRECT 가 `"11"`(`smali/K4/e.smali:40`), TRANSFER 가
    `"14"`(`smali/K4/e.smali:68`) 이며, jadx 는 값이 같은 무관한 상수 뒤에 이것을
    숨긴다. `S4/O.getSequenceNo` 는 `DecimalFormat("000")` 이라 순번은 전선에
    `"001"`/`"002"` 로 닿는다.
  - **환승의 두 다리 모두 `txtJrnyTpCd="14"` 를 싣는다.** `C5/a.java:60` 의 삼항은
    다리별 반복문 안에 있지만 배열의 *길이* 를 보고, 두 줄 아래 `:61` 은 반복
    *색인* 을 본다. 이것을 뒤집으면 앱이 결코 보내지 않는 폼을 보내게 되므로, 둘 다
    `smali/C5/a.smali:306-338`(`array-length` 가 매 반복 다시 평가된다)과
    `:343`(`if-nez v1`)으로 다시 읽었다.
  - **두 다리는 앱의 천장이지 여기서 고른 제약이 아니다.** 폼에 여정 3 의 철자가
    없다. `OSeat.java:32-35` 와 `OSrcar.java:21-30` 이 각각 "여정 1 이냐 아니냐" 로
    갈리므로 세 번째 다리는 다리 2 를 *덮어쓴다*. `ReservationRequest.java:114-117`
    도 좌석 슬롯을 정확히 둘만 되읽는다. 그 밖의 다리 수는 폼을 만들기 전에
    거절한다.
  - 환승 **검색** 이 옮기는 필드는 정확히 하나다. `WRD000061` 이 오면 앱은 이미
    만들어 둔 요청에 `setRadJobId(TRANSFER_SQ_NO.getCode())` 만 부르고 그대로 넘긴다
    (`DirectInquiryActivity.java:615-624` → `DirectInquiryActivity.java:284-296`,
    `smali/…/DirectInquiryActivity.smali:1677-1689` 로 확인). `chtnCnt`,
    `chtnRsStnCd1`, `trnGpCnt`, `trnGpCd1` 은 여기 들어가지 않는다.
    `search_trains_with_transfer_fallback` 는 앱 자신의 흐름을 그대로 옮긴 것이고
    `KorailNoDirectTrainError` 만 삼킨다.
  - 환승 **응답의 모양은 다르지 않다**. 같은 평탄한 `trn_infos.trn_info` 목록을
    자리로 짝지어 0/1, 2/3 순으로 묶고 홀수로 남은 마지막 행은 버린다
    (`a5/k.java:156-170`). `h_chg_trn_seq` 는 그 자리를 서버가 복사해 준 값이라
    짝짓기 키가 아니라 일관성 검사로만 쓴다. 페이징에는 커서의 환승 쪽 절반
    `TrainSearchContinuation.query_train_no2` 가 생겼고 기본값 `""` 이라 직통 다음
    쪽은 그대로다.
  - 승객 구성은 **예약 단위** 로 조합되고(`w4/a.java:47-74` 가 `OPsg` 를 한 번
    만든다), 좌석등급과 좌석지정은 **다리 단위** 로 조합된다(`C5/a.java:59`/`:97`,
    `:120-133`). **예약대기(`1102`)는 조합되지 않고 거절된다** — 앱이 두 곳에서
    막는다. `a5/k.java:120-127`(직통이 아닌 결과에는 예약대기 검사가 false 를
    돌려준다)과 `DirectInquiryActivity.java:434`(유일한 `setJobId("1102")` 이며,
    `TransferInquiryActivity` 가 덮어 없애는 화면에 있다).
- NetFunnel 가상대기실 클라이언트 `KorailNetFunnelClient`. 게이트에 걸린 연산이
  실패하는 대신 차례를 기다릴 수 있다. **기본은 꺼짐이고, 2026-07-26 실서버 프로브로
  절반이 확인됐다.** 그날의 프로브가 `nf.letskorail.com` 을 상대로 프로토콜을 돌려
  그때까지 추정이던 것들을 확정했다 — 전선 형식은 네이티브 SDK 의
  `<code>:<params>` 이고, 진입 순서는 `5101` → `5002` → 게이트된 호출 → `5004` 이며,
  큐는 호스트 하나가 아니라 여럿의 풀이다. 자리 반납 경로는 끝까지 돌았다.
  **201 대기 경로(queued path)는 여전히 NOT live-exercised** — 그날 서버가 줄을
  세우지 않아서(`5101` 이 `nwait=0` 으로 답했다) 폴링 루프와 ttl 대기와 두 상한은
  형제 SRT 클라이언트의 폴링 경로와 똑같이 오프라인 픽스처로만 덮여 있다.
  - **큐는 풀이고 세션은 그 풀의 노드 하나에 산다 — 프로브가 드러낸 두 번째 결함이자
    경고를 따로 적어 둘 값어치가 있는 것.** `nf.letskorail.com` 은 진입 호출을
    부하분산하는 정문(front door)이다. 세션을 끝낼 수 있는 것은 그 호출이 떨어진
    노드뿐이고, 모든 응답이 자기 `ip`/`port` 로 그 노드를 알려 준다. 이 클라이언트는
    모든 opcode 를 정문으로 보내고 있었으므로 자리 반납이 **절반쯤, 비결정적으로
    (half the time, non-deterministic)** 실패했다 — 획득·반납 다섯 번은 이랬다.

    ```
    acquire said ip=rnf12.letskorail.com  -> release 503
    acquire said ip=rnf12.letskorail.com  -> release 503
    acquire said ip=rnf13.letskorail.com  -> release 503
    acquire said ip=rnf14.letskorail.com  -> release 200
    acquire said ip=rnf13.letskorail.com  -> release 200
    ```

    그리고 결론을 낸 통제된 한 쌍은 이랬다.

    ```
    acquire on nf.letskorail.com (reply said ip=rnf13.letskorail.com)
      release via nf.letskorail.com    -> 503:msg="Wrong Server ID"
      release via rnf13.letskorail.com -> 200:key=&nwait=0&…
    ```

    **`Wrong Server ID` 는 문자 그대로(literal)의 뜻이다.** 적어 두지 않으면 다음
    읽는 사람의 한 시간을 먹는다 — 자격증명이나 파라미터 불평처럼 읽히지만 둘 다
    아니고, 큐 노드가 발급한 세션을 정문이 갖고 있지 않다는 말이다. 되는 것처럼
    보이던 반납은 부하분산기가 우연히 주인 노드로 돌아간 경우였고, 같은 키가 어떤
    때는 멀쩡히 반납되던 이유도 그것이다. 앱은 처음부터 그 이름을 따라갔다.
    `T6/d.makeURL`(`T6/d.java:17-19`)이 `host_notmodify` 가 서 있지 않으면 직전
    응답의 `getHost()`/`getPort()` 로 URL 을 다시 만들고, 그 플래그는 기본
    `false`(`T6/h.java:43`, `isHostNotmodify()` 는 `:134-135`)이며 `KTApplication` 이
    세우지 않는다. `ip`/`port` 를 읽는 곳은 `T6/i.java:50-53` 이다. 이것을 따르지
    않으면 잡은 자리의 절반쯤이 새고(leaked), 그것이야말로 NetFunnel 이 막으려고
    있는 일이다. 그래서 `5101` 은 정문으로, `5002` 와 `5004` 는 세션을 발급한 노드로
    간다. 노드는 `KorailNetFunnelToken.node` 에 실려 다니며 키와 같은 방식으로 뒤엣것이
    앞엣것을 덮는다(supersede) — 노드를 말하지 않은 응답은 직전 노드를 그대로 두고, 우회에는
    세션도 노드도 없다.
  - **리다이렉트는 믿는 것이 아니라 좁히는 것이다.** 다음 요청이 어디로 갈지를 응답이
    고르는 것이야말로 origin 가드가 막으라고 있는 일이므로, 그 이름은 큐 자신의 풀
    안으로만 받아들인다 — `rnf<1-99>.letskorail.com`, 소문자, 앞자리 0 없음, 라벨
    단위로 일치, 아니면 정문 자신. 스킴은 `https`, 포트는 `443` 뿐이다. 포트도 서버가
    시킨다고 따라가지 않는다. 규칙 밖은 무엇이든 **hard error** 이고 정문으로 조용히
    되돌아가는 일은 없다 — 조용한 폴백이 바로 그 오락가락하는 반납을 만든 것이고,
    "이 응답이 우리에게 거짓말을 한다"를 "자리가 샜다"로 바꿔 놓는데 샌 자리는 아무
    소리도 내지 않는다. 규칙은 클라이언트가 아니라 `safety.py` 의 origin 단언 옆에
    산다. `assert_korail_netfunnel_origin` 은 여전히 노드를 거절하고(설정된 origin 과
    진입 호출을 지키므로 한쪽 가드를 넓혀도 다른 쪽이 넓어지지 않는다),
    `follow_redirects` 는 `False` 그대로이며, `smart.letskorail.com` 의 표준 origin
    보장은 손대지 않았다.
  - **`5101` 의 키는 세션이 아니라 표(ticket)다 — 프로브가 드러낸 첫 번째 결함.**
    `acquire` 는 원래 5101 응답을 돌려주고 `release` 가 그 키를 `setComplete` 로
    보냈는데, 서버는 `sid`/`aid` 가 있든 없든 매번 `503:msg="Wrong Server ID"` 로
    거절한다. 완료할 수 있는 키는 `chkEnter` 가 발급한 것뿐이고 그것은 더 짧은 다른
    키다(252자가 104자가 된다). 그래서 `acquire` 는 5101 이 `nwait=0` 이라고 해도
    항상 5002 를 수행하고, **매 단계의 키가 앞 단계의 키를 덮는다(supersede)** — 201 폴
    하나하나가 그렇고, 키를 하나도 echo 하지 않은 201 도 그렇다(그 경우 마지막으로
    알려진 키가 그대로 유효하다). 반납이 성공하면 `200:` 에 *빈* `key=` 가 와서, 잘린
    본문이 아니라 반납으로 파싱된다. `503` 은 우리가 받아들이는 `502` 옆에 두지 않고
    거절하며, `release` 의 키 없는 지름길은 우회(`300`)로 좁혀서 다른 토큰이 요청을
    조용히 건너뛰지 못하게 했다. `503` 에는 원인이 **둘** 있고 전선으로는 구별할 수
    없다 — 교환하지 않은 표이거나, 틀린 노드다. 그래서 예외 메시지가 둘 다 말한다.
  - **글자 그대로 읽으면 APK 와 어긋나고, 이길 쪽은 실서버다.** `T6/g.java` 의 폴
    루프는 상태가 Continue 가 아닌 순간 빠져나온다 — `T6/g$a.smali:243-247` → `:282`
    → `:892` 에서 흘러내린 자리가 `return` 이다. 그러니 5101 이 200 을 주면 앱은
    5002 를 보내지 않고 표로 완료한다. 그래도 `5002` 는 무조건 보낸다. 깨끗하게
    반납되는 것이 확인된 순서는 `5101` → `5002` → `5004` 뿐이고, 그 표가 자기 노드
    에서 완료되는지는 프로브해 본 적이 없다. 키가 덮어써진다는 것은 APK 도 뒷받침한다
    — 응답 객체 하나를 `:61` 과 `:107` 에서 덮어쓰고 `Complete()` 가 마지막으로 도착한
    키를 보낸다(`:79`).
  - **KORAIL 은 JavaScript 방언을 쓰지 않는다. 이 변경의 실질은 전부 이것이다.**
    `nf.letskorail.com` 이 두 앱을 다 받으므로 실서버로 검증된 `srt-mobile-api`
    구현이 본이 될 줄 알았으나 아니다. SRT 는 `netfunnel.js` 위의 WebView 라 브라우저
    방언(`nfid`, `prefix`, `js=yes`, 끝의 epoch)을 보내고, `korail.apk` 는 STCLab 의
    네이티브 안드로이드 SDK — `T6`/`U6` 패키지 — 를 품고 있어 그중 아무것도 보내지
    않는다. 요청 셋은 `5101` `opcode,sid,aid`(`T6/d.java:99-101`),
    `5002` `opcode,key`(`:54-55`), `5004` `opcode,key`(`:78-79`)이고 이 순서인 것은
    `U6/a.java` 가 `addParam` 목록을 `URLEncodedUtils.format` 으로 렌더링하기
    때문이다. 그래서 `sid`/`aid` 는 `5101` 에**만** 실리고 이는 JS 방언과 정반대다.
    `ttl` 은 아예 되보내지 않고 얼마나 잘지 정하려고 읽을 뿐이며(`T6/g.java:462`)
    JS 번들의 5초가 아니라 30초로 잘린다(`T6/h.java:40`).
  - **응답 모양은 실서버가 확인해 준 적 없던 유일한 가정이었고, 맞았다.**
    `T6/i.java:36-43` 이 첫 `:` 앞을 전부 상태코드로 파싱하므로 응답은
    `<code>:<params>` 여야 하고 JS 방언의 `<rtype>:<code>:<params>` 이면 안 된다 —
    뒤엣것을 앱에 먹이면 코드를 5002 로 읽고 키를 찾지 못한다. 2026-07-26 의 응답은
    전부 정확히 네이티브 형태로 왔다. `parse_netfunnel_body` 는 여전히
    `NetFunnel.gRtype=…` 본문을 거절하고 오류 메시지에 그 가능성을 적는데, 이제는
    우리 추측에 대한 보험이 아니라 서버가 바뀐 경우의 진단이다.
  - **키는 KORAIL 요청에 절대 실리지 않는다.** 앱의 어떤 Retrofit 인터페이스도
    어떤 라우트에 `netfunnelKey` 모양의 필드를 선언하지 않는다. 큐는 호출을 게이트할
    뿐 호출에 파라미터를 더하지 않는다. 이것이 별도 호스트 위의 별도 클라이언트인
    이유이고, 예약·결제·취소·환불이 이전과 정확히 같은 것을 보내는 이유다.
  - **기본은 꺼짐이고 생성 시점에 강제한다.** `KorailConfig.netfunnel_enabled` 는
    `False` 이고, 그것 없이 만든 설정으로 `KorailNetFunnelClient` 를 만들면 소켓이
    생기기 전에 예외가 난다. 켜면 게이트된 연산마다 왕복 하나와 실패 양상 하나가
    늘고, 서버가 실제로 우리를 재기 전까지는 얻는 것이 없다. 성수기용이며, 앱이
    성수기 조회 큐(`act_8_2`)를 따로 들고 있는 이유도 그것이다.
  - **대기는 두 겹으로 제한된다** — 폴 20회와 60초 중 먼저 오는 쪽. 앱은 사람이 닫을
    수 있는 다이얼로그 뒤에서 무한히 폴한다(`T6/g.java:449`). 이 라이브러리에는
    다이얼로그가 없고, 큐는 재시도가 아니라 기다림이다. 재시도 로직은 넣지 않았다.
  - **자리는 두 경로 모두에서 반납된다.** 앱이 `BaseDaoHelper` 의 `onPostExecute`
    (:105-107)에서 게이트된 호출이 터졌든 아니든 반납하는 것과 같다. 반납 실패는
    성공 경로에서 삼켜지지 않고 **예외로 올라간다** — 형제 저장소가 키를 128자로
    묶어 뒀는데 실제 키는 256자라서 모든 반납이 보내지기도 전에 거절됐고, 실서버
    실행이 드러낼 때까지 모든 자리를 조용히 흘렸다. 2026-07-26 프로브가 실제 길이 둘
    — `5101` 의 252, `5002` 의 104 — 을 더했으므로 가드는 512자에 두고 관측된 어느
    한 길이로도 일부러 좁히지 않는다.
  - **정확한 질의 계약 셋을 등록한 것이지 허용목록을 느슨하게 한 것이 아니다.** 큐
    호스트에는 자기 origin 단언이 따로 있다 — 정문과 진입 호출용 하나, 풀용으로 더
    넓은 하나, 그리고 주어진 opcode 가 둘 중 어느 쪽을 받을지 정하는 셋째.
    `KORAIL_READ_ONLY_ROUTES` 는 54 그대로라 `post_form`/`get_json` 이 `/ts.wseq` 에
    닿을 길이 없다. `5003`, `5105`, `5106` 은 상수로 선언해 두고 가드가 거절한다.
- 서버 쪽 실패를 전부 하나의 `KorailAppError` 로 받는 대신 `h_msg_cd` 로 분류한다.
  새 타입은 `KorailNoResultsError`(그 아래 `KorailNoDirectTrainError`),
  `KorailSoldOutError`, `KorailSeatUnavailableError`,
  `KorailReservationRefusedError`, `KorailInvalidRequestError`,
  `KorailNotEntitledError`, `KorailServiceUnavailableError`,
  `KorailAppUpdateRequiredError` 이고 `classify_app_error` 를 함께 내보낸다.
  어느 것이 재시도 무의미이고 어느 것이 재로그인이며 어느 것이 "요청은 멀쩡했고
  그냥 아무것도 없었다"인지는 README 의 에러 분류표에 있다.
  - **기존 코드가 깨지지 않는다.** 새 타입은 전부 `KorailAppError` 의 하위라 기존
    `except` 절의 의미가 바뀌지 않고, `code`/`message`/`raw` 가 전부에 그대로 있어
    호출자가 점진적으로 옮겨갈 수 있다.
  - **실패를 지어내지 않는다.** 응답이 실패인지는 여전히 `strResult` 와 앱 자신의
    `WRC000288` 이 정하고, 분류는 이미 올라가기로 정해진 실패에 어느 예외가 어울리는지만
    고른다. 앱도 같다 — `FAIL` 이 아닌 응답의 모르는 코드는 `onReceive()` 로 성공으로
    간다(`BaseActivity.java:629`). 그래서 경고가 붙은 성공은 여기서도 성공이다.
    `strResult=SUCC` 와 취소 가능한 진짜 PNR 을 달고 왔던 `WRR664296` 이 테스트로
    고정돼 있고, APK 자신의 성공 쪽 코드 `IRR000014`, `IRT800005`, `WRS800036` 도
    마찬가지다.
  - **재시도 로직은 넣지 않았다.** 이 라이브러리는 여전히 스스로 재시도하지 않고
    `reserve` 는 절대 재시도하지 않는다. 재시도한 예약은 중복 예약이기 때문이다.
  - 매진(`ERR211161`), 좌석에 한정된 거절
    (`WRI411345`/`ERR911081`/`WRT800176` — 앱은 여기서 막다른 길 대신 자동 좌석배정을
    제안한다), 예약 거절(`WRR800029`/`ERR911531`/`ERR911051` — 앱은 사용자의 기존
    예약 화면으로 보내며 답한다), `WRD000061`, `WRG000000`, `P114`, `SEMGTK`,
    `SUPDATE` 는 전부 APK 분기이고 docstring 마다 file:line 으로 인용돼 있다.
    `P100`, `WRT300005`, `ERR299943`, `WRG200018`, `WRT100002`, `WRT100124` 는 APK
    적중이 0인 이 저장소의 실서버 관측이며 그렇게 표시돼 있다.
  - 안티매크로는 코드가 아니었다. `BaseDaoHelper.java:59-86` 이 `DynaPath-Result`
    헤더를 읽고 `h_msg_cd` 사다리를 돌리는 대신 본문의 `message` 를 띄우므로, 기존
    `KorailDynaPathError` 가 곧 안티매크로 거절이다. srtgo_plus 의 `MACRO` 부분문자열
    규칙과 srtgo 의 두 번째 매진 코드 `IRT010110` 은 제3자 주장으로만 기록하고 코드에
    넣지 않았다. 둘 다 채택하지 않았다는 것을 테스트가 단언한다.
  - `[3]인증정보에 문제가 있습니다.` 는 일부러 분류하지 않고 둔다. 이 문구와 함께
    잡힌 `h_msg_cd` 가 없고 문자열 자체가 APK 에서 0적중이라, 분류하려면 이 변경이
    없애려는 바로 그 한국어 문구 맞추기를 해야 한다.
- `reserve` 가 예약 화면의 job type 셋에 모두 닿는다. 키워드 전용이고 기본값이 있는
  `job_type`(`KorailReservationJobType`) 으로 고른다. 기본은 `IMMEDIATE`
  (`txtJobId="1101"`) 이고 이 패키지가 지금까지 보내 온 유일한 값이라, 기존 호출은
  바이트 단위로 그대로다. **변형 둘은 2026-07-26 에 실서버로 확인됐다** — 예약 →
  되읽기 → 취소. `1103` 은 요청한 좌석을 정확히 잡았다(대조는 재고의 `seat_spec` 과
  상세의 `h_seat_no` 이지 `seat_no` 가 아니다). 매진 열차의 `1102` 는 `IRR000014` 로,
  `confirm_standby_hold` 는 `IRZ000003` 으로 답했다.
  - `SEAT_DESIGNATED`(`"1103"`)는 좌석을 지정해 잡는다. `seats` 는 승객 한 명당
    `KorailSeatAssignment` 하나를 받고, 기존 좌석 읽기가 돌려주는 식별자 둘 —
    `SeatCar.car_no`/`SeatInventoryResponse.car_no` 와 `PhysicalSeat.seat_no` — 을
    그대로 싣는다. `KorailSeatAssignment.from_inventory()` 가 둘을 짝지으며 읽기가
    판매 불가로 표시한 좌석은 거절한다. 폼은 여정 블록 뒤에 `txtSrcarCnt`(*좌석* 수)
    를 붙이고 이어서 색인 1부터 `txtSrcarNo{i}`/`txtSeatNo{i}` 를 붙인다. 보통 hold
    는 그 키를 하나도 보내지 않는다 — 앱이 `OSrcar` 맵을 비우고 빈 Retrofit
    `@FieldMap` 은 필드를 하나도 더하지 않으므로, srtgo 의 무조건적인
    `txtSrcarCnt="0"` 은 앱이 만들지 않는 모양이다. 길이가 승객 총원과 다르거나 같은
    좌석을 두 번 부르는 좌석 목록은 무엇을 만들기 전에 거절한다. 반쪽만 예약된 hold
    는 반쪽짜리 좌석 목록에서 나온다.
  - `STANDBY`(`"1102"`)는 예약대기다. 자격 조건은 "매진" 이 아니다 — 앱은 필드
    하나, 검색 행의 `h_wait_rsv_flg` 를 읽어 두 글자 리터럴 `" 9"`(앞이 공백,
    `KORAIL_STANDBY_WAIT_FLAG` 로 export)와 비교하며, 그것도 일반실 탭에서만 한다.
    버튼을 여는 것은 그것뿐이고 잔여석 코드는 아예 보지 않는다. 그래서 예약대기는
    `1101` 이 강제하는 "좌석 있음" 검사를 건너뛰고, 대신 그 플래그와 일반실을
    요구하며, `txtStndFlg` 를 `"N"` 으로 고정하지 않고 앱 자신의 `isStndSeat` 에서
    계산한다. korail2 는 이 필드를 `-2`/`9`/`0` 으로 설명하지만 이 앱에서 근거가
    있는 것은 9 뿐이다. 예약대기는 **members-only** 다 — 이 job id 에 대해 앱의
    요청이 스스로를 비회원 불가로 선언한다. 이 클라이언트는 그것을 구조적으로
    만족한다. 모든 상태 변경이 로그인된 회원 세션을 요구하기 때문이다.
- `confirm_standby_hold`. 예약대기 예약에 필요한 두 번째 호출이다. `"1102"` hold 는
  `h_msg_cd = IRR000014`(`KORAIL_STANDBY_HOLD_MESSAGE_CODE`)를 달고 돌아오는데,
  앱의 예약대기 화면을 여는 코드는 그것뿐이다. 그 화면이 이어서
  `reservationWait.ReservationWait` 로 `txtPsrmClChgFlg`(좌석등급 변경 동의)와
  `txtSmsSndFlg`/`txtCpNo` 를 POST 한다. 전화번호는 SMS 를 켰을 때만 보내고 10자리
  또는 11자리여야 하며, 그 밖에는 빈 값으로 보내지 않고 아예 뺀다 — 필드가 null 이라
  Retrofit 이 떨구는 앱과 같다. 이미 있는 PNR 에 대한 상태 변경 호출이므로 나머지와
  같은 이중 게이트 상태 변경 transport 를 탄다. 새 범주를 만들지 않고
  **`reserve` consent 범주** 를 일부러 함께 쓰는 것은, 이 호출이
  `allow_reserve` consent 가 허가한 예약을 마무리하는 것이고 돈을 움직이지도 좌석을
  놓아 주지도 않기 때문이다. 새 범주를 만들면 예약대기를 걸기로 옵트인한 호출자가
  그것을 끝맺지 못하게 된다. `reservationWait.ReservationWait` 가 다섯 번째 상태
  변경 라우트가 됐고, 읽기 전용 허용목록과 그 보장은 그대로다. 실서버로 돌린 적은
  없다.
- `reserve` 가 임의의 승객 구성을 두 좌석등급 어느 쪽으로든 예약한다. 앱의 요청이
  줄곧 실어 온 행마다 필드 하나씩을 가진 `KorailPassengerCounts`(어른, 청소년,
  어린이, 동반유아, 경로, 1~3급 장애, 4~6급 장애, 안내견)와
  `KorailSeatClass`(일반실 `"1"` / 특실 `"2"`)를 받는다. 둘 다 키워드 전용이고
  기본값이 일반실 어른 1명이라, 기존 호출은 키까지 바이트 단위로 같은 폼을 보낸다.
  `txtTotPsgCnt` 는 무릎 위 유아와 안내견을 포함해 모든 행을 더한 값이다. 앱이
  `TOTAL_PERSON_COUNT` 를 그렇게 계산하기 때문이다. 구성은 음수가 아니어야 하고,
  최소 한 명을 담아야 하며, `KORAIL_MAX_PASSENGERS_PER_RESERVATION`(9, 앱의 승객
  선택기가 강제하는 상한) 안이어야 한다. 할인 승객 행에 할인카드 필드가 따라붙지는
  않는다 — 앱의 `OPsg` 는 `txtCardNo_` 만 선언하고 그것을 쓰는 것은 별개의 N카드
  요청뿐이며, korail2 와 srtgo 의 `txtCardCode_`/`txtCardPw_` 는 디컴파일한 앱
  어디에도 없다. 특실 hold 는 그 열차의 일반실이 아니라 특실 좌석이 남아 있다는
  근거를 요구한다. 2026-07-26 에 예약→취소 왕복으로 실서버 확인했다 — 일반실 어른
  2명(hold 합계 119,600 = 2 × 59,800)과 특실 어른 1명(되읽으면
  `h_psrm_cl_nm='특실'`, `h_rcvd_amt=83,700`). 특실 hold 는 결제 금액이 왜
  `h_tot_rcvd_amt` 에서 와야 하는지도 보여 준다 — 그 `h_tot_prc` 는 `59,800` 이라
  옛 빌더였다면 23,900원을 덜 냈을 것이다. 다른 승객 종류와 종류가 섞인 구성은
  여전히 정적 근거뿐이고 전송된 적이 없다.
- 과금되는 실카드 결제가 가능해졌다. 명시적이고 덧붙이는 방식의 옵트인이다.
  `MutationConsent` 에 `real_card_acknowledged`(기본 `False`)가 생겼다 — 과금되는
  진짜 PAN 이 평문으로 전송되고 실제로 돈이 움직인다는 것을 호출자가 확인했다는
  표시다. 기본이 `False` 이므로 이것이 생기기 전에 쓰인 consent 는 전과 정확히 같은
  뜻이고 기본 자세도 그대로다 — 가짜카드만.
- `KorailClient.pay_with_card` 를 더했다. `pay_with_fake_card` 는 그대로 옆에
  있다. 새 메서드는 `real_card_acknowledged=True` 와 `fake_card_only=False` 를
  **둘 다** 요구하고, 옛 메서드는 여전히 테스트 카드가 아니면 거절하므로 이름이
  뜻하는 바를 지킨다. 둘 다 같은 `build_card_payment_form` 을 만들고 같은 이중
  게이트 `post_mutation_form` 으로 나가므로, 실결제가 실서버로 확인된 전선 모양에서
  벗어날 수 없다. `pay_with_card` 는 FAIL 에 예외를 올리는 대신 파싱된 결제 봉투를
  돌려준다. 그 봉투가 돈에 무슨 일이 있었는지, 그리고 hold 를 아직 취소할 수 있는지에
  대한 유일한 기록이기 때문이다.
- `scripts/reserve_pay_refund_roundtrip.py`. 실카드로 예약 → 결제 → 환불 왕복을 한
  번 도는 운영자용 스크립트다. 환경변수 옵트인 셋이 모두 필요하고
  (`KORAIL_MOBILE_API_LIVE=1`, `KORAIL_LIVE_MUTATION=1`,
  `KORAIL_LIVE_REAL_CHARGE=1`), 카드는 환경변수에서만 읽는다 — 파일도 argv 도
  아니다. 계정에 예약이 0건이 아니면 시작하지 않고, PNR 이 생기는 즉시 찍고, 결제
  전에 청구액을 독립된 서버 읽기와 대조하고, 환불 전에 환불액과 수수료를 찍는다.
  이후 어느 단계가 실패하든 PNR 과 무엇이 남았는지와 실행 가능한 복구 명령
  (`KORAIL_RECOVER_PNR` 과 함께 쓰는 `--recover`)을 담은 놓칠 수 없는 배너를 찍는다.
  PAN, 비밀번호 자릿수, 유효기간, 생년월일은 예외 문구를 포함한 모든 출력 경로에서
  지워진다. PNR 은 일부러 지우지 않는다. 그것을 잃는 것이 최악이기 때문이다.
- 읽기 전용 라우트 셋. 이 패키지를 제3자 참조 클라이언트 넷(srtgo, srtgo_plus,
  ryanking13/SRT, korail2)과 대조하다 찾았고, 셋 다 우리가 디컴파일한 APK 에도
  선언돼 있다. `get_ticket_reservation_detail` 은 잡아 둔 예약 하나를 PNR 로
  되읽으며(`certification.ReservationList`, `CertificationService.java:45-46`),
  결제 폼이 정산하는 `h_wct_no` 와 좌석별 `h_rcvd_amt` 행을 독립적으로 볼 수 있게
  해 준다. `get_refund_commission`(`refunds.CommissionView`,
  `RefundService.java:19-21`)은 `ret_amt`/`ret_fee`/`prg_psb_flg` 를,
  `get_refund_ticket_detail`(`refunds.SelTicketInfo`, `RefundService.java:23-25`)은
  환불 대상의 승차권 상세와 `retPsbFlg` 를 알려 준다. 뒤의 둘을 합치면 `refund` 가
  한 번도 가져 본 적 없는 "얼마가 돌아오고 수수료는 얼마인가" 사전 확인이 된다.
  참조 클라이언트 넷 중 어느 것도 이 둘을 구현하지 않았다. 경계는 이제 정확한
  로그인·읽기 라우트 54개와 공개 메서드 60개다.
- 상태 변경 요청을 위한 consent·safety 토대. frozen `MutationConsent`(범주별
  `allow_*` 기본 `False`, `dry_run` 기본 `True`, `fake_card_only` 기본 `True`)와
  frozen `MutationPreview`(payload 가 생성 시점에 `redact_payload` 를 통과하므로
  미리보기가 날 PAN·PNR·판매 신원을 담을 수 없다)가 `consent.py` 에 있다. 라우트
  등록부가 층을 갖게 됐다 — `KORAIL_MUTATION_ROUTES` 가 상태 변경 라우트 넷을 들고
  있고 `KORAIL_READ_ONLY_ROUTES` 에는 일부러 절대 더하지 않으며,
  `KORAIL_MUTATION_ROUTE_CATEGORIES` 와 `assert_mutation_route_category` 가 호출자의
  consent 범주를 라우트와 맞대조하므로 한 범주의 consent 로 다른 범주의 라우트를
  POST 할 수 없다. 마스킹은 상태 변경 필드까지 넓혔다 — 카드번호, PNR, 원표 판매
  신원, 반환 비밀번호, `txtPrnNo`, `h_orgtk_sale_wct_no`.
- consent 게이트가 걸린 상태 변경 메서드 넷: `reserve`, `cancel_unpaid_hold`,
  `pay_with_fake_card`, `refund`. 각각 인증된 세션과 자기 범주로 옵트인한
  `MutationConsent` 를 요구하고, 그렇지 않으면 무엇을 만들기 전에
  `MutationNotAllowedError` 로 거절한다. 기본 `dry_run=True` 에서는 입력을 검증하고
  *보냈을* 폼을 마스킹한 `MutationPreview` 로 돌려주며 아무것도 보내지 않는다.
  전송하는 것은 `dry_run=False` 인 consent 뿐이고 통로는 `post_mutation_form` 하나다.
  그 통로가 consent 를 다시 검사하고, `dry_run=True` 인 consent 를 거절하며, 상태
  변경 라우트인지와 그 범주에 속하는지를 둘 다 단언한다. 읽기 전송 경로
  (`post_form`/`get_json`)는 모든 상태 변경 라우트를 여전히 거절한다.
  `pay_with_fake_card` 는 메서드와 전송 게이트 양쪽에서 `fake_card_only` 가 서 있지
  않으면 거절한다. 결제 폼이 카드번호를 평문으로 싣기 때문이고, 과금되지 않는 테스트
  카드만 지원한다.
- `refund` 를 같은 게이트 전송 경로에 올렸다. 전송 경로는 막힌 코드가 아니라 완전히
  살아 있는 코드이지만 실서버로 돌아 본 적이 없다 — 환불은 정산된 승차권에 작용하는데
  이 패키지의 가짜카드 결제는 언제나 거절되므로 여기서 결제된 승차권이 생기지 않는다.
  요청 계약과 게이트와 마스킹은 오프라인 테스트로만 덮여 있고, 실서비스에 대해서는
  미검증으로 다뤄야 한다.
- 인증이 필요한 일회성 승차권 참조 읽기 다섯. 배송 수령인 상세, 승차권 중복 건수,
  PBP 인수 명세, 승강장 번호, 최근 배송 이력이다. 정확한 정적 계약은 `repr` 에서
  가려진 타입 붙은 승차권·PNR 출처만 받고, 반복되는 `tkRetNo` 의 순서를 개수까지
  같게 보존하며, 최근 이력의 `custMgNo` 를 로그인 세션에서만 유도하고, DynaPath 를
  끈다. 구현 자체는 실서버 요청을 하나도 보내지 않았다. 그 시점(pre-R149)의 인벤토리는
  165 중 성공 31, 실패 10, 미실행 124 였다. 패키지 경계는 읽기·로그인 라우트 51개와
  공개 메서드 57개가 됐고 DynaPath 허용목록은 여섯 경로 그대로다. 승차권 참조 구현
  자체는 실서버 입출력을 쓰지 않았고 상태 변경 능력을 더하지 않았다.
- 선물하기 승차권 목록 모드, 정기권 job `a`/`b`/`c`, 한 다리·두 다리 운임 견적에
  대한 닫힌 태그 공개 읽기. 정확한 순서 폼이 R31 의 중복 필드를 보존하고 R52 의
  `trnCnt` 는 일부러 뺀다. 기존의 조건부 DynaPath 경로를 쓰는 것은 R52 뿐이다.
- R39 를 위한 엄격 합성 응답 모델·파서와 내부 전용 정확 요청 빌더. R39 의 NetFunnel
  `service_1`/`act_6` 라우트는 여전히 쓸 수 없게 두었고 R54 도 transport 에서 막혀
  있다. 그 구현 단계에서 DynaPath 허용목록과 실행 인벤토리는 그대로였고, 실서버 호출도
  상태 변경 능력 추가도 없었다. 현재 경계는 읽기·로그인 라우트 51개와 공개 메서드
  57개다.
- 인증이 필요한 고정형·계정형 읽기 넷. 다자녀 할인 대상, 로그인 고객의 여정 정보,
  현재 또는 범위를 정한 이력의 MaaS 서비스 상세, 여행변경 가능일 조회다. 정확한
  라우트와 순서 폼은 DynaPath 를 끄고, 검증은 transport 이전에 일어난다.
- R13, R32, R43, R45 에 대한 엄격 합성 파서와 `repr` 안전한 frozen 모델. R54
  관광열차 응답 파싱은 정적 계약 지원까지만이다 — 클라이언트 메서드도, safety 라우트도,
  날문자열 요청 빌더도 없다.
- 정적 APK 근거에서 나온 타입 붙은 P0 열차 읽기 넷을 처음 넣었다. 자유석 객차 안내,
  안내 좌석 조건, 좌석배정 일정, 병합좌석 조회다.
- 최초 구현이 frozen 닫힌 요청 객체, 정확한 POST 필드 허용목록, 엄격 응답 파서,
  `repr` 에서 가려진 식별자·자유문구·날매핑, 합성 전용 픽스처를 더했다. 그 구현
  단계는 실서버 호출도 DynaPath 라우트도 더하지 않았다.
- 타입 붙은 정기권 메뉴·정기권 종류 메뉴·승무원 요청 옵션 읽기. 세션 요구 여부가
  확인되지 않은(session-unverified) 것들이고 호출자가 런타임 구분 코드를 직접 줘야
  한다. 실서버 검증은 로그인 이후에만 시작한다.
- `repr` 안전한 frozen 모델, 엄격 파서, 합성 픽스처, 그리고 라우트·요청·오류·export·
  문서에 대한 오프라인 커버리지.
- 정적 근거가 있는 리무진버스 읽기 셋. 호출자가 주는 닫힌 질의 dataclass, 정확한
  POST 허용목록, 타입 붙은 `repr` 안전 파서, 일회성 세션·오류 처리를 갖추고 DynaPath
  는 꺼져 있다.
- **이 패키지에 라이선스가 생겼다.** `LICENSE` 가 Apache License 2.0 원문을 그대로
  담고, `pyproject.toml` 이 PEP 639 SPDX 형식(`license = "Apache-2.0"`,
  `license-files = ["LICENSE", "NOTICE"]`)으로 선언한다. setuptools 가 경고하고
  2027-02-18 부터는 아예 거절할 낡은 `license = {text = ...}` 테이블을 쓰지 않는다.
  빌드 최소 버전이 `setuptools>=77` 로 올라간 것도 같은 이유다. 그 이전 버전은
  `license-files` 를 조용히 무시해서, 라이선스를 주장하면서 라이선스 본문은 싣지 않는
  wheel 을 만든다. `License ::` 분류자는 함께 쓰지 않는다 — PEP 639 가 둘을 상호
  배타로 만들었다. `NOTICE` 를 저장소 뿌리에만 두지 않고 `LICENSE` 와 나란히 선언하는
  것은 Apache-2.0 §4(d) 가 재배포자에게 귀속 고지를 이어 나르도록 요구하는데, 그
  파일을 뺀 wheel 은 그것을 불가능하게 만들기 때문이다. 두 산출물 모두 두 파일을
  싣는다.
- 소유자와 표준 URL 메타데이터. `authors` 가 `yakisoba0728` 과 연락처 주소를
  가리키며, 철자는 `pyproject.toml` 에만 있고 여기 옮겨 적지 않는다 —
  `tests/test_readme.py` 가 근거 문서에 맨 이메일 주소가 있는 것을 금지하고 그 게이트가
  중복해 적는 것보다 값어치가 있다. `[project.urls]` 는 Homepage, Repository, Issues,
  Changelog 를 `https://github.com/yakisoba0728/korail-mobile-api` 로 고정한다.
- `korail_mobile_api.__version__`. `project.version` 과 같은지를 단언하는 테스트가
  함께 있다. 손으로 쓴 던더와 손으로 쓴 TOML 리터럴을 맞춰 주는 것이 빌드에는 없고
  그 테스트뿐이다. `__all__` 에는 일부러 넣지 않았다.
- **`tests/test_public_surface_rule.py`.** 위의 것들이 편리한 이름 하나를 export
  하고 싶은 다음 사람에 의해 되돌려지는 것을 막는 장치다. 이름 목록을 들고 있지
  않다 — 손으로 유지되는 이름 목록이야말로 썩는 것이다. `ast` 로 `__init__.py` 의
  import 문에서 `__all__` 의 기대 내용을 유도하고(그래서 import 는 남긴 채 `__all__`
  항목만 지우면 실패한다), 짧은 모듈 정책 목록에 없는 모듈에서 온 이름을 거절하고,
  `parse_*`/`pair_*` 는 아예 거절하고, 모든 공개 클라이언트 메서드 애너테이션의 추이
  폐포를 걸어 그 안의 패키지 정의 타입이 전부 export 되기를 요구하며, export 된
  타입 아닌 것은 전부 이유가 적힌 `DOMAIN_CONSTANTS` 표에 나타나기를 요구한다. 이
  파일은 저장소별 헤더 아래에서 SRT 패키지와 글자 그대로 공유한다.
- 문서 사이트. `mkdocs.yml` 이 `docs/` 아래 여섯 쪽을 만들고, API 레퍼런스는 공개면을
  내보내는 모듈마다 docstring 에서 생성한다. 빌드 도구는 `docs` extra 로 들어간다
  (`pip install -e ".[docs]"`). 런타임 의존성은 늘지 않는다 —
  METADATA 에는 `Requires-Dist: ...; extra == "docs"` 로만 나간다.

### Changed

- **`scripts/reserve_pay_refund_roundtrip.py` 는 운임 상한 없이는 시작하지 않는다.**
  `KORAIL_MAX_FARE` 는 "optional … strongly recommended" 로 적혀 있었지만, 이 스크립트가
  결제하는 금액을 막는 것은 *이것뿐*이다. (d) 단계가 청구 금액을 이 값과 비교하는데, 값이
  없으면 비교를 그냥 건너뛴다. 열차 선택도 비용을 묶어 주지 않는다. 운임 조회도, 검색 행의
  가격 힌트도 얻을 수 없으면 스크립트는 값이 얼마든 첫 예약 가능 열차로 내려간다. 그래서
  문서에 적힌 명령을 이 변수 없이 따른 운영자는 상한 없는 실카드 결제를 돌리고 있었다.
  요구는 결제 경로에서만, 카드를 읽기 전에, 로그인 전에, 어떤 요청보다 먼저 강제한다.
  형식이 잘못된 값도 200 줄 뒤가 아니라 거기서 중단시킨다. `--recover` 는 영향을 받지
  않는다. 두 분기 모두 아무것도 결제하지 않는다.
- 문서가 디컴파일된 KORAIL 앱 코드를 그대로 싣지 않는다. Java 메서드 본문과 그 smali 를
  붙여넣었던 한 곳(`docs/deep-dive/impl-audit-2026-07-22.md` 의 `setTrnCnt` 자기대입 무동작)
  과 Retrofit 인터페이스 선언을 붙여넣었던 한 곳(`docs/audit-2026-07-27/phase2/safety.md`
  의 `dcntCrdExtn.do`)이 이제 관찰한 내용을 서술한다. 모든 `file:line` 인용은 그대로이고,
  디컴파일러 산물이 아님을 가른 바이트코드 수준의 세부도 그대로다. 바뀐 것은 근거의 형식이지
  근거의 힘이 아니다. 해당 감사 문서가 지금 따르는 규칙을 명시한다. 제3자의 저작물은 위치로
  인용하고, 클라이언트가 맞춰야 하는 와이어 이름만 인용한다.
- 기계 생성 카탈로그 둘도 생성물이라는 이유로 예외를 두지 않고 같은 규칙을 따랐다. 펜스
  태그가 아니라 내용으로 다시 훑자 펜스 스캔이 찾은 것보다 약 660 줄이 더 나왔다.
  `docs/deep-dive/local-storage-catalog.md` 는 644개 키 행마다 문장 전체를 붙여넣었고,
  `docs/deep-dive/webview-and-url-catalog.md` 는 메서드 26줄과 문장 셀 17개를 붙여넣었다.
  근거로서 잃은 것은 없다. 저장소 카탈로그의 Context 열은 원래 의미하던 접근을
  (`쓰기 putString` / `읽기 getInt` / `존재 확인 containsKey`) 대체한 문장에서 기계적으로
  유도해 적는다. WebView 카탈로그의 Signature 열은 본문 여는 중괄호를 뺐는데, 그것이 그 행을
  시그니처가 아니라 소스 줄로 만들던 것이다. 라우트 애너테이션 셀은 그대로 둔다. 라우트는
  클라이언트가 맞춰야 하는 인터페이스다. 키 이름, `file:line`, 개수는 바뀌지 않았으므로 모든
  행을 같은 APK 로 다시 확인할 수 있다.
- 문서의 절대경로에 로컬 사용자명이 남지 않는다. 14개 전부 저장소 기준 상대경로로 다시
  썼으므로, 나중에 새는 값이 숨을 예외 목록이 없다. 이 저장소 안이 아닌 유일한 경로인
  `srtgo_plus` 참조 체크아웃은 없는 업스트림 URL 을 지어내는 대신 로컬 체크아웃이라고
  적는다.
- 히스토리 재작성이 남긴 벤더 키 자리표시자가 문장으로 읽힌다. `<KORAIL-APP-…-REDACTED>`
  자리마다 원래 어떤 필드였고 왜 값이 없는지 적는다. 거짓 리터럴이 돼 버린
  `kakao<key>://oauth` 는 원래부터 규칙이었던 대로 쓴다(스킴은 `kakao` 뒤에 앱 키가 붙는다).
  `docs/RELEASE_GAP_PLAN.md` 는 "values deliberately NOT copied into this plan" 이라고
  선언하면서 정작 그 값을 인쇄하는 문서를 가리키고 있었다. 이제 그 모순이 해소됐다는 것,
  값이 트리뿐 아니라 히스토리에서도 사라졌다는 것, 그리고 아직 평문으로 남은 값 하나(GCM
  sender id — 자격증명이 아니라 Firebase 프로젝트 *번호*)는 놓친 것이 아니라 일부러 남긴
  것임을 기록한다.
- **동작 변경. 맨손 `KorailClient()` 로 로그인할 수 있다.** 전에는 되지 않았고, 그래서
  README 의 빠른 시작 — `KorailClient()` 다음 `login(...)` — 은 거짓이었다. 2026-07-27
  실검증: 기본 `KorailConfig()` 는 DynaPath 를 끈 채
  `User-Agent: korail-mobile-api/0.2.0` 을 보냈고, `login.Login` 은 자동화 방지 검사에서
  `**MACRO ERROR**` 를 돌려줬다. 로그인에 성공한 유일한 설정은 `build_config_from_env`
  였는데 README 는 그것을 언급하지 않았고 `__all__` 도 내보내지 않았다. 이 실패는 읽기
  어려웠다. **위장돼 있기** 때문이다. 서버는 매크로 거부를
  "원활한 서비스 이용을 위해 앱을 최신 버전으로 업데이트한 뒤…" 로 돌려준다.
  게다가 계정과 무관한 읽기는 같은 설정에서 계속
  성공하므로, 증상이 클라이언트 형태 문제가 아니라 버전 게이트처럼 보인다. 실제로 한 번
  그렇게 오진된 적이 있다. 기본값 셋이 바뀌었다.
  - `KORAIL_USER_AGENT` 가 `korail-mobile-api/0.2.0` 대신 플랫폼 기본 Dalvik 문자열
    `Dalvik/2.1.0 (Linux; U; Android 15; Android)` 이 됐다. 앱은 UA 를 하드코딩하지 않는다.
    Retrofit v1 이 `UrlConnectionClient`/`HttpURLConnection` 위에서 돈다
    (`ExecuteDao.java:7-11`). 그러니 서버가 실제 앱에서 보는 것은 플랫폼 문자열이다. 이 값은
    새 `build_dalvik_user_agent` 가 DynaPath 토큰의 `dm` 과 `os` 가 싣는 것과 같은
    `KORAIL_DEFAULT_DEVICE_NAME` / `KORAIL_DEFAULT_ANDROID_OS_RELEASE` 에서 **유도**한다.
    `build_config_from_env` 도 같은 빌더를 부른다. 한 요청 안에서 UA 는 이 단말이라 하고
    토큰은 저 단말이라 하는 것 자체가 신호이므로, 둘을 따로 적을 수 없게 했다.
  - **DynaPath 가 기본으로 켜진다.** 이제 모든 클라이언트가 허용된 여섯 경로에
    `x-dynapath-m-token` 을 붙인다. 전에는 하나도 붙이지 않았다. 어디에 토큰을 보내는지는
    그대로이고 보내느냐 마느냐만 바뀐다. 끄려면
    `KorailConfig(dynapath=DynapathConfig())` 를 쓴다. `DynapathConfig` 자신의 기본값은
    건드리지 않았다. 켜진 기본값과 토큰 설정은 `KorailConfig` 의 필드 팩토리 쪽에 달려
    있다. `DynapathConfig.__post_init__` 이 `token_provider`/`token_settings` 중 정확히
    하나를 요구하므로, `token_settings` 에 기본값이 있으면 모든
    `DynapathConfig(enabled=True, token_provider=fn)` 이 모순이 된다.
  - 기본 토큰 설정은 기기 신원을 `generate_dynapath_device_id` 로 **`KorailConfig`
    인스턴스마다** 생성한다. 고정된 기기 ID 는 패키지에 넣지 않는다. `di` 는 단말의
    `Settings.Secure.ANDROID_ID` 이고 (`AbstractC1228a.java:16`, `C1229b.java:103` 에서
    그대로 실린다), 라이브러리의 모든 설치본이 공유하는 식별자야말로 이 헤더가 잡으려는 봇
    서명이다. 이 저장소가 srtgo 의 고정값 `558a4f02041657ea` 에 이미 제기한 비판이 그것이다.
    값은 `uuid.uuid4().hex[:16]` 으로 ANDROID_ID 의 실제 형태인 소문자 16진수 16자리와
    같고, 설정 객체가 사는 동안 유지되며 저장되지 않는다. `app_start_ts` 는 설정을 만든
    시각이며 `AbstractC1228a.java:14` 가 기록하는 것이 그것이다.
- `EXCLUDED_API_DOMAINS` 가 `"points-mileage"` 대신 `"points-mileage-write"` 를 담는다.
  옛 이름은 잔액 읽기까지 포함해 적립 영역 전체를 막았는데, 사용자가 그 읽기를 요청했다.
  새 이름은 여전히 거부하는 것만 가리키고, 거부마다 범주가 아니라 이유가 붙는다.
  `mlg.lpotAthn.do` 와 `xPoint.XPointView` 는 사용자가 입력한 포인트 **비밀번호**를 받고
  실패 횟수 `pwdErrTno` 로 답한다. 화면 제목이 무엇이든 틀린 추측 한 번이 적립 사업자 쪽
  상태 변경이다. `xPoint.OkCashbagCertView`, `mileage.acpnMlgSave.do`,
  `mileage.acpnMlgNoti.do` 는 등록·적립 쓰기다. 다섯 개가 계속 닿을 수 없다는 것과 다른
  제외 도메인이 움직이지 않았다는 것을 테스트가 고정한다.
  - **`xPoint.MyXPointView` 는 이 프로젝트가 가진 줄 몰랐던 계정 자격 읽기다.** 포인트
    잔액 외에 `h_hdcp_flg` 를 싣는데, `MyPageActivity.java:206-212` 가 이 플래그 하나로
    장애인 절 전체를 드러내고 두 행을 `h_subt_dcs_cl_nm`(라벨 장애인증, `:353,393`)과
    `h_cust_lead_flg_nm`(라벨 보조견, `:355,394`)으로 채운다. 따라서 플래그가 `"Y"` 가
    아닌 계정은 두 등록 중 어느 것도 갖고 있지 않다. 바이트 단위로 일치하는 폼에 대해
    1~3급 장애 + 안내견을 거부한 라이브 `ERR299943` "예약할인이 지원되지 않습니다" 의
    설명이 될 만한 모양이다(`docs/MUTATION_HANDOFF.md:172-179`). **발견이 아니라 가설**
    이다. 앱이 그 플래그로 무엇을 하는지일 뿐 관찰된 짝은 아니다.
  - `point_dv_cd` 는 호출자 인자가 아니다. `KorailPointInquiryDao.java:87-92` 에는 요청
    클래스가 없고 리터럴 `"0"` 을 넘기므로 빌더는 인자를 하나도 받지 않는다.
  - 마일리지 읽기의 페이지 크기는 선택지가 아니라 앱이 하드코딩한 `"20"` 이고
    (`MileageHistoryActivity.java:274`), `qryDvVal` 은 코드가 아니라 드롭다운 **인덱스**다.
    `:566` 이 `onItemSelected` 에서 온 `Integer.toString(i9)` 를 그대로 대입하고, 세 항목은
    `:502` 에서 전체/적립/사용으로 선언된다. 기간에는 기본값이 없다. 기본값을 주면 페이로드
    빌더 안에 시계를 넣는 셈이기 때문이다. 앱 자신의 기본값은 `:372-380` 의 "최근 3개월"
    분기다.
- `scripts/reserve_pay_refund_roundtrip.py` 는 운임 조회를 만들 수 없을 때 검색 행 자신의
  가격 필드로 열차를 고른다. 라이브 ScheduleView 행에는 상품 번호가 없어서 `trn.prcFare.do`
  를 보통 만들 수 없고, 그러면 스크립트는 `fare: UNKNOWN` 을 찍고 첫 예약 가능 열차를 잡았다.
  지어내는 것은 여전히 없다. `KORAIL_TRAIN_NO` 가 열차를 정확히 지정하고(그 열차가 예약
  불가면 예약 전에 중단한다), 그다음이 가장 싼 운임 조회, 그다음이
  `RsvInquiryResponse.TrainInfo` 가 선언하는 `h_rcvd_amt`/`h_rcvd_fare` 기준 최저가다.
  이 값은 `~N KRW (HINT from the search row, not a quote)` 로 찍어 곧 청구될 금액으로 읽힐
  수 없게 한다. 그다음이 전과 같은 문구의 첫 예약 가능 열차다. 어느 분기가 실행됐는지는 항상
  출력에 이름으로 나온다. 권위 있는 금액은 여전히 결제 전에 다시 읽어 교차 확인한 값이고,
  청구의 유일한 상한은 여전히 `KORAIL_MAX_FARE` 다.
- 전송 게이트가 결제 동의에 카드 주장 **하나**만 있을 것을 요구한다. 둘 다 설정하지 않은
  경우는 원래대로 거부다. 둘 다 설정한 경우는 모순으로 거부한다. 테스트 카드라고 주장하면서
  실제 과금을 확인했다는 동의는 호출자 버그이고, 모호한 동의로 결제하는 것이야말로 이
  게이트가 막으려는 실수다. 경계는 이제 정확한 로그인·읽기 라우트 54개와 공개 메서드
  61개이며 새 라우트는 없다.
- `ReservationSeatDetail` 은 승객 유형을 `h_psg_tp_cd` 에서 가져온다.
  `ReservationResponse.SeatInfo` 가 선언하는 것이 그것이다. 어떤 참조 클라이언트가 쓰는
  `h_psg_tp_dv_nm` 은 디컴파일된 앱 어디에도 없고 라이브에서도 관찰되지 않아 일부러 매핑하지
  않는다. 매핑하지 않은 키는 `raw` 로 닿을 수 있다.
- 패키지 경계가 정확한 로그인·읽기 라우트 51개와 공개 메서드 57개가 됐다. 읽기 전용 요청만
  보내는 감사된 로그인·읽기 메서드 53개에 동의 게이트가 걸린 상태 변경 메서드 4개다. 상태
  변경 라우트 4개는 별도 집합으로 관리하며 읽기 경로에서는 절대 닿을 수 없다.
- `logout()` 이 로컬 상태를 지우기 전에 맨 `GET` `login.Logout` 으로 서버 세션을 무효화한다.
  전송 오류나 이미 만료된 세션에서 실패하지 않도록 best-effort 다. 쿠키로 인증되고 매개변수가
  없는 이 라우트가 읽기 전용 허용 목록에 들어갔고, 그래서 목록이 50개가 아니라 51개다.
  `KORAIL_DYNAPATH_SDK_VERSION` 도 디컴파일된 앱에 맞춰 `v1` 에서 `v1.0.3` 으로 고쳤다. 이
  상수가 본문 필드 `sv` 와 `dyn_key` 양쪽의 씨앗이다.
- R17 의 알려진 HTTP 404 는 재시도·대체·우회 없이 요청 한 번짜리 `KorailTransportError` 로
  둔다. R17 과 R31 은 로컬 세션을 요구하고, R52 는 세션을 지어내지 않는다.
- 로그인 응답의 `strCustNo` 는 고객 여정 요청용 세션 고객번호로 repr 에서 숨긴 채 보관한다.
  회원·회원카드 식별자는 대체값이 아니다.
- Java Retrofit 이름은 문서용 별칭으로만 두고, `TrainSummary` 편의 연결과 인접한 모든 상태
  변경은 일부러 뺐다.
- 기존의 `FAIL`, `P058`, `WRC000288` 오류를 보존한 뒤 이 네 라우트의 파서만 정확한
  `strResult=SUCC` 를 요구하도록 좁혔다.
- 리무진 질의의 하위 클래스를 거부하고, Sid 생성이나 전송 전에 각 구체 데이터클래스의
  검증기를 비가상으로 호출한다.
- P0 메뉴와 리무진의 모든 타입 파서가 정확한 `strResult=SUCC` 를 요구한다.
- 라이브에서 확인된 JSON 정수와 ASCII 10진 문자열 형태의 역 팝업 유형·실제 도착 지연 횟수를
  더 넓은 강제 변환 없이 정규화한다.
- **`scripts/verify_distribution.py` 가 이 메타데이터를 금지하는 대신 검증한다.** PEP 639
  빌드가 내는 네 헤더 — `License-Expression`, `License-File`, `Author-email`,
  `Project-URL` — 가 금지 목록에서 나와, `Name`/`Version`/`Requires-Python` 이 이미 받고
  있던 것과 같은 `pyproject.toml` 기반 정확값 검사로 들어갔다. 금지만 풀었다면 라이선스와
  소유자가 산출물에서 유일하게 검사되지 않는 메타데이터로 남았을 것이다. `License`,
  맨 `Author`, `Home-page`, `Download-URL`, `Maintainer`, `Maintainer-email` 은 계속
  금지다. 여기의 어떤 설정도 그것들을 내지 않으므로, 그 헤더가 있다는 것은 이 pyproject 가
  아닌 무언가가 썼다는 뜻이다. 두 산출물은 선언한 라이선스 파일을 비어 있지 않은 일반
  멤버로도 실어야 한다. wheel 에서는 `dist-info/licenses/LICENSE`, tarball 에서는 sdist
  루트다. 라이선스 파일을 가리키는 메타데이터 헤더는 파일에 대한 주장이지 파일이 아니다.
- `Development Status :: 3 - Alpha` → `5 - Production/Stable`.
- **`MutationNotAllowedError` → `KorailMutationNotAllowedError` 로 이름을 바꿨다(파괴적
  변경).** 예외 타입 스무 개 중 패키지 접두사가 없는 유일한 이름이었고, 자매 SRT 패키지는
  대응하는 이름을 이미 `SrtMutationNotAllowedError` 로 쓴다. 별칭은 남기지 않는다. 1.0.0
  에서 더한 별칭은 그 자체로 영구 계약이 되며, 지금 바꾸는 이유가 바로 아직 공짜라는
  것이다.

### Fixed

- `docs/RELEASE_GAP_PLAN.md` 의 srtgo 정정 부록에 남아 있던 철회된 주장 — "Korail uses
  **no** NetFunnel at all — only SRT does" — 을 본문에 맞춰 고쳤다. 본문은 이미 반대로
  말하고 있었다. `README.md` 와 `docs/IMPLEMENTATION_PROGRESS.md` 에서 `service_1` /
  `act_6` 게이트를 "아직 구현되지 않았다"고 적은 주석도 함께 고쳤다. 게이트는 있고, R39 를
  막고 있는 것은 등록되지 않은 라우트다.
- `scripts/reserve_pay_refund_roundtrip.py` 가 정작 출력해야 할 PNR 을 가리고 있었다.
  콘솔 스크러버가 13~19 자리 카드번호 패턴을 아무 텍스트에나 적용했는데 KORAIL PNR 이
  10진수 15자리라, 2026-07-25 실행에서 `LIVE HOLD CREATED   PNR [REDACTED_CARD]` 가 찍혔고
  복구 명령줄 안의 PNR 까지 가려졌다. 식별자 없는 미결제 예약만 남는 셈이다. 이제
  스크러버는 실제로 건네받은 카드 값 네 개만 정확히 값으로 치환하고 자릿수 패턴은 전혀
  적용하지 않는다. 15자리 연속 숫자는 모양만으로 Amex PAN 과 구별할 수 없고, PNR 은 반드시
  운영자에게 닿아야 하는 유일한 값이다. `redact_payload` 와 패키지의 `CARD_RE` 는 그대로다.
  일반 패턴은 알 수 없는 키 아래의 PAN 으로부터 mutation 페이로드를 지키는 자리에 있을 때
  옳다.
- `get_ticket_reservation_detail` 가 라이브 성공 본문을 거부했다. 성공 형태 처리는 APK 의
  DAO 선언에서 만들었는데 거기서는 모든 필드가 Java `String` 이다. 실제 서버는 좌석 행의
  `h_srcar_no` 를 JSON 숫자로 보내므로 첫 실제 예약에서 — 예약이 이미 생긴 뒤에 —
  `KorailProtocolError: ... h_srcar_no must be a string or null` 이 났다. 같은 이음매에서
  나온 세 번째 라이브 발견(`h_jrny_cnt` = `"0001"`, `h_st_prnb`/`h_cls_prnb` = 선언은
  `int` 인데 0으로 채운 문자열)이라 필드별로가 아니라 체계적으로 고쳤다.
  `certification.ReservationList`, `refunds.CommissionView`,
  `refunds.SelTicketInfo` 의 모든 단언된 스칼라가 — 응답·여정·좌석 층 모두 — JSON 문자열과
  JSON 숫자를 함께 받아 나머지 코드가 기대하는 문자열로 정규화한다. 앱이 이것을 못 느낀
  이유는 Gson 의 `JsonReader.nextString()` 이 숫자를 String 으로 강제하기 때문이다. 진짜
  잘못된 타입은 여전히 거부한다. 스칼라 자리의 bool, float, 리스트, 객체는 프로토콜
  오류다.
- `parse_reservation_hold_response` 가 예약 목록에서 예약을 다시 읽어내지 못했다. PNR 을
  잃었을 때 문서가 안내하는 복구 경로가 바로 그것이다. 목록은 `h_jrny_cnt` 를 JSON 정수
  `1` 로 보내는데 예약 응답은 문자열 `"0001"` 로 보내므로 파서가 예외를 냈고, 운영자는 실제
  예약을 취소하려고 예약 객체를 손으로 조립해야 했다. 이제 예약·결제 파서의 모든 스칼라가
  JSON 문자열과 JSON 숫자를 함께 받아 폼 빌더가 기대하는 문자열로 정규화하므로 `1`, `"1"`,
  `"0001"` 이 모두 `build_unpaid_reservation_cancel_form` 에 닿는다. 그쪽은 이미 수치로
  비교하고 있었다. 같은 관용이 PNR, 발권창구 번호, job 시퀀스, 정산 금액에도 적용된다.
  이 값들은 서버에 이미 존재할 수 있는 예약을 가리키므로, 하나를 거부하면 그 예약이 붕 뜬다.
  PNR 을 절대 잃지 않는 것이 유일한 일인 마지막 대비책
  `KorailClient._hold_from_reservation_response` 도 같이 정규화한다. bool, float, 리스트,
  객체는 여전히 프로토콜 오류다.
- `docs/RELEASE_GAP_PLAN.md` 의 NetFunnel 서술을 정정했다. Korail 이 "does NOT use
  NetFunnel at all" 이라는 말은 지나쳤다. 앱은 실제로 그 왕복을 배선해 두고 있다. 참인 것은
  어떤 Retrofit 요청 본문도 토큰 필드를 싣지 않으며 이쪽 라이브 호출이 토큰 없이
  성공한다는 것이다.

### Removed

- 여행변경 mutation 체인과 `ticket_change` 동의 범주 — `change_trip_reservation`,
  `rollback_trip_change`, `change_reservation_passengers`, 그리고
  `MutationConsent.allow_ticket_change`. 만들었다가 같은 날 거뒀다. 이 체인을 실행하려면
  결제된 승차권이 있어야 하고 변경수수료가 나가며 깨끗한 되돌리기가 없다. 되돌리기 쪽
  자체가 미검증인 경로에 돈을 쓰지 않고는 검증할 방법이 없었다. 체인이 시작되는 읽기 둘은
  남았고 아래에 있다. 분석은 `docs/RELEASE_GAP_PLAN.md` 에 남긴다. 중간 커밋을 가져간
  사람에게는 **파괴적 변경**이다.
- 비회원 오프라인 반환 짝과 비회원 세션 — `verify_offline_refund_ticket`,
  `execute_offline_refund`, `begin_non_member`, `end_non_member`,
  `KorailNonMemberSession`. 역시 만들었다가 같은 날 거뒀고 이유도 비슷하다. 이 짝의 전제는
  종이 승차권 실물이고 verify 호출이 거기 인쇄된 반환번호를 소모하므로 어느 쪽도 실행해 볼
  수 없다. 반환번호 철자들은 `redaction.py` 에 일부러 등록된 채로 둔다.
  `research.tripChgOgtk.do` 가 여전히 같은 네 부분 번호를 실어 나르고, 민감 키 집합에서
  빠진 철자는 무언가가 그것을 다시 들여오는 날 새어 나간다. 같은 조건으로 **파괴적
  변경**이다.
- **최상위 `__all__` 에서 이름 47개가 빠져 263 → 216 이 됐다(파괴적 변경).** 빠진 이름은
  전부 정의된 모듈에서 그대로 임포트할 수 있다. 이동이지 삭제가 아니며
  `from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS` 는 전과 똑같이
  동작한다. 달라진 것은 패키지가 *약속하는* 범위다. 1.0.0 이후로는 내보낸 이름을 거두면
  누군가가 깨지므로, 표면에는 호출자가 반드시 이름으로 부를 수 있어야 하는 것만 남긴다.
  클라이언트·설정·세션, 공개 메서드의 애너테이션에서 닿는 모든 타입, 오류, 동의 타입,
  그리고 호출자가 넘기거나 응답과 비교하는 도메인 값이다. 무엇이 어떤 이유로 빠졌는지는
  이렇다.
  - 전송 계층 상수: base URL, 앱 키, API 버전, 기기 화면 정보와 SDK 정수, NetFunnel 의
    URL·경로·서비스 ID·타임아웃, DynaPath 헤더 이름과 허용 목록, 부트스트랩 코드 목록.
    전부 `KorailConfig` 필드의 기본값으로 닿을 수 있고, 값을 바꾸려는 호출자는 어차피
    거기로 가야 한다.
  - DynaPath 토큰 기계: `generate_dynapath_token`,
    `generate_dynapath_encoding_table`, `build_dynapath_prefix`,
    `DynapathTokenGenerator`, `DynapathRequestContext`, 그리고 `KORAIL_DYNAPATH_*` 신원
    상수 다섯. `DynapathConfig` 와 `DynapathTokenSettings` 는 남는다. `KorailConfig` 의
    필드 타입이다.
  - 내부 라우트·정책 표: `KORAIL_MUTATION_ROUTES`, `KORAIL_NETFUNNEL_ROUTES`,
    `KORAIL_CARD_BEARING_MUTATION_CATEGORIES`, `EXCLUDED_API_DOMAINS`,
    `KORAIL_NETFUNNEL_GATED_OPERATIONS`. mutation 라우트 표가 논쟁적인데, 안전 정보의
    공개처럼 읽히기 때문이다. 그러나 짝인 `KORAIL_READ_ONLY_ROUTES` 는 애초에 내보낸 적이
    없고, 분류의 절반만 공개하는 것은 둘 다 `safety.py` 에 함께 두는 것보다 나쁘다.
  - 클라이언트가 대신 호출해 주는 파서: `parse_base_response`,
    `parse_reservation_hold_response`, `parse_reservation_payment_response`,
    `parse_discount_card_purchase_response`, `pair_transfer_itineraries`. 이들의 *반환*
    타입은 모두 그대로 내보내며, 호출자가 애너테이션에 쓰는 쪽은 그쪽이다.
  - `redact_mapping` 과 `redact_payload`. `MutationPreview` 가 생성 시점에 페이로드를
    마스킹하므로 기본 동작에서 잃는 것은 없다. 자기 로깅에 쓰려는 호출자는 이 둘과, 함께
    떨어져 나온 다른 헬퍼 넷을 `korail_mobile_api.redaction` 에서 임포트하면 된다.

### Security

- `ogtkRetPwd` 를 비롯한 원표 반환번호 네 값이 마스킹 대상이 됐다. `ogtkRetPwd` 는 세
  경로로 오간다. `research.cmtrInfo.do` 의 원표 분기에 붙는 맨 `@Field` (이 패키지는
  `build_commuter_info_form` 이 생긴 이래 계속 보내왔다), 인덱스가 붙은 `@FieldMap` 키,
  그리고 돌아오는 `OrgTk.ogtkRetPwd`. 셋 다 가려지지 않았다.
  `ogtkSaleWctNo`/`ogtkSaleDd`/`ogtkSaleSqno`/`ogtkSaleDt` 를 함께 등록한다. 반환번호의
  4분의 3만 가리면 나머지로 복원되기 때문이다. 행 인덱스는 `_index_stripped` 가 덮는다.
  지연증명 튜플 `Cmpn.dlayOgtk*` (`Cmpn.java:11-14`), 정산 행의
  `stlCrdNo`/`prepCrdNo`/`apvNo` (`Stl.java:5-16`), 그리고 할인카드 구매 mutation 이 이미
  돌려주는 `lumpStlTgtNo` 의 두 철자도 등록했다. `cmpnList`/`stlList` 는 일부러 파싱하지
  않고 `raw` 안에서 마스킹된 채로 둔다.
- `hidDscpNo`, `hidCustNo`, `hidFmlyNo`, `psrm_cl_cd` 가 `SENSITIVE_KEYS` 에 들어갔다.
  첫째는 쿠폰·국가유공자 증서 번호로, 들어올 때 이미 가려지던 `h_cpn_no` 와 같은 값이
  나가는 쪽이다. 나머지 셋은 고객번호, 가족 구성원 일련번호, 그리고 이미 가려지던
  `psrmClCd` 의 언더스코어 철자다.
- `redact_payload` 가 리스트 값을 `str()` 로 뭉개는 대신 원소 단위로 가리고 길이를
  유지한다. 이제 폼 키 하나가 여러 값을 가질 수 있는데, 리스트를 문자열로 만들면 모든
  원소가 리스트 자신의 따옴표 뒤로 숨어 `redact_text` 에 닿지 않는다.
- `txtCardNo_1..N` 이 `SENSITIVE_KEYS` 에 들어갔다. 들어오는 철자는 이미 가려지고 있었지만
  나가는 폼 키는 아니었고, 할인카드 예약의 dry-run 미리보기가 쓸 수 있는 카드번호를 평문으로
  찍었다.
- `redact_payload` 가 `txtCpNo` 와 인덱스가 붙은 `txtSrcarNo{i}`/`txtSeatNo{i}` 를 가린다.
  mutation 미리보기가 예약대기 통보번호와 지정 좌석을 드러내지 않는다. 차량·좌석 식별자는
  읽어 들이는 쪽에서는 이미 전부 가려지고 있었고, 이것은 같은 값이 나가는 쪽이다.

### 알려진 제약과 넣지 않은 것

- 특실 업그레이드의 `myTicket.reqUpgradeSeat` (`MyTicketService.java:23-24`)는 일부러 넣지
  않았다. 요청만 보면 금액도, 결제수단도, 확인 플래그도 없어서 잠깐 읽기로 구현했다. 그런데
  이 라우트의 **응답**이 `lumpStlTgtNo` 를 발급하고
  (`SpecialRoomUpgradeDao.java:13,19`), `procUpgrade` 가 그 일괄결제대상번호를
  `stlMnsCd` / `crdInpWayCd` / `ismtMnthNum` / `mnsStlAmt` 와 함께 받는다
  (`MyTicketService.java:21`). 결제가 소모할 정산 대상을 만드는 것은 가격을 조회하는 게
  아니라 미결제 구매를 만드는 것이다. 이 저장소가 `research.dcntCrdInfo.do` 에 이미 적용한
  판단("Despite the 'Info' in its path this is a PURCHASE")과 같고, 그래서 그 라우트가
  `KORAIL_MUTATION_ROUTES` 에 있다. mutation 으로도 등록하지 않았다. 짝이 되는 쓰기
  `procUpgradeSeat` 는 의도적으로 미룬 것이고, 구매 체인의 절반만 있으면 호출자가 정산
  대상을 만들어 놓고 정산할 수도 버릴 수도 없게 된다.
  `tests/test_ticket_change_chain_reads.py` 가 두 짝 모두 두 허용 목록 밖에 있음을 고정한다.
- 정기권 구매는 개시하지 않는다. 구매 짝(`pass.passReserve` / `pass.passPayIssue`)은 개시
  전 같은 주기 안에서 구현했다가 다시 지웠다. `reserve_commuter_pass`,
  `pay_for_commuter_pass`, `CommuterPass*` 타입, `KORAIL_COMMUTER_PASS_PAYMENT_FIELDS`,
  `commuter_pass` 동의 범주, `MutationConsent.allow_commuter_pass` 는 존재하지 않는다.
  전송한 적이 없고 개시된 버전이 이것을 실은 적도 없다.
  - **되돌릴 수 없는 돈을 쓰지 않고는 정확성을 증명할 수 없다.** 1개월 정기권이 대략
    ₩150,000~₩250,000 이고, 이 패키지에는 정기권 환불 라우트도 취소 라우트도 없다.
    `cancel_unpaid_hold` 는 승차권 취소다.
  - **비교할 캡처도 없다.** 개시된 앱조차 `passPayIssue` 를 낼 수 없기 때문이다.
    `PaymentActivity.isCommPaymentRequest()` 가
    `getIPaymentRequest() instanceof CommPaymentDao.CommPaymentResponse` 를 검사한다.
    Request 가 와야 할 자리에 Response 타입이다 (`PaymentActivity.java:502-503`, 바이트코드는
    `smali/…/PaymentActivity.smali:3963-3980`). 그래서 이 검사는 항상 거짓이고 DAO 는
    실행되지 않는다. 캡처도 없고 감당할 만한 라이브 호출도 없는 상태에서 디컴파일된 코드로
    조립한 폼은 참고문헌이 달린 추측이다.
  - **정기권 읽기는 그대로다.** `get_pass_menu`, `get_pass_available_dates`,
    `get_pass_schedule` 는 바뀌지 않았다.
  - **알아낸 것은 버리지 않고 남긴다.** README 의 정기권 절이 `passReserve` 필드 20개와
    그것을 채우는 루프, 한 열차 형태(`hidChtrnStnCd`/`Nm` 은 빈 문자열로 보내고
    `hidTrnNo2`/`hidTrnGpCd2`/`hidDtour2` 는 아예 없다), `passPayIssue` 의 `@FieldMap` 둘과
    v6.5.0 이 둘 다 채우는 이유, `hidPayAmount` 체인, `isCommPaymentRequest()` 결함,
    `passOtrReserve`/`passOtrPayIssue` 가 다른 상품(자유이용권: 내일로 / A-PASS /
    강릉패스)인 이유, 그리고 이 기능을 되살리려면 무엇을 증명해야 하는지를 기록한다.
  - `KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 는 이름 있는 집합으로 **남는다**. 지금은
    다시 `{"payment"}` 하나다. 원소가 둘이어서가 아니라 `category == "payment"` 가 잘못된
    질문이어서 별도의 동작 보존 변경으로 도입한 것이고, 카드를 싣는 범주가 GET mutation
    라우트를 소유하지 않는다는 검사된 불변식을 여전히 지고 있다.
  - `h_cust_nm`, `usernames`, `h_chg_mg_no` 와 그 모델 속성 이름
    (`customer_name`, `user_names`, `change_management_no`)이 `SENSITIVE_KEYS` 에서
    빠졌다. 전부 정기권 결제 폼 때문에 들어온 것들이고, 이 패키지에 남은 어떤 응답·폼·모델도
    이 값들을 싣지 않는다. `h_cust_nm` 과 `h_chg_mg_no` 는 APK 전체에서 DAO 하나
    (`CommReservationDao`)에만 나오는데 이제 여기서 파싱하지 않는다. 원래 있던
    `h_cust_no` / `customer_no` 항목은 그대로다.
- 알려진 제약: **`cancel_unpaid_hold` 는 환승 예약을 풀지 못한다.** `h_jrny_cnt` 가 수치로
  1 이어야 하기 때문이다. 앱에는 그런 제약이 없다.
  `DReservationConfirmActivity.java:269-278` 이 `getH_jrny_cnt()` 를 그대로
  `txtJrnyCnt` 로 넘기며 같은 고정값 `txtJrnySqno="0001"`/`hidRsvChgNo="000"` 을 함께
  보낸다. 고치는 방법은 `"1"` 로 박는 대신 예약 자신의 여정 수를 넘기는 것이다. 그 수정은
  환승 작업의 범위 밖인 취소 경로를 건드리므로, 고치지 않고 보고한다. 이 수정이 들어오기
  전에 보낸 라이브 환승 예약은 KORAIL 앱이나 웹사이트에서 취소해야 한다.
- `pay_with_card` 도 `refund` 도 라이브로 확인된 성공 봉투가 없다. 이 저장소에 기록된 어떤
  실행도 실제 결제를 성사시키거나 돈을 돌려받은 적이 없다. 문서는 실제 과금이 불가능하다고
  말하는 대신 이 사실을 적는다.
- `certification.ReservationList` 에는 쓰기 성격의 두 번째 Retrofit 오버로드
  `applyDisabilityCertification` (`CertificationService.java:22`)이 있다. 잡아둔 예약에
  장애인 증명을 적용하는 호출이다. 여기서는 읽기 오버로드만 옮겼고, 이 라우트의
  `KORAIL_EXACT_REQUEST_FIELDS` 항목이 읽기의 정확한 네 필드를 고정하므로, 경로가 같더라도
  쓰기 오버로드의 더 넓은 형태(`txtPsgDisc0019Cnt` 와 `@QueryMap` 여섯)는 전송 전에
  거부된다.
- `refunds.SelTicketInfo` 는 앱이 선언한 대로 보낸다. POST 이고 `h_purchase_history` 를
  싣는다. srtgo 가 보내는 방식(`ktx.py:791-800` 은 GET 을 쓰고 이 필드를 뺀다)과 다르다.
  앱의 모든 호출 지점이 이 플래그를 설정하며, 구매내역 화면에서는 "Y", 그 밖에서는 "N"
  이다.
- 정적 근거가 있는 정확한 읽기 계약 셋만 등록했다. 상태를 바꾸는 승무원 호출 라우트는
  제외된 채로 둔다.
- 라이브에서 얻은 서비스·메뉴·열차·차량 상수, 좌석지정, 예약, 발권, 결제, 취소, 그 밖의
  상태 변경 기능은 하나도 넣지 않았다. 새 계약은 합성 픽스처로만 덮인다.

### 검증 기록

범위를 정해 돌린 실서버 확인이 무엇을 확정했고 무엇을 확정하지 못했는지. 같은
내용이 근거 인용까지 붙어 `docs/verification-record.md` 와
`docs/IMPLEMENTATION_PROGRESS.md` 에 있다.

- **서버 규칙 둘은 이 패키지의 결함이 아니다.** `ERR299943 예약할인이 지원되지
  않습니다` 는 청소년 단독과 1~3급 장애+안내견 조합을 거절했고, 다른 여섯 조합은
  받아들여졌다. 이 코드는 디컴파일한 APK 어디에도 없고 폼은 앱과 정확히 같았으므로
  요청 모양이 아니라 계정 자격의 문제다. 별개로, hold 응답이
  `h_msg_cd = WRR664296`(주말 할인 안내)을 달고 왔는데 그것은 취소 가능한 진짜
  예약이었다. 성공의 기준은 `strResult = SUCC` 와 PNR 이지
  `h_msg_cd == IRR000018` 이 아니며, `IRR000018` 이 아닌 코드를 실패로 다루는
  경로는 하나도 없다.
- **승차권 참조 읽기 셋은 요청 모양까지만 확정됐다.** 예약이 0건인 계정으로 셋 다
  HTTP 200 으로 받아들여졌고 DynaPath 거절도 없었다. 일부러 틀린 인자에 대해
  서버는 키 세 개짜리 FAIL 봉투로 답했다 — `WRG200018` 입력값오류(PNR번호),
  `WRT100002` 창구번호미입력,미승인창구, `WRT100124` 반환번호를 확인해주세요. 각
  코드가 서버가 실제로 파싱한 필드를 지목하므로 이것이 요청 모양의 근거다. 이
  본문들은 오프라인 회귀로 그대로 고정돼 있다. **성공 본문은 미확인이고** APK 가
  선언한 합성 픽스처로만 덮여 있다 — 만들어 보려면 실제로 잡히거나 발권된 승차권이
  있어야 한다.
- **`reserve` → `cancel_unpaid_hold` → `pay_with_fake_card` 왕복이 실서버에서
  끝까지 돌았다.** hold 는 `h_msg_cd=IRR000018`, 취소는 `h_msg_cd=IRG000000`,
  가짜카드 결제는 `strResult=FAIL` 과 `h_msg_cd=WRT200342` 로 거절됐고 청구는
  없었다. 여기서 두 가지가 드러났다. 실서버 hold 응답의 `h_jrny_cnt` 는 앞에 0 이
  채워진 `"0001"` 이므로 `build_unpaid_reservation_cancel_form` 은 1 과 같은 숫자
  문자열이면 무엇이든 받는다. 그리고 서버가 이미 hold 를 만든 뒤 엄격 파싱이
  실패하면 `reserve` 는 PNR 만 실은 최소 hold 로 물러선다 — 만들어진 hold 는 언제나
  취소할 수 있어야 하기 때문이다. 왕복마다 예약 내역은 0행으로 돌아왔고 카드에
  청구된 것은 없다.
- **즉시·좌석지정·예약대기·입석+좌석 네 `KorailReservationJobType` 이 모두 실서버
  hold 를 만들었다.** 좌석지정은 `h_msg_cd=IRR000014`, 예약대기 확정
  (`confirm_standby_hold`)은 `h_msg_cd=IRZ000003` 이었다. 여기서 좌석 식별자의
  함정이 확인됐다 — 폼에 나가는 것은 `KorailSeatAssignment.seat_no` 이고 서버가
  응답 `h_seat_no` 로 돌려주는 것은 사람이 읽는 표시 `seat_spec` 이다. 둘을 맞대면
  제대로 된 예약이 틀린 것처럼 보인다. 입석+좌석은 `txtSrcarCnt` 를 요구하고,
  할인카드 예약은 members-only 자격이 없는 계정에서 `ERR299943` 로 거절된다.
- **읽기 표면의 실행 상태는 세어서 관리한다.** Retrofit 항목 165개 가운데 현재
  성공 32, 실패 10, 미실행 123 이다. 이 수치는 손으로 적는 대신
  `docs/api-status-by-service.md` 의 서비스별 표에서 유도하며, 표를 고치지 않고
  문장만 고칠 수 없다.
- **인증 읽기 재검증에서 확정된 응답 형태.** R13 은 `WRC800029` 를 돌려주고
  `KorailAppError` 로 올라오며 재시도되지 않는다. R32 와 현행 R43 은 0행, R45 는
  15행, 안전한 열차 검색은 10행으로 성공했다. R52 는 타입 붙은 여정이 없어
  `skipped_no_typed_leg` 로 남았고 R149 는 1행으로 성공했다. R17, R31, R39, R54 는
  호출되지 않았다. `strCustNo` 는 로그인 응답에서만 오고 `customer_no` 는 `repr`
  에서 가려진다. 어느 재검증도 상태변경 라우트를 부르지 않았고, 자격증명·식별자·원본
  응답을 남기지 않았다.
- **P0 읽기 표면은 오프라인 재생까지 확인됐다.** R30 `getFresScar` 는 정확히
  `strResult="SUCC"` 로 파싱됐고, R33 `getGuideSeatCnd` 는 서버가 준 좌석속성에
  대해 완전한 `FAIL` 봉투를 돌려주며 재시도 없이 `KorailAppError` 로 올라왔다.
  R37 과 R51 은 미실행이다. 저장한 원본을 오프라인으로 재생하면 27개가 파싱되고
  예상된 `KorailAppError` 하나가 나며 예상 밖 실패는 0이다.

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
