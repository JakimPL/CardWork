import fcntl
import logging
import os
import signal
import socket
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import suppress
from http import HTTPStatus
from http.client import HTTPConnection, HTTPResponse
from json import dumps
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Final, NamedTuple
from urllib.parse import quote

HOME: Final[Path] = Path(__file__).resolve().parents[1]
PACKAGES: Final[Path] = HOME / "src"
CONFIGURATION: Final[Path] = HOME / "config.yaml"
LOG: Final[Path] = HOME / "table.log"
LOCK: Final[Path] = HOME / "table.lock"
STANDING: Final[Path] = HOME / "table.pid"
RESTART: Final[Path] = HOME / "tmp" / "restart.txt"

ADDRESS: Final[str] = "127.0.0.1"
PORT: Final[int] = 8421

CONNECT_PATIENCE: Final[float] = 10.0
STARTING_PATIENCE: Final[float] = 30.0
STOPPING_PATIENCE: Final[float] = 15.0
PROBE_PATIENCE: Final[float] = 0.5
BETWEEN_PROBES: Final[float] = 0.25
CHUNK: Final[int] = 65536

NEVER: Final[float] = 0.0
RECORDED: Final[int] = 2
NOT_OURS: Final[str] = "-"

REPORTED: Final[str] = "%(asctime)s %(levelname)s [%(process)d] passenger: %(message)s"
LISTENING: Final[int] = 0

HOP_BY_HOP: Final[frozenset[str]] = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
)

logging.basicConfig(
    level=logging.INFO,
    format=REPORTED,
    handlers=[logging.FileHandler(LOG, encoding="utf-8")],
)
LOGGER: Final[logging.Logger] = logging.getLogger("passenger")

Environ = dict[str, Any]
StartResponse = Callable[[str, list[tuple[str, str]]], object]


class Table(NamedTuple):
    """The table this entry last dealt with: the process it runs in, and the ask it was started for.

    A table this entry did not start runs in a process it names none, which is what leaves it standing where a
    restart would otherwise replace it.
    """

    process: int | None
    asked: float


def listening() -> bool:
    """Whether the table's own server answers on the port it is served behind."""
    with socket.socket() as probe:
        probe.settimeout(PROBE_PATIENCE)
        return probe.connect_ex((ADDRESS, PORT)) == LISTENING


def asked_afresh() -> float:
    """When a table was last asked for afresh, which is the moment the restart file carries.

    The file is the one a panel touches to restart an application and the one `touch tmp/restart.txt` names by
    hand. A checkout that has never been asked for afresh carries no such moment, and the table that answers
    stands as it is.
    """
    if not RESTART.is_file():
        return NEVER

    return RESTART.stat().st_mtime


def the_table_that_stands() -> Table | None:
    """The table this entry last started, and nothing where it has started none."""
    if not STANDING.is_file():
        return None

    stated = STANDING.read_text(encoding="utf-8").split()
    if len(stated) != RECORDED:
        return None

    try:
        return Table(None if stated[0] == NOT_OURS else int(stated[0]), float(stated[1]))
    except ValueError:
        return None


def remember(table: Table) -> None:
    """Write down which process the table runs in and which ask it stands for."""
    process = NOT_OURS if table.process is None else str(table.process)
    STANDING.write_text(f"{process} {table.asked}\n", encoding="utf-8")


def out_of_date() -> bool:
    """Whether the table answering now was started before a table was last asked for afresh."""
    asked = asked_afresh()
    if asked == NEVER:
        return False

    standing = the_table_that_stands()
    return standing is None or standing.asked < asked


def stop_the_table(process: int) -> None:
    """Stop the table that stands, and wait for the port to go quiet before another is started on it."""
    try:
        os.kill(process, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        LOGGER.error("process %d is not this account's to stop", process)
        return

    asked = monotonic()
    while monotonic() - asked < STOPPING_PATIENCE:
        if not listening():
            LOGGER.info("the table on process %d stopped after %.1f seconds", process, monotonic() - asked)
            return

        sleep(BETWEEN_PROBES)

    LOGGER.error("process %d held the port through %.0f seconds, ending it outright", process, STOPPING_PATIENCE)
    with suppress(ProcessLookupError):
        os.kill(process, signal.SIGKILL)


def retire_a_stale_table(asked: float) -> None:
    """Stop the table answering now where it was started before a table was last asked for afresh.

    A host's own restart recycles the workers this file is imported into and leaves the table alone, since the
    table is a session of its own by design and outliving a recycling is the point of that. The restart file is
    what carries the ask through to it, so a deploy takes hold on the panel's own button and on one `touch`.

    A table standing on a port this entry never started it on is a table only its operator can stop, and the
    log says so once per ask rather than at every request that finds it.
    """
    if asked == NEVER or not listening():
        return

    standing = the_table_that_stands()
    if standing is not None and standing.asked >= asked:
        return

    if standing is None or standing.process is None:
        LOGGER.error(
            "a table answers on %s:%d that this entry did not start, so the restart asked for reaches nothing"
            " — `pkill -f cardtable.cli` stops it, and the next request starts the checkout as it now stands",
            ADDRESS,
            PORT,
        )
        remember(Table(None, asked))
        return

    LOGGER.info(
        "process %d was started before the last ask for a table afresh, stopping it",
        standing.process,
    )
    stop_the_table(standing.process)


def surroundings() -> dict[str, str]:
    """What the table's process is started with, the checkout named among the places it imports from.

    A host runs this file under an interpreter of its own making, and the table is to be the package standing
    beside it rather than any other of that name. Naming the checkout here is what settles that, and whatever
    the host already stated is kept, since that is where its own installed packages are found.
    """
    stated = dict(os.environ)
    standing = [str(place) for place in (HOME, PACKAGES) if place.is_dir()]
    already = stated.get("PYTHONPATH")
    if already:
        standing.append(already)

    stated["PYTHONPATH"] = os.pathsep.join(standing)
    return stated


def start_the_table() -> None:
    """Start the one process the table lives in, and wait for it to answer.

    The lock is what makes this happen once: several workers reaching a stopped table all arrive here, and the
    first of them through starts it while the rest wait and find it answering. The process is started in a
    session of its own, so it outlives the worker that started it and every recycling Passenger does afterwards.

    A table asked for afresh is retired under the same lock, so the one that goes on to answer is the one the
    files now describe.
    """
    with LOCK.open("w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        asked = asked_afresh()
        retire_a_stale_table(asked)
        if listening():
            return

        if not CONFIGURATION.is_file():
            LOGGER.error(
                "no configuration stands at %s, which is the file a table is gathered from",
                CONFIGURATION,
            )
            return

        LOGGER.info("no table answers on %s:%d, starting one", ADDRESS, PORT)
        log = LOG.open("a", encoding="utf-8")
        try:
            started = subprocess.Popen(  # pylint: disable=consider-using-with
                [
                    sys.executable,
                    "-c",
                    "from cardtable.cli import main; main()",
                    "--config",
                    str(CONFIGURATION),
                    "--host",
                    ADDRESS,
                    "--port",
                    str(PORT),
                    "--forwarded-allow-ips",
                    ADDRESS,
                ],
                cwd=str(HOME),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=surroundings(),
            )
        finally:
            log.close()

        remember(Table(started.pid, asked))
        gathering = monotonic()
        while monotonic() - gathering < STARTING_PATIENCE:
            if listening():
                LOGGER.info(
                    "the table answers on process %d after %.1f seconds",
                    started.pid,
                    monotonic() - gathering,
                )
                return

            sleep(BETWEEN_PROBES)

        LOGGER.error(
            "no table answered inside %.0f seconds — read %s for what it said",
            STARTING_PATIENCE,
            LOG,
        )


def a_table_stands() -> None:
    """Make sure a table answers before a request is handed to it, and that it is the one now asked for."""
    if not listening() or out_of_date():
        start_the_table()


def headers_of(environ: Environ) -> list[tuple[str, str]]:
    """The headers a request carries, as the table is to read them.

    A server states them with the dashes turned to underscores and a prefix in front, apart from the two
    describing the body, which it states under names of their own. Every one of them is turned back into the
    header it was sent as, since a table reads its seat token, its resume point and the shape of a body out of
    exactly those names.

    The address the request came from goes on as a forwarding header, so the table counts a wrong code against
    the guest who offered it. It is the last word on the matter: whatever a caller sent under that name is
    dropped here, which is what keeps the count honest.
    """
    carried = [
        (name.removeprefix("HTTP_").replace("_", "-").lower(), str(value))
        for name, value in environ.items()
        if name.startswith("HTTP_")
    ]
    for stated, header in (("CONTENT_TYPE", "content-type"), ("CONTENT_LENGTH", "content-length")):
        if environ.get(stated):
            carried.append((header, str(environ[stated])))

    passing = [(name, value) for name, value in carried if name not in HOP_BY_HOP and name != "x-forwarded-for"]
    passing.append(("x-forwarded-for", str(environ.get("REMOTE_ADDR", ""))))
    passing.append(("x-forwarded-proto", str(environ.get("wsgi.url_scheme", "https"))))
    return passing


def body_of(environ: Environ) -> bytes:
    """The body a request carries, read to the length it states."""
    stated = environ.get("CONTENT_LENGTH")
    length = int(stated) if stated else 0
    if length <= 0:
        return b""

    return bytes(environ["wsgi.input"].read(length))


def address_of(environ: Environ) -> str:
    """Where a request is asking, written as it arrived on the wire."""
    path = quote(str(environ.get("PATH_INFO", "/")).encode("latin-1"))
    query = str(environ.get("QUERY_STRING", ""))
    return f"{path}?{query}" if query else path


def streaming(
    connection: HTTPConnection,
    answered: HTTPResponse,
) -> Iterator[bytes]:
    """The answer as it is written, a chunk at a time.

    An event stream is an answer that never ends: the table writes a frame whenever the room changes, and a
    page reads each one as it lands. Handing them over as they arrive is what keeps that true through here,
    and hanging up at the far end closes this connection, which is how the table learns a page has left.
    """
    try:
        while chunk := answered.read1(CHUNK):
            yield chunk
    finally:
        connection.close()


def unreached(start_response: StartResponse, trouble: OSError) -> list[bytes]:
    """What a caller is told when the table cannot be reached at all.

    The answer states a kind and a sentence, which is the shape the table states its own refusals in, so a page
    shown this puts the same kind of words in front of a person as it does for any other refusal.
    """
    LOGGER.error(
        "the table at %s:%d could not be reached: %s",
        ADDRESS,
        PORT,
        trouble,
    )
    body = dumps(
        {
            "error": "Unreached",
            "detail": "The table this page is served by is not answering just now — try again in a moment",
        }
    ).encode("utf-8")
    start_response(
        f"{HTTPStatus.BAD_GATEWAY.value} {HTTPStatus.BAD_GATEWAY.phrase}",
        [("content-type", "application/json"), ("content-length", str(len(body)))],
    )
    return [body]


def application(
    environ: Environ,
    start_response: StartResponse,
) -> Iterator[bytes] | list[bytes]:
    """One request handed to the table, and its answer handed back as it is written."""
    a_table_stands()
    connection = HTTPConnection(ADDRESS, PORT, timeout=CONNECT_PATIENCE)
    try:
        connection.connect()
        if connection.sock is not None:
            connection.sock.settimeout(None)

        connection.request(
            str(environ.get("REQUEST_METHOD", "GET")),
            address_of(environ),
            body=body_of(environ),
            headers=dict(headers_of(environ)),
        )
        answered = connection.getresponse()
    except OSError as trouble:
        connection.close()
        return unreached(start_response, trouble)

    start_response(
        f"{answered.status} {answered.reason}",
        [(name.lower(), value) for name, value in answered.getheaders() if name.lower() not in HOP_BY_HOP],
    )
    return streaming(connection, answered)
