import type { ReactElement } from "react";
import { useMemo } from "react";

import type { Layout, Plaque as Standing } from "../api/layout";
import type { PositionView } from "../api/views";
import { seatReadouts, seatValue } from "../play/readouts";
import type { Target } from "../play/selection";
import { offerTo } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import { Landing } from "./Landing";
import { drawnAt } from "./placing";

interface PlaqueProps {
  plaque: Standing;
  layout: Layout;
  view: PositionView;
  playing: Playing;
}

/**
 * One player as the whole table reads them: who they are, what they hold, and whether the turn is theirs.
 *
 * Every seat takes one of these, the observer's own among them, so the standing reads across the table in a
 * single row. The counts are what a seat's cards say to everybody else, and the figures beside them are the
 * readouts the game scopes to a seat.
 *
 * A seat the cards in hand can be sent to lies under a place to send them, since a move naming a player is
 * committed by pointing at that player. Where the table draws that seat's own cards, the cards themselves are
 * what a player points at and the plaque leaves the move to them, which is the nearer thing to reach for.
 */
export function Plaque({ plaque, layout, view, playing }: PlaqueProps): ReactElement {
  const acting = view.state.to_act.includes(plaque.seat);
  const seated = plaque.seat === layout.observer;
  const onto = useMemo<Target>(() => ({ commit: "seat", seat: plaque.seat }), [plaque.seat]);
  const landing = drawnAt(layout, plaque.seat) ? null : offerTo(playing.standing, onto);
  return (
    <div className={classes("plaque", acting && "acting", seated && "own", landing !== null && "live")}>
      {landing !== null && (
        <Landing onto={onto} caption={landing.caption} label={`${landing.caption}: ${plaque.name}`} playing={playing} />
      )}
      <span className="who">{seated ? `${plaque.name} (you)` : plaque.name}</span>
      <dl className="figures">
        {seatReadouts(layout).map((readout) => (
          <div className="figure" key={readout.field}>
            <dt>{readout.label}</dt>
            <dd>{seatValue(view.state, readout, plaque.seat)}</dd>
          </div>
        ))}
        {plaque.counts.map((tally) => (
          <div className="figure" key={tally.zone}>
            <dt>{tally.label}</dt>
            <dd>{view.zones[tally.zone]?.cards.length ?? 0}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
