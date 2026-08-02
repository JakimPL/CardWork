from collections import Counter

from cardwork.cards.game import CardOrJoker, GameCard, is_joker
from cardwork.cards.joker import Joker
from cardwork.decks.deck import Deck, GameDeck


def normalize_deck(deck: GameDeck) -> list[CardOrJoker]:
    return [game_card.card if isinstance(game_card, GameCard) else game_card for game_card in deck]


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
