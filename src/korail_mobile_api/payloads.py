# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""열차·좌석·공통 조회 요청 빌더. dict·순서 있는 필드 목록만 만들고 전송하지 않습니다. @FieldMap 선언만으로 개별 키나 순서가
증명되지는 않으며, 이를 고정하던 테스트가 삭제돼 지금은 각 빌더의 코드가 계약입니다. 나머지 조회는 read_payloads, 상태 변경은
mutation_payloads 에 있습니다."""
import time
from collections.abc import Sequence

from ._payload_helpers import _device_version, _is_ascii_digits
from .config import KorailConfig
from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_TRANSFER_ITINERARY_CODE,
)
from .errors import KorailProtocolError
from .models import TrainSearchContinuation, TrainSearchQuery, TrainSummary


def _required_ascii_digits(
    value: object,
    name: str,
    *,
    lengths: frozenset[int],
) -> str:
    if not _is_ascii_digits(value, lengths):
        expected = ", ".join(str(length) for length in sorted(lengths))
        raise KorailProtocolError(
            f"{name} must contain {expected} ASCII digit(s)"
        )
    return value


def validate_seat_inventory_inputs(
    train: TrainSummary,
    passenger_count: int,
    *,
    car_no: int | None = None,
) -> None:
    """TrainSummary 타입, 인원 1~9, 지정 호차의 양의 정수 여부를 검사합니다. 행의 열차·역·날짜 식별자는 재검사하지 않으므로 임의 생성한 행의 유효성은 보장하지 않습니다."""
    if not isinstance(train, TrainSummary):
        raise KorailProtocolError("train must be a TrainSummary")
    if type(passenger_count) is not int or not 1 <= passenger_count <= 9:
        raise KorailProtocolError("passenger_count must be an integer from 1 through 9")
    if car_no is not None and (type(car_no) is not int or car_no < 1):
        raise KorailProtocolError("car_no must be a positive integer")
    # 좌석 속성과 상품번호는 선택된 예약 구간에서 옵니다(TrainSeatMapViewModel.java:2527,2546,2573-2577). 선언:
    # TrainResearchIn.java:39,43,68. 후행 속성의 앱 기본 리터럴은 보호돼 있습니다.
    if train.seat_attribute_code:
        _required_ascii_digits(
            train.seat_attribute_code,
            "seat_attribute_code",
            lengths=frozenset({3}),
        )
    if train.goods_no:
        _wire_goods_no(train.goods_no)


def _wire_goods_no(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.isascii()
        or any(character <= " " or character == "\x7f" for character in value)
    ):
        raise KorailProtocolError(
            "goods_no must be a printable ASCII value"
        )
    return value


def _validated_room_class_code(value: str) -> str:
    # 객실은 사용자 선택값(TrainScheduleListContentRowItemPriceKt.java:600,621)이며 좌석 조회도 구간에서
    # 복사합니다(TrainSeatMapViewModel.java:2542,2546). PsrmType.java:19-22 의 GENERAL/SPECIAL 값은 보호됨. 이 코드의 1/2 배정은
    # 라이브 기록에 의존합니다.
    if value not in {"1", "2"}:
        raise KorailProtocolError(
            'room_class_code must be "1" (general) or "2" (first class)'
        )
    return value


def build_seat_car_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    passenger_count: int,
    room_class_code: str = "1",
    seat_attribute_code: str | None = None,
    menu_id: str = "11",
) -> dict[str, str]:
    """호차 조회(NetworkApi.java:771-773). 열차번호는 5자리 영 채움이며 좌석 속성·상품번호가 없으면 생략합니다. Sid 는 DTO 에
    없습니다(TrainResearchIn.java:68).

    빌더 dict 의 빈 문자열은 http._drop_empty 단계에서 빠집니다. 앱도 DTO 를 직렬화한 뒤
    평탄화합니다(NetworkService.java:14524-14528,15335-15343). 보호된 explicitNulls 설정은 확정할 수 없으므로 빈 문자열 처리와 null 처리를
    혼동하지 마십시오(NetworkServiceKt.java:28). menu_id 의 기본값 밖 코드는 보호돼 있으므로 맥락을 아는 호출자만 재정의하십시오."""
    validate_seat_inventory_inputs(train, passenger_count)
    # 명시한 코드도 행에서 읽은 코드와 같은 검증을 적용합니다.
    if seat_attribute_code:
        _required_ascii_digits(
            seat_attribute_code, "seat_attribute_code", lengths=frozenset({3})
        )
    seat_attribute = seat_attribute_code or train.seat_attribute_code
    return {
        **_device_version(config),
        "Key": config.key,
        "txtMenuId": menu_id,
        "txtPsrmClCd": _validated_room_class_code(room_class_code),
        "txtRunDt": train.run_date or "",
        "txtDptDt": train.departure_date or "",
        "txtDptTm": train.departure_time or "",
        "txtTrnClsfCd": train.train_class_code or "",
        "txtTrnNo": train.train_no.zfill(5),
        "txtDptRsStnCd": train.departure_station_code or "",
        "txtArvRsStnCd": train.arrival_station_code or "",
        "txtDptStnRunOrdr": train.departure_run_order or "",
        "txtArvStnRunOrdr": train.arrival_run_order or "",
        "txtTrnGpCd": train.train_group_code or "",
        "txtTotPsgCnt": str(passenger_count),
        # 상품이 아닌 좌석속성은 열차별 값입니다(TrainResearchIn.java:43; TrainSeatMapViewModel.java:2546,2577). 앱 평탄화기는 빈
        # primitive 를 생략합니다 (NetworkService.java:15335-15343). 속성이 없으면 임의 기본값을 넣지 않습니다.
        **({"txtSeatAttCd": seat_attribute} if seat_attribute else {}),
        # 상품번호는 예약 입력에서 옵니다(TrainResearchIn.java:39; TrainSeatMapViewModel.java:2527). 값이 없으면 임의 기본값을 넣지 않습니다.
        **({"txtGdNo": train.goods_no} if train.goods_no else {}),
    }


def build_seat_inventory_form(
    config: KorailConfig,
    train: TrainSummary,
    car_no: int,
    *,
    passenger_count: int,
    room_class_code: str = "1",
    seat_attribute_code: str | None = None,
) -> dict[str, str]:
    """좌석 재고(NetworkApi.java:739-741). 호차 키는 txt 접두사 없는 srcarNo 입니다. seatAttCd·gdNo 는 없으면 생략합니다. 앱 DTO 의 누락 기본값도
    null 입니다 (TResidualSeatsResearchIn.java:107-110,127-130). ctlDvCd 는 빈 문자열이며 전송 때 제거됩니다. Sid 는 싣지
    않습니다(TResidualSeatsResearchIn.java:65). 앱 평탄화 호출: NetworkService.java:14800-14803,15335-15343. explicitNulls 의
    보호 리터럴 때문에 앱 null 생략까지 확정한 것은 아닙니다(NetworkServiceKt.java:28).

    isArrow 는 좌석도 기본 경로의 false 입니다. 기본 인자 마스크 0x2000(TrainSeatMapViewModel.smali:4232-4238)과 DTO 기본값
    (TResidualSeatsResearchIn.java:159-160)이 근거이며, encodeDefaults 가 보호되어 앱이 false 를 명시하는지 생략하는지는 미확정입니다. 호차 목록
    조회에서 좌석 속성을 재정의했다면 같은 seat_attribute_code 를 넘기십시오. 앱도 직전 TrainResearchIn 값을 이어
    씁니다(TrainSeatMapViewModel.smali:4116)."""
    validate_seat_inventory_inputs(
        train,
        passenger_count,
        car_no=car_no,
    )
    seat_attribute = (
        train.seat_attribute_code
        if seat_attribute_code is None
        else seat_attribute_code
    )
    return {
        **_device_version(config),
        "Key": config.key,
        "trnClsfCd": train.train_class_code or "",
        "trnGpCd": train.train_group_code or "",
        "runDt": train.run_date or "",
        "trnNo": train.train_no.zfill(5),
        "srcarNo": str(car_no),
        "psrmClCd": _validated_room_class_code(room_class_code),
        "dptRsStnCd": train.departure_station_code or "",
        "arvRsStnCd": train.arrival_station_code or "",
        # 속성이 없으면 기본값 015 를 만들지 않습니다. FieldMap 경로(NetworkApi.java:739-741)는 DTO 를 빈 primitive 제외 후
        # 평탄화합니다(TResidualSeatsResearchIn.java:39; NetworkService.java:14800-14803,15335-15343).
        **({"seatAttCd": seat_attribute} if seat_attribute else {}),
        "dptStnRunOrdr": train.departure_run_order or "",
        "arvStnRunOrdr": train.arrival_run_order or "",
        "totPsgCnt": str(passenger_count),
        # 상품번호가 없으면 라이브러리는 해당 필드를 생략합니다. 개별 @Field 의 null 규칙과 구분합니다.
        **({"gdNo": train.goods_no} if train.goods_no else {}),
        "isArrow": "false",
        "ctlDvCd": "",
    }


def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
    """캐시 요청의 timeStamp 쿼리. timestamp_ms 를 생략하면 현재 밀리초 epoch 이며, 제공한 값은 검증하지 않습니다."""
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}


def build_train_search_form(
    config: KorailConfig,
    query: TrainSearchQuery,
    *,
    departure_name: str,
    arrival_name: str,
    member_card_no: str | None = None,
    continuation: TrainSearchContinuation | None = None,
    transfer: bool = False,
    menu_id: str = "11",
) -> dict[str, str]:
    """열차 한 페이지의 폼. 첫 페이지는 커서 4개를 생략하고 다음 페이지는 continuation 의 3개 값만 싣습니다. pgPrCnt 는 보내지
    않습니다(TrainScheduleIn.java:641-650, TrainScheduleViewModel.java:3212,7340). qryDvCd 는 커서와 별개로 항상 포함합니다.

    transfer 는 radJobId 를 바꾸며(TrainScheduleViewModel.java:3136,3212), 명시한 환승역· 후속 열차군은 목록 필드로 추가합니다. Sid 는 DTO 에
    없습니다(TrainScheduleIn.java:95). menu_id 기본값 밖의 보호 코드는 build_seat_car_form 의 경고를 따릅니다."""
    if continuation is not None and not isinstance(
        continuation, TrainSearchContinuation
    ):
        raise KorailProtocolError(
            "KORAIL train search continuation must be a "
            "TrainSearchContinuation"
        )
    counts = (
        query.passengers,
        query.child_passengers,
        query.senior_passengers,
        query.high_disability_passengers,
        query.low_disability_passengers,
    )
    if any(type(count) is not int or count < 0 for count in counts) or not sum(counts):
        raise KorailProtocolError("passenger counts must be non-negative integers with a nonzero total")
    if not isinstance(query.seat_attribute_code, str) or not query.seat_attribute_code:
        raise KorailProtocolError("seat_attribute_code must be a non-empty string")
    form = {
        **_device_version(config),
        "Key": config.key,
        "txtMenuId": menu_id,
        "radJobId": (
            KORAIL_TRANSFER_ITINERARY_CODE
            if transfer
            else KORAIL_DIRECT_ITINERARY_CODE
        ),
        "selGoTrain": query.train_group_code,
        "txtTrnGpCd": query.train_group_code,
        "txtGoStart": departure_name,
        "txtGoEnd": arrival_name,
        "txtGoAbrdDt": query.departure_date,
        "txtGoHour": query.departure_time,
        "txtPsgFlg_1": str(query.passengers),
        "txtPsgFlg_2": str(query.child_passengers),
        "txtPsgFlg_3": str(query.senior_passengers),
        "txtPsgFlg_4": str(query.high_disability_passengers),
        "txtPsgFlg_5": str(query.low_disability_passengers),
        "txtSeatAttCd_2": "000",
        "txtSeatAttCd_3": "000",
        "txtSeatAttCd_4": query.seat_attribute_code,
        # 앱 두 선택 조건은 isSrt() || isSuseoTogether() 로 같습니다 (TrainScheduleViewModel.java:3137,3147;
        # TrainScheduleIn.java:33). 이 사실만으로 두 보호 리터럴이 Y/N 이거나 SRT 체크박스만의 조건이라고 할 수는 없습니다.
        "ebizCrossCheck": "Y" if query.include_srt else "N",
        "srtCheckYn": "Y" if query.include_srt else "N",
        "rtYn": "N",
        "adjStnScdlOfrFlg": "N",
    }
    if member_card_no:
        form["mbCrdNo"] = member_card_no
    # 페이징 필드 위치는 DTO 선언 순서에 따릅니다(TrainScheduleIn.java:27,33). 이 진입점은 승차권 변경용 tkPsrmClCd/tkRcvdAmt 를 채우지 않습니다. 전송
    # 생략은 @Field 바인딩이 아니라 직렬화·평탄화 과정입니다.
    if not isinstance(query.query_division_code, str) or not query.query_division_code:
        raise KorailProtocolError("query_division_code must be a non-empty string")
    if not isinstance(query.connection_station_codes, tuple) or any(
        not isinstance(code, str) or not code for code in query.connection_station_codes
    ):
        raise KorailProtocolError("connection_station_codes must be a tuple of non-empty strings")
    if query.connection_train_group_code is not None and (
        not isinstance(query.connection_train_group_code, str)
        or not query.connection_train_group_code
    ):
        raise KorailProtocolError("connection_train_group_code must be a non-empty string or None")
    if not transfer and (
        query.connection_station_codes or query.connection_train_group_code is not None
    ):
        raise KorailProtocolError("connection filters require transfer=True")
    form["qryDvCd"] = query.query_division_code
    # 신규 빌드의 커서 4개는 null(TrainScheduleViewModel.java:3212). 다음 페이지의 3튜플만 복사하며 pgPrCnt 는 추가하지
    # 않습니다(TrainScheduleViewModel.java:7340).
    if continuation is not None:
        form["qryStNo"] = continuation.query_station_no
        form["qryStTrnNo"] = continuation.query_train_no
        # continuation 의 결과를 재판정하지 않고 전달합니다. 일반 결과는 세 번째 커서가 빈 값, 환승 결과는 h_ectb_trn_no_next 를 사용할 수
        # 있습니다(TrainScheduleOut.java:67). 앱 responseTrainSchedule 는 jadx 복원 실패로 이 자료만으로 분기 전체를 확인할 수 없습니다. 기존
        # smali 근거 위치: TrainScheduleViewModel.smali:35654-35698,36812-36851. strJobId 비교의 보호 리터럴은 미확인; 두 커서 존재
        # 여부 조건은 라이브러리 정책입니다.
        form["qryStTrnNo2"] = continuation.query_train_no2
    # 배열에 1기반 접미사를 붙입니다. 선택역·후보 목록은 호출자가 주며 보호된 선택값은 추정하지 않습니다.
    if query.connection_station_codes:
        form["chtnCnt"] = str(len(query.connection_station_codes))
        for index, code in enumerate(query.connection_station_codes, 1):
            form[f"chtnRsStnCd{index}"] = code
    if query.connection_train_group_code is not None:
        form["trnGpCnt"] = "1"
        form["trnGpCd1"] = query.connection_train_group_code
    return form


def build_train_schedule_special_form(
    config: KorailConfig,
    query: TrainSearchQuery,
    *,
    departure_name: str,
    arrival_name: str,
    member_card_no: str | None = None,
    continuation: TrainSearchContinuation | None = None,
    transfer: bool = False,
) -> dict[str, str]:
    """ScheduleViewSpecial 의 FieldMap. 기본 조회 키를 공유하며 Key 를 포함하고 Sid 는 제외합니다. 보호된 qryDvCd 값은 재구성하지 않고 query 에서 받습니다."""
    form = build_train_search_form(
        config,
        query,
        departure_name=departure_name,
        arrival_name=arrival_name,
        member_card_no=member_card_no,
        continuation=continuation,
        transfer=transfer,
    )
    # continuation 이 없으면 커서 키를 만들지 않습니다. pgPrCnt 도 이 빌더에서 보내지 않습니다.
    device = form.pop("Device")
    version = form.pop("Version")
    # 앱 평탄화기처럼 빈 primitive 를 생략합니다(NetworkService.java:15335-15343).
    form = {key: value for key, value in form.items() if value}
    return {
        "Device": device,
        "Version": version,
        "Key": config.key,
        **form,
    }


def build_train_schedule_form(
    config: KorailConfig,
    run_date: str,
    train_no: str,
) -> dict[str, str]:
    """정차역·지연 조회. 열차번호는 5자리 영 채움, Key 는 싣지 않습니다. 설정된 lang 은 공통 필드에 포함합니다(ActualTrainScheduleIn.java:53,
    CommonIn.java:40,432,467-474)."""
    return {
        **_device_version(config),
        "runDt": run_date,
        "trnNo": train_no.zfill(5),
    }


def build_common_code_form(
    config: KorailConfig,
    code: str | Sequence[str],
) -> dict[str, object]:
    """공통코드를 같은 이름의 반복 키로 전송할 폼을 만듭니다. 라우트 선언: NetworkApi.java:317,321. 기기 크기·SDK 정수는 설정을 사용합니다
    (CommonCodeIn.java:31-34,55). 로그인 암호화 파라미터 조회에도 사용합니다."""
    form: dict[str, object] = {
        **_device_version(config),
        "Key": config.key,
        "code": [code] if isinstance(code, str) else list(code),
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
    }
    form["OSVersion"] = config.android_sdk_int
    return form


TICKET_LIST_MODE_ACTIVE = "1"
TICKET_LIST_MODE_HISTORY = "2"


def build_ticket_list_form(
    config: KorailConfig,
    page_no: int,
    *,
    mode: str = TICKET_LIST_MODE_ACTIVE,
    boarding_date_from: str = "",
    boarding_date_to: str = "",
) -> dict[str, str]:
    """txtIndex 는 페이지가 아닌 목록 종류입니다(MyTicketListIn.java:62). mode 는 1/2 만 허용하며 h_page_no 는 최소 1 입니다. 앱 호출 리터럴은 보호돼
    있습니다 (MyTicketBaseViewModel.java:1029, LoginViewModel.java:1083,
    AppViewModel$executeTicketListForAutoLogin$result$1.java:67). 2026-09-22 관측: 1 은 빈 현재 목록 WRT300005, 2 는 구매이력
    128건. 날짜 범위는 그대로 전달하며 잘못된 범위는 WRT100101 을 관측했습니다. 이 표본으로 모든 계정·앱의 페이지 값을 단정하지 않습니다."""
    if mode not in {TICKET_LIST_MODE_ACTIVE, TICKET_LIST_MODE_HISTORY}:
        raise KorailProtocolError(
            'ticket list mode must be "1" (active) or "2" (history)'
        )
    return {
        "txtDeviceId": config.advertising_id,
        "txtIndex": mode,
        "h_page_no": str(max(1, page_no)),
        "h_abrd_dt_from": boarding_date_from,
        "h_abrd_dt_to": boarding_date_to,
        "hiduserYn": "Y",
    }


def build_maas_menu_form(config: KorailConfig) -> dict[str, str]:
    """MaaS 메뉴. include_common=False 이므로 Key 를 이 빌더에서 넣습니다. 앱 DTO 는 CommonIn 기본 생성자를 사용합니다(GdMenuLtIn.java:59-61).
    공통 필드 인코딩: CommonIn.java:448-465. 보호된 기본값의 실제 포함 여부와는 구분합니다."""
    return {
        **_device_version(config),
        "Key": config.key,
        "timeStamp": str(int(time.time() * 1000)),
    }


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    """``EbizMaasStationList.do`` 의 역 목록 조회 폼을 만듭니다.

    부가서비스 코드(``addSrvDvCd``) 하나뿐이고 공통 필드도 붙지 않습니다. 값은
    :meth:`~korail_mobile_api.client.KorailClient.get_maas_menu_list` 결과의 항목에서 옵니다. 비어 있으면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다."""
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise KorailProtocolError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}
