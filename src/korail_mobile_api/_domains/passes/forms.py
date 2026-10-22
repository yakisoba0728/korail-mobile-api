# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""정기권·패스·N카드·여행상품 입력과 폼입니다. 입력 모델의 생성은 전송하지 않으며 raw·repr은 마스킹하지 않습니다.

조회 폼도 DTO 선언 순서를 따르며 보호된 입력 코드는 서버 메타데이터 또는 명시값을 사용합니다. DTO 필드·배열 순서와 빈 값 생략은 실제 전송에 영향을 주므로 유지합니다."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal
from typing import cast as _cast

from ..._core.validation import (
    _ascii_digits,
    _int_text,
    _optional_text,
    _required_mutation_text,
    _required_text,
)
from ..._core.wire import _device_version, _device_version_key
from ...config import KorailConfig
from ...constants import (
    KORAIL_DISCOUNT_CARD_DISCOUNT_CODE,
    KORAIL_DISCOUNT_CARD_MENU_ID,
    KORAIL_MAX_DISCOUNT_CARD_SECTIONS,
)
from ...errors import KorailProtocolError
from ..reservations.forms import _PASSENGER_ROWS, _in_reservation_order, build_reservation_form
from ..tickets.forms import OriginalTicketReference
from ..trains.models import TrainSummary
from .models import CommuterInfoResponse, PassMenuData, ProductDetailResponse


@dataclass(frozen=True)
class DiscountCardSectionRequest:
    """구매할 N카드의 적용 구간을 구성합니다.

    요청에는 구간마다 1부터 매긴 번호를 붙여 보냅니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. DTO 키는 밑줄로 끝나며(NCardjrny.java:96-112) 공통
    # 평탄화가 1-기반 인덱스를 붙입니다(NetworkService.java:15345-15366).

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    journey_type_code: str = "11"


@dataclass(frozen=True)
class DiscountCardAdditionalUser:
    """2인용 N카드의 추가 사용자 정보를 구성합니다.

    요청 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. NCardInfoIn.java:30-34 의 속성명 자체에 _1 이
    # 포함됩니다. serializer 이름은 보호돼 전송 키는 속성명에 따른 추정입니다.

    customer_no: str
    name: str
    phone: str


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """N카드 구매에 필요한 구간·사용자·상품 정보를 구성합니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 라우트는 NetworkApi.java:335-337 입니다.

    card_kind_management_no: str
    customer_no: str
    validity_start_date: str = ""
    usable_trip_count: str = ""
    sections: tuple[DiscountCardSectionRequest, ...] = ()
    additional_users: tuple[DiscountCardAdditionalUser, ...] = ()


@dataclass(frozen=True)
class DiscountCardTicket:
    """N카드 기간연장에 필요한 원표의 반환 식별자를 구성합니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 기간연장용 원표 식별자(MyTicketDetailViewModel.java:1049,
    # NCardExtensionIn.java:180).

    sale_window_no: str
    sale_date: str
    sale_sequence: str
    return_password: str


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
    # txtSelPage: 관측에서 요청값을 바꿔도 h_page_no=1 이었습니다. 앱의 해당 인자도 고정이지만 평문은 보호돼
    # 있습니다(CheckUsagePeriodSectionViewModel.java:389). 페이징 신호의 관측 한계는 PassScheduleMainInfo 참고.
    #: 요청할 페이지 번호(``txtSelPage``)입니다. 이 값을 바꿔도 서버가 첫 페이지를 돌려줄 수 있으므로, 받을 건수는
    #: ``page_size``로 정하세요.
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

    # 보호된 기본 코드는 미확인입니다. 실서버 검증 못 함(NCardScheduleIn.java:30-40).

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

        일부 관리번호는 ``"B2N"``, 나머지는 ``"MMM"``을 씁니다. 이 구분이 앱과 같은지는 확인하지 못했습니다."""
        # 앱 대응 함수는 NCardDefine.findDcntCrdKndCd(NCardDefine.java:58-88)이며 그 함수가 특별 취급하는 관리번호 집합은
        # 이 구현과 다릅니다(_B2N_CARD_KIND_MANAGEMENT_NOS 참고).
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
class CommuterTicketInquiryRequest:
    """정기권 예매의 원표 조회 입력을 구성합니다."""

    original_ticket: OriginalTicketReference
    inquiry_type: Literal["0", "1"] = "0"

    def __post_init__(self) -> None:
        if self.inquiry_type not in {"0", "1"}:
            raise KorailProtocolError("inquiry_type must be '0' or '1'")
        if not isinstance(self.original_ticket, OriginalTicketReference):
            raise KorailProtocolError("original_ticket must be an OriginalTicketReference")


#: ``get_commuter_info()``에 넘기는 세 단계 입력 중 하나입니다. 초기 조건(``CommuterInitialRequest``), 승객·인원
#: 조건(``CommuterPassengerRequest``), 원표 조회(``CommuterTicketInquiryRequest``) 중 하나를 넘깁니다.
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
        # WRT800115, 인원 1+E05, 1+E06, 2+E05/E05 는 IRZ000008 이었습니다. 실서버 관측: 이 키를 빼면 1명·2명 모두 FAIL/ERR000100 이었습니다.
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


def build_discount_card_usage_query(card_no: str) -> dict[str, str]:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. ``ticket.dcntCrdUseQry.do`` — ``NetworkApi.java:218``."""
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


def build_discount_card_purchase_form(
    config: KorailConfig,
    request: DiscountCardPurchaseRequest,
) -> dict[str, str]:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 단일 FieldMap 라우트(NetworkApi.java:336-337)와
    NCardInfoIn.java:29-39, NCardjrny.java:55 의 @SerialName 을 따릅니다."""
    if not isinstance(request, DiscountCardPurchaseRequest):
        raise KorailProtocolError("KORAIL discount card purchase requires an exact DiscountCardPurchaseRequest")
    form = _device_version_key(config)
    form.update(
        {
            wire: _required_mutation_text(getattr(request, attr), field=attr)
            for wire, attr in (
                ("dcntCrdKndMgNo", "card_kind_management_no"),
                ("custMgNo", "customer_no"),
                ("vlidTrmStDt", "validity_start_date"),
                ("usePsbTno", "usable_trip_count"),
            )
        }
    )
    sections = tuple(request.sections)
    if not sections or len(sections) > KORAIL_MAX_DISCOUNT_CARD_SECTIONS:
        raise KorailProtocolError(
            f"KORAIL discount card purchase needs 1 to {KORAIL_MAX_DISCOUNT_CARD_SECTIONS} sections"
        )
    form["jrnyCnt"] = str(len(sections))
    for index, section in enumerate(sections, start=1):
        if not isinstance(section, DiscountCardSectionRequest):
            raise KorailProtocolError(
                "KORAIL discount card purchase requires exact DiscountCardSectionRequest values"
            )
        for wire, attr in (
            ("jrnyTpCd", "journey_type_code"),
            ("runDt", "run_date"),
            ("trnNo", "train_no"),
            ("dptRsStnCd", "departure_station_code"),
            ("arvRsStnCd", "arrival_station_code"),
        ):
            form[f"{wire}_{index}"] = _required_mutation_text(
                getattr(section, attr),
                field=attr,
            )
    users = tuple(request.additional_users)
    # 이 입력 모델은 부가사용자 _1 키 한 묶음만 표현합니다(NCardInfoIn.java:29-39).
    if len(users) > 1:
        raise KorailProtocolError("KORAIL discount card purchase takes at most 1 additional user")
    if users:
        form["apdUsrCnt"] = str(len(users))
        for index, user in enumerate(users, start=1):
            if not isinstance(user, DiscountCardAdditionalUser):
                raise KorailProtocolError(
                    "KORAIL discount card purchase requires exact DiscountCardAdditionalUser values"
                )
            for wire, attr in (
                ("custMgNo", "customer_no"),
                ("apdCustName", "name"),
                ("apdCustTeln", "phone"),
            ):
                form[f"{wire}_{index}"] = _required_mutation_text(
                    getattr(user, attr),
                    field=f"additional user {attr}",
                )
    return form


def build_discount_card_extension_query(
    config: KorailConfig,
    ticket: DiscountCardTicket,
) -> dict[str, str]:
    """이름과 달리 POST이며 키는 속성명 추정·실서버 검증 못 함입니다(NetworkApi.java:518-520; NCardExtensionIn.java:31-34)."""
    if not isinstance(ticket, DiscountCardTicket):
        raise KorailProtocolError("KORAIL discount card extension requires an exact DiscountCardTicket")
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


#: 일반 예약에서는 0명 행을 전송하지 않으며, N카드 홀드는 존재하는 행을 한 행으로 대체합니다.
_PASSENGER_ROW_KEYS = frozenset(
    f"{prefix}{index}"
    for prefix in ("txtCompaCnt", "txtPsgTpCd", "txtDiscKndCd")
    for index in range(1, len(_PASSENGER_ROWS) + 1)
)


def build_discount_card_reservation_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    card_no: str,
) -> dict[str, str]:
    """생성만으로 예약하거나 결제하지 않습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
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
    """여행상품 예약 취소의 GET 쿼리를 구성하며 전송하지 않습니다. ProductCancelIn.java:67-70 의 txtVrRsNo·txtGdSqno 이며 둘 다
    get_product_detail 결과에서 옵니다(ProductReservationListScreenKt.java:1252-1253,
    MyTicketDetailViewModel.java:3290)."""
    if not isinstance(detail, ProductDetailResponse):
        raise KorailProtocolError("detail must be a ProductDetailResponse from get_product_detail")
    return {
        "txtVrRsNo": _required_mutation_text(
            detail.virtual_reservation_no, field="virtual_reservation_no", context="product cancel"
        ),
        "txtGdSqno": _required_mutation_text(
            detail.goods_sequence, field="goods_sequence", context="product cancel"
        ),
    }
