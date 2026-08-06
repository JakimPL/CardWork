/** The key a player puts a selection back down with, which is the one a page is backed out of everywhere. */
const CLEARS = "Escape";

/** The key a player says a move with, which is the one a hand already resting on a keyboard covers. */
const SAYS = " ";

/** The element the space bar presses of its own accord, which the browser answers for rather than the page. */
const PRESSED = "BUTTON";

/** Whether a keystroke is the one that puts the cards in hand back down. */
export function clears(key: string): boolean {
  return key === CLEARS;
}

/**
 * Whether a keystroke says a move, read against whatever the keyboard is resting on.
 *
 * The space bar presses the control holding the focus, so a stroke arriving at one is the browser's to answer and
 * a stroke arriving at the page itself is this one. A move a turn stands ready to say is said a single time,
 * whichever of the two a player reached for.
 *
 * @param key - the keystroke as the page received it.
 * @param resting - the name of the element holding the focus, where one holds it.
 */
export function says(key: string, resting: string | null): boolean {
  return key === SAYS && resting !== PRESSED;
}
