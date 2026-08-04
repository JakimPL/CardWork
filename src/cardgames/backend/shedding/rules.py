from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.game import CardOrJoker
from cardwork.cards.orders import RANK_SEQUENCE, SUIT_SEQUENCE
from cardwork.cards.rank import Rank
from cardwork.combinations.detect import matches
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.policy import Duplicates, Evaluation
from cardwork.decks.deck import Indices
from cardwork.states.state import Points

HAND_SIZE: Final[int] = 4
SHED_LEAST: Final[int] = 2
ONE_CARD: Final[int] = 1
ROUND_POINT: Final[int] = 1
NOTHING: Final[int] = 0
NO_CARDS: Final[int] = 0

SHEDDING_EVALUATION: Final[Evaluation] = Evaluation(
    ranks=RANK_SEQUENCE,
    suits=SUIT_SEQUENCE,
    wheel=False,
    wild_jokers=False,
    duplicates=Duplicates.COUNT,
)


def ranked(card: CardOrJoker) -> Rank:
    """The rank a card reads as, which every card of the deck this game is played with carries.

    Raises:
        ValueError: when the card is a joker, which the one standard deck of this game holds none of.
    """
    if isinstance(card, Card):
        return card.rank

    raise ValueError(f"This game is played with suited cards alone, and read {card}")


def reads_alike(cards: Sequence[CardOrJoker]) -> bool:
    """Whether the cards are a set: two of them or more, every one reading as the one rank.

    This is the whole rule a shed is held to, and `SameRank` at as many places as there are cards states it:
    a pair, a triplet and four of a rank all answer to it, and cards of two ranks answer to none of them.
    """
    return len(cards) >= SHED_LEAST and matches(
        cards,
        SameRank(places=len(cards)),
        SHEDDING_EVALUATION,
    )


def alike_places(hand: Sequence[CardOrJoker]) -> Mapping[Rank, tuple[int, ...]]:
    """The positions of a hand filed under the rank the card standing at each of them reads as."""
    places: dict[Rank, tuple[int, ...]] = {}
    for place, card in enumerate(hand):
        rank = ranked(card)
        places[rank] = places.get(rank, ()) + (place,)

    return places


def holds_a_set(hand: Sequence[CardOrJoker]) -> bool:
    """Whether the hand holds a set to shed, which is two of its cards or more reading as one rank."""
    return any(len(places) >= SHED_LEAST for places in alike_places(hand).values())


def sets_in(hand: Sequence[CardOrJoker]) -> tuple[Indices, ...]:
    """Every set of positions a hand may shed, from a pair of one rank up to the whole of that rank.

    A set is drawn from the positions one rank stands at, so every one of them reads alike by construction,
    and the ranks of a hand are what keeps the list short: a hand offers as many sets as its repeated ranks
    hold subsets, rather than as many as its positions do.
    """
    return tuple(
        frozenset(chosen)
        for places in alike_places(hand).values()
        for size in range(SHED_LEAST, len(places) + 1)
        for chosen in combinations(places, size)
    )


def drawn_from(stock: int) -> Indices:
    """The position a draw takes, which is the card lying at the end of the stock.

    A stock of backs reads alike from either end, so this game draws from the end its players point at: an
    interface reads a heap by the last card of the run (`presentation.spread.Spread`), and that is the card a
    seat clicking the stock has picked out. The deal takes from the other end, which a shuffled pile is as
    indifferent to.

    Args:
        stock: how many cards the stock holds.

    Raises:
        ValueError: when the stock has run out, which leaves no card to draw.
    """
    if stock <= NO_CARDS:
        raise ValueError("A draw takes the card at the end of the stock, and the stock has run out")

    return frozenset({stock - ONE_CARD})


def may_act(hand: Sequence[CardOrJoker], stock: int) -> bool:
    """Whether a seat has a turn to take: a set in hand to shed, or a stock still holding a card to draw.

    Args:
        hand: the cards the seat holds.
        stock: how many cards the stock holds.
    """
    return stock > NO_CARDS or holds_a_set(hand)


def taken_by(hands: Sequence[int]) -> Points:
    """The round's award: the point it is worth to each seat left holding the fewest cards.

    A seat that sheds its last card holds none, which is the fewest a hand runs to, so a seat going out takes
    the round it closes. A round the stock ran out of goes to the shortest hand at the table, and to each of
    them where several stand as short as one another.

    Args:
        hands: how many cards each seat holds, in seat order.
    """
    fewest = min(hands)
    return tuple(ROUND_POINT if held == fewest else NOTHING for held in hands)


def gone_out(hands: Sequence[int]) -> int | None:
    """The seat that shed its last card, and None where every seat is still holding one.

    Args:
        hands: how many cards each seat holds, in seat order.
    """
    return next((seat for seat, held in enumerate(hands) if held == NO_CARDS), None)
