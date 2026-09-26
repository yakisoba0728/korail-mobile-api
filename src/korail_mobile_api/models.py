# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Self

from .errors import KorailProtocolError


@dataclass(frozen=True)
class KorailSession:
    """로그인 쿠키와 계정 식별자를 보관합니다.

    고객번호(``customer_no``)와 회원번호(``member_no``)는 서로 다른 값입니다. ``raw``와 ``repr()``은 개인정보를 가리지
    않으므로 로그에 남기지 마세요."""

    jsessionid: str | None = None
    member_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    member_card_no: str | None = None
    customer_no: str | None = None


@dataclass(frozen=True)
class BaseKorailResponse:
    """응답의 공통 상태·메시지와 원본을 담습니다.

    ``str_result``, ``h_msg_cd``, ``h_msg_txt``는 모든 응답에 공통인 봉투 필드이며, ``raw``에는 서버가 보낸 응답이 그대로
    남습니다."""

    # from_raw는 봉투 타입만 검사하며, 성공·실패 판정은 http.parse_base_response가 맡습니다.

    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)

    @classmethod
    def from_raw(cls, raw: object) -> Self:
        """봉투 세 필드를 그대로 옮겨 담아 응답을 만듭니다.

        성공·실패는 판정하지 않습니다. ``raw``가 JSON 객체가 아니거나 봉투 필드가 문자열·정수·``null``이 아니면
        ``KorailProtocolError``가 발생합니다."""
        from ._parsing import _envelope

        if not isinstance(raw, dict):
            error = KorailProtocolError("KORAIL response must be a JSON object")
            error.raw = raw
            raise error
        envelope = _envelope(raw)
        return cls(
            h_msg_cd=envelope["h_msg_cd"],
            h_msg_txt=envelope["h_msg_txt"],
            str_result=envelope["strResult"],
            raw=raw,
        )


@dataclass(frozen=True)
class AppVersionInfo:
    """앱 버전과 업데이트 안내 주소를 담습니다."""

    message: str | None = None
    new_version: str | None = None
    # 근거: MobilePlusMainVersion.java:52; AppKt.java:1240,1323,1635.
    #: 앱 업데이트 안내 주소(``CNTAURL``)입니다.
    store_url: str | None = None


@dataclass(frozen=True)
class AppDataResponse(BaseKorailResponse):
    """앱 메인 캐시의 버전·공지 정보를 담습니다."""

    disability_certification_msg: str | None = None
    railplus_cardinfo: str | None = None
    version: AppVersionInfo | None = None
    notice: "NoticeResponse | None" = None


@dataclass(frozen=True)
class NoticeResponse(BaseKorailResponse):
    """앱 메인 화면의 공지를 담습니다."""

    board_id: str | None = None
    post_sequence: str | None = None
    post_title: str | None = None
    post_content: str | None = None


@dataclass(frozen=True)
class UuidResponse(BaseKorailResponse):
    """서버가 발급한 단말 검증값을 담습니다."""

    verification_code: str | None = None


@dataclass(frozen=True)
class MaasMenuItem:
    """부가서비스 메뉴 한 항목과 역 선택 조건을 담습니다."""

    active: str | None = None
    additional_service_code: str | None = None
    app_data: str | None = None
    icon_off: str | None = None
    icon_on: str | None = None
    info: str | None = None
    login_required: str | None = None
    name: str | None = None
    popup_image: str | None = None
    menu_type: str | None = None
    url: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)

    @property
    def uses_station_selection(self) -> bool:
        """메뉴가 역 선택을 사용하는지 판정합니다.

        ``active``가 ``"Y"``이고, ``menu_type``이 ``"N"``이 아니고, ``app_data``가 비어 있지 않으면서 ``"N"``도 아니고,
        ``additional_service_code``가 있을 때 ``True``입니다."""
        return (
            self.active == "Y"
            and self.menu_type != "N"
            # appData='N'만 역 선택에서 제외합니다. 실서버 관측: 'C'(604)는 역 15개, 'N'(001)은 0개, 'Y'·'M30'은 25~111개였으므로 Y·M10·M30만 허용하는
            # 방식으로 제한하지 않습니다.
            and self.app_data not in (None, "", "N")
            and isinstance(self.additional_service_code, str)
            and bool(self.additional_service_code.strip())
        )


@dataclass(frozen=True)
class MaasMenuListResponse(BaseKorailResponse):
    """부가서비스 메뉴 목록을 담습니다."""

    items: tuple[MaasMenuItem, ...] = ()
    departure_elevator_url: str | None = None
    departure_navigation_url: str | None = None
    departure_parking_url: str | None = None
    arrival_elevator_url: str | None = None
    arrival_bus_info_url: str | None = None
    arrival_parking_url: str | None = None
    arrival_baggage_transfer_robot_url: str | None = None


@dataclass(frozen=True)
class KorailStation:
    """역 코드·이름과 역별 안내 정보를 담습니다."""

    code: str
    name: str
    longitude: str | None = None
    latitude: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    group: str | None = None
    major: str | None = None
    # popupType 은 String 선언이므로 문자열로 유지합니다(StationDataOutStnItem.java:60).
    #: 역 안내 팝업의 종류(``popupType``)입니다. 서버가 정수로 보내도 문자열로 담습니다.
    popup_type: str | None = None
    popup_message: str | None = None
    popup_link_title: str | None = None
    popup_link_url: str | None = None
    area: str | None = None
    stop: str | None = None


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    """전체 역 목록을 담습니다."""

    stations: tuple[KorailStation, ...] = ()


@dataclass(frozen=True)
class StationInfoResponse(BaseKorailResponse):
    """역 데이터의 판본과 역 수를 담습니다."""

    # count 는 String 선언이므로 정수로 바꾸지 않습니다(StationInfoOut.java:47).
    #: 역 수입니다. 정수로 바꾸지 않고 문자열로 담습니다.
    count: str = ""
    map_version: str | None = None


@dataclass(frozen=True)
class TrainCalendarDay:
    """열차 운행일 한 날짜와 예매 조건을 담습니다."""

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
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class TrainCalendarResponse(BaseKorailResponse):
    """예매 가능한 운행일 달력을 담습니다."""

    days: tuple[TrainCalendarDay, ...] = ()


@dataclass(frozen=True)
class TrainScheduleStop:
    """열차의 정차역 한 곳과 도착·출발 정보를 담습니다."""

    station_code: str | None = None
    station_name: str | None = None
    station_construction_order: str | None = None
    run_order: str | None = None
    actual_arrival_delay_count: str | None = None
    actual_arrival_date: str | None = None
    actual_arrival_time: str | None = None
    actual_departure_date: str | None = None
    actual_departure_time: str | None = None
    planned_arrival_date: str | None = None
    planned_arrival_time: str | None = None
    planned_departure_date: str | None = None
    planned_departure_time: str | None = None
    delay_fare_return_division_code: str | None = None
    delay_fare_return_division_name: str | None = None
    solo_operation_delay_flag: str | None = None
    detour_driver_delay_count: str | None = None
    expected_arrival_delay_count: str | None = None
    expected_departure_delay_count: str | None = None
    regular_flag: str | None = None
    service_flag: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class TrainScheduleResponse(BaseKorailResponse):
    """열차 한 편의 정차역 목록을 담습니다."""

    delay_detail_reason_content: str | None = None
    stops: tuple[TrainScheduleStop, ...] = ()
    delay_station_construction_order: str | None = None
    integrated_message_code: str | None = None
    message_code: str | None = None
    message_content: str | None = None
    message_text: str | None = None
    origin_station_code: str | None = None
    origin_station_name: str | None = None
    route_code: str | None = None
    route_name: str | None = None
    run_date: str | None = None
    run_segment_order: str | None = None
    regular_sale_flag: str | None = None
    standard_train_class_code: str | None = None
    terminal_station_code: str | None = None
    terminal_station_name: str | None = None
    train_attribute_code: str | None = None
    train_departure_flag: str | None = None
    train_no: str | None = None
    special_train_flag: str | None = None
    up_down_division_code: str | None = None


@dataclass(frozen=True)
class TransferStation:
    """환승 가능한 역 한 곳을 나타냅니다."""

    station_code: str | None = None
    station_name: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class TransferStationListResponse(BaseKorailResponse):
    """환승 가능한 역 목록을 담습니다."""

    stations: tuple[TransferStation, ...] = ()


@dataclass(frozen=True)
class LoginCryptoInfo:
    idx: str = ""
    key: str = ""
    pwd_aes_cphd: str = "N"


@dataclass(frozen=True)
class TrainSearchQuery:
    """직통·환승 열차의 조회 조건을 구성합니다.

    출발역·도착역에 숫자로만 된 역 코드를 넣으면 클라이언트가 역 목록을 조회해 역 이름으로 바꿔 보내고, 그 밖의 값은 역
    이름으로 보고 그대로 보냅니다. 앱이 쓰는 열차군·조회 구분 코드는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    기본값과 다른 값이 필요하면 ``train_group_code``와 ``query_division_code``를 직접 지정하세요."""

    # 열차군·정렬 코드는 보호돼 있어 관측값 또는 명시값을 씁니다(TrainGroup.java:25,29,335).

    departure_station_code: str
    arrival_station_code: str
    departure_date: str
    departure_time: str = "000000"
    passengers: int = 1
    train_group_code: str = "109"
    include_srt: bool = False
    child_passengers: int = 0
    senior_passengers: int = 0
    high_disability_passengers: int = 0
    low_disability_passengers: int = 0
    seat_attribute_code: str = "015"
    connection_station_codes: tuple[str, ...] = ()
    connection_train_group_code: str | None = None
    # 앱의 정렬 선택별 값은 보호되어 있으므로 전송 코드를 직접 지정합니다.
    #: 조회 구분 코드(``qryDvCd``)입니다. 앱의 정렬 선택별 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했으므로, 다른 값이
    #: 필요하면 직접 지정하세요.
    query_division_code: str = "1"
    # 근거: TrainScheduleViewModel.java:280-306,3050-3075.
    #: 청소년 승객 수입니다. 앱처럼 청소년·안내견은 어른 칸(``txtPsgFlg_1``)에, 유아는 어린이 칸(``txtPsgFlg_2``)에 더해
    #: 보냅니다.
    teenager_passengers: int = 0
    infant_passengers: int = 0
    guide_dog_passengers: int = 0


def _train_scalar(value: object, key: str, *, required: bool = False) -> str | None:
    """String 선언(TrainScheduleOutTrainInfo.java:63,1152)보다 넓게 받는 라이브러리 정책이며 앱 Json 설정은 보호돼
    있습니다(NetworkModule.java:862, NetworkServiceKt.java:29). 그 밖의 모양은 선택 필드면 None, ``required`` (train_no)면
    KorailProtocolError 입니다."""
    if value is None or isinstance(value, str):
        return value
    # bool 을 숫자로 받지 않도록 정확한 int 타입만 허용합니다.
    if type(value) is int:
        try:
            return str(value)
        except ValueError:
            pass
    if required:
        raise KorailProtocolError(f"KORAIL train field {key} must be a string, an integer, or null")
    return None


def _train_optional_int(
    raw: Mapping[str, object],
    key: str,
) -> int | None:
    # 선택 필드라 정수가 아니면 None 입니다(bool 도 정수로 치지 않음).
    value: object = raw.get(key)
    return value if type(value) is int else None


#: 세 번째 칸이 있으면 첫 키가 없거나 거짓일 때(정수 0 제외) 그 철자를 읽습니다(``h_trn_gp_cd`` 와 ``trnGpCd`` 등). 오류는 언제나 첫 키 이름으로 냅니다.
_TRAIN_SUMMARY_KEYS: tuple[tuple[str, str, str | None], ...] = (
    ("train_group_code", "h_trn_gp_cd", "trnGpCd"),
    ("departure_station_code", "h_dpt_rs_stn_cd", "dptRsStnCd"),
    ("arrival_station_code", "h_arv_rs_stn_cd", "arvRsStnCd"),
    ("departure_station_name", "h_dpt_rs_stn_nm", "dptRsStnNm"),
    ("arrival_station_name", "h_arv_rs_stn_nm", "arvRsStnNm"),
    ("departure_date", "h_dpt_dt", "dptDt"),
    ("departure_time", "h_dpt_tm", "dptTm"),
    ("arrival_time", "h_arv_tm", "arvTm"),
    #: ``h_arv_dt`` 도착일(TrainScheduleOutTrainInfo.java:1068).
    ("arrival_date", "h_arv_dt", None),
    ("run_date", "h_run_dt", "runDt"),
    ("train_class_code", "h_trn_clsf_cd", "trnClsfCd"),
    ("departure_run_order", "h_dpt_stn_run_ordr", "dptStnRunOrdr"),
    ("arrival_run_order", "h_arv_stn_run_ordr", "arvStnRunOrdr"),
    ("seat_map_flag", "h_rd_seat_map_flg", None),
    ("general_reservation_code", "h_gen_rsv_cd", None),
    #: ``h_gen_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:83``. 일반실 예약가능 플래그 원래 값(코드가 아니라 플래그).
    ("general_reservation_flag", "h_gen_rsv_flg", None),
    ("departure_construction_order", "h_dpt_stn_cons_ordr", None),
    ("arrival_construction_order", "h_arv_stn_cons_ordr", None),
    ("seat_attribute_code", "h_seat_att_cd", None),
    ("car_type_code", "h_car_tp_cd", None),
    ("car_type_name", "h_car_tp_nm", None),
    ("train_class_name", "h_trn_clsf_nm", None),
    ("train_group_name", "h_trn_gp_nm", None),
    ("general_room_class_name", "h_gen_psrm_cl_nm", None),
    ("special_room_class_name", "h_spe_psrm_cl_nm", None),
    ("secondary_general_reservation_code", "h_gen_rsv_cd2", None),
    ("special_reservation_code", "h_spe_rsv_cd", None),
    #: ``h_spe_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:108`` (Java 필드명 ``hSpRsvFlg``).
    ("special_reservation_flag", "h_spe_rsv_flg", None),
    ("secondary_special_reservation_code", "h_spe_rsv_cd2", None),
    ("free_reservation_code", "h_free_rsv_cd", None),
    #: ``h_free_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:75``.
    ("free_reservation_flag", "h_free_rsv_flg", None),
    ("standing_reservation_code", "h_stnd_rsv_cd", None),
    #: ``h_stnd_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:151`` (Java 필드명 ``h_stnd_rsv_flg`` 그대로).
    ("standing_reservation_flag", "h_stnd_rsv_flg", None),
    #: ``h_rsv_psb_flg`` -- ``TrainScheduleOutTrainInfo.java:100``.
    ("reservation_available_flag", "h_rsv_psb_flg", None),
    ("general_availability_name", "h_gen_rsv_nm", None),
    ("special_availability_name", "h_spe_rsv_nm", None),
    #: ``TrainScheduleOutTrainInfo.java:1380``/``:1196`` 의 ``@SerialName`` 이고, 합성 생성자(``:172``)에서 이미 읽고 있던 일반실
    #: ``h_gen_rsv_nm``(str42)·특실 ``h_spe_rsv_nm``(str47) 바로 옆의 str51/str53 입니다.
    ("standing_availability_name", "h_stnd_rsv_nm", None),
    ("free_availability_name", "h_free_rsv_nm", None),
    ("general_fare_text", "h_rsv_psb_nm", None),
    ("special_fare_text", "h_spe_rsv_psb_nm", None),
    ("wait_reservation_flag", "h_wait_rsv_flg", None),
    ("standard_remaining_seat_count", "h_std_rest_seat_cnt", None),
    ("first_class_remaining_seat_count", "h_fst_rest_seat_cnt", None),
    #: ``h_free_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:73``.
    ("free_remaining_seat_count", "h_free_rest_seat_cnt", None),
    #: ``h_stnd_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:150`` (Java 필드명 ``h_stnd_rest_seat_cnt``
    #: 그대로).
    ("standing_remaining_seat_count", "h_stnd_rest_seat_cnt", None),
    #: 관측: 이 값이 "000" 이 아닌 열차만 자유석 호차 조회에 호차가 있었습니다(KorailClient.get_free_seat_car_info 참고).
    ("free_car_count", "h_free_sracar_cnt", None),
    ("reservation_wait_passenger_count", "h_rsv_wait_ps_cnt", None),
    ("train_sequence", "h_trn_seq", None),
    ("change_train_sequence", "h_chg_trn_seq", None),
    ("change_train_division_code", "h_chg_trn_dv_cd", None),
    ("merge_seat_application_flag", "h_yms_apl_flg", None),
    ("train_suspension_flag", "h_trn_sps_flg", None),
)


def _train_value(
    raw: Mapping[str, object], key: str, fallback: str | None, *, required: bool = False
) -> str | None:
    value = raw.get(key)
    if fallback is not None and type(value) is not int:
        value = value or raw.get(fallback)
    return _train_scalar(value, key, required=required)


@dataclass(frozen=True)
class TrainSummary:
    """열차 한 편의 식별자·예약 상태·운임 표시를 담습니다.

    좌석 예약 상태(``general_reservation_code`` 등)와 운임 문구(``general_fare_text``, ``special_fare_text``)는 서로 다른
    필드입니다."""

    # 식별값은 후속 예약 때 서버가 다시 검증합니다(실서버 관측).

    train_no: str
    train_group_code: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    run_date: str | None = None
    train_class_code: str | None = None
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    seat_map_flag: str | None = None
    general_reservation_code: str | None = None
    general_reservation_flag: str | None = None
    departure_construction_order: str | None = None
    arrival_construction_order: str | None = None
    seat_attribute_code: str | None = None
    car_type_code: str | None = None
    car_type_name: str | None = None
    train_class_name: str | None = None
    train_group_name: str | None = None
    general_room_class_name: str | None = None
    special_room_class_name: str | None = None
    secondary_general_reservation_code: str | None = None
    special_reservation_code: str | None = None
    special_reservation_flag: str | None = None
    secondary_special_reservation_code: str | None = None
    free_reservation_code: str | None = None
    free_reservation_flag: str | None = None
    standing_reservation_code: str | None = None
    standing_reservation_flag: str | None = None
    reservation_available_flag: str | None = None
    general_availability_name: str | None = None
    special_availability_name: str | None = None
    wait_reservation_flag: str | None = None
    standard_remaining_seat_count: str | None = None
    first_class_remaining_seat_count: str | None = None
    free_remaining_seat_count: str | None = None
    standing_remaining_seat_count: str | None = None
    free_car_count: str | None = None
    reservation_wait_passenger_count: str | None = None
    total_passenger_count: int | None = None
    goods_no: str | None = None
    # 근거: TrainScheduleViewModel.smali:36958-37040, TrainScheduleOutTrainInfo.java:1464.
    #: 열차 순번(``h_trn_seq``)입니다. 앱은 환승 조회 결과에서 이 값이 같은 두 행을 한 여정으로 묶습니다.
    train_sequence: str | None = None
    # h_chg_trn_seq 는 구간 순서(TrainScheduleOutTrainInfo.java:53,172,1112; TrainList.java:35,234). 관측: 직통 6질의의 행도
    # 모두 1, 환승 6여정 12구간은 1/2였습니다.
    #: 환승 여정 안에서 이 열차 구간의 순서(``h_chg_trn_seq``)입니다. ``train_sequence``와는 다른 값입니다.
    change_train_sequence: str | None = None
    # 관측: 직통 6질의는 1/직통, 환승 6여정 12구간은 2/환승이었습니다.
    #: 직통·환승 구분 코드(``h_chg_trn_dv_cd``)입니다.
    change_train_division_code: str | None = None
    # h_yms_apl_flg 선언: TrainScheduleOutTrainInfo.java:147,1480. 같은 DTO 의 isCombination/isSpecialCombination 이
    # 판정에 사용합니다 (TrainScheduleOutTrainInfo.java:1500-1552).
    #: 병합 좌석 적용 플래그(``h_yms_apl_flg``)입니다. 앱은 이 값으로 병합 좌석 여부를 판정합니다.
    merge_seat_application_flag: str | None = None
    train_suspension_flag: str | None = None
    general_fare_text: str | None = None
    special_fare_text: str | None = None
    standing_availability_name: str | None = None
    free_availability_name: str | None = None
    arrival_date: str | None = None

    @classmethod
    def from_raw(cls, raw: Mapping[str, object]) -> Self:
        """검색 응답의 행 하나를 ``TrainSummary``로 만듭니다.

        주요 값은 ``h_`` 접두 철자와 접두 없는 철자를 둘 다 찾습니다(``h_trn_no``와 ``trnNo`` 등). 정수로 온 값은 문자열로
        바꾸고, 선택 필드에 문자열·정수가 아닌 값이 오면 ``None``이 됩니다. ``train_no``에 문자열·정수·``null``이 아닌 값이
        오면 ``KorailProtocolError``가 발생합니다."""
        # 모든 스칼라는 _train_scalar 를 지납니다.
        return cls(
            train_no=_train_value(raw, "h_trn_no", "trnNo", required=True) or "",
            **{attr: _train_value(raw, key, fallback) for attr, key, fallback in _TRAIN_SUMMARY_KEYS},
            total_passenger_count=_train_optional_int(raw, "totPsgCnt"),
            # 예약 입력 없이 좌석을 조회하도록 행의 후보 상품번호를 보관하며 없으면 None입니다. h_gd_no는 봉투 선언이지 행 선언이
            # 아닙니다(TrainScheduleOut.java:29,184,232).
            goods_no=(_train_value(raw, "h_gd_no", None) or _train_value(raw, "txtGdNo", None)),
            raw=raw,
        )


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
class SeatAttribute:
    """좌석 속성 코드와 표시 이름을 담습니다."""

    name: str
    code: str | None = None


@dataclass(frozen=True)
class SeatCar:
    """좌석 조회에 사용할 호차 번호와 좌석 속성을 담습니다."""

    # 호차번호·잔여석은 mask 상 선택 String 입니다(TrainResearchOutCarInfo.java:59-85).
    #: 호차 번호입니다. 응답에 없거나 빈 문자열이면 ``None``입니다.
    car_no: int | None
    room_class_name: str
    #: 잔여 좌석 수입니다. 응답에 없거나 빈 문자열이면 ``None``입니다.
    remaining_seat_count: int | None
    attributes: tuple[SeatAttribute, ...]
    room_class_code: str | None = None
    total_seat_count: int | None = None


@dataclass(frozen=True)
class SeatCarListResponse(BaseKorailResponse):
    """열차 한 편의 조회 가능한 호차 목록을 담습니다."""

    recommended_car_no: int | None = None
    train_no: str | None = None
    cars: tuple[SeatCar, ...] = ()
    train_class_code: str | None = None
    train_group_code: str | None = None
    # h_scar_num 은 nullable String 선언입니다(TrainResearchOut.java:27,105).
    #: 호차 수(``h_scar_num``)입니다. 문자열로 담으며, 응답에 없거나 읽을 수 없으면 ``None``입니다.
    car_count: str | None = None


@dataclass(frozen=True)
class PhysicalSeat:
    """좌석표 한 자리의 식별자·표시·판매 가능 여부를 담습니다.

    좌석 지정에는 표시용 ``specification``이 아니라 식별자 ``seat_no``를 쓰세요. ``sale_possible``이 ``"Y"``인 좌석은
    ``KorailSeatAssignment.from_inventory()``로 좌석 지정 입력으로 바꿀 수 있습니다. ``floor``는 앱이 읽지 않는 값이며
    응답에 없으면 ``None``입니다."""

    # floor 는 앱 DTO 에 없습니다(TResidualSeatsResearchOutSeat.java:32-41).

    seat_no: str
    sale_possible: str
    direction_code: str
    other_attribute_code: str | None
    requested_attribute_code: str
    floor: str | None
    specification: str
    sequence_no: str
    message_code: str
    message: str
    visual_message_division_code: str | None


@dataclass(frozen=True)
class SeatWindow:
    """좌석 배치도의 창문 위치 비율을 담습니다.

    비율이 응답에 없거나 빈 문자열이면 ``None``입니다."""

    # 비율은 mask 상 선택 String 입니다(TResidualSeatsResearchOutWindow.java:51-56).

    start_location_ratio: float | None
    close_location_ratio: float | None


@dataclass(frozen=True)
class SeatInventoryResponse(BaseKorailResponse):
    """한 호차의 좌석 재고와 창문 위치를 담습니다.

    ``car_no``가 없으면 ``KorailSeatAssignment.from_inventory()``를 쓸 수 없으므로
    ``KorailSeatAssignment(car_no=..., seat_no=...)``로 직접 만드세요."""

    # layout_type 은 String 선언(TResidualSeatsResearchOut.java:29)이지만 서버 표본은 JSON 정수였습니다.
    #: 좌석 배치 형식입니다. 서버가 정수로 보내도 문자열로 담으며, 응답에 없으면 빈 문자열입니다.
    layout_type: str = ""
    arrangement_code: str = ""
    # 7.0.6 TResidualSeatsResearchOut DTO에는 seat_remain_count·seat_total_count 키가 없습니다.
    #: 잔여 좌석 수(``seat_remain_count``)입니다. 음이 아닌 정수로 읽을 수 없으면 ``None``입니다.
    remaining_count: int | None = None
    #: 전체 좌석 수(``seat_total_count``)입니다. 음이 아닌 정수로 읽을 수 없으면 ``None``입니다.
    total_count: int | None = None
    seats: tuple[PhysicalSeat, ...] = ()
    windows: tuple[SeatWindow, ...] = ()
    vr_banner_url: str | None = None
    car_type_code: str | None = None
    car_no: int | None = None
    up_down_division_code: str | None = None


@dataclass(frozen=True)
class TrainSearchMetadata:
    """열차 조회 결과의 공통 조건과 페이지 커서를 담습니다.

    ``next_page_flag``가 ``"Y"``여도 커서가 없으면 다음 페이지를 조회할 수 없습니다. 다음 조회에 넘길 값은 결과의
    ``next_page()``로 만드세요."""

    # 관측: 직통 6질의는 다음 페이지 Y 여도 필수 커서가 없었습니다.

    job_id: str | None = None
    menu_id: str | None = None
    product_no: str | None = None
    next_page_flag: str | None = None
    next_query_station_no: str | None = None
    next_train_no: str | None = None
    # 환승 커서 선언: TrainScheduleOut.java:28,33,67. 사용: TrainScheduleViewModel.java:7340.
    #: 다음 환승 조회에 넘길 선행 열차 번호 커서입니다.
    next_preceding_train_no: str | None = None
    next_connecting_train_no: str | None = None
    result_count: str | None = None
    # h_notice_msg 선언: TrainScheduleOut.java:32,67,196. 경고창: TrainScheduleViewModel.smali:36742-36786.
    #: 검색 안내 문구(``h_notice_msg``)입니다. 앱은 값이 있으면 경고창으로 보여 줍니다.
    notice_message: str | None = None
    first_seat_count: str | None = None
    second_seat_count: str | None = None
    first_departure_time: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )
    agreement_text: str | None = None
    remaining_seat_count: str | None = None


@dataclass(frozen=True)
class TrainSearchContinuation:
    """다음 열차 조회에 전달할 세 개의 커서 값을 담습니다.

    보통 직접 만들지 않고 조회 결과의 ``next_page()``가 돌려주는 값을 씁니다. 세 값은 각각 ``qryStNo``, ``qryStTrnNo``,
    ``qryStTrnNo2``로 보냅니다. ``query_station_no``와 ``query_train_no``는 비어 있지 않은 문자열이어야 하고
    ``query_train_no2``만 빈 문자열을 허용하며, 조건에 맞지 않으면 ``KorailProtocolError``가 발생합니다."""

    # 앱 근거: TrainScheduleViewModel.java:205,7340,10262-10279. 대상 필드: TrainScheduleIn.java:95.

    query_station_no: str
    query_train_no: str
    query_train_no2: str = ""

    def __post_init__(self) -> None:
        for name in ("query_station_no", "query_train_no"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise KorailProtocolError(f"TrainSearchContinuation.{name} must be a non-empty string")
        if not isinstance(self.query_train_no2, str):
            raise KorailProtocolError("TrainSearchContinuation.query_train_no2 must be a string")


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
    except KorailProtocolError:
        return None


@dataclass(frozen=True)
class TrainSearchResult:
    """직통 열차 조회 한 페이지와 후속 조회 정보를 담습니다.

    예외 없이 반환돼도 ``trains``가 비어 있을 수 있으므로 확인하세요."""

    # 관측: WRG000000/SUCC 에서 trn_infos 없이 빈 목록을 반환했습니다.

    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 조회에 넘길 ``TrainSearchContinuation``을 반환합니다.

        ``next_page_flag``가 ``"Y"``이고 필수 커서가 모두 있을 때만 값을 돌려줍니다. ``trains``가 비었거나 커서가 없으면
        ``None``입니다."""
        # 관측: 직통 6질의는 커서가 없어 None 이었습니다. 수동 커서 조합도 같은 10행을 반환한 기록이 있지만 모든 조건에서
        # 페이지가 없다고 일반화할 수는 없습니다.
        # 앱은 결과 목록이 비어 있으면 다음 페이지를 부르지 않습니다(TrainScheduleViewModel.smali:36786-36804).
        if not self.trains:
            return None
        metadata = self.metadata
        return _train_search_continuation(metadata, query_train_no=metadata.next_train_no or "")

    def next_query_from_last_departure(
        self,
        query: TrainSearchQuery,
    ) -> TrainSearchQuery | None:
        """``query``의 출발 날짜·시각을 마지막 열차의 출발 날짜·시각으로 바꾼 조회 조건을 만듭니다.

        요청은 보내지 않습니다. ``trains``가 비었거나 마지막 열차에 출발 날짜·시각이 없으면 ``None``입니다."""
        if not self.trains:
            return None
        last = self.trains[-1]
        date = last.departure_date
        time = last.departure_time
        if not date or not time:
            return None
        return replace(query, departure_date=date, departure_time=time)


@dataclass(frozen=True)
class TransferItinerary:
    """탑승 순서가 있는 두 구간의 환승 여정을 담습니다.

    환승 조회 결과에서 ``train_sequence``(``h_trn_seq``)가 같은 두 행을 응답에 나온 순서대로 묶은 것입니다. 구간 순서를
    나타내는 ``change_train_sequence``(``h_chg_trn_seq``)와는 다른 값입니다."""

    # 묶는 규칙은 pair_transfer_itineraries. h_trn_seq 와 h_chg_trn_seq 는 서로 다른 DTO 원소입니다
    # (TrainScheduleOutTrainInfo.java:1464,1112).

    first: TrainSummary
    second: TrainSummary

    @property
    def legs(self) -> tuple[TrainSummary, ...]:
        """두 열차 구간을 탑승 순서대로 반환합니다."""
        return (self.first, self.second)

    @property
    def transfer_station_code(self) -> str | None:
        """첫 구간 도착역과 다음 구간 출발역이 같을 때만 그 역 코드를 반환합니다.

        다르면 ``None``이므로 두 구간의 역을 직접 확인하세요."""
        # 앱의 구간별 이름 표시는 DialogsKt.java:170668,170678 참고.
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
    묶습니다(TrainScheduleViewModel.smali:36958-37040 의 LinkedHashMap groupBy). 두 구간이 아닌 묶음은 여정으로 만들지 않고
    ``trains`` 에만 남습니다."""
    by_sequence: dict[str | None, list[TrainSummary]] = {}
    for train in trains:
        by_sequence.setdefault(train.train_sequence, []).append(train)
    return [
        TransferItinerary(first=group[0], second=group[1]) for group in by_sequence.values() if len(group) == 2
    ]


@dataclass(frozen=True)
class TransferSearchResult:
    """환승 조회의 전체 열차 행과 두 구간으로 묶은 여정을 담습니다."""

    itineraries: list[TransferItinerary]
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 조회에 넘길 ``TrainSearchContinuation``을 반환합니다.

        ``next_page_flag``가 ``"Y"``이고 커서가 있을 때만 값을 돌려줍니다. 환승 커서(``next_preceding_train_no``,
        ``next_connecting_train_no``)가 둘 다 있으면 그 값을 쓰고, 하나라도 없으면 직통 커서(``next_train_no``)를 씁니다.
        ``trains``가 비었거나 커서가 없으면 ``None``입니다."""
        # 환승 커서 둘이 모두 있으면 사용하고 하나라도 없으면 직통 커서로 폴백하는 것은 라이브러리 정책입니다. 앱의 세 값
        # 전달은 TrainScheduleViewModel.java:7340과 TrainScheduleViewModel.smali:36806-36845, 분기 비교는
        # TrainScheduleViewModel.smali:35654-35698에서 확인되지만 비교 리터럴은 보호돼 있습니다.
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
