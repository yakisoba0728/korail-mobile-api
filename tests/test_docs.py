"""README·문서 예제가 공개 API와 실제 조회 흐름을 유지하는지 확인합니다.

- API 페이지의 시그니처 블록이 소스의 시그니처와 같고, 공개 메서드가 모두 한 번씩 문서화돼 있어야 합니다.
- Python 예제의 공개 이름·호출 인자를 검사하고 대표 조회·예약 예제는 MockTransport로 실행합니다.

docs/ 는 sdist 에 들어가지 않으므로 없으면 건너뜁니다.
"""

from __future__ import annotations

import ast
import datetime as datetime_module
import inspect
import pathlib
import re
import runpy
import textwrap
import xml.etree.ElementTree as ET
from contextlib import closing, nullcontext
from datetime import datetime, timezone
from functools import cache
from types import SimpleNamespace

import httpx
import pytest
from conftest import synthetic_config, wire_form

import korail_mobile_api

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CLIENT = ROOT / "src" / "korail_mobile_api" / "client.py"

# The sdist ships tests but not docs/; a moved client.py must fail, not skip.
pytestmark = pytest.mark.skipif(not DOCS.is_dir(), reason="docs/ is not shipped in the sdist")

_FENCE = re.compile(r"^([ \t]*)```python[^\n]*\n(.*?)^\1```", re.S | re.M)


def _param(arg: ast.arg, default: ast.expr | None) -> str:
    text = arg.arg
    if arg.annotation is not None:
        text += f": {ast.unparse(arg.annotation)}"
    if default is not None:
        text += f" = {ast.unparse(default)}" if arg.annotation is not None else f"={ast.unparse(default)}"
    return text


def _signature(fn: ast.FunctionDef) -> str:
    args = fn.args
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parts = [_param(a, d) for a, d in zip(positional, defaults) if a.arg != "self"]
    if args.vararg is not None:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")
    parts += [_param(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults)]
    if args.kwarg is not None:
        parts.append("**" + args.kwarg.arg)
    returns = f" -> {ast.unparse(fn.returns)}" if fn.returns is not None else ""
    return f"KorailClient.{fn.name}({', '.join(parts)}){returns}"


def _client_signatures() -> dict[str, str]:
    tree = ast.parse(CLIENT.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "KorailClient")
    return {
        n.name: _signature(n) for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
    }


def _normalise(text: str) -> str:
    return re.sub(r"\s+", "", text).replace(",)", ")").replace('"', "'")


@cache
def _python_blocks() -> list[tuple[pathlib.Path, str]]:
    blocks = []
    for path in [ROOT / "README.md", *sorted(DOCS.rglob("*.md"))]:
        for match in _FENCE.finditer(path.read_text(encoding="utf-8")):
            blocks.append((path, textwrap.dedent(match.group(2))))
    return blocks


def _is_signature(block: str) -> bool:
    return block.lstrip().startswith("KorailClient.")


def test_every_public_method_has_one_signature_matching_the_source() -> None:
    expected = _client_signatures()
    seen: dict[str, pathlib.Path] = {}
    for path, block in _python_blocks():
        if not _is_signature(block):
            continue
        name = block.lstrip().split("(", 1)[0].removeprefix("KorailClient.")
        assert name in expected, f"{path.relative_to(ROOT)}: unknown method {name}"
        assert name not in seen, f"{name} is documented in both {seen[name]} and {path}"
        assert _normalise(block) == _normalise(expected[name]), (
            f"{path.relative_to(ROOT)}: signature of {name} differs from the source:\n{expected[name]}"
        )
        seen[name] = path.relative_to(ROOT)
    assert sorted(seen) == sorted(expected), f"undocumented: {sorted(set(expected) - set(seen))}"


def test_examples_compile_and_use_public_names_and_arguments() -> None:
    exported = set(korail_mobile_api.__all__)
    public_objects = {name: getattr(korail_mobile_api, name) for name in exported}
    public_objects.update(
        {
            "client": korail_mobile_api.KorailClient,
            "korail": korail_mobile_api.Korail,
            "korail.client": korail_mobile_api.KorailClient,
            "korail.stations": korail_mobile_api.StationResource,
            "korail.trains": korail_mobile_api.TrainResource,
            "korail.reservations": korail_mobile_api.ReservationResource,
            "korail.tickets": korail_mobile_api.TicketResource,
            "korail.membership": korail_mobile_api.MembershipResource,
            "korail.airport_bus": korail_mobile_api.AirportBusResource,
        }
    )
    demo = DOCS / "assets" / "demo.svg"
    demo_lines = ["".join(node.itertext()) for node in ET.parse(demo).iter("{http://www.w3.org/2000/svg}text")]
    demo_block = "\n".join(
        line[4:].replace("\N{NO-BREAK SPACE}", " ") for line in demo_lines if line.startswith((">>> ", "... "))
    )
    for path, block in [*_python_blocks(), (demo, demo_block)]:
        if _is_signature(block):
            continue
        where = path.relative_to(ROOT)
        tree = ast.parse(block, filename=str(where))
        compile(tree, str(where), "exec")
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "korail_mobile_api":
                missing = [alias.name for alias in node.names if alias.name not in exported]
                assert not missing, f"{where}: not exported from korail_mobile_api: {missing}"
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("korail_mobile_api."):
                raise AssertionError(f"{where}: import from the package root instead of {node.module}")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = ast.unparse(node.func)
            target = public_objects.get(name)
            parent, _, member = name.rpartition(".")
            if parent in public_objects:
                owner = public_objects[parent]
                assert not member.startswith("_") and hasattr(owner, member), f"{where}: unknown API {name}"
                target = getattr(owner, member)
            if target is None:
                continue
            assert callable(target), f"{where}: {name} is not callable"
            if any(isinstance(arg, ast.Starred) for arg in node.args) or any(
                k.arg is None for k in node.keywords
            ):
                continue
            signature = inspect.signature(target)
            if "self" in signature.parameters:
                signature = signature.replace(parameters=list(signature.parameters.values())[1:])
            try:
                signature.bind(*[None] * len(node.args), **{k.arg: None for k in node.keywords})
            except TypeError as error:
                raise AssertionError(f"{where}: {name}: {error}") from error


@pytest.mark.parametrize(
    "path, marker",
    [
        ("docs/getting-started.md", "continuation = result.next_page()"),
        ("docs/guide/convenience.md", "include_no_seats=False"),
    ],
)
@pytest.mark.parametrize("utc_hour, expected_date", [(14, "20990102"), (15, "20990103")])
def test_documented_search_and_pagination_keep_connections_open(
    path: str, marker: str, utc_hour: int, expected_date: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run only the selected read-only examples; the suite's socket guard stays active."""
    (block,) = [block for source, block in _python_blocks() if source == ROOT / path and marker in block]
    now = datetime(2099, 1, 1, utc_hour, 30, tzinfo=timezone.utc)

    class ExampleClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz is not None else now.replace(tzinfo=None)

    monkeypatch.setattr(datetime_module, "datetime", ExampleClock)
    events: list[str] = []
    forms: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        if request.url.host == "queue.example.invalid":
            opcode = request.url.params["opcode"]
            assert opcode in {"5101", "5004"}
            events.append(opcode)
            return httpx.Response(200, text="200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1")
        assert request.url.host == "api.example.invalid"
        if request.url.path.endswith("common.stationdata"):
            events.append("stations")
            return httpx.Response(
                200,
                json={
                    "stns": {
                        "stn": [{"stn_cd": "0001", "stn_nm": "서울"}, {"stn_cd": "0020", "stn_nm": "부산"}]
                    }
                },
            )
        assert request.url.path.endswith("seatMovie.ScheduleView")
        events.append("search")
        forms.append(wire_form(request))
        assert len(forms) <= 2, "the example must not fetch extra pages"
        first_page = len(forms) == 1
        trains = [
            {"h_trn_no": "90001" if first_page else "90003", "h_gen_rsv_cd": "13" if first_page else "11"},
            {"h_trn_no": "90002" if first_page else "90004", "h_gen_rsv_cd": "13"},
        ]
        return httpx.Response(
            200,
            json={
                "strResult": "SUCC",
                "h_next_pg_flg": "Y" if first_page else "N",
                "h_qry_st_no_next": "0001",
                "h_trn_no_next": "90002",
                "trn_infos": {"trn_info": trains},
            },
        )

    config = synthetic_config(
        dynapath=korail_mobile_api.DynapathConfig(enabled=True, token_provider=lambda _: "SYNTHETIC-TOKEN")
    )
    client_type, korail_type = korail_mobile_api.KorailClient, korail_mobile_api.Korail
    clients: list[korail_mobile_api.KorailClient] = []

    def make_client():
        client = client_type(config, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client

    def make_korail():
        korail = korail_type(config, transport=httpx.MockTransport(handler))
        clients.append(korail.client)
        return korail

    monkeypatch.setattr(korail_mobile_api, "KorailClient", make_client)
    monkeypatch.setattr(korail_mobile_api, "Korail", make_korail)
    namespace: dict[str, object] = {}
    try:
        exec(compile(block, path, "exec"), namespace)
        assert len(clients) == 1
        with pytest.raises(korail_mobile_api.KorailProtocolError, match="closed"):  # the example closed it
            clients[0].get_service_status()
        assert len(forms) == 2
        assert all(form["txtGoAbrdDt"] == [expected_date] for form in forms)
        assert forms[0].get("qryStTrnNo") in (None, [""])
        assert forms[1]["qryStNo"] == ["0001"] and forms[1]["qryStTrnNo"] == ["90002"]
        expected_events = ["5101", "search", "5004"] * 2
        if path.endswith("convenience.md"):
            expected_events.insert(0, "stations")
            result, more = namespace["result"], namespace["more"]
            assert isinstance(result, korail_mobile_api.TrainSearchResult) and result.trains == []
            assert result.unfiltered_trains is not None and len(result.unfiltered_trains) == 2
            assert isinstance(more, korail_mobile_api.TrainSearchResult)
            assert [train.train_no for train in more.trains] == ["90003"]
        assert events == expected_events
    finally:
        for client in clients:
            client.close()


@pytest.mark.parametrize("use_option", [False, True], ids=["default", "general-first"])
def test_documented_reservation_keeps_search_passengers(
    use_option: bool, scripted_client_factory, f8_logged_in_session
) -> None:
    """Run the two reservation examples as alternatives using only the shared offline transport."""
    path = DOCS / "guide" / "convenience.md"
    (block,) = [
        block
        for source, block in _python_blocks()
        if source == path and "passengers = KorailPassengerCounts(adult=2, child=1)" in block
    ]
    if use_option:
        (option,) = [
            block
            for source, block in _python_blocks()
            if source == path and "option=KorailReserveOption.GENERAL_FIRST" in block
        ]
        block = block.split("hold = ", 1)[0] + option
    config = synthetic_config(netfunnel_enabled=False, disable_dynapath=True)
    row = {
        "h_trn_no": "90001",
        "h_trn_gp_cd": "101",
        "h_trn_clsf_cd": "00",
        "h_run_dt": "20990102",
        "h_dpt_dt": "20990102",
        "h_dpt_tm": "100000",
        "h_dpt_rs_stn_cd": "9901",
        "h_arv_rs_stn_cd": "9903",
        "h_dpt_stn_cons_ordr": "001",
        "h_arv_stn_cons_ordr": "002",
        "h_dpt_stn_run_ordr": "001",
        "h_arv_stn_run_ordr": "002",
        "h_gen_rsv_cd": "11",
    }
    client, requests, pending = scripted_client_factory(
        [
            {"strResult": "SUCC", "trn_infos": {"trn_info": [row]}},
            {
                "strResult": "SUCC",
                "h_pnr_no": "SYNTHETIC-PNR",
                "h_jrny_cnt": "1",
                "h_wct_no": "SYNTHETIC-WINDOW",
                "h_tmp_job_sqno1": "1",
                "h_tmp_job_sqno2": "2",
                "h_tot_prc": "1000",
                "h_rcvd_amt": "1000",
            },
        ],
        config=config,
        session=f8_logged_in_session,
    )
    korail = SimpleNamespace(
        trains=korail_mobile_api.TrainResource(
            client, korail_mobile_api.StationResource(client), validate_stations=False
        ),
        reservations=korail_mobile_api.ReservationResource(client),
    )
    with closing(client):
        exec(compile(block, str(path), "exec"), {"korail": korail})
    with pytest.raises(korail_mobile_api.KorailProtocolError, match="closed"):
        client.get_service_status()
    assert len(requests) == 2 and pending == []
    assert requests[0].url.path.endswith("seatMovie.ScheduleView")
    assert requests[1].url.path.endswith("certification.TicketReservation")
    search, reservation = [wire_form(request) for request in requests]
    assert search["txtPsgFlg_1"] == ["2"] and search["txtPsgFlg_2"] == ["1"]
    assert reservation["txtTotPsgCnt"] == ["3"]
    assert reservation["txtCompaCnt1"] == ["2"] and reservation["txtPsgTpCd1"] == ["1"]
    assert reservation["txtCompaCnt2"] == ["1"] and reservation["txtPsgTpCd2"] == ["3"]


def test_every_public_export_has_a_root_reference() -> None:
    directives = {
        name
        for path in DOCS.rglob("*.md")
        for name in re.findall(r"^::: korail_mobile_api\.(\w+)\s*$", path.read_text(encoding="utf-8"), re.M)
    }
    assert directives == set(korail_mobile_api.__all__)


@pytest.mark.parametrize(
    "text",
    [
        "``next_page()``로 이어서 조회하세요. ``repr()``은 원문을 숨깁니다.",
        "예제::\n\n    rows = ()\n    if rows:\n        print(rows)\n\n\n다음 문단입니다.",
    ],
)
def test_griffe_cleanup_preserves_calls_tuples_and_indentation(text: str) -> None:
    pytest.importorskip("griffe")
    clean = runpy.run_path(str(DOCS / "griffe_docs.py"))["clean"]
    assert clean(text) == text


def test_griffe_extension_keeps_wire_defaults_and_field_comments(tmp_path: pathlib.Path) -> None:
    griffe = pytest.importorskip("griffe")
    extension = runpy.run_path(str(DOCS / "griffe_docs.py"))["DocsExtension"]
    source = tmp_path / "doc_fields.py"
    source.write_text(
        "from korail_mobile_api._core.parsing import wire\n"
        "#: 첫 줄입니다.\n#: 두 번째 줄입니다.\n"
        'optional: str | None = wire("optional")\n'
        'required: str = wire("required", str)\n'
        'empty: str = wire("empty", str, default="")\n'
        'nullable: str | None = wire("nullable", str, default=None)\n',
        encoding="utf-8",
    )
    module = griffe.load(
        "doc_fields",
        search_paths=[tmp_path],
        extensions=griffe.load_extensions(extension),
        allow_inspection=False,
    )
    assert str(module["optional"].value) == "None"
    assert module["required"].value is None
    assert str(module["empty"].value) == "''"
    assert str(module["nullable"].value) == "None"
    assert module["optional"].docstring.value == "첫 줄입니다. 두 번째 줄입니다."


@pytest.mark.parametrize("invalid_input", [False, True], ids=["null-response", "preflight-rejection"])
def test_documented_recovery_checks_state_after_a_null_response(
    invalid_input: bool, scripted_client_factory, f8_logged_in_session, capsys: pytest.CaptureFixture[str]
) -> None:
    path = DOCS / "guide" / "errors.md"
    (block,) = [block for source, block in _python_blocks() if source == path and "def held_pnrs():" in block]
    row = {
        "h_trn_no": "90001",
        "h_trn_gp_cd": "101",
        "h_trn_clsf_cd": "00",
        "h_run_dt": "20990102",
        "h_dpt_dt": "20990102",
        "h_dpt_tm": "100000",
        "h_dpt_rs_stn_cd": "9901",
        "h_arv_rs_stn_cd": "9903",
        "h_dpt_stn_cons_ordr": "001",
        "h_arv_stn_cons_ordr": "002",
        "h_dpt_stn_run_ordr": "001",
        "h_arv_stn_run_ordr": "002",
        "h_gen_rsv_cd": "11",
    }
    if invalid_input:
        row["h_run_dt"] = "invalid"
    replies = [
        {"strResult": "SUCC", "trn_infos": {"trn_info": [row]}},
        {"strResult": "FAIL", "h_msg_cd": "P100"},
    ]
    if not invalid_input:
        replies += [None, {"strResult": "FAIL", "h_msg_cd": "P100"}]
    client, requests, pending = scripted_client_factory(
        replies,
        config=synthetic_config(netfunnel_enabled=False, disable_dynapath=True),
        session=f8_logged_in_session,
    )
    query = korail_mobile_api.TrainSearchQuery(
        departure_station="서울", arrival_station="부산", departure_date="20990102"
    )
    with client, pytest.raises(korail_mobile_api.KorailProtocolError) as caught:
        exec(compile(block, str(path), "exec"), {"client": client, "query": query})
    error = caught.value
    assert error.raw is None
    assert error.request_sent is (None if invalid_input else True)
    assert isinstance(error, korail_mobile_api.KorailInvalidInputError) is invalid_input
    expected = ["seatMovie.ScheduleView", "reservation.ReservationView"]
    if not invalid_input:
        expected += ["certification.TicketReservation", "reservation.ReservationView"]
    assert [request.url.path.rsplit("mobile.", 1)[-1] for request in requests] == expected
    assert pending == []
    assert ("새 홀드가 보이지 않습니다" in capsys.readouterr().out) is not invalid_input


@pytest.mark.parametrize("cart_fails", [False, True], ids=["cart-success", "cart-timeout"])
def test_documented_recalculation_keeps_the_latest_hold_if_optional_cart_fails(
    cart_fails: bool, scripted_client_factory, f8_logged_in_session, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = DOCS / "guide" / "payments.md"
    (block,) = [
        block
        for source, block in _python_blocks()
        if source == path and "recalculated = client.recalculate_price(request)" in block
    ]
    hold = korail_mobile_api.ReservationHoldResponse(
        str_result="SUCC",
        pnr_no="SYNTHETIC-PNR",
        received_amount="1200",
        journeys=(
            korail_mobile_api.ReservationJourney(
                raw={
                    "seat_infos": {
                        "seat_info": [{"h_psg_tp_cd": "1", "h_psrm_cl_cd": "1", "h_dcnt_knd_cd1": "000"}]
                    }
                }
            ),
        ),
    )
    client, requests, pending = scripted_client_factory(
        [
            {"strResult": "SUCC", "h_pnr_no": "SYNTHETIC-PNR", "h_tot_rcvd_amt": "1000"},
            httpx.ReadTimeout("synthetic cart timeout") if cart_fails else {"strResult": "SUCC"},
        ],
        config=synthetic_config(netfunnel_enabled=False, disable_dynapath=True),
        session=f8_logged_in_session,
    )
    monkeypatch.setattr("builtins.input", lambda _: "000")
    namespace = {"client": client, "hold": hold}
    expectation = pytest.raises(korail_mobile_api.KorailTransportError) if cart_fails else nullcontext()
    with client, expectation:
        exec(compile(block, str(path), "exec"), namespace)
    assert namespace["hold"] is namespace["recalculated"]
    assert namespace["hold"].received_amount == "1000"
    assert len(requests) == 2 and pending == []
    assert wire_form(requests[1])["hidPnrNo"] == ["SYNTHETIC-PNR"]
    assert all("ReservationPayment" not in request.url.path for request in requests)
    with pytest.raises(korail_mobile_api.KorailProtocolError, match="closed"):
        client.get_service_status()


@pytest.mark.parametrize("method", ["pay_with_card", "get_guide_seat_condition", "list_discount_coupons"])
def test_documented_update_code_keeps_each_methods_existing_failure_policy(
    method: str, scripted_client_factory, f8_logged_in_session
) -> None:
    raw = {"strResult": "FAIL", "h_msg_cd": "-8204", "h_msg_txt": "synthetic update required"}
    client, requests, pending = scripted_client_factory(
        [raw],
        config=synthetic_config(netfunnel_enabled=False, disable_dynapath=True),
        session=f8_logged_in_session,
    )
    if method == "pay_with_card":
        args = (
            korail_mobile_api.ReservationHoldResponse(
                str_result="SUCC",
                pnr_no="SYNTHETIC-PNR",
                window_no="SYNTHETIC-WINDOW",
                journey_count="1",
                received_amount="1000",
            ),
            korail_mobile_api.CardPayment(
                card_number="0000000000000000", card_password="00", card_expire="9912", birthday="000000"
            ),
        )
    elif method == "get_guide_seat_condition":
        args = (korail_mobile_api.GuideSeatConditionRequest(seat_attribute_code="SYNTHETIC"),)
    else:
        args = ()
    with client:
        if method == "list_discount_coupons":
            with pytest.raises(korail_mobile_api.KorailAppUpdateRequiredError) as caught:
                getattr(client, method)(*args)
            assert caught.value.raw == raw and caught.value.message == raw["h_msg_txt"]
        else:
            result = getattr(client, method)(*args)
            assert result.str_result == "FAIL" and result.h_msg_cd == "-8204" and result.raw == raw
    assert len(requests) == 1 and pending == []
