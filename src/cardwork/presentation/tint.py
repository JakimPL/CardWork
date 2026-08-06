from enum import StrEnum


class Tint(StrEnum):
    """One player as the table tells them apart from the next, beside the name they play under.

    A seat is read by its name, and a company round one table reads faster for a mark that carries at a
    glance: the plaque, the cards and the place a player holds all say the same one of these. Which player
    holds which is settled where a company gathers, and a table stands under as many tints as it seats.

    What a tint comes to on a screen is the interface's, as the colour of a highlight is: these name eight
    players apart and say nothing about how any of them is drawn.
    """

    ROSE = "rose"
    CORAL = "coral"
    AMBER = "amber"
    LEMON = "lemon"
    TEAL = "teal"
    AZURE = "azure"
    INDIGO = "indigo"
    VIOLET = "violet"
