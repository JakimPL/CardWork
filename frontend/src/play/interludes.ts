import type { Award, Interlude, Interludes, Layout } from "../api/layout";
import type { Cursor, EventView } from "../api/views";

/** The end of the standing a match is won at, as the two members of the vocabulary read. */
const HIGHEST: Award = "highest";

/** A pause in play the players read, and the cursor the commit that brought them to it left. */
export interface Report {
  interlude: Interlude;
  state: Cursor;
}

/** One commit off the stream, beside the pause it brings play to. */
export interface Arrival {
  event: EventView;
  interlude: Interlude | null;
}

/** How a client stands with the boundaries the stream carries: the pause it is held at, and what waits behind it. */
export interface Interluding {
  report: Report | null;
  waiting: readonly Arrival[];
}

/** What one commit leaves a client with: where it now stands, and the commits the table on screen takes. */
export interface Reading {
  interluding: Interluding;
  applied: readonly EventView[];
}

/** A client with play running through it, which is a table at no boundary and no commit waiting on one. */
export const PLAYING_ON: Interluding = { report: null, waiting: [] };

/**
 * The pause a cursor stands at, and nothing where play carries on through it.
 *
 * A phase the layout keyed as an interlude is one the game pauses at; every other phase says the table is running
 * and the commit carrying it is applied where it lands.
 */
export function interludeIn(interludes: Interludes, state: Cursor): Interlude | null {
  return interludes[state.phase] ?? null;
}

/**
 * Where a commit off the stream leaves a client, and which commits the table on screen takes with it.
 *
 * A boundary settles in a burst — one commit scoring the round, the next dealing its successor — so what raises
 * the report is the commit stream rather than the table drawn from it: a render may only ever show the last of a
 * burst, where the stream carries every one of them in order. The commit that pauses play is applied and read
 * out, and every commit behind it waits, so a player reads the round that just closed on the cards that played
 * it rather than on the deal that replaced them.
 */
export function arriving(interluding: Interluding, arrival: Arrival): Reading {
  if (interluding.report !== null) {
    return { interluding: { ...interluding, waiting: [...interluding.waiting, arrival] }, applied: [] };
  }

  return {
    interluding: { report: reportOf(arrival), waiting: [] },
    applied: [arrival.event],
  };
}

/**
 * Where a client stands once a report has been read and dismissed, with the commits held behind it applied.
 *
 * The commits that waited run through in the order they arrived, and a boundary among them raises its own report
 * and holds the rest again — which is what leaves a match played out read as a round closed and then as a match
 * decided, one dismissal apiece.
 */
export function dismissed(interluding: Interluding): Reading {
  let read: Reading = { interluding: PLAYING_ON, applied: [] };
  for (const arrival of interluding.waiting) {
    const next = arriving(read.interluding, arrival);
    read = { interluding: next.interluding, applied: [...read.applied, ...next.applied] };
  }

  return read;
}

/**
 * The seats the standing leaves the match with, which is every one of them where several stand equally well.
 *
 * The rules keep a standing and no winner, so which end of it a match is won at is the layout's to state and this
 * is the whole of the reading: the best figure the standing holds, and every seat holding it.
 */
export function leading(layout: Layout, state: Cursor): number[] {
  const points = state.points;
  if (points === null || points.length === 0) {
    return [];
  }

  const best = layout.award === HIGHEST ? Math.max(...points) : Math.min(...points);
  return points.flatMap((held, seat) => (held === best ? [seat] : []));
}

/** The report a commit at a boundary raises, and none where play carries on through it. */
function reportOf(arrival: Arrival): Report | null {
  return arrival.interlude === null ? null : { interlude: arrival.interlude, state: arrival.event.state };
}
