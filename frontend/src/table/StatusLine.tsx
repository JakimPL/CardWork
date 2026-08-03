import type { ReactElement } from "react";

import type { Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import { phaseCaption, tableReadouts, tableValue } from "../play/readouts";
import type { Connection } from "../play/useTable";
import { classes } from "./classes";

/** What a client watching a table says of itself, in the words a person reads. */
const CONNECTIONS: Record<Connection, string> = {
  joining: "Joining",
  following: "Live",
  resuming: "Reconnecting",
  refused: "Disconnected",
};

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
        <span className="value">{acting(view)}</span>
      </span>
      <span className={classes("connection", connection)} title={trouble ?? undefined}>
        {CONNECTIONS[connection]}
      </span>
    </div>
  );
}

/** The seats that owe an action, which is one seat while a turn goes round and several while a round is sealed. */
function acting(view: PositionView): string {
  const seats = [...view.state.to_act].sort((one, other) => one - other);
  return seats.length === 0 ? "nobody" : seats.map((seat) => `seat ${seat}`).join(", ");
}
