from __future__ import annotations

import re

from .config import KorailConfig
from .errors import KorailProtocolError
from .models import TrainSummary
from .mutation_models import CardPayment, ReservationHoldResponse


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
            "hidRsvChgNo": "000",
        }
    )
    return form


_CARD_FIELD_RE = re.compile(r"[0-9]+")


def build_card_payment_form(
    config: KorailConfig,
    hold: ReservationHoldResponse,
    card: CardPayment,
) -> dict[str, str]:
    """Build the single-card ReservationPayment form for an unpaid hold.

    Field set and constants mirror the evidenced app/srtgo ``pay_with_card``
    (``ktx.py:1030-1051``, cross-validated against decompiled ``PaymentMethod``):
    a single card settlement row (``hidStlMnsCd1="02"``) carrying the raw PAN.
    ``hidTmpJobSqno1/2`` are the app's fixed ``"000000"``. The reservation
    identity and amount come from ``hold`` (a fresh successful hold with a PNR,
    window number, and total price). ``card`` MUST be a non-chargeable fake card
    — the caller/method is responsible for enforcing that.
    """
    if type(hold) is not ReservationHoldResponse:
        raise KorailProtocolError(
            "KORAIL payment requires an exact reservation hold response"
        )
    if type(card) is not CardPayment:
        raise KorailProtocolError("KORAIL payment requires a CardPayment")
    pnr_no = hold.pnr_no
    window_no = hold.window_no
    amount = hold.total_price
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
            "PNR, window number, and numeric amount"
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
            "hidTmpJobSqno1": "000000",
            "hidTmpJobSqno2": "000000",
            "hidRsvChgNo": "000",
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
