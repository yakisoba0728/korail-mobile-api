# 15. 로컬 저장소, DB, Preferences, Crypto 분석

## 분석 범위와 전제

- 대상 APK: `korail.apk`
- 분석 방식: 로컬 정적 분석. JADX로 `/tmp/korail-jadx`에 디컴파일한 Java 소스를 기준으로 확인했다.
- 범위: ORMLite DB helper/model, `SharedPreferences` 키와 사용처, 로컬 AES helper, 저장 승차권/카드/역/로그인 데이터, 사용자 식별자, 캐시 삭제 및 마이그레이션.
- 한계: 실제 단말의 `/data/data/com.korail.talk/` 파일 권한, 백업 정책, 런타임 DB 내용은 실행 분석을 하지 않아 확인하지 않았다.

## 저장소 구성 요약

| 영역 | 구현 | 저장 위치/이름 | 핵심 내용 |
|---|---|---|---|
| SQLite/ORMLite | `J4.a extends OrmLiteSqliteOpenHelper` | DB 파일명 `korailtalk.sqlite`, schema version `15` | 역 데이터, 즐겨찾기 구간, 즐겨찾기 카드, 비상승차권/상세 캐시, 최근 구간, 메인 팝업, 다시 보지 않기, 보호자 SMS 번호 |
| DB facade | `J4.b` singleton | `J4.b.init(context)` 후 `getInstance()` | 각 테이블의 CRUD, 최근 구간 2개 제한, 일부 캐시 삭제 |
| Preferences | `S4.H` | `PreferenceManager.getDefaultSharedPreferences(context)` | 로그인 저장값, common-code JSON 캐시, UI/설정 플래그 |
| 로컬 암호화 | `F4.a` | 저장값 자체를 Base64(AES ciphertext) 문자열로 보관 | Android ID 기반 AES/ECB/PKCS5Padding |
| 서버 전송 암호화 | `S4.C0812l`, `BaseActivity.L()`, `K5.b.E0()` | 로컬 저장이 아니라 로그인/금액 등 API 요청값 생성 | common-code의 `LOGIN_DATA.key`, `pwdAESCphd`에 따라 AES/CBC 후 Base64 또는 단순 Base64 |

## ORMLite DB Helper

`J4.a`는 `OrmLiteSqliteOpenHelper`이며 생성자에서 `super(context, "korailtalk.sqlite", null, 15)`를 호출한다. `onCreate()`는 `TableUtils.createTableIfNotExists()`로 9개 모델 테이블을 만든다.

| 항목 | 내용 |
|---|---|
| DB helper | `J4.a` |
| DB 파일명 | `korailtalk.sqlite` |
| schema version | `15` |
| 모델 등록 | `StationData`, `FavoriteStation`, `CreditCard`, `IssueList`, `TicketDetail`, `ZRecentStation`, `MainPopupData`, `DoNotLookAgain`, `SMSData` |
| 테이블명 | 모델에 `@DatabaseTable(tableName=...)`가 없으므로 ORMLite 기본 테이블명 규칙을 따른다. 필드명은 Java field명이 기본 column명으로 쓰인다. |
| DAO 캐시 | helper 내부에 각 모델 DAO를 lazy-init하고 `close()`에서 null 처리한다. |

### 생성 및 업그레이드

| 흐름 | 동작 | 데이터 영향 |
|---|---|---|
| 최초 생성 | 모든 현재 모델 테이블을 `createTableIfNotExists`로 생성 | 기존 데이터 없음 |
| 업그레이드 | `oldVersion != newVersion`이면 `StationData`, `MainPopupData`, `DoNotLookAgain` 드롭 | 역/팝업/다시 보지 않기 상태는 업그레이드 시 삭제 |
| 카드 마이그레이션 | `com.korail.talk.database.model.old.CreditCard`를 읽어 현재 `CreditCard`로 복사 | 기존 카드의 `id`, nickname, number, month, year를 유지하고 `cardType`은 `"0"`으로 채움 |
| old 카드 삭제 | old `CreditCard` 테이블 드롭 후 `onCreate()` 재호출 | 현재 스키마 테이블 재생성 |
| 주의 | `businessNum`은 old 모델에 없어 마이그레이션 대상이 아니다 | 법인카드 사업자번호는 old 데이터에서 복원 불가 |

## DB 모델과 필드

모든 모델 필드는 명시적 columnName 없이 `@DatabaseField`를 사용한다.

| 모델 | 주요 용도 | 필드 |
|---|---|---|
| `CreditCard` | 즐겨찾기 결제 카드 | `id` generatedId, `cardNickname`, `cardNumber`, `cardValidateMonth`, `cardValidateYear`, `cardType`, `businessNum` |
| `old.CreditCard` | schema upgrade용 이전 카드 모델 | `id` generatedId, `cardNickname`, `cardNumber`, `cardValidateMonth`, `cardValidateYear` |
| `FavoriteStation` | 즐겨찾기 구간 | `id` generatedId, `startStation`, `startStationCode`, `arrivalStation`, `arrivalStationCode` |
| `ZRecentStation` | 최근 검색/예약 구간 | `id` generatedId, `startStation`, `startStationCode`, `arrivalStation`, `arrivalStationCode`, `timestamp` |
| `StationData` | 역 마스터/팝업 메타데이터 | `id` id, `stnCd`, `stnNm`, `longitude`, `latitude`, `group`, `major`, `popupType`, `popupMessage`, `popupLinkTitle`, `popupLinkUrl`, `doNotLookADay`, `doNotLookAgain` |
| `TicketDetail` | 비상/오프라인 승차권 상세 캐시 | `id` generatedId, `pnrNo`, `ticketDetail` |
| `IssueList` | 비상/오프라인 승차권 목록 캐시 | `id` generatedId, `issueList` |
| `SMSData` | 보호자 안심 SMS 수신번호 캐시 | `pnrNo` id, `phoneNumber` |
| `MainPopupData` | 메인 팝업 캐시 | `id` generatedId, `noticeId`, `isShow`, `title`, `message`, `linkUrl`, `linkTitle`, `isExternalBrowser`, `confirmDate`, `imageUrl`, `buttonType`, `checkType`, `size`, `clsBtn`, `voice` |
| `DoNotLookAgain` | 로그인 후 팝업 "다시 보지 않기" | `custMgNo` id+uniqueCombo, `doNotLookAgainType` uniqueCombo, `confirmDate` |

## DB Read/Write Call Sites

### 역 데이터와 역 팝업

| 작업 | 호출부 | 저장/조회 값 |
|---|---|---|
| 역 정보 버전 확인 | `IntroActivity.x0()` | `StationInfoResponse.map_version`, station count, DB row count를 비교하고 `MAP_VERSION` prefs 갱신 |
| 역 데이터 전체 갱신 | `IntroActivity.d.a()` | 기존 `StationData` 전체 삭제 후 서버 `StationDataDao.STN` 목록을 DB에 삽입 |
| 역 목록 조회 | `StationSearch.getDBStationList()` | `J4.b.getAllStationList()` |
| 역명/코드 조회 | `J4.b.getStationDataByCode()`, `getStationDataByName()` | `stnCd`, `stnNm` 조건 조회 |
| 역 팝업 suppress | `MainBookingActivity.q1()` | 체크박스 선택 시 `StationData.doNotLookADay=today` 또는 `doNotLookAgain=true` 후 update |

`StationData`는 역명, 역코드, 위경도, 그룹, 주요역 여부, 팝업 문구/링크를 평문 DB 필드로 저장한다. `doNotLookADay`는 일회성 suppress 날짜(`yyyyMMdd`)로 보이며, `doNotLookAgain`은 영구 suppress boolean으로 쓰인다.

### 즐겨찾기 구간과 최근 구간

| 작업 | 호출부 | 저장/조회 값 |
|---|---|---|
| 즐겨찾기 구간 중복 검사 | `favoriteSections.a.C0()` | `FavoriteStation.startStation`, `arrivalStation` |
| 즐겨찾기 구간 저장/수정 | `favoriteSections.a` | 출발/도착 역명 저장. 코드 필드는 모델에 있으나 해당 저장 흐름에서는 설정하지 않는다. |
| 즐겨찾기 구간 삭제 | `favoriteSections.b` | row `id`로 delete |
| 즐겨찾기 구간 조회 | `favoriteSections.b.B0/C0()`, `StationSearch.getFavoriteStationList()` | 최신순 reverse 후 UI 표시 |
| 최근 구간 저장 | `MainBookingActivity.C1()` | 같은 출발/도착 조합을 먼저 삭제하고 새 `ZRecentStation(timestamp=now)` 삽입 |
| 최근 구간 제한 | `J4.b.a()` | `timestamp desc` 조회 결과가 2개를 넘으면 3번째 이후 삭제 |
| 최근 구간 조회 | `StationSearch.getRecentStationList()` | `timestamp desc` 정렬 조회 |

즐겨찾기/최근 구간은 역명만 사용하는 흐름이 확인된다. 모델에는 역코드 필드가 있지만 대표 저장 호출부에서는 채우지 않는다.

### 즐겨찾기 카드

| 작업 | 호출부 | 저장/조회 값 |
|---|---|---|
| 카드 저장 | `favoriteCards.a.M0()` | nickname, 카드번호 전체, 유효월/년, 카드유형, 법인카드 사업자번호를 `F4.a.encryptAES()` 후 저장 |
| 카드 수정 | `favoriteCards.a.M0()` | 기존 `cardId`를 설정하고 `updateCreditCard()` |
| 중복 검사 | `favoriteCards.a.M0()` | 암호화된 nickname/cardNumber 문자열끼리 비교 |
| 카드 목록 조회 | `favoriteCards.b.A0()` | `H4.a.getCreditCardList()`로 복호화 가능한 row만 필터링 후 각 필드를 `F4.a.decryptAES()` |
| 카드 삭제 | `favoriteCards.b` | row `cardId`로 delete |
| migration | `J4.a.onUpgrade()` | old 카드 모델에서 현재 모델로 복사하고 `cardType="0"` 설정 |

카드 저장값은 로컬 AES로 암호화된다. 단, AES/ECB이고 키가 Android ID에서 파생되므로 동일 평문은 동일 ciphertext가 된다. 이 특성 때문에 저장 코드가 암호문 직접 비교로 중복 검사를 할 수 있다.

### 비상/오프라인 승차권 캐시

| 작업 | 호출부 | 저장/조회 값 |
|---|---|---|
| 승차권 목록 refresh 시작 | `TicketListActivity.onReceive(dao_ticket_list)` | `IssueList`, `TicketDetail` 전체 삭제 |
| 목록 캐시 저장 | `TicketListActivity.onReceive(dao_ticket_list)` | 로그인 상태이고 `KEY_LOGIN_ID` 복호화가 가능하면 `TicketListResponse` JSON을 AES 암호화해 `IssueList.issueList` 저장 |
| 상세 캐시 저장 | `TicketListActivity.A1()` | `TicketDetailResponse` 리스트 JSON을 AES 암호화해 `TicketDetail.ticketDetail` 저장. `pnrNo`는 첫 상세의 `h_pnr_no` |
| 목록 캐시 복호화 | `H4.a.decryptIssueListData()` | `IssueList.issueList` 복호화 후 `TicketListResponse`로 JSON parse |
| 상세 캐시 복호화 | `H4.a.decryptIssueDetailListData()` | `pnrNo`로 `TicketDetail` 조회, 복호화 후 `TicketDetailResponse[]` parse |
| 오프라인/캐시 목록 표시 | `TicketListActivity.setList()` | `decryptIssueListData()`, `decryptIssueDetailListData()` 결과로 UI 구성 |

`IssueList`와 `TicketDetail`은 민감한 승차권 정보를 포함한다. DB field는 문자열 하나지만 내부는 API response JSON 전체이며, PNR, 반환 비밀번호, 판매일/창구번호/일련번호, 여정/좌석 정보 등이 포함될 수 있다.

### 보호자 안심 SMS 번호

| 작업 | 호출부 | 저장/조회 값 |
|---|---|---|
| 기존 번호 조회 | `TicketListActivity.moveToGuardianReliefSMS()` | `SMSData(pnrNo)`로 조회 |
| 기존 번호 사용 | `TicketListActivity.moveToGuardianReliefSMS()` | `SMSData.phoneNumber`를 AES 복호화해 `GuardianReliefSmsRequest.rcvPsHndyTeln`에 설정 |
| 새 번호 저장 | `GuardianReliefSmsActivity.onReceive()` | SMS API 성공 후 입력 전화번호를 AES 암호화해 `SMSData.phoneNumber` 저장 |
| stale 번호 삭제 | `TicketListActivity.onReceive(dao_ticket_detail)` | 현재 승차권 PNR 목록에 없는 `SMSData` row 삭제 |

### 메인 팝업과 로그인 팝업 Suppress

| 작업 | 호출부 | 저장/조회 값 |
|---|---|---|
| 메인 팝업 저장 | `IntroActivity.onReceive(dao_common_code)` | common-code의 `MainPopup`을 `MainPopupData`로 저장 |
| 메인 팝업 삭제 | `IntroActivity.onReceive(dao_common_code)` | show=`N`이거나 noticeId/confirmDate 조건 불일치 시 삭제 후 재삽입 |
| 로그인 팝업 suppress 조회 | `C0811k.showLoginDialog()` | `DoNotLookAgain(custMgNo, doNotLookAgainType)` 조회 |
| 로그인 팝업 suppress 저장 | `C0811k.c()` | 체크박스 선택 시 `confirmDate = today + 7일` 저장/update |

`DoNotLookAgain`은 고객관리번호(`custMgNo`)와 팝업 유형을 조합해 suppress를 관리한다. 해당 DB 값은 암호화되지 않는다.

## SharedPreferences Helper

`S4.H`는 Android default shared preferences만 사용한다. 모든 write는 `commit()` 동기 저장이다. `remove()`나 `clear()` wrapper는 보이지 않는다.

| 메서드 | 동작 |
|---|---|
| `getString(context, key)` | default `""` |
| `getString(context, key, default)` | 지정 default |
| `putString(context, key, value)` | null이면 `""`로 치환 후 commit |
| `getBoolean/putBoolean` | default false 또는 지정 default |
| `getInt/putInt` | default 0 또는 지정 default |
| `getIntList/putIntList` | JSON array 문자열로 정수 리스트 저장 |

## 주요 Preferences 키

### 로그인/사용자 식별자

| 키 | 타입 | 저장값 | 암호화 | 주요 write | 주요 read |
|---|---|---|---|---|---|
| `KEY_LOGIN_TYPE` | String | 로그인 유형. 전화/이메일/회원번호/간편로그인 구분 (`"2"`, `"K"`, `"N"`, Google, Onepass 등) | 없음 | `K5.b.onReceive()` | 로그인 탭 선택, 자동로그인, 마이페이지 간편로그인 해제 판단 |
| `KEY_MEMBER_NUM` | Boolean | ID 저장 체크 여부 | 없음 | `K5.b.onReceive()` | 로그인 화면 ID 자동 채움, `DataActivity` export |
| `KEY_AUTO_LOGIN` | Boolean | 자동로그인 여부 | 없음 | `K5.b.onReceive()`, `b5.h.initLoginData()` | Intro 자동로그인, BaseActivity 재로그인, 위젯, WebView, DataActivity |
| `KEY_LOGIN_ID` | String | 로그인 ID 또는 간편로그인 custId | `F4.a` AES | `K5.b.onReceive()` | 로그인 화면 채움, 자동로그인, DataActivity, 승차권 캐시 저장 조건 |
| `KEY_LOGIN_PW` | String | 일반 로그인 비밀번호 | `F4.a` AES | `K5.b.onReceive()`, logout/reset 시 `""` | 로그인 화면 채움, 자동로그인, DataActivity |
| `KEY_LOGIN_CUST_NO` | String | `LoginResponse.strCustNo` 고객번호/고객관리번호 | `F4.a` AES | `K5.b.onReceive()` | 위젯 편의설정, 장바구니/MAAS cancel 등 |
| `KEY_LOGIN_INTEGRATION_FLAG` | String | 로그인 통합 플래그 | 없음 | `K5.b`, `BaseActivity` 로그인 응답 처리 | `X5.j` 등 |
| `KEY_LOGIN_INTEGRATION_MSG` | String | 통합 안내 메시지 | 없음 | `K5.b`, `BaseActivity` | UI 안내 |
| `KEY_LOGIN_INTEGRATION_URL` | String | 통합 URL | 없음 | `K5.b`, `BaseActivity` | UI/웹 이동 |
| `is_exist_push_data` | String | push DB 기본값 생성 여부 확인용 최근 `strCustNo` | 없음 | `BaseActivity` 로그인 성공 처리 | 같은 고객번호 중복 push 기본값 생성 방지 |
| `보훈번호` | String | 보훈번호 | `F4.a` AES | `VeteransNoSettingActivity` | 보훈 할인 입력 UI |

로그아웃/세션 초기화 흐름인 `b5.h.initLoginData()`는 쿠키를 지우고 `KEY_AUTO_LOGIN=false`, `KEY_LOGIN_PW=""`를 저장한다. 확인된 코드상 `KEY_LOGIN_ID`, `KEY_LOGIN_TYPE`, `KEY_MEMBER_NUM`, `KEY_LOGIN_CUST_NO`는 이 함수에서 명시적으로 삭제하지 않는다.

### 서버 common-code / 앱 설정 캐시

`IntroActivity.onReceive(dao_common_code)`와 `dao_app_data`는 서버 응답 일부를 JSON 문자열로 prefs에 저장한다.

| 키 | 저장값 |
|---|---|
| `LOGIN_DATA` | common-code `Login` JSON. `key`, `idx`, `pwdAESCphd` 등 로그인 암호화 정책 포함 |
| `EASY_LOGIN` | 간편로그인 노출 정책 JSON |
| `VAR_DATA` | 앱 feature/config JSON. `isMacroEnable`, `autoRefresh` 등 |
| `ATHN` | 인증 관련 설정 JSON |
| `VIEW_VISIBILITY` | 화면 표시 정책 JSON |
| `EASY_PAY_OPTION` | 간편결제 옵션 JSON |
| `POINT_PAY_OPTION` | 포인트 결제 옵션 JSON |
| `MENU_BIZ`, `MENU_RAIL_POINT`, `KORAIL_BOSS`, `LOST_ARTICLE`, `REPORT_DATA`, `HOLIDAY_POPUP_DATA` | 메뉴/안내/신고/팝업 관련 서버 설정 JSON |
| `CONVENIENCE_SETTING_VISIBLE` | 바로구매/편의설정 노출 여부 |
| `CONVENIENCE_SETTING_UPDATE` | 편의설정 갱신 필요 플래그 |
| `OREO_DATA` | Android O 미만 기기용 OS 팝업 데이터 |
| `KEY_RAIL_PLUS_CARD_INFO`, `KEY_LIMOUSINE_MSG`, `KEY_LIMOUSINE_MAIN_MSG`, `DISABILITY_CERTIFICATION_MSG` | 앱 데이터 API 응답 문자열 |
| `NOTICE_DATA` | 공지 제목/POST 데이터 JSON |
| `MAP_VERSION` | 역 정보 버전 int |

이 영역은 대부분 평문 JSON이다. `LOGIN_DATA.key`는 서버 전송 암호화에 쓰이는 key material로 보이며 prefs에 평문 저장된다.

### UI/기능 플래그

| 키 | 저장값/용도 |
|---|---|
| `IS_DEVICE_POPUP_TODAY` | 기기 OS 팝업 "오늘 보지 않기" 날짜 |
| `IS_DIALOG_AUTO_POPUP_CHATBOT` | 챗봇 자동 팝업 표시 여부 |
| `IS_TICKET_AUTO_REFRESH` | 승차권 자동 새로고침 설정 |
| `KEY_SETTING_SECURE_ANDROID_ID` | 비상승차권에서 Android ID 관련 fallback/상태 판단에 사용 |
| `TRAIN_NEAR_STATION`, `TRAIN_SRT_STATION`, `TRAIN_NEAR_SRT_STATION` | 메인 예약 화면 역 필터 토글 |
| `IS_MULTI_LANGUAGE_TYPE` | 다국어 설정 |

## 로컬 AES Helper: `F4.a`

### 키 파생

`F4.a`의 private key 함수는 다음 로직이다.

1. `Settings.Secure.getString(contentResolver, "android_id")`를 읽는다.
2. Android ID bytes로 `UUID.nameUUIDFromBytes(...)`를 만든다.
3. UUID 문자열의 UTF-8 bytes 앞 16바이트를 잘라 AES key로 사용한다.

즉 로컬 저장 암호화 키는 앱 내부 난수나 Android Keystore가 아니라 단말의 Android ID에서 결정된다.

### 알고리즘

| 함수 | 알고리즘 | 인코딩 | 사용처 |
|---|---|---|---|
| `encryptAES(context, plain)` | `AES/ECB/PKCS5Padding` | ciphertext를 Android Base64 flag `0`로 인코딩 | 로그인 ID/PW/customer no, 즐겨찾기 카드, 승차권 캐시, SMS 번호, 보훈번호 |
| `decryptAES(context, value)` | `AES/ECB/PKCS5PADDING` | Base64 flag `0` decode 후 AES decrypt | 저장값 복호화 |
| `encryptBase64(plain)` | Base64 flag `2` | 암호화 아님 | 서버 전송 전 wrapper, DataActivity export |
| `decryptBase64(value)` | Base64 flag `2` | 암호화 아님 | Base64 decode |

대소문자 차이(`PKCS5Padding`/`PKCS5PADDING`)는 JCE transformation 처리상 동일하게 취급된다.

### 저장값별 암호화 적용 범위

| 저장값 | 암호화 여부 | 비고 |
|---|---|---|
| `KEY_LOGIN_ID`, `KEY_LOGIN_PW`, `KEY_LOGIN_CUST_NO` | AES | `F4.a` |
| 즐겨찾기 카드 전체 주요 필드 | AES | nickname/번호/월/년/type/businessNum |
| `IssueList.issueList`, `TicketDetail.ticketDetail` | AES | API response JSON 전체 |
| `SMSData.phoneNumber` | AES | PNR 자체는 평문 id |
| `보훈번호` | AES | prefs |
| `StationData`, `FavoriteStation`, `ZRecentStation`, `MainPopupData`, `DoNotLookAgain` | 대부분 평문 | 역/구간/팝업/suppress 정보 |
| common-code prefs JSON | 평문 | `LOGIN_DATA` 포함 |

## 서버 전송용 암호화와 로컬 저장 암호화의 차이

로그인 비밀번호는 로컬 저장 시 `F4.a.encryptAES()`로 저장되지만, 서버 전송 시에는 다시 다른 방식으로 가공된다.

| 흐름 | 동작 |
|---|---|
| 로그인 입력 전송 | `K5.b.B0()`이 입력 ID/PW를 `LoginRequest`에 설정한다. PW는 `E0()` 처리 결과를 사용한다. |
| 자동 로그인 전송 | `K5.b.z0()` 또는 `BaseActivity.G()`가 prefs의 `KEY_LOGIN_ID/PW`를 `F4.a.decryptAES()`로 복호화한 뒤 서버 전송용으로 다시 암호화한다. |
| 서버 암호화 정책 | `LOGIN_DATA` JSON의 `pwdAESCphd`가 `"Y"`이면 `S4.C0812l.encryptAES(login.key, plain)` 후 다시 `F4.a.encryptBase64()` 적용 |
| fallback | `pwdAESCphd != "Y"`이면 평문 비밀번호를 단순 Base64로 인코딩 |
| AES/CBC detail | `S4.C0812l.encryptAES(key, value)`는 `AES/CBC/PKCS5Padding`, key bytes를 AES key로 사용하고 IV는 `key.substring(0, 16)` |
| SID | `S4.C0812l.getSid()`는 고정 key `"2485dd54d9deaa36"`로 `"AD" + timestamp`를 AES/CBC 암호화 |

`LOGIN_DATA.key`와 `pwdAESCphd`는 common-code 응답으로 받아 prefs에 평문 JSON으로 저장된다. 따라서 서버 전송용 암호화는 로컬 저장값 보호와 별개의 프로토콜/난독화 성격이 강하다.

## 캐시 삭제와 상태 초기화

| 흐름 | 삭제/초기화 대상 | 비고 |
|---|---|---|
| DB upgrade | `StationData`, `MainPopupData`, `DoNotLookAgain`, old 카드 테이블 | 현재 카드 데이터는 old 모델에서 best-effort migration |
| 역 데이터 갱신 | `deleteAllStationList()` 후 전체 station insert | `MAP_VERSION`, station count 비교로 갱신 결정 |
| 승차권 목록 refresh | `deleteIssueList()`, `deleteTicketDetail()` | 새 목록/상세를 다시 AES 저장 |
| 승차권 상세 처리 완료 | `deleteSMSData(currentPnrList)` | 현재 PNR에 없는 SMS 번호 row 삭제 |
| 메인 팝업 갱신 | `deleteMainPopupData()` 후 조건부 insert | 서버 show/noticeId/confirmDate에 의존 |
| 로그아웃/세션 초기화 | 쿠키 삭제, `KEY_AUTO_LOGIN=false`, `KEY_LOGIN_PW=""`, 메모리 login data 초기화 | `KEY_LOGIN_ID`, `KEY_LOGIN_CUST_NO`는 확인된 함수에서 삭제되지 않음 |
| 자동로그인 실패 | `BaseActivity`에서 `initLoginData()` 호출 가능 | redirect URL이 없을 때 로그인 저장 상태 일부 초기화 |

## 개인정보와 보안 메모

| 항목 | 관찰 | 영향 |
|---|---|---|
| Android ID 기반 키 | 로컬 AES key가 Android ID에서 결정된다 | Keystore/사용자 인증 기반 보호가 아니며, Android ID를 얻을 수 있는 환경에서는 복호화 가능성이 커진다 |
| AES/ECB | IV가 없고 deterministic | 같은 평문은 같은 ciphertext가 되어 패턴 노출 및 암호문 비교가 가능하다 |
| Base64 fallback | `pwdAESCphd != "Y"`이면 서버 전송 비밀번호가 단순 Base64 | Base64는 암호화가 아니므로 전송 보안은 TLS와 서버 정책에 의존 |
| `LOGIN_DATA.key` 평문 저장 | 서버 전송 AES key material이 prefs JSON에 평문 저장 | 앱 데이터 접근자가 서버 전송 암호화 재현 가능 |
| DB 자체 암호화 없음 | ORMLite/SQLite helper만 확인되고 SQLCipher/Keystore 사용은 확인되지 않음 | DB 파일 접근 시 평문 테이블과 AES ciphertext가 함께 노출 |
| 로그인 reset 불완전 | `initLoginData()`는 PW와 auto-login만 명시 초기화 | 저장 ID/customer no/type/member-save flag가 남을 수 있다 |
| 승차권 캐시 | 목록/상세 JSON 전체 저장 | PNR, 반환 비밀번호, 좌석/여정 정보 등 민감 데이터가 로컬에 남는다 |
| 카드 저장 | 카드번호/유효기간/사업자번호를 AES 저장 | PAN 저장 범위가 넓고 ECB/Android ID 기반 키라 보안 강도가 제한적 |
| PNR/SMS | `SMSData.pnrNo`는 평문 primary key | 전화번호는 AES 저장이나 PNR 기반 linkage는 노출 |
| 팝업 suppress | `DoNotLookAgain.custMgNo` 평문 | 고객관리번호와 팝업 행동 데이터가 DB에 평문 저장 |

## 소스 참조

| 주제 | 파일/라인 |
|---|---|
| DB helper 생성자, DAO, create/upgrade | `/tmp/korail-jadx/sources/J4/a.java:55`, `:73`, `:140`, `:158` |
| DB facade CRUD | `/tmp/korail-jadx/sources/J4/b.java:62`, `:78`, `:134`, `:195`, `:232`, `:252`, `:272`, `:326`, `:359`, `:400`, `:461`, `:469` |
| DB 모델 | `/tmp/korail-jadx/sources/com/korail/talk/database/model/*.java` |
| 로컬 AES helper | `/tmp/korail-jadx/sources/F4/a.java:13`, `:17`, `:32`, `:43` |
| 서버 AES/CBC helper | `/tmp/korail-jadx/sources/S4/C0812l.java:18`, `:26`, `:43` |
| Preferences helper | `/tmp/korail-jadx/sources/S4/H.java:13`, `:34`, `:38`, `:59`, `:68` |
| 로그인 저장/자동로그인 | `/tmp/korail-jadx/sources/K5/b.java:102`, `:124`, `:211`, `:445` |
| 로그인 화면 저장값 복호화 | `/tmp/korail-jadx/sources/K5/a.java:35`, `/tmp/korail-jadx/sources/K5/c.java:35`, `/tmp/korail-jadx/sources/K5/d.java:35` |
| BaseActivity 자동로그인 | `/tmp/korail-jadx/sources/com/korail/talk/view/base/BaseActivity.java:145`, `:214`, `:385` |
| 로그인 메모리 상태와 초기화 | `/tmp/korail-jadx/sources/S4/u.java:138`, `/tmp/korail-jadx/sources/b5/h.java:182` |
| common-code prefs와 팝업 캐시 | `/tmp/korail-jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:614`, `:667` |
| 역 데이터 갱신 | `/tmp/korail-jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:119`, `:433`, `:720` |
| 즐겨찾기 카드 | `/tmp/korail-jadx/sources/com/korail/talk/ui/setting/favoriteCards/a.java:179`, `/tmp/korail-jadx/sources/com/korail/talk/ui/setting/favoriteCards/b.java:197` |
| 즐겨찾기 구간 | `/tmp/korail-jadx/sources/com/korail/talk/ui/setting/favoriteSections/a.java:112`, `:284`, `/tmp/korail-jadx/sources/com/korail/talk/ui/setting/favoriteSections/b.java:94` |
| 최근 구간 | `/tmp/korail-jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:390`, `/tmp/korail-jadx/sources/com/korail/talk/ui/booking/option/station/StationSearch.java:265` |
| 승차권 캐시 | `/tmp/korail-jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:333`, `:1386`, `:1634`, `/tmp/korail-jadx/sources/H4/a.java:26`, `:40` |
| SMS 번호 캐시 | `/tmp/korail-jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1129`, `/tmp/korail-jadx/sources/com/korail/talk/ui/service/sms/GuardianReliefSmsActivity.java:126` |
| DoNotLookAgain | `/tmp/korail-jadx/sources/S4/C0811k.java:59`, `:161`, `/tmp/korail-jadx/sources/J4/b.java:242`, `:336` |
| 사용자 식별자 prefs 사용 | `/tmp/korail-jadx/sources/com/korail/talk/ui/scheme/DataActivity.java:23`, `/tmp/korail-jadx/sources/com/korail/talk/provider/WidgetReceiver.java:52`, `/tmp/korail-jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java:590` |
