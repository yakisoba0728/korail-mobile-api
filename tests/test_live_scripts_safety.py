# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Offline safety tests for the live scripts that had none.

``verify_706_new_live.py``, ``retry_unprotected_live.py`` and
``retry_delivery_roundtrip.py`` came with 7.0.6; ``capture_live_read_surface.py``
predates them and can make and cancel a real hold. All four talk to the live
server, and ``retry_delivery_roundtrip.py`` charges a real card. These hold
them to the rules ``scripts/README.md`` states for every live script, the same
way ``test_reserve_pay_refund_roundtrip.py`` holds its script:

* importing does nothing -- only imports, definitions, literal constants and
  the ``__main__`` guard at module level, and no environment read or file open
  while the module loads;
* ``main()`` refuses unless every opt-in switch the script names is set, and
  refuses before it prompts for anything, builds a client, or writes to the
  environment.

Nothing here reaches the network.
"""

from __future__ import annotations

import ast
import importlib.util
import itertools
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from korail_mobile_api import OriginalTicketReference
from korail_mobile_api.consent import MUTATION_CATEGORIES


SCRIPTS = Path(__file__).parents[1] / "scripts"

# Each script and the switches its main() requires, all of them.
OPT_INS = {
    "verify_706_new_live": ("KORAIL_MOBILE_API_LIVE", "KORAIL_LIVE_706_READS"),
    "retry_unprotected_live": ("KORAIL_MOBILE_API_LIVE", "KORAIL_LIVE_RETRY_READS"),
    "retry_delivery_roundtrip": (
        "KORAIL_MOBILE_API_LIVE",
        "KORAIL_LIVE_MUTATION",
        "KORAIL_LIVE_REAL_CHARGE",
    ),
}
# What main() may write to the environment before it refuses. Only the delivery
# round trip writes anything: its fixed fare ceiling, which the parent's gate
# requires to be present before it will judge the charging path. Never a secret.
ALLOWED_WRITES_BEFORE_REFUSAL = {"retry_delivery_roundtrip": {"KORAIL_MAX_FARE"}}

# Scripts held to the import rules. capture_live_read_surface's opt-ins depend
# on its arguments (--reserve adds a third), so its main() has its own tests.
IMPORT_SAFE = (*sorted(OPT_INS), "capture_live_read_surface")


def _load(name: str, monkeypatch: pytest.MonkeyPatch, *, as_name: str | None = None):
    # retry_delivery_roundtrip imports its sibling by module name, the way it
    # runs from a checkout: python3 scripts/<name>.py puts scripts/ on the path.
    monkeypatch.syspath_prepend(str(SCRIPTS))
    module_name = as_name or name
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", IMPORT_SAFE)
def test_module_level_code_is_only_definitions_and_literal_constants(name: str) -> None:
    """Every top-level statement is inert, and every assignment is a literal.

    A literal right-hand side is the stricter form of the roundtrip script's
    rule: ``X = some_call()`` is an assignment too, and it runs on import.
    """
    tree = ast.parse((SCRIPTS / f"{name}.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Constant), ast.dump(node)
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            assert node.value is not None
            ast.literal_eval(node.value)
            continue
        assert isinstance(node, ast.If), ast.dump(node)
        assert ast.unparse(node.test) == "__name__ == '__main__'"


@pytest.mark.parametrize("name", IMPORT_SAFE)
def test_importing_reads_no_environment_variable_and_opens_no_file(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Poisoned(dict):
        def __getitem__(self, key):  # pragma: no cover - must never run
            raise AssertionError(f"import read os.environ[{key!r}]")

        def get(self, key, default=None):  # pragma: no cover - must never run
            raise AssertionError(f"import read os.environ.get({key!r})")

    def _no_open(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("import opened a file")

    monkeypatch.setattr(os, "environ", _Poisoned())
    monkeypatch.setattr("builtins.open", _no_open)
    module = _load(name, monkeypatch, as_name=f"{name}_import_probe")
    assert callable(module.main)


def _refusing_cases():
    for name, switches in sorted(OPT_INS.items()):
        for size in range(len(switches)):
            for present in itertools.combinations(switches, size):
                label = "+".join(present) or "none"
                yield pytest.param(name, present, id=f"{name}[{label}]")


@pytest.mark.parametrize(("name", "present"), list(_refusing_cases()))
def test_main_refuses_until_every_opt_in_is_set(
    name: str,
    present: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load(name, monkeypatch)
    # A private copy of the environment, so whatever main() writes is both
    # visible here and gone after the test.
    monkeypatch.setattr(os, "environ", dict(os.environ))
    for switch in OPT_INS[name]:
        monkeypatch.delenv(switch, raising=False)
    for switch in present:
        monkeypatch.setenv(switch, "1")
    monkeypatch.setattr(sys, "argv", [f"{name}.py"])
    before = dict(os.environ)

    def _no_prompt(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("prompted for a secret despite a missing opt-in")

    def _no_client(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("built a client despite a missing opt-in")

    monkeypatch.setattr(module.getpass, "getpass", _no_prompt)
    monkeypatch.setattr(module, "KorailClient", _no_client)
    try:
        result = module.main()
    except SystemExit as refusal:
        assert "KORAIL_MOBILE_API_LIVE=1" in str(refusal.code)
    else:
        assert result == 2
    written = {
        key
        for key in set(before) | set(os.environ)
        if before.get(key) != os.environ.get(key)
    }
    assert written <= ALLOWED_WRITES_BEFORE_REFUSAL.get(name, set())


def test_delivery_round_trip_uses_the_parent_scripts_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Not a copy of the gate: whatever the parent's _require_opt_ins refuses,
    # this script refuses with it, before prompting or building anything.
    module = _load("retry_delivery_roundtrip", monkeypatch)
    monkeypatch.setattr(os, "environ", dict(os.environ))

    def parent_gate(*, real_charge: bool) -> None:
        assert real_charge is True
        raise module.operator.RoundTripAborted("the parent gate said no")

    def _no_prompt(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("prompted for a secret after the gate refused")

    monkeypatch.setattr(module.operator, "_require_opt_ins", parent_gate)
    monkeypatch.setattr(module.getpass, "getpass", _no_prompt)
    assert module.main() == 2
    assert "the parent gate said no" in capsys.readouterr().out


def test_delivery_round_trip_needs_a_real_device_identity_before_any_prompt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Every switch set, no DynaPath device values: the config is built from the
    # environment like the parent's, so this stops before a secret is asked for.
    module = _load("retry_delivery_roundtrip", monkeypatch)
    monkeypatch.setattr(os, "environ", dict(os.environ))
    for switch in OPT_INS["retry_delivery_roundtrip"]:
        monkeypatch.setenv(switch, "1")
    for name in (
        "KORAIL_DYNAPATH_DEVICE_ID",
        "KORAIL_DYNAPATH_OS_VERSION",
        "KORAIL_DYNAPATH_DEVICE_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    def _no_prompt(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("prompted for a secret without a device identity")

    def _no_client(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("built a client without a device identity")

    monkeypatch.setattr(module.getpass, "getpass", _no_prompt)
    monkeypatch.setattr(module, "KorailClient", _no_client)
    assert module.main() == 2
    assert "KORAIL_DYNAPATH_DEVICE_ID" in capsys.readouterr().out


def test_delivery_round_trip_refunds_with_the_flag_the_server_gave(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RecipientRoundTrip.quote_refund hands back what the parent read.

    run() feeds the return value into refund(); when the override dropped it,
    every refund this real-card script sent carried pbpAcepTgtFlg "N" whatever
    the refund-detail response said.
    """
    module = _load("retry_delivery_roundtrip", monkeypatch)
    detail = SimpleNamespace(
        sale_date=None,
        original_window_no=None,
        original_sale_sequence=None,
        original_return_password=None,
        refund_possible_flag="Y",
        companion_name=None,
        companion_birth_date=None,
        pbp_acceptance_target_flag="Y",
    )
    commission = SimpleNamespace(
        refund_amount="8400",
        refund_fee="0",
        proceed_possible_flag="Y",
        secondary_message_text="",
    )
    trip = object.__new__(module.RecipientRoundTrip)
    trip.client = SimpleNamespace(
        get_refund_ticket_detail=lambda reference: detail,
        get_refund_commission=lambda reference, companion: commission,
    )
    trip.console = SimpleNamespace(say=lambda *a, **k: None, banner=lambda *a, **k: None)
    reference = OriginalTicketReference(
        sale_date="20990101",
        sale_window_no="0001",
        sale_sequence="0001",
        return_password="0000",
    )
    assert trip.quote_refund(reference) == "Y"


# --- capture_live_read_surface: one hold, one cancel, nothing else -------------


def test_capture_consents_open_exactly_one_category_each(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--reserve makes one hold and cancels it; its consents can do no more.

    Checked against every category rather than the payment and refund pair the
    helpers assert themselves, so a category added later is covered too.
    """
    module = _load("capture_live_read_surface", monkeypatch)
    for helper, opened in (
        (module._reserve_consent, "reserve"),
        (module._cancel_consent, "cancel"),
    ):
        consent = helper()
        assert consent.dry_run is False
        for category in MUTATION_CATEGORIES:
            assert getattr(consent, f"allow_{category}") is (category == opened), (
                helper.__name__,
                category,
            )
        assert consent.fake_card_only is True
        assert consent.real_card_acknowledged is False


@pytest.mark.parametrize(
    ("switches", "reserve", "refusal"),
    [
        ((), False, "KORAIL_MOBILE_API_LIVE=1"),
        (("KORAIL_MOBILE_API_LIVE",), False, "KORAIL_LIVE_READ_SURFACE=1"),
        (("KORAIL_LIVE_READ_SURFACE",), False, "KORAIL_MOBILE_API_LIVE=1"),
        (
            ("KORAIL_MOBILE_API_LIVE", "KORAIL_LIVE_READ_SURFACE"),
            True,
            "KORAIL_LIVE_ALLOW_RESERVE=1",
        ),
    ],
    ids=["none", "live-only", "surface-only", "reserve-without-its-switch"],
)
def test_capture_main_refuses_before_building_anything(
    switches: tuple[str, ...],
    reserve: bool,
    refusal: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load("capture_live_read_surface", monkeypatch)
    for switch in (
        "KORAIL_MOBILE_API_LIVE",
        "KORAIL_LIVE_READ_SURFACE",
        "KORAIL_LIVE_ALLOW_RESERVE",
    ):
        monkeypatch.delenv(switch, raising=False)
    for switch in switches:
        monkeypatch.setenv(switch, "1")

    def _no_client(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("built a client despite a missing opt-in")

    monkeypatch.setattr(module, "KorailClient", _no_client)
    monkeypatch.setattr(module, "build_config_from_env", _no_client)
    out = tmp_path / "capture"
    argv = ["--out", str(out), "--date", "20990101"]
    if reserve:
        argv.append("--reserve")
    with pytest.raises(SystemExit, match=refusal):
        module.main(argv)
    assert not out.exists()


def test_no_script_guards_anything_with_assert() -> None:
    """``python -O`` strips ``assert``; a guard in a live script must survive it.

    The capture script's consent factories used to check the money categories
    with ``assert``. The round trip already raised instead, and said why.
    """
    offenders = []
    for path in sorted(SCRIPTS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders.extend(
            f"{path.name}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Assert)
        )
    assert offenders == []


def test_retry_reads_exits_non_zero_when_login_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # main() returned None, so the process exited 0 even when it could not log
    # in and read nothing.
    module = _load("retry_unprotected_live", monkeypatch)
    monkeypatch.setattr(os, "environ", dict(os.environ))
    for switch in OPT_INS["retry_unprotected_live"]:
        monkeypatch.setenv(switch, "1")
    monkeypatch.setattr(module.getpass, "getpass", lambda prompt: "synthetic")

    class _RefusingClient:
        def __init__(self, config) -> None:
            self.http = SimpleNamespace(_client=SimpleNamespace(event_hooks={"request": []}))

        def login(self, member, password):
            raise RuntimeError("synthetic login refusal")

        def logout(self) -> None:
            pass

        def close(self) -> None:
            pass

    monkeypatch.setattr(module, "KorailClient", _RefusingClient)
    assert module.main() == 1
    assert "login: RuntimeError" in capsys.readouterr().out
