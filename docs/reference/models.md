# 열차·공통 모델

열차 조회, 좌석, 역·달력 같은 공통 응답과 조회 입력입니다.

::: korail_mobile_api.KorailSession

::: korail_mobile_api.BaseKorailResponse

`from_raw()`는 바로 아래 키가 문자열인 `dict`의 봉투 세 필드만 옮기며 도메인 파싱·성공 판정을 하지 않습니다. 상속한 모델의 필수 도메인 인자가 더 필요하면 원문과 생성자 `TypeError` cause를 보존한 `KorailProtocolError`입니다. 전체 DTO는 해당 typed client 조회로 받으세요. 직접 생성자는 기존 필수 키워드 인자와 기본값을 유지합니다.

::: korail_mobile_api.AppVersionInfo

::: korail_mobile_api.AppDataResponse

::: korail_mobile_api.NoticeResponse

::: korail_mobile_api.UuidResponse

::: korail_mobile_api.MaasMenuItem

::: korail_mobile_api.MaasMenuListResponse

::: korail_mobile_api.KorailStation

::: korail_mobile_api.StationDataResponse

::: korail_mobile_api.StationInfoResponse

::: korail_mobile_api.TrainCalendarDay

::: korail_mobile_api.TrainCalendarResponse

::: korail_mobile_api.TrainScheduleStop

::: korail_mobile_api.TrainScheduleResponse

::: korail_mobile_api.TransferStation

::: korail_mobile_api.TransferStationListResponse

::: korail_mobile_api.TrainSearchQuery

::: korail_mobile_api.TrainSummary

::: korail_mobile_api.ReservationPassengerInfo

::: korail_mobile_api.SeatAttribute

::: korail_mobile_api.SeatCar

::: korail_mobile_api.SeatCarListResponse

::: korail_mobile_api.PhysicalSeat

::: korail_mobile_api.SeatWindow

::: korail_mobile_api.SeatInventoryResponse

::: korail_mobile_api.TrainSearchMetadata

::: korail_mobile_api.TrainSearchContinuation

::: korail_mobile_api.TrainSearchResult

::: korail_mobile_api.TransferItinerary

::: korail_mobile_api.TransferSearchResult
