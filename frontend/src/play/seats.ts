import type { Layout, Tint } from "../api/layout";

/** What a seat reads as where the plaques name none, which a layout leaves no room for. */
const SEATED = "Seat";

/** What one seat is called, which is the name its plaque reads under. */
export function nameOf(layout: Layout, seat: number): string {
  return layout.plaques.find((plaque) => plaque.seat === seat)?.name ?? `${SEATED} ${seat}`;
}

/** The tint one seat plays under, and nothing where the table was served with no host holding one for it. */
export function tintOf(layout: Layout, seat: number): Tint | null {
  return layout.plaques.find((plaque) => plaque.seat === seat)?.tint ?? null;
}

/** The tint the seat reading the page plays under, and nothing where a spectator is reading it. */
export function ownTint(layout: Layout): Tint | null {
  return layout.observer === null ? null : tintOf(layout, layout.observer);
}

/**
 * How far round the table one seat sits from the seat reading the page, counting the way play runs.
 *
 * The seat reading the page sits at nought and the seat it plays into at one, so a table reads the same to
 * everybody at it: each player has the same neighbor to their left whichever seat they hold. A spectator reads
 * the table from the first seat, which is the one arrangement a table with nobody at its near edge admits.
 */
export function turnOf(layout: Layout, seat: number): number {
  return (seat - (layout.observer ?? 0) + layout.players) % layout.players;
}
