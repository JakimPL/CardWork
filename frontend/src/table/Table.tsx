import type { ReactElement } from "react";

import type { Seat } from "../api/seat";
import { useTable } from "../play/useTable";
import { Playfield } from "./Playfield";
import { Waiting } from "./Waiting";

interface TableProps {
  seat: Seat;
}

/**
 * The table this tab holds a seat at, once the table has answered for itself.
 *
 * A client needs the arrangement and a position before it can draw anything, so what stands here until both
 * arrive says where the joining has got to and offers the way to another seat.
 */
export function Table({ seat }: TableProps): ReactElement {
  const { layout, view, connection, trouble, arrivals, report, refresh, dismiss } = useTable(seat);

  if (layout === null || view === null) {
    return <Waiting table={seat.table} connection={connection} trouble={trouble} />;
  }

  return (
    <Playfield
      seat={seat}
      layout={layout}
      view={view}
      connection={connection}
      trouble={trouble}
      arrivals={arrivals}
      report={report}
      refresh={refresh}
      dismiss={dismiss}
    />
  );
}
