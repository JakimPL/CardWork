import type { Layout, Slot, Spread } from "../api/layout";
import { turnOf } from "../play/seats";

/**
 * Where a group of zones sits on the page, which follows from the seat the zones belong to.
 *
 * The seat reading the page holds its own, another seat holds theirs, and the rest of the zones are shared. The
 * three names are the group's alone: the style sheet reads a placement off the group it belongs to, and a seat
 * round the table is drawn by a box of its own under a name of its own.
 */
export type Placement = "shared" | "own" | "theirs";

/** How the one card a seat seals a commitment in lies, which is the arrangement a station lays out on its own. */
const SEALED: Spread = "slot";

/** Which side of the table a seat sits at, read from the near edge the seat reading the page holds. */
export type Side = "left" | "across" | "right";

/** The three sides of a table, in the order play runs round them. */
export const SIDES: readonly Side[] = ["left", "across", "right"];

/** The seats drawn round the table, gathered by the side of it they sit at. */
export type Ring = Record<Side, Station[]>;

/** One seat drawn round the table: whose it is, how far round it sits, and the zones the table reads of it. */
export interface Station {
  seat: number;
  turn: number;
  slots: Slot[];
}

/** The two seats a pair of them makes, which is what a table divides its other seats into sides by. */
const PAIRED = 2;

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

/**
 * The lines one group of zones lies in, in the order they stand one above another.
 *
 * A group with the width of the page to lie along lies in one line, which is the panel a player plays from and the
 * zones at the middle of the table. A seat drawn across the table has the depth of the edge it sits at instead: the
 * holdings the table reads of it lie side by side under its name, and the places it seals a card in lie beneath
 * them, which leaves a station half as wide and reading in two glances. So the cards of a seat are drawn to the
 * room its corner of the table has rather than to the width the whole of it laid out in a line would need.
 *
 * @param place - where the group sits on the page.
 * @param slots - the zones of the group, in the order the layout places them.
 */
export function linesOf(place: Placement, slots: Slot[]): Slot[][] {
  switch (place) {
    case "shared":
    case "own":
      return [slots];
    case "theirs": {
      const holdings = slots.filter((slot) => slot.spread !== SEALED);
      const sealed = slots.filter((slot) => slot.spread === SEALED);
      return [holdings, sealed].filter((line) => line.length > 0);
    }
  }
}

/**
 * The seats round the table gathered by the side of it they sit at, in the order play runs.
 *
 * A table is read from the near edge, which the seat reading the page holds: the seats it plays into first sit up
 * the left of it, the ones facing it across the top, and the rest down the right, which is a card table as it is
 * drawn. So a table of four reads left, across and right, and a table of seven two seats up each side and two
 * across, and the middle of it belongs to the zones every seat shares.
 *
 * Each side is a run of its own on the page, so the room a seat takes is the room its neighbours give way by: no
 * seat is drawn over another and no name is covered, whatever the cards at either of them come to.
 */
export function ringOf(layout: Layout): Ring {
  const seated = stations(layout);
  const across = facingAcross(seated.length);
  const aside = (seated.length - across) / PAIRED;
  return {
    left: seated.slice(0, aside),
    across: seated.slice(aside, aside + across),
    right: seated.slice(aside + across),
  };
}

/**
 * How many seats face the near edge, which is what the seats beside them pair off into sides around.
 *
 * A table whose other seats pair off seats two of them across, and one otherwise, so every pair left over takes
 * one seat up each side and a table of any size reads as a ring.
 */
function facingAcross(seated: number): number {
  if (seated === 0) {
    return 0;
  }

  return seated % PAIRED === 0 ? PAIRED : 1;
}

/** Whether the table draws a seat's own cards, which is what leaves a move onto it landing on those cards. */
export function drawnAt(layout: Layout, seat: number): boolean {
  return layout.slots.some((slot) => slot.seat === seat);
}
