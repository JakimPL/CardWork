import type { Seat } from "../api/seat";

/**
 * The fields a tab is told which table it plays at, and as whom, which mirror `cardtable.interface`.
 *
 * They are read out of the fragment of the address, which the browser keeps to itself: the token reaches the
 * server in a header on each request and stands in no address it logs. The host prints one of these addresses
 * per seat as it opens a table, so a person joins by opening the line they were handed.
 */
export const TABLE_FIELD = "table";
export const TOKEN_FIELD = "token";

/** The seat a fragment names, and nothing where it names no table. */
export function seatIn(fragment: string): Seat | null {
  const stated = new URLSearchParams(fragment.replace(/^#/, ""));
  const table = stated.get(TABLE_FIELD);
  if (table === null || table === "") {
    return null;
  }

  const token = stated.get(TOKEN_FIELD);
  return { table, token: token === null || token === "" ? null : token };
}

/** The fragment one seat is reached through, which is what a tab joining a table sets. */
export function fragmentFor(seat: Seat): string {
  const stated = new URLSearchParams({ [TABLE_FIELD]: seat.table });
  if (seat.token !== null) {
    stated.set(TOKEN_FIELD, seat.token);
  }

  return `#${stated.toString()}`;
}
