from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.cards import ACE_OF_SPADES, KING_OF_HEARTS
from cardwork.cards.game import GameCard
from cardwork.zones.audience import Audience
from cardwork.zones.presets import HAND, HIDDEN, PILE
from cardwork.zones.resolution import audience, visible_to
from cardwork.zones.visibility import Visibility
from cardwork.zones.zone import Zone

PLAYERS: Final[int] = 3
EVERYONE: Final[frozenset[int]] = frozenset(range(PLAYERS))

FACE_UP: Final[GameCard] = GameCard(card=ACE_OF_SPADES, face_down=False)
FACE_DOWN: Final[GameCard] = GameCard(card=KING_OF_HEARTS, face_down=True)


@dataclass(frozen=True)
class AudienceCase:
    name: str
    zone: Zone
    card: GameCard
    expected: frozenset[int]


CASES: Final[tuple[AudienceCase, ...]] = (
    AudienceCase(
        name="a hand holds its owner's cards face down",
        zone=Zone(id="hand:1", owner=1, visibility=HAND),
        card=FACE_DOWN,
        expected=frozenset({1}),
    ),
    AudienceCase(
        name="an exposed penalty card in a hand is public",
        zone=Zone(id="hand:1", owner=1, visibility=HAND),
        card=FACE_UP,
        expected=EVERYONE,
    ),
    AudienceCase(
        name="a blind holding hides cards from its owner too",
        zone=Zone(id="blind:1", owner=1, visibility=PILE),
        card=FACE_DOWN,
        expected=frozenset(),
    ),
    AudienceCase(
        name="the draw pile hides its cards",
        zone=Zone(id="draw", visibility=PILE),
        card=FACE_DOWN,
        expected=frozenset(),
    ),
    AudienceCase(
        name="the face-up card of a discard pile is public",
        zone=Zone(id="discard", visibility=PILE),
        card=FACE_UP,
        expected=EVERYONE,
    ),
    AudienceCase(
        name="a hidden zone keeps a face-up card to itself",
        zone=Zone(id="void", visibility=HIDDEN),
        card=FACE_UP,
        expected=frozenset(),
    ),
)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_audience_resolves_the_visibility_table(case: AudienceCase) -> None:
    assert audience(case.zone, case.card, PLAYERS) == case.expected


def test_audience_grants_an_ad_hoc_reveal_on_top_of_the_policy() -> None:
    shown_to_one_opponent = Visibility(face_up=Audience.ALL, face_down=Audience.NONE, extra=frozenset({2}))
    zone = Zone(id="draw", visibility=shown_to_one_opponent)

    assert audience(zone, FACE_DOWN, PLAYERS) == frozenset({2})


def test_audience_of_an_unowned_hand_reaches_nobody() -> None:
    zone = Zone(id="orphan", visibility=HAND)

    assert audience(zone, FACE_DOWN, PLAYERS) == frozenset()


@dataclass(frozen=True)
class SpectatorCase:
    name: str
    zone: Zone
    card: GameCard
    expected: bool


SPECTATOR_CASES: Final[tuple[SpectatorCase, ...]] = (
    SpectatorCase(
        name="a card lying face up on the table is public",
        zone=Zone(id="discard", visibility=PILE),
        card=FACE_UP,
        expected=True,
    ),
    SpectatorCase(
        name="an exposed card in a hand is public too",
        zone=Zone(id="hand:1", owner=1, visibility=HAND),
        card=FACE_UP,
        expected=True,
    ),
    SpectatorCase(
        name="a card a seat holds belongs to that seat",
        zone=Zone(id="hand:1", owner=1, visibility=HAND),
        card=FACE_DOWN,
        expected=False,
    ),
    SpectatorCase(
        name="the draw pile keeps its cards from the gallery",
        zone=Zone(id="draw", visibility=PILE),
        card=FACE_DOWN,
        expected=False,
    ),
    SpectatorCase(
        name="a hidden zone shows nothing to anyone",
        zone=Zone(id="void", visibility=HIDDEN),
        card=FACE_UP,
        expected=False,
    ),
    SpectatorCase(
        name="a reveal granted to named seats stays with those seats",
        zone=Zone(id="draw", visibility=Visibility(face_down=Audience.NONE, extra=frozenset({0, 1, 2}))),
        card=FACE_DOWN,
        expected=False,
    ),
)


@pytest.mark.parametrize("case", SPECTATOR_CASES, ids=lambda case: case.name)
def test_visible_to_grants_a_spectator_what_the_table_shows_everyone(case: SpectatorCase) -> None:
    assert visible_to(case.zone, case.card, PLAYERS, None) is case.expected


@pytest.mark.parametrize("seat", range(PLAYERS))
def test_visible_to_follows_the_audience_for_a_seated_observer(seat: int) -> None:
    zone = Zone(id="hand:1", owner=1, visibility=HAND)

    assert visible_to(zone, FACE_DOWN, PLAYERS, seat) is (seat in audience(zone, FACE_DOWN, PLAYERS))
