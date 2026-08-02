from collections import deque
from typing import Optional

from pydantic import BaseModel, Field

from cardwork.board.decks import compare_decks
from cardwork.board.move import pop_card
from cardwork.cards.deck import Deck, Stack, Variant
from cardwork.cards.game import GameCard


class Board(BaseModel, extra="forbid"):
    public: dict[str, Variant]
    players: list[Variant]
    rejected: Stack = Field(default_factory=deque)
    starting_deck: Deck

    @property
    def public_cards(self) -> list[GameCard]:
        return sum(map(list, self.public.values()), [])

    @property
    def player_cards(self) -> list[GameCard]:
        return sum(map(list, self.players), [])

    def validate_board(self) -> None:
        public_cards = self.public_cards
        player_cards = self.player_cards
        rejected_cards = list(self.rejected)
        cards = public_cards + player_cards + rejected_cards
        if compare_decks(cards, self.starting_deck):
            raise ValueError("Cards don't match")

    def _reject(
        self,
        collection: Variant,
        index: Optional[int] = None,
    ) -> None:
        card = pop_card(collection, index)
        self.rejected.append(card)

    def discard_player_card(
        self,
        player: int,
        index: Optional[int] = None,
    ) -> None:
        player_cards = self.players[player]
        self._reject(player_cards, index)

    def discard_public_card(
        self,
        group: str,
        index: Optional[int] = None,
    ) -> None:
        public_cards = self.public[group]
        self._reject(public_cards, index)
