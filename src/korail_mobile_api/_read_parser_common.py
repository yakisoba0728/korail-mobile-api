# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""조회 봉투와 필수 행 규칙, 승차권·계정이 공유하는 부가서비스 행을 읽습니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._parsing import _envelope, _nullable_scalar_fields, _optional_mapping, _rows, _strict_scalar_string
from .errors import SESSION_EXPIRED_CODE, KorailProtocolError, KorailSessionExpiredError, classify_app_error
from .read_models import MaasServiceDetail, MaasServiceDetailInfo


def _validate_envelope(
    raw: Mapping[str, Any],
    *,
    accepted_empty_codes: frozenset[str] = frozenset(),
    returned_failure_codes: frozenset[str] = frozenset(),
    return_all_failures: bool = False,
    allow_result_only_success: bool = False,
) -> bool:
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    # raw 를 직접 받는 호출자는 http.parse_base_response 를 거치지 않으므로 봉투 필드 타입을 여기서도 확인합니다.
    envelope = _envelope(raw)
    if "strResult" not in raw:
        raise KorailProtocolError(
            "KORAIL response omitted strResult; the protected APK default "
            "cannot be inferred for this typed read"
        )
    if allow_result_only_success and ("h_msg_cd" not in raw and "h_msg_txt" not in raw):
        if raw["strResult"] != "SUCC":
            raise KorailProtocolError("KORAIL result-only envelope requires the exact success result")
        return False
    code = envelope["h_msg_cd"]
    message = envelope["h_msg_txt"]
    result = envelope["strResult"]
    # 앱은 strResult 실패일 때만 로그인 필요로 봅니다(CommonOut.java:426-438).
    if result == "FAIL" and code == SESSION_EXPIRED_CODE:
        raise KorailSessionExpiredError(code, message, raw=raw)
    failed = result == "FAIL"
    if (
        failed
        and not return_all_failures
        and code not in accepted_empty_codes
        and code not in returned_failure_codes
    ):
        raise classify_app_error(code, message, raw=raw)
    return failed


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
        raise KorailProtocolError("KORAIL strict read response strResult must be SUCC")


def _required_read_rows(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Mapping[str, Any]]:
    """누락·null·비객체 행은 거절합니다(ReceiptInfos.java:49, DeliveredTicketOut.java:50 의 필수 마스크)."""
    value = data.get(key)
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise KorailProtocolError(f"KORAIL {context} field {key} must be an object list")
    return value


def _required_read_strings(
    data: Mapping[str, Any],
    fields: Mapping[str, str],
    context: str,
) -> dict[str, Any]:
    """누락·null 은 거절하고, JSON 정수는 문자열로 받습니다(String 선언 필드가 정수로 온 관측, :func:`_strict_scalar_string`)."""
    values = {}
    for attr, key in fields.items():
        value = _strict_scalar_string(data, key, context)
        if value is None:
            raise KorailProtocolError(f"KORAIL {context} field {key} is required")
        values[attr] = value
    return values


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


def _parse_add_srv_item(
    item: Mapping[str, Any],
    context: str,
    info_context: str,
) -> MaasServiceDetail:
    """MaaS 상세와 승차권의 부가서비스를 같은 모델로 읽습니다 (AddSrvItem.java:28-49, MaasDetailOut.java:27,
    MyTicketListOutReservation.java:39). @SerialName 이 없고 serializer 이름이 보호돼 있어 전송 키는 속성명에 따른 추정입니다."""
    info_raw = _optional_mapping(item, "detailInfo")
    detail_info = None
    if info_raw is not None:
        detail_info = MaasServiceDetailInfo(
            **_nullable_scalar_fields(info_raw, _MAAS_DETAIL_INFO_FIELDS, info_context),
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
    """객체가 아니면 ``None``."""
    item = _optional_mapping(data, key)
    if item is None:
        return None
    return _parse_add_srv_item(item, item_context, info_context)


def _optional_read_rows(data: Mapping[str, Any], key: str, context: str) -> list[Mapping[str, Any]]:
    """선택·nullable 객체 목록을 읽습니다. 누락·null 은 빈 목록이고, 목록이 아니거나 객체가 아닌 행은 거절합니다."""
    if data.get(key) is None:
        return []
    return _required_read_rows(data, key, context)
