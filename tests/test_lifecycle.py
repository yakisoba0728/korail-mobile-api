"""Cleanup must preserve the first failure while attempting both connection pools."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from conftest import synthetic_config
from test_auth_transport import COMMON, COOKIE, ID, LOGIN, PASSWORD, SERVICE, bootstrap, envelope

from korail_mobile_api import (
    DynapathConfig,
    Korail,
    KorailAuthError,
    KorailClient,
    KorailConfig,
    KorailInvalidInputError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
)


def _rig(
    monkeypatch: pytest.MonkeyPatch,
    errors: tuple[BaseException | None, BaseException | None],
) -> tuple[Korail, list[str]]:
    korail = Korail(transport=httpx.MockTransport(lambda request: pytest.fail("unexpected request")))
    calls: list[str] = []
    assert korail.client.netfunnel is not None

    def closer(close: Callable[[], None], name: str, error: BaseException | None) -> Callable[[], None]:
        def run() -> None:
            calls.append(name)
            close()
            if error is not None:
                raise error

        return run

    for pool, name, error in zip(
        (korail.client.http, korail.client.netfunnel), ("HTTP", "queue"), errors, strict=True
    ):
        monkeypatch.setattr(pool, "close", closer(pool.close, name, error))
    return korail, calls


@pytest.mark.parametrize("stage", ["login", "initialization", "context"])
@pytest.mark.parametrize("error_type", [KorailAuthError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_failed_operation_keeps_original_error(
    monkeypatch: pytest.MonkeyPatch, stage: str, error_type: type[BaseException], cleanup_fails: bool
) -> None:
    original = error_type("synthetic original failure")
    errors = (RuntimeError("HTTP cleanup"), RuntimeError("queue cleanup")) if cleanup_fails else (None, None)
    korail, calls = _rig(monkeypatch, errors)

    def fail(*args: object, **kwargs: object) -> None:
        raise original

    if stage == "login":
        monkeypatch.setattr(
            Korail, "__init__", lambda self, *args, **kwargs: self.__dict__.update(korail.__dict__)
        )
        monkeypatch.setattr(Korail, "login", fail)
    elif stage == "initialization":
        monkeypatch.setattr(
            "korail_mobile_api.client.KorailHttpClient", lambda *args, **kwargs: korail.client.http
        )
        monkeypatch.setattr("korail_mobile_api.client.KorailNetFunnelClient", fail)

    with pytest.raises(error_type) as caught:
        if stage == "login":
            Korail.logged_in("SYNTHETIC-MEMBER", "SYNTHETIC-PASSWORD")
        elif stage == "initialization":
            KorailClient(KorailConfig())
        else:
            with korail:
                raise original
    assert caught.value is original
    assert calls == (["HTTP"] if stage == "initialization" else ["HTTP", "queue"])
    assert korail.client.http._client.is_closed
    if cleanup_fails:
        notes = " ".join(original.__notes__)
        assert "HTTP cleanup" in notes
        if stage != "initialization":
            assert "queue cleanup" in notes
    # Initialization never owns the pre-existing queue used by this synthetic rig.
    if stage == "initialization":
        korail.client.netfunnel._client.close()


@pytest.mark.parametrize("context", [False, True])
@pytest.mark.parametrize("failures", [(False, False), (True, False), (False, True), (True, True)])
def test_close_attempts_both_pools_and_reports_first_failure(
    monkeypatch: pytest.MonkeyPatch, context: bool, failures: tuple[bool, bool]
) -> None:
    errors = tuple(
        RuntimeError(f"{name} cleanup") if failed else None
        for name, failed in zip(("HTTP", "queue"), failures, strict=True)
    )
    korail, calls = _rig(monkeypatch, errors)
    first = next((error for error in errors if error is not None), None)

    def close() -> None:
        if context:
            with korail:
                pass
        else:
            korail.close()

    if first is None:
        close()
    else:
        with pytest.raises(RuntimeError) as caught:
            close()
        assert caught.value is first
        if all(failures):
            assert "queue cleanup" in " ".join(first.__notes__)
    assert calls == ["HTTP", "queue"]
    assert korail.client.http._client.is_closed and korail.client.netfunnel._client.is_closed


def test_failed_cleanup_diagnostics_cannot_replace_original_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BadDiagnosticError(Exception):
        def __repr__(self) -> str:
            raise RuntimeError("synthetic repr failure")

    original = KorailAuthError("synthetic body failure")
    korail, calls = _rig(monkeypatch, (BadDiagnosticError(), None))
    with pytest.raises(KorailAuthError) as caught:
        with korail:
            raise original
    assert caught.value is original and calls == ["HTTP", "queue"]


@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_client_context_manager_closes_and_keeps_the_block_error(
    monkeypatch: pytest.MonkeyPatch, cleanup_fails: bool
) -> None:
    errors = (RuntimeError("HTTP cleanup"), None) if cleanup_fails else (None, None)
    korail, calls = _rig(monkeypatch, errors)
    original = KorailAuthError("synthetic body failure")
    with pytest.raises(KorailAuthError) as caught:
        with korail.client as client:
            assert client is korail.client
            raise original
    assert caught.value is original and calls == ["HTTP", "queue"]
    assert ("HTTP cleanup" in " ".join(getattr(original, "__notes__", []))) is cleanup_fails
    assert korail.client.http._client.is_closed and korail.client.netfunnel._client.is_closed


def test_client_context_manager_raises_the_first_cleanup_error(monkeypatch: pytest.MonkeyPatch) -> None:
    errors = (RuntimeError("HTTP cleanup"), RuntimeError("queue cleanup"))
    korail, calls = _rig(monkeypatch, errors)
    with pytest.raises(RuntimeError) as caught:
        with korail.client:
            pass
    assert caught.value is errors[0] and calls == ["HTTP", "queue"]
    assert "queue cleanup" in " ".join(errors[0].__notes__)


@pytest.mark.parametrize("stage", ["crypto", "login", "provider"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, RuntimeError])
def test_interrupted_login_clears_bootstrap_cookies(scripted_client_factory, stage, error_type):
    original = error_type("synthetic interruption")
    first, crypto = bootstrap()
    first = httpx.Response(200, json=first, headers={"Set-Cookie": "BOOTSTRAP=synthetic; Path=/"})
    replies = [first, original] if stage == "crypto" else [first, crypto]

    def provider(context):
        if stage == "provider":
            raise original
        return "synthetic-token"

    if stage == "login":
        replies.append(original)
    replies.append(envelope())
    client, requests, pending = scripted_client_factory(
        replies, config=synthetic_config(dynapath=DynapathConfig(enabled=True, token_provider=provider))
    )
    # Ordinary provider exceptions are wrapped by HTTP; process interruptions are not.
    if stage == "provider" and error_type is RuntimeError:
        expected = KorailProtocolError
    else:
        expected = error_type
    with pytest.raises(expected) as caught:
        client.login(ID, PASSWORD)
    assert (caught.value.__cause__ if expected is not error_type else caught.value) is original
    assert client.session.current is None and client.session.pending is None
    assert not client.http.cookies
    assert [request.url.path for request in requests] == (
        [SERVICE, COMMON] if stage != "login" else [SERVICE, COMMON, LOGIN]
    )
    client.get_service_status()
    assert "cookie" not in requests[-1].headers and not pending


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_login_interruption_survives_cookie_cleanup_failure(scripted_client_factory, monkeypatch, error_type):
    original = error_type("synthetic interruption")
    client, requests, _ = scripted_client_factory([bootstrap()[0], original])
    clear = client.http.cookies.clear
    clears = 0

    def fail_second_clear():
        nonlocal clears
        clears += 1
        if clears == 1:
            clear()
        else:
            raise RuntimeError("synthetic cookie cleanup")

    monkeypatch.setattr(client.http.cookies, "clear", fail_second_clear)
    with pytest.raises(error_type) as caught:
        client.login(ID, PASSWORD)
    assert caught.value is original and len(requests) == 2 and clears == 2
    assert client.session.current is None and client.session.pending is None
    assert "synthetic cookie cleanup" in " ".join(original.__notes__)


@pytest.mark.parametrize("stage", ["login", "logout", "expired-read"])
@pytest.mark.parametrize("bad_diagnostic", [False, True])
def test_session_cleanup_preserves_original_error(
    scripted_client_factory, f8_logged_in_session, monkeypatch, stage, bad_diagnostic
):
    class BadDiagnosticError(RuntimeError):
        def __repr__(self):
            raise RuntimeError("synthetic repr failure")

    transport_error = httpx.ReadError("synthetic read failure")
    failure = envelope("P058", "FAIL") if stage == "expired-read" else transport_error
    replies = [bootstrap()[0], failure] if stage == "login" else [failure]
    client, requests, pending = scripted_client_factory(replies, session=f8_logged_in_session)
    client.http.cookies.set("JSESSIONID", COOKIE)
    cleanup_error = BadDiagnosticError() if bad_diagnostic else RuntimeError("synthetic cookie cleanup")
    clear, post = client.http.cookies.clear, client.http.post_form
    originals = []
    clears = 0

    def fail_clear():
        nonlocal clears
        clears += 1
        if stage == "login" and clears == 1:
            clear()
        else:
            raise cleanup_error

    def observe_error(*args, **kwargs):
        try:
            return post(*args, **kwargs)
        except BaseException as error:
            originals.append((error, error.raw, error.request_sent, error.__cause__))
            raise

    monkeypatch.setattr(client.http.cookies, "clear", fail_clear)
    monkeypatch.setattr(client.http, "post_form", observe_error)
    expected = KorailSessionExpiredError if stage == "expired-read" else KorailTransportError
    with pytest.raises(expected) as caught:
        if stage == "login":
            client.login(ID, PASSWORD)
        elif stage == "logout":
            client.logout()
        else:
            client.list_tickets()
    error = caught.value
    ((original, raw, sent, cause),) = originals
    assert error is original and error.raw is raw and error.request_sent is sent and error.__cause__ is cause
    assert client.session.current is None and client.session.pending is None
    assert not pending and len(requests) == (2 if stage == "login" else 1)
    if stage == "expired-read":
        assert error.raw == failure and error.request_sent is None
    else:
        assert error.__cause__ is transport_error and error.raw is None and error.request_sent is True
    if not bad_diagnostic:
        assert "synthetic cookie cleanup" in " ".join(error.__notes__)


@pytest.mark.parametrize("operation", ["clear_session", "logout"])
def test_session_cleanup_without_primary_still_raises(
    scripted_client_factory, f8_logged_in_session, monkeypatch, operation
):
    client, requests, _ = scripted_client_factory([envelope()], session=f8_logged_in_session)
    original = RuntimeError("synthetic cookie cleanup")

    def fail_clear():
        raise original

    monkeypatch.setattr(client.http.cookies, "clear", fail_clear)
    with pytest.raises(RuntimeError) as caught:
        getattr(client, operation)()
    assert caught.value is original
    assert client.session.current is None and client.session.pending is None
    assert len(requests) == (1 if operation == "logout" else 0)


@pytest.mark.parametrize("input_flag", [None, "synthetic-flag"])
def test_unencodable_login_id_is_rejected_before_bootstrap(scripted_client_factory, input_flag):
    client, requests, _ = scripted_client_factory(bootstrap())
    with pytest.raises(KorailInvalidInputError) as caught:
        client.login("synthetic\ud800@example.invalid", PASSWORD, input_flag=input_flag)
    assert isinstance(caught.value.__cause__, UnicodeEncodeError)
    assert caught.value.request_sent is None
    assert not requests and not client.http.cookies
    assert client.session.current is None and client.session.pending is None


TICKET_LIST = "/classes/com.korail.mobile.myTicket.MyTicketNewList.do"


@pytest.mark.parametrize(
    "base_url,attributes,usable",
    [
        ("https://api.example.invalid", "Path=/unrelated", False),
        ("https://api.example.invalid", "Path=" + LOGIN, False),
        ("https://api.example.invalid", "Path=/", True),
        ("https://api.example.invalid", "Path=/classes", True),
        ("https://api.example.invalid", "Path=" + TICKET_LIST, True),
        ("https://api.example.invalid", "Path=/; Domain=other.invalid", False),
        ("https://api.example.invalid", "Path=/; Max-Age=0", False),
        ("https://api.example.invalid", "Path=/; Secure", True),
        ("http://api.example.invalid", "Path=/; Secure", False),
        ("https://api.example.invalid/prefix", "Path=/classes", False),
        ("https://api.example.invalid/prefix", "Path=/prefix/classes", True),
    ],
)
def test_login_requires_cookie_for_configured_ticket_list(
    scripted_client_factory, base_url, attributes, usable
):
    """Usable means selected by the jar for list_tickets, not acceptance by every remote API."""
    contexts = []

    def provider(context):
        contexts.append(context)
        return "synthetic-token"

    client, requests, pending = scripted_client_factory(
        [
            *bootstrap(),
            httpx.Response(200, json=envelope(), headers={"Set-Cookie": f"JSESSIONID={COOKIE}; {attributes}"}),
            envelope(),
        ],
        config=synthetic_config(
            base_url=base_url, dynapath=DynapathConfig(enabled=True, token_provider=provider)
        ),
    )
    if usable:
        session = client.login(ID, PASSWORD)
        assert session is client.session.current and session.jsessionid == COOKIE
        assert len(requests) == 3
        client.list_tickets()
        assert requests[-1].headers["cookie"] == f"JSESSIONID={COOKIE}"
        assert requests[-1].url.path == base_url.removeprefix("https://api.example.invalid") + TICKET_LIST
        assert not pending
    else:
        with pytest.raises(KorailAuthError) as caught:
            client.login(ID, PASSWORD)
        assert caught.value.raw["h_msg_cd"] == "IRZ000001"
        assert client.session.current is None and not client.http.cookies
        assert len(requests) == 3 and pending == [envelope()]
    assert client.session.pending is None and len(contexts) == 1


@pytest.mark.parametrize("first_path", ["/", LOGIN, "/unrelated"])
def test_usable_multipath_session_cookie_is_still_accepted(scripted_client_factory, first_path):
    both = httpx.Response(
        200,
        json=envelope(),
        headers=[
            ("Set-Cookie", f"JSESSIONID=synthetic-other; Path={first_path}"),
            ("Set-Cookie", f"JSESSIONID={COOKIE}; Path=/classes"),
        ],
    )
    client, requests, _ = scripted_client_factory([*bootstrap(), both, envelope()])
    session = client.login(ID, PASSWORD)
    assert session.jsessionid in ({COOKIE, "synthetic-other"} if first_path == "/" else {COOKIE})
    client.list_tickets()
    assert f"JSESSIONID={session.jsessionid}" in requests[-1].headers["cookie"]
    assert len(requests) == 4


@pytest.mark.parametrize("empty_path", ["/", "/classes"])
def test_empty_multipath_cookie_does_not_hide_usable_session(scripted_client_factory, empty_path):
    other_path = "/classes" if empty_path == "/" else "/"
    response = httpx.Response(
        200,
        json=envelope(),
        headers=[
            ("Set-Cookie", f"JSESSIONID=; Path={empty_path}"),
            ("Set-Cookie", f"JSESSIONID={COOKIE}; Path={other_path}"),
        ],
    )
    client, requests, _ = scripted_client_factory([*bootstrap(), response, envelope()])
    assert client.login(ID, PASSWORD).jsessionid == COOKIE
    client.list_tickets()
    assert f"JSESSIONID={COOKIE}" in requests[-1].headers["cookie"]


def test_other_cookie_value_cannot_supply_session_cookie(scripted_client_factory):
    response = httpx.Response(
        200,
        json=envelope(),
        headers={"Set-Cookie": 'OTHER="synthetic; JSESSIONID=synthetic-fake"; Path=/'},
    )
    client, requests, _ = scripted_client_factory([*bootstrap(), response])
    with pytest.raises(KorailAuthError):
        client.login(ID, PASSWORD)
    assert len(requests) == 3 and not client.http.cookies and client.session.current is None
