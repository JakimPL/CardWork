from typing import Final

from hypothesis import given
from hypothesis import strategies as st

from cardwork.moves.move import Moves
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.views.projection import project_position, project_transaction
from cardwork.zones.resolution import visible_to

from .strategies import (
    POOL,
    Commit,
    commits,
    concealed_slots,
    moves,
    observers,
    positions,
    substitute_concealed,
    swap_concealed,
)

SEQ: Final[int] = 11
MOST_MOVES: Final[int] = 6


def scrambled(position: Position[GameState], observer: int | None, data: st.DataObject) -> Position[GameState]:
    """The same table with every card the observer may not identify dealt back out among those places."""
    slots = concealed_slots(position, observer)
    return swap_concealed(position, slots, tuple(data.draw(st.permutations(range(len(slots))))))


def offered(players: int, data: st.DataObject) -> Moves:
    """A run of moves the rules might admit from a table of that many seats, drawn across the seats."""
    return tuple(data.draw(st.lists(moves(players), max_size=MOST_MOVES)))


def restocked(position: Position[GameState], observer: int | None, data: st.DataObject) -> Position[GameState]:
    """The same table with a freely chosen card standing in every place the observer may not identify."""
    slots = concealed_slots(position, observer)
    cards = data.draw(st.lists(st.sampled_from(POOL), min_size=len(slots), max_size=len(slots)))
    return substitute_concealed(position, slots, tuple(cards))


@given(position=positions(), data=st.data())
def test_a_position_view_survives_any_rearrangement_of_what_it_conceals(
    position: Position[GameState], data: st.DataObject
) -> None:
    observer = data.draw(observers(position.players))

    assert project_position(position, SEQ, observer, legal=()) == project_position(
        scrambled(position, observer, data), SEQ, observer, legal=()
    )


@given(commit=commits(), data=st.data())
def test_an_event_view_survives_any_rearrangement_of_what_it_conceals(commit: Commit, data: st.DataObject) -> None:
    transaction, before, after = commit
    observer = data.draw(observers(before.players))

    assert project_transaction(transaction, before, after, observer, legal=()) == project_transaction(
        transaction,
        scrambled(before, observer, data),
        scrambled(after, observer, data),
        observer,
        legal=(),
    )


@given(position=positions(), data=st.data())
def test_a_position_view_survives_any_substitution_of_what_it_conceals(
    position: Position[GameState], data: st.DataObject
) -> None:
    observer = data.draw(observers(position.players))

    assert project_position(position, SEQ, observer, legal=()) == project_position(
        restocked(position, observer, data), SEQ, observer, legal=()
    )


@given(commit=commits(), data=st.data())
def test_an_event_view_survives_any_substitution_of_what_it_conceals(commit: Commit, data: st.DataObject) -> None:
    transaction, before, after = commit
    observer = data.draw(observers(before.players))

    assert project_transaction(transaction, before, after, observer, legal=()) == project_transaction(
        transaction,
        restocked(before, observer, data),
        restocked(after, observer, data),
        observer,
        legal=(),
    )


@given(position=positions(), data=st.data())
def test_a_position_view_holds_one_entry_for_every_card_on_the_board(
    position: Position[GameState], data: st.DataObject
) -> None:
    observer = data.draw(observers(position.players))

    view = project_position(position, SEQ, observer, legal=())

    assert {zone_id: len(zone.cards) for zone_id, zone in view.zones.items()} == {
        zone_id: len(zone.cards) for zone_id, zone in position.board.zones.items()
    }


@given(position=positions(), data=st.data())
def test_a_position_view_reports_each_card_it_shows_at_the_index_the_board_holds_it(
    position: Position[GameState], data: st.DataObject
) -> None:
    observer = data.draw(observers(position.players))

    view = project_position(position, SEQ, observer, legal=())

    assert all(
        shown is None or shown == position.board.zone(zone_id).cards[index]
        for zone_id, zone in view.zones.items()
        for index, shown in enumerate(zone.cards)
    )


@given(position=positions(), data=st.data())
def test_a_position_view_shows_every_card_the_observer_is_entitled_to(
    position: Position[GameState], data: st.DataObject
) -> None:
    observer = data.draw(observers(position.players))

    view = project_position(position, SEQ, observer, legal=())

    assert all(
        view.zones[zone_id].cards[index] == card
        for zone_id, zone in position.board.zones.items()
        for index, card in enumerate(zone.cards)
        if visible_to(zone, card, position.players, observer)
    )


@given(commit=commits(), data=st.data())
def test_an_event_view_reports_exactly_the_zones_the_observer_reads_differently(
    commit: Commit, data: st.DataObject
) -> None:
    transaction, before, after = commit
    observer = data.draw(observers(before.players))

    event = project_transaction(transaction, before, after, observer, legal=())

    seen_before = project_position(before, SEQ, observer, legal=()).zones
    seen_after = project_position(after, SEQ, observer, legal=()).zones
    altered = {zone_id for zone_id in seen_before if seen_before[zone_id].cards != seen_after[zone_id].cards}
    assert {change.zone for change in event.changes} == altered


@given(commit=commits(), data=st.data())
def test_an_event_view_withholds_the_action_from_every_seat_but_the_one_that_made_it(
    commit: Commit, data: st.DataObject
) -> None:
    transaction, before, after = commit
    observer = data.draw(observers(before.players))

    event = project_transaction(transaction, before, after, observer, legal=())

    assert event.move is None or event.move.action is None or event.move.player == observer


@given(position=positions(), data=st.data())
def test_a_position_view_offers_no_move_belonging_to_another_seat(
    position: Position[GameState], data: st.DataObject
) -> None:
    observer = data.draw(observers(position.players))
    admitted = offered(position.players, data)

    view = project_position(position, SEQ, observer, legal=admitted)

    assert all(move.player == observer for move in view.legal)


@given(commit=commits(), data=st.data())
def test_an_event_view_offers_no_move_belonging_to_another_seat(commit: Commit, data: st.DataObject) -> None:
    transaction, before, after = commit
    observer = data.draw(observers(before.players))
    admitted = offered(before.players, data)

    event = project_transaction(transaction, before, after, observer, legal=admitted)

    assert all(move.player == observer for move in event.legal)
