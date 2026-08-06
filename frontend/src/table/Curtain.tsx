import { type ReactElement, useEffect } from "react";

import type { Interlude, Layout } from "../api/layout";
import type { Report } from "../play/interludes";
import { leading } from "../play/interludes";
import { seatReadouts, seatValue, tableReadouts, tableValue } from "../play/readouts";
import { nameOf } from "../play/seats";
import { clicking } from "./clicks";
import { clears } from "./keys";

/** What each pause in play is called, in the interface's own words rather than any game's. */
const TITLES: Record<Interlude, string> = {
  round: "Round over",
  match: "Match over",
};

/** How the seats a match belongs to read, and how two of them read beside each other. */
const TAKES_THE_MATCH = "takes the match";
const SHARE_THE_MATCH = "share the match";
const ALSO = " and ";

/** The pause a match is read out at, which is the one that names a winner. */
const MATCH: Interlude = "match";

/** How many seats hold a match one seat won outright. */
const ALONE = 1;

/** A click the panel keeps to itself, since it is the page behind the panel that a click dismisses. */
const KEPT = (): void => undefined;

interface CurtainProps {
  layout: Layout;
  report: Report;
  dismiss: () => void;
}

/**
 * What the table came to, held over the cards until the player reading it says they have.
 *
 * A boundary settles in one burst, so a round scored and the next round dealt reach a player as one motion and the
 * screen alone says nothing about what the round was worth. This is where it is said: the standing seat by seat as
 * the closing commit left it, the figures the game keeps of the whole table beneath, and the seat a decided match
 * belongs to named from the end of the standing the layout points to. Every figure comes off the layout's own
 * readouts, so what a particular game counts reaches this panel without it holding the name of any of them.
 *
 * Dismissing it is one player saying they have read it, which is what lets the commits held behind it land. It is
 * each player's own reading and no message to the table, so a seat that looks away holds nobody up: a turn simply
 * waits at the seat it belongs to, as it does at any other moment of a round.
 *
 * Three ways out, the same three that put a selection back down: the button, `Escape`, and a click away from the
 * panel. It lies over the whole page while it stands, so no card beneath it can be reached by accident.
 */
export function Curtain({ layout, report, dismiss }: CurtainProps): ReactElement {
  useEffect(() => {
    const pressed = (event: KeyboardEvent): void => {
      if (clears(event.key)) {
        dismiss();
      }
    };

    window.addEventListener("keydown", pressed);
    return () => {
      window.removeEventListener("keydown", pressed);
    };
  }, [dismiss]);

  return (
    <div className="curtain" onClick={clicking(dismiss)} role="presentation">
      <section className="report" onClick={clicking(KEPT)} role="presentation">
        <h2 className="outcome">{TITLES[report.interlude]}</h2>
        {report.interlude === MATCH && <p className="winner">{won(layout, report)}</p>}
        <ul className="results">
          {layout.plaques.map((plaque) => (
            <li className="result" key={plaque.seat} data-tint={plaque.tint}>
              <span className="who">{plaque.name}</span>
              <dl className="figures">
                {seatReadouts(layout).map((readout) => (
                  <div className="figure" key={readout.field}>
                    <dt>{readout.label}</dt>
                    <dd>{seatValue(report.state, readout, plaque.seat)}</dd>
                  </div>
                ))}
              </dl>
            </li>
          ))}
        </ul>
        <dl className="figures table">
          {tableReadouts(layout).map((readout) => (
            <div className="figure" key={readout.field}>
              <dt>{readout.label}</dt>
              <dd>{tableValue(report.state, readout)}</dd>
            </div>
          ))}
        </dl>
        <button type="button" className="onward" onClick={clicking(dismiss)}>
          OK
        </button>
      </section>
    </div>
  );
}

/** The seats a decided match belongs to, named as the plaques name them. */
function won(layout: Layout, report: Report): string {
  const seats = leading(layout, report.state);
  const named = seats.map((seat) => nameOf(layout, seat)).join(ALSO);
  return `${named} ${seats.length === ALONE ? TAKES_THE_MATCH : SHARE_THE_MATCH}`;
}
