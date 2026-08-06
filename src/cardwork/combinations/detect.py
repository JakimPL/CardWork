from collections.abc import Iterable, Iterator

from cardwork.cards.game import CardOrJoker
from cardwork.combinations.assembly.assembly import Assembly
from cardwork.combinations.combination import BY_STRENGTH, Combination
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.selection import Selecting, Selection
from cardwork.combinations.tally import Tally


def instances(
    cards: Iterable[CardOrJoker],
    pattern: Pattern,
    evaluation: Evaluation,
) -> Iterator[Combination]:
    """Every instance of the pattern the cards hold, one per reading the pattern admits, strongest first.

    A reading that the cards answer yields the strongest instance of itself, so three kings yield the pair of
    kings once, read from the two strongest of them.
    """
    counted = Tally.of(cards, evaluation)
    for shape in pattern.shapes(evaluation):
        combination = Assembly(counted, pattern, shape).combination()
        if combination is not None:
            yield combination


def contains(
    cards: Iterable[CardOrJoker],
    pattern: Pattern,
    evaluation: Evaluation,
) -> bool:
    """Whether the cards hold the pattern somewhere among them, cards to spare being welcome."""
    return next(instances(cards, pattern, evaluation), None) is not None


def matches(
    cards: Iterable[CardOrJoker],
    pattern: Pattern,
    evaluation: Evaluation,
) -> bool:
    """Whether the cards are that combination and are all of it, every one of them taking a place in it.

    A set of cards answers to every pattern it forms, so A 2 3 4 5 of spades is a straight, a flush and a
    straight flush alike; a ranking is what states which of the three it counts as.
    """
    held = tuple(cards)
    return len(held) == pattern.size and contains(held, pattern, evaluation)


def find(
    cards: Iterable[CardOrJoker],
    pattern: Pattern,
    evaluation: Evaluation,
) -> Combination | None:
    """The strongest instance of the pattern the cards hold, or None where they hold none.

    Two instances of one strength are settled by the reading the pattern names first, which puts the higher
    suit ahead where suits are all that separate them.
    """
    found = tuple(instances(cards, pattern, evaluation))
    if not found:
        return None

    return max(found, key=BY_STRENGTH.key)


def find_all(
    cards: Iterable[CardOrJoker],
    pattern: Pattern,
    evaluation: Evaluation,
) -> tuple[Combination, ...]:
    """Every instance of the pattern the cards hold, from the strongest downwards."""
    return BY_STRENGTH.descending(instances(cards, pattern, evaluation))


def selections(
    cards: Iterable[CardOrJoker],
    pattern: Pattern,
    evaluation: Evaluation,
) -> tuple[Selection, ...]:
    """Every set of places in the run of cards whose cards are that pattern and are all of it.

    `find_all` reads one instance per reading the pattern admits, so three kings hold the pair of kings once.
    This reads the places instead, so those same three kings offer their pair three ways, and the cards each
    of them leaves behind are what tells the three moves apart. The readings the pattern names first lead, and
    each set of places comes out once.
    """
    held = tuple(cards)
    return tuple(
        dict.fromkeys(
            selection
            for shape in pattern.shapes(evaluation)
            for selection in Selecting(held, shape, evaluation).selections
        )
    )
