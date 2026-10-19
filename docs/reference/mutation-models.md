# 예약·결제 모델

예약·결제·환불 메서드의 입력과 응답 모델입니다.

::: korail_mobile_api.mutation_models.RefundTicketResponse

::: korail_mobile_api.mutation_models.StationRefundOriginalTicket

::: korail_mobile_api.mutation_models.StationRefundVerificationRequest

::: korail_mobile_api.mutation_models.StationRefundVerificationResponse

::: korail_mobile_api.mutation_models.StationRefundExecutionRequest

::: korail_mobile_api.mutation_models.StationRefundExecutionResponse

::: korail_mobile_api.mutation_models.KorailPassengerCounts

::: korail_mobile_api.mutation_models.KorailSeatAssignment

::: korail_mobile_api.mutation_models.ReservationJourney

::: korail_mobile_api.mutation_models.ReservationHoldResponse

::: korail_mobile_api.mutation_models.ReservationPaymentCoupon

::: korail_mobile_api.mutation_models.ReservationPaymentTicket

::: korail_mobile_api.mutation_models.ReservationPaymentSettlement

::: korail_mobile_api.mutation_models.ReservationPaymentTableSeat

::: korail_mobile_api.mutation_models.ReservationPaymentResponse

::: korail_mobile_api.mutation_models.CardPayment

2.6.0부터 `PaidTicket`은 현재 `sale_date`와 원표 `return_sale_date`를 구분합니다.
새 키워드 전용 필드는 `return_sale_date: str | None = None`, `companion_name: str = ""`,
`companion_certificate_no: str = ""`이며 세 필드는 `repr`에서 숨깁니다.
수동 생성 시 환불하려면 원표 반환일을 명시해야 합니다. `from_refund_detail()`은
`detail.original_sale_date`와 `detail.companion_name`·`detail.companion_birth_date`를 복사합니다.
환불에는 같은 원표·동반자의 실제 수수료 조회 성공 응답이 필요합니다. [환불 가이드](../guide/payments.md#commission)를 참고하세요.

::: korail_mobile_api.mutation_models.PaidTicket

::: korail_mobile_api.mutation_models.DiscountCardSectionRequest

::: korail_mobile_api.mutation_models.DiscountCardAdditionalUser

::: korail_mobile_api.mutation_models.DiscountCardPurchaseRequest

::: korail_mobile_api.mutation_models.DiscountCardTicket

::: korail_mobile_api.mutation_models.DiscountCardPurchaseResponse

::: korail_mobile_api.mutation_models.PriceRecalculationRow

::: korail_mobile_api.mutation_models.PriceRecalculationRequest

::: korail_mobile_api.mutation_models.CartDiscountAddition

::: korail_mobile_api.mutation_models.CartAddResponse

::: korail_mobile_api.mutation_models.ProductCancelResponse

::: korail_mobile_api.mutation_models.CartAddRequest

::: korail_mobile_api.mutation_models.SelfCheckInRegisterResponse

::: korail_mobile_api.mutation_models.SelfCheckInCancelResponse

::: korail_mobile_api.mutation_models.DeliveredTicketRetrievalResponse
