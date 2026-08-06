import type { Seat } from "../api/seat";

/**
 * The fields a tab is told which table it stands at, and as whom, which mirror `cardtable.interface`.
 *
 * They are read out of the fragment of the address, which the browser keeps to itself: the code a guest arrives
 * on and the token they speak through afterwards both stand there and in no address a server logs. The host
 * prints one such address as it gathers a table, so a person joins by opening the line they were handed.
 */
export const TABLE_FIELD = "table";
export const TOKEN_FIELD = "token";
export const CODE_FIELD = "code";

/**
 * Where a tab stands: the table it is at, and the code it has yet to arrive on.
 *
 * The two carry a tab across the whole of its joining. A table and a code is what a person is handed and what
 * a name is offered against; a table and a token is what stands from the arrival onward, and the code leaves
 * the address the moment one exists.
 */
export interface Standing {
  seat: Seat | null;
  code: string | null;
}

/** The seat a fragment names, and nothing where it names no table. */
export function seatIn(fragment: string): Seat | null {
  const stated = stating(fragment);
  const table = stated.get(TABLE_FIELD);
  if (table === null || table === "") {
    return null;
  }

  return { table, token: named(stated, TOKEN_FIELD) };
}

/** The code a fragment carries, and nothing where it carries none. */
export function codeIn(fragment: string): string | null {
  return named(stating(fragment), CODE_FIELD);
}

/** Where a fragment leaves a tab standing, which is the whole of what the address says of it. */
export function standingIn(fragment: string): Standing {
  return { seat: seatIn(fragment), code: codeIn(fragment) };
}

/**
 * The fragment one tab is reached through, which is what a tab joining a table sets.
 *
 * A token supersedes the code it was minted against, so the code a guest arrived on leaves the address as soon
 * as they hold something to speak through and a reload rejoins on the token with no name asked again.
 */
export function fragmentFor(seat: Seat, code: string | null): string {
  const stated = new URLSearchParams({ [TABLE_FIELD]: seat.table });
  if (seat.token !== null) {
    stated.set(TOKEN_FIELD, seat.token);
  } else if (code !== null) {
    stated.set(CODE_FIELD, code);
  }

  return `#${stated.toString()}`;
}

/** The fields a fragment states, read whether or not it was handed over with its leading mark. */
function stating(fragment: string): URLSearchParams {
  return new URLSearchParams(fragment.replace(/^#/, ""));
}

/** One field of a fragment, and nothing where it stands empty or stands nowhere. */
function named(stated: URLSearchParams, field: string): string | null {
  const read = stated.get(field);
  return read === null || read === "" ? null : read;
}
