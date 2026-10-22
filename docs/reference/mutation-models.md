# 예약·결제 모델

예약·결제·환불 메서드의 입력과 응답 모델입니다.

::: korail_mobile_api.RefundTicketResponse

::: korail_mobile_api.StationRefundOriginalTicket

::: korail_mobile_api.StationRefundVerificationRequest

::: korail_mobile_api.StationRefundVerificationResponse

::: korail_mobile_api.StationRefundExecutionRequest

::: korail_mobile_api.StationRefundExecutionResponse

::: korail_mobile_api.KorailPassengerCounts

::: korail_mobile_api.KorailSeatAssignment

::: korail_mobile_api.ReservationJourney

::: korail_mobile_api.ReservationHoldResponse

::: korail_mobile_api.HoldReference

::: korail_mobile_api.ReservationPaymentCoupon

::: korail_mobile_api.ReservationPaymentTicket

::: korail_mobile_api.ReservationPaymentSettlement

::: korail_mobile_api.ReservationPaymentTableSeat

::: korail_mobile_api.ReservationPaymentResponse

::: korail_mobile_api.CardPayment

`PaidTicket`은 현재 `sale_date`와 원표 `return_sale_date`를 구분합니다.
새 키워드 전용 필드는 `return_sale_date: str | None = None`, `companion_name: str = ""`,
`companion_certificate_no: str = ""`이며 세 필드는 `repr`에서 숨깁니다.
수동 생성 시 환불하려면 원표 반환일을 명시해야 합니다. `from_refund_detail()`은
`detail.original_sale_date`와 `detail.companion_name`·`detail.companion_birth_date`를 복사합니다.
환불에는 같은 원표·동반자의 실제 수수료 조회 성공 응답이 필요합니다. [환불 가이드](../guide/payments.md#commission)를 참고하세요.

::: korail_mobile_api.PaidTicket

::: korail_mobile_api.PriceRecalculationRow

::: korail_mobile_api.PriceRecalculationRequest

::: korail_mobile_api.CartDiscountAddition

::: korail_mobile_api.CartAddResponse

::: korail_mobile_api.ProductCancelResponse

::: korail_mobile_api.CartAddRequest

::: korail_mobile_api.SelfCheckInRegisterResponse

::: korail_mobile_api.SelfCheckInCancelResponse

::: korail_mobile_api.DeliveredTicketRetrievalResponse
