# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""읽기 라우트 응답을 :mod:`korail_mobile_api.read_models` 타입으로 변환.

파서 하나가 라우트 하나를 맡습니다. 봉투 확인 후 DAO 필드만 추출하며,
원본 JSON 은 모델의 ``raw`` 에 보존됩니다.

KORAIL 은 ``String`` 선언 필드를 JSON 숫자로도 보내므로
:func:`_optional_scalar_string` 으로 양쪽을 수용합니다.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from .errors import (
    SESSION_EXPIRED_CODE,
    KorailProtocolError,
    KorailSessionExpiredError,
    classify_app_error,
)
from .models import BaseKorailResponse
from .read_models import (
    CartItem,
    CartListResponse,
    CommuterInfoResponse,
    CommuterKindMenuResponse,
    CommuterPassengerOption,
    CrewRequestListResponse,
    CrewRequestOption,
    CustomerTripInfo,
    CustomerTripInfoResponse,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DeliveryRecipientResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCardOnTicket,
    DiscountCardScheduleResponse,
    DiscountCardScheduleTrain,
    DiscountCardSection,
    DiscountCardUsage,
    DiscountCardUsageListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    IntermediateStation,
    KorailPointSummaryResponse,
    MaasServiceDetail,
    MaasServiceDetailInfo,
    MaasServiceDetailListResponse,
    MergeSeatsInquiryResponse,
    MileageHistoryEntry,
    MileageHistoryResponse,
    MultiChildDiscountTarget,
    MultiChildDiscountTargetResponse,
    OriginalTicket,
    OriginalTicketInquiryResponse,
    OriginalTicketJourney,
    OriginalTicketSeat,
    PassAgeOption,
    PassAvailabilityMainInfo,
    PassAvailabilityResponse,
    PassGoodsInfo,
    PassMenuData,
    PassMenuItem,
    PassMenuResponse,
    PassOffice,
    PassOpenDate,
    PassPassengerInfo,
    PassPassengerInfos,
    PassPeriodOption,
    PassScheduleInfo,
    PassScheduleMainInfo,
    PassScheduleResponse,
    PassScheduleTrain,
    PbpAcceptanceJourney,
    PbpAcceptanceSeat,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
    PriceFare,
    PriceFareQuoteResponse,
    ProductDetailResponse,
    ProductReservation,
    ProductReservationListResponse,
    ReceiptCashPayment,
    ReceiptPayment,
    RecentDeliveryHistoryResponse,
    RecentDeliveryRecipient,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    RefundTicketSeat,
    ReservationDetailJourney,
    ReservationHistoryJourney,
    ReservationHistoryOriginalTicket,
    ReservationHistoryPassenger,
    ReservationHistoryReservation,
    ReservationHistoryResponse,
    ReservationHistoryTicket,
    ReservationHistoryTrain,
    ReservationSeatDetail,
    SeatAssignmentScheduleResponse,
    SelfSeatChangeInfoResponse,
    SelfSeatChangeReason,
    SelfSeatChangeStation,
    ServiceStatusResponse,
    TicketDuplicationCheckResponse,
    TicketListReservation,
    TicketListResponse,
    TicketListTicket,
    TicketReceipt,
    TicketReceiptResponse,
    TicketReservationDetailResponse,
    TrainScheduleItem,
    TripChangeDateResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
)


def parse_ticket_list_response(response: BaseKorailResponse) -> TicketListResponse:
    """7.0.6 ``pnr_list`` → ``ticket_list`` 승차권 목록.

    결과가 **하나도 없을 때만** 서버가 목록 키를 ``pnr_list`` 대신
    ``reservation_list`` 로 바꿔 보냅니다(``h_msg_cd`` 는 ``WRT300005``).
    ``mode`` 와는 무관합니다 — 2026-09-22 확인: 결과가 있는 ``mode="2"`` 는
    ``pnr_list``(128행), 빈 ``mode="1"`` 과 빈 ``mode="2"`` 는 둘 다
    ``reservation_list``(0행). 빈 봉투에는 어차피 행이 없으므로 ``pnr_list``
    만 읽는 것이 맞고, ``reservation_list`` 를 덧대도 얻는 것이 없습니다.
    앱 DTO 도 ``MyTicketListOut.java:82`` 의 ``@SerialName("pnr_list")`` 하나뿐입니다.
    """
    raw = response.raw
    reservations: list[TicketListReservation] = []
    for reservation_raw in _rows(raw, "pnr_list", "ticket list", "ticket list reservation"):
        tickets: list[TicketListTicket] = []
        for ticket_raw in _rows(
            reservation_raw, "ticket_list", "ticket list", "ticket list ticket"
        ):
            train_info = tuple(
                _rows(ticket_raw, "jrn_info", "ticket list", "ticket list jrn_info")
            )
            tickets.append(
                TicketListTicket(
                    **_nullable_scalar_fields(
                        ticket_raw, _TICKET_LIST_TICKET_FIELDS, "ticket list"
                    ),
                    train_info=train_info,
                    raw=ticket_raw,
                )
            )
        # MyTicketListOutReservation.java — only ticket_list has an explicit
        # @SerialName; the rest are PROTECTED (Kotlin field names used as
        # best-effort keys). addSrvInfo (AddSrvItem) and ticketKind
        # (TicketDefine.TicketKind, an enum) are left unmodeled — they need
        # their own nested types — and stay reachable through `raw`.
        reservations.append(
            TicketListReservation(
                tickets=tuple(tickets),
                departure_datetime=_optional_string(
                    reservation_raw, "hDptDtTm", "ticket list reservation"
                ),
                ticket_kind_code=_optional_string(
                    reservation_raw, "hTkKndCd", "ticket list reservation"
                ),
                list_count=_optional_string(
                    reservation_raw, "listCnt", "ticket list reservation"
                ),
                seat_assign_count=_optional_integer(
                    reservation_raw, "seatAssignCount", "ticket list reservation"
                ),
                ticket_status=_optional_string(
                    reservation_raw, "ticketStatus", "ticket list reservation"
                ),
                is_finished=_optional_bool(
                    reservation_raw, "isFinished", "ticket list reservation"
                ),
                is_history=_optional_bool(
                    reservation_raw, "isHistory", "ticket list reservation"
                ),
                is_emergency=_optional_bool(
                    reservation_raw, "isEmergency", "ticket list reservation"
                ),
                display_ticket_name=_optional_string(
                    reservation_raw, "displayTicketName", "ticket list reservation"
                ),
                is_non_member=_optional_bool(
                    reservation_raw, "isNonMember", "ticket list reservation"
                ),
                is_transfer=_optional_bool(
                    reservation_raw, "isTransfer", "ticket list reservation"
                ),
                is_wheelchair_member=_optional_bool(
                    reservation_raw, "isWheelchairMember", "ticket list reservation"
                ),
                is_rail_police_enabled=_optional_bool(
                    reservation_raw, "isRailPoliceEnabled", "ticket list reservation"
                ),
                raw=reservation_raw,
            )
        )
    return TicketListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        reservations=tuple(reservations),
        total_count=_optional_string(raw, "h_total_cnt", "ticket list"),
    )


def _validate_envelope(
    raw: Mapping[str, Any],
    *,
    accepted_empty_codes: frozenset[str] = frozenset(),
    returned_failure_codes: frozenset[str] = frozenset(),
    allow_result_only_success: bool = False,
) -> bool:
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    # http.parse_base_response 의 것과 같은 판정을 앞에 둔다. 이 함수는 raw 를
    # 직접 받는 호출자(파서를 단위로 부르는 코드, 이 아래의 frozenset 멤버십
    # 검사 자체)가 있어 http.py 를 반드시 거치지 않으므로, 값이 무엇인지 보기
    # 전에 여기서도 따로 확인해야 한다 — 그러지 않으면 h_msg_cd 가 리스트·객체로
    # 오면 아래 ``code not in accepted_empty_codes`` 가 TypeError 로 죽는다.
    invalid = [
        name
        for name in ("h_msg_cd", "h_msg_txt", "strResult")
        if name in raw and raw[name] is not None and not isinstance(raw[name], str)
    ]
    if invalid:
        raise KorailProtocolError(
            "KORAIL response envelope fields must be strings or null: "
            f"{', '.join(invalid)}"
        )
    if "strResult" not in raw:
        raise KorailProtocolError(
            "KORAIL response omitted strResult; the protected APK default "
            "cannot be inferred for this typed read"
        )
    if allow_result_only_success and (
        "h_msg_cd" not in raw and "h_msg_txt" not in raw
    ):
        if raw["strResult"] != "SUCC":
            raise KorailProtocolError(
                "KORAIL result-only envelope requires the exact success result"
            )
        return False
    code = raw.get("h_msg_cd")
    message = raw.get("h_msg_txt")
    result = raw.get("strResult")
    if code == SESSION_EXPIRED_CODE:
        raise KorailSessionExpiredError(code, message, raw=raw)
    failed = result == "FAIL" or code == "WRC000288"
    if failed and code not in accepted_empty_codes and code not in returned_failure_codes:
        # ``accepted_empty_codes`` still wins: a per-endpoint opt-in returns an
        # empty result without raising anything, so classification never touches
        # it. Only a failure that was already going to be raised gets refined.
        raise classify_app_error(code, message, raw=raw)
    return failed


def _response_fields(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "h_msg_cd": raw.get("h_msg_cd"),
        "h_msg_txt": raw.get("h_msg_txt"),
        "str_result": raw.get("strResult"),
        "raw": raw,
    }


def _validate_strict_read_envelope(
    raw: Mapping[str, Any],
    *,
    allow_result_only_success: bool = False,
) -> None:
    _validate_envelope(
        raw,
        allow_result_only_success=allow_result_only_success,
    )
    if raw.get("strResult") != "SUCC":
        raise KorailProtocolError(
            "KORAIL strict read response strResult must be SUCC"
        )


def _optional_mapping(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> Mapping[str, Any] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be an object or null"
        )
    return value


def _optional_list(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a list or null"
        )
    return value


def _nested_rows(
    raw: Mapping[str, Any],
    outer_key: str,
    inner_key: str,
    context: str,
) -> list[Any]:
    outer = _optional_mapping(raw, outer_key, context)
    if outer is None:
        return []
    return _optional_list(outer, inner_key, context)


def _row(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(
            f"KORAIL {context} contained a non-object item"
        )
    return value


def _rows(
    data: Mapping[str, Any],
    key: str,
    context: str,
    row_context: str | None = None,
) -> Iterator[Mapping[str, Any]]:
    """``key`` 리스트의 각 항목을 객체로 검증하며 지연 순회.

    목록 조회(``_optional_list``)는 즉시 실행되고, 항목별 객체 검증
    (``_row``)은 순회 시점에 지연 실행됩니다.
    """
    row_label = row_context if row_context is not None else f"{context} {key}"
    return (_row(value, row_label) for value in _optional_list(data, key, context))


def _optional_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string or null"
        )
    return value


def _required_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str:
    """``_optional_string`` 의 필수 쪽 짝. 키가 없거나 ``None`` 이면 거부합니다.

    W4 finding: ``Seat`` 의 합성 생성자(``Seat.java:53-59``)는 다섯 필드(마스크
    31) 전부가 없으면 ``throwMissingFieldException`` 을 던집니다 — 7.0.6 이
    정상 처리하지 않는 응답 모양이므로, 이 필드들을 선택으로 읽으면 그 계약보다
    느슨해집니다.
    """
    value = data.get(key)
    if not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string"
        )
    return value


def _present_strings(
    data: Mapping[str, Any],
    keys: tuple[str, ...],
    context: str,
) -> tuple[str, ...]:
    """선택 문자열 값이 실제로 온 키들을 순서대로 모읍니다."""
    values: list[str] = []
    for key in keys:
        value = _optional_string(data, key, context)
        if value is not None:
            values.append(value)
    return tuple(values)


def _optional_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    """스칼라 필드 — JSON 문자열과 JSON 정수를 모두 수용.

    KORAIL 은 APK 가 자바 ``String`` 으로 선언한 필드를 둘 중 아무 쪽으로나
    보냅니다. 예약 응답은 여정 수를 ``h_jrny_cnt="0001"`` 로 보내는데 예약 이력은
    같은 필드를 JSON 정수 ``1`` 로 보냅니다. 같은 식으로 숫자로도 오는 필드로
    ``h_srcar_no`` 가 있습니다. 홀드를 이력에서 다시 읽는 것이 PNR 을 잃었을 때의
    복구 경로이므로 둘 다 파싱돼야 합니다.

    따옴표가 없다고 거부하면 실제 예약이 고아가 되므로, 폼 빌더가 기대하는
    문자열로 정규화하고 정말로 다른 모양인 것 — ``bool``, ``float``, 리스트,
    객체 — 만 계속 거부합니다. 인원 수 ``h_st_prnb``/``h_cls_prnb`` 는 반대로
    정수로 읽으므로 :func:`_optional_integer` 가 맡습니다.
    """
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    # `type(...) is int` on purpose: bool is an int subclass and `True` is not
    # a number KORAIL ever sends for one of these fields.
    if type(value) is int:
        return str(value)
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a string, an integer, or null"
    )


def _optional_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int | None:
    if data.get(key) is None:
        return None
    return _required_integer(data, key, context)


def _required_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    # These fields are declared Java `int` in the DAO, and Gson's
    # JsonReader.nextInt() coerces a quoted numeric string ("2") into the int,
    # so the app accepts both the number and the string form. Accept either
    # (int or ASCII-decimal string); keep rejecting null/bool/float/non-numeric.
    value = data.get(key)
    if type(value) is int:
        return value
    if (
        isinstance(value, str)
        and value
        and all("0" <= character <= "9" for character in value)
    ):
        try:
            return int(value)
        except ValueError as exc:
            raise KorailProtocolError(
                f"KORAIL {context} field {key} has an unsupported "
                "ASCII-decimal length"
            ) from exc
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be an integer or an "
        "ASCII decimal string"
    )


def _optional_bool(
    data: Mapping[str, Any],
    key: str,
    context: str,
    *,
    default: bool | None = None,
) -> bool | None:
    """kotlinx ``Boolean`` 필드를 읽습니다. 없으면 ``default``.

    기본값이 ``False`` 가 아니라 ``None`` 인 이유: 이 헬퍼를 쓰는 자리는
    전부 ``MyTicketNewList.do`` 의 예약 행인데, 그 행은 실서버에서
    ``ticket_list`` **하나만** 옵니다(2026-09-22: 예약 128행 전부). 기본이
    ``False`` 였을 때 ``is_transfer`` 같은 필드가 "환승이 아니다" 라고
    단정했지만, 실제로는 서버가 그 키를 아예 보내지 않은 것이었습니다 —
    "없음" 과 "거짓" 은 구분되어야 합니다.
    """
    value = data.get(key)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a boolean or null"
    )


def _nullable_string_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
    context: str,
) -> dict[str, str | None]:
    return {
        attribute: _optional_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
    }


def _nullable_scalar_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
    context: str,
) -> dict[str, str | None]:
    """Like :func:`_nullable_string_fields` but accepts JSON numbers too.

    See :func:`_optional_scalar_string`.
    """
    return {
        attribute: _optional_scalar_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
    }


# ─── Field maps for the first-half parsers ───────────────────────────────────

_TICKET_LIST_TICKET_FIELDS: dict[str, str] = {
    "pnr_no": "h_pnr_no",
    "sale_window_no": "h_orgtk_wct_no",
    "sale_date": "h_orgtk_sale_dt",
    "return_sale_date": "h_orgtk_ret_sale_dt",
    "sale_sequence": "h_orgtk_sale_sqno",
    "return_password": "h_orgtk_ret_pwd",
    "ticket_status_code": "h_tk_stt_cd",
    # 승차권 종류는 예약 행이 아니라 여기 있습니다. 예약 행의
    # ``hTkKndCd`` 는 @SerialName 없는 추측이었고 실서버는 보내지 않습니다
    # (2026-09-22: 예약 128행 전부 ``ticket_list`` 하나뿐). 반대로 승차권
    # 행은 131/131 이 ``h_tk_knd_cd``/``h_tk_knd_nm`` 을 싣습니다
    # (``'72'``/``'스마트티켓'``).
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    # MyTicketListOutTicket.java:92 가 선언하는 31개 @SerialName 중 아래 여섯이
    # 빠져 있었습니다. 전부 라이브 131/131행에 옵니다(2026-09-22). 특히
    # h_pbp_acep_tgt_flg 는 **이 행이 유일한 출처** 입니다 — 환불 상세
    # (refunds.SelTicketInfo)는 이 키를 보내지 않고, 앱도 여기서 읽어 상세 DTO 에
    # 주입합니다(MyTicketBaseViewModel.java:769).
    "ticket_sequence": "h_tk_sqno",
    "ticket_status_name": "h_tk_stt_nm",
    "return_possible_flag": "h_ret_psb_flg",
    "use_transaction_no": "h_use_tno",
    "notify_use_transaction_no": "h_noty_use_tno",
    "pbp_acceptance_target_flag": "h_pbp_acep_tgt_flg",
    # jrn_info 는 일부러 타입 없는 Mapping 으로 둡니다(위 parse_ticket_list_response).
    # 언젠가 타입을 붙이거든 h_srcar_no 는 반드시 _optional_scalar_string 또는
    # _optional_integer 로 읽으십시오. TicketListTrainInfo.java:47,72,284 는 이
    # 필드를 non-null String 으로 선언하지만 실서버는 **JSON 정수** 로 보냅니다
    # (2026-09-22: 138/138행). 앱 DTO 의 선언을 그대로 베껴 _optional_string 을
    # 쓰면 전 행이 KorailProtocolError 로 죽습니다.
}

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

_DEPOSIT_BANK_FIELDS: dict[str, str] = {
    "code": "dptnBankCd",
    "display_name": "dptnBankNm",
}

_DELAY_DISCOUNT_TICKET_FIELDS: dict[str, str] = {
    "fare": "h_dlay_fare",
    "original_sale_date": "h_orgtk_ret_sale_dt",
    "window_no": "h_orgtk_wct_no",
    "sale_sequence": "h_orgtk_sale_sqno",
    "return_password": "h_orgtk_ret_pwd",
    "ticket_sequence": "h_tk_sqno",
    "ticket_kind_code": "h_tk_knd_cd",
    "original_ticket_sale_date": "h_orgtk_sale_dt",
    "received_amount": "h_rcvd_amt",
    "train_class_code": "h_trn_clsf_cd",
    "room_class_code": "h_psrm_cl_cd",
    "train_no": "h_trn_no",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "ticket_status_code": "h_tk_stt_cd",
    "ticket_status_name": "h_tk_stt_nm",
    "buyer_name": "h_buy_ps_nm",
    "passenger_name": "h_abrd_ps_nm",
    "page_no": "h_page_no",
}

_DELAY_DISCOUNT_MAIN_INFO_FIELDS: dict[str, str] = {
    "current_page": "h_page_no",
    "total_pages": "h_tot_page_cnt",
    "total_count": "h_tot_cnt",
    "row_count": "h_row_cnt",
    "last_page_flag": "h_last_page_yn",
}

_CREW_REQUEST_OPTION_FIELDS: dict[str, str] = {
    "message_code": "intgMsgCd",
    "content": "prsCont",
}

_PASS_MENU_ITEM_FIELDS: dict[str, str] = {
    # ``afterDay`` 는 문자열입니다 — ``PassMenuOutItem.java:28`` 이
    # ``public final String afterDay`` 이고, 실서버도 따옴표로 보냅니다
    # (2026-09-22: ``menu_no`` ``"1"`` 25행·``"2"`` 10행 전부 str). 예전에는
    # ``_optional_integer`` 로 정수화했는데, 형제
    # :class:`~korail_mobile_api.read_models.CommuterKindMenuResponse` 는 같은
    # 키를 문자열로 두고 있어 같은 값이 경로에 따라 형이 달랐습니다. 게다가 이
    # 라우트는 빈 문자열을 흔하게 보내는데(같은 25행에서 ``detailType``·
    # ``isExpand``·``saleMsg1-3`` 등이 ``""``), ``_optional_integer`` 는
    # ``""`` 를 ``KorailProtocolError`` 로 터뜨립니다. 앱은 그 자리에서
    # ``StringExKt.safeToInt`` 로 파싱 실패 시 0을 쓰므로 예외를 내지 않습니다.
    "after_day": "afterDay",
    "agreement": "agree",
    "detail_type": "detailType",
    "detail_description": "dtlDsc",
    "enabled": "enable",
    "item_id": "id",
    "information": "information",
    "sale_message_1": "saleMsg1",
    "sale_message_2": "saleMsg2",
    "sale_message_3": "saleMsg3",
    "expanded": "isExpand",
    "parent_id": "parentId",
    "representative_arrival": "repSegArv",
    "representative_departure": "repSegDpt",
    "title": "title",
    "train_group_code": "trnGpCd",
    "item_type": "type",
}

_COMMUTER_KIND_MENU_FIELDS: dict[str, str] = {
    "after_day": "afterDay",
    "agreement": "agree",
    "information": "information",
    "title": "title",
}

_TRIP_MENU_CONTENT_FIELDS: dict[str, str] = {
    "title": "contTitle",
    "detail": "contDetail",
    # 예전 속성 이름은 content_type 이었습니다. detailType(TrGdMenuLtOutCont.java:42)
    # 은 "이 줄의 종류"를 주지 않습니다 — 라이브 60행 중 54행에 키가 없고 6행은
    # ''(2026-09-22). 이름을 와이어 키에 맞춰 형제 PassMenuItem.detail_type 과
    # 통일했습니다. 아래 passType 을 content_type 자리로 올리지 마십시오:
    # 7.0.6 에는 detailType/passType/passActive/passAgree/passInfo 를 읽는
    # 코드가 한 줄도 없습니다(APK 전수 게터 조사).
    "detail_type": "detailType",
    "active": "passActive",
    "agree": "passAgree",
    "info": "passInfo",
    "image": "contImage",
    "url": "contUrl",
    # 반대로 아래 둘은 앱이 실제로 읽는 필드입니다 —
    # PassConditionViewModel.java:1241 이 contList 를 훑으며 getCmtrKndCd() 를
    # 목표 코드와 비교하고, :1246 이 getPassData() 를 꺼냅니다.
    # menuType='P' 메뉴에만 옵니다(2026-09-22: 60행 중 6행).
    "commuter_kind_code": "cmtrKndCd",
    "pass_type": "passType",
}

_TRIP_MENU_ITEM_FIELDS: dict[str, str] = {
    "title": "menuTitle",
    "detail": "menuDetail",
    "menu_type": "menuType",
    "button": "menuBtn",
    "url": "menuUrl",
}

_PRODUCT_RESERVATION_FIELDS: dict[str, str] = {
    "product_name": "strGdNm",
    "reservation_status": "strRsvSttNm",
    "payment_deadline": "strStlDlnDt",
    "payment_status": "strStlSttCd",
    "virtual_reservation_no": "strVrRsvNo",
}

_PRODUCT_DETAIL_FIELDS: dict[str, str] = {
    "product_name": "strGdNm",
    "reservation_status": "strRsvSttNm",
    "cancellation_deadline": "strCncDlnDt",
    "cancellation_amount": "strCncRetAmt",
    "cancellation_fee": "strCncRetFee",
    "received_amount": "strRcvdAmt",
    "total_amount": "strTotStlAmt",
    "usage_period": "strUtlTrmCont",
    "virtual_reservation_no": "strVrRsvNo",
}

_RECEIPT_PAYMENT_FIELDS: dict[str, str] = {
    "payment_method": "h_stl_way_nm",
    "approval_date": "h_apv_dt",
    "account_no": "h_acnt_no",
    "approval_no": "h_apv_no",
    "card_no": "h_stl_crd_no",
    "point_no": "h_xpot_no",
}

_RECEIPT_CASH_PAYMENT_FIELDS: dict[str, str] = {
    "approval_method_name": "h_apv_mtd_nm",
    "authentication_domain_recognition_no": "h_athn_dmn_rcgn_no",
    "cash_receipt_approval_no": "h_cash_rcet_apv_no",
    "cash_receipt_transaction_division_code": "h_cash_rcet_txn_dv_cd",
}

_TICKET_RECEIPT_FIELDS: dict[str, str] = {
    "travel_date": "h_abrd_dt",
    "departure_station": "h_dpt_rs_stn_nm",
    "departure_time": "h_dpt_tm",
    "arrival_station": "h_arv_rs_stn_nm",
    "arrival_time": "h_arv_tm",
    "commuter_kind_code": "h_cmtr_knd_cd",
    "journey_type_code": "h_jrny_tp_cd",
    "printed_discount_name": "h_prt_disc_knd_nm",
    "printed_discount_kind_code": "h_prt_disc_knd_cd",
    "print_type": "h_prt_type",
    "seat_class_name": "h_psrm_cl_nm",
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    "ticket_status_code": "h_tk_stt_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "train_group_code": "h_trn_gp_cd",
    "train_no": "h_trn_no",
    "member_card_no": "h_stl_mb_crd_no",
}

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
    # ReservationViewOutTrainInfo.java:496 — the only money field on this row.
    "reserved_amount": "h_rsv_amt",
    "pnr_no": "h_pnr_no",
    # 아래 여섯은 ReservationViewOutTrainInfo.java:94 의 37개 @SerialName 중
    # 빠져 있던 것들입니다. 앞의 셋이 핵심입니다 — 미결제 홀드의 "언제까지"를
    # 말하는 값인데, payment_flag/settlement_flag 로 "결제해야 한다"만 알 수
    # 있었습니다. 이 계정에는 살아 있는 홀드가 없어(2026-09-22: h_msg_cd='P100',
    # jrny_info == []) 라이브 값은 미확인이고, 근거는 위 선언입니다.
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

# Two DTOs, each with its own field map (see TrainScheduleItem's docstring in
# read_models.py for why one shared row map used to be wrong for both):
#
# - MergeSeatsCOutTrnInfo (mergeSeatsC.do / parse_merge_seats_inquiry_response)
# - TrainScheduleOutTrainInfo (assignScheduleView.do /
#   parse_seat_assignment_schedule_response)

_MERGE_SEATS_TRAIN_FIELDS: dict[str, str] = {
    "train_no": "h_trn_no",
    "train_no_qb": "h_trn_no_qb",
    "train_sequence": "h_trn_seq",
    "train_group_code": "h_trn_gp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "shuttle_standing_open_flag": "shtmStndOpFlg",
    "run_date": "h_run_dt",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_run_order": "h_dpt_stn_run_ordr",
    "arrival_run_order": "h_arv_stn_run_ordr",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "departure_date": "h_dpt_dt",
    "arrival_date": "h_arv_dt",
    "departure_time": "h_dpt_tm",
    "departure_time_qb": "h_dpt_tm_qb",
    "arrival_time": "h_arv_tm",
    "arrival_time_qb": "h_arv_tm_qb",
    "standard_remaining_seat_count": "h_std_rest_seat_cnt",
    "general_reservation_code": "h_gen_rsv_cd",
    "general_reservation_name": "h_gen_rsv_nm",
    "remaining_standing_count": "restStndNum",
    "standing_reservation_code": "h_stnd_rsv_cd",
    "standing_reservation_name": "h_stnd_rsv_nm",
    "journey_reservation_code": "h_jrny_rsv_cd",
    "journey_reservation_name": "h_jrny_rsv_nm",
}

_TRAIN_SCHEDULE_OUT_TRAIN_FIELDS: dict[str, str] = {
    "train_no": "h_trn_no",
    "train_group_code": "h_trn_gp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "run_date": "h_run_dt",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "departure_run_order": "h_dpt_stn_run_ordr",
    "arrival_run_order": "h_arv_stn_run_ordr",
    "car_type_name": "h_car_tp_nm",
    "general_room_name": "h_gen_psrm_cl_nm",
    "special_room_name": "h_spe_psrm_cl_nm",
    "general_reservation_code": "h_gen_rsv_cd",
    "special_reservation_code": "h_spe_rsv_cd",
    "free_seat_reservation_code": "h_free_rsv_cd",
    "standing_reservation_code": "h_stnd_rsv_cd",
    # 네 개의 *_rsv_nm — TrainScheduleOutTrainInfo.java:1228/1380/1344/1196 이
    # 코드 짝과 나란히 선언하는데 이 맵에 하나도 없어, 전선에 '예약하기'/
    # '역발매중' 이 와도 전부 None 이었습니다(2026-09-22: menu_id='A1','A2'
    # 각 10행). general/standing 은 형제 mergeSeatsC 맵에는 이미 있었습니다.
    "general_reservation_name": "h_gen_rsv_nm",
    "standing_reservation_name": "h_stnd_rsv_nm",
    "special_reservation_name": "h_spe_rsv_nm",
    "free_seat_reservation_name": "h_free_rsv_nm",
    "seat_map_flag": "h_rd_seat_map_flg",
    "delay_sale_flag": "h_dlay_sale_flg",
    "wait_reservation_flag": "h_wait_rsv_flg",
    # h_rsv_psb_nm 은 이 DTO 자신의 키입니다(:1296). 내용이 메뉴에 따라 바뀌어
    # ('A1'→'예약가능', 'A2'→'15%할인'/'20%할인', 2026-09-22) 할인 라벨이 튀어
    # 나오지만 그것은 서버가 보내는 화면 문구이지 매핑 실수가 아닙니다 —
    # 다른 키로 바꾸지 마십시오.
    "reservation_possible_name": "h_rsv_psb_nm",
    "special_reservation_possible_name": "h_spe_rsv_psb_nm",
    "info_text": "h_info_txt",
    "popup_message": "h_popup_msg",
    # TrainScheduleOutTrainInfo.java:1204,1364,1468,1480 — these 4 were
    # missing from the old shared map.
    "standard_remaining_seat_count": "h_std_rest_seat_cnt",
    "first_remaining_seat_count": "h_fst_rest_seat_cnt",
    "merge_target_flag": "h_yms_apl_flg",
    "train_suspended_flag": "h_trn_sps_flg",
}

_PASS_SCHEDULE_TRAIN_FIELDS: dict[str, str] = {
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "detour_code": "h_dtour",
    "schedule_price": "h_schd_prc",
    "train_group_code": "h_trn_gp_cd",
    "train_no": "h_trn_no",
    # TrainList.java:25-70 declares 20 fields; these 12 were missing,
    # including h_run_dt — the only date on this row.
    "train_sequence": "h_trn_seq",
    "change_train_sequence": "h_chg_trn_seq",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "run_date": "h_run_dt",
    "price_class_code": "h_prc_cl_cd",
    "route_code": "h_rout_cd",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "car_type_code": "h_car_tp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "commuter_use_terminal_code": "h_cmtr_utl_trm_cd",
    "commuter_use_terminal_name": "h_cmtr_utl_trm_nm",
}

_PASS_SCHEDULE_MAIN_FIELDS: dict[str, str] = {
    "sale_window_no": "h_wct_no",
    "work_date": "h_work_dt",
    "work_time": "h_work_tm",
    "job_id": "h_job_id",
    "version_no": "h_ver_no",
    "message_code": "h_msg_cd",
    "selected_count": "h_sel_cnt",
    "total_selected_count": "h_tot_sel_cnt",
    "count_per_page": "h_cnt_per_page",
    "page_count": "h_page_cnt",
    "next_page_flag": "h_next_pg_flg",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "page_no": "h_page_no",
}

_PASS_AVAILABILITY_MAIN_FIELDS: dict[str, str] = {
    "message_code": "h_msg_cd",
    "total_count": "h_tot_cnt",
    "row_count": "h_row_cnt",
    "selected_page_no": "h_sel_pg_no",
}

_PASS_AGE_OPTION_FIELDS: dict[str, str] = {
    "commuter_age_code": "h_cmtr_utl_age_cd",
    "display_name": "h_comn_cd_nm",
    "minimum_age": "h_min_age",
    "maximum_age": "h_max_age",
}

_PASS_PERIOD_OPTION_FIELDS: dict[str, str] = {
    "commuter_period_code": "h_cmtr_utl_trm_cd",
    "display_name": "h_comn_cd_nm",
}


# ─── Composite parse helpers ─────────────────────────────────────────────────

def _parse_pass_menu_data(
    data: Mapping[str, Any] | None,
    context: str,
) -> PassMenuData | None:
    if data is None:
        return None
    age_options = tuple(
        PassAgeOption(
            **_nullable_string_fields(row, _PASS_AGE_OPTION_FIELDS, "pass age option"),
            raw=row,
        )
        for row in _rows(data, "pass_ageinfo", context)
    )
    period_options = tuple(
        PassPeriodOption(
            **_nullable_string_fields(row, _PASS_PERIOD_OPTION_FIELDS, "pass period option"),
            raw=row,
        )
        for row in _rows(data, "pass_periodinfo", context)
    )
    return PassMenuData(
        commuter_kind_code=_optional_string(data, "h_cmtr_knd_cd", context),
        station_selection=_optional_string(data, "h_select_station", context),
        age_options=age_options,
        period_options=period_options,
        raw=data,
    )


def _parse_pass_goods_info(
    data: Mapping[str, Any] | None,
    context: str,
) -> PassGoodsInfo | None:
    if data is None:
        return None
    passenger_infos_data = _optional_mapping(data, "psg_infos", context)
    passenger_infos = None
    if passenger_infos_data is not None:
        passengers = []
        for item in _rows(
            passenger_infos_data,
            "psg_info",
            "pass passenger infos",
        ):
            passengers.append(
                PassPassengerInfo(
                    # The live pass menu sends these counts as ZERO-PADDED
                    # decimal strings ("h_st_prnb": "000001", "h_cls_prnb":
                    # "000009"), never as JSON integers, so demanding a JSON
                    # integer rejected every real goods row. _optional_integer
                    # accepts both and coerces the padded string to int, which
                    # is what the int|None model field already promises.
                    h_cls_prnb=_optional_integer(
                        item,
                        "h_cls_prnb",
                        "pass passenger info",
                    ),
                    h_dcnt_knd_cd=_optional_string(
                        item,
                        "h_dcnt_knd_cd",
                        "pass passenger info",
                    ),
                    h_st_prnb=_optional_integer(
                        item,
                        "h_st_prnb",
                        "pass passenger info",
                    ),
                    raw=item,
                )
            )
        passenger_infos = PassPassengerInfos(
            h_chtn_allw_flg=_optional_string(
                passenger_infos_data,
                "h_chtn_allw_flg",
                "pass passenger infos",
            ),
            h_max_cnt=_optional_string(
                passenger_infos_data,
                "h_max_cnt",
                "pass passenger infos",
            ),
            h_min_cnt=_optional_string(
                passenger_infos_data,
                "h_min_cnt",
                "pass passenger infos",
            ),
            psg_info=tuple(passengers),
            raw=passenger_infos_data,
        )
    return PassGoodsInfo(
        h_cnd_flg_disc_no=_optional_string(
            data,
            "h_cnd_flg_disc_no",
            context,
        ),
        psg_infos=passenger_infos,
        raw=data,
    )


def parse_pass_menu_response(raw: Mapping[str, Any]) -> PassMenuResponse:
    # Live pass.passMenu.do success is result-only (no h_msg_cd/h_msg_txt).
    _validate_strict_read_envelope(raw, allow_result_only_success=True)
    items = []
    for item in _rows(raw, "list", "pass menu"):
        web_data = _optional_mapping(item, "webData", "pass menu item")
        items.append(
            PassMenuItem(
                **_nullable_string_fields(item, _PASS_MENU_ITEM_FIELDS, "pass menu item"),
                goods_data=_parse_pass_goods_info(
                    _optional_mapping(item, "goodsData", "pass menu item"),
                    "pass goods info",
                ),
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(item, "passData", "pass menu item"),
                    "pass menu data",
                ),
                url=(
                    _optional_string(web_data, "url", "pass menu web data")
                    if web_data is not None
                    else None
                ),
                raw=item,
            )
        )
    return PassMenuResponse(items=tuple(items), **_response_fields(raw))


def parse_commuter_kind_menu_response(
    raw: Mapping[str, Any],
) -> CommuterKindMenuResponse:
    _validate_strict_read_envelope(raw)
    return CommuterKindMenuResponse(
        **_nullable_string_fields(raw, _COMMUTER_KIND_MENU_FIELDS, "commuter kind menu"),
        pass_data=_parse_pass_menu_data(
            _optional_mapping(raw, "passData", "commuter kind menu"),
            "commuter kind pass data",
        ),
        **_response_fields(raw),
    )


def parse_crew_request_list_response(
    raw: Mapping[str, Any],
) -> CrewRequestListResponse:
    _validate_strict_read_envelope(raw)
    items = tuple(
        CrewRequestOption(
            **_nullable_string_fields(row, _CREW_REQUEST_OPTION_FIELDS, "crew request option"),
            raw=row,
        )
        for row in _rows(raw, "prsList", "crew request list")
    )
    return CrewRequestListResponse(items=items, **_response_fields(raw))


def parse_service_status_response(
    raw: Mapping[str, Any],
) -> ServiceStatusResponse:
    _validate_envelope(raw)
    return ServiceStatusResponse(**_response_fields(raw))


def parse_cart_list_response(raw: Mapping[str, Any]) -> CartListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = []
    for value in _nested_rows(raw, "cart_infos", "cart_info", "cart list"):
        item = _row(value, "cart list cart_info")
        items.append(
            CartItem(
                **_nullable_string_fields(item, _CART_ITEM_FIELDS, "cart item"),
                # CartInfo.java:51 declares h_tk_cnt as String, not int.
                ticket_count=_optional_string(item, "h_tk_cnt", "cart item"),
                raw=item,
            )
        )
    return CartListResponse(items=tuple(items), **_response_fields(raw))


def parse_deposit_bank_response(
    raw: Mapping[str, Any],
) -> DepositBankListResponse:
    _validate_envelope(raw)
    items = tuple(
        DepositBank(
            **_nullable_string_fields(row, _DEPOSIT_BANK_FIELDS, "deposit bank"),
            raw=row,
        )
        for row in _rows(raw, "dptnBank", "deposit bank list")
    )
    return DepositBankListResponse(items=items, **_response_fields(raw))


def parse_delay_discount_ticket_response(
    raw: Mapping[str, Any],
) -> DelayDiscountTicketListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    rows = _nested_rows(raw, "disc_infos", "disc_info", "delay discount ticket list")
    items = tuple(
        DelayDiscountTicket(
            **_nullable_string_fields(row, _DELAY_DISCOUNT_TICKET_FIELDS, "delay discount ticket"),
            raw=row,
        )
        for row in (
            _row(v, "delay discount ticket list disc_info")
            for v in rows
        )
    )
    # main_info 는 DelayDiscountViewOut.java:24,51 이 선언하지 않는 **서버 추가**
    # 블록입니다(그 DTO 는 disc_infos 하나뿐). 앱이 읽지 않으니 파서가 놓친 것이
    # 아니라 아예 없던 표면인데, 형제 DiscountCouponListResponse 는 같은 네
    # 개념을 이미 내놓고 있었습니다. 중첩 블록을 타입화하는 방식은
    # parse_pass_schedule_response 의 main_info 를 따릅니다.
    #
    # 다섯 값을 문자열로 둡니다: 와이어가 0을 채운 문자열이고
    # ('0000'/'000000000') h_last_page_yn 은 ''로 와서, 쿠폰 쪽처럼
    # _optional_integer 를 쓰면 그 빈 문자열이 KorailProtocolError 가 됩니다.
    # 이 계정에는 지연할인권이 없어 전부 0인 응답만 봤습니다(2026-09-22).
    main_info = _optional_mapping(raw, "main_info", "delay discount ticket list")
    pagination: dict[str, str | None] = {}
    if main_info is not None:
        pagination = _nullable_string_fields(
            main_info,
            _DELAY_DISCOUNT_MAIN_INFO_FIELDS,
            "delay discount ticket list main_info",
        )
    return DelayDiscountTicketListResponse(
        items=items,
        **pagination,
        **_response_fields(raw),
    )


def parse_discount_coupon_response(
    raw: Mapping[str, Any],
) -> DiscountCouponListResponse:
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"WRG000000"}),
    )
    if empty:
        return DiscountCouponListResponse(**_response_fields(raw))
    items = []
    rows = _nested_rows(
        raw,
        "coupon_infos",
        "coupon_info",
        "discount coupon list",
    )
    for value in rows:
        item = _row(value, "discount coupon list coupon_info")
        discount_values = _present_strings(
            item,
            (
                "h_disc_rt_amt_dv_cd",
                "h_inwk_fare_disc_rt_amt",
                "h_inwk_prc_disc_rt_amt",
                "h_wknd_fare_disc_rt_amt",
                "h_wknd_prc_disc_rt_amt",
            ),
            "discount coupon",
        )
        remarks = _present_strings(
            item,
            ("h_rmk_1_cont", "h_rmk_2_cont", "h_rmk_3_cont"),
            "discount coupon",
        )
        items.append(
            DiscountCoupon(
                guide=_optional_string(item, "guide", "discount coupon"),
                start_date=_optional_string(
                    item, "h_fdcert_mg_st_dt", "discount coupon"
                ),
                expiration_date=_optional_string(
                    item, "h_fdcert_mg_cls_dt", "discount coupon"
                ),
                discount_kind_code=_optional_string(
                    item, "h_dscp_knd_cd", "discount coupon"
                ),
                discount_values=discount_values,
                remarks=remarks,
                coupon_no=_optional_string(
                    item, "h_cpn_no", "discount coupon"
                ),
                raw=item,
            )
        )
    return DiscountCouponListResponse(
        items=tuple(items),
        current_page=_optional_integer(raw, "h_page_no", "coupon response"),
        total_pages=_optional_integer(
            raw, "h_tot_page_cnt", "coupon response"
        ),
        total_count=_optional_string(raw, "h_tot_cnt", "coupon response"),
        row_count=_optional_string(raw, "h_row_cnt", "coupon response"),
        **_response_fields(raw),
    )


def parse_pass_availability_response(
    raw: Mapping[str, Any],
) -> PassAvailabilityResponse:
    # A live pass.passInfoList success nests its code as main_info.h_msg_cd and
    # leaves the top level with strResult only, so the top-level envelope check
    # rejected every successful response. Same result-only accommodation as
    # parse_pass_menu_response.
    _validate_envelope(raw, allow_result_only_success=True)
    # PassInfo.java:92,96,100 은 세 필드를 선언하는데 예전에는 h_use_open_dt 만
    # 뽑아 날짜 문자열 튜플로 납작하게 만들고 h_pnr_no/h_item_sqno 를 버렸습니다
    # — 같은 응답의 wct_info 로 만드는 PassOffice 는 raw 를 들고 있는데 이쪽만
    # 그렇지 않았습니다. open_dates 는 그대로 두고(공개 튜플의 원소 형을 바꾸는
    # 것은 파괴적 변경입니다) 세 값을 다 담은 pass_info 를 나란히 놓습니다.
    open_dates = []
    pass_rows = []
    for item in _rows(raw, "pass_info", "pass availability"):
        date = _optional_string(item, "h_use_open_dt", "pass date")
        if date is not None:
            open_dates.append(date)
        pass_rows.append(
            PassOpenDate(
                open_date=date,
                item_sequence=_optional_string(item, "h_item_sqno", "pass date"),
                pnr_no=_optional_string(item, "h_pnr_no", "pass date"),
                raw=item,
            )
        )
    ticket_issue_dates = []
    for item in _rows(raw, "ticket_info", "pass availability"):
        date = _optional_string(item, "h_ise_dt2", "ticket issue date")
        if date is not None:
            ticket_issue_dates.append(date)
    offices = []
    for item in _rows(raw, "wct_info", "pass availability"):
        offices.append(
            PassOffice(
                code=_optional_string(item, "eng_cd_val", "pass office"),
                display_name=_optional_string(
                    item, "kor_cd_val", "pass office"
                ),
                raw=item,
            )
        )
    # main_info(PassInfoListOut.java:115 → MainInfo.java:103,107,111,115)는 이
    # 라우트의 유일한 상태 코드가 사는 곳입니다 — 최상위 봉투에는 h_msg_cd 가
    # 아예 오지 않습니다(2026-09-22: 입력 29종 전부). 예전에는 raw 로만 닿을 수
    # 있었습니다.
    #
    # IRZ000005("조회할 자료가 없습니다")를 KorailNoResultsError 로 올리지는
    # 않습니다. 형제 라우트들이 ERR000100 에 올리는 것은 strResult 가 'FAIL'
    # 이기 때문인데, 여기서는 'SUCC' 로 오고 앱도 성공으로 봅니다:
    # PassInfoListOut 은 isSuccess() 를 재정의하지 않고
    # CommonOut.isSuccess()→commonFail()(CommonOut.java:455-463)은 strResult 만
    # 봅니다. 두 소비자(PeriodTicketViewModel.java:796,
    # PassConditionViewModel.java:904)도 isSuccess() 뒤에 pass_info 가 비었는지로
    # 분기하고(:797-800, :910,927) main_info 는 읽지 않습니다 — MainInfo 를
    # 참조하는 파일은 디컴파일 전체에서 PassInfoListOut 과 그 serializer 뿐입니다.
    # 성공 봉투를 예외로 바꾸면 앱보다 엄격해지고, 채워진 응답의 IRZ000001 까지
    # 봉투 코드 자리로 끌어올리게 됩니다. 코드가 필요하면
    # response.main_info.message_code 를 보십시오.
    main_raw = _optional_mapping(raw, "main_info", "pass availability")
    main_info = (
        PassAvailabilityMainInfo(
            **_nullable_string_fields(
                main_raw, _PASS_AVAILABILITY_MAIN_FIELDS, "pass availability main info"
            ),
            raw=main_raw,
        )
        if main_raw is not None
        else None
    )
    return PassAvailabilityResponse(
        open_dates=tuple(open_dates),
        ticket_issue_dates=tuple(ticket_issue_dates),
        offices=tuple(offices),
        pass_info=tuple(pass_rows),
        main_info=main_info,
        **_response_fields(raw),
    )


def parse_trip_menu_response(raw: Mapping[str, Any]) -> TripMenuResponse:
    _validate_envelope(raw)
    items = []
    for item in _rows(raw, "menuList", "trip menu"):
        contents = tuple(
            TripMenuContent(
                **_nullable_string_fields(row, _TRIP_MENU_CONTENT_FIELDS, "trip menu content"),
                # TrGdMenuLtOutCont.java:45 passData → TrGdMenuLtOutPass.java:29-35.
                # 정기권 메뉴·종류 라우트가 싣는 것과 같은 모양이라 같은 헬퍼를
                # 씁니다.
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(row, "passData", "trip menu content"),
                    "trip menu pass data",
                ),
                raw=row,
            )
            for row in _rows(item, "contList", "trip menu")
        )
        items.append(
            TripMenuItem(
                **_nullable_string_fields(item, _TRIP_MENU_ITEM_FIELDS, "trip menu item"),
                # contCount 는 TrGdMenuLtOutMenu.java:27 의 선언이 String 인데
                # 실서버는 JSON 숫자로 보냅니다(2026-09-22: 11/6/6/4/3). 그래서
                # 문자열 필드 맵에 넣지 않고 _optional_integer 로 읽습니다 —
                # 정수와 ASCII 10진 문자열을 모두 받습니다.
                content_count=_optional_integer(item, "contCount", "trip menu item"),
                contents=contents,
                raw=item,
            )
        )
    return TripMenuResponse(
        items=tuple(items),
        popup_message=_optional_string(raw, "poppMsg", "trip menu response"),
        **_response_fields(raw),
    )


def parse_product_reservation_list_response(
    raw: Mapping[str, Any],
) -> ProductReservationListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    main = _optional_mapping(raw, "mainInfo", "product reservation list")
    if main is None:
        return ProductReservationListResponse(**_response_fields(raw))
    items = tuple(
        ProductReservation(
            **_nullable_string_fields(row, _PRODUCT_RESERVATION_FIELDS, "product reservation"),
            raw=row,
        )
        for row in _rows(main, "entity", "product reservation list")
    )
    return ProductReservationListResponse(
        items=items,
        total_count=_optional_integer(main, "strTotCnt", "product reservation list"),
        **_response_fields(raw),
    )


def parse_product_detail_response(
    raw: Mapping[str, Any],
) -> ProductDetailResponse:
    _validate_envelope(raw)
    main = _optional_mapping(raw, "mainInfo", "product detail")
    if main is None:
        return ProductDetailResponse(**_response_fields(raw))
    included_items = []
    for item in _rows(main, "entityOne", "product detail"):
        name = _optional_string(item, "strGdConsItmNm", "included item")
        if name is not None:
            included_items.append(name)
    return ProductDetailResponse(
        **_nullable_string_fields(main, _PRODUCT_DETAIL_FIELDS, "product detail"),
        included_item_names=tuple(included_items),
        detail_raw=main,
        **_response_fields(raw),
    )


def parse_ticket_receipt_response(
    raw: Mapping[str, Any],
) -> TicketReceiptResponse:
    _validate_envelope(raw)
    items = []
    rows = _nested_rows(raw, "receipt_infos", "receipt_info", "ticket receipt")
    for value in rows:
        item = _row(value, "ticket receipt receipt_info")
        payments = []
        for payment in _rows(item, "stl_info", "ticket receipt"):
            payments.append(
                ReceiptPayment(
                    **_nullable_string_fields(
                        payment, _RECEIPT_PAYMENT_FIELDS, "receipt payment"
                    ),
                    installment_months=_optional_integer(
                        payment, "h_ismt_mnth_num", "receipt payment"
                    ),
                    amount=_optional_integer(
                        payment, "h_stl_amt", "receipt payment"
                    ),
                    raw=payment,
                )
            )
        cash_receipts = []
        for cash in _rows(item, "cash_rcet_info", "ticket receipt"):
            cash_receipts.append(
                ReceiptCashPayment(
                    **_nullable_string_fields(
                        cash, _RECEIPT_CASH_PAYMENT_FIELDS,
                        "receipt cash payment",
                    ),
                    total_approved_amount=_optional_integer(
                        cash, "h_tot_apv_amt", "receipt cash payment"
                    ),
                    raw=cash,
                )
            )
        items.append(
            TicketReceipt(
                **_nullable_string_fields(item, _TICKET_RECEIPT_FIELDS, "ticket receipt"),
                passenger_counts=(
                    _optional_integer(item, "h_psg_type1_cnt", "ticket receipt"),
                    _optional_integer(item, "h_psg_type2_cnt", "ticket receipt"),
                    _optional_integer(item, "h_psg_type3_cnt", "ticket receipt"),
                ),
                received_amount=_optional_integer(item, "h_rcvd_amt", "ticket receipt"),
                card_refund_amount=_optional_integer(item, "h_crd_ret_amt", "ticket receipt"),
                refund_fee=_optional_integer(item, "h_ret_fee", "ticket receipt"),
                refund_received_amount=_optional_integer(item, "h_ret_rcvd_amt", "ticket receipt"),
                point_refund_amount=_optional_integer(item, "h_xpoint_ret_amt", "ticket receipt"),
                payments=tuple(payments),
                cash_receipts=tuple(cash_receipts),
                raw=item,
            )
        )
    return TicketReceiptResponse(items=tuple(items), **_response_fields(raw))


def _parse_reservation_history_reservation(
    raw: Mapping[str, Any] | None,
) -> ReservationHistoryReservation | None:
    """여정 옆에 매달린 ``ReservationOut`` 층을 읽습니다.

    ``ReservationViewOutJrnyInfo.java:55`` 의 다섯 번째 생성자 인자가 이
    객체인데 ``@SerialName`` 이 없어 정확한 와이어 키는 PROTECTED 입니다 —
    코틀린 필드명 ``reservationOut`` 을 최선으로 사용합니다.
    """
    if raw is None:
        return None
    tickets = tuple(
        ReservationHistoryTicket(
            **_nullable_scalar_fields(
                item, _RESERVATION_HISTORY_TICKET_FIELDS,
                "reservation history ticket",
            ),
            raw=item,
        )
        for item in _rows(raw, "tkList", "reservation history reservation")
    )
    original_tickets = tuple(
        ReservationHistoryOriginalTicket(
            **_nullable_scalar_fields(
                item, _RESERVATION_HISTORY_ORIGINAL_TICKET_FIELDS,
                "reservation history original ticket",
            ),
            raw=item,
        )
        for item in _rows(raw, "orgTkList", "reservation history reservation")
    )
    passengers_container = _optional_mapping(
        raw, "psg_infos", "reservation history reservation"
    )
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    if passengers_container is not None:
        passengers = tuple(
            ReservationHistoryPassenger(
                **_nullable_scalar_fields(
                    item, _RESERVATION_HISTORY_PASSENGER_FIELDS,
                    "reservation history passenger",
                ),
                raw=item,
            )
            for item in _rows(
                passengers_container, "psg_info",
                "reservation history passenger infos",
            )
        )
    return ReservationHistoryReservation(
        **_nullable_scalar_fields(
            raw, _RESERVATION_HISTORY_RESERVATION_FIELDS,
            "reservation history reservation",
        ),
        tickets=tickets,
        original_tickets=original_tickets,
        passengers=passengers,
        raw=raw,
    )


def parse_reservation_history_response(
    raw: Mapping[str, Any],
) -> ReservationHistoryResponse:
    """``research.reservationView.do`` — ``ReservationViewOut.java:64``.

    이전에는 ``jrny_infos[].train_infos[]`` 만 읽어 최상위 신원 필드
    (``h_rsv_ps_nm``/``h_tel_no`` 등)와 여정마다 매달린 ``srv_infos``/
    ``acmp_infos``, 그리고 그 PNR 의 실제 운임·결제·발권 내용을 담은
    ``ReservationOut`` 중첩 전체를 건너뛰었습니다.
    """
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"P100"}),
    )
    if empty:
        return ReservationHistoryResponse(**_response_fields(raw))
    guide_infos = _optional_mapping(raw, "guide_infos", "reservation history")
    guide_info = (
        _optional_string(guide_infos, "guide_info", "reservation history guide_infos")
        if guide_infos is not None
        else None
    )
    journeys: list[ReservationHistoryJourney] = []
    all_trains: list[ReservationHistoryTrain] = []
    for journey_value in _nested_rows(
        raw, "jrny_infos", "jrny_info", "reservation history"
    ):
        journey = _row(journey_value, "reservation history jrny_info")
        trains: list[ReservationHistoryTrain] = []
        for train_value in _nested_rows(
            journey, "train_infos", "train_info", "reservation history"
        ):
            train = _row(train_value, "reservation history train_info")
            history_train = ReservationHistoryTrain(
                **_nullable_string_fields(
                    train, _RESERVATION_HISTORY_TRAIN_FIELDS,
                    "reservation history train",
                ),
                seat_count=_optional_integer(
                    train, "h_tot_seat_cnt",
                    "reservation history train",
                ),
                standing_count=_optional_integer(
                    train, "h_tot_stnd_cnt",
                    "reservation history train",
                ),
                raw=train,
            )
            trains.append(history_train)
            all_trains.append(history_train)
        service_infos = tuple(
            _row(v, "reservation history srv_info")
            for v in _nested_rows(
                journey, "srv_infos", "srv_info", "reservation history journey"
            )
        )
        accompanying_infos = tuple(
            _row(v, "reservation history acmp_info")
            for v in _nested_rows(
                journey, "acmp_infos", "acmp_info", "reservation history journey"
            )
        )
        reservation = _parse_reservation_history_reservation(
            _optional_mapping(journey, "reservationOut", "reservation history jrny_info")
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
        **_nullable_string_fields(
            raw, _RESERVATION_HISTORY_TOP_FIELDS, "reservation history"
        ),
        # h_jrny_cnt is the exact cross-endpoint inconsistency
        # _optional_scalar_string's own docstring already documents: the hold
        # response sends it quoted ("0001"), reservation history sends it as
        # a bare JSON integer (1). Live-confirmed 2026-09-21 -- every history
        # row with an active journey crashed here before this fix.
        journey_count=_optional_scalar_string(raw, "h_jrny_cnt", "reservation history"),
        guide_info=guide_info,
        journeys=tuple(journeys),
        items=tuple(all_trains),
        **_response_fields(raw),
    )


def parse_free_seat_car_response(
    raw: Mapping[str, Any],
) -> FreeSeatCarResponse:
    _validate_strict_read_envelope(raw)
    return FreeSeatCarResponse(
        title=_optional_string(raw, "fresTtl", "free seat car response"),
        car_no=_optional_string(
            raw,
            "fresScarNo",
            "free seat car response",
        ),
        content=_optional_string(
            raw,
            "fresCont",
            "free seat car response",
        ),
        **_response_fields(raw),
    )


def parse_guide_seat_condition_response(
    raw: Mapping[str, Any],
) -> GuideSeatConditionResponse:
    # The helper-seat warning is the text the app shows when selection is gated.
    # Preserve this advisory as a response; unrelated failures still raise.
    _validate_envelope(raw, returned_failure_codes=frozenset({"MRR800011"}))
    if raw.get("strResult") != "SUCC" and not (
        raw.get("strResult") == "FAIL" and raw.get("h_msg_cd") == "MRR800011"
    ):
        raise KorailProtocolError(
            "KORAIL seat guidance result must be SUCC or FAIL/MRR800011"
        )
    # GuideSeatCndOut.java:29 의 "timeStamp" 에는 @SerialName 이 없지만
    # 철자는 추측이 아닙니다 -- 생성된 descriptor 의 요소 이름이 9자이고
    # (GuideSeatCndOut$$serializer.java:39) 그것이 곧 "timeStamp" 입니다.
    #
    # 다만 실서버는 이 키를 **아예 보내지 않아** time_stamp 는 언제나 None
    # 입니다(2026-09-22: 좌석속성코드 14종 전부). 키가 틀린 것이 아니라
    # 라우트가 안 싣는 것이므로, 값이 없다고 철자를 다시 고치지 마십시오.
    return GuideSeatConditionResponse(
        time_stamp=_optional_integer(raw, "timeStamp", "guide seat condition"),
        **_response_fields(raw),
    )


def _parse_train_schedule_item(
    raw: Mapping[str, Any],
    field_map: Mapping[str, str],
) -> TrainScheduleItem:
    return TrainScheduleItem(
        **_nullable_string_fields(raw, field_map, "train schedule item"),
        raw=raw,
    )


def _parse_train_schedule_container(
    raw: Mapping[str, Any],
    context: str,
    field_map: Mapping[str, str],
    *,
    read_merge_flag: bool,
) -> tuple[str | None, tuple[TrainScheduleItem, ...]]:
    """``trn_infos`` 컨테이너를 파싱합니다.

    ``read_merge_flag`` 는 호출자가 골라야 합니다 — 같은 컨테이너 키
    ``trn_infos`` 아래 실제 DTO 가 라우트마다 다릅니다.
    ``MergeSeatsCOutTrnInfos``(``:25-26``)만 ``h_merge_rsv_psb_flg`` 를
    선언하고, ``TrainScheduleOutTrainInfos``(``:25-26``)는 ``trn_info``
    하나뿐입니다. 예전에는 이 구분 없이 두 라우트 모두에서 같은 키를
    읽어, 좌석배정 시각표 쪽은 항상 죽은 읽기였습니다.
    """
    container = _optional_mapping(raw, "trn_infos", context)
    if container is None:
        return None, ()
    merge_flag = (
        _optional_string(container, "h_merge_rsv_psb_flg", context)
        if read_merge_flag
        else None
    )
    trains = tuple(
        _parse_train_schedule_item(_row(value, f"{context} trn_info"), field_map)
        for value in _optional_list(container, "trn_info", context)
    )
    return merge_flag, trains


def parse_seat_assignment_schedule_response(
    raw: Mapping[str, Any],
) -> SeatAssignmentScheduleResponse:
    """``assignScheduleView.do``.

    ``h_merge_rsv_psb_flg`` 는 읽지 않습니다 — 이 라우트의 ``trn_infos`` 는
    ``TrainScheduleOutTrainInfos``(``trn_info`` 하나뿐)이고, 그 키는
    ``MergeSeatsCOutTrnInfo``(``mergeSeatsC.do``)에 속합니다.

    다음 페이지 커서(``strJobId``, ``h_menu_id`` 등)도 같은 ``TrainScheduleOut``
    생성자(``:67``)가 함께 선언하는데, 이전에는 ``h_next_pg_flg`` 하나만
    꺼냈습니다. 같은 DTO 모양을 읽는 형제 파서
    ``parsers.py::parse_train_search_metadata`` 가 이미 이 전체 필드 집합을
    읽으므로 그 패턴을 그대로 따릅니다.
    """
    _validate_strict_read_envelope(raw)
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        "seat assignment schedule",
        _TRAIN_SCHEDULE_OUT_TRAIN_FIELDS,
        read_merge_flag=False,
    )
    return SeatAssignmentScheduleResponse(
        next_page_flag=_optional_string(
            raw,
            "h_next_pg_flg",
            "seat assignment schedule",
        ),
        merge_reservation_possible_flag=merge_flag,
        job_id=_optional_string(raw, "strJobId", "seat assignment schedule"),
        menu_id=_optional_string(raw, "h_menu_id", "seat assignment schedule"),
        goods_no=_optional_string(raw, "h_gd_no", "seat assignment schedule"),
        notice_message=_optional_string(
            raw, "h_notice_msg", "seat assignment schedule"
        ),
        first_seat_count=_optional_string(
            raw, "h_seat_cnt_first", "seat assignment schedule"
        ),
        second_seat_count=_optional_string(
            raw, "h_seat_cnt_second", "seat assignment schedule"
        ),
        agreement_text=_optional_string(
            raw, "h_agree_txt", "seat assignment schedule"
        ),
        first_departure_time=_optional_string(
            raw, "txtGoHour_first", "seat assignment schedule"
        ),
        result_count=_optional_string(raw, "h_rslt_cnt", "seat assignment schedule"),
        next_query_station_no=_optional_string(
            raw, "h_qry_st_no_next", "seat assignment schedule"
        ),
        next_train_no=_optional_string(
            raw, "h_trn_no_next", "seat assignment schedule"
        ),
        next_preceding_train_no=_optional_string(
            raw, "h_prcd_trn_no_next", "seat assignment schedule"
        ),
        next_connecting_train_no=_optional_string(
            raw, "h_ectb_trn_no_next", "seat assignment schedule"
        ),
        remaining_seat_count=_optional_string(
            raw, "h_rest_seat_cnt", "seat assignment schedule"
        ),
        trains=trains,
        **_response_fields(raw),
    )


def parse_merge_seats_inquiry_response(
    raw: Mapping[str, Any],
) -> MergeSeatsInquiryResponse:
    _validate_strict_read_envelope(raw)
    stations = []
    for station in _rows(raw, "midStnList", "merge seats inquiry"):
        stations.append(
            IntermediateStation(
                code=_optional_string(
                    station,
                    "rsStnCd",
                    "merge seats intermediate station",
                ),
                name=_optional_string(
                    station,
                    "rsStnNm",
                    "merge seats intermediate station",
                ),
                run_order=_optional_string(
                    station,
                    "runOrdr",
                    "merge seats intermediate station",
                ),
                raw=station,
            )
        )
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        "merge seats inquiry",
        _MERGE_SEATS_TRAIN_FIELDS,
        read_merge_flag=True,
    )
    return MergeSeatsInquiryResponse(
        merge_reservation_possible_flag=merge_flag,
        # MergeSeatsCOut.java:29,112 — @SerialName("runDt"), top-level. 철자는
        # 맞지만 **서버가 보내지 않습니다**: 실서버 최상위 봉투는 스칼라 5개
        # (h_msg_cd/h_msg_txt/msgCd/msgTxt/strResult)에 midStnList(:108)와
        # trn_infos(:116)뿐이고 runDt 가 없어 이 값은 항상 None 입니다
        # (2026-09-22, 20여 회 호출 전부). 운행일자는 행 단위로 옵니다 —
        # trains[i].run_date(h_run_dt)가 매번 정확히 돌아옵니다. 다른 키를
        # 찾아 "고치려" 하지 마십시오; 이 DTO 에 다른 최상위 날짜는 없습니다.
        run_date=_optional_string(raw, "runDt", "merge seats inquiry"),
        intermediate_stations=tuple(stations),
        trains=trains,
        **_response_fields(raw),
    )


def parse_pass_schedule_response(
    raw: Mapping[str, Any],
) -> PassScheduleResponse:
    # WRG000000 is a non-fatal empty result (CommutationInquiryActivity.java:182).
    empty = _validate_envelope(raw, accepted_empty_codes=frozenset({"WRG000000"}))
    if empty:
        return PassScheduleResponse(**_response_fields(raw))
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError("KORAIL pass schedule strResult must be exact SUCC")
    main_raw = _optional_mapping(raw, "main_info", "pass schedule")
    main_info = (
        PassScheduleMainInfo(
            **_nullable_string_fields(
                main_raw, _PASS_SCHEDULE_MAIN_FIELDS, "pass schedule main info"
            ),
            raw=main_raw,
        )
        if main_raw is not None
        else None
    )
    schedules = []
    for schedule in _rows(raw, "schedule_info", "pass schedule"):
        trains = tuple(
            PassScheduleTrain(
                **_nullable_string_fields(row, _PASS_SCHEDULE_TRAIN_FIELDS, "pass schedule train"),
                raw=row,
            )
            for row in _rows(
                schedule,
                "train_list",
                "pass schedule schedule_info",
                "pass schedule train_list",
            )
        )
        schedules.append(PassScheduleInfo(trains=trains, raw=schedule))
    return PassScheduleResponse(
        main_info=main_info,
        schedules=tuple(schedules),
        **_response_fields(raw),
    )


_KORAIL_POINT_SUMMARY_FIELDS = {
    "korail_point": "h_korail_point",
    "discount_coupon_count": "h_disc_coup_cnt",
    "delay_discount_count": "h_delay_cnt",
    "disability_flag": "h_hdcp_flg",
    "welfare_discount_class_name": "h_subt_dcs_cl_nm",
    "welfare_discount_class_code": "h_subt_dcs_cl_cd",
    "customer_lead_flag_name": "h_cust_lead_flg_nm",
    "phone_verified_flag": "h_cp_athn_flg",
    "email_verified_flag": "h_emil_athn_flg",
    "contact_channel_content": "h_cntc_chn_cont1",
    # MyXPointViewOut.java:43,53,54 — 플래그 쪽만 빠져 있어 비대칭이었습니다:
    # customer_lead_flag_name(h_cust_lead_flg_nm)은 있는데 h_cust_lead_flg 가
    # 없었고, disability_flag(h_hdcp_flg)는 있는데 유형 코드·이름이 없었습니다.
    # 셋 다 라이브 48키 응답에 옵니다(2026-09-22).
    "customer_lead_flag": "h_cust_lead_flg",
    "disability_type_code": "h_hdcp_tp_cd",
    "disability_type_name": "h_hdcp_tp_cd_nm",
    # 아래 넷의 네이버/카카오/구글/애플 **순서는 7.0.6 에서 미확인** 입니다
    # (read_models.KorailPointSummaryResponse 의 해당 주석 참고).
    "naver_linked_flag": "h_logn_tp_cd1",
    "kakao_linked_flag": "h_logn_tp_cd2",
    "google_linked_flag": "h_logn_tp_cd4",
    "apple_linked_flag": "h_logn_tp_cd5",
}

_MILEAGE_HISTORY_FIELDS = {
    "page_count": "pgCnt",
    "query_count": "qryCnt",
    "total_available_rail_point": "totAvlRailPontValNum",
    "total_available_rail_point_1": "totAvlRailPontValNum1",
    "total_available_affiliate_point": "totAvlAfltPontValNum",
    "total_accumulated_rail_point_1": "totAcmRailPontValNum1",
    "total_used_rail_point_1": "totUseRailPontValNum1",
    # "railNowSavePontValNum1" is deliberately NOT mapped: the 7.0.6 DTO does not
    # declare it — neither AmtSpecOut
    # (analysis/jadx/sources/com/korail/talk/network/model/AmtSpecOut.java:29-39,
    # getters :199-247 = exactly the 9 scalars above plus specList) nor its row
    # DTO AmtSpecOutSpecInfo.java:29-35.
    #
    # The older comment here called it "a phantom key that made
    # rail_now_saved_point_1 permanently None". Both halves of that were wrong
    # and the next person must not repeat them. The live server DOES send
    # railNowSavePontValNum1 on every mlg.amtSpec.do response — a 9-character
    # string on the KTX and RAIL_POINT ledgers and on every page (2026-09-22),
    # equal to totAcmRailPontValNum1 on the test account — and the mapping that
    # was removed used that exact spelling, so it was never None either. The
    # defensible reason is only the first one: the app does not model it, so
    # neither do we. It stays reachable through `raw`.
    "expiring_point_value": "delPontValNum",
    "ktx_mileage_info": "ktxMlgInfo",
}

_MILEAGE_HISTORY_ENTRY_FIELDS = {
    "departure_date": "dptDt",
    "point_division_name": "pontDvNm",
    "accrual_division_name": "mlgAcmDvCdNm",
    "receipt_division_name": "rcpDvNm",
    "point_amount": "pontAmt",
    "saved_point_value": "savePontValNum",
    "settlement_amount": "stlAmt",
}


def parse_korail_point_summary_response(
    raw: Mapping[str, Any],
) -> KorailPointSummaryResponse:
    _validate_strict_read_envelope(raw)
    return KorailPointSummaryResponse(
        # Scalar rather than string: every field on MyXPointViewOut.java:27-74 is
        # a Kotlin String, but the point totals are numbers in spirit and KORAIL
        # has been caught sending a declared-String number on several reads (see
        # _optional_scalar_string), so the tolerant reader is the safe default.
        #
        # The old comment justified this with "the app reads them back through
        # N.getInteger / N.getDecimalFormatString (MileageHistoryActivity.java:
        # 574-580)" — that file does not exist in the 7.0.6 decompile (0 hits in
        # analysis/jadx and analysis/apktool), so the rationale is the wire
        # tolerance above, not an app call site. Live, all 48 top-level keys
        # arrive as strings (2026-09-22).
        **_nullable_scalar_fields(
            raw,
            _KORAIL_POINT_SUMMARY_FIELDS,
            "korail point summary",
        ),
        **_response_fields(raw),
    )


def parse_mileage_history_response(
    raw: Mapping[str, Any],
) -> MileageHistoryResponse:
    _validate_strict_read_envelope(raw)
    entries = []
    for value in _optional_list(raw, "specList", "mileage history"):
        item = _row(value, "mileage history specList")
        entries.append(
            MileageHistoryEntry(
                **_nullable_scalar_fields(
                    item,
                    _MILEAGE_HISTORY_ENTRY_FIELDS,
                    "mileage history entry",
                ),
                raw=item,
            )
        )
    return MileageHistoryResponse(
        **_nullable_scalar_fields(
            raw,
            _MILEAGE_HISTORY_FIELDS,
            "mileage history",
        ),
        entries=tuple(entries),
        **_response_fields(raw),
    )


_DISCOUNT_CARD_USAGE_FIELDS = {
    "passenger_name": "custNm",
    "departure_station_name": "dptStnNm",
    "arrival_station_name": "arvStnNm",
    "run_date": "runDt1",
    "additional_user_flag": "apdUsrFlg",
    # NCardHistoryInfo.java:224 의 copy(runDt1, custNm, dptStnNm, arvStnNm,
    # apdUsrFlg, saleDt, saleSqno, saleWctNo) — 여덟 중 아래 셋이 빠져
    # 있었습니다. 근거는 "앱 화면이 다섯 개만 그린다" 였는데(7.0.6 에서도 맞습니다
    # — NCardHistoryScreenKt.java:431,439,526,528,301), 화면이 안 그리는 것과
    # DTO 에 없는 것은 다릅니다. @SerialName 이 하나도 없으므로 코틀린 프로퍼티
    # 이름이 곧 와이어 키입니다.
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
}

_DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS = {
    "train_no": "trnNo",
    "train_group_code": "trnGpCd",
    "run_date": "runDt",
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "arrival_station_code": "arvRsStnCd",
    "arrival_station_name": "arvRsStnNm",
    "departure_station_order": "dptStnConsOrdr",
    "arrival_station_order": "arvStnConsOrdr",
    "departure_run_order": "dptStnRunOrdr",
    "arrival_run_order": "arvStnRunOrdr",
    "transfer_train_order_no": "chtnTrnOrdrNo",
    "price_class_code": "prcClCd",
    "settlement_car_type_code": "stlbCarTpCd",
    "settlement_train_class_code": "stlbTrnClsfCd",
    "commuter_price": "cmtrPrc",
    "direct_transfer_division_code": "dirtChtnDvCd",
    "detour_code": "dturCd",
    "detour_name": "dturNm",
    "route_code": "routCd",
    # "stationStringInfo" is not read: 0 occurrences anywhere in the
    # decompile. NCardScheduleItem.java:25-49 declares no such field; the app
    # builds that Spanned label itself from the station names above.
}


def parse_discount_card_usage_response(
    raw: Mapping[str, Any],
) -> DiscountCardUsageListResponse:
    _validate_strict_read_envelope(raw)
    items = []
    for item in _rows(raw, "tkUseList", "discount card usage"):
        items.append(
            DiscountCardUsage(
                # Scalar rather than string, for the same reason the sibling
                # NCard route gives below (parse_discount_card_schedule_response):
                # this route has never been seen populated — every card number
                # tried answers ERR000100 (2026-09-22) — and saleSqno/saleWctNo
                # are zero-padded ordinals, exactly the shape KORAIL has already
                # been caught sending as a JSON number on other reads (see
                # _optional_scalar_string). The tolerant reader cannot lose data
                # a string reader would have kept.
                **_nullable_scalar_fields(
                    item,
                    _DISCOUNT_CARD_USAGE_FIELDS,
                    "discount card usage",
                ),
                raw=item,
            )
        )
    return DiscountCardUsageListResponse(
        items=tuple(items),
        **_response_fields(raw),
    )


def parse_discount_card_schedule_response(
    raw: Mapping[str, Any],
) -> DiscountCardScheduleResponse:
    _validate_strict_read_envelope(raw)
    trains = []
    for item in _rows(raw, "trnScdlList", "discount card schedule"):
        trains.append(
            DiscountCardScheduleTrain(
                # Scalar rather than string: cmtrPrc is a fare and the
                # station-order fields are ordinals, and KORAIL has already
                # been caught sending a declared-String number on three
                # separate reads (see _optional_scalar_string). This route has
                # never been seen live, so the tolerant reader is the correct
                # default rather than a concession.
                **_nullable_scalar_fields(
                    item,
                    _DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS,
                    "discount card schedule train",
                ),
                raw=item,
            )
        )
    # "fllwPgExt" is not read here: NCardScheduleOut.java:27-28 declares only
    # trnScdlList — fllwPgExt belongs to a different DTO (ScdlQryOut, the
    # limousine schedule). NCardScheduleOut has no other field, so this
    # route's server-side pagination signal is unconfirmed; following_page_exists
    # stays None rather than being wired to an always-false read. See
    # DiscountCardScheduleResponse's docstring.
    return DiscountCardScheduleResponse(
        trains=tuple(trains),
        **_response_fields(raw),
    )


_MULTI_CHILD_FIELDS = {
    "birth_date": "btdt",
    "customer_family_name": "custFmlyNm",
    "discount_kind_code": "dcntKndCd",
    "family_sequence": "fmlySqno",
    "passenger_type_code": "psgTpCd",
    "passenger_type_name": "psgTpNm",
    "room_class_code": "psrmClCd",
    "requested_discount_kind_code": "rqDcntKndCd",
}

_CUSTOMER_TRIP_FIELDS = {
    "additional_seat_attribute_code": "addSeatAttCd",
    "adult_disabled_person_count": "adltHdcpPrnb",
    "adult_count": "adulCnt",
    "arrival_station_code": "arvStnCd",
    "arrival_station_name": "arvStnNm",
    "baby_accompanying_person_count": "babyAcpnPrnb",
    "changed_at": "chgDttm",
    "changed_by": "chgUsrId",
    "child_count": "chilCnt",
    "child_disabled_person_count": "chldHdcpPrnb",
    "customer_management_no": "custMgNo",
    "day_code": "dayCd",
    "direction_seat_attribute_group_code": "dirSeatAttGpCd",
    "direct_transfer_division_code": "dirtChtnDvCd",
    "departure_station_code": "dptStnCd",
    "departure_station_name": "dptStnNm",
    "early_train_departure_time": "ectbTrnDptTm",
    "elderly_person_count": "edrPrnb",
    "included_flag": "inclFlg",
    "job_start_hour": "jobStHr",
    "location_seat_attribute_group_code": "locSeatAttGpCd",
    "media_division_code": "medDvCd",
    "room_class_code": "psrmClCd",
    "passenger_total": "ptwtTtl",
    "registered_at": "regDttm",
    "registration_sequence": "regSqno",
    "registered_by": "regUsrId",
    "trip_day_no": "tripDno",
    "train_classification_code": "trnClsfCd",
    "train_connection_flag": "trnCnecFlg",
    "train_group_code": "trnGpCd",
    "usage_day_no": "utlDno",
    # CustTripInfo.java:48 — no @SerialName (PROTECTED), Java field name used
    # as best-effort. 33rd of 33 declared fields; only one missing before.
    "goods_no": "gdNo",
}

_MAAS_DETAIL_FIELDS = {
    "additional_service_division_code": "addSrvDvCd",
    "additional_service_goods_code": "addSrvGdCd",
    "additional_service_id": "addSrvId",
    "marketing_entity_id": "addSrvMrkEntId",
    "marketing_entity_name": "addSrvMrkEntNm",
    "additional_service_name": "addSrvNm",
    "progress_status_code": "addSrvPrgSttCd",
    "request_no": "addSrvReqNo",
    "passenger_reference_content": "cgPsRefAtclCont",
    "partner_reservation_no": "coptEntRsvNo",
    "delivery_close_time": "dlivPsbClsTm",
    "delivery_start_time": "dlivPsbStTm",
    "lead_message_1": "leadMsgCont1",
    "lead_message_2": "leadMsgCont2",
    "pnr_no": "pnrNo",
    "request_date": "reqDt",
    "request_quantity": "reqQnty",
    "reservation_station_code_name": "rsStnCdNm",
    "reservation_specification_url": "rsvSpecUrl",
    "usage_close_date": "utlClsDt",
    "usage_start_date": "utlStDt",
}

_MAAS_DETAIL_INFO_FIELDS = {
    "additional_service_request_no": "addSrvReqNo",
    "booking_time": "bookTime",
    "branch_name": "branchName",
    "partner_name": "coptEntName",
    "delivery_datetime": "deliveryDtm",
    "drop_times": "dropTimes",
    "dropoff_name": "dropoffName",
    "image": "image",
    "name": "name",
    "option_name": "optionName",
    "pickup_name": "pickupName",
    "pickup_place": "pickupPlace",
    "pickup_times": "pickupTimes",
    "reservation_date": "reserveDt",
    "return_datetime": "returnDttm",
    "start_datetime": "startDttm",
    "cancel_deadline_date": "strCncDlnDt",
    "cancel_return_amount": "strCncRetAmt",
    "cancel_return_fee": "strCncRetFee",
    "goods_sequence": "strGdSqno",
    "intermediate_value": "strInt11",
    "received_amount": "strRcvdAmt",
    "reservation_status_name": "strRsvSttNm",
    "reservation_passenger_name": "strRsvpsnm",
    "settlement_deadline_date": "strStlDlnDt",
    "settlement_deadline_datetime": "strStlDlnDttm",
    "settlement_status_code": "strStlSttCd",
    "settlement_status_name": "strStlSttNm",
    "total_settlement_amount": "strTotStlAmt",
    "usage_period_content": "strUtlTrmCont",
}


def parse_multi_child_discount_target_response(
    raw: Mapping[str, Any],
) -> MultiChildDiscountTargetResponse:
    _validate_strict_read_envelope(raw)
    targets = []
    for item in _rows(raw, "fmlyList", "multi-child targets"):
        targets.append(
            MultiChildDiscountTarget(
                **_nullable_string_fields(
                    item,
                    _MULTI_CHILD_FIELDS,
                    "multi-child target",
                ),
                raw=item,
            )
        )
    return MultiChildDiscountTargetResponse(
        targets=tuple(targets),
        **_response_fields(raw),
    )


def parse_customer_trip_info_response(
    raw: Mapping[str, Any],
) -> CustomerTripInfoResponse:
    _validate_strict_read_envelope(raw)
    trips = []
    for item in _rows(raw, "mainList", "customer trip info"):
        trips.append(
            CustomerTripInfo(
                **_nullable_string_fields(
                    item,
                    _CUSTOMER_TRIP_FIELDS,
                    "customer trip info",
                ),
                raw=item,
            )
        )
    return CustomerTripInfoResponse(
        trips=tuple(trips),
        **_response_fields(raw),
    )


def parse_maas_service_detail_list_response(
    raw: Mapping[str, Any],
) -> MaasServiceDetailListResponse:
    _validate_strict_read_envelope(raw)
    details = []
    for item in _rows(raw, "addSrvList", "MaaS service details"):
        info_raw = _optional_mapping(item, "detailInfo", "MaaS service detail")
        detail_info = None
        if info_raw is not None:
            entity_one = tuple(
                _row(v, "MaaS service detail detailInfo entityOne")
                for v in _optional_list(info_raw, "entityOne", "MaaS detail info")
            )
            detail_info = MaasServiceDetailInfo(
                **_nullable_string_fields(
                    info_raw, _MAAS_DETAIL_INFO_FIELDS, "MaaS detail info"
                ),
                entity_one=entity_one,
                raw=info_raw,
            )
        details.append(
            MaasServiceDetail(
                **_nullable_string_fields(
                    item,
                    _MAAS_DETAIL_FIELDS,
                    "MaaS service detail",
                ),
                detail_info=detail_info,
                raw=item,
            )
        )
    return MaasServiceDetailListResponse(
        details=tuple(details),
        **_response_fields(raw),
    )


def parse_trip_change_date_response(
    raw: Mapping[str, Any],
) -> TripChangeDateResponse:
    _validate_strict_read_envelope(raw)
    dates = []
    for value in _optional_list(raw, "tripChgDates", "trip change dates"):
        if not isinstance(value, str):
            raise KorailProtocolError(
                "KORAIL trip change dates field tripChgDates must contain only strings"
            )
        dates.append(value)
    # "tripChgDate" (singular) is not read here: TipChgDateInquiryOut.java:28-30
    # declares only lastRunDt and the plural List<String> tripChgDates.
    # "tripChgDate" is the *request* DTO's field
    # (TipChgDateInquiryIn.java:29), not part of this response.
    return TripChangeDateResponse(
        last_run_date=_optional_string(raw, "lastRunDt", "trip change dates"),
        trip_change_dates=tuple(dates),
        **_response_fields(raw),
    )


def _primitive_json_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    # Psg.java declares these Kotlin `Int`, but the live server sends
    # zero-padded ASCII-decimal strings for at least custAgeFrom/custAgeTo/
    # psgPrnbFrom/psgPrnbTo ("0000", "0999", ...), not bare JSON integers --
    # live-confirmed 2026-09-21, every commuter-info call with a travel-pass
    # commuter_kind_code crashed here before this fix. Psg.java is a kotlinx
    # @Serializable, not Gson, but the number-vs-string tolerance is the same
    # class of problem _required_integer handles; mirrors its acceptance rule.
    value = data.get(key)
    if value is None:
        return 0
    if type(value) is int:
        return value
    if (
        isinstance(value, str)
        and value
        and all("0" <= character <= "9" for character in value)
    ):
        try:
            return int(value)
        except ValueError as exc:
            raise KorailProtocolError(
                f"KORAIL {context} field {key} has an unsupported "
                "ASCII-decimal length"
            ) from exc
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a JSON integer, an "
        "ASCII-decimal string, or null"
    )


def parse_commuter_info_response(
    raw: Mapping[str, Any],
) -> CommuterInfoResponse:
    _validate_strict_read_envelope(raw)
    passenger_options = []
    for item in _rows(raw, "psgList", "commuter info"):
        passenger_options.append(
            CommuterPassengerOption(
                commuter_usage_age_code=_optional_string(
                    item,
                    "cmtrUtlAgeCd",
                    "commuter passenger option",
                ),
                common_code_name=_optional_string(
                    item,
                    "comnCdNm",
                    "commuter passenger option",
                ),
                # Psg.java:30-31 — int custAgeFrom/custAgeTo, siblings of the
                # already-read psgPrnbFrom/psgPrnbTo below.
                customer_age_from=_primitive_json_integer(
                    item,
                    "custAgeFrom",
                    "commuter passenger option",
                ),
                customer_age_to=_primitive_json_integer(
                    item,
                    "custAgeTo",
                    "commuter passenger option",
                ),
                passenger_count_from=_primitive_json_integer(
                    item,
                    "psgPrnbFrom",
                    "commuter passenger option",
                ),
                passenger_count_to=_primitive_json_integer(
                    item,
                    "psgPrnbTo",
                    "commuter passenger option",
                ),
                raw=item,
            )
        )
    return CommuterInfoResponse(
        additional_service_goods_flag=_optional_string(
            raw,
            "addSrvGdFlg",
            "commuter info",
        ),
        companion_flag=_optional_string(raw, "cmpaFlg", "commuter info"),
        commuter_kind_code=_optional_string(
            raw,
            "cmtrKndCd",
            "commuter info",
        ),
        commuter_usage_age_code=_optional_string(
            raw,
            "cmtrUtlAgeCd",
            "commuter info",
        ),
        menu_id=_optional_string(raw, "menuId", "commuter info"),
        popup_message=_optional_string(raw, "poppMsg", "commuter info"),
        promotion_message=_optional_string(
            raw,
            "prmoMsg",
            "commuter info",
        ),
        promotion_url=_optional_string(raw, "prmoUrl", "commuter info"),
        seat_attribute_code=_optional_string(
            raw,
            "seatAttCd1",
            "commuter info",
        ),
        available_passenger_count_from=_primitive_json_integer(
            raw,
            "avlPrnbFrom",
            "commuter info",
        ),
        available_passenger_count_to=_primitive_json_integer(
            raw,
            "avlPrnbTo",
            "commuter info",
        ),
        passenger_options=tuple(passenger_options),
        **_response_fields(raw),
    )


_PRICE_FARE_FIELDS = {
    "journey_sequence": "jrnySqno",
    "room_class_name": "psrmClNm",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "total_amount": "sumAmt",
    "train_no": "trnNo",
}


def parse_price_fare_quote_response(
    raw: Mapping[str, Any],
) -> PriceFareQuoteResponse:
    _validate_strict_read_envelope(raw)
    fares = []
    for item in _rows(raw, "prcList", "price fare quote"):
        fares.append(
            PriceFare(
                **_nullable_string_fields(
                    item,
                    _PRICE_FARE_FIELDS,
                    "price fare",
                ),
                raw=item,
            )
        )
    return PriceFareQuoteResponse(
        fares=tuple(fares),
        **_response_fields(raw),
    )


_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "member_card_no": "mbCrdNo",
}

_PBP_ACCEPTANCE_TICKET_FIELDS = {
    "pnr_no": "pnrNo",
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
    "return_password": "tkRetPwd",
}

_PBP_ACCEPTANCE_JOURNEY_FIELDS = {
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "journey_type_code": "jrnyTpCd",
    "member_division_name": "mbDvNm",
    "acceptance_kind_name": "pbpAcepKndNm",
    "pbp_reservation_no": "pbpRsvNo",
    "registered_date": "regDt",
    "withdrawal_possible_flag": "wdrwPsbFlg",
}

_PBP_ACCEPTANCE_SEAT_FIELDS = {
    "passenger_type_division_name": "psgTpDvNm",
    "room_class_code": "psrmClCd",
    "room_class_name": "psrmClNm",
    "seat_no": "seatNo",
}

_RECENT_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_flag": "acepCustMgFlg",
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "acceptance_customer_phone_2": "acepCustTeln2",
    "member_card_no": "mbCrdNo",
}


def parse_delivery_recipient_response(
    raw: Mapping[str, Any],
) -> DeliveryRecipientResponse:
    _validate_strict_read_envelope(raw)
    return DeliveryRecipientResponse(
        **_nullable_string_fields(
            raw,
            _DELIVERY_RECIPIENT_FIELDS,
            "delivery recipient",
        ),
        **_response_fields(raw),
    )


def parse_ticket_duplication_check_response(
    raw: Mapping[str, Any],
) -> TicketDuplicationCheckResponse:
    _validate_strict_read_envelope(raw)
    return TicketDuplicationCheckResponse(
        # TicketDupCheckOut.java:28,50 declares rsvCnt as a kotlinx String
        # field (@SerialName("rsvCnt")), not a Java int — the old comment's
        # "Gson coerces a quoted numeric string" reasoning does not apply to
        # this DTO. Read it as a string; behavior was already neutral since
        # both "0" and 0 were previously accepted, but a future maintainer
        # trusting the old comment could otherwise drop string handling.
        reservation_count=_optional_string(
            raw,
            "rsvCnt",
            "ticket duplication check",
        ),
        **_response_fields(raw),
    )


def parse_pbp_acceptance_specification_response(
    raw: Mapping[str, Any],
) -> PbpAcceptanceSpecificationResponse:
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket in _rows(raw, "tkList", "PBP acceptance specification"):
        journeys = []
        for journey in _rows(ticket, "jrnyList", "PBP acceptance ticket"):
            seats = []
            for seat in _rows(journey, "seatList", "PBP acceptance journey"):
                seats.append(
                    PbpAcceptanceSeat(
                        # Seat.java:53-59's synthetic constructor requires all
                        # five of these fields (mask 31) -- throws
                        # MissingFieldException if any is absent. Reading them
                        # as optional would accept a response shape 7.0.6
                        # itself refuses to deserialize.
                        **{
                            attr: _required_string(seat, wire_key, "PBP acceptance seat")
                            for attr, wire_key in _PBP_ACCEPTANCE_SEAT_FIELDS.items()
                        },
                        # PbpAcepSpecDao.Seat.scarNo is Java `int`
                        # (PbpAcepSpecDao.java:102); Gson coerces a quoted
                        # numeric string, so accept both "3" and 3.
                        car_no=_required_integer(
                            seat,
                            "scarNo",
                            "PBP acceptance seat",
                        ),
                        raw=seat,
                    )
                )
            journeys.append(
                PbpAcceptanceJourney(
                    **_nullable_string_fields(
                        journey,
                        _PBP_ACCEPTANCE_JOURNEY_FIELDS,
                        "PBP acceptance journey",
                    ),
                    seats=tuple(seats),
                    raw=journey,
                )
            )
        tickets.append(
            PbpAcceptanceTicket(
                **_nullable_string_fields(
                    ticket,
                    _PBP_ACCEPTANCE_TICKET_FIELDS,
                    "PBP acceptance ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return PbpAcceptanceSpecificationResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )


def parse_recent_delivery_history_response(
    raw: Mapping[str, Any],
) -> RecentDeliveryHistoryResponse:
    _validate_strict_read_envelope(raw)
    recipients = []
    for recipient in _rows(raw, "acepList", "recent delivery history"):
        recipients.append(
            RecentDeliveryRecipient(
                **_nullable_string_fields(
                    recipient,
                    _RECENT_DELIVERY_RECIPIENT_FIELDS,
                    "recent delivery recipient",
                ),
                raw=recipient,
            )
        )
    return RecentDeliveryHistoryResponse(
        changed_acceptance_reservation_no=_optional_string(
            raw, "chgePbpRsvNo", "recent delivery history"
        ),
        recipients=tuple(recipients),
        **_response_fields(raw),
    )


_RESERVATION_SEAT_DETAIL_FIELDS = {
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "room_class_code": "h_psrm_cl_cd",
    "room_class_name": "h_psrm_cl_nm",
    # The old comment here read "No h_psg_tp_dv_nm exists anywhere in the
    # decompiled app, so the display-name variant is deliberately NOT mapped"
    # and concluded it was a third-party invention. Both premises are false.
    # `grep -r h_psg_tp_dv_nm analysis/` returns 2 hits: the app's OWN captured
    # sample of this very response, embedded at BasketTicketDataKt.java:44 (and
    # its smali twin smali_classes6/.../BasketTicketDataKt.smali:89), where it
    # sits at /jrny_infos/jrny_info[*]/seat_infos/seat_info[0] with the value
    # '어른'. Live it arrives on 8/8 seat rows next to h_psg_tp_cd (2026-09-22).
    # It IS absent from ReservationOutSeatInfo's @SerialName set
    # (ReservationOutSeatInfo.java:81) — that much was right — but a key the app
    # itself captured and the server always sends is worth modelling.
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_type_name": "h_psg_tp_dv_nm",
    "received_amount": "h_rcvd_amt",
    "seat_price": "h_seat_prc",
    "seat_fare": "h_seat_fare",
    # ReservationOutSeatInfo.java:269 — @SerialName("h_tot_disc_amt"). The
    # only one of the four seat-level money fields that was missing.
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
    # ReservationOutJrnyInfo.java:86,305 — @SerialName("h_arv_dt"), distinct
    # from arrival_time (h_arv_tm).
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


def parse_ticket_reservation_detail_response(
    raw: Mapping[str, Any],
) -> TicketReservationDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = []
    for value in _nested_rows(
        raw,
        "jrny_infos",
        "jrny_info",
        "ticket reservation detail",
    ):
        journey = _row(value, "ticket reservation detail jrny_info")
        seats = []
        for seat_value in _nested_rows(
            journey,
            "seat_infos",
            "seat_info",
            "ticket reservation detail journey",
        ):
            seat = _row(seat_value, "ticket reservation detail seat_info")
            seats.append(
                ReservationSeatDetail(
                    **_nullable_scalar_fields(
                        seat,
                        _RESERVATION_SEAT_DETAIL_FIELDS,
                        "reservation seat detail",
                    ),
                    raw=seat,
                )
            )
        journeys.append(
            ReservationDetailJourney(
                **_nullable_scalar_fields(
                    journey,
                    _RESERVATION_DETAIL_JOURNEY_FIELDS,
                    "reservation detail journey",
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
        **_response_fields(raw),
    )


_REFUND_COMMISSION_FIELDS = {
    "refund_amount": "ret_amt",
    "refund_fee": "ret_fee",
    "proceed_possible_flag": "prg_psb_flg",
    "ticket_return_times_division_code": "tk_ret_tms_dv_cd",
    "usable_mileage": "use_psb_mlg_num",
    "secondary_message_code": "h_msg_cd2",
    "secondary_message_text": "h_msg_txt2",
}


def parse_refund_commission_response(
    raw: Mapping[str, Any],
) -> RefundCommissionResponse:
    _validate_strict_read_envelope(raw)
    return RefundCommissionResponse(
        **_nullable_scalar_fields(
            raw,
            _REFUND_COMMISSION_FIELDS,
            "refund commission",
        ),
        **_response_fields(raw),
    )


_REFUND_TICKET_SEAT_FIELDS = {
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "buyer_name": "h_buy_ps_nm",
    "checkin_status_code": "h_chckn_stt_cd",
    "discount_kind_code": "h_dcnt_knd_cd",
    "discount_kind_name": "h_dcnt_knd_nm",
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_type_name": "h_psg_tp_nm",
    "seat_group_name": "h_sgr_nm",
}

_REFUND_TICKET_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "train_no": "h_trn_no",
    "train_class_name": "h_trn_clsf_nm",
    "room_class_name": "h_psrm_cl_nm",
    "platform_no": "h_plf_no",
}

_REFUND_TICKET_DETAIL_FIELDS = {
    "pnr_no": "h_pnr_no",
    "sale_date": "h_sale_dt",
    "sale_time": "h_sale_tm",
    "window_name": "h_wct_nm",
    "original_sale_date": "h_orgtk_ret_sale_dt",
    "original_window_no": "h_orgtk_wct_no",
    "original_sale_sequence": "h_orgtk_sale_sqno",
    "original_return_password": "h_orgtk_ret_pwd",
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    "refund_possible_flag": "retPsbFlg",
    "return_flag": "h_ret_flg",
    "total_fare_amount": "h_tot_fare_amt",
    "total_discount_amount": "h_tot_disc_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "train_running_flag": "h_trn_running_flg",
    # h_abrd_ps_nm/s_brth are the RIDER's own name+birthdate pair
    # (TicketDetailOut.java:410,418) — a single top-level summary pair,
    # distinct from the LIST psgNmList (below) and from the companion pair
    # h_compa_nm/h_compa_brth.
    "passenger_name": "h_abrd_ps_nm",
    "passenger_birth_date": "s_brth",
    "companion_name": "h_compa_nm",
    "companion_birth_date": "h_compa_brth",
    # "h_pbp_acep_tgt_flg" was mapped here and is now gone: SelTicketInfo does
    # not carry it. It is not even a TicketDetailOut serial name — the 32
    # explicit @SerialName entries at TicketDetailOut.java:117 do not include it;
    # it belongs to MyTicketListOutTicket.java:92,300. Live, neither
    # h_pbp_acep_tgt_flg nor the pbpAcepTgtFlg fallback appeared in any of 40
    # responses (20 tickets x from_purchase_history False/True, 2026-09-22),
    # including the 6 whose list row says 'Y'. Decisive: TicketDetailOut declares
    # pbpAcepTgtFlg NON-FINAL with a setter (:65, setter :1936) and the app
    # INJECTS the list row's value right after SelTicketInfo succeeds
    # (MyTicketBaseViewModel.java:769) before echoing it into the refund
    # (MyTicketDetailViewModel.java:1521) — it would not need to if the server
    # sent it. The old comment's "without parsing it there is no way for a caller
    # to send anything but a guess" is therefore also wrong: read it from
    # TicketListTicket.pbp_acceptance_target_flag, which is exactly where the app
    # reads it. (The old citations TicketDetailDao.java:227-281 and
    # ticketReturn/a.java:430-431 are 6.5.0 paths absent from the 7.0.6
    # decompile.) The pbpAcepTgtFlg fallback below stays — it is the correct
    # default kotlinx name for TicketDetailOut's own field — but note that field
    # is app-set, not server-sent.
    "delay_flag": "h_dlay_flg",
    "delay_ticket_flag": "h_dlay_tk_flg",
    # "mlgSaveFlg"/"mlgSaveTgt" are not read: 0 occurrences anywhere in the
    # decompile (TicketDetailOut.java:39-91 has no mileage-save field and the 32
    # @SerialName entries at :117 have none). That is a phantom of the APP, not
    # of the wire — the live server still sends both keys on every
    # refunds.SelTicketInfo response, always as empty strings (40/40 on
    # 2026-09-22). Both stay reachable through `raw`.
    "additional_service_flag": "addSrvFlg",
    "additional_service_cancel": "addSrvCancel",
}


_DISCOUNT_CARD_SECTION_FIELDS = {
    # "dcntCrdAplSegSqno" is not read: 0 occurrences anywhere in the
    # decompile. journey_sequence (jrnySqno, below) is the real nearby field.
    "departure_station_name": "dptRsStnNm",
    "arrival_station_name": "arvRsStnNm",
    "journey_sequence": "jrnySqno",
    "journey_type_code": "jrnyTpCd",
    "train_group_code": "trnGpCd",
    "detour_division_name": "stlbDturDvNm",
}


def _discount_card_on_ticket(
    raw: Mapping[str, Any],
) -> DiscountCardOnTicket | None:
    """승차권 상세에서 ``dcnt_crd_info`` 를 읽습니다. 없으면 ``None``.

    평범한 승차권에는 없으므로 부재가 오류가 아닙니다. 구간 목록의 전선 키는
    ``appSegList`` — Gson 이 직렬화하는 자바 **필드** 이름입니다
    (``TicketDetailDao.java:124``). 게터는 ``getAppSeg_info()`` 로 철자가 다르며
    그것은 전선 이름이 아닙니다.
    """
    info = _optional_mapping(raw, "dcnt_crd_info", "refund ticket detail")
    if info is None:
        return None
    sections = []
    for value in _optional_list(
        info,
        "appSegList",
        "refund ticket detail dcnt_crd_info",
    ):
        item = _row(value, "refund ticket detail appSegList")
        sections.append(
            DiscountCardSection(
                **_nullable_scalar_fields(
                    item,
                    _DISCOUNT_CARD_SECTION_FIELDS,
                    "discount card section",
                ),
                raw=item,
            )
        )
    return DiscountCardOnTicket(
        card_no=_optional_scalar_string(
            info,
            "h_dcnt_crd_no",
            "discount card info",
        ),
        term_extension_possible_flag=_optional_string(
            info,
            "h_dcnt_crd_trm_extn_psb_flg",
            "discount card info",
        ),
        sections=tuple(sections),
        raw=info,
    )


def parse_refund_ticket_detail_response(
    raw: Mapping[str, Any],
) -> RefundTicketDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = []
    for value in _nested_rows(
        raw,
        "ticket_infos",
        "ticket_info",
        "refund ticket detail",
    ):
        journey = _row(value, "refund ticket detail ticket_info")
        seats = []
        for seat_value in _optional_list(
            journey,
            "tk_seat_info",
            "refund ticket detail ticket_info",
        ):
            seat = _row(seat_value, "refund ticket detail tk_seat_info")
            seats.append(
                RefundTicketSeat(
                    **_nullable_scalar_fields(
                        seat,
                        _REFUND_TICKET_SEAT_FIELDS,
                        "refund ticket seat",
                    ),
                    raw=seat,
                )
            )
        journeys.append(
            RefundTicketJourney(
                **_nullable_scalar_fields(
                    journey,
                    _REFUND_TICKET_JOURNEY_FIELDS,
                    "refund ticket journey",
                ),
                seats=tuple(seats),
                raw=journey,
            )
        )
    detail_fields = _nullable_scalar_fields(
        raw, _REFUND_TICKET_DETAIL_FIELDS, "refund ticket detail"
    )
    # pbpAcepTgtFlg 는 TicketDetailOut.java:65 의 코틀린 필드명입니다(@SerialName
    # 이 없어 와이어 철자는 PROTECTED). 서버가 언젠가 이 철자로 보내면 읽도록
    # 폴백을 남겨 둡니다 — 다만 2026-09-22 라이브 40응답 전부에 없었고, 앱에서도
    # 이 필드는 목록 행에서 주입되는 값이지 서버가 보내는 값이 아닙니다
    # (위 _REFUND_TICKET_DETAIL_FIELDS 주석). 짝이던 h_pbp_acep_tgt_flg 매핑은
    # 이 DTO 의 키가 아니어서 제거했습니다.
    if "pbpAcepTgtFlg" in raw:
        detail_fields["pbp_acceptance_target_flag"] = _optional_string(
            raw, "pbpAcepTgtFlg", "refund ticket detail"
        )
    # h_qrcode has an explicit @SerialName (TicketDetailOut.java:478).
    qr_code = _optional_string(raw, "h_qrcode", "refund ticket detail")
    # psgNmList/seatTicketList/limousine/dtlList have NO explicit @SerialName
    # on TicketDetailOut (PROTECTED wire spelling) — the Kotlin field names
    # are used as a best-effort key, matching this module's treatment of
    # other unannotated fields (e.g. GuideSeatCndOut.timeStamp).
    passenger_names = tuple(
        _row(v, "refund ticket detail psgNmList")
        for v in _optional_list(raw, "psgNmList", "refund ticket detail")
    )
    seat_tickets = tuple(
        _row(v, "refund ticket detail seatTicketList")
        for v in _optional_list(raw, "seatTicketList", "refund ticket detail")
    )
    limousine = _optional_mapping(raw, "limousine", "refund ticket detail")
    delay_details = tuple(
        _row(v, "refund ticket detail dtlList")
        for v in _optional_list(raw, "dtlList", "refund ticket detail")
    )
    return RefundTicketDetailResponse(
        **detail_fields,
        qr_code=qr_code,
        passenger_names=passenger_names,
        seat_tickets=seat_tickets,
        limousine=limousine,
        delay_details=delay_details,
        journeys=tuple(journeys),
        discount_card=_discount_card_on_ticket(raw),
        **_response_fields(raw),
    )


_SELF_SEAT_CHANGE_STATION_FIELDS = {
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "departure_date": "dptDt",
    "departure_time": "dptTm",
    "arrival_date": "arvDt",
    "arrival_time": "arvTm",
    "departure_construction_order": "dptStnConsOrdr",
    "departure_run_order": "dptStnRunOrdr",
    "general_remaining_seats": "gnrmRestSeatNum",
    "special_remaining_seats": "sprmRestSeatNum",
}
_SELF_SEAT_CHANGE_REASON_FIELDS = {
    "query_code": "qryCode",
    "query_order": "qryOrdr",
    "reason_text": "frcSaleRsnCont",
}
_SELF_SEAT_CHANGE_INFO_FIELDS = {
    "train_no": "trnNo",
    "train_class_code": "trnClsfCd",
    "train_class_name": "trnClsfNm",
    "train_group_code": "trnGpCd",
    "train_group_name": "trnGpNm",
    "run_date": "runDt",
    "general_reservation_possible_code": "gnrmRsvPsbCd",
    "special_reservation_possible_code": "sprmRsvPsbCd",
    "change_before_departure_construction_order": "chgBfDptStnConsOrdr",
    "change_before_arrival_construction_order": "chgBfArvStnConsOrdr",
    "existing_departure_run_order": "exsDptStnRunOrdr",
    "existing_arrival_run_order": "exsArvStnRunOrdr",
}


def parse_self_seat_change_info_response(
    raw: Mapping[str, Any],
) -> SelfSeatChangeInfoResponse:
    """``self.seatChgInfo.do`` 를 파싱합니다.

    ``CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse`` 와 그 안의 두 행 타입
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:64-204``). DAO 가 선언한
    필드가 전부 자바 ``String`` 이라 모두 :func:`_optional_scalar_string` 으로
    읽습니다 — 잔여좌석 수와 편성/운행 순서가 맨 JSON 숫자로 오는 것이 관측된
    바로 그런 필드입니다.
    """
    _validate_strict_read_envelope(raw)
    stations = tuple(
        SelfSeatChangeStation(
            **_nullable_scalar_fields(
                station,
                _SELF_SEAT_CHANGE_STATION_FIELDS,
                "self seat change station",
            ),
            raw=station,
        )
        for station in (
            _row(value, "self seat change chgStnList")
            for value in _optional_list(
                raw,
                "chgStnList",
                "self seat change info",
            )
        )
    )
    reasons = tuple(
        SelfSeatChangeReason(
            **_nullable_scalar_fields(
                reason,
                _SELF_SEAT_CHANGE_REASON_FIELDS,
                "self seat change reason",
            ),
            raw=reason,
        )
        for reason in (
            _row(value, "self seat change chgRsnList")
            for value in _optional_list(
                raw,
                "chgRsnList",
                "self seat change info",
            )
        )
    )
    return SelfSeatChangeInfoResponse(
        **_nullable_scalar_fields(
            raw,
            _SELF_SEAT_CHANGE_INFO_FIELDS,
            "self seat change info",
        ),
        stations=stations,
        reasons=reasons,
        **_response_fields(raw),
    )


_ORIGINAL_TICKET_SEAT_FIELDS = {
    "passenger_sequence": "psgSqno",
    "assign_sequence": "asgnSqno",
    "passenger_type_code": "psgTpDvCd",
    "room_class_code": "psrmClCd",
    "car_no": "scarNo",
    "seat_no": "seatNo",
    "seat_count": "seatNum",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "requested_seat_attribute_code": "rqSeatAttCd",
    "direction_seat_attribute_code": "dirSeatAttCd",
    "location_seat_attribute_code": "locSeatAttCd",
    "smoking_seat_attribute_code": "smkSeatAttCd",
    "additional_seat_attribute_code": "addSeatAttCd",
    "etc_seat_attribute_code": "etcSeatAttCd",
}
_ORIGINAL_TICKET_JOURNEY_FIELDS = {
    "journey_sequence": "jrnySqno",
    "journey_order": "jrnyOrdr",
    "journey_type_code": "jrnyTpCd",
    "train_no": "trnNo",
    "train_group_code": "trnGpCd",
    "departure_date": "dptDt",
    "departure_time": "dptTm",
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "departure_construction_order": "dptStnConsOrdr",
    "arrival_date": "arvDt",
    "arrival_time": "arvTm",
    "arrival_station_code": "arvRsStnCd",
    "arrival_station_name": "arvRsStnNm",
    "arrival_construction_order": "arvStnConsOrdr",
    "goods_no": "gdNo",
    "total_seat_count": "totSeatNum",
    "total_standing_count": "totStndNum",
    "general_change_allowed_flag": "genChgAllwFlg",
    "single_ticket_flag": "snglTkFlg",
}
_ORIGINAL_TICKET_FIELDS = {
    "pnr_no": "pnrNo",
    "ticket_kind_code": "tkKndCd",
    "original_sale_datetime": "ogtkSaleDt",
    "original_window_no": "ogtkSaleWctNo",
    "original_sale_sequence": "ogtkSaleSqno",
    "original_return_password": "ogtkRetPwd",
    "member_card_no": "mbCrdNo",
    "adult_count": "adulCnt",
    "child_count": "chilCnt",
    "group_discount_count": "grpDcntCnt",
    "passenger_type_division_code": "psgTpDvCd",
    "received_amount": "rcvdAmt",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "change_sale_transaction_no": "chgSaleTno",
    "sms_send_flag": "smsSndFlg",
    "forced_sale_reason_text": "frcSaleRsnCont",
}


def parse_original_ticket_inquiry_response(
    raw: Mapping[str, Any],
) -> OriginalTicketInquiryResponse:
    """``research.tripChgOgtk.do`` 를 파싱합니다.

    ``OgTkInquiryDao.OgTkInquiryResponse`` → ``response/research/OrgTk.java`` 의
    ``orgTkList``. 각 원표는 ``Jrny.java`` 의 ``jrnyList`` 를, 각 여정은
    ``Seat.java`` 의 ``seatList`` 를 가집니다.

    ``cmpnList`` 와 ``stlList`` 는 일부러 파싱하지 않습니다. 지연증명 반환번호
    (``Cmpn.java:11-14``)와 카드/승인번호(``Stl.java:5-16``) 같은 소지 자격증명을
    더 싣는데 변경 과정의 어느 단계도 그것을 필요로 하지 않습니다. ``raw`` 는
    원본을 그대로 보존하므로 그 안의 두 목록도 그대로 남습니다. 로깅 또는 외부
    직렬화 전에 :func:`~korail_mobile_api.redaction.redact_mapping` 을 적용해야
    합니다.
    """
    _validate_strict_read_envelope(raw)
    tickets = []
    for value in _optional_list(raw, "orgTkList", "original ticket inquiry"):
        ticket = _row(value, "original ticket inquiry orgTkList")
        journeys = []
        for journey_value in _optional_list(
            ticket,
            "jrnyList",
            "original ticket",
        ):
            journey = _row(journey_value, "original ticket jrnyList")
            seats = tuple(
                OriginalTicketSeat(
                    **_nullable_scalar_fields(
                        seat,
                        _ORIGINAL_TICKET_SEAT_FIELDS,
                        "original ticket seat",
                    ),
                    raw=seat,
                )
                for seat in (
                    _row(seat_value, "original ticket seatList")
                    for seat_value in _optional_list(
                        journey,
                        "seatList",
                        "original ticket journey",
                    )
                )
            )
            journeys.append(
                OriginalTicketJourney(
                    **_nullable_scalar_fields(
                        journey,
                        _ORIGINAL_TICKET_JOURNEY_FIELDS,
                        "original ticket journey",
                    ),
                    seats=seats,
                    raw=journey,
                )
            )
        tickets.append(
            OriginalTicket(
                **_nullable_scalar_fields(
                    ticket,
                    _ORIGINAL_TICKET_FIELDS,
                    "original ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return OriginalTicketInquiryResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )
