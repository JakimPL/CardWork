import pytest

from cardwork.cards.cards import ACE_OF_SPADES, RED_JOKER
from cardwork.cards.game import CardOrJoker, GameCard, is_joker


@pytest.mark.parametrize(
    ("card", "expected"),
    [
        (ACE_OF_SPADES, False),
        (RED_JOKER, True),
        (GameCard(card=ACE_OF_SPADES), False),
        (GameCard(card=RED_JOKER), True),
    ],
)
def test_is_joker_accepts_bare_and_wrapped_cards(card: CardOrJoker | GameCard, expected: bool) -> None:
    assert is_joker(card) is expected


def test_game_card_marks_a_face_down_card() -> None:
    assert str(GameCard(card=ACE_OF_SPADES, face_down=True)) == "A♠?"
    assert str(GameCard(card=ACE_OF_SPADES, face_down=False)) == "A♠"


def test_with_face_turns_a_card_over_and_keeps_the_original() -> None:
    game_card = GameCard(card=ACE_OF_SPADES, face_down=True)

    turned = game_card.with_face(False)

    assert turned == GameCard(card=ACE_OF_SPADES, face_down=False)
    assert game_card.face_down is True


def test_game_card_rejects_attribute_assignment() -> None:
    game_card = GameCard(card=ACE_OF_SPADES)

    with pytest.raises(ValueError):
        game_card.face_down = True
