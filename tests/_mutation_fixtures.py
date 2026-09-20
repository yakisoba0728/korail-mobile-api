# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""Value factories the mutation test files share: a bookable train and a test card.

Plain functions, not fixtures: test_mutation_payloads calls them inside
@pytest.mark.parametrize, at collection time. Only values that were identical
in every file using them live here.

The paid hold and paid ticket take the PNR as a required argument. Each file
checks that a preview does not leak "its" PNR; a shared default PNR could
drift away from the one a file looks for, and that check would then pass
without looking at anything.
"""

from __future__ import annotations

from korail_mobile_api import TrainSummary
from korail_mobile_api.mutation_models import (
    CardPayment,
    PaidTicket,
    ReservationHoldResponse,
    ReservationJourney,
)


def eligible_train() -> TrainSummary:
    """A general seat evidenced as available (general_reservation_code == "11")."""
    return TrainSummary(
        train_no="00209",
        train_group_code="100",
        departure_station_code="0001",
        arrival_station_code="0501",
        departure_date="20990101",
        departure_time="100700",
        arrival_time="102400",
        run_date="20990101",
        train_class_code="00",
        departure_run_order="1",
        arrival_run_order="2",
        general_reservation_code="11",
        departure_construction_order="1",
        arrival_construction_order="2",
        seat_attribute_code="015",
    )


def fake_card() -> CardPayment:
    """A non-chargeable test card: all-zero number, a PG declines it."""
    return CardPayment(
        card_number="0000000000000000",
        card_password="00",
        card_expire="2612",
        birthday="900101",
    )


def paid_hold(pnr_no: str) -> ReservationHoldResponse:
    """An unpaid hold ready for payment, carrying ``pnr_no``."""
    return ReservationHoldResponse(
        h_msg_cd="IRR000018",
        h_msg_txt="ok",
        str_result="SUCC",
        raw={},
        pnr_no=pnr_no,
        journey_count="0001",
        window_no="SYNTHETIC_WCT",
        temporary_job_sequence_1="SYNTHETIC_JOB_1",
        temporary_job_sequence_2="SYNTHETIC_JOB_2",
        total_price="8400",
        received_amount="7560",
        # Deliberately NOT "000": a builder that regressed to the constant would
        # otherwise pass against a fixture whose value happened to match the
        # fallback.
        journeys=(
            ReservationJourney(
                journey_sequence="0001",
                reservation_change_no="SYNTHETIC_CHG_NO",
            ),
        ),
    )


def paid_ticket(pnr_no: str) -> PaidTicket:
    """A paid ticket's refund identity, carrying ``pnr_no``."""
    return PaidTicket(
        pnr_no=pnr_no,
        sale_date="20260725",
        sale_window_no="SYNTHETIC_WCT",
        sale_sequence="0001",
        return_password="SYNTHETIC_RETPWD",
        train_no="00209",
    )
