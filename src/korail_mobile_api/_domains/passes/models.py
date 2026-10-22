# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""정기권·패스·N카드·여행상품 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..._core.parsing import optional_int, wire
from ..common.models import BaseKorailResponse


@dataclass(frozen=True)
class PassOffice:
    """패스 조회의 발권처 코드와 표시 이름을 담습니다."""

    code: str | None = wire("eng_cd_val")
    display_name: str | None = wire("kor_cd_val")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassOpenDate:
    """패스 사용 개시일 한 행과 그 항목 일련번호·PNR을 담습니다.

    ``PassAvailabilityResponse.pass_info``의 한 행입니다. 사용 개시일만 필요하면 ``PassAvailabilityResponse.open_dates``를
    쓰세요."""

    # 항목 일련번호·PNR 의 할당 원리와 행마다 달라지는지는 미확인입니다.
    open_date: str | None = wire("h_use_open_dt")
    item_sequence: str | None = wire("h_item_sqno")
    pnr_no: str | None = wire("h_pnr_no")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassAvailabilityMainInfo:
    """패스 사용일 조회의 중첩 상태와 건수를 담습니다.

    이 응답은 결과 코드를 최상위가 아니라 이 블록의 ``message_code``에만 담아 보낼 수 있습니다. 라이브러리는 이 값으로 예외를
    발생시키지 않으므로 필요하면 직접 확인하세요."""

    message_code: str | None = wire("h_msg_cd")
    total_count: str | None = wire("h_tot_cnt")
    row_count: str | None = wire("h_row_cnt")
    selected_page_no: str | None = wire("h_sel_pg_no")
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

    title: str | None = wire("contTitle")
    detail: str | None = wire("contDetail")
    detail_type: str | None = wire("detailType")
    active: str | None = wire("passActive")
    agree: str | None = wire("passAgree")
    info: str | None = wire("passInfo")
    image: str | None = wire("contImage")
    url: str | None = wire("contUrl")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    #: 정기권 종류 코드(``cmtrKndCd``)입니다. ``get_commuter_kind_menu``의 ``commuter_kind_code``로 넘깁니다. 정기권 메뉴가 아닌
    #: 행에서는 ``None``일 수 있습니다.
    commuter_kind_code: str | None = wire("cmtrKndCd")
    #: 응답의 ``passType`` 값입니다. 의미를 확인하지 못했습니다.
    pass_type: str | None = wire("passType")
    #: 정기권 조회에 필요한 연령·기간 선택지 묶음(``passData``)입니다. 없으면 ``None``입니다.
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class TripMenuItem:
    """여행상품 메뉴 한 항목과 그 안내 목록을 담습니다."""

    title: str | None = wire("menuTitle")
    detail: str | None = wire("menuDetail")
    menu_type: str | None = wire("menuType")
    button: str | None = wire("menuBtn")
    contents: tuple[TripMenuContent, ...] = ()
    url: str | None = wire("menuUrl")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # String 선언이지만 실서버에서 JSON 정수로 와서 정수로 읽습니다.
    #: 안내 행 개수(``contCount``)입니다. 정수나 숫자 문자열을 정수로 읽으며, 그 밖의 값이면 ``None``입니다.
    content_count: int | None = wire("contCount", optional_int, default=None)


@dataclass(frozen=True)
class TripMenuResponse(BaseKorailResponse):
    """여행상품 메뉴 목록을 담습니다."""

    items: tuple[TripMenuItem, ...] = ()
    popup_message: str | None = wire("poppMsg")


@dataclass(frozen=True)
class ProductReservation:
    """여행상품 예약 한 건의 식별자와 상태를 담습니다."""

    product_name: str | None = wire("strGdNm")
    reservation_status_name: str | None = wire("strRsvSttNm")
    settlement_deadline: str | None = wire("strStlDlnDt")
    settlement_status_code: str | None = wire("strStlSttCd")
    virtual_reservation_no: str | None = wire("strVrRsvNo")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    #: 예약 순번(``strVrRsvSqno``)입니다. ``virtual_reservation_no``와 함께 ``get_product_detail``의 ``reservation_sequence``로
    #: 넘깁니다.
    reservation_sequence: str | None = wire("strVrRsvSqno")
    #: 예약 상태 코드(``strRsvSttCd``)입니다. 코드 값의 의미는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    reservation_status_code: str | None = wire("strRsvSttCd")


@dataclass(frozen=True)
class ProductReservationListResponse(BaseKorailResponse):
    """여행상품 예약 목록 한 페이지를 담습니다."""

    items: tuple[ProductReservation, ...] = ()
    # 응답의 mainInfo 객체에서 읽습니다.
    total_count: int | None = wire("strTotCnt", optional_int, default=None)


@dataclass(frozen=True)
class ProductDetailResponse(BaseKorailResponse):
    """여행상품 예약의 상세·금액·취소 조건을 담습니다."""

    # wire 필드는 응답의 mainInfo 객체에서 읽습니다.
    product_name: str | None = wire("strGdNm")
    reservation_status_name: str | None = wire("strRsvSttNm")
    cancellation_deadline: str | None = wire("strCncDlnDt")
    cancellation_return_amount: str | None = wire("strCncRetAmt")
    cancellation_fee: str | None = wire("strCncRetFee")
    received_amount: str | None = wire("strRcvdAmt")
    total_settlement_amount: str | None = wire("strTotStlAmt")
    usage_period: str | None = wire("strUtlTrmCont")
    included_item_names: tuple[str, ...] = ()
    virtual_reservation_no: str | None = wire("strVrRsvNo")
    detail_raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    #: 상품 일련번호(``strGdSqno``)입니다. ``cancel_product_reservation``은 이 값과 ``virtual_reservation_no``로 취소를 요청하며,
    #: 값이 비어 있으면 요청을 보내기 전에 ``KorailProtocolError``를 발생시킵니다.
    goods_sequence: str | None = wire("strGdSqno")


@dataclass(frozen=True)
class PassScheduleTrain:
    """정기권으로 이용할 수 있는 열차 한 편을 담습니다."""

    arrival_station_code: str | None = wire("h_arv_rs_stn_cd")
    arrival_station_name: str | None = wire("h_arv_rs_stn_nm")
    departure_station_code: str | None = wire("h_dpt_rs_stn_cd")
    departure_station_name: str | None = wire("h_dpt_rs_stn_nm")
    detour_code: str | None = wire("h_dtour")
    schedule_price: str | None = wire("h_schd_prc")
    train_group_code: str | None = wire("h_trn_gp_cd")
    train_no: str | None = wire("h_trn_no")
    train_sequence: str | None = wire("h_trn_seq")
    change_train_sequence: str | None = wire("h_chg_trn_seq")
    change_train_division_code: str | None = wire("h_chg_trn_dv_cd")
    run_date: str | None = wire("h_run_dt")
    price_class_code: str | None = wire("h_prc_cl_cd")
    route_code: str | None = wire("h_rout_cd")
    departure_construction_order: str | None = wire("h_dpt_stn_cons_ordr")
    arrival_construction_order: str | None = wire("h_arv_stn_cons_ordr")
    car_type_code: str | None = wire("h_car_tp_cd")
    train_class_code: str | None = wire("h_trn_clsf_cd")
    commuter_period_code: str | None = wire("h_cmtr_utl_trm_cd")
    commuter_use_terminal_name: str | None = wire("h_cmtr_utl_trm_nm")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassAgeOption:
    """패스 예매에 사용할 연령 선택 항목을 담습니다."""

    commuter_age_code: str | None = wire("h_cmtr_utl_age_cd")
    display_name: str | None = wire("h_comn_cd_nm")
    minimum_age: str | None = wire("h_min_age")
    maximum_age: str | None = wire("h_max_age")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassScheduleInfo:
    """정기권 열차 조회의 조건과 부가 정보를 담습니다."""

    trains: tuple[PassScheduleTrain, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassScheduleMainInfo:
    """정기권 열차 조회의 중첩 상태와 조건을 담습니다."""

    sale_window_no: str | None = wire("h_wct_no")
    work_date: str | None = wire("h_work_dt")
    work_time: str | None = wire("h_work_tm")
    job_id: str | None = wire("h_job_id")
    version_no: str | None = wire("h_ver_no")
    message_code: str | None = wire("h_msg_cd")
    selected_count: str | None = wire("h_sel_cnt")
    total_selected_count: str | None = wire("h_tot_sel_cnt")
    count_per_page: str | None = wire("h_cnt_per_page")
    #: 페이지 수(``h_page_cnt``)입니다. 전체 건수가 페이지 크기보다 커도 ``next_page_flag``가 ``"N"``으로 올 수 있으므로, 이 값과
    #: ``next_page_flag``만으로 모든 결과를 받았다고 판단하지 마세요.
    page_count: str | None = wire("h_page_cnt")
    next_page_flag: str | None = wire("h_next_pg_flg")
    change_train_division_code: str | None = wire("h_chg_trn_dv_cd")
    page_no: str | None = wire("h_page_no")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassPeriodOption:
    """패스 예매에 사용할 기간 선택 항목을 담습니다."""

    commuter_period_code: str | None = wire("h_cmtr_utl_trm_cd")
    display_name: str | None = wire("h_comn_cd_nm")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassMenuData:
    """패스 메뉴의 역 선택 조건과 상품 코드를 담습니다."""

    commuter_kind_code: str | None = wire("h_cmtr_knd_cd")
    # 키가 패스 메뉴는 h_select_station, 여행 메뉴는 서버 철자 h_seiect_station 이라 파서가 골라 채웁니다.
    station_selection: str | None = None
    age_options: tuple[PassAgeOption, ...] = ()
    period_options: tuple[PassPeriodOption, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassPassengerInfo:
    """패스의 승객 종류별 인원 조건을 담습니다."""

    # 관측된 인원은 000001 같은 0 채움 문자열이라 정수로 읽습니다.
    h_cls_prnb: int | None = wire("h_cls_prnb", optional_int, default=None)
    h_dcnt_knd_cd: str | None = wire("h_dcnt_knd_cd")
    h_st_prnb: int | None = wire("h_st_prnb", optional_int, default=None)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassPassengerInfos:
    """패스 승객 조건 목록을 담습니다."""

    h_chtn_allw_flg: str | None = wire("h_chtn_allw_flg")
    h_max_cnt: str | None = wire("h_max_cnt")
    h_min_cnt: str | None = wire("h_min_cnt")
    psg_info: tuple[PassPassengerInfo, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassGoodsInfo:
    """패스 메뉴에 연결된 상품 정보를 담습니다."""

    h_cnd_flg_disc_no: str | None = wire("h_cnd_flg_disc_no")
    psg_infos: PassPassengerInfos | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassMenuItem:
    """정기권·패스 메뉴 한 항목과 안내를 담습니다."""

    # 앱은 safeToInt 로 읽고 실패하면 0 을 쓰지만, 라이브러리는 받은 문자열을 그대로 둡니다.
    #: 응답의 ``afterDay`` 값입니다. 서버가 보낸 문자열을 그대로 담으므로, 정수가 필요하면 직접 변환하세요.
    after_day: str | None = wire("afterDay")
    agreement: str | None = wire("agree")
    detail_type: str | None = wire("detailType")
    detail_description: str | None = wire("dtlDsc")
    enabled: str | None = wire("enable")
    item_id: str | None = wire("id")
    information: str | None = wire("information")
    sale_message_1: str | None = wire("saleMsg1")
    sale_message_2: str | None = wire("saleMsg2")
    sale_message_3: str | None = wire("saleMsg3")
    expanded: str | None = wire("isExpand")
    parent_id: str | None = wire("parentId")
    representative_arrival: str | None = wire("repSegArv")
    representative_departure: str | None = wire("repSegDpt")
    title: str | None = wire("title")
    train_group_code: str | None = wire("trnGpCd")
    item_type: str | None = wire("type")
    goods_data: PassGoodsInfo | None = None
    pass_data: PassMenuData | None = None
    # 항목 안의 webData 객체에서 읽습니다.
    url: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PassMenuResponse(BaseKorailResponse):
    """정기권·패스 메뉴 목록을 담습니다."""

    items: tuple[PassMenuItem, ...] = ()


@dataclass(frozen=True)
class CommuterKindMenuResponse(BaseKorailResponse):
    """정기권 종류별 안내와 예매 조건을 담습니다."""

    after_day: str | None = wire("afterDay")
    agreement: str | None = wire("agree")
    information: str | None = wire("information")
    title: str | None = wire("title")
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

    passenger_name: str | None = wire("custNm")
    departure_station_name: str | None = wire("dptStnNm")
    arrival_station_name: str | None = wire("arvStnNm")
    run_date: str | None = wire("runDt1")
    #: 추가 사용자 여부 플래그(``apdUsrFlg``)입니다. 값의 의미는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    additional_user_flag: str | None = wire("apdUsrFlg")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    #: 이 사용 건의 발매 일자(``saleDt``)입니다.
    sale_date: str | None = wire("saleDt")
    #: 발매 일련번호(``saleSqno``)입니다.
    sale_sequence: str | None = wire("saleSqno")
    #: 발매 창구번호(``saleWctNo``)입니다.
    sale_window_no: str | None = wire("saleWctNo")


@dataclass(frozen=True)
class DiscountCardUsageListResponse(BaseKorailResponse):
    """N카드 한 장의 사용 내역 목록을 담습니다.

    응답에는 사용 내역 목록(``tkUseList``)만 있으므로 요약 필드는 없습니다."""

    items: tuple[DiscountCardUsage, ...] = ()


@dataclass(frozen=True)
class DiscountCardScheduleTrain:
    """N카드로 이용 가능한 열차 한 편을 담습니다."""

    train_no: str | None = wire("trnNo")
    train_group_code: str | None = wire("trnGpCd")
    run_date: str | None = wire("runDt")
    departure_station_code: str | None = wire("dptRsStnCd")
    departure_station_name: str | None = wire("dptRsStnNm")
    arrival_station_code: str | None = wire("arvRsStnCd")
    arrival_station_name: str | None = wire("arvRsStnNm")
    departure_construction_order: str | None = wire("dptStnConsOrdr")
    arrival_construction_order: str | None = wire("arvStnConsOrdr")
    departure_run_order: str | None = wire("dptStnRunOrdr")
    arrival_run_order: str | None = wire("arvStnRunOrdr")
    transfer_train_order_no: str | None = wire("chtnTrnOrdrNo")
    price_class_code: str | None = wire("prcClCd")
    settlement_car_type_code: str | None = wire("stlbCarTpCd")
    settlement_train_class_code: str | None = wire("stlbTrnClsfCd")
    commuter_price: str | None = wire("cmtrPrc")
    direct_transfer_division_code: str | None = wire("dirtChtnDvCd")
    detour_code: str | None = wire("dturCd")
    detour_name: str | None = wire("dturNm")
    route_code: str | None = wire("routCd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DiscountCardScheduleResponse(BaseKorailResponse):
    """N카드로 이용 가능한 열차 목록을 담습니다. 이 응답에는 다음 페이지 신호가 없습니다."""

    trains: tuple[DiscountCardScheduleTrain, ...] = ()


@dataclass(frozen=True)
class CommuterPassengerOption:
    """정기권 승객 종류의 인원·연령 범위를 담습니다."""

    commuter_usage_age_code: str | None = wire("cmtrUtlAgeCd")
    common_code_name: str | None = wire("comnCdNm")
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

    additional_service_goods_flag: str | None = wire("addSrvGdFlg")
    companion_flag: str | None = wire("cmpaFlg")
    commuter_kind_code: str | None = wire("cmtrKndCd")
    #: 정기권 이용 연령 코드(``cmtrUtlAgeCd``)입니다. 요청에 넣은 승객별 연령 코드와 다른 값이 올 수 있으므로, 요청 값이 그대로
    #: 돌아온다고 보지 마세요.
    commuter_usage_age_code: str | None = wire("cmtrUtlAgeCd")
    menu_id: str | None = wire("menuId")
    popup_message: str | None = wire("poppMsg")
    promotion_message: str | None = wire("prmoMsg")
    promotion_url: str | None = wire("prmoUrl")
    seat_attribute_code: str | None = wire("seatAttCd1")
    #: 선택할 수 있는 최소 인원(``avlPrnbFrom``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    available_passenger_count_from: int | None = 0
    #: 선택할 수 있는 최대 인원(``avlPrnbTo``)입니다. 키가 없거나 ``null``이면 ``0``, 정수로 읽을 수 없는 값이면 ``None``입니다.
    available_passenger_count_to: int | None = 0
    passenger_options: tuple[CommuterPassengerOption, ...] = ()


@dataclass(frozen=True)
class ProductCancelResponse(BaseKorailResponse):
    """여행상품 예약의 실제 취소 결과를 담습니다."""

    integrated_message_code: str | None = wire("intgMsgCd")
