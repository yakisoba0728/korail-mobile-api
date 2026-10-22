# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""정기권·패스·N카드·여행상품 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..common.models import BaseKorailResponse


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
class PassPeriodOption:
    """패스 예매에 사용할 기간 선택 항목을 담습니다."""

    commuter_period_code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


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
class PassScheduleResponse(BaseKorailResponse):
    """정기권으로 이용 가능한 열차 목록을 담습니다."""

    main_info: PassScheduleMainInfo | None = None
    schedules: tuple[PassScheduleInfo, ...] = ()


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
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """N카드 구매의 결제 전 예약 결과를 담습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 구매의 결제 전 응답(NCardInfoOut.java:25-38,
    # NetworkApi.java:335-337).

    lump_settlement_target_no: str | None = None
    discount_card_settlement_target_no: str | None = None
    received_amount: str | None = None
    stx_amount: str | None = None
    taxt_supply_amount: str | None = None
    usable_trip_count: str | None = None
    validity_start_date: str | None = None
    validity_end_date: str | None = None
    # 요청의 DiscountCardPurchaseRequest.card_kind_management_no ("요청한 값")과 다른 이름을 써서, 호출자가 "무엇을
    # 요청했는지"와 "서버가 실제로 등록한 것"을 구분할 수 있게 합니다 (NCardInfoOut.java:30, dcntCrdStlTgtNo 와는 별개 필드).
    #: 응답에 담긴 카드 종류 관리번호입니다. 요청한 값은 ``DiscountCardPurchaseRequest.card_kind_management_no``에 있습니다.
    registered_card_kind_management_no: str | None = None


@dataclass(frozen=True)
class ProductCancelResponse(BaseKorailResponse):
    """여행상품 예약의 실제 취소 결과를 담습니다."""

    integrated_message_code: str | None = None
