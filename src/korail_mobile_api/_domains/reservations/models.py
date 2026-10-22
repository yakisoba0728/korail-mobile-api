# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예약·예약 내역·장바구니 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ...errors import KorailApiError
from ..common.models import BaseKorailResponse


@dataclass(frozen=True)
class ReservationPassengerInfo:
    """예약 응답의 승객 유형별 인원과 할인 정보를 담습니다."""

    passenger_type_code: str | None = None
    passenger_count: str | None = None
    discount_kind_code: str | None = None
    discount_kind_code_2: str | None = None
    discount_proof_no: str | None = None
    discount_proof_no_2: str | None = None
    delay_original_window_no: str | None = None
    delay_original_sale_date: str | None = None
    delay_original_sale_sequence: str | None = None
    delay_original_return_password: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class CartItem:
    """장바구니의 열차·공항버스 예약 또는 부가서비스 한 행을 담습니다."""

    service_code: str | None = None
    provider_name: str | None = None
    product_name: str | None = None
    item_type: str | None = None
    departure_date: str | None = None
    received_amount: str | None = None
    reservation_received_date: str | None = None
    # h_tk_cnt — CartInfo.java:51 의 선언은 String 이고 이 DTO 는 kotlinx 이므로 문자열로 둡니다.
    #: 승차권 매수(``h_tk_cnt``)입니다. 서버가 정수로 보내도 문자열로 담습니다.
    ticket_count: str | None = None
    usage_start_date: str | None = None
    usage_start_time: str | None = None
    usage_close_time: str | None = None
    partner_reservation_no: str | None = None
    pnr_no: str | None = None
    lump_sum_target_no: str | None = None
    customer_no: str | None = None
    virtual_reservation_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # CartInfo.java:28-61,281-392의 문자열은 읽고 중첩 결제 상세 6객체는 raw에 보존합니다. 보호 리터럴은 미확인입니다.
    item_type_code: str | None = None
    # h_add_srv_mrk_ent_id: CartInfo.java:31, @SerialName 289행. provider_name 은 h_add_srv_mrk_ent_nm(CartInfo.java:32)입니다.
    #: 부가서비스 제공 업체 ID(``h_add_srv_mrk_ent_id``)입니다. 업체 이름은 ``provider_name``에 있습니다.
    provider_id: str | None = None
    # CartInfo.java:40,41,42, @SerialName 325/329/333행.
    #: 이 행의 항목 일련번호(``h_item_sqno``)입니다.
    item_sequence: str | None = None
    #: 여정 일련번호(``h_jrny_sqno``)입니다.
    journey_sequence: str | None = None
    #: 여정 구분 코드(``h_jrny_tp_cd``)입니다.
    journey_type_code: str | None = None
    # utlClsDt: CartInfo.java:56, @SerialName 377행. 앱도 둘을 이어 붙여 한 일시로 씁니다(PayTicketContentKt.java:5234:
    # getUtlClsDt() + getUtlClsTm()).
    #: 이용 종료 날짜(``utlClsDt``)입니다. ``usage_close_time``과 이어 붙이면 이용 종료 일시가 됩니다.
    usage_close_date: str | None = None
    # h_stl_lmt_tm: CartInfo.java:49,361. 앱은 MaaS 전용 분기에서 행을 고른 뒤 남은 시간을 계산합니다
    # (PayViewModel.java:11658-11679, DateTimeExKt.java:407-431).
    #: 결제 기한(``h_stl_lmt_tm``)입니다. 그 자체로 기한을 나타내는 문자열입니다.
    settlement_limit_time: str | None = None
    # 아래 다섯은 CartInfo 가 선언만 하고(CartInfo.java:48,50,36,47,35, @SerialName 357/365/309/353/305행) 디컴파일
    # 어디에서도 게터를 읽는 화면 코드를 찾지 못했습니다. 이름은 와이어 키를 그대로 옮긴 것이고 의미는 미확인입니다.
    #: 응답의 ``h_stl_extns_tno`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    settlement_extension_transaction_no: str | None = None
    #: 응답의 ``h_stl_mns_allw_val`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    settlement_means_allow_value: str | None = None
    #: 응답의 ``h_fld_stl_dv`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    field_settlement_division: str | None = None
    #: 응답의 ``h_spvs_rs_stn_cd`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    supervising_station_code: str | None = None
    #: 응답의 ``h_filler`` 값을 그대로 담습니다. 의미를 확인하지 못했습니다.
    filler: str | None = None

    @property
    def usage_window(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        """이용 시작일·시작 시각·종료 시각을 한 번에 반환합니다."""
        return (
            self.usage_start_date,
            self.usage_start_time,
            self.usage_close_time,
        )


@dataclass(frozen=True)
class CartListResponse(BaseKorailResponse):
    """로그인 계정의 장바구니 목록을 담습니다."""

    items: tuple[CartItem, ...] = ()


@dataclass(frozen=True)
class ReservationHistoryTrain:
    """예약 이력의 열차와 결제 기한 정보를 담습니다.

    결제 기한은 ``payment_deadline_date``와 ``payment_deadline_time``에 있으며, 값이 없으면 ``None``입니다. 플래그 필드만으로는
    기한을 알 수 없습니다. 이 모델이 읽지 않는 응답 키도 있으며, 원본은 ``raw``에 남습니다."""

    # 평문 @SerialName 37개 외 보호된 슬롯이 있습니다 (ReservationViewOutTrainInfo.java:94,
    # ReservationViewOutTrainInfo$$serializer.java:39-79). 채워진 결제 기한 값은 미확인입니다.
    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    run_date: str | None = None
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    reservation_type_code: str | None = None
    acceptance_possible_flag: str | None = None
    payment_flag: str | None = None
    settlement_flag: str | None = None
    # ReservationViewOutTrainInfo.java:496.
    #: 예약 금액(``h_rsv_amt``)입니다. 이 열차 행에 있는 유일한 금액 필드입니다.
    reserved_amount: str | None = None
    seat_count: int | None = None
    standing_count: int | None = None
    pnr_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    payment_message: str | None = None
    payment_possible_date: str | None = None
    prepayment_target_flag: str | None = None
    journey_sequence: str | None = None


@dataclass(frozen=True)
class ReservationHistoryTicket:
    """예약 이력에 중첩된 발권 승차권 한 행을 담습니다."""

    sale_date: str | None = None
    sale_window_no: str | None = None
    sale_sequence: str | None = None
    ticket_kind_code: str | None = None
    movie_ticket_flag: str | None = None
    delay_discount_flag: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryOriginalTicket:
    """예약 이력에 중첩된 원표 한 행을 담습니다."""

    sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryPassenger:
    """예약 이력의 승객 유형별 인원·할인 정보를 담습니다."""

    passenger_type_code: str | None = None
    passenger_count_per_info: str | None = None
    discount_kind_code: str | None = None
    discount_kind_code_2: str | None = None
    discount_no: str | None = None
    discount_no_2: str | None = None
    delay_original_window_no: str | None = None
    delay_original_sale_date: str | None = None
    delay_original_sale_sequence: str | None = None
    delay_original_return_password: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryReservation:
    """예약 이력에 중첩된 예약·운임·결제 정보를 담습니다.

    이 블록은 추정한 응답 키(``reservationOut``)로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    키가 다르면 ``ReservationHistoryJourney.reservation``은 ``None``입니다."""

    # 앱 근거: ReservationViewOutJrnyInfo.java:55. 전송 키 reservationOut 은 보호된 serializer 대신 속성명을 사용한 추정입니다.
    pnr_no: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    payment_flag: str | None = None
    tickets: tuple[ReservationHistoryTicket, ...] = ()
    original_tickets: tuple[ReservationHistoryOriginalTicket, ...] = ()
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryJourney:
    """예약 이력의 여정 한 개와 열차·부가 정보를 담습니다.

    ``service_infos``(``srv_infos``)와 ``accompanying_infos``(``acmp_infos``)는 행을 해석하지 않고 응답의 원본 매핑을 그대로
    담습니다."""

    # srv_infos/acmp_infos 는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다 — 원본 그대로라도 여정 단위로 닿을 수 있게 하기
    # 위해서입니다.
    trains: tuple[ReservationHistoryTrain, ...] = ()
    service_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    accompanying_infos: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    reservation: ReservationHistoryReservation | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationHistoryResponse(BaseKorailResponse):
    """현재 예약 이력과 여정별 상세를 담습니다.

    남아 있는 예약이 없어 결과 코드 ``P100``의 실패 응답이 오면 예외를 발생시키지 않고, 목록이 빈 응답을 돌려줍니다."""

    # 라우트는 /classes/com.korail.mobile.reservation.ReservationView입니다(NetworkApi.java:635-636;
    # ReservationViewOut.java:64).
    reservation_passenger_name: str | None = None
    phone_no: str | None = None
    reservation_limit_flag: str | None = None
    seatmap_flag: str | None = None
    process_flag: str | None = None
    follow_flag: str | None = None
    customer_no: str | None = None
    customer_division_code: str | None = None
    customer_sort_code: str | None = None
    customer_class_code: str | None = None
    journey_count: str | None = None
    guide_info: str | None = None
    journeys: tuple[ReservationHistoryJourney, ...] = ()
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        """``items``와 같은 열차 목록을 반환합니다."""
        return self.items


@dataclass(frozen=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    """PNR 기준 중복 예약 확인 결과를 담습니다."""

    # rsvCnt — TicketDupCheckOut.java:28 의 선언은 String 이고 이 DTO 는 kotlinx 이므로 문자열로 읽습니다("0007" 은 그대로).
    # 서버가 이 값을 JSON 정수로 보낸 적이 있는지는 확인하지 않았습니다.
    #: 예약 건수(``rsvCnt``)입니다. ``"0007"``처럼 서버가 보낸 문자열을 그대로 담습니다.
    reservation_count: str | None = None


@dataclass(frozen=True)
class ReservationSeatDetail:
    """예약 상세의 좌석·승객·운임 정보를 담습니다."""

    # ReservationOutSeatInfo.java:33,81. h_psg_tp_dv_nm은 DTO에는 없지만 앱 내장 표본(BasketTicketDataKt.java:44)과 실서버 8/8행에서
    # 확인했습니다. 재계산 입력의 기존 종류·객실·할인 코드는 같은 모양의 홀드 좌석 행을 사용하며(PriceRecalculationRequest.for_hold)
    # 다른 응답에서도 같은 필드가 오는지는 검증 못 함입니다.
    car_no: str | None = None
    seat_no: str | None = None
    room_class_code: str | None = None
    room_class_name: str | None = None
    passenger_type_code: str | None = None
    # 홀드 정산액 계산: mutation_parsers._received_amount (좌석 합을 먼저 구하고 선언 총액과 대조, 좌석 행이 없으면 선언 총액).
    #: 좌석별 받을 금액(``h_rcvd_amt``)입니다. 예약 메서드가 돌려주는 ``ReservationHoldResponse``의 ``received_amount``는 홀드
    #: 응답에 좌석 행이 있으면 그 행들의 이 값을 합한 금액입니다.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    total_discount_amount: str | None = None
    seat_group_name: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # 위 클래스 주석의 관측 한계를 따릅니다.
    #: 승객 유형 이름(``h_psg_tp_dv_nm``)입니다. 응답에 따라 없을 수 있으며, 없으면 ``None``입니다.
    passenger_type_name: str | None = None


@dataclass(frozen=True)
class ReservationDetailJourney:
    """홀드(결제 전 예약)의 여정 한 개와 좌석 상세를 담습니다."""

    journey_sequence: str | None = None
    journey_type_code: str | None = None
    reservation_change_no: str | None = None
    #: 7.0.8 여정의 운행일(``h_run_dt``). 누락은 빈 문자열, 명시적 null·잘못된 타입은 None입니다.
    run_date: str | None = ""
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    arrival_date: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    train_no: str | None = None
    train_class_name: str | None = None
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR로 다시 조회한 예약의 여정·좌석·정산액을 담습니다."""

    pnr_no: str | None = None
    window_no: str | None = None
    journey_count: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    payment_flag: str | None = None
    journeys: tuple[ReservationDetailJourney, ...] = ()
    customer_management_no: str | None = None
    mandatory_message: str | None = None
    additional_service_flag: str | None = None
    disability_certificate_number: str | None = None
    pre_settlement_target_flag: str | None = None
    family_info_confirm_flag: str | None = None
    special_room_fare: str | None = None
    issue_possible_date: str | None = None
    issue_possible_time: str | None = None
    passengers: tuple[ReservationPassengerInfo, ...] = ()


@dataclass(frozen=True)
class ReservationJourney:
    """예약된 여정 한 개의 열차·구간·변경 식별자를 담습니다."""

    # 선언: ReservationOutJrnyInfo.java:86,361. 관측: 예약 생성 응답 21/21행에는 없고 재계산 4/4행·예약 상세 8/8행에는
    # 있었습니다. 이 관측이 모든 예약 생성 응답에서 None임을 보장하지는 않습니다.
    #: 여정 순번(``h_jrny_sqno``)입니다. 예약 생성 응답에는 없을 수 있으며, 그러면 ``None``입니다.
    journey_sequence: str | None = None
    reservation_change_no: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    # 선언: ReservationOutJrnyInfo.java:86,305. 관측: reserve/transfer/merge 의 21여정에는 키가 없었으며 익일 도착도
    # 포함됐습니다.
    #: 도착일(``h_arv_dt``)입니다. 예약 응답에는 없을 수 있으며, 그러면 ``None``입니다. 밤을 넘기는 열차는 도착 시각만으로
    #: 도착일을 알 수 없습니다.
    arrival_date: str | None = None
    arrival_time: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    train_no: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationHoldResponse(BaseKorailResponse):
    """홀드(결제 전 예약)의 식별값과 결제 기한·금액을 담습니다.

    예약·할인 재계산 응답이나 ``get_reservation_hold``로 가져온 기존 예약을 나타냅니다.
    이 객체를 받았다는 것만으로 예약이 성공했다고 보장하지 않으므로 응답 상태(``str_result``)와 ``pnr_no``를 확인하세요.
    결제할 금액은 ``received_amount``입니다."""

    pnr_no: str | None = None
    journey_count: str | None = None
    window_no: str | None = None
    temporary_job_sequence_1: str | None = None
    temporary_job_sequence_2: str | None = None
    payment_flag: str | None = None
    payment_message: str | None = None
    # 근거: ReservationOut.java:49,408-409.
    #: ``h_pay_limit_msg`` 값입니다. 결제 기한은 이 필드가 아니라 ``payment_deadline_date``와 ``payment_deadline_time``에
    #: 있습니다.
    payment_deadline_message: str | None = None
    payment_deadline_notice: str | None = None
    # 근거: ReservationOut.java:400,404; 표시는 MyReservationScreenKt.java:6008-6010, DateHelper.java:302.
    #: 결제 기한 날짜입니다. 앱은 이 값과 ``payment_deadline_time``을 이어 붙여 결제 기한으로 표시합니다.
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    # h_tot_fare는 선언됐지만 일반적인 의미는 미확인입니다(ReservationOut.java:444). 내장 표본(BasketTicketDataKt.java:44)은
    # 일반식의 증거가 아닙니다.
    #: ``h_tot_fare`` 값입니다. 의미를 확인하지 못했습니다. 결제 금액으로는 ``received_amount``를 쓰세요.
    total_fare: str | None = None
    # h_tot_prc는 앱의 표시 합계에 쓰입니다(ReservationOut.java:448; PayViewModel.java:11314-11318). 실서버 관측: 일반실·특실
    # 기준액은 54,400원, 정산액은 53,900/78,400원이었습니다.
    #: 앱이 표시하는 합계 금액(``h_tot_prc``)입니다. 결제에는 ``received_amount``를 쓰세요.
    total_price: str | None = None
    # 좌석 합을 먼저 구하고 선언 총액과 대조하며, 사용할 좌석 행이 없으면 선언 총액을 사용합니다(mutation_parsers._received_amount).
    #: 결제할 금액입니다. 좌석별 금액(``h_rcvd_amt``)의 합이며, 응답의 총액(``h_tot_rcvd_amt``)과 다르면 응답을 읽을 때
    #: ``KorailProtocolError``가 발생합니다. 좌석 행이 없으면 응답의 총액을 쓰고, 좌석 금액을 읽을 수 없으면 ``None``입니다.
    received_amount: str | None = None
    journeys: tuple[ReservationJourney, ...] = ()
    total_discount_amount: str | None = None
    customer_management_no: str | None = None
    mandatory_message: str | None = None
    additional_service_flag: str | None = None
    disability_certificate_number: str | None = None
    pre_settlement_target_flag: str | None = None
    family_info_confirm_flag: str | None = None
    special_room_fare: str | None = None
    issue_possible_date: str | None = None
    issue_possible_time: str | None = None
    passengers: tuple[ReservationPassengerInfo, ...] = ()
    # 앱은 예약대기 홀드를 결제하지 않고 대기 옵션만 저장합니다(TrainScheduleViewModel.java:5096-5101;
    # ReservationWaitViewModel.java:1155-1160). reserve·reserve_transfer 가 STANDBY 홀드에 False 를 넣습니다.
    #: 결제할 수 있는 홀드인지 나타냅니다. 예약대기(``STANDBY``)로 만든 홀드는 ``False``이며, ``pay_with_card``는 이런 홀드를
    #: 요청 전에 거절합니다.
    payable: bool = True
    # 근거: client.recalculate_price 의 add_to_cart 분기(raise_on_fail=False).
    #: ``recalculate_price(..., add_to_cart=True)``로 받은 결과에만 장바구니 추가 결과가 들어갑니다. 장바구니 추가가
    #: 실패해도 예외 없이 이 필드에 담기므로 ``str_result``를 확인하세요. 그 밖에는 ``None``입니다.
    cart_addition: CartAddResponse | None = None
    # 재계산은 이미 서버에 반영됐으므로 장바구니 단계의 예외로 결과를 잃지 않습니다(앱도 실패를 알리기만 합니다).
    #: ``add_to_cart=True``에서 장바구니 요청이 라이브러리 예외로 끝났다면 그 예외입니다. 이때 ``cart_addition``은
    #: ``None``이며 장바구니에 추가됐는지는 알 수 없습니다. 그 밖에는 ``None``입니다.
    cart_addition_error: KorailApiError | None = field(default=None, compare=False)


@dataclass(frozen=True)
class CartDiscountAddition:
    """장바구니 추가 결과의 승객별 할인 정보를 담습니다."""

    # 명시적 키: PsgDiscAddInfo.java:81,85.

    passenger_sequence_no: str | None = None
    # h_duty_ref_rcgn_ps_dv_cd 는 DTO 에 선언된 구분 코드입니다(APK 필드명 보존).
    #: ``h_duty_ref_rcgn_ps_dv_cd`` 값입니다. 의미와 가능한 값을 확인하지 못했습니다.
    duty_reference_recognition_division_code: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class CartAddResponse(BaseKorailResponse):
    """장바구니 추가 결과와 승객별 할인 목록을 담습니다.

    할인 행이 없으면 ``discount_additions``는 빈 튜플입니다."""

    # 구조: AddCartListOut.java:24-25,76 → PsgDiscAddInfos.java:81.

    discount_additions: tuple[CartDiscountAddition, ...] = ()
