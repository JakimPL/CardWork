import type { Prospect } from "./selection";

/** What the line under the cards says while a player has nothing to do, or nothing yet. */
const WAITING = "Nothing to play just now";
const CHOOSING = "Pick a card to play";
const EXTENDING = "Pick another card";
const SPENT = "No move sends these cards";

/** How two things a selection could send read beside each other. */
const BESIDES = " · ";

/**
 * What to tell the player about the move in their hands, in the words a person reads.
 *
 * A refusal is what matters most, since it is the table answering something the player did. Beyond that the
 * line follows the selection: the captions of the moves it stands ready to send, the invitation to add a card
 * where a longer move is still open, and the standing invitation to pick one up.
 */
export function guidance(standing: Prospect, notice: string | null): string {
  if (notice !== null) {
    return notice;
  }

  if (standing.armed.length > 0) {
    return [...new Set(standing.armed.map((offer) => offer.caption))].join(BESIDES);
  }

  if (standing.selection !== null) {
    return standing.open.size === 0 ? SPENT : EXTENDING;
  }

  return standing.offers.length === 0 ? WAITING : CHOOSING;
}
