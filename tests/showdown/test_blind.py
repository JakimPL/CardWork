from typing import Final

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cardgames.showdown.rules import BLIND_SIZE, HAND_SIZE
from cardgames.showdown.state import ShowdownState
from cardgames.showdown.zones import blind_of, hand_of
from cardwork.cards.card import Card
from cardwork.cards.cards import STANDARD_CARDS
from cardwork.cards.game import GameCard
from cardwork.positions.position import Position
from cardwork.views.project import project_position

from .driving import ROUNDS, SEATS, SEED, a_match

OWNER: Final[int] = 0
OBSERVERS: Final[tuple[int | None, ...]] = (*range(SEATS), None)
DEALT: Final[Position[ShowdownState]] = a_match(SEATS, ROUNDS, SEED).position
SEQ: Final[int] = 0


def restocked(position: Position[ShowdownState], cards: tuple[Card, ...]) -> Position[ShowdownState]:
    """The same table with those cards standing face down in the owner's blind, in place of the ones dealt.

    Substitution is what `tests/views` states concealment as: a view surviving any card standing in a place is
    a view carrying nothing of what stands there.
    """
    blind = position.board.zone(blind_of(OWNER))
    stood = blind.with_cards(tuple(GameCard(card=card, face_down=True) for card in cards))
    return position.with_board(position.board.with_zones(stood))


@given(cards=st.lists(st.sampled_from(STANDARD_CARDS), min_size=BLIND_SIZE, max_size=BLIND_SIZE))
def test_a_blind_reads_the_same_to_everybody_whatever_stands_in_it(cards: list[Card]) -> None:
    substituted = restocked(DEALT, tuple(cards))

    assert all(
        project_position(DEALT, SEQ, observer, legal=()) == project_position(substituted, SEQ, observer, legal=())
        for observer in OBSERVERS
    )


@pytest.mark.parametrize("observer", OBSERVERS, ids=[str(observer) for observer in OBSERVERS])
def test_a_blind_reports_its_size_to_every_observer_and_its_cards_to_none(observer: int | None) -> None:
    view = project_position(DEALT, SEQ, observer, legal=())

    assert all(card is None for card in view.zones[blind_of(OWNER)].cards)
    assert len(view.zones[blind_of(OWNER)].cards) == BLIND_SIZE


def test_a_seat_reads_the_five_of_its_hand_while_the_five_of_its_blind_stay_unread() -> None:
    view = project_position(DEALT, SEQ, OWNER, legal=())

    assert view.zones[hand_of(OWNER)].cards == DEALT.board.zone(hand_of(OWNER)).cards
    assert len(view.zones[hand_of(OWNER)].cards) == HAND_SIZE
    assert all(card is None for card in view.zones[blind_of(OWNER)].cards)
