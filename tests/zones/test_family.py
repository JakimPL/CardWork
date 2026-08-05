from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.exceptions import IllegalMove
from cardwork.zones.audience import Audience
from cardwork.zones.family import Family, family_named
from cardwork.zones.presets import HAND, HIDDEN
from cardwork.zones.visibility import Visibility
from cardwork.zones.zone import ZoneId
from cardwork.zones.zones import HANDS, hand_of, hands
from tests.cases import Case, descriptions

SEATS: Final[int] = 3
SEAT: Final[int] = 1
ANOTHER_SEAT: Final[int] = 2
DEALT: Final[int] = 5
ON_LEAD: Final[int] = 6
BLINDS: Final[Family] = Family(name="blind", ordered=True, visibility=HIDDEN)


def everyone_else(seat: int, players: int) -> Visibility:
    """The sight a board gives each seat: every hand but the one holding it, which is how Hanabi is played."""
    return Visibility(face_up=Audience.ALL, face_down=Audience.NONE, extra=frozenset(range(players)) - {seat})


BOARDS: Final[Family] = Family(name="board", ordered=False, visibility=everyone_else)


@dataclass(frozen=True)
class OwnershipCase(Case):
    """One zone id and whether the hand family reads it as one of its own."""

    zone_id: ZoneId
    owned: bool


OWNERSHIPS: Final[tuple[OwnershipCase, ...]] = (
    OwnershipCase(description="the hand of a seat", zone_id="hand:0", owned=True),
    OwnershipCase(description="the hand of a seat past the first ten", zone_id="hand:11", owned=True),
    OwnershipCase(description="the zone of another family at the same seat", zone_id="blind:0", owned=False),
    OwnershipCase(description="a zone of the table belonging to no seat", zone_id="discard", owned=False),
    OwnershipCase(description="the family name standing without a seat", zone_id="hand", owned=False),
    OwnershipCase(description="a name the family opens but a seat does not close", zone_id="hand:", owned=False),
    OwnershipCase(description="a place named by something other than a seat", zone_id="hand:left", owned=False),
    OwnershipCase(description="a name the family opens and reaches past", zone_id="handy:0", owned=False),
)


def test_a_family_names_the_zone_it_gives_one_seat() -> None:
    assert BLINDS.of(SEAT) == "blind:1"


@pytest.mark.parametrize("case", OWNERSHIPS, ids=descriptions(OWNERSHIPS))
def test_a_family_reads_the_zone_ids_that_are_its_own(case: OwnershipCase) -> None:
    assert HANDS.owns(case.zone_id) is case.owned


def test_a_family_owns_every_zone_it_names() -> None:
    assert all(HANDS.owns(HANDS.of(seat)) for seat in range(SEATS))


def test_a_family_stands_one_zone_at_every_seat() -> None:
    standing = BLINDS.zones(SEATS)

    assert sorted(standing) == [BLINDS.of(seat) for seat in range(SEATS)]
    assert all(zone.id == zone_id for zone_id, zone in standing.items())
    assert all(zone.cards == () for zone in standing.values())


def test_each_zone_of_a_family_belongs_to_the_seat_it_is_named_by() -> None:
    standing = BLINDS.zones(SEATS)

    assert [standing[BLINDS.of(seat)].owner for seat in range(SEATS)] == list(range(SEATS))


def test_a_family_gives_every_zone_of_it_the_word_it_states_on_arrangement() -> None:
    assert all(zone.ordered for zone in BLINDS.zones(SEATS).values())
    assert all(not zone.ordered for zone in HANDS.zones(SEATS).values())


def test_one_policy_stands_for_every_seat_of_a_family_that_states_one() -> None:
    assert all(zone.visibility == HAND for zone in HANDS.zones(SEATS).values())


def test_a_family_owing_each_seat_a_sight_of_its_own_reads_the_policy_per_seat() -> None:
    standing = BOARDS.zones(SEATS)

    assert standing[BOARDS.of(SEAT)].visibility.extra == frozenset({0, ANOTHER_SEAT})
    assert standing[BOARDS.of(ANOTHER_SEAT)].visibility.extra == frozenset({0, SEAT})


def test_a_table_of_no_seats_stands_no_zone_of_a_family() -> None:
    assert BLINDS.zones(0) == {}


def test_one_size_deals_it_to_every_seat_named() -> None:
    assert HANDS.dealt(DEALT, range(SEATS)) == {hand_of(seat): DEALT for seat in range(SEATS)}


def test_a_size_for_each_seat_deals_every_seat_its_own() -> None:
    sizes = {0: ON_LEAD, SEAT: DEALT, ANOTHER_SEAT: DEALT}

    assert HANDS.dealt(sizes, range(SEATS)) == {hand_of(0): ON_LEAD, hand_of(SEAT): DEALT, hand_of(ANOTHER_SEAT): DEALT}


def test_a_deal_hands_the_cards_out_in_the_run_the_seats_are_named_in() -> None:
    from_the_last_seat = (ANOTHER_SEAT, 0, SEAT)

    dealt = HANDS.dealt(DEALT, from_the_last_seat)

    assert tuple(dealt) == tuple(hand_of(seat) for seat in from_the_last_seat)


def test_a_deal_naming_a_size_for_the_seats_it_reaches_states_one_for_each_of_them() -> None:
    with pytest.raises(KeyError):
        HANDS.dealt({0: DEALT}, range(SEATS))


def test_the_zones_a_deal_names_are_the_zones_the_family_stands() -> None:
    dealt: Mapping[ZoneId, int] = HANDS.dealt(DEALT, range(SEATS))

    assert frozenset(dealt) == frozenset(HANDS.zones(SEATS))


def test_a_family_is_named_apart_from_the_seat_it_stands_at() -> None:
    with pytest.raises(ValidationError, match="holds ':'"):
        Family(name="hand:1", ordered=False, visibility=HAND)


def test_a_family_carries_a_name_to_be_read_by() -> None:
    with pytest.raises(ValidationError):
        Family(name="", ordered=False, visibility=HAND)


def test_a_word_a_seat_names_is_read_back_to_the_family_it_stands_for() -> None:
    holdings = (HANDS, BLINDS)

    assert family_named(holdings, HANDS.name, SEAT) is HANDS
    assert family_named(holdings, BLINDS.name, SEAT) is BLINDS


def test_a_word_naming_none_of_the_families_a_seat_holds_cards_in_is_refused() -> None:
    with pytest.raises(IllegalMove, match=f"Seat {SEAT} holds cards in 'hand' or 'blind', and named 'meld'"):
        family_named((HANDS, BLINDS), "meld", SEAT)


def test_the_hands_of_the_table_are_the_zones_the_hand_family_stands() -> None:
    assert hands(SEATS) == HANDS.zones(SEATS)


def test_the_hand_of_a_seat_is_the_zone_the_hand_family_gives_it() -> None:
    assert hand_of(SEAT) == HANDS.of(SEAT) == "hand:1"
