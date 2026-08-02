from collections import deque

from pydantic import BaseModel, Field

from cardwork.decks.deck import Deck, Group, Stack, Variant
from cardwork.decks.decks import compare_decks
from cardwork.moves.actions import Discard, Give, Play, Reject, Take
from cardwork.moves.transfer import transfer_cards


class Board(BaseModel, extra="forbid"):
    starting_deck: Deck
    public: dict[str, Variant] = Field(default_factory=dict)
    players: list[Variant] = Field(default_factory=list)
    discarded: Stack = Field(default_factory=deque)

    @property
    def public_cards(self) -> Group:
        return sum(map(list, self.public.values()), [])

    @property
    def player_cards(self) -> Group:
        return sum(map(list, self.players), [])

    def validate_board(self) -> None:
        public_cards = self.public_cards
        player_cards = self.player_cards
        rejected_cards = list(self.discarded)
        cards = public_cards + player_cards + rejected_cards
        if compare_decks(cards, self.starting_deck):
            raise ValueError("Cards don't match")

        for card in self.discarded:
            if not card.hidden:
                raise ValueError(f"Card {card.card} is supposed to be hidden in the rejected stack")

    @transfer_cards
    def _play(self, cards: Group, group: str) -> None:
        public_cards = self.public[group]
        public_cards.extend(cards)

    @transfer_cards
    def _take(self, cards: Group, player: int) -> None:
        player_cards = self.players[player]
        player_cards.extend(cards)

    @transfer_cards
    def _give(self, cards: Group, player: int) -> None:
        for card in cards:
            card.hidden = True

        player_cards = self.players[player]
        player_cards.extend(cards)

    @transfer_cards
    def _discard(self, cards: Group) -> None:
        self.discarded.extend(cards)

    def play(
        self,
        player: int,
        action: Play,
    ) -> None:
        player_cards = self.players[player]
        self._play(player_cards, action.indices, action.group)

    def take(
        self,
        player: int,
        action: Take,
    ) -> None:
        public_cards = self.public[action.group]
        self._take(public_cards, action.indices, player)

    def give(
        self,
        player: int,
        action: Give,
    ) -> None:
        player_cards = self.players[player]
        self._give(player_cards, action.indices, action.target_player)

    def reject(
        self,
        player: int,
        action: Reject,
    ) -> None:
        player_cards = self.players[player]
        self._discard(player_cards, action.indices)

    def discard(
        self,
        action: Discard,
    ) -> None:
        public_cards = self.public[action.group]
        self._discard(public_cards, action.indices)
