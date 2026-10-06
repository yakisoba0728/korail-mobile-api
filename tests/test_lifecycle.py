"""Cleanup must preserve the first failure while attempting both connection pools."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from korail_mobile_api import Korail, KorailAuthError, KorailClient, KorailConfig


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
