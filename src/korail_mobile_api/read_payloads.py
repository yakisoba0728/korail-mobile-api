from __future__ import annotations

import time
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date

from .config import KorailConfig
from .read_models import (
    CommuterInfoResponse,
    CommuterPassengerOption,
    PassGoodsInfo,
    PassMenuItem,
    PassMenuData,
    PassPassengerInfos,
    ProductTrainInquiryResponse,
)


def _positive_int(value: int, name: str) -> str:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return str(value)


def _required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _ascii_date(value: str, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 8
        or any(ch < "0" or ch > "9" for ch in value)
    ):
        raise ValueError(f"{name} must use ASCII YYYYMMDD")
    return value


def _optional_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value


def _ascii_digits(value: str, name: str, length: int) -> str:
    if (
        not isinstance(value, str)
        or len(value) != length
        or any(character < "0" or character > "9" for character in value)
    ):
        raise ValueError(
            f"{name} must contain exactly {length} ASCII digits"
        )
    return value


def _ascii_identifier(
    value: str,
    name: str,
    *,
    maximum_length: int | None = None,
) -> str:
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
    if (
        not isinstance(value, str)
        or not value
        or any(character < "0" or character > "9" for character in value)
        or not any(character != "0" for character in value)
    ):
        raise ValueError(
            f"{name} must be a positive ASCII decimal string"
        )
    return value


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
        _ascii_digits(self.run_date, "run_date", 8)
        _ascii_identifier(
            self.train_no,
            "train_no",
            maximum_length=5,
        )
        _ascii_identifier(
            self.departure_construction_order,
            "departure_construction_order",
        )
        _ascii_identifier(
            self.arrival_construction_order,
            "arrival_construction_order",
        )
        _ascii_identifier(
            self.departure_run_order,
            "departure_run_order",
        )
        _ascii_identifier(
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
        _ascii_digits(self.departure_date, "departure_date", 8)
        _ascii_digits(self.departure_time, "departure_time", 6)
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
    selected_station_name: str = field(repr=False)
    room_class_code: str = field(repr=False)
    seat_attribute_code: str = field(repr=False)
    passenger_count: int = field(repr=False)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        _ascii_digits(self.boarding_datetime, "boarding_datetime", 14)
        _ascii_digits(self.run_datetime, "run_datetime", 14)
        _ascii_identifier(
            self.train_no,
            "train_no",
            maximum_length=5,
        )
        _required_text(
            self.departure_station_name,
            "departure_station_name",
        )
        _required_text(self.arrival_station_name, "arrival_station_name")
        _required_text(self.selected_station_name, "selected_station_name")
        _required_text(self.room_class_code, "room_class_code")
        _required_text(self.seat_attribute_code, "seat_attribute_code")
        _passenger_count(self.passenger_count, "passenger_count")


def build_free_seat_car_form(
    request: FreeSeatCarRequest,
) -> dict[str, str]:
    if type(request) is not FreeSeatCarRequest:
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
    if type(request) is not GuideSeatConditionRequest:
        raise TypeError("request must be a GuideSeatConditionRequest")
    GuideSeatConditionRequest._validate(request)
    return {"rqSeatAttCd": request.seat_attribute_code}


def build_seat_assignment_schedule_form(
    request: SeatAssignmentScheduleRequest,
) -> dict[str, str]:
    if type(request) is not SeatAssignmentScheduleRequest:
        raise TypeError("request must be a SeatAssignmentScheduleRequest")
    SeatAssignmentScheduleRequest._validate(request)
    return {
        "menuId": request.menu_id,
        "dptDt": request.departure_date,
        "dptTm": request.departure_time,
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
        "trnGpCd": request.train_group_code,
        "psrmClCd": request.room_class_code,
        "seatAttCd1": request.seat_attribute_code,
        "psgNum1": str(request.passenger_count),
        "stlbDturDvNm1": request.standing_detour_division_name,
        "dirtChtnDvCd": request.transfer_type_code,
        "chtnArvRsStnNm": request.connection_arrival_station_name,
    }


def build_merge_seats_inquiry_form(
    request: MergeSeatsInquiryRequest,
) -> dict[str, str]:
    if type(request) is not MergeSeatsInquiryRequest:
        raise TypeError("request must be a MergeSeatsInquiryRequest")
    MergeSeatsInquiryRequest._validate(request)
    return {
        "abrdDt": request.boarding_datetime,
        "runDt": request.run_datetime,
        "trnNo": request.train_no.zfill(5),
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
        "selRsStnNm": request.selected_station_name,
        "psrmClCd": request.room_class_code,
        "seatAttCd": request.seat_attribute_code,
        "totPsgNum": str(request.passenger_count),
    }


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
    _ascii_digits(request.departure_date, "departure_date", 8)
    _ascii_digits(request.departure_time, "departure_time", 6)
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
    if type(request) is not PassScheduleRequest:
        raise TypeError("request must be exactly a PassScheduleRequest")
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
    if timestamp_ms is not None and (
        type(timestamp_ms) is not int or timestamp_ms < 0
    ):
        raise ValueError(
            "timestamp_ms must be a non-negative integer or None"
        )
    resolved = (
        int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    )
    return {"timeStamp": str(resolved)}


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
    return {"dptDtTo": _ascii_date(departure_date_to, "departure_date_to")}


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
        "Device": config.device,
        "Version": config.version,
    }


def build_pass_menu_form(menu_no: str) -> dict[str, str]:
    return {"menuNo": _required_text(menu_no, "menu_no")}


def build_crew_request_list_query(
    query_division_code: str,
) -> dict[str, str]:
    return {
        "qryDvCd": _required_text(
            query_division_code,
            "query_division_code",
        )
    }


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
) -> dict[str, str]:
    return {
        "txtSelPage": _positive_int(page_no, "page_no"),
        "txtCntPerPage": _positive_int(page_size, "page_size"),
    }


def build_product_detail_query(
    reservation_no: str,
    reservation_sequence: str,
) -> dict[str, str]:
    return {
        "txtVrRsNo": _required_text(reservation_no, "reservation_no"),
        "txtVrRsvSqNo": _required_text(
            reservation_sequence,
            "reservation_sequence",
        ),
    }


def build_ticket_receipt_form(
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
) -> dict[str, str]:
    return {
        "h_orgtk_sale_dt": _ascii_date(sale_date, "sale_date"),
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


def _calendar_date(value: str, name: str) -> date:
    _ascii_date(value, name)
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
    if (start_date is None) != (end_date is None):
        raise ValueError("MaaS history requires both dates or neither")
    if start_date is None:
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
    def current(cls) -> "MaasServiceDetailQuery":
        return cls()

    @classmethod
    def history(
        cls,
        start_date: str,
        end_date: str,
    ) -> "MaasServiceDetailQuery":
        return cls(start_date=start_date, end_date=end_date)


def build_multi_child_discount_target_form(
    departure_date: str,
) -> dict[str, str]:
    return {"dptDt": _ascii_date(departure_date, "departure_date")}


def build_korail_point_summary_form() -> dict[str, str]:
    """``xPoint.MyXPointView`` — one constant, not a caller parameter.

    ``KorailPointInquiryDao.java:87-92`` has no request class at all: it builds
    a bare ``BaseRequest`` and passes the literal ``"0"`` as ``point_dv_cd``.
    Both call sites (``MyPageActivity.java:414``,
    ``MemberCardActivity.java:67``) instantiate the DAO with no arguments, so
    ``"0"`` is the only value the app can send and this builder takes nothing.
    """
    return {"point_dv_cd": "0"}


#: ``pontTpVal`` — which ledger ``mlg.amtSpec.do`` reads.
#: ``MileageHistoryActivity.java:289,543`` sets ``"1"`` for the KTX 마일리지 tab
#: (the screen's default) and ``:313`` sets ``"2"`` for the 철도포인트 tab.
KORAIL_MILEAGE_LEDGER_KTX = "1"
KORAIL_MILEAGE_LEDGER_RAIL_POINT = "2"

#: ``qryDvVal`` — the 전체/적립/사용 selector, sent as the dropdown INDEX rather
#: than as a code: ``MileageHistoryActivity.java:566`` assigns
#: ``Integer.toString(i9)`` straight from ``onItemSelected``, and ``:502``
#: declares the three entries in this order. ``"0"`` is the field's initial
#: value (``:134``).
KORAIL_MILEAGE_MOVEMENT_ALL = "0"
KORAIL_MILEAGE_MOVEMENT_EARNED = "1"
KORAIL_MILEAGE_MOVEMENT_SPENT = "2"

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
    """The 마일리지 내역 read's inputs (``XPointService.java:26-28``).

    The defaults are the screen's own: the KTX ledger
    (``MileageHistoryActivity.java:543``), 전체 movements (``:134``), and
    ``pgPrCnt="20"`` — a hardcoded literal at ``:274``, not a preference, which
    is why it is not a constructor argument. ``nowPgNo`` is 1-based (``:131``)
    and the app increments it while ``page_no <= pgCnt`` (``:158,252-253``).

    :attr:`start_date` and :attr:`end_date` have no default because the app has
    none either: ``onCreate`` calls ``e1(2)`` (``:545``), which is the "최근
    3개월" branch at ``:372-380``. Reproducing a relative default here would
    put a clock in a payload builder, so the caller supplies both dates.
    """

    start_date: str
    end_date: str
    ledger: str = KORAIL_MILEAGE_LEDGER_KTX
    movement: str = KORAIL_MILEAGE_MOVEMENT_ALL
    page_no: int = 1


def build_mileage_history_form(
    request: MileageHistoryRequest,
) -> dict[str, str]:
    if type(request) is not MileageHistoryRequest:
        raise TypeError("request must be an exact MileageHistoryRequest")
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
    start_date = _ascii_date(request.start_date, "start_date")
    end_date = _ascii_date(request.end_date, "end_date")
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
    """``ticket.dcntCrdUseQry.do`` — one card number, nothing else.

    ``ResearchService.java:51-52``. The app never asks the user to type this:
    ``Y4/C0907b.java:303`` copies ``dcnt_crd_info.h_dcnt_crd_no`` off the
    N-card ticket's own detail response into an intent extra, and
    ``TicketNCardHistoryActivity.java:138,109`` reads it straight back out into
    ``setDcntCrdNo``. So the natural source for this argument is
    :attr:`~korail_mobile_api.read_models.RefundTicketDetailResponse.discount_card`.
    """
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


@dataclass(frozen=True)
class DiscountCardScheduleRequest:
    """The 할인카드 schedule read's inputs (``ResearchService.java:54-55``).

    The app builds this in exactly two places — ``u4/b.java:52-65`` for the
    1-section N카드 and ``u4/b.java:67-81`` for the v2 (기간+횟수) card — and
    the two differ only in whether they carry :attr:`usage_period_days`. The
    defaults below are the values BOTH builders hardcode, so a caller who
    supplies only the card identity and the section's two station names sends
    what the app sends:

    * ``dptTm`` ``"000000"`` (``u4/b.java:55,70``) — from midnight, i.e. the
      whole day, which is why the app never offers a time picker here.
    * ``trnGpCd`` ``"109"`` — ``K4/s.java:5`` ``ALL("전체", "109")``
      (``u4/b.java:58,73``).
    * ``dirtChtnDvCd`` ``"1"`` — ``K4/d.java:5`` ``DIRECT_SQ_NO("직통", "1")``
      (``u4/b.java:59,74``). An N카드 section is always a direct leg; the app
      never sends ``"2"`` on this route.

    :attr:`card_kind_code` is one of exactly two literals. ``u4/b.java:60-61``
    sends ``"B2N"`` for the two original 1-section products
    (``B2N18120402``/``B2N18120403``) and ``"MMM"`` for everything else;
    ``u4/b.java:76`` hardcodes ``"MMM"`` on the v2 path. :meth:`for_card`
    reproduces that rule so a caller does not have to.

    NOT VERIFIED. No live call has been made on this route, and no account this
    project has access to owns an N카드, so the response shape below is the
    APK's DAO declaration rather than an observed body.
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
    ) -> "DiscountCardScheduleRequest":
        """Build a request, deriving ``dcntCrdKndCd`` the way ``u4/b.java`` does."""
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


#: The two ``dcntCrdKndMgNo`` values that make ``dcntCrdKndCd`` ``"B2N"``
#: rather than ``"MMM"`` (``u4/b.java:61``). They are the 2개월 and 3개월
#: 1-section N카드 products declared at
#: ``NCard1SectionBookingActivity.java:28``.
_B2N_CARD_KIND_MANAGEMENT_NOS = frozenset({"B2N18120402", "B2N18120403"})


def build_discount_card_schedule_query(
    request: DiscountCardScheduleRequest,
) -> dict[str, str]:
    """Render :class:`DiscountCardScheduleRequest` as the route's query.

    ``useTrmDno`` and ``qryPgNo`` are OMITTED when they are ``None``, because
    that is what the app transmits: neither builder ever calls ``setQryPgNo``
    and the 1-section builder never calls ``setUseTrmDno``, so Retrofit drops
    the null ``@Query`` (``ResearchService.java:54-55``). Both are registered
    as omittable in
    :data:`~korail_mobile_api.safety.KORAIL_OPTIONAL_REQUEST_FIELDS`.
    """
    if type(request) is not DiscountCardScheduleRequest:
        raise TypeError("request must be an exact DiscountCardScheduleRequest")
    query = {
        "dptDt": _ascii_date(request.departure_date, "departure_date"),
        "dptRsStnNm": _required_text(
            request.departure_station_name,
            "departure_station_name",
        ),
        "arvRsStnNm": _required_text(
            request.arrival_station_name,
            "arrival_station_name",
        ),
        "dptTm": _ascii_digits(request.departure_time, "departure_time", 6),
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
    if type(query) is not MaasServiceDetailQuery:
        raise TypeError("query must be an exact MaasServiceDetailQuery")
    _validate_maas_service_detail_query_values(
        query.start_date,
        query.end_date,
    )
    form = {"Device": config.device, "Version": config.version}
    if query.start_date is not None:
        form["qryDtFrom"] = query.start_date
        form["qryDtTo"] = query.end_date
    return form


def build_trip_change_date_form(departure_date: str) -> dict[str, str]:
    return {"tripChgDate": _ascii_date(departure_date, "departure_date")}


@dataclass(frozen=True, init=False)
class GiftTicketHistoryRequest:
    start_date: str = field(repr=False)
    end_date: str = field(repr=False)
    _query_division_code: str = field(repr=False)

    @classmethod
    def sent(
        cls,
        start_date: str,
        end_date: str,
    ) -> "GiftTicketHistoryRequest":
        return cls._create("A", start_date, end_date)

    @classmethod
    def received(
        cls,
        start_date: str,
        end_date: str,
    ) -> "GiftTicketHistoryRequest":
        return cls._create("C", start_date, end_date)

    @classmethod
    def _create(
        cls,
        query_division_code: str,
        start_date: str,
        end_date: str,
    ) -> "GiftTicketHistoryRequest":
        instance = object.__new__(cls)
        object.__setattr__(instance, "start_date", start_date)
        object.__setattr__(instance, "end_date", end_date)
        object.__setattr__(
            instance,
            "_query_division_code",
            query_division_code,
        )
        _validate_gift_ticket_history_request(instance)
        return instance


@dataclass(frozen=True)
class GiftTicketPaymentEligibilityRequest:
    pass


def _validate_gift_ticket_history_request(
    request: GiftTicketHistoryRequest,
) -> None:
    if request._query_division_code not in {"A", "C"}:
        raise ValueError("gift-ticket history mode is not supported")
    start = _calendar_date(request.start_date, "start_date")
    end = _calendar_date(request.end_date, "end_date")
    if end < start:
        raise ValueError("end_date must not be before start_date")


def build_gift_ticket_list_form(
    request: GiftTicketHistoryRequest
    | GiftTicketPaymentEligibilityRequest,
) -> tuple[tuple[str, str], ...]:
    if type(request) is GiftTicketHistoryRequest:
        _validate_gift_ticket_history_request(request)
        return (
            ("qryDvCd", request._query_division_code),
            ("qryVal", "E"),
            ("abrdDtFrom", request.start_date),
            ("abrdDtTo", request.end_date),
            ("usePsbFlg", ""),
        )
    if type(request) is GiftTicketPaymentEligibilityRequest:
        return (("qryDvCd", "F"), ("qryVal", "E"))
    raise TypeError("request must be an exact gift-ticket request variant")


def _exact_server_pass_data(pass_data: PassMenuData) -> str:
    if type(pass_data) is not PassMenuData:
        raise TypeError("pass_data must be an exact PassMenuData")
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
    ) -> "CommuterPassengerRequest":
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
    if type(request.source) is not CommuterInfoResponse:
        raise TypeError("source must be an exact CommuterInfoResponse")
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
    for option, age_code in zip(
        request.source.passenger_options,
        age_codes,
        strict=True,
    ):
        if type(option) is not CommuterPassengerOption:
            raise TypeError("response passenger options must use exact types")
        _required_text(age_code, "commuter_usage_age_code")
    for count in request.passenger_counts:
        if type(count) is not int or count < 0:
            raise ValueError(
                "passenger counts must be non-negative integers"
            )
    return age_codes


@dataclass(frozen=True)
class OriginalTicketReference:
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
    if type(reference) is not OriginalTicketReference:
        raise TypeError(
            "ticket must be an exact OriginalTicketReference"
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
    if type(request) is not TicketDuplicationCheckRequest:
        raise TypeError(
            "request must be an exact TicketDuplicationCheckRequest"
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


def build_platform_number_form(
    tickets: tuple[OriginalTicketReference, ...],
) -> tuple[tuple[str, str], ...]:
    references = _exact_ticket_reference_tuple(tickets)
    return (
        ("tkCnt", str(len(references))),
        *(("tkRetNo", _ticket_return_number(ticket)) for ticket in references),
    )


def build_original_ticket_inquiry_form(
    tickets: tuple[OriginalTicketReference, ...],
    *,
    ticket_count: int | None = None,
) -> tuple[tuple[str, str | int], ...]:
    """Build the 원표(원승차권) lookup's ordered form.

    ``POST research.tripChgOgtk.do`` (``ResearchService.java:61-63``). The
    route declares ``@Field("tkCnt") int`` followed by a ``@FieldMap``, so
    everything past ``tkCnt`` is one indexed group per original ticket. The
    key prefixes come from ``ROrtg.java:8-11`` (cross-checked
    ``ROrtg.smali:20-26``) and already end in ``_``, so row 1 is transmitted
    as ``ogtkSaleWctNo_1`` / ``ogtkSaleDd_1`` / ``ogtkSaleSqno_1`` /
    ``ogtkRetPwd_1``. Indices are 1-based: all three call sites increment
    before appending (``TCBookingActivity.java:169-175``,
    ``SeatSearchActivity.java:605-611``, ``PushHistoryActivity.java:
    345-351``).

    TWO honest caveats about this shape.

    The ORDER of the indexed keys is this library's choice, not the app's. The
    app builds a ``java.util.HashMap`` and hands it to Retrofit
    (``OgTkInquiryDao.java:15,52``), so its wire order is whatever the hash
    yields — and the app does not even agree with itself about the insertion
    order, since ``PushHistoryActivity`` puts ``ogtkSaleDd`` first while the
    other two put ``ogtkSaleWctNo`` first. Grouping by ticket in ``ROrtg``
    declaration order is deterministic and reproducible, which a map iteration
    is not.

    ``ticket_count`` (``tkCnt``) defaults to the number of tickets but is a
    free parameter, because the app's own three call sites mean three
    different things by it: ``TCBookingActivity.java:179`` sends the passenger
    count, ``PushHistoryActivity.java:357`` sends the row count and
    ``SeatSearchActivity.java:615`` hardcodes ``1`` while writing
    ``f29962H.size()`` rows. It is transmitted as an ``int`` because the smali
    signature says ``I`` (``ResearchService.smali:613,628-632``) — the
    neighbouring ``tk.plfNo.do`` declares the same NAME as a ``String``
    (``TicketService.java:72``), and sending the wrong one is exactly the
    string/number mismatch this codebase has been bitten by before.
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


@dataclass(frozen=True)
class SelfSeatChangeInfoRequest:
    """The train a 자율 좌석/열차 변경 is being considered for.

    ``POST self.seatChgInfo.do`` (``TicketService.java:54-56``). Every value
    is copied straight off the ticket the caller already holds:
    ``TCSOptionsActivity.java:131-134`` reads ``h_run_dt`` / ``h_trn_no`` /
    ``h_dpt_rs_stn_cd`` / ``h_arv_rs_stn_cd`` off the reservation's train
    info, unmodified — in particular ``trnNo`` is NOT zero-padded here, unlike
    the seat-inventory reads.

    :attr:`room_class_code` is genuinely optional. The app sets it only when
    the ticket's own class is 일반실 (``"1"``) or 특실 (``"2"``)
    (``TCSOptionsActivity.java:135-138``, ``K4/o.java:7-8``, cross-checked
    ``K4/o.smali:34-82``); for anything else the field stays null and Retrofit
    drops it, so ``None`` here reproduces a request the app really sends.
    """

    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    room_class_code: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        _validate_self_seat_change_info_request(self)


#: The two 객실 등급 codes the app will send on ``self.seatChgInfo.do``.
#: ``K4/o.java:7-8`` — GENERAL("일반실", "1") and SPECIAL("특실", "2"). The
#: enum's third member ALL ("전체", "9") is deliberately absent: the app's
#: branch admits only the first two.
SELF_SEAT_CHANGE_ROOM_CLASS_CODES = frozenset({"1", "2"})


def _validate_self_seat_change_info_request(
    request: SelfSeatChangeInfoRequest,
) -> None:
    _ascii_date(request.run_date, "run_date")
    _ascii_identifier(request.train_no, "train_no", maximum_length=5)
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
    if type(request) is not SelfSeatChangeInfoRequest:
        raise TypeError(
            "request must be an exact SelfSeatChangeInfoRequest"
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


@dataclass(frozen=True)
class SpecialRoomUpgradeQuoteRequest:
    """One journey of one ticket, priced for a 특실 업그레이드.

    ``GET myTicket.reqUpgradeSeat`` (``MyTicketService.java:23-24``,
    twenty-three of its twenty-six ``@Query`` parameters — ``Device`` /
    ``Version`` / ``Key`` are added by the transport).

    This is the QUOTE, not the purchase: the app shows the returned
    ``scnIndcAmt`` in a "이 마일리지를 차감하여 업그레이드 하시겠습니까?" dialog
    and only then calls the separate ``procUpgradeSeat`` route
    (``SpecialRoomUpgradeActivity.java:51-67,90-94``). See
    :meth:`~korail_mobile_api.client.KorailClient.get_special_room_upgrade_quote`
    for what that does and does not let you conclude.

    :attr:`car_no` and :attr:`seat_no` default to ``""`` — the app's own "any
    seat" branch sends them empty (``SpecialRoomUpgradeActivity.java:
    163-165``) and fills them only when the user picked a seat from the map
    (``:268-270``). :attr:`requested_seat_attribute_code` defaults to ``"15"``
    because both of those branches send exactly that: ``I4/a.AFTER_DEPARTURE``
    (``I4/a.java:5``, cross-checked ``I4/a.smali:7``).
    """

    original_ticket: OriginalTicketReference = field(repr=False)
    journey_type_code: str = field(repr=False)
    journey_sequence: str = field(repr=False)
    departure_date: str = field(repr=False)
    departure_construction_order: str = field(repr=False)
    departure_run_order: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    departure_time: str = field(repr=False)
    arrival_date: str = field(repr=False)
    arrival_construction_order: str = field(repr=False)
    arrival_run_order: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    arrival_time: str = field(repr=False)
    train_no: str = field(repr=False)
    run_date: str = field(repr=False)
    room_classification_code: str = field(repr=False)
    #: ``trnGpCd``. The app hardcodes ``"100"``
    #: (``SpecialRoomUpgradeActivity.java:126``) because a 특실 upgrade is a
    #: KTX-only product.
    train_group_code: str = field(default="100", repr=False)
    car_no: str = field(default="", repr=False)
    seat_no: str = field(default="", repr=False)
    requested_seat_attribute_code: str = field(default="15", repr=False)

    def __post_init__(self) -> None:
        _validate_special_room_upgrade_quote_request(self)


def _validate_special_room_upgrade_quote_request(
    request: SpecialRoomUpgradeQuoteRequest,
) -> None:
    if type(request.original_ticket) is not OriginalTicketReference:
        raise TypeError(
            "original_ticket must be an exact OriginalTicketReference"
        )
    _validate_original_ticket_reference(request.original_ticket)
    _ascii_date(request.departure_date, "departure_date")
    _ascii_date(request.arrival_date, "arrival_date")
    _ascii_date(request.run_date, "run_date")
    _ascii_digits(request.departure_time, "departure_time", 6)
    _ascii_digits(request.arrival_time, "arrival_time", 6)
    _ascii_identifier(request.train_no, "train_no", maximum_length=5)
    for value, name in (
        (request.journey_type_code, "journey_type_code"),
        (request.journey_sequence, "journey_sequence"),
        (
            request.departure_construction_order,
            "departure_construction_order",
        ),
        (request.departure_run_order, "departure_run_order"),
        (request.departure_station_code, "departure_station_code"),
        (request.arrival_construction_order, "arrival_construction_order"),
        (request.arrival_run_order, "arrival_run_order"),
        (request.arrival_station_code, "arrival_station_code"),
        (request.room_classification_code, "room_classification_code"),
        (request.train_group_code, "train_group_code"),
        (
            request.requested_seat_attribute_code,
            "requested_seat_attribute_code",
        ),
    ):
        _required_text(value, name)
    # Blank is the app's own "no seat chosen" value, so these two are checked
    # for type only.
    _optional_text(request.car_no, "car_no")
    _optional_text(request.seat_no, "seat_no")


def build_special_room_upgrade_quote_query(
    request: SpecialRoomUpgradeQuoteRequest,
) -> dict[str, str]:
    if type(request) is not SpecialRoomUpgradeQuoteRequest:
        raise TypeError(
            "request must be an exact SpecialRoomUpgradeQuoteRequest"
        )
    _validate_special_room_upgrade_quote_request(request)
    ticket = request.original_ticket
    return {
        "ogtkSaleDd": ticket.sale_date,
        "ogtkSaleWctNo": ticket.sale_window_no,
        "ogtkSaleSqno": ticket.sale_sequence,
        "ogtkRetPwd": ticket.return_password,
        "jrnyTpCd": request.journey_type_code,
        "jrnySqno": request.journey_sequence,
        "dptDt": request.departure_date,
        "dptStnConsOrdr": request.departure_construction_order,
        "dptStnRunOrdr": request.departure_run_order,
        "dptRsStnCd": request.departure_station_code,
        "dptTm": request.departure_time,
        "arvDt": request.arrival_date,
        "arvStnConsOrdr": request.arrival_construction_order,
        "arvStnRunOrdr": request.arrival_run_order,
        "arvRsStnCd": request.arrival_station_code,
        "arvTm": request.arrival_time,
        "trnNo": request.train_no,
        "runDt": request.run_date,
        "trnGpCd": request.train_group_code,
        "roomClsfCd": request.room_classification_code,
        "scarNo": request.car_no,
        "seatNo": request.seat_no,
        "rqSeatAttCd": request.requested_seat_attribute_code,
    }


def build_recent_delivery_history_form(customer_no: str) -> dict[str, str]:
    return {"custMgNo": _required_text(customer_no, "customer_no")}


@dataclass(frozen=True)
class CommuterTicketInquiryRequest:
    original_ticket: OriginalTicketReference = field(repr=False)
    inquiry_type: str = field(default="0", repr=False)

    def __post_init__(self) -> None:
        if self.inquiry_type not in {"0", "1"}:
            raise ValueError("inquiry_type must be '0' or '1'")
        if type(self.original_ticket) is not OriginalTicketReference:
            raise TypeError(
                "original_ticket must be an exact OriginalTicketReference"
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
        return (
            ("jobDvCd", "b"),
            ("cmtrKndCd", kind_code),
            ("psgCnt", str(len(age_codes))),
            *(("cmtrUtlAgeCd", value) for value in age_codes),
            *(("psgPrnb", str(value)) for value in request.passenger_counts),
        )
    if type(request) is CommuterTicketInquiryRequest:
        if type(request.original_ticket) is not OriginalTicketReference:
            raise TypeError(
                "original_ticket must be an exact OriginalTicketReference"
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
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    goods_no: str = field(repr=False)
    requested_seat_attribute_code: str = field(repr=False)
    train_group_code: str = field(repr=False)
    standing_train_classification_code: str = field(repr=False)

    def __post_init__(self) -> None:
        _validate_price_fare_leg(self)


def _validate_price_fare_leg(leg: PriceFareLeg) -> None:
    for value, name in (
        (leg.departure_station_code, "departure_station_code"),
        (leg.arrival_station_code, "arrival_station_code"),
        (leg.run_date, "run_date"),
        (leg.train_no, "train_no"),
        (leg.goods_no, "goods_no"),
        (leg.requested_seat_attribute_code, "requested_seat_attribute_code"),
        (leg.train_group_code, "train_group_code"),
        (
            leg.standing_train_classification_code,
            "standing_train_classification_code",
        ),
    ):
        _wire_component(value, name)


@dataclass(frozen=True)
class PriceFareQuoteRequest:
    """One or two legs to price, plus the app's client-side ``txtMenuId``.

    ``txtMenuId`` is NOT a server value. The app hardcodes it: ``a5/k.java:92-94``
    returns ``"11"``, ``a5/u.java:279`` passes it as the ``MENU_ID`` intent
    extra, ``PriceFareActivity.java:49`` reads it back and ``:62`` sets it on the
    Price2Fare request. The default is therefore the app's constant, so a quote
    can be built straight from a parsed search response.

    This used to read ``menu_id`` off ``TrainSearchMetadata``, which parsed it
    from a response key (``h_menu_id``) that does not exist anywhere in the app,
    so every request built from a real search result raised.
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
        if type(leg) is not PriceFareLeg:
            raise TypeError("legs must contain exact PriceFareLeg values")
        _validate_price_fare_leg(leg)


def build_price_fare_quote_form(
    request: PriceFareQuoteRequest,
) -> tuple[tuple[str, str], ...]:
    if type(request) is not PriceFareQuoteRequest:
        raise TypeError("request must be an exact PriceFareQuoteRequest")
    _validate_price_fare_quote_request(request)
    columns = (
        ("dptRsStnCd", "departure_station_code"),
        ("arvRsStnCd", "arrival_station_code"),
        ("runDt", "run_date"),
        ("trnNo", "train_no"),
        ("gdNo", "goods_no"),
        ("rqSeatAttCd", "requested_seat_attribute_code"),
        ("trnGpCd", "train_group_code"),
        ("stlbTrnClsfCd", "standing_train_classification_code"),
    )
    return (
        ("txtMenuId", request.menu_id),
        ("chtnDvCd", str(len(request.legs))),
        *(
            (
                wire_name,
                ",".join(getattr(leg, attribute) for leg in request.legs),
            )
            for wire_name, attribute in columns
        ),
    )


_PRODUCT_TRAIN_GROUP_CODES = frozenset({"100", "101", "102", "104", "109"})
_PRODUCT_SEAT_ATTRIBUTE_CODES = frozenset(
    {"015", "018", "019", "020", "021", "028", "032", "052"}
)


@dataclass(frozen=True)
class _ProductPassengerGroups:
    adult: int = field(repr=False)
    child: int = field(repr=False)
    senior: int = field(repr=False)
    high_disability: int = field(repr=False)
    low_disability: int = field(repr=False)

    def __post_init__(self) -> None:
        for value in (
            self.adult,
            self.child,
            self.senior,
            self.high_disability,
            self.low_disability,
        ):
            if type(value) is not int or value < 0:
                raise ValueError(
                    "product passenger groups must be non-negative integers"
                )
        if self.total < 1:
            raise ValueError("product inquiry requires at least one passenger")

    @property
    def total(self) -> int:
        return (
            self.adult
            + self.child
            + self.senior
            + self.high_disability
            + self.low_disability
        )


@dataclass(frozen=True)
class _ProductTransferContext:
    connection_station_code: str = field(repr=False)
    connection_train_group_code: str = field(repr=False)

    def __post_init__(self) -> None:
        _required_text(
            self.connection_station_code,
            "connection_station_code",
        )
        if self.connection_train_group_code not in _PRODUCT_TRAIN_GROUP_CODES:
            raise ValueError(
                "connection_train_group_code is not an observed product code"
            )


@dataclass(frozen=True, init=False)
class _ProductTrainInquiryContinuation:
    source: ProductTrainInquiryResponse = field(repr=False)
    _mode: str = field(repr=False)

    @classmethod
    def direct(
        cls,
        source: ProductTrainInquiryResponse,
    ) -> "_ProductTrainInquiryContinuation":
        return cls._create("direct", source)

    @classmethod
    def transfer(
        cls,
        source: ProductTrainInquiryResponse,
    ) -> "_ProductTrainInquiryContinuation":
        return cls._create("transfer", source)

    @classmethod
    def _create(
        cls,
        mode: str,
        source: ProductTrainInquiryResponse,
    ) -> "_ProductTrainInquiryContinuation":
        instance = object.__new__(cls)
        object.__setattr__(instance, "source", source)
        object.__setattr__(instance, "_mode", mode)
        _validate_product_train_inquiry_continuation(instance)
        return instance


def _validate_product_train_inquiry_continuation(
    continuation: _ProductTrainInquiryContinuation,
) -> tuple[str, str, str, str]:
    if type(continuation) is not _ProductTrainInquiryContinuation:
        raise TypeError(
            "continuation must be an exact product inquiry continuation"
        )
    if type(continuation.source) is not ProductTrainInquiryResponse:
        raise TypeError(
            "continuation source must be an exact ProductTrainInquiryResponse"
        )
    source = continuation.source
    query_station_no = _required_text(
        source.next_query_station_no,
        "continuation next_query_station_no",
    )
    page_count = _required_text(
        source.result_count,
        "continuation result_count",
    )
    if continuation._mode == "direct":
        first_train_no = _required_text(
            source.next_train_no,
            "continuation next_train_no",
        )
        second_train_no = ""
    elif continuation._mode == "transfer":
        first_train_no = _required_text(
            source.preceding_train_no_next,
            "continuation preceding_train_no_next",
        )
        second_train_no = _required_text(
            source.early_train_no_next,
            "continuation early_train_no_next",
        )
    else:
        raise ValueError("product inquiry continuation mode is invalid")
    return query_station_no, first_train_no, second_train_no, page_count


@dataclass(frozen=True)
class _ProductTrainInquiryRequest:
    product: PassMenuItem = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    departure_date: str = field(repr=False)
    departure_time: str = field(repr=False)
    passengers: _ProductPassengerGroups = field(repr=False)
    seat_attribute_code: str = field(default="015", repr=False)
    transfer: _ProductTransferContext | None = field(default=None, repr=False)
    continuation: _ProductTrainInquiryContinuation | None = field(
        default=None,
        repr=False,
    )

    def __post_init__(self) -> None:
        _validate_product_train_inquiry_request(self)


def _validate_product_train_inquiry_request(
    request: _ProductTrainInquiryRequest,
) -> tuple[str, str]:
    if type(request.product) is not PassMenuItem:
        raise TypeError("product must be an exact PassMenuItem")
    goods_data = request.product.goods_data
    if goods_data is None or type(goods_data) is not PassGoodsInfo:
        raise ValueError("product must contain server goods metadata")
    goods_no = _required_text(
        goods_data.h_cnd_flg_disc_no,
        "product goods number",
    )
    train_group_code = _required_text(
        request.product.train_group_code,
        "product train group code",
    )
    if train_group_code not in _PRODUCT_TRAIN_GROUP_CODES:
        raise ValueError("product train group code is not observed")
    _required_text(
        request.departure_station_code,
        "departure_station_code",
    )
    _required_text(request.arrival_station_code, "arrival_station_code")
    _ascii_date(request.departure_date, "departure_date")
    _ascii_digits(request.departure_time, "departure_time", 6)
    if type(request.passengers) is not _ProductPassengerGroups:
        raise TypeError("passengers must be exact product passenger groups")
    _ProductPassengerGroups.__post_init__(request.passengers)
    passenger_info = goods_data.psg_infos
    if passenger_info is not None:
        if type(passenger_info) is not PassPassengerInfos:
            raise TypeError(
                "product passenger metadata must use its exact response type"
            )
        minimum = passenger_info.h_min_cnt
        maximum = passenger_info.h_max_cnt
        if minimum is not None:
            minimum_value = int(_ascii_identifier(minimum, "product minimum"))
            if request.passengers.total < minimum_value:
                raise ValueError("passenger total is below the product minimum")
        if maximum is not None:
            maximum_value = int(_ascii_identifier(maximum, "product maximum"))
            if request.passengers.total > maximum_value:
                raise ValueError("passenger total exceeds the product maximum")
    if request.seat_attribute_code not in _PRODUCT_SEAT_ATTRIBUTE_CODES:
        raise ValueError("seat_attribute_code is not an observed product value")
    if request.transfer is not None and type(
        request.transfer
    ) is not _ProductTransferContext:
        raise TypeError("transfer must be an exact product transfer context")
    if request.transfer is not None:
        _ProductTransferContext.__post_init__(request.transfer)
    if request.continuation is not None:
        if type(request.continuation) is not _ProductTrainInquiryContinuation:
            raise TypeError(
                "continuation must be an exact product inquiry continuation"
            )
        _validate_product_train_inquiry_continuation(request.continuation)
        expected_mode = "transfer" if request.transfer is not None else "direct"
        if request.continuation._mode != expected_mode:
            raise ValueError(
                "continuation mode must match the selected product inquiry mode"
            )
    return goods_no, train_group_code


def _build_product_train_inquiry_form(
    config: KorailConfig,
    request: _ProductTrainInquiryRequest,
) -> tuple[tuple[str, str], ...]:
    if type(request) is not _ProductTrainInquiryRequest:
        raise TypeError("request must be an exact product inquiry request")
    goods_no, train_group_code = _validate_product_train_inquiry_request(
        request
    )
    transfer_fields: tuple[tuple[str, str], ...] = ()
    query_station_no = "0"
    first_train_no = "00000"
    second_train_no = ""
    page_count = "10"
    job_id = "1"
    if request.transfer is not None:
        job_id = "2"
        page_count = "0"
        transfer_fields = (
            ("chtnCnt", "1"),
            (
                "chtnRsStnCd1",
                request.transfer.connection_station_code,
            ),
            ("trnGpCnt", "1"),
            ("trnGpCd1", request.transfer.connection_train_group_code),
        )
    if request.continuation is not None:
        (
            query_station_no,
            first_train_no,
            second_train_no,
            page_count,
        ) = _validate_product_train_inquiry_continuation(
            request.continuation
        )
    passenger_values = (
        request.passengers.adult,
        request.passengers.child,
        request.passengers.senior,
        request.passengers.high_disability,
        request.passengers.low_disability,
    )
    return (
        ("Device", config.device),
        ("Version", config.version),
        ("txtMenuId", "41"),
        ("radJobId", job_id),
        ("selGoTrain", train_group_code),
        ("txtTrnGpCd", train_group_code),
        ("txtGoStart", request.departure_station_code),
        ("txtGoEnd", request.arrival_station_code),
        ("txtGoAbrdDt", request.departure_date),
        ("txtGoHour", request.departure_time),
        *(
            (f"txtPsgFlg_{index}", str(value))
            for index, value in enumerate(passenger_values, 1)
        ),
        ("txtSeatAttCd_2", "000"),
        ("txtSeatAttCd_3", "000"),
        ("txtSeatAttCd_4", request.seat_attribute_code),
        ("txtGdNo", goods_no),
        ("qryDvCd", "1"),
        ("qryStNo", query_station_no),
        ("qryStTrnNo", first_train_no),
        ("qryStTrnNo2", second_train_no),
        ("pgPrCnt", page_count),
        *transfer_fields,
    )


@dataclass(frozen=True)
class TicketReservationDetailRequest:
    """The PNR whose held-reservation detail to read.

    Feeds ``certification.ReservationList`` (``inquiryTicketRsv``,
    ``CertificationService.java:45-46``). The PNR is ``repr=False`` because it
    identifies a real reservation.
    """

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
    """Build the READ overload's exact single query field.

    ``certification.ReservationList`` also hosts the write-flavoured
    ``applyDisabilityCertification`` overload (``CertificationService.java:22``),
    which adds ``txtPsgDisc0019Cnt`` and six ``@QueryMap``s. This builder emits
    ``hidPnrNo`` and nothing else, and the route's entry in
    ``KORAIL_EXACT_REQUEST_FIELDS`` refuses anything wider, so the write shape
    cannot be produced through this path.
    """
    if type(request) is not TicketReservationDetailRequest:
        raise TypeError(
            "request must be an exact TicketReservationDetailRequest"
        )
    _validate_ticket_reservation_detail_request(request)
    return {"hidPnrNo": request.pnr_no}


@dataclass(frozen=True)
class RefundCompanion:
    """The companion identity ``refunds.CommissionView`` echoes back.

    Both app call sites take these straight off a ``SelTicketInfo`` response:
    ``h_comp_nm`` from ``getH_compa_nm()`` and ``h_comp_cert_no`` from
    ``getH_compa_brth()`` (``TicketListActivity.java:908-909``,
    ``ui/ticket/ticketReturn/a.java:355-356``). A ticket with no companion
    sends both empty, which is why empty strings are accepted here — the two
    fields are always transmitted, never omitted.
    """

    name: str = field(default="", repr=False)
    certificate_no: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        _validate_refund_companion(self)


def _validate_refund_companion(companion: RefundCompanion) -> None:
    for value, name in (
        (companion.name, "name"),
        (companion.certificate_no, "certificate_no"),
    ):
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def _exact_refund_companion(companion: RefundCompanion) -> RefundCompanion:
    if type(companion) is not RefundCompanion:
        raise TypeError("companion must be an exact RefundCompanion")
    _validate_refund_companion(companion)
    return companion


def build_refund_commission_form(
    ticket: OriginalTicketReference,
    companion: RefundCompanion = RefundCompanion(),
) -> dict[str, str]:
    """Build the refund fee / refundable-amount pre-check form.

    ``RefundService.java:19-21`` declares POST + @FormUrlEncoded with exactly
    these six fields on top of Device/Version/Key. Note the sale-date field is
    ``h_orgtk_ret_sale_dt`` here, NOT the ``h_orgtk_sale_dt`` the receipt read
    uses — the two routes spell the same value differently.
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
) -> dict[str, str]:
    """Build the refund-target ticket detail form.

    POST with the four identity fields plus ``h_purchase_history``
    (``RefundService.java:23-25``). The flag is exactly "Y" or "N" in the app:
    the purchase-history screen sends "Y"
    (``TicketPurchaseHistoryActivity.java:267``) and the ticket list and
    seat-assign screens send "N" (``TicketListActivity.java:926``,
    ``SeatAssignBookingActivity.java:317``).

    srtgo issues this as a GET and drops ``h_purchase_history`` entirely
    (``ktx.py:791-800``). The app is the authority and it declares POST with
    the field present, so this builder always emits it.
    """
    reference = _exact_original_ticket_reference(ticket)
    if type(from_purchase_history) is not bool:
        raise TypeError("from_purchase_history must be a bool")
    return {
        "h_orgtk_ret_sale_dt": reference.sale_date,
        "h_orgtk_wct_no": reference.sale_window_no,
        "h_orgtk_sale_sqno": reference.sale_sequence,
        "h_orgtk_ret_pwd": reference.return_password,
        "h_purchase_history": "Y" if from_purchase_history else "N",
    }
