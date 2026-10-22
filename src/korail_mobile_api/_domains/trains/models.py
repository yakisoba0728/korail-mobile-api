# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""열차 조회·좌석 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Self

from ..._core.parsing import (
    _typed_optional_int,
    defaulted_str,
    nullable_str,
    optional_int,
    strict_str,
    wire,
    wire_model,
)
from ...constants import KORAIL_STANDBY_WAIT_FLAG
from ...errors import KorailInvalidInputError
from ..common.models import BaseKorailResponse


def _train_datetime(date: str | None, time: str | None) -> datetime | None:
    if not date or not time or len(date) != 8 or len(time) != 6:
        return None
    value = date + time
    if not value.isascii() or not value.isdecimal():
        return None
    try:
        return datetime.strptime(value, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _or_alias(alias: str) -> Callable[[Mapping[str, object], str, str], str | None]:
    """첫 키가 없거나 거짓(정수 0 제외)이면 접두 없는 철자 ``alias`` 를 읽습니다."""

    def read(data: Mapping[str, object], key: str, context: str) -> str | None:
        value = data.get(key)
        return nullable_str(data, key if type(value) is int or value else alias, context)

    return read


def _train_no(data: Mapping[str, object], key: str, context: str) -> str:
    """``trnNo`` 도 같은 규칙으로 읽고 둘 다 없으면 ``""`` 입니다. 오류는 언제나 첫 키 이름으로 냅니다."""
    value = data.get(key)
    if type(value) is not int:
        value = value or data.get("trnNo")
    return strict_str({key: value}, key, context) or ""


def _goods_no(data: Mapping[str, object], key: str, context: str) -> str | None:
    # 예약 입력 없이 좌석을 조회하도록 행의 후보 상품번호를 보관합니다. 앱은 h_gd_no 를 행이 아닌 봉투에 선언합니다.
    return nullable_str(data, key, context) or nullable_str(data, "txtGdNo", context)


def _json_int(data: Mapping[str, object], key: str, context: str) -> int | None:
    # JSON 정수만 받습니다(bool·숫자 문자열은 None).
    value = data.get(key)
    return value if type(value) is int else None


def _optional_count(data: Mapping[str, object], key: str, context: str) -> int | None:
    return _typed_optional_int(data, key)


@dataclass(frozen=True, kw_only=True)
class TrainScheduleStop:
    """열차의 정차역 한 곳과 도착·출발 정보를 담습니다."""

    station_code: str | None = wire("stopRsStnCd")
    # 앱은 stopStnNm 누락에 기본값을 쓰지만 18개 예외가 아니므로 None 입니다.
    station_name: str | None = wire("stopStnNm")
    station_construction_order: str | None = wire("stnConsOrdr")
    run_order: str | None = wire("runOrdr")
    actual_arrival_delay_count: str | None = wire("actArvDlayTnum")
    actual_arrival_date: str | None = wire("actArvDt")
    actual_arrival_time: str | None = wire("actArvTm")
    actual_departure_date: str | None = wire("actDptDt")
    actual_departure_time: str | None = wire("actDptTm")
    arrival_date: str | None = wire("arvDt")
    arrival_time: str | None = wire("arvTm")
    departure_date: str | None = wire("dptDt")
    departure_time: str | None = wire("dptTm")
    delay_fare_return_division_code: str | None = wire("dlayFareRetDvCd")
    delay_fare_return_division_name: str | None = wire("dlayFareRetDvCdNm")
    solo_operation_delay_flag: str | None = wire("dlaySoloOprFlg")
    detour_driver_delay_count: str | None = wire("dturDrvDlayTnum")
    expected_arrival_delay_count: str | None = wire("expnArvDlayTnum")
    expected_departure_delay_count: str | None = wire("expnDptDlayTnum")
    regular_flag: str | None = wire("rgulFlg")
    service_flag: str | None = wire("saodFlg")
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, kw_only=True)
class TrainScheduleResponse(BaseKorailResponse):
    """열차 한 편의 정차역 목록을 담습니다."""

    delay_detail_reason_content: str | None = wire("dlayDtlRsnCont")
    stops: tuple[TrainScheduleStop, ...] = ()
    delay_station_construction_order: str | None = wire("dlayStnConsOrdr")
    integrated_message_code: str | None = wire("intgMsgCd")
    message_code: str | None = wire("msgCd")
    message_content: str | None = wire("msgCont")
    message_text: str | None = wire("msgTxt")
    origin_station_code: str | None = wire("orgRsStnCd")
    origin_station_name: str | None = wire("orgRsStnNm")
    route_code: str | None = wire("routCd")
    route_name: str | None = wire("routNm")
    # 앱은 trnNo1·runDt1 누락에 보호된 기본값을 쓰지만 재현하지 않으므로 None 입니다.
    run_date: str | None = wire("runDt1")
    run_segment_order: str | None = wire("runSegOrdr")
    regular_sale_flag: str | None = wire("saleRgulFlg")
    settlement_train_class_code: str | None = wire("stlbTrnClsfCd")
    terminal_station_code: str | None = wire("tmnRsStnCd")
    terminal_station_name: str | None = wire("tmnRsStnNm")
    train_attribute_code: str | None = wire("trnAttCd")
    train_departure_flag: str | None = wire("trnDptFlg")
    train_no: str | None = wire("trnNo1")
    special_train_flag: str | None = wire("trnSpsFlg")
    up_down_division_code: str | None = wire("upDnDvCd")


@dataclass(frozen=True, kw_only=True)
class TransferStation:
    """환승 가능한 역 한 곳을 나타냅니다."""

    station_code: str | None = wire("chtnRsStnCd")
    station_name: str | None = wire("chtnRsStnNm")
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, kw_only=True)
class TransferStationListResponse(BaseKorailResponse):
    """환승 가능한 역 목록을 담습니다."""

    stations: tuple[TransferStation, ...] = ()


@dataclass(frozen=True, kw_only=True)
class TrainSearchQuery:
    """직통·환승 열차의 조회 조건을 구성합니다.

    출발역·도착역에 숫자로만 된 역 코드를 넣으면 클라이언트가 역 목록을 조회해 역 이름으로 바꿔 보내고, 그 밖의 값은 역
    이름으로 보고 그대로 보냅니다. 앱이 쓰는 열차군·조회 구분 코드는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    기본값과 다른 값이 필요하면 ``train_group_code``와 ``query_division_code``를 직접 지정하세요."""

    departure_station: str
    arrival_station: str
    departure_date: str
    departure_time: str = "000000"
    passengers: int = 1
    # evidence: app 7.0.6 TrainGroup.java:25,29,335 (평문은 보호돼 관측값을 씁니다)
    train_group_code: str = "109"
    include_srt: bool = False
    child_passengers: int = 0
    senior_passengers: int = 0
    high_disability_passengers: int = 0
    low_disability_passengers: int = 0
    seat_attribute_code: str = "015"
    connection_station_codes: tuple[str, ...] = ()
    connection_train_group_code: str | None = None
    #: 조회 구분 코드(``qryDvCd``)입니다. 앱의 정렬 선택별 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했으므로, 다른 값이
    #: 필요하면 직접 지정하세요.
    query_division_code: str = "1"
    #: 청소년 승객 수입니다. 앱처럼 청소년·안내견은 어른 칸(``txtPsgFlg_1``)에, 유아는 어린이 칸(``txtPsgFlg_2``)에 더해
    #: 보냅니다.
    teenager_passengers: int = 0
    infant_passengers: int = 0
    guide_dog_passengers: int = 0
    #: 인접역을 포함해 조회합니다. 기본값은 기존 요청과 같은 ``False``입니다.
    include_nearby_stations: bool = False


@dataclass(frozen=True, kw_only=True)
class TrainSummary:
    """열차 한 편의 식별자·예약 상태·운임 표시를 담습니다.

    좌석 예약 상태(``general_reservation_code`` 등)와 운임 문구(``general_fare_text``, ``special_fare_text``)는 서로 다른
    필드입니다."""

    # 식별값은 후속 예약 때 서버가 다시 검증합니다(실서버 관측).

    train_no: str = wire("h_trn_no", _train_no)
    train_group_code: str | None = wire("h_trn_gp_cd", _or_alias("trnGpCd"), default=None)
    departure_station_code: str | None = wire("h_dpt_rs_stn_cd", _or_alias("dptRsStnCd"), default=None)
    arrival_station_code: str | None = wire("h_arv_rs_stn_cd", _or_alias("arvRsStnCd"), default=None)
    departure_date: str | None = wire("h_dpt_dt", _or_alias("dptDt"), default=None)
    departure_time: str | None = wire("h_dpt_tm", _or_alias("dptTm"), default=None)
    arrival_time: str | None = wire("h_arv_tm", _or_alias("arvTm"), default=None)
    departure_station_name: str | None = wire("h_dpt_rs_stn_nm", _or_alias("dptRsStnNm"), default=None)
    arrival_station_name: str | None = wire("h_arv_rs_stn_nm", _or_alias("arvRsStnNm"), default=None)
    run_date: str | None = wire("h_run_dt", _or_alias("runDt"), default=None)
    train_class_code: str | None = wire("h_trn_clsf_cd", _or_alias("trnClsfCd"), default=None)
    departure_run_order: str | None = wire("h_dpt_stn_run_ordr", _or_alias("dptStnRunOrdr"), default=None)
    arrival_run_order: str | None = wire("h_arv_stn_run_ordr", _or_alias("arvStnRunOrdr"), default=None)
    seat_map_flag: str | None = wire("h_rd_seat_map_flg")
    general_reservation_code: str | None = wire("h_gen_rsv_cd")
    general_reservation_flag: str | None = wire("h_gen_rsv_flg")
    departure_construction_order: str | None = wire("h_dpt_stn_cons_ordr")
    arrival_construction_order: str | None = wire("h_arv_stn_cons_ordr")
    seat_attribute_code: str | None = wire("h_seat_att_cd")
    car_type_code: str | None = wire("h_car_tp_cd")
    car_type_name: str | None = wire("h_car_tp_nm")
    train_class_name: str | None = wire("h_trn_clsf_nm")
    train_group_name: str | None = wire("h_trn_gp_nm")
    general_room_class_name: str | None = wire("h_gen_psrm_cl_nm")
    special_room_class_name: str | None = wire("h_spe_psrm_cl_nm")
    secondary_general_reservation_code: str | None = wire("h_gen_rsv_cd2")
    special_reservation_code: str | None = wire("h_spe_rsv_cd")
    special_reservation_flag: str | None = wire("h_spe_rsv_flg")
    secondary_special_reservation_code: str | None = wire("h_spe_rsv_cd2")
    free_reservation_code: str | None = wire("h_free_rsv_cd")
    free_reservation_flag: str | None = wire("h_free_rsv_flg")
    standing_reservation_code: str | None = wire("h_stnd_rsv_cd")
    standing_reservation_flag: str | None = wire("h_stnd_rsv_flg")
    reservation_available_flag: str | None = wire("h_rsv_psb_flg")
    general_availability_name: str | None = wire("h_gen_rsv_nm")
    special_availability_name: str | None = wire("h_spe_rsv_nm")
    wait_reservation_flag: str | None = wire("h_wait_rsv_flg")
    standard_remaining_seat_count: str | None = wire("h_std_rest_seat_cnt")
    first_class_remaining_seat_count: str | None = wire("h_fst_rest_seat_cnt")
    free_remaining_seat_count: str | None = wire("h_free_rest_seat_cnt")
    standing_remaining_seat_count: str | None = wire("h_stnd_rest_seat_cnt")
    free_car_count: str | None = wire("h_free_sracar_cnt")
    reservation_wait_passenger_count: str | None = wire("h_rsv_wait_ps_cnt")
    total_passenger_count: int | None = wire("totPsgCnt", _json_int, default=None)
    goods_no: str | None = wire("h_gd_no", _goods_no, default=None)
    #: 열차 순번(``h_trn_seq``)입니다. 앱은 환승 조회 결과에서 이 값이 같은 두 행을 한 여정으로 묶습니다.
    train_sequence: str | None = wire("h_trn_seq")
    # 관측: 직통 6질의의 행은 모두 1, 환승 6여정 12구간은 1/2였습니다.
    #: 환승 여정 안에서 이 열차 구간의 순서(``h_chg_trn_seq``)입니다. ``train_sequence``와는 다른 값입니다.
    change_train_sequence: str | None = wire("h_chg_trn_seq")
    # 관측: 직통 6질의는 1/직통, 환승 6여정 12구간은 2/환승이었습니다.
    #: 직통·환승 구분 코드(``h_chg_trn_dv_cd``)입니다.
    change_train_division_code: str | None = wire("h_chg_trn_dv_cd")
    #: 병합 좌석 적용 플래그(``h_yms_apl_flg``)입니다. 앱은 이 값으로 병합 좌석 여부를 판정합니다.
    merge_seat_application_flag: str | None = wire("h_yms_apl_flg")
    train_suspension_flag: str | None = wire("h_trn_sps_flg")
    general_fare_text: str | None = wire("h_rsv_psb_nm")
    special_fare_text: str | None = wire("h_spe_rsv_psb_nm")
    standing_availability_name: str | None = wire("h_stnd_rsv_nm")
    free_availability_name: str | None = wire("h_free_rsv_nm")
    arrival_date: str | None = wire("h_arv_dt")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)

    def has_general_seat(self) -> bool:
        """일반실 예약 코드가 가용 값 ``"11"``인지 확인합니다."""
        return self.general_reservation_code == "11"

    def has_special_seat(self) -> bool:
        """특실 예약 코드가 가용 값 ``"11"``인지 확인합니다."""
        return self.special_reservation_code == "11"

    def has_seat(self) -> bool:
        """일반실 또는 특실에 가용 좌석이 있는지 확인합니다."""
        return self.has_general_seat() or self.has_special_seat()

    def has_waiting_list(self) -> bool:
        """일반실 예약대기 플래그가 가능 값 ``" 9"``인지 확인합니다."""
        return self.wait_reservation_flag == KORAIL_STANDBY_WAIT_FLAG

    @property
    def duration_minutes(self) -> int | None:
        """실제 출발·도착 날짜와 시각으로 소요 시간을 계산합니다.

        날짜·시각이 없거나 잘못됐거나 도착이 출발보다 빠르면 ``None``입니다.
        도착 날짜를 추측하지 않습니다."""
        departure = _train_datetime(self.departure_date, self.departure_time)
        arrival = _train_datetime(self.arrival_date, self.arrival_time)
        if departure is None or arrival is None or arrival < departure:
            return None
        return int((arrival - departure).total_seconds() // 60)

    @property
    def duration_text(self) -> str | None:
        """소요 시간을 ``"3시간 30분"`` 형태로 표시합니다."""
        minutes = self.duration_minutes
        if minutes is None:
            return None
        hours, remainder = divmod(minutes, 60)
        if hours == 0:
            return f"{remainder}분"
        return f"{hours}시간" + (f" {remainder}분" if remainder else "")

    def summary(self) -> str:
        """열차, 출발·도착 일정, 역과 소요 시간을 한 줄로 표시합니다."""
        departure = _train_datetime(self.departure_date, self.departure_time)
        arrival = _train_datetime(self.arrival_date, self.arrival_time)
        departure_text = departure.strftime("%Y-%m-%d %H:%M") if departure is not None else "?"
        arrival_text = arrival.strftime("%Y-%m-%d %H:%M") if arrival is not None else "?"
        departure_name = self.departure_station_name or self.departure_station_code or "?"
        arrival_name = self.arrival_station_name or self.arrival_station_code or "?"
        kind = self.train_class_name or self.train_group_name or self.train_class_code or "열차"
        duration = self.duration_text
        return f"[{kind} {self.train_no}] {departure_text}~{arrival_text} {departure_name}~{arrival_name}" + (
            f" ({duration})" if duration is not None else ""
        )

    @classmethod
    def from_raw(cls, raw: Mapping[str, object]) -> Self:
        """검색 응답의 행 하나를 ``TrainSummary``로 만듭니다.

        주요 값은 ``h_`` 접두 철자와 접두 없는 철자를 둘 다 찾습니다(``h_trn_no``와 ``trnNo`` 등). 정수로 온 값은 문자열로
        바꾸고, 선택 필드에 문자열·정수가 아닌 값이 오면 ``None``이 됩니다. ``train_no``에 문자열·정수·``null``이 아닌 값이
        오면 ``KorailProtocolError``가 발생합니다."""
        return wire_model(cls, raw, "train", raw=raw)


@dataclass(frozen=True, kw_only=True)
class SeatAttribute:
    """좌석 속성 코드와 표시 이름을 담습니다."""

    name: str = wire("seatAttNm", defaulted_str)
    code: str | None = wire("seatAttCd")


@dataclass(frozen=True, kw_only=True)
class SeatCar:
    """좌석 조회에 사용할 호차 번호와 좌석 속성을 담습니다."""

    #: 호차 번호입니다. 응답에 없거나 빈 문자열이면 ``None``입니다.
    car_no: int | None
    room_class_name: str
    #: 잔여 좌석 수입니다. 응답에 없거나 빈 문자열이면 ``None``입니다.
    remaining_seat_count: int | None
    attributes: tuple[SeatAttribute, ...]
    room_class_code: str | None = None
    total_seat_count: int | None = None


@dataclass(frozen=True, kw_only=True)
class SeatCarListResponse(BaseKorailResponse):
    """열차 한 편의 조회 가능한 호차 목록을 담습니다."""

    recommended_car_no: int | None = wire("h_rcmd_srcar_no", _optional_count, default=None)
    train_no: str | None = wire("h_trn_no")
    cars: tuple[SeatCar, ...] = ()
    train_class_code: str | None = wire("h_trn_clsf_cd")
    train_group_code: str | None = wire("h_trn_gp_cd")
    #: 호차 수(``h_scar_num``)입니다. 문자열로 담으며, 응답에 없거나 읽을 수 없으면 ``None``입니다.
    car_count: str | None = wire("h_scar_num")


@dataclass(frozen=True, kw_only=True)
class PhysicalSeat:
    """좌석표 한 자리의 식별자·표시·판매 가능 여부를 담습니다.

    좌석 지정에는 표시용 ``specification``이 아니라 식별자 ``seat_no``를 쓰세요. ``sale_possible``이 ``"Y"``인 좌석은
    ``KorailSeatAssignment.from_inventory()``로 좌석 지정 입력으로 바꿀 수 있습니다. ``floor``는 앱이 읽지 않는 값이며
    응답에 없으면 ``None``입니다."""

    seat_no: str = wire("seat_no", defaulted_str)
    sale_possible: str = wire("sale_psb_flg", defaulted_str)
    direction_code: str = wire("dir_seat_att_cd", defaulted_str)
    other_attribute_code: str | None = wire("etc_seat_att_cd", nullable_str)
    requested_attribute_code: str = wire("rq_seat_att_cd", defaulted_str)
    floor: str | None = wire("floor", nullable_str)
    specification: str = wire("seat_spec", defaulted_str)
    sequence_no: str = wire("sqr_no", defaulted_str)
    message_code: str = wire("intg_msg_cd", defaulted_str)
    message: str = wire("intg_msg", defaulted_str)
    visual_message_division_code: str | None = wire("vz_msg_dv_cd", nullable_str)


@dataclass(frozen=True, kw_only=True)
class SeatWindow:
    """좌석 배치도의 창문 위치 비율을 담습니다.

    비율이 응답에 없거나 빈 문자열이면 ``None``입니다."""

    start_location_ratio: float | None
    close_location_ratio: float | None


@dataclass(frozen=True, kw_only=True)
class SeatInventoryResponse(BaseKorailResponse):
    """한 호차의 좌석 재고와 창문 위치를 담습니다.

    ``car_no``가 없으면 ``KorailSeatAssignment.from_inventory()``를 쓸 수 없으므로
    ``KorailSeatAssignment(car_no=..., seat_no=...)``로 직접 만드세요."""

    # 앱 선언은 String 이지만 서버 표본은 JSON 정수였습니다.
    #: 좌석 배치 형식입니다. 서버가 정수로 보내도 문자열로 담으며, 응답에 없으면 빈 문자열입니다.
    layout_type: str = wire("layout_type", defaulted_str, default="")
    arrangement_code: str = wire("seat_ary_cd", defaulted_str, default="")
    # 두 수는 앱 DTO 에 없는 키입니다.
    #: 잔여 좌석 수(``seat_remain_count``)입니다. 음이 아닌 정수로 읽을 수 없으면 ``None``입니다.
    remaining_count: int | None = wire("seat_remain_count", _optional_count, default=None)
    #: 전체 좌석 수(``seat_total_count``)입니다. 음이 아닌 정수로 읽을 수 없으면 ``None``입니다.
    total_count: int | None = wire("seat_total_count", _optional_count, default=None)
    seats: tuple[PhysicalSeat, ...] = ()
    windows: tuple[SeatWindow, ...] = ()
    vr_banner_url: str | None = wire("vrBnrUrl")
    car_type_code: str | None = wire("car_tp_cd")
    car_no: int | None = wire("scar_no", _optional_count, default=None)
    up_down_division_code: str | None = wire("up_dn_dv_cd")


@dataclass(frozen=True, kw_only=True)
class TrainSearchMetadata:
    """열차 조회 결과의 공통 조건과 페이지 커서를 담습니다.

    ``next_page_flag``가 ``"Y"``여도 커서가 없으면 다음 페이지를 조회할 수 없습니다. 다음 조회에 넘길 값은 결과의
    ``next_page()``로 만드세요."""

    job_id: str | None = wire("strJobId")
    menu_id: str | None = wire("h_menu_id")
    goods_no: str | None = wire("h_gd_no")
    next_page_flag: str | None = wire("h_next_pg_flg")
    next_query_station_no: str | None = wire("h_qry_st_no_next")
    next_train_no: str | None = wire("h_trn_no_next")
    #: 다음 환승 조회에 넘길 선행 열차 번호 커서입니다.
    next_preceding_train_no: str | None = wire("h_prcd_trn_no_next")
    next_connecting_train_no: str | None = wire("h_ectb_trn_no_next")
    result_count: str | None = wire("h_rslt_cnt")
    #: 검색 안내 문구(``h_notice_msg``)입니다. 앱은 값이 있으면 경고창으로 보여 줍니다.
    notice_message: str | None = wire("h_notice_msg")
    first_seat_count: str | None = wire("h_seat_cnt_first")
    second_seat_count: str | None = wire("h_seat_cnt_second")
    first_departure_time: str | None = wire("txtGoHour_first")
    agreement_text: str | None = wire("h_agree_txt")
    remaining_seat_count: str | None = wire("h_rest_seat_cnt")
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, kw_only=True)
class TrainSearchContinuation:
    """다음 열차 조회에 전달할 세 개의 커서 값을 담습니다.

    보통 직접 만들지 않고 조회 결과의 ``next_page()``가 돌려주는 값을 씁니다. 세 값은 각각 ``qryStNo``, ``qryStTrnNo``,
    ``qryStTrnNo2``로 보냅니다. ``query_station_no``와 ``query_train_no``는 비어 있지 않은 문자열이어야 하고
    ``query_train_no2``만 빈 문자열을 허용하며, 조건에 맞지 않으면 ``KorailProtocolError``가 발생합니다."""

    query_station_no: str
    query_train_no: str
    query_train_no2: str = ""

    def __post_init__(self) -> None:
        for name in ("query_station_no", "query_train_no"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise KorailInvalidInputError(f"TrainSearchContinuation.{name} must be a non-empty string")
        if not isinstance(self.query_train_no2, str):
            raise KorailInvalidInputError("TrainSearchContinuation.query_train_no2 must be a string")


def _train_search_continuation(
    metadata: TrainSearchMetadata,
    *,
    query_train_no: str,
    query_train_no2: str = "",
) -> TrainSearchContinuation | None:
    if metadata.next_page_flag != "Y":
        return None
    try:
        return TrainSearchContinuation(
            query_station_no=metadata.next_query_station_no or "",
            query_train_no=query_train_no,
            query_train_no2=query_train_no2,
        )
    except KorailInvalidInputError:
        return None


@dataclass(frozen=True, kw_only=True)
class TrainSearchResult:
    """직통 열차 조회 한 페이지와 후속 조회 정보를 담습니다.

    예외 없이 반환돼도 ``trains``가 비어 있을 수 있으므로 확인하세요."""

    trains: list[TrainSummary]
    response: BaseKorailResponse
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)
    #: 간편 검색 필터를 적용하기 전의 열차 목록입니다. 필터를 쓰지 않았으면 ``None``입니다.
    unfiltered_trains: list[TrainSummary] | None = field(default=None, repr=False, compare=False)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 조회에 넘길 ``TrainSearchContinuation``을 반환합니다.

        ``next_page_flag``가 ``"Y"``이고 필수 커서가 모두 있을 때만 값을 돌려줍니다. ``trains``가 비었거나 커서가 없으면
        ``None``입니다. 간편 검색 필터를 사용했다면 필터 전 목록을 기준으로 판정합니다."""
        # 앱은 결과 목록이 비어 있으면 다음 페이지를 부르지 않습니다.
        trains = self.unfiltered_trains if self.unfiltered_trains is not None else self.trains
        if not trains:
            return None
        metadata = self.metadata
        return _train_search_continuation(metadata, query_train_no=metadata.next_train_no or "")

    def next_query_from_last_departure(
        self,
        query: TrainSearchQuery,
    ) -> TrainSearchQuery | None:
        """``query``의 출발 날짜·시각을 마지막 열차의 출발 날짜·시각으로 바꾼 조회 조건을 만듭니다.

        요청은 보내지 않습니다. 필터 전 목록의 마지막 열차를 사용하며,
        목록이 비었거나 마지막 열차에 출발 날짜·시각이 없으면 ``None``입니다."""
        trains = self.unfiltered_trains if self.unfiltered_trains is not None else self.trains
        if not trains:
            return None
        last = trains[-1]
        date = last.departure_date
        time = last.departure_time
        if not date or not time:
            return None
        return replace(query, departure_date=date, departure_time=time)


@dataclass(frozen=True, kw_only=True)
class TransferItinerary:
    """응답에서 묶인 두 구간의 환승 여정을 담습니다.

    환승 조회 결과에서 ``train_sequence``(``h_trn_seq``)가 같은 두 행을 응답에 나온 순서대로 묶은 것입니다. 구간 순서를
    나타내는 ``change_train_sequence``(``h_chg_trn_seq``)와는 다른 값입니다."""

    first: TrainSummary
    second: TrainSummary

    @property
    def legs(self) -> tuple[TrainSummary, ...]:
        """두 열차 구간을 응답에서 묶인 원래 순서대로 반환합니다."""
        return (self.first, self.second)

    @property
    def transfer_station_code(self) -> str | None:
        """첫 구간 도착역과 다음 구간 출발역이 같을 때만 그 역 코드를 반환합니다.

        다르면 ``None``이므로 두 구간의 역을 직접 확인하세요."""
        arrival = self.first.arrival_station_code
        return arrival if arrival == self.second.departure_station_code else None

    @property
    def transfer_station_name(self) -> str | None:
        """두 구간이 연결되는 환승역 이름을 반환합니다.

        첫 구간 도착역 이름과 다음 구간 출발역 이름이 같을 때만 그 이름을 반환하고, 다르면 ``None``입니다."""
        arrival = self.first.arrival_station_name
        return arrival if arrival == self.second.departure_station_name else None


def pair_transfer_itineraries(
    trains: list[TrainSummary],
) -> list[TransferItinerary]:
    """앱처럼 ``h_trn_seq``(:attr:`TrainSummary.train_sequence`, 없으면 ``None`` 끼리)가 같은 행을 처음 나온 순서대로
    묶습니다. 두 구간이 아닌 묶음은 여정으로 만들지 않고 ``trains`` 에만 남습니다."""
    by_sequence: dict[str | None, list[TrainSummary]] = {}
    for train in trains:
        by_sequence.setdefault(train.train_sequence, []).append(train)
    return [
        TransferItinerary(first=group[0], second=group[1]) for group in by_sequence.values() if len(group) == 2
    ]


@dataclass(frozen=True, kw_only=True)
class TransferSearchResult:
    """환승 조회의 전체 열차 행과 두 구간으로 묶은 여정을 담습니다."""

    itineraries: list[TransferItinerary]
    trains: list[TrainSummary]
    response: BaseKorailResponse
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 조회에 넘길 ``TrainSearchContinuation``을 반환합니다.

        ``next_page_flag``가 ``"Y"``이고 커서가 있을 때만 값을 돌려줍니다. 환승 커서(``next_preceding_train_no``,
        ``next_connecting_train_no``)가 둘 다 있으면 그 값을 쓰고, 하나라도 없으면 직통 커서(``next_train_no``)를 씁니다.
        ``trains``가 비었거나 커서가 없으면 ``None``입니다."""
        # 환승 커서 하나가 없을 때 직통 커서로 폴백하는 것은 라이브러리 정책입니다(앱의 비교 리터럴은 보호됨).
        if not self.trains:
            return None
        metadata = self.metadata
        preceding = metadata.next_preceding_train_no or ""
        connecting = metadata.next_connecting_train_no or ""
        transfer_cursor = bool(preceding.strip()) and bool(connecting.strip())
        return _train_search_continuation(
            metadata,
            query_train_no=preceding if transfer_cursor else metadata.next_train_no or "",
            query_train_no2=connecting if transfer_cursor else "",
        )


@dataclass(frozen=True, kw_only=True)
class FreeSeatCarResponse(BaseKorailResponse):
    """열차의 자유석 호차와 안내 문구를 담습니다."""

    title: str | None = wire("fresTtl")
    #: 자유석 호차 번호(``fresScarNo``)입니다. 자유석이 없는 열차는 ``None``입니다.
    car_no: str | None = wire("fresScarNo")
    content: str | None = wire("fresCont")


@dataclass(frozen=True, kw_only=True)
class GuideSeatConditionResponse(BaseKorailResponse):
    """도우미석 이용 조건과 서버 안내를 담습니다.

    실패 응답도 예외를 발생시키지 않고 돌려줍니다(세션 만료는 제외). 안내 문구는 ``h_msg_txt``에 있습니다. ``time_stamp``는 추정한
    응답 키(``timeStamp``)로 읽으며, 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 전송 키는 long 속성명에 따른 추정입니다.
    time_stamp: int | None = wire("timeStamp", optional_int, default=None)


@dataclass(frozen=True, kw_only=True)
class TrainScheduleItem:
    """좌석배정·병합 조회에 사용하는 열차 정보를 담습니다.

    ``get_seat_assignment_schedule``과 ``get_merge_seat_options``는 응답 모양이 달라 채우는 필드가 다릅니다. 한쪽 응답에 없는
    필드는 ``None``입니다."""

    # 두 조회는 같은 키를 쓰지만 선언 집합이 달라 parsers.py 가 상대 조회에만 있는 키를 읽지 않습니다.
    train_no: str | None = wire("h_trn_no")
    train_no_qb: str | None = wire("h_trn_no_qb")
    train_sequence: str | None = wire("h_trn_seq")
    train_group_code: str | None = wire("h_trn_gp_cd")
    train_class_code: str | None = wire("h_trn_clsf_cd")
    train_class_name: str | None = wire("h_trn_clsf_nm")
    run_date: str | None = wire("h_run_dt")
    departure_date: str | None = wire("h_dpt_dt")
    departure_time: str | None = wire("h_dpt_tm")
    departure_time_qb: str | None = wire("h_dpt_tm_qb")
    arrival_date: str | None = wire("h_arv_dt")
    arrival_time: str | None = wire("h_arv_tm")
    arrival_time_qb: str | None = wire("h_arv_tm_qb")
    departure_station_code: str | None = wire("h_dpt_rs_stn_cd")
    departure_station_name: str | None = wire("h_dpt_rs_stn_nm")
    arrival_station_code: str | None = wire("h_arv_rs_stn_cd")
    arrival_station_name: str | None = wire("h_arv_rs_stn_nm")
    departure_construction_order: str | None = wire("h_dpt_stn_cons_ordr")
    arrival_construction_order: str | None = wire("h_arv_stn_cons_ordr")
    departure_run_order: str | None = wire("h_dpt_stn_run_ordr")
    arrival_run_order: str | None = wire("h_arv_stn_run_ordr")
    car_type_name: str | None = wire("h_car_tp_nm")
    general_room_name: str | None = wire("h_gen_psrm_cl_nm")
    special_room_name: str | None = wire("h_spe_psrm_cl_nm")
    general_reservation_code: str | None = wire("h_gen_rsv_cd")
    #: 일반실 예약 표시 이름(``h_gen_rsv_nm``)입니다. 두 조회 모두 이 필드를 채웁니다.
    general_reservation_name: str | None = wire("h_gen_rsv_nm")
    special_reservation_code: str | None = wire("h_spe_rsv_cd")
    free_seat_reservation_code: str | None = wire("h_free_rsv_cd")
    standing_reservation_code: str | None = wire("h_stnd_rsv_cd")
    #: 입석 예약 표시 이름(``h_stnd_rsv_nm``)입니다. 고정값 ``"-"``가 아니라 행마다 다른 값(예: ``"역발매중"``)이 옵니다.
    standing_reservation_name: str | None = wire("h_stnd_rsv_nm")
    journey_reservation_code: str | None = wire("h_jrny_rsv_cd")
    journey_reservation_name: str | None = wire("h_jrny_rsv_nm")
    seat_map_flag: str | None = wire("h_rd_seat_map_flg")
    delay_sale_flag: str | None = wire("h_dlay_sale_flg")
    wait_reservation_flag: str | None = wire("h_wait_rsv_flg")
    # 이 필드의 할인 라벨은 매핑 실수가 아니라 서버가 보내는 값입니다. 다른 키로 "고치지" 마세요.
    #: 예약 가능 표시 문구(``h_rsv_psb_nm``)입니다. 가부 플래그가 아니라 메뉴에 따라 내용이 달라지는 화면 문구이며, 할인 라벨이
    #: 들어 있을 수도 있습니다.
    reservation_possible_name: str | None = wire("h_rsv_psb_nm")
    special_reservation_possible_name: str | None = wire("h_spe_rsv_psb_nm")
    info_text: str | None = wire("h_info_txt")
    popup_message: str | None = wire("h_popup_msg")
    shuttle_standing_open_flag: str | None = wire("shtmStndOpFlg")
    standing_remaining_seat_count: str | None = wire("restStndNum")
    standard_remaining_seat_count: str | None = wire("h_std_rest_seat_cnt")
    first_remaining_seat_count: str | None = wire("h_fst_rest_seat_cnt")
    merge_target_flag: str | None = wire("h_yms_apl_flg")
    train_suspended_flag: str | None = wire("h_trn_sps_flg")
    special_reservation_name: str | None = wire("h_spe_rsv_nm")
    free_seat_reservation_name: str | None = wire("h_free_rsv_nm")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class SeatAssignmentScheduleResponse(BaseKorailResponse):
    """좌석배정 예매 화면의 열차 목록과 조회 조건을 담습니다.

    조회 조건 필드의 이름은 열차 조회 결과의 ``TrainSearchMetadata``와 대부분 같습니다. ``merge_reservation_possible_flag``는
    이 응답에서 읽지 않으므로 항상 ``None``입니다."""

    next_page_flag: str | None = wire("h_next_pg_flg")
    # h_merge_rsv_psb_flg 는 병합 조회 컨테이너에만 선언됩니다.
    merge_reservation_possible_flag: str | None = None
    job_id: str | None = wire("strJobId")
    menu_id: str | None = wire("h_menu_id")
    goods_no: str | None = wire("h_gd_no")
    notice_message: str | None = wire("h_notice_msg")
    first_seat_count: str | None = wire("h_seat_cnt_first")
    second_seat_count: str | None = wire("h_seat_cnt_second")
    agreement_text: str | None = wire("h_agree_txt")
    first_departure_time: str | None = wire("txtGoHour_first")
    result_count: str | None = wire("h_rslt_cnt")
    next_query_station_no: str | None = wire("h_qry_st_no_next")
    next_train_no: str | None = wire("h_trn_no_next")
    next_preceding_train_no: str | None = wire("h_prcd_trn_no_next")
    next_connecting_train_no: str | None = wire("h_ectb_trn_no_next")
    remaining_seat_count: str | None = wire("h_rest_seat_cnt")
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True, kw_only=True)
class IntermediateStation:
    """좌석 병합 구간이 나뉘는 중간역을 담습니다."""

    code: str | None = wire("rsStnCd")
    name: str | None = wire("rsStnNm")
    run_order: str | None = wire("runOrdr")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class MergeSeatsInquiryResponse(BaseKorailResponse):
    """병합 가능한 열차와 중간역 목록을 담습니다."""

    merge_reservation_possible_flag: str | None = None
    # 최상위 runDt 는 관측 20여 회에 없었고 행의 h_run_dt 만 있었습니다.
    #: 응답 최상위의 운행일(``runDt``)입니다. 응답에 없으면 ``None``이며, 열차별 운행일은 ``trains`` 각 항목의 ``run_date``에
    #: 있습니다.
    run_date: str | None = wire("runDt")
    intermediate_stations: tuple[IntermediateStation, ...] = ()
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True, kw_only=True)
class PriceFare:
    """열차 한 구간의 운임 정보를 담습니다."""

    journey_sequence: str | None = wire("jrnySqno")
    room_class_name: str | None = wire("psrmClNm")
    #: 요금(``rcvdFare``)입니다. 특실 추가 요금 등이 들어갑니다.
    received_fare: str | None = wire("rcvdFare")
    #: 운임(``rcvdPrc``)입니다. 쉼표와 "원"이 붙은 표시 문자열입니다(예: ``"21,600원"``).
    received_price: str | None = wire("rcvdPrc")
    #: 합계 금액(``sumAmt``)입니다.
    total_amount: str | None = wire("sumAmt")
    train_no: str | None = wire("trnNo")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class PriceFareQuoteResponse(BaseKorailResponse):
    """예매 전 운임 조회 결과를 담습니다."""

    fares: tuple[PriceFare, ...] = ()
