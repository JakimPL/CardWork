import { useEffect, useState } from "react";

import { followCommits, readLayout, readView } from "../api/client";
import type { Layout } from "../api/layout";
import { reasonOf } from "../api/refusal";
import type { Seat } from "../api/seat";
import type { PositionView } from "../api/views";
import { applyCommit } from "./commits";

/** How a client stands with the table it is watching. */
export type Connection = "joining" | "following" | "resuming" | "refused";

/** A table as one tab holds it: how it is laid out, where it stands, and how the two are being kept current. */
export interface Watched {
  layout: Layout | null;
  view: PositionView | null;
  connection: Connection;
  trouble: string | null;
}

/**
 * Join one table and stay current with it for as long as the tab holds the seat.
 *
 * A client asks for two things as it joins and one thereafter: the arrangement, which answers for the whole
 * match, the position it joins on, and then every commit from that position onward. The stream carries the
 * cursor and the moves a seat may make alongside each change, so the table on screen is never a round trip
 * behind the table itself.
 *
 * @param seat - the table watched and the token it is watched as.
 */
export function useTable(seat: Seat): Watched {
  const [layout, setLayout] = useState<Layout | null>(null);
  const [view, setView] = useState<PositionView | null>(null);
  const [connection, setConnection] = useState<Connection>("joining");
  const [trouble, setTrouble] = useState<string | null>(null);

  useEffect(() => {
    const watching = { held: true };
    let stop: (() => void) | null = null;

    const join = async (): Promise<void> => {
      const [arrangement, position] = await Promise.all([readLayout(seat), readView(seat)]);
      if (!watching.held) {
        return;
      }

      setLayout(arrangement);
      setView(position);
      setConnection("following");
      setTrouble(null);
      stop = followCommits(seat, position.seq, {
        onOpen: () => {
          setConnection("following");
          setTrouble(null);
        },
        onCommit: (event) => setView((held) => (held === null ? held : applyCommit(held, event))),
        onDropped: (reason) => {
          setConnection("resuming");
          setTrouble(reason);
        },
        onRefused: (reason) => {
          setConnection("refused");
          setTrouble(reason);
        },
      });
    };

    setConnection("joining");
    join().catch((refusal: unknown) => {
      if (watching.held) {
        setConnection("refused");
        setTrouble(reasonOf(refusal));
      }
    });

    return () => {
      watching.held = false;
      stop?.();
    };
  }, [seat.table, seat.token]);

  return { layout, view, connection, trouble };
}
