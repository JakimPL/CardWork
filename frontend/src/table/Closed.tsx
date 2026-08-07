import type { ReactElement } from "react";

import { leave } from "../play/useStanding";

interface ClosedProps {
  table: string;
  reason: string | null;
}

/**
 * How a tab reads once the table it followed was broken up, whether it was gathering or in play.
 *
 * A close reaches every page over the stream it already holds, so the room falls away with a word rather than a
 * silence: the host or the overseer ends the table, the reason they left stands here, and the page offers the way
 * on to another table.
 */
export function Closed({ table, reason }: ClosedProps): ReactElement {
  return (
    <div className="notice closed">
      <p>
        Table <strong>{table}</strong> was closed.
      </p>
      {reason !== null && <p className="reason">{reason}</p>}
      <button type="button" onClick={leave}>
        Name another table
      </button>
    </div>
  );
}
