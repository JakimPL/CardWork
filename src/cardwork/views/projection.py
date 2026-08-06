from collections.abc import Mapping

from cardwork.cards.game import GameCard
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.transactions.transaction import Transaction
from cardwork.views.event import EventView, MoveView, ZoneChange
from cardwork.views.position import PositionView
from cardwork.views.zone import ZoneView
from cardwork.zones.resolution import arrangeable_by, visible_to
from cardwork.zones.zone import Zone, ZoneId

ProjectedZones = Mapping[ZoneId, ZoneView]
ProjectedCards = tuple[GameCard | None, ...]


def project_position(
    position: Position[StateT],
    seq: int,
    observer: int | None,
    legal: Moves,
) -> PositionView[StateT]:
    """A position narrowed to what one observer is entitled to know, stamped with the sequence it holds at.

    This is the security boundary: a full position stays on the server, and this is what a client
    receives in its place. The sequence number comes from the caller because a position is a snapshot
    of a table rather than a point in its history, and the same snapshot is projected at whatever
    sequence the journal reached. The moves come from the caller for the same reason: enumerating them
    is the rules' work, and narrowing them to one seat is this boundary's.

    Args:
        position: the server-side snapshot to narrow.
        seq: the journal sequence this snapshot stands at, which the client quotes back as `base_seq`.
        observer: the seat receiving the view, or None for a spectator.
        legal: every move the rules admit from the position, of which the observer receives its own.
    """
    return PositionView(
        observer=observer,
        seq=seq,
        zones=project_zones(position, observer),
        state=position.state.project(observer),
        legal=project_moves(legal, observer),
    )


def project_transaction(
    transaction: Transaction[StateT],
    before: Position[StateT],
    after: Position[StateT],
    observer: int | None,
    legal: Moves,
) -> EventView[StateT]:
    """What one observer learns from a commit: who acted, which of their zones read differently, and the new cursor.

    The changes are the difference between two projections of the same observer, so an event discloses
    exactly what a pair of position views would have, and both shapes answer to one audience rule. The
    effects themselves stay on the server, where they name every card they touched.

    Args:
        transaction: the commit, read for its sequence number and the move that prompted it.
        before: the position the commit was applied to.
        after: the position the commit produced.
        observer: the seat receiving the event, or None for a spectator.
        legal: every move the rules admit from `after`, of which the observer receives its own.
    """
    return EventView(
        seq=transaction.seq,
        observer=observer,
        move=project_move(transaction.move, observer),
        changes=zone_changes(
            project_zones(before, observer),
            project_zones(after, observer),
        ),
        state=after.state.project(observer),
        legal=project_moves(legal, observer),
    )


def project_zones(
    position: Position[StateT],
    observer: int | None,
) -> ProjectedZones:
    """Every zone of a position as one observer reads it, filed under the same ids the board uses."""
    return {
        zone_id: project_zone(
            zone,
            position.players,
            observer,
        )
        for zone_id, zone in position.board.zones.items()
    }


def project_zone(zone: Zone, players: int, observer: int | None) -> ZoneView:
    """One zone with a placeholder standing in for each card outside the observer's audience.

    Placeholders hold the index of the card they conceal, so position 3 of a hand names the same card
    to the client and to the server, and an action addressing it lands where the player aimed. The zone
    carries this observer's standing to arrange it beside its cards, which is the one thing a client is
    told of a zone's policy: the cards it may read, and the run it may lay them out in.
    """
    return ZoneView(
        id=zone.id,
        owner=zone.owner,
        arrangeable=arrangeable_by(zone, observer),
        cards=tuple(
            (
                card
                if visible_to(
                    zone,
                    card,
                    players,
                    observer,
                )
                else None
            )
            for card in zone.cards
        ),
    )


def project_move(move: Move | None, observer: int | None) -> MoveView | None:
    """The move behind a commit as one observer may know it, and None for a commit the engine raised itself.

    The acting seat receives their own action back, confirming what the server accepted. Everyone else
    receives the seat alone: an action names positions inside a zone whose contents they cannot read,
    and passing those positions on would let them follow a once-seen card through a hand.
    """
    if move is None:
        return None

    return MoveView(
        player=move.player,
        action=move.action if observer == move.player else None,
    )


def project_moves(moves: Moves, observer: int | None) -> Moves:
    """The moves one observer may make, out of every move the rules admit from a position.

    A seat reads its own options and nothing else. That matters most where several seats owe an action at
    once: the moves open to another seat name positions inside zones this one cannot read, so serving them
    would spell out the size and shape of a holding the projection is concealing. A spectator holds none,
    since a move belongs to a seat.
    """
    return tuple(move for move in moves if move.player == observer)


def zone_changes(
    before: ProjectedZones,
    after: ProjectedZones,
) -> tuple[ZoneChange, ...]:
    """One entry per zone whose projection the commit altered, ordered by zone id.

    A zone the observer reads the same way on both sides stays out, which is what keeps a shuffle of a
    face-down pile silent for everyone it stays hidden from.
    """
    changes = []
    for zone_id in sorted(before.keys() | after.keys()):
        was, now = projected_cards(before, zone_id), projected_cards(after, zone_id)
        if was != now:
            changes.append(ZoneChange(zone=zone_id, before=was, after=now))

    return tuple(changes)


def projected_cards(zones: ProjectedZones, zone_id: ZoneId) -> ProjectedCards:
    """The projected contents of one zone, and an empty run where the projection holds no such zone."""
    view = zones.get(zone_id)
    return () if view is None else view.cards
