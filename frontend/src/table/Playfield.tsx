import { type ReactElement, useEffect } from "react";

import type { Layout } from "../api/layout";
import type { Seat } from "../api/seat";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import type { Connection } from "../play/connection";
import type { Report } from "../play/interludes";
import { ownTint } from "../play/seats";
import { saidAlone } from "../play/selection";
import { useArtwork } from "../play/useArtwork";
import { usePlay } from "../play/usePlay";
import { classes } from "./classes";
import { answering } from "./clicks";
import { Curtain } from "./Curtain";
import { Header } from "./Header";
import { clears, says } from "./keys";
import { Reaching } from "./landings";
import { own, ringOf, shared, SIDES } from "./placing";
import { Sitting } from "./Sitting";
import { crowding, shaping } from "./sizing";
import { StatusLine } from "./StatusLine";
import { Zones } from "./Zones";

interface PlayfieldProps {
  seat: Seat;
  layout: Layout;
  view: PositionView;
  connection: Connection;
  trouble: string | null;
  arrivals: Arrivals;
  report: Report | null;
  refresh: () => void;
  dismiss: () => void;
}

/**
 * One table as a seat plays it: the standing across the top, the table in the middle, its own cards below.
 *
 * The three bands are the whole page and they fit the window between them, so a player reads the table without
 * scrolling for any part of it. The middle band is the table itself: the zones every seat shares lie at the
 * center of it and the other players sit round three sides of them — up the left, across the top and down the
 * right — each with the cards the table reads of them, which is what a game of cards looks like. Every zone
 * drawn, every figure read and every word of the phase comes from the layout the game stated, which is what
 * leaves this page holding no knowledge of any game.
 *
 * The proportions of a card stand on the page itself, since every card on it is drawn from the one pack the
 * table serves: a pack written at another shape is drawn at that shape, hand and table alike.
 *
 * The places a move is sent by are held for the whole page, since the cards travel under the hand that took hold
 * of them: a move is sent by carrying its cards onto the place it goes to as readily as by pointing at that place.
 *
 * Three presses put the cards in hand back down, which between them cover every way a table is played: a click
 * on the page away from the cards, a press of the other button wherever it lands, and `Escape`. The first is the
 * one a touch screen has, and the other two are what a hand already resting on a mouse or a keyboard reaches for.
 *
 * The space bar says the move a turn stands ready to say, where a turn stands ready to say one move and one
 * alone: a stroke arriving at the page is that move, and a stroke arriving at a control is the browser pressing
 * the control it arrived at, so a move said either way is said a single time.
 *
 * The line under the cards is read out as it changes, so a move sent, a refusal the game phrased and a turn
 * coming round reach a player reading the page by ear as well as by eye.
 *
 * A round closed or a match decided stands over the whole of it as a report to be read, so a boundary the player
 * was looking at is a boundary they get to keep looking at.
 */
export function Playfield({
  seat,
  layout,
  view,
  connection,
  trouble,
  arrivals,
  report,
  refresh,
  dismiss,
}: PlayfieldProps): ReactElement {
  const playing = usePlay(seat, layout, view, refresh);
  const { clear, say } = playing;
  const spoken = saidAlone(playing.standing);
  const ring = ringOf(layout);
  const middle = shared(layout);
  const artwork = useArtwork();

  useEffect(() => {
    const pressed = (event: KeyboardEvent): void => {
      if (clears(event.key)) {
        clear();
        return;
      }

      if (spoken !== null && says(event.key, document.activeElement?.tagName ?? null)) {
        event.preventDefault();
        say(spoken);
      }
    };

    window.addEventListener("keydown", pressed);
    return () => {
      window.removeEventListener("keydown", pressed);
    };
  }, [clear, say, spoken]);

  return (
    <Reaching>
      <div
        className={classes("page", playing.sending && "sending")}
        data-tint={ownTint(layout)}
        style={shaping(artwork)}
        onClick={clear}
        onContextMenu={answering(clear)}
        role="presentation"
      >
        <Header layout={layout} view={view} playing={playing} />
        <main className="felt" style={crowding(ring, middle)}>
          {SIDES.map((side) => (
            <Sitting
              key={side}
              side={side}
              seats={ring[side]}
              layout={layout}
              view={view}
              arrivals={arrivals}
              playing={playing}
            />
          ))}
          <Zones place="shared" slots={middle} view={view} arrivals={arrivals} playing={playing} />
        </main>
        <footer className="controls">
          <Zones place="own" slots={own(layout)} view={view} arrivals={arrivals} playing={playing} />
          <p className="guidance" role="status">
            {playing.hint}
          </p>
          <StatusLine layout={layout} view={view} connection={connection} trouble={trouble} />
        </footer>
        {report !== null && <Curtain layout={layout} report={report} dismiss={dismiss} />}
      </div>
    </Reaching>
  );
}
