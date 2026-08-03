from collections import defaultdict
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Self

from cardwork.cards.card import Card, Cards
from cardwork.cards.game import CardOrJoker
from cardwork.cards.joker import Joker, Jokers
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.policy import Duplicates, Evaluation


@dataclass(frozen=True)
class Tally:
    """What a run of cards offers a combination, counted once so every question about it reads one figure.

    `of` reads a hand into one, and the reading it makes is what the search fills shapes from. The cards a
    reading admits are held three ways over: in one run from the strongest downwards, and indexed by rank and
    by suit, each index likewise strongest first. A combination asks for cards by rank, by suit, by both or by
    neither, so one of the three answers it directly. `wilds` are the jokers free to stand in for what a
    combination asks, which is what makes a hand reach further than the cards it holds.
    """

    naturals: Cards
    wilds: Jokers
    by_rank: Mapping[Rank, Cards]
    by_suit: Mapping[Suit, Cards]
    evaluation: Evaluation

    @classmethod
    def of(cls, cards: Iterable[CardOrJoker], evaluation: Evaluation) -> Self:
        """Read the cards once, so that every question the reading answers costs one pass over them."""
        naturals, wilds = cls._available(cards, evaluation)
        ranked = evaluation.card_order().descending(naturals)
        return cls(
            naturals=ranked,
            wilds=wilds,
            by_rank=cls._grouped(ranked, lambda card: card.rank),
            by_suit=cls._grouped(ranked, lambda card: card.suit),
            evaluation=evaluation,
        )

    @staticmethod
    def _available(
        cards: Iterable[CardOrJoker],
        evaluation: Evaluation,
    ) -> tuple[Cards, Jokers]:
        """The natural cards a combination may draw on, beside the jokers free to stand in for one."""
        held = tuple(cards)
        if evaluation.duplicates is Duplicates.COLLAPSE:
            held = tuple(dict.fromkeys(held))

        naturals = tuple(card for card in held if isinstance(card, Card))
        jokers = tuple(card for card in held if isinstance(card, Joker))
        return naturals, jokers if evaluation.wild_jokers else ()

    @staticmethod
    def _grouped[KeyT: Hashable](
        cards: Sequence[Card],
        named_by: Callable[[Card], KeyT],
    ) -> Mapping[KeyT, Cards]:
        """The cards indexed by the given reading of them, each group keeping the order it was given in."""
        groups: defaultdict[KeyT, list[Card]] = defaultdict(list)
        for card in cards:
            groups[named_by(card)].append(card)

        return {key: tuple(group) for key, group in groups.items()}
