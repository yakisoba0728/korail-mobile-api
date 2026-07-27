from dataclasses import dataclass, field
from typing import Any

from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_TRANSFER_ITINERARY_CODE,
)
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
    # The two 환승 markers a ScheduleView row carries
    # (RsvInquiryResponse.java:75-76, getters at :171/:175).
    #
    # ``change_train_sequence`` (``h_chg_trn_seq``) is the leg's position inside
    # its itinerary, and the app reads it against K4/d's codes -- "1" for a
    # first leg, "2" for a second. Two independent places test it that way:
    # u4/a.java:111-131 de-duplicates a newly fetched page against the rows
    # already held by finding a ``"2"`` row that matches one it has and dropping
    # that row TOGETHER WITH ITS PREDECESSOR (`list2.get(i - 1)`), and
    # RsvInquiryRequest.java:164-172 seeds the next page's ``txtGoHour`` from
    # the last row when that row is a ``"1"`` and from the second-to-last
    # otherwise. Both only make sense if a ``"2"`` row is the back half of a
    # pair whose front half is the row before it.
    #
    # ``change_train_division_code`` (``h_chg_trn_dv_cd``) is the row's 환승
    # division; DirectInquiryActivity.java:194 defaults a null one to
    # ``DIRECT_SQ_NO`` before forwarding it as ``chtnDvCd``. A direct search
    # leaves both null, which is why both default to ``None`` here rather than
    # to a code.
    change_train_sequence: str | None = field(default=None, repr=False)
    change_train_division_code: str | None = field(default=None, repr=False)
    # ``h_yms_apl_flg``: the only input to the app's 병합 (입석+좌석) test.
    # S4/J.java:61-63's isMixedSeat(cabin, flag) reads nothing else off the row,
    # and a5/u.java:378-380 feeds each row's value into it to decide whether the
    # booking button becomes 입석+좌석 예매 with tag "1202" (:394-397). Named for
    # what it decides rather than for the abbreviation: the same field is
    # already parsed under a guessed expansion elsewhere in this package, and
    # only this call site shows what it is actually consulted for. See
    # KORAIL_MERGE_SEAT_FLAGS_BY_CABIN.
    merge_seat_application_flag: str | None = field(default=None, repr=False)

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
            change_train_sequence=_train_optional_string(
                raw,
                "h_chg_trn_seq",
            ),
            change_train_division_code=_train_optional_string(
                raw,
                "h_chg_trn_dv_cd",
            ),
            merge_seat_application_flag=_train_optional_string(
                raw,
                "h_yms_apl_flg",
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
    # No menu_id: there is no h_menu_id in the ScheduleView response. The app's
    # txtMenuId is a client-side constant ("11" from a5/k.java:92-94, carried
    # to PriceFareActivity as the MENU_ID intent extra), never a server value —
    # h_menu_id has zero hits across the whole decompiled app.
    job_id: str | None = field(default=None, repr=False)
    product_no: str | None = field(default=None, repr=False)
    next_page_flag: str | None = None
    next_query_station_no: str | None = field(default=None, repr=False)
    next_train_no: str | None = field(default=None, repr=False)
    # The 환승 half of the cursor. b5/c.java:370-371 stashes h_prcd_trn_no_next
    # and h_ectb_trn_no_next beside the three fields above, and :192-194 replays
    # them through setSelectTransferPages -- which overwrites qryStTrnNo with
    # the first and sets qryStTrnNo2 to the second (RsvInquiryRequest.java:
    # 212-215) -- but only when BOTH are non-empty. A direct search leaves them
    # empty, which is why a direct next page keeps qryStTrnNo = h_trn_no_next
    # and qryStTrnNo2 = "".
    next_preceding_train_no: str | None = field(default=None, repr=False)
    next_connecting_train_no: str | None = field(default=None, repr=False)
    result_count: str | None = None
    #: ``h_notice_msg`` — the notice the server attaches to a search
    #: (``RsvInquiryResponse.java:12``). Declared by the app's own DTO, and read
    #: by the sibling parsers that return this same shape
    #: (``read_parsers.py``, ``limousine_parsers.py``); this parser was the only
    #: one that dropped it.
    notice_message: str | None = None
    # WARNING -- the four fields below are NOT attested by the APK. Each of
    # strJobId / h_seat_cnt_first / h_seat_cnt_second / txtGoHour_first occurs
    # in ZERO files across analysis/, while RsvInquiryResponse.java:8-17
    # declares exactly nine top-level fields and none of these is among them.
    # They are kept because removing a public attribute would break callers,
    # not because they are evidenced: expect them to be None against a real
    # server. Compare h_menu_id, which was excluded from this very model for
    # exactly this reason -- the same standard simply had not been applied
    # here. The fixture that exercises them uses SYNTHETIC- values, so the test
    # covering them proves only that the parser reads keys it was written to
    # read.
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
class TrainSearchContinuation:
    """The follow-up-page cursor the app carries between ScheduleView calls.

    The app keeps the previous response's paging fields on the search screen
    (``b5/c.java:367-371``) and, when the user asks for more results, replays
    them into the next request (``b5/c.java:184-194``):
    ``setNextTimeTC(h_qry_st_no_next, h_trn_no_next)`` sets ``qryStNo`` and
    ``qryStTrnNo`` (``RsvInquiryRequest.java:174-177``) and
    ``setSelectTransferPage(h_qry_st_no_next, h_rslt_cnt)`` sets ``qryStNo``
    and ``pgPrCnt`` (``:207-210``).

    ``query_train_no2`` is the fourth cursor and belongs to a 환승 search.
    ``b5/c.java:192-194`` calls ``setSelectTransferPages`` only when both
    ``h_prcd_trn_no_next`` and ``h_ectb_trn_no_next`` came back non-empty, and
    that call overwrites ``qryStTrnNo`` with the first and sets ``qryStTrnNo2``
    to the second (``RsvInquiryRequest.java:212-215``). A direct search never
    populates the pair, so a direct continuation carries the empty-string
    default and puts the first page's ``qryStTrnNo2 = ""`` back on the wire --
    unchanged from before this field existed. It is therefore the one field
    here that is allowed to be empty.

    Build one with :meth:`TrainSearchResult.next_page` or
    :meth:`TransferSearchResult.next_page` rather than by hand.
    """

    query_station_no: str = field(repr=False)
    query_train_no: str = field(repr=False)
    page_count: str = "10"
    query_train_no2: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        for name in ("query_station_no", "query_train_no", "page_count"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"TrainSearchContinuation.{name} must be a non-empty string"
                )
        if not isinstance(self.query_train_no2, str):
            raise ValueError(
                "TrainSearchContinuation.query_train_no2 must be a string"
            )


@dataclass(frozen=True)
class TrainSearchResult:
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """Cursor for the page after this one, or ``None`` when there is none.

        Mirrors the app's own gate: ``b5/c.java:381-387`` only keeps the
        "more results" affordance alive while ``h_next_pg_flg`` equals ``"Y"``.
        ``None`` is also returned when the response withheld a cursor field,
        because a half-filled cursor would silently re-request page one.
        """
        metadata = self.metadata
        if metadata.next_page_flag != "Y":
            return None
        try:
            return TrainSearchContinuation(
                query_station_no=metadata.next_query_station_no or "",
                query_train_no=metadata.next_train_no or "",
                page_count=metadata.result_count or "10",
            )
        except ValueError:
            return None


@dataclass(frozen=True)
class TransferItinerary:
    """One 환승 itinerary: the two legs a transfer reservation books together.

    A transfer ScheduleView response does NOT nest its legs, and it does not
    return a separate itinerary object either. It returns the same flat
    ``trn_infos.trn_info`` list a direct search returns, and the app pairs it up
    **positionally**:

    * ``a5/k.java:142-172`` (``P0``) walks the list and, on the ``!isDirect``
      branch, opens a fresh ``new Bundle[2]`` whenever ``i % 2 == 0`` and only
      appends the row once ``i % 2 == 1`` -- so rows 0/1 are one itinerary,
      rows 2/3 the next, and a trailing unpaired row is silently dropped.
    * ``a5/k.java:108-110`` (``E0``) reads a selected itinerary straight back
      out of the flat list as ``{list[i * 2], list[i * 2 + 1]}``, and that array
      is exactly what the reservation's journey builder receives
      (``a5/u.java:495``/``:938`` call ``N0(E0())``).
    * ``a5/u.java:947-956`` names the transfer station the same way, off
      ``f236n.get(i * 2)`` and ``f236n.get(i * 2 + 1)``.

    ``h_chg_trn_seq`` is the server's own copy of that position -- ``"1"`` on a
    first leg, ``"2"`` on a second. This class uses the positional pairing the
    app uses, and treats the sequence markers, when the server populates them,
    as a consistency check rather than as the pairing key; see
    :func:`pair_transfer_itineraries`.
    """

    first: TrainSummary
    second: TrainSummary

    @property
    def legs(self) -> tuple[TrainSummary, ...]:
        """The itinerary's legs in boarding order, ready for ``reserve_transfer``."""
        return (self.first, self.second)

    @property
    def transfer_station_code(self) -> str | None:
        """Where the passenger changes trains, or ``None`` if the legs disagree.

        The app never sends this as a field of its own: the change of trains is
        simply leg 1's arrival and leg 2's departure, which the reservation form
        restates as ``txtArvRsStnCd1`` and ``txtDptRsStnCd2``.

        ``None`` is a real answer, not a parse failure. ``a5/u.java:947-956``
        prints leg 1's arrival name and leg 2's departure name as two separate
        labels and only collapses them to one when they are equal, so KORAIL
        does return itineraries that arrive at one station and leave from
        another. Read :attr:`arrival_station_code <TrainSummary>` on
        :attr:`first` and :attr:`departure_station_code <TrainSummary>` on
        :attr:`second` when that case matters to you.
        """
        arrival = self.first.arrival_station_code
        if arrival is not None and arrival == self.second.departure_station_code:
            return arrival
        return None

    @property
    def transfer_station_name(self) -> str | None:
        """The transfer station's name under the same equal-or-``None`` rule."""
        arrival = self.first.arrival_station_name
        if arrival is not None and arrival == self.second.departure_station_name:
            return arrival
        return None


def pair_transfer_itineraries(
    trains: list[TrainSummary],
) -> list[TransferItinerary]:
    """Chunk a flat transfer result list into itineraries, the app's way.

    Mirrors ``a5/k.java:156-170`` exactly, including its treatment of a trailing
    odd row: the app adds a row to the rendered list only on ``i % 2 == 1``, so
    a final unpaired leg is dropped rather than shown as a bookable half.

    Raises :class:`KorailProtocolError` when the server populated
    ``h_chg_trn_seq`` on a row but not as ``"1"`` then ``"2"``. That check is
    this package's, not the app's -- the app pairs blind -- but a misaligned
    list would otherwise hand :meth:`KorailClient.reserve_transfer` two rows
    that are not one itinerary, and this package will not build a form it cannot
    justify. A response that omits the marker entirely is accepted, because
    ``DirectInquiryActivity.java:194-195`` and ``TransferInquiryActivity.java:44``
    both show the app defaulting a null marker from the row's position.
    """
    itineraries: list[TransferItinerary] = []
    for index in range(0, len(trains) - 1, 2):
        first = trains[index]
        second = trains[index + 1]
        _assert_leg_sequence(first, index, KORAIL_DIRECT_ITINERARY_CODE)
        _assert_leg_sequence(second, index + 1, KORAIL_TRANSFER_ITINERARY_CODE)
        itineraries.append(TransferItinerary(first=first, second=second))
    return itineraries


def _assert_leg_sequence(
    train: TrainSummary,
    index: int,
    expected: str,
) -> None:
    sequence = train.change_train_sequence
    if sequence is not None and sequence.strip() and sequence != expected:
        raise KorailProtocolError(
            "KORAIL transfer search returned a misaligned leg: row "
            f"{index} carries h_chg_trn_seq {sequence!r}, expected {expected!r}"
        )


@dataclass(frozen=True)
class TransferSearchResult:
    """One page of 환승 itineraries.

    ``trains`` is the untouched flat row list the server sent, in server order;
    ``itineraries`` is that list paired up by :func:`pair_transfer_itineraries`.
    Both are exposed because the app keeps both too -- ``a5/k.java``'s ``f236n``
    is the flat list it indexes with ``i * 2`` and ``f237o`` is the paired one
    it renders.
    """

    itineraries: list[TransferItinerary]
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """Cursor for the page after this one, or ``None`` when there is none.

        Same ``h_next_pg_flg == "Y"`` gate as a direct search
        (``b5/c.java:381-387``), but the cursor is not the same cursor. A
        transfer page comes back with two extra fields, and ``b5/c.java:192-194``
        replays them through ``setSelectTransferPages``, which overwrites
        ``qryStTrnNo`` with ``h_prcd_trn_no_next`` and sets ``qryStTrnNo2`` to
        ``h_ectb_trn_no_next`` (``RsvInquiryRequest.java:212-215``). The app
        applies that overwrite only when BOTH are non-empty, so this does too:
        with either missing the cursor stays the direct-search one built at
        ``:186``/``:190`` from ``h_trn_no_next``.
        """
        metadata = self.metadata
        if metadata.next_page_flag != "Y":
            return None
        preceding = metadata.next_preceding_train_no or ""
        connecting = metadata.next_connecting_train_no or ""
        transfer_cursor = bool(preceding.strip()) and bool(connecting.strip())
        try:
            return TrainSearchContinuation(
                query_station_no=metadata.next_query_station_no or "",
                query_train_no=(
                    preceding if transfer_cursor else metadata.next_train_no or ""
                ),
                page_count=metadata.result_count or "10",
                query_train_no2=connecting if transfer_cursor else "",
            )
        except ValueError:
            return None
