from collections.abc import Callable
from typing import TypeVar

import httpx

from .config import KorailConfig
from .crypto import generate_sid
from .errors import KorailAuthError, KorailSessionExpiredError
from .http import KorailHttpClient
from .models import (
    AppDataResponse,
    BaseKorailResponse,
    KorailSession,
    NoticeResponse,
    StationDataResponse,
    TrainSearchQuery,
    TrainSearchResult,
    UuidResponse,
)
from .parsers import (
    parse_app_data_response,
    parse_notice_response,
    parse_station_data_response,
    parse_station_name_map,
    parse_train_rows,
    parse_uuid_response,
    resolve_station_name,
)
from .payloads import (
    build_cache_query,
    build_common_code_form,
    build_maas_station_form,
    build_ticket_list_form,
    build_train_schedule_form,
    build_train_search_form,
)
from .session import KorailSessionClient

T = TypeVar("T")


class KorailClient:
    def __init__(self, config: KorailConfig | None = None, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        self.session = KorailSessionClient(self.http)
        self._station_names: dict[str, str] | None = None

    def close(self) -> None:
        self.http.close()

    def login(
        self,
        member_no: str,
        password: str,
        *,
        input_flag: str | None = None,
        check_valid_pw: str = "Y",
        cust_id: str | None = "",
        etr_path: str | None = "",
    ) -> KorailSession:
        return self.session.login(
            member_no,
            password,
            input_flag=input_flag,
            check_valid_pw=check_valid_pw,
            cust_id=cust_id,
            etr_path=etr_path,
        )

    def clear_session(self) -> None:
        self.session.clear_session()

    def logout(self) -> None:
        self.clear_session()

    def _run_read(self, operation: Callable[[], T]) -> T:
        try:
            return operation()
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def get_common_code(self, code: str = "") -> BaseKorailResponse:
        return self._run_read(
            lambda: self.http.post_form(
                "/classes/com.korail.mobile.common.code.do",
                build_common_code_form(self.config, code),
                include_common=False,
            )
        )

    def get_app_data(
        self,
        timestamp_ms: int | None = None,
    ) -> AppDataResponse:
        return self._run_read(
            lambda: parse_app_data_response(
                self.http.get_json(
                    "/file/CACHE/prdMobilePlusMain.cache",
                    build_cache_query(timestamp_ms),
                    require_envelope=False,
                )
            )
        )

    def get_notice(
        self,
        timestamp_ms: int | None = None,
    ) -> NoticeResponse:
        return self._run_read(
            lambda: parse_notice_response(
                self.http.get_json(
                    "/file/CACHE/prdMobilePlusNotice.cache",
                    build_cache_query(timestamp_ms),
                    require_envelope=False,
                )
            )
        )

    def get_uuid(self) -> UuidResponse:
        return self._run_read(
            lambda: parse_uuid_response(
                self.http.get_json(
                    "/ebizcross/getUUID.do",
                    require_envelope=False,
                )
            )
        )

    def get_maas_station_data(
        self,
        additional_service_code: str,
    ) -> StationDataResponse:
        form = build_maas_station_form(additional_service_code)
        return self._run_read(
            lambda: parse_station_data_response(
                self.http.post_form(
                    "/ebizmaas/EbizMaasStationList.do",
                    form,
                    include_common=False,
                    require_envelope=False,
                )
            )
        )

    def get_station_info(self, device: str = "AD") -> BaseKorailResponse:
        return self._run_read(
            lambda: self.http.get_json(
                "/classes/com.korail.mobile.common.stationinfo",
                {"Device": device},
                require_envelope=False,
            )
        )

    def get_station_data(self) -> BaseKorailResponse:
        return self._run_read(
            lambda: self.http.get_json(
                "/classes/com.korail.mobile.common.stationdata",
                require_envelope=False,
            )
        )

    def get_train_calendar(self) -> BaseKorailResponse:
        return self._run_read(
            lambda: self.http.get_json(
                "/classes/com.korail.mobile.schedule.runDt"
            )
        )

    def search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
        return self._run_read(lambda: self._search_trains(query))

    def _search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
        departure_name = self._resolve_station_reference(
            query.departure_station_code
        )
        arrival_name = self._resolve_station_reference(
            query.arrival_station_code
        )
        current = self.session.current
        form = build_train_search_form(
            self.config,
            query,
            departure_name=departure_name,
            arrival_name=arrival_name,
            sid=generate_sid(),
            member_card_no=current.member_card_no if current else None,
        )
        response = self.http.post_form(
            "/classes/com.korail.mobile.seatMovie.ScheduleView",
            form,
            include_common=False,
        )
        return TrainSearchResult(
            trains=parse_train_rows(response.raw),
            response=response,
            raw=response.raw,
        )

    def _resolve_station_reference(self, reference: str) -> str:
        if not reference.strip().isdigit():
            return resolve_station_name(reference, {})
        if self._station_names is None:
            self._station_names = parse_station_name_map(
                self.get_station_data().raw
            )
        return resolve_station_name(reference, self._station_names)

    def get_train_schedule(self, run_date: str, train_no: str) -> BaseKorailResponse:
        return self._run_read(
            lambda: self.http.post_form(
                "/classes/com.korail.mobile.research.actualTrainSchedule.do",
                build_train_schedule_form(
                    self.config,
                    run_date,
                    train_no,
                ),
                include_common=False,
            )
        )

    def get_transfer_stations(self, departure_station_code: str, arrival_station_code: str) -> BaseKorailResponse:
        return self._run_read(
            lambda: self.http.post_form(
                "/classes/com.korail.mobile.qry.chtnStn.do",
                {
                    "dptRsStnCd": departure_station_code,
                    "arvRsStnCd": arrival_station_code,
                },
            )
        )

    def get_ticket_list(self, page_no: int = 0) -> BaseKorailResponse:
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL ticket list requires an authenticated session"
            )
        return self._run_read(
            lambda: self.http.post_form(
                "/classes/com.korail.mobile.myTicket.MyTicketList",
                build_ticket_list_form(self.config, page_no),
            )
        )
