import type { ReactElement } from "react";

import type { Seat } from "../api/seat";
import { useTable } from "../play/useTable";
import { Header } from "./Header";
import { StatusLine } from "./StatusLine";
import { Zones } from "./Zones";

interface TableProps {
  seat: Seat;
}

/**
 * One table as a seat plays it: the standing across the top, the shared cards in the middle, its own below.
 *
 * The three regions are the whole page and they fit the window between them, so a player reads the table
 * without scrolling for any part of it. Every zone drawn, every figure read and every word of the phase comes
 * from the layout the game stated, which is what leaves this page holding no knowledge of either game.
 */
export function Table({ seat }: TableProps): ReactElement {
  const { layout, view, connection, trouble } = useTable(seat);

  if (layout === null || view === null) {
    return (
      <div className="notice">
        <p>
          {connection === "refused" ? `Table ${seat.table} turned this tab away` : `Joining table ${seat.table}`}
        </p>
        {trouble !== null && <p className="trouble">{trouble}</p>}
        <p>
          <a href="#">Take another seat</a>
        </p>
      </div>
    );
  }

  return (
    <div className="page">
      <Header layout={layout} view={view} />
      <main className="shared">
        <Zones region="table" layout={layout} view={view} />
      </main>
      <footer className="controls">
        <Zones region="seat" layout={layout} view={view} />
        <StatusLine layout={layout} view={view} connection={connection} trouble={trouble} />
      </footer>
    </div>
  );
}
