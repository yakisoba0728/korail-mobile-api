"""The 승차권 여행변경 chain: tripChgPrsC / tripChgHndgCnc / reservationChange.

Three routes, one consent category, and eleven ``@FieldMap``s between them.
Everything asserted here is pinned to the decompiled app; the ``file:line``
references live in the builders' own docstrings.
"""

from __future__ import annotations

from urllib.parse import parse_qsl

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.consent import (
    MUTATION_CATEGORIES,
    MutationConsent,
    MutationPreview,
    require_mutation_consent,
)
from korail_mobile_api.errors import (
    KorailAuthError,
    KorailProtocolError,
    MutationNotAllowedError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.mutation_models import (
    KorailPassengerCounts,
    ReservationHoldResponse,
    ReservationPassengerChangeLeg,
    ReservationPassengerChangeRequest,
    ReservationPassengerChangeResponse,
    TripChangeDiscount,
    TripChangeLeg,
    TripChangeOriginalTicket,
    TripChangePassenger,
    TripChangeReservationRequest,
    TripChangeSeatAssignment,
)
from korail_mobile_api.mutation_parsers import (
    parse_reservation_passenger_change_response,
)
from korail_mobile_api.mutation_payloads import (
    build_reservation_passenger_change_form,
    build_trip_change_reservation_form,
    build_trip_change_rollback_form,
)
from korail_mobile_api.redaction import SENSITIVE_KEYS, redact_payload
from korail_mobile_api.safety import (
    KORAIL_CARD_BEARING_MUTATION_CATEGORIES,
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


CHANGE_ROUTE = "/classes/com.korail.mobile.reservation.tripChgPrsC.do"
ROLLBACK_ROUTE = "/classes/com.korail.mobile.ticket.tripChgHndgCnc.do"
PASSENGER_ROUTE = (
    "/classes/com.korail.mobile.reservation.reservationChange.do"
)
TICKET_CHANGE_ROUTES = (CHANGE_ROUTE, ROLLBACK_ROUTE, PASSENGER_ROUTE)

OTHER_CATEGORIES = (
    "reserve",
    "payment",
    "cancel",
    "refund",
    "discount_card",
    "price_recalculation",
)
OTHER_FLAGS = (
    "allow_reserve",
    "allow_payment",
    "allow_cancel",
    "allow_refund",
    "allow_discount_card",
    "allow_price_recalculation",
)

ALLOWED = MutationConsent(allow_ticket_change=True, dry_run=False)
DRY_RUN = MutationConsent(allow_ticket_change=True)


def _ticket(index: int = 1) -> TripChangeOriginalTicket:
    return TripChangeOriginalTicket(
        sale_window_no=f"SYNTHETIC_WCT_{index}",
        sale_date="20990101",
        sale_sequence=f"SYNTHETIC_SQNO_{index}",
        return_password=f"SYNTHETIC_PWD_{index}",
    )


def _leg(**overrides: object) -> TripChangeLeg:
    fields: dict[str, object] = {
        "train_no": "101",
        "run_date": "20990101",
        "train_classification_code": "00",
        "train_group_code": "100",
        "departure_date": "20990101",
        "departure_time": "080000",
        "departure_station_code": "0001",
        "departure_station_consecutive_order": "000000",
        "departure_station_run_order": "000001",
        "arrival_date": "20990101",
        "arrival_time": "100000",
        "arrival_station_code": "0020",
        "arrival_station_consecutive_order": "000010",
        "arrival_station_run_order": "000011",
    }
    fields.update(overrides)
    return TripChangeLeg(**fields)  # type: ignore[arg-type]


def _request(**overrides: object) -> TripChangeReservationRequest:
    fields: dict[str, object] = {
        "original_tickets": (_ticket(),),
        "legs": (_leg(),),
        "passengers": (TripChangePassenger(),),
    }
    fields.update(overrides)
    return TripChangeReservationRequest(**fields)  # type: ignore[arg-type]


def _passenger_leg(**overrides: object) -> ReservationPassengerChangeLeg:
    fields: dict[str, object] = {
        "journey_sequence_no": "0001",
        "journey_type_code": "11",
        "train_no": "101",
        "departure_date": "20990101",
        "train_classification_code": "00",
        "train_group_code": "100",
        "departure_time": "080000",
        "departure_station_code": "0001",
        "departure_station_consecutive_order": "000000",
        "arrival_station_code": "0020",
        "arrival_station_consecutive_order": "000010",
    }
    fields.update(overrides)
    return ReservationPassengerChangeLeg(**fields)  # type: ignore[arg-type]


def _passenger_request(
    **overrides: object,
) -> ReservationPassengerChangeRequest:
    fields: dict[str, object] = {
        "pnr_no": "SYNTHETIC_PNR",
        "reservation_change_no": "SYNTHETIC_CHG_TNO",
        "journey_count": "1",
        "legs": (_passenger_leg(),),
        "passengers": KorailPassengerCounts(adult=1),
    }
    fields.update(overrides)
    return ReservationPassengerChangeRequest(**fields)  # type: ignore[arg-type]


def _client(handler) -> KorailClient:
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(
        jsessionid="SYNTHETIC_SESSION",
        member_no="SYNTHETIC_MEMBER_NO",
        customer_no="SYNTHETIC_CUSTOMER_NO",
        raw={},
    )
    return client


def _refuse(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"nothing may be sent: {request.method} {request.url}")


# --- consent category -------------------------------------------------------


def test_ticket_change_is_its_own_consent_category():
    assert "ticket_change" in MUTATION_CATEGORIES
    assert len(MUTATION_CATEGORIES) == 7
    # A default consent grants it nothing.
    assert MutationConsent().allow_ticket_change is False
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(MutationConsent(), "ticket_change")
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(None, "ticket_change")
    # ...and no other category's opt-in unlocks it. allow_reserve is the one
    # that matters: a 여행변경 stakes an already-paid ticket, which is not
    # what "I want to hold a seat" authorises.
    for other in OTHER_FLAGS:
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(**{other: True}),
                "ticket_change",
            )
    require_mutation_consent(
        MutationConsent(allow_ticket_change=True),
        "ticket_change",
    )
    # ...and it unlocks nothing else.
    for category in OTHER_CATEGORIES:
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(allow_ticket_change=True),
                category,
            )


def test_the_rollback_shares_the_category_it_undoes():
    # The design decision, asserted rather than commented: one flag opens the
    # change AND its rollback, so a caller who made a change can always unmake
    # it. A separate flag would strand a paid ticket half-changed.
    consent = MutationConsent(allow_ticket_change=True)
    require_mutation_consent(consent, "ticket_change")
    assert (
        KORAIL_MUTATION_ROUTE_CATEGORIES[CHANGE_ROUTE]
        == KORAIL_MUTATION_ROUTE_CATEGORIES[ROLLBACK_ROUTE]
        == "ticket_change"
    )


def test_routes_are_mutation_routes_owned_by_that_category():
    assert len(KORAIL_MUTATION_ROUTES) == 11
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)
    for route in TICKET_CHANGE_ROUTES:
        assert ("POST", route) in KORAIL_MUTATION_ROUTES
        assert ("GET", route) not in KORAIL_MUTATION_ROUTES
        assert KORAIL_MUTATION_ROUTE_CATEGORIES[route] == "ticket_change"
        assert_mutation_route("POST", route)
        assert_mutation_route_category(route, "ticket_change")
        # Neither direction of the binding may be crossed: another category
        # cannot reach this route...
        for wrong in OTHER_CATEGORIES:
            with pytest.raises(KorailProtocolError):
                assert_mutation_route_category(route, wrong)
        # ...and the read-only guarantee stays intact.
        assert ("POST", route) not in KORAIL_READ_ONLY_ROUTES
        with pytest.raises(KorailProtocolError):
            assert_read_only_route("POST", route)


def test_ticket_change_reaches_no_other_categorys_route():
    # The other direction of the binding: a ticket_change consent cannot be
    # redirected onto a route it does not own.
    for route, category in KORAIL_MUTATION_ROUTE_CATEGORIES.items():
        if category == "ticket_change":
            continue
        with pytest.raises(KorailProtocolError):
            assert_mutation_route_category(route, "ticket_change")


def test_category_carries_no_card_and_never_reaches_the_card_gate():
    # None of the three forms carries a PAN: the settlement that follows a
    # change is a separate payment call. Registering the category as
    # card-bearing would make the payment gate demand a card kind it has no
    # card for.
    assert "ticket_change" not in KORAIL_CARD_BEARING_MUTATION_CATEGORIES
    assert KORAIL_CARD_BEARING_MUTATION_CATEGORIES <= set(MUTATION_CATEGORIES)


# --- tripChgPrsC.do: the fifteen scalars ------------------------------------


_TRIP_CHANGE_SCALARS = (
    "Device",
    "Version",
    "Key",
    "trvlKndCd",
    "totPrnb",
    "isePrnb",
    "stndSeatFlg",
    "intgTktIseFlg",
    "prcFareReCalcFlg",
    "alcSeatDmnPsDvCd",
    "jrny2Cnt",
    "psg2Cnt",
)


def test_first_call_sends_the_twelve_scalars_retrofit_would_send():
    form = build_trip_change_reservation_form(KorailConfig(), _request())
    # tmpJobSqno / ctlDvCd / frcSaleRsnCont are null on this path and Retrofit
    # DROPS a null @Field rather than sending it empty.
    for absent in ("tmpJobSqno", "ctlDvCd", "frcSaleRsnCont"):
        assert absent not in form
    assert form["trvlKndCd"] == "1"
    assert form["totPrnb"] == "1"
    assert form["isePrnb"] == "1"
    assert form["stndSeatFlg"] == "N"
    assert form["intgTktIseFlg"] == "N"
    assert form["prcFareReCalcFlg"] == "N"
    assert form["alcSeatDmnPsDvCd"] == "000"
    assert form["jrny2Cnt"] == "0000"
    assert form["psg2Cnt"] == "0000"
    assert set(_TRIP_CHANGE_SCALARS) <= set(form)


def test_totprnb_counts_original_tickets_and_psgcnt_counts_passengers():
    # w4/b.java:136-137 uses orgTkList.size() for both totPrnb and isePrnb
    # while :175 uses the picker's total for psgCnt. They differ whenever a
    # 동반유아 joins, and conflating them would misprice the change.
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(
            original_tickets=(_ticket(1),),
            passengers=(
                TripChangePassenger(),
                TripChangePassenger(passenger_type_code="3"),
            ),
        ),
    )
    assert form["totPrnb"] == "1"
    assert form["isePrnb"] == "1"
    assert form["psgCnt"] == "2"


def test_the_reprice_call_adds_the_pnr_and_flips_one_flag():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(
            recalculate_fare=True,
            temporary_job_sequence="SYNTHETIC_TMP_PNR",
        ),
    )
    assert form["prcFareReCalcFlg"] == "Y"
    assert form["tmpJobSqno"] == "SYNTHETIC_TMP_PNR"


def test_the_two_reprice_halves_cannot_be_sent_apart():
    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(
            KorailConfig(),
            _request(recalculate_fare=True),
        )
    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(
            KorailConfig(),
            _request(temporary_job_sequence="SYNTHETIC_TMP_PNR"),
        )


def test_the_start_station_scalars_are_added_but_select_no_other_shape():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(control_division_code="3584", forced_sale_reason="01"),
    )
    assert form["ctlDvCd"] == "3584"
    assert form["frcSaleRsnCont"] == "01"
    # ...and the rest of the form is unchanged. 발상역 변경 is NOT implemented:
    # that path writes jrnyTpCd "21"/"22" (K4/e STANDING_SEAT_1/2), takes its
    # station orders off a StartStationDto, and indexes RSrcar off a train
    # rather than a leg. These two scalars do not switch any of that on, and
    # this test exists so nobody later mistakes them for a mode selector.
    assert form["jrnyTpCd_1"] == "11"
    plain = build_trip_change_reservation_form(KorailConfig(), _request())
    assert {
        name: value
        for name, value in form.items()
        if name not in {"ctlDvCd", "frcSaleRsnCont"}
    } == plain


# --- tripChgPrsC.do: the six FieldMaps --------------------------------------


def test_the_six_fieldmaps_are_emitted_in_executedao_order():
    # TCReservationDao.executeDao:222 passes RJrny, RSrcar, RSeat, RPsg,
    # ROrtg, RDscp -- in that order, which the form's insertion order keeps.
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(seats=(TripChangeSeatAssignment(leg=1, car_no="3", seat_no="5A"),)),
    )
    names = list(form)
    order = [
        names.index("jrnyCnt"),  # RJrny
        names.index("srcarCnt_1"),  # RSrcar
        names.index("seatCnt_1"),  # RSeat
        names.index("psgCnt"),  # RPsg
        names.index("ortgCnt"),  # ROrtg
        names.index("dscpCnt_1"),  # RDscp
    ]
    assert order == sorted(order)
    # ...and the scalars all precede the first map key.
    assert max(names.index(name) for name in _TRIP_CHANGE_SCALARS) < order[0]


def test_rjrny_expands_one_row_per_leg_with_the_derived_keys():
    form = build_trip_change_reservation_form(KorailConfig(), _request())
    assert form["jrnyCnt"] == "0001"
    assert form["jrnySqno_1"] == "0001"
    assert form["jrnyTpCd_1"] == "11"
    # trnNo is zero-padded to five (N.addZero(5, ...)), the count to four.
    assert form["trnNo_1"] == "00101"
    assert form["runDt_1"] == "20990101"
    assert form["stlbTrnClsfCd_1"] == "00"
    assert form["trnGpCd_1"] == "100"
    assert form["dptDt_1"] == "20990101"
    assert form["dptTm_1"] == "080000"
    assert form["dptRsStnCd_1"] == "0001"
    assert form["dptStnConsOrdr_1"] == "000000"
    assert form["dptStnRunOrdr_1"] == "000001"
    assert form["arvDt_1"] == "20990101"
    assert form["arvTm_1"] == "100000"
    assert form["arvRsStnCd_1"] == "0020"
    assert form["arvStnConsOrdr_1"] == "000010"
    assert form["arvStnRunOrdr_1"] == "000011"
    # chgFlg_ is declared on RJrny and written by nobody.
    assert not [name for name in form if name.startswith("chgFlg_")]


def test_a_transfer_makes_both_legs_type_14_and_renumbers_the_sequence():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(legs=(_leg(), _leg(train_no="202"))),
    )
    assert form["jrnyCnt"] == "0002"
    assert form["jrnySqno_1"] == "0001"
    assert form["jrnySqno_2"] == "0002"
    # The journey type is per REQUEST, not per leg: C5/d.java:52 asks how many
    # trains were selected, not which one this is.
    assert form["jrnyTpCd_1"] == "14"
    assert form["jrnyTpCd_2"] == "14"
    assert form["trnNo_2"] == "00202"


def test_rseat_carries_the_overwritten_count_and_the_four_option_codes():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(legs=(_leg(), _leg(train_no="202", room_class_code="2"))),
    )
    # seatCnt_N is written twice by the app; C5/d.java:69 wins, so it is a
    # zero-padded LEG COUNT, not the "1"/"2" w4/b.java:164 wrote first.
    assert form["seatCnt_1"] == "0002"
    assert form["seatCnt_2"] == "0002"
    for index in (1, 2):
        assert form[f"smkSeatAttCd_{index}_1"] == "000"
        assert form[f"dirSeatAttCd_{index}_1"] == "000"
        assert form[f"locSeatAttCd_{index}_1"] == "000"
        assert form[f"etcSeatAttCd_{index}_1"] == "000"
        assert form[f"rqSeatAttCd_{index}_1"] == "015"
    assert form["roomClsfCd_1_1"] == "1"
    assert form["roomClsfCd_2_1"] == "2"
    # seatPsrmClCd_ belongs to the OTHER trip-change route, not this one.
    assert not [name for name in form if name.startswith("seatPsrmClCd_")]


def test_rseat_key_order_survives_the_two_builders_re_putting_into_it():
    # RSeat is the one map two files write, and a LinkedHashMap re-put keeps
    # the key's FIRST position. So of C5/d.java's three writes per leg, only
    # roomClsfCd_ is a new key: seatCnt_ and rqSeatAttCd_ land back where
    # w4/b.java:164,168 first put them. Emitting in call order instead of
    # insertion order would put rqSeatAttCd_ after etcSeatAttCd_ and
    # interleave roomClsfCd_ per leg, neither of which is what goes out.
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(legs=(_leg(), _leg(train_no="202"))),
    )
    names = list(form)
    seat_block = names[names.index("seatCnt_1") : names.index("psgCnt")]
    assert seat_block == [
        "seatCnt_1",
        "smkSeatAttCd_1_1",
        "dirSeatAttCd_1_1",
        "locSeatAttCd_1_1",
        "rqSeatAttCd_1_1",
        "etcSeatAttCd_1_1",
        "seatCnt_2",
        "smkSeatAttCd_2_1",
        "dirSeatAttCd_2_1",
        "locSeatAttCd_2_1",
        "rqSeatAttCd_2_1",
        "etcSeatAttCd_2_1",
        "roomClsfCd_1_1",
        "roomClsfCd_2_1",
    ]


def test_rsrcar_is_empty_unless_seats_were_picked():
    form = build_trip_change_reservation_form(KorailConfig(), _request())
    assert not [
        name
        for name in form
        if name.startswith(("srcarCnt_", "scarCnt_", "scarNo_", "seatNo_"))
    ]


def test_rsrcar_uses_the_srcar_count_spelling_and_two_indices():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(
            legs=(_leg(), _leg(train_no="202")),
            seats=(
                TripChangeSeatAssignment(leg=1, car_no="3", seat_no="5A"),
                TripChangeSeatAssignment(leg=1, car_no="3", seat_no="6A"),
                TripChangeSeatAssignment(leg=2, car_no="7", seat_no="1B"),
            ),
        ),
    )
    # srcarCnt_, NOT scarCnt_ (SeatSearchActivity.java:660 takes the else
    # branch for TYPE_TCRR_RIR); and setSrcarNo writes scarNo_.
    assert form["srcarCnt_1"] == "2"
    assert form["srcarCnt_2"] == "1"
    assert "scarCnt_1" not in form
    assert "srcarNo_1_1" not in form
    assert form["scarNo_1_1"] == "3"
    assert form["seatNo_1_2"] == "6A"
    assert form["scarNo_2_1"] == "7"


def test_a_seat_on_a_leg_that_is_not_in_the_request_is_refused():
    for leg in (0, 2, "1"):
        with pytest.raises(KorailProtocolError):
            build_trip_change_reservation_form(
                KorailConfig(),
                _request(
                    seats=(
                        TripChangeSeatAssignment(
                            leg=leg,  # type: ignore[arg-type]
                            car_no="3",
                            seat_no="5A",
                        ),
                    )
                ),
            )


def test_rpsg_is_one_row_per_passenger_and_keeps_the_callers_order():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(
            original_tickets=(_ticket(1), _ticket(2)),
            passengers=(
                TripChangePassenger(passenger_type_code="1"),
                TripChangePassenger(passenger_type_code="3"),
            ),
        ),
    )
    assert form["psgCnt"] == "2"
    assert form["psgInfoPerPrnb_1"] == "1"
    assert form["psgInfoPerPrnb_2"] == "1"
    assert form["psgTpDvCd_1"] == "1"
    assert form["psgTpDvCd_2"] == "3"


def test_rortg_is_one_row_per_original_ticket_one_based():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(original_tickets=(_ticket(1), _ticket(2))),
    )
    assert form["ortgCnt"] == "0002"
    assert form["ogtkSaleWctNo_1"] == "SYNTHETIC_WCT_1"
    assert form["ogtkSaleDd_1"] == "20990101"
    assert form["ogtkSaleSqno_1"] == "SYNTHETIC_SQNO_1"
    assert form["ogtkRetPwd_1"] == "SYNTHETIC_PWD_1"
    assert form["retNoMnlInpFlg_1"] == "N"
    assert form["ogtkSaleWctNo_2"] == "SYNTHETIC_WCT_2"
    assert "ogtkSaleWctNo_0" not in form
    # cmtrDvCd_ is declared on ROrtg and written by nobody.
    assert not [name for name in form if name.startswith("cmtrDvCd_")]


def test_rdscp_always_sends_a_zero_padded_count_even_at_zero():
    form = build_trip_change_reservation_form(KorailConfig(), _request())
    assert form["dscpCnt_1"] == "0000"
    assert not [name for name in form if name.startswith("dcntKndCd_")]


def test_rdscp_rows_use_both_indices_and_pad_the_count():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(
            passengers=(
                TripChangePassenger(
                    discounts=(
                        TripChangeDiscount(
                            discount_kind_code="131",
                        ),
                        TripChangeDiscount(
                            discount_kind_code="151",
                            certificate_no="SYNTHETIC_COUPON",
                        ),
                    )
                ),
                TripChangePassenger(),
            ),
        ),
    )
    assert form["dscpCnt_1"] == "0002"
    assert form["dcntKndCd_1_1"] == "131"
    # A discount with no certificate sends no dscpNo key at all.
    assert "dscpNo_1_1" not in form
    assert form["dcntKndCd_1_2"] == "151"
    assert form["dscpNo_1_2"] == "SYNTHETIC_COUPON"
    assert form["dscpCnt_2"] == "0000"


def test_a_delay_certificate_sends_its_whole_return_number_or_is_refused():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(
            passengers=(
                TripChangePassenger(
                    discounts=(
                        TripChangeDiscount(
                            discount_kind_code="401",
                            delay_window_no="SYNTHETIC_DLY_WCT",
                            delay_sale_date="20990101",
                            delay_sale_sequence="SYNTHETIC_DLY_SQNO",
                            delay_return_password="SYNTHETIC_DLY_PWD",
                        ),
                    )
                ),
            ),
        ),
    )
    assert form["dcntKndCd_1_1"] == "401"
    assert form["dlayOgtkWctNo_1_1"] == "SYNTHETIC_DLY_WCT"
    assert form["dlayOgtkSaleDd_1_1"] == "20990101"
    assert form["dlayOgtkSaleSqno_1_1"] == "SYNTHETIC_DLY_SQNO"
    assert form["dlayOgtkRetPwd_1_1"] == "SYNTHETIC_DLY_PWD"

    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(
            KorailConfig(),
            _request(
                passengers=(
                    TripChangePassenger(
                        discounts=(
                            TripChangeDiscount(
                                discount_kind_code="401",
                                delay_window_no="SYNTHETIC_DLY_WCT",
                            ),
                        )
                    ),
                ),
            ),
        )


def test_the_builder_refuses_a_foreign_or_empty_request():
    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(KorailConfig(), object())  # type: ignore[arg-type]
    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(
            KorailConfig(), _request(original_tickets=())
        )
    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(KorailConfig(), _request(legs=()))
    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(
            KorailConfig(), _request(passengers=())
        )
    # Three legs is more than any itinerary the app can express.
    with pytest.raises(KorailProtocolError):
        build_trip_change_reservation_form(
            KorailConfig(), _request(legs=(_leg(), _leg(), _leg()))
        )


# --- tripChgHndgCnc.do ------------------------------------------------------


def test_rollback_form_is_the_count_and_a_one_based_map():
    form = build_trip_change_rollback_form(
        KorailConfig(),
        ("SYNTHETIC_LUMP_1",),
    )
    assert set(form) == {
        "Device",
        "Version",
        "Key",
        "lumpStlCnt",
        "lumpStlTgtNo_1",
    }
    assert form["lumpStlCnt"] == "1"
    assert form["lumpStlTgtNo_1"] == "SYNTHETIC_LUMP_1"
    assert "lumpStlTgtNo_0" not in form


def test_rollback_count_is_derived_from_the_map_it_describes():
    form = build_trip_change_rollback_form(
        KorailConfig(),
        ("SYNTHETIC_LUMP_1", "SYNTHETIC_LUMP_2"),
    )
    assert form["lumpStlCnt"] == "2"
    assert form["lumpStlTgtNo_2"] == "SYNTHETIC_LUMP_2"


def test_rollback_refuses_an_empty_or_blank_target_list():
    with pytest.raises(KorailProtocolError):
        build_trip_change_rollback_form(KorailConfig(), ())
    with pytest.raises(KorailProtocolError):
        build_trip_change_rollback_form(KorailConfig(), ("",))


# --- reservationChange.do ---------------------------------------------------


def test_passenger_change_sends_the_ten_scalars_and_pins_four_flags():
    form = build_reservation_passenger_change_form(
        KorailConfig(), _passenger_request()
    )
    assert form["pnrNo"] == "SYNTHETIC_PNR"
    assert form["chgTno"] == "SYNTHETIC_CHG_TNO"
    assert form["totPrnb"] == "1"
    assert form["stndFlg"] == "N"
    assert form["evntWctFlg"] == "N"
    assert form["wctHndgCncDvCd"] == "N"
    assert form["lrgCrgFlg"] == "N"


def test_psgcnt_reaches_the_wire_exactly_once_from_the_map():
    # The eleventh @Field is literally @Field("psgCnt") and would collide with
    # RPsg's own key -- except that setPsgCnt on the REQUEST has no call site
    # in v6.5.0, so the scalar is null and Retrofit drops it. A dict cannot
    # hold the key twice; what this pins is that the one occurrence sits in the
    # map's position, after the RSeat block, not among the leading scalars.
    form = build_reservation_passenger_change_form(
        KorailConfig(), _passenger_request()
    )
    names = list(form)
    assert names.count("psgCnt") == 1
    assert names.index("psgCnt") > names.index("seatCnt_1")
    assert names.index("psgCnt") > names.index("lrgCrgFlg")


def test_passenger_change_five_fieldmaps_are_emitted_in_executedao_order():
    # ReservationChangeDao.executeDao:166 passes RJrny, RSrcar, RSeat, RPsg,
    # RDscp. ROrtg is absent: this route stakes no 원표.
    form = build_reservation_passenger_change_form(
        KorailConfig(), _passenger_request()
    )
    names = list(form)
    order = [
        names.index("jrnyCnt"),
        names.index("scarCnt_1"),
        names.index("seatCnt_1"),
        names.index("psgCnt"),
        names.index("dscpCnt_1"),
    ]
    assert order == sorted(order)
    assert "ortgCnt" not in form
    assert not [name for name in form if name.startswith("ogtk")]


def test_passenger_change_rjrny_echoes_the_hold_and_omits_four_keys():
    form = build_reservation_passenger_change_form(
        KorailConfig(), _passenger_request()
    )
    # jrnyCnt is echoed from h_jrny_cnt, NOT zero-padded the way the other
    # trip-change route pads it.
    assert form["jrnyCnt"] == "1"
    assert form["jrnySqno_1"] == "0001"
    assert form["jrnyTpCd_1"] == "11"
    assert form["trnNo_1"] == "00101"
    # runDt_ is the DEPARTURE date here: w4/a.java:145 passes getH_dpt_dt().
    assert form["runDt_1"] == form["dptDt_1"] == "20990101"
    for absent in (
        "dptStnRunOrdr_1",
        "arvDt_1",
        "arvTm_1",
        "arvStnRunOrdr_1",
    ):
        assert absent not in form


def test_passenger_change_uses_the_other_spelling_of_both_seat_keys():
    form = build_reservation_passenger_change_form(
        KorailConfig(), _passenger_request()
    )
    # scarCnt_, not srcarCnt_ -- and always "0".
    assert form["scarCnt_1"] == "0"
    assert "srcarCnt_1" not in form
    # seatPsrmClCd_, not roomClsfCd_.
    assert form["seatCnt_1"] == "1"
    assert form["seatPsrmClCd_1_1"] == "1"
    assert form["rqSeatAttCd_1_1"] == "015"
    assert "roomClsfCd_1_1" not in form


def test_passenger_change_walks_the_six_counters_in_the_apps_order():
    form = build_reservation_passenger_change_form(
        KorailConfig(),
        _passenger_request(
            passengers=KorailPassengerCounts(
                adult=1,
                child=1,
                infant=1,
                senior=1,
                severe_disability=1,
                mild_disability=1,
            ),
        ),
    )
    assert form["totPrnb"] == "6"
    assert form["psgCnt"] == "6"
    # 어른 → 어린이 → 동반유아 → 경로 → 1~3급 → 4~6급 (w4/a.java:164-235).
    assert [form[f"psgTpDvCd_{i}"] for i in range(1, 7)] == [
        "1",
        "3",
        "3",
        "1",
        "1",
        "1",
    ]
    # The RDscp counts here are bare, not zero-padded: w4/a.java writes the
    # literal strings "0" and "1".
    assert [form[f"dscpCnt_{i}"] for i in range(1, 7)] == [
        "0",
        "0",
        "1",
        "1",
        "1",
        "1",
    ]
    assert "dcntKndCd_1_1" not in form
    assert "dcntKndCd_2_1" not in form
    assert form["dcntKndCd_3_1"] == "321"
    assert form["dcntKndCd_4_1"] == "131"
    assert form["dcntKndCd_5_1"] == "111"
    assert form["dcntKndCd_6_1"] == "112"


def test_passenger_change_refuses_the_two_counters_the_app_ignores():
    # w4/a.java reads six of the eight counters; a mix with 청소년 or 안내견
    # would send a totPrnb that does not match the rows.
    for counts in (
        KorailPassengerCounts(adult=1, teenager=1),
        KorailPassengerCounts(adult=1, guide_dog=1),
    ):
        with pytest.raises(KorailProtocolError):
            build_reservation_passenger_change_form(
                KorailConfig(),
                _passenger_request(passengers=counts),
            )


def test_passenger_change_refuses_a_foreign_or_empty_request():
    with pytest.raises(KorailProtocolError):
        build_reservation_passenger_change_form(KorailConfig(), object())  # type: ignore[arg-type]
    with pytest.raises(KorailProtocolError):
        build_reservation_passenger_change_form(
            KorailConfig(), _passenger_request(legs=())
        )
    with pytest.raises(KorailProtocolError):
        build_reservation_passenger_change_form(
            KorailConfig(), _passenger_request(journey_count="")
        )


def test_passenger_change_response_parses_the_settlement_targets():
    parsed = parse_reservation_passenger_change_response(
        {
            "h_msg_cd": "IRG000000",
            "h_msg_txt": "정상처리되었습니다",
            "strResult": "SUCC",
            "jrnyList": [
                {"lumpStlTgtNo": "SYNTHETIC_LUMP_1"},
                {"lumpStlTgtNo": "SYNTHETIC_LUMP_2"},
            ],
        }
    )
    assert type(parsed) is ReservationPassengerChangeResponse
    assert parsed.lump_settlement_target_nos == (
        "SYNTHETIC_LUMP_1",
        "SYNTHETIC_LUMP_2",
    )
    # The handle is a secret and stays out of the repr.
    assert "SYNTHETIC_LUMP_1" not in repr(parsed)


def test_passenger_change_response_without_a_settlement_target_is_refused():
    for raw in (
        {"h_msg_cd": "IRG000000", "strResult": "SUCC"},
        {"h_msg_cd": "IRG000000", "strResult": "SUCC", "jrnyList": []},
        {"h_msg_cd": "IRG000000", "strResult": "SUCC", "jrnyList": [{}]},
    ):
        with pytest.raises(KorailProtocolError):
            parse_reservation_passenger_change_response(raw)


# --- redaction --------------------------------------------------------------


def test_every_identity_key_these_forms_add_is_registered_as_sensitive():
    for key in (
        "ogtkSaleWctNo",
        "ogtkSaleDd",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "tmpJobSqno",
        "chgTno",
        "lumpStlTgtNo",
        "pnrNo",
        "scarNo_1_1",
        "seatNo_1_1",
        "dscpNo_1_1",
        "dlayOgtkRetPwd_1_1",
    ):
        assert key.casefold() in SENSITIVE_KEYS


def test_the_preview_of_a_change_leaks_no_return_number():
    form = build_trip_change_reservation_form(
        KorailConfig(),
        _request(
            recalculate_fare=True,
            temporary_job_sequence="SYNTHETIC_TMP_PNR",
            seats=(TripChangeSeatAssignment(leg=1, car_no="3", seat_no="5A"),),
            passengers=(
                TripChangePassenger(
                    discounts=(
                        TripChangeDiscount(
                            discount_kind_code="401",
                            certificate_no="SYNTHETIC_COUPON",
                            delay_window_no="SYNTHETIC_DLY_WCT",
                            delay_sale_date="20990101",
                            delay_sale_sequence="SYNTHETIC_DLY_SQNO",
                            delay_return_password="SYNTHETIC_DLY_PWD",
                        ),
                    )
                ),
            ),
        ),
    )
    rendered = str(redact_payload(form))
    for secret in (
        "SYNTHETIC_WCT_1",
        "SYNTHETIC_SQNO_1",
        "SYNTHETIC_PWD_1",
        "SYNTHETIC_TMP_PNR",
        "SYNTHETIC_COUPON",
        "SYNTHETIC_DLY_WCT",
        "SYNTHETIC_DLY_SQNO",
        "SYNTHETIC_DLY_PWD",
    ):
        assert secret not in rendered
    # ...while the non-identity half of the form stays readable, so an operator
    # can still see what the change would do.
    redacted = redact_payload(form)
    assert redacted["trnNo_1"] == "00101"
    assert redacted["prcFareReCalcFlg"] == "Y"
    assert redacted["ortgCnt"] == "0001"


def test_the_preview_of_a_rollback_and_a_remix_leaks_no_handle():
    rollback = redact_payload(
        build_trip_change_rollback_form(
            KorailConfig(), ("SYNTHETIC_LUMP_1",)
        )
    )
    assert rollback["lumpStlTgtNo_1"] == "[REDACTED]"
    assert rollback["lumpStlCnt"] == "1"
    remix = redact_payload(
        build_reservation_passenger_change_form(
            KorailConfig(), _passenger_request()
        )
    )
    assert remix["pnrNo"] == "[REDACTED]"
    assert remix["chgTno"] == "[REDACTED]"


# --- the client methods -----------------------------------------------------


def test_every_method_previews_under_a_dry_run_consent_and_sends_nothing():
    client = _client(_refuse)
    try:
        previews = (
            client.create_trip_change_reservation(_request(), consent=DRY_RUN),
            client.roll_back_trip_change(
                ("SYNTHETIC_LUMP_1",), consent=DRY_RUN
            ),
            client.change_reservation_passengers(
                _passenger_request(), consent=DRY_RUN
            ),
        )
        for preview, route in zip(previews, TICKET_CHANGE_ROUTES):
            assert type(preview) is MutationPreview
            assert preview.category == "ticket_change"
            assert preview.method == "POST"
            assert preview.route == route
            assert preview.note == "dry-run: not sent"
    finally:
        client.close()


def test_every_method_refuses_the_four_ways_a_consent_can_fall_short():
    client = _client(_refuse)
    try:
        # 1. no consent at all; 2. the default consent, which grants nothing;
        # 3. every other category's opt-in. All three send nothing, and the
        # MockTransport would raise if anything did.
        refused = [None, MutationConsent()]
        refused += [
            MutationConsent(**{flag: True}, dry_run=False)
            for flag in OTHER_FLAGS
        ]
        for consent in refused:
            with pytest.raises(MutationNotAllowedError):
                client.create_trip_change_reservation(
                    _request(), consent=consent
                )
            with pytest.raises(MutationNotAllowedError):
                client.roll_back_trip_change(
                    ("SYNTHETIC_LUMP_1",), consent=consent
                )
            with pytest.raises(MutationNotAllowedError):
                client.change_reservation_passengers(
                    _passenger_request(), consent=consent
                )
        # 4. the right category, but dry_run -- the send path itself refuses
        # it, so even the low-level transmit cannot be talked into it.
        for route in TICKET_CHANGE_ROUTES:
            with pytest.raises(MutationNotAllowedError):
                client.http.post_mutation_form(
                    route,
                    {},
                    consent=DRY_RUN,
                    category="ticket_change",
                )
    finally:
        client.close()


def test_the_transport_gate_refuses_these_routes_under_any_other_category():
    client = _client(_refuse)
    try:
        everything = MutationConsent(
            allow_reserve=True,
            allow_payment=True,
            allow_cancel=True,
            allow_refund=True,
            allow_discount_card=True,
            allow_price_recalculation=True,
            allow_ticket_change=True,
            dry_run=False,
        )
        for route in TICKET_CHANGE_ROUTES:
            for category in OTHER_CATEGORIES:
                with pytest.raises(KorailProtocolError):
                    client.http.post_mutation_form(
                        route,
                        {},
                        consent=everything,
                        category=category,
                    )
    finally:
        client.close()


def test_every_method_requires_a_session_even_with_consent():
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )
    try:
        for consent in (DRY_RUN, ALLOWED):
            with pytest.raises(KorailAuthError):
                client.create_trip_change_reservation(
                    _request(), consent=consent
                )
            with pytest.raises(KorailAuthError):
                client.roll_back_trip_change(
                    ("SYNTHETIC_LUMP_1",), consent=consent
                )
            with pytest.raises(KorailAuthError):
                client.change_reservation_passengers(
                    _passenger_request(), consent=consent
                )
    finally:
        client.close()


def test_an_acknowledged_change_transmits_the_built_form_and_parses_a_hold():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "정상처리되었습니다",
                "strResult": "SUCC",
                "h_pnr_no": "SYNTHETIC_PNR",
                "h_jrny_cnt": "1",
                "h_tot_frei": "60000",
                "h_tot_prc": "60000",
                "h_tot_rcvd_amt": "8000",
            },
        )

    client = _client(handler)
    try:
        response = client.create_trip_change_reservation(
            _request(), consent=ALLOWED
        )
    finally:
        client.close()
    assert type(response) is ReservationHoldResponse
    assert len(seen) == 1
    assert seen[0].url.path == CHANGE_ROUTE
    body = dict(parse_qsl(seen[0].content.decode(), keep_blank_values=True))
    assert body == build_trip_change_reservation_form(
        KorailConfig(), _request()
    )
    # The three null @Fields never appear on the wire.
    for absent in ("tmpJobSqno", "ctlDvCd", "frcSaleRsnCont"):
        assert absent not in body


def test_an_acknowledged_rollback_transmits_the_one_indexed_target():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "정상처리되었습니다",
                "strResult": "SUCC",
            },
        )

    client = _client(handler)
    try:
        client.roll_back_trip_change(("SYNTHETIC_LUMP_1",), consent=ALLOWED)
    finally:
        client.close()
    assert len(seen) == 1
    assert seen[0].url.path == ROLLBACK_ROUTE
    body = dict(parse_qsl(seen[0].content.decode(), keep_blank_values=True))
    assert body["lumpStlCnt"] == "1"
    assert body["lumpStlTgtNo_1"] == "SYNTHETIC_LUMP_1"
