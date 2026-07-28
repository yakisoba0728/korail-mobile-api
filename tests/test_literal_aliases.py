"""Every exported ``Literal`` alias must still name exactly the values the
runtime accepts.

A ``Literal`` alias is a hand-written copy of a set that lives somewhere else —
a frozenset a builder validates against, or the ``allow_*`` flag table a consent
gate reads. Copies drift, and a drifted alias is worse than no alias: the type
checker starts refusing a value the library itself accepts, so the caller's only
escape is ``# type: ignore``. Each test below pins one alias to the runtime
structure that decides the same question, so widening one without the other
fails here.
"""

from typing import get_args

from korail_mobile_api.consent import _CONSENT_FLAG_BY_CATEGORY, MutationCategory
from korail_mobile_api.read_payloads import (
    _KORAIL_MILEAGE_LEDGERS,
    _KORAIL_MILEAGE_MOVEMENTS,
    SELF_SEAT_CHANGE_ROOM_CLASS_CODES,
    KorailMileageLedger,
    KorailMileageMovement,
    KorailSelfSeatChangeRoomClassCode,
)


def test_mileage_ledger_alias_matches_the_validated_set():
    assert set(get_args(KorailMileageLedger)) == _KORAIL_MILEAGE_LEDGERS


def test_mileage_movement_alias_matches_the_validated_set():
    assert set(get_args(KorailMileageMovement)) == _KORAIL_MILEAGE_MOVEMENTS


def test_self_seat_change_room_class_alias_matches_the_validated_set():
    assert (
        set(get_args(KorailSelfSeatChangeRoomClassCode))
        == SELF_SEAT_CHANGE_ROOM_CLASS_CODES
    )


def test_mutation_category_alias_matches_the_consent_flag_table():
    assert set(get_args(MutationCategory)) == set(_CONSENT_FLAG_BY_CATEGORY)
