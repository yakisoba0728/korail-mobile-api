# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""서버가 준 노드라도 허용 범위 밖이면 신뢰하지 않고 정문을 사용합니다."""

import logging
import re
from urllib.parse import urlsplit

from .constants import KORAIL_NETFUNNEL_URL

_log = logging.getLogger(__name__)

KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname

#: SDK 기본값 host_notmodify=true는 응답 노드 이동을 막습니다 (com/netfunnel/api/Response.java:143-146;
#: CommandClient.java:33-38; com/netfunnel/api/Property.java:23). 앱 기동 시 변경 여부는 보호된 setter 때문에
#: 미확인입니다(KorailTalkApplication.java:361-389).
KORAIL_NETFUNNEL_NODE_HOST_RE = re.compile(r"rnf[1-9][0-9]?\.letskorail\.com")

KORAIL_NETFUNNEL_NODE_PORT = 443


def korail_netfunnel_node_url(ip: str, port: str) -> str:
    """노드가 없거나 허용 범위 밖이면 빈 문자열이며, 호출자는 정문을 씁니다. SDK 기본값은 노드를 따르지 않습니다(com/netfunnel/api/Property.java:23)."""
    if not ip and not port:
        return ""
    host_allowed = ip == KORAIL_NETFUNNEL_HTTPS_HOST or KORAIL_NETFUNNEL_NODE_HOST_RE.fullmatch(ip) is not None
    if not host_allowed or port != str(KORAIL_NETFUNNEL_NODE_PORT):
        _log.warning(
            "KORAIL NetFunnel reply named node %r port %r; only rnf<1-99>.letskorail.com (lowercase) or the "
            "front door on %d are followed, so the front door is used",
            ip,
            port,
            KORAIL_NETFUNNEL_NODE_PORT,
        )
        return ""
    return f"https://{ip}"
