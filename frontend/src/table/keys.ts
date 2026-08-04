/** The key a player puts a selection back down with, which is the one a page is backed out of everywhere. */
const CLEARS = "Escape";

/** Whether a keystroke is the one that puts the cards in hand back down. */
export function clears(key: string): boolean {
  return key === CLEARS;
}
