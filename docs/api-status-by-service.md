# KORAIL Mobile API Status by Service

기준: `analysis/reports/api-endpoints.tsv`, 2026-07-09 안전 범위 실제 호출
스냅샷, 2026-07-14 MAAS 메뉴·역 목록 읽기 검증, 2026-07-15 객차·좌석
구조, P0 열차 읽기, 고정/account-shaped 및 R149 읽기 검증.

**상태 변경 API에 대한 이 문서의 범위는 2026-07-26에 바뀌었다.** 원래 문장은
"결제/예약 생성/취소/환불/체크인/회원탈퇴처럼 운영 상태를 바꿀 수 있는 API는
실행하지 않았다"였고, 그건 이제 사실이 아니다. 예약 생성·취소, 가짜카드 결제,
그리고 2026-07-27의 장바구니 담기(`cart.addCartList`)가 실제로 실행됐다.
여전히 실행하지 않은 것은 **실카드 결제·환불·체크인·회원탈퇴**다.

실행 방식이 두 종류라는 점도 표에서 구분되지 않으므로 여기 적는다. 아래 성공
33건 중 대부분은 2026-07-09~15의 **스크립트 실행**(bounded live structural
evidence)에서 나왔고, `cart.addCartList`(성공)와 `self.seatChgInfo.do`(실패)
2건은 2026-07-27의 **수기 실행**이다. 어느 스크립트도 그 둘을 재현하지 않는다.

| 상태 | 건수 |
|---|---:|
| 성공 | 33 |
| 실패 | 14 |
| 미실행 | 118 |
| 전체 | 165 |

상태 기준: `성공`은 실제 호출 성공 또는 HTTP 200 캐시성 응답, `실패`는 실제 호출했으나 404/앱 오류/입력 오류, `미실행`은 운영 상태 변경 가능성 또는 실데이터 부족으로 보류한 항목이다.

Package coverage: 60 exact login/read routes and 77 public methods. Sixty-four
are audited login/read methods or local helpers; the other thirteen are
consent-gated mutations: `reserve`,
`reserve_transfer`, `reserve_merge`, `reserve_with_discount_card`,
`confirm_standby_hold`, `cancel_unpaid_hold`, `pay_with_fake_card`,
`pay_with_card`, `refund`, `add_to_cart`,
`register_discount_card`, `extend_discount_card`
and `recalculate_price`. Each is
denied without a matching-category `MutationConsent`; with the default
`dry_run=True` each only returns a redacted `MutationPreview` (sending nothing),
and only a `dry_run=False` consent performs the live state change, exclusively
through the double-gated `post_mutation_form` path. `pay_with_fake_card`
additionally requires `fake_card_only`, so it still sends only non-chargeable
test cards; a real, chargeable card is reachable only through `pay_with_card` on
a consent that explicitly sets `real_card_acknowledged=True` and
`fake_card_only=False`, and the transmit gate refuses a payment consent that
claims neither or both. reserve/cancel/pay were verified live (fake card
declined, no charge); `pay_with_card` and `refund` have no live-verified success
envelope. The read-only
send path still refuses every mutation route. The package
now exposes the ten
previously successful but unwrapped reads plus the already registered service
status cache as 11 public methods, plus the two typed car and physical-seat
reads, three static P0 menu/reference reads, and the static-only R20
pass-schedule candidate read. The latter P0 reads use only
APK/source evidence and synthetic fixtures; they are session-unverified, any
live verification starts only after login, and no live result is claimed. The
seat reads now have bounded live structural evidence: both returned
`IRG000000`/`SUCC`, with 5 cars and 75 seat rows, without retaining raw values
or identifiers. A later eleven-method wrapper replay parsed five reads, stopped
four at `KorailProtocolError`, and omitted two identifier-dependent calls. The
runtime rows below remain route-level historical outcomes; the four current
wrapper parser mismatches are tracked in `docs/IMPLEMENTATION_PROGRESS.md`.
The four P0 train-adjacent routes were initially implemented from static APK
contracts with synthetic fixtures only. A later bounded authenticated run made
28 requests and received 28 responses, producing 25 successful operations, one
expected typed application failure, and three input-dependent skips.
Deposit-bank and trip-menu reads succeeded after login. R30 `getFresScar`
returned exact `strResult="SUCC"` and parsed, while R33 `getGuideSeatCnd`
returned a full `FAIL` application envelope for the server-supplied seat
attribute, surfaced as `KorailAppError`, and was not retried. R37
`getAssignScheduleView` and R51 `getMergeSeatsInquiry` remain static-only and
unexecuted. Offline raw replay yielded 27 parsed responses, one expected
`KorailAppError`, and zero unexpected failures. The three additional limousine
P0 wrappers remain static-contract-only.

Historical pre-revalidation inventory was 28 successful, 9 failed,
and 128 unexecuted. A later bounded authenticated read-only revalidation used
an empty advertising ID, logged in once, and confirmed that the repr-hidden
`customer_no` was available. R13 made one request and returned `WRC800029`,
surfaced as `KorailAppError` and was not retried. R32 succeeded with 0 rows,
current-form R43 succeeded with 0 rows, R45 succeeded with 15 rows, and the
existing safe train search succeeded with 10 rows. R52 made zero requests and
was recorded as `skipped_no_typed_leg`; R17, R31, R39, and R54 were not called.
No mutation route was called, and no credential, identifier, or raw response
value was retained. At that pre-R149 point, inventory was 31 successful, 10
failed, and 124 unexecuted entries out of 165.

R137, R138, R146, R148, and R149 now have static-only typed wrappers with exact
authenticated forms, strict response parsers, repr-safe data, one-shot
transport, and DynaPath disabled. At implementation completion no live request
had been made, all five rows were unexecuted, and the pre-R149 inventory was 31
successful, 10 failed, and 124 unexecuted. Package coverage is 54 exact routes
and 65 public methods; the DynaPath allowlist remains six paths.

A later bounded authenticated read-only revalidation used an empty advertising
ID, made one successful login call, confirmed logged-in state and
customer-number presence, and called only R149 once. R149 succeeded with one
row and was not retried; R137, R138, R146, and R148 made zero calls. No
mutation, raw response, PII, credential, or server message was retained.
Current inventory is 33 successful, 14 failed, and 118 unexecuted out of 165.

## Service Index

| Service | 역할 | 총 | 성공 | 실패 | 미실행 |
|---|---|---:|---:|---:|---:|
| `AddService` | 부가서비스 예약/구매/도움서비스 | 5 | 0 | 0 | 5 |
| `BusReservationService` | 연계 교통 예약 목록, 좌석, 변경/취소 확인 | 4 | 0 | 0 | 4 |
| `CacheService` | 앱 공지, 메인, 서비스 점검 캐시 조회 | 3 | 3 | 0 | 0 |
| `CalendarService` | 운행일 캘린더 조회 | 1 | 1 | 0 | 0 |
| `CartService` | 장바구니 및 MAAS 예약 상태 | 3 | 2 | 0 | 1 |
| `CashReceipt` | 현금영수증 발급 | 1 | 0 | 0 | 1 |
| `CertificationService` | 할인/자격 인증 및 증빙 | 12 | 0 | 1 | 11 |
| `CommonService` | 공통코드, 약관, 앱 설정, QR 위치 인증 | 11 | 6 | 0 | 5 |
| `CompensateService` | 보상 환불 대상 조회 및 실행 | 3 | 0 | 1 | 2 |
| `CustService` | 고객 할인 대상 조회 | 1 | 0 | 1 | 0 |
| `DelayService` | 지연증명, 지연료, 지연환불 조회/신청 | 9 | 1 | 1 | 7 |
| `GiftInfoService` | 승차권 선물 | 1 | 0 | 0 | 1 |
| `GifticketService` | 기프티켓 조회/예약/이력 | 4 | 0 | 2 | 2 |
| `IndependentService` | 사용자 부가정보 등록 | 1 | 0 | 0 | 1 |
| `LoginService` | 로그인, 로그아웃, 회원번호/비밀번호 확인 | 7 | 1 | 0 | 6 |
| `MileageService` | 마일리지 적립/알림 | 3 | 0 | 0 | 3 |
| `MyTicketService` | 내 승차권 및 구매이력 조회 | 3 | 1 | 0 | 2 |
| `NFilterService` | NFilter 보안 키 생성 | 1 | 0 | 1 | 0 |
| `PassCardService` | 패스카드/할인권 등록 및 조회 | 4 | 2 | 0 | 2 |
| `PassService` | 정기권/패스권 조회, 예약, 결제, 반환 | 8 | 2 | 1 | 5 |
| `PayService` | 간편결제/Payco/포인트/결제수단 | 12 | 0 | 0 | 12 |
| `PaymentService` | 예약 결제 실행 | 1 | 0 | 0 | 1 |
| `ProductService` | 관광/여행상품 조회 | 4 | 2 | 0 | 2 |
| `PushService` | 푸시 설정 및 승무원 호출 | 4 | 0 | 0 | 4 |
| `RailPlusService` | RailPlus 자동충전 조회 | 1 | 0 | 0 | 1 |
| `ReceiptService` | 승차권 영수증 조회 | 1 | 1 | 0 | 0 |
| `RefundService` | 승차권 환불/반환 실행 | 5 | 0 | 2 | 3 |
| `ResearchService` | 열차/좌석/N카드 관련 조회 | 11 | 3 | 2 | 6 |
| `ReservationCancelService` | 예약 취소 | 3 | 0 | 0 | 3 |
| `ReservationService` | 승차권 예약 및 좌석 조건 | 4 | 1 | 1 | 2 |
| `ReservationWaitService` | 예약대기 신청 | 1 | 0 | 0 | 1 |
| `SeatMovieService` | 열차 스케줄 및 예약 조회 | 3 | 1 | 0 | 2 |
| `TicketService` | 발권, 승차권 관리, 체크인, 티켓 정보 | 19 | 3 | 1 | 15 |
| `TrainsInfoService` | 열차/객차/자유석 정보 조회 | 6 | 3 | 0 | 3 |
| `XPointService` | OK캐쉬백/X포인트 인증 및 적립 | 5 | 0 | 0 | 5 |

## AddService

- 역할: 부가서비스 예약/구매/도움서비스
- 상태: 총 5개 / 성공 0 / 실패 0 / 미실행 5

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 1 | `additionalService` | POST | `/classes/com.korail.mobile.addService.reserve.do` | 부가서비스 예약/신청 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo, jrnySqno, saleWctNo, saleDt, saleSqno, jobDvCd, addSrvId, reqQnty, helpSrvTgtCnt, rcpSqno, cncTgtCnt, addSrvReqNo | `AdditionalServiceDao.AdditionalServiceResponse` |
| 2 | `dealCarBuy` | POST | `/classes/com.korail.mobile.addService.buyConfirm.do` | 부가서비스 구매확정 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, addSrvCnt, addSrvReqNo | `BaseResponse` |
| 3 | `getExtraProductList` | POST | `/classes/com.korail.mobile.addService.reserveList.do` | 부가서비스 예약 목록 조회 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo | `ExtraProductListDao.ExtraProductListResponse` |
| 4 | `helpSrvCust` | POST | `/classes/com.korail.mobile.addSrv.helpSrvCust.do` | 도움서비스 고객 신청/조회 | 미실행 | 미검증 | Device, Version, Key, saleWctNo, saleDt, saleSqno, reqCnt, reqAddSrvDvCd, reqAddRcpSrvCd, reqCustNm, reqCntcChnCont, qryDvCd, addSrvDvCd, rcpSqno | `HelpSrvCustDao.HelpSrvCustResponse` |
| 5 | `helpSrvTk` | POST | `/classes/com.korail.mobile.addSrv.helpSrvTk.do` | 도움서비스 승차권 조회 | 미실행 | 미검증 | Device, Version, Key, saleWctNo, saleDt, saleSqno | `HelpSrvTkDao.HelpSrvTkDaoResponse` |

## BusReservationService

- 역할: 연계 교통 예약 목록, 좌석, 변경/취소 확인
- 상태: 총 4개 / 성공 0 / 실패 0 / 미실행 4

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 13 | `reservationCancelCheck` | POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | 예약 취소 가능 확인 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtPnrNo, txtJrnySqno, txtJrnyCnt, hidRsvChgNo | `BaseResponse` |
| 14 | `reservationChange` | POST | `/classes/com.korail.mobile.reservation.reservationChange.do` | 예약 변경 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo, chgTno, totPrnb, stndFlg, evntWctFlg, wctHndgCncDvCd, lrgCrgFlg, psgCnt, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `ReservationChangeDao.ReservationChangeResponse` |
| 15 | `reservationList` | POST | `/classes/com.korail.mobile.lmu.scdlQry.do` | 예약/스케줄 목록 조회 | 미실행 | 미검증 | Device, Version, Key, dptDt, dptRsStnCd, arvRsStnCd, tmGpCd, psrmClCd, dptTm, trnNo, seatAttCd, rsvSaleDvCd | `BusReservationListDao.BusInquiryResponse` |
| 16 | `reservationSeatList` | POST | `/classes/com.korail.mobile.lms.TResidualSeatsResearch.do` | 잔여좌석 조회 | 미실행 | 미검증 | Device, Version, Key, trnClsfCd, trnGpCd, runDt, trnNo, srcarNo, psrmClCd, dptRsStnCd, arvRsStnCd, seatAttCd, dptStnRunOrdr, arvStnRunOrdr, totPsgCnt, gdNo, isArrow | `BusReservationSeatListDao.SeatListResponse` |

## CacheService

- 역할: 앱 공지, 메인, 서비스 점검 캐시 조회
- 상태: 총 3개 / 성공 3 / 실패 0 / 미실행 0

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 6 | `checkService` | GET | `/file/CACHE/MobileService.cache` | 서비스 점검/캐시 확인 | 성공 | S000 시스템 점검 작업으로‘26.07.08. 01시 30분 ~ 04시 30분까지 승차권 예매 서비스를 일시 중지 하오니 이점 양해 부탁드립니다. | timeStamp | `BaseResponse` |
| 7 | `getAppData` | GET | `/file/CACHE/prdMobilePlusMain.cache` | 앱 메인 캐시 조회 | 성공 | HTTP 200(비JSON/캐시성 응답 포함) | timeStamp | `AppDataDao.AppDataResponse` |
| 8 | `getNotice` | GET | `/file/CACHE/prdMobilePlusNotice.cache` | 공지 캐시 조회 | 성공 | HTTP 200(비JSON/캐시성 응답 포함) | timeStamp | `NoticeDao.NoticeResponse` |

## CalendarService

- 역할: 운행일 캘린더 조회
- 상태: 총 1개 / 성공 1 / 실패 0 / 미실행 0

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 132 | `getTrainCalendar` | GET | `/classes/com.korail.mobile.schedule.runDt` | 운행일 캘린더 조회 | 성공 | API.I00000 Success |  | `TrainCalendarDao.TrainCalendarResponse` |

## CartService

- 역할: 장바구니 및 MAAS 예약 상태
- 상태: 총 3개 / 성공 2 / 실패 0 / 미실행 1

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 9 | `addCart` | POST | `/classes/com.korail.mobile.cart.addCartList` | 장바구니 추가 | 성공 | `SUCC`/`IRZ000002`, 2026-07-27 수기 실행; 추가된 행을 `getCartList`로 확인 | Device, Version, Key, hidPnrNo | `BaseResponse` |
| 10 | `getCartList` | POST | `/classes/com.korail.mobile.cart.showCartList` | 장바구니 목록 조회 | 성공 |  | Device, Version, Key, pnrNo, addSrvReqNo | `CartListDao.CartListResponse` |
| 11 | `verifyMaasStatus` | POST | `/classes/com.korail.mobile.maas.rsvStt.do` | MAAS 예약 상태 확인 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, addSrvDvCd, addSrvReqNo, coptEntRsvNo, lumpStlTgtNo | `BaseResponse` |

## CashReceipt

- 역할: 현금영수증 발급
- 상태: 총 1개 / 성공 0 / 실패 0 / 미실행 1

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 12 | `issue` | POST | `/classes/com.korail.mobile.cashReceipt.issue.do` | 현금영수증 발급 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, cashRcetTxnDvCd, vltIsuFlg, cashRcetAthnMtdCd, athnDmnRcgnNo, apvCnt, FieldMap | `BaseResponse` |

## CertificationService

- 역할: 할인/자격 인증 및 증빙
- 상태: 총 12개 / 성공 0 / 실패 1 / 미실행 11

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 17 | `applyDisabilityCertification` | GET | `/classes/com.korail.mobile.certification.ReservationList` | 장애 할인 적용 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, hidPnrNo, txtPsgDisc0019Cnt, QueryMap, QueryMap, QueryMap, QueryMap, QueryMap, QueryMap | `BaseResponse` |
| 18 | `certCongressperson` | GET | `/classes/com.korail.mobile.certification.assemblyCert` | 국회의원 인증 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, freeDiscCertNo, certNo, abrdDt | `CongresspersonCertDao.CongresspersonCertResponse` |
| 19 | `certMerit` | POST | `/classes/com.korail.mobile.certification.MeritCert` | 유공자 인증 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtFreeDiscCertNo, txtAcptPwd, txtJuminNo7, txtAbrdDt | `MeritCertDao.MeritCertResponse` |
| 20 | `disabledCertification` | GET | `/classes/com.korail.mobile.certification.disabled.do` | 장애 인증 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, regNum, hdcpGrade | `DisabledCertificationDao.DisabledCertificationResponse` |
| 21 | `getDiscountPrice` | POST | `/classes/com.korail.mobile.certification.PriceReCalculation` | 할인 적용 후 운임 재계산 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, hidPnrNo, txtJobId, hiduserYn, hidCustNo, txtPsgGridcnt, psg_tp_dv_cd, hidDcntKndCd, dcnt_knd_cd1, hidDscpNo, psrm_cl_cd, hidFmlyNo | `ReservationResponse` |
| 22 | `govermentCertification1` | GET | `/classes/com.korail.mobile.pbep.toknCre.do` | 정부 인증 토큰 생성 | 미실행 | 운영 상태 변경 가능 | Device, Version | `GovernmentCertificationStep1Dao.GovernmentCertificationResponse` |
| 23 | `govermentCertification2` | GET | `/classes/com.korail.mobile.pbep.sttChck.do` | 정부 인증 상태 확인 | 미실행 | 운영 상태 변경 가능 | Device, Version, csrfToken | `GovernmentCertificationStep2Dao.GovernmentCertificationStep2Response` |
| 24 | `inquiryTicketRsv` | GET | `/classes/com.korail.mobile.certification.ReservationList` | 예약 상세/인증 목록 조회 | 실패 | 읽기 전용. 라이브 호출 수락됨, 예약 0건 계정이라 `WRG200018` 입력값오류(PNR번호). 2026-07-25 실제 예약 보유 상태에서 성공 응답을 받았으나 파서가 거부함: 좌석 행의 `h_srcar_no`가 APK DAO 선언(`String`)과 달리 JSON 숫자로 옴. 파서를 문자열/숫자 모두 허용하도록 수정. 성공 응답 전체 필드는 여전히 미기록 | Device, Version, Key, hidPnrNo | `ReservationResponse` |
| 25 | `reservation` | POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | 승차권 예약 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo, txtMenuId, txtJobId, txtGdNo, hidFreeFlg, txtStndFlg, txtCustNm, txtCpNo, txtCustPw, FieldMap, FieldMap, FieldMap, FieldMap | `ReservationResponse` |
| 26 | `reservation` | POST | `/classes/com.korail.mobile.certification.TicketReservation` | 승차권 예약 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo, txtMenuId, txtJobId, txtGdNo, hidFreeFlg, txtStndFlg, pbepInfo, FieldMap, FieldMap, FieldMap, FieldMap | `ReservationResponse` |
| 27 | `reservation` | POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | 승차권 예약 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtCustNm, txtCpNo, txtCustPw, FieldMap | `ReservationResponse` |
| 28 | `reservation` | POST | `/classes/com.korail.mobile.certification.TicketReservation` | 승차권 예약 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, FieldMap | `ReservationResponse` |

## CommonService

- 역할: 공통코드, 약관, 앱 설정, QR 위치 인증
- 상태: 총 11개 / 성공 6 / 실패 0 / 미실행 5

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 29 | `authQRLocation` | POST | `/classes/com.korail.mobile.qr.bchTripSv.do` | QR 위치 인증 | 미실행 | 운영 상태 변경 가능 | Device, Version, qrcode, latitude, longitude | `authQRLocationDao.QRLocationResponse` |
| 30 | `ckValue` | GET | `/ebizcross/getUUID.do` | UUID/cookie 값 조회 | 성공 |  |  | `CookieDao.RsvWaitResponse` |
| 31 | `getCommonCode` | POST | `/classes/com.korail.mobile.common.code.do` | 공통코드 조회 | 성공 | API.I00000 Success | Device, Version, Key, code, deviceWidth, deviceHeight, departDate, arrivalDate, holidayYn, OSVersion | `CommonCodeDao.CommonCodeResponse` |
| 32 | `getDecrypt` | POST | `/classes/com.korail.mobile.common.decrypt.do` | 공통 복호화 | 미실행 | 미검증 | Device, Version, Key, type, values | `DecryptDao.DecryptResponse` |
| 33 | `getEncrypt` | POST | `/classes/com.korail.mobile.common.encrypt.do` | 공통 암호화 | 미실행 | 미검증 | Device, Version, Key, type, values | `EncryptDao.EncryptResponse` |
| 34 | `getKBPayEncrypt` | POST | `/classes/com.korail.mobile.common.encrypt.do` | KBPay 암호화 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, type, values | `KBPayEncryptDao.KBpayEncryptResponse` |
| 35 | `getMaasMenuList` | POST | `/classes/com.korail.mobile.copt.gdMenuLt.do` | MAAS 메뉴 조회 | 성공 | 일반 메뉴 조회 HTTP 200, 엄격 envelope, 메뉴 11개 | Device, Version, pnrNo, tkRetNo, addSrvReqNo | `MaasMenuListDao.MaasMenuListResponse` |
| 36 | `getMaasStationList` | POST | `/ebizmaas/EbizMaasStationList.do` | MAAS 역 목록 조회 | 성공 | 메뉴 응답의 동적 addSrvDvCd로 HTTP 200, 역 101개 | addSrvDvCd | `StationDataDao.StationDataResponse` |
| 37 | `getStationData` | GET | `/classes/com.korail.mobile.common.stationdata` | 역 데이터 조회 | 성공 | HTTP 200(비JSON/캐시성 응답 포함) |  | `StationDataDao.StationDataResponse` |
| 38 | `getStationInfo` | GET | `/classes/com.korail.mobile.common.stationinfo` | 역 정보 조회 | 성공 | HTTP 200(비JSON/캐시성 응답 포함) | Device | `StationInfoDao.StationInfoResponse` |
| 39 | `seedEncrypt` | POST | `/classes/com.korail.mobile.shinhan.Encrypt.do` | 신한/SEED 암호화 | 미실행 | 미검증 | Device, Version, Key, value | `SeedEncryptDao.SeedEncryptResponse` |

## CompensateService

- 역할: 보상 환불 대상 조회 및 실행
- 상태: 총 3개 / 성공 0 / 실패 1 / 미실행 2

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 40 | `executeCompensateRefund` | POST | `/classes/com.korail.mobile.compensate.ticketReturn.do` | 보상 환불 실행 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, tkCnt, trnStpRsStnCd, jrnyStpTkFlg, ogTkSaleWctNo, ogTkSaleDd, ogTkSaleSqNo, ogTkRetPwd | `BaseResponse` |
| 41 | `executeCompensateRefundDetail` | POST | `/classes/com.korail.mobile.compensate.ticketDetail.do` | 보상 환불 상세 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, tkCnt, trnStpRsStnCd, jrnyStpTkFlg, ogTkSaleWctNo, ogTkSaleDd, ogTkSaleSqNo, ogTkRetPwd | `BaseResponse` |
| 42 | `executeCompensateRefundList` | POST | `/classes/com.korail.mobile.compensate.ticketList.do` | 보상 환불 목록 조회 | 실패 | WRG000000 조회 결과가 없습니다. | Device, Version, Key, nowPgNo, dptDtFrom, dptDtTo | `CompensateRefundListDao.CompensateRefundListResponse` |

## CustService

- 역할: 고객 할인 대상 조회
- 상태: 총 1개 / 성공 0 / 실패 1 / 미실행 0

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 43 | `mchdDcntTgt` | POST | `/classes/com.korail.mobile.cust.mchdDcntTgt.do` | 고객 할인 대상 조회 | 실패 | `WRC800029`; `KorailAppError`, 1회 호출, 재시도 없음 | Device, Version, Key, dptDt | `MchdDcntTgtDao.MchdDcntTgtResponse` |

## DelayService

- 역할: 지연증명, 지연료, 지연환불 조회/신청
- 상태: 총 9개 / 성공 1 / 실패 1 / 미실행 7

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 44 | `athnIsu` | POST | `/classes/com.korail.mobile.dlay.athnIsu.do` | 지연증명 발급 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, ogtkSaleWctNo, ogtkSaleDd, ogtkSaleSqno, ogtkRetPwd, runDt, trnNo | `DelayCertificateDao.DelayCertificateResponse` |
| 45 | `cashRfn` | POST | `/classes/com.korail.mobile.dlay.cashRfn.do` | 지연 현금 환불 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, dmnPrsDvCd, saleWctNo, saleDd, saleSqno, tkRetPwd, dptnBankCd, dptnAcntNo, custNm, custTeln, rmk1Cont | `CashRfnDao.CashRfnResponse` |
| 46 | `dealyReturnReceipt` | POST | `/classes/com.korail.mobile.dlay.pymtRcet.do` | 지연 반환 영수증 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, saleWctNo, saleDd, saleSqno, tkRetPwd | `DelayReturnReceiptDao.DelayReturnReceiptResponse` |
| 47 | `dptnBank` | POST | `/classes/com.korail.mobile.dlay.dptnBank.do` | 입금은행 목록 조회 | 성공 | API.I00000 Success | Device, Version, Key | `DptnBankDao.DptnBankResponse` |
| 48 | `executeDelayPNRAccept` | POST | `/classes/com.korail.mobile.delay.acptPrs.do` | 지연 PNR 접수 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, jobDvCd, pnrCnt, pnrNo, ogtkWctNo | `BaseResponse` |
| 49 | `executeDelayPNRQuery` | POST | `/classes/com.korail.mobile.delay.pnrQry.do` | 지연 PNR 조회 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, jobDvCd, pnrCnt, pnrNo, ogtkWctNo | `DelayPNRQueryDao.DelayPNRQueryResponse` |
| 50 | `executeDelayRefund` | POST | `/classes/com.korail.mobile.delay.ticketReturn.do` | 지연 환불 실행 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, dlayFarePymtMtdCd, tkCnt, ogTkSaleWctNo, ogTkSaleDd, ogTkSaleSqNo, ogTkRetPwd | `BaseResponse` |
| 51 | `executeDelayRefundDetail` | POST | `/classes/com.korail.mobile.delay.ticketDetail.do` | 지연 환불 상세 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, tkCnt, ogTkSaleWctNo, ogTkSaleDd, ogTkSaleSqNo, ogTkRetPwd | `BaseResponse` |
| 52 | `executeDelayRefundList` | POST | `/classes/com.korail.mobile.delay.ticketList.do` | 지연 환불 목록 조회 | 실패 | WRG000000 조회 결과가 없습니다. | Device, Version, Key, nowPgNo, dptDtFrom, dptDtTo | `DelayRefundListDao.DelayRefundListResponse` |

## GiftInfoService

- 역할: 승차권 선물
- 상태: 총 1개 / 성공 0 / 실패 0 / 미실행 1

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 53 | `presentTicket` | POST | `/classes/com.korail.mobile.giftInfo.GiftSend` | 승차권 선물 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, hidAcepPsNm, hidAcepPsTeln, hidPbpAcepPsMbFlg, hidPbpAcepPsCustMgNo, hidPnrNo, hidTotNewStlAmt, hidRsvChgNo, hidInfoInpDvCd, hidSaleCnt, hidAcepPwd, FieldMap | `TicketPresentDao.TicketPresentResponse` |

## GifticketService

- 역할: 기프티켓 조회/예약/이력
- 상태: 총 4개 / 성공 0 / 실패 2 / 미실행 2

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 54 | `bookingGifticket` | POST | `/classes/com.korail.mobile.gift.gdRsv.do` | 기프티켓 예약 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, itmCnt, mrkAmt_1, prnbCnt, mbCrdNo_1, gdUtlPsNm_1 | `GifticketBookingDao.GifticketBookingResponse` |
| 55 | `getGifticketList` | POST | `/classes/com.korail.mobile.gift.gdLst.do` | 기프티켓 목록 조회 | 실패 | HTTP 404(현재 host/version 경로 미노출 가능) | Device, Version, Key, qryDvCd, qryVal, abrdDtFrom, abrdDtTo, usePsbFlg, qryNumNext, fllwQryFlg, trnOprBzDvCd | `GifticketListDao.GifticketListResponse` |
| 56 | `historyGifticket` | POST | `/classes/com.korail.mobile.gift.gdUseSpec.do` | 기프티켓 사용이력 | 실패 | HTTP 404(현재 host/version 경로 미노출 가능) | Device, Version, Key, tkId | `GifticketHistoryDao.GifticketHistoryResponse` |
| 57 | `returnGifticket` | POST | `/classes/com.korail.mobile.gift.gdRet.do` | 기프티켓 반환 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, tkId | `GifticketReturnDao.GifticketReturnResponse` |

## IndependentService

- 역할: 사용자 부가정보 등록
- 상태: 총 1개 / 성공 0 / 실패 0 / 미실행 1

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 58 | `registerUserInfo` | POST | `/classes/com.korail.mobile.login.poppCfmRec.do` | 사용자 정보 등록 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, FieldMap | `BaseResponse` |

## LoginService

- 역할: 로그인, 로그아웃, 회원번호/비밀번호 확인
- 상태: 총 7개 / 성공 1 / 실패 0 / 미실행 6

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 59 | `certMember` | POST | `/classes/com.korail.mobile.login.userCheck` | 회원 인증/회원번호 확인 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtAcptPsNm, acept, txtCpNo, memNum, txtEmailNo | `MemberCertDao.MemberCertResponse` |
| 60 | `login` | POST | `/classes/com.korail.mobile.login.Login` | 로그인 | 성공 | IRZ000001 정상적으로 조회 되었습니다. | Device, Version, Key, txtMemberNo, txtPwd, txtInputFlg, checkValidPw, custId, etrPath, idx | `LoginDao.LoginResponse` |
| 61 | `loginAthnReg` | POST | `/classes/com.korail.mobile.login.loginAthnReg.do` | 간편로그인 등록 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, lognTpCd, custId | `BaseResponse` |
| 62 | `loginAthnRmv` | POST | `/classes/com.korail.mobile.login.loginAthnRmv.do` | 간편로그인 해제 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, srvQryDvVal, lognTpCd | `BaseResponse` |
| 63 | `logout` | GET | `/classes/com.korail.mobile.login.Logout` | 로그아웃 | 미실행 | 미검증 |  | `BaseResponse` |
| 64 | `memberCheck` | POST | `/classes/com.korail.mobile.login.joinCfm.do` | 회원 가입 확인 | 미실행 | 미검증 | Device, Version, hmpgPwd, custNm | `BaseResponse` |
| 65 | `memberDrop` | POST | `/classes/com.korail.mobile.login.mbSced.do` | 회원 탈퇴 | 미실행 | 운영 상태 변경 가능 | Device, Version | `BaseResponse` |

## MileageService

- 역할: 마일리지 적립/알림
- 상태: 총 3개 / 성공 0 / 실패 0 / 미실행 3

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 66 | `acpnMlgNoti` | POST | `/classes/com.korail.mobile.mileage.acpnMlgNoti.do` | 동반 마일리지 알림 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, saleWctNo, saleDt, saleSqno, retPwd, rcvPsHndyTeln | `BaseResponse` |
| 67 | `acpnMlgSave` | POST | `/classes/com.korail.mobile.mileage.acpnMlgSave.do` | 동반 마일리지 적립 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, rsvMbCrdNo, custNm, mlgAcmMbCrdNo, saleWctNo, saleDd, saleSqno, tkRetPwd | `BaseResponse` |
| 68 | `acpnMlgSpec` | POST | `/classes/com.korail.mobile.mileage.acpnMlgSpec.do` | 동반 마일리지 내역 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, pnrNo | `AcpnMlgSpecDao.AcpnMlgSpecResponse` |

## MyTicketService

- 역할: 내 승차권 및 구매이력 조회
- 상태: 총 3개 / 성공 1 / 실패 0 / 미실행 2

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 69 | `getTicketList` | POST | `/classes/com.korail.mobile.myTicket.MyTicketList` | 내 승차권/구매이력 조회 | 성공 | WRT300005 조회자료가 없습니다. | Device, Version, Key, txtDeviceId, txtIndex, h_page_no, h_abrd_dt_from, h_abrd_dt_to, hiduserYn, hidName, hidTeleNo, hidPwd, tsRsStnCd | `TicketListDao.TicketListResponse` |
| 70 | `procUpgrade` | GET | `/classes/com.korail.mobile.myTicket.procUpgradeSeat` | 좌석 업그레이드 결제/처리 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, totTxnAmt, totCncRetAmt, totCncRetFee, feeProyStlSqno, lumpStlTgtNo, mnsGridcnt, stlMnsSqno, stlMnsCd, mnsStlAmt, crdInpWayCd, ismtMnthNum, pontDvCd, pontInpDvCd, prepCrdTxnBfAmt, prepCrdTxnAftAmt | `BaseResponse` |
| 71 | `requestUpgradeSeat` | GET | `/classes/com.korail.mobile.myTicket.reqUpgradeSeat` | 특실 업그레이드 요청 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, ogtkSaleDd, ogtkSaleWctNo, ogtkSaleSqno, ogtkRetPwd, jrnyTpCd, jrnySqno, dptDt, dptStnConsOrdr, dptStnRunOrdr, dptRsStnCd, dptTm, arvDt, arvStnConsOrdr, arvStnRunOrdr, arvRsStnCd, arvTm, trnNo, runDt, trnGpCd, roomClsfCd, scarNo, seatNo, rqSeatAttCd | `SpecialRoomUpgradeDao.SpecialRoomUpgradeResponse` |

## NFilterService

- 역할: NFilter 보안 키 생성
- 상태: 총 1개 / 성공 0 / 실패 1 / 미실행 0

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 72 | `createKey` | POST | `/classes/com.korail.mobile.nFilter.createKey.do` | NFilter 공개키 생성 | 실패 | HTTP 404(현재 host/version 경로 미노출 가능) | Device, Version, Key | `NFilterCreateKeyDao.NFilterCreateKeyResponse` |

## PassCardService

- 역할: 패스카드/할인권 등록 및 조회
- 상태: 총 4개 / 성공 2 / 실패 0 / 미실행 2

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 81 | `addDelayTicket` | POST | `/classes/com.korail.mobile.passCard.DelayDiscountCheck` | 지연할인권 등록 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, h_dlay_disc_cnt, h_orgtk_ret_sale_dt, h_orgtk_wct_no, h_orgtk_sale_sqno, h_orgtk_ret_pwd | `BaseResponse` |
| 82 | `certDCCoupon` | POST | `/classes/com.korail.mobile.passCard.DiscountCheck` | 할인쿠폰 인증 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtCertNo, txtCertPwd | `BaseResponse` |
| 83 | `getDelayTicketList` | POST | `/classes/com.korail.mobile.passCard.DelayDiscountView` | 지연할인권 목록 | 성공 |  | Device, Version, Key, dptDtTo | `DelayTicketListDao.DelayTicketListResponse` |
| 84 | `getDiscountCoupon` | POST | `/classes/com.korail.mobile.passCard.CouponView` | 할인쿠폰 목록 | 성공 | WRG000000 조회 결과가 없습니다. | Device, Version, Key, txtSelPage, pnrNo | `DCCouponListDao.DCCouponListResponse` |

## PassService

- 역할: 정기권/패스권 조회, 예약, 결제, 반환
- 상태: 총 8개 / 성공 2 / 실패 1 / 미실행 5

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 73 | `commPayment` | POST | `/classes/com.korail.mobile.pass.passPayIssue` | 정기권 결제 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, hidPayAmount, FieldMap, FieldMap | `CommPaymentDao.CommPaymentResponse` |
| 74 | `commReservation` | POST | `/classes/com.korail.mobile.pass.passReserve` | 정기권 예약 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, hidCmtrKndCd, hidCmtrUtlTrmCd, hidCmtrUtlTrmNm, hidCmtrUtlAgeCd, hidUseOpenDt, hidAppDptStnCd, hidAppDptStnNm, hidAppArvStnCd, hidAppArvStnNm, hidChtrnStnCd, hidChtrnStnNm, hidTrnNo1, hidTrnNo2, hidTrnGpCd1, hidTrnGpCd2, hidDtour1, hidDtour2 | `CommReservationDao.CommReservationResponse` |
| 75 | `getCommRsvInquiry` | POST | `/classes/com.korail.mobile.pass.passScheduleInfoList` | 정기권 스케줄 조회 | 미실행 | 미검증 | Device, Version, Key, selGoTrain, selGoAbrdDt, txtGoHour, radChgTrnDvCd, txtCmtrKndCd, txtCmtrUtlTrmCd, txtCmtrUtlAgeCd, txtSelPage, txtCntPerPage, txtGoStart, txtGoEnd, txtWkndUseFlg | `CommRsvInquiryDao.CommRsvInquiryResponse` |
| 76 | `getEnableDate` | POST | `/classes/com.korail.mobile.pass.passInfoList` | 패스 사용 가능일 조회 | 성공 |  | Device, Version, Key, txtCmtrKndCd, txtCmtrUtlTrmCd, txtCmtrUtlAgeCd | `EnableDateDao.EnableDateResponse` |
| 77 | `passMenu` | POST | `/classes/com.korail.mobile.pass.passMenu.do` | 패스 메뉴 조회 | 실패 | menuNo Error menuNo Error | Device, Version, Key, menuNo | `DiscountMenuDao.DiscountMenuResponse` |
| 78 | `passPayment` | POST | `/classes/com.korail.mobile.pass.passOtrPayIssue` | 패스 결제 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, hidPayAmount, h_rcvd_prc, hidWctNo, FieldMap, FieldMap | `PassPaymentDao.PassPaymentResponse` |
| 79 | `passReservation` | POST | `/classes/com.korail.mobile.pass.passOtrReserve` | 패스 예약 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, hidCmtrKndCd, hidCmtrUtlTrmCd, hidCmtrUtlAgeCd, hidUseOpenDt | `PassReservationDao.PassReservationResponse` |
| 80 | `tripMenu` | POST | `/classes/com.korail.mobile.pass.trGdMenuLt.do` | 여행/패스 메뉴 조회 | 성공 | API.I00000 Success | Device, Version | `TripMenuDao.TripMenuResponse` |

## PayService

- 역할: 간편결제/Payco/포인트/결제수단
- 상태: 총 12개 / 성공 0 / 실패 0 / 미실행 12

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 85 | `getPaycoResult` | POST | `/classes/com.korail.mobile.payment.reserve.payco.do` | Payco 결제 준비 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, ticketPrice, ticketName | `PaycoDao.PaycoPaymentResponse` |
| 86 | `getSpayCphdDatVal` | POST | `/classes/com.korail.mobile.pay.spayCphdDatVal.do` | 간편결제 데이터 검증 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, spayDvCd, data | `SpayCphdDatValDao.SpayCphdDatValResponse` |
| 87 | `getSpayCphdDatValMonimo` | POST | `/classes/com.korail.mobile.pay.monimoDecrypt.do` | Monimo 결제 데이터 복호화 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, otcNo | `SpayCphdDatValMonimoDao.SpayCphdDatValMonimoResponse` |
| 88 | `getSpayOdrNo` | POST | `/classes/com.korail.mobile.pay.spayOrdNo.do` | 간편결제 주문번호 발급 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, spayDvCd, totTxnAmt, tgtCnt, encTotTxnAmt, idx, lumpStlTgtNo | `SpayOdrNoDao.SpayOdrNoResponse` |
| 89 | `intgStl` | POST | `/classes/com.korail.mobile.pay.intgStl.do` | 통합결제 처리 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, ctlDvCd, stlPrsJobId, cart_LumpStlTgtNo, FieldMap | `BaseResponse` |
| 90 | `naverPayMoneyRsv` | POST | `/classes/com.korail.mobile.pay.naverPayMoneyRsv.do` | 네이버페이 머니 예약 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, productCount, productAmount | `NaverPayRsvDao.NaverPayRsvResponse` |
| 91 | `naverPayRsv` | POST | `/classes/com.korail.mobile.pay.naverPayRsv.do` | 네이버페이 예약 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, productCount, productAmount | `NaverPayRsvDao.NaverPayRsvResponse` |
| 92 | `stbkAcnt` | POST | `/classes/com.korail.mobile.pay.stbkAcnt.do` | 계좌 결제/인증 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, stlBankCd, jobDvCd, acntNo, custCpNo, stbkTxnNo, stlApvPwd | `StbkAcntDao.StbkAcntResponse` |
| 93 | `stbkRegBank` | POST | `/classes/com.korail.mobile.pay.stbkRegBank.do` | 계좌 등록 은행 조회 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key | `StbkRegBankDao.StbkRegBankResponse` |
| 94 | `stlKeyPrs` | POST | `/classes/com.korail.mobile.pay.stlKeyPrs.do` | 결제키 등록/처리 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, jobDvCd, spayDvCd, spayStlKeyVal, stlBankCd, acntNo, binNo | `BaseResponse` |
| 95 | `stlKeyQry` | POST | `/classes/com.korail.mobile.pay.stlKeyQry.do` | 결제키 조회 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, spayDvCd | `TossAutoStlKeyQryDao.StlKeyQryResponse` |
| 96 | `tossautoC` | POST | `/classes/com.korail.mobile.pay.tossautoC.do` | Toss 자동결제 생성 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key | `TossAutoCreateDao.TossAutoCResponse` |

## PaymentService

- 역할: 예약 결제 실행
- 상태: 총 1개 / 성공 0 / 실패 0 / 미실행 1

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 97 | `payment` | POST | `/classes/com.korail.mobile.payment.ReservationPayment` | 예약 결제 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, hidPnrNo, hidWctNo, hidTmpJobSqno1, hidTmpJobSqno2, hidRsvChgNo, FieldMap | `RsvPaymentDao.RsvPaymentResponse` |

## ProductService

- 역할: 관광/여행상품 조회
- 상태: 총 4개 / 성공 2 / 실패 0 / 미실행 2

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 98 | `getProductDetail` | GET | `/classes/com.korail.mobile.product.ReservationDetail` | 여행상품 상세 | 성공 |  | Device, Version, Key, txtVrRsNo, txtVrRsvSqNo | `ProductDetailDao.ProductDetailResponse` |
| 99 | `getProductList` | GET | `/classes/com.korail.mobile.product.ReservationList` | 여행상품 예약 목록 | 성공 |  | Device, Version, Key, txtSelPage, txtCntPerPage | `ProductListDao.ProductListResponse` |
| 100 | `paymentCheck` | GET | `/classes/com.korail.mobile.product.payInfo` | 여행상품 결제 확인 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, txtVrRsNo, txtRsvGdSqno | `ProductPaymentCheckDao.ProductPaymentCheckResponse` |
| 101 | `productCancel` | GET | `/classes/com.korail.mobile.product.ReservationCancel` | 여행상품 취소 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtVrRsNo, txtGdSqno | `BaseResponse` |

## PushService

- 역할: 푸시 설정 및 승무원 호출
- 상태: 총 4개 / 성공 0 / 실패 0 / 미실행 4

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 102 | `callCrew` | GET | `/classes/com.korail.mobile.push.callCrew.do` | 승무원 호출 | 미실행 | 미검증 | Device, Version, Key, pnrNo, jrnySqno, saleWctNo, saleDt, saleSqno, tkRetPwd, sndSqno, coutMsgDvCd, intgMsgCd1, intgMsgCd2, intgMsgCd3, intgMsgCd4, intgMsgCd5, intgMsgCd6, intgMsgCd7, intgMsgCd8, intgMsgCd9, intgMsgCd10, intgMsgCont | `BaseResponse` |
| 103 | `callCrewRequestList` | GET | `/classes/com.korail.mobile.push.crwCallRq.do` | 승무원 호출 목록 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, qryDvCd | `CallCrewRequestListDao.CallCrewListResponse` |
| 104 | `cmtrKndPassMenu` | GET | `/classes/com.korail.mobile.push.cmtrKnd.do` | 정기권 종류 메뉴 | 미실행 | 미검증 | Device, Version, Key, cmtrKndCd | `CmtrKndMenuDao.CmtrKndMenuResponse` |
| 105 | `pushUpdate` | GET | `/classes/com.korail.mobile.push.update` | 푸시 설정 갱신 | 미실행 | 운영 상태 변경 가능 | Device, Version, job_dv_cd, tnsm_flg1, tnsm_flg2, tnsm_flg3, tnsm_flg4, dptUsrInpTnum, arvUsrInpTnum | `PushUpdateDao.PushUpdateResponse` |

## RailPlusService

- 역할: RailPlus 자동충전 조회
- 상태: 총 1개 / 성공 0 / 실패 0 / 미실행 1

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 106 | `getAutoCharge` | GET | `/classes/com.korail.mobile.railplus.autoCharge.do` | RailPlus 자동충전 조회 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, jobDvCd, prepCrdNo | `AutoChargeDao.AutoChargeResponse` |

## ReceiptService

- 역할: 승차권 영수증 조회
- 상태: 총 1개 / 성공 1 / 실패 0 / 미실행 0

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 107 | `getTicketReceipt` | POST | `/classes/com.korail.mobile.receipt.ReceiptInfo` | 승차권 영수증 조회 | 성공 | 영수증 5건 조회 성공(IRT000000) | Device, Version, Key, h_orgtk_sale_dt, h_orgtk_wct_no, h_orgtk_sale_sqno, h_orgtk_tk_ret_pwd | `ReceiptDao.ReceiptResponse` |

## RefundService

- 역할: 승차권 환불/반환 실행
- 상태: 총 5개 / 성공 0 / 실패 2 / 미실행 3

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 108 | `executeOnlineRefunds` | POST | `/classes/com.korail.mobile.refunds.executeOnlineRefunds` | 온라인 환불 실행 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo, tkKndCd, retDvCd, retRsnCd, ogtkSaleDt, ogtkSaleWctNo, ogtkSaleSqno, ogtkRetPwd, retAmt, retFee, custTeln, acepCustNm | `RefundExecuteTicketRefundDao.RefundExecuteTicketRefundResponse` |
| 109 | `getTicketCommission` | POST | `/classes/com.korail.mobile.refunds.CommissionView` | 환불 수수료 조회 | 실패 | 읽기 전용 사전조회. 라이브 호출 수락됨, 실티켓 없어 `WRT100124`. 성공 응답 미검증 | Device, Version, Key, h_orgtk_ret_sale_dt, h_orgtk_wct_no, h_orgtk_sale_sqno, h_orgtk_ret_pwd, h_comp_nm, h_comp_cert_no | `RefundCommissionDao.RefundCommissionResponse` |
| 110 | `getTicketDetail` | POST | `/classes/com.korail.mobile.refunds.SelTicketInfo` | 환불용 티켓 상세 | 실패 | 읽기 전용. 라이브 호출 수락됨, 실티켓 없어 `WRT100002`. 성공 응답 미검증 | Device, Version, Key, h_orgtk_ret_sale_dt, h_orgtk_wct_no, h_orgtk_sale_sqno, h_orgtk_ret_pwd, h_purchase_history | `TicketDetailDao.TicketDetailResponse` |
| 111 | `returnTicket` | POST | `/classes/com.korail.mobile.refunds.RefundsRequest` | 승차권 환불 요청 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtPnrNo, h_orgtk_sale_dt, h_orgtk_sale_wct_no, h_orgtk_sale_sqno, h_orgtk_ret_pwd, h_mlg_stl, tk_ret_tms_dv_cd, trnNo, pbpAcepTgtFlg, latitude, longitude | `RefundDao.RefundResponse` |
| 112 | `verifyOnlineRefunds` | POST | `/classes/com.korail.mobile.refunds.verifyOnlineRefunds` | 온라인 환불 검증 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, retNo1, retNo2, retNo3, retNo4, strName | `RefundVerifyTicketDao.RefundVerifyTicketResponse` |

## ResearchService

- 역할: 열차/좌석/N카드 관련 조회
- 상태: 총 11개 / 성공 3 / 실패 2 / 미실행 6

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 113 | `getAssignScheduleView` | POST | `/classes/com.korail.mobile.research.assignScheduleView.do` | 좌석배정 스케줄 조회 | 미실행 | static-only / 미실행 | Device, Version, Key, menuId, dptDt, dptTm, dptRsStnNm, arvRsStnNm, trnGpCd, psrmClCd, seatAttCd1, psgNum1, stlbDturDvNm1, dirtChtnDvCd, chtnArvRsStnNm | `SeatAssignScheduleViewDao.SeatAssignScheduleViewResponse` |
| 114 | `getCarList` | POST | `/classes/com.korail.mobile.research.TrainResearch` | 객차 목록 조회 | 성공 | IRG000000 / SUCC, 5개 객차 구조 검증 | Device, Version, Key, Sid, txtMenuId, txtPsrmClCd, txtRunDt, txtDptDt, txtTrnClsfCd, txtTrnNo, txtDptRsStnCd, txtArvRsStnCd, txtDptStnRunOrdr, txtArvStnRunOrdr, txtTrnGpCd, txtTotPsgCnt, txtSeatAttCd, txtGdNo, sidTest | `SearchCarListDao.SearchCarListResponse` |
| 115 | `getCmtrInfo` | POST | `/classes/com.korail.mobile.research.cmtrInfo.do` | 정기권 정보 조회 | 미실행 | 미검증 | Device, Version, Key, jobDvCd, cmtrKndCd, psgCnt, cmtrUtlAgeCd, psgPrnb, ogtkSaleWctNo, ogtkSaleDd, ogtkSaleSqno, ogtkRetPwd, inquiryType | `CmtrInfoDao.CmtrInfoResponse` |
| 116 | `getCustTripInfo` | POST | `/classes/com.korail.mobile.research.custTripInfo.do` | 고객 여행 편의설정 조회 | 성공 | 0 rows | Device, Version, Key, custMgNo, medDvCd, regSqno | `ConvenienceSettingDao.ConvenienceSettingResponse` |
| 117 | `getMergeSeatsInquiry` | POST | `/classes/com.korail.mobile.research.mergeSeatsC.do` | 병합좌석 조회 | 미실행 | static-only / 미실행 | Device, Version, Key, abrdDt, runDt, trnNo, dptRsStnNm, arvRsStnNm, selRsStnNm, psrmClCd, seatAttCd, totPsgNum | `MergeSeatInquiryDao.MergeSeatInquiryResponse` |
| 118 | `getNCardHistory` | GET | `/classes/com.korail.mobile.ticket.dcntCrdUseQry.do` | N카드 사용이력 | 실패 | WRR000100 입력값 오류(dcntCrdNo) | Device, Version, Key, dcntCrdNo | `NCardHistoryDao.NCardHistoryResponse` |
| 119 | `getNCardSchedultView` | GET | `/classes/com.korail.mobile.research.dcntCrdScheduleView.do` | N카드 스케줄 조회 | 실패 | WRR000100 입력값 오류(dcntCrdKndCd) | Device, Version, Key, dptDt, dptRsStnNm, arvRsStnNm, dptTm, trnGpCd, dirtChtnDvCd, dcntCrdKndCd, dcntCrdKndMgNo, useTrmDno, usePsbTno, qryPgNo | `NCardInquiryDao.NCardInquiryResponse` |
| 120 | `getSeatList` | POST | `/classes/com.korail.mobile.research.TResidualSeatsResearch.do` | 잔여좌석 조회 | 성공 | IRG000000 / SUCC, 75개 좌석 구조 검증 | Device, Version, Key, trnClsfCd, trnGpCd, runDt, trnNo, srcarNo, psrmClCd, dptRsStnCd, arvRsStnCd, seatAttCd, dptStnRunOrdr, arvStnRunOrdr, totPsgCnt, gdNo, isArrow, Sid, sidTest, ctlDvCd | `SearchSeatListDao.SearchSeatListResponse` |
| 121 | `getTicketOriginalInquiry` | POST | `/classes/com.korail.mobile.research.tripChgOgtk.do` | 변경 원권 조회 | 미실행 | 미검증 | Device, Version, Key, tkCnt, FieldMap | `OgTkInquiryDao.OgTkInquiryResponse` |
| 122 | `setNCardExtension` | GET | `/classes/com.korail.mobile.reservation.dcntCrdExtn.do` | N카드 연장 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, saleWctNo, saleDd, saleSqno, tkRetPwd | `BaseResponse` |
| 123 | `setNCardReservation` | POST | `/classes/com.korail.mobile.research.dcntCrdInfo.do` | N카드 예약 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, dcntCrdKndMgNo, custMgNo, vlidTrmStDt, usePsbTno, FieldMap, FieldMap | `NCardReservationDao.NCardReservationResponse` |

## ReservationCancelService

- 역할: 예약 취소
- 상태: 총 3개 / 성공 0 / 실패 0 / 미실행 3

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 128 | `reservationCancel` | POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancel` | 예약 취소 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtPnrNo, txtJrnySqno, txtJrnyCnt, hidRsvChgNo | `BaseResponse` |
| 129 | `reservationCancelCheck` | POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | 예약 취소 가능 확인 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtPnrNo, txtJrnySqno, txtJrnyCnt, hidRsvChgNo | `BaseResponse` |
| 130 | `reservationChange` | POST | `/classes/com.korail.mobile.reservation.reservationChange.do` | 예약 변경 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo, chgTno, totPrnb, stndFlg, evntWctFlg, wctHndgCncDvCd, lrgCrgFlg, psgCnt, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `ReservationChangeDao.ReservationChangeResponse` |

## ReservationService

- 역할: 승차권 예약 및 좌석 조건
- 상태: 총 4개 / 성공 1 / 실패 1 / 미실행 2

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 124 | `getGuideSeatCnd` | POST | `/classes/com.korail.mobile.reservation.guideSeatCnd.do` | 좌석 조건 안내 | 실패 | server-supplied `rqSeatAttCd`의 전체 `FAIL` 앱 envelope / `KorailAppError`, 재시도 없음 | Device, Version, Key, rqSeatAttCd | `BaseResponse` |
| 125 | `getRsvHistory` | GET | `/classes/com.korail.mobile.reservation.ReservationView` | 예약 내역 조회 | 성공 | P100 검색된 데이터가 없습니다. | Device, Version, Key | `TicketRsvHistoryDao.TicketRsvHistoryResponse` |
| 126 | `getTicketChangeReservation` | POST | `/classes/com.korail.mobile.reservation.tripChgPrsC.do` | 여정 변경 예약 | 미실행 | 미검증 | Device, Version, Key, trvlKndCd, totPrnb, isePrnb, stndSeatFlg, intgTktIseFlg, prcFareReCalcFlg, tmpJobSqno, alcSeatDmnPsDvCd, jrny2Cnt, psg2Cnt, ctlDvCd, frcSaleRsnCont, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `ReservationResponse` |
| 127 | `setSeatAssignReservation` | POST | `/classes/com.korail.mobile.reservation.seatAssign.do` | 좌석 지정 예약 | 미실행 | 미검증 | Device, Version, Key, menuId, custMgNo, totPrnb, stndFlg, rqScarNum, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `SeatAssignReservationDao.SeatAssignReservationResponse` |

## ReservationWaitService

- 역할: 예약대기 신청
- 상태: 총 1개 / 성공 0 / 실패 0 / 미실행 1

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 131 | `rsvWait` | POST | `/classes/com.korail.mobile.reservationWait.ReservationWait` | 예약대기 신청 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, txtPnrNo, txtPsrmClChgFlg, txtSmsSndFlg, txtCpNo | `BaseResponse` |

## SeatMovieService

- 역할: 열차 스케줄 및 예약 조회
- 상태: 총 3개 / 성공 1 / 실패 0 / 미실행 2

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 133 | `getRsvInquiry` | POST | `/classes/com.korail.mobile.seatMovie.ScheduleView` | 열차 스케줄 조회 | 성공 | IRG000000 정상처리, 기존 safe search 10 rows | Device, Version, Sid, txtMenuId, radJobId, selGoTrain, txtTrnGpCd, txtGoTrnNo, txtGoStart, txtGoEnd, txtGoAbrdDt, txtGoHour, txtPsgFlg_1, txtPsgFlg_2, txtPsgFlg_3, txtPsgFlg_4, txtPsgFlg_5, txtSeatAttCd_2, txtSeatAttCd_3, txtSeatAttCd_4, txtJobDv, etrPath, tkDptDt, tkDptTm, tkTrnNo, ebizCrossCheck, srtCheckYn, rtYn, adjStnScdlOfrFlg, mbCrdNo, tkPsrmClCd, tkRcvdAmt, qryDvCd, qryStNo, qryStTrnNo, qryStTrnNo2, pgPrCnt, chtnCnt, chtnRsStnCd1, trnGpCnt, trnGpCd1 | `RsvInquiryResponse` |
| 134 | `getRsvLimousineInquiry` | POST | `/classes/com.korail.mobile.seatMovie.LimousineScheduleView` | 리무진 연계 스케줄 조회 | 미실행 | 미검증 | Device, Version, Sid, txtMenuId, radJobId, txtJobDv, selGoTrain, txtTrnGpCd, txtGoTrnNo, txtGoStart, txtGoEnd, txtGoAbrdDt, txtGoHour, txtPsgFlg_1, txtPsgFlg_2, txtPsgFlg_3, txtPsgFlg_4, txtPsgFlg_5, txtSeatAttCd_2, txtSeatAttCd_3, txtSeatAttCd_4, ebizCrossCheck, srtCheckYn, rtYn | `RsvInquiryResponse` |
| 135 | `getRsvProductInquiry` | POST | `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` | 상품/특가 스케줄 조회 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, txtMenuId, radJobId, selGoTrain, txtTrnGpCd, txtGoStart, txtGoEnd, txtGoAbrdDt, txtGoHour, txtPsgFlg_1, txtPsgFlg_2, txtPsgFlg_3, txtPsgFlg_4, txtPsgFlg_5, txtSeatAttCd_2, txtSeatAttCd_3, txtSeatAttCd_4, txtGdNo, qryDvCd, qryStNo, qryStTrnNo, qryStTrnNo2, pgPrCnt, chtnCnt, chtnRsStnCd1, trnGpCnt, trnGpCd1 | `RsvInquiryResponse` |

## TicketService

- 역할: 발권, 승차권 관리, 체크인, 티켓 정보
- 상태: 총 19개 / 성공 3 / 실패 1 / 미실행 15

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 136 | `deviceReset` | POST | `/classes/com.korail.mobile.tk.dvcInfoInit.do` | 승차권 기기정보 초기화 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, teln, custNm, nonMbPwd, stlbTrnClsfCd, dptDttm, latitude, longitude, trnNo | `BaseResponse` |
| 137 | `dlvRcvCust` | POST | `/classes/com.korail.mobile.tk.dlvRcvCust.do` | 전달 수령자 조회 | 미실행 | static-only / live 미실행 | Device, Version, Key, saleWctNo, saleDt, saleSqno, tkRetPwd | `DlvRcvCustDao.DlvRcvCustwResponse` |
| 138 | `duplicationCheck` | POST | `/classes/com.korail.mobile.ticket.ticketDupCheck.do` | 승차권 중복 확인 | 미실행 | static-only / live 미실행 | Device, Version, Key, pnrNo | `TicketDuplicationCheckDao.DuplicationCheckResponse` |
| 139 | `getMaasCancel` | POST | `/classes//com.korail.mobile.addService.cancelPay.do` | MAAS 결제 취소 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, custMgNo, lumpStlTgtNo | `BaseResponse` |
| 140 | `getMaasServiceCancel` | POST | `/classes/com.korail.mobile.addService.coptCnc.do` | MAAS 서비스 취소 | 미실행 | 운영 상태 변경 가능 | Device, Version, pnrNo, cncTgtCnt, cncAddSrvReqNo, cncRetFee | `BaseResponse` |
| 141 | `getMaasServiceCancelFee` | POST | `/classes/com.korail.mobile.maas.cncFee.do` | MAAS 취소 수수료 조회 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, addSrvReqNo, addSrvDvCd, coptEntRsvNo | `MaasServiceCancelFeeDao.MaasServiceCancelFeeResponse` |
| 142 | `getMaasServiceDetailList` | POST | `/classes/com.korail.mobile.copt.gdReqQry.do` | MAAS 서비스 상세 목록 | 성공 | current form, 0 rows | Device, Version, qryDtFrom, qryDtTo | `MaasServiceDetailListDao.MaasServivceDetailResponse` |
| 143 | `getSelfSeatChgInfo` | POST | `/classes/com.korail.mobile.self.seatChgInfo.do` | 셀프 좌석변경 정보 | 실패 | `WRT800176` 좌석변경가능시간아님; `KorailAppError`, 2026-07-27, 1회 호출, 재시도 없음 | Device, Version, Key, runDt, trnNo, dptRsStnCd, arvRsStnCd, psrmClCd | `CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse` |
| 144 | `getTripChgDate` | POST | `/classes/com.korail.mobile.reservation.tripChgDate.do` | 여정변경 가능일 조회 | 성공 | 15 rows | Device, Version, Key, tripChgDate | `TripChgInfoDao.TripChgInfoDaoResponse` |
| 145 | `gurdSmsSnd` | POST | `/classes/com.korail.mobile.tk.gurdSmsSnd.do` | 보호자 안심 SMS 발송 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pnrNo, jrnySqno, rcvPsHndyTeln | `BaseResponse` |
| 146 | `pbpAcepSpec` | POST | `/classes/com.korail.mobile.tk.pbpAcepSpec.do` | PBP 수락 내역 | 미실행 | static-only / live 미실행 | Device, Version, Key, tkCnt, tkRetNo | `PbpAcepSpecDao.PbpAcepSpecResponse` |
| 147 | `pbpTkWdrw` | POST | `/classes/com.korail.mobile.tk.pbpWdrw.do` | PBP 승차권 회수 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, pbpCnt, pbpRsvNo, pnrNo | `BaseResponse` |
| 148 | `plfNo` | POST | `/classes/com.korail.mobile.tk.plfNo.do` | 플랫폼 번호 조회 | 미실행 | static-only / live 미실행 | Device, Version, Key, tkCnt, tkRetNo | `UpdatePlatformDao.PlfNoResponse` |
| 149 | `rcntDlvHst` | POST | `/classes/com.korail.mobile.tk.rcntDlvHst.do` | 최근 전달 이력 | 성공 | `1 row, 1회 호출, 재시도 없음` | Device, Version, Key, custMgNo | `RecentDeliveryHistoryDao.RcntDlvHstResponse` |
| 150 | `selfCheckinCancel` | POST | `/classes/com.korail.mobile.checkin.cnc.do` | 셀프체크인 취소 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, saleWctNo, saleDt, saleSqno, tkRetPwd, jrnySqno | `BaseResponse` |
| 151 | `selfCheckinInfo` | POST | `/classes/com.korail.mobile.checkin.info.do` | 셀프체크인 정보 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, saleWctNo, saleDt, saleSqno, tkRetPwd, jrnySqno | `SelfCheckinInfoDao.SelfCheckinInfoResponse` |
| 152 | `selfCheckinPossible` | POST | `/classes/com.korail.mobile.checkin.psbFlg.do` | 셀프체크인 가능 여부 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, qrcode, saleWctNo, saleDd, saleSqno, tkRetPwd, jrnySqno | `SelfCheckinPossibleDao.SelfCheckinPossibleResponse` |
| 153 | `selfCheckinRegister` | POST | `/classes/com.korail.mobile.checkin.reg.do` | 셀프체크인 등록 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, cpsNo, scarNo, seatNo, saleWctNo, saleDd, saleSqno, tkRetPwd, jrnySqno | `BaseResponse` |
| 154 | `ticketChangeCancel` | POST | `/classes/com.korail.mobile.ticket.tripChgHndgCnc.do` | 승차권 변경 취소 | 미실행 | 운영 상태 변경 가능 | Device, Version, Key, lumpStlCnt, FieldMap | `BaseResponse` |

## TrainsInfoService

- 역할: 열차/객차/자유석 정보 조회
- 상태: 총 6개 / 성공 3 / 실패 0 / 미실행 3

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 155 | `getFresScar` | POST | `/classes/com.korail.mobile.trn.fresScar.do` | 자유석/객차 조회 | 성공 | exact `strResult="SUCC"`, typed parse 성공 | Device, Version, Key, runDt, trnNo, dptStnConsOrdr, arvStnConsOrdr, dptStnRunOrdr, arvStnRunOrdr | `FresScarDao.FresScarResponse` |
| 156 | `getPrice2Fare` | POST | `/classes/com.korail.mobile.trn.prcFare.do` | 운임 재계산 | 미실행 | 미검증 | Device, Version, Key, txtMenuId, chtnDvCd, trnCnt, FieldMap | `Price2FareDao.Price2FareResponse` |
| 157 | `getPriceFare` | POST | `/classes/com.korail.mobile.trainsInfo.TrainCharge` | 운임 조회 | 미실행 | `skipped_no_typed_leg`; 0회 호출 | Device, Version, Key, txtMenuId, txtRtnDvCd, txtChtrDvCd1, txtSeatAttCd4, FieldMap | `PriceFareDao.PriceFareResponse` |
| 158 | `getSelectStationInfo` | POST | `/classes/com.korail.mobile.qry.chtnStn.do` | 선택역 정보 조회 | 성공 | IRZ000001 정상적으로 조회 되었습니다. | Device, Version, Key, dptRsStnCd, arvRsStnCd | `TrainSelectStationDao.TrainSelectStationResponse` |
| 159 | `getTourTrainInfo` | POST | `/classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom` | 관광열차 정보 | 미실행 | PNR/티켓/N카드/상품 등 실데이터 필요 | Device, Version, Key, txtTrnGpCd | `TourTrainInfoDao.TourTrainInfoResponse` |
| 160 | `getTrainSchedule` | POST | `/classes/com.korail.mobile.research.actualTrainSchedule.do` | 실제 열차 운행 스케줄 | 성공 | EVZ000048 열차가 존재하지 않습니다 | Device, Version, runDt, trnNo | `TrainScheduleDao.TrainScheduleResponse` |

## XPointService

- 역할: OK캐쉬백/X포인트 인증 및 적립
- 상태: 총 5개 / 성공 0 / 실패 0 / 미실행 5

| # | Java method | HTTP | Path | 역할 | 성공 여부 | 비고 | Params | Return type |
|---:|---|---|---|---|---|---|---|---|
| 161 | `certifyOKCashbag` | POST | `/classes/com.korail.mobile.xPoint.OkCashbagCertView` | OK캐쉬백 인증 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, cp_no | `BaseResponse` |
| 162 | `getKorailPoint` | POST | `/classes/com.korail.mobile.xPoint.MyXPointView` | 코레일 포인트 조회 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, point_dv_cd | `KorailPointInquiryDao.KorailPointInquiryResponse` |
| 163 | `getLPoint` | POST | `/classes/com.korail.mobile.mlg.lpotAthn.do` | L.Point 조회 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, pontPwd | `LPointDao.LPointInquiryResponse` |
| 164 | `getMileage` | POST | `/classes/com.korail.mobile.mlg.amtSpec.do` | 마일리지 조회 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, pontTpVal, qryDvVal, qryStDt, qryClsDt, pgPrCnt, nowPgNo | `MileageInquiryDao.MileageInquiryResponse` |
| 165 | `getPoint` | POST | `/classes/com.korail.mobile.xPoint.XPointView` | XPoint 조회 | 미실행 | 결제/간편결제/포인트/금전성 API | Device, Version, Key, inp_dv_cd, point_dv_cd, xpoint_no, xpoint_pwd, stl_crd_valid_trm | `PointInquiryDao.PointInquiryResponse` |
