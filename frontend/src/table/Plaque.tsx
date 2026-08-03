import type { ReactElement } from "react";

import type { Layout, Plaque as Standing } from "../api/layout";
import type { PositionView } from "../api/views";
import { seatReadouts, seatValue } from "../play/readouts";
import { offerTo } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import { clicking } from "./clicks";

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
 * committed by pointing at that player.
 */
export function Plaque({ plaque, layout, view, playing }: PlaqueProps): ReactElement {
  const acting = view.state.to_act.includes(plaque.seat);
  const own = plaque.seat === layout.observer;
  const landing = offerTo(playing.standing, { commit: "seat", seat: plaque.seat });
  return (
    <div className={classes("plaque", acting && "acting", own && "own", landing !== null && "live")}>
      {landing !== null && (
        <button
          type="button"
          className="landing"
          title={landing.caption}
          aria-label={`${landing.caption}: ${plaque.name}`}
          onClick={clicking(() => {
            playing.commit(landing.target);
          })}
        />
      )}
      <span className="who">{own ? `${plaque.name} (you)` : plaque.name}</span>
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
