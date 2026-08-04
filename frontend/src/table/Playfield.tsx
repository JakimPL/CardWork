import { type ReactElement, useEffect } from "react";

import type { Layout } from "../api/layout";
import type { Seat } from "../api/seat";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import { usePlay } from "../play/usePlay";
import type { Connection } from "../play/useTable";
import { classes } from "./classes";
import { answering } from "./clicks";
import { Header } from "./Header";
import { clears } from "./keys";
import { StatusLine } from "./StatusLine";
import { Zones } from "./Zones";

interface PlayfieldProps {
  seat: Seat;
  layout: Layout;
  view: PositionView;
  connection: Connection;
  trouble: string | null;
  arrivals: Arrivals;
  refresh: () => void;
}

/**
 * One table as a seat plays it: the standing across the top, the shared cards in the middle, its own below.
 *
 * The three regions are the whole page and they fit the window between them, so a player reads the table
 * without scrolling for any part of it. Every zone drawn, every figure read and every word of the phase comes
 * from the layout the game stated, which is what leaves this page holding no knowledge of either game.
 *
 * Three presses put the cards in hand back down, which between them cover every way a table is played: a click
 * on the page away from the cards, a press of the other button wherever it lands, and `Escape`. The first is the
 * one a touch screen has, and the other two are what a hand already resting on a mouse or a keyboard reaches for.
 */
export function Playfield({
  seat,
  layout,
  view,
  connection,
  trouble,
  arrivals,
  refresh,
}: PlayfieldProps): ReactElement {
  const playing = usePlay(seat, layout, view, refresh);
  const { clear } = playing;

  useEffect(() => {
    const pressed = (event: KeyboardEvent): void => {
      if (clears(event.key)) {
        clear();
      }
    };

    window.addEventListener("keydown", pressed);
    return () => {
      window.removeEventListener("keydown", pressed);
    };
  }, [clear]);

  return (
    <div
      className={classes("page", playing.sending && "sending")}
      onClick={clear}
      onContextMenu={answering(clear)}
      role="presentation"
    >
      <Header layout={layout} view={view} playing={playing} />
      <main className="shared">
        <Zones region="table" layout={layout} view={view} arrivals={arrivals} playing={playing} />
      </main>
      <footer className="controls">
        <Zones region="seat" layout={layout} view={view} arrivals={arrivals} playing={playing} />
        <p className="guidance">{playing.hint}</p>
        <StatusLine layout={layout} view={view} connection={connection} trouble={trouble} />
      </footer>
    </div>
  );
}
