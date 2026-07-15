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
    MaasMenuListResponse,
    NoticeResponse,
    SeatCarListResponse,
    SeatInventoryResponse,
    StationDataResponse,
    StationInfoResponse,
    TrainCalendarResponse,
    TrainSearchQuery,
    TrainSearchResult,
    TrainScheduleResponse,
    TrainSummary,
    TransferStationListResponse,
    UuidResponse,
)
from .parsers import (
    parse_app_data_response,
    parse_maas_menu_list_response,
    parse_notice_response,
    parse_seat_car_list_response,
    parse_seat_inventory_response,
    parse_station_data_response,
    parse_station_info_response,
    parse_station_name_map,
    parse_train_calendar_response,
    parse_train_rows,
    parse_train_schedule_response,
    parse_train_search_metadata,
    parse_transfer_station_list_response,
    parse_uuid_response,
    resolve_station_name,
)
from .payloads import (
    build_cache_query,
    build_common_code_form,
    build_maas_menu_form,
    build_maas_station_form,
    build_seat_car_form,
    build_seat_inventory_form,
    build_ticket_list_form,
    build_train_schedule_form,
    build_train_search_form,
    validate_seat_inventory_inputs,
)
from .read_models import (
    CartListResponse,
    CommuterKindMenuResponse,
    CrewRequestListResponse,
    DelayDiscountTicketListResponse,
    DepositBankListResponse,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    MergeSeatsInquiryResponse,
    PassAvailabilityResponse,
    PassMenuResponse,
    ProductDetailResponse,
    ProductReservationListResponse,
    ReservationHistoryResponse,
    SeatAssignmentScheduleResponse,
    ServiceStatusResponse,
    TicketReceiptResponse,
    TripMenuResponse,
)
from .read_payloads import (
    build_cart_list_form,
    build_commuter_kind_menu_query,
    build_crew_request_list_query,
    build_delay_discount_ticket_form,
    build_discount_coupon_form,
    build_free_seat_car_form,
    build_guide_seat_condition_form,
    build_merge_seats_inquiry_form,
    build_pass_availability_form,
    build_pass_menu_form,
    build_product_detail_query,
    build_product_reservations_query,
    build_service_status_query,
    build_seat_assignment_schedule_form,
    build_ticket_receipt_form,
    build_trip_menu_form,
    FreeSeatCarRequest,
    GuideSeatConditionRequest,
    MergeSeatsInquiryRequest,
    SeatAssignmentScheduleRequest,
)
from .read_parsers import (
    parse_cart_list_response,
    parse_commuter_kind_menu_response,
    parse_crew_request_list_response,
    parse_delay_discount_ticket_response,
    parse_deposit_bank_response,
    parse_discount_coupon_response,
    parse_free_seat_car_response,
    parse_guide_seat_condition_response,
    parse_merge_seats_inquiry_response,
    parse_pass_availability_response,
    parse_pass_menu_response,
    parse_product_detail_response,
    parse_product_reservation_list_response,
    parse_reservation_history_response,
    parse_service_status_response,
    parse_seat_assignment_schedule_response,
    parse_ticket_receipt_response,
    parse_trip_menu_response,
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

    def _require_session(self) -> None:
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL account read requires an authenticated session"
            )

    def get_seat_cars(
        self,
        train: TrainSummary,
        *,
        passenger_count: int = 1,
    ) -> SeatCarListResponse:
        self._require_session()
        validate_seat_inventory_inputs(train, passenger_count)
        form = build_seat_car_form(
            self.config,
            train,
            passenger_count=passenger_count,
            sid=generate_sid(),
        )
        return self._run_read(
            lambda: parse_seat_car_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.TrainResearch",
                    form,
                    include_common=False,
                    include_dynapath=False,
                )
            )
        )

    def get_seat_inventory(
        self,
        train: TrainSummary,
        car_no: int,
        *,
        passenger_count: int = 1,
    ) -> SeatInventoryResponse:
        self._require_session()
        validate_seat_inventory_inputs(
            train,
            passenger_count,
            car_no=car_no,
        )
        form = build_seat_inventory_form(
            self.config,
            train,
            car_no,
            passenger_count=passenger_count,
            sid=generate_sid(),
        )
        return self._run_read(
            lambda: parse_seat_inventory_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.TResidualSeatsResearch.do",
                    form,
                    include_common=False,
                    include_dynapath=False,
                )
            )
        )

    def get_service_status(
        self,
        timestamp_ms: int | None = None,
    ) -> ServiceStatusResponse:
        query = build_service_status_query(timestamp_ms)
        return self._run_read(
            lambda: parse_service_status_response(
                self.http.get_json(
                    "/file/CACHE/MobileService.cache",
                    query,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_cart_list(
        self,
        pnr_no: str = "",
        additional_service_request_no: str = "",
    ) -> CartListResponse:
        self._require_session()
        form = build_cart_list_form(
            pnr_no,
            additional_service_request_no,
        )
        return self._run_read(
            lambda: parse_cart_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.cart.showCartList",
                    form,
                    include_dynapath=False,
                    require_envelope=False,
                ).raw
            )
        )

    def get_deposit_banks(self) -> DepositBankListResponse:
        self._require_session()
        return self._run_read(
            lambda: parse_deposit_bank_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.dlay.dptnBank.do",
                    include_dynapath=False,
                ).raw
            )
        )

    def get_delay_discount_tickets(
        self,
        departure_date_to: str,
    ) -> DelayDiscountTicketListResponse:
        self._require_session()
        form = build_delay_discount_ticket_form(departure_date_to)
        return self._run_read(
            lambda: parse_delay_discount_ticket_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.passCard.DelayDiscountView",
                    form,
                    include_dynapath=False,
                    require_envelope=False,
                ).raw
            )
        )

    def get_discount_coupons(
        self,
        page_no: int = 1,
        pnr_no: str = "",
    ) -> DiscountCouponListResponse:
        self._require_session()
        form = build_discount_coupon_form(page_no, pnr_no)
        return self._run_read(
            lambda: parse_discount_coupon_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.passCard.CouponView",
                    form,
                    include_dynapath=False,
                    raise_on_fail=False,
                ).raw
            )
        )

    def get_pass_available_dates(
        self,
        kind_code: str,
        period_code: str,
        age_code: str,
    ) -> PassAvailabilityResponse:
        form = build_pass_availability_form(
            kind_code,
            period_code,
            age_code,
        )
        return self._run_read(
            lambda: parse_pass_availability_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.pass.passInfoList",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_trip_menu(self) -> TripMenuResponse:
        self._require_session()
        form = build_trip_menu_form(self.config)
        return self._run_read(
            lambda: parse_trip_menu_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.pass.trGdMenuLt.do",
                    form,
                    include_common=False,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_pass_menu(self, menu_no: str) -> PassMenuResponse:
        form = build_pass_menu_form(menu_no)
        return self._run_read(
            lambda: parse_pass_menu_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.pass.passMenu.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_crew_request_list(
        self,
        query_division_code: str,
    ) -> CrewRequestListResponse:
        query = build_crew_request_list_query(query_division_code)
        return self._run_read(
            lambda: parse_crew_request_list_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.push.crwCallRq.do",
                    query,
                    include_common=True,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_commuter_kind_menu(
        self,
        commuter_kind_code: str,
    ) -> CommuterKindMenuResponse:
        query = build_commuter_kind_menu_query(commuter_kind_code)
        return self._run_read(
            lambda: parse_commuter_kind_menu_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.push.cmtrKnd.do",
                    query,
                    include_common=True,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_product_reservations(
        self,
        page_no: int = 1,
        page_size: int = 20,
    ) -> ProductReservationListResponse:
        self._require_session()
        query = build_product_reservations_query(page_no, page_size)
        return self._run_read(
            lambda: parse_product_reservation_list_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.product.ReservationList",
                    query,
                    include_common=True,
                    include_dynapath=False,
                    require_envelope=False,
                ).raw
            )
        )

    def get_product_detail(
        self,
        reservation_no: str,
        reservation_sequence: str,
    ) -> ProductDetailResponse:
        self._require_session()
        query = build_product_detail_query(
            reservation_no,
            reservation_sequence,
        )
        return self._run_read(
            lambda: parse_product_detail_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.product.ReservationDetail",
                    query,
                    include_common=True,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_ticket_receipt(
        self,
        sale_date: str,
        window_no: str,
        sale_sequence: str,
        return_password: str,
    ) -> TicketReceiptResponse:
        self._require_session()
        form = build_ticket_receipt_form(
            sale_date,
            window_no,
            sale_sequence,
            return_password,
        )
        return self._run_read(
            lambda: parse_ticket_receipt_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.receipt.ReceiptInfo",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_reservation_history(self) -> ReservationHistoryResponse:
        self._require_session()
        return self._run_read(
            lambda: parse_reservation_history_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.reservation.ReservationView",
                    include_common=True,
                    include_dynapath=False,
                    raise_on_fail=False,
                ).raw
            )
        )

    def get_free_seat_car_info(
        self,
        request: FreeSeatCarRequest,
    ) -> FreeSeatCarResponse:
        form = build_free_seat_car_form(request)
        return self._run_read(
            lambda: parse_free_seat_car_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.trn.fresScar.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_guide_seat_condition(
        self,
        request: GuideSeatConditionRequest,
    ) -> GuideSeatConditionResponse:
        form = build_guide_seat_condition_form(request)
        return self._run_read(
            lambda: parse_guide_seat_condition_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.reservation.guideSeatCnd.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_seat_assignment_schedule(
        self,
        request: SeatAssignmentScheduleRequest,
    ) -> SeatAssignmentScheduleResponse:
        form = build_seat_assignment_schedule_form(request)
        return self._run_read(
            lambda: parse_seat_assignment_schedule_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.assignScheduleView.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_merge_seats_inquiry(
        self,
        request: MergeSeatsInquiryRequest,
    ) -> MergeSeatsInquiryResponse:
        form = build_merge_seats_inquiry_form(request)
        return self._run_read(
            lambda: parse_merge_seats_inquiry_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.mergeSeatsC.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

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
                    include_dynapath=False,
                    require_envelope=False,
                )
            )
        )

    def get_maas_menu_list(self) -> MaasMenuListResponse:
        form = build_maas_menu_form(self.config)
        return self._run_read(
            lambda: parse_maas_menu_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.copt.gdMenuLt.do",
                    form,
                    include_common=False,
                    include_dynapath=False,
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
                    include_dynapath=False,
                    require_envelope=False,
                )
            )
        )

    def get_station_info(self, device: str = "AD") -> StationInfoResponse:
        return self._run_read(
            lambda: parse_station_info_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.common.stationinfo",
                    {"Device": device},
                    require_envelope=False,
                )
            )
        )

    def get_station_data(self) -> StationDataResponse:
        return self._run_read(
            lambda: parse_station_data_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.common.stationdata",
                    require_envelope=False,
                )
            )
        )

    def get_train_calendar(self) -> TrainCalendarResponse:
        return self._run_read(
            lambda: parse_train_calendar_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.schedule.runDt"
                )
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
            metadata=parse_train_search_metadata(response.raw),
        )

    def _resolve_station_reference(self, reference: str) -> str:
        if not reference.strip().isdigit():
            return resolve_station_name(reference, {})
        if self._station_names is None:
            self._station_names = parse_station_name_map(
                self.get_station_data().raw
            )
        return resolve_station_name(reference, self._station_names)

    def get_train_schedule(
        self,
        run_date: str,
        train_no: str,
    ) -> TrainScheduleResponse:
        return self._run_read(
            lambda: parse_train_schedule_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.actualTrainSchedule.do",
                    build_train_schedule_form(
                        self.config,
                        run_date,
                        train_no,
                    ),
                    include_common=False,
                )
            )
        )

    def get_transfer_stations(
        self,
        departure_station_code: str,
        arrival_station_code: str,
    ) -> TransferStationListResponse:
        return self._run_read(
            lambda: parse_transfer_station_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.qry.chtnStn.do",
                    {
                        "dptRsStnCd": departure_station_code,
                        "arvRsStnCd": arrival_station_code,
                    },
                )
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
