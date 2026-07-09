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

| Key | Source | Line | Context |
|---|---|---:|---|
| `DISCOUNT_MENU_NO` | `com/korail/talk/view/base/BaseViewActivity.java` | 258 | `bundle.putString("DISCOUNT_MENU_NO", "1");` |
| `DISCOUNT_MENU_NO` | `com/korail/talk/view/base/BaseViewActivity.java` | 269 | `bundle2.putString("DISCOUNT_MENU_NO", "2");` |
| `USE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 82 | `bundle.putInt("USE_POINT", getInputPoints());` |
| `USE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 131 | `return this.f30868d.getInt("USE_POINT", 0);` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 143 | `bundle.putString("CARD_NO_1", e(this.f30871g));` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 144 | `bundle.putString("CARD_NO_2", e(this.f30872h));` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 145 | `bundle.putString("CARD_NO_3", e(this.f30873i));` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 146 | `bundle.putString("CARD_NO_4", e(this.f30874j));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 147 | `bundle.putString("CARD_MONTH", e(this.f30875k));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 148 | `bundle.putString("CARD_YEAR", e(this.f30876l));` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 149 | `bundle.putString("CARD_PASSWORD", e(this.f30877m));` |
| `INPUT_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 167 | `bundle.putInt("INPUT_POINT", getInputPoints());` |
| `ENABLE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 168 | `bundle.putInt("ENABLE_POINT", Integer.parseInt(C.getNumber(e(this.f30870f))));` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 176 | `bundle2.putString("CARD_NO_1", e(this.f30871g));` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 177 | `bundle2.putString("CARD_NO_2", e(this.f30872h));` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 178 | `bundle2.putString("CARD_NO_3", e(this.f30873i));` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 179 | `bundle2.putString("CARD_NO_4", e(this.f30874j));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 180 | `bundle2.putString("CARD_MONTH", e(this.f30875k));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 181 | `bundle2.putString("CARD_YEAR", e(this.f30876l));` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 182 | `bundle2.putString("CARD_PASSWORD", e(this.f30877m));` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 188 | `this.f30871g.setText(this.f30867c.getString("CARD_NO_1"));` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 189 | `this.f30872h.setText(this.f30867c.getString("CARD_NO_2"));` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 190 | `this.f30873i.setText(this.f30867c.getString("CARD_NO_3"));` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 191 | `this.f30874j.setText(this.f30867c.getString("CARD_NO_4"));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 192 | `this.f30875k.setText(this.f30867c.getString("CARD_MONTH"));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 193 | `this.f30876l.setText(this.f30867c.getString("CARD_YEAR"));` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 194 | `this.f30877m.setText(this.f30867c.getString("CARD_PASSWORD"));` |
| `USE_POINT` | `com/korail/talk/view/payment/point/WoorimorePointView.java` | 218 | `setUsePointsEdit(this.f30868d.getInt("USE_POINT", 0));` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/CityPointView.java` | 103 | `bundle.putString("CARD_NO_1", e(this.f30814e));` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/CityPointView.java` | 104 | `bundle.putString("CARD_NO_2", e(this.f30815f));` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/CityPointView.java` | 105 | `bundle.putString("CARD_NO_3", e(this.f30816g));` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/CityPointView.java` | 106 | `bundle.putString("CARD_NO_4", e(this.f30817h));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/CityPointView.java` | 107 | `bundle.putString("CARD_MONTH", e(this.f30818i));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/CityPointView.java` | 108 | `bundle.putString("CARD_YEAR", e(this.f30819j));` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/CityPointView.java` | 120 | `bundle.putString("CARD_NO_1", e(this.f30814e));` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/CityPointView.java` | 121 | `bundle.putString("CARD_NO_2", e(this.f30815f));` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/CityPointView.java` | 122 | `bundle.putString("CARD_NO_3", e(this.f30816g));` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/CityPointView.java` | 123 | `bundle.putString("CARD_NO_4", e(this.f30817h));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/CityPointView.java` | 124 | `bundle.putString("CARD_MONTH", e(this.f30818i));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/CityPointView.java` | 125 | `bundle.putString("CARD_YEAR", e(this.f30819j));` |
| `CARD_NO_1` | `com/korail/talk/view/payment/point/CityPointView.java` | 131 | `this.f30814e.setText(this.f30811b.getString("CARD_NO_1"));` |
| `CARD_NO_2` | `com/korail/talk/view/payment/point/CityPointView.java` | 132 | `this.f30815f.setText(this.f30811b.getString("CARD_NO_2"));` |
| `CARD_NO_3` | `com/korail/talk/view/payment/point/CityPointView.java` | 133 | `this.f30816g.setText(this.f30811b.getString("CARD_NO_3"));` |
| `CARD_NO_4` | `com/korail/talk/view/payment/point/CityPointView.java` | 134 | `this.f30817h.setText(this.f30811b.getString("CARD_NO_4"));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/point/CityPointView.java` | 135 | `this.f30818i.setText(this.f30811b.getString("CARD_MONTH"));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/point/CityPointView.java` | 136 | `this.f30819j.setText(this.f30811b.getString("CARD_YEAR"));` |
| `USE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 69 | `bundle.putInt("USE_POINT", getInputPoints());` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 97 | `bundle.putString("PHONE_NM", e(this.f30856g));` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 98 | `bundle.putString("AUTH_NO", e(this.f30857h));` |
| `USE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 103 | `return this.f30853d.getInt("USE_POINT", 0);` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 127 | `bundle.putString("PHONE_NM", e(this.f30856g));` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 136 | `bundle2.putString("PHONE_NM", e(this.f30856g));` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 137 | `bundle2.putString("AUTH_NO", e(this.f30857h));` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 145 | `bundle3.putString("AUTH_NO", e(this.f30857h));` |
| `INPUT_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 146 | `bundle3.putInt("INPUT_POINT", getInputPoints());` |
| `ENABLE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 147 | `bundle3.putInt("ENABLE_POINT", Integer.parseInt(C.getNumber(e(this.f30855f))));` |
| `PHONE_NM` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 153 | `this.f30856g.setText(this.f30852c.getString("PHONE_NM"));` |
| `AUTH_NO` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 154 | `this.f30857h.setText(this.f30852c.getString("AUTH_NO"));` |
| `USE_POINT` | `com/korail/talk/view/payment/point/OkCashBackPointView.java` | 178 | `setUsePointsEdit(this.f30853d.getInt("USE_POINT", 0));` |
| `USE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 74 | `bundle.putInt("USE_POINT", getInputPoints());` |
| `USE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 101 | `return this.f30843d.getInt("USE_POINT", 0);` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/point/LPointView.java` | 133 | `bundle.putString("CARD_PASSWORD", this.f30848i.getText().toString());` |
| `INPUT_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 148 | `bundle2.putInt("INPUT_POINT", getInputPoints());` |
| `ENABLE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 149 | `bundle2.putInt("ENABLE_POINT", Integer.parseInt(C.getNumber(e(this.f30847h))));` |
| `USE_POINT` | `com/korail/talk/view/payment/point/LPointView.java` | 170 | `setUsePointsEdit(this.f30843d.getInt("USE_POINT", 0));` |
| `CARD_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 111 | `String[] strArrSplit = bundle.getString("CARD_NO").split(e.STATE_NAME_NONE);` |
| `CARD_MONTH` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 116 | `CreditCardView.this.f30708m.setText(bundle.getString("CARD_MONTH"));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 117 | `CreditCardView.this.f30709n.setText(bundle.getString("CARD_YEAR"));` |
| `CARD_TYPE` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 122 | `String string = bundle.getString("CARD_TYPE");` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 125 | `String string2 = bundle.getString("CARD_BUSINESS_NUMBER");` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 277 | `bundle.putString("CARD_NICK_NAME", bundle2.getString("CARD_NICK_NAME"));` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 277 | `bundle.putString("CARD_NICK_NAME", bundle2.getString("CARD_NICK_NAME"));` |
| `CARD_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 279 | `bundle.putString("CARD_NO", e(this.f30704i) + e(this.f30705j) + e(this.f30706k) + e(this.f30707l));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 280 | `bundle.putString("CARD_MONTH", e(this.f30708m));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 281 | `bundle.putString("CARD_YEAR", e(this.f30709n));` |
| `CARD_PASSWORD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 282 | `bundle.putString("CARD_PASSWORD", e(this.f30710o));` |
| `IS_NOMAL_CARD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 283 | `bundle.putBoolean("IS_NOMAL_CARD", this.f30712q.getCheckedRadioButtonId() == f.normalCardRadio);` |
| `AUTH_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 284 | `bundle.putString("AUTH_NO", e(this.f30711p));` |
| `INSTALLMENT_PERIOD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 285 | `bundle.putInt("INSTALLMENT_PERIOD", this.f30703h.getSelectIndex());` |
| `CARD_NO_1` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | `setCreditCardInput(bundle.getString("CARD_NO_1"), bundle.getString("CARD_NO_2"), bundle.getString("CARD_NO_3"), bundle.getString("CARD_NO_4"), bundle.getString("CARD_YEAR"), bundle.getString("CARD_MONTH"));` |
| `CARD_NO_2` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | `setCreditCardInput(bundle.getString("CARD_NO_1"), bundle.getString("CARD_NO_2"), bundle.getString("CARD_NO_3"), bundle.getString("CARD_NO_4"), bundle.getString("CARD_YEAR"), bundle.getString("CARD_MONTH"));` |
| `CARD_NO_3` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | `setCreditCardInput(bundle.getString("CARD_NO_1"), bundle.getString("CARD_NO_2"), bundle.getString("CARD_NO_3"), bundle.getString("CARD_NO_4"), bundle.getString("CARD_YEAR"), bundle.getString("CARD_MONTH"));` |
| `CARD_NO_4` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | `setCreditCardInput(bundle.getString("CARD_NO_1"), bundle.getString("CARD_NO_2"), bundle.getString("CARD_NO_3"), bundle.getString("CARD_NO_4"), bundle.getString("CARD_YEAR"), bundle.getString("CARD_MONTH"));` |
| `CARD_YEAR` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | `setCreditCardInput(bundle.getString("CARD_NO_1"), bundle.getString("CARD_NO_2"), bundle.getString("CARD_NO_3"), bundle.getString("CARD_NO_4"), bundle.getString("CARD_YEAR"), bundle.getString("CARD_MONTH"));` |
| `CARD_MONTH` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 322 | `setCreditCardInput(bundle.getString("CARD_NO_1"), bundle.getString("CARD_NO_2"), bundle.getString("CARD_NO_3"), bundle.getString("CARD_NO_4"), bundle.getString("CARD_YEAR"), bundle.getString("CARD_MONTH"));` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 331 | `bundle.putString("CARD_NICK_NAME", b(j.payment_direct_input_plus));` |
| `IS_NOMAL_CARD` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 332 | `bundle.putBoolean("IS_NOMAL_CARD", true);` |
| `CARD_NICK_NAME` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 337 | `strArr[i9] = arrayList.get(i9).getString("CARD_NICK_NAME");` |
| `CARD_NO` | `com/korail/talk/view/payment/creditCard/CreditCardView.java` | 454 | `} else if (str7.equals(((Bundle) this.f30698c.get(i9)).getString("CARD_NO"))) {` |
| `loginType` | `com/korail/talk/ui/scheme/DataActivity.java` | 31 | `jSONObject.put("loginType", string);` |
| `loginId` | `com/korail/talk/ui/scheme/DataActivity.java` | 32 | `jSONObject.put("loginId", (z10 \|\| z9) ? a.decryptAES(getApplicationContext(), string2) : "");` |
| `loginPw` | `com/korail/talk/ui/scheme/DataActivity.java` | 33 | `jSONObject.put("loginPw", z9 ? a.decryptAES(getApplicationContext(), string3) : "");` |
| `isAutoLogin` | `com/korail/talk/ui/scheme/DataActivity.java` | 34 | `jSONObject.put("isAutoLogin", z9);` |
| `isSaveMemberNumber` | `com/korail/talk/ui/scheme/DataActivity.java` | 35 | `jSONObject.put("isSaveMemberNumber", z10);` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/limousine/RenewalLimousineActivity.java` | 332 | `this.f29475p.setEnabled(bundle.getInt("TOTAL_PERSON_COUNT") > 0);` |
| `dptRsStnCd` | `com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java` | 376 | `this.f29459t = this.f29457r.getString("dptRsStnCd");` |
| `psrmClCd` | `com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java` | 378 | `this.f29461v = this.f29457r.getString("psrmClCd");` |
| `seatAttCd` | `com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java` | 379 | `this.f29463x = this.f29457r.getString("seatAttCd");` |
| `dptRsStnCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 120 | `this.f29428q = this.f29425n.getString("dptRsStnCd");` |
| `arvRsStnNm` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 122 | `this.f29430s = this.f29425n.getString("arvRsStnNm");` |
| `tmGpCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 123 | `this.f29431t = this.f29425n.getString("tmGpCd");` |
| `psrmClCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 124 | `this.f29432u = this.f29425n.getString("psrmClCd");` |
| `seatAttCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 127 | `this.f29435x = this.f29425n.getString("seatAttCd");` |
| `rsvSaleDvCd` | `com/korail/talk/ui/limousine/LimousineListActivity.java` | 128 | `this.f29436y = this.f29425n.getString("rsvSaleDvCd");` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 283 | `this.f29412p.setEnabled(bundle.getInt("TOTAL_PERSON_COUNT") > 0);` |
| `dptRsStnCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 314 | `bundle.putString("dptRsStnCd", "0501");` |
| `arvRsStnNm` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 316 | `bundle.putString("arvRsStnNm", this.f29416t[this.f29415s]);` |
| `tmGpCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 317 | `bundle.putString("tmGpCd", s.LIMOUSINE.getCode());` |
| `psrmClCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 318 | `bundle.putString("psrmClCd", "1");` |
| `seatAttCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 321 | `bundle.putString("seatAttCd", "");` |
| `rsvSaleDvCd` | `com/korail/talk/ui/limousine/LimousineActivity.java` | 322 | `bundle.putString("rsvSaleDvCd", "T");` |
| `TRAIN_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 127 | `aVar.f29360a.setText(bundle.getString("TRAIN_NAME"));` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 128 | `aVar.f29361b.setText(bundle.getString("TOTAL_AMOUNT"));` |
| `STATION_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 129 | `aVar.f29362c.setText(N.fromHtml(bundle.getString("STATION_NAME")));` |
| `STATION_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 195 | `commReservationRequest.setStationInfo(((Bundle) this.f29355o.get(i9)).getString("STATION_NAME"));` |
| `TRAIN_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 298 | `bundle.putString("TRAIN_NAME", O.getTrainGroupName(N.getIntegerString(train_list.get(0).getH_trn_gp_cd())));` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 299 | `bundle.putString("TOTAL_AMOUNT", getString(j.common_amount, N.getDecimalFormatString(train_list.get(0).getH_schd_prc())));` |
| `STATION_NAME` | `com/korail/talk/ui/inquiry/CommutationInquiryActivity.java` | 300 | `bundle.putString("STATION_NAME", C0816p.getRoute(train_list));` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 132 | `if (((Integer) group.get("CHECKED_POSITION")).intValue() == i10) {` |
| `DEPARTURE_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 179 | `c0304b.f29380b.setText((String) group.get("DEPARTURE_STATION_NM"));` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 180 | `c0304b.f29381c.setText((String) group.get("ARRIVAL_STATION_NM"));` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 333 | `this.f29370p.getGroup(i9).put("CHECKED_POSITION", Integer.valueOf(i10));` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 341 | `int iIntValue = ((Integer) ((HashMap) this.f29365k.get(i11)).get("CHECKED_POSITION")).intValue();` |
| `DEPARTURE_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 411 | `map.put("DEPARTURE_STATION_NM", nCardInquiryRequest.getDptRsStnNm());` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 412 | `map.put("ARRIVAL_STATION_NM", nCardInquiryRequest.getArvRsStnNm());` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 413 | `map.put("CHECKED_POSITION", -1);` |
| `DEPARTURE_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 443 | `map.put("DEPARTURE_STATION_NM", nCardInquiryRequest.getDptRsStnNm());` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 444 | `map.put("ARRIVAL_STATION_NM", nCardInquiryRequest.getArvRsStnNm());` |
| `CHECKED_POSITION` | `com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java` | 445 | `map.put("CHECKED_POSITION", -1);` |
| `NOTICE_MESSAGE` | `com/korail/talk/ui/intro/IntroActivity.java` | 770 | `jSONObject.put("NOTICE_MESSAGE", noticeResponse.getPtwtTtl());` |
| `NOTICE_POST_DATA` | `com/korail/talk/ui/intro/IntroActivity.java` | 771 | `jSONObject.put("NOTICE_POST_DATA", noticeResponse.getNoticePostData());` |
| `callback` | `com/korail/talk/ui/web/BaseWebViewActivity.java` | 982 | `jSONObject.remove("callback");` |
| `Device` | `com/korail/talk/ui/reservation/BixbyReservationActivity.java` | 29 | `map.put("Device", BaseRequest.ANDROID);` |
| `Version` | `com/korail/talk/ui/reservation/BixbyReservationActivity.java` | 30 | `map.put("Version", "250601003");` |
| `Key` | `com/korail/talk/ui/reservation/BixbyReservationActivity.java` | 31 | `map.put("Key", BaseRequest.APP_KEY);` |
| `tss_srcar_no` | `com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java` | 268 | `pushUpdateRequestN0.setScarNo((String) map.get("tss_srcar_no"));` |
| `tss_seat_no` | `com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java` | 269 | `pushUpdateRequestN0.setSeatNo((String) map.get("tss_seat_no"));` |
| `messageId` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 148 | `String string = ((Bundle) PushHistoryActivity.this.f29895o.get(this.f29911a)).getString("messageId");` |
| `message` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 171 | `PushHistoryActivity.this.U0(((MSGVo) PushHistoryActivity.this.f29900t.get(this.f29913a)).getParam(), this.f29914b.getString("message"));` |
| `noticeDate` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 221 | `long j9 = bundle.getLong("noticeDate");` |
| `noticeDate` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 239 | `PushHistoryActivity.this.f29891k.setTimeInMillis(((Bundle) PushHistoryActivity.this.f29895o.get(i9 - 1)).getLong("noticeDate"));` |
| `message` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 247 | `((TextView) view.findViewById(f.msgTxt)).setText(bundle.getString("message"));` |
| `messageId` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 249 | `int i10 = Integer.parseInt(bundle.getString("messageId"));` |
| `ADULT_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 549 | `bundle.putInt("ADULT_COUNT", i9);` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 550 | `bundle.putInt("TEENAGER_COUNT", 0);` |
| `CHILD_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 551 | `bundle.putInt("CHILD_COUNT", i10);` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 552 | `bundle.putInt("CHILD_ACCOMPANY_COUNT", i11);` |
| `SENIOR_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 553 | `bundle.putInt("SENIOR_COUNT", i12);` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 554 | `bundle.putInt("HIGH_DISABLE_COUNT", i13);` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 555 | `bundle.putInt("LOW_DISABLE_COUNT", i14);` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 556 | `bundle.putInt("GUIDE_DOG_COUNT", 0);` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 557 | `bundle.putInt("TOTAL_PERSON_COUNT", i15);` |
| `noticeDate` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 566 | `bundle.putLong("noticeDate", C0808h.getCalendarFromString(((MSGVo) this.f29900t.get(i9)).getTimeStamp(), "yyyyMMddHHmmss").getTime().getTime());` |
| `messageId` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 567 | `bundle.putString("messageId", ((MSGVo) this.f29900t.get(i9)).getTaskName());` |
| `message` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 568 | `bundle.putString("message", ((MSGVo) this.f29900t.get(i9)).getContent());` |
| `msg_vo` | `com/korail/talk/ui/push/PushHistoryActivity.java` | 569 | `bundle.putString("msg_vo", ((MSGVo) this.f29900t.get(i9)).getParam());` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 191 | `aVar.mTvDepartureDate.setText(item.getString("DEPARTURE_DATE"));` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 192 | `aVar.mTvTicketCount.setText(ReservedTicketActivity.this.getString(j.common_s_ticket_count, Integer.valueOf(item.getInt("TICKET_COUNT"))));` |
| `TICKET_TRAIN_INFO` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 193 | `aVar.mTvTicketTrainInfo.setText(item.getString("TICKET_TRAIN_INFO"));` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 194 | `aVar.mTvTicketNotice.setText(item.getString("TICKET_NOTICE"));` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 200 | `aVar.mBtnCancelable.setEnabled(item.getBoolean("TICKET_CANCELABLE"));` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 202 | `aVar.mBtnChange.setEnabled(item.getBoolean("TICKET_CHANGE"));` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 205 | `if (item.getBoolean("TICKET_PURCHASABLE")) {` |
| `TICKET_PAYMENT_FLG` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 214 | `if (item.getString("TICKET_PAYMENT_FLG", "").equals("N")) {` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 327 | `bundle.putString("TICKET_NOTICE", getString(j.reserved_ticket_wait_reservation));` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 329 | `bundle.putBoolean("TICKET_CANCELABLE", true);` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 330 | `bundle.putBoolean("TICKET_PURCHASABLE", false);` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 331 | `bundle.putBoolean("TICKET_CHANGE", false);` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 334 | `bundle.putString("TICKET_NOTICE", getString(j.reserved_ticket_pay_completed));` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 337 | `bundle.putBoolean("TICKET_CANCELABLE", false);` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 338 | `bundle.putBoolean("TICKET_PURCHASABLE", false);` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 339 | `bundle.putBoolean("TICKET_CHANGE", false);` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 342 | `bundle.putBoolean("TICKET_CANCELABLE", true);` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 343 | `bundle.putBoolean("TICKET_PURCHASABLE", true);` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 344 | `bundle.putBoolean("TICKET_CHANGE", false);` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 347 | `bundle.putBoolean("TICKET_CANCELABLE", true);` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 348 | `bundle.putBoolean("TICKET_PURCHASABLE", true);` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 349 | `bundle.putBoolean("TICKET_CHANGE", false);` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 369 | `bundle.putString("TICKET_NOTICE", (string + X.LF) + getString(j.reserved_ticket_pay_deadline_desc));` |
| `TICKET_CANCELABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 371 | `bundle.putBoolean("TICKET_CANCELABLE", true);` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 372 | `bundle.putBoolean("TICKET_PURCHASABLE", true);` |
| `TICKET_CHANGE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 373 | `bundle.putBoolean("TICKET_CHANGE", true);` |
| `TICKET_PAYMENT_FLG` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 374 | `bundle.putString("TICKET_PAYMENT_FLG", trainInfo.getH_payment_flg() == null ? "" : trainInfo.getH_payment_flg());` |
| `TICKET_PURCHASABLE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 435 | `if (item.getBoolean("TICKET_PURCHASABLE")) {` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 436 | `if (item.getInt("TICKET_COUNT") > 9) {` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 469 | `bundle.putString("DEPARTURE_DATE", C0808h.convertFormat(trainInfo.getH_run_dt(), "yyyyMMdd", "yyyy년 MM월 dd일 (E)"));` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 470 | `bundle.putInt("TICKET_COUNT", I0(trainInfo));` |
| `TICKET_TRAIN_INFO` | `com/korail/talk/ui/menu/ReservedTicketActivity.java` | 472 | `bundle.putString("TICKET_TRAIN_INFO", C0816p.getTrainInfo(train_info));` |
| `DISCOUNT_SUM` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 105 | `aVar.f29552b.setText(DelayDiscountCouponActivity.this.getString(j.common_amount, N.getDecimalFormatString(bundleA.getInt("DISCOUNT_SUM"))) + X.LF + DelayDiscountCouponActivity.this.getString(j.common_discount));` |
| `EXPIRED_DATE` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 106 | `aVar.f29553c.setText(bundleA.getString("EXPIRED_DATE"));` |
| `COUPON_NO` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 108 | `aVar.f29551a.setText(bundleA.getString("COUPON_NO"));` |
| `COUPON_NO` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 185 | `bundle.putString("COUPON_NO", H4.a.getReturnNumberWithDash(h_orgtk_wct_no, h_orgtk_ret_sale_dt, h_orgtk_sale_sqno, h_orgtk_ret_pwd));` |
| `DISCOUNT_SUM` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 187 | `bundle.putInt("DISCOUNT_SUM", Integer.parseInt(delayCoupon.getH_dlay_fare()));` |
| `EXPIRED_DATE` | `com/korail/talk/ui/menu/DelayDiscountCouponActivity.java` | 188 | `bundle.putString("EXPIRED_DATE", C0808h.convertFormat(delayCoupon.getH_use_psb_dt(), "yyyyMMdd", "yyyy년 MM월 dd일") + "까지 사용 가능\n");` |
| `ADULT_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `ADULT_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `CHILD_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `CHILD_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `SENIOR_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `SENIOR_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/menu/ReservedTicketChangeActivity.java` | 61 | `this.f29591p.setEnabled(((bundle.getInt("ADULT_COUNT") == this.f29586k.getInt("ADULT_COUNT") && bundle.getInt("CHILD_COUNT") == this.f29586k.getInt("CHILD_COUNT") && bundle.getInt("CHILD_ACCOMPANY_COUNT") == this.f29586k.getInt("CHILD_ACCOMPANY_COUNT") && bundle.getInt("SENIOR_COUNT") == this.f29586` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 223 | `aVar.mCheckBox.setChecked(bundleB.getBoolean("CHECK_BOX"));` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 224 | `aVar.mTvDepartureDate.setText(bundleB.getString("DEPARTURE_DATE"));` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 225 | `aVar.mTvTicketCnt.setText(BasketTicketActivity.this.getString(j.common_s_ticket_count, Integer.valueOf(bundleB.getInt("TICKET_COUNT"))));` |
| `TRAIN_NAME` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 226 | `aVar.mTvTrainRoute.setText(bundleB.getString("TRAIN_NAME"));` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 227 | `aVar.mTvTicketNotice.setText(bundleB.getString("TICKET_NOTICE"));` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 228 | `String decimalFormatString = N.getDecimalFormatString(bundleB.getInt("TOTAL_AMOUNT"));` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 229 | `String decimalFormatString2 = N.getDecimalFormatString(bundleB.getInt("RECEIVED_AMOUNT"));` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 240 | `bundleB.getBoolean("IS_DISCOUNT_ABLE");` |
| `IS_LIMOUSINE_TICKET` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 241 | `aVar.mBtnBookingDetail.setVisibility(bundleB.getBoolean("IS_LIMOUSINE_TICKET") ? 8 : 0);` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 248 | `sb.append(bundleB.getString("DEPARTURE_DATE"));` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 250 | `sb.append(BasketTicketActivity.this.getString(j.common_s_ticket_count, Integer.valueOf(bundleB.getInt("TICKET_COUNT"))));` |
| `TRAIN_NAME` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 252 | `sb.append(bundleB.getString("TRAIN_NAME"));` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 259 | `sb.append(bundleB.getString("TICKET_NOTICE"));` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 271 | `String string = bundleB.getString("PNR_NO");` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 276 | `BasketTicketActivity.this.G0(bundleB.getString("PNR_NO"), reservationResponse.getH_jrny_cnt(), bundleB.getString(DisabilityCertificationActivity.SQ_NO), reservationResponse.getJrny_infos().getJrny_info().get(0).getH_rsv_chg_no());` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 287 | `b(i9).putBoolean("CHECK_BOX", ((CheckBox) view).isChecked());` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 301 | `String string2 = this.f29521K.b(i9).getString("H_VR_RSV_NO");` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 307 | `if (((Bundle) this.f29515E.get(i10)).getBoolean("CHECK_BOX") && (string = this.f29521K.b(i10).getString("H_VR_RSV_NO")) != null && !string.isEmpty()) {` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 307 | `if (((Bundle) this.f29515E.get(i10)).getBoolean("CHECK_BOX") && (string = this.f29521K.b(i10).getString("H_VR_RSV_NO")) != null && !string.isEmpty()) {` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 395 | `arrayList.add(bundleB.getString("PNR_NO"));` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 396 | `sb.append(bundleB.getString("LUMP_STL_TGT_NO"));` |
| `HID_RSV_CHG_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 397 | `string = bundleB.getString("HID_RSV_CHG_NO");` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 398 | `i11 = bundleB.getInt("RECEIVED_AMOUNT");` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 399 | `i10 = bundleB.getInt("TOTAL_AMOUNT") - bundleB.getInt("RECEIVED_AMOUNT");` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 399 | `i10 = bundleB.getInt("TOTAL_AMOUNT") - bundleB.getInt("RECEIVED_AMOUNT");` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 400 | `z9 = bundleB.getBoolean("IS_DISCOUNT_ABLE");` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 408 | `if (((Bundle) this.f29515E.get(i15)).getBoolean("CHECK_BOX")) {` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 412 | `String string2 = bundleB2.getString("PNR_NO");` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 415 | `arrayList.add(bundleB2.getString("PNR_NO"));` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 420 | `sb.append(bundleB2.getString("LUMP_STL_TGT_NO"));` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 421 | `i14 += bundleB2.getInt("RECEIVED_AMOUNT");` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 422 | `i13 += bundleB2.getInt("TOTAL_AMOUNT") - bundleB2.getInt("RECEIVED_AMOUNT");` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 422 | `i13 += bundleB2.getInt("TOTAL_AMOUNT") - bundleB2.getInt("RECEIVED_AMOUNT");` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 462 | `maasCancelRequest.setLumpStlTgtNo(bundle.getString("LUMP_STL_TGT_NO"));` |
| `custMgNo` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 463 | `maasCancelRequest.setCustMgNo(bundle.getString("custMgNo"));` |
| `ADD_SRV_DV_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 506 | `arrayList.add(bundleB.getString("ADD_SRV_DV_CD"));` |
| `COPT_ENT_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 507 | `arrayList3.add(bundleB.getString("COPT_ENT_RSV_NO"));` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 508 | `arrayList4.add(bundleB.getString("LUMP_STL_TGT_NO"));` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 509 | `arrayList2.add(bundleB.getString("H_VR_RSV_NO"));` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 520 | `if (((Bundle) this.f29515E.get(i11)).getBoolean("CHECK_BOX")) {` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 522 | `if (bundleB2.getString("H_VR_RSV_NO") != null && !bundleB2.getString("H_VR_RSV_NO").isEmpty()) {` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 522 | `if (bundleB2.getString("H_VR_RSV_NO") != null && !bundleB2.getString("H_VR_RSV_NO").isEmpty()) {` |
| `ADD_SRV_DV_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 523 | `arrayList.add(bundleB2.getString("ADD_SRV_DV_CD"));` |
| `COPT_ENT_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 524 | `arrayList3.add(bundleB2.getString("COPT_ENT_RSV_NO"));` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 525 | `arrayList4.add(bundleB2.getString("LUMP_STL_TGT_NO"));` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 526 | `arrayList2.add(bundleB2.getString("H_VR_RSV_NO"));` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 547 | `if (((Bundle) this.f29515E.get(i9)).getBoolean("CHECK_BOX")) {` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 560 | `if (bundle.getBoolean("CHECK_BOX")) {` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 561 | `arrayList.add(bundle.getString("PNR_NO"));` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 572 | `bundle2.putBoolean("CHECK_BOX", this.f29518H.contains(h_pnr_no));` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 574 | `bundle2.putBoolean("CHECK_BOX", arrayList.contains(h_pnr_no));` |
| `JRNY_TP_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 576 | `bundle2.putString("JRNY_TP_CD", cartInfo.getH_jrny_tp_cd());` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 581 | `bundle2.putString("PNR_NO", h_pnr_no);` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 582 | `bundle2.putString("DEPARTURE_DATE", C0808h.convertFormat(cartInfo.getH_dpt_dt().isEmpty() ? cartInfo.getUtlStDt() : cartInfo.getH_dpt_dt(), "yyyyMMdd", "yyyy년 MM월 dd일 (E)"));` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 584 | `bundle2.putString("DEPARTURE_DATE", C0808h.convertFormat(cartInfo.getH_dpt_dt(), "yyyyMMdd", "yyyy년 MM월 dd일 (E)"));` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 585 | `bundle2.putInt("TICKET_COUNT", cartInfo.getH_tk_cnt());` |
| `DEPARTURE_DATE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 587 | `bundle2.putString("DEPARTURE_DATE", C0808h.convertFormat(cartInfo.getUtlStDt(), "yyyyMMdd", "yyyy년 MM월 dd일 (E)"));` |
| `TICKET_COUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 588 | `bundle2.putInt("TICKET_COUNT", 1);` |
| `h_vr_rsv_no` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 591 | `bundle2.putString("h_vr_rsv_no", cartInfo.getH_vr_rsv_no());` |
| `h_rcvd_amt` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 592 | `bundle2.putString("h_rcvd_amt", cartInfo.getH_rcvd_amt());` |
| `custMgNo` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 593 | `bundle2.putString("custMgNo", strDecryptAES);` |
| `TRAIN_NAME` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 594 | `bundle2.putString("TRAIN_NAME", cartInfo.getH_gd_nm());` |
| `LUMP_STL_TGT_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 595 | `bundle2.putString("LUMP_STL_TGT_NO", cartInfo.getH_lump_stl_tgt_no());` |
| `H_VR_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 596 | `bundle2.putString("H_VR_RSV_NO", cartInfo.getH_vr_rsv_no());` |
| `ADD_SRV_DV_CD` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 597 | `bundle2.putString("ADD_SRV_DV_CD", cartInfo.getAddSrvDvCd());` |
| `COPT_ENT_RSV_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 598 | `bundle2.putString("COPT_ENT_RSV_NO", cartInfo.getCoptEntRsvNo());` |
| `IS_LIMOUSINE_TICKET` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 599 | `bundle2.putBoolean("IS_LIMOUSINE_TICKET", "3".equals(cartInfo.getH_item_dv_cd()));` |
| `TICKET_NOTICE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 601 | `bundle2.putString("TICKET_NOTICE", h_stl_lmt_tm.length() == 8 ? String.format(getString(j.reserved_ticket_pay_deadline), C0808h.convertFormat(h_stl_lmt_tm, "yyyyMMdd", "yyyy년 MM월 dd일")) : String.format(getString(j.reserved_ticket_pay_deadline), C0808h.convertFormat(h_stl_lmt_tm, "yyyyMMddHHmmss", "y` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 605 | `I0(((Bundle) this.f29515E.get(this.f29519I)).getString("PNR_NO"));` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 637 | `bundle.putInt("TOTAL_AMOUNT", Integer.parseInt(reservationResponse.getH_tot_prc()) + Integer.parseInt(reservationResponse.getH_tot_fare()));` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 638 | `bundle.putInt("RECEIVED_AMOUNT", Integer.parseInt(reservationResponse.getH_tot_rcvd_amt()));` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 640 | `bundle.putBoolean("IS_DISCOUNT_ABLE", T4.a.isDiscountReservation(reservationResponse));` |
| `HID_RSV_CHG_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 641 | `bundle.putString("HID_RSV_CHG_NO", reservationResponse.getJrny_infos().getJrny_info().get(0).getH_rsv_chg_no());` |
| `TOTAL_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 643 | `bundle.putInt("TOTAL_AMOUNT", Integer.parseInt(((Bundle) this.f29515E.get(this.f29519I)).getString("h_rcvd_amt")));` |
| `h_rcvd_amt` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 643 | `bundle.putInt("TOTAL_AMOUNT", Integer.parseInt(((Bundle) this.f29515E.get(this.f29519I)).getString("h_rcvd_amt")));` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 644 | `bundle.putInt("RECEIVED_AMOUNT", Integer.parseInt(((Bundle) this.f29515E.get(this.f29519I)).getString("h_rcvd_amt")));` |
| `h_rcvd_amt` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 644 | `bundle.putInt("RECEIVED_AMOUNT", Integer.parseInt(((Bundle) this.f29515E.get(this.f29519I)).getString("h_rcvd_amt")));` |
| `IS_DISCOUNT_ABLE` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 645 | `bundle.putBoolean("IS_DISCOUNT_ABLE", false);` |
| `PNR_NO` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 650 | `I0(((Bundle) this.f29515E.get(this.f29519I)).getString("PNR_NO"));` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 684 | `((Bundle) it.next()).putBoolean("CHECK_BOX", this.f29523M.isChecked());` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 725 | `if (((Bundle) it.next()).getBoolean("CHECK_BOX")) {` |
| `CHECK_BOX` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 827 | `if (bundle.getBoolean("CHECK_BOX")) {` |
| `RECEIVED_AMOUNT` | `com/korail/talk/ui/menu/BasketTicketActivity.java` | 829 | `i10 += bundle.getInt("RECEIVED_AMOUNT");` |
| `hidSaleWctNo1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | `u0(ticketPresentParams.get("hidSaleWctNo1"), ticketPresentParams.get("hidSaleDt1"), ticketPresentParams.get("hidSaleSqno1"), ticketPresentParams.get("hidtkRetPwd1"));` |
| `hidSaleDt1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | `u0(ticketPresentParams.get("hidSaleWctNo1"), ticketPresentParams.get("hidSaleDt1"), ticketPresentParams.get("hidSaleSqno1"), ticketPresentParams.get("hidtkRetPwd1"));` |
| `hidSaleSqno1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | `u0(ticketPresentParams.get("hidSaleWctNo1"), ticketPresentParams.get("hidSaleDt1"), ticketPresentParams.get("hidSaleSqno1"), ticketPresentParams.get("hidtkRetPwd1"));` |
| `hidtkRetPwd1` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 89 | `u0(ticketPresentParams.get("hidSaleWctNo1"), ticketPresentParams.get("hidSaleDt1"), ticketPresentParams.get("hidSaleSqno1"), ticketPresentParams.get("hidtkRetPwd1"));` |
| `chgePbpRsvNo` | `com/korail/talk/ui/delivery/DeliveryActivity.java` | 156 | `map.put("chgePbpRsvNo", str);` |
| `txtPsgDisc0019Sqno_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 117 | `map.put("txtPsgDisc0019Sqno_" + i10, Integer.valueOf(buntData.getInt(SQ_NO)));` |
| `txtJobDvCd0019_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 118 | `map2.put("txtJobDvCd0019_" + i10, "1");` |
| `txtPsgDisc0019PsDvCd_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 119 | `map3.put("txtPsgDisc0019PsDvCd_" + i10, buntData.getString(DISABILITY_CERTIFICATION_CODE));` |
| `txtPsgDisc0019CustNm_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 120 | `map4.put("txtPsgDisc0019CustNm_" + i10, "");` |
| `txtPsgDisc0019Birth_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 121 | `map2.put("txtPsgDisc0019Birth_" + i10, buntData.getString(BIRTH_DAY));` |
| `txtPsgDisc0019Grade_` | `com/korail/talk/ui/certification/DisabilityCertificationActivity.java` | 122 | `map2.put("txtPsgDisc0019Grade_" + i10, buntData.getString(SUITABILITY_RATING_CODE));` |
| `ADULT_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 455 | `bundle.putInt("ADULT_COUNT", i9);` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 456 | `bundle.putInt("TEENAGER_COUNT", 0);` |
| `CHILD_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 457 | `bundle.putInt("CHILD_COUNT", i10);` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 458 | `bundle.putInt("CHILD_ACCOMPANY_COUNT", i11);` |
| `SENIOR_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 459 | `bundle.putInt("SENIOR_COUNT", i12);` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 460 | `bundle.putInt("HIGH_DISABLE_COUNT", i13);` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 461 | `bundle.putInt("LOW_DISABLE_COUNT", i14);` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 462 | `bundle.putInt("GUIDE_DOG_COUNT", 0);` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 463 | `bundle.putInt("TOTAL_PERSON_COUNT", i15);` |
| `tss_srcar_no` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 653 | `map.put("tss_srcar_no", String.valueOf(iF0));` |
| `tss_seat_no` | `com/korail/talk/ui/seat/SeatSearchActivity.java` | 654 | `map.put("tss_seat_no", selectedSeatList.get(0).getSeat_no());` |
| `cardId` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 109 | `J4.b.getInstance().deleteCreditCard(bundle.getInt("cardId"));` |
| `type` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 135 | `return d(i9).getInt("type");` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 150 | `String string = d(i9).getString("CARD_NICK_NAME");` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 202 | `bundle.putString("CARD_NICK_NAME", F4.a.decryptAES(getApplicationContext(), creditCard.getCardNickname()));` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 203 | `bundle.putString("CARD_NO", F4.a.decryptAES(getApplicationContext(), creditCard.getCardNumber()));` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 204 | `bundle.putString("CARD_MONTH", F4.a.decryptAES(getApplicationContext(), creditCard.getCardValidateMonth()));` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 205 | `bundle.putString("CARD_YEAR", F4.a.decryptAES(getApplicationContext(), creditCard.getCardValidateYear()));` |
| `CARD_TYPE` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 206 | `bundle.putString("CARD_TYPE", F4.a.decryptAES(getApplicationContext(), creditCard.getCardType()));` |
| `cardId` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 207 | `bundle.putInt("cardId", creditCard.getId());` |
| `type` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 208 | `bundle.putInt("type", 0);` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 210 | `bundle.putString("CARD_BUSINESS_NUMBER", F4.a.decryptAES(getApplicationContext(), creditCard.getBusinessNum()));` |
| `type` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 216 | `bundle2.putInt("type", 1);` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 256 | `this.f30098i0.setText(data.getString("CARD_NICK_NAME"));` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 257 | `StringBuilder sb = new StringBuilder(data.getString("CARD_NO"));` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 263 | `this.f30099j0.setText(getString(j.favorite_card_info, sb.toString(), data.getString("CARD_MONTH"), data.getString("CARD_YEAR")));` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/b.java` | 263 | `this.f30099j0.setText(getString(j.favorite_card_info, sb.toString(), data.getString("CARD_MONTH"), data.getString("CARD_YEAR")));` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 41 | `bundle.putString("CARD_NICK_NAME", "");` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 42 | `bundle.putString("CARD_NO", extras.getString("CARD_NO"));` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 42 | `bundle.putString("CARD_NO", extras.getString("CARD_NO"));` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 43 | `bundle.putString("CARD_MONTH", extras.getString("CARD_MONTH"));` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 43 | `bundle.putString("CARD_MONTH", extras.getString("CARD_MONTH"));` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 44 | `bundle.putString("CARD_YEAR", extras.getString("CARD_YEAR"));` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 44 | `bundle.putString("CARD_YEAR", extras.getString("CARD_YEAR"));` |
| `CARD_CREDIT_TYPE` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 45 | `String string = extras.getString("CARD_CREDIT_TYPE");` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 49 | `bundle.putString("CARD_BUSINESS_NUMBER", extras.getString("CARD_BUSINESS_NUMBER"));` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 49 | `bundle.putString("CARD_BUSINESS_NUMBER", extras.getString("CARD_BUSINESS_NUMBER"));` |
| `CARD_TYPE` | `com/korail/talk/ui/setting/favoriteCards/FavoriteCardsSettingActivity.java` | 52 | `bundle.putString("CARD_TYPE", str);` |
| `cardId` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 194 | `creditCard.setId(getArguments().getInt("cardId"));` |
| `CARD_NICK_NAME` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 264 | `this.f30079d0.setText(arguments.getString("CARD_NICK_NAME"));` |
| `CARD_NO` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 267 | `String string = arguments.getString("CARD_NO");` |
| `CARD_MONTH` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 272 | `this.f30081f0.setText(arguments.getString("CARD_MONTH"));` |
| `CARD_YEAR` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 273 | `this.f30082g0.setText(arguments.getString("CARD_YEAR"));` |
| `CARD_TYPE` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 274 | `String string2 = arguments.getString("CARD_TYPE");` |
| `CARD_BUSINESS_NUMBER` | `com/korail/talk/ui/setting/favoriteCards/a.java` | 283 | `String string3 = arguments.getString("CARD_BUSINESS_NUMBER");` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 104 | `bundle.putString("AMOUNT", TCActivity.this.getString(j.common_amount, N.getDecimalFormatString(ticketDetailResponse.getH_tot_rcvd_amt())));` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 121 | `bundle.putString("AGE_TYPE", sb.toString());` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 122 | `bundle.putString("SEAT_NO", sb2.toString());` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 152 | `this.f30251v.setText(bundleG.getString("AGE_TYPE"));` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 153 | `this.f30252w.setText(bundleG.getString("SEAT_NO"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCActivity.java` | 154 | `this.f30253x.setText(bundleG.getString("AMOUNT"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 99 | `bundle.putString("AMOUNT", TCSActivity.this.getString(j.common_amount, N.getDecimalFormatString(ticketDetailResponse.getH_tot_rcvd_amt())));` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 116 | `bundle.putString("AGE_TYPE", sb.toString());` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 117 | `bundle.putString("SEAT_NO", sb2.toString());` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 169 | `this.f30271v.setText(bundleH.getString("AGE_TYPE"));` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 170 | `this.f30272w.setText(bundleH.getString("SEAT_NO"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/change/TCSActivity.java` | 171 | `this.f30273x.setText(bundleH.getString("AMOUNT"));` |
| `chtnDvCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 691 | `jSONObject.put("chtnDvCd", code);` |
| `chtnTrnOrdrNo` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 692 | `jSONObject.put("chtnTrnOrdrNo", h_chg_trn_seq);` |
| `trnGpCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 694 | `jSONObject.put("trnGpCd", trainInfo.getH_trn_gp_cd());` |
| `trnGpNm` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 695 | `jSONObject.put("trnGpNm", O.getTrainGroupName(trainInfo.getH_trn_gp_cd()));` |
| `stlbTrnClsfCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 696 | `jSONObject.put("stlbTrnClsfCd", trainInfo.getH_trn_clsf_cd());` |
| `stlbTrnClsfNm` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 697 | `jSONObject.put("stlbTrnClsfNm", trainInfo.getH_trn_clsf_nm());` |
| `runDt` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 698 | `jSONObject.put("runDt", trainInfo.getH_run_dt());` |
| `arvDt` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 701 | `jSONObject.put("arvDt", trainInfo.getH_arv_dt());` |
| `arvTm` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 702 | `jSONObject.put("arvTm", trainInfo.getH_arv_tm());` |
| `dptRsStnCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 703 | `jSONObject.put("dptRsStnCd", trainInfo.getH_dpt_rs_stn_cd());` |
| `dptStnConsOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 705 | `jSONObject.put("dptStnConsOrdr", trainInfo.getH_dpt_stn_cons_ordr());` |
| `arvStnConsOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 706 | `jSONObject.put("arvStnConsOrdr", trainInfo.getH_arv_stn_cons_ordr());` |
| `dptStnRunOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 707 | `jSONObject.put("dptStnRunOrdr", trainInfo.getH_dpt_stn_run_ordr());` |
| `arvStnRunOrdr` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 708 | `jSONObject.put("arvStnRunOrdr", trainInfo.getH_arv_stn_run_ordr());` |
| `seatAttCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 709 | `jSONObject.put("seatAttCd", h_seat_att_cd);` |
| `rsvPsbFlg` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 710 | `jSONObject.put("rsvPsbFlg", "13".equals(h_spe_rsv_cd) ? "N" : "Y");` |
| `ticketType` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 711 | `jSONObject.put("ticketType", oVar.getCode().equals(str) ? "spe" : "gen");` |
| `psrmClCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 712 | `jSONObject.put("psrmClCd", str);` |
| `totPrnb` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 713 | `jSONObject.put("totPrnb", String.valueOf(i9));` |
| `goStart` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 714 | `jSONObject.put("goStart", trainInfo.getH_dpt_rs_stn_nm());` |
| `goEnd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 715 | `jSONObject.put("goEnd", trainInfo.getH_arv_rs_stn_nm());` |
| `reserveType` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 740 | `jSONObject.put("reserveType", "reserve");` |
| `mutMrkVrfCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 741 | `jSONObject.put("mutMrkVrfCd", str);` |
| `radJobId` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 742 | `jSONObject.put("radJobId", str2);` |
| `dptRstnCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 743 | `jSONObject.put("dptRstnCd", trainInfo.getH_dpt_rs_stn_cd());` |
| `goStart` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 745 | `jSONObject.put("goStart", rsvInquiryRequest.getTxtGoStart());` |
| `goEnd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 746 | `jSONObject.put("goEnd", rsvInquiryRequest.getTxtGoEnd());` |
| `psgFlg1` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 749 | `jSONObject.put("psgFlg1", rsvInquiryRequest.getTxtPsgFlg_1());` |
| `psgFlg2` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 750 | `jSONObject.put("psgFlg2", rsvInquiryRequest.getTxtPsgFlg_2());` |
| `psgFlg3` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 751 | `jSONObject.put("psgFlg3", rsvInquiryRequest.getTxtPsgFlg_3());` |
| `psgFlg4` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 752 | `jSONObject.put("psgFlg4", rsvInquiryRequest.getTxtPsgFlg_4());` |
| `psgFlg5` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 753 | `jSONObject.put("psgFlg5", rsvInquiryRequest.getTxtPsgFlg_5());` |
| `psgFlg6` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 754 | `jSONObject.put("psgFlg6", "0");` |
| `seatAttCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 755 | `jSONObject.put("seatAttCd", txtSeatAttCd_4);` |
| `trnGpCd` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 756 | `jSONObject.put("trnGpCd", rsvInquiryRequest.getSelGoTrain());` |
| `trainList` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 757 | `jSONObject.put("trainList", jSONArray);` |
| `INDEX` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1610 | `bundle.putInt("INDEX", i11);` |
| `TICKET_KIND` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1611 | `bundle.putInt("TICKET_KIND", 9);` |
| `MAAS_SERVICE_DV_CD` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1612 | `bundle.putString("MAAS_SERVICE_DV_CD", addSrvItem.getAddSrvDvCd());` |
| `MAAS_SERVICE_NAME` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1613 | `bundle.putString("MAAS_SERVICE_NAME", addSrvItem.getAddSrvNm());` |
| `MAAS_RESERVATION_NUM` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1614 | `bundle.putString("MAAS_RESERVATION_NUM", addSrvItem.getAddSrvReqNo());` |
| `MAAS_PNR_NUM` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1615 | `bundle.putString("MAAS_PNR_NUM", addSrvItem.getPnrNo());` |
| `MAAS_MESSAGE_1` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1616 | `bundle.putString("MAAS_MESSAGE_1", addSrvItem.getCgPsRefAtclCont());` |
| `MAAS_SERVICE_DETAIL_URL` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1617 | `bundle.putString("MAAS_SERVICE_DETAIL_URL", addSrvItem.getRsvSpecUrl());` |
| `MAAS_PSB_START_DATE` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1618 | `bundle.putString("MAAS_PSB_START_DATE", addSrvItem.getUtlStDt());` |
| `MAAS_PSB_END_DATE` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1619 | `bundle.putString("MAAS_PSB_END_DATE", addSrvItem.getUtlClsDt());` |
| `MAAS_PSB_START_TIME` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1620 | `bundle.putString("MAAS_PSB_START_TIME", addSrvItem.getDlivPsbStTm());` |
| `MAAS_PSB_END_TIME` | `com/korail/talk/ui/ticket/confirm/TicketListActivity.java` | 1621 | `bundle.putString("MAAS_PSB_END_TIME", addSrvItem.getDlivPsbClsTm());` |
| `IS_EMERGENCY` | `com/korail/talk/ui/ticket/confirm/a.java` | 84 | `this.f30350d0 = getArguments().getBoolean("IS_EMERGENCY", false);` |
| `RETURN_NO` | `com/korail/talk/ui/ticket/confirm/a.java` | 386 | `if (str.equals(((Bundle) parcelableArrayList2.get(i13)).getString("RETURN_NO"))) {` |
| `KEY_PLF_NO` | `com/korail/talk/ui/ticket/confirm/a.java` | 387 | `((Bundle) parcelableArrayList2.get(i13)).putString("KEY_PLF_NO", plfNo);` |
| `_display_name` | `com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java` | 206 | `contentValues.put("_display_name", str);` |
| `mime_type` | `com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java` | 207 | `contentValues.put("mime_type", "image/png");` |
| `relative_path` | `com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java` | 208 | `contentValues.put("relative_path", Environment.DIRECTORY_DOWNLOADS);` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 68 | `bundle.putString("AMOUNT", LimousineReturnActivity.this.getString(j.common_amount, N.getDecimalFormatString(ticketDetailResponse.getH_tot_rcvd_amt())));` |
| `START_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 69 | `bundle.putString("START_STATION_NM", ticket_info.get(0).getH_dpt_rs_stn_nm());` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 70 | `bundle.putString("ARRIVAL_STATION_NM", ticket_info.get(0).getH_arv_rs_stn_nm());` |
| `SEAT_TOTAL_COUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 71 | `bundle.putString("SEAT_TOTAL_COUNT", String.valueOf(ticket_info.get(0).getTk_seat_info().size()));` |
| `START_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 99 | `this.f30536v.setText(bundleG.getString("START_STATION_NM"));` |
| `ARRIVAL_STATION_NM` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 100 | `this.f30537w.setText(bundleG.getString("ARRIVAL_STATION_NM"));` |
| `SEAT_TOTAL_COUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 101 | `this.f30538x.setText(bundleG.getString("SEAT_TOTAL_COUNT"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/LimousineReturnActivity.java` | 102 | `this.f30539y.setText(bundleG.getString("AMOUNT"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 157 | `bundle.putString("AMOUNT", TicketReturnActivity.this.getString(j.common_amount, N.getDecimalFormatString(ticketDetailResponse.getH_tot_rcvd_amt())));` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 174 | `bundle.putString("AGE_TYPE", sb.toString());` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 175 | `bundle.putString("SEAT_NO", sb2.toString());` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 204 | `this.f30554u.setContentDescription(bundleG.getString("AGE_TYPE") + bundleG.getString("SEAT_NO") + bundleG.getString("AMOUNT"));` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 204 | `this.f30554u.setContentDescription(bundleG.getString("AGE_TYPE") + bundleG.getString("SEAT_NO") + bundleG.getString("AMOUNT"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 204 | `this.f30554u.setContentDescription(bundleG.getString("AGE_TYPE") + bundleG.getString("SEAT_NO") + bundleG.getString("AMOUNT"));` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 205 | `this.f30555v.setText(bundleG.getString("AGE_TYPE"));` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 206 | `this.f30555v.setContentDescription(bundleG.getString("AGE_TYPE"));` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 207 | `this.f30556w.setText(bundleG.getString("SEAT_NO"));` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 208 | `this.f30556w.setContentDescription(bundleG.getString("SEAT_NO"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 209 | `this.f30557x.setText(bundleG.getString("AMOUNT"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java` | 210 | `this.f30557x.setContentDescription(bundleG.getString("AMOUNT"));` |
| `INDEX` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 808 | `bundle.putInt("INDEX", i11);` |
| `IS_PURCHASE_HISTORY` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 809 | `bundle.putBoolean("IS_PURCHASE_HISTORY", true);` |
| `TICKET_KIND` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 810 | `bundle.putInt("TICKET_KIND", 9);` |
| `MAAS_SERVICE_DV_CD` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 811 | `bundle.putString("MAAS_SERVICE_DV_CD", addSrvItem.getAddSrvDvCd());` |
| `MAAS_SERVICE_NAME` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 812 | `bundle.putString("MAAS_SERVICE_NAME", addSrvItem.getAddSrvNm());` |
| `MAAS_RESERVATION_NUM` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 813 | `bundle.putString("MAAS_RESERVATION_NUM", addSrvItem.getAddSrvReqNo());` |
| `MAAS_PNR_NUM` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 814 | `bundle.putString("MAAS_PNR_NUM", addSrvItem.getPnrNo());` |
| `MAAS_MESSAGE_1` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 815 | `bundle.putString("MAAS_MESSAGE_1", addSrvItem.getCgPsRefAtclCont());` |
| `MAAS_SERVICE_DETAIL_URL` | `com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java` | 816 | `bundle.putString("MAAS_SERVICE_DETAIL_URL", addSrvItem.getRsvSpecUrl());` |
| `AMOUNT` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 116 | `bundle.putString("AMOUNT", TicketDeliveryListActivity.this.getString(j.common_amount, N.getDecimalFormatString(ticketDetailResponse.getH_tot_rcvd_amt())));` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 133 | `bundle.putString("AGE_TYPE", sb.toString());` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 134 | `bundle.putString("SEAT_NO", sb2.toString());` |
| `AGE_TYPE` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 164 | `this.f30374v.setText(bundleG.getString("AGE_TYPE"));` |
| `SEAT_NO` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 165 | `this.f30375w.setText(bundleG.getString("SEAT_NO"));` |
| `AMOUNT` | `com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java` | 166 | `this.f30376x.setText(bundleG.getString("AMOUNT"));` |
| `STATUS` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 116 | `String string = bundleB.getString("STATUS");` |
| `TITLE` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 118 | `aVar.f29744a.setText(bundleB.getString("TITLE"));` |
| `PAY_PERIOD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 119 | `aVar.f29745b.setText(bundleB.getString("PAY_PERIOD"));` |
| `VR_RSV_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 181 | `bundle2.putString("VR_RSV_NO", bundle.getString("VR_RSV_NO"));` |
| `VR_RSV_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 181 | `bundle2.putString("VR_RSV_NO", bundle.getString("VR_RSV_NO"));` |
| `VR_RSV_SQ_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 182 | `bundle2.putString("VR_RSV_SQ_NO", bundle.getString("VR_RSV_SQ_NO"));` |
| `VR_RSV_SQ_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 182 | `bundle2.putString("VR_RSV_SQ_NO", bundle.getString("VR_RSV_SQ_NO"));` |
| `RSV_STT_CD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 184 | `bundle2.putBoolean("RSV_STT_CD", v0(bundle.getString("RSV_STT_CD")));` |
| `RSV_STT_CD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 184 | `bundle2.putBoolean("RSV_STT_CD", v0(bundle.getString("RSV_STT_CD")));` |
| `WEB_POST_URL` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 207 | `bundle.putString("WEB_POST_URL", g.TOUR_PACKAGE_URL);` |
| `STATUS` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 227 | `if (bundleB.getString("STATUS").contains(getString(j.common_reservation_cancel))) {` |
| `TITLE` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 242 | `bundle.putString("TITLE", reservationProduct.getStrGdNm());` |
| `PAY_PERIOD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 243 | `bundle.putString("PAY_PERIOD", C0808h.convertFormat(reservationProduct.getStrStlDlnDt(), "yyyyMMdd", "yyyy년 MM월 dd일"));` |
| `STATUS` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 244 | `bundle.putString("STATUS", reservationProduct.getStrRsvSttNm());` |
| `RSV_STT_CD` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 245 | `bundle.putString("RSV_STT_CD", reservationProduct.getStrRsvSttCd());` |
| `VR_RSV_NO` | `com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java` | 246 | `bundle.putString("VR_RSV_NO", reservationProduct.getStrVrRsvNo());` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/change/TCBookingActivity.java` | 86 | `this.f28898r.setEnabled(bundle.getInt("TOTAL_PERSON_COUNT") == this.f28892l);` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/change/TCBookingActivity.java` | 179 | `ogTkInquiryRequest.setTkCnt(passengerInfo.getInt("TOTAL_PERSON_COUNT"));` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 633 | `bundle.putInt("ADULT_COUNT", N.intValue(custTripInfo.getAdulCnt(), 1));` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 634 | `bundle.putInt("TEENAGER_COUNT", 0);` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 635 | `bundle.putInt("CHILD_COUNT", N.intValue(custTripInfo.getChilCnt(), 0));` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 636 | `bundle.putInt("CHILD_ACCOMPANY_COUNT", N.intValue(custTripInfo.getBabyAcpnPrnb(), 0));` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 637 | `bundle.putInt("SENIOR_COUNT", N.intValue(custTripInfo.getEdrPrnb(), 0));` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 638 | `bundle.putInt("HIGH_DISABLE_COUNT", N.intValue(custTripInfo.getAdltHdcpPrnb(), 0));` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 639 | `bundle.putInt("LOW_DISABLE_COUNT", N.intValue(custTripInfo.getChldHdcpPrnb(), 0));` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 706 | `bundle.putBoolean("IS_DIRECT_SHOW_MULTI_LANGUAGE", true);` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 714 | `bundle2.putBoolean("IS_DIRECT_SHOW_MULTI_LANGUAGE", true);` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 795 | `bundle.putBoolean("IS_DIRECT", true);` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 826 | `bundle.putInt("ADULT_COUNT", N.intValue(custTripInfo.getAdulCnt(), 1));` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 827 | `bundle.putInt("GUIDE_DOG_COUNT", 0);` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 828 | `bundle.putInt("TEENAGER_COUNT", 0);` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 829 | `bundle.putInt("CHILD_COUNT", N.intValue(custTripInfo.getChilCnt(), 0));` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 830 | `bundle.putInt("CHILD_ACCOMPANY_COUNT", N.intValue(custTripInfo.getBabyAcpnPrnb(), 0));` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 831 | `bundle.putInt("SENIOR_COUNT", N.intValue(custTripInfo.getEdrPrnb(), 0));` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 832 | `bundle.putInt("HIGH_DISABLE_COUNT", N.intValue(custTripInfo.getAdltHdcpPrnb(), 0));` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 833 | `bundle.putInt("LOW_DISABLE_COUNT", N.intValue(custTripInfo.getChldHdcpPrnb(), 0));` |
| `WEB_POST_URL` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 975 | `bundle.putString("WEB_POST_URL", K4.g.CONVENIENCE_SETTING_URL);` |
| `IS_CLOSE_VIEW` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 976 | `bundle.putBoolean("IS_CLOSE_VIEW", true);` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1011 | `String code = (bundle.getBoolean("IS_DIRECT", false) ? K4.d.DIRECT_SQ_NO : K4.d.TRANSFER_SQ_NO).getCode();` |
| `ROUTE_DATE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1012 | `CalendarData calendarInfo = bundle.containsKey("ROUTE_DATE") ? C0808h.getCalendarInfo(C0808h.getCalendarFromString(bundle.getString("ROUTE_DATE"), "yyyyMMddHHmmss")) : null;` |
| `SEAT_OPTION_INDEX` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1013 | `int i9 = bundle.getInt("SEAT_OPTION_INDEX", 0);` |
| `SEAT_OPTION_CODE` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1014 | `String string = bundle.getString("SEAT_OPTION_CODE", p.DEFAULT.getCode());` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1024 | `String string2 = bundle.getString("TRANSFER_CHTNRSSTNCD");` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1025 | `String string3 = bundle.getString("TRANSFER_TRNGPCD");` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1026 | `boolean z9 = bundle.getBoolean("IS_SELECT_TRANSFER");` |
| `srtDep` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1124 | `String string = extras.getString("srtDep");` |
| `srtArv` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1125 | `String string2 = extras.getString("srtArv");` |
| `srtDt` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1126 | `String string3 = extras.getString("srtDt");` |
| `srtTm` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1127 | `String string4 = extras.getString("srtTm");` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1250 | `this.f29023B.getInt("TOTAL_PERSON_COUNT");` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1252 | `int i11 = this.f29023B.getInt("ADULT_COUNT");` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1253 | `int i12 = this.f29023B.getInt("TEENAGER_COUNT");` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1254 | `int i13 = this.f29023B.getInt("CHILD_COUNT");` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1255 | `int i14 = this.f29023B.getInt("CHILD_ACCOMPANY_COUNT");` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1256 | `int i15 = this.f29023B.getInt("SENIOR_COUNT");` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1257 | `int i16 = this.f29023B.getInt("HIGH_DISABLE_COUNT");` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1258 | `int i17 = this.f29023B.getInt("LOW_DISABLE_COUNT");` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1259 | `int i18 = this.f29023B.getInt("GUIDE_DOG_COUNT");` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1529 | `bundle.putInt("ADULT_COUNT", 1);` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1530 | `bundle.putInt("TEENAGER_COUNT", 0);` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1531 | `bundle.putInt("CHILD_COUNT", 0);` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1532 | `bundle.putInt("CHILD_ACCOMPANY_COUNT", 0);` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1533 | `bundle.putInt("SENIOR_COUNT", 0);` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1534 | `bundle.putInt("HIGH_DISABLE_COUNT", 0);` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1535 | `bundle.putInt("LOW_DISABLE_COUNT", 0);` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1536 | `bundle.putInt("GUIDE_DOG_COUNT", 0);` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java` | 1537 | `bundle.putInt("TOTAL_PERSON_COUNT", 1);` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 266 | `bundle.putInt("ADULT_COUNT", N.intValue(custTripInfo.getAdulCnt(), 1));` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 267 | `bundle.putInt("TEENAGER_COUNT", 0);` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 268 | `bundle.putInt("CHILD_COUNT", N.intValue(custTripInfo.getChilCnt(), 0));` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 269 | `bundle.putInt("CHILD_ACCOMPANY_COUNT", N.intValue(custTripInfo.getBabyAcpnPrnb(), 0));` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 270 | `bundle.putInt("SENIOR_COUNT", N.intValue(custTripInfo.getEdrPrnb(), 0));` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 271 | `bundle.putInt("HIGH_DISABLE_COUNT", N.intValue(custTripInfo.getAdltHdcpPrnb(), 0));` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 272 | `bundle.putInt("LOW_DISABLE_COUNT", N.intValue(custTripInfo.getChldHdcpPrnb(), 0));` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 286 | `bundle.putBoolean("IS_DIRECT_SHOW_MULTI_LANGUAGE", true);` |
| `IS_DIRECT_SHOW_MULTI_LANGUAGE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 294 | `bundle2.putBoolean("IS_DIRECT_SHOW_MULTI_LANGUAGE", true);` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 382 | `bundle.putBoolean("IS_DIRECT", true);` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 405 | `bundle.putInt("ADULT_COUNT", N.intValue(custTripInfo.getAdulCnt(), 1));` |
| `GUIDE_DOG_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 406 | `bundle.putInt("GUIDE_DOG_COUNT", 0);` |
| `TEENAGER_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 407 | `bundle.putInt("TEENAGER_COUNT", 0);` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 408 | `bundle.putInt("CHILD_COUNT", N.intValue(custTripInfo.getChilCnt(), 0));` |
| `CHILD_ACCOMPANY_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 409 | `bundle.putInt("CHILD_ACCOMPANY_COUNT", N.intValue(custTripInfo.getBabyAcpnPrnb(), 0));` |
| `SENIOR_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 410 | `bundle.putInt("SENIOR_COUNT", N.intValue(custTripInfo.getEdrPrnb(), 0));` |
| `HIGH_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 411 | `bundle.putInt("HIGH_DISABLE_COUNT", N.intValue(custTripInfo.getAdltHdcpPrnb(), 0));` |
| `LOW_DISABLE_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 412 | `bundle.putInt("LOW_DISABLE_COUNT", N.intValue(custTripInfo.getChldHdcpPrnb(), 0));` |
| `WEB_POST_URL` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 494 | `bundle.putString("WEB_POST_URL", K4.g.CONVENIENCE_SETTING_URL);` |
| `IS_CLOSE_VIEW` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 495 | `bundle.putBoolean("IS_CLOSE_VIEW", true);` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 520 | `String code = (bundle.getBoolean("IS_DIRECT", false) ? K4.d.DIRECT_SQ_NO : K4.d.TRANSFER_SQ_NO).getCode();` |
| `ROUTE_DATE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 521 | `CalendarData calendarInfo = bundle.containsKey("ROUTE_DATE") ? C0808h.getCalendarInfo(C0808h.getCalendarFromString(bundle.getString("ROUTE_DATE"), "yyyyMMddHHmmss")) : null;` |
| `SEAT_OPTION_INDEX` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 522 | `int i9 = bundle.getInt("SEAT_OPTION_INDEX", 0);` |
| `SEAT_OPTION_CODE` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 523 | `String string = bundle.getString("SEAT_OPTION_CODE", p.DEFAULT.getCode());` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java` | 1023 | `this.f29105z.setEnabled(bundle.getInt("TOTAL_PERSON_COUNT") > 0);` |
| `h_cmpa_cnt` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 553 | `map.put("h_cmpa_cnt", String.valueOf(companionData.size()));` |
| `h_cmpa_nm_` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 556 | `map.put("h_cmpa_nm_" + i9, viewOnClickListenerC5954a.getCompanionName());` |
| `h_cmpa_btdt_` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 557 | `map.put("h_cmpa_btdt_" + i9, viewOnClickListenerC5954a.getCompanionBirthDate());` |
| `h_cmpa_sex_dv_cd_` | `com/korail/talk/ui/booking/discountBooking/pass/NewAPassBookingActivity.java` | 558 | `map.put("h_cmpa_sex_dv_cd_" + i9, viewOnClickListenerC5954a.getGender());` |
| `ADULT_COUNT` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 95 | `int i9 = passengerInfo.getInt("ADULT_COUNT");` |
| `CHILD_COUNT` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 96 | `int i10 = passengerInfo.getInt("CHILD_COUNT");` |
| `h_cmpa_cnt` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 365 | `map.put("h_cmpa_cnt", String.valueOf(companionData.size()));` |
| `h_cmpa_nm_` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 368 | `map.put("h_cmpa_nm_" + i9, viewOnClickListenerC5954a.getCompanionName());` |
| `h_cmpa_btdt_` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 369 | `map.put("h_cmpa_btdt_" + i9, viewOnClickListenerC5954a.getCompanionBirthDate());` |
| `h_cmpa_sex_dv_cd_` | `com/korail/talk/ui/booking/discountBooking/pass/GangneungPassBookingActivity.java` | 370 | `map.put("h_cmpa_sex_dv_cd_" + i9, viewOnClickListenerC5954a.getGender());` |
| `h_cmpa_cnt` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 547 | `map.put("h_cmpa_cnt", String.valueOf(companionData.size()));` |
| `h_cmpa_nm_` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 550 | `map.put("h_cmpa_nm_" + i9, viewOnClickListenerC5954a.getCompanionName());` |
| `h_cmpa_btdt_` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 551 | `map.put("h_cmpa_btdt_" + i9, viewOnClickListenerC5954a.getCompanionBirthDate());` |
| `h_cmpa_sex_dv_cd_` | `com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java` | 552 | `map.put("h_cmpa_sex_dv_cd_" + i9, viewOnClickListenerC5954a.getGender());` |
| `CMTR_KND_CD` | `com/korail/talk/ui/booking/discountBooking/commutation/a.java` | 139 | `cmtrKndMenuRequest.setCmtrKndCd(jSONObject.getString("CMTR_KND_CD"));` |
| `FST_DPT_RS_STN_CD` | `com/korail/talk/ui/booking/discountBooking/commutation/a.java` | 439 | `this.f28912r.setStationNm(J4.b.getInstance().getStationNameByCode(jSONObject.getString("FST_DPT_RS_STN_CD")), J4.b.getInstance().getStationNameByCode(jSONObject.getString("LAST_ARV_RS_STN_CD")));` |
| `LAST_ARV_RS_STN_CD` | `com/korail/talk/ui/booking/discountBooking/commutation/a.java` | 439 | `this.f28912r.setStationNm(J4.b.getInstance().getStationNameByCode(jSONObject.getString("FST_DPT_RS_STN_CD")), J4.b.getInstance().getStationNameByCode(jSONObject.getString("LAST_ARV_RS_STN_CD")));` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 55 | `this.f28924p.setEnabled(bundle.getInt("TOTAL_PERSON_COUNT") > 0);` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 181 | `String string = bundle.getString("TRANSFER_CHTNRSSTNCD");` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 182 | `String string2 = bundle.getString("TRANSFER_TRNGPCD");` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountTourTrainBookingActivity.java` | 183 | `boolean z9 = bundle.getBoolean("IS_SELECT_TRANSFER");` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 57 | `this.f28924p.setEnabled(bundle.getInt("TOTAL_PERSON_COUNT") == 4);` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 167 | `String string = bundle.getString("TRANSFER_CHTNRSSTNCD");` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 168 | `String string2 = bundle.getString("TRANSFER_TRNGPCD");` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/discountBooking/goods/FamilyBookingActivity.java` | 169 | `boolean z9 = bundle.getBoolean("IS_SELECT_TRANSFER");` |
| `IS_DIRECT` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountBookingActivity.java` | 127 | `String code = (bundle.getBoolean("IS_DIRECT", false) ? d.DIRECT_SQ_NO : d.TRANSFER_SQ_NO).getCode();` |
| `ROUTE_DATE` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountBookingActivity.java` | 128 | `CalendarData calendarInfo = bundle.containsKey("ROUTE_DATE") ? C0808h.getCalendarInfo(C0808h.getCalendarFromString(bundle.getString("ROUTE_DATE"), "yyyyMMddHHmmss")) : null;` |
| `TOTAL_PERSON_COUNT` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 73 | `this.f28924p.setEnabled(bundle.getInt("TOTAL_PERSON_COUNT") > 0);` |
| `TRANSFER_CHTNRSSTNCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 180 | `String string = bundle.getString("TRANSFER_CHTNRSSTNCD");` |
| `TRANSFER_TRNGPCD` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 181 | `String string2 = bundle.getString("TRANSFER_TRNGPCD");` |
| `IS_SELECT_TRANSFER` | `com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java` | 182 | `boolean z9 = bundle.getBoolean("IS_SELECT_TRANSFER");` |
| `chtnDvCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 48 | `jSONObject.put("chtnDvCd", code);` |
| `chtnTrnOrdrNo` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 49 | `jSONObject.put("chtnTrnOrdrNo", h_chg_trn_seq);` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 51 | `jSONObject.put("trnGpCd", trainInfo.getH_trn_gp_cd());` |
| `trnGpNm` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 52 | `jSONObject.put("trnGpNm", O.getTrainGroupName(trainInfo.getH_trn_gp_cd()));` |
| `stlbTrnClsfCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 53 | `jSONObject.put("stlbTrnClsfCd", trainInfo.getH_trn_clsf_cd());` |
| `stlbTrnClsfNm` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 54 | `jSONObject.put("stlbTrnClsfNm", trainInfo.getH_trn_clsf_nm());` |
| `runDt` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 55 | `jSONObject.put("runDt", trainInfo.getH_run_dt());` |
| `arvDt` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 58 | `jSONObject.put("arvDt", trainInfo.getH_arv_dt());` |
| `arvTm` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 59 | `jSONObject.put("arvTm", trainInfo.getH_arv_tm());` |
| `dptRsStnCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 60 | `jSONObject.put("dptRsStnCd", trainInfo.getH_dpt_rs_stn_cd());` |
| `dptStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 62 | `jSONObject.put("dptStnConsOrdr", trainInfo.getH_dpt_stn_cons_ordr());` |
| `arvStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 63 | `jSONObject.put("arvStnConsOrdr", trainInfo.getH_arv_stn_cons_ordr());` |
| `dptStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 64 | `jSONObject.put("dptStnRunOrdr", trainInfo.getH_dpt_stn_run_ordr());` |
| `arvStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 65 | `jSONObject.put("arvStnRunOrdr", trainInfo.getH_arv_stn_run_ordr());` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 66 | `jSONObject.put("seatAttCd", h_seat_att_cd);` |
| `rsvPsbFlg` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 67 | `jSONObject.put("rsvPsbFlg", "13".equals(h_spe_rsv_cd) ? "N" : "Y");` |
| `ticketType` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 68 | `jSONObject.put("ticketType", oVar.getCode().equals(str) ? "spe" : "gen");` |
| `psrmClCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 69 | `jSONObject.put("psrmClCd", str);` |
| `totPrnb` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 70 | `jSONObject.put("totPrnb", String.valueOf(i9));` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 71 | `jSONObject.put("goStart", trainInfo.getH_dpt_rs_stn_nm());` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 72 | `jSONObject.put("goEnd", trainInfo.getH_arv_rs_stn_nm());` |
| `reserveType` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 88 | `jSONObject.put("reserveType", "reserve");` |
| `mutMrkVrfCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 89 | `jSONObject.put("mutMrkVrfCd", str);` |
| `radJobId` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 90 | `jSONObject.put("radJobId", str2);` |
| `dptRsStnCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 91 | `jSONObject.put("dptRsStnCd", trainInfo.getH_dpt_rs_stn_cd());` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 93 | `jSONObject.put("goStart", rsvInquiryRequest.getTxtGoStart());` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 94 | `jSONObject.put("goEnd", rsvInquiryRequest.getTxtGoEnd());` |
| `psgFlg1` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 97 | `jSONObject.put("psgFlg1", rsvInquiryRequest.getTxtPsgFlg_1());` |
| `psgFlg2` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 98 | `jSONObject.put("psgFlg2", rsvInquiryRequest.getTxtPsgFlg_2());` |
| `psgFlg3` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 99 | `jSONObject.put("psgFlg3", rsvInquiryRequest.getTxtPsgFlg_3());` |
| `psgFlg4` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 100 | `jSONObject.put("psgFlg4", rsvInquiryRequest.getTxtPsgFlg_4());` |
| `psgFlg5` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 101 | `jSONObject.put("psgFlg5", rsvInquiryRequest.getTxtPsgFlg_5());` |
| `psgFlg6` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 102 | `jSONObject.put("psgFlg6", "0");` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 103 | `jSONObject.put("seatAttCd", txtSeatAttCd_4);` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 104 | `jSONObject.put("trnGpCd", "300");` |
| `trainList` | `com/korail/talk/ui/inquiry/rir/orr/TransferInquiryActivity.java` | 105 | `jSONObject.put("trainList", jSONArray);` |
| `reserveType` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 171 | `jSONObject.put("reserveType", z9 ? "seatmap" : "reserve");` |
| `mutMrkVrfCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 172 | `jSONObject.put("mutMrkVrfCd", str);` |
| `radJobId` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 173 | `jSONObject.put("radJobId", K4.d.DIRECT_SQ_NO.getCode());` |
| `dptRstnCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 174 | `jSONObject.put("dptRstnCd", bundle.getString(z5.e.KEY_TRAIN_DEPARTURE_CD));` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 176 | `jSONObject.put("goStart", this.f837Z.getTxtGoStart());` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 177 | `jSONObject.put("goEnd", this.f837Z.getTxtGoEnd());` |
| `psgFlg1` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 180 | `jSONObject.put("psgFlg1", this.f837Z.getTxtPsgFlg_1());` |
| `psgFlg2` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 181 | `jSONObject.put("psgFlg2", this.f837Z.getTxtPsgFlg_2());` |
| `psgFlg3` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 182 | `jSONObject.put("psgFlg3", this.f837Z.getTxtPsgFlg_3());` |
| `psgFlg4` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 183 | `jSONObject.put("psgFlg4", this.f837Z.getTxtPsgFlg_4());` |
| `psgFlg5` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 184 | `jSONObject.put("psgFlg5", this.f837Z.getTxtPsgFlg_5());` |
| `psgFlg6` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 185 | `jSONObject.put("psgFlg6", "0");` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 186 | `jSONObject.put("seatAttCd", str3);` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 187 | `jSONObject.put("trnGpCd", this.f837Z.getSelGoTrain());` |
| `trainList` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 188 | `jSONObject.put("trainList", jSONArray);` |
| `chtnDvCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 199 | `jSONObject.put("chtnDvCd", h_chg_trn_dv_cd);` |
| `chtnTrnOrdrNo` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 200 | `jSONObject.put("chtnTrnOrdrNo", h_chg_trn_seq);` |
| `trnGpCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 202 | `jSONObject.put("trnGpCd", trainInfo.getH_trn_gp_cd());` |
| `trnGpNm` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 203 | `jSONObject.put("trnGpNm", O.getTrainGroupName(trainInfo.getH_trn_gp_cd()));` |
| `stlbTrnClsfCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 204 | `jSONObject.put("stlbTrnClsfCd", trainInfo.getH_trn_clsf_cd());` |
| `stlbTrnClsfNm` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 205 | `jSONObject.put("stlbTrnClsfNm", trainInfo.getH_trn_clsf_nm());` |
| `runDt` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 206 | `jSONObject.put("runDt", trainInfo.getH_run_dt());` |
| `arvDt` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 209 | `jSONObject.put("arvDt", trainInfo.getH_arv_dt());` |
| `arvTm` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 210 | `jSONObject.put("arvTm", trainInfo.getH_arv_tm());` |
| `dptRsStnCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 211 | `jSONObject.put("dptRsStnCd", trainInfo.getH_dpt_rs_stn_cd());` |
| `dptStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 213 | `jSONObject.put("dptStnConsOrdr", trainInfo.getH_dpt_stn_cons_ordr());` |
| `arvStnConsOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 214 | `jSONObject.put("arvStnConsOrdr", trainInfo.getH_arv_stn_cons_ordr());` |
| `dptStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 215 | `jSONObject.put("dptStnRunOrdr", trainInfo.getH_dpt_stn_run_ordr());` |
| `arvStnRunOrdr` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 216 | `jSONObject.put("arvStnRunOrdr", trainInfo.getH_arv_stn_run_ordr());` |
| `seatAttCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 217 | `jSONObject.put("seatAttCd", h_seat_att_cd);` |
| `rsvPsbFlg` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 218 | `jSONObject.put("rsvPsbFlg", "13".equals(h_spe_rsv_cd) ? "N" : "Y");` |
| `ticketType` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 219 | `jSONObject.put("ticketType", oVar.getCode().equals(str) ? "spe" : "gen");` |
| `psrmClCd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 220 | `jSONObject.put("psrmClCd", str);` |
| `totPrnb` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 221 | `jSONObject.put("totPrnb", String.valueOf(i9));` |
| `goStart` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 222 | `jSONObject.put("goStart", trainInfo.getH_dpt_rs_stn_nm());` |
| `goEnd` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 223 | `jSONObject.put("goEnd", trainInfo.getH_arv_rs_stn_nm());` |
| `arvTm_` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 486 | `if (N.isNotNull(oJrny.get("arvTm_" + code))) {` |
| `arvTm_` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 488 | `sb2.append(C0808h.convertFormat(oJrny.get("arvTm_" + code), "HHmmss", "HH:mm"));` |
| `txtPsrmClCd1` | `com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java` | 604 | `oSeat.setPsrmClCd(i10, reservationRequest.getOSeat().get("txtPsrmClCd1"));` |