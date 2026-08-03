import type { ReactElement } from "react";

import { leaveSeat } from "../play/useSeat";
import type { Connection } from "../play/useTable";

interface WaitingProps {
  table: string;
  connection: Connection;
  trouble: string | null;
}

/** How a tab reads while the table it named has yet to answer for itself, and where a refusal leaves it. */
export function Waiting({ table, connection, trouble }: WaitingProps): ReactElement {
  return (
    <div className="notice">
      <p>{connection === "refused" ? `Table ${table} turned this tab away` : `Joining table ${table}`}</p>
      {trouble !== null && <p className="trouble">{trouble}</p>}
      <button type="button" onClick={leaveSeat}>
        Take another seat
      </button>
    </div>
  );
}
