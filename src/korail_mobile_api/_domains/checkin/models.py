# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대리수령·셀프 체크인 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..common.models import BaseKorailResponse


@dataclass(frozen=True, kw_only=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    """N카드 2인 승차권의 전달 수령자 후보를 담습니다.

    네 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다.
    acceptance_customer_management_no: str
    acceptance_customer_name: str
    acceptance_customer_phone: str
    member_card_no: str


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceSeat:
    """대리수령 내역의 좌석 한 자리를 담습니다."""

    passenger_type_division_name: str
    room_class_code: str
    room_class_name: str
    car_no: int
    seat_no: str
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceJourney:
    """대리수령 내역의 여정과 좌석 목록을 담습니다."""

    acceptance_customer_name: str
    acceptance_customer_phone: str
    journey_type_code: str
    member_division_name: str
    acceptance_kind_name: str
    pbp_reservation_no: str
    registered_date: str
    withdrawal_possible_flag: str
    seats: tuple[PbpAcceptanceSeat, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    member_card_no: str


@dataclass(frozen=True, kw_only=True)
class PbpAcceptanceTicket:
    """대리수령 내역의 승차권과 여정 목록을 담습니다."""

    pnr_no: str
    sale_date: str
    sale_sequence: str
    sale_window_no: str
    return_password: str
    journeys: tuple[PbpAcceptanceJourney, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    """승차권별 대리수령 내역 목록을 담습니다.

    승차권·여정·좌석의 모든 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다."""

    tickets: tuple[PbpAcceptanceTicket, ...] = ()


@dataclass(frozen=True, kw_only=True)
class RecentDeliveryRecipient:
    """최근 승차권을 전달한 수령자 한 명을 담습니다."""

    acceptance_customer_management_flag: str
    acceptance_customer_management_no: str
    acceptance_customer_name: str
    acceptance_customer_phone: str
    acceptance_customer_phone_2: str
    member_card_no: str
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    """최근 승차권 전달 수령자 목록을 담습니다."""

    changed_acceptance_reservation_no: str | None = None
    recipients: tuple[RecentDeliveryRecipient, ...] = ()


@dataclass(frozen=True)
class SelfCheckInSeat:
    """셀프 체크인할 수 있는 좌석 한 행을 담습니다.

    열여섯 필드 모두 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다. 등록할 때는 이 행을
    ``register_self_checkin``의 ``seat``로 넘깁니다."""

    # 열여섯 키 모두 필수입니다(ConsList.java:63-65,86-101). 앱은 첫 행을 등록에
    # 넘깁니다(SelfCheckInInfoViewModel.java:151-153,224-225).
    pnr_no: str
    journey_sequence: str
    assignment_sequence: str
    run_date: str
    train_no: str
    departure_construction_order: str
    departure_station_code: str
    arrival_construction_order: str
    arrival_station_code: str
    ticket_kind_code: str
    train_group_code: str
    car_no: str
    seat_no: str
    departure_datetime: str
    arrival_datetime: str
    cps_no: str
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfCheckInSeatCheckResponse(BaseKorailResponse):
    """셀프 체크인 좌석 확인 결과를 담습니다.

    응답에 ``consList`` 키가 없으면 ``KorailProtocolError``가 발생하고, 값이 ``null``이면 ``seats``는 빈 튜플입니다."""

    # checkin.psbFlg.do. consList 는 필수·nullable 입니다(SelfCheckInPossibleOut.java:50-55). 앱은 행이 없으면 아무것도 하지
    # 않습니다.
    seats: tuple[SelfCheckInSeat, ...] = ()


@dataclass(frozen=True)
class SelfCheckInInfoResponse(BaseKorailResponse):
    """셀프 체크인한 좌석 정보를 담습니다.

    열 필드의 키가 응답에 모두 있어야 하며, 하나라도 없으면 ``KorailProtocolError``가 발생합니다. 값이 ``null``이면 해당 필드는
    ``None``입니다."""

    # 열 키 모두 필수·nullable 입니다(SelfCheckInInfoOut.java:56-59,146).
    pnr_no: str | None = None
    train_no: str | None = None
    departure_station_name: str | None = None
    departure_time: str | None = None
    arrival_station_name: str | None = None
    arrival_time: str | None = None
    car_no: str | None = None
    seat_no: str | None = None
    train_class_name: str | None = None
    checkin_division_code: str | None = None


@dataclass(frozen=True)
class SelfCheckInRegisterResponse(BaseKorailResponse):
    """셀프 체크인 등록 결과를 담습니다.

    ``message_id``(``msgId``)는 ``null``일 수 있으며 앱은 이 값을 쓰지 않습니다. 응답에 ``msgId`` 키가 없으면
    ``KorailProtocolError``가 발생합니다."""

    # checkin.reg.do. msgId 는 필수·nullable 이며 앱은 읽지 않습니다(SelfCheckInRegisterOut.java:47-52).

    message_id: str | None = None


@dataclass(frozen=True)
class SelfCheckInCancelResponse(BaseKorailResponse):
    """셀프 체크인 취소 결과를 담습니다.

    ``message_id``(``msgId``)는 응답에 없으면 ``None``입니다."""

    # checkin.cnc.do. msgId 는 선택입니다(SelfCheckInCancelOut.java:50-56).

    message_id: str | None = None


@dataclass(frozen=True)
class DeliveredTicketRetrievalResponse(BaseKorailResponse):
    """대리수령으로 전달한 승차권을 회수한 결과를 담습니다.

    ``process_flags``에는 응답 행마다 처리 결과 플래그(``prsFlg``)가 들어 있습니다. 응답에 목록(``prsList``)이 없거나
    행에 ``prsFlg``가 없으면 ``KorailProtocolError``가 발생합니다."""

    # tk.pbpWdrw.do. prsList 는 필수이고 각 행의 prsFlg 도 필수입니다(RetrieveTicketOut.java:54-59, Prs.java:46-50).

    process_flags: tuple[str, ...] = ()
