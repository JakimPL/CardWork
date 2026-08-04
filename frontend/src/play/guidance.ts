import type { Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Prospect } from "./selection";

/** What the line under the cards says while a player holds a turn, or a selection part of the way to a move. */
const CHOOSING = "Pick a card to play";
const EXTENDING = "Pick another card";
const SPENT = "No move sends these cards";

/** What it says while the table owes this seat nothing: whom the turn stands with, or the table itself. */
const WAITING_ON = "Waiting for";
const WAITING = "Waiting for the table";

/** What a seat reads as where the plaques name none, which a layout leaves no room for. */
const SEATED = "Seat";

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
 * that rather than as a table gone quiet.
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

  return standing.offers.length === 0 ? waitingOn(layout, view) : CHOOSING;
}

/**
 * Whom the table stands on while this seat owes it nothing, named as the plaques name them.
 *
 * The observer's own seat stands among those that owe an action for as long as the rules still owe a settlement
 * of its turn, which is the table's business rather than a player's, so what reads out is the seats beside it.
 * A boundary between rounds and a match played out leave every seat at rest, and read as the table itself.
 */
function waitingOn(layout: Layout, view: PositionView): string {
  const named = view.state.to_act.filter((seat) => seat !== layout.observer).map((seat) => nameOf(layout, seat));
  return named.length === 0 ? WAITING : `${WAITING_ON} ${named.join(ALSO)}`;
}

/** What one seat is called, which is the name its plaque reads under. */
function nameOf(layout: Layout, seat: number): string {
  return layout.plaques.find((plaque) => plaque.seat === seat)?.name ?? `${SEATED} ${seat}`;
}
