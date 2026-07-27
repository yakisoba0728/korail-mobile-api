# K7 — 정기권·패스·포인트·기프트 (pass / passCard / mileage / xPoint / gifticket / giftInfo)

감사 대상: `analysis/jadx/sources/com/korail/talk/network/dao/{pass,passCard,mileage,xPoint,gifticket,giftInfo}/` (총 24개 자바 파일, Retrofit 엔드포인트 25개) vs `src/korail_mobile_api/`.

## 0. 방법

- 6개 디렉터리의 `*Service.java`(Retrofit 인터페이스)로 전체 엔드포인트 표면을 먼저 확정한 뒤, 각 `*Dao.java`를 전문 정독해 요청/응답 필드를 추출.
- 라이브러리 쪽은 `client.py`(공개 메서드) → `read_payloads.py`/`mutation_payloads.py`(요청 빌더) → `read_parsers.py`/`mutation_parsers.py`(응답 파서) → `read_models.py`(dataclass)를 필드 단위로 대조.
- `safety.py`의 `KORAIL_READ_ONLY_ROUTES` / `KORAIL_MUTATION_ROUTES` / `EXCLUDED_API_DOMAINS` 및 `tests/test_loyalty_reads.py` 등으로 게이트 경계를 교차 검증.
- 이 저장소의 `docs/RELEASE_GAP_PLAN.md`, `docs/IMPLEMENTATION_PROGRESS.md`, `docs/deep-dive/impl-audit-*.md`(과거 감사) 를 "의도적 제외인지 아닌지"를 판별하는 1차 증거로 사용 — 이 담당 영역은 이미 세 차례(07-20, 07-22, 07-26) 별도 감사가 지나간 흔적이 있어, 새 주장을 하기 전에 반드시 기존 판정과 대조했다.

## 1. 엔드포인트 전체 목록 (25개)

### pass/ (PassService.java) — 8개

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 1 | 정기권 결제 실행 | `POST pass.passPayIssue` | `CommPaymentDao.java`, `PassService.java:19-21` | 없음 | **의도적 제외** (정기권 구매) |
| 2 | 정기권 예약 | `POST pass.passReserve` | `CommReservationDao.java`, `PassService.java:23-25` | 없음 | **의도적 제외** (정기권 구매) |
| 3 | 정기권 열차 스케줄 조회 | `POST pass.passScheduleInfoList` | `CommRsvInquiryDao.java`, `PassService.java:27-29` | `KorailClient.get_pass_schedule` (`client.py:684-698`) | 있음 |
| 4 | 정기권 발매가능일 조회 | `POST pass.passInfoList` | `EnableDateDao.java`, `PassService.java:31-33` | `KorailClient.get_pass_available_dates` (`client.py:659-681`) | 있음 |
| 5 | 정기권/할인 메뉴 조회 | `POST pass.passMenu.do` | `DiscountMenuDao.java`, `PassService.java:35-37` | `KorailClient.get_pass_menu` (`client.py:716-733`) | 있음 |
| 6 | 자유이용권(Otr) 결제 | `POST pass.passOtrPayIssue` | `PassPaymentDao.java`, `PassService.java:39-41` | 없음 | **의도적 제외** (다른 상품군, `IMPLEMENTATION_PROGRESS.md:87-89`) |
| 7 | 자유이용권(Otr) 예약 | `POST pass.passOtrReserve` | `PassReservationDao.java`, `PassService.java:43-45` | 없음 | **의도적 제외** (상동) |
| 8 | 여행지 메뉴(트립메뉴) 조회 | `POST pass.trGdMenuLt.do` | `TripMenuDao.java`, `PassService.java:47-49` | `KorailClient.get_trip_menu` (`client.py:702-714`) | 있음 |

### passCard/ (PassCardService.java) — 4개

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 9 | 지연할인권 등록 | `POST passCard.DelayDiscountCheck` | `DelayTicketAddDao.java`, `PassCardService.java:12-14` | 없음 | **의도적 제외** (계정에 자격 등록/금전성, `IMPLEMENTATION_PROGRESS.md:57-58`) |
| 10 | 할인쿠폰 인증(등록) | `POST passCard.DiscountCheck` | `DCCouponCertDao.java`(+ 하위 `DCEmployeeCouponCertDao.java`), `PassCardService.java:16-18` | 없음 | **의도적 제외** (상동) |
| 11 | 지연할인권 목록 조회 | `POST passCard.DelayDiscountView` | `DelayTicketListDao.java`, `PassCardService.java:20-22` | `KorailClient.get_delay_discount_tickets` (`client.py:480-494`) | 있음 |
| 12 | 할인쿠폰 목록 조회 | `POST passCard.CouponView` | `DCCouponListDao.java`, `PassCardService.java:24-26` | `KorailClient.get_discount_coupons` (`client.py:497-511`) | 있음 |

### mileage/ (MileageService.java) — 3개

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 13 | 동반 마일리지 알림 | `POST mileage.acpnMlgNoti.do` | `AcpnMlgNotiDao.java`, `MileageService.java:11-13` | 없음 | **의도적 제외** (`IMPLEMENTATION_PROGRESS.md:57-58`) |
| 14 | 동반 마일리지 적립 | `POST mileage.acpnMlgSave.do` | `AcpnMlgSaveDao.java`, `MileageService.java:15-17` | 없음 | **의도적 제외** (상동) |
| 15 | 동반 마일리지 내역(PNR별) 조회 | `POST mileage.acpnMlgSpec.do` | `AcpnMlgSpecDao.java`, `MileageService.java:19-21` | 없음 | **누락 (K7-01)** |

### xPoint/ (XPointService.java) — 5개

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 16 | OK캐시백 카드 인증(등록) | `POST xPoint.OkCashbagCertView` | `OKCashbagCertDao.java`, `XPointService.java:14-16` | 없음 | **의도적 제외** (등록 write) |
| 17 | 코레일포인트 요약 조회 | `POST xPoint.MyXPointView` | `KorailPointInquiryDao.java`, `XPointService.java:18-20` | `KorailClient.get_korail_point_summary` (`client.py:517-553`) | 있음 |
| 18 | L.POINT 비밀번호 인증 조회 | `POST mlg.lpotAthn.do` | `LPointDao.java`, `XPointService.java:22-24` | 없음 | **의도적 제외** (비밀번호 시도 카운터) |
| 19 | 마일리지/철도포인트 내역 조회 | `POST mlg.amtSpec.do` | `MileageInquiryDao.java`, `XPointService.java:26-28` | `KorailClient.get_mileage_history` (`client.py:558-584`) | 있음 |
| 20 | 교통카드/제휴포인트 인증 조회 | `POST xPoint.XPointView` | `PointInquiryDao.java`, `XPointService.java:30-32` | 없음 | **의도적 제외** (비밀번호 동일 사유) |

### gifticket/ (GifticketService.java) — 4개

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 21 | 기프티켓(포인트 상품권) 예약/구매 | `POST gift.gdRsv.do` | `GifticketBookingDao.java`, `GifticketService.java:13-15` | 없음 | **의도적 제외 (미확정 범위)** — `RELEASE_GAP_PLAN.md:441-448` |
| 22 | 기프티켓 목록 조회 | `POST gift.gdLst.do` | `GifticketListDao.java`, `GifticketService.java:17-19` | `KorailClient.get_gift_ticket_list` (`client.py:973-986`) | 있음 |
| 23 | 기프티켓 사용이력 조회 | `POST gift.gdUseSpec.do` | `GifticketHistoryDao.java`, `GifticketService.java:21-23` | 없음 | **의도적 제외 (미확정 범위)** — `RELEASE_GAP_PLAN.md:137` (G10) |
| 24 | 기프티켓 반환/취소 | `POST gift.gdRet.do` | `GifticketReturnDao.java`, `GifticketService.java:25-27` | 없음 | **의도적 제외 (미확정 범위)** — `RELEASE_GAP_PLAN.md:441-448` |

### giftInfo/ (GiftInfoService.java) — 1개

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 25 | 승차권 선물(양도) | `POST giftInfo.GiftSend` | `TicketPresentDao.java`, `GiftInfoService.java:12-14` | 없음 | **의도적 제외 (미확정 범위)** — `RELEASE_GAP_PLAN.md:444` |

**요약**: 25개 중 9개 구현(모두 필드 단위로 정확), 15개는 근거 문서에서 명시적으로 이유를 밝히고 제외한 항목(정기권 구매 4 + Otr 2 + passCard 결제성 write 2 + mileage write 2 + xPoint write 3 + gifticket/giftInfo write 4 — 단 gifticket write 3개는 위 표처럼 3개), 1개(`mileage.acpnMlgSpec.do`)는 근거 문서 어디에도 개별적으로 "왜 뺐는지"가 없는 **미채워진 공백**이다.

---

## 2. 있는 것 — 필드 단위 검증 결과 (문제 없음, 9개)

구현된 9개 전부 요청 필드명·순서·타입(문자열 유지), 응답 필드 매핑, 페이지네이션, 빈 결과 코드 처리까지 DAO/서비스 인터페이스와 대조해 확인했다. 특기할 점만 기록한다.

- **`get_pass_schedule`**(`pass.passScheduleInfoList`): `CommRsvInquiryRequest`의 `txtCmtrUtlTrmNm` 필드는 DTO에 getter가 있지만 `PassService.getCommRsvInquiry(...)` 호출부(`PassService.java:29`)에 실제로 전달되지 않는다 — 라이브러리도 이 필드를 보내지 않는다(`read_payloads.py:340-359`). 죽은 DTO 필드까지 정확히 재현.
- **`get_korail_point_summary`**(`xPoint.MyXPointView`): `point_dv_cd` 하드코딩 `"0"` 재현(`KorailPointInquiryDao.java:91` ↔ `read_payloads.py:556-566`), 14개 응답 필드 전부 매핑(`read_parsers.py:1549-1564`).
- **`get_mileage_history`**(`mlg.amtSpec.do`): 응답 9개 스칼라 필드 + `specList` 항목 7개 필드 전부 매핑(`read_parsers.py:1566-1586`). `pgPrCnt="20"` 하드코딩까지 앱 소스(`MileageHistoryActivity.java:274`)와 대조해 재현.
- **`get_discount_coupons`**(`passCard.CouponView`): `pnrNo`(Retrofit 실제 필드명, DTO getter는 `getPnr()`이라 이름이 다름)를 정확히 사용(`read_payloads.py:396-403`), `WRG000000`을 빈 결과로 처리(`read_parsers.py:771-776`).
- **`get_gift_ticket_list`**(`gift.gdLst.do`): 앱이 실제 호출부에서 절대 채우지 않는 `qryNumNext`/`fllwQryFlg`/`trnOprBzDvCd` 3개 필드를 라이브러리도 보내지 않는다 — `GifticketView`/`B6/b.java:267-272`, `B6/f.java:180-185`(실제 호출부) 대조 결과 앱 자신도 이 3필드를 셋업하지 않으므로 정확히 일치. (`GifticketListDao`의 Retrofit 서명은 11필드지만 실사용은 8필드뿐.)
- 응답 필드 중 정수처럼 보이는 값(`h_st_prnb`, `h_cls_prnb` 등)이 실제로는 zero-padded 문자열(`"000001"`)로 오는 것까지 파서가 처리(`read_parsers.py:426-436`) — "문자열/숫자 타입 불일치" 함정에 이 영역은 걸리지 않았다.

---

## 3. 문제 항목 상세

### K7-01 — `mileage.acpnMlgSpec.do`(동반 마일리지 PNR별 내역 조회)가 완전히 누락, 그리고 그 사실이 3번의 이전 감사에서도 반복해서 놓쳐짐

**분류**: missing · **심각도**: medium

**앱 근거**: `analysis/jadx/sources/com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java:1-168`, 선언부 `MileageService.java:19-21`.
- 요청은 `pnrNo` 단 하나(`AcpnMlgSpecDao.java:13-26`) — 비밀번호·카드번호 등 인증성 필드 없음. `Device`/`Version`/`Key`(세션 쿠키 동봉)만 있으면 호출 가능한 순수 조회.
- 응답은 `tkList: List<Ticket>`이며 각 `Ticket`은 `jrnyList`(여정) → `seatList`(좌석)까지 내려오고, 좌석마다 `mlgSaveFlg`/`mlgSaveTgt`(이 좌석이 마일리지 적립 대상인지/적립됐는지)를 담는다(`AcpnMlgSpecDao.java:70-155`) — 즉 "동반 탑승자 마일리지가 이 PNR의 어느 좌석에 적립됐는지"를 읽는 화면 전용 조회다. 상태를 바꾸지 않는다.

**라이브러리 근거**: `src/korail_mobile_api/client.py`, `read_payloads.py`, `read_parsers.py`, `read_models.py`, `mutation_*.py`, `safety.py` 전체에 `acpnMlgSpec` 문자열이 **단 한 번도** 등장하지 않는다(grep 결과 0건). `KORAIL_READ_ONLY_ROUTES`(`safety.py:69-175`)에도, `KORAIL_MUTATION_ROUTES`에도, `EXCLUDED_API_DOMAINS`의 사유 주석(`safety.py:17-35`)에도 이 경로는 없다.

**왜 "의도적 제외"가 아니라 "누락"인가 — 증거 사슬**:
1. `safety.py:17-35`의 주석은 `points-mileage-write`로 제외된 항목을 **정확히 5개**로 못박는다: `mlg.lpotAthn.do`, `xPoint.XPointView`, `xPoint.OkCashbagCertView`, `mileage.acpnMlgSave.do`, `mileage.acpnMlgNoti.do`. `acpnMlgSpec.do`는 이 목록에 없다.
2. `docs/IMPLEMENTATION_PROGRESS.md:34`(2026-07-26 최신 할인/포인트 서베이)는 "무엇이 빠졌는지" 표에서 `mileage.acpnMlgSave.do / acpnMlgNoti.do / acpnMlgSpec.do`를 한 행으로 묶어 "companion-mileage accrual, notification, per-PNR spec"이라고 세 개를 뭉뚱그려 적었다. 그런데 바로 아래 "왜 뺐는지"를 설명하는 절(`:57-58`, "Accrual and registration writes")에서는 정확히 **4개**만 나열한다: `OkCashbagCertView, acpnMlgSave.do, acpnMlgNoti.do, passCard.DiscountCheck, passCard.DelayDiscountCheck`. `acpnMlgSpec.do`는 "빠졌다"는 표에는 있지만 "왜 뺐는지" 목록에는 없다 — 조회이므로 이 write 전용 사유("계정에 자격/포인트를 등록·이동한다")가 애초에 적용되지 않는다.
3. 이전 감사(`docs/deep-dive/impl-audit-reverify2-2026-07-22.md:127`)도 동일한 구조로 실수를 반복한다: "Points / mileage reads ... (`AcpnMlgSpecDao` at `mileage.acpnMlgSpec.do`, `AcpnMlgNotiDao`), but none has a client counterpart"라고 적어 **읽기 전용인 `AcpnMlgSpecDao`를 쓰기 전용인 `AcpnMlgNotiDao`와 같은 문장에 묶어** "구현 안 됨" 한 줄로 처리했다.
4. `docs/RELEASE_GAP_PLAN.md`의 읽기 전용 갭 전용 테이블(G1~G12, `:128-139`)에는 이런 성격의 "아직 안 옮긴 조회"가 12개나 개별 사유와 함께 등재돼 있는데, `acpnMlgSpec.do`는 이 표에도 없다.
5. 결정적으로, `tests/test_loyalty_reads.py:76`의 테스트 이름 자체가 `test_only_the_two_password_free_loyalty_reads_are_reachable`이다 — "비밀번호 없는 로열티 조회는 정확히 두 개뿐"이라는 전제로 짜여 있다. 그러나 실제로는 `xPoint.MyXPointView`, `mlg.amtSpec.do`에 더해 `mileage.acpnMlgSpec.do`까지 **비밀번호가 없는 세 번째 로열티 조회**가 앱에 존재한다(위 1번 근거). 같은 파일의 `WITHHELD_PATHS`(`:44-49`, "의도적으로 뺀 경로" 목록)에도 `acpnMlgSpec.do`는 없다 — 즉 이 엔드포인트는 "구현됨" 목록에도, "의도적으로 뺀" 목록에도 속하지 않는, 시스템 전체에서 존재 자체가 인지되지 않은 사각지대다.

**영향**: "동반 탑승자에게 마일리지가 실제로 적립됐는지"를 PNR 단위로 확인할 수 있는 유일한 화면 전용 조회가 라이브러리에 없다. 세션·비밀번호 요구도 없어 구현 난이도가 낮고(요청 1필드, 응답 파싱은 기존 `AcpnMlgSpecDao`/`Ticket`/`Jrny`/`Seat` 구조를 그대로 옮기면 됨), 안전 게이트를 새로 설계할 필요도 없다(다른 두 로열티 조회와 동일한 `_require_session()` + 무비밀번호 패턴).

**제안**: `get_companion_mileage_detail(pnr_no: str)` 형태로 `mileage.acpnMlgSpec.do`를 `KORAIL_READ_ONLY_ROUTES`에 추가하고 `AcpnMlgSpecResponse.tkList[].jrnyList[].seatList[].{mlgSaveFlg,mlgSaveTgt,...}` 구조를 그대로 모델링. `test_only_the_two_password_free_loyalty_reads_are_reachable`이라는 테스트명·전제도 함께 갱신 필요.

---

## 4. 확인 후 "결함 아님"으로 판단해 findings에서 제외한 항목 (참고용)

아래는 라이브러리에 없지만, 근거 문서에서 **개별적으로** 이유가 확인되어 findings에 넣지 않은 항목이다. 지침의 "의도적으로 제외된 범위를 누락으로 보고하지 마라"에 해당한다.

| 엔드포인트 | 제외 사유(근거) |
|---|---|
| `pass.passPayIssue` / `passReserve` / `passOtrPayIssue` / `passOtrReserve` | 정기권/자유이용권 **구매** — 작업 지시서상 명시적 제외 범위. `IMPLEMENTATION_PROGRESS.md:78-89`에 추가로: `passReserve`/`passPayIssue`는 2026-07-26 한 번 구현했다가 같은 날 제거됨(환불 경로 없는 ₩150,000~250,000 결제 + `passPayIssue`는 앱 자체에서 `PaymentActivity.isCommPaymentRequest()`의 `instanceof` 버그로 **영원히 도달 불가**한 죽은 코드라 실제 트래픽으로 검증 불가). |
| `passCard.DiscountCheck`(certDCCoupon) / `DelayDiscountCheck`(addDelayTicket) | 계정에 쿠폰/지연할인권을 **등록**하는 write. `IMPLEMENTATION_PROGRESS.md:57-58`에 "금전 등가물을 이동하거나 계정에 자격을 귀속시키며, 오프라인으로 검증 불가"로 명시. |
| `mileage.acpnMlgSave.do` / `acpnMlgNoti.do` | 마일리지 적립/알림 write. 동일 근거(`IMPLEMENTATION_PROGRESS.md:57-58`), `safety.py:17-35`에도 명시. |
| `xPoint.OkCashbagCertView` | OK캐시백 카드를 계정에 **등록**하는 write(`OKCashbagCertDao.java` 확인 — `cpNo`만 받아 인증/등록). |
| `mlg.lpotAthn.do` / `xPoint.XPointView` | 응답에 `pwdErrTno`(비밀번호 오류 횟수 카운터)가 있어, 잘못된 비밀번호 한 번이 외부 포인트 제공자 쪽 계정 상태를 바꾼다(`LPointDao.java:44-68`, `PointInquiryDao.java` 확인 — `xpointNo`+`xpointPwd` 자격증명 필드 존재). `safety.py:17-35` 사유와 일치함을 DAO 원문으로 재확인. |
| `gift.gdRsv.do` / `gdRet.do` / `gdUseSpec.do`, `giftInfo.GiftSend` | 기프티켓 예약/반환/이력, 승차권 선물 — 4개 모두 `RELEASE_GAP_PLAN.md`에 개별 근거와 함께 "명시적으로 스코프될 때까지 보류"로 등재(`:137` G10, `:441-448`). 목록 조회(`gdLst`)만 먼저 구현된 상태. |
| `TripMenuContent`가 `cmtrKndCd`/`passType`/`passData`를 타입 필드로 노출하지 않음(`raw`로만 접근 가능) | 이전 감사에서 "의도된 설계"로 이미 판정됨(`docs/deep-dive/impl-audit-reverify4-2026-07-22.md:120`, "Curated response subsets ... deliberate design, not a mis-parse") — 형제 응답인 `PassMenuItem.pass_data`는 반대로 타입화돼 있어 비일관적으로 보이지만, 원본 데이터는 `raw`에 보존되어 손실은 없음. 재확인만 하고 findings에는 넣지 않음. |

---

## 5. 확인 불가 (라이브 미검증, 결함 아님 — 문서에도 명시됨)

- `get_korail_point_summary`의 `disability_flag`(`h_hdcp_flg`) ↔ `ERR299943` 거절 사유 상관관계는 라이브러리 자체 docstring에 "가설, 라이브 미검증"으로 명시돼 있다(`client.py:534-538`). 이 영역 담당 범위 밖이라 별도 검증하지 않음.
- `get_mileage_history` 전체가 "NOT LIVE-VERIFIED"로 명시(`client.py:573`). DAO 구조 대조만으로는 필드 존재 여부는 확인되나 실제 서버가 이 형태로 응답하는지는 확인 불가.
