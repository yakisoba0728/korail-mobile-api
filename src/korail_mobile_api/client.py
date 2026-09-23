# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""KorailClient 의 공개 메서드와 전송·빌더·파서 연결. 읽기에도 인증이 필요한 경로가 있습니다. 상태 변경 메서드는 로그인 후 즉시 전송되므로 홀드·결제·환불 호출 전에
인자를 확인하십시오. 실험에는 MockTransport 를 사용합니다.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal, TypeVar, overload

import httpx

from .config import KorailConfig
from .constants import KorailReservationJobType, KorailSeatClass
from .errors import (
    KorailApiError,
    KorailAuthError,
    KorailNoDirectTrainError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from .http import KorailHttpClient
from .netfunnel import KorailNetFunnelClient
from .limousine_models import (
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
    CartAddResponse,
    CardPayment,
    CartAddRequest,
    DiscountCardPurchaseRequest,
    DiscountCardPurchaseResponse,
    DiscountCardTicket,
    KorailPassengerCounts,
    KorailSeatAssignment,
    PaidTicket,
    PriceRecalculationRequest,
    RefundTicketResponse,
    ReservationHoldResponse,
    ReservationPaymentResponse,
    StationRefundExecutionRequest,
    StationRefundExecutionResponse,
    StationRefundVerificationRequest,
    StationRefundVerificationResponse,
)
from .mutation_parsers import (
    parse_cart_add_response,
    parse_discount_card_purchase_response,
    parse_refund_ticket_response,
    parse_reservation_hold_response,
    parse_reservation_payment_response,
    parse_station_refund_execution_response,
    parse_station_refund_verification_response,
)
from .mutation_payloads import (
    build_card_payment_form,
    build_cart_add_form,
    build_discount_card_extension_query,
    build_discount_card_purchase_form,
    build_discount_card_reservation_form,
    build_merge_reservation_form,
    build_price_recalculation_form,
    build_refund_form,
    build_reservation_form,
    build_standby_wait_form,
    build_station_refund_execution_form,
    build_transfer_reservation_form,
    build_unpaid_reservation_cancel_form,
)
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
    DelayDiscountTicketListResponse,
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
    PriceFareQuoteResponse,
    ProductDetailResponse,
    ProductReservationListResponse,
    RecentDeliveryHistoryResponse,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    ReservationHistoryResponse,
    SeatAssignmentScheduleResponse,
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
    parse_delay_discount_ticket_response,
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
    build_customer_trip_info_form,
    build_delay_discount_ticket_form,
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


class KorailClient:
    """KORAIL 7.0.6 기반 비공식 클라이언트.

    DynaPath 는 합성 기기 값으로 기본 활성화됩니다. disable_dynapath=True 면 필수 경로의 로그인은 전송 전에 거절됩니다. 서버 수용은 보장하지 않습니다.
    transport 에 MockTransport 를 넣어 오프라인 시험할 수 있습니다.

    NetFunnel 은 기본 활성화되며 적용 메서드는 KORAIL_NETFUNNEL_GATES 와 호출부를 따릅니다. 대기·차단 결과를 무시하지 않습니다. 상태 변경은 별도 확인
    절차 없이 전송됩니다.

    with 문은 지원하지 않습니다. close 는 연결 풀만 닫습니다. 서버 로그아웃은 logout, 로컬 상태만 폐기할 때는 clear_session 을 별도로 호출하십시오.
    """

    def __init__(
        self,
        config: KorailConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        #: 대기열 클라이언트. ``netfunnel_enabled`` 가 거짓이면 ``None``.
        self.netfunnel = (
            KorailNetFunnelClient(self.config, transport=transport)
            if self.config.netfunnel_enabled
            else None
        )
        self.session = KorailSessionClient(self.http)
        self._station_names: dict[str, str] | None = None

    def close(self) -> None:
        """HTTP 커넥션 풀을 닫습니다. 로그인 상태는 건드리지 않습니다.

        :meth:`~korail_mobile_api.http.KorailHttpClient.close` 로 위임하며 네트워크 호출을 하지 않습니다. 로그인까지 끝내려면 먼저
        :meth:`logout`(서버 세션 무효화) 이나 :meth:`clear_session`(로컬만 폐기)을 부르면 됩니다.
        """
        self.http.close()
        if self.netfunnel is not None:
            self.netfunnel.close()

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
        """기존 세션을 비운 뒤 서비스 상태·암호화 파라미터를 읽고 로그인합니다. 라우트: NetworkApi.java:459-460. member_no 는
        회원번호·휴대폰번호·이메일이며 input_flag 를 생략하면 infer_login_input_flag 가 선택합니다.

        로그인 거절은 앱처럼 코드로 가릅니다(:data:`~korail_mobile_api.session.KORAIL_LOGIN_CONTINUATION_CODES`).
        휴면(WRC000116)·비밀번호 변경(WRC000420)은 KorailAuthContinuationRequired 로 올리고 session.pending 에 남깁니다.
        서비스 점검 등 따로 분류된 코드는 그 KorailAppError 하위 예외, 그 밖의 거절(잠김 WRC000390, 정보 오류 WRR000101 등)이나
        JSESSIONID 누락은 ``code``·``raw`` 가 붙은 KorailAuthError 입니다. 사전 조회(MobileService.cache·common.code.do)의 FAIL 은
        KorailAppError 하위 예외, 전송 실패는 KorailTransportError, JSON·봉투·암호화 파라미터 이상은 KorailProtocolError 로 그대로 올라옵니다.
        실패 시 세션·쿠키는 비웁니다.
        """
        return self.session.login(
            member_no,
            password,
            input_flag=input_flag,
            check_valid_pw=check_valid_pw,
            cust_id=cust_id,
            etr_path=etr_path,
        )

    def login_social(
        self,
        cust_id: str,
        *,
        input_flag: str,
        check_valid_pw: str,
    ) -> KorailSession:
        """외부 제공자 인증 후 고객번호 로그인 분기를 사용합니다. input_flag 와 보호된 checkValidPw 값은 호출자가 제공해야 합니다. 제공자 SDK 토큰
        교환이나 자격증명 파일 저장은 수행하지 않습니다.
        """
        return self.session.login_social(
            cust_id,
            input_flag=input_flag,
            check_valid_pw=check_valid_pw,
        )

    def clear_session(self) -> None:
        """서버에 알리지 않고 로컬 로그인 상태만 버립니다.

        쿠키 저장소(``JSESSIONID`` 포함), 현재 :class:`KorailSession`, 보류 중인 2단계 인증 상태를 모두 비웁니다. 네트워크 호출이 없으므로
        서버 쪽 세션은 스스로 만료될 때까지 살아 있습니다. 서버 세션까지 무효화하려면 :meth:`logout` 을 쓰면 됩니다.
        """
        self.session.clear_session()

    def logout(self) -> None:
        """로그인 상태이면 서버 로그아웃(login.Logout)을 보내고, 어느 경우든 finally 에서 로컬 세션·쿠키를 비웁니다. FAIL 봉투는 예외가 아니지만
        전송 오류 등은 그대로 전파됩니다. 연결 풀은 close 로 닫습니다.
        """
        self.session.logout()

    def _run_read(self, operation: Callable[[], T]) -> T:
        """P058 → clear_session → 재발생; 읽기·변경 골격이 함께 씁니다."""
        try:
            return operation()
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def _queued(self, gate: str, send: Callable[[], T]) -> T:
        """``gate`` 관문의 대기열을 통과한 뒤 ``send()`` — 대기열이 꺼져 있으면 바로 ``send()``."""
        if self.netfunnel is None:
            return send()
        return self.netfunnel.run(gate, send)

    @staticmethod
    def _inquiry_gate(*, peak_season: bool, special: bool = False) -> str:
        """열차조회 관문(``TrainScheduleViewModel.java:5213-5235`` 의 aid 선택)."""
        if special:
            return "product_inquiry"
        return "peak_season_inquiry" if peak_season else "inquiry"

    def _require_session(self, what: str = "account read requires") -> None:
        """세션이 없으면 요청 전에 인증 오류를 냅니다."""
        if self.session.current is None:
            raise KorailAuthError(f"KORAIL {what} an authenticated session")

    def _require_customer_no(self, what: str) -> str:
        """세션과 로그인 고객번호가 모두 있어야 후속 요청을 만듭니다."""
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
        parser: Callable[[dict[str, Any]], T],
        include_common: bool = True,
        include_dynapath: bool = False,
        require_envelope: bool = True,
        raise_on_fail: bool = True,
    ) -> T:
        """POST 읽기의 공통 골격: POST → 파싱 → 세션만료 복구."""
        return self._run_read(
            lambda: parser(
                self.http.post_form(
                    route,
                    form,
                    include_common=include_common,
                    include_dynapath=include_dynapath,
                    require_envelope=require_envelope,
                    raise_on_fail=raise_on_fail,
                ).raw
            )
        )

    def _get_read(
        self,
        route: str,
        params: Mapping[str, Any] | None = None,
        *,
        parser: Callable[[dict[str, Any]], T],
        require_envelope: bool = True,
    ) -> T:
        """GET 읽기의 공통 골격: GET → 파싱 → 세션만료 복구."""
        return self._run_read(
            lambda: parser(
                self.http.get_json(
                    route,
                    params,
                    include_common=True,
                    include_dynapath=False,
                    require_envelope=require_envelope,
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
        parser: Callable[[dict[str, Any]], T],
        raise_on_fail: bool = ...,
    ) -> T: ...

    def _mutation(
        self,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: Callable[[dict[str, Any]], T] | None = None,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse | T:
        """변경 응답 파싱 실패 시 예외 raw 에 응답 전체를, 기존 부분 raw 는 parser_raw 에 보존합니다. 서버 변경 여부는 파싱 실패만으로 알 수 없습니다.
        상태를 확인하지 않고 재전송하지 마십시오.
        """
        response = self._run_read(
            lambda: self.http.post_mutation_form(
                route,
                form,
                raise_on_fail=raise_on_fail,
            )
        )
        if parser is not None:
            try:
                return parser(response.raw)
            except KorailApiError as error:
                # 봉투 통과는 변경 성공 보장이 아닙니다(raise_on_fail=False 면 FAIL 도 도달). 부분 raw 로 전체 응답을 잃지 않게 하여
                # 호출자가 서버 상태를 확인할 수 있도록 합니다. 파싱 실패를 재전송 신호로 사용하면 중복 홀드·결제가 생길 수 있습니다.
                error.parser_raw = getattr(error, "raw", None)
                error.raw = response.raw
                raise
            except Exception as error:
                # 파서가 이 패키지의 예외가 아닌 것을 낼 수도 있습니다 — 예를 들어 자릿수 한도를 넘는 정수를 ``str()`` 로 바꾸다 나는
                # ``ValueError``. 위의 ``except`` 는 그것을 못 잡으므로 여기서 같은 계약으로 감쌉니다: 원문을 붙인
                # :class:`KorailProtocolError`.
                wrapped = KorailProtocolError(
                    "KORAIL response was received but could not be parsed:"
                    f" {type(error).__name__}"
                )
                wrapped.raw = response.raw
                raise wrapped from error
        return response

    def get_seat_cars(
        self,
        train: TrainSummary,
        *,
        passenger_count: int = 1,
        room_class_code: str = "1",
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
        room_class_code: str = "1",
        seat_attribute_code: str | None = None,
    ) -> SeatInventoryResponse:
        """한 호차의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다.

        2026-09-21 실서버 확인: 같은 세션에서 :meth:`get_seat_cars` 를 먼저 호출하지 않고 이 메서드를 바로 부르면 ``KorailAppError:
        [3]인증정보에 문제가 있습니다`` 가 돌아올 수 있습니다 — 실앱의 화면 진입 순서(호차 목록 → 좌석 배치도)와 같습니다. 호출 순서를 지키십시오.
        """
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
        """로그인 계정의 장바구니에 담긴 부가상품 항목을 조회합니다."""
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
        """입금은행 코드표. ``POST dlay.dptnBank.do`` (``NetworkApi.java:392-393`` —
        ``postDptnBank(@Field("Device"), @Field("Version"), @Field("Key"))``; 이 라우트만 예외적으로
        ``@FieldMap`` 이 아니라 개별 ``@Field`` 세 개입니다). 로그인 필요.
        """
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.dlay.dptnBank.do",
            parser=parse_deposit_bank_response,
        )

    def get_delay_discount_tickets(
        self,
        departure_date_to: str,
    ) -> DelayDiscountTicketListResponse:
        """지연할인권 조회. ``POST passCard.DelayDiscountView`` (``NetworkApi.java:352-353`` —
        ``postDelayDiscountView(@QueryMap)``. ``@FormUrlEncoded`` 선언인데 인자는 ``@QueryMap`` 이라, 7.0.6 도 이
        라우트만은 값을 쿼리스트링으로 붙입니다 — 이 메서드가 ``post_query`` 를 쓰는 이유입니다).

        로그인 필요.
        """
        self._require_session()
        return self._run_read(
            lambda: parse_delay_discount_ticket_response(
                self.http.post_query(
                    "/classes/com.korail.mobile.passCard.DelayDiscountView",
                    build_delay_discount_ticket_form(departure_date_to),
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
        """할인쿠폰 조회. ``POST passCard.CouponView``(``NetworkApi.java:328-329`` —
        ``postCoupon(@FieldMap)``). 로그인 필요.

        보유분 없으면 ``WRG000000`` 으로 빈 결과(예외 아님).
        """
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.passCard.CouponView",
            build_discount_coupon_form(page_no, pnr_no),
            parser=parse_discount_coupon_response,
            raise_on_fail=False,
        )

    def get_korail_point_summary(self) -> KorailPointSummaryResponse:
        """포인트·쿠폰·복지자격 요약. ``POST xPoint.MyXPointView``.

        로그인 필요. 복지 등록 상태(장애인증·보조견)도 함께 옵니다. 라우트 선언은
        ``NetworkApi.java:515-516``(``postMyXPointView(@FieldMap)``), 응답 필드는
        ``MyXPointViewOut.java:27-74`` 입니다.
        """
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
        """할인카드(N카드) 한 장을 이미 사용한 여행 내역을 조회합니다."""
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
        """할인카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회합니다."""
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
            # 성공 본문은 strResult 와 main_info 내부 코드인 관측이 있어 완전한 상위 봉투를 요구하지 않습니다. P058 은 공통 전송 계층에서
            # 처리합니다.
            require_envelope=False,
        )

    def get_pass_schedule(
        self,
        request: PassScheduleRequest,
    ) -> PassScheduleResponse:
        """정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회합니다.

        보유분 없으면 ``WRG000000`` 으로 빈 결과(예외 아님).
        """
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
            parser=parse_trip_menu_response, include_common=False,
        )

    def get_pass_menu(self, menu_no: str) -> PassMenuResponse:
        """정기권·패스 메뉴 한 갈래의 화면 구성 항목을 조회합니다."""
        form = build_pass_menu_form(menu_no)
        return self._post_read(
            "/classes/com.korail.mobile.pass.passMenu.do",
            form,
            parser=parse_pass_menu_response,
            # 성공 본문의 list·strResult 관측을 수용합니다. 상위 메시지 필드를 요구하지 않지만 P058 검사는 공통 전송 계층에 남습니다.
            require_envelope=False,
        )

    def get_crew_request_list(self) -> CrewRequestListResponse:
        """승무원 호출 화면에 띄울 요청 사유 선택지를 조회합니다.

        공통 필드만 보냅니다. 앱은 ``CrewCallCommonIn`` 을 만들지만 ``CommonIn.serializer()`` 로
        인코딩해(``NetworkService.java:3952-3955``) 하위 클래스의 ``timeStamp`` 는 나가지 않습니다.
        """
        return self._post_read(
            "/classes/com.korail.mobile.push.crwCallRq.do",
            {},
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
            query,
            parser=parse_commuter_kind_menu_response,
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
            parser=parse_product_detail_response,
        )

    def get_ticket_receipt(
        self,
        sale_date: str,
        window_no: str,
        sale_sequence: str,
        return_password: str,
        txt_index: str | None = None,
    ) -> TicketReceiptResponse:
        """승차권 한 장의 영수증과 결제수단을 조회합니다.

        네 식별값과 선택적인 ``txt_index`` 는 같은 승차권 상세 응답에서 가져와야 합니다. ``sale_date`` 는 반환원표일자입니다.
        """
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
        """한 열차의 자유석 호차와 안내 문구를 조회합니다."""
        return self._post_read(
            "/classes/com.korail.mobile.trn.fresScar.do",
            build_free_seat_car_form(request),
            parser=parse_free_seat_car_response,
        )

    def get_guide_seat_condition(
        self,
        request: GuideSeatConditionRequest,
    ) -> GuideSeatConditionResponse:
        """도우미석 안내문을 읽습니다. 앱처럼 ``FAIL`` 도 예외가 아니라 안내 응답으로 돌려주므로
        ``h_msg_cd``·``h_msg_txt`` 를 확인하십시오. 2026-09-22 관측에서 좌석속성 14종 모두 같은
        FAIL/MRR800011 안내였습니다.
        """
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
        """좌석배정 예매 화면의 열차 조회. 앱 호출: TrainScheduleViewModel.java:2639-2754. 2026-09-22 일반 검색 메뉴 11 의 7가지
        변형은 SUCC/WRG000000 과 빈 목록이었습니다. A1/A2 는 행을 반환한 관측값이며, 날짜·구간에 따라 WRD000057 로 거절될 수 있습니다. 빈 결과가
        열차 부재가 아닌 메뉴 차이일 수 있습니다. 열차조회 대기열을 거칩니다.
        """
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
        resolved_query = (
            query if query is not None else MaasServiceDetailQuery.current()
        )
        return self._post_read(
            "/classes/com.korail.mobile.copt.gdReqQry.do",
            build_maas_service_detail_form(self.config, resolved_query),
            parser=parse_maas_service_detail_list_response, include_common=False,
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
        """열차 한두 편의 운임을 예매 전에 미리 계산해 받습니다."""
        form = build_price_fare_quote_form(request)
        return self._post_read(
            "/classes/com.korail.mobile.trn.prcFare.do",
            form,
            parser=parse_price_fare_quote_response,
            include_dynapath=True,
        )

    def get_delivery_recipient(
        self,
        ticket: OriginalTicketReference,
    ) -> DeliveryRecipientResponse:
        """N카드 2인 승차권의 전달 전 수령자 후보를 조회합니다. 앱은 isNCardTwoPeople() 일 때
        호출합니다(DeliveryTicketFormViewModel.java:697-700). 그 판정의 보호 리터럴을 평문 Y 로 확정하지 않습니다. 2026-09-22 표본
        60장은 IRZ000005(조회 자료 없음)였습니다. 이 표본만으로 모든 비N카드 응답을 보장하지 않습니다. 전달 완료 내역은
        get_pbp_acceptance_specifications 참고.
        """
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
        tickets: tuple[OriginalTicketReference, ...],
    ) -> PbpAcceptanceSpecificationResponse:
        """승차권 여러 장의 PBP 수락 내역을 여정·좌석 단위로 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.tk.pbpAcepSpec.do",
            build_pbp_acceptance_specification_form(tickets),
            parser=parse_pbp_acceptance_specification_response,
        )

    def get_original_ticket_inquiry(
        self,
        tickets: tuple[OriginalTicketReference, ...],
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
        """자율 좌석/열차 변경으로 갈 수 있는 승차역과 변경 사유를 조회합니다."""
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
        """환불했을 때 돌려받을 금액과 떼일 수수료를 미리 묻습니다.

        :meth:`refund` 와 같은 단위, 즉 ``ticket`` 이 지목한 **승차권 한 장** 에 대한 답입니다. 2인 PNR 의 한 장을 넣으면 8,400원이라고
        답하는데, 그것은 결제 총액 16,800원을 잘못 센 것이 아니라 그 한 장을 반환하면 실제로 8,400원이 돌아온다는 정확한 답입니다. 총액을 알고 싶으면 장마다
        물어야 합니다.
        """
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.refunds.CommissionView",
            build_refund_commission_form(ticket, companion),
            parser=parse_refund_commission_response,
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

    def get_common_code(
        self,
        code: str | Sequence[str] = "",
    ) -> BaseKorailResponse:
        """문자열 하나 또는 문자열 시퀀스를 code 반복 키로 보냅니다. 바인딩: NetworkApi.java:315-321. 앱 부팅은 코드 목록을 한 호출로 전달합니다
        (NetworkService.java:2015-2025). 2026-09-22: 부팅 상수 18개를 한 POST 로 보내 SUCC/API.I00000 과 18키를
        받았으며 개별 요청 결과와 같았습니다. 미등록 코드·빈 코드도 SUCC 와 빈 문자열 항목으로 돌아왔습니다. 관측한 응답을 그대로 반환하며 임의의 코드가 항상 지원된다는
        보장은 없습니다.
        """
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
        """일반 또는 승차권별 MaaS 메뉴를 조회합니다. 원승차권 반환번호는 tkRetNo 반복 필드이며 하나로 합친 문자열이 아닙니다.
        NetworkApi.java:402-404 의 postGdMenuLt 선언을 따릅니다.
        """
        if pnr_no is None and ticket_return_numbers is None:
            form = build_maas_menu_form(self.config)
            include_common = False
        else:
            self._require_session()
            if not isinstance(pnr_no, str) or not pnr_no.strip():
                raise KorailProtocolError(
                    "KORAIL ticket MaaS menu requires a PNR"
                )
            if (
                ticket_return_numbers is None
                or isinstance(ticket_return_numbers, (str, bytes))
                or not 1 <= len(ticket_return_numbers) <= 8
                or any(
                    not isinstance(number, str) or not number.strip()
                    for number in ticket_return_numbers
                )
            ):
                raise KorailProtocolError(
                    "KORAIL ticket MaaS menu requires 1-8 return numbers"
                )
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

        열차조회 대기열을 거칩니다. ``peak_season`` 은 출발일이 성수기인지입니다 — 앱은 달력(``RunDateOutItem.isPeakSeason()``)으로
        고르지만 그 판정 코드값이 보호돼 있어 호출자가 정합니다. 거짓이면 달력이 없는 앱과 같은 ``act_8`` 입니다. ``use_special_schedule`` 이면
        ``product_inquiry`` 관문입니다(**추정**).
        """
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
        """같은 질의를 환승 여정으로 바꿔 한 페이지 조회합니다.

        대기열은 :meth:`search_trains` 와 같습니다.
        """
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
        """직통 조회가 KorailNoDirectTrainError(WRD000061)일 때만 환승 첫 페이지를 조회합니다. 2026-09-22 관측의 SUCC/WRG000000
        빈 목록은 폴백하지 않습니다. 반환형뿐 아니라 trains 를 확인하십시오. continuation 은 직통 조회에만 전달합니다. 앱은 사용자 확인 후 필터를
        바꿉니다(TrainScheduleViewModel.java:3216-3219,11051-11079). 이 메서드는 확인창 없이 자동 전환합니다. 오류 분기의 기존 근거
        기록은 TrainScheduleViewModel.smali:35513-35566 이며 jadx 만으로는 재검증되지 않았습니다.
        """
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
            query, continuation, transfer=False,
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
            query, continuation, transfer=True,
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
        departure_name = self._resolve_station_reference(
            query.departure_station_code
        )
        arrival_name = self._resolve_station_reference(
            query.arrival_station_code
        )
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
            self._inquiry_gate(
                peak_season=peak_season, special=use_special_schedule
            ),
            lambda: self.http.post_form(route, form, include_common=False),
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
        page_no: int = 0,
        *,
        mode: Literal["1", "2"] = "1",
        boarding_date_from: str = "",
        boarding_date_to: str = "",
    ) -> TicketListResponse:
        """승차권 목록을 예약→승차권 구조로 읽습니다. mode 는 페이지 커서가 아닙니다. 1 은 현재 승차권, 2 는 구매이력이라는 뜻은 라이브 관측입니다. 필드 선언은
        MyTicketListIn.java:62 이지만 호출부 값은 보호돼 있습니다 (MyTicketBaseViewModel.java:980,1029;
        LoginViewModel.java:1083).

        mode=2 날짜는 YYYYMMDD 를 사용하십시오. 빌더는 날짜 폭·순서·기간을 검증하지 않습니다. 2026-09-22: 양쪽 누락, 한쪽 누락, 6자리, 역순의 네
        표본은 WRT100101 이었고, 2년 범위는 128행, 같은 달 범위는 3행이었습니다. 이 관측으로 최대 기간을 보장하지 않습니다. mode=1 의 날짜는 빈 값이며
        전송 단계에서 생략됩니다. page_no 는 최소 1 로 보정합니다.
        """
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
        """열차 한 편에 미결제 홀드를 만듭니다. 결제 또는 취소는 호출자 책임입니다. 좌석 속성은 명시값→열차 행→기본값
        순서입니다(TrainScheduleViewModel.java:2914-2930,2982-2999).

        응답 파싱이 실패하면 KorailProtocolError 이고 ``.raw`` 에 응답 전체(h_pnr_no 포함)가 있습니다. 홀드가 잡혔을 수 있으니 재시도하지 말고
        ``.raw`` 나 get_reservation_history 로 확인하십시오. 네 예약 메서드가 모두 같습니다. job_type 기본은 IMMEDIATE(1101)입니다.

        SEAT_DESIGNATED 는 승객별 좌석이 필요합니다. STANDBY 는 대기 가능한 행만 받으며, 성공한 대기 홀드는 confirm_standby_hold 로 알림
        옵션을 기록합니다. IRR000014 의 트리거 의미는 라이브 기록이고 앱 비교값은 보호돼 있습니다. MERGE_STANDING 은 병합 첫 홀드이며 후속 호출은
        reserve_merge 입니다. 모든 변경 경로가 로그인을 요구합니다. 대기 예약에만 별도 회원 제한이 있다는 근거는 없습니다.
        """
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
        return self._queued(
            "reserve",
            lambda: self._mutation(
                route,
                form,
                parser=parse_reservation_hold_response,
            ),
        )

    def confirm_standby_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        allow_seat_class_change: bool = False,
        sms_notify: bool = False,
        phone_no: str | None = None,
    ) -> BaseKorailResponse:
        """이미 만든 예약대기 홀드에 알림·좌석변경 옵션을 기록합니다. 후속 라우트: NetworkApi.java:639-640; 화면과 저장 입력:
        ReservationWaitViewModel.java:68-80. WAIT enum 은 ReservationJobId.java:21 에 있으나 코드값은 보호돼 있습니다.
        IRR000014 의 메시지는 error_json.json 에 있고 트리거 의미는 라이브 기록에 근거합니다. 문자열 자산만으로 앱의 분기 조건까지 확정하지 않습니다.
        """
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
        seat_classes: Sequence[KorailSeatClass] | KorailSeatClass = (
            KorailSeatClass.GENERAL
        ),
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
        seats: Sequence[Sequence[KorailSeatAssignment]] | None = None,
        seat_attribute_codes: Sequence[str | None] | None = None,
    ) -> ReservationHoldResponse:
        """탑승 순서의 TrainSummary 두 개를 한 PNR 로 홀드합니다. search_transfer_trains 결과의 TransferItinerary.legs 를 넘길
        수 있습니다. 같은 라우트·DTO 의 여정 반복입니다(NetworkApi.java:752-753; TicketReservationIn.java:34-37,80).
        seat_classes 는 공통값 또는 구간별 값이며 좌석 지정도 구간별입니다 (TicketReservationInJrny.java:69;
        TicketReservationInSrcar.java:51; TicketReservationInSrcarTrailing.java:52). 2026-07-31: 성인
        1인·일반실·편도 환승이 SUCC/IRR000018, 49,700원, 여정 수 2 의 한 PNR 로 반환됐고 한 번의 cancel_unpaid_hold 로 해제됐습니다.
        다른 승객·객실 조합까지 검증된 것은 아닙니다.
        """
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
        return self._queued(
            "reserve",
            lambda: self._mutation(
                route,
                form,
                parser=parse_reservation_hold_response,
            ),
        )

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
        """병합예약의 두 번째 홀드. 첫 홀드 요청을 다시 보내되 ``txtStndFlg`` 와 중간역 세 필드만
        바꿉니다(앱과 같음 — :func:`~korail_mobile_api.mutation_payloads.build_merge_reservation_form`).
        열차·승객·등급·job·좌석속성은 첫 홀드와 같은 값을 넘기고, ``merge_rows`` 는
        :meth:`get_merge_seats_inquiry` 응답의 ``trains`` 를 그대로 넘깁니다.

        순서: ``job_type=MERGE_STANDING`` 첫 홀드 → 병합 좌석 조회 → 첫 홀드 취소 → 이 호출.
        첫 홀드 취소는 호출자가 합니다(앱: ``ReservationMergeViewModel.java:1352,1556``).

        2026-09-22: 첫 홀드부터 여정 21/22 로 나뉘었고 두 번째 호출은 별도 PNR 을 만들었습니다. 첫
        홀드를 유지한 표본의 ``WRR664260`` 도 SUCC 와 새 PNR·좌석이 있는 홀드였습니다 — 메시지만 보고
        실패로 간주하거나 재전송하지 마십시오. 남은 홀드는 각각 확인·취소해야 합니다. 첫 홀드 취소 후
        예전 두 여정 폼은 ``IRR000018`` 이었습니다.
        """
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

    def cancel_unpaid_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        check_first: bool = True,
    ) -> BaseKorailResponse:
        """미결제 홀드를 취소합니다. 앱처럼 ``ReservationCancel`` 로 먼저 취소 가능 여부를 묻고
        (``MyReservationViewModel.java:1557,1720-1745`` — 성공이면 확인창, 아니면 ``h_msg_txt`` 안내)
        그다음 ``ReservationCancelChk`` 로 취소합니다(``:1566``). 두 요청의 폼은 같습니다.
        확인 단계가 FAIL 이면 코드에 맞는 예외이고 취소는 보내지 않습니다. ``check_first=False`` 면
        바로 취소합니다.

        2026-09-24: 확인 단계는 SUCC/IRR000011("여정취소 가능합니다.")이었고 그 뒤에도 홀드가
        남아 있었습니다(확인만 함). 취소는 IRG000000. 2026-07-26·31 환승은 한 PNR 의 두 여정이
        함께 풀렸습니다.
        """
        self._require_session("cancellation requires")
        form = build_unpaid_reservation_cancel_form(self.config, hold)
        if check_first:
            self._mutation(
                "/classes/com.korail.mobile.reservationCancel.ReservationCancel", form
            )
        return self._mutation(
            "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk", form
        )

    def pay_with_fake_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
    ) -> ReservationPaymentResponse:
        """시험용 카드 객체로 결제 요청을 보냅니다. 오프라인 시뮬레이션이 아닙니다. 실제 결제와 같은 전송 경로이므로 이름만으로 비과금이 보장되지 않습니다. 실험은
        MockTransport 에서 수행하고 카드 정보가 담긴 폼·raw 를 기록하지 마십시오.
        """
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

    def pay_with_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
    ) -> ReservationPaymentResponse:
        """홀드를 카드로 결제합니다. 실제 청구가 발생할 수 있습니다. pay_with_fake_card 와 같은 빌더·전송 경로이며 이름 차이가 폼 검증을 추가하지 않습니다.
        2026-07-31: 8,400원 1장 IRT000000 발권과 2인 PNR 결제 기록; 2026-09-15: 7.0.6 결제·전액 환불 기록이 있습니다. 모든
        카드·요청 조합의 성공 보장은 아닙니다.
        """
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
        commission: RefundCommissionResponse | None = None,
        latitude: str | None = None,
        longitude: str | None = None,
    ) -> RefundTicketResponse:
        """PaidTicket 이 가리키는 발권 승차권 한 장을 환불합니다. PNR 전체 환불이 아닙니다. 여러 장이면 각 승차권의 결과·잔여 목록을 확인해야 합니다. 같은 장을
        무조건 재전송하지 마십시오. 국내 앱의 pbpAcepTgtFlg 는 상세값 에코(MyTicketDetailViewModel.java:1521)이나 외국인 경로는 보호
        상수(FTicketDetailViewModel.java:634)입니다. 라이브러리는 값이 없으면 빈 문자열을 만들고 전송 단계에서 생략합니다. 반환 횟수 코드는 이
        메서드의 인자가 아닙니다. 2026-07-31: 성인 2인 16,800원 PNR 에 한 번 호출해 SUCC/IRT200277 과 8,400원이 반환됐고, 남은 한 장에
        별도 환불을 한 뒤 목록이 비었습니다.

        앱의 환불 화면처럼 먼저 :meth:`get_refund_commission` 으로 수수료를 확인하고 그 응답을
        ``commission`` 으로 넘기면 ``tk_ret_tms_dv_cd``·``trnNo`` 도 싣습니다. ``latitude``/``longitude``
        는 앱이 위치를 얻었을 때만 싣는 값입니다(:func:`~korail_mobile_api.mutation_payloads.build_refund_form`).
        """
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
        return self._mutation(
            route, form, parser=parse_refund_ticket_response
        )

    def verify_station_ticket_refund(
        self,
        request: StationRefundVerificationRequest,
    ) -> StationRefundVerificationResponse:
        """역 발행 승차권을 온라인 환불 전에 검증합니다.

        응답 ``VerifyOnlineRefundsOut`` 은 ``CommonOut`` 을 상속하지 않아 ``strResult`` 가 없을 수 있습니다 —
        :data:`~korail_mobile_api.http._NON_COMMON_OUT_READ_PATHS` 가 이 경로를 그렇게 다룹니다.
        """
        self._require_session("station ticket refund verification requires")
        return self._post_read(
            "/classes/com.korail.mobile.refunds.verifyOnlineRefunds",
            build_station_refund_verification_form(request),
            parser=parse_station_refund_verification_response,
        )

    def execute_station_ticket_refund(
        self,
        request: StationRefundExecutionRequest,
    ) -> StationRefundExecutionResponse:
        """검증된 역 발행 승차권의 환불을 실행합니다. **실제로 돈이 움직입니다.**"""
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
        """미결제 예약을 장바구니에 담습니다(NetworkApi.java:266-267; AddCartListIn.java:52).
        psgDiscAdd_infos.psgDiscAdd_info 는 discount_additions 로 파싱합니다 (AddCartListOut.java:24-25,76).
        행 내용은 라이브 미검증이며 담기 자체는 상태 변경입니다.
        """
        self._require_session("cart add requires")
        route = "/classes/com.korail.mobile.cart.addCartList"
        form = build_cart_add_form(self.config, request)
        return self._mutation(
            route, form, parser=parse_cart_add_response
        )

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
    ) -> DiscountCardPurchaseResponse:
        """N카드 미결제 구매를 만듭니다. 경로 이름의 Info 가 조회를 뜻하지 않습니다. NetworkApi.java:336-337; NCardInfoOut.java:32-33
        의 일괄결제 대상과 금액은 PayViewModel.java:6628 의 결제 입력으로 이어집니다.
        """
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
        """할인카드의 유효기간을 연장합니다(기간연장).

        ``POST reservation.dcntCrdExtn.do`` (7.0.6 ``NetworkApi``).

        ``post_mutation_form`` 으로 전송합니다. 로그인 상태를 요구합니다.
        """
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
        """N카드로 좌석을 홀드합니다. 일반 예약 라우트(NetworkApi.java:752-753)에 승객별 txtCardNo_ 를
        보냅니다(TicketReservationInPassengerInfo.java:55,105).
        """
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
    ) -> ReservationHoldResponse:
        """홀드의 할인 조합을 재계산합니다. 변경 결과를 읽은 뒤 결제·취소 여부를 판단하십시오. NetworkApi.java:583-584 는 일반 폼 외 여섯 반복 필드를
        받습니다. 입력 구성은 PayViewModel.java:902,1316,14278 이며 화면의 모든 변경 트리거는 확인되지 않았습니다. 선택 객실·좌석속성 4필드는
        PriceReCalculationIn.java:38-41 에 있으나 값을 채운 라이브 검증은 없습니다. 일반 경로 default-null 의 기존 근거는
        PayViewModel.smali:11834-11850 입니다.

        2026-09-22: 무변경 요청은 ERR930202, 할인 변경 표본(hidDcntKndCd='131')은 SUCC/IRZ000008 과 ReservationOut 을 반환했고 12스칼라·여정 추가
        필드도 파싱됐습니다. 3개 열차에서 재현된 기록입니다. 동일 PNR 재요청은 비교값에 따라 WRE800036 또는 성공으로 달랐습니다. 자동 재시도하지 마십시오. 자격
        검증과 할인 반영이 어긋난 관측도 있으므로 자격 없는 할인을 신청하는 용도로 사용하지 마십시오. 할인 코드 반영만으로 금액 변경을 보장하지 않습니다. 토요일 두 표본은
        WRR664296 과 금액 유지, 평일 표본은 28,600→20,000원(할인액 8,600원)이었습니다. 이는 표본 기록이지 일반 보장이 아닙니다.
        """
        self._require_session("price recalculation requires")
        route = "/classes/com.korail.mobile.certification.PriceReCalculation"
        form = build_price_recalculation_form(self.config, request)
        # 변경 응답을 받은 뒤 타입 파싱이 실패할 수 있습니다. 공통 변경 경로가 원문을 보존하며, 홀드가 실제로 변경됐는지 확인하기 전에는 같은 재계산을 다시 보내지
        # 않습니다.
        return self._mutation(
            route,
            form,
            parser=parse_reservation_hold_response,
        )

