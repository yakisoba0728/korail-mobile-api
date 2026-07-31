""":class:`KorailClient` — 이 패키지에 하나뿐인 진입점.

여기에는 클래스가 하나뿐입니다. 라우트를 고르고, 폼을 만들고, 응답을 파싱하는 일은
전부 :mod:`korail_mobile_api.read_payloads`,
:mod:`korail_mobile_api.mutation_payloads`,
:mod:`korail_mobile_api.read_parsers` 에 있고 이 모듈은 그것들을 순서대로 엮어
메서드 하나로 만듭니다.

공개 메서드는 두 종류뿐입니다. 로그인·읽기 메서드는 인자만 받고, 상태를 바꾸는
메서드는 키워드 전용 ``consent`` 를 함께 요구합니다. 후자는 예외 없이
:func:`~korail_mobile_api.consent.require_mutation_consent` 로 시작하므로, 폼을
만들기도 전에 거절됩니다. 어떤 범주가 어떤 라우트를 소유하는지는
:mod:`korail_mobile_api.safety` 가 정하고 전송 직전에 다시 검사합니다.
"""

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

import httpx

from .config import KorailConfig
from .consent import (
    MutationCategory,
    MutationConsent,
    MutationPreview,
    require_mutation_consent,
)
from .constants import KorailReservationJobType, KorailSeatClass
from .crypto import generate_sid
from .errors import (
    KorailAuthError,
    KorailMutationNotAllowedError,
    KorailNoDirectTrainError,
    KorailProtocolError,
    KorailSessionExpiredError,
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
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from .mutation_parsers import (
    parse_discount_card_purchase_response,
    parse_reservation_hold_response,
    parse_reservation_payment_response,
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
    build_transfer_reservation_form,
    build_unpaid_reservation_cancel_form,
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
    GiftTicketListResponse,
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
    PlatformNumberResponse,
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
    parse_gift_ticket_list_response,
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
    parse_platform_number_response,
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
    parse_ticket_receipt_response,
    parse_ticket_reservation_detail_response,
    parse_trip_change_date_response,
    parse_trip_menu_response,
)
from .read_payloads import (
    CommuterInfoRequest,
    DiscountCardScheduleRequest,
    FreeSeatCarRequest,
    GiftTicketHistoryRequest,
    GiftTicketPaymentEligibilityRequest,
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
    build_gift_ticket_list_form,
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
    build_platform_number_form,
    build_price_fare_quote_form,
    build_product_detail_query,
    build_product_reservations_query,
    build_recent_delivery_history_form,
    build_refund_commission_form,
    build_refund_ticket_detail_form,
    build_seat_assignment_schedule_form,
    build_self_seat_change_info_form,
    build_service_status_query,
    build_ticket_duplication_check_form,
    build_ticket_receipt_form,
    build_ticket_reservation_detail_query,
    build_trip_change_date_form,
    build_trip_menu_form,
)
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

    ``KorailClient()`` — 인자 없이 — 만들면 바로 동작합니다.
    :class:`~korail_mobile_api.config.KorailConfig` 기본값이 앱의
    ``Device``/``Version``/``Key`` 와 DynaPath 안티오토메이션을 켠 상태로 채워지기
    때문입니다. ``transport`` 는 시험용 :mod:`httpx` 전송로를 끼워 넣는 자리입니다.

    읽기 메서드는 게이트가 없습니다. 상태를 바꾸는 메서드는 모두
    :class:`~korail_mobile_api.consent.MutationConsent` 를 키워드로 요구하며, 기본
    consent 는 어느 범주도 허용하지 않아
    :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError` 로 막힙니다.
    범주를 허용해도 ``dry_run`` 이 기본 참이라 아무것도 전송하지 않고
    :class:`~korail_mobile_api.consent.MutationPreview` 가 돌아옵니다.

    자원 정리는 :meth:`close` 입니다. ``__enter__``/``__exit__`` 를 정의하지 않으므로
    ``with`` 문으로는 쓸 수 없습니다. :meth:`close` 는 커넥션 풀만 닫으니 로그인까지
    끝내려면 :meth:`logout`(서버 세션 무효화)이나 :meth:`clear_session`(로컬만 폐기)을
    따로 부르면 됩니다.

    .. code-block:: python

        from korail_mobile_api import KorailClient, TrainSearchQuery

        client = KorailClient()
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

    def clear_session(self) -> None:
        """서버에 알리지 않고 로컬 로그인 상태만 버립니다.

        쿠키 저장소(``JSESSIONID`` 포함), 현재 :class:`KorailSession`, 보류 중인 2단계
        인증 상태를 모두 비웁니다. 네트워크 호출이 없으므로 서버 쪽 세션은 스스로 만료될
        때까지 살아 있습니다. 서버 세션까지 무효화하려면 :meth:`logout` 을 쓰면 됩니다.
        """
        self.session.clear_session()

    def logout(self) -> None:
        """서버 세션을 무효화하고 로컬 로그인 상태도 버립니다.

        ``GET login.Logout``(``LoginService.java:29``). 요청에 질의값이 하나도 없고
        ``JSESSIONID`` 쿠키만으로 인증되므로 봉투를 싣지 않습니다.

        로그인 상태가 아니면 요청 자체를 보내지 않습니다. 서버 무효화는 최선노력이라
        전송이 실패하거나 세션이 이미 만료돼 있어도 예외를 올리지 않고, 로컬
        상태(:meth:`clear_session` 이 지우는 것들)는 어느 경우에나 비워집니다. HTTP
        커넥션 풀은 그대로 남으니 :meth:`close` 는 따로 부르면 됩니다.
        """
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

    # ------------------------------------------------------------------
    # Internal helpers: read pattern (post_form → parser → _run_read)
    # ------------------------------------------------------------------

    def _post_read(
        self,
        route: str,
        form: Any = None,
        *,
        parser: Callable[..., T],
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
        query: dict[str, str] | None = None,
        *,
        parser: Callable[..., T],
        include_dynapath: bool = False,
        require_envelope: bool = True,
    ) -> T:
        """GET 읽기의 공통 골격: GET → 파싱 → 세션만료 복구."""
        return self._run_read(
            lambda: parser(
                self.http.get_json(
                    route,
                    query,
                    include_dynapath=include_dynapath,
                    require_envelope=require_envelope,
                )
            )
        )

    def _mutation(
        self,
        consent: MutationConsent,
        category: MutationCategory,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        method: str = "POST",
        parser: Callable[..., T] | None = None,
        raise_on_fail: bool = True,
    ) -> MutationPreview | T:
        """상태변경 메서드의 공통 골격: dry_run 분기 → 전송 → 파싱 → 세션만료 복구."""
        if consent.dry_run:
            return MutationPreview(
                category=category,
                method=method,
                route=route,
                payload=form,
            )
        try:
            response = self.http.post_mutation_form(
                route,
                form,  # type: ignore[arg-type]
                consent=consent,
                category=category,
                raise_on_fail=raise_on_fail,
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise
        if parser is not None:
            raw = response.raw if isinstance(response.raw, dict) else {}
            return parser(raw)
        return response  # type: ignore[return-value]

    def get_seat_cars(
        self,
        train: TrainSummary,
        *,
        passenger_count: int = 1,
        room_class_code: str = "1",
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
        """한 호차의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다."""
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

    def get_limousine_schedule_view(
        self,
        query: LimousineScheduleViewQuery,
    ) -> LimousineScheduleViewResponse:
        """좌석이동 화면이 쓰는 리무진 연계 열차 목록을 조회합니다."""
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
        """예매 서비스가 열려 있는지를 서버 봉투로 확인합니다."""
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
        """로그인 계정의 장바구니에 담긴 부가상품 항목을 조회합니다."""
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
        return self._post_read(
            "/classes/com.korail.mobile.passCard.DelayDiscountView",
            build_delay_discount_ticket_form(departure_date_to),
            parser=parse_delay_discount_ticket_response,
            require_envelope=False,
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

        로그인 필요. 복지 등록 상태(장애인증·보조견)도 함께 옴 — ``MyPageActivity.java:206-212``.
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
        """할인카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회합니다."""
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
        """정기권 상품 하나의 사용 개시 가능일과 발권 가능일을 조회합니다."""
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
        """정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.pass.passScheduleInfoList",
            build_pass_schedule_form(request),
            parser=parse_pass_schedule_response,
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
        """승무원 호출 화면에 띄울 요청 사유 선택지를 조회합니다."""
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
        """정기권 종류 하나의 안내 문구와 조회 파라미터를 받아 옵니다."""
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
        """로그인 계정이 예약한 여행상품 목록 한 페이지를 조회합니다."""
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
        """여행상품 예약 한 건의 상세와 취소 조건을 조회합니다."""
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
        """승차권 한 장의 영수증과 그 결제수단 내역을 조회합니다."""
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
        """로그인 계정에 아직 살아 있는 예약(미결제 홀드 포함)을 조회합니다."""
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
        """좌석속성 코드 하나에 대한 안내를 서버 봉투로 받습니다."""
        return self._post_read(
            "/classes/com.korail.mobile.reservation.guideSeatCnd.do",
            build_guide_seat_condition_form(request),
            parser=parse_guide_seat_condition_response,
        )

    def get_seat_assignment_schedule(
        self,
        request: SeatAssignmentScheduleRequest,
    ) -> SeatAssignmentScheduleResponse:
        """좌석배정 예매 화면이 쓰는 열차 목록을 조회합니다."""
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
        self._require_session()
        session = self.session.current
        customer_no = session.customer_no if session is not None else None
        if not isinstance(customer_no, str) or not customer_no.strip():
            raise KorailAuthError(
                "KORAIL customer trip read requires a login customer number"
            )
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
        return self._post_read(
            "/classes/com.korail.mobile.reservation.tripChgDate.do",
            build_trip_change_date_form(departure_date),
            parser=parse_trip_change_date_response,
        )

    def get_gift_ticket_list(
        self,
        request: GiftTicketHistoryRequest
        | GiftTicketPaymentEligibilityRequest,
    ) -> GiftTicketListResponse:
        """기프티켓 목록을 두 가지 조회 목적 중 하나로 읽습니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.gift.gdLst.do",
            build_gift_ticket_list_form(request),
            parser=parse_gift_ticket_list_response,
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
        """승차권 한 장을 전달받은 수령자 정보를 조회합니다."""
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

    def get_platform_numbers(
        self,
        tickets: tuple[OriginalTicketReference, ...],
    ) -> PlatformNumberResponse:
        """승차권 여러 장의 승강장 번호를 여정 단위로 조회합니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.tk.plfNo.do",
            build_platform_number_form(tickets),
            parser=parse_platform_number_response,
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
        return self._run_read(
            lambda: parse_original_ticket_inquiry_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.research.tripChgOgtk.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
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
        self._require_session()
        session = self.session.current
        customer_no = session.customer_no if session is not None else None
        if not isinstance(customer_no, str) or not customer_no.strip():
            raise KorailAuthError(
                "KORAIL delivery history read requires a login customer number"
            )
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
        """환불했을 때 돌려받을 금액과 떼일 수수료를 미리 묻습니다."""
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
    ) -> RefundTicketDetailResponse:
        """환불 대상 승차권의 여정·좌석·운임 상세를 조회합니다."""
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
        """공통코드 표를 코드 하나만큼 조회합니다."""
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
        """공지 배너 캐시 파일을 받아 옵니다."""
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
        """서버가 발급하는 단말 검증값 하나를 받아 옵니다."""
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
        """역 연계 MaaS 서비스 메뉴와 역 안내 링크들을 조회합니다."""
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

    def get_station_info(self, device: str = "AD") -> StationInfoResponse:
        """역 데이터의 판본과 수록 역 수만 가볍게 확인합니다."""
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
        """전체 역 목록을 코드·이름·좌표까지 한 번에 받아 옵니다."""
        return self._run_read(
            lambda: parse_station_data_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.common.stationdata",
                    require_envelope=False,
                )
            )
        )

    def get_train_calendar(self) -> TrainCalendarResponse:
        """지금 예매할 수 있는 운행일 달력을 받아 옵니다."""
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
        """한 구간·한 날짜의 직통 열차 한 페이지를 조회합니다."""
        return self._run_read(
            lambda: self._search_trains(query, continuation)
        )

    def search_transfer_trains(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
    ) -> TransferSearchResult:
        """같은 질의를 환승 여정으로 바꿔 한 페이지 조회합니다."""
        return self._run_read(
            lambda: self._search_transfer_trains(query, continuation)
        )

    def search_trains_with_transfer_fallback(
        self,
        query: TrainSearchQuery,
        *,
        continuation: TrainSearchContinuation | None = None,
    ) -> TrainSearchResult | TransferSearchResult:
        """직통을 찾고, 하나도 없을 때만 환승으로 한 번 더 찾습니다.

        지어낸 편의기능이 아니라 앱의 흐름 그대로입니다. 직통 조회가 아무것도 못 찾으면
        서버가 ``WRD000061``("직통열차가 없습니다")로 답하는데,
        ``DirectInquiryActivity.java:615-624`` 는 오직 그 코드만 잡아 확인 창을 띄우고, 확인을
        누르면 ``:284-296`` 이 ``radJobId="2"`` 로 다시 질의합니다. 이 클라이언트도
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
        mode: str = "1",
        boarding_date_from: str = "",
        boarding_date_to: str = "",
    ) -> BaseKorailResponse:
        """로그인 계정의 승차권 목록을 파싱하지 않은 봉투로 돌려줍니다.

        ``POST myTicket.MyTicketList``(``MyTicketService.java:16``). 로그인 필요.

        전용 파싱 모델이 없습니다. :class:`~korail_mobile_api.models.BaseKorailResponse` 를
        그대로 돌려주므로 승차권 행은 ``raw`` 에서 직접 꺼냅니다.

        ``mode`` 는 페이지 커서가 아니라 목록 종류입니다 — ``"1"`` 은 현재
        승차권(``TicketListActivity.java:937-939``), ``"2"`` 는
        구매이력(``TicketPurchaseHistoryActivity.java:276-278``)이고 그 밖의 값은 거부됩니다.
        ``"2"`` 는 ``boarding_date_from``·``boarding_date_to`` 를 둘 다 ``YYYYMMDD`` 로
        요구하며 한쪽이라도 비면 요청을 만들기 전에 막습니다. ``"1"`` 은 두 값을 빈 문자열로
        보냅니다.

        ``page_no`` 는 ``h_page_no`` 로 나가고 1 미만은 1 로 올려 보내므로 기본값 ``0`` 도 첫
        페이지를 뜻합니다.
        """
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
        """열차 한 편에 결제 전 예약을 잡습니다. consent 게이트가 있습니다.

        ``require_mutation_consent(consent, "reserve")`` 와 로그인 세션을 요구합니다.

        ``consent.dry_run`` 이 참이면(기본) ``train`` 을 검증하고 실제로 나갈 폼을 담은

        열차에만 붙습니다. 회원 전용입니다(``ReservationRequest.java:105-119``) — 이
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
        """예약대기 홀드에 대기 옵션을 기록합니다. consent 게이트가 있습니다.

        예약대기 화면을 엽니다(``ui/inquiry/rir/orr/a.java:222-225``). 그 화면이

        ``reservationWait.ReservationWait``(``ReservationWaitService.java:10-12``).

        ``require_mutation_consent(consent, "reserve")`` 와 로그인 세션을 요구하고,
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
        return self._mutation(consent, "reserve", route, form)

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
        """환승 여정 하나를 두 구간·한 PNR 로 홀드합니다. consent 게이트가 있습니다.

        (``C5/a.java:52-119``). consent·``dry_run``·돌려주는 홀드에 대해

        만들기 전에 거절합니다(:data:`~korail_mobile_api.KORAIL_MAX_JOURNEY_LEGS`).

        선택이 구간별입니다(``C5/a.java:59``, ``:97``). ``seats`` 도 마찬가지로
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
        """한 열차를 중간역에서 나눈 병합예약을 홀드합니다. consent 게이트가 있습니다.

        :data:`~korail_mobile_api.constants.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE`

        취소하지만(``DirectInquiryActivity.java:227-250``), 여기서는 ``"cancel"``

        전송된 적이 없습니다. 여기서 만든 병합 폼이 KORAIL 에 나간 적은 없습니다.
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
        """결제 전 예약 홀드를 취소합니다. 여정이 몇 개든 상관없습니다.

        ``require_mutation_consent(consent, "cancel")`` 와 로그인 세션을 요구합니다.

        ``consent.dry_run`` 이 참이면 PNR 을 가린 :class:`MutationPreview` 를, 거짓이면

        ``ReservationCancel`` 을 생략해도 취소가 성립하는 것은 라이브로 확인했습니다.
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
        return self._mutation(consent, "cancel", route, form)

    def pay_with_fake_card(
        self,
        hold: ReservationHoldResponse,
        card: CardPayment,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationPaymentResponse:
        """미결제 홀드를 비과금 시험카드로 결제 시도합니다. consent 게이트가 있습니다.

        ``require_mutation_consent(consent, "payment")`` 와 로그인 세션에 더해

        ``consent.dry_run`` 이 참이면 카드·신원 필드를 가린 :class:`MutationPreview` 를
        """
        require_mutation_consent(consent, "payment")
        if not consent.fake_card_only:
            raise KorailMutationNotAllowedError(
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
        """미결제 홀드를 실제 청구되는 카드로 결제합니다. consent 게이트가 있습니다.

        ``require_mutation_consent(consent, "payment")`` 와 로그인 세션에 더해

        :meth:`~korail_mobile_api.http.KorailHttpClient.post_mutation_form` 으로

        ``consent.dry_run`` 이 참이면 카드·신원을 가린 :class:`MutationPreview` 만
        """
        require_mutation_consent(consent, "payment")
        if not consent.real_card_acknowledged:
            raise KorailMutationNotAllowedError(
                "pay_with_card requires consent.real_card_acknowledged=True; a "
                "real, chargeable card number is transmitted in the clear and "
                "money actually moves, so the caller must say so explicitly "
                "(use pay_with_fake_card for a non-chargeable test card)"
            )
        if consent.fake_card_only:
            raise KorailMutationNotAllowedError(
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
        """결제까지 끝난 승차권을 환불합니다. consent 게이트가 있습니다.

        ``POST refunds.RefundsRequest``. ``require_mutation_consent(consent,

        반환비밀번호)이어야 합니다. ``consent.dry_run`` 이 참이면 승차권 신원을 가린
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
        return self._mutation(consent, "refund", route, form)

    def add_to_cart(
        self,
        request: CartAddRequest,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """홀드 중인 예약의 PNR 을 장바구니에 담습니다. consent 게이트가 있습니다.

        ``POST cart.addCartList``(``CartService.java:11-13``). 공통 세 필드 말고 요청

        필드는 ``hidPnrNo`` 하나뿐입니다(``AddCartDao.java:9-24``, smali 로 교차 확인).

        ``require_mutation_consent(consent, "cart")`` 와 로그인 세션을 요구합니다.
        """
        require_mutation_consent(consent, "cart")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL cart add requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.cart.addCartList"
        form = build_cart_add_form(self.config, request)
        return self._mutation(consent, "cart", route, form)

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | DiscountCardPurchaseResponse:
        """할인카드(N카드)를 구매합니다. consent 게이트가 있습니다.

        ``POST research.dcntCrdInfo.do``(``ResearchService.java:68-70``). 경로에

        ``rcvdAmt`` 를 주고(``NCardReservationDao.java:127-134``) 앱은 그 대상번호를

        결제 화면으로 그대로 넘깁니다(``SectionNCardInquiryActivity.java:213-257``).
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
        """할인카드의 유효기간을 연장합니다(기간연장). consent 게이트가 있습니다.

        ``GET reservation.dcntCrdExtn.do``(``ResearchService.java:65-66``) — 앱이 GET

        ``post_mutation_form`` 과 같은 게이트를 모두 갖춘

        나갑니다. ``require_mutation_consent(consent, "discount_card")`` 와 로그인
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
        """할인카드(N카드)로 좌석 하나를 홀드합니다. consent 게이트가 있습니다.

        ``w4/a.java:93-104`` 이 평범한 ``ReservationRequest`` 를 만들고

        ``c5/b.java:128-138`` 이 평범한 ``ReservationDao`` 로

        ``require_mutation_consent(consent, "reserve")`` 입니다 — 할인카드를 쓴다고
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
        """홀드된 PNR 의 운임을 다른 할인 조합으로 다시 계산합니다. consent 게이트가 있습니다.

        ``POST certification.PriceReCalculation``(``CertificationService.java:35-37``,

        화면에서 이것을 쏘고(``a6/C1042B.java:265-296``), 응답은 홀드가 돌려주는 것과

        ``require_mutation_consent(consent, "price_recalculation")`` 와 로그인 세션을
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

