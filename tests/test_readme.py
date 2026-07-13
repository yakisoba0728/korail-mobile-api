from pathlib import Path


README = Path(__file__).parents[1] / "README.md"


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
    assert "get_app_data()" in text
    assert "get_notice()" in text
    assert "/file/CACHE/prdMobilePlusMain.cache" in text
    assert "/file/CACHE/prdMobilePlusNotice.cache" in text
    assert "appDataLoaded" in text
    assert "noticeLoaded" in text
