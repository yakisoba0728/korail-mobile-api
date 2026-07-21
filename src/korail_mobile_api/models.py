from dataclasses import dataclass, field
from typing import Any

from .errors import KorailProtocolError


@dataclass(frozen=True)
class KorailSession:
    jsessionid: str | None = field(default=None, repr=False)
    member_no: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    member_card_no: str | None = field(default=None, repr=False)
    customer_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class BaseKorailResponse:
    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "BaseKorailResponse":
        if not isinstance(raw, dict):
            raise KorailProtocolError("KORAIL response must be a JSON object")
        envelope_fields = ("h_msg_cd", "h_msg_txt", "strResult")
        missing = [
            field_name
            for field_name in envelope_fields
            if field_name not in raw
        ]
        if missing:
            raise KorailProtocolError(f"KORAIL response missing required envelope fields: {', '.join(missing)}")
        invalid = [
            field_name
            for field_name in envelope_fields
            if raw[field_name] is not None
            and not isinstance(raw[field_name], str)
        ]
        if invalid:
            raise KorailProtocolError(
                "KORAIL response envelope fields must be strings or null: "
                f"{', '.join(invalid)}"
            )
        return cls(
            h_msg_cd=raw.get("h_msg_cd"),
            h_msg_txt=raw.get("h_msg_txt"),
            str_result=raw.get("strResult"),
            raw=raw,
        )


@dataclass(frozen=True)
class AppVersionInfo:
    message: str | None = None
    new_version: str | None = None


@dataclass(frozen=True)
class AppDataResponse(BaseKorailResponse):
    disability_certification_msg: str | None = None
    for_seat_intg: str | None = None
    airport_bus_msg: str | None = None
    railplus_cardinfo: str | None = None
    version: AppVersionInfo | None = None


@dataclass(frozen=True)
class NoticeResponse(BaseKorailResponse):
    board_id: str | None = None
    post_sequence: str | None = None
    post_title: str | None = None


@dataclass(frozen=True)
class UuidResponse(BaseKorailResponse):
    verification_code: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class MaasMenuItem:
    active: str | None = None
    additional_service_code: str | None = field(default=None, repr=False)
    app_data: str | None = None
    icon_off: str | None = field(default=None, repr=False)
    icon_on: str | None = field(default=None, repr=False)
    info: str | None = None
    login_required: str | None = None
    name: str | None = None
    popup_image: str | None = field(default=None, repr=False)
    menu_type: str | None = None
    url: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def uses_station_selection(self) -> bool:
        return (
            self.active == "Y"
            and self.menu_type != "N"
            and self.app_data in {"Y", "M10", "M30"}
            and isinstance(self.additional_service_code, str)
            and bool(self.additional_service_code.strip())
        )


@dataclass(frozen=True)
class MaasMenuListResponse(BaseKorailResponse):
    items: tuple[MaasMenuItem, ...] = ()
    departure_elevator_url: str | None = field(default=None, repr=False)
    departure_navigation_url: str | None = field(default=None, repr=False)
    departure_parking_url: str | None = field(default=None, repr=False)
    arrival_elevator_url: str | None = field(default=None, repr=False)
    arrival_bus_info_url: str | None = field(default=None, repr=False)
    arrival_parking_url: str | None = field(default=None, repr=False)
    arrival_baggage_transfer_robot_url: str | None = field(
        default=None,
        repr=False,
    )


@dataclass(frozen=True)
class KorailStation:
    code: str
    name: str
    longitude: str | None = None
    latitude: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    group: str | None = field(default=None, repr=False)
    major: str | None = field(default=None, repr=False)
    popup_type: int | None = None
    popup_message: str | None = field(default=None, repr=False)
    popup_link_title: str | None = field(default=None, repr=False)
    popup_link_url: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    stations: tuple[KorailStation, ...] = ()


@dataclass(frozen=True)
class StationInfoResponse(BaseKorailResponse):
    count: int = 0
    map_version: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TrainCalendarDay:
    run_date: str | None = None
    business_day_stage_code: str | None = None
    day_division_code: str | None = None
    holiday_division_code: str | None = None
    sale_day_division_code: str | None = None
    a_train_operation_flag: str | None = None
    d_train_operation_flag: str | None = None
    g_train_operation_flag: str | None = None
    o_train_operation_flag: str | None = None
    s_train_operation_flag: str | None = None
    v_train_operation_flag: str | None = None
    x_train_operation_flag: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class TrainCalendarResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    days: tuple[TrainCalendarDay, ...] = ()


@dataclass(frozen=True)
class TrainScheduleStop:
    station_code: str | None = field(default=None, repr=False)
    station_name: str | None = field(default=None, repr=False)
    station_construction_order: str | None = field(default=None, repr=False)
    run_order: str | None = field(default=None, repr=False)
    actual_arrival_delay_count: int | None = None
    actual_arrival_date: str | None = field(default=None, repr=False)
    actual_arrival_time: str | None = field(default=None, repr=False)
    actual_departure_date: str | None = field(default=None, repr=False)
    actual_departure_time: str | None = field(default=None, repr=False)
    planned_arrival_date: str | None = field(default=None, repr=False)
    planned_arrival_time: str | None = field(default=None, repr=False)
    planned_departure_date: str | None = field(default=None, repr=False)
    planned_departure_time: str | None = field(default=None, repr=False)
    delay_fare_return_division_code: str | None = field(
        default=None,
        repr=False,
    )
    delay_fare_return_division_name: str | None = field(
        default=None,
        repr=False,
    )
    solo_operation_delay_flag: str | None = None
    detour_driver_delay_count: str | None = None
    expected_arrival_delay_count: str | None = None
    expected_departure_delay_count: str | None = None
    regular_flag: str | None = None
    service_flag: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class TrainScheduleResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    delay_detail_reason_content: str | None = field(default=None, repr=False)
    stops: tuple[TrainScheduleStop, ...] = ()
    delay_station_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    integrated_message_code: str | None = field(default=None, repr=False)
    message_code: str | None = field(default=None, repr=False)
    message_content: str | None = field(default=None, repr=False)
    message_text: str | None = field(default=None, repr=False)
    origin_station_code: str | None = field(default=None, repr=False)
    origin_station_name: str | None = field(default=None, repr=False)
    route_code: str | None = field(default=None, repr=False)
    route_name: str | None = field(default=None, repr=False)
    run_date: str | None = field(default=None, repr=False)
    run_segment_order: str | None = field(default=None, repr=False)
    regular_sale_flag: str | None = None
    standard_train_class_code: str | None = field(default=None, repr=False)
    terminal_station_code: str | None = field(default=None, repr=False)
    terminal_station_name: str | None = field(default=None, repr=False)
    train_attribute_code: str | None = field(default=None, repr=False)
    train_departure_flag: str | None = None
    train_no: str | None = field(default=None, repr=False)
    special_train_flag: str | None = None
    up_down_division_code: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TransferStation:
    station_code: str | None = field(default=None, repr=False)
    station_name: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class TransferStationListResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    stations: tuple[TransferStation, ...] = ()


@dataclass(frozen=True)
class LoginCryptoInfo:
    idx: str = ""
    key: str = ""
    pwd_aes_cphd: str = "N"


@dataclass(frozen=True)
class TrainSearchQuery:
    departure_station_code: str
    arrival_station_code: str
    departure_date: str
    departure_time: str = "000000"
    passengers: int = 1
    train_group_code: str = "109"
    include_srt: bool = False


def _train_optional_string(
    raw: dict[str, Any],
    key: str,
) -> str | None:
    value = raw.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL train field {key} must be a string or null"
        )
    return value


def _train_optional_int(
    raw: dict[str, Any],
    key: str,
) -> int | None:
    value = raw.get(key)
    if value is not None and type(value) is not int:
        raise KorailProtocolError(
            f"KORAIL train field {key} must be an integer or null"
        )
    return value


@dataclass(frozen=True)
class TrainSummary:
    train_no: str
    train_group_code: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    run_date: str | None = None
    train_class_code: str | None = None
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    seat_map_flag: str | None = None
    general_reservation_code: str | None = None
    departure_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    arrival_construction_order: str | None = field(default=None, repr=False)
    seat_attribute_code: str | None = field(default=None, repr=False)
    car_type_code: str | None = field(default=None, repr=False)
    car_type_name: str | None = field(default=None, repr=False)
    train_class_name: str | None = field(default=None, repr=False)
    train_group_name: str | None = field(default=None, repr=False)
    general_room_class_name: str | None = field(default=None, repr=False)
    special_room_class_name: str | None = field(default=None, repr=False)
    secondary_general_reservation_code: str | None = field(
        default=None,
        repr=False,
    )
    special_reservation_code: str | None = field(default=None, repr=False)
    secondary_special_reservation_code: str | None = field(
        default=None,
        repr=False,
    )
    free_reservation_code: str | None = field(default=None, repr=False)
    standing_reservation_code: str | None = field(default=None, repr=False)
    general_availability_name: str | None = field(default=None, repr=False)
    special_availability_name: str | None = field(default=None, repr=False)
    wait_reservation_flag: str | None = field(default=None, repr=False)
    standard_remaining_seat_count: str | None = field(
        default=None,
        repr=False,
    )
    first_class_remaining_seat_count: str | None = field(
        default=None,
        repr=False,
    )
    free_car_count: str | None = field(default=None, repr=False)
    reservation_wait_passenger_count: str | None = field(
        default=None,
        repr=False,
    )
    total_passenger_count: int | None = None
    goods_no: str | None = field(default=None, repr=False)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "TrainSummary":
        return cls(
            train_no=str(raw.get("h_trn_no") or raw.get("trnNo") or ""),
            train_group_code=raw.get("h_trn_gp_cd") or raw.get("trnGpCd"),
            departure_station_code=raw.get("h_dpt_rs_stn_cd") or raw.get("dptRsStnCd"),
            arrival_station_code=raw.get("h_arv_rs_stn_cd") or raw.get("arvRsStnCd"),
            departure_station_name=raw.get("h_dpt_rs_stn_nm") or raw.get("dptRsStnNm"),
            arrival_station_name=raw.get("h_arv_rs_stn_nm") or raw.get("arvRsStnNm"),
            departure_date=raw.get("h_dpt_dt") or raw.get("dptDt"),
            departure_time=raw.get("h_dpt_tm") or raw.get("dptTm"),
            arrival_time=raw.get("h_arv_tm") or raw.get("arvTm"),
            run_date=raw.get("h_run_dt") or raw.get("runDt"),
            train_class_code=(
                raw.get("h_trn_clsf_cd") or raw.get("trnClsfCd")
            ),
            departure_run_order=(
                raw.get("h_dpt_stn_run_ordr")
                or raw.get("dptStnRunOrdr")
            ),
            arrival_run_order=(
                raw.get("h_arv_stn_run_ordr")
                or raw.get("arvStnRunOrdr")
            ),
            seat_map_flag=raw.get("h_rd_seat_map_flg"),
            general_reservation_code=raw.get("h_gen_rsv_cd"),
            departure_construction_order=_train_optional_string(
                raw,
                "h_dpt_stn_cons_ordr",
            ),
            arrival_construction_order=_train_optional_string(
                raw,
                "h_arv_stn_cons_ordr",
            ),
            seat_attribute_code=_train_optional_string(
                raw,
                "h_seat_att_cd",
            ),
            car_type_code=_train_optional_string(raw, "h_car_tp_cd"),
            car_type_name=_train_optional_string(raw, "h_car_tp_nm"),
            train_class_name=_train_optional_string(raw, "h_trn_clsf_nm"),
            train_group_name=_train_optional_string(raw, "h_trn_gp_nm"),
            general_room_class_name=_train_optional_string(
                raw,
                "h_gen_psrm_cl_nm",
            ),
            special_room_class_name=_train_optional_string(
                raw,
                "h_spe_psrm_cl_nm",
            ),
            secondary_general_reservation_code=_train_optional_string(
                raw,
                "h_gen_rsv_cd2",
            ),
            special_reservation_code=_train_optional_string(
                raw,
                "h_spe_rsv_cd",
            ),
            secondary_special_reservation_code=_train_optional_string(
                raw,
                "h_spe_rsv_cd2",
            ),
            free_reservation_code=_train_optional_string(
                raw,
                "h_free_rsv_cd",
            ),
            standing_reservation_code=_train_optional_string(
                raw,
                "h_stnd_rsv_cd",
            ),
            general_availability_name=_train_optional_string(
                raw,
                "h_rsv_psb_nm",
            ),
            special_availability_name=_train_optional_string(
                raw,
                "h_spe_rsv_psb_nm",
            ),
            wait_reservation_flag=_train_optional_string(
                raw,
                "h_wait_rsv_flg",
            ),
            standard_remaining_seat_count=_train_optional_string(
                raw,
                "h_std_rest_seat_cnt",
            ),
            first_class_remaining_seat_count=_train_optional_string(
                raw,
                "h_fst_rest_seat_cnt",
            ),
            free_car_count=_train_optional_string(
                raw,
                "h_free_sracar_cnt",
            ),
            reservation_wait_passenger_count=_train_optional_string(
                raw,
                "h_rsv_wait_ps_cnt",
            ),
            total_passenger_count=_train_optional_int(raw, "totPsgCnt"),
            # x4/b.java:23 sources the seat-search txtGdNo from
            # trainInfo.getTxtGdNo(); capture the goods number from the train
            # row (h_gd_no / txtGdNo) so the seat-map builders can forward it.
            goods_no=(
                _train_optional_string(raw, "h_gd_no")
                or _train_optional_string(raw, "txtGdNo")
            ),
            raw=raw,
        )


@dataclass(frozen=True)
class SeatAttribute:
    name: str
    code: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class SeatCar:
    car_no: int
    room_class_name: str
    remaining_seat_count: int
    attributes: tuple[SeatAttribute, ...]
    room_class_code: str | None = field(default=None, repr=False)
    total_seat_count: int | None = None


@dataclass(frozen=True)
class SeatCarListResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    recommended_car_no: int | None = None
    train_no: str | None = field(default=None, repr=False)
    cars: tuple[SeatCar, ...] = ()
    train_class_code: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class PhysicalSeat:
    seat_no: str = field(repr=False)
    sale_possible: str
    direction_code: str
    other_attribute_code: str
    requested_attribute_code: str
    floor: str | None
    specification: str
    sequence_no: str
    message_code: str
    message: str = field(repr=False)
    visual_message_division_code: str


@dataclass(frozen=True)
class SeatWindow:
    start_location_ratio: float
    close_location_ratio: float


@dataclass(frozen=True)
class SeatInventoryResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    layout_type: int = 0
    arrangement_code: str = ""
    remaining_count: int = 0
    total_count: int = 0
    seats: tuple[PhysicalSeat, ...] = ()
    windows: tuple[SeatWindow, ...] = ()
    vr_banner_url: str | None = field(default=None, repr=False)
    car_type_code: str | None = field(default=None, repr=False)
    car_no: int | None = None
    up_down_division_code: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TrainSearchMetadata:
    menu_id: str | None = field(default=None, repr=False)
    job_id: str | None = field(default=None, repr=False)
    product_no: str | None = field(default=None, repr=False)
    next_page_flag: str | None = None
    next_query_station_no: str | None = field(default=None, repr=False)
    next_train_no: str | None = field(default=None, repr=False)
    result_count: str | None = None
    first_seat_count: str | None = None
    second_seat_count: str | None = None
    first_departure_time: str | None = field(default=None, repr=False)
    merge_reservation_available_flag: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class TrainSearchResult:
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)
