"""README·문서 예제가 공개 API와 실제 조회 흐름을 유지하는지 확인합니다.

- API 페이지의 시그니처 블록이 소스의 시그니처와 같고, 공개 메서드가 모두 한 번씩 문서화돼 있어야 합니다.
- Python 예제의 공개 이름·호출 인자를 검사하고 대표 조회 예제는 MockTransport로 실행합니다.

docs/ 는 sdist 에 들어가지 않으므로 없으면 건너뜁니다.
"""

from __future__ import annotations

import ast
import datetime as datetime_module
import inspect
import pathlib
import re
import textwrap
from datetime import datetime, timezone
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CLIENT = ROOT / "src" / "korail_mobile_api" / "client.py"

pytestmark = pytest.mark.skipif(
    not DOCS.is_dir() or not CLIENT.is_file(), reason="docs/ is not shipped in the sdist"
)

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
        }
    )
    for path, block in _python_blocks():
        if _is_signature(block):
            continue
        where = path.relative_to(ROOT)
        tree = ast.parse(block, filename=str(where))
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
        forms.append(parse_qs(request.content.decode(), keep_blank_values=True))
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

    config = korail_mobile_api.KorailConfig(
        base_url="https://api.example.invalid",
        netfunnel_url="https://queue.example.invalid",
        dynapath=korail_mobile_api.DynapathConfig(enabled=True, token_provider=lambda _: "SYNTHETIC-TOKEN"),
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
        assert len(clients) == 1 and clients[0].http._client.is_closed
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
