# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·계정·상품 조회 응답 모델을 제공합니다. 열차·좌석 모델은 models, 전송 키 대응은 read_parsers를 따릅니다. 모든 하위 객체가 raw를 갖지는 않습니다. 내부 가변값과
개인정보·반환 비밀번호의 기록·노출에 관한 주의는 models 모듈을 따릅니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse, ReservationPassengerInfo


@dataclass(frozen=True)
class TicketListTrain:
    """승차권 한 장에 포함된 열차 구간 정보를 담습니다. 앱 근거: TicketListTrainInfo.java:72. 선택값으로 관대하게 읽습니다.

    2026-09-24 라이브 이력 139행: 21개 키가 모두 있었고 ``h_srcar_no`` 는 String 선언과 달리 모두 JSON 정수였습니다(문자열로 받습니다). DTO 밖의
    ``h_psrm_cl_cd``·``h_seat_no_end``·``h_sgr_nm_1``/``_2``·``srtStnFlg`` 도 왔으며 raw 에 남습니다."""

    journey_sequence: str | None = None
    run_date: str | None = None
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    car_no: str | None = None
    seat_no: str | None = None
    seat_count: str | None = None
    passenger_type_code: str | None = None
    received_amount: str | None = None
    buyer_name: str | None = None
    passenger_name: str | None = None
    train_suspension_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class TicketListTicket:
    """승차권 한 장의 식별자·상태와 열차 구간을 담습니다."""

    pnr_no: str | None = None
    sale_window_no: str | None = None
    sale_date: str | None = None
    return_sale_date: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    ticket_status_code: str | None = None
    #: ``h_tk_knd_cd``/``h_tk_knd_nm`` — 승차권 종류(``'72'``/``'스마트티켓'``). 예약 행이 아니라 승차권 행에서 읽습니다. 2026-09-22 한 계정
    #: 관측에서 131행 모두에 있었습니다. 다른 응답의 필드 존재까지 보장하지 않습니다. 관대하게 읽습니다.
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    train_info: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # h_tk_sqno 선언: MyTicketListOutTicket.java:92. 2026-09-22 표본 131행 모두에 있었습니다. 다른 조건에서도 필수인지는 검증 못 함입니다.
    ticket_sequence: str | None = None
    #: ticket_status_name은 h_tk_stt_nm을 읽으며 상태 코드를 임의의 이름으로 번역하지 않습니다.
    ticket_status_name: str | None = None
    #: 목록 행의 환불 플래그. 2026-09-22 기록: 이력 143장의 목록 값은 N, 같은 승차권의 상세 retPsbFlg 는 Y 였습니다. 둘을 같은 판정으로 취급하지 마십시오. 앱 버튼
    #: 조건은 상세 플래그와 사용 여부 검사입니다(NormalTicketSectionKt.java:951, TicketHelper.java:3173-3199). 비교 리터럴은 보호돼 있습니다.
    return_possible_flag: str | None = None
    use_transaction_no: str | None = None
    notify_use_transaction_no: str | None = None
    #: PBP 인수 대상. 앱은 목록 값을 상세에 주입합니다(MyTicketBaseViewModel.java:769, MyTicketDetailViewModel.java:1521).
    #: 2026-09-22 상세 40응답에는 두 후보 키가 없었습니다. 같은 날 목록 131행은 N 125/Y 6이었습니다. 다른 값의 의미는 검증 못 함입니다.
    pbp_acceptance_target_flag: str | None = None
    #: :attr:`train_info` 의 행을 :class:`TicketListTrain` 으로 읽은 것. 2026-09-24 이력에서 승차권 132장 중 7장이 두 구간이었습니다.
    trains: tuple[TicketListTrain, ...] = ()


@dataclass(frozen=True)
class TicketListReservation:
    """예약 하나에 속한 승차권 목록과 부가서비스를 담습니다. MyTicketListOutReservation 의 명시적 키는 ticket_list 이며 나머지는 보호된 serializer 대신
    속성명으로 읽는 추정입니다. 추가 서비스·종류도 raw 에 남습니다."""

    tickets: tuple[TicketListTicket, ...] = ()
    #: 선택 스칼라의 전송 키는 속성명에 따른 추정입니다. 2026-09-22 mode=2 의 예약 128행은 ticket_list 외 키가 없었습니다. 다른 응답의 필드 부재까지 보장하지
    #: 않습니다. 누락은 거짓이 아닌 모름(None)입니다. 종류 코드는 TicketListTicket.ticket_kind_code 를 보십시오.
    departure_datetime: str | None = None
    ticket_kind_code: str | None = None
    list_count: str | None = None
    seat_assign_count: int | None = None
    ticket_status: str | None = None
    is_finished: bool | None = None
    is_history: bool | None = None
    is_emergency: bool | None = None
    display_ticket_name: str | None = None
    is_non_member: bool | None = None
    is_transfer: bool | None = None
    is_wheelchair_member: bool | None = None
    is_rail_police_enabled: bool | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # 선택값의 타입이 어긋나면 해당 값만 비웁니다. addSrvInfo(MyTicketListOutReservation.java:39)는 MaaS 의 AddSrvItem 과 같은 타입이라 모델을
    # 공유합니다(MaasDetailOut.java:27, AddSrvItem.java:28-49). 키는 속성명에 따른 추정입니다.
    additional_service: MaasServiceDetail | None = None
    #: ticketKind 는 보호된 enum 이름을 매핑하지 않고 문자열로 둡니다 (MyTicketListOutReservation.java:52,59;
    #: TicketDefine.java:1078-1131). 앱 기본값은 GENERAL(MyTicketListOutReservation.java:133-134)이며, write$Self 는 기본값
    #: 기록 설정 또는 비기본값일 때 인코딩합니다(MyTicketListOutReservation.java:261). 따라서 기본값과 같다는 이유만으로 키가 반드시 생략된다고 할 수 없습니다.
    ticket_kind: str | None = None


@dataclass(frozen=True)
class TicketListResponse(BaseKorailResponse):
    """현재 승차권 또는 구매 이력을 예약별로 묶어 담습니다."""

    reservations: tuple[TicketListReservation, ...] = ()
    #: h_total_cnt는 구매이력(mode="2")의 총건수이며 영 채움을 보존합니다. 키가 없으면 None입니다.
    total_count: str | None = None


@dataclass(frozen=True)
class ServiceStatusResponse(BaseKorailResponse):
    """예매 서비스의 운영 상태 응답을 담습니다."""

    pass


@dataclass(frozen=True)
class CartItem:
    """장바구니의 열차·공항버스 예약 또는 부가서비스 한 행을 담습니다."""

    service_code: str | None = None
    provider_name: str | None = None
    product_name: str | None = None
    item_type: str | None = None
    departure_date: str | None = None
    received_amount: str | None = None
    reservation_received_date: str | None = None
    #: ``h_tk_cnt`` — ``CartInfo.java:51`` 의 선언은 ``String`` 이고 이 DTO 는 kotlinx 이므로 문자열로 둡니다.
    ticket_count: str | None = None
    usage_start_date: str | None = None
    usage_start_time: str | None = None
    usage_close_time: str | None = None
    partner_reservation_no: str | None = None
    pnr_no: str | None = None
    lump_sum_target_no: str | None = None
    customer_no: str | None = None
    virtual_reservation_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # CartInfo.java:28-61,281-392의 문자열은 읽고 중첩 결제 상세 6객체는 raw에 보존합니다. GreenCarPayDetail 12·LotteRentalPayDetail
    # 9·LoyquPayDetail 10·SKRentalCarPayDetail 13·YanoljaDetail 8· ZimCarryDetail 7로 String 59개이며 채워진 상세의 실서버
    # 형식은 미확인입니다. skRentalPayDetail의 타입은 SKRentalCarPayDetail입니다. h_item_dv_cd는 CartInfo.java:38,317에 선언되지만 앱
    # 분기값은 보호돼 있습니다(BasketTicketViewModel.java:4186,4295).
    item_type_code: str | None = None
    #: ``h_add_srv_mrk_ent_id`` — :attr:`provider_name`(``h_add_srv_mrk_ent_nm``, ``CartInfo.java:32``)의 ID
    #: 짝(``CartInfo.java:31``, ``@SerialName`` 289행).
    provider_id: str | None = None
    #: ``h_item_sqno``/``h_jrny_sqno``/``h_jrny_tp_cd`` — 이 행의 항목 일련번호, 여정 일련번호, 여정 구분
    #: 코드(``CartInfo.java:40,41,42``, ``@SerialName`` 325/329/333행). 뒤의 둘은 예약·영수증 쪽에서 쓰는 이름을 그대로 씁니다.
    item_sequence: str | None = None
    journey_sequence: str | None = None
    journey_type_code: str | None = None
    #: ``utlClsDt`` — :attr:`usage_close_time`(``utlClsTm``)의 날짜 짝 (``CartInfo.java:56``, ``@SerialName`` 377행).
    #: 앱도 둘을 이어 붙여 한 일시로 씁니다(``PayTicketContentKt.java:5234``: ``getUtlClsDt() + getUtlClsTm()``).
    usage_close_date: str | None = None
    #: h_stl_lmt_tm 은 자체로 기한을 나타내는 문자열(CartInfo.java:49,361). 앱은 MaaS 전용 분기에서 행을 고른 뒤 남은 시간을 계산합니다
    #: (PayViewModel.java:11658-11679, DateTimeExKt.java:407-431). 비교·파싱 패턴은 보호돼 있어 선택 방향과 정확한 날짜 형식은 미확인입니다.
    settlement_limit_time: str | None = None
    #: 아래 다섯은 ``CartInfo`` 가 선언만 하고(``CartInfo.java:48,50,36,47,35``, ``@SerialName`` 357/365/309/353/305행) 디컴파일
    #: 어디에서도 게터를 읽는 화면 코드를 찾지 못했습니다. 이름은 와이어 키를 그대로 옮긴 것이고 의미는 미확인입니다 — 값 해석은 호출자 몫입니다.
    settlement_extension_transaction_no: str | None = None
    settlement_means_allow_value: str | None = None
    field_settlement_division: str | None = None
    supervising_station_code: str | None = None
    filler: str | None = None

    @property
    def usage_window(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        return (
            self.usage_start_date,
            self.usage_start_time,
            self.usage_close_time,
        )


@dataclass(frozen=True)
class CartListResponse(BaseKorailResponse):
    """로그인 계정의 장바구니 목록을 담습니다."""

    items: tuple[CartItem, ...] = ()


@dataclass(frozen=True)
class DepositBank:
    """입금 가능한 은행의 코드와 이름을 담습니다."""

    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DepositBankListResponse(BaseKorailResponse):
    """입금 가능한 은행 목록을 담습니다."""

    items: tuple[DepositBank, ...] = ()


@dataclass(frozen=True)
class DelayDiscountTicket:
    """지연할인권 한 장의 식별자·사용 조건을 담습니다. 앱 근거: DelayCoupon.java:32-55.

    ``h_use_psb_dt``(사용 가능 기한)는 전 디컴파일에 0건이라 읽지 않습니다."""

    fare: str | None = None
    original_sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    ticket_sequence: str | None = None
    ticket_kind_code: str | None = None
    #: ``h_orgtk_sale_dt`` — 원표 자체의 발매일. ``original_sale_date`` (``h_orgtk_ret_sale_dt``, 반환일)와는 다른 필드입니다.
    original_ticket_sale_date: str | None = None
    #: ``h_rcvd_amt`` — ``fare``(``h_dlay_fare``)와 별개인 수령 금액.
    received_amount: str | None = None
    train_class_code: str | None = None
    room_class_code: str | None = None
    train_no: str | None = None
    departure_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_station_code: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    ticket_status_code: str | None = None
    ticket_status_name: str | None = None
    #: ``h_buy_ps_nm``/``h_abrd_ps_nm`` — 구매자·탑승자 성명. 둘 다 개인정보.
    buyer_name: str | None = None
    passenger_name: str | None = None
    page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DelayDiscountTicketListResponse(BaseKorailResponse):
    """지연할인권 목록과 페이지 정보를 담습니다. main_info는 DTO 밖 서버 추가 블록입니다(DelayDiscountViewOut.java:24,51). 2026-09-22 날짜 입력
    8종에서 12키를 확인했지만 할인권 없는 응답뿐이었습니다. 영 채움·빈 문자열을 보존하려고 페이지 값을 문자열로 두며, 채워진 응답의 의미는 검증하지 못했습니다."""

    items: tuple[DelayDiscountTicket, ...] = ()
    current_page: str | None = None
    total_pages: str | None = None
    total_count: str | None = None
    row_count: str | None = None
    last_page_flag: str | None = None


@dataclass(frozen=True)
class DiscountCoupon:
    """할인쿠폰 한 장의 조건과 유효기간을 담습니다."""

    guide: str | None = None
    start_date: str | None = None
    expiration_date: str | None = None
    discount_kind_code: str | None = None
    #: ``h_disc_rt_amt_dv_cd`` — 아래 네 할인값이 율인지 금액인지 나누는 코드입니다. 코드 값의 의미는 미확인입니다(CouponOutInfo.java:63).
    discount_rate_amount_division_code: str | None = None
    weekday_fare_discount: str | None = None
    weekday_price_discount: str | None = None
    weekend_fare_discount: str | None = None
    weekend_price_discount: str | None = None
    #: ``h_rmk_1_cont``~``h_rmk_3_cont`` 중 온 줄만 순서대로 담습니다.
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DiscountCouponListResponse(BaseKorailResponse):
    """할인쿠폰 목록과 안내를 담습니다."""

    items: tuple[DiscountCoupon, ...] = ()
    current_page: int | None = None
    total_pages: int | None = None
    total_count: str | None = None
    row_count: str | None = None


@dataclass(frozen=True)
class PassOffice:
    """패스 조회의 발권처 코드와 표시 이름을 담습니다."""

    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassOpenDate:
    """패스 사용 개시일과 발권 가능 날짜 정보를 담습니다. 앱 근거: PassInfo.java:92,96,100,149. open_dates 는 날짜만 모은 편의 목록입니다. 2026-09-22
    기록: 같은 입력 두 호출의 pnr_no 는 달랐고 E05/E06 변경 시 행은 같았습니다. 할당 원리·항상 변화 여부는 미확인입니다. 안정된 식별자로 보관하거나 open_dates 와
    재결합하지 마십시오."""

    open_date: str | None = None
    item_sequence: str | None = None
    pnr_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassAvailabilityMainInfo:
    """패스 사용일 조회의 중첩 상태와 건수를 담습니다. 앱 근거: MainInfo.java:103,107,111,115,172. 2026-09-22 관측 29종은 최상위 h_msg_cd 없이 이
    블록에 IRZ000001/IRZ000005 등을 담았습니다. 중첩 코드를 실패 예외로 승격하지 않습니다. 앱도 isSuccess 이후 pass_info 를 확인합니다
    (PeriodTicketViewModel.java:796-800, PassConditionViewModel.java:904-927). 다른 조건에서도 이것이 유일한 코드라고 보장하지는
    않습니다."""

    message_code: str | None = None
    total_count: str | None = None
    row_count: str | None = None
    selected_page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassAvailabilityResponse(BaseKorailResponse):
    """패스의 사용 개시일·발권 가능일·창구 목록을 담습니다."""

    #: open_dates는 pass_info의 날짜만 모으므로 날짜가 없는 행을 건너뜁니다. 전체 행은 pass_info를 사용하십시오.
    open_dates: tuple[str, ...] = ()
    ticket_issue_dates: tuple[str, ...] = ()
    offices: tuple[PassOffice, ...] = ()
    pass_info: tuple[PassOpenDate, ...] = ()
    main_info: PassAvailabilityMainInfo | None = None


@dataclass(frozen=True)
class TripMenuContent:
    """여행상품 메뉴의 안내 한 행과 패스 조건을 담습니다. 21개 문자열과 passData 객체입니다(TrGdMenuLtOutCont.java:26-47,72). 2026-09-22 2회
    60행은 detailType 누락 54/빈 값 6으로 유효한 값을 보지 못했습니다. passType 을 검증된 메뉴 종류 코드로 승격하지 마십시오. DTO 속성과 실제 소비 의미는
    별개입니다."""

    title: str | None = None
    detail: str | None = None
    detail_type: str | None = None
    active: str | None = None
    agree: str | None = None
    info: str | None = None
    image: str | None = None
    url: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    #: cmtrKndCd는 get_commuter_kind_menu의 입력입니다(TrGdMenuLtOutCont.java:26). 앱도 contList에서 이 코드로
    #: 찾습니다(PassConditionViewModel.java:1241). 2026-09-22: 60행 중 menuType='P'인 6행에만 0046·0007·0049 값이 있었습니다.
    commuter_kind_code: str | None = None
    #: ``passType``(``:47``) — 위 6행에서 ``'aPass'``. 7.0.6 에 소비자가 없어 무엇을 뜻하는지는 미확인입니다(클래스 독스트링 참고).
    pass_type: str | None = None
    #: ``passData``(``:45``, ``TrGdMenuLtOutPass.java:29-35``) — 정기권 조회에 필요한 연령·기간 선택지 묶음. 정기권 메뉴/종류 라우트와 구조가
    #: 비슷해 ``_parse_pass_menu_data`` 를 쓰되 역 선택 키는 ``h_seiect_station`` 입니다. ``PassConditionViewModel.java:1244``
    #: 가 이 객체를 꺼내고, 같은 함수의 ``:1247-1248`` 이 ``null`` 이면 ``backAlert`` 로 화면을 되돌립니다.
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class TripMenuItem:
    """여행상품 메뉴 한 항목과 그 안내 목록을 담습니다."""

    title: str | None = None
    detail: str | None = None
    menu_type: str | None = None
    button: str | None = None
    contents: tuple[TripMenuContent, ...] = ()
    url: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    #: contCount(TrGdMenuLtOutMenu.java:27)는 String 선언이지만 2026-09-22 라이브 5개 메뉴에서는 JSON 정수 11/6/6/4/3 으로 왔고
    #: len(contList) 와 같았습니다. 라이브러리는 _optional_integer 로 읽습니다. NetworkServiceKt.java:29 의 setLenient 인자는 보호돼 있어
    #: true 또는 숫자 수용의 원인으로 단정할 수 없습니다.
    content_count: int | None = None


@dataclass(frozen=True)
class TripMenuResponse(BaseKorailResponse):
    """여행상품 메뉴 목록을 담습니다."""

    items: tuple[TripMenuItem, ...] = ()
    popup_message: str | None = None


@dataclass(frozen=True)
class ProductReservation:
    """여행상품 예약 한 건의 식별자와 상태를 담습니다."""

    product_name: str | None = None
    reservation_status: str | None = None
    payment_deadline: str | None = None
    payment_status: str | None = None
    virtual_reservation_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    #: ``strVrRsvSqno`` — 예약 상품 순번. 앱 장바구니는 결제정보 조회에 이 값을 씁니다
    #: (BasketTicketViewModel$getPaymentDataForSelectedItems$2$deferredList$1$1.java:235-238).
    reservation_sequence: str | None = None
    #: ``strRsvSttCd`` — 예약 상태 코드. 결제·취소 버튼을 가르는 앱의 비교값은 보호돼 있습니다(ProductReservationListScreenKt.java:744-749).
    reservation_status_code: str | None = None


@dataclass(frozen=True)
class ProductReservationListResponse(BaseKorailResponse):
    """여행상품 예약 목록 한 페이지를 담습니다."""

    items: tuple[ProductReservation, ...] = ()
    total_count: int | None = None


@dataclass(frozen=True)
class ProductDetailResponse(BaseKorailResponse):
    """여행상품 예약의 상세·금액·취소 조건을 담습니다."""

    product_name: str | None = None
    reservation_status: str | None = None
    cancellation_deadline: str | None = None
    cancellation_amount: str | None = None
    cancellation_fee: str | None = None
    received_amount: str | None = None
    total_amount: str | None = None
    usage_period: str | None = None
    included_item_names: tuple[str, ...] = ()
    virtual_reservation_no: str | None = None
    detail_raw: Mapping[str, object] = field(default_factory=dict[str, Any], compare=False)
    #: ``mainInfo.strGdSqno`` — 상품 순번. 여행상품 취소(product.ReservationCancel 의 txtGdSqno)에 씁니다
    #: (ProductReservationListScreenKt.java:1252-1253, MyTicketDetailViewModel.java:3290).
    goods_sequence: str | None = None


@dataclass(frozen=True, kw_only=True)
class ReceiptPayment:
    """영수증의 결제수단 한 행을 담습니다."""

    payment_method: str
    #: h_apv_dt. 계좌·승인·카드·포인트 번호를 포함한 기록 경고는 모듈 설명 참고.
    approval_date: str
    installment_months: int
    amount: int
    account_no: str
    approval_no: str
    card_no: str
    point_no: str
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True, kw_only=True)
class ReceiptCashPayment:
    """영수증에 포함된 현금영수증 한 행을 담습니다. 앱 근거: ReceiptInfo.java:37. String 4개·int 금액 1개이며 전송 키는
    CashReceiptInfo.java:26-35,52 의 명시적 @SerialName 입니다."""

    #: h_apv_mtd_nm — 승인방법 라벨. 인증도메인 인식번호·현금영수증 승인번호도 마스킹하지 않습니다.
    approval_method_name: str
    authentication_domain_recognition_no: str
    cash_receipt_approval_no: str
    cash_receipt_transaction_division_code: str
    total_approved_amount: int
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True, kw_only=True)
class TicketReceipt:
    """승차권 영수증의 이용 내역과 결제 정보를 담습니다."""

    travel_date: str
    departure_station: str
    departure_time: str
    arrival_station: str
    arrival_time: str
    commuter_kind_code: str
    journey_type_code: str
    #: ``h_prt_disc_knd_nm``/``h_prt_disc_knd_cd`` — 영수증에 인쇄된 할인 종류의 이름·코드.
    printed_discount_name: str
    printed_discount_kind_code: str
    print_type: str
    seat_class_name: str
    ticket_kind_code: str
    ticket_kind_name: str
    ticket_status_code: str
    train_class_code: str
    train_class_name: str
    train_group_code: str
    train_no: str
    passenger_counts: tuple[int, int, int]
    received_amount: int
    card_refund_amount: int
    refund_fee: int
    refund_received_amount: int
    point_refund_amount: int
    payments: tuple[ReceiptPayment, ...] = ()
    cash_receipts: tuple[ReceiptCashPayment, ...] = ()
    member_card_no: str
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class TicketReceiptResponse(BaseKorailResponse):
    """승차권 영수증 조회 결과를 담습니다."""

    items: tuple[TicketReceipt, ...] = ()


@dataclass(frozen=True)
class ReservationHistoryTrain:
    """예약 이력의 열차와 결제 기한 정보를 담습니다. 평문 @SerialName 37개 외 보호된 슬롯이 있습니다 (ReservationViewOutTrainInfo.java:94,
    ReservationViewOutTrainInfo$$serializer.java:39-79). 결제 기한은 날짜·시각·문구를 함께 보십시오. 플래그만으로 기한을 알 수는 없습니다.
    2026-09-22 관측은 P100/빈 jrny_info 여서 기한 필드의 라이브 값은 미확인입니다."""

    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    run_date: str | None = None
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    reservation_type_code: str | None = None
    acceptance_possible_flag: str | None = None
    payment_flag: str | None = None
    settlement_flag: str | None = None
    #: ``h_rsv_amt`` — 이 열차 행의 유일한 금액 필드 (``ReservationViewOutTrainInfo.java:496``).
    reserved_amount: str | None = None
    seat_count: int | None = None
    standing_count: int | None = None
    pnr_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # ``h_ntisu_lmt_dt``/``h_ntisu_lmt_tm`` — 이 홀드의 결제 기한 날짜·시각.
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    payment_message: str | None = None
    payment_possible_date: str | None = None
    prepayment_target_flag: str | None = None
    #: h_jrny_sqno는 ReservationHistoryPassenger와 여정을 연결하는 순번입니다.
    journey_sequence: str | None = None


@dataclass(frozen=True)
class ReservationHistoryTicket:
    """예약 이력에 중첩된 발권 승차권 한 행을 담습니다. 앱 근거: ReservationOutTK.java.

    할인(``dcntList``)·동반가족(``fmlyList``)·정산(``stlList``) 하위 목록은 일부러 :attr:`raw` 에만 남깁니다 — :class:`OriginalTicket`
    이 같은 이유로 ``cmpnList``/``stlList`` 를 raw 전용으로 두는 것과 같은 판단입니다."""

    sale_date: str | None = None
    sale_window_no: str | None = None
    sale_sequence: str | None = None
    ticket_kind_code: str | None = None
    movie_ticket_flag: str | None = None
    delay_discount_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryOriginalTicket:
    """예약 이력에 중첩된 원승차권 한 행을 담습니다. 앱 근거: ReservationOrgTk.java."""

    sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    #: ``ogtkRetPwd`` — 원표 반환 비밀번호. 그 자체로 반환 권한이라 민감합니다.
    return_password: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryPassenger:
    """예약 이력의 승객 유형별 인원·할인 정보를 담습니다. 앱 근거: ReservationOutPsgInfo.java."""

    passenger_type_code: str | None = None
    passenger_count_per_info: str | None = None
    discount_kind_code: str | None = None
    discount_kind_code_2: str | None = None
    discount_no: str | None = None
    discount_no_2: str | None = None
    delay_original_window_no: str | None = None
    delay_original_sale_date: str | None = None
    delay_original_sale_sequence: str | None = None
    #: ``dlayOgtkRetPwd`` — 지연배상 원표의 반환 비밀번호.
    delay_original_return_password: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryReservation:
    """예약 이력에 중첩된 예약·운임·결제 정보를 담습니다. 앱 근거: ReservationViewOutJrnyInfo.java:55. 전송 키 reservationOut 은 보호된
    serializer 대신 속성명을 사용한 추정입니다."""

    pnr_no: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    payment_flag: str | None = None
    tickets: tuple[ReservationHistoryTicket, ...] = ()
    original_tickets: tuple[ReservationHistoryOriginalTicket, ...] = ()
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryJourney:
    """예약 이력의 여정 한 개와 열차·부가 정보를 담습니다. 앱 근거: ReservationViewOutJrnyInfo.java.

    ``srv_infos``/``acmp_infos`` 는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다 — 원본 그대로라도 여정 단위로 닿을 수 있게 하기 위해서입니다."""

    trains: tuple[ReservationHistoryTrain, ...] = ()
    service_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    accompanying_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    reservation: ReservationHistoryReservation | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryResponse(BaseKorailResponse):
    """현재 예약 이력과 여정별 상세를 담습니다. 라우트는
    /classes/com.korail.mobile.reservation.ReservationView입니다(NetworkApi.java:635-636;
    ReservationViewOut.java:64)."""

    reservation_passenger_name: str | None = None
    phone_no: str | None = None
    reservation_limit_flag: str | None = None
    seatmap_flag: str | None = None
    process_flag: str | None = None
    follow_flag: str | None = None
    customer_no: str | None = None
    customer_division_code: str | None = None
    customer_sort_code: str | None = None
    customer_class_code: str | None = None
    journey_count: str | None = None
    #: ``guide_infos.guide_info`` — 단일 안내 문구.
    guide_info: str | None = None
    journeys: tuple[ReservationHistoryJourney, ...] = ()
    #: trains는 모든 여정의 열차를 평탄화합니다. 여정별 예약·금액은 journeys에 남습니다.
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        return self.items


@dataclass(frozen=True)
class FreeSeatCarResponse(BaseKorailResponse):
    """열차의 자유석 호차와 안내 문구를 담습니다."""

    title: str | None = None
    #: ``fresScarNo`` -- 호차 문구 그대로입니다(예: "자유석 1량 : 18호차"). 자유석이 없는 열차는 None 입니다.
    car_no: str | None = None
    content: str | None = None


@dataclass(frozen=True)
class GuideSeatConditionResponse(BaseKorailResponse):
    """도우미석 이용 조건과 서버 안내를 담습니다. 파서는 FAIL도 응답으로 반환하지만 FAIL/P058은 세션 만료 예외입니다. 안내는 h_msg_txt를 확인하십시오. timeStamp는
    long 선언이며(GuideSeatCndOut.java:29,50), 보호된 전송 키는 속성명에 따른 추정입니다."""

    time_stamp: int | None = None


@dataclass(frozen=True)
class TrainScheduleItem:
    """좌석배정·병합 조회에 사용하는 열차 정보를 담습니다. 각 DTO 는 다르므로 read_parsers 의 라우트별 필드 맵으로 채웁니다. 한쪽에 없는 필드는 None 이며 맵을 하나로 합치면
    안 됩니다."""

    train_no: str | None = None
    train_no_qb: str | None = None
    train_sequence: str | None = None
    train_group_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    run_date: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    departure_time_qb: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_time_qb: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_construction_order: str | None = None
    arrival_construction_order: str | None = None
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    car_type_name: str | None = None
    general_room_name: str | None = None
    special_room_name: str | None = None
    general_reservation_code: str | None = None
    #: ``h_gen_rsv_nm`` — 두 DTO 모두 선언합니다 (``MergeSeatsCOutTrnInfo``, ``TrainScheduleOutTrainInfo.java:1228``).
    #: ``assignScheduleView.do`` 에서도 실려 옵니다(2026-09-22: ``A1``/``A2`` 각 10행 전부 ``'예약하기'``).
    general_reservation_name: str | None = None
    special_reservation_code: str | None = None
    free_seat_reservation_code: str | None = None
    standing_reservation_code: str | None = None
    #: ``h_stnd_rsv_nm``(``TrainScheduleOutTrainInfo.java:1380``) — 상수 ``'-'`` 가 아니라 살아 있는 값입니다(2026-09-22:
    #: ``A2`` 일부 행이 ``'역발매중'``).
    standing_reservation_name: str | None = None
    journey_reservation_code: str | None = None
    journey_reservation_name: str | None = None
    seat_map_flag: str | None = None
    delay_sale_flag: str | None = None
    wait_reservation_flag: str | None = None
    #: ``h_rsv_psb_nm``(``TrainScheduleOutTrainInfo.java:1296``) — 메뉴에 따라 **내용이 달라지는 화면 문구** 이지 가부 플래그가 아닙니다. 같은
    #: 열차·같은 날짜로 ``menu_id='A1'`` 은 ``'예약가능'``, ``'A2'``(할인 메뉴)는 ``'15%할인'``/``'20%할인'`` 을 돌려줍니다(2026-09-22). 이
    #: 필드에서 할인 라벨이 나오는 것은 매핑 실수가 아니라 서버가 그렇게 보내는 것입니다 — 다른 키로 "고치지" 마십시오.
    reservation_possible_name: str | None = None
    special_reservation_possible_name: str | None = None
    info_text: str | None = None
    popup_message: str | None = None
    shuttle_standing_open_flag: str | None = None
    remaining_standing_count: str | None = None
    standard_remaining_seat_count: str | None = None
    first_remaining_seat_count: str | None = None
    #: h_yms_apl_flg로 병합 대상을 판정합니다. TrainSummary와 같은 의미입니다.
    merge_target_flag: str | None = None
    train_suspended_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # 추가 필드의 잘못된 선택값은 해당 값만 비웁니다.
    special_reservation_name: str | None = None
    free_seat_reservation_name: str | None = None


@dataclass(frozen=True)
class PassScheduleTrain:
    """정기권으로 이용할 수 있는 열차 한 편을 담습니다. 앱 근거: TrainList.java:25-70."""

    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    detour_code: str | None = None
    schedule_price: str | None = None
    train_group_code: str | None = None
    train_no: str | None = None
    train_sequence: str | None = None
    #: h_chg_trn_seq/h_chg_trn_dv_cd — 구간 순서·여정 종류(1 직통/2 환승). TrainSummary 의 설명을 따릅니다.
    change_train_sequence: str | None = None
    change_train_division_code: str | None = None
    run_date: str | None = None
    price_class_code: str | None = None
    route_code: str | None = None
    departure_construction_order: str | None = None
    arrival_construction_order: str | None = None
    car_type_code: str | None = None
    train_class_code: str | None = None
    commuter_use_terminal_code: str | None = None
    commuter_use_terminal_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassAgeOption:
    """패스 예매에 사용할 연령 선택 항목을 담습니다."""

    commuter_age_code: str | None = None
    display_name: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassScheduleInfo:
    """정기권 열차 조회의 조건과 부가 정보를 담습니다."""

    trains: tuple[PassScheduleTrain, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassScheduleMainInfo:
    """정기권 열차 조회의 중첩 상태와 조건을 담습니다."""

    sale_window_no: str | None = None
    work_date: str | None = None
    work_time: str | None = None
    job_id: str | None = None
    version_no: str | None = None
    message_code: str | None = None
    selected_count: str | None = None
    total_selected_count: str | None = None
    count_per_page: str | None = None
    #: 2026-09-22 관측: 총건수>페이지 크기여도 next_page_flag=N, page_count=00000, page_no=1 이었습니다. 이 표본에서 Y 반복만으로는 후속 결과를
    #: 얻지 못합니다. page_size 를 늘리는 방법도 서버 상한·응답을 확인해야 하며 모든 조건의 완전성을 보장하지 않습니다.
    page_count: str | None = None
    next_page_flag: str | None = None
    change_train_division_code: str | None = None
    page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class SeatAssignmentScheduleResponse(BaseKorailResponse):
    """좌석배정 예매 화면의 열차 목록과 조회 조건을 담습니다. 앱 근거: TrainScheduleOut.java:67.

    같은 DTO 모양을 쓰는 형제 파서 ``parsers.py::parse_train_search_metadata``/``TrainSearchMetadata`` 가 이미 이 필드 집합을 정확히
    이렇게 읽으므로 그 이름을 그대로 따릅니다."""

    next_page_flag: str | None = None
    merge_reservation_possible_flag: str | None = None
    job_id: str | None = None
    menu_id: str | None = None
    goods_no: str | None = None
    notice_message: str | None = None
    first_seat_count: str | None = None
    second_seat_count: str | None = None
    agreement_text: str | None = None
    first_departure_time: str | None = None
    result_count: str | None = None
    next_query_station_no: str | None = None
    next_train_no: str | None = None
    next_preceding_train_no: str | None = None
    next_connecting_train_no: str | None = None
    remaining_seat_count: str | None = None
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class IntermediateStation:
    """좌석 병합 구간이 나뉘는 중간역을 담습니다."""

    code: str | None = None
    name: str | None = None
    run_order: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassPeriodOption:
    """패스 예매에 사용할 기간 선택 항목을 담습니다."""

    commuter_period_code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MergeSeatsInquiryResponse(BaseKorailResponse):
    """병합 가능한 열차와 중간역 목록을 담습니다."""

    merge_reservation_possible_flag: str | None = None
    #: 최상위 runDt 선언: MergeSeatsCOut.java:29,112. 2026-09-22 관측 20여 회에는 없었고 행의 h_run_dt 는 존재했습니다. 필요하면
    #: trains[i].run_date 를 확인하십시오. 항상 None 이라는 보장은 아닙니다.
    run_date: str | None = None
    intermediate_stations: tuple[IntermediateStation, ...] = ()
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class PassMenuData:
    """패스 메뉴의 역 선택 조건과 상품 코드를 담습니다."""

    commuter_kind_code: str | None = None
    station_selection: str | None = None
    age_options: tuple[PassAgeOption, ...] = ()
    period_options: tuple[PassPeriodOption, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassPassengerInfo:
    """패스의 승객 종류별 인원 조건을 담습니다."""

    h_cls_prnb: int | None = None
    h_dcnt_knd_cd: str | None = None
    h_st_prnb: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassPassengerInfos:
    """패스 승객 조건 목록을 담습니다."""

    h_chtn_allw_flg: str | None = None
    h_max_cnt: str | None = None
    h_min_cnt: str | None = None
    psg_info: tuple[PassPassengerInfo, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassGoodsInfo:
    """패스 메뉴에 연결된 상품 정보를 담습니다."""

    h_cnd_flg_disc_no: str | None = None
    psg_infos: PassPassengerInfos | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassMenuItem:
    """정기권·패스 메뉴 한 항목과 안내를 담습니다."""

    #: ``afterDay`` — 서버가 문자열로 보냅니다(``PassMenuOutItem.java:28`` ``String``). 형제
    #: :attr:`CommuterKindMenuResponse.after_day` 와 형이 같습니다. 정수가 필요하면 호출자가 변환하십시오 — 앱도 그 자리에서
    #: ``StringExKt.safeToInt`` 로 파싱 실패 시 0을 씁니다.
    after_day: str | None = None
    agreement: str | None = None
    detail_type: str | None = None
    detail_description: str | None = None
    enabled: str | None = None
    item_id: str | None = None
    information: str | None = None
    sale_message_1: str | None = None
    sale_message_2: str | None = None
    sale_message_3: str | None = None
    expanded: str | None = None
    parent_id: str | None = None
    representative_arrival: str | None = None
    representative_departure: str | None = None
    title: str | None = None
    train_group_code: str | None = None
    item_type: str | None = None
    goods_data: PassGoodsInfo | None = None
    pass_data: PassMenuData | None = None
    url: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassMenuResponse(BaseKorailResponse):
    """정기권·패스 메뉴 목록을 담습니다."""

    items: tuple[PassMenuItem, ...] = ()


@dataclass(frozen=True)
class CommuterKindMenuResponse(BaseKorailResponse):
    """정기권 종류별 안내와 예매 조건을 담습니다."""

    after_day: str | None = None
    agreement: str | None = None
    information: str | None = None
    title: str | None = None
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class CrewRequestOption:
    """승무원 호출 시 선택할 요청 사유를 담습니다."""

    message_code: str | None = None
    content: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class CrewRequestListResponse(BaseKorailResponse):
    """승무원 호출 사유 목록을 담습니다."""

    items: tuple[CrewRequestOption, ...] = ()


@dataclass(frozen=True)
class PassScheduleResponse(BaseKorailResponse):
    """정기권으로 이용 가능한 열차 목록을 담습니다."""

    main_info: PassScheduleMainInfo | None = None
    schedules: tuple[PassScheduleInfo, ...] = ()


@dataclass(frozen=True)
class DiscountCardSection:
    """N카드를 적용할 수 있는 구간 한 개를 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 적용 구간(AppSegInfo.java:24-37,
    DiscountCardInfo.java:28). @SerialName 별칭이 없는 키는 보호된 serializer 대신 속성명을 사용한 추정입니다. 일정 조회가 받는 역 이름을 구간에서
    확인할 수 있습니다."""

    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    #: ``jrnySqno`` — 이 구간의 순번(``dcntCrdAplSegSqno`` 는 전 디컴파일 0건인 키입니다).
    journey_sequence: str | None = None
    journey_type_code: str | None = None
    train_group_code: str | None = None
    #: 경유 이름(AppSegInfo.java:36)은 NCardReservationViewModel.java:154-164 의 Triple 을 거쳐
    #: TrainScheduleViewModel.java:2639,2730-2736,2749,2831 에서 입력에 복사됩니다. 대상 필드: AssignScheduleIn.java:41 의
    #: stlbDturDvNm1.
    detour_division_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DiscountCardOnTicket:
    """승차권 상세에 포함된 N카드와 적용 구간을 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 상세의 선택
    할인카드(DiscountCardInfo.java:27-32, TicketDetailOut.java:49,438). 카드번호는 사용내역·할인 예약에 사용합니다. 앱도 N카드 예약 모드에서
    승객 행에 넣습니다 (Passengers.java:766, TicketReservationInPassengerInfo.java:26-34). 할인 코드 153 은 라이브 기록에 의존하며
    ReqDiscount.java:36 의 보호된 평문은 미확인입니다."""

    #: ``h_dcnt_crd_no``(``DiscountCardInfo.java:113`` 의 ``@SerialName``).
    card_no: str | None = None
    #: 기간연장 플래그는 DiscountCardInfo.java:30,117에 선언됩니다. 앱은 이 값을 비교해 연장 버튼에 전달합니다
    #: (NCardTicketSectionKt.smali:7821-7843). 비교 리터럴은 보호돼 Y의 의미를 정적으로 확정하지 않으며 실서버 검증 못 함입니다.
    term_extension_possible_flag: str | None = None
    sections: tuple[DiscountCardSection, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class KorailPointSummaryResponse(BaseKorailResponse):
    """계정의 포인트·쿠폰·복지 자격 요약을 담습니다. 앱 근거: MyXPointViewOut.java:27-74. 별칭 없는 키는 속성명에 따른 추정입니다. 2026-09-22 관측은 자체
    43+봉투 3+서버 추가 2(h_coup_sno1/srNoticeUrl)=48키였습니다. 소비자는 AppSuitLinker 를 거치므로 플래그 코드의 의미를 필드명만으로 확정하지 마십시오."""

    korail_point: str | None = None
    #: h_disc_coup_cnt — 서버가 보고한 할인쿠폰 개수. get_discount_coupons 결과 길이와 항상 같다는 보장은 없습니다.
    discount_coupon_count: str | None = None
    delay_discount_count: str | None = None
    #: h_hdcp_flg — 장애인 등록 관련 서버 플래그. 값은 그대로 보존합니다.
    disability_flag: str | None = None
    #: ``h_subt_dcs_cl_nm`` / ``h_subt_dcs_cl_cd`` — 그 등록이 주는 우대할인 등급. 앱에서 장애인증 라벨 아래 찍힙니다.
    welfare_discount_class_name: str | None = None
    welfare_discount_class_code: str | None = None
    #: ``h_cust_lead_flg_nm`` — 앱에서 보조견 라벨 아래 찍힙니다.
    customer_lead_flag_name: str | None = None
    #: ``h_cp_athn_flg`` / ``h_emil_athn_flg`` — 휴대폰·이메일 인증 여부.
    phone_verified_flag: str | None = None
    email_verified_flag: str | None = None
    contact_channel_content: str | None = None
    #: 소셜 연동 플래그의 서비스별 순서는 7.0.6 에서 미확인입니다. 소비 값이 보호된 LoginMethodApiData.java:18-21 을 거치므로 Python 필드명을 확정된 매핑으로
    #: 신뢰하지 마십시오. 특정 서비스를 연동했을 때의 변화 관측이 필요합니다.
    naver_linked_flag: str | None = None
    kakao_linked_flag: str | None = None
    google_linked_flag: str | None = None
    apple_linked_flag: str | None = None
    # ``h_cust_lead_flg``(``MyXPointViewOut.java:43``) — 보조견 등록 플래그 그 자체. 사람이 읽는 짝은
    # :attr:`customer_lead_flag_name`(``:44``)입니다.
    customer_lead_flag: str | None = None
    #: ``h_hdcp_tp_cd``/``h_hdcp_tp_cd_nm``(``:53,54``) — 장애 유형 코드와 이름. 유형은
    #: :attr:`disability_flag`(``h_hdcp_flg``)가 아니라 이 둘에 있습니다. 셋 다 라이브 응답에 옵니다(2026-09-22).
    disability_type_code: str | None = None
    disability_type_name: str | None = None


@dataclass(frozen=True)
class MileageHistoryEntry:
    """마일리지 적립 또는 사용 내역 한 행을 담습니다.

    ``AmtSpecOutSpecInfo.java:29-35`` 가 선언하는 것이 정확히 아래 일곱 필드입니다. 2026-09-22 라이브에서 3페이지 14행 전부가 이 일곱 키를 문자열로 싣고 그
    밖의 키는 없었습니다."""

    departure_date: str | None = None
    point_division_name: str | None = None
    accrual_division_name: str | None = None
    receipt_division_name: str | None = None
    #: ``pontAmt`` — 이 줄의 포인트 증감. 부호가 붙습니다.
    point_amount: str | None = None
    saved_point_value: str | None = None
    settlement_amount: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """마일리지 내역 한 페이지와 적립·사용 합계를 담습니다. 앱 근거: AmtSpecOut.java:29-39,199-247. 별도로 선언된 합계 필드는 합치지 않습니다. 2026-09-22
    KTX/RAIL_POINT 의 3페이지에서 DTO 밖 railNowSavePontValNum1 을 관측했으며 해당 계정에서는 totAcmRailPontValNum1 과 같았습니다. 추가
    키는 raw 로 제공합니다."""

    #: ``pgCnt`` — 전체 페이지 수(``AmtSpecOut.java:32``).
    page_count: str | None = None
    query_count: str | None = None
    total_available_rail_point: str | None = None
    total_available_rail_point_1: str | None = None
    total_available_affiliate_point: str | None = None
    total_accumulated_rail_point_1: str | None = None
    total_used_rail_point_1: str | None = None
    expiring_point_value: str | None = None
    ktx_mileage_info: str | None = None
    entries: tuple[MileageHistoryEntry, ...] = ()


@dataclass(frozen=True)
class DiscountCardUsage:
    """N카드를 사용한 여행 내역 한 행을 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 사용 내역(NCardHistoryInfo.java:22,224).
    전송 키는 속성명에 따른 추정입니다. 화면 사용: NCardHistoryScreenKt.java:301,431,439,526,528,
    NCardHistoryViewModel.java:123,141. sale_date/sequence/window_no 가 OriginalTicketReference 로 바로 호환된다고
    가정하지 마십시오. 2026-09-22 카드번호 4종은 모두 ERR000100 으로 채워진 응답을 확인하지 못했습니다."""

    #: ``custNm`` — 이 구간을 실제로 탄 사람의 이름.
    passenger_name: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    run_date: str | None = None
    #: apdUsrFlg — 두 번째 등록 사용자(N카드 2인용)가 탔는지의 플래그. 앱은 보호된 1바이트 리터럴과 비교합니다 (NCardHistoryScreenKt.java:301); 그 평문은
    #: 추정하지 않습니다.
    additional_user_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # ``saleDt``/``saleSqno``/``saleWctNo`` — 이 사용 건의 바탕이 된 발매 일자·일련번호·창구번호(``NCardHistoryInfo.java:224``). 클래스
    # 독스트링의 경고를 읽으십시오.
    sale_date: str | None = None
    sale_sequence: str | None = None
    sale_window_no: str | None = None


@dataclass(frozen=True)
class DiscountCardUsageListResponse(BaseKorailResponse):
    """N카드 한 장의 사용 내역 목록을 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. ``ticket.dcntCrdUseQry.do`` — 카드가 쓰인 여행
    목록.

    ``NCardHistoryOut.java:27,82`` 가 싣는 것은 ``@SerialName("tkUseList")`` 하나뿐이라, 전송에 없는 요약 필드를 이 모델도 만들어 붙이지 않습니다.
    """

    items: tuple[DiscountCardUsage, ...] = ()


@dataclass(frozen=True)
class DiscountCardScheduleTrain:
    """N카드로 이용 가능한 열차 한 편을 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 사용 가능
    열차(NCardScheduleItem.java:30-49). 보호된 serializer 대신 속성명으로 읽습니다. 앱이 표시용으로 만드는 Spanned stationInfo 를 서버 필드로
    모델링하지 않습니다. 명시적 @SerialName 이 없다는 사실만으로 실제 전송 키를 확정할 수는 없습니다."""

    train_no: str | None = None
    train_group_code: str | None = None
    run_date: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_station_order: str | None = None
    arrival_station_order: str | None = None
    #: ``dptStnRunOrdr`` — 승차역 "운행" 순서. ``departure_station_order`` (``dptStnConsOrdr``, "편성" 순서)와는 다른 필드입니다.
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    transfer_train_order_no: str | None = None
    price_class_code: str | None = None
    settlement_car_type_code: str | None = None
    settlement_train_class_code: str | None = None
    commuter_price: str | None = None
    direct_transfer_division_code: str | None = None
    detour_code: str | None = None
    detour_name: str | None = None
    route_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DiscountCardScheduleResponse(BaseKorailResponse):
    """N카드로 이용 가능한 열차 목록을 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 일정(NetworkApi.java:339-341,
    NCardScheduleOut.java:27-28). DTO 는 trnScdlList 만 선언합니다. 이 파서는 following_page_exists 를 채우지 않으므로 이 필드를 폴링
    신호로 쓰지 마십시오. 실제 서버의 페이지 지원 여부는 미확인입니다."""

    #: 파서는 이 값을 채우지 않습니다. DiscountCardScheduleResponse의 검증 한계를 따릅니다.
    following_page_exists: str | None = None
    trains: tuple[DiscountCardScheduleTrain, ...] = ()


@dataclass(frozen=True)
class MultiChildDiscountTarget:
    """다자녀 할인 대상으로 등록된 가족 한 명을 담습니다."""

    birth_date: str | None = None
    customer_family_name: str | None = None
    discount_kind_code: str | None = None
    family_sequence: str | None = None
    passenger_type_code: str | None = None
    passenger_type_name: str | None = None
    room_class_code: str | None = None
    requested_discount_kind_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MultiChildDiscountTargetResponse(BaseKorailResponse):
    """다자녀 할인 대상 가족 목록을 담습니다."""

    targets: tuple[MultiChildDiscountTarget, ...] = ()


@dataclass(frozen=True)
class CustomerTripInfo:
    """계정에 저장된 여행 편의설정을 담습니다."""

    additional_seat_attribute_code: str | None = None
    adult_disabled_person_count: str | None = None
    adult_count: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    baby_accompanying_person_count: str | None = None
    changed_at: str | None = None
    changed_by: str | None = None
    child_count: str | None = None
    child_disabled_person_count: str | None = None
    customer_management_no: str | None = None
    day_code: str | None = None
    direction_seat_attribute_group_code: str | None = None
    direct_transfer_division_code: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    early_train_departure_time: str | None = None
    elderly_person_count: str | None = None
    included_flag: str | None = None
    job_start_hour: str | None = None
    location_seat_attribute_group_code: str | None = None
    media_division_code: str | None = None
    room_class_code: str | None = None
    passenger_total: str | None = None
    registered_at: str | None = None
    registration_sequence: str | None = None
    registered_by: str | None = None
    trip_day_no: str | None = None
    train_classification_code: str | None = None
    train_connection_flag: str | None = None
    train_group_code: str | None = None
    usage_day_no: str | None = None
    #: ``gdNo`` — 상품번호(``CustTripInfo.java`` 33필드 중 하나). ``@SerialName`` 이 없어 와이어 철자는 보호됨 이며 코틀린 필드명을 추정해 사용합니다.
    goods_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class CustomerTripInfoResponse(BaseKorailResponse):
    """여행 편의설정 조회 결과를 담습니다."""

    trips: tuple[CustomerTripInfo, ...] = ()


@dataclass(frozen=True)
class MaasServiceDetailInfo:
    """부가서비스의 상품·이용·결제 상세를 담습니다."""

    additional_service_request_no: str | None = None
    booking_time: str | None = None
    branch_name: str | None = None
    partner_name: str | None = None
    delivery_datetime: str | None = None
    drop_times: str | None = None
    dropoff_name: str | None = None
    image: str | None = None
    name: str | None = None
    option_name: str | None = None
    pickup_name: str | None = None
    pickup_place: str | None = None
    pickup_times: str | None = None
    reservation_date: str | None = None
    return_datetime: str | None = None
    start_datetime: str | None = None
    cancel_deadline_date: str | None = None
    cancel_return_amount: str | None = None
    cancel_return_fee: str | None = None
    goods_sequence: str | None = None
    intermediate_value: str | None = None
    received_amount: str | None = None
    reservation_status_name: str | None = None
    reservation_passenger_name: str | None = None
    settlement_deadline_date: str | None = None
    settlement_deadline_datetime: str | None = None
    settlement_status_code: str | None = None
    settlement_status_name: str | None = None
    total_settlement_amount: str | None = None
    usage_period_content: str | None = None
    entity_one: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MaasServiceDetail:
    """신청한 부가서비스 한 건과 그 상세를 담습니다."""

    additional_service_division_code: str | None = None
    additional_service_goods_code: str | None = None
    additional_service_id: str | None = None
    marketing_entity_id: str | None = None
    marketing_entity_name: str | None = None
    additional_service_name: str | None = None
    progress_status_code: str | None = None
    request_no: str | None = None
    passenger_reference_content: str | None = None
    partner_reservation_no: str | None = None
    delivery_close_time: str | None = None
    delivery_start_time: str | None = None
    lead_message_1: str | None = None
    lead_message_2: str | None = None
    pnr_no: str | None = None
    request_date: str | None = None
    request_quantity: str | None = None
    reservation_station_code_name: str | None = None
    reservation_specification_url: str | None = None
    usage_close_date: str | None = None
    usage_start_date: str | None = None
    detail_info: MaasServiceDetailInfo | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MaasServiceDetailListResponse(BaseKorailResponse):
    """신청한 부가서비스 목록을 담습니다."""

    details: tuple[MaasServiceDetail, ...] = ()


@dataclass(frozen=True)
class MaasCancelFeeResponse(BaseKorailResponse):
    """지원하지 않는 부가서비스 환불 수수료 응답 구조를 기록합니다. 결제된 부가서비스의 환불 수수료(maas.cncFee.do, MaasCancelFeeOut.java). 앱은 "환불수수료
    N원" 확인창에 보여 준 뒤 그 값으로 환불을 요청합니다(MyTicketDetailViewModel.java:840-860,1922)."""

    cancel_fee: str | None = None


@dataclass(frozen=True)
class TripChangeDateResponse(BaseKorailResponse):
    """승차권을 변경할 수 있는 날짜 목록을 담습니다. 앱 근거: NetworkApi.java:238; TipChgDateInquiryOut.java:28-30.

    ``tripChgDate``(단수)는 **요청** DTO(``TipChgDateInquiryIn.java:29``)의 필드입니다 — 응답은 복수형
    ``tripChgDates``(``List<String>``)만 선언하므로, 여기서는 단수형을 읽지 않습니다."""

    last_run_date: str | None = None
    trip_change_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommuterPassengerOption:
    """정기권 승객 종류의 인원·연령 범위를 담습니다. 앱 근거: Psg.java:28-33."""

    commuter_usage_age_code: str | None = None
    common_code_name: str | None = None
    #: 연령 범위는 키가 없으면 0이며 정수로 읽을 수 없는 값이면 None입니다.
    customer_age_from: int | None = 0
    customer_age_to: int | None = 0
    #: 인원 범위도 같습니다. 키가 없으면 0, 정수로 읽을 수 없는 값이면 None입니다.
    passenger_count_from: int | None = 0
    passenger_count_to: int | None = 0
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class CommuterInfoResponse(BaseKorailResponse):
    """정기권 예매 단계별 조건·승객·원표 정보를 담습니다."""

    additional_service_goods_flag: str | None = None
    companion_flag: str | None = None
    commuter_kind_code: str | None = None
    #: 요청의 승객별 cmtrUtlAgeCd 목록과 응답의 최상위 스칼라는 동일한 에코로 간주하지 마십시오 (CommutationInfoIn.java:31,
    #: PassConditionViewModel.java:633,653). 2026-09-22 상품 0046 은 E05→E06/E06→E05, 단일 행 상품은 ERR000100 을 관측했습니다.
    #: 타입 차이만으로 모든 에코 가능성을 배제하지는 않으며 선택값은 요청에서 보존하십시오.
    commuter_usage_age_code: str | None = None
    menu_id: str | None = None
    popup_message: str | None = None
    promotion_message: str | None = None
    promotion_url: str | None = None
    seat_attribute_code: str | None = None
    #: 키가 없으면 0, 정수로 읽을 수 없는 값이면 None입니다.
    available_passenger_count_from: int | None = 0
    available_passenger_count_to: int | None = 0
    passenger_options: tuple[CommuterPassengerOption, ...] = ()


@dataclass(frozen=True)
class PriceFare:
    """열차 한 구간의 운임 정보를 담습니다."""

    journey_sequence: str | None = None
    room_class_name: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    total_amount: str | None = None
    train_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PriceFareQuoteResponse(BaseKorailResponse):
    """예매 전 운임 조회 결과를 담습니다."""

    fares: tuple[PriceFare, ...] = ()


@dataclass(frozen=True, kw_only=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    """N카드 2인 승차권의 전달 수령자 후보를 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""

    acceptance_customer_management_no: str
    acceptance_customer_name: str
    acceptance_customer_phone: str
    member_card_no: str


@dataclass(frozen=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    """PNR 기준 중복 예약 확인 결과를 담습니다."""

    #: ``rsvCnt`` — ``TicketDupCheckOut.java:28`` 의 선언은 ``String`` 이고 이 DTO 는 kotlinx 이므로 문자열로 읽습니다(``"0007"`` 은
    #: 그대로). 서버가 이 값을 JSON 정수로 보낸 적이 있는지는 확인하지 않았습니다.
    reservation_count: str | None = None


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceSeat:
    """PBP 수락 내역의 좌석 한 자리를 담습니다."""

    passenger_type_division_name: str
    room_class_code: str
    room_class_name: str
    car_no: int
    seat_no: str
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceJourney:
    """PBP 수락 내역의 여정과 좌석 목록을 담습니다."""

    acceptance_customer_name: str
    acceptance_customer_phone: str
    journey_type_code: str
    member_division_name: str
    acceptance_kind_name: str
    pbp_reservation_no: str
    registered_date: str
    withdrawal_possible_flag: str
    seats: tuple[PbpAcceptanceSeat, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    member_card_no: str


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceTicket:
    """PBP 수락 내역의 승차권과 여정 목록을 담습니다."""

    pnr_no: str
    sale_date: str
    sale_sequence: str
    sale_window_no: str
    return_password: str
    journeys: tuple[PbpAcceptanceJourney, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    """승차권별 PBP 수락 내역 목록을 담습니다."""

    tickets: tuple[PbpAcceptanceTicket, ...] = ()


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """자율 좌석변경이 가능한 승차역과 잔여석을 담습니다. 앱 근거: ChgStnInfo.java:21-35; SeatAvailabilityOut.java:32. 전송 키는 속성명에 따른
    추정입니다. 역별 일반실·특실 잔여좌석을 제공합니다. DTO 의 도착역 코드·이름·편성/운행순서 4개 필드는 이 모델에서 읽지 않습니다."""

    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    departure_construction_order: str | None = None
    departure_run_order: str | None = None
    general_remaining_seats: str | None = None
    special_remaining_seats: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeReason:
    """자율 좌석변경 시 선택할 변경 사유를 담습니다. 앱 근거: ChgRsnInfo.java:21-24; SeatAvailabilityOut.java:31.

    String 속성은 frcSaleRsnCont/qryCode/qryOrdr 입니다. serializer descriptor 의 이름이 보호돼 있어
    (ChgRsnInfo$$serializer.java:34-36) 전송 키는 속성명에 따른 추정입니다."""

    query_code: str | None = None
    query_order: str | None = None
    reason_text: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """자율 좌석변경의 대상 역·사유·열차 정보를 담습니다. 앱 근거: NetworkApi.java:806-808; SeatAvailabilityOut.java:28-42,68. 자체 필드의 전송
    키는 속성명에 따른 추정입니다. 열차 단위 가부와 stations 의 역별 잔여좌석은 다릅니다."""

    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    train_group_code: str | None = None
    train_group_name: str | None = None
    run_date: str | None = None
    general_reservation_possible_code: str | None = None
    special_reservation_possible_code: str | None = None
    change_before_departure_construction_order: str | None = None
    change_before_arrival_construction_order: str | None = None
    existing_departure_run_order: str | None = None
    existing_arrival_run_order: str | None = None
    stations: tuple[SelfSeatChangeStation, ...] = ()
    reasons: tuple[SelfSeatChangeReason, ...] = ()


@dataclass(frozen=True)
class OriginalTicketSeat:
    """변경 기준인 원승차권의 좌석 정보를 담습니다. 앱 근거: SeatInfo.java:25-51; JrnyInfo.java:58. 대리수령용 Seat.java:27-36 과는 이름과 구조가
    다른 타입입니다."""

    passenger_sequence: str | None = None
    assign_sequence: str | None = None
    passenger_type_code: str | None = None
    room_class_code: str | None = None
    car_no: str | None = None
    seat_no: str | None = None
    seat_count: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    requested_seat_attribute_code: str | None = None
    direction_seat_attribute_code: str | None = None
    location_seat_attribute_code: str | None = None
    smoking_seat_attribute_code: str | None = None
    additional_seat_attribute_code: str | None = None
    etc_seat_attribute_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class OriginalTicketJourney:
    """변경 기준인 원승차권의 구간과 좌석 목록을 담습니다. 앱 근거: OrgTk.java:38; JrnyInfo.java:29-63. 대리수령용 Jrny.java:29-38 과 다릅니다. 여정
    순번·역코드·운행순서를 후속 변경 조회에 재사용합니다."""

    journey_sequence: str | None = None
    journey_order: str | None = None
    journey_type_code: str | None = None
    train_no: str | None = None
    train_group_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_construction_order: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    arrival_construction_order: str | None = None
    goods_no: str | None = None
    total_seat_count: str | None = None
    total_standing_count: str | None = None
    general_change_allowed_flag: str | None = None
    single_ticket_flag: str | None = None
    seats: tuple[OriginalTicketSeat, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class OriginalTicket:
    """변경 기준인 원승차권의 식별자·상태·여정을 담습니다. 앱 근거: OrgTk.java:28-52; OgTicketInquiryOut.java:27. 전송 키는 속성명에 따른 추정입니다.
    original_* 는 요청한 승차권 자신의 반환번호가 되돌아온 값이며 repr 에서 숨기지 않습니다. 변경에 필요하지 않은 cmpnList·stlList 는 타입화하지 않지만 raw 에
    지연증명·결제 자격증명이 그대로 남습니다(Cmpn.java:35-38, Stl.java:29,32,37)."""

    pnr_no: str | None = None
    ticket_kind_code: str | None = None
    original_sale_datetime: str | None = None
    original_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    member_card_no: str | None = None
    adult_count: str | None = None
    child_count: str | None = None
    group_discount_count: str | None = None
    passenger_type_division_code: str | None = None
    received_amount: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    change_sale_transaction_no: str | None = None
    sms_send_flag: str | None = None
    forced_sale_reason_text: str | None = None
    journeys: tuple[OriginalTicketJourney, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class OriginalTicketInquiryResponse(BaseKorailResponse):
    """변경 기준인 원승차권 목록을 담습니다. 앱 근거: NetworkApi.java:234-236; OgTicketInquiryOut.java:26-27,54."""

    tickets: tuple[OriginalTicket, ...] = ()


@dataclass(frozen=True, kw_only=True)
class RecentDeliveryRecipient:
    """최근 승차권을 전달한 수령자 한 명을 담습니다."""

    acceptance_customer_management_flag: str
    acceptance_customer_management_no: str
    acceptance_customer_name: str
    acceptance_customer_phone: str
    acceptance_customer_phone_2: str
    member_card_no: str
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    """최근 승차권 전달 수령자 목록을 담습니다."""

    changed_acceptance_reservation_no: str | None = None
    recipients: tuple[RecentDeliveryRecipient, ...] = ()


@dataclass(frozen=True)
class ReservationSeatDetail:
    """예약 상세의 좌석·승객·운임 정보를 담습니다(ReservationOutSeatInfo.java:33,81). h_psg_tp_dv_nm은 DTO에는 없지만 앱 내장
    표본(BasketTicketDataKt.java:44)과 2026-09-22 실서버 8/8행에서 확인했습니다. 재계산 입력의 기존 종류·객실·할인 코드는 이 좌석을 사용하며 다른 응답에서도
    같은 필드가 오는지는 검증 못 함입니다."""

    car_no: str | None = None
    seat_no: str | None = None
    room_class_code: str | None = None
    room_class_name: str | None = None
    passenger_type_code: str | None = None
    #: h_rcvd_amt의 좌석별 합계는 예약 응답에 총액이 없을 때 결제 정산액의 출처가 됩니다.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    total_discount_amount: str | None = None
    seat_group_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # h_psg_tp_dv_nm은 승객 유형의 표시 이름입니다. 클래스 설명의 관측 한계를 따릅니다.
    passenger_type_name: str | None = None


@dataclass(frozen=True)
class ReservationDetailJourney:
    """미결제 예약의 여정 한 개와 좌석 상세를 담습니다."""

    journey_sequence: str | None = None
    journey_type_code: str | None = None
    reservation_change_no: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    #: h_arv_dt는 심야·익일 열차의 도착 시각이 속한 날짜입니다.
    arrival_date: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    train_no: str | None = None
    train_class_name: str | None = None
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR로 다시 조회한 예약의 여정·좌석·정산액을 담습니다. ReservationOut 을 공유하며 창구번호·좌석별 정산액을 확인하는 경로입니다."""

    pnr_no: str | None = None
    window_no: str | None = None
    journey_count: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 정산 합계. 결제 폼의 ``hidMnsStlAmt1`` 을 예약 응답이 아닌 출처로 대조할 수 있습니다.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    journeys: tuple[ReservationDetailJourney, ...] = ()
    #: ReservationOut의 추가 스칼라는 _parsing.RESERVATION_OUT_EXTRA_FIELDS의 대응표를 따릅니다.
    customer_management_no: str | None = None
    mandatory_message: str | None = None
    additional_service_flag: str | None = None
    disability_certificate_number: str | None = None
    pre_settlement_target_flag: str | None = None
    family_info_confirm_flag: str | None = None
    special_room_fare: str | None = None
    issue_possible_date: str | None = None
    issue_possible_time: str | None = None
    passengers: tuple[ReservationPassengerInfo, ...] = ()


@dataclass(frozen=True)
class RefundCommissionResponse(BaseKorailResponse):
    """환불 전 예상 환불액과 수수료를 담습니다. 앱 근거: NetworkApi.java:598-600. 키 근거: RefundCommissionOut.java:35-41,62,140-164. 이
    응답 자체는 실제 환불 완료가 아닙니다."""

    refund_amount: str | None = None
    refund_fee: str | None = None
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
    #: ``h_msg_cd2``/``h_msg_txt2`` — 이 경로가 봉투의 것과 별개로 싣는 **두 번째** 메시지 짝. 성공한 사전 조회에 수수료 정책 안내가 붙는 식입니다.
    secondary_message_code: str | None = None
    secondary_message_text: str | None = None


@dataclass(frozen=True)
class RefundTicketSeat:
    """환불 대상 승차권의 좌석 한 자리를 담습니다."""

    car_no: str | None = None
    seat_no: str | None = None
    buyer_name: str | None = None
    checkin_status_code: str | None = None
    discount_kind_code: str | None = None
    discount_kind_name: str | None = None
    passenger_type_code: str | None = None
    passenger_type_name: str | None = None
    seat_group_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class RefundTicketJourney:
    """환불 대상 승차권의 여정 한 개를 담습니다."""

    journey_sequence: str | None = None
    journey_type_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    departure_station_name: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_station_name: str | None = None
    train_no: str | None = None
    train_class_name: str | None = None
    room_class_name: str | None = None
    platform_no: str | None = None
    seats: tuple[RefundTicketSeat, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class RefundTicketDetailResponse(BaseKorailResponse):
    """환불 대상 승차권의 식별자·여정·운임 상세를 담습니다. 앱 근거: TicketDetailOut.java:38,117. 별칭 없는 전송 키는 추정입니다. 동반자 값은 수수료 조회에
    전달하며(MyTicketDetailViewModel.java:277), 환불 입력은 PaidTicket.from_refund_detail 로 조립하십시오. 2026-09-22 관측
    40응답의 mlgSaveFlg/mlgSaveTgt 는 모두 빈 문자열이었습니다. DTO 미선언(TicketDetailOut.java:39-91,117)이므로 타입화하지 않지만 raw 에
    남습니다."""

    pnr_no: str | None = None
    sale_date: str | None = None
    sale_time: str | None = None
    window_name: str | None = None
    original_sale_date: str | None = None
    original_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    #: retPsbFlg는 환불 성공 보장이 아닙니다(TicketDetailOut.java:71). 2026-09-22: 상세 40응답은 Y였지만 수수료 조회는 승차일 경과 5건
    #: WRT200022·이미 반환 2건 WRT200399였고, 목록 이력 143장은 N이었습니다. 앱은 사용 여부도 검사합니다(NormalTicketSectionKt.java:951). 비교값과
    #: 화면 진입 조건은 미확인입니다. 수수료 조회와 실제 환불 결과를 별도로 확인하십시오.
    refund_possible_flag: str | None = None
    return_flag: str | None = None
    total_fare_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    train_running_flag: str | None = None
    #: ``h_abrd_ps_nm``/``s_brth`` — **탑승자 본인**의 성명·생년월일. ``h_compa_nm``/``h_compa_brth``(동승자 쌍, 아래)와는 별개의, 최상위
    #: 단일 필드 쌍입니다(``TicketDetailOut.java:410,418``). ``psgNmList`` (아래 :attr:`passenger_names`, 승객 성명 **목록**)와도
    #: 서로 다른 필드입니다 — 요약 필드 하나와 목록 하나이지 같은 것의 중복이 아닙니다.
    passenger_name: str | None = None
    passenger_birth_date: str | None = None
    #: ``h_compa_nm``/``h_compa_brth`` — CommissionView 요청에 ``h_comp_nm``/``h_comp_cert_no`` 로 그대로 복사돼 나갑니다.
    companion_name: str | None = None
    companion_birth_date: str | None = None
    #: PBP 대상은 우선 TicketListTicket.pbp_acceptance_target_flag에서 확인하십시오. 2026-09-22 상세 40응답(20승차권×2모드)에는 후보 키가
    #: 없었으며 목록 Y 6건도 같았습니다. 목록 키는 MyTicketListOutTicket.java:92,300, 상세 필드·setter는
    #: TicketDetailOut.java:65,1936입니다. 앱은 목록 값을 주입하지만 서버 전송 불가능의 증거는 아닙니다(MyTicketBaseViewModel.java:769).
    pbp_acceptance_target_flag: str | None = None
    #: ``h_dlay_flg``/``h_dlay_tk_flg`` — 지연 보상 대상 여부.
    delay_flag: str | None = None
    delay_ticket_flag: str | None = None
    #: ``addSrvFlg``/``addSrvCancel`` — 딸린 부가서비스가 있는지, 환불이 그것도 함께 취소하는지 여부.
    additional_service_flag: str | None = None
    additional_service_cancel: str | None = None
    #: ``h_qrcode`` — 이 승차권의 QR 코드(``TicketDetailOut.java:478``).
    qr_code: str | None = None
    #: ``psgNmList`` — 승객 성명 목록(``List<PsgNameInfo>``). ``@SerialName`` 이 없어 와이어 철자는 보호됨, 코틀린 필드명을 추정해 사용합니다. 각
    #: 원소는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다.
    passenger_names: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    #: ``seatTicketList`` — 좌석 배정 목록(``List<SeatAssignInfo>``, 보호됨).
    seat_tickets: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    #: ``limousine`` — 연계된 리무진 예약(단일 객체, 보호됨). 없으면 ``None``.
    limousine: Mapping[str, object] | None = field(default=None, compare=False)
    #: ``dtlList`` — 지연 정보 목록(``List<DelayInfo>``, 보호됨).
    delay_details: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    journeys: tuple[RefundTicketJourney, ...] = ()
    #: ``dcnt_crd_info`` — 이 "승차권"이 실은 할인카드(N카드)일 때만 있습니다. 보통 승차권에서는 ``None`` 입니다.
    discount_card: DiscountCardOnTicket | None = None
