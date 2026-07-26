# 코레일톡 앱 ↔ korail-mobile-api 대조 감사 — 열차조회·시간표·운임 (K2 슬라이스)

감사 범위: `network/dao/trainsInfo/`, `network/dao/schedule/`, `network/dao/research/`, `network/dao/product/` (앱측)
대조 대상: `src/korail_mobile_api/{read_,}payloads.py`, `{read_,}parsers.py`, `{read_,}models.py`, `client.py`, `mutation_*.py`

방법: jadx로 각 DAO의 요청/응답 필드를 전수 추출 → 의심 지점은 `analysis/apktool/smali`로 상수/필드를 재확인 → 라이브러리에서
동일 엔드포인트를 호출하는 `client.py` 지점을 찾아 필드명·타입·기본값을 1:1 대조.

**핵심 결론 먼저**: 이 슬라이스에서 critical/high 등급 결함은 없다. 안전게이트 우회, 금전/예약 오작동, 카드정보 유출 사례를 찾지
못했다. 발견된 문제는 모두 (a) 근거 없이 부풀려진 응답 스키마 1건, (b) 이미 알려진 미구현 엔드포인트 3~4건, (c) 편의성/연쇄호출
관련 저위험 항목들이다.

---

## 0. 범위 밖 명시

- **정렬(sort) 파라미터**: 태스크 지시에 언급되었으나, 실제 정렬 로직은 열차 검색 결과 화면(`seatMovie.ScheduleView` /
  `build_train_search_form`, `models.py:235-` `TrainSearchQuery`)에 있다. 이 패키지는 `network/dao/seatMovie/`
  소속으로 내 담당 4개 디렉터리(`trainsInfo/schedule/research/product`) 밖이다. **범위 외 — 미검증.**
- **정기권(통근패스) 구매, 단체예약**: 사용자 지시에 따라 의도된 제외. 다만 확인 결과 이 슬라이스에는 "구매 자체를 배제하고
  질의만 구현"한 사례(`CmtrInfoDao`/`getCmtrInfo`)가 있었고 이는 실제로 **구현되어 있음**을 확인했다 (§2 표 참조). 즉 이
  슬라이스에서 "의도된 제외"로 분류할 항목은 없었다 — 배제 대상인 "구매 실행"(`pass.passReserve` 등)은애초에 다른 패키지
  (`dao/pass/`) 소속이라 내 범위에 없다.

---

## 1. 엔드포인트 전수 목록과 상태

앱의 4개 Retrofit 서비스 인터페이스(`TrainsInfoService`, `CalendarService`, `ResearchService`, `ProductService`)가
선언한 메서드 = 22개. 아래 표가 그 전수이며 `app_functions_extracted = 22`.

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 1 | 자유석 차량 안내 | POST `trn.fresScar.do` | `TrainsInfoService.java:20-22`, `FresScarDao.java` | `get_free_seat_car_info` / `build_free_seat_car_form` / `parse_free_seat_car_response` (`client.py:842-851`, `read_payloads.py:232-245`, `read_parsers.py:1230-1249`) | 있음 |
| 2 | 운임 조회(2legs, 실사용) | POST `trn.prcFare.do` | `TrainsInfoService.java:24-26`, `Price2FareDao.java` | `get_price_fare_quote` / `build_price_fare_quote_form` / `parse_price_fare_quote_response` (`client.py:1006-1018`, `read_payloads.py:1223-1249`, `read_parsers.py:2119-2140`) | 있음 |
| 3 | 운임 조회(TrainCharge, **앱 자체 미사용**) | POST `trainsInfo.TrainCharge` | `TrainsInfoService.java:28-30`, `PriceFareDao.java` | 없음 | 없음(단, 앱도 어디서도 호출하지 않는 죽은 코드 — §3.3) |
| 4 | 환승역 조회 | POST `qry.chtnStn.do` | `TrainsInfoService.java:32-34`, `TrainSelectStationDao.java` | `get_transfer_stations` / `parse_transfer_station_list_response` (`client.py:1470-1485`, `parsers.py:744-782`) | 있음 |
| 5 | 관광열차 특실정보 | POST `trainsInfo.TourTrainSpecialRoom` | `TrainsInfoService.java:36-38`, `TourTrainInfoDao.java` | 파서/모델만 존재, payload builder·client 미연결 (`read_parsers.py:1910-1969`, `read_models.py:813-829`) | **부분** (§3.1) |
| 6 | 실제 운행 스케줄/지연 | POST `research.actualTrainSchedule.do` | `TrainsInfoService.java:40-42`, `TrainScheduleDao.java` | `get_train_schedule` / `build_train_schedule_form` / `parse_train_schedule_response` (`client.py:1451-1468`, `payloads.py:341-352`, `parsers.py:573-741`) | 있음 (단, 응답 스키마 과다확장 — §3.2) |
| 7 | 열차운행 달력 | GET `schedule.runDt` | `CalendarService.java:8-9`, `TrainCalendarDao.java` | `get_train_calendar` / `parse_train_calendar_response` (`client.py:1283-1288`, `parsers.py:454-` ) | 있음 |
| 8 | 좌석배정 가능 스케줄 | POST `research.assignScheduleView.do` | `ResearchService.java:31-33`, `SeatAssignScheduleViewDao.java` | `get_seat_assignment_schedule` / `build_seat_assignment_schedule_form` / `parse_seat_assignment_schedule_response` (`client.py:872-885`, `read_payloads.py:257-276`, `read_parsers.py:1400-1417`) | 있음 (§3.5 연쇄호출 참고) |
| 9 | 좌석도 객차 목록 | POST `research.TrainResearch` | `ResearchService.java:35-37`, `SearchCarListDao.java` | `get_seat_cars` / `build_seat_car_form` / `parse_seat_car_list_response` (`client.py:322-347`, `payloads.py:141-178`, `parsers.py:883-979`) | 있음 (§3.4 추가필드 참고) |
| 10 | 통근열차 정보질의 | POST `research.cmtrInfo.do` | `ResearchService.java:39-41`, `CmtrInfoDao.java` | `get_commuter_info` / `build_commuter_info_form` / `parse_commuter_info_response` (`client.py:990-1004`, `read_payloads.py:1088-1147`, `read_parsers.py:2032-2106`) | 있음 |
| 11 | 여정 편의설정 조회 | POST `research.custTripInfo.do` | `ResearchService.java:43-45`, `ConvenienceSettingDao.java` | `build_customer_trip_info_form` / `parse_customer_trip_info_response` (`read_payloads.py:797-802`, `read_parsers.py:1841-1861`) | 있음 |
| 12 | 병합좌석 조회 | POST `research.mergeSeatsC.do` | `ResearchService.java:47-49`, `MergeSeatInquiryDao.java` | `get_merge_seats_inquiry` / `build_merge_seats_inquiry_form` / `parse_merge_seats_inquiry_response` (`client.py:887-896`, `read_payloads.py:279-295`, `read_parsers.py:1420-1456`) | 있음 |
| 13 | N카드 사용내역 | GET `ticket.dcntCrdUseQry.do` | `ResearchService.java:51-52`, `NCardHistoryDao.java` | `get_discount_card_usage`(추정 함수명) / `build_discount_card_usage_query` / `parse_discount_card_usage_response` (`client.py:590-615`, `read_payloads.py:649-661`, `read_parsers.py:1636-1683`) | 있음 |
| 14 | N카드 예약가능 스케줄 | GET `research.dcntCrdScheduleView.do` | `ResearchService.java:54-55`, `NCardInquiryDao.java` | `build_discount_card_schedule_query` / `parse_discount_card_schedule_response` (`client.py:626-651`, `read_payloads.py:741-796`, `read_parsers.py:1644-1717`) | 있음 (**RELEASE_GAP_PLAN.md 오기재 — §3.6**) |
| 15 | 좌석도 좌석 목록 | POST `research.TResidualSeatsResearch.do` | `ResearchService.java:57-59`, `SearchSeatListDao.java` | `get_seat_inventory` / `build_seat_inventory_form` / `parse_seat_inventory_response` (`client.py:349-380`, `payloads.py:181-223`, `parsers.py:1007-1103`) | 있음 (§3.4, §3.7 참고) |
| 16 | 승차권 변경용 원표 조회 | POST `research.tripChgOgtk.do` | `ResearchService.java:61-63`, `OgTkInquiryDao.java` | 없음 | **없음** (기지정 gap G4 — §3.8) |
| 17 | N카드 유효기간 연장 | GET `reservation.dcntCrdExtn.do` | `ResearchService.java:65-66` | `extend_discount_card`(mutation) (`client.py:2121-` , `mutation_payloads.py:1587-`) | 있음(mutation 파일) |
| 18 | N카드 구매 | POST `research.dcntCrdInfo.do` | `ResearchService.java:68-70` | `buy_discount_card`(mutation) (`client.py:2059-`, `mutation_payloads.py:1477-`) | 있음(mutation 파일) |
| 19 | 예약상품 상세 | GET `product.ReservationDetail` | `ProductService.java:12-13`, `ProductDetailDao.java` | `get_product_detail` / `build_product_detail_query` / `parse_product_detail_response` (`client.py:784-798`, `read_payloads.py:461-471`, `read_parsers.py:968-1010`) | 있음 (§3.9 참고) |
| 20 | 예약상품 목록 | GET `product.ReservationList` | `ProductService.java:15-16`, `ProductListDao.java` | `get_product_reservations` / `build_product_reservations_query` / `parse_product_reservation_list_response` (`client.py:765-782`, `read_payloads.py:451-458`, `read_parsers.py:927-965`) | 있음 (§3.9 참고) |
| 21 | 예약상품 결제확인 | GET `product.payInfo` | `ProductService.java:18-19`, `ProductPaymentCheckDao.java` | 없음 | **없음** (기지정 gap G9) |
| 22 | 예약상품 취소 | GET `product.ReservationCancel` | `ProductService.java:21-22`, `ProductCancelDao.java` | 없음 | **없음** (mutation, RELEASE_GAP_PLAN.md:326에 이름만 등재) |

**집계**: 있음 17 / 부분 1 / 없음(제품 기능 갭) 3 / 없음(앱 자체 죽은 코드) 1 = 22.
`implemented_count = 17` (완전히 도달 가능하고 필드 검증까지 통과한 것만 카운트; 부분·갭·죽은코드는 제외).

---

## 2. 상세 검증 노트 (문제 없음 확인된 것들, 요약)

아래는 findings에는 안 올렸지만 실제로 필드 단위 대조를 수행해 "일치"를 확인한 것들이다 (근거: jadx + 일부는 smali 확인).

- **FresScarDao ↔ FreeSeatCarRequest/Response**: `runDt,trnNo(5자리 zero-pad),dptStnConsOrdr,arvStnConsOrdr,dptStnRunOrdr,arvStnRunOrdr` 요청 6필드, `fresTtl→title,fresScarNo→car_no,fresCont→content` 응답 3필드 모두 일치.
- **Price2FareDao ↔ PriceFareQuoteRequest**: `txtMenuId="11"`(근거 `a5/k.java:92-94`), `chtnDvCd=leg수`, 8개 맵 필드(`dptRsStnCd,arvRsStnCd,runDt,trnNo,gdNo,rqSeatAttCd,trnGpCd,stlbTrnClsfCd`) 모두 콤마조인 방식까지 `PriceFareActivity.java:79-98`과 일치. 응답 `prcList[]`의 6필드(`jrnySqno,psrmClNm,rcvdFare,rcvdPrc,sumAmt,trnNo`)도 정확히 일치.
- **TrainSelectStationDao ↔ get_transfer_stations**: `dptRsStnCd,arvRsStnCd` 요청, `chtnList[].chtnRsStnCd/chtnRsStnNm` 응답 일치.
- **TrainCalendarDao ↔ TrainCalendarDay**: 12개 필드(`runDt,bizDdStgCd,dayDvCd,hldyDvCd,saleDdDvCd,a/d/g/o/s/v/x TrnOpFlg`) **완전 일치(12/12)**.
- **SeatAssignScheduleViewDao/MergeSeatInquiryDao ↔ 대응 함수**: 요청 필드(`menuId,dptDt,dptTm,dptRsStnNm,arvRsStnNm,trnGpCd,psrmClCd,seatAttCd1,psgNum1,stlbDturDvNm1,dirtChtnDvCd,chtnArvRsStnNm` / `abrdDt,runDt,trnNo,dptRsStnNm,arvRsStnNm,selRsStnNm,psrmClCd,seatAttCd,totPsgNum`) 전부 일치. `dirtChtnDvCd∈{"1","2"}` 제약도 앱의 `K4/d.java`(`DIRECT_SQ_NO="1", TRANSFER_SQ_NO="2"`)와 정확히 일치. 응답의 `trn_infos.trn_info[]`가 참조하는 `RsvInquiryResponse.TrainInfo`의 약 30개 필드 중 라이브러리가 소비하는 27개(`h_trn_no,h_trn_gp_cd,h_trn_clsf_cd,h_trn_clsf_nm,h_run_dt,h_dpt_dt,h_dpt_tm,h_arv_dt,h_arv_tm,h_dpt_rs_stn_cd,h_dpt_rs_stn_nm,h_arv_rs_stn_cd,h_arv_rs_stn_nm,h_dpt_stn_cons_ordr,h_arv_stn_cons_ordr,h_dpt_stn_run_ordr,h_arv_stn_run_ordr,h_car_tp_nm,h_gen_psrm_cl_nm,h_spe_psrm_cl_nm,h_gen_rsv_cd,h_spe_rsv_cd,h_free_rsv_cd,h_stnd_rsv_cd,h_rd_seat_map_flg,h_dlay_sale_flg,h_wait_rsv_flg,h_rsv_psb_nm,h_spe_rsv_psb_nm,h_info_txt,h_popup_msg`)는 실제 `RsvInquiryResponse.java:65-455`에 전부 존재함을 확인.
- **SearchCarListDao/SearchSeatListDao ↔ get_seat_cars/get_seat_inventory**: `SeatSearchRequest` 17필드 전부 매핑 확인. `isArrow` 하드코딩 `true`(앱 DAO도 리터럴 `true` 전달, `SearchSeatListDao.java:137`), `txtMenuId="11"`, `room_class_code∈{"1","2"}`(근거 `K4/o.java` GENERAL/SPECIAL) 등 전부 앱 소스와 일치. 응답 `SearchSeatListResponse`의 필수 필드(`layout_type,seat_ary_cd,seat_remain_count,seat_total_count,seatList[],windowList[],vrBnrUrl`)와 `Seat`/`Window`의 11개 필드 **완전 일치**(smali 확인, `SearchSeatListDao$SearchSeatListResponse.smali`).
- **ConvenienceSettingDao ↔ CustomerTripInfo**: 요청 3필드(`custMgNo,medDvCd="03"(고정),regSqno="0"(고정)`), 응답 `mainList[]`의 **31/31 필드 완전 일치**.
- **NCardHistoryDao/NCardInquiryDao ↔ discount_card_usage/schedule**: `tkUseList[]` 5/5, `trnScdlList[]` 15/15(`stationStringInfo` 포함) 완전 일치. 조회 파라미터(`dcntCrdNo` 단일, 13필드 스케줄질의) 모두 일치.
- **CmtrInfoDao ↔ get_commuter_info**: `jobDvCd∈{"a","b","c"}`(앱 상수 `JOB_DV_CD_A/B/C`와 일치), 3가지 요청 변형(초기조회/인원조회/원표조회) 전부 앱의 `psgCnt,cmtrUtlAgeCd[],psgPrnb[],ogtkSaleWctNo,ogtkSaleDd,ogtkSaleSqno,ogtkRetPwd,inquiryType`와 정확히 매핑. 응답 12필드(`psgList[]` 포함) **완전 일치**.
- **ProductDetailDao/ProductListDao**: wire key가 앱 DTO 필드명(`txtVrRsvNo`)과 다르고 실제 `@Query`/`@Field` 애너테이션(`txtVrRsNo`)을 따라야 하는 함정이 있었는데, 라이브러리는 애너테이션 값을 정확히 사용함 (`read_payloads.py:461-471`).

---

## 3. 문제 상세

### 3.1 [TSF-01] TourTrainInfo — 파서/모델만 존재, 실제로 호출 불가 (partial, low)

`TourTrainInfoDao`(`/classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom`)의 응답 파서(`parse_tour_train_info_response`,
`read_parsers.py:1910-1969`)와 모델(`TourTrainInfoResponse`, `read_models.py:813-829`)은 존재하지만:
- `read_payloads.py`에 대응하는 `build_*_form` 함수가 없음
- `client.py`에 이 경로를 호출하는 메서드가 없음 (`grep tour_train client.py` → 0건)

즉 `parse_tour_train_info_response`는 라이브러리 내에서 아무도 호출하지 않는 죽은 코드다. 이미 `docs/RELEASE_GAP_PLAN.md:132`
G5로 추적되고 있는 항목이며 (`Not ported`), 문서와 실측이 일치한다. 관광열차 특실정보는 핵심 열차조회 흐름은 아니라 낮은 우선순위.

### 3.2 [TSF-02] TrainSchedule 응답 모델이 앱 DTO 대비 근거 없이 ~20개 필드를 추가로 주장 (unverifiable, medium)

`parse_train_schedule_response`/`TrainScheduleResponse`/`TrainScheduleStop`(`parsers.py:573-741`, `models.py:180-243`)은
`actualTrainSchedule.do` 응답에서 앱의 `TrainScheduleDao.TrainScheduleResponse`/`TimeInfo`에 없는 필드를 다수 읽는다.

**앱 DTO의 실제 필드(smali로 재확인, jadx와 일치)**:
- `TrainScheduleDao$TrainScheduleResponse.smali`: `dlayDtlRsnCont, dlayList, msgCont, runDt1, runSegOrdr, trnDptFlg, trnNo1` (7개)
- `TrainScheduleDao$TimeInfo.smali`: `actArvDlayTnum, actArvDt, actArvTm, actDptDt, actDptTm, arvDt, arvTm, dptDt, dptTm, expnArvDlayTnum, expnDptDlayTnum, rgulFlg, saodFlg, stopStnNm` (14개)

**라이브러리가 추가로 읽는 wire key들** (`parsers.py:590-740`): 최상위 `dlayStnConsOrdr, intgMsgCd, msgCd, msgTxt, orgRsStnCd, orgRsStnNm, routCd, routNm, saleRgulFlg, stlbTrnClsfCd, tmnRsStnCd, tmnRsStnNm, trnAttCd, trnSpsFlg, upDnDvCd` (15개), stop 레벨 `stopRsStnCd, stnConsOrdr, runOrdr, dlayFareRetDvCd, dlayFareRetDvCdNm, dlaySoloOprFlg, dturDrvDlayTnum` (7개).

전체 앱 디컴파일 트리(242개 파일)에서 이 키들을 재검색한 결과:
- `stopRsStnCd, stnConsOrdr, dlayFareRetDvCd, dlaySoloOprFlg, dturDrvDlayTnum, dlayStnConsOrdr, orgRsStnCd, saleRgulFlg, tmnRsStnCd, trnAttCd, upDnDvCd` — **앱 전체에서 0건 검색**.
- `intgMsgCd, routCd, stlbTrnClsfCd, trnSpsFlg`만 다른(무관한) DTO에서 발견됨(동일 backend 명명 관례 추정, 이 endpoint에 대한 직접 근거는 아님).

같은 파일(`parsers.py`) 안에서도 `TrainCalendarDay`는 12/12, `_CUSTOMER_TRIP_FIELDS`는 31/31로 정확히 앱과 일치하므로,
이건 이 라이브러리의 일반적 스타일이 아니라 이 함수만의 예외다. 다른 함수들은 전부 `x4/b.java:19`, `a5/k.java:92-94`,
`TrainScheduleDao.java:123`, `SeatSearchActivity.java:201-213`처럼 정확한 근거 인용이 달려 있는데, 이 15+7개 추가
필드에는 그런 인용이 전혀 없다.

**근거로 판단할 수 없는 것**: Gson은 DTO에 선언 안 된 JSON 키를 조용히 무시하므로, 앱 DTO에 없다고 해서 실제 서버 응답에도
없다고 단정할 수는 없다(서버가 앱이 안 쓰는 필드를 더 보낼 개연성은 이 API 계열에서 흔함). 그래서 "틀렸다"가 아니라
**"확인불가"**로 분류한다. 모두 옵셔널 파싱(`_typed_optional_string`)이라 크래시는 없다 — 실제 서버에 없으면 그냥 `None`이
된다.

**실질적 위험**: `tests/fixtures/raw_typed_train_schedule.json`이 이 20개 키를 전부 `"SYNTHETIC-..."` 값으로 박아넣고
있어서, 테스트가 초록불이어도 이 스키마가 검증됐다는 뜻이 아니다 — 다음 감사자가 "테스트 통과 = 확인됨"으로 오독할 위험이
크다.

**권고**: 이 15+7개 필드에 "실서버 미검증(unverified against live traffic)" 주석을 달거나, 근거가 생길 때까지 모델에서
제거하고 `raw`로만 접근하게 하는 편이 안전하다.

### 3.3 [TSF-03] PriceFareDao(TrainCharge) — 앱도 안 쓰는 죽은 엔드포인트, 라이브러리 미구현 (info)

`TrainsInfoService.getPriceFare` (`/classes/com.korail.mobile.trainsInfo.TrainCharge`)는 `TrainsInfoService.java`에
선언은 되어 있지만, 앱 전체(242개 network 파일 + UI 레이어)에서 `PriceFareRequest`를 생성하거나 `dao_price_fare`를
실행하는 코드가 전혀 없다(`grep -rn "PriceFareRequest\b" analysis/jadx/sources/com/korail/talk` → `PriceFareDao.java`
자신과 `TrainsInfoService.java`, `R.java`(리소스 id)만 매칭). 실제 운임조회는 전부 `Price2FareDao`(`trn.prcFare.do`, §행2)로
대체된 것으로 보인다. 라이브러리가 이 엔드포인트를 구현하지 않은 것은 실제 앱 동작을 정확히 반영한 것이며 **결함이 아니다**.

### 3.4 [TSF-04] get_seat_cars/get_seat_inventory 응답에 앱 DTO에 없는 옵셔널 필드 소수 추가 (unverifiable, low)

§3.2보다 훨씬 작은 규모의 동일 패턴:
- `SeatCar.room_class_code`(`h_psrm_cl_cd`), `SeatCar.total_seat_count`(`h_seat_cnt`), `SeatAttribute.code`(`seatAttCd`),
  `SeatCarListResponse.train_class_code`(`h_trn_clsf_cd`)/`train_group_code`(`h_trn_gp_cd`) — `SearchCarListDao`의
  `CarInfo`/`SeatAttInfo`/`SearchCarListResponse`(smali로 재확인: `h_psrm_cl_nm, h_rest_seat_cnt, h_srcar_no,
  seatAttInfos` / `seatAttNm` / `h_rcmd_srcar_no, h_trn_no, srcar_infos`)에는 없음.
- `SeatInventoryResponse.car_type_code`(`car_tp_cd`), `car_no`(`scar_no`), `up_down_division_code`(`up_dn_dv_cd`) —
  `SearchSeatListDao$SearchSeatListResponse`(smali 재확인)에는 없음.

다만 이 키들은 `h_psrm_cl_cd, h_seat_cnt, seatAttCd, car_tp_cd, scar_no, up_dn_dv_cd` 전부 앱의 **다른** DTO
(환불/발권/버스예약 등)에서 실제로 쓰이는 명명 관례라서, §3.2처럼 완전히 근거 없는 것과는 성격이 다르다 — 정황상 타당한
방어적 파싱으로 보이나 이 엔드포인트 자체에 대한 직접 근거는 없다. 전부 옵셔널이라 크래시 없음. **확인불가, 낮은 우선순위.**

### 3.5 [TSF-05] SeatAssignmentSchedule/MergeSeatsInquiry 응답에서 좌석도 연쇄호출에 필요한 필드가 raw로만 접근 가능 (partial, low)

`get_seat_assignment_schedule`/`get_merge_seats_inquiry`가 반환하는 `trains: tuple[TrainScheduleItem, ...]`은
`RsvInquiryResponse.TrainInfo`의 27개 필드만 이름 있는 속성으로 노출한다(§2 참고). 그런데 `h_seat_att_cd`와 `txtGdNo`는
정확히 `build_seat_car_form`/`build_seat_inventory_form`(`payloads.py:171,210`, `train.seat_attribute_code`/
`train.goods_no`)이 다음 단계(좌석도 조회)를 만들 때 필요한 두 입력값이다. 이 두 필드가 `TrainScheduleItem`에 없으므로,
이 두 read-only 응답에서 얻은 열차로 바로 좌석도를 조회하려면 `.raw["h_seat_att_cd"]`/`.raw["txtGdNo"]`를 직접 꺼내야
한다 — 크래시는 아니지만 API 사용자가 눈치채기 어려운 연쇄호출 마찰이다.

### 3.6 [TSF-06] RELEASE_GAP_PLAN.md가 N카드 스케줄/사용내역 갭을 실제보다 낡게 기록 (doc-drift, low)

`docs/RELEASE_GAP_PLAN.md:129-130`은 G2(`research.dcntCrdScheduleView.do`)와 G3(`ticket.dcntCrdUseQry.do`)를
"N-card read family not ported" / "Not ported"로 적어 놓았지만, 실측 결과 둘 다 구현·연결되어 있다
(`client.py:612` `ticket.dcntCrdUseQry.do`, `client.py:651` `dcntCrdScheduleView.do`, 필드 대조는 §2 참고). G4/G5/G9는
문서와 실측이 일치함을 확인했으므로 이 드리프트는 G2/G3 두 항목에 국한된다. 릴리스 계획 문서가 이미 닫힌 갭을 열린 것으로
보여주면 우선순위 재조정을 오도할 수 있다.

### 3.7 [TSF-07] get_seat_inventory의 ctlDvCd가 항상 ""로 고정 — 승차권변경(TCS) 좌석검색 변형은 재현 불가 (partial, low)

`build_seat_inventory_form`(`payloads.py:217`)은 `"ctlDvCd": ""`를 항상 하드코딩한다. 앱은 일반 좌석검색에서는 동일하게
`""`를 쓰지만(`SeatSearchActivity.java:207`), 승차권 변경(TCS) 플로우에서는 `"3584"`를 쓴다
(`TCSOptionsActivity.java:506`, `SeatSearchActivity.java:784,852`). 라이브러리에 `ctlDvCd`를 바꿀 방법이 없으므로 TCS
좌석검색 컨텍스트를 정확히 재현할 수 없다. 다만 TCS 자체(승차권 변경)는 이 슬라이스 밖의 기능이라 우선순위는 낮다.

### 3.8 [TSF-08] research.tripChgOgtk.do (원표 조회) 미구현 — 승차권변경 체인의 선행 조회 (missing, low)

`OgTkInquiryDao`(`ResearchService.java:61-63`)에 대응하는 payload/parser/client 코드가 없다. 이미
`docs/RELEASE_GAP_PLAN.md:131` G4로 추적 중("Change-flow read not ported (needed before tripChgPrsC)"). 승차권 변경
자체가 이 슬라이스 밖의 기능이므로 이 선행조회의 우선순위도 낮다.

### 3.9 [TSF-09] product.payInfo / product.ReservationCancel 미구현 (missing, medium)

- `ProductPaymentCheckDao`(GET `product.payInfo`, `ProductService.java:18-19`)는 payload/parser/model/client 어디에도
  없다. `docs/RELEASE_GAP_PLAN.md:136` G9로 이미 추적됨.
- `ProductCancelDao`(GET `product.ReservationCancel`, `ProductService.java:21-22`, mutation)도 `mutation_*.py`
  포함 전체 검색에서 0건. `docs/RELEASE_GAP_PLAN.md:326`에 이름만 등재되어 있고 구현 여부는 안 적혀 있음 — 실측으로
  **미구현**임을 확인.

둘 다 "여행상품"(product) 예약의 결제확인/취소로, 열차 좌석예약의 결제/취소와는 다른 별도 API 계열이다. 이미 추적 중인
갭이라 신규 발견은 아니지만, 내 담당 패키지(`product/`) 전수 조사 결과로 재확인했다.

### 3.10 부가: ProductDetail/ProductList의 사소한 필드 누락 (raw로 보완됨, info)

- `ProductReservation`(목록)은 `strRsvSttNm`(상태명)만 매핑하고 `strRsvSttCd`(상태 코드)는 매핑하지 않음. `raw`에는 남아있음.
- `ProductDetailResponse`(상세)는 `strGdSqno`(상품 순번 — `ProductCancelDao.txtGdSqno`/`ProductPaymentCheckDao.txtRsvGdSqno`
  체이닝에 쓰일 수 있는 값), `strStlSttCd`(결제상태 코드), `strInt11`(의미 불명)을 매핑하지 않음. `raw`에는 남아있음.

크래시 없음, `raw` 폴백 존재. §3.9의 미구현 취소/결제확인 엔드포인트가 언젠가 구현되면 `strGdSqno`를 named field로
승격하는 편이 연쇄호출에 편리할 것.

---

## 4. Price2FareDao의 trnCnt 자기대입 버그 — 앱 자체 버그, 라이브러리와 무관 (info)

`Price2FareDao$Price2FareRequest.setTrnCnt()`가 smali에서 확인한 바로는 `iget-object p1,...trnCnt` 후 즉시
`iput-object p1,...trnCnt`로, 전달된 파라미터를 무시하고 필드의 기존 값(항상 null)을 자기 자신에게 다시 쓰는 자기대입
버그다(`Price2FareDao$Price2FareRequest.smali:149-157`). 즉 앱은 실제로 `trnCnt` 필드를 절대 세팅하지 못하고 항상
null로 보낸다. 라이브러리의 `build_price_fare_quote_form`은애초에 `trnCnt` 키를 아예 만들지 않는데, `payloads.py:126-132`
주석이 이미 확립한 프로젝트 지식(Retrofit이 null `@Field`를 드롭한다 — `txtGdNo`/`gdNo` 처리에서도 동일 근거 사용)과
일관된다. 결과적으로 앱과 라이브러리 둘 다 이 필드를 사실상 전송하지 않으므로 **일치**하며, 이건 단지 흥미로운 앱측
버그의 기록일 뿐 라이브러리 결함이 아니다.

---

## 5. 요약 수치

- `app_functions_extracted` = 22 (4개 서비스 인터페이스 메서드 전수)
- `implemented_count` = 17 (완전 도달가능 + 필드검증 통과)
- 부분 구현 1 (TourTrainInfo)
- 미구현(실질 갭, 이미 추적됨) 3 (OgTkInquiry, product.payInfo, product.ReservationCancel)
- 미구현(앱 자체 죽은 코드, 결함 아님) 1 (PriceFareDao/TrainCharge)
- critical/high 등급 findings: **0건**
