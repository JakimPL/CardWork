from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.exceptions import ArrangementRefused, StalePosition
from cardwork.moves.actions import Play
from cardwork.moves.move import Move
from cardwork.zones.zone import ZoneId

from .demo import HAND_SIZE, SEATS, DiscardGame, hand_of

SORTER: Final[int] = 0
REVERSED: Final[tuple[int, ...]] = tuple(reversed(range(HAND_SIZE)))
LAID_DOWN: Final[Move] = Move(player=SORTER, action=Play(group="discard", indices=frozenset({0})))


def test_arrange_numbers_the_transaction_where_the_journal_stood(game: DiscardGame) -> None:
    assert game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head).seq == 1


def test_arrange_carries_the_table_one_commit_onwards(game: DiscardGame) -> None:
    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert game.head == 2


def test_arrange_records_a_commit_no_move_asked_for(game: DiscardGame) -> None:
    """A seat sorting its hand states no intent the rules answer, so the record carries the effect alone."""
    transaction = game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert transaction.move is None
    assert len(transaction.effects) == 1


def test_arrange_lays_the_cards_out_in_the_order_it_was_asked_for(game: DiscardGame) -> None:
    held = game.board.zone(hand_of(SORTER)).cards

    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert game.board.zone(hand_of(SORTER)).cards == tuple(held[index] for index in REVERSED)


def test_arrange_leaves_the_hand_holding_the_cards_it_held(game: DiscardGame) -> None:
    held = game.board.zone(hand_of(SORTER)).cards

    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert set(game.board.zone(hand_of(SORTER)).cards) == set(held)


def test_arrange_leaves_every_card_at_the_face_it_lay_at(game: DiscardGame) -> None:
    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert all(card.face_down for card in game.board.zone(hand_of(SORTER)).cards)


def test_arrange_leaves_the_rules_cursor_where_it_stood(game: DiscardGame) -> None:
    stood = game.state

    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert game.state == stood


def test_arrange_leaves_the_zones_beside_it_untouched(game: DiscardGame) -> None:
    others = {zone_id: zone for zone_id, zone in game.board.zones.items() if zone_id != hand_of(SORTER)}

    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert {zone_id: zone for zone_id, zone in game.board.zones.items() if zone_id != hand_of(SORTER)} == others


def test_arrange_leaves_the_moves_the_rules_admit_as_they_stood(game: DiscardGame) -> None:
    """A card a seat may sort is not thereby a card it may play, so the options a seat holds stand as they were."""
    offered = len(game.view(SORTER).legal)

    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert len(game.view(SORTER).legal) == offered


def test_arrange_is_admitted_from_a_seat_the_turn_has_passed_by(game: DiscardGame) -> None:
    """A player sorts its hand while another acts, which is the whole reason an arrangement is no move."""
    game.submit(LAID_DOWN, base_seq=game.head)
    assert SORTER not in game.state.to_act

    game.arrange(hand_of(SORTER), (1, 0), SORTER, base_seq=game.head)

    assert len(game.board.zone(hand_of(SORTER)).cards) == HAND_SIZE - 1


def test_arrange_replays_from_the_record_to_the_position_it_reached(game: DiscardGame) -> None:
    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=game.head)

    assert game.replay() == game.position


def test_arrange_tells_the_other_seats_nothing_of_a_hand_they_cannot_read(game: DiscardGame) -> None:
    """A run of placeholders reads the same however it is permuted, so the commit carries no change at all."""
    since = game.head
    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=since)

    for observer in [seat for seat in range(SEATS) if seat != SORTER] + [None]:
        assert [event.changes for event in game.events(observer, since)] == [()]


def test_arrange_carries_the_new_order_to_the_seat_that_asked_for_it(game: DiscardGame) -> None:
    since = game.head
    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=since)

    (event,) = game.events(SORTER, since)

    assert [change.zone for change in event.changes] == [hand_of(SORTER)]


def test_a_move_built_before_an_arrangement_is_refused_for_the_position_it_names(game: DiscardGame) -> None:
    """Sorting a hand moves the card each position names, so a move aimed at the old run is turned away."""
    aimed = game.head
    game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=aimed)

    with pytest.raises(StalePosition):
        game.submit(LAID_DOWN, base_seq=aimed)


@pytest.mark.parametrize("base_seq", [0, 2], ids=["a position since superseded", "a position yet to be reached"])
def test_arrange_refuses_an_order_built_on_another_position(game: DiscardGame, base_seq: int) -> None:
    with pytest.raises(StalePosition):
        game.arrange(hand_of(SORTER), REVERSED, SORTER, base_seq=base_seq)


@dataclass(frozen=True)
class RefusalCase:
    name: str
    zone: ZoneId
    order: tuple[int, ...]
    seat: int


REFUSAL_CASES: Final[tuple[RefusalCase, ...]] = (
    RefusalCase(
        name="a pile whose run the table keeps stays as the table laid it",
        zone="draw",
        order=(1, 0),
        seat=SORTER,
    ),
    RefusalCase(
        name="a discard reads by the card on top of it, so its run is the table's",
        zone="discard",
        order=(),
        seat=SORTER,
    ),
    RefusalCase(
        name="a seat lays out its own hand and no other seat's",
        zone=hand_of(1),
        order=REVERSED,
        seat=SORTER,
    ),
    RefusalCase(
        name="a zone the table holds none of is nobody's to lay out",
        zone="nowhere",
        order=(0,),
        seat=SORTER,
    ),
    RefusalCase(
        name="an order naming fewer positions than the hand holds leaves cards unplaced",
        zone=hand_of(SORTER),
        order=(1, 0),
        seat=SORTER,
    ),
    RefusalCase(
        name="an order naming one position twice would hold a card twice",
        zone=hand_of(SORTER),
        order=(0, 1, 1),
        seat=SORTER,
    ),
    RefusalCase(
        name="an order reaching past the hand names a card it holds none of",
        zone=hand_of(SORTER),
        order=(0, 1, HAND_SIZE),
        seat=SORTER,
    ),
)


@pytest.mark.parametrize("case", REFUSAL_CASES, ids=lambda case: case.name)
def test_arrange_refuses_what_a_seat_holds_no_standing_to_lay_out(game: DiscardGame, case: RefusalCase) -> None:
    with pytest.raises(ArrangementRefused):
        game.arrange(case.zone, case.order, case.seat, base_seq=game.head)


@pytest.mark.parametrize("case", REFUSAL_CASES, ids=lambda case: case.name)
def test_a_refused_arrangement_leaves_the_table_where_it_stood(game: DiscardGame, case: RefusalCase) -> None:
    stood = game.position

    with pytest.raises(ArrangementRefused):
        game.arrange(case.zone, case.order, case.seat, base_seq=game.head)

    assert game.position == stood
    assert game.head == 1
