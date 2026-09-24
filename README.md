> [!IMPORTANT]
> ## 🚆 The Journey Begins Again
>
> ### **여기서, 여정이 다시 시작됩니다.**
>
> 2026년 9월 1일, KORAIL과 SR의 통합과 함께 KTX와 SRT 역시 하나의 체계로 합쳐졌습니다.
> 두 갈래로 이어져 오던 서비스가 하나의 선로 위에서 만난 것처럼,
> **[`srt-mobile-api`](https://github.com/yakisoba0728/srt-mobile-api)의 개발과 기록도
> 이제 `korail-mobile-api`로 이어집니다.**
>
> `srt-mobile-api`는 여기서 멈췄지만, 그 안에서 확인한 수많은 요청과 응답,
> 시행착오와 검증의 기록까지 사라지는 것은 아닙니다.
> 그 경험은 이 프로젝트의 다음 장을 이루는 기반으로 남습니다.
>
> **우리는 SRT를 기억할 것입니다.**  
> 하나의 프로젝트는 종착역에 도착했지만, 그 여정은 이곳에서 다시 출발합니다.
>
> **One journey ended. Another begins here.**
>
> → [`srt-mobile-api` — Final Stop](https://github.com/yakisoba0728/srt-mobile-api)

## 직접 지원하지 않는 기능

### 부가서비스(MaaS) 구매·결제·환불

렌터카·카셰어링·짐배송·레저이용권·관광택시·주차 같은 부가서비스는 KORAIL 앱의 자체 기능이 아니라 제휴사 서비스입니다.

- **예약은 제휴사 사이트에서만 됩니다.** 앱 메뉴의 중계 페이지(`/ebizmaas/EbizMaasShopView.do`)가 요청번호를 발급하고, 암호화된 본인 정보를 제휴사 사이트(야놀자, 짐캐리, 로이쿠, SK·롯데 렌터카, 그린카, KN파킹)로 넘깁니다. 제휴사에서 상품을 고르면 그때 KORAIL 장바구니에 결제 전 항목이 생깁니다. KORAIL API로는 이 항목을 만들 수 없습니다.
- **결제와 환불은 폼 값을 알 수 없습니다.** 부가서비스 결제(`pay.intgStl.do`)와 환불(`addService.coptCnc.do`)에 들어가는 상수가 앱에서 보호돼 있습니다.

그래서 부가서비스는 조회만 지원합니다: `get_maas_menu_list`, `get_maas_station_data`, `get_maas_service_details`, `get_cart_list`.

앱 코드와 같게 만들어 두었지만 실서버에서 확인하지 못한 세 호출(환불 수수료 `maas.cncFee.do`, 결제 전 상태 확인 `maas.rsvStt.do`, 결제 전 해제 `addService.cancelPay.do`)은 공개 API에서 빼고 기록용으로 `src/korail_mobile_api/_maas_unsupported.py`에 남겨 두었습니다. 이 모듈은 어디에서도 쓰지 않습니다.

공항버스는 KORAIL 자체 예약이라 조회·예약·결제·환불·취소를 모두 지원합니다(`reserve_limousine`).
