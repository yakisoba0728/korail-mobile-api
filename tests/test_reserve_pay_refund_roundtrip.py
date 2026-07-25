"""Offline safety tests for the real-card operator script.

``scripts/reserve_pay_refund_roundtrip.py`` is the one thing in this repository
that can move real money, so what is pinned here is its SAFETY behaviour rather
than its convenience:

* importing it performs no I/O and reads no environment variable
* the card comes from the environment and from nowhere else
* the PAN never reaches stdout, on any path, including failures
* it refuses to run without every opt-in, and refuses to start on an account
  that already holds a reservation
* a payment failure cancels the unpaid hold and never attempts a refund
* any failure after a successful reserve prints the PNR, what is outstanding,
  and a runnable recovery command

Every request goes through ``httpx.MockTransport``. Nothing here touches the
network, and every card value below is an obviously-fake placeholder.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

from korail_mobile_api import CardPayment, KorailClient, KorailSession

SCRIPT_PATH = (
    Path(__file__).parents[1] / "scripts" / "reserve_pay_refund_roundtrip.py"
)
SCRIPT_SOURCE = SCRIPT_PATH.read_text(encoding="utf-8")


def _load_script(name: str = "reserve_pay_refund_roundtrip"):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rt = _load_script()


# Obviously-fake placeholders. 4111111111111111 is the industry-standard test
# PAN; nothing here is transmitted anywhere.
PLACEHOLDER_CARD_NUMBER = "4111111111111111"
PLACEHOLDER_CARD_PASSWORD = "00"
PLACEHOLDER_CARD_EXPIRE = "3012"
PLACEHOLDER_CARD_BIRTHDAY = "900101"
SYNTHETIC_PNR = "SYNTHETICPNR1"
#: A PNR shaped exactly like a live one: KORAIL issues 15 DECIMAL DIGITS. This
#: value is synthetic (a real PNR starts from the issue date), but its shape is
#: the real one, and its shape is the whole point -- a 15-digit run is
#: indistinguishable from an Amex PAN, so any generic card-number pattern eats
#: it. The 2026-07-25 live run lost its PNR to exactly that.
LIVE_SHAPED_PNR = "399999999999999"

SEARCH = "/classes/com.korail.mobile.seatMovie.ScheduleView"
HISTORY = "/classes/com.korail.mobile.reservation.ReservationView"
RESERVE = "/classes/com.korail.mobile.certification.TicketReservation"
DETAIL = "/classes/com.korail.mobile.certification.ReservationList"
PAYMENT = "/classes/com.korail.mobile.payment.ReservationPayment"
TICKETS = "/classes/com.korail.mobile.myTicket.MyTicketList"
SEL_TICKET = "/classes/com.korail.mobile.refunds.SelTicketInfo"
COMMISSION = "/classes/com.korail.mobile.refunds.CommissionView"
REFUND = "/classes/com.korail.mobile.refunds.RefundsRequest"
CANCEL = "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk"


def _ok(**extra: Any) -> dict[str, Any]:
    return {"h_msg_cd": "SYNTHETIC.OK", "h_msg_txt": "ok", "strResult": "SUCC", **extra}


def _train_row(train_no: str) -> dict[str, Any]:
    return {
        "h_trn_no": train_no,
        "h_trn_gp_cd": "100",
        "h_dpt_rs_stn_cd": "0001",
        "h_arv_rs_stn_cd": "0020",
        "h_dpt_rs_stn_nm": "서울",
        "h_arv_rs_stn_nm": "부산",
        "h_dpt_dt": "20990101",
        "h_dpt_tm": "060000",
        "h_arv_tm": "083000",
        "h_run_dt": "20990101",
        "h_trn_clsf_cd": "00",
        "h_dpt_stn_run_ordr": "1",
        "h_arv_stn_run_ordr": "2",
        "h_gen_rsv_cd": "11",
        "h_dpt_stn_cons_ordr": "1",
        "h_arv_stn_cons_ordr": "2",
        "h_seat_att_cd": "015",
        "h_trn_clsf_nm": "KTX",
    }


def _replies(*, pnr: str = SYNTHETIC_PNR, **overrides: Any) -> dict[str, dict[str, Any]]:
    base = {
        SEARCH: _ok(trn_infos={"trn_info": [_train_row("00101"), _train_row("00103")]}),
        HISTORY: _ok(jrny_infos={"jrny_info": []}),
        RESERVE: _ok(
            h_pnr_no=pnr,
            h_jrny_cnt="1",
            h_wct_no="SYNTHETIC_WCT",
            h_tmp_job_sqno1="SYNTHETIC_JOB_1",
            h_tmp_job_sqno2="SYNTHETIC_JOB_2",
            h_tot_prc="8400",
            h_tot_rcvd_amt="8400",
            jrny_infos={
                "jrny_info": [{"h_jrny_sqno": "0001", "h_rsv_chg_no": "001"}]
            },
        ),
        DETAIL: _ok(
            h_pnr_no=pnr,
            h_wct_no="SYNTHETIC_WCT",
            h_jrny_cnt="1",
            h_tot_fare="8400",
            h_tot_prc="8400",
            h_tot_dcnt_amt="0",
            h_tot_rcvd_amt="8400",
            h_payment_flg="N",
            # The live server sends the seat row's car number as a JSON NUMBER,
            # not the String the APK's DAO declares. On 2026-07-25 that killed
            # this step after a real unpaid hold already existed, so the shape
            # is carried here on the default reply rather than in one test.
            jrny_infos={
                "jrny_info": [
                    {
                        "h_jrny_sqno": "001",
                        "h_trn_no": "00101",
                        "seat_infos": {
                            "seat_info": [
                                {
                                    "h_srcar_no": 3,
                                    "h_seat_no": 12,
                                    "h_rcvd_amt": 8400,
                                }
                            ]
                        },
                    }
                ]
            },
        ),
        PAYMENT: _ok(h_img_tk_flg="N"),
        TICKETS: _ok(
            tickets=[
                {
                    "h_pnr_no": pnr,
                    "h_orgtk_ret_sale_dt": "20990101",
                    "h_orgtk_wct_no": "SYNTHETIC_WCT",
                    "h_orgtk_sale_sqno": "0001",
                    "h_orgtk_ret_pwd": "SYNTHETIC_RETPWD",
                }
            ]
        ),
        SEL_TICKET: _ok(
            h_pnr_no=pnr,
            retPsbFlg="Y",
            h_compa_nm="",
            h_compa_brth="",
        ),
        COMMISSION: _ok(ret_amt="8400", ret_fee="0", prg_psb_flg="Y"),
        REFUND: _ok(),
        CANCEL: _ok(),
    }
    base.update(overrides)
    return base


class _Recorder:
    def __init__(self, replies: dict[str, dict[str, Any]]) -> None:
        self.replies = replies
        self.seen: list[tuple[str, str]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append((request.method, request.url.path))
        body = self.replies.get(request.url.path)
        if body is None:  # pragma: no cover - guards test wiring mistakes
            raise AssertionError(
                f"unexpected {request.method} {request.url.path}"
            )
        return httpx.Response(200, json=body)

    def paths(self) -> list[str]:
        return [path for _, path in self.seen]


def _card() -> CardPayment:
    return CardPayment(
        card_number=PLACEHOLDER_CARD_NUMBER,
        card_password=PLACEHOLDER_CARD_PASSWORD,
        card_expire=PLACEHOLDER_CARD_EXPIRE,
        birthday=PLACEHOLDER_CARD_BIRTHDAY,
    )


def _round_trip(
    recorder: _Recorder, monkeypatch: pytest.MonkeyPatch, **env: str
) -> Any:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    client = KorailClient(transport=httpx.MockTransport(recorder))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    # The login handshake is not what these tests are about; stub it so every
    # recorded request belongs to the round trip itself.
    monkeypatch.setattr(
        client, "login", lambda *a, **k: KorailSession(jsessionid="s")
    )
    monkeypatch.setattr(rt, "read_credentials_from_env", lambda: ("m", "p"))
    card = _card()
    console = rt._console_for(card)
    args = argparse.Namespace(date="20990101", min_interval=1.5, recover=False)
    return rt.RoundTrip(client, console, card, args)


def _assert_no_card_leak(text: str) -> None:
    for secret in (
        PLACEHOLDER_CARD_NUMBER,
        PLACEHOLDER_CARD_EXPIRE,
        PLACEHOLDER_CARD_BIRTHDAY,
    ):
        assert secret not in text, secret
    # Not even a fragment of the PAN.
    assert PLACEHOLDER_CARD_NUMBER[:6] not in text
    assert PLACEHOLDER_CARD_NUMBER[-4:] not in text


# --- import safety -----------------------------------------------------------


def test_module_level_code_is_only_definitions_and_constants():
    """Structural proof that importing cannot do anything.

    Every top-level statement must be an import, a definition, a constant
    assignment, or the ``if __name__ == "__main__"`` guard. A stray call at
    module level would fail here.
    """
    tree = ast.parse(SCRIPT_SOURCE)
    for node in tree.body:
        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Assign,
                ast.AnnAssign,
                ast.Expr,  # the module docstring
            ),
        ):
            if isinstance(node, ast.Expr):
                assert isinstance(node.value, ast.Constant), ast.dump(node)
            continue
        assert isinstance(node, ast.If), ast.dump(node)
        assert ast.unparse(node.test) == "__name__ == '__main__'"


def test_importing_reads_no_environment_variable_and_opens_no_file(
    monkeypatch: pytest.MonkeyPatch,
):
    class _Poisoned(dict):
        def __getitem__(self, key):  # pragma: no cover - must never run
            raise AssertionError(f"import read os.environ[{key!r}]")

        def get(self, key, default=None):  # pragma: no cover
            raise AssertionError(f"import read os.environ.get({key!r})")

    def _no_open(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("import opened a file")

    monkeypatch.setattr(os, "environ", _Poisoned())
    monkeypatch.setattr("builtins.open", _no_open)
    module = _load_script("reserve_pay_refund_roundtrip_import_probe")
    assert module.DEFAULT_DAYS_AHEAD == 14


# --- the card comes only from the environment --------------------------------


def test_the_script_declares_no_card_source_other_than_the_environment():
    for name in (
        "KORAIL_CARD_NUMBER",
        "KORAIL_CARD_PASSWORD",
        "KORAIL_CARD_EXPIRE",
        "KORAIL_CARD_BIRTHDAY",
    ):
        assert name in SCRIPT_SOURCE
    # No file source anywhere in the script...
    for forbidden in ("open(", "read_text", "write_text", "Path(", "json.dump"):
        assert forbidden not in SCRIPT_SOURCE, forbidden
    # ...and no command-line option that could carry a card value, because argv
    # is world-readable through `ps`.
    options = {
        action.dest for action in rt.build_parser()._actions
    }
    assert options == {"help", "date", "min_interval", "recover"}


@pytest.mark.parametrize(
    "missing",
    [
        "KORAIL_CARD_NUMBER",
        "KORAIL_CARD_PASSWORD",
        "KORAIL_CARD_EXPIRE",
        "KORAIL_CARD_BIRTHDAY",
    ],
)
def test_read_card_from_env_aborts_when_any_value_is_absent(
    monkeypatch: pytest.MonkeyPatch, missing: str
):
    monkeypatch.setenv("KORAIL_CARD_NUMBER", PLACEHOLDER_CARD_NUMBER)
    monkeypatch.setenv("KORAIL_CARD_PASSWORD", PLACEHOLDER_CARD_PASSWORD)
    monkeypatch.setenv("KORAIL_CARD_EXPIRE", PLACEHOLDER_CARD_EXPIRE)
    monkeypatch.setenv("KORAIL_CARD_BIRTHDAY", PLACEHOLDER_CARD_BIRTHDAY)
    monkeypatch.delenv(missing)
    with pytest.raises(rt.RoundTripAborted) as excinfo:
        rt.read_card_from_env()
    assert missing in str(excinfo.value)


@pytest.mark.parametrize(
    "name,value",
    [
        ("KORAIL_CARD_NUMBER", "4111-1111-1111-1111"),
        ("KORAIL_CARD_PASSWORD", "0"),
        ("KORAIL_CARD_EXPIRE", "301"),
        ("KORAIL_CARD_BIRTHDAY", "90010"),
    ],
)
def test_read_card_from_env_rejects_a_malformed_value(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
):
    monkeypatch.setenv("KORAIL_CARD_NUMBER", PLACEHOLDER_CARD_NUMBER)
    monkeypatch.setenv("KORAIL_CARD_PASSWORD", PLACEHOLDER_CARD_PASSWORD)
    monkeypatch.setenv("KORAIL_CARD_EXPIRE", PLACEHOLDER_CARD_EXPIRE)
    monkeypatch.setenv("KORAIL_CARD_BIRTHDAY", PLACEHOLDER_CARD_BIRTHDAY)
    monkeypatch.setenv(name, value)
    with pytest.raises(rt.RoundTripAborted):
        rt.read_card_from_env()


def test_the_card_hides_every_value_from_repr():
    assert PLACEHOLDER_CARD_NUMBER not in repr(_card())
    assert PLACEHOLDER_CARD_BIRTHDAY not in repr(_card())


# --- the console cannot emit a card secret -----------------------------------


def test_console_masks_the_pan_password_expiry_and_birthday():
    console = rt._console_for(_card())
    text = console.scrub(
        f"pan={PLACEHOLDER_CARD_NUMBER} pwd={PLACEHOLDER_CARD_PASSWORD} "
        f"exp={PLACEHOLDER_CARD_EXPIRE} birth={PLACEHOLDER_CARD_BIRTHDAY}"
    )
    _assert_no_card_leak(text)


def test_console_masks_a_pan_written_with_separators():
    console = rt._console_for(_card())
    spaced = " ".join(
        PLACEHOLDER_CARD_NUMBER[index : index + 4] for index in range(0, 16, 4)
    )
    text = console.scrub(f"card {spaced} end")
    assert "4111" not in text
    assert "1111" not in text


def test_console_keeps_the_pnr_and_ordinary_numbers_readable():
    # The PNR is the single most important thing this script prints; a scrubber
    # that ate it would defeat the whole recovery design. Dates, times and
    # amounts must survive too.
    console = rt._console_for(_card())
    text = console.scrub(
        f"PNR {SYNTHETIC_PNR} 20990101 060000-083000 amount 8400 fee 0"
    )
    assert SYNTHETIC_PNR in text
    assert "20990101 060000-083000" in text
    assert "8400" in text


def test_console_keeps_a_live_shaped_15_digit_pnr_but_still_masks_the_pan():
    """The exact regression from the 2026-07-25 live run.

    A 15-digit PNR and a 16-digit PAN sit in one string. The PAN must go; the
    PNR must survive byte for byte. A digit-run rule cannot do both, which is
    why the scrubber matches the card by exact value instead.
    """
    console = rt._console_for(_card())
    text = console.scrub(
        f"LIVE HOLD CREATED   PNR {LIVE_SHAPED_PNR} "
        f"card {PLACEHOLDER_CARD_NUMBER}"
    )
    assert LIVE_SHAPED_PNR in text
    _assert_no_card_leak(text)


def test_the_recovery_command_survives_scrubbing_with_a_live_shaped_pnr():
    # The banner prints a runnable command line. Redacting the PNR inside it is
    # what left the last live run holding an unpaid reservation it could not
    # name; the command has to come out copy-pasteable.
    console = rt._console_for(_card())
    command = rt._recovery_command(LIVE_SHAPED_PNR)
    scrubbed = console.scrub(command)
    assert scrubbed == command
    assert f"KORAIL_RECOVER_PNR={LIVE_SHAPED_PNR}" in scrubbed
    assert "[REDACTED" not in scrubbed


def test_console_scrubs_exception_text_too():
    console = rt._console_for(_card())
    error = ValueError(f"rejected card {PLACEHOLDER_CARD_NUMBER}")
    _assert_no_card_leak(console.scrub(error))


# --- opt-ins -----------------------------------------------------------------


@pytest.mark.parametrize(
    "present",
    [
        {},
        {"KORAIL_MOBILE_API_LIVE": "1"},
        {"KORAIL_MOBILE_API_LIVE": "1", "KORAIL_LIVE_MUTATION": "1"},
    ],
)
def test_main_refuses_unless_all_three_opt_ins_are_set(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    present: dict[str, str],
):
    for name in (
        "KORAIL_MOBILE_API_LIVE",
        "KORAIL_LIVE_MUTATION",
        "KORAIL_LIVE_REAL_CHARGE",
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in present.items():
        monkeypatch.setenv(name, value)

    def _no_client(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("a client was built despite a missing opt-in")

    monkeypatch.setattr(rt, "KorailClient", _no_client)
    assert rt.main([]) == 2
    assert "ABORTED" in capsys.readouterr().out


def test_main_refuses_before_reading_the_card_when_opt_ins_are_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    for name in (
        "KORAIL_MOBILE_API_LIVE",
        "KORAIL_LIVE_MUTATION",
        "KORAIL_LIVE_REAL_CHARGE",
    ):
        monkeypatch.delenv(name, raising=False)

    def _no_card():  # pragma: no cover - must never run
        raise AssertionError("the card was read despite a missing opt-in")

    monkeypatch.setattr(rt, "read_card_from_env", _no_card)
    assert rt.main([]) == 2


# --- consents ----------------------------------------------------------------


def test_every_consent_grants_exactly_one_category():
    for consent in (
        rt.reserve_consent(),
        rt.cancel_consent(),
        rt.refund_consent(),
        rt.real_card_payment_consent(),
    ):
        granted = [
            name
            for name in ("reserve", "payment", "cancel", "refund")
            if getattr(consent, f"allow_{name}")
        ]
        assert len(granted) == 1, granted
        assert consent.dry_run is False


def test_only_the_payment_consent_acknowledges_a_real_charge():
    payment = rt.real_card_payment_consent()
    assert payment.real_card_acknowledged is True
    assert payment.fake_card_only is False
    for consent in (
        rt.reserve_consent(),
        rt.cancel_consent(),
        rt.refund_consent(),
    ):
        assert consent.real_card_acknowledged is False
        assert consent.fake_card_only is True


# --- refusing to start -------------------------------------------------------


def test_refuses_to_start_when_the_account_already_holds_a_reservation(
    monkeypatch: pytest.MonkeyPatch,
):
    recorder = _Recorder(
        _replies(
            **{
                HISTORY: _ok(
                    jrny_infos={
                        "jrny_info": [
                            {
                                "train_infos": {
                                    "train_info": [
                                        {"h_pnr_no": "SOMEONE_ELSES_PNR"}
                                    ]
                                }
                            }
                        ]
                    }
                )
            }
        )
    )
    trip = _round_trip(recorder, monkeypatch)
    with pytest.raises(rt.RoundTripAborted) as excinfo:
        trip.run()
    assert "already holds" in str(excinfo.value)
    # Nothing was reserved, paid, or refunded.
    assert RESERVE not in recorder.paths()
    assert PAYMENT not in recorder.paths()
    assert REFUND not in recorder.paths()


# --- the happy path ----------------------------------------------------------


def test_full_round_trip_reserves_pays_refunds_and_leaks_no_card(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    recorder = _Recorder(_replies())
    trip = _round_trip(recorder, monkeypatch)
    assert trip.run() == 0
    assert recorder.paths() == [
        HISTORY,
        SEARCH,
        RESERVE,
        DETAIL,
        PAYMENT,
        TICKETS,
        SEL_TICKET,
        COMMISSION,
        REFUND,
        HISTORY,
    ]
    out = capsys.readouterr().out
    _assert_no_card_leak(out)
    # The PNR is printed the instant the hold exists, and the amounts the
    # operator has to see are printed before the money moves.
    assert SYNTHETIC_PNR in out
    assert out.index(SYNTHETIC_PNR) < out.index("PAYING WITH THE REAL CARD")
    assert "REFUND AMOUNT: 8400 KRW" in out
    assert "REFUND FEE:    0 KRW" in out
    assert out.index("REFUND FEE") < out.index("[h] refunding")


def test_a_live_shaped_pnr_reaches_the_operator_through_every_banner(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """End-to-end proof of the 2026-07-25 regression, on the path that failed.

    The hold banner and the failure banner both print the PNR and the runnable
    recovery command. With a 15-digit PNR the previous digit-run backstop turned
    every one of those into ``[REDACTED_CARD]``, which is how a real unpaid hold
    ended up with no identifier attached to it.
    """
    # TICKETS returns nothing, so the run fails AFTER paying: this exercises the
    # hold banner and the not-clean failure banner in one pass.
    recorder = _Recorder(
        _replies(pnr=LIVE_SHAPED_PNR, **{TICKETS: _ok(tickets=[])})
    )
    trip = _round_trip(recorder, monkeypatch)
    with pytest.raises(rt.RoundTripAborted):
        trip.run()
    out = capsys.readouterr().out
    assert f"LIVE HOLD CREATED   PNR {LIVE_SHAPED_PNR}" in out
    assert f"PNR {LIVE_SHAPED_PNR}" in out
    assert rt._recovery_command(LIVE_SHAPED_PNR) in out
    # Nothing anywhere in the run was mistaken for a card number.
    assert "[REDACTED_CARD]" not in out
    _assert_no_card_leak(out)


def test_the_confirmed_amount_is_the_independently_read_one(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    recorder = _Recorder(_replies())
    trip = _round_trip(recorder, monkeypatch)
    assert trip.run() == 0
    assert "confirmed: 8400 KRW will be charged" in capsys.readouterr().out


# --- stopping before the money moves -----------------------------------------


def test_an_amount_disagreement_stops_before_paying_and_releases_the_hold(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    recorder = _Recorder(
        _replies(
            **{
                DETAIL: _ok(
                    h_pnr_no=SYNTHETIC_PNR,
                    h_wct_no="SYNTHETIC_WCT",
                    h_jrny_cnt="1",
                    h_tot_fare="9900",
                    h_tot_prc="9900",
                    h_tot_dcnt_amt="0",
                    # Deliberately not the hold's 8400.
                    h_tot_rcvd_amt="9900",
                    h_payment_flg="N",
                )
            }
        )
    )
    trip = _round_trip(recorder, monkeypatch)
    with pytest.raises(rt.RoundTripAborted) as excinfo:
        trip.run()
    assert "does not match" in str(excinfo.value)
    assert PAYMENT not in recorder.paths()
    assert CANCEL in recorder.paths()
    assert SYNTHETIC_PNR in capsys.readouterr().out


def test_a_fare_over_the_ceiling_stops_before_paying(
    monkeypatch: pytest.MonkeyPatch,
):
    recorder = _Recorder(_replies())
    trip = _round_trip(recorder, monkeypatch, KORAIL_MAX_FARE="1000")
    with pytest.raises(rt.RoundTripAborted) as excinfo:
        trip.run()
    assert "KORAIL_MAX_FARE" in str(excinfo.value)
    assert PAYMENT not in recorder.paths()
    assert CANCEL in recorder.paths()


# --- payment failure ---------------------------------------------------------


def test_a_declined_payment_cancels_the_hold_and_never_refunds(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    recorder = _Recorder(
        _replies(
            **{
                PAYMENT: {
                    "strResult": "FAIL",
                    "h_msg_cd": "WRC000123",
                    "h_msg_txt": "card declined",
                }
            }
        )
    )
    trip = _round_trip(recorder, monkeypatch)
    assert trip.run() == 1
    paths = recorder.paths()
    assert PAYMENT in paths
    assert CANCEL in paths
    # A payment that did not succeed is never followed by a refund attempt.
    assert REFUND not in paths
    assert COMMISSION not in paths
    out = capsys.readouterr().out
    assert "h_msg_cd=WRC000123" in out
    assert "the hold was cancelled and nothing" in out
    # The run stopped cleanly, so no recovery banner is raised for a hold that
    # no longer exists.
    assert "THIS RUN DID NOT FINISH CLEANLY." not in out
    _assert_no_card_leak(out)


# --- failure after the charge ------------------------------------------------


def test_a_failure_after_payment_banners_the_pnr_and_the_recovery_command(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    # The payment succeeded but the paid ticket's refund identity cannot be
    # found. This is the worst case the script is designed against: money has
    # moved and the operator must be told exactly what they are holding.
    recorder = _Recorder(_replies(**{TICKETS: _ok(tickets=[])}))
    trip = _round_trip(recorder, monkeypatch)
    with pytest.raises(rt.RoundTripAborted):
        trip.run()
    out = capsys.readouterr().out
    assert "THIS RUN DID NOT FINISH CLEANLY." in out
    assert f"PNR {SYNTHETIC_PNR}" in out
    assert "The ticket is PAID -- it needs a REFUND. MONEY HAS MOVED." in out
    assert rt._recovery_command(SYNTHETIC_PNR) in out
    assert REFUND not in recorder.paths()
    _assert_no_card_leak(out)


def test_a_payment_that_never_answers_is_reported_as_unknown_not_unpaid(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    # A transport failure after the server committed looks exactly like one
    # before it. Printing "UNPAID -- no money moved" here would be the most
    # dangerous thing this script could say, so it must claim nothing.
    replies = _replies()
    recorder = _Recorder(replies)

    def _handler(request: httpx.Request) -> httpx.Response:
        recorder.seen.append((request.method, request.url.path))
        if request.url.path == PAYMENT:
            raise httpx.ConnectError("connection reset")
        return httpx.Response(200, json=replies[request.url.path])

    client = KorailClient(transport=httpx.MockTransport(_handler))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    monkeypatch.setattr(
        client, "login", lambda *a, **k: KorailSession(jsessionid="s")
    )
    monkeypatch.setattr(rt, "read_credentials_from_env", lambda: ("m", "p"))
    card = _card()
    trip = rt.RoundTrip(
        client,
        rt._console_for(card),
        card,
        argparse.Namespace(date="20990101", min_interval=1.5, recover=False),
    )
    with pytest.raises(Exception):
        trip.run()
    out = capsys.readouterr().out
    assert "The payment outcome is UNKNOWN" in out
    assert "MAY BE PAID" in out
    assert "No money moved." not in out
    assert f"PNR {SYNTHETIC_PNR}" in out
    assert rt._recovery_command(SYNTHETIC_PNR) in out
    _assert_no_card_leak(out)


def test_the_recovery_command_names_the_scripts_own_recover_mode():
    command = rt._recovery_command(SYNTHETIC_PNR)
    assert "scripts/reserve_pay_refund_roundtrip.py --recover" in command
    assert f"KORAIL_RECOVER_PNR={SYNTHETIC_PNR}" in command
    # The recovery run must not need the real-charge opt-in: it only cancels or
    # refunds, and neither charges anything.
    assert "KORAIL_LIVE_REAL_CHARGE" not in command


# --- refund identity matching ------------------------------------------------


def test_find_ticket_identity_ignores_a_ticket_belonging_to_another_pnr():
    raw = {
        "tickets": [
            {
                "h_pnr_no": "SOMEONE_ELSE",
                "h_orgtk_ret_sale_dt": "20990101",
                "h_orgtk_wct_no": "OTHER_WCT",
                "h_orgtk_sale_sqno": "0001",
                "h_orgtk_ret_pwd": "OTHER_PWD",
            }
        ]
    }
    assert rt.find_ticket_identity(raw, pnr_no=SYNTHETIC_PNR) is None


def test_find_ticket_identity_accepts_an_identity_nested_under_its_pnr():
    raw = {
        "tickets": [
            {
                "h_pnr_no": SYNTHETIC_PNR,
                "seat_infos": {
                    "seat_info": [
                        {
                            "h_orgtk_ret_sale_dt": "20990101",
                            "h_orgtk_wct_no": "SYNTHETIC_WCT",
                            "h_orgtk_sale_sqno": "0001",
                            "h_orgtk_ret_pwd": "SYNTHETIC_RETPWD",
                        }
                    ]
                },
            }
        ]
    }
    reference = rt.find_ticket_identity(raw, pnr_no=SYNTHETIC_PNR)
    assert reference is not None
    assert reference.sale_window_no == "SYNTHETIC_WCT"
    assert reference.return_password == "SYNTHETIC_RETPWD"


# --- recovery mode -----------------------------------------------------------


def test_recover_cancels_an_unpaid_hold(monkeypatch: pytest.MonkeyPatch):
    recorder = _Recorder(
        _replies(
            **{
                TICKETS: _ok(tickets=[]),
                HISTORY: _ok(
                    jrny_infos={
                        "jrny_info": [
                            {
                                "train_infos": {
                                    "train_info": [
                                        {
                                            "h_pnr_no": SYNTHETIC_PNR,
                                            "h_trn_no": "00101",
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ),
            }
        )
    )
    client = KorailClient(transport=httpx.MockTransport(recorder))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    monkeypatch.setattr(
        client, "login", lambda *a, **k: KorailSession(jsessionid="s")
    )
    monkeypatch.setattr(rt, "read_credentials_from_env", lambda: ("m", "p"))
    assert rt.recover(client, rt._Console(), SYNTHETIC_PNR) == 0
    assert CANCEL in recorder.paths()
    assert REFUND not in recorder.paths()


def test_recover_reports_and_exits_non_zero_for_an_unknown_pnr(
    monkeypatch: pytest.MonkeyPatch,
):
    recorder = _Recorder(_replies(**{TICKETS: _ok(tickets=[])}))
    client = KorailClient(transport=httpx.MockTransport(recorder))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    monkeypatch.setattr(
        client, "login", lambda *a, **k: KorailSession(jsessionid="s")
    )
    monkeypatch.setattr(rt, "read_credentials_from_env", lambda: ("m", "p"))
    assert rt.recover(client, rt._Console(), "NOT_ON_THIS_ACCOUNT") == 1
    # Nothing was cancelled or refunded on a PNR the account does not hold.
    assert CANCEL not in recorder.paths()
    assert REFUND not in recorder.paths()


def test_find_train_no_reads_the_train_recorded_beside_the_pnr():
    raw = {
        "tickets": [
            {"h_pnr_no": "OTHER", "h_trn_no": "00999"},
            {"h_pnr_no": SYNTHETIC_PNR, "h_trn_no": "00101"},
        ]
    }
    assert rt.find_train_no(raw, pnr_no=SYNTHETIC_PNR) == "00101"
    assert rt.find_train_no(raw, pnr_no="MISSING") == ""


def test_recover_refunds_a_paid_ticket_after_printing_its_commission(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    recorder = _Recorder(_replies())
    client = KorailClient(transport=httpx.MockTransport(recorder))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    monkeypatch.setattr(
        client, "login", lambda *a, **k: KorailSession(jsessionid="s")
    )
    monkeypatch.setattr(rt, "read_credentials_from_env", lambda: ("m", "p"))
    assert rt.recover(client, rt._Console(), SYNTHETIC_PNR) == 0
    out = capsys.readouterr().out
    assert "REFUND AMOUNT: 8400 KRW" in out
    assert out.index("REFUND AMOUNT") < out.index("refund: strResult=SUCC")
    assert REFUND in recorder.paths()
    assert CANCEL not in recorder.paths()
