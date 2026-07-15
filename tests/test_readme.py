from pathlib import Path


README = Path(__file__).parents[1] / "README.md"
STATUS = Path(__file__).parents[1] / "docs" / "api-status-by-service.md"
BUILD_GUIDE = Path(__file__).parents[1] / "docs" / "library-build-guide.md"
PROGRESS = Path(__file__).parents[1] / "docs" / "IMPLEMENTATION_PROGRESS.md"


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
    assert "| 성공 | 27 |" in status
    assert "| 실패 | 8 |" in status
    assert "| 미실행 | 130 |" in status
    assert "Package coverage: 27 exact login/read routes" in status
    assert "bounded live structural evidence" in status

    guide = BUILD_GUIDE.read_text(encoding="utf-8")
    assert "성공 27 / 실패 8 / 미실행 130" in guide
    assert "성공 25 / 실패 8 / 미실행 132" not in guide

    progress = PROGRESS.read_text(encoding="utf-8")
    assert "27 exact login/read routes" in progress
    assert "30 public methods" in progress
    assert "75" in progress
    assert "IRG000000" in progress


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
        assert "raw-backed typed response core" in text
        assert "StationInfoResponse" in text
        assert "TrainCalendarResponse" in text
        assert "TrainScheduleResponse" in text
        assert "TransferStationListResponse" in text
        assert "TrainSearchMetadata" in text
        assert "request payload semantics remain unchanged" in text
        assert "appended, defaulted fields" in text
        assert "raw mappings remain `repr=False`" in text
    for key in (
        "h_std_rest_seat_cnt",
        "h_fst_rest_seat_cnt",
        "h_free_sracar_cnt",
        "h_rsv_wait_ps_cnt",
    ):
        assert key in readme
