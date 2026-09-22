# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

""":class:`KorailClient` — 이 패키지에 하나뿐인 진입점.

여기에는 클래스가 하나뿐입니다. 라우트를 고르고, 폼을 만들고, 응답을 파싱하는 일은
전부 :mod:`korail_mobile_api.read_payloads`,
:mod:`korail_mobile_api.mutation_payloads`,
:mod:`korail_mobile_api.read_parsers` 에 있고 이 모듈은 그것들을 순서대로 엮어
메서드 하나로 만듭니다.

로그인·읽기 메서드와 상태를 바꾸는 메서드 모두, 인증된 세션만 있으면 즉시
전송됩니다. 어떤 범주가 어떤 라우트를 소유하는지는 :mod:`korail_mobile_api.safety`
가 정하고 전송 직전에 다시 검사합니다.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal, TypeVar, overload

import httpx

from .config import KorailConfig
from .constants import KorailReservationJobType, KorailSeatClass
from .crypto import generate_sid
from .errors import (
    KorailAuthError,
    KorailNoDirectTrainError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from .http import KorailHttpClient
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
    validate_seat_inventory_inputs,
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
    build_crew_request_list_query,
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
from .safety import MutationCategory
from .session import KorailSessionClient


T = TypeVar("T")


def _scalar_text(value: object) -> str | None:
    """KORAIL 스칼라를 텍스트로. 따옴표로 왔든 숫자로 왔든 같게 만듭니다.

    ``type(...) is int`` 는 bool 을 제외합니다. bool 은 int 의 하위 타입이지만
    KORAIL 의 신원 값으로 오는 일이 없습니다.
    """
    if isinstance(value, str):
        return value
    if type(value) is int:
        return str(value)
    return None


class KorailClient:
    """KORAIL 모바일 앱(코레일톡)의 비공개 API 를 그대로 부르는 클라이언트.

    :class:`~korail_mobile_api.config.KorailConfig` 기본값이 앱의
    ``Device``/``Version``/``Key`` 를 채우므로 읽기는 ``KorailClient()`` 로 바로 됩니다.
    DynaPath 안티오토메이션은 기본으로 **꺼져** 있어, 로그인하려면
    ``KorailClient(KorailConfig(enable_dynapath=True))`` 로 켜야 합니다. 끈 채
    :meth:`login` 을 부르면 전송 전에
    :class:`~korail_mobile_api.errors.KorailDynaPathRequiredError` 로 막힙니다.
    ``transport`` 는 시험용 :mod:`httpx` 전송로를 끼워 넣는 자리입니다.

    상태를 바꾸는 메서드는 읽기 메서드와 마찬가지로 세션만 있으면 즉시
    전송됩니다. 어떤 라우트가 어떤 범주에 속하는지는
    :mod:`korail_mobile_api.safety` 가 정하고 전송 직전에 다시 검사합니다.

    자원 정리는 :meth:`close` 입니다. ``__enter__``/``__exit__`` 를 정의하지 않으므로
    ``with`` 문으로는 쓸 수 없습니다. :meth:`close` 는 커넥션 풀만 닫으니 로그인까지
    끝내려면 :meth:`logout`(서버 세션 무효화)이나 :meth:`clear_session`(로컬만 폐기)을
    따로 부르면 됩니다.

    .. code-block:: python

        from korail_mobile_api import KorailClient, KorailConfig, TrainSearchQuery

        client = KorailClient(KorailConfig(enable_dynapath=True))
        client.login("1234567890", "비밀번호")
        result = client.search_trains(
            TrainSearchQuery(
                departure_station_code="서울",
                arrival_station_code="부산",
                departure_date="20260801",
                departure_time="060000",
            )
        )
        for train in result.trains:
            print(train.train_no, train.departure_time)
        client.logout()
        client.close()
    """

    def __init__(
        self,
        config: KorailConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        self.session = KorailSessionClient(self.http)
        self._station_names: dict[str, str] | None = None

    def close(self) -> None:
        """HTTP 커넥션 풀을 닫습니다. 로그인 상태는 건드리지 않습니다.

        :meth:`~korail_mobile_api.http.KorailHttpClient.close` 로 위임하며 네트워크
        호출을 하지 않습니다. 로그인까지 끝내려면 먼저 :meth:`logout`(서버 세션 무효화)
        이나 :meth:`clear_session`(로컬만 폐기)을 부르면 됩니다.
        """
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
        """회원 자격증명으로 로그인하고 살아 있는 세션을 돌려줍니다.

        ``POST login.Login``(``LoginService.java:17``). 부르는 즉시 기존 세션을 먼저 버리고,
        서비스 상태 캐시와 비밀번호 암호화 파라미터(``common.code.do``)를 읽은 뒤 변환한
        비밀번호를 보냅니다.

        ``member_no`` 는 회원번호·휴대폰번호·이메일 중 아무거나 되고, ``input_flag`` 를 주지
        않으면 :func:`~korail_mobile_api.session.infer_login_input_flag` 가 값의 모양을 보고
        ``"2"``/``"4"``/``"5"`` 중에서 고릅니다.

        :class:`~korail_mobile_api.models.KorailSession` 을 돌려주며 여기에 ``JSESSIONID``,
        회원카드번호, 고객번호(``strCustNo``)가 담깁니다.

        서버가 ``strRedirectUrl`` 을 주면 2단계 인증이 필요하다는 뜻이라
        :class:`~korail_mobile_api.errors.KorailAuthContinuationRequired` 를 올리고 그 예외를
        ``session.pending`` 에 남깁니다. 그 밖의 실패는
        :class:`~korail_mobile_api.errors.KorailAuthError` 이며, 쿠키가 오지 않은 성공 응답도
        같은 예외로 막습니다.
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
        """Use the APK's customer-ID login branch after provider authentication.

        The provider's ``input_flag`` and the APK's protected
        ``checkValidPw`` value must be supplied by the caller. No provider SDK
        token exchange or local credential storage occurs here.
        """
        return self.session.login_social(
            cust_id,
            input_flag=input_flag,
            check_valid_pw=check_valid_pw,
        )

    def clear_session(self) -> None:
        """서버에 알리지 않고 로컬 로그인 상태만 버립니다.

        쿠키 저장소(``JSESSIONID`` 포함), 현재 :class:`KorailSession`, 보류 중인 2단계
        인증 상태를 모두 비웁니다. 네트워크 호출이 없으므로 서버 쪽 세션은 스스로 만료될
        때까지 살아 있습니다. 서버 세션까지 무효화하려면 :meth:`logout` 을 쓰면 됩니다.
        """
        self.session.clear_session()

    def logout(self) -> None:
        """서버 세션을 무효화하고 로컬 로그인 상태도 버립니다.

        7.0.6 앱과 같이 ``login.Logout``에 ``timeStamp``와 공통 필드가 든
        폼 POST를 보냅니다. ``JSESSIONID`` 쿠키로 현재 세션을 가리킵니다.

        로그인 상태가 아니면 요청 자체를 보내지 않습니다. 서버 무효화는 최선노력이라
        전송이 실패하거나 세션이 이미 만료돼 있어도 예외를 올리지 않고, 로컬
        상태(:meth:`clear_session` 이 지우는 것들)는 어느 경우에나 비워집니다. HTTP
        커넥션 풀은 그대로 남으니 :meth:`close` 는 따로 부르면 됩니다.
        """
        self.session.logout()

    def _run_read(self, operation: Callable[[], T]) -> T:
        """P058 → clear_session → 재발생; 읽기·변경 골격이 함께 씁니다."""
        try:
            return operation()
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def _require_session(self, what: str = "account read requires") -> None:
        """No session, no request: ``KORAIL <what> an authenticated session``."""
        if self.session.current is None:
            raise KorailAuthError(f"KORAIL {what} an authenticated session")

    def _require_customer_no(self, what: str) -> str:
        """No session or customer number: ``KORAIL <what> requires a login customer number``."""
        self._require_session()
        session = self.session.current
        customer_no = session.customer_no if session is not None else None
        if not isinstance(customer_no, str) or not customer_no.strip():
            raise KorailAuthError(f"KORAIL {what} requires a login customer number")
        return customer_no

    # ------------------------------------------------------------------
    # Internal helpers: the read skeleton (post/get → parser → _run_read) and
    # the mutation skeleton (_mutation: post → _run_read → parse),
    # both sharing _run_read's session-expiry handling
    # ------------------------------------------------------------------

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
        category: MutationCategory,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: None = ...,
        raise_on_fail: bool = ...,
    ) -> BaseKorailResponse: ...

    @overload
    def _mutation(
        self,
        category: MutationCategory,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: Callable[[dict[str, Any]], T],
        raise_on_fail: bool = ...,
    ) -> T: ...

    def _mutation(
        self,
        category: MutationCategory,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        parser: Callable[[dict[str, Any]], T] | None = None,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse | T:
        """상태변경 메서드의 공통 골격: 전송 → 파싱 → 세션만료 복구."""
        response = self._run_read(
            lambda: self.http.post_mutation_form(
                route,
                form,
                category=category,
                raise_on_fail=raise_on_fail,
            )
        )
        if parser is not None:
            return parser(response.raw)
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
        validate_seat_inventory_inputs(train, passenger_count)
        form = build_seat_car_form(
            self.config,
            train,
            passenger_count=passenger_count,
            sid=generate_sid(),
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
    ) -> SeatInventoryResponse:
        """한 호차의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다.

        2026-09-21 실서버 확인: 같은 세션에서 :meth:`get_seat_cars` 를 먼저
        호출하지 않고 이 메서드를 바로 부르면 ``KorailAppError: [3]인증정보에
        문제가 있습니다`` 가 돌아올 수 있습니다 — 실앱의 화면 진입 순서(호차
        목록 → 좌석 배치도)와 같습니다. 호출 순서를 지키십시오.
        """
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
        """입금은행 코드표. ``POST dlay.dptnBank.do``(``DelayService.java:30``). 로그인 필요."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.dlay.dptnBank.do",
            parser=parse_deposit_bank_response,
        )

    def get_delay_discount_tickets(
        self,
        departure_date_to: str,
    ) -> DelayDiscountTicketListResponse:
        """지연할인권 조회. ``POST passCard.DelayDiscountView``(``PassCardService.java:20``).

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
        """할인쿠폰 조회. ``POST passCard.CouponView``(``PassCardService.java:24``). 로그인 필요.

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
        """포인트·쿠폰·복지자격 요약. ``POST xPoint.MyXPointView``(``XPointService.java:18-20``).

        로그인 필요. 복지 등록 상태(장애인증·보조견)도 함께 옵니다. 응답 필드는
        ``MyXPointViewOut.java:27-74`` 이고 라우트는 ``xPoint.MyXPointView``
        (``NetworkApi.java:515``) 입니다 — 예전에 적혀 있던
        ``MyPageActivity`` 는 6.5.0 클래스로 7.0.6 에 없습니다.
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
            # A success body carries strResult only (its code lives in
            # main_info), so the envelope gate would reject it before
            # the parser ever saw it. A P058/FAIL body still carries the
            # full envelope and is still raised on.
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
            # A success body is {"list": [...], "strResult": "SUCC"}
            # with no h_msg_cd/h_msg_txt, so the envelope gate would
            # reject it before the parser ever saw it. A P058/FAIL body
            # still carries the full envelope and is still raised on.
            require_envelope=False,
        )

    def get_crew_request_list(
        self,
        *,
        timestamp_ms: int | None = None,
    ) -> CrewRequestListResponse:
        """승무원 호출 화면에 띄울 요청 사유 선택지를 조회합니다.

        이전 시그니처의 ``query_division_code`` 는 삭제됐습니다 — 이 라우트의
        실제 DTO(``CrewCallCommonIn.java:50``)에는 그런 필드가 없고, 옛 값은
        무관한 다른 DTO(``TrainScheduleIn`` 등)의 필드명이었습니다. 유일한
        입력은 ``timeStamp`` 이며, 주지 않으면 호출 시점의 밀리초 epoch 입니다.
        자세한 근거는 :func:`~korail_mobile_api.read_payloads.build_crew_request_list_query`
        의 독스트링을 참고하십시오.
        """
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

        네 식별값과 선택적인 ``txt_index`` 는 같은 승차권 상세 응답에서
        가져와야 합니다. ``sale_date`` 는 반환원표일자입니다.
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
        return self._post_read(
            "/classes/com.korail.mobile.reservation.ReservationView",
            {"timeStamp": 0},
            parser=parse_reservation_history_response,
            raise_on_fail=False,
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
        """도우미석 안내문을 받습니다. 사실상 **정적** 응답입니다.

        요청의 좌석속성코드가 무엇이든 같은 안내가 ``FAIL``/``MRR800011`` 로
        돌아옵니다(2026-09-22: 14종 전부 동일). 그래서 ``raise_on_fail=False``
        입니다 — 여기서 ``FAIL`` 은 실패가 아니라 그 안내문을 싣는 방식입니다.
        :class:`~korail_mobile_api.read_payloads.GuideSeatConditionRequest`
        참조.
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
    ) -> SeatAssignmentScheduleResponse:
        """좌석배정 예매 화면이 쓰는 열차 목록을 조회합니다.

        ``menu_id`` 가 결과를 정합니다. 일반 검색 메뉴 ``"11"`` 로 부르면
        서버는 ``SUCC``/``WRG000000`` 에 **빈 목록**으로 답합니다(2026-09-22,
        7가지 변형 전부). 행이 오는 것은 좌석배정·할인 메뉴 ``"A1"``/``"A2"``
        (:data:`~korail_mobile_api.constants.KORAIL_DISCOUNT_CARD_MENU_ID`)
        이고, 7.0.6 도 이 라우트에 일반 검색 메뉴를 보내지 않습니다
        (``TrainScheduleViewModel.java:2639-2754``). 빈 결과가 곧 "해당 열차
        없음" 이 아니라 "메뉴가 틀렸음" 일 수 있다는 뜻입니다.

        ``"A1"``/``"A2"`` 라도 날짜·구간에 따라 ``WRD000057``
        (명절대수송기간)로 거절될 수 있습니다.
        """
        return self._post_read(
            "/classes/com.korail.mobile.research.assignScheduleView.do",
            build_seat_assignment_schedule_form(request),
            parser=parse_seat_assignment_schedule_response,
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
        """N카드 2인 승차권을 **전달하기 전에** 수령자 후보를 조회합니다.

        이미 전달된 승차권의 수령자를 보는 곳이 아닙니다 — 예전 서술이
        그렇게 읽혀 오해를 샀습니다. 7.0.6 은 전달 화면을 만드는 동안에만
        이것을 부르고, 그나마 ``isNCardTwoPeople()`` 일 때뿐입니다
        (``DeliveryTicketFormViewModel.java:697-700``, 즉
        ``TicketDetailOut.pbpAcepPsQryFlg == 'Y'``). 답은
        ``DeliveryTicketEffect.NCardTwoPeopleUpdated`` 로 흘러갑니다.

        그래서 N카드 2인 승차권이 아니면 ``IRZ000005``("조회된 자료가
        없습니다")가 **정상 응답**입니다 — 2026-09-22 에 이 계정의 승차권
        60장이 전부 그랬습니다.

        이미 전달된 승차권의 수령자가 필요하면
        :meth:`get_pbp_acceptance_specifications` 를 쓰십시오. 그쪽
        ``jrnyList`` 행에 ``acepCustNm``/``acepCustTeln``/``pbpAcepKndNm``/
        ``pbpRsvNo`` 가 있습니다.
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

        :meth:`refund` 와 같은 단위, 즉 ``ticket`` 이 지목한 **승차권 한 장** 에
        대한 답입니다. 2인 PNR 의 한 장을 넣으면 8,400원이라고 답하는데, 그것은 결제
        총액 16,800원을 잘못 센 것이 아니라 그 한 장을 반환하면 실제로 8,400원이
        돌아온다는 정확한 답입니다. 총액을 알고 싶으면 장마다 물어야 합니다.
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
        """공통코드 표를 조회합니다 — 한 호출에 코드를 여러 개 실을 수 있습니다.

        ``code`` 는 문자열 하나이거나 문자열 시퀀스입니다. 어느 쪽이든 전선에서는
        ``code`` 라는 같은 이름의 반복 키가 되고, 서버는 요청한 키 전부를 한 본문에
        담아 돌려줍니다.

        **이전 시그니처는 ``code: str`` 하나였습니다.** 그건 코드 하나마다 왕복
        하나를 강제하는데, 라우트도 앱도 그렇게 동작하지 않으므로 틀린 좁힘이었습니다
        — 7.0.6 은 같은 경로에 Retrofit 바인딩을 둘 선언하고
        (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:317``
        ``postCommonCode(@FieldMap)``, ``:321`` ``postCommonCodeMulti(@FieldMap,
        @Field("code") List<String>)``), 부팅 시퀀스는 코드 22 개를 한 리스트로 묶어
        (``analysis/jadx/sources/com/korail/talk/network/NetworkService.java:2015``,
        ``DEBUG`` 빌드면 ``:2017-2018`` 에서 둘 더) **한 번**의
        ``postCommonCodeMulti`` 로 보냅니다(``:2025``). 단일 바인딩을 쓰는 곳은
        ``NetworkService.java:1829`` 하나뿐입니다. 2026-09-22 실서버 확인:
        :data:`~korail_mobile_api.constants.KORAIL_COMMON_CODE_BOOTSTRAP_CODES`
        18 개를 한
        POST 로 보내 ``API.I00000``/``SUCC`` 와 요청한 18 키 전부가 한 본문에 왔고,
        같은 코드들을 하나씩 따로 부른 값과 바이트 단위로 같았습니다. 즉 코드 N 개를
        원하면 왕복도 1 번이면 됩니다.

        모르는 코드는 오류가 아닙니다 — ``raw`` 에 그 이름의 키가 빈 문자열 값으로
        옵니다(``'app.no.such.code'`` → ``SUCC``, 값 ``''``). 기본값 ``""`` 도
        거절되지 않고 이름이 ``''`` 인 빈 항목 하나로 돌아옵니다. 둘 다 2026-09-22
        확인이며, 라이브러리가 오류를 삼킨 게 아니라 서버 응답을 그대로 옮긴 것입니다.
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
        """Read generic or ticket-specific MaaS menus.

        The ticket-detail screen supplies its PNR and one or more original
        return numbers. The latter are repeated ``tkRetNo`` form fields in the
        7.0.6 Retrofit declaration, rather than a joined value.
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

    def get_station_info(self, device: Literal["AD"] = "AD") -> StationInfoResponse:
        """역 데이터의 판본과 수록 역 수를 빈 POST로 조회합니다.

        ``device``는 이전 공개 인자 호환용이며 7.0.6 요청에는 실리지 않습니다.
        """
        # The annotation does not reach an untyped caller; this does.
        if device != "AD":
            raise KorailProtocolError(
                "7.0.6 station info does not accept a device parameter"
            )
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
    ) -> TrainSearchResult:
        """한 구간·한 날짜의 직통 열차 한 페이지를 조회합니다."""
        return self._run_read(
            lambda: self._search_trains(
                query, continuation, use_special_schedule=use_special_schedule
            )
        )

    def search_transfer_trains(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
        use_special_schedule: bool = False,
    ) -> TransferSearchResult:
        """같은 질의를 환승 여정으로 바꿔 한 페이지 조회합니다."""
        return self._run_read(
            lambda: self._search_transfer_trains(
                query, continuation, use_special_schedule=use_special_schedule
            )
        )

    def search_trains_with_transfer_fallback(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
        use_special_schedule: bool = False,
    ) -> TrainSearchResult | TransferSearchResult:
        """직통을 찾고, 하나도 없을 때만 환승으로 한 번 더 찾습니다.

        .. note::

           "하나도 없을 때" 는 **서버가 ``WRD000061`` 로 답할 때** 뿐입니다.
           직통 조회가 ``WRG000000``/``SUCC`` 에 행 0개로 오는 경우도 있는데
           (2026-09-22 확인), 그때는 환승으로 넘어가지 않고 빈
           :class:`~korail_mobile_api.models.TrainSearchResult` 를 그대로
           돌려줍니다. 즉 이 메서드가 ``TrainSearchResult`` 를 돌려줬다고 해서
           직통 열차가 있다는 뜻은 아니므로 ``trains`` 를 확인해야 합니다.

        지어낸 편의기능이 아니라 앱의 흐름 그대로입니다. 직통 조회가 아무것도 못 찾으면
        서버가 ``WRD000061``("직통열차가 없습니다")로 답하는데, 7.0.6
        ``TrainScheduleViewModel`` 은 ``responseTrainSchedule()`` 에서 오직 그
        코드만 잡아 확인 창을 띄우고(smali:35513-35566), 확인을 누르면
        ``changeFilterTransfer()``/``updateTrainScheduleFilterData()``
        (java:3216-3219, :11051-11079)를 거쳐 ``buildTrainScheduleIn()``
        (java:3136, :3212)이 ``radJobId="2"`` 로 다시 질의합니다. 이 클라이언트도
        ``WRD000061`` 을 :class:`~korail_mobile_api.KorailNoDirectTrainError` 로 분류하므로
        되돌리는 조건은 그 예외 하나뿐이고 다른 실패는 그대로 올라갑니다.

        어느 쪽이 일어났는지는 반환 타입이 말해 줍니다 —
        :class:`~korail_mobile_api.TrainSearchResult` 면 직통이 성공한 것이고,
        :class:`~korail_mobile_api.TransferSearchResult` 면 직통이 없어서 받아 온 환승
        대안입니다.

        ``continuation`` 은 직통 조회에만 전달합니다. 커서는 그것을 만든 조회에 묶인 값이라
        되돌린 환승 조회는 언제나 첫 페이지부터입니다.
        """
        try:
            return self.search_trains(
                query,
                continuation=continuation,
                use_special_schedule=use_special_schedule,
            )
        except KorailNoDirectTrainError:
            return self.search_transfer_trains(
                query, use_special_schedule=use_special_schedule
            )

    def _search_trains(
        self,
        query: TrainSearchQuery,
        continuation: TrainSearchContinuation | None = None,
        *,
        use_special_schedule: bool = False,
    ) -> TrainSearchResult:
        response = self._post_schedule_view(
            query, continuation, transfer=False,
            use_special_schedule=use_special_schedule,
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
    ) -> TransferSearchResult:
        response = self._post_schedule_view(
            query, continuation, transfer=True,
            use_special_schedule=use_special_schedule,
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
                sid=generate_sid(),
                member_card_no=current.member_card_no if current else None,
                continuation=continuation,
                transfer=transfer,
            )
            route = "/classes/com.korail.mobile.seatMovie.ScheduleView"
        return self.http.post_form(
            route,
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
        """로그인 계정의 승차권 목록을 예약→승차권 구조로 돌려줍니다.

        7.0.6 ``POST myTicket.MyTicketNewList.do``. 로그인 필요.

        원본 JSON은 ``raw``에 그대로 보존됩니다.

        ``mode`` 는 페이지 커서가 아니라 목록 종류입니다 — ``"1"`` 은 현재
        승차권(``TicketListActivity.java:937-939``), ``"2"`` 는
        구매이력(``TicketPurchaseHistoryActivity.java:276-278``)이고 그 밖의 값은 거부됩니다.
        ``"2"`` 는 ``boarding_date_from``·``boarding_date_to`` 를 둘 다 ``YYYYMMDD`` 로
        요구하지만 **이 클라이언트가 그것을 강제하지는 않습니다.** 비었거나 자릿수가
        틀리거나 앞뒤가 뒤집힌 범위도 그대로 나가고 서버가 ``WRT100101``
        ("일자를 확인해주세요 / 3개월단위로 조회할 수 있습니다")로 거절합니다 —
        2026-09-22 에 빈 두 값, ``from`` 만 채운 값(``"20250101"``), 여섯 자리
        값(``"202501"``/``"202612"``), 뒤집힌 범위(``"20261231"``→``"20250101"``)
        네 경우를 모두 실서버에서 확인했습니다. 이전 문장은 "한쪽이라도 비면 요청을
        만들기 전에 막습니다" 라고 적혀 있었는데 그런 검사는 코드에 없습니다
        (``payloads.build_ticket_list_form`` 은 ``mode`` 만 검증하고 두 날짜는
        ``h_abrd_dt_from``/``h_abrd_dt_to`` 로 그냥 흘려보냅니다) — 같은 함수의
        도크스트링이 처음부터 정직했던 쪽입니다. 거꾸로, 서버 문구의 "3개월단위" 도
        강제되지 않습니다: ``20250101``→``20261231`` 2 년 범위가 128 행,
        ``20260901``→``20260922`` 가 3 행을 돌려줬습니다. 즉 ``WRT100101`` 을
        부르는 것은 기간의 길이가 아니라 빠졌거나 폭이 틀렸거나 뒤집힌 범위입니다.
        ``"1"`` 은 두 값을 빈 문자열로 보냅니다.

        ``page_no`` 는 ``h_page_no`` 로 나가고 1 미만은 1 로 올려 보내므로 기본값 ``0`` 도 첫
        페이지를 뜻합니다.
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
        """열차 한 편에 결제 전 예약을 잡습니다.

        로그인 세션을 요구합니다. ``train`` 을 검증하고 이중 게이트 전송로로 홀드를
        걸고 파싱한 :class:`ReservationHoldResponse` 를 돌려줍니다. 그 ``pnr_no`` 가
        :meth:`cancel_unpaid_hold` 의 입력입니다 — 살아 있는 홀드는 미결제 예약이고
        취소하든 결제하든 호출자 책임입니다.

        ``seat_attribute_code`` 는 ``txtSeatAttCd4`` 로 나가는 세 자리 좌석 속성
        코드입니다. 주지 않으면 열차 행의 ``seat_attribute_code`` 를, 그것도 없으면
        ``"015"`` 를 씁니다(7.0.6 ``TrainScheduleViewModel.java:2914-2930,2982-2999``).

        ``job_type`` 은 :class:`KorailReservationJobType` 이고 기본이
        ``IMMEDIATE``(``txtJobId="1101"``)입니다.

        * ``SEAT_DESIGNATED``(``"1103"``)는 좌석지정 예매라 ``seats`` 가 필요합니다 —
          승객 한 명당 정확히 하나의 :class:`KorailSeatAssignment` 를
          :meth:`get_seat_cars` 와 :meth:`get_seat_inventory` 에서 골라 넘깁니다. 수가
          승객 총원과 맞지 않으면 요청을 만들기 전에 거절합니다.
        * ``STANDBY``(``"1102"``)는 예약대기이고, 검색 행이 대기 가능이라고 말한
          열차에만 붙습니다. 회원 전용입니다(``ReservationRequest.java:105-119``) — 이
          클라이언트는 모든 상태 변경이 로그인 세션을 요구하므로 구조적으로 그 조건을
          만족합니다. 성공한 대기 홀드는 ``h_msg_cd`` 가
          :data:`~korail_mobile_api.KORAIL_STANDBY_HOLD_MESSAGE_CODE`(``IRR000014``)로
          오고, :meth:`confirm_standby_hold` 로 알림 옵션을 기록해야 비로소 끝납니다.
        * ``MERGE_STANDING``(``"1202"``)은 병합예약의 첫 홀드입니다. 두 번째 홀드는
          :meth:`reserve_merge` 가 겁니다.
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
        return self._mutation(
            "reserve",
            route,
            form,
            parser=self._hold_from_reservation_response,
        )

    def confirm_standby_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        allow_seat_class_change: bool = False,
        sms_notify: bool = False,
        phone_no: str | None = None,
    ) -> BaseKorailResponse:
        """예약대기 홀드에 대기 옵션을 기록합니다.

        예약대기는 호출 두 번입니다. ``job_type=STANDBY`` 로 부른 :meth:`reserve` 가
        PNR 을 만들고 ``h_msg_cd`` = ``IRR000014`` 를 돌려주는데, 앱은 이 코드에서만
        예약대기 화면을 엽니다(``ui/inquiry/rir/orr/a.java:222-225``). 그 화면이
        사용자의 선택을 실어 보내는 두 번째 POST 가 이 메서드입니다 —
        ``reservationWait.ReservationWait``(``ReservationWaitService.java:10-12``).

        로그인 세션을 요구하고, 다른 모든 상태 변경과 같은 이중 게이트 전송로로
        나갑니다. 이미 있는 PNR 의 예약을 마무리할 뿐 돈을 옮기지도 좌석을 놓지도
        않으므로 소비 범주가 ``"reserve"`` 입니다.
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
        return self._mutation("reserve", route, form)

    @staticmethod
    def _hold_from_reservation_response(
        raw: dict[str, Any],
    ) -> ReservationHoldResponse:
        # A live reserve may create a real hold on the server; we must NEVER
        # lose the identity needed to cancel it. Strict parsing can raise on an
        # unrelated malformed optional field AFTER the hold exists, so when it
        # does we fall back to a minimal hold that still carries the PNR and
        # journey count, letting the caller auto-cancel. We only re-raise when
        # no PNR was returned (no hold to orphan).
        try:
            return parse_reservation_hold_response(raw)
        except KorailProtocolError as exc:
            # Bound as `exc` so the original parse failure is nameable and, if
            # anything below raises a NEW exception, it can be chained with
            # `from exc` instead of being lost. The bare `raise` just below
            # re-raises this SAME exception object, which already preserves
            # its traceback without needing `from exc` -- chaining only
            # matters when constructing a different exception.
            #
            # A PNR or journey count that arrived as a JSON number is a hold we
            # can still cancel, so normalise both here the same way the parser
            # does rather than discarding the only identity we have.
            pnr = _scalar_text(raw.get("h_pnr_no"))
            if not (pnr and pnr.strip()):
                raise
            try:
                base = BaseKorailResponse.from_raw(raw)
            except KorailProtocolError as envelope_exc:
                raise envelope_exc from exc
            # journey_count deliberately does NOT stay None here. The whole
            # purpose of this fallback is to preserve enough identity for the
            # caller to auto-cancel a hold that may have actually been created
            # server-side via cancel_unpaid_hold(). That path's
            # build_unpaid_reservation_cancel_form() requires journey_count to
            # be a digit string (ReservationCancelChkIn.txtJrnyCnt is a
            # non-null String on the wire -- see
            # ReservationCancelChkIn.java's synthetic constructor, which has
            # no null-tolerant slot for this field). If the very field that
            # failed strict parsing was h_jrny_cnt itself, _scalar_text would
            # return None here, and a None journey_count would make the cancel
            # builder raise KorailProtocolError too -- turning one confusing
            # failure into a second, harder-to-diagnose one on the exact path
            # this fallback exists to keep open. This library's own reserve()
            # docstring states single-leg and multi-leg (max
            # KORAIL_MAX_JOURNEY_LEGS == 2) are the only shapes reserve() ever
            # produces, so "1" is a conservative single-journey assumption --
            # not a guess at what the server actually sent, but the minimum
            # that keeps cancel_unpaid_hold callable. This mirrors the
            # existing last-resort literals in mutation_payloads.py
            # (_ABSENT_JOB_SEQUENCE, _ABSENT_RESERVATION_CHANGE_NO): an
            # explicit, documented fallback instead of a silent None that
            # fails again downstream.
            journey_count = _scalar_text(raw.get("h_jrny_cnt")) or "1"
            return ReservationHoldResponse(
                h_msg_cd=base.h_msg_cd,
                h_msg_txt=base.h_msg_txt,
                str_result=base.str_result,
                raw=raw,
                pnr_no=pnr,
                journey_count=journey_count,
            )

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
        """환승 여정 하나를 두 구간·한 PNR 로 홀드합니다.

        라우트도 범주도 세션 요구도 :meth:`reserve` 와 같습니다. 앱도 엔드포인트와
        요청 빌더를 하나만 쓰고 구간 수만 폼을 바꿉니다(``C5/a.java:52-119``).
        돌려주는 홀드에 대해 :meth:`reserve` 가 말한 것이 그대로 적용됩니다.

        ``legs`` 는 탑승 순서대로 정확히 두 개의
        :class:`~korail_mobile_api.TrainSummary` 여야 하고,
        :meth:`search_transfer_trains` 가 준 :attr:`TransferItinerary.legs
        <korail_mobile_api.TransferItinerary.legs>` 가 그것입니다. 다른 개수는 폼을
        만들기 전에 거절합니다(:data:`~korail_mobile_api.KORAIL_MAX_JOURNEY_LEGS`).

        ``seat_classes`` 는 두 구간에 하나를 주거나 구간마다 하나를 줍니다 — 앱의 실별
        선택이 구간별입니다(``C5/a.java:59``, ``:97``). ``seats`` 도 마찬가지로
        구간마다 한 묶음입니다(``C5/a.java:120-133``).

        **2026-07-31 실서버 확인.** 서울→여수EXPO 를 :meth:`search_transfer_trains`
        로 찾아 서울→오송(열차 009) + 오송→여수EXPO(열차 503) 를 성인 1명으로 보내
        ``SUCC``/``IRR000018``, 49,700원, PNR 하나를 받았습니다. 되읽은
        상세의 ``journey_count`` 가 ``"2"`` 였고 :meth:`cancel_unpaid_hold` 가 PNR
        하나로 두 구간을 함께 해제했습니다 — SRT 쪽과 달리 취소에 여정 수를 따로
        줄 필요가 없습니다. 확인된 것은 **1인·일반실·편도** 한 건입니다.
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
        return self._mutation(
            "reserve",
            route,
            form,
            parser=self._hold_from_reservation_response,
        )

    def reserve_merge(
        self,
        standing_hold_train: TrainSummary,
        legs: Sequence[TrainScheduleItem],
        *,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
        seat_attribute_code: str | None = None,
    ) -> ReservationHoldResponse:
        """한 열차를 중간역에서 나눈 병합예약을 홀드합니다.

        병합 흐름의 두 번째이자 마지막 홀드입니다. 첫 번째는
        ``job_type=KorailReservationJobType.MERGE_STANDING``(``"1202"``, 입석+좌석
        예매)으로 부르는 :meth:`reserve` 입니다. 나누는 지점은
        :meth:`get_merge_seats_inquiry` 가 알려준 중간역이고, 다섯 단계 전체와 그
        근거는
        :data:`~korail_mobile_api.constants.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE`
        에 적혀 있습니다.

        **이 도크스트링은 두 가지를 틀리게 적고 있었습니다. 되돌리지 마십시오.**

        하나, "``MERGE_STANDING`` 이 전 구간을 입석으로 잡는다" 는 틀립니다. 그
        첫 홀드가 **이미** ``h_jrny_cnt='0002'`` 에 ``h_jrny_tp_cd``
        ``"21"``/``"22"`` 인 두 여정으로 중간역에서 쪼개져 돌아옵니다 — 2026-09-22
        열차 305 대전→울산(통도사) ``20260923``: 선행 대전→동대구
        ``h_seat_no='입석'``(15,000원), 후행 동대구→울산(통도사) 실좌석
        ``'10A'``(9,600원). 열차 005 에서도 같은 모양(입석 14,600원 + ``'3C'``
        9,600원)이었고, 같은 PNR 을 :meth:`get_ticket_reservation_detail` 로
        되읽어도 ``21``/``22`` 와 같은 좌석이 나옵니다. 즉 입석이 되는 것은 선행
        구간뿐이고, 아래에서 보듯 아예 한 구간도 입석이 아닐 수 있습니다. 바로 위
        ``"1202"`` 를 "입석+좌석 예매" 라고 부르는 문구가 처음부터 옳았고, 그 두 줄
        아래 문장이 그것과 모순돼 있었습니다.

        둘, 이 메서드가 그 홀드를 "바꾼다" 는 것도 틀립니다. **변환이 아니라
        별도의 두 번째 PNR 을 만듭니다** — 2026-09-22 열차 305 에서 입석 홀드와
        이 호출의 ``pnr_no`` 가 서로 달랐고, 새 PNR 은 똑같이 ``21``/``22`` 모양에
        양쪽 다 진짜 좌석(``4C``, ``5A``)이라 입석 구간이 하나도 없었습니다.
        입석 홀드는 그대로 살아 있으므로 **둘 다** 취소해야 합니다.

        호출 순서도 관측됐습니다. 입석 홀드를 살려 둔 채 이 메서드를 부르면
        ``WRR664260``("동일한 시간대에 예약 또는 구매하신 승차권이 존재합니다")이
        오고, 앱과 같은 순서로 입석 홀드를 먼저 취소한 뒤 부르면 완전히 같은
        호출이 ``IRR000018``("결제하지 않으면 예약이 취소됩니다")로 통과합니다.
        ``WRR664260`` 은 프로토콜 실패가 아니라 겹치는 홀드에 대한 정상적인
        업무규칙 응답입니다.

        .. warning::
           ``WRR664260`` 은 **거절이 아닙니다.** 2026-09-22 확인: 그 응답도
           ``strResult='SUCC'`` 에 새 ``pnr_no`` 와 좌석(``4C``/``5A``)이 붙은
           온전한 홀드였고, 예외도 오르지 않았습니다. 이것을 "실패했으니 치울 게
           없다" 로 읽으면 **실제로 잡힌 좌석을 그대로 흘립니다.** 이 메서드가
           돌려준 것은 ``h_msg_cd`` 가 무엇이든 ``pnr_no`` 가 있으면 홀드이니
           :meth:`cancel_unpaid_hold` 로 치우십시오.

        입석 홀드를 대신 취소하지는 않습니다. 앱은 다시 예약하기 전에 그것을
        취소하지만(7.0.6 ``ReservationMergeViewModel.java:1352``
        ``requestReservationCancel``, :1556 ``requestReservationCancelChk`` —
        ``analysis/reports/7.0.6-compare/booking-ticket-payment.md`` 의 기존
        분석과도 일치), 여기서는 "cancel" 범주
        아래의 :meth:`cancel_unpaid_hold` 로 호출자가 직접 합니다 — "reserve" 범주
        호출로 살아 있는 PNR 을 조용히 취소하는 것은 이 게이트들이 막으려는 범주
        혼동 그 자체입니다.

        2026-09-21 실서버 확인: 대전→울산(301, 동대구에서 분할)으로 실제
        호출됨 — 홀드 응답의 ``h_jrny_tp_cd`` 가 두 여정에 각각
        :data:`~korail_mobile_api.constants.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE`
        (``"21"``)·
        :data:`~korail_mobile_api.constants.KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE`
        (``"22"``)로 정확히 찍혔고, 입석 구간과 좌석 구간이 문서와 같이
        분리돼 돌아왔습니다. 두 여정 다 단일 :meth:`cancel_unpaid_hold`
        호출로 함께 풀립니다. (2026-09-22 에 밝혀졌듯 그 ``21``/``22`` 분할은 이
        메서드의 홀드에만 있는 게 아니라 앞선 ``MERGE_STANDING`` 홀드에 이미
        있습니다 — 위 문단 참고. 이 확인은 분할이 이 메서드 고유의 결과라는
        뜻으로 읽으면 안 됩니다.)
        """
        self._require_session("reservation requires")
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_merge_reservation_form(
            self.config,
            standing_hold_train,
            legs,
            passengers=passengers,
            seat_class=seat_class,
            seat_attribute_code=seat_attribute_code,
        )
        return self._mutation(
            "reserve",
            route,
            form,
            parser=self._hold_from_reservation_response,
        )

    def cancel_unpaid_hold(
        self,
        hold: ReservationHoldResponse,
    ) -> BaseKorailResponse:
        """결제 전 예약 홀드를 취소합니다. 여정이 몇 개든 상관없습니다.

        로그인 세션을 요구합니다. 이중 게이트 전송로로 POST 한 뒤 파싱한 봉투를
        돌려줍니다.

        앱의 취소 호출 두 개 중 뒤쪽(``ReservationCancelChk``)만 보냅니다. 앞의
        ``ReservationCancel`` 을 생략해도 취소가 성립하는 것은 라이브로 확인했습니다 —
        2026-07-31 직통 홀드가 ``IRG000000`` 으로 풀렸고, 두 여정짜리 환승 홀드는
        2026-07-26 과 2026-07-31 에 PNR 하나로 함께 풀렸습니다.
        """
        self._require_session("cancellation requires")
        route = (
            "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk"
        )
        form = build_unpaid_reservation_cancel_form(self.config, hold)
        return self._mutation("cancel", route, form)

    def pay_with_fake_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
    ) -> ReservationPaymentResponse:
        """미결제 홀드를 비과금 시험카드로 결제 시도합니다.

        로그인 세션을 요구합니다. KORAIL 결제 호출은 카드번호를 평문으로 싣기
        때문에, ``card`` 는 PG 가 거절할 비과금 시험카드여야 합니다.

        이중 게이트 전송로로 POST 하고 파싱한 :class:`ReservationPaymentResponse`
        를 돌려줍니다.
        """
        self._require_session("payment requires")
        route = "/classes/com.korail.mobile.payment.ReservationPayment"
        form = build_card_payment_form(self.config, hold, card)
        # raise_on_fail=False: a declined card is an answer to read, not an
        # error to raise.
        return self._mutation(
            "payment",
            route,
            form,
            parser=parse_reservation_payment_response,
            raise_on_fail=False,
        )

    def pay_with_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
    ) -> ReservationPaymentResponse:
        """미결제 홀드를 실제 청구되는 카드로 결제합니다.

        로그인 세션을 요구합니다. ``card`` 의 카드번호가 실제로 청구되는 카드여야
        합니다 — 이 메서드는 :meth:`pay_with_fake_card` 와 별개의 메서드로, 호출자가
        메서드 이름으로 그 사실을 명시합니다.

        전선 모양은 :meth:`pay_with_fake_card` 와 같습니다. 둘 다 같은
        ``build_card_payment_form`` 을 만들고 같은 이중 게이트
        :meth:`~korail_mobile_api.http.KorailHttpClient.post_mutation_form` 으로
        나가므로, 실제 결제가 라이브로 검증된 모양에서 벗어날 수 없습니다.

        실제 돈으로 확인했습니다. 2026-07-31 에 8,400원 한 장이 ``IRT000000`` 으로
        결제·발권됐고 같은 날 2인 PNR 도 결제했으며, 2026-09-15 에 7.0.6 판으로 다시
        결제·전액 환불했습니다.
        """
        self._require_session("payment requires")
        route = "/classes/com.korail.mobile.payment.ReservationPayment"
        form = build_card_payment_form(self.config, hold, card)
        # raise_on_fail=False: a declined card is an answer to read, not an
        # error to raise.
        return self._mutation(
            "payment",
            route,
            form,
            parser=parse_reservation_payment_response,
            raise_on_fail=False,
        )

    def refund(
        self,
        ticket: PaidTicket,
        *,
        settle_mileage: bool = False,
        pbp_acceptance_target_flag: str | None = None,
    ) -> RefundTicketResponse:
        """결제까지 끝난 승차권 **한 장** 을 환불합니다.

        ``POST refunds.RefundsRequest``. 로그인 세션을 요구합니다. ``ticket`` 은
        :class:`~korail_mobile_api.mutation_models.PaidTicket`(PNR + 원발매 자격증명 +
        반환비밀번호)이어야 합니다. 이중 게이트 전송로로 POST 한 뒤 파싱한
        :class:`RefundTicketResponse` 를 돌려줍니다.

        **PNR 단위가 아니라 승차권 단위입니다.** ``ticket`` 이 PNR 을 싣기는 하지만
        서버가 되돌리는 것은 ``sale_sequence`` 로 지목된 그 한 장뿐입니다. 승객 2명을
        한 PNR 로 예약하면 승차권이 2장 생기고, 이 메서드를 한 번 부르면 한 장만
        반환됩니다 — 나머지는 결제된 상태로 계정에 남고, 예약 목록은 비어 있어서
        (반환된 것은 예약이 아니라 승차권이므로) 다 끝난 것처럼 보입니다.
        **여러 장이면 장마다 한 번씩 부르십시오.** 남은 장의 신원은
        :meth:`get_ticket_list` 응답에서 ``h_orgtk_wct_no``·``h_orgtk_ret_sale_dt``·
        ``h_orgtk_sale_sqno``·``h_orgtk_ret_pwd`` 로 읽습니다.

        ``pbp_acceptance_target_flag`` 는 **항상 그대로 에코합니다.** 승차권
        상세 조회 등 사전 서버 응답에 실제 값이 있었다면 그 값을 넘기십시오.
        ``None`` 이고 ``ticket.pbp_acceptance_target_flag`` 도 ``None`` 이면
        빈 문자열로 에코합니다 — 이 필드는 7.0.6 응답 DTO
        (``TicketDetailOut.java:167``) 에서도 옵셔널이라 서버가 안 보내면
        빈 문자열로 떨어지고, 실앱 두 호출부 모두 그 값을 검사 없이 그대로
        요청에 싣습니다. 값을 지어내는 게 아니라 실앱과 같은 기본값을 쓰는
        것입니다(W1 finding 7 / :func:`~korail_mobile_api.mutation_payloads.build_refund_form`
        참고).

        **더 이상 ``return_times_division_code`` 인자를 받지 않습니다.** 7.0.6
        은 ``tk_ret_tms_dv_cd`` 를 실제 환불 제출에 절대 싣지 않습니다 — 이
        DTO 를 만드는 두 실호출부 모두 리터럴 ``null`` 을 넘기고, 수수료
        응답의 같은 이름 필드는 UI 다이얼로그 선택에만 쓰입니다(W3
        finding 6). PyPI 배포가 보류 중이라 호환성 약속이 없어, 조용한
        no-op 으로 남기는 대신 시그니처에서 제거했습니다.

        2026-07-31 실서버 확인: 성인 2명 16,800원(8,400×2)을 한 PNR 로 결제한 뒤
        이 메서드를 한 번 부르니
        ``SUCC``/``IRT200277`` 과 함께 8,400원만 돌아왔고, 좌석 032 한 장이
        ``h_rcvd_amt="00000008400"`` 으로 남았습니다. 같은 방식으로 한 번 더 부르니
        비었습니다. 부분 환불을 노린 API 가 아니라, 이것이 이 라우트의 단위입니다.
        """
        self._require_session("refund requires")
        route = "/classes/com.korail.mobile.refunds.RefundsRequest"
        form = build_refund_form(
            self.config,
            ticket,
            settle_mileage=settle_mileage,
            pbp_acceptance_target_flag=pbp_acceptance_target_flag,
        )
        return self._mutation(
            "refund", route, form, parser=parse_refund_ticket_response
        )

    def verify_station_ticket_refund(
        self,
        request: StationRefundVerificationRequest,
    ) -> StationRefundVerificationResponse:
        """역 발행 승차권을 온라인 환불 전에 검증합니다.

        응답 ``VerifyOnlineRefundsOut`` 은 ``CommonOut`` 을 상속하지 않아 ``strResult``
        가 없을 수 있습니다 — :data:`~korail_mobile_api.http._NON_COMMON_OUT_READ_PATHS`
        가 이 경로를 그렇게 다룹니다.
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
            "refund",
            "/classes/com.korail.mobile.refunds.executeOnlineRefunds",
            build_station_refund_execution_form(self.config, request),
            parser=parse_station_refund_execution_response,
        )

    def add_to_cart(
        self,
        request: CartAddRequest,
    ) -> BaseKorailResponse:
        """홀드 중인 예약의 PNR 을 장바구니에 담습니다.

        ``POST cart.addCartList``(``CartService.java:11-13``). 공통 세 필드 말고 요청
        필드는 ``hidPnrNo`` 하나뿐입니다(``AddCartDao.java:9-24``, smali 로 교차 확인).

        로그인 세션을 요구합니다.
        """
        self._require_session("cart add requires")
        route = "/classes/com.korail.mobile.cart.addCartList"
        form = build_cart_add_form(self.config, request)
        return self._mutation("cart", route, form)

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
    ) -> DiscountCardPurchaseResponse:
        """할인카드(N카드)를 구매합니다.

        ``POST research.dcntCrdInfo.do``(``ResearchService.java:68-70``). 경로에
        "Info" 가 붙어 있지만 조회가 아니라 구매입니다 — 응답이 ``lumpStlTgtNo`` 와
        ``rcvdAmt`` 를 주고(``NCardReservationDao.java:127-134``) 앱은 그 대상번호를
        결제 화면으로 그대로 넘깁니다(``SectionNCardInquiryActivity.java:213-257``).
        만들어지는 것은 결제를 기다리는 미결제 구매입니다.
        """
        self._require_session("discount card purchase requires")
        route = "/classes/com.korail.mobile.research.dcntCrdInfo.do"
        form = build_discount_card_purchase_form(self.config, request)
        return self._mutation(
            "discount_card",
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

        ``post_mutation_form`` 게이트로 전송합니다. 로그인 상태를 요구합니다.
        """
        self._require_session("discount card extension requires")
        route = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"
        query = build_discount_card_extension_query(self.config, ticket)
        return self._mutation("discount_card", route, query)

    def reserve_with_discount_card(
        self,
        train: TrainSummary,
        *,
        card_no: str,
    ) -> ReservationHoldResponse:
        """할인카드(N카드)로 좌석 하나를 홀드합니다.

        라우트도 범주도 :meth:`reserve` 와 같습니다. 같은 호출이기 때문입니다 —
        ``w4/a.java:93-104`` 이 평범한 ``ReservationRequest`` 를 만들고
        ``c5/b.java:128-138`` 이 평범한 ``ReservationDao`` 로
        ``certification.TicketReservation`` 에 보냅니다. N카드 전용 예약 엔드포인트는
        없고 N카드 승객 블록이 있을 뿐입니다. 그래서 범주도 ``"reserve"`` 입니다 —
        할인카드를 쓴다고 예약이 예약 아닌 것이 되지 않습니다.
        """
        self._require_session("reservation requires")
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_discount_card_reservation_form(
            self.config,
            train,
            card_no=card_no,
        )
        return self._mutation(
            "reserve",
            route,
            form,
            parser=self._hold_from_reservation_response,
        )

    def recalculate_price(
        self,
        request: PriceRecalculationRequest,
    ) -> ReservationHoldResponse:
        """홀드된 PNR 의 운임을 다른 할인 조합으로 다시 계산합니다.

        ``POST certification.PriceReCalculation``(``CertificationService.java:35-37``,
        ``getDiscountPrice``)입니다. 앱은 예약의 할인 선택이 바뀔 때마다 결제
        화면에서 이것을 쏘고(``a6/C1042B.java:265-296``), 응답은 홀드가 돌려주는 것과
        같은 ``ReservationOut`` 입니다
        (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:584,753``).

        로그인 세션을 요구합니다.

        **부분 검증 경로입니다.** 7.0.6 DTO 는 ``txtPsrmClCd1``,
        ``txtSeatAttCd2``, ``txtSeatAttCd4``, ``txtSeatAttCd5`` 를 더 선언하지만
        (``analysis/jadx/sources/com/korail/talk/network/model/PriceReCalculationIn.java:38-41``)
        이 폼은 넷 중 어느 것도 보내지 않습니다. 그 값은 앱의 화면 상태에서 오는데 그
        경로를 추적하지 않았습니다.

        2026-09-22 에 실서버로 처음 나갔습니다. 홀드 중인 PNR 의 좌석에서
        ``h_psg_tp_cd``/``h_psrm_cl_cd``/``h_dcnt_knd_cd1`` 을 그대로 베낀 한 줄을
        :attr:`~korail_mobile_api.PriceRecalculationRow.requested_discount_code`
        를 ``""`` 로 두고 보내면
        서버가 ``ERR930202``("변경항목이 없습니다")로 답합니다 — 바꾼 게 없으니
        맞는 답이고, 요청이 읽히고 해석됐다는 뜻이라 폼의 모양 자체도 유효합니다.

        **성공 본문 파싱 경로도 이제 검증됐습니다.** 같은 날 평범한 회원 세션이
        ``hidDcntKndCd='131'``(경로)을 1인 홀드에 보내자(줄의 앞 세 값은 그 PNR 의
        좌석에서 복사: ``psg_tp_dv_cd='1'``, ``psrm_cl_cd='1'``,
        ``dcnt_knd_cd1='000'``) 서버가 ``SUCC``/``IRZ000008``("정상적으로 처리
        되었습니다")와 함께 ``h_tot_prc``·``h_tot_fare``·``h_tot_dcnt_amt``·
        ``h_tot_rcvd_amt``·``jrny_infos`` 를 갖춘 온전한 ``ReservationOut`` 본문을
        돌려줬고, :func:`parse_reservation_hold_response` 가 폴백 없이 그대로
        파싱했습니다(``window_no`` 등 12 개 스칼라가 모두 살아 있었고, 여정 행에는
        홀드 응답에 없던 ``h_arv_dt``·``h_jrny_sqno`` 까지 들어 있었습니다).
        서로 다른 열차 셋(서울→부산 KTX 013·1005, 서울→대전 KTX 207)에서
        재현했고, 이후 그 PNR 의 좌석은 ``h_dcnt_knd_cd1='204'`` /
        ``h_dcnt_knd_cd_nm1='경로 할인'`` 으로 읽혔습니다. 이전 판은 "할인이 실제로
        바뀌는 성공 응답은 아직 못 봤다", "성공 본문 파싱 경로는 여전히 미검증",
        "이 계정에 없는 자격이 필요하다" 셋을 적어 뒀는데 셋 다 틀렸습니다 —
        ``131`` 은 아무 자격도 없는 계정에서 동작합니다. 되돌리지 마십시오.

        같은 PNR 에 두 번째 재계산을 거는 경우는 직관과 반대입니다. 서버가 써 넣은
        값(``204``)을 다시 읽어 ``discount_kind_code`` 로 보내면
        ``WRE800036``("동일한 할인종류가 입력되었습니다…중복 입력은 불가합니다")로
        **거절**되고, 오히려 낡은 ``000`` 을 그대로 다시 보내는 쪽이
        ``SUCC``/``IRZ000008`` 로 통과합니다. 즉 이 필드는 "지금 좌석에 붙어 있는
        할인" 이 아니라 "요청 당시 베껴 온 원래 값" 으로 두십시오.

        끝으로 금액 주의: ``204`` 가 기록돼도 돈이 늘 움직이지는 않습니다. 토요일
        두 편에서는 코드만 기록되고 정산액이 그대로였는데, ``WRR664296``
        ("KTX/새마을호/ITX-청춘 열차의 경로 및 장애인(4-6급)할인은 토/일/공휴일에는
        적용되지 않습니다")이 그 이유입니다. 평일에는 같은 할인이 실제로 깎입니다
        (28,600 → 20,000, ``h_tot_dcnt_amt='000008600'``).
        """
        self._require_session("price recalculation requires")
        route = "/classes/com.korail.mobile.certification.PriceReCalculation"
        form = build_price_recalculation_form(self.config, request)
        # Strict parsing, not the reserve methods' PNR-keeping fallback: a
        # recalculation creates no hold, and the caller already has the PNR it
        # asked about, so there is no hold to orphan and nothing for a fallback
        # to rescue -- it would only hide a parse failure. This used to be
        # justified by the path "never having been sent live"; that is no
        # longer true (2026-09-22 SUCC/IRZ000008 on two trains, parsed here
        # without incident), and the justification above is the durable one.
        return self._mutation(
            "price_recalculation",
            route,
            form,
            parser=parse_reservation_hold_response,
        )

