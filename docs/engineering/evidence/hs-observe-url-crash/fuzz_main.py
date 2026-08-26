"""main() 퍼징 — goal 문서의 `crash=0 bad_exit=0 multiline=0` 을 재현한다.

게이트가 아니다. seed 와 입력 목록을 소스에 고정해 남이 같은 숫자를 얻게 하는 것이 목적이다.
실행: cd humansearch && PYTHONPATH=src uv run --no-sync python ../docs/engineering/evidence/hs-observe-url-crash/fuzz_main.py
"""

import io
import json
import random
import sys

from humansearch import observe
from humansearch.auth_surface import SurfaceRole

SEED = 20260825
CONTRACT = observe.MarkerContract(
    channel="saramin",
    diagnostic_host="127.0.0.1",
    diagnostic_ports=frozenset({9225}),
    targets_path="/json/list",
    allowed_origins=frozenset({"https://portal.invalid"}),
    loggable_paths=frozenset({"/home"}),
    surface_markers=("header",),
    role_markers={role: (f"{role.value}-marker",) for role in SurfaceRole},
)
ALPHABET = (
    "abc./:@?#[]%-_0123456789"
    + " \t\n\r\x00\x0b\x0c\x1c\x85"
    + "  \ud800￿℀ﬀ。＃"
)
HOST = "https://portal.invalid"


def _run(body: bytes) -> tuple[int | None, str, str | None]:
    class Response:
        status = 200

        def read(self, amount: int) -> bytes:
            return body

    class Connection:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            pass

        def request(self, method: str, path: str, headers: object) -> None:
            pass

        def getresponse(self) -> Response:
            return Response()

        def close(self) -> None:
            pass

    observe.HTTPConnection = Connection  # type: ignore[misc]
    buffer = io.StringIO()
    saved = sys.stdout
    sys.stdout = buffer
    try:
        return observe.main(["--channel", "saramin", "--port", "9225", "--once"]), buffer.getvalue(), None
    except BaseException as exc:  # noqa: BLE001 - 퍼저는 모든 탈출을 세야 한다
        return None, buffer.getvalue(), f"{type(exc).__name__}: {exc}"
    finally:
        sys.stdout = saved


def main() -> int:
    observe._load_contract = lambda channel: CONTRACT  # type: ignore[assignment]
    observe.observe_markers = lambda *a, **k: {"contract_valid": True, "matched_roles": []}  # type: ignore[assignment]

    rng = random.Random(SEED)
    urls = [HOST + "/home", HOST, HOST + ":444/home", "https://[::1", ""]
    for _ in range(500):
        urls.append("".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 40))))
    for _ in range(500):
        urls.append("https://" + "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 25))))
    for _ in range(500):
        urls.append(HOST + "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 15))))

    bodies = [
        json.dumps([{"type": "page", "url": u, "webSocketDebuggerUrl": "ws"}]).encode()
        for u in urls
    ]
    bodies += [
        b"[" * 300000 + b"]" * 300000,
        b"[]",
        b"null",
        b"[" + b"1" * 4301 + b"]",
        b"\xff",
        b"[{}]",
        b'[{"type":"page","url":1,"webSocketDebuggerUrl":null}]',
    ]

    crash = bad_exit = multiline = 0
    for body in bodies:
        code, out, err = _run(body)
        if err is not None:
            crash += 1
            print(f"CRASH: {err[:80]}")
        elif code not in (0, 2):
            bad_exit += 1
            print(f"BAD_EXIT: {code}")
        elif len(out.rstrip("\n").splitlines()) != 1:
            multiline += 1
            print(f"MULTILINE: {out!r}")
    print(f"seed={SEED} total={len(bodies)} crash={crash} bad_exit={bad_exit} multiline={multiline}")
    return 0 if crash == bad_exit == multiline == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
