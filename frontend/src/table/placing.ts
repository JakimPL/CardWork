import type { Layout, Slot } from "../api/layout";
import { turnOf } from "../play/seats";

/** Where a group of zones sits on the page, which follows from the seat the zones belong to. */
export type Placement = "shared" | "own" | "station";

/** One seat drawn round the table: whose it is, how far round it sits, and the zones the table reads of it. */
export interface Station {
  seat: number;
  turn: number;
  slots: Slot[];
}

/** The zones one owner holds, in the order the layout places them. */
function ownedBy(layout: Layout, owner: number | null): Slot[] {
  return layout.slots.filter((slot) => slot.seat === owner).sort((one, other) => one.place - other.place);
}

/** The zones every seat reads the same way, which lie in the middle within reach of all of them. */
export function shared(layout: Layout): Slot[] {
  return ownedBy(layout, null);
}

/** The zones the seat reading the page holds of its own, which lie in the panel it plays from. */
export function own(layout: Layout): Slot[] {
  return layout.observer === null ? [] : ownedBy(layout, layout.observer);
}

/**
 * The seats drawn round the table, in the order play runs from the seat reading the page.
 *
 * A seat whose cards the layout draws nowhere takes no station: what it holds is a figure on its plaque rather
 * than cards on the table, which is how a game keeps a holding off the table altogether.
 */
export function stations(layout: Layout): Station[] {
  return layout.plaques
    .filter((plaque) => plaque.seat !== layout.observer)
    .map((plaque) => ({ seat: plaque.seat, turn: turnOf(layout, plaque.seat), slots: ownedBy(layout, plaque.seat) }))
    .filter((station) => station.slots.length > 0)
    .sort((one, other) => one.turn - other.turn);
}

/** Whether the table draws a seat's own cards, which is what leaves a move onto it landing on those cards. */
export function drawnAt(layout: Layout, seat: number): boolean {
  return layout.slots.some((slot) => slot.seat === seat);
}
