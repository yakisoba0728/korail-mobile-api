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
from typing import TypeGuard

from .config import KorailConfig
from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_TRANSFER_ITINERARY_CODE,
)
from .errors import KorailProtocolError
from .models import TrainSearchContinuation, TrainSearchQuery, TrainSummary


def _device_version(config: KorailConfig) -> dict[str, str]:
    """The ``Device`` and ``Version`` pair every read form here starts with."""
    return {"Device": config.device, "Version": config.version}


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
    # x4/b.java:19,23 derive txtSeatAttCd/txtGdNo from the selected train row
    # rather than pinning them; validate the row's own values when present so
    # the seat-map builders can forward a dynamic-but-well-formed value.
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
    # psrmClCd / txtPsrmClCd is the user-selected cabin class, not a constant:
    # c5/c.java:90 reads RSeat.SEAT_PSRM_CL_CD and feeds it into
    # X4.b.getSearchRequest -> setTxtPsrmClCd (x4/b.java:18). The value comes
    # from getSelectSeatTypeCode (U4/a.java:87), which only ever yields
    # K4/o.java GENERAL("1", 일반실) or SPECIAL("2", 특실), so restrict to that
    # domain and let general ("1") stay the default.
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

    ``txtTrnNo`` 는 다섯 자리로 0 을 채웁니다. ``txtSeatAttCd`` 는 열차 행이 좌석
    속성 코드를 가지고 있을 때만 실립니다 — ``TrainResearchIn.java`` 의
    ``txtSeatAttCd`` 를 앱이 ``trainInfo.getH_seat_att_cd()`` 그대로 넘기고,
    ScheduleView 행처럼 코드가 없으면 Retrofit 이 ``@Field`` 를 떨어뜨리기
    때문입니다(``NetworkApi.java`` 의 ``getCarList``). 일반석 ``"015"`` 로 대신
    채우지 않습니다. ``txtGdNo`` 도 값이 없으면 같은 이유로 빠집니다.

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
        # x4/b.java:19 forwards trainInfo.getH_seat_att_cd() verbatim; when the
        # selected row carries no code (ScheduleView rows are null) Retrofit
        # omits the @Field (getCarList txtSeatAttCd, ResearchService:37), so
        # omit it here rather than substituting a general-seat "015".
        **({"txtSeatAttCd": seat_attribute} if seat_attribute else {}),
        # x4/b.java:23 forwards trainInfo.getTxtGdNo() verbatim, which is null for
        # a normal (non-goods) train (SeatSearchRequest.txtGdNo defaults to null),
        # and Retrofit drops null @Field params (ResearchService getCarList
        # txtGdNo:37 / getSeatList gdNo:59). So the app OMITS the field for
        # standard searches; leave the key out here when there is none.
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

    ``seatAttCd`` 와 ``gdNo`` 는 값이 없으면 빠집니다. ``getSeatList`` 도 null
    ``@Field`` 를 떨어뜨리기 때문입니다(``ResearchService:59``). ``isArrow`` 는
    고정 ``"true"``, ``ctlDvCd`` 는 고정 빈 문자열입니다.

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
        # As with getCarList, getSeatList forwards h_seat_att_cd verbatim and
        # Retrofit omits the @Field when it is null (ResearchService:59), so
        # omit seatAttCd for a row without a code instead of sending "015".
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
        # MainBookingActivity.java:775-776 sets both ebizCrossCheck and
        # srtCheckYn from the single "include SRT" checkbox (f29041T), so the
        # app always sends them equal; keep the pair coupled to include_srt.
        "ebizCrossCheck": "Y" if query.include_srt else "N",
        "srtCheckYn": "Y" if query.include_srt else "N",
        "rtYn": "N",
        "adjStnScdlOfrFlg": "N",
    }
    if member_card_no:
        form["mbCrdNo"] = member_card_no
    # Declared order in SeatMovieService.java:14 is
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
        # setSelectTransferPages only fires when both transfer cursors came back
        # non-empty (b5/c.java:192-194), which a direct search never does. The
        # continuation carries the outcome of that rule rather than re-deciding
        # it here: TrainSearchResult.next_page leaves query_train_no2 at "" and
        # TransferSearchResult.next_page fills it from h_ectb_trn_no_next.
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

    ``Device``/``Version`` 만 붙고 ``Key`` 는 붙지 않습니다. ``trnNo`` 는 다섯
    자리로 0 을 채웁니다.
    """
    return {
        **_device_version(config),
        "runDt": run_date,
        "trnNo": train_no.zfill(5),
    }


def build_common_code_form(
    config: KorailConfig,
    code: str | list[str],
    *,
    depart_date: str = "",
    arrival_date: str = "",
    holiday_yn: str = "",
) -> dict[str, object]:
    """``common.code.do`` 의 공통코드 조회 폼을 만듭니다.

    ``code`` 는 문자열 하나이거나 목록이며, 하나를 줘도 목록으로 감싸 보냅니다 —
    전선에서는 같은 이름의 반복 키가 됩니다.

    ``depart_date``·``arrival_date``·``holiday_yn`` 은 비어 있으면 키 자체가
    빠집니다. 화면 크기와 ``OSVersion``(안드로이드 SDK 정수)은 설정에서 옵니다.

    로그인 직전에 비밀번호 암호화 파라미터를 받아 오는 것도 이 라우트입니다
    (:meth:`~korail_mobile_api.session.KorailSessionClient.get_login_crypto_info`).
    """
    form: dict[str, object] = {
        **_device_version(config),
        "Key": config.key,
        "code": [code] if isinstance(code, str) else code,
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
    현재 승차권(``TicketListActivity.java:937-939``), ``"2"`` 는 구매이력
    (``TicketPurchaseHistoryActivity.java:276-278``)이고 그 밖의 값은
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    ``boarding_date_from``·``boarding_date_to`` 는 그대로 전달합니다 — 서버가
    받아들이거나 거절합니다. 화면은 ``"2"`` 에서 언제나 두 날짜를 갖춰 보내고
    (``TicketPurchaseHistoryActivity.java:277-280``) ``"1"`` 은 빈 문자열로
    보내지만(``TicketListActivity.java:939-941``), 이 함수는 그 UI 관례를
    강제하지 않습니다.

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

    ``Device``·``Version``·``Key``·``timeStamp`` 를 싣습니다. 7.0.6
    ``GdMenuLtIn.java:59-61`` 은 ``super(null,null,null,null,15,null)`` 로
    ``CommonIn`` 의 네 필드(``Device``/``Version``/``Key``/``lang``)를 한꺼번에
    기본값화하는데, ``CommonIn.write$Self`` 가 그중 ``Device``/``Version``/``Key``
    에 동일한 인코딩 게이트를 쓰므로(``CommonIn.java:448-465``) 셋 중 둘만 나가는
    분기는 없습니다 — 이 라우트를 호출하는 곳은 ``include_common=False`` 를 써서
    :func:`~korail_mobile_api.http.common_fields` 의 주입을 건너뛰므로, ``Key``
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
