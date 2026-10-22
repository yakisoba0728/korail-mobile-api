# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""요청은 자동 재전송하지 않으며 변경 응답 파싱 실패도 서버 처리 실패를 뜻하지 않습니다."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from types import TracebackType
from typing import Any, Literal, Self, TypeVar

import httpx

from ._core.cleanup import _close_connections
from ._core.http import KorailHttpClient
from ._core.netfunnel import KorailNetFunnelClient, KorailNetFunnelGateName
from ._core.parsing import _preserve_read_raw
from ._core.session import KorailSessionClient
from ._domains.airport_bus.forms import (
    LimousineScheduleQuery,
    LimousineSeatInventoryQuery,
    MaasServiceDetailQuery,
    _build_ticket_maas_menu_form,
    build_limousine_reservation_form,
    build_limousine_schedule_form,
    build_limousine_seat_inventory_form,
    build_maas_menu_form,
    build_maas_service_detail_form,
    build_maas_station_form,
)
from ._domains.airport_bus.models import (
    LimousineSchedule,
    LimousineScheduleResponse,
    LimousineSeatInventoryResponse,
    MaasMenuListResponse,
    MaasServiceDetailListResponse,
)
from ._domains.airport_bus.parsers import (
    parse_limousine_schedule_response,
    parse_limousine_seat_inventory_response,
    parse_maas_menu_list_response,
    parse_maas_service_detail_list_response,
)
from ._domains.checkin.forms import (
    build_delivered_ticket_retrieval_form,
    build_delivery_recipient_form,
    build_pbp_acceptance_specification_form,
    build_recent_delivery_history_form,
    build_self_checkin_cancel_form,
    build_self_checkin_info_form,
    build_self_checkin_register_form,
    build_self_checkin_seat_check_form,
)
from ._domains.checkin.models import (
    DeliveredTicketRetrievalResponse,
    DeliveryRecipientResponse,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
    RecentDeliveryHistoryResponse,
    SelfCheckInCancelResponse,
    SelfCheckInInfoResponse,
    SelfCheckInRegisterResponse,
    SelfCheckInSeat,
    SelfCheckInSeatCheckResponse,
)
from ._domains.checkin.parsers import (
    parse_delivered_ticket_retrieval_response,
    parse_delivery_recipient_response,
    parse_pbp_acceptance_specification_response,
    parse_recent_delivery_history_response,
    parse_self_checkin_cancel_response,
    parse_self_checkin_info_response,
    parse_self_checkin_register_response,
    parse_self_checkin_seat_check_response,
)
from ._domains.common.forms import (
    build_cache_query,
    build_common_code_form,
)
from ._domains.common.models import (
    AppDataResponse,
    BaseKorailResponse,
    CrewRequestListResponse,
    KorailSession,
    NoticeResponse,
    ServiceStatusResponse,
    StationDataResponse,
    StationInfoResponse,
    TrainCalendarResponse,
    UuidResponse,
)
from ._domains.common.parsers import (
    parse_app_data_response,
    parse_crew_request_list_response,
    parse_service_status_response,
    parse_station_data_response,
    parse_station_info_response,
    parse_train_calendar_response,
    parse_uuid_response,
    resolve_station_name,
)
from ._domains.passes.forms import (
    CommuterInfoRequest,
    DiscountCardPurchaseRequest,
    DiscountCardScheduleRequest,
    DiscountCardTicket,
    PassScheduleRequest,
    build_commuter_info_form,
    build_commuter_kind_menu_query,
    build_discount_card_extension_query,
    build_discount_card_purchase_form,
    build_discount_card_reservation_form,
    build_discount_card_schedule_query,
    build_discount_card_usage_query,
    build_pass_availability_form,
    build_pass_menu_form,
    build_pass_schedule_form,
    build_product_cancel_query,
    build_product_detail_query,
    build_product_reservations_query,
    build_trip_menu_form,
)
from ._domains.passes.models import (
    CommuterInfoResponse,
    CommuterKindMenuResponse,
    DiscountCardPurchaseResponse,
    DiscountCardScheduleResponse,
    DiscountCardUsageListResponse,
    PassAvailabilityResponse,
    PassMenuResponse,
    PassScheduleResponse,
    ProductCancelResponse,
    ProductDetailResponse,
    ProductReservationListResponse,
    TripMenuResponse,
)
from ._domains.passes.parsers import (
    parse_commuter_info_response,
    parse_commuter_kind_menu_response,
    parse_discount_card_purchase_response,
    parse_discount_card_schedule_response,
    parse_discount_card_usage_response,
    parse_pass_availability_response,
    parse_pass_menu_response,
    parse_pass_schedule_response,
    parse_product_cancel_response,
    parse_product_detail_response,
    parse_product_reservation_list_response,
    parse_trip_menu_response,
)
from ._domains.payments.forms import (
    CardPayment,
    PaidTicket,
    PriceRecalculationRequest,
    RefundCompanion,
    StationRefundExecutionRequest,
    StationRefundVerificationRequest,
    build_card_payment_form,
    build_price_recalculation_form,
    build_refund_commission_form,
    build_refund_form,
    build_refund_ticket_detail_form,
    build_station_refund_execution_form,
    build_station_refund_verification_form,
)
from ._domains.payments.models import (
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketResponse,
    ReservationPaymentResponse,
    StationRefundExecutionResponse,
    StationRefundVerificationResponse,
    _RefundCommissionContext,
)
from ._domains.payments.parsers import (
    parse_refund_commission_response,
    parse_refund_ticket_detail_response,
    parse_refund_ticket_response,
    parse_reservation_payment_response,
    parse_station_refund_execution_response,
    parse_station_refund_verification_response,
)
from ._domains.reservations.forms import (
    CartAddRequest,
    KorailPassengerCounts,
    KorailSeatAssignment,
    TicketDuplicationCheckRequest,
    TicketReservationDetailRequest,
    build_cart_add_form,
    build_cart_list_form,
    build_merge_reservation_form,
    build_reservation_form,
    build_standby_wait_form,
    build_ticket_duplication_check_form,
    build_ticket_reservation_detail_query,
    build_transfer_reservation_form,
    build_unpaid_reservation_cancel_form,
)
from ._domains.reservations.models import (
    CartAddResponse,
    CartListResponse,
    ReservationHistoryResponse,
    ReservationHoldResponse,
    TicketDuplicationCheckResponse,
    TicketReservationDetailResponse,
)
from ._domains.reservations.parsers import (
    parse_cart_add_response,
    parse_cart_list_response,
    parse_existing_reservation_hold_response,
    parse_reservation_history_response,
    parse_reservation_hold_response,
    parse_ticket_duplication_check_response,
    parse_ticket_reservation_detail_response,
)
from ._domains.tickets.forms import (
    MileageHistoryRequest,
    OriginalTicketReference,
    SelfSeatChangeInfoRequest,
    build_customer_trip_info_form,
    build_delay_certificate_form,
    build_delay_discount_ticket_form,
    build_delay_return_receipt_form,
    build_discount_coupon_form,
    build_korail_point_summary_form,
    build_mileage_history_form,
    build_multi_child_discount_target_form,
    build_original_ticket_inquiry_form,
    build_self_seat_change_info_form,
    build_ticket_list_form,
    build_ticket_receipt_form,
    build_trip_change_date_form,
)
from ._domains.tickets.models import (
    CustomerTripInfoResponse,
    DelayCertificateResponse,
    DelayDiscountTicketListResponse,
    DelayReturnReceiptResponse,
    DepositBankListResponse,
    DiscountCouponListResponse,
    KorailPointSummaryResponse,
    MileageHistoryResponse,
    MultiChildDiscountTargetResponse,
    OriginalTicketInquiryResponse,
    SelfSeatChangeInfoResponse,
    TicketListResponse,
    TicketReceiptResponse,
    TripChangeDateResponse,
)
from ._domains.tickets.parsers import (
    parse_customer_trip_info_response,
    parse_delay_certificate_response,
    parse_delay_discount_ticket_response,
    parse_delay_return_receipt_response,
    parse_deposit_bank_response,
    parse_discount_coupon_response,
    parse_korail_point_summary_response,
    parse_mileage_history_response,
    parse_multi_child_discount_target_response,
    parse_original_ticket_inquiry_response,
    parse_self_seat_change_info_response,
    parse_ticket_list_response,
    parse_ticket_receipt_response,
    parse_trip_change_date_response,
)
from ._domains.trains.forms import (
    FreeSeatCarRequest,
    GuideSeatConditionRequest,
    MergeSeatsInquiryRequest,
    PriceFareQuoteRequest,
    SeatAssignmentScheduleRequest,
    build_free_seat_car_form,
    build_guide_seat_condition_form,
    build_merge_seats_inquiry_form,
    build_price_fare_quote_form,
    build_seat_assignment_schedule_form,
    build_seat_car_form,
    build_seat_inventory_form,
    build_train_schedule_form,
    build_train_search_form,
    validate_train_search_query,
)
from ._domains.trains.models import (
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    MergeSeatsInquiryResponse,
    PriceFareQuoteResponse,
    SeatAssignmentScheduleResponse,
    SeatCarListResponse,
    SeatInventoryResponse,
    TrainScheduleItem,
    TrainScheduleResponse,
    TrainSearchContinuation,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
    TransferSearchResult,
    TransferStationListResponse,
    pair_transfer_itineraries,
)
from ._domains.trains.parsers import (
    parse_free_seat_car_response,
    parse_guide_seat_condition_response,
    parse_merge_seats_inquiry_response,
    parse_price_fare_quote_response,
    parse_seat_assignment_schedule_response,
    parse_seat_car_list_response,
    parse_seat_inventory_response,
    parse_train_rows,
    parse_train_schedule_response,
    parse_train_search_metadata,
    parse_transfer_station_list_response,
)
from .config import KorailConfig
from .constants import KorailLoginInputFlag, KorailReservationJobType, KorailRoomClassCode, KorailSeatClass
from .errors import (
    KorailApiError,
    KorailAuthError,
    KorailInvalidInputError,
    KorailNoDirectTrainError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
)

T = TypeVar("T")


def _note_possible_processing(error: KorailApiError) -> None:
    if error.request_sent:
        error.add_note("KORAIL may have processed this request; check its state before sending it again")


def _hold_for_job(hold: ReservationHoldResponse, job_type: KorailReservationJobType) -> ReservationHoldResponse:
    # 앱은 예약대기 홀드를 결제하지 않습니다.
    if KorailReservationJobType(job_type) is KorailReservationJobType.STANDBY:
        return replace(hold, payable=False)
    return hold


class KorailClient:
    """KORAIL 코레일+ 앱 7.0.8의 확인된 요청 계약을 따르는 비공식 동기 클라이언트입니다.

    ``config``를 생략하면 기본값으로 만든 ``KorailConfig``를 쓰며, 기본 설정에서는 DynaPath와 대기열이 켜져 있습니다.
    ``transport``에 넣은 ``httpx`` 전송 계층은 KORAIL API 요청과 대기열 요청에 함께 쓰입니다. ``config.proxy``와 함께 넘기면
    ``ValueError``가 발생합니다. 예약·결제·환불처럼 서버
    상태를 바꾸는 메서드는 호출하는 즉시 요청을 보내며, 실패해도 KORAIL API 요청을 자동으로 다시 보내지 않습니다. 다 쓴
    뒤에는 ``close``를 호출해 연결을 닫으세요. ``with`` 문으로 쓰면 블록이 끝날 때 닫습니다."""

    # 안전한 사용과 한계는 checks/BEHAVIOR.md 를 따릅니다.

    def __init__(
        self,
        config: KorailConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        try:
            self.netfunnel = (
                KorailNetFunnelClient(self.config, transport=transport)
                if self.config.netfunnel_enabled
                else None
            )
        except BaseException as error:
            _close_connections(self.http.close, primary=error)
            raise
        self.session = KorailSessionClient(self.http)
        self._station_data: StationDataResponse | None = None
        self._station_names: dict[str, str] | None = None

    def close(self) -> None:
        """HTTP·대기열 연결 풀을 닫습니다. 서버 로그아웃은 하지 않습니다."""
        closers = (self.http.close,) if self.netfunnel is None else (self.http.close, self.netfunnel.close)
        _close_connections(*closers)

    def __enter__(self) -> Self:
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
        """기존 세션을 비운 뒤 서비스 상태·암호화 키를 읽고 로그인합니다."""
        return self.session.login(
            member_no,
            password,
            input_flag=input_flag,
            check_valid_pw=check_valid_pw,
            cust_id=cust_id,
            etr_path=etr_path,
        )

    def clear_session(self) -> None:
        """서버에 알리지 않고 로컬 로그인 상태(쿠키·세션)만 버립니다."""
        self.session.clear_session()

    def logout(self) -> None:
        """로그인 상태이면 서버에 로그아웃을 보내고, 어느 경우든 로컬 세션·쿠키를 비웁니다."""
        self.session.logout()

    def _run_read(self, operation: Callable[[], T]) -> T:
        try:
            return operation()
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def _queued(self, gate: KorailNetFunnelGateName, send: Callable[[], T]) -> T:
        if self.netfunnel is None:
            return send()
        return self.netfunnel.run(gate, send)

    @staticmethod
    def _inquiry_gate(*, peak_season: bool, special: bool = False) -> KorailNetFunnelGateName:
        """앱이 열차 조회에 쓰는 대기열 관문을 고릅니다."""
        if special:
            return "product_inquiry"
        return "peak_season_inquiry" if peak_season else "inquiry"

    def _require_session(self, what: str = "account read requires") -> None:
        """세션이 없으면 요청 전에 인증 오류를 냅니다. 앱에는 없는 라이브러리 검사입니다(서버라면 P058 로 답합니다)."""
        if self.session.current is None:
            raise KorailAuthError(f"KORAIL {what} an authenticated session")

    def _require_customer_no(self, what: str) -> str:
        self._require_session()
        session = self.session.current
        customer_no = session.customer_no if session is not None else None
        if not isinstance(customer_no, str) or not customer_no.strip():
            raise KorailAuthError(f"KORAIL {what} requires a login customer number")
        return customer_no

    def _post_read(
        self,
        route: str,
        form: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        *,
        parser: Callable[[Mapping[str, object]], T],
        include_common: bool = True,
        require_envelope: bool = True,
        raise_on_fail: bool = True,
        omit_empty_fields: bool = True,
        form_encoded: bool = True,
    ) -> T:
        """자동 재로그인·재전송은 하지 않습니다."""
        return self._run_read(
            lambda: parser(
                self.http.post_form(
                    route,
                    form,
                    include_common=include_common,
                    require_envelope=require_envelope,
                    raise_on_fail=raise_on_fail,
                    omit_empty_fields=omit_empty_fields,
                    form_encoded=form_encoded,
                ).raw
            )
        )

    def _get_read(
        self,
        route: str,
        params: Mapping[str, Any] | None = None,
        *,
        parser: Callable[[Mapping[str, object]], T],
        require_envelope: bool = True,
        include_common: bool = True,
        omit_empty_fields: bool = False,
    ) -> T:
        return self._run_read(
            lambda: parser(
                self.http.get_json(
                    route,
                    params,
                    include_common=include_common,
                    require_envelope=require_envelope,
                    omit_empty_fields=omit_empty_fields,
                ).raw
            )
        )

    def _mutation(
        self,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: Callable[[Mapping[str, object]], T],
        raise_on_fail: bool = True,
    ) -> T:
        return self._send_mutation(
            lambda: self.http.post_form(route, form, include_common=False, raise_on_fail=raise_on_fail),
            parser,
        )

    def _send_mutation(
        self,
        send: Callable[[], BaseKorailResponse],
        parser: Callable[[Mapping[str, object]], T],
    ) -> T:
        """파싱 실패만으로 서버 변경 여부를 알 수 없으므로 상태 확인 없이 재전송하지 마십시오."""
        try:
            return self._parse_mutation_response(self._run_read(send).raw, parser)
        except (KorailTransportError, KorailProtocolError) as error:
            _note_possible_processing(error)
            raise

    @staticmethod
    @_preserve_read_raw
    def _parse_mutation_response(
        raw: Mapping[str, object],
        parser: Callable[[Mapping[str, object]], T],
    ) -> T:
        """POST·GET 변경 및 환불 검증의 파싱 오류에 전체 응답을 보존합니다. 재전송하지 않습니다."""
        try:
            return parser(raw)
        except KorailProtocolError as error:
            error.request_sent = True
            raise
        except KorailApiError:
            raise
        except Exception as error:
            # 패키지 밖 예외도 원문을 붙인 KorailProtocolError로 감싸며 재전송하지 않습니다.
            wrapped = KorailProtocolError(
                f"KORAIL response was received but could not be parsed: {type(error).__name__}", raw=raw
            )
            wrapped.request_sent = True
            raise wrapped from error

    def get_seat_cars(
        self,
        train: TrainSummary,
        *,
        passenger_count: int = 1,
        room_class_code: KorailRoomClassCode = "1",
        seat_attribute_code: str | None = None,
    ) -> SeatCarListResponse:
        """좌석지정 화면이 쓰는 한 열차의 호차 목록을 조회합니다."""
        self._require_session()
        form = build_seat_car_form(
            self.config,
            train,
            passenger_count=passenger_count,
            room_class_code=room_class_code,
            seat_attribute_code=seat_attribute_code,
        )
        return self._post_read(
            "/classes/com.korail.mobile.research.TrainResearch",
            form,
            parser=parse_seat_car_list_response,
            include_common=False,
        )

    def get_seat_inventory(
        self,
        train: TrainSummary,
        car_no: int,
        *,
        passenger_count: int = 1,
        room_class_code: KorailRoomClassCode = "1",
        seat_attribute_code: str | None = None,
    ) -> SeatInventoryResponse:
        """한 호차의 좌석 배치와 판매 가능 여부를 조회합니다(같은 세션에서 get_seat_cars 를 먼저 부르십시오)."""
        self._require_session()
        form = build_seat_inventory_form(
            self.config,
            train,
            car_no,
            passenger_count=passenger_count,
            room_class_code=room_class_code,
            seat_attribute_code=seat_attribute_code,
        )
        return self._post_read(
            "/classes/com.korail.mobile.research.TResidualSeatsResearch.do",
            form,
            parser=parse_seat_inventory_response,
            include_common=False,
        )

    def get_limousine_schedules(
        self,
        query: LimousineScheduleQuery,
    ) -> LimousineScheduleResponse:
        """리무진 연계 구간의 운행 스케줄 한 페이지를 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.lmu.scdlQry.do",
            build_limousine_schedule_form(self.config, query),
            parser=parse_limousine_schedule_response,
            include_common=False,
        )

    def get_limousine_seat_inventory(
        self,
        query: LimousineSeatInventoryQuery,
    ) -> LimousineSeatInventoryResponse:
        """리무진 연계 편 한 호차의 좌석 점유 상태를 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do",
            build_limousine_seat_inventory_form(self.config, query),
            parser=parse_limousine_seat_inventory_response,
            include_common=False,
        )

    def get_service_status(
        self,
        timestamp_ms: int | None = None,
    ) -> ServiceStatusResponse:
        """예매 서비스가 열려 있는지를 서버 봉투로 확인합니다."""
        return self._post_read(
            "/file/CACHE/MobileService.cache",
            build_cache_query(timestamp_ms),
            parser=parse_service_status_response,
            include_common=False,
        )

    def get_cart_list(
        self,
        pnr_no: str = "",
        additional_service_request_no: str = "",
    ) -> CartListResponse:
        """로그인 계정의 장바구니를 조회합니다."""
        self._require_session()
        form = build_cart_list_form(
            pnr_no,
            additional_service_request_no,
        )
        return self._post_read(
            "/classes/com.korail.mobile.cart.showCartList",
            form,
            parser=parse_cart_list_response,
            require_envelope=False,
        )

    def get_deposit_banks(self) -> DepositBankListResponse:
        """입금 가능한 은행의 코드와 이름 목록을 조회합니다."""
        self._require_session()
        # 공통 DTO 가 아닌 개별 필드라 Device·Version·Key·AppVersion 순서이고 lang 이 없습니다.
        form = {"Device": self.config.device, "Version": self.config.version, "Key": self.config.key}
        if self.config.app_version is not None:
            form["AppVersion"] = self.config.app_version
        return self._post_read(
            "/classes/com.korail.mobile.dlay.dptnBank.do",
            form,
            parser=parse_deposit_bank_response,
            include_common=False,
            omit_empty_fields=False,
        )

    def get_delay_discount_tickets(
        self,
        departure_date_to: str,
    ) -> DelayDiscountTicketListResponse:
        """계정의 지연할인권 목록을 조회합니다."""
        self._require_session()
        return self._run_read(
            lambda: parse_delay_discount_ticket_response(
                self.http.post_query(
                    "/classes/com.korail.mobile.passCard.DelayDiscountView",
                    build_delay_discount_ticket_form(departure_date_to),
                    omit_empty_fields=True,
                    require_envelope=False,
                ).raw
            )
        )

    def get_discount_coupons(
        self,
        page_no: int = 1,
        pnr_no: str = "",
    ) -> DiscountCouponListResponse:
        """계정의 할인쿠폰 한 페이지를 조회합니다(보유분이 없으면 빈 결과)."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.passCard.CouponView",
            build_discount_coupon_form(page_no, pnr_no),
            parser=parse_discount_coupon_response,
            raise_on_fail=False,
        )

    def get_korail_point_summary(self) -> KorailPointSummaryResponse:
        """계정의 포인트·쿠폰·복지 자격 요약을 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.xPoint.MyXPointView",
            build_korail_point_summary_form(),
            parser=parse_korail_point_summary_response,
        )

    def get_mileage_history(
        self,
        request: MileageHistoryRequest,
    ) -> MileageHistoryResponse:
        """마일리지 적립/사용 내역 한 페이지를 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.mlg.amtSpec.do",
            build_mileage_history_form(request),
            parser=parse_mileage_history_response,
        )

    def get_discount_card_usage_history(
        self,
        card_no: str,
    ) -> DiscountCardUsageListResponse:
        """할인카드(N카드) 한 장의 사용 내역을 조회합니다. 검증 못 함: N카드가 없는 계정이라 성공 응답을 보지 못했습니다."""
        self._require_session()
        query = build_discount_card_usage_query(card_no)
        return self._post_read(
            "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do",
            query,
            parser=parse_discount_card_usage_response,
        )

    def get_discount_card_schedule(
        self,
        request: DiscountCardScheduleRequest,
    ) -> DiscountCardScheduleResponse:
        """할인카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회합니다. 검증 못 함: N카드가 없는 계정이라 성공 응답을 보지 못했습니다."""
        self._require_session()
        query = build_discount_card_schedule_query(request)
        return self._post_read(
            "/classes/com.korail.mobile.research.dcntCrdScheduleView.do",
            query,
            parser=parse_discount_card_schedule_response,
        )

    def get_pass_available_dates(
        self,
        kind_code: str,
        period_code: str,
        age_code: str,
    ) -> PassAvailabilityResponse:
        """정기권 상품 하나의 사용 개시 가능일과 발권 가능일을 조회합니다."""
        form = build_pass_availability_form(
            kind_code,
            period_code,
            age_code,
        )
        return self._post_read(
            "/classes/com.korail.mobile.pass.passInfoList",
            form,
            parser=parse_pass_availability_response,
            require_envelope=False,
        )

    def get_pass_schedule(
        self,
        request: PassScheduleRequest,
    ) -> PassScheduleResponse:
        """정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회합니다(WRG000000 은 빈 결과)."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.pass.passScheduleInfoList",
            build_pass_schedule_form(request),
            parser=parse_pass_schedule_response,
            raise_on_fail=False,
        )

    def get_trip_menu(self) -> TripMenuResponse:
        """여행상품 메뉴 화면에 그릴 항목과 그 안의 문구 묶음을 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.pass.trGdMenuLt.do",
            build_trip_menu_form(self.config),
            parser=parse_trip_menu_response,
        )

    def get_pass_menu(self, menu_no: str) -> PassMenuResponse:
        """정기권·패스 메뉴 한 갈래의 화면 구성 항목을 조회합니다."""
        form = build_pass_menu_form(menu_no)
        return self._post_read(
            "/classes/com.korail.mobile.pass.passMenu.do",
            form,
            parser=parse_pass_menu_response,
            require_envelope=False,
        )

    def get_crew_request_list(
        self,
        *,
        timestamp_ms: int | None = None,
    ) -> CrewRequestListResponse:
        """승무원 호출 화면의 요청 사유 선택지를 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.push.crwCallRq.do",
            build_cache_query(timestamp_ms),
            parser=parse_crew_request_list_response,
        )

    def get_commuter_kind_menu(
        self,
        commuter_kind_code: str,
    ) -> CommuterKindMenuResponse:
        """정기권 종류 하나의 안내 문구와 조회 파라미터를 받아 옵니다."""
        query = build_commuter_kind_menu_query(commuter_kind_code)
        return self._get_read(
            "/classes/com.korail.mobile.push.cmtrKnd.do",
            {
                "Device": self.config.device,
                "Version": self.config.version,
                "Key": self.config.key,
                **query,
            },
            parser=parse_commuter_kind_menu_response,
            include_common=False,
        )

    def get_product_reservations(
        self,
        page_no: int = 1,
        page_size: int = 20,
        *,
        reservation_status_code: str | None = None,
        payment_status_code: str | None = None,
    ) -> ProductReservationListResponse:
        """로그인 계정이 예약한 여행상품 목록 한 페이지를 조회합니다."""
        self._require_session()
        query = build_product_reservations_query(
            page_no,
            page_size,
            reservation_status_code=reservation_status_code,
            payment_status_code=payment_status_code,
        )
        return self._get_read(
            "/classes/com.korail.mobile.product.ReservationList",
            query,
            omit_empty_fields=True,
            parser=parse_product_reservation_list_response,
            require_envelope=False,
        )

    def get_product_detail(
        self,
        reservation_no: str,
        reservation_sequence: str | None = None,
    ) -> ProductDetailResponse:
        """여행상품 예약 한 건의 상세와 취소 조건을 조회합니다."""
        self._require_session()
        query = build_product_detail_query(
            reservation_no,
            reservation_sequence,
        )
        return self._get_read(
            "/classes/com.korail.mobile.product.ReservationDetail",
            query,
            omit_empty_fields=True,
            parser=parse_product_detail_response,
        )

    def cancel_product_reservation(self, detail: ProductDetailResponse) -> ProductCancelResponse:
        """여행상품 예약을 취소합니다.

        결제된 상품이면 환불이 실행되므로 get_product_detail 의 수수료를 먼저 확인하고, 실패해도 다시 보내지 마십시오."""
        self._require_session("product cancel requires")
        query = build_product_cancel_query(detail)
        return self._send_mutation(
            lambda: self.http.get_json(
                "/classes/com.korail.mobile.product.ReservationCancel",
                query,
                include_common=True,
            ),
            parse_product_cancel_response,
        )

    def get_ticket_receipt(
        self,
        *,
        sale_date: str,
        window_no: str,
        sale_sequence: str,
        return_password: str,
        txt_index: str | None = None,
    ) -> TicketReceiptResponse:
        """승차권 한 장의 영수증과 결제수단을 조회합니다."""
        self._require_session()
        form = build_ticket_receipt_form(
            sale_date,
            window_no,
            sale_sequence,
            return_password,
            txt_index,
        )
        return self._post_read(
            "/classes/com.korail.mobile.receipt.ReceiptInfo",
            form,
            parser=parse_ticket_receipt_response,
        )

    def get_reservation_history(self) -> ReservationHistoryResponse:
        """로그인 계정에 아직 살아 있는 예약(미결제 홀드 포함)을 조회합니다."""
        self._require_session()
        return self._queued(
            "reservation_view",
            lambda: self._post_read(
                "/classes/com.korail.mobile.reservation.ReservationView",
                {"timeStamp": 0},
                parser=parse_reservation_history_response,
                raise_on_fail=False,
            ),
        )

    def get_free_seat_car_info(
        self,
        request: FreeSeatCarRequest,
    ) -> FreeSeatCarResponse:
        """한 열차의 자유석 호차 안내 문구를 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.trn.fresScar.do",
            build_free_seat_car_form(request),
            parser=parse_free_seat_car_response,
        )

    def get_guide_seat_condition(
        self,
        request: GuideSeatConditionRequest,
    ) -> GuideSeatConditionResponse:
        """도우미석 안내문을 읽습니다."""
        return self._post_read(
            "/classes/com.korail.mobile.reservation.guideSeatCnd.do",
            build_guide_seat_condition_form(request),
            parser=parse_guide_seat_condition_response,
            raise_on_fail=False,
        )

    def get_seat_assignment_schedule(
        self,
        request: SeatAssignmentScheduleRequest,
        *,
        peak_season: bool = False,
    ) -> SeatAssignmentScheduleResponse:
        """좌석배정 예매 화면의 열차 목록을 조회합니다."""
        return self._queued(
            self._inquiry_gate(peak_season=peak_season),
            lambda: self._post_read(
                "/classes/com.korail.mobile.research.assignScheduleView.do",
                build_seat_assignment_schedule_form(request),
                parser=parse_seat_assignment_schedule_response,
            ),
        )

    def get_merge_seats_inquiry(
        self,
        request: MergeSeatsInquiryRequest,
    ) -> MergeSeatsInquiryResponse:
        """좌석 병합이 가능한 열차와 좌석이 갈리는 중간역을 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.research.mergeSeatsC.do",
            build_merge_seats_inquiry_form(request),
            parser=parse_merge_seats_inquiry_response,
        )

    def get_multi_child_discount_targets(
        self,
        departure_date: str,
    ) -> MultiChildDiscountTargetResponse:
        """다자녀 할인 대상으로 등록된 가족 구성원을 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.cust.mchdDcntTgt.do",
            build_multi_child_discount_target_form(departure_date),
            parser=parse_multi_child_discount_target_response,
        )

    def get_customer_trip_info(self) -> CustomerTripInfoResponse:
        """로그인 계정에 저장된 여행 편의설정을 조회합니다."""
        customer_no = self._require_customer_no("customer trip read")
        return self._post_read(
            "/classes/com.korail.mobile.research.custTripInfo.do",
            build_customer_trip_info_form(customer_no),
            parser=parse_customer_trip_info_response,
        )

    def get_maas_service_details(
        self,
        query: MaasServiceDetailQuery | None = None,
    ) -> MaasServiceDetailListResponse:
        """계정이 신청한 MaaS 부가서비스 내역을 조회합니다."""
        self._require_session()
        resolved_query = query if query is not None else MaasServiceDetailQuery.current()
        return self._post_read(
            "/classes/com.korail.mobile.copt.gdReqQry.do",
            build_maas_service_detail_form(self.config, resolved_query),
            parser=parse_maas_service_detail_list_response,
            include_common=False,
        )

    def get_trip_change_dates(
        self,
        departure_date: str,
    ) -> TripChangeDateResponse:
        """승차권 변경으로 옮겨 갈 수 있는 날짜 목록을 조회합니다."""
        self._require_session()
        return self._get_read(
            "/classes/com.korail.mobile.reservation.tripChgDate.do",
            build_trip_change_date_form(departure_date),
            omit_empty_fields=True,
            parser=parse_trip_change_date_response,
        )

    def get_commuter_info(
        self,
        request: CommuterInfoRequest,
    ) -> CommuterInfoResponse:
        """정기권 예매에 필요한 조건을 세 단계 중 하나로 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.research.cmtrInfo.do",
            build_commuter_info_form(request),
            parser=parse_commuter_info_response,
        )

    def get_price_fare_quote(
        self,
        request: PriceFareQuoteRequest,
    ) -> PriceFareQuoteResponse:
        """열차 한두 편의 표시용 운임을 예매 전에 받습니다(결제액은 홀드의 received_amount)."""
        form = build_price_fare_quote_form(request)
        # 앱은 빈 값을 뺀 뒤 운임 여덟 칸을 직접 넣으므로 빈 gdNo 도 보냅니다.
        return self._post_read(
            "/classes/com.korail.mobile.trn.prcFare.do",
            form,
            parser=parse_price_fare_quote_response,
            omit_empty_fields=False,
        )

    def get_delivery_recipient(
        self,
        ticket: OriginalTicketReference,
    ) -> DeliveryRecipientResponse:
        """N카드 2인 승차권의 전달 전 수령자 후보를 조회합니다. 검증 못 함: 채워진 수령자 응답을 보지 못했습니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.tk.dlvRcvCust.do",
            build_delivery_recipient_form(ticket),
            parser=parse_delivery_recipient_response,
        )

    def check_ticket_duplication(
        self,
        request: TicketDuplicationCheckRequest,
    ) -> TicketDuplicationCheckResponse:
        """같은 PNR 로 이미 잡혀 있는 예약이 몇 건인지 셉니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.ticket.ticketDupCheck.do",
            build_ticket_duplication_check_form(request),
            parser=parse_ticket_duplication_check_response,
        )

    def get_pbp_acceptance_specifications(
        self,
        tickets: Sequence[OriginalTicketReference],
    ) -> PbpAcceptanceSpecificationResponse:
        """승차권 여러 장의 PBP 수락 내역을 여정·좌석 단위로 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.tk.pbpAcepSpec.do",
            build_pbp_acceptance_specification_form(tickets),
            parser=parse_pbp_acceptance_specification_response,
        )

    def retrieve_delivered_ticket(self, ticket: PbpAcceptanceTicket) -> DeliveredTicketRetrievalResponse:
        """다른 회원에게 전달한 승차권을 회수합니다.

        상태를 바꾸므로 실패해도 다시 보내지 말고 승차권 상태를 확인하십시오(실서버 검증 못 함)."""
        self._require_session()
        return self._mutation(
            "/classes/com.korail.mobile.tk.pbpWdrw.do",
            build_delivered_ticket_retrieval_form(self.config, ticket),
            parser=parse_delivered_ticket_retrieval_response,
        )

    def get_original_ticket_inquiry(
        self,
        tickets: Sequence[OriginalTicketReference],
        *,
        ticket_count: int | None = None,
    ) -> OriginalTicketInquiryResponse:
        """승차권 변경의 출발점이 되는 원표(원승차권)를 조회합니다."""
        self._require_session()
        form = build_original_ticket_inquiry_form(
            tickets,
            ticket_count=ticket_count,
        )
        return self._post_read(
            "/classes/com.korail.mobile.research.tripChgOgtk.do",
            form,
            parser=parse_original_ticket_inquiry_response,
        )

    def get_self_seat_change_info(
        self,
        request: SelfSeatChangeInfoRequest,
    ) -> SelfSeatChangeInfoResponse:
        """자율 좌석·열차 변경으로 갈 수 있는 승차역과 변경 사유를 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.self.seatChgInfo.do",
            build_self_seat_change_info_form(request),
            parser=parse_self_seat_change_info_response,
        )

    def get_recent_delivery_history(self) -> RecentDeliveryHistoryResponse:
        """최근에 승차권을 전달했던 수령자 목록을 조회합니다."""
        customer_no = self._require_customer_no("delivery history read")
        return self._post_read(
            "/classes/com.korail.mobile.tk.rcntDlvHst.do",
            build_recent_delivery_history_form(customer_no),
            parser=parse_recent_delivery_history_response,
        )

    def get_ticket_reservation_detail(
        self,
        request: TicketReservationDetailRequest,
    ) -> TicketReservationDetailResponse:
        """홀드된 예약 하나의 여정·좌석 상세를 PNR 로 되읽습니다."""
        self._require_session()
        query = build_ticket_reservation_detail_query(request)
        return self._post_read(
            "/classes/com.korail.mobile.certification.ReservationList",
            query,
            parser=parse_ticket_reservation_detail_response,
        )

    def get_reservation_hold(self, pnr_no: str) -> ReservationHoldResponse:
        """이미 잡힌 예약을 PNR 로 조회해 카드 결제용 홀드로 가져옵니다. 결제는 하지 않습니다."""
        detail = self.get_ticket_reservation_detail(TicketReservationDetailRequest(pnr_no))
        return parse_existing_reservation_hold_response(detail.raw, pnr_no=pnr_no)

    def get_refund_commission(
        self,
        ticket: OriginalTicketReference,
        companion: RefundCompanion = RefundCompanion(),
    ) -> RefundCommissionResponse:
        """승차권 한 장의 예상 환불액과 수수료를 조회하고, refund 가 대조할 조회 대상을 결과에 연결합니다."""
        self._require_session()
        response = self._post_read(
            "/classes/com.korail.mobile.refunds.CommissionView",
            build_refund_commission_form(ticket, companion),
            parser=parse_refund_commission_response,
        )
        return replace(
            response,
            _request_context=_RefundCommissionContext(
                ticket.sale_window_no,
                ticket.sale_date,
                ticket.sale_sequence,
                ticket.return_password,
                companion.name,
                companion.certificate_no,
            ),
        )

    def get_refund_ticket_detail(
        self,
        ticket: OriginalTicketReference,
        *,
        from_purchase_history: bool = False,
        txt_index: str | None = None,
    ) -> RefundTicketDetailResponse:
        """환불 대상 승차권의 여정·좌석·운임 상세를 조회합니다."""
        self._require_session()
        form = build_refund_ticket_detail_form(
            ticket,
            from_purchase_history=from_purchase_history,
            txt_index=txt_index,
        )
        return self._post_read(
            "/classes/com.korail.mobile.refunds.SelTicketInfo",
            form,
            parser=parse_refund_ticket_detail_response,
        )

    def get_delay_certificate(self, ticket: OriginalTicketReference) -> DelayCertificateResponse:
        """지연된 승차권의 지연확인증(도착 지연 분)을 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.dlay.athnIsu.do",
            build_delay_certificate_form(ticket),
            parser=parse_delay_certificate_response,
        )

    def get_delay_return_receipt(self, ticket: OriginalTicketReference) -> DelayReturnReceiptResponse:
        """열차 지연으로 돌려받은 지연료의 반환 영수증을 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.dlay.pymtRcet.do",
            build_delay_return_receipt_form(ticket),
            parser=parse_delay_return_receipt_response,
        )

    def get_self_checkin_info(self, detail: RefundTicketDetailResponse) -> SelfCheckInInfoResponse:
        """get_refund_ticket_detail 결과로 셀프 체크인한 자유석 정보를 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.checkin.info.do",
            build_self_checkin_info_form(detail),
            parser=parse_self_checkin_info_response,
        )

    def check_self_checkin_seat(
        self, detail: RefundTicketDetailResponse, qr_code: str
    ) -> SelfCheckInSeatCheckResponse:
        """좌석 QR 문자열로 셀프 체크인할 수 있는 좌석을 확인합니다. 상태는 바꾸지 않습니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.checkin.psbFlg.do",
            build_self_checkin_seat_check_form(detail, qr_code),
            parser=parse_self_checkin_seat_check_response,
        )

    def register_self_checkin(
        self, detail: RefundTicketDetailResponse, seat: SelfCheckInSeat
    ) -> SelfCheckInRegisterResponse:
        """check_self_checkin_seat 의 좌석으로 셀프 체크인을 등록합니다.

        상태를 바꾸므로 실패해도 다시 보내지 마십시오(실서버 검증 못 함)."""
        self._require_session()
        return self._mutation(
            "/classes/com.korail.mobile.checkin.reg.do",
            build_self_checkin_register_form(self.config, detail, seat),
            parser=parse_self_checkin_register_response,
        )

    def cancel_self_checkin(self, detail: RefundTicketDetailResponse) -> SelfCheckInCancelResponse:
        """셀프 체크인을 취소합니다.

        상태를 바꾸므로 실패해도 다시 보내지 마십시오(실서버 검증 못 함)."""
        self._require_session()
        return self._mutation(
            "/classes/com.korail.mobile.checkin.cnc.do",
            build_self_checkin_cancel_form(self.config, detail),
            parser=parse_self_checkin_cancel_response,
        )

    def get_common_code(
        self,
        code: str | Sequence[str] = "",
    ) -> BaseKorailResponse:
        """요청한 공통코드 종류(하나 또는 목록)의 설정값을 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.common.code.do",
            build_common_code_form(self.config, code),
            parser=BaseKorailResponse.from_raw,
            include_common=False,
        )

    def get_app_data(
        self,
        timestamp_ms: int | None = None,
    ) -> AppDataResponse:
        """앱 메인 화면이 쓰는 캐시 파일을 받아 옵니다."""
        return self._post_read(
            "/file/CACHE/prdMobilePlusMain.cache",
            {**build_cache_query(timestamp_ms), "srtCheckYn": "Y"},
            parser=parse_app_data_response,
            require_envelope=False,
        )

    def get_notice(
        self,
        timestamp_ms: int | None = None,
    ) -> NoticeResponse:
        """앱 메인 캐시의 중첩 ``notice`` 를 읽습니다."""
        app_data = self.get_app_data(timestamp_ms)
        return app_data.notice or NoticeResponse(
            h_msg_cd=app_data.h_msg_cd,
            h_msg_txt=app_data.h_msg_txt,
            str_result=app_data.str_result,
            raw=app_data.raw,
        )

    def get_uuid(self) -> UuidResponse:
        """서버가 발급하는 단말 검증값 하나를 받아 옵니다."""
        return self._post_read(
            "/ebizcross/getUUID.do",
            parser=parse_uuid_response,
            include_common=False,
            form_encoded=False,
            require_envelope=False,
        )

    def get_maas_menu_list(
        self,
        *,
        pnr_no: str | None = None,
        ticket_return_numbers: Sequence[str] | None = None,
    ) -> MaasMenuListResponse:
        """일반 또는 승차권별 MaaS 메뉴를 조회합니다."""
        form: Mapping[str, str] | list[tuple[str, str]]
        if pnr_no is None and ticket_return_numbers is None:
            form = build_maas_menu_form(self.config)
            include_common = False
        else:
            self._require_session()
            form = _build_ticket_maas_menu_form(pnr_no, ticket_return_numbers)
            include_common = True
        return self._post_read(
            "/classes/com.korail.mobile.copt.gdMenuLt.do",
            form,
            parser=parse_maas_menu_list_response,
            include_common=include_common,
        )

    def get_maas_station_data(
        self,
        additional_service_code: str,
    ) -> StationDataResponse:
        """MaaS 부가서비스 하나가 지원하는 역 목록을 조회합니다."""
        return self._post_read(
            "/ebizmaas/EbizMaasStationList.do",
            build_maas_station_form(additional_service_code),
            parser=parse_station_data_response,
            include_common=False,
            require_envelope=False,
        )

    def get_station_info(self) -> StationInfoResponse:
        """역 데이터의 판본과 수록 역 수를 빈 POST로 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.common.stationinfo",
            parser=parse_station_info_response,
            include_common=False,
            form_encoded=False,
            require_envelope=False,
        )

    def get_station_data(self) -> StationDataResponse:
        """전체 역 목록을 코드·이름·좌표까지 한 번에 받아 옵니다."""
        return self._post_read(
            "/classes/com.korail.mobile.common.stationdata",
            parser=parse_station_data_response,
            include_common=False,
            form_encoded=False,
            require_envelope=False,
        )

    def get_train_calendar(self) -> TrainCalendarResponse:
        """지금 예매할 수 있는 운행일 달력을 받아 옵니다."""
        return self._post_read(
            "/classes/com.korail.mobile.schedule.runDt",
            build_cache_query(),
            parser=parse_train_calendar_response,
        )

    def search_trains(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
        use_special_schedule: bool = False,
        peak_season: bool = False,
    ) -> TrainSearchResult:
        """한 구간·한 날짜의 직통 열차 한 페이지를 조회합니다(성수기 여부 peak_season 은 호출자가 정합니다)."""
        return self._run_read(
            lambda: self._search_trains(
                query,
                continuation,
                use_special_schedule=use_special_schedule,
                peak_season=peak_season,
            )
        )

    def search_transfer_trains(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
        use_special_schedule: bool = False,
        peak_season: bool = False,
    ) -> TransferSearchResult:
        """같은 질의를 환승 여정으로 바꿔 한 페이지 조회합니다."""
        return self._run_read(
            lambda: self._search_transfer_trains(
                query,
                continuation,
                use_special_schedule=use_special_schedule,
                peak_season=peak_season,
            )
        )

    def search_trains_with_transfer_fallback(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
        use_special_schedule: bool = False,
        peak_season: bool = False,
    ) -> TrainSearchResult | TransferSearchResult:
        """직통 조회가 KorailNoDirectTrainError(WRD000061)이면 같은 조건으로 환승 첫 페이지를 조회합니다."""
        try:
            return self.search_trains(
                query,
                continuation=continuation,
                use_special_schedule=use_special_schedule,
                peak_season=peak_season,
            )
        except KorailNoDirectTrainError:
            return self.search_transfer_trains(
                query,
                use_special_schedule=use_special_schedule,
                peak_season=peak_season,
            )

    def _search_trains(
        self,
        query: TrainSearchQuery,
        continuation: TrainSearchContinuation | None = None,
        *,
        use_special_schedule: bool = False,
        peak_season: bool = False,
    ) -> TrainSearchResult:
        response = self._post_schedule_view(
            query,
            continuation,
            transfer=False,
            use_special_schedule=use_special_schedule,
            peak_season=peak_season,
        )
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
        *,
        use_special_schedule: bool = False,
        peak_season: bool = False,
    ) -> TransferSearchResult:
        response = self._post_schedule_view(
            query,
            continuation,
            transfer=True,
            use_special_schedule=use_special_schedule,
            peak_season=peak_season,
        )
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
        use_special_schedule: bool = False,
        peak_season: bool = False,
    ) -> BaseKorailResponse:
        validate_train_search_query(query)
        departure_name = self._resolve_station_reference(query.departure_station_code)
        arrival_name = self._resolve_station_reference(query.arrival_station_code)
        current = self.session.current
        form = build_train_search_form(
            self.config,
            query,
            departure_name=departure_name,
            arrival_name=arrival_name,
            member_card_no=current.member_card_no if current else None,
            continuation=continuation,
            transfer=transfer,
        )
        route = (
            "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"
            if use_special_schedule
            else "/classes/com.korail.mobile.seatMovie.ScheduleView"
        )
        return self._queued(
            self._inquiry_gate(peak_season=peak_season, special=use_special_schedule),
            lambda: self.http.post_form(route, form, include_common=False),
        )

    def _cached_station_data(self, *, refresh: bool = False) -> StationDataResponse:
        # 간편 API의 역 검사와 숫자 역 코드 해석이 같은 목록을 한 번만 받아 씁니다.
        if self._station_data is None or refresh:
            self._station_data = self.get_station_data()
            self._station_names = None
        return self._station_data

    def _resolve_station_reference(self, reference: str) -> str:
        if not reference.strip().isdigit():
            return resolve_station_name(reference, {})
        if self._station_names is None:
            stations = self._cached_station_data().stations
            self._station_names = {
                station.code: station.name for station in stations if station.code and station.name
            }
        return resolve_station_name(reference, self._station_names)

    def get_train_schedule(
        self,
        run_date: str,
        train_no: str,
    ) -> TrainScheduleResponse:
        """열차 한 편이 하루 동안 서는 정차역과 지연 상황을 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
            build_train_schedule_form(self.config, run_date, train_no),
            parser=parse_train_schedule_response,
            include_common=False,
        )

    def get_transfer_stations(
        self,
        departure_station_code: str,
        arrival_station_code: str,
    ) -> TransferStationListResponse:
        """한 구간에서 환승할 수 있는 역들을 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.qry.chtnStn.do",
            {"dptRsStnCd": departure_station_code, "arvRsStnCd": arrival_station_code},
            parser=parse_transfer_station_list_response,
        )

    def get_ticket_list(
        self,
        page_no: int = 1,
        *,
        mode: Literal["1", "2"] = "1",
        boarding_date_from: str = "",
        boarding_date_to: str = "",
    ) -> TicketListResponse:
        """승차권 목록을 예약→승차권 구조로 읽습니다(mode 1 은 현재표, 2 는 이력)."""
        self._require_session("ticket list requires")
        return self._post_read(
            "/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
            build_ticket_list_form(
                self.config,
                page_no,
                mode=mode,
                boarding_date_from=boarding_date_from,
                boarding_date_to=boarding_date_to,
            ),
            parser=parse_ticket_list_response,
        )

    def reserve(
        self,
        train: TrainSummary,
        *,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
        seats: Sequence[KorailSeatAssignment] | None = None,
        seat_attribute_code: str | None = None,
    ) -> ReservationHoldResponse:
        """열차 한 편에 실제 미결제 예약(홀드)을 만듭니다.

        결제·취소는 호출자 몫입니다. 응답을 읽지 못해도 홀드가 잡혔을 수 있으니 다시 보내지 말고 get_reservation_history 로 확인하십시오."""
        self._require_session("reservation requires")
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_reservation_form(
            self.config,
            train,
            passengers=passengers,
            seat_class=seat_class,
            job_type=job_type,
            seats=seats,
            seat_attribute_code=seat_attribute_code,
        )
        hold = self._queued(
            "reserve",
            lambda: self._mutation(
                route,
                form,
                parser=parse_reservation_hold_response,
            ),
        )
        return _hold_for_job(hold, job_type)

    def confirm_standby_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        allow_seat_class_change: bool = False,
        sms_notify: bool = False,
        phone_no: str | None = None,
    ) -> BaseKorailResponse:
        """이미 만든 예약대기 홀드에 알림·좌석변경 옵션을 저장합니다.

        서버 상태를 바꾸므로 실패해도 다시 보내지 마십시오."""
        self._require_session("standby options require")
        route = "/classes/com.korail.mobile.reservationWait.ReservationWait"
        form = build_standby_wait_form(
            self.config,
            hold,
            allow_seat_class_change=allow_seat_class_change,
            sms_notify=sms_notify,
            phone_no=phone_no,
        )
        return self._mutation(route, form, parser=BaseKorailResponse.from_raw)

    def reserve_transfer(
        self,
        legs: Sequence[TrainSummary],
        *,
        passengers: KorailPassengerCounts | None = None,
        seat_classes: Sequence[KorailSeatClass] | KorailSeatClass = (KorailSeatClass.GENERAL),
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
        seats: Sequence[Sequence[KorailSeatAssignment]] | None = None,
        seat_attribute_codes: Sequence[str | None] | None = None,
    ) -> ReservationHoldResponse:
        """탑승 순서의 열차 두 편을 한 PNR 로 홀드합니다.

        결제·취소는 호출자 몫이며, 실패해도 다시 보내지 말고 get_reservation_history 로 확인하십시오."""
        self._require_session("reservation requires")
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_transfer_reservation_form(
            self.config,
            legs,
            passengers=passengers,
            seat_classes=seat_classes,
            job_type=job_type,
            seats=seats,
            seat_attribute_codes=seat_attribute_codes,
        )
        hold = self._queued(
            "reserve",
            lambda: self._mutation(
                route,
                form,
                parser=parse_reservation_hold_response,
            ),
        )
        return _hold_for_job(hold, job_type)

    def reserve_merge(
        self,
        standing_hold_train: TrainSummary,
        merge_rows: Sequence[TrainScheduleItem],
        *,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
        job_type: KorailReservationJobType = KorailReservationJobType.MERGE_STANDING,
        seat_attribute_code: str | None = None,
    ) -> ReservationHoldResponse:
        """병합예약의 후속 요청으로 실제 미결제 예약을 만듭니다.

        첫 홀드 취소는 호출자 몫이고 후속 홀드는 별도 PNR 일 수 있으니, 실패해도 다시 보내지 말고 예약 내역을 확인하십시오."""
        self._require_session("reservation requires")
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_merge_reservation_form(
            self.config,
            standing_hold_train,
            merge_rows,
            passengers=passengers,
            seat_class=seat_class,
            job_type=job_type,
            seat_attribute_code=seat_attribute_code,
        )
        return self._mutation(
            route,
            form,
            parser=parse_reservation_hold_response,
        )

    def reserve_limousine(
        self,
        schedule: LimousineSchedule,
        seat_nos: Sequence[str],
        *,
        passengers: KorailPassengerCounts | None = None,
    ) -> ReservationHoldResponse:
        """공항버스 좌석을 실제로 미결제 예약합니다.

        결제·취소는 호출자 몫이며, 실패해도 다시 보내지 말고 get_reservation_history 로 확인하십시오."""
        self._require_session("reservation requires")
        form = build_limousine_reservation_form(self.config, schedule, seat_nos, passengers=passengers)
        return self._mutation(
            "/classes/com.korail.mobile.certification.TicketReservation",
            form,
            parser=parse_reservation_hold_response,
        )

    def cancel_unpaid_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        check_first: bool = True,
    ) -> BaseKorailResponse:
        """미결제 홀드를 취소합니다(기본은 가능 여부 확인 뒤 취소).

        서버 상태를 바꾸므로 실패해도 다시 보내지 말고 예약 내역을 확인하십시오."""
        self._require_session("cancellation requires")
        form = build_unpaid_reservation_cancel_form(self.config, hold)
        if check_first:
            self._mutation(
                "/classes/com.korail.mobile.reservationCancel.ReservationCancel",
                form,
                parser=BaseKorailResponse.from_raw,
            )
        return self._mutation(
            "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk",
            form,
            parser=BaseKorailResponse.from_raw,
        )

    def pay_with_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
    ) -> ReservationPaymentResponse:
        """홀드의 received_amount 를 카드로 결제합니다.

        실제 청구가 발생하며 카드 거절은 FAIL 모델로 돌아옵니다. 실패해도 다시 보내지 말고 결제 상태를 확인하십시오."""
        self._require_session("payment requires")
        route = "/classes/com.korail.mobile.payment.ReservationPayment"
        form = build_card_payment_form(self.config, hold, card)
        # 카드 거절도 응답으로 읽으므로 FAIL 예외를 억제합니다. 결과를 성공으로 바꾸지는 않습니다.
        return self._queued(
            "pay",
            lambda: self._mutation(
                route,
                form,
                parser=parse_reservation_payment_response,
                raise_on_fail=False,
            ),
        )

    def refund(
        self,
        ticket: PaidTicket,
        *,
        settle_mileage: bool = False,
        pbp_acceptance_target_flag: str | None = None,
        commission: RefundCommissionResponse,
        latitude: str | None = None,
        longitude: str | None = None,
    ) -> RefundTicketResponse:
        """get_refund_commission 으로 확인한 발권 승차권 한 장을 환불합니다.

        실제 환불과 수수료가 발생하며 자동 재전송하지 않으니, 실패하면 승차권 상태를 확인하십시오."""
        self._require_session("refund requires")
        route = "/classes/com.korail.mobile.refunds.RefundsRequest"
        form = build_refund_form(
            self.config,
            ticket,
            settle_mileage=settle_mileage,
            pbp_acceptance_target_flag=pbp_acceptance_target_flag,
            commission=commission,
            latitude=latitude,
            longitude=longitude,
        )
        return self._mutation(route, form, parser=parse_refund_ticket_response)

    def verify_station_ticket_refund(
        self,
        request: StationRefundVerificationRequest,
    ) -> StationRefundVerificationResponse:
        """역발행 승차권의 온라인 환불 가능 여부와 금액을 확인합니다. 환불은 하지 않습니다(실서버 검증 못 함)."""
        self._require_session("station ticket refund verification requires")
        return self._post_read(
            "/classes/com.korail.mobile.refunds.verifyOnlineRefunds",
            build_station_refund_verification_form(request),
            parser=lambda raw: self._parse_mutation_response(raw, parse_station_refund_verification_response),
        )

    def execute_station_ticket_refund(
        self,
        request: StationRefundExecutionRequest,
    ) -> StationRefundExecutionResponse:
        """검증된 역발행 승차권의 환불을 요청합니다.

        실제 환불·접수 상태를 바꿀 수 있으니 다시 보내지 말고 결과를 확인하십시오(검증 못 함)."""
        self._require_session("station ticket refund requires")
        return self._mutation(
            "/classes/com.korail.mobile.refunds.executeOnlineRefunds",
            build_station_refund_execution_form(self.config, request),
            parser=parse_station_refund_execution_response,
        )

    def add_to_cart(
        self,
        request: CartAddRequest,
    ) -> CartAddResponse:
        """미결제 예약을 실제 장바구니에 추가합니다.

        서버 상태를 바꾸므로 실패해도 다시 보내지 마십시오."""
        self._require_session("cart add requires")
        route = "/classes/com.korail.mobile.cart.addCartList"
        form = build_cart_add_form(self.config, request)
        return self._mutation(route, form, parser=parse_cart_add_response)

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
    ) -> DiscountCardPurchaseResponse:
        """N카드 미결제 구매를 만듭니다.

        서버 상태를 바꾸므로 실패해도 다시 보내지 마십시오(실서버 검증 못 함)."""
        self._require_session("discount card purchase requires")
        route = "/classes/com.korail.mobile.research.dcntCrdInfo.do"
        form = build_discount_card_purchase_form(self.config, request)
        return self._mutation(
            route,
            form,
            parser=parse_discount_card_purchase_response,
        )

    def extend_discount_card(
        self,
        ticket: DiscountCardTicket,
    ) -> BaseKorailResponse:
        """N카드의 유효기간을 실제로 연장합니다.

        서버 상태를 바꾸므로 실패해도 다시 보내지 마십시오(검증 못 함: N카드가 없는 계정)."""
        self._require_session("discount card extension requires")
        route = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"
        query = build_discount_card_extension_query(self.config, ticket)
        return self._mutation(route, query, parser=BaseKorailResponse.from_raw)

    def reserve_with_discount_card(
        self,
        train: TrainSummary,
        *,
        card_no: str,
    ) -> ReservationHoldResponse:
        """N카드로 좌석을 홀드합니다.

        결제·취소는 호출자 몫이며 실패해도 다시 보내지 마십시오(검증 못 함: N카드가 없는 계정)."""
        self._require_session("reservation requires")
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_discount_card_reservation_form(
            self.config,
            train,
            card_no=card_no,
        )
        return self._queued(
            "reserve",
            lambda: self._mutation(
                route,
                form,
                parser=parse_reservation_hold_response,
            ),
        )

    def recalculate_price(
        self,
        request: PriceRecalculationRequest,
        *,
        add_to_cart: bool = False,
    ) -> ReservationHoldResponse:
        """홀드의 할인 조합을 재계산합니다.

        재계산된 홀드는 서버에 반영되므로 실패해도 다시 보내지 마십시오. add_to_cart=True 의 장바구니 실패는 결과에 남습니다."""
        if not isinstance(add_to_cart, bool):
            raise KorailInvalidInputError("add_to_cart must be a bool")
        self._require_session("price recalculation requires")
        route = "/classes/com.korail.mobile.certification.PriceReCalculation"
        form = build_price_recalculation_form(self.config, request)
        hold = self._mutation(
            route,
            form,
            parser=parse_reservation_hold_response,
        )
        if not add_to_cart:
            return hold
        try:
            cart = self._mutation(
                "/classes/com.korail.mobile.cart.addCartList",
                build_cart_add_form(self.config, CartAddRequest(request.pnr_no)),
                parser=parse_cart_add_response,
                raise_on_fail=False,
            )
        except KorailApiError as exc:
            # 재계산된 홀드는 서버에 이미 반영됐으므로 돌려주고, 장바구니 실패는 결과에 남깁니다.
            return replace(hold, cart_addition_error=exc)
        return replace(hold, cart_addition=cart)
