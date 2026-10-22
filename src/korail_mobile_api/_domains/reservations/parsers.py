# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예약·예약 내역·장바구니 응답을 읽습니다. 변경 응답 파싱 실패 시 전체 raw와 부분 parser_raw를 보존하며 재전송하지 않습니다."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from ..._core.parsing import (
    _nested_rows,
    _nullable_scalar_fields,
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _required_integer,
    _response_fields,
    _rows,
    _strict_scalar_string,
    _validate_envelope,
    _validate_strict_read_envelope,
)
from ..._core.parsing import _response_fields as _base_fields
from ...errors import KorailProtocolError
from .models import (
    CartAddResponse,
    CartDiscountAddition,
    CartItem,
    CartListResponse,
    ReservationDetailJourney,
    ReservationHistoryJourney,
    ReservationHistoryOriginalTicket,
    ReservationHistoryPassenger,
    ReservationHistoryReservation,
    ReservationHistoryResponse,
    ReservationHistoryTicket,
    ReservationHistoryTrain,
    ReservationHoldResponse,
    ReservationJourney,
    ReservationPassengerInfo,
    ReservationSeatDetail,
    TicketDuplicationCheckResponse,
    TicketReservationDetailResponse,
)

RESERVATION_OUT_EXTRA_FIELDS: dict[str, str] = {
    "customer_management_no": "h_cust_mg_no",
    "mandatory_message": "h_msg_mndry",
    "additional_service_flag": "h_add_srv_flg",
    "disability_certificate_number": "h_hdcp_ctfc_num",
    "pre_settlement_target_flag": "h_pre_stl_tgt_flg",
    "family_info_confirm_flag": "h_fmly_info_cfm_flg",
    "special_room_fare": "h_sprm_fare",
    "issue_possible_date": "h_ise_psb_dt",
    "issue_possible_time": "h_ise_psb_tm",
}

_RESERVATION_PASSENGER_FIELDS: dict[str, str] = {
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_count": "h_psg_info_per_prnb",
    "discount_kind_code": "h_dcnt_knd_cd",
    "discount_kind_code_2": "h_dcnt_knd_cd2",
    "discount_proof_no": "h_dcsp_no",
    "discount_proof_no_2": "h_dcsp_no2",
    "delay_original_window_no": "dlayOgtkWctNo",
    "delay_original_sale_date": "dlayOgtkSaleDt",
    "delay_original_sale_sequence": "dlayOgtkSaleSqno",
    "delay_original_return_password": "dlayOgtkRetPwd",
}


def _reservation_passengers(raw: Mapping[str, Any]) -> tuple[ReservationPassengerInfo, ...]:
    """컨테이너가 없거나 모양이 다르면 빈 튜플이고 원문은 raw 에 남습니다."""
    return tuple(
        ReservationPassengerInfo(
            **_nullable_scalar_fields(row, _RESERVATION_PASSENGER_FIELDS, "reservation passenger"),
            raw=dict(row),
        )
        for row in _nested_rows(raw, "psg_infos", "psg_info")
    )


_CART_ITEM_FIELDS: dict[str, str] = {
    "service_code": "addSrvDvCd",
    "provider_name": "h_add_srv_mrk_ent_nm",
    "product_name": "h_gd_nm",
    "item_type": "h_item_dv_nm",
    "departure_date": "h_dpt_dt",
    "received_amount": "h_rcvd_amt",
    "reservation_received_date": "h_rsv_rcp_dt",
    "usage_start_date": "utlStDt",
    "usage_start_time": "utlStTm",
    "usage_close_time": "utlClsTm",
    "partner_reservation_no": "coptEntRsvNo",
    "pnr_no": "h_pnr_no",
    "lump_sum_target_no": "h_lump_stl_tgt_no",
    "customer_no": "h_cust_no",
    "virtual_reservation_no": "h_vr_rsv_no",
}

# CartInfo.java:28-61,281-392의 문자열 28개를 읽습니다. 숫자형 전송 가능성을 고려해 JSON 정수도 허용하지만 각 장바구니 필드의 실제 숫자 형식은 미확인입니다.
_CART_ITEM_SCALAR_FIELDS: dict[str, str] = {
    "item_type_code": "h_item_dv_cd",
    "provider_id": "h_add_srv_mrk_ent_id",
    "item_sequence": "h_item_sqno",
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "usage_close_date": "utlClsDt",
    "settlement_limit_time": "h_stl_lmt_tm",
    "settlement_extension_transaction_no": "h_stl_extns_tno",
    "settlement_means_allow_value": "h_stl_mns_allw_val",
    "field_settlement_division": "h_fld_stl_dv",
    "supervising_station_code": "h_spvs_rs_stn_cd",
    "filler": "h_filler",
}


@_preserve_read_raw
def parse_cart_list_response(raw: Mapping[str, Any]) -> CartListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = []
    for item in _nested_rows(raw, "cart_infos", "cart_info"):
        items.append(
            CartItem(
                **_nullable_scalar_fields(item, _CART_ITEM_FIELDS),
                **_nullable_scalar_fields(item, _CART_ITEM_SCALAR_FIELDS, "cart item"),
                # h_tk_cnt 는 String 선언입니다(CartInfo.java:51).
                ticket_count=_optional_scalar_string(item, "h_tk_cnt"),
                raw=item,
            )
        )
    return CartListResponse(items=tuple(items), **_response_fields(raw))


_RESERVATION_HISTORY_TRAIN_FIELDS: dict[str, str] = {
    "departure_station": "h_dpt_rs_stn_nm",
    "departure_time": "h_dpt_tm",
    "arrival_station": "h_arv_rs_stn_nm",
    "arrival_time": "h_arv_tm",
    "run_date": "h_run_dt",
    "train_no": "h_trn_no",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "reservation_type_code": "h_rsv_tp_cd",
    "acceptance_possible_flag": "h_acpt_ps_flg",
    "payment_flag": "h_payment_flg",
    "settlement_flag": "h_stl_flg",
    # ReservationViewOutTrainInfo.java:496 의 금액 필드.
    "reserved_amount": "h_rsv_amt",
    "pnr_no": "h_pnr_no",
    # 결제 기한 선언: ReservationViewOutTrainInfo.java:94; 채워진 기한 값은 미확인입니다.
    "payment_deadline_date": "h_ntisu_lmt_dt",
    "payment_deadline_time": "h_ntisu_lmt_tm",
    "payment_message": "h_payment_msg",
    "payment_possible_date": "h_ntisu_psb_dt",
    "prepayment_target_flag": "h_pre_stl_tgt_flg",
    "journey_sequence": "h_jrny_sqno",
}

_RESERVATION_HISTORY_TOP_FIELDS: dict[str, str] = {
    "reservation_passenger_name": "h_rsv_ps_nm",
    "phone_no": "h_tel_no",
    "reservation_limit_flag": "h_rsv_lmt_flg",
    "seatmap_flag": "h_seatmap_flg",
    "process_flag": "h_proc_flag",
    "follow_flag": "h_fllw_flag",
    "customer_no": "h_cust_no",
    "customer_division_code": "h_cust_dv_cd",
    "customer_sort_code": "h_cust_srt_cd",
    "customer_class_code": "h_cust_cl_cd",
}

_RESERVATION_HISTORY_TICKET_FIELDS: dict[str, str] = {
    "sale_date": "saleDt",
    "sale_window_no": "saleWctNo",
    "sale_sequence": "saleSqno",
    "ticket_kind_code": "tkKndCd",
    "movie_ticket_flag": "mvieTkFlg",
    "delay_discount_flag": "dlayDscpFlg",
}

_RESERVATION_HISTORY_ORIGINAL_TICKET_FIELDS: dict[str, str] = {
    "sale_date": "ogtkSaleDt",
    "window_no": "ogtkWctNo",
    "sale_sequence": "ogtkSaleSqno",
    "return_password": "ogtkRetPwd",
}

_RESERVATION_HISTORY_PASSENGER_FIELDS: dict[str, str] = {
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_count_per_info": "h_psg_info_per_prnb",
    "discount_kind_code": "h_dcnt_knd_cd",
    "discount_kind_code_2": "h_dcnt_knd_cd2",
    "discount_no": "h_dcsp_no",
    "discount_no_2": "h_dcsp_no2",
    "delay_original_window_no": "dlayOgtkWctNo",
    "delay_original_sale_date": "dlayOgtkSaleDt",
    "delay_original_sale_sequence": "dlayOgtkSaleSqno",
    "delay_original_return_password": "dlayOgtkRetPwd",
}

_RESERVATION_HISTORY_RESERVATION_FIELDS: dict[str, str] = {
    "pnr_no": "h_pnr_no",
    "total_fare": "h_tot_fare",
    "total_price": "h_tot_prc",
    "total_discount_amount": "h_tot_dcnt_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "payment_flag": "h_payment_flg",
}


def _parse_reservation_history_reservation(
    raw: Mapping[str, Any] | None,
) -> ReservationHistoryReservation | None:
    """ReservationViewOutJrnyInfo.java:55의 다섯 번째 생성자 인자입니다. @SerialName이 없어 전송 키는 보호돼 있으며 속성명 reservationOut을
    추정해 사용합니다."""
    if raw is None:
        return None
    tickets = tuple(
        ReservationHistoryTicket(
            **_nullable_scalar_fields(
                item,
                _RESERVATION_HISTORY_TICKET_FIELDS,
                "reservation history ticket",
            ),
            raw=item,
        )
        for item in _rows(raw, "tkList")
    )
    original_tickets = tuple(
        ReservationHistoryOriginalTicket(
            **_nullable_scalar_fields(
                item,
                _RESERVATION_HISTORY_ORIGINAL_TICKET_FIELDS,
                "reservation history original ticket",
            ),
            raw=item,
        )
        for item in _rows(raw, "orgTkList")
    )
    passengers = tuple(
        ReservationHistoryPassenger(
            **_nullable_scalar_fields(
                item,
                _RESERVATION_HISTORY_PASSENGER_FIELDS,
                "reservation history passenger",
            ),
            raw=item,
        )
        for item in _nested_rows(raw, "psg_infos", "psg_info")
    )
    return ReservationHistoryReservation(
        **_nullable_scalar_fields(
            raw,
            _RESERVATION_HISTORY_RESERVATION_FIELDS,
            "reservation history reservation",
        ),
        tickets=tickets,
        original_tickets=original_tickets,
        passengers=passengers,
        raw=raw,
    )


@_preserve_read_raw
def parse_reservation_history_response(
    raw: Mapping[str, Any],
) -> ReservationHistoryResponse:
    """예약 이력의 예약자 정보와 여정별 상세를 읽습니다(ReservationViewOut.java:64)."""
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"P100"}),
    )
    if empty:
        return ReservationHistoryResponse(**_response_fields(raw))
    guide_infos = _optional_mapping(raw, "guide_infos")
    guide_info = (
        _optional_scalar_string(guide_infos, "guide_info", "reservation history guide_infos")
        if guide_infos is not None
        else None
    )
    journeys: list[ReservationHistoryJourney] = []
    all_trains: list[ReservationHistoryTrain] = []
    for journey in _nested_rows(raw, "jrny_infos", "jrny_info"):
        trains: list[ReservationHistoryTrain] = []
        for train in _nested_rows(journey, "train_infos", "train_info"):
            history_train = ReservationHistoryTrain(
                **_nullable_scalar_fields(
                    train, _RESERVATION_HISTORY_TRAIN_FIELDS, "reservation history train"
                ),
                seat_count=_optional_integer(
                    train,
                    "h_tot_seat_cnt",
                    "reservation history train",
                ),
                standing_count=_optional_integer(
                    train,
                    "h_tot_stnd_cnt",
                    "reservation history train",
                ),
                raw=train,
            )
            trains.append(history_train)
            all_trains.append(history_train)
        service_infos = tuple(_nested_rows(journey, "srv_infos", "srv_info"))
        accompanying_infos = tuple(_nested_rows(journey, "acmp_infos", "acmp_info"))
        reservation = _parse_reservation_history_reservation(
            _optional_mapping(journey, "reservationOut"),
        )
        journeys.append(
            ReservationHistoryJourney(
                trains=tuple(trains),
                service_infos=service_infos,
                accompanying_infos=accompanying_infos,
                reservation=reservation,
                raw=journey,
            )
        )
    return ReservationHistoryResponse(
        **_nullable_scalar_fields(raw, _RESERVATION_HISTORY_TOP_FIELDS, "reservation history"),
        journey_count=_optional_scalar_string(raw, "h_jrny_cnt", "reservation history"),
        guide_info=guide_info,
        journeys=tuple(journeys),
        items=tuple(all_trains),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_ticket_duplication_check_response(
    raw: Mapping[str, Any],
) -> TicketDuplicationCheckResponse:
    _validate_strict_read_envelope(raw)
    return TicketDuplicationCheckResponse(
        # rsvCnt 는 String 선언입니다(TicketDupCheckOut.java:28,50).
        reservation_count=_optional_scalar_string(
            raw,
            "rsvCnt",
            "ticket duplication check",
        ),
        **_response_fields(raw),
    )


_RESERVATION_SEAT_DETAIL_FIELDS = {
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "room_class_code": "h_psrm_cl_cd",
    "room_class_name": "h_psrm_cl_nm",
    # h_psg_tp_dv_nm 은 앱 내장 응답 예시에 존재(BasketTicketDataKt.java:44)하나 ReservationOutSeatInfo.java:81 의 @SerialName
    # 에는 없습니다. 한 계정 8좌석에서 확인했지만 항상 전송된다는 보장은 없습니다.
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_type_name": "h_psg_tp_dv_nm",
    "received_amount": "h_rcvd_amt",
    "seat_price": "h_seat_prc",
    "seat_fare": "h_seat_fare",
    # ReservationOutSeatInfo.java:269 — @SerialName("h_tot_disc_amt").
    "total_discount_amount": "h_tot_disc_amt",
    "seat_group_name": "h_sgr_nm",
}

_RESERVATION_DETAIL_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "reservation_change_no": "h_rsv_chg_no",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_time": "h_arv_tm",
    # 도착일 h_arv_dt 는 도착시각과 별개입니다(ReservationOutJrnyInfo.java:86,305).
    "arrival_date": "h_arv_dt",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "train_no": "h_trn_no",
    "train_class_name": "h_trn_clsf_nm",
}

_TICKET_RESERVATION_DETAIL_FIELDS = {
    "pnr_no": "h_pnr_no",
    "window_no": "h_wct_no",
    "journey_count": "h_jrny_cnt",
    "total_fare": "h_tot_fare",
    "total_price": "h_tot_prc",
    "total_discount_amount": "h_tot_dcnt_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "payment_flag": "h_payment_flg",
}


@_preserve_read_raw
def parse_ticket_reservation_detail_response(
    raw: Mapping[str, Any],
) -> TicketReservationDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = []
    for journey in _nested_rows(
        raw,
        "jrny_infos",
        "jrny_info",
    ):
        seats = []
        for seat in _nested_rows(
            journey,
            "seat_infos",
            "seat_info",
        ):
            seats.append(
                ReservationSeatDetail(
                    **_nullable_scalar_fields(seat, _RESERVATION_SEAT_DETAIL_FIELDS, "reservation seat detail"),
                    raw=seat,
                )
            )
        journeys.append(
            ReservationDetailJourney(
                **_nullable_scalar_fields(
                    journey, _RESERVATION_DETAIL_JOURNEY_FIELDS, "reservation detail journey"
                ),
                run_date=(
                    _optional_scalar_string(journey, "h_run_dt", "reservation detail journey")
                    if "h_run_dt" in journey
                    else ""
                ),
                seats=tuple(seats),
                raw=journey,
            )
        )
    return TicketReservationDetailResponse(
        **_nullable_scalar_fields(
            raw,
            _TICKET_RESERVATION_DETAIL_FIELDS,
            "ticket reservation detail",
        ),
        journeys=tuple(journeys),
        **_nullable_scalar_fields(raw, RESERVATION_OUT_EXTRA_FIELDS, "ticket reservation detail"),
        passengers=_reservation_passengers(raw),
        **_response_fields(raw),
    )


_DIGITS_RE = re.compile(r"[0-9]+")


def _response_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    """봉투 3필드의 타입은 _parsing._envelope 가 검사하며 성공 여부는 이 모듈이 검사하지 않습니다."""
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    return dict(raw)


def _row(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(f"KORAIL {context} must be an object")
    return value


def _received_amount(
    raw: Mapping[str, Any],
    journey_rows: list[Mapping[str, Any]],
) -> str | None:
    """앱은 일반 결제에서 h_tot_rcvd_amt 를 합산합니다(PayViewModel.java:11297-11307). 번호 붙은 결제 금액으로의 최종 연결은 보호된 Bundle 키
    때문에 미확인입니다 (PaymentMethodHelper.java:113,211)."""
    declared = _strict_scalar_string(raw, "h_tot_rcvd_amt", "reservation")
    if declared is not None:
        declared = declared.strip()
        if not _DIGITS_RE.fullmatch(declared):
            declared = None
    declared_int: int | None
    if declared is None:
        declared_int = None
    else:
        try:
            declared_int = int(declared)
        except ValueError:
            declared_int = None

    summed = 0
    seats_seen = 0
    for journey in journey_rows:
        container = journey.get("seat_infos")
        if container is None:
            continue
        if not isinstance(container, Mapping):
            raise KorailProtocolError("KORAIL reservation seat_infos must be an object or null")
        seat_rows = container.get("seat_info")
        if seat_rows is None:
            continue
        if not isinstance(seat_rows, list):
            raise KorailProtocolError("KORAIL reservation seat_infos.seat_info must be a list or null")
        for seat in seat_rows:
            seat = _row(seat, "reservation seat_info row")
            amount = _strict_scalar_string(seat, "h_rcvd_amt", "reservation seat")
            if amount is None or not _DIGITS_RE.fullmatch(amount.strip()):
                return None
            try:
                value = int(amount)
            except ValueError:
                # 큰 정수의 문자열 변환 실패도 0원으로 취급하지 않습니다.
                return None
            seat_no = _optional_scalar_string(seat, "h_seat_no", "reservation seat") or ""
            if value == 0 and not seat_no.strip():
                # 예약대기 관측: 좌석번호 없는 0원 행은 정산 좌석이 아니었습니다.
                continue
            summed += value
            seats_seen += 1
    if seats_seen == 0:
        return None if declared_int is None else str(declared_int)
    seat_total = str(summed)
    # 표기 문자열이 아니라 숫자로 비교해야 같은 금액을 모순으로 오인하지 않습니다.
    if declared_int is not None and declared_int != summed:
        raise KorailProtocolError(
            "KORAIL reservation settlement amount is ambiguous: the seat rows "
            f"sum to {summed} but h_tot_rcvd_amt says {declared_int}. This "
            "library treats the per-seat sum as its primary source -- that is "
            "this package's policy, not a rule the app enforces -- so it "
            "refuses here rather than guess which amount to charge."
        )
    # 0 채움 없는 정산액 반환은 앱 재현이 아닌 라이브러리 정책입니다. 7.0.6 에는 번호 붙은 hidMnsStlAmt1 이 평문 0건이고 번호 없는
    # hidMnsStlAmt(ReservationPaymentInStlInfo, PaymentMethod)만 있습니다. hidMnsStlAmt<N> 으로 가는 마지막 단계는 보호돼 있습니다.
    return seat_total


_RESERVATION_HOLD_REQUIRED_FIELDS = {
    "pnr_no": "h_pnr_no",
    "journey_count": "h_jrny_cnt",
    "window_no": "h_wct_no",
    "temporary_job_sequence_1": "h_tmp_job_sqno1",
    "temporary_job_sequence_2": "h_tmp_job_sqno2",
}

_RESERVATION_HOLD_FIELDS = {
    "payment_flag": "h_payment_flg",
    "payment_message": "h_payment_msg",
    "payment_deadline_message": "h_pay_limit_msg",
    "payment_deadline_notice": "h_ntisu_lmt",
    "payment_deadline_date": "h_ntisu_lmt_dt",
    "payment_deadline_time": "h_ntisu_lmt_tm",
    "total_fare": "h_tot_fare",
    "total_price": "h_tot_prc",
    "total_discount_amount": "h_tot_dcnt_amt",
}

_RESERVATION_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_time": "h_arv_tm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "train_no": "h_trn_no",
    "arrival_date": "h_arv_dt",
}


@_preserve_read_raw
def parse_reservation_hold_response(
    raw: Mapping[str, Any],
) -> ReservationHoldResponse:
    """여정·정산값은 엄격히 검사하되 성공 여부는 재검사하지 않습니다. 직접 호출자는 str_result·h_msg_cd 를 확인하고, 파싱 실패만 보고 다시 요청하지 마십시오 — 예약이
    이미 생성됐을 수 있습니다."""
    copied = _response_mapping(raw)
    journeys_container = copied.get("jrny_infos")
    if journeys_container is None:
        journey_rows: list[Any] = []
    elif isinstance(journeys_container, Mapping):
        value = journeys_container.get("jrny_info")
        if value is None:
            journey_rows = []
        elif isinstance(value, list):
            journey_rows = value
        else:
            raise KorailProtocolError("KORAIL reservation jrny_infos.jrny_info must be a list or null")
    else:
        raise KorailProtocolError("KORAIL reservation jrny_infos must be an object or null")

    journeys: list[ReservationJourney] = []
    for value in journey_rows:
        row = dict(_row(value, "reservation journey"))
        journeys.append(
            ReservationJourney(
                **_nullable_scalar_fields(row, _RESERVATION_JOURNEY_FIELDS, "reservation journey"),
                reservation_change_no=_strict_scalar_string(row, "h_rsv_chg_no", "reservation journey"),
                raw=row,
            )
        )

    required: dict[str, Any] = {
        attr: _strict_scalar_string(copied, wire_key, "reservation")
        for attr, wire_key in _RESERVATION_HOLD_REQUIRED_FIELDS.items()
    }
    return ReservationHoldResponse(
        **_base_fields(copied),
        **required,
        **_nullable_scalar_fields(copied, _RESERVATION_HOLD_FIELDS, "reservation"),
        received_amount=_received_amount(
            copied,
            [journey.raw for journey in journeys],
        ),
        journeys=tuple(journeys),
        **_nullable_scalar_fields(copied, RESERVATION_OUT_EXTRA_FIELDS, "reservation"),
        passengers=_reservation_passengers(copied),
    )


@_preserve_read_raw
def parse_existing_reservation_hold_response(
    raw: Mapping[str, object],
    *,
    pnr_no: str,
) -> ReservationHoldResponse:
    """예약 상세 원문을 카드 결제용 홀드로 읽습니다. 검증 실패 시 값을 추측하지 않습니다.

    ReservationList도 ReservationOut을 반환합니다(MyReservationViewModel.java:1280-1302).
    2026-09-29 실서버 상세는 h_payment_flg를 생략했습니다. 누락은 그대로 보존하고, 명시된
    플래그만 Y인지 검사합니다. 기존 예약 생성 응답 파서의 관용 규칙은 바꾸지 않습니다.
    """
    try:
        hold = parse_reservation_hold_response(raw)
    except ValueError as error:
        raise KorailProtocolError("KORAIL reservation detail contains an unsupported numeric value") from error
    if hold.str_result != "SUCC" or hold.pnr_no != pnr_no:
        raise KorailProtocolError("KORAIL reservation detail must be successful and match the requested PNR")
    if not hold.window_no or not hold.window_no.strip():
        raise KorailProtocolError("KORAIL reservation detail is missing its payment window number")
    if "h_payment_flg" in raw and hold.payment_flag != "Y":
        raise KorailProtocolError("KORAIL existing reservation h_payment_flg must be Y when present")

    count = _required_integer(raw, "h_jrny_cnt", "existing reservation")
    if count < 1 or count != len(hold.journeys):
        raise KorailProtocolError("KORAIL reservation detail has missing or inconsistent journey rows")
    # 총액이 아예 없으면 좌석 합을 쓸 수 있지만, 명시된 잘못된 총액은 무시하지 않습니다.
    if "h_tot_rcvd_amt" in raw:
        declared = _required_integer(raw, "h_tot_rcvd_amt", "existing reservation")
        if declared < 0:
            raise KorailProtocolError("KORAIL reservation detail has a negative settlement amount")
    for journey in hold.journeys:
        container = _row(journey.raw.get("seat_infos"), "existing reservation seat_infos")
        seats = container.get("seat_info")
        if not isinstance(seats, list) or not seats:
            raise KorailProtocolError("KORAIL reservation detail requires seat rows for every journey")
        for item in seats:
            seat = _row(item, "existing reservation seat")
            amount = _required_integer(seat, "h_rcvd_amt", "existing reservation seat")
            if amount < 0:
                raise KorailProtocolError("KORAIL reservation detail has a negative seat amount")
            # 기존 홀드 파서에서 정산 좌석으로 세지 않는 예약대기 관측값입니다.
            if amount == 0 and not (_optional_scalar_string(seat, "h_seat_no") or "").strip():
                raise KorailProtocolError("KORAIL reservation detail contains an unassigned zero-amount seat")
    if hold.received_amount is None or int(hold.received_amount) <= 0:
        raise KorailProtocolError("KORAIL existing reservation requires a positive card payment amount")
    return hold


_CART_DISCOUNT_ADDITION_FIELDS = {
    "passenger_sequence_no": "h_psg_sqno",
    "duty_reference_recognition_division_code": "h_duty_ref_rcgn_ps_dv_cd",
}


def _cart_discount_additions(
    data: Mapping[str, Any],
) -> tuple[CartDiscountAddition, ...]:
    return tuple(
        CartDiscountAddition(
            raw=item,
            **_nullable_scalar_fields(item, _CART_DISCOUNT_ADDITION_FIELDS, "cart add discount row"),
        )
        for item in _nested_rows(data, "psgDiscAdd_infos", "psgDiscAdd_info")
    )


@_preserve_read_raw
def parse_cart_add_response(raw: Mapping[str, Any]) -> CartAddResponse:
    """키 근거: AddCartListOut.java:76, PsgDiscAddInfos.java:81, PsgDiscAddInfo.java:81,85."""
    data = _response_mapping(raw)
    return CartAddResponse(
        **_base_fields(data),
        discount_additions=_cart_discount_additions(data),
    )
