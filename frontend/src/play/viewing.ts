/** What a page says about whether anybody is looking at it, which is the whole of a document this reads. */
export interface Viewing {
  hidden: boolean;
  addEventListener: (change: "visibilitychange", noticed: () => void) => void;
  removeEventListener: (change: "visibilitychange", noticed: () => void) => void;
}

/** The change a page reports as it comes into view and as it goes out of view again. */
const LOOKED = "visibilitychange" as const;

/**
 * Hold something for as long as the page is in view, and let it go while the page is out of view.
 *
 * A browser allows a handful of connections to one address at a time, and a stream held open spends one of
 * them for as long as it stands. A table played from a tab per seat — which is how one machine seats several
 * players, and how a seating of seven is read at all — spends every connection on streams, and everything
 * else queues behind them: the move a player commits waits for a connection to carry it, and a tab that
 * joined once the rest were streaming reads a table that stands still.
 *
 * The page in front of the player is the one whose stream earns its connection. A page out of view holds
 * nothing and picks up where it left off as it returns, which the journal behind the stream is what makes
 * exact: what a tab missed while it was away is read from the record the moment it comes back.
 *
 * @param page - the page it is held in, which says whether it is in view and reports each change.
 * @param hold - taking the thing up, answering with letting it go.
 * @returns letting go for good, which leaves the page reporting to nobody.
 */
export function whileInView(page: Viewing, hold: () => () => void): () => void {
  let held: (() => void) | null = null;

  const looked = (): void => {
    if (page.hidden) {
      held?.();
      held = null;
      return;
    }

    held ??= hold();
  };

  looked();
  page.addEventListener(LOOKED, looked);
  return () => {
    page.removeEventListener(LOOKED, looked);
    held?.();
    held = null;
  };
}
