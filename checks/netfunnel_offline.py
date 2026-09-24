"""NetFunnel 대기열 연결을 오프라인으로 검사합니다(실행 방법: ``checks/README.md``).

:class:`~korail_mobile_api.client.KorailClient` 가 대기열이 걸린 작업에서 앱처럼
5101 → (대기면 ttl 만큼 자고 5002) → KORAIL 요청 → 5004 순서를 지키는지 봅니다.
두 호스트(``nf.letskorail.com``/``rnf*.letskorail.com`` 와 ``smart.letskorail.com``)를
하나의 ``httpx.MockTransport`` 가 받고, 대기는 가짜 ``sleep`` 이라 즉시 끝납니다.
네트워크를 쓰지 않습니다. 값은 전부 합성값입니다.

종료 코드: 0 통과, 1 실패, 2 검사 불완전(import 실패, 검사기 자신의 예외).

    python3 checks/netfunnel_offline.py
"""

from __future__ import annotations

import logging
import pathlib
import sys
import traceback
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

failures: list[str] = []

KORAIL_EMPTY = {"strResult": "FAIL", "h_msg_cd": "P100", "h_msg_txt": "synthetic"}
KORAIL_SEARCH = {"strResult": "SUCC", "h_msg_cd": "IRG000000", "h_msg_txt": "synthetic"}
NODE = "ip=rnf12.letskorail.com&port=443"


def check(name: str, ok: bool, detail: str = "") -> None:
    if not ok:
        failures.append(f"{name}: {detail}")


class World:
    """두 호스트를 흉내 내고 오간 요청을 순서대로 기록합니다."""

    def __init__(
        self,
        queue: list[str | Exception],
        *,
        korail: dict[str, Any] | Exception = KORAIL_EMPTY,
    ) -> None:
        self.queue = list(queue)  # 5101/5002 에 차례로 줄 답
        self.korail = korail
        self.log: list[tuple[str, str, dict[str, str]]] = []

    def handler(self, request: Any) -> Any:
        import httpx

        host = request.url.host
        if host.endswith("letskorail.com") and request.url.path == "/ts.wseq":
            query = {k: v[0] for k, v in parse_qs(request.url.query.decode()).items()}
            self.log.append(("nf", host, query))
            if query.get("opcode") == "5004":
                return httpx.Response(200, text="200:key=&nwait=0")
            if not self.queue:
                raise AssertionError(f"unexpected queue request {query}")
            answer = self.queue.pop(0)
            if isinstance(answer, Exception):
                raise httpx.ConnectError(str(answer), request=request)
            return httpx.Response(200, text=answer)
        if host == "smart.letskorail.com":
            self.log.append(("korail", host, {"path": request.url.path}))
            if isinstance(self.korail, Exception):
                raise httpx.ConnectError(str(self.korail), request=request)
            return httpx.Response(200, json=self.korail)
        raise AssertionError(f"request to unexpected host {host}")

    def opcodes(self) -> list[str]:
        return [q.get("opcode", "") if kind == "nf" else "KORAIL" for kind, _host, q in self.log]

    def completes(self) -> list[tuple[str, str]]:
        return [
            (host, q.get("key", "")) for kind, host, q in self.log if kind == "nf" and q.get("opcode") == "5004"
        ]


def make_client(world: World, **config: Any) -> tuple[Any, list[float]]:
    import httpx

    from korail_mobile_api import KorailClient, KorailConfig
    from korail_mobile_api.models import KorailSession

    client = KorailClient(KorailConfig(**config), transport=httpx.MockTransport(world.handler))
    client.session.current = KorailSession(jsessionid="SYNTHETIC-JSESSIONID", member_no="0000000000")
    sleeps: list[float] = []
    now = [0.0]

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    if client.netfunnel is not None:
        client.netfunnel._sleep = fake_sleep
        client.netfunnel._clock = lambda: now[0]
    return client, sleeps


def raises(call: Callable[[], object]) -> BaseException | None:
    try:
        call()
    except Exception as error:  # noqa: BLE001
        return error
    return None


def search(client: Any) -> object:
    from korail_mobile_api import TrainSearchQuery

    return client.search_trains(
        TrainSearchQuery(
            departure_station_code="서울",
            arrival_station_code="부산",
            departure_date="20260801",
            departure_time="060000",
        )
    )


# ---------------------------------------------------------------------------
def case_immediate_pass() -> None:
    world = World([f"200:key=K1&nwait=0&{NODE}"])
    client, sleeps = make_client(world)
    client.get_reservation_history()
    check("a", world.opcodes() == ["5101", "KORAIL", "5004"], f"순서 {world.opcodes()}")
    check("a", world.completes() == [("rnf12.letskorail.com", "K1")], f"반납 {world.completes()}")
    check("a", sleeps == [], f"잠 {sleeps}")
    first = world.log[0][2]
    check("a", first == {"opcode": "5101", "sid": "service_1", "aid": "act_21"}, f"5101 {first}")
    check("a", world.log[0][1] == "nf.letskorail.com", f"5101 호스트 {world.log[0][1]}")


def case_wait_then_pass() -> None:
    world = World(
        [
            f"201:key=K0&ttl=5&nwait=30&{NODE}",
            f"201:key=K1&ttl=99&nwait=20&{NODE}",
            "202:key=K2&ttl=0&nwait=10",
            f"200:key=K3&nwait=0&{NODE}",
        ]
    )
    client, sleeps = make_client(world)
    client.get_reservation_history()
    check("b", world.opcodes() == ["5101", "5002", "5002", "5002", "KORAIL", "5004"], f"순서 {world.opcodes()}")
    keys = [q.get("key") for kind, _h, q in world.log if q.get("opcode") == "5002"]
    check("b", keys == ["K0", "K1", "K2"], f"5002 키 {keys}")
    check("b", sleeps == [5, 30, 1], f"ttl [1,30] 대기 {sleeps}")
    # 최신 응답에 노드가 없으면 정문: CommandClient.java:33-38,137.
    hosts = [h for kind, h, q in world.log if q.get("opcode") in {"5002", "5004"}]
    check(
        "b",
        hosts == ["rnf12.letskorail.com", "rnf12.letskorail.com", "nf.letskorail.com", "rnf12.letskorail.com"],
        f"노드 {hosts}",
    )
    check("b", world.completes() == [("rnf12.letskorail.com", "K3")], f"반납 {world.completes()}")


def case_blocked() -> None:
    from korail_mobile_api import KorailQueueRejectedError

    for label, call in (("reservation_view", lambda c: c.get_reservation_history()), ("inquiry", search)):
        world = World([f"301:key=KB&{NODE}"], korail=KORAIL_SEARCH)
        client, _ = make_client(world)
        error = raises(lambda: call(client))
        check("c", isinstance(error, KorailQueueRejectedError), f"{label}: {type(error).__name__}")
        check("c", "KORAIL" not in world.opcodes(), f"{label}: KORAIL 요청이 나감")
        check("c", world.completes() == [("rnf12.letskorail.com", "KB")], f"{label}: 반납 {world.completes()}")


def case_korail_raises() -> None:
    from korail_mobile_api import KorailTransportError

    world = World([f"200:key=K1&{NODE}"], korail=RuntimeError("synthetic down"))
    client, _ = make_client(world)
    error = raises(client.get_reservation_history)
    check("d", isinstance(error, KorailTransportError), f"{type(error).__name__}")
    check("d", world.opcodes() == ["5101", "KORAIL", "5004"], f"순서 {world.opcodes()}")
    check("d", world.completes() == [("rnf12.letskorail.com", "K1")], f"반납 {world.completes()}")


def case_disabled() -> None:
    world = World([])
    client, _ = make_client(world, netfunnel_enabled=False)
    client.get_reservation_history()
    check("e", client.netfunnel is None, "대기열 클라이언트가 만들어짐")
    check("e", world.opcodes() == ["KORAIL"], f"순서 {world.opcodes()}")


def case_queue_down() -> None:
    """현재 관문 정책: 조회(mode=1)는 우회하고 예약내역(mode=0)은 거절. 재시도 1회."""
    from korail_mobile_api import KorailNetFunnelError

    world = World([RuntimeError("down"), RuntimeError("down")])
    client, sleeps = make_client(world)
    error = raises(client.get_reservation_history)
    check("f", isinstance(error, KorailNetFunnelError), f"mode=0: {type(error).__name__}")
    check("f", world.opcodes() == ["5101", "5101"], f"mode=0 순서 {world.opcodes()}")
    check("f", sleeps == [3.0, 3.0], f"마지막 실패도 timeout 대기 {sleeps}")

    world = World([RuntimeError("down"), "garbage"], korail=KORAIL_SEARCH)
    client, _ = make_client(world)
    error = raises(lambda: search(client))
    check("f", error is None, f"mode=1: {type(error).__name__}: {error}")
    check("f", world.opcodes() == ["5101", "5101", "KORAIL"], f"mode=1 순서 {world.opcodes()}")


def case_mode0_non_200() -> None:
    """mode=0 은 300/303 에서도 요청하지 않고, mode=1 은 보냅니다(키 없음 → 반납 없음)."""
    from korail_mobile_api import KorailNetFunnelError

    world = World(["300:key=&nwait=0"])
    client, _ = make_client(world)
    error = raises(client.get_reservation_history)
    check("g", isinstance(error, KorailNetFunnelError), f"mode=0: {type(error).__name__}")
    check("g", world.opcodes() == ["5101"], f"mode=0 순서 {world.opcodes()}")

    world = World(["303:key=&nwait=0"], korail=KORAIL_SEARCH)
    client, _ = make_client(world)
    check("g", raises(lambda: search(client)) is None, "mode=1 303 이 실패함")
    check("g", world.opcodes() == ["5101", "KORAIL"], f"mode=1 순서 {world.opcodes()}")
    aid = world.log[0][2].get("aid")
    check("g", aid == "act_8", f"조회 aid {aid}")


def case_wait_limit_and_override() -> None:
    from korail_mobile_api import KorailNetFunnelError

    world = World([f"201:key=K0&ttl=20&{NODE}", f"201:key=K1&ttl=20&{NODE}"])
    client, sleeps = make_client(
        world, netfunnel_wait_limit=30.0, netfunnel_actions={"reservation_view": "act_99"}
    )
    error = raises(client.get_reservation_history)
    check("h", isinstance(error, KorailNetFunnelError), f"{type(error).__name__}")
    check("h", "KORAIL" not in world.opcodes(), f"순서 {world.opcodes()}")
    check("h", sleeps == [20], f"대기 {sleeps}")
    check("h", world.completes() == [("rnf12.letskorail.com", "K1")], f"반납 {world.completes()}")
    check("h", world.log[0][2].get("aid") == "act_99", f"aid 덮어쓰기 {world.log[0][2]}")


def case_bad_node() -> None:
    from korail_mobile_api import KorailProtocolError

    world = World(["200:key=K1&ip=evil.example.com&port=443"])
    client, _ = make_client(world)
    error = raises(client.get_reservation_history)
    check("i", isinstance(error, KorailProtocolError), f"{type(error).__name__}")
    check("i", world.opcodes() == ["5101"], f"순서 {world.opcodes()}")


CASES = [
    case_immediate_pass,
    case_wait_then_pass,
    case_blocked,
    case_korail_raises,
    case_disabled,
    case_queue_down,
    case_mode0_non_200,
    case_wait_limit_and_override,
    case_bad_node,
]


def main() -> int:
    try:
        import httpx  # noqa: F401

        import korail_mobile_api  # noqa: F401
    except Exception as error:  # noqa: BLE001
        print(f"검사 불완전 — import 실패: {type(error).__name__}: {error}")
        return 2
    # case_queue_down 의 mode=1 우회는 경고 로그를 남깁니다 — 여기서는 소음입니다.
    logging.getLogger("korail_mobile_api").setLevel(logging.ERROR)
    incomplete: list[str] = []
    for case in CASES:
        try:
            case()
        except Exception as error:  # noqa: BLE001
            where = traceback.extract_tb(error.__traceback__)[-1]
            incomplete.append(
                f"{case.__name__}: {type(error).__name__}: {error}"
                f" ({pathlib.Path(where.filename).name}:{where.lineno})"
            )
    if failures:
        print(f"실패 {len(failures)}건")
        for line in failures:
            print("  " + line)
    if incomplete:
        print(f"검사 불완전 {len(incomplete)}건")
        for line in incomplete:
            print("  " + line)
        return 2
    if failures:
        return 1
    print(f"NetFunnel 오프라인 {len(CASES)}건 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
