# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대리수령·셀프 체크인 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..._core.parsing import present_str, required_int, required_str, wire
from ..common.models import BaseKorailResponse


@dataclass(frozen=True, kw_only=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    """N카드 2인 승차권의 전달 수령자 후보를 담습니다.

    네 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다."""

    acceptance_customer_management_no: str = field(metadata={"wire": "acepCustMgNo", "read": required_str})
    acceptance_customer_name: str = field(metadata={"wire": "acepCustNm", "read": required_str})
    acceptance_customer_phone: str = field(metadata={"wire": "acepCustTeln", "read": required_str})
    member_card_no: str = field(metadata={"wire": "mbCrdNo", "read": required_str})


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceSeat:
    """대리수령 내역의 좌석 한 자리를 담습니다."""

    passenger_type_division_name: str = field(metadata={"wire": "psgTpDvNm", "read": required_str})
    room_class_code: str = field(metadata={"wire": "psrmClCd", "read": required_str})
    room_class_name: str = field(metadata={"wire": "psrmClNm", "read": required_str})
    # 앱 DTO 가 int 라 정수입니다. 그대로 되돌려 보내는 SelfCheckInSeat.car_no 는 문자열로 둡니다.
    car_no: int = field(metadata={"wire": "scarNo", "read": required_int})
    seat_no: str = field(metadata={"wire": "seatNo", "read": required_str})
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceJourney:
    """대리수령 내역의 여정과 좌석 목록을 담습니다."""

    acceptance_customer_name: str = field(metadata={"wire": "acepCustNm", "read": required_str})
    acceptance_customer_phone: str = field(metadata={"wire": "acepCustTeln", "read": required_str})
    journey_type_code: str = field(metadata={"wire": "jrnyTpCd", "read": required_str})
    member_division_name: str = field(metadata={"wire": "mbDvNm", "read": required_str})
    acceptance_kind_name: str = field(metadata={"wire": "pbpAcepKndNm", "read": required_str})
    pbp_reservation_no: str = field(metadata={"wire": "pbpRsvNo", "read": required_str})
    registered_date: str = field(metadata={"wire": "regDt", "read": required_str})
    withdrawal_possible_flag: str = field(metadata={"wire": "wdrwPsbFlg", "read": required_str})
    seats: tuple[PbpAcceptanceSeat, ...] = ()
    member_card_no: str = field(metadata={"wire": "mbCrdNo", "read": required_str})
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceTicket:
    """대리수령 내역의 승차권과 여정 목록을 담습니다."""

    pnr_no: str = field(metadata={"wire": "pnrNo", "read": required_str})
    sale_date: str = field(metadata={"wire": "saleDt", "read": required_str})
    sale_sequence: str = field(metadata={"wire": "saleSqno", "read": required_str})
    sale_window_no: str = field(metadata={"wire": "saleWctNo", "read": required_str})
    return_password: str = field(metadata={"wire": "tkRetPwd", "read": required_str})
    journeys: tuple[PbpAcceptanceJourney, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    """승차권별 대리수령 내역 목록을 담습니다.

    승차권·여정·좌석의 모든 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다."""

    tickets: tuple[PbpAcceptanceTicket, ...] = ()


@dataclass(frozen=True, kw_only=True)
class RecentDeliveryRecipient:
    """최근 승차권을 전달한 수령자 한 명을 담습니다."""

    acceptance_customer_management_flag: str = field(metadata={"wire": "acepCustMgFlg", "read": required_str})
    acceptance_customer_management_no: str = field(metadata={"wire": "acepCustMgNo", "read": required_str})
    acceptance_customer_name: str = field(metadata={"wire": "acepCustNm", "read": required_str})
    acceptance_customer_phone: str = field(metadata={"wire": "acepCustTeln", "read": required_str})
    acceptance_customer_phone_2: str = field(metadata={"wire": "acepCustTeln2", "read": required_str})
    member_card_no: str = field(metadata={"wire": "mbCrdNo", "read": required_str})
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    """최근 승차권 전달 수령자 목록을 담습니다."""

    # 앱 마스크는 필수지만 실서버 응답에 이 키만 없었으므로 선택으로 읽습니다.
    changed_acceptance_reservation_no: str | None = wire("chgePbpRsvNo")
    recipients: tuple[RecentDeliveryRecipient, ...] = ()


@dataclass(frozen=True, kw_only=True)
class SelfCheckInSeat:
    """셀프 체크인할 수 있는 좌석 한 행을 담습니다.

    열여섯 필드 모두 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다. 등록할 때는 이 행을
    ``register_self_checkin``의 ``seat``로 넘깁니다."""

    # 앱은 첫 행을 등록에 넘깁니다.
    pnr_no: str = field(metadata={"wire": "pnrNo", "read": required_str})
    journey_sequence: str = field(metadata={"wire": "jrnySqno", "read": required_str})
    assignment_sequence: str = field(metadata={"wire": "asgnSqno", "read": required_str})
    run_date: str = field(metadata={"wire": "runDt", "read": required_str})
    train_no: str = field(metadata={"wire": "trnNo", "read": required_str})
    departure_construction_order: str = field(metadata={"wire": "dptStnConsOrdr", "read": required_str})
    departure_station_code: str = field(metadata={"wire": "dptRsStnCd", "read": required_str})
    arrival_construction_order: str = field(metadata={"wire": "arvStnConsOrdr", "read": required_str})
    arrival_station_code: str = field(metadata={"wire": "arvRsStnCd", "read": required_str})
    ticket_kind_code: str = field(metadata={"wire": "tkKndCd", "read": required_str})
    train_group_code: str = field(metadata={"wire": "trnGpCd", "read": required_str})
    car_no: str = field(metadata={"wire": "scarNo", "read": required_str})
    seat_no: str = field(metadata={"wire": "seatNo", "read": required_str})
    departure_datetime: str = field(metadata={"wire": "dptDttm", "read": required_str})
    arrival_datetime: str = field(metadata={"wire": "arvDttm", "read": required_str})
    cps_no: str = field(metadata={"wire": "cpsNo", "read": required_str})
    raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)


@dataclass(frozen=True, kw_only=True)
class SelfCheckInSeatCheckResponse(BaseKorailResponse):
    """셀프 체크인 좌석 확인 결과를 담습니다.

    응답에 ``consList`` 키가 없으면 ``KorailProtocolError``가 발생하고, 값이 ``null``이면 ``seats``는 빈 튜플입니다."""

    # 앱은 행이 없으면 아무것도 하지 않습니다.
    seats: tuple[SelfCheckInSeat, ...] = ()


@dataclass(frozen=True, kw_only=True)
class SelfCheckInInfoResponse(BaseKorailResponse):
    """셀프 체크인한 좌석 정보를 담습니다.

    열 필드의 키가 응답에 모두 있어야 하며, 하나라도 없으면 ``KorailProtocolError``가 발생합니다. 값이 ``null``이면 해당 필드는
    ``None``입니다."""

    pnr_no: str | None = wire("pnrNo", present_str, default=None)
    train_no: str | None = wire("trnNo", present_str, default=None)
    departure_station_name: str | None = wire("dptRsStnNm", present_str, default=None)
    departure_time: str | None = wire("dptTmQb", present_str, default=None)
    arrival_station_name: str | None = wire("arvRsStnNm", present_str, default=None)
    arrival_time: str | None = wire("arvTmQb", present_str, default=None)
    car_no: str | None = wire("scarNo", present_str, default=None)
    seat_no: str | None = wire("seatNo", present_str, default=None)
    train_class_name: str | None = wire("stlbTrnClsfNm", present_str, default=None)
    checkin_division_code: str | None = wire("chcknDvCd", present_str, default=None)


@dataclass(frozen=True, kw_only=True)
class SelfCheckInRegisterResponse(BaseKorailResponse):
    """셀프 체크인 등록 결과를 담습니다.

    ``message_id``(``msgId``)는 ``null``일 수 있으며 앱은 이 값을 쓰지 않습니다. 응답에 ``msgId`` 키가 없으면
    ``KorailProtocolError``가 발생합니다."""

    message_id: str | None = wire("msgId", present_str, default=None)


@dataclass(frozen=True, kw_only=True)
class SelfCheckInCancelResponse(BaseKorailResponse):
    """셀프 체크인 취소 결과를 담습니다.

    ``message_id``(``msgId``)는 응답에 없으면 ``None``입니다."""

    message_id: str | None = wire("msgId")


@dataclass(frozen=True, kw_only=True)
class DeliveredTicketRetrievalResponse(BaseKorailResponse):
    """대리수령으로 전달한 승차권을 회수한 결과를 담습니다.

    ``process_flags``에는 응답 행마다 처리 결과 플래그(``prsFlg``)가 들어 있습니다. 응답에 목록(``prsList``)이 없거나
    행에 ``prsFlg``가 없으면 ``KorailProtocolError``가 발생합니다."""

    process_flags: tuple[str, ...] = ()
