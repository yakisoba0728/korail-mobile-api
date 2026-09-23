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

from collections.abc import Mapping
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
    ``mode`` 와는 무관합니다 — 2026-09-22 한 계정 관측: 결과가 있는
    ``mode="2"`` 는 ``pnr_list``(128행), 빈 ``mode="1"`` 과 빈 ``mode="2"`` 는
    둘 다 ``reservation_list``(0행). 캡처가 이 저장소에 연결돼 있지 않아 행
    수는 재검산할 수 없습니다(관측 범위 한정, 미검증). 빈 봉투에는 어차피 행이 없으므로 ``pnr_list``
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
        # best-effort keys). addSrvInfo (AddSrvItem, :39) is read through the
        # shared AddSrvItem reader, and ticketKind (TicketDefine.TicketKind,
        # :52) is kept as the raw string that arrives — the enum's serialized
        # names are AlienGuard ciphertext (TicketDefine.java:1092-1130), so no
        # code mapping is claimed. Both stay reachable through `raw` as before.
        additional_service = _optional_add_srv_item(
            reservation_raw,
            "addSrvInfo",
            "ticket list addSrvInfo",
            "ticket list addSrvInfo detailInfo",
        )
        reservations.append(
            TicketListReservation(
                tickets=tuple(tickets),
                departure_datetime=_optional_scalar_string(
                    reservation_raw, "hDptDtTm", "ticket list reservation"
                ),
                ticket_kind_code=_optional_scalar_string(
                    reservation_raw, "hTkKndCd", "ticket list reservation"
                ),
                list_count=_optional_scalar_string(
                    reservation_raw, "listCnt", "ticket list reservation"
                ),
                seat_assign_count=_optional_integer(
                    reservation_raw, "seatAssignCount", "ticket list reservation"
                ),
                ticket_status=_optional_scalar_string(
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
                display_ticket_name=_optional_scalar_string(
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
                additional_service=additional_service,
                ticket_kind=_optional_scalar_string(
                    reservation_raw, "ticketKind", "ticket list reservation"
                ),
            )
        )
    return TicketListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        reservations=tuple(reservations),
        total_count=_optional_scalar_string(raw, "h_total_cnt", "ticket list"),
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


# ─── 필드 읽기 규칙 ─────────────────────────────────────────────────────────────
#
# **선택 필드는 관대하게 읽습니다.** 모양이 어긋난 스칼라는 ``None``, 객체·목록
# 자리에 다른 값이 오면 ``None``/빈 목록, 목록 안의 객체가 아닌 원소는 건너뜁니다.
# 선택 필드 하나 때문에 응답 전체를 버리지 않습니다 — 원문은 언제나 ``raw`` 에
# 있습니다. 필수 필드(봉투, ``_required_*``)만 어긋나면
# :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.


def _optional_mapping(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> Mapping[str, Any] | None:
    """객체면 그대로, 아니면(없음·리스트·스칼라) ``None``."""
    value = data.get(key)
    return value if isinstance(value, Mapping) else None


def _optional_list(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> list[Any]:
    """리스트면 그대로(원소 검사 없음), 아니면 빈 리스트."""
    value = data.get(key)
    return value if isinstance(value, list) else []


def _nested_rows(
    raw: Mapping[str, Any],
    outer_key: str,
    inner_key: str,
    context: str = "",
) -> list[Mapping[str, Any]]:
    """``{outer: {inner: [...]}}`` 의 객체 원소들. 모양이 어긋나면 빈 리스트."""
    outer = _optional_mapping(raw, outer_key)
    if outer is None:
        return []
    return [item for item in _optional_list(outer, inner_key) if isinstance(item, Mapping)]


def _row(value: Any, context: str) -> Mapping[str, Any]:
    """필수 객체 — 객체가 아니면 거부합니다."""
    if not isinstance(value, Mapping):
        raise KorailProtocolError(
            f"KORAIL {context} contained a non-object item"
        )
    return value


def _rows(
    data: Mapping[str, Any] | None,
    key: str,
    context: str = "",
    row_context: str | None = None,
) -> list[Mapping[str, Any]]:
    """``key`` 리스트의 객체 원소들. 리스트가 아니면 빈 리스트, 객체가 아닌 원소는 건너뜀."""
    if not isinstance(data, Mapping):
        return []
    return [item for item in _optional_list(data, key) if isinstance(item, Mapping)]


def _optional_string(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> str | None:
    """문자열이면 그대로, 아니면 ``None``."""
    value = data.get(key)
    return value if isinstance(value, str) else None


def _required_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str:
    """필수 문자열. 키가 없거나 문자열이 아니면 거부합니다.

    ``Seat`` 의 합성 생성자(``Seat.java:53-59``)는 다섯 필드 중 하나라도 없으면
    ``throwMissingFieldException`` 을 던집니다 — 7.0.6 도 처리하지 않는 응답
    모양이므로 선택으로 읽지 않습니다.
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


def _strict_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    """JSON 문자열·정수·``null`` 을 받고 그 밖의 모양은 **거부**합니다.

    KORAIL 은 APK 가 자바 ``String`` 으로 선언한 필드를 숫자로도 보냅니다(예약
    응답의 ``h_jrny_cnt="0001"`` 과 예약 이력의 ``1``). 정수는 문자열로
    정규화합니다. 폼에 되울리는 값처럼 정확해야 하는 필드에만 씁니다 —
    선택 필드는 :func:`_optional_scalar_string` 입니다.
    """
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    # `type(...) is int` on purpose: bool is an int subclass.
    if type(value) is int:
        try:
            return str(value)
        except ValueError as exc:  # 파이썬의 정수→문자열 자릿수 한도
            raise KorailProtocolError(
                f"KORAIL {context} field {key} is an integer too long to use"
            ) from exc
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a string, an integer, or null"
    )


def _optional_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> str | None:
    """선택 스칼라 — 문자열은 그대로, JSON 정수는 문자열로, 그 밖은 ``None``."""
    try:
        return _strict_scalar_string(data, key, context)
    except KorailProtocolError:
        return None


#: ``limousine_parsers`` 가 이 이름으로 import 합니다.
_additive_scalar_string = _optional_scalar_string


def _optional_integer(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> int | None:
    """선택 정수 — 정수나 ASCII 10진 문자열이면 ``int``, 그 밖은 ``None``."""
    if data.get(key) is None:
        return None
    try:
        return _required_integer(data, key, context)
    except KorailProtocolError:
        return None


def _required_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    """필수 정수. JSON 정수와 따옴표 친 ASCII 10진 문자열을 받습니다.

    앱의 kotlinx 디코더(``StreamingJsonDecoder.decodeInt()`` →
    ``JsonReader.consumeNumericLiteral()``)도 따옴표 친 숫자를 받습니다.
    null/bool/float/비숫자는 거부합니다.
    """
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
    context: str = "",
) -> bool | None:
    """``bool`` 이면 그대로, 아니면(없음 포함) ``None`` — "없음" 과 "거짓" 을 구분합니다."""
    value = data.get(key)
    return value if isinstance(value, bool) else None


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
    """:func:`_nullable_string_fields` 와 같되 JSON 정수도 문자열로 받습니다."""
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
    # 승차권 종류 코드는 승차권 행의 ``h_tk_knd_cd``/``h_tk_knd_nm`` 에서 읽습니다.
    # 예약 행의 ``hTkKndCd`` 는 @SerialName 이 없는 Kotlin 속성명을 전선 키로
    # 짐작한 것입니다.
    #
    # **관측 범위(미검증).** 2026-09-22 에 개발자가 자기 계정 하나로 받은 응답에서
    # 예약 행 128개가 ``ticket_list`` 외의 키를 싣지 않았고, 승차권 행 131개가
    # 모두 ``h_tk_knd_cd``/``h_tk_knd_nm``(``'72'``/``'스마트티켓'``)을 실었다고
    # 적어 두었습니다. 그 캡처 원문·식별자는 이 저장소에 연결돼 있지 않아 숫자를
    # 재검산할 수 없고, 한 계정·한 날짜의 관측이지 서버 전반의 동작이 아닙니다 —
    # "서버는 ``hTkKndCd`` 를 보내지 않는다" 로 읽지 마십시오.
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    # MyTicketListOutTicket.java:92 가 선언하는 31개 @SerialName 중 아래
    # 여섯입니다. 위와 같은 2026-09-22 의 한 계정 관측(재검산 불가, 미검증)
    # 에서는 131행 모두에 있었다고 적혀 있습니다. ``h_pbp_acep_tgt_flg`` 는 앱이
    # 이 행에서 읽어 상세 DTO 에 주입합니다(MyTicketBaseViewModel.java:769).
    # 환불 상세(refunds.SelTicketInfo) 응답에 이 키가 없었다는 것도 같은 범위의
    # 관측일 뿐이라, 이 행이 이 값의 "유일한 출처" 라고 단정하지 않습니다.
    "ticket_sequence": "h_tk_sqno",
    "ticket_status_name": "h_tk_stt_nm",
    "return_possible_flag": "h_ret_psb_flg",
    "use_transaction_no": "h_use_tno",
    "notify_use_transaction_no": "h_noty_use_tno",
    "pbp_acceptance_target_flag": "h_pbp_acep_tgt_flg",
    # jrn_info 는 일부러 타입 없는 Mapping 으로 둡니다(위 parse_ticket_list_response).
    # 언젠가 타입을 붙이거든 h_srcar_no 는 반드시 _optional_scalar_string 또는
    # _optional_integer 로 읽으십시오. TicketListTrainInfo.java:47,72,284 는 이
    # 필드를 non-null String 으로 선언하지만, 같은 2026-09-22 한 계정 관측(138행,
    # 재검산 불가·미검증)에서는 JSON 정수로 왔다고 적혀 있습니다 — 문자열과
    # 정수를 둘 다 받아야 합니다.
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

# CartInfo.java 는 28개 문자열 필드(선언 28-61행) **전부** 에 평문
# ``@SerialName`` 을 답니다(281-392행). 위 지도 + ``h_tk_cnt`` 로 16개를 읽고
# 있었으므로, 나머지 열둘을 여기서 읽습니다.
#
# 스칼라로 읽는 이유: 장바구니 응답의 라이브 캡처가 없어 KORAIL 이 숫자꼴
# 키(``h_item_sqno``, ``h_jrny_sqno``, ``h_stl_lmt_tm`` …)를 JSON 정수로
# 보내는지 확인할 수 없습니다 — ``h_srcar_no`` 에서 이미 겪은 일입니다.
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
}

_DELAY_DISCOUNT_TICKET_SCALAR_FIELDS: dict[str, str] = {
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
    # (2026-09-22: ``menu_no`` ``"1"`` 25행·``"2"`` 10행 전부 str). 형제
    # :class:`~korail_mobile_api.read_models.CommuterKindMenuResponse` 도 같은
    # 키를 문자열로 두므로 경로에 따라 형이 달라지지 않습니다. 게다가 이
    # 라우트는 빈 문자열을 흔하게 보냅니다(같은 25행에서 ``detailType``·
    # ``isExpand``·``saleMsg1-3`` 등이 ``""``).
    "after_day": "afterDay",
    "agreement": "agree",
    "detail_type": "detailType",
    "detail_description": "dtlDsc",
    "enabled": "enable",
    "item_id": "id",
    "information": "information",
    "expanded": "isExpand",
    "parent_id": "parentId",
    "representative_arrival": "repSegArv",
    "representative_departure": "repSegDpt",
    "title": "title",
    "train_group_code": "trnGpCd",
    "item_type": "type",
}

_PASS_MENU_ITEM_SCALAR_FIELDS: dict[str, str] = {
    "sale_message_1": "saleMsg1",
    "sale_message_2": "saleMsg2",
    "sale_message_3": "saleMsg3",
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
    # detailType(TrGdMenuLtOutCont.java:42)
    # 은 "이 줄의 종류"를 주지 않습니다 — 라이브 60행 중 54행에 키가 없고 6행은
    # ''(2026-09-22). 이름은 와이어 키에 맞춰 형제 PassMenuItem.detail_type 과
    # 같습니다. 아래 passType 을 content_type 자리로 올리지 마십시오:
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
    # 목표 코드와 비교하고, :1244 가 getPassData() 를 꺼냅니다. 같은 함수의
    # :1247-1248 이 passData == null 이면 backAlert 로 화면을 되돌립니다.
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
    # 아래 여섯은 ReservationViewOutTrainInfo.java:94 의 37개 @SerialName 에
    # 있습니다. 앞의 셋이 핵심입니다 — 미결제 홀드의 "언제까지"를 말하는
    # 값으로, payment_flag/settlement_flag 는 "결제해야 한다"만 알려 줍니다.
    # 이 계정에는 살아 있는 홀드가 없어(2026-09-22: h_msg_cd='P100',
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
# read_models.py for why one shared row map is wrong for both):
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
    # 코드 짝과 나란히 선언하며, 전선에 '예약하기'/'역발매중' 같은 값으로
    # 옵니다(2026-09-22: menu_id='A1','A2' 각 10행).
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
    # TrainScheduleOutTrainInfo.java:1204,1364,1468,1480.
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
    # TrainList.java:25-70 declares 20 fields; the 12 below include
    # h_run_dt — the only date on this row.
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
    *,
    station_selection_key: str = "h_select_station",
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
        station_selection=_optional_string(data, station_selection_key, context),
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
                **_nullable_scalar_fields(
                    item, _PASS_MENU_ITEM_SCALAR_FIELDS, "pass menu item"
                ),
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
    for item in _nested_rows(raw, "cart_infos", "cart_info", "cart list"):
        items.append(
            CartItem(
                **_nullable_string_fields(item, _CART_ITEM_FIELDS, "cart item"),
                **_nullable_scalar_fields(
                    item, _CART_ITEM_SCALAR_FIELDS, "cart item"
                ),
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
            **_nullable_scalar_fields(
                row, _DELAY_DISCOUNT_TICKET_SCALAR_FIELDS, "delay discount ticket"
            ),
            raw=row,
        )
        for row in rows
    )
    # main_info 는 DelayDiscountViewOut.java:24,51 이 선언하지 않는 **서버 추가**
    # 블록입니다(그 DTO 는 disc_infos 하나뿐). 앱이 읽지 않는 표면이지만, 형제
    # DiscountCouponListResponse 도 같은 네 개념을 내놓습니다. 중첩 블록을 타입화하는 방식은
    # parse_pass_schedule_response 의 main_info 를 따릅니다.
    #
    # 다섯 값을 문자열로 둡니다: 와이어가 0을 채운 문자열이고
    # ('0000'/'000000000') h_last_page_yn 은 ''로 와서, 쿠폰 쪽처럼
    # _optional_integer 를 쓰면 그 빈 문자열이 None 이 됩니다.
    # 이 계정에는 지연할인권이 없어 전부 0인 응답만 봤습니다(2026-09-22).
    main_info = _optional_mapping(raw, "main_info")
    pagination: dict[str, str | None] = {}
    if main_info is not None:
        pagination = _nullable_scalar_fields(
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
    for item in rows:
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
                start_date=_optional_scalar_string(
                    item, "h_fdcert_mg_st_dt", "discount coupon"
                ),
                expiration_date=_optional_string(
                    item, "h_fdcert_mg_cls_dt", "discount coupon"
                ),
                discount_kind_code=_optional_scalar_string(
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
        total_count=_optional_scalar_string(raw, "h_tot_cnt", "coupon response"),
        row_count=_optional_scalar_string(raw, "h_row_cnt", "coupon response"),
        **_response_fields(raw),
    )


def parse_pass_availability_response(
    raw: Mapping[str, Any],
) -> PassAvailabilityResponse:
    # A live pass.passInfoList success nests its code as main_info.h_msg_cd and
    # leaves the top level with strResult only, so a strict top-level envelope
    # check would reject every successful response. Same result-only accommodation as
    # parse_pass_menu_response.
    _validate_envelope(raw, allow_result_only_success=True)
    # PassInfo.java:92,96,100 은 세 필드를 선언합니다. open_dates 는
    # h_use_open_dt 만 담은 날짜 문자열 튜플로 두고(공개 튜플의 원소 형을 바꾸는
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
                item_sequence=_optional_scalar_string(item, "h_item_sqno", "pass date"),
                pnr_no=_optional_scalar_string(item, "h_pnr_no", "pass date"),
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
    # 아예 오지 않습니다(2026-09-22: 입력 29종 전부).
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
    main_raw = _optional_mapping(raw, "main_info")
    main_info = (
        PassAvailabilityMainInfo(
            **_nullable_scalar_fields(
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
                **_nullable_scalar_fields(row, _TRIP_MENU_CONTENT_FIELDS, "trip menu content"),
                # TrGdMenuLtOutCont.java:45 passData → TrGdMenuLtOutPass.java:29-35.
                # 정기권 메뉴·종류 라우트가 싣는 것과 같은 모양이라 같은 헬퍼를 씁니다.
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(row, "passData"),
                    "trip menu pass data",
                    # TrGdMenuLtOutPass.java:152 — 여행 메뉴의 키 철자는 별도입니다.
                    station_selection_key="h_seiect_station",
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
    for item in rows:
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
                **_nullable_scalar_fields(item, _TICKET_RECEIPT_FIELDS, "ticket receipt"),
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
        for item in _rows(raw, "tkList")
    )
    original_tickets = tuple(
        ReservationHistoryOriginalTicket(
            **_nullable_scalar_fields(
                item, _RESERVATION_HISTORY_ORIGINAL_TICKET_FIELDS,
                "reservation history original ticket",
            ),
            raw=item,
        )
        for item in _rows(raw, "orgTkList")
    )
    passengers = tuple(
        ReservationHistoryPassenger(
            **_nullable_scalar_fields(
                item, _RESERVATION_HISTORY_PASSENGER_FIELDS,
                "reservation history passenger",
            ),
            raw=item,
        )
        for item in _nested_rows(raw, "psg_infos", "psg_info")
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

    ``jrny_infos[].train_infos[]`` 뿐 아니라 최상위 신원 필드
    (``h_rsv_ps_nm``/``h_tel_no`` 등)와 여정마다 매달린 ``srv_infos``/
    ``acmp_infos``, 그리고 그 PNR 의 실제 운임·결제·발권 내용을 담은
    ``ReservationOut`` 중첩 전체도 읽습니다.
    """
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
    for journey in _nested_rows(
        raw, "jrny_infos", "jrny_info", "reservation history"
    ):
        trains: list[ReservationHistoryTrain] = []
        for train in _nested_rows(
            journey, "train_infos", "train_info", "reservation history"
        ):
            history_train = ReservationHistoryTrain(
                **_nullable_scalar_fields(
                    train, _RESERVATION_HISTORY_TRAIN_FIELDS, "reservation history train"
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
        service_infos = tuple(_nested_rows(journey, "srv_infos", "srv_info"))
        accompanying_infos = tuple(
            _nested_rows(journey, "acmp_infos", "acmp_info")
        )
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
        **_nullable_scalar_fields(
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
    # 2026-09-22 한 계정 관측(좌석속성코드 14종)에서는 이 키가 오지 않아
    # time_stamp 가 None 이었다고 기록돼 있습니다 — 관측 범위의 이야기이지
    # 서버가 늘 안 보낸다는 뜻은 아닙니다(미검증). 값이 없다고 철자를 다시
    # 고치지 마십시오.
    return GuideSeatConditionResponse(
        time_stamp=_optional_integer(raw, "timeStamp", "guide seat condition"),
        **_response_fields(raw),
    )


def _parse_train_schedule_item(
    raw: Mapping[str, Any],
    field_map: Mapping[str, str],
) -> TrainScheduleItem:
    return TrainScheduleItem(
        **_nullable_scalar_fields(raw, field_map, "train schedule item"),
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
    ``MergeSeatsCOutTrnInfos.java:25-26`` 만 ``hMergeRsvPsbFlg`` 를
    선언하고 — 와이어 키는 같은 파일 ``:85`` 의 명시적
    ``@SerialName("h_merge_rsv_psb_flg")`` 입니다 —
    ``TrainScheduleOutTrainInfos.java:25-26`` 은 ``trnInfo`` 하나뿐입니다
    (그쪽 와이어 키도 명시적 ``@SerialName("trn_info")``, 같은 파일 ``:78``).
    (두 DTO 의 줄번호가 똑같이 ``:25-26`` 이라, 생략형으로 적으면 어느
    파일인지 구분되지 않습니다 — 서로 다른 두 파일입니다.) 좌석배정 시각표
    쪽에서 이 키를 읽으면 항상 ``None`` 입니다.
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
        _parse_train_schedule_item(value, field_map)
        for value in _rows(container, "trn_info", context)
    )
    return merge_flag, trains


def parse_seat_assignment_schedule_response(
    raw: Mapping[str, Any],
) -> SeatAssignmentScheduleResponse:
    """``assignScheduleView.do``.

    ``h_merge_rsv_psb_flg`` 는 읽지 않습니다 — 이 라우트의 ``trn_infos`` 는
    ``TrainScheduleOutTrainInfos``(``trn_info`` 하나뿐)이고, 그 키는
    ``MergeSeatsCOutTrnInfo``(``mergeSeatsC.do``)에 속합니다.

    다음 페이지 커서(``strJobId``, ``h_menu_id`` 등)도 같은 DTO 의 합성
    생성자 ``TrainScheduleOut.java:67`` 이 ``@SerialName("strJobId")``/
    ``@SerialName("h_menu_id")`` 로 함께 선언하므로 ``h_next_pg_flg`` 만이
    아니라 전부 꺼냅니다. 같은 DTO 모양을 읽는 형제 파서
    ``parsers.py::parse_train_search_metadata`` 가 이 전체 필드 집합을
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
        job_id=_optional_scalar_string(raw, "strJobId", "seat assignment schedule"),
        menu_id=_optional_scalar_string(raw, "h_menu_id", "seat assignment schedule"),
        goods_no=_optional_scalar_string(raw, "h_gd_no", "seat assignment schedule"),
        notice_message=_optional_scalar_string(
            raw, "h_notice_msg", "seat assignment schedule"
        ),
        first_seat_count=_optional_scalar_string(
            raw, "h_seat_cnt_first", "seat assignment schedule"
        ),
        second_seat_count=_optional_scalar_string(
            raw, "h_seat_cnt_second", "seat assignment schedule"
        ),
        agreement_text=_optional_scalar_string(
            raw, "h_agree_txt", "seat assignment schedule"
        ),
        first_departure_time=_optional_scalar_string(
            raw, "txtGoHour_first", "seat assignment schedule"
        ),
        result_count=_optional_scalar_string(raw, "h_rslt_cnt", "seat assignment schedule"),
        next_query_station_no=_optional_scalar_string(
            raw, "h_qry_st_no_next", "seat assignment schedule"
        ),
        next_train_no=_optional_scalar_string(
            raw, "h_trn_no_next", "seat assignment schedule"
        ),
        next_preceding_train_no=_optional_scalar_string(
            raw, "h_prcd_trn_no_next", "seat assignment schedule"
        ),
        next_connecting_train_no=_optional_scalar_string(
            raw, "h_ectb_trn_no_next", "seat assignment schedule"
        ),
        remaining_seat_count=_optional_scalar_string(
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
        # 맞지만 **관측한 응답에는 없었습니다**: 2026-09-22 의 20여 회 호출
        # 모두에서 실서버 최상위 봉투는 스칼라 5개
        # (h_msg_cd/h_msg_txt/msgCd/msgTxt/strResult)에 midStnList(:108)와
        # trn_infos(:116)뿐이었고 runDt 는 한 번도 오지 않아 이 값은 None
        # 이었습니다. 다른 조건에서 서버가 보내는지는 확인하지 않았습니다.
        # 운행일자는 행 단위로 왔습니다 — 관측한 호출마다
        # trains[i].run_date(h_run_dt)가 정확히 돌아왔습니다. 다른 키를
        # 찾아 "고치려" 하지 마십시오; 이 DTO 에 다른 최상위 날짜는 없습니다.
        run_date=_optional_scalar_string(raw, "runDt", "merge seats inquiry"),
        intermediate_stations=tuple(stations),
        trains=trains,
        **_response_fields(raw),
    )


def parse_pass_schedule_response(
    raw: Mapping[str, Any],
) -> PassScheduleResponse:
    # WRG000000 is a non-fatal empty result: error_json.json:4173 spells it
    # "조회 결과가 없습니다." (EN row 14397: "There is no train in the search
    # results."). No 7.0.6 Java/smali file
    # contains the literal "WRG000000" at all — the only occurrences anywhere
    # under analysis/ are the four error_json.json rows. So treating it as
    # non-fatal is grounded in the message dictionary plus this library's own
    # live observation, not in an app call site — 미출처로 두는 대신 그 한계를
    # 여기 적어 둡니다.
    empty = _validate_envelope(raw, accepted_empty_codes=frozenset({"WRG000000"}))
    if empty:
        return PassScheduleResponse(**_response_fields(raw))
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError("KORAIL pass schedule strResult must be exact SUCC")
    main_raw = _optional_mapping(raw, "main_info")
    main_info = (
        PassScheduleMainInfo(
            **_nullable_scalar_fields(
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
                **_nullable_scalar_fields(row, _PASS_SCHEDULE_TRAIN_FIELDS, "pass schedule train"),
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
    # MyXPointViewOut.java:43,53,54 — customer_lead_flag_name 의 플래그 짝과
    # disability_flag 의 유형 코드·이름입니다. 셋 다 라이브 48키 응답에
    # 옵니다(2026-09-22).
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
    # It is not a phantom key: the live server DOES send
    # railNowSavePontValNum1 on every mlg.amtSpec.do response — a 9-character
    # string on the KTX and RAIL_POINT ledgers and on every page (2026-09-22),
    # equal to totAcmRailPontValNum1 on the test account. The only reason not
    # to map it is that the app does not model it, so neither do we. It stays
    # reachable through `raw`.
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
        # The rationale is the wire tolerance above, not an app call site.
        # Live, all 48 top-level keys arrive as strings (2026-09-22).
        **_nullable_scalar_fields(raw, _KORAIL_POINT_SUMMARY_FIELDS, "korail point summary"),
        **_response_fields(raw),
    )


def parse_mileage_history_response(
    raw: Mapping[str, Any],
) -> MileageHistoryResponse:
    _validate_strict_read_envelope(raw)
    entries = []
    for item in _rows(raw, "specList", "mileage history"):
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
        **_nullable_scalar_fields(raw, _MILEAGE_HISTORY_FIELDS, "mileage history"),
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
    # apdUsrFlg, saleDt, saleSqno, saleWctNo) — 여덟 중 아래 셋은 앱 화면이
    # 그리지 않지만(화면은 다섯 개만 그립니다 —
    # NCardHistoryScreenKt.java:431,439,526,528,301) DTO 에는 있습니다. @SerialName 이 하나도 없으므로 코틀린 프로퍼티
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
                **_nullable_scalar_fields(item, _DISCOUNT_CARD_USAGE_FIELDS, "discount card usage"),
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
                **_nullable_scalar_fields(item, _DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS, "discount card schedule train"),
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
                **_nullable_scalar_fields(item, _CUSTOMER_TRIP_FIELDS, "customer trip info"),
                raw=item,
            )
        )
    return CustomerTripInfoResponse(
        trips=tuple(trips),
        **_response_fields(raw),
    )


def _parse_add_srv_item(
    item: Mapping[str, Any],
    context: str,
    info_context: str,
) -> MaasServiceDetail:
    """``AddSrvItem`` 한 건(``AddSrvItem.java:28-49``).

    이 DTO 는 두 곳에서 같은 모양으로 옵니다 — MaaS 상세 목록의 행
    (``MaasDetailOut.java:27`` 의 ``List<AddSrvItem> addSrvList``)과 승차권 목록
    예약 행의 ``addSrvInfo``(``MyTicketListOutReservation.java:39``). 그래서
    :class:`MaasServiceDetail` 하나로 읽습니다. ``AddSrvItem`` 에는
    ``@SerialName`` 이 하나도 없으므로 키는 코틀린 필드명이라고 **추론**합니다
    -- kotlinx 의 기본 규칙에 기댄 것입니다. ``AddSrvItem$$serializer.java`` 의
    디스크립터 원소 이름(``addElement(...)``)은 AlienGuard 로 보호되어 있어
    직접 확인하지 못했습니다.
    """
    info_raw = _optional_mapping(item, "detailInfo")
    detail_info = None
    if info_raw is not None:
        detail_info = MaasServiceDetailInfo(
            **_nullable_scalar_fields(
                info_raw, _MAAS_DETAIL_INFO_FIELDS, info_context
            ),
            entity_one=tuple(_rows(info_raw, "entityOne")),
            raw=info_raw,
        )
    return MaasServiceDetail(
        **_nullable_scalar_fields(item, _MAAS_DETAIL_FIELDS, context),
        detail_info=detail_info,
        raw=item,
    )


def _optional_add_srv_item(
    data: Mapping[str, Any],
    key: str,
    item_context: str,
    info_context: str,
) -> MaasServiceDetail | None:
    """``addSrvInfo`` 같은 선택 ``AddSrvItem`` 객체. 객체가 아니면 ``None``."""
    item = _optional_mapping(data, key)
    if item is None:
        return None
    return _parse_add_srv_item(item, item_context, info_context)


def parse_maas_service_detail_list_response(
    raw: Mapping[str, Any],
) -> MaasServiceDetailListResponse:
    _validate_strict_read_envelope(raw)
    details = []
    for item in _rows(raw, "addSrvList", "MaaS service details"):
        details.append(
            _parse_add_srv_item(item, "MaaS service detail", "MaaS detail info")
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
        if isinstance(value, str):
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
) -> int | None:
    """Kotlin ``Int`` 필드 — 없으면 ``0``(앱의 기본값), 읽을 수 없는 모양이면 ``None``.

    Psg.java declares these Kotlin `Int`, but the live server sends
    zero-padded ASCII-decimal strings for at least custAgeFrom/custAgeTo/
    psgPrnbFrom/psgPrnbTo ("0000", "0999", ...), not bare JSON integers
    (live-confirmed 2026-09-21).
    """
    if data.get(key) is None:
        return 0
    return _optional_integer(data, key, context)


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
                # psgPrnbFrom/psgPrnbTo below.
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
        # field (@SerialName("rsvCnt")), not a Java int. Read it as a scalar string ("0007" stays "0007").
        reservation_count=_optional_scalar_string(
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
                        # Seat.scarNo is the one non-String field on this row:
                        # Seat.java:35 declares `public final int scarNo` and
                        # the synthetic constructor takes it as
                        # `@SerialName("scarNo") int i2` (Seat.java:53).
                        #
                        # 7.0.6 deserializes this route with kotlinx.serialization,
                        # not Gson: NetworkServiceKt.java:15-31 builds the shared
                        # `KJson` and calls setIgnoreUnknownKeys/setEncodeDefaults/
                        # setCoerceInputValues/setLenient with one protected
                        # literal compared `> 0` and setExplicitNulls with
                        # another compared `> 1`. The literals are AlienGuard
                        # protected, so read the values as inferred rather than
                        # confirmed -- but lenient mode is what makes a quoted
                        # "3" acceptable for an Int. Either way this reader
                        # accepts both "3" and 3 on purpose.
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
        changed_acceptance_reservation_no=_optional_scalar_string(
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
    # h_psg_tp_dv_nm is a real key, not a third-party invention.
    # `grep -r h_psg_tp_dv_nm analysis/` returns 2 hits: the app's OWN captured
    # sample of this very response, embedded at BasketTicketDataKt.java:44 (and
    # its smali twin smali_classes6/.../BasketTicketDataKt.smali:89), where it
    # sits at /jrny_infos/jrny_info[*]/seat_infos/seat_info[0] with the value
    # '어른'. That is one embedded sample, not a guarantee; a 2026-09-22
    # single-account observation (8 seat rows, capture not linked here, so
    # unverified) also saw it next to h_psg_tp_cd. It IS absent from
    # ReservationOutSeatInfo's @SerialName set (ReservationOutSeatInfo.java:81).
    # Modelled; the server is not known to always send it.
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
    for journey in _nested_rows(
        raw,
        "jrny_infos",
        "jrny_info",
        "ticket reservation detail",
    ):
        seats = []
        for seat in _nested_rows(
            journey,
            "seat_infos",
            "seat_info",
            "ticket reservation detail journey",
        ):
            seats.append(
                ReservationSeatDetail(
                    **_nullable_scalar_fields(seat, _RESERVATION_SEAT_DETAIL_FIELDS, "reservation seat detail"),
                    raw=seat,
                )
            )
        journeys.append(
            ReservationDetailJourney(
                **_nullable_scalar_fields(journey, _RESERVATION_DETAIL_JOURNEY_FIELDS, "reservation detail journey"),
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
    # "h_pbp_acep_tgt_flg" is not mapped: SelTicketInfo does
    # not carry it. It is not even a TicketDetailOut serial name — the 32
    # explicit @SerialName entries at TicketDetailOut.java:117 do not include it;
    # it belongs to MyTicketListOutTicket.java:92,300. Live, neither
    # h_pbp_acep_tgt_flg nor the pbpAcepTgtFlg fallback appeared in any of 40
    # responses (20 tickets x from_purchase_history False/True, 2026-09-22),
    # including the 6 whose list row says 'Y'. Decisive: TicketDetailOut declares
    # pbpAcepTgtFlg NON-FINAL with a setter (TicketDetailOut.java:65 is a bare
    # `public String`, and its setPbpAcepTgtFlg is at TicketDetailOut.java:1936
    # -- spelled out because the nearest preceding citation is
    # MyTicketListOutTicket.java, so bare :65/:1936 would point at the wrong
    # file) and the app
    # INJECTS the list row's value right after SelTicketInfo succeeds
    # (MyTicketBaseViewModel.java:769) before echoing it into the refund
    # (MyTicketDetailViewModel.java:1521) — it would not need to if the server
    # sent it. Callers should read it from
    # TicketListTicket.pbp_acceptance_target_flag, which is exactly where the app
    # reads it. The pbpAcepTgtFlg fallback below stays — it is the correct
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

    평범한 승차권에는 없으므로 부재가 오류가 아닙니다. 봉투 키
    ``dcnt_crd_info`` 는 ``TicketDetailOut.java:438`` 의 ``@SerialName`` 이고,
    구간 목록의 전선 키 ``appSegList`` 는 ``DiscountCardInfo.java:28`` 의 필드
    이름입니다 — 이 클래스 안에서 ``appSegList`` 만 ``@SerialName`` 이 없어
    kotlinx 기본값(= 프로퍼티 이름)이 그대로 전선 철자가 됩니다
    (나머지 넷은 ``:113-125`` 에 ``h_*`` 이름이 붙어 있습니다).

    이 라우트는 kotlinx.serialization 으로 읽히고(``NetworkServiceKt.java:15-31``
    의 공유 ``KJson``), 7.0.6 의 게터는 ``getAppSegList()``
    (``DiscountCardInfo.java:244``)입니다.
    """
    info = _optional_mapping(raw, "dcnt_crd_info", "refund ticket detail")
    if info is None:
        return None
    sections = []
    for item in _rows(
        info,
        "appSegList",
        "refund ticket detail dcnt_crd_info",
    ):
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
    for journey in _nested_rows(
        raw,
        "ticket_infos",
        "ticket_info",
        "refund ticket detail",
    ):
        seats = []
        for seat in _rows(
            journey,
            "tk_seat_info",
            "refund ticket detail ticket_info",
        ):
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
    # (위 _REFUND_TICKET_DETAIL_FIELDS 주석). h_pbp_acep_tgt_flg 는 이 DTO 의
    # 키가 아니어서 매핑하지 않습니다.
    if "pbpAcepTgtFlg" in raw:
        detail_fields["pbp_acceptance_target_flag"] = _optional_scalar_string(
            raw, "pbpAcepTgtFlg", "refund ticket detail"
        )
    # h_qrcode has an explicit @SerialName (TicketDetailOut.java:478).
    qr_code = _optional_scalar_string(raw, "h_qrcode", "refund ticket detail")
    # psgNmList/seatTicketList/limousine/dtlList have NO explicit @SerialName
    # on TicketDetailOut (PROTECTED wire spelling) — the Kotlin field names
    # are used as a best-effort key, matching this module's treatment of
    # other unannotated fields (e.g. GuideSeatCndOut.timeStamp).
    passenger_names = tuple(_rows(raw, "psgNmList"))
    seat_tickets = tuple(_rows(raw, "seatTicketList"))
    limousine = _optional_mapping(raw, "limousine")
    delay_details = tuple(_rows(raw, "dtlList"))
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

    7.0.6 의 응답 DTO 는 ``SeatAvailabilityOut.java:28-42``
    (``NetworkApi.java:806-808`` 의 ``seatAvailabilityCall``)이고 그 안의 두 행
    타입은 ``ChgStnInfo.java:21-35`` 와 ``ChgRsnInfo.java:21-24`` 입니다.
    세 DTO 가 선언한
    필드가 전부 코틀린 ``String`` 이라 모두 :func:`_optional_scalar_string` 으로
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
            value
            for value in _rows(
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
            value
            for value in _rows(
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

    7.0.6 의 사슬은 ``NetworkApi.java:234-236``
    (``@POST(".../research.tripChgOgtk.do") → OgTicketInquiryOut``) →
    ``OgTicketInquiryOut.java:27`` 의 ``List<OrgTk> orgTkList`` →
    ``OrgTk.java:38`` 의 ``List<JrnyInfo> jrnyList`` → ``JrnyInfo.java:58`` 의
    ``List<SeatInfo> seatList`` 입니다.

    **동명 오인 경고.** 7.0.6 에 ``model/Jrny.java`` 와 ``model/Seat.java`` 가 실제로
    있지만 **이 응답의 타입이 아닙니다** — ``Jrny.java:29-38`` 의 필드는
    ``acepCustNm``/``acepCustTeln``/``pbpAcepKndNm``/``pbpRsvNo``/
    ``wdrwPsbFlg`` 로 PBP(대리수령) 접수 정보이고, 그것이 담은
    ``Seat.java:27-36`` 은 필드가 다섯이며 ``scarNo`` 가 ``int`` 입니다. 두
    클래스는 ``DeliveredTicketOut``(``:27``) → ``Tk``(``:27``) 사슬, 즉
    ``tk.pbpAcepSpec.do``(``NetworkApi.java:367-369``) 쪽에 속합니다. 원표
    조회의 여정/좌석은 위의 ``JrnyInfo``/``SeatInfo`` 이고 아래 필드 맵도
    그쪽 철자를 씁니다. 같은 이름을 보고 갈아 끼우지 마십시오.

    ``cmpnList`` 와 ``stlList`` 는 일부러 파싱하지 않습니다. 지연증명 반환번호
    (``Cmpn.java:35-38`` 의 ``dlayOgtkRetPwd``/``dlayOgtkSaleDt``/
    ``dlayOgtkSaleSqno``/``dlayOgtkWctNo``)와 카드/승인번호
    (``Stl.java:29,32,37`` 의 ``apvNo``/``prepCrdNo``/``stlCrdNo``) 같은 소지
    자격증명을
    더 싣는데 변경 과정의 어느 단계도 그것을 필요로 하지 않습니다. ``raw`` 는
    원본을 그대로 보존하므로 그 안의 두 목록도 그대로 남습니다.
    """
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket in _rows(raw, "orgTkList", "original ticket inquiry"):
        journeys = []
        for journey in _rows(
            ticket,
            "jrnyList",
            "original ticket",
        ):
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
                    seat_value
                    for seat_value in _rows(
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
