# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대기열 응답이 지목한 노드(``ip``/``port``)를 제한하는 가드. 서버가 정하는 값이라 풀 밖 호스트로 대기열 키를 보내지 않도록 검사합니다."""
import re
from urllib.parse import urlsplit

from .constants import KORAIL_NETFUNNEL_URL
from .errors import KorailProtocolError


KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname

#: 응답이 가리킬 수 있는 대기열 노드 이름. SDK 는 기본 host_notmodify=true 로 응답 노드를 따르지 않습니다 (com/netfunnel/api/Response.java:143-146,
#: CommandClient.java:33-38, com/netfunnel/api/Property.java:23). 앱의 기동 설정(KorailTalkApplication.java:361-389)이 이 값을 바꾸는지는 보호된
#: setter 때문에 확인되지 않습니다. 이 라이브러리는
#: 일부러 노드를 따르되 rnf<1-99>.letskorail.com(소문자)의 HTTPS/443 으로 제한합니다. 2026-07-26 라이브 관측: 정문 완료(5004)는 약 절반이
#: 503/Wrong Server ID, 지정 노드(rnf12/rnf13/rnf14) 완료는 수용됐습니다.
KORAIL_NETFUNNEL_NODE_HOST_RE = re.compile(r"rnf[1-9][0-9]?\.letskorail\.com")

#: 지목된 노드에 허용되는 유일한 포트.
KORAIL_NETFUNNEL_NODE_PORT = 443


def korail_netfunnel_node_url(ip: str, port: str) -> str:
    """노드가 없으면 빈 문자열, 유효하면 HTTPS origin. 불완전하거나 허용 범위 밖인 노드는 거절합니다.

    SDK 의 노드 미지정 시 정문 유지 조건: CommandClient.java:34-37. 잘못된 노드를 정문으로 조용히 바꾸지 않아 완료 요청의 실패를 숨기지 않습니다.
    """
    if not ip and not port:
        return ""
    if (
        ip != KORAIL_NETFUNNEL_HTTPS_HOST
        and KORAIL_NETFUNNEL_NODE_HOST_RE.fullmatch(ip) is None
    ):
        raise KorailProtocolError(
            f"KORAIL NetFunnel reply named {ip!r} as its node; only "
            "rnf<1-99>.letskorail.com (lowercase) or the front door "
            f"{KORAIL_NETFUNNEL_HTTPS_HOST!r} are followed"
        )
    if port != str(KORAIL_NETFUNNEL_NODE_PORT):
        raise KorailProtocolError(
            f"KORAIL NetFunnel reply named port {port!r} for node {ip!r}; "
            f"only {KORAIL_NETFUNNEL_NODE_PORT} is followed"
        )
    return f"https://{ip}"

