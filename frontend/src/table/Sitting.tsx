import type { ReactElement } from "react";

import type { Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import type { Side, Station as Seated } from "./placing";
import { Station } from "./Station";

interface SittingProps {
  side: Side;
  seats: Seated[];
  layout: Layout;
  view: PositionView;
  arrivals: Arrivals;
  playing: Playing;
}

/**
 * The seats at one side of the table, in the order play runs round them.
 *
 * A side stands its seats in a run of its own, so each of them holds the room its cards ask for and its
 * neighbors stand clear of it: a table of any size reads with every name legible and every holding whole. The
 * seats up the left are read from the near edge upward, which is the way a card travels round a table.
 */
export function Sitting({ side, seats, layout, view, arrivals, playing }: SittingProps): ReactElement {
  return (
    <div className={classes("sitting", side)}>
      {seats.map((station) => (
        <Station
          key={station.seat}
          station={station}
          layout={layout}
          view={view}
          arrivals={arrivals}
          playing={playing}
        />
      ))}
    </div>
  );
}
