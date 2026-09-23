# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대기열 응답이 지목한 노드(``ip``/``port``)를 따라갈지 정하는 가드.

서버 응답이 정하는 값이라 검사합니다 — 풀 밖 호스트로 대기열 키를 보내지 않습니다.
"""
import re
from urllib.parse import urlsplit

from .constants import KORAIL_NETFUNNEL_URL
from .errors import KorailProtocolError


KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname

#: 응답이 가리킬 수 있는 대기열 노드 이름.
#:
#: 7.0.6 SDK 는 응답의 ``ip``/``port`` 를 읽기는 하지만(``com/netfunnel/api/
#: Response.java:143-146``) 따라가지 않습니다 — ``CommandClient.makeURL``
#: (``CommandClient.java:33-38``)이 ``!property.isHostNotmodify()`` 일 때만 노드로
#: URL 을 다시 만드는데 기본값이 ``true``(``Property.java:23``)이고 KORAIL 의
#: ``KorailTalkApplication.setNetFunnel()``(``:361-389``)은 그 값을 바꾸지 않습니다.
#: 이 라이브러리는 **일부러** 따라갑니다: 2026-07-26 실서버에서 정문으로 보낸
#: 완료(5004)는 약 절반이 ``503:msg="Wrong Server ID"`` 였고 응답이 지목한 노드
#: (``rnf12``/``rnf13``/``rnf14.letskorail.com``, https/443)로 보내면 받아졌습니다.
#: 따라가되 풀 자신의 이름(``rnf<1-99>.letskorail.com``, 소문자)과 443 으로만
#: 제한합니다.
KORAIL_NETFUNNEL_NODE_HOST_RE = re.compile(r"rnf[1-9][0-9]?\.letskorail\.com")

#: 지목된 노드에 허용되는 유일한 포트.
KORAIL_NETFUNNEL_NODE_PORT = 443


def korail_netfunnel_node_url(ip: str, port: str) -> str:
    """응답의 ``ip``/``port`` 를 노드 origin(``https://<host>``)으로 바꿉니다.

    응답이 노드를 가리키지 않았으면(둘 다 없음) ``""`` 입니다 — 7.0.6
    ``CommandClient.makeURL`` 이 ``response.getHost().length() > 0 &&
    response.getPort() > 0`` 이 아닐 때 정문에 머무는 것(``CommandClient.java:34,37``)
    과 같습니다. 한쪽만 오거나, 풀 밖 호스트이거나, 443 이 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 잘못된 재지정을
    정문으로 조용히 되돌리면 샌 슬롯이 되므로 일부러 시끄럽게 실패합니다.
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

