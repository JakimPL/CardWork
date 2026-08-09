from dataclasses import dataclass
from typing import Final

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.types import Receive, Scope, Send

from cardserver.keeping import ANSWERING, KEEPING, UNKEPT, Keeping
from tests.cases import Case, descriptions

from .conftest import BASE_URL, GATHERING, OFFERED, TABLES, arrives, holding

NAMED: Final[str] = "Ada"
NOWHERE: Final[str] = "/no-such-address"
A_YEAR: Final[str] = "public, max-age=31536000, immutable"
ANSWERED: Final[int] = 200
BODY: Final[str] = "http.response.body"


@dataclass(frozen=True)
class KeptCase(Case):
    """One address a client reads, and whether it speaks a token as it does."""

    address: str
    credentialled: bool


KEPT: Final[tuple[KeptCase, ...]] = (
    KeptCase(description="the games a host offers", address=OFFERED, credentialled=False),
    KeptCase(description="the tables gathering here", address=TABLES, credentialled=False),
    KeptCase(description="the gathering as a guest reads it", address=GATHERING, credentialled=True),
    KeptCase(
        description="a gathering asked for with no token, which is refused", address=GATHERING, credentialled=False
    ),
    KeptCase(description="an address this server answers for nothing", address=NOWHERE, credentialled=False),
)


@pytest.mark.parametrize("case", KEPT, ids=descriptions(KEPT))
async def test_an_answer_states_it_is_to_be_kept_nowhere(visitor: AsyncClient, case: KeptCase) -> None:
    """Every answer states its own policy, since a host settles one where an answer states none."""
    headers = holding(await arrives(visitor, NAMED)) if case.credentialled else {}
    answered = await visitor.get(case.address, headers=headers)

    assert answered.headers[KEEPING] == UNKEPT


async def test_an_answer_stating_a_policy_of_its_own_keeps_it() -> None:
    """A built interface says how long its files may be kept, and what it says is what reaches the browser."""

    async def kept(scope: Scope, receive: Receive, send: Send) -> None:
        await send(
            {
                "type": ANSWERING,
                "status": ANSWERED,
                "headers": [(KEEPING.encode(), A_YEAR.encode())],
            }
        )
        await send({"type": BODY, "body": b""})

    async with AsyncClient(
        transport=ASGITransport(app=Keeping(kept, UNKEPT)),
        base_url=BASE_URL,
    ) as client:
        answered = await client.get(NOWHERE)

    assert answered.headers[KEEPING] == A_YEAR
