# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스·부가서비스 모델입니다. 공항버스 응답의 서버 코드는 알려지지 않은 값도 보존하기 위해 str로 둡니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..._core.parsing import wire
from ..common.models import BaseKorailResponse
from ..trains.models import SeatWindow

#: 공항버스 좌석 조회와 예약에 쓰는 호차 번호입니다. 앱 상수 ``DEFINE_SRCARNO``의 보호된 값입니다.
AIRPORT_BUS_CAR_NO = "0001"  # evidence: app 7.0.8 AirportBusSeatMapViewModel.java:101
# 앱 공항버스 화면이 보내는 보호된 값이며 2026-09-24 실서버 예약에서 받아들여졌습니다.
AIRPORT_BUS_ROOM_CLASS_CODE = "1"  # evidence: app 7.0.8 AirportBusSeatMapViewModel.java:752-788
AIRPORT_BUS_SEAT_ATTRIBUTE_CODE = "015"  # evidence: app 7.0.8 AirportBusSeatMapViewModel.java:752-788


@dataclass(frozen=True)
class AirportBusStop:
    """공통 코드 조회에서 짝지은 공항버스 정류장 코드와 이름입니다."""

    code: str
    name: str


@dataclass(frozen=True)
class AirportBusSchedule:
    """조회된 공항버스 한 편의 구간·운행·운임 정보를 담습니다."""

    arrival_date: str | None = wire("arvDt")
    arrival_station_code: str | None = wire("arvRsStnCd")
    arrival_run_order: str | None = wire("arvStnRunOrdr")
    arrival_time: str | None = wire("arvTm")
    transfer_division_code: str | None = wire("chtnDvCd")
    departure_date: str | None = wire("dptDt")
    departure_station_code: str | None = wire("dptRsStnCd")
    departure_run_order: str | None = wire("dptStnRunOrdr")
    departure_time: str | None = wire("dptTm")
    general_remaining_seat_count: str | None = wire("gnrmRestSeatNum")
    delay_minutes: str | None = wire("ocurDlayTnum")
    free_remaining_seat_count: str | None = wire("restFresNum")
    standing_remaining_seat_count: str | None = wire("restStndNum")
    run_date: str | None = wire("runDt")
    special_remaining_seat_count: str | None = wire("sprmRestSeatNum")
    settlement_train_class_code: str | None = wire("stlbTrnClsfCd")
    train_group_code: str | None = wire("trnGpCd")
    train_no: str | None = wire("trnNo")
    # 실서버 검증 못 함: 앱 속성 선언만 확인했습니다.
    train_order_no: str | None = wire("trnOrdrNo")
    # 앱 속성명은 ymsAplFlgYMS 이고, 전송 키 ymsAplFlg 는 실서버 관측입니다.
    yms_application_flag: str | None = wire("ymsAplFlg")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    #: 표시용 운임 문자열(``rcvdPrc``)입니다.
    received_price: str | None = wire("rcvdPrc")


@dataclass(frozen=True)
class AirportBusScheduleResponse(BaseKorailResponse):
    """공항버스 운행 스케줄 한 페이지를 담습니다."""

    following_page_extension: str | None = wire("fllwPgExt")
    long_short_division_code: str | None = wire("lgtmShtmDvCd")
    schedules: tuple[AirportBusSchedule, ...] = ()


@dataclass(frozen=True)
class AirportBusSeat:
    """공항버스 좌석표 한 자리의 식별자와 점유 상태를 담습니다."""

    direction_attribute_code: str | None = wire("dir_seat_att_cd")
    other_attribute_code: str | None = wire("etc_seat_att_cd")
    integrated_message: str | None = wire("intg_msg")
    integrated_message_code: str | None = wire("intg_msg_cd")
    requested_attribute_code: str | None = wire("rq_seat_att_cd")
    sale_possible_flag: str | None = wire("sale_psb_flg")
    seat_no: str | None = wire("seat_no")
    specification: str | None = wire("seat_spec")
    sequence_no: str | None = wire("sqr_no")
    visual_message_division_code: str | None = wire("vz_msg_dv_cd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class AirportBusSeatInventoryResponse(BaseKorailResponse):
    """공항버스 한 호차의 좌석표와 배치 정보를 담습니다.

    응답 형식은 열차 좌석 재고와 같으며, 창문 위치는 같은 ``SeatWindow``로 담습니다. 좌석 목록이 없거나 ``null``이면
    ``seats``는 빈 튜플입니다."""

    car_type_code: str | None = wire("car_tp_cd")
    car_no: str | None = wire("scar_no")
    seat_arrangement_code: str | None = wire("seat_ary_cd")
    up_down_division_code: str | None = wire("up_dn_dv_cd")
    layout_type: str | None = wire("layout_type")
    vr_banner_url: str | None = wire("vrBnrUrl")
    windows: tuple[SeatWindow, ...] = ()
    seats: tuple[AirportBusSeat, ...] = ()


@dataclass(frozen=True)
class MaasMenuItem:
    """부가서비스 메뉴 한 항목과 역 선택 조건을 담습니다."""

    active: str | None = wire("active")
    additional_service_code: str | None = wire("addSrvDvCd")
    app_data: str | None = wire("appData")
    icon_off: str | None = wire("iconOff")
    icon_on: str | None = wire("iconOn")
    info: str | None = wire("info")
    login_required: str | None = wire("login")
    name: str | None = wire("name")
    popup_image: str | None = wire("poppImg")
    menu_type: str | None = wire("type")
    url: str | None = wire("url")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)

    @property
    def uses_station_selection(self) -> bool:
        """메뉴가 역 선택을 사용하는지 판정합니다.

        ``active``가 ``"Y"``이고, ``menu_type``이 ``"N"``이 아니고, ``app_data``가 비어 있지 않으면서 ``"N"``도 아니고,
        ``additional_service_code``가 있을 때 ``True``입니다."""
        return (
            self.active == "Y"
            and self.menu_type != "N"
            # 실서버에서 역이 0개인 appData 는 'N'뿐이었고 'C'·'Y'·'M30'은 역이 있었으므로 허용 목록으로 좁히지 않습니다.
            and self.app_data not in (None, "", "N")
            and isinstance(self.additional_service_code, str)
            and bool(self.additional_service_code.strip())
        )


@dataclass(frozen=True)
class MaasMenuListResponse(BaseKorailResponse):
    """부가서비스 메뉴 목록을 담습니다."""

    items: tuple[MaasMenuItem, ...] = ()
    departure_elevator_url: str | None = wire("dElevatorUrl")
    departure_navigation_url: str | None = wire("dLeadNaviUrl")
    departure_parking_url: str | None = wire("dParkingLotUrl")
    arrival_elevator_url: str | None = wire("aElevatorUrl")
    arrival_bus_info_url: str | None = wire("aBisInfoUrl")
    arrival_parking_url: str | None = wire("aParkingLotUrl")
    arrival_baggage_transfer_robot_url: str | None = wire("aBggTrsfRbtUrl")


@dataclass(frozen=True)
class MaasServiceDetailInfo:
    """부가서비스의 상품·이용·결제 상세를 담습니다."""

    additional_service_request_no: str | None = wire("addSrvReqNo")
    booking_time: str | None = wire("bookTime")
    branch_name: str | None = wire("branchName")
    partner_name: str | None = wire("coptEntName")
    delivery_datetime: str | None = wire("deliveryDtm")
    drop_times: str | None = wire("dropTimes")
    dropoff_name: str | None = wire("dropoffName")
    image: str | None = wire("image")
    name: str | None = wire("name")
    option_name: str | None = wire("optionName")
    pickup_name: str | None = wire("pickupName")
    pickup_place: str | None = wire("pickupPlace")
    pickup_times: str | None = wire("pickupTimes")
    reservation_date: str | None = wire("reserveDt")
    return_datetime: str | None = wire("returnDttm")
    start_datetime: str | None = wire("startDttm")
    cancellation_deadline: str | None = wire("strCncDlnDt")
    cancellation_return_amount: str | None = wire("strCncRetAmt")
    cancellation_fee: str | None = wire("strCncRetFee")
    goods_sequence: str | None = wire("strGdSqno")
    intermediate_value: str | None = wire("strInt11")
    received_amount: str | None = wire("strRcvdAmt")
    reservation_status_name: str | None = wire("strRsvSttNm")
    reservation_passenger_name: str | None = wire("strRsvpsnm")
    settlement_deadline: str | None = wire("strStlDlnDt")
    settlement_deadline_datetime: str | None = wire("strStlDlnDttm")
    settlement_status_code: str | None = wire("strStlSttCd")
    settlement_status_name: str | None = wire("strStlSttNm")
    total_settlement_amount: str | None = wire("strTotStlAmt")
    usage_period: str | None = wire("strUtlTrmCont")
    entity_one: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MaasServiceDetail:
    """신청한 부가서비스 한 건과 그 상세를 담습니다."""

    additional_service_code: str | None = wire("addSrvDvCd")
    additional_service_goods_code: str | None = wire("addSrvGdCd")
    additional_service_id: str | None = wire("addSrvId")
    marketing_entity_id: str | None = wire("addSrvMrkEntId")
    marketing_entity_name: str | None = wire("addSrvMrkEntNm")
    additional_service_name: str | None = wire("addSrvNm")
    progress_status_code: str | None = wire("addSrvPrgSttCd")
    additional_service_request_no: str | None = wire("addSrvReqNo")
    passenger_reference_content: str | None = wire("cgPsRefAtclCont")
    partner_reservation_no: str | None = wire("coptEntRsvNo")
    delivery_close_time: str | None = wire("dlivPsbClsTm")
    delivery_start_time: str | None = wire("dlivPsbStTm")
    lead_message_1: str | None = wire("leadMsgCont1")
    lead_message_2: str | None = wire("leadMsgCont2")
    pnr_no: str | None = wire("pnrNo")
    request_date: str | None = wire("reqDt")
    request_quantity: str | None = wire("reqQnty")
    reservation_station_code_name: str | None = wire("rsStnCdNm")
    reservation_specification_url: str | None = wire("rsvSpecUrl")
    usage_close_date: str | None = wire("utlClsDt")
    usage_start_date: str | None = wire("utlStDt")
    detail_info: MaasServiceDetailInfo | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MaasServiceDetailListResponse(BaseKorailResponse):
    """신청한 부가서비스 목록을 담습니다."""

    details: tuple[MaasServiceDetail, ...] = ()
