from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from typing import Annotated, ClassVar, Final

from pydantic import BeforeValidator, SerializeAsAny

from cardwork.cards.card import Cards
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.models.base import BaseFrozen
from cardwork.ordering.preorder import Key

type Reading = Cards

KIND: Final[str] = "kind"


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

    `kind` is the word the rule travels under, which each pattern states as the default of the field, and
    writing the class is what puts that word in play. `AnyPattern` reads a word back to the rule it names, so a
    pattern arrives off the wire as the class that wrote it: a game may carry a combination in its cursor, and a
    ranking chosen at the table — a bid contract, a rank named wild mid-hand — travels and replays as itself.
    """

    _rules: ClassVar[dict[str, type[Pattern]]] = {}

    kind: str

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: object) -> None:
        """Put the word a concrete pattern states in play, so that the wire form reads it back to this class.

        Raises:
            TypeError: when a pattern ready to be instantiated states no word of its own, or states one another
                pattern already travels under.
        """
        if cls.__abstractmethods__:
            return

        word = cls.model_fields[KIND].default
        if not isinstance(word, str):
            raise TypeError(f"{cls.__name__} is read back by the word naming its rule, and it states none")

        stated = Pattern._rules.get(word)
        if stated is not None and stated is not cls:
            raise TypeError(f"{word!r} already names {stated.__name__}, and {cls.__name__} states it as well")

        Pattern._rules[word] = cls

    @classmethod
    def named(cls, kind: str) -> type[Pattern]:
        """The rule one word names, out of the patterns in play.

        Raises:
            ValueError: when no pattern in play states that word.
        """
        stated = Pattern._rules.get(kind)
        if stated is None:
            words = ", ".join(sorted(Pattern._rules))
            raise ValueError(f"No rule travels under {kind!r}; the rules in play are {words}")

        return stated

    @property
    @abstractmethod
    def size(self) -> int:
        """How many cards the rule takes."""

    @property
    @abstractmethod
    def alike(self) -> bool:
        """Whether every place of every reading this rule admits asks the same of the card that fills it.

        Two of a rank ask alike, and so do five of a suit and three loose places; a run asks each of its places
        for a rank of its own. `Apart` reads this before it holds places apart by rank or by suit: where the
        places ask alike, every card showing one facing answers every one of them, and the filling settles
        which card takes which place.
        """

    @property
    def spread(self) -> bool:
        """Whether this rule holds any of its places apart, which `Apart` states and a compound carries on."""
        return False

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
        return tuple(
            sorted(
                (places[card.rank] for card in reading),
                reverse=True,
            )
        )


def _as_pattern(value: object) -> object:
    """The rule a wire form names, read back as the pattern class that word belongs to.

    A pattern travels as a mapping stating its `kind`, and the word settles which rule the fields beside it are
    read as, which is what lets a game's own pattern travel alongside the ones this package states. A pattern
    given as itself passes through, and so does anything else, for the field to validate and refuse.

    Raises:
        ValueError: when a mapping names its rule by no word, or by a word no pattern in play states.
    """
    if not isinstance(value, Mapping):
        return value

    kind = value.get(KIND)
    if not isinstance(kind, str):
        raise ValueError(f"A pattern names the rule it is by a word, and this one carries {kind!r}")

    return Pattern.named(kind).model_validate(value)


type AnyPattern = Annotated[
    SerializeAsAny[Pattern],
    BeforeValidator(_as_pattern),
]
