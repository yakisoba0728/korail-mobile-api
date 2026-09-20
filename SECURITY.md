# 보안

## 신고 경로

보안 문제는 이 저장소의
[GitHub Security Advisories](https://github.com/yakisoba0728/korail-mobile-api/security/advisories/new)
로 비공개 신고해 주시면 됩니다("Security" 탭 → "Report a vulnerability"). 수정이 준비될 때까지
신고자와 관리자 사이에서만 열립니다. 취약점을 공개 이슈나 디스커션으로 올리면 안 됩니다.

자격증명, 쿠키, 토큰, PNR, 원본 응답, 운영 식별자는 공개 이슈·디스커션·로그·픽스처·커밋
어디에도 남기면 안 됩니다. 진단 출력을 공유하기 전에 그 값들을 지우거나 다른 값으로
바꾸고, 재현에 필요한 최소한만 담아야 합니다.

## 재현할 때의 제약

- 실제 상태 변경을 실행해서 재현하면 안 됩니다.
- 과금되는 카드를 쓰면 안 됩니다.
- 승인되지 않은 운영 서버 요청을 보내면 안 됩니다.
- 본인 계정만 써야 합니다. 실카드 결제는 패키지 소유자가 자기 계정과 자기 카드에 대해
  쓰라고 있는 기능이지, 신고를 조사하면서 무언가를 결제해도 된다는 뜻이 아닙니다.

## 상태 변경 표면

이 패키지는 기본이 읽기 전용이지만 읽기 전용만은 아닙니다. 공개 클라이언트에는
상태를 바꾸는 메서드 14개가 있습니다. 동의 객체도 dry-run도 미리보기도 없습니다 —
로그인한 세션만 있으면 아래 메서드는 부르는 순간 실제 요청을 보냅니다.

| 범주 | 메서드 |
| --- | --- |
| `reserve` | `reserve`, `reserve_transfer`, `reserve_merge`, `reserve_with_discount_card`, `confirm_standby_hold` |
| `cancel` | `cancel_unpaid_hold` |
| `payment` | `pay_with_fake_card`, `pay_with_card` |
| `refund` | `refund`, `execute_station_ticket_refund` |
| `cart` | `add_to_cart` |
| `discount_card` | `register_discount_card`, `extend_discount_card` |
| `price_recalculation` | `recalculate_price` |

기존 13개 메서드는 로그인 세션을 요구하고(없으면 `KorailAuthError`), 전송은
`post_mutation_form` 하나로 나갑니다 — 9개 변경 라우트는 모두 POST이고, 6.5.0 때
`@GET`으로 선언됐던 `dcntCrdExtn.do`도 7.0.6부터 POST로 바뀌어 실제로 닿을 수 있는
GET 변경 라우트는 없습니다. 각 클라이언트 메서드가 호출하는 범주는 코드에 고정돼
있고, 호출자가 고를 수 있는 인자가 아닙니다.

`execute_station_ticket_refund`는 7.0.6 계약 게이트웨이 `V7Gateway`(`client.v7`)로
`NetworkApi.executeOnlineRefunds` 하나만 부릅니다. 이 레지스트리에 남은 계약은 그것과
조회용 `verifyOnlineRefunds` 둘뿐입니다 — 그 밖의 115개 계약(정기권/패스 구매 네
개를 포함)은 삭제됐습니다. 정기권/패스 구매 계약 네 개는 `V7Gateway.call()`이 무엇을
넘기든 이름으로 무조건 거부합니다(`KorailMutationNotAllowedError`).

## 전송 직전 검사

전송 경로는 프로세스 밖으로 무언가 나가기 전에 같은 세 가지를 검사합니다.

1. `(method, path)` 쌍이 등록된 상태 변경 라우트인가.
2. 호출자의 범주가 그 라우트를 **소유한** 범주인가 — 한 범주로 다른 범주의
   라우트를 부를 수 없습니다.
3. 나가는 폼이 평탄한 문자열→문자열(반복 키를 보내는 라우트 하나만 문자열→리스트)이고,
   여기의 모든 빌더가 쓰는 공통 필드 3개를 담고 있는가.

마지막 검사는 손으로 조립한 dict 만 만들 수 있는 값을 거릅니다. 자리수 없이 인코딩될
정수, `"True"` 로 인코딩될 불리언, `None`, 중첩된 매핑이 그것입니다. 이 세 검사는
호출자가 끌 수 없습니다 — 세 검사를 다 지나면 곧바로 나갑니다.

## 결제 카드는 메서드 이름으로만 갈립니다

결제 폼은 카드번호를 평문으로 싣습니다. `pay_with_fake_card` 와 `pay_with_card` 는
같은 `build_card_payment_form` 으로 폼을 만들고 같은 전송 경로로 나갑니다 — 카드가
테스트용인지 실제로 청구되는지를 검사하는 코드는 없습니다. 둘을 가르는 것은 호출자가
어느 이름의 메서드를 불렀는가, 그것 하나뿐입니다. 세션이 있는 상태에서
`pay_with_card(hold, card)` 를 부르면 그 카드로 곧바로 청구됩니다. **이 경계는
코드가 강제하는 게이트가 아니라 이름이 지키는 약속입니다** — 실카드를 실수로
청구하지 않는 것은 호출하는 쪽의 책임입니다.
