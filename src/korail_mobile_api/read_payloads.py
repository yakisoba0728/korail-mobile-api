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
from .errors import KorailProtocolError
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
        raise KorailProtocolError(f"{name} must be a positive integer")
    return str(value)


def _required_text(value: str | None, name: str) -> str:
    """``value`` 를 그대로 돌려주되 없거나 빈 문자열이면 거부합니다.

    호출자 대부분이 서버 응답에서 파싱한 선택 필드를 그대로 넘기므로, ``None``
    도 인자로 받아 :class:`~korail_mobile_api.errors.KorailProtocolError` 로
    거절합니다.
    """
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(f"{name} must not be empty")
    return value


def _optional_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise KorailProtocolError(f"{name} must be a string")
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
                raise KorailProtocolError(
                    f"{name} must contain exactly {length} ASCII digits"
                )
            expected = ", ".join(str(length) for length in sorted(lengths))
            raise KorailProtocolError(f"{name} must contain {expected} ASCII digit(s)")
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
        raise KorailProtocolError(f"{name} must be an ASCII decimal string{suffix}")
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
        raise KorailProtocolError(f"{name} must be a positive ASCII decimal string")
    return resolved


def _passenger_count(value: int, name: str) -> int:
    if type(value) is not int or not 1 <= value <= 9:
        raise KorailProtocolError(f"{name} must be an integer from 1 through 9")
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
    """``guideSeatCnd.do`` 입력 — 사실상 **정적 안내문** 조회입니다.

    서버는 :attr:`seat_attribute_code` 가 무엇이든 같은 도우미석 안내를
    ``FAIL``/``MRR800011`` 로 돌려줍니다(2026-09-22: 좌석속성코드 14종 전부
    동일). 7.0.6 도 ``SeatType.HELPER`` 의 코드 하나만 보냅니다
    (``TrainOptionViewModel.java:270``). 즉 이 값으로 결과가 갈리지 않습니다.
    """

    seat_attribute_code: str = field(repr=False)

    def __post_init__(self) -> None:
        _required_text(self.seat_attribute_code, "seat_attribute_code")


@dataclass(frozen=True)
class SeatAssignmentScheduleRequest:
    #: ``menuId`` — 좌석배정·할인 메뉴 코드입니다. 일반 검색 메뉴 ``"11"`` 은
    #: 빈 목록만 돌려주므로(2026-09-22 확인) 행을 받으려면 ``"A1"``/``"A2"``
    #: (:data:`~korail_mobile_api.constants.KORAIL_DISCOUNT_CARD_MENU_ID`)를
    #: 씁니다. 자세한 것은
    #: :meth:`~korail_mobile_api.client.KorailClient.get_seat_assignment_schedule`
    #: docstring 참조.
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
            raise KorailProtocolError("transfer_type_code must be '1' or '2'")
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
        raise KorailProtocolError("request must be a FreeSeatCarRequest")
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
        raise KorailProtocolError("request must be a GuideSeatConditionRequest")
    return {"rqSeatAttCd": request.seat_attribute_code}


def build_seat_assignment_schedule_form(
    request: SeatAssignmentScheduleRequest,
) -> dict[str, str]:
    if not isinstance(request, SeatAssignmentScheduleRequest):
        raise KorailProtocolError("request must be a SeatAssignmentScheduleRequest")
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
        raise KorailProtocolError("request must be a MergeSeatsInquiryRequest")
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
    #: ``txtSelPage`` — **이 라우트는 무시합니다.** 어떤 값을 넣어도 응답의
    #: ``h_page_no`` 는 ``'1'`` 로 돌아왔고(2026-09-22 실측), 7.0.6 도
    #: ``CheckUsagePeriodSectionViewModel.java:389`` 에서 ``'1'`` 을 박아
    #: 보냅니다. 더 받으려면 이 값이 아니라 :attr:`page_size` 를 키우십시오.
    #: 응답 쪽 페이징 신호도 믿을 수 없습니다 —
    #: :class:`~korail_mobile_api.read_models.PassScheduleMainInfo` 참조.
    page_no: str = field(repr=False)
    #: ``txtSelCnt`` — 실제로 결과 수를 정하는 값입니다.
    page_size: str = field(repr=False)
    departure_station_name: str = field(repr=False)
    arrival_station_name: str = field(repr=False)
    weekend_use_flag: str = field(repr=False)

    def __post_init__(self) -> None:
        _required_text(self.selected_train_code, "selected_train_code")
        _ascii_digits(self.departure_date, "departure_date", lengths=frozenset({8}))
        _ascii_digits(self.departure_time, "departure_time", lengths=frozenset({6}))
        _required_text(self.transfer_type_code, "transfer_type_code")
        _required_text(self.pass_kind_code, "pass_kind_code")
        _required_text(self.pass_period_code, "pass_period_code")
        _required_text(self.pass_age_code, "pass_age_code")
        _positive_ascii_text(self.page_no, "page_no")
        _positive_ascii_text(
            self.page_size,
            "page_size",
            allow_empty=True,
        )
        _required_text(
            self.departure_station_name,
            "departure_station_name",
        )
        _required_text(self.arrival_station_name, "arrival_station_name")
        if self.weekend_use_flag not in {"Y", "N"}:
            raise KorailProtocolError("weekend_use_flag must be 'Y' or 'N'")


def build_pass_schedule_form(
    request: PassScheduleRequest,
) -> dict[str, str]:
    if not isinstance(request, PassScheduleRequest):
        raise KorailProtocolError("request must be a PassScheduleRequest")
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
    ``qryDvCd`` 가 이 라우트에 존재하지 않는 필드라 제거했습니다. 호출부
    :meth:`~korail_mobile_api.client.KorailClient.get_crew_request_list` 는
    이제 ``timestamp_ms`` 만 넘깁니다.
    """
    return build_cache_query(timestamp_ms)


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
            raise KorailProtocolError("txt_index must be a string or None")
        if txt_index.strip():
            form["txtIndex"] = txt_index
    return form


def _calendar_date(value: str, name: str) -> date:
    _ascii_digits(value, name, lengths=frozenset({8}))
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError as exc:
        raise KorailProtocolError(f"{name} must be a valid calendar date") from exc


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
            raise KorailProtocolError("MaaS history requires both dates or neither")
        return
    start = _calendar_date(start_date, "start_date")
    end = _calendar_date(end_date, "end_date")
    if end < start:
        raise KorailProtocolError("end_date must not be before start_date")
    if end > _add_calendar_months(start, 3):
        raise KorailProtocolError(
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
    # 위 :func:`build_trip_change_date_form` 과 같은 이유로 달력 검증입니다.
    return {
        "dptDt": _calendar_date(departure_date, "departure_date").strftime("%Y%m%d")
    }


def build_korail_point_summary_form() -> dict[str, str]:
    """``xPoint.MyXPointView`` 의 고정 폼 (``NetworkApi.java:515``).

    ``point_dv_cd`` 가 ``"0"`` 으로 고정인 근거였던 ``KorailPointInquiryDao``
    는 6.5.0 클래스라 7.0.6 디컴파일에 없습니다(2026-09-22 확인). 값 자체는
    라이브로 동작하지만 고정 이유의 출처는 지금 없습니다 — **미출처**로
    두고, 7.0.6 호출 지점을 찾으면 그때 채우십시오.
    """
    return {"point_dv_cd": "0"}


#: ``"1"`` KTX 마일리지, ``"2"`` 철도포인트.
KorailMileageLedger = Literal["1", "2"]

#: ``"0"`` 전체, ``"1"`` 적립, ``"2"`` 사용.
KorailMileageMovement = Literal["0", "1", "2"]

#: 원래 근거였던 ``MileageHistoryActivity`` 는 6.5.0 클래스로 7.0.6
#: 디컴파일에 없습니다(2026-09-22 확인). 두 값 모두 라이브로는 동작하지만
#: 출처가 없으므로 **미출처** 상수로 둡니다.
KORAIL_MILEAGE_LEDGER_KTX: KorailMileageLedger = "1"
KORAIL_MILEAGE_LEDGER_RAIL_POINT: KorailMileageLedger = "2"

#: 위와 같은 이유로 **미출처**입니다(``MileageHistoryActivity`` 부재).
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
    """마일리지 내역 조회 입력 (``mlg.amtSpec.do``, ``NetworkApi.java:274``).

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
        raise KorailProtocolError("request must be a MileageHistoryRequest")
    if request.ledger not in _KORAIL_MILEAGE_LEDGERS:
        raise KorailProtocolError(
            "ledger must be KORAIL_MILEAGE_LEDGER_KTX or "
            "KORAIL_MILEAGE_LEDGER_RAIL_POINT"
        )
    if request.movement not in _KORAIL_MILEAGE_MOVEMENTS:
        raise KorailProtocolError(
            "movement must be one of KORAIL_MILEAGE_MOVEMENT_ALL, "
            "KORAIL_MILEAGE_MOVEMENT_EARNED, KORAIL_MILEAGE_MOVEMENT_SPENT"
        )
    start_date = _ascii_digits(request.start_date, "start_date", lengths=frozenset({8}))
    end_date = _ascii_digits(request.end_date, "end_date", lengths=frozenset({8}))
    if start_date > end_date:
        raise KorailProtocolError("start_date must not be after end_date")
    return {
        "pontTpVal": request.ledger,
        "qryDvVal": request.movement,
        "qryStDt": start_date,
        "qryClsDt": end_date,
        # 매 호출 같은 리터럴입니다. 근거였던 MileageHistoryActivity 는
        # 6.5.0 클래스라 7.0.6 에 없어(2026-09-22 확인) 지금은 미출처입니다.
        "pgPrCnt": "20",
        "nowPgNo": _positive_int(request.page_no, "page_no"),
    }


def build_discount_card_usage_query(card_no: str) -> dict[str, str]:
    """``ticket.dcntCrdUseQry.do`` — ``NetworkApi.java:218``."""
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


@dataclass(frozen=True)
class DiscountCardScheduleRequest:
    """할인카드 운행일정 조회 입력 (``NetworkApi.java:340``).

    7.0.6 의 입력 DTO 는 ``NCardScheduleIn.java:25``(필드 ``:30-40``)이고,
    앱이 이것을 조립하는 유일한 지점은
    ``CheckUsageNCardSectionViewModel.java:390-396`` 입니다. 원래 인용
    ``u4/b.java:52-65``(1구간 N카드) / ``:67-81``(v2 카드)는 7.0.6 디컴파일에
    없는 경로였고, **1구간/v2 라는 두 빌더로 갈라진다는 설명 자체도 7.0.6
    에서는 확인되지 않습니다** — 조립 지점은 위 한 곳뿐입니다.

    기본값 셋(``dptTm`` ``"000000"``, ``trnGpCd`` ``"109"``,
    ``dirtChtnDvCd`` ``"1"``)의 **값은 7.0.6 소스로 확인할 수 없습니다.**
    원래 인용 ``K4/s.java:5``/``K4/d.java:5`` 는 없는 경로이고, 7.0.6 의 해당
    자리는 전부 AlienGuard 로 보호돼 있습니다: ``dptTm`` 은
    ``CheckUsageNCardSectionViewModel.java:390`` 의 6바이트 보호 리터럴,
    ``dirtChtnDvCd`` 는 ``:396`` 의 1바이트 보호 리터럴, ``trnGpCd`` 는
    ``TrainGroup.KTX``(``TrainGroup.java:36``)의 ``trnGpCd``
    (``:48``)인데 열거 상수의 문자열 인수도 보호됩니다. 길이만 맞고 값은
    라이브 관측에서 온 것이므로, 이 셋은 "구조 확인 + 값 미출처" 입니다.

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
        """카드 종류에서 ``dcntCrdKndCd`` 를 유도해 요청을 만듭니다.

        원래 이 한 줄은 "``u4/b.java`` 방식으로" 라고 적었는데 그 경로는 7.0.6
        디컴파일에 없습니다. 7.0.6 의 대응물은
        ``NCardDefine.findDcntCrdKndCd``(``NCardDefine.java:58-88``)이고,
        아래 :data:`_B2N_CARD_KIND_MANAGEMENT_NOS` 주석에 적은 대로 **그 함수가
        특별 취급하는 관리번호 집합이 이 구현과 다릅니다.** 여기서는 코드를
        바꾸지 않고 사실만 남깁니다.
        """
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


#: ``"B2N"`` 을 쓰는 두 상품. 원래 인용 ``u4/b.java:61`` 과
#: ``NCard1SectionBookingActivity.java:28`` 은 둘 다 7.0.6 디컴파일에 없는
#: 경로였습니다.
#:
#: **7.0.6 재조사 결과가 이 집합과 어긋납니다(코드는 건드리지 않았습니다).**
#: 7.0.6 의 분기는 ``NCardDefine.findDcntCrdKndCd``
#: (``NCardDefine.java:58-88``)이고, jadx 가 이 함수의 case 본문을 잃어버렸으므로
#: (``:56`` 의 "Code decompiled incorrectly") smali 로 읽었습니다 —
#: ``smali_classes5/com/korail/talk/common/define/NCardDefine.smali:689``,
#: 분기표 ``:1219-1225``. sparse-switch 키 네 개는
#: ``0x447cfa13``/``0x447cfa14``/``0x447d5bad``/``0x447d5bae``
#: = ``1149041171``/``1149041172``/``1149066157``/``1149066158`` 이고, 이는
#: ``NCardDefine.java:14-17`` 의 상수
#: ``B2N19060502``/``B2N19060503``/``B2N19061002``/``B2N19061003`` 의 자바
#: ``String.hashCode()`` 와 정확히 일치합니다. 매칭되면
#: ``NCardDefine.smali:1180-1193`` 의 3바이트 보호 리터럴을, 아니면
#: 같은 smali ``:1196-1215`` 의 다른 3바이트 보호 리터럴을
#: 돌려줍니다(둘 다 3자 코드이므로 ``"B2N"``/``"MMM"`` 과 길이는 맞습니다).
#: — 이 두 줄번호는 **smali** 쪽입니다. 직전 문장이 ``NCardDefine.java:14-17``
#: 을 인용하므로 생략형으로 적으면 89행짜리 java 파일을 가리키는 것으로
#: 읽혀 따라갈 수 없습니다.
#:
#: 아래 두 값 ``B2N18120402``/``B2N18120403`` 은 해시가
#: ``286471596``/``286471597`` 로, 그 네 case 에 **없습니다** —
#: ``NCardDefine.java:12-13`` 에 상수로는 존재하지만 이 함수가 특별 취급하지는
#: 않습니다. 즉 7.0.6 기준으로는 이 집합이 뒤바뀐 것으로 보입니다. 어느 쪽이
#: 실서버에서 맞는지는 할인카드 보유 계정으로만 확인할 수 있어(이 라우트는
#: 카드 미보유 시 ``EAZ000028`` 로 먼저 끊김) 라이브 대조 전까지 값을 바꾸지
#: 않았습니다. 바꾸려면 코드 변경이므로 별도 판단이 필요합니다.
_B2N_CARD_KIND_MANAGEMENT_NOS = frozenset({"B2N18120402", "B2N18120403"})


def build_discount_card_schedule_query(
    request: DiscountCardScheduleRequest,
) -> dict[str, str]:
    """``useTrmDno``/``qryPgNo`` 는 ``None`` 이면 이 딕셔너리에서 생략합니다.

    **정정(2026-09-22)**: 원래 이 자리에 "Retrofit 은 널 ``@Query`` 를 빼기
    때문입니다" 라고 적혀 있었는데 이 라우트에 ``@Query`` 는 없습니다 —
    ``NetworkApi.java:339-341`` 은 ``@FormUrlEncoded`` +
    ``postDcntCrdScheduleView(@FieldMap Map<String, String>)`` 입니다. 앱은
    ``NCardScheduleIn`` 을 공유 ``KJson`` 으로 직렬화한 뒤
    ``Map<String, String>`` 으로 펴서 넘깁니다
    (``NetworkService.java:2387-2393``). 따라서 생략은 Retrofit 의 널
    처리가 아니라 **이 빌더가 키를 넣지 않는 것** 이 유일한 메커니즘입니다.

    앱은 그 둘을 **항상 키로는 채워 보냅니다** —
    ``CheckUsageNCardSectionViewModel.java:396`` 의
    ``new NCardScheduleIn(...)`` 가 인자 11개를 모두 넘기고, ``KJson`` 이
    ``encodeDefaults`` 로 직렬화하므로 키가 빠지지 않습니다.
    다만 원래 주석의 "모두 **비어 있지 않게** 넘긴다"는 보장이 아닙니다:
    기간·횟수는 ``StringExKt.convertOnlyInt``(``StringExKt.java:121-135``)를
    거치는데 그 함수는 ``Regex(<보호된 패턴>).replace(str, "")`` 일 뿐이어서
    숫자가 없는 입력에는 ``""`` 를 돌려줍니다. 즉 "키 생략" 경로는 앱에 없고,
    "빈 문자열" 경로는 앱에도 있습니다.

    그래도 기본값을 바꾸지 않은 이유는 **확인할 수 없기 때문**입니다.
    ``NCardScheduleIn`` 의 ``@SerialName`` 은 공통 셋(``Device``/``Version``/
    ``Key``)말고는 AlienGuard 로 싸여 있어 두 키의 전선 철자를 정적으로 읽을
    수 없고, 이 라우트는 할인카드 보유를 먼저 검사해(``EAZ000028``) 카드 없는
    계정으로는 생략 여부의 차이를 라이브로 볼 수 없습니다. 같은 종류의
    추측이 리무진 ``ymsAplFlgYMS`` 에서 이미 한 번 필드를 죽였습니다 —
    속성명을 전선 키로 베껐다가 값이 늘 ``None`` 이었습니다. 카드를 가진
    계정이 생기면 그때 확인하고 바꾸십시오.
    """
    if type(request) is not DiscountCardScheduleRequest:
        raise KorailProtocolError("request must be an exact DiscountCardScheduleRequest")
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
        raise KorailProtocolError("query must be a MaasServiceDetailQuery")
    form = _device_version(config)
    # __post_init__ already rejected one date without the other, so testing
    # both is equivalent to testing only ``start_date``.
    if query.start_date is not None and query.end_date is not None:
        form["qryDtFrom"] = query.start_date
        form["qryDtTo"] = query.end_date
    return form


def build_trip_change_date_form(departure_date: str) -> dict[str, str]:
    # 자릿수만 보던 예전 검증은 ``20260230`` 같은 달력에 없는 날짜를 그대로
    # 보냈고, 서버는 그것을 빈 목록으로 조용히 돌려줬습니다 -- 호출자는
    # "변경 가능한 날짜가 없다" 와 "날짜를 잘못 썼다" 를 구분할 수 없었습니다.
    # ``_calendar_date`` 는 이 모듈이 이미 쓰는 검증기입니다.
    return {
        "tripChgDate": _calendar_date(
            departure_date, "departure_date"
        ).strftime("%Y%m%d")
    }


def _exact_server_pass_data(pass_data: PassMenuData) -> str:
    if not isinstance(pass_data, PassMenuData):
        raise KorailProtocolError("pass_data must be a PassMenuData")
    return _required_text(
        pass_data.commuter_kind_code,
        "pass_data.commuter_kind_code",
    )


@dataclass(frozen=True)
class CommuterInitialRequest:
    pass_data: PassMenuData = field(repr=False)

    def __post_init__(self) -> None:
        _exact_server_pass_data(self.pass_data)


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
        raise KorailProtocolError("source must be a CommuterInfoResponse")
    if type(request.passenger_counts) is not tuple:
        raise KorailProtocolError("passenger_counts must be a tuple")
    age_codes = tuple(
        option.commuter_usage_age_code
        for option in request.source.passenger_options
    )
    if not age_codes or len(age_codes) != len(request.passenger_counts):
        raise KorailProtocolError(
            "passenger counts must match the response age-code rows"
        )
    validated_age_codes: list[str] = []
    for option, age_code in zip(
        request.source.passenger_options,
        age_codes,
        strict=True,
    ):
        if not isinstance(option, CommuterPassengerOption):
            raise KorailProtocolError("response passenger options must be CommuterPassengerOption")
        validated_age_codes.append(
            _required_text(age_code, "commuter_usage_age_code")
        )
    for count in request.passenger_counts:
        if type(count) is not int or count < 0:
            raise KorailProtocolError(
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

        8자리를 줬을 때 오는 코드는 엔드포인트마다 다릅니다 — 예전에
        여기 적혀 있던 "각각" 순서는 틀렸습니다(2026-09-22 재확인):
        ``get_refund_commission`` → ``WRT200408``,
        ``get_refund_ticket_detail`` → ``ERZ800027``,
        ``get_original_ticket_inquiry`` → ``ERZ800027``,
        ``return_no_2`` → ``WRT100124``. 마지막 것은 자릿수 전용이 아니라
        반환번호가 형식에 안 맞을 때 두루 오는 코드라 6자리에도 옵니다.

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
        for value, name in (
            (self.sale_window_no, "sale_window_no"),
            (self.sale_date, "sale_date"),
            (self.sale_sequence, "sale_sequence"),
            (self.return_password, "return_password"),
        ):
            _required_text(value, name)


def _exact_original_ticket_reference(
    reference: OriginalTicketReference,
) -> OriginalTicketReference:
    if not isinstance(reference, OriginalTicketReference):
        raise KorailProtocolError(
            "ticket must be an OriginalTicketReference"
        )
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
        raise KorailProtocolError("tickets must be an exact tuple")
    if not tickets:
        raise KorailProtocolError("tickets must contain at least one reference")
    for ticket in tickets:
        _exact_original_ticket_reference(ticket)
    return tickets


@dataclass(frozen=True)
class TicketDuplicationCheckRequest:
    pnr_no: str = field(repr=False)

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


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
        raise KorailProtocolError(
            "request must be a TicketDuplicationCheckRequest"
        )
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
    """원표 조회 순서 폼 (``research.tripChgOgtk.do``, ``NetworkApi.java:235``).

    7.0.6 의 입력 DTO 는 ``OgTicketInquiryIn.java:28-30``
    (``List<ChangeOrtkInfo> ortkList`` + ``int tkCnt``)입니다.

    인덱스 키 순서는 ``ChangeOrtkInfo.java:52`` 의 ``@SerialName`` 선언 순서
    ``ogtkSaleWctNo_`` → ``ogtkSaleDd_`` → ``ogtkSaleSqno_`` →
    ``ogtkRetPwd_`` 그대로입니다 — 이름이 밑줄로 끝나는 것이 인덱스 접미사가
    붙는 자리라는 증거이고, 아래 ``rows.append`` 네 줄과 순서가 같습니다.
    (원래 인용 ``ROrtg.java:8-11`` 은 7.0.6 디컴파일에 없는 경로였습니다.)

    ``ticket_count`` 는 ``OgTicketInquiryIn.java:81`` 의
    ``@SerialName("tkCnt")`` 이고 같은 파일 ``:30`` 의 DTO 선언이
    ``int`` 입니다(생략형 ``:81``/``:30`` 으로 적으면 직전에 인용한
    ``ChangeOrtkInfo.java`` 를 가리키는 것으로 읽힙니다) — 원래 근거였던
    ``ResearchService.smali:613,628-632`` 도 없는 경로였으나 결론은 그대로
    유효합니다.

    호출 지점마다 값이 다르다는 관찰은 7.0.6 에서 **부분만** 맞습니다. 이
    DTO 의 생성 지점은 넷이고, 셋은 목록 **행 수** 를 넣습니다 —
    ``NotificationViewModel.java:197``, ``PassengerTypeChangeViewModel.java:147``,
    ``TrainSeatMapViewModel.java:1282`` 이 모두 ``arrayList.size()`` 입니다.
    넷째 ``RefundTicketViewModel.java:258`` 은 보호된 리터럴(``> 0`` 비교로
    1)을 한 행짜리 목록과 함께 넣습니다. 즉 "행수"와 "리터럴 1"은 확인되지만
    원래 주석이 말한 **"승객수"를 보내는 지점은 7.0.6 에 없습니다** — 그
    셋째 경우는 미출처입니다. 원래 인용 ``TCBookingActivity.java:179`` /
    ``PushHistoryActivity.java:357`` / ``SeatSearchActivity.java:615`` 는 모두
    7.0.6 에 없는 경로였습니다.
    """
    references = _exact_ticket_reference_tuple(tickets)
    if ticket_count is None:
        count = len(references)
    elif type(ticket_count) is not int or ticket_count < 1:
        raise KorailProtocolError("ticket_count must be a positive integer")
    else:
        count = ticket_count
    # ``count`` 가 ``references`` 보다 작으면 서버는 앞의 ``count`` 개
    # ``ogtkSaleWctNo_N`` 묶음만 읽고 나머지는 **조용히 무시**합니다
    # (2026-09-22 확인). 앱이 호출 지점마다 다른 값을 보내므로 여기서
    # 같기를 강제하지는 않지만, 전부 조회하려면 ``ticket_count`` 를 주지
    # 말거나 ``len(tickets)`` 와 같게 주십시오.
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
    """자율 좌석/열차 변경 대상 (``SeatAvailabilityIn.java:25``, 필드 ``:26-30``).

    라우트는 ``NetworkApi.java:806-808``(``.../self.seatChgInfo.do``)이고, 입력
    DTO 는 ``String`` 다섯(``runDt``/``trnNo``/``dptRsStnCd``/``arvRsStnCd``/
    ``psrmClCd``)뿐입니다. ``@SerialName`` 은 공통 넷(``Device``/``Version``/
    ``Key``/``LANG``)에만 붙어 있어(``:55``) 나머지 다섯은 프로퍼티 이름이 곧
    와이어 키입니다 — 아래 폼 빌더가 쓰는 철자와 같습니다. 원래 인용
    ``TicketService.java:54-56`` 은 7.0.6 디컴파일에 없는 경로였습니다.

    모든 값은 승차권의 ``h_run_dt``/``h_trn_no``/``h_dpt_rs_stn_cd``/
    ``h_arv_rs_stn_cd`` 에서 복사합니다 —
    ``SelfSeatChangeOptionViewModel.java:344`` 가
    ``new SeatAvailabilityIn(ticketListTrainInfo.getHRunDt(), getHTrnNo(),
    getHDptRsStnCd(), getHArvRsStnCd(), psrmClCd)`` 로 그대로 넘깁니다(원래
    인용 ``TCSOptionsActivity.java:131-134`` 는 없는 경로였습니다).
    ``trnNo`` 는 0 채움 없음.

    **:attr:`room_class_code` 에 대한 정정(2026-09-22).** 원래 주석은
    "일반실/특실일 때만 전송(``TCSOptionsActivity.java:135-138``,
    ``K4/o.java:7-8``)" 이라고 했는데 두 경로 모두 7.0.6 에 없고, 7.0.6 의
    동작도 그와 다릅니다: ``SelfSeatChangeOptionViewModel.java:342-343`` 은
    ``selfSeatChangeTicket.getPsrmClCd()`` 를 그대로 쓰고 그것이 ``null`` 이
    아닐 때 요청을 만듭니다 — 값을 두 코드로 걸러 내는 분기가 없습니다.
    실제로 ``PsrmType`` 은 ``ticketselfseat`` 패키지에서 한 번도 참조되지
    않습니다. 여기서 ``None`` 일 때 키를 빼는 것은 이 라이브러리의 선택이며
    앱 동작의 재현이 아닙니다.
    """

    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    room_class_code: KorailSelfSeatChangeRoomClassCode | None = field(
        default=None, repr=False
    )

    def __post_init__(self) -> None:
        _ascii_digits(self.run_date, "run_date", lengths=frozenset({8}))
        _ascii_digits(self.train_no, "train_no", maximum_length=5)
        _required_text(
            self.departure_station_code,
            "departure_station_code",
        )
        _required_text(self.arrival_station_code, "arrival_station_code")
        if (
            self.room_class_code is not None
            and self.room_class_code not in SELF_SEAT_CHANGE_ROOM_CLASS_CODES
        ):
            raise KorailProtocolError(
                "room_class_code must be '1', '2' or None"
            )


#: 7.0.6 의 ``PsrmType``(``PsrmType.java:16``)은 상수가 딱 둘입니다 —
#: ``GENERAL``(``:19``)과 ``SPECIAL``(``:20``) — 이며 각 상수의 ``psrmClCd``
#: 문자열(``:22``, 생성자 ``:37``)은 AlienGuard 로 보호되어 정적으로 읽을 수
#: 없습니다. 따라서 아래 ``"1"``/``"2"`` 는 라이브 관측값이고 7.0.6 소스로
#: 확인된 것이 아닙니다.
#:
#: 원래 주석은 ``K4/o.java:7-8`` 을 인용하며 ``ALL("9") 는 제외`` 라고
#: 적었는데, ① 그 경로는 7.0.6 에 없고 ② 7.0.6 의 ``PsrmType`` 에는 애초에
#: ``ALL`` 상수가 없습니다(``PsrmType.java:24-29`` 의 ``$values()`` 가
#: ``:26``/``:27`` 에서 둘만 채웁니다 — 생략형으로 적으면 직전에 인용한
#: 없는 경로 ``K4/o.java`` 를 가리키는 것으로 읽힙니다).
#: 즉 "제외"할 세 번째 값이 존재하지 않습니다 — 그 주장은 미출처입니다.
SELF_SEAT_CHANGE_ROOM_CLASS_CODES = frozenset({"1", "2"})


def build_self_seat_change_info_form(
    request: SelfSeatChangeInfoRequest,
) -> dict[str, str]:
    if not isinstance(request, SelfSeatChangeInfoRequest):
        raise KorailProtocolError(
            "request must be a SelfSeatChangeInfoRequest"
        )
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
            raise KorailProtocolError("inquiry_type must be '0' or '1'")
        if not isinstance(self.original_ticket, OriginalTicketReference):
            raise KorailProtocolError(
                "original_ticket must be an OriginalTicketReference"
            )


CommuterInfoRequest = (
    CommuterInitialRequest
    | CommuterPassengerRequest
    | CommuterTicketInquiryRequest
)


def build_commuter_info_form(
    request: CommuterInfoRequest,
) -> tuple[tuple[str, str], ...]:
    if type(request) is CommuterInitialRequest:
        return (
            ("jobDvCd", "a"),
            ("cmtrKndCd", request.pass_data.commuter_kind_code),
            ("psgCnt", "0"),
        )
    if type(request) is CommuterPassengerRequest:
        age_codes = tuple(
            option.commuter_usage_age_code
            for option in request.source.passenger_options
        )
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
            raise KorailProtocolError(
                "passenger_counts must select at least one passenger"
            )
        return (
            ("jobDvCd", "b"),
            ("cmtrKndCd", request.pass_data.commuter_kind_code),
            ("psgCnt", str(len(selected))),
            *(("cmtrUtlAgeCd", value) for value in selected),
        )
    if type(request) is CommuterTicketInquiryRequest:
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
    raise KorailProtocolError("request must be an exact commuter request variant")


def _wire_component(value: str, name: str) -> str:
    resolved = _required_text(value, name)
    if "," in resolved:
        raise KorailProtocolError(f"{name} must not contain a comma")
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
    #: ``stlbTrnClsfCd`` — 열차 종류 코드입니다. 예전 이름
    #: ``standing_train_classification_code`` 는 ``stlb`` 를 입석(standing)
    #: 으로 읽은 오해였습니다 — 같은 전선 키를 이 저장소의 다른 세 곳이
    #: 전부 열차 종류로 읽습니다(``limousine_parsers.py:95``
    #: ``train_class_code``, ``parsers.py:834`` ``standard_train_class_code``,
    #: ``read_parsers.py:1853`` ``settlement_train_class_code``).
    #: 열차 행의 ``train_class_code`` 를 그대로 옮기면 됩니다.
    train_class_code: str = field(repr=False)
    goods_no: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.departure_station_code, "departure_station_code"),
            (self.arrival_station_code, "arrival_station_code"),
            (self.run_date, "run_date"),
            (self.train_no, "train_no"),
            (self.requested_seat_attribute_code, "requested_seat_attribute_code"),
            (self.train_group_code, "train_group_code"),
            (self.train_class_code, "train_class_code"),
        ):
            _wire_component(value, name)
        if self.goods_no is not None:
            _wire_component(self.goods_no, "goods_no")


@dataclass(frozen=True)
class PriceFareQuoteRequest:
    """운임 계산 요청 — 한두 구간 + ``txtMenuId``.

    7.0.6 의 입력 DTO 는 ``PrcFareIn.java:27``(필드 ``:28-31``:
    ``txtMenuId``/``chtnDvCd``/``trnCnt`` + ``List<PrcFareInItem> paramList``)
    이고, 앱의 유일한 조립 지점은 ``TrainOpInfoViewModel.java:794`` 입니다 —
    ``new PrcFareIn(txtMenuId, chtnDvCd, trnCnt, paramList)``
    (인자 순서는 ``PrcFareIn.java:197`` 의 ``copy`` 로 확인).

    ``txtMenuId`` 가 앱 상수라는 것은 맞습니다 —
    ``TrainOpInfoViewModel.java:794`` 의 ``new PrcFareIn(…)`` 두 곳 모두
    첫 인자가 ``method_name_3(…, new byte[]{47, 109}, false)``, 즉
    **2바이트** AlienGuard 리터럴입니다. (파일명을 다시 적는 이유: 직전
    문장이 ``PrcFareIn.java:197`` 을 인용하므로 생략형 ``:794`` 는 274행짜리
    그 DTO 파일을 가리키는 것으로 읽혀 존재하지 않는 줄이 됩니다.) 다만 **값 ``"11"`` 자체는 7.0.6
    소스로 확인되지 않습니다**(길이만 일치). 원래 인용 ``a5/k.java:92-94`` 와
    ``PriceFareActivity.java:49,62`` 는 둘 다 7.0.6 디컴파일에 없는
    경로였습니다.
    """

    legs: tuple[PriceFareLeg, ...] = field(repr=False)
    menu_id: str = field(default="11", repr=False)

    def __post_init__(self) -> None:
        _wire_component(self.menu_id, "menu_id")
        if type(self.legs) is not tuple or len(self.legs) not in {1, 2}:
            raise KorailProtocolError("legs must be a tuple containing one or two legs")
        for leg in self.legs:
            if not isinstance(leg, PriceFareLeg):
                raise KorailProtocolError("legs must contain PriceFareLeg values")


def build_price_fare_quote_form(
    request: PriceFareQuoteRequest,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(request, PriceFareQuoteRequest):
        raise KorailProtocolError("request must be a PriceFareQuoteRequest")
    columns = [
        ("dptRsStnCd", "departure_station_code"),
        ("arvRsStnCd", "arrival_station_code"),
        ("runDt", "run_date"),
        ("trnNo", "train_no"),
        ("rqSeatAttCd", "requested_seat_attribute_code"),
        ("trnGpCd", "train_group_code"),
        ("stlbTrnClsfCd", "train_class_code"),
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
            raise KorailProtocolError(
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
                ",".join(getattr(leg, attribute) for leg in request.legs),
            )
            for wire_name, attribute in columns
        ),
    )


@dataclass(frozen=True)
class TicketReservationDetailRequest:
    """미결제 예약 PNR (``ReservationListIn.java:30`` 의 ``hidPnrNo``).

    라우트는 ``certification.ReservationList`` 로, 7.0.6 에는 같은 경로가 두
    번 선언됩니다(``NetworkApi.java:422-424`` ``postInquiryTicketRsv`` 와
    ``:626-628`` ``postReservationList``) — 둘 다 ``@FormUrlEncoded`` +
    ``@FieldMap`` 이고 응답은 ``ReservationOut`` 입니다. 입력 DTO
    ``ReservationListIn.java:29`` 는 ``hidPnrNo``(``:30``) 외에
    ``txtPsgDisc0019Cnt``(``:32``)와 ``psgDisc0019List``(``:31``)도
    선언하는데, 이 라이브러리는 PNR 하나만 보냅니다. ``@SerialName`` 은 공통
    넷에만 있어(``:58``) ``hidPnrNo`` 는 프로퍼티 이름이 곧 와이어 키입니다.
    원래 인용 ``CertificationService.java:45-46`` 은 7.0.6 디컴파일에 없는
    경로였습니다.
    """

    pnr_no: str = field(repr=False)

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


def build_ticket_reservation_detail_query(
    request: TicketReservationDetailRequest,
) -> dict[str, str]:
    """``hidPnrNo`` 하나 — ``ReservationListIn.java:30``.

    (원래 인용 ``CertificationService.java:45-46`` 은 7.0.6 에 없는 경로입니다.
    클래스 독스트링 참고.)
    """
    if not isinstance(request, TicketReservationDetailRequest):
        raise KorailProtocolError(
            "request must be a TicketReservationDetailRequest"
        )
    return {"hidPnrNo": request.pnr_no}


@dataclass(frozen=True)
class RefundCompanion:
    """동반자 신원 (``RefundCommissionIn.java:34-35``).

    와이어 키는 ``@SerialName("h_comp_nm")``/``@SerialName("h_comp_cert_no")``
    (``RefundCommissionIn.java:59``)입니다. 원래 인용
    ``TicketListActivity.java:908-909`` 과
    ``ui/ticket/ticketReturn/a.java:355-356`` 은 둘 다 7.0.6 디컴파일에 없는
    경로였습니다.

    없으면 빈 문자열 전송 — 생략 불가. 7.0.6 에서도 그렇습니다:
    ``MyTicketDetailViewModel.java:277`` 과
    ``FTicketDetailViewModel.java:179`` 가 ``ticketDetailOut.getCompaNm()`` 과
    ``getCompaBrth()`` 를 **조건 없이** 5·6번째 인자로 넘기고, 두 필드는
    승차권 상세 DTO 에서 기본값 ``""`` 을 가집니다. 6번째 자리가
    ``h_comp_cert_no`` 인데 앱이 거기 넣는 값은 동반자 **생년월일**
    (``compaBrth``)이라는 점도 함께 확인됩니다.
    """

    name: str = field(default="", repr=False)
    certificate_no: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        _optional_text(self.name, "name")
        _optional_text(self.certificate_no, "certificate_no")


def _exact_refund_companion(companion: RefundCompanion) -> RefundCompanion:
    if not isinstance(companion, RefundCompanion):
        raise KorailProtocolError("companion must be a RefundCompanion")
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
    """환불 수수료 사전조회 폼 (``refunds.CommissionView``).

    라우트는 ``NetworkApi.java:598-600``, 입력 DTO 는
    ``RefundCommissionIn.java:27``(필드 ``:32-42``)입니다. 아래 여섯 키는
    ``:59`` 의 ``@SerialName`` 집합에서 그대로 읽었고 순서도 같습니다.
    원래 인용 ``RefundService.java:19-21`` 은 7.0.6 디컴파일에 없는
    경로였습니다.

    판매일자 필드는 ``h_orgtk_ret_sale_dt`` — 영수증 조회의 ``h_orgtk_sale_dt``
    와 다름. 7.0.6 도 같습니다: ``RefundCommissionIn.java:37`` 이
    ``hOrgtkRetSaleDt`` 를, 형제 ``RefundTicketIn.java:38`` 이
    ``hOrgtkSaleDt`` 를 선언합니다 — 서로 다른 두 파일이므로 생략형
    ``:37``/``:38`` 로 적으면 바로 위에서 인용한(그리고 7.0.6 에 없는)
    ``RefundService.java`` 를 가리키는 것으로 읽힙니다.
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
    """환불 대상 승차권 상세 (``refunds.SelTicketInfo``).

    라우트는 ``NetworkApi.java:406-408``
    (``postGetTicketDetail(@FieldMap …) → TicketDetailOut``), 입력 DTO 는
    ``TicketDetailIn.java:26``(필드 ``:31-36``)입니다. 아래 여섯 키는 모두
    ``TicketDetailIn.java:57`` 의 ``@SerialName`` 집합입니다 —
    ``h_orgtk_ret_sale_dt``/``h_orgtk_wct_no``/``h_orgtk_sale_sqno``/
    ``h_orgtk_ret_pwd``/``h_purchase_history``/``txtIndex``. 원래 인용
    ``RefundService.java:23-25`` 는 7.0.6 디컴파일에 없는 경로였습니다.

    ``h_purchase_history`` 가 구매이력/승차권목록 두 값으로 갈린다는 관찰은
    ``MyTicketBaseViewModel.java:696`` 에서 구조로 확인됩니다 —
    ``new TicketDetailIn(…, z ? <1바이트 리터럴> : <1바이트 리터럴>, txtIndex)``
    로 불리언 하나에 1바이트 코드 두 개가 걸려 있습니다. **다만 그 두 값이
    ``"Y"``/``"N"`` 이라는 것은 7.0.6 소스로 확인되지 않습니다** — 리터럴이
    AlienGuard 로 보호되어 길이(1자)만 맞습니다. 값 자체는 라이브 관측에서
    왔습니다. 원래 근거였던 ``TicketPurchaseHistoryActivity.java:267`` 과
    ``TicketListActivity.java:926`` 은 둘 다 7.0.6 에 없는 경로였습니다.
    """
    reference = _exact_original_ticket_reference(ticket)
    if type(from_purchase_history) is not bool:
        raise KorailProtocolError("from_purchase_history must be a bool")
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
