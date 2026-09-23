# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""읽기 전용 조회 응답 타입 — 승차권, 환불, 할인카드, 마이페이지.

열차 검색·좌석 조회 타입은 :mod:`korail_mobile_api.models`.
전부 ``frozen=True`` 데이터클래스이며 ``raw`` 에 원본 JSON 보존.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse


@dataclass(frozen=True)
class TicketListTicket:
    pnr_no: str | None = field(default=None, repr=False)
    sale_window_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    return_sale_date: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    ticket_status_code: str | None = None
    #: ``h_tk_knd_cd``/``h_tk_knd_nm`` — 승차권 종류(``'72'``/``'스마트티켓'``).
    #: 예약 행이 아니라 승차권 행에 실려 옵니다(라이브 131/131행).
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    train_info: tuple[Mapping[str, Any], ...] = field(default=(), repr=False, compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    # 아래 여섯은 ``raw`` **뒤** 에 붙입니다. 이 데이터클래스들이 위치 인자로
    # 만들어지는 곳이 있을 수 있어, 중간에 끼우면 기존 위치 인자의 의미가 조용히
    # 바뀝니다. 새 필드는 항상 끝에 덧붙입니다.
    #: ``h_tk_sqno`` — 이 승차권 행의 신원 앵커. ``MyTicketListOutTicket.java:92``
    #: 가 선언하는 31개 키 중 하나이고 라이브 131/131행에 옵니다(2026-09-22).
    #: 형제 :attr:`DelayDiscountTicket.ticket_sequence` 와 같은 와이어 키입니다.
    ticket_sequence: str | None = field(default=None, repr=False)
    #: ``h_tk_stt_nm`` — :attr:`ticket_status_code`(``h_tk_stt_cd``)의 사람이 읽는
    #: 짝. 코드만 있고 이름이 없어 ``'09'`` 가 "반환"인지 호출자가 알 수
    #: 없었습니다.
    ticket_status_name: str | None = None
    #: ``h_ret_psb_flg`` — 이 **목록 행** 이 말하는 환불 가능 여부.
    #: :attr:`RefundTicketDetailResponse.refund_possible_flag`(``retPsbFlg``)와
    #: 정면으로 엇갈립니다 — 2026-09-22 라이브에서 이력 143장 전부 여기서는
    #: ``'N'`` 인데 상세 라우트는 같은 승차권에 ``'Y'`` 를 돌려줍니다.
    #: **정정(2026-09-22)**: 이 자리에 원래 "앱도 이 둘을 AND 로
    #: 묶습니다(``NormalTicketSectionKt.java:951``)"라고 적혀 있었는데
    #: 그 인용이 말하는 AND 의 짝이 틀렸습니다. 951행의 실제 활성화 조건은
    #: ``Intrinsics.areEqual(<보호된 리터럴>, ticketDetailOut.getRetPsbFlg())
    #: && !TicketHelper.INSTANCE.isUsedTicketInTrain(reservation)`` 이고,
    #: 여기에 목록 행의 ``h_ret_psb_flg`` 는 등장하지 않습니다. AND 의 뒷항은
    #: ``TicketHelper.java:3173-3199`` 로, 예약의 **첫** 승차권
    #: ``runClsFlg``/``stpvFlg``/``trainInfo`` 로 승차 후 사용 여부를 봅니다.
    #: 비교 리터럴(``'Y'`` 로 추정)은 AlienGuard 로 보호되어 확인 불가입니다.
    #: 즉 이 두 키가 라이브에서 엇갈린다는 관측은 유효하지만, 앱이 그 둘을
    #: AND 한다는 근거는 없습니다 — 그 주장은 미출처입니다.
    return_possible_flag: str | None = None
    #: ``h_use_tno``/``h_noty_use_tno`` — 사용·미통지 사용 거래번호.
    use_transaction_no: str | None = field(default=None, repr=False)
    notify_use_transaction_no: str | None = field(default=None, repr=False)
    #: ``h_pbp_acep_tgt_flg`` — PBP(대리수령) 인수 대상 여부. **여기가 이 값의
    #: 유일한 출처입니다.** ``refunds.SelTicketInfo`` 상세 응답에는 이 키가 오지
    #: 않고(2026-09-22: 20장×2조건 = 40응답 전부 부재), 앱도 목록 행의 값을
    #: 상세 DTO 에 주입해 쓴 뒤(``MyTicketBaseViewModel.java:769``
    #: ``ticketDetailOut.setPbpAcepTgtFlg(myTicketListOutTicket2.getHPbpAcepTgtFlg())``)
    #: 환불 요청에 되돌려 넣습니다(``MyTicketDetailViewModel.java:1521``).
    #: 라이브 131/131행에 있고 ``'N'`` 125 / ``'Y'`` 6 입니다.
    pbp_acceptance_target_flag: str | None = None


@dataclass(frozen=True)
class TicketListReservation:
    """``MyTicketListOutReservation.java`` — ``ticket_list`` 만 ``@SerialName``
    이 있고 나머지 15개 멤버는 없습니다(PROTECTED, 코틀린 필드명이 최선).
    그중 ``addSrvInfo``(부가서비스, ``AddSrvItem`` 객체)는
    :attr:`additional_service`, ``ticketKind``(``TicketDefine.TicketKind``
    열거형)는 :attr:`ticket_kind` 로 읽습니다. 열거형은 코드값 자체를 읽을 수
    없어 온 문자열 그대로 둡니다(아래 필드 주석). 물론 둘 다 :attr:`raw` 로도
    계속 닿을 수 있습니다.
    """

    tickets: tuple[TicketListTicket, ...] = ()
    #: 아래 스칼라들은 모두 ``@SerialName`` 이 없어 코틀린 필드명을 추측한
    #: 것이고, 실서버 예약 행에는 ``ticket_list`` **하나만** 옵니다
    #: (2026-09-22: ``mode="2"`` 예약 128행 전부, 다른 키 0개). 따라서 지금은
    #: 전부 ``None`` 입니다. 불리언들이 ``False`` 가 아니라 ``None`` 인 이유가
    #: 이것입니다 — 서버가 "거짓" 이라고 말한 것이 아니라 아무 말도 하지
    #: 않았습니다. 승차권 종류는 예약이 아니라 **승차권** 행에 있습니다
    #: (:attr:`TicketListTicket.ticket_kind_code`, ``h_tk_knd_cd``, 라이브
    #: 131/131행).
    departure_datetime: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    list_count: str | None = None
    seat_assign_count: int | None = None
    ticket_status: str | None = None
    is_finished: bool | None = None
    is_history: bool | None = None
    is_emergency: bool | None = None
    display_ticket_name: str | None = None
    is_non_member: bool | None = None
    is_transfer: bool | None = None
    is_wheelchair_member: bool | None = None
    is_rail_police_enabled: bool | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    # 아래 둘은 ``raw`` **뒤** 에 붙입니다 — 위 :class:`TicketListTicket` 과 같은
    # 이유로, 위치 인자로 만들어지는 호출부가 조용히 어긋나지 않게 새 필드는
    # 언제나 끝에 덧붙입니다.
    # 둘 다 *관대하게* 읽습니다: 라이브 캡처가 없는 키라, 값이 예상 밖 모양으로
    # 오면 그 필드만 ``None`` 이 되고 예약 행은 그대로 파싱됩니다 — 필드를
    # 덧붙인 일이 예전에 되던 응답을 오류로 바꾸면 안 되기 때문입니다. 무엇이
    # 왔든 :attr:`raw` 에 남습니다(``read_parsers._additive_add_srv_item``).
    #: ``addSrvInfo`` — 이 예약에 딸린 부가서비스 한 건
    #: (``MyTicketListOutReservation.java:39``, 타입 ``AddSrvItem``).
    #: ``AddSrvItem`` 은 MaaS 상세 목록의 행과 **같은 DTO** 이므로
    #: (``MaasDetailOut.java:27`` 의 ``List<AddSrvItem> addSrvList``)
    #: :class:`MaasServiceDetail` 을 그대로 재사용합니다
    #: (``AddSrvItem.java:28-49``, 문자열 21개 + ``detailInfo``).
    #: 이 멤버에도 ``@SerialName`` 이 없어 키(``addSrvInfo``)는 형제 스칼라들과
    #: 마찬가지로 코틀린 필드명 추측입니다.
    additional_service: MaasServiceDetail | None = field(default=None, repr=False)
    #: ``ticketKind`` — ``MyTicketListOutReservation.java:52``, 타입은
    #: ``TicketDefine.TicketKind`` 열거형(``TicketDefine.java:1078-1131``, 10개).
    #: **열거형으로 모델링하지 않고 온 문자열 그대로 둡니다.** 직렬화기가
    #: ``EnumsKt.createSimpleEnumSerializer`` 로 만들어지는데
    #: (``MyTicketListOutReservation.java:59``)
    #: 각 항목의 이름 인자가 ``AlienGuard...method_name_*`` 암호문이라
    #: (``TicketDefine.java:1092-1094,1113-1130``) 와이어에 실제로 실리는
    #: 문자열을 읽을 수 없습니다 — jadx 가 보여주는 식별자
    #: (GENERAL/AIRPORT_BUS/SEAT_ASSIGN/MAAS/COMMUTATION/N_CARD/PASS/
    #: PASS_SUBURBAN_ONE_DAY/RAIL/KORAIL_PASS)가 그 문자열과 같다는 근거가 없어
    #: 매핑을 만들지 않았습니다. 선언된 기본값은 ``GENERAL`` 입니다 --
    #: ``MyTicketListOutReservation.java:133-134`` 이 비트가 없을 때 그 값을
    #: 채웁니다. 다만 키 생략은 "기본값과 같으면 뺀다" 는 값 비교 하나가
    #: **아닙니다**: ``:261`` 의 ``write$Self`` 게이트는
    #: ``output.shouldEncodeElementDefault(serialDesc, 6)`` **또는**
    #: ``ticketKind != GENERAL`` 이면 키를 씁니다(앞쪽 난독화 슬롯은
    #: ``CommonIn.java:444,467`` 의 ``lang`` 게이트가 쓰는 것과 같은 상수).
    #: 즉 생략되는 것은 인코더가 기본값 기록을 요구하지 **않고** 값이
    #: ``GENERAL`` 일 때뿐이고, 그때만 ``None`` 과 ``GENERAL`` 이
    #: 구분되지 않습니다.
    ticket_kind: str | None = None


@dataclass(frozen=True)
class TicketListResponse(BaseKorailResponse):
    reservations: tuple[TicketListReservation, ...] = ()
    #: ``h_total_cnt`` — 구매이력(``mode="2"``)의 서버측 총건수. 0 을 채운
    #: 문자열로 오므로(``'0128'``) 문자열로 둡니다. ``mode="1"`` 과 빈
    #: 응답에는 이 키가 없어 ``None`` 입니다.
    total_count: str | None = None


@dataclass(frozen=True)
class ServiceStatusResponse(BaseKorailResponse):
    pass


@dataclass(frozen=True)
class CartItem:
    service_code: str | None = None
    provider_name: str | None = None
    product_name: str | None = None
    item_type: str | None = None
    departure_date: str | None = None
    received_amount: str | None = None
    reservation_received_date: str | None = None
    #: ``h_tk_cnt`` — ``CartInfo.java:51`` 의 선언은 ``String`` 입니다. 예전에는
    #: int 로 강제 변환해 읽었습니다(6.5.0 Gson 전제를 잘못 적용한 것 —
    #: 이 DTO 는 kotlinx 입니다).
    ticket_count: str | None = None
    usage_start_date: str | None = None
    usage_start_time: str | None = None
    usage_close_time: str | None = None
    partner_reservation_no: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    lump_sum_target_no: str | None = field(default=None, repr=False)
    customer_no: str | None = field(default=None, repr=False)
    virtual_reservation_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    # ``CartInfo.java`` 는 28개 문자열 필드(선언 28-61행) 전부에 평문
    # ``@SerialName`` 을 답니다(281-392행). 위에서 16개만 읽고 있었으므로 남은
    # 열둘을 아래에 덧붙입니다 — ``raw`` **뒤** 인 이유는
    # :class:`TicketListTicket` 과 같습니다(위치 인자 안전).
    # **문자열 말고 중첩 객체가 여섯 더 있습니다.** 이 클래스는 그 여섯을
    # typed 로 제공하지 않습니다 — :attr:`raw` 에만 있습니다. 측정한 범위는
    # 다음과 같습니다(2026-09-23, ``CartInfo.java:28-61`` 의 선언 순서):
    #
    # =========================  ==========================  ===========
    # 전선 키(필드명)            클래스                      String 필드
    # =========================  ==========================  ===========
    # ``greenCarPayDetail``      ``GreenCarPayDetail``       36
    # ``lotteRentalPayDetail``   ``LotteRentalPayDetail``    27
    # ``loyquPayDetail``         ``LoyquPayDetail``          30
    # ``skRentalPayDetail``      ``SKRentalCarPayDetail``    39
    # ``yanoljaDetail``          ``YanoljaDetail``           24
    # ``zimCarryDetail``         ``ZimCarryDetail``          21
    # =========================  ==========================  ===========
    #
    # 합쳐서 177개입니다. 전부 제휴 상품(그린카·롯데렌탈·로이큐·SK렌터카·
    # 야놀자·짐캐리)의 결제 상세라 이 패키지의 핵심 흐름이 건드리지 않고,
    # **라이브 캡처도 없습니다.** 그래서 지금 한꺼번에 모델링하지 않았습니다 —
    # 검증 안 된 표면을 177개 늘리는 쪽이 ``raw`` 로 두는 쪽보다 낫다고 볼
    # 근거가 없습니다. 실제 응답을 한 번이라도 보면 그때 좁혀서 넣는 것이
    # 맞습니다.
    #
    # 찾을 때 주의: **필드명과 클래스명이 하나 어긋납니다.**
    # ``skRentalPayDetail`` 의 타입은 ``SkRentalPayDetail`` 이 아니라
    # ``SKRentalCarPayDetail`` 입니다. 필드명으로 파일을 찾으면 "그런 클래스
    # 없음"이라는 잘못된 결론이 납니다(그렇게 한 번 틀렸습니다).
    #
    # ``ZimCarryDetail`` 과 ``YanoljaDetail`` 은 ``@SerialName`` 이 0개라
    # 전선 키가 코틀린 속성명 그대로일 것으로 보이지만, 그것은 **추론이지
    # 확인이 아닙니다** — 나머지 넷은 각각 10~14개의 평문 ``@SerialName`` 을
    # 답니다.
    #
    # 열둘 모두 *관대하게* 읽습니다: 라이브 캡처가 없어 서버가 보내는 모양을
    # 확인할 수 없으므로, ``bool``/``float``/리스트/객체가 와도 그 필드만
    # ``None`` 이 되고 장바구니 행은 살아 남습니다. 덧붙인 필드가 예전 버전에서
    # 파싱되던 응답을 오류로 바꾸는 일은 없어야 합니다 — 원본 값은 :attr:`raw`
    # 에 그대로 있습니다(``read_parsers._additive_scalar_string``). 위 16개는
    # 예전처럼 엄격합니다.
    #: ``h_item_dv_cd`` — :attr:`item_type`(``h_item_dv_nm``)의 코드 짝
    #: (``CartInfo.java:38``, ``@SerialName`` 은 같은 파일 317행). 앱은 이 코드로
    #: 장바구니 행을 갈라 보지만(``BasketTicketViewModel.java:4186,4295``) 비교
    #: 리터럴이 AlienGuard 로 보호돼 있어 코드값 표는 확인하지 못했습니다.
    item_type_code: str | None = None
    #: ``h_add_srv_mrk_ent_id`` — :attr:`provider_name`(``h_add_srv_mrk_ent_nm``,
    #: ``CartInfo.java:32``)의 ID 짝(``CartInfo.java:31``, ``@SerialName`` 289행).
    provider_id: str | None = field(default=None, repr=False)
    #: ``h_item_sqno``/``h_jrny_sqno``/``h_jrny_tp_cd`` — 이 행의 항목 일련번호,
    #: 여정 일련번호, 여정 구분 코드(``CartInfo.java:40,41,42``, ``@SerialName``
    #: 325/329/333행). 뒤의 둘은 예약·영수증 쪽에서 쓰는 이름을 그대로 씁니다.
    item_sequence: str | None = field(default=None, repr=False)
    journey_sequence: str | None = field(default=None, repr=False)
    journey_type_code: str | None = None
    #: ``utlClsDt`` — :attr:`usage_close_time`(``utlClsTm``)의 날짜 짝
    #: (``CartInfo.java:56``, ``@SerialName`` 377행). 앱도 둘을 이어 붙여 한
    #: 일시로 씁니다(``PayTicketContentKt.java:5234``:
    #: ``getUtlClsDt() + getUtlClsTm()``). 시작 쪽 짝인 :attr:`usage_start_date`
    #: 는 이미 있었고 종료 쪽만 날짜가 빠져 있었습니다.
    usage_close_date: str | None = None
    #: ``h_stl_lmt_tm`` — 결제 기한(``CartInfo.java:49``, ``@SerialName`` 361행).
    #: 앱은 장바구니 행들 중 가장 늦은 값을 고른 뒤 이 값 **하나만** 으로 남은
    #: 초를 셉니다(``PayViewModel.java:11666-11678`` →
    #: ``DateTimeExKt.java:407-431``). 즉 시각 조각이 아니라 그 자체로 완결된
    #: 기한 문자열입니다. 다만 파싱에 쓰는 ``SimpleDateFormat`` 패턴이
    #: AlienGuard 로 보호돼 있어 정확한 자릿수·형식은 확인하지 못했습니다.
    settlement_limit_time: str | None = None
    #: 아래 다섯은 ``CartInfo`` 가 선언만 하고(``CartInfo.java:48,50,36,47,35``,
    #: ``@SerialName`` 357/365/309/353/305행) 디컴파일 어디에서도 게터를 읽는
    #: 화면 코드를 찾지 못했습니다. 이름은 와이어 키를 그대로 옮긴 것이고 의미는
    #: 미확인입니다 — 값 해석은 호출자 몫입니다.
    settlement_extension_transaction_no: str | None = field(default=None, repr=False)
    settlement_means_allow_value: str | None = None
    field_settlement_division: str | None = None
    supervising_station_code: str | None = None
    filler: str | None = field(default=None, repr=False)

    @property
    def usage_window(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        return (
            self.usage_start_date,
            self.usage_start_time,
            self.usage_close_time,
        )


@dataclass(frozen=True)
class CartListResponse(BaseKorailResponse):
    items: tuple[CartItem, ...] = ()


@dataclass(frozen=True)
class DepositBank:
    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DepositBankListResponse(BaseKorailResponse):
    items: tuple[DepositBank, ...] = ()


@dataclass(frozen=True)
class DelayDiscountTicket:
    """지연배상 쿠폰 한 장(``DelayCoupon.java:32-55``, 23개 String 필드).

    ``h_use_psb_dt``(사용 가능 기한)는 전 디컴파일에 0건이라 더 이상 읽지
    않습니다 — 예전에는 이 자리를 채우던 팬텀 키였습니다.
    """

    fare: str | None = None
    original_sale_date: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    #: ``h_tk_sqno`` — 이 줄이 어느 실물 승차권에 붙었는지를 가리키는 신원 앵커.
    ticket_sequence: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    #: ``h_orgtk_sale_dt`` — 원표 자체의 발매일. ``original_sale_date``
    #: (``h_orgtk_ret_sale_dt``, 반환일)와는 다른 필드입니다.
    original_ticket_sale_date: str | None = field(default=None, repr=False)
    #: ``h_rcvd_amt`` — ``fare``(``h_dlay_fare``)와 별개인 수령 금액.
    received_amount: str | None = None
    train_class_code: str | None = None
    room_class_code: str | None = None
    train_no: str | None = None
    departure_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_station_code: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    ticket_status_code: str | None = None
    ticket_status_name: str | None = None
    #: ``h_buy_ps_nm``/``h_abrd_ps_nm`` — 구매자·탑승자 성명. 둘 다 개인정보.
    buyer_name: str | None = field(default=None, repr=False)
    passenger_name: str | None = field(default=None, repr=False)
    page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DelayDiscountTicketListResponse(BaseKorailResponse):
    """``passCard.DelayDiscountView`` — 지연할인권 목록 한 페이지.

    ``DelayDiscountViewOut.java:24,51`` 이 선언하는 것은 ``disc_infos`` 하나뿐인데
    실서버는 ``main_info`` 페이징 블록을 함께 보냅니다(2026-09-22: 8가지 날짜
    입력 전부에서 12키). 앱이 읽지 않는 **서버 추가 키** 라서 파서가 누락한
    것이 아니라 아예 없던 표면이고, 형제
    :class:`DiscountCouponListResponse` 는 같은 네 개념을 이미 내놓고 있어
    비대칭이었습니다.

    다섯 값을 **문자열로** 둡니다. 형제 쿠폰 응답은
    :attr:`~DiscountCouponListResponse.current_page` 와 ``total_pages`` 를 int 로
    바꾸지만, 여기 와이어 값은 0을 채운 문자열(``'0000'``/``'000000000'``)이고
    :attr:`last_page_flag` 는 빈 문자열로 옵니다 — int 로 강제하면 그 빈
    문자열이 ``KorailProtocolError`` 가 됩니다. 이 계정에는 지연할인권이 없어
    다섯 값이 전부 0인 응답만 관측했으므로(2026-09-22), 채워진 응답에서의 정확한
    의미(특히 ``h_page_no`` 가 요청을 되비추는지 — 이 라우트는 페이지 인자를
    받지 않습니다)는 아직 미확인입니다.
    """

    items: tuple[DelayDiscountTicket, ...] = ()
    #: ``main_info.h_page_no``.
    current_page: str | None = None
    #: ``main_info.h_tot_page_cnt``.
    total_pages: str | None = None
    #: ``main_info.h_tot_cnt``.
    total_count: str | None = None
    #: ``main_info.h_row_cnt``.
    row_count: str | None = None
    #: ``main_info.h_last_page_yn``.
    last_page_flag: str | None = None


@dataclass(frozen=True)
class DiscountCoupon:
    guide: str | None = None
    start_date: str | None = None
    expiration_date: str | None = None
    discount_kind_code: str | None = None
    discount_values: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DiscountCouponListResponse(BaseKorailResponse):
    items: tuple[DiscountCoupon, ...] = ()
    current_page: int | None = None
    total_pages: int | None = None
    total_count: str | None = None
    row_count: str | None = None


@dataclass(frozen=True)
class PassOffice:
    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassOpenDate:
    """``pass_info`` 행 하나(``PassInfo.java:92,96,100``, ``:149`` copy).

    ``PassInfo`` 가 선언하는 것은 정확히 세 필드인데 이전에는 ``h_use_open_dt``
    만 뽑아 :attr:`PassAvailabilityResponse.open_dates` 의 날짜 문자열로 납작하게
    만들고 나머지 둘을 버렸습니다 — 같은 응답의 ``wct_info`` 로 만드는
    :class:`PassOffice` 는 ``raw`` 를 들고 있는데 이쪽만 그렇지 않았습니다.

    :attr:`pnr_no` 는 **호출마다 달라집니다.** 같은 입력
    (``'0046'``/``'D007'``/``'E05'``)을 두 번 불러 서로 다른 값을 받았습니다
    (2026-09-22). 나이 코드를 ``E05``→``E06`` 으로 바꿔도 행은 바이트 단위로
    같았으니 승객별 값도 아닙니다 — 살아 있는 할당 카운터로 보입니다. 따라서
    이 값을 안정된 식별자로 저장하거나 ``open_dates`` 와 인덱스로 다시 짝지어
    쓰지 마십시오.
    """

    open_date: str | None = None
    item_sequence: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassAvailabilityMainInfo:
    """``pass.passInfoList`` 의 ``main_info``(``MainInfo.java:103,107,111,115``).

    :class:`PassScheduleMainInfo` 와 같은 자리의 블록이지만 DTO 가 다릅니다 —
    이쪽은 네 필드뿐입니다(``MainInfo.java:172`` ``copy(hMsgCd, hTotCnt,
    hRowCnt, hSelPgNo)``).

    :attr:`message_code` 가 이 라우트의 **유일한** 상태 코드입니다. 최상위 봉투는
    ``strResult`` 만 싣고 ``h_msg_cd`` 를 보내지 않아
    (2026-09-22: 입력 29종 전부에서 최상위 ``h_msg_cd`` 가 ``None``),
    ``IRZ000001``("정상적으로 조회 되었습니다")과 ``IRZ000005``("조회할 자료가
    없습니다")가 여기에만 있습니다. 이전에는 ``raw`` 로만 닿을 수 있었습니다.

    그래도 ``IRZ000005`` 를 예외로 올리지는 **않습니다.** 7.0.6 도 올리지 않기
    때문입니다: ``PassInfoListOut`` 은 ``isSuccess()`` 를 재정의하지 않고,
    ``CommonOut.isSuccess()``→``commonFail()``(``CommonOut.java:455-463``)은
    최상위 ``strResult`` 만 봅니다. 이 DTO 의 두 소비자
    (``PeriodTicketViewModel.java:796``, ``PassConditionViewModel.java:904``)는
    ``isSuccess()`` 통과 후 ``pass_info`` 가 **비었는지** 로 분기하고
    (``:797-800``, ``:910,927``) ``main_info`` 는 읽지 않습니다 —
    ``MainInfo`` 를 참조하는 파일은 디컴파일 전체에서
    ``PassInfoListOut``/``MainInfo$$serializer`` 뿐입니다.
    """

    message_code: str | None = None
    total_count: str | None = None
    row_count: str | None = None
    selected_page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassAvailabilityResponse(BaseKorailResponse):
    #: ``pass_info[].h_use_open_dt`` 만 모은 편의 목록. 키가 없는 행은
    #: 건너뛰므로 :attr:`pass_info` 보다 짧을 수 있습니다 — 세 필드를 전부
    #: 쓰려면 :attr:`pass_info` 를 보십시오.
    open_dates: tuple[str, ...] = ()
    ticket_issue_dates: tuple[str, ...] = ()
    offices: tuple[PassOffice, ...] = ()
    pass_info: tuple[PassOpenDate, ...] = ()
    main_info: PassAvailabilityMainInfo | None = None


@dataclass(frozen=True)
class TripMenuContent:
    """여행상품 메뉴 한 줄(``TrGdMenuLtOutCont.java:25``, 필드 22개).

    **정정(2026-09-22)**: 위 한 줄은 원래 "22개 String 필드"였습니다.
    ``TrGdMenuLtOutCont.java:26-47`` 을 세어 보면 ``String`` 은 21개이고
    나머지 하나는 ``TrGdMenuLtOutPass passData``(``:45``) 객체입니다 —
    합성 생성자(``:72``)의 인수 나열도 ``String`` 21개 + ``TrGdMenuLtOutPass``
    로 같은 구성을 확인합니다. "전부 String" 으로 읽으면 :attr:`pass_data` 를
    문자열로 파싱하려는 실수가 나옵니다.

    :attr:`detail_type` 은 예전에 ``content_type`` 이라는 이름이었습니다. 이름을
    와이어 키(``detailType``, ``TrGdMenuLtOutCont.java:42``)에 맞춰 되돌린 이유:
    "이 줄의 종류"를 약속하는 이름이었는데 그런 값이 오지 않습니다 —
    2026-09-22 에 2회 호출 60행을 세어 54행은 키 자체가 없고 6행은 ``''``,
    쓸 수 있는 값은 한 번도 없었습니다. 형제 :attr:`PassMenuItem.detail_type`
    도 같은 와이어 키를 같은 이름으로 둡니다.

    :attr:`pass_type`(``passType``)을 ``content_type`` 으로 승격하지 **마십시오.**
    ``'aPass'`` 가 실려 오는 것은 맞지만 7.0.6 어디에서도 읽지 않습니다 —
    APK 전수 게터 조사에서 ``detailType``/``passType``/``passActive``/
    ``passAgree``/``passInfo`` 는 호출 지점이 0건이고, 앱이 실제로 읽는 것은
    ``contUrl``/``contImage``/``contTitle``/``contDetail``/``contRouteInfo``/
    ``contBi``/``contCode``/``passData``/``cmtrKndCd`` 뿐입니다.
    """

    title: str | None = None
    detail: str | None = None
    detail_type: str | None = None
    active: str | None = None
    agree: str | None = None
    info: str | None = None
    image: str | None = field(default=None, repr=False)
    url: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    #: ``cmtrKndCd``(``TrGdMenuLtOutCont.java:26``) — 이 줄이 가리키는 정기권
    #: 종류 코드. :meth:`~korail_mobile_api.client.KorailClient.get_commuter_kind_menu`
    #: 의 입력이 바로 이 값이라, 없으면 그 사슬의 시작점이 타입 API 에
    #: 없었습니다. 앱도 같은 식으로 씁니다 — ``PassConditionViewModel.java:1241``
    #: 이 ``contList`` 를 훑으며 ``getCmtrKndCd()`` 를 목표 코드와 비교합니다.
    #: ``menuType='P'``(자유여행패스) 메뉴에만 옵니다(2026-09-22: 60행 중 6행,
    #: ``'0046'``/``'0007'``/``'0049'``).
    commuter_kind_code: str | None = None
    #: ``passType``(``:47``) — 위 6행에서 ``'aPass'``. 7.0.6 에 소비자가 없어
    #: 무엇을 뜻하는지는 미확인입니다(클래스 독스트링 참고).
    pass_type: str | None = None
    #: ``passData``(``:45``, ``TrGdMenuLtOutPass.java:29-35``) — 정기권 조회에
    #: 필요한 연령·기간 선택지 묶음. 정기권 메뉴/종류 라우트가 싣는 것과 같은
    #: 모양이라 ``_parse_pass_menu_data`` 를 그대로 씁니다.
    #: ``PassConditionViewModel.java:1244`` 가 이 객체를 꺼내고, 같은 함수의
    #: ``:1247-1248`` 이 ``null`` 이면 ``backAlert`` 로 화면을 되돌립니다.
    #: (원래 인용은 ``:1246`` 이었는데 그 줄은 닫는 중괄호입니다 —
    #: 동작 설명은 맞았고 줄 번호만 한 칸 어긋나 있었습니다.)
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class TripMenuItem:
    title: str | None = None
    detail: str | None = None
    menu_type: str | None = None
    button: str | None = None
    contents: tuple[TripMenuContent, ...] = ()
    url: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    #: ``contCount``(``TrGdMenuLtOutMenu.java:27``) — 앱 DTO 의 선언은
    #: ``String`` 인데 실서버는 **JSON 숫자** 로 보냅니다(2026-09-22: 5개 메뉴가
    #: 11/6/6/4/3, 전부 ``len(contList)`` 와 일치). 앱이 견디는 것은 그 Json 이
    #: ``setLenient(true)`` 이기 때문입니다(``NetworkServiceKt.java:29``).
    #: 그래서 문자열 필드 맵이 아니라 ``_optional_integer`` 로 읽습니다 —
    #: 그쪽은 정수와 ASCII 10진 문자열을 모두 받습니다.
    content_count: int | None = None


@dataclass(frozen=True)
class TripMenuResponse(BaseKorailResponse):
    items: tuple[TripMenuItem, ...] = ()
    popup_message: str | None = None


@dataclass(frozen=True)
class ProductReservation:
    product_name: str | None = None
    reservation_status: str | None = None
    payment_deadline: str | None = None
    payment_status: str | None = None
    virtual_reservation_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ProductReservationListResponse(BaseKorailResponse):
    items: tuple[ProductReservation, ...] = ()
    total_count: int | None = None


@dataclass(frozen=True)
class ProductDetailResponse(BaseKorailResponse):
    product_name: str | None = None
    reservation_status: str | None = None
    cancellation_deadline: str | None = None
    cancellation_amount: str | None = None
    cancellation_fee: str | None = None
    received_amount: str | None = None
    total_amount: str | None = None
    usage_period: str | None = None
    included_item_names: tuple[str, ...] = ()
    virtual_reservation_no: str | None = field(default=None, repr=False)
    detail_raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReceiptPayment:
    payment_method: str | None = None
    #: ``h_apv_dt``. 형제 필드(계좌·승인·카드·포인트 번호)는 전부 보호되는데
    #: 이 필드만 빠져 있었습니다.
    approval_date: str | None = field(default=None, repr=False)
    installment_months: int | None = None
    amount: int | None = None
    account_no: str | None = field(default=None, repr=False)
    approval_no: str | None = field(default=None, repr=False)
    card_no: str | None = field(default=None, repr=False)
    point_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReceiptCashPayment:
    """현금영수증 줄 (``CashReceiptInfo.java:26-35``).

    원래 인용은 ``ReceiptDao.java:12-40,43-44`` 였는데 7.0.6 에는 그 경로가
    없습니다(6.5.0 시절 잔재). 7.0.6 의 대응물은
    ``ReceiptInfo.java:37`` 의 ``List<CashReceiptInfo> cashRcetInfo`` 이고,
    ``CashReceiptInfo.java:26-35`` 가 필드 다섯을 선언합니다 — ``String`` 넷과
    ``int hTotApvAmt`` 하나. 아래 다섯 속성과 1:1 로 맞고 와이어 키는
    합성 생성자의 ``@SerialName``(``CashReceiptInfo.java:52``)에서 읽었습니다:
    ``h_apv_mtd_nm``/``h_athn_dmn_rcgn_no``/``h_cash_rcet_apv_no``/
    ``h_cash_rcet_txn_dv_cd``/``h_tot_apv_amt``. 여기는 난독화되지 않은
    ``@SerialName`` 리터럴이라 속성 이름이 아니라 실제 전선 철자입니다.
    """

    #: ``h_apv_mtd_nm`` — 사람이 읽는 승인방법 라벨. 형제 필드(인증도메인
    #: 인식번호·현금영수증 승인번호)는 보호되는데 이 필드만 빠져 있었습니다.
    approval_method_name: str | None = field(default=None, repr=False)
    authentication_domain_recognition_no: str | None = field(
        default=None, repr=False
    )
    cash_receipt_approval_no: str | None = field(default=None, repr=False)
    cash_receipt_transaction_division_code: str | None = None
    total_approved_amount: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TicketReceipt:
    travel_date: str | None = None
    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    commuter_kind_code: str | None = None
    journey_type_code: str | None = None
    #: ``h_prt_disc_knd_nm``/``h_prt_disc_knd_cd`` — 영수증에 인쇄된 할인
    #: 종류의 이름·코드. ``ReceiptInfo.java`` 의 19개 String 중 셋(이 코드
    #: 포함)이 빠져 있었습니다.
    printed_discount_name: str | None = None
    printed_discount_kind_code: str | None = None
    print_type: str | None = None
    seat_class_name: str | None = None
    ticket_kind_code: str | None = None
    #: ``h_tk_knd_nm`` — 승차권 종류의 사람이 읽는 이름.
    ticket_kind_name: str | None = None
    ticket_status_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    #: ``h_trn_gp_cd`` — 열차 그룹 코드(KTX/새마을 등).
    train_group_code: str | None = None
    train_no: str | None = None
    passenger_counts: tuple[int | None, int | None, int | None] = (
        None,
        None,
        None,
    )
    received_amount: int | None = None
    card_refund_amount: int | None = None
    refund_fee: int | None = None
    refund_received_amount: int | None = None
    point_refund_amount: int | None = None
    payments: tuple[ReceiptPayment, ...] = ()
    #: ``cash_rcet_info`` — 현금영수증 줄들.
    cash_receipts: tuple[ReceiptCashPayment, ...] = ()
    member_card_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TicketReceiptResponse(BaseKorailResponse):
    items: tuple[TicketReceipt, ...] = ()


@dataclass(frozen=True)
class ReservationHistoryTrain:
    """예약 이력 여정의 열차 행 하나.

    ``ReservationViewOutTrainInfo.java:94`` 의 합성 생성자에는 평문
    ``@SerialName`` 이 37개 있습니다. 그것이 **전부는 아닙니다** — 생성된
    serializer 의 descriptor 에는 슬롯이 40개라(``…$$serializer.java:39-79``),
    이름이 평문으로 남지 않은 셋이 더 있습니다. 예전에 "전체 집합이 정확히
    37개" 라고 적은 것은 부분집합을 전체로 말한 것이었습니다. 그중 미결제 홀드가
    실제로 "무엇에 관한 것인지"를 말하는 결제 기한 삼총사
    (:attr:`payment_deadline_date`/:attr:`payment_deadline_time`/
    :attr:`payment_message`)가 빠져 있었습니다 — :attr:`payment_flag` 와
    :attr:`settlement_flag` 로 "결제해야 한다"는 것만 알고 "언제까지"는 알 수
    없었다는 뜻입니다.

    이 계정에는 살아 있는 미결제 홀드가 없어(2026-09-22:
    ``h_msg_cd='P100'``, ``jrny_info == []``) 아래 여섯 필드의 라이브 값은
    확인하지 못했습니다. 홀드를 만들려면 예매가 필요해 범위 밖이었습니다 —
    근거는 위 ``@SerialName`` 선언입니다.
    """

    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    run_date: str | None = None
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    reservation_type_code: str | None = None
    acceptance_possible_flag: str | None = None
    payment_flag: str | None = None
    settlement_flag: str | None = None
    #: ``h_rsv_amt`` — 이 열차 행의 유일한 금액 필드
    #: (``ReservationViewOutTrainInfo.java:496``).
    reserved_amount: str | None = None
    seat_count: int | None = None
    standing_count: int | None = None
    pnr_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    # 새 필드는 ``raw`` 뒤에 덧붙입니다(위치 인자 의미 보존).
    #: ``h_ntisu_lmt_dt``/``h_ntisu_lmt_tm`` — 이 홀드의 결제 기한 날짜·시각.
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    #: ``h_payment_msg`` — 그 기한을 사람이 읽는 문구로 옮긴 것.
    payment_message: str | None = None
    #: ``h_ntisu_psb_dt`` — 결제를 시작할 수 있는 날짜(기한의 반대쪽 끝).
    payment_possible_date: str | None = None
    #: ``h_pre_stl_tgt_flg`` — 선결제 대상 여부.
    prepayment_target_flag: str | None = None
    #: ``h_jrny_sqno`` — 이 행이 속한 여정의 순번. 같은 이름을 쓰는 형제
    #: :attr:`ReservationHistoryPassenger` 쪽과 여정을 맞출 때 필요합니다.
    journey_sequence: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class ReservationHistoryTicket:
    """예약 이력 여정의 ``ReservationOut.tkList`` 행 하나(``ReservationOutTK.java``).

    할인(``dcntList``)·동반가족(``fmlyList``)·정산(``stlList``) 하위 목록은
    일부러 :attr:`raw` 에만 남깁니다 — :class:`OriginalTicket` 이 같은 이유로
    ``cmpnList``/``stlList`` 를 raw 전용으로 두는 것과 같은 판단입니다.
    """

    sale_date: str | None = None
    sale_window_no: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    movie_ticket_flag: str | None = None
    delay_discount_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryOriginalTicket:
    """예약 이력 여정의 ``ReservationOut.orgTkList`` 행 하나(``ReservationOrgTk.java``)."""

    sale_date: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    #: ``ogtkRetPwd`` — 원표 반환 비밀번호. 그 자체로 반환 권한이라 민감합니다.
    return_password: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryPassenger:
    """예약 이력 여정의 ``ReservationOut.psgInfos.psgInfo`` 행 하나(``ReservationOutPsgInfo.java``)."""

    passenger_type_code: str | None = None
    passenger_count_per_info: str | None = None
    discount_kind_code: str | None = None
    discount_kind_code_2: str | None = None
    discount_no: str | None = field(default=None, repr=False)
    discount_no_2: str | None = field(default=None, repr=False)
    delay_original_window_no: str | None = field(default=None, repr=False)
    delay_original_sale_date: str | None = field(default=None, repr=False)
    delay_original_sale_sequence: str | None = field(default=None, repr=False)
    #: ``dlayOgtkRetPwd`` — 지연배상 원표의 반환 비밀번호.
    delay_original_return_password: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryReservation:
    """예약 이력 여정에 매달린 ``ReservationOut`` — 실제 PNR·운임·결제 층.

    7.0.6 이 이 층 전체를 여정 옆에 익명 중첩으로 선언합니다
    (``ReservationViewOutJrnyInfo.java:55`` 의 다섯 번째 생성자 인자). 이전에는
    예약 이력 파서가 여정·열차 층만 읽고 이 층 전체를 건너뛰어, PNR 의 실제
    운임·결제·발권 내용이 타입 API 어디에도 없었습니다.

    이 중첩 자체의 정확한 와이어 철자는 ``@SerialName`` 이 없어 PROTECTED 입니다
    — 코틀린 필드명 ``reservationOut`` 을 최선으로 사용합니다
    (``ReservationViewOutJrnyInfo.java`` 의 ``getReservationOut$annotations()``
    부재).
    """

    #: ``h_pnr_no``.
    pnr_no: str | None = field(default=None, repr=False)
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 이 PNR 의 실제 결제(정산) 금액.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    tickets: tuple[ReservationHistoryTicket, ...] = ()
    original_tickets: tuple[ReservationHistoryOriginalTicket, ...] = ()
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryJourney:
    """예약 이력의 여정 하나(``ReservationViewOutJrnyInfo.java``).

    ``srv_infos``/``acmp_infos`` 는 아직 행 단위로 모델링하지 않고 원본 그대로
    노출합니다 — 이전에는 이 층 자체가 최상위 ``raw`` 블롭에만 남아 타입
    응답 어디로도 들어오지 못했으므로, 원본 그대로라도 여정 단위로 닿을 수
    있게 하는 것이 이번 수정의 목적입니다.
    """

    trains: tuple[ReservationHistoryTrain, ...] = ()
    service_infos: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    accompanying_infos: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    reservation: ReservationHistoryReservation | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryResponse(BaseKorailResponse):
    """``ReservationViewOut`` — 예약 이력(``research.reservationView.do``).

    최상위 신원 필드(``h_rsv_ps_nm``/``h_tel_no`` 등)와 :attr:`journeys` 는
    이전에는 전혀 파싱되지 않고 최상위 ``raw`` 안에만 있었습니다
    (``ReservationViewOut.java:64``).
    """

    #: ``h_rsv_ps_nm`` — 예약자 성명.
    reservation_passenger_name: str | None = field(default=None, repr=False)
    #: ``h_tel_no`` — 예약자 전화번호.
    phone_no: str | None = field(default=None, repr=False)
    reservation_limit_flag: str | None = None
    seatmap_flag: str | None = None
    process_flag: str | None = None
    follow_flag: str | None = None
    #: ``h_cust_no`` — 고객관리번호. 신원 식별자라 민감.
    customer_no: str | None = field(default=None, repr=False)
    customer_division_code: str | None = None
    customer_sort_code: str | None = None
    customer_class_code: str | None = None
    journey_count: str | None = None
    #: ``guide_infos.guide_info`` — 단일 안내 문구.
    guide_info: str | None = None
    journeys: tuple[ReservationHistoryJourney, ...] = ()
    #: 모든 여정의 열차 행을 평탄화한 목록입니다. 개별 여정의 돈·PNR 층에
    #: 닿으려면 :attr:`journeys` 를 쓰십시오.
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        return self.items


@dataclass(frozen=True)
class FreeSeatCarResponse(BaseKorailResponse):
    title: str | None = None
    car_no: str | None = field(default=None, repr=False)
    content: str | None = None


@dataclass(frozen=True)
class GuideSeatConditionResponse(BaseKorailResponse):
    """``reservation.guideSeatCnd.do`` 의 응답.

    ``FAIL``/``MRR800011``(도우미 좌석 안내)도 예외가 아니라 이 응답으로 옵니다.
    안내 문구는 ``h_msg_txt`` 에 있습니다.

    ``GuideSeatCndOut`` 이 선언하는 자체 필드는 :attr:`time_stamp`
    (``GuideSeatCndOut.java:29`` 의 ``public final long timeStamp``)
    하나뿐입니다 — 그래서 이전에는 봉투 밖으로 아무것도 읽지 않았습니다.
    (파일명을 여기서 적는 이유: 직전 주석에 다른 파일 인용이 없어 생략형
    ``:29`` 는 가리킬 선행 파일명이 아예 없었습니다.)

    이전 주석은 와이어 철자를 "PROTECTED" 라고 적었는데 그 표현은
    정확하지 않습니다. ``GuideSeatCndOut.java:50`` 의 합성 생성자를 보면
    봉투 두 칸에는 ``@SerialName("h_msg_cd")``/``@SerialName("h_msg_txt")``
    가 붙어 있고 ``long j``(= ``timeStamp``)에는 아무것도 붙지 않습니다 —
    즉 AlienGuard 로 난독화된 리터럴이 아니라 ``@SerialName`` 이 없어
    kotlinx 기본값(= 프로퍼티 이름)이 곧 와이어 키인 경우입니다. 그래서
    ``timeStamp`` 를 최선으로 쓰되 라이브로 재확인하기 전까지는 추정으로
    둡니다(아래 ``NCardScheduleItem`` 주석과 같은 구분).
    """

    time_stamp: int | None = None


@dataclass(frozen=True)
class TrainScheduleItem:
    """열차 행 하나 — ``assignScheduleView.do``(``TrainScheduleOutTrainInfo``)와
    ``mergeSeatsC.do``(``MergeSeatsCOutTrnInfo``) 두 라우트가 공유합니다.

    두 DTO 는 서로 다른데(``TrainScheduleOutTrainInfo`` 는 100여 필드,
    ``MergeSeatsCOutTrnInfo`` 는 30필드) 실제 필드 이름의 상당수가
    (``train_no``/``run_date``/``departure_*``/``arrival_*``/
    ``*_reservation_code`` 등) 의미상 겹칩니다. 완전히 별개 데이터클래스로
    쪼개는 대신, 각 라우트 전용 필드 맵(``_MERGE_SEATS_TRAIN_FIELDS``와
    ``_TRAIN_SCHEDULE_OUT_TRAIN_FIELDS``, ``read_parsers.py``)으로 각 DTO 의
    실제 와이어 키만 채우도록 나누고, 이 데이터클래스는 두 DTO 의 필드를
    합친 상위집합으로 유지합니다 — 한쪽 라우트에서 안 쓰는 필드는 그냥
    ``None`` 입니다. 필드 맵을 하나로 재사용하던 이전 버그(서로의 DTO 에
    없는 키를 읽고, 있는 키는 빠뜨림)의 근본 원인이 바로 이 공유였습니다.
    """

    train_no: str | None = None
    #: ``h_trn_no_qb`` — 병합예약 조회 전용 열차번호(``MergeSeatsCOutTrnInfo``).
    train_no_qb: str | None = field(default=None, repr=False)
    #: ``h_trn_seq`` — 열차 순번(``MergeSeatsCOutTrnInfo``).
    train_sequence: str | None = field(default=None, repr=False)
    train_group_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    run_date: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    #: ``h_dpt_tm_qb``(``MergeSeatsCOutTrnInfo``).
    departure_time_qb: str | None = field(default=None, repr=False)
    arrival_date: str | None = None
    arrival_time: str | None = None
    #: ``h_arv_tm_qb``(``MergeSeatsCOutTrnInfo``).
    arrival_time_qb: str | None = field(default=None, repr=False)
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_construction_order: str | None = None
    arrival_construction_order: str | None = None
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    car_type_name: str | None = None
    general_room_name: str | None = None
    special_room_name: str | None = None
    general_reservation_code: str | None = None
    #: ``h_gen_rsv_nm`` — 두 DTO 모두 선언합니다
    #: (``MergeSeatsCOutTrnInfo``, ``TrainScheduleOutTrainInfo.java:1228``).
    #: 예전에는 병합 라우트에서만 읽어 ``assignScheduleView.do`` 쪽은 전선에
    #: ``'예약하기'`` 가 와도 항상 ``None`` 이었습니다(2026-09-22: ``A1``/``A2``
    #: 각 10행 전부).
    general_reservation_name: str | None = None
    special_reservation_code: str | None = None
    free_seat_reservation_code: str | None = None
    standing_reservation_code: str | None = None
    #: ``h_stnd_rsv_nm``(``TrainScheduleOutTrainInfo.java:1380``) — 위와 같은
    #: 이유로 좌석배정 라우트에서 죽은 읽기였습니다. 상수 ``'-'`` 가 아니라
    #: 살아 있는 값입니다(2026-09-22: ``A2`` 일부 행이 ``'역발매중'``).
    standing_reservation_name: str | None = None
    #: ``h_jrny_rsv_cd``/``h_jrny_rsv_nm``(``MergeSeatsCOutTrnInfo``).
    journey_reservation_code: str | None = None
    journey_reservation_name: str | None = None
    seat_map_flag: str | None = None
    delay_sale_flag: str | None = None
    wait_reservation_flag: str | None = None
    #: ``h_rsv_psb_nm``(``TrainScheduleOutTrainInfo.java:1296``) — 메뉴에 따라
    #: **내용이 달라지는 화면 문구** 이지 가부 플래그가 아닙니다. 같은 열차·같은
    #: 날짜로 ``menu_id='A1'`` 은 ``'예약가능'``, ``'A2'``(할인 메뉴)는
    #: ``'15%할인'``/``'20%할인'`` 을 돌려줍니다(2026-09-22). 이 필드에서
    #: 할인 라벨이 나오는 것은 매핑 실수가 아니라 서버가 그렇게 보내는
    #: 것입니다 — 다른 키로 "고치지" 마십시오.
    reservation_possible_name: str | None = None
    special_reservation_possible_name: str | None = None
    info_text: str | None = None
    popup_message: str | None = field(default=None, repr=False)
    #: ``shtmStndOpFlg`` — 셔틀 입석 오픈 여부(``MergeSeatsCOutTrnInfo``).
    shuttle_standing_open_flag: str | None = None
    #: ``restStndNum`` — 잔여 입석수(``MergeSeatsCOutTrnInfo``).
    remaining_standing_count: str | None = None
    #: ``h_std_rest_seat_cnt`` — 일반실 잔여석. 두 DTO 모두 선언합니다.
    standard_remaining_seat_count: str | None = None
    #: ``h_fst_rest_seat_cnt`` — 특실 잔여석(``TrainScheduleOutTrainInfo``).
    first_remaining_seat_count: str | None = None
    #: ``h_yms_apl_flg`` — 이 행이 병합(입석+좌석) 대상인지를 정하는 유일한
    #: 입력(``TrainScheduleOutTrainInfo``, ``models.TrainSummary`` 참고).
    merge_target_flag: str | None = None
    #: ``h_trn_sps_flg`` — 운휴 표시/예약 게이트(``TrainScheduleOutTrainInfo``).
    train_suspended_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    # 새 필드는 ``raw`` 뒤에 덧붙입니다(위치 인자 의미 보존).
    #: ``h_spe_rsv_nm``/``h_free_rsv_nm``
    #: (``TrainScheduleOutTrainInfo.java:1344,1196``) — 특실·자유석 예약 문구.
    #: 코드 짝(:attr:`special_reservation_code`/
    #: :attr:`free_seat_reservation_code`)은 있는데 이름 짝만 모델에 자리가
    #: 아예 없었습니다. ``MergeSeatsCOutTrnInfo`` 에는 없는 필드라 병합
    #: 라우트에서는 ``None`` 입니다.
    special_reservation_name: str | None = None
    free_seat_reservation_name: str | None = None


@dataclass(frozen=True)
class PassScheduleTrain:
    """정기권 일정의 열차 한 행(``TrainList.java:25-70``, 20개 필드).

    이전에는 8개만 매핑돼 :attr:`run_date`(``h_run_dt``) — 이 행의 유일한
    날짜 — 조차 없었습니다.
    """

    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    detour_code: str | None = None
    schedule_price: str | None = None
    train_group_code: str | None = None
    train_no: str | None = None
    #: ``h_trn_seq`` — 열차 순번.
    train_sequence: str | None = field(default=None, repr=False)
    #: ``h_chg_trn_seq``/``h_chg_trn_dv_cd`` — 변경된 열차의 순번·구분 코드.
    change_train_sequence: str | None = field(default=None, repr=False)
    change_train_division_code: str | None = None
    #: ``h_run_dt`` — 이 행의 유일한 운행일자.
    run_date: str | None = None
    price_class_code: str | None = None
    route_code: str | None = field(default=None, repr=False)
    departure_construction_order: str | None = field(default=None, repr=False)
    arrival_construction_order: str | None = field(default=None, repr=False)
    car_type_code: str | None = None
    train_class_code: str | None = None
    commuter_use_terminal_code: str | None = None
    commuter_use_terminal_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassAgeOption:
    commuter_age_code: str | None = None
    display_name: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassScheduleInfo:
    trains: tuple[PassScheduleTrain, ...] = field(
        default=(),
        repr=False,
    )
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassScheduleMainInfo:
    sale_window_no: str | None = field(default=None, repr=False)
    work_date: str | None = field(default=None, repr=False)
    work_time: str | None = field(default=None, repr=False)
    job_id: str | None = field(default=None, repr=False)
    version_no: str | None = None
    message_code: str | None = None
    selected_count: str | None = None
    total_selected_count: str | None = None
    count_per_page: str | None = None
    #: 이 라우트의 페이징 신호 셋은 **믿을 수 없습니다.** 2026-09-22 실측:
    #: :attr:`total_selected_count` 가 :attr:`count_per_page` 를 넘는데도
    #: :attr:`next_page_flag` 는 항상 ``'N'``, :attr:`page_count` 는 항상
    #: ``'00000'``, :attr:`page_no` 는 항상 ``'1'`` 이었습니다. 그러므로
    #: ``while next_page_flag == 'Y'`` 같은 반복 조건으로 쓰면 첫 페이지에서
    #: 멈춥니다. 더 받으려면 페이지를 넘기지 말고
    #: :attr:`~korail_mobile_api.read_payloads.PassScheduleRequest.page_size`
    #: 를 키우십시오.
    page_count: str | None = None
    next_page_flag: str | None = None
    change_train_division_code: str | None = None
    page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class SeatAssignmentScheduleResponse(BaseKorailResponse):
    """``assignScheduleView.do`` — ``TrainScheduleOut.java:67`` 의 전체 필드.

    이전에는 :attr:`next_page_flag` 만 꺼내 페이징 신호는 있는데 되실을
    커서가 없었습니다. 같은 DTO 모양을 쓰는 형제 파서
    ``parsers.py::parse_train_search_metadata``/``TrainSearchMetadata`` 가
    이미 이 필드 집합을 정확히 이렇게 읽으므로 그 이름을 그대로 따릅니다.
    """

    next_page_flag: str | None = None
    merge_reservation_possible_flag: str | None = None
    job_id: str | None = None
    menu_id: str | None = None
    goods_no: str | None = None
    notice_message: str | None = None
    first_seat_count: str | None = None
    second_seat_count: str | None = None
    agreement_text: str | None = None
    first_departure_time: str | None = None
    result_count: str | None = None
    next_query_station_no: str | None = None
    next_train_no: str | None = None
    next_preceding_train_no: str | None = None
    next_connecting_train_no: str | None = None
    remaining_seat_count: str | None = None
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class IntermediateStation:
    code: str | None = None
    name: str | None = None
    run_order: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassPeriodOption:
    commuter_period_code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MergeSeatsInquiryResponse(BaseKorailResponse):
    merge_reservation_possible_flag: str | None = None
    #: ``runDt`` — 최상위 운행일자(``MergeSeatsCOut.java:29,112``).
    #:
    #: **항상 ``None`` 입니다.** 읽는 키가 틀린 것이 아니라 서버가 자기 DTO 가
    #: 선언한 키를 보내지 않습니다 — 실서버 ``mergeSeatsC.do`` 의 최상위 봉투는
    #: ``h_msg_cd``/``h_msg_txt``/``msgCd``/``msgTxt``/``strResult`` 다섯
    #: 스칼라에 ``midStnList``/``trn_infos`` 뿐이고 ``runDt`` 가 없습니다
    #: (2026-09-22, 20여 회 호출 전부). 같은 DTO 가 선언하는 ``midStnList``
    #: (``:108``)와 ``trn_infos``(``:116``)는 정상적으로 옵니다.
    #: 운행일자는 행 단위로 옵니다 — ``trains[i].run_date``(``h_run_dt``)를
    #: 쓰십시오.
    run_date: str | None = None
    intermediate_stations: tuple[IntermediateStation, ...] = ()
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class PassMenuData:
    commuter_kind_code: str | None = None
    station_selection: str | None = None
    age_options: tuple[PassAgeOption, ...] = ()
    period_options: tuple[PassPeriodOption, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassPassengerInfo:
    h_cls_prnb: int | None = None
    h_dcnt_knd_cd: str | None = None
    h_st_prnb: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassPassengerInfos:
    h_chtn_allw_flg: str | None = None
    h_max_cnt: str | None = None
    h_min_cnt: str | None = None
    psg_info: tuple[PassPassengerInfo, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassGoodsInfo:
    h_cnd_flg_disc_no: str | None = field(default=None, repr=False)
    psg_infos: PassPassengerInfos | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassMenuItem:
    #: ``afterDay`` — 서버가 문자열로 보냅니다(``PassMenuOutItem.java:28``
    #: ``String``). 형제 :class:`CommuterKindMenuResponse.after_day` 와 형이
    #: 같습니다. 정수가 필요하면 호출자가 변환하십시오 — 앱도 그 자리에서
    #: ``StringExKt.safeToInt`` 로 파싱 실패 시 0을 씁니다.
    after_day: str | None = None
    agreement: str | None = None
    detail_type: str | None = None
    detail_description: str | None = None
    enabled: str | None = None
    item_id: str | None = None
    information: str | None = None
    sale_message_1: str | None = None
    sale_message_2: str | None = None
    sale_message_3: str | None = None
    expanded: str | None = None
    parent_id: str | None = None
    representative_arrival: str | None = None
    representative_departure: str | None = None
    title: str | None = None
    train_group_code: str | None = None
    item_type: str | None = None
    goods_data: PassGoodsInfo | None = None
    pass_data: PassMenuData | None = None
    url: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassMenuResponse(BaseKorailResponse):
    items: tuple[PassMenuItem, ...] = ()


@dataclass(frozen=True)
class CommuterKindMenuResponse(BaseKorailResponse):
    after_day: str | None = None
    agreement: str | None = None
    information: str | None = None
    title: str | None = None
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class CrewRequestOption:
    message_code: str | None = None
    content: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class CrewRequestListResponse(BaseKorailResponse):
    items: tuple[CrewRequestOption, ...] = ()


@dataclass(frozen=True)
class PassScheduleResponse(BaseKorailResponse):
    main_info: PassScheduleMainInfo | None = None
    schedules: tuple[PassScheduleInfo, ...] = field(
        default=(),
        repr=False,
    )


@dataclass(frozen=True)
class DiscountCardSection:
    """할인카드가 등록된 구간 하나.

    7.0.6 의 대응 DTO 는 ``AppSegInfo.java:24-37`` 입니다 — ``String`` 아홉
    (``jrnySqno``/``jrnyTpCd``/``trnGpCd``/``dptRsStnNm``/``dptRsStnCd``/
    ``arvRsStnNm``/``arvRsStnCd``/``stlbDturDvNm``/``stlbDturDvCd``)이고
    ``@SerialName`` 이 하나도 없으므로 **프로퍼티 이름이 곧 와이어 키** 입니다.
    ``DiscountCardInfo.java:28`` 의 ``List<AppSegInfo> appSegList`` 로 실려
    옵니다. 원래 인용은 ``dao/refund/TicketDetailDao.java:25-64`` 였는데 7.0.6
    디컴파일에 그 경로가 없습니다(6.5.0 잔재) — 아래 여섯 속성이 위 아홉 중
    여섯과 1:1 로 맞아 같은 구조로 확인했습니다.
    N카드는 이런 구간 1~3 개에
    대해 팔리고, 그 구간을 지나는 열차에만 쓸 수 있습니다.
    :meth:`~korail_mobile_api.client.KorailClient.get_discount_card_schedule`
    가 역코드가 아니라 역 **이름** 을 받는 것도 그것이 여기서 나오기
    때문입니다.
    """

    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    #: ``jrnySqno`` — 이 구간의 순번. 예전에는 존재하지 않는 키
    #: (``dcntCrdAplSegSqno``, 전 디컴파일 0건)를 ``section_sequence`` 로
    #: 잘못 읽었는데, 실제로 가장 가까운 필드는 바로 이 ``journey_sequence``
    #: 입니다.
    journey_sequence: str | None = field(default=None, repr=False)
    journey_type_code: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)
    #: ``stlbDturDvNm``(``AppSegInfo.java:36``) — 경유 이름. 앱이 좌석지정
    #: 시각표 요청에 그대로 넘깁니다. 원래 인용은 ``u4/b.java:104`` 였는데
    #: 7.0.6 에 그 경로가 없어 사슬을 다시 찾았습니다:
    #: ``NCardReservationViewModel.java:154-158`` 이
    #: ``getDcntCrdInfo().getAppSegList()[index].getStlbDturDvNm()`` 을
    #: ``Triple`` 에 담아 같은 파일 ``:164`` 의 ``new TrainScheduleRoute(…)``
    #: 로 넘기고, ``TrainScheduleViewModel.java:2639`` 의
    #: ``buildAssignSchedule`` 이 그 ``Triple`` 에서 값을 꺼내(같은 파일
    #: ``:2730-2736``) ``AssignScheduleIn`` 의 열 번째 인자로 넣습니다(같은
    #: 파일 ``:2749``/``:2831`` 의 두 ``return new AssignScheduleIn(…)``,
    #: 열 번째 인자가 그 ``str2``) — 그 자리가 ``AssignScheduleIn.java:41``
    #: 의 ``stlbDturDvNm1`` 입니다. ``:2639`` 이하 네 줄번호는
    #: **TrainScheduleViewModel.java**(11116행) 쪽입니다. 생략형으로 적으면
    #: 직전에 인용한 431행짜리 ``NCardReservationViewModel.java`` 를
    #: 가리키는 것으로 읽혀 따라갈 수 없습니다.
    detour_division_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DiscountCardOnTicket:
    """승차권 상세가 설명하는 할인카드.

    7.0.6 의 대응 DTO 는 ``DiscountCardInfo.java:27-32`` 입니다
    (``List<AppSegInfo> appSegList`` + ``String`` 넷). 원래 인용
    ``dao/refund/TicketDetailDao.java:123-142`` 는 7.0.6 에 없는 경로였습니다.
    ``TicketDetailOut.java:49`` 의 필드 ``dcntCrdInfo`` 로 달려 오고 와이어
    키는 ``TicketDetailOut.java:438`` 의 ``@SerialName("dcnt_crd_info")``
    입니다 — 예전 인용 ``:233`` 은 없어진 Dao 의 줄번호였습니다. 읽고 있는
    "승차권"이 실은 카드일 때만 있고, 보통 승차권에는 이 객체가 없습니다.

    :attr:`card_no` 를 얻으려고 있는 모델입니다.
    :meth:`~korail_mobile_api.client.KorailClient.get_discount_card_usage_history`
    의 유일한 입력이고, N카드 할인종류 코드와 함께 평범한 예약을 할인 예약으로
    바꾸는 유일한 입력이기도 합니다. 원래 인용 ``w4/a.java:100-101`` 은 7.0.6
    에 없는 경로이고, 실제 조립 지점은 ``Passengers.java:766`` 입니다 —
    ``screenMode == ReservationType.MY_N_CARD_RESERVATION`` 일 때만
    ``TicketReservationInPassengerInfo``(``:26-34``)의 ``txtDiscKndCd`` 에
    ``ReqDiscount.N_CARD.getDiscKndCd()``(``ReqDiscount.java:36``)를,
    ``txtCardNo`` 에 카드번호를 넣고 그 밖에는 카드번호를 ``''`` 로 둡니다.
    ``ReqDiscount.N_CARD`` 의 코드 리터럴 자체는 AlienGuard 로 보호되어
    디컴파일로는 읽을 수 없습니다 — 이 라이브러리가 쓰는
    :data:`~korail_mobile_api.constants.KORAIL_DISCOUNT_CARD_DISCOUNT_CODE`
    (``'153'``)는 라이브 관측에서 온 값이고 7.0.6 소스로 재확인된 것은
    아닙니다.
    :mod:`korail_mobile_api.redaction` 에 등록돼 있어 마스킹됩니다.
    """

    #: ``h_dcnt_crd_no``(``DiscountCardInfo.java:113`` 의 ``@SerialName``).
    card_no: str | None = field(default=None, repr=False)
    #: ``h_dcnt_crd_trm_extn_psb_flg``(``DiscountCardInfo.java:117`` 의
    #: ``@SerialName``, 필드는 ``:30``) — 기간연장이 가능하면 ``"Y"``.
    #: 앱에서 "기간연장" 버튼을 켜는 것도 이 값 하나입니다. 원래 인용
    #: ``Y4/C0907b.java:301`` → ``Y4/Q.java:1013-1026`` 은 7.0.6 에 없는
    #: 경로였습니다. 7.0.6 의 실제 지점은 smali 로만 보입니다(jadx 출력에는
    #: 이 람다가 남지 않았습니다):
    #: ``smali_classes6/.../detail/NCardTicketSectionKt.smali:7821-7843`` 이
    #: ``getDcntCrdInfo().getDcntCrdTrmExtnPsbFlg()`` 를 AlienGuard 1바이트
    #: 리터럴과 ``Intrinsics.areEqual`` 로 비교하고 그 결과를
    #: ``TicketDetailMediumContainerButton`` 의 ``enabled`` 인자로 넘깁니다.
    #: 비교 리터럴(``"Y"`` 로 추정)은 보호되어 확인 불가입니다.
    term_extension_possible_flag: str | None = None
    sections: tuple[DiscountCardSection, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class KorailPointSummaryResponse(BaseKorailResponse):
    """``xPoint.MyXPointView`` — 포인트·자격 요약.

    필드는 ``MyXPointViewOut.java:27-74`` 를 따릅니다. 이 DTO 는 43개 코틀린
    프로퍼티를 선언하고 ``@SerialName`` 은 ``CommonOut`` 에서 물려받는
    ``h_msg_cd``/``h_msg_txt`` 둘뿐이라, **프로퍼티 이름이 곧 와이어 키** 입니다.
    라이브 응답은 48키입니다(43 + 봉투 3 + DTO 밖 서버 추가 2:
    ``h_coup_sno1``/``srNoticeUrl``, 2026-09-22).

    이전 독스트링은 ``KorailPointInquiryDao.java`` 와 ``MyPageActivity.java`` 를
    인용했는데 두 파일 모두 7.0.6 디컴파일에 존재하지 않습니다(jadx 0건,
    apktool 0건) — 6.5.0 시절 경로가 남아 있던 것으로, ``DirectInquiryActivity``
    정리(989c93f)와 같은 부류입니다. 7.0.6 에서 이 DTO 를 실제로 참조하는 곳은
    ``MembershipViewModel.java``/``PrivacyManagerViewModel.java``/
    ``AuthInfoManagerViewModel.java``/``ManageLoginMethodViewModel.java`` 이며,
    모두 ``AppSuitLinker`` 리플렉션을 거쳐 필드에 닿습니다.

    ``h_hdcp_flg == "Y"`` 일 때 장애인 등록이 있습니다(``:52``).
    """

    #: ``h_korail_point`` — 마이페이지에 뜨는 코레일 포인트 잔액.
    korail_point: str | None = None
    #: ``h_disc_coup_cnt`` — 계정이 가진 할인쿠폰 개수.
    #: :meth:`~korail_mobile_api.client.KorailClient.get_discount_coupons` 가
    #: 실제로 돌려주는 목록의 개수입니다.
    discount_coupon_count: str | None = None
    #: ``h_delay_cnt`` — 계정이 가진 지연할인권 개수.
    delay_discount_count: str | None = None
    #: ``h_hdcp_flg`` — 장애인 등록이 있으면 ``"Y"``.
    disability_flag: str | None = field(default=None, repr=False)
    #: ``h_subt_dcs_cl_nm`` / ``h_subt_dcs_cl_cd`` — 그 등록이 주는 우대할인
    #: 등급. 앱에서 장애인증 라벨 아래 찍힙니다.
    welfare_discount_class_name: str | None = field(default=None, repr=False)
    welfare_discount_class_code: str | None = field(default=None, repr=False)
    #: ``h_cust_lead_flg_nm`` — 앱에서 보조견 라벨 아래 찍힙니다.
    customer_lead_flag_name: str | None = field(default=None, repr=False)
    #: ``h_cp_athn_flg`` / ``h_emil_athn_flg`` — 휴대폰·이메일 인증 여부.
    phone_verified_flag: str | None = field(default=None, repr=False)
    email_verified_flag: str | None = field(default=None, repr=False)
    contact_channel_content: str | None = field(default=None, repr=False)
    #: ``h_logn_tp_cd1``/``2``/``4``/``5`` — 소셜 로그인 연동 플래그.
    #:
    #: 네이버·카카오·구글·애플이라는 **순서는 7.0.6 에서 확인되지 않았습니다.**
    #: 6.5.0 시절 판단을 그대로 옮겨 온 것이고, 예전에 근거로 달려 있던
    #: ``MyPageActivity.java:214-236`` 은 7.0.6 디컴파일에 존재하지 않는
    #: 파일입니다. ``MyXPointViewOut`` 자신과 그 smali 말고는 ``logn_tp_cd`` 를
    #: 언급하는 파일이 없고, 실제 소비자 네 ViewModel 은 ``AppSuitLinker``
    #: 리플렉션으로 필드에 닿으며 ``LoginMethodApiData`` 의 필드는 난독화돼
    #: 있습니다(``LoginMethodApiData.java:18-21``의 ``STLgde``~``STLgdh``,
    #: 내용도 이메일·휴대폰 인증뿐). 확정하려면 소셜 하나를 실제로 연동한 뒤
    #: 어느 인덱스가 뒤집히는지 보는 A/B 가 필요합니다 — 그전까지 이 이름들을
    #: 신뢰하지 마십시오.
    naver_linked_flag: str | None = field(default=None, repr=False)
    kakao_linked_flag: str | None = field(default=None, repr=False)
    google_linked_flag: str | None = field(default=None, repr=False)
    apple_linked_flag: str | None = field(default=None, repr=False)
    # 새 필드는 끝에 덧붙입니다(위치 인자 의미 보존).
    #: ``h_cust_lead_flg``(``MyXPointViewOut.java:43``) — 보조견 등록 플래그
    #: 그 자체. 사람이 읽는 짝 :attr:`customer_lead_flag_name`(``:44``)만 있고
    #: 플래그가 없어, 라벨 문자열을 파싱해야 자격 여부를 알 수 있었습니다.
    customer_lead_flag: str | None = field(default=None, repr=False)
    #: ``h_hdcp_tp_cd``/``h_hdcp_tp_cd_nm``(``:53,54``) — 장애 유형 코드와 이름.
    #: :attr:`disability_flag`(``h_hdcp_flg``)는 "등록이 있는가"만 말하고
    #: 유형은 이 둘에 있습니다. 셋 다 라이브 응답에 옵니다(2026-09-22).
    disability_type_code: str | None = field(default=None, repr=False)
    disability_type_name: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class MileageHistoryEntry:
    """마일리지 내역의 적립 또는 사용 한 줄.

    ``AmtSpecOutSpecInfo.java:29-35`` 가 선언하는 것이 정확히 아래 일곱
    필드입니다. 예전 인용 ``dao/xPoint/MileageInquiryDao.java:128-167`` 은 7.0.6
    디컴파일에 없는 파일이었습니다(jadx·apktool 양쪽 0건) — 6.5.0 잔재이며
    ``DirectInquiryActivity`` 정리(989c93f)와 같은 부류입니다. 값 자체는
    맞았습니다: 2026-09-22 라이브에서 3페이지 14행 전부가 이 일곱 키를
    문자열로 싣고 그 밖의 키는 없었습니다.
    """

    #: ``dptDt`` — 이 줄이 귀속된 출발일.
    departure_date: str | None = None
    #: ``pontDvNm`` — 적립/사용 구분 이름.
    point_division_name: str | None = None
    #: ``mlgAcmDvCdNm`` — 어떤 방식으로 적립됐는지.
    accrual_division_name: str | None = None
    #: ``rcpDvNm`` — 수납 구분 이름.
    receipt_division_name: str | None = None
    #: ``pontAmt`` — 이 줄의 포인트 증감. 부호가 붙습니다.
    point_amount: str | None = None
    #: ``savePontValNum`` — 이 줄 시점의 누적 잔액.
    saved_point_value: str | None = field(default=None, repr=False)
    #: ``stlAmt`` — 이 줄이 나온 정산 운임.
    settlement_amount: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """``mlg.amtSpec.do`` — 마일리지 적립/사용 내역 한 페이지.

    ``AmtSpecOut.java:29-39``(게터 ``:199-247``)가 선언하는 것은 스칼라 9개 +
    ``specList`` 이고, 아래 열 필드가 그것과 1:1 입니다. 예전 인용
    ``dao/xPoint/MileageInquiryDao.java:72-126`` 과
    ``MileageHistoryActivity.java`` 는 둘 다 7.0.6 디컴파일에 없는 파일입니다 —
    :class:`MileageHistoryEntry` 와 같은 6.5.0 잔재였습니다.

    :attr:`total_available_rail_point` 와 :attr:`total_available_rail_point_1` 을
    하나로 합치지 않는 이유는 여기서 다시 근거를 댈 수 없습니다 — "앱이 둘을
    각각 찍고 더한다"는 설명의 출처였던 ``MileageHistoryActivity.java:574-578``
    이 존재하지 않기 때문입니다. 지금 근거는 DTO 뿐입니다: ``AmtSpecOut`` 이
    둘을 **별개 필드로** 선언하므로 별개로 내놓습니다.

    서버는 DTO 밖의 키 ``railNowSavePontValNum1`` 을 모든 응답에 함께
    보냅니다(2026-09-22: KTX·RAIL_POINT 원장, 3개 페이지 전부에서 9자 문자열,
    이 계정에서는 ``totAcmRailPontValNum1`` 과 같은 값). ``AmtSpecOut`` 도
    ``AmtSpecOutSpecInfo`` 도 이 키를 선언하지 않아 모델링하지 않으며,
    :attr:`~korail_mobile_api.models.BaseKorailResponse.raw` 로 닿을 수 있습니다.
    """

    #: ``pgCnt`` — 전체 페이지 수(``AmtSpecOut.java:32``).
    page_count: str | None = None
    query_count: str | None = None
    total_available_rail_point: str | None = None
    total_available_rail_point_1: str | None = None
    total_available_affiliate_point: str | None = None
    total_accumulated_rail_point_1: str | None = field(
        default=None,
        repr=False,
    )
    total_used_rail_point_1: str | None = field(default=None, repr=False)
    #: ``delPontValNum`` — 이번 달에 소멸하는 포인트.
    expiring_point_value: str | None = None
    ktx_mileage_info: str | None = field(default=None, repr=False)
    entries: tuple[MileageHistoryEntry, ...] = ()


@dataclass(frozen=True)
class DiscountCardUsage:
    """할인카드(N카드)를 이미 쓴 여행 한 건.

    ``NCardHistoryInfo.java:22`` 는 ``@Serializable`` 만 있고 ``@SerialName`` 이
    한 개도 없어 **코틀린 프로퍼티 이름이 곧 와이어 이름** 입니다. 선언은 정확히
    여덟 개입니다(``:224`` ``copy(runDt1, custNm, dptStnNm, arvStnNm,
    apdUsrFlg, saleDt, saleSqno, saleWctNo)``).

    예전 인용 ``dao/research/NCardHistoryDao.java`` 와
    ``TicketNCardHistoryActivity.java`` 는 7.0.6 디컴파일에 없는 파일이었습니다.
    앱이 다섯 필드만 그린다는 관찰 자체는 7.0.6 에서도 맞습니다 —
    ``NCardHistoryScreenKt.java:431``(``custNm``), ``:439``(``runDt1`` 를
    ``yyyy.MM.dd`` 로 변환), ``:526,528``(``dptStnNm``→``arvStnNm``),
    ``:301``(``apdUsrFlg == "Y"``), 정렬은
    ``NCardHistoryViewModel.java:123,141``. 다만 **화면이 안 그린다는 것이
    모델링하지 않을 이유는 아닙니다**: 아래 :attr:`sale_date`/
    :attr:`sale_sequence`/:attr:`sale_window_no` 는 화면 호출 지점이 0건이지만
    DTO 가 선언하는 실제 와이어 필드이고, 예전에는 그 이유로 빠져 있었습니다.

    그 셋이 그대로
    :class:`~korail_mobile_api.read_payloads.OriginalTicketReference` 가 된다고
    **가정하지 마십시오.** 철자 계열이 다르고(``saleWctNo`` 대 ``h_orgtk_wct_no``)
    그 사슬은 검증된 적이 없습니다 — 이 계정으로는 ``tkUseList`` 가 채워지지
    않아(카드번호 네 종류 전부 ``ERR000100`` "조회된 자료가 없습니다",
    2026-09-22) 라이브로 확인할 수단 자체가 없었습니다.
    """

    #: ``custNm`` — 이 구간을 실제로 탄 사람의 이름.
    passenger_name: str | None = field(default=None, repr=False)
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    #: ``runDt1``, ``yyyyMMdd``.
    run_date: str | None = None
    #: ``apdUsrFlg`` — 카드 소유자가 아니라 **두 번째** 등록 사용자가 탔으면
    #: ``"Y"`` 입니다(N카드 2인용).
    additional_user_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    # 새 필드는 ``raw`` 뒤에 덧붙입니다(위치 인자 의미 보존).
    #: ``saleDt``/``saleSqno``/``saleWctNo`` — 이 사용 건의 바탕이 된 발매
    #: 일자·일련번호·창구번호(``NCardHistoryInfo.java:224``). 클래스
    #: 독스트링의 경고를 읽으십시오.
    sale_date: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    sale_window_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class DiscountCardUsageListResponse(BaseKorailResponse):
    """``ticket.dcntCrdUseQry.do`` — 카드가 쓰인 여행 목록.

    ``NCardHistoryOut.java:27,82`` 가 싣는 것은 ``@SerialName("tkUseList")``
    하나뿐이라, 전선에 없는 요약 필드를 이 모델도 만들어 붙이지 않습니다.
    예전 인용 ``dao/research/NCardHistoryDao.java:78-87`` 은 7.0.6 디컴파일에
    없는 파일이었습니다(주장 자체는 맞고 출처만 낡았습니다).
    """

    items: tuple[DiscountCardUsage, ...] = ()


@dataclass(frozen=True)
class DiscountCardScheduleTrain:
    """할인카드를 아직 쓸 수 있는 열차 하나.

    7.0.6 의 대응 DTO 는 ``NCardScheduleItem.java:25``(필드 ``:30-49``)
    입니다. 원래 인용은 ``NCardInquiryDao.TrainInfo``
    (``dao/research/NCardInquiryDao.java:144-236``)였는데 7.0.6 디컴파일에
    그 경로가 없습니다(6.5.0 잔재).

    ``stationInfo`` 는 일부러 없습니다. 그것은 앱이 중간 정차역 문자열로부터
    스스로 만들어 내는 ``android.text.Spanned`` 이지 전선에서 읽는 값이
    아닙니다. ``stationStringInfo`` 라는 전선 키 자체가 전 디컴파일에 0건이라
    더 이상 읽지 않습니다.

    ``NCardScheduleItem`` 은 20개 필드를 선언하는데
    (``NCardScheduleItem.java:30-49``; 생략형으로 적으면 직전에 인용한
    없는 경로 ``dao/research/NCardInquiryDao.java`` 를 가리키는 것으로
    읽힙니다) 파일 전체에
    ``@SerialName`` 이 0건이어서 코틀린 필드명을 최선으로 사용합니다. 다만
    "PROTECTED" 라는 표현은 정확하지 않습니다 — 난독화된 것이 아니라
    ``@SerialName`` 자체가 없어 kotlinx 기본값(= 프로퍼티 이름)이 곧 와이어
    철자인 경우입니다. 라이브 응답으로 재확인하기 전까지는 추정으로 두되,
    필드명을 "보호된 리터럴" 로 오해하지 마십시오.
    """

    train_no: str | None = None
    train_group_code: str | None = None
    run_date: str | None = None
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = None
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = None
    departure_station_order: str | None = field(default=None, repr=False)
    arrival_station_order: str | None = field(default=None, repr=False)
    #: ``dptStnRunOrdr`` — 승차역 "운행" 순서. ``departure_station_order``
    #: (``dptStnConsOrdr``, "편성" 순서)와는 다른 필드입니다.
    departure_run_order: str | None = field(default=None, repr=False)
    #: ``arvStnRunOrdr`` — 하차역 운행 순서.
    arrival_run_order: str | None = field(default=None, repr=False)
    #: ``chtnTrnOrdrNo`` — 환승 열차 순번.
    transfer_train_order_no: str | None = field(default=None, repr=False)
    #: ``prcClCd`` — 운임 구분 코드.
    price_class_code: str | None = None
    #: ``stlbCarTpCd``/``stlbTrnClsfCd`` — 정산용 호차·열차 종류 코드.
    settlement_car_type_code: str | None = field(default=None, repr=False)
    settlement_train_class_code: str | None = field(default=None, repr=False)
    #: ``cmtrPrc`` — 이 카드의 구간에 매겨진 운임.
    commuter_price: str | None = None
    direct_transfer_division_code: str | None = field(default=None, repr=False)
    detour_code: str | None = field(default=None, repr=False)
    detour_name: str | None = field(default=None, repr=False)
    route_code: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DiscountCardScheduleResponse(BaseKorailResponse):
    """``research.dcntCrdScheduleView.do`` — 카드로 예약할 수 있는 열차들.

    7.0.6 의 라우트 선언은 ``NetworkApi.java:339-341``
    (``@FormUrlEncoded @POST(".../research.dcntCrdScheduleView.do")
    postDcntCrdScheduleView(@FieldMap …) → NCardScheduleOut``)이고 응답 DTO 는
    ``NCardScheduleOut.java:27-28`` 입니다. 원래 인용
    ``NCardInquiryDao.NCardInquiryResponse``
    (``dao/research/NCardInquiryDao.java:128-142``)는 7.0.6 디컴파일에 없는
    경로였습니다 — 라우트가 같다는 것이 그 옛 클래스의 필드까지 같다는 뜻은
    아니므로, 아래 설명의 근거는 ``NCardScheduleOut`` 자신입니다.

    :attr:`following_page_exists` 는 더 이상 채워지지 않습니다. 7.0.6 의
    ``NCardScheduleOut.java:27-28`` 은 ``trnScdlList`` 하나만 선언할 뿐
    ``fllwPgExt`` 를 갖지 않습니다 — 그 키는 다른 DTO(``ScdlQryOut``, 리무진
    일정)의 필드입니다. ``NCardScheduleOut`` 자체에는 대체할 다른 페이징
    신호도 없어(정확히 이 한 필드만 선언), 이 라우트의 서버측 페이징 여부는
    현재 미확인입니다 — 항상 ``None`` 인 이 필드를 폴링 신호로 쓰지
    마십시오.
    """

    #: 항상 ``None``. 아래 클래스 독스트링 참고.
    following_page_exists: str | None = None
    trains: tuple[DiscountCardScheduleTrain, ...] = ()


@dataclass(frozen=True)
class MultiChildDiscountTarget:
    birth_date: str | None = field(default=None, repr=False)
    customer_family_name: str | None = field(default=None, repr=False)
    discount_kind_code: str | None = None
    family_sequence: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = None
    passenger_type_name: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    requested_discount_kind_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MultiChildDiscountTargetResponse(BaseKorailResponse):
    targets: tuple[MultiChildDiscountTarget, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class CustomerTripInfo:
    additional_seat_attribute_code: str | None = None
    adult_disabled_person_count: str | None = None
    adult_count: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    baby_accompanying_person_count: str | None = None
    changed_at: str | None = None
    changed_by: str | None = field(default=None, repr=False)
    child_count: str | None = None
    child_disabled_person_count: str | None = None
    customer_management_no: str | None = field(default=None, repr=False)
    day_code: str | None = None
    direction_seat_attribute_group_code: str | None = None
    direct_transfer_division_code: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    early_train_departure_time: str | None = None
    elderly_person_count: str | None = None
    included_flag: str | None = None
    job_start_hour: str | None = None
    location_seat_attribute_group_code: str | None = None
    media_division_code: str | None = None
    room_class_code: str | None = field(default=None, repr=False)
    passenger_total: str | None = None
    registered_at: str | None = None
    registration_sequence: str | None = None
    registered_by: str | None = field(default=None, repr=False)
    trip_day_no: str | None = None
    train_classification_code: str | None = None
    train_connection_flag: str | None = None
    train_group_code: str | None = None
    usage_day_no: str | None = None
    #: ``gdNo`` — 상품번호. ``CustTripInfo.java`` 33필드 중 마지막으로
    #: 빠져 있던 필드. ``@SerialName`` 이 없어 와이어 철자는 PROTECTED 이며
    #: 코틀린 필드명을 최선으로 사용합니다.
    goods_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class CustomerTripInfoResponse(BaseKorailResponse):
    trips: tuple[CustomerTripInfo, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class MaasServiceDetailInfo:
    additional_service_request_no: str | None = field(default=None, repr=False)
    booking_time: str | None = None
    branch_name: str | None = None
    partner_name: str | None = None
    delivery_datetime: str | None = None
    drop_times: str | None = None
    dropoff_name: str | None = None
    image: str | None = field(default=None, repr=False)
    name: str | None = None
    option_name: str | None = None
    pickup_name: str | None = None
    pickup_place: str | None = None
    pickup_times: str | None = None
    reservation_date: str | None = None
    return_datetime: str | None = None
    start_datetime: str | None = None
    cancel_deadline_date: str | None = None
    cancel_return_amount: str | None = None
    cancel_return_fee: str | None = None
    goods_sequence: str | None = field(default=None, repr=False)
    intermediate_value: str | None = None
    received_amount: str | None = None
    reservation_status_name: str | None = None
    reservation_passenger_name: str | None = field(default=None, repr=False)
    settlement_deadline_date: str | None = None
    settlement_deadline_datetime: str | None = None
    settlement_status_code: str | None = None
    settlement_status_name: str | None = None
    total_settlement_amount: str | None = None
    usage_period_content: str | None = None
    entity_one: tuple[Mapping[str, Any], ...] = field(default=(), repr=False, compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MaasServiceDetail:
    additional_service_division_code: str | None = field(default=None, repr=False)
    additional_service_goods_code: str | None = field(default=None, repr=False)
    additional_service_id: str | None = field(default=None, repr=False)
    marketing_entity_id: str | None = field(default=None, repr=False)
    marketing_entity_name: str | None = field(default=None, repr=False)
    additional_service_name: str | None = field(default=None, repr=False)
    progress_status_code: str | None = field(default=None, repr=False)
    request_no: str | None = field(default=None, repr=False)
    passenger_reference_content: str | None = field(default=None, repr=False)
    partner_reservation_no: str | None = field(default=None, repr=False)
    delivery_close_time: str | None = field(default=None, repr=False)
    delivery_start_time: str | None = field(default=None, repr=False)
    lead_message_1: str | None = field(default=None, repr=False)
    lead_message_2: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    request_date: str | None = field(default=None, repr=False)
    request_quantity: str | None = field(default=None, repr=False)
    reservation_station_code_name: str | None = None
    reservation_specification_url: str | None = field(default=None, repr=False)
    usage_close_date: str | None = field(default=None, repr=False)
    usage_start_date: str | None = field(default=None, repr=False)
    detail_info: MaasServiceDetailInfo | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MaasServiceDetailListResponse(BaseKorailResponse):
    details: tuple[MaasServiceDetail, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class TripChangeDateResponse(BaseKorailResponse):
    """``reservation.tripChgDate.do``(``NetworkApi.java:238``) (``TipChgDateInquiryOut.java:28-30``).

    ``tripChgDate``(단수)는 **요청** DTO(``TipChgDateInquiryIn.java:29``)의
    필드입니다 — 응답은 복수형 ``tripChgDates``(``List<String>``)만
    선언하므로, 여기서는 단수형을 읽지 않습니다.
    """

    last_run_date: str | None = None
    trip_change_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommuterPassengerOption:
    """``Psg.java:28-33``, 6개 필드 중 4개만 있으면 연령 하한/상한이 없습니다."""

    commuter_usage_age_code: str | None = None
    common_code_name: str | None = None
    #: ``custAgeFrom``/``custAgeTo`` — 이 옵션이 적용되는 연령 하한/상한.
    customer_age_from: int = 0
    customer_age_to: int = 0
    passenger_count_from: int = 0
    passenger_count_to: int = 0
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class CommuterInfoResponse(BaseKorailResponse):
    additional_service_goods_flag: str | None = None
    companion_flag: str | None = None
    commuter_kind_code: str | None = None
    #: ``cmtrUtlAgeCd`` — 보낸 코드의 에코가 **아닙니다.** 요청 DTO 는
    #: ``List<String>``(``CommutationInfoIn.java:31``)인데 응답 DTO 는 스칼라
    #: ``String`` 이라 애초에 에코가 될 수 없고, 7.0.6 앱도 이 최상위 값을
    #: 읽지 않습니다(``PassConditionViewModel.java:633,653`` 은 행 단위
    #: ``psg.getCmtrUtlAgeCd()`` 만 읽습니다). 실측 2026-09-22: 다중 행 상품
    #: ``0046`` 에서 ``E05`` 를 보내면 ``E06`` 이, ``E06`` 을 보내면 ``E05``
    #: 가 돌아왔습니다. 단일 행 상품은 승객 단계가 ``ERR000100`` 으로
    #: 거부돼 "항상 다른 행을 준다" 는 일반 규칙까지는 확인하지 못했습니다.
    #: 고른 코드가 필요하면 **요청에 넣은 값**을 쓰십시오.
    commuter_usage_age_code: str | None = None
    menu_id: str | None = None
    popup_message: str | None = field(default=None, repr=False)
    promotion_message: str | None = None
    promotion_url: str | None = None
    seat_attribute_code: str | None = None
    available_passenger_count_from: int = 0
    available_passenger_count_to: int = 0
    passenger_options: tuple[CommuterPassengerOption, ...] = ()


@dataclass(frozen=True)
class PriceFare:
    journey_sequence: str | None = None
    room_class_name: str | None = field(default=None, repr=False)
    received_fare: str | None = None
    received_price: str | None = None
    total_amount: str | None = None
    train_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PriceFareQuoteResponse(BaseKorailResponse):
    fares: tuple[PriceFare, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    acceptance_customer_management_no: str | None = field(
        default=None,
        repr=False,
    )
    acceptance_customer_name: str | None = field(default=None, repr=False)
    acceptance_customer_phone: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    #: ``rsvCnt`` — ``TicketDupCheckOut.java:28`` 의 선언은 ``String`` 입니다.
    #: 예전 주석은 "Gson 이 DAO 의 Java int 를 강제 변환한다" 고 적었지만 이
    #: DTO 는 kotlinx이고 끝까지 String 입니다 — 지금까지는 동작이 중립이었을
    #: 뿐(둘 다 ASCII-decimal 문자열을 받아들이므로), 그 잘못된 근거를 믿고
    #: 나중에 문자열 처리 경로를 지우는 사고를 막기 위해 고칩니다.
    reservation_count: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class PbpAcceptanceSeat:
    passenger_type_division_name: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    car_no: int = field(default=0, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PbpAcceptanceJourney:
    acceptance_customer_name: str | None = field(default=None, repr=False)
    acceptance_customer_phone: str | None = field(default=None, repr=False)
    journey_type_code: str | None = field(default=None, repr=False)
    member_division_name: str | None = field(default=None, repr=False)
    acceptance_kind_name: str | None = field(default=None, repr=False)
    pbp_reservation_no: str | None = field(default=None, repr=False)
    registered_date: str | None = field(default=None, repr=False)
    withdrawal_possible_flag: str | None = field(default=None, repr=False)
    seats: tuple[PbpAcceptanceSeat, ...] = field(default=(), repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PbpAcceptanceTicket:
    pnr_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    sale_window_no: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    journeys: tuple[PbpAcceptanceJourney, ...] = field(default=(), repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    tickets: tuple[PbpAcceptanceTicket, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """자율 좌석 변경으로 옮겨 갈 수 있는 승차역 하나.

    7.0.6 의 대응 DTO 는 ``ChgStnInfo.java:21-35`` 입니다(``String`` 14개,
    ``@SerialName`` 0건이므로 프로퍼티 이름이 곧 와이어 키).
    ``SeatAvailabilityOut.java:32`` 의 ``List<ChgStnInfo> chgStnList`` 로
    실려 옵니다. 원래 인용 ``CallSelfSeatChgInfoDao.ChgStnList``
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:157-204``)는 7.0.6
    디컴파일에 없는 경로였습니다(6.5.0 잔재).
    아래 열 속성은 그 14개 중 열과 맞습니다 — 나머지 넷
    (``arvRsStnCd``/``arvRsStnNm``/``arvStnConsOrdr``/``arvStnRunOrdr``)은
    DTO 가 선언하지만 이 모델이 아직 읽지 않습니다.

    이 줄을 고를 수 있는지는 좌석 수 둘이 정합니다 —
    :attr:`general_remaining_seats`(``gnrmRestSeatNum``)와
    :attr:`special_remaining_seats`(``sprmRestSeatNum``)가 이 역에서 시작하는
    구간의 일반실·특실 잔여 좌석입니다.
    """

    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    departure_construction_order: str | None = None
    departure_run_order: str | None = None
    general_remaining_seats: str | None = None
    special_remaining_seats: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class SelfSeatChangeReason:
    """좌석 변경 사유 한 줄(``ChgRsnInfo.java:21-24``).

    ``String`` 셋(``frcSaleRsnCont``/``qryCode``/``qryOrdr``)뿐이고
    ``@SerialName`` 은 0건이라 프로퍼티 이름이 곧 와이어 키입니다. 아래 세
    속성과 1:1 입니다. ``SeatAvailabilityOut.java:31`` 의
    ``List<ChgRsnInfo> chgRsnList`` 로 옵니다. 원래 인용
    ``CallSelfSeatChgInfoDao.java:136-155`` 는 7.0.6 디컴파일에 없는
    경로였습니다.
    """

    query_code: str | None = None
    query_order: str | None = None
    reason_text: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """``self.seatChgInfo.do`` — 자율 좌석·열차 변경이 무엇으로 바뀔 수 있는지.

    7.0.6 의 라우트 선언은 ``NetworkApi.java:806-808``
    (``@FormUrlEncoded @POST(".../self.seatChgInfo.do")
    seatAvailabilityCall(@FieldMap …) → SeatAvailabilityOut``)이고 응답 DTO 는
    ``SeatAvailabilityOut.java:28-42`` 입니다 — 스칼라 ``String`` 12개 +
    ``chgRsnList``/``chgStnList`` 두 목록으로, 아래 필드 구성과 1:1 입니다.
    봉투 밖 ``@SerialName`` 은 ``CommonOut`` 에서 물려받는
    ``h_msg_cd``/``h_msg_txt`` 둘뿐(``:68``)이라 나머지는 프로퍼티 이름이 곧
    와이어 키입니다. 원래 인용
    ``CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse``
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:64-134``)는 7.0.6
    디컴파일에 없는 경로였습니다.

    :attr:`general_reservation_possible_code` /
    :attr:`special_reservation_possible_code`
    (``gnrmRsvPsbCd``/``sprmRsvPsbCd``)는 객실 등급별 **열차 단위**
    가부입니다. 역별 잔여 좌석은 :attr:`stations` 쪽에 있습니다.
    """

    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    train_group_code: str | None = None
    train_group_name: str | None = None
    run_date: str | None = None
    general_reservation_possible_code: str | None = None
    special_reservation_possible_code: str | None = None
    change_before_departure_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    change_before_arrival_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    existing_departure_run_order: str | None = field(
        default=None,
        repr=False,
    )
    existing_arrival_run_order: str | None = field(
        default=None,
        repr=False,
    )
    stations: tuple[SelfSeatChangeStation, ...] = ()
    reasons: tuple[SelfSeatChangeReason, ...] = ()


@dataclass(frozen=True)
class OriginalTicketSeat:
    """원표의 한 여정에 딸린 좌석 하나(``SeatInfo.java:25-51``).

    원래 인용은 ``response/research/Seat.java`` 였습니다. 7.0.6 에 그 경로는
    없고, **같은 basename 의 ``model/Seat.java`` 를 대신 인용하면 안 됩니다** —
    그 ``Seat``(``Seat.java:27-36``)는 필드가 다섯이고 ``scarNo`` 가 ``int``
    이며, PBP(대리수령) 응답 계열(``DeliveredTicketOut`` → ``Tk`` → ``Jrny``)에
    딸린 전혀 다른 구조입니다. 원표 조회의 좌석은
    ``JrnyInfo.java:58`` 의 ``List<SeatInfo> seatList`` 이고 그 원소가
    ``SeatInfo.java:25``(필드 ``:30-51``, ``String`` 22개)입니다 — 아래 열다섯
    속성이 그 22개 중 열다섯과 맞습니다.

    좌석 식별자 자체(``scarNo``/``seatNo``)는
    :mod:`korail_mobile_api.redaction` 에 등록돼 있습니다.
    """

    passenger_sequence: str | None = None
    assign_sequence: str | None = None
    passenger_type_code: str | None = None
    room_class_code: str | None = field(default=None, repr=False)
    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    seat_count: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    requested_seat_attribute_code: str | None = None
    direction_seat_attribute_code: str | None = None
    location_seat_attribute_code: str | None = None
    smoking_seat_attribute_code: str | None = None
    additional_seat_attribute_code: str | None = None
    etc_seat_attribute_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class OriginalTicketJourney:
    """원표의 구간 하나(``JrnyInfo.java:29-63``).

    원래 인용은 ``response/research/Jrny.java`` 였습니다. 7.0.6 에 그 경로는
    없고, **같은 basename 의 ``model/Jrny.java`` 로 바꿔 인용하면 안 됩니다** —
    그 ``Jrny``(``Jrny.java:29-38``)의 필드는 ``acepCustNm``/``acepCustTeln``/
    ``pbpAcepKndNm``/``pbpRsvNo``/``wdrwPsbFlg`` 같은 PBP(대리수령) 접수
    정보이고 ``Tk.java:27`` 이 담는 다른 응답 계열입니다. 원표 조회의 구간은
    ``OrgTk.java:38`` 의 ``List<JrnyInfo> jrnyList`` 이고 그 원소가
    ``JrnyInfo.java:29``(필드 ``:30-63``, ``String`` 33개 + ``:58`` 의
    ``List<SeatInfo> seatList``)입니다.

    변경 흐름이 이 줄을 열쇠로 삼습니다 — ``jrnySqno`` 와 출발·도착 역코드·
    운행순서가 뒤따르는 조회들이 그대로 요구하는 인자입니다.
    """

    journey_sequence: str | None = None
    journey_order: str | None = None
    #: ``jrnyTpCd``. 전선 철자와 속성 철자 양쪽이 민감 키로 등록돼 있어, 이
    #: 값을 드러내는 다른 모델과 마찬가지로 표현에서 뺍니다.
    journey_type_code: str | None = field(default=None, repr=False)
    train_no: str | None = None
    train_group_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_construction_order: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    arrival_construction_order: str | None = None
    goods_no: str | None = None
    total_seat_count: str | None = None
    total_standing_count: str | None = None
    general_change_allowed_flag: str | None = None
    single_ticket_flag: str | None = None
    seats: tuple[OriginalTicketSeat, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class OriginalTicket:
    """원표 하나(``OrgTk.java:28-52``).

    원래 인용 ``response/research/OrgTk.java`` 는 7.0.6 에 없는 경로였습니다.
    7.0.6 의 같은 이름 ``model/OrgTk.java`` 가 이번에는 실제로 같은 구조입니다
    — ``String`` 21개 + 목록 셋(``cmpnList``/``jrnyList``/``stlList``)이고
    ``@SerialName`` 은 0건이므로 프로퍼티 이름이 곧 와이어 키입니다.
    ``OgTicketInquiryOut.java:27`` 의 ``List<OrgTk> orgTkList`` 로 옵니다.

    ``original_*`` 네 값은 승차권 자신의 반환번호가 되돌아온 것입니다 — 요청이
    보낸 것과 같은 비밀이라 전선 철자와 속성 철자 양쪽에서 마스킹됩니다.

    ``cmpnList``(동반 할인, ``OrgTk.java:32`` → ``Cmpn.java:29-44``)와
    ``stlList``(정산 줄, ``OrgTk.java:51`` → ``Stl.java:29-40``)는 일부러
    :attr:`raw` 에만 남깁니다. 지연증명 반환번호
    (``Cmpn.java:35-38`` 의 ``dlayOgtkRetPwd``/``dlayOgtkSaleDt``/
    ``dlayOgtkSaleSqno``/``dlayOgtkWctNo``), 카드번호
    (``Stl.java:32,37`` 의 ``prepCrdNo``/``stlCrdNo``), 승인번호
    (``Stl.java:29`` 의 ``apvNo``) 같은 자격증명이 더 들어
    있는데 변경 흐름에는 쓸 일이 없기 때문입니다.

    **``raw`` 는 마스킹되지 않습니다.** 그 전선 키들이
    :mod:`korail_mobile_api.redaction` 에 등록돼 있다는 것은 마스킹 함수가
    그 이름을 안다는 뜻일 뿐이고, 파서는 원본 매핑을 **그대로** 보존합니다 —
    로그나 예외에 실을 생각이면 호출자가
    :func:`~korail_mobile_api.redaction.redact_mapping` 을 직접 불러야
    합니다. 파서 쪽 문서는 처음부터 그렇게 적고 있었고, 여기만 반대로
    말하고 있었습니다.
    """

    pnr_no: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    original_sale_datetime: str | None = field(default=None, repr=False)
    original_window_no: str | None = field(default=None, repr=False)
    original_sale_sequence: str | None = field(default=None, repr=False)
    original_return_password: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)
    adult_count: str | None = None
    child_count: str | None = None
    group_discount_count: str | None = None
    passenger_type_division_code: str | None = None
    received_amount: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    change_sale_transaction_no: str | None = field(default=None, repr=False)
    sms_send_flag: str | None = None
    forced_sale_reason_text: str | None = None
    journeys: tuple[OriginalTicketJourney, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class OriginalTicketInquiryResponse(BaseKorailResponse):
    """``research.tripChgOgtk.do`` — 변경이 출발점으로 삼을 원표들.

    7.0.6 의 라우트 선언은 ``NetworkApi.java:234-236``
    (``@FormUrlEncoded @POST(".../research.tripChgOgtk.do")
    getTicketOriginalInquiry(@FieldMap …) → OgTicketInquiryOut``)이고 응답
    DTO 는 ``OgTicketInquiryOut.java:26-27`` — ``List<OrgTk> orgTkList`` 하나뿐
    입니다(봉투 ``h_msg_cd``/``h_msg_txt`` 는 ``CommonOut`` 에서, ``:54``).
    원래 인용 ``OgTkInquiryDao.OgTkInquiryResponse``
    (``dao/research/OgTkInquiryDao.java:38-46``)는 7.0.6 디컴파일에 없는
    경로였습니다 — 라우트가 같다는 것만으로 옛 클래스의 필드 구성까지
    같다고 볼 수는 없으므로, 근거는 ``OgTicketInquiryOut`` 자신입니다.
    """

    tickets: tuple[OriginalTicket, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class RecentDeliveryRecipient:
    acceptance_customer_management_flag: str | None = field(
        default=None,
        repr=False,
    )
    acceptance_customer_management_no: str | None = field(
        default=None,
        repr=False,
    )
    acceptance_customer_name: str | None = field(default=None, repr=False)
    acceptance_customer_phone: str | None = field(default=None, repr=False)
    acceptance_customer_phone_2: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    changed_acceptance_reservation_no: str | None = field(default=None, repr=False)
    recipients: tuple[RecentDeliveryRecipient, ...] = field(
        default=(),
        repr=False,
    )


@dataclass(frozen=True)
class ReservationSeatDetail:
    """보류된 예약의 좌석 한 줄(``seat_infos.seat_info[]``).

    필드 이름은 ``ReservationOutSeatInfo.java:33``(``@SerialName`` 전체 집합은
    합성 생성자 ``:81``)을 따릅니다. 예전 인용
    ``response/certification/ReservationResponse.java:296-313`` 은 7.0.6
    디컴파일에 없는 파일입니다.

    :attr:`passenger_type_name` 은 ``ReservationOutSeatInfo.java:81`` 의
    ``@SerialName`` 집합에는 없지만
    실재하는 키입니다. 예전 주석은 "``h_psg_tp_dv_nm`` 은 디컴파일된 앱 어디에도
    없다 → 서드파티가 지어낸 이름이다" 라고 적었는데 **두 전제가 다 틀렸습니다.**
    ``grep -r h_psg_tp_dv_nm analysis/`` 는 2건을 돌려줍니다 —
    ``BasketTicketDataKt.java:44``(와 그 smali 쌍둥이
    ``smali_classes6/.../BasketTicketDataKt.smali:89``)에 박혀 있는, 앱이 직접
    떠 둔 **이 응답의 실제 캡처** 이고, 그 안의
    ``/jrny_infos/jrny_info[*]/seat_infos/seat_info[0]`` 에 ``'어른'`` 으로
    들어 있습니다. 라이브에서도 8/8 좌석 행이 ``h_psg_tp_cd='1'`` 옆에
    ``h_psg_tp_dv_nm='어른'`` 을 싣습니다(2026-09-22).

    운임 재계산 요청의
    :class:`~korail_mobile_api.mutation_models.PriceRecalculationRow` 는 이
    줄에서 앞의 세 값을 그대로 베낍니다.
    """

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = field(default=None, repr=False)
    #: ``h_rcvd_amt`` — 이 좌석에 실제로 걷히는 금액. 예약 응답에
    #: ``h_tot_rcvd_amt`` 가 없을 때 결제 경로가 ``hidMnsStlAmt1`` 을 이 값들의
    #: 합으로 구하므로, 정산 금액을 다른 출처로 대조해 볼 수 있습니다.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    #: ``h_tot_disc_amt`` — 이 좌석의 총 할인액. 형제 금액 필드(수령액·좌석가·
    #: 좌석운임)와 함께 있었는데 이 필드만 빠져 있었습니다. 같은 와이어 키를
    #: ``_REFUND_TICKET_DETAIL_FIELDS`` 가 ``total_discount_amount`` 로 매핑하는
    #: 것과 이름을 맞춥니다.
    total_discount_amount: str | None = None
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    # 새 필드는 ``raw`` 뒤에 덧붙입니다(위치 인자 의미 보존).
    #: ``h_psg_tp_dv_nm`` — :attr:`passenger_type_code` 의 사람이 읽는 짝.
    #: 클래스 독스트링 참고.
    passenger_type_name: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class ReservationDetailJourney:
    """보류된 예약의 여정 하나(``jrny_infos.jrny_info[]``)."""

    journey_sequence: str | None = None
    journey_type_code: str | None = field(default=None, repr=False)
    reservation_change_no: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    #: ``h_arv_dt`` — 도착일. ``arrival_time``(``h_arv_tm``)과 별개 필드라,
    #: 심야·익일 도착 열차에서 도착 시각을 고정할 날짜가 이 필드 없이는
    #: 없었습니다.
    arrival_date: str | None = None
    departure_station_name: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    train_class_name: str | None = None
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR 로 다시 읽은 보류 예약(``certification.ReservationList``).

    응답 타입이 예약 요청이 돌려주는 것과 같은 ``ReservationOut``
    입니다(``ReservationOut.java``; 예전에 여기 적혀 있던
    ``ReservationResponse`` 는 7.0.6 에 없는 이름입니다 — 2026-09-23 정정).
    그래서 이 조회는 이 패키지가 이미 만들 수 있는 예약을 **다른 출처로**
    다시 보는 셈이고, 창구번호(``h_wct_no``)와 결제 폼이 정산할 좌석별
    금액을 여기서 확인할 수 있습니다.
    """

    pnr_no: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    journey_count: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 정산 합계. 결제 폼의 ``hidMnsStlAmt1`` 을 예약
    #: 응답이 아닌 출처로 대조할 수 있습니다.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    journeys: tuple[ReservationDetailJourney, ...] = ()


@dataclass(frozen=True)
class RefundCommissionResponse(BaseKorailResponse):
    """원표 하나의 환불 수수료와 환불액.

    필드는 ``RefundCommissionOut.java:30``(필드 ``:35-41``)을 따릅니다 —
    라우트는 ``NetworkApi.java:598-600``
    (``@POST(".../refunds.CommissionView") → RefundCommissionOut``)입니다.
    원래 인용 ``RefundCommissionDao.RefundCommissionResponse``
    (``dao/refund/RefundCommissionDao.java:70-77``)는 7.0.6 디컴파일에 없는
    경로였습니다. 아래 일곱 속성의 와이어 키는 모두 명시적
    ``@SerialName``(``RefundCommissionOut.java:140-164`` 의 애노테이션
    블록과 같은 파일 ``:62`` 의 합성 생성자 — 둘 사이에 없는 경로
    ``dao/refund/RefundCommissionDao.java`` 를 인용했으므로 생략형으로는
    따라갈 수 없습니다)에서 읽었습니다:
    ``ret_fee``/``ret_amt``/``h_msg_cd2``/``h_msg_txt2``/``prg_psb_flg``/
    ``use_psb_mlg_num``/``tk_ret_tms_dv_cd``. 보호되지 않은 리터럴이라
    프로퍼티 이름(``retFee`` 등)이 아니라 이 철자가 실제 전선 키입니다.

    "얼마가 돌아오고 수수료는 얼마인가"를 미리 보는 조회입니다. 실제 환불을
    보내기 전에 먼저 불러야 합니다.
    """

    #: ``ret_amt`` — 돌려받을 금액.
    refund_amount: str | None = None
    #: ``ret_fee`` — 거기서 떼는 수수료.
    refund_fee: str | None = None
    #: ``prg_psb_flg`` — 환불을 진행할 수 있는지 여부입니다.
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
    #: ``h_msg_cd2``/``h_msg_txt2`` — 이 경로가 봉투의 것과 별개로 싣는
    #: **두 번째** 메시지 짝. 성공한 사전 조회에 수수료 정책 안내가 붙는
    #: 식입니다.
    secondary_message_code: str | None = None
    secondary_message_text: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class RefundTicketSeat:
    """환불 대상 승차권의 좌석 하나(``tk_seat_info[]``)."""

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    buyer_name: str | None = field(default=None, repr=False)
    checkin_status_code: str | None = None
    discount_kind_code: str | None = None
    discount_kind_name: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = None
    passenger_type_name: str | None = field(default=None, repr=False)
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class RefundTicketJourney:
    """환불 대상 승차권의 여정 하나(``ticket_infos.ticket_info[]``)."""

    journey_sequence: str | None = None
    journey_type_code: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
    departure_station_name: str | None = field(default=None, repr=False)
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_station_name: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    train_class_name: str | None = None
    room_class_name: str | None = field(default=None, repr=False)
    platform_no: str | None = field(default=None, repr=False)
    seats: tuple[RefundTicketSeat, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class RefundTicketDetailResponse(BaseKorailResponse):
    """환불 대상 승차권의 상세(``refunds.SelTicketInfo``).

    필드는 ``TicketDetailOut.java:38`` 을 따릅니다(명시적 ``@SerialName`` 32개는
    합성 생성자 ``:117``, 나머지 필드는 ``@SerialName`` 이 없어 와이어 철자가
    PROTECTED 입니다). 예전 인용 ``dao/refund/TicketDetailDao.java:227-281`` 은
    7.0.6 디컴파일에 없는 파일이었습니다.

    두 조회가 사슬로 이어집니다. 앱은 :attr:`companion_name` 과
    :attr:`companion_birth_date` 를 뒤따르는 ``CommissionView`` 호출에 그대로
    넘깁니다(``MyTicketDetailViewModel.java:277`` 의 ``RefundCommissionIn(...,
    ticketDetailOut.getCompaNm(), ticketDetailOut.getCompaBrth(), ...)``; 예전
    인용 ``TicketListActivity.java:908-909`` 도 없는 파일이었습니다).

    환불 신원을 손으로 조립하지 말고
    :meth:`~korail_mobile_api.mutation_models.PaidTicket.from_refund_detail`
    에 이 응답을 넘겨야 합니다.

    ``mlgSaveFlg``/``mlgSaveTgt``(환불 시 마일리지 복구 여부)는 읽지 않습니다.
    7.0.6 디컴파일에는 0건이 맞습니다 — ``TicketDetailOut.java:39-91`` 에 해당
    필드가 없고 ``:117`` 의 32개 ``@SerialName`` 에도 없으며
    ``analysis/jadx/sources``·``analysis/apktool/smali_classes*`` grep 도 0건.
    하지만 **서버는 지금도 보냅니다** — 2026-09-22 라이브 40응답 전부가 두 키를
    싣고, 값은 언제나 빈 문자열이었습니다. 즉 "팬텀 키" 인 것은 **앱** 쪽이지
    전선 쪽이 아닙니다. 두 키는 :attr:`raw` 로 계속 닿을 수 있습니다.
    """

    pnr_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    sale_time: str | None = field(default=None, repr=False)
    window_name: str | None = field(default=None, repr=False)
    original_sale_date: str | None = field(default=None, repr=False)
    original_window_no: str | None = field(default=None, repr=False)
    original_sale_sequence: str | None = field(default=None, repr=False)
    original_return_password: str | None = field(default=None, repr=False)
    #: ``h_tk_knd_cd`` — 승차권 종류 코드. 개인정보가 아닙니다. 형제 클래스
    #: ``OriginalTicket``/``StationRefundOriginalTicket`` 에서도 평범한
    #: 필드라, 그쪽과 표시를 맞춥니다.
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    #: ``retPsbFlg``(``TicketDetailOut.java:71``) — **환불 가능 여부의 판정이
    #: 아닙니다.** 예전 주석은 "환불 전에 볼 수 있는 가장 싼 사전 점검"이라고
    #: 적었지만, 서버는 이미 반환된 승차권(``h_tk_stt_cd='09'``)과 승차일이
    #: 지난 승차권에도 ``'Y'`` 를 돌려줍니다 — 2026-09-22 라이브 40응답 전부가
    #: ``'Y'`` 였고, 같은 원표로 곧바로 ``refunds.CommissionView`` 를 부르면
    #: 5장은 ``WRT200022``("승차일이 경과되어 반환할 수 없습니다"), 2장은
    #: ``WRT200399``("반환된 승차권입니다")로 거절당합니다. 같은 승차권에 대해
    #: 목록 행의 :attr:`TicketListTicket.return_possible_flag`(``h_ret_psb_flg``)
    #: 는 ``'N'`` 이라고 말합니다(이력 143장 전부).
    #:
    #: 앱이 이 값을 혼자 쓰지 않는 것도 같은 이유입니다 — 환불 버튼은
    #: ``"Y".equals(retPsbFlg) && !TicketHelper.isUsedTicketInTrain(...)`` 로
    #: 켜지고(``NormalTicketSectionKt.java:951``) 그 화면은 **현재 승차권**
    #: 목록에서만 열리므로, 반환된 승차권의 ``'Y'`` 는 앱에서 한 번도 실행되지
    #: 않습니다. UI 활성화 힌트로만 쓰고, 정말 환불되는지는
    #: :meth:`~korail_mobile_api.client.KorailClient.get_refund_commission`
    #: 으로 확인하십시오.
    refund_possible_flag: str | None = None
    return_flag: str | None = None
    total_fare_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    train_running_flag: str | None = None
    #: ``h_abrd_ps_nm``/``s_brth`` — **탑승자 본인**의 성명·생년월일.
    #: ``h_compa_nm``/``h_compa_brth``(동승자 쌍, 아래)와는 별개의, 최상위
    #: 단일 필드 쌍입니다(``TicketDetailOut.java:410,418``). ``psgNmList``
    #: (아래 :attr:`passenger_names`, 승객 성명 **목록**)와도 서로 다른
    #: 필드입니다 — 요약 필드 하나와 목록 하나이지 같은 것의 중복이
    #: 아닙니다.
    passenger_name: str | None = field(default=None, repr=False)
    passenger_birth_date: str | None = field(default=None, repr=False)
    #: ``h_compa_nm``/``h_compa_brth`` — CommissionView 요청에
    #: ``h_comp_nm``/``h_comp_cert_no`` 로 그대로 복사돼 나갑니다.
    companion_name: str | None = field(default=None, repr=False)
    companion_birth_date: str | None = field(default=None, repr=False)
    #: ``pbpAcepTgtFlg`` — PBP(대리수령) 인수 대상 여부. **이 라우트에서는 항상
    #: ``None`` 입니다.**
    #:
    #: 서버가 보내지 않습니다: ``refunds.SelTicketInfo`` 응답 40건(승차권 20장 ×
    #: ``from_purchase_history`` 두 값, 2026-09-22)의 최상위 키 집합 어디에도
    #: ``h_pbp_acep_tgt_flg`` 도 ``pbpAcepTgtFlg`` 도 없습니다. 목록 행이
    #: ``'Y'`` 인 승차권 6장도 마찬가지였습니다.
    #:
    #: 그럴 수밖에 없습니다 — ``h_pbp_acep_tgt_flg`` 는 애초에 이 DTO 의
    #: ``@SerialName`` 이 아니라 ``MyTicketListOutTicket.java:92,300`` 의
    #: 것입니다. ``TicketDetailOut`` 쪽 ``pbpAcepTgtFlg`` 는 **세터가 있는
    #: 비-final 필드** 이고(``TicketDetailOut.java:65``, 세터 ``:1936``), 앱은
    #: SelTicketInfo 가 성공한 직후 목록 행의 값을 여기에 **주입** 한 뒤
    #: (``MyTicketBaseViewModel.java:769``) 환불 요청에 되돌려 넣습니다
    #: (``MyTicketDetailViewModel.java:1521``). 서버가 돌려줬다면 앱이 그 주입을
    #: 할 이유가 없습니다.
    #:
    #: 값이 필요하면 :attr:`TicketListTicket.pbp_acceptance_target_flag` 에서
    #: 가져오십시오 — 앱이 읽는 바로 그 자리입니다. 이 필드가 채워지는 경우는
    #: 서버가 언젠가 코틀린 필드명 ``pbpAcepTgtFlg`` 를 실어 보낼 때뿐입니다
    #: (파서가 그 철자를 폴백으로 계속 읽습니다).
    pbp_acceptance_target_flag: str | None = None
    #: ``h_dlay_flg``/``h_dlay_tk_flg`` — 지연 보상 대상 여부.
    delay_flag: str | None = None
    delay_ticket_flag: str | None = None
    #: ``addSrvFlg``/``addSrvCancel`` — 딸린 부가서비스가 있는지, 환불이 그것도
    #: 함께 취소하는지 여부.
    additional_service_flag: str | None = None
    additional_service_cancel: str | None = None
    #: ``h_qrcode`` — 이 승차권의 QR 코드(``TicketDetailOut.java:478``).
    qr_code: str | None = field(default=None, repr=False)
    #: ``psgNmList`` — 승객 성명 목록(``List<PsgNameInfo>``). ``@SerialName``
    #: 이 없어 와이어 철자는 PROTECTED, 코틀린 필드명을 최선으로 사용합니다.
    #: 각 원소는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다.
    passenger_names: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    #: ``seatTicketList`` — 좌석 배정 목록(``List<SeatAssignInfo>``, PROTECTED).
    seat_tickets: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    #: ``limousine`` — 연계된 리무진 예약(단일 객체, PROTECTED). 없으면 ``None``.
    limousine: Mapping[str, Any] | None = field(default=None, repr=False, compare=False)
    #: ``dtlList`` — 지연 정보 목록(``List<DelayInfo>``, PROTECTED).
    delay_details: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    journeys: tuple[RefundTicketJourney, ...] = ()
    #: ``dcnt_crd_info`` — 이 "승차권"이 실은 할인카드(N카드)일 때만 있습니다.
    #: 보통 승차권에서는 ``None`` 입니다.
    discount_card: DiscountCardOnTicket | None = None
