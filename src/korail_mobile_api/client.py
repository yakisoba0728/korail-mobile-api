# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""조회·예약·결제 메서드를 전송·빌더·파서에 연결합니다. 인증이 필요한 조회도 있으며 변경 메서드는 호출 즉시 서버 상태를 바꿀 수 있습니다. 예약·청구·환불 결과가 불명확하면 재전송하지 말고 서버
상태를 먼저 확인하십시오."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
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
    StationRefundExecutionRequest,
    StationRefundExecutionResponse,
    StationRefundVerificationRequest,
    StationRefundVerificationResponse,
)
from .mutation_parsers import (
    parse_cart_add_response,
    parse_discount_card_purchase_response,
    parse_product_cancel_response,
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
    build_limousine_reservation_form,
    build_merge_reservation_form,
    build_price_recalculation_form,
    build_product_cancel_query,
    build_refund_form,
    build_reservation_form,
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

T = TypeVar("T")


def _hold_for_job(hold: ReservationHoldResponse, job_type: KorailReservationJobType) -> ReservationHoldResponse:
    # 앱은 예약대기 홀드를 결제하지 않습니다. 근거는 ReservationHoldResponse.payable 참고.
    if KorailReservationJobType(job_type) is KorailReservationJobType.STANDBY:
        return replace(hold, payable=False)
    return hold


class KorailClient:
    """KORAIL 7.0.6의 조회·예약·결제 기능을 제공하는 비공식 클라이언트입니다.

    DynaPath 는 합성 기기 값으로 기본 활성화됩니다. disable_dynapath=True 면 필수 경로의 로그인은 전송 전에 거절됩니다. 서버 수용은 보장하지 않습니다. transport
    에 MockTransport 를 넣어 오프라인 시험할 수 있습니다.

    NetFunnel 은 기본 활성화되며 관문 이름은 KorailConfig.netfunnel_actions 설명을 따릅니다. 대기·차단 결과를 무시하지 않습니다. 상태 변경은 별도 확인 절차 없이
    전송됩니다.

    with 문은 지원하지 않습니다. close 는 연결 풀만 닫습니다. 서버 로그아웃은 logout, 로컬 상태만 폐기할 때는 clear_session 을 별도로 호출하십시오."""

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
        """HTTP·대기열 연결 풀을 닫습니다. 네트워크 요청은 하지 않으며 로컬 로그인 상태·쿠키는 남습니다.
        로그인도 끝내려면 먼저 :meth:`logout`(서버 로그아웃 시도)이나 :meth:`clear_session`(로컬만 폐기)을 부르십시오."""
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
        input_flag: str | None = None,
        check_valid_pw: str = "Y",
        cust_id: str | None = "",
        etr_path: str | None = "",
    ) -> KorailSession:
        """기존 세션을 비운 뒤 서비스 상태·암호화 파라미터를 읽고 로그인합니다. 라우트: NetworkApi.java:459-460. member_no 는 회원번호·휴대폰번호·이메일이며
        input_flag 를 생략하면 infer_login_input_flag 가 선택합니다.

        로그인 거절은 앱처럼 코드로 가릅니다(:data:`~korail_mobile_api.session.KORAIL_LOGIN_CONTINUATION_CODES`).
        휴면(WRC000116)·비밀번호 변경(WRC000420)은 KorailAuthContinuationRequired 로 올리고 session.pending 에 남깁니다. 서비스 점검 등
        따로 분류된 코드는 그 KorailAppError 하위 예외, 그 밖의 거절(잠김 WRC000390, 정보 오류 WRR000101 등)이나 JSESSIONID 누락은
        ``code``·``raw`` 가 붙은 KorailAuthError 입니다. 사전 조회(MobileService.cache·common.code.do)의 FAIL 은
        KorailAppError 하위 예외, 전송 실패는 KorailTransportError, JSON·봉투·암호화 파라미터 이상은 KorailProtocolError 로 그대로 올라옵니다.
        일반 실패 시 세션·쿠키를 비우지만, 웹 단계 예외는 current=None 인 채 pending 과 응답 쿠키를 보존합니다.
        청구·예약 변경은 없습니다. 기존 실서버 로그인 확인: 2026-09-24; 웹 단계의 실서버 확인은 별도입니다.
        input_flag 를 생략하면 숫자만도 이메일도 아닌 ID(예: 하이픈이 든 전화번호)는 앱처럼 보내지 않고 KorailProtocolError 입니다."""
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

        쿠키 저장소(``JSESSIONID`` 포함), 현재 :class:`KorailSession`, 보류 중인 웹 단계 예외를 모두 비웁니다.
        서버 세션 무효화는 요청하지 않습니다. 서버 로그아웃을 시도하려면 :meth:`logout` 을 쓰십시오.
        청구·예약 변경은 없습니다. 로컬 처리이며 실서버 확인 대상이 아닙니다."""
        self.session.clear_session()

    def logout(self) -> None:
        """로그인 상태이면 서버 로그아웃(login.Logout)을 보내고, 어느 경우든 finally 에서 로컬 세션·쿠키를 비웁니다. FAIL 봉투는 예외가 아니지만(FAIL/P058 은
        세션 만료) 전송 오류 등은 그대로 전파됩니다. 서버 세션 무효화까지 보장하지 않으며 연결 풀은 close 로 닫습니다.
        청구·예약 변경은 없습니다. 기존 실서버 확인: 2026-09-24, 로그아웃 뒤 FAIL/P058."""
        self.session.logout()

    def _run_read(self, operation: Callable[[], T]) -> T:
        """조회·변경 실행 중 P058이 발생하면 로컬 세션을 비운 뒤 예외를 전파합니다."""
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
        """열차 조회 조건에 맞는 대기열 관문 이름을 반환합니다. 앱 근거: TrainScheduleViewModel.java:5213-5235."""
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
        parser: Callable[[dict[str, Any]], T],
        include_common: bool = True,
        include_dynapath: bool = False,
        require_envelope: bool = True,
        raise_on_fail: bool = True,
        omit_empty_fields: bool = True,
    ) -> T:
        """읽기 POST 를 실행하며 세션 만료 시 로컬 상태를 비우고 예외를 전파합니다. 자동 재로그인·재전송은 하지 않습니다."""
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
        parser: Callable[[dict[str, Any]], T],
        require_envelope: bool = True,
        include_common: bool = True,
        omit_empty_fields: bool = False,
    ) -> T:
        """GET 조회를 실행하고 세션 만료 시 로컬 상태를 비웁니다. 세션 만료 처리는 _run_read 를 따릅니다."""
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
        """상태 변경 폼을 전송하고 선택 파서로 응답을 변환합니다. KorailApiError는 유형을 유지하며 raw에 전체 응답, parser_raw에 기존 부분 원문을 둡니다. 다른 파서
        예외는 전체 raw를 가진 KorailProtocolError로 감쌉니다. 파싱 실패만으로 서버 변경 여부를 알 수 없으므로 상태 확인 없이 재전송하지 마십시오."""
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
        raw: dict[str, Any],
        parser: Callable[[dict[str, Any]], T],
    ) -> T:
        """POST·GET 변경 및 환불 검증의 파싱 오류에 전체 응답을 보존합니다. 재전송하지 않습니다."""
        try:
            return parser(raw)
        except KorailApiError as error:
            # 파싱 실패를 재전송 신호로 쓰면 중복 예약·결제가 생길 수 있으므로 전체 응답과 부분 원문을 함께 보존합니다. 변경 파서는 직접
            # 불러도 같도록 _preserve_read_raw 가 이미 옮겨 두므로, 그때는 parser_raw 를 덮어쓰지 않습니다.
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

        2026-09-21 실서버 확인: 같은 세션에서 :meth:`get_seat_cars` 를 먼저 호출하지 않고 이 메서드를 바로 부르면 ``KorailAppError: [3]인증정보에
        문제가 있습니다`` 가 돌아올 수 있습니다 — 실앱의 화면 진입 순서(호차 목록 → 좌석 배치도)와 같습니다. 호출 순서를 지키십시오."""
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
        """로그인 계정의 장바구니를 조회합니다. 열차·공항버스 홀드 행(pnr_no 있음)과 부가서비스 행(pnr_no 빈 값)이 함께 옵니다. 2026-09-24 라이브:
        add_to_cart 한 열차·공항버스 홀드가 행으로 나왔고, 홀드를 취소하자 장바구니도 비었습니다."""
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
        """입금 가능한 은행의 코드와 이름 목록을 조회합니다. ``POST dlay.dptnBank.do`` (``NetworkApi.java:392-393`` —
        ``postDptnBank(@Field("Device"), @Field("Version"), @Field("Key"))``; ``@FieldMap`` 이 아니라 개별
        ``@Field`` 세 개이며 postCashRfn·postDecrypt 도 같은 방식입니다). 로그인 필요."""
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
        """계정의 지연할인권 목록을 조회합니다. ``POST passCard.DelayDiscountView`` (``NetworkApi.java:352-353`` —
        ``postDelayDiscountView(@QueryMap)``. ``@FormUrlEncoded`` 선언인데 인자는 ``@QueryMap`` 이라, 7.0.6 도 이 라우트만은
        값을 쿼리스트링으로 붙입니다 — 이 메서드가 ``post_query`` 를 쓰는 이유입니다).

        로그인 필요."""
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
        """계정의 할인쿠폰 목록을 조회합니다. ``POST passCard.CouponView``(``NetworkApi.java:328-329`` —
        ``postCoupon(@FieldMap)``). 로그인 필요.

        보유분 없으면 ``WRG000000`` 으로 빈 결과(예외 아님)."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.passCard.CouponView",
            build_discount_coupon_form(page_no, pnr_no),
            parser=parse_discount_coupon_response,
            raise_on_fail=False,
        )

    def get_korail_point_summary(self) -> KorailPointSummaryResponse:
        """계정의 포인트·쿠폰·복지 자격 요약을 조회합니다. ``POST xPoint.MyXPointView``.

        로그인 필요. 복지 등록 상태(장애인증·보조견)도 함께 옵니다. 라우트 선언은
        ``NetworkApi.java:515-516``(``postMyXPointView(@FieldMap)``), 응답 필드는 ``MyXPointViewOut.java:27-74`` 입니다.
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
        """할인카드(N카드) 한 장을 이미 사용한 여행 내역을 조회합니다. 검증 못 함: N카드가 없는 계정이라 성공 응답을 본 적이 없습니다(2026-09-24 ERR000100 조회 자료
        없음)."""
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
        """할인카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회합니다. 검증 못 함: N카드가 없는 계정이라 성공 응답을 본 적이 없습니다(2026-09-24 WRR000100 사용횟수
        입력값 오류)."""
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
        """정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회합니다. 구매·예약은 하지 않습니다.

        ``WRG000000`` 응답은 빈 결과(예외 아님)로 반환하며, 정기권 보유 여부를 뜻한다고 단정하지 않습니다.

        종류·기간·나이 코드는 get_pass_menu("1") 의 일반정기권(0001)·기간자유형(0028) pass_data 에서 가져오십시오. 2026-09-25: 두 종류
        다섯 조합이 모두 SUCC(서울→부산 7편, 서울→대전 4편)였고, 2026-09-24 의 EAZ000028 은 내일로(0046) 코드를 넣은 결과였습니다."""
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

        이 라우트의 실제 DTO(``CrewCallCommonIn.java:50``)의 유일한 입력은 ``timeStamp`` 이며, 주지 않으면 호출 시점의 밀리초 epoch 입니다. 자세한
        근거는 ``read_payloads.build_crew_request_list_query`` 의 독스트링을 참고하십시오."""
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
        """로그인 계정이 예약한 여행상품 목록 한 페이지를 조회합니다. 여행상품 예약은 KORAIL 웹(/ebizmk/prd/rvStep1.do → rvStep2.do →
        reservation.do)에서만 만들어집니다. 2026-09-24 라이브: 웹에서 만든 결제 전 예약 1건이 예약확정(03)·결제상태 01 로 나왔고, 취소 뒤에는 목록에
        예약취소(고객)(05)로 남았습니다."""
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
        """여행상품 예약 한 건의 상세와 취소 조건을 조회합니다. reservation_sequence 는 목록 행의 reservation_sequence 입니다. 2026-09-24 라이브:
        고흥군 당일 자유여행 결제 전 예약에서 받을 금액 15,400원, 취소 수수료 0원, goods_sequence 0001, 포함 항목(무궁화 1972·1977 열차)을 읽었습니다."""
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
        """여행상품 예약을 취소합니다(product.ReservationCancel, GET). detail 은 get_product_detail 의 결과입니다. 앱은 결제 전 예약은 이
        호출로 해제하고(여행상품 목록의 X 버튼, 장바구니 삭제), 결제된 예약은 같은 호출로 환불합니다(MyTicketDetailViewModel.java:1183-1192,
        3271-3291). 수수료는 따로 묻지 않고 상세의 cancellation_fee·cancellation_amount 로 보여 줄 뿐이니 먼저 확인하십시오. 변경 요청이므로
        실패해도 자동으로 다시 보내지 않습니다. 2026-09-24 라이브: 결제 전 예약을 SUCC 로 취소했고 목록 상태가 05 로 바뀌었습니다. 결제된 예약의 환불은 확인하지
        못했습니다(여행상품 결제는 pay.intgStl.do 의 보호 상수 stlPrsJobId 때문에 라이브러리로 할 수 없습니다)."""
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
        """승차권 한 장의 영수증과 결제수단을 조회합니다.

        네 식별값과 선택적인 ``txt_index`` 는 같은 승차권 상세 응답에서 가져와야 합니다. ``sale_date`` 는 반환원표일자입니다. 비슷한
        OriginalTicketReference 와 날짜·창구번호 순서가 반대라 위치 인자로 넘기면 서로 바뀌므로 키워드로만 받습니다."""
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
        """한 열차의 자유석 호차와 안내 문구를 조회합니다. 요청 값은 열차 조회 행에서 가져옵니다.

        2026-09-25 라이브: 2026-10-06 평일 10개 노선 542편 가운데 203편을 조회했습니다. 조회 행의 ``free_car_count`` 가 001·002 인 183편은
        모두 SUCC/IRZ000001 과 호차 문구(예: "자유석 1량 : 18호차", "자유석 2량 : 17, 18호차")를, 000 인 20편은 SUCC/IRZ000005 와
        ``car_no=None`` 을 돌려줬습니다. 호차는 숫자 목록이 아니라 문구로 옵니다."""
        return self._post_read(
            "/classes/com.korail.mobile.trn.fresScar.do",
            build_free_seat_car_form(request),
            parser=parse_free_seat_car_response,
        )

    def get_guide_seat_condition(
        self,
        request: GuideSeatConditionRequest,
    ) -> GuideSeatConditionResponse:
        """도우미석 안내문을 읽습니다. 일반 FAIL 은 안내 응답으로 반환하지만 FAIL/P058 은 세션을 비우고 만료 예외를 냅니다.
        h_msg_cd·h_msg_txt 를 확인하십시오. 날짜 있는 비교 관측은 GuideSeatConditionRequest 참고. FAIL/MRR800011 은 대피도우미석
        대상(만20~50세, 시발~종착 이용)이 아니라는 회원 판정으로 보이며, 2026-09-25 에는 좌석코드 999 도 같은 응답이었습니다."""
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
        """좌석배정 예매 화면의 열차 목록을 조회합니다. 앱 호출: TrainScheduleViewModel.java:2639-2754. 2026-09-22 일반 검색 메뉴 11 의 7가지
        변형은 SUCC/WRG000000 과 빈 목록이었습니다. A1/A2 는 행을 반환한 관측값이며, 날짜·구간에 따라 WRD000057 로 거절될 수 있습니다. 빈 결과가 열차 부재가
        아닌 메뉴 차이일 수 있습니다. 열차조회 대기열을 거칩니다."""
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
        """열차 한두 편의 운임을 예매 전에 미리 계산해 받습니다. 앱은 열차 정보 화면의 운임·요금 탭에서만 부르고 표시만 합니다
        (TrainOpInfoViewModel.java:941-962; TrainOpInfoScreenKt.java:2055-2159). 표의 운임은 received_price, 요금은
        received_fare, 합계는 total_amount 입니다. 앱은 표시 중인 열차 번호의 행만 남기지만 이 메서드는 모든 행을 돌려줍니다.
        승객·할인 입력이 없는 기준 운임이라 예약 금액과 다를 수 있으므로 결제 금액은 홀드의 received_amount 를 보십시오.

        2026-09-25: 1구간은 일반실·특실 두 행, 환승 2구간은 여정 0001·0002 마다 두 행씩 네 행이었습니다. 같은 열차 성인 홀드의
        h_tot_prc 는 운임과 같았고(7,500원·21,600원, 성인 2명 43,200원) 정산액은 좌석 할인만큼 낮을 수 있었습니다(21,500원,
        토요일 20,400원)."""
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
        """N카드 2인 승차권의 전달 전 수령자 후보를 조회합니다. 앱의 isNCardTwoPeople() 분기를 따르며 보호 리터럴을 Y로 확정하지 않습니다
        (DeliveryTicketFormViewModel.java:697-700). 검증 못 함: 2026-09-22 표본 60장과 2026-09-24 조회는 IRZ000005였고,
        자료가 있는 응답은 확인하지 못했습니다. 다른 조건까지 일반화하지 않습니다. 전달 완료 내역은 get_pbp_acceptance_specifications를 사용합니다."""
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
        """승차권 여러 장의 PBP 수락 내역을 여정·좌석 단위로 조회합니다. 승차권 목록에서 pbp_acceptance_target_flag 가 Y 인 승차권을
        sale_date(YYYYMMDD)로 넘기십시오. 2026-09-25: Y 승차권 6장은 6장, 1장은 1장의 명세를 돌려줬고 N 승차권은 0건이었습니다."""
        self._require_session()
        return self._post_read(
            "/classes/com.korail.mobile.tk.pbpAcepSpec.do",
            build_pbp_acceptance_specification_form(tickets),
            parser=parse_pbp_acceptance_specification_response,
        )

    def get_original_ticket_inquiry(
        self,
        tickets: Sequence[OriginalTicketReference],
        *,
        ticket_count: int | None = None,
    ) -> OriginalTicketInquiryResponse:
        """승차권 변경의 출발점이 되는 원표(원승차권)를 조회합니다.

        2026-09-25: 구매이력의 인쇄완료(02) 승차권은 SUCC/IRT000001("원권조회완료"), 환불된(09) 승차권은 WRT200399 였습니다."""
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
        """자율 좌석/열차 변경으로 갈 수 있는 승차역과 변경 사유를 조회합니다. 요청은 승차권 없이 열차 정보만 받습니다. 2026-09-25:
        운행 중인 KTX 023 은 SUCC, 운행 시간 밖 열차는 WRT800176("좌석변경가능시간아님")이었습니다."""
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
        """승차권 한 장의 예상 환불액과 수수료를 조회합니다. 실제 환불은 하지 않습니다. 환불 단위는 refund와 같으며 여러 장의 PNR 총액은 각 승차권의 결과를 합산해야 합니다."""
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
        """요청한 공통코드 종류의 설정값을 조회합니다. 바인딩: NetworkApi.java:315-321. 앱 부팅은 코드 목록을 한 호출로 전달합니다
        (NetworkService.java:2015-2025). 2026-09-22: 부팅 상수 18개를 한 POST 로 보내 SUCC/API.I00000 과 18키를 받았으며 개별 요청
        결과와 같았습니다. 미등록 코드·빈 코드도 SUCC 와 빈 문자열 항목으로 돌아왔습니다. 관측한 응답을 그대로 반환하며 임의의 코드가 항상 지원된다는 보장은 없습니다."""
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
        """일반 또는 승차권별 MaaS 메뉴를 조회합니다. 원승차권 반환번호는 tkRetNo 반복 필드이며 하나로 합친 문자열이 아닙니다. NetworkApi.java:402-404 의
        postGdMenuLt 선언을 따릅니다."""
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

        열차조회 대기열을 거칩니다. ``peak_season`` 은 출발일이 성수기인지입니다 — 앱은 달력(``RunDateOutItem.isPeakSeason()``)으로 고르지만 그 판정
        코드값이 보호돼 있어 호출자가 정합니다. 거짓이면 라이브러리 기본 관문 ``act_8`` 이며 앱 aid 평문은 미확인입니다.
        ``use_special_schedule`` 이면 ``product_inquiry`` 관문입니다(**추정**)."""
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

        대기열은 :meth:`search_trains` 와 같습니다."""
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
        """직통 조회가 KorailNoDirectTrainError(WRD000061)일 때만 같은 query 로 환승 첫 페이지를 자동 조회합니다. continuation 은 직통 조회에만
        전달합니다.

        2026-09-22 라이브의 SUCC/WRG000000 빈 목록은 폴백하지 않습니다. 반환형뿐 아니라 trains 를 확인하십시오. 앱은 사용자 확인 후 필터와 열차군을
        TrainGroup.ALL(값 보호)로 바꿉니다(TrainScheduleViewModel.java:3216-3219,11051-11079). 이 메서드는 확인창 없이 열차군을 그대로
        둡니다. 오류 분기·smali 의 한계는 KorailNoDirectTrainError 참고."""
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
        """승차권 목록을 예약→승차권 구조로 읽습니다. mode 는 페이지 커서가 아닙니다. 1 은 현재 승차권, 2 는 구매이력이라는 뜻은 라이브 관측입니다. 필드 선언은
        MyTicketListIn.java:62 이지만 호출부 값은 보호돼 있습니다 (MyTicketBaseViewModel.java:980,1029;
        LoginViewModel.java:1083).

        mode=2 날짜는 YYYYMMDD 를 사용하십시오. 빌더는 날짜 폭·순서·기간을 검증하지 않습니다. 2026-09-22: 양쪽 누락, 한쪽 누락, 6자리, 역순의 네 표본은
        WRT100101 이었고, 2년 범위는 128행, 같은 달 범위는 3행이었습니다. 이 관측으로 최대 기간을 보장하지 않습니다. mode=1 도
        날짜를 명시하면 그대로 전송하며, 기본 빈 값만 전송 단계에서 생략됩니다. page_no 는 보정하지 않고 그대로
        보냅니다(라이브에서 확인한 값은 1)."""
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
        """열차 한 편에 실제 미결제 예약(홀드)을 만듭니다. 결제 또는 취소는 호출자 책임입니다. 좌석 속성은 명시값→열차 행→기본값
        순서입니다(TrainScheduleViewModel.java:2914-2930,2982-2999).

        응답 파싱이 실패하면 KorailProtocolError 이고 ``.raw`` 에 응답 전체(h_pnr_no 포함)가 있습니다. 홀드가 잡혔을 수 있으니 재시도하지 말고 ``.raw``
        나 get_reservation_history 로 확인하십시오. 이 주의사항은 다른 예약 메서드에도 적용됩니다. job_type 기본은 IMMEDIATE(1101)입니다.

        SEAT_DESIGNATED 는 승객별 좌석이 필요합니다. STANDBY 는 대기 가능한 행만 받으며, 성공한 대기 홀드는 confirm_standby_hold 로 알림 옵션을
        기록합니다. IRR000014 의 트리거 의미는 라이브 기록이고 앱 비교값은 보호돼 있습니다. MERGE_STANDING 은 병합 첫 홀드이며 후속 호출은 reserve_merge
        입니다. STANDBY 홀드는 ``payable=False`` 라 pay_with_card 가 거절합니다. 모든 변경 경로가 로그인을 요구합니다. 대기 예약에만 별도 회원 제한이
        있다는 근거는 없습니다."""
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
        """이미 만든 예약대기 홀드에 알림·좌석변경 옵션을 저장합니다. 새 홀드나 결제는 만들지 않습니다.

        라우트는 NetworkApi.java:639-640, 화면 입력은 ReservationWaitViewModel.java:68-80을 따릅니다. WAIT는
        ReservationJobId.java:21에 선언되지만 값은 보호돼 있습니다. IRR000014 메시지의 자산 기록만으로 앱 분기를 확정하지
        않습니다. 2026-09-25 라이브: 예약대기 홀드(SUCC/IRR000014) 뒤 sms_notify=False, allow_seat_class_change=False 로
        SUCC/IRZ000003("정상적으로 수정 되었습니다.")이었고 cancel_unpaid_hold 로 IRG000000 이었습니다. 알림·등급 변경을 켠 조합은
        검증하지 않았습니다."""
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
        """탑승 순서의 TrainSummary 두 개를 한 PNR 로 홀드합니다. search_transfer_trains 결과의 TransferItinerary.legs 를 넘길 수
        있습니다. 같은 라우트·DTO 의 여정 반복입니다(NetworkApi.java:752-753; TicketReservationIn.java:34-37,80). seat_classes
        는 공통값 또는 구간별 값이며 좌석 지정도 구간별입니다 (TicketReservationInJrny.java:69; TicketReservationInSrcar.java:51;
        TicketReservationInSrcarTrailing.java:52). 2026-07-31: 성인 1인·일반실·편도 환승이 SUCC/IRR000018, 49,700원, 여정 수
        2 의 한 PNR 로 반환됐고 한 번의 cancel_unpaid_hold 로 해제됐습니다. 다른 승객·객실 조합까지 검증된 것은 아닙니다."""
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
        """병합예약의 후속 요청으로 실제 미결제 예약을 만듭니다. 열차·승객·객실·job·좌석속성은 첫 홀드와 같게, merge_rows는 get_merge_seats_inquiry의
        trains로 지정합니다. 첫 요청과 다른 필드는 mutation_payloads.build_merge_reservation_form을 따릅니다. 호출 순서는
        MERGE_STANDING 첫 홀드→병합 조회→첫 홀드 취소→이 메서드입니다. 첫 홀드는 호출자가 취소해야
        합니다(ReservationMergeViewModel.java:1352,1556). 2026-09-22: 첫 홀드부터 여정 21/22로 나뉘었고 후속 호출은 별도 PNR을
        만들었습니다. 첫 홀드를 유지한 표본의 SUCC/WRR664260도 새 PNR·좌석이 있는 예약이었으며, 첫 홀드 취소 후 두 여정 입력 표본은 IRR000018이었습니다. 메시지만
        보고 실패로 간주하거나 재전송하지 말고 남은 예약을 각각 확인·취소하십시오."""
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
        """공항버스 좌석을 실제로 미결제 예약합니다. schedule 은 get_limousine_schedules 의 행, seat_nos 는
        get_limousine_seat_inventory 의 좌석번호이며 인원 수만큼 줍니다. 승객은 어른·어린이만 됩니다. 앱처럼 대기열 없이 열차 예약과 같은 경로로 보내고, 결제는
        pay_with_card, 취소는 cancel_unpaid_hold 입니다. 폼과 확인된 값은
        mutation_payloads.build_limousine_reservation_form 참고. 2026-09-24 라이브: 광명→인천공항 T1 어른 1명
        SUCC/IRR000018(16,000원)·어른+어린이 24,000원 홀드를 cancel_unpaid_hold 로 취소(IRG000000·P100)했고, 16,000원 홀드를
        pay_with_card 로 결제(SUCC/IRT000000)한 뒤 수수료 0원으로 refund(SUCC/IRT200277) 했습니다. 승차권 목록에는 "KTX-공항버스" 로
        나옵니다."""
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
        """미결제 홀드를 취소합니다. 앱처럼 ``ReservationCancel`` 로 먼저 취소 가능 여부를 묻고
        (``MyReservationViewModel.java:1557,1720-1745`` — 성공이면 확인창, 아니면 ``h_msg_txt`` 안내) 그다음
        ``ReservationCancelChk`` 로 취소합니다(``:1566``). 두 요청의 폼은 같습니다. 확인 단계가 FAIL 이면 코드에 맞는 예외이고 취소는 보내지 않습니다.
        ``check_first=False`` 면 바로 취소합니다.

        2026-09-24: 확인 단계는 SUCC/IRR000011("여정취소 가능합니다.")이었고 그 뒤에도 홀드가 남아 있었습니다(확인만 함). 취소는 IRG000000.
        2026-07-26·31 환승은 한 PNR 의 두 여정이 함께 풀렸습니다."""
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
        """홀드를 카드로 결제합니다. 실제 청구가 발생합니다. 카드 거절은 예외가 아니라 FAIL 응답으로 돌아오므로 str_result·h_msg_cd 를 확인하십시오. 2026-07-31:
        8,400원 1장 IRT000000 발권과 2인 PNR 결제 기록; 2026-09-15: 7.0.6 결제·전액 환불 기록; 2026-09-24: 결제 후
        refund(commission=) 로 수수료 0원 전액 환불. 2026-09-25: 대기열 POST·새 User-Agent 로 7,500원 결제(IRT000000, 정산액 =
        홀드 received_amount) 후 수수료 0원 환불. 모든 카드·요청 조합의 성공 보장은 아닙니다. 앱처럼 0원 홀드는 카드로 결제하지 않습니다
        (PayViewModel.java:15572)."""
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
        """PaidTicket 이 가리키는 발권 승차권 한 장을 환불합니다. PNR 전체 환불이 아닙니다. 여러 장이면 각 승차권의 결과·잔여 목록을 확인해야 합니다. 같은 장을 무조건
        재전송하지 마십시오. 국내 앱의 pbpAcepTgtFlg 는 상세값 에코(MyTicketDetailViewModel.java:1521)이나 외국인 경로는 보호
        상수(FTicketDetailViewModel.java:634)입니다. 라이브러리는 값이 없으면 빈 문자열을 만들고 전송 단계에서 생략합니다. 2026-07-31: 성인 2인
        16,800원 PNR 에 한 번 호출해 SUCC/IRT200277 과 8,400원이 반환됐고, 남은 한 장에 별도 환불을 한 뒤 목록이 비었습니다.

        ``commission`` 은 필수입니다. 앱은 승차권 상세·환불 두 화면 모두 먼저 수수료를 조회하고 성공해야만 환불을
        보냅니다(MyTicketDetailViewModel.java:300-358,
        RefundTicketViewModel$executeRefundCommission$2.smali:1045-1086). 먼저 :meth:`get_refund_commission` 을
        부르고 그 응답을 넘기십시오. 환불 화면처럼 ``tk_ret_tms_dv_cd``·``trnNo`` 도 싣습니다. ``latitude``/``longitude``
        는 앱이 위치를 얻었을 때만 싣는 값입니다(:func:`~korail_mobile_api.mutation_payloads.build_refund_form`).
        commission 은 자동 조회하지 않으며, 넘긴 응답이 SUCC 가 아니면 금액 보호를 위해 전송 전에 거절합니다. 앱의 검사
        자체는 CommonOut.isSuccess() 입니다.
        환불 화면의 보호된 ctlDvCd 는 생략하므로 그 경로의 전체 폼이 앱과 동일하다고 보장하지 않습니다.

        ``settle_mileage=True`` 는 앱처럼 ``commission`` 이 있고 사용 가능 마일리지가 수수료 이상일 때만 보냅니다
        (MyTicketDetailViewModel.java:1811-1823). 아니면 전송 전에 거절합니다. 앱이 함께 보는 진행 가능 플래그는 비교값이 보호돼
        확인하지 않습니다.

        환불 요청에는 금액이 없고(RefundTicketIn.java:66) 앱도 환불액과 결제액을 대조하지 않습니다. 앱이 수수료 응답의 보호된 코드로
        환불을 막는 분기는 구현하지 않았습니다. 2026-09-25: 7,500원 승차권의 수수료 조회가 환불 7,500원·수수료 0원이었고 환불은
        SUCC/IRT200277 이었습니다."""
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
        """역발행 승차권의 온라인 환불 가능 여부와 금액을 확인합니다. 실제 환불은 실행하지 않습니다. VerifyOnlineRefundsOut은 CommonOut을 상속하지 않아
        strResult 누락을 허용합니다 (http._NON_COMMON_OUT_READ_PATHS). 검증 못 함: 2026-09-24 상태표 기준 역발행 승차권이 없어 확인하지
        못했습니다."""
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
        """검증된 역발행 승차권의 환불을 요청합니다. 실제 환불·접수 상태를 바꿀 수 있으므로 반환 구분과 결과를 확인하십시오.
        응답이 불명확하면 재전송하지 말고 환불 상태를 확인하십시오. 검증 못 함: 2026-09-24 상태표 기준 역발행 승차권이 없어
        실행하지 못했습니다."""
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
        """미결제 예약을 실제 장바구니에 추가합니다(NetworkApi.java:266-267; AddCartListIn.java:52).
        psgDiscAdd_infos.psgDiscAdd_info는 discount_additions로 읽습니다(AddCartListOut.java:24-25,76). 2026-09-24:
        열차·공항버스 예약 모두 SUCC/IRZ000002였으나 할인 행은 없었습니다. 할인 행이 채워진 응답은 검증 못 함입니다."""
        self._require_session("cart add requires")
        route = "/classes/com.korail.mobile.cart.addCartList"
        form = build_cart_add_form(self.config, request)
        return self._mutation(route, form, parser=parse_cart_add_response)

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
    ) -> DiscountCardPurchaseResponse:
        """N카드 미결제 구매를 만듭니다. 경로 이름의 Info 가 조회를 뜻하지 않습니다. NetworkApi.java:336-337; NCardInfoOut.java:32-33 의 일괄결제
        대상과 금액은 PayViewModel.java:6628 의 결제 입력으로 이어집니다. 검증 못 함: 실제 N카드 구매(결제)로 이어지므로 실서버에서 시도하지 않았습니다."""
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
        """N카드의 유효기간을 실제로 연장합니다. reservation.dcntCrdExtn.do로 전송하며 로그인이 필요합니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지
        못했습니다."""
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
        """홀드의 할인 조합을 재계산합니다. 변경 결과를 읽은 뒤 결제·취소 여부를 판단하십시오. NetworkApi.java:583-584 는 일반 폼 외 여섯 반복 필드를 받습니다. 입력
        구성은 PayViewModel.java:902,1316,14278 이며 화면의 모든 변경 트리거는 확인되지 않았습니다. 선택 객실·좌석속성 4필드는
        PriceReCalculationIn.java:38-41 에 있으나 값을 채운 라이브 검증은 없습니다. 일반 경로의 기본 null 근거는
        PayViewModel.smali:11834-11850 입니다.

        2026-09-22: 무변경 요청은 ERR930202, 할인 변경 표본(hidDcntKndCd='131')은 SUCC/IRZ000008 과 ReservationOut 을 반환했고
        12스칼라·여정 추가 필드도 파싱됐습니다. 3개 열차에서 재현된 기록입니다. 결제에는 원래 홀드가 아니라 이 메서드가 돌려준 홀드를 넘기십시오. 원래 홀드의
        received_amount 는 재계산 전 금액입니다. 앱은 결제 화면에서만 재계산하므로 예약대기 PNR 에는 쓰지 마십시오.
        동일 PNR 재요청은 비교값에 따라 WRE800036 또는 성공으로 달랐습니다. 자동 재시도하지 마십시오.
        자격 검증과 할인 반영이 어긋난 관측도 있으므로 자격 없는 할인을 신청하는 용도로 사용하지 마십시오. 할인 코드 반영만으로 금액 변경을 보장하지 않습니다. 토요일 두 표본은
        WRR664296 과 금액 유지, 평일 표본은 28,600→20,000원(할인액 8,600원)이었습니다. 이는 표본 기록이지 일반 보장이 아닙니다.

        2026-09-25 재확인: 무변경은 ERR930202("변경항목이 없습니다."), 평일 할인 변경은 SUCC/IRZ000008 로 21,500→15,000원(좌석 할인코드
        204)이었습니다. 토요일은 같은 SUCC/IRZ000008 인데 금액이 20,400원 그대로여서 성공 코드만으로는 할인 미적용을 알 수 없으니
        received_amount 를 비교하십시오. 앱은 할인 화면의 선택을 보호된 표(ReqDiscount, PayViewModel.java:5462-5530)로 요청 코드에
        옮기고, 성공하면 금액을 이 응답으로 바꾼 뒤 로그인 상태면 장바구니 추가를 부르며(:14412-14431) 보호된 코드일 때
        "승객할인이 미적용 되었습니다." 를 띄웁니다(:14437-14446). 라이브러리는 코드 매핑과 그 안내를 하지 않습니다. 행은
        :meth:`PriceRecalculationRequest.for_hold` 로 앱처럼 홀드의 첫 여정 좌석에서 만들 수 있습니다(2026-09-25 실서버 SUCC/IRZ000008).

        ``add_to_cart=True`` 면 앱처럼 재계산이 성공한 뒤 같은 PNR 로 장바구니 추가(:meth:`add_to_cart`)를 이어서 보내고 그 응답을
        ``cart_addition`` 에 담습니다(:14428-14436). 앱은 장바구니 추가가 실패해도 안내만 띄우고 재계산 결과를 유지하므로 FAIL 응답도
        예외 없이 담습니다. 재계산이 실패하면 보내지 않습니다. 장바구니 요청에서 전송 오류가 나면 예외가 나므로 재계산 결과는
        예약 조회로 확인하십시오. 앱의 결제 경로는 장바구니 화면에서 넘어온 목록으로만 갈리므로(:5355, :6662-6684) 이 추가 뒤에도
        :meth:`pay_with_card` 와 같은 단일 예약 결제입니다. 2026-09-25: 홀드만으로는 장바구니가 비어 있었고, 재계산(21,500→15,000원)
        뒤 추가는 SUCC/IRZ000002 였으며 장바구니에 15,000원 행이 생겼다가 홀드를 취소하자 비었습니다."""
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
