import type { ReactElement } from "react";

import type { Seat } from "./api/seat";
import { Drawing } from "./play/useArtwork";
import { useSeat } from "./play/useSeat";
import { Joining } from "./table/Joining";
import { Table } from "./table/Table";

/**
 * The page: the table the address names, or the way to name one.
 *
 * A table is held under the seat it is played as, so taking another seat starts the table over rather than
 * carrying one seat's position into another's. The pack the cards are drawn from stands over both, since which
 * artwork a table draws with is one thing for the whole page and holds across every seat it is opened at.
 */
export function App(): ReactElement {
  const seat = useSeat();
  return <Drawing>{seat === null ? <Joining /> : <Table key={held(seat)} seat={seat} />}</Drawing>;
}

/** One name per seat at a table, which is what tells the page it is playing as somebody else now. */
function held(seat: Seat): string {
  return `${seat.table}/${seat.token ?? ""}`;
}
