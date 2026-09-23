# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대기열 호스트(``nf.letskorail.com``)로 나가는 곳을 제한하는 가드.

검사하는 것은 이 라이브러리가 스스로 정하지 않는 값뿐입니다 — 호출자가 넘긴 정문
origin(:attr:`~korail_mobile_api.config.KorailConfig.netfunnel_url`), 서버가 응답에
실어 보낸 노드(``ip``/``port``)와 키. 이 라이브러리가 고정 순서로 만드는 질의 문자열
자체는 검사하지 않습니다.

메인 API 쪽 가드는 :func:`~korail_mobile_api.http.assert_korail_origin` 입니다.
"""
import re
from urllib.parse import urlsplit

from .constants import KORAIL_NETFUNNEL_URL
from .errors import KorailProtocolError


KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname

#: 서버가 발급한 키의 모양. 키는 불투명한 값이라 모양으로만 봅니다.
#: 실서버 키는 대문자 16진 256자였습니다(2026-07-26). 상한 512 는 여유를 둔 값입니다 —
#: 너무 좁게 잡으면 정상 키의 완료(5004)가 전송 전에 막혀 슬롯이 조용히 샙니다.
KORAIL_NETFUNNEL_KEY_RE = re.compile(r"[A-Za-z0-9_.:@~-]{1,512}")

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


def assert_korail_netfunnel_origin(netfunnel_url: str) -> None:
    """설정된 대기열 정문을 ``https://nf.letskorail.com``(443)으로 고정합니다.

    https 가 아니거나, 호스트가 다르거나, 443 이 아닌 포트·userinfo·path·query·fragment
    가 붙어 있으면 :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.
    """
    parsed = urlsplit(netfunnel_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise KorailProtocolError(
            "KORAIL NetFunnel request origin is not allowed"
        ) from exc
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != KORAIL_NETFUNNEL_HTTPS_HOST
        or port not in {None, KORAIL_NETFUNNEL_NODE_PORT}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise KorailProtocolError(
            "KORAIL NetFunnel request origin is not allowed"
        )


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


def assert_korail_netfunnel_key(key: str) -> None:
    """서버가 준 키가 :data:`KORAIL_NETFUNNEL_KEY_RE` 모양인지 봅니다."""
    if KORAIL_NETFUNNEL_KEY_RE.fullmatch(key) is None:
        raise KorailProtocolError("KORAIL NetFunnel reply carried a malformed key")
