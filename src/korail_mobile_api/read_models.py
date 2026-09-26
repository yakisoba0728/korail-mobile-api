# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""선택 스칼라의 부재는 None이며 원문·민감값 정책은 models와 같습니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .models import BaseKorailResponse, ReservationPassengerInfo


@dataclass(frozen=True)
class TicketListTrain:
    """승차권 한 장에 포함된 열차 구간 정보를 담습니다.

    호차 번호(``car_no``)처럼 서버가 정수로 보내는 값도 문자열로 담습니다."""

    # 앱 근거: TicketListTrainInfo.java:72. 라이브 이력 139행: 21개 키가 모두 있었고 h_srcar_no 는 String 선언과 달리 모두 JSON
    # 정수였습니다(문자열로 받습니다).
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    # 한 계정 관측에서 131행 모두에 있었습니다.
    #: 승차권 종류 코드(``h_tk_knd_cd``)입니다. 예약 행이 아니라 승차권 행의 값을 읽습니다.
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    train_info: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # h_tk_sqno 선언: MyTicketListOutTicket.java:92. 다른 조건에서도 필수인지는 검증 못 함입니다.
    ticket_sequence: str | None = None
    #: 승차권 상태 이름(``h_tk_stt_nm``)입니다. 서버가 보낸 이름을 그대로 담으며 ``ticket_status_code``를 따로 번역하지 않습니다.
    ticket_status_name: str | None = None
    # 앱 버튼 조건은 상세 플래그와 사용 여부 검사입니다(NormalTicketSectionKt.java:951, TicketHelper.java:3173-3199). 비교 리터럴은
    # 보호돼 있습니다.
    #: 반환 가능 여부 플래그(``h_ret_psb_flg``)입니다. 앱은 승차권 상세의 플래그와 사용 여부도 함께 확인하므로 이 값만으로 환불할 수
    #: 있는지 판단할 수 없습니다. 앱이 비교하는 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    return_possible_flag: str | None = None
    use_transaction_no: str | None = None
    notify_use_transaction_no: str | None = None
    # 실서버 검증 못 함. 앱은 목록 값을 상세에 주입합니다(MyTicketBaseViewModel.java:769, MyTicketDetailViewModel.java:1521). 상세
    # 40응답에는 두 후보 키가 없었습니다.
    #: 대리수령 대상 여부 플래그(``h_pbp_acep_tgt_flg``)입니다. 승차권 상세 응답에는 이 값이 보통 없으므로, 앱처럼 환불하려면 이 값을
    #: ``refund``의 ``pbp_acceptance_target_flag``로 넘기세요.
    pbp_acceptance_target_flag: str | None = None
    trains: tuple[TicketListTrain, ...] = ()


@dataclass(frozen=True)
class TicketListReservation:
    """예약 하나에 속한 승차권 목록과 부가서비스를 담습니다.

    ``tickets`` 외의 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 키가
    다르면 해당 필드는 ``None``입니다."""

    # MyTicketListOutReservation 의 명시적 키는 ticket_list 이며 나머지는 보호된 serializer 대신 속성명으로 읽는 추정입니다.
    tickets: tuple[TicketListTicket, ...] = ()
    # 선택 스칼라의 전송 키는 속성명에 따른 추정입니다. mode=2 의 예약 128행은 ticket_list 외 키가 없었습니다. 다른 응답의 필드
    # 부재까지 보장하지 않습니다.
    #: 출발 일시(``hDptDtTm``)입니다. 응답에 없으면 ``None``입니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # 선택값의 타입이 어긋나면 해당 값만 비웁니다. addSrvInfo(MyTicketListOutReservation.java:39)는 MaaS 의 AddSrvItem 과 같은 타입이라 모델을
    # 공유합니다(MaasDetailOut.java:27, AddSrvItem.java:28-49).
    additional_service: MaasServiceDetail | None = None
    # ticketKind 는 보호된 enum 이름을 매핑하지 않고 문자열로 둡니다 (MyTicketListOutReservation.java:52,59;
    # TicketDefine.java:1078-1131).
    #: 승차권 종류(``ticketKind``)입니다. 서버가 보낸 문자열을 그대로 담으며, 값의 의미는 앱 내부 값이 공개돼 있지 않아 확인하지
    #: 못했습니다.
    ticket_kind: str | None = None


@dataclass(frozen=True)
class TicketListResponse(BaseKorailResponse):
    """현재 승차권 또는 구매 이력을 예약별로 묶어 담습니다."""

    reservations: tuple[TicketListReservation, ...] = ()
    #: 전체 건수(``h_total_cnt``)입니다. 키가 없으면 ``None``입니다.
    total_count: str | None = None


@dataclass(frozen=True)
class ServiceStatusResponse(BaseKorailResponse):
    """예매 서비스의 운영 상태 응답을 담습니다."""


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
    # h_tk_cnt — CartInfo.java:51 의 선언은 String 이고 이 DTO 는 kotlinx 이므로 문자열로 둡니다.
    #: 승차권 매수(``h_tk_cnt``)입니다. 서버가 정수로 보내도 문자열로 담습니다.
    ticket_count: str | None = None
    usage_start_date: str | None = None
    usage_start_time: str | None = None
    usage_close_time: str | None = None
    partner_reservation_no: str | None = None
    pnr_no: str | None = None
    lump_sum_target_no: str | None = None
    customer_no: str | None = None
    virtual_reservation_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # CartInfo.java:28-61,281-392의 문자열은 읽고 중첩 결제 상세 6객체는 raw에 보존합니다. 보호 리터럴은 미확인입니다.
    item_type_code: str | None = None
    # h_add_srv_mrk_ent_id: CartInfo.java:31, @SerialName 289행. provider_name 은 h_add_srv_mrk_ent_nm(CartInfo.java:32)입니다.
    #: 부가서비스 제공 업체 ID(``h_add_srv_mrk_ent_id``)입니다. 업체 이름은 ``provider_name``에 있습니다.
    provider_id: str | None = None
    # CartInfo.java:40,41,42, @SerialName 325/329/333행.
    #: 이 행의 항목 일련번호(``h_item_sqno``)입니다.
    item_sequence: str | None = None
    #: 여정 일련번호(``h_jrny_sqno``)입니다.
    journey_sequence: str | None = None
    #: 여정 구분 코드(``h_jrny_tp_cd``)입니다.
    journey_type_code: str | None = None
    # utlClsDt: CartInfo.java:56, @SerialName 377행. 앱도 둘을 이어 붙여 한 일시로 씁니다(PayTicketContentKt.java:5234:
    # getUtlClsDt() + getUtlClsTm()).
    #: 이용 종료 날짜(``utlClsDt``)입니다. ``usage_close_time``과 이어 붙이면 이용 종료 일시가 됩니다.
    usage_close_date: str | None = None
    # h_stl_lmt_tm: CartInfo.java:49,361. 앱은 MaaS 전용 분기에서 행을 고른 뒤 남은 시간을 계산합니다
    # (PayViewModel.java:11658-11679, DateTimeExKt.java:407-431).
    #: 결제 기한(``h_stl_lmt_tm``)입니다. 그 자체로 기한을 나타내는 문자열입니다.
    settlement_limit_time: str | None = None
    # 아래 다섯은 CartInfo 가 선언만 하고(CartInfo.java:48,50,36,47,35, @SerialName 357/365/309/353/305행) 디컴파일
    # 어디에서도 게터를 읽는 화면 코드를 찾지 못했습니다. 이름은 와이어 키를 그대로 옮긴 것이고 의미는 미확인입니다.
    #: 응답의 ``h_stl_extns_tno`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    settlement_extension_transaction_no: str | None = None
    #: 응답의 ``h_stl_mns_allw_val`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    settlement_means_allow_value: str | None = None
    #: 응답의 ``h_fld_stl_dv`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    field_settlement_division: str | None = None
    #: 응답의 ``h_spvs_rs_stn_cd`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    supervising_station_code: str | None = None
    #: 응답의 ``h_filler`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    filler: str | None = None

    @property
    def usage_window(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        """이용 시작일·시작 시각·종료 시각을 한 번에 반환합니다."""
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DepositBankListResponse(BaseKorailResponse):
    """입금 가능한 은행 목록을 담습니다."""

    items: tuple[DepositBank, ...] = ()


@dataclass(frozen=True)
class DelayDiscountTicket:
    """지연할인권 한 장의 식별자·사용 조건을 담습니다.

    사용 가능 기한(``h_use_psb_dt``)은 읽지 않습니다. 응답에 있으면 ``raw``에서 확인하세요."""

    # 앱 근거: DelayCoupon.java:32-55. h_use_psb_dt(사용 가능 기한)는 전 디컴파일에 0건이라 읽지 않습니다.
    fare: str | None = None
    original_sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    ticket_sequence: str | None = None
    ticket_kind_code: str | None = None
    original_ticket_sale_date: str | None = None
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
    buyer_name: str | None = None
    passenger_name: str | None = None
    page_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DelayDiscountTicketListResponse(BaseKorailResponse):
    """지연할인권 목록과 페이지 정보를 담습니다.

    페이지 정보(``current_page``, ``total_pages``, ``total_count``, ``row_count``, ``last_page_flag``)는 응답의 ``main_info``
    블록에서 읽습니다. 블록이 없으면 모두 ``None``입니다."""

    # main_info는 DTO 밖 서버 추가 블록입니다(DelayDiscountViewOut.java:24,51). 날짜 입력 8종에서 12키를 확인했지만 할인권 없는
    # 응답뿐이었습니다.
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
    # CouponOutInfo.java:63.
    #: 할인율·할인액 구분 코드(``h_disc_rt_amt_dv_cd``)입니다. 코드 값의 의미를 확인하지 못했습니다.
    discount_rate_amount_division_code: str | None = None
    weekday_fare_discount: str | None = None
    weekday_price_discount: str | None = None
    weekend_fare_discount: str | None = None
    weekend_price_discount: str | None = None
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassOpenDate:
    """패스 사용 개시일 한 행과 그 항목 일련번호·PNR을 담습니다.

    ``PassAvailabilityResponse.pass_info``의 한 행입니다. 사용 개시일만 필요하면 ``PassAvailabilityResponse.open_dates``를
    쓰세요."""

    # 앱 근거: PassInfo.java:92,96,100,149. open_dates 는 날짜만 모은 편의 목록입니다. 할당 원리·항상 변화 여부는 미확인입니다.
    open_date: str | None = None
    item_sequence: str | None = None
    pnr_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassAvailabilityMainInfo:
    """패스 사용일 조회의 중첩 상태와 건수를 담습니다.

    이 응답은 결과 코드를 최상위가 아니라 이 블록의 ``message_code``에만 담아 보낼 수 있습니다. 라이브러리는 이 값으로 예외를
    발생시키지 않으므로 필요하면 직접 확인하세요."""

    # 앱 근거: MainInfo.java:103,107,111,115,172. 관측 29종은 최상위 h_msg_cd 없이 이 블록에 IRZ000001/IRZ000005 등을 담았습니다.
    message_code: str | None = None
    total_count: str | None = None
    row_count: str | None = None
    selected_page_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassAvailabilityResponse(BaseKorailResponse):
    """패스의 사용 개시일·발권 가능일·창구 목록을 담습니다."""

    #: ``pass_info``의 사용 개시일만 모은 목록입니다. 날짜가 없는 행은 건너뜁니다.
    open_dates: tuple[str, ...] = ()
    ticket_issue_dates: tuple[str, ...] = ()
    offices: tuple[PassOffice, ...] = ()
    pass_info: tuple[PassOpenDate, ...] = ()
    main_info: PassAvailabilityMainInfo | None = None


@dataclass(frozen=True)
class TripMenuContent:
    """여행상품 메뉴의 안내 한 행과 패스 조건을 담습니다."""

    # 21개 문자열과 passData 객체입니다(TrGdMenuLtOutCont.java:26-47,72).
    title: str | None = None
    detail: str | None = None
    detail_type: str | None = None
    active: str | None = None
    agree: str | None = None
    info: str | None = None
    image: str | None = None
    url: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # cmtrKndCd: TrGdMenuLtOutCont.java:26. 앱도 contList에서 이 코드로 찾습니다(PassConditionViewModel.java:1241). 실서버 관측:
    # 60행 중 menuType='P'인 6행에만 0046·0007·0049 값이 있었습니다.
    #: 정기권 종류 코드(``cmtrKndCd``)입니다. ``get_commuter_kind_menu``의 ``commuter_kind_code``로 넘깁니다. 정기권 메뉴가 아닌
    #: 행에서는 ``None``일 수 있습니다.
    commuter_kind_code: str | None = None
    # 7.0.6 에 소비자가 없어 무엇을 뜻하는지는 미확인입니다.
    #: 응답의 ``passType`` 값입니다. 의미를 확인하지 못했습니다.
    pass_type: str | None = None
    # passData(TrGdMenuLtOutCont.java:45, TrGdMenuLtOutPass.java:29-35). PassConditionViewModel.java:1244 가 이 객체를 꺼내고,
    # 같은 함수의 1247-1248행이 null 이면 backAlert 로 화면을 되돌립니다.
    #: 정기권 조회에 필요한 연령·기간 선택지 묶음(``passData``)입니다. 없으면 ``None``입니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # contCount(TrGdMenuLtOutMenu.java:27)는 String 선언이지만 라이브 5개 메뉴에서는 JSON 정수 11/6/6/4/3 으로 왔고 len(contList) 와
    # 같았습니다. NetworkServiceKt.java:29 의 setLenient 인자는 보호돼 있어 true 또는 숫자 수용의 원인으로 단정할 수 없습니다.
    #: 안내 행 개수(``contCount``)입니다. 정수나 숫자 문자열을 정수로 읽으며, 그 밖의 값이면 ``None``입니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # 앱 장바구니는 결제정보 조회에 이 값을 씁니다
    # (BasketTicketViewModel$getPaymentDataForSelectedItems$2$deferredList$1$1.java:235-238).
    #: 예약 순번(``strVrRsvSqno``)입니다. ``virtual_reservation_no``와 함께 ``get_product_detail``의 ``reservation_sequence``로
    #: 넘깁니다.
    reservation_sequence: str | None = None
    # 결제·취소 버튼을 가르는 앱의 비교값은 보호돼 있습니다(ProductReservationListScreenKt.java:744-749).
    #: 예약 상태 코드(``strRsvSttCd``)입니다. 코드 값의 의미는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
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
    detail_raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # 여행상품 취소(product.ReservationCancel 의 txtGdSqno)에 씁니다 (ProductReservationListScreenKt.java:1252-1253,
    # MyTicketDetailViewModel.java:3290).
    #: 상품 일련번호(``strGdSqno``)입니다. ``cancel_product_reservation``은 이 값과 ``virtual_reservation_no``로 취소를 요청하며,
    #: 값이 비어 있으면 요청을 보내기 전에 ``KorailProtocolError``를 발생시킵니다.
    goods_sequence: str | None = None


@dataclass(frozen=True, kw_only=True)
class ReceiptPayment:
    """영수증의 결제수단 한 행을 담습니다."""

    payment_method: str
    approval_date: str
    installment_months: int
    amount: int
    account_no: str
    approval_no: str
    card_no: str
    point_no: str
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, kw_only=True)
class ReceiptCashPayment:
    """영수증에 포함된 현금영수증 한 행을 담습니다.

    인증 도메인 인식번호와 현금영수증 승인번호도 가리지 않고 서버가 보낸 값 그대로 담습니다."""

    # 앱 근거: ReceiptInfo.java:37. String 4개·int 금액 1개이며 전송 키는 CashReceiptInfo.java:26-35,52 의 명시적 @SerialName
    # 입니다.
    #: 승인 방법 이름(``h_apv_mtd_nm``)입니다.
    approval_method_name: str
    authentication_domain_recognition_no: str
    cash_receipt_approval_no: str
    cash_receipt_transaction_division_code: str
    total_approved_amount: int
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TicketReceiptResponse(BaseKorailResponse):
    """승차권 영수증 조회 결과를 담습니다."""

    items: tuple[TicketReceipt, ...] = ()


@dataclass(frozen=True)
class ReservationHistoryTrain:
    """예약 이력의 열차와 결제 기한 정보를 담습니다.

    결제 기한은 ``payment_deadline_date``와 ``payment_deadline_time``에 있으며, 값이 없으면 ``None``입니다. 플래그 필드만으로는
    기한을 알 수 없습니다. 이 모델이 읽지 않는 응답 키도 있으며, 원본은 ``raw``에 남습니다."""

    # 평문 @SerialName 37개 외 보호된 슬롯이 있습니다 (ReservationViewOutTrainInfo.java:94,
    # ReservationViewOutTrainInfo$$serializer.java:39-79). 채워진 결제 기한 값은 미확인입니다.
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
    # ReservationViewOutTrainInfo.java:496.
    #: 예약 금액(``h_rsv_amt``)입니다. 이 열차 행에 있는 유일한 금액 필드입니다.
    reserved_amount: str | None = None
    seat_count: int | None = None
    standing_count: int | None = None
    pnr_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    payment_message: str | None = None
    payment_possible_date: str | None = None
    prepayment_target_flag: str | None = None
    journey_sequence: str | None = None


@dataclass(frozen=True)
class ReservationHistoryTicket:
    """예약 이력에 중첩된 발권 승차권 한 행을 담습니다."""

    sale_date: str | None = None
    sale_window_no: str | None = None
    sale_sequence: str | None = None
    ticket_kind_code: str | None = None
    movie_ticket_flag: str | None = None
    delay_discount_flag: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryOriginalTicket:
    """예약 이력에 중첩된 원표 한 행을 담습니다."""

    sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryPassenger:
    """예약 이력의 승객 유형별 인원·할인 정보를 담습니다."""

    passenger_type_code: str | None = None
    passenger_count_per_info: str | None = None
    discount_kind_code: str | None = None
    discount_kind_code_2: str | None = None
    discount_no: str | None = None
    discount_no_2: str | None = None
    delay_original_window_no: str | None = None
    delay_original_sale_date: str | None = None
    delay_original_sale_sequence: str | None = None
    delay_original_return_password: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryReservation:
    """예약 이력에 중첩된 예약·운임·결제 정보를 담습니다.

    이 블록은 추정한 응답 키(``reservationOut``)로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    키가 다르면 ``ReservationHistoryJourney.reservation``은 ``None``입니다."""

    # 앱 근거: ReservationViewOutJrnyInfo.java:55. 전송 키 reservationOut 은 보호된 serializer 대신 속성명을 사용한 추정입니다.
    pnr_no: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    payment_flag: str | None = None
    tickets: tuple[ReservationHistoryTicket, ...] = ()
    original_tickets: tuple[ReservationHistoryOriginalTicket, ...] = ()
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryJourney:
    """예약 이력의 여정 한 개와 열차·부가 정보를 담습니다.

    ``service_infos``(``srv_infos``)와 ``accompanying_infos``(``acmp_infos``)는 행을 해석하지 않고 응답의 원본 매핑을 그대로
    담습니다."""

    # srv_infos/acmp_infos 는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다 — 원본 그대로라도 여정 단위로 닿을 수 있게 하기
    # 위해서입니다.
    trains: tuple[ReservationHistoryTrain, ...] = ()
    service_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    accompanying_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    reservation: ReservationHistoryReservation | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryResponse(BaseKorailResponse):
    """현재 예약 이력과 여정별 상세를 담습니다.

    남아 있는 예약이 없어 결과 코드 ``P100``의 실패 응답이 오면 예외를 발생시키지 않고, 목록이 빈 응답을 돌려줍니다."""

    # 라우트는 /classes/com.korail.mobile.reservation.ReservationView입니다(NetworkApi.java:635-636;
    # ReservationViewOut.java:64).
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
    guide_info: str | None = None
    journeys: tuple[ReservationHistoryJourney, ...] = ()
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        """``items``와 같은 열차 목록을 반환합니다."""
        return self.items


@dataclass(frozen=True)
class FreeSeatCarResponse(BaseKorailResponse):
    """열차의 자유석 호차와 안내 문구를 담습니다."""

    title: str | None = None
    #: 자유석 호차 번호(``fresScarNo``)입니다. 자유석이 없는 열차는 ``None``입니다.
    car_no: str | None = None
    content: str | None = None


@dataclass(frozen=True)
class GuideSeatConditionResponse(BaseKorailResponse):
    """도우미석 이용 조건과 서버 안내를 담습니다.

    실패 응답도 예외를 발생시키지 않고 돌려줍니다(세션 만료는 제외). 안내 문구는 ``h_msg_txt``에 있습니다. ``time_stamp``는 추정한
    응답 키(``timeStamp``)로 읽으며, 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 앱은 실패 응답의 h_msg_txt를 안내합니다. timeStamp는 long 선언이며(GuideSeatCndOut.java:29,50), 보호된 전송 키는 속성명에
    # 따른 추정입니다.
    time_stamp: int | None = None


@dataclass(frozen=True)
class TrainScheduleItem:
    """좌석배정·병합 조회에 사용하는 열차 정보를 담습니다.

    ``get_seat_assignment_schedule``과 ``get_merge_seats_inquiry``는 응답 모양이 달라 채우는 필드가 다릅니다. 한쪽 응답에 없는
    필드는 ``None``입니다."""

    # 각 DTO 는 다르므로 read_parsers 의 라우트별 필드 맵으로 채웁니다. 한쪽에 없는 필드는 None 이며 맵을 하나로 합치면 안 됩니다.
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
    # h_gen_rsv_nm — 두 DTO 모두 선언합니다 (MergeSeatsCOutTrnInfo, TrainScheduleOutTrainInfo.java:1228).
    #: 일반실 예약 표시 이름(``h_gen_rsv_nm``)입니다. 두 조회 모두 이 필드를 채웁니다.
    general_reservation_name: str | None = None
    special_reservation_code: str | None = None
    free_seat_reservation_code: str | None = None
    standing_reservation_code: str | None = None
    # h_stnd_rsv_nm(TrainScheduleOutTrainInfo.java:1380). 관측: menu_id A2 일부 행이 '역발매중'이었습니다.
    #: 입석 예약 표시 이름(``h_stnd_rsv_nm``)입니다. 고정값 ``"-"``가 아니라 행마다 다른 값(예: ``"역발매중"``)이 옵니다.
    standing_reservation_name: str | None = None
    journey_reservation_code: str | None = None
    journey_reservation_name: str | None = None
    seat_map_flag: str | None = None
    delay_sale_flag: str | None = None
    wait_reservation_flag: str | None = None
    # h_rsv_psb_nm(TrainScheduleOutTrainInfo.java:1296). 이 필드에서 할인 라벨이 나오는 것은 매핑 실수가 아니라 서버가 그렇게
    # 보내는 것입니다 — 다른 키로 "고치지" 마세요.
    #: 예약 가능 표시 문구(``h_rsv_psb_nm``)입니다. 가부 플래그가 아니라 메뉴에 따라 내용이 달라지는 화면 문구이며, 할인 라벨이
    #: 들어 있을 수도 있습니다.
    reservation_possible_name: str | None = None
    special_reservation_possible_name: str | None = None
    info_text: str | None = None
    popup_message: str | None = None
    shuttle_standing_open_flag: str | None = None
    remaining_standing_count: str | None = None
    standard_remaining_seat_count: str | None = None
    first_remaining_seat_count: str | None = None
    merge_target_flag: str | None = None
    train_suspended_flag: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    special_reservation_name: str | None = None
    free_seat_reservation_name: str | None = None


@dataclass(frozen=True)
class PassScheduleTrain:
    """정기권으로 이용할 수 있는 열차 한 편을 담습니다."""

    # 앱 근거: TrainList.java:25-70.
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    detour_code: str | None = None
    schedule_price: str | None = None
    train_group_code: str | None = None
    train_no: str | None = None
    train_sequence: str | None = None
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassAgeOption:
    """패스 예매에 사용할 연령 선택 항목을 담습니다."""

    commuter_age_code: str | None = None
    display_name: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassScheduleInfo:
    """정기권 열차 조회의 조건과 부가 정보를 담습니다."""

    trains: tuple[PassScheduleTrain, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    # 관측: 총건수>페이지 크기여도 next_page_flag=N, page_count=00000, page_no=1 이었습니다. 이 표본에서 Y 반복만으로는 후속 결과를
    # 얻지 못합니다. page_size 를 늘리는 방법도 서버 상한·응답을 확인해야 하며 모든 조건의 완전성을 보장하지 않습니다.
    #: 페이지 수(``h_page_cnt``)입니다. 전체 건수가 페이지 크기보다 커도 ``next_page_flag``가 ``"N"``으로 올 수 있으므로, 이 값과
    #: ``next_page_flag``만으로 모든 결과를 받았다고 판단하지 마세요.
    page_count: str | None = None
    next_page_flag: str | None = None
    change_train_division_code: str | None = None
    page_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SeatAssignmentScheduleResponse(BaseKorailResponse):
    """좌석배정 예매 화면의 열차 목록과 조회 조건을 담습니다.

    조회 조건 필드의 이름은 열차 조회 결과의 ``TrainSearchMetadata``와 대부분 같습니다. ``merge_reservation_possible_flag``는
    이 응답에서 읽지 않으므로 항상 ``None``입니다."""

    # 앱 근거: TrainScheduleOut.java:67. 같은 DTO 모양을 쓰는 형제 파서 parsers.py::parse_train_search_metadata/TrainSearchMetadata
    # 가 이미 이 필드 집합을 정확히 이렇게 읽으므로 그 이름을 그대로 따릅니다. h_merge_rsv_psb_flg 는 MergeSeatsCOutTrnInfos 에만
    # 선언됩니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassPeriodOption:
    """패스 예매에 사용할 기간 선택 항목을 담습니다."""

    commuter_period_code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MergeSeatsInquiryResponse(BaseKorailResponse):
    """병합 가능한 열차와 중간역 목록을 담습니다."""

    merge_reservation_possible_flag: str | None = None
    # 최상위 runDt 선언: MergeSeatsCOut.java:29,112. 관측 20여 회에는 없었고 행의 h_run_dt 는 존재했습니다.
    #: 응답 최상위의 운행일(``runDt``)입니다. 응답에 없으면 ``None``이며, 열차별 운행일은 ``trains`` 각 항목의 ``run_date``에
    #: 있습니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassPassengerInfo:
    """패스의 승객 종류별 인원 조건을 담습니다."""

    h_cls_prnb: int | None = None
    h_dcnt_knd_cd: str | None = None
    h_st_prnb: int | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassPassengerInfos:
    """패스 승객 조건 목록을 담습니다."""

    h_chtn_allw_flg: str | None = None
    h_max_cnt: str | None = None
    h_min_cnt: str | None = None
    psg_info: tuple[PassPassengerInfo, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassGoodsInfo:
    """패스 메뉴에 연결된 상품 정보를 담습니다."""

    h_cnd_flg_disc_no: str | None = None
    psg_infos: PassPassengerInfos | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassMenuItem:
    """정기권·패스 메뉴 한 항목과 안내를 담습니다."""

    # afterDay: PassMenuOutItem.java:28 String. 앱은 그 자리에서 StringExKt.safeToInt 로 파싱 실패 시 0을 씁니다.
    #: 응답의 ``afterDay`` 값입니다. 서버가 보낸 문자열을 그대로 담으므로, 정수가 필요하면 직접 변환하세요.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    """N카드를 적용할 수 있는 구간 한 개를 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 적용 구간(AppSegInfo.java:24-37,
    # DiscountCardInfo.java:28). @SerialName 별칭이 없는 키는 보호된 serializer 대신 속성명을 사용한 추정입니다.
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    journey_sequence: str | None = None
    journey_type_code: str | None = None
    train_group_code: str | None = None
    # 경유 이름(AppSegInfo.java:36)은 NCardReservationViewModel.java:154-164 의 Triple 을 거쳐
    # TrainScheduleViewModel.java:2639,2730-2736,2749,2831 에서 입력에 복사됩니다. 대상 필드: AssignScheduleIn.java:41 의
    # stlbDturDvNm1. 라이브러리에서는 SeatAssignmentScheduleRequest.standing_detour_division_name 이 같은 폼 키로 나갑니다.
    #: 경유 구분 이름(``stlbDturDvNm``)입니다. 앱은 N카드 구간으로 좌석배정 열차를 조회할 때 이 값을
    #: ``SeatAssignmentScheduleRequest.standing_detour_division_name``과 같은 입력 필드로 보냅니다.
    detour_division_name: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DiscountCardOnTicket:
    """승차권 상세에 포함된 N카드와 적용 구간을 담습니다."""

    # N카드 적용 구간은 상세 DTO에 따르며 코드 평문·실서버 검증 못 함입니다(DiscountCardInfo.java:27-32; TicketDetailOut.java:49,438).
    # h_dcnt_crd_no: DiscountCardInfo.java:113 의 @SerialName.
    #: N카드 번호(``h_dcnt_crd_no``)입니다.
    card_no: str | None = None
    # 실서버 검증 못 함. 기간연장 플래그는 DiscountCardInfo.java:30,117에 선언됩니다. 앱은 이 값을 비교해 연장 버튼에 전달합니다
    # (NCardTicketSectionKt.smali:7821-7843).
    #: 기간 연장 가능 여부 플래그(``h_dcnt_crd_trm_extn_psb_flg``)입니다.
    term_extension_possible_flag: str | None = None
    sections: tuple[DiscountCardSection, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class KorailPointSummaryResponse(BaseKorailResponse):
    """계정의 포인트·쿠폰·복지 자격 요약을 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 소셜 연동 플래그 네
    개(``naver_linked_flag``, ``kakao_linked_flag``, ``google_linked_flag``, ``apple_linked_flag``)가 각각 어느 서비스에
    대응하는지도 확인하지 못했으므로, 필드 이름의 서비스 대응을 확정된 것으로 보지 마세요."""

    # 앱 근거: MyXPointViewOut.java:27-74. 별칭 없는 키는 속성명에 따른 추정입니다.
    korail_point: str | None = None
    #: 서버가 알려 준 할인쿠폰 개수(``h_disc_coup_cnt``)입니다. ``get_discount_coupons`` 결과의 개수와 항상 같다는 보장은 없습니다.
    discount_coupon_count: str | None = None
    delay_discount_count: str | None = None
    disability_flag: str | None = None
    welfare_discount_class_name: str | None = None
    welfare_discount_class_code: str | None = None
    customer_lead_flag_name: str | None = None
    phone_verified_flag: str | None = None
    email_verified_flag: str | None = None
    contact_channel_content: str | None = None
    # 소셜 연동 플래그의 서비스별 순서는 7.0.6 에서 미확인입니다. 소비 값이 보호된 LoginMethodApiData.java:18-21 을 거치므로 Python
    # 필드명을 확정된 매핑으로 신뢰하지 않습니다.
    #: 네이버 연동 여부로 추정하는 플래그(``h_logn_tp_cd1``)입니다.
    naver_linked_flag: str | None = None
    #: 카카오 연동 여부로 추정하는 플래그(``h_logn_tp_cd2``)입니다.
    kakao_linked_flag: str | None = None
    #: 구글 연동 여부로 추정하는 플래그(``h_logn_tp_cd4``)입니다.
    google_linked_flag: str | None = None
    #: 애플 연동 여부로 추정하는 플래그(``h_logn_tp_cd5``)입니다.
    apple_linked_flag: str | None = None
    # ``h_cust_lead_flg``(``MyXPointViewOut.java:43``) — 보조견 등록 플래그 그 자체.
    customer_lead_flag: str | None = None
    #: 장애 유형 코드(``h_hdcp_tp_cd``)입니다. 장애 유형은 ``disability_flag``가 아니라 이 필드와 ``disability_type_name``에
    #: 있습니다.
    disability_type_code: str | None = None
    #: 장애 유형 이름(``h_hdcp_tp_cd_nm``)입니다.
    disability_type_name: str | None = None


@dataclass(frozen=True)
class MileageHistoryEntry:
    """마일리지 적립 또는 사용 내역 한 행을 담습니다."""

    # AmtSpecOutSpecInfo.java:29-35 가 선언하는 것이 정확히 아래 일곱 필드입니다. 라이브에서 3페이지 14행 전부가 이 일곱 키를
    # 문자열로 싣고 그 밖의 키는 없었습니다.
    departure_date: str | None = None
    point_division_name: str | None = None
    accrual_division_name: str | None = None
    receipt_division_name: str | None = None
    point_amount: str | None = None
    saved_point_value: str | None = None
    settlement_amount: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """마일리지 내역 한 페이지와 적립·사용 합계를 담습니다.

    응답에 따로 있는 합계 필드는 서로 합치지 않고 각각 담습니다."""

    # 앱 근거: AmtSpecOut.java:29-39,199-247. pgCnt 는 AmtSpecOut.java:32.
    #: 전체 페이지 수(``pgCnt``)입니다.
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
    """N카드를 사용한 여행 내역 한 행을 담습니다.

    발매 정보(``sale_date``, ``sale_sequence``, ``sale_window_no``)에는 반환 비밀번호가 없으므로 반환 식별자로 바로 쓸 수
    없습니다."""

    # 채워진 응답은 실서버 검증 못 함입니다(NCardHistoryInfo.java:22,224).
    passenger_name: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    run_date: str | None = None
    # 앱은 보호된 1바이트 리터럴과 비교합니다 (NCardHistoryScreenKt.java:301); 그 평문은 추정하지 않습니다.
    #: 추가 사용자 여부 플래그(``apdUsrFlg``)입니다. 값의 의미는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    additional_user_flag: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # saleDt/saleSqno/saleWctNo — 이 사용 건의 바탕이 된 발매 일자·일련번호·창구번호(NCardHistoryInfo.java:224).
    #: 이 사용 건의 발매 일자(``saleDt``)입니다.
    sale_date: str | None = None
    #: 발매 일련번호(``saleSqno``)입니다.
    sale_sequence: str | None = None
    #: 발매 창구번호(``saleWctNo``)입니다.
    sale_window_no: str | None = None


@dataclass(frozen=True)
class DiscountCardUsageListResponse(BaseKorailResponse):
    """N카드 한 장의 사용 내역 목록을 담습니다.

    응답에는 사용 내역 목록(``tkUseList``)만 있으므로 요약 필드는 없습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. NCardHistoryOut.java:27,82 가 싣는 것은
    # @SerialName("tkUseList") 하나뿐이라, 전송에 없는 요약 필드를 이 모델도 만들어 붙이지 않습니다.
    items: tuple[DiscountCardUsage, ...] = ()


@dataclass(frozen=True)
class DiscountCardScheduleTrain:
    """N카드로 이용 가능한 열차 한 편을 담습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 사용 가능 열차(NCardScheduleItem.java:30-49).
    train_no: str | None = None
    train_group_code: str | None = None
    run_date: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_station_order: str | None = None
    arrival_station_order: str | None = None
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DiscountCardScheduleResponse(BaseKorailResponse):
    """N카드로 이용 가능한 열차 목록을 담습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 일정(NetworkApi.java:339-341,
    # NCardScheduleOut.java:27-28). fllwPgExt 는 ScdlQryOut 필드이며 NCardScheduleOut 은 trnScdlList 만 선언합니다.
    #: 다음 페이지 여부입니다. 라이브러리가 값을 채우지 않으므로 항상 ``None``입니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    # @SerialName 이 없어 와이어 철자는 보호됨 이며 코틀린 필드명을 추정해 사용합니다(CustTripInfo.java:48).
    #: 상품 번호입니다. 추정한 응답 키(``gdNo``)로 읽으며, 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    goods_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MaasServiceDetailListResponse(BaseKorailResponse):
    """신청한 부가서비스 목록을 담습니다."""

    details: tuple[MaasServiceDetail, ...] = ()


@dataclass(frozen=True)
class MaasCancelFeeResponse(BaseKorailResponse):
    """부가서비스 환불 수수료 응답을 담습니다. 이 요청을 보내는 공개 메서드는 없습니다."""

    # 지원하지 않는 부가서비스 환불 수수료 응답 구조를 기록합니다(_maas_unsupported.get_maas_cancel_fee). 앱은 "환불수수료 N원"
    # 확인창에 보여 준 뒤 그 값으로 환불을 요청합니다(MyTicketDetailViewModel.java:840-860,1922).
    cancel_fee: str | None = None


@dataclass(frozen=True)
class TripChangeDateResponse(BaseKorailResponse):
    """승차권을 변경할 수 있는 날짜 목록을 담습니다.

    ``trip_change_dates``는 응답의 ``tripChgDates`` 목록입니다. 목록이 없거나 ``null`` 원소가 있으면 ``KorailProtocolError``가
    발생합니다."""

    # 앱 근거: NetworkApi.java:238; TipChgDateInquiryOut.java:28-30. tripChgDate(단수)는 요청 DTO(TipChgDateInquiryIn.java:29)의
    # 필드입니다 — 응답은 복수형 tripChgDates(List<String>)만 선언하므로, 여기서는 단수형을 읽지 않습니다.
    last_run_date: str | None = None
    trip_change_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommuterPassengerOption:
    """정기권 승객 종류의 인원·연령 범위를 담습니다."""

    # 앱 근거: Psg.java:28-33.
    commuter_usage_age_code: str | None = None
    common_code_name: str | None = None
    #: 최소 연령(``custAgeFrom``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    customer_age_from: int | None = 0
    #: 최대 연령(``custAgeTo``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    customer_age_to: int | None = 0
    #: 최소 인원(``psgPrnbFrom``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    passenger_count_from: int | None = 0
    #: 최대 인원(``psgPrnbTo``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    passenger_count_to: int | None = 0
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class CommuterInfoResponse(BaseKorailResponse):
    """정기권 예매 단계별 조건·승객·원표 정보를 담습니다."""

    additional_service_goods_flag: str | None = None
    companion_flag: str | None = None
    commuter_kind_code: str | None = None
    # 요청의 승객별 cmtrUtlAgeCd 목록과 응답의 최상위 스칼라는 동일한 에코로 간주하지 않습니다 (CommutationInfoIn.java:31,
    # PassConditionViewModel.java:633,653). 상품 0046 은 E05→E06/E06→E05, 단일 행 상품은 ERR000100 을 관측했습니다.
    #: 정기권 이용 연령 코드(``cmtrUtlAgeCd``)입니다. 요청에 넣은 승객별 연령 코드와 다른 값이 올 수 있으므로, 요청 값이 그대로
    #: 돌아온다고 보지 마세요.
    commuter_usage_age_code: str | None = None
    menu_id: str | None = None
    popup_message: str | None = None
    promotion_message: str | None = None
    promotion_url: str | None = None
    seat_attribute_code: str | None = None
    #: 선택할 수 있는 최소 인원(``avlPrnbFrom``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    available_passenger_count_from: int | None = 0
    #: 선택할 수 있는 최대 인원(``avlPrnbTo``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    available_passenger_count_to: int | None = 0
    passenger_options: tuple[CommuterPassengerOption, ...] = ()


@dataclass(frozen=True)
class PriceFare:
    """열차 한 구간의 운임 정보를 담습니다."""

    journey_sequence: str | None = None
    room_class_name: str | None = None
    # 앱 운임 표의 "요금" 칸(TrainOpInfoScreenKt.java:2123).
    #: 요금(``rcvdFare``)입니다. 특실 추가 요금 등이 들어갑니다.
    received_fare: str | None = None
    # 앱 운임 표의 "운임" 칸(TrainOpInfoScreenKt.java:2089).
    #: 운임(``rcvdPrc``)입니다. 쉼표와 "원"이 붙은 표시 문자열입니다(예: ``"21,600원"``).
    received_price: str | None = None
    # 앱 운임 표의 "합계" 칸(TrainOpInfoScreenKt.java:2158).
    #: 합계 금액(``sumAmt``)입니다.
    total_amount: str | None = None
    train_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PriceFareQuoteResponse(BaseKorailResponse):
    """예매 전 운임 조회 결과를 담습니다."""

    fares: tuple[PriceFare, ...] = ()


@dataclass(frozen=True, kw_only=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    """N카드 2인 승차권의 전달 수령자 후보를 담습니다.

    네 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다.
    acceptance_customer_management_no: str
    acceptance_customer_name: str
    acceptance_customer_phone: str
    member_card_no: str


@dataclass(frozen=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    """PNR 기준 중복 예약 확인 결과를 담습니다."""

    # rsvCnt — TicketDupCheckOut.java:28 의 선언은 String 이고 이 DTO 는 kotlinx 이므로 문자열로 읽습니다("0007" 은 그대로).
    # 서버가 이 값을 JSON 정수로 보낸 적이 있는지는 확인하지 않았습니다.
    #: 예약 건수(``rsvCnt``)입니다. ``"0007"``처럼 서버가 보낸 문자열을 그대로 담습니다.
    reservation_count: str | None = None


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceSeat:
    """대리수령 내역의 좌석 한 자리를 담습니다."""

    passenger_type_division_name: str
    room_class_code: str
    room_class_name: str
    car_no: int
    seat_no: str
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceJourney:
    """대리수령 내역의 여정과 좌석 목록을 담습니다."""

    acceptance_customer_name: str
    acceptance_customer_phone: str
    journey_type_code: str
    member_division_name: str
    acceptance_kind_name: str
    pbp_reservation_no: str
    registered_date: str
    withdrawal_possible_flag: str
    seats: tuple[PbpAcceptanceSeat, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    member_card_no: str


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceTicket:
    """대리수령 내역의 승차권과 여정 목록을 담습니다."""

    pnr_no: str
    sale_date: str
    sale_sequence: str
    sale_window_no: str
    return_password: str
    journeys: tuple[PbpAcceptanceJourney, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    """승차권별 대리수령 내역 목록을 담습니다.

    승차권·여정·좌석의 모든 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다."""

    tickets: tuple[PbpAcceptanceTicket, ...] = ()


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """자율 좌석변경이 가능한 승차역과 잔여석을 담습니다.

    응답의 도착역 코드·이름과 도착역 편성·운행 순서는 읽지 않습니다. 원본은 ``raw``에 남습니다."""

    # 앱 근거: ChgStnInfo.java:21-35; SeatAvailabilityOut.java:32. DTO 의 도착역 코드·이름·편성/운행순서 4개 필드는 이 모델에서
    # 읽지 않습니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeReason:
    """자율 좌석변경 시 선택할 변경 사유를 담습니다.

    필드는 추정한 응답 키(``qryCode``, ``qryOrdr``, ``frcSaleRsnCont``)로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아
    확인하지 못했습니다."""

    # 앱 근거: ChgRsnInfo.java:21-24; SeatAvailabilityOut.java:31. serializer descriptor 의 이름이 보호돼 있어
    # (ChgRsnInfo$$serializer.java:34-36) 전송 키는 속성명에 따른 추정입니다.
    query_code: str | None = None
    query_order: str | None = None
    reason_text: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """자율 좌석변경의 대상 역·사유·열차 정보를 담습니다."""

    # 앱 근거: NetworkApi.java:806-808; SeatAvailabilityOut.java:28-42,68.
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
    """변경 기준인 원표의 좌석 정보를 담습니다."""

    # 앱 근거: SeatInfo.java:25-51; JrnyInfo.java:58. 대리수령용 Seat.java:27-36 과는 이름과 구조가 다른 타입입니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicketJourney:
    """변경 기준인 원표의 구간과 좌석 목록을 담습니다."""

    # 앱 근거: OrgTk.java:38; JrnyInfo.java:29-63. 대리수령용 Jrny.java:29-38 과 다릅니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicket:
    """변경 기준인 원표의 식별자·상태·여정을 담습니다.

    필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. ``original_*`` 필드는
    요청한 승차권의 반환 식별자가 그대로 돌아온 값이며 ``repr``에서도 가리지 않습니다."""

    # 앱 근거: OrgTk.java:28-52; OgTicketInquiryOut.java:27. 전송 키는 속성명에 따른 추정입니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicketInquiryResponse(BaseKorailResponse):
    """변경 기준인 원표 목록을 담습니다."""

    # 앱 근거: NetworkApi.java:234-236; OgTicketInquiryOut.java:26-27,54.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    """최근 승차권 전달 수령자 목록을 담습니다."""

    changed_acceptance_reservation_no: str | None = None
    recipients: tuple[RecentDeliveryRecipient, ...] = ()


@dataclass(frozen=True)
class ReservationSeatDetail:
    """예약 상세의 좌석·승객·운임 정보를 담습니다."""

    # ReservationOutSeatInfo.java:33,81. h_psg_tp_dv_nm은 DTO에는 없지만 앱 내장 표본(BasketTicketDataKt.java:44)과 실서버 8/8행에서
    # 확인했습니다. 재계산 입력의 기존 종류·객실·할인 코드는 같은 모양의 홀드 좌석 행을 사용하며(PriceRecalculationRequest.for_hold)
    # 다른 응답에서도 같은 필드가 오는지는 검증 못 함입니다.
    car_no: str | None = None
    seat_no: str | None = None
    room_class_code: str | None = None
    room_class_name: str | None = None
    passenger_type_code: str | None = None
    # 홀드 정산액 계산: mutation_parsers._received_amount (좌석 합을 먼저 구하고 선언 총액과 대조, 좌석 행이 없으면 선언 총액).
    #: 좌석별 받을 금액(``h_rcvd_amt``)입니다. 예약 메서드가 돌려주는 ``ReservationHoldResponse``의 ``received_amount``는 홀드
    #: 응답에 좌석 행이 있으면 그 행들의 이 값을 합한 금액입니다.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    total_discount_amount: str | None = None
    seat_group_name: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # 위 클래스 주석의 관측 한계를 따릅니다.
    #: 승객 유형 이름(``h_psg_tp_dv_nm``)입니다. 응답에 따라 없을 수 있으며, 없으면 ``None``입니다.
    passenger_type_name: str | None = None


@dataclass(frozen=True)
class ReservationDetailJourney:
    """홀드(결제 전 예약)의 여정 한 개와 좌석 상세를 담습니다."""

    journey_sequence: str | None = None
    journey_type_code: str | None = None
    reservation_change_no: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    arrival_date: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    train_no: str | None = None
    train_class_name: str | None = None
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR로 다시 조회한 예약의 여정·좌석·정산액을 담습니다."""

    pnr_no: str | None = None
    window_no: str | None = None
    journey_count: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    payment_flag: str | None = None
    journeys: tuple[ReservationDetailJourney, ...] = ()
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
    """환불 전 예상 환불액과 수수료를 담습니다.

    ``get_refund_commission``이 돌려줍니다. 환불하려면 이 응답을 ``refund``의 ``commission``에 넘기세요. ``refund``는
    ``commission``이 이 타입이 아니면(``None`` 포함) 요청을 보내기 전에 ``KorailProtocolError``를 발생시킵니다."""

    # 앱 근거: NetworkApi.java:598-600. 키 근거: RefundCommissionOut.java:35-41,62,140-164.
    refund_amount: str | None = None
    refund_fee: str | None = None
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class RefundTicketDetailResponse(BaseKorailResponse):
    """환불 대상 승차권의 식별자·여정·운임 상세를 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 앱 근거: TicketDetailOut.java:38,117. 별칭 없는 전송 키는 추정입니다.
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
    # retPsbFlg는 환불 성공 보장이 아닙니다(TicketDetailOut.java:71). 실서버 관측: 상세 40응답은 Y였지만 수수료 조회는 승차일 경과
    # 5건 WRT200022·이미 반환 2건 WRT200399였고, 목록 이력 143장은 N이었습니다. 앱은 사용 여부도 검사합니다
    # (NormalTicketSectionKt.java:951).
    #: 환불 가능 여부 플래그(``retPsbFlg``)입니다. ``"Y"``여도 환불할 수 있다는 보장은 없으므로 ``get_refund_commission``의 결과로
    #: 확인하세요.
    refund_possible_flag: str | None = None
    return_flag: str | None = None
    total_fare_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    train_running_flag: str | None = None
    # 탑승자 이름·생년월일 요약이며 동승자(h_compa_nm/h_compa_brth)나 psgNmList 와 별개입니다(TicketDetailOut.java:410,418).
    #: 탑승자 이름(``h_abrd_ps_nm``)입니다. 동승자 이름(``companion_name``)이나 ``passenger_names`` 목록과는 다른 필드입니다.
    passenger_name: str | None = None
    #: 탑승자 생년월일(``s_brth``)입니다.
    passenger_birth_date: str | None = None
    #: 동승자 이름(``h_compa_nm``)입니다.
    companion_name: str | None = None
    #: 동승자 생년월일(``h_compa_brth``)입니다.
    companion_birth_date: str | None = None
    # 상세 40응답(20승차권×2모드)에는 후보 키가 없었으며 목록 Y 6건도 같았습니다. 목록 키는 MyTicketListOutTicket.java:92,300, 상세
    # 필드·setter는 TicketDetailOut.java:65,1936입니다.
    #: 대리수령 대상 여부 플래그입니다. 응답에 ``pbpAcepTgtFlg`` 키가 있을 때만 채우며 보통은 ``None``입니다. 앱처럼 환불하려면
    #: ``get_ticket_list`` 승차권의 ``pbp_acceptance_target_flag``를 ``refund``에 넘기세요.
    pbp_acceptance_target_flag: str | None = None
    delay_flag: str | None = None
    delay_ticket_flag: str | None = None
    additional_service_flag: str | None = None
    additional_service_cancel: str | None = None
    # h_qrcode: TicketDetailOut.java:478.
    #: 이 승차권의 QR 코드(``h_qrcode``)입니다.
    qr_code: str | None = None
    # psgNmList: @SerialName 이 없어 와이어 철자는 보호됨, 코틀린 필드명을 추정해 사용합니다. 각 원소는 아직 행 단위로 모델링하지
    # 않고 원본 그대로 노출합니다.
    #: 승객 이름 목록(``psgNmList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    passenger_names: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    # seatTicketList — List<SeatAssignInfo>, 보호됨.
    #: 좌석 배정 목록(``seatTicketList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    seat_tickets: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    # limousine — 단일 객체, 보호됨.
    #: 연계된 리무진 예약(``limousine``)입니다. 추정한 응답 키로 읽은 원본 매핑이며, 없으면 ``None``입니다.
    limousine: Mapping[str, object] | None = field(default=None, compare=False)
    # dtlList — List<DelayInfo>, 보호됨.
    #: 지연 정보 목록(``dtlList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    delay_details: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    journeys: tuple[RefundTicketJourney, ...] = ()
    #: N카드 정보(``dcnt_crd_info``)입니다. 응답에 없으면 ``None``이며, N카드 승차권이 아니면 보통 ``None``입니다.
    discount_card: DiscountCardOnTicket | None = None


@dataclass(frozen=True)
class DelayCertificateRow:
    """지연확인증 한 행을 담습니다.

    ``run_date``를 뺀 일곱 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다. 앱은
    ``delay_arrival_flag``가 특정 값인 행만 보여 주지만, 라이브러리는 거르지 않고 모든 행을 돌려줍니다. 앱이 고르는 값은 앱 내부
    값이 공개돼 있지 않아 확인하지 못했습니다."""

    # DelayCertificate.java:57-60 의 마스크는 여덟 키 모두 필수로 둡니다. 앱은 dlayArvFlg 가 보호된 1글자 값과 같은 행만 보여
    # 주므로(DelayCertificateViewModel.java:139-150) 이 라이브러리는 거르지 않고 모두 돌려줍니다.
    run_day: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    arrival_station_name: str
    delay_arrival_flag: str
    delay_minutes: str
    # runDt 는 마스크상 필수이지만 실서버 응답에는 없었습니다.
    #: 운행일(``runDt``)입니다. 응답에 없으면 ``None``이며, 운행일은 ``run_day``에도 있습니다(예: 요일이 붙은 날짜).
    run_date: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DelayCertificateResponse(BaseKorailResponse):
    """지연확인증의 행을 담습니다.

    응답에 목록(``dlayList``)이 없거나 ``null``이면 ``delays``는 빈 튜플입니다."""

    # dlay.athnIsu.do. dlayList 는 선택·nullable 입니다(DelayCertificateOut.java:53-59).
    delays: tuple[DelayCertificateRow, ...] = ()


@dataclass(frozen=True)
class DelayReturnReceiptResponse(BaseKorailResponse):
    """지연료 반환 영수증을 담습니다.

    세 필드 모두 응답에 없으면 ``None``입니다."""

    # 세 필드 모두 선택입니다(DelayReturnReceiptOut.java:53-69).
    return_date: str | None = None
    payment_method_name: str | None = None
    return_amount: str | None = None


@dataclass(frozen=True)
class TravelProduct:
    """여행상품 검색 결과의 상품 한 개를 담습니다.

    열두 필드 모두 응답에 없으면 ``None``입니다. ``goods_no``는 ``get_product_detail``의 예약 번호가 아닙니다."""

    # 열두 필드 모두 선택입니다(TravelProductItem.java:61-105). 앱은 goods_no·name·info_url·representative_fare 만
    # 씁니다(TravelSearchViewModel.java:1070-1074).
    goods_no: str | None = None
    name: str | None = None
    area_code: str | None = None
    area_name: str | None = None
    event_start_date: str | None = None
    event_end_date: str | None = None
    company_name: str | None = None
    info_url: str | None = None
    representative_fare: str | None = None
    description: str | None = None
    standard_clause_1: str | None = None
    standard_clause_2: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TravelProductSearchResponse(BaseKorailResponse):
    """여행상품 검색 결과를 담습니다.

    응답의 목록 객체(``lst``)가 없거나 ``null``이면 빈 결과입니다. 이 요청을 보내는 공개 메서드는 없습니다."""

    # 여행상품 검색(/ebizcom/gdLstDtl.do, _travel_search_unsupported). lst 객체는 선택·nullable 이고
    # (TravelSearchProductOut.java:48-55) 그 안의 gdList·qryCnt·pgCnt 도 모두 선택입니다(TravelProductList.java:56-68). 앱은 현재 쪽
    # 번호가 page_count 이상이면 더 부르지 않습니다.
    products: tuple[TravelProduct, ...] = ()
    query_count: str | None = None
    page_count: str | None = None


@dataclass(frozen=True)
class SelfCheckInSeat:
    """셀프 체크인할 수 있는 좌석 한 행을 담습니다.

    열여섯 필드 모두 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다. 등록할 때는 이 행을
    ``register_self_checkin``의 ``seat``로 넘깁니다."""

    # 열여섯 키 모두 필수입니다(ConsList.java:63-65,86-101). 앱은 첫 행을 등록에
    # 넘깁니다(SelfCheckInInfoViewModel.java:151-153,224-225).
    pnr_no: str
    journey_sequence: str
    assignment_sequence: str
    run_date: str
    train_no: str
    departure_construction_order: str
    departure_station_code: str
    arrival_construction_order: str
    arrival_station_code: str
    ticket_kind_code: str
    train_group_code: str
    car_no: str
    seat_no: str
    departure_datetime: str
    arrival_datetime: str
    cps_no: str
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfCheckInSeatCheckResponse(BaseKorailResponse):
    """셀프 체크인 좌석 확인 결과를 담습니다.

    응답에 ``consList`` 키가 없으면 ``KorailProtocolError``가 발생하고, 값이 ``null``이면 ``seats``는 빈 튜플입니다."""

    # checkin.psbFlg.do. consList 는 필수·nullable 입니다(SelfCheckInPossibleOut.java:50-55). 앱은 행이 없으면 아무것도 하지
    # 않습니다.
    seats: tuple[SelfCheckInSeat, ...] = ()


@dataclass(frozen=True)
class SelfCheckInInfoResponse(BaseKorailResponse):
    """셀프 체크인한 좌석 정보를 담습니다.

    열 필드의 키가 응답에 모두 있어야 하며, 하나라도 없으면 ``KorailProtocolError``가 발생합니다. 값이 ``null``이면 해당 필드는
    ``None``입니다."""

    # 열 키 모두 필수·nullable 입니다(SelfCheckInInfoOut.java:56-59,146).
    pnr_no: str | None = None
    train_no: str | None = None
    departure_station_name: str | None = None
    departure_time: str | None = None
    arrival_station_name: str | None = None
    arrival_time: str | None = None
    car_no: str | None = None
    seat_no: str | None = None
    train_class_name: str | None = None
    checkin_division_code: str | None = None
