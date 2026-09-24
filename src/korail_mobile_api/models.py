# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공통 봉투와 열차·좌석 조회 모델. raw 를 가진 모델은 받은 원문을 보존합니다. frozen dataclass 도 내부 dict/list 까지 불변으로 만들지는 않습니다. 필드와 raw 는
repr·로그·직렬화에 평문 그대로 나옵니다. 승차권 등 조회는 read_models, 상태 변경은 mutation_models 에 있습니다."""

from dataclasses import dataclass, field, replace
from typing import Any

from .errors import KorailProtocolError


@dataclass(frozen=True)
class KorailSession:
    """로그인 쿠키와 계정 식별자. client.session.current 에 저장됩니다. customer_no 는 회원번호와 다른 고객번호이며 member_card_no 는 검색의
    mbCrdNo 에 사용합니다. 필드는 repr 에도 원문 그대로 나옵니다."""

    jsessionid: str | None = None
    member_no: str | None = None
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)
    member_card_no: str | None = None
    customer_no: str | None = None


@dataclass(frozen=True)
class BaseKorailResponse:
    """공통 봉투의 값 객체. 모든 응답 모델이 이를 상속하는 것은 아닙니다. from_raw 는 성공 여부·봉투 필드 타입을 판정하지 않습니다. HTTP 판정은
    parse_base_response 참고. FAIL/P058 은 raise_on_fail 과 무관하게 만료 예외이며, 일반 코드가 존재한다는 사실만으로 실패가 되지는 않습니다. raw 는 원본
    JSON 입니다."""

    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "BaseKorailResponse":
        """봉투 세 필드를 그대로 옮겨 담아 응답을 만듭니다.

        ``raw`` 가 JSON 객체가 아니면 :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 값이 무엇인지는 보지 않습니다 — 실패
        판정은 호출자 몫입니다."""
        if not isinstance(raw, dict):
            raise KorailProtocolError("KORAIL response must be a JSON object")
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
    #: 업데이트 버튼의 CNTAURL(MobilePlusMainVersion.java:52, AppKt.java:1240,1323,1635). 2026-09-22 라이브에서 확인한 스토어 링크이며
    #: 위치 인자 호환성을 위해 뒤에 둡니다.
    store_url: str | None = None


@dataclass(frozen=True)
class AppDataResponse(BaseKorailResponse):
    disability_certification_msg: str | None = None
    railplus_cardinfo: str | None = None
    version: AppVersionInfo | None = None
    notice: "NoticeResponse | None" = None


@dataclass(frozen=True)
class NoticeResponse(BaseKorailResponse):
    board_id: str | None = None
    post_sequence: str | None = None
    post_title: str | None = None
    post_content: str | None = None


@dataclass(frozen=True)
class UuidResponse(BaseKorailResponse):
    verification_code: str | None = None


@dataclass(frozen=True)
class MaasMenuItem:
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
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)

    @property
    def uses_station_selection(self) -> bool:
        return (
            self.active == "Y"
            and self.menu_type != "N"
            # ``appData`` 가 ``"N"`` 일 때만 역 목록이 비어 있습니다. 허용 목록으로 두지 않는 것은 ``{"Y", "M10", "M30"}`` 밖의 값이 실제로 오기
            # 때문입니다 — 2026-09-22 라이브: ``appData='C'``(부가서비스 코드 ``604``)가 ``get_maas_station_data`` 로 역 15개를
            # 돌려줬습니다. 같은 호출에서 ``'N'``(코드 ``001``)만 0개였고, ``'Y'``/``'M30'`` 은 25~111개였습니다.
            and self.app_data not in (None, "", "N")
            and isinstance(self.additional_service_code, str)
            and bool(self.additional_service_code.strip())
        )


@dataclass(frozen=True)
class MaasMenuListResponse(BaseKorailResponse):
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
    """역 코드·이름 쌍. 검색에 코드를 쓰면 클라이언트가 역 목록으로 이름을 찾아 전송합니다. popup_* 는 역별 안내값입니다."""

    code: str
    name: str
    longitude: str | None = None
    latitude: str | None = None
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)
    group: str | None = None
    major: str | None = None
    #: popupType 은 String 선언이므로 문자열로 유지합니다(StationDataOutStnItem.java:60).
    popup_type: str | None = None
    popup_message: str | None = None
    popup_link_title: str | None = None
    popup_link_url: str | None = None
    area: str | None = None
    stop: str | None = None


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    stations: tuple[KorailStation, ...] = ()


@dataclass(frozen=True)
class StationInfoResponse(BaseKorailResponse):
    #: count 는 String 선언이므로 정수로 바꾸지 않습니다(StationInfoOut.java:47).
    count: str = ""
    map_version: str | None = None


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
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class TrainCalendarResponse(BaseKorailResponse):
    days: tuple[TrainCalendarDay, ...] = ()


@dataclass(frozen=True)
class TrainScheduleStop:
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
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class TrainScheduleResponse(BaseKorailResponse):
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
    station_code: str | None = None
    station_name: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class TransferStationListResponse(BaseKorailResponse):
    stations: tuple[TransferStation, ...] = ()


@dataclass(frozen=True)
class LoginCryptoInfo:
    idx: str = ""
    key: str = ""
    pwd_aes_cphd: str = "N"


@dataclass(frozen=True)
class TrainSearchQuery:
    """열차 조회 조건. 역 이름·코드를 받으며 코드는 전송 전에 이름으로 변환합니다. 날짜·시각 형식은 YYYYMMDD·HHMMSS 입니다. 기본 열차군 109 는 라이브 기록에 의존하며
    TrainGroup.ALL 의 보호된 값은 정적으로 확인되지 않습니다(TrainGroup.java:25,29,335). include_srt 는 두 플래그를 함께 설정하지만 앱은 SRT 또는
    수서 함께 조회 조건을 사용합니다 (TrainScheduleViewModel.java:3137,3147). 보호된 query_division_code 는 코드를 아는 경우만 지정하십시오."""

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
    #: 7.0.6 TrainScheduleIn의 환승역 목록. 코드가 공개된 역만 지정합니다.
    connection_station_codes: tuple[str, ...] = ()
    #: 7.0.6 화면은 선택한 후속 열차군 하나를 목록으로 전송합니다.
    connection_train_group_code: str | None = None
    #: APK의 정렬 선택별 값은 보호되어 있으므로 전선 코드를 직접 지정합니다.
    query_division_code: str = "1"


def _train_scalar(value: Any, key: str, *, required: bool = False) -> str | None:
    """검색 스칼라는 문자열·JSON 정수를 받습니다. String 선언(TrainScheduleOutTrainInfo.java:63,1152)보다 넓게 받는 라이브러리 정책이며
    앱 Json 설정은 보호돼 있습니다(NetworkModule.java:862, NetworkServiceKt.java:29). 그 밖의 모양은 선택 필드면 None, ``required``
    (train_no)면 KorailProtocolError 입니다. 원문은 raw 에 남고, 예약 빌더가 에코하는 값을 다시 검사합니다. 이미 사라진 영 채움은
    복원하지 않습니다."""
    if value is None or isinstance(value, str):
        return value
    # bool 을 숫자로 받지 않도록 정확한 int 타입만 허용합니다.
    if type(value) is int:
        try:
            return str(value)
        except ValueError:
            # 파이썬의 정수→문자열 자릿수 한도(기본 4,300자리)를 넘은 값입니다.
            pass
    if required:
        raise KorailProtocolError(f"KORAIL train field {key} must be a string, an integer, or null")
    return None


def _train_optional_int(
    raw: dict[str, Any],
    key: str,
) -> int | None:
    # 선택 필드라 정수가 아니면 None 입니다(bool 도 정수로 치지 않음). 원문은 raw 에.
    value = raw.get(key)
    return value if type(value) is int else None


#: TrainSummary 의 ``train_no``·``goods_no``·``total_passenger_count`` 를 뺀 필드와 그 필드를 읽는 키. 세 번째 칸이 있으면 첫 키가 없거나
#: 거짓일 때(정수 0 제외) 그 철자를 읽습니다(``h_trn_gp_cd`` 와 ``trnGpCd`` 등). 오류는 언제나 첫 키 이름으로 냅니다.
_TRAIN_SUMMARY_KEYS: tuple[tuple[str, str, str | None], ...] = (
    ("train_group_code", "h_trn_gp_cd", "trnGpCd"),
    ("departure_station_code", "h_dpt_rs_stn_cd", "dptRsStnCd"),
    ("arrival_station_code", "h_arv_rs_stn_cd", "arvRsStnCd"),
    ("departure_station_name", "h_dpt_rs_stn_nm", "dptRsStnNm"),
    ("arrival_station_name", "h_arv_rs_stn_nm", "arvRsStnNm"),
    ("departure_date", "h_dpt_dt", "dptDt"),
    ("departure_time", "h_dpt_tm", "dptTm"),
    ("arrival_time", "h_arv_tm", "arvTm"),
    #: ``h_arv_dt`` 도착일(TrainScheduleOutTrainInfo.java:1068). 자정을 넘는 열차는 출발일과 다릅니다.
    ("arrival_date", "h_arv_dt", None),
    ("run_date", "h_run_dt", "runDt"),
    ("train_class_code", "h_trn_clsf_cd", "trnClsfCd"),
    ("departure_run_order", "h_dpt_stn_run_ordr", "dptStnRunOrdr"),
    ("arrival_run_order", "h_arv_stn_run_ordr", "arvStnRunOrdr"),
    ("seat_map_flag", "h_rd_seat_map_flg", None),
    ("general_reservation_code", "h_gen_rsv_cd", None),
    #: ``h_gen_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:83``. 일반실 예약가능 플래그 원시값(코드가 아니라 플래그).
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
    #: ``h_spe_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:108`` (Java 필드명 ``hSpRsvFlg``). 특실 예약가능 플래그.
    ("special_reservation_flag", "h_spe_rsv_flg", None),
    ("secondary_special_reservation_code", "h_spe_rsv_cd2", None),
    ("free_reservation_code", "h_free_rsv_cd", None),
    #: ``h_free_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:75``. 자유석 예약가능 플래그.
    ("free_reservation_flag", "h_free_rsv_flg", None),
    ("standing_reservation_code", "h_stnd_rsv_cd", None),
    #: ``h_stnd_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:151`` (Java 필드명 ``h_stnd_rsv_flg`` 그대로). 입석 예약가능
    #: 플래그.
    ("standing_reservation_flag", "h_stnd_rsv_flg", None),
    #: ``h_rsv_psb_flg`` -- ``TrainScheduleOutTrainInfo.java:100``. 열차 전체의 예약가능 여부를 정하는 최상위 플래그(등급별
    #: ``*_reservation_flag`` 와 별개).
    ("reservation_available_flag", "h_rsv_psb_flg", None),
    # 잔여 문구는 ``h_gen_rsv_nm``/``h_spe_rsv_nm`` 입니다. ``h_rsv_psb_nm``/``h_spe_rsv_psb_nm`` 는 이름과 달리 문구가 아니라
    # **운임**입니다 -- 2026-09-22 라이브(서울→부산 20260925) 확인: 같은 행에서 ``h_gen_rsv_nm='매진'`` 인데
    # ``h_rsv_psb_nm='47,500원'``. ``"매진"``/``"좌석부족"`` 은 앞의 키에만 옵니다.
    ("general_availability_name", "h_gen_rsv_nm", None),
    ("special_availability_name", "h_spe_rsv_nm", None),
    #: ``h_stnd_rsv_nm``/``h_free_rsv_nm`` -- 입석·자유석 쪽의 같은 화면 문구.
    #: ``TrainScheduleOutTrainInfo.java:1380``/``:1196`` 의 ``@SerialName`` 이고, 합성 생성자(``:172``)에서 이미 읽고 있던 일반실
    #: ``h_gen_rsv_nm``(str42)·특실 ``h_spe_rsv_nm``(str47) 바로 옆의 str51/str53 입니다.
    ("standing_availability_name", "h_stnd_rsv_nm", None),
    ("free_availability_name", "h_free_rsv_nm", None),
    ("general_fare_text", "h_rsv_psb_nm", None),
    ("special_fare_text", "h_spe_rsv_psb_nm", None),
    ("wait_reservation_flag", "h_wait_rsv_flg", None),
    ("standard_remaining_seat_count", "h_std_rest_seat_cnt", None),
    ("first_class_remaining_seat_count", "h_fst_rest_seat_cnt", None),
    #: ``h_free_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:73``. 자유석 잔여석 수 --
    #: ``h_std_rest_seat_cnt``/``h_fst_rest_seat_cnt`` 의 셋째 등급.
    ("free_remaining_seat_count", "h_free_rest_seat_cnt", None),
    #: ``h_stnd_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:150`` (Java 필드명 ``h_stnd_rest_seat_cnt``
    #: 그대로). 입석 잔여석 수.
    ("standing_remaining_seat_count", "h_stnd_rest_seat_cnt", None),
    ("free_car_count", "h_free_sracar_cnt", None),
    ("reservation_wait_passenger_count", "h_rsv_wait_ps_cnt", None),
    ("train_sequence", "h_trn_seq", None),
    ("change_train_sequence", "h_chg_trn_seq", None),
    ("change_train_division_code", "h_chg_trn_dv_cd", None),
    ("merge_seat_application_flag", "h_yms_apl_flg", None),
    ("train_suspension_flag", "h_trn_sps_flg", None),
)


def _train_value(
    raw: dict[str, Any], key: str, fallback: str | None, *, required: bool = False
) -> str | None:
    value = raw.get(key)
    if fallback is not None and type(value) is not int:
        value = value or raw.get(fallback)
    return _train_scalar(value, key, required=required)


@dataclass(frozen=True)
class TrainSummary:
    """열차 조회 한 행. reserve 등에서 식별자를 재사용하지만 필요한 값의 존재까지 보장하지는 않습니다. 예약 가능 코드·표시 문구와 운임 문구를 구분하십시오.
    h_gen_rsv_nm/h_spe_rsv_nm 은 좌석 상태, h_rsv_psb_nm 은 운임일 수 있습니다. 2026-09-22 관측에서 같은 행에 매진과 47,500원이 함께 있었습니다.
    원시 플래그의 보호된 코드 해석은 constants 의 근거·한계를 따릅니다."""

    train_no: str
    train_group_code: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    run_date: str | None = None
    train_class_code: str | None = None
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    seat_map_flag: str | None = None
    general_reservation_code: str | None = None
    #: ``h_gen_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:83``. 일반실 예약가능 플래그.
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
    #: ``h_spe_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:108`` (Java 필드명 ``hSpRsvFlg``). 특실 예약가능 플래그.
    special_reservation_flag: str | None = None
    secondary_special_reservation_code: str | None = None
    free_reservation_code: str | None = None
    #: ``h_free_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:75``. 자유석 예약가능 플래그.
    free_reservation_flag: str | None = None
    standing_reservation_code: str | None = None
    #: ``h_stnd_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:151`` (Java 필드명 ``h_stnd_rsv_flg`` 그대로). 입석 예약가능
    #: 플래그.
    standing_reservation_flag: str | None = None
    #: ``h_rsv_psb_flg`` -- ``TrainScheduleOutTrainInfo.java:100``. 열차 전체의 예약가능 여부를 정하는 최상위 플래그.
    reservation_available_flag: str | None = None
    general_availability_name: str | None = None
    special_availability_name: str | None = None
    wait_reservation_flag: str | None = None
    standard_remaining_seat_count: str | None = None
    first_class_remaining_seat_count: str | None = None
    #: ``h_free_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:73``. 자유석 잔여석 수.
    free_remaining_seat_count: str | None = None
    #: ``h_stnd_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:150`` (Java 필드명 ``h_stnd_rest_seat_cnt``
    #: 그대로). 입석 잔여석 수.
    standing_remaining_seat_count: str | None = None
    free_car_count: str | None = None
    reservation_wait_passenger_count: str | None = None
    total_passenger_count: int | None = None
    goods_no: str | None = None
    #: h_trn_seq — 환승 여정 번호. 앱은 이 값으로 환승 행을 묶습니다 (TrainScheduleViewModel.smali:36958-37040,
    #: TrainScheduleOutTrainInfo.java:1464). 2026-09-24 강릉→목포: 여정마다 000/001, 여정 안의 두 구간이 같은 값.
    train_sequence: str | None = None
    #: h_chg_trn_seq 는 구간 순서(TrainScheduleOutTrainInfo.java:53,172,1112; TrainList.java:35,234). 2026-09-22 관측:
    #: 직통 6질의의 행도 모두 1, 환승 6여정 12구간은 1/2였습니다. 따라서 이 값의 존재만으로 환승을 판정할 수 없습니다. 여정 종류 h_chg_trn_dv_cd 와도 다릅니다.
    change_train_sequence: str | None = None
    #: h_chg_trn_dv_cd 는 여정 종류. 2026-09-22 직통 6질의는 1/직통, 환승 6여정 12구간은 2/환승을 관측했습니다. 이 값은 검색 job id 와 별개입니다. 환승
    #: 묶음은 pair_transfer_itineraries 참고.
    change_train_division_code: str | None = None
    #: h_yms_apl_flg 선언: TrainScheduleOutTrainInfo.java:147,1480. 같은 DTO 의 isCombination/isSpecialCombination 이
    #: 판정에 사용합니다 (TrainScheduleOutTrainInfo.java:1500-1552). 비교 리터럴은 보호돼 코드 배정은 정적 미확인입니다.
    merge_seat_application_flag: str | None = None
    #: 7.0.6 h_trn_sps_flg: 운휴 표시/예약 게이트용 원표 플래그.
    train_suspension_flag: str | None = None
    #: ``h_rsv_psb_nm`` — 일반실 **운임** 문구(``"47,500원"``). 이름이 예약가능("rsv_psb")처럼 보이지만 실제로 담겨 오는 값은 금액입니다. 잔여 문구는
    #: :attr:`general_availability_name` 쪽입니다.
    general_fare_text: str | None = None
    #: ``h_spe_rsv_psb_nm`` — 특실 **운임** 문구. 위와 같은 이유로 이름과 내용이 어긋나는 키라, 잔여 문구는 :attr:`special_availability_name`
    #: 에서 읽습니다.
    special_fare_text: str | None = None
    #: ``h_stnd_rsv_nm`` — 입석 잔여 화면 문구. :attr:`standing_reservation_code`(``h_stnd_rsv_cd``)가 코드이고 이쪽이 사람이 읽는
    #: 글자라, 둘 다 있어야 화면을 그대로 재현할 수 있습니다. 2026-09-22 라이브 값: ``'매진'``(서울→부산 20260925, 동대구→서울 20260927),
    #: ``'역발매중'``(용산→목포 20260926), ``'-'``(서울→부산 20261015 일부 행).
    standing_availability_name: str | None = None
    #: ``h_free_rsv_nm`` — 자유석 쪽 같은 문구. 값에 줄바꿈이 들어옵니다 — 2026-09-22 서울→부산 20261015 에서 ``'역발매중\n(1량)'``,
    #: ``'역발매중\n(2량)'`` 을 받았습니다. 한 줄에 찍을 곳이라면 호출자가 직접 다듬어야 합니다.
    free_availability_name: str | None = None
    arrival_date: str | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "TrainSummary":
        """검색 응답의 행 하나를 :class:`TrainSummary` 로 만듭니다.

        주요 값은 ``h_`` 접두 철자와 접두 없는 철자를 둘 다 찾습니다 (``h_trn_no`` 와 ``trnNo`` 등). 모든 스칼라는 :func:`_train_scalar` 를
        지나므로 숫자로 온 값도 받아들이고, 선택 필드의 그 밖의 모양은 None 이 됩니다."""
        return cls(
            # _train_scalar 를 지난 뒤 ""로 기본값을 준다. train_no 만이 이 클래스에서 유일하게 선택적이지 않은 속성이다.
            train_no=_train_value(raw, "h_trn_no", "trnNo", required=True) or "",
            **{
                attr: _train_value(raw, key, fallback)
                for attr, key, fallback in _TRAIN_SUMMARY_KEYS
            },
            total_passenger_count=_train_optional_int(raw, "totPsgCnt"),
            # 예약 입력 없이도 좌석 조회하도록 상품번호를 행에 보관합니다. h_gd_no 는 앱의 응답 봉투에 선언되며 행 필드라는 근거는
            # 아닙니다(TrainScheduleOut.java:29,184,232). 앱의 좌석 조회 값은 예약 입력→TrainResearchIn→좌석 재고로 전달됩니다
            # (TrainSeatMapViewModel.java:1974-1976,2527,2546; TrainResearchIn.java:68,275-278). 서버 행의 두 후보 키가
            # 없으면 None 입니다.
            goods_no=(
                _train_value(raw, "h_gd_no", None) or _train_value(raw, "txtGdNo", None)
            ),
            raw=raw,
        )


@dataclass(frozen=True)
class ReservationPassengerInfo:
    """``ReservationOut.psg_infos.psg_info`` 한 행 — 승객 유형별 인원과 할인(ReservationOutPsgInfo.java 의 @SerialName 10개).
    선택값으로 관대하게 읽습니다. 2026-09-24 라이브 홀드: 성인 1명 행 하나에 앞의 6개 키가 있었고 할인·증빙 값은 빈 문자열이었습니다."""

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
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class SeatAttribute:
    name: str
    code: str | None = None


@dataclass(frozen=True)
class SeatCar:
    """호차 요약. car_no 를 좌석 재고 조회에 사용하고 attributes 는 호차의 좌석 속성입니다."""

    car_no: int
    room_class_name: str
    remaining_seat_count: int
    attributes: tuple[SeatAttribute, ...]
    room_class_code: str | None = None
    total_seat_count: int | None = None


@dataclass(frozen=True)
class SeatCarListResponse(BaseKorailResponse):
    recommended_car_no: int | None = None
    train_no: str | None = None
    cars: tuple[SeatCar, ...] = ()
    train_class_code: str | None = None
    train_group_code: str | None = None
    #: h_scar_num 은 nullable String 선언입니다(TrainResearchOut.java:27,105).
    car_count: str | None = None


@dataclass(frozen=True)
class PhysicalSeat:
    """좌석표 한 자리. 좌석지정에는 표시 specification 이 아니라 식별자 seat_no 를 사용하십시오. KorailSeatAssignment.from_inventory 로 옮길 수
    있습니다. floor 는 앱 DTO 에 없습니다(TResidualSeatsResearchOutSeat.java:32-41). 그러나 이 파서는 서버 추가 문자열을 읽으므로 항상 None 이라고
    보장하지 않습니다."""

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
    start_location_ratio: float
    close_location_ratio: float


@dataclass(frozen=True)
class SeatInventoryResponse(BaseKorailResponse):
    """한 호차의 좌석과 창측 비율. car_no 가 없으면 from_inventory 에 호차번호를 직접 제공해야 합니다."""

    #: layout_type 은 String 선언(TResidualSeatsResearchOut.java:29)이지만 2026-09-21 서버 표본은 JSON 정수였습니다. 파서는 두 형식을 받아
    #: str 로 정규화합니다.
    layout_type: str = ""
    arrangement_code: str = ""
    #: 7.0.6 TResidualSeatsResearchOut DTO에는 이 두 건수 키가 없습니다.
    remaining_count: int | None = None
    total_count: int | None = None
    seats: tuple[PhysicalSeat, ...] = ()
    windows: tuple[SeatWindow, ...] = ()
    vr_banner_url: str | None = None
    car_type_code: str | None = None
    car_no: int | None = None
    up_down_division_code: str | None = None


@dataclass(frozen=True)
class TrainSearchMetadata:
    """행 이외의 검색 조건·커서. 2026-09-22 직통 6질의는 다음 페이지 Y 여도 필수 커서가 없었습니다. 플래그만으로 다음 요청 가능 여부를 판단하지 마십시오. h_menu_id 는
    요청 txtMenuId 와 별도로 받은 값입니다."""

    job_id: str | None = None
    menu_id: str | None = None
    product_no: str | None = None
    next_page_flag: str | None = None
    next_query_station_no: str | None = None
    next_train_no: str | None = None
    #: 환승 커서 선언: TrainScheduleOut.java:28,33,67. 사용: TrainScheduleViewModel.java:7340. 응답에서 선택하는 메서드는 jadx 복원
    #: 실패입니다. 기존 smali 근거는 TrainScheduleViewModel.smali:36806-36851 이며 보호된 분기 값은 미확인입니다. 라이브러리는
    #: TransferSearchResult.next_page 에서 두 커서 존재 여부로 선택합니다.
    next_preceding_train_no: str | None = None
    next_connecting_train_no: str | None = None
    result_count: str | None = None
    #: ``h_notice_msg`` — 서버가 검색 결과에 붙이는 안내 문구 (``TrainScheduleOut.java:32,67,196`` 의
    #: ``@SerialName("h_notice_msg")``). 7.0.6 은 이 값이 비어 있지 않으면 그대로 경고 대화상자로 띄웁니다
    #: (``TrainScheduleViewModel.smali:36742-36786`` — ``getHNoticeMsg()`` 길이 검사 후
    #: ``ScreenViewModel.alert$default``).
    notice_message: str | None = None
    # 7.0.6 TrainScheduleOut 이 셋 다 선언한다.
    first_seat_count: str | None = None
    second_seat_count: str | None = None
    first_departure_time: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )
    agreement_text: str | None = None
    remaining_seat_count: str | None = None


@dataclass(frozen=True)
class TrainSearchContinuation:
    """다음 요청에 전달하는 3튜플 커서(TrainScheduleViewModel.java:205,7340,10262-10279). 대상 필드: TrainScheduleIn.java:95 의
    qryStNo/qryStTrnNo/qryStTrnNo2. query_train_no2 만 빈 문자열을 허용합니다. 직접 구성하기보다 검색
    결과의 next_page 를 사용하십시오."""

    query_station_no: str
    query_train_no: str
    query_train_no2: str = ""

    def __post_init__(self) -> None:
        for name in ("query_station_no", "query_train_no"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise KorailProtocolError(
                    f"TrainSearchContinuation.{name} must be a non-empty string"
                )
        if not isinstance(self.query_train_no2, str):
            raise KorailProtocolError(
                "TrainSearchContinuation.query_train_no2 must be a string"
            )


def _train_search_continuation(
    metadata: TrainSearchMetadata,
    *,
    query_train_no: str,
    query_train_no2: str = "",
) -> TrainSearchContinuation | None:
    """직통·환승 ``next_page`` 가 공유하는 다음 페이지 게이트 겸 커서 생성기."""
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
    """직통 조회 한 페이지. 예외가 없어도 trains 가 비었는지 확인하십시오. 2026-09-22 관측: WRG000000/SUCC 에서 trn_infos 없이 빈 목록을 반환했습니다.
    WRD000061 은 환승 재조회 계기이지 환승 결과 존재를 보장하지 않습니다."""

    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 페이지 Y 와 필수 커서가 모두 있을 때만 continuation 을 반환합니다. 2026-09-22 직통 6질의는 커서가 없어 None 이었습니다. 수동 커서 조합도 같은
        10행을 반환한 기록이 있지만 모든 조건에서 페이지가 없다고 일반화할 수는 없습니다. 필요하면 next_query_from_last_departure 로 별도 질의를 만드십시오."""
        # 앱은 결과 목록이 비어 있으면 다음 페이지를 부르지 않습니다(TrainScheduleViewModel.smali:36786-36804).
        if not self.trains:
            return None
        metadata = self.metadata
        return _train_search_continuation(
            metadata, query_train_no=metadata.next_train_no or ""
        )

    def next_query_from_last_departure(
        self,
        query: TrainSearchQuery,
    ) -> TrainSearchQuery | None:
        """마지막 행의 출발 날짜·시각을 복사한 질의만 만들며 전송하지 않습니다. 행이나 날짜·시각이 없으면 None 입니다. 날짜 없이 시각만 옮기지 않습니다. 2026-09-22 관측:
        재조회 10행 중 첫 행이 앞 페이지 마지막 열차와 겹치고 9행이 새로 왔습니다. 결합 시 열차번호뿐 아니라 운행일·구간도 고려해 동일한 경계 행을 제거하십시오. 앱 기본 화면의 동일
        동작은 보장하지 않습니다. 기존 다른 화면의 근거 기록은 TrainScheduleViewModel.smali:29590-29846,36938-36956 이며 현재 자료로 재검증하지
        못했습니다."""
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
    """두 구간의 환승 여정. 묶는 규칙은 pair_transfer_itineraries 참고. h_trn_seq 와 h_chg_trn_seq 는 서로 다른 DTO 원소입니다
    (TrainScheduleOutTrainInfo.java:1464,1112). 같은 값이라고 가정하지 마십시오."""

    first: TrainSummary
    second: TrainSummary

    @property
    def legs(self) -> tuple[TrainSummary, ...]:
        """탑승 순서의 두 구간. reserve_transfer 의 legs 인자로 넘길 수 있습니다."""
        return (self.first, self.second)

    @property
    def transfer_station_code(self) -> str | None:
        """첫 구간 도착역과 다음 구간 출발역이 같을 때만 그 코드를 반환합니다. 다르면 None 이며 두 역을 직접 읽어야 합니다. 합치기 규칙은 라이브러리 정책입니다. 앱의 구간별 이름
        표시는 DialogsKt.java:170668,170678 참고."""
        arrival = self.first.arrival_station_code
        return arrival if arrival == self.second.departure_station_code else None

    @property
    def transfer_station_name(self) -> str | None:
        """환승역 이름. 같으면 그 이름, 다르면 ``None`` — 코드 쪽과 같은 규칙입니다."""
        arrival = self.first.arrival_station_name
        return arrival if arrival == self.second.departure_station_name else None


def pair_transfer_itineraries(
    trains: list[TrainSummary],
) -> list[TransferItinerary]:
    """환승 행을 여정으로 묶습니다. 앱처럼 ``h_trn_seq``(:attr:`TrainSummary.train_sequence`, 없으면 ``None`` 끼리)가 같은 행을 처음 나온
    순서대로 묶습니다(TrainScheduleViewModel.smali:36958-37040 의 LinkedHashMap groupBy). 두 구간이 아닌 묶음은 여정으로 만들지 않고
    ``trains`` 에만 남습니다."""
    by_sequence: dict[str | None, list[TrainSummary]] = {}
    for train in trains:
        by_sequence.setdefault(train.train_sequence, []).append(train)
    return [
        TransferItinerary(first=group[0], second=group[1])
        for group in by_sequence.values()
        if len(group) == 2
    ]


@dataclass(frozen=True)
class TransferSearchResult:
    """평평한 trains 와 h_trn_seq 로 묶은 itineraries 를 함께 제공합니다. 묶는 규칙은 pair_transfer_itineraries 참고."""

    itineraries: list[TransferItinerary]
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 페이지 Y 이고 필수 값이 있을 때만 반환합니다. 환승 커서 둘이 모두 비어 있지 않으면 그 둘을 사용하고, 하나라도 없으면 직통 커서로 폴백합니다. 이 선택 조건은 라이브러리
        정책입니다. 앱의 3튜플 전달: TrainScheduleViewModel.java:7340. 선택 분기의 기존 근거는
        TrainScheduleViewModel.smali:35654-35698,36806-36845 이며 보호 리터럴은 미확인입니다."""
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
