import type { Layout, Readout, Scope } from "../api/layout";
import type { Cursor } from "../api/views";

const TABLE: Scope = "table";
const SEAT: Scope = "seat";

/** What a figure the cursor holds nothing for reads as. */
const NOTHING = "—";

/** The readouts speaking about the whole table, which read in the line stating where play stands. */
export function tableReadouts(layout: Layout): Readout[] {
  return layout.readouts.filter((readout) => readout.scope === TABLE);
}

/** The readouts speaking about each seat in turn, which read on the plaques. */
export function seatReadouts(layout: Layout): Readout[] {
  return layout.readouts.filter((readout) => readout.scope === SEAT);
}

/** What one readout of the table says, in words. */
export function tableValue(state: Cursor, readout: Readout): string {
  return stated(state[readout.field]);
}

/**
 * What one readout says about one seat, in words.
 *
 * A seat field holds one value per seat in seat order, so a cursor standing at nothing yet — a score before
 * the first deal — leaves every seat reading as the figure it holds none of.
 */
export function seatValue(state: Cursor, readout: Readout, seat: number): string {
  const held = state[readout.field];
  return Array.isArray(held) ? stated(held[seat]) : NOTHING;
}

/** The phase in the words the game calls it by, and under its own name where the layout states none. */
export function phaseCaption(layout: Layout, state: Cursor): string {
  return layout.phases[state.phase] ?? state.phase;
}

/** One value of the cursor as a person reads it. */
function stated(value: unknown): string {
  if (value === null || value === undefined) {
    return NOTHING;
  }

  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }

  if (typeof value === "number" || typeof value === "string") {
    return String(value);
  }

  return JSON.stringify(value);
}
