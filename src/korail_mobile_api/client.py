# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""요청은 자동 재전송하지 않으며 변경 응답 파싱 실패도 서버 처리 실패를 뜻하지 않습니다."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from typing import Any, Literal, TypeVar, overload

import httpx

from .config import KorailConfig
from .constants import KorailLoginInputFlag, KorailReservationJobType, KorailRoomClassCode, KorailSeatClass
from .errors import (
    KorailApiError,
    KorailAuthError,
    KorailNoDirectTrainError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from .http import KorailHttpClient
from .limousine_models import (
    LimousineSchedule,
    LimousineScheduleQuery,
    LimousineScheduleResponse,
    LimousineSeatInventoryQuery,
    LimousineSeatInventoryResponse,
)
from .limousine_parsers import (
    parse_limousine_schedule_response,
    parse_limousine_seat_inventory_response,
)
from .limousine_payloads import (
    build_limousine_schedule_form,
    build_limousine_seat_inventory_form,
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
    TrainScheduleResponse,
    TrainSearchContinuation,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
    TransferSearchResult,
    TransferStationListResponse,
    UuidResponse,
    pair_transfer_itineraries,
)
from .mutation_models import (
    CardPayment,
    CartAddRequest,
    CartAddResponse,
    DeliveredTicketRetrievalResponse,
    DiscountCardPurchaseRequest,
    DiscountCardPurchaseResponse,
    DiscountCardTicket,
    KorailPassengerCounts,
    KorailSeatAssignment,
    PaidTicket,
    PriceRecalculationRequest,
    ProductCancelResponse,
    RefundTicketResponse,
    ReservationHoldResponse,
    ReservationPaymentResponse,
    SelfCheckInCancelResponse,
    SelfCheckInRegisterResponse,
    StationRefundExecutionRequest,
    StationRefundExecutionResponse,
    StationRefundVerificationRequest,
    StationRefundVerificationResponse,
)
from .mutation_parsers import (
    parse_cart_add_response,
    parse_delivered_ticket_retrieval_response,
    parse_discount_card_purchase_response,
    parse_product_cancel_response,
    parse_refund_ticket_response,
    parse_reservation_hold_response,
    parse_reservation_payment_response,
    parse_self_checkin_cancel_response,
    parse_self_checkin_register_response,
    parse_station_refund_execution_response,
    parse_station_refund_verification_response,
)
from .mutation_payloads import (
    build_card_payment_form,
    build_cart_add_form,
    build_delivered_ticket_retrieval_form,
    build_discount_card_extension_query,
    build_discount_card_purchase_form,
    build_discount_card_reservation_form,
    build_limousine_reservation_form,
    build_merge_reservation_form,
    build_price_recalculation_form,
    build_product_cancel_query,
    build_refund_form,
    build_reservation_form,
    build_self_checkin_cancel_form,
    build_self_checkin_register_form,
    build_standby_wait_form,
    build_station_refund_execution_form,
    build_transfer_reservation_form,
    build_unpaid_reservation_cancel_form,
)
from .netfunnel import KorailNetFunnelClient
from .parsers import (
    parse_app_data_response,
    parse_maas_menu_list_response,
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
    build_train_schedule_special_form,
    build_train_search_form,
)
from .read_models import (
    CartListResponse,
    CommuterInfoResponse,
    CommuterKindMenuResponse,
    CrewRequestListResponse,
    CustomerTripInfoResponse,
    DelayCertificateResponse,
    DelayDiscountTicketListResponse,
    DelayReturnReceiptResponse,
    DeliveryRecipientResponse,
    DepositBankListResponse,
    DiscountCardScheduleResponse,
    DiscountCardUsageListResponse,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    KorailPointSummaryResponse,
    MaasServiceDetailListResponse,
    MergeSeatsInquiryResponse,
    MileageHistoryResponse,
    MultiChildDiscountTargetResponse,
    OriginalTicketInquiryResponse,
    PassAvailabilityResponse,
    PassMenuResponse,
    PassScheduleResponse,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
    PriceFareQuoteResponse,
    ProductDetailResponse,
    ProductReservationListResponse,
    RecentDeliveryHistoryResponse,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    ReservationHistoryResponse,
    SeatAssignmentScheduleResponse,
    SelfCheckInInfoResponse,
    SelfCheckInSeat,
    SelfCheckInSeatCheckResponse,
    SelfSeatChangeInfoResponse,
    ServiceStatusResponse,
    TicketDuplicationCheckResponse,
    TicketListResponse,
    TicketReceiptResponse,
    TicketReservationDetailResponse,
    TrainScheduleItem,
    TripChangeDateResponse,
    TripMenuResponse,
)
from .read_parsers import (
    parse_cart_list_response,
    parse_commuter_info_response,
    parse_commuter_kind_menu_response,
    parse_crew_request_list_response,
    parse_customer_trip_info_response,
    parse_delay_certificate_response,
    parse_delay_discount_ticket_response,
    parse_delay_return_receipt_response,
    parse_delivery_recipient_response,
    parse_deposit_bank_response,
    parse_discount_card_schedule_response,
    parse_discount_card_usage_response,
    parse_discount_coupon_response,
    parse_free_seat_car_response,
    parse_guide_seat_condition_response,
    parse_korail_point_summary_response,
    parse_maas_service_detail_list_response,
    parse_merge_seats_inquiry_response,
    parse_mileage_history_response,
    parse_multi_child_discount_target_response,
    parse_original_ticket_inquiry_response,
    parse_pass_availability_response,
    parse_pass_menu_response,
    parse_pass_schedule_response,
    parse_pbp_acceptance_specification_response,
    parse_price_fare_quote_response,
    parse_product_detail_response,
    parse_product_reservation_list_response,
    parse_recent_delivery_history_response,
    parse_refund_commission_response,
    parse_refund_ticket_detail_response,
    parse_reservation_history_response,
    parse_seat_assignment_schedule_response,
    parse_self_checkin_info_response,
    parse_self_checkin_seat_check_response,
    parse_self_seat_change_info_response,
    parse_service_status_response,
    parse_ticket_duplication_check_response,
    parse_ticket_list_response,
    parse_ticket_receipt_response,
    parse_ticket_reservation_detail_response,
    parse_trip_change_date_response,
    parse_trip_menu_response,
)
from .read_payloads import (
    CommuterInfoRequest,
    DiscountCardScheduleRequest,
    FreeSeatCarRequest,
    GuideSeatConditionRequest,
    MaasServiceDetailQuery,
    MergeSeatsInquiryRequest,
    MileageHistoryRequest,
    OriginalTicketReference,
    PassScheduleRequest,
    PriceFareQuoteRequest,
    RefundCompanion,
    SeatAssignmentScheduleRequest,
    SelfSeatChangeInfoRequest,
    TicketDuplicationCheckRequest,
    TicketReservationDetailRequest,
    build_cart_list_form,
    build_commuter_info_form,
    build_commuter_kind_menu_query,
    build_crew_request_list_query,
    build_customer_trip_info_form,
    build_delay_certificate_form,
    build_delay_discount_ticket_form,
    build_delay_return_receipt_form,
    build_delivery_recipient_form,
    build_discount_card_schedule_query,
    build_discount_card_usage_query,
    build_discount_coupon_form,
    build_free_seat_car_form,
    build_guide_seat_condition_form,
    build_korail_point_summary_form,
    build_maas_service_detail_form,
    build_merge_seats_inquiry_form,
    build_mileage_history_form,
    build_multi_child_discount_target_form,
    build_original_ticket_inquiry_form,
    build_pass_availability_form,
    build_pass_menu_form,
    build_pass_schedule_form,
    build_pbp_acceptance_specification_form,
    build_price_fare_quote_form,
    build_product_detail_query,
    build_product_reservations_query,
    build_recent_delivery_history_form,
    build_refund_commission_form,
    build_refund_ticket_detail_form,
    build_seat_assignment_schedule_form,
    build_self_checkin_info_form,
    build_self_checkin_seat_check_form,
    build_self_seat_change_info_form,
    build_service_status_query,
    build_station_refund_verification_form,
    build_ticket_duplication_check_form,
    build_ticket_receipt_form,
    build_ticket_reservation_detail_query,
    build_trip_change_date_form,
    build_trip_menu_form,
)
from .session import KorailSessionClient

T = TypeVar("T")


def _hold_for_job(hold: ReservationHoldResponse, job_type: KorailReservationJobType) -> ReservationHoldResponse:
    # 앱은 예약대기 홀드를 결제하지 않습니다.
    if KorailReservationJobType(job_type) is KorailReservationJobType.STANDBY:
        return replace(hold, payable=False)
    return hold


class KorailClient:
    """KORAIL 7.0.6의 조회·예약·결제 기능을 제공하는 비공식 클라이언트입니다.

    DynaPath·대기열은 기본 활성화이며 변경 메서드는 즉시 전송합니다; 안전한 사용과 한계는 checks/BEHAVIOR.md를 따릅니다."""

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
        except BaseException:
            self.http.close()
            raise
        self.session = KorailSessionClient(self.http)
        self._station_names: dict[str, str] | None = None

    def close(self) -> None:
        """HTTP·대기열 연결 풀을 닫습니다.

        연결 풀만 닫으므로 로그인 폐기는 logout 또는 clear_session으로 별도 수행합니다."""
        try:
            self.http.close()
        finally:
            if self.netfunnel is not None:
                self.netfunnel.close()

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
        """기존 세션을 비운 뒤 서비스 상태·암호화 파라미터를 읽고 로그인합니다.

        앱처럼 서비스·암호화 사전 조회 후 로그인하며 웹 후속 조치는 자동 수행하지 않습니다(LoginViewModel.java:1390-1520)."""
        return self.session.login(
            member_no,
            password,
            input_flag=input_flag,
            check_valid_pw=check_valid_pw,
            cust_id=cust_id,
            etr_path=etr_path,
        )

    def clear_session(self) -> None:
        """서버에 알리지 않고 로컬 로그인 상태만 버립니다.

        서버 로그아웃 없이 쿠키와 로컬 세션만 폐기합니다. 역 이름 캐시는 유지합니다."""
        self.session.clear_session()

    def logout(self) -> None:
        """로그인 상태이면 서버 로그아웃(login.Logout)을 보내고, 어느 경우든 finally 에서 로컬 세션·쿠키를 비웁니다.

        FAIL 봉투는 예외가 아니지만(FAIL/P058 은 세션 만료) 전송 오류 등은 그대로 전파됩니다. 서버 세션 무효화까지 보장하지 않으며 연결 풀은 close 로 닫습니다."""
        self.session.logout()

    def _run_read(self, operation: Callable[[], T]) -> T:
        try:
            return operation()
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def _queued(self, gate: str, send: Callable[[], T]) -> T:
        if self.netfunnel is None:
            return send()
        return self.netfunnel.run(gate, send)

    @staticmethod
    def _inquiry_gate(*, peak_season: bool, special: bool = False) -> str:
        """앱 근거: TrainScheduleViewModel.java:5213-5235."""
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
        include_dynapath: bool = False,
        require_envelope: bool = True,
        raise_on_fail: bool = True,
        omit_empty_fields: bool = True,
    ) -> T:
        """자동 재로그인·재전송은 하지 않습니다."""
        return self._run_read(
            lambda: parser(
                self.http.post_form(
                    route,
                    form,
                    include_common=include_common,
                    include_dynapath=include_dynapath,
                    require_envelope=require_envelope,
                    raise_on_fail=raise_on_fail,
                    omit_empty_fields=omit_empty_fields,
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
                    include_dynapath=False,
                    require_envelope=require_envelope,
                    omit_empty_fields=omit_empty_fields,
                ).raw
            )
        )

    @overload
    def _mutation(
        self,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: None = ...,
        raise_on_fail: bool = ...,
    ) -> BaseKorailResponse: ...

    @overload
    def _mutation(
        self,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: Callable[[Mapping[str, object]], T],
        raise_on_fail: bool = ...,
    ) -> T: ...

    def _mutation(
        self,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: Callable[[Mapping[str, object]], T] | None = None,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse | T:
        """파싱 실패만으로 서버 변경 여부를 알 수 없으므로 상태 확인 없이 재전송하지 마십시오."""
        response = self._run_read(
            lambda: self.http.post_mutation_form(
                route,
                form,
                raise_on_fail=raise_on_fail,
            )
        )
        if parser is not None:
            return self._parse_mutation_response(response.raw, parser)
        return response

    @staticmethod
    def _parse_mutation_response(
        raw: Mapping[str, object],
        parser: Callable[[Mapping[str, object]], T],
    ) -> T:
        """POST·GET 변경 및 환불 검증의 파싱 오류에 전체 응답을 보존합니다. 재전송하지 않습니다."""
        try:
            return parser(raw)
        except KorailApiError as error:
            # 파싱 실패를 재전송 신호로 쓰면 중복 예약·결제가 생길 수 있으므로 전체 응답과 부분 원문을 함께 보존합니다. 변경 파서는 직접 불러도 같도록 _preserve_read_raw
            # 가 이미 옮겨 두므로, 그때는 parser_raw 를 덮어쓰지 않습니다.
            if error.raw is not raw:
                error.parser_raw = error.raw
                error.raw = raw
            raise
        except Exception as error:
            # 패키지 밖 예외도 원문을 붙인 KorailProtocolError로 감싸며 재전송하지 않습니다.
            wrapped = KorailProtocolError(
                f"KORAIL response was received but could not be parsed: {type(error).__name__}"
            )
            wrapped.raw = raw
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
        room_class_code: KorailRoomClassCode = "1",
        seat_attribute_code: str | None = None,
    ) -> SeatInventoryResponse:
        """한 호차의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다.

        실서버 확인: 같은 세션에서 :meth:`get_seat_cars` 를 먼저 호출하지 않고 이 메서드를 바로 부르면 ``KorailAppError: [3]인증정보에 문제가
        있습니다`` 가 돌아올 수 있습니다 — 실앱의 화면 진입 순서(호차 목록 → 좌석 배치도)와 같습니다."""
        self._require_session()
        form = build_seat_inventory_form(
            self.config,
            train,
            car_no,
            passenger_count=passenger_count,
            room_class_code=room_class_code,
            seat_attribute_code=seat_attribute_code,
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
        """리무진 연계 구간의 운행 스케줄 한 페이지를 조회합니다."""
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
        """리무진 연계 편 한 호차의 좌석 점유 상태를 조회합니다."""
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

    def get_service_status(
        self,
        timestamp_ms: int | None = None,
    ) -> ServiceStatusResponse:
        """예매 서비스가 열려 있는지를 서버 봉투로 확인합니다."""
        query = build_service_status_query(timestamp_ms)
        return self._post_read(
            "/file/CACHE/MobileService.cache",
            query,
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
        """입금 가능한 은행의 코드와 이름 목록을 조회합니다.

        ``POST dlay.dptnBank.do`` (``NetworkApi.java:392-393`` — ``postDptnBank(@Field("Device"),
        @Field("Version"), @Field("Key"))``; ``@FieldMap`` 이 아니라 개별 ``@Field`` 세 개이며
        postCashRfn·postDecrypt 도 같은 방식입니다)."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.dlay.dptnBank.do",
            {
                "Device": self.config.device,
                "Version": self.config.version,
                "Key": self.config.key,
            },
            parser=parse_deposit_bank_response,
            include_common=False,
            omit_empty_fields=False,
        )

    def get_delay_discount_tickets(
        self,
        departure_date_to: str,
    ) -> DelayDiscountTicketListResponse:
        """계정의 지연할인권 목록을 조회합니다.

        ``POST passCard.DelayDiscountView`` (``NetworkApi.java:352-353`` —
        ``postDelayDiscountView(@QueryMap)``."""
        self._require_session()
        return self._run_read(
            lambda: parse_delay_discount_ticket_response(
                self.http.post_query(
                    "/classes/com.korail.mobile.passCard.DelayDiscountView",
                    build_delay_discount_ticket_form(departure_date_to),
                    include_dynapath=False,
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
        """계정의 할인쿠폰 목록을 조회합니다.

        ``POST passCard.CouponView``(``NetworkApi.java:328-329`` — ``postCoupon(@FieldMap)``). 보유분 없으면
        ``WRG000000`` 으로 빈 결과(예외 아님)."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.passCard.CouponView",
            build_discount_coupon_form(page_no, pnr_no),
            parser=parse_discount_coupon_response,
            raise_on_fail=False,
        )

    def get_korail_point_summary(self) -> KorailPointSummaryResponse:
        """계정의 포인트·쿠폰·복지 자격 요약을 조회합니다.

        라우트 선언은 ``NetworkApi.java:515-516``(``postMyXPointView(@FieldMap)``), 응답 필드는
        ``MyXPointViewOut.java:27-74`` 입니다."""
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
        """할인카드(N카드) 한 장을 이미 사용한 여행 내역을 조회합니다.

        검증 못 함: N카드가 없는 계정이라 성공 응답을 본 적이 없습니다(ERR000100 조회 자료 없음)."""
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
        """할인카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회합니다.

        검증 못 함: N카드가 없는 계정이라 성공 응답을 본 적이 없습니다(WRR000100 사용횟수 입력값 오류)."""
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
        """정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회합니다.

        구매·예약은 하지 않습니다. ``WRG000000`` 응답은 빈 결과(예외 아님)로 반환하며, 정기권 보유 여부를 뜻한다고 단정하지 않습니다."""
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
        """승무원 호출 화면에 띄울 요청 사유 선택지를 조회합니다.

        이 라우트의 실제 DTO(``CrewCallCommonIn.java:50``)의 유일한 입력은 ``timeStamp`` 이며, 주지 않으면 호출 시점의 밀리초 epoch
        입니다."""
        query = build_crew_request_list_query(timestamp_ms)
        return self._post_read(
            "/classes/com.korail.mobile.push.crwCallRq.do",
            query,
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

        같은 GET이 미결제 취소와 결제 후 환불에 쓰이므로 상세 수수료를 먼저 확인합니다(MyTicketDetailViewModel.java:1183-1192,3271-3291)."""
        self._require_session("product cancel requires")
        query = build_product_cancel_query(detail)
        return self._run_read(
            lambda: self._parse_mutation_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.product.ReservationCancel",
                    query,
                    include_common=True,
                    include_dynapath=False,
                ).raw,
                parse_product_cancel_response,
            )
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
        """한 열차의 자유석 호차와 안내 문구를 조회합니다.

        조회 행의 ``free_car_count`` 가 001·002 인 183편은 모두 SUCC/IRZ000001 과 호차 문구(예: "자유석 1량 : 18호차", "자유석 2량 :
        17, 18호차")를, 000 인 20편은 SUCC/IRZ000005 와 ``car_no=None`` 을 돌려줬습니다. 호차는 숫자 목록이 아니라 문구로 옵니다."""
        return self._post_read(
            "/classes/com.korail.mobile.trn.fresScar.do",
            build_free_seat_car_form(request),
            parser=parse_free_seat_car_response,
        )

    def get_guide_seat_condition(
        self,
        request: GuideSeatConditionRequest,
    ) -> GuideSeatConditionResponse:
        """도우미석 안내문을 읽습니다.

        날짜 있는 비교 관측은 GuideSeatConditionRequest 참고. FAIL/MRR800011 은 대피도우미석 대상(만20~50세, 시발~종착 이용)이 아니라는 회원
        판정으로 보이며, 는 좌석코드 999 도 같은 응답이었습니다."""
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
        """좌석배정 예매 화면의 열차 목록을 조회합니다.

        앱 호출: TrainScheduleViewModel.java:2639-2754. A1/A2 는 행을 반환한 관측값이며, 날짜·구간에 따라 WRD000057 로 거절될 수
        있습니다."""
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
        """열차 한두 편의 운임을 예매 전에 미리 계산해 받습니다.

        표시용 기준 운임이며 결제액은 홀드 received_amount를 사용합니다(TrainOpInfoViewModel.java:941-962)."""
        form = build_price_fare_quote_form(request)
        # 앱의 평탄화기는 빈 값을 빼지만(NetworkService.java:15335-15343) 여덟 칸은 그 뒤에 직접 넣어 빈 gdNo 도 보냅니다(:9895-9902).
        return self._post_read(
            "/classes/com.korail.mobile.trn.prcFare.do",
            form,
            parser=parse_price_fare_quote_response,
            include_dynapath=True,
            omit_empty_fields=False,
        )

    def get_delivery_recipient(
        self,
        ticket: OriginalTicketReference,
    ) -> DeliveryRecipientResponse:
        """N카드 2인 승차권의 전달 전 수령자 후보를 조회합니다.

        검증 못 함: 채워진 수령자 응답은 미확인이고 보호된 N카드 분기값을 추측하지 않습니다(DeliveryTicketFormViewModel.java:697-700)."""
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

        첫 여정의 PBP 번호로 회수하며 실서버 검증 못 함입니다(DeliveredTicketViewModel.java:185-205,283)."""
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
        """자율 좌석/열차 변경으로 갈 수 있는 승차역과 변경 사유를 조회합니다.

        요청은 승차권 없이 열차 정보만 받습니다. 실서버 관측: 운행 중인 KTX 023 은 SUCC, 운행 시간 밖 열차는 WRT800176("좌석변경가능시간아님")이었습니다."""
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

    def get_refund_commission(
        self,
        ticket: OriginalTicketReference,
        companion: RefundCompanion = RefundCompanion(),
    ) -> RefundCommissionResponse:
        """승차권 한 장의 예상 환불액과 수수료를 조회합니다.

        실제 환불은 하지 않습니다."""
        self._require_session()
        # RefundCommissionIn 은 공통 필드를 원표 식별자 뒤에 선언합니다(RefundCommissionIn.java:59).
        return self._post_read(
            "/classes/com.korail.mobile.refunds.CommissionView",
            {**build_refund_commission_form(ticket, companion), **self.http.common_fields()},
            parser=parse_refund_commission_response,
            include_common=False,
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
        """지난 승차권의 지연확인증(열차가 몇 분 늦게 도착했는지)을 조회합니다.

        원표 반환일을 사용하며 지연 승차권만 대상입니다(DelayCertificateViewModel.java:94; NormalTicketSectionKt.java:786-808)."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.dlay.athnIsu.do",
            build_delay_certificate_form(ticket),
            parser=parse_delay_certificate_response,
        )

    def get_delay_return_receipt(self, ticket: OriginalTicketReference) -> DelayReturnReceiptResponse:
        """열차 지연으로 돌려받은 지연료의 반환 영수증을 조회합니다.

        지연확인증과 같은 원표 식별자를 사용하며 채워진 영수증은 실서버 미확인입니다(DelayReturnReceiptViewModel.java:88)."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.dlay.pymtRcet.do",
            build_delay_return_receipt_form(ticket),
            parser=parse_delay_return_receipt_response,
        )

    def get_self_checkin_info(self, detail: RefundTicketDetailResponse) -> SelfCheckInInfoResponse:
        """셀프 체크인한 자유석 정보를 조회합니다(checkin.info.do, NetworkApi.java:674-676). detail 은 get_refund_ticket_detail
        의 결과입니다(SelfCheckInResultViewModel.java:249-250). 대기열은 없습니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.checkin.info.do",
            build_self_checkin_info_form(detail),
            parser=parse_self_checkin_info_response,
        )

    def check_self_checkin_seat(
        self, detail: RefundTicketDetailResponse, qr_code: str
    ) -> SelfCheckInSeatCheckResponse:
        """자유석에 앉아 좌석 테이블의 QR 을 스캔한 문자열로 체크인할 수 있는 좌석을 확인합니다.

        상태를 바꾸지 않습니다. 실서버 검증 못 함(checkin.psbFlg.do, NetworkApi.java:678-680;
        SelfCheckInInfoViewModel.java:102-108)."""
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

        상태를 바꾸므로 실패해도 다시 보내지 않습니다. 실서버 검증 못 함(checkin.reg.do, NetworkApi.java:682-684;
        SelfCheckInInfoViewModel.java:224-225)."""
        self._require_session()
        return self._mutation(
            "/classes/com.korail.mobile.checkin.reg.do",
            build_self_checkin_register_form(self.config, detail, seat),
            parser=parse_self_checkin_register_response,
        )

    def cancel_self_checkin(self, detail: RefundTicketDetailResponse) -> SelfCheckInCancelResponse:
        """셀프 체크인을 취소합니다.

        상태를 바꾸므로 실패해도 다시 보내지 않습니다. 실서버 검증 못 함(checkin.cnc.do, NetworkApi.java:288-290;
        SelfCheckInResultViewModel.java:111-112)."""
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
        """요청한 공통코드 종류의 설정값을 조회합니다.

        바인딩: NetworkApi.java:315-321. 앱 부팅은 코드 목록을 한 호출로 전달합니다 (NetworkService.java:2015-2025). 실서버 관측: 부팅 상수
        18개를 한 POST 로 보내 SUCC/API.I00000 과 18키를 받았으며 개별 요청 결과와 같았습니다."""
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
        """앱 메인 화면이 쓰는 캐시 파일을 받아 옵니다."""
        return self._run_read(
            lambda: parse_app_data_response(
                self.http.post_form(
                    "/file/CACHE/prdMobilePlusMain.cache",
                    build_cache_query(timestamp_ms),
                    include_common=False,
                    require_envelope=False,
                )
            )
        )

    def get_notice(
        self,
        timestamp_ms: int | None = None,
    ) -> NoticeResponse:
        """7.0.6 메인 캐시의 중첩 ``notice`` 를 읽습니다."""
        app_data = self.get_app_data(timestamp_ms)
        return app_data.notice or NoticeResponse(
            h_msg_cd=app_data.h_msg_cd,
            h_msg_txt=app_data.h_msg_txt,
            str_result=app_data.str_result,
            raw=app_data.raw,
        )

    def get_uuid(self) -> UuidResponse:
        """서버가 발급하는 단말 검증값 하나를 받아 옵니다."""
        return self._run_read(
            lambda: parse_uuid_response(
                self.http.post_form(
                    "/ebizcross/getUUID.do",
                    include_common=False,
                    form_encoded=False,
                    include_dynapath=False,
                    require_envelope=False,
                )
            )
        )

    def get_maas_menu_list(
        self,
        *,
        pnr_no: str | None = None,
        ticket_return_numbers: Sequence[str] | None = None,
    ) -> MaasMenuListResponse:
        """일반 또는 승차권별 MaaS 메뉴를 조회합니다.

        NetworkApi.java:402-404 의 postGdMenuLt 선언을 따릅니다."""
        form: Mapping[str, str] | list[tuple[str, str]]
        if pnr_no is None and ticket_return_numbers is None:
            form = build_maas_menu_form(self.config)
            include_common = False
        else:
            self._require_session()
            if not isinstance(pnr_no, str) or not pnr_no.strip():
                raise KorailProtocolError("KORAIL ticket MaaS menu requires a PNR")
            if (
                ticket_return_numbers is None
                or isinstance(ticket_return_numbers, (str, bytes))
                or not ticket_return_numbers
                or any(not isinstance(number, str) or not number.strip() for number in ticket_return_numbers)
            ):
                raise KorailProtocolError("KORAIL ticket MaaS menu requires at least one return number")
            form = [
                ("pnrNo", pnr_no),
                *(("tkRetNo", number) for number in ticket_return_numbers),
            ]
            include_common = True
        return self._run_read(
            lambda: parse_maas_menu_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.copt.gdMenuLt.do",
                    form,
                    include_common=include_common,
                    include_dynapath=False,
                )
            )
        )

    def get_maas_station_data(
        self,
        additional_service_code: str,
    ) -> StationDataResponse:
        """MaaS 부가서비스 하나가 지원하는 역 목록을 조회합니다."""
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

    def get_station_info(self) -> StationInfoResponse:
        """역 데이터의 판본과 수록 역 수를 빈 POST로 조회합니다."""
        return self._run_read(
            lambda: parse_station_info_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.common.stationinfo",
                    include_common=False,
                    form_encoded=False,
                    require_envelope=False,
                )
            )
        )

    def get_station_data(self) -> StationDataResponse:
        """전체 역 목록을 코드·이름·좌표까지 한 번에 받아 옵니다."""
        return self._run_read(
            lambda: parse_station_data_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.common.stationdata",
                    include_common=False,
                    form_encoded=False,
                    require_envelope=False,
                )
            )
        )

    def get_train_calendar(self) -> TrainCalendarResponse:
        """지금 예매할 수 있는 운행일 달력을 받아 옵니다."""
        return self._run_read(
            lambda: parse_train_calendar_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.schedule.runDt",
                    build_cache_query(),
                )
            )
        )

    def search_trains(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
        use_special_schedule: bool = False,
        peak_season: bool = False,
    ) -> TrainSearchResult:
        """한 구간·한 날짜의 직통 열차 한 페이지를 조회합니다.

        ``peak_season`` 은 출발일이 성수기인지입니다 — 앱은 달력(``RunDateOutItem.isPeakSeason()``)으로 고르지만 그 판정 코드값이 보호돼 있어
        호출자가 정합니다. 거짓이면 라이브러리 기본 관문 ``act_8`` 이며 앱 aid 평문은 미확인입니다."""
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
        """직통 조회가 KorailNoDirectTrainError(WRD000061)일 때만 같은 query 로 환승 첫 페이지를 자동 조회합니다.

        WRD000061만 자동 환승 재조회하며 앱과 달리 확인창·열차군 변경은 없습니다(TrainScheduleViewModel.java:3216-3219,11051-11079)."""
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
        departure_name = self._resolve_station_reference(query.departure_station_code)
        arrival_name = self._resolve_station_reference(query.arrival_station_code)
        current = self.session.current
        if use_special_schedule:
            form = build_train_schedule_special_form(
                self.config,
                query,
                departure_name=departure_name,
                arrival_name=arrival_name,
                member_card_no=current.member_card_no if current else None,
                continuation=continuation,
                transfer=transfer,
            )
            route = "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"
        else:
            form = build_train_search_form(
                self.config,
                query,
                departure_name=departure_name,
                arrival_name=arrival_name,
                member_card_no=current.member_card_no if current else None,
                continuation=continuation,
                transfer=transfer,
            )
            route = "/classes/com.korail.mobile.seatMovie.ScheduleView"
        return self._queued(
            self._inquiry_gate(peak_season=peak_season, special=use_special_schedule),
            lambda: self.http.post_form(route, form, include_common=False),
        )

    def _resolve_station_reference(self, reference: str) -> str:
        if not reference.strip().isdigit():
            return resolve_station_name(reference, {})
        if self._station_names is None:
            self._station_names = parse_station_name_map(self.get_station_data().raw)
        return resolve_station_name(reference, self._station_names)

    def get_train_schedule(
        self,
        run_date: str,
        train_no: str,
    ) -> TrainScheduleResponse:
        """열차 한 편이 하루 동안 서는 정차역과 지연 상황을 조회합니다."""
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
        """한 구간에서 환승할 수 있는 역들을 조회합니다."""
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
        page_no: int = 1,
        *,
        mode: Literal["1", "2"] = "1",
        boarding_date_from: str = "",
        boarding_date_to: str = "",
    ) -> TicketListResponse:
        """승차권 목록을 예약→승차권 구조로 읽습니다.

        관측상 mode=1은 현재표, 2는 이력이며 날짜·쪽번호는 보정하지 않습니다(MyTicketListIn.java:62; 호출 리터럴은 보호됨)."""
        self._require_session("ticket list requires")
        return self._run_read(
            lambda: parse_ticket_list_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
                    build_ticket_list_form(
                        self.config,
                        page_no,
                        mode=mode,
                        boarding_date_from=boarding_date_from,
                        boarding_date_to=boarding_date_to,
                    ),
                )
            )
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
        """열차 한 편에 실제 미결제 예약(홀드)을 만듭니다. 결제 또는 취소는 호출자 책임입니다.

        응답을 읽지 못해도 홀드는 잡혔을 수 있으니 다시 보내지 말고 예외의 ``.raw`` 나 get_reservation_history 로 확인하십시오.
        다른 예약 메서드도 같습니다. 좌석속성은 명시값→열차 행→기본값이며 STANDBY 홀드는 결제하지 않습니다(TrainScheduleViewModel.java:2914-2930,6773-6781)."""
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

        기존 대기 홀드의 옵션만 저장하며 새 예약·결제는 만들지 않습니다(ReservationWaitViewModel.java:68-80)."""
        self._require_session("standby options require")
        route = "/classes/com.korail.mobile.reservationWait.ReservationWait"
        form = build_standby_wait_form(
            self.config,
            hold,
            allow_seat_class_change=allow_seat_class_change,
            sms_notify=sms_notify,
            phone_no=phone_no,
        )
        return self._mutation(route, form)

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
        """탑승 순서의 TrainSummary 두 개를 한 PNR 로 홀드합니다.

        한 PNR에 탑승 순서의 두 여정을 넣습니다(TicketReservationIn.java:34-37,80)."""
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

        첫 홀드는 호출자가 취소해야 하며 후속 홀드는 별도 PNR일 수 있습니다(ReservationMergeViewModel.java:1352,1556; 실서버 관측)."""
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

        어른·어린이만 같은 예약 DTO로 보내며 좌석 수가 인원과 같아야 합니다(AirportBusSeatMapViewModel.java:752-788,1914)."""
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
        """미결제 홀드를 취소합니다.

        기본은 가능 여부 확인→취소이며 확인 실패 시 취소하지 않습니다(MyReservationViewModel.java:1557,1566,1720-1745)."""
        self._require_session("cancellation requires")
        form = build_unpaid_reservation_cancel_form(self.config, hold)
        if check_first:
            self._mutation("/classes/com.korail.mobile.reservationCancel.ReservationCancel", form)
        return self._mutation("/classes/com.korail.mobile.reservationCancel.ReservationCancelChk", form)

    def pay_with_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
    ) -> ReservationPaymentResponse:
        """홀드를 카드로 결제합니다. 실제 청구가 발생합니다.

        금액은 홀드의 received_amount 입니다. 카드 거절은 FAIL 모델로 반환하며 0원·대기 홀드는 카드 결제를 거절합니다(PayViewModel.java:15572)."""
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
        """PaidTicket 이 가리키는 발권 승차권 한 장을 환불합니다. PNR 전체 환불이 아니며 수수료가 붙을 수 있습니다.

        먼저 get_refund_commission 을 부르고 그 성공 응답을 ``commission`` 으로 넘기십시오. 승차권 한 장씩 환불하며 자동 조회·재전송하지 않습니다(MyTicketDetailViewModel.java:300-358,1811-1823)."""
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
        """역발행 승차권의 온라인 환불 가능 여부와 금액을 확인합니다.

        실서버 검증 못 함. 실제 환불은 실행하지 않습니다. VerifyOnlineRefundsOut은 CommonOut을 상속하지 않아 strResult 누락을 허용합니다
        (http._NON_COMMON_OUT_READ_PATHS)."""
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

        실제 환불·접수 상태를 바꿀 수 있으므로 반환 구분과 결과를 확인하십시오. 검증 못 함: 역발행 승차권이 없어 실행하지 못했습니다."""
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

        psgDiscAdd_infos.psgDiscAdd_info는 discount_additions로 읽습니다(NetworkApi.java:266-267; AddCartListIn.java:52;
        AddCartListOut.java:24-25,76). 실서버 관측: 열차·공항버스 예약 모두 SUCC/IRZ000002였으나 할인 행은 없었습니다."""
        self._require_session("cart add requires")
        route = "/classes/com.korail.mobile.cart.addCartList"
        form = build_cart_add_form(self.config, request)
        return self._mutation(route, form, parser=parse_cart_add_response)

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
    ) -> DiscountCardPurchaseResponse:
        """N카드 미결제 구매를 만듭니다.

        실서버 검증 못 함. 경로 이름의 Info 가 조회를 뜻하지 않습니다. NetworkApi.java:336-337; NCardInfoOut.java:32-33 의 일괄결제
        대상과 금액은 PayViewModel.java:6628 의 결제 입력으로 이어집니다."""
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

        검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
        self._require_session("discount card extension requires")
        route = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"
        query = build_discount_card_extension_query(self.config, ticket)
        return self._mutation(route, query)

    def reserve_with_discount_card(
        self,
        train: TrainSummary,
        *,
        card_no: str,
    ) -> ReservationHoldResponse:
        """N카드로 좌석을 홀드합니다.

        일반 예약 라우트(NetworkApi.java:752-753)에 승객별 txtCardNo_ 를
        보냅니다(TicketReservationInPassengerInfo.java:55,105). 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
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

        재계산 성공 뒤에만 선택적으로 장바구니에 추가하며 추가 실패는 결과에 남깁니다(PayViewModel.java:14428-14436)."""
        if not isinstance(add_to_cart, bool):
            raise KorailProtocolError("add_to_cart must be a bool")
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
        cart = self._mutation(
            "/classes/com.korail.mobile.cart.addCartList",
            build_cart_add_form(self.config, CartAddRequest(request.pnr_no)),
            parser=parse_cart_add_response,
            raise_on_fail=False,
        )
        return replace(hold, cart_addition=cart)
