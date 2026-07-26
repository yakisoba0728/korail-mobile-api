from collections.abc import Callable, Sequence
from typing import TypeVar

import httpx

from .config import KorailConfig
from .consent import (
    MutationConsent,
    MutationPreview,
    require_mutation_consent,
)
from .constants import KorailReservationJobType, KorailSeatClass
from .crypto import generate_sid
from .errors import (
    KorailAuthError,
    KorailProtocolError,
    KorailSessionExpiredError,
    MutationNotAllowedError,
)
from .mutation_models import (
    CardPayment,
    KorailPassengerCounts,
    KorailSeatAssignment,
    PaidTicket,
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from .mutation_parsers import (
    parse_reservation_hold_response,
    parse_reservation_payment_response,
)
from .mutation_payloads import (
    build_card_payment_form,
    build_refund_form,
    build_reservation_form,
    build_standby_wait_form,
    build_unpaid_reservation_cancel_form,
)
from .http import KorailHttpClient
from .limousine_models import (
    LimousineScheduleQuery,
    LimousineScheduleResponse,
    LimousineScheduleViewQuery,
    LimousineScheduleViewResponse,
    LimousineSeatInventoryQuery,
    LimousineSeatInventoryResponse,
)
from .limousine_parsers import (
    parse_limousine_schedule_response,
    parse_limousine_schedule_view_response,
    parse_limousine_seat_inventory_response,
)
from .limousine_payloads import (
    build_limousine_schedule_form,
    build_limousine_schedule_view_form,
    build_limousine_seat_inventory_form,
    validate_limousine_schedule_view_query,
)
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
    TrainSearchContinuation,
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
    CustomerTripInfoResponse,
    DelayDiscountTicketListResponse,
    DeliveryRecipientResponse,
    DepositBankListResponse,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GiftTicketListResponse,
    GuideSeatConditionResponse,
    MaasServiceDetailListResponse,
    MergeSeatsInquiryResponse,
    MultiChildDiscountTargetResponse,
    CommuterInfoResponse,
    PassAvailabilityResponse,
    PassMenuResponse,
    PassScheduleResponse,
    PbpAcceptanceSpecificationResponse,
    PlatformNumberResponse,
    ProductDetailResponse,
    PriceFareQuoteResponse,
    RecentDeliveryHistoryResponse,
    ProductReservationListResponse,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    ReservationHistoryResponse,
    SeatAssignmentScheduleResponse,
    ServiceStatusResponse,
    TicketReceiptResponse,
    TicketReservationDetailResponse,
    TicketDuplicationCheckResponse,
    TripChangeDateResponse,
    TripMenuResponse,
)
from .read_payloads import (
    build_customer_trip_info_form,
    build_delivery_recipient_form,
    build_commuter_info_form,
    build_cart_list_form,
    build_commuter_kind_menu_query,
    build_crew_request_list_query,
    build_delay_discount_ticket_form,
    build_discount_coupon_form,
    build_free_seat_car_form,
    build_gift_ticket_list_form,
    build_guide_seat_condition_form,
    build_maas_service_detail_form,
    build_merge_seats_inquiry_form,
    build_multi_child_discount_target_form,
    build_pass_availability_form,
    build_pass_menu_form,
    build_pass_schedule_form,
    build_pbp_acceptance_specification_form,
    build_platform_number_form,
    build_product_detail_query,
    build_product_reservations_query,
    build_price_fare_quote_form,
    build_recent_delivery_history_form,
    build_refund_commission_form,
    build_refund_ticket_detail_form,
    build_service_status_query,
    build_seat_assignment_schedule_form,
    build_ticket_receipt_form,
    build_ticket_reservation_detail_query,
    build_ticket_duplication_check_form,
    build_trip_menu_form,
    build_trip_change_date_form,
    FreeSeatCarRequest,
    CommuterInfoRequest,
    GiftTicketHistoryRequest,
    GiftTicketPaymentEligibilityRequest,
    GuideSeatConditionRequest,
    MaasServiceDetailQuery,
    MergeSeatsInquiryRequest,
    SeatAssignmentScheduleRequest,
    PassScheduleRequest,
    PriceFareQuoteRequest,
    OriginalTicketReference,
    RefundCompanion,
    TicketDuplicationCheckRequest,
    TicketReservationDetailRequest,
)
from .read_parsers import (
    parse_cart_list_response,
    parse_commuter_kind_menu_response,
    parse_crew_request_list_response,
    parse_customer_trip_info_response,
    parse_delay_discount_ticket_response,
    parse_delivery_recipient_response,
    parse_deposit_bank_response,
    parse_discount_coupon_response,
    parse_free_seat_car_response,
    parse_gift_ticket_list_response,
    parse_guide_seat_condition_response,
    parse_maas_service_detail_list_response,
    parse_merge_seats_inquiry_response,
    parse_multi_child_discount_target_response,
    parse_commuter_info_response,
    parse_pass_availability_response,
    parse_pass_menu_response,
    parse_pass_schedule_response,
    parse_pbp_acceptance_specification_response,
    parse_platform_number_response,
    parse_product_detail_response,
    parse_price_fare_quote_response,
    parse_recent_delivery_history_response,
    parse_product_reservation_list_response,
    parse_refund_commission_response,
    parse_refund_ticket_detail_response,
    parse_reservation_history_response,
    parse_service_status_response,
    parse_seat_assignment_schedule_response,
    parse_ticket_receipt_response,
    parse_ticket_reservation_detail_response,
    parse_ticket_duplication_check_response,
    parse_trip_change_date_response,
    parse_trip_menu_response,
)
from .session import KorailSessionClient

T = TypeVar("T")


def _scalar_text(value: object) -> str | None:
    """A KORAIL scalar as text, whether it arrived quoted or as a number.

    ``type(...) is int`` excludes bool, which is an int subclass and is never a
    KORAIL identity value.
    """
    if isinstance(value, str):
        return value
    if type(value) is int:
        return str(value)
    return None


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
        self.session.logout()

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
        room_class_code: str = "1",
    ) -> SeatCarListResponse:
        self._require_session()
        validate_seat_inventory_inputs(train, passenger_count)
        form = build_seat_car_form(
            self.config,
            train,
            passenger_count=passenger_count,
            sid=generate_sid(),
            room_class_code=room_class_code,
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
        room_class_code: str = "1",
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
            room_class_code=room_class_code,
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

    def get_limousine_schedules(
        self,
        query: LimousineScheduleQuery,
    ) -> LimousineScheduleResponse:
        form = build_limousine_schedule_form(self.config, query)
        return self._run_read(
            lambda: parse_limousine_schedule_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.lmu.scdlQry.do",
                    form,
                    include_common=False,
                    include_dynapath=False,
                )
            )
        )

    def get_limousine_seat_inventory(
        self,
        query: LimousineSeatInventoryQuery,
    ) -> LimousineSeatInventoryResponse:
        form = build_limousine_seat_inventory_form(self.config, query)
        return self._run_read(
            lambda: parse_limousine_seat_inventory_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do",
                    form,
                    include_common=False,
                    include_dynapath=False,
                )
            )
        )

    def get_limousine_schedule_view(
        self,
        query: LimousineScheduleViewQuery,
    ) -> LimousineScheduleViewResponse:
        validate_limousine_schedule_view_query(query)
        form = build_limousine_schedule_view_form(
            self.config,
            query,
            sid=generate_sid(),
        )
        return self._run_read(
            lambda: parse_limousine_schedule_view_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.seatMovie.LimousineScheduleView",
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
                    # A success body carries strResult only (its code lives in
                    # main_info), so the envelope gate would reject it before
                    # the parser ever saw it. A P058/FAIL body still carries the
                    # full envelope and is still raised on.
                    require_envelope=False,
                ).raw
            )
        )

    def get_pass_schedule(
        self,
        request: PassScheduleRequest,
    ) -> PassScheduleResponse:
        self._require_session()
        form = build_pass_schedule_form(request)
        return self._run_read(
            lambda: parse_pass_schedule_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.pass.passScheduleInfoList",
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
                    # A success body is {"list": [...], "strResult": "SUCC"}
                    # with no h_msg_cd/h_msg_txt, so the envelope gate would
                    # reject it before the parser ever saw it. A P058/FAIL body
                    # still carries the full envelope and is still raised on.
                    require_envelope=False,
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

    def get_multi_child_discount_targets(
        self,
        departure_date: str,
    ) -> MultiChildDiscountTargetResponse:
        self._require_session()
        form = build_multi_child_discount_target_form(departure_date)
        return self._run_read(
            lambda: parse_multi_child_discount_target_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.cust.mchdDcntTgt.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_customer_trip_info(self) -> CustomerTripInfoResponse:
        self._require_session()
        session = self.session.current
        customer_no = session.customer_no if session is not None else None
        if not isinstance(customer_no, str) or not customer_no.strip():
            raise KorailAuthError(
                "KORAIL customer trip read requires a login customer number"
            )
        form = build_customer_trip_info_form(customer_no)
        return self._run_read(
            lambda: parse_customer_trip_info_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.custTripInfo.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_maas_service_details(
        self,
        query: MaasServiceDetailQuery | None = None,
    ) -> MaasServiceDetailListResponse:
        self._require_session()
        resolved_query = (
            query if query is not None else MaasServiceDetailQuery.current()
        )
        form = build_maas_service_detail_form(self.config, resolved_query)
        return self._run_read(
            lambda: parse_maas_service_detail_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.copt.gdReqQry.do",
                    form,
                    include_common=False,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_trip_change_dates(
        self,
        departure_date: str,
    ) -> TripChangeDateResponse:
        self._require_session()
        form = build_trip_change_date_form(departure_date)
        return self._run_read(
            lambda: parse_trip_change_date_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.reservation.tripChgDate.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_gift_ticket_list(
        self,
        request: GiftTicketHistoryRequest
        | GiftTicketPaymentEligibilityRequest,
    ) -> GiftTicketListResponse:
        self._require_session()
        form = build_gift_ticket_list_form(request)
        return self._run_read(
            lambda: parse_gift_ticket_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.gift.gdLst.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_commuter_info(
        self,
        request: CommuterInfoRequest,
    ) -> CommuterInfoResponse:
        self._require_session()
        form = build_commuter_info_form(request)
        return self._run_read(
            lambda: parse_commuter_info_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.cmtrInfo.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_price_fare_quote(
        self,
        request: PriceFareQuoteRequest,
    ) -> PriceFareQuoteResponse:
        form = build_price_fare_quote_form(request)
        return self._run_read(
            lambda: parse_price_fare_quote_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.trn.prcFare.do",
                    form,
                ).raw
            )
        )

    def get_delivery_recipient(
        self,
        ticket: OriginalTicketReference,
    ) -> DeliveryRecipientResponse:
        self._require_session()
        form = build_delivery_recipient_form(ticket)
        return self._run_read(
            lambda: parse_delivery_recipient_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.tk.dlvRcvCust.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def check_ticket_duplication(
        self,
        request: TicketDuplicationCheckRequest,
    ) -> TicketDuplicationCheckResponse:
        self._require_session()
        form = build_ticket_duplication_check_form(request)
        return self._run_read(
            lambda: parse_ticket_duplication_check_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.ticket.ticketDupCheck.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_pbp_acceptance_specifications(
        self,
        tickets: tuple[OriginalTicketReference, ...],
    ) -> PbpAcceptanceSpecificationResponse:
        self._require_session()
        form = build_pbp_acceptance_specification_form(tickets)
        return self._run_read(
            lambda: parse_pbp_acceptance_specification_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.tk.pbpAcepSpec.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_platform_numbers(
        self,
        tickets: tuple[OriginalTicketReference, ...],
    ) -> PlatformNumberResponse:
        self._require_session()
        form = build_platform_number_form(tickets)
        return self._run_read(
            lambda: parse_platform_number_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.tk.plfNo.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_recent_delivery_history(self) -> RecentDeliveryHistoryResponse:
        self._require_session()
        session = self.session.current
        customer_no = session.customer_no if session is not None else None
        if not isinstance(customer_no, str) or not customer_no.strip():
            raise KorailAuthError(
                "KORAIL delivery history read requires a login customer number"
            )
        form = build_recent_delivery_history_form(customer_no)
        return self._run_read(
            lambda: parse_recent_delivery_history_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.tk.rcntDlvHst.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_ticket_reservation_detail(
        self,
        request: TicketReservationDetailRequest,
    ) -> TicketReservationDetailResponse:
        """Read one held reservation back by PNR.

        Ports ONLY the read overload of
        ``/classes/com.korail.mobile.certification.ReservationList``
        (``CertificationService.java:45-46`` ``inquiryTicketRsv``). The same
        path also carries ``applyDisabilityCertification`` (:22), which applies
        a disability certificate to a held reservation and is therefore a
        write; it is not ported, and the route's four-field pin in
        ``KORAIL_EXACT_REQUEST_FIELDS`` means its wider request shape cannot be
        emitted here even by accident.
        """
        self._require_session()
        query = build_ticket_reservation_detail_query(request)
        return self._run_read(
            lambda: parse_ticket_reservation_detail_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.certification.ReservationList",
                    query,
                    include_common=True,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_refund_commission(
        self,
        ticket: OriginalTicketReference,
        companion: RefundCompanion = RefundCompanion(),
    ) -> RefundCommissionResponse:
        """Ask what a refund of ``ticket`` would return and what it would cost.

        Read-only pre-check for :meth:`refund` (``RefundService.java:19-21``).
        Nothing is refunded by calling this; it reports ``ret_amt`` /``ret_fee``
        /``prg_psb_flg`` so a caller can decide before touching the mutation
        route.
        """
        self._require_session()
        form = build_refund_commission_form(ticket, companion)
        return self._run_read(
            lambda: parse_refund_commission_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.refunds.CommissionView",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_refund_ticket_detail(
        self,
        ticket: OriginalTicketReference,
        *,
        from_purchase_history: bool = False,
    ) -> RefundTicketDetailResponse:
        """Read the refund target's ticket detail (``RefundService.java:23-25``).

        The app chains this before :meth:`get_refund_commission`: the response's
        ``h_compa_nm``/``h_compa_brth`` become that call's
        ``h_comp_nm``/``h_comp_cert_no`` (``TicketListActivity.java:908-909``).
        Set ``from_purchase_history=True`` to send the app's purchase-history
        variant (``h_purchase_history="Y"``).
        """
        self._require_session()
        form = build_refund_ticket_detail_form(
            ticket,
            from_purchase_history=from_purchase_history,
        )
        return self._run_read(
            lambda: parse_refund_ticket_detail_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.refunds.SelTicketInfo",
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

    def search_trains(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
    ) -> TrainSearchResult:
        """Search one page of trains.

        Pass ``continuation=previous.next_page()`` to fetch the page after
        ``previous``; the app pages the same way, replaying the previous
        response's cursor into ``qryStNo``/``qryStTrnNo``/``pgPrCnt``
        (``b5/c.java:184-194``). ``next_page()`` returns ``None`` once the
        server stops setting ``h_next_pg_flg="Y"``, which is the app's own
        stop condition.
        """
        return self._run_read(
            lambda: self._search_trains(query, continuation)
        )

    def _search_trains(
        self,
        query: TrainSearchQuery,
        continuation: TrainSearchContinuation | None = None,
    ) -> TrainSearchResult:
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
            continuation=continuation,
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

    def get_ticket_list(
        self,
        page_no: int = 0,
        *,
        mode: str = "1",
        boarding_date_from: str = "",
        boarding_date_to: str = "",
    ) -> BaseKorailResponse:
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL ticket list requires an authenticated session"
            )
        return self._run_read(
            lambda: self.http.post_form(
                "/classes/com.korail.mobile.myTicket.MyTicketList",
                build_ticket_list_form(
                    self.config,
                    page_no,
                    mode=mode,
                    boarding_date_from=boarding_date_from,
                    boarding_date_to=boarding_date_to,
                ),
            )
        )

    def reserve(
        self,
        train: TrainSummary,
        *,
        consent: MutationConsent,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
        seats: Sequence[KorailSeatAssignment] | None = None,
    ) -> MutationPreview | ReservationHoldResponse:
        """Hold a reservation for a passenger mix under explicit consent.

        Gated by ``require_mutation_consent(consent, "reserve")``: a default
        :class:`MutationConsent` (``allow_reserve=False``) or ``None`` is denied
        with :class:`MutationNotAllowedError` before anything is built. Requires
        an authenticated session. With the default ``dry_run=True`` it validates
        ``train`` and returns a :class:`MutationPreview` of the exact form that
        WOULD be POSTed, without touching the network. With ``dry_run=False`` it
        performs the live hold via the double-gated mutation send path and
        returns the parsed :class:`ReservationHoldResponse` (whose ``pnr_no``
        feeds :meth:`cancel_unpaid_hold`). A live hold is an unpaid reservation
        that the caller is responsible for cancelling or paying.

        ``passengers`` is a :class:`KorailPassengerCounts`, defaulting to its
        own one-adult default, and ``seat_class`` a :class:`KorailSeatClass`,
        defaulting to 일반실. Omitting both sends exactly the form this method
        sent before mixes existed, so no existing caller changes behaviour.
        Only that single-adult, general-class form has ever been accepted by
        the live server; a multi-passenger or 특실 hold is built from the app's
        own request builder but is NOT live-verified.

        ``job_type`` is a :class:`KorailReservationJobType` and defaults to
        ``IMMEDIATE`` (``txtJobId="1101"``), the only value this method sent
        before, so an existing call is byte-for-byte unchanged:

        * ``SEAT_DESIGNATED`` (``"1103"``) books named seats and needs ``seats``
          -- exactly one :class:`KorailSeatAssignment` per passenger, each taken
          from :meth:`get_seat_cars` + :meth:`get_seat_inventory`. A count that
          does not match the passenger total is refused here, before any
          request is built.
        * ``STANDBY`` (``"1102"``) places a 예약대기 booking on a train whose
          search row says standby is possible. It is **members only** -- the
          app's own request refuses to offer the non-member path for this job id
          (``ReservationRequest.java:105-119``) -- which this client satisfies
          structurally, since every mutation here needs a logged-in member
          session and the non-member booking route is not reachable at all. A
          successful standby hold comes back with ``h_msg_cd`` =
          :data:`~korail_mobile_api.KORAIL_STANDBY_HOLD_MESSAGE_CODE`
          (``IRR000014``) and is only complete once
          :meth:`confirm_standby_hold` records its notify options.

        Neither non-default job type has ever been transmitted.
        """
        require_mutation_consent(consent, "reserve")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL reservation requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_reservation_form(
            self.config,
            train,
            passengers=passengers,
            seat_class=seat_class,
            job_type=job_type,
            seats=seats,
        )
        if consent.dry_run:
            return MutationPreview(
                category="reserve",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            response = self.http.post_mutation_form(
                route, form, consent=consent, category="reserve"
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise
        return self._hold_from_reservation_response(response)

    def confirm_standby_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        consent: MutationConsent,
        allow_seat_class_change: bool = False,
        sms_notify: bool = False,
        phone_no: str | None = None,
    ) -> MutationPreview | BaseKorailResponse:
        """Record the 예약대기 options for a standby hold (second half of "1102").

        A standby booking is two calls in the app, not one: :meth:`reserve` with
        ``job_type=STANDBY`` creates the PNR and returns ``h_msg_cd`` =
        ``IRR000014``, which is the only code that opens 예약대기 screen
        (``ui/inquiry/rir/orr/a.java:222-225``); that screen then POSTs
        ``reservationWait.ReservationWait``
        (``ReservationWaitService.java:10-12``) with the user's choices. This
        method is that second POST.

        It is a state-changing call on an existing PNR, so it goes through the
        same double-gated mutation transport as every other mutation -- never
        the read path. Its consent category is deliberately ``"reserve"``: it
        completes the booking that an ``allow_reserve`` consent authorised, and
        moves no money and releases no seat. See
        :data:`~korail_mobile_api.KORAIL_MUTATION_ROUTES` for why that is not a
        new category.

        ``allow_seat_class_change`` is ``txtPsrmClChgFlg`` (may KORAIL seat the
        booking in a different cabin when it assigns one) and ``sms_notify`` is
        ``txtSmsSndFlg``; both default to the unchecked state the app's screen
        opens in. ``phone_no`` is required when, and permitted only when,
        ``sms_notify`` is True.

        With the default ``dry_run=True`` it returns a :class:`MutationPreview`
        (PNR and phone number redacted) and sends nothing.

        NOT live-verified.
        """
        require_mutation_consent(consent, "reserve")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL standby options require an authenticated session"
            )
        route = "/classes/com.korail.mobile.reservationWait.ReservationWait"
        form = build_standby_wait_form(
            self.config,
            hold,
            allow_seat_class_change=allow_seat_class_change,
            sms_notify=sms_notify,
            phone_no=phone_no,
        )
        if consent.dry_run:
            return MutationPreview(
                category="reserve",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            return self.http.post_mutation_form(
                route, form, consent=consent, category="reserve"
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    @staticmethod
    def _hold_from_reservation_response(
        response: BaseKorailResponse,
    ) -> ReservationHoldResponse:
        # A live reserve may create a real hold on the server; we must NEVER
        # lose the identity needed to cancel it. Strict parsing can raise on an
        # unrelated malformed optional field AFTER the hold exists, so when it
        # does we fall back to a minimal hold that still carries the PNR and
        # journey count, letting the caller auto-cancel. We only re-raise when
        # no PNR was returned (no hold to orphan).
        raw = response.raw if isinstance(response.raw, dict) else {}
        try:
            return parse_reservation_hold_response(raw)
        except KorailProtocolError:
            # A PNR or journey count that arrived as a JSON number is a hold we
            # can still cancel, so normalise both here the same way the parser
            # does rather than discarding the only identity we have.
            pnr = _scalar_text(raw.get("h_pnr_no"))
            if not (pnr and pnr.strip()):
                raise
            base = BaseKorailResponse.from_raw(raw)
            return ReservationHoldResponse(
                h_msg_cd=base.h_msg_cd,
                h_msg_txt=base.h_msg_txt,
                str_result=base.str_result,
                raw=raw,
                pnr_no=pnr,
                journey_count=_scalar_text(raw.get("h_jrny_cnt")),
            )

    def cancel_unpaid_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """Cancel a fresh, unpaid single-journey reservation hold.

        Gated by ``require_mutation_consent(consent, "cancel")`` and an
        authenticated session. ``build_unpaid_reservation_cancel_form`` requires
        ``hold`` to be one successful (``SUCC``) single-journey hold with a PNR,
        so this only ever releases a hold produced by :meth:`reserve`. With
        ``dry_run=True`` it returns a :class:`MutationPreview` (redacting the
        PNR); with ``dry_run=False`` it POSTs the cancellation via the
        double-gated mutation send path and returns the parsed envelope. This is
        the auto-cancel used to immediately release a live test hold.
        """
        require_mutation_consent(consent, "cancel")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL cancellation requires an authenticated session"
            )
        route = (
            "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk"
        )
        form = build_unpaid_reservation_cancel_form(self.config, hold)
        if consent.dry_run:
            return MutationPreview(
                category="cancel",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            return self.http.post_mutation_form(
                route, form, consent=consent, category="cancel"
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def pay_with_fake_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationPaymentResponse:
        """Attempt a single-card payment for an unpaid hold (FAKE cards only).

        Gated by ``require_mutation_consent(consent, "payment")`` and an
        authenticated session. The KORAIL pay call sends the PAN in the clear,
        so this method refuses unless ``consent.fake_card_only`` is True and
        expects the supplied ``card`` to be a non-chargeable test card that the
        PG will decline. With ``dry_run=True`` it returns a
        :class:`MutationPreview` whose card and identity fields are redacted;
        with ``dry_run=False`` it POSTs the payment via the double-gated
        mutation path and returns the parsed :class:`ReservationPaymentResponse`
        WITHOUT raising on a decline (``raise_on_fail=False``), so the caller can
        inspect the rejection code. The hold stays unpaid on decline and can be
        released with :meth:`cancel_unpaid_hold`.
        """
        require_mutation_consent(consent, "payment")
        if not consent.fake_card_only:
            raise MutationNotAllowedError(
                "pay_with_fake_card requires consent.fake_card_only=True; only "
                "non-chargeable test cards are supported"
            )
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL payment requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.payment.ReservationPayment"
        form = build_card_payment_form(self.config, hold, card)
        if consent.dry_run:
            return MutationPreview(
                category="payment",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            response = self.http.post_mutation_form(
                route,
                form,
                consent=consent,
                category="payment",
                raise_on_fail=False,
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise
        return parse_reservation_payment_response(response.raw)

    def pay_with_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationPaymentResponse:
        """Pay for an unpaid hold with a REAL, CHARGEABLE card. Money moves.

        This is the sibling of :meth:`pay_with_fake_card`, not a replacement for
        it: that method still exists, still refuses anything but a test card, and
        its name still means what it says. The wire shape is identical — both
        build the same ``build_card_payment_form`` and both leave through the
        same double-gated
        :meth:`~korail_mobile_api.http.KorailHttpClient.post_mutation_form`
        — so a real payment cannot drift from the shape that was verified live.
        The ONLY difference is which consent each accepts.

        This one requires ``consent.real_card_acknowledged is True`` AND
        ``consent.fake_card_only is False``. Both halves must be stated:
        acknowledging a real charge while still claiming a test card is a
        contradiction, and it is refused here and again at the transmit gate
        rather than resolved. The default :class:`MutationConsent` satisfies
        neither, so nothing that has not been deliberately written for a real
        charge can reach this path. Gated further by
        ``require_mutation_consent(consent, "payment")`` and an authenticated
        session. With ``dry_run=True`` it returns a :class:`MutationPreview`
        whose card and identity fields are redacted and transmits nothing.

        Like its sibling it sends with ``raise_on_fail=False``, but for a
        different reason. A fake card is *expected* to decline; a real card is
        not, and precisely because a real failure is unexpected the caller needs
        the server's own envelope rather than an exception. The response code is
        what distinguishes "declined, the hold is still unpaid, cancel it" from
        an ambiguous outcome that must NOT be blind-cancelled, and it is the only
        record of what happened to the money. Raising would discard that at the
        exact moment it matters most, leaving a hold of unknown payment state.
        So the parsed :class:`ReservationPaymentResponse` is always returned and
        the caller decides; check ``str_result``/``h_msg_cd`` before assuming the
        ticket is paid.
        """
        require_mutation_consent(consent, "payment")
        if not consent.real_card_acknowledged:
            raise MutationNotAllowedError(
                "pay_with_card requires consent.real_card_acknowledged=True; a "
                "real, chargeable card number is transmitted in the clear and "
                "money actually moves, so the caller must say so explicitly "
                "(use pay_with_fake_card for a non-chargeable test card)"
            )
        if consent.fake_card_only:
            raise MutationNotAllowedError(
                "pay_with_card requires consent.fake_card_only=False; a consent "
                "that still claims a non-chargeable test card while "
                "acknowledging a real charge is contradictory and is never sent"
            )
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL payment requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.payment.ReservationPayment"
        form = build_card_payment_form(self.config, hold, card)
        if consent.dry_run:
            return MutationPreview(
                category="payment",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            response = self.http.post_mutation_form(
                route,
                form,
                consent=consent,
                category="payment",
                raise_on_fail=False,
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise
        return parse_reservation_payment_response(response.raw)

    def refund(
        self,
        ticket: PaidTicket,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """Refund a settled (paid) ticket via ``refunds.RefundsRequest``.

        Gated by ``require_mutation_consent(consent, "refund")`` and an
        authenticated session. ``build_refund_form`` requires a
        :class:`~korail_mobile_api.mutation_models.PaidTicket` (PNR + original
        sale identity + return password). With ``dry_run=True`` it returns a
        :class:`MutationPreview` with the ticket identity redacted; with
        ``dry_run=False`` it POSTs via the double-gated mutation path and returns
        the parsed envelope. NOTE: a refund acts on a *paid* ticket, and this
        package's fake-card payment is always declined, so no live paid ticket is
        produced here — the live path exists but is exercised offline only.
        """
        require_mutation_consent(consent, "refund")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL refund requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.refunds.RefundsRequest"
        form = build_refund_form(self.config, ticket)
        if consent.dry_run:
            return MutationPreview(
                category="refund",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            return self.http.post_mutation_form(
                route, form, consent=consent, category="refund"
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise
