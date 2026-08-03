from typing import Final

from cardwork.cards.cards import STANDARD_CARDS
from cardwork.cards.game import is_joker
from cardwork.decks.deck import Deck, GameDeck
from cardwork.decks.decks import compare_decks, count_cards, jokers

ONE_DECK: Final[int] = 1
NO_WHOLE_DECKS: Final[int] = 0


def standard_decks(
    count: int,
    *,
    black_jokers: int,
    red_jokers: int,
) -> Deck:
    """`count` whole standard decks laid together, and the jokers a host asks for besides.

    Several decks in play let a card be held twice, which a game reads through the duplicates policy of its
    own evaluation.

    Raises:
        ValueError: when fewer than one deck is asked for.
    """
    if count < ONE_DECK:
        raise ValueError(f"A deck is made of at least {ONE_DECK} standard deck, and {count} were asked for")

    return (
        *(card for _ in range(count) for card in STANDARD_CARDS),
        *jokers(
            black=black_jokers,
            red=red_jokers,
        ),
    )


def standard_deck(
    *,
    black_jokers: int = 0,
    red_jokers: int = 0,
) -> Deck:
    return standard_decks(
        ONE_DECK,
        black_jokers=black_jokers,
        red_jokers=red_jokers,
    )


def standard_multiplicity(deck: GameDeck) -> int:
    """How many whole standard decks the suited cards of a deck make, and `NO_WHOLE_DECKS` where they make none.

    Jokers stand outside the count, so two standard decks beside three jokers make two. A game played with
    whole decks reads this to accept the deck it was handed.
    """
    suited = {card: held for card, held in count_cards(deck).items() if not is_joker(card)}
    if set(suited) != set(STANDARD_CARDS):
        return NO_WHOLE_DECKS

    fewest, most = min(suited.values()), max(suited.values())
    return fewest if fewest == most else NO_WHOLE_DECKS


def is_standard_deck(
    deck: GameDeck,
    *,
    black_jokers: int = 0,
    red_jokers: int = 0,
) -> bool:
    return compare_decks(
        deck,
        standard_deck(
            black_jokers=black_jokers,
            red_jokers=red_jokers,
        ),
    )
