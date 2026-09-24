"""Public-call wiring regression tests against 291e01c, not live API acceptance.

Every request and response is synthetic. No builder, parser or queue method is
mocked. Literal exchange expectations are independent of the code at test time.
Retrofit route/method evidence: com/korail/talk/network/NetworkApi.java:87-811 and PushService.java:16-17.
Queue protocol evidence: com/netfunnel/api/Netfunnel.java:610-664,848-880.
Protected aid/mode literals are not independently verified by these tests.
The per-method source-line map and limitations are recorded in the release report.
"""
from __future__ import annotations

import inspect
import json
import runpy
import socket
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api as api

F8_DATE = "20990102"
F8_ENV = {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": "synthetic"}


def _f8_arguments() -> dict[str, dict[str, Any]]:
    train = api.TrainSummary(
        train_no="90001", train_group_code="100", train_class_code="00",
        departure_station_code="9901", arrival_station_code="9903",
        departure_station_name="출발시험역", arrival_station_name="도착시험역",
        departure_date=F8_DATE, run_date=F8_DATE, departure_time="090000",
        arrival_date=F8_DATE, arrival_time="110000", departure_run_order="1",
        arrival_run_order="3", departure_construction_order="1",
        arrival_construction_order="3", seat_attribute_code="015",
        general_reservation_code="11", general_reservation_flag="Y",
    )
    query = api.TrainSearchQuery("출발시험역", "도착시험역", F8_DATE, "090000")
    hold = api.ReservationHoldResponse(
        str_result="SUCC", pnr_no="SYNTHETIC-PNR", journey_count="1",
        window_no="SYNTHETIC-WINDOW", temporary_job_sequence_1="1",
        temporary_job_sequence_2="2", total_price="1000", received_amount="1000",
    )
    ticket = api.OriginalTicketReference("SYNTHETIC-WINDOW", F8_DATE, "1", "SYNTHETIC-RETURN")
    schedule = api.LimousineSchedule(
        departure_date=F8_DATE, run_date=F8_DATE, departure_time="090000",
        departure_station_code="9901", arrival_station_code="9903",
        departure_run_order="1", arrival_run_order="3", train_class_code="80",
        service_code="800", train_no="90001", general_remaining_seat_count="2",
    )
    result: dict[str, dict[str, Any]] = {
        "login": {"member_no": "SYNTHETIC-MEMBER", "password": "SYNTHETIC-PASSWORD"},
        "logout": {}, "clear_session": {}, "close": {},
        "search_trains": {"query": query},
        "search_transfer_trains": {"query": query},
        "search_trains_with_transfer_fallback": {"query": query},
        "get_train_schedule": {"run_date": F8_DATE, "train_no": "90001"},
        "get_transfer_stations": {"departure_station_code": "9901", "arrival_station_code": "9903"},
        "get_train_calendar": {}, "get_seat_cars": {"train": train},
        "get_seat_inventory": {"train": train, "car_no": 1},
        "get_free_seat_car_info": {"request": api.FreeSeatCarRequest(F8_DATE, "90001", "1", "3", "1", "3")},
        "get_guide_seat_condition": {"request": api.GuideSeatConditionRequest("015")},
        "get_merge_seats_inquiry": {"request": api.MergeSeatsInquiryRequest(
            F8_DATE + "090000", F8_DATE + "090000", "90001", "출발시험역", "도착시험역", None, "1", "015", 1)},
        "get_price_fare_quote": {"request": api.PriceFareQuoteRequest((api.PriceFareLeg(
            "9901", "9903", F8_DATE, "90001", "015", "100", "00"),))},
        "get_station_info": {}, "get_station_data": {},
        "get_common_code": {"code": ["synthetic.code"]},
        "get_app_data": {"timestamp_ms": 1}, "get_notice": {"timestamp_ms": 1},
        "get_uuid": {}, "get_service_status": {"timestamp_ms": 1},
        "get_maas_menu_list": {}, "get_maas_station_data": {"additional_service_code": "SYNTHETIC-SERVICE"},
        "get_maas_service_details": {"query": api.MaasServiceDetailQuery(F8_DATE, F8_DATE)},
        "get_cart_list": {"pnr_no": "SYNTHETIC-PNR"}, "get_deposit_banks": {},
        "get_delay_discount_tickets": {"departure_date_to": F8_DATE},
        "get_discount_coupons": {"page_no": 1, "pnr_no": "SYNTHETIC-PNR"},
        "get_korail_point_summary": {},
        "get_mileage_history": {"request": api.MileageHistoryRequest(F8_DATE, F8_DATE)},
        "get_discount_card_usage_history": {"card_no": "SYNTHETIC-CARD"},
        "get_discount_card_schedule": {"request": api.DiscountCardScheduleRequest(
            "SYNTHETIC-KIND", "출발시험역", "도착시험역", F8_DATE)},
        "get_pass_available_dates": {"kind_code": "SYNTHETIC-KIND", "period_code": "1", "age_code": "1"},
        "get_pass_schedule": {"request": api.PassScheduleRequest(
            "100", F8_DATE, "090000", "1", "SYNTHETIC-KIND", "1", "1", "1", "10", "출발시험역", "도착시험역", "N")},
        "get_trip_menu": {}, "get_pass_menu": {"menu_no": "SYNTHETIC-MENU"},
        "get_crew_request_list": {"timestamp_ms": 1},
        "get_commuter_kind_menu": {"commuter_kind_code": "SYNTHETIC-KIND"},
        "get_commuter_info": {"request": api.CommuterTicketInquiryRequest(ticket)},
        "get_product_reservations": {"page_no": 1, "page_size": 10},
        "get_product_detail": {"reservation_no": "SYNTHETIC-RESERVATION", "reservation_sequence": "1"},
        "get_ticket_receipt": {"sale_date": "0102", "window_no": ticket.sale_window_no,
            "sale_sequence": ticket.sale_sequence, "return_password": ticket.return_password},
        "get_reservation_history": {},
        "get_seat_assignment_schedule": {"request": api.SeatAssignmentScheduleRequest(
            "11", F8_DATE, "090000", "출발시험역", "도착시험역", "100", "1", "015", 1, "N", "1", "")},
        "get_multi_child_discount_targets": {"departure_date": F8_DATE},
        "get_customer_trip_info": {}, "get_trip_change_dates": {"departure_date": F8_DATE},
        "get_delivery_recipient": {"ticket": ticket},
        "check_ticket_duplication": {"request": api.TicketDuplicationCheckRequest("SYNTHETIC-PNR")},
        "get_pbp_acceptance_specifications": {"tickets": (ticket,)},
        "get_original_ticket_inquiry": {"tickets": (ticket,)},
        "get_self_seat_change_info": {"request": api.SelfSeatChangeInfoRequest(F8_DATE, "90001", "9901", "9903")},
        "get_recent_delivery_history": {},
        "get_ticket_reservation_detail": {"request": api.TicketReservationDetailRequest("SYNTHETIC-PNR")},
        "get_refund_commission": {"ticket": ticket}, "get_refund_ticket_detail": {"ticket": ticket},
        "get_ticket_list": {}, "reserve": {"train": train},
        "reserve_transfer": {"legs": (
            replace(train, arrival_station_code="9902", arrival_run_order="2", arrival_time="100000"),
            replace(train, train_no="90002", departure_station_code="9902", departure_run_order="2", departure_time="101000"))},
        "reserve_merge": {"standing_hold_train": replace(train, merge_seat_application_flag="A"), "merge_rows": (
            api.TrainScheduleItem(train_no="90001", arrival_station_code="9902",
                arrival_construction_order="2", arrival_run_order="2",
                general_reservation_code="11", standing_reservation_code="11"),
            api.TrainScheduleItem(train_no="90001", arrival_station_code="9903",
                general_reservation_code="13", standing_reservation_code="11"))},
        "reserve_with_discount_card": {"train": train, "card_no": "SYNTHETIC-CARD"},
        "confirm_standby_hold": {"hold": hold}, "cancel_unpaid_hold": {"hold": hold},
        "cancel_product_reservation": {"detail": api.ProductDetailResponse(
            virtual_reservation_no="SYNTHETIC-RESERVATION", goods_sequence="1")},
        "pay_with_card": {"hold": hold, "card": api.CardPayment("0" * 16, "00", "9912", "000101")},
        "refund": {"ticket": api.PaidTicket("SYNTHETIC-PNR", F8_DATE, ticket.sale_window_no,
            ticket.sale_sequence, ticket.return_password, "90001")},
        "verify_station_ticket_refund": {"request": api.StationRefundVerificationRequest(
            "SYNTHETIC-NAME", "00000", "00000000", "0000000", "00000")},
        "execute_station_ticket_refund": {"request": api.StationRefundExecutionRequest(
            "SYNTHETIC-PNR", F8_DATE, "SYNTHETIC-WINDOW", "1", "SYNTHETIC-RETURN",
            "1", "1", "1", "00000000000", "1000", "0", "SYNTHETIC-NAME")},
        "add_to_cart": {"request": api.CartAddRequest("SYNTHETIC-PNR")},
        "register_discount_card": {"request": api.DiscountCardPurchaseRequest(
            "SYNTHETIC-KIND", "SYNTHETIC-CUSTOMER", F8_DATE, "1",
            (api.DiscountCardSectionRequest(F8_DATE, "90001", "9901", "9903"),))},
        "extend_discount_card": {"ticket": api.DiscountCardTicket(
            ticket.sale_window_no, ticket.sale_date, ticket.sale_sequence, ticket.return_password)},
        "recalculate_price": {"request": api.PriceRecalculationRequest(
            "SYNTHETIC-PNR", (api.PriceRecalculationRow("1", "1", "000"),))},
        "get_limousine_schedules": {"query": api.LimousineScheduleQuery(
            F8_DATE, "9901", "9903", "800", "1", "090000", "90001", "015", "1")},
        "get_limousine_seat_inventory": {"query": api.LimousineSeatInventoryQuery(
            "80", "800", F8_DATE, "90001", "0001", "1", "9901", "9903", "015", "1", "3", 1)},
        "reserve_limousine": {"schedule": schedule, "seat_nos": ("1A",)},
    }
    return result

# Literal golden exchanges captured from synthetic calls, then route-checked against APK sources.
F8_CASE_DATA: dict[str, Any] = json.loads(r'''
{
  "login": {"return_type": "KorailSession","exchanges": [{"method": "POST","path": "/file/CACHE/MobileService.cache","host": "api.example.invalid","query": {},"form": {"timeStamp": ["<DYNAMIC>"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","strCustNo": "SYNTHETIC-CUSTOMER","strMbCrdNo": "SYNTHETIC-MEMBER-CARD"}},{"method": "POST","path": "/classes/com.korail.mobile.common.code.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"code": ["app.display.image","app.menu.railpoint","app.main.popup","app.easyLogin.isShow","app.korail.boss","app.menu.buynow","app.menu.lost112","app.event.easyPay","app.hndy.athn","app.view.visibility","app.menu.biz","app.event.point","app.var.data","app.login.cphd","app.illegal.report","app.holiday.popup","app.MaaS.test","app.limousine.mainMsg"],"deviceWidth": ["1440"],"deviceHeight": ["3120"],"OSVersion": ["37"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","app.login.cphd": {"idx": "1","key": "0123456789abcdef0123456789abcdef","pwdAESCphd": "Y"}}},{"method": "POST","path": "/classes/com.korail.mobile.login.Login","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMemberNo": ["SYNTHETIC-MEMBER"],"txtPwd": ["NEVMMWdrT3FoZ250aUVDOUM3TTlYU2lhMFVJK1dkU3Y0M25ESFBlUmlyWT0=\n"],"txtInputFlg": ["2"],"checkValidPw": ["Y"],"idx": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","strCustNo": "SYNTHETIC-CUSTOMER","strMbCrdNo": "SYNTHETIC-MEMBER-CARD"}}]},
  "logout": {"return_type": "NoneType","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.login.Logout","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"timeStamp": ["<DYNAMIC>"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "clear_session": {"return_type": "NoneType","exchanges": []},
  "close": {"return_type": "NoneType","exchanges": []},
  "search_trains": {"return_type": "TrainSearchResult","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_8"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.seatMovie.ScheduleView","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"radJobId": ["1"],"selGoTrain": ["109"],"txtTrnGpCd": ["109"],"txtGoStart": ["출발시험역"],"txtGoEnd": ["도착시험역"],"txtGoAbrdDt": ["20990102"],"txtGoHour": ["090000"],"txtPsgFlg_1": ["1"],"txtPsgFlg_2": ["0"],"txtPsgFlg_3": ["0"],"txtPsgFlg_4": ["0"],"txtPsgFlg_5": ["0"],"txtSeatAttCd_2": ["000"],"txtSeatAttCd_3": ["000"],"txtSeatAttCd_4": ["015"],"ebizCrossCheck": ["N"],"srtCheckYn": ["N"],"rtYn": ["N"],"adjStnScdlOfrFlg": ["N"],"mbCrdNo": ["SYNTHETIC-MEMBER-CARD"],"qryDvCd": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","trn_infos": {"trn_info": [{"h_trn_no": "90001","h_dpt_rs_stn_cd": "9901","h_arv_rs_stn_cd": "9903","h_dpt_dt": "20990102","h_dpt_tm": "090000","h_arv_tm": "110000","h_run_dt": "20990102"}]},"f8_marker": "search_trains"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "search_transfer_trains": {"return_type": "TransferSearchResult","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_8"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.seatMovie.ScheduleView","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"radJobId": ["2"],"selGoTrain": ["109"],"txtTrnGpCd": ["109"],"txtGoStart": ["출발시험역"],"txtGoEnd": ["도착시험역"],"txtGoAbrdDt": ["20990102"],"txtGoHour": ["090000"],"txtPsgFlg_1": ["1"],"txtPsgFlg_2": ["0"],"txtPsgFlg_3": ["0"],"txtPsgFlg_4": ["0"],"txtPsgFlg_5": ["0"],"txtSeatAttCd_2": ["000"],"txtSeatAttCd_3": ["000"],"txtSeatAttCd_4": ["015"],"ebizCrossCheck": ["N"],"srtCheckYn": ["N"],"rtYn": ["N"],"adjStnScdlOfrFlg": ["N"],"mbCrdNo": ["SYNTHETIC-MEMBER-CARD"],"qryDvCd": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","trn_infos": {"trn_info": []},"f8_marker": "search_transfer_trains"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "search_trains_with_transfer_fallback": {"return_type": "TrainSearchResult","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_8"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.seatMovie.ScheduleView","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"radJobId": ["1"],"selGoTrain": ["109"],"txtTrnGpCd": ["109"],"txtGoStart": ["출발시험역"],"txtGoEnd": ["도착시험역"],"txtGoAbrdDt": ["20990102"],"txtGoHour": ["090000"],"txtPsgFlg_1": ["1"],"txtPsgFlg_2": ["0"],"txtPsgFlg_3": ["0"],"txtPsgFlg_4": ["0"],"txtPsgFlg_5": ["0"],"txtSeatAttCd_2": ["000"],"txtSeatAttCd_3": ["000"],"txtSeatAttCd_4": ["015"],"ebizCrossCheck": ["N"],"srtCheckYn": ["N"],"rtYn": ["N"],"adjStnScdlOfrFlg": ["N"],"mbCrdNo": ["SYNTHETIC-MEMBER-CARD"],"qryDvCd": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","trn_infos": {"trn_info": [{"h_trn_no": "90001","h_dpt_rs_stn_cd": "9901","h_arv_rs_stn_cd": "9903","h_dpt_dt": "20990102","h_dpt_tm": "090000","h_arv_tm": "110000","h_run_dt": "20990102"}]},"f8_marker": "search_trains_with_transfer_fallback"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "get_train_schedule": {"return_type": "TrainScheduleResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.actualTrainSchedule.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"runDt": ["20990102"],"trnNo": ["90001"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_transfer_stations": {"return_type": "TransferStationListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.qry.chtnStn.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"dptRsStnCd": ["9901"],"arvRsStnCd": ["9903"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_train_calendar": {"return_type": "TrainCalendarResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.schedule.runDt","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"timeStamp": ["<DYNAMIC>"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_seat_cars": {"return_type": "SeatCarListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.TrainResearch","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"txtPsrmClCd": ["1"],"txtRunDt": ["20990102"],"txtDptDt": ["20990102"],"txtDptTm": ["090000"],"txtTrnClsfCd": ["00"],"txtTrnNo": ["90001"],"txtDptRsStnCd": ["9901"],"txtArvRsStnCd": ["9903"],"txtDptStnRunOrdr": ["1"],"txtArvStnRunOrdr": ["3"],"txtTrnGpCd": ["100"],"txtTotPsgCnt": ["1"],"txtSeatAttCd": ["015"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_seat_inventory": {"return_type": "SeatInventoryResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.TResidualSeatsResearch.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"trnClsfCd": ["00"],"trnGpCd": ["100"],"runDt": ["20990102"],"trnNo": ["90001"],"srcarNo": ["1"],"psrmClCd": ["1"],"dptRsStnCd": ["9901"],"arvRsStnCd": ["9903"],"seatAttCd": ["015"],"dptStnRunOrdr": ["1"],"arvStnRunOrdr": ["3"],"totPsgCnt": ["1"],"isArrow": ["false"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","layout_type": "1","seat_ary_cd": "1","seatList": [],"f8_marker": "get_seat_inventory"}}]},
  "get_free_seat_car_info": {"return_type": "FreeSeatCarResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.trn.fresScar.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"runDt": ["20990102"],"trnNo": ["90001"],"dptStnConsOrdr": ["1"],"arvStnConsOrdr": ["3"],"dptStnRunOrdr": ["1"],"arvStnRunOrdr": ["3"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_guide_seat_condition": {"return_type": "GuideSeatConditionResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.reservation.guideSeatCnd.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"rqSeatAttCd": ["015"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_merge_seats_inquiry": {"return_type": "MergeSeatsInquiryResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.mergeSeatsC.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"abrdDt": ["20990102090000"],"runDt": ["20990102090000"],"trnNo": ["90001"],"dptRsStnNm": ["출발시험역"],"arvRsStnNm": ["도착시험역"],"psrmClCd": ["1"],"seatAttCd": ["015"],"totPsgNum": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_price_fare_quote": {"return_type": "PriceFareQuoteResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.trn.prcFare.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"chtnDvCd": ["1"],"trnCnt": ["1"],"dptRsStnCd": ["9901"],"arvRsStnCd": ["9903"],"runDt": ["20990102"],"trnNo": ["90001"],"rqSeatAttCd": ["015"],"trnGpCd": ["100"],"stlbTrnClsfCd": ["00"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_station_info": {"return_type": "StationInfoResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.common.stationinfo","host": "api.example.invalid","query": {},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","count": "1","map_version": "synthetic","f8_marker": "get_station_info"}}]},
  "get_station_data": {"return_type": "StationDataResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.common.stationdata","host": "api.example.invalid","query": {},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","stns": {"stn": [{"stn_cd": "9901","stn_nm": "출발시험역"}]},"f8_marker": "get_station_data"}}]},
  "get_common_code": {"return_type": "BaseKorailResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.common.code.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"code": ["synthetic.code"],"deviceWidth": ["1440"],"deviceHeight": ["3120"],"OSVersion": ["37"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_app_data": {"return_type": "AppDataResponse","exchanges": [{"method": "POST","path": "/file/CACHE/prdMobilePlusMain.cache","host": "api.example.invalid","query": {},"form": {"timeStamp": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_notice": {"return_type": "NoticeResponse","exchanges": [{"method": "POST","path": "/file/CACHE/prdMobilePlusMain.cache","host": "api.example.invalid","query": {},"form": {"timeStamp": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_uuid": {"return_type": "UuidResponse","exchanges": [{"method": "POST","path": "/ebizcross/getUUID.do","host": "api.example.invalid","query": {},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","mutMrkVrfCd": "SYNTHETIC-UUID","f8_marker": "get_uuid"}}]},
  "get_service_status": {"return_type": "ServiceStatusResponse","exchanges": [{"method": "POST","path": "/file/CACHE/MobileService.cache","host": "api.example.invalid","query": {},"form": {"timeStamp": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_maas_menu_list": {"return_type": "MaasMenuListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.copt.gdMenuLt.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"timeStamp": ["<DYNAMIC>"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_maas_station_data": {"return_type": "StationDataResponse","exchanges": [{"method": "POST","path": "/ebizmaas/EbizMaasStationList.do","host": "api.example.invalid","query": {},"form": {"addSrvDvCd": ["SYNTHETIC-SERVICE"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","stns": {"stn": [{"stn_cd": "9901","stn_nm": "출발시험역"}]},"f8_marker": "get_maas_station_data"}}]},
  "get_maas_service_details": {"return_type": "MaasServiceDetailListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.copt.gdReqQry.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"qryDtFrom": ["20990102"],"qryDtTo": ["20990102"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_cart_list": {"return_type": "CartListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.cart.showCartList","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"pnrNo": ["SYNTHETIC-PNR"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_deposit_banks": {"return_type": "DepositBankListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.dlay.dptnBank.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_delay_discount_tickets": {"return_type": "DelayDiscountTicketListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.passCard.DelayDiscountView","host": "api.example.invalid","query": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"h_page_no": ["20990102"]},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_discount_coupons": {"return_type": "DiscountCouponListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.passCard.CouponView","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtSelPage": ["1"],"pnrNo": ["SYNTHETIC-PNR"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_korail_point_summary": {"return_type": "KorailPointSummaryResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.xPoint.MyXPointView","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"point_dv_cd": ["0"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_mileage_history": {"return_type": "MileageHistoryResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.mlg.amtSpec.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"pontTpVal": ["1"],"qryDvVal": ["0"],"qryStDt": ["20990102"],"qryClsDt": ["20990102"],"pgPrCnt": ["20"],"nowPgNo": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_discount_card_usage_history": {"return_type": "DiscountCardUsageListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"dcntCrdNo": ["SYNTHETIC-CARD"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_discount_card_schedule": {"return_type": "DiscountCardScheduleResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.dcntCrdScheduleView.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"dptDt": ["20990102"],"dptRsStnNm": ["출발시험역"],"arvRsStnNm": ["도착시험역"],"dptTm": ["000000"],"trnGpCd": ["109"],"dirtChtnDvCd": ["1"],"dcntCrdKndCd": ["MMM"],"dcntCrdKndMgNo": ["SYNTHETIC-KIND"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_pass_available_dates": {"return_type": "PassAvailabilityResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.pass.passInfoList","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtCmtrKndCd": ["SYNTHETIC-KIND"],"txtCmtrUtlTrmCd": ["1"],"txtCmtrUtlAgeCd": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_pass_schedule": {"return_type": "PassScheduleResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.pass.passScheduleInfoList","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"selGoTrain": ["100"],"selGoAbrdDt": ["20990102"],"txtGoHour": ["090000"],"radChgTrnDvCd": ["1"],"txtCmtrKndCd": ["SYNTHETIC-KIND"],"txtCmtrUtlTrmCd": ["1"],"txtCmtrUtlAgeCd": ["1"],"txtSelPage": ["1"],"txtCntPerPage": ["10"],"txtGoStart": ["출발시험역"],"txtGoEnd": ["도착시험역"],"txtWkndUseFlg": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_trip_menu": {"return_type": "TripMenuResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.pass.trGdMenuLt.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"timeStamp": ["<DYNAMIC>"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_pass_menu": {"return_type": "PassMenuResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.pass.passMenu.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"menuNo": ["SYNTHETIC-MENU"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_crew_request_list": {"return_type": "CrewRequestListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.push.crwCallRq.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"timeStamp": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_commuter_kind_menu": {"return_type": "CommuterKindMenuResponse","exchanges": [{"method": "GET","path": "/classes/com.korail.mobile.push.cmtrKnd.do","host": "api.example.invalid","query": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"cmtrKndCd": ["SYNTHETIC-KIND"]},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_commuter_info": {"return_type": "CommuterInfoResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.cmtrInfo.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"jobDvCd": ["c"],"psgCnt": ["0"],"ogtkSaleWctNo": ["SYNTHETIC-WINDOW"],"ogtkSaleDd": ["20990102"],"ogtkSaleSqno": ["1"],"ogtkRetPwd": ["SYNTHETIC-RETURN"],"inquiryType": ["0"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_product_reservations": {"return_type": "ProductReservationListResponse","exchanges": [{"method": "GET","path": "/classes/com.korail.mobile.product.ReservationList","host": "api.example.invalid","query": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtSelPage": ["1"],"txtCntPerPage": ["10"]},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_product_detail": {"return_type": "ProductDetailResponse","exchanges": [{"method": "GET","path": "/classes/com.korail.mobile.product.ReservationDetail","host": "api.example.invalid","query": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtVrRsNo": ["SYNTHETIC-RESERVATION"],"txtVrRsvSqNo": ["1"]},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_ticket_receipt": {"return_type": "TicketReceiptResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.receipt.ReceiptInfo","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"h_orgtk_sale_dt": ["0102"],"h_orgtk_wct_no": ["SYNTHETIC-WINDOW"],"h_orgtk_sale_sqno": ["1"],"h_orgtk_tk_ret_pwd": ["SYNTHETIC-RETURN"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","receipt_infos": {"receipt_info": []},"f8_marker": "get_ticket_receipt"}}]},
  "get_reservation_history": {"return_type": "ReservationHistoryResponse","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_21"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.reservation.ReservationView","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"timeStamp": ["<DYNAMIC>"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "get_seat_assignment_schedule": {"return_type": "SeatAssignmentScheduleResponse","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_8"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.research.assignScheduleView.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"menuId": ["11"],"dptDt": ["20990102"],"dptTm": ["090000"],"dptRsStnNm": ["출발시험역"],"arvRsStnNm": ["도착시험역"],"trnGpCd": ["100"],"psrmClCd": ["1"],"dirtChtnDvCd": ["1"],"seatAttCd1": ["015"],"psgNum1": ["1"],"stlbDturDvNm1": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "get_multi_child_discount_targets": {"return_type": "MultiChildDiscountTargetResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.cust.mchdDcntTgt.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"dptDt": ["20990102"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_customer_trip_info": {"return_type": "CustomerTripInfoResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.custTripInfo.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"custMgNo": ["SYNTHETIC-CUSTOMER"],"medDvCd": ["03"],"regSqno": ["0"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","mainList": []}}]},
  "get_trip_change_dates": {"return_type": "TripChangeDateResponse","exchanges": [{"method": "GET","path": "/classes/com.korail.mobile.reservation.tripChgDate.do","host": "api.example.invalid","query": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"tripChgDate": ["20990102"]},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","tripChgDates": ["20990102"],"f8_marker": "get_trip_change_dates"}}]},
  "get_delivery_recipient": {"return_type": "DeliveryRecipientResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.tk.dlvRcvCust.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"saleWctNo": ["SYNTHETIC-WINDOW"],"saleDt": ["20990102"],"saleSqno": ["1"],"tkRetPwd": ["SYNTHETIC-RETURN"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","acepCustMgNo": "SYNTHETIC-CUSTOMER","acepCustNm": "SYNTHETIC-NAME","acepCustTeln": "00000000000","acepCustTeln2": "00000000000","mbCrdNo": "SYNTHETIC-MEMBER-CARD","f8_marker": "get_delivery_recipient"}}]},
  "check_ticket_duplication": {"return_type": "TicketDuplicationCheckResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.ticket.ticketDupCheck.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"pnrNo": ["SYNTHETIC-PNR"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_pbp_acceptance_specifications": {"return_type": "PbpAcceptanceSpecificationResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.tk.pbpAcepSpec.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"tkCnt": ["1"],"tkRetNo": ["SYNTHETIC-WINDOW-20990102-1-SYNTHETIC-RETURN"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","tkList": [],"f8_marker": "get_pbp_acceptance_specifications"}}]},
  "get_original_ticket_inquiry": {"return_type": "OriginalTicketInquiryResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.tripChgOgtk.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"tkCnt": ["1"],"ogtkSaleWctNo_1": ["SYNTHETIC-WINDOW"],"ogtkSaleDd_1": ["20990102"],"ogtkSaleSqno_1": ["1"],"ogtkRetPwd_1": ["SYNTHETIC-RETURN"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_self_seat_change_info": {"return_type": "SelfSeatChangeInfoResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.self.seatChgInfo.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"runDt": ["20990102"],"trnNo": ["90001"],"dptRsStnCd": ["9901"],"arvRsStnCd": ["9903"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_recent_delivery_history": {"return_type": "RecentDeliveryHistoryResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.tk.rcntDlvHst.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"custMgNo": ["SYNTHETIC-CUSTOMER"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_ticket_reservation_detail": {"return_type": "TicketReservationDetailResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.certification.ReservationList","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"hidPnrNo": ["SYNTHETIC-PNR"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_refund_commission": {"return_type": "RefundCommissionResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.refunds.CommissionView","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"h_orgtk_ret_sale_dt": ["20990102"],"h_orgtk_wct_no": ["SYNTHETIC-WINDOW"],"h_orgtk_sale_sqno": ["1"],"h_orgtk_ret_pwd": ["SYNTHETIC-RETURN"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_refund_ticket_detail": {"return_type": "RefundTicketDetailResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.refunds.SelTicketInfo","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"h_orgtk_ret_sale_dt": ["20990102"],"h_orgtk_wct_no": ["SYNTHETIC-WINDOW"],"h_orgtk_sale_sqno": ["1"],"h_orgtk_ret_pwd": ["SYNTHETIC-RETURN"],"h_purchase_history": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "get_ticket_list": {"return_type": "TicketListResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.myTicket.MyTicketNewList.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtIndex": ["1"],"h_page_no": ["1"],"hiduserYn": ["Y"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "reserve": {"return_type": "ReservationHoldResponse","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_14"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.certification.TicketReservation","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"txtJobId": ["1101"],"hidFreeFlg": ["N"],"txtStndFlg": ["N"],"txtTotPsgCnt": ["1"],"txtCompaCnt1": ["1"],"txtPsgTpCd1": ["1"],"txtDiscKndCd1": ["000"],"txtSeatAttCd1": ["000"],"txtSeatAttCd2": ["000"],"txtSeatAttCd3": ["000"],"txtSeatAttCd4": ["015"],"txtSeatAttCd5": ["000"],"txtPsrmClCd1": ["1"],"txtJrnyCnt": ["1"],"txtJrnyTpCd1": ["11"],"txtJrnySqno1": ["001"],"txtTrnNo1": ["90001"],"txtTrnClsfCd1": ["00"],"txtTrnGpCd1": ["100"],"txtRunDt1": ["20990102"],"txtDptDt1": ["20990102"],"txtDptTm1": ["090000"],"txtDptRsStnCd1": ["9901"],"txtDptStnConsOrdr1": ["1"],"txtDptStnRunOrdr1": ["1"],"txtArvRsStnCd1": ["9903"],"txtArvStnConsOrdr1": ["3"],"txtArvStnRunOrdr1": ["3"],"txtChgFlg1": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","h_pnr_no": "SYNTHETIC-PNR","h_jrny_cnt": "1","h_wct_no": "SYNTHETIC-WINDOW","h_tmp_job_sqno1": "1","h_tmp_job_sqno2": "2","h_tot_prc": "1000","h_rcvd_amt": "1000","f8_marker": "recalculate_price"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "reserve_transfer": {"return_type": "ReservationHoldResponse","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_14"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.certification.TicketReservation","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"txtJobId": ["1101"],"hidFreeFlg": ["N"],"txtStndFlg": ["N"],"txtTotPsgCnt": ["1"],"txtCompaCnt1": ["1"],"txtPsgTpCd1": ["1"],"txtDiscKndCd1": ["000"],"txtSeatAttCd1": ["000"],"txtSeatAttCd2": ["000"],"txtSeatAttCd3": ["000"],"txtSeatAttCd4": ["015"],"txtSeatAttCd5": ["000"],"txtPsrmClCd1": ["1"],"txtSeatAttCd4_1": ["015"],"txtPsrmClCd2": ["1"],"txtJrnyCnt": ["2"],"txtJrnyTpCd1": ["14"],"txtJrnySqno1": ["001"],"txtTrnNo1": ["90001"],"txtTrnClsfCd1": ["00"],"txtTrnGpCd1": ["100"],"txtRunDt1": ["20990102"],"txtDptDt1": ["20990102"],"txtDptTm1": ["090000"],"txtDptRsStnCd1": ["9901"],"txtDptStnConsOrdr1": ["1"],"txtDptStnRunOrdr1": ["1"],"txtArvRsStnCd1": ["9902"],"txtArvStnConsOrdr1": ["3"],"txtArvStnRunOrdr1": ["2"],"txtChgFlg1": ["N"],"txtJrnyTpCd2": ["14"],"txtJrnySqno2": ["002"],"txtTrnNo2": ["90002"],"txtTrnClsfCd2": ["00"],"txtTrnGpCd2": ["100"],"txtRunDt2": ["20990102"],"txtDptDt2": ["20990102"],"txtDptTm2": ["101000"],"txtDptRsStnCd2": ["9902"],"txtDptStnConsOrdr2": ["1"],"txtDptStnRunOrdr2": ["2"],"txtArvRsStnCd2": ["9903"],"txtArvStnConsOrdr2": ["3"],"txtArvStnRunOrdr2": ["3"],"txtChgFlg2": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","h_pnr_no": "SYNTHETIC-PNR","h_jrny_cnt": "1","h_wct_no": "SYNTHETIC-WINDOW","h_tmp_job_sqno1": "1","h_tmp_job_sqno2": "2","h_tot_prc": "1000","h_rcvd_amt": "1000","f8_marker": "recalculate_price"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "reserve_merge": {"return_type": "ReservationHoldResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.certification.TicketReservation","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"txtJobId": ["1202"],"hidFreeFlg": ["N"],"txtStndFlg": ["Y"],"txtTotPsgCnt": ["1"],"txtCompaCnt1": ["1"],"txtPsgTpCd1": ["1"],"txtDiscKndCd1": ["000"],"txtSeatAttCd1": ["000"],"txtSeatAttCd2": ["000"],"txtSeatAttCd3": ["000"],"txtSeatAttCd4": ["015"],"txtSeatAttCd5": ["000"],"txtPsrmClCd1": ["1"],"txtJrnyCnt": ["1"],"txtJrnyTpCd1": ["11"],"txtJrnySqno1": ["001"],"txtTrnNo1": ["90001"],"txtTrnClsfCd1": ["00"],"txtTrnGpCd1": ["100"],"txtRunDt1": ["20990102"],"txtDptDt1": ["20990102"],"txtDptTm1": ["090000"],"txtDptRsStnCd1": ["9901"],"txtDptStnConsOrdr1": ["1"],"txtDptStnRunOrdr1": ["1"],"txtArvRsStnCd1": ["9903"],"txtArvStnConsOrdr1": ["3"],"txtArvStnRunOrdr1": ["3"],"txtChgFlg1": ["N"],"txtMidRsStnCd": ["9902"],"txtMidStnConsOrdr": ["2"],"txtMidStnRunOrdr": ["2"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","h_pnr_no": "SYNTHETIC-PNR","h_jrny_cnt": "1","h_wct_no": "SYNTHETIC-WINDOW","h_tmp_job_sqno1": "1","h_tmp_job_sqno2": "2","h_tot_prc": "1000","h_rcvd_amt": "1000","f8_marker": "recalculate_price"}}]},
  "reserve_with_discount_card": {"return_type": "ReservationHoldResponse","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_14"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.certification.TicketReservation","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["A2"],"txtJobId": ["1101"],"hidFreeFlg": ["N"],"txtStndFlg": ["N"],"txtTotPsgCnt": ["1"],"txtCompaCnt1": ["1"],"txtPsgTpCd1": ["1"],"txtDiscKndCd1": ["153"],"txtCardNo_1": ["SYNTHETIC-CARD"],"txtSeatAttCd1": ["000"],"txtSeatAttCd2": ["000"],"txtSeatAttCd3": ["000"],"txtSeatAttCd4": ["015"],"txtSeatAttCd5": ["000"],"txtPsrmClCd1": ["1"],"txtJrnyCnt": ["1"],"txtJrnyTpCd1": ["11"],"txtJrnySqno1": ["001"],"txtTrnNo1": ["90001"],"txtTrnClsfCd1": ["00"],"txtTrnGpCd1": ["100"],"txtRunDt1": ["20990102"],"txtDptDt1": ["20990102"],"txtDptTm1": ["090000"],"txtDptRsStnCd1": ["9901"],"txtDptStnConsOrdr1": ["1"],"txtDptStnRunOrdr1": ["1"],"txtArvRsStnCd1": ["9903"],"txtArvStnConsOrdr1": ["3"],"txtArvStnRunOrdr1": ["3"],"txtChgFlg1": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","h_pnr_no": "SYNTHETIC-PNR","h_jrny_cnt": "1","h_wct_no": "SYNTHETIC-WINDOW","h_tmp_job_sqno1": "1","h_tmp_job_sqno2": "2","h_tot_prc": "1000","h_rcvd_amt": "1000","f8_marker": "recalculate_price"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "confirm_standby_hold": {"return_type": "BaseKorailResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.reservationWait.ReservationWait","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtPnrNo": ["SYNTHETIC-PNR"],"txtPsrmClChgFlg": ["N"],"txtSmsSndFlg": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "cancel_unpaid_hold": {"return_type": "BaseKorailResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.reservationCancel.ReservationCancel","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtPnrNo": ["SYNTHETIC-PNR"],"txtJrnySqno": ["0001"],"txtJrnyCnt": ["1"],"hidRsvChgNo": ["000"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}},{"method": "POST","path": "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtPnrNo": ["SYNTHETIC-PNR"],"txtJrnySqno": ["0001"],"txtJrnyCnt": ["1"],"hidRsvChgNo": ["000"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "cancel_product_reservation": {"return_type": "ProductCancelResponse","exchanges": [{"method": "GET","path": "/classes/com.korail.mobile.product.ReservationCancel","host": "api.example.invalid","query": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtVrRsNo": ["SYNTHETIC-RESERVATION"],"txtGdSqno": ["1"]},"form": {},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "pay_with_card": {"return_type": "ReservationPaymentResponse","exchanges": [{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5101"],"sid": ["service_1"],"aid": ["act_18"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"},{"method": "POST","path": "/classes/com.korail.mobile.payment.ReservationPayment","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"hidPnrNo": ["SYNTHETIC-PNR"],"hidWctNo": ["SYNTHETIC-WINDOW"],"hidTmpJobSqno1": ["1"],"hidTmpJobSqno2": ["2"],"hidRsvChgNo": ["000"],"hidInrecmnsGridcnt": ["1"],"hidStlMnsSqno1": ["1"],"hidStlMnsCd1": ["02"],"hidMnsStlAmt1": ["1000"],"hidCrdInpWayCd1": ["@"],"hidStlCrCrdNo1": ["0000000000000000"],"hidVanPwd1": ["00"],"hidCrdVlidTrm1": ["9912"],"hidIsmtMnthNum1": ["0"],"hidAthnDvCd1": ["J"],"hidAthnVal1": ["000101"],"hiduserYn": ["Y"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","h_rsv_no": "SYNTHETIC-PNR","h_tot_rcvd_amt": "1000","h_stl_amt": "1000","tk_infos": {"tk_info": [{"h_sale_dt": "20990102","h_sale_sqno": "1","h_tk_ret_pwd": "SYNTHETIC-RETURN"}]},"f8_marker": "pay_with_card"}},{"method": "GET","path": "/ts.wseq","host": "queue.example.invalid","query": {"opcode": ["5004"],"key": ["SYNTHETIC-QUEUE"]},"form": {},"response": "200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1"}]},
  "refund": {"return_type": "RefundTicketResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.refunds.RefundsRequest","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtPnrNo": ["SYNTHETIC-PNR"],"h_orgtk_sale_dt": ["20990102"],"h_orgtk_sale_wct_no": ["SYNTHETIC-WINDOW"],"h_orgtk_sale_sqno": ["1"],"h_orgtk_ret_pwd": ["SYNTHETIC-RETURN"],"h_mlg_stl": ["N"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","stlList": [{"stl_mns_cd": "02"}],"f8_marker": "refund"}}]},
  "verify_station_ticket_refund": {"return_type": "StationRefundVerificationResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.refunds.verifyOnlineRefunds","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"strName": ["SYNTHETIC-NAME"],"retNo1": ["00000"],"retNo2": ["00000000"],"retNo3": ["0000000"],"retNo4": ["00000"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","orgtkinfo_list": [{"pnr_no": "SYNTHETIC-PNR","ogtk_sale_dt": "0102","ogtk_sale_wct_no": "SYNTHETIC-WINDOW","ogtk_sale_sqno": "1","ogtk_ret_pwd": "SYNTHETIC-RETURN","tk_knd_cd": "1","ret_dv_cd": "1","ret_rsn_cd": "1"}],"rcvd_amt": "1000","ret_fee": "0","ret_amt": "1000","f8_marker": "verify_station_ticket_refund"}}]},
  "execute_station_ticket_refund": {"return_type": "StationRefundExecutionResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.refunds.executeOnlineRefunds","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"pnrNo": ["SYNTHETIC-PNR"],"ogtkSaleDt": ["20990102"],"ogtkSaleWctNo": ["SYNTHETIC-WINDOW"],"ogtkSaleSqno": ["1"],"ogtkRetPwd": ["SYNTHETIC-RETURN"],"retDvCd": ["1"],"retRsnCd": ["1"],"tkKndCd": ["1"],"custTeln": ["00000000000"],"retAmt": ["1000"],"retFee": ["0"],"acepCustNm": ["SYNTHETIC-NAME"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "add_to_cart": {"return_type": "CartAddResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.cart.addCartList","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"hidPnrNo": ["SYNTHETIC-PNR"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "register_discount_card": {"return_type": "DiscountCardPurchaseResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.research.dcntCrdInfo.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"dcntCrdKndMgNo": ["SYNTHETIC-KIND"],"custMgNo": ["SYNTHETIC-CUSTOMER"],"vlidTrmStDt": ["20990102"],"usePsbTno": ["1"],"jrnyCnt": ["1"],"jrnyTpCd_1": ["11"],"runDt_1": ["20990102"],"trnNo_1": ["90001"],"dptRsStnCd_1": ["9901"],"arvRsStnCd_1": ["9903"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "extend_discount_card": {"return_type": "BaseKorailResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.reservation.dcntCrdExtn.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"saleWctNo": ["SYNTHETIC-WINDOW"],"saleDd": ["20990102"],"saleSqno": ["1"],"tkRetPwd": ["SYNTHETIC-RETURN"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic"}}]},
  "recalculate_price": {"return_type": "ReservationHoldResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.certification.PriceReCalculation","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"hidPnrNo": ["SYNTHETIC-PNR"],"txtJobId": ["1101"],"txtPsgGridcnt": ["1"],"psg_tp_dv_cd": ["1"],"hidDcntKndCd": [""],"dcnt_knd_cd1": ["000"],"hidDscpNo": [""],"psrm_cl_cd": ["1"],"hidFmlyNo": [""]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","h_pnr_no": "SYNTHETIC-PNR","h_jrny_cnt": "1","h_wct_no": "SYNTHETIC-WINDOW","h_tmp_job_sqno1": "1","h_tmp_job_sqno2": "2","h_tot_prc": "1000","h_rcvd_amt": "1000","f8_marker": "recalculate_price"}}]},
  "get_limousine_schedules": {"return_type": "LimousineScheduleResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.lmu.scdlQry.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"dptDt": ["20990102"],"dptRsStnCd": ["9901"],"arvRsStnCd": ["9903"],"trnGpCd": ["800"],"psrmClCd": ["1"],"dptTm": ["090000"],"trnNo": ["90001"],"seatAttCd": ["015"],"rsvSaleDvCd": ["1"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","trainList": [{"trnNo": "90001","dptDt": "20990102","runDt": "20990102","dptRsStnCd": "9901","arvRsStnCd": "9903"}],"f8_marker": "get_limousine_schedules"}}]},
  "get_limousine_seat_inventory": {"return_type": "LimousineSeatInventoryResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"trnClsfCd": ["80"],"trnGpCd": ["800"],"runDt": ["20990102"],"trnNo": ["90001"],"srcarNo": ["0001"],"psrmClCd": ["1"],"dptRsStnCd": ["9901"],"arvRsStnCd": ["9903"],"seatAttCd": ["015"],"dptStnRunOrdr": ["1"],"arvStnRunOrdr": ["3"],"totPsgCnt": ["1"],"isArrow": ["false"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","seatList": [{"seat_no": "1A","sale_psb_flg": "Y"}],"f8_marker": "get_limousine_seat_inventory"}}]},
  "reserve_limousine": {"return_type": "ReservationHoldResponse","exchanges": [{"method": "POST","path": "/classes/com.korail.mobile.certification.TicketReservation","host": "api.example.invalid","query": {},"form": {"Device": ["AD"],"Version": ["250601003"],"Key": ["SYNTHETIC-APP-KEY"],"txtMenuId": ["11"],"txtJobId": ["1101"],"hidFreeFlg": ["N"],"txtStndFlg": ["N"],"txtTotPsgCnt": ["1"],"txtCompaCnt1": ["1"],"txtPsgTpCd1": ["1"],"txtDiscKndCd1": ["000"],"txtSeatAttCd1": ["000"],"txtSeatAttCd2": ["000"],"txtSeatAttCd3": ["000"],"txtSeatAttCd4": ["015"],"txtSeatAttCd5": ["000"],"txtPsrmClCd1": ["1"],"txtJrnyCnt": ["1"],"txtJrnyTpCd1": ["11"],"txtJrnySqno1": ["001"],"txtTrnNo1": ["90001"],"txtTrnClsfCd1": ["80"],"txtTrnGpCd1": ["800"],"txtRunDt1": ["20990102"],"txtDptDt1": ["20990102"],"txtDptTm1": ["090000"],"txtDptRsStnCd1": ["9901"],"txtDptStnRunOrdr1": ["1"],"txtArvRsStnCd1": ["9903"],"txtArvStnRunOrdr1": ["3"],"txtSrcarCnt": ["1"],"txtSrcarNo1": ["0001"],"txtSeatNo1": ["1A"]},"response": {"strResult": "SUCC","h_msg_cd": "IRZ000001","h_msg_txt": "synthetic","h_pnr_no": "SYNTHETIC-PNR","h_jrny_cnt": "1","h_wct_no": "SYNTHETIC-WINDOW","h_tmp_job_sqno1": "1","h_tmp_job_sqno2": "2","h_tot_prc": "1000","h_rcvd_amt": "1000","f8_marker": "recalculate_price"}}]}
}
''')


def _f8_match_fields(actual: dict[str, list[str]], expected: dict[str, list[str]]) -> None:
    assert actual.keys() == expected.keys()
    for key, values in expected.items():
        if values == ["<DYNAMIC>"]:
            assert len(actual[key]) == 1 and actual[key][0].isdigit()
        else:
            assert actual[key] == values, key


def _f8_handler(
    exchanges: list[dict[str, Any]],
) -> tuple[Callable[[httpx.Request], httpx.Response], list[str]]:
    pending = list(exchanges)
    seen: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        assert pending, f"unexpected extra request: {request.method} {request.url.path}"
        expected = pending.pop(0)
        assert request.method == expected["method"]
        assert request.url.scheme == "https"
        assert request.url.host == expected["host"]
        assert request.url.path == expected["path"]
        _f8_match_fields(parse_qs(request.url.query.decode(), keep_blank_values=True),
                         expected["query"])
        _f8_match_fields(parse_qs(request.content.decode(), keep_blank_values=True),
                         expected["form"])
        opcode = request.url.params.get("opcode")
        seen.append(opcode or request.url.path)
        payload = expected["response"]
        if isinstance(payload, str):
            return httpx.Response(200, text=payload)
        headers = {"set-cookie": "JSESSIONID=SYNTHETIC-SESSION; Path=/"} if (
            request.url.path.endswith("login.Login")
        ) else {}
        return httpx.Response(200, json=payload, headers=headers)

    # Caller also checks length/sequence: swallowed completion errors cannot pass silently.
    return handle, seen


@pytest.mark.parametrize("method_name", list(F8_CASE_DATA))
def test_f8_all_public_methods(method_name: str, f8_client_factory: Callable[..., api.KorailClient]) -> None:
    """NetworkApi.java:87-811; PushService.java:16-17; Netfunnel.java:610-664,848-880.

    Each call asserts the entire query/form key set and values, HTTP method/path,
    typed result, and all 5101/API/5004 events, not just mocked method invocations.
    Fixtures freeze the baseline; they do not prove protected fields or live acceptance.
    """
    case = F8_CASE_DATA[method_name]
    handler, seen = _f8_handler(case["exchanges"])
    client = f8_client_factory(handler, logged_in=method_name != "login")
    result = getattr(client, method_name)(**_f8_arguments()[method_name])
    expected_type = type(None) if case["return_type"] == "NoneType" else getattr(api, case["return_type"])
    assert type(result) is expected_type
    expected_seen = [exchange["query"].get("opcode", [exchange["path"]])[0]
                     for exchange in case["exchanges"]]
    assert seen == expected_seen
    if "5101" in seen:
        assert seen[0] == "5101" and seen[-1] == "5004"
    if method_name == "login":
        assert result.customer_no == "SYNTHETIC-CUSTOMER"
        assert client.session.current is result
    elif method_name in {"logout", "clear_session"}:
        assert client.session.current is None
    elif method_name == "close":
        # Closing twice remains harmless; the factory finalizer also closes all clients.
        client.close()
    elif hasattr(result, "raw"):
        api_exchanges = [exchange for exchange in case["exchanges"]
                         if exchange["host"] == "api.example.invalid"]
        assert result.raw == api_exchanges[-1]["response"]


def test_f8_public_method_inventory() -> None:
    actual = {name for name, method in inspect.getmembers(api.KorailClient, inspect.isfunction)
              if not name.startswith("_")}
    assert len(actual) == 77
    assert actual == F8_CASE_DATA.keys() == _f8_arguments().keys()
    assert len(api.__all__) == len(set(api.__all__))
    for name in api.__all__:
        assert hasattr(api, name), name
    assert "ProductCancelResponse" in api.__all__


@pytest.mark.parametrize("script", ["contract_api.py", "netfunnel_offline.py"])
def test_f8_existing_checks(script: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run original G9/G10/G11 and nine queue checks under the same socket guard."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", [script])
    path = Path(__file__).resolve().parents[1] / "checks" / script
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as error:
        assert error.code in (0, None)


def test_f8_socket_guard_blocks_dns_tcp_and_udp() -> None:
    with pytest.raises(AssertionError, match="f8: network access"):
        socket.getaddrinfo("example.invalid", 443)
    with socket.socket() as stream:
        with pytest.raises(AssertionError, match="f8: network access"):
            stream.connect(("127.0.0.1", 9))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as datagram:
        with pytest.raises(AssertionError, match="f8: network access"):
            datagram.sendto(b"synthetic", ("127.0.0.1", 9))


def test_f8_queue_is_completed_after_api_error(f8_client_factory: Callable[..., api.KorailClient]) -> None:
    """Netfunnel.java:848-880 describes completion; error cleanup is library policy."""
    exchanges = json.loads(json.dumps(F8_CASE_DATA["search_trains"]["exchanges"]))
    failure = {"strResult": "FAIL", "h_msg_cd": "F8-SYNTHETIC-ERROR", "h_msg_txt": "synthetic"}
    exchanges[1]["response"] = failure
    handler, seen = _f8_handler(exchanges)
    client = f8_client_factory(handler)
    with pytest.raises(api.KorailAppError) as caught:
        client.search_trains(**_f8_arguments()["search_trains"])
    assert caught.value.code == "F8-SYNTHETIC-ERROR"
    assert caught.value.raw == failure
    assert seen == ["5101", exchanges[1]["path"], "5004"]


def test_f8_card_decline_returns_failure_model(f8_client_factory: Callable[..., api.KorailClient]) -> None:
    """NetworkApi.java:631-649 fixes the route; FAIL return is library policy."""
    exchanges = json.loads(json.dumps(F8_CASE_DATA["pay_with_card"]["exchanges"]))
    failure = {"strResult": "FAIL", "h_msg_cd": "F8-CARD-DECLINED", "h_msg_txt": "synthetic"}
    exchanges[1]["response"] = failure
    handler, seen = _f8_handler(exchanges)
    client = f8_client_factory(handler)
    result = client.pay_with_card(**_f8_arguments()["pay_with_card"])
    assert type(result) is api.ReservationPaymentResponse
    assert result.str_result == "FAIL" and result.h_msg_cd == "F8-CARD-DECLINED"
    assert result.raw == failure
    assert seen == ["5101", exchanges[1]["path"], "5004"]
