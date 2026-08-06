from collections.abc import Mapping
from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardwork.boards.board import Board
from cardwork.cards.card import Card, Cards
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.decks.decks import to_game_cards
from cardwork.effects.effects import AnyEffect, SetFace
from cardwork.effects.fold import fold
from cardwork.positions.position import Position
from cardwork.rounds.redeal import DRAWS_MOST, Admits, Redeal
from cardwork.states.state import GameState
from cardwork.zones.presets import PILE
from cardwork.zones.zone import Zone, ZoneId, cards_of
from tests.cases import Case, descriptions

STOCK: Final[ZoneId] = "stock"
HAND: Final[ZoneId] = "hand:0"
SEED: Final[int] = 20260805
ONE_CARD: Final[int] = 1
FIRST_CARD: Final[int] = 0
DRAWS: Final[int] = 20
LAID_OUT: Final[str] = "laid out"
CARDS: Final[Cards] = (
    Card(rank=Rank.TWO, suit=Suit.SPADE),
    Card(rank=Rank.THREE, suit=Suit.HEART),
    Card(rank=Rank.FOUR, suit=Suit.CLUB),
    Card(rank=Rank.FIVE, suit=Suit.DIAMOND),
)


def a_table(contents: Mapping[ZoneId, Cards]) -> Position[GameState]:
    """A table laid out as the contents state, every card of it face up and every zone read by all."""
    zones = {
        zone_id: Zone(id=zone_id, visibility=PILE, ordered=True, cards=to_game_cards(cards, face_down=False))
        for zone_id, cards in contents.items()
    }
    deck = tuple(card for cards in contents.values() for card in cards)
    return Position(board=Board(starting_deck=deck, zones=zones), state=GameState(phase=LAID_OUT), players=2)


def a_redeal(position: Position[GameState]) -> Redeal[GameState]:
    """A re-deal gathering that table into its stock, face down."""
    return Redeal(position, pile=STOCK, face_down=True)


@dataclass(frozen=True)
class GatherCase(Case):
    contents: Mapping[ZoneId, Cards]
    gathered: tuple[tuple[str, ZoneId], ...]


GATHERS: Final[tuple[GatherCase, ...]] = (
    GatherCase(
        description="every zone holding a card empties into the pile, in the order their names sort",
        contents={"b": CARDS[:1], STOCK: (), "a": CARDS[1:2]},
        gathered=(("move_cards", "a"), ("move_cards", "b")),
    ),
    GatherCase(
        description="a zone standing empty is left where it is",
        contents={"a": (), STOCK: CARDS[:1], "b": CARDS[1:2]},
        gathered=(("set_face", STOCK), ("move_cards", "b")),
    ),
    GatherCase(
        description="the pile keeps what it holds and comes to the one face",
        contents={STOCK: CARDS[:2]},
        gathered=(("set_face", STOCK),),
    ),
)


@dataclass(frozen=True)
class DealCase(Case):
    counts: Mapping[ZoneId, int]
    dealt: tuple[tuple[ZoneId, int], ...]


DEALS: Final[tuple[DealCase, ...]] = (
    DealCase(
        description="the cards leave the pile in the order the counts name the zones",
        counts={"b": 1, "a": 2},
        dealt=(("b", 1), ("a", 2)),
    ),
    DealCase(
        description="a zone owed nothing takes nothing",
        counts={"a": 2, "b": 0},
        dealt=(("a", 2),),
    ),
    DealCase(
        description="a deal of no cards at all moves nothing",
        counts={},
        dealt=(),
    ),
)


def addressed(effect: AnyEffect[GameState]) -> tuple[str, ZoneId]:
    """The kind of one gathering effect beside the zone it reads, whether it turns cards or moves them."""
    return (effect.kind, effect.zone if isinstance(effect, SetFace) else effect.source)


@pytest.mark.parametrize("case", GATHERS, ids=descriptions(GATHERS))
def test_gathering_empties_the_table_into_the_pile(case: GatherCase) -> None:
    gathered = a_redeal(a_table(case.contents)).gather()

    assert tuple(addressed(effect) for effect in gathered) == case.gathered
    assert all(effect.face_down for effect in gathered)


@pytest.mark.parametrize("case", DEALS, ids=descriptions(DEALS))
def test_a_deal_hands_each_zone_the_count_it_is_owed(case: DealCase) -> None:
    dealt = a_redeal(a_table({STOCK: CARDS})).distribute(case.counts)

    assert tuple((effect.target, len(effect.indices)) for effect in dealt) == case.dealt
    assert all(effect.source == STOCK and effect.face_down for effect in dealt)


def test_a_gathered_pile_holds_every_card_the_table_held_face_down() -> None:
    position = a_table({STOCK: CARDS[:1], "a": CARDS[1:3], "b": CARDS[3:]})

    gathered = fold(a_redeal(position).gather(), position)

    assert len(gathered.board.zone(STOCK).cards) == len(CARDS)
    assert all(card.face_down for card in gathered.board.zone(STOCK).cards)
    gathered.board.validate_board()


def test_the_shuffle_lays_out_every_card_the_pile_comes_to_hold() -> None:
    redeal = a_redeal(a_table({STOCK: CARDS[:2], "a": CARDS[2:]}))

    shuffle = redeal.shuffle(Random(SEED))

    assert sorted(shuffle[0].order) == list(range(len(CARDS)))
    assert redeal.shuffle(Random(SEED)) == shuffle


def test_a_re_deal_hands_out_its_counts_and_leaves_the_rest_in_the_pile() -> None:
    position = a_table({STOCK: (), "hand:0": CARDS[:2], "hand:1": CARDS[2:], "discard": ()})

    redealt = fold(a_redeal(position).effects({"hand:0": 1, "hand:1": 2}, Random(SEED)), position)

    assert len(redealt.board.zone("hand:0").cards) == 1
    assert len(redealt.board.zone("hand:1").cards) == 2
    assert len(redealt.board.zone(STOCK).cards) == len(CARDS) - 3
    assert redealt.board.zone("discard").cards == ()
    redealt.board.validate_board()


def test_a_re_deal_asking_for_more_cards_than_the_table_holds_is_refused() -> None:
    position = a_table({STOCK: (), "hand:0": CARDS})

    with pytest.raises(KeyError):
        fold(a_redeal(position).effects({"hand:0": len(CARDS) + 1}, Random(SEED)), position)


def a_hand_without(unwanted: Card) -> Admits[GameState]:
    """A deal admitted where the hand it lays out holds none of that card."""

    def admits(dealt: Position[GameState]) -> bool:
        return unwanted not in cards_of(dealt.board.zone(HAND))

    return admits


def test_a_deal_the_game_admits_at_once_is_the_one_it_is_dealt() -> None:
    position = a_table({STOCK: (), HAND: CARDS})

    admitted = a_redeal(position).admitted({HAND: ONE_CARD}, Random(SEED), lambda dealt: True)

    assert admitted == a_redeal(position).effects({HAND: ONE_CARD}, Random(SEED))


def test_the_deal_a_game_keeps_is_the_first_draw_it_admits() -> None:
    """Each draw is a shuffle of the whole pile, so the deal kept is the first the game did not refuse."""
    position = a_table({STOCK: (), HAND: CARDS})
    counts = {HAND: ONE_CARD}
    first = fold(a_redeal(position).effects(counts, Random(SEED)), position)
    admits = a_hand_without(cards_of(first.board.zone(HAND))[FIRST_CARD])
    generator = Random(SEED)
    drawn = tuple(a_redeal(position).effects(counts, generator) for _ in range(DRAWS))

    admitted = a_redeal(position).admitted(counts, Random(SEED), admits)

    assert admitted == next(deal for deal in drawn if admits(fold(deal, position)))
    assert admitted != drawn[FIRST_CARD]


def test_a_deal_no_draw_satisfies_is_refused_rather_than_drawn_for_ever() -> None:
    """A game asking for a deal its cards hold none of is answered, so no table waits on a draw never coming."""
    position = a_table({STOCK: (), HAND: CARDS})

    with pytest.raises(ValueError, match=str(DRAWS_MOST)):
        a_redeal(position).admitted({HAND: ONE_CARD}, Random(SEED), lambda dealt: False)
