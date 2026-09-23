# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""읽기 라우트 가운데 기본 조회들의 요청 폼 빌더.

열차 조회(``seatMovie.ScheduleView``), 좌석 조회, 역 정보, 공통코드, 승차권 목록,
MaaS 메뉴의 폼을 만듭니다. 나머지 읽기 라우트는
:mod:`korail_mobile_api.read_payloads`, 상태 변경은
:mod:`korail_mobile_api.mutation_payloads` 에 있습니다.

여기 함수들은 dict 를 돌려줄 뿐 아무것도 보내지 않습니다. 필드 이름과 순서는
APK 의 Retrofit 선언에서 나왔습니다. 그것을 고정하던 테스트는 삭제됐고, 지금
계약을 말하는 것은 각 빌더의 코드뿐입니다 — :mod:`korail_mobile_api.safety` 는
라우트와 변경 폼의 값 모양만 보고 필드 이름·순서는 강제하지 않습니다.
"""
import time
from collections.abc import Sequence
from typing import TypeGuard

from .config import KorailConfig
from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_TRANSFER_ITINERARY_CODE,
)
from .errors import KorailProtocolError
from .models import TrainSearchContinuation, TrainSearchQuery, TrainSummary


def _device_version(config: KorailConfig) -> dict[str, str]:
    """이 모듈의 읽기 폼이 공통으로 시작하는 ``Device``/``Version``(+ ``lang``).

    ``lang`` 이 여기 있는 이유: 이 헬퍼를 쓰는 폼들은
    :meth:`~korail_mobile_api.http.KorailHttpClient.post_form` 을
    ``include_common=False`` 로 부르므로 HTTP 계층의 공통 필드 주입을 받지
    않습니다. 그래서 ``KorailConfig(lang=...)`` 을 설정해도 열차 검색·호차
    조회·좌석 조회에는 실리지 않았습니다 — 같은 종류의 누락을 변경 폼에서
    먼저 고쳤는데(``mutation_payloads._common_fields``) 읽기 쪽이 남아
    있었습니다.

    세 라우트의 입력 DTO 는 모두 ``@SerialName(Constants.LANG)`` 을 선언합니다
    (``TrainScheduleIn``/``TrainResearchIn``/``TResidualSeatsResearchIn``).
    기본값 ``None`` 이면 예전과 똑같이 아무것도 싣지 않으므로, 달라지는 것은
    실제 값을 넘긴 호출자뿐입니다.
    """
    fields = {"Device": config.device, "Version": config.version}
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


def _is_ascii_digits(value: object, lengths: frozenset[int]) -> TypeGuard[str]:
    """``value`` 가 ``lengths`` 중 한 길이의 ASCII 숫자 문자열인지.

    ``str.isdigit`` 은 전각 숫자도 받으므로 쓰지 않습니다. read_payloads 도 이것을
    씁니다; 거절할 때의 예외와 문구는 각 모듈이 정합니다.
    """
    return (
        isinstance(value, str)
        and len(value) in lengths
        and all("0" <= character <= "9" for character in value)
    )


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
    """좌석 조회에 쓸 열차 행과 인원이 전선에 낼 만한지 검사합니다.

    ``train`` 은 :class:`TrainSummary` 여야 합니다. 그 행의 열차번호·역코드·날짜
    등 식별 필드는 여기서 다시 검사하지 않습니다 — 이 값들은 조회 응답을 파싱해서
    채운 행에서만 오고, 호출자가 손으로 지어낸 값을 넣는 오용은 이 함수의 방어
    범위 밖입니다.

    ``passenger_count`` 는 1~9 의 정수이고, ``car_no`` 를 주면 양의 정수여야
    합니다. :func:`build_seat_car_form` 과 :func:`build_seat_inventory_form` 이
    폼을 만들기 전에 부릅니다.
    """
    if not isinstance(train, TrainSummary):
        raise KorailProtocolError("train must be a TrainSummary")
    if type(passenger_count) is not int or not 1 <= passenger_count <= 9:
        raise ValueError("passenger_count must be an integer from 1 through 9")
    if car_no is not None and (type(car_no) is not int or car_no < 1):
        raise ValueError("car_no must be a positive integer")
    # txtSeatAttCd/txtGdNo are carried per selected train, not pinned: in
    # 7.0.6 the seat-map view model fills TrainResearchIn from the reservation
    # input it was handed -- txtGdNo from ticketReservationIn.getTxtGdNo()
    # (TrainSeatMapViewModel.java:2527) and the seat attribute from the leg
    # (:2546 preceding; :2573-2577 trailing, which falls back to an
    # AlienGuard-protected literal when getTrailingTxtSeatAttCd4() is null, so
    # the substituted plaintext is not readable). Both are declared on the
    # request DTO as non-null Strings (TrainResearchIn.java:39 txtGdNo, :43
    # txtSeatAttCd; @SerialName list at :68). The old citation x4/b.java:19,23
    # is a 6.5.0 leftover -- no such path exists in 7.0.6. Validate the row's
    # own values when present so the seat-map builders can forward a
    # dynamic-but-well-formed value.
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
    # psrmClCd / txtPsrmClCd is the user-selected cabin class, not a constant.
    # In 7.0.6: the schedule row's price UI picks PsrmType.GENERAL or
    # PsrmType.SPECIAL from the tap the user makes on that row
    # (TrainScheduleListContentRowItemPriceKt.java:600,621), the chosen
    # PsrmType.psrmClCd is what reaches a journey input
    # (AirportBusScheduleViewModel.java:167 ->
    # toTicketReservationInput(PsrmType.GENERAL.getPsrmClCd())), and the
    # seat-map search copies it off the leg into TrainResearchIn.txtPsrmClCd
    # (TrainSeatMapViewModel.java:2542,2546; DTO field at
    # TrainResearchIn.java:41).
    #
    # The two-member domain is confirmed -- PsrmType declares exactly GENERAL
    # (PsrmType.java:19) and SPECIAL (:20) -- but their psrmClCd literals
    # (field at :22) are AlienGuard-protected, so 7.0.6 does NOT let us read
    # that GENERAL is "1" and SPECIAL is "2"; that mapping rests on live
    # traffic, not on the APK. The old citations c5/c.java:90,
    # x4/b.java:18, U4/a.java:87 and K4/o.java are all 6.5.0 leftovers with no
    # 7.0.6 counterpart. Restrict to the two-value domain and let general
    # ("1") stay the default.
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
    sid: str,
    room_class_code: str = "1",
    seat_attribute_code: str | None = None,
    menu_id: str = "11",
) -> dict[str, str]:
    """``research.TrainResearch`` 의 호차 목록 조회 폼을 만듭니다.

    라우트 선언은 ``NetworkApi.java:771-773``
    (``@FormUrlEncoded`` + ``postTrainResearch(@FieldMap Map<String, String>)``)
    입니다.

    ``txtTrnNo`` 는 다섯 자리로 0 을 채웁니다. ``txtSeatAttCd`` 는 열차 행이 좌석
    속성 코드를 가지고 있을 때만 실리고, 일반석 ``"015"`` 로 대신 채우지 않습니다.
    ``txtGdNo`` 도 값이 없으면 빠집니다.

    **그 이유로 적혀 있던 "Retrofit 이 개별 ``@Field`` 를 떨어뜨린다
    (``NetworkApi.java`` 의 ``getCarList``)"는 7.0.6 과 다릅니다.** 7.0.6 에는
    ``getCarList`` 라는 선언도, 이 라우트의 매개변수별 ``@Field`` 바인딩도 없고
    (위의 ``@FieldMap`` 하나뿐), 요청 DTO 의 필드는 모두 널이 될 수 없는
    ``String`` 입니다(``TrainResearchIn.java:32-47``). 같은 결과가 나오는 자리는
    Retrofit 이 아니라 DTO→맵 평탄화입니다: 앱은
    ``kJson.encodeToJsonElement(TrainResearchIn.serializer(), …)`` 로 만든
    JSON 을 ``NetworkService.STLibw``(``NetworkService.java:15304``)에 넘기는데,
    이 함수는 ``JsonPrimitive`` 의 내용 **길이가 0 보다 클 때만** 맵에 넣습니다
    (``:15335-15343``). 인코딩 단계에서 ``explicitNulls = false``
    (``NetworkServiceKt.java:28``)가 널을 이미 지우므로, 널이든 빈 문자열이든
    폼에서 사라집니다 — 이 라우트의 실제 호출 경로는
    ``NetworkService.java:14524,14528`` 입니다.

    **이 함수가 ``""`` 로 채우는 다른 키(``txtRunDt``·``txtDptDt`` 등)도
    전선에는 나가지 않습니다.** 빌더가 *돌려주는* dict 와 실제로 *보내지는* 폼을
    구분해야 합니다: 반환 dict 에는 키가 ``""`` 로 남지만,
    :meth:`~korail_mobile_api.http.KorailHttpClient.post_form` 이 보내기 직전에
    빈 문자열 항목을 걸러 냅니다 -- ``http.py:226-239`` 의
    ``_is_empty_string``/``_drop_empty`` 이고, 매핑 폼에는 ``http.py:453``,
    순서 있는 폼에는 ``http.py:444-446`` 에서 적용됩니다. 그러므로 전선 모양은
    이미 7.0.6 평탄화기와 같습니다. 예전에 여기 적혀 있던 "7.0.6 이라면 빠졌을
    값인데 우리는 그대로 보낸다"는 설명은 HTTP 계층을 보지 않고 쓴 것이라
    틀렸습니다. 빌더가 ``""`` 를 남겨 두는 것은 반환 dict 의 키 집합을 호출부와
    테스트에서 안정적으로 유지하기 위한 것일 뿐입니다.

    ``sid`` 는 받지만 쓰지 않습니다 — 7.0.6 ``TrainResearchIn.java:68`` 의
    ``@SerialName`` 20개 중 ``Sid`` 는 없으므로 이 라우트에는 애초에 실을 자리가
    없습니다(6.5.0 잔재). 매개변수를 남겨 두는 것은 클라이언트가 여전히
    ``sid=generate_sid()`` 를 키워드로 넘기기 때문일 뿐입니다 — 그 호출부를
    바꾸는 것은 이 파일의 범위 밖입니다.

    ``menu_id`` 는 기본값 ``"11"`` 만 근거가 있습니다. 7.0.6 은 예약 맥락별로
    ``ReservationMenuId`` 열거형(7개 멤버)에서 값을 고르는데, DEFAULT 이외
    나머지 6개의 복호값은 AppSuit 로 보호돼 있어 추측하지 않습니다 — 맥락을 아는
    호출자만 재정의하십시오.
    """
    validate_seat_inventory_inputs(train, passenger_count)
    # The override stands in for the row's code, so it gets the row's check.
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
        # The seat attribute rides along per train (TrainResearchIn.java:43,
        # filled off the leg at TrainSeatMapViewModel.java:2546/:2577), and an
        # absent one leaves the form empty-handed rather than defaulted: the
        # DTO-to-@FieldMap flattener keeps only non-empty primitives
        # (NetworkService.java:15335-15343). So omit the key rather than
        # substituting a general-seat "015". Old citations x4/b.java:19 and
        # "getCarList txtSeatAttCd, ResearchService:37" are 6.5.0 leftovers --
        # 7.0.6 has neither file, and this route takes one bare @FieldMap
        # (NetworkApi.java:771-773), not per-parameter @Fields.
        **({"txtSeatAttCd": seat_attribute} if seat_attribute else {}),
        # Same for txtGdNo (TrainResearchIn.java:39): 7.0.6 forwards
        # ticketReservationIn.getTxtGdNo() verbatim
        # (TrainSeatMapViewModel.java:2527) and the flattener drops it when it
        # encodes to nothing, so a standard (non-goods) search carries no
        # txtGdNo. Leave the key out here when there is none. The old
        # citations x4/b.java:23, SeatSearchRequest.txtGdNo and
        # "ResearchService getCarList txtGdNo:37 / getSeatList gdNo:59" are
        # 6.5.0 leftovers absent from 7.0.6.
        **({"txtGdNo": train.goods_no} if train.goods_no else {}),
    }


def build_seat_inventory_form(
    config: KorailConfig,
    train: TrainSummary,
    car_no: int,
    *,
    passenger_count: int,
    sid: str,
    room_class_code: str = "1",
) -> dict[str, str]:
    """``research.TResidualSeatsResearch.do`` 의 좌석표 조회 폼을 만듭니다.

    :func:`build_seat_car_form` 이 고른 호차 하나를 ``srcarNo`` 로 지목합니다.
    키 철자가 호차 목록 쪽과 다릅니다 — 이쪽은 ``txt`` 접두사가 없습니다.

    ``seatAttCd`` 와 ``gdNo`` 는 값이 없으면 빠집니다. 근거는 7.0.6 에서 다시
    유도했습니다 -- 이 라우트의 선언은 ``NetworkApi.java:739-741``
    (``@FormUrlEncoded`` +
    ``postTResidualSeatsResearch(@FieldMap Map<String, String>)``)로 매개변수별
    ``@Field`` 바인딩이 없습니다. 요청 DTO 의 두 필드는 **널이 될 수 있습니다**
    -- 합성 역직렬화 생성자가 페이로드에 없는 필드에 널을 넣습니다
    (``TResidualSeatsResearchIn.java:107-110`` ``seatAttCd``, ``:127-130``
    ``gdNo``). jadx 가 찍는 ``public final String`` 선언(``:39``/``:35``)은
    코틀린 널가능성을 지운 것이라 근거가 되지 못했습니다. 값이 빠지는 일이
    실제로 일어나는 자리는 Retrofit 이 아니라 DTO→맵 평탄화입니다:
    호출 경로(``NetworkService.java:14800,14803``)가
    ``kJson.encodeToJsonElement(TResidualSeatsResearchIn.serializer(), …)`` 를
    ``NetworkService.STLibw``(``NetworkService.java:15304``)에 넘기고, 이 함수는
    ``JsonPrimitive`` 의 내용 길이가 **0 보다 클 때만** 맵에 넣습니다
    (``:15335-15343``). 인코딩 단계의 ``explicitNulls = false``
    (``NetworkServiceKt.java:28``)가 널을 이미 지우므로 널이든 빈 문자열이든
    폼에서 사라집니다.

    **예전 인용 ``ResearchService:59`` 는 6.5.0 클래스이고 7.0.6 decompile 에
    존재하지 않습니다** -- ``.java`` 확장자가 없어 낡은 인용 탐지를 계속
    빠져나갔습니다. 위 재유도가 그 자리를 대신하므로 이 주장은 이제
    미출처가 아닙니다.

    ``isArrow`` 는 고정 ``"true"``, ``ctlDvCd`` 는 고정 빈 문자열입니다 -- 빈
    문자열인 ``ctlDvCd`` 는 :func:`build_seat_car_form` 의 ``""`` 키들과 똑같이
    ``post_form`` 단계에서 빠지므로 전선에는 나가지 않습니다.

    ``sid`` 는 받지만 쓰지 않습니다 — 7.0.6 ``TResidualSeatsResearchIn.java:65``
    의 ``@SerialName`` 19개 중 ``Sid`` 는 없으므로 이 라우트에도 실을 자리가
    없습니다(6.5.0 잔재). 매개변수를 남겨 두는 것은 클라이언트가 여전히
    ``sid=generate_sid()`` 를 키워드로 넘기기 때문일 뿐입니다.
    """
    validate_seat_inventory_inputs(
        train,
        passenger_count,
        car_no=car_no,
    )
    seat_attribute = train.seat_attribute_code
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
        # Omit seatAttCd for a row without a code instead of sending "015".
        # Re-derived in 7.0.6: this route is one bare @FieldMap
        # (NetworkApi.java:739-741), the DTO field is a non-null String
        # (TResidualSeatsResearchIn.java:39), and the DTO-to-map flattener keeps
        # only primitives whose content length is > 0
        # (NetworkService.java:15335-15343) on the call path at
        # NetworkService.java:14800,14803. The old citation "ResearchService:59"
        # is a 6.5.0 leftover with no 7.0.6 counterpart -- it carries no .java
        # extension, which is why the stale-citation sweep kept missing it.
        **({"seatAttCd": seat_attribute} if seat_attribute else {}),
        "dptStnRunOrdr": train.departure_run_order or "",
        "arvStnRunOrdr": train.arrival_run_order or "",
        "totPsgCnt": str(passenger_count),
        # Same null-@Field omission as build_seat_car_form's txtGdNo, above.
        **({"gdNo": train.goods_no} if train.goods_no else {}),
        "isArrow": "true",
        "ctlDvCd": "",
    }


def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
    """캐시 파일 요청의 ``timeStamp`` 쿼리를 만듭니다.

    ``timestamp_ms`` 를 주지 않으면 현재 밀리초 epoch 입니다. 음수나 정수가 아닌
    값은 ``ValueError`` 입니다. 캐시를 우회하려는 값이라 서버가 내용을 보지
    않습니다.
    """
    if timestamp_ms is not None and (
        type(timestamp_ms) is not int or timestamp_ms < 0
    ):
        raise ValueError("timestamp_ms must be a non-negative integer or None")
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}


def build_train_search_form(
    config: KorailConfig,
    query: TrainSearchQuery,
    *,
    departure_name: str,
    arrival_name: str,
    sid: str,
    member_card_no: str | None = None,
    continuation: TrainSearchContinuation | None = None,
    transfer: bool = False,
    menu_id: str = "11",
) -> dict[str, str]:
    """``seatMovie.ScheduleView`` 폼을 한 페이지 분량으로 만듭니다.

    ``continuation=None`` 이면 앱의 첫 페이지 요청입니다. 그다음 페이지는
    :meth:`TrainSearchResult.next_page` 가 준
    :class:`TrainSearchContinuation` 을 넘겨 요청하면 됩니다. ``qryDvCd`` 는
    환승 전용이 아니라 모든 검색에 항상 오릅니다. 반면
    ``qryStNo``/``qryStTrnNo``/``qryStTrnNo2`` 는 첫 페이지에서 아예 빠지고
    커서가 있을 때만 실립니다 — 7.0.6 ``TrainScheduleIn.write$Self`` 가 이 셋을
    ``self.<field> != null`` 일 때만 인코딩하고(``TrainScheduleIn.java:641-647``),
    첫 페이지를 만드는 유일한 빌더 ``TrainScheduleViewModel.buildTrainScheduleIn()``
    은 매 신규 빌드마다 넷 다 리터럴 ``null`` 을 넘기기 때문입니다
    (``TrainScheduleViewModel.java:3212``). ``pgPrCnt`` 는 **어느 페이지에서도**
    앱이 보내지 않습니다 — 유일한 연속 경로(``TrainScheduleViewModel.java:7340``)
    가 쓰는 3튜플 커서에는 애초에 ``pgPrCnt`` 자리가 없습니다. 이 함수도 같은
    모양을 냅니다: 첫 페이지엔 네 키를 전부 생략하고, 다음 페이지엔 커서의
    ``qryStNo``/``qryStTrnNo``/``qryStTrnNo2`` 세 값만 싣고 ``pgPrCnt`` 는 어느
    쪽도 싣지 않습니다.

    ``sid`` 는 받지만 쓰지 않습니다 — 7.0.6 ``TrainScheduleIn.java:95`` 의
    ``@SerialName`` 목록에 ``Sid`` 가 없으므로 이 라우트에도 실을 자리가
    없습니다(6.5.0 잔재). 매개변수를 남겨 두는 것은 클라이언트가 여전히
    ``sid=generate_sid()`` 를 키워드로 넘기기 때문일 뿐입니다 — 그 호출부를
    바꾸는 것은 이 파일의 범위 밖입니다.

    ``menu_id`` 는 기본값 ``"11"`` 만 근거가 있습니다 — 나머지 근거는
    :func:`build_seat_car_form` 의 같은 매개변수 설명을 보십시오.

    ``transfer=True`` 는 직통 대신 환승 여정을 묻습니다. 필터를 지정하지
    않은 기본 쿼리에서는 움직이는 필드가 ``radJobId`` 하나뿐이며
    :data:`~korail_mobile_api.KORAIL_DIRECT_ITINERARY_CODE` 에서
    :data:`~korail_mobile_api.KORAIL_TRANSFER_ITINERARY_CODE` 로 바뀝니다. 앱의
    환승 재조회도 그게 전부입니다 — 7.0.6
    ``TrainScheduleViewModel.buildTrainScheduleIn()`` 의 바로 그 자리
    (``TrainScheduleViewModel.java:3136`` 의 ``isTransfer()`` 삼항연산이
    ``:3212`` 에서 ``TrainScheduleIn`` 의 ``radJobId`` 인자로 들어감)이며,
    환승역 필터가 같이 없으면 이 필드 말고는 바뀌는 게 없습니다.

    환승역·후속 열차군을 명시하면 7.0.6 ``TrainScheduleIn`` 목록 계약대로
    ``chtnCnt``/``chtnRsStnCdN``/``trnGpCnt``/``trnGpCd1`` 을 추가합니다.
    기본 쿼리에서는 이 필드를 생략합니다.
    """
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
        raise ValueError("passenger counts must be non-negative integers with a nonzero total")
    if not isinstance(query.seat_attribute_code, str) or not query.seat_attribute_code:
        raise ValueError("seat_attribute_code must be a non-empty string")
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
        # 두 키를 같은 값으로 묶어 보냅니다. 7.0.6 에서 재유도했습니다 --
        # 키 이름으로 grep 하면 DTO 밖에는 안 나오지만(그래서 한때 미출처로
        # 적었습니다), 값을 고르는 자리는 ``TrainScheduleViewModel.java:3137``
        # 과 ``:3147`` 의 **같은 조건** 두 개입니다:
        # ``if (filterUiData.isSrt() || filterUiData.isSuseoTogether())``.
        # 그 두 지역변수가 ``TrainScheduleIn`` 생성자의 ``ebizCrossCheck`` /
        # ``srtCheckYn`` 자리로 들어갑니다(``TrainScheduleIn.java:33`` 선언).
        #
        # 그래서 "짝으로 움직인다" 는 확인됐지만 두 가지는 아직 아닙니다 --
        # 고르는 문자열이 ``"Y"``/``"N"`` 인지(리터럴이 AlienGuard 로 보호됨),
        # 그리고 조건이 SRT 체크박스 **하나**인지(실제로는 수서 함께 조회까지
        # 포함한 OR). 예전 인용 ``MainBookingActivity.java:775-776`` 은 7.0.6 에
        # 없는 6.5.0 클래스입니다.
        "ebizCrossCheck": "Y" if query.include_srt else "N",
        "srtCheckYn": "Y" if query.include_srt else "N",
        "rtYn": "N",
        "adjStnScdlOfrFlg": "N",
    }
    if member_card_no:
        form["mbCrdNo"] = member_card_no
    # 선언 순서의 근거는 이제 요청 DTO 자체입니다 -- ``TrainScheduleIn.java:27``
    # 의 ``@Metadata`` 속성 배열과 ``:33`` 이후의 필드 선언이 그 순서를 말합니다
    # (예전 인용 ``SeatMovieService.java:14`` 는 7.0.6 에 없는 클래스입니다).
    # 순서는
    # ... adjStnScdlOfrFlg, mbCrdNo, tkPsrmClCd, tkRcvdAmt, qryDvCd, qryStNo,
    # qryStTrnNo, qryStTrnNo2, pgPrCnt, chtnCnt, ... so the paging block goes
    # after mbCrdNo. tkPsrmClCd/tkRcvdAmt belong to the ticket-change entry
    # point, which this client does not drive, and the app leaves them null
    # there (Retrofit then omits the @Field).
    if not isinstance(query.query_division_code, str) or not query.query_division_code:
        raise ValueError("query_division_code must be a non-empty string")
    if not isinstance(query.connection_station_codes, tuple) or any(
        not isinstance(code, str) or not code for code in query.connection_station_codes
    ):
        raise ValueError("connection_station_codes must be a tuple of non-empty strings")
    if query.connection_train_group_code is not None and (
        not isinstance(query.connection_train_group_code, str)
        or not query.connection_train_group_code
    ):
        raise ValueError("connection_train_group_code must be a non-empty string or None")
    if not transfer and (
        query.connection_station_codes or query.connection_train_group_code is not None
    ):
        raise ValueError("connection filters require transfer=True")
    form["qryDvCd"] = query.query_division_code
    # buildTrainScheduleIn() leaves qryStNo/qryStTrnNo/qryStTrnNo2/pgPrCnt
    # literal null on every fresh (first-page) build (TrainScheduleViewModel
    # .java:3212), and TrainScheduleIn.write$Self only encodes each when it is
    # non-null (TrainScheduleIn.java:641-650) — so the app sends none of the
    # four keys on the first page. The only continuation path
    # (TrainScheduleViewModel.java:7340) overwrites qryStNo/qryStTrnNo/
    # qryStTrnNo2 from a 3-tuple cursor via copy$default(mask=254) but never
    # touches pgPrCnt, which stays null (= unsent) forever. Mirror that: omit
    # all four on the first page, and never send pgPrCnt at all.
    if continuation is not None:
        form["qryStNo"] = continuation.query_station_no
        form["qryStTrnNo"] = continuation.query_train_no
        # The continuation carries the outcome of the app's own rule rather
        # than re-deciding it here: TrainSearchResult.next_page leaves
        # query_train_no2 at "" and TransferSearchResult.next_page fills it
        # from h_ectb_trn_no_next.
        #
        # The old citation b5/c.java:192-194 ("setSelectTransferPages fires
        # only when both transfer cursors came back non-empty") is a 6.5.0
        # path that does not exist in 7.0.6, and no such method name exists
        # there either. Partially re-derived from the apktool smali instead,
        # because jadx dropped this block -- the only reads of
        # getHQryStNoNext/getHTrnNoNext/getHPrcdTrnNoNext/getHEctbTrnNoNext
        # outside the DTO survive only in
        # analysis/apktool/smali_classes5/com/korail/talk/ui/screen/train/
        # TrainScheduleViewModel.smali. There, responseTrainSchedule builds the
        # 3-tuple cursor in two shapes and branches on a boolean register:
        #   :36812  if-nez v3 -> Triple(hQryStNoNext, hPrcdTrnNoNext,
        #                               hEctbTrnNoNext)        (:36834-36843)
        #   fallthrough        -> Triple(hQryStNoNext, hTrnNoNext, <literal>)
        #                                                      (:36814-36831)
        # storing the result at :36851, or null when the guard at :36786/:36804
        # fails. The third slot on the fallthrough branch is an AlienGuard
        # literal decoded from an empty byte[] -- the same call shape the DTO
        # uses for its "" field defaults (TrainScheduleOut.java:106) -- so that
        # branch does not read a third cursor off the response at all. That is
        # what supports the shape we forward here.
        #
        # That boolean IS statically readable -- an earlier note of ours said
        # it had "no static definition in reach", and that was wrong. The
        # dataflow, all in the same smali file:
        #   :35654        getStrJobId() -> v0
        #   :35660-35676  AlienGuard method_name_4(...) -> v1, a literal
        #                 decoded at runtime from a 1-byte seed
        #   :35682-35694  filled-new-array {v0, v1}; AppSuitLinker1
        #                 .djsflxlftm1(null, VTHLSC..., arr) -> boxed Boolean
        #                 -> booleanValue() -> v0. A 2-arg string compare,
        #                 dispatched reflectively, so the callee is an index.
        #   :35696-35698  const/4 v9, 0x1 ; xor-int/2addr v0, v9 -- INVERTED
        #   :35790        move v3, v0 (flag into v3, before the trnInfo loop)
        #   :35845        iput v3 -> responseTrainSchedule$1.STLaqs:I
        #   :34950        iget v3 <- STLaqs (resume, STLr==1)
        #   :34843        iget v10 <- STLaqs (resume, STLr==2), then :34910
        #                 move v3, v10 restores the same register convention
        #   :36812        if-nez v3 -- and nothing writes v3 between the loop
        #                 exit at :36204 and here
        # So the selector is  v3 = !(strJobId == <protected literal>):
        #   strJobId != literal -> Triple(hQryStNoNext, hPrcdTrnNoNext,
        #                                 hEctbTrnNoNext)   (:36834-36843)
        #   strJobId == literal -> Triple(hQryStNoNext, hTrnNoNext, <lit>)
        #                                                    (:36814-36831)
        #
        # Two different claims, and only the first is sourced. (a) The flag's
        # definition and the control flow are fully traceable, as above.
        # (b) The literal it is compared against is NOT: it is an AlienGuard
        # blob with no plaintext anywhere in ./analysis, so we cannot say
        # which strJobId value means transfer. Naming the :36834 branch the
        # transfer one is still inference from the field name
        # (h_ectb_trn_no_next, TrainScheduleOut.java:67), not a decoded
        # condition. The old "both cursors non-empty" wording stays wrong:
        # 7.0.6 branches on the echoed strJobId, not on emptiness. None of
        # this judges our cursor policy either way: the builder forwards
        # whatever the continuation carries.
        form["qryStTrnNo2"] = continuation.query_train_no2
    # NetworkService.STLibw flattens TrainScheduleInChtnRsStn / TrnGp arrays
    # as `chtnRsStnCd1`, `trnGpCd1` etc. The selected station or all candidates
    # are supplied by the caller; protected selection/default codes are not
    # inferred here.
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
    """7.0.6 ``ScheduleViewSpecial`` 의 ``@FieldMap`` 입력.

    APK ``NetworkService`` 는 ``TrainScheduleIn`` 을 JSON으로 직렬화한 뒤
    스칼라와 목록을 폼 필드로 펼칩니다. 조회 본문의 공통 키는 기존
    ``ScheduleView`` 와 같지만, 7.0.6 ``CommonIn`` 은 ``Key`` 를 선언하고
    ``Sid`` 는 선언하지 않습니다. 정렬별 ``qryDvCd`` 값은 보호되어
    :class:`TrainSearchQuery` 에서 받은 값만 보냅니다.
    """
    form = build_train_search_form(
        config,
        query,
        departure_name=departure_name,
        arrival_name=arrival_name,
        sid="",
        member_card_no=member_card_no,
        continuation=continuation,
        transfer=transfer,
    )
    # build_train_search_form already gives this shape: qryStNo/qryStTrnNo/
    # qryStTrnNo2 are absent on a first page (continuation=None) and present
    # only once a continuation exists, and pgPrCnt is never present at all —
    # buildTrainScheduleIn() leaves all four paging fields literal null on
    # every fresh (first-page) build, and the only continuation path never
    # touches pgPrCnt either. Nothing further to strip here.
    device = form.pop("Device")
    version = form.pop("Version")
    # NetworkService.STLibw keeps only non-empty JsonPrimitive values; unlike
    # the legacy @Field overload it does not send empty values.
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
    """``research.actualTrainSchedule.do`` 의 정차역·지연 조회 폼을 만듭니다.

    공통 키는 :func:`_device_version` 이 주는 ``Device``/``Version`` 과,
    ``KorailConfig(lang=...)`` 을 설정했을 때만 함께 실리는 ``lang`` 입니다.
    ``Key`` 는 붙지 않습니다. 예전에 "``Device``/``Version`` 만"이라고 적혀
    있던 것은 그 헬퍼가 조건부 ``lang`` 을 싣게 된 뒤로 낡은 설명이었습니다 --
    이 라우트의 입력 DTO 도 ``lang`` 을 선언합니다
    (``ActualTrainScheduleIn.java:53`` 의 합성 직렬화 생성자가
    ``@SerialName(Constants.LANG)`` 을 달고 있고, 실제 필드 선언과 인코딩
    게이트는 상위 ``CommonIn.java:40``·``:432``·``:467-474`` 입니다).

    ``trnNo`` 는 다섯 자리로 0 을 채웁니다.
    """
    return {
        **_device_version(config),
        "runDt": run_date,
        "trnNo": train_no.zfill(5),
    }


def build_common_code_form(
    config: KorailConfig,
    code: str | Sequence[str],
    *,
    depart_date: str = "",
    arrival_date: str = "",
    holiday_yn: str = "",
) -> dict[str, object]:
    """``common.code.do`` 의 공통코드 조회 폼을 만듭니다.

    ``code`` 는 문자열 하나이거나 시퀀스이며, 하나를 줘도 목록으로 감싸 보냅니다 —
    전선에서는 같은 이름의 반복 키가 됩니다. 7.0.6 이 같은 경로에 바인딩을 둘
    선언한 것과 맞습니다: ``postCommonCode(@FieldMap)``
    (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:317``)와
    ``postCommonCodeMulti(@FieldMap, @Field("code") List<String>)``(``:321``).

    ``depart_date``·``arrival_date``·``holiday_yn`` 은 비어 있으면 키 자체가
    빠집니다. 화면 크기와 ``OSVersion``(안드로이드 SDK 정수)은 설정에서 옵니다.

    **그 세 인자는 7.0.6 에 대응물이 없습니다.** 요청 DTO
    ``analysis/jadx/sources/com/korail/talk/network/model/CommonCodeIn.java:31-34``
    와 그 합성 생성자의 ``@SerialName`` 목록(``:55``)이 선언하는 필드는
    ``Device``·``Version``·``Key``·``lang``·``code``·``deviceWidth``·
    ``deviceHeight``·``OSVersion`` 여덟 개뿐이고, ``departDate``·``holidayYn`` 은
    ``analysis/jadx/sources/com/korail/`` 전체에 검색 결과가 0 입니다. 2026-09-22
    실서버에서도 무해했습니다 — ``app.holiday.popup`` 을 ``depart_date``
    ``"20260925"``/``arrival_date`` ``"20260926"``/``holiday_yn`` ``"Y"`` 와 함께
    보낸 응답 값이 세 키를 뺀 평범한 호출과 같았습니다. 즉 앱이 만든 적 없는
    전선 모양이면서 서버도 무시하는 값이라, 공개 메서드
    :meth:`~korail_mobile_api.KorailClient.get_common_code` 는 일부러 노출하지
    않습니다. 여기 남겨 둔 것은 순전히 그 관측 기록을 위해서입니다.

    로그인 직전에 비밀번호 암호화 파라미터를 받아 오는 것도 이 라우트입니다
    (:meth:`~korail_mobile_api.session.KorailSessionClient.get_login_crypto_info`).
    """
    form: dict[str, object] = {
        **_device_version(config),
        "Key": config.key,
        "code": [code] if isinstance(code, str) else list(code),
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
    }
    if depart_date:
        form["departDate"] = depart_date
    if arrival_date:
        form["arrivalDate"] = arrival_date
    if holiday_yn:
        form["holidayYn"] = holiday_yn
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
    """``myTicket.MyTicketNewList.do`` 의 승차권 목록 조회 폼을 만듭니다.

    ``txtIndex``(``mode``)는 페이지 커서가 아니라 **목록 종류**입니다. ``"1"`` 은
    현재 승차권, ``"2"`` 는 구매이력이고 그 밖의 값은
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    이 키는 ``MyTicketListIn.java:62`` 의 ``@SerialName("txtIndex")`` 이고 7.0.6
    호출 지점은 ``MyTicketBaseViewModel.java:1029``·``LoginViewModel.java:1083``·
    ``AppViewModel$executeTicketListForAutoLogin$result$1.java:67`` 입니다. 다만
    **값 리터럴은 AlienGuard 로 보호돼** 어느 화면이 ``"1"`` 을 보내고 어느
    화면이 ``"2"`` 를 보내는지는 정적으로 읽을 수 없습니다 -- 예전에 달려 있던
    ``TicketListActivity``/``TicketPurchaseHistoryActivity`` 인용은 7.0.6 에 없는
    6.5.0 클래스였습니다. 두 값의 뜻은 대신 라이브로 확인했습니다(2026-09-22):
    깨끗한 계정에서 ``"1"`` 은 ``WRT300005``(조회자료 없음), ``"2"`` 는 넓은
    날짜 범위로 구매이력 128건을 돌려줬습니다.

    ``boarding_date_from``·``boarding_date_to`` 는 그대로 전달합니다 — 서버가
    받아들이거나 거절합니다. 어느 화면이 두 날짜를 갖춰 보내는지는 위와 같은
    이유(보호된 리터럴 + 6.5.0 클래스 부재)로 **미출처**이고, 이 함수는 어차피
    그 UI 관례를 강제하지 않습니다. 잘못된 범위는 서버가 ``WRT100101`` 로
    거절합니다(2026-09-22 확인).

    페이지는 ``h_page_no`` 로 나가며 1 미만은 1 로 올립니다. 앱의 두 호출 지점은
    언제나 ``"1"`` 을 보냅니다.
    """
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
    """``copt.gdMenuLt.do`` 의 MaaS 메뉴 조회 폼.

    ``Device``·``Version``·``Key``·``timeStamp`` 를 싣고,
    ``KorailConfig(lang=...)`` 을 설정했으면 :func:`_device_version` 이 ``lang``
    도 함께 싣습니다(그 헬퍼가 조건부 ``lang`` 을 갖게 된 뒤로 이 열거도
    갱신했습니다). 7.0.6
    ``GdMenuLtIn.java:59-61`` 은 ``super(null,null,null,null,15,null)`` 로
    ``CommonIn`` 의 네 필드(``Device``/``Version``/``Key``/``lang``)를 한꺼번에
    기본값화하는데, ``CommonIn.write$Self`` 가 그중 ``Device``/``Version``/``Key``
    에 동일한 인코딩 게이트를 쓰므로(``CommonIn.java:448-465``) 셋 중 둘만 나가는
    분기는 없습니다 — 이 라우트를 호출하는 곳은 ``include_common=False`` 를 써서
    :meth:`~korail_mobile_api.http.KorailHttpClient.common_fields` 의 주입을 건너뛰므로, ``Key``
    는 여기서 직접 싣습니다.
    """
    return {
        **_device_version(config),
        "Key": config.key,
        "timeStamp": str(int(time.time() * 1000)),
    }


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    """``EbizMaasStationList.do`` 의 역 목록 조회 폼을 만듭니다.

    부가서비스 코드(``addSrvDvCd``) 하나뿐이고 공통 필드도 붙지 않습니다. 값은
    :meth:`~korail_mobile_api.client.KorailClient.get_maas_menu_list` 결과의
    항목에서 옵니다. 비어 있으면 ``ValueError`` 입니다.
    """
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise ValueError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}
