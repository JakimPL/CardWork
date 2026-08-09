from typing import Self

from pydantic import model_validator

from cardserver.schemas.choice import Choice
from cardwork.decks.standard import ONE_DECK
from cardwork.exceptions import GameValidationError
from cardwork.games.capacity import Capacity
from cardwork.models.base import BaseFrozen


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
