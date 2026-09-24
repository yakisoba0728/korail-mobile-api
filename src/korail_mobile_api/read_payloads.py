# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·예약·환불·마일리지·할인카드·MaaS 조회 폼 빌더. 기본 조회는 payloads, 상태 변경은 mutation_payloads 에 있습니다. 키 근거는 DTO·호출부이며 FieldMap 선언
자체가 키 이름·순서를 검증하지는 않습니다."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

from .config import KorailConfig
from .errors import KorailProtocolError
from ._payload_helpers import _device_version, _is_ascii_digits
from .payloads import build_cache_query
from .read_models import (
    CommuterInfoResponse,
    CommuterPassengerOption,
    PassMenuData,
)


if TYPE_CHECKING:
    from .mutation_models import StationRefundVerificationRequest


def _int_text(value: int, name: str) -> str:
    """페이지 값을 문자열 DTO 필드로 옮깁니다. 앱 DTO 는 String 이고 범위 검사가 없어 값의 판정은 서버에 맡깁니다
    (CouponIn.java:29-30, ProductListIn.java:30-35, AmtSpecIn.java:30-36)."""
    if type(value) is not int:
        raise KorailProtocolError(f"{name} must be an integer")
    return str(value)


def _required_text(value: str | None, name: str) -> str:
    """``value`` 를 그대로 돌려주되 없거나 빈 문자열이면 거부합니다.

    호출자 대부분이 서버 응답에서 파싱한 선택 필드를 그대로 넘기므로, ``None`` 도 인자로 받아
    :class:`~korail_mobile_api.errors.KorailProtocolError` 로 거절합니다."""
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(f"{name} must not be empty")
    return value


def _optional_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise KorailProtocolError(f"{name} must be a string")
    return value


def _ascii_digits(
    value: str,
    name: str,
    *,
    lengths: frozenset[int] | None = None,
    maximum_length: int | None = None,
    allow_empty: bool = False,
) -> str:
    """ASCII 숫자 검사. lengths 는 허용 길이 집합, maximum_length 는 상한입니다. 둘 다 없으면 길이를 제한하지 않고 allow_empty=True 이면 빈 문자열도
    허용합니다."""
    if allow_empty and value == "":
        return value
    if lengths is not None:
        if not _is_ascii_digits(value, lengths):
            if len(lengths) == 1:
                (length,) = lengths
                raise KorailProtocolError(
                    f"{name} must contain exactly {length} ASCII digits"
                )
            expected = ", ".join(str(length) for length in sorted(lengths))
            raise KorailProtocolError(f"{name} must contain {expected} ASCII digit(s)")
        return value
    if (
        not isinstance(value, str)
        or not value
        or any(character < "0" or character > "9" for character in value)
        or (maximum_length is not None and len(value) > maximum_length)
    ):
        suffix = (
            f" with at most {maximum_length} digits"
            if maximum_length is not None
            else ""
        )
        raise KorailProtocolError(f"{name} must be an ASCII decimal string{suffix}")
    return value


def _passenger_count(value: int, name: str) -> int:
    if type(value) is not int or not 1 <= value <= 9:
        raise KorailProtocolError(f"{name} must be an integer from 1 through 9")
    return value


@dataclass(frozen=True)
class FreeSeatCarRequest:
    run_date: str
    train_no: str
    departure_construction_order: str
    arrival_construction_order: str
    departure_run_order: str
    arrival_run_order: str


@dataclass(frozen=True)
class GuideSeatConditionRequest:
    """guideSeatCnd.do 입력. 2026-09-22 라이브에서는 좌석속성코드 14종이 같은 도우미석 안내(FAIL/MRR800011)를 반환했습니다. 앱은 SeatType.HELPER 코드를
    사용합니다(TrainOptionViewModel.java:270). 이 표본만으로 모든 입력·시점의 응답이 같다고 보장하지 않습니다."""

    seat_attribute_code: str


@dataclass(frozen=True)
class SeatAssignmentScheduleRequest:
    #: ``menuId`` — 좌석배정·할인 메뉴 코드입니다. 일반 검색 메뉴 ``"11"`` 은 빈 목록만 돌려주므로(2026-09-22 확인) 행을 받으려면 ``"A1"``/``"A2"``
    #: (:data:`~korail_mobile_api.constants.KORAIL_DISCOUNT_CARD_MENU_ID`)를 씁니다. 자세한 것은
    #: :meth:`~korail_mobile_api.client.KorailClient.get_seat_assignment_schedule` docstring 참조.
    menu_id: str
    departure_date: str
    departure_time: str
    departure_station_name: str
    arrival_station_name: str
    train_group_code: str
    room_class_code: str
    seat_attribute_code: str
    passenger_count: int
    standing_detour_division_name: str
    transfer_type_code: str
    connection_arrival_station_name: str

    def __post_init__(self) -> None:
        _passenger_count(self.passenger_count, "passenger_count")


@dataclass(frozen=True)
class MergeSeatsInquiryRequest:
    boarding_datetime: str
    run_datetime: str
    train_no: str
    departure_station_name: str
    arrival_station_name: str
    selected_station_name: str | None
    room_class_code: str
    seat_attribute_code: str
    passenger_count: int

    def __post_init__(self) -> None:
        _passenger_count(self.passenger_count, "passenger_count")


def build_free_seat_car_form(
    request: FreeSeatCarRequest,
) -> dict[str, str]:
    return {
        "runDt": request.run_date,
        "trnNo": request.train_no.zfill(5),
        "dptStnConsOrdr": request.departure_construction_order,
        "arvStnConsOrdr": request.arrival_construction_order,
        "dptStnRunOrdr": request.departure_run_order,
        "arvStnRunOrdr": request.arrival_run_order,
    }


def build_guide_seat_condition_form(
    request: GuideSeatConditionRequest,
) -> dict[str, str]:
    return {"rqSeatAttCd": request.seat_attribute_code}


def build_seat_assignment_schedule_form(
    request: SeatAssignmentScheduleRequest,
) -> dict[str, str]:
    form = {
        "menuId": request.menu_id,
        "dptDt": request.departure_date,
        "dptTm": request.departure_time,
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
        "trnGpCd": request.train_group_code,
        "psrmClCd": request.room_class_code,
        "dirtChtnDvCd": request.transfer_type_code,
        "chtnArvRsStnNm": request.connection_arrival_station_name,
    }
    # seatAttCdN/psgNumN/stlbDturDvNmN 은 승객별 번호 그룹이고 psgNumN 은 인원수가 아니라 그 자리의 점유 플래그(0/1)입니다. 2026-09-22
    # 라이브: psgNum1=0/1 은 WRG000000, 2/02/3/9 는 SUPDATE 였고 그룹을 1..9 로 늘린 요청은 통과했습니다.
    for slot in range(1, request.passenger_count + 1):
        form[f"seatAttCd{slot}"] = request.seat_attribute_code
        form[f"psgNum{slot}"] = "1"
        form[f"stlbDturDvNm{slot}"] = request.standing_detour_division_name
    return form


def build_merge_seats_inquiry_form(
    request: MergeSeatsInquiryRequest,
) -> dict[str, str]:
    form = {
        "abrdDt": request.boarding_datetime,
        "runDt": request.run_datetime,
        "trnNo": request.train_no.zfill(5),
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
        "psrmClCd": request.room_class_code,
        "seatAttCd": request.seat_attribute_code,
        "totPsgNum": str(request.passenger_count),
    }
    if request.selected_station_name is not None:
        form["selRsStnNm"] = request.selected_station_name
    return form


@dataclass(frozen=True)
class PassScheduleRequest:
    selected_train_code: str
    departure_date: str
    departure_time: str
    transfer_type_code: str
    pass_kind_code: str
    pass_period_code: str
    pass_age_code: str
    #: txtSelPage: 2026-09-22 관측에서 요청값을 바꿔도 h_page_no=1 이었습니다. 앱의 해당 인자도 고정이지만 평문은 보호돼
    #: 있습니다(CheckUsagePeriodSectionViewModel.java:389). page_size 로 요청 건수를 정하며 페이징 신호의 관측 한계는
    #: PassScheduleMainInfo 참고.
    page_no: str
    #: ``txtCntPerPage`` — 실제로 결과 수를 정하는 값입니다.
    page_size: str
    departure_station_name: str
    arrival_station_name: str
    weekend_use_flag: str


def build_pass_schedule_form(
    request: PassScheduleRequest,
) -> dict[str, str]:
    return {
        "selGoTrain": request.selected_train_code,
        "selGoAbrdDt": request.departure_date,
        "txtGoHour": request.departure_time,
        "radChgTrnDvCd": request.transfer_type_code,
        "txtCmtrKndCd": request.pass_kind_code,
        "txtCmtrUtlTrmCd": request.pass_period_code,
        "txtCmtrUtlAgeCd": request.pass_age_code,
        "txtSelPage": request.page_no,
        "txtCntPerPage": request.page_size,
        "txtGoStart": request.departure_station_name,
        "txtGoEnd": request.arrival_station_name,
        "txtWkndUseFlg": request.weekend_use_flag,
    }


def build_service_status_query(
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    """``MobileService.cache`` 의 ``timeStamp`` 쿼리 — 캐시 파일 요청과 같은 모양입니다."""
    return build_cache_query(timestamp_ms)


def build_cart_list_form(
    pnr_no: str = "",
    additional_service_request_no: str = "",
) -> dict[str, str]:
    return {
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
        "addSrvReqNo": _optional_text(
            additional_service_request_no,
            "additional_service_request_no",
        ),
    }


def build_delay_discount_ticket_form(
    departure_date_to: str,
) -> dict[str, str]:
    # dptDtTo 속성의 전송 키는 명시적 h_page_no(DelayDiscountViewIn.java:50,77). 2026-09-16 관측: 날짜·1·다른 후보 키·키 생략 모두 같은 빈
    # SUCC. 할인권 없는 계정이므로 이 표본은 실제 필터 동작을 입증하지 못합니다.
    return {
        "h_page_no": _ascii_digits(
            departure_date_to, "departure_date_to", lengths=frozenset({8})
        )
    }


def build_discount_coupon_form(
    page_no: int = 1,
    pnr_no: str = "",
) -> dict[str, str]:
    return {
        "txtSelPage": _int_text(page_no, "page_no"),
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
    }


def build_pass_availability_form(
    kind_code: str,
    period_code: str,
    age_code: str,
) -> dict[str, str]:
    return {
        "txtCmtrKndCd": _required_text(kind_code, "kind_code"),
        "txtCmtrUtlTrmCd": _required_text(period_code, "period_code"),
        "txtCmtrUtlAgeCd": _required_text(age_code, "age_code"),
    }


def build_trip_menu_form(config: KorailConfig) -> dict[str, str]:
    return {
        **_device_version(config),
        "timeStamp": str(int(time.time() * 1000)),
    }


def build_pass_menu_form(menu_no: str) -> dict[str, str]:
    return {"menuNo": _required_text(menu_no, "menu_no")}


def build_crew_request_list_query(
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    """승무원 호출 사유 조회. 별도 입력은 timeStamp 뿐입니다(CrewCallCommonIn.java:50, NetworkRepositoryImpl.java:4105-4107).
    timestamp_ms 를 생략하면 현재 epoch 밀리초입니다.

    앱은 CommonIn.serializer() 로 인코딩하지만(NetworkService.java:3952-3955) CommonIn 은 sealed 추상 클래스라 그 직렬화기가
    CrewCallCommonIn$$serializer 로 넘기므로(CommonIn.java:35,70,220,350) timeStamp 가 나갑니다. 다형 판별 키(type, 값 보호)는 싣지
    않습니다."""
    return build_cache_query(timestamp_ms)


def build_commuter_kind_menu_query(
    commuter_kind_code: str,
) -> dict[str, str]:
    return {
        "cmtrKndCd": _required_text(
            commuter_kind_code,
            "commuter_kind_code",
        )
    }


def build_product_reservations_query(
    page_no: int = 1,
    page_size: int = 20,
    *,
    reservation_status_code: str | None = None,
    payment_status_code: str | None = None,
) -> dict[str, str]:
    query = {
        "txtSelPage": _int_text(page_no, "page_no"),
        "txtCntPerPage": _int_text(page_size, "page_size"),
    }
    # 상태 기본값은 보호돼 있습니다(ProductReservationViewModel.java:836). 입력 DTO 의 두 상태 필드는 호출자가 관측한 값으로 지정해야 합니다.
    if reservation_status_code is not None:
        query["txtRsvSttCd"] = _required_text(
            reservation_status_code, "reservation_status_code"
        )
    if payment_status_code is not None:
        query["txtStlSttCd"] = _required_text(
            payment_status_code, "payment_status_code"
        )
    return query


def build_product_detail_query(
    reservation_no: str,
    reservation_sequence: str | None = None,
) -> dict[str, str]:
    query = {
        "txtVrRsNo": _required_text(reservation_no, "reservation_no"),
    }
    if reservation_sequence is not None:
        query["txtVrRsvSqNo"] = _required_text(
            reservation_sequence, "reservation_sequence"
        )
    return query


def build_ticket_receipt_form(
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
    txt_index: str | None = None,
) -> dict[str, str]:
    form = {
        # 4자리 MMDD 만 허용합니다. 2026-09-22 라이브 승차권 128장은 4자리 128/128 성공, 8자리 ERZ800027 이었습니다. 여기서 막지 않으면
        # TicketListTicket.sale_date 를 그대로 넘긴 호출자가 원인이 모호한 서버 오류를 받습니다. 라우트별 차이는 OriginalTicketReference 참고.
        "h_orgtk_sale_dt": _ascii_digits(sale_date, "sale_date", lengths=frozenset({4})),
        "h_orgtk_wct_no": _required_text(window_no, "window_no"),
        "h_orgtk_sale_sqno": _required_text(
            sale_sequence,
            "sale_sequence",
        ),
        "h_orgtk_tk_ret_pwd": _required_text(
            return_password,
            "return_password",
        ),
    }
    if txt_index is not None:
        if not isinstance(txt_index, str):
            raise KorailProtocolError("txt_index must be a string or None")
        if txt_index.strip():
            form["txtIndex"] = txt_index
    return form


def _calendar_date(value: str, name: str) -> date:
    _ascii_digits(value, name, lengths=frozenset({8}))
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError as exc:
        raise KorailProtocolError(f"{name} must be a valid calendar date") from exc


def _validate_maas_service_detail_query_values(
    start_date: str | None,
    end_date: str | None,
) -> None:
    if start_date is None or end_date is None:
        if start_date is not None or end_date is not None:
            raise KorailProtocolError("MaaS history requires both dates or neither")
        return
    start = _calendar_date(start_date, "start_date")
    end = _calendar_date(end_date, "end_date")
    if end < start:
        raise KorailProtocolError("end_date must not be before start_date")


@dataclass(frozen=True)
class MaasServiceDetailQuery:
    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self) -> None:
        _validate_maas_service_detail_query_values(
            self.start_date,
            self.end_date,
        )

    @classmethod
    def current(cls) -> MaasServiceDetailQuery:
        return cls()

    @classmethod
    def history(
        cls,
        start_date: str,
        end_date: str,
    ) -> MaasServiceDetailQuery:
        return cls(start_date=start_date, end_date=end_date)


def build_multi_child_discount_target_form(
    departure_date: str,
) -> dict[str, str]:
    # 위 :func:`build_trip_change_date_form` 과 같은 이유로 달력 검증입니다.
    return {
        "dptDt": _calendar_date(departure_date, "departure_date").strftime("%Y%m%d")
    }


def build_korail_point_summary_form() -> dict[str, str]:
    """``xPoint.MyXPointView`` 의 고정 폼 (``NetworkApi.java:515``).

    ``point_dv_cd`` 를 ``"0"`` 으로 고정하는 7.0.6 근거는 찾지 못했습니다 (**미출처**). 값 자체는 라이브로 동작합니다."""
    return {"point_dv_cd": "0"}


#: ``"1"`` KTX 마일리지, ``"2"`` 철도포인트.
KorailMileageLedger = Literal["1", "2"]

#: ``"0"`` 전체, ``"1"`` 적립, ``"2"`` 사용.
KorailMileageMovement = Literal["0", "1", "2"]

#: 두 값 모두 라이브로는 동작하지만 7.0.6 출처가 없는 **미출처** 상수입니다.
KORAIL_MILEAGE_LEDGER_KTX: KorailMileageLedger = "1"
KORAIL_MILEAGE_LEDGER_RAIL_POINT: KorailMileageLedger = "2"

#: 위와 같이 **미출처**입니다.
KORAIL_MILEAGE_MOVEMENT_ALL: KorailMileageMovement = "0"
KORAIL_MILEAGE_MOVEMENT_EARNED: KorailMileageMovement = "1"
KORAIL_MILEAGE_MOVEMENT_SPENT: KorailMileageMovement = "2"

_KORAIL_MILEAGE_LEDGERS = frozenset(
    {KORAIL_MILEAGE_LEDGER_KTX, KORAIL_MILEAGE_LEDGER_RAIL_POINT}
)
_KORAIL_MILEAGE_MOVEMENTS = frozenset(
    {
        KORAIL_MILEAGE_MOVEMENT_ALL,
        KORAIL_MILEAGE_MOVEMENT_EARNED,
        KORAIL_MILEAGE_MOVEMENT_SPENT,
    }
)


@dataclass(frozen=True)
class MileageHistoryRequest:
    """마일리지 내역 조회 입력 (``mlg.amtSpec.do``, ``NetworkApi.java:274``).

    기본값: KTX 마일리지 원장, 전체 증감, 페이지 1. ``start_date``/``end_date`` 는 호출자가 반드시 제공해야 합니다."""

    start_date: str
    end_date: str
    ledger: KorailMileageLedger = KORAIL_MILEAGE_LEDGER_KTX
    movement: KorailMileageMovement = KORAIL_MILEAGE_MOVEMENT_ALL
    page_no: int = 1


def build_mileage_history_form(
    request: MileageHistoryRequest,
) -> dict[str, str]:
    if request.ledger not in _KORAIL_MILEAGE_LEDGERS:
        raise KorailProtocolError(
            "ledger must be KORAIL_MILEAGE_LEDGER_KTX or "
            "KORAIL_MILEAGE_LEDGER_RAIL_POINT"
        )
    if request.movement not in _KORAIL_MILEAGE_MOVEMENTS:
        raise KorailProtocolError(
            "movement must be one of KORAIL_MILEAGE_MOVEMENT_ALL, "
            "KORAIL_MILEAGE_MOVEMENT_EARNED, KORAIL_MILEAGE_MOVEMENT_SPENT"
        )
    start_date = _ascii_digits(request.start_date, "start_date", lengths=frozenset({8}))
    end_date = _ascii_digits(request.end_date, "end_date", lengths=frozenset({8}))
    if start_date > end_date:
        raise KorailProtocolError("start_date must not be after end_date")
    return {
        "pontTpVal": request.ledger,
        "qryDvVal": request.movement,
        "qryStDt": start_date,
        "qryClsDt": end_date,
        # 매 호출 같은 리터럴입니다(7.0.6 출처 없음, 미출처).
        "pgPrCnt": "20",
        "nowPgNo": _int_text(request.page_no, "page_no"),
    }


def build_discount_card_usage_query(card_no: str) -> dict[str, str]:
    """``ticket.dcntCrdUseQry.do`` — ``NetworkApi.java:218``."""
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


@dataclass(frozen=True)
class DiscountCardScheduleRequest:
    """할인카드 운행일정 입력(NetworkApi.java:340, NCardScheduleIn.java:30-40). 앱 생성자:
    CheckUsageNCardSectionViewModel.java:390-396. dptTm·dirtChtnDvCd· TrainGroup.KTX 의 값은 보호돼 기본값 000000/1/109 의
    평문 근거가 아닙니다(TrainGroup.java:36,48). 2026-09-21 관측: usable_trip_count="" 는 WRR000100(usePsbTno)으로 거절됐습니다. 올바른
    기본값은 미확인이라 호출자가 실제 카드의 값을 제공해야 합니다."""

    card_kind_management_no: str
    departure_station_name: str
    arrival_station_name: str
    departure_date: str
    card_kind_code: str = "MMM"
    usable_trip_count: str = ""
    usage_period_days: str | None = None
    page_no: str | None = None
    departure_time: str = "000000"
    train_group_code: str = "109"
    direct_transfer_division_code: str = "1"

    @classmethod
    def for_card(
        cls,
        card_kind_management_no: str,
        *,
        departure_station_name: str,
        arrival_station_name: str,
        departure_date: str,
        usable_trip_count: str = "",
        usage_period_days: str | None = None,
        page_no: str | None = None,
    ) -> DiscountCardScheduleRequest:
        """카드 종류에서 dcntCrdKndCd 를 유도합니다. 앱 대응 함수는 NCardDefine.findDcntCrdKndCd(NCardDefine.java:58-88)이며
        그 함수가 특별 취급하는 관리번호 집합은 이 구현과 다릅니다(_B2N_CARD_KIND_MANAGEMENT_NOS 참고)."""
        kind_code = (
            "B2N"
            if card_kind_management_no in _B2N_CARD_KIND_MANAGEMENT_NOS
            else "MMM"
        )
        return cls(
            card_kind_management_no=card_kind_management_no,
            departure_station_name=departure_station_name,
            arrival_station_name=arrival_station_name,
            departure_date=departure_date,
            card_kind_code=kind_code,
            usable_trip_count=usable_trip_count,
            usage_period_days=usage_period_days,
            page_no=page_no,
        )


#: 라이브러리 B2N 상품 집합으로 앱과의 일치는 미확인입니다. NCardDefine.java:56-88 은 jadx 복원 실패이며 NCardDefine.smali:689,1180-1225 에 분기와
#: 보호된 반환값이 있습니다. B2N19060502/03·B2N19061002/03 은 NCardDefine.java:14-17 에 선언돼 있으나 아래 B2N18120402/03 과 다릅니다. 보호된
#: 반환 평문은 복원하지 않았고 카드 미보유 응답 EAZ000028 로는 집합의 정합성을 검증할 수 없습니다. 값은 근거 없이 바꾸지 않습니다.
_B2N_CARD_KIND_MANAGEMENT_NOS = frozenset({"B2N18120402", "B2N18120403"})


def build_discount_card_schedule_query(
    request: DiscountCardScheduleRequest,
) -> dict[str, str]:
    """useTrmDno·qryPgNo 가 None 이면 폼에서 생략합니다. 앱은 DTO→KJson→FieldMap 경로입니다(NetworkApi.java:339-341,
    NetworkService.java:2387-2393). 생성자가 값을 넘긴다는 사실(CheckUsageNCardSectionViewModel.java:396)만으로 실제 전송 키가 항상
    존재한다고 단정할 수 없습니다. 빈 값은 후속 평탄화에서 제거될 수 있고 encodeDefaults·전송 키의 보호 리터럴도 미확인입니다. 카드 없는 계정은 EAZ000028 로 중단돼 이
    차이를 라이브 검증하지 못했습니다."""
    query = {
        "dptDt": _ascii_digits(request.departure_date, "departure_date", lengths=frozenset({8})),
        "dptRsStnNm": _required_text(
            request.departure_station_name,
            "departure_station_name",
        ),
        "arvRsStnNm": _required_text(
            request.arrival_station_name,
            "arrival_station_name",
        ),
        "dptTm": _ascii_digits(request.departure_time, "departure_time", lengths=frozenset({6})),
        "trnGpCd": _required_text(
            request.train_group_code,
            "train_group_code",
        ),
        "dirtChtnDvCd": _required_text(
            request.direct_transfer_division_code,
            "direct_transfer_division_code",
        ),
        "dcntCrdKndCd": _required_text(
            request.card_kind_code,
            "card_kind_code",
        ),
        "dcntCrdKndMgNo": _required_text(
            request.card_kind_management_no,
            "card_kind_management_no",
        ),
        "usePsbTno": _optional_text(
            request.usable_trip_count,
            "usable_trip_count",
        ),
    }
    if request.usage_period_days is not None:
        query["useTrmDno"] = _required_text(
            request.usage_period_days,
            "usage_period_days",
        )
    if request.page_no is not None:
        query["qryPgNo"] = _required_text(request.page_no, "page_no")
    return query


def build_customer_trip_info_form(customer_no: str) -> dict[str, str]:
    return {
        "custMgNo": _required_text(customer_no, "customer_no"),
        "medDvCd": "03",
        "regSqno": "0",
    }


def build_maas_service_detail_form(
    config: KorailConfig,
    query: MaasServiceDetailQuery,
) -> dict[str, str]:
    form = _device_version(config)
    # 두 날짜의 동시 지정은 __post_init__ 에서 검사합니다.
    if query.start_date is not None and query.end_date is not None:
        form["qryDtFrom"] = query.start_date
        form["qryDtTo"] = query.end_date
    return form


def build_trip_change_date_form(departure_date: str) -> dict[str, str]:
    # 달력 검증은 앱에 없는 라이브러리 검사입니다(앱은 날짜 선택기 값만 보냅니다). 2026-09-24 라이브: 20260230·20261340 은
    # SUCC/API.I00000 에 tripChgDates 없이 돌아왔고, 정상 날짜는 변경 가능일이 없어도 빈 tripChgDates 를 실었습니다(20250101·20991231 등).
    # 로컬에서 막지 않으면 잘못 쓴 날짜가 성공 봉투로 돌아옵니다.
    return {
        "tripChgDate": _calendar_date(
            departure_date, "departure_date"
        ).strftime("%Y%m%d")
    }


def _exact_server_pass_data(pass_data: PassMenuData) -> str:
    if not isinstance(pass_data, PassMenuData):
        raise KorailProtocolError("pass_data must be a PassMenuData")
    return _required_text(
        pass_data.commuter_kind_code,
        "pass_data.commuter_kind_code",
    )


@dataclass(frozen=True)
class CommuterInitialRequest:
    pass_data: PassMenuData

    def __post_init__(self) -> None:
        _exact_server_pass_data(self.pass_data)


@dataclass(frozen=True, init=False)
class CommuterPassengerRequest:
    pass_data: PassMenuData
    source: CommuterInfoResponse
    passenger_counts: tuple[int, ...]

    @classmethod
    def from_response(
        cls,
        pass_data: PassMenuData,
        source: CommuterInfoResponse,
        passenger_counts: tuple[int, ...],
    ) -> CommuterPassengerRequest:
        instance = object.__new__(cls)
        object.__setattr__(instance, "pass_data", pass_data)
        object.__setattr__(instance, "source", source)
        object.__setattr__(instance, "passenger_counts", passenger_counts)
        _validate_commuter_passenger_request(instance)
        return instance


def _validate_commuter_passenger_request(
    request: CommuterPassengerRequest,
) -> tuple[str, ...]:
    _exact_server_pass_data(request.pass_data)
    if not isinstance(request.source, CommuterInfoResponse):
        raise KorailProtocolError("source must be a CommuterInfoResponse")
    if type(request.passenger_counts) is not tuple:
        raise KorailProtocolError("passenger_counts must be a tuple")
    age_codes = tuple(
        option.commuter_usage_age_code
        for option in request.source.passenger_options
    )
    if not age_codes or len(age_codes) != len(request.passenger_counts):
        raise KorailProtocolError(
            "passenger counts must match the response age-code rows"
        )
    validated_age_codes: list[str] = []
    for option, age_code in zip(
        request.source.passenger_options,
        age_codes,
        strict=True,
    ):
        if not isinstance(option, CommuterPassengerOption):
            raise KorailProtocolError("response passenger options must be CommuterPassengerOption")
        validated_age_codes.append(
            _required_text(age_code, "commuter_usage_age_code")
        )
    for count in request.passenger_counts:
        if type(count) is not int or count < 0:
            raise KorailProtocolError(
                "passenger counts must be non-negative integers"
            )
    return tuple(validated_age_codes)


@dataclass(frozen=True)
class OriginalTicketReference:
    """원표 식별자. sale_date 형식은 라우트별로 다르므로 같은 객체를 무조건 재사용하지 마십시오.

    2026-09-22 관측 기록(승차권 128장): 환불 수수료·환불 상세·원표 조회·역 환불 return_no_2 는 return_sale_date(MMDD)를 사용합니다. YYYYMMDD 를
    넣으면 각각 WRT200408·ERZ800027·ERZ800027·WRT100124 를 관측했습니다. WRT100124 는 자릿수 전용 코드가 아니며 6자리에도 관측됐습니다. 수령자 후보 조회
    saleDt 와 대리수령 tkRetNo 는 sale_date(YYYYMMDD)를 사용하며 MMDD 를 넣으면 ERB000001 을 관측했습니다. 이 기록을 다른 조건의 성공 보장으로 해석하지
    마십시오."""

    sale_window_no: str
    sale_date: str
    sale_sequence: str
    return_password: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.sale_window_no, "sale_window_no"),
            (self.sale_date, "sale_date"),
            (self.sale_sequence, "sale_sequence"),
            (self.return_password, "return_password"),
        ):
            _required_text(value, name)


def _exact_original_ticket_reference(
    reference: OriginalTicketReference,
) -> OriginalTicketReference:
    if not isinstance(reference, OriginalTicketReference):
        raise KorailProtocolError(
            "ticket must be an OriginalTicketReference"
        )
    return reference


def _ticket_return_number(reference: OriginalTicketReference) -> str:
    ticket = _exact_original_ticket_reference(reference)
    return "-".join(
        (
            ticket.sale_window_no,
            ticket.sale_date,
            ticket.sale_sequence,
            ticket.return_password,
        )
    )


def _exact_ticket_reference_tuple(
    tickets: tuple[OriginalTicketReference, ...],
) -> tuple[OriginalTicketReference, ...]:
    if type(tickets) is not tuple:
        raise KorailProtocolError("tickets must be an exact tuple")
    if not tickets:
        raise KorailProtocolError("tickets must contain at least one reference")
    for ticket in tickets:
        _exact_original_ticket_reference(ticket)
    return tickets


@dataclass(frozen=True)
class TicketDuplicationCheckRequest:
    pnr_no: str

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


def build_delivery_recipient_form(
    ticket: OriginalTicketReference,
) -> dict[str, str]:
    reference = _exact_original_ticket_reference(ticket)
    return {
        "saleWctNo": reference.sale_window_no,
        "saleDt": reference.sale_date,
        "saleSqno": reference.sale_sequence,
        "tkRetPwd": reference.return_password,
    }


def build_ticket_duplication_check_form(
    request: TicketDuplicationCheckRequest,
) -> dict[str, str]:
    if not isinstance(request, TicketDuplicationCheckRequest):
        raise KorailProtocolError(
            "request must be a TicketDuplicationCheckRequest"
        )
    return {"pnrNo": request.pnr_no}


def build_pbp_acceptance_specification_form(
    tickets: tuple[OriginalTicketReference, ...],
) -> tuple[tuple[str, str | int], ...]:
    references = _exact_ticket_reference_tuple(tickets)
    return (
        ("tkCnt", len(references)),
        *(("tkRetNo", _ticket_return_number(ticket)) for ticket in references),
    )


def build_original_ticket_inquiry_form(
    tickets: tuple[OriginalTicketReference, ...],
    *,
    ticket_count: int | None = None,
) -> tuple[tuple[str, str | int], ...]:
    """원표 조회(NetworkApi.java:235). 키 접두사·순서: ChangeOrtkInfo.java:52. 건수 tkCnt 는 OgTicketInquiryIn.java:30,81 의 정수이며
    이 빌더는 목록 길이를 사용합니다. 앱의 행 수 사용: NotificationViewModel.java:197, PassengerTypeChangeViewModel.java:147,
    TrainSeatMapViewModel.java:1282. RefundTicketViewModel.java:258 의 리터럴은 보호돼 있습니다."""
    references = _exact_ticket_reference_tuple(tickets)
    if ticket_count is None:
        count = len(references)
    elif type(ticket_count) is not int or ticket_count < 1:
        raise KorailProtocolError("ticket_count must be a positive integer")
    else:
        count = ticket_count
    # 2026-09-22 라이브: ticket_count 를 len(tickets) 보다 작게 보내면 앞의 해당 개수만 조회됐습니다. 전부 조회하려면 ticket_count 를 생략하거나
    # len(tickets) 로 주십시오. 앱 호출별 값이 달라 길이 일치를 강제하지는 않습니다.
    rows: list[tuple[str, str | int]] = [("tkCnt", count)]
    for index, ticket in enumerate(references, start=1):
        rows.append((f"ogtkSaleWctNo_{index}", ticket.sale_window_no))
        rows.append((f"ogtkSaleDd_{index}", ticket.sale_date))
        rows.append((f"ogtkSaleSqno_{index}", ticket.sale_sequence))
        rows.append((f"ogtkRetPwd_{index}", ticket.return_password))
    return tuple(rows)


#: ``"1"`` 일반실, ``"2"`` 특실(라이브 기록에 따른 값; PsrmType.java:19-29 의 리터럴은 보호됨), ``None`` 은 필드 생략.
KorailSelfSeatChangeRoomClassCode = Literal["1", "2"]


@dataclass(frozen=True)
class SelfSeatChangeInfoRequest:
    """자율 좌석변경 입력(NetworkApi.java:806-808, SeatAvailabilityIn.java:26-30,55). 5개 자체 필드의 전송 키는 속성명에 따른 추정입니다. 앱은
    승차권의 식별자를 복사하고 객실 값이 null 이 아닐 때 요청합니다(SelfSeatChangeOptionViewModel.java:342-344). 여기서 room_class_code=None
    이면 생략하는 것은 앱과 다른 라이브러리 정책입니다."""

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    room_class_code: KorailSelfSeatChangeRoomClassCode | None = None

    def __post_init__(self) -> None:
        _ascii_digits(self.run_date, "run_date", lengths=frozenset({8}))
        _ascii_digits(self.train_no, "train_no", maximum_length=5)
        _required_text(
            self.departure_station_code,
            "departure_station_code",
        )
        _required_text(self.arrival_station_code, "arrival_station_code")
        # 객실 코드는 허용목록으로 거르지 않습니다: 앱 DTO 는 String 이고 코드 리터럴은 보호돼 있습니다(PsrmType.java:19-29).
        if self.room_class_code is not None:
            _required_text(self.room_class_code, "room_class_code")


def build_self_seat_change_info_form(
    request: SelfSeatChangeInfoRequest,
) -> dict[str, str]:
    form = {
        "runDt": request.run_date,
        "trnNo": request.train_no,
        "dptRsStnCd": request.departure_station_code,
        "arvRsStnCd": request.arrival_station_code,
    }
    if request.room_class_code is not None:
        form["psrmClCd"] = request.room_class_code
    return form


def build_recent_delivery_history_form(customer_no: str) -> dict[str, str]:
    return {"custMgNo": _required_text(customer_no, "customer_no")}


@dataclass(frozen=True)
class CommuterTicketInquiryRequest:
    original_ticket: OriginalTicketReference
    inquiry_type: str = "0"

    def __post_init__(self) -> None:
        if self.inquiry_type not in {"0", "1"}:
            raise KorailProtocolError("inquiry_type must be '0' or '1'")
        if not isinstance(self.original_ticket, OriginalTicketReference):
            raise KorailProtocolError(
                "original_ticket must be an OriginalTicketReference"
            )


CommuterInfoRequest = (
    CommuterInitialRequest
    | CommuterPassengerRequest
    | CommuterTicketInquiryRequest
)


def build_commuter_info_form(
    request: CommuterInfoRequest,
) -> tuple[tuple[str, str], ...]:
    if isinstance(request, CommuterInitialRequest):
        return (
            ("jobDvCd", "a"),
            ("cmtrKndCd", request.pass_data.commuter_kind_code),
            ("psgCnt", "0"),
        )
    if isinstance(request, CommuterPassengerRequest):
        age_codes = tuple(
            option.commuter_usage_age_code
            for option in request.source.passenger_options
        )
        # cmtrUtlAgeCd 는 종류 행당이 아니라 승객당 반복합니다(CommutationInfoIn.java:31,38). 2026-09-22 kind=0046 관측: E05/E06 을
        # 행당 한 번 보내면 WRT800115, 인원 1+E05, 1+E06, 2+E05/E05 는 IRZ000008 이었습니다. 2026-09-24: 이 키를 빼면 1명·2명 모두
        # FAIL/ERR000100 이었습니다. 앱의 폼 평탄화(NetworkService.java:15345-15355)는 객체 배열만 펼치는 것으로 읽히지만 서버는 이 키를
        # 요구하므로, 앱이 이 필드를 어떻게 싣는지는 미확인입니다.
        selected = tuple(
            code
            for code, count in zip(
                age_codes,
                request.passenger_counts,
                strict=True,
            )
            for _ in range(count)
        )
        if not selected:
            raise KorailProtocolError(
                "passenger_counts must select at least one passenger"
            )
        return (
            ("jobDvCd", "b"),
            ("cmtrKndCd", request.pass_data.commuter_kind_code),
            ("psgCnt", str(len(selected))),
            *(("cmtrUtlAgeCd", value) for value in selected),
        )
    if isinstance(request, CommuterTicketInquiryRequest):
        ticket = request.original_ticket
        return (
            ("jobDvCd", "c"),
            ("psgCnt", "0"),
            ("ogtkSaleWctNo", ticket.sale_window_no),
            ("ogtkSaleDd", ticket.sale_date),
            ("ogtkSaleSqno", ticket.sale_sequence),
            ("ogtkRetPwd", ticket.return_password),
            ("inquiryType", request.inquiry_type),
        )
    raise KorailProtocolError("request must be a commuter request variant")


def _wire_component(value: str, name: str) -> str:
    resolved = _required_text(value, name)
    if "," in resolved:
        raise KorailProtocolError(f"{name} must not contain a comma")
    return resolved


@dataclass(frozen=True)
class PriceFareLeg:
    """운임 구간. goods_no=None 이면 gdNo 를 생략합니다. 앱의 일반 열차 생성자는 기본값 마스크 64 를 사용합니다(TrainOpInfoViewModel.java:794,
    PrcFareInItem.java:85). 보호된 기본값·직렬화 때문에 이것만으로 실제 폼 생략은 확정하지 않습니다. 2026-09-21 관측에서는 gdNo 유무에 따른 응답 차이가 없었습니다."""

    departure_station_code: str
    arrival_station_code: str
    run_date: str
    train_no: str
    requested_seat_attribute_code: str
    train_group_code: str
    #: stlbTrnClsfCd 는 정산용 열차 종류이지 입석 코드가 아닙니다. 호출자는 열차 행의 train_class_code 를 그대로 옮기십시오. 다른 대응은
    #: limousine_parsers·parsers·read_parsers 의 stlbTrnClsfCd 매핑 참고.
    train_class_code: str
    goods_no: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.departure_station_code, "departure_station_code"),
            (self.arrival_station_code, "arrival_station_code"),
            (self.run_date, "run_date"),
            (self.train_no, "train_no"),
            (self.requested_seat_attribute_code, "requested_seat_attribute_code"),
            (self.train_group_code, "train_group_code"),
            (self.train_class_code, "train_class_code"),
        ):
            _wire_component(value, name)
        if self.goods_no is not None:
            _wire_component(self.goods_no, "goods_no")


@dataclass(frozen=True)
class PriceFareQuoteRequest:
    """운임 조회의 한두 구간과 메뉴. DTO: PrcFareIn.java:28-31,197. 생성자 TrainOpInfoViewModel.java:794 의 메뉴 리터럴은 보호됨. 길이 2가 기본값
    11 을 증명하지 않습니다."""

    legs: tuple[PriceFareLeg, ...]
    menu_id: str = "11"

    def __post_init__(self) -> None:
        _wire_component(self.menu_id, "menu_id")
        if type(self.legs) is not tuple or len(self.legs) not in {1, 2}:
            raise KorailProtocolError("legs must be a tuple containing one or two legs")
        for leg in self.legs:
            if not isinstance(leg, PriceFareLeg):
                raise KorailProtocolError("legs must contain PriceFareLeg values")


def build_price_fare_quote_form(
    request: PriceFareQuoteRequest,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(request, PriceFareQuoteRequest):
        raise KorailProtocolError("request must be a PriceFareQuoteRequest")
    columns = [
        ("dptRsStnCd", "departure_station_code"),
        ("arvRsStnCd", "arrival_station_code"),
        ("runDt", "run_date"),
        ("trnNo", "train_no"),
        ("rqSeatAttCd", "requested_seat_attribute_code"),
        ("trnGpCd", "train_group_code"),
        ("stlbTrnClsfCd", "train_class_code"),
    ]
    # 상품번호가 있는 구간만 보내는 혼합 입력은 지원하지 않습니다. 쉼표 결합 시 빈 구간의 자리 표현이 관측되지 않아 임의 생성하지 않습니다. 앱 입력 null:
    # TrainOpInfoViewModel.java:794.
    supplied = [leg.goods_no is not None for leg in request.legs]
    if any(supplied):
        if not all(supplied):
            raise KorailProtocolError(
                "goods_no must be set on every leg or on none of them"
            )
        columns.insert(4, ("gdNo", "goods_no"))
    return (
        ("txtMenuId", request.menu_id),
        ("chtnDvCd", str(len(request.legs))),
        ("trnCnt", str(len(request.legs))),
        *(
            (
                wire_name,
                ",".join(getattr(leg, attribute) for leg in request.legs),
            )
            for wire_name, attribute in columns
        ),
    )


@dataclass(frozen=True)
class TicketReservationDetailRequest:
    """PNR 로 예약 상세를 조회합니다(NetworkApi.java:422-424,626-628). DTO 는 PNR 외 할인승객 목록도 선언하나 이 빌더는 PNR 만 보냅니다
    (ReservationListIn.java:29-32,58). hidPnrNo 전송 키는 속성명에 따른 추정입니다."""

    pnr_no: str

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


def build_ticket_reservation_detail_query(
    request: TicketReservationDetailRequest,
) -> dict[str, str]:
    """``hidPnrNo`` 하나 — ``ReservationListIn.java:30``."""
    if not isinstance(request, TicketReservationDetailRequest):
        raise KorailProtocolError(
            "request must be a TicketReservationDetailRequest"
        )
    return {"hidPnrNo": request.pnr_no}


@dataclass(frozen=True)
class RefundCompanion:
    """환불 수수료 조회의 동반자 이름·생년월일(RefundCommissionIn.java:34-35,59). 앱 호출자는 compaNm/compaBrth 를
    전달합니다(MyTicketDetailViewModel.java:277, FTicketDetailViewModel.java:179). 빌더의 빈 문자열은 HTTP 단계에서 제거되므로 빈 값을
    반드시 전송한다고 보장하지 않습니다."""

    name: str = ""
    certificate_no: str = ""

    def __post_init__(self) -> None:
        _optional_text(self.name, "name")
        _optional_text(self.certificate_no, "certificate_no")


def _exact_refund_companion(companion: RefundCompanion) -> RefundCompanion:
    if not isinstance(companion, RefundCompanion):
        raise KorailProtocolError("companion must be a RefundCompanion")
    return companion


def build_station_refund_verification_form(
    request: StationRefundVerificationRequest,
) -> dict[str, str]:
    """NetworkApi.verifyOnlineRefunds 의 VerifyOnlineRefundsIn 폼. 요청 객체가 값을 검사하며 공통 필드는 KorailHttpClient 가 추가합니다."""
    return {
        "strName": request.customer_name,
        "retNo1": request.return_no_1,
        "retNo2": request.return_no_2,
        "retNo3": request.return_no_3,
        "retNo4": request.return_no_4,
    }


def build_refund_commission_form(
    ticket: OriginalTicketReference,
    companion: RefundCompanion = RefundCompanion(),
) -> dict[str, str]:
    """환불 수수료 사전조회(NetworkApi.java:598-600, RefundCommissionIn.java:32-42,59). 판매일 키 h_orgtk_ret_sale_dt 는 환불 실행의
    h_orgtk_sale_dt 와 다릅니다(RefundTicketIn.java:38)."""
    reference = _exact_original_ticket_reference(ticket)
    party = _exact_refund_companion(companion)
    return {
        "h_orgtk_ret_sale_dt": reference.sale_date,
        "h_orgtk_wct_no": reference.sale_window_no,
        "h_orgtk_sale_sqno": reference.sale_sequence,
        "h_orgtk_ret_pwd": reference.return_password,
        "h_comp_nm": party.name,
        "h_comp_cert_no": party.certificate_no,
    }


def build_refund_ticket_detail_form(
    ticket: OriginalTicketReference,
    *,
    from_purchase_history: bool = False,
    txt_index: str | None = None,
) -> dict[str, str]:
    """환불 상세(NetworkApi.java:406-408). 여섯 키는 TicketDetailIn.java:57 의 @SerialName 입니다. h_purchase_history 는 앱에서
    불리언에 따라 선택하지만 리터럴은 보호돼 있습니다 (MyTicketBaseViewModel.java:696). Y/N 배정은 라이브 기록에 의존합니다."""
    reference = _exact_original_ticket_reference(ticket)
    if type(from_purchase_history) is not bool:
        raise KorailProtocolError("from_purchase_history must be a bool")
    form = {
        "h_orgtk_ret_sale_dt": reference.sale_date,
        "h_orgtk_wct_no": reference.sale_window_no,
        "h_orgtk_sale_sqno": reference.sale_sequence,
        "h_orgtk_ret_pwd": reference.return_password,
        "h_purchase_history": "Y" if from_purchase_history else "N",
    }
    if txt_index is not None:
        form["txtIndex"] = _required_text(txt_index, "txt_index")
    return form
