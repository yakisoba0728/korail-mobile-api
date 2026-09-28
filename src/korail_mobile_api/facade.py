# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""일상적인 조회·예약 흐름을 기존 KorailClient 위에 조합한 간편 API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from difflib import get_close_matches
from types import TracebackType

import httpx

from .client import KorailClient
from .config import KorailConfig
from .constants import KorailReservationJobType, KorailSeatClass
from .models import (
    BaseKorailResponse,
    KorailSession,
    KorailStation,
    TrainSearchContinuation,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
)
from .mutation_models import (
    CardPayment,
    KorailPassengerCounts,
    PaidTicket,
    RefundTicketResponse,
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from .read_models import (
    RefundCommissionResponse,
    ReservationHistoryResponse,
    TicketListResponse,
    TicketReservationDetailResponse,
)
from .read_payloads import OriginalTicketReference, TicketReservationDetailRequest

KST = timezone(timedelta(hours=9))
_PAST_TOLERANCE = timedelta(minutes=1)


class StationResource:
    """역 목록을 클라이언트 수명 동안 캐시하고 이름을 검증합니다."""

    def __init__(self, client: KorailClient) -> None:
        self._client = client
        self._cache: tuple[KorailStation, ...] | None = None

    def all(self, *, refresh: bool = False) -> tuple[KorailStation, ...]:
        if self._cache is None or refresh:
            self._cache = self._client.get_station_data().stations
        return self._cache

    def find(self, reference: str) -> KorailStation | None:
        value = reference.strip()
        if not value:
            return None
        return next((station for station in self.all() if value in (station.name, station.code)), None)

    def ensure_exists(self, *references: str) -> None:
        stations = self.all()
        names = {station.name for station in stations}
        codes = {station.code for station in stations}
        for reference in references:
            value = reference.strip()
            if value in names or value in codes:
                continue
            suggestions = get_close_matches(value, sorted(names), n=3)
            hint = f"; 가까운 역: {', '.join(suggestions)}" if suggestions else ""
            raise ValueError(f"역을 찾을 수 없습니다: {reference!r}{hint}")


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
    ) -> TrainSearchResult:
        """직통 열차 한 페이지를 조회합니다. 결과의 ``next_page()``로 계속 조회하세요.

        시간대가 없는 시각은 KST로 읽고, 시간대가 있으면 KST로 변환합니다.
        과거 시각은 요청 전에 거절합니다. ``passengers``는 기존 예약 입력 모델을
        사용하며 생략하면 성인 한 명입니다.
        """
        moment = depart_after if depart_after is not None else datetime.now(KST)
        if not isinstance(moment, datetime):
            raise TypeError("depart_after must be a datetime")
        moment = moment.replace(tzinfo=KST) if moment.tzinfo is None else moment.astimezone(KST)
        if moment < datetime.now(KST) - _PAST_TOLERANCE:
            raise ValueError("이미 지난 출발 시각입니다")
        if self._validate_stations:
            self._stations.ensure_exists(departure, arrival)
        counts = passengers if passengers is not None else KorailPassengerCounts()
        if not isinstance(counts, KorailPassengerCounts):
            raise TypeError("passengers must be KorailPassengerCounts")
        query = TrainSearchQuery(
            departure_station_code=departure,
            arrival_station_code=arrival,
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
        return self._client.search_trains(query, peak_season=peak_season, continuation=continuation)


class ReservationResource:
    """기존 예약 API의 결과와 안전 검사를 유지하는 짧은 진입점입니다."""

    def __init__(self, client: KorailClient) -> None:
        self._client = client

    def create(
        self,
        train: TrainSummary,
        *,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    ) -> ReservationHoldResponse:
        """실제 미결제 홀드를 만듭니다. 결제 또는 취소는 호출자 책임입니다."""
        return self._client.reserve(train, passengers=passengers, seat_class=seat_class, job_type=job_type)

    def detail(self, hold: ReservationHoldResponse | str) -> TicketReservationDetailResponse:
        """이미 생성된 예약을 별도 조회합니다. 생성 직후 자동 재조회하지 않습니다."""
        pnr_no = hold.pnr_no if isinstance(hold, ReservationHoldResponse) else hold
        if not pnr_no:
            raise ValueError("a successful hold with a PNR is required")
        return self._client.get_ticket_reservation_detail(TicketReservationDetailRequest(pnr_no))

    def all(self) -> ReservationHistoryResponse:
        """기존 예약 이력 응답을 보존합니다."""
        return self._client.get_reservation_history()

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

    def all(self, *, page_no: int = 1) -> TicketListResponse:
        return self._client.get_ticket_list(page_no)

    def refund_fee(self, ticket: OriginalTicketReference) -> RefundCommissionResponse:
        """실제 환불 없이 수수료를 조회합니다."""
        return self._client.get_refund_commission(ticket)

    def refund(
        self,
        ticket: PaidTicket,
        *,
        commission: RefundCommissionResponse,
    ) -> RefundTicketResponse:
        """수수료 성공 응답을 받은 뒤 승차권 한 장을 실제 환불합니다."""
        return self._client.refund(ticket, commission=commission)


class Korail:
    """일상적인 네 리소스를 제공하는 선택적 간편 클라이언트입니다.

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
        except BaseException:
            korail.close()
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
        self.close()

    def login(self, member_no: str, password: str) -> KorailSession:
        return self.client.login(member_no, password)

    def logout(self) -> None:
        self.client.logout()

    def close(self) -> None:
        self.client.close()
