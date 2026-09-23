# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그·직렬화에 남으면 안 되는 값을 가립니다.

:data:`SENSITIVE_KEYS` = 가려야 할 폼/응답 키 집합. 민감 키의 값은 ``[REDACTED]``,
그 밖의 값에서 발견된 카드번호 모양은 ``[REDACTED_CARD]``.

키 매칭: 대소문자 무시 + 꼬리 인덱스 제거(:func:`is_sensitive_key`).
KORAIL 이 한 필드를 행 번호 붙은 여러 키로 쓰기 때문(``custMgNo_1``, ``txtSeatNo1``).
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION


SENSITIVE_KEYS = frozenset(
    key.casefold()
    for key in {
        # --- 인증·세션 ---
        "txtMemberNo",
        "txtPwd",
        # 소셜 로그인의 고객 식별자(session.login_social). login.Login 에 필드
        # 계약이 생기면서 드러난 빈자리다 -- 그 전에는 어느 계약에도 없었다.
        "custId",
        "password",
        "JSESSIONID",
        "Cookie",
        "Set-Cookie",
        # --- 응답 메시지(서버가 입력을 인용할 수 있으므로) ---
        "h_msg_txt",
        # --- PNR·예약 식별 ---
        "rsvCnt",
        "pnrNo",
        "hidPnrNo",
        "txtPnrNo",
        "txtPrnNo",
        "pnr_no",
        # 반환 응답 철자. 옛 인용 RefundVerifyTicketDao.java:123,151 은 6.5.0
        # 이고 7.0.6 디컴파일에 없다. "prnNo" 라는 철자 자체도 7.0.6 어디에도
        # 없다(jadx 소스 전체 0건, 2026-09-22) -- 7.0.6 의 역창구 반환 검증
        # 응답은 orgtkinfo_list 원소에 "pnr_no" 로 담는다
        # (network/model/Orgtkinfo.java:163,
        #  VerifyOnlineRefundsOut.java:141). 그러므로 이 항목은 7.0.6 에
        # 대응 출처가 없는 방어용 철자다 -- 미출처. 가리는 쪽으로 남겨 두는
        # 것은 무해하므로 지우지 않는다.
        "prnNo",
        "h_pnr_no",
        # ReservationPaymentOut 최상위 예약번호 -- pnrNo/h_pnr_no 와 같은 성질의
        # 식별자인데 철자가 다르다. .raw 로만 나간다
        # (ReservationPaymentOut.java:319, W3 finding 1).
        "h_rsv_no",
        "coptEntRsvNo",
        "pbpRsvNo",
        "pbp_reservation_no",
        "strVrRsvNo",
        "txtVrRsNo",
        "txtVrRsvSqNo",
        "h_vr_rsv_no",
        "virtual_reservation_no",
        "reservation_count",
        # --- 결제·정산 식별 ---
        "tkRetPwd",
        "tkRetNo",
        "h_tk_ret_no",
        # 카드결제 응답 ReservationPaymentOutTkInfo 의 반환 비밀번호 -- 위
        # h_tk_ret_no 와 다른 철자다. .raw 로만 나간다
        # (ReservationPaymentOutTkInfo.java:546, W3 finding 1).
        "h_tk_ret_pwd",
        "ticket_return_no",
        "return_password",
        "saleWctNo",
        "saleDt",
        "saleSqno",
        # 판매일자의 세 번째 철자. 옛 인용 PaymentService.java:12-14 는 6.5.0
        # 이고 7.0.6 에 없으며, 7.0.6 의 결제 요청 DTO
        # (network/model/ReservationPaymentIn.java:29-35) 에는 saleDd 가
        # 아예 없다. 7.0.6 에서 이 철자를 실제로 쓰는 곳은 다음 넷이다:
        #   network/model/DelayReturnReceiptIn.java:77
        #   network/model/SelfCheckInRegisterIn.java:117
        #   network/model/SelfCheckInPossibleIn.java:115
        #   network/model/AcpnMlgSaveRequest.java:125
        # (모두 @SerialName("saleDd")). N카드 기간연장 요청
        # network/model/NCardExtensionIn.java:31 도 같은 이름을 쓴다
        # (@SerialName 없음 -> 프로퍼티 이름이 곧 전선 이름).
        "saleDd",
        "sale_window_no",
        "sale_date",
        # 같은 dataclass 안에서 sale_date 옆에 있는데 이 철자만 빠져 있었다:
        # 와이어 키 h_orgtk_ret_sale_dt 는 등록돼 있어 폼은 가려지지만,
        # redact_value 는 데이터클래스를 field.name 으로 훑으므로
        # TicketListTicket.return_sale_date 만 객체 경로에서 평문으로 남았다.
        # CardPayment.card_password 가 ffb5189 에서 샜던 것과 같은 모양이다.
        "return_sale_date",
        "sale_sequence",
        "h_wct_no",
        "hidWctNo",
        "window_no",
        "h_orgtk_sale_dt",
        "h_orgtk_ret_sale_dt",
        "h_orgtk_wct_no",
        "h_orgtk_sale_sqno",
        "h_orgtk_ret_pwd",
        "h_orgtk_tk_ret_pwd",
        "h_orgtk_sale_wct_no",
        "original_sale_date",
        "original_window_no",
        # 변경 쪽 모델의 철자. read_models 는 original_window_no 로, mutation_models
        # (StationRefundOriginalTicket / StationRefundExecutionRequest) 는 이 이름으로
        # 같은 발매창구번호를 들고 있다. redact_value 는 데이터클래스를 필드명으로
        # 판정하므로(388-412), 철자 하나가 빠지면 그 경로만 원문이 남는다.
        "original_sale_window_no",
        "original_sale_sequence",
        "original_return_password",
        "h_lump_stl_tgt_no",
        "lump_sum_target_no",
        "lumpStlTgtNo",
        "lump_settlement_target_no",
        # 바로 위 짝과 같은 성질인데 양쪽 철자 모두 빠져 있었다
        # (mutation_models.py 가 둘을 나란히 선언한다).
        "dcntCrdStlTgtNo",
        "discount_card_settlement_target_no",
        "lump_settlement_target_nos",
        # --- 카드·결제수단(PaymentMethod 맵, CARD_RE 가 못 잡는 변형) ---
        "hidStlCrCrdNo1",
        "hidVanPwd1",
        "hidCrdVlidTrm1",
        # ``CardPayment`` 의 파이썬 속성명. 바로 위 세 와이어 키와 같은 값인데
        # redact_value 는 데이터클래스를 ``field.name`` 으로 훑으므로(388-412) 폼
        # 딕셔너리만 가려지고 객체 경로는 평문이었다. ``card_number`` 는 CARD_RE 가
        # 우연히 잡아 주지만 그것은 13~19자리 숫자일 때뿐이라 기댈 수 없다.
        "card_number",
        "card_password",
        "card_expire",
        "hidAthnVal1",
        "hidAthnDvCd1",
        "hidIsmtMnthNum1",
        "hidCrdInpWayCd1",
        "mbCrdNo",
        "strMbCrdNo",
        "member_card_no",
        "h_stl_mb_crd_no",
        # ReservationPaymentOut 최상위의 회원카드번호 철자 -- 위 세 개와 다르다.
        # .raw 로만 나간다(ReservationPaymentOut.java:303, W3 finding 1).
        "h_mb_crd_no",
        "h_stl_crd_no",
        "card_no",
        "stlCrdNo",
        "prepCrdNo",
        "prepaid_card_no",
        "settlement_card_no",
        "h_acnt_no",
        "account_no",
        "h_apv_no",
        "apvNo",
        "approval_no",
        "h_xpot_no",
        "point_no",
        # ReservationPaymentOutStlInfo 의 포인트 승인번호 -- h_xpot_no 와 다른
        # 철자다. .raw 로만 나간다
        # (ReservationPaymentOutStlInfo.java:346, W3 finding 1).
        "h_xpoint_apv_no",
        # --- 고객 식별(회원번호·이름·전화·생년) ---
        "custMgNo",
        # custMgNo_1 같은 인덱스 형은 위의 custMgNo 가 이미 가린다(꼬리 인덱스 제거).
        # 이 항목이 더 막는 것은 번호 없는 "custMgNo_" 철자 하나뿐이고, 방어용으로 둔다.
        "custMgNo_",
        "acepCustMgFlg",
        "acepCustMgNo",
        "acepCustNm",
        "acepCustTeln",
        "acepCustTeln2",
        "h_cust_no",
        "hidCustNo",
        "strCustNo",
        "encryptCustNo",
        "customer_no",
        "acceptance_customer_management_flag",
        "acceptance_customer_management_no",
        "acceptance_customer_name",
        "acceptance_customer_phone",
        "acceptance_customer_phone_2",
        # 모델의 파이썬 속성명. 위 acep* 와 아래 wire key 들이 폼 딕셔너리 경로를
        # 덮는 것과 달리, 이 철자들은 redact_value 가 데이터클래스를 필드명으로
        # 훑는 경로(388-412)에서만 나타난다. 전부 이미 repr=False 인 필드들이다 —
        # 표시에서는 숨겨 두고 여기 등록만 빠져 있었다.
        "customer_name",
        "customer_phone",
        # 아래 네 개는 위와 달리 **와이어 키도 함께** 빠져 있었다 — 어느 경로로도
        # 가려진 적이 없다. custNm 은 "이 구간을 실제로 탄 사람의 이름"이고
        # (read_models.py:684), strRsvpsnm 은 예약 승객명이다.
        "passenger_name",
        "custNm",
        "reservation_passenger_name",
        "strRsvpsnm",
        # 회원·비회원 식별자. KorailSession.member_no 와 가격 재계산 요청의
        # non_member_no 로, 둘 다 개인을 지목한다.
        "member_no",
        "non_member_no",
        "customer_management_no",
        "customer_family_name",
        # 다자녀 할인 대상자 행(Fmly)의 와이어 키. 파이썬 속성 customer_family_name 은
        # 이미 repr=False + 위 항목으로 보호되지만, raw=item 으로 나가는 원본 딕트는
        # 이 리터럴이 없으면 가려지지 않는다(Fmly.java:137, W3 finding 3).
        "custFmlyNm",
        "integrated_customer_name_1",
        "integrated_customer_name_2",
        "birth_date",
        # 같은 이유로 다자녀 대상자의 생년월일 와이어 키. birth_date 속성은 이미
        # repr=False + 위 항목으로 보호되지만 raw=item 경로는 별도다
        # (Fmly.java:133, W3 finding 3).
        "btdt",
        "birthday",
        "phone",
        # 로그인 응답 전화번호. 옛 인용 LoginDao.java:84-107 은 6.5.0 이고
        # 7.0.6 에 없다. 7.0.6 대응물은 network/model/LoginOut.java:54 의
        # strCpNo 프로퍼티다. LoginOut 은 @SerialName("Key")(:383) 하나만
        # 명시하고 나머지에는 애노테이션이 없으므로, 이 철자는 프로퍼티
        # 이름에서 온 최선 추정이고 전선 스펠링 자체는 PROTECTED 다
        # (session.py 상단의 LoginOut 필드 주석과 같은 판정).
        "strCpNo",
        "strCustNm",
        "strBtdt",
        "strEmailAdr",
        # 예약대기 전화번호. 옛 인용 ReservationWaitService.java:12 는 6.5.0
        # 이고 7.0.6 에 없다. 7.0.6 대응물은
        # network/model/ReservationWaitIn.java:107 의 @SerialName("txtCpNo")
        # 이며(라우트는 NetworkApi.java:638-640
        # reservationWait.ReservationWait), 같은 DTO 의 나머지 셋은
        # txtPnrNo/txtPsrmClChgFlg/txtSmsSndFlg(:111-119) 다.
        "txtCpNo",
        # 비회원 반환 전화번호. 옛 인용 s5/h.java:123 은 6.5.0 이고 7.0.6 에
        # 없다. 7.0.6 대응물은
        # network/model/ExecuteOnlineRefundsIn.java:122 의
        # @SerialName("custTeln") 이다 -- 역창구 반환 실행
        # (refunds.executeOnlineRefunds, NetworkApi.java:191-193)의 요청
        # 필드이고, 같은 DTO 가 acepCustNm(:118)과 ogtk* 넷(:126-138)을 함께
        # 싣는다.
        "custTeln",
        # 예약 이력(research.reservationView.do) 최상위의 예약자 성명·전화번호.
        # ReservationHistoryResponse.reservation_passenger_name/phone_no 는 이미
        # repr=False 로 보호되지만, .raw 경로는 이 리터럴이 없으면 가려지지 않는다
        # (ReservationViewOut.java:64, h_rsv_ps_nm / h_tel_no).
        "h_rsv_ps_nm",
        "h_tel_no",
        # --- 할인카드(N카드) ---
        # h_dcnt_crd_no 는 bearer credential. 옛 인용 w4/a.java:100-101 은
        # 6.5.0 이고 7.0.6 에 없다. 7.0.6 에서 bearer 라는 판정을 뒷받침하는
        # 것은 두 곳이다: 응답 쪽 철자는
        # network/model/DiscountCardInfo.java:113 의
        # @SerialName("h_dcnt_crd_no") 이고, 요청 쪽에서는
        # common/define/Passengers.java:731,766 이 N카드 예약
        # (ReservationType.MY_N_CARD_RESERVATION)일 때 카드번호 문자열을
        # 그대로 TicketReservationInPassengerInfo 의 네 번째 인자로 넘긴다 --
        # 그 필드의 전선 이름이
        # network/model/TicketReservationInPassengerInfo.java:105 의
        # @SerialName("txtCardNo_") 이고, 같은 DTO 에 카드 비밀번호 필드는
        # 없다(:31-34 가 전부). 즉 번호만으로 할인이 붙는다.
        "dcntCrdNo",
        "h_dcnt_crd_no",
        "discount_card_no",
        # ReservationPaymentOutTkInfo 의 할인카드번호 철자 -- 위 두 철자와 다르다.
        # .raw 로만 나간다(ReservationPaymentOutTkInfo.java:414, W3 finding 1).
        "h_disc_card_no",
        *(f"txtCardNo_{i}" for i in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)),
        "txtCardNo",
        # 할인카드(N카드) 2인용의 추가 사용자. 옛 인용
        # NCardReservationDao.java:16,29,30 은 6.5.0 이고 7.0.6 에 없다.
        # 7.0.6 대응물은 network/model/NCardInfoIn.java:30-31 이고, 거기서는
        # 이름에 이미 인덱스가 박혀 있다 -- apdCustName_1 / apdCustTeln_1
        # (@SerialName 없음 -> 프로퍼티 이름이 곧 전선 이름). 아래 두
        # 리터럴은 인덱스를 뗀 형태이고, is_sensitive_key 가 꼬리 인덱스를
        # 떼고 다시 보므로 apdCustName_1 도 걸린다.
        "apdCustName",
        "apdCustTeln",
        # --- 현금영수증(개인 소득공제에 붙는 번호, 속성명·와이어 키 둘 다 누락돼 있었다) ---
        "receipt_no",
        "rcptNo",
        "cash_receipt_approval_no",
        "cashRcetApvNo",
        "h_cash_rcet_apv_no",
        "authentication_recognition_no",
        "authentication_domain_recognition_no",
        "h_athn_dmn_rcgn_no",
        # --- 승객유형명(코드가 아닌 사람이 읽는 라벨) ---
        # 정책: 사람이 읽는 값은 가리고 코드(psg_tp_dv_cd)는 남긴다.
        "psgTpDvNm",
        "psgTpNm",
        "h_psg_tp_nm",
        "h_dcnt_knd_nm",
        "h_subt_dcs_cl_nm",
        "passenger_type_division_name",
        "member_division_name",
        "acceptance_kind_name",
        "mbDvNm",
        "pbpAcepKndNm",
        # --- 좌석·객실·플랫폼 ---
        "psrmClCd",
        "psrmClNm",
        "psrm_cl_cd",
        "psrm_cl_nm",
        "room_class_code",
        "room_class_name",
        "scarNo",
        "scar_no",
        "seatNo",
        "plfNo",
        "car_no",
        "seat_no",
        "platform_no",
        "h_srcar_no",
        "h_seat_no",
        "h_plf_no",
        # 좌석 지정 출력. 옛 인용 SeatSearchActivity.java:679-680 은 6.5.0
        # 이고 7.0.6 에 없다. 7.0.6 대응물은
        # network/model/TicketReservationInSrcar.java:81-88 의
        # @SerialName("txtSeatNo") / @SerialName("txtSrcarNo") 이고, 값을
        # 채우는 곳은 ui/screen/train/TrainSeatMapViewModel.java:2210
        # (buildTicketReservationIn(), :1989) 이다.
        #
        # 주의: 후속 구간용 형제 DTO
        # network/model/TicketReservationInSrcarTrailing.java:82-89 는
        # @SerialName("txtSeatNo1_") / @SerialName("txtSrcarNo1_") -- 인덱스
        # 뒤에 밑줄이 더 붙는다. _index_stripped 는 꼬리 숫자만 떼므로 그
        # 철자는 아래 열거에 걸리지 않는다. 규칙을 넓히는 것은 이 작업의
        # 범위가 아니라 별도 판단이 필요하므로 여기서는 사실만 적어 둔다.
        *(f"txtSrcarNo{i}" for i in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)),
        *(f"txtSeatNo{i}" for i in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)),
        "txtSrcarNo",
        "txtSeatNo",
        # --- 쿠폰·할인증명·임시직렬 ---
        "h_coup_no",
        "h_cpn_no",
        "h_cert_pwd",
        "coupon_no",
        "certificate_password",
        "hidDscpNo",
        # 다자녀 가족 구성원 일련번호. 옛 인용 a6/C1041A.java:75 는 6.5.0
        # 이고 7.0.6 에 없다. 7.0.6 에서 이 필드에 빈 값이 아닌 것을 넣는
        # 곳은 ui/screen/pay/PayViewModel.java:16863 한 줄뿐이고
        # (setHidFmlyNo(payFmly.getFmly().getFmlySqno())), 출처 키는
        # network/model/Fmly.java:145 의 @SerialName("fmlySqno") 다. 전선
        # 이름 hidFmlyNo 자체는
        # network/model/PriceReCalculationInPassengerInfo.java:139 와
        # NetworkApi.java:584 의 @Field("hidFmlyNo") 에서 확인된다.
        "hidFmlyNo",
        "hidRsvChgNo",
        "h_rsv_chg_no",
        "reservation_change_no",
        "h_tmp_job_sqno1",
        "h_tmp_job_sqno2",
        "hidTmpJobSqno1",
        "hidTmpJobSqno2",
        "temporary_job_sequence_1",
        "temporary_job_sequence_2",
        "temporary_job_sequence",
        "tmpJobSqno",
        "chgTno",
        # --- DynaPath·부가서비스·기타 ---
        "x-dynapath-m-token",
        "mutMrkVrfCd",
        "verification_code",
        "addSrvDvCd",
        "additional_service_code",
        "addSrvReqNo",
        "partner_reservation_no",
        "jrnyTpCd",
        "journey_type_code",
        "regDt",
        "registered_date",
        "wdrwPsbFlg",
        "withdrawal_possible_flag",
        "url",
        "image",
        "menuUrl",
        "contUrl",
        "contImage",
        # --- 구매자·동반자·좌석그룹 이름 ---
        "h_sgr_nm",
        "h_buy_ps_nm",
        # ReservationPaymentOutTkInfo 의 수령인 성명. .raw 로만 나간다
        # (ReservationPaymentOutTkInfo.java:522, W3 finding 1).
        "h_take_name",
        "h_compa_nm",
        "h_compa_brth",
        # 동승자(h_compa_nm/h_compa_brth) 바로 옆에 선언된, 탑승자 본인의 성명·
        # 생년월일. 파싱도 마스킹도 안 되어 있었다 -- s_brth 는 숫자로 끝나지 않아
        # _index_stripped 가 안 잡으므로 순수 리터럴로 등록한다
        # (TicketDetailOut.java:410,418, W3 finding 2).
        "h_abrd_ps_nm",
        "s_brth",
        "h_comp_nm",
        "h_comp_cert_no",
        "h_wct_nm",
        "seat_group_name",
        "buyer_name",
        "companion_name",
        "companion_birth_date",
        "window_name",
        "certificate_no",
        # --- 반환번호 4분할 ---
        # 16자리가 5/4/5/2 로 분할되어 CARD_RE 에 안 걸림.
        # 옛 인용 RefundService.java:33 은 6.5.0 이고 7.0.6 에 없다. 7.0.6
        # 대응물은 network/model/VerifyOnlineRefundsIn.java:102-114 의
        # @SerialName("retNo1"..."retNo4") 네 개이고, 라우트는
        # NetworkApi.java:810-812 (refunds.verifyOnlineRefunds) 다. 같은 DTO
        # 가 요청자 이름 strName(:118)까지 다섯 필드가 전부다.
        "retNo1",
        "retNo2",
        "retNo3",
        "retNo4",
        "retNo",
        "return_no_1",
        "return_no_2",
        "return_no_3",
        "return_no_4",
        "return_no",
        # 요청자 이름. 옛 인용 s5/c.java:71 은 6.5.0 이고 7.0.6 에 없다.
        # 7.0.6 에서 "strName" 이라는 전선 키는 딱 한 군데,
        # network/model/VerifyOnlineRefundsIn.java:118 의 @SerialName 뿐이다
        # (위 retNo1~4 와 같은 DTO -- 역창구 반환 검증의 본인 확인 이름).
        "strName",
        "requester_name",
        "requester_phone",
        # --- 원표 4분할 ---
        # 옛 인용 ROrtg.java:8-11 과 RefundService.java:17 은 6.5.0 이고
        # 7.0.6 에 없다. 7.0.6 에서 같은 네 조각이 철자 셋으로 갈린다:
        #   camelCase + "Sale" : network/model/ExecuteOnlineRefundsIn.java
        #       :126-138 (ogtkRetPwd / ogtkSaleDt / ogtkSaleSqno /
        #       ogtkSaleWctNo) -- 역창구 반환 실행 요청
        #   camelCase, "Sale" 없음 : network/model/ReservationOrgTk.java
        #       :141-153 (ogtkRetPwd / ogtkSaleDt / ogtkSaleSqno / ogtkWctNo)
        #   snake_case : network/model/Orgtkinfo.java:147-159
        #       (ogtk_ret_pwd / ogtk_sale_dt / ogtk_sale_sqno /
        #       ogtk_sale_wct_no) -- verifyOnlineRefunds 응답의
        #       orgtkinfo_list 원소
        # ogtkSaleDd 는 또 다른 철자로, network/model/DelayCertificateIn.java
        # :96 의 @SerialName("ogtkSaleDd") 에서 확인된다.
        "ogtkSaleDt",
        "ogtkSaleDd",
        "ogtkSaleWctNo",
        # 예약 이력의 ReservationOrgTk 가 쓰는 발매창구번호 철자 -- 위
        # ogtkSaleWctNo 와 다르다("Sale" 없음). .raw 로만 나간다
        # (ReservationOrgTk.java, ReservationHistoryOriginalTicket.window_no).
        "ogtkWctNo",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "ogtk_ret_pwd",
        "ogtk_sale_dt",
        "ogtk_sale_sqno",
        "ogtk_sale_wct_no",
        "original_sale_datetime",
        # --- 지연증명 원표 ---
        # 클래스는 7.0.6 에도 같은 이름으로 살아 있고 패키지만 옮겼다:
        # network/model/Cmpn.java:35-38 이 dlayOgtkRetPwd / dlayOgtkSaleDt /
        # dlayOgtkSaleSqno / dlayOgtkWctNo 를 선언한다(@SerialName 없음 ->
        # 프로퍼티 이름이 곧 전선 이름). 옛 경로
        # response/research/Cmpn.java:11-14 는 7.0.6 에 없다. 같은 네 철자
        # 중 둘은 예약 응답에도 있다 --
        # network/model/ReservationOutPsgInfo.java:130,134.
        "dlayOgtkRetPwd",
        "dlayOgtkSaleDt",
        "dlayOgtkSaleSqno",
        "dlayOgtkWctNo",
        "delay_certificate_return_password",
        "delay_certificate_sale_date",
        "delay_certificate_sale_sequence",
        "delay_certificate_window_no",
        # --- 구매내역 ---
        "h_purchase_history",
        # --- poppMsg(서버 합성 안내, 입력 인용 가능) ---
        # 옛 인용 RefundVerifyTicketDao.java:66 은 6.5.0 이고 7.0.6 에 없다.
        # 7.0.6 대응물은 network/model/VerifyOnlineRefundsOut.java:145 의
        # @SerialName("poppMsg") 다(같은 응답의 나머지는 orgtkinfo_list,
        # rcvd_amt, ret_amt, ret_fee, strMsg -- :141-165).
        "poppMsg",
        "popup_message",
        # --- 이중 인덱스 키(outer=journey/passenger, inner=seat/discount row) ---
        # _index_stripped 는 인덱스 하나만 떼므로 이중 인덱스는 열거 필요
        *(
            f"{prefix}{outer}_{inner}"
            for prefix in (
                "scarNo_",
                "seatNo_",
                "roomClsfCd_",
                "seatPsrmClCd_",
                "dscpNo_",
                "dlayOgtkWctNo_",
                "dlayOgtkSaleDd_",
                "dlayOgtkSaleSqno_",
                "dlayOgtkRetPwd_",
            )
            for outer in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
            for inner in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        ),
    }
)

#: 꼬리 인덱스는 숫자로 끝나기도 하고 **숫자 뒤에 밑줄**이 더 붙기도 합니다 —
#: 앱이 실제로 그 모양을 씁니다: ``TicketReservationInSrcarTrailing.java:82-89``
#: 의 ``@SerialName`` 은 ``txtSrcarNo1_``·``txtSeatNo1_`` 이고,
#: ``TicketReservationInPassengerInfo.java:105`` 는 ``txtCardNo_`` 입니다.
#: 예전 패턴은 끝의 숫자만 떼서 그 셋을 전부 놓쳤습니다 —
#: ``is_sensitive_key("txtSrcarNo1_")`` 가 거짓이었고, 카드번호 키까지 포함해
#: 그대로 로그에 찍힐 수 있었습니다(2026-09-22 확인).
#: 인덱스 앞에도 밑줄이 붙는 모양이 있습니다 — ``h_sgr_nm_1``·``h_sgr_nm_2``
#: (``ReservationPaymentOutTblSeatInfo.java:166-170``). 인덱스 없이 밑줄만
#: 붙는 모양도 있습니다 — ``txtCardNo_``
#: (``TicketReservationInPassengerInfo.java:105``).
#:
#: 이 패턴 하나를 :func:`_index_stripped` 와 :data:`SENSITIVE_KEY_VALUE_RE` 가
#: **함께** 씁니다. 나눠 적었을 때 실제로 갈라졌습니다: 키 판정은 인덱스 앞
#: 밑줄을 떼는데 텍스트 탐지는 안 떼서, ``is_sensitive_key("h_sgr_nm_1")`` 은
#: 참인데 ``redact_text("h_sgr_nm_1=...")`` 는 값을 그대로 남겼습니다 —
#: 즉 dict 는 가려지고 같은 값이 문자열·JSON·상대 URL 로 로그에 실리면
#: 평문이었습니다(2026-09-23 확인).
_INDEX_SUFFIX_PATTERN = r"(?:_?\d+_?|_)"

_INDEX_SUFFIX_RE = re.compile(r"^(?P<base>.*?)" + _INDEX_SUFFIX_PATTERN + r"$")


def _index_stripped(name: str) -> str | None:
    """꼬리 인덱스를 뗀 이름. 없으면 ``None``."""
    match = _INDEX_SUFFIX_RE.match(name)
    if match is None:
        return None
    return match.group("base") or None


def is_sensitive_key(name: str) -> bool:
    """``name`` 이 민감 값의 이름인지. 대소문자 무시 + 꼬리 인덱스 제거."""
    folded = name.casefold()
    if folded in SENSITIVE_KEYS:
        return True
    base = _index_stripped(folded)
    return base is not None and base in SENSITIVE_KEYS


# W4 finding: a bare 13-digit epoch-millisecond timestamp (int(time.time() *
# 1000) is exactly 13 digits from 2001 through 2286) collides with this
# pattern's old 13-digit floor. This package builds and sends such a value
# under the wire key "timeStamp" (payloads.py build_cache_query and friends,
# MobileServiceIn.java:30 confirms the same shape server-side) -- and since
# is_sensitive_key("timeStamp") is correctly False, the value still reaches
# redact_text via redact_url's fallback, so a real diagnostic timestamp was
# being destroyed as "[REDACTED_CARD]" in any log routed through this module.
# Raising the floor to 14 digits excludes that collision. The trade-off is
# narrower coverage for the least common card length (13-digit schemes, e.g.
# some older Visa numbers) in UNSTRUCTURED text with no key context -- the
# PRIMARY defense for a known card_number field is still its SENSITIVE_KEYS
# registration, unaffected by this regex either way.
_WHITESPACE_RE = re.compile(r"\s")

#: :func:`_parse_json_document` 의 "JSON 아님" 표식. ``None`` 은 유효한
#: JSON 값(``null``)이라 구분자로 쓸 수 없습니다.
_NO_JSON = object()

#: ``scheme://아이디:비밀번호@host`` 의 자격증명. :func:`redact_url` 은 netloc 을
#: 뜯어보지만 :func:`redact_text` 는 URL 을 파싱하지 않으므로, 로그 한 줄에 박힌
#: URL 은 여기서 잡아야 합니다. ``://`` 뒤에서만 보므로 ``a:b@c`` 같은 평범한
#: 문자열은 건드리지 않습니다 — **``:`` 를 요구하지는 않습니다.** 사용자명만
#: 있는 userinfo 도 자격증명입니다.
#: ``[^/?#\s]*@`` 가 탐욕적이라 authority 안의 **마지막** ``@`` 까지 먹습니다.
#: 예전 패턴 ``[^/\s@]+:[^/\s@]*@`` 는 세 가지를 틀렸습니다(2026-09-23 확인):
#: ``:`` 를 요구해서 ``https://비밀@host`` 처럼 사용자명만 있는 형태를 놓쳤고,
#: 첫 ``@`` 에서 멈춰 ``user:pass@비밀@host`` 의 꼬리를 남겼으며, ``?``·``#``
#: 를 경계로 보지 않아 ``https://host:443?contact=a@b`` 의 **호스트와 공개
#: 쿼리까지** userinfo 로 오인해 지웠습니다.
URL_USERINFO_RE = re.compile(r"(?<=://)[^/?#\s]*@")

CARD_RE = re.compile(r"\b(?:\d[ -]*?){14,19}\b")
#: 앞에 시작 경계가 없으면 ``notJSESSIONID=공개값`` 처럼 **민감 키가 아닌**
#: 이름의 값까지 가렸습니다 — ``is_sensitive_key("notJSESSIONID")`` 는 거짓인데
#: 이 정규식만 따로 먹었습니다(2026-09-23 확인). 누출은 아니지만 진단 정보가
#: 사라집니다.
SESSION_RE = re.compile(r"(?i)(?<![\w-])(JSESSIONID=)[^&;\s]+")
#: 키의 ``_``/``-`` 는 퍼센트 인코딩된 ``%5F``/``%2D`` 로도 실려 옵니다. 절대
#: URL 은 :func:`redact_url` 이 키를 디코딩해서 보지만 텍스트 경로는 못 봤습니다
#: — 같은 값이 진입점에 따라 갈렸습니다(2026-09-23 확인).
#:
#: 한때 여기 "민감 키의 비영숫자는 ``_`` 뿐"이라고 적고 밑줄만 다뤘는데
#: **틀렸습니다** — ``set-cookie`` 와 ``x-dynapath-m-token`` 에 ``-`` 가
#: 있습니다. 그 둘을 함께 다룹니다. 나머지 문자까지 인코딩된 형태는 이 경로가
#: 여전히 **다루지 않습니다**.
def _percent_tolerant(key: str) -> str:
    escaped = re.escape(key)
    escaped = escaped.replace("_", "(?:_|%5[Ff])")
    return escaped.replace(r"\-", "(?:-|%2[Dd])").replace("-", "(?:-|%2[Dd])")


SENSITIVE_KEY_VALUE_RE = re.compile(
    r"(?P<prefix>(?<![\w-])(?P<key_quote>[\"']?)(?:"
    + "|".join(
        sorted(
            (_percent_tolerant(key) for key in SENSITIVE_KEYS),
            key=len,
            reverse=True,
        )
    )
    # 꼬리 인덱스는 :data:`_INDEX_SUFFIX_PATTERN` — 키 판정과 **같은** 규칙을
    # 씁니다. 이것이 없으면 ``txtSeatNo`` 는 가려지는데 ``txtSeatNo1_`` 은
    # 그대로 남았습니다: 키 뒤의 ``(?![\w-])`` 가 인덱스 숫자에서 막혀 아예
    # 매치가 안 됐기 때문입니다.
    + r")"
    + _INDEX_SUFFIX_PATTERN
    + r"?(?P=key_quote)(?![\w-])\s*(?:(?P<eq>=)|:)(?P<gap>[ \t]+)?)"
    # 값의 끝을 어디로 볼지는 **묶는 기호에 따라 다릅니다**. 한 규칙으로
    # 밀어붙였다가 실제로 누출을 만들었습니다: ``&``/``;`` 를 값에서 무조건
    # 빼도록 고쳤더니 구분자가 값 **안**에 있는 ``Cookie: a=1;other=<비밀>``
    # 과 ``txtPwd=HEAD&<비밀>`` 의 꼬리가 평문으로 남았습니다(2026-09-23).
    # 과잉 마스킹을 누출과 바꾼 셈이라 방향이 틀렸습니다 — 마스킹은 애매하면
    # 더 가리는 쪽이어야 합니다.
    #
    # * ``:`` 로 묶이면(헤더·산문) 값은 공백/쉼표까지 그대로 갑니다. 쿠키
    #   헤더의 ``;`` 와 ``=`` 는 값의 일부입니다.
    # * ``=`` 로 묶이면(쿼리 파라미터) ``&``/``;`` 는 **뒤에 새 ``키=`` 가
    #   따라올 때만** 값을 끝냅니다. 그래야 ``txtSeatNo1_=X&trnNo1=Y`` 의
    #   이웃은 살고, ``txtPwd=HEAD&<비밀>`` 의 꼬리는 함께 가려집니다.
    + r'(?P<value>"(?:\\.|[^"\\])*(?:"|$)'
    + r"|'(?:\\.|[^'\\])*(?:'|$)"
    # 직렬화된 배열·객체는 한 덩어리로 먹습니다. scalar 정규식으로 다루면
    # ``{"hidDscpNo": ["a", "<비밀>"]}`` 가 첫 원소만 가려졌습니다.
    + r"|\[[^\[\]]*\]"
    + r"|\{[^{}]*\}"
    # ``=`` 묶음: 값이 그 자체로 ``키=`` 로 시작하면 그것은 값이 아니라
    # **다음 필드**입니다. 앞의 ``\s*`` 가 공백을 넘어가서
    # ``h_sgr_nm_1= trnNo1=Y`` 의 ``trnNo1=Y`` 를 값으로 먹던 자리입니다.
    # 구분자로 **시작**하는 값: 뒤에 새 ``키=`` 가 붙을 때만 다음 필드로 보고
    # 비켜 줍니다(``h_sgr_nm_1=&trnNo1=Y``). 그냥 ``txtPwd=&<비밀>`` 이면
    # ``&<비밀>`` 이 값입니다 — 무조건 막았더니 그 꼬리가 평문으로 남았습니다.
    #
    # ``키=`` 로 보이면 다음 필드라는 가드는 **공백이 있었을 때만** 겁니다.
    # 무조건 걸었더니 ``txtPwd=U0VDUkVUQQ==`` 같은 base64 패딩 값과 ``=`` 를
    # 품은 값이 통째로 다음 필드 취급돼 평문으로 남았습니다(2026-09-23 확인).
    # 공백이 없으면 ``키=값`` 한 덩어리이므로 가드가 필요 없습니다.
    # ``=`` 뒤에 서식 공백이 있을 때 "다음 필드처럼 생겼으면 비켜 준다"는
    # 가드는 **뺐습니다**. 그 가드는 ``h_sgr_nm_1= trnNo1=X`` 의 이웃을 살리려는
    # 것이었는데, ``txtPwd= <base64>`` 처럼 ``=`` 를 품은 정상 값까지 다음
    # 필드로 보고 평문으로 남겼습니다(2026-09-23 확인). 자유 텍스트에서 그
    # 둘은 구분되지 않습니다. 이 함수는 **애매하면 더 가리는 쪽**이므로,
    # 공백 뒤의 토큰은 값으로 봅니다 — 이웃 필드가 함께 가려질 수 있고 그것은
    # 진단 정보 손실이지 누출이 아닙니다. 이웃을 살려야 하는 쪽은 구조화된
    # 입구(:func:`redact_mapping`·:func:`redact_payload`·:func:`redact_url`)를
    # 쓰십시오.
    + r"|(?(eq)(?![&;][\w.%\[\]-]+=)[^\s,]+?"
    + r"(?=(?:[&;](?=[\w.%\[\]-]+=))|[\s,]|$)"
    + r"|[^\s,]+))",
    re.IGNORECASE,
)


def _redact_sensitive_key_value(match: re.Match[str]) -> str:
    value = match.group("value")
    quote = (
        value[0]
        if len(value) >= 2
        and value[0] in {'"', "'"}
        and value[-1] == value[0]
        else ""
    )
    return f"{match.group('prefix')}{quote}[REDACTED]{quote}"


class _Pairs:
    """JSON 객체를 **키-값 쌍의 순서 있는 목록**으로 들고 있습니다.

    ``dict`` 로 받으면 중복 키의 앞 값이 사라집니다. 그래서 한때 중복 키를
    감지하면 구조 마스킹을 통째로 포기하고 정규식 경로로 넘겼는데, 그쪽은
    ``\\u005f`` 로 escape 된 민감 키를 못 봅니다 — **원문을 지키려다 비밀값을
    남겼습니다**(2026-09-23 확인). 둘을 맞바꿀 필요가 없습니다: 쌍을 그대로
    들고 다니면 중복 키도 보존하면서 구조로 가릴 수 있습니다.
    """

    __slots__ = ("items",)

    def __init__(self, items: list[tuple[str, Any]]) -> None:
        self.items = items


class _RawNumber:
    """JSON 숫자를 **원문 그대로** 들고 있습니다.

    ``float`` 로 받으면 ``0.1234567890123456789`` 의 자릿수가 줄고 ``1e400`` 이
    ``Infinity`` 가 됩니다. 원문 문자열을 그대로 다시 쓰면 그 손실이 없습니다.
    """

    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text


def _parse_json_document(value: str) -> object:
    """문자열 전체가 JSON 이면 손실 없는 표현으로, 아니면 ``_NO_JSON``.

    구조로 다뤄야 정규식이 못 보는 두 모양을 받습니다 — escape 된 키
    (``{"h\\u005fsgr\\u005fnm_1": ...}`` 는 파싱해야 민감 키로 보입니다)와
    중첩 배열·객체(키의 민감성이 값 **트리 전체**에 걸립니다).
    """
    stripped = value.strip()
    if not stripped or stripped[0] not in '{["':
        return _NO_JSON
    try:
        return json.loads(
            stripped,
            object_pairs_hook=_Pairs,
            parse_float=_RawNumber,
            parse_int=_RawNumber,
            parse_constant=_RawNumber,
        )
    except (ValueError, TypeError, RecursionError):
        return _NO_JSON


def _redact_json_double_encoded(node: object) -> str | None:
    """JSON **문자열 안에** JSON 이 든 경우. 아니면 ``None``.

    ``"{\\"k\\": \\"v\\"}"`` 처럼 한 겹 더 싸인 모양은 바깥 값이 문자열이라
    구조 순회가 들어가지 못합니다. 안쪽을 다시 :func:`redact_text` 에 넣고
    문자열로 다시 씁니다.
    """
    if not isinstance(node, str):
        return None
    inner = redact_text(node)
    return json.dumps(inner) if inner != node else None


def _redact_json_node(node: object, *, key: str | None = None) -> object:
    """파싱된 JSON 트리를 가립니다. 키가 민감하면 **값 트리 전체**가 대상입니다."""
    if key is not None and is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(node, _Pairs):
        return _Pairs(
            [(name, _redact_json_node(item, key=name)) for name, item in node.items]
        )
    if isinstance(node, list):
        return [_redact_json_node(item) for item in node]
    if isinstance(node, _RawNumber):
        # 카드번호 모양은 키와 무관하게 값 자체로 잡습니다. 예전에는 다 쓴
        # JSON 문자열에 :data:`CARD_RE` 를 덧칠했는데, 그러면 치환 문자열에
        # 따옴표가 없어 **출력이 JSON 이 아니게** 되고 숫자 키까지 같은
        # 문자열로 바뀌어 서로 다른 항목이 합쳐졌습니다(2026-09-23 확인).
        return (
            "[REDACTED_CARD]"
            if CARD_RE.fullmatch(node.text)
            else node
        )
    if isinstance(node, str):
        return _redact_json_scalar(node)
    return node


def _redact_json_scalar(text: str) -> str:
    """JSON 문자열 값 하나. 키 규칙은 이미 위에서 봤으므로 값 패턴만 겁니다."""
    masked = URL_USERINFO_RE.sub("[REDACTED]@", text)
    masked = CARD_RE.sub("[REDACTED_CARD]", masked)
    return SESSION_RE.sub(r"\1[REDACTED]", masked)


def _dump_json(node: object) -> str:
    """:func:`_parse_json_document` 가 만든 트리를 다시 씁니다.

    ``json.dumps`` 를 쓰지 않는 이유는 :class:`_Pairs` 와 :class:`_RawNumber`
    때문입니다 — 중복 키와 숫자 원문을 지켜야 합니다. 문자열은 ``json.dumps``
    에 맡기므로 짝 없는 surrogate 도 ``\\ud800`` escape 로 나가고, 결과를
    UTF-8 로 인코딩하는 다음 단계가 터지지 않습니다.
    """
    if isinstance(node, _Pairs):
        inner = ", ".join(
            f"{json.dumps(name)}: {_dump_json(item)}" for name, item in node.items
        )
        return "{" + inner + "}"
    if isinstance(node, list):
        return "[" + ", ".join(_dump_json(item) for item in node) + "]"
    if isinstance(node, _RawNumber):
        return node.text
    if node is True:
        return "true"
    if node is False:
        return "false"
    if node is None:
        return "null"
    return json.dumps(node)


def redact_text(value: str) -> str:
    """문자열에서 카드번호·세션·민감 키값을 가립니다.

    **알려진 한계 — 따옴표 없는 값 안의 공백.** ``h_sgr_nm_1=홍 길동`` 처럼
    인용하지 않은 값에 공백이 있으면 공백까지만 가려지고 뒤가 남습니다.
    공백을 값의 일부로 보려면 ``h_sgr_nm=X 이후 문장 전체``를 먹어야 해서,
    로그 한 줄이 통째로 사라집니다. 평문에서 그 둘은 구분할 수 없습니다.

    그래서 이 함수는 **따옴표 없는 값에 공백이 없다고 가정합니다.** 실제로
    공백이 들어가는 값은 구조화된 입구로 넘기십시오 — ``redact_mapping``·
    ``redact_payload``·``redact_url`` 은 키 단위로 보므로 값 안의 공백과
    무관하게 전부 가립니다.

    **그 경로를 타는 것은 호출자의 몫입니다.** 한때 여기 "폼을 만드는 이
    패키지 자신은 언제나 그 경로를 쓴다"고 적었는데 사실이 아닙니다. 이
    패키지가 스스로 부르는 마스킹은 :mod:`korail_mobile_api.errors` 의 예외
    생성자 안 :func:`redact_text` 뿐이고, 빌더가 돌려준 폼은 **가려지지 않은
    채로** 넘어옵니다. 그것을 로그에 찍기 전에 :func:`redact_payload` 를
    부르는 쪽은 호출자입니다(2026-09-23 확인).
    """
    # ``{\\"k\\": \\"v\\"}`` 처럼 백슬래시로 escape 된 채 로그에 실린 JSON 은
    # 그 자체로는 파싱되지 않습니다. 한 겹 벗겨 보고, 되면 원래 모양대로
    # 다시 escape 해 돌려줍니다.
    escaped = False
    parsed = _parse_json_document(value)
    if parsed is _NO_JSON and '\\"' in value:
        parsed = _parse_json_document(value.replace('\\"', '"'))
        escaped = parsed is not _NO_JSON
    if parsed is not _NO_JSON:
        dumped = _redact_json_double_encoded(parsed)
        if dumped is None:
            dumped = _dump_json(_redact_json_node(parsed))
        if dumped is not None:
            if escaped:
                dumped = dumped.replace('"', '\\"')
            # 구조 처리로 끝내지 않습니다. 카드번호 모양과 세션 토큰은 키와
            # 무관하게 값 자체로 잡는 것이라, 여기서 빠뜨리면 JSON 으로 실린
            # 카드번호만 예외가 됩니다 — 실제로 ``{"debug": 4111…}`` 가
            # 그대로 남았습니다(2026-09-23 확인).
            return dumped
    redacted = URL_USERINFO_RE.sub("[REDACTED]@", value)
    redacted = CARD_RE.sub("[REDACTED_CARD]", redacted)
    redacted = SENSITIVE_KEY_VALUE_RE.sub(
        _redact_sensitive_key_value,
        redacted,
    )
    return SESSION_RE.sub(r"\1[REDACTED]", redacted)


def redact_url(value: str) -> str:
    """URL 을 가립니다. 쿼리는 키 단위로, 경로와 fragment 는 :func:`redact_text` 로.

    경로도 봐야 하는 이유: 서블릿은 쿠키가 없으면 세션을 ``;jsessionid=...`` 로
    경로에 붙이고, fragment 에는 ``key=value`` 가 그대로 실릴 수 있습니다.
    폴백 규칙: scheme/netloc 이 없으면 보통 :func:`redact_text` 로 갑니다.
    **예외가 하나 있습니다** — 경로가 ``/`` 로 시작하고 쿼리에 공백이 없으면
    상대 URL 로 보고 쿼리를 키 단위로 처리합니다. 그렇게 하지 않으면 퍼센트
    인코딩된 키가 절대 URL 로는 가려지고 상대 URL 로는 남았습니다.
    """
    try:
        parsed = urlsplit(value)
    except ValueError:
        # ``urlsplit`` 은 URL 이 아닌 문자열에 예외를 냅니다 — 예: 대괄호가
        # 닫히지 않은 ``https://[`` (IPv6 리터럴로 읽다가 실패). 이 함수는
        # :func:`redact_value` 를 통해 **임의의 문자열**에 불리므로, 그
        # 예외는 마스킹을 건너뛰게 만드는 대신 로깅 자체를 깨뜨립니다.
        # 파싱이 안 되면 URL 이 아닌 것으로 보고 텍스트 경로로 갑니다.
        return redact_text(value)
    # 절대 URL 이 아니어도 **경로+쿼리 모양**이면 쿼리를 키 단위로 봅니다.
    # ``urlsplit`` 은 상대 URL 에서도 ``query`` 를 이미 갈라 주는데, 예전에는
    # 그것을 버리고 통째로 :func:`redact_text` 로 보냈습니다. 그래서 같은 값이
    # 진입점에 따라 갈렸습니다: 퍼센트 인코딩된 키(``h%5Fsgr%5Fnm``)가 절대
    # URL 로는 가려지고 상대 URL 로는 평문으로 남았습니다(2026-09-23 확인) —
    # 키 단위 경로는 키를 디코딩해서 보고 텍스트 경로는 못 하기 때문입니다.
    #
    # ``path`` 가 ``/`` 로 시작할 때만 이 길로 보냅니다. 그 조건이 없으면
    # ``"오류? a=b"`` 같은 **평범한 문장**이 URL 로 해석돼서 ``urlencode`` 에
    # 뭉개집니다 — 이 함수는 :func:`redact_value` 를 통해 임의의 문자열에
    # 불리므로 그쪽이 훨씬 흔합니다.
    # ``/`` 로 시작한다는 것만으로는 부족했습니다: ``/로그? a=b 입니다`` 같은
    # **문장**이 쿼리로 해석돼 공백이 ``+`` 로 바뀌었습니다(2026-09-23 확인).
    # 진짜 쿼리 문자열에는 인코딩되지 않은 공백이 없으므로 그것으로 가릅니다.
    relative_with_query = (
        not parsed.scheme
        and not parsed.netloc
        and parsed.query
        and parsed.path.startswith("/")
        and not _WHITESPACE_RE.search(parsed.query)
    )
    if (not parsed.scheme or not parsed.netloc) and not relative_with_query:
        return redact_text(value)
    query = [
        (
            key,
            "[REDACTED]" if is_sensitive_key(key) else redact_text(item),
        )
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    # ``https://아이디:비밀번호@host/...`` 의 userinfo 는 netloc 안에 있어서
    # 쿼리·경로만 보던 예전 코드가 통째로 지나쳤습니다. 회원번호도 비밀번호도
    # 여기 실릴 수 있으므로 **둘 다** 가립니다(2026-09-23 확인).
    netloc = parsed.netloc
    if parsed.username is not None or parsed.password is not None:
        host = netloc.rsplit("@", 1)[-1]
        netloc = f"[REDACTED]@{host}"
    return urlunsplit(
        (
            parsed.scheme,
            netloc,
            redact_text(parsed.path),
            urlencode(query),
            redact_text(parsed.fragment),
        )
    )


def redact_value(value: Any, *, key: str | None = None) -> Any:
    """임의의 값을 재귀적으로 가립니다.

    매핑→키마다, 리스트/튜플→원소마다(컨테이너 타입 유지), 데이터클래스→필드별
    dict, 문자열→:func:`redact_url`. 나머지 타입은 그대로.
    """
    if key is not None and is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {
            item_key: redact_value(item, key=str(item_key))
            for item_key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: redact_value(getattr(value, field.name), key=field.name)
            for field in fields(value)
        }
    if isinstance(value, str):
        return redact_url(value)
    return value


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """매핑의 각 항목을 :func:`redact_value` 로 가립니다 — 매핑에 대한 그것과 같습니다."""
    return redact_value(data)


def redact_payload(
    payload: Mapping[str, object],
) -> dict[str, str | list[str]]:
    """변경 폼(mutation form) 마스킹 — 호출자가 로그·직렬화 전에 부릅니다.

    이 패키지 자신은 부르지 않습니다.

    민감 키는 ``[REDACTED]``, 나머지는 :func:`redact_text`. 리스트 값은 원소별로
    가리고 길이를 유지합니다 — 길이가 의미를 갖는 것은 운임 재계산 폼이
    여섯 개의 ``List @Field`` 를 **인덱스로 맞물려** 보내기 때문입니다
    (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:582-584``
    의 ``postPriceReCalculation`` 이 ``psg_tp_dv_cd``/``psrm_cl_cd``/
    ``dcnt_knd_cd1``/``hidDscpNo``/``hidDcntKndCd``/``hidFmlyNo`` 여섯 개를
    ``@Field List<String>`` 으로 받고,
    ``network/NetworkService.java:9997-10043`` 이 승객 행 목록을 그 여섯으로
    쪼갭니다). 옛 인용 ``CertificationService.java:35-37`` 은 6.5.0 이고
    7.0.6 디컴파일에 없습니다.
    """
    redacted: dict[str, str | list[str]] = {}
    for key, value in payload.items():
        name = str(key)
        sensitive = is_sensitive_key(name)
        if isinstance(value, (list, tuple)):
            redacted[name] = [
                "[REDACTED]" if sensitive else redact_text(str(item))
                for item in value
            ]
        else:
            redacted[name] = (
                "[REDACTED]" if sensitive else redact_text(str(value))
            )
    return redacted
