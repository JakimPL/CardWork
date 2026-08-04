from pathlib import Path
from time import sleep
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TIMEOUT: Final[float] = 30.0
ATTEMPTS: Final[int] = 4
PAUSE: Final[float] = 2.0
SERVER_ERROR: Final[int] = 500
AGENT: Final[str] = "CardWork/0.1 (card artwork for local play)"


def answered(request: Request) -> bytes:
    """The bytes one request is answered with."""
    with urlopen(request, timeout=TIMEOUT) as answer:
        body: bytes = answer.read()

    return body


def passing(error: URLError) -> bool:
    """Whether one failure is the kind that answers differently a moment later.

    A host turning a request away for the moment says so with a status of its own making, and a host saying
    the address names nothing will say the same however long a fetch waits.
    """
    if isinstance(error, HTTPError):
        return error.code >= SERVER_ERROR

    return True


def read(url: str) -> bytes:
    """The bytes one address answers with, asked again after a pause where the answer was a passing failure.

    An archive answering many requests at once turns some of them away for a moment, and the artwork a pack
    is built from is fetched a file at a time, so a build waits out the moment rather than falling over it.

    Raises:
        URLError: when the address names nothing, or when every attempt at it is turned away.
    """
    request = Request(url, headers={"User-Agent": AGENT})
    for attempt in range(1, ATTEMPTS):
        try:
            return answered(request)
        except URLError as error:
            if not passing(error):
                raise

            sleep(PAUSE * attempt)

    return answered(request)


def fetch(url: str, into: Path) -> int:
    """Fetch one file to a path, making the directories above it, and answer with how many bytes landed."""
    body = read(url)
    into.parent.mkdir(parents=True, exist_ok=True)
    into.write_bytes(body)
    return len(body)


def cached(url: str, into: Path, *, refresh: bool) -> bytes:
    """The bytes of one file, fetched where the path holds none and read off the path from then on.

    A build reads its sources many times over as it cuts a pack out of them, and a run after a run costs one
    read of the disk; `refresh` fetches afresh where an upstream has moved.
    """
    if into.exists() and not refresh:
        return into.read_bytes()

    fetch(url, into)
    return into.read_bytes()
