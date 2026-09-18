# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

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
    assert result["depositBankCount"] >= 0
    assert result["tripMenuCount"] >= 0
    assert result["stationDataCount"] > 0
    assert result["trainCount"] >= 0
    assert "raw" not in result
    assert result["uuidLoaded"] is True
    assert result["maasMenuCount"] > 0
    if result["maasStationTested"]:
        assert result["maasStationCount"] > 0
    else:
        assert result["maasStationCount"] == 0
