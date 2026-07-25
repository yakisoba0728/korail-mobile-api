from __future__ import annotations

import re

from .config import KorailConfig
from .errors import KorailProtocolError
from .models import TrainSummary
from .mutation_models import CardPayment, PaidTicket, ReservationHoldResponse


_DATE_RE = re.compile(r"[0-9]{8}")
_TIME_RE = re.compile(r"[0-9]{6}")
_DIGITS_RE = re.compile(r"[0-9]+")


def _required_digits(value: str | None, *, field: str) -> str:
    if not isinstance(value, str) or _DIGITS_RE.fullmatch(value) is None:
        raise KorailProtocolError(
            f"KORAIL reservation train field {field} must be decimal digits"
        )
    return value


def _required_pattern(
    value: str | None,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise KorailProtocolError(
            f"KORAIL reservation train field {field} has an invalid shape"
        )
    return value


def _common_fields(config: KorailConfig) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
    }


def build_single_adult_reservation_form(
    config: KorailConfig,
    train: TrainSummary,
) -> dict[str, str]:
    if type(train) is not TrainSummary:
        raise KorailProtocolError(
            "KORAIL reservation requires an exact TrainSummary"
        )
    if train.general_reservation_code != "11":
        raise KorailProtocolError(
            "KORAIL reservation requires an evidenced available general seat"
        )

    train_no = _required_digits(train.train_no, field="train_no")
    train_group_code = _required_digits(
        train.train_group_code,
        field="train_group_code",
    )
    train_class_code = _required_digits(
        train.train_class_code,
        field="train_class_code",
    )
    run_date = _required_pattern(
        train.run_date,
        field="run_date",
        pattern=_DATE_RE,
    )
    departure_date = _required_pattern(
        train.departure_date,
        field="departure_date",
        pattern=_DATE_RE,
    )
    departure_time = _required_pattern(
        train.departure_time,
        field="departure_time",
        pattern=_TIME_RE,
    )
    arrival_time = _required_pattern(
        train.arrival_time,
        field="arrival_time",
        pattern=_TIME_RE,
    )
    departure_station_code = _required_digits(
        train.departure_station_code,
        field="departure_station_code",
    )
    arrival_station_code = _required_digits(
        train.arrival_station_code,
        field="arrival_station_code",
    )
    departure_construction_order = _required_digits(
        train.departure_construction_order,
        field="departure_construction_order",
    )
    arrival_construction_order = _required_digits(
        train.arrival_construction_order,
        field="arrival_construction_order",
    )
    departure_run_order = _required_digits(
        train.departure_run_order,
        field="departure_run_order",
    )
    arrival_run_order = _required_digits(
        train.arrival_run_order,
        field="arrival_run_order",
    )
    form = _common_fields(config)
    form.update(
        {
            "txtMenuId": "11",
            "txtJobId": "1101",
            "txtGdNo": "",
            "hidFreeFlg": "N",
            "txtStndFlg": "N",
            "txtTotPsgCnt": "1",
        }
    )
    passenger_rows = (
        ("1", "1", "000"),
        ("0", "1", "P11"),
        ("0", "3", "000"),
        ("0", "3", "321"),
        ("0", "1", "131"),
        ("0", "1", "111"),
        ("0", "1", "112"),
        ("0", "1", "173"),
    )
    for index, (count, passenger_type, discount_code) in enumerate(
        passenger_rows,
        start=1,
    ):
        form[f"txtCompaCnt{index}"] = count
        form[f"txtPsgTpCd{index}"] = passenger_type
        form[f"txtDiscKndCd{index}"] = discount_code
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            "txtSeatAttCd4": "015",
            "txtSeatAttCd5": "000",
            "txtPsrmClCd1": "1",
            "txtJrnyCnt": "1",
            "txtJrnyTpCd1": "11",
            "txtJrnySqno1": "001",
            "txtTrnNo1": train_no,
            "txtTrnClsfCd1": train_class_code,
            "txtTrnGpCd1": train_group_code,
            "txtRunDt1": run_date,
            "txtDptDt1": departure_date,
            "txtDptTm1": departure_time,
            "arvTm_1": arrival_time,
            "txtDptRsStnCd1": departure_station_code,
            "txtDptStnConsOrdr1": departure_construction_order,
            "txtDptStnRunOrdr1": departure_run_order,
            "txtArvRsStnCd1": arrival_station_code,
            "txtArvStnConsOrdr1": arrival_construction_order,
            "txtArvStnRunOrdr1": arrival_run_order,
            "txtChgFlg1": "N",
        }
    )
    return form


def build_unpaid_reservation_cancel_form(
    config: KorailConfig,
    response: ReservationHoldResponse,
) -> dict[str, str]:
    if type(response) is not ReservationHoldResponse:
        raise KorailProtocolError(
            "KORAIL cancellation requires an exact reservation hold response"
        )
    # A live TicketReservation returns the journey count zero-padded
    # (h_jrny_cnt="0001"), not "1". Accept any digit string that is numerically
    # one single journey; the cancel form still transmits the app's txtJrnyCnt.
    journey_count = response.journey_count
    is_single_journey = (
        isinstance(journey_count, str)
        and journey_count.strip().isdigit()
        and int(journey_count) == 1
    )
    if (
        response.str_result != "SUCC"
        or not isinstance(response.pnr_no, str)
        or not response.pnr_no.strip()
        or not is_single_journey
    ):
        raise KorailProtocolError(
            "KORAIL cancellation requires one fresh successful unpaid hold"
        )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": response.pnr_no,
            "txtJrnySqno": "0001",
            "txtJrnyCnt": "1",
            # A literal "000" here, NOT the hold's h_rsv_chg_no -- deliberately
            # unlike build_card_payment_form below. Every app flow that cancels
            # a just-created hold from its ReservationResponse hardcodes it,
            # next to the same fixed txtJrnySqno="0001":
            # DReservationConfirmActivity.java:270-279 is decisive, because
            # executeRsvCancel(ReservationResponse) reads getH_pnr_no() and
            # getH_jrny_cnt() off that very response, even stores the whole
            # object via setReservationResponse, and STILL sets "000" rather
            # than jrny_info[0].getH_rsv_chg_no(). Likewise
            # ReservationWaitActivity.java:118-128, a6/x.java:97-106,
            # LimousineActivity.java:134-143 and
            # LimousineSelectSeatActivity.java:325. The only cancel call sites
            # that pass a real change number are the reservation-LIST screens
            # (ReservedTicketActivity.java:228, BasketTicketActivity.java:276),
            # which cancel an arbitrary listed row and therefore also pass that
            # row's own h_jrny_sqno instead of "0001". This builder is the
            # fresh-single-journey-hold flow, so it sends the app's constant.
            "hidRsvChgNo": "000",
        }
    )
    return form


_CARD_FIELD_RE = re.compile(r"[0-9]+")

# What the app sends when the hold response withheld the sequence. The app
# passes whatever getH_tmp_job_sqno1/2() returned, including null, and Retrofit
# then omits the @Field entirely — a shape this client cannot reproduce without
# making the field conditional, and one no observed hold has produced (both
# 2026-07 live holds returned populated sequences). "000000" is the value this
# builder has always sent and the value srtgo hardcodes, so it stays as the
# explicit last resort rather than dropping reservation state silently.
_ABSENT_JOB_SEQUENCE = "000000"


def _echoed_job_sequence(value: str | None) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return _ABSENT_JOB_SEQUENCE


# What the payment form sends when the hold response carried no usable
# first-journey h_rsv_chg_no. The app never handles that case: V4/b.java:41
# dereferences getJrny_infos().getJrny_info().get(0) unconditionally, so a hold
# without a journey row would throw inside the app rather than produce a wire
# value, and a null h_rsv_chg_no would be forwarded and then dropped by Retrofit
# -- neither shape is reproducible here without making the @Field conditional,
# and no observed hold has produced one. "000" is the value this builder has
# always sent, the value every fresh-hold cancel in the app hardcodes, and the
# value srtgo uses, so it stays as the explicit last resort. Note V4/b.java:25-30
# falls back to "0" instead, but only on getRecalculationRsvPaymentRequest,
# whose source is a previous request object rather than the reservation
# response; it is not this path's fallback.
_ABSENT_RESERVATION_CHANGE_NO = "000"


def _echoed_reservation_change_no(hold: ReservationHoldResponse) -> str:
    # The FIRST journey specifically, mirroring the app's
    # getJrny_infos().getJrny_info().get(0).getH_rsv_chg_no() (V4/b.java:41).
    journeys = hold.journeys
    if journeys:
        value = journeys[0].reservation_change_no
        if isinstance(value, str) and value.strip():
            return value
    return _ABSENT_RESERVATION_CHANGE_NO


def build_card_payment_form(
    config: KorailConfig,
    hold: ReservationHoldResponse,
    card: CardPayment,
) -> dict[str, str]:
    """Build the single-card ReservationPayment form for an unpaid hold.

    Field set and constants mirror the evidenced app/srtgo ``pay_with_card``
    (``ktx.py:1030-1051``, cross-validated against decompiled ``PaymentMethod``):
    a single card settlement row (``hidStlMnsCd1="02"``) carrying the raw PAN.
    ``hidTmpJobSqno1/2`` echo the hold response, not a constant: ``V4/b.java:39-40``
    does ``setJobSqNo1(reservationResponse.getH_tmp_job_sqno1())`` (likewise 2)
    and ``RsvPaymentDao.executeDao()`` (``:129-131``) hands those straight to
    ``PaymentService.payment``'s ``@Field("hidTmpJobSqno1"/"2")``
    (``PaymentService.java:14``). ``hidRsvChgNo`` echoes the hold the same way:
    ``V4/b.java:41`` does ``setHidRsvChgNo(reservationResponse.getJrny_infos()
    .getJrny_info().get(0).getH_rsv_chg_no())`` — the FIRST journey's change
    number — and the app repeats that exact expression at every other payment
    call site (``MainBookingActivity.java:998``,
    ``OldMainBookingActivity.java:505``, ``TicketListActivity.java:1518``,
    ``ReservedTicketActivity.java:414``, ``LimousineActivity.java:189``,
    ``LimousineSelectSeatActivity.java:180``). It is per-reservation state, not a
    protocol constant; the cancel builder's fixed ``"000"`` is a genuinely
    different case, evidenced separately there. The reservation identity and
    amount come from ``hold`` (a fresh successful hold with a PNR, window
    number, and a received amount). This builder does not decide whether ``card``
    is chargeable and cannot tell: both ``pay_with_fake_card`` and
    ``pay_with_card`` build through here, and the consent they each accept is
    what separates a test card from an acknowledged real charge.

    ``hidMnsStlAmt1`` is the app's ``getReceivedAmount()``, not the display
    total: ``AbstractC1269e.java:406`` puts ``String.valueOf(getReceivedAmount())``
    into ``PAYMENT_AMOUNT`` and ``V4/a.java:27`` sets that as ``hidMnsStlAmt1``.
    ``h_tot_prc`` goes to ``mTotPrc`` (``PaymentActivity.java:174``), which is
    read only by ``getmTotPrc()`` (``:497``) for the UI. The two coincide for a
    single undiscounted adult, which is why the one live (card-declined) run
    never exposed the difference, but they diverge as soon as a discount or a
    second passenger is involved.
    """
    if type(hold) is not ReservationHoldResponse:
        raise KorailProtocolError(
            "KORAIL payment requires an exact reservation hold response"
        )
    if type(card) is not CardPayment:
        raise KorailProtocolError("KORAIL payment requires a CardPayment")
    pnr_no = hold.pnr_no
    window_no = hold.window_no
    # Deliberately NOT hold.total_price: that is the display figure. See the
    # docstring — the app settles getReceivedAmount(). When a hold response
    # carries neither h_tot_rcvd_amt nor readable per-seat h_rcvd_amt rows we
    # refuse rather than substitute the display total, because substituting is
    # exactly the defect this replaces.
    amount = hold.received_amount
    if (
        hold.str_result != "SUCC"
        or not isinstance(pnr_no, str)
        or not pnr_no.strip()
        or not isinstance(window_no, str)
        or not window_no.strip()
        or not isinstance(amount, str)
        or _DIGITS_RE.fullmatch(amount) is None
    ):
        raise KorailProtocolError(
            "KORAIL payment requires a fresh successful unpaid hold with a "
            "PNR, window number, and numeric received amount"
        )
    # The card number must be all digits (a fake test PAN is still digits); the
    # decline happens server-side at authorization.
    if _CARD_FIELD_RE.fullmatch(card.card_number) is None:
        raise KorailProtocolError("KORAIL payment card number must be digits")
    form = _common_fields(config)
    form.update(
        {
            "hidPnrNo": pnr_no,
            "hidWctNo": window_no,
            "hidTmpJobSqno1": _echoed_job_sequence(
                hold.temporary_job_sequence_1
            ),
            "hidTmpJobSqno2": _echoed_job_sequence(
                hold.temporary_job_sequence_2
            ),
            "hidRsvChgNo": _echoed_reservation_change_no(hold),
            "hidInrecmnsGridcnt": "1",
            "hidStlMnsSqno1": "1",
            "hidStlMnsCd1": "02",
            "hidMnsStlAmt1": amount,
            "hidCrdInpWayCd1": "@",
            "hidStlCrCrdNo1": card.card_number,
            "hidVanPwd1": card.card_password,
            "hidCrdVlidTrm1": card.card_expire,
            "hidIsmtMnthNum1": card.installment,
            "hidAthnDvCd1": card.card_type,
            "hidAthnVal1": card.birthday,
            "hiduserYn": "Y",
        }
    )
    return form


def build_refund_form(
    config: KorailConfig,
    ticket: PaidTicket,
) -> dict[str, str]:
    """Build the ticket-refund (``refunds.RefundsRequest``) form for a paid ticket.

    Field set and order follow the app's own Retrofit declaration
    (``RefundService.java:29`` / ``RefundService.smali:212``): the PNR is
    ``txtPnrNo`` (P-n-r), plus the original-ticket sale window/date/sequence and
    return password, with the fixed ``h_mlg_stl="N"``,
    ``tk_ret_tms_dv_cd="21"``, ``pbpAcepTgtFlg="N"`` and empty geo fields.
    srtgo's ``ktx.py:1082`` spells the same field ``txtPrnNo``; that is a
    korail2-lineage typo which occurs ZERO times in the decompiled app, and
    Retrofit ``@Field`` names are exact-match, so sending it would transmit a
    refund with no PNR at all. A refund acts on a settled ticket; the caller
    supplies the :class:`PaidTicket` identity.
    """
    if type(ticket) is not PaidTicket:
        raise KorailProtocolError("KORAIL refund requires a PaidTicket")
    for name, value in (
        ("pnr_no", ticket.pnr_no),
        ("sale_date", ticket.sale_date),
        ("sale_window_no", ticket.sale_window_no),
        ("sale_sequence", ticket.sale_sequence),
        ("return_password", ticket.return_password),
    ):
        if not isinstance(value, str) or not value.strip():
            raise KorailProtocolError(
                f"KORAIL refund requires a non-empty PaidTicket.{name}"
            )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": ticket.pnr_no,
            "h_orgtk_sale_dt": ticket.sale_date,
            "h_orgtk_sale_wct_no": ticket.sale_window_no,
            "h_orgtk_sale_sqno": ticket.sale_sequence,
            "h_orgtk_ret_pwd": ticket.return_password,
            "h_mlg_stl": "N",
            "tk_ret_tms_dv_cd": "21",
            "trnNo": ticket.train_no,
            "pbpAcepTgtFlg": "N",
            "latitude": "",
            "longitude": "",
        }
    )
    return form
