from collections.abc import Iterable, Mapping
from typing import Final, Self

from pydantic import model_validator

from cardwork.cards.card import Card
from cardwork.cards.game import CardOrJoker
from cardwork.cards.rank import Rank
from cardwork.models.base import BaseFrozen

HIGH_CARD_POINTS: Final[int] = 10
LOW_ACE_POINTS: Final[int] = 1
JOKER_POINTS: Final[int] = 0


class PointTable(BaseFrozen):
    """What each rank is worth to a game that counts its cards, beside the worth of a joker.

    Scoring is a game's own affair, so this is vocabulary rather than rule: the tables below carry the
    common reading, and a game that counts differently states its own.
    """

    values: Mapping[Rank, int]
    joker: int

    @model_validator(mode="after")
    def _every_rank_carries_a_worth(self) -> Self:
        unscored = tuple(rank for rank in Rank if rank not in self.values)
        if unscored:
            raise ValueError(f"A point table scores every rank, and these are left out: {unscored}")

        return self

    def of(self, card: CardOrJoker) -> int:
        """What one card is worth here."""
        return self.values[card.rank] if isinstance(card, Card) else self.joker

    def total(self, cards: Iterable[CardOrJoker]) -> int:
        """What a run of cards is worth here, counting every one of them."""
        return sum(self.of(card) for card in cards)


REGULAR_POINTS: Final[PointTable] = PointTable(
    values={rank: int(rank.value) if rank.pip else HIGH_CARD_POINTS for rank in Rank},
    joker=JOKER_POINTS,
)
ACE_LOW_POINTS: Final[PointTable] = PointTable(
    values={**REGULAR_POINTS.values, Rank.ACE: LOW_ACE_POINTS},
    joker=JOKER_POINTS,
)
