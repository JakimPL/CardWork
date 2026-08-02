from cardwork.cards.game import GameCard
from cardwork.zones.audience import Audience
from cardwork.zones.zone import Zone


def rule_for(zone: Zone, card: GameCard) -> Audience:
    """The clause of a zone's visibility policy that governs a card, chosen by the way the card lies."""
    return zone.visibility.face_down if card.face_down else zone.visibility.face_up


def audience(zone: Zone, card: GameCard, players: int) -> frozenset[int]:
    """The seats entitled to identify a card lying in a zone.

    Raises:
        ValueError: when the policy names an audience this resolver has no clause for.
    """
    rule = rule_for(zone, card)
    match rule:
        case Audience.ALL:
            base = frozenset(range(players))
        case Audience.OWNER:
            base = frozenset() if zone.owner is None else frozenset({zone.owner})
        case Audience.NONE:
            base = frozenset()
        case _:
            raise ValueError(f"Unexpected audience value: {rule}")

    return base | zone.visibility.extra


def visible_to(
    zone: Zone,
    card: GameCard,
    players: int,
    observer: int | None,
) -> bool:
    """Whether one observer may identify a card lying in a zone.

    A spectator holds no seat, so they read what the table reads: the cards a zone shows to everyone.
    A grant through `extra` names seats, which leaves it to the players it was written for.

    Args:
        zone: the zone holding the card, whose policy decides the question.
        card: the card in question, read for the way it lies.
        players: the seat count of the table, which fixes what "everyone" means.
        observer: the seat asking, or None for a spectator.
    """
    if observer is None:
        return rule_for(zone, card) is Audience.ALL

    return observer in audience(zone, card, players)
