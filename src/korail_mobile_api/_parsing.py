# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""선택값은 관대하게, 후속 요청에 필요한 값은 엄격하게 읽습니다; 공통 규칙은 checks/BEHAVIOR.md 참고."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, ParamSpec, TypedDict, TypeVar

from .errors import KorailApiError, KorailProtocolError
from .models import ReservationPassengerInfo

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _preserve_read_raw(parser: Callable[_P, _R]) -> Callable[_P, _R]:
    """파서가 거절한 응답 전체를 기존 예외의 raw 에, 기존 부분 원문을 parser_raw 에 남깁니다. 검사·재전송은 하지 않습니다."""

    @wraps(parser)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return parser(*args, **kwargs)
        except KorailApiError as error:
            response = args[0] if args else kwargs.get("raw", kwargs.get("response"))
            raw = response if isinstance(response, Mapping) else getattr(response, "raw", response)
            if error.raw is not raw:
                error.parser_raw = error.raw
                error.raw = raw
            raise

    return wrapped


def _envelope(data: Mapping[str, Any]) -> dict[str, str | None]:
    """JSON 정수는 관측에 따라 문자열로 읽고, 다른 비문자열 값은 거절합니다."""
    envelope: dict[str, str | None] = {}
    invalid = []
    for name in ("h_msg_cd", "h_msg_txt", "strResult"):
        value = data.get(name)
        if isinstance(value, int) and not isinstance(value, bool):
            try:
                envelope[name] = str(value)
            except ValueError as exc:
                error = KorailProtocolError(
                    f"KORAIL response envelope field {name} is an integer too long to use"
                )
                error.raw = data
                raise error from exc
        elif value is None or isinstance(value, str):
            envelope[name] = value
        else:
            invalid.append(name)
    if invalid:
        error = KorailProtocolError(
            f"KORAIL response envelope fields must be strings or null: {', '.join(invalid)}"
        )
        error.raw = data
        raise error
    return envelope


class _ResponseFields(TypedDict):
    h_msg_cd: str | None
    h_msg_txt: str | None
    str_result: str | None
    raw: Mapping[str, object]


def _response_fields(raw: Mapping[str, object]) -> _ResponseFields:
    envelope = _envelope(raw)
    return {
        "h_msg_cd": envelope["h_msg_cd"],
        "h_msg_txt": envelope["h_msg_txt"],
        "str_result": envelope["strResult"],
        "raw": raw,
    }


def _optional_mapping(
    data: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any] | None:
    value = data.get(key)
    return value if isinstance(value, Mapping) else None


def _optional_list(
    data: Mapping[str, Any],
    key: str,
) -> list[Any]:
    value = data.get(key)
    return value if isinstance(value, list) else []


def _nested_rows(
    raw: Mapping[str, Any],
    outer_key: str,
    inner_key: str,
) -> list[Mapping[str, Any]]:
    return _rows(_optional_mapping(raw, outer_key), inner_key)


def _row(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(f"KORAIL {context} contained a non-object item")
    return value


def _rows(
    data: Mapping[str, Any] | None,
    key: str,
) -> list[Mapping[str, Any]]:
    if not isinstance(data, Mapping):
        return []
    return [item for item in _optional_list(data, key) if isinstance(item, Mapping)]


def _present_strings(
    data: Mapping[str, Any],
    keys: tuple[str, ...],
) -> tuple[str, ...]:
    values: list[str] = []
    for key in keys:
        value = _optional_scalar_string(data, key)
        if value is not None:
            values.append(value)
    return tuple(values)


def _strict_scalar_string(
    data: Mapping[str, object],
    key: str,
    context: str,
) -> str | None:
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    if type(value) is int:
        try:
            return str(value)
        except ValueError as exc:  # 파이썬의 정수→문자열 자릿수 한도
            raise KorailProtocolError(f"KORAIL {context} field {key} is an integer too long to use") from exc
    raise KorailProtocolError(f"KORAIL {context} field {key} must be a string, an integer, or null")


def _optional_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> str | None:
    """선택 스칼라를 문자열로 읽고 잘못된 값은 None으로 처리합니다."""
    try:
        return _strict_scalar_string(data, key, context)
    except KorailProtocolError:
        return None


def _optional_integer(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> int | None:
    """JSON 정수나 ASCII 숫자 문자열을 정수로 읽고 그 밖의 값은 None으로 처리합니다."""
    if data.get(key) is None:
        return None
    try:
        return _required_integer(data, key, context)
    except KorailProtocolError:
        return None


def _required_integer(
    data: Mapping[str, object],
    key: str,
    context: str,
) -> int:
    """필수 정수: JSON int 또는 ASCII 숫자 문자열(앞의 ``-`` 하나 허용)을 받습니다. null/bool/float·지수 표기는 거절합니다. 앱의 따옴표 숫자 처리는
    StreamingJsonDecoder.java:395-403 → kotlinx/serialization/json/internal/JsonReader.java:575-640 에 있고,
    첫 글자의 ``-`` 만 부호로 받습니다."""
    value = data.get(key)
    if type(value) is int:
        return value
    if isinstance(value, str):
        digits = value[1:] if value.startswith("-") else value
        if digits and all("0" <= character <= "9" for character in digits):
            try:
                return int(value)
            except ValueError as exc:
                raise KorailProtocolError(
                    f"KORAIL {context} field {key} has an unsupported ASCII-decimal length"
                ) from exc
    raise KorailProtocolError(f"KORAIL {context} field {key} must be an integer or an ASCII decimal string")


def _optional_bool(
    data: Mapping[str, object],
    key: str,
) -> bool | None:
    """불리언을 그대로 반환하고 누락·다른 타입은 None으로 처리합니다."""
    value = data.get(key)
    return value if isinstance(value, bool) else None


def _nullable_scalar_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
    context: str = "",
) -> dict[str, Any]:
    """String 선택값을 같은 규칙으로 읽으며 모델 생성자 **kwargs 호환을 위해 값 타입은 Any입니다."""
    return {
        attribute: _optional_scalar_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
    }


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
