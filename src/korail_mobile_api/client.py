# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

""":class:`KorailClient` — 이 패키지에 하나뿐인 진입점.

여기에는 클래스가 하나뿐입니다. 라우트를 고르고, 폼을 만들고, 응답을 파싱하는 일은
전부 :mod:`korail_mobile_api.read_payloads`,
:mod:`korail_mobile_api.mutation_payloads`,
:mod:`korail_mobile_api.read_parsers` 에 있고 이 모듈은 그것들을 순서대로 엮어
메서드 하나로 만듭니다.

공개 메서드는 두 종류뿐입니다. 로그인·읽기 메서드는 인자만 받고, 상태를 바꾸는
메서드는 키워드 전용 ``consent`` 를 함께 요구합니다. 후자는
:func:`~korail_mobile_api.consent.require_mutation_consent` 로 시작하므로, 폼을
만들기도 전에 거절됩니다. 어떤 범주가 어떤 라우트를 소유하는지는
:mod:`korail_mobile_api.safety` 가 정하고 전송 직전에 다시 검사합니다.

예외가 하나 있습니다. 7.0.6 계약으로 나가는 :meth:`KorailClient.execute_station_ticket_refund`
는 범주가 아니라 메서드 이름을 여는 :class:`~korail_mobile_api.v7.V7MutationConsent` 를
받습니다. 같은 동의 체계가 ``client.v7`` 게이트웨이의 7.0.6 계약 전부에 쓰입니다.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal, TypeVar, overload

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
from .session import KorailSessionClient
from .v7 import V7Gateway, V7MutationConsent, V7MutationPreview


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

    읽기 메서드는 게이트가 없습니다. 상태를 바꾸는 메서드는
    :class:`~korail_mobile_api.consent.MutationConsent` 를 키워드로 요구하며, 기본
    consent 는 어느 범주도 허용하지 않아
    :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError` 로 막힙니다.
    범주를 허용해도 ``dry_run`` 이 기본 참이라 아무것도 전송하지 않고
    :class:`~korail_mobile_api.consent.MutationPreview` 가 돌아옵니다. 7.0.6 계약으로
    나가는 :meth:`execute_station_ticket_refund` 만 메서드 단위
    :class:`~korail_mobile_api.v7.V7MutationConsent` 를 받습니다.

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
        partner_origins: Mapping[str, str] | None = None,
        partner_transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        try:
            self.v7 = V7Gateway(
                self.http,
                partner_origins=partner_origins,
                partner_transport=partner_transport,
            )
        except Exception:
            self.http.close()
            raise
        self.session = KorailSessionClient(self.http)
        self._station_names: dict[str, str] | None = None

    def close(self) -> None:
        """HTTP 커넥션 풀을 닫습니다. 로그인 상태는 건드리지 않습니다.

        :meth:`~korail_mobile_api.http.KorailHttpClient.close` 로 위임하며 네트워크
        호출을 하지 않습니다. 로그인까지 끝내려면 먼저 :meth:`logout`(서버 세션 무효화)
        이나 :meth:`clear_session`(로컬만 폐기)을 부르면 됩니다.
        """
        self.v7.close()
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
        try:
            return operation()
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def _require_session(self, what: str = "account read requires") -> None:
        """No session, no request: ``KORAIL <what> an authenticated session``."""
        if self.session.current is None:
            raise KorailAuthError(f"KORAIL {what} an authenticated session")

    # ------------------------------------------------------------------
    # Internal helpers: the read skeleton (post → parser → _run_read) and the
    # mutation skeleton (_mutation: dry-run branch → send → parse)
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

    @overload
    def _mutation(
        self,
        consent: MutationConsent,
        category: MutationCategory,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        method: str = ...,
        parser: None = ...,
        raise_on_fail: bool = ...,
    ) -> MutationPreview | BaseKorailResponse: ...

    @overload
    def _mutation(
        self,
        consent: MutationConsent,
        category: MutationCategory,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        method: str = ...,
        parser: Callable[[dict[str, Any]], T],
        raise_on_fail: bool = ...,
    ) -> MutationPreview | T: ...

    def _mutation(
        self,
        consent: MutationConsent,
        category: MutationCategory,
        route: str,
        form: dict[str, str] | dict[str, str | list[str]],
        *,
        method: str = "POST",
        parser: Callable[[dict[str, Any]], T] | None = None,
        raise_on_fail: bool = True,
    ) -> MutationPreview | BaseKorailResponse | T:
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
                form,
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

    def get_service_status(
        self,
        timestamp_ms: int | None = None,
    ) -> ServiceStatusResponse:
        """예매 서비스가 열려 있는지를 서버 봉투로 확인합니다."""
        query = build_service_status_query(timestamp_ms)
        return self._run_read(
            lambda: parse_service_status_response(
                self.http.post_form(
                    "/file/CACHE/MobileService.cache",
                    query,
                    include_common=False,
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
                self.http.post_form(
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
                self.http.post_form(
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
                self.http.post_form(
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
        reservation_sequence: str | None = None,
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
                self.http.post_form(
                    "/classes/com.korail.mobile.reservation.ReservationView",
                    {"timeStamp": 0},
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
        """좌석 안내 봉투를 받습니다. ``MRR800011`` 문구도 반환합니다."""
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
        return self._run_read(
            lambda: parse_trip_change_date_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.reservation.tripChgDate.do",
                    build_trip_change_date_form(departure_date),
                    include_common=True,
                    include_dynapath=False,
                ).raw
            )
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
                self.http.post_form(
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
        요구하며 한쪽이라도 비면 요청을 만들기 전에 막습니다. ``"1"`` 은 두 값을 빈 문자열로
        보냅니다.

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
        consent: MutationConsent,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
        job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
        seats: Sequence[KorailSeatAssignment] | None = None,
        seat_attribute_code: str | None = None,
    ) -> MutationPreview | ReservationHoldResponse:
        """열차 한 편에 결제 전 예약을 잡습니다. consent 게이트가 있습니다.

        ``require_mutation_consent(consent, "reserve")`` 와 로그인 세션을 요구합니다.

        ``consent.dry_run`` 이 참이면(기본) ``train`` 을 검증하고 실제로 나갈 폼을 담은
        :class:`MutationPreview` 를 돌려줄 뿐 네트워크를 건드리지 않습니다. 거짓이면
        이중 게이트 전송로로 홀드를 걸고 파싱한 :class:`ReservationHoldResponse` 를
        돌려줍니다. 그 ``pnr_no`` 가 :meth:`cancel_unpaid_hold` 의 입력입니다 — 살아
        있는 홀드는 미결제 예약이고 취소하든 결제하든 호출자 책임입니다.

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
        require_mutation_consent(consent, "reserve")
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
            consent,
            "reserve",
            route,
            form,
            parser=self._hold_from_reservation_response,
        )

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

        예약대기는 호출 두 번입니다. ``job_type=STANDBY`` 로 부른 :meth:`reserve` 가
        PNR 을 만들고 ``h_msg_cd`` = ``IRR000014`` 를 돌려주는데, 앱은 이 코드에서만
        예약대기 화면을 엽니다(``ui/inquiry/rir/orr/a.java:222-225``). 그 화면이
        사용자의 선택을 실어 보내는 두 번째 POST 가 이 메서드입니다 —
        ``reservationWait.ReservationWait``(``ReservationWaitService.java:10-12``).

        ``require_mutation_consent(consent, "reserve")`` 와 로그인 세션을 요구하고,
        다른 모든 상태 변경과 같은 이중 게이트 전송로로 나갑니다. 이미 있는 PNR 의
        예약을 마무리할 뿐 돈을 옮기지도 좌석을 놓지도 않으므로 소비 범주가
        ``"reserve"`` 입니다.
        """
        require_mutation_consent(consent, "reserve")
        self._require_session("standby options require")
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
        seat_attribute_codes: Sequence[str | None] | None = None,
    ) -> MutationPreview | ReservationHoldResponse:
        """환승 여정 하나를 두 구간·한 PNR 로 홀드합니다. consent 게이트가 있습니다.

        라우트도 consent 범주도 세션 요구도 :meth:`reserve` 와 같습니다. 앱도
        엔드포인트와 요청 빌더를 하나만 쓰고 구간 수만 폼을 바꿉니다
        (``C5/a.java:52-119``). consent·``dry_run``·돌려주는 홀드에 대해
        :meth:`reserve` 가 말한 것이 그대로 적용됩니다.

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
        require_mutation_consent(consent, "reserve")
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
            consent,
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
        consent: MutationConsent,
        passengers: KorailPassengerCounts | None = None,
        seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
        seat_attribute_code: str | None = None,
    ) -> MutationPreview | ReservationHoldResponse:
        """한 열차를 중간역에서 나눈 병합예약을 홀드합니다. consent 게이트가 있습니다.

        병합 흐름의 두 번째이자 마지막 홀드입니다. 첫 번째는
        ``job_type=KorailReservationJobType.MERGE_STANDING``(``"1202"``, 입석+좌석
        예매)으로 부르는 :meth:`reserve` 이고 그것이 전 구간을 입석으로 잡습니다. 이
        메서드가 그것을 같은 열차의 두 여정 예약으로 바꾸는데, 나누는 지점은
        :meth:`get_merge_seats_inquiry` 가 알려준 중간역입니다. 다섯 단계 전체와 그
        근거는
        :data:`~korail_mobile_api.constants.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE`
        에 적혀 있습니다.

        입석 홀드를 대신 취소하지는 않습니다. 앱은 다시 예약하기 전에 그것을
        취소하지만(``DirectInquiryActivity.java:227-250``), 여기서는 ``"cancel"``
        consent 아래의 :meth:`cancel_unpaid_hold` 로 호출자가 직접 합니다 —
        ``"reserve"`` 동의만 받고 살아 있는 PNR 을 조용히 취소하는 것은 이 게이트들이
        막으려는 범주 혼동 그 자체입니다.

        전송된 적이 없습니다. 여기서 만든 병합 폼이 KORAIL 에 나간 적은 없습니다.
        """
        require_mutation_consent(consent, "reserve")
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
            consent,
            "reserve",
            route,
            form,
            parser=self._hold_from_reservation_response,
        )

    def cancel_unpaid_hold(
        self,
        hold: ReservationHoldResponse,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """결제 전 예약 홀드를 취소합니다. 여정이 몇 개든 상관없습니다.

        ``require_mutation_consent(consent, "cancel")`` 와 로그인 세션을 요구합니다.

        ``consent.dry_run`` 이 참이면 PNR 을 가린 :class:`MutationPreview` 를, 거짓이면
        이중 게이트 전송로로 POST 한 뒤 파싱한 봉투를 돌려줍니다.

        앱의 취소 호출 두 개 중 뒤쪽(``ReservationCancelChk``)만 보냅니다. 앞의
        ``ReservationCancel`` 을 생략해도 취소가 성립하는 것은 라이브로 확인했습니다 —
        2026-07-31 직통 홀드가 ``IRG000000`` 으로 풀렸고, 두 여정짜리 환승 홀드는
        2026-07-26 과 2026-07-31 에 PNR 하나로 함께 풀렸습니다.
        """
        require_mutation_consent(consent, "cancel")
        self._require_session("cancellation requires")
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
        ``consent.fake_card_only`` 가 참이어야 합니다. KORAIL 결제 호출은 카드번호를
        평문으로 싣기 때문에, ``card`` 는 PG 가 거절할 비과금 시험카드여야 합니다.

        ``consent.dry_run`` 이 참이면 카드·신원 필드를 가린 :class:`MutationPreview` 를
        돌려주고 아무것도 보내지 않습니다. 거짓이면 이중 게이트 전송로로 POST 하고
        파싱한 :class:`ReservationPaymentResponse` 를 돌려줍니다.
        """
        require_mutation_consent(consent, "payment")
        if not consent.fake_card_only:
            raise KorailMutationNotAllowedError(
                "pay_with_fake_card requires consent.fake_card_only=True; only "
                "non-chargeable test cards are supported"
            )
        self._require_session("payment requires")
        route = "/classes/com.korail.mobile.payment.ReservationPayment"
        form = build_card_payment_form(self.config, hold, card)
        # raise_on_fail=False: a declined card is an answer to read, not an
        # error to raise.
        return self._mutation(
            consent,
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
        *,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationPaymentResponse:
        """미결제 홀드를 실제 청구되는 카드로 결제합니다. consent 게이트가 있습니다.

        ``require_mutation_consent(consent, "payment")`` 와 로그인 세션에 더해
        ``consent.real_card_acknowledged`` 가 참이고 ``consent.fake_card_only`` 가
        거짓이어야 합니다. 두 조건을 모두 적어야 합니다 — 실제 청구를 인정하면서
        시험카드라고 주장하는 consent 는 모순이라 여기서도, 전송 게이트에서도
        거절합니다. 기본 :class:`MutationConsent` 는 어느 쪽도 만족하지 않습니다.

        전선 모양은 :meth:`pay_with_fake_card` 와 같습니다. 둘 다 같은
        ``build_card_payment_form`` 을 만들고 같은 이중 게이트
        :meth:`~korail_mobile_api.http.KorailHttpClient.post_mutation_form` 으로
        나가므로, 실제 결제가 라이브로 검증된 모양에서 벗어날 수 없습니다. 다른 것은
        어느 consent 를 받느냐뿐입니다.

        ``consent.dry_run`` 이 참이면 카드·신원을 가린 :class:`MutationPreview` 만
        돌려주고 아무것도 전송하지 않습니다.

        실제 돈으로 확인했습니다. 2026-07-31 에 8,400원 한 장이 ``IRT000000`` 으로
        결제·발권됐고 같은 날 2인 PNR 도 결제했으며, 2026-09-15 에 7.0.6 판으로 다시
        결제·전액 환불했습니다(``docs/verification-record.md``,
        ``docs/7.0.6-live-verification.md``).
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
        self._require_session("payment requires")
        route = "/classes/com.korail.mobile.payment.ReservationPayment"
        form = build_card_payment_form(self.config, hold, card)
        # raise_on_fail=False: a declined card is an answer to read, not an
        # error to raise.
        return self._mutation(
            consent,
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
        consent: MutationConsent,
        return_times_division_code: str | None = None,
        settle_mileage: bool = False,
        pbp_acceptance_target_flag: str | None = None,
    ) -> MutationPreview | RefundTicketResponse:
        """결제까지 끝난 승차권 **한 장** 을 환불합니다. consent 게이트가 있습니다.

        ``POST refunds.RefundsRequest``. ``require_mutation_consent(consent,
        "refund")`` 와 로그인 세션을 요구합니다. ``ticket`` 은
        :class:`~korail_mobile_api.mutation_models.PaidTicket`(PNR + 원발매 자격증명 +
        반환비밀번호)이어야 합니다. ``consent.dry_run`` 이 참이면 승차권 신원을 가린
        :class:`MutationPreview` 를, 거짓이면 이중 게이트 전송로로 POST 한 뒤 파싱한
        :class:`RefundTicketResponse` 를 돌려줍니다.

        **PNR 단위가 아니라 승차권 단위입니다.** ``ticket`` 이 PNR 을 싣기는 하지만
        서버가 되돌리는 것은 ``sale_sequence`` 로 지목된 그 한 장뿐입니다. 승객 2명을
        한 PNR 로 예약하면 승차권이 2장 생기고, 이 메서드를 한 번 부르면 한 장만
        반환됩니다 — 나머지는 결제된 상태로 계정에 남고, 예약 목록은 비어 있어서
        (반환된 것은 예약이 아니라 승차권이므로) 다 끝난 것처럼 보입니다.
        **여러 장이면 장마다 한 번씩 부르십시오.** 남은 장의 신원은
        :meth:`get_ticket_list` 응답에서 ``h_orgtk_wct_no``·``h_orgtk_ret_sale_dt``·
        ``h_orgtk_sale_sqno``·``h_orgtk_ret_pwd`` 로 읽습니다.

        2026-07-31 실서버 확인: 성인 2명 16,800원(8,400×2)을 한 PNR 로 결제한 뒤
        이 메서드를 한 번 부르니
        ``SUCC``/``IRT200277`` 과 함께 8,400원만 돌아왔고, 좌석 032 한 장이
        ``h_rcvd_amt="00000008400"`` 으로 남았습니다. 같은 방식으로 한 번 더 부르니
        비었습니다. 부분 환불을 노린 API 가 아니라, 이것이 이 라우트의 단위입니다.
        """
        require_mutation_consent(consent, "refund")
        self._require_session("refund requires")
        route = "/classes/com.korail.mobile.refunds.RefundsRequest"
        form = build_refund_form(
            self.config,
            ticket,
            return_times_division_code=return_times_division_code,
            settle_mileage=settle_mileage,
            pbp_acceptance_target_flag=pbp_acceptance_target_flag,
        )
        return self._mutation(
            consent, "refund", route, form, parser=parse_refund_ticket_response
        )

    def verify_station_ticket_refund(
        self,
        request: StationRefundVerificationRequest,
    ) -> StationRefundVerificationResponse:
        """Verify an existing station-issued ticket before online refund."""
        self._require_session("station ticket refund verification requires")
        fields = build_station_refund_verification_form(request)
        def run() -> StationRefundVerificationResponse:
            result = self.v7.call(
                "NetworkApi.verifyOnlineRefunds", fields, include_common=True
            )
            if isinstance(result, V7MutationPreview):
                raise KorailProtocolError(
                    "KORAIL station refund verification returned a mutation preview"
                )
            return parse_station_refund_verification_response(result.raw)
        return self._run_read(run)

    def execute_station_ticket_refund(
        self,
        request: StationRefundExecutionRequest,
        *,
        consent: V7MutationConsent,
    ) -> V7MutationPreview | StationRefundExecutionResponse:
        """Execute a verified station-ticket refund with method-scoped consent."""
        self._require_session("station ticket refund requires")
        fields = build_station_refund_execution_form(self.config, request)
        # The same P058 handling as _mutation, which this call cannot use: it
        # goes through the 7.0.6 gateway and its method-scoped consent.
        try:
            result = self.v7.call(
                "NetworkApi.executeOnlineRefunds", fields, consent=consent
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise
        if isinstance(result, V7MutationPreview):
            return result
        return parse_station_refund_execution_response(result.raw)

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
        self._require_session("cart add requires")
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
        "Info" 가 붙어 있지만 조회가 아니라 구매입니다 — 응답이 ``lumpStlTgtNo`` 와
        ``rcvdAmt`` 를 주고(``NCardReservationDao.java:127-134``) 앱은 그 대상번호를
        결제 화면으로 그대로 넘깁니다(``SectionNCardInquiryActivity.java:213-257``).
        만들어지는 것은 결제를 기다리는 미결제 구매입니다.
        """
        require_mutation_consent(consent, "discount_card")
        self._require_session("discount card purchase requires")
        route = "/classes/com.korail.mobile.research.dcntCrdInfo.do"
        form = build_discount_card_purchase_form(self.config, request)
        return self._mutation(
            consent,
            "discount_card",
            route,
            form,
            parser=parse_discount_card_purchase_response,
        )

    def extend_discount_card(
        self,
        ticket: DiscountCardTicket,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """할인카드의 유효기간을 연장합니다(기간연장). consent 게이트가 있습니다.

        ``POST reservation.dcntCrdExtn.do`` (7.0.6 ``NetworkApi``).

        ``post_mutation_form`` 게이트로 전송합니다. 변경 동의와 로그인 상태를
        요구하며 dry-run에서는 전송 대신 preview를 돌려줍니다.
        """
        require_mutation_consent(consent, "discount_card")
        self._require_session("discount card extension requires")
        route = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"
        query = build_discount_card_extension_query(self.config, ticket)
        return self._mutation(consent, "discount_card", route, query)

    def reserve_with_discount_card(
        self,
        train: TrainSummary,
        *,
        card_no: str,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationHoldResponse:
        """할인카드(N카드)로 좌석 하나를 홀드합니다. consent 게이트가 있습니다.

        라우트도 범주도 게이트도 :meth:`reserve` 와 같습니다. 같은 호출이기 때문입니다 —
        ``w4/a.java:93-104`` 이 평범한 ``ReservationRequest`` 를 만들고
        ``c5/b.java:128-138`` 이 평범한 ``ReservationDao`` 로
        ``certification.TicketReservation`` 에 보냅니다. N카드 전용 예약 엔드포인트는
        없고 N카드 승객 블록이 있을 뿐입니다. 그래서
        ``require_mutation_consent(consent, "reserve")`` 입니다 — 할인카드를 쓴다고
        예약이 예약 아닌 것이 되지 않고, 좌석 홀드에 동의하지 않은 호출자가 이 길로
        홀드해서도 안 됩니다.
        """
        require_mutation_consent(consent, "reserve")
        self._require_session("reservation requires")
        route = "/classes/com.korail.mobile.certification.TicketReservation"
        form = build_discount_card_reservation_form(
            self.config,
            train,
            card_no=card_no,
        )
        return self._mutation(
            consent,
            "reserve",
            route,
            form,
            parser=self._hold_from_reservation_response,
        )

    def recalculate_price(
        self,
        request: PriceRecalculationRequest,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | ReservationHoldResponse:
        """홀드된 PNR 의 운임을 다른 할인 조합으로 다시 계산합니다. consent 게이트가 있습니다.

        ``POST certification.PriceReCalculation``(``CertificationService.java:35-37``,
        ``getDiscountPrice``)입니다. 앱은 예약의 할인 선택이 바뀔 때마다 결제
        화면에서 이것을 쏘고(``a6/C1042B.java:265-296``), 응답은 홀드가 돌려주는 것과
        같은 ``ReservationOut`` 입니다
        (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:584,753``).

        ``require_mutation_consent(consent, "price_recalculation")`` 와 로그인 세션을
        요구합니다. ``consent.dry_run`` 이 참이면(기본) 폼을 검증만 하고 가린
        :class:`~korail_mobile_api.consent.MutationPreview` 를 돌려주며 아무것도
        보내지 않습니다.

        **미검증 경로로 다뤄야 합니다.** 7.0.6 DTO 는 ``txtPsrmClCd1``,
        ``txtSeatAttCd2``, ``txtSeatAttCd4``, ``txtSeatAttCd5`` 를 더 선언하지만
        (``analysis/jadx/sources/com/korail/talk/network/model/PriceReCalculationIn.java:38-41``)
        이 폼은 넷 중 어느 것도 보내지 않습니다. 그 값은 앱의 화면 상태에서 오는데 그
        경로를 추적하지 않았습니다. 또 이 경로는 실서버에 한 번도 보낸 적이 없습니다.
        """
        require_mutation_consent(consent, "price_recalculation")
        self._require_session("price recalculation requires")
        route = "/classes/com.korail.mobile.certification.PriceReCalculation"
        form = build_price_recalculation_form(self.config, request)
        # Strict parsing, not the reserve methods' PNR-keeping fallback: a
        # recalculation creates no hold, and the caller already has the PNR it
        # asked about. A fallback here would only hide a parse failure on a
        # path that has never been sent live.
        return self._mutation(
            consent,
            "price_recalculation",
            route,
            form,
            parser=parse_reservation_hold_response,
        )

