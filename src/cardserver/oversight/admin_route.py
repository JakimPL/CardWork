from typing import Annotated

from fastapi import APIRouter, Depends, Header

from cardserver.identity.headers import ADMIN_HEADER
from cardserver.oversight.lobby.setting import LobbySetting
from cardserver.oversight.lobby.view import LobbyView
from cardserver.oversight.oversight import Oversight
from cardserver.oversight.posting import Posting
from cardserver.oversight.table_card import TableCard
from cardserver.protocols.table import TableId
from cardserver.schemas.closing import Closing


def admin_routes(oversight: Oversight) -> APIRouter:
    """The routes an overseer reads and runs the lobby through, every one of them behind the host's own token.

    Nothing here is open to a seat: the token this host was started under is asked for before any of it is read,
    so the panel answers to whoever runs the server and to nobody the server admits. What it holds is the lobby
    whole — the tables gathering and in play alike — and the levers over it: gathering a table, breaking one up,
    and settling how many stand and who may open them.

    Args:
        oversight: the overseer's view of the lobby, and the policy that tells the overseer apart.
    """
    router = APIRouter(prefix="/admin")

    def overseer(credential: Annotated[str | None, Header(alias=ADMIN_HEADER)] = None) -> None:
        """Confirm this request carries the token this host oversees under, before any of the panel is read."""
        oversight.confirm(credential)

    @router.get("/lobby", dependencies=[Depends(overseer)])
    async def read_lobby() -> LobbyView:
        """The whole lobby as the overseer reads it: every table, and the terms it is held under."""
        return oversight.lobby()

    @router.put("/lobby", dependencies=[Depends(overseer)])
    async def settle_lobby(setting: LobbySetting) -> LobbyView:
        """Settle the terms the lobby is held under: how many tables stand at once, and who may open one."""
        return oversight.adjust(setting)

    @router.post("/tables", dependencies=[Depends(overseer)])
    async def post_table(posting: Posting) -> TableCard:
        """Gather a table on the company's behalf, answering with the card that carries the code it admits on."""
        return oversight.post(posting)

    @router.post("/tables/{table_id}/closing", dependencies=[Depends(overseer)])
    async def close_table(table_id: str, closing: Closing) -> LobbyView:
        """Break one table up whether it is gathering or in play, and answer with the lobby it leaves behind."""
        await oversight.close(table_id, closing.reason)
        return oversight.lobby()

    @router.post("/reap", dependencies=[Depends(overseer)])
    async def reap_tables() -> tuple[TableId, ...]:
        """Clear away every table nobody is at that has sat too long, and answer with the names cleared."""
        return await oversight.reap()

    return router
