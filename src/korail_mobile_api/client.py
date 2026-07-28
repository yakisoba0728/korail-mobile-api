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
        """List the stations and reasons a 자율 좌석/열차 변경 allows.

        ``POST self.seatChgInfo.do`` (``TicketService.java:54-56``). Keyed by
        the train the ticket is already on, it answers with the boarding
        stations the change may move to -- each with its 일반실/특실
        remaining-seat count -- and the 변경 사유 list the app puts in front of
        the user (``TCSOptionsActivity.java:128-140``).

        Leave
        :attr:`~korail_mobile_api.read_payloads.SelfSeatChangeInfoRequest.room_class_code`
        as ``None`` unless the ticket is 일반실 (``"1"``) or 특실 (``"2"``);
        the app omits the field entirely for any other class.

        **NOT LIVE-VERIFIED.** Reaching this route needs a live ticket on a
        train that permits a self seat change.
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
        with :class:`KorailMutationNotAllowedError` before anything is built. Requires
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

