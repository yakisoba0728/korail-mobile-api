"""Drive ONE live reserve -> pay -> refund round trip with a REAL card.

This is the operator script for the one thing this package could never do
before: settle a reservation with a real, chargeable card. Money actually moves.
It is meant to be run by a human, once, against their OWN account and their OWN
card, and it is deliberately loud at every step.

Safety posture
--------------
* THREE opt-ins are required, and none of them alone runs anything:
  ``KORAIL_MOBILE_API_LIVE=1`` (the package-wide live switch),
  ``KORAIL_LIVE_MUTATION=1`` (this run may change state), and
  ``KORAIL_LIVE_REAL_CHARGE=1`` (this run may charge a real card).
* ``KORAIL_MAX_FARE`` -- a ceiling in won -- is REQUIRED on the charging path,
  not a suggestion. It is the only thing that caps what may be charged, and it
  is checked before the card is read, before login, and before any request. A
  run without it would accept whatever amount the server says is owed.
  ``--recover`` does not need it because neither of its branches charges.
* The card is read ONLY from the environment: ``KORAIL_CARD_NUMBER``,
  ``KORAIL_CARD_PASSWORD`` (the first two digits of the card PIN),
  ``KORAIL_CARD_EXPIRE`` (YYMM) and ``KORAIL_CARD_BIRTHDAY`` (YYMMDD). Never a
  file, never a command-line argument (argv is visible in ``ps``), and never a
  default value. A missing one aborts before login.
* The PAN and the card password are scrubbed from EVERY line this script writes,
  including exception text and every error path, by :class:`_Console`. It does
  so by EXACT VALUE -- the four card values it was handed and nothing else. The
  card number is never printed, not even partially, and nothing is written to
  disk.
* The PNR is printed IN FULL, on purpose. A paid ticket whose PNR the operator
  does not know is the worst outcome this script can produce, so the PNR is
  printed the instant it exists and again, in an unmissable banner with a
  runnable recovery command, on any later failure. No digit-run pattern is
  applied to this output: a PNR is 15 digits and cannot be told from a PAN by
  shape, so such a pattern masks the one value that must always get through.
* Reserve, pay, cancel and refund each go out under their own single-category
  consent; no consent object in this file grants two money-moving categories at
  once, and each factory asserts that.
* Every request is paced (default 1.5s minimum spacing) because KORAIL bans IPs
  for macro-like traffic.
* The module is import-safe: importing it performs no I/O, reads no environment
  variable, and builds no client. Everything happens under :func:`main`.

Flow
----
a. log in, and REFUSE to start unless the account holds zero reservations
b. search the configured route ~14 days out (inside the fee-free refund window)
   and select a train: ``KORAIL_TRAIN_NO`` pins one exactly; otherwise the
   cheapest by fare QUOTE, else the cheapest by the search row's own price HINT,
   else the first available one -- and the printed reason always says which of
   the four it was
c. reserve one adult in the cheapest class; print the PNR immediately
d. read the reservation back independently and cross-check the amount owed
   against the hold's own amount; STOP (and cancel) if they disagree
e. pay with the real card; print the raw confirmation codes
f. on payment failure, cancel the still-unpaid hold and exit non-zero -- never
   attempt a refund for a payment that did not succeed
g. locate the paid ticket's refund identity and ask ``get_refund_commission``
   what comes back and what the fee is; print both BEFORE refunding
h. refund; print the raw codes
i. verify the account is back to zero reservations

Recovery
--------
``--recover`` (with ``KORAIL_RECOVER_PNR`` set) resolves one stranded PNR: it
cancels an unpaid hold, or refunds a paid ticket after printing its commission.
The failure banner prints the exact command line for it.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from typing import Any, NamedTuple

from korail_mobile_api import (
    CardPayment,
    KorailClient,
    MutationConsent,
    OriginalTicketReference,
    PaidTicket,
    PriceFareLeg,
    PriceFareQuoteRequest,
    RefundCompanion,
    ReservationHoldResponse,
    TicketReservationDetailRequest,
    TrainSearchQuery,
    TrainSummary,
)
from korail_mobile_api.live import (
    build_config_from_env,
    live_enabled,
    read_credentials_from_env,
)


LIVE_MUTATION_ENV = "KORAIL_LIVE_MUTATION"
LIVE_REAL_CHARGE_ENV = "KORAIL_LIVE_REAL_CHARGE"
CARD_NUMBER_ENV = "KORAIL_CARD_NUMBER"
CARD_PASSWORD_ENV = "KORAIL_CARD_PASSWORD"
CARD_EXPIRE_ENV = "KORAIL_CARD_EXPIRE"
CARD_BIRTHDAY_ENV = "KORAIL_CARD_BIRTHDAY"
MAX_FARE_ENV = "KORAIL_MAX_FARE"
TRAIN_NO_ENV = "KORAIL_TRAIN_NO"
RECOVER_PNR_ENV = "KORAIL_RECOVER_PNR"

DEFAULT_MIN_INTERVAL_S = 1.5
#: Far enough out that a refund is inside KORAIL's fee-free window, near enough
#: that the schedule is published. Overridable with ``--date``/``KORAIL_TEST_DATE``.
DEFAULT_DAYS_AHEAD = 14
#: The reservation-code value that means "a general seat is available", which is
#: also what ``build_single_adult_reservation_form`` insists on.
AVAILABLE_GENERAL_SEAT = "11"

#: The four keys that together identify a settled ticket for a refund. They are
#: what ``refunds.SelTicketInfo``/``CommissionView`` and the refund mutation all
#: key off; ``h_orgtk_ret_sale_dt`` is the source the app copies into the refund
#: form's ``h_orgtk_sale_dt`` (TicketReceiptActivity.java:402).
_TICKET_IDENTITY_KEYS = (
    "h_orgtk_ret_sale_dt",
    "h_orgtk_wct_no",
    "h_orgtk_sale_sqno",
    "h_orgtk_ret_pwd",
)


class RoundTripAborted(RuntimeError):
    """A refusal raised before or instead of a state change."""


def _secret_pattern(secret: str) -> re.Pattern[str]:
    """Match ``secret`` as a standalone token, spaces/dashes allowed inside.

    The token anchoring is what lets a two-digit card password be scrubbed
    without mangling every amount that happens to contain those digits: "00" is
    replaced when it stands alone, never inside "8400".
    """
    body = r"[ \-]*".join(re.escape(character) for character in secret)
    return re.compile(rf"(?<![0-9A-Za-z]){body}(?![0-9A-Za-z])")


class _Console:
    """stdout that can never emit a card secret, and never eats the PNR.

    Every string printed by this script goes through :meth:`scrub` first, which
    substitutes -- by EXACT VALUE, token-anchored and separator-tolerant -- the
    four secrets read from the card environment variables, and nothing else.

    There is deliberately NO generic digit-run pattern here, neither the
    package's ``CARD_RE`` nor a stricter local variant. A Korail PNR is a
    15-digit numeric string, which is indistinguishable from a PAN by shape
    alone (a 15-digit PAN is an ordinary Amex number), so any 13-19 digit rule
    masks the PNR as well. A 2026-07-25 live run proved it: the hold banner read
    ``LIVE HOLD CREATED   PNR [REDACTED_CARD]`` and so did the recovery command
    line beneath it, leaving the operator with a real unpaid hold and no
    identifier for it. That is precisely the orphaned-hold outcome this whole
    script is shaped to prevent, and it is a far worse failure than the one the
    backstop guarded against.

    Masking by exact value loses nothing real. The only card this process ever
    holds is the one it was handed, it is matched here separator-tolerantly, and
    :func:`_console_for` self-checks that match against the actual card before a
    single line is printed. A PAN that is not ours cannot reach this stdout:
    KORAIL never echoes one back, and we never read one from anywhere else.
    """

    def __init__(self, secrets: tuple[str, ...] = ()) -> None:
        self._patterns = tuple(
            _secret_pattern(secret)
            for secret in sorted(
                {secret for secret in secrets if secret},
                key=len,
                reverse=True,
            )
        )

    def scrub(self, value: Any) -> str:
        text = value if isinstance(value, str) else str(value)
        for pattern in self._patterns:
            text = pattern.sub("[REDACTED]", text)
        return text

    def say(self, message: Any = "") -> None:
        print(self.scrub(message), flush=True)

    def banner(self, lines: tuple[str, ...]) -> None:
        rule = "!" * 76
        self.say("")
        self.say(rule)
        for line in lines:
            self.say(f"!! {line}")
        self.say(rule)
        self.say("")


class _Pacer:
    """Enforce a minimum spacing between outbound requests."""

    def __init__(self, min_interval_s: float) -> None:
        self.min_interval_s = min_interval_s
        self._last: float | None = None

    def wait(self) -> None:
        now = time.monotonic()
        if self._last is not None:
            remaining = self.min_interval_s - (now - self._last)
            if remaining > 0:
                time.sleep(remaining)
        self._last = time.monotonic()


def _install_pacing(client: KorailClient, pacer: _Pacer) -> None:
    inner = client.http._client
    hooks = dict(inner.event_hooks)
    hooks["request"] = [
        *hooks.get("request", []),
        lambda request: pacer.wait(),
    ]
    inner.event_hooks = hooks


# --- environment inputs ------------------------------------------------------


def _required_env(name: str, *, why: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RoundTripAborted(f"{name} is required ({why})")
    return value


def read_card_from_env() -> CardPayment:
    """Build the card from the environment ONLY.

    There is no file source, no command-line source (argv is world-readable via
    ``ps``) and no default: every value must be present or the run aborts. The
    returned :class:`CardPayment` hides all four values from ``repr``.
    """
    number = _required_env(CARD_NUMBER_ENV, why="the card number to charge")
    password = _required_env(
        CARD_PASSWORD_ENV, why="the first two digits of the card PIN"
    )
    expire = _required_env(CARD_EXPIRE_ENV, why="the card expiry as YYMM")
    birthday = _required_env(
        CARD_BIRTHDAY_ENV, why="the personal-auth birthday as YYMMDD"
    )
    for value, name, length in (
        (number, CARD_NUMBER_ENV, None),
        (password, CARD_PASSWORD_ENV, 2),
        (expire, CARD_EXPIRE_ENV, 4),
        (birthday, CARD_BIRTHDAY_ENV, 6),
    ):
        if not value.isdigit():
            raise RoundTripAborted(f"{name} must be decimal digits")
        if length is not None and len(value) != length:
            raise RoundTripAborted(f"{name} must be exactly {length} digits")
    return CardPayment(
        card_number=number,
        card_password=password,
        card_expire=expire,
        birthday=birthday,
    )


def _console_for(card: CardPayment) -> _Console:
    console = _Console(
        (
            card.card_number,
            card.card_password,
            card.card_expire,
            card.birthday,
        )
    )
    # Prove the scrubber actually works on this card before anything is printed.
    probe = console.scrub(
        f"probe {card.card_number} {card.card_password} "
        f"{card.card_expire} {card.birthday}"
    )
    for secret in (
        card.card_number,
        card.card_password,
        card.card_expire,
        card.birthday,
    ):
        if secret in probe:
            raise RoundTripAborted(
                "the output scrubber failed its self-check; refusing to run"
            )
    return console


def _default_date() -> str:
    return time.strftime(
        "%Y%m%d", time.localtime(time.time() + DEFAULT_DAYS_AHEAD * 86400)
    )


def _max_fare_from_env() -> int | None:
    raw = os.environ.get(MAX_FARE_ENV, "").strip()
    if not raw:
        return None
    if not raw.isdigit():
        raise RoundTripAborted(f"{MAX_FARE_ENV} must be a whole number of won")
    return int(raw)


# --- consents ----------------------------------------------------------------


def _single_category_consent(category: str, **extra: bool) -> MutationConsent:
    """One consent, one category. Never two money-moving categories at once.

    The check raises rather than asserts on purpose: ``python -O`` strips
    ``assert``, and this is exactly the kind of invariant that must not quietly
    disappear under an optimisation flag.
    """
    consent = MutationConsent(
        **{f"allow_{category}": True}, dry_run=False, **extra
    )
    granted = [
        name
        for name in ("reserve", "payment", "cancel", "refund")
        if getattr(consent, f"allow_{name}")
    ]
    if granted != [category]:
        raise RoundTripAborted(
            f"consent for {category!r} unexpectedly granted {granted}"
        )
    return consent


def reserve_consent() -> MutationConsent:
    return _single_category_consent("reserve")


def cancel_consent() -> MutationConsent:
    return _single_category_consent("cancel")


def refund_consent() -> MutationConsent:
    return _single_category_consent("refund")


def real_card_payment_consent() -> MutationConsent:
    """The ONLY consent in this file that can move money.

    Both halves are stated deliberately: ``fake_card_only=False`` (this is not a
    test card) and ``real_card_acknowledged=True`` (yes, charge it). Setting one
    without the other is refused by both ``pay_with_card`` and the transmit gate.
    """
    consent = _single_category_consent(
        "payment", fake_card_only=False, real_card_acknowledged=True
    )
    if not consent.real_card_acknowledged or consent.fake_card_only:
        raise RoundTripAborted(
            "the real-card payment consent is not what it claims to be"
        )
    return consent


# --- helpers -----------------------------------------------------------------


def _envelope(response: Any) -> str:
    return (
        f"strResult={getattr(response, 'str_result', None)} "
        f"h_msg_cd={getattr(response, 'h_msg_cd', None)} "
        f"h_msg_txt={getattr(response, 'h_msg_txt', None)}"
    )


def _succeeded(response: Any) -> bool:
    return getattr(response, "str_result", None) == "SUCC"


def _won(amount: str | None) -> int | None:
    """원화 금액 문자열을 정수로. 모르는 값은 ``None`` 이고 0 이 아니다.

    KORAIL 은 같은 금액을 라우트마다 다른 폭으로 싣는다. 2026-07-31 실서버 관측:
    예약 응답(``certification.ReservationHold``)의 ``h_rcvd_amt`` 는 ``"8400"``
    인데 예약 상세(``tk.SelTicketInfo``)의 ``h_tot_rcvd_amt`` 는
    ``"0000000000008400"`` — 16자리 0채움이다. 둘 다 8,400원이다. 그래서 금액
    비교는 문자열이 아니라 수로 해야 한다.

    숫자가 아니거나 비어 있으면 ``None`` 을 준다. 결제 직전 교차검증에서 쓰이는
    함수라, 읽지 못한 값을 0 으로 접으면 "0원이 맞다"고 통과시켜 버린다.
    """
    if amount is None:
        return None
    text = amount.strip()
    if not text or not text.isdigit():
        return None
    return int(text)


def _won_text(amount: str | None) -> str:
    """배너에 찍을 금액. 0채움을 벗기고, 못 읽으면 원문을 그대로 보여 준다.

    ``refunds.CommissionView`` 는 이 두 필드를 14자리 0채움으로 보낸다
    (2026-07-31 관측: ``ret_amt='00000000008400'``,
    ``ret_fee='00000000000000'``). 조작자가 눈으로 읽고 환불을 계속할지 정하는
    줄이라, 그대로 찍으면 자릿수를 세게 된다. 숫자로 읽히지 않는 값은 감추지
    않는다 — 그것 자체가 봐야 할 신호다.
    """
    won = _won(amount)
    return str(won) if won is not None else repr(amount)


def find_ticket_identity(
    raw: Any,
    *,
    pnr_no: str,
    _pnr_in_scope: str | None = None,
) -> OriginalTicketReference | None:
    """Locate the refund identity belonging to ``pnr_no`` in a raw response.

    Walks the tree carrying down the nearest enclosing ``h_pnr_no``, so an
    identity block is only accepted when it (or an ancestor) names the PNR this
    run created. That matters because the ticket list can hold other tickets:
    refunding the wrong one would be irreversible.
    """
    if isinstance(raw, dict):
        scope = raw.get("h_pnr_no") or raw.get("pnrNo")
        in_scope = scope if isinstance(scope, str) and scope else _pnr_in_scope
        if in_scope == pnr_no and all(
            isinstance(raw.get(key), str) and raw[key].strip()
            for key in _TICKET_IDENTITY_KEYS
        ):
            return OriginalTicketReference(
                sale_window_no=raw["h_orgtk_wct_no"],
                sale_date=raw["h_orgtk_ret_sale_dt"],
                sale_sequence=raw["h_orgtk_sale_sqno"],
                return_password=raw["h_orgtk_ret_pwd"],
            )
        for value in raw.values():
            found = find_ticket_identity(
                value, pnr_no=pnr_no, _pnr_in_scope=in_scope
            )
            if found is not None:
                return found
    elif isinstance(raw, list):
        for item in raw:
            found = find_ticket_identity(
                item, pnr_no=pnr_no, _pnr_in_scope=_pnr_in_scope
            )
            if found is not None:
                return found
    return None


def find_train_no(raw: Any, *, pnr_no: str) -> str:
    """Find the train number recorded next to ``pnr_no``, or ``""``.

    The refund form carries ``trnNo``; a recovery run that only has a PNR still
    wants to send it rather than an empty field.
    """
    if isinstance(raw, dict):
        if raw.get("h_pnr_no") == pnr_no or raw.get("pnrNo") == pnr_no:
            train_no = raw.get("h_trn_no") or raw.get("trnNo")
            if isinstance(train_no, str) and train_no.strip():
                return train_no
        for value in raw.values():
            found = find_train_no(value, pnr_no=pnr_no)
            if found:
                return found
    elif isinstance(raw, list):
        for item in raw:
            found = find_train_no(item, pnr_no=pnr_no)
            if found:
                return found
    return ""


#: The price fields ``RsvInquiryResponse.TrainInfo`` declares on a search row
#: (``:102-104``), in the order they are preferred. ``h_rcvd_amt`` is the amount
#: actually collected, which is what a comparison wants; ``h_rcvd_fare`` is the
#: fare component. Neither is a quote -- ``trn.prcFare.do`` is the only authority
#: on what will be charged -- and no app screen was found reading either one off
#: THIS row, so whatever is here is a HINT and is labelled as one wherever it is
#: printed. It orders candidates; it never decides what may be paid.
_FARE_HINT_KEYS = ("h_rcvd_amt", "h_rcvd_fare")


def _fare_hint(train: TrainSummary) -> int | None:
    """The search row's own price field, in won, or ``None``.

    Reads only what the row actually carries: a value that is missing, empty or
    not a plain decimal string yields ``None`` rather than a guess. Accepts a
    JSON number as well as a string, because KORAIL is inconsistent about which
    it sends for a field its DAO declares as ``String``.
    """
    for key in _FARE_HINT_KEYS:
        value = train.raw.get(key)
        if type(value) is int and value > 0:
            return value
        if isinstance(value, str) and value.strip().isdigit():
            hint = int(value.strip())
            if hint > 0:
                return hint
    return None


def _pnr_present(raw: Any, *, pnr_no: str) -> bool:
    """Whether ``pnr_no`` appears anywhere in a raw response."""
    if isinstance(raw, dict):
        if raw.get("h_pnr_no") == pnr_no or raw.get("pnrNo") == pnr_no:
            return True
        return any(_pnr_present(value, pnr_no=pnr_no) for value in raw.values())
    if isinstance(raw, list):
        return any(_pnr_present(item, pnr_no=pnr_no) for item in raw)
    return False


def _safe_raw(read: Any, console: _Console, name: str) -> Any:
    """Read a source, reporting rather than raising when it refuses.

    Used only on the recovery paths, where one unavailable source must not stop
    the other from being tried.
    """
    try:
        return getattr(read(), "raw", None)
    except Exception as exc:  # 넓게 잡는다: 다른 출처가 아직 통할 수 있다
        console.say(f"    [note] the {name} read failed: {type(exc).__name__}")
        return None


def _recovery_command(pnr_no: str) -> str:
    return (
        f"KORAIL_MOBILE_API_LIVE=1 {LIVE_MUTATION_ENV}=1 "
        f"{RECOVER_PNR_ENV}={pnr_no} "
        "python3 scripts/reserve_pay_refund_roundtrip.py --recover"
    )


#: What the operator is left holding, per :attr:`RoundTrip.state`.
_OUTSTANDING_BY_STATE = {
    "none": "Nothing outstanding was recorded, but VERIFY the account anyway.",
    "unpaid": "The hold is UNPAID -- it needs a CANCEL. No money moved.",
    # The payment call went out and did not come back. The server may well have
    # settled it. Claiming "unpaid" here would be the single most dangerous
    # thing this script could print, so it claims nothing.
    "paying": (
        "The payment outcome is UNKNOWN -- the call did not return. The ticket "
        "MAY BE PAID. Do not assume it is not; the recovery command below "
        "checks which it is."
    ),
    "paid": "The ticket is PAID -- it needs a REFUND. MONEY HAS MOVED.",
    "refunded": (
        "The refund was accepted, but the account was not verified clean."
    ),
}


class _Candidate(NamedTuple):
    train: TrainSummary
    #: An authoritative quote from ``trn.prcFare.do``, when one can be built.
    fare: int | None
    #: The search row's own price field, when it carries one. See above.
    hint: int | None = None


# --- the round trip ----------------------------------------------------------


class RoundTrip:
    def __init__(
        self,
        client: KorailClient,
        console: _Console,
        card: CardPayment,
        args: argparse.Namespace,
    ) -> None:
        self.client = client
        self.console = console
        self.card = card
        self.args = args
        self.max_fare = _max_fare_from_env()
        #: Set the instant a hold exists, so the failure banner always has it.
        self.pnr_no: str | None = None
        #: "none" -> nothing exists yet, "unpaid" -> a hold needing a cancel,
        #: "paid" -> a settled ticket needing a refund, "refunded" -> done.
        #: The failure banner tells the operator which of those they are
        #: holding, which is the difference between a free cleanup and a
        #: forgotten charge.
        self.state = "none"

    # -- step a ---------------------------------------------------------------

    def login(self) -> None:
        member_no, password = read_credentials_from_env()
        self.console.say("[a] logging in")
        session = self.client.login(member_no, password)
        if not session.jsessionid:
            raise RoundTripAborted("login returned no session")
        self.console.say("    logged in")

    def outstanding_pnrs(self) -> tuple[str, ...]:
        history = self.client.get_reservation_history()
        return tuple(
            item.pnr_no for item in history.items if item.pnr_no
        )

    def require_zero_reservations(self, when: str) -> None:
        self.console.say(f"[a] checking the account holds no reservations ({when})")
        outstanding = self.outstanding_pnrs()
        if outstanding:
            raise RoundTripAborted(
                f"the account already holds {len(outstanding)} reservation(s) "
                f"({when}): "
                + ", ".join(outstanding)
                + ". This script only runs on a clean account, so it can never "
                "confuse someone else's booking with its own."
            )
        self.console.say("    confirmed: zero reservations")

    # -- step b ---------------------------------------------------------------

    def select_train(self) -> _Candidate:
        date = self.args.date
        departure = os.environ.get("KORAIL_DEPARTURE_STATION", "서울")
        arrival = os.environ.get("KORAIL_ARRIVAL_STATION", "부산")
        departure_time = os.environ.get("KORAIL_DEPARTURE_TIME", "060000")
        self.console.say(
            f"[b] searching {departure} -> {arrival} on {date} from {departure_time}"
        )
        query = TrainSearchQuery(
            departure_station_code=departure,
            arrival_station_code=arrival,
            departure_date=date,
            departure_time=departure_time,
        )
        search = self.client.search_trains(query)
        available = [
            train
            for train in search.trains
            if train.general_reservation_code == AVAILABLE_GENERAL_SEAT
        ]
        if not available:
            raise RoundTripAborted(
                f"no train on {departure}->{arrival} {date} has an available "
                "general seat"
            )
        self.console.say(f"    {len(available)} train(s) with an available seat")

        wanted = os.environ.get(TRAIN_NO_ENV, "").strip()
        if wanted:
            chosen = next(
                (train for train in available if train.train_no == wanted), None
            )
            if chosen is None:
                raise RoundTripAborted(
                    f"{TRAIN_NO_ENV}={wanted} is not among the available trains"
                )
            candidate = _Candidate(
                chosen,
                self._quote_fare(chosen, search),
                _fare_hint(chosen),
            )
            self._announce(candidate, reason=f"chosen by {TRAIN_NO_ENV}")
            return candidate

        priced = [
            _Candidate(train, self._quote_fare(train, search), _fare_hint(train))
            for train in available
        ]
        quoted = [item for item in priced if item.fare is not None]
        if quoted:
            candidate = min(quoted, key=lambda item: item.fare or 0)
            self._announce(candidate, reason="cheapest quoted fare")
            return candidate
        # A live ScheduleView row carries no goods number and the envelope's
        # h_gd_no is empty, so trn.prcFare.do cannot be built for it, and
        # "cheapest" has no authoritative source. Second best is the row's OWN
        # price field, which the app's DAO declares (see _FARE_HINT_KEYS); when
        # the server fills it in, ordering by it is reading KORAIL's own number
        # rather than inventing a train-class ranking. It is called a hint
        # everywhere it is printed, because it is not what the payment will
        # settle. The authoritative amount is still read back and cross-checked
        # at step (d), before any money moves, and KORAIL_MAX_FARE is the
        # operator's ceiling there.
        hinted = [item for item in priced if item.hint is not None]
        if hinted:
            candidate = min(hinted, key=lambda item: item.hint or 0)
            self._announce(
                candidate,
                reason=(
                    "cheapest by the search row's own price HINT -- no fare "
                    "quote was obtainable, so this is NOT a quote"
                ),
            )
            self.console.say(
                f"    the hint orders the choice only; {MAX_FARE_ENV} is what "
                "caps the charge"
            )
            return candidate
        candidate = priced[0]
        self._announce(
            candidate,
            reason=(
                "FIRST available train -- no fare quote and no price hint were "
                "obtainable, so 'cheapest' could NOT be established"
            ),
        )
        self.console.say(
            f"    set {TRAIN_NO_ENV} to choose a specific train, and "
            f"{MAX_FARE_ENV} to cap what may be charged"
        )
        return candidate

    def _quote_fare(self, train: TrainSummary, search: Any) -> int | None:
        goods_no = train.goods_no or (search.metadata.product_no or "")
        if not goods_no:
            return None
        try:
            quote = self.client.get_price_fare_quote(
                PriceFareQuoteRequest(
                    legs=(
                        PriceFareLeg(
                            departure_station_code=(
                                train.departure_station_code or ""
                            ),
                            arrival_station_code=train.arrival_station_code or "",
                            run_date=train.run_date or self.args.date,
                            train_no=train.train_no,
                            goods_no=goods_no,
                            requested_seat_attribute_code=(
                                train.seat_attribute_code or "015"
                            ),
                            train_group_code=train.train_group_code or "",
                            standing_train_classification_code="",
                        ),
                    )
                )
            )
        except Exception as exc:  # 넓게 잡는다: 운임을 못 매기는 열차는 정상이다
            self.console.say(
                f"    [note] no fare quote for train {train.train_no}: "
                f"{type(exc).__name__}"
            )
            return None
        fares = [
            int(fare.received_fare)
            for fare in quote.fares
            if fare.received_fare and fare.received_fare.isdigit()
        ]
        return min(fares) if fares else None

    def _announce(self, candidate: _Candidate, *, reason: str) -> None:
        train = candidate.train
        if candidate.fare is not None:
            fare = f"{candidate.fare} KRW (quoted)"
        elif candidate.hint is not None:
            # Never the bare number: an operator reading "8400 KRW" would
            # reasonably take it for the amount about to be charged.
            fare = (
                f"~{candidate.hint} KRW (HINT from the search row, not a quote)"
            )
        else:
            fare = "UNKNOWN (no fare quote available)"
        self.console.say(
            f"    selected train {train.train_no} "
            f"{train.train_class_name or train.train_class_code} "
            f"{train.departure_station_name}->{train.arrival_station_name} "
            f"{train.departure_date} {train.departure_time}-{train.arrival_time}"
        )
        self.console.say(f"    fare: {fare}   ({reason})")
        if self.max_fare is not None:
            self.console.say(f"    ceiling: {MAX_FARE_ENV}={self.max_fare} KRW")

    # -- step c ---------------------------------------------------------------

    def reserve(self, train: TrainSummary) -> ReservationHoldResponse:
        self.console.say("[c] reserving ONE adult, cheapest class")
        hold = self.client.reserve(train, consent=reserve_consent())
        if not isinstance(hold, ReservationHoldResponse):
            raise RoundTripAborted(
                "reserve returned a preview instead of a live hold"
            )
        pnr = hold.pnr_no
        if not pnr:
            raise RoundTripAborted(
                f"reserve returned no PNR: {_envelope(hold)}"
            )
        # Before anything else can fail.
        self.pnr_no = pnr
        self.state = "unpaid"
        self.console.banner(
            (
                f"LIVE HOLD CREATED   PNR {pnr}",
                "It is UNPAID. If this run stops now, cancel it with:",
                f"  {_recovery_command(pnr)}",
            )
        )
        self.console.say(f"    {_envelope(hold)}")
        return hold

    # -- step d ---------------------------------------------------------------

    def confirm_amount(self, hold: ReservationHoldResponse) -> str:
        self.console.say("[d] reading the reservation back to confirm the amount")
        pnr = hold.pnr_no or ""
        detail = self.client.get_ticket_reservation_detail(
            TicketReservationDetailRequest(pnr_no=pnr)
        )
        server_amount = detail.total_received_amount
        hold_amount = hold.received_amount
        self.console.say(
            f"    server says owed: {server_amount!r}; "
            f"hold said: {hold_amount!r}"
        )
        # 두 값은 같은 금액인데 폭이 다르다 (:func:`_won` 참고). 문자열로 비교하면
        # 8,400원과 8,400원이 서로 다르다고 나와서, 맞는 금액인데도 결제 전에
        # 멈춘다. 2026-07-31 실서버 왕복이 정확히 여기서 걸렸다.
        server_won = _won(server_amount)
        hold_won = _won(hold_amount)
        if server_won is None or hold_won is None or server_won != hold_won:
            raise RoundTripAborted(
                "the amount the server says is owed does not match the hold's "
                f"own amount ({server_amount!r} vs {hold_amount!r}); refusing "
                "to pay an amount two sources disagree on"
            )
        if self.max_fare is not None and server_won > self.max_fare:
            raise RoundTripAborted(
                f"the amount owed ({server_won} KRW) exceeds "
                f"{MAX_FARE_ENV}={self.max_fare} KRW"
            )
        self.console.say(f"    confirmed: {server_won} KRW will be charged")
        # 0채움을 벗긴 쪽을 돌려준다. 폭은 라우트마다 다르고 금액은 하나다.
        return str(server_won)

    # -- step e/f -------------------------------------------------------------

    def pay(self, hold: ReservationHoldResponse) -> bool:
        self.console.say("[e] PAYING WITH THE REAL CARD -- money moves now")
        # From here until the call returns, the payment outcome is UNKNOWN: a
        # transport failure after the server committed looks exactly like one
        # before it. pay_with_card only raises when it never got an envelope,
        # so the state is narrowed the moment one arrives.
        self.state = "paying"
        result = self.client.pay_with_card(
            hold, self.card, consent=real_card_payment_consent()
        )
        self.console.say(f"    {_envelope(result)}")
        self.console.say(f"    coupons returned: {len(result.coupons)}")
        if not _succeeded(result):
            # A declined payment is an answer: the server refused, so the hold
            # is still unpaid and still cancellable.
            self.state = "unpaid"
            return False
        self.state = "paid"
        return True

    def cancel_unpaid(self, hold: ReservationHoldResponse) -> bool:
        self.console.say("[f] cancelling the still-unpaid hold")
        result = self.client.cancel_unpaid_hold(hold, consent=cancel_consent())
        self.console.say(f"    {_envelope(result)}")
        if _succeeded(result):
            self.state = "none"
            return True
        return False

    # -- step g ---------------------------------------------------------------

    def refund_identity(self, pnr_no: str) -> OriginalTicketReference:
        self.console.say("[g] locating the paid ticket's refund identity")
        for name, read in (
            ("ticket list", self.client.get_ticket_list),
            ("reservation history", self.client.get_reservation_history),
        ):
            try:
                raw = getattr(read(), "raw", None)
            except Exception as exc:  # 넓게 잡는다: 다른 출처를 시도한다
                self.console.say(
                    f"    [note] the {name} read failed: {type(exc).__name__}"
                )
                continue
            reference = find_ticket_identity(raw, pnr_no=pnr_no)
            if reference is not None:
                self.console.say(f"    found it in the {name}")
                return reference
        raise RoundTripAborted(
            f"could not find the refund identity for PNR {pnr_no}; the ticket "
            "is PAID and must be refunded by hand"
        )

    def quote_refund(self, reference: OriginalTicketReference) -> None:
        self.console.say("[g] asking what a refund returns and what it costs")
        detail = self.client.get_refund_ticket_detail(reference)
        self.console.say(
            f"    ticket detail: {_envelope(detail)} "
            f"refund_possible_flag={detail.refund_possible_flag!r}"
        )
        commission = self.client.get_refund_commission(
            reference,
            RefundCompanion(
                name=detail.companion_name or "",
                certificate_no=detail.companion_birth_date or "",
            ),
        )
        self.console.banner(
            (
                f"REFUND AMOUNT: {_won_text(commission.refund_amount)} KRW",
                f"REFUND FEE:    {_won_text(commission.refund_fee)} KRW",
                f"proceed flag:  {commission.proceed_possible_flag!r}",
                f"note:          {commission.secondary_message_text!r}",
            )
        )

    # -- step h ---------------------------------------------------------------

    def refund(
        self,
        reference: OriginalTicketReference,
        *,
        pnr_no: str,
        train_no: str,
    ) -> bool:
        self.console.say("[h] refunding")
        result = self.client.refund(
            PaidTicket(
                pnr_no=pnr_no,
                sale_date=reference.sale_date,
                sale_window_no=reference.sale_window_no,
                sale_sequence=reference.sale_sequence,
                return_password=reference.return_password,
                train_no=train_no,
            ),
            consent=refund_consent(),
        )
        self.console.say(f"    {_envelope(result)}")
        return _succeeded(result)

    # -- orchestration --------------------------------------------------------

    def run(self) -> int:
        self.login()
        self.require_zero_reservations("before starting")
        candidate = self.select_train()
        hold = self.reserve(candidate.train)
        pnr = hold.pnr_no or ""
        clean = False
        try:
            try:
                self.confirm_amount(hold)
            except RoundTripAborted:
                # Nothing has been charged yet and the hold is unambiguously
                # ours and unpaid, so release it rather than leaving it behind.
                self.console.say(
                    "    stopping BEFORE payment; releasing the unpaid hold"
                )
                if self.cancel_unpaid(hold):
                    clean = True
                raise
            if not self.pay(hold):
                # A failed payment is NOT a refund situation. The hold is still
                # unpaid, so release it and stop.
                if not self.cancel_unpaid(hold):
                    raise RoundTripAborted(
                        "payment failed AND the unpaid hold could not be "
                        "cancelled"
                    )
                self.console.say(
                    "    payment failed; the hold was cancelled and nothing "
                    "was charged"
                )
                clean = True
                return 1
            reference = self.refund_identity(pnr)
            self.quote_refund(reference)
            if not self.refund(
                reference, pnr_no=pnr, train_no=candidate.train.train_no
            ):
                raise RoundTripAborted("the refund was refused by the server")
            self.state = "refunded"
            self.console.say("[i] verifying the account is back to zero")
            self.require_zero_reservations("after the refund")
            clean = True
            return 0
        finally:
            if not clean:
                self.console.banner(
                    (
                        "THIS RUN DID NOT FINISH CLEANLY.",
                        f"PNR {pnr}",
                        _OUTSTANDING_BY_STATE.get(
                            self.state, "State UNKNOWN -- check the account."
                        ),
                        "Recover it with:",
                        f"  {_recovery_command(pnr)}",
                        "or do it by hand in the KORAIL app. Do not ignore this.",
                    )
                )


# --- recovery ----------------------------------------------------------------


def _hold_for_cancel(pnr_no: str) -> ReservationHoldResponse:
    """The minimum hold shape ``build_unpaid_reservation_cancel_form`` accepts.

    A stranded PNR is all the operator has; the cancel form needs only the PNR
    plus a single-journey successful hold, and the app hardcodes the rest.
    """
    return ReservationHoldResponse(
        h_msg_cd="",
        h_msg_txt="",
        str_result="SUCC",
        raw={},
        pnr_no=pnr_no,
        journey_count="1",
    )


def recover(client: KorailClient, console: _Console, pnr_no: str) -> int:
    console.say(f"[recover] resolving PNR {pnr_no}")
    member_no, password = read_credentials_from_env()
    client.login(member_no, password)
    tickets_raw = _safe_raw(client.get_ticket_list, console, "ticket list")
    history_raw = _safe_raw(
        client.get_reservation_history, console, "reservation history"
    )
    reference = find_ticket_identity(tickets_raw, pnr_no=pnr_no)
    if reference is None:
        reference = find_ticket_identity(history_raw, pnr_no=pnr_no)
    if reference is not None:
        console.say("    the ticket is PAID (it has an original-sale identity)")
        detail = client.get_refund_ticket_detail(reference)
        commission = client.get_refund_commission(
            reference,
            RefundCompanion(
                name=detail.companion_name or "",
                certificate_no=detail.companion_birth_date or "",
            ),
        )
        console.banner(
            (
                f"REFUND AMOUNT: {_won_text(commission.refund_amount)} KRW",
                f"REFUND FEE:    {_won_text(commission.refund_fee)} KRW",
            )
        )
        train_no = find_train_no(tickets_raw, pnr_no=pnr_no) or find_train_no(
            history_raw, pnr_no=pnr_no
        )
        result = client.refund(
            PaidTicket(
                pnr_no=pnr_no,
                sale_date=reference.sale_date,
                sale_window_no=reference.sale_window_no,
                sale_sequence=reference.sale_sequence,
                return_password=reference.return_password,
                train_no=train_no,
            ),
            consent=refund_consent(),
        )
        console.say(f"    refund: {_envelope(result)}")
        return 0 if _succeeded(result) else 1
    if not _pnr_present(history_raw, pnr_no=pnr_no) and not _pnr_present(
        tickets_raw, pnr_no=pnr_no
    ):
        console.say(
            f"    PNR {pnr_no} is not on this account's reservation history or "
            "ticket list; nothing to recover here"
        )
        return 1
    console.say("    the reservation is UNPAID; cancelling it")
    result = client.cancel_unpaid_hold(
        _hold_for_cancel(pnr_no), consent=cancel_consent()
    )
    console.say(f"    cancel: {_envelope(result)}")
    return 0 if _succeeded(result) else 1


# --- entry point -------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run ONE live reserve -> pay -> refund round trip with a real "
            "card. The card is read from the environment only."
        )
    )
    parser.add_argument(
        "--date",
        default="",
        help=(
            "departure date YYYYMMDD; defaults to KORAIL_TEST_DATE, else "
            f"{DEFAULT_DAYS_AHEAD} days from today"
        ),
    )
    parser.add_argument(
        "--min-interval",
        type=float,
        default=DEFAULT_MIN_INTERVAL_S,
        help="minimum seconds between requests (rate-limit protection)",
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help=(
            f"resolve the single PNR in {RECOVER_PNR_ENV}: cancel it if it is "
            "unpaid, refund it if it is paid"
        ),
    )
    return parser


def _require_opt_ins(*, real_charge: bool) -> None:
    if not live_enabled():
        raise RoundTripAborted(
            "Set KORAIL_MOBILE_API_LIVE=1 to touch the live server"
        )
    if os.environ.get(LIVE_MUTATION_ENV) != "1":
        raise RoundTripAborted(
            f"Set {LIVE_MUTATION_ENV}=1 to opt in to changing state"
        )
    if real_charge and os.environ.get(LIVE_REAL_CHARGE_ENV) != "1":
        raise RoundTripAborted(
            f"Set {LIVE_REAL_CHARGE_ENV}=1 to opt in to charging a REAL card"
        )
    # A ceiling is not optional on the charging path. Step (d) compares the
    # amount owed against self.max_fare, and when that is None the comparison
    # is skipped -- i.e. the script would pay whatever the server says. The
    # train choice does not make up for it: when no fare quote and no price
    # hint can be obtained, _select_train falls through to the FIRST reservable
    # train, whose class and price are whatever the route happens to offer. So
    # the operator must name the most they are willing to lose, up front. This
    # call also surfaces a malformed value here rather than 200 lines later.
    if real_charge and _max_fare_from_env() is None:
        raise RoundTripAborted(
            f"Set {MAX_FARE_ENV} to the most you are willing to be charged, in "
            "won. It is the only ceiling on this run: without it, step (d) "
            "accepts whatever amount the server says is owed. (--recover does "
            "not need it -- neither of its branches charges anything.)"
        )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = _Console()
    client: KorailClient | None = None
    try:
        _require_opt_ins(real_charge=not args.recover)
        if args.recover:
            pnr_no = _required_env(
                RECOVER_PNR_ENV, why="the PNR to recover"
            ).strip()
            client = KorailClient(build_config_from_env())
            _install_pacing(client, _Pacer(args.min_interval))
            return recover(client, console, pnr_no)

        card = read_card_from_env()
        console = _console_for(card)
        args.date = (
            args.date or os.environ.get("KORAIL_TEST_DATE") or _default_date()
        )
        if len(args.date) != 8 or not args.date.isdigit():
            raise RoundTripAborted("--date must be an 8-digit YYYYMMDD date")
        if args.date < time.strftime("%Y%m%d"):
            raise RoundTripAborted(f"--date {args.date} is in the past")
        if args.min_interval < 1.0:
            raise RoundTripAborted(
                "--min-interval below 1.0s risks a KORAIL IP ban"
            )
        console.banner(
            (
                "THIS RUN WILL CHARGE A REAL CARD AND THEN REFUND IT.",
                f"date {args.date}, one adult, cheapest class.",
                "Interrupt now if that is not what you want.",
            )
        )
        client = KorailClient(build_config_from_env())
        _install_pacing(client, _Pacer(args.min_interval))
        return RoundTrip(client, console, card, args).run()
    except RoundTripAborted as exc:
        console.say(f"ABORTED: {console.scrub(exc)}")
        return 2
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:  # 넓게 잡는다: 원본 메시지가 새어 나가게 두지 않는다
        console.say(f"FAILED: {type(exc).__name__}: {console.scrub(exc)}")
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
