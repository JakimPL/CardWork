from typing import Optional

from cardwork.cards.deck import Variant
from cardwork.cards.game import GameCard


def pop_card(collection: Variant, index: Optional[int] = None) -> GameCard:
    if isinstance(collection, list) and index is not None:
        return collection.pop(index)

    return collection.pop()
