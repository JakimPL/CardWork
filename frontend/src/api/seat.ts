/**
 * The seat a tab speaks for: the table it plays at, and the token that holds a seat there.
 *
 * A token is the whole of what the host knows of a player, and a tab holding none watches the table. It rides
 * in a header on every request, so it stays out of the addresses a server logs.
 */
export interface Seat {
  table: string;
  token: string | null;
}

/** The header a client offers its token in, which mirrors `cardserver.identity.SEAT_HEADER`. */
export const SEAT_HEADER = "X-Seat-Token";

/** The headers one seat speaks through, which a spectator sends none of. */
export function credentials(seat: Seat): Record<string, string> {
  return seat.token === null ? {} : { [SEAT_HEADER]: seat.token };
}
