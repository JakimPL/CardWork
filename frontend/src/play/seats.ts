import type { Layout } from "../api/layout";

/** What a seat reads as where the plaques name none, which a layout leaves no room for. */
const SEATED = "Seat";

/** What one seat is called, which is the name its plaque reads under. */
export function nameOf(layout: Layout, seat: number): string {
  return layout.plaques.find((plaque) => plaque.seat === seat)?.name ?? `${SEATED} ${seat}`;
}

/**
 * How far round the table one seat sits from the seat reading the page, counting the way play runs.
 *
 * The seat reading the page sits at nought and the seat it plays into at one, so a table reads the same to
 * everybody at it: each player has the same neighbour to their left whichever seat they hold. A spectator reads
 * the table from the first seat, which is the one arrangement a table with nobody at its near edge admits.
 */
export function turnOf(layout: Layout, seat: number): number {
  return (seat - (layout.observer ?? 0) + layout.players) % layout.players;
}
