from collections import Counter
from collections.abc import Sequence

from cardwork.cards.game import CardOrJoker, CardsOrJokers, GameCard, is_joker
from cardwork.cards.joker import Joker
from cardwork.decks.deck import Deck, GameCards, GameDeck, Indices


def normalize_deck(deck: GameDeck) -> list[CardOrJoker]:
    return [game_card.card if isinstance(game_card, GameCard) else game_card for game_card in deck]


def named(cards: Sequence[CardOrJoker], indices: Indices) -> CardsOrJokers:
    """The cards standing at the given places of a run, in the order the run holds them.

    A client names the cards it plays by where they stand in the run it was shown, so this is the step from
    the places a move carries to the cards a rule reads. The cards come back in the run's own order, which
    leaves the reading the same whichever way a client named the places.

    Raises:
        KeyError: when a place lies past the end of the run.
    """
    size = len(cards)
    if indices and max(indices) >= size:
        raise KeyError(f"Place {max(indices)} lies past the {size} cards of the run")

    return tuple(card for place, card in enumerate(cards) if place in indices)


def to_game_cards(deck: GameDeck, *, face_down: bool) -> GameCards:
    """Wrap bare cards for play, giving every one of them the same face.

    Zones hold `GameCard`s, so this is the step between a deck definition and a board layout.
    """
    return tuple(GameCard(card=card, face_down=face_down) for card in normalize_deck(deck))


def count_cards(deck: GameDeck) -> Counter[CardOrJoker]:
    normalized_deck = normalize_deck(deck)
    return Counter(normalized_deck)


def compare_decks(deck1: GameDeck, deck2: GameDeck) -> bool:
    counter1 = count_cards(deck1)
    counter2 = count_cards(deck2)
    return counter1 == counter2


def does_contain_jokers(deck: GameDeck) -> bool:
    for game_card in deck:
        if is_joker(game_card):
            return True

    return False


def jokers(
    black: int = 0,
    red: int = 0,
) -> Deck:
    jokers_count = black + red
    return tuple(Joker(red=index >= black) for index in range(jokers_count))
