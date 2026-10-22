# 용어

문서 전체에서 같은 뜻으로 쓰는 용어입니다. 괄호 안은 같은 뜻으로 쓰지 않는 표현입니다.

| 용어 | 뜻 |
|---|---|
| 홀드 | 결제 전 예약입니다(임시 예약, 미결제 예약이라고 쓰지 않습니다). 좌석을 점유하며, 결제 기한까지 결제하거나 취소해야 합니다. 예약 메서드가 반환하는 [`ReservationHoldResponse`][korail_mobile_api.ReservationHoldResponse]가 홀드를 나타냅니다. 기존 예약은 [`get_reservation_hold`](../api/reservations.md#get_reservation_hold)로 같은 모델에 담아 가져올 수 있습니다. |
| 예약번호(PNR) | 홀드와 발권된 승차권을 가리키는 번호입니다. 응답의 `pnr_no` 필드에 들어 있습니다. |
| 승차권 | 결제가 끝나 발권된 표입니다(표라고만 쓰지 않습니다). 승차권 목록은 [`list_tickets`](../api/account.md#list_tickets)로 조회합니다. |
| 발권 | 결제가 끝나 승차권이 만들어진 상태입니다. 발권된 승차권은 취소가 아니라 환불로 처리합니다. |
| 일반 예약 | 좌석을 서버가 배정하는 예약입니다. `KorailReservationJobType.IMMEDIATE`입니다. |
| 좌석 지정 예약 | 호차와 좌석을 직접 골라 잡는 예약입니다. `KorailReservationJobType.SEAT_DESIGNATED`입니다. |
| 예약대기 | 매진된 열차에 빈자리가 생기면 배정받도록 신청하는 것입니다. 좌석을 확보한 것이 아니므로 바로 결제할 수 없습니다. `KorailReservationJobType.STANDBY`입니다. |
| 환승 예약 | 서로 다른 두 열차를 한 예약번호로 예약하는 것입니다. |
| 병합 예약 | 입석으로 잡은 구간과 좌석이 있는 구간을 이어 붙여 예약하는 것입니다. `KorailReservationJobType.MERGE_STANDING`으로 첫 홀드를 만든 뒤 `reserve_merge`로 이어서 예약합니다. |
| 객실 등급 | 일반실과 특실입니다. [`KorailSeatClass`][korail_mobile_api.KorailSeatClass]로 지정합니다. |
| 원표 | 여정 변경이나 환불의 기준이 되는 원래 승차권입니다. |
| 반환 식별자 | 발권된 승차권 한 장을 가리키는 값(판매 창구번호, 판매일, 일련번호, 반환 비밀번호)입니다. [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference]와 [`PaidTicket`][korail_mobile_api.PaidTicket]이 이 값을 담습니다. |
| 전달 | 구매한 승차권을 다른 회원에게 보내는 것입니다. 라이브러리는 전달을 지원하지 않습니다. |
| 대리수령 | 전달한 승차권을 다른 회원이 받아 쓰는 것입니다. 라이브러리는 이미 전달한 승차권의 수령자·내역 조회와 회수([`recall_delivered_ticket`](../api/delivery-checkin.md#recall_delivered_ticket))만 제공하며, 전달 자체는 하지 않습니다. 응답 필드 이름에는 `pbp`로, 메서드와 모델 이름에는 `delivery`·`delivered` 또는 `pbp`로 표시합니다. |
| 셀프 체크인 | 자유석 승객이 열차 좌석의 QR 코드를 스캔해 앉은 좌석을 등록하는 기능입니다. |
| N카드 | 선택한 구간을 정해진 횟수만큼 할인받는 할인카드입니다. 응답과 모델 이름에는 `discount_card`로 표시합니다. |
| 대기열 | 혼잡할 때 요청을 순서대로 받기 위한 NetFunnel 서버입니다. 열차 조회, 일부 예약(`reserve`, `reserve_transfer`, `reserve_with_discount_card`), 카드 결제, 예약 내역 조회 전에 거칩니다. |
| 관문 | 대기열에서 작업 종류별로 나뉜 입구입니다(`inquiry`, `reserve`, `pay` 등). |
| DynaPath | 앱이 보호하는 경로에 붙이는 토큰 헤더입니다. |
| 봉투 | 대부분의 응답에 공통으로 들어 있는 상태 필드(`strResult`, `h_msg_cd`, `h_msg_txt`)입니다. 역 목록처럼 봉투가 없을 수 있는 응답도 있습니다. |
| 결과 코드 | 봉투의 `h_msg_cd` 값입니다. 성공과 실패의 구체적인 사유를 나타냅니다. |
| 세션 만료 | 로그인 세션이 서버에서 끝난 상태입니다. 결과 코드 `P058`로 알려 오며 `KorailSessionExpiredError`가 발생합니다. |
| 원문(`raw`) | 서버가 보낸 응답을 가공하지 않은 값입니다(원본이라고 쓰지 않습니다). 응답 모델과 예외에 들어 있으며 개인정보를 가리지 않습니다. |
| 미확인 | 앱 근거가 없어 값이나 동작을 확정하지 못한 것입니다. 보호된 앱 값처럼 확인할 자료가 없는 경우에 씁니다. |
| 실서버 미검증 | 구현과 오프라인 테스트는 있지만 실제 KORAIL 서버에 보내 확인한 기록이 없는 것입니다. 오프라인 테스트 통과는 실서버 검증이 아닙니다. |
