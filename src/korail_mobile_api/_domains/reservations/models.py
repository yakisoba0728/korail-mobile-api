# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예약·예약 내역·장바구니 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..._core.parsing import _is_list, _is_mapping, _optional_scalar_string, optional_int, strict_str, wire
from ...errors import KorailInvalidInputError, KorailProtocolError
from ..common.models import BaseKorailResponse


@dataclass(frozen=True, kw_only=True)
class ReservationPassengerInfo:
    """예약 응답의 승객 유형별 인원과 할인 정보를 담습니다."""

    passenger_type_code: str | None = wire("h_psg_tp_cd")
    passenger_count: str | None = wire("h_psg_info_per_prnb")
    discount_kind_code: str | None = wire("h_dcnt_knd_cd")
    discount_kind_code_2: str | None = wire("h_dcnt_knd_cd2")
    discount_proof_no: str | None = wire("h_dcsp_no")
    discount_proof_no_2: str | None = wire("h_dcsp_no2")
    delay_original_window_no: str | None = wire("dlayOgtkWctNo")
    delay_original_sale_date: str | None = wire("dlayOgtkSaleDt")
    delay_original_sale_sequence: str | None = wire("dlayOgtkSaleSqno")
    delay_original_return_password: str | None = wire("dlayOgtkRetPwd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class CartItem:
    """장바구니의 열차·공항버스 예약 또는 부가서비스 한 행을 담습니다."""

    additional_service_code: str | None = wire("addSrvDvCd")
    provider_name: str | None = wire("h_add_srv_mrk_ent_nm")
    product_name: str | None = wire("h_gd_nm")
    item_type: str | None = wire("h_item_dv_nm")
    departure_date: str | None = wire("h_dpt_dt")
    received_amount: str | None = wire("h_rcvd_amt")
    reservation_received_date: str | None = wire("h_rsv_rcp_dt")
    #: 승차권 매수(``h_tk_cnt``)입니다. 서버가 정수로 보내도 문자열로 담습니다.
    ticket_count: str | None = wire("h_tk_cnt")
    usage_start_date: str | None = wire("utlStDt")
    usage_start_time: str | None = wire("utlStTm")
    usage_close_time: str | None = wire("utlClsTm")
    partner_reservation_no: str | None = wire("coptEntRsvNo")
    pnr_no: str | None = wire("h_pnr_no")
    lump_sum_target_no: str | None = wire("h_lump_stl_tgt_no")
    customer_no: str | None = wire("h_cust_no")
    virtual_reservation_no: str | None = wire("h_vr_rsv_no")
    # 중첩 결제 상세 6객체는 모델링하지 않고 raw 에만 둡니다.
    item_type_code: str | None = wire("h_item_dv_cd")
    #: 부가서비스 제공 업체 ID(``h_add_srv_mrk_ent_id``)입니다. 업체 이름은 ``provider_name``에 있습니다.
    provider_id: str | None = wire("h_add_srv_mrk_ent_id")
    #: 이 행의 항목 일련번호(``h_item_sqno``)입니다.
    item_sequence: str | None = wire("h_item_sqno")
    #: 여정 일련번호(``h_jrny_sqno``)입니다.
    journey_sequence: str | None = wire("h_jrny_sqno")
    #: 여정 구분 코드(``h_jrny_tp_cd``)입니다.
    journey_type_code: str | None = wire("h_jrny_tp_cd")
    #: 이용 종료 날짜(``utlClsDt``)입니다. ``usage_close_time``과 이어 붙이면 이용 종료 일시가 됩니다.
    usage_close_date: str | None = wire("utlClsDt")
    #: 결제 기한(``h_stl_lmt_tm``)입니다. 그 자체로 기한을 나타내는 문자열입니다.
    settlement_limit_time: str | None = wire("h_stl_lmt_tm")
    #: 응답의 ``h_stl_extns_tno`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    settlement_extension_transaction_no: str | None = wire("h_stl_extns_tno")
    #: 응답의 ``h_stl_mns_allw_val`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    settlement_means_allow_value: str | None = wire("h_stl_mns_allw_val")
    #: 응답의 ``h_fld_stl_dv`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    field_settlement_division: str | None = wire("h_fld_stl_dv")
    #: 응답의 ``h_spvs_rs_stn_cd`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    supervising_station_code: str | None = wire("h_spvs_rs_stn_cd")
    #: 응답의 ``h_filler`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    filler: str | None = wire("h_filler")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class CartListResponse(BaseKorailResponse):
    """로그인 계정의 장바구니 목록을 담습니다."""

    items: tuple[CartItem, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ReservationHistoryTrain:
    """예약 이력의 열차와 결제 기한 정보를 담습니다.

    결제 기한은 ``payment_deadline_date``와 ``payment_deadline_time``에 있으며, 값이 없으면 ``None``입니다. 플래그 필드만으로는
    기한을 알 수 없습니다. 이 모델이 읽지 않는 응답 키도 있으며, 원본은 ``raw``에 남습니다."""

    departure_station_name: str | None = wire("h_dpt_rs_stn_nm")
    departure_time: str | None = wire("h_dpt_tm")
    arrival_station_name: str | None = wire("h_arv_rs_stn_nm")
    arrival_time: str | None = wire("h_arv_tm")
    run_date: str | None = wire("h_run_dt")
    train_no: str | None = wire("h_trn_no")
    train_class_code: str | None = wire("h_trn_clsf_cd")
    train_class_name: str | None = wire("h_trn_clsf_nm")
    reservation_type_code: str | None = wire("h_rsv_tp_cd")
    acceptance_possible_flag: str | None = wire("h_acpt_ps_flg")
    payment_flag: str | None = wire("h_payment_flg")
    settlement_flag: str | None = wire("h_stl_flg")
    #: 예약 금액(``h_rsv_amt``)입니다. 이 열차 행에 있는 유일한 금액 필드입니다.
    reserved_amount: str | None = wire("h_rsv_amt")
    seat_count: int | None = wire("h_tot_seat_cnt", optional_int, default=None)
    standing_count: int | None = wire("h_tot_stnd_cnt", optional_int, default=None)
    pnr_no: str | None = wire("h_pnr_no")
    payment_deadline_date: str | None = wire("h_ntisu_lmt_dt")
    payment_deadline_time: str | None = wire("h_ntisu_lmt_tm")
    payment_message: str | None = wire("h_payment_msg")
    payment_possible_date: str | None = wire("h_ntisu_psb_dt")
    pre_settlement_target_flag: str | None = wire("h_pre_stl_tgt_flg")
    journey_sequence: str | None = wire("h_jrny_sqno")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class ReservationHistoryTicket:
    """예약 이력에 중첩된 발권 승차권 한 행을 담습니다."""

    sale_date: str | None = wire("saleDt")
    sale_window_no: str | None = wire("saleWctNo")
    sale_sequence: str | None = wire("saleSqno")
    ticket_kind_code: str | None = wire("tkKndCd")
    movie_ticket_flag: str | None = wire("mvieTkFlg")
    delay_discount_flag: str | None = wire("dlayDscpFlg")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class ReservationHistoryOriginalTicket:
    """예약 이력에 중첩된 원표 한 행을 담습니다."""

    sale_date: str | None = wire("ogtkSaleDt")
    window_no: str | None = wire("ogtkWctNo")
    sale_sequence: str | None = wire("ogtkSaleSqno")
    return_password: str | None = wire("ogtkRetPwd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class ReservationHistoryPassenger:
    """예약 이력의 승객 유형별 인원·할인 정보를 담습니다."""

    passenger_type_code: str | None = wire("h_psg_tp_cd")
    passenger_count: str | None = wire("h_psg_info_per_prnb")
    discount_kind_code: str | None = wire("h_dcnt_knd_cd")
    discount_kind_code_2: str | None = wire("h_dcnt_knd_cd2")
    discount_proof_no: str | None = wire("h_dcsp_no")
    discount_proof_no_2: str | None = wire("h_dcsp_no2")
    delay_original_window_no: str | None = wire("dlayOgtkWctNo")
    delay_original_sale_date: str | None = wire("dlayOgtkSaleDt")
    delay_original_sale_sequence: str | None = wire("dlayOgtkSaleSqno")
    delay_original_return_password: str | None = wire("dlayOgtkRetPwd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class ReservationHistoryReservation:
    """예약 이력에 중첩된 예약·운임·결제 정보를 담습니다.

    이 블록은 추정한 응답 키(``reservationOut``)로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    키가 다르면 ``ReservationHistoryJourney.reservation``은 ``None``입니다."""

    pnr_no: str | None = wire("h_pnr_no")
    total_fare: str | None = wire("h_tot_fare")
    total_price: str | None = wire("h_tot_prc")
    total_discount_amount: str | None = wire("h_tot_dcnt_amt")
    total_received_amount: str | None = wire("h_tot_rcvd_amt")
    payment_flag: str | None = wire("h_payment_flg")
    tickets: tuple[ReservationHistoryTicket, ...] = ()
    original_tickets: tuple[ReservationHistoryOriginalTicket, ...] = ()
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class ReservationHistoryJourney:
    """예약 이력의 여정 한 개와 열차·부가 정보를 담습니다.

    ``service_infos``(``srv_infos``)와 ``accompanying_infos``(``acmp_infos``)는 행을 해석하지 않고 응답의 원본 매핑을 그대로
    담습니다."""

    trains: tuple[ReservationHistoryTrain, ...] = ()
    service_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    accompanying_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    reservation: ReservationHistoryReservation | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class ReservationHistoryResponse(BaseKorailResponse):
    """현재 예약 이력과 여정별 상세를 담습니다.

    남아 있는 예약이 없어 결과 코드 ``P100``의 실패 응답이 오면 예외를 발생시키지 않고, 목록이 빈 응답을 돌려줍니다."""

    reservation_passenger_name: str | None = wire("h_rsv_ps_nm")
    phone_no: str | None = wire("h_tel_no")
    reservation_limit_flag: str | None = wire("h_rsv_lmt_flg")
    seatmap_flag: str | None = wire("h_seatmap_flg")
    process_flag: str | None = wire("h_proc_flag")
    follow_flag: str | None = wire("h_fllw_flag")
    customer_no: str | None = wire("h_cust_no")
    customer_division_code: str | None = wire("h_cust_dv_cd")
    customer_sort_code: str | None = wire("h_cust_srt_cd")
    customer_class_code: str | None = wire("h_cust_cl_cd")
    journey_count: str | None = wire("h_jrny_cnt")
    guide_info: str | None = None
    journeys: tuple[ReservationHistoryJourney, ...] = ()
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        """``items``와 같은 열차 목록을 반환합니다."""
        return self.items


@dataclass(frozen=True, kw_only=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    """PNR 기준 중복 예약 확인 결과를 담습니다."""

    #: 예약 건수(``rsvCnt``)입니다. ``"0007"``처럼 서버가 보낸 문자열을 그대로 담습니다.
    reservation_count: str | None = wire("rsvCnt")


@dataclass(frozen=True, kw_only=True)
class ReservationSeatDetail:
    """예약 상세의 좌석·승객·운임 정보를 담습니다."""

    car_no: str | None = wire("h_srcar_no")
    seat_no: str | None = wire("h_seat_no")
    room_class_code: str | None = wire("h_psrm_cl_cd")
    room_class_name: str | None = wire("h_psrm_cl_nm")
    passenger_type_code: str | None = wire("h_psg_tp_cd")
    #: 좌석별 받을 금액(``h_rcvd_amt``)입니다. 예약 메서드가 돌려주는 ``ReservationHoldResponse``의 ``received_amount``는 홀드
    #: 응답에 좌석 행이 있으면 그 행들의 이 값을 합한 금액입니다.
    received_amount: str | None = wire("h_rcvd_amt")
    seat_price: str | None = wire("h_seat_prc")
    seat_fare: str | None = wire("h_seat_fare")
    total_discount_amount: str | None = wire("h_tot_disc_amt")
    seat_group_name: str | None = wire("h_sgr_nm")
    # 앱 DTO 에는 없고 실서버 응답에서만 관측한 키입니다.
    #: 승객 유형 이름(``h_psg_tp_dv_nm``)입니다. 응답에 따라 없을 수 있으며, 없으면 ``None``입니다.
    passenger_type_name: str | None = wire("h_psg_tp_dv_nm")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class ReservationDetailJourney:
    """홀드(결제 전 예약)의 여정 한 개와 좌석 상세를 담습니다."""

    journey_sequence: str | None = wire("h_jrny_sqno")
    journey_type_code: str | None = wire("h_jrny_tp_cd")
    reservation_change_no: str | None = wire("h_rsv_chg_no")
    #: 7.0.8 여정의 운행일(``h_run_dt``). 누락은 빈 문자열, 명시적 null·잘못된 타입은 None입니다.
    run_date: str | None = ""
    departure_date: str | None = wire("h_dpt_dt")
    departure_time: str | None = wire("h_dpt_tm")
    arrival_time: str | None = wire("h_arv_tm")
    arrival_date: str | None = wire("h_arv_dt")
    departure_station_name: str | None = wire("h_dpt_rs_stn_nm")
    arrival_station_name: str | None = wire("h_arv_rs_stn_nm")
    train_no: str | None = wire("h_trn_no")
    train_class_name: str | None = wire("h_trn_clsf_nm")
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR로 다시 조회한 예약의 여정·좌석·정산액을 담습니다."""

    # ReservationHoldResponse 와 같은 ReservationOut 모양입니다. 겹치는 키는 같은 읽기 규칙이고 홀드의 식별값 다섯만 strict_str 입니다.
    pnr_no: str | None = wire("h_pnr_no")
    window_no: str | None = wire("h_wct_no")
    journey_count: str | None = wire("h_jrny_cnt")
    total_fare: str | None = wire("h_tot_fare")
    total_price: str | None = wire("h_tot_prc")
    total_discount_amount: str | None = wire("h_tot_dcnt_amt")
    total_received_amount: str | None = wire("h_tot_rcvd_amt")
    payment_flag: str | None = wire("h_payment_flg")
    journeys: tuple[ReservationDetailJourney, ...] = ()
    customer_management_no: str | None = wire("h_cust_mg_no")
    mandatory_message: str | None = wire("h_msg_mndry")
    additional_service_flag: str | None = wire("h_add_srv_flg")
    disability_certificate_number: str | None = wire("h_hdcp_ctfc_num")
    pre_settlement_target_flag: str | None = wire("h_pre_stl_tgt_flg")
    family_info_confirm_flag: str | None = wire("h_fmly_info_cfm_flg")
    special_room_fare: str | None = wire("h_sprm_fare")
    issue_possible_date: str | None = wire("h_ise_psb_dt")
    issue_possible_time: str | None = wire("h_ise_psb_tm")
    passengers: tuple[ReservationPassengerInfo, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ReservationJourney:
    """예약된 여정 한 개의 열차·구간·변경 식별자를 담습니다."""

    #: 여정 순번(``h_jrny_sqno``)입니다. 예약 생성 응답에는 없을 수 있으며, 그러면 ``None``입니다.
    journey_sequence: str | None = wire("h_jrny_sqno")
    reservation_change_no: str | None = wire("h_rsv_chg_no", strict_str, default=None)
    departure_date: str | None = wire("h_dpt_dt")
    departure_time: str | None = wire("h_dpt_tm")
    #: 도착일(``h_arv_dt``)입니다. 예약 응답에는 없을 수 있으며, 그러면 ``None``입니다. 밤을 넘기는 열차는 도착 시각만으로
    #: 도착일을 알 수 없습니다.
    arrival_date: str | None = wire("h_arv_dt")
    arrival_time: str | None = wire("h_arv_tm")
    departure_station_code: str | None = wire("h_dpt_rs_stn_cd")
    arrival_station_code: str | None = wire("h_arv_rs_stn_cd")
    train_no: str | None = wire("h_trn_no")
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, kw_only=True)
class HoldReference:
    """미결제 홀드를 취소할 때 쓰는 PNR·여정 식별자를 담습니다.

    ``ReservationHoldResponse.reference``로 얻거나, 응답을 읽지 못한 예약 원문(예외의 ``raw``)에서 ``from_raw``로 만듭니다.
    값은 ``cancel_unpaid_hold``가 요청 전에 검사합니다."""

    pnr_no: str
    #: 여정 수(``h_jrny_cnt``)입니다. 취소 요청에 그대로 보냅니다.
    journey_count: str
    #: 첫 여정의 순번(``h_jrny_sqno``)입니다. 없으면 취소 요청에 ``0001``을 보냅니다.
    journey_sequence: str | None = None
    #: 첫 여정의 예약 변경번호(``h_rsv_chg_no``)입니다. 없으면 취소 요청에 ``000``을 보냅니다.
    change_no: str | None = None

    @classmethod
    def from_raw(cls, raw: Mapping[str, object]) -> HoldReference:
        """예약 응답 원문에서 만듭니다. PNR(``h_pnr_no``)과 여정 수(``h_jrny_cnt``)만 있으면 되고, 첫 여정 값은 읽을 수 있을 때만 씁니다.

        두 값이 문자열이나 정수가 아니면 ``KorailProtocolError``가 발생합니다."""
        pnr_no = _optional_scalar_string(raw, "h_pnr_no")
        journey_count = _optional_scalar_string(raw, "h_jrny_cnt")
        if pnr_no is None or journey_count is None:
            raise KorailProtocolError("KORAIL hold reference needs h_pnr_no and h_jrny_cnt", raw=raw)
        container = raw.get("jrny_infos")
        rows = container.get("jrny_info") if _is_mapping(container) else None
        row = rows[0] if _is_list(rows) and rows else None
        first: Mapping[str, object] = row if _is_mapping(row) else {}
        return cls(
            pnr_no=pnr_no,
            journey_count=journey_count,
            journey_sequence=_optional_scalar_string(first, "h_jrny_sqno"),
            change_no=_optional_scalar_string(first, "h_rsv_chg_no"),
        )


@dataclass(frozen=True, kw_only=True)
class ReservationHoldResponse(BaseKorailResponse):
    """홀드(결제 전 예약)의 식별값과 결제 기한·금액을 담습니다.

    예약·할인 재계산 응답이나 ``get_reservation_hold``로 가져온 기존 예약을 나타냅니다.
    이 객체를 받았다는 것만으로 예약이 성공했다고 보장하지 않으므로 응답 상태(``str_result``)와 ``pnr_no``를 확인하세요.
    결제할 금액은 ``received_amount``입니다."""

    pnr_no: str | None = wire("h_pnr_no", strict_str, default=None)
    journey_count: str | None = wire("h_jrny_cnt", strict_str, default=None)
    window_no: str | None = wire("h_wct_no", strict_str, default=None)
    temporary_job_sequence_1: str | None = wire("h_tmp_job_sqno1", strict_str, default=None)
    temporary_job_sequence_2: str | None = wire("h_tmp_job_sqno2", strict_str, default=None)
    payment_flag: str | None = wire("h_payment_flg")
    payment_message: str | None = wire("h_payment_msg")
    #: ``h_pay_limit_msg`` 값입니다. 결제 기한은 이 필드가 아니라 ``payment_deadline_date``와 ``payment_deadline_time``에
    #: 있습니다.
    payment_deadline_message: str | None = wire("h_pay_limit_msg")
    payment_deadline_notice: str | None = wire("h_ntisu_lmt")
    #: 결제 기한 날짜입니다. 앱은 이 값과 ``payment_deadline_time``을 이어 붙여 결제 기한으로 표시합니다.
    payment_deadline_date: str | None = wire("h_ntisu_lmt_dt")
    payment_deadline_time: str | None = wire("h_ntisu_lmt_tm")
    #: ``h_tot_fare`` 값입니다. 의미를 확인하지 못했습니다. 결제 금액으로는 ``received_amount``를 쓰세요.
    total_fare: str | None = wire("h_tot_fare")
    #: 앱이 표시하는 합계 금액(``h_tot_prc``)입니다. 결제에는 ``received_amount``를 쓰세요.
    total_price: str | None = wire("h_tot_prc")
    #: 결제할 금액입니다. 좌석별 금액(``h_rcvd_amt``)의 합이며, 응답의 총액(``h_tot_rcvd_amt``)과 다르면 응답을 읽을 때
    #: ``KorailProtocolError``가 발생합니다. 좌석 행이 없으면 응답의 총액을 쓰고, 좌석 금액을 읽을 수 없으면 ``None``입니다.
    received_amount: str | None = None
    journeys: tuple[ReservationJourney, ...] = ()
    total_discount_amount: str | None = wire("h_tot_dcnt_amt")
    customer_management_no: str | None = wire("h_cust_mg_no")
    mandatory_message: str | None = wire("h_msg_mndry")
    additional_service_flag: str | None = wire("h_add_srv_flg")
    disability_certificate_number: str | None = wire("h_hdcp_ctfc_num")
    pre_settlement_target_flag: str | None = wire("h_pre_stl_tgt_flg")
    family_info_confirm_flag: str | None = wire("h_fmly_info_cfm_flg")
    special_room_fare: str | None = wire("h_sprm_fare")
    issue_possible_date: str | None = wire("h_ise_psb_dt")
    issue_possible_time: str | None = wire("h_ise_psb_tm")
    passengers: tuple[ReservationPassengerInfo, ...] = ()
    # 앱은 예약대기 홀드를 결제하지 않고 대기 옵션만 저장합니다.
    #: 결제할 수 있는 홀드인지 나타냅니다. 예약대기(``STANDBY``)로 만든 홀드는 ``False``이며, ``pay_with_card``는 이런 홀드를
    #: 요청 전에 거절합니다.
    payable: bool = True

    @property
    def reference(self) -> HoldReference:
        """취소에 쓰는 PNR·여정 식별자입니다. PNR이나 여정 수가 없으면 ``KorailInvalidInputError``가 발생합니다."""
        if self.pnr_no is None or self.journey_count is None:
            raise KorailInvalidInputError("KORAIL hold reference needs a PNR and a journey count")
        first = self.journeys[0] if self.journeys else None
        return HoldReference(
            pnr_no=self.pnr_no,
            journey_count=self.journey_count,
            journey_sequence=first.journey_sequence if first is not None else None,
            change_no=first.reservation_change_no if first is not None else None,
        )


@dataclass(frozen=True, kw_only=True)
class CartDiscountAddition:
    """장바구니 추가 결과의 승객별 할인 정보를 담습니다."""

    passenger_sequence_no: str | None = wire("h_psg_sqno")
    #: ``h_duty_ref_rcgn_ps_dv_cd`` 값입니다. 의미와 가능한 값을 확인하지 못했습니다.
    duty_reference_recognition_division_code: str | None = wire("h_duty_ref_rcgn_ps_dv_cd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class CartAddResponse(BaseKorailResponse):
    """장바구니 추가 결과와 승객별 할인 목록을 담습니다.

    할인 행이 없으면 ``discount_additions``는 빈 튜플입니다."""

    discount_additions: tuple[CartDiscountAddition, ...] = ()
