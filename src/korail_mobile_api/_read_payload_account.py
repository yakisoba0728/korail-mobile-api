# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""계정·정기권·상품 조회의 원시값과 서버 응답 기반 폼입니다. 키 순서와 빈 값 처리를 보존합니다."""

from __future__ import annotations

from ._read_payload_validation import _ascii_digits, _calendar_date, _int_text, _optional_text, _required_text
from .errors import KorailProtocolError
from .payloads import build_cache_query
from .read_models import CartItem, MaasServiceDetail


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


def _validate_maas_service_detail_query_values(
    start_date: str | None,
    end_date: str | None,
) -> None:
    # 앱은 두 날짜를 따로 nullable 로 넘깁니다(MaasDetailIn.java:65-68, MyTicketBaseViewModel$executeMaasList$1.java:117).
    # 짝·순서는 검사하지 않고, 주어진 값의 YYYYMMDD 형식만 봅니다.
    for value, name in ((start_date, "start_date"), (end_date, "end_date")):
        if value is not None:
            _ascii_digits(value, name, lengths=frozenset({8}))


def build_multi_child_discount_target_form(
    departure_date: str,
) -> dict[str, str]:
    return {"dptDt": _calendar_date(departure_date, "departure_date").strftime("%Y%m%d")}


def build_korail_point_summary_form() -> dict[str, str]:
    """앱 근거: NetworkApi.java:515."""
    return {"point_dv_cd": "0"}


def build_discount_card_usage_query(card_no: str) -> dict[str, str]:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. ``ticket.dcntCrdUseQry.do`` — ``NetworkApi.java:218``."""
    return {"dcntCrdNo": _required_text(card_no, "card_no")}


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


def build_trip_change_date_form(departure_date: str) -> dict[str, str]:
    # 달력 검증은 앱에 없는 라이브러리 검사입니다(앱은 날짜 선택기 값만 보냅니다). 라이브: 20260230·20261340 은 SUCC/API.I00000 에 tripChgDates 없이
    # 돌아왔고, 정상 날짜는 변경 가능일이 없어도 빈 tripChgDates 를 실었습니다(20250101·20991231 등).
    return {"tripChgDate": _calendar_date(departure_date, "departure_date").strftime("%Y%m%d")}


def build_recent_delivery_history_form(customer_no: str) -> dict[str, str]:
    return {"custMgNo": _required_text(customer_no, "customer_no")}
