from dataclasses import dataclass

from cardwork.cards.game import CardsOrJokers
from cardwork.combinations.pattern import Reading


@dataclass(frozen=True)
class Filling:
    """The cards a shape's places came to hold, beside what each of them reads as.

    `cards` are the cards themselves, a joker standing where the held cards left a place open, and
    `reading[place]` states what `cards[place]` reads as there.
    """

    cards: CardsOrJokers
    reading: Reading
