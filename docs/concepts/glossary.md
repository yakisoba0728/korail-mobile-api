# 용어

문서 전체에서 같은 뜻으로 쓰는 용어입니다.

| 용어 | 뜻 |
|---|---|
| 홀드 | 결제 전 예약입니다. 좌석을 점유하며, 결제 기한까지 결제하거나 취소해야 합니다. 예약 메서드가 반환하는 [`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse]가 홀드를 나타냅니다. |
| PNR | 예약 번호입니다. 홀드와 발권된 승차권을 가리킬 때 씁니다. 응답의 `pnr_no` 필드에 들어 있습니다. |
| 발권 | 결제가 끝나 승차권이 만들어진 상태입니다. 발권된 승차권은 취소가 아니라 환불로 처리합니다. |
| 일반 예약 | 좌석을 서버가 배정하는 예약입니다. `KorailReservationJobType.IMMEDIATE`입니다. |
| 좌석 지정 예약 | 호차와 좌석을 직접 골라 잡는 예약입니다. `KorailReservationJobType.SEAT_DESIGNATED`입니다. |
| 예약대기 | 매진된 열차에 빈자리가 생기면 배정받도록 신청하는 것입니다. 좌석을 확보한 것이 아니므로 바로 결제할 수 없습니다. `KorailReservationJobType.STANDBY`입니다. |
| 환승 예약 | 서로 다른 두 열차를 한 PNR로 예약하는 것입니다. |
| 병합 예약 | 입석으로 잡은 구간과 좌석이 있는 구간을 이어 붙여 예약하는 것입니다. `KorailReservationJobType.MERGE_STANDING`으로 첫 홀드를 만든 뒤 `reserve_merge`로 이어서 예약합니다. |
| 객실 등급 | 일반실과 특실입니다. [`KorailSeatClass`][korail_mobile_api.constants.KorailSeatClass]로 지정합니다. |
| 원표 | 여정 변경이나 환불의 기준이 되는 원래 승차권입니다. |
| 반환 식별자 | 발권된 승차권 한 장을 가리키는 값(판매 창구번호, 판매일, 일련번호, 반환 비밀번호)입니다. [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]와 [`PaidTicket`][korail_mobile_api.mutation_models.PaidTicket]이 이 값을 담습니다. |
| 대리수령 | 구매한 승차권을 다른 회원에게 전달해 그 회원이 받도록 하는 기능입니다. 응답과 모델 이름에는 `pbp`로 표시합니다. |
| 셀프 체크인 | 자유석 승객이 열차 좌석의 QR 코드를 스캔해 앉은 좌석을 등록하는 기능입니다. |
| N카드 | 선택한 구간을 정해진 횟수만큼 할인받는 할인카드입니다. 응답과 모델 이름에는 `discount_card`로 표시합니다. |
| 대기열 | 혼잡할 때 요청을 순서대로 받기 위한 NetFunnel 서버입니다. 열차 조회·예약·결제 전에 거칩니다. |
| 관문 | 대기열에서 작업 종류별로 나뉜 입구입니다(`inquiry`, `reserve`, `pay` 등). |
| DynaPath | 앱이 보호하는 경로에 붙이는 토큰 헤더입니다. |
| 봉투 | 모든 응답에 공통으로 들어 있는 상태 필드(`strResult`, `h_msg_cd`, `h_msg_txt`)입니다. |
| 결과 코드 | 봉투의 `h_msg_cd` 값입니다. 성공과 실패의 구체적인 사유를 나타냅니다. |
| 세션 만료 | 로그인 세션이 서버에서 끝난 상태입니다. 결과 코드 `P058`로 알려 오며 `KorailSessionExpiredError`가 발생합니다. |
| 원본(`raw`) | 서버가 보낸 응답을 가공하지 않은 값입니다. 응답 모델과 예외에 들어 있습니다. |
