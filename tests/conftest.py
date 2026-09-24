"""Shared release fixtures; f8_ names do not collide with domain-session fixtures."""
from __future__ import annotations

import os
import socket
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig, KorailSession

# Also installed as sitecustomize in child processes used for packaging checks.
_F8_SOCKET_GUARD = '''\
import socket

def _f8_denied(*args, **kwargs):
    raise AssertionError("f8: network access is forbidden; use httpx.MockTransport")

for _name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex",
              "gethostbyaddr"):
    setattr(socket, _name, _f8_denied)
for _name in ("connect", "connect_ex", "sendto", "sendmsg"):
    if hasattr(socket.socket, _name):
        setattr(socket.socket, _name, _f8_denied)
'''


@pytest.fixture(autouse=True)
def f8_block_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block TCP, DNS and unconnected UDP for every test, including other sessions."""
    def denied(*args: object, **kwargs: object) -> None:
        raise AssertionError("f8: network access is forbidden; use httpx.MockTransport")

    for name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex",
                 "gethostbyaddr"):
        monkeypatch.setattr(socket, name, denied)
    for name in ("connect", "connect_ex", "sendto", "sendmsg"):
        if hasattr(socket.socket, name):
            monkeypatch.setattr(socket.socket, name, denied)


@pytest.fixture
def f8_logged_in_session() -> KorailSession:
    """Purely synthetic session, not a login and not a real member identifier."""
    return KorailSession(
        jsessionid="SYNTHETIC-SESSION",
        member_no="SYNTHETIC-MEMBER",
        member_card_no="SYNTHETIC-MEMBER-CARD",
        customer_no="SYNTHETIC-CUSTOMER",
        raw={"source": "f8-synthetic"},
    )


@pytest.fixture
def f8_client_factory(
    f8_logged_in_session: KorailSession,
) -> Iterator[Callable[..., KorailClient]]:
    """Use the real HTTP, queue, payload and parser code with a scripted transport."""
    clients: list[KorailClient] = []

    def make(
        handler: Callable[[httpx.Request], httpx.Response],
        *,
        logged_in: bool = True,
        config: KorailConfig | None = None,
    ) -> KorailClient:
        client = KorailClient(
            config or KorailConfig(
                base_url="https://api.example.invalid",
                netfunnel_url="https://queue.example.invalid",
                key="SYNTHETIC-APP-KEY",
            ),
            transport=httpx.MockTransport(handler),
        )
        clients.append(client)
        if logged_in:
            client.session.current = f8_logged_in_session
            client.http.cookies.set("JSESSIONID", f8_logged_in_session.jsessionid)
        return client

    yield make
    for client in reversed(clients):
        client.close()


@pytest.fixture
def f8_subprocess_env(tmp_path: Path) -> dict[str, str]:
    """No package-index access or network escape through packaging subprocesses."""
    guard = tmp_path / "f8-network-guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(_F8_SOCKET_GUARD, encoding="utf-8")
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": str(guard),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_NO_INDEX": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    })
    return env
