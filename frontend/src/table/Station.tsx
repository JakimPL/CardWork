import type { ReactElement } from "react";

import type { Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import { nameOf } from "../play/seats";
import { offerTo } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import { clicking } from "./clicks";
import type { Station as Seated } from "./placing";
import { Zones } from "./Zones";

interface StationProps {
  station: Seated;
  layout: Layout;
  view: PositionView;
  arrivals: Arrivals;
  playing: Playing;
}

/**
 * One other seat where it sits: who is there, the cards the table reads of them, and whose turn it is.
 *
 * A card table is read by what lies in front of each player, so a seat's cards are drawn at the place round the
 * table it holds, counting from the seat reading the page. What a holding says from across the table is how many
 * cards it has, which it carries beside the backs standing for them, and the name of the seat stands over both.
 *
 * A seat the cards in hand can be sent to lies under a place to send them, so a card is passed by pointing at
 * the player it goes to.
 */
export function Station({ station, layout, view, arrivals, playing }: StationProps): ReactElement {
  const acting = view.state.to_act.includes(station.seat);
  const landing = offerTo(playing.standing, { commit: "seat", seat: station.seat });
  const name = nameOf(layout, station.seat);
  return (
    <div className={classes("station", acting && "acting", landing !== null && "live")}>
      {landing !== null && (
        <button
          type="button"
          className="landing"
          title={landing.caption}
          aria-label={`${landing.caption}: ${name}`}
          onClick={clicking(() => {
            playing.commit(landing.target);
          })}
        />
      )}
      <span className="who">{name}</span>
      <Zones place="station" slots={station.slots} view={view} arrivals={arrivals} playing={playing} />
    </div>
  );
}
