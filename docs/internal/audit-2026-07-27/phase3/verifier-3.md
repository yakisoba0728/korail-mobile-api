# 코레일톡 3차 검증 (반증자) — verifier-3

> 이 파일은 같은 경로에 있던 이전 판본(18,795바이트, 타임스탬프 01:51)을
> **의도적으로 대체**한 것이다(재실행 결과이지 다른 에이전트 산출물의 훼손이 아니다).

대상: korail-mobile-api (이 저장소)
저장소는 읽기만 했다. 파일 생성/수정/git 조작 없음. 파이썬 임포트는
`PYTHONDONTWRITEBYTECODE=1` 로 저장소 밖(scratchpad)에서 실행했다.

## 판정 규약 (4건의 "결함 아님" 주장 처리)

K1-01 / P2SAF-07 / P2SAF-13 / P2CRO-11 은 스스로 "결함이 아니다"를 주장한다.
이런 항목은 **주장의 사실적 내용이 성립하는가**로 판정한다. 사실이 맞으면
CONFIRMED + `corrected_severity: info`. 21건 전체에 동일하게 적용했다.

## 선행 확인 — redact_payload 의 매칭 의미론 (K5-02 / P2SAF-02 / P2SAF-05 공통)

`redaction.py:12-14` 는 `SENSITIVE_KEYS` 를 casefold 한 frozenset 으로 만들고,
`redact_payload`(:340) `redact_value`(:291) `redact_url`(:280) 는 모두
`name.casefold() in SENSITIVE_KEYS` — **완전일치**만 한다. 접두사/부분일치/정규식
키 매칭은 없다. `redact_text`(:263) 의 `CARD_RE` 는 13~19자리 숫자만 잡는다.
따라서 "철자가 다르면 마스킹되지 않는다"는 세 주장의 전제는 성립한다.

---

## K1-01 — 회원관리 5개 미구현 → CONFIRMED (info)

- 앱: `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:13`
  `certMember`(login.userCheck), `:20` `loginAthnReg`, `:24` `loginAthnRmv`,
  `:33` `memberCheck`(joinCfm), `:37` `memberDrop`(mbSced) — 5개 모두 실재.
- 라이브러리: `grep -rniE 'userCheck|loginAthnReg|loginAthnRmv|joinCfm|mbSced' src/` 0건.
- 문서: `docs/deep-dive/full-api-analysis-2026-07-20.md:2692-2696` 이 5개를
  각각 사유와 함께 열거("Account-linking write", "`member-drop` excluded" 등).
  `docs/RELEASE_GAP_PLAN.md:442-447` "Out of core v1" 에 member-drop /
  account link-unlink 명시.
- 결론: 사실 전부 성립. 결함 아님. info.

## K3-01 — 장바구니 담기 미구현 → CONFIRMED (info, 심각도 하향)

- 앱: `.../dao/cart/CartService.java:11-13`
  `@POST("/classes/com.korail.mobile.cart.addCartList") addCart(Device,Version,Key,hidPnrNo)`.
- 라이브러리: `grep -rniE 'addCartList|add_cart|AddCart|addProduct' src/` 0건.
- 문서: `docs/api-status-by-service.md:180` — `addCart` / 미실행 / 비고 "운영 상태 변경 가능".
- 이것은 **상태변경(write)** 이고, 이 패키지의 뮤테이션 표면은 `safety.py:205-280`
  의 8개 라우트로 의도적으로 한정되어 있다. 게이트 구멍이 아니라 범위 경계다.
- 결론: 사실 성립, 은닉 없음. medium → **info**.

## K3-03 — reservation.tripChgPrsC.do 미구현 → CONFIRMED (info, 하향)

- 앱: `.../dao/reservation/ReservationService.java:23-25`
  `getTicketChangeReservation` — trvlKndCd/totPrnb/isePrnb/stndSeatFlg/
  intgTktIseFlg/prcFareReCalcFlg/tmpJobSqno/alcSeatDmnPsDvCd/jrny2Cnt/psg2Cnt/
  ctlDvCd/frcSaleRsnCont + `@FieldMap × 6`. (주장은 :24-26, 1줄 드리프트.)
  `.../reservation/TCReservationDao.java:24,26,30` 필드 실재.
  `analysis/apktool/res/values/strings.xml:432` `승차권 변경`.
- 라이브러리: `grep -rniE 'tripChgPrsC|TCReservation|trvlKndCd|jrny2Cnt|psg2Cnt' src/` 0건.
- 문서: `docs/RELEASE_GAP_PLAN.md:278`(엔드포인트 카탈로그 행), `:867`(P4 체크리스트)
  에 추적 중. 선행 read `tripChgOgtk` 도 G4(:131)로 등재.
- 결론: 사실 성립, 추적된 갭. low → **info**.

## K4-01 — getTicketList 비구조화 → PARTIAL (low)

- 앱: `.../dao/myTicket/TicketListDao.java` (396줄) 에 ReservationList →
  TicketList → TrainInfo 중첩 DTO 실재.
- 라이브러리: `client.py:1487-1509` 가 `self.http.post_form(...)` 결과를 그대로 반환.
  `models.py:20-25` BaseKorailResponse 는 h_msg_cd/h_msg_txt/str_result/raw 4필드.
  read_parsers/read_models 에 MyTicketList 파서 없음(확인).
- **주장의 부정확한 부분**: `post_form` 의 반환 타입은 `BaseKorailResponse`
  (`http.py:153-162`, `:219` `parse_base_response(payload, ...)`)이지 "raw dict"가
  아니다. 봉투 파싱은 수행되며 43개 필드는 `.raw` 로 전부 접근 가능하다.
  타입 안전한 노출이 없다는 지적만 맞다.
- 공개 메서드 중 bare BaseKorailResponse 반환은 `get_ticket_list` 하나뿐이라는
  부분은 맞다(다른 하나 `client.py:1418` 은 private `_post_schedule_view`).
- 결론: PARTIAL, medium → **low** (읽을 수 없는 필드는 없다).

## K4-06 — pbpTkWdrw 미구현 → PARTIAL (info, 하향)

- 앱: `.../dao/ticket/TicketService.java:70-72`
  `@POST("/classes/com.korail.mobile.tk.pbpWdrw.do") pbpTkWdrw(Device,Version,Key,pbpCnt:int,pbpRsvNo:List,pnrNo:List)`.
  DAO `.../dao/ticket/PbpTkWdrwDao.java` 실재.
- 라이브러리: pbpWdrw 0건. 짝인 조회는 `client.py:1061`, `safety.py:152`,
  exact-field 핀 `safety.py:1012-1013` 로 완전 구현 — 여기까지 맞다.
- **주장의 틀린 부분**: "명시적 제외 문서 없음". 실제로는
  `docs/api-status-by-service.md:537` 이 `pbpTkWdrw` 를 미실행 / "운영 상태 변경 가능"
  으로 등재하고, `docs/deep-dive/full-api-analysis-2026-07-20.md:2761` 이 Write 로
  분류하며, `docs/api-endpoints.md:357`, `docs/deep-dive/api-contracts.md:5127`
  에도 있다. write 이므로 8개 뮤테이션 라우트 밖인 것이 설계와 일치한다.
- 결론: PARTIAL, low → **info**.

## K5-02 — hidRsvChgNo 마스킹 누락 → CONFIRMED (low, 하향)

- 앱: `.../dao/payment/PaymentService.java:12-14` `@Field("hidRsvChgNo")`.
  값 출처는 라이브러리 주석(`mutation_payloads.py:1330-1341`)이 인용한
  `V4/b.java:41` 표현식(첫 여정의 `h_rsv_chg_no`).
- 라이브러리: `mutation_payloads.py:1398` `"hidRsvChgNo": _echoed_reservation_change_no(hold)`,
  `:1306-1314` 가 hold 의 첫 여정 `reservation_change_no` 를 그대로 echo(없으면 "000").
  `redaction.py` SENSITIVE_KEYS 에 `h_rsv_chg_no`(:111) / `reservation_change_no`(:65)
  는 있으나 **`hidRsvChgNo` 는 없음** — 완전일치 매칭이므로 평문 잔류.
  `consent.py:130-131` MutationPreview 는 redact_payload 만 통과.
  문서 약속: `client.py:1891`, `:1957` "card and identity fields are redacted".
  테스트 `tests/test_real_card_payment.py:366-377` redacted-key 목록에 hidRsvChgNo 없음.
- 심각도: PNR/창구번호/tmpJobSqno1·2 는 모두 마스킹되어 있고, 노출되는 값은
  예약변경 시퀀스(통상 "000"급 소수 자릿수)로 단독 악용가치가 거의 없다.
  문서가 약속한 범위를 벗어난 것은 사실. medium → **low**.

## K6-03 — h_pbp_acep_tgt_flg 파싱경로 부재 + 전송 N 고정 → CONFIRMED (medium)

- 앱: `.../dao/refund/TicketDetailDao.java`(주장은 경로를 `dao/ticket/` 로 적었으나
  실제는 `dao/refund/`; 줄번호는 일치) `:250` 필드, `:374` getter, `:498` setter.
  함께 지목된 `:228 addSrvCancel`, `:229 addSrvFlg`, `:242 h_dlay_flg`,
  `:243 h_dlay_tk_flg`, `:266 mlgSaveFlg` 전부 실재.
  `.../ui/ticket/ticketReturn/a.java:430-431`
  `r3.getH_pbp_acep_tgt_flg()` → `r5.setPbpAcepTgtFlg(...)`.
  `.../dao/refund/RefundDao.java:144` `t.e("PbpAcepTgtFlg : " + ...)` (주장은 :132, 드리프트).
- 라이브러리: `read_parsers.py:2679-2698` `_REFUND_TICKET_DETAIL_FIELDS` 에
  h_pbp_acep_tgt_flg / h_dlay_flg / h_dlay_tk_flg / mlgSaveFlg / addSrvFlg /
  addSrvCancel 모두 없음. `grep -rn 'pbp_acep' src/` 0건 → 읽을 방법 자체가 없음.
  `mutation_payloads.py:1457` `"pbpAcepTgtFlg": "N"` 고정.
- 심각도: PBP 대상 승차권에 한정된 조건부 오류이고, 이 항목의 고유 기여는
  "파서 경로 부재"다(전송 고정값 자체는 P2CRO-12 가 포괄). high → **medium**.

## K7-01 — acpnMlgSpec 사각지대 → PARTIAL (info, 하향)

- 사실 성립 부분: `.../dao/mileage/MileageService.java:19-21`
  `acpnMlgSpec(Device,Version,Key,pnrNo)`, DAO `AcpnMlgSpecDao.java` 실재.
  `grep -rn 'acpnMlgSpec' src/` **0건** — 미구현 맞다.
  `safety.py:24-28` EXCLUDED 사유 주석은 5개만 열거, acpnMlgSpec 없음 — 맞다.
  `tests/test_loyalty_reads.py:44-50` WITHHELD_PATHS 5개 — 맞다.
  `docs/RELEASE_GAP_PLAN.md:126-139` G1~G12 에 없음 — 맞다.
- **주장의 핵심 명제가 무너짐**: "라이브러리·문서·테스트 어디에도 없음",
  "제외 사유가 한 번도 명시된 적 없는 사각지대", "시스템 어디에서도 인지되지 않고 있다".
  실제로는
  - `docs/api-status-by-service.md:323` — `acpnMlgSpec` / 미실행 / **비고
    "결제/간편결제/포인트/금전성 API"** (사유 명시).
  - `docs/api-endpoints.md:194`, `docs/deep-dive/full-api-analysis-2026-07-20.md:1140`,
    `docs/deep-dive/network-model-fields.md:1838-1884`,
    `docs/deep-dive/agent-reports/11-pass-mileage-xpoint-railplus.md:144,148,157`,
    `docs/deep-dive/webview-and-url-catalog.md:175` 전부 등재.
  - 테스트명 `test_only_the_two_password_free_loyalty_reads_are_reachable`
    (:76)은 **도달 가능한(reachable)** 로열티 read 가 2개라는 주장이며
    (`:77-85` 가 실제로 라우트 allowlist 도달성만 단언한다), "비밀번호 없는
    read 가 2개뿐"이라는 존재 주장이 아니다. "틀린 전제"라는 지적은 오독.
- 결론: 실제 미구현 read 갭은 맞으나 "인지되지 않은 맹점" 서사는 반증됨.
  PARTIAL, medium → **info**.

## K8-06 — DynaPath 403 판별의 경로 allowlist → REFUTED (info)

- 앱 오류처리: `.../network/BaseDaoHelper.java:54-92` — 확인. 403+forbidden 이면
  헤더를 훑어 `DynaPath-Result < 0` 이면 매크로거부. 경로 조건 없음. 여기까지 맞다.
- **결정적 반증 — 토큰 부착 지점**: `.../network/ExecuteDao.java:28` 이
  `{certification.TicketReservation, nonMember.NonMemTicket,
  seatMovie.ScheduleView, seatMovie.ScheduleViewSpecial, trn.prcFare.do,
  login.Login}` 6개 배열을 만들고 `:29-42` 에서 요청 URL 이 그중 하나를 포함할
  때만 `:47` `setRequestProperty("x-dynapath-m-token", ...)` 를 한다
  (그나마 `:26` `IS_MACRO_ACTIVE` 가 참일 때만; 이 값은 `I4/a.java:14` 에서
  false 로 시작해 `IntroActivity.java:663` 의 서버 코드 `isMacroEnable` 로 켜짐).
  즉 앱 자신의 모델에서 DynaPath 검문은 정확히 이 6경로에서만 성립한다.
- **smali 재확인**(jadx 상수 배열이므로 필수):
  `analysis/apktool/smali/com/korail/talk/network/ExecuteDao$1.smali:107`
  `sget-boolean v1, LI4/a;->IS_MACRO_ACTIVE:Z` 분기 아래
  `:115 trn.prcFare.do`, `:119 login.Login`, `:123 certification.TicketReservation`,
  `:127 nonMember.NonMemTicket`, `:131 seatMovie.ScheduleView`,
  `:135 seatMovie.ScheduleViewSpecial` 6개 리터럴, 그리고
  `:326 const-string v1, "x-dynapath-m-token"` 으로 헤더 부착. jadx 와 일치.
- 라이브러리 `constants.py:421-429` DYNAPATH_ALLOWLIST_PATHS 는 이 6개와 바이트 동일,
  `http.py:69-73` 의 세 조건은 앱의 모델을 그대로 재현한 것이다. 이 6경로 밖에서
  서버가 그 헤더를 내리면 오히려 출시된 앱이 먼저 깨진다.
- 결론: 분류상의 발산이 아니라 앱 모델의 정확한 이식. **REFUTED**, info.

## P2MIS-01 — ScheduleView 승객 5버킷 미지원 → CONFIRMED (low, 하향)

- 앱: `.../dao/seatMovie/SeatMovieService.java:14` `getRsvInquiry` 가
  `txtPsgFlg_1..5` 를 실제로 받는다(주장은 :12, 인터페이스 선언줄).
  `analysis/jadx/sources/u4/b.java:110-121` 8개 카운터,
  `:173-177` `setTxtPsgFlg_1(i9+i10+i16)` / `_2(i11+i12)` / `_3(i13)` /
  `_4(i14)` / `_5(i15)` — 합산 규칙 확인.
- 라이브러리: `payloads.py:298` `"txtPsgFlg_1": str(query.passengers)`,
  `:299-302` `_2.._5` 전부 상수 `"0"`.
  `models.py:270-277` TrainSearchQuery 는 `passengers: int` 하나뿐.
  대조군도 확인: `limousine_payloads.py:144-148` 은 5버킷 전부 파라미터화.
- 심각도: 전송 자체는 유효하고 실서버 성공 기록이 있다(주장도 인정). 좌석수
  조회 결과가 승객유형별로 갈릴 여지는 있으나 잘못된 요청은 아니다.
  medium → **low** (표현력 갭).

## P2MIS-05 — ScheduleViewSpecial 이 allowlist 에도 없음 → PARTIAL (info)

- 맞는 부분: `safety.py:69-203` KORAIL_READ_ONLY_ROUTES 에 seatMovie 항목은
  `:80 ScheduleView` 와 `:138 LimousineScheduleView` 뿐, ScheduleViewSpecial 부재.
  `assert_read_only_route`(`safety.py:1319-1331`)가 거부한다. 확인.
  `read_payloads.py:1465-1533` `_build_product_train_inquiry_form` 은 src 안에서
  호출되지 않는다(호출은 tests/test_next_variant_reads.py 뿐).
- **틀린/중복인 부분**:
  1. "'배선 보류'가 아니다" 라는 대비가 과하다. `tests/test_next_variant_reads.py:104-110`
     `test_route_and_holdback_boundary_is_exact` 가 `len(KORAIL_READ_ONLY_ROUTES)==58`,
     `not hasattr(KorailClient,"get_product_train_inquiry")`,
     `not hasattr(korail_mobile_api,"ProductTrainInquiryRequest")` 를 함께 고정한다.
     보류는 라우트·메서드·공개심볼 세 층 모두에서 의도적으로 테스트에 박혀 있다.
  2. "같은 패턴이 하나 더 있다 — ScheduleView 의 여행상품 변형(txtMenuId=41) 빌더"
     는 **같은 것을 둘로 센 것**이다. `_build_product_train_inquiry_form` 이 내는
     필드열(`txtGdNo`, `txtMenuId="41"`, Sid·txtGoTrnNo 없음)은
     `SeatMovieService.java:20` `getRsvProductInquiry`(=ScheduleViewSpecial) 및
     `.../seatMovie/ProductTrainInquiryDao.java:13` 의 인자열과 정확히 일치한다.
     별도의 ScheduleView 변형 빌더는 존재하지 않는다.
  3. "adult→_1/child→_2 단순 매핑" 지적은 약하다. 그 5개 필드는 앱에서도 5버킷이며
     limousine 쪽과 같은 그룹 파라미터화다(호출자가 adult 슬롯에 합산값을 넣으면 됨).
- 결론: PARTIAL, low → **info**.

## P2INC-07 — CardPayment.installment 기본값 "00" → CONFIRMED (low, 하향)

- 앱(smali, authoritative): `analysis/apktool/smali/K4/h.smali:48`
  `const-string v2, "0"` (INS_0 = 일시불). 나머지도 무패딩:
  `:76 "2"`, `:104 "3"`, `:132 "4"`, `:160 "5"`, `:188 "6"`, `:216 "12"`, `:244 "24"`.
- 사용처: `analysis/jadx/sources/v4/a.java:238-262` `getInstallmentType()` 가
  `hVar.getCode()` 반환, `:32/:84/:98/:108/:158` 이
  `paymentMethod.setHidIsmtMnthNum(1, ...)` 로 전송.
  포인트 결제 경로 `:288,296,308,339` 는 리터럴 `"0"`.
  `.../request/payment/PaymentMethod.java:60-61` 이 키를 `"hidIsmtMnthNum"+i` 로 조립.
  APK 에서 이 필드에 "00" 이 들어가는 경로는 발견되지 않음.
- 라이브러리: `mutation_models.py:311` `installment: str = "00"  # months; "00" = lump sum`,
  `mutation_payloads.py:1407` 이 그대로 전송.
- 심각도: 앱과의 바이트 불일치는 사실이고 결제 경로 기본값인 것도 맞다. 다만
  실패가 관측된 바 없고("00" 은 국내 VAN 계열에서 통용되는 일시불 표기이기도 하다)
  잘못되면 결제가 거절될 뿐 금액이 틀리지는 않는다. 1차의 low 가 타당.
  medium → **low**.

## P2INC-09 — txtSeatAttCd4 "015" 고정 → CONFIRMED (low)

- 앱(smali 재확인): `analysis/apktool/smali/K4/p.smali:75 "003"`(NORMAL_FREE),
  `:214 "015"`(DEFAULT), SECOND_FLOOR "018". jadx `K4/p.java:5,9,13` 과 일치.
  분기: `analysis/jadx/sources/c5/a.java:86-96` —
  `if (J.isFreeSeat(...)) setSeatAttCd4(i, p.NORMAL_FREE.getCode()); else {2층석 예외; else t2()}`.
  (주장은 `C5/a.java:85-97`; macOS 는 대소문자 무시라 같은 파일.)
- 라이브러리: `mutation_payloads.py:431,436`(병합) `:841,854`(직통/환승) 모두 `"015"`,
  검색측 `payloads.py:305` `txtSeatAttCd_4="015"`.
  `mutation_payloads.py:850-853` 이 이 선택을 명시적으로 문서화하고 있다.
- 검색이 015 를 보내므로 `t2()==SECOND_FLOOR` 는 거짓 → 2층석 분기는 도달 불가,
  재현 불가한 것은 자유석 분기 하나 — 주장 그대로 맞다.
- 결론: CONFIRMED, **low** 유지(자유석 예매 미지원이라는 능력 한계).

## P2SAF-02 — extend_discount_card 프리뷰의 saleDd 평문 → CONFIRMED (low, 하향)

- 앱: `.../dao/research/ResearchService.java:65-66`
  `@GET(".../reservation.dcntCrdExtn.do")` + `@Query saleWctNo/saleDd/saleSqno/tkRetPwd`.
- 라이브러리: `mutation_payloads.py:1614-1629` 가 네 개를 그대로 전송
  (`"saleDd"` 는 `:1618`). `redaction.py:26 saleWctNo`, `:27 **saleDt**`,
  `:28 saleSqno`, `:25 tkRetPwd` — `saleDd` 없음. 완전일치 매칭이므로 잔류.
  값이 `20260101` 형태면 CARD_RE(13~19자리)에도 걸리지 않는다.
- 심각도: 4분할 자격증명 중 유일하게 남는 것이 **판매일자**다. 창구번호·일련번호·
  반환비밀번호는 전부 마스킹되므로 남은 조각의 단독 가치는 거의 없다.
  정책 자기모순인 것은 맞다. medium → **low**.

## P2SAF-05 — 로그인 응답 PII 철자 미등재 → CONFIRMED (low, 하향)

- 앱: `.../dao/login/LoginDao.java` 의 LoginResponse 필드
  (encryptCustNo/strBtdt/strCpNo/strCustNm/strCustNo/strEmailAdr/strMbCrdNo).
- 라이브러리: `session.py:29-58` `KORAIL_LOGIN_CONTINUATION_FIELDS` 에 위 철자 전부
  열거되고 `:76-93` `build_login_authentication_post_data` 가 `key=value&...` 로
  직렬화. `:216-224` 가 그 문자열과 `raw=response.raw` 를 담아
  `KorailAuthContinuationRequired` 를 던지고 `:169` `self.pending = exc` 로 보관.
  `:248-254` `KorailSession(..., raw=response.raw)` 로 전체 응답 평문 보존.
  `:233-235` 가 `mbCrdNo` 와 `strMbCrdNo` 두 철자를 모두 읽는다.
  `redaction.py:35` 에는 `mbCrdNo` 만 있고 str* 계열은 하나도 없다 — 확인.
  같은 값이 어느 철자로 오느냐로 마스킹 여부가 갈린다는 지적은 정확하다.
- 심각도: 능동 유출은 없다(라이브러리가 스스로 로그하지 않음). 노출 대상은
  **호출자 본인의** 회원정보이고, 카드정보가 아니다. 위생 헬퍼의 사각지대라는
  점에서 실질은 견고성 문제다. medium → **low**.

## P2SAF-07 — NetFunnel 미배선 → CONFIRMED (info)

- 앱: `analysis/jadx/sources/K4/g.java:43-50` 액션 8종
  (act_8/act_8_2/act_6/act_18/act_22/act_21/act_14/act_4), `:51` `NETFUNNEL_SERVER_ID="service_1"`.
  라이브러리 `constants.py:370-393` 이 같은 표를 근거주석과 함께 담고 있다.
- 라이브러리: `grep -n netfunnel src/korail_mobile_api/{client,http}.py` **0건**.
  `config.py:57 netfunnel_enabled: bool = False`, 근거는 `:35-56` 에 장문으로 기록
  (모든 실측 호출이 토큰 없이 성공 / 켜면 매 호출 왕복 1회 + 3초 타임아웃).
  `netfunnel.py:838 slot()` 은 tests 에서만 사용(test_netfunnel.py:862 외 다수).
- 주장 스스로 "결함이 아니라 리스크"로 분류했고 그 판단이 맞다. CONFIRMED, info.

## P2SAF-13 — 게이트 불변식 8종 클린 → CONFIRMED (info)

scratchpad 스크립트로 기계 재계산(저장소 밖 실행):

```
mutation routes: 8 / route categories: 8 / symdiff: set()
read routes: 58
read ∩ mutation (tuple): frozenset()   read ∩ mutation (path): set()
consent flags: 6 ['cancel','discount_card','payment','price_recalculation','refund','reserve']
route category values: 동일 6개 → 전단사
GET mutation routes: [('GET', '/classes/com.korail.mobile.reservation.dcntCrdExtn.do')] (1개)
KORAIL_CARD_BEARING_MUTATION_CATEGORIES: frozenset({'payment'}) → GET 라우트 카테고리(discount_card)와 교집합 없음
KORAIL_EXACT_REQUEST_FIELD_ORDERS: 12, EXACT 밖 키 set()
KORAIL_OPTIONAL_REQUEST_FIELDS: 3, EXACT 밖 키 set()
```

(6) `client.py` 의 `require_mutation_consent(` 실호출 12건
(1565,1633,1735,1807,1853,1898,1971,2029,2085,2140,2207,2283) ↔ 전송 12건
(`post_mutation_form` 11: 1587,1654,1757,1828,1870,1918,1999,2044,2102,2226,2298 +
`get_mutation_query` 1: 2156) 대응.
(7) 전 소스 grep 결과 뮤테이션 라우트 전송은 `http.py:222 post_mutation_form` /
`http.py:318 get_mutation_query` 두 곳뿐.
(8) `http.py:36-42` — `h_msg_cd == "P058"` 이면 `raise_on_fail` 검사보다 **앞에서**
무조건 `KorailSessionExpiredError` 를 던진다. 확인.

전부 성립. CONFIRMED, info.

## P2CRO-12 — build_refund_form 이 서버 값 3개를 버림 → CONFIRMED (high 유지)

- 앱: `.../ui/ticket/ticketReturn/a.java:427-428`
  `RefundCommissionResponse.getTk_ret_tms_dv_cd()` → `setTk_ret_tms_dv_cd()`,
  `:430-431` `getH_pbp_acep_tgt_flg()` → `setPbpAcepTgtFlg()`, `:420 setH_mlg_stl(r9)`
  (`:185-190` 에서 `prg_psb_flg.equals("M") && use_psb_mlg_num >= commissionAmount`
  로 결정). `analysis/jadx/sources/I4/a.java:5-6`
  `AFTER_DEPARTURE="15" / BEFORE_DEPARTURE="21"`.
  실제 전송은 `.../dao/refund/RefundDao.java:145` `returnTicket(... getH_mlg_stl(),
  getTk_ret_tms_dv_cd(), getTrnNo(), getPbpAcepTgtFlg(), ...)`.
- 라이브러리: `mutation_payloads.py:1454 h_mlg_stl="N"`, `:1455 tk_ret_tms_dv_cd="21"`,
  `:1457 pbpAcepTgtFlg="N"` 하드코딩. `build_refund_form(config, ticket)` 에 override
  인자 없음; `client.py:2016-2050 refund()` 도 값을 넘길 수단이 없다 — override
  경로가 "안 쓰는" 게 아니라 **아예 없다**.
  앞 두 값은 `read_parsers.py:2630-2632` (`prg_psb_flg`, `tk_ret_tms_dv_cd`,
  `use_psb_mlg_num`)로 이미 파싱되어 `get_refund_commission()` 이 돌려주는데도
  전송에서 버려진다. `h_pbp_acep_tgt_flg` 는 파싱 자체가 없다(K6-03).
- 출발 후 환불은 예외적 조건이 아니라 흔한 정상 시나리오이고, 그때 앱이 절대
  보내지 않는 조합("21")이 나간다. **high 유지**.

## P2CRO-05 — get_maas_menu_list 변형 3종 중 1종만 → CONFIRMED (low, 하향)

- 앱: `.../dao/common/CommonService.java:46-48`
  `getMaasMenuList(Device, Version, pnrNo, tkRetNo:List, addSrvReqNo)`.
  호출 3종 확인:
  `.../ui/booking/mainBooking/MainBookingActivity.java:737-740` 무필터(`new BaseRequest()`),
  `.../ui/ticket/confirm/MaasAddReservationActivity.java:69-75` `setAddSrvReqNo(...)`,
  `.../ui/ticket/service/AdditionalServiceActivity.java:157-166`
  `setPnrNo(...)` + `setTkRetNo(ArrayList)`.
- 라이브러리: `safety.py:770-772`
  `"/classes/com.korail.mobile.copt.gdMenuLt.do": frozenset({"Device","Version"})`,
  `payloads.py:412-416 build_maas_menu_form(config)` 이 딱 2필드,
  `client.py:1232-1243 get_maas_menu_list(self)` 무인자.
  `assert_read_only_request_fields`(post_form 내부) 가 추가 필드를 거부하므로
  저수준으로도 도달 불가 — 맞다.
- 읽기 전용, 안전성 영향 없음, 순수 기능 축소. medium → **low**.

## P2CRO-07 — 인벤토리 수치 문서 모순 → PARTIAL (low)

- 모순 자체는 사실: `docs/api-status-by-service.md:9-15` 성공32/실패13/미실행120/전체165
  vs `docs/IMPLEMENTATION_PROGRESS.md:311` "current inventory is 32 successful,
  10 failed, and 123 unexecuted". 둘 다 합 165. 부수적으로 공개 메서드 수도
  74(status, `tests/test_readme.py:99`) vs 72(`IMPLEMENTATION_PROGRESS.md:312`) 로 갈린다.
- **틀린 부분**: "핀이 api-status 쪽에만 걸려 있어 IMPLEMENTATION_PROGRESS 의
  드리프트는 CI 에 보이지 않는다". 실제로는 `tests/test_readme.py:523` 과 `:546`
  이 `"32 successful, 10 failed, and 123 unexecuted"` 문자열을
  IMPLEMENTATION_PROGRESS(및 verification-record.md:1321)에 대해 고정한다.
  즉 CI 는 **서로 모순되는 두 수치를 동시에 강제**하고 있다 — 지적 방향은
  반대지만 문제 자체는 오히려 더 확실해진다.
- 성격상 PROGRESS 쪽 수치는 특정 트랜치 시점 스냅샷을 "current" 라고 부르는
  용어 문제(3건이 미실행→실패로 옮겨간 뒤 갱신되지 않음)로 보인다.
- PARTIAL, **low** 유지.

## P2CRO-11 — 45개 exact 핀 전수 대조 클린 → CONFIRMED (info)

- 수치 재계산: `KORAIL_EXACT_REQUEST_FIELDS` **45개 경로**,
  `KORAIL_READ_ONLY_ROUTES` **58개**, 핀 없는 read 경로 **13개**
  (common.code.do, common.stationdata, common.stationinfo, login.Login,
  myTicket.MyTicketList, qry.chtnStn.do, research.actualTrainSchedule.do,
  schedule.runDt, seatMovie.ScheduleView, /ebizcross/getUUID.do,
  /ebizmaas/EbizMaasStationList.do, prdMobilePlusMain.cache,
  prdMobilePlusNotice.cache) — 주장과 정확히 일치.
- 표본 대조(무작위 3개, 전부 정확히 일치):
  `refunds.SelTicketInfo` 핀 {Device,Key,Version,h_orgtk_ret_sale_dt,
  h_orgtk_wct_no,h_orgtk_sale_sqno,h_orgtk_ret_pwd,h_purchase_history} ↔
  `.../dao/refund/RefundService.java:25` 동일 8필드.
  `tk.pbpAcepSpec.do` 핀 {Device,Key,Version,tkCnt,tkRetNo} ↔ `TicketService.java:68` 동일.
  `mlg.amtSpec.do` 핀 9필드 ↔ `.../dao/xPoint/XPointService.java:28` 동일.
- "핀에 있으나 앱에 없는 필드 0건" 을 45경로 전수로 재실행하지는 않았으나
  표본·수치·근거 서술이 모두 성립. CONFIRMED, info.

---

## 부수 관찰 (21건 밖, 참고)

- `docs/RELEASE_GAP_PLAN.md:137` G11 이 "`client.logout()` only clears the local
  cookie jar; server session never invalidated" 라고 적었으나 실제로는
  `session.py:255-` 의 `logout()` 이 `GET /classes/com.korail.mobile.login.Logout`
  을 보내고 `safety.py:75` 에 라우트도 등록되어 있다. 문서 스테일.
- (초안에서 제기했다가 **자체 반증하여 철회**) `mutation_payloads.py:1453` 의
  `h_orgtk_sale_wct_no` 가 앱과 다르다고 의심했으나, 와이어 키는 DTO getter 이름이
  아니라 Retrofit 애너테이션에 있다:
  `.../dao/refund/RefundService.java:29`
  `@Field("h_orgtk_sale_wct_no")` — 라이브러리가 정확하다. 결함 아님.
