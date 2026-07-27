# 참조 분석: `srtgo_plus` (KTX/코레일 예매 로직)

> READ-ONLY 정적 분석 문서. 코드 실행·네트워크 호출 없음. 대상 라이브러리
> `korail-mobile-api`의 mutation 갭(`docs/RELEASE_GAP_PLAN.md` §3~§5)을 실제 동작
> 클라이언트의 요청/응답 형태로 검증·해소하기 위한 사실 정리.
>
> 참조 리포: `srtgo_plus` — 이 저장소 밖에 따로 받아 둔 로컬 체크아웃이다(공개 위치를
> 확인하지 않았으므로 URL은 적지 않는다). 아래 인용은 그 체크아웃의 아래 커밋 기준.
> 커밋: `354960197855b2ca5d2fe300f26d1b45bdbf66ab` "Initial commit" (2026-03-23)
> 핵심 파일: `srtgo/ktx.py` (1101줄), 오케스트레이션 `srtgo/srtgo.py`.
> 인용된 라인 번호는 모두 `srtgo/ktx.py` 기준(다른 파일은 명시).

---

## 1. 개요 — srtgo_plus란 무엇이고 코레일을 어떻게 다루는가

- `srtgo_plus`는 원본 [srtgo](https://github.com/lapis42/srtgo)의 유지보수 포크로,
  SRT/KTX 승차권 예매를 자동화하는 CLI 도구(`srtgo` 콘솔 스크립트,
  `pyproject.toml:34-35`). Python ≥3.10, 의존성 `curl_cffi`/`requests`/`PyCryptodome`
  /`keyring` 등.
- 코레일(KTX) 측 로직은 **carpedm20/korail2 (BSD)** 를 기반으로 하며, 파일 상단
  docstring이 `korail2.korail2 :copyright: (c) 2014 Taehoon Kim :license: BSD`
  임을 그대로 명시(`ktx.py:1-7`). 여기에 **anti-bot 대응 `x-dynapath-m-token`
  생성 엔진**과 로그인 비밀번호 AES 이중-Base64 스킴을 추가한 것이 srtgo_plus의
  핵심 변경점(README "변경사항", `DynaPathMasterEngine` `ktx.py:54-160`).
- 코레일 접근 방식 요약: **단일 세션(쿠키 자동 관리) + 서블릿형 엔드포인트에
  form/query 파라미터 전송**. 로그인·검색·예약·조회·결제·취소·환불을 모두
  `Korail` 클래스(`ktx.py:628-1102`) 하나가 담당. 비밀번호만 서버 키로 AES 암호화,
  나머지 바디는 평문. 예매 성공 후 선택적으로 **카드 자동 결제(RAW PAN 직접 전송)**.
- 대상 앱 버전 대비: srtgo_plus는 `Version="250601002"`(`ktx.py:643`)를 사용 →
  우리 분석 대상 앱 `250601003`보다 **한 단계 낮음**. `Device="AD"`,
  `Key="korail1234567890"`는 동일(`ktx.py:642-644`).

### 1.1 라이선스 노트 (중요)

- **srtgo_plus 라이선스: MIT** (`srtgo_plus/LICENSE:1-21`, `Copyright (c) 2023 DKim`).
  서드파티로 **SRT (MIT, 2018 Gyeongjae Choi)** 및 **korail2 (BSD-3-clause, 2014
  Taehoon Kim)** 를 포함(`LICENSE:23-79`). 즉 코레일 로직의 원저작권은 BSD-3.
- MIT/BSD-3 모두 **permissive(비-copyleft)** → GPL류의 소스 개방 전염 의무 없음.
  따라서 라이선스 전염 리스크는 없다.
- 그러나 **엔드포인트 경로·파라미터 키·요청 바디 형태는 "사실(fact)"** 이므로
  자유롭게 참조·재구현 가능. 반면 `DynaPathMasterEngine`의 인코딩 알고리즘 구현체
  (`ktx.py:54-160`)·클래스 구조·주석 등 **표현(expression)은 그대로 복붙하지 말
  것**. 우리 `korail-mobile-api`에는 현재 최상위 `LICENSE` 파일이 없고 pyproject에
  license 필드도 없음(미지정 상태). BSD-3는 **저작권 고지 유지 의무**가 있으므로,
  만약 crypto/DynaPath 로직을 파생시키면 korail2(BSD-3) attribution을 남길 것.
  본 문서는 **API 요청 형태(사실)만** 추출했고 소스 표현을 옮기지 않는다.

---

## 2. 엔드포인트 · 호스트 · 공통 envelope

- **베이스**: `KORAIL_MOBILE = "https://smart.letskorail.com:443/classes/com.korail.mobile"`
  (`ktx.py:42`). 우리 origin lock(`smart.letskorail.com`)과 동일 호스트.
- **NetFunnel 호스트(별개)**: `http://nf.letskorail.com/ts.wseq` (`ktx.py:524`) —
  단, 코레일 측에선 **미사용**(§4 참조). SRT 측만 사용.
- **공통 envelope**: 대부분 바디에 `Device="AD"` + `Version="250601002"`가 들어가고,
  예약/조회/결제/취소/환불 계열은 추가로 `Key="korail1234567890"`를 포함
  (`ktx.py:642-644`). 로그인·검색 바디에는 `Key`가 **없음**(로그인은 Device/Version만).
- `API_ENDPOINTS` 정의는 `ktx.py:161-174`.

| 논리명 | 서블릿 경로 (`…com.korail.mobile.` 접두) | HTTP | 라인 | 우리 앱-분석 매핑 |
|--|--|--|--|--|
| login | `login.Login` | POST(form) | 162, 695-739 | `login.Login` (§2.3, 세션 부트스트랩) |
| code(암호키) | `common.code.do` | POST(form) | 173, 677-693 | `common.code.do` `app.login.cphd` |
| logout | `common.logout` | GET | 163, 741-744 | ※ 우리 G11은 `login.Logout` — **경로 다름** |
| search_schedule | `seatMovie.ScheduleView` | POST(query params) | 164, 790-819 | `seatMovie.ScheduleView` (검색, act_8/Sid/DynaPath) |
| reserve | `certification.TicketReservation` | **GET(query params)** | 165, 841-917 | Flow A 멤버 hold |
| cancel | `reservationCancel.ReservationCancelChk` | POST(form) | 166, 1060-1075 | Flow B **step2만** |
| pay | `payment.ReservationPayment` | POST(form) | 171, 1017-1058 | Flow C 메인 결제 |
| refund | `refunds.RefundsRequest` | POST(form) | 172, 1077-1097 | Flow D 실행 |
| myticketlist | `myTicket.MyTicketList` | GET | 168, 919-962 | 발권 티켓 목록(read) |
| myticketseat | `refunds.SelTicketInfo` | GET | 167, 949 | 티켓 좌석 상세(read) |
| myreservationview | `reservation.ReservationView` | GET | 169, 964-993 | 예약 목록(read) |
| myreservationlist | `certification.ReservationList` | GET | 170, 995-1015 | 예약 상세/좌석(read, G12) |

**메서드 주의점**: `search_train`은 POST이지만 `params=`(쿼리스트링)로 전송
(`ktx.py:819`), `reserve`는 **GET + 쿼리스트링**(`ktx.py:909`). 결제/취소/환불만
POST + form body(`data=`). 즉 예약 hold가 GET이라는 점이 우리 가정(POST)과 다름 —
아래 §5 참조.

---

## 3. 로그인 / 인증

- **엔드포인트**: `login.Login` (POST form, `ktx.py:695-739`).
- **입력 플래그 추론**(`ktx.py:701-707`): 이메일 정규식 매치 → `txtInputFlg="5"`,
  전화번호(`\d{3}-\d{3,4}-\d{4}`) → `"4"`, 그 외(멤버십번호) → `"2"`. 우리
  `session.py:23-29`와 동일 로직.
- **비밀번호 암호화 스킴**(`__enc_password`, `ktx.py:677-693`) — 우리 `crypto.py:41-52`
  와 **완전 일치, RESOLVED/CONFIRMED**:
  1. `common.code.do`에 `{"code":"app.login.cphd"}` POST → 응답 `strResult=="SUCC"`
     이면 `app.login.cphd.idx`(→ 로그인 바디 `idx`)와 `app.login.cphd.key` 획득.
  2. `AES-CBC(key=key.encode(), iv=key[:16].encode())` 로 PKCS-block padding한
     비밀번호를 암호화.
  3. **이중 Base64**: `b64encode(b64encode(ciphertext))` → `txtPwd`.
  - 즉 `base64_nowrap(base64_default(AES-CBC-PKCS5(pw, key=login.key, iv=key[:16])))`.
- **로그인 바디**(`ktx.py:712-719`): `Device`, `Version`, `txtMemberNo`(=id),
  `txtPwd`(암호문), `txtInputFlg`, `idx`. DynaPath 경로이므로 추가로 `Sid`도 포함
  (`ktx.py:720-721`). **`Key`는 로그인 바디에 없음.**
- **Device/Version/Key 값**: `_device="AD"`, `_version="250601002"`,
  `_key="korail1234567890"` (`ktx.py:642-644`).
- **세션/쿠키(JSESSIONID)**: 명시적 쿠키 처리 코드 없음 — `requests`/`curl_cffi`
  세션 객체의 쿠키 jar가 `JSESSIONID`를 자동 보관·재전송(`ktx.py:635-639`). 우리
  `httpx.Client` jar 방식과 동일 개념.
- **로그인 응답 파싱**(`ktx.py:727-737`): `strResult=="SUCC"` && `strMbCrdNo` 존재 →
  `strMbCrdNo`(멤버십), `strCustNm`(이름), `strEmailAdr`, `strCpNo`(전화).
  주목: `self._key = j['Key']` 라인이 **주석 처리**(`ktx.py:728`)되어, `Key`는 계속
  정적값 `korail1234567890`을 사용. (서버가 세션마다 새 Key를 주더라도 무시.)
- **에러 코드 맵**(`ktx.py:493-512`): `P058`=NeedToLogin, `{P100,WRG000000,WRD000061,
  WRT300005}`=NoResults, `{IRT010110,ERR211161}`=SoldOut.

---

## 4. NetFunnel (가상대기열)

**핵심 발견: 코레일(KTX) 측은 NetFunnel 게이트를 실제로 사용하지 않는다.**

- `NetFunnelHelper` 클래스는 `ktx.py:523-625`에 정의되어 있고 `Korail.__init__`에서
  인스턴스화됨(`self._netfunnel = NetFunnelHelper()`, `ktx.py:640`).
- 그러나 **`NetFunnelHelper.run()`은 `ktx.py` 어디에서도 호출되지 않음.** repo 전체
  grep 결과 `.run()` 호출은 `srt.py:819, 987`(SRT 예약·결제 바디의 `netfunnelKey`)
  에만 존재. `ktx.py`에서 `_netfunnel`은 오직 `clear()`만 호출(`ktx.py:1100-1101`).
- 즉 코레일의 `reserve()`(`ktx.py:841-917`)·`pay_with_card()`(`ktx.py:1017-1058`)
  요청 바디에는 **NetFunnel 키가 전혀 들어가지 않는다.** SRT는 예약·결제 모두
  `netfunnelKey`를 넣지만(대조), 코레일은 넣지 않는다.
- NetFunnelHelper의 파라미터도 `sid="service_1", aid="act_8"` **하나뿐**
  (`ktx.py:601-608`) — 검색/예매용 `act_8`만 있고 **결제용 `act_18`은 아예 없음.**
  opcode는 `getTidchkEnter=5101`, `chkEnter=5002`, `setComplete=5004`
  (`ktx.py:530-534`), 응답 상태 `200`=PASS/`201`=대기/`502`=완료.
- 결론: srtgo_plus는 코레일 예약/결제를 **NetFunnel 없이** 성공시킨다(적어도 이
  코드가 작성/검증된 시점 기준). 우리 분석의 `act_18` 결제 게이트를 **구현하지도,
  검증하지도 않음** → 갭 해소 불가. 다만 "코레일 pay는 NetFunnel 토큰 없이도
  서버가 수락한다"는 **반례 데이터 포인트**로서 의미가 있음(§9 참조).
- macro 대응은 NetFunnel이 아니라 `x-dynapath-m-token`으로 처리(§7).

---

## 5. 예약(RESERVATION) 요청 바디 추출

`reserve()` (`ktx.py:841-917`) 전체 바디 (`data`, `ktx.py:864-904`), GET 쿼리스트링:

**공통/제어 키**
- `Device="AD"`, `Version="250601002"`, `Key="korail1234567890"`
- `txtMenuId="11"`
- `txtJobId = "1101"`(좌석 예약) / `"1102"`(예약대기) — 좌석 가능 여부로 분기
  (`reserving_seat`, `ktx.py:844`, 869)
- `txtGdNo=""`, `hidFreeFlg="N"`, `txtTotPsgCnt=cnt`(승객 합계)
- `txtSeatAttCd1..5 = "000","000","000","015","000"` (`ktx.py:874-877`) — `txtSeatAttCd4`
  만 `"015"`(우리 template와 동일 pin)
- `txtStndFlg="N"`(입석 여부), `txtSrcarCnt="0"`(지정 차량수 0 = 좌석 자동배정)
- `txtJrnyCnt="1"`(여정 수)

**여정(leg) 1 키** (`ktx.py:881-892`) — 레거시 `O*` 스타일 `txt*1`:
- `txtJrnySqno1="001"`, `txtJrnyTpCd1="11"`
- `txtDptDt1=train.dep_date`, `txtDptRsStnCd1=train.dep_code`, `txtDptTm1=train.dep_time`
- `txtArvRsStnCd1=train.arr_code`
- `txtTrnNo1=train.train_no`, `txtRunDt1=train.run_date`
- `txtTrnClsfCd1=train.train_type`, `txtTrnGpCd1=train.train_group`
- `txtPsrmClCd1 = "2"`(특실) / `"1"`(일반실) — `is_special_seat` 결정 로직 `ktx.py:846-858`
- `txtChgFlg1=""`

**여정 2 키**(`ktx.py:893-903`): `txtJrnySqno2..txtChgFlg2` 전부 `""`(빈 여정 placeholder).

**승객 행 키** (`Passenger.get_dict`, `ktx.py:406-415`, 1-based index로 반복 추가
`ktx.py:906-907`):
- `txtPsgTpCd{i}` = 유형코드(성인 `"1"`, 어린이/유아 `"3"`, 경로 `"1"`, 장애 `"1"`)
- `txtDiscKndCd{i}` = 할인유형(`"000"` 기본, 유아 `"321"`, 경로 `"131"`, 장애1-3 `"111"`,
  장애4-6 `"112"`) — `ktx.py:418-457`
- `txtCompaCnt{i}` = 인원수
- `txtCardCode_{i}`, `txtCardNo_{i}`, `txtCardPw_{i}` = 할인카드(밑줄 포함 키명 주의)

**응답 파싱**(`ktx.py:912-915`): `_result_check` 통과 후 `h_pnr_no`(예약번호) 추출 →
곧바로 `self.reservations(rsv_id)` 호출로 예약 상세를 재조회해 `Reservation` 객체 반환.
`Reservation`은 응답에서 `h_pnr_no`(rsv_id), `h_tot_seat_cnt`, `h_ntisu_lmt_dt/tm`
(구입기한), `h_rsv_amt`(가격), `txtJrnySqno`(기본 "001"), `txtJrnyCnt`(기본 "01"),
`hidRsvChgNo`(기본 "00000")를 읽음(`ktx.py:303-320`).

### 5.1 우리 정적분석이 지목한 "누락 키"에 대한 실측 결론

- **`pnrNo`**: srtgo_plus reserve 바디에 **없음.** 신규 멤버 hold는 `pnrNo` 없이
  성공. (엔드포인트는 우리와 동일한 `certification.TicketReservation`.)
- **`pbepInfo`**: **없음.** (정부 인증 전용 필드로, 일반 예약엔 불필요.)
- **`OSrcar` 지정좌석 키**(`txtSrcarNo{i}`/`txtSeatNo{i}`): **없음.** `txtSrcarCnt="0"`
  으로 **좌석 자동배정만** 수행. srtgo_plus는 특정 좌석 선택을 하지 않음 → 지정좌석
  바디 형태는 여기서 확인 불가.
- 즉 srtgo_plus의 예약 바디 = **일반실/특실 자동배정, `O*`(txt*) 레거시 캐리어**.
  `pnrNo`/`pbepInfo`가 없어도 동작한다는 실증. 새 `R*`(`x_i` 키) 캐리어는 미사용.

---

## 6. 결제(PAYMENT) — srtgo_plus는 카드 결제를 수행함

**srtgo_plus는 예약-only가 아니라 실제 카드 결제까지 수행한다.**
`pay_with_card()` (`ktx.py:1017-1058`), POST form → `payment.ReservationPayment`.

바디(`ktx.py:1030-1051`):

| 필드 | 값 | 비고 |
|--|--|--|
| `Device`/`Version`/`Key` | 공통 envelope | |
| `hidPnrNo` | `rsv.rsv_id` | 예약번호 |
| `hidWctNo` | `rsv.wct_no` | 발권창구번호(예약조회 `ticket_info`의 `h_wct_no`, `ktx.py:1009`) |
| `hidTmpJobSqno1` | `"000000"` | |
| `hidTmpJobSqno2` | `"000000"` | |
| `hidRsvChgNo` | `"000"` | |
| `hidInrecmnsGridcnt` | `"1"` | 결제수단 행 수 |
| `hidStlMnsSqno1` | `"1"` | 결제수단 순번 |
| `hidStlMnsCd1` | `"02"` | **02 = 카드** (우리 코드표와 일치) |
| `hidMnsStlAmt1` | `str(rsv.price)` | 결제 금액 |
| `hidCrdInpWayCd1` | `"@"` | 카드입력방식 |
| **`hidStlCrCrdNo1`** | `card_number` | **카드번호(RAW PAN, 서버 암호화 없음!)** |
| **`hidVanPwd1`** | `card_password` | **카드 비밀번호 앞 2자리(RAW)** |
| **`hidCrdVlidTrm1`** | `card_expire` | 유효기간 YYMM |
| `hidIsmtMnthNum1` | `installment` | 할부개월(기본 0) |
| `hidAthnDvCd1` | `card_type` | `"J"`(개인/주민 6자리) / `"S"`(법인/사업자 10자리), `srtgo.py:391` |
| `hidAthnVal1` | `birthday` | 인증값(생년월일 등) |
| `hiduserYn` | `"Y"` | 회원 결제 플래그 |

**중대 발견 — RAW PAN 직접 전송**: srtgo_plus는 카드번호/비밀번호를
**`shinhan.Encrypt.do`/`common.encrypt.do`로 서버 사전암호화하지 않고** 평문 PAN을
`hidStlCrCrdNo1`에 그대로 실어 보낸다. 우리 갭플랜 §3.7.3/§4.4의 "PG 서버측 encrypt
후 encValue만 전송" 가정과 **다르다**. 즉 실동작 클라이언트는 raw PAN을
`ReservationPayment`가 수락함을 보여준다. (우리 안전모델은 여전히 fake-card +
encrypt 경로를 유지하는 게 안전하나, 필드명은 여기서 확정됨.)

- 결제 응답 파싱(`ktx.py:1056-1057`): `_result_check` 통과 시 `True`.
- 오케스트레이션(`srtgo.py:381-393, 691-698, 899-904`): keyring에 저장된 카드
  (`number/password/birthday/expire`)를 읽어 `pay_with_card` 호출. 예약대기
  (`is_waiting`)면 결제 스킵. 결제는 예매 성공 직후 또는 "예약확인" 메뉴에서 수동.
- **NetFunnel `act_18` 없음**(§4). 결제 POST에 대기열 토큰 미포함.

---

## 7. Anti-bot — DynaPath / Sid / User-Agent / MACRO

- **`x-dynapath-m-token` 헤더** (README가 말하는 srtgo_plus의 핵심 신규 기능):
  `DynaPathMasterEngine`(`ktx.py:54-160`)이 요청마다 생성. `generate_token(device_id,
  ts, rand)`가 `ai=com.korail.talk&di={device_id}&as=%5B38ff…%5D&…&dm=SM-S928N&
  st=Android&sv=v1` 평문을 커스텀 Base-N 인코딩(`encode_normal_be`, 테이블
  `3FE9jgRD4…`)하여 `bEeEP…` 토큰 문자열 생성.
- **적용 경로 allowlist**(`DYNAPATH_PATHS`, `ktx.py:44-51`) = 우리 6-path와 동일:
  `TicketReservation`, `NonMemTicket`, `ScheduleView`, `ScheduleViewSpecial`,
  `trn.prcFare.do`, `login.Login`. `_get_auth_headers_and_sid`(`ktx.py:666-675`)가
  URL이 이 목록에 있으면 헤더 + Sid 생성.
- **중요 — srtgo_plus는 토큰을 "항상" 보낸다**: 앱과 달리 `IS_MACRO_ACTIVE`
  조건 없이, 해당 6경로면 무조건 `x-dynapath-m-token`을 붙인다(login/search/reserve
  가 모두 `_get_auth_headers_and_sid` 호출). 이는 우리 갭플랜 §5.10("앱은 macro
  활성 시에만 전송, 기본 OFF") 과 **반대**. README도 "코레일 anti-bot 정책 변경
  대응으로 토큰 엔진 구현"이라 명시 → **현행 실예약에는 토큰 전송이 필요**하다는
  신호. (우리는 기본 OFF + opt-in을 재검토할 근거.)
- **`Sid` 토큰**(`_generate_sid`, `ktx.py:661-664`):
  `base64(AES-CBC(key=b"2485dd54d9deaa36", iv=동일키, plaintext="AD"+ts)) + "\n"`.
  우리 `crypto.py:55-62`의 `Sid = AndroidBase64(AES-CBC(SID_KEY,"AD"+ts))`와 동일
  구조이며 **SID 키 구체값 `2485dd54d9deaa36`**(16바이트)를 확인. 단 실제 바디에
  `Sid`를 넣는 곳은 **로그인뿐**(`ktx.py:720-721`); search/reserve는 sid를 계산만
  하고 바디에 넣지 않음(헤더 토큰만 부착). → 우리 "예약 POST는 Sid 미포함" 가정과
  일치.
- **User-Agent**(`ktx.py:32`): `"Dalvik/2.1.0 (Linux; U; Android 13; SM-S928N
  Build/UP1A.231005.007)"` — 앱-충실 Dalvik UA. 우리 갭플랜 §5.9(현재 기본 UA가
  `korail-mobile-api/0.2.0`로 비앱적)의 **구체 대체값 확정**. `device_id=
  "558a4f02041657ea"`(`ktx.py:632`).
- **기본 헤더**(`ktx.py:34-40`): `Content-Type: application/x-www-form-urlencoded;
  charset=UTF-8`, `Host: smart.letskorail.com`, `Connection: Keep-Alive`,
  `Accept-Encoding: gzip`.
- **MACRO 에러 핸들링**(`srtgo.py:753-761`): `KorailError`의 code/msg에 `"MACRO"`가
  있으면 `rail.clear()`(netfunnel 키 클리어) 후 재시도. README "KTX MACRO ERROR
  핸들링 개선".
- **`curl_cffi` 임퍼서네이션**: 설치 시 `curl_cffi.Session()` 사용(`ktx.py:635-638`),
  NetFunnel은 `impersonate="chrome131_android"`(`ktx.py:544`)로 TLS 지문 위장.

---

## 8. 취소 / 환불

### 8.1 취소 (`cancel`, `ktx.py:1060-1075`) — **단일 호출**

- 엔드포인트: `reservationCancel.ReservationCancelChk` (POST form).
- **우리 §3.B의 2-step(`ReservationCancel` → `…Chk`)과 달리, srtgo_plus는
  `ReservationCancelChk` 하나만 호출**(step1 생략).
- 바디(`ktx.py:1063-1071`): `Device/Version/Key`, `txtPnrNo=rsv.rsv_id`,
  `txtJrnySqno=rsv.journey_no`, `txtJrnyCnt=rsv.journey_cnt`,
  `hidRsvChgNo=rsv.rsv_chg_no`.
- 상수 차이: 값들이 **하드코딩이 아니라 예약조회 응답에서 읽은 실제값**.
  기본 폴백은 `txtJrnySqno="001"`, `txtJrnyCnt="01"`, `hidRsvChgNo="00000"`
  (`ktx.py:315-317`) — 우리 갭플랜의 `"0001"`/`"000"`과 **자릿수가 다름**. 응답값을
  그대로 쓰는 것이 안전.

### 8.2 환불 (`refund`, `ktx.py:1077-1097`) — **단일 실행 호출**

- 엔드포인트: `refunds.RefundsRequest` (POST form).
- 바디(`ktx.py:1078-1093`):

| 필드 | 값(소스) | 비고 |
|--|--|--|
| `Device`/`Version`/`Key` | 공통 | |
| **`txtPrnNo`** | `ticket.pnr_no` | ⚠ 키명이 `txtPnrNo`가 아니라 **`txtPrnNo`**(P**r**n) |
| `h_orgtk_sale_dt` | `sale_info2` (=`h_orgtk_ret_sale_dt`) | |
| **`h_orgtk_sale_wct_no`** | `sale_info1` (=`h_orgtk_wct_no`) | 저장명은 wct_no, **전송명은 sale_wct_no** |
| `h_orgtk_sale_sqno` | `sale_info3` | |
| `h_orgtk_ret_pwd` | `sale_info4` | |
| `h_mlg_stl` | `"N"` | 마일리지 정산 |
| `tk_ret_tms_dv_cd` | `"21"` | 환불 구분 |
| `trnNo` | `ticket.train_no` | |
| `pbpAcepTgtFlg` | `"N"` | |
| `latitude` | `""` | GPS(빈값) |
| `longitude` | `""` | GPS(빈값) |

- **`h_orgtk_sale_wct_no` 전송명 = 우리 §5.5 wire-rename 트랩을 직접 확증.**
  또한 `latitude/longitude`(빈값), `tk_ret_tms_dv_cd="21"`, `pbpAcepTgtFlg="N"` 확정.
- 단 `txtPrnNo`(P**r**n) 오탈자스러운 키명은 우리 §3.D의 `txtPnrNo`와 다름 — 실서버
  필드명일 가능성(동작 도구)과 오타 가능성 **양쪽 다 플래그**. 라이브 검증 필요.
- SelTicketInfo(상세)·CommissionView(수수료 미리보기)는 `refund()` 자체엔 없음.
  상세/좌석 조회는 `tickets()`(`ktx.py:919-962`)가 `refunds.SelTicketInfo`로 별도
  수행. CommissionView(수수료 프리뷰)는 srtgo_plus 미구현 → 곧바로 실행 호출.

### 8.3 체크인 (self check-in)

- **srtgo_plus 미구현.** `checkin.*` 엔드포인트·메서드 전무. → 관련 갭 데이터 없음.

---

## 9. 갭플랜 해소 맵 (RELEASE_GAP_PLAN mutation 항목별)

각 항목이 srtgo_plus로 **해소(RESOLVED)** 되는지, 구체 형태와 함께 판정.

| 갭 항목 | 판정 | 핵심 근거(ktx.py) |
|--|--|--|
| **예약 seat-key `pnrNo`** (§5.3) | **RESOLVED (반증형)** | reserve 바디에 `pnrNo` **없음** → 신규 멤버 hold는 불필요. `ktx.py:864-904` |
| **예약 seat-key `pbepInfo`** (§5.3) | **RESOLVED (반증형)** | reserve 바디에 `pbepInfo` **없음**. 일반예약 불필요. `ktx.py:864-904` |
| **지정좌석 `OSrcar`(txtSrcarNo/txtSeatNo)** (§5.4) | **NOT** | srtgo_plus는 `txtSrcarCnt="0"` 자동배정만. 지정좌석 미지원 → 형태 확인 불가. `ktx.py:879` |
| **예약 바디 캐리어 전체 형태** (§3.A) | **RESOLVED** | 레거시 `O*`(txt*1/txt*2 여정 + `txtPsgTpCd{i}`… 승객행) 완전 추출. §5 표. `ktx.py:864-907` |
| **txtJobId 분기** | **RESOLVED** | `1101`(좌석)/`1102`(대기). `ktx.py:869` |
| **NetFunnel `act_18` 결제 게이트** (§3 NetFunnel) | **NOT (반례 제공)** | 코레일은 NetFunnel 미배선(`run()` 미호출), 결제에 토큰 없음. `act_8`만 존재, `act_18` 없음. 결제가 게이트 없이 수락됨을 시사. `ktx.py:640,1017-1058`; `run()` 부재 |
| **NetFunnel act_14 예약 게이트** | **NOT** | 예약도 NetFunnel 미사용(코레일). `ktx.py:841-917` |
| **결제 = 카드결제 수행 여부** (§6) | **RESOLVED — 카드결제 수행함** | `pay_with_card` → `payment.ReservationPayment`. `ktx.py:1017-1058` |
| **결제 카드 필드명(redaction 갭 §4.6)** | **RESOLVED** | `hidStlCrCrdNo1`/`hidVanPwd1`/`hidCrdVlidTrm1`/`hidIsmtMnthNum1`/`hidAthnDvCd1`/`hidAthnVal1` + 행제어 `hidStlMnsCd1="02"`/`hidMnsStlAmt1`/`hidCrdInpWayCd1="@"`/`hidPnrNo`/`hidWctNo`/`hidTmpJobSqno1/2`/`hidRsvChgNo`/`hiduserYn`. `ktx.py:1030-1051` |
| **카드 PG 서버암호화(encValue)** (§3.7.3) | **반증** | srtgo_plus는 **RAW PAN 직접 전송**, `shinhan.Encrypt.do`/`common.encrypt.do` 미사용. 서버가 raw 수락. `ktx.py:1044` |
| **취소 2-step 순서** (§3.B) | **부분/반증** | srtgo_plus는 **`ReservationCancelChk` 단일 호출**만으로 취소. step1 생략. `ktx.py:1060-1075` |
| **취소 파라미터** | **RESOLVED** | `txtPnrNo`/`txtJrnySqno`/`txtJrnyCnt`/`hidRsvChgNo` — 값은 예약응답에서 read(폴백 `001`/`01`/`00000`). `ktx.py:1063-1071,315-317` |
| **환불 RefundsRequest 형태** (§3.D) | **RESOLVED** | 전체 필드 §8.2 표. 단일 실행 호출. `ktx.py:1077-1097` |
| **환불 wire-rename `h_orgtk_sale_wct_no`** (§5.5) | **RESOLVED (확증)** | 저장 wct_no → 전송 `h_orgtk_sale_wct_no`. `ktx.py:1084` |
| **환불 GPS latitude/longitude** | **RESOLVED** | 둘 다 빈문자열 전송. `ktx.py:1091-1092` |
| **환불 PNR 필드명** | **주의(불일치)** | srtgo_plus는 `txtPrnNo`(우리 `txtPnrNo`와 다름) — 라이브 검증 필요. `ktx.py:1082` |
| **체크인 psbFlg/reg/info/cnc (§3.E)** | **NOT** | srtgo_plus 미구현. 데이터 없음 |
| **로그인 AES 이중-Base64** (crypto) | **RESOLVED (확증)** | `common.code.do`(`app.login.cphd`) → AES-CBC(key, iv=key[:16]) → b64(b64()). `ktx.py:677-693` |
| **User-Agent 앱-충실값** (§5.9) | **RESOLVED** | `Dalvik/2.1.0 (…Android 13; SM-S928N…)`. `ktx.py:32` |
| **DynaPath 토큰 기본 전송 여부** (§5.10) | **반증(신호)** | srtgo_plus는 6경로에 **항상 전송** — 현행 예약에 필요함을 시사. `ktx.py:666-675` |
| **Sid 키/구조** | **RESOLVED** | `AES-CBC(b"2485dd54d9deaa36", iv=동일, "AD"+ts)` + b64 + `\n`; 로그인 바디에만 부착. `ktx.py:661-664,720` |
| **logout 서버 무효화** (G11) | **부분** | srtgo_plus는 `common.logout`(GET) 사용 — 우리 G11의 `login.Logout`과 **경로 다름**. `ktx.py:163,741-744` |

### 요약 판단

- srtgo_plus는 우리 mutation 갭 중 **예약 바디 형태·결제 카드 필드명·환불 형태·
  로그인 crypto·UA·Sid**를 실동작 코드로 확정해 준다.
- 반면 **지정좌석(OSrcar), NetFunnel act_18/act_14, 체크인**은 미구현이라
  해소되지 않는다. 오히려 코레일은 **NetFunnel 자체를 안 쓰고**(SRT만 사용),
  **카드도 raw PAN을 직접 전송**한다는 점이 우리 앱-분석 가정과 어긋나는 중요한
  반례다 — 라이브 1회 검증으로 실제 서버 요구사항(토큰/암호화 강제 여부)을 확인
  후 계약을 확정할 것.
- **주의 트랩**: `txtPrnNo`(환불 PNR, P**r**n) / `common.logout` vs `login.Logout` /
  취소 단일-호출 vs 우리 2-step — 세 지점은 srtgo_plus와 우리 분석이 갈린다.
