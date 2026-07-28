import inspect
import re
from pathlib import Path

from korail_mobile_api import KorailClient


README = Path(__file__).parents[1] / "README.md"
# The README was rewritten for people who want to USE the library on
# 2026-07-26; the audit log it used to be moved WHOLE to docs/verification-
# record.md. Every assertion below that used to read README now reads whichever
# document actually carries its claim: the capability names, the safety model,
# the error taxonomy's "what should a caller do" and the current repository
# counts stayed in README, and the evidence behind them -- APK citations, live
# run codes, superseded claims -- follows the prose into RECORD. Nothing was
# dropped and nothing was loosened; each string is still asserted exactly once,
# somewhere it is actually supposed to appear.
RECORD = Path(__file__).parents[1] / "docs" / "verification-record.md"
STATUS = Path(__file__).parents[1] / "docs" / "api-status-by-service.md"
BUILD_GUIDE = Path(__file__).parents[1] / "docs" / "library-build-guide.md"
PROGRESS = Path(__file__).parents[1] / "docs" / "IMPLEMENTATION_PROGRESS.md"
# The standalone session-handoff note (docs/NEXT_SESSION.md) was removed during
# the docs consolidation; its handoff facts now live in IMPLEMENTATION_PROGRESS.md
# (see its "Package Handoff Summary" section), so handoff assertions read there.
HANDOFF = Path(__file__).parents[1] / "docs" / "IMPLEMENTATION_PROGRESS.md"
CHANGELOG = Path(__file__).parents[1] / "CHANGELOG.md"
SECURITY = Path(__file__).parents[1] / "SECURITY.md"


def test_record_describes_fixed_rt_dynapath_consistently():
    # The three account-neutral cache/menu reads are a capability, so they stay
    # named in the README; the DynaPath token contract and the live-smoke
    # environment behind them are evidence and moved with the record.
    readme = README.read_text(encoding="utf-8")
    for method_name in ("get_app_data()", "get_notice()", "get_maas_menu_list()"):
        assert method_name in readme

    text = RECORD.read_text(encoding="utf-8")
    assert "This work is static analysis only." not in text
    assert "The committed material is documentation" not in text
    assert "caller-supplied" in text
    assert "fixed `rt=0`" in text
    assert "SDK version `v1.0.3`" in text
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


def test_record_documents_every_successful_read_expansion_method_and_boundary():
    text = RECORD.read_text(encoding="utf-8")
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
    assert "| 성공 | 33 |" in status
    assert "| 실패 | 14 |" in status
    assert "| 미실행 | 118 |" in status
    assert "| 전체 | 165 |" in status
    assert "Package coverage: 60 exact login/read routes and 77 public methods" in status
    assert "Historical pre-revalidation inventory was 28 successful, 9 failed," in status
    assert "and 128 unexecuted" in status
    assert "| `CustService` | 고객 할인 대상 조회 | 1 | 0 | 1 | 0 |" in status
    assert "| `ResearchService` | 열차/좌석/N카드 관련 조회 | 11 | 3 | 2 | 6 |" in status
    assert "| `TicketService` | 발권, 승차권 관리, 체크인, 티켓 정보 | 19 | 3 | 1 | 15 |" in status
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
    for heading, role, totals in (
        (
            "ResearchService",
            "열차/좌석/N카드 관련 조회",
            "11개 / 성공 3 / 실패 2 / 미실행 6",
        ),
        (
            "TicketService",
            "발권, 승차권 관리, 체크인, 티켓 정보",
            "19개 / 성공 3 / 실패 1 / 미실행 15",
        ),
        (
            "TrainsInfoService",
            "열차/객차/자유석 정보 조회",
            "6개 / 성공 3 / 실패 0 / 미실행 3",
        ),
    ):
        assert (
            f"## {heading}\n\n- 역할: {role}\n- 상태: 총 {totals}" in status
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
    assert service_totals == (165, 33, 14, 118)

    guide = BUILD_GUIDE.read_text(encoding="utf-8")
    guide_normalized = " ".join(guide.split())
    assert "## Current Inventory" in guide
    assert "Runtime test status | 성공 33 / 실패 14 / 미실행 118" in guide
    assert "| `CustService` | 1 | 0 | 1 | 0 |" in guide
    assert "| `ResearchService` | 11 | 3 | 2 | 6 |" in guide
    assert "| `ReservationService` | 4 | 1 | 1 | 2 |" in guide
    assert "| `TicketService` | 19 | 3 | 1 | 15 |" in guide
    assert "| `TrainsInfoService` | 6 | 3 | 0 | 3 |" in guide
    guide_service_table = guide.split("## Service Runtime Status", 1)[1].split(
        "The historical pre-revalidation", 1
    )[0]
    guide_service_rows = re.findall(
        r"^\| `[^`]+` \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|$",
        guide_service_table,
        flags=re.MULTILINE,
    )
    assert len(guide_service_rows) == 35
    guide_totals = tuple(
        sum(int(row[index]) for row in guide_service_rows) for index in range(4)
    )
    assert guide_totals == (165, 33, 14, 118)
    assert "27 parsed responses" in guide_normalized
    assert "one expected `KorailAppError`" in guide_normalized
    assert "zero unexpected failures" in guide_normalized
    for stale_totals in (
        "성공 28 / 실패 9 / 미실행 128",
        "성공 27 / 실패 8 / 미실행 130",
        "성공 25 / 실패 8 / 미실행 132",
    ):
        assert stale_totals not in guide

    progress = PROGRESS.read_text(encoding="utf-8")
    assert "60 exact login/read routes" in progress
    assert "- Live-successful inventory entries: 32" in progress
    assert "IRG000000" in progress

    # The public-method count is measured, not quoted. Pinning the sentence
    # "72 public methods" looked like a guard and was not one: the count had
    # moved to 74 while the assertion still passed, because an older sentence
    # elsewhere in the same file satisfied the substring. A stale number in
    # prose is now a failure with the real figure in the message.
    actual_public_methods = len(
        [
            name
            for name, _ in inspect.getmembers(KorailClient, inspect.isfunction)
            if not name.startswith("_")
        ]
    )
    assert actual_public_methods == 77, (
        f"KorailClient now exposes {actual_public_methods} public methods; "
        "update this number and every doc that states it "
        "(README.md, api-status-by-service.md, verification-record.md, "
        "IMPLEMENTATION_PROGRESS.md)."
    )
    assert f"{actual_public_methods} public methods" in progress
    # ...and no sentence may claim the old figure as the CURRENT one. The
    # number survives in a milestone bullet, which is legitimate history, so
    # the check is on tense rather than on the digits: "exposed 72" records the
    # past, "exposes 72" asserts a present that is no longer true.
    # Every superseded figure is listed, not just the first one: 74 became
    # history when the 비회원 오프라인 반환 pair was removed on 2026-07-27 and
    # landed, and a guard that only knows about 72 would let the next stale
    # sentence through exactly as the "72"-only version let 74 through.
    stale_present_tense = [
        line
        for line in progress.splitlines()
        if re.search(
            r"(exposes|allows|boundary is)[^.]*\b(72|74) public methods",
            line,
        )
    ]
    assert not stale_present_tense, stale_present_tense


def test_ticket_reference_docs_keep_static_only_rows_and_scope_consistent():
    status = STATUS.read_text(encoding="utf-8")
    expected_rows = {
        137: (
            "`dlvRcvCust`",
            "/classes/com.korail.mobile.tk.dlvRcvCust.do",
        ),
        138: (
            "`duplicationCheck`",
            "/classes/com.korail.mobile.ticket.ticketDupCheck.do",
        ),
        146: (
            "`pbpAcepSpec`",
            "/classes/com.korail.mobile.tk.pbpAcepSpec.do",
        ),
        148: (
            "`plfNo`",
            "/classes/com.korail.mobile.tk.plfNo.do",
        ),
    }
    lines = status.splitlines()
    for row_no, (method, path) in expected_rows.items():
        matches = [line for line in lines if line.startswith(f"| {row_no} |")]
        assert len(matches) == 1
        row = matches[0]
        assert method in row
        assert path in row
        assert "| 미실행 | static-only / live 미실행 |" in row

    r149_rows = [line for line in lines if line.startswith("| 149 |")]
    assert len(r149_rows) == 1
    assert "`rcntDlvHst`" in r149_rows[0]
    assert "/classes/com.korail.mobile.tk.rcntDlvHst.do" in r149_rows[0]
    assert "| 성공 | `1 row, 1회 호출, 재시도 없음` |" in r149_rows[0]

    common_scope_claim = (
        "The ticket-reference implementation itself used no live I/O and "
        "added no mutation capability."
    )
    for document in (RECORD, CHANGELOG, PROGRESS, HANDOFF):
        normalized = " ".join(document.read_text(encoding="utf-8").split())
        assert common_scope_claim in normalized


def test_docs_describe_static_p0_menu_reads_and_exclude_crew_mutation():
    readme = README.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    progress = PROGRESS.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    for method_name in (
        "get_pass_menu",
        "get_crew_request_list",
        "get_commuter_kind_menu",
    ):
        assert f"{method_name}(" in record
    for path in (
        "/classes/com.korail.mobile.pass.passMenu.do",
        "/classes/com.korail.mobile.push.crwCallRq.do",
        "/classes/com.korail.mobile.push.cmtrKnd.do",
    ):
        assert path in record
    assert "caller-supplied runtime discriminator" in record
    # The crew-call exclusion is a boundary a USER has to know about, so it is
    # one of the few evidence-flavoured claims that stayed in the README. The
    # README is Korean, so the claim is pinned in Korean.
    assert "/classes/com.korail.mobile.push.callCrew.do" in readme
    assert "제외되어 있다" in readme
    assert "static APK evidence and synthetic fixtures only" in record
    assert "60 exact read/login routes" in progress
    for document in (record, progress, status, handoff, changelog):
        assert "session-unverified" in document
    assert "live verification only after login" in record
    assert (
        "No live request or raw response body was used to implement or verify "
        "this increment." in " ".join(record.split())
    )
    assert "Until a bounded live check can run after login" in " ".join(record.split())
    assert "Three account-neutral reference methods" not in record
    assert "Account-neutral pass-menu" not in progress
    assert "typed account-neutral pass-menu" not in changelog


def test_docs_document_typed_seat_inventory_scope_and_live_boundary():
    # The two methods are a capability; the fixed request shape and the bounded
    # evidence run that proved it are the record's.
    readme = README.read_text(encoding="utf-8")
    assert "get_seat_cars(" in readme
    assert "get_seat_inventory(" in readme

    text = RECORD.read_text(encoding="utf-8")
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
    record = RECORD.read_text(encoding="utf-8")
    progress = PROGRESS.read_text(encoding="utf-8")

    for text in (record, progress):
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
    assert "all client method signatures are preserved" not in record
    assert "Existing routes, public signatures" not in progress
    for key in (
        "h_std_rest_seat_cnt",
        "h_fst_rest_seat_cnt",
        "h_free_sracar_cnt",
        "h_rsv_wait_ps_cnt",
    ):
        assert key in record


def test_docs_document_bounded_live_p0_train_reads_and_closed_requests():
    # The package boundary is a repository fact and stays in the README; the
    # four closed request contracts and the bounded run that exercised them are
    # evidence and moved with the record. The README states it in Korean, and
    # both figures are measured here rather than transcribed, so adding a route
    # or a public method fails this test instead of rotting the sentence.
    from korail_mobile_api import safety

    route_count = len(set(safety.KORAIL_READ_ONLY_ROUTES))
    method_count = len(
        [
            name
            for name, _ in inspect.getmembers(KorailClient, inspect.isfunction)
            if not name.startswith("_")
        ]
    )
    assert (
        f"라우트 {route_count}개와 공개 메서드 {method_count}개"
        in README.read_text(encoding="utf-8")
    )

    text = RECORD.read_text(encoding="utf-8")
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
    assert "60 routes and 77 public methods" in text
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
    record = " ".join(RECORD.read_text(encoding="utf-8").split())
    progress = " ".join(PROGRESS.read_text(encoding="utf-8").split())
    handoff = " ".join(HANDOFF.read_text(encoding="utf-8").split())
    changelog = " ".join(CHANGELOG.read_text(encoding="utf-8").split())

    assert "made 28 requests and received 28 responses" in record
    assert "25 successful operations" in record
    assert "one expected typed application failure" in record
    assert "three input-dependent skips" in record
    assert "Deposit-bank and trip-menu reads succeeded after login" in record
    for text in (progress, handoff):
        assert "27 parsed responses" in text
        assert "one expected `KorailAppError`" in text
        assert "zero unexpected failures" in text
    # Only the HISTORICAL gate figures are pinned here. 1246 and 1247 were true
    # on the days they were written, can never change again, and a literal
    # string is the right way to keep a fact that is finished.
    #
    # The CURRENT figure used to be pinned alongside them -- the literal "2398
    # passed, 1 deselected" appeared four times across three documents and was
    # asserted in two test modules. Adding one test invalidated all of it at
    # once, which is the same way the sibling srt repository's README came to
    # advertise 1607 tests for a suite that ran 1662. It is now derived from the
    # suite's own collection in
    # tests/test_release_readiness.py::test_repository_truth_and_full_mutation_policy,
    # which asserts the derived string in README.md, docs/verification-record.md
    # and docs/IMPLEMENTATION_PROGRESS.md. Do not re-pin it here.
    assert (
        "Earlier gates in this repository's history were `1246 passed, 1 "
        "deselected` before the P0 live-evidence documentation coverage and "
        "`1247 passed, 1 deselected` directly after it" in record
    )
    assert (
        "Historically the same gate reported `1246 passed, 1 deselected` before "
        "the P0 live-evidence documentation contract test and `1247 passed, 1 "
        "deselected` directly after it" in progress
    )
    assert (
        "the historical gates were `1246 passed, 1 deselected` and, after the "
        "P0 live-evidence documentation coverage, `1247 passed, 1 deselected`"
        in handoff
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


def test_docs_document_static_only_limousine_read_contracts():
    # The three methods are a capability and are named in the README's read
    # table too; their closed request contracts stayed with the record.
    readme = README.read_text(encoding="utf-8")
    text = RECORD.read_text(encoding="utf-8")
    for method_name in (
        "get_limousine_schedules",
        "get_limousine_seat_inventory",
        "get_limousine_schedule_view",
    ):
        assert f"{method_name}(" in readme
        assert f"{method_name}(" in text
    assert "caller-supplied service" in text
    assert "caller-supplied menu" in text
    assert "DynaPath-disabled" in text
    assert "No live call was made for this increment" in text
    assert "seat selection" in text


def test_docs_record_fixed_account_reads_and_tour_train_holdback():
    documents = [
        RECORD.read_text(encoding="utf-8"),
        PROGRESS.read_text(encoding="utf-8"),
        HANDOFF.read_text(encoding="utf-8"),
        CHANGELOG.read_text(encoding="utf-8"),
    ]
    record = documents[0]
    for method_name in (
        "get_multi_child_discount_targets",
        "get_customer_trip_info",
        "get_maas_service_details",
        "get_trip_change_dates",
    ):
        assert f"{method_name}(" in record
    for path in (
        "/classes/com.korail.mobile.cust.mchdDcntTgt.do",
        "/classes/com.korail.mobile.research.custTripInfo.do",
        "/classes/com.korail.mobile.copt.gdReqQry.do",
        "/classes/com.korail.mobile.reservation.tripChgDate.do",
    ):
        assert path in record
    for text in documents:
        normalized = " ".join(text.split())
        assert "strCustNo" in text
        assert "R54" in text
        assert "historical" in normalized.casefold()
        assert "pre-revalidation" in normalized.casefold()
        assert "28 successful, 9 failed, and 128 unexecuted" in normalized
        assert (
            "pre-R149 inventory was 31 successful, 10 failed, and 124 "
            "unexecuted" in normalized
        )
        assert "mutation" in normalized
    normalized_record = " ".join(record.split())
    assert "no `get_tour_train_info` client method" in normalized_record
    assert "no registered safety route" in normalized_record
    assert "no raw-string request builder" in normalized_record


def test_docs_record_next_safe_read_bounded_live_evidence_without_secrets():
    documents = {
        "record": RECORD.read_text(encoding="utf-8"),
        "CHANGELOG": CHANGELOG.read_text(encoding="utf-8"),
        "progress": PROGRESS.read_text(encoding="utf-8"),
        "handoff": HANDOFF.read_text(encoding="utf-8"),
        "status": STATUS.read_text(encoding="utf-8"),
        "guide": BUILD_GUIDE.read_text(encoding="utf-8"),
    }
    for name, document in documents.items():
        normalized = " ".join(document.split())
        assert (
            "pre-R149 inventory was 31 successful, 10 failed, and 124 "
            "unexecuted" in normalized
        ), name
        assert "empty advertising ID" in normalized, name
        assert "customer_no" in normalized, name
        assert "WRC800029" in normalized, name
        assert "0 rows" in normalized, name
        assert "15 rows" in normalized, name
        assert "10 rows" in normalized, name
        assert "skipped_no_typed_leg" in normalized, name
        assert "R17, R31, R39, and R54 were not called" in normalized, name
        assert "No mutation" in normalized, name
        assert "one successful login call" in normalized, name
        assert (
            "confirmed logged-in state and customer-number presence"
            in normalized
        ), name
        assert "called only R149 once" in normalized, name
        assert "succeeded with one row and was not retried" in normalized, name
        assert "R137, R138, R146, and R148 made zero calls" in normalized, name
        assert (
            "No mutation, raw response, PII, credential, or server message was retained"
            in normalized
        ), name

    forbidden_patterns = {
        "concrete credential assignment": re.compile(
            r"(?im)^\s*(?:export\s+)?(?:KORAIL|SRT)_"
            r"(?:MEMBER_NO|PASSWORD|LOGIN_ID|USER_ID|PHONE|EMAIL)\s*=\s*"
            r"(?![\"']?<)(?!<)[^\s#]+"
        ),
        "email address": re.compile(
            r"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@"
            r"[A-Z0-9.-]+\.[A-Z]{2,}"
        ),
        "Korean mobile number": re.compile(
            r"(?<!\d)01[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)"
        ),
        "bearer token": re.compile(
            r"(?i)\bauthorization\s*:\s*bearer\s+[A-Z0-9._~-]{8,}"
        ),
        "session cookie value": re.compile(
            r"(?i)\bJSESSIONID\s*=\s*[A-Z0-9._~-]{8,}"
        ),
    }
    # The secret scan covers the README as well, even though its evidence text
    # moved: a rewritten README is exactly the kind of document into which a
    # credential gets pasted as an "example".
    scanned = dict(documents)
    scanned["README"] = README.read_text(encoding="utf-8")
    for name, document in scanned.items():
        for pattern_name, pattern in forbidden_patterns.items():
            assert pattern.search(document) is None, f"{name}: {pattern_name}"

    record = " ".join(documents["record"].split())
    assert "R13 made one request" in record
    assert "surfaced as `KorailAppError` and was not retried" in record
    assert "R32 succeeded with 0 rows" in record
    assert "current-form R43 succeeded with 0 rows" in record
    assert "R45 succeeded with 15 rows" in record
    assert "existing safe train search succeeded with 10 rows" in record
    assert "R52 made zero requests" in record


def test_readme_documents_the_error_taxonomy():
    """The taxonomy is only useful if a caller can find out what to DO with it.

    The three questions the docs must answer out loud are which exception means
    retry is pointless, which means re-login, and which means the request was
    fine and there was simply nothing there.
    """
    readme = " ".join(README.read_text(encoding="utf-8").split())
    record = " ".join(RECORD.read_text(encoding="utf-8").split())

    assert "### 에러 분류" in README.read_text(encoding="utf-8")
    assert "앱 자신이 분기하는 필드인 `h_msg_cd` 로 분류한다" in readme
    assert "한국어 메시지 문구로는 분류하지 않는다" in readme

    # Every exception in the taxonomy is named, so none can be added to the
    # code without being explained here.
    for name in (
        "KorailNoResultsError",
        "KorailNoDirectTrainError",
        "KorailSoldOutError",
        "KorailSeatUnavailableError",
        "KorailReservationRefusedError",
        "KorailInvalidRequestError",
        "KorailNotEntitledError",
        "KorailServiceUnavailableError",
        "KorailAppUpdateRequiredError",
        "KorailSessionExpiredError",
        "KorailDynaPathError",
        "classify_app_error",
    ):
        assert f"`{name}`" in readme, name

    # Retry is pointless / re-login / nothing was there.
    assert "이 열차는 재시도해도 소용없다. 다른 열차를 골라라." in readme
    assert "재시도는 소용없다. 다른 질문을 하라." in readme
    assert "**다시 로그인하라.**" in readme
    assert "**아무것도 없었다.** 요청 자체는 정상이다." in readme
    assert "**이 라이브러리는 스스로 재시도하지 않는다.**" in readme
    assert "재시도한 예약은 중복 예약이기 때문이다" in readme

    # A warning on a success must be documented as staying a success. The rule
    # is in the README because a caller hits it; the observation that proved it
    # is in the record.
    assert "성공으로 남는다" in readme
    assert "WRR664296" in record
    assert "`strResult=SUCC`" in record
    assert "a real, cancelable PNR" in record

    # Third-party claims are labelled, not adopted.
    assert "zero hits in\nthe decompiled APK".replace("\n", " ") in record
    assert "Anti-macro rejection has no message code" in record
    assert "IRT010110" in record
    assert "is not encoded" in record

    # The one observation we deliberately refused to classify. The README says
    # that there is one and where to read it; the record says which.
    assert "일부러 분류하지 않고 남겨 둔 관측 하나" in readme
    assert "left unclassified" in record
    assert "[3]인증정보에 문제가 있습니다." in record
    assert "Its trigger is unconfirmed" in record


def test_progress_records_the_error_taxonomy():
    progress = " ".join(PROGRESS.read_text(encoding="utf-8").split())
    assert "classified on `h_msg_cd`" in progress
    assert "pure refinement" in progress
    assert "never introduces a failure the server did not declare" in progress
    assert "third-party-attested only" in progress


def test_docs_record_transfer_as_implemented_and_unverified():
    """The 환승 documentation contract.

    Three documents must agree on the same three things: that transfer is built
    and unproven, what the wire shape is, and what the operator has to do. Each
    claim below is one this package could get wrong silently, so each is pinned
    rather than left to prose drift.
    """
    readme = README.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    progress = PROGRESS.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")

    # Built, and not proven, plus the two entry points and the read that probes
    # a candidate route cheaply -- the half a USER has to know, so it stays in
    # the README as well as in the three evidence documents. The README says it
    # in Korean, so it is pinned separately rather than folded into a combined
    # string that CHANGELOG could satisfy on its behalf.
    for document in (record, progress, changelog):
        assert "NOT live-verified" in document
        assert "search_transfer_trains" in document
        assert "reserve_transfer" in document
    assert "실서버 검증 안 됨" in readme
    assert "search_transfer_trains" in readme
    assert "reserve_transfer" in readme
    assert "get_transfer_stations" in readme
    # And the warning that a live transfer hold cannot be released from here.
    assert "KORAIL 앱에서 취소할 준비가 되어 있지 않으면 보내지 마라" in readme

    for document in (record, progress, changelog):
        # The two codes a reader would otherwise guess wrongly.
        assert "`14`" in document or '`"14"`' in document
        assert "001" in document and "002" in document
        # Two legs, and why it is the app's ceiling rather than ours.
        assert "OSeat.java:32-35" in document
        assert "OSrcar.java:21-30" in document
        # The one field the transfer search moves.
        assert "DirectInquiryActivity.java:284-296" in document
        # 예약대기 does not compose, with both of the app's gates named.
        assert "a5/k.java:120-127" in document
        assert "DirectInquiryActivity.java:434" in document
        # The cancel gap, in every document, because it blocks the round trip.
        assert "DReservationConfirmActivity.java:269-278" in document

    # jadx mangles the two ternaries, so the bytecode citation must survive.
    for document in (record, changelog):
        assert "smali/C5/a.smali:306-338" in document
        assert "smali/K4/e.smali:68" in document

    # The response shape, stated as the app's own pairing rather than invented.
    assert "a5/k.java:156-170" in record
    assert "paired\n**positionally**" in record or "paired positionally" in record
    assert "h_chg_trn_seq" in record

    # What the operator needs, including where the candidate pairs come from and
    # that they are inferred rather than verified here.
    assert "arrays.xml:200-208" in record
    assert "ktx_map" in record
    assert "강릉 → 여수엑스포" in record
    assert "not** verified against a timetable" in record
    assert "get_transfer_stations" in record
    # WRD000061 is the code the fallback keys on, so a caller meets it: it is
    # in the README's error table and in the record's evidence.
    assert "WRD000061" in readme
    assert "WRD000061" in record


def test_the_prose_inventory_agrees_with_the_service_table_it_summarises():
    """One inventory, measured -- not two literals frozen in opposite places.

    Two counts used to coexist: the per-service table in
    api-status-by-service.md summed to 32/13/120, while a sentence repeated
    across six documents said 32/10/123. Both were pinned, so CI enforced a
    contradiction and neither number could drift into agreement with the
    other. api-status-by-service.md contained BOTH, four lines apart.

    The table is the measurement and it is newer (490ae78, 2026-07-26, which
    moved three entries out of 미실행 when they were tried and failed); the
    sentence dates from 053ce30 on 2026-07-15 and was never updated. So the
    sentence is now derived from the table instead of asserted beside it, and
    a future revalidation that edits one has to edit the other.

    Dated archival entries are exempt on purpose: a CHANGELOG bullet and a
    closed increment record state what was true when they were written, and
    rewriting those would falsify the record rather than correct it.
    """
    status = STATUS.read_text(encoding="utf-8")
    rows = re.findall(
        r"^\| `[^`]+` \| [^|]+ \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|$",
        status,
        flags=re.MULTILINE,
    )
    total, success, failed, unexecuted = (
        sum(int(row[index]) for row in rows) for index in range(4)
    )
    sentence = (
        f"{success} successful, {failed} failed, and {unexecuted} unexecuted"
    )

    current_state_documents = {
        "status": status,
        "guide": BUILD_GUIDE.read_text(encoding="utf-8"),
        "record": RECORD.read_text(encoding="utf-8"),
        "progress": PROGRESS.read_text(encoding="utf-8"),
    }
    for name, document in current_state_documents.items():
        normalized = " ".join(document.split())
        assert sentence in normalized, f"{name} disagrees with the table"
        assert f"out of {total}" in normalized, name


def test_every_document_that_lists_the_mutation_methods_lists_all_of_them():
    """Measured against the client, not transcribed beside it.

    Four documents enumerate the consent-gated methods, and on 2026-07-27 all
    four were wrong in the same way: e8fa0e3 and 22ba4cc updated the COUNT in
    each paragraph and left the NAMES alone, so three documents still listed
    `verify_offline_refund_ticket`, `execute_offline_refund`, `begin_non_member`
    and `end_non_member` -- names that raise AttributeError -- while none of
    them listed `add_to_cart`, which had just shipped. README said "Thirteen"
    and "the other twelve" two lines apart.

    Counting is what the previous pins did and it is what let the names rot,
    so this asserts the names themselves, derived from the class.
    """
    gated = {
        name
        for name, member in inspect.getmembers(KorailClient, inspect.isfunction)
        if not name.startswith("_")
        and "require_mutation_consent" in inspect.getsource(member)
    }
    retired = {
        "verify_offline_refund_ticket",
        "execute_offline_refund",
        "begin_non_member",
        "end_non_member",
    }

    for name, path in (
        ("README", README),
        ("record", RECORD),
        ("status", STATUS),
        ("progress", PROGRESS),
        # SECURITY.md makes the strongest version of this claim -- it says
        # everything NOT listed "is not callable" -- so a name missing from it
        # is a security promise that is false, not a stale doc. It named
        # twelve methods and six categories for as long as it was
        # hand-maintained, while add_to_cart and the cart category shipped.
        ("SECURITY", SECURITY),
    ):
        document = path.read_text(encoding="utf-8")
        for method in gated:
            # Either spelling: `name` or `name(args)`. README uses the second.
            assert re.search(rf"`{method}[`(]", document), f"{name} omits {method}"
        for method in retired:
            assert not re.search(
                rf"`{method}[`(]", document
            ), f"{name} still names {method}"


def test_the_route_decomposition_is_measured_not_asserted():
    """"60 routes = 58 reads + the login POST + the logout GET", derived.

    README states the breakdown and nothing checked it, so every read added
    since would have silently made the sentence wrong while the total beside
    it stayed pinned and green. The two auth routes are identified by their
    exact (method, path) pairs rather than by a substring, because
    `login.Logout` contains `login` and a careless filter counts it twice.

    The README is Korean, so the derivation carries the Korean unit with it.
    The read figure used to be pinned as a bare `f"{reads}"`, which any stray
    pair of digits anywhere in the document satisfied; it now has to appear as
    a counted noun.
    """
    from korail_mobile_api import safety

    routes = set(safety.KORAIL_READ_ONLY_ROUTES)
    auth = {
        ("POST", "/classes/com.korail.mobile.login.Login"),
        ("GET", "/classes/com.korail.mobile.login.Logout"),
    }

    assert auth <= routes, "the login/logout pair is not on the allowlist"
    reads = len(routes) - len(auth)

    gated = {
        name
        for name, member in inspect.getmembers(KorailClient, inspect.isfunction)
        if not name.startswith("_")
        and "require_mutation_consent" in inspect.getsource(member)
    }
    public = {
        name
        for name, _ in inspect.getmembers(KorailClient, inspect.isfunction)
        if not name.startswith("_")
    }

    readme = README.read_text(encoding="utf-8")
    normalized = " ".join(readme.split())
    assert f"라우트 {len(routes)}개" in normalized
    assert f"읽기 {reads}개" in normalized, f"README does not state {reads} reads"
    assert f"경계에는 라우트 {len(routes)}개" in normalized
    # The mutation split is the other half of the same sentence, and it drifted
    # once already: the safety model said "fifteen mutation methods" while the
    # capability section two screens above said thirteen.
    assert f"변경 메서드 {len(gated)}개" in normalized
    assert f"나머지 {len(public) - len(gated)}개" in normalized

    # The three remaining counts the README states. Each is one the reader uses
    # to decide something -- how much of the surface can spend money, how much
    # of it carries the anti-automation token, how many people fit on one PNR --
    # so none of them may be a number somebody typed once.
    from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS
    from korail_mobile_api.redaction import (
        KORAIL_MAX_PASSENGERS_PER_RESERVATION,
    )

    assert f"변경 라우트 {len(safety.KORAIL_MUTATION_ROUTES)}개" in normalized
    assert f"{len(DYNAPATH_ALLOWLIST_PATHS)}개 경로" in normalized
    assert f"합계 {KORAIL_MAX_PASSENGERS_PER_RESERVATION}명까지" in normalized
