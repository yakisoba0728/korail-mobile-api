# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""읽기 전용 조회 응답 타입. 열차·좌석 타입은 models, 전송 키 대응은 read_parsers 를 참고하십시오.

frozen 데이터클래스라도 raw 내부는 불변이 아니며 모든 하위 값 객체가 raw 를 갖는 것은 아닙니다. 필드·repr·raw 는 마스킹하지 않으므로 개인정보·반환 비밀번호의 기록·노출은 호출자가
관리해야 합니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse


@dataclass(frozen=True)
class TicketListTrain:
    """승차권 한 장의 구간 한 줄(``jrn_info``, TicketListTrainInfo.java:72 의 String 21개). 선택값으로 관대하게 읽습니다.

    2026-09-24 라이브 이력 139행: 21개 키가 모두 있었고 ``h_srcar_no`` 는 String 선언과 달리 모두 JSON 정수였습니다(문자열로 받습니다).
    DTO 밖의 ``h_psrm_cl_cd``·``h_seat_no_end``·``h_sgr_nm_1``/``_2``·``srtStnFlg`` 도 왔으며 raw 에 남습니다."""

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
    pnr_no: str | None = None
    sale_window_no: str | None = None
    sale_date: str | None = None
    return_sale_date: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    ticket_status_code: str | None = None
    #: ``h_tk_knd_cd``/``h_tk_knd_nm`` — 승차권 종류(``'72'``/``'스마트티켓'``). 예약 행이 아니라 승차권 행에서 읽습니다. 2026-09-22 한 계정
    #: 관측에서 131행 모두에 있었다고 적혀 있으나 캡처가 연결돼 있지 않아 재검산할 수 없습니다(미검증). 관대하게 읽습니다.
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    train_info: tuple[Mapping[str, Any], ...] = field(default=(), compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # raw 의 위치 인자 자리를 유지하려고 추가 필드를 뒤에 둡니다. h_tk_sqno 선언: MyTicketListOutTicket.java:92. 2026-09-22 표본 131행 모두에
    # 있었다는 원래 관측 기록은 캡처가 연결되지 않아 재검증되지 않았습니다.
    ticket_sequence: str | None = None
    #: ``h_tk_stt_nm`` — :attr:`ticket_status_code`(``h_tk_stt_cd``)의 사람이 읽는 짝. 코드만으로는 ``'09'`` 가 "반환"인지 알 수
    #: 없습니다.
    ticket_status_name: str | None = None
    #: 목록 행의 환불 플래그. 2026-09-22 기록: 이력 143장의 목록 값은 N, 같은 승차권의 상세 retPsbFlg 는 Y 였습니다. 둘을 같은 판정으로 취급하지 마십시오. 앱 버튼
    #: 조건은 상세 플래그와 사용 여부 검사입니다(NormalTicketSectionKt.java:951, TicketHelper.java:3173-3199). 비교 리터럴은 보호돼 있습니다.
    return_possible_flag: str | None = None
    #: ``h_use_tno``/``h_noty_use_tno`` — 사용·미통지 사용 거래번호.
    use_transaction_no: str | None = None
    notify_use_transaction_no: str | None = None
    #: PBP 인수 대상. 앱은 목록 값을 상세에 주입합니다(MyTicketBaseViewModel.java:769, MyTicketDetailViewModel.java:1521).
    #: 2026-09-22 상세 40응답에는 두 후보 키가 없었습니다. 같은 날 목록 131행은 N 125/Y 6이라는 기록이 있으나 캡처 미연결로 재검산하지 못했습니다.
    pbp_acceptance_target_flag: str | None = None
    #: :attr:`train_info` 의 행을 :class:`TicketListTrain` 으로 읽은 것. 2026-09-24 이력에서 승차권 132장 중 7장이 두 구간이었습니다.
    trains: tuple[TicketListTrain, ...] = ()


@dataclass(frozen=True)
class TicketListReservation:
    """예약 단위 승차권 목록. MyTicketListOutReservation 의 명시적 키는 ticket_list 이며 나머지는 보호된 serializer 대신 속성명으로 읽는 추정입니다.
    추가 서비스·종류도 raw 에 남습니다."""

    tickets: tuple[TicketListTicket, ...] = ()
    #: 선택 스칼라의 전송 키는 속성명에 따른 추정입니다. 2026-09-22 mode=2 의 예약 128행은 ticket_list 외 키가 없었다는 기록이 있으나 캡처 미연결로 재검산하지
    #: 못했습니다. 누락은 거짓이 아닌 모름(None)입니다. 종류 코드는 TicketListTicket.ticket_kind_code 를 보십시오.
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
    # raw 의 위치 인자 자리를 유지합니다. 선택값의 타입이 어긋나면 해당 값만 비웁니다. addSrvInfo(MyTicketListOutReservation.java:39)는 MaaS 의
    # AddSrvItem 과 같은 타입이라 모델을 공유합니다(MaasDetailOut.java:27, AddSrvItem.java:28-49). 키는 속성명에 따른 추정입니다.
    additional_service: MaasServiceDetail | None = None
    #: ticketKind 는 보호된 enum 이름을 매핑하지 않고 문자열로 둡니다 (MyTicketListOutReservation.java:52,59;
    #: TicketDefine.java:1078-1131). 앱 기본값은 GENERAL(MyTicketListOutReservation.java:133-134)이며, write$Self 는 기본값
    #: 기록 설정 또는 비기본값일 때 인코딩합니다(MyTicketListOutReservation.java:261). 따라서 기본값과 같다는 이유만으로 키가 반드시 생략된다고 할 수 없습니다.
    ticket_kind: str | None = None


@dataclass(frozen=True)
class TicketListResponse(BaseKorailResponse):
    reservations: tuple[TicketListReservation, ...] = ()
    #: ``h_total_cnt`` — 구매이력(``mode="2"``)의 서버측 총건수. 0 을 채운 문자열로 오므로(``'0128'``) 문자열로 둡니다. ``mode="1"`` 과 빈
    #: 응답에는 이 키가 없어 ``None`` 입니다.
    total_count: str | None = None


@dataclass(frozen=True)
class ServiceStatusResponse(BaseKorailResponse):
    pass


@dataclass(frozen=True)
class CartItem:
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
    # CartInfo.java:28-61,281-392 의 문자열 필드를 읽고 중첩 결제 상세 6객체는 raw 에 둡니다: GreenCarPayDetail 12,
    # LotteRentalPayDetail 9, LoyquPayDetail 10, SKRentalCarPayDetail 13, YanoljaDetail 8, ZimCarryDetail 7 =
    # String 59개. 라이브 캡처는 없습니다. skRentalPayDetail 의 타입은 SKRentalCarPayDetail 입니다. raw 뒤에 필드를 두어 위치 인자 호환을 유지하며
    # 잘못된 선택 스칼라는 None 으로 읽습니다(_parsing._optional_scalar_string). h_item_dv_cd 선언: CartInfo.java:38,317; 앱 분기값은
    # 보호됩니다(BasketTicketViewModel.java:4186,4295).
    item_type_code: str | None = None
    #: ``h_add_srv_mrk_ent_id`` — :attr:`provider_name`(``h_add_srv_mrk_ent_nm``, ``CartInfo.java:32``)의 ID
    #: 짝(``CartInfo.java:31``, ``@SerialName`` 289행).
    provider_id: str | None = None
    #: ``h_item_sqno``/``h_jrny_sqno``/``h_jrny_tp_cd`` — 이 행의 항목 일련번호, 여정 일련번호, 여정 구분
    #: 코드(``CartInfo.java:40,41,42``, ``@SerialName`` 325/329/333행). 뒤의 둘은 예약·영수증 쪽에서 쓰는 이름을 그대로 씁니다.
    item_sequence: str | None = None
    journey_sequence: str | None = None
    journey_type_code: str | None = None
    #: ``utlClsDt`` — :attr:`usage_close_time`(``utlClsTm``)의 날짜 짝 (``CartInfo.java:56``,
    #: ``@SerialName`` 377행). 앱도 둘을 이어 붙여 한 일시로 씁니다(``PayTicketContentKt.java:5234``: ``getUtlClsDt()
    #: + getUtlClsTm()``).
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
    items: tuple[CartItem, ...] = ()


@dataclass(frozen=True)
class DepositBank:
    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DepositBankListResponse(BaseKorailResponse):
    items: tuple[DepositBank, ...] = ()


@dataclass(frozen=True)
class DelayDiscountTicket:
    """지연배상 쿠폰 한 장(``DelayCoupon.java:32-55``, 23개 String 필드).

    ``h_use_psb_dt``(사용 가능 기한)는 전 디컴파일에 0건이라 읽지 않습니다."""

    fare: str | None = None
    original_sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    #: ``h_tk_sqno`` — 이 줄이 어느 실물 승차권에 붙었는지를 가리키는 신원 앵커.
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
    """지연할인권 페이지. main_info 는 DTO 밖 서버 추가 블록(DelayDiscountViewOut.java:24,51). 2026-09-22 날짜 입력 8종에서 12키를 관측했지만
    할인권 없는 응답뿐이었습니다. 영 채움·빈 문자열을 보존하려고 페이징 값을 문자열로 둡니다. 선택 정수 헬퍼는 빈 값을 None 으로 처리하므로 예외가 난다는 설명은 맞지 않습니다. 채워진
    응답의 의미는 미확인입니다."""

    items: tuple[DelayDiscountTicket, ...] = ()
    current_page: str | None = None
    total_pages: str | None = None
    total_count: str | None = None
    row_count: str | None = None
    last_page_flag: str | None = None


@dataclass(frozen=True)
class DiscountCoupon:
    guide: str | None = None
    start_date: str | None = None
    expiration_date: str | None = None
    discount_kind_code: str | None = None
    discount_values: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DiscountCouponListResponse(BaseKorailResponse):
    items: tuple[DiscountCoupon, ...] = ()
    current_page: int | None = None
    total_pages: int | None = None
    total_count: str | None = None
    row_count: str | None = None


@dataclass(frozen=True)
class PassOffice:
    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassOpenDate:
    """pass_info 의 세 필드(PassInfo.java:92,96,100,149). open_dates 는 날짜만 모은 편의 목록입니다. 2026-09-22 기록: 같은 입력 두 호출의
    pnr_no 는 달랐고 E05/E06 변경 시 행은 같았습니다. 할당 원리·항상 변화 여부는 미확인입니다. 안정된 식별자로 보관하거나 open_dates 와 재결합하지 마십시오."""

    open_date: str | None = None
    item_sequence: str | None = None
    pnr_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassAvailabilityMainInfo:
    """pass.passInfoList 의 중첩 상태·건수(MainInfo.java:103,107,111,115,172). 2026-09-22 관측 29종은 최상위 h_msg_cd 없이 이 블록에
    IRZ000001/IRZ000005 등을 담았습니다. 중첩 코드를 실패 예외로 승격하지 않습니다. 앱도 isSuccess 이후 pass_info 를 확인합니다
    (PeriodTicketViewModel.java:796-800, PassConditionViewModel.java:904-927). 다른 조건에서도 이것이 유일한 코드라고 보장하지는
    않습니다."""

    message_code: str | None = None
    total_count: str | None = None
    row_count: str | None = None
    selected_page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassAvailabilityResponse(BaseKorailResponse):
    #: ``pass_info[].h_use_open_dt`` 만 모은 편의 목록. 키가 없는 행은 건너뛰므로 :attr:`pass_info` 보다 짧을 수 있습니다 — 세 필드를 전부 쓰려면
    #: :attr:`pass_info` 를 보십시오.
    open_dates: tuple[str, ...] = ()
    ticket_issue_dates: tuple[str, ...] = ()
    offices: tuple[PassOffice, ...] = ()
    pass_info: tuple[PassOpenDate, ...] = ()
    main_info: PassAvailabilityMainInfo | None = None


@dataclass(frozen=True)
class TripMenuContent:
    """여행상품 메뉴. 21개 문자열과 passData 객체입니다(TrGdMenuLtOutCont.java:26-47,72). 2026-09-22 2회 60행은 detailType 누락 54/빈
    값 6으로 유효한 값을 보지 못했습니다. passType 을 검증된 메뉴 종류 코드로 승격하지 마십시오. DTO 속성과 실제 소비 의미는 별개입니다."""

    title: str | None = None
    detail: str | None = None
    detail_type: str | None = None
    active: str | None = None
    agree: str | None = None
    info: str | None = None
    image: str | None = None
    url: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    #: ``cmtrKndCd``(``TrGdMenuLtOutCont.java:26``) — 이 줄이 가리키는 정기권 종류 코드.
    #: :meth:`~korail_mobile_api.client.KorailClient.get_commuter_kind_menu` 의 입력이 바로 이 값입니다. 앱도 같은 식으로 씁니다 —
    #: ``PassConditionViewModel.java:1241`` 이 ``contList`` 를 훑으며 ``getCmtrKndCd()`` 를 목표 코드와 비교합니다.
    #: ``menuType='P'``(자유여행패스) 메뉴에만 옵니다(2026-09-22: 60행 중 6행, ``'0046'``/``'0007'``/``'0049'``).
    commuter_kind_code: str | None = None
    #: ``passType``(``:47``) — 위 6행에서 ``'aPass'``. 7.0.6 에 소비자가 없어 무엇을 뜻하는지는 미확인입니다(클래스 독스트링 참고).
    pass_type: str | None = None
    #: ``passData``(``:45``, ``TrGdMenuLtOutPass.java:29-35``) — 정기권 조회에 필요한 연령·기간 선택지 묶음. 정기권 메뉴/종류 라우트와 구조가
    #: 비슷해 ``_parse_pass_menu_data`` 를 쓰되 역 선택 키는 ``h_seiect_station`` 입니다. ``PassConditionViewModel.java:1244``
    #: 가 이 객체를 꺼내고, 같은 함수의 ``:1247-1248`` 이 ``null`` 이면 ``backAlert`` 로 화면을 되돌립니다.
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class TripMenuItem:
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
    items: tuple[TripMenuItem, ...] = ()
    popup_message: str | None = None


@dataclass(frozen=True)
class ProductReservation:
    product_name: str | None = None
    reservation_status: str | None = None
    payment_deadline: str | None = None
    payment_status: str | None = None
    virtual_reservation_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ProductReservationListResponse(BaseKorailResponse):
    items: tuple[ProductReservation, ...] = ()
    total_count: int | None = None


@dataclass(frozen=True)
class ProductDetailResponse(BaseKorailResponse):
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
    detail_raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReceiptPayment:
    payment_method: str | None = None
    #: h_apv_dt. 계좌·승인·카드·포인트 번호를 포함한 기록 경고는 모듈 설명 참고.
    approval_date: str | None = None
    installment_months: int | None = None
    amount: int | None = None
    account_no: str | None = None
    approval_no: str | None = None
    card_no: str | None = None
    point_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReceiptCashPayment:
    """현금영수증 행(ReceiptInfo.java:37). String 4개·int 금액 1개이며 전송 키는 CashReceiptInfo.java:26-35,52 의 명시적 @SerialName
    입니다."""

    #: h_apv_mtd_nm — 승인방법 라벨. 인증도메인 인식번호·현금영수증 승인번호도 마스킹하지 않습니다.
    approval_method_name: str | None = None
    authentication_domain_recognition_no: str | None = None
    cash_receipt_approval_no: str | None = None
    cash_receipt_transaction_division_code: str | None = None
    total_approved_amount: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class TicketReceipt:
    travel_date: str | None = None
    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    commuter_kind_code: str | None = None
    journey_type_code: str | None = None
    #: ``h_prt_disc_knd_nm``/``h_prt_disc_knd_cd`` — 영수증에 인쇄된 할인 종류의 이름·코드.
    printed_discount_name: str | None = None
    printed_discount_kind_code: str | None = None
    print_type: str | None = None
    seat_class_name: str | None = None
    ticket_kind_code: str | None = None
    #: ``h_tk_knd_nm`` — 승차권 종류의 사람이 읽는 이름.
    ticket_kind_name: str | None = None
    ticket_status_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    #: ``h_trn_gp_cd`` — 열차 그룹 코드(KTX/새마을 등).
    train_group_code: str | None = None
    train_no: str | None = None
    passenger_counts: tuple[int | None, int | None, int | None] = (
        None,
        None,
        None,
    )
    received_amount: int | None = None
    card_refund_amount: int | None = None
    refund_fee: int | None = None
    refund_received_amount: int | None = None
    point_refund_amount: int | None = None
    payments: tuple[ReceiptPayment, ...] = ()
    #: ``cash_rcet_info`` — 현금영수증 줄들.
    cash_receipts: tuple[ReceiptCashPayment, ...] = ()
    member_card_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class TicketReceiptResponse(BaseKorailResponse):
    items: tuple[TicketReceipt, ...] = ()


@dataclass(frozen=True)
class ReservationHistoryTrain:
    """예약 이력 열차. 평문 @SerialName 37개 외 보호된 슬롯이 있습니다 (ReservationViewOutTrainInfo.java:94,
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
    # 새 필드는 ``raw`` 뒤에 덧붙입니다(위치 인자 의미 보존). ``h_ntisu_lmt_dt``/``h_ntisu_lmt_tm`` — 이 홀드의 결제 기한 날짜·시각.
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    #: ``h_payment_msg`` — 그 기한을 사람이 읽는 문구로 옮긴 것.
    payment_message: str | None = None
    #: ``h_ntisu_psb_dt`` — 결제를 시작할 수 있는 날짜(기한의 반대쪽 끝).
    payment_possible_date: str | None = None
    #: ``h_pre_stl_tgt_flg`` — 선결제 대상 여부.
    prepayment_target_flag: str | None = None
    #: ``h_jrny_sqno`` — 이 행이 속한 여정의 순번. 같은 이름을 쓰는 형제 :class:`ReservationHistoryPassenger` 쪽과 여정을 맞출 때 필요합니다.
    journey_sequence: str | None = None


@dataclass(frozen=True)
class ReservationHistoryTicket:
    """예약 이력 여정의 ``ReservationOut.tkList`` 행 하나(``ReservationOutTK.java``).

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
    """예약 이력 여정의 ``ReservationOut.orgTkList`` 행 하나(``ReservationOrgTk.java``)."""

    sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    #: ``ogtkRetPwd`` — 원표 반환 비밀번호. 그 자체로 반환 권한이라 민감합니다.
    return_password: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryPassenger:
    """예약 이력 여정의 ``ReservationOut.psgInfos.psgInfo`` 행 하나(``ReservationOutPsgInfo.java``)."""

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
    """예약 이력의 ReservationOut 중첩(ReservationViewOutJrnyInfo.java:55). 전송 키 reservationOut 은 보호된 serializer 대신
    속성명을 사용한 추정입니다."""

    pnr_no: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 이 PNR 의 실제 결제(정산) 금액.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    tickets: tuple[ReservationHistoryTicket, ...] = ()
    original_tickets: tuple[ReservationHistoryOriginalTicket, ...] = ()
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryJourney:
    """예약 이력의 여정 하나(``ReservationViewOutJrnyInfo.java``).

    ``srv_infos``/``acmp_infos`` 는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다 — 원본 그대로라도 여정 단위로 닿을 수 있게 하기 위해서입니다."""

    trains: tuple[ReservationHistoryTrain, ...] = ()
    service_infos: tuple[Mapping[str, Any], ...] = field(default=(), compare=False)
    accompanying_infos: tuple[Mapping[str, Any], ...] = field(default=(), compare=False)
    reservation: ReservationHistoryReservation | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class ReservationHistoryResponse(BaseKorailResponse):
    """``ReservationViewOut`` — 예약 이력(``research.reservationView.do``).

    최상위 신원 필드(``h_rsv_ps_nm``/``h_tel_no`` 등)와 :attr:`journeys` 는 ``ReservationViewOut.java:64`` 를 따릅니다."""

    #: ``h_rsv_ps_nm`` — 예약자 성명.
    reservation_passenger_name: str | None = None
    #: ``h_tel_no`` — 예약자 전화번호.
    phone_no: str | None = None
    reservation_limit_flag: str | None = None
    seatmap_flag: str | None = None
    process_flag: str | None = None
    follow_flag: str | None = None
    #: ``h_cust_no`` — 고객관리번호. 신원 식별자라 민감.
    customer_no: str | None = None
    customer_division_code: str | None = None
    customer_sort_code: str | None = None
    customer_class_code: str | None = None
    journey_count: str | None = None
    #: ``guide_infos.guide_info`` — 단일 안내 문구.
    guide_info: str | None = None
    journeys: tuple[ReservationHistoryJourney, ...] = ()
    #: 모든 여정의 열차 행을 평탄화한 목록입니다. 개별 여정의 돈·PNR 층에 닿으려면 :attr:`journeys` 를 쓰십시오.
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        return self.items


@dataclass(frozen=True)
class FreeSeatCarResponse(BaseKorailResponse):
    title: str | None = None
    car_no: str | None = None
    content: str | None = None


@dataclass(frozen=True)
class GuideSeatConditionResponse(BaseKorailResponse):
    """도우미석 안내. 앱처럼 FAIL 도 코드와 무관하게 응답으로 돌려주며(P058·코드 없는 FAIL 은 예외) h_msg_txt 에 안내가 있습니다. 자체 필드 timeStamp 는 long
    선언(GuideSeatCndOut.java:29,50)이지만 보호된 serializer 이름을 확인하지 못해 전송 키는 속성명에 따른 추정입니다."""

    time_stamp: int | None = None


@dataclass(frozen=True)
class TrainScheduleItem:
    """좌석배정·병합 조회의 열차 모델 상위집합. 각 DTO 는 다르므로 read_parsers 의 라우트별 필드 맵으로 채웁니다. 한쪽에 없는 필드는 None 이며 맵을 하나로 합치면 안
    됩니다."""

    train_no: str | None = None
    #: ``h_trn_no_qb`` — 병합예약 조회 전용 열차번호(``MergeSeatsCOutTrnInfo``).
    train_no_qb: str | None = None
    #: ``h_trn_seq`` — 열차 순번(``MergeSeatsCOutTrnInfo``).
    train_sequence: str | None = None
    train_group_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    run_date: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    #: ``h_dpt_tm_qb``(``MergeSeatsCOutTrnInfo``).
    departure_time_qb: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    #: ``h_arv_tm_qb``(``MergeSeatsCOutTrnInfo``).
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
    #: ``h_jrny_rsv_cd``/``h_jrny_rsv_nm``(``MergeSeatsCOutTrnInfo``).
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
    #: ``shtmStndOpFlg`` — 셔틀 입석 오픈 여부(``MergeSeatsCOutTrnInfo``).
    shuttle_standing_open_flag: str | None = None
    #: ``restStndNum`` — 잔여 입석수(``MergeSeatsCOutTrnInfo``).
    remaining_standing_count: str | None = None
    #: ``h_std_rest_seat_cnt`` — 일반실 잔여석. 두 DTO 모두 선언합니다.
    standard_remaining_seat_count: str | None = None
    #: ``h_fst_rest_seat_cnt`` — 특실 잔여석(``TrainScheduleOutTrainInfo``).
    first_remaining_seat_count: str | None = None
    #: ``h_yms_apl_flg`` — 이 행이 병합(입석+좌석) 대상인지를 정하는 유일한 입력(``TrainScheduleOutTrainInfo``,
    #: ``models.TrainSummary`` 참고).
    merge_target_flag: str | None = None
    #: ``h_trn_sps_flg`` — 운휴 표시/예약 게이트(``TrainScheduleOutTrainInfo``).
    train_suspended_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # raw 의 위치 인자 자리를 유지합니다. 추가 필드의 잘못된 타입은 해당 값만 비웁니다.
    special_reservation_name: str | None = None
    free_seat_reservation_name: str | None = None


@dataclass(frozen=True)
class PassScheduleTrain:
    """정기권 일정의 열차 한 행(``TrainList.java:25-70``, 20개 필드)."""

    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    detour_code: str | None = None
    schedule_price: str | None = None
    train_group_code: str | None = None
    train_no: str | None = None
    #: ``h_trn_seq`` — 열차 순번.
    train_sequence: str | None = None
    #: h_chg_trn_seq/h_chg_trn_dv_cd — 구간 순서·여정 종류(1 직통/2 환승). TrainSummary 의 설명을 따릅니다.
    change_train_sequence: str | None = None
    change_train_division_code: str | None = None
    #: ``h_run_dt`` — 이 행의 유일한 운행일자.
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
    commuter_age_code: str | None = None
    display_name: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassScheduleInfo:
    trains: tuple[PassScheduleTrain, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassScheduleMainInfo:
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
    """``assignScheduleView.do`` — ``TrainScheduleOut.java:67`` 의 전체 필드.

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
    code: str | None = None
    name: str | None = None
    run_order: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassPeriodOption:
    commuter_period_code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MergeSeatsInquiryResponse(BaseKorailResponse):
    merge_reservation_possible_flag: str | None = None
    #: 최상위 runDt 선언: MergeSeatsCOut.java:29,112. 2026-09-22 관측 20여 회에는 없었고 행의 h_run_dt 는 존재했습니다. 필요하면
    #: trains[i].run_date 를 확인하십시오. 항상 None 이라는 보장은 아닙니다.
    run_date: str | None = None
    intermediate_stations: tuple[IntermediateStation, ...] = ()
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class PassMenuData:
    commuter_kind_code: str | None = None
    station_selection: str | None = None
    age_options: tuple[PassAgeOption, ...] = ()
    period_options: tuple[PassPeriodOption, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassPassengerInfo:
    h_cls_prnb: int | None = None
    h_dcnt_knd_cd: str | None = None
    h_st_prnb: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassPassengerInfos:
    h_chtn_allw_flg: str | None = None
    h_max_cnt: str | None = None
    h_min_cnt: str | None = None
    psg_info: tuple[PassPassengerInfo, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassGoodsInfo:
    h_cnd_flg_disc_no: str | None = None
    psg_infos: PassPassengerInfos | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PassMenuItem:
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
    items: tuple[PassMenuItem, ...] = ()


@dataclass(frozen=True)
class CommuterKindMenuResponse(BaseKorailResponse):
    after_day: str | None = None
    agreement: str | None = None
    information: str | None = None
    title: str | None = None
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class CrewRequestOption:
    message_code: str | None = None
    content: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class CrewRequestListResponse(BaseKorailResponse):
    items: tuple[CrewRequestOption, ...] = ()


@dataclass(frozen=True)
class PassScheduleResponse(BaseKorailResponse):
    main_info: PassScheduleMainInfo | None = None
    schedules: tuple[PassScheduleInfo, ...] = ()


@dataclass(frozen=True)
class DiscountCardSection:
    """N카드 적용 구간(AppSegInfo.java:24-37, DiscountCardInfo.java:28). @SerialName 별칭이 없는 키는 보호된 serializer 대신 속성명을
    사용한 추정입니다. 일정 조회가 받는 역 이름을 구간에서 확인할 수 있습니다."""

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
    """상세의 선택 할인카드(DiscountCardInfo.java:27-32, TicketDetailOut.java:49,438). 카드번호는 사용내역·할인 예약에 사용합니다. 앱도 N카드 예약
    모드에서 승객 행에 넣습니다 (Passengers.java:766, TicketReservationInPassengerInfo.java:26-34). 할인 코드 153 은 라이브 기록에 의존하며
    ReqDiscount.java:36 의 보호된 평문은 미확인입니다."""

    #: ``h_dcnt_crd_no``(``DiscountCardInfo.java:113`` 의 ``@SerialName``).
    card_no: str | None = None
    #: 기간연장 플래그(DiscountCardInfo.java:30,117). Y 의 의미는 라이브 기록에 의존합니다. 버튼 연결의 기존 근거는
    #: NCardTicketSectionKt.smali:7821-7843 이며 현재 자료로 재검증하지 못했습니다. 앱의 비교 리터럴은 보호돼 있습니다.
    term_extension_possible_flag: str | None = None
    sections: tuple[DiscountCardSection, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class KorailPointSummaryResponse(BaseKorailResponse):
    """포인트·자격 요약(MyXPointViewOut.java:27-74). 별칭 없는 키는 속성명에 따른 추정입니다. 2026-09-22 관측은 자체 43+봉투 3+서버 추가
    2(h_coup_sno1/srNoticeUrl)=48키였습니다. 소비자는 AppSuitLinker 를 거치므로 플래그 코드의 의미를 필드명만으로 확정하지 마십시오."""

    #: ``h_korail_point`` — 마이페이지에 뜨는 코레일 포인트 잔액.
    korail_point: str | None = None
    #: h_disc_coup_cnt — 서버가 보고한 할인쿠폰 개수. get_discount_coupons 결과 길이와 항상 같다는 보장은 없습니다.
    discount_coupon_count: str | None = None
    #: ``h_delay_cnt`` — 계정이 가진 지연할인권 개수.
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
    # 새 필드는 끝에 덧붙입니다(위치 인자 의미 보존). ``h_cust_lead_flg``(``MyXPointViewOut.java:43``) — 보조견 등록 플래그 그 자체. 사람이 읽는 짝은
    # :attr:`customer_lead_flag_name`(``:44``)입니다.
    customer_lead_flag: str | None = None
    #: ``h_hdcp_tp_cd``/``h_hdcp_tp_cd_nm``(``:53,54``) — 장애 유형 코드와 이름. 유형은
    #: :attr:`disability_flag`(``h_hdcp_flg``)가 아니라 이 둘에 있습니다. 셋 다 라이브 응답에 옵니다(2026-09-22).
    disability_type_code: str | None = None
    disability_type_name: str | None = None


@dataclass(frozen=True)
class MileageHistoryEntry:
    """마일리지 내역의 적립 또는 사용 한 줄.

    ``AmtSpecOutSpecInfo.java:29-35`` 가 선언하는 것이 정확히 아래 일곱 필드입니다. 2026-09-22 라이브에서 3페이지 14행 전부가 이 일곱 키를 문자열로 싣고 그
    밖의 키는 없었습니다."""

    #: ``dptDt`` — 이 줄이 귀속된 출발일.
    departure_date: str | None = None
    #: ``pontDvNm`` — 적립/사용 구분 이름.
    point_division_name: str | None = None
    #: ``mlgAcmDvCdNm`` — 어떤 방식으로 적립됐는지.
    accrual_division_name: str | None = None
    #: ``rcpDvNm`` — 수납 구분 이름.
    receipt_division_name: str | None = None
    #: ``pontAmt`` — 이 줄의 포인트 증감. 부호가 붙습니다.
    point_amount: str | None = None
    #: ``savePontValNum`` — 이 줄 시점의 누적 잔액.
    saved_point_value: str | None = None
    #: ``stlAmt`` — 이 줄이 나온 정산 운임.
    settlement_amount: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """마일리지 페이지(AmtSpecOut.java:29-39,199-247). 별도로 선언된 합계 필드는 합치지 않습니다. 2026-09-22 KTX/RAIL_POINT 의 3페이지에서 DTO
    밖 railNowSavePontValNum1 을 관측했으며 해당 계정에서는 totAcmRailPontValNum1 과 같았습니다. 추가 키는 raw 로 제공합니다."""

    #: ``pgCnt`` — 전체 페이지 수(``AmtSpecOut.java:32``).
    page_count: str | None = None
    query_count: str | None = None
    total_available_rail_point: str | None = None
    total_available_rail_point_1: str | None = None
    total_available_affiliate_point: str | None = None
    total_accumulated_rail_point_1: str | None = None
    total_used_rail_point_1: str | None = None
    #: ``delPontValNum`` — 이번 달에 소멸하는 포인트.
    expiring_point_value: str | None = None
    ktx_mileage_info: str | None = None
    entries: tuple[MileageHistoryEntry, ...] = ()


@dataclass(frozen=True)
class DiscountCardUsage:
    """N카드 사용 내역(NCardHistoryInfo.java:22,224). 전송 키는 속성명에 따른 추정입니다. 화면 사용:
    NCardHistoryScreenKt.java:301,431,439,526,528, NCardHistoryViewModel.java:123,141.
    sale_date/sequence/window_no 가 OriginalTicketReference 로 바로 호환된다고 가정하지 마십시오. 2026-09-22 카드번호 4종은 모두
    ERR000100 으로 채워진 응답을 확인하지 못했습니다."""

    #: ``custNm`` — 이 구간을 실제로 탄 사람의 이름.
    passenger_name: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    #: runDt1, yyyyMMdd.
    run_date: str | None = None
    #: apdUsrFlg — 두 번째 등록 사용자(N카드 2인용)가 탔는지의 플래그. 앱은 보호된 1바이트 리터럴과 비교합니다
    #: (NCardHistoryScreenKt.java:301); 그 평문은 추정하지 않습니다.
    additional_user_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # 새 필드는 ``raw`` 뒤에 덧붙입니다(위치 인자 의미 보존). ``saleDt``/``saleSqno``/``saleWctNo`` — 이 사용 건의 바탕이 된 발매
    # 일자·일련번호·창구번호(``NCardHistoryInfo.java:224``). 클래스 독스트링의 경고를 읽으십시오.
    sale_date: str | None = None
    sale_sequence: str | None = None
    sale_window_no: str | None = None


@dataclass(frozen=True)
class DiscountCardUsageListResponse(BaseKorailResponse):
    """``ticket.dcntCrdUseQry.do`` — 카드가 쓰인 여행 목록.

    ``NCardHistoryOut.java:27,82`` 가 싣는 것은 ``@SerialName("tkUseList")`` 하나뿐이라, 전선에 없는 요약 필드를 이 모델도 만들어 붙이지
    않습니다."""

    items: tuple[DiscountCardUsage, ...] = ()


@dataclass(frozen=True)
class DiscountCardScheduleTrain:
    """N카드 사용 가능 열차(NCardScheduleItem.java:30-49). 보호된 serializer 대신 속성명으로 읽습니다. 앱이 표시용으로 만드는 Spanned
    stationInfo 를 서버 필드로 모델링하지 않습니다. 명시적 @SerialName 이 없다는 사실만으로 실제 전송 키를 확정할 수는 없습니다."""

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
    #: ``arvStnRunOrdr`` — 하차역 운행 순서.
    arrival_run_order: str | None = None
    #: ``chtnTrnOrdrNo`` — 환승 열차 순번.
    transfer_train_order_no: str | None = None
    #: ``prcClCd`` — 운임 구분 코드.
    price_class_code: str | None = None
    #: ``stlbCarTpCd``/``stlbTrnClsfCd`` — 정산용 호차·열차 종류 코드.
    settlement_car_type_code: str | None = None
    settlement_train_class_code: str | None = None
    #: ``cmtrPrc`` — 이 카드의 구간에 매겨진 운임.
    commuter_price: str | None = None
    direct_transfer_division_code: str | None = None
    detour_code: str | None = None
    detour_name: str | None = None
    route_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class DiscountCardScheduleResponse(BaseKorailResponse):
    """N카드 일정(NetworkApi.java:339-341, NCardScheduleOut.java:27-28). DTO 는 trnScdlList 만 선언합니다. 이 파서는
    following_page_exists 를 채우지 않으므로 이 필드를 폴링 신호로 쓰지 마십시오. 실제 서버의 페이지 지원 여부는 미확인입니다."""

    #: 항상 None. DiscountCardScheduleResponse 설명 참고.
    following_page_exists: str | None = None
    trains: tuple[DiscountCardScheduleTrain, ...] = ()


@dataclass(frozen=True)
class MultiChildDiscountTarget:
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
    targets: tuple[MultiChildDiscountTarget, ...] = ()


@dataclass(frozen=True)
class CustomerTripInfo:
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
    #: ``gdNo`` — 상품번호(``CustTripInfo.java`` 33필드 중 하나). ``@SerialName`` 이 없어 와이어 철자는 PROTECTED 이며 코틀린 필드명을 최선으로
    #: 사용합니다.
    goods_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class CustomerTripInfoResponse(BaseKorailResponse):
    trips: tuple[CustomerTripInfo, ...] = ()


@dataclass(frozen=True)
class MaasServiceDetailInfo:
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
    entity_one: tuple[Mapping[str, Any], ...] = field(default=(), compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class MaasServiceDetail:
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
    details: tuple[MaasServiceDetail, ...] = ()


@dataclass(frozen=True)
class TripChangeDateResponse(BaseKorailResponse):
    """``reservation.tripChgDate.do``(``NetworkApi.java:238``) (``TipChgDateInquiryOut.java:28-30``).

    ``tripChgDate``(단수)는 **요청** DTO(``TipChgDateInquiryIn.java:29``)의 필드입니다 — 응답은 복수형
    ``tripChgDates``(``List<String>``)만 선언하므로, 여기서는 단수형을 읽지 않습니다."""

    last_run_date: str | None = None
    trip_change_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommuterPassengerOption:
    """``Psg.java:28-33``, 6개 필드 중 4개만 있으면 연령 하한/상한이 없습니다."""

    commuter_usage_age_code: str | None = None
    common_code_name: str | None = None
    #: ``custAgeFrom``/``custAgeTo`` — 이 옵션이 적용되는 연령 하한/상한. 키가 없으면 형제 필드처럼 ``0`` 입니다. 정수로 읽을 수 없는 모양이면 응답을 거부하지
    #: 않고 ``None`` 입니다.
    customer_age_from: int | None = 0
    customer_age_to: int | None = 0
    passenger_count_from: int = 0
    passenger_count_to: int = 0
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class CommuterInfoResponse(BaseKorailResponse):
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
    available_passenger_count_from: int = 0
    available_passenger_count_to: int = 0
    passenger_options: tuple[CommuterPassengerOption, ...] = ()


@dataclass(frozen=True)
class PriceFare:
    journey_sequence: str | None = None
    room_class_name: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    total_amount: str | None = None
    train_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PriceFareQuoteResponse(BaseKorailResponse):
    fares: tuple[PriceFare, ...] = ()


@dataclass(frozen=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    acceptance_customer_management_no: str | None = None
    acceptance_customer_name: str | None = None
    acceptance_customer_phone: str | None = None
    member_card_no: str | None = None


@dataclass(frozen=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    #: ``rsvCnt`` — ``TicketDupCheckOut.java:28`` 의 선언은 ``String`` 이고 이 DTO 는 kotlinx 이므로 문자열로 읽습니다(``"0007"`` 은
    #: 그대로). 서버가 이 값을 JSON 정수로 보낸 적이 있는지는 확인하지 않았습니다.
    reservation_count: str | None = None


@dataclass(frozen=True)
class PbpAcceptanceSeat:
    passenger_type_division_name: str | None = None
    room_class_code: str | None = None
    room_class_name: str | None = None
    car_no: int = 0
    seat_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PbpAcceptanceJourney:
    acceptance_customer_name: str | None = None
    acceptance_customer_phone: str | None = None
    journey_type_code: str | None = None
    member_division_name: str | None = None
    acceptance_kind_name: str | None = None
    pbp_reservation_no: str | None = None
    registered_date: str | None = None
    withdrawal_possible_flag: str | None = None
    seats: tuple[PbpAcceptanceSeat, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    member_card_no: str | None = None


@dataclass(frozen=True)
class PbpAcceptanceTicket:
    pnr_no: str | None = None
    sale_date: str | None = None
    sale_sequence: str | None = None
    sale_window_no: str | None = None
    return_password: str | None = None
    journeys: tuple[PbpAcceptanceJourney, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    tickets: tuple[PbpAcceptanceTicket, ...] = ()


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """좌석변경 승차역(ChgStnInfo.java:21-35, SeatAvailabilityOut.java:32). 전송 키는 속성명에 따른 추정입니다. 역별 일반실·특실 잔여좌석을 제공합니다.
    DTO 의 도착역 코드·이름·편성/운행순서 4개 필드는 이 모델에서 읽지 않습니다."""

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
    """좌석 변경 사유(ChgRsnInfo.java:21-24, SeatAvailabilityOut.java:31).

    String 속성은 frcSaleRsnCont/qryCode/qryOrdr 입니다. serializer descriptor 의 이름이 보호돼 있어
    (ChgRsnInfo$$serializer.java:34-36) 전송 키는 속성명에 따른 추정입니다."""

    query_code: str | None = None
    query_order: str | None = None
    reason_text: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """자율 좌석변경 정보(NetworkApi.java:806-808, SeatAvailabilityOut.java:28-42,68). 자체 필드의 전송 키는 속성명에 따른 추정입니다. 열차 단위
    가부와 stations 의 역별 잔여좌석은 다릅니다."""

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
    """원표 좌석(SeatInfo.java:25-51, JrnyInfo.java:58). 대리수령용 Seat.java:27-36 과는 이름과 구조가 다른 타입입니다."""

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
    """원표 구간(OrgTk.java:38, JrnyInfo.java:29-63). 대리수령용 Jrny.java:29-38 과 다릅니다. 여정 순번·역코드·운행순서를 후속 변경 조회에
    재사용합니다."""

    journey_sequence: str | None = None
    journey_order: str | None = None
    #: jrnyTpCd. 다른 필드와 마찬가지로 repr 에 포함됩니다.
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
    """원표(OrgTk.java:28-52, OgTicketInquiryOut.java:27). 전송 키는 속성명에 따른 추정입니다. original_* 는 요청한 승차권 자신의 반환번호가
    되돌아온 값이며 repr 에서 숨기지 않습니다. 변경에 필요하지 않은 cmpnList·stlList 는 타입화하지 않지만 raw 에 지연증명·결제 자격증명이 그대로
    남습니다(Cmpn.java:35-38, Stl.java:29,32,37)."""

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
    """변경의 기준이 되는 원표 목록(NetworkApi.java:234-236, OgTicketInquiryOut.java:26-27,54)."""

    tickets: tuple[OriginalTicket, ...] = ()


@dataclass(frozen=True)
class RecentDeliveryRecipient:
    acceptance_customer_management_flag: str | None = None
    acceptance_customer_management_no: str | None = None
    acceptance_customer_name: str | None = None
    acceptance_customer_phone: str | None = None
    acceptance_customer_phone_2: str | None = None
    member_card_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    changed_acceptance_reservation_no: str | None = None
    recipients: tuple[RecentDeliveryRecipient, ...] = ()


@dataclass(frozen=True)
class ReservationSeatDetail:
    """예약 좌석. 명시적 필드: ReservationOutSeatInfo.java:33,81. h_psg_tp_dv_nm 은 DTO 에 없지만 앱 내장
    표본(BasketTicketDataKt.java:44)에 존재합니다. 이 표본의 실제 캡처 여부는 코드만으로 확인할 수 없습니다. 2026-09-22 라이브 8/8 행 관측 기록도 있으나 캡처
    미연결입니다. 재계산 행의 기존 종류·객실·할인 값을 이 좌석에서 가져옵니다."""

    car_no: str | None = None
    seat_no: str | None = None
    room_class_code: str | None = None
    room_class_name: str | None = None
    passenger_type_code: str | None = None
    #: ``h_rcvd_amt`` — 이 좌석에 실제로 걷히는 금액. 예약 응답에 ``h_tot_rcvd_amt`` 가 없을 때 결제 경로가 ``hidMnsStlAmt1`` 을 이 값들의 합으로
    #: 구하므로, 정산 금액을 다른 출처로 대조해 볼 수 있습니다.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    #: ``h_tot_disc_amt`` — 이 좌석의 총 할인액. 같은 와이어 키를 ``_REFUND_TICKET_DETAIL_FIELDS`` 가 ``total_discount_amount``
    #: 로 매핑하는 것과 이름을 맞춥니다.
    total_discount_amount: str | None = None
    seat_group_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    # 새 필드는 ``raw`` 뒤에 덧붙입니다(위치 인자 의미 보존). ``h_psg_tp_dv_nm`` — :attr:`passenger_type_code` 의 사람이 읽는 짝. 클래스 독스트링
    # 참고.
    passenger_type_name: str | None = None


@dataclass(frozen=True)
class ReservationDetailJourney:
    """보류된 예약의 여정 하나(``jrny_infos.jrny_info[]``)."""

    journey_sequence: str | None = None
    journey_type_code: str | None = None
    reservation_change_no: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    #: ``h_arv_dt`` — 도착일. ``arrival_time``(``h_arv_tm``)과 별개 필드로, 심야·익일 도착 열차에서 도착 시각이 어느 날짜인지 정합니다.
    arrival_date: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    train_no: str | None = None
    train_class_name: str | None = None
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR 로 다시 읽은 예약 상세. ReservationOut 을 공유하며 창구번호·좌석별 정산액을 확인하는 경로입니다."""

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


@dataclass(frozen=True)
class RefundCommissionResponse(BaseKorailResponse):
    """환불 전 수수료·예상 환불액 조회(NetworkApi.java:598-600). 키 근거: RefundCommissionOut.java:35-41,62,140-164. 이 응답 자체는 실제
    환불 완료가 아닙니다."""

    #: ``ret_amt`` — 돌려받을 금액.
    refund_amount: str | None = None
    #: ``ret_fee`` — 거기서 떼는 수수료.
    refund_fee: str | None = None
    #: ``prg_psb_flg`` — 환불을 진행할 수 있는지 여부입니다.
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
    #: ``h_msg_cd2``/``h_msg_txt2`` — 이 경로가 봉투의 것과 별개로 싣는 **두 번째** 메시지 짝. 성공한 사전 조회에 수수료 정책 안내가 붙는 식입니다.
    secondary_message_code: str | None = None
    secondary_message_text: str | None = None


@dataclass(frozen=True)
class RefundTicketSeat:
    """환불 대상 승차권의 좌석 하나(``tk_seat_info[]``)."""

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
    """환불 대상 승차권의 여정 하나(``ticket_infos.ticket_info[]``)."""

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
    """환불 대상 상세(TicketDetailOut.java:38,117). 별칭 없는 전송 키는 추정입니다. 동반자 값은 수수료 조회에
    전달하며(MyTicketDetailViewModel.java:277), 환불 입력은 PaidTicket.from_refund_detail 로 조립하십시오. 2026-09-22 관측 40응답의
    mlgSaveFlg/mlgSaveTgt 는 모두 빈 문자열이었습니다. DTO 미선언(TicketDetailOut.java:39-91,117)이므로 타입화하지 않지만 raw 에 남습니다."""

    pnr_no: str | None = None
    sale_date: str | None = None
    sale_time: str | None = None
    window_name: str | None = None
    original_sale_date: str | None = None
    original_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    #: ``h_tk_knd_cd`` — 승차권 종류 코드. 개인정보가 아닙니다. 형제 클래스 ``OriginalTicket``/``StationRefundOriginalTicket`` 에서도
    #: 평범한 필드라, 그쪽과 표시를 맞춥니다.
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    #: retPsbFlg(TicketDetailOut.java:71)는 환불 성공 보장이 아닙니다. 2026-09-22 상세 40응답은 Y 였지만 수수료 조회는 승차일 경과 5건
    #: WRT200022, 이미 반환 2건 WRT200399 로 거절했고 목록 이력 143장은 N 이었습니다. 앱은 이 값과 사용 여부를 함께
    #: 검사합니다(NormalTicketSectionKt.java:951). 비교 리터럴은 보호돼 있으며 상세 화면이 특정 목록에서만 열린다는 보장은 확인되지 않았습니다. 수수료 조회와 실제 반환
    #: 결과를 별도로 확인하십시오.
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
    #: pbpAcepTgtFlg: 2026-09-22 상세 40응답(20승차권×2모드)에는 후보 키가 없었고 목록 Y 6건도 같았습니다. 목록 키는
    #: MyTicketListOutTicket.java:92,300, 상세의 변경 가능 필드·setter 는 TicketDetailOut.java:65,1936. 앱은 목록 값을
    #: 주입합니다(MyTicketBaseViewModel.java:769). 주입 코드만으로 서버 전송이 불가능하다고 단정하지 않습니다. 파서는 pbpAcepTgtFlg 를 읽을 수 있습니다.
    #: 필요한 값은 TicketListTicket.pbp_acceptance_target_flag 에서 확인하십시오.
    pbp_acceptance_target_flag: str | None = None
    #: ``h_dlay_flg``/``h_dlay_tk_flg`` — 지연 보상 대상 여부.
    delay_flag: str | None = None
    delay_ticket_flag: str | None = None
    #: ``addSrvFlg``/``addSrvCancel`` — 딸린 부가서비스가 있는지, 환불이 그것도 함께 취소하는지 여부.
    additional_service_flag: str | None = None
    additional_service_cancel: str | None = None
    #: ``h_qrcode`` — 이 승차권의 QR 코드(``TicketDetailOut.java:478``).
    qr_code: str | None = None
    #: ``psgNmList`` — 승객 성명 목록(``List<PsgNameInfo>``). ``@SerialName`` 이 없어 와이어 철자는 PROTECTED, 코틀린 필드명을 최선으로
    #: 사용합니다. 각 원소는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다.
    passenger_names: tuple[Mapping[str, Any], ...] = field(default=(), compare=False)
    #: ``seatTicketList`` — 좌석 배정 목록(``List<SeatAssignInfo>``, PROTECTED).
    seat_tickets: tuple[Mapping[str, Any], ...] = field(default=(), compare=False)
    #: ``limousine`` — 연계된 리무진 예약(단일 객체, PROTECTED). 없으면 ``None``.
    limousine: Mapping[str, Any] | None = field(default=None, compare=False)
    #: ``dtlList`` — 지연 정보 목록(``List<DelayInfo>``, PROTECTED).
    delay_details: tuple[Mapping[str, Any], ...] = field(default=(), compare=False)
    journeys: tuple[RefundTicketJourney, ...] = ()
    #: ``dcnt_crd_info`` — 이 "승차권"이 실은 할인카드(N카드)일 때만 있습니다. 보통 승차권에서는 ``None`` 입니다.
    discount_card: DiscountCardOnTicket | None = None
