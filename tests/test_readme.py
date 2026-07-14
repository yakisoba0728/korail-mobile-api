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
    assert "25 exact login/read routes" in text
    assert "No live replay was performed for this expansion." in text
    assert "No new DynaPath route" in text
    assert "WRG000000" in text
    assert "P100" in text
    assert "typed empty" in text
    assert "caller-owned identifiers" in text
    assert "reservation, payment, and mutation routes remain excluded" in text
    assert "reservation_no=reservation_no" in text
    assert "reservation_sequence=reservation_sequence" in text


def test_status_and_progress_documents_match_current_inventory_and_coverage():
    status = STATUS.read_text(encoding="utf-8")
    assert "| 성공 | 25 |" in status
    assert "| 실패 | 8 |" in status
    assert "| 미실행 | 132 |" in status
    assert "Package coverage: 25 exact login/read routes" in status
    assert "No live replay was performed for this expansion." in status

    guide = BUILD_GUIDE.read_text(encoding="utf-8")
    assert "성공 25 / 실패 8 / 미실행 132" in guide
    assert "성공 24 / 실패 8 / 미실행 133" not in guide

    progress = PROGRESS.read_text(encoding="utf-8")
    assert "25 exact login/read routes" in progress
    assert "28 public methods" in progress
    assert "No live replay was performed for this expansion." in progress
