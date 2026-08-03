import type { ReactElement } from "react";

import type { Layout, Region } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import { Slot } from "./Slot";

interface ZonesProps {
  region: Region;
  layout: Layout;
  view: PositionView;
  arrivals: Arrivals;
  playing: Playing;
}

/**
 * The zones of one region, in the order the layout places them.
 *
 * The shared table and the observer's own holdings are the same drawing under different geography, which is
 * the whole of what a region says: one component serves both, and where each sits on the page is the style
 * sheet's affair.
 */
export function Zones({ region, layout, view, arrivals, playing }: ZonesProps): ReactElement {
  const slots = layout.slots.filter((slot) => slot.region === region).sort((one, other) => one.place - other.place);
  return (
    <div className={classes("region", region)}>
      {slots.map((slot) => (
        <Slot key={slot.zone} slot={slot} zone={view.zones[slot.zone]} arrivals={arrivals} playing={playing} />
      ))}
    </div>
  );
}
