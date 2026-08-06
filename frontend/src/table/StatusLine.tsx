import type { ReactElement } from "react";

import type { Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Connection } from "../play/connection";
import { CONNECTIONS } from "../play/connection";
import { phaseCaption, tableReadouts, tableValue } from "../play/readouts";
import { nameOf } from "../play/seats";
import { classes } from "./classes";

/** What stands where no seat owes an action, which is a table waiting on the boundary that scores it. */
const NOBODY = "nobody";

interface StatusLineProps {
  layout: Layout;
  view: PositionView;
  connection: Connection;
  trouble: string | null;
}

/**
 * Where play stands, in one line under the cards: the phase, the figures the game keeps, and whose turn it is.
 *
 * Everything read here comes off the layout the game stated, so a figure a particular game tracks reaches the
 * screen by the same route the score does and this line holds the name of none of them.
 */
export function StatusLine({ layout, view, connection, trouble }: StatusLineProps): ReactElement {
  return (
    <div className="status">
      <span className="phase">{phaseCaption(layout, view.state)}</span>
      {tableReadouts(layout).map((readout) => (
        <span className="reading" key={readout.field}>
          <span className="label">{readout.label}</span>
          <span className="value">{tableValue(view.state, readout)}</span>
        </span>
      ))}
      <span className="reading">
        <span className="label">To act</span>
        <span className="value">{acting(layout, view)}</span>
      </span>
      <span className={classes("connection", connection)} title={trouble ?? undefined}>
        {CONNECTIONS[connection]}
      </span>
    </div>
  );
}

/**
 * The seats that owe an action, which is one seat while a turn goes round and several while a round is sealed.
 *
 * A seat is read by the name its plaque carries, which is the name its guest arrived at the gathering under, so
 * a person waiting on somebody is told who.
 */
function acting(layout: Layout, view: PositionView): string {
  const seats = [...view.state.to_act].sort((one, other) => one - other);
  return seats.length === 0 ? NOBODY : seats.map((seat) => nameOf(layout, seat)).join(", ");
}
