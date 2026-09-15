"""Retry the delivery-recipient read on a fresh paid ticket, then refund it.

This wrapper reuses the established bounded round-trip operator and prompts all
credentials in memory. It prints only envelope codes and masked booking IDs.
"""

from __future__ import annotations

import argparse
import getpass
import os
import re

import reserve_pay_refund_roundtrip as operator
from korail_mobile_api import KorailClient, KorailConfig, OriginalTicketReference


class RedactedConsole:
    def __init__(self, inner: operator._Console) -> None:
        self.inner = inner

    def scrub(self, value: object) -> str:
        return re.sub(r"\b\d{12,19}\b", "[REDACTED_ID]", self.inner.scrub(value))

    def say(self, message: object = "") -> None:
        print(self.scrub(message), flush=True)

    def banner(self, lines: tuple[str, ...]) -> None:
        for line in lines:
            self.say(line)


class RecipientRoundTrip(operator.RoundTrip):
    def quote_refund(self, reference: OriginalTicketReference) -> None:
        detail = self.client.get_refund_ticket_detail(reference)
        fields = (
            detail.sale_date,
            detail.original_window_no,
            detail.original_sale_sequence,
            detail.original_return_password,
        )
        if all(isinstance(value, str) and value for value in fields):
            delivery_reference = OriginalTicketReference(
                sale_date=fields[0] or "",
                sale_window_no=fields[1] or "",
                sale_sequence=fields[2] or "",
                return_password=fields[3] or "",
            )
            try:
                recipient = self.client.get_delivery_recipient(delivery_reference)
            except Exception as exc:
                self.console.say(
                    f"delivery_recipient: {type(exc).__name__} "
                    f"code={getattr(exc, 'code', None)}"
                )
            else:
                self.console.say(
                    f"delivery_recipient: result={recipient.str_result} "
                    f"code={recipient.h_msg_cd} "
                    f"has_recipient={bool(recipient.acceptance_customer_management_no)}"
                )
        else:
            self.console.say("delivery_recipient: skipped (paid detail lacks exact fields)")
        super().quote_refund(reference)


def main() -> int:
    if (
        os.environ.get("KORAIL_LIVE_MUTATION") != "1"
        or os.environ.get("KORAIL_LIVE_REAL_CHARGE") != "1"
    ):
        print("Set KORAIL_LIVE_MUTATION=1 and KORAIL_LIVE_REAL_CHARGE=1")
        return 2
    os.environ["KORAIL_MOBILE_API_LIVE"] = "1"
    os.environ["KORAIL_MAX_FARE"] = "5000"
    os.environ["KORAIL_DEPARTURE_STATION"] = "서울"
    os.environ["KORAIL_ARRIVAL_STATION"] = "영등포"
    os.environ["KORAIL_DEPARTURE_TIME"] = "060000"
    os.environ["KORAIL_MEMBER_NO"] = getpass.getpass("member (hidden): ")
    os.environ["KORAIL_PASSWORD"] = getpass.getpass("password (hidden): ")
    os.environ["KORAIL_CARD_NUMBER"] = getpass.getpass("card (hidden): ")
    os.environ["KORAIL_CARD_PASSWORD"] = getpass.getpass("card PIN 2 digits (hidden): ")
    os.environ["KORAIL_CARD_EXPIRE"] = getpass.getpass("expiry YYMM (hidden): ")
    os.environ["KORAIL_CARD_BIRTHDAY"] = getpass.getpass("birth YYMMDD (hidden): ")
    card = operator.read_card_from_env()
    console = RedactedConsole(operator._console_for(card))
    client = KorailClient(KorailConfig(enable_dynapath=True))
    operator._install_pacing(client, operator._Pacer(1.5))
    args = argparse.Namespace(date=operator._default_date(), min_interval=1.5)
    trip = RecipientRoundTrip(client, console, card, args)
    try:
        return trip.run()
    except Exception as exc:
        console.say(
            f"round_trip: {type(exc).__name__} "
            f"code={getattr(exc, 'code', None)} state={trip.state}"
        )
        if trip.state in {"paid", "paying", "unpaid"} and trip.pnr_no:
            try:
                console.say("attempting immediate paid-ticket recovery")
                operator.recover(client, console, trip.pnr_no)
            except Exception as recovery_exc:
                console.say(
                    f"recovery: {type(recovery_exc).__name__} "
                    f"code={getattr(recovery_exc, 'code', None)}"
                )
        return 1
    finally:
        try:
            client.logout()
        except Exception:
            console.say("logout: failed")
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
