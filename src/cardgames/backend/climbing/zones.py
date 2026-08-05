from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.zones import presets
from cardwork.zones.zone import Zone, Zones
from cardwork.zones.zones import HANDS, STACK, discard


def climbing_zones(players: int, deck: Deck) -> Zones:
    """The table a climbing round is played on: a hand for each seat, the stack it plays onto, the discard beside it.

    A hand is the family standing at every seat, so `HANDS.name` is the word a play names its group by and the
    seat says which zone that word reaches. It lies face down, which its owner reads and the rest of the table
    reads the size of.

    The stack is the one pile of this game, holding the cards a round has yet to deal and the combinations it has
    put down: what a seat plays lands there face up, so the whole table reads the combination it stands on, and
    the deal of the next round gathers everything back into it. An equal share of the deck goes to every seat and
    what that leaves over lies face down on the discard, so a table of five dealt one standard deck sets two
    cards aside that nobody holds and nobody reads.
    """
    return {
        **HANDS.zones(players),
        STACK: Zone(
            id=STACK,
            visibility=presets.PILE,
            ordered=True,
            cards=to_game_cards(deck, face_down=True),
        ),
        **discard(),
    }
