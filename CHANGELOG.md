# Changelog

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
- Added: `RefundTicketDetailResponse.discount_card`, plus `DiscountCardOnTicket`
  and `DiscountCardSection`. No new route and no new method: `SelTicketInfo`
  already returns `TicketDetailDao.TicketDetailResponse`, which carries
  `dcnt_crd_info` (`dao/refund/TicketDetailDao.java:233`) whenever the "ticket"
  being read is itself a 할인카드. The package was already fetching that object
  and discarding it.
  - This is the entry point to everything else in the 할인카드 surface. The
    card number is the sole input to `get_discount_card_usage_history`, the
    section rows are where `get_discount_card_schedule`'s station NAMES come
    from, and `h_dcnt_crd_trm_extn_psb_flg` is the only thing that enables
    기간연장 in the app (`Y4/C0907b.java:301` → `Y4/Q.java:1013-1026`).
  - The section list's wire key is `appSegList` — the Java FIELD name
    (`TicketDetailDao.java:124`), which is what Gson serialises. The getter is
    spelled `getAppSeg_info()` and is NOT the wire name; taking the getter
    would have produced a parser that silently found no sections.
- Added: loyalty READS, and the welfare entitlement one of them exposes —
  `KorailClient.get_korail_point_summary` and
  `KorailClient.get_mileage_history`, plus `KorailPointSummaryResponse`,
  `MileageHistoryRequest`, `MileageHistoryEntry`, `MileageHistoryResponse` and
  the five `KORAIL_MILEAGE_*` selector constants. The read-only boundary is now
  58 routes.
- Added: 할인카드(N카드) reads — `KorailClient.get_discount_card_usage_history`
  and `KorailClient.get_discount_card_schedule`, plus
  `DiscountCardScheduleRequest`, `DiscountCardUsage`,
  `DiscountCardUsageListResponse`, `DiscountCardScheduleTrain` and
  `DiscountCardScheduleResponse`. The read-only boundary is now 56 routes.
  **Implemented and NOT live-verified**: no account this project can reach owns
  an N카드, so both shapes come from the APK's DAOs rather than from an observed
  body.
  - `GET ticket.dcntCrdUseQry.do` (`ResearchService.java:51-52`) takes one
    identifier, `dcntCrdNo`, and the card number is never typed by a user: the
    N카드 ticket's own detail response carries it as
    `dcnt_crd_info.h_dcnt_crd_no`, which `Y4/C0907b.java:303` puts in an intent
    extra and `TicketNCardHistoryActivity.java:138,109` reads straight back into
    `setDcntCrdNo`. That number is now redacted everywhere it can appear.
  - `GET research.dcntCrdScheduleView.do` (`ResearchService.java:54-55`) is not
    an ordinary train search. An N카드 is sold against one to three fixed 구간,
    and this route answers "which trains on this 구간 does this card cover",
    which is why it is keyed by the card product rather than by station codes.
  - **Two of its fourteen `@Query` parameters are omitted, because the app omits
    them.** Neither builder (`u4/b.java:52-65`, `:67-81`) ever calls
    `setQryPgNo`, and the 1-section builder never calls `setUseTrmDno`, so
    Retrofit drops both nulls. They are registered in
    `KORAIL_OPTIONAL_REQUEST_FIELDS` rather than pinned, since a request that
    carries them is equally conformant — the response's `fllwPgExt` is the
    app's own paging signal (`SectionNCardInquiryActivity.java:406-408`).
  - `dcntCrdKndCd` has exactly two values in the whole app. `u4/b.java:60-61`
    sends `"B2N"` for the two original 1-section products (`B2N18120402`,
    `B2N18120403`) and `"MMM"` for everything else; `:76` hardcodes `"MMM"`.
    `DiscountCardScheduleRequest.for_card` reproduces that rule.
  - **No endpoint supplies the card product codes.** Every `dcntCrdKndMgNo` the
    app can send is a client-side literal (`NCard1SectionBookingActivity.java:28`,
    `NCard2SectionBookingActivity.java:34`, `NCard3SectionBookingActivity.java:28`,
    `q5/ViewOnClickListenerC6267a.java:73,76`), and `pass.passMenu.do` returns
    only a `detailType` string that selects an Activity, not a code list.
  - The two `dcntCrd*` routes that CHANGE state — `research.dcntCrdInfo.do` and
    `reservation.dcntCrdExtn.do` — are deliberately absent from the read-only
    allowlist and from `KORAIL_MUTATION_ROUTES`; a test pins their absence.
- Added: 환승 (transfer) search and reservation — `KorailClient.search_transfer_trains`,
  `KorailClient.search_trains_with_transfer_fallback` and
  `KorailClient.reserve_transfer`, plus `TransferItinerary`,
  `TransferSearchResult`, `pair_transfer_itineraries` and the four resolved
  codes `KORAIL_DIRECT_ITINERARY_CODE`/`KORAIL_TRANSFER_ITINERARY_CODE`
  (`"1"`/`"2"`), `KORAIL_DIRECT_JOURNEY_TYPE_CODE`/
  `KORAIL_TRANSFER_JOURNEY_TYPE_CODE` (`"11"`/`"14"`) and
  `KORAIL_MAX_JOURNEY_LEGS` (`2`). Reservation is no longer one-leg-only.
  **Implemented and NOT live-verified**: nothing here has been sent to KORAIL.
  - The app has one request builder for both cases. `C5/a.java:52-119` (`N0`) is
    a loop over the train array, and the array's **length** decides everything:
    `txtJrnyCnt` is `(length == 1 ? "1" : "2")` at `:55`, the loop writes at
    `i + 1` so journey indices are 1-based, and the sixteen `OJrny` keys repeat
    per leg. `build_reservation_form` is now a one-leg call into a leg-sequence
    core and `build_transfer_reservation_form` is the same core with two, so the
    **single-leg form is byte-for-byte what it was, key order included** — a
    contract test pins all 56 keys in order rather than trusting that.
  - Four codes were read from **bytecode**, not assumed. `K4/d` is `"1"`/`"2"`
    (`smali/K4/d.smali:36,64`) and does three unrelated jobs with the same two
    values — search `radJobId`, `txtJrnyCnt`, and the seed for `txtJrnySqno`.
    `K4/e` is **not** `"1"`/`"2"`: DIRECT is `"11"` (`smali/K4/e.smali:40`) and
    TRANSFER is `"14"` (`smali/K4/e.smali:68`), which jadx hides behind an
    unrelated same-valued constant. `S4/O.getSequenceNo` is `DecimalFormat("000")`, so the
    sequence numbers reach the wire as `"001"`/`"002"`.
  - **Both legs of a transfer carry `txtJrnyTpCd="14"`.** The ternary at
    `C5/a.java:60` sits inside the per-leg loop but tests the array *length*,
    while `:61` two lines below tests the loop *index*. Getting that backwards
    would send a form the app never sends, so both were re-read as
    `smali/C5/a.smali:306-338` (`array-length` re-evaluated every iteration) and
    `:343` (`if-nez v1`).
  - **Two legs is the app's ceiling, not a limitation chosen here.** The form has
    no journey-3 spelling: `OSeat.java:32-35` and `OSrcar.java:21-30` each split
    on "journey 1 or not", so a third leg would *overwrite* leg 2, and
    `ReservationRequest.java:114-117` reads back exactly two seat slots. Any
    other leg count is refused before a form is built.
  - The transfer **search** moves exactly one field. On `WRD000061` the app calls
    `setRadJobId(TRANSFER_SQ_NO.getCode())` on the request it already built and
    hands it on untouched (`DirectInquiryActivity.java:615-624` into
    `DirectInquiryActivity.java:284-296`, confirmed at
    `smali/…/DirectInquiryActivity.smali:1677-1689`).
    `chtnCnt`/`chtnRsStnCd1`/`trnGpCnt`/`trnGpCd1` are not part of it.
    `search_trains_with_transfer_fallback` reproduces the app's own flow and
    swallows `KorailNoDirectTrainError` and nothing else.
  - A transfer **response is not shaped differently**: the same flat
    `trn_infos.trn_info` list, paired positionally, rows 0/1 then 2/3, trailing
    odd row dropped (`a5/k.java:156-170`). `h_chg_trn_seq` is the server's copy
    of that position and is used as a consistency check, not as the pairing key.
    Paging gained the transfer half of the cursor —
    `TrainSearchContinuation.query_train_no2`, defaulting to `""` so a direct
    next page is unchanged.
  - Passenger mix composes **per booking** (`w4/a.java:47-74` builds `OPsg` once);
    cabin class and 좌석지정 compose **per leg** (`C5/a.java:59`/`:97` and
    `:120-133`). **예약대기 (`1102`) does not compose and is refused**: the app
    gates it twice, at `a5/k.java:120-127` (the standby check returns false for
    a non-direct result) and at `DirectInquiryActivity.java:434` (its only
    `setJobId("1102")`, on a screen `TransferInquiryActivity` overrides away).
- Added: a NetFunnel virtual-waiting-room client, `KorailNetFunnelClient`, so a
  gated operation can wait its turn instead of failing.
  **Off by default, and partly live-confirmed on 2026-07-26.** Probing on that
  date ran the protocol against `nf.letskorail.com` and settled the standing
  inferences: the wire format is the native SDK's `<code>:<params>`, the entry
  sequence is `5101` → `5002` → gated call → `5004`, and the queue is a pool of
  hosts rather than one. The slot-release path was exercised end to end.
  **The 201 queued path is still NOT live-exercised**: the server was not
  queueing (`5101` answered `nwait=0`), so the polling loop, the ttl sleep and
  the two bounds remain covered by offline fixtures only, exactly as the
  sibling SRT client's polling path is.
  - **The queue is a POOL, and the session lives on one node of it — the second
    defect the probing exposed, and the one worth an explicit warning.**
    `nf.letskorail.com` is a *front door* that load-balances the entry call; the
    node it lands on is the only one that can complete the session, and every
    reply names that node in its `ip`/`port`. This client sent every opcode to
    the front door, so slot release failed **about half the time,
    non-deterministically** — five acquire-then-release cycles:

    ```
    acquire said ip=rnf12.letskorail.com  -> release 503
    acquire said ip=rnf12.letskorail.com  -> release 503
    acquire said ip=rnf13.letskorail.com  -> release 503
    acquire said ip=rnf14.letskorail.com  -> release 200
    acquire said ip=rnf13.letskorail.com  -> release 200
    ```

    and the controlled pair that settles it:

    ```
    acquire on nf.letskorail.com (reply said ip=rnf13.letskorail.com)
      release via nf.letskorail.com    -> 503:msg="Wrong Server ID"
      release via rnf13.letskorail.com -> 200:key=&nwait=0&…
    ```

    **`Wrong Server ID` is literal**, and it will cost the next reader an hour
    if this is not written down: it reads like a credential or parameter
    complaint and is neither — the front door does not own a session a queue
    node issued. The releases that appeared to work were the balancer happening
    to land back on the owning node, which is also why the same key sometimes
    released fine. The app has always followed the naming: `T6/d.makeURL`
    (`T6/d.java:17-19`) rebuilds the URL from the previous reply's
    `getHost()`/`getPort()` unless `host_notmodify` is set, and that flag is
    `false` by default (`T6/h.java:43`, `isHostNotmodify()` at `:134-135`) and
    never set by `KTApplication`; `T6/i.java:50-53` is where `ip`/`port` are
    read. Declining it leaked roughly half of every slot taken, which is exactly
    the behaviour NetFunnel exists to prevent.
    So `5101` now goes to the front door while `5002` and `5004` go to the node
    that issued the session, the node rides on `KorailNetFunnelToken.node`, and
    it supersedes as the key does — a reply naming no node leaves the last one
    in force, and a bypass has neither a session nor a node.
  - **The redirect is constrained, not trusted.** A response choosing where the
    next request goes is what an origin guard exists to stop, so the naming is
    admitted only into the queue's own pool: `rnf<1-99>.letskorail.com`,
    lowercase, no leading zero, matched as whole labels, or the front door
    itself; `https` on port `443` and no other port, because the port is not
    followed on the server's say-so either. Anything outside the rule is a
    **hard error**, never a quiet fall-back to the front door — falling back
    silently is what produced the flaky release, since it turns "this reply is
    lying to us" into "this slot leaked", and a leaked slot makes no noise. The
    rule lives in `safety.py` beside the origin assertions rather than in the
    client, `assert_korail_netfunnel_origin` still refuses a node (it guards the
    configured origin and the entry call, so widening one guard cannot widen the
    other), `follow_redirects` stays `False`, and the canonical-origin guarantee
    for `smart.letskorail.com` is untouched.
  - **The `5101` key is a ticket, not a session — the first defect the probing
    exposed.** `acquire` originally returned the 5101 reply and `release` sent
    that key to `setComplete`, which the server refuses with
    `503:msg="Wrong Server ID"` every time, with or without `sid`/`aid`. Only a
    key `chkEnter` issued is completable, and it is a different, shorter one
    (252 characters became 104). So `acquire` now always performs the 5002,
    even when 5101 reported `nwait=0`, and **every step's key supersedes the
    one before it** — including each 201 poll, and including a 201 that echoes
    no key at all, where the last known key stays in force. A successful
    release answers `200:` with an *empty* `key=`, which parses as a release
    rather than as a truncated body. `503` is refused rather than accepted
    beside the `502` we do accept, and the keyless short-circuit in `release`
    is narrowed to a bypass (`300`), so no other token can skip the request
    silently. Note that `503` has **two** causes and the wire cannot tell them
    apart — an unexchanged ticket, or the wrong node — so the exception message
    names both.
  - **Read literally, the APK disagrees, and the live server wins.**
    `T6/g.java`'s poll loop leaves the moment the status is not Continue —
    `T6/g$a.smali:243-247` → `:282` → `:892` shows the fall-through is a
    `return` — so after a 200 from 5101 the app sends no 5002 and completes
    with the ticket. The `5002` stays unconditional anyway: `5101` → `5002` →
    `5004` is the only sequence ever seen to release cleanly, and whether the
    ticket would complete at its own node has never been probed. The APK does
    corroborate the supersession: one response object, overwritten at `:61` and
    `:107`, with `Complete()` sending whatever key arrived last (`:79`).
  - **KORAIL does not speak the JavaScript dialect, and this is the whole
    substance of the change.** `nf.letskorail.com` serves both apps, so the
    live-verified `srt-mobile-api` implementation was expected to be a template.
    It is not: SRT is a WebView over `netfunnel.js` and sends the browser
    dialect (`nfid`, `prefix`, `js=yes`, a trailing epoch), while `korail.apk`
    embeds STCLab's native Android SDK — the `T6`/`U6` packages — which sends
    none of it. The three requests are `5101` `opcode,sid,aid`
    (`T6/d.java:99-101`), `5002` `opcode,key` (`:54-55`) and `5004` `opcode,key`
    (`:78-79`), in that order, because `U6/a.java` renders the `addParam` list
    with `URLEncodedUtils.format`. So `sid`/`aid` ride on `5101` **only**, the
    opposite of the JS dialect; `ttl` is never sent back at all, being read only
    to decide how long to sleep (`T6/g.java:462`) and clamped to 30 seconds
    (`T6/h.java:40`) rather than the JS bundle's 5.
  - **The response shape was the one assumption no live run had checked, and it
    holds.** `T6/i.java:36-43` parses everything before the first `:` as the
    status code, so the reply must be `<code>:<params>` and not the JS
    dialect's `<rtype>:<code>:<params>` — feed the app the latter and it reads
    the code as 5002 and finds no key. Every 2026-07-26 reply arrived in exactly
    the native form. `parse_netfunnel_body` still rejects a `NetFunnel.gRtype=…`
    body and names that possibility in its error message, now as a diagnosis
    for a server that changed rather than as a hedge against our own guess.
  - **The key never rides on a KORAIL request.** No Retrofit interface in the
    app declares a `netfunnelKey`-shaped field on any route; the queue gates the
    call rather than parameterising it, which is why this is a separate client
    on a separate host and why reserve, pay, cancel and refund send exactly what
    they sent before.
  - **Off by default, enforced at construction.** `KorailConfig.
    netfunnel_enabled` is `False`, and `KorailNetFunnelClient` on a config
    without it raises before any socket exists. Enabling it adds a round trip
    and a failure mode to every gated operation and buys nothing until the
    server actually meters us. It is meant for peak season, which is why the app
    carries a separate peak-season inquiry queue (`act_8_2`) at all.
  - **The wait is bounded twice** — 20 polls and 60 seconds, whichever comes
    first. The app polls indefinitely (`T6/g.java:449`) behind a dialog a human
    can close; this library has none, and a queue is a wait rather than a retry.
    No retry logic was added.
  - **The slot is released on both paths**, as the app releases it from
    `BaseDaoHelper`'s `onPostExecute` (:105-107) whether or not the gated call
    raised. A failed release **raises** on the success path instead of being
    swallowed: the sibling repo bounded its key at 128 characters while real
    keys are 256, so every release was refused before it was sent and leaked
    every slot silently until a live run exposed it. The 2026-07-26 probe added
    two more real lengths — 252 from `5101` and 104 from `5002` — so the guard
    stays at 512 characters and is deliberately not tightened to any single
    observed length.
  - **Three exact query contracts are registered, not an allowlist loosened**,
    and the queue hosts have their own origin assertions — one for the front
    door and the entry call, a wider one for the pool, and a third that decides
    which of the two a given opcode gets. `KORAIL_READ_ONLY_ROUTES` is untouched
    at 54, so `post_form`/`get_json` can never reach `/ts.wseq`. `5003`, `5105`
    and `5106` are declared as constants and rejected by the guard.
- Added: server-side failures are classified on `h_msg_cd` instead of all
  arriving as one `KorailAppError`. New types — `KorailNoResultsError` (with
  `KorailNoDirectTrainError`), `KorailSoldOutError`,
  `KorailSeatUnavailableError`, `KorailReservationRefusedError`,
  `KorailInvalidRequestError`, `KorailNotEntitledError`,
  `KorailServiceUnavailableError`, `KorailAppUpdateRequiredError` — plus the
  exported `classify_app_error`. See the error-taxonomy table in README for
  which one means retry is pointless, which means re-login, and which means the
  request was fine and there was simply nothing there.
  - **Compatibility-preserving.** Every new type subclasses `KorailAppError`,
    so no existing `except` clause changes meaning, and `code`/`message`/`raw`
    stay on all of them so a caller can migrate incrementally.
  - **It never invents a failure.** Whether a response failed is still decided
    by `strResult` plus the app's own `WRC000288`; classification only picks
    which exception describes a failure that was already going to be raised.
    The app behaves the same way — any unrecognised code on a non-`FAIL`
    response goes to `onReceive()` as a success (`BaseActivity.java:629`) — so
    a warning attached to a success stays a success. `WRR664296`, which came
    back with `strResult=SUCC` and a real, cancelable PNR, is pinned by test,
    as are the APK's own success-side codes `IRR000014`, `IRT800005` and
    `WRS800036`.
  - **No retry logic was added.** The library still does not retry on its own
    initiative, and `reserve` is never retried, because a retried reserve is a
    duplicate booking.
  - Sold-out (`ERR211161`), the seat-specific refusals
    (`WRI411345`/`ERR911081`/`WRT800176`, for which the app offers automatic
    seat assignment rather than a dead end), the reserve refusals
    (`WRR800029`/`ERR911531`/`ERR911051`, which the app answers by navigating
    to the user's existing reservations), `WRD000061`, `WRG000000`, `P114`,
    `SEMGTK` and `SUPDATE` are all APK branches, cited file:line in each
    docstring. `P100`, `WRT300005`, `ERR299943`, `WRG200018`, `WRT100002` and
    `WRT100124` are this repository's live observations with zero APK hits and
    are labelled as such.
  - Anti-macro turned out not to be a code: `BaseDaoHelper.java:59-86` reads
    the `DynaPath-Result` header and shows the body's `message` instead of
    running the `h_msg_cd` ladder, so the existing `KorailDynaPathError` already
    is the anti-macro refusal. srtgo_plus's `MACRO` substring rule and srtgo's
    second sold-out code `IRT010110` are recorded as third-party-attested only
    and not encoded; a test asserts neither was adopted.
  - `[3]인증정보에 문제가 있습니다.` is deliberately left unclassified: no
    `h_msg_cd` was captured with it and the string is 0-hit in the APK, so
    classifying it would mean the Korean-text matching this change removes.
- Added: `reserve` reaches all three of the booking screen's job types through a
  keyword-only, defaulted `job_type` (`KorailReservationJobType`). The default
  is `IMMEDIATE` (`txtJobId="1101"`), the only value this package has ever sent,
  so every existing call is byte-for-byte unchanged.
  **Both variants were live-verified on 2026-07-26** by reserve -> read back
  -> cancel. `1103` booked the exact seats requested (compare the
  inventory's `seat_spec` to the detail's `h_seat_no`, not `seat_no`).
  `1102` on a sold-out train answered `IRR000014`, and
  `confirm_standby_hold` answered `IRZ000003`.
  - `SEAT_DESIGNATED` (`"1103"`) books named seats. `seats` takes one
    `KorailSeatAssignment` per passenger, carrying exactly the two identifiers
    the existing seat reads return — `SeatCar.car_no` /
    `SeatInventoryResponse.car_no` and `PhysicalSeat.seat_no`, with
    `KorailSeatAssignment.from_inventory()` pairing them and refusing a seat the
    read marked unsellable. The form appends `txtSrcarCnt` (the *seat* count)
    then `txtSrcarNo{i}`/`txtSeatNo{i}` from index 1, after the journey block.
    An ordinary hold still sends none of those keys at all — the app clears its
    `OSrcar` map and an empty Retrofit `@FieldMap` contributes no fields, so
    srtgo's unconditional `txtSrcarCnt="0"` is a shape the app never produces.
    A seat list whose length is not the passenger total, or that names the same
    seat twice, is refused before anything is built: a partial seat list is how
    a half-booked hold happens.
  - `STANDBY` (`"1102"`) is 예약대기. Eligibility is not "sold out" — the app
    reads one field, the search row's `h_wait_rsv_flg`, and compares it to the
    two-character literal `" 9"` (leading space; exported as
    `KORAIL_STANDBY_WAIT_FLAG`), on the 일반실 tab only. That, and nothing
    else, enables its button; the availability code is never consulted. So
    standby skips the "seats available" check that `1101` enforces, requires
    the flag and the general cabin, and computes `txtStndFlg` from the app's
    own `isStndSeat` instead of pinning `"N"`. korail2 describes the field as
    `-2`/`9`/`0`; only the 9 has any support in this app. Standby is
    **members-only** — the app's request declares itself not-non-member-enabled
    for this job id — which this client satisfies structurally, since every
    mutation needs a logged-in member session.
- Added: `confirm_standby_hold`, the second call a standby booking needs. A
  `"1102"` hold comes back with `h_msg_cd = IRR000014`
  (`KORAIL_STANDBY_HOLD_MESSAGE_CODE`), the only code that opens the app's
  예약대기 screen; that screen then POSTs `reservationWait.ReservationWait` with
  `txtPsrmClChgFlg` (좌석등급 변경 동의) and `txtSmsSndFlg`/`txtCpNo`. The phone
  number is sent only when SMS is on, must be 10 or 11 digits, and is otherwise
  omitted entirely rather than sent empty — matching the app, where the field is
  null and Retrofit drops it. It is a state-changing call on an existing PNR, so
  it goes through the same double-gated mutation transport as everything else,
  and it deliberately shares the **`reserve` consent category** rather than
  introducing a new one: it completes the booking an `allow_reserve` consent
  authorised, moves no money and releases no seat, and a new category would mean
  a caller who opted into placing a standby booking could not finish placing it.
  `reservationWait.ReservationWait` is now a fifth mutation route; the read-only
  allowlist and its guarantee are untouched. Never live-run.
- Added: `reserve` books an arbitrary passenger mix in either cabin. It takes a
  `KorailPassengerCounts` — one field per row the app's request has always
  carried (어른, 청소년, 어린이, 동반유아, 경로, 1~3급 장애, 4~6급 장애,
  안내견) — and a `KorailSeatClass` (일반실 `"1"` / 특실 `"2"`). Both are
  keyword-only and default to one adult in a general seat, so an existing call
  sends the identical form, byte for byte and key for key. `txtTotPsgCnt` is
  every row summed, the lap infant and the guide dog included, because that is
  how the app computes `TOTAL_PERSON_COUNT`; the mix must be non-negative, hold
  at least one passenger, and stay within
  `KORAIL_MAX_PASSENGERS_PER_RESERVATION` (9, the cap the app's passenger
  picker enforces). No discount-card field accompanies a discounted row: the
  app's `OPsg` declares only `txtCardNo_`, written solely by the separate N-card
  request, and korail2's/srtgo's `txtCardCode_`/`txtCardPw_` appear nowhere in
  the decompiled app. A 특실 hold requires the train's special seats to be
  evidenced as available, not its general ones. Live-verified on 2026-07-26 by
  reserve->cancel round trips: two adults in a general seat (hold total
  119,600 = 2 x 59,800) and one adult in 특실 (read back as `h_psrm_cl_nm='특실'`,
  `h_rcvd_amt=83,700`). The 특실 hold also demonstrates why the payment amount
  must come from `h_tot_rcvd_amt`: its `h_tot_prc` reads `59,800`, so the old
  builder would have underpaid by 23,900 KRW. Other passenger types and mixes
  of types remain static-evidenced and have never been transmitted.
- Real (chargeable) card payment is now possible, as an explicit, additive
  opt-in. `MutationConsent` gains `real_card_acknowledged` (default `False`):
  the caller's acknowledgement that a real, chargeable PAN will be transmitted
  in the clear and that money will actually move. Because it defaults to
  `False`, every consent written before it existed means exactly what it meant
  before and the default posture is unchanged — fake-card-only.
- Added `KorailClient.pay_with_card`, beside an unchanged `pay_with_fake_card`.
  The new method requires `real_card_acknowledged=True` AND
  `fake_card_only=False`; the old one still refuses anything but a test card,
  so its name keeps meaning what it says. Both build the same
  `build_card_payment_form` and leave through the same double-gated
  `post_mutation_form`, so a real payment cannot drift from the wire shape that
  was verified live. `pay_with_card` returns the parsed payment envelope rather
  than raising on a FAIL, because that envelope is the only record of what
  happened to the money and of whether the hold is still cancellable.
- Added `scripts/reserve_pay_refund_roundtrip.py`, the operator script for one
  full reserve → pay → refund round trip on a real card. Three environment
  opt-ins are required (`KORAIL_MOBILE_API_LIVE=1`, `KORAIL_LIVE_MUTATION=1`,
  `KORAIL_LIVE_REAL_CHARGE=1`); the card is read from the environment only,
  never a file and never argv. It refuses to start unless the account holds
  zero reservations, prints the PNR the instant it exists, cross-checks the
  amount owed against an independent server read before paying, prints the
  refund amount and fee before refunding, and on any later failure prints an
  unmissable banner with the PNR, what is outstanding, and a runnable recovery
  command (`--recover` with `KORAIL_RECOVER_PNR`). The PAN, PIN digits, expiry
  and birthday are scrubbed from every output path including exception text;
  the PNR deliberately is not, because losing it is the worst outcome.
- Added three read-only routes found by comparing the package against four
  third-party reference clients (srtgo, srtgo_plus, ryanking13/SRT, korail2);
  all three are declared in our own decompiled APK. `get_ticket_reservation_detail`
  reads one held reservation back by PNR (`certification.ReservationList`,
  `CertificationService.java:45-46`), giving an independent view of `h_wct_no`
  and the per-seat `h_rcvd_amt` rows the payment form settles.
  `get_refund_commission` (`refunds.CommissionView`, `RefundService.java:19-21`)
  reports `ret_amt`/`ret_fee`/`prg_psb_flg`, and `get_refund_ticket_detail`
  (`refunds.SelTicketInfo`, `RefundService.java:23-25`) reports the refund
  target's ticket detail including `retPsbFlg`. Together the latter two are the
  "how much comes back and what is the fee" pre-check that `refund` has never
  had; none of the four reference clients implements either one. The boundary is
  now 54 exact login/read routes and 60 public methods.
- Added the consent and safety foundation for state-changing requests. Frozen
  `MutationConsent` (per-category `allow_*` default `False`, `dry_run` default
  `True`, `fake_card_only` default `True`) and frozen `MutationPreview` (whose
  payload is forced through `redact_payload` on construction, so a preview can
  never hold a raw PAN, PNR, or sale identity) live in `consent.py`. The route
  registry became tiered: `KORAIL_MUTATION_ROUTES` holds the four
  state-changing routes and is deliberately never added to
  `KORAIL_READ_ONLY_ROUTES`, while `KORAIL_MUTATION_ROUTE_CATEGORIES` and
  `assert_mutation_route_category` cross-check the caller's consent category
  against the route, so a consent for one category cannot post another
  category's route. Redaction was extended over the mutation fields, including
  the card number, PNR, original-ticket sale identity, return password,
  `txtPrnNo`, and `h_orgtk_sale_wct_no`.
- Added four consent-gated mutation methods: `reserve`, `cancel_unpaid_hold`,
  `pay_with_fake_card`, and `refund`. Each requires an authenticated session
  and a `MutationConsent` that opts into its own category, and each is denied
  with `MutationNotAllowedError` before anything is built otherwise. With the
  default `dry_run=True` a method validates its inputs and returns a redacted
  `MutationPreview` of the form that *would* be posted, sending nothing. Only a
  `dry_run=False` consent transmits, and only through `post_mutation_form`, the
  single send path that re-checks consent, refuses a `dry_run=True` consent,
  and asserts both the mutation route and its category. The read-only send path
  (`post_form`/`get_json`) still refuses every mutation route.
  `pay_with_fake_card` additionally refuses unless `fake_card_only` is set, at
  both the method and the send gate, because the payment form carries the card
  number in the clear; only a non-chargeable test card is supported.
- Added `refund` on the same gated send path. Its live send path is fully
  active code, not blocked, but it has never been exercised against the live
  server: a refund acts on a settled ticket, and this package's fake-card
  payment is always declined, so no paid ticket is produced here. Its request
  contract, gates, and redaction are covered by offline tests only, and it must
  be treated as unverified against the real service.
- Added five authenticated, one-shot ticket-reference reads for delivery
  recipient details, ticket-duplication count, PBP acceptance specifications,
  platform numbers, and recent delivery history. The exact static contracts
  accept only repr-hidden typed ticket/PNR provenance, preserve repeated
  `tkRetNo` order with exact count equality, derive recent-history `custMgNo`
  only from the login session, and force DynaPath off. The implementation made
  no live request; the pre-R149 inventory was 31 successful, 10 failed, and
  124 unexecuted out of 165. The package boundary is now 51 read/login routes
  and 57 public methods, with the DynaPath allowlist unchanged at six paths.
  The ticket-reference implementation itself used no live I/O and added no
  mutation capability.
- Added closed tagged public reads for gift-ticket list modes, commuter jobs
  `a`/`b`/`c`, and one/two-leg fare quotes. Exact ordered forms preserve R31
  duplicate fields and intentionally omit R52 `trnCnt`; only R52 uses the
  pre-existing conditional DynaPath path.
- Added strict synthetic response models/parsers plus an internal exact
  request builder for R39, while leaving its NetFunnel `service_1` / `act_6`
  route unavailable. R54 also remains transport-held. At that historical,
  pre-revalidation implementation step, the DynaPath allowlist and live
  inventory remained unchanged, no live call was made, and no mutation
  capability was added. The current boundary is 51 read/login routes and 57
  public methods.
- Added four authenticated fixed/account-shaped reads for multi-child discount
  targets, login-customer trip information, current or bounded-history MaaS
  service details, and trip-change date lookup. Their exact routes and ordered
  forms are DynaPath-disabled and validation occurs before transport.
- Added strict synthetic parsers and frozen repr-safe models for R13, R32,
  R43, and R45. R54 tour-train response parsing is static-contract support
  only: no client method, safety route, or raw-string request builder exists.
- Initially added four typed P0 train reads from static APK evidence for
  free-seat car guidance, guide-seat conditions, seat-assignment schedules,
  and merged-seat inquiry.
- Initial implementation added frozen closed request objects, exact POST field
  allowlists, strict response parsers, repr-hidden identifiers/free text/raw
  mappings, and synthetic-only fixtures; that implementation step added no
  live call or DynaPath route.
- Added typed session-unverified pass-menu, commuter-kind-menu, and
  crew-request option reads with caller-required runtime discriminator codes;
  any live verification starts only after login.
- Added frozen repr-safe models, strict parsers, synthetic fixtures, and
  offline route, request, error, export, and documentation coverage.
- Added three static-evidenced limousine schedule and seat-inventory reads with
  closed caller-supplied query dataclasses, exact POST allowlists, typed
  repr-safe parsers, one-shot session/error handling, and DynaPath disabled.
- **Added: this package is licensed.** `LICENSE` carries the Apache License
  2.0 verbatim, and `pyproject.toml` declares it in the PEP 639 SPDX form
  (`license = "Apache-2.0"`, `license-files = ["LICENSE", "NOTICE"]`) rather
  than the deprecated `license = {text = ...}` table, which setuptools now
  warns on and will reject outright from 2027-02-18. The build floor moved to
  `setuptools>=77` for the same reason: earlier versions ignore `license-files`
  silently, producing a wheel that claims a licence and ships no licence text.
  No `License ::` classifier accompanies it — PEP 639 makes the two mutually
  exclusive. `NOTICE` is declared alongside `LICENSE` rather than left at the
  repository root alone: Apache-2.0 §4(d) requires a redistributor to carry the
  attribution notices forward, and a wheel that omits the file makes that
  impossible. Both artifacts now carry both files.
- Added: owner and canonical-URL metadata. `authors` names `yakisoba0728` and
  a contact address — spelled in `pyproject.toml`, not repeated here, because
  `tests/test_readme.py` forbids a bare email address in the evidence
  documents and that gate is worth more than the duplication.
  `[project.urls]` pins Homepage, Repository, Issues and Changelog at
  `https://github.com/yakisoba0728/korail-mobile-api`.
- Added: `korail_mobile_api.__version__`, with a test asserting it equals
  `project.version`. Nothing in the build keeps a hand-written dunder and a
  hand-written TOML literal in step; that test is the only thing that does.
  It is deliberately absent from `__all__`.
- **Added: `tests/test_public_surface_rule.py`**, which is what stops the
  above from being undone by the next person with a convenient name to export.
  It holds no list of names — a hand-maintained name list is exactly what
  rots. It derives `__all__`'s expected contents from `__init__.py`'s import
  statements via `ast` (so dropping an `__all__` entry while leaving the
  import behind fails), refuses any name from a module not on a short
  module-level policy list, refuses `parse_*`/`pair_*` outright, walks the
  transitive closure of every public client method's annotations and requires
  each package-defined type in it to be exported, and requires every exported
  non-type to appear in a `DOMAIN_CONSTANTS` table with a written reason. The
  file is shared verbatim with the SRT package below a marked per-repository
  header.
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
