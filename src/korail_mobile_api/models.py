"""공통 응답 봉투와 열차 검색·좌석 조회가 돌려주는 타입.

전부 ``frozen=True`` 데이터클래스입니다. 서버가 준 원본은 어느 모델에서든
``raw`` 에 그대로 남아 있으므로, 이 패키지가 이름을 붙이지 않은 필드도
거기서 꺼낼 수 있습니다. ``repr=False`` 인 필드는 로그에 실수로 찍히지 않게
표현에서 뺀 것이지 값이 없는 것이 아닙니다.

승차권·환불·마이페이지 쪽 읽기 모델은
:mod:`korail_mobile_api.read_models`, 상태변경 요청·응답 모델은
:mod:`korail_mobile_api.mutation_models` 에 있습니다.
"""

from dataclasses import dataclass, field
from typing import Any

from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_TRANSFER_ITINERARY_CODE,
)
from .errors import KorailProtocolError


@dataclass(frozen=True)
class KorailSession:
    """로그인이 남긴 것 — 쿠키와 계정 식별자들.

    :meth:`~korail_mobile_api.client.KorailClient.login` 이 돌려주고 같은
    값이 ``client.session.current`` 에 남습니다.

    ``jsessionid`` 는 이후 요청에 붙는 세션 쿠키입니다. ``customer_no``
    (``strCustNo``)는 회원번호가 아니라 고객번호이고,
    :meth:`~korail_mobile_api.client.KorailClient.get_customer_trip_info` 와
    :meth:`~korail_mobile_api.client.KorailClient.get_recent_delivery_history`
    가 따로 요구하는 값입니다. ``member_card_no`` 는 열차 검색 폼에
    ``mbCrdNo`` 로 함께 실립니다.

    전부 ``repr=False`` 입니다 — 세션을 통째로 찍어도 자격증명이 새지
    않습니다.
    """

    jsessionid: str | None = field(default=None, repr=False)
    member_no: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    member_card_no: str | None = field(default=None, repr=False)
    customer_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class BaseKorailResponse:
    """모든 응답이 공유하는 봉투. 다른 응답 모델은 전부 이것을 상속합니다.

    ``str_result``(``strResult``)가 성공/실패를 정하는 유일한 값입니다.
    ``h_msg_cd``/``h_msg_txt`` 는 서버의 코드와 문구이며, 성공에 경고가
    딸려 오는 경우가 있으므로 코드가 있다고 실패인 것이 아닙니다. 실패일 때
    코드가 어느 예외가 되는지는
    :func:`~korail_mobile_api.errors.classify_app_error` 를 참조하면 됩니다.

    ``raw`` 는 파싱 전 JSON 전체입니다.
    """

    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "BaseKorailResponse":
        """봉투 세 필드를 검증하며 응답을 만듭니다.

        ``h_msg_cd``/``h_msg_txt``/``strResult`` 중 하나라도 없거나
        문자열도 ``null`` 도 아니면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 값이
        무엇인지는 보지 않습니다 — 실패 판정은 호출자 몫입니다.
        """
        if not isinstance(raw, dict):
            raise KorailProtocolError("KORAIL response must be a JSON object")
        envelope_fields = ("h_msg_cd", "h_msg_txt", "strResult")
        missing = [
            field_name
            for field_name in envelope_fields
            if field_name not in raw
        ]
        if missing:
            raise KorailProtocolError(
                "KORAIL response missing required envelope fields: "
                + ", ".join(missing)
            )
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
    """역 하나.

    :meth:`~korail_mobile_api.client.KorailClient.get_station_data` 가 주는
    전체 역 목록의 한 줄입니다. ``code`` 와 ``name`` 이 짝입니다.

    열차 검색 폼에는 코드가 아니라 **이름** 이 나가므로, 코드로 검색하면
    클라이언트가 이 목록을 한 번 조회해 이름으로 바꿉니다.

    ``popup_*`` 는 그 역을 고르면 앱이 띄우는 안내입니다(공사 중 등).
    """

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
    """열차 검색 한 번의 조건.

    두 역 필드는 역코드와 역이름을 **둘 다** 받습니다. 이름은 그대로 나가고,
    코드를 주면 클라이언트가 역 목록을 조회해 이름으로 바꿉니다. 날짜는
    ``YYYYMMDD``, 시각은 ``HHMMSS`` 이며 그 시각 **이후** 열차를 줍니다.

    ``train_group_code`` 기본값 ``"109"`` 는 ``K4/s.java:5`` 의
    ``ALL("전체", "109")``, 즉 열차 종류 제한 없음입니다. ``include_srt`` 는
    ``ebizCrossCheck``/``srtCheckYn`` 한 쌍을 ``"Y"`` 로 만듭니다 — 앱은 이
    둘을 항상 같은 값으로 보냅니다.

    :meth:`~korail_mobile_api.client.KorailClient.search_trains` 와
    :meth:`~korail_mobile_api.client.KorailClient.search_transfer_trains` 가
    같은 질의 객체를 받습니다.
    """

    departure_station_code: str
    arrival_station_code: str
    departure_date: str
    departure_time: str = "000000"
    passengers: int = 1
    train_group_code: str = "109"
    include_srt: bool = False


def _train_scalar(value: Any, key: str) -> str | None:
    """검색 행의 필드 하나를 JSON 문자열로도 JSON 숫자로도 받아들입니다.

    KORAIL 은 APK 가 Java ``String`` 으로 선언한 필드를 둘 중 어느 쪽으로
    보낼지 일관되지 않고, 앱은 그것을 알아채지 못합니다 — 이 행들은 Gson 이
    역직렬화하는데 ``JsonReader.nextString()`` 이 JSON 숫자를 문자열로
    강제하기 때문입니다. 그래서 ``"h_dpt_tm": 63000`` 으로 온 행도 앱에서는
    정상 예매되고, 여기서 거부하면 앱이라면 예약했을 열차를 거부하게 됩니다.

    둘을 받는 것이 아무거나 받는 것은 아닙니다. ``bool``, ``float``, 리스트,
    객체는 여전히
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다 — Gson 도
    그런 것을 String 으로 받지 않고, 문자열로 바꿔 넘기면 정말로 달라진
    응답을 가리게 됩니다.

    서버가 이미 떨군 자릿수를 되살리지는 못합니다. 여섯 자리
    ``h_dpt_tm`` 이 ``63000`` 으로 왔다면 앞의 0 은 바이트가 도착하기 전에
    사라진 것이고, 그것은 ``mutation_payloads`` 의 자릿수 검사가 잡습니다.
    """
    if value is None or isinstance(value, str):
        return value
    # isinstance 가 아니라 type(...) is int 인 것은 의도다. bool 이 int 의
    # 하위 타입이고, True 는 KORAIL 이 이런 필드로 보내는 숫자가 아니다.
    if type(value) is int:
        return str(value)
    raise KorailProtocolError(
        f"KORAIL train field {key} must be a string, an integer, or null"
    )


def _train_optional_string(
    raw: dict[str, Any],
    key: str,
) -> str | None:
    return _train_scalar(raw.get(key), key)


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
    """열차 검색 결과의 한 행. 예약 폼이 필요한 값이 전부 여기 있습니다.

    :meth:`~korail_mobile_api.client.KorailClient.reserve` 는 이 객체를
    그대로 받으므로 열차번호·역코드·날짜·시각을 손으로 옮겨 적을 일이
    없습니다.

    좌석 여유는 이름이 비슷한 코드가 여럿이라 헷갈리기 쉽습니다.
    ``general_reservation_code``/``special_reservation_code`` 는 일반실·특실의
    예약 가능 코드이고, ``general_availability_name``/
    ``special_availability_name`` 이 앱이 화면에 찍는 문구입니다(``"매진"``,
    ``"좌석부족"`` 등). 앱은 예매 버튼을 코드가 아니라 이 **문구** 로
    막습니다(``a5/u.java:354``).

    예약대기 가능 여부는 ``wait_reservation_flag`` 하나로 정해지며 값이
    :data:`~korail_mobile_api.constants.KORAIL_STANDBY_WAIT_FLAG` 와 같을
    때뿐입니다.

    ``raw`` 에 서버 원본 행이 그대로 있습니다.
    """

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
    #: ``h_chg_trn_seq`` — 환승 여정 안에서 이 구간의 위치. 1구간이 ``"1"``,
    #: 2구간이 ``"2"`` 입니다(``RsvInquiryResponse.java:75``). 직통 검색에서는
    #: ``None`` 입니다.
    #:
    #: 앱이 두 곳에서 그렇게 읽습니다. ``u4/a.java:111-131`` 은 새 페이지를
    #: 기존 행과 중복 제거할 때 ``"2"`` 행을 찾아 **그 앞 행과 함께** 버리고,
    #: ``RsvInquiryRequest.java:164-172`` 는 다음 페이지의 ``txtGoHour`` 를
    #: 마지막 행이 ``"1"`` 이면 그 행에서, 아니면 그 앞 행에서 가져옵니다.
    change_train_sequence: str | None = field(default=None, repr=False)
    #: ``h_chg_trn_dv_cd`` — 행의 환승 구분.
    #: ``DirectInquiryActivity.java:194`` 는 널이면 직통으로 채운 뒤
    #: ``chtnDvCd`` 로 넘깁니다. 직통 검색에서는 ``None`` 입니다.
    change_train_division_code: str | None = field(default=None, repr=False)
    #: ``h_yms_apl_flg`` — 이 행이 병합(입석+좌석) 대상인지를 정하는 유일한
    #: 입력. ``S4/J.java:61-63`` 의 ``isMixedSeat(객실등급, 플래그)`` 는 행에서
    #: 이것 말고 아무것도 읽지 않고, ``a5/u.java:378-380`` 이 그 결과로 예매
    #: 버튼을 입석+좌석 예매(태그 ``"1202"``)로 바꿉니다.
    #: :data:`~korail_mobile_api.constants.KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`
    #: 참조.
    merge_seat_application_flag: str | None = field(default=None, repr=False)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "TrainSummary":
        """검색 응답의 행 하나를 :class:`TrainSummary` 로 만듭니다.

        주요 값은 ``h_`` 접두 철자와 접두 없는 철자를 둘 다 찾습니다
        (``h_trn_no`` 와 ``trnNo`` 등). 모든 스칼라는
        :func:`_train_scalar` 를 지나므로 숫자로 온 값도 받아들입니다.
        """
        return cls(
            # _train_scalar 를 지난 뒤 ""로 기본값을 준다. train_no 만이
            # 이 클래스에서 유일하게 선택적이지 않은 속성이다.
            train_no=_train_scalar(
                raw.get("h_trn_no") or raw.get("trnNo"), "h_trn_no"
            )
            or "",
            train_group_code=_train_scalar(
                raw.get("h_trn_gp_cd") or raw.get("trnGpCd"), "h_trn_gp_cd"
            ),
            departure_station_code=_train_scalar(
                raw.get("h_dpt_rs_stn_cd") or raw.get("dptRsStnCd"),
                "h_dpt_rs_stn_cd",
            ),
            arrival_station_code=_train_scalar(
                raw.get("h_arv_rs_stn_cd") or raw.get("arvRsStnCd"),
                "h_arv_rs_stn_cd",
            ),
            departure_station_name=_train_scalar(
                raw.get("h_dpt_rs_stn_nm") or raw.get("dptRsStnNm"),
                "h_dpt_rs_stn_nm",
            ),
            arrival_station_name=_train_scalar(
                raw.get("h_arv_rs_stn_nm") or raw.get("arvRsStnNm"),
                "h_arv_rs_stn_nm",
            ),
            departure_date=_train_scalar(
                raw.get("h_dpt_dt") or raw.get("dptDt"), "h_dpt_dt"
            ),
            departure_time=_train_scalar(
                raw.get("h_dpt_tm") or raw.get("dptTm"), "h_dpt_tm"
            ),
            arrival_time=_train_scalar(
                raw.get("h_arv_tm") or raw.get("arvTm"), "h_arv_tm"
            ),
            run_date=_train_scalar(
                raw.get("h_run_dt") or raw.get("runDt"), "h_run_dt"
            ),
            train_class_code=_train_scalar(
                raw.get("h_trn_clsf_cd") or raw.get("trnClsfCd"),
                "h_trn_clsf_cd",
            ),
            departure_run_order=_train_scalar(
                raw.get("h_dpt_stn_run_ordr") or raw.get("dptStnRunOrdr"),
                "h_dpt_stn_run_ordr",
            ),
            arrival_run_order=_train_scalar(
                raw.get("h_arv_stn_run_ordr") or raw.get("arvStnRunOrdr"),
                "h_arv_stn_run_ordr",
            ),
            seat_map_flag=_train_optional_string(raw, "h_rd_seat_map_flg"),
            general_reservation_code=_train_optional_string(
                raw,
                "h_gen_rsv_cd",
            ),
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
            # x4/b.java:23 이 좌석 검색의 txtGdNo 를 trainInfo.getTxtGdNo()
            # 에서 가져오므로, 좌석 조회 폼이 넘길 수 있게 열차 행에서
            # 상품번호(h_gd_no / txtGdNo)를 붙잡아 둔다.
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
    """호차 하나의 남은 좌석 요약.

    :meth:`~korail_mobile_api.client.KorailClient.get_seat_cars` 결과의 한
    줄입니다. ``car_no`` 가 그대로
    :meth:`~korail_mobile_api.client.KorailClient.get_seat_inventory` 에
    넘길 호차 번호입니다. ``attributes`` 는 그 호차가 가진 좌석 속성(유아동반,
    휠체어 등)이며 코드와 이름이 함께 옵니다.
    """

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
    """좌석표의 좌석 한 자리.

    ``seat_no`` 가 전선에 나가는 식별자이고, ``specification`` 이 사람이 읽는
    표시(``"5A"``)입니다. 좌석지정 예약에 넘겨야 하는 것은 ``seat_no``
    쪽이고,
    :meth:`~korail_mobile_api.mutation_models.KorailSeatAssignment.from_inventory`
    를 쓰면 손으로 옮길 일이 없습니다.

    ``sale_possible`` 이 ``"Y"`` 인 좌석만 앱이 누를 수 있게 합니다.
    ``direction_code`` 는 순방향/역방향, ``floor`` 는 복층 차량의 층입니다.
    """

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
    """한 호차의 좌석표.

    :meth:`~korail_mobile_api.client.KorailClient.get_seat_inventory` 가
    돌려줍니다. ``seats`` 가 좌석 하나하나, ``windows`` 는 창문 위치 비율이라
    좌석표를 그릴 때만 씁니다. ``car_no`` 는 서버가 되돌려 준 호차
    번호(``scar_no``)이며,
    :meth:`~korail_mobile_api.mutation_models.KorailSeatAssignment.from_inventory`
    가 이 값을 요구합니다 — 없으면 호차를 직접 적어야 합니다.
    """

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
    """검색 응답에서 열차 행이 아닌 부분 — 주로 다음 페이지 커서.

    직접 읽을 일은 거의 없습니다. 다음 페이지는
    :meth:`TrainSearchResult.next_page` 가 이 값들로 만들어 줍니다.

    ``menu_id`` 는 없습니다. ScheduleView 응답에 ``h_menu_id`` 가 없기
    때문입니다 — 앱의 ``txtMenuId`` 는 클라이언트 쪽 상수
    (``a5/k.java:92-94`` 의 ``"11"``)이고 서버 값이 아닙니다.
    """

    job_id: str | None = field(default=None, repr=False)
    product_no: str | None = field(default=None, repr=False)
    next_page_flag: str | None = None
    next_query_station_no: str | None = field(default=None, repr=False)
    next_train_no: str | None = field(default=None, repr=False)
    #: 커서의 환승 쪽 절반(``h_prcd_trn_no_next``/``h_ectb_trn_no_next``).
    #: ``b5/c.java:192-194`` 는 **둘 다 비어 있지 않을 때만** 이것을 다시 실어,
    #: ``qryStTrnNo`` 를 앞것으로 덮어쓰고 ``qryStTrnNo2`` 를 뒷것으로
    #: 채웁니다(``RsvInquiryRequest.java:212-215``). 직통 검색은 둘 다 비워
    #: 보냅니다.
    next_preceding_train_no: str | None = field(default=None, repr=False)
    next_connecting_train_no: str | None = field(default=None, repr=False)
    result_count: str | None = None
    #: ``h_notice_msg`` — 서버가 검색 결과에 붙이는 안내 문구
    #: (``RsvInquiryResponse.java:12``).
    notice_message: str | None = None
    # 아래 네 필드는 APK 근거가 없다. strJobId / h_seat_cnt_first /
    # h_seat_cnt_second / txtGoHour_first 는 analysis/ 전체에서 0건이고,
    # RsvInquiryResponse.java:8-17 이 선언하는 아홉 개 최상위 필드에도 없다.
    # 공개 속성을 지우면 호출자가 깨지므로 남겨 둘 뿐이니, 실제 서버에서는
    # None 을 예상하라. 같은 이유로 h_menu_id 는 이 모델에서 제외돼 있다.
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
    """다음 페이지를 요청할 때 되싣는 커서.

    앱도 같은 방식입니다. 앞 응답의 페이징 필드를 검색 화면에 들고 있다가
    (``b5/c.java:367-371``) 더 보기를 누르면 다음 요청에 되싣습니다
    (``:184-194``) — ``qryStNo``/``qryStTrnNo``/``pgPrCnt`` 가 그것입니다
    (``RsvInquiryRequest.java:174-177``, ``:207-210``).

    ``query_train_no2`` 만 환승 검색의 것입니다. 앞뒤 열차번호가 둘 다 비어
    있지 않을 때만 채워지므로(``RsvInquiryRequest.java:212-215``) 직통
    검색에서는 빈 문자열이며, 여기서 비어 있어도 되는 유일한 필드입니다.

    손으로 만들지 말고 :meth:`TrainSearchResult.next_page` 나
    :meth:`TransferSearchResult.next_page` 가 주는 것을 쓰면 됩니다.
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
    """직통 열차 검색 한 페이지.

    ``trains`` 가 그 페이지의 행입니다. 조건에 맞는 직통 열차가 없으면 빈
    목록이 아니라
    :class:`~korail_mobile_api.errors.KorailNoDirectTrainError` 가 올라옵니다.

    ``response`` 는 봉투, ``metadata`` 는 페이징 커서입니다.
    """

    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 페이지 커서. 다음이 없으면 ``None``.

        앱과 같은 게이트입니다 — ``h_next_pg_flg`` 가 ``"Y"`` 인 동안만
        "더 보기"가 살아 있습니다(``b5/c.java:381-387``). 커서 필드가 하나라도
        빠져 있어도 ``None`` 입니다. 반쯤 채운 커서는 조용히 1페이지를 다시
        요청하기 때문입니다.
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
    """환승 여정 하나 — 함께 예약되는 두 구간.

    환승 검색 응답은 구간을 중첩해 주지 않습니다. 직통과 똑같은 평평한
    ``trn_infos.trn_info`` 목록을 주고, 앱이 그것을 **위치로** 짝짓습니다 —
    0/1 행이 한 여정, 2/3 행이 다음 여정이고, 짝이 안 맞고 남는 마지막 행은
    버립니다(``a5/k.java:142-172``). 고른 여정을 다시 꺼낼 때도
    ``{list[i * 2], list[i * 2 + 1]}`` 로 읽고(``a5/k.java:108-110``), 그
    배열이 그대로 예약 여정 빌더로 갑니다.

    ``h_chg_trn_seq`` 는 서버가 적어 보낸 같은 위치값입니다(1구간 ``"1"``,
    2구간 ``"2"``). 이 클래스도 앱처럼 위치로 짝짓고, 서버가 그 표시를 채워
    보냈을 때는 짝짓기 기준이 아니라 검증에 씁니다 —
    :func:`pair_transfer_itineraries`.
    """

    first: TrainSummary
    second: TrainSummary

    @property
    def legs(self) -> tuple[TrainSummary, ...]:
        """탑승 순서대로의 두 구간. ``reserve_transfer`` 에 그대로 넘길 수 있습니다."""
        return (self.first, self.second)

    @property
    def transfer_station_code(self) -> str | None:
        """환승역 코드. 두 구간이 다른 역을 가리키면 ``None``.

        서버는 이것을 따로 보내지 않습니다. 환승역이란 1구간의 도착역이자
        2구간의 출발역일 뿐이고, 예약 폼도 그렇게 ``txtArvRsStnCd1`` 과
        ``txtDptRsStnCd2`` 로 나눠 적습니다.

        ``None`` 은 파싱 실패가 아니라 진짜 답입니다. 앱도 두 이름을 각각
        찍고 같을 때만 하나로 합칩니다(``a5/u.java:947-956``) — 한 역에
        내려 다른 역에서 타는 여정이 실제로 옵니다. 그 경우가 중요하면
        :attr:`first` 의 도착역과 :attr:`second` 의 출발역을 직접 읽으면
        됩니다.
        """
        arrival = self.first.arrival_station_code
        if arrival is not None and arrival == self.second.departure_station_code:
            return arrival
        return None

    @property
    def transfer_station_name(self) -> str | None:
        """환승역 이름. 같으면 그 이름, 다르면 ``None`` — 코드 쪽과 같은 규칙입니다."""
        arrival = self.first.arrival_station_name
        if arrival is not None and arrival == self.second.departure_station_name:
            return arrival
        return None


def pair_transfer_itineraries(
    trains: list[TrainSummary],
) -> list[TransferItinerary]:
    """평평한 환승 결과 목록을 앱과 같은 방식으로 여정 단위로 묶습니다.

    ``a5/k.java:156-170`` 그대로입니다. 짝이 안 맞고 남는 마지막 행 처리까지
    같습니다 — 앱은 ``i % 2 == 1`` 일 때만 목록에 넣으므로 홀로 남은 구간은
    예약 가능한 반쪽으로 보여 주지 않고 버립니다.

    서버가 ``h_chg_trn_seq`` 를 채워 보냈는데 그 값이 ``"1"``, ``"2"`` 순서가
    아니면 :class:`~korail_mobile_api.errors.KorailProtocolError` 를 올립니다.
    이 검사는 앱에는 없는 이 패키지의 것입니다 — 앱은 눈감고 짝짓습니다.
    어긋난 목록을 그냥 두면 한 여정이 아닌 두 행이
    :meth:`~korail_mobile_api.client.KorailClient.reserve_transfer` 로
    넘어갑니다.

    표시가 아예 없는 응답은 받아들입니다. 앱도 널이면 행의 위치로 채워
    넣습니다(``DirectInquiryActivity.java:194-195``,
    ``TransferInquiryActivity.java:44``).
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
    """환승 여정 한 페이지.

    ``trains`` 는 서버가 보낸 순서 그대로의 평평한 행 목록이고,
    ``itineraries`` 는 그것을 :func:`pair_transfer_itineraries` 로 짝지은
    것입니다. 앱도 둘 다 들고 있으므로 둘 다 내놓습니다 — ``a5/k.java`` 의
    ``f236n`` 이 ``i * 2`` 로 인덱싱하는 평평한 목록, ``f237o`` 가 화면에
    그리는 짝지은 목록입니다.
    """

    itineraries: list[TransferItinerary]
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 페이지 커서. 다음이 없으면 ``None``.

        ``h_next_pg_flg == "Y"`` 게이트는 직통과 같지만 커서가 다릅니다. 환승
        페이지에는 필드가 둘 더 오고, 앱은 그것으로 ``qryStTrnNo`` 를
        ``h_prcd_trn_no_next`` 로 덮어쓰고 ``qryStTrnNo2`` 에
        ``h_ectb_trn_no_next`` 를 넣습니다(``RsvInquiryRequest.java:212-215``).

        앱이 그 덮어쓰기를 **둘 다 비어 있지 않을 때만** 하므로 여기서도
        같습니다. 하나라도 없으면 직통과 같은 커서를 그대로 씁니다.
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
