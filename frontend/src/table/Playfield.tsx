import type { ReactElement } from "react";

import type { Layout } from "../api/layout";
import type { Seat } from "../api/seat";
import type { PositionView } from "../api/views";
import { usePlay } from "../play/usePlay";
import type { Connection } from "../play/useTable";
import { classes } from "./classes";
import { Header } from "./Header";
import { StatusLine } from "./StatusLine";
import { Zones } from "./Zones";

interface PlayfieldProps {
  seat: Seat;
  layout: Layout;
  view: PositionView;
  connection: Connection;
  trouble: string | null;
  refresh: () => void;
}

/**
 * One table as a seat plays it: the standing across the top, the shared cards in the middle, its own below.
 *
 * The three regions are the whole page and they fit the window between them, so a player reads the table
 * without scrolling for any part of it. Every zone drawn, every figure read and every word of the phase comes
 * from the layout the game stated, which is what leaves this page holding no knowledge of either game.
 *
 * A click landing on the page itself is a click away from the cards, which puts a selection down.
 */
export function Playfield({ seat, layout, view, connection, trouble, refresh }: PlayfieldProps): ReactElement {
  const playing = usePlay(seat, layout, view, refresh);
  return (
    <div className={classes("page", playing.sending && "sending")} onClick={playing.clear} role="presentation">
      <Header layout={layout} view={view} playing={playing} />
      <main className="shared">
        <Zones region="table" layout={layout} view={view} playing={playing} />
      </main>
      <footer className="controls">
        <Zones region="seat" layout={layout} view={view} playing={playing} />
        <p className="guidance">{playing.hint}</p>
        <StatusLine layout={layout} view={view} connection={connection} trouble={trouble} />
      </footer>
    </div>
  );
}
