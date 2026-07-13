import os

import pytest

from korail_mobile_api.live import live_enabled, run_live_smoke_from_env


pytestmark = pytest.mark.live


def test_read_only_live_smoke():
    if not live_enabled():
        pytest.skip("KORAIL live smoke requires explicit opt-in")
    result = run_live_smoke_from_env()
    assert result["appDataLoaded"] is True
    assert result["noticeLoaded"] is True
    assert result["loggedIn"] is True
    assert result["stationDataCount"] > 0
    assert result["trainCount"] >= 0
    assert "raw" not in result
    assert result["uuidLoaded"] is True
    if os.environ.get("KORAIL_MAAS_SERVICE_CODE"):
        assert result["maasStationTested"] is True
        assert result["maasStationCount"] >= 0
    else:
        assert result["maasStationTested"] is False
        assert result["maasStationCount"] == 0
