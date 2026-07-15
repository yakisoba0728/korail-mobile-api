import re
from pathlib import Path


README = Path(__file__).parents[1] / "README.md"
STATUS = Path(__file__).parents[1] / "docs" / "api-status-by-service.md"
BUILD_GUIDE = Path(__file__).parents[1] / "docs" / "library-build-guide.md"
PROGRESS = Path(__file__).parents[1] / "docs" / "IMPLEMENTATION_PROGRESS.md"
HANDOFF = Path(__file__).parents[1] / "docs" / "NEXT_SESSION.md"
CHANGELOG = Path(__file__).parents[1] / "CHANGELOG.md"


def test_readme_describes_fixed_rt_dynapath_consistently():
    text = README.read_text(encoding="utf-8")
    assert "This work is static analysis only." not in text
    assert "The committed material is documentation" not in text
    assert "caller-supplied" in text
    assert "fixed `rt=0`" in text
    assert "SDK version `v1`" in text
    assert "DynapathTokenSettings" in text
    assert "compatibility-only" not in text
    assert "KorailProbeDynapathTokenProvider" not in text
    assert "rolling-delta" not in text
    assert "KORAIL_DYNAPATH_DEVICE_ID" in text
    assert "KORAIL_ADVERTISING_ID" in text
    assert "KORAIL_ADVERTISING_ID is optional" in text
    assert "get_app_data()" in text
    assert "get_notice()" in text
    assert "/file/CACHE/prdMobilePlusMain.cache" in text
    assert "/file/CACHE/prdMobilePlusNotice.cache" in text
    assert "appDataLoaded" in text
    assert "noticeLoaded" in text
    assert "get_maas_menu_list()" in text
    assert "menuList[].addSrvDvCd" in text
    assert "explicit override" in text


def test_readme_documents_every_successful_read_expansion_method_and_boundary():
    text = README.read_text(encoding="utf-8")
    for method_name in (
        "get_service_status",
        "get_cart_list",
        "get_deposit_banks",
        "get_delay_discount_tickets",
        "get_discount_coupons",
        "get_pass_available_dates",
        "get_trip_menu",
        "get_product_reservations",
        "get_product_detail",
        "get_ticket_receipt",
        "get_reservation_history",
    ):
        assert f"{method_name}(" in text
    assert "11 new public read methods" in text
    assert "27 exact login/read routes" in text
    assert "Five methods parsed successfully" in text
    assert "four stopped at `KorailProtocolError`" in text
    assert "two" in text
    assert "identifier-dependent calls were not issued" in text
    assert "No new DynaPath route" in text
    assert "WRG000000" in text
    assert "P100" in text
    assert "typed empty" in text
    assert "Deposit-bank and trip-menu reads require an authenticated session" in text
    assert "result-only success envelopes" in text
    assert "caller-owned identifiers" in text
    assert "reservation, payment, and mutation routes remain excluded" in text
    assert "reservation_no=reservation_no" in text
    assert "reservation_sequence=reservation_sequence" in text


def test_status_and_progress_documents_match_current_inventory_and_coverage():
    status = STATUS.read_text(encoding="utf-8")
    assert "| 성공 | 31 |" in status
    assert "| 실패 | 10 |" in status
    assert "| 미실행 | 124 |" in status
    assert "| 전체 | 165 |" in status
    assert "Package coverage: 45 exact login/read routes and 48 public methods" in status
    assert "Historical pre-revalidation inventory was 28 successful, 9 failed," in status
    assert "and 128 unexecuted" in status
    assert "| `CustService` | 고객 할인 대상 조회 | 1 | 0 | 1 | 0 |" in status
    assert "| `ResearchService` | 열차/좌석/N카드 관련 조회 | 11 | 3 | 2 | 6 |" in status
    assert "| `TicketService` | 발권, 승차권 관리, 체크인, 티켓 정보 | 19 | 2 | 0 | 17 |" in status
    assert "| `ReservationService` | 승차권 예약 및 좌석 조건 | 4 | 1 | 1 | 2 |" in status
    assert "| `TrainsInfoService` | 열차/객차/자유석 정보 조회 | 6 | 3 | 0 | 3 |" in status
    assert (
        "## CashReceipt\n\n- 역할: 현금영수증 발급\n"
        "- 상태: 총 1개 / 성공 0 / 실패 0 / 미실행 1" in status
    )
    assert (
        "## CustService\n\n- 역할: 고객 할인 대상 조회\n"
        "- 상태: 총 1개 / 성공 0 / 실패 1 / 미실행 0" in status
    )
    assert (
        "| 43 | `mchdDcntTgt` | POST | "
        "`/classes/com.korail.mobile.cust.mchdDcntTgt.do` | "
        "고객 할인 대상 조회 | 실패 | `WRC800029`; `KorailAppError`, "
        "1회 호출, 재시도 없음 |" in status
    )
    assert (
        "| 116 | `getCustTripInfo` | POST | "
        "`/classes/com.korail.mobile.research.custTripInfo.do` | "
        "고객 여행 편의설정 조회 | 성공 | 0 rows |" in status
    )
    assert (
        "| 142 | `getMaasServiceDetailList` | POST | "
        "`/classes/com.korail.mobile.copt.gdReqQry.do` | "
        "MAAS 서비스 상세 목록 | 성공 | current form, 0 rows |" in status
    )
    assert (
        "| 144 | `getTripChgDate` | POST | "
        "`/classes/com.korail.mobile.reservation.tripChgDate.do` | "
        "여정변경 가능일 조회 | 성공 | 15 rows |" in status
    )
    assert (
        "| 157 | `getPriceFare` | POST | "
        "`/classes/com.korail.mobile.trainsInfo.TrainCharge` | 운임 조회 | "
        "미실행 | `skipped_no_typed_leg`; 0회 호출 |" in status
    )
    assert (
        "| 124 | `getGuideSeatCnd` | POST | "
        "`/classes/com.korail.mobile.reservation.guideSeatCnd.do` | "
        "좌석 조건 안내 | 실패 |" in status
    )
    assert "server-supplied `rqSeatAttCd`" in status
    assert "`KorailAppError`, 재시도 없음" in status
    assert (
        "| 155 | `getFresScar` | POST | "
        "`/classes/com.korail.mobile.trn.fresScar.do` | 자유석/객차 조회 | "
        '성공 | exact `strResult="SUCC"`, typed parse 성공 |' in status
    )
    assert "bounded live structural evidence" in status
    assert "25 successful operations" in status
    assert "three input-dependent skips" in status

    service_rows = re.findall(
        r"^\| `[^`]+` \| [^|]+ \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|$",
        status,
        flags=re.MULTILINE,
    )
    assert len(service_rows) == 35
    service_totals = tuple(sum(int(row[index]) for row in service_rows) for index in range(4))
    assert service_totals == (165, 31, 10, 124)

    guide = BUILD_GUIDE.read_text(encoding="utf-8")
    guide_normalized = " ".join(guide.split())
    assert "성공 28 / 실패 9 / 미실행 128" in guide
    assert "| `ReservationService` | 4 | 1 | 1 | 2 |" in guide
    assert "| `TrainsInfoService` | 6 | 3 | 0 | 3 |" in guide
    assert "27 parsed responses" in guide_normalized
    assert "one expected `KorailAppError`" in guide_normalized
    assert "zero unexpected failures" in guide_normalized
    assert "성공 27 / 실패 8 / 미실행 130" not in guide
    assert "성공 25 / 실패 8 / 미실행 132" not in guide

    progress = PROGRESS.read_text(encoding="utf-8")
    assert "45 exact login/read routes" in progress
    assert "48 public methods" in progress
    assert "75" in progress
    assert "IRG000000" in progress


def test_docs_describe_static_p0_menu_reads_and_exclude_crew_mutation():
    readme = README.read_text(encoding="utf-8")
    progress = PROGRESS.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    for method_name in (
        "get_pass_menu",
        "get_crew_request_list",
        "get_commuter_kind_menu",
    ):
        assert f"{method_name}(" in readme
    for path in (
        "/classes/com.korail.mobile.pass.passMenu.do",
        "/classes/com.korail.mobile.push.crwCallRq.do",
        "/classes/com.korail.mobile.push.cmtrKnd.do",
    ):
        assert path in readme
    assert "caller-supplied runtime discriminator" in readme
    assert "/classes/com.korail.mobile.push.callCrew.do" in readme
    assert "remains excluded" in readme
    assert "static APK evidence and synthetic fixtures only" in readme
    assert "45 exact read/login routes" in progress
    for document in (readme, progress, status, handoff, changelog):
        assert "session-unverified" in document
    assert "live verification only after login" in readme
    assert (
        "No live request or raw response body was used to implement or verify "
        "this increment." in " ".join(readme.split())
    )
    assert "Until a bounded live check can run after login" in " ".join(readme.split())
    assert "Three account-neutral reference methods" not in readme
    assert "Account-neutral pass-menu" not in progress
    assert "typed account-neutral pass-menu" not in changelog


def test_readme_documents_typed_seat_inventory_scope_and_live_boundary():
    text = README.read_text(encoding="utf-8")
    assert "get_seat_cars(" in text
    assert "get_seat_inventory(" in text
    assert "main menu `11`" in text
    assert "general room" in text
    assert "seat attribute `015`" in text
    assert "include_dynapath=False" in text
    assert "capture_seat_inventory_evidence.py" in text
    assert "at most one login operation" in text
    assert "never followed" in text
    assert "5 cars" in text
    assert "75 seat rows" in text
    assert "IRG000000" in text
    assert "repeated seat labels" in text
    assert "service-status preflight" in text


def test_docs_describe_raw_backed_typed_core_and_compatibility_boundary():
    readme = README.read_text(encoding="utf-8")
    progress = PROGRESS.read_text(encoding="utf-8")

    for text in (readme, progress):
        normalized = " ".join(text.split())
        assert "raw-backed typed response core" in text
        assert "StationInfoResponse" in text
        assert "TrainCalendarResponse" in text
        assert "TrainScheduleResponse" in text
        assert "TransferStationListResponse" in text
        assert "TrainSearchMetadata" in text
        assert "request payload semantics remain unchanged" in text
        assert "appended, defaulted fields" in text
        assert "raw mappings remain `repr=False`" in text
        assert "Client call parameters remain unchanged" in normalized
        assert (
            "return annotations for five existing read methods are narrowed "
            "to typed responses" in normalized
        )
    assert "all client method signatures are preserved" not in readme
    assert "Existing routes, public signatures" not in progress
    for key in (
        "h_std_rest_seat_cnt",
        "h_fst_rest_seat_cnt",
        "h_free_sracar_cnt",
        "h_rsv_wait_ps_cnt",
    ):
        assert key in readme


def test_readme_documents_bounded_live_p0_train_reads_and_closed_requests():
    text = README.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    for method_name in (
        "get_free_seat_car_info",
        "get_guide_seat_condition",
        "get_seat_assignment_schedule",
        "get_merge_seats_inquiry",
    ):
        assert f"{method_name}(" in text
    for request_name in (
        "FreeSeatCarRequest",
        "GuideSeatConditionRequest",
        "SeatAssignmentScheduleRequest",
        "MergeSeatsInquiryRequest",
    ):
        assert request_name in text
    for java_name in (
        "getFresScar",
        "getGuideSeatCnd",
        "getAssignScheduleView",
        "getMergeSeatsInquiry",
    ):
        assert java_name in text
    assert "45 routes and 48 public methods" in text
    assert "synthetic fixtures" in text
    assert "does not accept `TrainSummary`" in text
    assert (
        "Initial implementation used only static APK evidence and synthetic "
        "fixtures." in normalized
    )
    assert (
        '`getFresScar` returned exact `strResult="SUCC"` and parsed successfully.'
        in normalized
    )
    assert "`getGuideSeatCnd` returned a full `FAIL` application envelope" in normalized
    assert "surfaced as `KorailAppError` and was not retried" in normalized
    assert (
        "R37 `getAssignScheduleView` and R51 `getMergeSeatsInquiry` remain "
        "static-only and unexecuted." in normalized
    )
    assert "does not establish pre-login server behavior" in normalized
    assert (
        "No live call was made, and all parser coverage uses synthetic fixtures."
        not in normalized
    )


def test_docs_record_bounded_p0_live_counts_and_replay():
    readme = " ".join(README.read_text(encoding="utf-8").split())
    progress = " ".join(PROGRESS.read_text(encoding="utf-8").split())
    handoff = " ".join(HANDOFF.read_text(encoding="utf-8").split())
    changelog = " ".join(CHANGELOG.read_text(encoding="utf-8").split())

    assert "made 28 requests and received 28 responses" in readme
    assert "25 successful operations" in readme
    assert "one expected typed application failure" in readme
    assert "three input-dependent skips" in readme
    assert "Deposit-bank and trip-menu reads succeeded after login" in readme
    for text in (progress, handoff):
        assert "27 parsed responses" in text
        assert "one expected `KorailAppError`" in text
        assert "zero unexpected failures" in text
    assert (
        "pre-P0-evidence reviewed offline gate was `1246 passed, 1 deselected`; "
        "after adding the documentation contract coverage in this increment, "
        "the fresh non-live gate is `1247 passed, 1 deselected`" in readme
    )
    assert (
        "historical full offline release gate reported `1246 passed, 1 "
        "deselected`. After adding the P0 live-evidence documentation contract "
        "test, the fresh non-live gate reports `1247 passed, 1 deselected`"
        in progress
    )
    assert (
        "historical reviewed offline gate of `1246 passed, 1 deselected`; the "
        "fresh P0 live-evidence documentation gate reports `1247 passed, 1 "
        "deselected`" in handoff
    )
    assert "authenticated 28-request, 28-response run" in changelog
    assert "25 successful operations" in changelog
    assert "three input-dependent skips" in changelog
    assert '`getFresScar` returned exact `strResult="SUCC"` and parsed' in changelog
    assert "full `FAIL` application envelope for the server-supplied seat attribute" in changelog
    assert "expected typed application failure without a retry" in changelog
    assert "27 parsed responses" in changelog
    assert "one expected `KorailAppError`" in changelog
    assert "zero unexpected failures" in changelog


def test_readme_documents_static_only_limousine_read_contracts():
    text = README.read_text(encoding="utf-8")
    for method_name in (
        "get_limousine_schedules",
        "get_limousine_seat_inventory",
        "get_limousine_schedule_view",
    ):
        assert f"{method_name}(" in text
    assert "caller-supplied service" in text
    assert "caller-supplied menu" in text
    assert "DynaPath-disabled" in text
    assert "No live call was made for this increment" in text
    assert "seat selection" in text


def test_docs_record_fixed_account_reads_and_tour_train_holdback():
    documents = [
        README.read_text(encoding="utf-8"),
        PROGRESS.read_text(encoding="utf-8"),
        HANDOFF.read_text(encoding="utf-8"),
        CHANGELOG.read_text(encoding="utf-8"),
    ]
    readme = documents[0]
    for method_name in (
        "get_multi_child_discount_targets",
        "get_customer_trip_info",
        "get_maas_service_details",
        "get_trip_change_dates",
    ):
        assert f"{method_name}(" in readme
    for path in (
        "/classes/com.korail.mobile.cust.mchdDcntTgt.do",
        "/classes/com.korail.mobile.research.custTripInfo.do",
        "/classes/com.korail.mobile.copt.gdReqQry.do",
        "/classes/com.korail.mobile.reservation.tripChgDate.do",
    ):
        assert path in readme
    for text in documents:
        normalized = " ".join(text.split())
        assert "strCustNo" in text
        assert "R54" in text
        assert "historical" in normalized.casefold()
        assert "pre-revalidation" in normalized.casefold()
        assert "28 successful, 9 failed, and 128 unexecuted" in normalized
        assert "31 successful, 10 failed, and 124 unexecuted" in normalized
        assert "mutation" in normalized
    normalized_readme = " ".join(readme.split())
    assert "no `get_tour_train_info` client method" in normalized_readme
    assert "no registered safety route" in normalized_readme
    assert "no raw-string request builder" in normalized_readme


def test_docs_record_next_safe_read_bounded_live_evidence_without_secrets():
    documents = {
        "README": README.read_text(encoding="utf-8"),
        "CHANGELOG": CHANGELOG.read_text(encoding="utf-8"),
        "progress": PROGRESS.read_text(encoding="utf-8"),
        "handoff": HANDOFF.read_text(encoding="utf-8"),
        "status": STATUS.read_text(encoding="utf-8"),
    }
    for name, document in documents.items():
        normalized = " ".join(document.split())
        assert "31 successful, 10 failed, and 124 unexecuted" in normalized, name
        assert "empty advertising ID" in normalized, name
        assert "customer_no" in normalized, name
        assert "WRC800029" in normalized, name
        assert "0 rows" in normalized, name
        assert "15 rows" in normalized, name
        assert "10 rows" in normalized, name
        assert "skipped_no_typed_leg" in normalized, name
        assert "R17, R31, R39, and R54 were not called" in normalized, name
        assert "No mutation" in normalized, name

    readme = " ".join(documents["README"].split())
    assert "R13 made one request" in readme
    assert "surfaced as `KorailAppError` and was not retried" in readme
    assert "R32 succeeded with 0 rows" in readme
    assert "current-form R43 succeeded with 0 rows" in readme
    assert "R45 succeeded with 15 rows" in readme
    assert "existing safe train search succeeded with 10 rows" in readme
    assert "R52 made zero requests" in readme
