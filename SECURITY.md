# 보안

## 신고 경로

보안 문제는 이 저장소의
[GitHub Security Advisories](https://github.com/yakisoba0728/korail-mobile-api/security/advisories/new)
로 비공개 신고해 주십시오("Security" 탭 → "Report a vulnerability"). 이 경로는 수정이
준비될 때까지 신고자와 관리자 사이에서만 열립니다. 취약점을 공개 이슈나 디스커션으로
올리면 안 됩니다.

자격증명, 쿠키, 토큰, PNR, 원본 응답, 운영 식별자는 공개 이슈·디스커션·로그·픽스처·커밋
어디에도 남기면 안 됩니다. 진단 출력을 공유하기 전에 그 값들을 지우거나 다른 값으로
바꿔야 합니다. 재현에 필요한 최소한의 정보만 담아 주십시오.

## 재현할 때의 제약

- 실제 상태 변경을 실행해서 재현하면 안 됩니다.
- 과금되는 카드를 쓰면 안 됩니다.
- 승인되지 않은 운영 서버 요청을 보내면 안 됩니다.
- 본인 계정만 써야 합니다. 실카드 결제는 패키지 소유자가 자기 계정과 자기 카드에 대해
  쓰라고 있는 기능이지, 신고를 조사하면서 무언가를 결제해도 된다는 뜻이 아닙니다.

## 상태 변경 표면

이 패키지는 기본이 읽기 전용이지만 읽기 전용만은 아닙니다. 명시적 동의 게이트 뒤에 상태를
바꾸는 메서드 13개가 있고, 각각 따로 옵트인해야 하는 범주 7개로 나뉩니다.

| 범주 | 메서드 |
| --- | --- |
| `reserve` | `reserve`, `reserve_transfer`, `reserve_merge`, `reserve_with_discount_card`, `confirm_standby_hold` |
| `cancel` | `cancel_unpaid_hold` |
| `payment` | `pay_with_fake_card`, `pay_with_card` |
| `refund` | `refund` |
| `cart` | `add_to_cart` |
| `discount_card` | `register_discount_card`, `extend_discount_card` |
| `price_recalculation` | `recalculate_price` |

각 메서드는 해당 범주로 옵트인한 `MutationConsent` 없이는 거부됩니다. 기본값
`dry_run=True` 에서는 마스킹된 미리보기만 돌려주고 아무것도 보내지 않습니다. 전송은
게이트가 걸린 두 경로로만 나갑니다 — POST 라우트 8개는 `post_mutation_form`, 앱이 `@GET`
으로 선언한 라우트 1개는 `get_mutation_query`. 체크인, 회원, 포인트·마일리지를 비롯한
나머지 모든 상태 변경 엔드포인트는 제외되어 있고 호출할 수 없습니다.

## 전송 직전 검사

두 전송 경로는 프로세스 밖으로 무언가 나가기 전에 같은 네 가지를 검사합니다.

1. 동의가 해당 범주로 옵트인했는가.
2. `(method, path)` 쌍이 등록된 상태 변경 라우트인가.
3. 호출자의 범주가 그 라우트를 **소유한** 범주인가 — 한 범주의 동의를 다른 범주의
   라우트로 돌려쓸 수 없습니다.
4. 나가는 폼이 평탄한 문자열→문자열(반복 키를 보내는 라우트 하나만 문자열→리스트)이고,
   여기의 모든 빌더가 쓰는 공통 필드 3개를 담고 있는가.

마지막 검사는 손으로 조립한 dict 만 만들 수 있는 값을 거릅니다. 자리수 없이 인코딩될
정수, `"True"` 로 인코딩될 불리언, `None`, 중첩된 매핑이 그것입니다.

## 결제 카드 게이트

결제 폼은 카드번호를 평문으로 싣습니다. 그래서 결제는 동의가 어떤 종류의 카드를
주장하는지 한 겹 더 검사합니다. `pay_with_fake_card` 는 `fake_card_only` 가 설정되어 있지
않으면 거부하므로 과금되지 않는 테스트 카드만 보낼 수 있습니다. 과금되는 실카드는 별도의
`pay_with_card` 로만 닿을 수 있고, `real_card_acknowledged=True` 와 `fake_card_only=False`
를 함께 명시한 동의여야 합니다. 두 플래그의 기본값은 안전한 쪽이므로 확인 표시를 하지 않은
동의로는 돈이 움직이지 않습니다. 전송 게이트는 둘 다 아니거나 둘 다인 동의도 독립적으로
거부합니다.
