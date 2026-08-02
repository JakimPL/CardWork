from cardwork.cards.cards import ACE_OF_SPADES, KING_OF_HEARTS
from cardwork.decks.decks import to_game_cards
from cardwork.zones.presets import HAND
from cardwork.zones.zone import Zone


def test_with_cards_keeps_the_zone_s_identity_and_policy() -> None:
    zone = Zone(id="hand:1", owner=1, visibility=HAND, cards=to_game_cards((ACE_OF_SPADES,), face_down=True))

    refilled = zone.with_cards(to_game_cards((KING_OF_HEARTS,), face_down=False))

    assert refilled.id == "hand:1"
    assert refilled.owner == 1
    assert refilled.visibility == HAND
    assert refilled.cards == to_game_cards((KING_OF_HEARTS,), face_down=False)


def test_with_cards_leaves_the_zone_it_was_given_untouched() -> None:
    zone = Zone(id="draw", visibility=HAND, cards=to_game_cards((ACE_OF_SPADES,), face_down=True))

    zone.with_cards(())

    assert len(zone.cards) == 1
