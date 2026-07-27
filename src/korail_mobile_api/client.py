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
    KorailNoDirectTrainError,
    KorailProtocolError,
    KorailSessionExpiredError,
    MutationNotAllowedError,
)
from .mutation_models import (
    CardPayment,
    DiscountCardPurchaseRequest,
    DiscountCardPurchaseResponse,
    DiscountCardTicket,
    KorailPassengerCounts,
    KorailSeatAssignment,
    OfflineRefundExecuteResponse,
    OfflineRefundReturnNumber,
    OfflineRefundVerifyResponse,
    PaidTicket,
    PriceRecalculationRequest,
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from .mutation_parsers import (
    parse_discount_card_purchase_response,
    parse_offline_refund_execute_response,
    parse_offline_refund_verify_response,
    parse_reservation_hold_response,
    parse_reservation_payment_response,
)
from .mutation_payloads import (
    build_card_payment_form,
    build_discount_card_extension_query,
    build_discount_card_purchase_form,
    build_discount_card_reservation_form,
    build_merge_reservation_form,
    build_offline_refund_execute_form,
    build_offline_refund_verify_form,
    build_price_recalculation_form,
    build_refund_form,
    build_reservation_form,
    build_standby_wait_form,
    build_transfer_reservation_form,
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
    KorailNonMemberSession,
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
    TransferSearchResult,
    TransferStationListResponse,
    UuidResponse,
    pair_transfer_itineraries,
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
    DiscountCardScheduleResponse,
    DiscountCardUsageListResponse,
    DeliveryRecipientResponse,
    DepositBankListResponse,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GiftTicketListResponse,
    GuideSeatConditionResponse,
    KorailPointSummaryResponse,
    MaasServiceDetailListResponse,
    MergeSeatsInquiryResponse,
    MileageHistoryResponse,
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
    TrainScheduleItem,
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
    DiscountCardScheduleRequest,
    build_delay_discount_ticket_form,
    build_discount_card_schedule_query,
    build_discount_card_usage_query,
    build_discount_coupon_form,
    build_free_seat_car_form,
    build_gift_ticket_list_form,
    build_guide_seat_condition_form,
    build_korail_point_summary_form,
    build_mileage_history_form,
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
    MileageHistoryRequest,
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
    parse_discount_card_schedule_response,
    parse_discount_card_usage_response,
    parse_delivery_recipient_response,
    parse_deposit_bank_response,
    parse_discount_coupon_response,
    parse_free_seat_car_response,
    parse_gift_ticket_list_response,
    parse_guide_seat_condition_response,
    parse_korail_point_summary_response,
    parse_mileage_history_response,
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

    def get_korail_point_summary(self) -> KorailPointSummaryResponse:
        """Read the my-page loyalty and welfare-entitlement summary.

        ``POST xPoint.MyXPointView`` (``XPointService.java:18-20``), the call
        마이페이지 makes on open (``MyPageActivity.java:414``). It takes no
        arguments: ``point_dv_cd`` is the literal ``"0"`` the DAO itself passes
        (``KorailPointInquiryDao.java:91``), and there is no request class.

        **Why this read is here.** Besides the point balance and the
        coupon/지연할인권 counts, the response carries the account's welfare
        registration: ``MyPageActivity.java:206-212`` shows the whole 장애인
        section only when ``h_hdcp_flg`` is ``"Y"``, then labels
        ``h_subt_dcs_cl_nm`` 장애인증 and ``h_cust_lead_flg_nm`` 보조견
        (``:353-355``, ``:393-394``). That makes this the cheapest available
        check on whether an account is even eligible for the 1~3급 장애 /
        안내견 fares, which a live reservation refused on 2026-07-26 with the
        server-only code ``ERR299943`` on a byte-exact form
        (``docs/MUTATION_HANDOFF.md:172-179``).

        **NOT LIVE-VERIFIED, and the entitlement reading is a hypothesis.** No
        call has been made on this route; the mapping above is what the app
        does with the fields, not an observed correlation between the flag and
        that refusal.

        This route reads points; it never moves them. The loyalty routes that
        carry a user password (``mlg.lpotAthn.do``, ``xPoint.XPointView``) are
        deliberately unimplemented — a wrong password there increments a
        server-side failure counter, which is a state change.
        """
        self._require_session()
        form = build_korail_point_summary_form()
        return self._run_read(
            lambda: parse_korail_point_summary_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.xPoint.MyXPointView",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_mileage_history(
        self,
        request: MileageHistoryRequest,
    ) -> MileageHistoryResponse:
        """Read one page of the 마일리지 적립/사용 내역 ledger.

        ``POST mlg.amtSpec.do`` (``XPointService.java:26-28``). ``request``
        chooses the ledger (KTX 마일리지 vs 철도포인트), the movement filter
        (전체/적립/사용) and the date window; the page size is fixed at 20
        because the app hardcodes it (``MileageHistoryActivity.java:274``).

        Paging is the caller's: the response's
        :attr:`~korail_mobile_api.read_models.MileageHistoryResponse.page_count`
        is the ceiling the app scrolls to (``:158,581``).

        **NOT LIVE-VERIFIED.** Shape from ``MileageInquiryDao``.
        """
        self._require_session()
        form = build_mileage_history_form(request)
        return self._run_read(
            lambda: parse_mileage_history_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.mlg.amtSpec.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_discount_card_usage_history(
        self,
        card_no: str,
    ) -> DiscountCardUsageListResponse:
        """List the trips a 할인카드(N카드) has already been spent on.

        ``GET ticket.dcntCrdUseQry.do`` (``ResearchService.java:51-52``), the
        read behind the ticket list's "사용 내역 조회하기" button
        (``Y4/Q.java:347-353``). ``card_no`` is the card's own number, which
        the app never asks a user to type: it comes off the N카드 ticket's
        detail response as ``dcnt_crd_info.h_dcnt_crd_no``
        (``Y4/C0907b.java:303``), i.e. from
        :attr:`~korail_mobile_api.read_models.RefundTicketDetailResponse.discount_card`.

        **NOT LIVE-VERIFIED.** No account this project can reach owns an N카드,
        so the request shape is the APK's declaration and the response shape is
        ``NCardHistoryDao`` rather than an observed body. Calling it with a
        card number that is not the caller's own is expected to be refused by
        the server; nothing here bypasses that.
        """
        self._require_session()
        query = build_discount_card_usage_query(card_no)
        return self._run_read(
            lambda: parse_discount_card_usage_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do",
                    query,
                    include_common=True,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_discount_card_schedule(
        self,
        request: DiscountCardScheduleRequest,
    ) -> DiscountCardScheduleResponse:
        """List the trains a 할인카드 may still be spent on, for one section.

        ``GET research.dcntCrdScheduleView.do``
        (``ResearchService.java:54-55``). This is NOT the ordinary train
        search: an N카드 is sold against one to three fixed 구간, and this
        route answers "which trains on this 구간 does this card cover", which
        is why it is keyed by the card product (``dcntCrdKndCd`` /
        ``dcntCrdKndMgNo``) rather than by station codes.

        Paging is the caller's: the response's
        :attr:`~korail_mobile_api.read_models.DiscountCardScheduleResponse.following_page_exists`
        is ``"Y"`` while another page follows, and the app re-issues the read
        with an incremented ``qryPgNo``
        (``SectionNCardInquiryActivity.java:406-408``). Build the next request
        with ``page_no`` set; leave it ``None`` for the first page, which is
        what v6.5.0 itself sends.

        **NOT LIVE-VERIFIED**, for the same reason as
        :meth:`get_discount_card_usage_history`.
        """
        self._require_session()
        query = build_discount_card_schedule_query(request)
        return self._run_read(
            lambda: parse_discount_card_schedule_response(
                self.http.get_json(
                    (
                        "/classes/com.korail.mobile.research."
                        "dcntCrdScheduleView.do"
                    ),
                    query,
                    include_common=True,
                    include_dynapath=False,
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

    def search_transfer_trains(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
    ) -> TransferSearchResult:
        """Search one page of 환승 itineraries for the same query.

        Same endpoint, same form, one field different: ``radJobId`` carries
        :data:`~korail_mobile_api.KORAIL_TRANSFER_ITINERARY_CODE` (``"2"``)
        instead of ``"1"``. That is the entirety of the app's transfer query --
        ``DirectInquiryActivity.java:284-296`` sets exactly that on the
        ``RsvInquiryRequest`` it already built and hands the object on
        untouched.

        The response is **not** shaped differently. It is the same flat
        ``trn_infos.trn_info`` list, and the legs are paired positionally: rows
        0/1 are one itinerary, rows 2/3 the next (``a5/k.java:156-170``, and
        ``:108-110`` reading a selection back out as ``{list[i*2],
        list[i*2+1]}``). :attr:`TransferSearchResult.itineraries
        <korail_mobile_api.TransferSearchResult.itineraries>` is that pairing;
        :attr:`~korail_mobile_api.TransferSearchResult.trains` is the raw list.

        Paging works, with a different cursor -- see
        :meth:`TransferSearchResult.next_page
        <korail_mobile_api.TransferSearchResult.next_page>`. Feed its result
        back in as ``continuation``.

        This is a read. It sends nothing that changes state, and a caller who
        never books can use it freely. NOT live-verified: reaching it requires a
        station pair with no direct service.
        """
        return self._run_read(
            lambda: self._search_transfer_trains(query, continuation)
        )

    def search_trains_with_transfer_fallback(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
    ) -> TrainSearchResult | TransferSearchResult:
        """Search direct trains, falling back to 환승 when there are none.

        This is the app's own flow, not a convenience invented here. A direct
        ScheduleView that finds nothing answers ``WRD000061`` ("직통열차가
        없습니다"); ``DirectInquiryActivity.java:615-624`` catches exactly that
        code, and nothing else, and raises a confirm dialog whose 확인 branch
        (``:284-296``) re-issues the query with ``radJobId="2"`` and moves the
        user to the transfer screen.

        This client already classifies ``WRD000061`` as
        :class:`~korail_mobile_api.KorailNoDirectTrainError`, so the fallback is
        that exception and no other: any other failure propagates. The return
        type tells you which happened -- a :class:`TrainSearchResult
        <korail_mobile_api.TrainSearchResult>` means the direct search
        succeeded, a :class:`TransferSearchResult
        <korail_mobile_api.TransferSearchResult>` means it did not and these are
        the transfer alternatives. Call :meth:`search_trains` or
        :meth:`search_transfer_trains` directly when you want one or the other
        unconditionally.

        ``continuation`` is forwarded to the direct search only. A cursor is
        specific to the search that produced it, and a direct cursor replayed
        into a transfer query would be asking a different question with the
        wrong bookmark, so the fallback always starts the transfer search at
        page one.
        """
        try:
            return self.search_trains(query, continuation=continuation)
        except KorailNoDirectTrainError:
            return self.search_transfer_trains(query)

    def _search_trains(
        self,
        query: TrainSearchQuery,
        continuation: TrainSearchContinuation | None = None,
    ) -> TrainSearchResult:
        response = self._post_schedule_view(query, continuation, transfer=False)
        return TrainSearchResult(
            trains=parse_train_rows(response.raw),
            response=response,
            raw=response.raw,
            metadata=parse_train_search_metadata(response.raw),
        )

    def _search_transfer_trains(
        self,
        query: TrainSearchQuery,
        continuation: TrainSearchContinuation | None = None,
    ) -> TransferSearchResult:
        response = self._post_schedule_view(query, continuation, transfer=True)
        trains = parse_train_rows(response.raw)
        return TransferSearchResult(
            itineraries=pair_transfer_itineraries(trains),
            trains=trains,
            response=response,
            raw=response.raw,
            metadata=parse_train_search_metadata(response.raw),
        )

    def _post_schedule_view(
        self,
        query: TrainSearchQuery,
        continuation: TrainSearchContinuation | None,
        *,
        transfer: bool,
    ) -> BaseKorailResponse:
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
            transfer=transfer,
        )
        return self.http.post_form(
            "/classes/com.korail.mobile.seatMovie.ScheduleView",
            form,
            include_common=False,
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

    def reserve_transfer(
        self,
        legs: Sequence[TrainSummary],
        *,
        consent: MutationConsent,
        passengers: KorailPassengerCounts | None = None,
        seat_classes: Sequence[KorailSeatClass] | KorailSeatClass = (
            KorailSeatClass.GENERAL
        ),
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
        seats: Sequence[Sequence[KorailSeatAssignment]] | None = None,
    ) -> MutationPreview | ReservationHoldResponse:
        """Hold one 환승 reservation -- two legs, one PNR.

        The same route, consent gate and session requirement as :meth:`reserve`;
        the app uses one endpoint and one request builder for both, and the leg
        count alone changes the form (``C5/a.java:52-119``). Everything
        :meth:`reserve` says about consent, ``dry_run`` and the returned hold
        applies unchanged.

        ``legs`` must be exactly two :class:`~korail_mobile_api.TrainSummary`
        rows in boarding order --
        :attr:`TransferItinerary.legs
        <korail_mobile_api.TransferItinerary.legs>` from
        :meth:`search_transfer_trains` produces them. Any other count is
        refused before anything is built; see
        :data:`~korail_mobile_api.KORAIL_MAX_JOURNEY_LEGS`.

        ``seat_classes`` takes one :class:`~korail_mobile_api.KorailSeatClass`
        for both legs or one per leg -- the app's cabin choice is per leg
        (``C5/a.java:59``/``:97``). ``seats`` likewise takes one seat list per
        leg, since the seat picker is opened per journey index
        (``C5/a.java:120-133``).

        ``job_type=STANDBY`` is **refused**: 예약대기 does not exist for a
        transfer itinerary. ``a5/k.java:120-127`` returns false from the
        standby-eligibility check for any non-direct result, and the app's only
        ``txtJobId="1102"`` sits on the direct screen
        (``DirectInquiryActivity.java:434``).

        NOT live-verified: no transfer hold has been sent to KORAIL.
        :meth:`cancel_unpaid_hold` DOES release one — it echoes the hold's own
        journey count rather than assuming one, so a two-journey transfer hold
        cancels through this client like any other.
        """
        require_mutation_consent(consent, "reserve")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL reservation requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_transfer_reservation_form(
            self.config,
            legs,
            passengers=passengers,
            seat_classes=seat_classes,
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

    def reserve_merge(
        self,
        standing_hold_train: TrainSummary,
        legs: Sequence[TrainScheduleItem],
        *,
        consent: MutationConsent,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
    ) -> MutationPreview | ReservationHoldResponse:
        """Hold a 병합예약 -- ONE train split at a mid station, two journeys.

        The second and last hold of the merge flow. The first is
        :meth:`reserve` with
        ``job_type=KorailReservationJobType.MERGE_STANDING`` (``"1202"``,
        입석+좌석 예매), which buys the whole route standing; this one replaces
        it with a two-journey booking on the same train, split at one of the
        stations :meth:`get_merge_seats_inquiry` names.
        :data:`~korail_mobile_api.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE`
        documents the five-step flow and its evidence.

        Same route, consent gate and session requirement as :meth:`reserve`. It
        is the reserve route and the ``"reserve"`` category: a merged booking is
        a booking, and it moves no money.

        ``standing_hold_train`` is the 직통 row the ``"1202"`` hold was placed
        on -- it is needed for more than validation, because the app's merged
        form carries that row's arrival time in ``arvTm_1`` (see
        :func:`~korail_mobile_api.mutation_payloads.build_merge_reservation_form`).
        ``legs`` are the two rows from
        :attr:`MergeSeatsInquiryResponse.trains
        <korail_mobile_api.MergeSeatsInquiryResponse.trains>`, in order.

        WHAT THIS METHOD DOES NOT DO: the app cancels the standing hold before
        re-booking (``DirectInquiryActivity.java:227-250`` -- ReservationCancel
        then ReservationCancelChk). That is :meth:`cancel_unpaid_hold`, under
        the ``"cancel"`` consent, and it is deliberately left to the caller
        rather than performed here: a method that silently cancels a live PNR
        under a ``"reserve"`` consent would be exactly the category confusion
        this client's gates exist to prevent.

        NEVER TRANSMITTED. No merged form built here has been sent to KORAIL.
        """
        require_mutation_consent(consent, "reserve")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL reservation requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_merge_reservation_form(
            self.config,
            standing_hold_train,
            legs,
            passengers=passengers,
            seat_class=seat_class,
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

    def cancel_unpaid_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """Cancel a fresh, unpaid reservation hold, however many journeys it has.

        Gated by ``require_mutation_consent(consent, "cancel")`` and an
        authenticated session. ``build_unpaid_reservation_cancel_form`` requires
        ``hold`` to be one successful (``SUCC``) hold with a PNR, and echoes the
        hold's OWN journey count into ``txtJrnyCnt`` rather than fixing it at
        one. That is deliberate: a 환승 hold carries two journeys and a 병합
        hold can carry more, and refusing them here would strand a live
        reservation with no way to release it. So this releases holds from
        :meth:`reserve`, :meth:`reserve_transfer` and :meth:`merge_reservation`
        alike. With ``dry_run=True`` it returns a :class:`MutationPreview`
        (redacting the PNR); with ``dry_run=False`` it POSTs the cancellation
        via the double-gated mutation send path and returns the parsed envelope.
        This is the auto-cancel used to immediately release a live test hold.

        This sends the SECOND of the app's two cancel calls
        (``ReservationCancelChk``), not both. Skipping ``ReservationCancel`` is
        a live-verified simplification, not an oversight — see
        ``docs/MUTATION_HANDOFF.md:21``.
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
        return_times_division_code: str | None = None,
        settle_mileage: bool = False,
        pbp_acceptance_target_flag: str | None = None,
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

        The app does not send fixed values for three of this form's fields; it
        echoes what the server just told it. To match it, chain the two reads
        that carry those values:

        1. :meth:`get_refund_ticket_detail` →
           :attr:`RefundTicketDetailResponse.pbp_acceptance_target_flag`
        2. :meth:`get_refund_commission` →
           :attr:`ticket_return_times_division_code` (``"21"`` before
           departure, ``"15"`` after)

        and pass both here. ``settle_mileage`` is a caller decision rather than
        an echo — the app sets it only when the ticket is mileage-settleable and
        the usable balance covers the fee. Omitting all three keeps the previous
        fixed ``"21"``/``"N"``/``"N"``, which is correct only for a
        before-departure, non-mileage, non-PBP refund.
        """
        require_mutation_consent(consent, "refund")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL refund requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.refunds.RefundsRequest"
        form = build_refund_form(
            self.config,
            ticket,
            return_times_division_code=return_times_division_code,
            settle_mileage=settle_mileage,
            pbp_acceptance_target_flag=pbp_acceptance_target_flag,
        )
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

    def _require_non_member_identity(self, *, operation: str):
        """The 비회원 precondition, and the member session's absence.

        Both halves matter. A held
        :class:`~korail_mobile_api.models.KorailNonMemberSession` is what these
        two routes send instead of a session cookie, so without one there is
        nothing to send. And an ACTIVE MEMBER SESSION is refused rather than
        ignored: a caller who is logged in and reaches for an offline refund
        has almost certainly reached for the wrong method, and the member path
        (:meth:`refund`) is one line away. ``begin_non_member`` already refuses
        the reverse ordering, so the two states cannot both be set — this is
        the defence at the point of use.
        """
        non_member = self.session.non_member
        if self.session.current is not None:
            raise KorailAuthError(
                f"KORAIL {operation} is the NON-MEMBER offline path and "
                "refuses to run while a member session is active; use "
                "refund() for a ticket bought while logged in"
            )
        if non_member is None:
            raise KorailAuthError(
                f"KORAIL {operation} requires a non-member identity; call "
                "begin_non_member(name, phone) first"
            )
        return non_member

    def verify_offline_refund_ticket(
        self,
        return_number: OfflineRefundReturnNumber,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | OfflineRefundVerifyResponse:
        """비회원 오프라인 반환 1단계 — resolve a printed 반환번호.

        ``POST refunds.verifyOnlineRefunds`` (``RefundService.java:31-33``).
        THE NON-MEMBER, PAPER-TICKET PATH: no login, no PNR, no
        :class:`~korail_mobile_api.mutation_models.PaidTicket`. It is not
        related to :meth:`refund`, which refunds a ticket bought in-app while
        logged in, nor to :meth:`get_refund_ticket_detail` /
        :meth:`get_refund_commission`, which are that path's reads.

        Requires a held non-member identity
        (:meth:`~korail_mobile_api.session.KorailSessionClient.begin_non_member`)
        and refuses to run while a member session is active. The requester's
        name goes out as ``strName``, exactly as the app reads it off the
        ``requestorEdit`` box (``s5/c.java:71``).

        Gated by ``require_mutation_consent(consent, "refund")`` — the SAME
        category as :meth:`refund`, deliberately. It is the same product act on
        the same money; only the identity differs. It is consent-gated at all
        despite the app calling it 조회 (``strings.xml:1300``) because it
        converts a printed number into the four-part sale identity and the
        return password that :meth:`execute_offline_refund` then spends
        (``RefundVerifyTicketDao.java:119-122``), and because the 반환번호 it
        takes is a bearer credential that must never be guessable through an
        ungated path. Whether the server itself records anything at this step
        is NOT established from the APK.

        With the default ``dry_run=True`` it returns a
        :class:`~korail_mobile_api.consent.MutationPreview` in which the four
        return-number segments and the requester's name are all ``[REDACTED]``,
        and sends nothing.

        **NOT LIVE-VERIFIED.** Exercising it needs a real paper ticket.
        """
        require_mutation_consent(consent, "refund")
        non_member = self._require_non_member_identity(
            operation="offline refund verification"
        )
        route = "/classes/com.korail.mobile.refunds.verifyOnlineRefunds"
        form = build_offline_refund_verify_form(
            self.config,
            return_number,
            requester_name=non_member.non_member_name,
        )
        if consent.dry_run:
            return MutationPreview(
                category="refund",
                method="POST",
                route=route,
                payload=form,
            )
        return parse_offline_refund_verify_response(
            self.http.post_mutation_form(
                route,
                form,
                consent=consent,
                category="refund",
            ).raw
        )

    def execute_offline_refund(
        self,
        verified: OfflineRefundVerifyResponse,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | OfflineRefundExecuteResponse:
        """비회원 오프라인 반환 2단계 — book the 반환 접수 / refund the ticket.

        ``POST refunds.executeOnlineRefunds`` (``RefundService.java:15-17``).
        THE NON-MEMBER, PAPER-TICKET PATH; :meth:`refund` is the member one.
        This is the call that moves money.

        ``verified`` must be the response :meth:`verify_offline_refund_ticket`
        returned. The app takes nine of the twelve fields straight off it
        (``s5/h.java:114-125``), and so does
        :func:`~korail_mobile_api.mutation_payloads.build_offline_refund_execute_form`
        — the four-part sale identity is never re-assembled by hand.

        The requester's name and phone number come from the held non-member
        identity and go out as ``acepCustNm`` and ``custTeln``. (The app's own
        bundle key for the NAME is ``"CUSTOMER_NUMBER"``, ``s5/h.java:105,122``
        — a misleading name, not a different value.)

        Gated by ``require_mutation_consent(consent, "refund")``, the same
        category as :meth:`refund`. With the default ``dry_run=True`` it
        returns a :class:`~korail_mobile_api.consent.MutationPreview` with the
        PNR, the sale identity, the return password, the requester's name and
        the phone number all ``[REDACTED]``, and sends nothing.

        The result's :attr:`~korail_mobile_api.mutation_models.OfflineRefundExecuteResponse.is_refund_completed`
        distinguishes the two outcomes: money already returned versus 반환 접수
        accepted, with the paper ticket still to be handed in at a station
        within a year (``s5/h.java:187``; ``strings.xml:1292-1297``).

        **NOT LIVE-VERIFIED.**
        """
        require_mutation_consent(consent, "refund")
        non_member = self._require_non_member_identity(
            operation="offline refund execution"
        )
        route = "/classes/com.korail.mobile.refunds.executeOnlineRefunds"
        form = build_offline_refund_execute_form(
            self.config,
            verified,
            requester_name=non_member.non_member_name,
            requester_phone=non_member.non_member_phone,
        )
        if consent.dry_run:
            return MutationPreview(
                category="refund",
                method="POST",
                route=route,
                payload=form,
            )
        return parse_offline_refund_execute_response(
            self.http.post_mutation_form(
                route,
                form,
                consent=consent,
                category="refund",
            ).raw
        )

    def begin_non_member(
        self,
        name: str,
        phone: str,
        *,
        password: str | None = None,
    ) -> KorailNonMemberSession:
        """Hold a 비회원 identity for the non-member routes. Sends NOTHING.

        KORAIL has no non-member login endpoint: the app's 비회원 등록 screen
        only stores the values locally
        (``NonMemberRegisterActivity.java:66-73``) and re-sends them on every
        request. This does the same and performs no I/O, so it can never be
        mistaken for authentication.

        The result is a
        :class:`~korail_mobile_api.models.KorailNonMemberSession`, a DIFFERENT
        type from :class:`~korail_mobile_api.models.KorailSession` with no
        ``jsessionid`` field, kept in a different slot
        (``client.session.non_member`` rather than ``client.session.current``).
        Refuses while a member session is active; :meth:`login` and
        :meth:`clear_session` both drop it.
        """
        return self.session.begin_non_member(name, phone, password=password)

    def end_non_member(self) -> None:
        """Drop the held 비회원 identity, leaving any member session alone."""
        self.session.end_non_member()

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | DiscountCardPurchaseResponse:
        """Buy a 할인카드(N카드). Consent-gated, dry-run by default.

        ``POST research.dcntCrdInfo.do`` (``ResearchService.java:68-70``).
        Despite the "Info" in its path this is a PURCHASE: it answers with a
        ``lumpStlTgtNo`` and an ``rcvdAmt``
        (``NCardReservationDao.java:127-134``) and the app carries that target
        number straight into the payment screen
        (``SectionNCardInquiryActivity.java:213-257``). What it creates is an
        unpaid purchase awaiting settlement.

        Gated by ``require_mutation_consent(consent, "discount_card")`` and an
        authenticated session. ``"discount_card"`` is its own consent category,
        not a reuse of ``"reserve"``: nobody who opted into placing a train
        booking also opted into buying a product. With the default
        ``dry_run=True`` this builds and validates the form and returns a
        redacted :class:`~korail_mobile_api.consent.MutationPreview`, sending
        nothing.

        **VERIFIED: the route, the method, the four scalar field names, and the
        two ``@FieldMap`` key spellings, all from the DAO.**

        **NOT VERIFIED, and an operator must settle it before trusting a live
        call:** no call site in v6.5.0 populates ``jrnyInfo``/``apdUsrInfo`` —
        only the setters that would — so whether a 1-section card must still
        send a section, and whether ``apdUsrCnt`` must be present as ``"0"``
        for a 1인용 card rather than omitted, is unknown. Nothing here has ever
        been transmitted, and no live-test path in this repository sends it.
        """
        require_mutation_consent(consent, "discount_card")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL discount card purchase requires an authenticated "
                "session"
            )
        route = "/classes/com.korail.mobile.research.dcntCrdInfo.do"
        form = build_discount_card_purchase_form(self.config, request)
        if consent.dry_run:
            return MutationPreview(
                category="discount_card",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            return parse_discount_card_purchase_response(
                self.http.post_mutation_form(
                    route,
                    form,
                    consent=consent,
                    category="discount_card",
                ).raw
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def extend_discount_card(
        self,
        ticket: DiscountCardTicket,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """Extend a 할인카드's validity (기간연장). Consent-gated, dry-run.

        ``GET reservation.dcntCrdExtn.do`` (``ResearchService.java:65-66``) —
        a mutation the app performs with a GET, registered here with that
        method rather than coerced into the POST send path. It goes out through
        :meth:`~korail_mobile_api.http.KorailHttpClient.get_mutation_query`,
        which carries every gate ``post_mutation_form`` does.

        ``ticket`` is the card ticket's own four-part credential, which
        ``TicketListActivity.java:1067-1072`` reads off the N카드 row. Check
        :attr:`~korail_mobile_api.read_models.DiscountCardOnTicket.term_extension_possible_flag`
        first: the app enables the 기간연장 button only when it is ``"Y"``
        (``Y4/C0907b.java:301`` → ``Y4/Q.java:1013-1026``), and that gate is
        deliberately not duplicated in the builder because it is a property of
        the card rather than of the request.

        **NOT VERIFIED IN EITHER DIRECTION.** The DAO's response type is a bare
        ``BaseResponse`` (``ResearchService.java:65``), so what a successful
        extension answers with, and whether it costs money, is unknown. Nothing
        here has ever been transmitted, and no live-test path sends it.
        """
        require_mutation_consent(consent, "discount_card")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL discount card extension requires an authenticated "
                "session"
            )
        route = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"
        query = build_discount_card_extension_query(self.config, ticket)
        if consent.dry_run:
            return MutationPreview(
                category="discount_card",
                method="GET",
                route=route,
                payload=query,
            )
        try:
            return self.http.get_mutation_query(
                route,
                query,
                consent=consent,
                category="discount_card",
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def reserve_with_discount_card(
        self,
        train: TrainSummary,
        *,
        card_no: str,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationHoldResponse:
        """Hold one seat and pay for it with a 할인카드(N카드).

        **The same route, category and gate as :meth:`reserve`**, because it is
        the same call: ``w4/a.java:93-104`` builds an ordinary
        ``ReservationRequest`` and ``c5/b.java:128-138`` POSTs it with an
        ordinary ``ReservationDao`` to
        ``certification.TicketReservation``. There is no N카드 reservation
        endpoint; there is an N카드 passenger block. Consequently this is
        gated by ``require_mutation_consent(consent, "reserve")`` — a discount
        card does not make a reservation something other than a reservation,
        and a caller who has not opted into holding seats must not hold one
        this way either.

        ``card_no`` is
        :attr:`~korail_mobile_api.read_models.DiscountCardOnTicket.card_no`,
        from the N카드 ticket's own detail
        (:meth:`get_refund_ticket_detail`). ``train`` should be a row from
        :meth:`get_discount_card_schedule`, which is the search that knows
        which trains the card actually covers.

        There is no ``passengers`` and no ``seat_class`` argument, because the
        app offers neither: ``w4/a.java:97-98`` hardcodes one passenger and
        ``:88`` pins the cabin to 일반실.

        **NEVER TRANSMITTED, BY ANYONE HERE.** This is a reserve-surface
        addition derived entirely from the APK. What is verified is the route,
        the two fields that differ from an ordinary hold
        (``txtDiscKndCd1="153"``, ``txtCardNo_1``), the ``txtMenuId="A2"``, and
        that everything else is the byte-identical form the live-verified
        single-adult path already sends. What is NOT verified is that the
        server accepts it, or what it answers for an expired, spent or
        borrowed card. Treat a first live call as an experiment and be ready to
        release the hold with :meth:`cancel_unpaid_hold`.
        """
        require_mutation_consent(consent, "reserve")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL reservation requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_discount_card_reservation_form(
            self.config,
            train,
            card_no=card_no,
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

    def recalculate_price(
        self,
        request: PriceRecalculationRequest,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationHoldResponse:
        """Re-price a held PNR under a different set of discounts.

        ``POST certification.PriceReCalculation``
        (``CertificationService.java:35-37``, ``getDiscountPrice``). The app
        fires it from the payment screen whenever the discount selection
        changes for a reservation that already exists
        (``a6/C1042B.java:265-296``), and answers with the same
        ``ReservationResponse`` a hold returns — so what comes back is the
        re-priced booking, with :attr:`ReservationHoldResponse.received_amount`
        the new amount that would be settled.

        Gated by ``require_mutation_consent(consent, "price_recalculation")``
        and an authenticated session. That category is its own, and in
        particular is NOT ``"payment"``: a payment consent authorises settling
        an amount that has already been quoted, whereas this call rewrites the
        quote. With the default ``dry_run=True`` this builds and validates the
        form and returns a redacted
        :class:`~korail_mobile_api.consent.MutationPreview`, sending nothing.

        ``request.rows`` must carry one
        :class:`~korail_mobile_api.mutation_models.PriceRecalculationRow` per
        seat of the journey, in seat order — take
        ``passenger_type_code``/``room_class_code`` and the seat's existing
        discount code from
        :meth:`get_ticket_reservation_detail`, which reads the same PNR.

        This method does NOT reuse ``reserve``'s lenient hold-recovery parse.
        That fallback exists so a live hold can never be orphaned by a strict
        parse failing after the server already created it; nothing is created
        here, so a malformed response is just a malformed response and is
        raised.

        **VERIFIED FROM THE APK: the route, the method, all fourteen ``@Field``
        names, the index-alignment of the six lists, and the repeated-key
        encoding** — the last confirmed in ``smali/a6.1/B.smali`` and
        ``RequestBuilder.smali`` rather than taken from jadx.

        **NOT VERIFIED: anything the server does with it.** It has never been
        sent, by this package or under observation, and no live-test path
        reaches it. Sending it against a real held PNR changes what the
        passenger is about to be charged, so an operator must verify it against
        a hold they are willing to have re-priced.
        """
        require_mutation_consent(consent, "price_recalculation")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL price recalculation requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.certification.PriceReCalculation"
        form = build_price_recalculation_form(self.config, request)
        if consent.dry_run:
            return MutationPreview(
                category="price_recalculation",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            response = self.http.post_mutation_form(
                route,
                form,
                consent=consent,
                category="price_recalculation",
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise
        raw = response.raw if isinstance(response.raw, dict) else {}
        return parse_reservation_hold_response(raw)
