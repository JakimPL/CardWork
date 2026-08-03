from abc import ABC, abstractmethod
from collections.abc import Iterator

from cardwork.cards.card import Cards
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.models.base import BaseFrozen
from cardwork.ordering.preorder import Key

type Reading = Cards


class Pattern(BaseFrozen, ABC):
    """A rule a set of cards can answer, such as two of a rank or five of a suit.

    Every question this package asks is asked about a pattern: `matches` tests a run of cards against one,
    `contains` looks for one among them, `find` reads out the strongest instance the cards hold, and a
    `Ranking` lists the patterns a game recognises. Patterns compose, so `Beside(parts=(TRIPLET, PAIR))` is a
    full house and `Together(parts=(STRAIGHT, FLUSH))` a straight flush, and `str(pattern)` says a rule in
    words. `cardwork.combinations.poker` states the familiar ones.

    A game states a rule of its own by writing a pattern: `size` is how many cards the rule takes, `shapes`
    lists the readings it admits over a given reading of the deck, and `strength` places one instance among
    the others of the same rule.
    """

    @property
    @abstractmethod
    def size(self) -> int:
        """How many cards the rule takes."""

    @abstractmethod
    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        """Every reading this rule admits over that reading of the deck, the strongest first."""

    @abstractmethod
    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        """Where an instance reading these cards stands among the others of this rule."""

    @abstractmethod
    def __str__(self) -> str:
        """The rule in words, as a game would state it."""

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def _descending_ranks(reading: Reading, evaluation: Evaluation) -> Key:
        """The places these ranks take from the highest down, which a rule naming no rank of its own keys on."""
        places = evaluation.rank_places()
        return tuple(sorted((places[card.rank] for card in reading), reverse=True))
