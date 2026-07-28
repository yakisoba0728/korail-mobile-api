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
    KorailMutationNotAllowedError,
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
    OriginalTicketInquiryResponse,
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
    SelfSeatChangeInfoResponse,
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
    build_original_ticket_inquiry_form,
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
    build_self_seat_change_info_form,
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
    SelfSeatChangeInfoRequest,
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
    parse_original_ticket_inquiry_response,
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
    parse_self_seat_change_info_response,
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
    """KORAIL 모바일 앱(코레일톡)의 비공개 API 를 그대로 부르는 클라이언트.

    ``KorailClient()`` — 인자 없이 — 만들면 바로 동작한다.
    :class:`~korail_mobile_api.config.KorailConfig` 기본값이 앱의
    ``Device``/``Version``/``Key`` 와 DynaPath 안티오토메이션을 켠 상태로
    채워지기 때문이다. ``transport`` 는 시험용 :mod:`httpx` 전송로를 끼워 넣는
    자리다.

    읽기 메서드는 게이트가 없다. 상태를 바꾸는 메서드는 모두
    :class:`~korail_mobile_api.consent.MutationConsent` 를 키워드로 요구하며,
    기본 consent 는 어느 범주도 허용하지 않아
    :class:`~korail_mobile_api.errors.KorailMutationNotAllowedError` 로 막힌다.
    범주를 허용해도 ``dry_run`` 이 기본 참이라 아무것도 전송하지 않고
    :class:`~korail_mobile_api.consent.MutationPreview` 가 돌아온다.

    자원 정리는 :meth:`close` 다. ``__enter__``/``__exit__`` 를 정의하지 않으므로
    ``with`` 문으로는 쓸 수 없다. :meth:`close` 는 커넥션 풀만 닫으니 로그인까지
    끝내려면 :meth:`logout`(서버 세션 무효화)이나 :meth:`clear_session`(로컬만
    폐기)을 따로 부른다.

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

    def __init__(self, config: KorailConfig | None = None, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        self.session = KorailSessionClient(self.http)
        self._station_names: dict[str, str] | None = None

    def close(self) -> None:
        """HTTP 커넥션 풀을 닫는다. 로그인 상태는 건드리지 않는다.

        :meth:`~korail_mobile_api.http.KorailHttpClient.close` 로 위임하며
        네트워크 호출을 하지 않는다. 로그인까지 끝내려면 먼저
        :meth:`logout`(서버 세션 무효화) 이나 :meth:`clear_session`(로컬만
        폐기)을 부른다.
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
        """회원 자격증명으로 로그인하고 살아 있는 세션을 돌려준다.

        ``POST login.Login`` (``LoginService.java:17``). 부르는 즉시 기존
        세션을 먼저 버리고, 서비스 상태 캐시와 비밀번호 암호화 파라미터
        (``common.code.do``)를 읽은 뒤 변환한 비밀번호를 보낸다.

        ``member_no`` 는 회원번호·휴대폰번호·이메일 중 아무거나 되고,
        ``input_flag`` 를 주지 않으면
        :func:`~korail_mobile_api.session.infer_login_input_flag` 가 값의 모양을
        보고 ``"2"``/``"4"``/``"5"`` 중에서 고른다. ``cust_id``·``etr_path`` 는
        비어 있으면 전선에 실리지 않는다.

        :class:`~korail_mobile_api.models.KorailSession` 을 돌려주며 여기에
        ``JSESSIONID``, 회원카드번호, 고객번호(``strCustNo``)가 담긴다. 고객번호는
        :meth:`get_customer_trip_info` 와 :meth:`get_recent_delivery_history` 가
        따로 요구하는 값이다.

        서버가 ``strRedirectUrl`` 을 주면 2단계 인증이 필요하다는 뜻이라
        :class:`~korail_mobile_api.errors.KorailAuthContinuationRequired` 를
        올리고 그 예외를 ``session.pending`` 에 남긴다. 그 밖의 실패는
        :class:`~korail_mobile_api.errors.KorailAuthError` 이며, 쿠키가 오지
        않은 성공 응답도 같은 예외로 막는다.
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
        """서버에 알리지 않고 로컬 로그인 상태만 버린다.

        쿠키 저장소(``JSESSIONID`` 포함), 현재 :class:`KorailSession`, 보류
        중인 2단계 인증 상태를 모두 비운다. 네트워크 호출이 없으므로 서버
        쪽 세션은 스스로 만료될 때까지 살아 있다. 서버 세션까지 무효화
        하려면 :meth:`logout` 을 쓴다.
        """
        self.session.clear_session()

    def logout(self) -> None:
        """서버 세션을 무효화하고 로컬 로그인 상태도 버린다.

        ``GET login.Logout`` (``LoginService.java:29``). 요청에 질의값이 하나도
        없고 ``JSESSIONID`` 쿠키만으로 인증되므로 봉투를 싣지 않는다.

        로그인 상태가 아니면 요청 자체를 보내지 않는다. 서버 무효화는
        최선노력이라 전송이 실패하거나 세션이 이미 만료돼 있어도 예외를 올리지
        않고, 로컬 상태(:meth:`clear_session` 이 지우는 것들)는 어느 경우에나
        비워진다. HTTP 커넥션 풀은 그대로 남으니 :meth:`close` 는 따로 부른다.
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

    def get_seat_cars(
        self,
        train: TrainSummary,
        *,
        passenger_count: int = 1,
        room_class_code: str = "1",
    ) -> SeatCarListResponse:
        """좌석지정 화면이 쓰는 한 열차의 호차 목록을 조회한다.

        ``POST research.TrainResearch`` (``ResearchService.java:35``). 로그인
        필요 — 세션이 없으면 :class:`~korail_mobile_api.errors.KorailAuthError`
        다. ``train`` 은 :meth:`search_trains` 가 준
        :class:`~korail_mobile_api.models.TrainSummary` 행이어야 하고, 열차번호·
        역코드·운행순서의 자릿수를 요청 전에 검사한다. ``passenger_count`` 는
        1~9, ``room_class_code`` 는 ``"1"``(일반실) 또는 ``"2"``(특실)다.

        :class:`~korail_mobile_api.models.SeatCarListResponse` 를 돌려주며 각
        호차는 번호와 잔여석, 좌석속성을 가진다. ``srcar_infos`` 가 ``null``
        이면 ``cars`` 가 빈 튜플이 될 뿐 예외가 아니다. 호차번호가 중복된
        응답은 :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        """
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
        """한 호차의 좌석 배치와 좌석별 판매 가능 여부를 조회한다.

        ``POST research.TResidualSeatsResearch.do``
        (``ResearchService.java:57``). 로그인 필요. ``car_no`` 는
        :meth:`get_seat_cars` 가 준 호차번호이며 양의 정수여야 한다. 나머지
        인자의 뜻과 검사는 :meth:`get_seat_cars` 와 같다.

        :class:`~korail_mobile_api.models.SeatInventoryResponse` 를 돌려준다.
        좌석마다 좌석번호·판매가능플래그·방향·기타 속성이 붙어 있어
        :meth:`reserve` 의 ``seats`` 에 넣을
        :class:`~korail_mobile_api.mutation_models.KorailSeatAssignment` 를 여기서
        고른다. 이 라우트는 호차 목록과 달리 관대하지 않다 — ``seatList``,
        ``layout_type``, ``seat_ary_cd``, ``seat_remain_count``,
        ``seat_total_count`` 가 모두 필수이고, 하나라도 없거나 잔여석이 전체석보다
        많으면 :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
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
        """리무진 연계 구간의 운행 스케줄 한 페이지를 조회한다.

        ``POST lmu.scdlQry.do`` (``BusReservationService.java:27``). 세션
        가드가 없어 비로그인 상태에서도 부를 수 있다. ``query`` 는 정확히
        :class:`~korail_mobile_api.limousine_models.LimousineScheduleQuery`
        여야 하고(하위 클래스는 거부), 날짜는 ``YYYYMMDD``, 시각은
        ``HHMMSS``, 역은 이름이 아니라 역코드로 준다.

        :class:`~korail_mobile_api.limousine_models.LimousineScheduleResponse`
        를 돌려준다. 서버가 ``trainList`` 를 비우거나 아예 내려보내지
        않으면 ``schedules`` 가 빈 튜플이 될 뿐 예외가 아니다. 다음 페이지
        여부는 ``following_page_extension`` 으로 판단한다. 봉투는 정확히
        ``SUCC`` 여야 하며 그 외에는 예외다.

        라이브 미검증 — 요청·응답 모양은 APK 선언에서 왔다.
        """
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
        """리무진 연계 편 한 호차의 좌석 점유 상태를 조회한다.

        ``POST lms.TResidualSeatsResearch.do``
        (``BusReservationService.java:31``). 세션 가드가 없다. ``query`` 는
        정확히
        :class:`~korail_mobile_api.limousine_models.LimousineSeatInventoryQuery`
        여야 한다.

        :class:`~korail_mobile_api.limousine_models.LimousineSeatInventoryResponse`
        를 돌려준다. 스케줄 조회와 달리 ``seatList`` 키는 필수라서, 키가
        없으면 :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        빈 리스트 자체는 정상이고 좌석 정보가 하나도 없다는 뜻이다.

        라이브 미검증.
        """
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
        """좌석이동 화면이 쓰는 리무진 연계 열차 목록을 조회한다.

        ``POST seatMovie.LimousineScheduleView``
        (``SeatMovieService.java:16``). 세션 가드가 없다. 이 폼만은 공통
        ``Key`` 대신 요청마다 새로 만든 ``Sid`` 를 싣는다. 역은 코드가
        아니라 역이름으로, 날짜는 ``YYYYMMDD`` 로 준다. 인원은
        ``txtPsgFlg_1``~``txtPsgFlg_5`` 다섯 칸으로 나뉘어 경로·중증장애·
        경증장애가 각각 제 칸을 가진다.

        :class:`~korail_mobile_api.limousine_models.LimousineScheduleViewResponse`
        를 돌려준다. ``trn_infos`` 가 ``null`` 이면 ``schedules`` 가 빈
        튜플이 될 뿐 예외가 아니다. 다음 페이지 여부는 ``next_page_flag``,
        전체 건수는 ``result_count`` 다.

        라이브 미검증.
        """
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
        """예매 서비스가 열려 있는지를 서버 봉투로 확인한다.

        ``GET /file/CACHE/MobileService.cache`` (``CacheService.java:11``).
        세션 가드가 없다. 로그인 절차가 맨 먼저 부르는 것도 이 읽기다.
        ``timestamp_ms`` 는 캐시 무효화용 ``timeStamp`` 값이고, 생략하면 현재
        시각을 쓴다.

        :class:`~korail_mobile_api.read_models.ServiceStatusResponse` 를
        돌려주는데 고유 필드가 없고 봉투(``h_msg_cd``/``h_msg_txt``/
        ``str_result``)뿐이다. 점검 중이라는 사실은 봉투가 ``FAIL`` 로 오면서
        :class:`~korail_mobile_api.errors.KorailAppError` 가 되는 것으로 드러난다.
        """
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
        """로그인 계정의 장바구니에 담긴 부가상품 항목을 조회한다.

        ``POST cart.showCartList`` (``CartService.java:15``). 로그인 필요 —
        세션이 없으면 :class:`~korail_mobile_api.errors.KorailAuthError` 다.
        ``pnr_no`` 와 ``additional_service_request_no`` 는 기본이 빈
        문자열이고, 그대로 두면 계정 전체를, 채우면 그 예약번호·요청번호로
        범위를 좁힌다.

        :class:`~korail_mobile_api.read_models.CartListResponse` 를
        돌려준다. 장바구니가 비어 있으면 ``items`` 가 빈 튜플이며 예외가
        아니다. 이 라우트의 성공 응답은 ``h_msg_cd`` 없이 ``strResult`` 만
        싣기도 해서 봉투 검사가 그 모양을 허용한다.
        """
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
        """지연 환불금을 받을 수 있는 입금은행 코드표를 조회한다.

        ``POST dlay.dptnBank.do`` (``DelayService.java:30``). 인자가 없고
        로그인이 필요하다.

        :class:`~korail_mobile_api.read_models.DepositBankListResponse` 를
        돌려주며, 각 항목은 은행코드(``dptnBankCd``)와 표시명이다. 지연
        현금환불 신청에서 은행을 고를 때 쓰는 코드표일 뿐, 이 메서드가
        환불을 신청하지는 않는다.
        """
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
        """계정이 보유한 지연할인권을 조회한다.

        ``POST passCard.DelayDiscountView`` (``PassCardService.java:20``).
        로그인 필요. ``departure_date_to`` 는 ``YYYYMMDD`` 이며, 그 날짜
        까지 출발한 승차권에 붙은 할인권으로 범위를 자른다.

        :class:`~korail_mobile_api.read_models.DelayDiscountTicketListResponse`
        를 돌려준다. 보유분이 없으면 ``items`` 가 빈 튜플이고 예외가
        아니다. 항목의 ``original_sale_date``·``window_no``·
        ``sale_sequence``·``return_password`` 네 값이 원승차권을 가리키는
        자격증명이다.
        """
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
        """계정이 보유한 할인쿠폰 한 페이지를 조회한다.

        ``POST passCard.CouponView`` (``PassCardService.java:24``). 로그인
        필요. ``page_no`` 는 1부터 세고, ``pnr_no`` 는 특정 예약에 쓸 수
        있는 쿠폰만 보고 싶을 때만 채운다.

        :class:`~korail_mobile_api.read_models.DiscountCouponListResponse`
        를 돌려주고 총 페이지 수는 ``total_pages`` 다. 보유 쿠폰이 없으면
        서버가 ``strResult=FAIL`` 에 ``h_msg_cd=WRG000000``("조회 결과가
        없습니다")를 실어 보내는데, 이 코드는 빈 결과로 받아들여 ``items``
        가 빈 응답을 돌려준다. 예외가 아니다.
        """
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
        """마이페이지의 포인트·쿠폰·복지자격 요약을 한 번에 조회한다.

        ``POST xPoint.MyXPointView`` (``XPointService.java:18-20``), 앱이
        마이페이지를 열 때 부르는 읽기다(``MyPageActivity.java:414``).
        인자가 없다 — ``point_dv_cd`` 는 DAO 가 직접 넣는 리터럴 ``"0"``
        이고(``KorailPointInquiryDao.java:91``) 요청 클래스도 없다.
        로그인 필요.

        :class:`~korail_mobile_api.read_models.KorailPointSummaryResponse` 를
        돌려준다. 포인트 잔액과 쿠폰·지연할인권 개수 말고도 계정의 복지
        등록 상태가 함께 온다: ``h_hdcp_flg`` 가 ``"Y"`` 일 때만 앱이
        장애인 항목 전체를 그리고(``MyPageActivity.java:206-212``),
        ``h_subt_dcs_cl_nm`` 이 장애인증, ``h_cust_lead_flg_nm`` 이
        보조견이다(``:353-355``, ``:393-394``). 장애·안내견 운임 자격을
        확인하는 가장 싼 읽기다.

        읽기만 하며 포인트를 움직이지 않는다. 사용자 비밀번호를 싣는
        포인트 라우트(``mlg.lpotAthn.do``, ``xPoint.XPointView``)는 틀린
        비밀번호가 서버 실패 카운터를 올리므로 일부러 구현하지 않았다.

        라이브 미검증이고, 복지 필드 해석은 앱 동작에서 유추한 것이다.
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
        """마일리지 적립/사용 내역 한 페이지를 조회한다.

        ``POST mlg.amtSpec.do`` (``XPointService.java:26-28``). 로그인
        필요. ``request`` 가 원장(KTX 마일리지 / 철도포인트), 증감 필터
        (전체/적립/사용), 조회 기간을 고른다. 페이지 크기는 앱이 20 으로
        박아 두어(``MileageHistoryActivity.java:274``) 바꿀 수 없다.

        :class:`~korail_mobile_api.read_models.MileageHistoryResponse` 를
        돌려준다. 페이지 넘기기는 호출자 몫이고,
        :attr:`~korail_mobile_api.read_models.MileageHistoryResponse.page_count`
        이 앱이 스크롤하는 상한이다(``:158,581``).

        라이브 미검증 — 응답 모양은 ``MileageInquiryDao`` 선언이다.
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
        """할인카드(N카드) 한 장을 이미 사용한 여행 내역을 조회한다.

        ``GET ticket.dcntCrdUseQry.do`` (``ResearchService.java:51-52``),
        승차권 목록의 "사용 내역 조회하기" 버튼이 부르는 읽기다
        (``Y4/Q.java:347-353``). 로그인 필요.

        ``card_no`` 는 카드 자신의 번호이고 사용자가 입력하는 값이 아니다.
        N카드 승차권 상세 응답의 ``dcnt_crd_info.h_dcnt_crd_no``
        (``Y4/C0907b.java:303``), 즉
        :attr:`~korail_mobile_api.read_models.RefundTicketDetailResponse.discount_card`
        에서 꺼내 쓴다.

        :class:`~korail_mobile_api.read_models.DiscountCardUsageListResponse`
        를 돌려준다. 남의 카드번호로 부르면 서버가 거절하며, 여기에 그것을
        우회하는 장치는 없다.

        라이브 미검증 — 이 프로젝트가 닿을 수 있는 계정 중 N카드를 가진
        것이 없어, 요청은 APK 선언, 응답은 ``NCardHistoryDao`` 선언이다.
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
        """할인카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회한다.

        ``GET research.dcntCrdScheduleView.do``
        (``ResearchService.java:54-55``). 로그인 필요. 일반 열차 조회가
        아니다 — N카드는 정해진 1~3 개 구간에 묶여 팔리므로, 이 라우트는
        역코드가 아니라 카드 상품(``dcntCrdKndCd`` / ``dcntCrdKndMgNo``)을
        키로 "이 카드가 이 구간에서 커버하는 열차"를 답한다.

        :class:`~korail_mobile_api.read_models.DiscountCardScheduleResponse`
        를 돌려준다. 페이지 넘기기는 호출자 몫으로,
        :attr:`~korail_mobile_api.read_models.DiscountCardScheduleResponse.following_page_exists`
        가 ``"Y"`` 인 동안 앱은 ``qryPgNo`` 를 올려 다시 읽는다
        (``SectionNCardInquiryActivity.java:406-408``). 다음 요청은
        ``page_no`` 를 채워 만들고, 첫 페이지는 ``None`` 으로 둔다 —
        v6.5.0 이 보내는 모양이 그것이다.

        라이브 미검증 — 사유는 :meth:`get_discount_card_usage_history` 와
        같다.
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
        """정기권 상품 하나의 사용 개시 가능일과 발권 가능일을 조회한다.

        ``POST pass.passInfoList`` (``PassService.java:31``). 세션 가드가
        없다. 세 인자는 모두 공통코드 값이다 — ``kind_code`` 는 정기권
        종류, ``period_code`` 는 사용기간, ``age_code`` 는 연령구분이며 빈
        문자열은 거부된다.

        :class:`~korail_mobile_api.read_models.PassAvailabilityResponse` 를
        돌려준다. ``open_dates`` 가 사용 개시일(``YYYYMMDD``),
        ``ticket_issue_dates`` 가 발권일, ``offices`` 가 수령 창구다.
        성공 응답은 자기 코드를 ``main_info.h_msg_cd`` 안에 넣고 최상위엔
        ``strResult`` 만 남기므로 봉투 검사가 그 모양을 허용한다. 실패
        응답은 최상위 봉투를 그대로 실어 예외가 된다.
        """
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
        """정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회한다.

        ``POST pass.passScheduleInfoList`` (``PassService.java:27``).
        로그인 필요. ``request`` 는 구간(역이름), 출발일 ``YYYYMMDD``,
        출발시각, 정기권 종류·기간·연령 코드, 페이지 번호와 페이지 크기를
        담는다.

        :class:`~korail_mobile_api.read_models.PassScheduleResponse` 를
        돌려준다. 조건에 맞는 열차가 없으면 서버가 ``strResult=FAIL`` 에
        ``h_msg_cd=WRG000000`` 을 실어 보내는데, 앱도 이 코드를 오류창 없이
        "결과 없음"으로 그리므로(``CommutationInquiryActivity.java:182``)
        여기서도 ``schedules`` 가 빈 응답으로 돌려준다. 그 밖의 ``FAIL`` 은
        예외다.

        라이브 미검증.
        """
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
        """여행상품 메뉴 화면에 그릴 항목과 그 안의 문구 묶음을 조회한다.

        ``POST pass.trGdMenuLt.do`` (``PassService.java:47``). 로그인 필요.
        인자가 없고 폼은 ``Device``/``Version`` 두 칸뿐이라 공통 ``Key`` 조차
        싣지 않는다.

        :class:`~korail_mobile_api.read_models.TripMenuResponse` 를 돌려준다.
        항목마다 제목·설명·버튼 문구·링크가 있고, 그 아래 ``contents`` 가 화면에
        펼칠 세부 문구(동의문·안내·이미지·링크)다. ``menuList`` 가 없거나
        ``null`` 이면 ``items`` 가 빈 튜플이 될 뿐 예외가 아니다.
        """
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
        """정기권·패스 메뉴 한 갈래의 화면 구성 항목을 조회한다.

        ``POST pass.passMenu.do`` (``PassService.java:35``). 세션 가드가
        없다. ``menu_no`` 는 상위 메뉴가 내려준 메뉴 번호이며 빈 문자열은
        거부된다.

        :class:`~korail_mobile_api.read_models.PassMenuResponse` 를
        돌려준다. 각 항목은 화면 문구(제목·설명·안내)와 함께 상품 정보
        (``goods_data``), 정기권 파라미터(``pass_data``)를 나른다. 성공
        응답은 ``{"list": [...], "strResult": "SUCC"}`` 뿐이고 ``h_msg_cd``
        가 없어서 봉투 검사가 그 모양을 허용한다. 서버가 모르는
        ``menu_no`` 는 봉투를 갖춘 ``FAIL`` 로 돌아와 예외가 된다.
        """
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
        """승무원 호출 화면에 띄울 요청 사유 선택지를 조회한다.

        ``GET push.crwCallRq.do`` (``PushService.java:16``). 세션 가드가
        없다. ``query_division_code`` 는 어느 갈래의 문구 묶음을 받을지
        고르는 공통코드이며 빈 문자열은 거부된다.

        :class:`~korail_mobile_api.read_models.CrewRequestListResponse` 를
        돌려준다. 항목은 문구(``content``)와 연동 메시지코드뿐이고,
        선택지가 없으면 ``items`` 가 빈 튜플이다. 이 메서드는 목록만 읽을
        뿐 승무원을 호출하지 않는다.

        라이브 미검증.
        """
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
        """정기권 종류 하나의 안내 문구와 조회 파라미터를 받아온다.

        ``GET push.cmtrKnd.do`` (``PushService.java:19``). 세션 가드가
        없다. ``commuter_kind_code`` 는 정기권 종류 코드이며 빈 문자열은
        거부된다.

        :class:`~korail_mobile_api.read_models.CommuterKindMenuResponse` 를
        돌려준다. 목록이 아니라 단일 객체이고, 핵심은 ``pass_data`` 다 —
        :meth:`get_commuter_info` 가 이 값을 그대로 받아 쓴다.
        ``after_day`` 는 며칠 뒤부터 개시할 수 있는지, ``agreement`` 는
        동의 문구다.

        라이브 미검증.
        """
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
        """로그인 계정이 예약한 여행상품 목록 한 페이지를 조회한다.

        ``GET product.ReservationList`` (``ProductService.java:15``). 로그인
        필요. 승차권이 아니라 상품 예약이다. ``page_no`` 는 1부터 세고
        ``page_size`` 는 한 페이지 건수이며, 둘 다 1 이상이어야 한다.

        :class:`~korail_mobile_api.read_models.ProductReservationListResponse` 를
        돌려주고 전체 건수는 ``total_count``(``strTotCnt``)다. 항목마다 상품명,
        예약상태, 결제기한, 그리고 :meth:`get_product_detail` 에 넣을
        ``virtual_reservation_no``(``strVrRsvNo``)가 들어 있다.

        예약이 없으면 서버가 ``mainInfo`` 를 아예 빼고 ``strResult=SUCC`` 만
        보내는데, 그때는 ``items`` 가 빈 튜플인 응답이 되고 예외가 아니다.
        봉투 검사도 그 모양을 허용한다.
        """
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
        """여행상품 예약 한 건의 상세와 취소 조건을 조회한다.

        ``GET product.ReservationDetail`` (``ProductService.java:12``). 로그인
        필요. 두 인자는 :meth:`get_product_reservations` 가 준
        ``virtual_reservation_no``(``txtVrRsNo``)와 그 예약일련번호
        (``txtVrRsvSqNo``)이며 빈 문자열은 거부된다.

        :class:`~korail_mobile_api.read_models.ProductDetailResponse` 를
        돌려준다. 상품명·예약상태·이용기간과 함께 취소기한
        (``cancellation_deadline``), 취소 시 환급액, 취소수수료가 오고,
        ``included_item_names`` 가 구성품목이다. 서버가 ``mainInfo`` 를 빼면
        봉투만 담긴 응답이 되고 나머지 필드는 모두 ``None`` 이다.
        """
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
        """승차권 한 장의 영수증과 그 결제수단 내역을 조회한다.

        ``POST receipt.ReceiptInfo`` (``ReceiptService.java:10``). 로그인
        필요. 네 인자가 승차권의 네 부분 자격증명이다 — ``sale_date`` 는
        발매일 ``YYYYMMDD``, ``window_no`` 는 발권창구번호, ``sale_sequence`` 는
        발매일련번호, ``return_password`` 는 반환비밀번호이며 어느 하나도
        비어 있을 수 없다.

        :class:`~korail_mobile_api.read_models.TicketReceiptResponse` 를
        돌려준다. 영수증마다 ``payments`` 가 붙어 결제수단명·승인일자·승인번호·
        할부개월·금액·카드번호를 나른다. 서버가 ``receipt_infos`` 를 비우거나
        빼면 ``items`` 가 빈 튜플이 될 뿐 예외가 아니다.
        """
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
        """로그인 계정에 아직 살아 있는 예약(미결제 홀드 포함)을 조회한다.

        ``GET reservation.ReservationView``
        (``ReservationService.java:21``). 로그인 필요. 인자가 없다.

        :class:`~korail_mobile_api.read_models.ReservationHistoryResponse` 를
        돌려주고 ``trains`` 는 ``items`` 의 별칭이다. 행마다 출발·도착역과
        시각, 열차번호, 좌석·입석 수, 결제 여부 플래그, 그리고 PNR 이 온다 —
        그 PNR 이 :meth:`get_ticket_reservation_detail` 과
        :meth:`cancel_unpaid_hold` 의 입력이다.

        예약이 하나도 없으면 서버가 ``strResult=FAIL`` 에 ``h_msg_cd=P100`` 을
        실어 보내는데, 이 코드는 빈 결과로 받아들여 ``items`` 가 빈 응답을
        돌려준다. 예외가 아니다. 그 밖의 ``FAIL`` 은 예외다.
        """
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
        """한 열차의 자유석 호차와 안내 문구를 조회한다.

        ``POST trn.fresScar.do`` (``TrainsInfoService.java:20``). 세션
        가드가 없다. ``request`` 는 정확히
        :class:`~korail_mobile_api.read_payloads.FreeSeatCarRequest` 여야
        하며, 운행일 ``YYYYMMDD``, 열차번호(빌더가 5자리로 0을 채운다),
        출발·도착역의 조성순서와 운행순서를 담는다.

        :class:`~korail_mobile_api.read_models.FreeSeatCarResponse` 를
        돌려준다. 목록이 아니라 제목·호차·본문 세 문자열이고, 서버가 비워
        보내면 ``None`` 이다.
        """
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
        """좌석속성 코드 하나에 대한 안내를 서버 봉투로 받는다.

        ``POST reservation.guideSeatCnd.do``
        (``ReservationService.java:17``). 세션 가드가 없다. ``request`` 는
        정확히
        :class:`~korail_mobile_api.read_payloads.GuideSeatConditionRequest`
        여야 하고 ``rqSeatAttCd`` 하나만 싣는다.

        DAO 의 응답 타입이 맨 ``BaseResponse`` 라 고유 필드가 없다 —
        돌려주는
        :class:`~korail_mobile_api.read_models.GuideSeatConditionResponse`
        는 봉투(``h_msg_cd``/``h_msg_txt``/``str_result``)뿐이고, 안내
        문구는 ``h_msg_txt`` 에 실려 온다. 서버가 인정하지 않는 코드는
        ``FAIL`` 로 돌아와 :class:`~korail_mobile_api.errors.KorailAppError`
        가 된다.
        """
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
        """좌석배정 예매 화면이 쓰는 열차 목록을 조회한다.

        ``POST research.assignScheduleView.do``
        (``ResearchService.java:31``). 세션 가드가 없다. ``request`` 는 정확히
        :class:`~korail_mobile_api.read_payloads.SeatAssignmentScheduleRequest`
        여야 하고, 출발일 ``YYYYMMDD``, 출발시각 ``HHMMSS``, 출발·도착역은
        코드가 아니라 역이름, 그리고 열차그룹·실별·좌석속성 코드와 인원을
        담는다.

        :class:`~korail_mobile_api.read_models.SeatAssignmentScheduleResponse` 를
        돌려준다. ``trains`` 가 그 조건에 맞는 열차이고, 조건에 맞는 열차가
        없어도 빈 튜플일 뿐 예외가 아니다.
        ``merge_reservation_possible_flag`` 는 병합예약이 가능한지,
        ``next_page_flag`` 는 다음 페이지가 있는지를 알려준다. 다만 이 폼에는
        페이지 인자가 없어서 첫 페이지만 받을 수 있다.

        라이브 미검증.
        """
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
        """좌석 병합이 가능한 열차와 좌석이 갈리는 중간역을 조회한다.

        ``POST research.mergeSeatsC.do`` (``ResearchService.java:47``).
        세션 가드가 없다. ``request`` 는 정확히
        :class:`~korail_mobile_api.read_payloads.MergeSeatsInquiryRequest`
        여야 하고, 승차일시·운행일시·열차번호(5자리로 0 채움), 출발·도착·
        선택 역이름, 실별코드·좌석속성코드·총인원을 담는다.

        :class:`~korail_mobile_api.read_models.MergeSeatsInquiryResponse` 를
        돌려준다. ``merge_reservation_possible_flag`` 가 병합 가능 여부,
        ``intermediate_stations`` 가 중간역, ``trains`` 가 그 구간의
        열차다. 각 목록은 비어 있어도 정상이다.

        라이브 미검증.
        """
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
        """다자녀 할인 대상으로 등록된 가족 구성원을 조회한다.

        ``POST cust.mchdDcntTgt.do`` (``CustService.java:11``). 로그인
        필요. ``departure_date`` 는 ``YYYYMMDD`` 이고, 그 날짜 기준으로
        자격이 판정된다.

        :class:`~korail_mobile_api.read_models.MultiChildDiscountTargetResponse`
        를 돌려준다. 파서가 성공 봉투를 요구하므로, 서버가 ``WRC800029``
        처럼 실패 코드로 답하면 빈 목록이 아니라
        :class:`~korail_mobile_api.errors.KorailAppError` 가 된다.
        """
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
        """로그인 계정에 저장된 여행 편의설정을 조회한다.

        ``POST research.custTripInfo.do`` (``ResearchService.java:43``).
        로그인 필요. 인자가 없다 — 고객번호는 로그인 응답의 ``strCustNo``
        에서 가져오며, 그 값이 비어 있으면 세션이 있어도 요청 전에
        :class:`~korail_mobile_api.errors.KorailAuthError` 로 막힌다.
        ``medDvCd``/``regSqno`` 는 빌더가 넣는 리터럴 ``"03"``/``"0"`` 이다.

        :class:`~korail_mobile_api.read_models.CustomerTripInfoResponse` 를
        돌려준다. 저장해 둔 설정이 없으면 ``trips`` 가 빈 튜플이고 예외가
        아니다.
        """
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
        """계정이 신청한 MaaS 부가서비스 내역을 조회한다.

        ``POST copt.gdReqQry.do`` (``TicketService.java:50``). 로그인
        필요. ``query`` 를 생략하면
        :meth:`~korail_mobile_api.read_payloads.MaasServiceDetailQuery.current`
        가 쓰이고, 그것은 기간 필드를 아예 빼서 현재 건만 받는다. 기간을
        지정할 때는 시작일과 종료일을 둘 다 ``YYYYMMDD`` 로 채워야 하며,
        한쪽만 주면 거부된다.

        :class:`~korail_mobile_api.read_models.MaasServiceDetailListResponse`
        를 돌려준다. 신청 내역이 없으면 ``details`` 가 빈 튜플이고 예외가
        아니다.
        """
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
        """승차권 변경으로 옮겨 갈 수 있는 날짜 목록을 조회한다.

        ``POST reservation.tripChgDate.do`` (``TicketService.java:58``).
        로그인 필요. ``departure_date`` 는 원승차권의 출발일 ``YYYYMMDD`` 이고
        폼에는 ``tripChgDate`` 한 칸으로 실린다. 승차권 변경 사슬에서 날짜를
        묻는 쪽이고, 원표 자체는 :meth:`get_original_ticket_inquiry` 가 읽는다.

        :class:`~korail_mobile_api.read_models.TripChangeDateResponse` 를
        돌려준다. ``trip_change_dates`` 가 선택 가능한 날짜(``YYYYMMDD``)들이고
        ``last_run_date`` 가 예매 가능한 마지막 운행일이다. 서버가
        ``tripChgDates`` 를 빼면 빈 튜플이 될 뿐 예외가 아니지만, 리스트 안에
        문자열이 아닌 값이 섞이면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        """
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
        """기프티켓 목록을 두 가지 조회 목적 중 하나로 읽는다.

        ``POST gift.gdLst.do`` (``GifticketService.java:17``). 로그인
        필요. ``request`` 의 타입이 목적을 정한다 —
        :class:`~korail_mobile_api.read_payloads.GiftTicketHistoryRequest`
        는 승차일 구간(``YYYYMMDD``)으로 내역을 읽고,
        :class:`~korail_mobile_api.read_payloads.GiftTicketPaymentEligibilityRequest`
        는 인자 없이 결제 가능 여부만 묻는다(``qryDvCd=F``). 둘 중 정확히
        한 타입이어야 하고 하위 클래스는 거부된다.

        :class:`~korail_mobile_api.read_models.GiftTicketListResponse` 를
        돌려주며, 다음 페이지 키는 ``next_query_no`` 다.

        라이브 미검증 — 시험한 host/version 에서는 이 경로가 404 였다.
        """
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
        """정기권 예매에 필요한 조건을 세 단계 중 하나로 조회한다.

        ``POST research.cmtrInfo.do`` (``ResearchService.java:39``).
        로그인 필요. ``request`` 의 타입이 ``jobDvCd`` 를 정한다 —
        :class:`~korail_mobile_api.read_payloads.CommuterInitialRequest` 가
        ``"a"``(상품 기본조건),
        :class:`~korail_mobile_api.read_payloads.CommuterPassengerRequest`
        가 ``"b"``(연령구분별 인원 확정),
        :class:`~korail_mobile_api.read_payloads.CommuterTicketInquiryRequest`
        가 ``"c"``(기존 정기권 승차권 조회)다. 앞의 둘은
        :meth:`get_commuter_kind_menu` 가 준 ``pass_data`` 를 그대로
        넘긴다.

        :class:`~korail_mobile_api.read_models.CommuterInfoResponse` 를
        돌려준다. ``available_passenger_count_from``/``_to`` 가 허용 인원
        범위, ``passenger_options`` 가 연령구분별 인원 범위이고,
        ``popup_message``/``promotion_message`` 는 화면에 띄울 문구다.

        라이브 미검증.
        """
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
        """열차 한두 편의 운임을 예매 전에 미리 계산해 받는다.

        ``POST trn.prcFare.do`` (``TrainsInfoService.java:24``). 세션 가드가
        없다. ``request`` 는 정확히
        :class:`~korail_mobile_api.read_payloads.PriceFareQuoteRequest` 여야
        하며, ``legs`` 는 한 개(직통) 또는 두 개(환승)다. 그 수가 그대로
        ``chtnDvCd`` 로 나가고, 역코드·운행일·열차번호 같은 값들은 구간별로
        쉼표로 이어 한 칸에 실린다. ``menu_id`` 는 서버값이 아니라 앱이 박아
        놓은 상수 ``"11"`` 이라 기본값 그대로 두면 된다.

        :class:`~korail_mobile_api.read_models.PriceFareQuoteResponse` 를
        돌려주고 ``fares`` 가 운임 항목이다. ``prcList`` 가 없거나 ``null``
        이면 빈 튜플이 될 뿐 예외가 아니다.
        """
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
        """승차권 한 장을 전달받은 수령자 정보를 조회한다.

        ``POST tk.dlvRcvCust.do`` (``TicketService.java:30``). 로그인
        필요. ``ticket`` 은 승차권의 네 부분 자격증명(발권창구번호·발매일·
        발매일련번호·반환비밀번호)이며, 정확히
        :class:`~korail_mobile_api.read_payloads.OriginalTicketReference`
        여야 한다.

        :class:`~korail_mobile_api.read_models.DeliveryRecipientResponse` 를
        돌려준다. 목록이 아니라 단일 객체이고 필드는 모두 선택값이라
        서버가 비워 보내면 ``None`` 이다.

        라이브 미검증.
        """
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
        """같은 PNR 로 이미 잡혀 있는 예약이 몇 건인지 센다.

        ``POST ticket.ticketDupCheck.do`` (``TicketService.java:34``).
        로그인 필요. ``request`` 는 정확히
        :class:`~korail_mobile_api.read_payloads.TicketDuplicationCheckRequest`
        여야 하고 PNR 하나만 싣는다.

        :class:`~korail_mobile_api.read_models.TicketDuplicationCheckResponse`
        를 돌려주며 핵심은 정수 ``reservation_count`` 하나다. 서버가 이
        값을 따옴표 친 숫자로 보내든 숫자로 보내든 양쪽 다 받는다
        (``TicketDuplicationCheckDao.java:27``). ``0`` 은 중복이 없다는
        정상 결과다.

        라이브 미검증.
        """
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
        """승차권 여러 장의 PBP 수락 내역을 여정·좌석 단위로 조회한다.

        ``POST tk.pbpAcepSpec.do`` (``TicketService.java:66``). 로그인
        필요. ``tickets`` 는
        :class:`~korail_mobile_api.read_payloads.OriginalTicketReference`
        튜플이고, 빌더가 장수를 ``tkCnt`` 로 앞에 붙인 뒤 승차권마다
        ``tkRetNo`` 를 반복해 넣는다.

        :class:`~korail_mobile_api.read_models.PbpAcceptanceSpecificationResponse`
        를 돌려준다. 승차권 → 여정(``journeys``) → 좌석(``seats``) 3단
        중첩이고, 좌석의 ``car_no`` 는 정수로 정규화된다
        (``PbpAcepSpecDao.java:102``). 각 단계의 하위 목록은 비어 있어도
        정상이다.

        라이브 미검증.
        """
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
        """승차권 여러 장의 승강장 번호를 여정 단위로 조회한다.

        ``POST tk.plfNo.do`` (``TicketService.java:74``). 로그인 필요.
        ``tickets`` 는
        :class:`~korail_mobile_api.read_payloads.OriginalTicketReference` 튜플이고,
        빌더가 장수를 ``tkCnt`` 로 앞에 붙인 뒤 승차권마다 ``tkRetNo`` 를
        "창구번호-발매일-발매일련번호-반환비밀번호" 로 이어 반복해 넣는다.

        :class:`~korail_mobile_api.read_models.PlatformNumberResponse` 를
        돌려준다. 승차권 → 여정(``journeys``) 2단 중첩이고 승강장 번호는 여정의
        ``platform_no``(``plfNo``)다. ``tkList`` 든 ``jrnyList`` 든 없거나
        ``null`` 이면 빈 튜플이 될 뿐 예외가 아니며, 승강장이 아직 정해지지
        않은 여정은 ``platform_no`` 가 ``None`` 이다.

        라이브 미검증.
        """
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

    def get_original_ticket_inquiry(
        self,
        tickets: tuple[OriginalTicketReference, ...],
        *,
        ticket_count: int | None = None,
    ) -> OriginalTicketInquiryResponse:
        """승차권 변경의 출발점이 되는 원표(원승차권)를 조회한다.

        ``POST research.tripChgOgtk.do`` (``ResearchService.java:61-63``).
        로그인 필요. 승차권 변경 사슬의 첫 읽기다 — 손에 든 승차권들의
        반환번호를 주면 그 승차권의 여정·좌석·운임을 돌려주고, 이후
        단계가 그 값을 키로 삼는다. 날짜 쪽 질문은 형제 라우트인
        :meth:`get_trip_change_dates`(``reservation.tripChgDate.do``)가
        답한다.

        ``ticket_count`` 는 ``tkCnt`` 이며 기본값은 ``len(tickets)``,
        ``PushHistoryActivity.java:357`` 이 보내는 값이다. 앱의 나머지 두
        호출부는 같은 자리에 승객 수(``TCBookingActivity.java:179``)나
        고정값 ``1``(``SeatSearchActivity.java:615``)을 넣기 때문에 인자로
        열어 두었다. 전선에는 정수로 나간다
        (``ResearchService.smali:613,628-632``).

        :class:`~korail_mobile_api.read_models.OriginalTicketInquiryResponse`
        를 돌려준다.

        라이브 미검증 — 요청은 APK 선언과 세 호출부, 응답은
        ``OgTkInquiryDao``/``OrgTk`` 선언이다.
        """
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
        """자율 좌석/열차 변경으로 갈 수 있는 승차역과 변경 사유를 조회한다.

        ``POST self.seatChgInfo.do`` (``TicketService.java:54-56``). 로그인
        필요. 이미 타고 있는 열차를 키로 삼아, 변경으로 옮겨 갈 수 있는 승차역을
        일반실·특실 잔여석과 함께, 그리고 앱이 사용자에게 고르게 하는 변경 사유
        목록을 함께 답한다(``TCSOptionsActivity.java:128-140``).

        ``request`` 의 값은 전부 손에 든 승차권에서 그대로 베낀 것이며, 특히
        ``train_no`` 는 좌석 조회들과 달리 0 을 채우지 않는다.
        :attr:`~korail_mobile_api.read_payloads.SelfSeatChangeInfoRequest.room_class_code`
        는 승차권이 일반실(``"1"``)이나 특실(``"2"``)일 때만 채우고 그 밖에는
        ``None`` 으로 둔다 — 앱도 그때는 필드를 아예 빼고 보낸다.

        :class:`~korail_mobile_api.read_models.SelfSeatChangeInfoResponse` 를
        돌려준다. 역 목록과 사유 목록은 각각 비어 있어도 정상이다.

        라이브 미검증 — 자율 변경이 허용된 열차의 실제 승차권이 있어야 닿는다.
        """
        self._require_session()
        form = build_self_seat_change_info_form(request)
        return self._run_read(
            lambda: parse_self_seat_change_info_response(
                self.http.post_form(
                    "/classes/com.korail.mobile.self.seatChgInfo.do",
                    form,
                    include_dynapath=False,
                ).raw
            )
        )

    def get_recent_delivery_history(self) -> RecentDeliveryHistoryResponse:
        """최근에 승차권을 전달했던 수령자 목록을 조회한다.

        ``POST tk.rcntDlvHst.do`` (``TicketService.java:78``). 로그인 필요.
        인자가 없다 — ``custMgNo`` 는 로그인 응답의 ``strCustNo`` 에서 가져오며,
        그 값이 비어 있으면 세션이 있어도 요청 전에
        :class:`~korail_mobile_api.errors.KorailAuthError` 로 막힌다. 세션 가드가
        두 겹인 셈이다.

        :class:`~korail_mobile_api.read_models.RecentDeliveryHistoryResponse` 를
        돌려주고 ``recipients`` 가 수령자다. 전달 이력이 없으면 빈 튜플이고
        예외가 아니다.

        라이브 미검증.
        """
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
        """홀드된 예약 하나의 여정·좌석 상세를 PNR 로 되읽는다.

        ``GET certification.ReservationList`` 의 읽기 오버로드만 옮겼다
        (``CertificationService.java:45-46``, ``inquiryTicketRsv``). 로그인
        필요. ``request`` 는 PNR 하나만 싣는다.

        같은 경로에 홀드된 예약에 장애인 증명을 적용하는
        ``applyDisabilityCertification``(``:22``)이 같이 있는데 그것은 쓰기라
        옮기지 않았고, ``KORAIL_EXACT_REQUEST_FIELDS`` 가 이 라우트를
        ``Device``/``Version``/``Key``/``hidPnrNo`` 네 칸으로 못박아 두어 더 넓은
        요청 모양은 실수로도 나가지 않는다.

        :class:`~korail_mobile_api.read_models.TicketReservationDetailResponse` 를
        돌려준다. 여정(``jrny_infos``) → 좌석(``seat_infos``) 2단 중첩이고 각
        단계의 하위 목록은 비어 있어도 정상이다. 좌석의 승객유형·실별·할인코드가
        :meth:`recalculate_price` 에 넣을 값이다.
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
        """환불했을 때 돌려받을 금액과 떼일 수수료를 미리 묻는다.

        ``POST refunds.CommissionView`` (``RefundService.java:19-21``).
        로그인 필요. :meth:`refund` 앞에 두는 읽기 전용 사전확인이며 이것을
        불러도 환불되지 않는다.

        ``ticket`` 은 승차권의 네 부분 자격증명이다. 이 폼만은 발매일을
        ``h_orgtk_ret_sale_dt`` 로 쓴다 — 영수증 읽기의 ``h_orgtk_sale_dt`` 와
        철자가 다르다. ``companion`` 은 서버가 되돌려주는 동반자 이름·증명번호로
        :meth:`get_refund_ticket_detail` 응답의
        ``companion_name``/``companion_birth_date`` 에서 가져온다. 동반자가 없는
        승차권은 둘 다 빈 문자열이 정상이며 두 필드는 언제나 전송된다.

        :class:`~korail_mobile_api.read_models.RefundCommissionResponse` 를
        돌려준다. ``refund_amount``(환급액)·``refund_fee``(수수료)·
        ``proceed_possible_flag``(진행 가능)를 보고 :meth:`refund` 를 부를지 정하고,
        ``ticket_return_times_division_code`` 는 :meth:`refund` 가 그대로
        되받는 값이다.
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
        """환불 대상 승차권의 여정·좌석·운임 상세를 조회한다.

        ``POST refunds.SelTicketInfo`` (``RefundService.java:23-25``).
        로그인 필요. 앱은 이 읽기를 :meth:`get_refund_commission` 앞에 둔다 —
        응답의 ``companion_name``/``companion_birth_date`` 가 그 호출의
        ``companion`` 인자가 되기 때문이다
        (``TicketListActivity.java:908-909``).

        ``from_purchase_history=True`` 면 구매이력 화면이 보내는
        ``h_purchase_history="Y"`` 로 나가고, 기본은 승차권 목록 화면과 같은
        ``"N"`` 이다. 이 플래그는 언제나 전송되며 생략되지 않는다.

        :class:`~korail_mobile_api.read_models.RefundTicketDetailResponse` 를
        돌려준다. 여정(``ticket_infos``) → 좌석 2단 중첩이고 하위 목록은 비어
        있어도 정상이다. ``pbp_acceptance_target_flag`` 는 :meth:`refund` 가
        그대로 되받는 값이고, N카드 승차권이면 ``discount_card`` 에 카드번호가
        실려 :meth:`get_discount_card_usage_history` 로 이어진다.
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
        """공통코드 표를 코드 하나만큼 조회한다.

        ``POST common.code.do`` (``CommonService.java:30``). 세션 가드가
        없고 로그인 전에도 부를 수 있다 — 로그인 절차 자체가 비밀번호
        암호화 파라미터를 이 라우트에서 먼저 받아 온다.

        파싱하지 않고 :class:`~korail_mobile_api.models.BaseKorailResponse`
        를 그대로 돌려주므로 코드값은 ``raw`` 에서 직접 꺼낸다. ``code`` 는
        문자열 하나를 받아 ``code=[""]`` 처럼 리스트 한 칸으로 나가고,
        여러 코드를 한 번에 받으려면
        :func:`~korail_mobile_api.payloads.build_common_code_form` 이
        리스트도 받는다.
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
        """앱 메인 화면이 쓰는 캐시 파일을 받아 온다.

        ``GET /file/CACHE/prdMobilePlusMain.cache``
        (``CacheService.java:14``). 세션 가드가 없다. ``timestamp_ms`` 는
        캐시 무효화용 ``timeStamp`` 질의값이고, 생략하면 현재 시각을 쓴다.

        :class:`~korail_mobile_api.models.AppDataResponse` 를 돌려준다.
        캐시 파일이라 KORAIL 봉투(``h_msg_cd``)가 없어 봉투 검사를 끈다.
        ``version`` 이 있으면 앱 업데이트 안내이고, 나머지는 장애인 인증·
        공항버스·레일플러스 카드 안내 문구다. 필드는 모두 선택값이라
        서버가 빼면 ``None`` 이다.
        """
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
        """공지 배너 캐시 파일을 받아 온다.

        ``GET /file/CACHE/prdMobilePlusNotice.cache``
        (``CacheService.java:17``). 세션 가드가 없다. ``timestamp_ms`` 는
        캐시 무효화용 값이고 생략하면 현재 시각을 쓴다.

        :class:`~korail_mobile_api.models.NoticeResponse` 를 돌려준다.
        게시판 ID·글 일련번호·제목 세 값뿐이고 본문은 없다. 띄울 공지가
        없으면 셋 다 ``None`` 이다. 캐시 파일이라 봉투 검사를 끈다.
        """
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
        """서버가 발급하는 단말 검증값 하나를 받아 온다.

        ``GET /ebizcross/getUUID.do`` (``CommonService.java:27``,
        ``ckValue``). 세션 가드가 없고 인자도 없다. 라이브로 성공을 확인한
        경로다.

        :class:`~korail_mobile_api.models.UuidResponse` 를 돌려주며 값은
        ``verification_code``(``mutMrkVrfCd``) 하나다. 필수라서 없거나 빈
        문자열이면 :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        KORAIL 봉투가 없는 응답이라 봉투 검사는 끈다.

        이 클라이언트는 받은 값을 어느 요청에도 되싣지 않는다. 서버가 이것을
        무엇에 쓰는지는 APK 선언만으로는 알 수 없다. 값 자체는
        :data:`~korail_mobile_api.redaction.SENSITIVE_KEYS` 에 등록돼 있어
        미리보기나 로그에 드러나지 않는다.
        """
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
        """역 연계 MaaS 서비스 메뉴와 역 안내 링크들을 조회한다.

        ``POST copt.gdMenuLt.do`` (``CommonService.java:46``). 세션 가드가
        없다. 인자가 없고 폼은 ``Device``/``Version`` 뿐이다.

        :class:`~korail_mobile_api.models.MaasMenuListResponse` 를
        돌려준다. 각 항목의 ``additional_service_code``(``addSrvDvCd``)가
        :meth:`get_maas_station_data` 에 넣을 값이고, ``login_required`` 는
        그 메뉴가 로그인 뒤에만 열리는지를 서버가 알려주는 플래그다.
        ``menuList`` 가 ``null`` 이면 ``items`` 가 빈 튜플이 될 뿐 예외가
        아니다. 출발·도착역의 엘리베이터·주차장·수하물 로봇 URL 은 응답
        최상위에 따로 실린다.
        """
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
        """MaaS 부가서비스 하나가 지원하는 역 목록을 조회한다.

        ``POST /ebizmaas/EbizMaasStationList.do``
        (``CommonService.java:50``). 세션 가드가 없다.
        ``additional_service_code`` 는 :meth:`get_maas_menu_list` 가 준
        ``addSrvDvCd`` 이며 빈 문자열은 거부된다.

        일반 역 목록과 같은
        :class:`~korail_mobile_api.models.StationDataResponse` 를 돌려주고
        각 역은 코드·이름과 위경도를 가진다. 이 라우트는 KORAIL 봉투를
        싣지 않아 봉투 검사를 끄지만 ``stns.stn`` 리스트는 필수라서, 없으면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        """
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
        """역 데이터의 판본과 수록 역 수만 가볍게 확인한다.

        ``GET common.stationinfo`` (``CommonService.java:57``). 세션 가드가
        없다. ``device`` 는 질의값 ``Device`` 이며 기본 ``"AD"``(안드로이드)다.

        :class:`~korail_mobile_api.models.StationInfoResponse` 를 돌려주는데
        역 목록은 들어 있지 않다 — 그것은 :meth:`get_station_data` 몫이고,
        여기서는 ``count``(역 수)와 ``map_version``(지도 판본) 둘뿐이다. 캐시해
        둔 역 목록을 다시 받을지 정할 때 쓴다.

        이 응답에는 KORAIL 봉투가 없어 봉투 검사를 끈다. 대신 두 값이 모두
        필수라서 빠지거나 ``map_version`` 이 빈 문자열이면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        """
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
        """전체 역 목록을 코드·이름·좌표까지 한 번에 받아 온다.

        ``GET common.stationdata`` (``CommonService.java:54``). 세션 가드가
        없고 인자도 없다. 봉투가 없는 응답이라 봉투 검사를 끈다.

        :class:`~korail_mobile_api.models.StationDataResponse` 를 돌려준다.
        역마다 코드(``stn_cd``)와 이름(``stn_nm``)은 필수이고 위경도·그룹·
        팝업 문구는 선택값이다. ``stns.stn`` 리스트가 없으면 빈 목록이 아니라
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다.

        :meth:`search_trains` 에 역이름 대신 역코드를 넘기면 이 조회를 한 번
        불러 이름 대응표를 만들고 클라이언트 안에 캐시한다.
        """
        return self._run_read(
            lambda: parse_station_data_response(
                self.http.get_json(
                    "/classes/com.korail.mobile.common.stationdata",
                    require_envelope=False,
                )
            )
        )

    def get_train_calendar(self) -> TrainCalendarResponse:
        """지금 예매할 수 있는 운행일 달력을 받아 온다.

        ``GET schedule.runDt`` (``CalendarService.java:8``). 세션 가드가 없고
        인자도 없다. 날짜 선택 화면이 열 수 있는 날의 범위가 이 목록이다.

        :class:`~korail_mobile_api.models.TrainCalendarResponse` 를 돌려주고
        ``days`` 가 하루씩의 행이다. ``runningCalendar`` 가 없거나 ``null``
        이면 빈 튜플이 될 뿐 예외가 아니다 — 앱도 그 경우를 빈 달력으로 다룬다
        (``C0805e.java:124``). 리스트가 아닌 값이 오면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다. 행의 날짜
        (``runDt``)도 선택값이라 ``None`` 인 행이 섞일 수 있다.
        """
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
        """한 구간·한 날짜의 직통 열차 한 페이지를 조회한다.

        ``POST seatMovie.ScheduleView`` (``SeatMovieService.java:12``).
        세션 가드가 없어 비로그인으로도 부를 수 있다 — 다만 로그인해 두면
        회원카드번호(``mbCrdNo``)가 폼에 함께 실린다.

        ``query`` 의 역은 역코드와 역이름 둘 다 받는다. 코드를 주면
        :meth:`get_station_data` 를 한 번 불러 이름으로 바꾼다. 날짜는
        ``YYYYMMDD``, 시각은 ``HHMMSS`` 이며 그 시각 이후 열차를 준다.

        :class:`~korail_mobile_api.models.TrainSearchResult` 를 돌려주고
        ``trains`` 가 그 페이지의 행이다. 조건에 맞는 직통 열차가 없으면 빈
        목록이 아니라 :class:`~korail_mobile_api.errors.KorailNoDirectTrainError`
        가 된다 — 그때 환승으로 넘어가려면
        :meth:`search_trains_with_transfer_fallback` 을 쓴다.

        다음 페이지는 ``continuation=previous.next_page()`` 로 요청한다. 앱도
        같은 방식으로 앞 응답의 커서를 ``qryStNo``/``qryStTrnNo``/``pgPrCnt``
        에 되싣는다(``b5/c.java:184-194``). 서버가 ``h_next_pg_flg="Y"`` 를
        멈추면 ``next_page()`` 가 ``None`` 이고 그것이 앱의 종료 조건이다.
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
        """같은 질의를 환승 여정으로 바꿔 한 페이지 조회한다.

        엔드포인트도 폼도 :meth:`search_trains` 와 같고 한 칸만 다르다 —
        ``radJobId`` 가 ``"1"`` 대신
        :data:`~korail_mobile_api.KORAIL_TRANSFER_ITINERARY_CODE`(``"2"``)다.
        앱의 환승 조회도 그것이 전부다(``DirectInquiryActivity.java:284-296``).
        세션 가드가 없다.

        응답 모양은 달라지지 않는다. 같은 평평한 ``trn_infos.trn_info`` 목록이고
        구간은 위치로 짝지어진다 — 0·1 행이 한 여정, 2·3 행이 다음 여정이다
        (``a5/k.java:156-170``, ``:108-110``).
        :attr:`~korail_mobile_api.TransferSearchResult.itineraries` 가 그
        짝짓기이고 :attr:`~korail_mobile_api.TransferSearchResult.trains` 가
        원본 목록이다.

        페이지 넘기기도 되지만 커서가 다르다 —
        :meth:`TransferSearchResult.next_page
        <korail_mobile_api.TransferSearchResult.next_page>` 결과를
        ``continuation`` 으로 되먹인다.

        상태를 바꾸는 것은 아무것도 보내지 않는 읽기다. 라이브 미검증 —
        직통이 없는 구간 조합이 있어야 닿는다.
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
        """직통을 찾고, 하나도 없을 때만 환승으로 한 번 더 찾는다.

        여기서 지어낸 편의기능이 아니라 앱의 흐름 그대로다. 직통 조회가 아무것도
        못 찾으면 서버가 ``WRD000061``("직통열차가 없습니다")로 답하는데,
        ``DirectInquiryActivity.java:615-624`` 는 오직 그 코드만 잡아 확인 창을
        띄우고, 확인을 누르면 ``:284-296`` 이 ``radJobId="2"`` 로 다시 질의해
        환승 화면으로 넘긴다.

        이 클라이언트는 ``WRD000061`` 을
        :class:`~korail_mobile_api.KorailNoDirectTrainError` 로 분류하므로
        되돌리는 조건은 그 예외 하나뿐이고 다른 실패는 그대로 올라간다.

        어느 쪽이 일어났는지는 반환 타입이 말해 준다 —
        :class:`~korail_mobile_api.TrainSearchResult` 면 직통 조회가 성공한
        것이고, :class:`~korail_mobile_api.TransferSearchResult` 면 직통이 없어서
        받아 온 환승 대안이다. 한쪽만 무조건 원하면 :meth:`search_trains` 나
        :meth:`search_transfer_trains` 를 직접 부른다.

        ``continuation`` 은 직통 조회에만 전달한다. 커서는 그것을 만든 조회에
        묶인 값이라 환승 질의에 되싣으면 엉뚱한 자리에서 시작하므로, 되돌린
        환승 조회는 언제나 첫 페이지부터다.
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
        """열차 한 편이 하루 동안 서는 정차역과 지연 상황을 조회한다.

        ``POST research.actualTrainSchedule.do``
        (``TrainsInfoService.java:40``). 세션 가드가 없다. ``run_date`` 는
        운행일 ``YYYYMMDD``, ``train_no`` 는 열차번호이며 빌더가 5자리로 0 을
        채운다. 이 폼은 공통 ``Key`` 를 싣지 않고 ``Device``/``Version``/
        ``runDt``/``trnNo`` 네 칸뿐이다.

        :class:`~korail_mobile_api.models.TrainScheduleResponse` 를 돌려주고
        ``stops`` 가 정차역이다. 역이름은 필수이고 실제·예정 도착·출발 시각과
        지연 분은 선택값이라 아직 지나지 않은 역은 ``None`` 이다. ``dlayList``
        자체는 필수라서 없으면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        """
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
        """한 구간에서 환승할 수 있는 역들을 조회한다.

        ``POST qry.chtnStn.do`` (``TrainsInfoService.java:32``). 세션 가드가
        없다. 두 인자는 ``dptRsStnCd``/``arvRsStnCd`` 로 그대로 나가는 역코드이며
        역이름이 아니다.

        :class:`~korail_mobile_api.models.TransferStationListResponse` 를
        돌려주고 ``stations`` 의 각 역은 코드와 이름을 모두 가진다(둘 다
        필수다). 빈 리스트는 그 구간에 환승역이 없다는 정상 결과이지만,
        ``chtnList`` 키 자체가 없으면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        """
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
        """로그인 계정의 승차권 목록을 파싱하지 않은 봉투로 돌려준다.

        ``POST myTicket.MyTicketList`` (``MyTicketService.java:16``). 로그인
        필요 — 세션이 없으면 :class:`~korail_mobile_api.errors.KorailAuthError`
        다.

        전용 파싱 모델이 없다. :class:`~korail_mobile_api.models.BaseKorailResponse`
        를 그대로 돌려주므로 승차권 행은 ``raw`` 에서 직접 꺼낸다. 승차권이 한
        장도 없어도 빈 목록을 만드는 대신 서버 응답을 있는 그대로 넘긴다.

        ``mode`` 는 페이지 커서가 아니라 목록 종류다 — ``"1"`` 은 현재 승차권
        (``TicketListActivity.java:937-939``), ``"2"`` 는 구매이력
        (``TicketPurchaseHistoryActivity.java:276-278``)이고 그 밖의 값은
        거부된다. ``"2"`` 는 ``boarding_date_from``·``boarding_date_to`` 를 둘
        다 ``YYYYMMDD`` 로 요구하며 한쪽이라도 비면 요청을 만들기 전에 막는다.
        ``"1"`` 은 두 값을 빈 문자열로 보낸다.

        ``page_no`` 는 ``h_page_no`` 로 나가고 1 미만은 1 로 올려 보내므로 기본값
        ``0`` 도 첫 페이지를 뜻한다.
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
        """열차 한 편에 결제 전 예약을 잡는다. consent 게이트가 있다.

        ``POST certification.TicketReservation``.
        ``require_mutation_consent(consent, "reserve")`` 와 로그인 세션을
        요구한다. 기본 :class:`MutationConsent`(``allow_reserve=False``)나
        ``None`` 은 폼을 만들기도 전에
        :class:`KorailMutationNotAllowedError` 로 거절된다.

        ``consent.dry_run`` 이 참이면(기본) ``train`` 을 검증하고 실제로 나갈
        폼을 담은 :class:`MutationPreview` 를 돌려줄 뿐 네트워크를 건드리지
        않는다. 거짓이면 이중 게이트 전송로로 홀드를 걸고 파싱한
        :class:`ReservationHoldResponse` 를 돌려준다. 그 ``pnr_no`` 가
        :meth:`cancel_unpaid_hold` 의 입력이다 — 살아 있는 홀드는 미결제
        예약이고 취소하든 결제하든 호출자 책임이다.

        ``passengers`` 는 :class:`KorailPassengerCounts`(기본 성인 1명),
        ``seat_class`` 는 :class:`KorailSeatClass`(기본 일반실)다. 라이브
        서버가 받아들이는 것이 확인된 조합은 성인 1명·일반실 하나뿐이고,
        여러 명이나 특실 홀드는 앱의 요청 빌더에서 그대로 왔을 뿐 미검증이다.

        ``job_type`` 은 :class:`KorailReservationJobType` 이고 기본이
        ``IMMEDIATE``(``txtJobId="1101"``)다.

        * ``SEAT_DESIGNATED``(``"1103"``)는 좌석지정 예매라 ``seats`` 가
          필요하다 — 승객 한 명당 정확히 하나의
          :class:`KorailSeatAssignment` 를 :meth:`get_seat_cars` 와
          :meth:`get_seat_inventory` 에서 골라 넘긴다. 수가 승객 총원과 맞지
          않으면 요청을 만들기 전에 거절한다.
        * ``STANDBY``(``"1102"``)는 예약대기이고, 검색 행이 대기 가능이라고
          말한 열차에만 붙는다. 회원 전용이다
          (``ReservationRequest.java:105-119``) — 이 클라이언트는 모든 상태
          변경이 로그인 세션을 요구하므로 구조적으로 그 조건을 만족한다.
          성공한 대기 홀드는 ``h_msg_cd`` 가
          :data:`~korail_mobile_api.KORAIL_STANDBY_HOLD_MESSAGE_CODE`
          (``IRR000014``)로 오고, :meth:`confirm_standby_hold` 로 알림 옵션을
          기록해야 비로소 끝난다.

        기본이 아닌 ``job_type`` 은 아직 전송된 적이 없다.

        폼이 옳아도 서버가 계정 자격을 이유로 거절할 때가 있다. 청소년 단독
        예약과 1~3급 장애 + 안내견 조합에서 ``ERR299943``("예약할인이 지원되지
        않습니다")이 온 관측이 있고, 이 코드는
        :class:`~korail_mobile_api.errors.KorailNotEntitledError` 로 분류된다.
        요청이 잘못된 것이 아니라 이 계정이 그 운임을 살 수 없다는 뜻이므로
        같은 폼을 다시 보낼 이유가 없다.
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
        """예약대기 홀드에 대기 옵션을 기록한다. consent 게이트가 있다.

        예약대기는 호출 두 번이다. ``job_type=STANDBY`` 로 부른
        :meth:`reserve` 가 PNR 을 만들고 ``h_msg_cd`` = ``IRR000014`` 를
        돌려주는데, 앱은 이 코드에서만 예약대기 화면을 연다
        (``ui/inquiry/rir/orr/a.java:222-225``). 그 화면이 사용자의 선택을
        실어 보내는 두 번째 POST 가 이 메서드다 —
        ``reservationWait.ReservationWait``
        (``ReservationWaitService.java:10-12``).

        ``require_mutation_consent(consent, "reserve")`` 와 로그인 세션을
        요구하고, 다른 모든 상태 변경과 같은 이중 게이트 전송로로 나간다.
        이미 있는 PNR 의 예약을 마무리할 뿐 돈을 옮기지도 좌석을 놓지도
        않으므로 소비 범주가 ``"reserve"`` 다.

        ``allow_seat_class_change`` 는 ``txtPsrmClChgFlg``(배정 때 다른
        실별에 앉혀도 되는지), ``sms_notify`` 는 ``txtSmsSndFlg`` 이고 둘
        다 앱 화면이 열릴 때의 해제 상태가 기본이다. ``phone_no`` 는
        ``sms_notify`` 가 참일 때만 허용되고, 그때는 반드시 필요하다.

        ``consent.dry_run`` 이 참이면(기본) 아무것도 보내지 않고 PNR·전화
        번호를 가린 :class:`MutationPreview` 를 돌려준다.

        라이브 미검증.
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
        """환승 여정 하나를 두 구간·한 PNR 로 홀드한다. consent 게이트가 있다.

        라우트도 consent 범주도 세션 요구도 :meth:`reserve` 와 같다. 앱도
        엔드포인트와 요청 빌더를 하나만 쓰고 구간 수만 폼을 바꾼다
        (``C5/a.java:52-119``). consent·``dry_run``·돌려주는 홀드에 대해
        :meth:`reserve` 가 말한 것이 그대로 적용된다.

        ``legs`` 는 탑승 순서대로 정확히 두 개의
        :class:`~korail_mobile_api.TrainSummary` 여야 하고,
        :meth:`search_transfer_trains` 가 준
        :attr:`TransferItinerary.legs
        <korail_mobile_api.TransferItinerary.legs>` 가 그것이다. 다른 개수는
        폼을 만들기 전에 거절한다
        (:data:`~korail_mobile_api.KORAIL_MAX_JOURNEY_LEGS`).

        ``seat_classes`` 는 두 구간에 하나를 주거나 구간마다 하나를 준다 —
        앱의 실별 선택이 구간별이다(``C5/a.java:59``, ``:97``). ``seats`` 도
        마찬가지로 구간마다 한 묶음이다(``C5/a.java:120-133``).

        ``job_type=STANDBY`` 는 거절한다. 환승 여정에는 예약대기가 없다 —
        ``a5/k.java:120-127`` 이 직통이 아닌 결과에 대해 대기 가능 검사를
        거짓으로 돌려주고, 앱의 유일한 ``txtJobId="1102"`` 는 직통 화면에만
        있다(``DirectInquiryActivity.java:434``).

        라이브 미검증 — 환승 홀드를 KORAIL 에 보낸 적이 없다. 다만
        :meth:`cancel_unpaid_hold` 는 이 홀드도 푼다. 여정 수를 1 로 박지 않고
        홀드 자신의 값을 실어 보내기 때문이다.
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
        """한 열차를 중간역에서 나눈 병합예약을 홀드한다. consent 게이트가 있다.

        병합 흐름의 두 번째이자 마지막 홀드다. 첫 번째는
        ``job_type=KorailReservationJobType.MERGE_STANDING``(``"1202"``,
        입석+좌석 예매)으로 부르는 :meth:`reserve` 이고 그것이 전 구간을
        입석으로 잡는다. 이 메서드가 그것을 같은 열차의 두 여정 예약으로
        바꾸는데, 나누는 지점은 :meth:`get_merge_seats_inquiry` 가 알려준
        중간역이다. 다섯 단계 전체와 그 근거는
        :data:`~korail_mobile_api.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE` 에
        적혀 있다.

        라우트·consent 범주·세션 요구는 :meth:`reserve` 와 같다. 병합예약도
        예약이고 돈을 옮기지 않으므로 범주가 ``"reserve"`` 다.

        ``standing_hold_train`` 은 ``"1202"`` 홀드를 붙인 직통 행이며 검증용만이
        아니다 — 앱의 병합 폼이 그 행의 도착시각을 ``arvTm_1`` 로 싣는다
        (:func:`~korail_mobile_api.mutation_payloads.build_merge_reservation_form`).
        ``legs`` 는
        :attr:`MergeSeatsInquiryResponse.trains
        <korail_mobile_api.MergeSeatsInquiryResponse.trains>` 의 두 행을 순서대로
        준다.

        입석 홀드를 대신 취소하지는 않는다. 앱은 다시 예약하기 전에 그것을
        취소하지만(``DirectInquiryActivity.java:227-250``), 여기서는 ``"cancel"``
        consent 아래의 :meth:`cancel_unpaid_hold` 로 호출자가 직접 한다 —
        ``"reserve"`` 동의만 받고 살아 있는 PNR 을 조용히 취소하는 것은 이
        게이트들이 막으려는 범주 혼동 그 자체다.

        전송된 적이 없다. 여기서 만든 병합 폼이 KORAIL 에 나간 적은 없다.
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
        """결제 전 예약 홀드를 취소한다. 여정이 몇 개든 상관없다.

        ``require_mutation_consent(consent, "cancel")`` 와 로그인 세션을
        요구한다. ``build_unpaid_reservation_cancel_form`` 은 ``hold`` 가
        PNR 을 가진 성공(``SUCC``) 홀드일 것을 요구하고, ``txtJrnyCnt`` 에
        1 을 박는 대신 그 홀드 자신의 여정 수를 그대로 실어 보낸다. 환승
        홀드는 여정이 둘이고 병합 홀드는 그보다 많을 수 있어서, 여기서
        거절하면 살아 있는 예약을 풀 방법이 없어지기 때문이다. 그래서
        :meth:`reserve`, :meth:`reserve_transfer`, :meth:`reserve_merge` 가
        만든 홀드를 모두 이 하나로 푼다.

        ``consent.dry_run`` 이 참이면 PNR 을 가린 :class:`MutationPreview`
        를, 거짓이면 이중 게이트 전송로로 POST 한 뒤 파싱한 봉투를
        돌려준다.

        앱의 취소 호출 두 개 중 뒤쪽(``ReservationCancelChk``)만 보낸다.
        앞의 ``ReservationCancel`` 을 생략해도 취소가 성립하는 것은 라이브로
        확인했다.
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
        """미결제 홀드를 비과금 시험카드로 결제 시도한다. consent 게이트가 있다.

        ``require_mutation_consent(consent, "payment")`` 와 로그인 세션에 더해
        ``consent.fake_card_only`` 가 참이어야 한다. KORAIL 결제 호출은 카드번호를
        평문으로 싣기 때문에, ``card`` 는 PG 가 거절할 비과금 시험카드여야 한다.

        ``consent.dry_run`` 이 참이면 카드·신원 필드를 가린
        :class:`MutationPreview` 를 돌려주고 아무것도 보내지 않는다. 거짓이면
        이중 게이트 전송로로 POST 하고 파싱한
        :class:`ReservationPaymentResponse` 를 돌려준다.

        거절에 예외를 던지지 않는다(``raise_on_fail=False``). 시험카드는 거절이
        정상 결과이고, 호출자가 거절 코드를 직접 봐야 하기 때문이다. 거절돼도
        홀드는 미결제로 남으므로 :meth:`cancel_unpaid_hold` 로 푼다.

        실제로 청구되는 카드를 쓰려면 :meth:`pay_with_card` 다.
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
        """미결제 홀드를 실제 청구되는 카드로 결제한다. consent 게이트가 있다.

        ``require_mutation_consent(consent, "payment")`` 와 로그인 세션에 더해
        ``consent.real_card_acknowledged`` 가 참이고 ``consent.fake_card_only``
        가 거짓이어야 한다. 두 조건을 모두 적어야 한다 — 실제 청구를 인정하면서
        시험카드라고 주장하는 consent 는 모순이라 여기서도, 전송 게이트에서도
        거절한다. 기본 :class:`MutationConsent` 는 어느 쪽도 만족하지 않는다.

        전선 모양은 :meth:`pay_with_fake_card` 와 같다. 둘 다 같은
        ``build_card_payment_form`` 을 만들고 같은 이중 게이트
        :meth:`~korail_mobile_api.http.KorailHttpClient.post_mutation_form` 으로
        나가므로, 실제 결제가 라이브로 검증된 모양에서 벗어날 수 없다. 다른
        것은 어느 consent 를 받느냐뿐이다.

        ``consent.dry_run`` 이 참이면 카드·신원을 가린
        :class:`MutationPreview` 만 돌려주고 아무것도 전송하지 않는다.

        형제 메서드와 마찬가지로 거절에 예외를 던지지 않지만 이유는 다르다.
        가짜 카드는 거절이 예상된 결과이고, 실제 카드는 그렇지 않다. 응답 코드가
        "거절됐고 홀드는 미결제니 취소하면 된다"와 "결과가 모호하니 함부로
        취소하면 안 된다"를 가르는 유일한 기록이며 돈에 무슨 일이 있었는지의
        유일한 근거다. 그래서 파싱한 :class:`ReservationPaymentResponse` 를 늘
        돌려주고 판단은 호출자가 한다 — 결제됐다고 단정하기 전에
        ``str_result``/``h_msg_cd`` 를 확인하라.
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
        """결제까지 끝난 승차권을 환불한다. consent 게이트가 있다.

        ``POST refunds.RefundsRequest``.
        ``require_mutation_consent(consent, "refund")`` 와 로그인 세션을
        요구한다. ``ticket`` 은
        :class:`~korail_mobile_api.mutation_models.PaidTicket`(PNR + 원발매
        자격증명 + 반환비밀번호)이어야 한다. ``consent.dry_run`` 이 참이면
        승차권 신원을 가린 :class:`MutationPreview` 를, 거짓이면 이중 게이트
        전송로로 POST 한 뒤 파싱한 봉투를 돌려준다.

        세 인자는 고정값을 넣는 자리가 아니라 서버가 방금 말해 준 값을 되돌려
        주는 자리다. 앱과 같은 폼을 보내려면 그 값을 실은 두 읽기를 먼저 사슬로
        부른다:

        1. :meth:`get_refund_ticket_detail` →
           :attr:`RefundTicketDetailResponse.pbp_acceptance_target_flag`
        2. :meth:`get_refund_commission` →
           ``ticket_return_times_division_code`` (출발 전 ``"21"``, 출발 후
           ``"15"``)

        ``settle_mileage`` 만은 되받는 값이 아니라 호출자의 결정이다 — 앱은
        마일리지 정산이 가능하고 사용 가능 잔액이 수수료를 덮을 때만 켠다. 셋을
        모두 생략하면 ``"21"``/``"N"``/``"N"`` 이 나가는데, 출발 전·마일리지
        미사용·PBP 아님인 환불에만 맞다.

        이 패키지의 가짜카드 결제는 언제나 거절되므로 라이브로 결제된 승차권이
        만들어지지 않는다. 전송로는 있지만 오프라인으로만 시험했다.
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

    def add_to_cart(
        self,
        request: CartAddRequest,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | BaseKorailResponse:
        """홀드 중인 예약의 PNR 을 장바구니에 담는다. consent 게이트가 있다.

        ``POST cart.addCartList`` (``CartService.java:11-13``). 공통 세
        필드 말고 요청 필드는 ``hidPnrNo`` 하나뿐이다
        (``AddCartDao.java:9-24``, smali 로 교차 확인).

        ``require_mutation_consent(consent, "cart")`` 와 로그인 세션을
        요구한다. ``"cart"`` 는 ``"reserve"`` 를 돌려 쓴 것이 아니라 독립
        범주다 — 대상 홀드는 이미 존재하고, 이 라우트는 이 패키지가 관측할
        수 있는 무엇도 만들거나 없애지 않으며, 카드번호를 싣지 않아
        :data:`~korail_mobile_api.safety.KORAIL_CARD_BEARING_MUTATION_CATEGORIES`
        에서 일부러 빠져 있다.

        ``consent.dry_run`` 이 참이면(기본) 폼을 만들어 검증만 하고
        :class:`~korail_mobile_api.consent.MutationPreview` 를 돌려준다.
        ``hidPnrNo`` 는 :data:`~korail_mobile_api.redaction.SENSITIVE_KEYS`
        에 등록돼 있어 미리보기에 PNR 이 드러나지 않는다.

        DAO 의 응답 타입이 맨 ``BaseResponse``(``CartService.java:13``)라
        성공했을 때 무엇이 오는지는 알 수 없다. 라이브 미검증이고, 이
        저장소에 실제로 보내는 경로도 없다.
        """
        require_mutation_consent(consent, "cart")
        if self.session.current is None:
            raise KorailAuthError(
                "KORAIL cart add requires an authenticated session"
            )
        route = "/classes/com.korail.mobile.cart.addCartList"
        form = build_cart_add_form(self.config, request)
        if consent.dry_run:
            return MutationPreview(
                category="cart",
                method="POST",
                route=route,
                payload=form,
            )
        try:
            return self.http.post_mutation_form(
                route, form, consent=consent, category="cart"
            )
        except KorailSessionExpiredError:
            self.clear_session()
            raise

    def register_discount_card(
        self,
        request: DiscountCardPurchaseRequest,
        *,
        consent: MutationConsent,
    ) -> MutationPreview | DiscountCardPurchaseResponse:
        """할인카드(N카드)를 구매한다. consent 게이트가 있다.

        ``POST research.dcntCrdInfo.do`` (``ResearchService.java:68-70``).
        경로에 "Info" 가 붙어 있지만 조회가 아니라 구매다 — 응답이
        ``lumpStlTgtNo`` 와 ``rcvdAmt`` 를 주고
        (``NCardReservationDao.java:127-134``) 앱은 그 대상번호를 결제 화면으로
        그대로 넘긴다(``SectionNCardInquiryActivity.java:213-257``). 만들어지는
        것은 결제를 기다리는 미결제 구매다.

        ``require_mutation_consent(consent, "discount_card")`` 와 로그인 세션을
        요구한다. ``"discount_card"`` 는 ``"reserve"`` 를 돌려 쓴 것이 아니라
        독립 범주다 — 열차 예약에 동의한 사람이 상품 구매에도 동의한 것은
        아니다. ``consent.dry_run`` 이 참이면(기본) 폼을 만들어 검증만 하고 가린
        :class:`~korail_mobile_api.consent.MutationPreview` 를 돌려주며 아무것도
        보내지 않는다.

        확인된 것: 라우트, 메서드, 네 개의 스칼라 필드명, 두 개의 ``@FieldMap``
        키 철자 — 모두 DAO 에서 왔다.

        확인되지 않은 것: v6.5.0 어디에도 ``jrnyInfo``/``apdUsrInfo`` 를 채우는
        호출부가 없고 채울 수 있는 setter 만 있다. 그래서 1구간 카드도 구간을
        실어야 하는지, 1인용 카드가 ``apdUsrCnt`` 를 ``"0"`` 으로 보내야 하는지
        빼야 하는지 알 수 없다. 라이브로 부르기 전에 운영자가 직접 확인해야 한다.
        전송된 적이 없고 이 저장소에 보내는 경로도 없다.
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
        """할인카드의 유효기간을 연장한다(기간연장). consent 게이트가 있다.

        ``GET reservation.dcntCrdExtn.do`` (``ResearchService.java:65-66``)
        — 앱이 GET 으로 수행하는 상태 변경이라 여기서도 GET 그대로
        등록했고, ``post_mutation_form`` 과 같은 게이트를 모두 갖춘
        :meth:`~korail_mobile_api.http.KorailHttpClient.get_mutation_query`
        로 나간다. ``require_mutation_consent(consent, "discount_card")`` 와
        로그인 세션을 요구하며, ``consent.dry_run`` 이 참이면(기본)
        :class:`MutationPreview` 만 돌려주고 아무것도 보내지 않는다.

        ``ticket`` 은 카드 승차권 자신의 네 부분 자격증명이고,
        ``TicketListActivity.java:1067-1072`` 가 N카드 행에서 읽어 오는
        값이다. 부르기 전에
        :attr:`~korail_mobile_api.read_models.DiscountCardOnTicket.term_extension_possible_flag`
        를 확인하라 — 앱은 이 값이 ``"Y"`` 일 때만 기간연장 버튼을 켠다
        (``Y4/C0907b.java:301`` → ``Y4/Q.java:1013-1026``). 카드의 성질이지
        요청의 성질이 아니라서 빌더는 이 조건을 중복 검사하지 않는다.

        DAO 의 응답 타입이 맨 ``BaseResponse``(``ResearchService.java:65``)
        라 성공했을 때 무엇이 오는지, 비용이 드는지 알 수 없다. 라이브
        미검증이고 보내는 경로도 없다.
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
        """할인카드(N카드)로 좌석 하나를 홀드한다. consent 게이트가 있다.

        라우트도 범주도 게이트도 :meth:`reserve` 와 같다. 같은 호출이기
        때문이다 — ``w4/a.java:93-104`` 이 평범한 ``ReservationRequest`` 를
        만들고 ``c5/b.java:128-138`` 이 평범한 ``ReservationDao`` 로
        ``certification.TicketReservation`` 에 보낸다. N카드 전용 예약
        엔드포인트는 없고 N카드 승객 블록이 있을 뿐이다. 그래서
        ``require_mutation_consent(consent, "reserve")`` 다 — 할인카드를 쓴다고
        예약이 예약 아닌 것이 되지 않고, 좌석 홀드에 동의하지 않은 호출자가 이
        길로 홀드해서도 안 된다.

        ``card_no`` 는 N카드 승차권 상세(:meth:`get_refund_ticket_detail`)의
        :attr:`~korail_mobile_api.read_models.DiscountCardOnTicket.card_no` 다.
        ``train`` 은 :meth:`get_discount_card_schedule` 이 준 행이어야 한다 —
        그 카드가 실제로 커버하는 열차를 아는 조회가 그것뿐이다.

        ``passengers`` 도 ``seat_class`` 도 인자로 없다. 앱이 승객 1명을 박고
        (``w4/a.java:97-98``) 실별을 일반실로 고정하기(``:88``) 때문이다.

        전송된 적이 없다. APK 에서만 끌어낸 예약 표면이다. 확인된 것은 라우트,
        평범한 홀드와 다른 두 필드(``txtDiscKndCd1="153"``, ``txtCardNo_1``),
        ``txtMenuId="A2"``, 그리고 나머지가 라이브 검증된 성인 1명 경로와 바이트
        단위로 같다는 것이다. 서버가 받아들이는지, 만료·소진·남의 카드에 무엇을
        답하는지는 모른다. 첫 라이브 호출은 실험으로 다루고
        :meth:`cancel_unpaid_hold` 로 홀드를 풀 준비를 해 두라.
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
        """홀드된 PNR 의 운임을 다른 할인 조합으로 다시 계산한다. consent 게이트가 있다.

        ``POST certification.PriceReCalculation``
        (``CertificationService.java:35-37``, ``getDiscountPrice``). 앱은 이미
        존재하는 예약의 할인 선택이 바뀔 때마다 결제 화면에서 이것을 쏘고
        (``a6/C1042B.java:265-296``), 응답은 홀드가 돌려주는 것과 같은
        ``ReservationResponse`` 다 — 그래서 돌아오는 것은 다시 계산된 예약이고
        :attr:`ReservationHoldResponse.received_amount` 가 새로 정산될 금액이다.

        ``require_mutation_consent(consent, "price_recalculation")`` 와 로그인
        세션을 요구한다. 이 범주는 독립이고 특히 ``"payment"`` 가 아니다 —
        결제 동의는 이미 제시된 금액을 정산하도록 허락하는 것이고, 이 호출은 그
        제시 금액 자체를 다시 쓴다. ``consent.dry_run`` 이 참이면(기본) 폼을
        만들어 검증만 하고 가린
        :class:`~korail_mobile_api.consent.MutationPreview` 를 돌려주며 아무것도
        보내지 않는다.

        ``request.rows`` 는 여정의 좌석 하나당
        :class:`~korail_mobile_api.mutation_models.PriceRecalculationRow` 하나를
        좌석 순서대로 담아야 한다 — ``passenger_type_code``/``room_class_code``
        와 좌석의 기존 할인코드는 같은 PNR 을 읽는
        :meth:`get_ticket_reservation_detail` 에서 가져온다.

        :meth:`reserve` 의 관대한 홀드 복구 파싱은 쓰지 않는다. 그 장치는 서버가
        이미 만든 홀드를 엄격한 파싱 실패로 잃지 않으려는 것인데, 여기서는
        만들어지는 것이 없으므로 망가진 응답은 그냥 예외가 된다.

        APK 에서 확인한 것: 라우트, 메서드, ``@Field`` 이름 열넷, 여섯 리스트의
        인덱스 정렬, 반복 키 인코딩 — 마지막 것은 jadx 가 아니라
        ``smali/a6.1/B.smali`` 와 ``RequestBuilder.smali`` 로 확인했다.

        확인되지 않은 것: 서버가 이것으로 무엇을 하는지. 전송된 적이 없고 라이브
        시험 경로도 없다. 실제 홀드에 보내면 승객이 곧 청구받을 금액이 바뀌므로,
        운영자는 다시 계산돼도 좋은 홀드에 대고 직접 확인해야 한다.
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

