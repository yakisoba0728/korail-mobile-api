# Local Database Model Field Catalog

Generated ORMLite field rows: **63**.

## `CreditCard`

- Source: `com/korail/talk/database/model/CreditCard.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `businessNum` | `String` | `@DatabaseField` | 9 |
| `cardNickname` | `String` | `@DatabaseField` | 12 |
| `cardNumber` | `String` | `@DatabaseField` | 15 |
| `cardType` | `String` | `@DatabaseField` | 18 |
| `cardValidateMonth` | `String` | `@DatabaseField` | 21 |
| `cardValidateYear` | `String` | `@DatabaseField` | 24 |
| `id` | `int` | `@DatabaseField(generatedId = true)` | 27 |

## `DoNotLookAgain`

- Source: `com/korail/talk/database/model/DoNotLookAgain.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `confirmDate` | `String` | `@DatabaseField` | 9 |
| `custMgNo` | `String` | `@DatabaseField(id = true, uniqueCombo = true)` | 12 |
| `doNotLookAgainType` | `int` | `@DatabaseField(uniqueCombo = true)` | 15 |

## `FavoriteStation`

- Source: `com/korail/talk/database/model/FavoriteStation.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `arrivalStation` | `String` | `@DatabaseField` | 9 |
| `arrivalStationCode` | `String` | `@DatabaseField` | 12 |
| `id` | `int` | `@DatabaseField(generatedId = true)` | 15 |
| `startStation` | `String` | `@DatabaseField` | 18 |
| `startStationCode` | `String` | `@DatabaseField` | 21 |

## `IssueList`

- Source: `com/korail/talk/database/model/IssueList.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `id` | `int` | `@DatabaseField(generatedId = true)` | 9 |
| `issueList` | `String` | `@DatabaseField` | 12 |

## `MainPopupData`

- Source: `com/korail/talk/database/model/MainPopupData.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `CHECK_TYPE_HIDDEN` | `int` | `` | 7 |
| `CHECK_TYPE_SHOW` | `int` | `` | 8 |
| `buttonType` | `String` | `@DatabaseField` | 11 |
| `checkType` | `int` | `@DatabaseField` | 14 |
| `clsBtn` | `String` | `@DatabaseField` | 17 |
| `confirmDate` | `String` | `@DatabaseField` | 20 |
| `id` | `int` | `@DatabaseField(generatedId = true)` | 23 |
| `imageUrl` | `String` | `@DatabaseField` | 26 |
| `isExternalBrowser` | `String` | `@DatabaseField` | 29 |
| `isShow` | `String` | `@DatabaseField` | 32 |
| `linkTitle` | `String` | `@DatabaseField` | 35 |
| `linkUrl` | `String` | `@DatabaseField` | 38 |
| `message` | `String` | `@DatabaseField` | 41 |
| `noticeId` | `int` | `@DatabaseField` | 44 |
| `size` | `String` | `@DatabaseField` | 47 |
| `title` | `String` | `@DatabaseField` | 50 |
| `voice` | `String` | `@DatabaseField` | 53 |

## `SMSData`

- Source: `com/korail/talk/database/model/SMSData.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `phoneNumber` | `String` | `@DatabaseField` | 10 |
| `pnrNo` | `String` | `@DatabaseField(id = true)` | 13 |

## `StationData`

- Source: `com/korail/talk/database/model/StationData.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `doNotLookADay` | `String` | `@DatabaseField` | 9 |
| `doNotLookAgain` | `boolean` | `@DatabaseField` | 12 |
| `group` | `String` | `@DatabaseField` | 15 |
| `id` | `int` | `@DatabaseField(id = true)` | 18 |
| `latitude` | `String` | `@DatabaseField` | 21 |
| `longitude` | `String` | `@DatabaseField` | 24 |
| `major` | `String` | `@DatabaseField` | 27 |
| `popupLinkTitle` | `String` | `@DatabaseField` | 30 |
| `popupLinkUrl` | `String` | `@DatabaseField` | 33 |
| `popupMessage` | `String` | `@DatabaseField` | 36 |
| `popupType` | `int` | `@DatabaseField` | 39 |
| `stnCd` | `String` | `@DatabaseField` | 42 |
| `stnNm` | `String` | `@DatabaseField` | 45 |

## `TicketDetail`

- Source: `com/korail/talk/database/model/TicketDetail.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `id` | `int` | `@DatabaseField(generatedId = true)` | 9 |
| `pnrNo` | `String` | `@DatabaseField` | 12 |
| `ticketDetail` | `String` | `@DatabaseField` | 15 |

## `ZRecentStation`

- Source: `com/korail/talk/database/model/ZRecentStation.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `arrivalStation` | `String` | `@DatabaseField` | 9 |
| `arrivalStationCode` | `String` | `@DatabaseField` | 12 |
| `id` | `int` | `@DatabaseField(generatedId = true)` | 15 |
| `startStation` | `String` | `@DatabaseField` | 18 |
| `startStationCode` | `String` | `@DatabaseField` | 21 |
| `timestamp` | `long` | `@DatabaseField` | 24 |

## `CreditCard`

- Source: `com/korail/talk/database/model/old/CreditCard.java`

| Field | Type | Annotation | Line |
|---|---|---|---:|
| `cardNickname` | `String` | `@DatabaseField` | 9 |
| `cardNumber` | `String` | `@DatabaseField` | 12 |
| `cardValidateMonth` | `String` | `@DatabaseField` | 15 |
| `cardValidateYear` | `String` | `@DatabaseField` | 18 |
| `id` | `int` | `@DatabaseField(generatedId = true)` | 21 |


# SharedPreferences Literal Key Inventory

Generated literal key rows: **645**. Constant-based keys require source lookup in referenced constants.

`Context` 열은 **그 줄에서 이 키를 어떻게 쓰는지**만 적는다 — 쓰기인지 읽기인지, 어느
접근자(`putString`/`getInt`/`containsKey` …)를 쓰는지. 원래는 앱 소스 줄을 그대로
옮겨 놓았으나, 디컴파일된 타사 소스 문장은 이 저장소가 재배포할 것이 아니다. 키 이름과
`file:line` 과 접근 종류가 이 표가 실제로 증명하는 전부이고, 원문이 필요하면 같은 APK를
디컴파일해 그 줄을 열면 된다.

| Key | Source | Line | Context |
|---|---|---:|---|
| `DISCOUNT_MENU_NO` | `com/korail/talk/view/base/BaseViewActivity.java` | 258 | 쓰기 `putString` |
| `DISCOUNT_MENU_NO` | `com/korail/talk/view/base/BaseViewActivity.java` | 269 | 쓰기 `putString` |
| `USE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 82 | 쓰기 `putInt` |
| `USE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 131 | 읽기 `getInt` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 143 | 쓰기 `putString` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 144 | 쓰기 `putString` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 145 | 쓰기 `putString` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 146 | 쓰기 `putString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 147 | 쓰기 `putString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 148 | 쓰기 `putString` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 149 | 쓰기 `putString` |
| `INPUT_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 167 | 쓰기 `putInt` |
| `ENABLE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 168 | 쓰기 `putInt` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 176 | 쓰기 `putString` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 177 | 쓰기 `putString` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 178 | 쓰기 `putString` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 179 | 쓰기 `putString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 180 | 쓰기 `putString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 181 | 쓰기 `putString` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 182 | 쓰기 `putString` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 188 | 읽기 `getString` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 189 | 읽기 `getString` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 190 | 읽기 `getString` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 191 | 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 192 | 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 193 | 읽기 `getString` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 194 | 읽기 `getString` |
| `USE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 218 | 읽기 `getInt` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/CityPointView.java` | 103 | 쓰기 `putString` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/CityPointView.java` | 104 | 쓰기 `putString` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/CityPointView.java` | 105 | 쓰기 `putString` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/CityPointView.java` | 106 | 쓰기 `putString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/CityPointView.java` | 107 | 쓰기 `putString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/CityPointView.java` | 108 | 쓰기 `putString` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/CityPointView.java` | 120 | 쓰기 `putString` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/CityPointView.java` | 121 | 쓰기 `putString` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/CityPointView.java` | 122 | 쓰기 `putString` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/CityPointView.java` | 123 | 쓰기 `putString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/CityPointView.java` | 124 | 쓰기 `putString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/CityPointView.java` | 125 | 쓰기 `putString` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/CityPointView.java` | 131 | 읽기 `getString` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/CityPointView.java` | 132 | 읽기 `getString` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/CityPointView.java` | 133 | 읽기 `getString` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/CityPointView.java` | 134 | 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/CityPointView.java` | 135 | 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/CityPointView.java` | 136 | 읽기 `getString` |
| `USE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 69 | 쓰기 `putInt` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 97 | 쓰기 `putString` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 98 | 쓰기 `putString` |
| `USE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 103 | 읽기 `getInt` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 127 | 쓰기 `putString` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 136 | 쓰기 `putString` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 137 | 쓰기 `putString` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 145 | 쓰기 `putString` |
| `INPUT_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 146 | 쓰기 `putInt` |
| `ENABLE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 147 | 쓰기 `putInt` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 153 | 읽기 `getString` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 154 | 읽기 `getString` |
| `USE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 178 | 읽기 `getInt` |
| `USE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 74 | 쓰기 `putInt` |
| `USE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 101 | 읽기 `getInt` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/LPointView.java` | 133 | 쓰기 `putString` |
| `INPUT_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 148 | 쓰기 `putInt` |
| `ENABLE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 149 | 쓰기 `putInt` |
| `USE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 170 | 읽기 `getInt` |
| `CARD_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 111 | 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 116 | 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 117 | 읽기 `getString` |
| `CARD_TYPE` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 122 | 읽기 `getString` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 125 | 읽기 `getString` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 277 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 277 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 279 | 쓰기 `putString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 280 | 쓰기 `putString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 281 | 쓰기 `putString` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 282 | 쓰기 `putString` |
| `IS_NOMAL_CARD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 283 | 쓰기 `putBoolean` |
| `AUTH_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 284 | 쓰기 `putString` |
| `INSTALLMENT_PERIOD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 285 | 쓰기 `putInt` |
| `CARD_NO_1` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | 읽기 `getString` |
| `CARD_NO_2` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | 읽기 `getString` |
| `CARD_NO_3` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | 읽기 `getString` |
| `CARD_NO_4` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | 읽기 `getString` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 331 | 쓰기 `putString` |
| `IS_NOMAL_CARD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 332 | 쓰기 `putBoolean` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 337 | 읽기 `getString` |
| `CARD_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 454 | 읽기 `getString` |
| `loginType` | `com/korail/talk/ui/scheme/DataActivity.java` | 31 | 쓰기 `put` |
| `loginId` | `com/korail/talk/ui/scheme/DataActivity.java` | 32 | `jSONObject.put("loginId", (z10 \|\| z9) ? a.decryptAES(getApplicationContext(), string2) : "");` |
| `loginPw` | `com/korail/talk/ui/scheme/DataActivity.java` | 33 | 쓰기 `put` |
| `isAutoLogin` | `com/korail/talk/ui/scheme/DataActivity.java` | 34 | 쓰기 `put` |
| `isSaveMemberNumber` | `com/korail/talk/ui/scheme/DataActivity.java` | 35 | 쓰기 `put` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/limousine/RenewalLimousineActivity.java` | 332 | 읽기 `getInt` |
| `dptRsStnCd` | `com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java` | 376 | 읽기 `getString` |
| `psrmClCd` | `com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java` | 378 | 읽기 `getString` |
| `seatAttCd` | `com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java` | 379 | 읽기 `getString` |
| `dptRsStnCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 120 | 읽기 `getString` |
| `arvRsStnNm` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 122 | 읽기 `getString` |
| `tmGpCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 123 | 읽기 `getString` |
| `psrmClCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 124 | 읽기 `getString` |
| `seatAttCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 127 | 읽기 `getString` |
| `rsvSaleDvCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 128 | 읽기 `getString` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 283 | 읽기 `getInt` |
| `dptRsStnCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 314 | 쓰기 `putString` |
| `arvRsStnNm` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 316 | 쓰기 `putString` |
| `tmGpCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 317 | 쓰기 `putString` |
| `psrmClCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 318 | 쓰기 `putString` |
| `seatAttCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 321 | 쓰기 `putString` |
| `rsvSaleDvCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 322 | 쓰기 `putString` |
| `TRAIN_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 127 | 읽기 `getString` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 128 | 읽기 `getString` |
| `STATION_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 129 | 읽기 `getString` |
| `STATION_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 195 | 읽기 `getString` |
| `TRAIN_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 298 | 쓰기 `putString` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 299 | 쓰기 `putString` |
| `STATION_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 300 | 쓰기 `putString` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 132 | 읽기 `get` |
| `DEPARTURE_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 179 | 읽기 `get` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 180 | 읽기 `get` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 333 | 쓰기 `put` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 341 | 읽기 `get` |
| `DEPARTURE_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 411 | 쓰기 `put` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 412 | 쓰기 `put` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 413 | 쓰기 `put` |
| `DEPARTURE_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 443 | 쓰기 `put` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 444 | 쓰기 `put` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 445 | 쓰기 `put` |
| `NOTICE_MESSAGE` | `com/korail/talk/ui/intro/IntroActivity.java` | 770 | 쓰기 `put` |
| `NOTICE_POST_DATA` | `com/korail/talk/ui/intro/IntroActivity.java` | 771 | 쓰기 `put` |
| `callback` | `com/korail/talk/ui/web/BaseWebViewActivity.java` | 982 | 삭제 `remove` |
| `Device` | `com/korail/talk/ui/reservation/BixbyReservationActivity.java` | 29 | 쓰기 `put` |
| `Version` | `com/korail/talk/ui/reservation/BixbyReservationActivity.java` | 30 | 쓰기 `put` |
| `Key` | `com/korail/talk/ui/reservation/BixbyReservationActivity.java` | 31 | 쓰기 `put` |
| `tss_srcar_no` | `com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java` | 268 | 읽기 `get` |
| `tss_seat_no` | `com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java` | 269 | 읽기 `get` |
| `messageId` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 148 | 읽기 `getString` |
| `message` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 171 | 읽기 `getString` |
| `noticeDate` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 221 | 읽기 `getLong` |
| `noticeDate` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 239 | 읽기 `getLong` |
| `message` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 247 | 읽기 `getString` |
| `messageId` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 249 | 읽기 `getString` |
| `ADULT_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 549 | 쓰기 `putInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 550 | 쓰기 `putInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 551 | 쓰기 `putInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 552 | 쓰기 `putInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 553 | 쓰기 `putInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 554 | 쓰기 `putInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 555 | 쓰기 `putInt` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 556 | 쓰기 `putInt` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 557 | 쓰기 `putInt` |
| `noticeDate` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 566 | 쓰기 `putLong` |
| `messageId` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 567 | 쓰기 `putString` |
| `message` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 568 | 쓰기 `putString` |
| `msg_vo` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 569 | 쓰기 `putString` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 191 | 읽기 `getString` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 192 | 읽기 `getInt` |
| `TICKET_TRAIN_INFO` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 193 | 읽기 `getString` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 194 | 읽기 `getString` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 200 | 읽기 `getBoolean` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 202 | 읽기 `getBoolean` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 205 | 읽기 `getBoolean` |
| `TICKET_PAYMENT_FLG` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 214 | 읽기 `getString` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 327 | 쓰기 `putString` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 329 | 쓰기 `putBoolean` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 330 | 쓰기 `putBoolean` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 331 | 쓰기 `putBoolean` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 334 | 쓰기 `putString` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 337 | 쓰기 `putBoolean` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 338 | 쓰기 `putBoolean` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 339 | 쓰기 `putBoolean` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 342 | 쓰기 `putBoolean` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 343 | 쓰기 `putBoolean` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 344 | 쓰기 `putBoolean` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 347 | 쓰기 `putBoolean` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 348 | 쓰기 `putBoolean` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 349 | 쓰기 `putBoolean` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 369 | 쓰기 `putString` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 371 | 쓰기 `putBoolean` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 372 | 쓰기 `putBoolean` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 373 | 쓰기 `putBoolean` |
| `TICKET_PAYMENT_FLG` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 374 | 쓰기 `putString` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 435 | 읽기 `getBoolean` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 436 | 읽기 `getInt` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 469 | 쓰기 `putString` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 470 | 쓰기 `putInt` |
| `TICKET_TRAIN_INFO` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 472 | 쓰기 `putString` |
| `DISCOUNT_SUM` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 105 | 읽기 `getInt` |
| `EXPIRED_DATE` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 106 | 읽기 `getString` |
| `COUPON_NO` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 108 | 읽기 `getString` |
| `COUPON_NO` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 185 | 쓰기 `putString` |
| `DISCOUNT_SUM` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 187 | 쓰기 `putInt` |
| `EXPIRED_DATE` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 188 | 쓰기 `putString` |
| `ADULT_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `ADULT_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 읽기 `getInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 같은 줄의 조건식에서 사용 (접근 종류는 해당 `file:line` 에서 확인) |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 같은 줄의 조건식에서 사용 (접근 종류는 해당 `file:line` 에서 확인) |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 같은 줄의 조건식에서 사용 (접근 종류는 해당 `file:line` 에서 확인) |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 같은 줄의 조건식에서 사용 (접근 종류는 해당 `file:line` 에서 확인) |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | 같은 줄의 조건식에서 사용 (접근 종류는 해당 `file:line` 에서 확인) |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 223 | 읽기 `getBoolean` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 224 | 읽기 `getString` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 225 | 읽기 `getInt` |
| `TRAIN_NAME` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 226 | 읽기 `getString` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 227 | 읽기 `getString` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 228 | 읽기 `getInt` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 229 | 읽기 `getInt` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 240 | 읽기 `getBoolean` |
| `IS_LIMOUSINE_TICKET` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 241 | 읽기 `getBoolean` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 248 | 읽기 `getString` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 250 | 읽기 `getInt` |
| `TRAIN_NAME` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 252 | 읽기 `getString` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 259 | 읽기 `getString` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 271 | 읽기 `getString` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 276 | 읽기 `getString` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 287 | 쓰기 `putBoolean` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 301 | 읽기 `getString` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 307 | 읽기 `getBoolean` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 307 | 읽기 `getString` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 395 | 읽기 `getString` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 396 | 읽기 `getString` |
| `HID_RSV_CHG_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 397 | 읽기 `getString` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 398 | 읽기 `getInt` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 399 | 읽기 `getInt` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 399 | 읽기 `getInt` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 400 | 읽기 `getBoolean` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 408 | 읽기 `getBoolean` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 412 | 읽기 `getString` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 415 | 읽기 `getString` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 420 | 읽기 `getString` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 421 | 읽기 `getInt` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 422 | 읽기 `getInt` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 422 | 읽기 `getInt` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 462 | 읽기 `getString` |
| `custMgNo` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 463 | 읽기 `getString` |
| `ADD_SRV_DV_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 506 | 읽기 `getString` |
| `COPT_ENT_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 507 | 읽기 `getString` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 508 | 읽기 `getString` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 509 | 읽기 `getString` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 520 | 읽기 `getBoolean` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 522 | 읽기 `getString` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 522 | 읽기 `getString` |
| `ADD_SRV_DV_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 523 | 읽기 `getString` |
| `COPT_ENT_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 524 | 읽기 `getString` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 525 | 읽기 `getString` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 526 | 읽기 `getString` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 547 | 읽기 `getBoolean` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 560 | 읽기 `getBoolean` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 561 | 읽기 `getString` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 572 | 쓰기 `putBoolean` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 574 | 쓰기 `putBoolean` |
| `JRNY_TP_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 576 | 쓰기 `putString` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 581 | 쓰기 `putString` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 582 | 쓰기 `putString` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 584 | 쓰기 `putString` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 585 | 쓰기 `putInt` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 587 | 쓰기 `putString` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 588 | 쓰기 `putInt` |
| `h_vr_rsv_no` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 591 | 쓰기 `putString` |
| `h_rcvd_amt` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 592 | 쓰기 `putString` |
| `custMgNo` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 593 | 쓰기 `putString` |
| `TRAIN_NAME` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 594 | 쓰기 `putString` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 595 | 쓰기 `putString` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 596 | 쓰기 `putString` |
| `ADD_SRV_DV_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 597 | 쓰기 `putString` |
| `COPT_ENT_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 598 | 쓰기 `putString` |
| `IS_LIMOUSINE_TICKET` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 599 | 쓰기 `putBoolean` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 601 | 쓰기 `putString` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 605 | 읽기 `getString` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 637 | 쓰기 `putInt` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 638 | 쓰기 `putInt` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 640 | 쓰기 `putBoolean` |
| `HID_RSV_CHG_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 641 | 쓰기 `putString` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 643 | 쓰기 `putInt` |
| `h_rcvd_amt` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 643 | 읽기 `getString` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 644 | 쓰기 `putInt` |
| `h_rcvd_amt` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 644 | 읽기 `getString` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 645 | 쓰기 `putBoolean` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 650 | 읽기 `getString` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 684 | 쓰기 `putBoolean` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 725 | 읽기 `getBoolean` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 827 | 읽기 `getBoolean` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 829 | 읽기 `getInt` |
| `hidSaleWctNo1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | 읽기 `get` |
| `hidSaleDt1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | 읽기 `get` |
| `hidSaleSqno1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | 읽기 `get` |
| `hidtkRetPwd1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | 읽기 `get` |
| `chgePbpRsvNo` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 156 | 쓰기 `put` |
| `txtPsgDisc0019Sqno_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 117 | 쓰기 `put` |
| `txtJobDvCd0019_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 118 | 쓰기 `put` |
| `txtPsgDisc0019PsDvCd_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 119 | 쓰기 `put` |
| `txtPsgDisc0019CustNm_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 120 | 쓰기 `put` |
| `txtPsgDisc0019Birth_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 121 | 쓰기 `put` |
| `txtPsgDisc0019Grade_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 122 | 쓰기 `put` |
| `ADULT_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 455 | 쓰기 `putInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 456 | 쓰기 `putInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 457 | 쓰기 `putInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 458 | 쓰기 `putInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 459 | 쓰기 `putInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 460 | 쓰기 `putInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 461 | 쓰기 `putInt` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 462 | 쓰기 `putInt` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 463 | 쓰기 `putInt` |
| `tss_srcar_no` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 653 | 쓰기 `put` |
| `tss_seat_no` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 654 | 쓰기 `put` |
| `cardId` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 109 | 읽기 `getInt` |
| `type` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 135 | 읽기 `getInt` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 150 | 읽기 `getString` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 202 | 쓰기 `putString` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 203 | 쓰기 `putString` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 204 | 쓰기 `putString` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 205 | 쓰기 `putString` |
| `CARD_TYPE` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 206 | 쓰기 `putString` |
| `cardId` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 207 | 쓰기 `putInt` |
| `type` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 208 | 쓰기 `putInt` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 210 | 쓰기 `putString` |
| `type` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 216 | 쓰기 `putInt` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 256 | 읽기 `getString` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 257 | 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 263 | 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 263 | 읽기 `getString` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 41 | 쓰기 `putString` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 42 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 42 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 43 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 43 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 44 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 44 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_CREDIT_TYPE` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 45 | 읽기 `getString` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 49 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 49 | 쓰기 `putString` + 읽기 `getString` |
| `CARD_TYPE` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 52 | 쓰기 `putString` |
| `cardId` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 194 | 읽기 `getInt` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 264 | 읽기 `getString` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 267 | 읽기 `getString` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 272 | 읽기 `getString` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 273 | 읽기 `getString` |
| `CARD_TYPE` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 274 | 읽기 `getString` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 283 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 104 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 121 | 쓰기 `putString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 122 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 152 | 읽기 `getString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 153 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 154 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 99 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 116 | 쓰기 `putString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 117 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 169 | 읽기 `getString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 170 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 171 | 읽기 `getString` |
| `chtnDvCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 691 | 쓰기 `put` |
| `chtnTrnOrdrNo` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 692 | 쓰기 `put` |
| `trnGpCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 694 | 쓰기 `put` |
| `trnGpNm` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 695 | 쓰기 `put` |
| `stlbTrnClsfCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 696 | 쓰기 `put` |
| `stlbTrnClsfNm` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 697 | 쓰기 `put` |
| `runDt` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 698 | 쓰기 `put` |
| `arvDt` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 701 | 쓰기 `put` |
| `arvTm` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 702 | 쓰기 `put` |
| `dptRsStnCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 703 | 쓰기 `put` |
| `dptStnConsOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 705 | 쓰기 `put` |
| `arvStnConsOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 706 | 쓰기 `put` |
| `dptStnRunOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 707 | 쓰기 `put` |
| `arvStnRunOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 708 | 쓰기 `put` |
| `seatAttCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 709 | 쓰기 `put` |
| `rsvPsbFlg` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 710 | 쓰기 `put` |
| `ticketType` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 711 | 쓰기 `put` |
| `psrmClCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 712 | 쓰기 `put` |
| `totPrnb` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 713 | 쓰기 `put` |
| `goStart` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 714 | 쓰기 `put` |
| `goEnd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 715 | 쓰기 `put` |
| `reserveType` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 740 | 쓰기 `put` |
| `mutMrkVrfCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 741 | 쓰기 `put` |
| `radJobId` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 742 | 쓰기 `put` |
| `dptRstnCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 743 | 쓰기 `put` |
| `goStart` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 745 | 쓰기 `put` |
| `goEnd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 746 | 쓰기 `put` |
| `psgFlg1` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 749 | 쓰기 `put` |
| `psgFlg2` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 750 | 쓰기 `put` |
| `psgFlg3` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 751 | 쓰기 `put` |
| `psgFlg4` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 752 | 쓰기 `put` |
| `psgFlg5` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 753 | 쓰기 `put` |
| `psgFlg6` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 754 | 쓰기 `put` |
| `seatAttCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 755 | 쓰기 `put` |
| `trnGpCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 756 | 쓰기 `put` |
| `trainList` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 757 | 쓰기 `put` |
| `INDEX` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1610 | 쓰기 `putInt` |
| `TICKET_KIND` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1611 | 쓰기 `putInt` |
| `MAAS_SERVICE_DV_CD` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1612 | 쓰기 `putString` |
| `MAAS_SERVICE_NAME` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1613 | 쓰기 `putString` |
| `MAAS_RESERVATION_NUM` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1614 | 쓰기 `putString` |
| `MAAS_PNR_NUM` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1615 | 쓰기 `putString` |
| `MAAS_MESSAGE_1` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1616 | 쓰기 `putString` |
| `MAAS_SERVICE_DETAIL_URL` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1617 | 쓰기 `putString` |
| `MAAS_PSB_START_DATE` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1618 | 쓰기 `putString` |
| `MAAS_PSB_END_DATE` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1619 | 쓰기 `putString` |
| `MAAS_PSB_START_TIME` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1620 | 쓰기 `putString` |
| `MAAS_PSB_END_TIME` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1621 | 쓰기 `putString` |
| `IS_EMERGENCY` | `com/korail/talk/ui/ticket/confirm/a.java` | 84 | 읽기 `getBoolean` |
| `RETURN_NO` | `com/korail/talk/ui/ticket/confirm/a.java` | 386 | 읽기 `getString` |
| `KEY_PLF_NO` | `com/korail/talk/ui/ticket/confirm/a.java` | 387 | 쓰기 `putString` |
| `_display_name` | `com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java` | 206 | 쓰기 `put` |
| `mime_type` | `com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java` | 207 | 쓰기 `put` |
| `relative_path` | `com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java` | 208 | 쓰기 `put` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 68 | 쓰기 `putString` |
| `START_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 69 | 쓰기 `putString` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 70 | 쓰기 `putString` |
| `SEAT_TOTAL_COUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 71 | 쓰기 `putString` |
| `START_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 99 | 읽기 `getString` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 100 | 읽기 `getString` |
| `SEAT_TOTAL_COUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 101 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 102 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 157 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 174 | 쓰기 `putString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 175 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 204 | 읽기 `getString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 204 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 204 | 읽기 `getString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 205 | 읽기 `getString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 206 | 읽기 `getString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 207 | 읽기 `getString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 208 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 209 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 210 | 읽기 `getString` |
| `INDEX` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 808 | 쓰기 `putInt` |
| `IS_PURCHASE_HISTORY` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 809 | 쓰기 `putBoolean` |
| `TICKET_KIND` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 810 | 쓰기 `putInt` |
| `MAAS_SERVICE_DV_CD` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 811 | 쓰기 `putString` |
| `MAAS_SERVICE_NAME` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 812 | 쓰기 `putString` |
| `MAAS_RESERVATION_NUM` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 813 | 쓰기 `putString` |
| `MAAS_PNR_NUM` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 814 | 쓰기 `putString` |
| `MAAS_MESSAGE_1` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 815 | 쓰기 `putString` |
| `MAAS_SERVICE_DETAIL_URL` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 816 | 쓰기 `putString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 116 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 133 | 쓰기 `putString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 134 | 쓰기 `putString` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 164 | 읽기 `getString` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 165 | 읽기 `getString` |
| `AMOUNT` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 166 | 읽기 `getString` |
| `STATUS` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 116 | 읽기 `getString` |
| `TITLE` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 118 | 읽기 `getString` |
| `PAY_PERIOD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 119 | 읽기 `getString` |
| `VR_RSV_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 181 | 쓰기 `putString` + 읽기 `getString` |
| `VR_RSV_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 181 | 쓰기 `putString` + 읽기 `getString` |
| `VR_RSV_SQ_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 182 | 쓰기 `putString` + 읽기 `getString` |
| `VR_RSV_SQ_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 182 | 쓰기 `putString` + 읽기 `getString` |
| `RSV_STT_CD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 184 | 쓰기 `putBoolean` + 읽기 `getString` |
| `RSV_STT_CD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 184 | 쓰기 `putBoolean` + 읽기 `getString` |
| `WEB_POST_URL` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 207 | 쓰기 `putString` |
| `STATUS` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 227 | 읽기 `getString` |
| `TITLE` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 242 | 쓰기 `putString` |
| `PAY_PERIOD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 243 | 쓰기 `putString` |
| `STATUS` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 244 | 쓰기 `putString` |
| `RSV_STT_CD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 245 | 쓰기 `putString` |
| `VR_RSV_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 246 | 쓰기 `putString` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/change/TCBookingActivity.java` | 86 | 읽기 `getInt` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/change/TCBookingActivity.java` | 179 | 읽기 `getInt` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 633 | 쓰기 `putInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 634 | 쓰기 `putInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 635 | 쓰기 `putInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 636 | 쓰기 `putInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 637 | 쓰기 `putInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 638 | 쓰기 `putInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 639 | 쓰기 `putInt` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 706 | 쓰기 `putBoolean` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 714 | 쓰기 `putBoolean` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 795 | 쓰기 `putBoolean` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 826 | 쓰기 `putInt` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 827 | 쓰기 `putInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 828 | 쓰기 `putInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 829 | 쓰기 `putInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 830 | 쓰기 `putInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 831 | 쓰기 `putInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 832 | 쓰기 `putInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 833 | 쓰기 `putInt` |
| `WEB_POST_URL` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 975 | 쓰기 `putString` |
| `IS_CLOSE_VIEW` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 976 | 쓰기 `putBoolean` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1011 | 읽기 `getBoolean` |
| `ROUTE_DATE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1012 | 존재 확인 `containsKey` + 읽기 `getString` |
| `SEAT_OPTION_INDEX` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1013 | 읽기 `getInt` |
| `SEAT_OPTION_CODE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1014 | 읽기 `getString` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1024 | 읽기 `getString` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1025 | 읽기 `getString` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1026 | 읽기 `getBoolean` |
| `srtDep` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1124 | 읽기 `getString` |
| `srtArv` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1125 | 읽기 `getString` |
| `srtDt` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1126 | 읽기 `getString` |
| `srtTm` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1127 | 읽기 `getString` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1250 | 읽기 `getInt` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1252 | 읽기 `getInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1253 | 읽기 `getInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1254 | 읽기 `getInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1255 | 읽기 `getInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1256 | 읽기 `getInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1257 | 읽기 `getInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1258 | 읽기 `getInt` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1259 | 읽기 `getInt` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1529 | 쓰기 `putInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1530 | 쓰기 `putInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1531 | 쓰기 `putInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1532 | 쓰기 `putInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1533 | 쓰기 `putInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1534 | 쓰기 `putInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1535 | 쓰기 `putInt` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1536 | 쓰기 `putInt` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1537 | 쓰기 `putInt` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 266 | 쓰기 `putInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 267 | 쓰기 `putInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 268 | 쓰기 `putInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 269 | 쓰기 `putInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 270 | 쓰기 `putInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 271 | 쓰기 `putInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 272 | 쓰기 `putInt` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 286 | 쓰기 `putBoolean` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 294 | 쓰기 `putBoolean` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 382 | 쓰기 `putBoolean` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 405 | 쓰기 `putInt` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 406 | 쓰기 `putInt` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 407 | 쓰기 `putInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 408 | 쓰기 `putInt` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 409 | 쓰기 `putInt` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 410 | 쓰기 `putInt` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 411 | 쓰기 `putInt` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 412 | 쓰기 `putInt` |
| `WEB_POST_URL` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 494 | 쓰기 `putString` |
| `IS_CLOSE_VIEW` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 495 | 쓰기 `putBoolean` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 520 | 읽기 `getBoolean` |
| `ROUTE_DATE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 521 | 존재 확인 `containsKey` + 읽기 `getString` |
| `SEAT_OPTION_INDEX` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 522 | 읽기 `getInt` |
| `SEAT_OPTION_CODE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 523 | 읽기 `getString` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 1023 | 읽기 `getInt` |
| `h_cmpa_cnt` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 553 | 쓰기 `put` |
| `h_cmpa_nm_` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 556 | 쓰기 `put` |
| `h_cmpa_btdt_` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 557 | 쓰기 `put` |
| `h_cmpa_sex_dv_cd_` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 558 | 쓰기 `put` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 95 | 읽기 `getInt` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 96 | 읽기 `getInt` |
| `h_cmpa_cnt` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 365 | 쓰기 `put` |
| `h_cmpa_nm_` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 368 | 쓰기 `put` |
| `h_cmpa_btdt_` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 369 | 쓰기 `put` |
| `h_cmpa_sex_dv_cd_` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 370 | 쓰기 `put` |
| `h_cmpa_cnt` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 547 | 쓰기 `put` |
| `h_cmpa_nm_` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 550 | 쓰기 `put` |
| `h_cmpa_btdt_` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 551 | 쓰기 `put` |
| `h_cmpa_sex_dv_cd_` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 552 | 쓰기 `put` |
| `CMTR_KND_CD` | `com/korail/talk/ui/booking/discountBooking/commutation/a.java` | 139 | 읽기 `getString` |
| `FST_DPT_RS_STN_CD` | `com/korail/talk/ui/booking/discountBooking/commutation/a.java` | 439 | 읽기 `getString` |
| `LAST_ARV_RS_STN_CD` | `com/korail/talk/ui/booking/discountBooking/commutation/a.java` | 439 | 읽기 `getString` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 55 | 읽기 `getInt` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 181 | 읽기 `getString` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 182 | 읽기 `getString` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 183 | 읽기 `getBoolean` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 57 | 읽기 `getInt` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 167 | 읽기 `getString` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 168 | 읽기 `getString` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 169 | 읽기 `getBoolean` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountBookingActivity.java` | 127 | 읽기 `getBoolean` |
| `ROUTE_DATE` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountBookingActivity.java` | 128 | 존재 확인 `containsKey` + 읽기 `getString` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 73 | 읽기 `getInt` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 180 | 읽기 `getString` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 181 | 읽기 `getString` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 182 | 읽기 `getBoolean` |
| `chtnDvCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 48 | 쓰기 `put` |
| `chtnTrnOrdrNo` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 49 | 쓰기 `put` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 51 | 쓰기 `put` |
| `trnGpNm` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 52 | 쓰기 `put` |
| `stlbTrnClsfCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 53 | 쓰기 `put` |
| `stlbTrnClsfNm` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 54 | 쓰기 `put` |
| `runDt` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 55 | 쓰기 `put` |
| `arvDt` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 58 | 쓰기 `put` |
| `arvTm` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 59 | 쓰기 `put` |
| `dptRsStnCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 60 | 쓰기 `put` |
| `dptStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 62 | 쓰기 `put` |
| `arvStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 63 | 쓰기 `put` |
| `dptStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 64 | 쓰기 `put` |
| `arvStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 65 | 쓰기 `put` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 66 | 쓰기 `put` |
| `rsvPsbFlg` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 67 | 쓰기 `put` |
| `ticketType` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 68 | 쓰기 `put` |
| `psrmClCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 69 | 쓰기 `put` |
| `totPrnb` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 70 | 쓰기 `put` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 71 | 쓰기 `put` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 72 | 쓰기 `put` |
| `reserveType` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 88 | 쓰기 `put` |
| `mutMrkVrfCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 89 | 쓰기 `put` |
| `radJobId` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 90 | 쓰기 `put` |
| `dptRsStnCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 91 | 쓰기 `put` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 93 | 쓰기 `put` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 94 | 쓰기 `put` |
| `psgFlg1` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 97 | 쓰기 `put` |
| `psgFlg2` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 98 | 쓰기 `put` |
| `psgFlg3` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 99 | 쓰기 `put` |
| `psgFlg4` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 100 | 쓰기 `put` |
| `psgFlg5` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 101 | 쓰기 `put` |
| `psgFlg6` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 102 | 쓰기 `put` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 103 | 쓰기 `put` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 104 | 쓰기 `put` |
| `trainList` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 105 | 쓰기 `put` |
| `reserveType` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 171 | 쓰기 `put` |
| `mutMrkVrfCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 172 | 쓰기 `put` |
| `radJobId` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 173 | 쓰기 `put` |
| `dptRstnCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 174 | 쓰기 `put` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 176 | 쓰기 `put` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 177 | 쓰기 `put` |
| `psgFlg1` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 180 | 쓰기 `put` |
| `psgFlg2` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 181 | 쓰기 `put` |
| `psgFlg3` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 182 | 쓰기 `put` |
| `psgFlg4` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 183 | 쓰기 `put` |
| `psgFlg5` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 184 | 쓰기 `put` |
| `psgFlg6` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 185 | 쓰기 `put` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 186 | 쓰기 `put` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 187 | 쓰기 `put` |
| `trainList` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 188 | 쓰기 `put` |
| `chtnDvCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 199 | 쓰기 `put` |
| `chtnTrnOrdrNo` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 200 | 쓰기 `put` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 202 | 쓰기 `put` |
| `trnGpNm` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 203 | 쓰기 `put` |
| `stlbTrnClsfCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 204 | 쓰기 `put` |
| `stlbTrnClsfNm` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 205 | 쓰기 `put` |
| `runDt` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 206 | 쓰기 `put` |
| `arvDt` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 209 | 쓰기 `put` |
| `arvTm` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 210 | 쓰기 `put` |
| `dptRsStnCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 211 | 쓰기 `put` |
| `dptStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 213 | 쓰기 `put` |
| `arvStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 214 | 쓰기 `put` |
| `dptStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 215 | 쓰기 `put` |
| `arvStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 216 | 쓰기 `put` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 217 | 쓰기 `put` |
| `rsvPsbFlg` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 218 | 쓰기 `put` |
| `ticketType` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 219 | 쓰기 `put` |
| `psrmClCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 220 | 쓰기 `put` |
| `totPrnb` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 221 | 쓰기 `put` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 222 | 쓰기 `put` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 223 | 쓰기 `put` |
| `arvTm_` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 486 | 읽기 `get` |
| `arvTm_` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 488 | 읽기 `get` |
| `txtPsrmClCd1` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 604 | 읽기 `get` |
