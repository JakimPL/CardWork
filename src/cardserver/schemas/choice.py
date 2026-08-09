from typing import Annotated

from pydantic import Field

from cardwork.decks.standard import ONE_DECK
from cardwork.games.capacity import ONE_SEAT
from cardwork.models.base import BaseFrozen
from cardwork.rounds.conclusion import Conclusion


class Choice(BaseFrozen):
    """What a gathering has settled to play: the game, the table, the decks it is dealt from, and where it ends.

    This is what a table is opened with once the deal is called for, and every field of it is something the
    company settles rather than something the host fixes. The game is named as a plain word for the same reason
    a phase is: the vocabulary belongs to whatever holds the rules, and the adapter reads a name it confirms
    against what the host says it offers.

    `cues` is the one field the rules read nothing of: whether the table lights the cards a seat may play, which
    a company settles like the rest and an advanced one turns off. It travels with the choice so a page settles
    it beside the game and it reaches the table the deal opens, where the layout carries it to every seat.
    """

    game: str
    players: Annotated[int, Field(ge=ONE_SEAT)]
    decks: Annotated[int, Field(ge=ONE_DECK)]
    conclusion: Conclusion
    cues: bool = True
