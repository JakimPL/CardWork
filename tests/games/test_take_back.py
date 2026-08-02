from typing import Final

import pytest

from cardwork.cards.game import GameCard
from cardwork.exceptions import IllegalMove, NotYourTurn
from cardwork.moves.actions import Play, Take
from cardwork.moves.move import Move
from cardwork.states.state import GameState
from cardwork.views.event import EventView

from .demo import HAND_SIZE, SEATS, SealedRoundGame, hand_of, tray_of

SEAL: Final[Move] = Move(player=1, action=Play(group="sealed", indices=frozenset({0})))
RECLAIM: Final[Move] = Move(player=1, action=Take(group="sealed", indices=frozenset({0})))
DEAL: Final[int] = 1


def close_the_round(sealed: SealedRoundGame) -> None:
    for seat in range(SEATS):
        sealed.submit(Move(player=seat, action=Play(group="sealed", indices=frozenset({0}))), base_seq=sealed.head)


def shown(events: tuple[EventView[GameState], ...]) -> set[GameCard]:
    """Every card these events name outright, which is what the observer they were built for learns."""
    return {
        card
        for event in events
        for change in event.changes
        for card in change.before + change.after
        if card is not None
    }


def test_a_commitment_lies_face_down_in_the_seat_s_own_tray(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)

    assert sealed.board.zone(tray_of(1)).cards[0].face_down


def test_a_seat_reads_what_it_sealed(sealed: SealedRoundGame) -> None:
    committed = sealed.board.zone(hand_of(1)).cards[0]

    sealed.submit(SEAL, base_seq=sealed.head)

    assert sealed.view(observer=1).zones[tray_of(1)].cards == (committed.with_face(True),)


def test_an_opponent_reads_a_count_where_the_commitment_lies(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)

    assert sealed.view(observer=0).zones[tray_of(1)].cards == (None,)


def test_a_seat_may_reclaim_what_it_sealed_while_the_round_stays_open(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)

    sealed.submit(RECLAIM, base_seq=sealed.head)

    assert sealed.board.zone(tray_of(1)).cards == ()
    assert len(sealed.board.zone(hand_of(1)).cards) == HAND_SIZE


def test_reclaiming_opens_the_turn_for_that_seat_again(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)
    sealed.submit(RECLAIM, base_seq=sealed.head)

    assert sealed.state.to_act == frozenset(range(SEATS))


def test_a_reclaimed_commitment_leaves_the_record_it_made_standing(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)
    sealed.submit(RECLAIM, base_seq=sealed.head)

    assert sealed.head == 3
    assert sealed.journal.transactions[DEAL].move == SEAL


def test_reclaiming_needs_no_turn_of_its_own(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)
    assert 1 not in sealed.state.to_act

    assert sealed.submit(RECLAIM, base_seq=sealed.head).move == RECLAIM


def test_a_seat_that_never_sealed_anything_has_nothing_to_reclaim(sealed: SealedRoundGame) -> None:
    with pytest.raises(IllegalMove):
        sealed.submit(RECLAIM, base_seq=sealed.head)


def test_an_opponent_never_learns_which_card_came_and_went(sealed: SealedRoundGame) -> None:
    committed = sealed.board.zone(hand_of(1)).cards[0]

    sealed.submit(SEAL, base_seq=sealed.head)
    sealed.submit(RECLAIM, base_seq=sealed.head)

    assert committed not in shown(sealed.events(observer=0, since=DEAL))


def test_an_opponent_reads_the_tray_filling_and_emptying(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)
    sealed.submit(RECLAIM, base_seq=sealed.head)

    trays = [
        change
        for event in sealed.events(observer=0, since=DEAL)
        for change in event.changes
        if change.zone == tray_of(1)
    ]
    assert [(change.before, change.after) for change in trays] == [((), (None,)), ((None,), ())]


def test_closing_the_round_turns_every_tray_over_at_once(sealed: SealedRoundGame) -> None:
    close_the_round(sealed)

    sealed.settle()

    assert len(sealed.board.zone("discard").cards) == SEATS
    assert all(not card.face_down for card in sealed.board.zone("discard").cards)


def test_a_commitment_settles_once_the_round_has_closed(sealed: SealedRoundGame) -> None:
    close_the_round(sealed)
    sealed.settle()

    with pytest.raises(IllegalMove):
        sealed.submit(RECLAIM, base_seq=sealed.head)


def test_a_seat_that_has_committed_waits_for_the_rest(sealed: SealedRoundGame) -> None:
    sealed.submit(SEAL, base_seq=sealed.head)

    with pytest.raises(NotYourTurn):
        sealed.submit(SEAL, base_seq=sealed.head)
