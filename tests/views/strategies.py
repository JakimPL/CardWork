from typing import Final

from hypothesis import strategies as st

from cardwork.boards.board import Board
from cardwork.cards.card import Card
from cardwork.cards.game import CardOrJoker, GameCard
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.decks.deck import GameCards
from cardwork.effects.effects import MoveCards
from cardwork.moves.actions import Play
from cardwork.moves.move import Move
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.transactions.transaction import Transaction
from cardwork.zones.presets import HAND, HIDDEN, PILE
from cardwork.zones.resolution import visible_to
from cardwork.zones.zone import Zone, ZoneId, Zones

MAX_PLAYERS: Final[int] = 4
POOL: Final[tuple[CardOrJoker, ...]] = tuple(
    Card(rank=rank, suit=suit) for rank in (Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK) for suit in Suit
)
PHASES: Final[tuple[str, ...]] = ("deal", "arrange", "play", "reveal", "score")

Slot = tuple[ZoneId, int]
Commit = tuple[Transaction[GameState], Position[GameState], Position[GameState]]


def empty_zones(players: int) -> Zones:
    """A table laid out to exercise every row of the visibility table at the given seat count."""
    seated: Zones = {
        f"hand:{seat}": Zone(
            id=f"hand:{seat}",
            owner=seat,
            visibility=HAND,
            ordered=False,
        )
        for seat in range(players)
    }
    blinds: Zones = {
        f"blind:{seat}": Zone(
            id=f"blind:{seat}",
            owner=seat,
            visibility=PILE,
            ordered=True,
        )
        for seat in range(players)
    }
    shared: Zones = {
        "draw": Zone(
            id="draw",
            visibility=PILE,
            ordered=True,
        ),
        "discard": Zone(
            id="discard",
            visibility=PILE,
            ordered=True,
        ),
        "vault": Zone(
            id="vault",
            visibility=HIDDEN,
            ordered=True,
        ),
    }
    return {**seated, **blinds, **shared}


@st.composite
def positions(draw: st.DrawFn) -> Position[GameState]:
    """A table of up to four seats with the pool spread arbitrarily across its zones, faces either way."""
    players = draw(st.integers(min_value=1, max_value=MAX_PLAYERS))
    layout = empty_zones(players)
    dealt = draw(st.permutations(POOL))
    placements = draw(
        st.lists(st.tuples(st.sampled_from(sorted(layout)), st.booleans()), max_size=len(POOL)),
    )

    held: dict[ZoneId, list[GameCard]] = {zone_id: [] for zone_id in layout}
    for card, (zone_id, face_down) in zip(dealt, placements):
        held[zone_id].append(GameCard(card=card, face_down=face_down))

    zones = {zone_id: zone.with_cards(tuple(held[zone_id])) for zone_id, zone in layout.items()}
    deck = tuple(game_card.card for zone in zones.values() for game_card in zone.cards)
    return Position(board=Board(starting_deck=deck, zones=zones), state=draw(states(players)), players=players)


@st.composite
def states(draw: st.DrawFn, players: int) -> GameState:
    return GameState(
        phase=draw(st.sampled_from(PHASES)),
        to_act=frozenset(draw(st.sets(st.integers(min_value=0, max_value=players - 1)))),
        points=draw(st.one_of(st.none(), st.tuples(*(st.integers(min_value=-9, max_value=99),) * players))),
    )


@st.composite
def observers(draw: st.DrawFn, players: int) -> int | None:
    return draw(st.one_of(st.none(), st.integers(min_value=0, max_value=players - 1)))


@st.composite
def commits(draw: st.DrawFn) -> Commit:
    """A commit that moves one card between two zones, together with the positions on either side of it."""
    before = draw(positions())
    filled = sorted(zone_id for zone_id, zone in before.board.zones.items() if zone.cards)
    move = draw(st.one_of(st.none(), moves(before.players)))
    seq = draw(st.integers(min_value=0, max_value=99))
    if not filled:
        return Transaction(seq=seq, move=move, effects=()), before, before

    source = draw(st.sampled_from(filled))
    effect: MoveCards[GameState] = MoveCards(
        source=source,
        indices=frozenset({draw(st.integers(min_value=0, max_value=len(before.board.zone(source).cards) - 1))}),
        target=draw(st.sampled_from(sorted(before.board.zones))),
        face_down=draw(st.one_of(st.none(), st.booleans())),
    )
    return Transaction(seq=seq, move=move, effects=(effect,)), before, effect.apply(before)


@st.composite
def moves(draw: st.DrawFn, players: int) -> Move:
    return Move(
        player=draw(st.integers(min_value=0, max_value=players - 1)),
        action=Play(
            group=draw(st.sampled_from(("table", "meld", "trick"))),
            indices=frozenset(draw(st.sets(st.integers(min_value=0, max_value=9), min_size=1))),
        ),
    )


def concealed_slots(position: Position[GameState], observer: int | None) -> tuple[Slot, ...]:
    """Every place on the board holding a card this observer may not identify."""
    return tuple(
        (zone_id, index)
        for zone_id, zone in position.board.zones.items()
        for index, card in enumerate(zone.cards)
        if not visible_to(zone, card, position.players, observer)
    )


def swap_concealed(
    position: Position[GameState], slots: tuple[Slot, ...], order: tuple[int, ...]
) -> Position[GameState]:
    """The same table with the cards in `slots` dealt back out among those slots in the given order.

    This is the rearrangement of §7: the table still holds the same cards, so a projection that reacts
    to which concealed card sits where gives itself away.
    """
    payloads = tuple(position.board.zone(zone_id).cards[index].card for zone_id, index in slots)
    return _rewritten(position, {slot: payloads[source] for slot, source in zip(slots, order)})


def substitute_concealed(
    position: Position[GameState], slots: tuple[Slot, ...], cards: tuple[CardOrJoker, ...]
) -> Position[GameState]:
    """The same table with a different card put in each of `slots`, drawn freely and with repeats allowed.

    Where a rearrangement keeps the concealed cards a permutation of themselves, this replaces them
    outright. It reaches the leaks a permutation is blind to: a count of aces in the pile, the spread
    of suits still undealt, any summary of what the observer cannot identify.
    """
    return _rewritten(position, dict(zip(slots, cards)))


def _rewritten(position: Position[GameState], written: dict[Slot, CardOrJoker]) -> Position[GameState]:
    """The same table with the cards named by slot written into place, each slot keeping the way it lies."""
    zones = tuple(
        zone.with_cards(_written_cards(zone.id, zone.cards, written)) for zone in position.board.zones.values()
    )
    board = position.board.with_zones(*zones)
    dealt = tuple(game_card.card for zone in board.zones.values() for game_card in zone.cards)
    return position.with_board(Board(starting_deck=dealt, zones=board.zones))


def _written_cards(zone_id: ZoneId, cards: GameCards, written: dict[Slot, CardOrJoker]) -> GameCards:
    return tuple(
        GameCard(card=written[(zone_id, index)], face_down=card.face_down) if (zone_id, index) in written else card
        for index, card in enumerate(cards)
    )
