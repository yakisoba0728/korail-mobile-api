# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대기열 응답의 노드 주소를 검사합니다. 대기열 키가 허용 범위 밖 호스트로 전송되지 않도록 ip·port를 제한합니다."""
import re
from urllib.parse import urlsplit

from .constants import KORAIL_NETFUNNEL_URL
from .errors import KorailProtocolError


KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname

#: SDK 기본값 host_notmodify=true는 응답 노드 이동을 막습니다 (com/netfunnel/api/Response.java:143-146;
#: CommandClient.java:33-38; com/netfunnel/api/Property.java:23). 앱 기동 시 변경 여부는 보호된 setter 때문에
#: 미확인입니다(KorailTalkApplication.java:361-389). 이 라이브러리는 정문 nf.letskorail.com 또는 소문자 rnf<1-99>.letskorail.com의
#: HTTPS/443을 허용합니다. 2026-07-26: 정문 5004는 약 절반이 503/Wrong Server ID였고 rnf12/rnf13/rnf14 완료는 수용됐습니다.
KORAIL_NETFUNNEL_NODE_HOST_RE = re.compile(r"rnf[1-9][0-9]?\.letskorail\.com")

KORAIL_NETFUNNEL_NODE_PORT = 443


def korail_netfunnel_node_url(ip: str, port: str) -> str:
    """허용된 대기열 노드의 HTTPS 원점 주소를 반환하며, 노드가 없으면 빈 문자열을 반환합니다."""
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

