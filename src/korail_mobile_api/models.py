# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공통 응답 봉투와 열차 검색·좌석 조회가 돌려주는 타입.

전부 ``frozen=True`` 데이터클래스입니다. 서버가 준 원본은 어느 모델에서든
``raw`` 에 그대로 남아 있으므로, 이 패키지가 이름을 붙이지 않은 필드도
거기서 꺼낼 수 있습니다. ``repr=False`` 인 필드는 로그에 실수로 찍히지 않게
표현에서 뺀 것이지 값이 없는 것이 아닙니다.

승차권·환불·마이페이지 쪽 읽기 모델은
:mod:`korail_mobile_api.read_models`, 상태변경 요청·응답 모델은
:mod:`korail_mobile_api.mutation_models` 에 있습니다.
"""

from dataclasses import dataclass, field, replace
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
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    member_card_no: str | None = field(default=None, repr=False)
    customer_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class BaseKorailResponse:
    """모든 응답이 공유하는 봉투. 다른 응답 모델은 전부 이것을 상속합니다.

    이 데이터클래스는 봉투 세 필드를 **담기만** 합니다 -- 무엇이 실패인지는
    정하지 않습니다(:meth:`from_raw` 는 값을 보지 않습니다). 판정하는 쪽은
    :func:`~korail_mobile_api.http.parse_base_response` 이고, 거기서 오류를
    만드는 검사는 ``str_result`` 하나가 아닙니다:

    * ``h_msg_cd`` 가 ``P058``
      (:data:`~korail_mobile_api.errors.SESSION_EXPIRED_CODE`)이면
      ``str_result`` 와 무관하게, ``raise_on_fail`` 이 꺼져 있어도
      :class:`~korail_mobile_api.errors.KorailSessionExpiredError`
      입니다(``http.py:147-152``).
    * ``raise_on_fail`` 이 참이면 ``str_result == "FAIL"`` 말고도
      ``h_msg_cd == "WRC000288"`` 이, 그리고 ``require_result`` 일 때는
      ``strResult`` 키 부재가 각각 따로 실패가 됩니다
      (``http.py:153-162``). ``WRC000288`` 을 실패로 치는 7.0.6 근거는
      ``parse_base_response`` 독스트링이 미출처로 남겨 둡니다.

    ``h_msg_cd``/``h_msg_txt`` 는 서버의 코드와 문구이며, 위 두 코드가 아닌
    한 코드가 있다고 실패인 것은 아닙니다 -- 성공에 경고가 딸려 오는 경우가
    있습니다. 실패일 때 코드가 어느 예외가 되는지는
    :func:`~korail_mobile_api.errors.classify_app_error` 를 참조하면 됩니다.

    ``raw`` 는 파싱 전 JSON 전체입니다.
    """

    h_msg_cd: str | None = None
    #: 서버가 호출자의 입력을 되받아 적을 수 있어 repr 에 싣지 않습니다. 하위
    #: 클래스는 이 선언을 물려받으므로 다시 적을 필요가 없습니다.
    h_msg_txt: str | None = field(default=None, repr=False)
    str_result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "BaseKorailResponse":
        """봉투 세 필드를 그대로 옮겨 담아 응답을 만듭니다.

        ``raw`` 가 JSON 객체가 아니면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 값이
        무엇인지는 보지 않습니다 — 실패 판정은 호출자 몫입니다.
        """
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
    #: ``CNTAURL`` — 업데이트 안내가 열 스토어 딥링크(2026-09-22 라이브에서
    #: ``market://details…``로 시작하는 문자열). 7.0.6 DTO 가 선언하는 필드는
    #: 정확히 셋이고(``MobilePlusMainVersion.java:52`` 의 역직렬화 생성자가
    #: ``@SerialName("NEWDVERSION")``/``@SerialName("CNTAURL")``/
    #: ``@SerialName("AMESSAGE")`` 딱 그 셋), 그중 이것만 여기 없었습니다 —
    #: 안내 문구와 새 버전은 있는데 정작 보낼 곳이 없는 2/3짜리였습니다.
    #: 앱은 ``AppKt.java:1240``·``:1323`` 에서 ``getCntAUrl()`` 로 읽어
    #: ``AppKt.java:1635`` 의 ``DialogsKt.StoreConfirmDialog(...)`` 에 넘깁니다.
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
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)

    @property
    def uses_station_selection(self) -> bool:
        return (
            self.active == "Y"
            and self.menu_type != "N"
            # ``appData`` 가 ``"N"`` 일 때만 역 목록이 비어 있습니다. 허용
            # 목록으로 두지 않는 것은 ``{"Y", "M10", "M30"}`` 밖의 값이
            # 실제로 오기 때문입니다 — 2026-09-22 라이브: ``appData='C'``(부가서비스
            # 코드 ``604``)가 ``get_maas_station_data`` 로 역 15개를 돌려줬습니다.
            # 같은 호출에서 ``'N'``(코드 ``001``)만
            # 0개였고, ``'Y'``/``'M30'`` 은 25~111개였습니다.
            and self.app_data not in (None, "", "N")
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
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    group: str | None = None
    major: str | None = None
    #: 7.0.6 ``StationDataOutStnItem.java:60`` declares
    #: ``@SerialName("popupType") String`` -- kept as a string, not coerced.
    popup_type: str | None = None
    popup_message: str | None = field(default=None, repr=False)
    popup_link_title: str | None = None
    popup_link_url: str | None = None


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    stations: tuple[KorailStation, ...] = ()


@dataclass(frozen=True)
class StationInfoResponse(BaseKorailResponse):
    #: 7.0.6 ``StationInfoOut.java:47`` declares ``@SerialName("count")
    #: String`` (same non-null String shape as ``map_version``) -- kept as a
    #: string, not coerced to ``int``.
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
        repr=False,
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
    actual_arrival_delay_count: int | None = None
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
        repr=False,
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
        repr=False,
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
    """열차 검색 한 번의 조건.

    두 역 필드는 역코드와 역이름을 **둘 다** 받습니다. 이름은 그대로 나가고,
    코드를 주면 클라이언트가 역 목록을 조회해 이름으로 바꿉니다. 날짜는
    ``YYYYMMDD``, 시각은 ``HHMMSS`` 이며 그 시각 **이후** 열차를 줍니다.

    ``train_group_code`` 기본값 ``"109"`` 는 열차 종류 제한 없음("전체")입니다.
    7.0.6 에도 그 열거형 멤버는 있습니다 — ``TrainGroup.ALL``(선언
    ``TrainGroup.java:29``, 생성 ``:335``, 멤버 목록은 ``:25`` 의 Kotlin 메타데이터
    ``"EMPTY","ALL","KTX",...``). **다만 ``trnGpCd`` 값 ``"109"`` 자체는 7.0.6 에서
    읽을 수 없습니다**: 생성 인자가 ``AlienGuard1789016769018.method_name_4(...)``
    호출이고 ``TrainGroup.smali`` 에는 ``const-string`` 이 한 줄도 없습니다(전수
    확인). 따라서 이 숫자는 실서버 관측에 기댑니다. ``include_srt`` 는
    ``ebizCrossCheck``/``srtCheckYn`` 한 쌍을 ``"Y"`` 로 만듭니다 — 앱은 이
    둘을 항상 같은 값으로 보냅니다.

    7.0.6 ``ScheduleViewSpecial`` 에서는 환승역 코드 목록과 후속 열차군
    코드를 지정할 수 있습니다. 정렬별 ``qryDvCd`` 값은 APK에서 보호되므로
    ``query_division_code`` 는 전선 코드를 알고 있을 때 직접 지정합니다.

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


def _train_scalar(value: Any, key: str) -> str | None:
    """검색 행의 필드 하나를 JSON 문자열로도 JSON 숫자로도 받아들입니다.

    KORAIL 은 APK 가 ``String`` 으로 선언한 필드를 둘 중 어느 쪽으로 보낼지
    일관되지 않습니다.

    7.0.6 의 이 응답은 Gson 이 아니라 kotlinx-serialization 으로 읽힙니다. 라우트는
    ``network/NetworkApi.java:658-660`` 의 ``postScheduleView`` 이고
    (``@FormUrlEncoded`` ``@POST(".../seatMovie.ScheduleView")`` →
    ``Response<TrainScheduleOut>``), 행 DTO
    ``network/model/TrainScheduleOutTrainInfo.java`` 는 ``:25-27`` 에서
    ``kotlinx.serialization`` 을 임포트하고 ``:36-37`` 에서 ``@Serializable``
    로 선언됩니다(``h_dpt_tm`` 은 ``:63`` 의 ``String hDptTm``, 키 표기는
    ``:1152``). 생성된 ``TrainScheduleOutTrainInfo$$serializer.java:35`` 는
    ``GeneratedSerializer`` 구현이고, ``:40-44`` 에서
    ``PluginGeneratedSerialDescriptor.addElement(..., true)`` 로 원소를 전부
    optional 로 잡은 뒤, ``:162-165`` 의 ``childSerializers()`` 가 내놓는
    ``StringSerializer.INSTANCE`` 로 ``:439-445`` 에서 원소마다 디코드합니다.
    ``network/`` 아래 Gson 참조는 전수 grep 에서 0 건입니다.

    **앱도 JSON 숫자를 받아 주는지는 알 수 없습니다.** 그것을 정하는 것은 ``Json`` 의 ``isLenient`` 인데,
    ``network/di/NetworkModule.java:862``(``providesNetworkJson``)와
    ``network/NetworkServiceKt.java:29`` 의 ``setLenient(...)`` 인자가 둘 다
    AlienGuard 암호문이라 켜졌는지 읽을 수 없습니다. 읽히는 것은 구조뿐입니다
    — 같은 암호문 리터럴이 ``ignoreUnknownKeys``·``encodeDefaults``·
    ``coerceInputValues`` 에도 그대로 쓰이고 ``explicitNulls`` 만 다른 리터럴을
    씁니다.

    따라서 아래의 관대함은 앱 재현이 아니라 **이 패키지의 정책**입니다.
    ``"h_dpt_tm": 63000`` 으로 온 행을 거부하면 실제로 예약 가능한 열차가
    목록에서 사라지므로 받아서 문자열로 정규화합니다.

    둘을 받는 것이 아무거나 받는 것은 아닙니다. ``bool``, ``float``, 리스트,
    객체는 여전히
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다 — 문자열로
    바꿔 넘기면 정말로 달라진 응답을 가리게 되기 때문이고, 이 경계 역시 앱
    인용이 아니라 이 패키지의 결정입니다.

    서버가 이미 떨군 자릿수를 되살리지는 못합니다. 여섯 자리
    ``h_dpt_tm`` 이 ``63000`` 으로 왔다면 앞의 0 은 바이트가 도착하기 전에
    사라진 것이고, 그것은 ``mutation_payloads`` 의 자릿수 검사가 잡습니다.
    """
    if value is None or isinstance(value, str):
        return value
    # isinstance 가 아니라 type(...) is int 인 것은 의도다. bool 이 int 의
    # 하위 타입이고, True 는 KORAIL 이 이런 필드로 보내는 숫자가 아니다.
    if type(value) is int:
        try:
            return str(value)
        except ValueError:
            # 파이썬의 정수→문자열 자릿수 한도(기본 4,300자리)를 넘으면 ``str()``
            # 이 ``ValueError`` 를 냅니다. 이 패키지의 예외로 올립니다.
            raise KorailProtocolError(
                f"KORAIL train field {key} integer is too large"
            ) from None
    raise KorailProtocolError(
        f"KORAIL train field {key} must be a string, an integer, or null"
    )


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


#: TrainSummary 의 ``train_no``·``goods_no``·``total_passenger_count`` 를 뺀 필드와
#: 그 필드를 읽는 키. 세 번째 칸이 있으면 첫 키가 없거나 거짓일 때 그 철자를
#: 읽습니다(``h_trn_gp_cd`` 와 ``trnGpCd`` 등). 오류는 언제나 첫 키 이름으로 냅니다.
_TRAIN_SUMMARY_KEYS: tuple[tuple[str, str, str | None], ...] = (
    ("train_group_code", "h_trn_gp_cd", "trnGpCd"),
    ("departure_station_code", "h_dpt_rs_stn_cd", "dptRsStnCd"),
    ("arrival_station_code", "h_arv_rs_stn_cd", "arvRsStnCd"),
    ("departure_station_name", "h_dpt_rs_stn_nm", "dptRsStnNm"),
    ("arrival_station_name", "h_arv_rs_stn_nm", "arvRsStnNm"),
    ("departure_date", "h_dpt_dt", "dptDt"),
    ("departure_time", "h_dpt_tm", "dptTm"),
    ("arrival_time", "h_arv_tm", "arvTm"),
    ("run_date", "h_run_dt", "runDt"),
    ("train_class_code", "h_trn_clsf_cd", "trnClsfCd"),
    ("departure_run_order", "h_dpt_stn_run_ordr", "dptStnRunOrdr"),
    ("arrival_run_order", "h_arv_stn_run_ordr", "arvStnRunOrdr"),
    ("seat_map_flag", "h_rd_seat_map_flg", None),
    ("general_reservation_code", "h_gen_rsv_cd", None),
    #: ``h_gen_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:83``. 일반실
    #: 예약가능 플래그 원시값(코드가 아니라 플래그).
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
    #: ``h_spe_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:108`` (Java 필드명
    #: ``hSpRsvFlg``). 특실 예약가능 플래그.
    ("special_reservation_flag", "h_spe_rsv_flg", None),
    ("secondary_special_reservation_code", "h_spe_rsv_cd2", None),
    ("free_reservation_code", "h_free_rsv_cd", None),
    #: ``h_free_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:75``. 자유석
    #: 예약가능 플래그.
    ("free_reservation_flag", "h_free_rsv_flg", None),
    ("standing_reservation_code", "h_stnd_rsv_cd", None),
    #: ``h_stnd_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:151`` (Java
    #: 필드명 ``h_stnd_rsv_flg`` 그대로). 입석 예약가능 플래그.
    ("standing_reservation_flag", "h_stnd_rsv_flg", None),
    #: ``h_rsv_psb_flg`` -- ``TrainScheduleOutTrainInfo.java:100``. 열차
    #: 전체의 예약가능 여부를 정하는 최상위 플래그(등급별
    #: ``*_reservation_flag`` 와 별개).
    ("reservation_available_flag", "h_rsv_psb_flg", None),
    # 잔여 문구는 ``h_gen_rsv_nm``/``h_spe_rsv_nm`` 입니다.
    # ``h_rsv_psb_nm``/``h_spe_rsv_psb_nm`` 는 이름과 달리 문구가
    # 아니라 **운임**입니다 -- 2026-09-22 라이브(서울→부산 20260925) 확인:
    # 같은 행에서 ``h_gen_rsv_nm='매진'`` 인데 ``h_rsv_psb_nm='47,500원'``.
    # ``"매진"``/``"좌석부족"`` 은 앞의 키에만 옵니다.
    ("general_availability_name", "h_gen_rsv_nm", None),
    ("special_availability_name", "h_spe_rsv_nm", None),
    #: ``h_stnd_rsv_nm``/``h_free_rsv_nm`` -- 입석·자유석 쪽의 같은 화면 문구.
    #: ``TrainScheduleOutTrainInfo.java:1380``/``:1196`` 의 ``@SerialName``
    #: 이고, 합성 생성자(``:172``)에서 이미 읽고 있던 일반실
    #: ``h_gen_rsv_nm``(str42)·특실 ``h_spe_rsv_nm``(str47) 바로 옆의
    #: str51/str53 입니다.
    ("standing_availability_name", "h_stnd_rsv_nm", None),
    ("free_availability_name", "h_free_rsv_nm", None),
    ("general_fare_text", "h_rsv_psb_nm", None),
    ("special_fare_text", "h_spe_rsv_psb_nm", None),
    ("wait_reservation_flag", "h_wait_rsv_flg", None),
    ("standard_remaining_seat_count", "h_std_rest_seat_cnt", None),
    ("first_class_remaining_seat_count", "h_fst_rest_seat_cnt", None),
    #: ``h_free_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:73``.
    #: 자유석 잔여석 수 -- ``h_std_rest_seat_cnt``/``h_fst_rest_seat_cnt`` 의
    #: 셋째 등급.
    ("free_remaining_seat_count", "h_free_rest_seat_cnt", None),
    #: ``h_stnd_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:150``
    #: (Java 필드명 ``h_stnd_rest_seat_cnt`` 그대로). 입석 잔여석 수.
    ("standing_remaining_seat_count", "h_stnd_rest_seat_cnt", None),
    ("free_car_count", "h_free_sracar_cnt", None),
    ("reservation_wait_passenger_count", "h_rsv_wait_ps_cnt", None),
    ("change_train_sequence", "h_chg_trn_seq", None),
    ("change_train_division_code", "h_chg_trn_dv_cd", None),
    ("merge_seat_application_flag", "h_yms_apl_flg", None),
    ("train_suspension_flag", "h_trn_sps_flg", None),
)


def _train_value(raw: dict[str, Any], key: str, fallback: str | None) -> str | None:
    value = raw.get(key)
    if fallback is not None:
        value = value or raw.get(fallback)
    return _train_scalar(value, key)


@dataclass(frozen=True)
class TrainSummary:
    """열차 검색 결과의 한 행. 예약 폼이 필요한 값이 전부 여기 있습니다.

    :meth:`~korail_mobile_api.client.KorailClient.reserve` 는 이 객체를
    그대로 받으므로 열차번호·역코드·날짜·시각을 손으로 옮겨 적을 일이
    없습니다.

    좌석 여유는 이름이 비슷한 코드가 여럿이라 헷갈리기 쉽습니다.
    ``general_reservation_code``/``special_reservation_code`` 는 일반실·특실의
    예약 가능 코드이고, ``general_availability_name``/
    ``special_availability_name``(``h_gen_rsv_nm``/``h_spe_rsv_nm``)이 화면에
    찍히는 문구입니다(``"매진"``, ``"매진임박"``, 없으면 ``"-"``). 입석·자유석도
    같은 짝이 있습니다 — 코드는
    ``standing_reservation_code``/``free_reservation_code``, 문구는
    :attr:`standing_availability_name`/:attr:`free_availability_name`.

    ``h_rsv_psb_nm``/``h_spe_rsv_psb_nm`` 은 이름만 "예약가능"이고 값은
    **운임**이라 :attr:`general_fare_text`/:attr:`special_fare_text` 로
    따로 둡니다 — 2026-09-22 라이브(서울→부산 20260925)에서 한 행이
    ``h_gen_rsv_nm='매진'`` 과 ``h_rsv_psb_nm='47,500원'`` 을 동시에 줬습니다.

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
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    run_date: str | None = None
    train_class_code: str | None = None
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    seat_map_flag: str | None = None
    general_reservation_code: str | None = None
    #: ``h_gen_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:83``. 일반실
    #: 예약가능 플래그.
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
    #: ``h_spe_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:108`` (Java
    #: 필드명 ``hSpRsvFlg``). 특실 예약가능 플래그.
    special_reservation_flag: str | None = None
    secondary_special_reservation_code: str | None = None
    free_reservation_code: str | None = None
    #: ``h_free_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:75``. 자유석
    #: 예약가능 플래그.
    free_reservation_flag: str | None = None
    standing_reservation_code: str | None = None
    #: ``h_stnd_rsv_flg`` -- ``TrainScheduleOutTrainInfo.java:151`` (Java
    #: 필드명 ``h_stnd_rsv_flg`` 그대로). 입석 예약가능 플래그.
    standing_reservation_flag: str | None = None
    #: ``h_rsv_psb_flg`` -- ``TrainScheduleOutTrainInfo.java:100``. 열차
    #: 전체의 예약가능 여부를 정하는 최상위 플래그.
    reservation_available_flag: str | None = None
    general_availability_name: str | None = None
    special_availability_name: str | None = None
    wait_reservation_flag: str | None = None
    standard_remaining_seat_count: str | None = None
    first_class_remaining_seat_count: str | None = None
    #: ``h_free_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:73``.
    #: 자유석 잔여석 수.
    free_remaining_seat_count: str | None = None
    #: ``h_stnd_rest_seat_cnt`` -- ``TrainScheduleOutTrainInfo.java:150``
    #: (Java 필드명 ``h_stnd_rest_seat_cnt`` 그대로). 입석 잔여석 수.
    standing_remaining_seat_count: str | None = None
    free_car_count: str | None = None
    reservation_wait_passenger_count: str | None = None
    total_passenger_count: int | None = None
    goods_no: str | None = None
    #: ``h_chg_trn_seq`` — 환승 여정 안에서 이 구간의 위치. 1구간이 ``"1"``,
    #: 2구간이 ``"2"`` 입니다. 키는 7.0.6 에서 확인됩니다
    #: (``TrainScheduleOutTrainInfo.java:53,172,1112`` 의
    #: ``@SerialName("h_chg_trn_seq")``; 같은 키를 ``TrainList.java:35,234`` 도
    #: 선언합니다). **``"1"``/``"2"`` 라는 값의 뜻은 디컴파일이 아니라 아래 실서버
    #: 관측에서 온 것입니다.**
    #:
    #: 직통 검색에서도 ``None`` 이 아닙니다 — 직통도 서버가
    #: ``"1"`` 을 채워 보냅니다. 2026-09-22 라이브 직통 검색 6건(서울→부산
    #: 20260925 060000·000000, 서울→부산 20261015, 서울→동대구 20260927,
    #: 용산→목포 20260926, 동대구→서울 20260927)의 **모든** 행이
    #: ``h_chg_trn_seq='1'`` 이었습니다. "``None`` 이면 직통"으로 분기하면
    #: 직통 열차가 한 건도 걸리지 않습니다. 환승 검색에서는 구간별로
    #: ``"1"``/``"2"`` 가 옵니다(같은 날 강릉→목포 1여정, 목포→강릉 5여정 =
    #: 12개 구간 전부).
    #:
    #: ``h_chg_trn_dv_cd``(:attr:`change_train_division_code`) 와 헷갈리기
    #: 쉽습니다. 이쪽은 여정 **안에서의 순서**, 저쪽은 여정 **종류**입니다.
    #:
    #: 앱이 이 필드로 페이지를 중복 제거하거나 ``txtGoHour`` 를 되싣는지는
    #: **7.0.6 미출처입니다.** ``getHChgTrnSeq()`` 를 DTO 밖에서 부르는 자리는 7.0.6 전체에 딱 하나
    #: (``SRTWebReserveTrainItem.java:115-137``, SRT 웹 예약 항목 변환)뿐이며 그것도
    #: 비교·대입 리터럴이 AlienGuard 로 보호돼 있어 무엇과 견주는지 읽을 수
    #: 없습니다(전수 grep 확인). 즉 이 필드로 페이지를 중복 제거하거나 다음 질의를
    #: 만드는 7.0.6 근거는 없습니다.
    change_train_sequence: str | None = None
    #: ``h_chg_trn_dv_cd`` — 행의 환승 구분. 직통 검색에서도 값이 옵니다. 2026-09-22
    #: 라이브에서 직통 6건(서울→부산 20260925 060000·000000, 서울→부산
    #: 20261015, 서울→동대구 20260927, 용산→목포 20260926, 동대구→서울
    #: 20260927)의 모든 행이 ``'1'``(같은 행의 ``h_chg_trn_dv_nm='직통'``),
    #: 환승 6여정 12구간(강릉→목포·목포→강릉 20260926)이 전부
    #: ``'2'``(``h_chg_trn_dv_nm='환승'``)였습니다. 관측된 두 값은
    #: :data:`~korail_mobile_api.constants.KORAIL_DIRECT_ITINERARY_CODE`/
    #: :data:`~korail_mobile_api.constants.KORAIL_TRANSFER_ITINERARY_CODE`
    #: 와 같은 자릿값이지만, 그 상수는 검색 job id 씨앗이라 여기서 쓰지
    #: 않습니다.
    #:
    #: ``h_chg_trn_dv_cd``/``getHChgTrnDvCd`` 는 7.0.6 전체
    #: 소스·스몰리를 뒤져도 DTO 선언 밖에서 읽히는 자리가 없습니다(전수
    #: grep 확인). 7.0.6 은 대신 서버가 준 ``h_trn_seq`` 로 행을 묶는 것으로
    #: 보입니다 — 자세한 근거와 한계는
    #: :func:`~korail_mobile_api.models.pair_transfer_itineraries` 의
    #: docstring을 보십시오.
    change_train_division_code: str | None = None
    #: ``h_yms_apl_flg`` — 병합(입석+좌석) 예약 판정에 쓰는 행 플래그. 키 자체는
    #: 7.0.6 에서 확인됩니다(``TrainScheduleOutTrainInfo.java:147,1480`` 의
    #: ``@SerialName("h_yms_apl_flg")``).
    #:
    #: **"이 행이 병합 대상인지를 정하는 유일한 입력"이라는 서술은 7.0.6 에서
    #: 뒷받침되지 않습니다 — 미출처.** 이름이 맞는 함수는 있는데(``SeatHelper.java:288-327``
    #: ``isMixedSeat(String seatClass, String standingSeatCode)``) 두 번째 인자가
    #: yms 플래그가 아니라 **입석 좌석 코드**로 이름 붙어 있고, 비교 리터럴은
    #: AlienGuard 로 보호돼 있으며, 7.0.6 소스·스몰리 전체에 이 함수를 부르는 자리가
    #: 없습니다. ``hYmsAplFlg`` 역시 DTO 선언(``TrainScheduleOutTrainInfo``) 밖에서
    #: 읽히는 자리가 소스·스몰리 어디에도 없습니다(전수 grep). 병합 예약 job id
    #: 멤버는 존재하지만(``ReservationJobId.java:23`` 의 ``MERGE``) 그 코드값
    #: ``"1202"`` 도 보호돼 있어 평문으로 읽히지 않습니다. 이 필드를 계속 파싱하는
    #: 이유는 실서버에서 값이 오기 때문이며, 그 해석은
    #: :data:`~korail_mobile_api.constants.KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`
    #: 쪽 관측 기록을 보십시오.
    merge_seat_application_flag: str | None = None
    #: 7.0.6 h_trn_sps_flg: 운휴 표시/예약 게이트용 원표 플래그.
    train_suspension_flag: str | None = None
    #: ``h_rsv_psb_nm`` — 일반실 **운임** 문구(``"47,500원"``). 이름이
    #: 예약가능("rsv_psb")처럼 보이지만 실제로 담겨 오는 값은 금액입니다.
    #: 잔여 문구는 :attr:`general_availability_name` 쪽입니다.
    general_fare_text: str | None = None
    #: ``h_spe_rsv_psb_nm`` — 특실 **운임** 문구. 위와 같은 이유로 이름과
    #: 내용이 어긋나는 키라, 잔여 문구는 :attr:`special_availability_name`
    #: 에서 읽습니다.
    special_fare_text: str | None = None
    #: ``h_stnd_rsv_nm`` — 입석 잔여 화면 문구.
    #: :attr:`standing_reservation_code`(``h_stnd_rsv_cd``)가 코드이고 이쪽이
    #: 사람이 읽는 글자라, 둘 다 있어야 화면을 그대로 재현할 수 있습니다.
    #: 2026-09-22 라이브 값: ``'매진'``(서울→부산 20260925, 동대구→서울
    #: 20260927), ``'역발매중'``(용산→목포 20260926), ``'-'``(서울→부산
    #: 20261015 일부 행).
    standing_availability_name: str | None = None
    #: ``h_free_rsv_nm`` — 자유석 쪽 같은 문구. 값에 줄바꿈이 들어옵니다 —
    #: 2026-09-22 서울→부산 20261015 에서 ``'역발매중\n(1량)'``,
    #: ``'역발매중\n(2량)'`` 을 받았습니다. 한 줄에 찍을 곳이라면 호출자가
    #: 직접 다듬어야 합니다.
    free_availability_name: str | None = None

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
            train_no=_train_value(raw, "h_trn_no", "trnNo") or "",
            **{
                attr: _train_value(raw, key, fallback)
                for attr, key, fallback in _TRAIN_SUMMARY_KEYS
            },
            total_passenger_count=_train_optional_int(raw, "totPsgCnt"),
            # 좌석 조회 폼이 넘길 수 있게 열차 행에서 상품번호
            # (h_gd_no / txtGdNo)를 붙잡아 둔다. 7.0.6 도 이 라우트에 txtGdNo
            # 자리를 두고 있다(TrainResearchIn.java:68 의
            # @SerialName("txtGdNo"), 직렬화 조건은 :275-278). 좌석 재고 요청을 만드는 7.0.6 자리는
            # TrainSeatMapViewModel.java:1974-1976 의
            # buildTResidualSeatsResearch(TrainResearchOutCarInfo,
            # TrainResearchIn) 이고, :1975 가 trainResearch.getTxtGdNo() 를 읽어
            # :1976 에서 TResidualSeatsResearchIn 의 13번째 인자로 넘긴다 —
            # 즉 열차 "행"이 아니라 조회 요청(TrainResearchIn)에서 온다.
            # 그 TrainResearchIn 을 실제로 채우는 자리는
            # TrainSeatMapViewModel.java:2527(txtGdNo =
            # ticketReservationIn.getTxtGdNo())이고 :2546 에서 TrainResearchIn
            # 의 16번째 인자로 들어간다 — 결국 예약 입력에서 온다.
            # 읽기 쪽 철자 h_gd_no 가 7.0.6 에 선언된 곳은 스케줄 응답 봉투
            # 하나뿐이다(TrainScheduleOut.java:184 의 @SerialName("h_gd_no"),
            # 필드는 :29, 행 목록 trn_infos 는 :232). 행 DTO
            # TrainScheduleOutTrainInfo 에는 GdNo 가 0건이므로 "열차 행이 이
            # 값을 싣는다"는 것 자체는 7.0.6 미출처다 — 서버 응답이 행에
            # 싣는지는 별개 문제이고, 이 파서는 두 철자 모두 없으면 None 으로
            # 남긴다. 이 패키지는 예약 입력을 만들기 전에도 좌석 조회를 할 수
            # 있어야 해서 같은 값을 행에 붙여 나른다. 다른 두 철자 필드와
            # 달리 첫 키가 거짓이어도 먼저 검사한다.
            goods_no=(
                _train_value(raw, "h_gd_no", None) or _train_value(raw, "txtGdNo", None)
            ),
            raw=raw,
        )


@dataclass(frozen=True)
class SeatAttribute:
    name: str
    code: str | None = None


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
    recommended_car_no: int | None = None
    train_no: str | None = None
    cars: tuple[SeatCar, ...] = ()
    train_class_code: str | None = None
    train_group_code: str | None = None
    #: ``h_scar_num`` -- ``TrainResearchOut.java:27,105``, one of the DTO's
    #: 6 own fields (``@SerialName("h_scar_num") String``, nullable). Kept
    #: as a string like its sibling ``train_no``/``train_class_code``, not
    #: coerced to ``int``.
    car_count: str | None = None


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

    ``floor`` 는 항상 ``None`` 입니다 — ``TResidualSeatsResearchOutSeat`` 의
    10개 own 필드(``TResidualSeatsResearchOutSeat.java:32-41``) 어디에도
    ``floor`` 가 없습니다. 복층 차량 층 표시는 이 라우트로는 구조적으로
    불가능하고, 서버가 그 정보를 다른 경로로 주는지는 확인되지 않았습니다.
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
    message: str
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

    #: 7.0.6 ``TResidualSeatsResearchOut.java:29`` declares
    #: ``@SerialName("layout_type") String``, but production sends a JSON
    #: integer (confirmed live 2026-09-21) -- the parser accepts either and
    #: normalizes to ``str``, matching this field's Python type.
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
    """검색 응답에서 열차 행이 아닌 부분 — 주로 다음 페이지 커서.

    직접 읽을 일은 거의 없습니다. 다음 페이지는
    :meth:`TrainSearchResult.next_page` 가 이 값들로 만들어 줍니다.

    다만 직통 검색에서는 ``next_page_flag='Y'`` 인데
    ``next_query_station_no``/``next_train_no`` 가 둘 다 ``None`` 으로
    옵니다(2026-09-22 라이브 6건). 플래그만 보고 "다음 페이지가 있다"고 읽지
    마십시오 — 자세한 것은 :meth:`TrainSearchResult.next_page` 의 설명에
    있습니다.

    7.0.6 ``TrainScheduleOut`` 는 ``h_menu_id`` 를 선언합니다. 요청의
    ``txtMenuId`` 와 별도로 서버가 되돌려 준 값을 보존합니다.
    """

    job_id: str | None = None
    menu_id: str | None = None
    product_no: str | None = None
    next_page_flag: str | None = None
    next_query_station_no: str | None = None
    next_train_no: str | None = None
    #: 커서의 환승 쪽 절반(``h_prcd_trn_no_next``/``h_ectb_trn_no_next``). 두 키는
    #: 7.0.6 응답 DTO 에 있습니다(``TrainScheduleOut.java:28,33``, ``@SerialName``
    #: 목록은 ``:67``). 직통 검색은 둘 다 비워 보냅니다(실서버 관측).
    #:
    #: 이 값을 되싣는 자리는 7.0.6 에서 스몰리로만 읽힙니다 — jadx 가
    #: ``TrainScheduleViewModel.responseTrainSchedule`` 의 본문 복원에 실패해
    #: ``getHPrcdTrnNoNext()``/``getHEctbTrnNoNext()`` 호출이 자바 출력에 아예
    #: 나오지 않습니다(전수 grep). 스몰리에서는
    #: ``analysis/apktool/smali_classes5/com/korail/talk/ui/screen/train/TrainScheduleViewModel.smali``
    #: 의 ``responseTrainSchedule``(선언 ``:34670``)이 ``:36806-36845`` 에서
    #: ``Triple(getHQryStNoNext(), getHPrcdTrnNoNext(), getHEctbTrnNoNext())`` 를
    #: 만들어 ``:36851`` 에서 ``nextTrainScheduleData`` 에 넣고,
    #: ``TrainScheduleViewModel.java:7340`` 이 그 3튜플을
    #: ``TrainScheduleIn.copy$default`` 의 31·32·33번째 인자 —
    #: ``TrainScheduleIn.java:95`` 의 ``@SerialName`` 순서대로
    #: ``qryStNo``/``qryStTrnNo``/``qryStTrnNo2`` — 로 넘깁니다.
    #:
    #: 같은 스몰리 블록에서 직통형과 환승형을 고르는 것은 두 값의 공백 여부가 아니라
    #: ``:35654-35698`` 에서 ``getStrJobId()`` 의 결과를 보호된 리터럴과 견주고
    #: 그 결과를 뒤집은 값입니다 — 즉 서버가 되돌려 준 ``strJobId`` 를 보고
    #: 갈라집니다(그 리터럴의 평문은 AppSuit 보호로 읽히지 않습니다).
    #:
    #: 비교는 ``Intrinsics.areEqual`` 이 아니라 수신자가 ``null`` 인
    #: ``AppSuitLinker1.djsflxlftm1`` 반사 호출이고,
    #: 인자 둘을 받아 ``Boolean`` 을 돌려줄 뿐 실제 콜리는 인덱스 뒤에
    #: 가려집니다(2026-09-23 확인).
    #:
    #: 이 패키지가 "둘 다 비었으면 직통 커서" 규칙을 쓰는 이유는 실서버에서
    #: 검증된 동작이기 때문이며, 앱과의 차이는
    #: :meth:`TransferSearchResult.next_page` 에 적어 두었습니다.
    next_preceding_train_no: str | None = None
    next_connecting_train_no: str | None = None
    result_count: str | None = None
    #: ``h_notice_msg`` — 서버가 검색 결과에 붙이는 안내 문구
    #: (``TrainScheduleOut.java:32,67,196`` 의 ``@SerialName("h_notice_msg")``).
    #: 7.0.6 은 이 값이 비어 있지 않으면 그대로 경고 대화상자로 띄웁니다
    #: (``TrainScheduleViewModel.smali:36742-36786`` — ``getHNoticeMsg()`` 길이
    #: 검사 후 ``ScreenViewModel.alert$default``).
    notice_message: str | None = None
    # 7.0.6 TrainScheduleOut 이 셋 다 선언한다.
    first_seat_count: str | None = None
    second_seat_count: str | None = None
    first_departure_time: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class TrainSearchContinuation:
    """다음 페이지를 요청할 때 되싣는 커서.

    앱도 같은 방식입니다 — 앞 응답의 페이징 필드를 뷰모델에 들고 있다가
    ("더 보기" = ``TrainScheduleViewModel.inquiryNextTrainSchedule()``,
    ``TrainScheduleViewModel.java:10262-10279``) 다음 요청에 되싣습니다. 7.0.6 이
    들고 있는 것은 ``Triple<String, String, String> nextTrainScheduleData``
    (``TrainScheduleViewModel.java:205``)이고, ``TrainScheduleViewModel.java:7340``
    이 그 세 값을 ``TrainScheduleIn.copy$default`` 의 31·32·33번째 인자 —
    ``TrainScheduleIn.java:95`` 의 ``@SerialName`` 순서대로
    ``qryStNo``/``qryStTrnNo``/``qryStTrnNo2`` — 에 넣습니다.

    **``pgPrCnt`` 는 그 3튜플에 자리가 없습니다.** 7.0.6 의 연속 경로는 ``pgPrCnt``
    (``TrainScheduleIn`` 37번 요소)를 건드리지 않습니다. 이 클래스의
    ``page_count`` 를 :func:`~korail_mobile_api.payloads.build_train_search_form`
    이 전선에 싣지 않는 것이 그 때문입니다.

    ``query_train_no2`` 만 환승 검색의 것입니다. 직통 검색에서는 빈 문자열이며,
    여기서 비어 있어도 되는 유일한 필드입니다. 앱이 환승형 커서를 고르는 조건은
    두 값의 공백 여부가 아니라 응답의 ``strJobId`` 비교입니다 —
    :attr:`TrainSearchMetadata.next_preceding_train_no` 의 설명을 보십시오.

    손으로 만들지 말고 :meth:`TrainSearchResult.next_page` 나
    :meth:`TransferSearchResult.next_page` 가 주는 것을 쓰면 됩니다.
    """

    query_station_no: str
    query_train_no: str
    page_count: str = "10"
    query_train_no2: str = ""

    def __post_init__(self) -> None:
        for name in ("query_station_no", "query_train_no", "page_count"):
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
            page_count=metadata.result_count or "10",
            query_train_no2=query_train_no2,
        )
    except KorailProtocolError:
        return None


@dataclass(frozen=True)
class TrainSearchResult:
    """직통 열차 검색 한 페이지.

    ``trains`` 가 그 페이지의 행입니다. 비어 있을 수 있습니다 — 직통이 없을
    때 서버는 이렇게 갈립니다(2026-09-22 확인):

    * ``WRD000061`` — 직통은 없지만 **환승 대안이 있는** 경우.
      :class:`~korail_mobile_api.errors.KorailNoDirectTrainError` 가
      올라옵니다.
    * ``WRG000000`` + ``strResult=SUCC`` — ``trn_infos`` 자체가 없는 경우.
      아무것도 올라오지 않고 ``trains`` 가 빈 목록인 :class:`TrainSearchResult`
      가 그대로 돌아옵니다.

    그래서 예외를 잡는 것만으로는 부족하고, 호출자는 ``trains`` 가 비었는지도
    확인해야 합니다.

    ``response`` 는 봉투, ``metadata`` 는 페이징 커서입니다.
    """

    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 페이지 커서. 다음이 없으면 ``None``.

        **직통 검색에서는 사실상 언제나 ``None`` 입니다.** 서버가
        ``h_next_pg_flg='Y'`` 를 주면서 커서 두 키(``h_qry_st_no_next``,
        ``h_trn_no_next``)를 **둘 다** ``null`` 로 보내기 때문입니다 —
        2026-09-22 라이브 직통 6건(서울→부산 20260925 060000·000000,
        서울→부산 20261015, 서울→동대구 20260927, 용산→목포 20260926,
        동대구→서울 20260927)이 전부 그랬고, 반쯤 찬 커서는 아래 게이트가
        걸러 ``None`` 이 됩니다. 손으로 ``qryStNo`` 를 ``'000010'``/``'10'``/
        ``'11'``/``'1'`` 로 채우고 마지막 행의 열차번호를 ``qryStTrnNo`` 에
        실어 봐도 1페이지와 똑같은 10행이 돌아옵니다(같은 날 확인). 환승
        검색은 정상적으로 커서를 받으므로, 빠지는 쪽은 직통뿐입니다.

        라이브러리가 앱과 달라서 생긴 일이 아닙니다. 7.0.6 의 기본 화면
        (``ReservationType.DEFAULT`` — ``ReservationType.java:18``)도 직통이면
        같은 두 키로 커서를 만듭니다: ``nextTrainScheduleData =
        Triple(getHQryStNoNext(), getHTrnNoNext(), "")``
        (``TrainScheduleViewModel.smali:36814-36851``, 환승일 때만
        ``h_prcd_trn_no_next``/``h_ectb_trn_no_next`` 쌍). 그러니 앱의
        "더 보기"도 같은 벽에 부딪힙니다. 두 번째 페이지가 필요하면
        :meth:`next_query_from_last_departure` 를 쓰십시오.

        게이트 자체는 앱과 같습니다 — ``h_next_pg_flg`` 가 ``"Y"`` 인 동안만
        "더 보기"가 살아 있습니다. 7.0.6 근거는
        ``TrainScheduleViewModel.smali:35700-35730``(``getHNextPgFlg()`` 를 보호된
        리터럴 하나와 비교해 불리언을 만듦)과 그 불리언으로 커서 생성을 막는
        ``:36786``(``if-eqz`` → 커서 ``null``)입니다. 비교 리터럴이 AppSuit 로
        보호돼 있어 그 값이 ``"Y"`` 라는 것은 실서버 관측에서 왔습니다. 7.0.6 은
        파싱된 행 목록이 비어 있을 때도 커서를 만들지 않습니다(``:36790-36806``).
        커서 필드가 하나라도
        빠져 있어도 ``None`` 입니다. 반쯤 채운 커서는 조용히 1페이지를 다시
        요청하기 때문입니다.
        """
        metadata = self.metadata
        return _train_search_continuation(
            metadata, query_train_no=metadata.next_train_no or ""
        )

    def next_query_from_last_departure(
        self,
        query: TrainSearchQuery,
    ) -> TrainSearchQuery | None:
        """마지막 행의 출발일시로 옮겨 적은 다음 질의. 행이 없으면 ``None``.

        :meth:`next_page` 가 직통에서 커서를 못 받으므로, 두 번째 페이지를
        얻는 길은 이것뿐입니다. ``query`` 를 그대로 복사하면서
        ``departure_date``/``departure_time`` 만 마지막 행의
        ``h_dpt_dt``/``h_dpt_tm`` 로 바꿔 돌려줍니다. 아무것도 호출하지
        않으므로 받은 질의를
        :meth:`~korail_mobile_api.client.KorailClient.search_trains` 에 다시
        넘기는 것은 호출자 몫입니다. 두 값 중 하나라도 비어 있으면 ``None``
        입니다 — 반쯤 옮긴 질의는 엉뚱한 날짜를 조회하기 때문입니다.

        **경계 행 한 줄이 겹칩니다.** 검색은 주어진 시각 "이후"를 포함하니
        1페이지 마지막 행이 2페이지 첫 행으로 다시 옵니다 — 2026-09-22
        라이브(서울→부산 20260925 060000, 마지막 행 ``'015'``
        ``h_dpt_tm='075000'``)에서 2페이지 10행의 첫 행이 같은 ``'015'``,
        나머지 9행이 새 열차였습니다. 이어 붙일 때 ``train_no`` 로 한 줄을
        버리십시오.

        앱에도 같은 방식이 있지만 **다른 화면의 것**입니다.
        ``TrainScheduleViewModel`` 은 마지막 행의
        ``getHDptDt()``/``getHDptTm()`` 을 ``nextTrainScheduleDataOld`` 에
        담아 두었다가(smali:36938-36956) ``txtGoAbrdDt``/``txtGoHour``
        (``TrainScheduleIn.java:872`` ``copy()`` 의 8·9번 인자)로 되싣는데, 그
        분기는 ``screenMode`` 가 ``MY_N_CARD_RESERVATION``/
        ``MY_TICKET_RESERVATION``/``MY_PASS_RESERVATION``/
        ``MY_PASS_RESERVATION_MULTILINGUAL`` 일 때만 탑니다
        (smali:29590-29616 의 비교가 ``:cond_b``(29740)로 뛰고, 그 복사의
        마스크 ``-0x181`` 이 smali:29846). 이 라이브러리가 흉내내는
        ``ReservationType.DEFAULT`` 는 ``:cond_a``(29618)로 떨어져
        :meth:`next_page` 쪽 커서 분기를 탑니다. 즉 이 메서드는 앱의 기본
        화면 동작이 아니라, 앱이 다른 화면에서 쓰는 우회로를 빌려 온
        것입니다 — 그래서 이름도 ``next_page`` 와 섞이지 않게 지었습니다.
        """
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
    """환승 여정 하나 — 함께 예약되는 두 구간.

    환승 검색 응답은 구간을 중첩해 주지 않습니다. 직통과 똑같은 평평한
    ``trn_infos.trn_info`` 목록을 주고, **이 패키지가** 그것을 **위치로**
    짝짓습니다 — 0/1 행이 한 여정, 2/3 행이 다음 여정이고, 짝이 안 맞고 남는
    마지막 행은 버립니다. 이 위치 짝짓기는 이 패키지의 정책이지 앱의 동작이
    아닙니다. 아래에 둘을 갈라 적습니다.

    **앱이 하는 것 — 키 그룹핑.** 7.0.6 이 하는 것은 위치가 아니라 키 기준
    그룹핑입니다:
    ``TrainScheduleViewModel.smali`` 의 ``responseTrainSchedule``
    (선언 ``:34670``, 이 구간 전체가 그 메서드 안 — 사이에 ``.end method`` 가
    없습니다)이 ``:36958-36960`` 에서 ``LinkedHashMap`` 을 만들고, ``:37003``
    에서 행마다 ``TrainScheduleOutTrainInfo.getHTrnSeq()`` 를 꺼내 그 맵의 키로
    씁니다. ``:37017`` 에서 그 키의 값이 없으면 ``ArrayList`` 를 만들어 넣고
    (``:37019-37029``), 있으면 그 리스트에 행을 더합니다(``:37032-37040``) —
    같은 ``h_trn_seq`` 끼리 묶는 ``getOrPut`` 모양입니다. 맵/리스트 메서드
    이름은 ``AppSuitLinker1.djsflxlftm1`` 리플렉션 뒤라 호출 모양으로 읽은
    것이고, 재구성 자체도 스몰리만으로 한 것입니다.

    **이 패키지가 하는 것 — 위치 짝짓기.** 앱의 키를 그대로 쓰지 못하는 이유는
    ``h_trn_seq`` 와 이 패키지가 읽는
    ``h_chg_trn_seq``(:attr:`TrainSummary.change_train_sequence`)가 같은 DTO 의
    **서로 다른 두 원소**이기 때문입니다 —
    ``network/model/TrainScheduleOutTrainInfo.java:1464`` 의
    ``@SerialName("h_trn_seq")`` 와 ``:1112`` 의
    ``@SerialName("h_chg_trn_seq")``. 두 값이 실제로 일치하는지는 확인하지
    못했습니다. 위치 짝짓기를 그대로 둔 이유와 한계는
    :func:`pair_transfer_itineraries` 의 docstring 에 있습니다.

    ``h_chg_trn_seq`` 는 서버가 적어 보낸 같은 위치값입니다(1구간 ``"1"``,
    2구간 ``"2"``). 이 클래스는 위치로 짝짓고, 서버가 그 표시를 채워
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

        ``None`` 은 파싱 실패가 아니라 진짜 답입니다 — 한 역에 내려 다른 역에서
        타는 여정이 실제로 옵니다. **"앱도 두 이름을 각각 찍고 같을 때만 하나로
        합친다"는 서술의 뒷절반(합치기 규칙)은 7.0.6 에서 확인하지 못했습니다 —
        미출처.** 7.0.6 에서 볼 수 있는 것은 앞절반뿐입니다: 여정 화면이 구간마다
        ``JourneyStationRow(hDptRsStnNm, hArvRsStnNm)`` 으로 출발·도착 이름을 따로
        그립니다(예: ``com/korail/talk/ui/component/atomic/DialogsKt.java:170668``,
        ``:170678``). 환승역 이름을 하나로 합치는 자리는 찾지 못했으므로, 아래
        규칙은 이 패키지의 결정입니다. 그 경우가 중요하면
        :attr:`first` 의 도착역과 :attr:`second` 의 출발역을 직접 읽으면
        됩니다.
        """
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
    """평평한 환승 결과 목록을 여정 단위로 묶습니다.

    ``i % 2 == 1`` 일 때만 목록에 넣습니다 — 짝이 안 맞고 남는 마지막 행은
    예약 가능한 반쪽으로 보여 주지 않고 버립니다.

    서버가 ``h_chg_trn_seq`` 를 채워 보냈는데 그 값이 ``"1"``, ``"2"`` 순서가
    아니면 :class:`~korail_mobile_api.errors.KorailProtocolError` 를 올립니다.
    어긋난 목록을 그냥 두면 한 여정이 아닌 두 행이
    :meth:`~korail_mobile_api.client.KorailClient.reserve_transfer` 로
    넘어갑니다.

    표시가 아예 없는 응답도 받아들여 행의 위치로 짝짓습니다. **이 홀짝-위치
    방식은 이 패키지의 정책이고, 앱이 그렇게 한다는 근거는 없습니다.**

    앱이 하는 것은 :class:`TransferItinerary` 의 docstring 에 적은 대로 키
    그룹핑입니다 — ``TrainScheduleViewModel.smali`` 의 ``responseTrainSchedule``
    (선언 ``:34670``)이 ``:36958-36960`` 의 ``LinkedHashMap`` 에 ``:37003`` 의
    ``getHTrnSeq()`` 를 키로 행을 모읍니다(``:37017-37040``). 곁가지로, 7.0.6 은
    ``h_chg_trn_dv_cd``(:attr:`TrainSummary.change_train_division_code`)를
    DTO 선언 밖에서 아예 읽지 않는 것으로 보입니다(전수 grep 확인).

    그 키를 여기서 그대로 쓰지 않는 이유는 두 가지입니다. 하나, 이 재구성은
    jadx 디컴파일이 실패해 스몰리만으로 한 것이라 완전히 확정하지 못했습니다.
    둘, ``h_trn_seq`` 는 이 패키지가 읽는
    ``h_chg_trn_seq``(:attr:`TrainSummary.change_train_sequence`)와 DTO 상
    별개 원소라 값이 같은지 확인하지 못했습니다. 반면 이 함수의 현재 홀짝
    짝짓기 + ``h_chg_trn_seq`` 검증은 2026-09-21 실서버(강릉→목포, 직통 없는
    구간)로 직접 확인됐습니다 — 그러니 정적분석만으로 바꾸지 않았습니다.
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
    것입니다. 평평한 목록과 묶은 목록을 앱도 둘 다 들고 있다는 것까지는 7.0.6 에서
    확인됩니다 — ``TrainScheduleViewModel.smali`` 의 ``responseTrainSchedule``
    (선언 ``:34670``)이 ``:35740-35786`` 에서 ``trn_infos.trn_info`` 를 그대로 훑어
    ``ArrayList`` 를 만들고, ``:37003-37050`` 에서 같은 행들을 ``h_trn_seq`` 키로
    묶은 맵을 따로 만듭니다. 묶는 방식은 ``i * 2`` 인덱싱이 아니라 키
    그룹핑입니다.
    """

    itineraries: list[TransferItinerary]
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    metadata: TrainSearchMetadata = field(default_factory=TrainSearchMetadata)

    def next_page(self) -> TrainSearchContinuation | None:
        """다음 페이지 커서. 다음이 없으면 ``None``.

        ``h_next_pg_flg == "Y"`` 게이트는 직통과 같지만 커서가 다릅니다. 환승
        페이지에는 필드가 둘 더 오고, 앱은 그것으로 ``qryStTrnNo`` 를
        ``h_prcd_trn_no_next`` 로, ``qryStTrnNo2`` 를 ``h_ectb_trn_no_next`` 로
        채웁니다 — 7.0.6 근거는 ``TrainScheduleViewModel.smali:36806-36845``
        (환승형 ``Triple(getHQryStNoNext(), getHPrcdTrnNoNext(),
        getHEctbTrnNoNext())``)과 그것을 ``qryStNo``/``qryStTrnNo``/``qryStTrnNo2``
        로 옮기는 ``TrainScheduleViewModel.java:7340`` 입니다.

        **아래의 "둘 다 비어 있지 않을 때만"은 앱의 조건이 아니라 이 패키지의
        조건입니다.** 7.0.6 이 환승형과 직통형 커서를 고르는 기준은 두 값의 공백
        여부가 아니라 응답의 ``strJobId`` 를 보호된 리터럴과 견주는 것입니다
        (``TrainScheduleViewModel.smali:35654-35698``). 여기서 공백 검사를 쓰는 것은
        실서버에서 검증된 동작이라 그대로 두었을 뿐이며, 두 규칙이 갈리는 경우
        (환승 응답인데 두 커서 절반이 빈 경우)의 실제 동작은 확인하지 않았습니다.
        하나라도 없으면 직통과 같은 커서를 그대로 씁니다.
        """
        metadata = self.metadata
        preceding = metadata.next_preceding_train_no or ""
        connecting = metadata.next_connecting_train_no or ""
        transfer_cursor = bool(preceding.strip()) and bool(connecting.strip())
        return _train_search_continuation(
            metadata,
            query_train_no=preceding if transfer_cursor else metadata.next_train_no or "",
            query_train_no2=connecting if transfer_cursor else "",
        )
