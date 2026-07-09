import httpx

from .config import KorailConfig
from .crypto import generate_sid
from .http import KorailHttpClient
from .models import BaseKorailResponse, KorailSession, TrainSearchQuery, TrainSearchResult, TrainSummary
from .session import KorailSessionClient


class KorailClient:
    def __init__(self, config: KorailConfig | None = None, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        self.session = KorailSessionClient(self.http)

    def close(self) -> None:
        self.http.close()

    def login(self, member_no: str, password: str, *, input_flag: str = "2") -> KorailSession:
        return self.session.login(member_no, password, input_flag=input_flag)

    def clear_session(self) -> None:
        self.session.clear_session()

    def logout(self) -> None:
        self.clear_session()

    def get_common_code(self, code: str = "") -> BaseKorailResponse:
        return self.http.post_form("/classes/com.korail.mobile.common.code.do", {"code": code}, raise_on_fail=False)

    def get_station_info(self, device: str = "AD") -> BaseKorailResponse:
        return self.http.get_json(
            "/classes/com.korail.mobile.common.stationinfo",
            {"Device": device},
            include_common=True,
            raise_on_fail=False,
        )

    def get_station_data(self) -> BaseKorailResponse:
        return self.http.get_json(
            "/classes/com.korail.mobile.common.stationdata",
            include_common=True,
            raise_on_fail=False,
        )

    def get_train_calendar(self) -> BaseKorailResponse:
        return self.http.get_json(
            "/classes/com.korail.mobile.schedule.runDt",
            include_common=True,
            raise_on_fail=False,
        )

    def search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
        response = self.http.post_form(
            "/classes/com.korail.mobile.seatMovie.ScheduleView",
            {
                "Sid": generate_sid(),
                "txtMenuId": "11",
                "radJobId": "1",
                "selGoTrain": query.train_group_code,
                "txtTrnGpCd": query.train_group_code,
                "txtGoTrnNo": "",
                "txtGoStart": query.departure_station_code,
                "txtGoEnd": query.arrival_station_code,
                "txtGoAbrdDt": query.departure_date,
                "txtGoHour": query.departure_time,
                "txtPsgFlg_1": str(query.passengers),
                "txtPsgFlg_2": "0",
                "txtPsgFlg_3": "0",
                "txtPsgFlg_4": "0",
                "txtPsgFlg_5": "0",
                "txtSeatAttCd_2": "000",
                "txtSeatAttCd_3": "000",
                "txtSeatAttCd_4": "015",
                "txtJobDv": "",
                "etrPath": "",
                "srtCheckYn": "Y" if query.include_srt else "N",
            },
            raise_on_fail=False,
        )
        rows = response.raw.get("trn_infos") or response.raw.get("trnInfos") or []
        trains = [TrainSummary.from_raw(row) for row in rows if isinstance(row, dict)]
        return TrainSearchResult(trains=trains, response=response, raw=response.raw)

    def get_train_schedule(self, run_date: str, train_no: str) -> BaseKorailResponse:
        return self.http.post_form(
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
            {"runDt": run_date, "trnNo": train_no},
            include_common=False,
            raise_on_fail=False,
        )

    def get_transfer_stations(self, departure_station_code: str, arrival_station_code: str) -> BaseKorailResponse:
        return self.http.post_form(
            "/classes/com.korail.mobile.qry.chtnStn.do",
            {"dptRsStnCd": departure_station_code, "arvRsStnCd": arrival_station_code},
            raise_on_fail=False,
        )

    def get_ticket_list(self, page_no: int = 0) -> BaseKorailResponse:
        return self.http.post_form(
            "/classes/com.korail.mobile.myTicket.MyTicketList",
            {"txtIndex": str(page_no), "h_page_no": str(page_no)},
            raise_on_fail=False,
        )
