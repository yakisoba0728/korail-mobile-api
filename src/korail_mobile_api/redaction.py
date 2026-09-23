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
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

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
        # 판정하므로(redact_value 의 데이터클래스 분기), 철자 하나가 빠지면 그
        # 경로만 원문이 남는다.
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
        # redact_value 는 데이터클래스를 ``field.name`` 으로 훑으므로(redact_value
        # 의 데이터클래스 분기) 폼 딕셔너리만 가려지고 객체 경로는 평문이었다.
        # ``card_number`` 는 CARD_RE 가 우연히 잡아 주지만 그것은 14~19자리
        # 숫자일 때뿐이라 기댈 수 없다.
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
        # 훑는 경로(redact_value 의 데이터클래스 분기)에서만 나타난다. 전부 이미 repr=False 인 필드들이다 —
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
#: 이 패턴 하나를 :func:`_index_stripped` 와 :data:`SENSITIVE_KEY_PREFIX_RE` 가
#: **함께** 씁니다. 나눠 적었을 때 실제로 갈라졌습니다: 키 판정은 인덱스 앞
#: 밑줄을 떼는데 텍스트 탐지는 안 떼서, ``is_sensitive_key("h_sgr_nm_1")`` 은
#: 참인데 ``redact_text("h_sgr_nm_1=...")`` 는 값을 그대로 남겼습니다 —
#: 즉 dict 는 가려지고 같은 값이 문자열·JSON·상대 URL 로 로그에 실리면
#: 평문이었습니다(2026-09-23 확인).
#: 밑줄 하나. 생 ``_`` 와 퍼센트 인코딩 ``%5F``, JSON escape ``\\u005f`` 를 모두
#: 받습니다. 키 본문(:func:`_percent_tolerant`)과 인덱스 접미사(바로 아래)가
#: **같은 정의를 씁니다** — 따로 적었을 때 접미사 쪽만 생 ``_`` 로 남아,
#: ``INFO {"h\\u005fsgr\\u005fnm\\u005f1": ...}`` 처럼 접미사 앞 밑줄까지
#: escape 된 키를 놓쳤습니다(2026-09-23, 전 레지스트리 시험에서 1,571건).
_UNDERSCORE = r"(?:_|%5[Ff]|\\u005[Ff])"
_HYPHEN = r"(?:-|%2[Dd]|\\u002[Dd])"

_INDEX_SUFFIX_PATTERN = (
    r"(?:" + _UNDERSCORE + r"?\d+" + _UNDERSCORE + r"?|" + _UNDERSCORE + r")"
)

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
#: scheme 을 생략한 ``//user@host`` 도 받습니다(줄 머리 또는 공백 뒤). :func:`redact_url` 과
#: 같은 모양을 보도록 맞췄습니다(C03).
URL_USERINFO_RE = re.compile(r"(?:(?<=://)|(?<=^//)|(?<=\s//))[^/?#\s]*@")

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
    """키의 ``_``/``-`` 를 ``%5F``·``%2D`` 와 JSON 의 ``\\u005f``·``\\u002d`` 로도 받습니다.

    JSON escape 를 **키 패턴에서만** 받는 이유: 로그 전체의 escape 를 먼저
    풀면 값 안의 escape 까지 바뀌어 누출과 값 변경이 같이 생겼습니다.
    """
    escaped = re.escape(key)
    underscore = _UNDERSCORE
    hyphen = _HYPHEN
    # ``re.escape`` 는 ``-`` 를 ``\-`` 로 바꿉니다. 밑줄은 그대로 둡니다.
    return escaped.replace("_", underscore).replace("\\-", hyphen)



#: 민감 키와 그 뒤의 ``=``/``:`` (그리고 서식 공백)까지만 봅니다. **값이 어디서
#: 끝나는지는 정규식이 정하지 않습니다** — :func:`_sensitive_value_end` 가 정합니다.
#: 예전에는 값까지 한 정규식으로 먹었는데, 정규식은 괄호의 짝을 셀 수 없어서
#: ``INFO {"txtPwd":{"a":{"b":1},"other":"<비밀>"}}`` 처럼 두 겹 이상 중첩된 값이
#: 안쪽 ``}`` 에서 끊겼고 뒤가 평문으로 남았습니다(외부 감사 C10).
SENSITIVE_KEY_PREFIX_RE = re.compile(
    r"(?<![\w-])(?P<key_quote>[\"']?)(?:"
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
    + r"?(?P=key_quote)(?![\w-])\s*(?:(?P<eq>=)|:)(?:[ \t]+)?",
    re.IGNORECASE,
)

#: ``&``/``;`` 뒤에 이것이 오면 그 구분자는 **다음 필드**의 시작입니다.
_NEXT_FIELD_KEY = r"[\w.%\[\]-]+="
_NEXT_FIELD_RE = re.compile(r"[&;]" + _NEXT_FIELD_KEY)
#: ``=`` 로 묶인 따옴표 없는 값의 끝: 공백, 또는 새 ``키=`` 앞의 ``&``/``;``.
#: **쉼표는 끝이 아닙니다.** 쉼표에서 끊었을 때 ``txtPwd=HEAD,<비밀>`` 의 쉼표
#: 뒤가 평문으로 남았습니다(외부 감사 C05). 애매하면 더 가리는 쪽입니다.
_EQ_VALUE_END_RE = re.compile(r"\s|[&;](?=" + _NEXT_FIELD_KEY + r")")
#: 괄호 값이 짝을 맞춰 닫힌 바로 뒤에 이 문자가 오면 값은 거기서 끝납니다.
#: 그 밖의 문자가 붙어 있으면(``txtPwd=[a]<비밀>``) 따옴표 없는 값처럼 이어 갑니다.
_AFTER_BRACKET_STOP = frozenset(",}])\"'")


def _quoted_end(text: str, start: int) -> tuple[int, bool]:
    """``text[start]`` 의 따옴표로 시작한 문자열의 끝(다음 위치)과 닫혔는지.

    escape 쌍은 **백슬래시 뒤의 아무 문자**입니다. 예전 정규식 ``\\\\.`` 는 ``.`` 가
    줄바꿈을 받지 않아, 백슬래시 바로 뒤에 실제 LF 가 온 값에서 escape 쌍이 끊기고
    둘째 줄이 평문으로 남았습니다(2026-09-23 최종 감사 C06).
    """
    quote = text[start]
    index = start + 1
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == quote:
            return index + 1, True
        index += 1
    return length, False


_CLOSER_OF = {"{": "}", "[": "]"}


def _balanced_end(text: str, start: int, memo: dict[int, int | None]) -> int | None:
    """``text[start]`` 의 ``{``/``[`` 와 **짝이 맞는** 닫는 괄호의 다음 위치.

    깊이와 무관합니다. 따옴표 친 문자열 안의 괄호는 세지 않습니다 — 예전 한 겹
    패턴은 문자열 안의 ``]`` 에서도 멈췄습니다(``INFO {"txtPwd":["]","<비밀>"]}``).
    재귀가 아니라 명시적 스택입니다. 짝이 안 맞거나 닫히지 않으면 ``None``.

    ``memo`` 는 한 텍스트 안에서 이미 판정한 여는 괄호의 결과입니다. 스캔이 지나간
    여는 괄호마다 짝(또는 짝 없음)을 적어 두고, 다음 스캔은 그것을 건너뜁니다.
    이것이 없으면 ``txtPwd=[ `` 를 10만 번 되풀이한 한 줄이 스캔마다 끝까지 가서
    제곱 시간이 걸렸습니다.
    """
    if start in memo:
        return memo[start]
    openers: list[int] = []
    index = start
    length = len(text)
    while index < length:
        char = text[index]
        if char in "\"'":
            index, closed = _quoted_end(text, index)
            if not closed:
                break
            continue
        if char in "{[":
            if index != start and index in memo:
                known = memo[index]
                if known is None:
                    break
                index = known
                continue
            openers.append(index)
        elif char in "}]":
            top = openers.pop()
            if char != _CLOSER_OF[text[top]]:
                memo[top] = None
                break
            memo[top] = index + 1
            if not openers:
                return index + 1
        index += 1
    for position in openers:
        memo[position] = None
    return None


def _unquoted_end(text: str, start: int, eq: bool) -> int:
    """따옴표 없는 값(``text[start]`` 는 공백이 아님)의 끝.

    공백 없는 **최대 길이**입니다. ``=`` 로 묶였으면 ``&``/``;`` 가 새 ``키=`` 앞에
    올 때만 끝납니다 — 그래야 ``txtSeatNo1_=X&trnNo1=Y`` 의 이웃은 살고
    ``txtPwd=HEAD&<비밀>`` 의 꼬리는 함께 가려집니다. ``:`` 로 묶이면(헤더·산문)
    쿠키 헤더의 ``;``·``=`` 도 값의 일부입니다.
    """
    end_re = _EQ_VALUE_END_RE if eq else _WHITESPACE_RE
    match = end_re.search(text, start + 1)
    return match.start() if match else len(text)


def _sensitive_value_end(
    text: str, start: int, eq: bool, memo: dict[int, int | None]
) -> int:
    """민감 키 바로 뒤 ``start`` 에서 시작하는 값의 끝. 값이 없으면 ``start``.

    * 따옴표 값: 짝 따옴표까지(escape 쌍 포함). 닫히지 않으면 끝까지.
    * ``{``/``[`` 로 시작: **짝이 맞는** 닫는 괄호까지(깊이 무관). 짝이 안
      맞으면 공백까지. 외부 감사 C10 이전에는 한 겹만 봐서 안쪽에서 끊겼습니다.
    * 그 밖: :func:`_unquoted_end`.

    ``=`` 로 묶인 값이 그 자체로 ``&키=``·``;키=`` 로 시작하면 값이 아니라 **다음
    필드**입니다(``h_sgr_nm_1=&trnNo1=Y``). 그냥 ``txtPwd=&<비밀>`` 이면
    ``&<비밀>`` 이 값입니다 — 무조건 막았더니 그 꼬리가 평문으로 남았습니다.

    ``=`` 뒤에 서식 공백이 있으면 공백 뒤의 토큰을 값으로 봅니다(한계 L4). 자유
    텍스트에서 ``txtPwd= <base64>`` 와 ``h_sgr_nm_1= trnNo1=X`` 는 구분되지 않고,
    이 함수는 **애매하면 더 가리는 쪽**입니다.
    """
    length = len(text)
    if start >= length or _WHITESPACE_RE.match(text, start):
        return start
    if eq and _NEXT_FIELD_RE.match(text, start):
        return start
    char = text[start]
    if char in "\"'":
        return _quoted_end(text, start)[0]
    if char in "{[":
        end = _balanced_end(text, start, memo)
        if end is None:
            match = _WHITESPACE_RE.search(text, start)
            return match.start() if match else length
        if (
            end >= length
            or text[end] in _AFTER_BRACKET_STOP
            or _WHITESPACE_RE.match(text, end)
            or (eq and _NEXT_FIELD_RE.match(text, end))
        ):
            return end
        return _unquoted_end(text, end, eq)
    return _unquoted_end(text, start, eq)


def _redacted_value_token(value: str, key_quote: str) -> str:
    """가린 값의 자리에 넣을 글자. 따옴표 값은 같은 따옴표로 둡니다.

    따옴표 없는 값(숫자·괄호 값)인데 **키가 따옴표로 싸여 있으면** 그 따옴표로
    감쌉니다. 산문에 박힌 JSON 에서 ``"txtPwd":{...}`` 가 ``"txtPwd":[REDACTED]``
    가 되면 그 조각이 더 이상 JSON 이 아니었습니다.
    """
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        wrap = value[0]
    else:
        wrap = key_quote
    return f"{wrap}[REDACTED]{wrap}"


def _redact_sensitive_values(text: str) -> str:
    """자유 텍스트의 ``민감키=값``·``민감키: 값``·``"민감키":값`` 을 가립니다."""
    out: list[str] = []
    emitted = 0
    search_at = 0
    memo: dict[int, int | None] = {}
    while True:
        match = SENSITIVE_KEY_PREFIX_RE.search(text, search_at)
        if match is None:
            break
        start = match.end()
        end = _sensitive_value_end(
            text, start, match.group("eq") is not None, memo
        )
        if end == start:
            search_at = match.start() + 1
            continue
        out.append(text[emitted:start])
        out.append(_redacted_value_token(text[start:end], match.group("key_quote")))
        emitted = search_at = end
    out.append(text[emitted:])
    return "".join(out)


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


class _JsonSyntaxError(ValueError):
    """:func:`_load_json_iteratively` 가 JSON 이 아니라고 판정했습니다."""


_JSON_WHITESPACE_RE = re.compile(r"[ \t\n\r]*")
#: 표준 :mod:`json` 의 숫자 문법 그대로입니다. ``\d`` 가 아니라 ``[0-9]`` 인 것은
#: ``\d`` 가 유니코드 숫자까지 받기 때문입니다.
_JSON_NUMBER_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?")
_JSON_LITERALS: tuple[tuple[str, object], ...] = (
    ("true", True),
    ("false", False),
    ("null", None),
    # 표준 json.loads 가 받는 비표준 상수. 원문 그대로 다시 씁니다.
    ("NaN", _RawNumber("NaN")),
    ("Infinity", _RawNumber("Infinity")),
    ("-Infinity", _RawNumber("-Infinity")),
)


def _skip_json_whitespace(text: str, index: int) -> int:
    match = _JSON_WHITESPACE_RE.match(text, index)
    assert match is not None  # ``*`` 라 언제나 맞습니다.
    return match.end()


def _read_json_key(text: str, index: int) -> tuple[str, int]:
    """``"키"`` 와 ``:`` 를 읽고, 값이 시작하는 위치를 돌려줍니다."""
    if not text.startswith('"', index):
        raise _JsonSyntaxError(index)
    key, index = json.decoder.scanstring(text, index + 1, True)
    index = _skip_json_whitespace(text, index)
    if not text.startswith(":", index):
        raise _JsonSyntaxError(index)
    return key, _skip_json_whitespace(text, index + 1)


def _read_json_scalar(text: str, index: int) -> tuple[object, int]:
    match = _JSON_NUMBER_RE.match(text, index)
    if match is not None:
        return _RawNumber(match.group()), match.end()
    for literal, value in _JSON_LITERALS:
        if text.startswith(literal, index):
            return value, index + len(literal)
    raise _JsonSyntaxError(index)


def _load_json_iteratively(text: str) -> object:
    """``json.loads(text, object_pairs_hook=_Pairs, parse_*=_RawNumber)`` 와 같은
    트리를 **깊이 제한 없이** 만듭니다.

    표준 ``json.loads`` 는 깊이 1만 겹짜리 문법상 유효한 JSON 을
    ``RecursionError`` 로 거절합니다. 예전에는 그러면 자유 텍스트 경로로 넘어가
    안쪽 괄호에서 값이 끊겨 비밀이 남았고, 치환 결과에 따옴표 없는
    ``[REDACTED]`` 가 들어가 출력이 JSON 이 아니었습니다(외부 감사 C10, 옛 한계
    L6). 이 파서는 명시적 스택이라 깊이가 문제 되지 않습니다. 문자열은 표준
    :func:`json.decoder.scanstring` (strict) 이 읽으므로 escape·제어 문자 규칙이
    ``json.loads`` 와 같습니다.
    """
    length = len(text)
    # 각 틀: [컨테이너(_Pairs 또는 list), 값을 기다리는 키]
    stack: list[list[Any]] = []
    index = _skip_json_whitespace(text, 0)
    while True:
        # --- 값 하나를 읽습니다.
        if index >= length:
            raise _JsonSyntaxError(index)
        char = text[index]
        value: object
        if char == "{":
            index = _skip_json_whitespace(text, index + 1)
            if text.startswith("}", index):
                value, index = _Pairs([]), index + 1
            else:
                key, index = _read_json_key(text, index)
                stack.append([_Pairs([]), key])
                continue
        elif char == "[":
            index = _skip_json_whitespace(text, index + 1)
            if text.startswith("]", index):
                value, index = [], index + 1
            else:
                stack.append([[], None])
                continue
        elif char == '"':
            value, index = json.decoder.scanstring(text, index + 1, True)
        else:
            value, index = _read_json_scalar(text, index)
        # --- 다 읽은 값을 부모에 붙입니다. 부모가 닫히면 부모가 다시 값이 됩니다.
        while True:
            if not stack:
                if _skip_json_whitespace(text, index) != length:
                    raise _JsonSyntaxError(index)
                return value
            frame = stack[-1]
            container = frame[0]
            if isinstance(container, list):
                container.append(value)
                closer = "]"
            else:
                container.items.append((frame[1], value))
                closer = "}"
            index = _skip_json_whitespace(text, index)
            if text.startswith(",", index):
                index = _skip_json_whitespace(text, index + 1)
                if closer == "}":
                    frame[1], index = _read_json_key(text, index)
                break
            if text.startswith(closer, index):
                index += 1
                stack.pop()
                value = container
                continue
            raise _JsonSyntaxError(index)


def _parse_json_document(value: str) -> object:
    """문자열 전체가 JSON 이면 손실 없는 표현으로, 아니면 ``_NO_JSON``.

    구조로 다뤄야 정규식이 못 보는 두 모양을 받습니다 — escape 된 키
    (``{"h\\u005fsgr\\u005fnm_1": ...}`` 는 파싱해야 민감 키로 보입니다)와
    중첩 배열·객체(키의 민감성이 값 **트리 전체**에 걸립니다).
    """
    # ``strip()`` 은 BOM(``﻿``)을 떼지 않습니다. 파일·스트림 앞머리에
    # 붙어 오는 흔한 문자이고, 그것 하나 때문에 첫 문자 검사가 빗나가
    # 구조 경로에 못 들어갔습니다(2026-09-23 확인).
    stripped = value.strip().lstrip("﻿").strip()
    # 맨 숫자도 JSON 문서입니다. 예전에는 ``{``·``[``·``"`` 로 시작할 때만 봐서
    # ``"4111111111111111"`` 이 텍스트 경로로 가 따옴표 없는 ``[REDACTED_CARD]``
    # 가 나왔고, JSON 숫자 입력에 대한 출력이 JSON 이 아니었습니다(최종 감사
    # C04). 아무 것도 가리지 않는 숫자는 위 규칙대로 원문이 그대로 나갑니다.
    if not stripped or stripped[0] not in '{["-0123456789':
        return _NO_JSON
    try:
        return _load_json_iteratively(stripped)
    except (ValueError, TypeError, RecursionError):
        return _NO_JSON


def _mask_key_text(name: str) -> str:
    """키·host 처럼 **구조 안의 이름**에 G5 를 적용합니다 — 카드번호 모양과
    ``JSESSIONID=`` 값.

    이름 전체에 :func:`redact_text` 를 걸지는 않습니다. 이름이 JSON 처럼 보이면
    구조 경로로 다시 읽혀 따옴표 붙은 결과가 나옵니다. 예전에는 카드번호만 봐서
    ``{"JSESSIONID=<비밀>": ...}`` 의 키와 ``https://JSESSIONID=<비밀>.host/`` 의
    host 가 그대로 남았습니다(외부 감사 C03).
    """
    return SESSION_RE.sub(r"\1[REDACTED]", CARD_RE.sub("[REDACTED_CARD]", name))


def _mask_key(name: str, used: set[str], reserved: set[str]) -> str:
    """키를 가리되 **같은 객체 안에서 서로 다르게** 둡니다.

    키도 문자열이므로 G5(모든 문자열의 카드번호 모양)의 대상입니다. 한때 키를
    아예 건드리지 않았는데, 카드번호가 키로 실리면 그대로 남았습니다. 그렇다고
    한 문자열로 바꾸면 서로 다른 두 키가 같아져 항목이 합쳐집니다. 그래서 겹치면
    ``#2``·``#3`` 을 붙입니다.

    ``reserved`` 는 그 객체의 **원래 키 전부**입니다. 이미 쓴 이름(``used``)만
    피했을 때, 원래부터 ``[REDACTED_CARD]`` 라는 키가 **뒤에** 있으면 가린 키와
    같아져 mapping 에서는 앞 값이 사라지고 JSON 에서는 없던 중복 키가
    생겼습니다(외부 감사 C06).
    """
    masked = _mask_key_text(name)
    if masked == name:
        used.add(name)
        return name
    candidate, number = masked, 1
    while candidate in used or candidate in reserved:
        number += 1
        candidate = f"{masked}#{number}"
    used.add(candidate)
    return candidate


#: JSON 숫자 리터럴 안의 카드번호 모양(14~19자리 숫자열). 부호·소수·지수가
#: 붙어도 봅니다. 예전에는 :data:`CARD_RE` 를 리터럴 **전체**에 ``fullmatch`` 해서
#: ``-4111…`` 과 ``4111….5`` 가 그대로 남았습니다(외부 감사 C04). G5 가 G3 의
#: "숫자 리터럴은 그대로" 보다 우선합니다. 카드번호 모양이 없는 숫자는 한 글자도
#: 바꾸지 않습니다(``1e0`` 은 ``1e0``).
_NUMBER_CARD_RE = re.compile(r"(?<![0-9])[0-9]{14,19}(?![0-9])")


def _redact_and_dump_json(root: object) -> tuple[str, bool]:
    """파싱된 JSON 트리를 가리면서 **한 번에** 다시 씁니다.

    재귀가 아니라 명시적 스택입니다. 재귀로 짰을 때 깊이 500짜리 1KB 문서가
    ``RecursionError`` 로 죽었습니다 — 표준 ``json`` 은 C 구현이라 같은 입력을
    처리하는데 파이썬 재귀는 한도(기본 1000)에 훨씬 빨리 닿습니다. **길이가
    아니라 깊이가 문제**라서, 100만 자짜리 얕은 문서는 재귀로도 멀쩡했습니다
    (2026-09-23 확인).
    """
    parts: list[str] = []
    changed = False
    # (노드, 키) 또는 리터럴 문자열
    stack: list[object] = [(root, None)]
    while stack:
        entry = stack.pop()
        if isinstance(entry, str):
            parts.append(entry)
            continue
        node, key = entry  # type: ignore[misc]
        if key is not None and is_sensitive_key(key):
            parts.append(json.dumps("[REDACTED]"))
            changed = True
            continue
        if isinstance(node, _Pairs):
            parts.append("{")
            pushed: list[object] = []
            used_keys: set[str] = set()
            reserved_keys = {name for name, _ in node.items}
            for index, (name, item) in enumerate(node.items):
                if index:
                    pushed.append(", ")
                shown = _mask_key(name, used_keys, reserved_keys)
                changed = changed or shown != name
                pushed.append(f"{json.dumps(shown)}: ")
                # 민감성은 **원래** 키로 판정합니다.
                pushed.append((item, name))
            pushed.append("}")
            stack.extend(reversed(pushed))
            continue
        if isinstance(node, list):
            parts.append("[")
            pushed = []
            for index, item in enumerate(node):
                if index:
                    pushed.append(", ")
                pushed.append((item, None))
            pushed.append("]")
            stack.extend(reversed(pushed))
            continue
        if isinstance(node, _RawNumber):
            # 카드번호 모양은 키와 무관하게 값 자체로 잡습니다. 예전에는 다 쓴
            # JSON 문자열에 :data:`CARD_RE` 를 덧칠했는데, 그러면 치환 문자열에
            # 따옴표가 없어 **출력이 JSON 이 아니게** 되고 숫자 키까지 같은
            # 문자열로 바뀌어 서로 다른 항목이 합쳐졌습니다(2026-09-23 확인).
            # 그래서 리터럴을 통째로 JSON **문자열** 로 바꿉니다.
            if _NUMBER_CARD_RE.search(node.text):
                parts.append(json.dumps("[REDACTED_CARD]"))
                changed = True
            else:
                parts.append(node.text)
            continue
        if isinstance(node, str):
            inner = redact_text(node)
            changed = changed or inner != node
            parts.append(json.dumps(inner))
            continue
        if node is True:
            parts.append("true")
        elif node is False:
            parts.append("false")
        elif node is None:
            parts.append("null")
        else:
            parts.append(json.dumps(node))
    return "".join(parts), changed


def redact_text(value: str) -> str:
    """문자열에서 카드번호·세션·민감 키값을 가립니다.

    **알려진 한계 — 따옴표 없는 값 안의 공백.** ``h_sgr_nm_1=홍 길동`` 처럼
    인용하지 않은 값에 공백이 있으면 공백까지만 가려지고 뒤가 남습니다.
    공백을 값의 일부로 보려면 ``h_sgr_nm=X 이후 문장 전체``를 먹어야 해서,
    로그 한 줄이 통째로 사라집니다. 평문에서 그 둘은 구분할 수 없습니다.

    그래서 이 함수는 **따옴표 없는 값에 공백이 없다고 가정합니다.** 공백이 아닌
    구분자(쉼표 등)는 값을 끝내지 않습니다 — 공백 없는 한 덩어리 전체가 값입니다.
    ``{``/``[`` 로 시작하는 값은 짝이 맞는 닫는 괄호까지 깊이와 무관하게 가립니다.
    실제로 공백이 들어가는 값은 구조화된 입구로 넘기십시오 — ``redact_mapping``·
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
        # JSON 문자열 안에 JSON 이 든 경우(이중 직렬화)도 여기서 같이 됩니다 —
        # 루트가 문자열이면 순회가 그 값을 :func:`redact_text` 에 넣습니다.
        # 한때 이 앞에 따로 "이중 직렬화" 분기를 두고, 바뀐 게 없으면 ``None``
        # 을 돌려 아래 순회가 **같은 작업을 다시** 하게 했습니다. 포장 수마다
        # 두 배씩 늘어 12겹에 8,191번을 불렀습니다(2026-09-23 확인). 이제
        # 겹마다 한 번입니다.
        dumped, changed = _redact_and_dump_json(parsed)
        # 가린 게 없으면 **원문을 그대로** 돌려줍니다. 다시 직렬화한 결과를
        # 돌려주면 서식만 바뀌는 게 아니었습니다: 문자열 값 ``"[1,2]"`` 가 안쪽에서
        # JSON 으로 다시 읽혀 ``"[1, 2]"`` 로 **값 자체가** 바뀌었습니다(최종
        # 감사 C05). 원문을 돌려주면 그 값은 한 글자도 안 바뀝니다.
        if not changed:
            return value
        if escaped:
            dumped = dumped.replace('"', '\\"')
        # 구조 처리로 끝내지 않습니다. 카드번호 모양과 세션 토큰은 키와
        # 무관하게 값 자체로 잡는 것이라, 여기서 빠뜨리면 JSON 으로 실린
        # 카드번호만 예외가 됩니다 — 실제로 ``{"debug": 4111…}`` 가
        # 그대로 남았습니다(2026-09-23 확인).
        return dumped
    # 여기까지 왔다는 것은 문자열 전체가 하나의 JSON 문서가 아니라는 뜻입니다
    # (``INFO {...}`` 처럼 앞에 산문이 붙었거나, 문서가 둘 이상이거나). 그 안의
    # ``_`` 로 escape 된 키는 :func:`_percent_tolerant` 가 **키 패턴 쪽에서**
    # 읽습니다.
    #
    # 한때 여기서 ASCII ``\uXXXX`` 를 문자열 전체에 걸쳐 먼저 풀었는데, 값까지
    # 바꿔 버렸습니다(2026-09-23 확인): 비밀번호 값 안의 ``"`` 가 ``"`` 로
    # 바뀌어 **값이 거기서 끝난 것으로 읽혀 뒷부분이 남았고**, 공개 문자열의
    # 리터럴 ``a`` 여섯 글자가 ``a`` 로 바뀌었습니다. 아직 파싱하지 않은
    # 로그 전체에서는 어느 escape 가 JSON 문자열 안에 있는지 알 수 없으므로,
    # 값은 건드리지 않습니다.
    redacted = value
    redacted = URL_USERINFO_RE.sub("[REDACTED]@", redacted)
    redacted = CARD_RE.sub("[REDACTED_CARD]", redacted)
    redacted = _redact_sensitive_values(redacted)
    return SESSION_RE.sub(r"\1[REDACTED]", redacted)


def redact_url(value: str) -> str:
    """URL 을 가립니다. 쿼리는 키 단위로, 경로와 fragment 는 :func:`redact_text` 로.

    경로도 봐야 하는 이유: 서블릿은 쿠키가 없으면 세션을 ``;jsessionid=...`` 로
    경로에 붙이고, fragment 에는 ``key=value`` 가 그대로 실릴 수 있습니다.
    폴백 규칙: scheme/netloc 이 없으면 보통 :func:`redact_text` 로 갑니다.
    **예외가 하나 있습니다** — 경로가 ``/`` 로 시작하고 쿼리에 공백이 없으면
    상대 URL 로 보고 쿼리를 키 단위로 처리합니다. 그렇게 하지 않으면 퍼센트
    인코딩된 키가 절대 URL 로는 가려지고 상대 URL 로는 남았습니다.

    쿼리 **키**와 host 도 가립니다(카드번호 모양·``JSESSIONID=`` 값, G5).
    """
    # 어떤 입력에도 예외를 내지 않습니다(G6). ``urlsplit`` 은 닫히지 않은 IPv6
    # 괄호에서 ``ValueError`` 를, ``urlencode`` 는 짝 없는 surrogate 에서
    # ``UnicodeEncodeError`` 를 냅니다 — 후자는 최종 감사 C08 에서 드러났습니다.
    # 구조로 못 다루면 :func:`_redact_url_fallback` 으로 갑니다.
    try:
        return _redact_url_structured(value)
    except (ValueError, UnicodeError):
        return _redact_url_fallback(value)


def _decoded_query_key(key: str) -> str:
    """쿼리 키의 ``+``·퍼센트 escape 를 풉니다 — ``urllib.parse.parse_qsl`` 과 같은 규칙."""
    return unquote(key.replace("+", " "), errors="replace")


def _redact_url_fallback(value: str) -> str:
    """구조 경로가 실패한 URL. 쿼리의 민감 키는 **디코딩한 키로** 판정합니다.

    예전에는 곧장 :func:`redact_text` 로 넘겼는데, 텍스트 경로는 ``_``/``-`` 외의
    문자가 퍼센트 인코딩된 키를 못 읽습니다. 그래서 짝 없는 surrogate 하나 때문에
    구조 경로가 실패하면, 구조 경로라면 가렸을 ``?%74xtPwd=<비밀>`` 의 값이
    그대로 나갔습니다(외부 감사 C09). 나머지(경로·fragment·카드번호·세션)는
    :func:`redact_text` 가 봅니다. 구분자는 ``&`` 와 ``;`` 를 모두 봅니다 —
    애매하면 더 가리는 쪽입니다.
    """
    head, question, rest = value.partition("?")
    if not question:
        return redact_text(value)
    query, hash_mark, fragment = rest.partition("#")
    pieces = re.split(r"([&;])", query)
    for position in range(0, len(pieces), 2):
        name, equals, _item = pieces[position].partition("=")
        if equals and is_sensitive_key(_decoded_query_key(name)):
            pieces[position] = f"{name}=[REDACTED]"
    return redact_text(f"{head}?{''.join(pieces)}{hash_mark}{fragment}")


def _redact_url_structured(value: str) -> str:
    parsed = urlsplit(value)
    # ``/`` 로 시작하는 **문장**이 쿼리로 해석돼 공백이 ``+`` 로 바뀌지 않도록,
    # 진짜 URL 에는 인코딩되지 않은 공백이 없다는 점으로 가릅니다.
    relative_with_query = (
        not parsed.scheme
        and not parsed.netloc
        and parsed.query
        and parsed.path.startswith("/")
        and not _WHITESPACE_RE.search(parsed.query)
    )
    # ``//user@host/p`` 같은 scheme 생략 URL 도 netloc 이 있으므로 구조로 봅니다.
    # 예전에는 scheme 이 없다는 이유로 텍스트 경로에 보냈고, 텍스트 경로의
    # userinfo 패턴은 ``://`` 뒤만 보므로 자격증명이 그대로 남았습니다(C03).
    scheme_relative = (
        not parsed.scheme
        and parsed.netloc
        and not _WHITESPACE_RE.search(value)
    )
    if not (parsed.scheme and parsed.netloc) and not (
        relative_with_query or scheme_relative
    ):
        return redact_text(value)
    # 쿼리 **키**도 문자열입니다(G5). 예전에는 키를 그대로 둬서
    # ``?4111…=public`` 의 숫자가 남았습니다(외부 감사 C02).
    query = [
        (
            _mask_key_text(key),
            "[REDACTED]" if is_sensitive_key(key) else redact_text(item),
        )
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    netloc = parsed.netloc
    userinfo, _, host = netloc.rpartition("@")
    # host 도 봅니다. 카드번호 모양과 세션 토큰은 어디에 있든 가립니다(G5) —
    # 예전에는 host 를 손대지 않아 ``https://4111….example/`` 의 숫자가
    # 남았고(C07), 카드만 봐서 ``https://JSESSIONID=<비밀>.example/`` 이
    # 남았습니다(외부 감사 C03).
    host = _mask_key_text(host)
    netloc = f"[REDACTED]@{host}" if userinfo else host
    return urlunsplit(
        (
            parsed.scheme,
            netloc,
            redact_text(parsed.path),
            urlencode(query),
            redact_text(parsed.fragment),
        )
    )


#: :func:`redact_value` 스택에서 "이 컨테이너를 다 봤다"는 표식.
_LEAVE = object()


def redact_value(value: Any, *, key: str | None = None) -> Any:
    """임의의 값을 가립니다.

    매핑→키마다, 리스트/튜플→원소마다(컨테이너 타입 유지), 데이터클래스→필드별
    dict, 문자열→:func:`redact_url`. 나머지 타입은 그대로. 매핑의 문자열 키도
    가립니다(카드번호 모양·``JSESSIONID=`` 값).

    **재귀가 아니라 명시적 스택입니다.** 재귀로 짰을 때 민감 키를 일반 dict
    1,500겹으로 감싼 입력이 ``RecursionError`` 로 죽었습니다(최종 감사 C02).
    구조화 입구는 깊이와 무관하게 가려야 합니다(G1).

    컨테이너가 **자기 조상 안에서** 다시 나오면(순환 참조) ``"[CYCLE]"`` 로
    둡니다 — 재귀판은 그런 입력에서 ``RecursionError`` 를 냈고, 반복판은 막지
    않으면 멈추지 않습니다. 판정은 **현재 경로**(조상 스택)로 합니다. 예전에는
    한 번이라도 본 객체를 전부 기억해서, 순환하지 않는 공유 객체
    (``{"left": d, "right": d}``)의 두 번째 자리가 ``[CYCLE]`` 로 바뀌어 내용이
    사라졌습니다(외부 감사 C07). 이제 공유 객체는 나올 때마다 다 가려서 씁니다.
    """
    result: list[Any] = [None]
    tuples: list[tuple[list[Any], Any, Any]] = []
    on_path: set[int] = set()
    stack: list[tuple[Any, Any, Any, Any]] = [(value, key, result, 0)]
    while stack:
        item, item_key, parent, slot = stack.pop()
        if item_key is _LEAVE:
            on_path.discard(item)
            continue
        if item_key is not None and is_sensitive_key(item_key):
            parent[slot] = "[REDACTED]"
            continue
        is_mapping = isinstance(item, Mapping)
        is_sequence = isinstance(item, (list, tuple))
        is_record = is_dataclass(item) and not isinstance(item, type)
        if is_mapping or is_sequence or is_record:
            if id(item) in on_path:
                parent[slot] = "[CYCLE]"
                continue
            on_path.add(id(item))
            # 자식보다 **먼저** 쌓으므로 자식을 다 본 뒤에 꺼내집니다.
            stack.append((id(item), _LEAVE, None, None))
        if is_mapping:
            mapping_out: dict[Any, Any] = {}
            parent[slot] = mapping_out
            used_keys: set[str] = set()
            reserved_keys = {name for name in item.keys() if isinstance(name, str)}
            for child_key, child in item.items():
                shown = (
                    _mask_key(child_key, used_keys, reserved_keys)
                    if isinstance(child_key, str)
                    else child_key
                )
                mapping_out[shown] = None
                # 민감성은 **원래** 키로 판정합니다.
                stack.append((child, str(child_key), mapping_out, shown))
        elif is_sequence:
            sequence_out: list[Any] = [None] * len(item)
            parent[slot] = sequence_out
            if isinstance(item, tuple):
                tuples.append((sequence_out, parent, slot))
            for index, child in enumerate(item):
                stack.append((child, None, sequence_out, index))
        elif is_record:
            record_out: dict[str, Any] = {}
            parent[slot] = record_out
            for record_field in fields(item):
                record_out[record_field.name] = None
                stack.append(
                    (
                        getattr(item, record_field.name),
                        record_field.name,
                        record_out,
                        record_field.name,
                    )
                )
        elif isinstance(item, str):
            parent[slot] = redact_url(item)
        else:
            parent[slot] = item
    # 튜플은 다 채운 뒤 바꿉니다. 안쪽이 나중에 쌓였으므로 뒤에서부터 바꿔야
    # 바깥 튜플이 이미 바뀐 안쪽 튜플을 담습니다.
    for sequence_out, parent, slot in reversed(tuples):
        parent[slot] = tuple(sequence_out)
    return result[0]


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """매핑의 각 항목을 :func:`redact_value` 로 가립니다 — 매핑에 대한 그것과 같습니다."""
    return redact_value(data)


def redact_payload(
    payload: Mapping[str, object],
) -> dict[str, str | list[str]]:
    """변경 폼(mutation form) 마스킹 — 호출자가 로그·직렬화 전에 부릅니다.

    이 패키지 자신은 부르지 않습니다.

    민감 키는 ``[REDACTED]``, 나머지는 :func:`redact_text`. 키도 가립니다
    (카드번호 모양·``JSESSIONID=`` 값, 겹치면 ``#2``). 리스트 값은 원소별로
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
    # 매핑이 아닌 입력에도 예외를 내지 않습니다(G6). 예전에는 ``.items()`` 를
    # 바로 불러 문자열 하나에 ``AttributeError`` 가 났습니다(최종 감사 C09).
    if not isinstance(payload, Mapping):
        return redact_value(payload)  # type: ignore[no-any-return]
    redacted: dict[str, str | list[str]] = {}
    used_keys: set[str] = set()
    reserved_keys = {str(key) for key in payload}
    for key, value in payload.items():
        # 민감성은 **원래** 키로 판정합니다. 예전에는 키를 그대로 내보내서
        # ``{"4111…": ...}`` 의 카드번호가 남았습니다(외부 감사 C01).
        original = str(key)
        sensitive = is_sensitive_key(original)
        name = _mask_key(original, used_keys, reserved_keys)
        if isinstance(value, (list, tuple)):
            redacted[name] = [
                "[REDACTED]" if sensitive else _redact_form_value(item)
                for item in value
            ]
        else:
            redacted[name] = (
                "[REDACTED]" if sensitive else _redact_form_value(value)
            )
    return redacted


def _repr_iterative(root: object) -> str:
    """:func:`redact_value` 의 결과를 ``str()`` 과 **같은 글자로**, 재귀 없이 씁니다.

    ``str()`` 은 중첩 dict 를 재귀로 씁니다. 가리는 쪽을 반복으로 바꾼 뒤에도
    마지막 ``str()`` 이 남아, 1만 겹 폼 값이 가린 **뒤에** ``RecursionError`` 로
    죽었습니다(외부 감사 C08). :func:`redact_value` 의 결과는 dict·list·tuple 과
    그 밖의 잎뿐이므로 그 셋만 풀어 쓰면 됩니다. 잎은 ``repr()`` 입니다.
    """
    parts: list[str] = []
    # (리터럴인가, 글자 또는 노드)
    stack: list[tuple[bool, Any]] = [(False, root)]
    while stack:
        is_literal, node = stack.pop()
        if is_literal:
            parts.append(node)
            continue
        kind = type(node)
        if kind is dict:
            parts.append("{")
            pushed: list[tuple[bool, Any]] = []
            for index, (name, child) in enumerate(node.items()):
                if index:
                    pushed.append((True, ", "))
                pushed.append((True, f"{name!r}: "))
                pushed.append((False, child))
            pushed.append((True, "}"))
            stack.extend(reversed(pushed))
        elif kind is list or kind is tuple:
            opener, closer = ("[", "]") if kind is list else ("(", ")")
            if kind is tuple and len(node) == 1:
                closer = ",)"
            parts.append(opener)
            pushed = []
            for index, child in enumerate(node):
                if index:
                    pushed.append((True, ", "))
                pushed.append((False, child))
            pushed.append((True, closer))
            stack.extend(reversed(pushed))
        else:
            parts.append(repr(node))
    return "".join(parts)


def _redact_form_value(value: object) -> str:
    """폼 값 하나를 문자열로. 중첩 구조는 **구조로** 가린 뒤 문자열로 만듭니다.

    예전에는 무엇이든 ``str()`` 로 먼저 바꿔 텍스트 정규식에 넣었습니다. 그러면
    ``{"outer": {"txtPwd": [["a", "<비밀>"]]}}`` 의 안쪽 민감 키가 Python repr
    속 텍스트로만 남아, 중첩 배열에서 뒤 원소가 평문으로 남았습니다(최종 감사
    C01). 구조화 입력은 깊이·타입과 무관하게 가려야 합니다(G1).
    """
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, (Mapping, list, tuple)) or (
        is_dataclass(value) and not isinstance(value, type)
    ):
        return _repr_iterative(redact_value(value))
    return redact_text(str(value))
