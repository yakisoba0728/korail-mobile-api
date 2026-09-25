# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""조회 폼도 DTO 선언 순서를 따르며 보호된 입력 코드는 서버 메타데이터 또는 명시값을 사용합니다."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal
from typing import cast as _cast

from ._payload_helpers import _device_version, _is_ascii_digits
from .config import KorailConfig
from .errors import KorailProtocolError
from .payloads import build_cache_query
from .read_models import (
    CartItem,
    CommuterInfoResponse,
    MaasServiceDetail,
    PassMenuData,
    RefundTicketDetailResponse,
)

if TYPE_CHECKING:
    from .mutation_models import StationRefundVerificationRequest


def _int_text(value: int, name: str) -> str:
    """앱 DTO 는 String 이고 범위 검사가 없어 값의 판정은 서버에 맡깁니다 (CouponIn.java:29-30, ProductListIn.java:30-35,
    AmtSpecIn.java:30-36)."""
    if type(value) is not int:
        raise KorailProtocolError(f"{name} must be an integer")
    return str(value)


def _required_text(value: str | None, name: str) -> str:
    """``value`` 를 그대로 돌려주되 없거나 빈 문자열이면 거부합니다. 호출자 대부분이 서버 응답에서 파싱한 선택 필드를 그대로 넘기므로, ``None`` 도 인자로 받아
    ``errors.KorailProtocolError`` 로 거절합니다."""
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
    """ASCII 숫자 형식을 검사하고 요청별 오류를 발생시킵니다. lengths 는 허용 길이 집합, maximum_length 는 상한입니다. 둘 다 없으면 길이를 제한하지 않고
    allow_empty=True 이면 빈 문자열도 허용합니다."""
    if allow_empty and value == "":
        return value
    if lengths is not None:
        if not _is_ascii_digits(value, lengths):
            if len(lengths) == 1:
                (length,) = lengths
                raise KorailProtocolError(f"{name} must contain exactly {length} ASCII digits")
            expected = ", ".join(str(length) for length in sorted(lengths))
            raise KorailProtocolError(f"{name} must contain {expected} ASCII digit(s)")
        return value
    if (
        not isinstance(value, str)
        or not value
        or any(character < "0" or character > "9" for character in value)
        or (maximum_length is not None and len(value) > maximum_length)
    ):
        suffix = f" with at most {maximum_length} digits" if maximum_length is not None else ""
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
    """앱은 SeatType.HELPER 코드를 사용합니다(TrainOptionViewModel.java:270). 이 표본만으로 모든 입력·시점의 응답이 같다고 보장하지 않습니다."""

    seat_attribute_code: str


@dataclass(frozen=True)
class SeatAssignmentScheduleRequest:
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
    # seatAttCdN/psgNumN/stlbDturDvNmN 은 승객별 번호 그룹이고 psgNumN 은 인원수가 아니라 그 자리의 점유 플래그(0/1)입니다.
    for slot in range(1, request.passenger_count + 1):
        form[f"seatAttCd{slot}"] = request.seat_attribute_code
        form[f"psgNum{slot}"] = "1"
        form[f"stlbDturDvNm{slot}"] = request.standing_detour_division_name
    return form


def build_merge_seats_inquiry_form(
    request: MergeSeatsInquiryRequest,
) -> dict[str, str]:
    # 키 순서는 MergeSeatsCIn 합성 생성자(MergeSeatsCIn.java:63)의 선언 순서입니다.
    form = {
        "abrdDt": request.boarding_datetime,
        "runDt": request.run_datetime,
        "trnNo": request.train_no.zfill(5),
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
    }
    if request.selected_station_name is not None:
        form["selRsStnNm"] = request.selected_station_name
    form["psrmClCd"] = request.room_class_code
    form["seatAttCd"] = request.seat_attribute_code
    form["totPsgNum"] = str(request.passenger_count)
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
    #: txtSelPage: 관측에서 요청값을 바꿔도 h_page_no=1 이었습니다. 앱의 해당 인자도 고정이지만 평문은 보호돼
    #: 있습니다(CheckUsagePeriodSectionViewModel.java:389). page_size 로 요청 건수를 정하며 페이징 신호의 관측 한계는
    #: PassScheduleMainInfo 참고.
    page_no: str
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
    # dptDtTo 속성의 전송 키는 명시적 h_page_no(DelayDiscountViewIn.java:50,77). 관측: 날짜·1·다른 후보 키·키 생략 모두 같은 빈 SUCC.
    return {"h_page_no": _ascii_digits(departure_date_to, "departure_date_to", lengths=frozenset({8}))}


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
    """sealed CommonIn이 실제 CrewCallCommonIn 직렬화기로 넘기므로 timeStamp를 싣습니다(NetworkService.java:3952-3955;
    CommonIn.java:350)."""
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
        query["txtRsvSttCd"] = _required_text(reservation_status_code, "reservation_status_code")
    if payment_status_code is not None:
        query["txtStlSttCd"] = _required_text(payment_status_code, "payment_status_code")
    return query


def build_product_detail_query(
    reservation_no: str,
    reservation_sequence: str | None = None,
) -> dict[str, str]:
    query = {
        "txtVrRsNo": _required_text(reservation_no, "reservation_no"),
    }
    if reservation_sequence is not None:
        query["txtVrRsvSqNo"] = _required_text(reservation_sequence, "reservation_sequence")
    return query


def build_ticket_receipt_form(
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
    txt_index: str | None = None,
) -> dict[str, str]:
    form = {
        # 여기서 막지 않으면 TicketListTicket.sale_date 를 그대로 넘긴 호출자가 원인이 모호한 서버 오류를 받습니다.
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
    # 앱은 두 날짜를 따로 nullable 로 넘깁니다(MaasDetailIn.java:65-68, MyTicketBaseViewModel$executeMaasList$1.java:117).
    # 짝·순서는 검사하지 않고, 주어진 값의 YYYYMMDD 형식만 봅니다.
    for value, name in ((start_date, "start_date"), (end_date, "end_date")):
        if value is not None:
            _ascii_digits(value, name, lengths=frozenset({8}))


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
    return {"dptDt": _calendar_date(departure_date, "departure_date").strftime("%Y%m%d")}


def build_korail_point_summary_form() -> dict[str, str]:
    """앱 근거: NetworkApi.java:515."""
    return {"point_dv_cd": "0"}


KorailMileageLedger = Literal["1", "2"]

KorailMileageMovement = Literal["0", "1", "2"]

#: 두 값 모두 라이브로는 동작하지만 7.0.6 출처가 없는 **미출처** 상수입니다.
KORAIL_MILEAGE_LEDGER_KTX: KorailMileageLedger = "1"
KORAIL_MILEAGE_LEDGER_RAIL_POINT: KorailMileageLedger = "2"

KORAIL_MILEAGE_MOVEMENT_ALL: KorailMileageMovement = "0"
KORAIL_MILEAGE_MOVEMENT_EARNED: KorailMileageMovement = "1"
KORAIL_MILEAGE_MOVEMENT_SPENT: KorailMileageMovement = "2"

_KORAIL_MILEAGE_LEDGERS = frozenset({KORAIL_MILEAGE_LEDGER_KTX, KORAIL_MILEAGE_LEDGER_RAIL_POINT})
_KORAIL_MILEAGE_MOVEMENTS = frozenset(
    {
        KORAIL_MILEAGE_MOVEMENT_ALL,
        KORAIL_MILEAGE_MOVEMENT_EARNED,
        KORAIL_MILEAGE_MOVEMENT_SPENT,
    }
)


@dataclass(frozen=True)
class MileageHistoryRequest:
    """앱 근거: NetworkApi.java:274. 기본값: KTX 마일리지 원장, 전체 증감, 페이지 1."""

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
            "ledger must be KORAIL_MILEAGE_LEDGER_KTX or KORAIL_MILEAGE_LEDGER_RAIL_POINT"
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
        # 앱은 보호된 상수를 씁니다(MileageHistoryViewModelKt.java:11).
        "pgPrCnt": "20",
        "nowPgNo": _int_text(request.page_no, "page_no"),
    }


def build_discount_card_usage_query(card_no: str) -> dict[str, str]:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. ``ticket.dcntCrdUseQry.do`` — ``NetworkApi.java:218``."""
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


@dataclass(frozen=True)
class DiscountCardScheduleRequest:
    """보호된 기본 코드는 미확인이므로 카드의 실제 usePsbTno를 지정해야 하며 실서버 검증 못 함입니다(NCardScheduleIn.java:30-40)."""

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
        """앱 대응 함수는 NCardDefine.findDcntCrdKndCd(NCardDefine.java:58-88)이며 그 함수가 특별 취급하는 관리번호 집합은 이 구현과
        다릅니다(_B2N_CARD_KIND_MANAGEMENT_NOS 참고)."""
        kind_code = "B2N" if card_kind_management_no in _B2N_CARD_KIND_MANAGEMENT_NOS else "MMM"
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
#: 보호된 반환값이 있습니다.
_B2N_CARD_KIND_MANAGEMENT_NOS = frozenset({"B2N18120402", "B2N18120403"})


def build_discount_card_schedule_query(
    request: DiscountCardScheduleRequest,
) -> dict[str, str]:
    """선택값은 None이면 생략하되 보호된 Json 설정·전송 키와 실서버 검증 못 함은 남습니다(NetworkService.java:2387-2393)."""
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
    # 앱의 두 값은 보호돼 있습니다(HomeViewModel.java:4335).
    return {
        "custMgNo": _required_text(customer_no, "customer_no"),
        "medDvCd": "03",
        "regSqno": "0",
    }


def build_maas_cancel_fee_form(item: MaasServiceDetail) -> dict[str, str]:
    """지원하지 않는 부가서비스 환불 수수료 조회 폼을 구성합니다. MaasCancelFeeIn.java 의 세 속성이며 값은 get_maas_service_details 행에서 옵니다
    (MyTicketDetailViewModel.java:840-860)."""
    if not isinstance(item, MaasServiceDetail):
        raise KorailProtocolError("item must be a MaasServiceDetail from get_maas_service_details")
    return {
        "addSrvReqNo": _required_text(item.request_no, "request_no"),
        "addSrvDvCd": _required_text(item.additional_service_division_code, "additional_service_division_code"),
        "coptEntRsvNo": _required_text(item.partner_reservation_no, "partner_reservation_no"),
    }


def _maas_cart_item(item: CartItem) -> CartItem:
    """앱은 h_pnr_no 가 빈 행을 부가서비스로 다루고(BasketTicketViewModel.java:3080-3160,3757-3780), 열차·공항버스 행은
    cancel_unpaid_hold 로 취소합니다."""
    if not isinstance(item, CartItem):
        raise KorailProtocolError("item must be a CartItem from get_cart_list")
    if item.pnr_no:
        raise KorailProtocolError(
            "KORAIL cart row with a PNR is a train or bus hold; use cancel_unpaid_hold for it"
        )
    return item


def build_maas_cart_status_form(item: CartItem) -> dict[str, str]:
    """지원하지 않는 부가서비스 장바구니 상태 조회 폼을 구성합니다. 앱은 선택한 행들의 값을 보호된 1글자 구분자로 잇는데
    (BasketTicketViewModel.java:1690-1750), 구분자를 모르므로 이 빌더는 한 행만 받습니다. seletedPos 는 전송되지 않습니다(:93)."""
    row = _maas_cart_item(item)
    return {
        "addSrvDvCd": _required_text(row.service_code, "service_code"),
        "addSrvReqNo": _required_text(row.virtual_reservation_no, "virtual_reservation_no"),
        "coptEntRsvNo": _required_text(row.partner_reservation_no, "partner_reservation_no"),
        "lumpStlTgtNo": _required_text(row.lump_sum_target_no, "lump_sum_target_no"),
    }


def build_maas_service_detail_form(
    config: KorailConfig,
    query: MaasServiceDetailQuery,
) -> dict[str, str]:
    form = _device_version(config)
    if query.start_date is not None:
        form["qryDtFrom"] = query.start_date
    if query.end_date is not None:
        form["qryDtTo"] = query.end_date
    return form


def build_trip_change_date_form(departure_date: str) -> dict[str, str]:
    # 달력 검증은 앱에 없는 라이브러리 검사입니다(앱은 날짜 선택기 값만 보냅니다). 라이브: 20260230·20261340 은 SUCC/API.I00000 에 tripChgDates 없이
    # 돌아왔고, 정상 날짜는 변경 가능일이 없어도 빈 tripChgDates 를 실었습니다(20250101·20991231 등).
    return {"tripChgDate": _calendar_date(departure_date, "departure_date").strftime("%Y%m%d")}


def _exact_server_pass_data(pass_data: PassMenuData) -> str:
    """빌더가 쓰는 값은 이것 하나라 객체 출처(PassMenuData 등)는 가리지 않습니다."""
    return _required_text(
        getattr(pass_data, "commuter_kind_code", None),
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
        if isinstance(passenger_counts, (str, bytes)) or not isinstance(passenger_counts, Sequence):
            raise KorailProtocolError("passenger_counts must be a sequence of integers")
        object.__setattr__(instance, "passenger_counts", tuple(passenger_counts))
        _validate_commuter_passenger_request(instance)
        return instance


def _validate_commuter_passenger_request(
    request: CommuterPassengerRequest,
) -> tuple[str, ...]:
    _exact_server_pass_data(request.pass_data)
    # 0명 선택 거절은 빌더에 남습니다.
    options = getattr(request.source, "passenger_options", None)
    if not isinstance(options, Sequence) or isinstance(options, (str, bytes)):
        raise KorailProtocolError("source must carry passenger_options")
    validated_age_codes = [
        _required_text(getattr(option, "commuter_usage_age_code", None), "commuter_usage_age_code")
        for option in options
    ]
    if not validated_age_codes or len(validated_age_codes) != len(request.passenger_counts):
        raise KorailProtocolError("passenger counts must match the response age-code rows")
    for count in request.passenger_counts:
        if type(count) is not int or count < 0:
            raise KorailProtocolError("passenger counts must be non-negative integers")
    return tuple(validated_age_codes)


@dataclass(frozen=True)
class OriginalTicketReference:
    """반환 경로는 MMDD, 수령자·PBP 경로는 YYYYMMDD를 사용하므로 라우트 사이에 날짜를 혼용하지 않습니다(실서버 관측)."""

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
        raise KorailProtocolError("ticket must be an OriginalTicketReference")
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


def _ticket_reference_tuple(
    tickets: Sequence[OriginalTicketReference],
) -> tuple[OriginalTicketReference, ...]:
    if isinstance(tickets, (str, bytes)) or not isinstance(tickets, Sequence):
        raise KorailProtocolError("tickets must be a sequence of OriginalTicketReference")
    if not tickets:
        raise KorailProtocolError("tickets must contain at least one reference")
    for ticket in tickets:
        _exact_original_ticket_reference(ticket)
    return tuple(tickets)


@dataclass(frozen=True)
class TicketDuplicationCheckRequest:
    pnr_no: str

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


def build_delivery_recipient_form(
    ticket: OriginalTicketReference,
) -> dict[str, str]:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
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
        raise KorailProtocolError("request must be a TicketDuplicationCheckRequest")
    return {"pnrNo": request.pnr_no}


def build_pbp_acceptance_specification_form(
    tickets: Sequence[OriginalTicketReference],
) -> tuple[tuple[str, str | int], ...]:
    references = _ticket_reference_tuple(tickets)
    return (
        ("tkCnt", len(references)),
        *(("tkRetNo", _ticket_return_number(ticket)) for ticket in references),
    )


def build_original_ticket_inquiry_form(
    tickets: Sequence[OriginalTicketReference],
    *,
    ticket_count: int | None = None,
) -> tuple[tuple[str, str | int], ...]:
    """앱 근거: NetworkApi.java:235. 키 접두사·순서: ChangeOrtkInfo.java:52. 보호 리터럴은 미확인입니다."""
    references = _ticket_reference_tuple(tickets)
    if ticket_count is None:
        count = len(references)
    elif type(ticket_count) is not int:
        raise KorailProtocolError("ticket_count must be an integer")
    else:
        count = ticket_count
    # 앱 호출별 값이 달라 길이 일치를 강제하지는 않습니다.
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
    """앱 근거: NetworkApi.java:806-808; SeatAvailabilityIn.java:26-30,55. 앱은 승차권의 식별자를 복사하고 객실 값이 null 이 아닐 때
    요청합니다(SelfSeatChangeOptionViewModel.java:342-344)."""

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
    inquiry_type: Literal["0", "1"] = "0"

    def __post_init__(self) -> None:
        if self.inquiry_type not in {"0", "1"}:
            raise KorailProtocolError("inquiry_type must be '0' or '1'")
        if not isinstance(self.original_ticket, OriginalTicketReference):
            raise KorailProtocolError("original_ticket must be an OriginalTicketReference")


CommuterInfoRequest = CommuterInitialRequest | CommuterPassengerRequest | CommuterTicketInquiryRequest


def build_commuter_info_form(
    request: CommuterInfoRequest,
) -> tuple[tuple[str, str], ...]:
    if isinstance(request, CommuterInitialRequest):
        return (
            ("jobDvCd", "a"),
            ("cmtrKndCd", _cast(str, request.pass_data.commuter_kind_code)),
            ("psgCnt", "0"),
        )
    if isinstance(request, CommuterPassengerRequest):
        age_codes = tuple(
            _cast(str, option.commuter_usage_age_code) for option in request.source.passenger_options
        )
        # cmtrUtlAgeCd 는 종류 행당이 아니라 승객당 반복합니다(CommutationInfoIn.java:31,38). kind=0046 관측: E05/E06 을 행당 한 번 보내면
        # WRT800115, 인원 1+E05, 1+E06, 2+E05/E05 는 IRZ000008 이었습니다. : 이 키를 빼면 1명·2명 모두 FAIL/ERR000100 이었습니다.
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
            raise KorailProtocolError("passenger_counts must select at least one passenger")
        return (
            ("jobDvCd", "b"),
            ("cmtrKndCd", _cast(str, request.pass_data.commuter_kind_code)),
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
    """예매 전 운임을 조회할 열차 한 구간을 구성합니다. goods_no=None 이면 앱처럼 gdNo 칸에 빈 문자열을 보냅니다. 앱의 일반 열차 생성자는 기본값 마스크 64 로 gdNo
    기본값을 쓰며(TrainOpInfoViewModel.java:794) 그 값은 길이 0 암호문, 곧 빈 문자열입니다(PrcFareInItem.java:109)."""

    departure_station_code: str
    arrival_station_code: str
    run_date: str
    train_no: str
    requested_seat_attribute_code: str
    train_group_code: str
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
    """DTO: PrcFareIn.java:28-31,197. 생성자 TrainOpInfoViewModel.java:794 의 메뉴 리터럴은 보호됨."""

    legs: tuple[PriceFareLeg, ...]
    menu_id: str = "11"

    def __post_init__(self) -> None:
        _wire_component(self.menu_id, "menu_id")
        # 목록 타입은 가리지 않고 tuple 로 고정합니다.
        if isinstance(self.legs, (str, bytes)) or not isinstance(self.legs, Sequence):
            raise KorailProtocolError("legs must be a sequence of one or two legs")
        object.__setattr__(self, "legs", tuple(self.legs))
        if len(self.legs) not in {1, 2}:
            raise KorailProtocolError("legs must contain one or two legs")
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
        ("gdNo", "goods_no"),
        ("rqSeatAttCd", "requested_seat_attribute_code"),
        ("trnGpCd", "train_group_code"),
        ("stlbTrnClsfCd", "train_class_code"),
    ]
    # 앱은 여덟 칸을 모두 같은 구분자로 이어 보내며 gdNo 도 빠지지 않습니다(NetworkService.java:9838-9905). 앱의 일반 열차 입력은 gdNo 가 null
    # 이라(TrainOpInfoViewModel.java:794) 기본값인 빈 문자열(PrcFareInItem.java:109, 길이 0 암호문)이 들어갑니다.
    supplied = [leg.goods_no is not None for leg in request.legs]
    if any(supplied) and not all(supplied):
        raise KorailProtocolError("goods_no must be set on every leg or on none of them")
    return (
        ("txtMenuId", request.menu_id),
        ("chtnDvCd", str(len(request.legs))),
        ("trnCnt", str(len(request.legs))),
        *(
            (
                wire_name,
                ",".join(getattr(leg, attribute) or "" for leg in request.legs),
            )
            for wire_name, attribute in columns
        ),
    )


@dataclass(frozen=True)
class TicketReservationDetailRequest:
    """TicketRsvInquiryIn.java:51 의 명시적 hidPnrNo 를 보냅니다(NetworkApi.java:422-424). 같은 라우트의 ReservationListIn 은
    할인승객 목록을 받는 별도 입력입니다(NetworkApi.java:626-628)."""

    pnr_no: str

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


def build_ticket_reservation_detail_query(
    request: TicketReservationDetailRequest,
) -> dict[str, str]:
    """전송 키 ``hidPnrNo`` 는 TicketRsvInquiryIn.java:51 에 명시돼 있습니다."""
    if not isinstance(request, TicketReservationDetailRequest):
        raise KorailProtocolError("request must be a TicketReservationDetailRequest")
    return {"hidPnrNo": request.pnr_no}


@dataclass(frozen=True)
class RefundCompanion:
    """앱 근거: RefundCommissionIn.java:34-35,59. 앱 호출자는 compaNm/compaBrth 를
    전달합니다(MyTicketDetailViewModel.java:277, FTicketDetailViewModel.java:179)."""

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
    """앱 근거: NetworkApi.java:598-600; RefundCommissionIn.java:32-42,59. 판매일 키 h_orgtk_ret_sale_dt 는 환불 실행의
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
    """앱 근거: NetworkApi.java:406-408. 여섯 키는 TicketDetailIn.java:57 의 @SerialName 입니다. h_purchase_history 는
    앱에서 불리언에 따라 선택하지만 리터럴은 보호돼 있습니다 (MyTicketBaseViewModel.java:696)."""
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


def build_delay_certificate_form(ticket: OriginalTicketReference) -> dict[str, str]:
    """앱은 승차권 상세의 h_orgtk_wct_no·h_orgtk_ret_sale_dt·h_orgtk_sale_sqno·h_orgtk_ret_pwd 를
    넣습니다(DelayCertificateViewModel.java:94; DelayCertificateIn.java:52). sale_date 에는 return_sale_date 를
    쓰십시오."""
    reference = _exact_original_ticket_reference(ticket)
    return {
        "ogtkSaleWctNo": _required_text(reference.sale_window_no, "sale_window_no"),
        "ogtkSaleDd": _required_text(reference.sale_date, "sale_date"),
        "ogtkSaleSqno": _required_text(reference.sale_sequence, "sale_sequence"),
        "ogtkRetPwd": _required_text(reference.return_password, "return_password"),
    }


def build_delay_return_receipt_form(ticket: OriginalTicketReference) -> dict[str, str]:
    """값의 출처는 지연확인증과 같습니다(DelayReturnReceiptViewModel.java:88; TicketReceiptRouteKt.java:309-313;
    DelayReturnReceiptIn.java:52)."""
    reference = _exact_original_ticket_reference(ticket)
    return {
        "saleWctNo": _required_text(reference.sale_window_no, "sale_window_no"),
        "saleDd": _required_text(reference.sale_date, "sale_date"),
        "saleSqno": _required_text(reference.sale_sequence, "sale_sequence"),
        "tkRetPwd": _required_text(reference.return_password, "return_password"),
    }


# 앱은 검색어를 한 칸에만 넣습니다(TravelSearchViewModel.java:877-904).
_TRAVEL_KEYWORD_KEYS = {"name": "gdNm", "area": "gdTripArNm", "theme": "gdThmNm", "category": "gdCateCdNm"}


@dataclass(frozen=True)
class TravelProductSearchQuery:
    """필수 funcDvCd가 보호돼 공개 클라이언트에서는 사용하지 않는 기록용 입력입니다(TravelSearchProductIn.java:78; 서버 거절 관측)."""

    keyword: str
    keyword_field: Literal["name", "area", "theme", "category"] = "name"
    page_no: int = 1
    function_code: str | None = None
    order_code: str | None = None
    page_size: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.keyword, "keyword")
        if self.keyword_field not in _TRAVEL_KEYWORD_KEYS:
            raise KorailProtocolError("keyword_field must be one of name, area, theme, category")
        _int_text(self.page_no, "page_no")
        for name in ("function_code", "order_code", "page_size"):
            value = getattr(self, name)
            if value is not None:
                _required_text(value, name)


def build_travel_product_search_form(query: TravelProductSearchQuery) -> dict[str, str]:
    """키 순서는 TravelSearchProductIn 합성 생성자(TravelSearchProductIn.java:60-81)의 순서이며 앱이 채우지 않는
    gdNo·qryCnt·mrkWctNo 는 빈 값이라 평탄화에서 빠집니다."""
    if not isinstance(query, TravelProductSearchQuery):
        raise KorailProtocolError("query must be a TravelProductSearchQuery")
    form: dict[str, str] = {}
    if query.function_code is not None:
        form["funcDvCd"] = query.function_code
    form[_TRAVEL_KEYWORD_KEYS[query.keyword_field]] = query.keyword.strip()
    if query.order_code is not None:
        form["bltnLstOrdr"] = query.order_code
    form["nowPgNo"] = _int_text(query.page_no, "page_no")
    if query.page_size is not None:
        form["pgPrCnt"] = query.page_size
    return form


def self_checkin_ticket_fields(
    detail: RefundTicketDetailResponse,
    *,
    sale_date_key: Literal["saleDt", "saleDd"],
) -> dict[str, str]:
    """가능 여부·등록은 saleDd 에 h_orgtk_ret_sale_dt 를, 정보·취소는 saleDt 에 h_sale_dt 를
    넣습니다(SelfCheckInInfoViewModel.java:102-108,224-225; SelfCheckInResultViewModel.java:111-112,249-250).
    jrnySqno 는 첫 여정의 h_jrny_sqno 이며 여정이 없으면 뺍니다."""
    if not isinstance(detail, RefundTicketDetailResponse):
        raise KorailProtocolError("detail must be a RefundTicketDetailResponse from get_refund_ticket_detail")
    sale_date = detail.original_sale_date if sale_date_key == "saleDd" else detail.sale_date
    fields = {
        "saleWctNo": _required_text(detail.original_window_no, "original_window_no"),
        sale_date_key: _required_text(
            sale_date, "original_sale_date" if sale_date_key == "saleDd" else "sale_date"
        ),
        "saleSqno": _required_text(detail.original_sale_sequence, "original_sale_sequence"),
        "tkRetPwd": _required_text(detail.original_return_password, "original_return_password"),
    }
    journey_sequence = detail.journeys[0].journey_sequence if detail.journeys else None
    if journey_sequence is not None:
        fields["jrnySqno"] = journey_sequence
    return fields


def build_self_checkin_info_form(detail: RefundTicketDetailResponse) -> dict[str, str]:
    """셀프 체크인 정보 조회 폼입니다(SelfCheckInInfoIn.java:55)."""
    return self_checkin_ticket_fields(detail, sale_date_key="saleDt")


def build_self_checkin_seat_check_form(detail: RefundTicketDetailResponse, qr_code: str) -> dict[str, str]:
    """셀프 체크인 좌석 확인 폼입니다(SelfCheckInPossibleIn.java:56). qr_code 는 좌석 테이블의 QR 을 스캔한 문자열이며 승차권 자체의 h_qrcode 가
    아닙니다(SelfCheckInInfoRouteKt.java:241-254; strings.xml:3245-3247)."""
    return {
        "qrcode": _required_text(qr_code, "qr_code"),
        **self_checkin_ticket_fields(detail, sale_date_key="saleDd"),
    }
