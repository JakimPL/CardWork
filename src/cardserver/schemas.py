from typing import Annotated, Final, Self

from pydantic import Field, field_validator, model_validator

from cardserver.protocol import TableId
from cardwork.decks.deck import Order
from cardwork.exceptions import GameValidationError
from cardwork.games.capacity import ONE_SEAT, Capacity
from cardwork.models.base import BaseFrozen
from cardwork.moves.move import Move
from cardwork.presentation.tint import Tint
from cardwork.rounds.conclusion import Conclusion
from cardwork.zones.zone import ZoneId

ONE_DECK: Final[int] = 1
NAME_LONGEST: Final[int] = 24


class MoveRequest(BaseFrozen):
    """A command as a client sends it: the intent, the position it was built on, and a name for the try.

    Repeating the key names the same attempt, so a client that retries a request it never saw answered
    lands its move once.
    """

    move: Move
    base_seq: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1)


class ArrangementRequest(BaseFrozen):
    """A seat laying a zone of its own out: the zone, the run it comes to lie in, and the position it was read at.

    The seat asking is the one thing this leaves out, since the server reads it off the credential: a client
    states which of its zones it is sorting and never whose zone that is.

    `order` names the positions the zone holds in the order they come to lie, so the first of them is the card
    that comes to lie first. Repeating the key names the same attempt, so a client that retries a request it
    never saw answered lands its order once.
    """

    zone: ZoneId
    order: Order
    base_seq: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1)


class CommandAccepted(BaseFrozen):
    """The sequence a command was committed at, which the table stands one commit past.

    A client holding this commit stands at `seq + 1` commits, and that count is what its next command quotes
    as `base_seq`. A move and an arrangement are answered alike, since what either of them leaves behind is
    one commit in the record every seat reads.
    """

    seq: int


class ErrorBody(BaseFrozen):
    """A refusal in the shape a client can act on: what kind it was, and what the server made of it.

    The kind is the name of the rule that refused, which lets a client branch on the answer while the
    detail stays a sentence for a person to read.
    """

    error: str
    detail: str


class Choice(BaseFrozen):
    """What a gathering has settled to play: the game, the table, the decks it is dealt from, and where it ends.

    This is what a table is opened with once the deal is called for, and every field of it is something the
    company settles rather than something the host fixes. The game is named as a plain word for the same reason
    a phase is: the vocabulary belongs to whatever holds the rules, and the adapter reads a name it confirms
    against what the host says it offers.
    """

    game: str
    players: Annotated[int, Field(ge=ONE_SEAT)]
    decks: Annotated[int, Field(ge=ONE_DECK)]
    conclusion: Conclusion


class Offering(BaseFrozen):
    """One game a host offers, the tables it seats and the deck counts it is dealt from.

    A client draws every control of a gathering from these, so a page settles a game while holding the name of
    none: what may be chosen is what the host says it offers, and a choice is confirmed against the same answer
    before a card is dealt.
    """

    game: str
    title: str
    seats: Capacity
    decks: tuple[int, ...]

    def confirm(self, choice: Choice) -> None:
        """Confirm this game is played the way a choice asks for.

        Raises:
            GameValidationError: when the game seats a table of another size, or is dealt from another count
                of decks.
        """
        self.seats.confirm(choice.players)
        if choice.decks not in self.decks:
            raise GameValidationError(
                f"{self.title} is dealt from {self._decks_spoken()}, and {choice.decks} were asked for"
            )

    def _decks_spoken(self) -> str:
        """The deck counts as a phrase, which is how a refusal states what a game is dealt from."""
        return f"{' or '.join(str(count) for count in self.decks)} decks"

    @model_validator(mode="after")
    def _a_game_states_the_decks_it_is_dealt_from(self) -> Self:
        """Confirm the offering names a count of decks the game is dealt from.

        Raises:
            ValueError: when no count is named, or when one of them falls short of a whole deck.
        """
        if not self.decks or any(count < ONE_DECK for count in self.decks):
            raise ValueError(f"A game is dealt from whole decks and names which counts, and these are: {self.decks}")

        return self


class Guest(BaseFrozen):
    """One person at a gathering as the company reads them: the name, the tint, the seat, and whether they are here.

    The name is what a guest arrived under and the whole of their identity at the table. The tint is what tells
    them apart from the rest of the company at a glance, and no two guests hold one. The seat is the one they
    have taken, and none while they are standing. Presence follows the stream a page holds open, so the company
    reads as the room does.
    """

    name: str
    tint: Tint
    seat: int | None
    present: bool


class GatheringView(BaseFrozen):
    """A gathering as one of its guests reads it: the company, what is settled, and where the gathering stands.

    `revision` counts the changes the gathering has been through, and a command quotes the one it was built on
    the way a move quotes a sequence, so two guests settling the choice at once leaves the second told rather
    than overruled. `dealt` turns true once, which is what carries every page from the gathering to the table.
    """

    table: TableId
    code: str
    company: tuple[Guest, ...]
    choice: Choice
    mine: str
    revision: Annotated[int, Field(ge=0)]
    dealt: bool


class Arriving(BaseFrozen):
    """One person arriving at a table: the code that admits them, and the name they will be read by."""

    code: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1, max_length=NAME_LONGEST)]

    @field_validator("name")
    @classmethod
    def _a_name_reads_at_the_table(cls, offered: str) -> str:
        """The name with the space around it trimmed off, which is how the company comes to read it.

        Raises:
            ValueError: when nothing but space was offered, or when a character of it shows nothing.
        """
        read = offered.strip()
        if not read:
            raise ValueError("A name is what the company reads a guest by, and this one holds nothing but space")

        if not read.isprintable():
            raise ValueError(f"A name reads at a table, and {offered!r} holds a character that shows nothing")

        return read


class Admitted(BaseFrozen):
    """What a guest is answered on arrival: the token they speak through, and the gathering they have joined.

    The token is the whole of what this server knows of them. It rides the fragment of an address, which a
    browser sends to nobody, and reaches every endpoint in a header of its own.
    """

    token: str
    gathering: GatheringView


class Claiming(BaseFrozen):
    """A guest taking a seat, or standing up from the one they hold by naming none."""

    seat: Annotated[int, Field(ge=0)] | None
    base_revision: Annotated[int, Field(ge=0)]


class Tinting(BaseFrozen):
    """A guest taking one of the company's tints, which is the mark the table tells them apart by."""

    tint: Tint
    base_revision: Annotated[int, Field(ge=0)]


class Choosing(BaseFrozen):
    """A guest settling what the table plays."""

    choice: Choice
    base_revision: Annotated[int, Field(ge=0)]


class Dealing(BaseFrozen):
    """A guest calling for the deal, which opens the table and ends the gathering."""

    base_revision: Annotated[int, Field(ge=0)]
