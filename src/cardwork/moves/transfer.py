from typing import ParamSpec, TypeVar

from cardwork.decks.deck import GameCards, Indices

P = ParamSpec("P")
R = TypeVar("R")
S = TypeVar("S")


def validate_indices(
    cards: GameCards,
    indices: Indices,
) -> None:
    if not indices:
        return

    max_index = max(indices)
    size = len(cards)
    if max_index >= size:
        raise KeyError(f"Index {max_index} exceeds the size {size} of the collections")


def pop_cards(
    cards: GameCards,
    remove: Indices,
) -> tuple[GameCards, GameCards]:
    kept = tuple(card for i, card in enumerate(cards) if i not in remove)
    popped = tuple(card for i, card in enumerate(cards) if i in remove)
    return kept, popped
