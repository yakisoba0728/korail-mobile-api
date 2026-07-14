from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from korail_mobile_api import (
    KorailClient,
    PhysicalSeat,
    SeatAttribute,
    SeatCar,
    SeatCarListResponse,
    SeatInventoryResponse,
    SeatWindow,
    TrainSearchQuery,
    TrainSummary,
)
from korail_mobile_api.live import (
    build_config_from_env,
    live_enabled,
    read_credentials_from_env,
)


_STATUSES = frozenset(
    {
        "setup_failed",
        "login_failed",
        "search_failed",
        "no_trains",
        "no_eligible_train",
        "car_list_failed",
        "no_cars",
        "seat_list_failed",
        "completed",
    }
)
_SUFFICIENCY = frozenset(
    {
        "insufficient_setup",
        "insufficient_login",
        "insufficient_search",
        "insufficient_no_trains",
        "insufficient_no_eligible_train",
        "insufficient_car_list",
        "insufficient_no_cars",
        "insufficient_seat_list",
        "insufficient_fields",
        "sufficient",
    }
)
_CALL_KEYS = ("login", "search", "car_list", "seat_list")
_FIELD_KEYS = (
    "train_fields_present",
    "car_fields_typed",
    "seat_fields_typed",
    "physical_seat_fields_typed",
    "window_fields_typed",
    "banner_field_typed",
)
_RESULT_KEYS = frozenset(
    {
        "status",
        "calls",
        "train_count",
        "car_count",
        "seat_count",
        "window_count",
        "fields",
        "sufficiency",
    }
)
_SENSITIVE_ENV_NAMES = (
    "KORAIL_MEMBER_NO",
    "KORAIL_PASSWORD",
    "KORAIL_DYNAPATH_DEVICE_ID",
    "KORAIL_DYNAPATH_AS_VALUE",
    "KORAIL_DYNAPATH_DEVICE_MODEL",
    "KORAIL_DYNAPATH_OS_VERSION",
    "KORAIL_ADVERTISING_ID",
    "KORAIL_BASE_URL",
    "KORAIL_USER_AGENT",
    "KORAIL_TEST_DATE",
    "KORAIL_DEPARTURE_STATION",
    "KORAIL_ARRIVAL_STATION",
    "KORAIL_DEPARTURE_STATION_CODE",
    "KORAIL_ARRIVAL_STATION_CODE",
    "KORAIL_DEPARTURE_TIME",
)


def _empty_result() -> dict[str, Any]:
    return {
        "status": "setup_failed",
        "calls": {name: 0 for name in _CALL_KEYS},
        "train_count": 0,
        "car_count": 0,
        "seat_count": 0,
        "window_count": 0,
        "fields": {name: False for name in _FIELD_KEYS},
        "sufficiency": "insufficient_setup",
    }


def _stop(
    result: dict[str, Any],
    status: str,
    sufficiency: str,
) -> dict[str, Any]:
    result["status"] = status
    result["sufficiency"] = sufficiency
    return result


def _bounded_count(values: Sequence[object]) -> int:
    return min(len(values), 10_000)


def _first_eligible_general_seat_train(
    trains: Sequence[TrainSummary],
) -> TrainSummary | None:
    for train in trains:
        if train.general_reservation_code in {"12", "13"}:
            continue
        flag = train.seat_map_flag
        if flag and flag[0] == "N":
            continue
        return train
    return None


def _train_fields_present(train: TrainSummary) -> bool:
    values = (
        train.train_no,
        train.train_group_code,
        train.departure_station_code,
        train.arrival_station_code,
        train.departure_date,
        train.run_date,
        train.train_class_code,
        train.departure_run_order,
        train.arrival_run_order,
    )
    return all(isinstance(value, str) and bool(value) for value in values)


def _car_fields_typed(response: SeatCarListResponse) -> bool:
    if (
        not isinstance(response, SeatCarListResponse)
        or (
            response.recommended_car_no is not None
            and type(response.recommended_car_no) is not int
        )
        or (
            response.train_no is not None
            and not isinstance(response.train_no, str)
        )
        or not isinstance(response.cars, tuple)
    ):
        return False
    return bool(response.cars) and all(
        isinstance(car, SeatCar)
        and type(car.car_no) is int
        and isinstance(car.room_class_name, str)
        and type(car.remaining_seat_count) is int
        and isinstance(car.attributes, tuple)
        and all(
            isinstance(attribute, SeatAttribute)
            and isinstance(attribute.name, str)
            for attribute in car.attributes
        )
        for car in response.cars
    )


def _seat_fields_typed(response: SeatInventoryResponse) -> bool:
    return (
        isinstance(response, SeatInventoryResponse)
        and type(response.layout_type) is int
        and isinstance(response.arrangement_code, str)
        and type(response.remaining_count) is int
        and type(response.total_count) is int
        and isinstance(response.seats, tuple)
        and isinstance(response.windows, tuple)
    )


def _physical_seat_fields_typed(seats: tuple[PhysicalSeat, ...]) -> bool:
    return bool(seats) and all(
        isinstance(seat, PhysicalSeat)
        and (
            seat.floor is None
            or isinstance(seat.floor, str)
        )
        and all(
            isinstance(value, str)
            for value in (
                seat.seat_no,
                seat.sale_possible,
                seat.direction_code,
                seat.other_attribute_code,
                seat.requested_attribute_code,
                seat.specification,
                seat.sequence_no,
                seat.message_code,
                seat.message,
                seat.visual_message_division_code,
            )
        )
        for seat in seats
    )


def _window_fields_typed(windows: tuple[SeatWindow, ...]) -> bool:
    return all(
        isinstance(window, SeatWindow)
        and type(window.start_location_ratio) is float
        and type(window.close_location_ratio) is float
        and math.isfinite(window.start_location_ratio)
        and math.isfinite(window.close_location_ratio)
        for window in windows
    )


def capture_evidence() -> dict[str, Any]:
    result = _empty_result()
    try:
        if not live_enabled():
            return result
        member_no, password = read_credentials_from_env()
        config = build_config_from_env()
        departure_date = os.environ.get("KORAIL_TEST_DATE", "")
        if not departure_date:
            return result
        departure_station = os.environ.get(
            "KORAIL_DEPARTURE_STATION",
            "서울",
        ).strip()
        arrival_station = os.environ.get(
            "KORAIL_ARRIVAL_STATION",
            "부산",
        ).strip()
        if (
            not departure_station
            or not arrival_station
            or departure_station.isdigit()
            or arrival_station.isdigit()
        ):
            return result
        query = TrainSearchQuery(
            departure_station_code=departure_station,
            arrival_station_code=arrival_station,
            departure_date=departure_date,
            departure_time=os.environ.get(
                "KORAIL_DEPARTURE_TIME",
                "060000",
            ),
            passengers=1,
        )
        client = KorailClient(config)
    except Exception:
        return result

    try:
        result["calls"]["login"] = 1
        try:
            client.login(member_no, password)
        except Exception:
            return _stop(result, "login_failed", "insufficient_login")

        result["calls"]["search"] = 1
        try:
            search = client.search_trains(query)
        except Exception:
            return _stop(result, "search_failed", "insufficient_search")
        result["train_count"] = _bounded_count(search.trains)
        if not search.trains:
            return _stop(result, "no_trains", "insufficient_no_trains")
        train = _first_eligible_general_seat_train(search.trains)
        if train is None:
            return _stop(
                result,
                "no_eligible_train",
                "insufficient_no_eligible_train",
            )
        result["fields"]["train_fields_present"] = (
            _train_fields_present(train)
        )

        result["calls"]["car_list"] = 1
        try:
            cars = client.get_seat_cars(train, passenger_count=1)
        except Exception:
            return _stop(
                result,
                "car_list_failed",
                "insufficient_car_list",
            )
        result["car_count"] = _bounded_count(cars.cars)
        result["fields"]["car_fields_typed"] = _car_fields_typed(cars)
        if not cars.cars:
            return _stop(result, "no_cars", "insufficient_no_cars")

        result["calls"]["seat_list"] = 1
        try:
            inventory = client.get_seat_inventory(
                train,
                cars.cars[0].car_no,
                passenger_count=1,
            )
        except Exception:
            return _stop(
                result,
                "seat_list_failed",
                "insufficient_seat_list",
            )
        result["seat_count"] = _bounded_count(inventory.seats)
        result["window_count"] = _bounded_count(inventory.windows)
        result["fields"]["seat_fields_typed"] = _seat_fields_typed(
            inventory
        )
        result["fields"]["physical_seat_fields_typed"] = (
            _physical_seat_fields_typed(inventory.seats)
        )
        result["fields"]["window_fields_typed"] = _window_fields_typed(
            inventory.windows
        )
        result["fields"]["banner_field_typed"] = (
            inventory.vr_banner_url is None
            or isinstance(inventory.vr_banner_url, str)
        )
        sufficiency = (
            "sufficient"
            if all(result["fields"].values())
            else "insufficient_fields"
        )
        return _stop(result, "completed", sufficiency)
    finally:
        try:
            client.close()
        except Exception:
            pass


def _validate_result(result: Mapping[str, Any]) -> None:
    if set(result) != _RESULT_KEYS:
        raise ValueError("evidence result has an unsafe schema")
    if result.get("status") not in _STATUSES:
        raise ValueError("evidence result has an invalid fixed status")
    if result.get("sufficiency") not in _SUFFICIENCY:
        raise ValueError("evidence result has an invalid sufficiency")
    calls = result.get("calls")
    if not isinstance(calls, Mapping) or set(calls) != set(_CALL_KEYS):
        raise ValueError("evidence result has invalid call counters")
    if any(type(calls[name]) is not int or calls[name] not in {0, 1} for name in _CALL_KEYS):
        raise ValueError("evidence call counter exceeded its budget")
    for name in ("train_count", "car_count", "seat_count", "window_count"):
        value = result.get(name)
        if type(value) is not int or not 0 <= value <= 10_000:
            raise ValueError("evidence count exceeded its bound")
    field_presence = result.get("fields")
    if (
        not isinstance(field_presence, Mapping)
        or set(field_presence) != set(_FIELD_KEYS)
        or any(type(field_presence[name]) is not bool for name in _FIELD_KEYS)
    ):
        raise ValueError("evidence field-presence schema is invalid")


def _safe_serialization(result: Mapping[str, Any]) -> str:
    _validate_result(result)
    serialized = json.dumps(
        result,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    lowered = serialized.casefold()
    for forbidden in (
        "http://",
        "https://",
        "://",
        "credential",
        "password",
        "member_no",
        "cookie",
        "token",
        "identifier",
        '"sid"',
        '"url"',
        '"date"',
        '"station"',
        '"card"',
        "card_no",
        "seat_no",
        "train_no",
        "station_code",
        '"raw"',
        '"message"',
    ):
        if forbidden in lowered:
            raise ValueError("evidence serialization failed the secret scan")
    for name in _SENSITIVE_ENV_NAMES:
        value = os.environ.get(name)
        if value and len(value) >= 4 and value.casefold() in lowered:
            raise ValueError("evidence serialization failed the secret scan")
    return serialized


def write_evidence(
    output: Path,
    result: Mapping[str, Any],
    *,
    force: bool,
) -> None:
    output = Path(output)
    serialized = _safe_serialization(result)
    if output.exists() and not force:
        raise FileExistsError(output)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(serialized)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        if force:
            os.replace(temporary_path, output)
        else:
            os.link(temporary_path, output)
            temporary_path.unlink()
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_output_destination(output: Path, *, force: bool) -> None:
    parent = output.parent
    if not parent.exists():
        raise FileNotFoundError(parent)
    if not parent.is_dir():
        raise NotADirectoryError(parent)
    if output.exists() and output.is_dir():
        raise IsADirectoryError(output)
    if os.path.lexists(output) and not force:
        raise FileExistsError(output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture bounded sanitized KORAIL seat inventory evidence"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args(argv)
    _validate_output_destination(
        arguments.output,
        force=arguments.force,
    )
    write_evidence(
        arguments.output,
        capture_evidence(),
        force=arguments.force,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
