# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예약·예약 내역·장바구니 응답을 읽습니다. 변경 응답 파싱 실패 시 전체 raw와 부분 parser_raw를 보존하며 재전송하지 않습니다."""

from __future__ import annotations

from collections.abc import Mapping

from ..._core.parsing import (
    _is_list,
    _is_mapping,
    _nested_rows,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _required_integer,
    _response_fields,
    _response_mapping,
    _row,
    _rows,
    _strict_scalar_string,
    _validate_envelope,
    _validate_strict_read_envelope,
    wire_model,
    wire_models,
)
from ..._core.wire import _is_ascii_digits
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


def _reservation_passengers(raw: Mapping[str, object]) -> tuple[ReservationPassengerInfo, ...]:
    """컨테이너가 없거나 모양이 다르면 빈 튜플이고 원문은 raw 에 남습니다."""
    return wire_models(
        ReservationPassengerInfo,
        _nested_rows(raw, "psg_infos", "psg_info"),
        "reservation passenger",
        copy_raw=True,
    )


@_preserve_read_raw
def parse_cart_list_response(raw: Mapping[str, object]) -> CartListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = wire_models(CartItem, _nested_rows(raw, "cart_infos", "cart_info"), "cart item")
    return CartListResponse(items=items, **_response_fields(raw))


def _parse_reservation_history_reservation(
    raw: Mapping[str, object] | None,
) -> ReservationHistoryReservation | None:
    """전송 키 reservationOut 은 보호된 serializer 대신 속성명으로 추정한 값입니다."""
    if raw is None:
        return None
    return wire_model(
        ReservationHistoryReservation,
        raw,
        "reservation history reservation",
        tickets=wire_models(ReservationHistoryTicket, _rows(raw, "tkList"), "reservation history ticket"),
        original_tickets=wire_models(
            ReservationHistoryOriginalTicket, _rows(raw, "orgTkList"), "reservation history original ticket"
        ),
        passengers=wire_models(
            ReservationHistoryPassenger,
            _nested_rows(raw, "psg_infos", "psg_info"),
            "reservation history passenger",
        ),
        raw=raw,
    )


@_preserve_read_raw
def parse_reservation_history_response(
    raw: Mapping[str, object],
) -> ReservationHistoryResponse:
    """예약 이력의 예약자 정보와 여정별 상세를 읽습니다."""
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"P100"}),
    )
    if empty:
        return ReservationHistoryResponse(**_response_fields(raw))
    guide_infos = _optional_mapping(raw, "guide_infos")
    guide_info = _optional_scalar_string(guide_infos, "guide_info") if guide_infos is not None else None
    journeys: list[ReservationHistoryJourney] = []
    all_trains: list[ReservationHistoryTrain] = []
    for journey in _nested_rows(raw, "jrny_infos", "jrny_info"):
        trains = wire_models(
            ReservationHistoryTrain,
            _nested_rows(journey, "train_infos", "train_info"),
            "reservation history train",
        )
        all_trains.extend(trains)
        journeys.append(
            ReservationHistoryJourney(
                trains=trains,
                service_infos=tuple(_nested_rows(journey, "srv_infos", "srv_info")),
                accompanying_infos=tuple(_nested_rows(journey, "acmp_infos", "acmp_info")),
                reservation=_parse_reservation_history_reservation(
                    _optional_mapping(journey, "reservationOut")
                ),
                raw=journey,
            )
        )
    return wire_model(
        ReservationHistoryResponse,
        raw,
        "reservation history",
        guide_info=guide_info,
        journeys=tuple(journeys),
        items=tuple(all_trains),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_ticket_duplication_check_response(
    raw: Mapping[str, object],
) -> TicketDuplicationCheckResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(TicketDuplicationCheckResponse, raw, "ticket duplication", **_response_fields(raw))


@_preserve_read_raw
def parse_ticket_reservation_detail_response(
    raw: Mapping[str, object],
) -> TicketReservationDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = tuple(
        wire_model(
            ReservationDetailJourney,
            journey,
            "reservation detail journey",
            run_date=(_optional_scalar_string(journey, "h_run_dt") if "h_run_dt" in journey else ""),
            seats=wire_models(
                ReservationSeatDetail, _nested_rows(journey, "seat_infos", "seat_info"), "reservation seat"
            ),
            raw=journey,
        )
        for journey in _nested_rows(raw, "jrny_infos", "jrny_info")
    )
    return wire_model(
        TicketReservationDetailResponse,
        raw,
        "reservation detail",
        journeys=journeys,
        passengers=_reservation_passengers(raw),
        **_response_fields(raw),
    )


def _received_amount(
    raw: Mapping[str, object],
    journey_rows: list[Mapping[str, object]],
) -> str | None:
    """앱은 일반 결제에서 h_tot_rcvd_amt 를 합산합니다. 번호 붙은 결제 금액으로의 최종 연결은 보호된 Bundle 키 때문에 미확인입니다."""
    declared = _strict_scalar_string(raw, "h_tot_rcvd_amt", "reservation")
    if declared is not None:
        declared = declared.strip()
        if not _is_ascii_digits(declared):
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
    journeys_with_seats = 0
    for journey in journey_rows:
        container = journey.get("seat_infos")
        if container is None:
            continue
        if not _is_mapping(container):
            raise KorailProtocolError("KORAIL reservation seat_infos must be an object or null")
        seat_rows = container.get("seat_info")
        if seat_rows is None:
            continue
        if not _is_list(seat_rows):
            raise KorailProtocolError("KORAIL reservation seat_infos.seat_info must be a list or null")
        previous_seats = seats_seen
        for seat in seat_rows:
            seat = _row(seat, "reservation seat_info row")
            amount = _strict_scalar_string(seat, "h_rcvd_amt", "reservation seat")
            if amount is None or not _is_ascii_digits(amount.strip()):
                return None
            try:
                value = int(amount)
            except ValueError:
                # 큰 정수의 문자열 변환 실패도 0원으로 취급하지 않습니다.
                return None
            seat_no = _optional_scalar_string(seat, "h_seat_no") or ""
            if value == 0 and not seat_no.strip():
                # 예약대기 관측: 좌석번호 없는 0원 행은 정산 좌석이 아니었습니다.
                continue
            summed += value
            seats_seen += 1
        if seats_seen > previous_seats:
            journeys_with_seats += 1
    count = _strict_scalar_string(raw, "h_jrny_cnt", "reservation")
    if (
        journey_rows
        and count is not None
        and _is_ascii_digits(count.strip())
        and count.strip().lstrip("0") != str(len(journey_rows))
    ):
        return None
    if seats_seen == 0:
        return None if declared_int is None else str(declared_int)
    # 일부 여정의 좌석 합은 명시 총액이 같아도 완전한 결제액이 아닙니다.
    if journeys_with_seats != len(journey_rows):
        return None
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
    # 0 채움 없는 정산액은 앱 재현이 아닌 라이브러리 정책입니다. hidMnsStlAmt<N> 으로 가는 마지막 단계는 보호돼 있습니다.
    return seat_total


@_preserve_read_raw
def parse_reservation_hold_response(
    raw: Mapping[str, object],
) -> ReservationHoldResponse:
    """여정·정산값은 엄격히 검사하되 성공 여부는 재검사하지 않습니다. 직접 호출자는 str_result·h_msg_cd 를 확인하고, 파싱 실패만 보고 다시 요청하지 마십시오 — 예약이
    이미 생성됐을 수 있습니다."""
    copied = _response_mapping(raw)
    journeys_container = copied.get("jrny_infos")
    journey_rows: list[object]
    if journeys_container is None:
        journey_rows = []
    elif _is_mapping(journeys_container):
        value = journeys_container.get("jrny_info")
        if value is None:
            journey_rows = []
        elif _is_list(value):
            journey_rows = value
        else:
            raise KorailProtocolError("KORAIL reservation jrny_infos.jrny_info must be a list or null")
    else:
        raise KorailProtocolError("KORAIL reservation jrny_infos must be an object or null")

    journeys: list[ReservationJourney] = []
    for value in journey_rows:
        row = dict(_row(value, "reservation journey"))
        journeys.append(wire_model(ReservationJourney, row, "reservation journey", raw=row))
    return wire_model(
        ReservationHoldResponse,
        copied,
        "reservation",
        received_amount=_received_amount(copied, [journey.raw for journey in journeys]),
        journeys=tuple(journeys),
        passengers=_reservation_passengers(copied),
        **_response_fields(copied),
    )


@_preserve_read_raw
def parse_existing_reservation_hold_response(
    raw: Mapping[str, object],
    *,
    pnr_no: str,
) -> ReservationHoldResponse:
    """예약 상세 원문을 카드 결제용 홀드로 읽습니다. 검증 실패 시 값을 추측하지 않습니다.

    실서버 상세가 생략한 h_payment_flg 는 누락을 보존하고 명시된 값만 Y 인지 검사합니다. 예약 생성 응답 파서의 관용 규칙은 그대로입니다.
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
        if not _is_list(seats) or not seats:
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


@_preserve_read_raw
def parse_cart_add_response(raw: Mapping[str, object]) -> CartAddResponse:
    data = _response_mapping(raw)
    return CartAddResponse(
        **_response_fields(data),
        discount_additions=wire_models(
            CartDiscountAddition,
            _nested_rows(data, "psgDiscAdd_infos", "psgDiscAdd_info"),
            "cart discount addition",
        ),
    )
