from pathlib import Path


README = Path(__file__).parents[1] / "README.md"


def test_readme_describes_live_scope_and_probe_provider_consistently():
    text = README.read_text(encoding="utf-8")
    assert "This work is static analysis only." not in text
    assert "The committed material is documentation" not in text
    assert "The live smoke path uses the probe-compatible" not in text
    assert "caller-supplied" in text
    assert "compatibility-only" in text
    assert "KORAIL_DYNAPATH_DEVICE_ID" in text
    assert "KORAIL_ADVERTISING_ID" in text
    assert "get_app_data()" in text
    assert "get_notice()" in text
    assert "/file/CACHE/prdMobilePlusMain.cache" in text
    assert "/file/CACHE/prdMobilePlusNotice.cache" in text
    assert "appDataLoaded" in text
    assert "noticeLoaded" in text
