# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""읽기 라우트의 요청 폼·쿼리 빌더.

승차권·예약·환불·마일리지·할인카드·MaaS 등 읽기 전용 라우트. 기본 조회는
:mod:`korail_mobile_api.payloads`, 상태 변경은
:mod:`korail_mobile_api.mutation_payloads`.

필드 이름·순서는 APK Retrofit 선언 기준입니다. 그 정확한 계약을 고정하던 테스트
픽스처는 삭제됐고, 지금 계약을 말하는 것은 각 빌더의 코드뿐입니다.
"""
from __future__ import annotations

import time
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Literal

from .config import KorailConfig
from .payloads import _device_version, _is_ascii_digits, build_cache_query
from .read_models import (
    CommuterInfoResponse,
    CommuterPassengerOption,
    PassMenuData,
)


if TYPE_CHECKING:
    from .mutation_models import StationRefundVerificationRequest


def _positive_int(value: int, name: str) -> str:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return str(value)


def _required_text(value: str | None, name: str) -> str:
    """``value`` 를 그대로 돌려주되 없거나 빈 문자열이면 거부합니다.

    호출자 대부분이 서버 응답에서 파싱한 선택 필드를 그대로 넘기므로, ``None``
    도 인자로 받아 ``TypeError`` 가 아닌 ``ValueError`` 로 바꿉니다.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _optional_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value


def _ascii_digits(
    value: str,
    name: str,
    *,
    lengths: frozenset[int] | None = None,
    maximum_length: int | None = None,
    allow_empty: bool = False,
) -> str:
    """ASCII 숫자 문자열인지 확인합니다 (``payloads._is_ascii_digits`` 재사용).

    ``lengths`` 를 주면 그 길이 집합에 들어야 합니다 — 날짜(``YYYYMMDD``,
    8), 시각(6), 원표일자(4 또는 8)처럼 길이가 정해진 필드용입니다.
    ``lengths`` 를 생략하고 ``maximum_length`` 만 주면 1자리부터 그 자릿수
    까지, 둘 다 생략하면 자릿수를 보지 않습니다 — 열차번호·순번처럼 길이가
    자유로운 식별자용입니다. ``allow_empty`` 면 빈 문자열을 그대로
    통과시킵니다.
    """
    if allow_empty and value == "":
        return value
    if lengths is not None:
        if not _is_ascii_digits(value, lengths):
            if len(lengths) == 1:
                (length,) = lengths
                raise ValueError(
                    f"{name} must contain exactly {length} ASCII digits"
                )
            expected = ", ".join(str(length) for length in sorted(lengths))
            raise ValueError(f"{name} must contain {expected} ASCII digit(s)")
        return value
    if (
        not isinstance(value, str)
        or not value
        or any(character < "0" or character > "9" for character in value)
        or (maximum_length is not None and len(value) > maximum_length)
    ):
        suffix = (
            f" with at most {maximum_length} digits"
            if maximum_length is not None
            else ""
        )
        raise ValueError(f"{name} must be an ASCII decimal string{suffix}")
    return value


def _positive_ascii_text(
    value: str,
    name: str,
    *,
    allow_empty: bool = False,
) -> str:
    if allow_empty and value == "":
        return value
    resolved = _ascii_digits(value, name)
    if not any(character != "0" for character in resolved):
        raise ValueError(f"{name} must be a positive ASCII decimal string")
    return resolved


def _passenger_count(value: int, name: str) -> int:
    if type(value) is not int or not 1 <= value <= 9:
        raise ValueError(f"{name} must be an integer from 1 through 9")
    return value


@dataclass(frozen=True)
class FreeSeatCarRequest:
    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    departure_construction_order: str = field(repr=False)
    arrival_construction_order: str = field(repr=False)
    departure_run_order: str = field(repr=False)
    arrival_run_order: str = field(repr=False)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        _ascii_digits(self.run_date, "run_date", lengths=frozenset({8}))
        _ascii_digits(
            self.train_no,
            "train_no",
            maximum_length=5,
        )
        _ascii_digits(
            self.departure_construction_order,
            "departure_construction_order",
        )
        _ascii_digits(
            self.arrival_construction_order,
            "arrival_construction_order",
        )
        _ascii_digits(
            self.departure_run_order,
            "departure_run_order",
        )
        _ascii_digits(
            self.arrival_run_order,
            "arrival_run_order",
        )


@dataclass(frozen=True)
class GuideSeatConditionRequest:
    seat_attribute_code: str = field(repr=False)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        _required_text(self.seat_attribute_code, "seat_attribute_code")


@dataclass(frozen=True)
class SeatAssignmentScheduleRequest:
    menu_id: str = field(repr=False)
    departure_date: str = field(repr=False)
    departure_time: str = field(repr=False)
    departure_station_name: str = field(repr=False)
    arrival_station_name: str = field(repr=False)
    train_group_code: str = field(repr=False)
    room_class_code: str = field(repr=False)
    seat_attribute_code: str = field(repr=False)
    passenger_count: int = field(repr=False)
    standing_detour_division_name: str = field(repr=False)
    transfer_type_code: str = field(repr=False)
    connection_arrival_station_name: str = field(repr=False)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        _required_text(self.menu_id, "menu_id")
        _ascii_digits(self.departure_date, "departure_date", lengths=frozenset({8}))
        _ascii_digits(self.departure_time, "departure_time", lengths=frozenset({6}))
        _required_text(
            self.departure_station_name,
            "departure_station_name",
        )
        _required_text(self.arrival_station_name, "arrival_station_name")
        _required_text(self.train_group_code, "train_group_code")
        _required_text(self.room_class_code, "room_class_code")
        _required_text(self.seat_attribute_code, "seat_attribute_code")
        _passenger_count(self.passenger_count, "passenger_count")
        _optional_text(
            self.standing_detour_division_name,
            "standing_detour_division_name",
        )
        if self.transfer_type_code not in {"1", "2"}:
            raise ValueError("transfer_type_code must be '1' or '2'")
        _optional_text(
            self.connection_arrival_station_name,
            "connection_arrival_station_name",
        )


@dataclass(frozen=True)
class MergeSeatsInquiryRequest:
    boarding_datetime: str = field(repr=False)
    run_datetime: str = field(repr=False)
    train_no: str = field(repr=False)
    departure_station_name: str = field(repr=False)
    arrival_station_name: str = field(repr=False)
    selected_station_name: str | None = field(repr=False)
    room_class_code: str = field(repr=False)
    seat_attribute_code: str = field(repr=False)
    passenger_count: int = field(repr=False)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        _ascii_digits(self.boarding_datetime, "boarding_datetime", lengths=frozenset({14}))
        _ascii_digits(self.run_datetime, "run_datetime", lengths=frozenset({14}))
        _ascii_digits(
            self.train_no,
            "train_no",
            maximum_length=5,
        )
        _required_text(
            self.departure_station_name,
            "departure_station_name",
        )
        _required_text(self.arrival_station_name, "arrival_station_name")
        if self.selected_station_name is not None:
            _required_text(self.selected_station_name, "selected_station_name")
        _required_text(self.room_class_code, "room_class_code")
        _required_text(self.seat_attribute_code, "seat_attribute_code")
        _passenger_count(self.passenger_count, "passenger_count")


def build_free_seat_car_form(
    request: FreeSeatCarRequest,
) -> dict[str, str]:
    if not isinstance(request, FreeSeatCarRequest):
        raise TypeError("request must be a FreeSeatCarRequest")
    FreeSeatCarRequest._validate(request)
    return {
        "runDt": request.run_date,
        "trnNo": request.train_no.zfill(5),
        "dptStnConsOrdr": request.departure_construction_order,
        "arvStnConsOrdr": request.arrival_construction_order,
        "dptStnRunOrdr": request.departure_run_order,
        "arvStnRunOrdr": request.arrival_run_order,
    }


def build_guide_seat_condition_form(
    request: GuideSeatConditionRequest,
) -> dict[str, str]:
    if not isinstance(request, GuideSeatConditionRequest):
        raise TypeError("request must be a GuideSeatConditionRequest")
    GuideSeatConditionRequest._validate(request)
    return {"rqSeatAttCd": request.seat_attribute_code}


def build_seat_assignment_schedule_form(
    request: SeatAssignmentScheduleRequest,
) -> dict[str, str]:
    if not isinstance(request, SeatAssignmentScheduleRequest):
        raise TypeError("request must be a SeatAssignmentScheduleRequest")
    SeatAssignmentScheduleRequest._validate(request)
    form = {
        "menuId": request.menu_id,
        "dptDt": request.departure_date,
        "dptTm": request.departure_time,
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
        "trnGpCd": request.train_group_code,
        "psrmClCd": request.room_class_code,
        "dirtChtnDvCd": request.transfer_type_code,
        "chtnArvRsStnNm": request.connection_arrival_station_name,
    }
    # ``seatAttCdN``/``psgNumN``/``stlbDturDvNmN`` 은 승객 한 명당 한 벌인
    # 번호 그룹입니다. ``psgNumN`` 은 그 자리의 **점유 플래그**(0/1)이지
    # 인원수가 아니라서, 예전처럼 ``psgNum1`` 에 총원을 넣으면 2 이상은
    # 서버가 전부 ``SUPDATE`` 로 막았습니다 -- 2026-09-22 라이브 확인:
    # ``psgNum1`` 이 ``"0"``/``"1"`` 이면 ``WRG000000`` 이지만
    # ``"2"``/``"02"``/``"3"``/``"9"`` 는 SUPDATE 이고, 대신 그룹을 1..9 까지
    # 늘리면 9명까지 그대로 통과합니다.
    for slot in range(1, request.passenger_count + 1):
        form[f"seatAttCd{slot}"] = request.seat_attribute_code
        form[f"psgNum{slot}"] = "1"
        form[f"stlbDturDvNm{slot}"] = request.standing_detour_division_name
    return form


def build_merge_seats_inquiry_form(
    request: MergeSeatsInquiryRequest,
) -> dict[str, str]:
    if not isinstance(request, MergeSeatsInquiryRequest):
        raise TypeError("request must be a MergeSeatsInquiryRequest")
    MergeSeatsInquiryRequest._validate(request)
    form = {
        "abrdDt": request.boarding_datetime,
        "runDt": request.run_datetime,
        "trnNo": request.train_no.zfill(5),
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
        "psrmClCd": request.room_class_code,
        "seatAttCd": request.seat_attribute_code,
        "totPsgNum": str(request.passenger_count),
    }
    if request.selected_station_name is not None:
        form["selRsStnNm"] = request.selected_station_name
    return form


@dataclass(frozen=True)
class PassScheduleRequest:
    selected_train_code: str = field(repr=False)
    departure_date: str = field(repr=False)
    departure_time: str = field(repr=False)
    transfer_type_code: str = field(repr=False)
    pass_kind_code: str = field(repr=False)
    pass_period_code: str = field(repr=False)
    pass_age_code: str = field(repr=False)
    page_no: str = field(repr=False)
    page_size: str = field(repr=False)
    departure_station_name: str = field(repr=False)
    arrival_station_name: str = field(repr=False)
    weekend_use_flag: str = field(repr=False)

    def __post_init__(self) -> None:
        _validate_pass_schedule_request(self)


def _validate_pass_schedule_request(request: PassScheduleRequest) -> None:
    _required_text(request.selected_train_code, "selected_train_code")
    _ascii_digits(request.departure_date, "departure_date", lengths=frozenset({8}))
    _ascii_digits(request.departure_time, "departure_time", lengths=frozenset({6}))
    _required_text(request.transfer_type_code, "transfer_type_code")
    _required_text(request.pass_kind_code, "pass_kind_code")
    _required_text(request.pass_period_code, "pass_period_code")
    _required_text(request.pass_age_code, "pass_age_code")
    _positive_ascii_text(request.page_no, "page_no")
    _positive_ascii_text(
        request.page_size,
        "page_size",
        allow_empty=True,
    )
    _required_text(
        request.departure_station_name,
        "departure_station_name",
    )
    _required_text(request.arrival_station_name, "arrival_station_name")
    if request.weekend_use_flag not in {"Y", "N"}:
        raise ValueError("weekend_use_flag must be 'Y' or 'N'")


def build_pass_schedule_form(
    request: PassScheduleRequest,
) -> dict[str, str]:
    if not isinstance(request, PassScheduleRequest):
        raise TypeError("request must be a PassScheduleRequest")
    _validate_pass_schedule_request(request)
    return {
        "selGoTrain": request.selected_train_code,
        "selGoAbrdDt": request.departure_date,
        "txtGoHour": request.departure_time,
        "radChgTrnDvCd": request.transfer_type_code,
        "txtCmtrKndCd": request.pass_kind_code,
        "txtCmtrUtlTrmCd": request.pass_period_code,
        "txtCmtrUtlAgeCd": request.pass_age_code,
        "txtSelPage": request.page_no,
        "txtCntPerPage": request.page_size,
        "txtGoStart": request.departure_station_name,
        "txtGoEnd": request.arrival_station_name,
        "txtWkndUseFlg": request.weekend_use_flag,
    }


def build_service_status_query(
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    """``MobileService.cache`` 의 ``timeStamp`` 쿼리 — 캐시 파일 요청과 같은 모양입니다."""
    return build_cache_query(timestamp_ms)


def build_cart_list_form(
    pnr_no: str = "",
    additional_service_request_no: str = "",
) -> dict[str, str]:
    return {
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
        "addSrvReqNo": _optional_text(
            additional_service_request_no,
            "additional_service_request_no",
        ),
    }


def build_delay_discount_ticket_form(
    departure_date_to: str,
) -> dict[str, str]:
    # 7.0.6 DelayDiscountViewIn 은 속성 dptDtTo 에 @SerialName("h_page_no") 를 달았고
    # (암호화되지 않은 애너테이션 상수), serializer 다섯째 이름의 암호문도 9바이트로
    # len("h_page_no") 와 같다. wire 키만 바꾸고 앱 속성명을 따른 인자 이름은 둔다.
    # analysis/jadx/sources/com/korail/talk/network/model/DelayDiscountViewIn.java:50,77
    # analysis/jadx/sources/com/korail/talk/network/model/DelayDiscountViewIn$$serializer.java:38
    # 선언 수준 근거일 뿐이다. 이 입력을 만드는 7.0.6 화면은 찾지 못했다. 2026-09-16
    # 실서버에서 h_page_no=날짜·dptDtTo=날짜·키 없음·h_page_no=1 이 모두 같은 빈 SUCC 였다.
    # 지연할인권이 없는 계정이라 키는 아직 실서버로 가려지지 않았다.
    return {
        "h_page_no": _ascii_digits(
            departure_date_to, "departure_date_to", lengths=frozenset({8})
        )
    }


def build_discount_coupon_form(
    page_no: int = 1,
    pnr_no: str = "",
) -> dict[str, str]:
    return {
        "txtSelPage": _positive_int(page_no, "page_no"),
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
    }


def build_pass_availability_form(
    kind_code: str,
    period_code: str,
    age_code: str,
) -> dict[str, str]:
    return {
        "txtCmtrKndCd": _required_text(kind_code, "kind_code"),
        "txtCmtrUtlTrmCd": _required_text(period_code, "period_code"),
        "txtCmtrUtlAgeCd": _required_text(age_code, "age_code"),
    }


def build_trip_menu_form(config: KorailConfig) -> dict[str, str]:
    return {
        **_device_version(config),
        "timeStamp": str(int(time.time() * 1000)),
    }


def build_pass_menu_form(menu_no: str) -> dict[str, str]:
    return {"menuNo": _required_text(menu_no, "menu_no")}


def build_crew_request_list_query(
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    """``crwCallRq.do`` 의 승무원 호출 사유 조회 쿼리를 만듭니다.

    7.0.6 ``CrewCallCommonIn.java:50`` 의 합성 생성자는 ``Device``/``Version``/
    ``Key``/``lang`` 외에 ``timeStamp``(``long``) 하나만 선언합니다. 이전 구현이
    보내던 ``qryDvCd`` 는 이 DTO 에 없는 이름입니다 — ``TrainScheduleIn`` 등
    무관한 다른 DTO 에만 있는 필드였습니다. 유일한 호출부
    ``NetworkRepositoryImpl.java:4105-4107`` 는 ``new CrewCallCommonIn(timestamp)``
    만 만듭니다. ``timestamp_ms`` 를 주지 않으면 현재 밀리초 epoch 입니다
    (``build_cache_query`` 와 같은 패턴).

    이 함수는 이전엔 필수 ``query_division_code: str`` 하나를 받았습니다.
    ``qryDvCd`` 가 이 라우트에 존재하지 않는 필드라 그 매개변수 자체가
    UNSUPPORTED 였으므로 제거했습니다. 현재 유일한 호출부인
    ``client.py::get_crew_request_list`` 는 여전히
    ``build_crew_request_list_query(query_division_code)`` 로 그 값을 위치
    인자로 넘기고 있어, 문자열이 ``timestamp_ms`` 자리에 들어가 아래 검증에서
    :class:`ValueError` 가 됩니다 — client.py 쪽에서 ``get_crew_request_list``
    의 시그니처와 이 호출을 ``build_crew_request_list_query()`` (또는 호출자가
    타임스탬프를 지정하고 싶다면 ``build_crew_request_list_query(timestamp_ms=...)``)
    로 바꾸는 후속 수정이 필요합니다.
    """
    if timestamp_ms is not None and (
        type(timestamp_ms) is not int or timestamp_ms < 0
    ):
        raise ValueError("timestamp_ms must be a non-negative integer or None")
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}


def build_commuter_kind_menu_query(
    commuter_kind_code: str,
) -> dict[str, str]:
    return {
        "cmtrKndCd": _required_text(
            commuter_kind_code,
            "commuter_kind_code",
        )
    }


def build_product_reservations_query(
    page_no: int = 1,
    page_size: int = 20,
    *,
    reservation_status_code: str | None = None,
    payment_status_code: str | None = None,
) -> dict[str, str]:
    query = {
        "txtSelPage": _positive_int(page_no, "page_no"),
        "txtCntPerPage": _positive_int(page_size, "page_size"),
    }
    # ProductListIn has both status fields. Their UI defaults are AlienGuard
    # protected in 7.0.6 ProductReservationViewModel.java:836, so require the
    # caller to supply observed codes instead of inventing defaults.
    if reservation_status_code is not None:
        query["txtRsvSttCd"] = _required_text(
            reservation_status_code, "reservation_status_code"
        )
    if payment_status_code is not None:
        query["txtStlSttCd"] = _required_text(
            payment_status_code, "payment_status_code"
        )
    return query


def build_product_detail_query(
    reservation_no: str,
    reservation_sequence: str | None = None,
) -> dict[str, str]:
    query = {
        "txtVrRsNo": _required_text(reservation_no, "reservation_no"),
    }
    if reservation_sequence is not None:
        query["txtVrRsvSqNo"] = _required_text(
            reservation_sequence, "reservation_sequence"
        )
    return query


def build_ticket_receipt_form(
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
    txt_index: str | None = None,
) -> dict[str, str]:
    form = {
        # 4자리 ``MMDD`` 만 받습니다. 예전에는 8자리도 통과시켰는데, 서버는
        # 8자리를 언제나 ``ERZ800027`` 로 되돌려보냅니다 -- 2026-09-22 에 실제
        # 승차권 128장으로 확인(4자리 128/128 성공). 8자리를 여기서 막지 않으면
        # 호출자가 ``TicketListTicket.sale_date`` 를 그대로 넘겨 놓고 원인이
        # 모호한 서버 오류를 받습니다. 자릿수 규칙 전체는
        # :class:`OriginalTicketReference` 의 docstring 에 있습니다.
        "h_orgtk_sale_dt": _ascii_digits(sale_date, "sale_date", lengths=frozenset({4})),
        "h_orgtk_wct_no": _required_text(window_no, "window_no"),
        "h_orgtk_sale_sqno": _required_text(
            sale_sequence,
            "sale_sequence",
        ),
        "h_orgtk_tk_ret_pwd": _required_text(
            return_password,
            "return_password",
        ),
    }
    if txt_index is not None:
        if not isinstance(txt_index, str):
            raise ValueError("txt_index must be a string or None")
        if txt_index.strip():
            form["txtIndex"] = txt_index
    return form


def _calendar_date(value: str, name: str) -> date:
    _ascii_digits(value, name, lengths=frozenset({8}))
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid calendar date") from exc


def _add_calendar_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, zero_based_month = divmod(index, 12)
    month = zero_based_month + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def _validate_maas_service_detail_query_values(
    start_date: str | None,
    end_date: str | None,
) -> None:
    if start_date is None or end_date is None:
        if start_date is not None or end_date is not None:
            raise ValueError("MaaS history requires both dates or neither")
        return
    start = _calendar_date(start_date, "start_date")
    end = _calendar_date(end_date, "end_date")
    if end < start:
        raise ValueError("end_date must not be before start_date")
    if end > _add_calendar_months(start, 3):
        raise ValueError(
            "MaaS history range must be at most three calendar months"
        )


@dataclass(frozen=True)
class MaasServiceDetailQuery:
    start_date: str | None = field(default=None, repr=False)
    end_date: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        _validate_maas_service_detail_query_values(
            self.start_date,
            self.end_date,
        )

    @classmethod
    def current(cls) -> MaasServiceDetailQuery:
        return cls()

    @classmethod
    def history(
        cls,
        start_date: str,
        end_date: str,
    ) -> MaasServiceDetailQuery:
        return cls(start_date=start_date, end_date=end_date)


def build_multi_child_discount_target_form(
    departure_date: str,
) -> dict[str, str]:
    return {"dptDt": _ascii_digits(departure_date, "departure_date", lengths=frozenset({8}))}


def build_korail_point_summary_form() -> dict[str, str]:
    """Constant form — ``KorailPointInquiryDao.java:87-92``."""
    return {"point_dv_cd": "0"}


#: ``"1"`` KTX 마일리지, ``"2"`` 철도포인트.
KorailMileageLedger = Literal["1", "2"]

#: ``"0"`` 전체, ``"1"`` 적립, ``"2"`` 사용.
KorailMileageMovement = Literal["0", "1", "2"]

#: ``MileageHistoryActivity.java:289,543`` KTX, ``:313`` 철도포인트.
KORAIL_MILEAGE_LEDGER_KTX: KorailMileageLedger = "1"
KORAIL_MILEAGE_LEDGER_RAIL_POINT: KorailMileageLedger = "2"

#: ``MileageHistoryActivity.java:566`` 드롭다운 인덱스(``:502``).
KORAIL_MILEAGE_MOVEMENT_ALL: KorailMileageMovement = "0"
KORAIL_MILEAGE_MOVEMENT_EARNED: KorailMileageMovement = "1"
KORAIL_MILEAGE_MOVEMENT_SPENT: KorailMileageMovement = "2"

_KORAIL_MILEAGE_LEDGERS = frozenset(
    {KORAIL_MILEAGE_LEDGER_KTX, KORAIL_MILEAGE_LEDGER_RAIL_POINT}
)
_KORAIL_MILEAGE_MOVEMENTS = frozenset(
    {
        KORAIL_MILEAGE_MOVEMENT_ALL,
        KORAIL_MILEAGE_MOVEMENT_EARNED,
        KORAIL_MILEAGE_MOVEMENT_SPENT,
    }
)


@dataclass(frozen=True)
class MileageHistoryRequest:
    """마일리지 내역 조회 입력 (``XPointService.java:26-28``).

    기본값: KTX 마일리지 원장, 전체 증감, 페이지 1.
    ``start_date``/``end_date`` 는 호출자가 반드시 제공해야 합니다.
    """

    start_date: str
    end_date: str
    ledger: KorailMileageLedger = KORAIL_MILEAGE_LEDGER_KTX
    movement: KorailMileageMovement = KORAIL_MILEAGE_MOVEMENT_ALL
    page_no: int = 1


def build_mileage_history_form(
    request: MileageHistoryRequest,
) -> dict[str, str]:
    if not isinstance(request, MileageHistoryRequest):
        raise TypeError("request must be a MileageHistoryRequest")
    if request.ledger not in _KORAIL_MILEAGE_LEDGERS:
        raise ValueError(
            "ledger must be KORAIL_MILEAGE_LEDGER_KTX or "
            "KORAIL_MILEAGE_LEDGER_RAIL_POINT"
        )
    if request.movement not in _KORAIL_MILEAGE_MOVEMENTS:
        raise ValueError(
            "movement must be one of KORAIL_MILEAGE_MOVEMENT_ALL, "
            "KORAIL_MILEAGE_MOVEMENT_EARNED, KORAIL_MILEAGE_MOVEMENT_SPENT"
        )
    start_date = _ascii_digits(request.start_date, "start_date", lengths=frozenset({8}))
    end_date = _ascii_digits(request.end_date, "end_date", lengths=frozenset({8}))
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    return {
        "pontTpVal": request.ledger,
        "qryDvVal": request.movement,
        "qryStDt": start_date,
        "qryClsDt": end_date,
        # MileageHistoryActivity.java:274 -- a literal, every call.
        "pgPrCnt": "20",
        "nowPgNo": _positive_int(request.page_no, "page_no"),
    }


def build_discount_card_usage_query(card_no: str) -> dict[str, str]:
    """``ticket.dcntCrdUseQry.do`` — ``ResearchService.java:51-52``."""
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


@dataclass(frozen=True)
class DiscountCardScheduleRequest:
    """할인카드 운행일정 조회 입력 (``ResearchService.java:54-55``).

    1구간 N카드: ``u4/b.java:52-65``, v2 카드: ``u4/b.java:67-81``.
    기본값은 두 빌더 공통 상수. ``dptTm`` ``"000000"``, ``trnGpCd`` ``"109"``
    (``K4/s.java:5``), ``dirtChtnDvCd`` ``"1"`` (``K4/d.java:5``).

    2026-09-21 실서버 확인: ``usable_trip_count`` 의 기본값 ``""`` 는 서버가
    거부합니다(``WRR000100: 입력값 오류(usePsbTno)``) — 이 필드는 사실상
    필수입니다. 다만 어떤 값이 "맞는" 기본값인지는 여전히 확인되지 않아
    임의로 채우지 않습니다 — 호출자가 실제 값(예: ``"01"``)을 넘겨야
    합니다.
    """

    card_kind_management_no: str
    departure_station_name: str
    arrival_station_name: str
    departure_date: str
    card_kind_code: str = "MMM"
    usable_trip_count: str = ""
    usage_period_days: str | None = None
    page_no: str | None = None
    departure_time: str = "000000"
    train_group_code: str = "109"
    direct_transfer_division_code: str = "1"

    @classmethod
    def for_card(
        cls,
        card_kind_management_no: str,
        *,
        departure_station_name: str,
        arrival_station_name: str,
        departure_date: str,
        usable_trip_count: str = "",
        usage_period_days: str | None = None,
        page_no: str | None = None,
    ) -> DiscountCardScheduleRequest:
        """카드 종류에서 ``dcntCrdKndCd`` 를 ``u4/b.java`` 방식으로 유도해 요청을 만듭니다."""
        kind_code = (
            "B2N"
            if card_kind_management_no in _B2N_CARD_KIND_MANAGEMENT_NOS
            else "MMM"
        )
        return cls(
            card_kind_management_no=card_kind_management_no,
            departure_station_name=departure_station_name,
            arrival_station_name=arrival_station_name,
            departure_date=departure_date,
            card_kind_code=kind_code,
            usable_trip_count=usable_trip_count,
            usage_period_days=usage_period_days,
            page_no=page_no,
        )


#: ``"B2N"`` 을 쓰는 두 상품 (``u4/b.java:61``, ``NCard1SectionBookingActivity.java:28``).
_B2N_CARD_KIND_MANAGEMENT_NOS = frozenset({"B2N18120402", "B2N18120403"})


def build_discount_card_schedule_query(
    request: DiscountCardScheduleRequest,
) -> dict[str, str]:
    """``useTrmDno``/``qryPgNo`` 는 ``None`` 이면 생략 — Retrofit null @Query
    (``ResearchService.java:54-55``; 생략 가능한 필드 목록은
    삭제된 테스트 픽스처의 ``KORAIL_OPTIONAL_REQUEST_FIELDS`` 가 이를 기록했었다).
    """
    if type(request) is not DiscountCardScheduleRequest:
        raise TypeError("request must be an exact DiscountCardScheduleRequest")
    query = {
        "dptDt": _ascii_digits(request.departure_date, "departure_date", lengths=frozenset({8})),
        "dptRsStnNm": _required_text(
            request.departure_station_name,
            "departure_station_name",
        ),
        "arvRsStnNm": _required_text(
            request.arrival_station_name,
            "arrival_station_name",
        ),
        "dptTm": _ascii_digits(request.departure_time, "departure_time", lengths=frozenset({6})),
        "trnGpCd": _required_text(
            request.train_group_code,
            "train_group_code",
        ),
        "dirtChtnDvCd": _required_text(
            request.direct_transfer_division_code,
            "direct_transfer_division_code",
        ),
        "dcntCrdKndCd": _required_text(
            request.card_kind_code,
            "card_kind_code",
        ),
        "dcntCrdKndMgNo": _required_text(
            request.card_kind_management_no,
            "card_kind_management_no",
        ),
        "usePsbTno": _optional_text(
            request.usable_trip_count,
            "usable_trip_count",
        ),
    }
    if request.usage_period_days is not None:
        query["useTrmDno"] = _required_text(
            request.usage_period_days,
            "usage_period_days",
        )
    if request.page_no is not None:
        query["qryPgNo"] = _required_text(request.page_no, "page_no")
    return query


def build_customer_trip_info_form(customer_no: str) -> dict[str, str]:
    return {
        "custMgNo": _required_text(customer_no, "customer_no"),
        "medDvCd": "03",
        "regSqno": "0",
    }


def build_maas_service_detail_form(
    config: KorailConfig,
    query: MaasServiceDetailQuery,
) -> dict[str, str]:
    if not isinstance(query, MaasServiceDetailQuery):
        raise TypeError("query must be an exact MaasServiceDetailQuery")
    _validate_maas_service_detail_query_values(
        query.start_date,
        query.end_date,
    )
    form = _device_version(config)
    # The validator above already rejected one date without the other, so
    # testing both is equivalent to testing only ``start_date``.
    if query.start_date is not None and query.end_date is not None:
        form["qryDtFrom"] = query.start_date
        form["qryDtTo"] = query.end_date
    return form


def build_trip_change_date_form(departure_date: str) -> dict[str, str]:
    return {"tripChgDate": _ascii_digits(departure_date, "departure_date", lengths=frozenset({8}))}


def _exact_server_pass_data(pass_data: PassMenuData) -> str:
    if not isinstance(pass_data, PassMenuData):
        raise TypeError("pass_data must be a PassMenuData")
    return _required_text(
        pass_data.commuter_kind_code,
        "pass_data.commuter_kind_code",
    )


@dataclass(frozen=True)
class CommuterInitialRequest:
    pass_data: PassMenuData = field(repr=False)


@dataclass(frozen=True, init=False)
class CommuterPassengerRequest:
    pass_data: PassMenuData = field(repr=False)
    source: CommuterInfoResponse = field(repr=False)
    passenger_counts: tuple[int, ...] = field(repr=False)

    @classmethod
    def from_response(
        cls,
        pass_data: PassMenuData,
        source: CommuterInfoResponse,
        passenger_counts: tuple[int, ...],
    ) -> CommuterPassengerRequest:
        instance = object.__new__(cls)
        object.__setattr__(instance, "pass_data", pass_data)
        object.__setattr__(instance, "source", source)
        object.__setattr__(instance, "passenger_counts", passenger_counts)
        _validate_commuter_passenger_request(instance)
        return instance


def _validate_commuter_passenger_request(
    request: CommuterPassengerRequest,
) -> tuple[str, ...]:
    _exact_server_pass_data(request.pass_data)
    if not isinstance(request.source, CommuterInfoResponse):
        raise TypeError("source must be a CommuterInfoResponse")
    if type(request.passenger_counts) is not tuple:
        raise TypeError("passenger_counts must be a tuple")
    age_codes = tuple(
        option.commuter_usage_age_code
        for option in request.source.passenger_options
    )
    if not age_codes or len(age_codes) != len(request.passenger_counts):
        raise ValueError(
            "passenger counts must match the response age-code rows"
        )
    validated_age_codes: list[str] = []
    for option, age_code in zip(
        request.source.passenger_options,
        age_codes,
        strict=True,
    ):
        if not isinstance(option, CommuterPassengerOption):
            raise TypeError("response passenger options must be CommuterPassengerOption")
        validated_age_codes.append(
            _required_text(age_code, "commuter_usage_age_code")
        )
    for count in request.passenger_counts:
        if type(count) is not int or count < 0:
            raise ValueError(
                "passenger counts must be non-negative integers"
            )
    return tuple(validated_age_codes)


@dataclass(frozen=True)
class OriginalTicketReference:
    """원표(발권 승차권) 한 장을 가리키는 네 값.

    :attr:`sale_date` 의 자릿수가 **엔드포인트마다 다릅니다.** 같은 객체를
    아무 데나 넘길 수 없다는 뜻이라, 여기 적어 둡니다 — 2026-09-22 에 실제
    승차권 128장을 전 엔드포인트에 통과시켜 확인한 결과입니다.

    4자리 ``MMDD``(:attr:`~korail_mobile_api.read_models.TicketListTicket.return_sale_date`)
        :meth:`~korail_mobile_api.client.KorailClient.get_refund_commission`,
        :meth:`~korail_mobile_api.client.KorailClient.get_refund_ticket_detail`,
        :meth:`~korail_mobile_api.client.KorailClient.get_original_ticket_inquiry`,
        그리고 :class:`StationRefundVerificationRequest` 의 ``return_no_2``.
        8자리를 주면 각각 ``ERZ800027``/``WRT200408``/``WRT100124`` 입니다.

    8자리 ``YYYYMMDD``(:attr:`~korail_mobile_api.read_models.TicketListTicket.sale_date`)
        :meth:`~korail_mobile_api.client.KorailClient.get_delivery_recipient`
        (``saleDt``)와
        :meth:`~korail_mobile_api.client.KorailClient.get_pbp_acceptance_specifications`
        (``tkRetNo`` 안). 4자리를 주면 ``ERB000001``
        ("INPUT 값 검증 도중 오류")입니다.

    두 이름이 비슷해서 실제로 한 번 물렸습니다 — 환불이
    :attr:`~korail_mobile_api.read_models.TicketListTicket.sale_date` 8자리
    때문에 ``ERZ800027`` 로 막혔고, 4자리
    :attr:`~korail_mobile_api.read_models.TicketListTicket.return_sale_date`
    로 바꾸고서야 통과했습니다. 승차권 목록에서 옮겨 담을 때 어느 쪽인지
    먼저 확인하십시오.
    """

    sale_window_no: str = field(repr=False)
    sale_date: str = field(repr=False)
    sale_sequence: str = field(repr=False)
    return_password: str = field(repr=False)

    def __post_init__(self) -> None:
        _validate_original_ticket_reference(self)


def _validate_original_ticket_reference(
    reference: OriginalTicketReference,
) -> None:
    for value, name in (
        (reference.sale_window_no, "sale_window_no"),
        (reference.sale_date, "sale_date"),
        (reference.sale_sequence, "sale_sequence"),
        (reference.return_password, "return_password"),
    ):
        _required_text(value, name)


def _exact_original_ticket_reference(
    reference: OriginalTicketReference,
) -> OriginalTicketReference:
    if not isinstance(reference, OriginalTicketReference):
        raise TypeError(
            "ticket must be an OriginalTicketReference"
        )
    _validate_original_ticket_reference(reference)
    return reference


def _ticket_return_number(reference: OriginalTicketReference) -> str:
    ticket = _exact_original_ticket_reference(reference)
    return "-".join(
        (
            ticket.sale_window_no,
            ticket.sale_date,
            ticket.sale_sequence,
            ticket.return_password,
        )
    )


def _exact_ticket_reference_tuple(
    tickets: tuple[OriginalTicketReference, ...],
) -> tuple[OriginalTicketReference, ...]:
    if type(tickets) is not tuple:
        raise TypeError("tickets must be an exact tuple")
    if not tickets:
        raise ValueError("tickets must contain at least one reference")
    for ticket in tickets:
        _exact_original_ticket_reference(ticket)
    return tickets


@dataclass(frozen=True)
class TicketDuplicationCheckRequest:
    pnr_no: str = field(repr=False)

    def __post_init__(self) -> None:
        _validate_ticket_duplication_check_request(self)


def _validate_ticket_duplication_check_request(
    request: TicketDuplicationCheckRequest,
) -> None:
    _required_text(request.pnr_no, "pnr_no")


def build_delivery_recipient_form(
    ticket: OriginalTicketReference,
) -> dict[str, str]:
    reference = _exact_original_ticket_reference(ticket)
    return {
        "saleWctNo": reference.sale_window_no,
        "saleDt": reference.sale_date,
        "saleSqno": reference.sale_sequence,
        "tkRetPwd": reference.return_password,
    }


def build_ticket_duplication_check_form(
    request: TicketDuplicationCheckRequest,
) -> dict[str, str]:
    if not isinstance(request, TicketDuplicationCheckRequest):
        raise TypeError(
            "request must be a TicketDuplicationCheckRequest"
        )
    _validate_ticket_duplication_check_request(request)
    return {"pnrNo": request.pnr_no}


def build_pbp_acceptance_specification_form(
    tickets: tuple[OriginalTicketReference, ...],
) -> tuple[tuple[str, str | int], ...]:
    references = _exact_ticket_reference_tuple(tickets)
    return (
        ("tkCnt", len(references)),
        *(("tkRetNo", _ticket_return_number(ticket)) for ticket in references),
    )


def build_original_ticket_inquiry_form(
    tickets: tuple[OriginalTicketReference, ...],
    *,
    ticket_count: int | None = None,
) -> tuple[tuple[str, str | int], ...]:
    """원표 조회 순서 폼 (``ResearchService.java:61-63``).

    인덱스 키 순서는 ``ROrtg.java:8-11`` 선언 순서. ``ticket_count`` 는
    호출 지점마다 다른 값을 보냄 — 승객수/행수/리터럴 1
    (``TCBookingActivity.java:179``, ``PushHistoryActivity.java:357``,
    ``SeatSearchActivity.java:615``). ``int`` 전송은
    ``ResearchService.smali:613,628-632`` 확인.
    """
    references = _exact_ticket_reference_tuple(tickets)
    if ticket_count is None:
        count = len(references)
    elif type(ticket_count) is not int or ticket_count < 1:
        raise ValueError("ticket_count must be a positive integer")
    else:
        count = ticket_count
    rows: list[tuple[str, str | int]] = [("tkCnt", count)]
    for index, ticket in enumerate(references, start=1):
        rows.append((f"ogtkSaleWctNo_{index}", ticket.sale_window_no))
        rows.append((f"ogtkSaleDd_{index}", ticket.sale_date))
        rows.append((f"ogtkSaleSqno_{index}", ticket.sale_sequence))
        rows.append((f"ogtkRetPwd_{index}", ticket.return_password))
    return tuple(rows)


#: ``"1"`` 일반실, ``"2"`` 특실, ``None`` 은 필드 생략.
KorailSelfSeatChangeRoomClassCode = Literal["1", "2"]


@dataclass(frozen=True)
class SelfSeatChangeInfoRequest:
    """자율 좌석/열차 변경 대상 (``TicketService.java:54-56``).

    모든 값은 승차권의 ``h_run_dt``/``h_trn_no``/``h_dpt_rs_stn_cd``/
    ``h_arv_rs_stn_cd`` 에서 복사 (``TCSOptionsActivity.java:131-134``).
    ``trnNo`` 는 0 채움 없음. :attr:`room_class_code` 는 일반실/특실일 때만
    전송 (``TCSOptionsActivity.java:135-138``, ``K4/o.java:7-8``).
    """

    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    room_class_code: KorailSelfSeatChangeRoomClassCode | None = field(
        default=None, repr=False
    )

    def __post_init__(self) -> None:
        _validate_self_seat_change_info_request(self)


#: ``K4/o.java:7-8`` GENERAL("1") / SPECIAL("2"). ALL("9") 는 제외.
SELF_SEAT_CHANGE_ROOM_CLASS_CODES = frozenset({"1", "2"})


def _validate_self_seat_change_info_request(
    request: SelfSeatChangeInfoRequest,
) -> None:
    _ascii_digits(request.run_date, "run_date", lengths=frozenset({8}))
    _ascii_digits(request.train_no, "train_no", maximum_length=5)
    _required_text(
        request.departure_station_code,
        "departure_station_code",
    )
    _required_text(request.arrival_station_code, "arrival_station_code")
    if request.room_class_code is None:
        return
    if request.room_class_code not in SELF_SEAT_CHANGE_ROOM_CLASS_CODES:
        raise ValueError(
            "room_class_code must be '1', '2' or None"
        )


def build_self_seat_change_info_form(
    request: SelfSeatChangeInfoRequest,
) -> dict[str, str]:
    if not isinstance(request, SelfSeatChangeInfoRequest):
        raise TypeError(
            "request must be a SelfSeatChangeInfoRequest"
        )
    _validate_self_seat_change_info_request(request)
    form = {
        "runDt": request.run_date,
        "trnNo": request.train_no,
        "dptRsStnCd": request.departure_station_code,
        "arvRsStnCd": request.arrival_station_code,
    }
    if request.room_class_code is not None:
        form["psrmClCd"] = request.room_class_code
    return form


def build_recent_delivery_history_form(customer_no: str) -> dict[str, str]:
    return {"custMgNo": _required_text(customer_no, "customer_no")}


@dataclass(frozen=True)
class CommuterTicketInquiryRequest:
    original_ticket: OriginalTicketReference = field(repr=False)
    inquiry_type: str = field(default="0", repr=False)

    def __post_init__(self) -> None:
        if self.inquiry_type not in {"0", "1"}:
            raise ValueError("inquiry_type must be '0' or '1'")
        if not isinstance(self.original_ticket, OriginalTicketReference):
            raise TypeError(
                "original_ticket must be an OriginalTicketReference"
            )
        _validate_original_ticket_reference(self.original_ticket)


CommuterInfoRequest = (
    CommuterInitialRequest
    | CommuterPassengerRequest
    | CommuterTicketInquiryRequest
)


def build_commuter_info_form(
    request: CommuterInfoRequest,
) -> tuple[tuple[str, str], ...]:
    if type(request) is CommuterInitialRequest:
        kind_code = _exact_server_pass_data(request.pass_data)
        return (
            ("jobDvCd", "a"),
            ("cmtrKndCd", kind_code),
            ("psgCnt", "0"),
        )
    if type(request) is CommuterPassengerRequest:
        kind_code = _exact_server_pass_data(request.pass_data)
        age_codes = _validate_commuter_passenger_request(request)
        # One ``cmtrUtlAgeCd`` per **passenger**, not per age-code row, and
        # ``psgCnt`` is their total -- so ``passenger_counts`` decides both.
        # It used to be ignored here: the form always carried every row once
        # with ``psgCnt`` = row count, which cannot express any valid
        # composition for a multi-row pass. Live 2026-09-22 on kind ``0046``
        # (rows ``E05``/``E06``): the old row-shaped form is rejected
        # ``WRT800115 유효하지 않은 인원구성입니다``, while ``psgCnt=1``+``E05``,
        # ``psgCnt=1``+``E06`` and ``psgCnt=2``+``E05``,``E05`` all answer
        # ``IRZ000008``. Matches ``CommutationInfoIn.java:31,38``
        # (``cmtrUtlAgeCd: List<String>`` alongside a scalar ``psgCnt: int``).
        selected = tuple(
            code
            for code, count in zip(
                age_codes,
                request.passenger_counts,
                strict=True,
            )
            for _ in range(count)
        )
        if not selected:
            raise ValueError(
                "passenger_counts must select at least one passenger"
            )
        return (
            ("jobDvCd", "b"),
            ("cmtrKndCd", kind_code),
            ("psgCnt", str(len(selected))),
            *(("cmtrUtlAgeCd", value) for value in selected),
        )
    if type(request) is CommuterTicketInquiryRequest:
        if not isinstance(request.original_ticket, OriginalTicketReference):
            raise TypeError(
                "original_ticket must be an OriginalTicketReference"
            )
        _validate_original_ticket_reference(request.original_ticket)
        if request.inquiry_type not in {"0", "1"}:
            raise ValueError("inquiry_type must be '0' or '1'")
        ticket = request.original_ticket
        return (
            ("jobDvCd", "c"),
            ("psgCnt", "0"),
            ("ogtkSaleWctNo", ticket.sale_window_no),
            ("ogtkSaleDd", ticket.sale_date),
            ("ogtkSaleSqno", ticket.sale_sequence),
            ("ogtkRetPwd", ticket.return_password),
            ("inquiryType", request.inquiry_type),
        )
    raise TypeError("request must be an exact commuter request variant")


def _wire_component(value: str, name: str) -> str:
    resolved = _required_text(value, name)
    if "," in resolved:
        raise ValueError(f"{name} must not contain a comma")
    return resolved


@dataclass(frozen=True)
class PriceFareLeg:
    """운임 계산 구간 하나 (``PrcFareInItem.java``).

    ``goods_no`` (``gdNo``) 는 **선택입니다.** 일반 열차의 운임 조회에서 앱은
    이 값을 보내지 않습니다 — ``TrainOpInfoViewModel.java:794`` 의 세 생성자
    호출이 모두 7번째 인자에 리터럴 ``(String) null`` 과 기본값 마스크 ``64``
    를 넘기고, DTO 쪽도 ``PrcFareInItem.java:85`` 에서
    ``this.gdNo = (i & 64) == 0 ? <기본값> : str7`` 로 옵셔널 선언입니다.
    ``None`` 이면 ``gdNo`` 열 자체를 폼에서 뺍니다(앱과 같은 모양).
    실서버는 값을 넣든 빼든 같은 응답을 돌려줍니다(2026-09-21 확인).
    """

    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    requested_seat_attribute_code: str = field(repr=False)
    train_group_code: str = field(repr=False)
    standing_train_classification_code: str = field(repr=False)
    goods_no: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        _validate_price_fare_leg(self)


def _validate_price_fare_leg(leg: PriceFareLeg) -> None:
    for value, name in (
        (leg.departure_station_code, "departure_station_code"),
        (leg.arrival_station_code, "arrival_station_code"),
        (leg.run_date, "run_date"),
        (leg.train_no, "train_no"),
        (leg.requested_seat_attribute_code, "requested_seat_attribute_code"),
        (leg.train_group_code, "train_group_code"),
        (
            leg.standing_train_classification_code,
            "standing_train_classification_code",
        ),
    ):
        _wire_component(value, name)
    if leg.goods_no is not None:
        _wire_component(leg.goods_no, "goods_no")


@dataclass(frozen=True)
class PriceFareQuoteRequest:
    """운임 계산 요청 — 한두 구간 + ``txtMenuId``.

    ``txtMenuId`` 는 앱 상수 ``"11"`` (``a5/k.java:92-94`` →
    ``PriceFareActivity.java:49,62``).
    """

    legs: tuple[PriceFareLeg, ...] = field(repr=False)
    menu_id: str = field(default="11", repr=False)

    def __post_init__(self) -> None:
        _validate_price_fare_quote_request(self)


def _validate_price_fare_quote_request(
    request: PriceFareQuoteRequest,
) -> None:
    _wire_component(request.menu_id, "menu_id")
    if type(request.legs) is not tuple or len(request.legs) not in {1, 2}:
        raise ValueError("legs must be a tuple containing one or two legs")
    for leg in request.legs:
        if not isinstance(leg, PriceFareLeg):
            raise TypeError("legs must contain PriceFareLeg values")
        _validate_price_fare_leg(leg)


def build_price_fare_quote_form(
    request: PriceFareQuoteRequest,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(request, PriceFareQuoteRequest):
        raise TypeError("request must be a PriceFareQuoteRequest")
    _validate_price_fare_quote_request(request)
    columns = [
        ("dptRsStnCd", "departure_station_code"),
        ("arvRsStnCd", "arrival_station_code"),
        ("runDt", "run_date"),
        ("trnNo", "train_no"),
        ("rqSeatAttCd", "requested_seat_attribute_code"),
        ("trnGpCd", "train_group_code"),
        ("stlbTrnClsfCd", "standing_train_classification_code"),
    ]
    # gdNo is sent only when the caller actually has a goods number. The app's
    # ordinary fare check omits it (TrainOpInfoViewModel.java:794 passes a
    # literal null plus the default mask). A mix of set and unset across legs
    # has no observed wire shape -- the columns are comma-joined positionally,
    # so there is nothing to put in an absent leg's slot -- and this library
    # does not invent one.
    supplied = [leg.goods_no is not None for leg in request.legs]
    if any(supplied):
        if not all(supplied):
            raise ValueError(
                "goods_no must be set on every leg or on none of them"
            )
        columns.insert(4, ("gdNo", "goods_no"))
    return (
        ("txtMenuId", request.menu_id),
        ("chtnDvCd", str(len(request.legs))),
        ("trnCnt", str(len(request.legs))),
        *(
            (
                wire_name,
                # Validated above; through _wire_component again so the join
                # sees str rather than getattr's Any.
                ",".join(
                    _wire_component(getattr(leg, attribute), attribute)
                    for leg in request.legs
                ),
            )
            for wire_name, attribute in columns
        ),
    )


@dataclass(frozen=True)
class TicketReservationDetailRequest:
    """미결제 예약 PNR (``CertificationService.java:45-46``)."""

    pnr_no: str = field(repr=False)

    def __post_init__(self) -> None:
        _validate_ticket_reservation_detail_request(self)


def _validate_ticket_reservation_detail_request(
    request: TicketReservationDetailRequest,
) -> None:
    _required_text(request.pnr_no, "pnr_no")


def build_ticket_reservation_detail_query(
    request: TicketReservationDetailRequest,
) -> dict[str, str]:
    """``hidPnrNo`` 하나 — ``CertificationService.java:45-46``."""
    if not isinstance(request, TicketReservationDetailRequest):
        raise TypeError(
            "request must be a TicketReservationDetailRequest"
        )
    _validate_ticket_reservation_detail_request(request)
    return {"hidPnrNo": request.pnr_no}


@dataclass(frozen=True)
class RefundCompanion:
    """동반자 신원 (``TicketListActivity.java:908-909``, ``ui/ticket/ticketReturn/a.java:355-356``).

    없으면 빈 문자열 전송 — 생략 불가.
    """

    name: str = field(default="", repr=False)
    certificate_no: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        _validate_refund_companion(self)


def _validate_refund_companion(companion: RefundCompanion) -> None:
    _optional_text(companion.name, "name")
    _optional_text(companion.certificate_no, "certificate_no")


def _exact_refund_companion(companion: RefundCompanion) -> RefundCompanion:
    if not isinstance(companion, RefundCompanion):
        raise TypeError("companion must be a RefundCompanion")
    _validate_refund_companion(companion)
    return companion


def build_station_refund_verification_form(
    request: StationRefundVerificationRequest,
) -> dict[str, str]:
    """``NetworkApi.verifyOnlineRefunds`` 의 입력(``VerifyOnlineRefundsIn``).

    7.0.6 계약이 조회로 등록한 라우트라 여기 있습니다. 공통 필드는 7.0.6
    게이트웨이가 붙입니다. 값은 요청 객체가 이미 검사했습니다.
    """
    return {
        "strName": request.customer_name,
        "retNo1": request.return_no_1,
        "retNo2": request.return_no_2,
        "retNo3": request.return_no_3,
        "retNo4": request.return_no_4,
    }


def build_refund_commission_form(
    ticket: OriginalTicketReference,
    companion: RefundCompanion = RefundCompanion(),
) -> dict[str, str]:
    """환불 수수료 사전조회 폼 (``RefundService.java:19-21``).

    판매일자 필드는 ``h_orgtk_ret_sale_dt`` — 영수증 조회의 ``h_orgtk_sale_dt``
    와 다름.
    """
    reference = _exact_original_ticket_reference(ticket)
    party = _exact_refund_companion(companion)
    return {
        "h_orgtk_ret_sale_dt": reference.sale_date,
        "h_orgtk_wct_no": reference.sale_window_no,
        "h_orgtk_sale_sqno": reference.sale_sequence,
        "h_orgtk_ret_pwd": reference.return_password,
        "h_comp_nm": party.name,
        "h_comp_cert_no": party.certificate_no,
    }


def build_refund_ticket_detail_form(
    ticket: OriginalTicketReference,
    *,
    from_purchase_history: bool = False,
    txt_index: str | None = None,
) -> dict[str, str]:
    """환불 대상 승차권 상세 (``RefundService.java:23-25``).

    ``h_purchase_history``: "Y" 구매이력(``TicketPurchaseHistoryActivity.java:267``),
    "N" 승차권 목록(``TicketListActivity.java:926``).
    """
    reference = _exact_original_ticket_reference(ticket)
    if type(from_purchase_history) is not bool:
        raise TypeError("from_purchase_history must be a bool")
    form = {
        "h_orgtk_ret_sale_dt": reference.sale_date,
        "h_orgtk_wct_no": reference.sale_window_no,
        "h_orgtk_sale_sqno": reference.sale_sequence,
        "h_orgtk_ret_pwd": reference.return_password,
        "h_purchase_history": "Y" if from_purchase_history else "N",
    }
    if txt_index is not None:
        form["txtIndex"] = _required_text(txt_index, "txt_index")
    return form
