# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Retry the delivery-recipient read on a fresh paid ticket, then refund it.

This wrapper reuses the established bounded round-trip operator and prompts all
credentials in memory. It prints through the operator's own console, so the card
values are scrubbed by exact value and the PNR is printed in full: a digit-run
mask would hide the 15-digit PNR a stranded paid ticket is recovered with (see
``_Console`` in ``reserve_pay_refund_roundtrip.py``).
"""

from __future__ import annotations

import argparse
import getpass
import os

import reserve_pay_refund_roundtrip as operator
from korail_mobile_api import KorailClient, OriginalTicketReference


class RecipientRoundTrip(operator.RoundTrip):
    def quote_refund(self, reference: OriginalTicketReference) -> str | None:
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
        return super().quote_refund(reference)


def main() -> int:
    # This script always runs under a 5,000 won ceiling. The parent's gate
    # refuses the charging path unless a ceiling is set, so it goes in first.
    os.environ[operator.MAX_FARE_ENV] = "5000"
    try:
        # The parent's own gate, not a copy of it: a safeguard added there
        # applies here too. The device identity comes from the environment the
        # same way, so the real-card run is made from a stable device rather
        # than a new synthetic one each time. Both fail before any secret is
        # asked for.
        operator._require_opt_ins(real_charge=True)
        config = operator.build_config_from_env()
    except (operator.RoundTripAborted, RuntimeError) as exc:
        print(f"ABORTED: {exc}")
        return 2
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
    console = operator._console_for(card)
    client = KorailClient(config)
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
