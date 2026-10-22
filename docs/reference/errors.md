# 예외

라이브러리가 발생시키는 예외입니다. 모두 `KorailApiError`를 상속합니다.

`display_message`, 메시지 사전 조회와 계정 잠금·요청 제한·처리 중·기처리 예외는 2.5.0부터 제공합니다.

::: korail_mobile_api.KorailApiError

::: korail_mobile_api.KorailTransportError

::: korail_mobile_api.KorailProtocolError

::: korail_mobile_api.KorailAuthError

::: korail_mobile_api.KorailSessionExpiredError

::: korail_mobile_api.KorailAccountLockedError

::: korail_mobile_api.KorailDynaPathError

::: korail_mobile_api.KorailAuthContinuationRequired

::: korail_mobile_api.KorailAppError

::: korail_mobile_api.KorailNoResultsError

::: korail_mobile_api.KorailNoDirectTrainError

::: korail_mobile_api.KorailSoldOutError

::: korail_mobile_api.KorailSeatUnavailableError

::: korail_mobile_api.KorailReservationRefusedError

::: korail_mobile_api.KorailInvalidRequestError

::: korail_mobile_api.KorailNotEntitledError

::: korail_mobile_api.KorailServiceUnavailableError

::: korail_mobile_api.KorailRateLimitError

::: korail_mobile_api.KorailProcessingError

::: korail_mobile_api.KorailAlreadyProcessedError

::: korail_mobile_api.KorailAppUpdateRequiredError

::: korail_mobile_api.KorailNetFunnelError

::: korail_mobile_api.KorailQueueRejectedError

::: korail_mobile_api.KorailDynaPathRequiredError

## 메시지 조회

::: korail_mobile_api.get_error_message

::: korail_mobile_api.resolve_error_message
