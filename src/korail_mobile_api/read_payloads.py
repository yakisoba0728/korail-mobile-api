from __future__ import annotations

import time
from dataclasses import dataclass, field

from .config import KorailConfig


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
