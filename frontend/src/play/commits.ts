import type { EventView, PositionView, ZoneId, ZoneView } from "../api/views";

/** How far one commit carries a client: a view stands at the count of commits, an event at the number of one. */
const APPLIED = 1;

/**
 * The view a client holds once a commit off the stream has been reckoned with.
 *
 * A client stands at the number of commits it holds, so the commit it wants next is the one numbered that.
 * One numbered lower is a commit already in hand — which a client that read the position afresh while the
 * stream was catching up is served again — and the view it already holds is the later of the two.
 */
export function advanced(view: PositionView, event: EventView): PositionView {
  return event.seq < view.seq ? view : applyCommit(view, event);
}

/**
 * The view a client holds once one commit has landed on it.
 *
 * A commit carries both sides of every zone it altered, the cursor it left and the moves it opened, so a
 * client following the stream stays current without asking the table anything. Applying one is what keeps the
 * position on screen and the sequence a move quotes in step with each other.
 */
export function applyCommit(view: PositionView, event: EventView): PositionView {
  return {
    observer: view.observer,
    seq: event.seq + APPLIED,
    zones: rearranged(view.zones, event),
    state: event.state,
    legal: event.legal,
  };
}

/** Every zone of a view, with each one the commit read differently holding what it reads now. */
function rearranged(zones: Record<ZoneId, ZoneView>, event: EventView): Record<ZoneId, ZoneView> {
  const rearrangement = { ...zones };
  for (const change of event.changes) {
    rearrangement[change.zone] = { ...zoneOf(zones, change.zone), cards: change.after };
  }

  return rearrangement;
}

/** The zone a change speaks about, and an empty one of that name where the view holds none. */
function zoneOf(zones: Record<ZoneId, ZoneView>, zone: ZoneId): ZoneView {
  return zones[zone] ?? { id: zone, owner: null, cards: [] };
}
