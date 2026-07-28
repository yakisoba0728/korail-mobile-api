"""읽기 라우트 가운데 기본 조회들의 요청 폼 빌더.

열차 조회(``seatMovie.ScheduleView``), 좌석 조회, 역 정보, 공통코드,
승차권 목록, MaaS 메뉴의 폼을 만든다. 나머지 읽기 라우트는
:mod:`korail_mobile_api.read_payloads`, 상태 변경은
:mod:`korail_mobile_api.mutation_payloads` 에 있다.

여기 함수들은 dict 를 돌려줄 뿐 아무것도 보내지 않는다. 필드 이름과 순서는
APK 의 Retrofit 선언에서 나왔고,
:mod:`korail_mobile_api.safety` 의 필드 계약이 전송 직전에 그것을 다시
확인한다.
"""
import time

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
    if (
        not isinstance(value, str)
        or len(value) not in lengths
        or any(character < "0" or character > "9" for character in value)
    ):
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
    if not isinstance(train, TrainSummary):
        raise KorailProtocolError("train must be a TrainSummary")
    if type(passenger_count) is not int or not 1 <= passenger_count <= 9:
        raise ValueError("passenger_count must be an integer from 1 through 9")
    if car_no is not None and (type(car_no) is not int or car_no < 1):
        raise ValueError("car_no must be a positive integer")
    _required_ascii_digits(
        train.train_no,
        "train_no",
        lengths=frozenset(range(1, 6)),
    )
    _required_ascii_digits(
        train.train_group_code,
        "train_group_code",
        lengths=frozenset({3}),
    )
    _required_ascii_digits(
        train.departure_station_code,
        "departure_station_code",
        lengths=frozenset({4}),
    )
    _required_ascii_digits(
        train.arrival_station_code,
        "arrival_station_code",
        lengths=frozenset({4}),
    )
    _required_ascii_digits(
        train.departure_date,
        "departure_date",
        lengths=frozenset({8}),
    )
    _required_ascii_digits(
        train.run_date,
        "run_date",
        lengths=frozenset({8}),
    )
    _required_ascii_digits(
        train.train_class_code,
        "train_class_code",
        lengths=frozenset({2}),
    )
    _required_ascii_digits(
        train.departure_run_order,
        "departure_run_order",
        lengths=frozenset({6}),
    )
    _required_ascii_digits(
        train.arrival_run_order,
        "arrival_run_order",
        lengths=frozenset({6}),
    )
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


def _resolved_goods_no(train: TrainSummary) -> str | None:
    # x4/b.java:23 forwards trainInfo.getTxtGdNo() verbatim, which is null for a
    # normal (non-goods) train (SeatSearchRequest.txtGdNo defaults to null), and
    # Retrofit drops null @Field params (ResearchService getCarList txtGdNo:37 /
    # getSeatList gdNo:59). So the app OMITS the field for standard searches;
    # return None here and let the builders delete the key when there is none.
    return train.goods_no or None


def _inventory_sid(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("sid must be a non-empty string")
    return value


def build_seat_car_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    passenger_count: int,
    sid: str,
    room_class_code: str = "1",
) -> dict[str, str]:
    validate_seat_inventory_inputs(train, passenger_count)
    form = {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "Sid": _inventory_sid(sid),
        "txtMenuId": "11",
        "txtPsrmClCd": _validated_room_class_code(room_class_code),
        "txtRunDt": train.run_date or "",
        "txtDptDt": train.departure_date or "",
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
        "txtSeatAttCd": train.seat_attribute_code,
        "txtGdNo": _resolved_goods_no(train),
    }
    if not train.seat_attribute_code:
        del form["txtSeatAttCd"]
    if form["txtGdNo"] is None:
        del form["txtGdNo"]
    return form


def build_seat_inventory_form(
    config: KorailConfig,
    train: TrainSummary,
    car_no: int,
    *,
    passenger_count: int,
    sid: str,
    room_class_code: str = "1",
) -> dict[str, str]:
    validate_seat_inventory_inputs(
        train,
        passenger_count,
        car_no=car_no,
    )
    form = {
        "Device": config.device,
        "Version": config.version,
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
        "seatAttCd": train.seat_attribute_code,
        "dptStnRunOrdr": train.departure_run_order or "",
        "arvStnRunOrdr": train.arrival_run_order or "",
        "totPsgCnt": str(passenger_count),
        "gdNo": _resolved_goods_no(train),
        "isArrow": "true",
        "Sid": _inventory_sid(sid),
        "ctlDvCd": "",
    }
    if not train.seat_attribute_code:
        del form["seatAttCd"]
    if form["gdNo"] is None:
        del form["gdNo"]
    return form


def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
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
) -> dict[str, str]:
    """``seatMovie.ScheduleView`` 폼을 한 페이지 분량으로 만든다.

    ``continuation=None`` 이면 앱의 첫 페이지 요청이다. ``b5/c.java`` 는 모든
    검색에서 ``setQryDvCd("1")``(``:145``),
    ``setSelectTransferPage("0", "10")``(``:146``),
    ``setSelectTransferPages("00000", "")``(``:147``)를 조건 없이 부르므로
    ``qryDvCd``/``qryStNo``/``pgPrCnt``/``qryStTrnNo``/``qryStTrnNo2`` 는 항상
    전선에 오른다 — 환승 전용 부가 필드가 아니다. 그다음 페이지는
    :meth:`TrainSearchResult.next_page` 가 준
    :class:`TrainSearchContinuation` 을 넘겨 요청한다.

    ``transfer=True`` 는 같은 엔드포인트에 직통 대신 환승 여정을 묻는다. 움직이는
    필드는 정확히 하나다. ``radJobId`` 가
    :data:`~korail_mobile_api.KORAIL_DIRECT_ITINERARY_CODE` 에서
    :data:`~korail_mobile_api.KORAIL_TRANSFER_ITINERARY_CODE` 로 바뀐다. 앱의
    환승 재조회도 그게 전부다 — WRD000061 대화상자 처리기
    (``DirectInquiryActivity.java:284-296``, ``n3`` 의 ``102``/확인 가지)가
    직통 검색에 쓰던 **바로 그** ``RsvInquiryRequest`` 객체에
    ``setRadJobId(TRANSFER_SQ_NO.getCode())`` 만 부르고 그대로
    ``TransferInquiryActivity`` 에 ``INQUIRY_REQUEST`` 로 넘긴다. 다른 것은
    건드리지 않는다(``smali/…/DirectInquiryActivity.smali:1677-1689``).

    ``SeatMovieService.java:14`` 필드 목록 꼬리의
    ``chtnCnt``/``chtnRsStnCd1``/``trnGpCnt``/``trnGpCd1`` 은 여기 속하지 않는다.
    ``b5/c.java:154-160`` 은 사용자가 ``TRANSFER_CHTNRSSTNCD`` 인텐트 엑스트라로
    특정 환승역을 따로 지정했을 때만 그것들을 채우며, 그 화면은 이 클라이언트가
    다루지 않는다.
    """
    if continuation is not None and type(continuation) is not (
        TrainSearchContinuation
    ):
        raise KorailProtocolError(
            "KORAIL train search continuation must be an exact "
            "TrainSearchContinuation"
        )
    form = {
        "Device": config.device,
        "Version": config.version,
        "Sid": sid,
        "txtMenuId": "11",
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
        "txtPsgFlg_2": "0",
        "txtPsgFlg_3": "0",
        "txtPsgFlg_4": "0",
        "txtPsgFlg_5": "0",
        "txtSeatAttCd_2": "000",
        "txtSeatAttCd_3": "000",
        "txtSeatAttCd_4": "015",
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
    form["qryDvCd"] = "1"
    if continuation is None:
        form["qryStNo"] = "0"
        form["qryStTrnNo"] = "00000"
        form["qryStTrnNo2"] = ""
        form["pgPrCnt"] = "10"
    else:
        form["qryStNo"] = continuation.query_station_no
        form["qryStTrnNo"] = continuation.query_train_no
        # setSelectTransferPages only fires when both transfer cursors came back
        # non-empty (b5/c.java:192-194), which a direct search never does. The
        # continuation carries the outcome of that rule rather than re-deciding
        # it here: TrainSearchResult.next_page leaves query_train_no2 at "" and
        # TransferSearchResult.next_page fills it from h_ectb_trn_no_next.
        form["qryStTrnNo2"] = continuation.query_train_no2
        form["pgPrCnt"] = continuation.page_count
    return form


def build_train_schedule_form(
    config: KorailConfig,
    run_date: str,
    train_no: str,
) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
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
    form: dict[str, object] = {
        "Device": config.device,
        "Version": config.version,
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
    # txtIndex is a fixed list-mode selector, not a page cursor:
    # TicketListActivity.java:937-939 sends "1" for the active/current ticket
    # list and TicketPurchaseHistoryActivity.java:276-278 sends "2" for the
    # purchase-history list (MyTicketService getTicketList). The page rides
    # h_page_no (both app call sites pin it to "1"); history mode additionally
    # carries h_abrd_dt_from/h_abrd_dt_to boarding-date bounds.
    if mode not in {TICKET_LIST_MODE_ACTIVE, TICKET_LIST_MODE_HISTORY}:
        raise KorailProtocolError(
            'ticket list mode must be "1" (active) or "2" (history)'
        )
    # History mode without the bounds is a form the app never builds: every
    # entry point into TicketPurchaseHistoryActivity (:365, :372, :719) arrives
    # with both dates formatted, and :277-280 sends them. The comment above has
    # always said history "carries" them; this makes that true rather than
    # aspirational. Mode "1" deliberately keeps the empty strings, because
    # TicketListActivity.java:939-941 transmits them empty.
    if mode == TICKET_LIST_MODE_HISTORY and not (
        boarding_date_from.strip() and boarding_date_to.strip()
    ):
        raise KorailProtocolError(
            'ticket list mode "2" (history) requires both boarding_date_from '
            "and boarding_date_to; the app never sends this list without them"
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
    return {
        "Device": config.device,
        "Version": config.version,
    }


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise ValueError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}
