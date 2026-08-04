import type { Interlude, Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import { interludeIn, leading } from "./interludes";
import { nameOf } from "./seats";
import type { Prospect } from "./selection";

/** What the line under the cards says while a player holds a turn, or a selection part of the way to a move. */
const CHOOSING = "Pick a card to play";
const EXTENDING = "Pick another card";
const SPENT = "No move sends these cards";

/** What it says while the table owes this seat nothing: whom the turn stands with, or the table itself. */
const WAITING_ON = "Waiting for";
const WAITING = "Waiting for the table";

/** What it says once the match is played out, which is the seat or seats it belongs to. */
const TOOK_THE_MATCH = "took the match";
const SHARED_THE_MATCH = "shared the match";

/** The pause a match played out stands at, which is the one that outlasts a dismissal. */
const MATCH: Interlude = "match";

/** How many seats hold a match one seat won outright. */
const ALONE = 1;

/** How two things a selection could send read beside each other. */
const BESIDES = " · ";

/** How two seats the table stands on read beside each other. */
const ALSO = ", ";

/**
 * What to tell the player about the move in their hands, in the words a person reads.
 *
 * A refusal is what matters most, since it is the table answering something the player did. Beyond that the
 * line follows the selection: the captions of the moves it stands ready to send, the invitation to add a card
 * where a longer move is still open, and the standing invitation to pick one up.
 *
 * A seat with no move to make is told whom the table stands on, so a turn belonging to somebody else reads as
 * that rather than as a table gone quiet. A match played out reads as the seat it belongs to, which is what the
 * line goes on saying once the report naming that seat has been read and put away.
 */
export function guidance(layout: Layout, view: PositionView, standing: Prospect, notice: string | null): string {
  if (notice !== null) {
    return notice;
  }

  if (standing.armed.length > 0) {
    return [...new Set(standing.armed.map((offer) => offer.caption))].join(BESIDES);
  }

  if (standing.selection !== null) {
    return standing.open.size === 0 ? SPENT : EXTENDING;
  }

  if (interludeIn(layout.interludes, view.state) === MATCH) {
    return decided(layout, view);
  }

  return standing.offers.length === 0 ? waitingOn(layout, view) : CHOOSING;
}

/**
 * Whom the table stands on while this seat owes it nothing, named as the plaques name them.
 *
 * The observer's own seat stands among those that owe an action for as long as the rules still owe a settlement
 * of its turn, which is the table's business rather than a player's, so what reads out is the seats beside it.
 * A boundary between rounds leaves every seat at rest, and reads as the table itself.
 */
function waitingOn(layout: Layout, view: PositionView): string {
  const named = view.state.to_act.filter((seat) => seat !== layout.observer).map((seat) => nameOf(layout, seat));
  return named.length === 0 ? WAITING : `${WAITING_ON} ${named.join(ALSO)}`;
}

/** The seats a played-out match belongs to, read off the end of the standing the layout points to. */
function decided(layout: Layout, view: PositionView): string {
  const seats = leading(layout, view.state);
  const named = seats.map((seat) => nameOf(layout, seat)).join(ALSO);
  return `${named} ${seats.length === ALONE ? TOOK_THE_MATCH : SHARED_THE_MATCH}`;
}
