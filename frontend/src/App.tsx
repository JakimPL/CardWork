import type { ReactElement } from "react";

import type { Seat } from "./api/seat";
import { Drawing } from "./play/useArtwork";
import { useStanding } from "./play/useStanding";
import { useTables } from "./play/useTables";
import { Arriving } from "./table/Arriving";
import { Room } from "./table/Room";

/**
 * The page: the table the address names, or the way to name one.
 *
 * Two states carry a person from an address to a seat. A tab holding no token arrives at a table, which the
 * address names where a host announced one and the tables gathering offer otherwise; and a tab holding a token is
 * in the room, which is the gathering until the company deals it and the table from then on.
 *
 * A room is held under the token it is attended as, so arriving as somebody else starts it over rather than
 * carrying one guest's reading into another's. The pack the cards are drawn from stands over all of it, since
 * which artwork a table draws with is one thing for the whole page.
 */
export function App(): ReactElement {
  const { seat, code } = useStanding();
  const tables = useTables(seat === null);

  return (
    <Drawing>
      {seat !== null && seat.token !== null ? (
        <Room key={held(seat)} seat={seat} />
      ) : (
        <Arriving table={seat?.table ?? null} code={code} tables={tables} />
      )}
    </Drawing>
  );
}

/** One name per guest at a table, which is what tells the page it is standing there as somebody else now. */
function held(seat: Seat): string {
  return `${seat.table}/${seat.token ?? ""}`;
}
