import type { ReactElement } from "react";
import { useMemo } from "react";

import type { Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import { nameOf, tintOf } from "../play/seats";
import type { Target } from "../play/selection";
import { offerTo } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import { Landing } from "./Landing";
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
 * The holdings of a seat lie side by side under that name and the places it seals a card in lie beneath them,
 * since the room round the edge of a table runs deeper than it runs wide.
 *
 * A seat the cards in hand can be sent to lies under a place to send them, so a card is passed by pointing at
 * the player it goes to, or by carrying it onto them.
 */
export function Station({ station, layout, view, arrivals, playing }: StationProps): ReactElement {
  const acting = view.state.to_act.includes(station.seat);
  const onto = useMemo<Target>(() => ({ commit: "seat", seat: station.seat }), [station.seat]);
  const landing = offerTo(playing.standing, onto);
  const name = nameOf(layout, station.seat);
  return (
    <div
      className={classes("station", acting && "acting", landing !== null && "live")}
      data-tint={tintOf(layout, station.seat)}
    >
      {landing !== null && (
        <Landing onto={onto} caption={landing.caption} label={`${landing.caption}: ${name}`} playing={playing} />
      )}
      <span className="who">{name}</span>
      <Zones place="theirs" slots={station.slots} view={view} arrivals={arrivals} playing={playing} />
    </div>
  );
}
