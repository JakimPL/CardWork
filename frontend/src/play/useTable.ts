import { useCallback, useEffect, useRef, useState } from "react";

import { followCommits, readLayout, readView } from "../api/client";
import type { Layout } from "../api/layout";
import { reasonOf } from "../api/refusal";
import type { Seat } from "../api/seat";
import type { PositionView } from "../api/views";
import type { Arrivals } from "./arrivals";
import { useArrivals } from "./arrivals";
import { advanced, reachedBy } from "./commits";
import { whileInView } from "./viewing";

/** How far a client has read before it holds a position, which the one it joins on settles at once. */
const UNREAD = 0;

/** How a client stands with the table it is watching. */
export type Connection = "joining" | "following" | "resuming" | "refused";

/** A table as one tab holds it: how it is laid out, where it stands, and how the two are being kept current. */
export interface Watched {
  layout: Layout | null;
  view: PositionView | null;
  connection: Connection;
  trouble: string | null;
  arrivals: Arrivals;
  refresh: () => void;
}

/**
 * Join one table and stay current with it for as long as the tab holds the seat.
 *
 * A client asks for two things as it joins and one thereafter: the arrangement, which answers for the whole
 * match, the position it joins on, and then every commit from that position onward. The stream carries the
 * cursor and the moves a seat may make alongside each change, so the table on screen is never a round trip
 * behind the table itself.
 *
 * The stream is held while the page is in view and let go while it is out of view, which is what leaves a
 * browser the connections a move goes up on where one machine holds a tab per seat. A tab coming back into
 * view opens the stream afresh at the commits it holds, and the journal behind the stream serves it every
 * commit it missed, so looking away costs a player the reading of what happened and nothing else.
 *
 * `refresh` reads the position again, which is what a client does when it learns the table has moved past
 * where it thought it stood. `arrivals` is what the newest commit laid down, which the cards it landed on are
 * drawn open for as long as that takes to read.
 *
 * @param seat - the table watched and the token it is watched as.
 */
export function useTable(seat: Seat): Watched {
  const [layout, setLayout] = useState<Layout | null>(null);
  const [view, setView] = useState<PositionView | null>(null);
  const [connection, setConnection] = useState<Connection>("joining");
  const [trouble, setTrouble] = useState<string | null>(null);
  const { arrivals, landed } = useArrivals();
  const reached = useRef(UNREAD);

  const hold = useCallback((position: PositionView) => {
    reached.current = position.seq;
    setView(position);
  }, []);

  const refresh = useCallback(() => {
    readView(seat)
      .then(hold)
      .catch((refusal: unknown) => {
        setTrouble(reasonOf(refusal));
      });
  }, [seat, hold]);

  useEffect(() => {
    const watching = { held: true };
    let release: (() => void) | null = null;

    const following = (): (() => void) => {
      const stop = followCommits(seat, reached.current, {
        onOpen: () => {
          setConnection("following");
          setTrouble(null);
        },
        onCommit: (event) => {
          reached.current = Math.max(reached.current, reachedBy(event));
          setView((held) => (held === null ? held : advanced(held, event)));
          landed(event);
        },
        onDropped: (reason) => {
          setConnection("resuming");
          setTrouble(reason);
        },
        onRefused: (reason) => {
          setConnection("refused");
          setTrouble(reason);
        },
      });

      return () => {
        setConnection("joining");
        stop();
      };
    };

    const join = async (): Promise<void> => {
      const [arrangement, position] = await Promise.all([readLayout(seat), readView(seat)]);
      if (!watching.held) {
        return;
      }

      setLayout(arrangement);
      hold(position);
      setTrouble(null);
      release = whileInView(document, following);
    };

    join().catch((refusal: unknown) => {
      if (watching.held) {
        setConnection("refused");
        setTrouble(reasonOf(refusal));
      }
    });

    return () => {
      watching.held = false;
      release?.();
    };
  }, [seat, landed, hold]);

  return { layout, view, connection, trouble, arrivals, refresh };
}
