# Phase 1 — 인증·로그인·본인확인·세션 감사 보고서

담당 영역: `network/dao/login/`, `network/dao/certification/`, `network/dao/cust/`, `network/dao/nFilter/`
대조 대상: `src/korail_mobile_api/session.py`, `crypto.py`, `client.py`, `safety.py`, `constants.py`, `read_payloads.py`, `read_parsers.py`, `limousine_payloads.py`, `limousine_parsers.py`

## 카운팅 규칙

이 앱은 여러 `LoginDao` 하위클래스(`AutoLoginDao`/`EasyLoginDao`)가 **같은** Retrofit 메서드(`login`)를
호출하고, `certification.ReservationList`/`nonMember.NonMemTicket`/`certification.TicketReservation`은
**한 경로에 서로 다른 필드 집합을 가진 복수의 Retrofit 오버로드**가 걸려 있다. `login`은 wire-shape가
다른 3가지 DAO(manual/auto/easy)를 표에서 **별도 행**(#1/#2/#3)으로 나눠, 그중 manual/auto는 완전히
일치하고 easy만 어긋난다는 것을 드러낸다. 아래 카운트는 **"1. 전체 기능 목록" 표의 행 수** 그대로다.

- **추출한 앱 함수/엔드포인트**: 25 (LoginService 9 + CustService 1 + NFilterService 1 +
  CertificationService 10 + BusReservationService 4)
- **라이브러리에 올바르게 구현된 것**: 10 — `있음`으로 표기된 행 (#1, #2, #4, #10, #12, #13, #14,
  #22a, #22b, #22c)
- 나머지 15개 행 중: `login`의 easy 하위 shape 1건(부분구현, K1-02), 회원관리 5건은
  `docs/RELEASE_GAP_PLAN.md`에 의도적 보류로 명시됨(K1-01, info), nFilter 1건은 서버상 사용되지
  않는 dead code로 제외가 정당함(정보), 나머지 8건은 certification/BusReservation 패키지에 얹혀
  있는 예약·할인인증 도메인 기능으로 인증·세션 범위 밖(K1-04, 다른 phase 소관으로 인계 권장).

## 1. 전체 기능 목록

### 1.1 LoginService (`network/dao/login/`)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 1 | 회원 로그인 (수동, ID/휴대폰/이메일) | `POST /classes/com.korail.mobile.login.Login` (`login`) | `LoginService.java:17-19`; `LoginDao.java:236-243`; 버튼 클릭 `k5/b.java:403-404,115-117`(`C0()`→checkValidPw=`"Y"`) | `session.py:146-250` (`KorailSessionClient.login/_login`), `client.py:284-299` | 있음 |
| 2 | 자동 로그인 (저장된 자격증명 재사용, checkValidPw=`"N"`) | 동일 엔드포인트, DAO=`AutoLoginDao` | `AutoLoginDao.java:6-12`; `k5/b.java:211-225`(`z0()`), `BaseActivity.java:385-402`(`G()`) | `session.py`의 `check_valid_pw` 파라미터로 호출자가 재현 가능 (`"N"` 전달 시 필드 구성 동일) | 있음 |
| 3 | 간편(소셜) 로그인 — Kakao/Naver/Google/Onepass, `custId`만 전송 | 동일 엔드포인트, DAO=`EasyLoginDao` | `EasyLoginDao.java:6-10`; `k5/b.java:236-244`(`executeEasyLogin`, `txtMemberNo`/`txtPwd`/`idx` 미설정) | 없음 — `session.py:_login()`이 `member_no`/`password`를 항상 폼에 실어 보냄 | **부분 구현 (K1-02)** |
| 4 | 로그아웃 | `GET /classes/com.korail.mobile.login.Logout` (`logout`, 파라미터 없음, 쿠키 인증) | `LoginService.java:29-30`; `LogoutDao.java:8-12` | `session.py:252-268` | 있음 |
| 5 | 회원 인증 조회(userCheck, N카드/기프티켓/마일리지 등에서 이름+식별자로 회원카드번호 조회) | `POST /classes/com.korail.mobile.login.userCheck` (`certMember`) | `LoginService.java:13-15`; `MemberCertDao.java:11-89` | 없음 | **없음 (K1-01)** |
| 6 | 간편로그인 연동 등록 (My Page, 소셜 계정 연결) | `POST /classes/com.korail.mobile.login.loginAthnReg.do` (`loginAthnReg`) | `LoginService.java:21-23`; `LoginAthnRegDao.java:35-40`; `MyPageActivity.java:417-424` | 없음 | **없음 (K1-01)** |
| 7 | 간편로그인 연동 해제 | `POST /classes/com.korail.mobile.login.loginAthnRmv.do` (`loginAthnRmv`) | `LoginService.java:25-27`; `LoginAthnRmvDao.java:35-40`; `MyPageActivity.java:427-431` | 없음 | **없음 (K1-01)** |
| 8 | 회원가입 확인/탈퇴 전 비밀번호 확인 (`hmpgPwd` 평문) | `POST /classes/com.korail.mobile.login.joinCfm.do` (`memberCheck`) | `LoginService.java:32-34`; `MemberCheckDao.java:35-40` | 없음 | **없음 (K1-01)** |
| 9 | 회원 탈퇴 예약 | `POST /classes/com.korail.mobile.login.mbSced.do` (`memberDrop`, `Key` 없음) | `LoginService.java:36-38`; `MemberDropDao.java:16-21` | 없음 | **없음 (K1-01)** |

### 1.2 CustService (`network/dao/cust/`)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 10 | 다자녀 등 할인대상 가족 조회 | `POST /classes/com.korail.mobile.cust.mchdDcntTgt.do` | `CustService.java:11-13`; `MchdDcntTgtDao.java:12-103` (`Fmly`: `btdt,custFmlyNm,dcntKndCd,fmlySqno,psgTpCd,psgTpNm,psrmClCd,rqDcntKndCd`) | `client.py:900-913`(`get_multi_child_discount_targets`), `read_payloads.py:551-554`, `read_parsers.py:1720-1729,1816-1834` | 있음 |

### 1.3 NFilterService (`network/dao/nFilter/`)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 11 | 보안 키패드 공개키 발급(명목상) | `POST /classes/com.korail.mobile.nFilter.createKey.do` | `NFilterService.java:10-12`; `NFilterCreateKeyDao.java` — **앱 전체에서 caller 0건**, `docs/deep-dive/full-api-analysis-2026-07-20.md:496`은 라이브 프로브 HTTP 404까지 확인 | 없음 | **의도된 제외 (정보)** — dead code, 서버에 경로 자체가 없음 |

### 1.4 CertificationService (`network/dao/certification/`) — 본인확인/식별 성격

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 12 | 예약 상세 조회 (PNR로 보류중 예약 읽기) | `GET /classes/com.korail.mobile.certification.ReservationList` (`inquiryTicketRsv`) | `CertificationService.java:45-46`; `TicketRsvInquiryDao.java:26-31` | `client.py:1102-1127`(`get_ticket_reservation_detail`), `read_payloads.py:1557-` | 있음 |
| 13 | 운임 재계산 (보류 PNR 할인 변경) | `POST /classes/com.korail.mobile.certification.PriceReCalculation` (`getDiscountPrice`) | `CertificationService.java:35-37`; `DiscountPriceDao.java:12-128` (14 `@Field`, 6개 리스트) | `client.py:2234-2308`(`recalculate_price`), `mutation_payloads.py:1748-` | 있음 |
| 14 | 회원 예약 확정/보류 (좌석 hold) | `POST /classes/com.korail.mobile.certification.TicketReservation` (`reservation`, 회원 분기) | `CertificationService.java:52-54,60-62`; `ReservationDao.java:12-18` (custNm/cpNo 없으면 이 경로) | `client.py:1570,1740,1812,2212` 등 (`reserve`, transfer/merge/discount-card holds) | 있음 |
| 15 | 비회원 예약 확정/보류 (이름+휴대폰+5자리 비밀번호) | `POST /classes/com.korail.mobile.nonMember.NonMemTicket` (`reservation`, 비회원 분기 + Bixby 변형) | `CertificationService.java:48-50,56-58`; `ReservationDao.java:15-17`(custNm/cpNo 존재 시); `BixbyReservationDao.java` | 없음 — `reserve()`가 항상 `self.session.current is None`이면 예외 | **없음 (K1-04, 정보)** |
| 16 | 장애인 등록 할인증명서 신청/적용 | `GET /classes/com.korail.mobile.certification.ReservationList` (`applyDisabilityCertification`, 같은 경로의 별도 오버로드) | `CertificationService.java:22-23` | 없음 — 이 경로는 read overload(`inquiryTicketRsv`)만 4필드로 pin되어 있어 이 write overload 자체가 나갈 수 없음(`safety.py:62-` 주석) | **없음 (K1-04, 정보)** |
| 17 | 국회의원 할인 인증 | `GET /classes/com.korail.mobile.certification.assemblyCert` (`certCongressperson`) | `CertificationService.java:25-26`; `CongresspersonCertDao.java` | 없음 | **없음 (K1-04, 정보)** |
| 18 | 국가유공자 할인 인증 (주민번호 앞7자리+비밀번호) | `POST /classes/com.korail.mobile.certification.MeritCert` (`certMerit`) | `CertificationService.java:28-30`; `MeritCertDao.java:11-107` | 없음 | **없음 (K1-04, 정보)** |
| 19 | 장애 할인 인증 | `GET /classes/com.korail.mobile.certification.disabled.do` (`disabledCertification`) | `CertificationService.java:32-33`; `DisabledCertificationDao.java` | 없음 | **없음 (K1-04, 정보)** |
| 20 | 공공기관(정부) 인증 토큰 생성 | `GET /classes/com.korail.mobile.pbep.toknCre.do` (`govermentCertification1`) | `CertificationService.java:39-40`; `GovernmentCertificationStep1Dao.java` | 없음 | **없음 (K1-04, 정보)** |
| 21 | 공공기관(정부) 인증 상태 확인 | `GET /classes/com.korail.mobile.pbep.sttChck.do` (`govermentCertification2`) | `CertificationService.java:42-43`; `GovernmentCertificationStep2Dao.java` | 없음 | **없음 (K1-04, 정보)** |

### 1.5 BusReservationService (`network/dao/certification/`, 같은 패키지에 별도 인터페이스)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 22a | 리무진(연계교통) 스케줄 조회 | `POST /classes/com.korail.mobile.lmu.scdlQry.do` (`reservationList`) | `BusReservationService.java:27-29`; `BusReservationListDao.java` — **주의:** `@Field("tmGpCd")`가 실제 wire 이름이며 DTO 필드명 `trnGpCd`와 다름 | `client.py:378-393`(`get_limousine_schedules`), `limousine_payloads.py:76-94`(`tmGpCd` 정확히 반영) | 있음 |
| 22b | 리무진 잔여좌석 조회 | `POST /classes/com.korail.mobile.lms.TResidualSeatsResearch.do` (`reservationSeatList`) | `BusReservationService.java:31-33`; `BusReservationSeatListDao.java` (`isArrow`는 Java `boolean`) | `client.py:395-410`(`get_limousine_seat_inventory`), `limousine_payloads.py:97-120`(`isArrow`→`"true"/"false"`) | 있음 |
| 22c | 보류 예약 취소 확인 | `POST /classes/com.korail.mobile.reservationCancel.ReservationCancelChk` (`reservationCancelCheck`) | `BusReservationService.java:19-21` | `client.py:1859`(`cancel_unpaid_hold`), `safety.py:228,284` | 있음 |
| 22d | 예약 변경 (승차인원/입석/대형수하물 등) | `POST /classes/com.korail.mobile.reservation.reservationChange.do` (`reservationChange`) | `BusReservationService.java:23-25` | 없음 | **없음 (K1-04, 정보)** |

## 2. Findings

### K1-01 — 회원관리 5개 엔드포인트 미구현 (문서화된 의도적 보류)

- 분류: missing / 심각도: info
- 대상: `certMember`(userCheck), `loginAthnReg`, `loginAthnRmv`, `memberCheck`(joinCfm), `memberDrop`(mbSced)
- 앱 근거: `LoginService.java:13-38`; 각 DAO(`MemberCertDao.java`, `LoginAthnRegDao.java`, `LoginAthnRmvDao.java`,
  `MemberCheckDao.java`, `MemberDropDao.java`)
- 라이브러리 근거: 없음 — `grep -rn "loginAthnReg|loginAthnRmv|mbSced|joinCfm|userCheck|memberDrop|memberCheck|certMember" src/` 전부 무결과
- 상세: 이 5개는 `docs/RELEASE_GAP_PLAN.md:445-447`("member-drop (`login.mbSced.do`), account link/unlink...
  Keep in `EXCLUDED_API_DOMAINS` until explicitly scoped")과
  `docs/deep-dive/full-api-analysis-2026-07-20.md:2692-2696`("Not ported" / "Account-linking write" /
  "Withdrawal pre-check" / "`member-drop` excluded")에 명시적으로 문서화된 의도적 제외다. `memberDrop`은
  특히 비가역적 회원탈퇴이므로 계속 배제하는 것이 안전 모델과 일치한다. **결함이 아니다** — 다만
  "완전 목록"에는 포함해야 하므로 기록한다.

### K1-02 — 간편(소셜) 로그인 wire-shape가 라이브러리에서 재현 불가능

- 분류: missing / 심각도: low
- 앱 근거: `k5/b.java:236-244` (`executeEasyLogin`) — `LoginDao.LoginRequest`에 `loginType`, `custId`,
  `checkValidPw`만 설정하고 `txtMemberNo`/`txtPwd`/`idx`는 **설정하지 않음**(Java null → Retrofit이
  해당 `@Field`를 폼에서 완전히 생략). 제공자 코드는 `S4/u.java:126-128`
  (`isEasyLoginType`: `"K".equals || "N".equals || R1.x.MAX_AD_CONTENT_RATING_G.equals || HelpSrvCustDao.HelpSrvCustRequest.f28874D.equals`)에서
  직접 확인 — `R1/x.java:34`가 `MAX_AD_CONTENT_RATING_G = "G"`, `HelpSrvCustDao.java:19`가
  `f28874D = "D"`이므로 실제 코드는 `K`/`N`/`G`/`D` 4종.
- 라이브러리 근거: `session.py:173-208` (`_login`) — `form` 딕셔너리가 항상 `"txtMemberNo": member_no`,
  `"txtPwd": transformed`를 채우며, `member_no`/`password`가 `KorailSessionClient.login()`의 필수
  위치 인자다. `custId`만 보내고 나머지 두 필드를 완전히 생략하는 경로가 없다.
- 실패 시나리오: 호출자가 이 shape를 우회하려고 `member_no=""`, `password=""`를 넘기면, 앱은 필드
  자체가 부재(`null` → Retrofit이 드롭)한 요청을 보내는 반면 라이브러리는 `txtMemberNo=""`(빈
  문자열이지만 **존재**)와 `transform_login_password("", info)`의 결과인 비어있지 않은 `txtPwd`
  (AES-암호화된 빈 문자열의 Base64, 또는 최소한 `""`의 Base64)를 보낸다. "필드가 비어있음"과
  "필드가 아예 없음"은 서버가 다르게 취급할 수 있는 별개의 상태이며, 이 경로로는 카카오/네이버/구글/
  Onepass로 연동된 계정을 이 라이브러리로 재로그인할 방법이 없다.
- 제안: 소셜 로그인은 별도 OAuth 플로우(카카오/네이버/구글 SDK, Onepass WebView)로 `custId`를
  획득해야 하므로 라이브러리 범위 밖일 가능성이 높다 — 다만 문서에 명시적 제외 결정이 없으므로,
  향후 `login()`과 별개로 `login_easy(login_type, cust_id, check_valid_pw="N")` 같은 명시적
  API를 추가하거나, 최소한 "이 라이브러리는 소셜/간편 로그인 continuation을 지원하지 않는다"는
  문서화를 권장.

### K1-03 — `EXCLUDED_API_DOMAINS`의 `"reservation"` 라벨이 실제 구현 상태와 불일치 (doc-drift, 인계)

- 분류: doc-drift / 심각도: low
- 앱 근거: 해당 없음 (라이브러리 내부 문서 주석 문제)
- 라이브러리 근거: `safety.py:41-51` — `EXCLUDED_API_DOMAINS`가 `"reservation"`을 "considered and
  declined" 영역으로 기록하지만, `client.py:1570,1740,1812,2212`에서 `reserve`/`transfer`/
  `merge`/`discount-card` hold가 이미 광범위하게 구현되어 있다(`require_mutation_consent(consent,
  "reserve")` 게이트까지 포함). 주석 자체가 "This set is documentary: nothing dispatches on it"이라
  기능적 결함은 아니지만, 목록이 최신 구현 상태를 반영하지 못해 오해를 유발할 수 있다.
- 이 항목은 예약(reservation) 도메인 소관이므로 여기서는 발견만 기록하고 인계한다. 심층 조사는
  하지 않음.

### K1-04 — certification 패키지의 할인인증/비회원예약 8건 미구현 (도메인 밖 가능성, 정보)

- 분류: missing / 심각도: info
- 앱 근거: `CertificationService.java:22-58`(`applyDisabilityCertification`, `certCongressperson`,
  `certMerit`, `disabledCertification`, `govermentCertification1/2`, 비회원 `reservation`×2 = 표의
  #15-#21, 7건), `BusReservationService.java:23-25`(`reservationChange` = 표의 #22d, 1건) — 합계 8건
- 라이브러리 근거: 없음 — `grep -rn "MeritCert|assemblyCert|DisabledCertification|disabled.do|toknCre|sttChck|NonMemTicket|reservationChange" src/`
  중 `NonMemTicket`은 `constants.py:424`(DynaPath allowlist 문서화)에만 등장하고 실제 송신 경로는 없으며,
  `reservationChange`는 결과 0건
- 상세: 이 8개는 (1) 장애인/국가유공자/국회의원/공공기관 **할인 자격 인증**이거나 (2) **비회원**
  예약/(3) **예약 변경**으로, 로그인 세션·본인확인 자체보다는 예약·운임(pricing) 도메인에 더 가깝다.
  `docs/RELEASE_GAP_PLAN.md`의 "Core mutation endpoint count: 27" 목록에도 명시적으로 포함되어
  있지 않다. 다만 `memberDrop` 등과 달리 "제외한다"는 명시적 결정 문장은 찾지 못했다 — 즉
  **의도적 제외인지 단순 누락인지 문서만으로는 확인불가**다. 국가유공자 인증(`MeritCert`)은
  주민등록번호 앞 7자리(`txtJuminNo7`)를 평문으로 전송하는 민감 정보 흐름이라는 점만 기록해 둔다
  (`MeritCertDao.java:14,33-35`). 예약/할인 도메인 담당 phase에서 재검토를 권장하며, 본 보고서는
  발견 사실만 기록하고 그 이상 판단하지 않는다.

### K1-05 — `infer_login_input_flag`의 휴대폰/회원번호 판별이 앱에 없는 라이브러리 자체 추론이며 겹칠 수 있음

- 분류: risk / 심각도: low
- 앱 근거: `k5/b.java:119-122`(`D0()`) — 앱은 추론하지 않는다. 사용자가 탭(휴대폰/이메일/회원번호)을
  직접 선택하면 `txtInputFlg`가 그 탭의 고정값으로 결정된다. 회원번호 탭은
  `k5/c.java:19-22`(`LengthFilter(10)`, `setInputType(2)` 숫자)로 **10자리 숫자**를 받는다.
- 라이브러리 근거: `session.py:63-69`(`infer_login_input_flag`) — `login_id`가 `"01"`로 시작하고
  길이가 10~11자리인 순수 숫자면 무조건 `"4"`(휴대폰)로 추론하고, 그 외 숫자는 `"2"`(회원번호)로
  추론한다.
- 상세: 회원번호 탭이 받는 10자리 숫자 범위와 휴대폰 판별 조건(`01`로 시작 + 10~11자리)이 값
  공간에서 겹친다 — `01`로 시작하는 10자리 회원번호가 존재한다면 `infer_login_input_flag`가
  이를 `"4"`(휴대폰)로 잘못 분류해 `login()` 호출자가 `input_flag`를 명시하지 않으면 실제로는
  회원번호인데 휴대폰으로 전송될 수 있다. KORAIL 회원번호가 실제로 `01`로 시작할 수 있는지는
  APK 정적분석만으로는 확인 불가(회원번호 채번 규칙은 서버 정책이라 unknown) — 그래서 `risk`로만
  분류한다. `input_flag`를 호출자가 명시하면 이 추론 자체가 우회되므로 심각도는 낮다.
- 제안: 문서에 "회원번호가 `01`로 시작하는 경우 `input_flag="2"`를 명시적으로 전달하라"는 주의를
  추가하거나, 추론 휴리스틱 자체를 재고할 것을 권장.

## 3. 상세 검증 — 정확히 맞는지 확인한 핵심 항목 (문제 없음, 기록용)

다음은 특히 꼼꼼히 대조했고 **문제가 없다고 확인된** 항목들이다(반복되는 "문자열 vs 숫자" 함정과
"jadx만 보고 단정" 함정을 피하기 위해 smali/원본 소스까지 직접 확인함):

1. **로그인 타입 코드 `"2"/"4"/"5"`.** `k5/b.java:119-122`(`D0()`)의 3항 연산자가 탭 인덱스별로
   `StbkAcntDao.ACCOUNT_REGISTER`(휴대폰 탭, index 0), `StbkAcntDao.CHANGE_PASSWORD`(이메일 탭,
   index 1), 리터럴 `"2"`(회원번호 탭, index 2)를 반환한다. 상수값은
   `analysis/apktool/smali/com/korail/talk/network/dao/pay/StbkAcntDao.smali:18,24`에서
   `ACCOUNT_REGISTER="4"`, `CHANGE_PASSWORD="5"`로 직접 확인했다(jadx와 smali 일치). 탭-프래그먼트
   매핑은 `LoginActivity.java:88`(순서: `K5.d, K5.a, K5.c`)과 각 프래그먼트의
   `TAG`/`getTitle(n)` 호출로 확인: `k5/d.java:12,25`="PhoneLoginFragment"(index 0),
   `k5/a.java:12,25`="EmailLoginFragment"(index 1), `k5/c.java:12,25`="MemberLoginFragment"(index 2).
   결론: 휴대폰="4", 이메일="5", 회원번호="2". `session.py:19-21`의
   `KORAIL_LOGIN_TYPE_MEMBER_NO="2"`, `KORAIL_LOGIN_TYPE_PHONE="4"`, `KORAIL_LOGIN_TYPE_EMAIL="5"`와
   **정확히 일치**.
2. **로그인 성공 코드.** `S4/u.java:130-132`(`isLoginSuccess`) = `"IRZ000001".equals || "S200".equals`.
   `session.py:18`(`KORAIL_LOGIN_SUCCESS_CODES = {"IRZ000001","S200"}`)와 일치.
3. **비밀번호 전송 암호화.** `S4/C0812l.java:18-24`(`encryptAES`: AES/CBC/PKCS5Padding, IV=key 문자열의
   앞 16자) → `F4/a.java:43-45`(`encryptBase64`: 결과 문자열을 다시 `Base64.encodeToString(..., NO_WRAP)`로
   한 번 더 인코딩). `crypto.py:41-52`(`transform_login_password`)가 동일한 이중 인코딩(내부
   AES+개행포함 Base64, 외부 NO_WRAP Base64)을 재현한다.
4. **로그인 continuation POST 데이터.** `S4/u.java:21-47`(`getLoginAuthenticationPostData`) —
   `callLogin=Y&memId=<loginId 또는 custId>&inputFlg=<loginType>&` 뒤에 `q.toJson(loginResponse)`의
   키를 순회하며 `strResult`/`h_msg_txt`만 제외하고 이어붙인다(URL 인코딩 없음). `session.py:76-94`
   (`build_login_authentication_post_data`)이 `KORAIL_LOGIN_CONTINUATION_FIELDS`(`LoginDao.java:82-110`
   선언 순서 그대로 29개 필드 + `h_msg_cd`)로 동일하게 재현.
5. **`BaseRequest` 공통 상수.** `Device="AD"`, `Version="250601003"`, `Key="korail1234567890"`
   (`BaseRequest.java:7,14`) = `constants.py:4-6`과 일치.
6. **`login`의 정확한 필드 순서.** `LoginService.java:19`(`Device,Version,Key,txtMemberNo,txtPwd,
   txtInputFlg,checkValidPw,custId,etrPath,idx`) — `idx`가 마지막. `session.py:187-203` 주석 및 폼
   구성이 이 순서를 그대로 따름.
7. **`mchdDcntTgt` 요청/응답 필드.** `MchdDcntTgtDao.java`의 `dptDt`(요청)와 `Fmly`의 8개 필드
   (`btdt,custFmlyNm,dcntKndCd,fmlySqno,psgTpCd,psgTpNm,psrmClCd,rqDcntKndCd`)가
   `read_payloads.py:551-554`, `read_parsers.py:1720-1729`와 정확히 일치.
8. **리무진(Bus) 스케줄/좌석 조회의 `tmGpCd` 함정.** `BusReservationService.java:29`의 Retrofit
   시그니처는 DTO 필드명이 `trnGpCd`임에도 실제 wire 이름은 `@Field("tmGpCd")`(오탈자성 이름)다.
   `limousine_payloads.py:88`이 정확히 `"tmGpCd"`를 쓴다 — 좌석조회(`:31-33`)는 반대로 진짜
   `trnGpCd`를 쓰며 `limousine_payloads.py:107`도 `"trnGpCd"`로 정확히 구분했다. `isArrow`(Java
   `boolean`)는 `"true"/"false"` 문자열로 정확히 변환(`limousine_payloads.py:119`).
9. **`ReservationList` 경로의 2-오버로드 함정.** 같은 경로가 read(`inquiryTicketRsv`, 4 `@Query`)와
   write(`applyDisabilityCertification`, `+txtPsgDisc0019Cnt`+6 `@QueryMap`)로 나뉘는데,
   `safety.py`의 `KORAIL_EXACT_REQUEST_FIELDS`가 read overload의 4필드만 허용하도록 pin되어 있어
   write overload가 이 경로로 나갈 수 없다 — `client.py:1108-1117` 주석에서도 명시.
10. **`memberCheck`가 `Key` 없이 평문 비밀번호 전송.** `LoginService.java:32-34`가 `Key` `@Field`를
    받지 않고 `hmpgPwd`도 암호화 처리 흔적이 없다 — 다만 K1-01에 의해 이 엔드포인트 자체가
    미구현이므로 라이브러리에 영향 없음.

## 4. 확인은 했으나 범위 밖으로 판단한 것 (누락 아님)

- **회원정보 조회/수정(프로필 편집)**: `network/dao/login|cust|certification|nFilter` 전체를 뒤졌으나
  구조화된 JSON "프로필 편집" API는 존재하지 않는다. 회원 식별 정보는 로그인 성공 응답
  (`LoginResponse`)의 `strCustNm/strEmailAdr/strHdcpFlg/...` 필드로만 제공되며(읽기 전용,
  `session.py`가 `raw`에 전량 보존), 실제 정보 수정은 WebView 기반 MyPage 화면으로 이루어지는 것으로
  보인다(본 담당 범위의 Retrofit 인터페이스에는 없음). 이는 "번들에 없다≠프로토콜에 없다" 함정과
  달리, 애초에 이 4개 디렉터리 안에 JSON 계약 자체가 없는 경우이므로 확인불가가 아니라 "해당 없음"으로
  분류한다.
- **본인확인(MCertify) WebView, 회원가입 WebView**: `docs/deep-dive/full-api-analysis-2026-07-20.md:424,428`가
  이미 `/ebizmk/member/mk_join_member.do`, `/classes/com.korail.mobile.certification.MCertify.do`를
  HTML 응답 WebView 흐름으로 확인했다 — JSON 계약이 없어 라이브러리 대조 대상이 아니다.
- **기기 등록**: 이 앱 빌드에는 별도의 "디바이스 등록" API가 없다(로그인 시 `Device`/`Version`/`Key`
  상수만 전송). "간편 로그인 연동(loginAthnReg/Rmv)"이 실질적으로 이에 가장 가까운 기능이며 K1-01에
  포함했다.
