# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""정기권·패스·N카드·여행상품 입력과 폼입니다. 입력 모델의 생성은 전송하지 않으며 raw·repr은 마스킹하지 않습니다.

조회 폼도 DTO 선언 순서를 따르며 보호된 입력 코드는 서버 메타데이터 또는 명시값을 사용합니다. DTO 필드·배열 순서와 빈 값 생략은 실제 전송에 영향을 주므로 유지합니다."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, fields
from typing import Literal

from ..._core.validation import (
    _ascii_digits,
    _int_text,
    _optional_text,
    _required_mutation_text,
    _required_text,
)
from ..._core.wire import _device_version, _device_version_key, _in_reservation_order
from ...config import KorailConfig
from ...errors import KorailInvalidInputError
from ..reservations.forms import build_reservation_form
from ..tickets.forms import OriginalTicketReference
from ..trains.models import TrainSummary
from .models import CommuterInfoResponse, PassMenuData, ProductDetailResponse

# 발권 응답의 ResDiscount.N_CARD("443")와 별개입니다. 예약 성공은 실서버 미확인입니다.
# evidence: app 7.0.8 ReqDiscount.N_CARD (복호화), DiscountHelper.java:818, TCReservationRequestHelper.java:284
KORAIL_DISCOUNT_CARD_DISCOUNT_CODE = "153"
# 미확인: 좌석배정 메뉴 값을 재사용합니다. 앱은 SEAT_ASSIGN 과 N_CARD 를 따로 선언하며 두 값은 보호돼 있습니다.
# evidence: app 7.0.6 TicketReservationIn.java:43, ReservationMenuId.java:21-22
KORAIL_DISCOUNT_CARD_MENU_ID = "A2"


@dataclass(frozen=True)
class PassScheduleRequest:
    """정기권으로 이용 가능한 열차 조회 조건을 구성합니다."""

    selected_train_code: str
    departure_date: str
    departure_time: str
    transfer_type_code: str
    pass_kind_code: str
    pass_period_code: str
    pass_age_code: str
    #: 요청할 페이지 번호(``txtSelPage``)입니다. 이 값을 바꿔도 서버가 첫 페이지를 돌려줄 수 있으므로, 받을 건수는
    #: ``page_size``로 정하세요.
    page_no: str
    page_size: str
    departure_station_name: str
    arrival_station_name: str
    weekend_use_flag: str

    def __post_init__(self) -> None:
        # 문자열이 아닌 값은 만들 때 거절합니다. "" 는 이전처럼 전송 단계에서 생략됩니다.
        for item in fields(self):
            if not isinstance(getattr(self, item.name), str):
                raise KorailInvalidInputError(f"{item.name} must be a string")


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


def build_trip_menu_form(config: KorailConfig) -> dict[str, str]:
    return {
        **_device_version(config),
        "timeStamp": str(int(time.time() * 1000)),
    }


@dataclass(frozen=True)
class DiscountCardScheduleRequest:
    """N카드 한 구간의 이용 가능한 열차 조회 조건을 구성합니다.

    ``usable_trip_count``(``usePsbTno``)에는 카드의 실제 값을 넣으세요. 앱의 기본 코드는 앱 내부 값이 공개돼 있지 않아
    확인하지 못했습니다. 보통 ``for_card()``로 만듭니다."""

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
        """카드 종류 관리번호로 할인카드 종류 코드(``card_kind_code``, ``dcntCrdKndCd``)를 정해 조회 조건을 만듭니다.

        ``B2N18120402``·``B2N18120403``만 ``"B2N"``, 나머지는 ``"MMM"``으로 정합니다. 이 ``B2N``·``MMM`` 구분은 앱 7.0.6 정적
        근거(``B2N1906…`` 네 상품을 따로 다룸)와 다르고 실서버에서도 확인하지 못했으므로, 카드 종류 코드를 알면 생성자의
        ``card_kind_code``로 직접 넘기세요."""
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


# 이전 앱 규칙의 2018 상품 집합입니다. 7.0.6 분기의 B2N1906… 네 상품과 달라 for_card() 문서에 적어 둡니다.
_B2N_CARD_KIND_MANAGEMENT_NOS = frozenset({"B2N18120402", "B2N18120403"})


def build_discount_card_schedule_query(
    request: DiscountCardScheduleRequest,
) -> dict[str, str]:
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


def _exact_server_pass_data(pass_data: PassMenuData) -> str:
    """빌더가 쓰는 값은 이것 하나라 객체 출처(PassMenuData 등)는 가리지 않습니다."""
    return _required_text(
        getattr(pass_data, "commuter_kind_code", None),
        "pass_data.commuter_kind_code",
    )


@dataclass(frozen=True)
class CommuterInitialRequest:
    """정기권 예매의 초기 조건 조회 입력을 구성합니다."""

    pass_data: PassMenuData

    def __post_init__(self) -> None:
        _exact_server_pass_data(self.pass_data)


@dataclass(frozen=True, init=False)
class CommuterPassengerRequest:
    """정기권 예매의 승객·인원 조건 조회 입력을 ``from_response()``로 구성합니다."""

    pass_data: PassMenuData
    source: CommuterInfoResponse
    passenger_counts: tuple[int, ...]

    def __init__(self) -> None:
        raise TypeError("CommuterPassengerRequest must be created with from_response()")

    @classmethod
    def from_response(
        cls,
        pass_data: PassMenuData,
        source: CommuterInfoResponse,
        passenger_counts: tuple[int, ...],
    ) -> CommuterPassengerRequest:
        """초기 조회 응답과 승객 종류별 인원으로 인원 조건 조회 입력을 만들고 검증합니다."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "pass_data", pass_data)
        object.__setattr__(instance, "source", source)
        if isinstance(passenger_counts, (str, bytes)) or not isinstance(passenger_counts, Sequence):
            raise KorailInvalidInputError("passenger_counts must be a sequence of integers")
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
        raise KorailInvalidInputError("source must carry passenger_options")
    validated_age_codes = [
        _required_text(getattr(option, "commuter_usage_age_code", None), "commuter_usage_age_code")
        for option in options
    ]
    if not validated_age_codes or len(validated_age_codes) != len(request.passenger_counts):
        raise KorailInvalidInputError("passenger counts must match the response age-code rows")
    for count in request.passenger_counts:
        if type(count) is not int or count < 0:
            raise KorailInvalidInputError("passenger counts must be non-negative integers")
    return tuple(validated_age_codes)


@dataclass(frozen=True)
class CommuterTicketInquiryRequest:
    """정기권 예매의 원표 조회 입력을 구성합니다."""

    original_ticket: OriginalTicketReference
    inquiry_type: Literal["0", "1"] = "0"

    def __post_init__(self) -> None:
        if self.inquiry_type not in {"0", "1"}:
            raise KorailInvalidInputError("inquiry_type must be '0' or '1'")
        if not isinstance(self.original_ticket, OriginalTicketReference):
            raise KorailInvalidInputError("original_ticket must be an OriginalTicketReference")


#: ``get_commuter_info()``에 넘기는 세 단계 입력 중 하나입니다. 초기 조건(``CommuterInitialRequest``), 승객·인원
#: 조건(``CommuterPassengerRequest``), 원표 조회(``CommuterTicketInquiryRequest``) 중 하나를 넘깁니다.
CommuterInfoRequest = CommuterInitialRequest | CommuterPassengerRequest | CommuterTicketInquiryRequest


def build_commuter_info_form(
    request: CommuterInfoRequest,
) -> tuple[tuple[str, str], ...]:
    if isinstance(request, CommuterInitialRequest):
        return (
            ("jobDvCd", "a"),
            ("cmtrKndCd", _exact_server_pass_data(request.pass_data)),
            ("psgCnt", "0"),
        )
    if isinstance(request, CommuterPassengerRequest):
        age_codes = _validate_commuter_passenger_request(request)
        # cmtrUtlAgeCd 는 종류 행당이 아니라 승객당 반복합니다(실서버: 행당 한 번이면 WRT800115, 빼면 ERR000100).
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
            raise KorailInvalidInputError("passenger_counts must select at least one passenger")
        return (
            ("jobDvCd", "b"),
            ("cmtrKndCd", _exact_server_pass_data(request.pass_data)),
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
    raise KorailInvalidInputError("request must be a commuter request variant")


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


def build_pass_menu_form(menu_no: str) -> dict[str, str]:
    return {"menuNo": _required_text(menu_no, "menu_no")}


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
    # 앱의 상태 기본값은 보호돼 있어 호출자가 준 값만 보냅니다.
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


def build_discount_card_usage_query(card_no: str) -> dict[str, str]:
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


def build_discount_card_extension_query(
    config: KorailConfig,
    ticket: OriginalTicketReference,
) -> dict[str, str]:
    """이름과 달리 POST 로 보냅니다. 전송 키는 앱 DTO 의 속성명에서 추정했습니다."""
    if not isinstance(ticket, OriginalTicketReference):
        raise KorailInvalidInputError("KORAIL discount card extension requires an OriginalTicketReference")
    query = _device_version_key(config)
    query.update(
        {
            wire: _required_mutation_text(getattr(ticket, attr), field=attr)
            for wire, attr in (
                ("saleWctNo", "sale_window_no"),
                ("saleDd", "sale_date"),
                ("saleSqno", "sale_sequence"),
                ("tkRetPwd", "return_password"),
            )
        }
    )
    return query


# N카드 홀드는 기본 승객(어른 1명)으로 만든 폼의 승객 행 하나를 N카드 행으로 대체합니다.
_PASSENGER_ROW_KEYS = frozenset({"txtCompaCnt1", "txtPsgTpCd1", "txtDiscKndCd1"})


def build_discount_card_reservation_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    card_no: str,
) -> dict[str, str]:
    """N카드 좌석 홀드 폼을 만듭니다. 생성만으로 예약하거나 결제하지 않습니다."""
    form = build_reservation_form(config, train)
    rebuilt: dict[str, str] = {}
    for name, value in form.items():
        if name == "txtTotPsgCnt":
            rebuilt[name] = "1"
            rebuilt["txtCompaCnt1"] = "1"
            rebuilt["txtPsgTpCd1"] = "1"
            rebuilt["txtDiscKndCd1"] = KORAIL_DISCOUNT_CARD_DISCOUNT_CODE
            rebuilt["txtCardNo_1"] = _required_mutation_text(
                card_no,
                field="card_no",
            )
            continue
        if name in _PASSENGER_ROW_KEYS:
            continue
        rebuilt[name] = value
    rebuilt["txtMenuId"] = KORAIL_DISCOUNT_CARD_MENU_ID
    return _in_reservation_order(rebuilt)


def build_product_cancel_query(detail: ProductDetailResponse) -> dict[str, str]:
    """여행상품 예약 취소의 GET 쿼리를 구성하며 전송하지 않습니다. 두 값은 get_product_detail 결과에서 옵니다."""
    if not isinstance(detail, ProductDetailResponse):
        raise KorailInvalidInputError("detail must be a ProductDetailResponse from get_product_detail")
    return {
        "txtVrRsNo": _required_mutation_text(
            detail.virtual_reservation_no, field="virtual_reservation_no", context="product cancel"
        ),
        "txtGdSqno": _required_mutation_text(
            detail.goods_sequence, field="goods_sequence", context="product cancel"
        ),
    }
