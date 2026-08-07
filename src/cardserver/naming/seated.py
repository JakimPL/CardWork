from cardwork.models.base import BaseFrozen
from cardwork.presentation.tint import Tint


class Seated(BaseFrozen):
    """One seat as the table it was dealt into reads it: the name its guest took it under, and their tint.

    This is the whole of what a gathering has to say about a player, and it is what a plaque carries: who is
    there, and which of the company's tints tells them apart from the rest.
    """

    name: str
    tint: Tint
