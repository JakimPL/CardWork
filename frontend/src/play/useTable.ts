import { useCallback, useEffect, useRef, useState } from "react";

import { followCommits, readLayout, readView } from "../api/client";
import type { Interludes, Layout } from "../api/layout";
import { reasonOf } from "../api/refusal";
import type { Seat } from "../api/seat";
import type { EventView, PositionView } from "../api/views";
import type { Arrivals } from "./arrivals";
import { useArrivals } from "./arrivals";
import { advanced, reachedBy } from "./commits";
import type { Interluding, Reading, Report } from "./interludes";
import { arriving, dismissed, interludeIn, PLAYING_ON } from "./interludes";
import { whileInView } from "./viewing";

/** How far a client has read before it holds a position, which the one it joins on settles at once. */
const UNREAD = 0;

/** Where play pauses before a client has been told, which is a table it reads straight through. */
const UNTOLD: Interludes = {};

/** How a client stands with the table it is watching. */
export type Connection = "joining" | "following" | "resuming" | "refused";

/** A table as one tab holds it: how it is laid out, where it stands, and how the two are being kept current. */
export interface Watched {
  layout: Layout | null;
  view: PositionView | null;
  connection: Connection;
  trouble: string | null;
  arrivals: Arrivals;
  report: Report | null;
  refresh: () => void;
  dismiss: () => void;
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
 * A commit at a boundary the layout names holds the table where the players can read it: `report` is what stands
 * to be read and `dismiss` is one player saying they have read it, at which point the commits that waited behind
 * it land. So the boundary is taken off the stream rather than off the table on screen, since a settlement
 * commits the close of one round and the deal of the next in a burst and a render may show only the last of them.
 *
 * @param seat - the table watched and the token it is watched as.
 */
export function useTable(seat: Seat): Watched {
  const [layout, setLayout] = useState<Layout | null>(null);
  const [view, setView] = useState<PositionView | null>(null);
  const [connection, setConnection] = useState<Connection>("joining");
  const [trouble, setTrouble] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const { arrivals, landed } = useArrivals();
  const reached = useRef(UNREAD);
  const pauses = useRef<Interludes>(UNTOLD);
  const interluding = useRef<Interluding>(PLAYING_ON);

  const hold = useCallback((position: PositionView) => {
    reached.current = position.seq;
    setView(position);
  }, []);

  const carry = useCallback(
    (read: Reading) => {
      interluding.current = read.interluding;
      setReport(read.interluding.report);
      for (const event of read.applied) {
        setView((held) => (held === null ? held : advanced(held, event)));
        landed(event);
      }
    },
    [landed],
  );

  const arrive = useCallback(
    (event: EventView) => {
      carry(arriving(interluding.current, { event, interlude: interludeIn(pauses.current, event.state) }));
    },
    [carry],
  );

  const dismiss = useCallback(() => {
    carry(dismissed(interluding.current));
  }, [carry]);

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
          arrive(event);
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

      pauses.current = arrangement.interludes;
      interluding.current = PLAYING_ON;
      setLayout(arrangement);
      setReport(null);
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
  }, [seat, arrive, hold]);

  return { layout, view, connection, trouble, arrivals, report, refresh, dismiss };
}
