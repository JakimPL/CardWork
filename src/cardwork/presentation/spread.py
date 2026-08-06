from enum import StrEnum


class Spread(StrEnum):
    """How the cards of one zone lie against each other.

    `SLOT` is a single place, holding one card or standing empty. `STACK` is a heap, read by the card on top
    with the depth beneath it suggested. `FAN` overlaps cards so each stays partly readable, which is a hand
    held. `ROW` lays them side by side, each one whole.

    A heap reads by its last card, since that is the end a game lays on. A heap dealt from its other end
    holds cards nobody reads — a face-down pile is a heap of backs, and reads alike from either end — so the
    field saying which end faces up arrives with the first game that deals readable cards from position zero.
    """

    SLOT = "slot"
    STACK = "stack"
    FAN = "fan"
    ROW = "row"
