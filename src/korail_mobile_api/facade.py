# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""일상적인 조회·예약 흐름을 기존 KorailClient 위에 조합한 간편 API."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from difflib import get_close_matches
from types import TracebackType
from typing import Literal

import httpx

from ._core.cleanup import _close_connections
from ._core.validation import _optional_text, _passenger_count, _required_text
from ._domains.airport_bus.forms import AirportBusScheduleQuery, AirportBusSeatInventoryQuery
from ._domains.airport_bus.models import (
    AIRPORT_BUS_ROOM_CLASS_CODE,
    AIRPORT_BUS_SEAT_ATTRIBUTE_CODE,
    AirportBusSchedule,
    AirportBusScheduleResponse,
    AirportBusSeatInventoryResponse,
    AirportBusStop,
)
from ._domains.airport_bus.parsers import parse_limousine_stops
from ._domains.common.models import BaseKorailResponse, KorailSession, KorailStation
from ._domains.payments.forms import CardPayment, PaidTicket, RefundCompanion
from ._domains.payments.models import (
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketResponse,
    ReservationPaymentResponse,
)
from ._domains.reservations.forms import KorailPassengerCounts, TicketReservationDetailRequest
from ._domains.reservations.models import (
    ReservationHistoryResponse,
    ReservationHoldResponse,
    TicketReservationDetailResponse,
)
from ._domains.tickets.forms import (
    KorailMileageLedger,
    KorailMileageMovement,
    MileageHistoryRequest,
    OriginalTicketReference,
)
from ._domains.tickets.models import DiscountCouponListResponse, MileageHistoryResponse, TicketListResponse
from ._domains.trains.models import (
    TrainSearchContinuation,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
    _train_datetime,
)
from .client import KorailClient
from .config import KorailConfig
from .constants import KorailLoginInputFlag, KorailReservationJobType, KorailReserveOption, KorailSeatClass
from .errors import KorailInvalidInputError, KorailNoResultsError

KST = timezone(timedelta(hours=9))
_PAST_TOLERANCE = timedelta(minutes=1)


def _departure_moment(depart_after: datetime | None, *, allow_past: bool = False) -> datetime:
    moment = depart_after if depart_after is not None else datetime.now(KST)
    if not isinstance(moment, datetime):
        raise TypeError("depart_after must be a datetime")
    moment = moment.replace(tzinfo=KST) if moment.tzinfo is None else moment.astimezone(KST)
    if not allow_past and moment < datetime.now(KST) - _PAST_TOLERANCE:
        raise KorailInvalidInputError("이미 지난 출발 시각입니다")
    return moment


class StationResource:
    """역 목록을 클라이언트 수명 동안 캐시하고 이름을 검증합니다."""

    def __init__(self, client: KorailClient) -> None:
        self._client = client

    def all(self, *, refresh: bool = False) -> tuple[KorailStation, ...]:
        """역 목록을 반환합니다. 처음 한 번 또는 ``refresh=True`` 일 때만 서버에서 읽습니다."""
        return self._client._cached_station_data(refresh=refresh).stations

    def find(self, reference: str) -> KorailStation | None:
        """이름이나 코드가 같은 역을 반환하고, 없으면 ``None`` 입니다."""
        value = reference.strip()
        if not value:
            return None
        return next((station for station in self.all() if value in (station.name, station.code)), None)

    def names(self) -> set[str]:
        """캐시된 역 이름 집합의 복사본을 반환합니다."""
        return {station.name for station in self.all()}

    def ensure_exists(self, *references: str) -> None:
        """모든 참조가 캐시된 역 이름이나 코드인지 확인하고, 아니면 ``KorailInvalidInputError`` 를 발생시킵니다."""
        stations = self.all()
        names = {station.name for station in stations}
        codes = {station.code for station in stations}
        for reference in references:
            value = reference.strip()
            if value in names or value in codes:
                continue
            suggestions = get_close_matches(value, sorted(names), n=3)
            hint = f"; 가까운 역: {', '.join(suggestions)}" if suggestions else ""
            raise KorailInvalidInputError(f"역을 찾을 수 없습니다: {reference!r}{hint}")


class TrainResource:
    """KST ``datetime``을 기존 열차 조회 조건으로 바꿉니다."""

    def __init__(self, client: KorailClient, stations: StationResource, *, validate_stations: bool) -> None:
        self._client = client
        self._stations = stations
        self._validate_stations = validate_stations

    def search(
        self,
        departure: str,
        arrival: str,
        *,
        depart_after: datetime | None = None,
        passengers: KorailPassengerCounts | None = None,
        train_group_code: str = "109",
        include_srt: bool = False,
        include_nearby_stations: bool = False,
        peak_season: bool = False,
        continuation: TrainSearchContinuation | None = None,
        include_no_seats: bool = True,
        include_waiting_list: bool = False,
    ) -> TrainSearchResult:
        """KST 출발 시각 이후의 직통 열차 한 페이지를 조회합니다. 결과의 ``next_page()``로 이어서 조회하세요."""
        if type(include_no_seats) is not bool or type(include_waiting_list) is not bool:
            raise TypeError("include_no_seats and include_waiting_list must be bool")
        # 다음 페이지는 첫 페이지와 같은 조건이어야 하므로 시각을 다시 읽지 않고 지난 시각도 허용합니다.
        if continuation is not None and depart_after is None:
            raise KorailInvalidInputError("continuation needs the depart_after of the first page")
        moment = _departure_moment(depart_after, allow_past=continuation is not None)
        query = self._query(
            departure,
            arrival,
            moment,
            passengers,
            train_group_code,
            include_srt=include_srt,
            include_nearby_stations=include_nearby_stations,
        )
        result = self._client.search_trains(query, peak_season=peak_season, continuation=continuation)
        return self._filter(
            result, include_no_seats=include_no_seats, include_waiting_list=include_waiting_list
        )

    def _query(
        self,
        departure: str,
        arrival: str,
        moment: datetime,
        passengers: KorailPassengerCounts | None,
        train_group_code: str,
        *,
        include_srt: bool,
        include_nearby_stations: bool,
    ) -> TrainSearchQuery:
        counts = passengers if passengers is not None else KorailPassengerCounts()
        if not isinstance(counts, KorailPassengerCounts):
            raise TypeError("passengers must be KorailPassengerCounts")
        if self._validate_stations:
            self._stations.ensure_exists(departure, arrival)
        return TrainSearchQuery(
            departure_station=departure,
            arrival_station=arrival,
            departure_date=moment.strftime("%Y%m%d"),
            departure_time=moment.strftime("%H%M%S"),
            passengers=counts.adult,
            teenager_passengers=counts.teenager,
            child_passengers=counts.child,
            infant_passengers=counts.infant,
            senior_passengers=counts.senior,
            high_disability_passengers=counts.severe_disability,
            low_disability_passengers=counts.mild_disability,
            guide_dog_passengers=counts.guide_dog,
            train_group_code=train_group_code,
            include_srt=include_srt,
            include_nearby_stations=include_nearby_stations,
        )

    @staticmethod
    def _filter(
        result: TrainSearchResult, *, include_no_seats: bool, include_waiting_list: bool
    ) -> TrainSearchResult:
        if include_no_seats:
            return result
        return replace(
            result,
            trains=[
                train
                for train in result.trains
                if train.has_seat() or (include_waiting_list and train.has_waiting_list())
            ],
            unfiltered_trains=result.trains,
        )

    def iter_search(
        self,
        departure: str,
        arrival: str,
        *,
        max_pages: int,
        depart_after: datetime | None = None,
        passengers: KorailPassengerCounts | None = None,
        train_group_code: str = "109",
        include_srt: bool = False,
        include_nearby_stations: bool = False,
        peak_season: bool = False,
        include_no_seats: bool = True,
        include_waiting_list: bool = False,
    ) -> Iterator[TrainSummary]:
        """직통 검색을 순회할 때 최대 ``max_pages``(1~20) 페이지까지 이어 읽으며 중복 열차를 제외합니다."""
        if type(max_pages) is not int or not 1 <= max_pages <= 20:
            raise KorailInvalidInputError("max_pages must be an integer from 1 through 20")
        if type(include_no_seats) is not bool or type(include_waiting_list) is not bool:
            raise TypeError("include_no_seats and include_waiting_list must be bool")
        moment = _departure_moment(depart_after)
        query = self._query(
            departure,
            arrival,
            moment,
            passengers,
            train_group_code,
            include_srt=include_srt,
            include_nearby_stations=include_nearby_stations,
        )
        seen: set[tuple[str | None, ...]] = set()
        cursors: set[TrainSearchContinuation] = set()
        continuation = None
        for page in range(max_pages):
            try:
                result = self._filter(
                    self._client.search_trains(query, peak_season=peak_season, continuation=continuation),
                    include_no_seats=include_no_seats,
                    include_waiting_list=include_waiting_list,
                )
            except KorailNoResultsError:
                if page == 0:
                    raise
                return
            source = result.unfiltered_trains if result.unfiltered_trains is not None else result.trains
            identities = {self._identity(train) for train in source}
            if not source or (None not in identities and not identities - seen):
                return
            for train in result.trains:
                identity = self._identity(train)
                if identity is None or identity not in seen:
                    if identity is not None:
                        seen.add(identity)
                    yield train
            seen.update(identity for identity in identities if identity is not None)
            if None in identities or page + 1 == max_pages or result.metadata.next_page_flag == "N":
                return
            continuation = result.next_page()
            if continuation is not None:
                if continuation in cursors:
                    return
                cursors.add(continuation)
                continue
            next_query = result.next_query_from_last_departure(query)
            if next_query is None:
                return
            following = _train_datetime(next_query.departure_date, next_query.departure_time)
            if following is None or following.replace(tzinfo=KST) <= moment:
                return
            query = next_query
            moment = following.replace(tzinfo=KST)

    @staticmethod
    def _identity(train: TrainSummary) -> tuple[str | None, ...] | None:
        identity = (
            train.train_no,
            train.departure_date,
            train.departure_time,
            train.departure_station_code or train.departure_station_name,
            train.arrival_station_code or train.arrival_station_name,
            train.run_date,
            train.train_group_code,
            train.train_class_code,
        )
        return identity if all(identity[:5]) else None


class MembershipResource:
    """기존 마일리지·쿠폰 응답을 보존하며 날짜 입력을 단순화합니다."""

    def __init__(self, client: KorailClient) -> None:
        self._client = client

    def mileage(
        self,
        *,
        start_date: date | datetime | None = None,
        end_date: date | datetime | None = None,
        ledger: KorailMileageLedger = "1",
        movement: KorailMileageMovement = "0",
        page_no: int = 1,
    ) -> MileageHistoryResponse:
        """기본 최근 30일의 마일리지 한 페이지입니다. datetime은 KST 날짜로 읽습니다."""
        end = self._date(end_date, datetime.now(KST).date())
        if start_date is None:
            try:
                start = end - timedelta(days=30)
            except OverflowError as error:
                raise KorailInvalidInputError("end_date must allow a 30-day default range") from error
        else:
            start = self._date(start_date, end)
        return self._client.get_mileage_history(
            MileageHistoryRequest(
                start_date=start.isoformat().replace("-", ""),
                end_date=end.isoformat().replace("-", ""),
                ledger=ledger,
                movement=movement,
                page_no=page_no,
            )
        )

    @staticmethod
    def _date(value: date | datetime | None, default: date) -> date:
        if value is None:
            return default
        if isinstance(value, datetime):
            return (value.replace(tzinfo=KST) if value.tzinfo is None else value.astimezone(KST)).date()
        if not isinstance(value, date):
            raise TypeError("start_date and end_date must be date or datetime values")
        return value

    def coupons(self, *, page_no: int = 1, pnr_no: str = "") -> DiscountCouponListResponse:
        """쿠폰 한 페이지를 조회합니다. 목록·페이지 정보·원문을 그대로 반환합니다."""
        return self._client.list_discount_coupons(page_no=page_no, pnr_no=pnr_no)


class AirportBusResource:
    """기존 공통 코드·공항버스 조회를 이름 기반으로 조합합니다. 예약은 하지 않습니다."""

    def __init__(self, client: KorailClient) -> None:
        self._client = client
        self._stops: tuple[AirportBusStop, ...] | None = None

    def stops(self, *, refresh: bool = False) -> tuple[AirportBusStop, ...]:
        """정류장 이름·코드 목록을 한 번 조회해 캐시합니다. 잘못된 응답은 캐시하지 않습니다."""
        if self._stops is None or refresh:
            response = self._client.get_common_codes(["app.limousine.stationNm", "app.limousine.stationCd"])
            self._stops = parse_limousine_stops(response.raw)
        return self._stops

    def search(
        self,
        departure: str,
        arrival: str,
        *,
        service_code: str,
        depart_after: datetime | None = None,
        reservation_sale_division_code: str = "",
    ) -> AirportBusScheduleResponse:
        """이름 또는 코드로 운행 편 한 페이지를 조회합니다. 운행 그룹은 명시적으로 받습니다."""
        moment = _departure_moment(depart_after)
        _required_text(service_code, "service_code")
        _optional_text(reservation_sale_division_code, "reservation_sale_division_code")
        references = (
            _required_text(departure, "departure").strip(),
            _required_text(arrival, "arrival").strip(),
        )
        codes: list[str] = []
        stops = self.stops()
        for reference in references:
            matches = [stop for stop in stops if reference in (stop.name, stop.code)]
            if not matches:
                raise KorailInvalidInputError(f"공항버스 정류장을 찾을 수 없습니다: {reference!r}")
            if len(matches) != 1:
                raise KorailInvalidInputError(f"공항버스 정류장 이름·코드를 구분할 수 없습니다: {reference!r}")
            codes.append(matches[0].code)
        return self._client.list_airport_bus_schedules(
            AirportBusScheduleQuery(
                departure_date=moment.strftime("%Y%m%d"),
                departure_station_code=codes[0],
                arrival_station_code=codes[1],
                service_code=service_code,
                room_class_code=AIRPORT_BUS_ROOM_CLASS_CODE,
                departure_time=moment.strftime("%H%M%S"),
                train_no="",
                seat_attribute_code=AIRPORT_BUS_SEAT_ATTRIBUTE_CODE,
                reservation_sale_division_code=reservation_sale_division_code,
            )
        )

    def seats(
        self, schedule: AirportBusSchedule, *, passenger_count: int = 1
    ) -> AirportBusSeatInventoryResponse:
        """조회한 편의 식별값으로 좌석 배치를 읽습니다. 필수값이 없으면 요청 전에 거절합니다."""
        if not isinstance(schedule, AirportBusSchedule):
            raise TypeError("schedule must be an AirportBusSchedule")
        _passenger_count(passenger_count, "passenger_count")
        return self._client.get_airport_bus_seat_inventory(
            AirportBusSeatInventoryQuery.from_schedule(schedule, passenger_count=passenger_count)
        )


class ReservationResource:
    """기존 예약 API의 결과와 안전 검사를 유지하는 짧은 진입점입니다."""

    def __init__(self, client: KorailClient) -> None:
        self._client = client

    def create(
        self,
        train: TrainSummary,
        *,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass | None = None,
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
        option: KorailReserveOption | None = None,
    ) -> ReservationHoldResponse:
        """실제 미결제 홀드를 만듭니다(기본 일반실, ``option``은 조회 결과로 객실 선택).

        결제·취소는 호출자 몫이며, 실패해도 다른 객실이나 예약대기로 다시 보내지 않습니다."""
        if option is not None:
            if not isinstance(option, KorailReserveOption):
                raise TypeError("option must be KorailReserveOption")
            if seat_class is not None or job_type is not KorailReservationJobType.IMMEDIATE:
                raise KorailInvalidInputError("option requires immediate reservation without seat_class")
            if not isinstance(train, TrainSummary):
                raise TypeError("train must be TrainSummary")
            candidates = {
                KorailReserveOption.GENERAL_FIRST: (KorailSeatClass.GENERAL, KorailSeatClass.SPECIAL),
                KorailReserveOption.SPECIAL_FIRST: (KorailSeatClass.SPECIAL, KorailSeatClass.GENERAL),
                KorailReserveOption.GENERAL_ONLY: (KorailSeatClass.GENERAL,),
                KorailReserveOption.SPECIAL_ONLY: (KorailSeatClass.SPECIAL,),
            }[option]
            seat_class = next(
                (
                    cabin
                    for cabin in candidates
                    if (
                        train.has_general_seat()
                        if cabin is KorailSeatClass.GENERAL
                        else train.has_special_seat()
                    )
                ),
                None,
            )
            if seat_class is None:
                raise KorailInvalidInputError("KORAIL reservation option requires an evidenced available seat")
        selected = KorailSeatClass.GENERAL if seat_class is None else seat_class
        return self._client.reserve(train, passengers=passengers, seat_class=selected, job_type=job_type)

    def get(self, pnr_no: str) -> ReservationHoldResponse:
        """PNR로 기존 예약을 한 번 조회해 결제용 홀드를 반환합니다."""
        return self._client.get_reservation_hold(pnr_no)

    def detail(self, hold: ReservationHoldResponse | str) -> TicketReservationDetailResponse:
        """이미 생성된 예약을 별도 조회합니다. 생성 직후 자동 재조회하지 않습니다."""
        pnr_no = hold.pnr_no if isinstance(hold, ReservationHoldResponse) else hold
        if not pnr_no:
            raise KorailInvalidInputError("a successful hold with a PNR is required")
        return self._client.get_ticket_reservation_detail(TicketReservationDetailRequest(pnr_no=pnr_no))

    def all(self) -> ReservationHistoryResponse:
        """기존 예약 이력 응답을 보존합니다."""
        return self._client.list_reservations()

    def cancel(self, hold: ReservationHoldResponse) -> BaseKorailResponse:
        """미결제 홀드의 가능 여부를 확인한 뒤 취소합니다."""
        return self._client.cancel_unpaid_hold(hold)

    def pay(self, hold: ReservationHoldResponse, card: CardPayment) -> ReservationPaymentResponse:
        """카드를 실제 청구합니다. 서버 거절은 결과의 ``str_result``로 확인하세요."""
        return self._client.pay_with_card(hold, card)


class TicketResource:
    """승차권 조회·환불의 기존 사전 확인 절차를 노출합니다."""

    def __init__(self, client: KorailClient) -> None:
        self._client = client

    def all(
        self,
        page_no: int = 1,
        *,
        mode: Literal["1", "2"] = "1",
        boarding_date_from: str = "",
        boarding_date_to: str = "",
    ) -> TicketListResponse:
        """승차권 목록 한 페이지를 읽습니다(mode 1 은 현재표, 2 는 승차일 범위의 이력)."""
        return self._client.list_tickets(
            page_no, mode=mode, boarding_date_from=boarding_date_from, boarding_date_to=boarding_date_to
        )

    def detail(
        self, ticket: OriginalTicketReference, *, from_purchase_history: bool = False
    ) -> RefundTicketDetailResponse:
        """원표 식별자로 승차권 한 장의 여정·좌석·운임 상세를 조회합니다."""
        return self._client.get_refund_ticket_detail(ticket, from_purchase_history=from_purchase_history)

    def refund_quote(
        self,
        ticket: OriginalTicketReference,
        *,
        companion: RefundCompanion = RefundCompanion(),
    ) -> RefundCommissionResponse:
        """실제 환불 없이 원표·동반자의 수수료를 조회하고 결과에 로컬 연결합니다."""
        return self._client.get_refund_fee(ticket, companion)

    def refund(
        self,
        ticket: PaidTicket,
        *,
        commission: RefundCommissionResponse,
    ) -> RefundTicketResponse:
        """수수료 성공 응답을 받은 뒤 승차권 한 장을 실제 환불합니다."""
        return self._client.refund(ticket, commission=commission)


class Korail:
    """일상적인 조회·예약 리소스를 제공하는 선택적 간편 클라이언트입니다.

    ``client`` 속성에서 전체 ``KorailClient`` API에 접근할 수 있습니다.
    컨텍스트 종료는 연결만 닫으며 서버 로그아웃은 별도로 호출해야 합니다.
    """

    def __init__(
        self,
        config: KorailConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        validate_stations: bool = True,
    ) -> None:
        self.client = KorailClient(config, transport=transport)
        self.stations = StationResource(self.client)
        self.trains = TrainResource(self.client, self.stations, validate_stations=validate_stations)
        self.reservations = ReservationResource(self.client)
        self.tickets = TicketResource(self.client)
        self.membership = MembershipResource(self.client)
        self.airport_bus = AirportBusResource(self.client)

    @classmethod
    def logged_in(
        cls,
        member_no: str,
        password: str,
        *,
        config: KorailConfig | None = None,
        transport: httpx.BaseTransport | None = None,
        validate_stations: bool = True,
    ) -> Korail:
        """로그인 실패 시 연결을 닫고 원래 예외를 다시 발생시킵니다."""
        korail = cls(config, transport=transport, validate_stations=validate_stations)
        try:
            korail.login(member_no, password)
        except BaseException as error:
            _close_connections(korail.close, primary=error)
            raise
        return korail

    def __enter__(self) -> Korail:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        _close_connections(self.close, primary=exc)

    def login(
        self,
        member_no: str,
        password: str,
        *,
        input_flag: KorailLoginInputFlag | None = None,
        check_valid_pw: Literal["Y", "N"] = "Y",
        cust_id: str | None = "",
        etr_path: str | None = "",
    ) -> KorailSession:
        """``KorailClient.login``과 같은 옵션으로 로그인합니다."""
        return self.client.login(
            member_no,
            password,
            input_flag=input_flag,
            check_valid_pw=check_valid_pw,
            cust_id=cust_id,
            etr_path=etr_path,
        )

    def logout(self) -> None:
        """``KorailClient.logout`` 을 호출합니다."""
        self.client.logout()

    def close(self) -> None:
        """``KorailClient.close`` 를 호출합니다."""
        self.client.close()
